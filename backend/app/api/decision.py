"""
Personal AI OS - Decision API
决策记录接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.decision import Decision
from app.schemas.decision import (
    DecisionCreateRequest,
    DecisionUpdateRequest,
    DecisionResponse,
    DecisionListResponse
)

router = APIRouter(prefix="/decision", tags=["决策记录"])


@router.post("", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    request: DecisionCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    创建决策记录
    """
    decision = Decision(
        user_id=current_user_id,
        problem=request.problem,
        background=request.background,
        options=request.options,
        choice=request.choice,
        reasoning=request.reasoning,
        risk=request.risk,
        expected_result=request.expected_result,
        actual_result=request.actual_result,
        lesson=request.lesson,
        category=request.category,
        tags=request.tags,
        decision_date=request.decision_date
    )
    
    db.add(decision)
    await db.flush()
    await db.refresh(decision)
    
    return DecisionResponse.model_validate(decision)


@router.get("", response_model=DecisionListResponse)
async def list_decisions(
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取决策列表
    """
    query = select(Decision).where(Decision.user_id == current_user_id)
    
    if category:
        query = query.where(Decision.category == category)
    
    # 获取总数
    count_query = select(func.count()).select_from(Decision).where(Decision.user_id == current_user_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(Decision.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    decisions = result.scalars().all()
    
    return DecisionListResponse(
        items=[DecisionResponse.model_validate(d) for d in decisions],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取决策详情
    """
    result = await db.execute(
        select(Decision).where(
            Decision.decision_id == decision_id,
            Decision.user_id == current_user_id
        )
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="决策记录不存在"
        )
    
    return DecisionResponse.model_validate(decision)


@router.put("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: str,
    request: DecisionUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新决策记录
    """
    result = await db.execute(
        select(Decision).where(
            Decision.decision_id == decision_id,
            Decision.user_id == current_user_id
        )
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="决策记录不存在"
        )
    
    # 更新字段
    if request.problem is not None:
        decision.problem = request.problem
    if request.background is not None:
        decision.background = request.background
    if request.options is not None:
        decision.options = request.options
    if request.choice is not None:
        decision.choice = request.choice
    if request.reasoning is not None:
        decision.reasoning = request.reasoning
    if request.risk is not None:
        decision.risk = request.risk
    if request.expected_result is not None:
        decision.expected_result = request.expected_result
    if request.actual_result is not None:
        decision.actual_result = request.actual_result
    if request.lesson is not None:
        decision.lesson = request.lesson
    if request.category is not None:
        decision.category = request.category
    if request.tags is not None:
        decision.tags = request.tags
    
    await db.flush()
    await db.refresh(decision)
    
    return DecisionResponse.model_validate(decision)


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_decision(
    decision_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    删除决策记录
    """
    result = await db.execute(
        select(Decision).where(
            Decision.decision_id == decision_id,
            Decision.user_id == current_user_id
        )
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="决策记录不存在"
        )
    
    await db.delete(decision)
    
    return None


@router.get("/stats/summary")
async def get_decision_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取决策统计信息
    """
    # 总数
    total_result = await db.execute(
        select(func.count()).select_from(Decision).where(
            Decision.user_id == current_user_id
        )
    )
    total = total_result.scalar()
    
    # 按类别统计
    category_result = await db.execute(
        select(Decision.category, func.count())
        .where(Decision.user_id == current_user_id)
        .group_by(Decision.category)
    )
    categories = {row[0] or "未分类": row[1] for row in category_result.all()}
    
    # 最近决策
    recent_result = await db.execute(
        select(Decision)
        .where(Decision.user_id == current_user_id)
        .order_by(Decision.created_at.desc())
        .limit(5)
    )
    recent = recent_result.scalars().all()
    
    return {
        "total": total,
        "categories": categories,
        "recent": [DecisionResponse.model_validate(d) for d in recent]
    }
