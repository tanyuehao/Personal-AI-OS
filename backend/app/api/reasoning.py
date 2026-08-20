"""
Personal AI OS - Reasoning API
自主推理接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.reasoning_engine import get_reasoning_engine

router = APIRouter(prefix="/reasoning", tags=["自主推理"])


class AnalyzeRequest(BaseModel):
    """分析请求"""
    query: str
    reasoning_type: str = "analytical"


class AnalogyRequest(BaseModel):
    """类比推理请求"""
    situation: str


class ReasoningStepResponse(BaseModel):
    """推理步骤响应"""
    step_number: str
    step_type: str
    content: str
    confidence: float


class ReasoningResponse(BaseModel):
    """推理响应"""
    session_id: str
    reasoning_type: str
    conclusion: str
    confidence: float
    steps: List[dict]
    evidence: List[str]
    analogies: List[dict]


class SuggestionResponse(BaseModel):
    """建议响应"""
    suggestion_id: str
    title: str
    description: str
    suggestion_type: str
    priority: str
    confidence: float
    reasoning: str
    action_items: List[str]
    is_read: bool


@router.post("/analyze", response_model=ReasoningResponse)
async def analyze_independently(
    request: AnalyzeRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    独立分析问题

    基于用户的知识库、记忆和观点，独立分析问题。
    """
    engine = get_reasoning_engine(db)
    result = await engine.analyze_independently(
        current_user_id,
        request.query,
        request.reasoning_type
    )

    # 保存推理会话
    session = await engine.save_reasoning_session(
        current_user_id,
        request.query,
        result
    )

    return ReasoningResponse(
        session_id=str(session.session_id),
        reasoning_type=result.reasoning_type,
        conclusion=result.conclusion,
        confidence=result.confidence,
        steps=result.steps,
        evidence=result.evidence,
        analogies=result.analogies
    )


@router.post("/multi-step", response_model=ReasoningResponse)
async def multi_step_reasoning(
    request: AnalyzeRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    多步推理

    将复杂问题分解为多个步骤进行推理。
    """
    engine = get_reasoning_engine(db)
    result = await engine.multi_step_reasoning(
        current_user_id,
        request.query
    )

    # 保存推理会话
    session = await engine.save_reasoning_session(
        current_user_id,
        request.query,
        result
    )

    return ReasoningResponse(
        session_id=str(session.session_id),
        reasoning_type=result.reasoning_type,
        conclusion=result.conclusion,
        confidence=result.confidence,
        steps=result.steps,
        evidence=result.evidence,
        analogies=result.analogies
    )


@router.post("/analogy", response_model=ReasoningResponse)
async def analogical_reasoning(
    request: AnalogyRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    类比推理

    基于历史经验，对新情况进行类比推理。
    """
    engine = get_reasoning_engine(db)
    result = await engine.analogical_reasoning(
        current_user_id,
        request.situation
    )

    # 保存推理会话
    session = await engine.save_reasoning_session(
        current_user_id,
        request.situation,
        result
    )

    return ReasoningResponse(
        session_id=str(session.session_id),
        reasoning_type=result.reasoning_type,
        conclusion=result.conclusion,
        confidence=result.confidence,
        steps=result.steps,
        evidence=result.evidence,
        analogies=result.analogies
    )


@router.get("/history", response_model=List[ReasoningResponse])
async def get_reasoning_history(
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取推理历史"""
    engine = get_reasoning_engine(db)
    sessions = await engine.get_reasoning_history(current_user_id, limit)

    return [
        ReasoningResponse(
            session_id=str(s.session_id),
            reasoning_type=s.reasoning_type,
            conclusion=s.conclusion,
            confidence=s.confidence,
            steps=s.reasoning_steps or [],
            evidence=s.evidence_used or [],
            analogies=s.analogies_used or []
        )
        for s in sessions
    ]


@router.get("/analogies")
async def get_analogies(
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取类比记录"""
    engine = get_reasoning_engine(db)
    analogies = await engine.get_analogies(current_user_id, limit)

    return {
        "analogies": [
            {
                "source_situation": a.source_situation,
                "target_situation": a.target_situation,
                "similarity_score": a.similarity_score,
                "lesson": a.lesson,
                "created_at": a.created_at.isoformat()
            }
            for a in analogies
        ]
    }


@router.post("/suggestions/generate")
async def generate_suggestions(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    生成主动建议

    基于用户的数据生成有价值的建议。
    """
    engine = get_reasoning_engine(db)
    suggestions = await engine.generate_suggestions(current_user_id)

    return {
        "message": f"生成了 {len(suggestions)} 条建议",
        "count": len(suggestions)
    }


@router.get("/suggestions", response_model=List[SuggestionResponse])
async def get_suggestions(
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取主动建议"""
    engine = get_reasoning_engine(db)
    suggestions = await engine.get_user_suggestions(current_user_id, limit)

    return [
        SuggestionResponse(
            suggestion_id=str(s.suggestion_id),
            title=s.title,
            description=s.description,
            suggestion_type=s.suggestion_type,
            priority=s.priority,
            confidence=s.confidence,
            reasoning=s.reasoning or "",
            action_items=s.action_items or [],
            is_read=s.is_read
        )
        for s in suggestions
    ]


@router.get("/types")
async def get_reasoning_types():
    """获取推理类型定义"""
    from app.services.reasoning_engine import REASONING_TYPES, SUGGESTION_TYPES
    return {
        "reasoning_types": REASONING_TYPES,
        "suggestion_types": SUGGESTION_TYPES
    }
