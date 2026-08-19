"""
Personal AI OS - Memory Repository
记忆仓储
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.memory import Memory, MemoryType
from app.repositories.base import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    """记忆仓储"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Memory)
    
    async def get_by_type(self, user_id: str, memory_type: MemoryType) -> List[Memory]:
        """根据类型获取记忆"""
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.memory_type == memory_type.value
            ).order_by(Memory.importance.desc())
        )
        return list(result.scalars().all())
    
    async def get_confirmed(self, user_id: str, limit: int = 20) -> List[Memory]:
        """获取已确认的记忆"""
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            ).order_by(Memory.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_candidates(self, user_id: str, limit: int = 20) -> List[Memory]:
        """获取待确认的记忆"""
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "PENDING"
            ).order_by(Memory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def confirm(self, memory_id: str) -> Optional[Memory]:
        """确认记忆"""
        return await self.update(memory_id, is_confirmed="CONFIRMED")
    
    async def reject(self, memory_id: str) -> Optional[Memory]:
        """拒绝记忆"""
        return await self.update(memory_id, is_confirmed="REJECTED")
    
    async def search_by_content(self, user_id: str, query: str, limit: int = 10) -> List[Memory]:
        """按内容搜索记忆"""
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.content.ilike(f"%{query}%")
            ).order_by(Memory.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
