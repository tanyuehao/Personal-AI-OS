"""
Personal AI OS - Prediction Model
预测需求模型 - 预测用户下一步行动 + 提前准备信息
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class UserPattern(Base):
    """用户行为模式表 - 识别用户的常见行为模式"""
    __tablename__ = "user_patterns"

    pattern_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 模式信息
    pattern_type = Column(String(50), nullable=False)    # 模式类型
    pattern_name = Column(String(100), nullable=False)   # 模式名称
    description = Column(Text, nullable=False)           # 模式描述
    frequency = Column(Float, default=0.5)               # 频率 0-1
    confidence = Column(Float, default=0.5)              # 置信度 0-1

    # 模式数据
    triggers = Column(JSONB, nullable=True)              # 触发条件
    actions = Column(JSONB, nullable=True)               # 行为序列
    context = Column(JSONB, nullable=True)               # 上下文信息
    examples = Column(JSONB, nullable=True)              # 示例

    # 时间戳
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_prediction_pattern_user_type", "user_id", "pattern_type"),
    )

    def __repr__(self):
        return f"<UserPattern {self.pattern_name}: {self.pattern_type}>"


class NeedPrediction(Base):
    """需求预测表 - 预测用户下一步可能需要什么"""
    __tablename__ = "need_predictions"

    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 预测信息
    prediction_type = Column(String(50), nullable=False)   # 预测类型
    title = Column(String(255), nullable=False)            # 标题
    description = Column(Text, nullable=False)             # 描述
    priority = Column(String(20), default="medium")        # 优先级
    confidence = Column(Float, default=0.5)                # 置信度

    # 预测详情
    predicted_need = Column(Text, nullable=False)          # 预测的需求
    suggested_action = Column(Text, nullable=True)         # 建议行动
    relevant_resources = Column(JSONB, nullable=True)      # 相关资源
    time_horizon = Column(String(50), nullable=True)       # 时间范围

    # 状态
    is_relevant = Column(Boolean, default=True)            # 是否相关
    user_feedback = Column(String(20), nullable=True)      # 用户反馈
    is_acted = Column(Boolean, default=False)              # 是否已执行

    # 时间戳
    predicted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_prediction_user_type", "user_id", "prediction_type"),
    )

    def __repr__(self):
        return f"<NeedPrediction {self.title}>"


class PreparedInfo(Base):
    """预准备信息表 - 提前准备好的信息"""
    __tablename__ = "prepared_infos"

    info_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 信息内容
    info_type = Column(String(50), nullable=False)        # 信息类型
    title = Column(String(255), nullable=False)           # 标题
    content = Column(Text, nullable=False)                # 内容
    source = Column(JSONB, nullable=True)                 # 来源

    # 关联
    related_prediction_id = Column(UUID(as_uuid=True), nullable=True)
    related_memory_ids = Column(JSONB, nullable=True)

    # 状态
    is_used = Column(Boolean, default=False)              # 是否已使用
    use_count = Column(String(20), default="0")           # 使用次数

    # 时间戳
    prepared_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_prepared_user_type", "user_id", "info_type"),
    )

    def __repr__(self):
        return f"<PreparedInfo {self.title}>"


# 预测类型定义
PREDICTION_TYPES = {
    "next_action": "下一步行动",
    "information_need": "信息需求",
    "decision_pending": "待决策事项",
    "learning_opportunity": "学习机会",
    "risk_alert": "风险提醒",
    "optimization": "优化建议",
}

# 模式类型定义
PATTERN_TYPES = {
    "daily_routine": "日常规律",
    "work_pattern": "工作模式",
    "learning_pattern": "学习模式",
    "decision_pattern": "决策模式",
    "communication_pattern": "沟通模式",
    "preference_pattern": "偏好模式",
}
