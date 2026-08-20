"""
Personal AI OS - Proactive Intelligence Model
主动智能模型 - 主动提醒 + 趋势预测 + 上下文感知
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class ProactiveInsight(Base):
    """主动洞察表 - 系统主动发现的信息"""
    __tablename__ = "proactive_insights"

    insight_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 洞察信息
    insight_type = Column(String(50), nullable=False)    # 类型
    title = Column(String(255), nullable=False)          # 标题
    description = Column(Text, nullable=False)           # 描述
    priority = Column(String(20), default="medium")      # 优先级: low, medium, high
    category = Column(String(50), nullable=True)         # 分类

    # 关联
    related_ids = Column(JSONB, nullable=True)           # 关联的 ID 列表
    action_suggestion = Column(Text, nullable=True)      # 建议操作

    # 状态
    is_read = Column(Boolean, default=False)             # 是否已读
    is_dismissed = Column(Boolean, default=False)        # 是否已忽略
    is_acted = Column(Boolean, default=False)            # 是否已执行建议

    # 时间戳
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 过期时间
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 索引
    __table_args__ = (
        Index("ix_insight_user_type", "user_id", "insight_type"),
        Index("ix_insight_user_unread", "user_id", "is_read"),
    )

    def __repr__(self):
        return f"<ProactiveInsight {self.title}: {self.insight_type}>"


class ContextSnapshot(Base):
    """上下文快照表 - 用户当前的工作上下文"""
    __tablename__ = "context_snapshots"

    snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 上下文信息
    current_topic = Column(String(255), nullable=True)      # 当前话题
    current_project = Column(String(255), nullable=True)    # 当前项目
    recent_documents = Column(JSONB, nullable=True)         # 最近访问的文档
    recent_topics = Column(JSONB, nullable=True)            # 最近讨论的话题
    active_memories = Column(JSONB, nullable=True)          # 活跃的记忆
    pending_decisions = Column(JSONB, nullable=True)        # 待决策

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_context_user", "user_id"),
    )

    def __repr__(self):
        return f"<ContextSnapshot {self.current_topic}>"


class TrendPrediction(Base):
    """趋势预测表 - 基于历史数据的预测"""
    __tablename__ = "trend_predictions"

    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 预测信息
    prediction_type = Column(String(50), nullable=False)   # 预测类型
    title = Column(String(255), nullable=False)            # 标题
    description = Column(Text, nullable=False)             # 描述
    confidence = Column(Float, default=0.5)                # 置信度
    evidence = Column(JSONB, nullable=True)                # 证据
    suggested_actions = Column(JSONB, nullable=True)       # 建议操作

    # 状态
    is_relevant = Column(Boolean, default=True)            # 是否相关
    user_feedback = Column(String(20), nullable=True)      # 用户反馈: useful, not_useful

    # 时间戳
    predicted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_trend_user_type", "user_id", "prediction_type"),
    )

    def __repr__(self):
        return f"<TrendPrediction {self.title}>"


# 洞察类型定义
INSIGHT_TYPES = {
    "knowledge_gap": "知识缺口",
    "memory_decay": "记忆衰退",
    "decision_pattern": "决策模式",
    "conflict_detected": "冲突检测",
    "opportunity": "机会发现",
    "reminder": "提醒事项",
    "trend": "趋势变化",
    "recommendation": "推荐建议",
}

# 预测类型定义
PREDICTION_TYPES = {
    "next_topic": "下一个话题",
    "knowledge_need": "知识需求",
    "decision_impact": "决策影响",
    "memory_relevance": "记忆相关性",
    "learning_path": "学习路径",
}
