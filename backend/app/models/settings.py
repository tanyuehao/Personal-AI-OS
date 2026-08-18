"""
Personal AI OS - User Settings Model
用户设置模型 - 存储 API Key 等配置
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserSettings(Base):
    """用户设置表"""
    __tablename__ = "user_settings"
    
    # 主键
    settings_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), unique=True, nullable=False, index=True)
    
    # AI 模型配置
    ai_provider = Column(String(50), default="siliconflow")  # siliconflow, deepseek
    
    # 硅基流动配置
    siliconflow_api_key = Column(Text, nullable=True)  # 加密存储
    siliconflow_api_base = Column(String(255), default="https://api.siliconflow.cn/v1")
    
    # DeepSeek 配置
    deepseek_api_key = Column(Text, nullable=True)  # 加密存储
    deepseek_api_base = Column(String(255), default="https://api.deepseek.com")
    
    # 模型选择
    llm_model = Column(String(100), default="deepseek-ai/DeepSeek-V3")
    embedding_model = Column(String(100), default="BAAI/bge-m3")
    reranker_enabled = Column(Boolean, default=True)
    reranker_model = Column(String(100), default="BAAI/bge-reranker-v2-m3")
    
    # 图片模型
    image_model_enabled = Column(Boolean, default=True)
    image_model = Column(String(100), default="Kwai-Kolors/Kolors")
    
    # 高级设置
    temperature = Column(String(10), default="0.7")
    max_tokens = Column(String(10), default="2000")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<UserSettings {self.user_id}>"


class APIKeyHistory(Base):
    """API Key 使用记录"""
    __tablename__ = "api_key_history"
    
    # 主键
    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # 使用记录
    provider = Column(String(50), nullable=False)  # siliconflow, deepseek
    model = Column(String(100), nullable=False)
    tokens_used = Column(String(20), default="0")
    cost = Column(String(20), default="0")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<APIKeyHistory {self.provider}/{self.model}>"
