"""
Personal AI OS - Memory Extractor Service
记忆提取服务 - 从对话中自动提取重要信息
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, MemoryType
from app.services.ai_service import create_ai_service


@dataclass
class ExtractedMemory:
    """提取的记忆"""
    content: str
    memory_type: str
    importance: float
    confidence: float
    source: Optional[str] = None


class MemoryExtractor:
    """记忆提取器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None
    
    async def _get_ai_service(self):
        """获取 AI 服务"""
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service
    
    async def extract_from_conversation(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Dict[str, str]]
    ) -> List[ExtractedMemory]:
        """
        从对话中提取记忆
        
        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            messages: 对话消息列表
        
        Returns:
            提取的记忆列表
        """
        if not messages:
            return []
        
        # 构建提取提示词
        extraction_prompt = """分析以下对话，提取用户的重要信息、观点、决策和偏好。

对话内容：
"""
        
        for msg in messages:
            role = "用户" if msg.get("role") == "user" else "AI"
            extraction_prompt += f"{role}: {msg.get('content', '')}\n"
        
        extraction_prompt += """
请提取以下类型的信息：

1. FACT (事实): 用户明确陈述的事实信息
   - 重要程度: 0.3-0.5
   
2. EXPERIENCE (经验): 用户的经验、教训、成功/失败案例
   - 重要程度: 0.6-0.8
   
3. OPINION (观点): 用户的观点、看法、判断
   - 重要程度: 0.5-0.7
   
4. DECISION (决策): 用户做出的重要决策
   - 重要程度: 0.7-0.9
   
5. PREFERENCE (偏好): 用户的偏好、习惯、喜好
   - 重要程度: 0.4-0.6

请以 JSON 格式返回提取的记忆列表，格式如下：
{
  "memories": [
    {
      "content": "记忆内容",
      "memory_type": "FACT|EXPERIENCE|OPINION|DECISION|PREFERENCE",
      "importance": 0.0-1.0,
      "confidence": 0.0-1.0,
      "source": "来源描述（可选）"
    }
  ]
}

如果没有值得提取的信息，返回空列表 {"memories": []}"""
        
        try:
            ai_service = await self._get_ai_service()
            
            response = await ai_service.chat(
                messages=[{"role": "user", "content": extraction_prompt}],
                system_prompt="你是一个专业的信息提取助手。只返回 JSON 格式的结果，不要添加其他说明。",
                temperature=0.3,
                max_tokens=2000
            )
            
            # 解析响应
            import json
            content = response.content.strip()
            
            # 尝试提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            
            memories = []
            for item in result.get("memories", []):
                memories.append(ExtractedMemory(
                    content=item.get("content", ""),
                    memory_type=item.get("memory_type", "FACT"),
                    importance=item.get("importance", 0.5),
                    confidence=item.get("confidence", 0.7),
                    source=item.get("source")
                ))
            
            return memories
            
        except Exception as e:
            print(f"记忆提取失败: {str(e)}")
            return []
    
    async def save_memories(
        self,
        user_id: str,
        extracted_memories: List[ExtractedMemory],
        conversation_id: Optional[str] = None
    ) -> List[Memory]:
        """
        保存提取的记忆
        
        Args:
            user_id: 用户 ID
            extracted_memories: 提取的记忆列表
            conversation_id: 对话 ID
        
        Returns:
            保存的记忆列表
        """
        saved_memories = []
        
        for extracted in extracted_memories:
            # 检查是否已存在相似记忆
            existing = await self._find_similar_memory(
                user_id=user_id,
                content=extracted.content,
                memory_type=extracted.memory_type
            )
            
            if existing:
                # 更新现有记忆的重要性
                existing.frequency += 1
                existing.importance = min(1.0, existing.importance + 0.1)
                saved_memories.append(existing)
            else:
                # 创建新记忆
                memory = Memory(
                    user_id=user_id,
                    memory_type=extracted.memory_type,
                    content=extracted.content,
                    source=extracted.source or f"对话提取 (conversation_id: {conversation_id})",
                    importance=extracted.importance,
                    confidence=extracted.confidence
                )
                self.db.add(memory)
                saved_memories.append(memory)
        
        await self.db.flush()
        
        return saved_memories
    
    async def _find_similar_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str,
        threshold: float = 0.8
    ) -> Optional[Memory]:
        """
        查找相似记忆
        
        Args:
            user_id: 用户 ID
            content: 内容
            memory_type: 记忆类型
            threshold: 相似度阈值
        
        Returns:
            相似记忆（如果找到）
        """
        from sqlalchemy import select
        
        # 简单的文本相似度检查（转义 ILIKE 通配符）
        safe_content = content[:50].replace("%", "\\%").replace("_", "\\_")
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.memory_type == memory_type,
                Memory.content.ilike(f"%{safe_content}%", escape="\\")
            ).limit(1)
        )
        
        return result.scalar_one_or_none()
    
    async def extract_and_save(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Dict[str, str]]
    ) -> List[Memory]:
        """
        提取并保存记忆（完整流程）
        
        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            messages: 对话消息列表
        
        Returns:
            保存的记忆列表
        """
        # 1. 提取记忆
        extracted = await self.extract_from_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages
        )
        
        # 2. 保存记忆
        saved = await self.save_memories(
            user_id=user_id,
            extracted_memories=extracted,
            conversation_id=conversation_id
        )
        
        return saved


async def create_memory_extractor(db: AsyncSession) -> MemoryExtractor:
    """创建记忆提取器"""
    return MemoryExtractor(db)
