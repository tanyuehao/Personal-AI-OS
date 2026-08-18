"""
Personal AI OS - Agent Model
Agent 数据模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class AgentTask(Base):
    """Agent 任务表"""
    __tablename__ = "agent_tasks"
    
    # 主键
    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Agent 类型
    agent_type = Column(String(50), nullable=False)  # business, investment, writing, review
    
    # 任务内容
    title = Column(String(255), nullable=True)
    input_text = Column(Text, nullable=False)
    context = Column(JSONB, nullable=True)  # 上下文信息
    
    # 执行结果
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    result = Column(Text, nullable=True)
    steps = Column(JSONB, nullable=True)  # 执行步骤记录
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<AgentTask {self.agent_type}: {self.title}>"
