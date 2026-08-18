"""
Personal AI OS - Knowledge Chunk Model
知识切片数据模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from app.core.database import Base


class KnowledgeChunk(Base):
    """知识切片表"""
    __tablename__ = "knowledge_chunks"

    # 主键
    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 文档关联
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False, index=True)

    # 内容
    content = Column(Text, nullable=False)

    # 向量嵌入（pgvector）
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)

    # 元数据
    topic = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    # 位置信息
    chunk_index = Column(Integer, default=0)
    start_page = Column(Integer, nullable=True)
    end_page = Column(Integer, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 关联关系
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<KnowledgeChunk {self.chunk_id}>"
