"""
Personal AI OS - Reflection Service
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision
from app.services.ai_service import create_ai_service


@dataclass
class DuplicateCluster:
    memory_ids: List[str]
    representative_content: str
    suggested_action: str


@dataclass
class WeeklySummary:
    period: str
    new_memories: int
    confirmed_memories: int
    new_beliefs: int
    belief_changes: int
    new_decisions: int
    key_insights: List[str]
    cognitive_trends: List[str]


class ReflectionService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def find_duplicate_memories(self, user_id: str, threshold: float = 0.8) -> List[DuplicateCluster]:
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            ).order_by(Memory.created_at.desc())
        )
        memories = result.scalars().all()

        if len(memories) < 2:
            return []

        memory_list = "\n".join([
            f"[{m.memory_id}] ({m.memory_type}) {m.content}"
            for m in memories[:50]
        ])

        prompt = (
            "Analyze the following memories and find duplicates or highly similar ones.\n\n"
            f"Memories:\n{memory_list}\n\n"
            "Return JSON:\n"
            '{"clusters": [{"memory_ids": ["id1", "id2"], '
            '"representative_content": "...", "suggested_action": "merge|keep_one|keep_all"}]}\n'
            "If no duplicates, return {\"clusters\": []}"
        )

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="Return only JSON.",
                temperature=0.3,
                max_tokens=1500
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)
            clusters = []
            for item in result.get("clusters", []):
                clusters.append(DuplicateCluster(
                    memory_ids=item.get("memory_ids", []),
                    representative_content=item.get("representative_content", ""),
                    suggested_action=item.get("suggested_action", "keep_all")
                ))
            return clusters
        except Exception:
            return []

    async def detect_belief_conflicts(self, user_id: str) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(Belief).where(
                Belief.user_id == user_id,
                Belief.status == "ACTIVE"
            )
        )
        beliefs = result.scalars().all()

        if len(beliefs) < 2:
            return []

        belief_list = "\n".join([
            f"[{b.belief_id}] ({b.topic}) {b.content}"
            for b in beliefs
        ])

        prompt = (
            "Analyze these beliefs for conflicts.\n\n"
            f"Beliefs:\n{belief_list}\n\n"
            "Return JSON:\n"
            '{"conflicts": [{"belief_ids": ["id1", "id2"], '
            '"conflict_type": "contradiction|implicit|ambiguous", "description": "..."}]}\n'
            "If no conflicts, return {\"conflicts\": []}"
        )

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="Return only JSON.",
                temperature=0.3,
                max_tokens=1500
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content).get("conflicts", [])
        except Exception:
            return []

    async def generate_weekly_summary(self, user_id: str, days: int = 7) -> WeeklySummary:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        new_memories = (await self.db.execute(
            select(func.count()).select_from(Memory).where(
                Memory.user_id == user_id, Memory.created_at >= since
            )
        )).scalar() or 0

        confirmed_memories = (await self.db.execute(
            select(func.count()).select_from(Memory).where(
                Memory.user_id == user_id, Memory.is_confirmed == "CONFIRMED",
                Memory.updated_at >= since
            )
        )).scalar() or 0

        new_beliefs = (await self.db.execute(
            select(func.count()).select_from(Belief).where(
                Belief.user_id == user_id, Belief.created_at >= since
            )
        )).scalar() or 0

        belief_changes = (await self.db.execute(
            select(func.count()).select_from(Belief).where(
                Belief.user_id == user_id, Belief.updated_at >= since,
                Belief.created_at < since
            )
        )).scalar() or 0

        new_decisions = (await self.db.execute(
            select(func.count()).select_from(Decision).where(
                Decision.user_id == user_id, Decision.created_at >= since
            )
        )).scalar() or 0

        recent_memories = (await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id, Memory.created_at >= since
            ).order_by(Memory.created_at.desc()).limit(20)
        )).scalars().all()

        recent_beliefs = (await self.db.execute(
            select(Belief).where(
                Belief.user_id == user_id, Belief.created_at >= since
            ).order_by(Belief.created_at.desc()).limit(10)
        )).scalars().all()

        memory_lines = [f"- ({m.memory_type}) {m.content[:50]}" for m in recent_memories[:10]]
        belief_lines = [f"- [{b.topic}] {b.content[:50]}" for b in recent_beliefs[:5]]

        context = f"Recent {days} days cognitive changes:\n\n"
        context += f"New memories ({new_memories}):\n" + "\n".join(memory_lines) + "\n\n"
        context += f"New beliefs ({new_beliefs}):\n" + "\n".join(belief_lines) + "\n\n"
        context += f"Belief changes ({belief_changes})\nNew decisions ({new_decisions})\n"

        prompt = (
            f"Based on this cognitive change data, generate insights and trends.\n\n{context}\n\n"
            "Return JSON:\n"
            '{"key_insights": ["insight1"], "cognitive_trends": ["trend1"]}'
        )

        key_insights = []
        cognitive_trends = []

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="Return only JSON.",
                temperature=0.5,
                max_tokens=500
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)
            key_insights = result.get("key_insights", [])
            cognitive_trends = result.get("cognitive_trends", [])
        except Exception:
            pass

        return WeeklySummary(
            period=f"Last {days} days",
            new_memories=new_memories,
            confirmed_memories=confirmed_memories,
            new_beliefs=new_beliefs,
            belief_changes=belief_changes,
            new_decisions=new_decisions,
            key_insights=key_insights,
            cognitive_trends=cognitive_trends
        )


def get_reflection_service(db: AsyncSession) -> ReflectionService:
    return ReflectionService(db)
