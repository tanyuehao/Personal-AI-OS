"""
Personal AI OS - Decision Style Model
决策风格模型 - 建模用户思维方式和决策模式
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DecisionStyle(Base):
    """决策风格表 - 存储用户的决策模式分析结果"""
    __tablename__ = "decision_styles"

    # 主键
    style_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 风格维度
    risk_tolerance = Column(Float, default=0.5)        # 风险偏好 0=保守 1=冒险
    analysis_depth = Column(Float, default=0.5)         # 分析深度 0=直觉 1=深度分析
    decisiveness = Column(Float, default=0.5)           # 果断程度 0=犹豫 1=果断
    collaboration = Column(Float, default=0.5)          # 协作倾向 0=独立 1=协作
    time_preference = Column(Float, default=0.5)        # 时间偏好 0=短期 1=长期
    evidence_reliance = Column(Float, default=0.5)      # 证据依赖 0=经验 1=数据
    intuition_ratio = Column(Float, default=0.5)        # 直觉比例 0=纯分析 1=纯直觉
    emotional_influence = Column(Float, default=0.5)    # 情绪影响 0=冷静 1=情绪化

    # 综合评估
    primary_style = Column(String(50), nullable=True)   # 主要风格类型
    secondary_style = Column(String(50), nullable=True) # 次要风格类型
    style_description = Column(Text, nullable=True)     # 风格描述

    # 统计数据
    total_decisions = Column(String(20), default="0")   # 总决策数
    avg_confidence = Column(Float, default=0.5)         # 平均置信度
    avg_outcome_score = Column(Float, default=0.5)      # 平均结果评分

    # 时间戳
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 关联关系
    user = relationship("User", backref="decision_styles")

    # 索引
    __table_args__ = (
        Index("ix_decision_style_user", "user_id"),
    )

    def __repr__(self):
        return f"<DecisionStyle {self.primary_style}: risk={self.risk_tolerance:.2f}>"


class DecisionPattern(Base):
    """决策模式表 - 记录从决策中提取的具体模式"""
    __tablename__ = "decision_patterns"

    # 主键
    pattern_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 用户关联
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 模式内容
    pattern_type = Column(String(50), nullable=False)   # 模式类型
    pattern_name = Column(String(100), nullable=False)  # 模式名称
    description = Column(Text, nullable=False)          # 模式描述
    examples = Column(JSONB, nullable=True)             # 示例决策 ID 列表
    confidence = Column(Float, default=0.7)             # 置信度

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 索引
    __table_args__ = (
        Index("ix_pattern_user_type", "user_id", "pattern_type"),
    )

    def __repr__(self):
        return f"<DecisionPattern {self.pattern_name}: {self.pattern_type}>"
