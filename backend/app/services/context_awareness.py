"""
Personal AI OS - Context Awareness Engine
上下文感知引擎 - 实时检测用户当前工作状态
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.context import (
    WorkSession, ActivityLog, UserFocus,
    SESSION_TYPES, ACTIVITY_TYPES, FOCUS_TYPES
)
from app.models.memory import Memory
from app.models.document import Document
from app.models.conversation import Conversation, ConversationMessage
from app.services.ai_service import create_ai_service


@dataclass
class ContextState:
    """当前上下文状态"""
    current_session: Optional[Dict[str, Any]]
    active_focus: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]
    current_mood: str
    energy_level: float
    suggestions: List[str]


class ContextAwarenessEngine:
    """上下文感知引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    # ========== 工作会话管理 ==========

    async def start_session(
        self,
        user_id: str,
        session_type: str = "coding",
        title: str = "",
        description: str = ""
    ) -> WorkSession:
        """开始一个新的工作会话"""
        # 结束之前的活跃会话
        await self._end_active_sessions(user_id)

        session = WorkSession(
            user_id=user_id,
            session_type=session_type,
            title=title,
            description=description,
            status="active",
            started_at=datetime.now(timezone.utc),
            last_active_at=datetime.now(timezone.utc)
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def _end_active_sessions(self, user_id: str):
        """结束用户的活跃会话"""
        result = await self.db.execute(
            select(WorkSession).where(
                WorkSession.user_id == user_id,
                WorkSession.status == "active"
            )
        )
        sessions = result.scalars().all()

        for session in sessions:
            session.status = "completed"
            session.ended_at = datetime.now(timezone.utc)

        await self.db.flush()

    async def update_session(
        self,
        user_id: str,
        session_id: str,
        **kwargs
    ):
        """更新工作会话"""
        result = await self.db.execute(
            select(WorkSession).where(
                WorkSession.session_id == session_id,
                WorkSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()

        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.last_active_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def get_active_session(self, user_id: str) -> Optional[WorkSession]:
        """获取当前活跃的会话"""
        result = await self.db.execute(
            select(WorkSession).where(
                WorkSession.user_id == user_id,
                WorkSession.status == "active"
            ).order_by(WorkSession.started_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_session_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[WorkSession]:
        """获取会话历史"""
        result = await self.db.execute(
            select(WorkSession)
            .where(WorkSession.user_id == user_id)
            .order_by(WorkSession.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # ========== 活动追踪 ==========

    async def log_activity(
        self,
        user_id: str,
        activity_type: str,
        action: str,
        details: str = "",
        page: str = "",
        tool: str = "",
        data: Optional[Dict] = None,
        session_id: Optional[str] = None
    ):
        """记录活动"""
        log = ActivityLog(
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            action=action,
            details=details,
            page=page,
            tool=tool,
            data=data
        )
        self.db.add(log)

        # 更新会话最后活跃时间
        if session_id:
            session = await self.get_active_session(user_id)
            if session:
                session.last_active_at = datetime.now(timezone.utc)

        await self.db.flush()

    async def get_recent_activities(
        self,
        user_id: str,
        hours: int = 24,
        limit: int = 50
    ) -> List[ActivityLog]:
        """获取最近的活动"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        result = await self.db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.user_id == user_id,
                ActivityLog.created_at >= since
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_activity_stats(self, user_id: str) -> Dict[str, Any]:
        """获取活动统计"""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        # 最近1小时活动
        hour_count = (await self.db.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id, ActivityLog.created_at >= hour_ago)
        )).scalars().all()

        # 最近24小时活动
        day_count = (await self.db.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id, ActivityLog.created_at >= day_ago)
        )).scalars().all()

        # 活动类型分布
        hour_types = {}
        for log in hour_count:
            hour_types[log.activity_type] = hour_types.get(log.activity_type, 0) + 1

        return {
            "last_hour": len(hour_count),
            "last_day": len(day_count),
            "activity_types": hour_types,
            "is_active": len(hour_count) > 0
        }

    # ========== 焦点识别 ==========

    async def detect_focus(
        self,
        user_id: str
    ) -> List[UserFocus]:
        """
        识别用户当前的关注点

        基于最近的活动和对话，识别用户当前关注的领域。
        """
        # 获取最近的活动
        recent_activities = await self.get_recent_activities(user_id, hours=6, limit=20)

        # 获取最近的对话
        recent_convs = await self.db.execute(
            select(Conversation.title, Conversation.updated_at)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(10)
        )
        conversations = recent_convs.all()

        # 获取最近的记忆
        recent_memories = await self.db.execute(
            select(Memory.content, Memory.memory_type)
            .where(Memory.user_id == user_id, Memory.is_confirmed == "CONFIRMED")
            .order_by(Memory.created_at.desc())
            .limit(10)
        )
        memories = recent_memories.all()

        # 构建分析数据
        activity_data = "\n".join([
            f"- {a.activity_type}: {a.action} ({a.created_at.strftime('%H:%M')})"
            for a in recent_activities[:10]
        ])

        conv_data = "\n".join([
            f"- {c[0]}"
            for c in conversations[:5] if c[0]
        ])

        memory_data = "\n".join([
            f"- ({m[1]}) {m[0][:50]}"
            for m in memories[:5]
        ])

        # 使用 AI 分析焦点
        focus_prompt = f"""分析以下用户活动数据，识别用户当前的关注点。

最近的活动：
{activity_data or '无'}

最近的对话：
{conv_data or '无'}

最近的记忆：
{memory_data or '无'}

请识别用户当前关注的 2-4 个焦点，每个焦点包含：
- type: 焦点类型（topic/project/task/skill/person/document）
- name: 焦点名称
- description: 描述
- priority: 优先级（0-1）
- confidence: 置信度（0-1）

以 JSON 格式返回：
{{
  "focuses": [
    {{
      "type": "焦点类型",
      "name": "焦点名称",
      "description": "描述",
      "priority": 0.8,
      "confidence": 0.7
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": focus_prompt}],
                system_prompt="你是一个注意力分析专家。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=800
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            # 保存焦点
            focuses = []
            for item in result.get("focuses", []):
                # 检查是否已存在
                existing = await self.db.execute(
                    select(UserFocus).where(
                        UserFocus.user_id == user_id,
                        UserFocus.focus_name == item.get("name", "")
                    )
                )
                existing_focus = existing.scalar_one_or_none()

                if existing_focus:
                    existing_focus.last_active_at = datetime.now(timezone.utc)
                    existing_focus.confidence = item.get("confidence", 0.5)
                    focuses.append(existing_focus)
                else:
                    focus = UserFocus(
                        user_id=user_id,
                        focus_type=item.get("type", "topic"),
                        focus_name=item.get("name", ""),
                        description=item.get("description", ""),
                        priority=item.get("priority", 0.5),
                        confidence=item.get("confidence", 0.5)
                    )
                    self.db.add(focus)
                    focuses.append(focus)

            await self.db.flush()
            return focuses

        except Exception as e:
            print(f"焦点识别失败: {str(e)}")
            return []

    async def get_active_focuses(self, user_id: str) -> List[UserFocus]:
        """获取活跃焦点"""
        result = await self.db.execute(
            select(UserFocus)
            .where(
                UserFocus.user_id == user_id,
                UserFocus.is_active == True
            )
            .order_by(UserFocus.priority.desc())
            .limit(5)
        )
        return result.scalars().all()

    # ========== 综合上下文 ==========

    async def get_current_context(self, user_id: str) -> ContextState:
        """
        获取当前完整上下文状态

        综合所有信息，提供当前的完整上下文。
        """
        # 获取活跃会话
        session = await self.get_active_session(user_id)
        session_data = None
        if session:
            session_data = {
                "session_id": str(session.session_id),
                "type": session.session_type,
                "title": session.title,
                "status": session.status,
                "mood": session.mood,
                "energy_level": session.energy_level,
                "current_task": session.current_task,
                "started_at": session.started_at.isoformat()
            }

        # 获取焦点
        focuses = await self.get_active_focuses(user_id)
        focus_data = [
            {
                "name": f.focus_name,
                "type": f.focus_type,
                "priority": f.priority,
                "confidence": f.confidence
            }
            for f in focuses
        ]

        # 获取最近活动
        activities = await self.get_recent_activities(user_id, hours=2, limit=10)
        activity_data = [
            {
                "type": a.activity_type,
                "action": a.action,
                "time": a.created_at.isoformat()
            }
            for a in activities
        ]

        # 获取活动统计
        stats = await self.get_activity_stats(user_id)

        # 推断当前状态
        current_mood = "neutral"
        energy_level = 0.5
        suggestions = []

        if stats["is_active"]:
            if stats["last_hour"] > 10:
                energy_level = 0.8
                current_mood = "focused"
            elif stats["last_hour"] > 5:
                energy_level = 0.6
                current_mood = "engaged"
            else:
                energy_level = 0.4
                current_mood = "relaxed"

        # 生成建议
        if focus_data:
            suggestions.append(f"你当前关注的领域: {focus_data[0]['name']}")
        if session_data and session_data.get("current_task"):
            suggestions.append(f"当前任务: {session_data['current_task']}")
        if stats["last_hour"] > 15:
            suggestions.append("你已经工作很长时间了，建议休息一下")

        return ContextState(
            current_session=session_data,
            active_focus=focus_data,
            recent_activities=activity_data,
            current_mood=current_mood,
            energy_level=energy_level,
            suggestions=suggestions
        )

    async def log_page_visit(self, user_id: str, page: str):
        """记录页面访问"""
        await self.log_activity(
            user_id=user_id,
            activity_type="page_visit",
            action=f"访问 {page}",
            page=page
        )

    async def log_action(
        self,
        user_id: str,
        action: str,
        details: str = "",
        page: str = ""
    ):
        """记录操作"""
        await self.log_activity(
            user_id=user_id,
            activity_type="user_action",
            action=action,
            details=details,
            page=page
        )


def get_context_awareness_engine(db: AsyncSession) -> ContextAwarenessEngine:
    """获取上下文感知引擎实例"""
    return ContextAwarenessEngine(db)
