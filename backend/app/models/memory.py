"""
Personal AI OS - Memory Model
记忆数据模型
"""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index, CheckConstraint, UniqueConstraint
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
    summary = Column(Text, nullable=True)

    # 断言类型 (server-controlled, default LEGACY_UNKNOWN)
    assertion_kind = Column(String(30), nullable=False, default="LEGACY_UNKNOWN")

    # 来源
    source = Column(String(255), nullable=True)  # 来源描述
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True)

    # 权重
    importance = Column(Float, default=0.5)  # 重要程度 0-1
    confidence = Column(Float, default=0.8)  # 可信程度 0-1
    frequency = Column(Integer, default=1)  # 出现频率

    # 时间
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # 确认状态
    is_confirmed = Column(String(20), default="PENDING")  # PENDING, CONFIRMED, REJECTED, ARCHIVED, SUPERSEDED

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 关联关系
    user = relationship("User", back_populates="memories")
    evidence_records = relationship("MemoryEvidence", back_populates="memory", cascade="all, delete-orphan")

    # 复合索引与约束（优化常用查询）
    __table_args__ = (
        UniqueConstraint("memory_id", "user_id", name="uq_memory_user"),
        Index("ix_memory_user_confirmed", "user_id", "is_confirmed"),
        Index("ix_memory_user_type", "user_id", "memory_type"),
        Index("ix_memory_user_importance", "user_id", "importance"),
        Index("ix_memory_assertion_kind", "user_id", "assertion_kind"),
        CheckConstraint("is_confirmed IN ('PENDING','CONFIRMED','REJECTED','ARCHIVED','SUPERSEDED')", name="chk_memory_status"),
        CheckConstraint("assertion_kind IN ('USER_STATED','OBSERVED','INFERRED','LEGACY_UNKNOWN')", name="chk_assertion_kind"),
        CheckConstraint("memory_type IN ('FACT','EXPERIENCE','OPINION','DECISION','PREFERENCE')", name="chk_memory_type"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_memory_confidence"),
        CheckConstraint("importance >= 0.0 AND importance <= 1.0", name="chk_memory_importance"),
    )

    def __repr__(self):
        return f"<Memory {self.memory_type}: {self.content[:50]}>"
