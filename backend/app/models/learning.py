"""
Personal AI OS - Learning Model
持续学习模型 - 从交互中学习和改进
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class LearningEvent(Base):
    """学习事件表 - 记录每次学习的事件"""
    __tablename__ = "learning_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 事件信息
    event_type = Column(String(50), nullable=False)      # 事件类型
    source = Column(String(50), nullable=False)          # 来源
    content = Column(Text, nullable=False)               # 学习内容
    impact = Column(Float, default=0.5)                  # 影响程度 0-1

    # 关联
    related_memory_id = Column(UUID(as_uuid=True), nullable=True)
    related_belief_id = Column(UUID(as_uuid=True), nullable=True)

    # 状态
    is_applied = Column(Boolean, default=False)          # 是否已应用

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_learning_event_user_type", "user_id", "event_type"),
    )

    def __repr__(self):
        return f"<LearningEvent {self.event_type}: {self.content[:50]}>"


class Correction(Base):
    """修正记录表 - 用户对 AI 的修正"""
    __tablename__ = "corrections"

    correction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 修正信息
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    original_ai_response = Column(Text, nullable=False)    # AI 原始回答
    user_correction = Column(Text, nullable=False)          # 用户修正
    correction_type = Column(String(50), nullable=False)    # 修正类型
    lesson_learned = Column(Text, nullable=True)            # 学到的教训

    # 状态
    is_applied = Column(Boolean, default=False)             # 是否已应用到模型

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_correction_user", "user_id"),
    )

    def __repr__(self):
        return f"<Correction {self.correction_type}: {self.user_correction[:50]}>"


class Preference(Base):
    """偏好表 - 用户的偏好和喜好"""
    __tablename__ = "preferences"

    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 偏好信息
    category = Column(String(50), nullable=False)         # 偏好类别
    key = Column(String(100), nullable=False)             # 偏好键
    value = Column(Text, nullable=False)                  # 偏好值
    confidence = Column(Float, default=0.7)               # 置信度
    source = Column(String(50), nullable=True)            # 来源

    # 统计
    mention_count = Column(String(20), default="1")       # 被提及次数
    last_confirmed = Column(DateTime(timezone=True), nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_preference_user_category", "user_id", "category"),
    )

    def __repr__(self):
        return f"<Preference {self.category}/{self.key}: {self.value}>"


class Feedback(Base):
    """反馈表 - 用户对 AI 回答的反馈"""
    __tablename__ = "feedbacks"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 反馈信息
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    message_id = Column(UUID(as_uuid=True), nullable=True)
    rating = Column(Float, nullable=False)                 # 评分 1-5
    comment = Column(Text, nullable=True)                  # 评论
    feedback_type = Column(String(50), default="quality")  # 反馈类型

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_feedback_user", "user_id"),
    )

    def __repr__(self):
        return f"<Feedback rating={self.rating}>"


class UserCognitiveModel(Base):
    """用户认知模型表 - 综合的用户画像"""
    __tablename__ = "user_cognitive_models"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)

    # 认知特征
    thinking_style = Column(String(50), nullable=True)      # 思维风格
    learning_style = Column(String(50), nullable=True)      # 学习风格
    communication_style = Column(String(50), nullable=True) # 沟通风格
    decision_style = Column(String(50), nullable=True)      # 决策风格

    # 知识水平
    expertise_areas = Column(JSONB, nullable=True)           # 专业领域
    knowledge_depth = Column(Float, default=0.5)             # 知识深度
    learning_rate = Column(Float, default=0.5)               # 学习速率

    # 个性化参数
    response_preference = Column(JSONB, nullable=True)       # 回答偏好
    content_preference = Column(JSONB, nullable=True)        # 内容偏好

    # 统计
    total_interactions = Column(String(20), default="0")     # 总交互次数
    total_learning_events = Column(String(20), default="0")  # 总学习事件数
    model_version = Column(String(20), default="1.0")        # 模型版本

    # 时间戳
    last_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_cognitive_model_user", "user_id"),
    )

    def __repr__(self):
        return f"<UserCognitiveModel {self.thinking_style}/{self.learning_style}>"


# 学习事件类型定义
LEARNING_EVENT_TYPES = {
    "new_knowledge": "新知识获取",
    "preference_learned": "偏好学习",
    "correction_applied": "修正应用",
    "pattern_discovered": "模式发现",
    "model_updated": "模型更新",
    "feedback_received": "反馈接收",
}

# 修正类型定义
CORRECTION_TYPES = {
    "factual": "事实修正",
    "preference": "偏好修正",
    "style": "风格修正",
    "tone": "语气修正",
    "content": "内容修正",
}
