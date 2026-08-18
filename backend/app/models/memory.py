"""
Personal AI OS - Memory Model
记忆数据模型
"""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from app.core.types import CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MemoryType(str, enum.Enum):
    """记忆类型"""
    FACT = "FACT"              # 事实记忆
    EXPERIENCE = "EXPERIENCE"  # 经验记忆
    OPINION = "OPINION"        # 观点记忆
    DECISION = "DECISION"      # 决策记忆
    PREFERENCE = "PREFERENCE"  # 偏好记忆


class Memory(Base):
    """记忆表"""
    __tablename__ = "memories"
    
    # 主键
    memory_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # 记忆内容
    memory_type = Column(String(20), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # 来源
    source = Column(String(255), nullable=True)  # 来源描述
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=True)
    
    # 权重
    importance = Column(Float, default=0.5)  # 重要程度 0-1
    confidence = Column(Float, default=0.8)  # 可信程度 0-1
    frequency = Column(Integer, default=1)  # 出现频率
    
    # 时间
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 确认状态
    is_confirmed = Column(String(20), default="PENDING")  # PENDING, CONFIRMED, REJECTED
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="memories")
    
    def __repr__(self):
        return f"<Memory {self.memory_type}: {self.content[:50]}>"
