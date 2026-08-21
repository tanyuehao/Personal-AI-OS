"""
Personal AI OS - Unified Cognitive Model API
统一认知模型接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.cognitive_model import get_cognitive_model

router = APIRouter(prefix="/cognitive-model", tags=["统一认知模型"])


@router.get("/profile")
async def get_cognitive_profile(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户认知画像

    融合所有模块数据，构建完整的用户认知画像。
    """
    model = get_cognitive_model(db)
    return await model.get_cognitive_profile(current_user_id)


@router.get("/summary")
async def get_cognitive_summary(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户认知摘要（自然语言）
    """
    model = get_cognitive_model(db)
    summary = await model.get_user_summary(current_user_id)
    return {"summary": summary}


@router.get("/stats")
async def get_cognitive_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取认知统计
    """
    model = get_cognitive_model(db)
    profile = await model.build_cognitive_profile(current_user_id)

    return {
        "knowledge_domains": len(profile.knowledge_domains),
        "core_values": len(profile.core_values),
        "strengths": len(profile.strengths),
        "weaknesses": len(profile.weaknesses),
        "opportunities": len(profile.opportunities),
        "confidence": profile.confidence,
        "last_updated": profile.last_updated
    }
