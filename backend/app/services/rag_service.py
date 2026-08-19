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
from app.models.memory import Memory
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
    
    async def _search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆（文本匹配 + 重要性排序）
        """
        try:
            # 获取用户所有已确认记忆，按重要性排序
            result = await self.db.execute(
                select(Memory).where(
                    Memory.user_id == user_id,
                    Memory.is_confirmed == "CONFIRMED"
                ).order_by(Memory.importance.desc())
                .limit(20)
            )
            all_memories = result.scalars().all()

            if not all_memories:
                return []

            # 关键词匹配打分
            query_lower = query.lower()
            query_words = [w for w in query_lower.split() if len(w) > 1]
            scored_memories = []

            for mem in all_memories:
                content_lower = mem.content.lower()
                score = 0
                for word in query_words:
                    if word in content_lower:
                        score += 1
                # 结合关键词分数和重要性
                final_score = score * 0.7 + mem.importance * 0.3
                scored_memories.append((mem, final_score))

            # 按综合分数排序
            scored_memories.sort(key=lambda x: x[1], reverse=True)

            # 返回 top N（至少返回 1 条）
            top_memories = scored_memories[:limit]
            if not top_memories:
                top_memories = [(all_memories[0], 0.5)]

            return [
                {
                    "memory_id": str(mem.memory_id),
                    "content": mem.content,
                    "memory_type": mem.memory_type,
                    "importance": mem.importance,
                    "relevance_score": round(score, 4)
                }
                for mem, score in top_memories
            ]

        except Exception:
            return []

    async def _build_memory_context(self, memories: List[Dict[str, Any]], max_tokens: int = 1000) -> str:
        """构建记忆上下文（带 Token budget）"""
        if not memories:
            return ""

        parts = ["以下是关于该用户的记忆信息：\n"]
        current_tokens = 10

        type_map = {
            "FACT": "事实",
            "EXPERIENCE": "经验",
            "OPINION": "观点",
            "DECISION": "决策",
            "PREFERENCE": "偏好"
        }

        for i, mem in enumerate(memories, 1):
            mem_type = type_map.get(mem["memory_type"], mem["memory_type"])
            mem_text = f"[{i}] ({mem_type}) {mem['content']}"
            mem_tokens = len(mem_text) * 2

            if current_tokens + mem_tokens > max_tokens:
                break

            parts.append(mem_text)
            current_tokens += mem_tokens

        parts.append("\n请参考以上记忆信息回答用户问题，使回答更加个性化。")
        return "\n".join(parts)

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
        sources: List[Dict[str, Any]],
        max_tokens: int = 3000
    ) -> str:
        """
        构建上下文（带 Token budget 控制）

        Args:
            query: 用户问题
            sources: 相关知识
            max_tokens: 最大 token 数（粗略估算：1 中文 ≈ 2 tokens）

        Returns:
            上下文字符串
        """
        if not sources:
            return ""

        context_parts = ["以下是与问题相关的知识库内容：\n"]
        current_tokens = 10  # 预留开头

        for i, source in enumerate(sources, 1):
            source_text = f"[{i}] 来源：{source['document_name']}\n内容：{source['content']}\n"
            source_tokens = len(source_text) * 2  # 粗略估算

            if current_tokens + source_tokens > max_tokens:
                break

            context_parts.append(source_text)
            current_tokens += source_tokens

        context_parts.append("请基于以上内容回答用户的问题。如果知识库中没有相关信息，请说明。")

        return "\n".join(context_parts)
    
    async def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是 Personal AI OS 的 AI 助手，一个个人认知操作系统。

你的职责是：
1. 基于用户的个人知识库回答问题
2. 参考用户的记忆（偏好、经验、观点等）提供个性化回答
3. 提供准确、有依据的回答
4. 引用知识来源
5. 帮助用户理解和利用他们的知识资产

回答要求：
- 基于知识库内容回答，不要编造信息
- 参考用户记忆，使回答更加个性化
- 如果知识库中没有相关信息，诚实说明
- 提供清晰、简洁的回答
- 必须引用来源：在回答中使用 [1]、[2] 等编号引用知识库内容
- 区分"资料事实"和"AI推断"：明确标注哪些是知识库中的事实，哪些是你的推断
- 不要把历史选择当成当前必然答案"""
    
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

    async def _extract_beliefs(
        self,
        user_id: str,
        messages: List[Dict[str, str]]
    ):
        """
        从对话中提取观点候选
        """
        try:
            from app.services.cognitive_engine import get_cognitive_engine
            from app.models.belief import Belief

            engine = get_cognitive_engine(self.db)
            beliefs = await engine.extract_beliefs_from_conversation(
                user_id=user_id,
                messages=messages
            )

            # 保存观点候选（状态为 CANDIDATE）
            for b in beliefs:
                if b.topic and b.content:
                    belief = Belief(
                        user_id=user_id,
                        topic=b.topic,
                        content=b.content,
                        confidence=b.confidence,
                        status="CANDIDATE"
                    )
                    self.db.add(belief)

            await self.db.flush()

        except Exception as e:
            print(f"观点提取失败: {str(e)}")

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

        # 2. 搜索相关记忆
        memories = []
        if memory_enabled:
            memories = await self._search_memories(message, user_id)

        # 3. 构建上下文（知识 + 记忆），带 Token budget 控制
        # 总预算 4000 tokens，知识占 3000，记忆占 1000
        context = await self._build_context(message, sources, max_tokens=3000)
        memory_context = await self._build_memory_context(memories, max_tokens=1000)
        
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

        # 添加当前问题（带知识上下文 + 记忆上下文）
        user_content = message
        if context or memory_context:
            parts = []
            if memory_context:
                parts.append(memory_context)
            if context:
                parts.append(context)
            parts.append(f"用户问题：{message}")
            user_content = "\n\n".join(parts)

        messages.append({
            "role": "user",
            "content": user_content
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

        # 10. 自动提取记忆和观点（后台异步）
        if memory_enabled:
            try:
                all_messages = [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": ai_response.content}
                ]
                await self._extract_memories(
                    user_id=user_id,
                    conversation_id=str(conversation.conversation_id),
                    messages=all_messages
                )

                # 提取观点候选
                await self._extract_beliefs(
                    user_id=user_id,
                    messages=all_messages
                )
            except Exception:
                pass  # 提取失败不影响主流程

        return RAGResponse(
            answer=ai_response.content,
            sources=sources,
            conversation_id=str(conversation.conversation_id),
            memory_used=memories if memories else None
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
