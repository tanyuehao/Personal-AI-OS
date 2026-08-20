"""
Personal AI OS - Proactive Intelligence API
主动智能接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.proactive_engine import get_proactive_engine

router = APIRouter(prefix="/proactive", tags=["主动智能"])


class InsightResponse(BaseModel):
    """洞察响应"""
    insight_id: str
    insight_type: str
    title: str
    description: str
    priority: str
    category: str
    action_suggestion: str
    is_read: bool
    created_at: str


class PredictionResponse(BaseModel):
    """预测响应"""
    prediction_id: str
    prediction_type: str
    title: str
    description: str
    confidence: float
    evidence: List[str]
    suggested_actions: List[str]


class ContextResponse(BaseModel):
    """上下文响应"""
    current_topic: Optional[str]
    current_project: Optional[str]
    recent_documents: List[dict]
    recent_topics: List[str]
    active_memories: List[dict]
    pending_decisions: List[dict]
    last_updated: str


@router.get("/context", response_model=ContextResponse)
async def get_current_context(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前上下文

    分析用户的最近活动，构建当前工作上下文。
    """
    engine = get_proactive_engine(db)
    context = await engine.get_current_context(current_user_id)
    return ContextResponse(**context)


@router.post("/insights/generate")
async def generate_insights(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    生成主动洞察

    分析用户数据，发现需要注意的事项。
    """
    engine = get_proactive_engine(db)
    insights = await engine.generate_insights(current_user_id)

    return {
        "message": f"生成了 {len(insights)} 条洞察",
        "count": len(insights)
    }


@router.get("/insights", response_model=List[InsightResponse])
async def get_insights(
    unread_only: bool = Query(False, description="仅显示未读"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取洞察列表
    """
    engine = get_proactive_engine(db)
    insights = await engine.get_user_insights(current_user_id, unread_only)

    return [
        InsightResponse(
            insight_id=str(i.insight_id),
            insight_type=i.insight_type,
            title=i.title,
            description=i.description,
            priority=i.priority,
            category=i.category,
            action_suggestion=i.action_suggestion or "",
            is_read=i.is_read,
            created_at=i.created_at.isoformat()
        )
        for i in insights
    ]


@router.post("/insights/{insight_id}/read")
async def mark_insight_read(
    insight_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """标记洞察为已读"""
    engine = get_proactive_engine(db)
    await engine.mark_insight_read(current_user_id, insight_id)
    return {"message": "已标记为已读"}


@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(
    insight_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """忽略洞察"""
    engine = get_proactive_engine(db)
    await engine.dismiss_insight(current_user_id, insight_id)
    return {"message": "已忽略"}


@router.post("/trends/predict")
async def predict_trends(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    生成趋势预测

    基于历史数据预测未来趋势。
    """
    engine = get_proactive_engine(db)
    trends = await engine.predict_trends(current_user_id)

    return {
        "message": f"生成了 {len(trends)} 个趋势预测",
        "count": len(trends)
    }


@router.get("/trends", response_model=List[PredictionResponse])
async def get_predictions(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取趋势预测列表
    """
    engine = get_proactive_engine(db)
    predictions = await engine.get_user_predictions(current_user_id)

    return [
        PredictionResponse(
            prediction_id=str(p.prediction_id),
            prediction_type=p.prediction_type,
            title=p.title,
            description=p.description,
            confidence=p.confidence,
            evidence=p.evidence or [],
            suggested_actions=p.suggested_actions or []
        )
        for p in predictions
    ]


@router.get("/types")
async def get_insight_types():
    """获取洞察类型定义"""
    from app.services.proactive_engine import INSIGHT_TYPES, PREDICTION_TYPES
    return {
        "insight_types": INSIGHT_TYPES,
        "prediction_types": PREDICTION_TYPES
    }
