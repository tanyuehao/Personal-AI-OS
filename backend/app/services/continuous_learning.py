"""
Personal AI OS - Continuous Learning Engine
持续学习引擎 - 从交互中学习和改进
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.learning import (
    LearningEvent, Correction, Preference, Feedback, UserCognitiveModel,
    LEARNING_EVENT_TYPES, CORRECTION_TYPES
)
from app.models.memory import Memory
from app.models.conversation import ConversationMessage, Conversation
from app.services.ai_service import create_ai_service


@dataclass
class LearningResult:
    """学习结果"""
    event_type: str
    content: str
    impact: float
    related_memory_id: Optional[str] = None
    related_belief_id: Optional[str] = None


class ContinuousLearningEngine:
    """持续学习引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    # ========== 从对话学习 ==========

    async def learn_from_conversation(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        ai_response: str
    ) -> List[LearningResult]:
        """
        从对话中学习

        分析对话内容，提取新知识和偏好。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            user_message: 用户消息
            ai_response: AI 回复

        Returns:
            学习结果列表
        """
        learnings = []

        # 使用 AI 分析对话中的学习点
        analysis_prompt = f"""分析以下对话，提取用户的新知识、偏好和观点。

用户：{user_message}

AI：{ai_response}

请识别：
1. 用户表达的新偏好（preference）
2. 用户提供的新事实（knowledge）
3. 用户的观点变化（opinion）
4. 值得记住的信息

以 JSON 格式返回：
{{
  "learnings": [
    {{
      "type": "preference|knowledge|opinion",
      "content": "学习内容",
      "impact": 0.0-1.0
    }}
  ]
}}

如果没有值得学习的内容，返回空列表 {{"learnings": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt="你是一个学习分析助手。只返回 JSON 格式的结果。",
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

            for item in result.get("learnings", []):
                learning = LearningResult(
                    event_type="new_knowledge",
                    content=item.get("content", ""),
                    impact=item.get("impact", 0.5)
                )
                learnings.append(learning)

                # 保存学习事件
                event = LearningEvent(
                    user_id=user_id,
                    event_type="new_knowledge",
                    source="conversation",
                    content=item.get("content", ""),
                    impact=item.get("impact", 0.5)
                )
                self.db.add(event)

            await self.db.flush()

        except Exception as e:
            print(f"对话学习失败: {str(e)}")

        return learnings

    # ========== 错误修正 ==========

    async def record_correction(
        self,
        user_id: str,
        conversation_id: str,
        original_response: str,
        correction: str,
        correction_type: str = "content"
    ) -> Correction:
        """
        记录用户对 AI 的修正

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            original_response: AI 原始回答
            correction: 用户修正
            correction_type: 修正类型

        Returns:
            修正记录
        """
        # 使用 AI 分析修正内容，提取教训
        lesson_prompt = f"""分析以下 AI 回答和用户修正，提取教训。

AI 回答：{original_response}

用户修正：{correction}

