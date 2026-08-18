"""
Personal AI OS - User Model
用户数据模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text
from app.core.types import CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    # 主键
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基础信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 个人信息
    avatar = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    documents = relationship("Document", back_populates="user", lazy="selectin")
    memories = relationship("Memory", back_populates="user", lazy="selectin")
    
    def __repr__(self):
        return f"<User {self.username}>"
