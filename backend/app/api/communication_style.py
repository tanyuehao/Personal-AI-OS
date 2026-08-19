"""
Personal AI OS - Communication Style API
沟通风格和语言习惯接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.communication_style_analyzer import (
    get_communication_style_analyzer,
    COMMUNICATION_STYLES, LANGUAGE_HABIT_TYPES, CONVERSATION_PATTERN_TYPES
)

router = APIRouter(prefix="/cognitive", tags=["沟通风格"])


class StyleResponse(BaseModel):
    """风格响应"""
    style_id: str
    formality: float
    directness: float
    emotional_expression: float
    verbosity: float
    humor: float
    professionalism: float
    question_asking: float
    preferred_mode: str
    response_length: str
    last_analyzed_at: Optional[str] = None


class HabitResponse(BaseModel):
    """语言习惯响应"""
    habit_id: str
    habit_type: str
    habit_name: str
    pattern: str
    frequency: float
    examples: Optional[List[str]] = None


class PatternResponse(BaseModel):
    """对话模式响应"""
    pattern_id: str
    pattern_type: str
    pattern_name: str
    description: str
    confidence: float
    examples: Optional[List[str]] = None


@router.get("/communication-style", response_model=StyleResponse)
async def get_communication_style(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的沟通风格
    """
    analyzer = get_communication_style_analyzer(db)
    style = await analyzer.get_user_style(current_user_id)

    if not style:
        # 如果没有分析过，触发分析
        analysis = await analyzer.analyze_user_style(current_user_id)
        style = await analyzer.save_style_analysis(current_user_id, analysis)

    return StyleResponse(
        style_id=str(style.style_id),
        formality=style.formality,
        directness=style.directness,
        emotional_expression=style.emotional_expression,
        verbosity=style.verbosity,
        humor=style.humor,
        professionalism=style.professionalism,
        question_asking=style.question_asking,
        preferred_mode=style.preferred_mode or "文字",
        response_length=style.response_length or "适中",
        last_analyzed_at=style.last_analyzed_at.isoformat() if style.last_analyzed_at else None
    )


@router.post("/communication-style/analyze")
async def analyze_communication_style(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    重新分析用户的沟通风格
    """
    analyzer = get_communication_style_analyzer(db)
    analysis = await analyzer.analyze_user_style(current_user_id)
    style = await analyzer.save_style_analysis(current_user_id, analysis)

    return {
        "message": "沟通风格分析完成",
        "style_id": str(style.style_id),
        "formality": style.formality,
        "preferred_mode": style.preferred_mode
    }


@router.get("/communication-style/habits", response_model=List[HabitResponse])
async def get_language_habits(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的语言习惯
    """
    analyzer = get_communication_style_analyzer(db)
    habits = await analyzer.get_language_habits(current_user_id)

    return [
        HabitResponse(
            habit_id=str(h.habit_id),
            habit_type=h.habit_type,
            habit_name=h.habit_name,
            pattern=h.pattern,
            frequency=h.frequency,
            examples=h.examples
        )
        for h in habits
    ]


@router.get("/communication-style/patterns", response_model=List[PatternResponse])
async def get_conversation_patterns(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的对话模式
    """
    analyzer = get_communication_style_analyzer(db)
    patterns = await analyzer.get_conversation_patterns(current_user_id)

    return [
        PatternResponse(
            pattern_id=str(p.pattern_id),
            pattern_type=p.pattern_type,
            pattern_name=p.pattern_name,
            description=p.description,
            confidence=p.confidence,
            examples=p.examples
        )
        for p in patterns
    ]


@router.get("/communication-style/types")
async def get_style_types():
    """获取沟通风格类型定义"""
    return {
        "communication_styles": COMMUNICATION_STYLES,
        "language_habit_types": LANGUAGE_HABIT_TYPES,
        "conversation_pattern_types": CONVERSATION_PATTERN_TYPES
    }
