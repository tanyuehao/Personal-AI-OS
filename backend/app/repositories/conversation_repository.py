"""
Personal AI OS - Conversation Repository
对话仓储
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.conversation import Conversation, ConversationMessage
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """对话仓储"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Conversation)
    
    async def get_by_user(self, user_id: str, limit: int = 20) -> List[Conversation]:
        """获取用户对话列表"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_with_messages(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话及其消息"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None
    ) -> ConversationMessage:
        """添加消息"""
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources
        )
        self.db.add(message)
        await self.db.flush()
        return message
    
    async def get_messages(self, conversation_id: str) -> List[ConversationMessage]:
        """获取对话消息"""
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
        )
        return list(result.scalars().all())
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话及其消息"""
        # 先删除消息
        messages = await self.get_messages(conversation_id)
        for message in messages:
            await self.db.delete(message)
        
        # 再删除对话
        return await self.delete(conversation_id)
