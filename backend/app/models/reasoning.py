"""
Personal AI OS - Reasoning Model
自主推理模型 - 独立分析 + 多步推理 + 类比推理
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class ReasoningSession(Base):
    """推理会话表 - 记录一次完整的推理过程"""
    __tablename__ = "reasoning_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 推理信息
    query = Column(Text, nullable=False)                  # 推理问题
    reasoning_type = Column(String(50), nullable=False)   # 推理类型
    conclusion = Column(Text, nullable=True)              # 结论
    confidence = Column(Float, default=0.5)               # 置信度

    # 推理链
    reasoning_steps = Column(JSONB, nullable=True)        # 推理步骤
    evidence_used = Column(JSONB, nullable=True)          # 使用的证据
    analogies_used = Column(JSONB, nullable=True)         # 使用的类比

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_reasoning_user_type", "user_id", "reasoning_type"),
    )

    def __repr__(self):
        return f"<ReasoningSession {self.reasoning_type}: {self.query[:50]}>"


class ReasoningChain(Base):
    """推理链表 - 多步推理的每一步"""
    __tablename__ = "reasoning_chains"

    chain_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("reasoning_sessions.session_id"), nullable=False, index=True)

    # 步骤信息
    step_number = Column(String(10), nullable=False)      # 步骤编号
    step_type = Column(String(50), nullable=False)        # 步骤类型
    content = Column(Text, nullable=False)                # 步骤内容
    confidence = Column(Float, default=0.5)               # 置信度
    evidence = Column(JSONB, nullable=True)               # 支持证据

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 关联关系
    session = relationship("ReasoningSession", backref="steps")

    __table_args__ = (
        Index("ix_chain_session", "session_id"),
    )

    def __repr__(self):
        return f"<ReasoningChain Step {self.step_number}: {self.step_type}>"


class Analogy(Base):
    """类比表 - 历史经验的类比"""
    __tablename__ = "analogies"

    analogy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 类比信息
    source_situation = Column(Text, nullable=False)      # 原始情境
    target_situation = Column(Text, nullable=False)      # 目标情境
    similarity_score = Column(Float, default=0.5)        # 相似度
    lesson = Column(Text, nullable=True)                 # 经验教训
    outcome = Column(Text, nullable=True)                # 原始结果

    # 关联
    source_decision_id = Column(UUID(as_uuid=True), nullable=True)
    source_memory_id = Column(UUID(as_uuid=True), nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_analogy_user", "user_id"),
    )

    def __repr__(self):
        return f"<Analogy similarity={self.similarity_score:.2f}>"


class ProactiveSuggestion(Base):
    """主动建议表 - 基于推理的主动建议"""
    __tablename__ = "proactive_suggestions"

    suggestion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 建议信息
    title = Column(String(255), nullable=False)           # 标题
    description = Column(Text, nullable=False)            # 描述
    suggestion_type = Column(String(50), nullable=False)  # 类型
    priority = Column(String(20), default="medium")       # 优先级
    confidence = Column(Float, default=0.5)               # 置信度
    reasoning = Column(Text, nullable=True)               # 推理过程
    action_items = Column(JSONB, nullable=True)           # 行动项

    # 状态
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    user_feedback = Column(String(20), nullable=True)     # useful, not_useful

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_suggestion_user_type", "user_id", "suggestion_type"),
    )

    def __repr__(self):
        return f"<ProactiveSuggestion {self.title}>"


# 推理类型定义
REASONING_TYPES = {
    "analytical": "分析推理",
    "analogical": "类比推理",
    "causal": "因果推理",
    "inductive": "归纳推理",
    "deductive": "演绎推理",
    "abductive": "溯因推理",
}

# 推理步骤类型
REASONING_STEP_TYPES = {
    "observation": "观察",
    "hypothesis": "假设",
    "evidence": "证据",
    "analysis": "分析",
    "inference": "推断",
    "conclusion": "结论",
}

# 建议类型
SUGGESTION_TYPES = {
    "action": "行动建议",
    "learning": "学习建议",
    "decision": "决策建议",
    "improvement": "改进建议",
    "exploration": "探索建议",
}
