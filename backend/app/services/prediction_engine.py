"""
Personal AI OS - Prediction Engine
预测需求引擎 - 预测用户下一步行动 + 提前准备信息
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.prediction import (
    UserPattern, NeedPrediction, PreparedInfo,
    PREDICTION_TYPES, PATTERN_TYPES
)
from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision
from app.models.document import Document
from app.models.conversation import Conversation, ConversationMessage
from app.services.ai_service import create_ai_service


@dataclass
class PredictionResult:
    """预测结果"""
    prediction_type: str
    title: str
    description: str
    priority: str
    confidence: float
    predicted_need: str
    suggested_action: str
    relevant_resources: List[str]
    time_horizon: str


class PredictionEngine:
    """预测需求引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    # ========== 模式识别 ==========

    async def recognize_patterns(self, user_id: str) -> List[Dict[str, Any]]:
        """
        识别用户的行为模式

        分析用户的历史数据，识别常见模式。
        """
        # 获取最近的活动
        recent_convs = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(30)
        )
        conversations = recent_convs.scalars().all()

        recent_memories = await self.db.execute(
            select(Memory)
            .where(Memory.user_id == user_id, Memory.is_confirmed == "CONFIRMED")
            .order_by(Memory.created_at.desc())
            .limit(30)
        )
        memories = recent_memories.scalars().all()

        recent_decisions = await self.db.execute(
            select(Decision)
            .where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc())
            .limit(20)
        )
        decisions = recent_decisions.scalars().all()

        # 构建分析数据
        conv_data = "\n".join([
            f"- {c.title} ({c.updated_at.strftime('%Y-%m-%d') if c.updated_at else 'N/A'})"
            for c in conversations[:15]
        ])

        memory_data = "\n".join([
            f"- ({m.memory_type}) {m.content[:50]}"
            for m in memories[:15]
        ])

        decision_data = "\n".join([
            f"- {d.problem}: {d.choice or '未定'}"
            for d in decisions[:10]
        ])

        pattern_prompt = f"""分析以下用户行为数据，识别常见模式。

最近的对话：
{conv_data or '无'}

最近的记忆：
{memory_data or '无'}

历史决策：
{decision_data or '无'}

请识别 3-5 个用户的行为模式，每个模式包含：
- type: 模式类型（daily_routine/work_pattern/learning_pattern/decision_pattern/communication_pattern/preference_pattern）
- name: 模式名称
- description: 模式描述
- frequency: 频率（0-1）
- confidence: 置信度（0-1）
- triggers: 触发条件列表
- actions: 行为序列列表

以 JSON 格式返回：
{{
  "patterns": [
    {{
      "type": "模式类型",
      "name": "模式名称",
      "description": "描述",
      "frequency": 0.8,
      "confidence": 0.7,
      "triggers": ["触发条件1", "触发条件2"],
      "actions": ["行为1", "行为2"]
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": pattern_prompt}],
                system_prompt="你是一个专业的行为分析专家。只返回 JSON 格式的结果。",
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
            return result.get("patterns", [])

        except Exception as e:
            print(f"模式识别失败: {str(e)}")
            return []

    # ========== 需求预测 ==========

    async def predict_needs(
        self,
        user_id: str
    ) -> List[PredictionResult]:
        """
        预测用户下一步可能需要什么

        基于用户的历史行为、当前上下文和模式识别。
        """
        # 获取当前上下文
        context = await self._gather_prediction_context(user_id)

        # 识别模式
        patterns = await self.recognize_patterns(user_id)

        pattern_text = "\n".join([
            f"- [{p.get('type', '')}] {p.get('name', '')}: {p.get('description', '')}"
            for p in patterns
        ]) if patterns else "无明显模式"

        prediction_prompt = f"""基于以下用户数据，预测用户下一步可能需要什么。

当前上下文：
- 最近话题：{context.get('recent_topics', '无')}
- 活跃记忆：{context.get('active_memories_count', 0)} 条
- 待决策：{context.get('pending_decisions_count', 0)} 个
- 最近文档：{context.get('recent_docs_count', 0)} 个

用户行为模式：
{pattern_text}

历史决策：
{context.get('recent_decisions', '无')}

请预测用户接下来可能需要：
1. 什么信息或知识
2. 什么帮助或建议
3. 什么行动或决策

