"""
Personal AI OS - RAG Service
RAG 检索增强生成服务
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.knowledge import KnowledgeChunk
from app.models.conversation import Conversation, ConversationMessage
from app.services.ai_service import create_ai_service, AIResponse


@dataclass
class RAGResponse:
    """RAG 响应"""
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: str
    memory_used: Optional[List[Dict[str, Any]]] = None


class RAGService:
    """RAG 服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None
    
    async def _get_ai_service(self):
        """获取 AI 服务"""
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service
    
    async def _search_knowledge(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相关知识（向量语义搜索，降级为文本搜索）
        """
        try:
            # 尝试向量搜索
            from app.services.embedding import create_embedding
            from app.core.config import settings
            from app.services.vector_store import VectorStore

            embedding_service = create_embedding(provider=settings.EMBEDDING_PROVIDER)
            query_embedding = await embedding_service.embed_query(query)

            vector_store = VectorStore(self.db)
            results = await vector_store.search_similar(
                query_embedding=query_embedding,
                user_id=user_id,
                limit=limit,
                threshold=0.3
            )

            if results:
                sources = []
                for chunk, score in results:
                    # 使用预加载的 document 关系
                    document = chunk.document if hasattr(chunk, 'document') and chunk.document else None
                    sources.append({
                        "chunk_id": str(chunk.chunk_id),
                        "content": chunk.content,
                        "document_id": str(chunk.document_id),
                        "document_name": document.file_name if document else "未知文档",
                        "relevance_score": round(score, 4)
                    })
                return sources

        except Exception:
            pass

        # 降级为文本搜索（转义 ILIKE 通配符，使用 selectinload 避免 N+1）
        safe_query = query.replace("%", "\\%").replace("_", "\\_")
        result = await self.db.execute(
            select(KnowledgeChunk)
            .options(selectinload(KnowledgeChunk.document))
            .join(Document)
            .where(
                Document.user_id == user_id,
                KnowledgeChunk.content.ilike(f"%{safe_query}%", escape="\\")
            )
            .limit(limit)
        )

        chunks = result.scalars().all()

        sources = []
        for chunk in chunks:
            sources.append({
                "chunk_id": str(chunk.chunk_id),
                "content": chunk.content,
                "document_id": str(chunk.document_id),
                "document_name": chunk.document.file_name if chunk.document else "未知文档",
                "relevance_score": 0.5
            })

        return sources
    
    async def _build_context(
        self,
        query: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        构建上下文
        
        Args:
            query: 用户问题
            sources: 相关知识
        
        Returns:
            上下文字符串
        """
        if not sources:
            return ""
        
        context_parts = ["以下是与问题相关的知识库内容：\n"]
        
        for i, source in enumerate(sources, 1):
            context_parts.append(f"[{i}] 来源：{source['document_name']}")
            context_parts.append(f"内容：{source['content']}\n")
        
        context_parts.append("请基于以上内容回答用户的问题。如果知识库中没有相关信息，请说明。")
        
        return "\n".join(context_parts)
    
    async def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是 Personal AI OS 的 AI 助手，一个个人认知操作系统。

你的职责是：
1. 基于用户的个人知识库回答问题
2. 提供准确、有依据的回答
3. 引用知识来源
4. 帮助用户理解和利用他们的知识资产

回答要求：
- 基于知识库内容回答，不要编造信息
- 如果知识库中没有相关信息，诚实说明
- 提供清晰、简洁的回答
- 在适当的地方引用来源"""
    
    async def _extract_memories(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Dict[str, str]]
    ):
        """
        从对话中提取记忆
        
        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            messages: 对话消息列表
        """
        try:
            from app.services.memory_extractor import create_memory_extractor
            
            extractor = await create_memory_extractor(self.db)
            await extractor.extract_and_save(
                user_id=user_id,
                conversation_id=conversation_id,
                messages=messages
            )
        except Exception as e:
            # 记忆提取失败不应该影响主流程
            print(f"记忆提取失败: {str(e)}")

    async def chat(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        memory_enabled: bool = True
    ) -> RAGResponse:
        """
        RAG 聊天
        
        Args:
            user_id: 用户 ID
            message: 用户消息
            conversation_id: 对话 ID（可选）
            memory_enabled: 是否启用记忆
        
        Returns:
            RAG 响应
        """
        # 1. 搜索相关知识
        sources = await self._search_knowledge(message, user_id)
        
        # 2. 构建上下文
        context = await self._build_context(message, sources)
        
        # 3. 获取或创建对话
        if conversation_id:
            result = await self.db.execute(
                select(Conversation).where(
                    Conversation.conversation_id == conversation_id,
                    Conversation.user_id == user_id
                )
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                # 创建新对话
                conversation = Conversation(
                    user_id=user_id,
                    title=message[:50] + "..." if len(message) > 50 else message
                )
                self.db.add(conversation)
                await self.db.flush()
        else:
            # 创建新对话
            conversation = Conversation(
                user_id=user_id,
                title=message[:50] + "..." if len(message) > 50 else message
            )
            self.db.add(conversation)
            await self.db.flush()
        
        # 4. 保存用户消息
        user_message = ConversationMessage(
            conversation_id=conversation.conversation_id,
            role="user",
            content=message
        )
        self.db.add(user_message)
        await self.db.flush()
        
        # 5. 获取历史消息（最近10条）
        history_result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation.conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(10)
        )
        history_messages = history_result.scalars().all()
        history_messages.reverse()
        
        # 6. 构建消息列表
        messages = []
        for msg in history_messages[:-1]:  # 排除刚添加的用户消息
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 添加当前问题（带上下文）
        if context:
            messages.append({
                "role": "user",
                "content": f"{context}\n\n用户问题：{message}"
            })
        else:
            messages.append({
                "role": "user",
                "content": message
            })
        
        # 7. 调用 AI
        ai_service = await self._get_ai_service()
        system_prompt = await self._get_system_prompt()
        
        ai_response = await ai_service.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000
        )
        
        # 8. 保存 AI 回复
        assistant_message = ConversationMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content=ai_response.content,
            sources=sources,
            metadata_={
                "context_used": bool(context),
                "sources_count": len(sources)
            }
        )
        self.db.add(assistant_message)
        await self.db.flush()
        
        # 9. 更新对话标题（如果是第一条消息）
        if len(history_messages) <= 1:
            conversation.title = message[:50] + "..." if len(message) > 50 else message
            await self.db.flush()
        
        return RAGResponse(
            answer=ai_response.content,
            sources=sources,
            conversation_id=str(conversation.conversation_id),
            memory_used=None  # TODO: 实现记忆调用
        )
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
        
        Returns:
            消息列表
        """
        # 验证对话属于当前用户
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.conversation_id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return []
        
        # 获取消息
        messages_result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
        )
        messages = messages_result.scalars().all()
        
        return [
            {
                "message_id": str(msg.message_id),
                "role": msg.role,
                "content": msg.content,
                "sources": msg.sources,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    
    async def list_conversations(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取对话列表
        
        Args:
            user_id: 用户 ID
            limit: 返回数量
        
        Returns:
            对话列表
        """
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        
        conversations = result.scalars().all()
        
        return [
            {
                "conversation_id": str(conv.conversation_id),
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat()
            }
            for conv in conversations
        ]


async def create_rag_service(db: AsyncSession) -> RAGService:
    """创建 RAG 服务"""
    return RAGService(db)
