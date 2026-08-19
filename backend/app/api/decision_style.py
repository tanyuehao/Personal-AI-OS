"""
Personal AI OS - Decision Style API
决策风格分析接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.decision_style_analyzer import (
    get_decision_style_analyzer,
    DECISION_STYLES
)

router = APIRouter(prefix="/cognitive", tags=["决策风格"])


class StyleResponse(BaseModel):
    """风格响应"""
    style_id: str
    risk_tolerance: float
    analysis_depth: float
    decisiveness: float
    collaboration: float
    time_preference: float
    evidence_reliance: float
    intuition_ratio: float
    emotional_influence: float
    primary_style: str
    secondary_style: str
    style_description: str
    last_analyzed_at: Optional[str] = None


class PatternResponse(BaseModel):
    """模式响应"""
    pattern_id: str
    pattern_type: str
    pattern_name: str
    description: str
    confidence: float


class StyleRecommendationRequest(BaseModel):
    """风格建议请求"""
    decision_context: str


@router.get("/decision-style", response_model=StyleResponse)
async def get_decision_style(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的决策风格

    返回用户的决策风格分析结果。
    """
    analyzer = get_decision_style_analyzer(db)
    style = await analyzer.get_user_style(current_user_id)

    if not style:
        # 如果没有分析过，触发分析
        analysis = await analyzer.analyze_user_style(current_user_id)
        style = await analyzer.save_style_analysis(current_user_id, analysis)

    return StyleResponse(
        style_id=str(style.style_id),
        risk_tolerance=style.risk_tolerance,
        analysis_depth=style.analysis_depth,
        decisiveness=style.decisiveness,
        collaboration=style.collaboration,
        time_preference=style.time_preference,
        evidence_reliance=style.evidence_reliance,
        intuition_ratio=style.intuition_ratio,
        emotional_influence=style.emotional_influence,
        primary_style=style.primary_style or "analytical",
        secondary_style=style.secondary_style or "intuitive",
        style_description=style.style_description or "",
        last_analyzed_at=style.last_analyzed_at.isoformat() if style.last_analyzed_at else None
    )


@router.post("/decision-style/analyze")
async def analyze_decision_style(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    重新分析用户的决策风格

    基于所有决策记录重新计算风格。
    """
    analyzer = get_decision_style_analyzer(db)
    analysis = await analyzer.analyze_user_style(current_user_id)
    style = await analyzer.save_style_analysis(current_user_id, analysis)

    return {
        "message": "决策风格分析完成",
        "style_id": str(style.style_id),
        "primary_style": style.primary_style,
        "style_description": style.style_description
    }


@router.get("/decision-style/patterns", response_model=List[PatternResponse])
async def get_decision_patterns(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的决策模式列表
    """
    analyzer = get_decision_style_analyzer(db)
    patterns = await analyzer.get_user_patterns(current_user_id)

    return [
        PatternResponse(
            pattern_id=str(p.pattern_id),
            pattern_type=p.pattern_type,
            pattern_name=p.pattern_name,
            description=p.description,
            confidence=p.confidence
        )
        for p in patterns
    ]


@router.post("/decision-style/recommendations")
async def get_style_recommendations(
    request: StyleRecommendationRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    基于用户风格提供决策建议

    根据用户的决策风格和当前决策场景，提供个性化建议。
    """
    analyzer = get_decision_style_analyzer(db)
    recommendations = await analyzer.get_style_recommendations(
        current_user_id,
        request.decision_context
    )

    return {"recommendations": recommendations}


@router.get("/decision-style/types")
async def get_style_types():
    """
    获取所有决策风格类型说明
    """
    return {"types": DECISION_STYLES}
