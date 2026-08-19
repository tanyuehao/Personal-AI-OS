"""
Personal AI OS - Knowledge Repository
知识仓储
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.knowledge import KnowledgeChunk
from app.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository[KnowledgeChunk]):
    """知识仓储"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, KnowledgeChunk)
    
    async def get_by_document(self, document_id: str) -> List[KnowledgeChunk]:
        """获取文档的所有切片"""
        result = await self.db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        return list(result.scalars().all())
    
    async def search_text(self, user_id: str, query: str, limit: int = 10) -> List[KnowledgeChunk]:
        """文本搜索"""
        from app.models.document import Document
        
        result = await self.db.execute(
            select(KnowledgeChunk)
            .join(Document)
            .where(
                Document.user_id == user_id,
                KnowledgeChunk.content.ilike(f"%{query}%")
            )
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_by_document(self, document_id: str) -> int:
        """删除文档的所有切片"""
        result = await self.db.execute(
            select(KnowledgeChunk).where(
                KnowledgeChunk.document_id == document_id
            )
        )
        chunks = result.scalars().all()
        count = len(chunks)
        for chunk in chunks:
            await self.db.delete(chunk)
        await self.db.flush()
        return count
