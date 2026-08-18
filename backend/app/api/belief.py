"""
Personal AI OS - Belief API
观点管理接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.belief import Belief, BeliefHistory
from app.schemas.belief import (
    BeliefCreateRequest,
    BeliefUpdateRequest,
    BeliefResponse,
    BeliefListResponse,
    BeliefHistoryResponse
)

router = APIRouter(prefix="/cognitive", tags=["认知模型"])


@router.post("/beliefs", response_model=BeliefResponse, status_code=status.HTTP_201_CREATED)
async def create_belief(
    request: BeliefCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    创建观点
    """
    belief = Belief(
        user_id=current_user_id,
        topic=request.topic,
        content=request.content,
        confidence=request.confidence or 0.7,
        supporting_evidence=request.supporting_evidence,
        opposing_evidence=request.opposing_evidence
    )
    
    db.add(belief)
    await db.flush()
    await db.refresh(belief)
    
    return BeliefResponse.model_validate(belief)


@router.get("/beliefs", response_model=BeliefListResponse)
async def list_beliefs(
    page: int = 1,
    limit: int = 20,
    topic: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取观点列表
    """
    query = select(Belief).where(Belief.user_id == current_user_id)
    
    if topic:
        safe_topic = topic.replace("%", "\\%").replace("_", "\\_")
        query = query.where(Belief.topic.ilike(f"%{safe_topic}%", escape="\\"))
    
    # 获取总数
    count_query = select(func.count()).select_from(Belief).where(Belief.user_id == current_user_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(Belief.updated_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    beliefs = result.scalars().all()
    
    return BeliefListResponse(
        items=[BeliefResponse.model_validate(b) for b in beliefs],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/beliefs/{belief_id}", response_model=BeliefResponse)
async def get_belief(
    belief_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取观点详情
    """
    result = await db.execute(
        select(Belief).where(
            Belief.belief_id == belief_id,
            Belief.user_id == current_user_id
        )
    )
    belief = result.scalar_one_or_none()
    
    if not belief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="观点不存在"
        )
    
    return BeliefResponse.model_validate(belief)


@router.put("/beliefs/{belief_id}", response_model=BeliefResponse)
async def update_belief(
    belief_id: str,
    request: BeliefUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新观点
    """
    result = await db.execute(
        select(Belief).where(
            Belief.belief_id == belief_id,
            Belief.user_id == current_user_id
        )
    )
    belief = result.scalar_one_or_none()
    
    if not belief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="观点不存在"
        )
    
    # 记录变化历史
    if request.content and request.content != belief.content:
        history = BeliefHistory(
            belief_id=belief.belief_id,
            old_content=belief.content,
            new_content=request.content,
            change_reason=request.change_reason
        )
        db.add(history)
        
        # 更新演化历史
        if not belief.evolution_history:
            belief.evolution_history = []
        belief.evolution_history.append({
            "old_content": belief.content,
            "new_content": request.content,
            "change_reason": request.change_reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # 更新字段
    if request.topic is not None:
        belief.topic = request.topic
    if request.content is not None:
        belief.content = request.content
    if request.confidence is not None:
        belief.confidence = request.confidence
    if request.supporting_evidence is not None:
        belief.supporting_evidence = request.supporting_evidence
    if request.opposing_evidence is not None:
        belief.opposing_evidence = request.opposing_evidence
    if request.status is not None:
        belief.status = request.status
    
    await db.flush()
    await db.refresh(belief)
    
    return BeliefResponse.model_validate(belief)


@router.delete("/beliefs/{belief_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_belief(
    belief_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    删除观点
    """
    result = await db.execute(
        select(Belief).where(
            Belief.belief_id == belief_id,
            Belief.user_id == current_user_id
        )
    )
    belief = result.scalar_one_or_none()
    
    if not belief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="观点不存在"
        )
    
    await db.delete(belief)
    
    return None


@router.get("/beliefs/{belief_id}/history", response_model=List[BeliefHistoryResponse])
async def get_belief_history(
    belief_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取观点变化历史
    """
    # 验证观点属于当前用户
    belief_result = await db.execute(
        select(Belief).where(
            Belief.belief_id == belief_id,
            Belief.user_id == current_user_id
        )
    )
    belief = belief_result.scalar_one_or_none()
    
    if not belief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="观点不存在"
        )
    
    # 获取历史
    result = await db.execute(
        select(BeliefHistory)
        .where(BeliefHistory.belief_id == belief_id)
        .order_by(BeliefHistory.created_at.desc())
    )
    histories = result.scalars().all()
    
    return [BeliefHistoryResponse.model_validate(h) for h in histories]
