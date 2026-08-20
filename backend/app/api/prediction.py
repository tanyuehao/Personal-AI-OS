"""
Personal AI OS - Prediction API
预测需求接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.prediction_engine import get_prediction_engine

router = APIRouter(prefix="/prediction", tags=["预测需求"])


class PatternResponse(BaseModel):
    """模式响应"""
    pattern_type: str
    pattern_name: str
    description: str
    frequency: float
    confidence: float
    triggers: List[str]
    actions: List[str]


class PredictionResponse(BaseModel):
    """预测响应"""
    prediction_id: str
    prediction_type: str
    title: str
    description: str
    priority: str
    confidence: float
    predicted_need: str
    suggested_action: str
    relevant_resources: List[str]
    time_horizon: str


class PreparedInfoResponse(BaseModel):
    """预准备信息响应"""
    info_id: str
    info_type: str
    title: str
    content: str
    source: List[str]


@router.get("/patterns", response_model=List[PatternResponse])
async def get_patterns(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    识别用户行为模式

    分析用户的历史数据，识别常见行为模式。
    """
    engine = get_prediction_engine(db)
    patterns = await engine.recognize_patterns(current_user_id)

    return [
        PatternResponse(
            pattern_type=p.get("type", ""),
            pattern_name=p.get("name", ""),
            description=p.get("description", ""),
            frequency=p.get("frequency", 0.5),
            confidence=p.get("confidence", 0.5),
            triggers=p.get("triggers", []),
            actions=p.get("actions", [])
        )
        for p in patterns
    ]


@router.post("/predict")
async def predict_needs(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    预测用户需求

    基于用户的历史行为和模式，预测下一步可能需要什么。
    """
    engine = get_prediction_engine(db)
    predictions = await engine.predict_needs(current_user_id)

    # 保存预测
    saved = await engine.save_predictions(current_user_id, predictions)

    return {
        "message": f"生成了 {len(predictions)} 个预测",
        "count": len(predictions)
    }


@router.get("/predictions", response_model=List[PredictionResponse])
async def get_predictions(
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取需求预测"""
    engine = get_prediction_engine(db)
    predictions = await engine.get_user_predictions(current_user_id, limit)

    return [
        PredictionResponse(
            prediction_id=str(p.prediction_id),
            prediction_type=p.prediction_type,
            title=p.title,
            description=p.description,
            priority=p.priority,
            confidence=p.confidence,
            predicted_need=p.predicted_need,
            suggested_action=p.suggested_action or "",
            relevant_resources=p.relevant_resources or [],
            time_horizon=p.time_horizon or "short_term"
        )
        for p in predictions
    ]


@router.post("/prepare/{prediction_id}")
async def prepare_information(
    prediction_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    为预测准备相关信息

    根据预测的需求，提前准备相关信息。
    """
    engine = get_prediction_engine(db)
    infos = await engine.prepare_information(current_user_id, prediction_id)

    return {
        "message": f"准备了 {len(infos)} 条信息",
        "count": len(infos)
    }


@router.get("/prepared", response_model=List[PreparedInfoResponse])
async def get_prepared_infos(
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取预准备信息"""
    engine = get_prediction_engine(db)
    infos = await engine.get_prepared_infos(current_user_id, limit)

    return [
        PreparedInfoResponse(
            info_id=str(i.info_id),
            info_type=i.info_type,
            title=i.title,
            content=i.content,
            source=i.source or []
        )
        for i in infos
    ]


@router.get("/types")
async def get_prediction_types():
    """获取预测类型定义"""
    from app.services.prediction_engine import PREDICTION_TYPES, PATTERN_TYPES
    return {
        "prediction_types": PREDICTION_TYPES,
        "pattern_types": PATTERN_TYPES
    }
