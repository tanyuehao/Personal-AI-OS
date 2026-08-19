"""
Personal AI OS - User Repository
用户仓储
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户仓储"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, username: str, email: str, password_hash: str) -> User:
        """创建用户"""
        return await self.create(
            username=username,
            email=email,
            password_hash=password_hash
        )
