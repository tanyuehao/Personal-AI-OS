"""
Personal AI OS - Proactive Intelligence Engine
主动智能引擎 - 主动提醒 + 趋势预测 + 上下文感知
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.proactive import (
    ProactiveInsight, ContextSnapshot, TrendPrediction,
    INSIGHT_TYPES, PREDICTION_TYPES
)
from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision
from app.models.document import Document
from app.models.conversation import Conversation, ConversationMessage
from app.services.ai_service import create_ai_service


@dataclass
class InsightItem:
    """洞察项"""
    insight_type: str
    title: str
    description: str
    priority: str
    category: str
    related_ids: List[str]
    action_suggestion: str


@dataclass
class TrendItem:
    """趋势项"""
    prediction_type: str
    title: str
    description: str
    confidence: float
    evidence: List[str]
    suggested_actions: List[str]


class ProactiveEngine:
    """主动智能引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    # ========== 上下文感知 ==========

    async def build_context_snapshot(self, user_id: str) -> ContextSnapshot:
        """
        构建用户当前上下文快照

        分析用户的最近活动，构建当前工作上下文。
        """
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # 最近讨论的话题（从对话中提取）
        recent_convs = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(10)
        )
        conversations = recent_convs.scalars().all()

        recent_topics = []
        for conv in conversations:
            if conv.title:
                recent_topics.append(conv.title)

        # 最近活跃的记忆
        recent_memories = await self.db.execute(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED",
                Memory.created_at >= week_ago
            )
            .order_by(Memory.importance.desc())
            .limit(10)
        )
        memories = recent_memories.scalars().all()
        active_memories = [{"id": str(m.memory_id), "content": m.content[:50], "type": m.memory_type} for m in memories]

        # 待决策
        pending_decisions = await self.db.execute(
            select(Decision)
            .where(
                Decision.user_id == user_id,
                Decision.choice == None
            )
            .order_by(Decision.created_at.desc())
            .limit(5)
        )
        decisions = pending_decisions.scalars().all()
        pending = [{"id": str(d.decision_id), "problem": d.problem[:50]} for d in decisions]

        # 最近文档
        recent_docs = await self.db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(5)
        )
        docs = recent_docs.scalars().all()
        recent_documents = [{"id": str(d.document_id), "name": d.file_name, "type": d.file_type} for d in docs]

        # 推断当前话题
        current_topic = recent_topics[0] if recent_topics else None
        current_project = None

        # 保存快照
        snapshot = ContextSnapshot(
            user_id=user_id,
            current_topic=current_topic,
            current_project=current_project,
            recent_documents=recent_documents,
            recent_topics=recent_topics,
            active_memories=active_memories,
            pending_decisions=pending
        )
        self.db.add(snapshot)
        await self.db.flush()

        return snapshot

    async def get_current_context(self, user_id: str) -> Dict[str, Any]:
        """获取当前上下文"""
        # 获取最近的快照
        result = await self.db.execute(
            select(ContextSnapshot)
            .where(ContextSnapshot.user_id == user_id)
            .order_by(ContextSnapshot.created_at.desc())
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            snapshot = await self.build_context_snapshot(user_id)

        return {
            "current_topic": snapshot.current_topic,
            "current_project": snapshot.current_project,
            "recent_documents": snapshot.recent_documents or [],
            "recent_topics": snapshot.recent_topics or [],
            "active_memories": snapshot.active_memories or [],
            "pending_decisions": snapshot.pending_decisions or [],
            "last_updated": snapshot.created_at.isoformat()
        }

    # ========== 主动提醒 ==========

    async def generate_insights(self, user_id: str) -> List[InsightItem]:
        """
        生成主动洞察

        分析用户数据，发现需要注意的事项。
        """
        now = datetime.now(timezone.utc)
        insights = []

        # 1. 检查记忆衰退
        decay_insights = await self._check_memory_decay(user_id, now)
        insights.extend(decay_insights)

        # 2. 检查待决策
        decision_insights = await self._check_pending_decisions(user_id)
        insights.extend(decision_insights)

        # 3. 检查知识缺口
        gap_insights = await self._check_knowledge_gaps(user_id)
        insights.extend(gap_insights)

        # 4. 检查冲突
        conflict_insights = await self._check_conflicts(user_id)
        insights.extend(conflict_insights)

        # 保存洞察
        for insight in insights:
            proactive = ProactiveInsight(
                user_id=user_id,
                insight_type=insight.insight_type,
                title=insight.title,
                description=insight.description,
                priority=insight.priority,
                category=insight.category,
                related_ids=insight.related_ids,
                action_suggestion=insight.action_suggestion,
                expires_at=now + timedelta(days=7)
            )
            self.db.add(proactive)

        await self.db.flush()
        return insights

    async def _check_memory_decay(self, user_id: str, now: datetime) -> List[InsightItem]:
        """检查记忆衰退"""
        week_ago = now - timedelta(days=7)

        # 获取超过一周未使用的高重要性记忆
        result = await self.db.execute(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED",
                Memory.importance >= 0.7,
                Memory.last_used_at < week_ago
            )
            .order_by(Memory.importance.desc())
            .limit(5)
        )
        memories = result.scalars().all()

        insights = []
        if memories:
            insights.append(InsightItem(
                insight_type="memory_decay",
                title=f"有 {len(memories)} 条重要记忆需要复习",
                description=f"你有 {len(memories)} 条重要记忆超过一周未使用，建议复习以保持记忆强度。",
                priority="medium",
                category="记忆管理",
                related_ids=[str(m.memory_id) for m in memories],
                action_suggestion="复习这些重要记忆，增强长期记忆"
            ))

        return insights

    async def _check_pending_decisions(self, user_id: str) -> List[InsightItem]:
        """检查待决策"""
        result = await self.db.execute(
            select(Decision)
            .where(
                Decision.user_id == user_id,
                Decision.choice == None
            )
            .order_by(Decision.created_at.desc())
            .limit(5)
        )
        decisions = result.scalars().all()

        insights = []
        if decisions:
            insights.append(InsightItem(
                insight_type="reminder",
                title=f"你有 {len(decisions)} 个待决策事项",
                description="以下决策尚未做出选择，建议尽快处理。",
                priority="high",
                category="决策管理",
                related_ids=[str(d.decision_id) for d in decisions],
                action_suggestion="回顾这些决策并做出选择"
            ))

        return insights

    async def _check_knowledge_gaps(self, user_id: str) -> List[InsightItem]:
        """检查知识缺口"""
        # 检查最近对话中提到但知识库中没有的主题
        recent_convs = await self.db.execute(
            select(ConversationMessage)
            .join(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(20)
        )
        messages = recent_convs.scalars().all()

        user_messages = [m.content for m in messages if m.role == "user"]

        if not user_messages:
            return []

        # 使用 AI 分析知识缺口
        context = "\n".join(user_messages[:10])

        gap_prompt = f"""分析以下用户最近的对话，找出用户感兴趣但知识库中可能缺少的主题。

用户最近的对话：
{context[:2000]}

请找出 2-3 个用户可能需要补充知识的主题。

以 JSON 格式返回：
{{
  "gaps": [
    {{
      "topic": "主题",
      "reason": "为什么需要这个知识",
      "suggestion": "建议的补充方式"
    }}
  ]
}}

如果没有明显缺口，返回空列表 {{"gaps": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": gap_prompt}],
                system_prompt="你是一个知识管理助手。只返回 JSON 格式的结果。",
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

            insights = []
            for gap in result.get("gaps", []):
                insights.append(InsightItem(
                    insight_type="knowledge_gap",
                    title=f"知识缺口：{gap.get('topic', '')}",
                    description=gap.get("reason", ""),
                    priority="low",
                    category="知识管理",
                    related_ids=[],
                    action_suggestion=gap.get("suggestion", "")
                ))

            return insights

        except Exception:
            return []

    async def _check_conflicts(self, user_id: str) -> List[InsightItem]:
        """检查观点冲突"""
        from app.services.cognitive_engine import get_cognitive_engine

        engine = get_cognitive_engine(self.db)
        conflicts = await engine.detect_belief_conflicts(user_id)

        insights = []
        for conflict in conflicts[:2]:
            insights.append(InsightItem(
                insight_type="conflict_detected",
                title="检测到观点冲突",
                description=conflict.get("description", ""),
                priority="medium",
                category="认知一致性",
                related_ids=conflict.get("belief_ids", []),
                action_suggestion=conflict.get("suggestion", "查看并澄清冲突的观点")
            ))

        return insights

    async def get_user_insights(
        self,
        user_id: str,
        unread_only: bool = False
    ) -> List[ProactiveInsight]:
        """获取用户的洞察列表"""
        query = select(ProactiveInsight).where(
            ProactiveInsight.user_id == user_id,
            ProactiveInsight.is_dismissed == False
        )

        if unread_only:
            query = query.where(ProactiveInsight.is_read == False)

        query = query.order_by(
            ProactiveInsight.priority.desc(),
            ProactiveInsight.created_at.desc()
        ).limit(20)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_insight_read(self, user_id: str, insight_id: str):
        """标记洞察为已读"""
        result = await self.db.execute(
            select(ProactiveInsight).where(
                ProactiveInsight.insight_id == insight_id,
                ProactiveInsight.user_id == user_id
            )
        )
        insight = result.scalar_one_or_none()
        if insight:
            insight.is_read = True
            await self.db.flush()

    async def dismiss_insight(self, user_id: str, insight_id: str):
        """忽略洞察"""
        result = await self.db.execute(
            select(ProactiveInsight).where(
                ProactiveInsight.insight_id == insight_id,
                ProactiveInsight.user_id == user_id
            )
        )
        insight = result.scalar_one_or_none()
        if insight:
            insight.is_dismissed = True
            await self.db.flush()

    # ========== 趋势预测 ==========

    async def predict_trends(self, user_id: str) -> List[TrendItem]:
        """
        基于历史数据预测趋势

        分析用户的知识变化、决策模式、记忆趋势。
        """
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=30)

        # 获取统计数据
        memory_count = (await self.db.execute(
            select(func.count()).select_from(Memory)
            .where(Memory.user_id == user_id, Memory.created_at >= month_ago)
        )).scalar() or 0

        belief_count = (await self.db.execute(
            select(func.count()).select_from(Belief)
            .where(Belief.user_id == user_id, Belief.created_at >= month_ago)
        )).scalar() or 0

        decision_count = (await self.db.execute(
            select(func.count()).select_from(Decision)
            .where(Decision.user_id == user_id, Decision.created_at >= month_ago)
        )).scalar() or 0

        doc_count = (await self.db.execute(
            select(func.count()).select_from(Document)
            .where(Document.user_id == user_id, Document.created_at >= month_ago)
        )).scalar() or 0

        # 获取最近的话题
        recent_convs = await self.db.execute(
            select(Conversation.title)
            .where(Conversation.user_id == user_id, Conversation.created_at >= month_ago)
            .order_by(Conversation.created_at.desc())
            .limit(10)
        )
        topics = [t[0] for t in recent_convs.all() if t[0]]

        # 使用 AI 生成趋势预测
        stats_text = f"""
最近30天的活动统计：
- 新增记忆：{memory_count} 条
- 新增观点：{belief_count} 条
- 新增决策：{decision_count} 个
- 上传文档：{doc_count} 个

最近讨论的话题：
{chr(10).join(topics[:5])}
"""

        trend_prompt = f"""基于以下用户活动数据，预测未来趋势和需求。

{stats_text}

请预测：
1. 用户接下来可能关注的话题
2. 用户可能需要的知识
3. 用户可能面临的决策
4. 用户的学习/成长方向

以 JSON 格式返回：
{{
  "trends": [
    {{
      "type": "预测类型",
      "title": "预测标题",
      "description": "详细描述",
      "confidence": 0.0-1.0,
      "evidence": ["证据1", "证据2"],
      "actions": ["建议操作1", "建议操作2"]
    }}
  ]
}}

返回 3-5 个趋势预测。"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": trend_prompt}],
                system_prompt="你是一个专业的趋势分析专家。只返回 JSON 格式的结果。",
                temperature=0.5,
                max_tokens=1000
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            trends = []
            for item in result.get("trends", []):
                trends.append(TrendItem(
                    prediction_type=item.get("type", "next_topic"),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    confidence=item.get("confidence", 0.5),
                    evidence=item.get("evidence", []),
                    suggested_actions=item.get("actions", [])
                ))

            # 保存预测
            for trend in trends:
                prediction = TrendPrediction(
                    user_id=user_id,
                    prediction_type=trend.prediction_type,
                    title=trend.title,
                    description=trend.description,
                    confidence=trend.confidence,
                    evidence=trend.evidence,
                    suggested_actions=trend.suggested_actions,
                    expires_at=now + timedelta(days=7)
                )
                self.db.add(prediction)

            await self.db.flush()
            return trends

        except Exception as e:
            print(f"趋势预测失败: {str(e)}")
            return []

    async def get_user_predictions(self, user_id: str) -> List[TrendPrediction]:
        """获取用户的趋势预测"""
        result = await self.db.execute(
            select(TrendPrediction)
            .where(
                TrendPrediction.user_id == user_id,
                TrendPrediction.is_relevant == True
            )
            .order_by(TrendPrediction.confidence.desc())
            .limit(10)
        )
        return result.scalars().all()


def get_proactive_engine(db: AsyncSession) -> ProactiveEngine:
    """获取主动智能引擎实例"""
    return ProactiveEngine(db)
