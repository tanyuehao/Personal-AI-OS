"""
Personal AI OS - Learning API
持续学习接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.continuous_learning import get_continuous_learning_engine

router = APIRouter(prefix="/learning", tags=["持续学习"])


class CorrectionRequest(BaseModel):
    """修正请求"""
    conversation_id: Optional[str] = None
    original_response: str
    correction: str
    correction_type: str = "content"


class PreferenceRequest(BaseModel):
    """偏好请求"""
    category: str
    key: str
    value: str
    confidence: float = 0.7


class FeedbackRequest(BaseModel):
    """反馈请求"""
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    rating: float
    comment: str = ""
    feedback_type: str = "quality"


class CorrectionResponse(BaseModel):
    """修正响应"""
    correction_id: str
    correction_type: str
    user_correction: str
    lesson_learned: Optional[str]
    created_at: str


class PreferenceResponse(BaseModel):
    """偏好响应"""
    preference_id: str
    category: str
    key: str
    value: str
    confidence: float
    mention_count: int


class LearningEventResponse(BaseModel):
    """学习事件响应"""
    event_id: str
    event_type: str
    source: str
    content: str
    impact: float
    created_at: str


@router.post("/corrections", response_model=CorrectionResponse)
async def record_correction(
    request: CorrectionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    记录用户对 AI 的修正

    当用户纠正 AI 的回答时，记录修正并提取教训。
    """
    engine = get_continuous_learning_engine(db)
    correction = await engine.record_correction(
        user_id=current_user_id,
        conversation_id=request.conversation_id or "",
        original_response=request.original_response,
        correction=request.correction,
        correction_type=request.correction_type
    )

    return CorrectionResponse(
        correction_id=str(correction.correction_id),
        correction_type=correction.correction_type,
        user_correction=correction.user_correction,
        lesson_learned=correction.lesson_learned,
        created_at=correction.created_at.isoformat()
    )


@router.get("/corrections", response_model=List[CorrectionResponse])
async def get_corrections(
    limit: int = Query(20, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的修正记录"""
    engine = get_continuous_learning_engine(db)
    corrections = await engine.get_user_corrections(current_user_id, limit)

    return [
        CorrectionResponse(
            correction_id=str(c.correction_id),
            correction_type=c.correction_type,
            user_correction=c.user_correction,
            lesson_learned=c.lesson_learned,
            created_at=c.created_at.isoformat()
        )
        for c in corrections
    ]


@router.post("/preferences", response_model=PreferenceResponse)
async def learn_preference(
    request: PreferenceRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    学习用户偏好

    记录用户的偏好设置。
    """
    engine = get_continuous_learning_engine(db)
    preference = await engine.learn_preference(
        user_id=current_user_id,
        category=request.category,
        key=request.key,
        value=request.value,
        confidence=request.confidence,
        source="manual"
    )

    return PreferenceResponse(
        preference_id=str(preference.preference_id),
        category=preference.category,
        key=preference.key,
        value=preference.value,
        confidence=preference.confidence,
        mention_count=int(preference.mention_count)
    )


@router.get("/preferences", response_model=List[PreferenceResponse])
async def get_preferences(
    category: Optional[str] = Query(None, description="偏好类别"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户偏好"""
    engine = get_continuous_learning_engine(db)
    preferences = await engine.get_user_preferences(current_user_id, category)

    return [
        PreferenceResponse(
            preference_id=str(p.preference_id),
            category=p.category,
            key=p.key,
            value=p.value,
            confidence=p.confidence,
            mention_count=int(p.mention_count)
        )
        for p in preferences
    ]


@router.post("/feedback")
async def record_feedback(
    request: FeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    记录用户反馈

    对 AI 回答进行评分和评论。
    """
    engine = get_continuous_learning_engine(db)
    feedback = await engine.record_feedback(
        user_id=current_user_id,
        conversation_id=request.conversation_id or "",
        message_id=request.message_id or "",
        rating=request.rating,
        comment=request.comment,
        feedback_type=request.feedback_type
    )

    return {"message": "反馈已记录", "feedback_id": str(feedback.feedback_id)}


@router.get("/feedback/stats")
async def get_feedback_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取反馈统计"""
    engine = get_continuous_learning_engine(db)
    return await engine.get_user_feedback_stats(current_user_id)


@router.get("/events", response_model=List[LearningEventResponse])
async def get_learning_events(
    limit: int = Query(20, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取学习事件"""
    engine = get_continuous_learning_engine(db)
    events = await engine.get_learning_events(current_user_id, limit)

    return [
        LearningEventResponse(
            event_id=str(e.event_id),
            event_type=e.event_type,
            source=e.source,
            content=e.content,
            impact=e.impact,
            created_at=e.created_at.isoformat()
        )
        for e in events
    ]


@router.get("/stats")
async def get_learning_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取学习统计"""
    engine = get_continuous_learning_engine(db)
    return await engine.get_learning_stats(current_user_id)


@router.post("/update-model")
async def update_cognitive_model(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户认知模型

    基于所有学习事件更新用户的认知模型。
    """
    engine = get_continuous_learning_engine(db)
    model = await engine.update_cognitive_model(current_user_id)

    return {
        "message": "认知模型已更新",
        "model_id": str(model.model_id),
        "total_interactions": model.total_interactions,
        "total_learning_events": model.total_learning_events,
        "learning_rate": model.learning_rate
    }
