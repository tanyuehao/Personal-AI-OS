"""
Personal AI OS - Cognitive Engine API
认知引擎接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.cognitive_engine import get_cognitive_engine

router = APIRouter(prefix="/cognitive", tags=["认知引擎"])


class BeliefExtractionRequest(BaseModel):
    """观点提取请求"""
    messages: List[dict]  # [{"role": "user", "content": "..."}, ...]


class BeliefExtractionResponse(BaseModel):
    """观点提取响应"""
    beliefs: List[dict]
    count: int


class ConflictCheckRequest(BaseModel):
    """冲突检测请求"""
    content: str
    topic: Optional[str] = None


class ConflictCheckResponse(BaseModel):
    """冲突检测响应"""
    conflicts: List[dict]
    count: int
    has_conflicts: bool


class DecisionLinkRequest(BaseModel):
    """决策关联请求"""
    decision_id: str


class DecisionLinkResponse(BaseModel):
    """决策关联响应"""
    linked_memories: List[str]
    linked_beliefs: List[str]
    potential_memories: List[str]
    analysis: str


@router.post("/beliefs/extract", response_model=BeliefExtractionResponse)
async def extract_beliefs(
    request: BeliefExtractionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    从对话中提取观点候选

    使用 AI 分析对话内容，提取用户明确表达的观点、看法和偏好。
    """
    engine = get_cognitive_engine(db)

    beliefs = await engine.extract_beliefs_from_conversation(
        user_id=current_user_id,
        messages=request.messages
    )

    return BeliefExtractionResponse(
        beliefs=[
            {
                "topic": b.topic,
                "content": b.content,
                "confidence": b.confidence,
                "evidence": b.evidence
            }
            for b in beliefs
        ],
        count=len(beliefs)
    )


@router.post("/beliefs/check-conflict", response_model=ConflictCheckResponse)
async def check_conflict(
    request: ConflictCheckRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    检测新观点与现有观点的冲突

    分析新观点是否与用户现有的观点存在矛盾、细化或演变关系。
    """
    engine = get_cognitive_engine(db)

    conflicts = await engine.detect_conflicts(
        user_id=current_user_id,
        new_content=request.content,
        topic=request.topic
    )

    return ConflictCheckResponse(
        conflicts=[
            {
                "existing_content": c.existing_content,
                "new_content": c.new_content,
                "conflict_type": c.conflict_type,
                "explanation": c.explanation
            }
            for c in conflicts
        ],
        count=len(conflicts),
        has_conflicts=len(conflicts) > 0
    )


@router.post("/decisions/link", response_model=DecisionLinkResponse)
async def link_decision(
    request: DecisionLinkRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    将决策关联到相关记忆和观点

    分析决策与用户记忆和观点的关联，识别影响决策的因素。
    """
    engine = get_cognitive_engine(db)

    result = await engine.link_decision_to_context(
        user_id=current_user_id,
        decision_id=request.decision_id
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return DecisionLinkResponse(**result)


@router.get("/memory-score")
async def calculate_memory_score(
    importance: float = 0.5,
    confidence: float = 0.7,
    frequency: int = 1,
    user_confirmed: bool = False,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    计算记忆推荐分数

    使用公式：score = 0.35 * importance + 0.25 * confidence + 0.20 * recurrence + 0.20 * explicit_user_signal
    """
    engine = get_cognitive_engine(db)

    score = await engine.calculate_memory_score(
        importance=importance,
        confidence=confidence,
        frequency=frequency,
        user_confirmed=user_confirmed
    )

    return {
        "score": score,
        "factors": {
            "importance": importance,
            "confidence": confidence,
            "recurrence": min(frequency / 10, 1.0),
            "explicit_signal": 1.0 if user_confirmed else 0.3
        },
        "formula": "0.35 * importance + 0.25 * confidence + 0.20 * recurrence + 0.20 * explicit_user_signal"
    }
