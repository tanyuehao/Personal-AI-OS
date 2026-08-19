"""
Personal AI OS - Base Repository
仓储基类
"""
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)


class BaseRepository(Generic[T]):
    """仓储基类"""
    
    def __init__(self, db: AsyncSession, model: Type[T]):
        self.db = db
        self.model = model
    
    async def get_by_id(self, id_value: str) -> Optional[T]:
        """根据 ID 获取"""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id_value)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        order_by: Optional[str] = None
    ) -> tuple[List[T], int]:
        """获取列表"""
        query = select(self.model)
        
        if user_id and hasattr(self.model, 'user_id'):
            query = query.where(self.model.user_id == user_id)
        
        # 获取总数
        count_query = select(func.count()).select_from(self.model)
        if user_id and hasattr(self.model, 'user_id'):
            count_query = count_query.where(self.model.user_id == user_id)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 排序
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by).desc())
        
        # 分页
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def create(self, **kwargs) -> T:
        """创建"""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance
    
    async def update(self, id_value: str, **kwargs) -> Optional[T]:
        """更新"""
        instance = await self.get_by_id(id_value)
        if not instance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        await self.db.flush()
        await self.db.refresh(instance)
        return instance
    
    async def delete(self, id_value: str) -> bool:
        """删除"""
        instance = await self.get_by_id(id_value)
        if not instance:
            return False
        
        await self.db.delete(instance)
        await self.db.flush()
        return True
    
    async def count(self, user_id: Optional[str] = None) -> int:
        """计数"""
        query = select(func.count()).select_from(self.model)
        if user_id and hasattr(self.model, 'user_id'):
            query = query.where(self.model.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar()
