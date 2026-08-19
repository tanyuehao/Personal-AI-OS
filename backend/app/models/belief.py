"""
Personal AI OS - Belief Model
观点/信念数据模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Belief(Base):
    """观点/信念表"""
    __tablename__ = "beliefs"
    
    # 主键
    belief_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # 观点内容
    topic = Column(String(255), nullable=False)  # 主题
    content = Column(Text, nullable=False)  # 观点内容
    
    # 评分
    confidence = Column(Float, default=0.7)  # 可信度 0-1
    
    # 证据
    supporting_evidence = Column(JSONB, nullable=True)  # 支持证据列表
    opposing_evidence = Column(JSONB, nullable=True)  # 反对证据列表
    
    # 变化历史
    evolution_history = Column(JSONB, nullable=True)  # 演化历史
    
    # 状态
    status = Column(String(20), default="ACTIVE")  # CANDIDATE, ACTIVE, ARCHIVED, REVISED
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 复合索引
    __table_args__ = (
        Index("ix_belief_user_status", "user_id", "status"),
    )

    def __repr__(self):
        return f"<Belief {self.topic}: {self.content[:50]}>"


class BeliefHistory(Base):
    """观点变化历史表"""
    __tablename__ = "belief_history"
    
    # 主键
    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 观点关联
    belief_id = Column(UUID(as_uuid=True), ForeignKey("beliefs.belief_id"), nullable=False, index=True)
    
    # 变化内容
    old_content = Column(Text, nullable=False)
    new_content = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # 关联关系
    belief = relationship("Belief", backref="histories")
    
    def __repr__(self):
        return f"<BeliefHistory {self.belief_id}>"
