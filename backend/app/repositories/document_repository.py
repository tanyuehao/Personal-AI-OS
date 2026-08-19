"""
Personal AI OS - Document Repository
文档仓储
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.document import Document, DocumentStatus
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """文档仓储"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Document)
    
    async def get_by_user(self, user_id: str, page: int = 1, limit: int = 20) -> tuple[List[Document], int]:
        """获取用户文档列表"""
        return await self.get_all(user_id=user_id, page=page, limit=limit, order_by="created_at")
    
    async def get_by_status(self, user_id: str, status: DocumentStatus) -> List[Document]:
        """根据状态获取文档"""
        result = await self.db.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.status == status.value
            )
        )
        return list(result.scalars().all())
    
    async def update_status(self, document_id: str, status: DocumentStatus, message: Optional[str] = None) -> Optional[Document]:
        """更新文档状态"""
        update_data = {"status": status.value}
        if message:
            update_data["status_message"] = message
        return await self.update(document_id, **update_data)
    
    async def delete_with_chunks(self, document_id: str) -> bool:
        """删除文档及其所有切片"""
        from app.models.knowledge import KnowledgeChunk
        
        # 先删除切片
        result = await self.db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)
        )
        chunks = result.scalars().all()
        for chunk in chunks:
            await self.db.delete(chunk)
        
        # 再删除文档
        return await self.delete(document_id)
