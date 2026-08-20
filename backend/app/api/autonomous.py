"""
Personal AI OS - Autonomous Action API
自主行动接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.autonomous_action import get_autonomous_action_engine

router = APIRouter(prefix="/autonomous", tags=["自主行动"])


class PlanRequest(BaseModel):
    """规划请求"""
    goal: str
    context: str = ""


class PlanResponse(BaseModel):
    """计划响应"""
    plan_id: str
    title: str
    description: str
    action_type: str
    priority: str
    steps: List[dict]
    risk_level: str
    requires_approval: bool
    status: str
    created_at: str


class ResultResponse(BaseModel):
    """结果响应"""
    result_id: str
    status: str
    output: str
    error: str
    executed_at: str


class SafetyRuleRequest(BaseModel):
    """安全规则请求"""
    rule_name: str
    description: str
    rule_type: str
    condition: str
    action: str = "require_approval"


class SafetyRuleResponse(BaseModel):
    """安全规则响应"""
    rule_id: str
    rule_name: str
    description: str
    rule_type: str
    action: str
    is_active: bool


@router.post("/plan", response_model=PlanResponse)
async def plan_action(
    request: PlanRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    规划行动

    AI 分析目标和上下文，规划具体的行动步骤。
    """
    engine = get_autonomous_action_engine(db)
    proposal = await engine.plan_action(current_user_id, request.goal, request.context)

    # 检查安全规则
    safety = await engine.check_safety_rules(
        current_user_id,
        proposal.action_type,
        proposal.parameters
    )

    # 保存计划
    from app.models.autonomous import ActionPlan
    plan = ActionPlan(
        user_id=current_user_id,
        title=proposal.title,
        description=proposal.description,
        action_type=proposal.action_type,
        priority=proposal.priority,
        steps=proposal.steps,
        parameters=proposal.parameters,
        expected_outcome=proposal.expected_outcome,
        risk_level=proposal.risk_level,
        requires_approval=proposal.requires_approval or safety["requires_approval"],
        status="pending" if proposal.requires_approval else "approved"
    )
    db.add(plan)
    await db.flush()

    return PlanResponse(
        plan_id=str(plan.plan_id),
        title=plan.title,
        description=plan.description or "",
        action_type=plan.action_type,
        priority=plan.priority,
        steps=plan.steps or [],
        risk_level=plan.risk_level,
        requires_approval=plan.requires_approval,
        status=plan.status,
        created_at=plan.created_at.isoformat()
    )


@router.post("/execute/{plan_id}", response_model=ResultResponse)
async def execute_action(
    plan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    执行行动

    执行已批准的行动计划。
    """
    engine = get_autonomous_action_engine(db)
    result = await engine.execute_action(current_user_id, plan_id)

    return ResultResponse(
        result_id=str(result.result_id),
        status=result.status,
        output=result.output or "",
        error=result.error or "",
        executed_at=result.executed_at.isoformat()
    )


@router.post("/approve/{plan_id}")
async def approve_action(
    plan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """批准行动"""
    engine = get_autonomous_action_engine(db)
    success = await engine.approve_action(current_user_id, plan_id)

    if success:
        return {"message": "行动已批准"}
    else:
        raise HTTPException(status_code=404, detail="计划不存在")


@router.post("/reject/{plan_id}")
async def reject_action(
    plan_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """拒绝行动"""
    engine = get_autonomous_action_engine(db)
    success = await engine.reject_action(current_user_id, plan_id)

    if success:
        return {"message": "行动已拒绝"}
    else:
        raise HTTPException(status_code=404, detail="计划不存在")


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(20, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取行动计划"""
    engine = get_autonomous_action_engine(db)
    plans = await engine.get_user_plans(current_user_id, status, limit)

    return [
        PlanResponse(
            plan_id=str(p.plan_id),
            title=p.title,
            description=p.description or "",
            action_type=p.action_type,
            priority=p.priority,
            steps=p.steps or [],
            risk_level=p.risk_level,
            requires_approval=p.requires_approval,
            status=p.status,
            created_at=p.created_at.isoformat()
        )
        for p in plans
    ]


@router.get("/pending", response_model=List[PlanResponse])
async def get_pending_approvals(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取待批准的行动"""
    engine = get_autonomous_action_engine(db)
    plans = await engine.get_pending_approvals(current_user_id)

    return [
        PlanResponse(
            plan_id=str(p.plan_id),
            title=p.title,
            description=p.description or "",
            action_type=p.action_type,
            priority=p.priority,
            steps=p.steps or [],
            risk_level=p.risk_level,
            requires_approval=p.requires_approval,
            status=p.status,
            created_at=p.created_at.isoformat()
        )
        for p in plans
    ]


@router.get("/stats")
async def get_action_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取行动统计"""
    engine = get_autonomous_action_engine(db)
    return await engine.get_action_stats(current_user_id)


# ========== 安全规则 ==========

@router.post("/rules", response_model=SafetyRuleResponse)
async def create_safety_rule(
    request: SafetyRuleRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建安全规则"""
    engine = get_autonomous_action_engine(db)
    rule = await engine.create_safety_rule(
        current_user_id,
        request.rule_name,
        request.description,
        request.rule_type,
        request.condition,
        request.action
    )

    return SafetyRuleResponse(
        rule_id=str(rule.rule_id),
        rule_name=rule.rule_name,
        description=rule.description or "",
        rule_type=rule.rule_type,
        action=rule.action,
        is_active=rule.is_active
    )


@router.get("/rules", response_model=List[SafetyRuleResponse])
async def get_safety_rules(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取安全规则"""
    engine = get_autonomous_action_engine(db)
    rules = await engine.get_user_rules(current_user_id)

    return [
        SafetyRuleResponse(
            rule_id=str(r.rule_id),
            rule_name=r.rule_name,
            description=r.description or "",
            rule_type=r.rule_type,
            action=r.action,
            is_active=r.is_active
        )
        for r in rules
    ]


@router.get("/types")
async def get_action_types():
    """获取行动类型定义"""
    from app.services.autonomous_action import ACTION_TYPES, RISK_LEVELS
    return {
        "action_types": ACTION_TYPES,
        "risk_levels": RISK_LEVELS
    }