以 JSON 格式返回 3-5 个预测：
{{
  "predictions": [
    {{
      "type": "预测类型（next_action/information_need/decision_pending/learning_opportunity/risk_alert/optimization）",
      "title": "预测标题",
      "description": "详细描述",
      "priority": "high/medium/low",
      "confidence": 0.0-1.0,
      "need": "预测的需求",
      "action": "建议行动",
      "resources": ["相关资源1", "相关资源2"],
      "time_horizon": "immediate/short_term/long_term"
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prediction_prompt}],
                system_prompt="你是一个专业的需求预测专家。基于用户的历史行为和模式预测下一步需求。只返回 JSON 格式的结果。",
                temperature=0.5,
                max_tokens=1500
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            predictions = []
            for item in result.get("predictions", []):
                predictions.append(PredictionResult(
                    prediction_type=item.get("type", "next_action"),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    priority=item.get("priority", "medium"),
                    confidence=item.get("confidence", 0.5),
                    predicted_need=item.get("need", ""),
                    suggested_action=item.get("action", ""),
                    relevant_resources=item.get("resources", []),
                    time_horizon=item.get("time_horizon", "short_term")
                ))

            return predictions

        except Exception as e:
            print(f"需求预测失败: {str(e)}")
            return []

    async def _gather_prediction_context(self, user_id: str) -> Dict[str, Any]:
        """收集预测上下文"""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # 最近话题
        recent_convs = await self.db.execute(
            select(Conversation.title)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(10)
        )
        recent_topics = [t[0] for t in recent_convs.all() if t[0]]

        # 活跃记忆
        mem_result = await self.db.execute(
            select(Memory)
            .where(Memory.user_id == user_id, Memory.is_confirmed == "CONFIRMED")
            .order_by(Memory.importance.desc())
            .limit(10)
        )
        active_memories = mem_result.scalars().all()

        # 待决策
        dec_result = await self.db.execute(
            select(Decision)
            .where(Decision.user_id == user_id, Decision.choice == None)
            .limit(5)
        )
        pending_decisions = dec_result.scalars().all()

        # 最近文档
        doc_result = await self.db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(5)
        )
        recent_docs = doc_result.scalars().all()

        # 最近决策
        recent_dec_result = await self.db.execute(
            select(Decision)
            .where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc())
            .limit(5)
        )
        recent_decisions = recent_dec_result.scalars().all()

        return {
            "recent_topics": ", ".join(recent_topics[:5]) if recent_topics else "无",
            "active_memories_count": len(active_memories),
            "pending_decisions_count": len(pending_decisions),
            "recent_docs_count": len(recent_docs),
            "recent_decisions": "\n".join([
                f"- {d.problem}: {d.choice or '未定'}"
                for d in recent_decisions
            ]) if recent_decisions else "无"
        }

    # ========== 保存预测 ==========

    async def save_predictions(
        self,
        user_id: str,
        predictions: List[PredictionResult]
    ) -> List[NeedPrediction]:
        """保存预测结果"""
        saved = []
        now = datetime.now(timezone.utc)

        for pred in predictions:
            prediction = NeedPrediction(
                user_id=user_id,
                prediction_type=pred.prediction_type,
                title=pred.title,
                description=pred.description,
                priority=pred.priority,
                confidence=pred.confidence,
                predicted_need=pred.predicted_need,
                suggested_action=pred.suggested_action,
                relevant_resources=pred.relevant_resources,
                time_horizon=pred.time_horizon,
                expires_at=now + timedelta(days=7)
            )
            self.db.add(prediction)
            saved.append(prediction)

        await self.db.flush()
        return saved

    async def get_user_predictions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[NeedPrediction]:
        """获取用户的预测"""
        result = await self.db.execute(
            select(NeedPrediction)
            .where(
                NeedPrediction.user_id == user_id,
                NeedPrediction.is_relevant == True
            )
            .order_by(NeedPrediction.confidence.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # ========== 预准备信息 ==========

    async def prepare_information(
        self,
        user_id: str,
        prediction_id: str
    ) -> List[PreparedInfo]:
        """
        为预测准备相关信息

        根据预测的需求，提前准备相关信息。
        """
        # 获取预测
        pred_result = await self.db.execute(
            select(NeedPrediction).where(NeedPrediction.prediction_id == prediction_id)
        )
        prediction = pred_result.scalar_one_or_none()

        if not prediction:
            return []

        # 获取相关资源
        resources = prediction.relevant_resources or []

        # 使用 AI 生成预准备信息
        prepare_prompt = f"""为以下需求准备相关信息。

需求：{prediction.predicted_need}
建议行动：{prediction.suggested_action}
相关资源：{', '.join(resources) if resources else '无'}

请准备 2-3 条相关信息，每条包含：
- type: 信息类型（summary/checklist/reference/guide）
- title: 标题
- content: 内容（50-100字）
- source: 来源

以 JSON 格式返回：
{{
  "infos": [
    {{
      "type": "信息类型",
      "title": "标题",
      "content": "内容",
      "source": "来源"
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prepare_prompt}],
                system_prompt="你是一个信息准备助手。只返回 JSON 格式的结果。",
                temperature=0.5,
                max_tokens=800
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            prepared = []
            now = datetime.now(timezone.utc)

            for item in result.get("infos", []):
                info = PreparedInfo(
                    user_id=user_id,
                    info_type=item.get("type", "summary"),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    source=[item.get("source", "")],
                    related_prediction_id=prediction_id,
                    expires_at=now + timedelta(days=7)
                )
                self.db.add(info)
                prepared.append(info)

            await self.db.flush()
            return prepared

        except Exception as e:
            print(f"信息准备失败: {str(e)}")
            return []

    async def get_prepared_infos(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[PreparedInfo]:
        """获取预准备信息"""
        result = await self.db.execute(
            select(PreparedInfo)
            .where(
                PreparedInfo.user_id == user_id,
                PreparedInfo.is_used == False
            )
            .order_by(PreparedInfo.prepared_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


def get_prediction_engine(db: AsyncSession) -> PredictionEngine:
    """获取预测引擎实例"""
    return PredictionEngine(db)
