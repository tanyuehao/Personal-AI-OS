"""
Personal AI OS - Document Model
文档数据模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    """文档状态"""
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    # 主键
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # 文件信息
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    
    # 元数据
    source = Column(String(100), nullable=True)  # 来源：upload, api, etc.
    category = Column(String(100), nullable=True)  # 分类
    
    # 内容
    content = Column(Text, nullable=True)  # 原始文本内容
    summary = Column(Text, nullable=True)  # AI 生成的摘要
    
    # 状态
    status = Column(String(20), default=DocumentStatus.UPLOADING.value, nullable=False)
    status_message = Column(Text, nullable=True)
    
    # 元数据
    metadata_ = Column("metadata", JSONB, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    user = relationship("User", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", lazy="selectin")
    
    def __repr__(self):
        return f"<Document {self.file_name}>"