请总结从这个修正中学到了什么（20字以内）。"""

        lesson = ""
        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": lesson_prompt}],
                system_prompt="你是一个学习分析助手。只返回简短的教训总结。",
                temperature=0.3,
                max_tokens=100
            )
            lesson = response.content.strip()
        except Exception:
            pass

        # 保存修正记录
        correction_record = Correction(
            user_id=user_id,
            conversation_id=conversation_id,
            original_ai_response=original_response,
            user_correction=correction,
            correction_type=correction_type,
            lesson_learned=lesson
        )
        self.db.add(correction_record)

        # 保存学习事件
        event = LearningEvent(
            user_id=user_id,
            event_type="correction_applied",
            source="correction",
            content=f"修正类型: {correction_type}, 教训: {lesson}",
            impact=0.8
        )
        self.db.add(event)

        await self.db.flush()
        return correction_record

    async def get_user_corrections(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Correction]:
        """获取用户的修正记录"""
        result = await self.db.execute(
            select(Correction)
            .where(Correction.user_id == user_id)
            .order_by(Correction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # ========== 偏好学习 ==========

    async def learn_preference(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        confidence: float = 0.7,
        source: str = "conversation"
    ) -> Preference:
        """
        学习用户偏好

        Args:
            user_id: 用户 ID
            category: 偏好类别
            key: 偏好键
            value: 偏好值
            confidence: 置信度
            source: 来源

        Returns:
            偏好记录
        """
        # 检查是否已存在
        result = await self.db.execute(
            select(Preference).where(
                Preference.user_id == user_id,
                Preference.category == category,
                Preference.key == key
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新现有偏好
            existing.value = value
            existing.confidence = min(1.0, existing.confidence + 0.1)
            count = int(existing.mention_count) + 1
            existing.mention_count = str(count)
            existing.last_confirmed = datetime.now(timezone.utc)
            preference = existing
        else:
            # 创建新偏好
            preference = Preference(
                user_id=user_id,
                category=category,
                key=key,
                value=value,
                confidence=confidence,
                source=source,
                last_confirmed=datetime.now(timezone.utc)
            )
            self.db.add(preference)

            # 保存学习事件
            event = LearningEvent(
                user_id=user_id,
                event_type="preference_learned",
                source=source,
                content=f"学习到偏好: {category}/{key} = {value}",
                impact=0.6
            )
            self.db.add(event)

        await self.db.flush()
        return preference

    async def learn_preferences_from_text(
        self,
        user_id: str,
        text: str
    ) -> List[Preference]:
        """从文本中自动学习偏好"""
        preference_prompt = f"""从以下文本中提取用户的偏好。

文本：{text[:1000]}

请提取以下类别的偏好：
- language: 语言/工具偏好
- style: 风格偏好
- format: 格式偏好
- content: 内容偏好
- other: 其他偏好

以 JSON 格式返回：
{{
  "preferences": [
    {{
      "category": "类别",
      "key": "偏好键",
      "value": "偏好值",
      "confidence": 0.0-1.0
    }}
  ]
}}

