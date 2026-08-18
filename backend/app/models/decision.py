"""
Personal AI OS - Decision Model
决策数据模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class Decision(Base):
    """决策记录表"""
    __tablename__ = "decisions"
    
    # 主键
    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # 决策内容
    problem = Column(Text, nullable=False)  # 问题/背景
    background = Column(Text, nullable=True)  # 背景信息
    options = Column(JSONB, nullable=True)  # 备选方案列表
    choice = Column(Text, nullable=True)  # 选择的方案
    reasoning = Column(Text, nullable=True)  # 判断依据
    risk = Column(Text, nullable=True)  # 风险因素
    
    # 结果
    expected_result = Column(Text, nullable=True)  # 预期结果
    actual_result = Column(Text, nullable=True)  # 实际结果
    lesson = Column(Text, nullable=True)  # 经验教训
    
    # 分类
    category = Column(String(100), nullable=True)  # 决策类别
    tags = Column(JSONB, nullable=True)  # 标签
    
    # 时间戳
    decision_date = Column(DateTime(timezone=True), nullable=True)  # 决策日期
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f"<Decision {self.problem[:50]}>"
