"""
Personal AI OS - Smarter API
比你更聪明接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.smarter_engine import get_smarter_engine

router = APIRouter(prefix="/smarter", tags=["比你更聪明"])


class BlindSpotResponse(BaseModel):
    area: str
    description: str
    impact: str
    suggestion: str
    confidence: float


class CounterArgumentRequest(BaseModel):
    claim: str


class CounterArgumentResponse(BaseModel):
    original_claim: str
    counter_claim: str
    evidence: List[str]
    strength: float
    recommendation: str


class CrossDomainResponse(BaseModel):
    domain_a: str
    domain_b: str
    connection: str
    insight: str
    value: str


class BestPracticeResponse(BaseModel):
    area: str
    practice: str
    description: str
    source: str
    applicability: float


class DecisionOptRequest(BaseModel):
    problem: str
    current_choice: str = ""


class DecisionOptResponse(BaseModel):
    original_decision: str
    alternative: str
    reasoning: str
    expected_improvement: str
    confidence: float


@router.get("/blind-spots", response_model=List[BlindSpotResponse])
async def find_blind_spots(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """发现思维盲区"""
    engine = get_smarter_engine(db)
    spots = await engine.find_blind_spots(current_user_id)
    return [BlindSpotResponse(**s.__dict__) for s in spots]


@router.post("/counter-arguments", response_model=List[CounterArgumentResponse])
async def generate_counter_arguments(
    request: CounterArgumentRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """生成反面论证"""
    engine = get_smarter_engine(db)
    args = await engine.generate_counter_arguments(current_user_id, request.claim)
    return [CounterArgumentResponse(**a.__dict__) for a in args]


@router.get("/cross-domain", response_model=List[CrossDomainResponse])
async def find_cross_domain_insights(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """发现跨领域洞察"""
    engine = get_smarter_engine(db)
    insights = await engine.find_cross_domain_insights(current_user_id)
    return [CrossDomainResponse(**i.__dict__) for i in insights]


@router.get("/best-practices", response_model=List[BestPracticeResponse])
async def recommend_best_practices(
    area: str = Query("", description="关注领域"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """推荐最佳实践"""
    engine = get_smarter_engine(db)
    practices = await engine.recommend_best_practices(current_user_id, area)
    return [BestPracticeResponse(**p.__dict__) for p in practices]


@router.post("/optimize-decision", response_model=List[DecisionOptResponse])
async def optimize_decision(
    request: DecisionOptRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """优化决策"""
    engine = get_smarter_engine(db)
    optimizations = await engine.optimize_decision(
        current_user_id,
        request.problem,
        request.current_choice
    )
    return [DecisionOptResponse(**o.__dict__) for o in optimizations]
