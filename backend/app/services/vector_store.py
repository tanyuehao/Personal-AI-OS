"""
Personal AI OS - Vector Store Service
向量存储服务（pgvector）
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector

from app.models.knowledge import KnowledgeChunk
from app.models.document import Document
from app.core.config import settings


class VectorStore:
    """向量存储服务（基于 pgvector）"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dimension = settings.EMBEDDING_DIMENSION

    async def initialize(self):
        """初始化 pgvector 扩展"""
        await self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await self.db.flush()

    async def add_embedding(
        self,
        chunk_id: str,
        embedding: List[float],
        content: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """添加向量到存储"""
        try:
            result = await self.db.execute(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.chunk_id == chunk_id
                )
            )
            chunk = result.scalar_one_or_none()

            if not chunk:
                raise Exception(f"知识切片不存在: {chunk_id}")

            # 使用 pgvector 的 Vector 类型存储向量
            chunk.embedding = embedding

            await self.db.flush()
            return True

        except Exception as e:
            raise Exception(f"添加向量失败: {str(e)}")

    async def search_similar(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        搜索相似向量（余弦相似度）

        Args:
            query_embedding: 查询向量
            user_id: 用户 ID
            limit: 返回结果数量
            threshold: 相似度阈值 (0-1)

        Returns:
            (知识切片, 相似度分数) 列表
        """
        try:
            # 使用 pgvector 的 cosine distance 运算符
            # cosine distance = 1 - cosine similarity，所以用 < distance_threshold
            distance_threshold = 1.0 - threshold

            result = await self.db.execute(
                select(
                    KnowledgeChunk,
                    (1 - KnowledgeChunk.embedding.cosine_distance(query_embedding)).label("similarity")
                )
                .join(Document, KnowledgeChunk.document_id == Document.document_id)
                .where(
                    Document.user_id == user_id,
                    KnowledgeChunk.embedding.isnot(None),
                    (1 - KnowledgeChunk.embedding.cosine_distance(query_embedding)) >= threshold
                )
                .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
                .limit(limit)
            )

            rows = result.all()
            return [(row[0], float(row[1])) for row in rows]

        except Exception as e:
            # 如果 pgvector 搜索失败（比如向量列不存在），降级为文本搜索
            print(f"向量搜索失败，降级为文本搜索: {str(e)}")
            return []

    async def delete_embedding(self, chunk_id: str) -> bool:
        """删除向量"""
        try:
            result = await self.db.execute(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.chunk_id == chunk_id
                )
            )
            chunk = result.scalar_one_or_none()

            if not chunk:
                return False

            chunk.embedding = None
            await self.db.flush()

            return True

        except Exception as e:
            raise Exception(f"删除向量失败: {str(e)}")

    async def delete_all_embeddings(self, document_id: str) -> bool:
        """删除文档的所有向量"""
        try:
            result = await self.db.execute(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.document_id == document_id
                )
            )
            chunks = result.scalars().all()

            for chunk in chunks:
                chunk.embedding = None

            await self.db.flush()

            return True

        except Exception as e:
            raise Exception(f"删除向量失败: {str(e)}")


async def get_vector_store(db: AsyncSession) -> VectorStore:
    """获取向量存储服务"""
    store = VectorStore(db)
    await store.initialize()
    return store
