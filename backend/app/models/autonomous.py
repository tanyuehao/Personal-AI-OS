"""
Personal AI OS - Autonomous Action Model
自主行动模型 - 行动规划 + 执行 + 监控 + 安全约束
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID

from app.core.database import Base


class ActionPlan(Base):
    """行动计划表 - AI 规划的行动"""
    __tablename__ = "action_plans"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 行动信息
    title = Column(String(255), nullable=False)           # 行动标题
    description = Column(Text, nullable=True)             # 行动描述
    action_type = Column(String(50), nullable=False)      # 行动类型
    priority = Column(String(20), default="medium")       # 优先级

    # 行动详情
    steps = Column(JSONB, nullable=True)                  # 行动步骤
    parameters = Column(JSONB, nullable=True)             # 参数
    expected_outcome = Column(Text, nullable=True)        # 预期结果

    # 安全约束
    requires_approval = Column(Boolean, default=False)    # 是否需要用户批准
    risk_level = Column(String(20), default="low")        # 风险等级
    scope = Column(String(50), default="internal")        # 作用范围

    # 状态
    status = Column(String(20), default="pending")        # pending, approved, executing, completed, failed, cancelled
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_action_plan_user_status", "user_id", "status"),
    )

    def __repr__(self):
        return f"<ActionPlan {self.title}: {self.status}>"


class ActionResult(Base):
    """行动结果表 - 记录行动执行的结果"""
    __tablename__ = "action_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("action_plans.plan_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 结果信息
    status = Column(String(20), nullable=False)           # success, partial, failed
    output = Column(Text, nullable=True)                  # 输出结果
    error = Column(Text, nullable=True)                   # 错误信息
    side_effects = Column(JSONB, nullable=True)           # 副作用

    # 学习
    lesson_learned = Column(Text, nullable=True)          # 学到的教训
    would_repeat = Column(Boolean, nullable=True)         # 是否会重复执行

    # 时间戳
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 关联关系
    plan = relationship("ActionPlan", backref="results")

    __table_args__ = (
        Index("ix_action_result_plan", "plan_id"),
    )

    def __repr__(self):
        return f"<ActionResult {self.status}>"


class SafetyRule(Base):
    """安全规则表 - 定义行动的安全约束"""
    __tablename__ = "safety_rules"

    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 规则信息
    rule_name = Column(String(100), nullable=False)       # 规则名称
    description = Column(Text, nullable=True)             # 规则描述
    rule_type = Column(String(50), nullable=False)        # 规则类型
    condition = Column(Text, nullable=False)              # 条件
    action = Column(String(50), nullable=False)           # 动作：allow, deny, require_approval

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_safety_rule_user_type", "user_id", "rule_type"),
    )

    def __repr__(self):
        return f"<SafetyRule {self.rule_name}: {self.action}>"


# 行动类型定义
ACTION_TYPES = {
    "document_management": "文档管理",
    "memory_management": "记忆管理",
    "knowledge_organization": "知识整理",
    "decision_analysis": "决策分析",
    "learning_optimization": "学习优化",
    "report_generation": "报告生成",
    "reminder_setup": "提醒设置",
    "data_export": "数据导出",
    "system_optimization": "系统优化",
}

# 安全规则类型
SAFETY_RULE_TYPES = {
    "action_restriction": "行动限制",
    "time_restriction": "时间限制",
    "scope_restriction": "范围限制",
    "approval_required": "需要批准",
    "notification_required": "需要通知",
}

# 风险等级
RISK_LEVELS = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
    "critical": "高危风险",
}
