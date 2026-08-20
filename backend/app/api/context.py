"""
Personal AI OS - Context Awareness API
上下文感知接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.context_awareness import get_context_awareness_engine

router = APIRouter(prefix="/context", tags=["上下文感知"])


class SessionStartRequest(BaseModel):
    """开始会话请求"""
    session_type: str = "coding"
    title: str = ""
    description: str = ""


class ActivityLogRequest(BaseModel):
    """记录活动请求"""
    activity_type: str
    action: str
    details: str = ""
    page: str = ""
    tool: str = ""


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    session_type: str
    title: str
    status: str
    started_at: str


class ActivityResponse(BaseModel):
    """活动响应"""
    log_id: str
    activity_type: str
    action: str
    details: str
    created_at: str


class FocusResponse(BaseModel):
    """焦点响应"""
    focus_id: str
    focus_type: str
    focus_name: str
    description: str
    priority: float
    confidence: float


class ContextResponse(BaseModel):
    """上下文响应"""
    current_session: Optional[dict]
    active_focus: List[dict]
    recent_activities: List[dict]
    current_mood: str
    energy_level: float
    suggestions: List[str]


@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    request: SessionStartRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    开始新的工作会话
    """
    engine = get_context_awareness_engine(db)
    session = await engine.start_session(
        current_user_id,
        request.session_type,
        request.title,
        request.description
    )

    return SessionResponse(
        session_id=str(session.session_id),
        session_type=session.session_type,
        title=session.title or "",
        status=session.status,
        started_at=session.started_at.isoformat()
    )


@router.post("/session/{session_id}/end")
async def end_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """结束工作会话"""
    engine = get_context_awareness_engine(db)
    await engine.update_session(
        current_user_id,
        session_id,
        status="completed",
        ended_at=datetime.now(timezone.utc)
    )
    return {"message": "会话已结束"}


@router.get("/sessions")
async def get_sessions(
    limit: int = Query(10, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取会话历史"""
    from datetime import datetime, timezone
    engine = get_context_awareness_engine(db)
    sessions = await engine.get_session_history(current_user_id, limit)

    return [
        {
            "session_id": str(s.session_id),
            "session_type": s.session_type,
            "title": s.title or "",
            "status": s.status,
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None
        }
        for s in sessions
    ]


@router.post("/activity")
async def log_activity(
    request: ActivityLogRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """记录活动"""
    engine = get_context_awareness_engine(db)
    session = await engine.get_active_session(current_user_id)

    await engine.log_activity(
        user_id=current_user_id,
        activity_type=request.activity_type,
        action=request.action,
        details=request.details,
        page=request.page,
        tool=request.tool,
        session_id=str(session.session_id) if session else None
    )

    return {"message": "活动已记录"}


@router.get("/activities", response_model=List[ActivityResponse])
async def get_activities(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取最近活动"""
    engine = get_context_awareness_engine(db)
    activities = await engine.get_recent_activities(current_user_id, hours, limit)

    return [
        ActivityResponse(
            log_id=str(a.log_id),
            activity_type=a.activity_type,
            action=a.action,
            details=a.details or "",
            created_at=a.created_at.isoformat()
        )
        for a in activities
    ]


@router.get("/activities/stats")
async def get_activity_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取活动统计"""
    engine = get_context_awareness_engine(db)
    return await engine.get_activity_stats(current_user_id)


@router.post("/focus/detect")
async def detect_focus(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    识别当前焦点

    分析用户最近的活动，识别当前关注的领域。
    """
    engine = get_context_awareness_engine(db)
    focuses = await engine.detect_focus(current_user_id)

    return {
        "message": f"识别了 {len(focuses)} 个焦点",
        "count": len(focuses)
    }


@router.get("/focus", response_model=List[FocusResponse])
async def get_focuses(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取活跃焦点"""
    engine = get_context_awareness_engine(db)
    focuses = await engine.get_active_focuses(current_user_id)

    return [
        FocusResponse(
            focus_id=str(f.focus_id),
            focus_type=f.focus_type,
            focus_name=f.focus_name,
            description=f.description or "",
            priority=f.priority,
            confidence=f.confidence
        )
        for f in focuses
    ]


@router.get("/current", response_model=ContextResponse)
async def get_current_context(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前完整上下文

    综合所有信息，提供当前的完整上下文状态。
    """
    engine = get_context_awareness_engine(db)
    context = await engine.get_current_context(current_user_id)

    return ContextResponse(
        current_session=context.current_session,
        active_focus=context.active_focus,
        recent_activities=context.recent_activities,
        current_mood=context.current_mood,
        energy_level=context.energy_level,
        suggestions=context.suggestions
    )


@router.get("/types")
async def get_context_types():
    """获取上下文类型定义"""
    from app.services.context_awareness import SESSION_TYPES, ACTIVITY_TYPES, FOCUS_TYPES
    return {
        "session_types": SESSION_TYPES,
        "activity_types": ACTIVITY_TYPES,
        "focus_types": FOCUS_TYPES
    }
