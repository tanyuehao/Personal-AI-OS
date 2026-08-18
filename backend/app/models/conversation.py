"""
Personal AI OS - Conversation Model
对话数据模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Conversation(Base):
    """对话表"""
    __tablename__ = "conversations"
    
    # 主键
    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # 对话信息
    title = Column(String(255), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # 关联关系
    messages = relationship("ConversationMessage", back_populates="conversation", lazy="selectin")
    
    def __repr__(self):
        return f"<Conversation {self.title}>"


class ConversationMessage(Base):
    """对话消息表"""
    __tablename__ = "conversation_messages"
    
    # 主键
    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 对话关联
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    
    # 消息内容
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # 元数据
    sources = Column(JSONB, nullable=True)  # 引用来源
    metadata_ = Column("metadata", JSONB, nullable=True)  # 其他元数据
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ConversationMessage {self.role}: {self.content[:50]}>"
