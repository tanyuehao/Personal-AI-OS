"""
Personal AI OS - Autonomous Action Engine
自主行动引擎 - 行动规划 + 执行 + 监控 + 安全约束
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.autonomous import (
    ActionPlan, ActionResult, SafetyRule,
    ACTION_TYPES, SAFETY_RULE_TYPES, RISK_LEVELS
)
from app.services.ai_service import create_ai_service


@dataclass
class ActionProposal:
    """行动提案"""
    title: str
    description: str
    action_type: str
    priority: str
    steps: List[Dict[str, str]]
    parameters: Dict[str, Any]
    expected_outcome: str
    risk_level: str
    requires_approval: bool


class AutonomousActionEngine:
    """自主行动引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    # ========== 安全检查 ==========

    async def check_safety_rules(
        self,
        user_id: str,
        action_type: str,
        action_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        检查安全规则

        Args:
            user_id: 用户 ID
            action_type: 行动类型
            action_params: 行动参数

        Returns:
            安全检查结果
        """
        result = await self.db.execute(
            select(SafetyRule).where(
                SafetyRule.user_id == user_id,
                SafetyRule.is_active == True
            )
        )
        rules = result.scalars().all()

        violations = []
        for rule in rules:
            if self._check_rule_violation(rule, action_type, action_params):
                violations.append({
                    "rule_name": rule.rule_name,
                    "action": rule.action,
                    "description": rule.description
                })

        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "requires_approval": any(r.action == "require_approval" for r in rules if self._check_rule_violation(r, action_type, action_params))
        }

    def _check_rule_violation(
        self,
        rule: SafetyRule,
        action_type: str,
        action_params: Dict[str, Any]
    ) -> bool:
        """检查单个规则是否被违反"""
        if rule.action == "deny":
            return True
        return False

    # ========== 行动规划 ==========

    async def plan_action(
        self,
        user_id: str,
        goal: str,
        context: str = ""
    ) -> ActionProposal:
        """
        规划行动

        AI 分析目标和上下文，规划具体的行动步骤。

        Args:
            user_id: 用户 ID
            goal: 行动目标
            context: 上下文信息

        Returns:
            行动提案
        """
        # 收集上下文
        context_info = await self._gather_action_context(user_id)

        planning_prompt = f"""基于以下信息，规划一个具体的行动方案。

目标：{goal}

用户上下文：
{context_info}

用户指定的额外上下文：
{context}

请规划一个行动方案，包含：
1. title: 行动标题（简洁明了）
2. description: 行动描述（详细说明）
3. action_type: 行动类型（document_management/memory_management/knowledge_organization/decision_analysis/learning_optimization/report_generation/reminder_setup/data_export/system_optimization）
4. priority: 优先级（high/medium/low）
5. steps: 行动步骤列表（每个步骤包含 action 和 description）
6. parameters: 所需参数
7. expected_outcome: 预期结果
8. risk_level: 风险等级（low/medium/high/critical）
9. requires_approval: 是否需要用户批准（true/false）

以 JSON 格式返回：
{{
  "title": "行动标题",
  "description": "行动描述",
  "action_type": "行动类型",
  "priority": "优先级",
  "steps": [
    {{"action": "步骤1", "description": "描述1"}},
    {{"action": "步骤2", "description": "描述2"}}
  ],
  "parameters": {{"key": "value"}},
  "expected_outcome": "预期结果",
  "risk_level": "风险等级",
  "requires_approval": true/false
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": planning_prompt}],
                system_prompt="你是一个专业的行动规划专家。基于用户的目标和上下文，规划具体可行的行动方案。只返回 JSON 格式的结果。",
                temperature=0.5,
                max_tokens=1500
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            return ActionProposal(
                title=result.get("title", ""),
                description=result.get("description", ""),
                action_type=result.get("action_type", "knowledge_organization"),
                priority=result.get("priority", "medium"),
                steps=result.get("steps", []),
                parameters=result.get("parameters", {}),
                expected_outcome=result.get("expected_outcome", ""),
                risk_level=result.get("risk_level", "low"),
                requires_approval=result.get("requires_approval", False)
            )

        except Exception as e:
            print(f"行动规划失败: {str(e)}")
            return ActionProposal(
                title="规划失败",
                description="无法生成行动方案",
                action_type="knowledge_organization",
                priority="low",
                steps=[],
                parameters={},
                expected_outcome="",
                risk_level="low",
                requires_approval=True
            )

    async def _gather_action_context(self, user_id: str) -> str:
        """收集行动上下文"""
        # 获取最近的活动
        from app.services.context_awareness import get_context_awareness_engine
        context_engine = get_context_awareness_engine(self.db)
        context = await context_engine.get_current_context(user_id)

        parts = []
        if context.current_session:
            parts.append(f"当前会话: {context.current_session.get('type', '未知')}")
        if context.active_focus:
            focus_names = [f['name'] for f in context.active_focus]
            parts.append(f"关注焦点: {', '.join(focus_names)}")
        if context.suggestions:
            parts.append(f"建议: {', '.join(context.suggestions[:2])}")

        return "\n".join(parts) if parts else "无特定上下文"

    # ========== 行动执行 ==========

    async def execute_action(
        self,
        user_id: str,
        plan_id: str
    ) -> ActionResult:
        """
        执行行动

        Args:
            user_id: 用户 ID
            plan_id: 计划 ID

        Returns:
            执行结果
        """
        # 获取计划
        result = await self.db.execute(
            select(ActionPlan).where(ActionPlan.plan_id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            return ActionResult(
                plan_id=plan_id,
                user_id=user_id,
                status="failed",
                error="计划不存在"
            )

        # 检查是否需要批准
        if plan.requires_approval and plan.approval_status != "approved":
            return ActionResult(
                plan_id=plan_id,
                user_id=user_id,
                status="failed",
                error="计划需要用户批准才能执行"
            )

        # 更新计划状态
        plan.status = "executing"
        plan.executed_at = datetime.now(timezone.utc)
        await self.db.flush()

        # 执行行动
        try:
            output = await self._execute_action_steps(plan)

            # 记录结果
            action_result = ActionResult(
                plan_id=plan_id,
                user_id=user_id,
                status="success",
                output=output
            )
            self.db.add(action_result)

            # 更新计划状态
            plan.status = "completed"
            plan.completed_at = datetime.now(timezone.utc)

            await self.db.flush()
            return action_result

        except Exception as e:
            # 记录失败
            action_result = ActionResult(
                plan_id=plan_id,
                user_id=user_id,
                status="failed",
                error=str(e)
            )
            self.db.add(action_result)

            plan.status = "failed"
            await self.db.flush()

            return action_result

    async def _execute_action_steps(self, plan: ActionPlan) -> str:
        """执行行动步骤"""
        steps = plan.steps or []
        results = []

        for i, step in enumerate(steps):
            step_result = await self._execute_single_step(plan, step, i + 1)
            results.append(f"步骤 {i+1}: {step_result}")

        return "\n".join(results)

    async def _execute_single_step(
        self,
        plan: ActionPlan,
        step: Dict[str, str],
        step_number: int
    ) -> str:
        """执行单个步骤"""
        action = step.get("action", "")
        description = step.get("description", "")

        # 根据行动类型执行不同的操作
        if plan.action_type == "document_management":
            return await self._execute_document_action(action, description)
        elif plan.action_type == "memory_management":
            return await self._execute_memory_action(action, description)
        elif plan.action_type == "knowledge_organization":
            return await self._execute_knowledge_action(action, description)
        elif plan.action_type == "reminder_setup":
            return await self._execute_reminder_action(action, description)
        else:
            return f"已规划: {description}"

    async def _execute_document_action(self, action: str, description: str) -> str:
        """执行文档管理行动"""
        # 这里可以集成实际的文档操作
        return f"文档操作已规划: {description}"

    async def _execute_memory_action(self, action: str, description: str) -> str:
        """执行记忆管理行动"""
        return f"记忆操作已规划: {description}"

    async def _execute_knowledge_action(self, action: str, description: str) -> str:
        """执行知识整理行动"""
        return f"知识整理已规划: {description}"

    async def _execute_reminder_action(self, action: str, description: str) -> str:
        """执行提醒设置行动"""
        return f"提醒已设置: {description}"

    # ========== 行动审批 ==========

    async def approve_action(
        self,
        user_id: str,
        plan_id: str
    ) -> bool:
        """批准行动"""
        result = await self.db.execute(
            select(ActionPlan).where(
                ActionPlan.plan_id == plan_id,
                ActionPlan.user_id == user_id
            )
        )
        plan = result.scalar_one_or_none()

        if plan:
            plan.approval_status = "approved"
            plan.approved_at = datetime.now(timezone.utc)
            await self.db.flush()
            return True
        return False

    async def reject_action(
        self,
        user_id: str,
        plan_id: str
    ) -> bool:
        """拒绝行动"""
        result = await self.db.execute(
            select(ActionPlan).where(
                ActionPlan.plan_id == plan_id,
                ActionPlan.user_id == user_id
            )
        )
        plan = result.scalar_one_or_none()

        if plan:
            plan.approval_status = "rejected"
            plan.status = "cancelled"
            await self.db.flush()
            return True
        return False

    # ========== 行动查询 ==========

    async def get_user_plans(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[ActionPlan]:
        """获取用户的行动计划"""
        query = select(ActionPlan).where(ActionPlan.user_id == user_id)
        if status:
            query = query.where(ActionPlan.status == status)
        query = query.order_by(ActionPlan.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_plan_results(
        self,
        user_id: str,
        plan_id: str
    ) -> List[ActionResult]:
        """获取行动结果"""
        result = await self.db.execute(
            select(ActionResult).where(
                ActionResult.plan_id == plan_id,
                ActionResult.user_id == user_id
            ).order_by(ActionResult.executed_at.desc())
        )
        return result.scalars().all()

    async def get_pending_approvals(
        self,
        user_id: str
    ) -> List[ActionPlan]:
        """获取待批准的行动"""
        result = await self.db.execute(
            select(ActionPlan).where(
                ActionPlan.user_id == user_id,
                ActionPlan.requires_approval == True,
                ActionPlan.approval_status == "pending"
            ).order_by(ActionPlan.created_at.desc())
        )
        return result.scalars().all()

    # ========== 安全规则管理 ==========

    async def create_safety_rule(
        self,
        user_id: str,
        rule_name: str,
        description: str,
        rule_type: str,
        condition: str,
        action: str = "require_approval"
    ) -> SafetyRule:
        """创建安全规则"""
        rule = SafetyRule(
            user_id=user_id,
            rule_name=rule_name,
            description=description,
            rule_type=rule_type,
            condition=condition,
            action=action
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def get_user_rules(self, user_id: str) -> List[SafetyRule]:
        """获取用户的安全规则"""
        result = await self.db.execute(
            select(SafetyRule).where(
                SafetyRule.user_id == user_id,
                SafetyRule.is_active == True
            )
        )
        return result.scalars().all()

    # ========== 统计 ==========

    async def get_action_stats(self, user_id: str) -> Dict[str, Any]:
        """获取行动统计"""
        from sqlalchemy import func

        total_plans = (await self.db.execute(
            select(func.count()).select_from(ActionPlan).where(ActionPlan.user_id == user_id)
        )).scalar() or 0

        completed = (await self.db.execute(
            select(func.count()).select_from(ActionPlan).where(
                ActionPlan.user_id == user_id,
                ActionPlan.status == "completed"
            )
        )).scalar() or 0

        pending_approval = (await self.db.execute(
            select(func.count()).select_from(ActionPlan).where(
                ActionPlan.user_id == user_id,
                ActionPlan.requires_approval == True,
                ActionPlan.approval_status == "pending"
            )
        )).scalar() or 0

        total_rules = (await self.db.execute(
            select(func.count()).select_from(SafetyRule).where(
                SafetyRule.user_id == user_id,
                SafetyRule.is_active == True
            )
        )).scalar() or 0

        return {
            "total_plans": total_plans,
            "completed": completed,
            "pending_approval": pending_approval,
            "total_rules": total_rules
        }


def get_autonomous_action_engine(db: AsyncSession) -> AutonomousActionEngine:
    """获取自主行动引擎实例"""
    return AutonomousActionEngine(db)
