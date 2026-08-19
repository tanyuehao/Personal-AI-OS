"""
Personal AI OS - Memory Network Model
记忆网络模型 - 遗忘曲线 + 记忆强化 + 联想召回
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MemoryAssociation(Base):
    """记忆关联表 - 记忆之间的联想关系"""
    __tablename__ = "memory_associations"

    association_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 关联信息
    source_memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.memory_id"), nullable=False, index=True)
    target_memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.memory_id"), nullable=False, index=True)
    association_type = Column(String(50), nullable=False)  # 关联类型
    strength = Column(Float, default=1.0)                  # 关联强度 0-1
    context = Column(Text, nullable=True)                  # 关联上下文

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activated = Column(DateTime(timezone=True), nullable=True)  # 最后激活时间

    # 关联关系
    source_memory = relationship("Memory", foreign_keys=[source_memory_id], backref="outgoing_associations")
    target_memory = relationship("Memory", foreign_keys=[target_memory_id], backref="incoming_associations")

    # 索引
    __table_args__ = (
        Index("ix_assoc_source", "source_memory_id"),
        Index("ix_assoc_target", "target_memory_id"),
    )

    def __repr__(self):
        return f"<MemoryAssociation {self.source_memory_id} -> {self.target_memory_id}>"


class MemoryStrength(Base):
    """记忆强度表 - 跟踪记忆的遗忘曲线"""
    __tablename__ = "memory_strengths"

    strength_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.memory_id"), nullable=False, index=True)

    # 强度指标
    base_strength = Column(Float, default=1.0)           # 基础强度
    current_strength = Column(Float, default=1.0)        # 当前强度（考虑遗忘）
    decay_rate = Column(Float, default=0.1)              # 衰减速率
    last_reviewed = Column(DateTime(timezone=True), nullable=True)  # 最后复习时间
    review_count = Column(String(20), default="0")       # 复习次数

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 索引
    __table_args__ = (
        Index("ix_strength_memory", "memory_id"),
    )

    def __repr__(self):
        return f"<MemoryStrength {self.memory_id}: {self.current_strength:.2f}>"


class MemoryCluster(Base):
    """记忆聚类表 - 将相似记忆分组"""
    __tablename__ = "memory_clusters"

    cluster_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 聚类信息
    name = Column(String(255), nullable=False)            # 聚类名称
    description = Column(Text, nullable=True)              # 聚类描述
    cluster_type = Column(String(50), nullable=False)     # 聚类类型
    memory_ids = Column(JSONB, nullable=True)             # 包含的记忆ID列表
    centroid = Column(JSONB, nullable=True)               # 聚类中心（可选）

    # 统计
    memory_count = Column(String(20), default="0")
    avg_importance = Column(Float, default=0.5)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<MemoryCluster {self.name}: {self.cluster_type}>"


# 关联类型定义
ASSOCIATION_TYPES = {
    "temporal": "时间关联",      # 同一时间段的记忆
    "semantic": "语义关联",      # 内容相似的记忆
    "causal": "因果关联",        # 有因果关系的记忆
    "emotional": "情感关联",     # 情感相似的记忆
    "contextual": "情境关联",    # 相同情境下的记忆
    "contrastive": "对比关联",   # 对比鲜明的记忆
}
