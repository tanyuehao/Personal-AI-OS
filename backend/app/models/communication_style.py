"""
Personal AI OS - Communication Style Model
沟通风格和语言习惯模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class CommunicationStyle(Base):
    """沟通风格表 - 用户的沟通方式特征"""
    __tablename__ = "communication_styles"

    style_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 正式程度
    formality = Column(Float, default=0.5)           # 0=非常口语 1=非常正式

    # 直接程度
    directness = Column(Float, default=0.5)          # 0=委婉 1=直接

    # 情感表达
    emotional_expression = Column(Float, default=0.5) # 0=冷静 1=情感丰富

    # 详细程度
    verbosity = Column(Float, default=0.5)            # 0=简洁 1=详细

    # 幽默感
    humor = Column(Float, default=0.5)                # 0=严肃 1=幽默

    # 专业性
    professionalism = Column(Float, default=0.5)      # 0=随意 1=专业

    # 互动偏好
    question_asking = Column(Float, default=0.5)      # 0=少问 1=多问

    # 沟通模式
    preferred_mode = Column(String(50), nullable=True)  # 文字/语音/混合
    response_length = Column(String(50), nullable=True) # 简短/适中/详细

    # 时间戳
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_comm_style_user", "user_id"),
    )

    def __repr__(self):
        return f"<CommunicationStyle formality={self.formality:.2f}>"


class LanguageHabit(Base):
    """语言习惯表 - 用户的用词和表达习惯"""
    __tablename__ = "language_habits"

    habit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 习惯类型
    habit_type = Column(String(50), nullable=False)    # 类型
    habit_name = Column(String(100), nullable=False)   # 名称
    pattern = Column(Text, nullable=False)             # 模式/示例
    frequency = Column(Float, default=0.5)             # 频率 0-1
    examples = Column(JSONB, nullable=True)            # 示例列表

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_lang_habit_user_type", "user_id", "habit_type"),
    )

    def __repr__(self):
        return f"<LanguageHabit {self.habit_name}: {self.habit_type}>"


class ConversationPattern(Base):
    """对话模式表 - 用户的对话习惯"""
    __tablename__ = "conversation_patterns"

    pattern_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 模式信息
    pattern_type = Column(String(50), nullable=False)   # 模式类型
    pattern_name = Column(String(100), nullable=False)  # 模式名称
    description = Column(Text, nullable=False)          # 模式描述
    examples = Column(JSONB, nullable=True)             # 示例
    confidence = Column(Float, default=0.7)             # 置信度

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_conv_pattern_user_type", "user_id", "pattern_type"),
    )

    def __repr__(self):
        return f"<ConversationPattern {self.pattern_name}>"


# 沟通风格类型定义
COMMUNICATION_STYLES = {
    "formal": "正式型",
    "casual": "随意型",
    "direct": "直接型",
    "indirect": "委婉型",
    "analytical": "分析型",
    "emotional": "情感型",
    "concise": "简洁型",
    "detailed": "详细型",
    "humorous": "幽默型",
    "professional": "专业型",
}

# 语言习惯类型定义
LANGUAGE_HABIT_TYPES = {
    "vocabulary": "词汇偏好",
    "phrase": "常用短语",
    "sentence_pattern": "句式模式",
    "greeting": "问候方式",
    "closing": "结束语",
    "filler": "填充词",
    "emphasis": "强调方式",
    "transition": "过渡词",
}

# 对话模式类型定义
CONVERSATION_PATTERN_TYPES = {
    "greeting": "开场模式",
    "question_asking": "提问模式",
    "explanation": "解释模式",
    "agreement": "同意模式",
    "disagreement": "反对模式",
    "request": "请求模式",
    "complaint": "抱怨模式",
    "gratitude": "感谢模式",
}