如果没有明显偏好，返回空列表 {{"preferences": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": preference_prompt}],
                system_prompt="你是一个偏好分析助手。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=500
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)
            preferences = []

            for item in result.get("preferences", []):
                pref = await self.learn_preference(
                    user_id=user_id,
                    category=item.get("category", "other"),
                    key=item.get("key", ""),
                    value=item.get("value", ""),
                    confidence=item.get("confidence", 0.7),
                    source="auto_extract"
                )
                preferences.append(pref)

            return preferences

        except Exception:
            return []

    async def get_user_preferences(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> List[Preference]:
        """获取用户偏好"""
        query = select(Preference).where(Preference.user_id == user_id)
        if category:
            query = query.where(Preference.category == category)
        query = query.order_by(Preference.confidence.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    # ========== 反馈循环 ==========

    async def record_feedback(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        rating: float,
        comment: str = "",
        feedback_type: str = "quality"
    ) -> Feedback:
        """
        记录用户反馈

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            message_id: 消息 ID
            rating: 评分 1-5
            comment: 评论
            feedback_type: 反馈类型

        Returns:
            反馈记录
        """
        feedback = Feedback(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating,
            comment=comment,
            feedback_type=feedback_type
        )
        self.db.add(feedback)

        # 保存学习事件
        event = LearningEvent(
            user_id=user_id,
            event_type="feedback_received",
            source="feedback",
            content=f"评分: {rating}, 评论: {comment[:50] if comment else '无'}",
            impact=0.3
        )
        self.db.add(event)

        await self.db.flush()
        return feedback

    async def get_user_feedback_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户反馈统计"""
        # 平均评分
        avg_result = await self.db.execute(
            select(func.avg(Feedback.rating)).where(Feedback.user_id == user_id)
        )
        avg_rating = avg_result.scalar() or 0

        # 总反馈数
        count_result = await self.db.execute(
            select(func.count()).select_from(Feedback).where(Feedback.user_id == user_id)
        )
        total_count = count_result.scalar() or 0

        # 最近反馈
        recent_result = await self.db.execute(
            select(Feedback)
            .where(Feedback.user_id == user_id)
            .order_by(Feedback.created_at.desc())
            .limit(5)
        )
        recent = recent_result.scalars().all()

        return {
            "average_rating": round(float(avg_rating), 2),
            "total_feedbacks": total_count,
            "recent_feedbacks": [
                {
                    "rating": f.rating,
                    "comment": f.comment,
                    "created_at": f.created_at.isoformat()
                }
                for f in recent
            ]
        }

    # ========== 认知模型更新 ==========

    async def update_cognitive_model(self, user_id: str) -> UserCognitiveModel:
        """
        更新用户认知模型

        基于所有学习事件更新用户的认知模型。
        """
        # 获取或创建模型
        result = await self.db.execute(
            select(UserCognitiveModel).where(UserCognitiveModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            model = UserCognitiveModel(user_id=user_id)
            self.db.add(model)

        # 统计学习事件
        event_count = (await self.db.execute(
            select(func.count()).select_from(LearningEvent)
            .where(LearningEvent.user_id == user_id)
        )).scalar() or 0

        # 统计交互次数
        conv_count = (await self.db.execute(
            select(func.count()).select_from(ConversationMessage)
            .join(Conversation)
            .where(Conversation.user_id == user_id)
        )).scalar() or 0

        # 获取最新偏好
        prefs_result = await self.db.execute(
            select(Preference)
            .where(Preference.user_id == user_id)
            .order_by(Preference.confidence.desc())
            .limit(10)
        )
        preferences = prefs_result.scalars().all()

        # 更新模型
        model.total_interactions = str(conv_count)
        model.total_learning_events = str(event_count)
        model.last_updated_at = datetime.now(timezone.utc)

        # 更新偏好
        response_prefs = {}
        for pref in preferences:
            if pref.category not in response_prefs:
                response_prefs[pref.category] = {}
            response_prefs[pref.category][pref.key] = pref.value

        model.response_preference = response_prefs

        # 计算学习速率（基于学习事件频率）
        if conv_count > 0:
            model.learning_rate = min(1.0, event_count / conv_count)

        await self.db.flush()
        return model

    async def get_learning_events(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[LearningEvent]:
        """获取学习事件"""
        result = await self.db.execute(
            select(LearningEvent)
            .where(LearningEvent.user_id == user_id)
            .order_by(LearningEvent.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_learning_stats(self, user_id: str) -> Dict[str, Any]:
        """获取学习统计"""
        # 总学习事件
        event_count = (await self.db.execute(
            select(func.count()).select_from(LearningEvent)
            .where(LearningEvent.user_id == user_id)
        )).scalar() or 0

        # 偏好数量
        pref_count = (await self.db.execute(
            select(func.count()).select_from(Preference)
            .where(Preference.user_id == user_id)
        )).scalar() or 0

        # 修正数量
        correction_count = (await self.db.execute(
            select(func.count()).select_from(Correction)
            .where(Correction.user_id == user_id)
        )).scalar() or 0

        # 反馈数量
        feedback_count = (await self.db.execute(
            select(func.count()).select_from(Feedback)
            .where(Feedback.user_id == user_id)
        )).scalar() or 0

        # 平均反馈评分
        avg_rating = (await self.db.execute(
            select(func.avg(Feedback.rating))
            .where(Feedback.user_id == user_id)
        )).scalar() or 0

        return {
            "total_learning_events": event_count,
            "total_preferences": pref_count,
            "total_corrections": correction_count,
            "total_feedbacks": feedback_count,
            "average_feedback_rating": round(float(avg_rating), 2)
        }


def get_continuous_learning_engine(db: AsyncSession) -> ContinuousLearningEngine:
    """获取持续学习引擎实例"""
    return ContinuousLearningEngine(db)
