"""
Personal AI OS - Context Awareness Model
上下文感知模型 - 实时检测用户当前工作状态
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class WorkSession(Base):
    """工作会话表 - 记录用户的工作会话"""
    __tablename__ = "work_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 会话信息
    session_type = Column(String(50), nullable=False)     # 会话类型
    title = Column(String(255), nullable=True)            # 会话标题
    description = Column(Text, nullable=True)             # 会话描述

    # 状态
    status = Column(String(20), default="active")         # active, paused, completed
    mood = Column(String(50), nullable=True)              # 当前心情/状态
    energy_level = Column(Float, default=0.5)             # 精力水平 0-1

    # 上下文
    current_task = Column(Text, nullable=True)            # 当前任务
    focus_area = Column(String(255), nullable=True)       # 焦点领域
    tools_used = Column(JSONB, nullable=True)             # 使用的工具
    related_documents = Column(JSONB, nullable=True)      # 相关文档
    related_memories = Column(JSONB, nullable=True)       # 相关记忆

    # 时间戳
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_active_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_work_session_user_status", "user_id", "status"),
    )

    def __repr__(self):
        return f"<WorkSession {self.session_type}: {self.status}>"


class ActivityLog(Base):
    """活动日志表 - 记录用户的活动"""
    __tablename__ = "activity_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("work_sessions.session_id"), nullable=True, index=True)

    # 活动信息
    activity_type = Column(String(50), nullable=False)    # 活动类型
    action = Column(String(100), nullable=False)          # 具体操作
    details = Column(Text, nullable=True)                 # 详情
    duration = Column(Float, nullable=True)               # 持续时间（秒）

    # 上下文
    page = Column(String(100), nullable=True)             # 页面
    tool = Column(String(100), nullable=True)             # 工具
    data = Column(JSONB, nullable=True)                   # 相关数据

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_activity_user_type", "user_id", "activity_type"),
        Index("ix_activity_user_time", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<ActivityLog {self.activity_type}: {self.action}>"


class UserFocus(Base):
    """用户焦点表 - 识别用户当前的关注点"""
    __tablename__ = "user_focuses"

    focus_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 焦点信息
    focus_type = Column(String(50), nullable=False)       # 焦点类型
    focus_name = Column(String(255), nullable=False)      # 焦点名称
    description = Column(Text, nullable=True)             # 描述
    priority = Column(Float, default=0.5)                 # 优先级 0-1

    # 状态
    is_active = Column(Boolean, default=True)             # 是否活跃
    confidence = Column(Float, default=0.5)               # 置信度

    # 时间戳
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_active_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_focus_user_type", "user_id", "focus_type"),
    )

    def __repr__(self):
        return f"<UserFocus {self.focus_name}: {self.focus_type}>"


# 会话类型定义
SESSION_TYPES = {
    "coding": "编码",
    "research": "研究",
    "writing": "写作",
    "learning": "学习",
    "planning": "规划",
    "reviewing": "复盘",
    "meeting": "会议",
    "break": "休息",
}

# 活动类型定义
ACTIVITY_TYPES = {
    "document_upload": "文档上传",
    "document_read": "文档阅读",
    "chat_message": "对话消息",
    "memory_create": "记忆创建",
    "decision_make": "决策制定",
    "knowledge_search": "知识搜索",
    "ai_interaction": "AI交互",
    "setting_change": "设置变更",
}

# 焦点类型定义
FOCUS_TYPES = {
    "topic": "话题",
    "project": "项目",
    "task": "任务",
    "skill": "技能",
    "person": "人物",
    "document": "文档",
}
