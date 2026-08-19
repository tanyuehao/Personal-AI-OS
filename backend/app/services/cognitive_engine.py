"""
Personal AI OS - Cognitive Engine
认知引擎 - 自动提取观点、检测冲突、关联决策
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.belief import Belief, BeliefHistory
from app.models.memory import Memory
from app.models.decision import Decision
from app.services.ai_service import create_ai_service


@dataclass
class ExtractedBelief:
    """提取的观点"""
    topic: str
    content: str
    confidence: float
    evidence: Optional[str] = None


@dataclass
class ConflictSignal:
    """冲突信号"""
    existing_belief_id: str
    existing_content: str
    new_content: str
    conflict_type: str  # "contradiction", "nuance", "evolution"
    explanation: str


class CognitiveEngine:
    """认知引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def extract_beliefs_from_conversation(
        self,
        user_id: str,
        messages: List[Dict[str, str]]
    ) -> List[ExtractedBelief]:
        """
        从对话中提取观点候选

        Args:
            user_id: 用户 ID
            messages: 对话消息列表

        Returns:
            提取的观点列表
        """
        if not messages:
            return []

        # 构建提取提示词
        conversation_text = "\n".join([
            f"{'用户' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')}"
            for m in messages
        ])

        extraction_prompt = f"""分析以下对话，提取用户明确表达的观点、看法、判断和偏好。

对话内容：
{conversation_text}

请提取用户的观点，注意：
1. 只提取用户明确表达的观点，不要推断
2. 区分事实陈述和观点表达
3. 每个观点应该是一个独立的判断

以 JSON 格式返回：
{{
  "beliefs": [
    {{
      "topic": "主题（简短）",
      "content": "观点内容（完整句子）",
      "confidence": 0.0-1.0,
      "evidence": "来源（可选）"
    }}
  ]
}}

如果没有值得提取的观点，返回空列表 {{"beliefs": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": extraction_prompt}],
                system_prompt="你是一个专业的信息提取助手。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=1000
            )

            # 解析响应
            import json
            content = response.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            beliefs = []
            for item in result.get("beliefs", []):
                beliefs.append(ExtractedBelief(
                    topic=item.get("topic", ""),
                    content=item.get("content", ""),
                    confidence=item.get("confidence", 0.7),
                    evidence=item.get("evidence")
                ))

            return beliefs

        except Exception as e:
            print(f"观点提取失败: {str(e)}")
            return []

    async def detect_conflicts(
        self,
        user_id: str,
        new_content: str,
        topic: Optional[str] = None
    ) -> List[ConflictSignal]:
        """
        检测新观点与现有观点的冲突

        Args:
            user_id: 用户 ID
            new_content: 新观点内容
            topic: 主题（可选）

        Returns:
            冲突信号列表
        """
        # 获取相关现有观点
        query = select(Belief).where(
            Belief.user_id == user_id,
            Belief.status == "ACTIVE"
        )

        if topic:
            query = query.where(Belief.topic.ilike(f"%{topic}%"))

        result = await self.db.execute(query)
        existing_beliefs = result.scalars().all()

        if not existing_beliefs:
            return []

        # 构建冲突检测提示词
        beliefs_text = "\n".join([
            f"- [{b.topic}] {b.content} (可信度: {b.confidence})"
            for b in existing_beliefs
        ])

        conflict_prompt = f"""分析新观点是否与用户现有的观点存在冲突或演变。

现有观点：
{beliefs_text}

新观点：{new_content}

请判断：
1. 是否与现有观点矛盾（contradiction）
2. 是否是现有观点的细化（nuance）
3. 是否是观点的演变（evolution）
4. 是否是全新观点（no_conflict）

以 JSON 格式返回：
{{
  "conflicts": [
    {{
      "belief_id": "冲突的观点ID",
      "existing_content": "现有观点内容",
      "new_content": "新观点内容",
      "conflict_type": "contradiction|nuance|evolution|no_conflict",
      "explanation": "解释"
    }}
  ]
}}

如果没有冲突，返回空列表 {{"conflicts": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": conflict_prompt}],
                system_prompt="你是一个专业的观点分析助手。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=1000
            )

            import json
            content = response.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            conflicts = []
            for item in result.get("conflicts", []):
                if item.get("conflict_type") != "no_conflict":
                    conflicts.append(ConflictSignal(
                        existing_belief_id=item.get("belief_id", ""),
                        existing_content=item.get("existing_content", ""),
                        new_content=item.get("new_content", new_content),
                        conflict_type=item.get("conflict_type", "nuance"),
                        explanation=item.get("explanation", "")
                    ))

            return conflicts

        except Exception as e:
            print(f"冲突检测失败: {str(e)}")
            return []

    async def link_decision_to_context(
        self,
        user_id: str,
        decision_id: str
    ) -> Dict[str, Any]:
        """
        将决策关联到相关记忆和观点

        Args:
            user_id: 用户 ID
            decision_id: 决策 ID

        Returns:
            关联结果
        """
        # 获取决策
        result = await self.db.execute(
            select(Decision).where(Decision.decision_id == decision_id)
        )
        decision = result.scalar_one_or_none()

        if not decision:
            return {"error": "决策不存在"}

        # 获取相关记忆
        memory_result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            ).order_by(Memory.importance.desc()).limit(20)
        )
        memories = memory_result.scalars().all()

        # 获取相关观点
        belief_result = await self.db.execute(
            select(Belief).where(
                Belief.user_id == user_id,
                Belief.status == "ACTIVE"
            )
        )
        beliefs = belief_result.scalars().all()

        # 使用 AI 分析关联
        context_text = f"""
决策：{decision.problem}
选择：{decision.choice or '未定'}
理由：{decision.reasoning or '未提供'}

相关记忆：
{chr(10).join([f"- {m.content}" for m in memories[:10]])}

相关观点：
{chr(10).join([f"- [{b.topic}] {b.content}" for b in beliefs[:10]])}
"""

        link_prompt = f"""分析以下决策与用户记忆和观点的关联。

{context_text}

请识别：
1. 哪些记忆影响了这个决策
2. 哪些观点与这个决策相关
3. 这个决策可能产生的新记忆

以 JSON 格式返回：
{{
  "linked_memories": ["相关记忆内容"],
  "linked_beliefs": ["相关观点内容"],
  "potential_memories": ["可能产生的新记忆"],
  "analysis": "关联分析"
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": link_prompt}],
                system_prompt="你是一个专业的决策分析助手。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=1000
            )

            import json
            content = response.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content)

        except Exception as e:
            print(f"决策关联失败: {str(e)}")
            return {"error": str(e)}

    async def calculate_memory_score(
        self,
        importance: float,
        confidence: float,
        frequency: int,
        user_confirmed: bool
    ) -> float:
        """
        计算记忆推荐分数

        score = 0.35 * importance + 0.25 * confidence + 0.20 * recurrence + 0.20 * explicit_user_signal

        Args:
            importance: 重要程度 0-1
            confidence: 可信程度 0-1
            frequency: 出现频率
            user_confirmed: 是否用户确认

        Returns:
            推荐分数 0-1
        """
        # 归一化频率（0-1）
        recurrence = min(frequency / 10, 1.0)

        # 用户确认信号
        explicit_signal = 1.0 if user_confirmed else 0.3

        score = (
            0.35 * importance +
            0.25 * confidence +
            0.20 * recurrence +
            0.20 * explicit_signal
        )

        return round(min(max(score, 0), 1), 4)


# 全局实例
cognitive_engine = None


def get_cognitive_engine(db: AsyncSession) -> CognitiveEngine:
    """获取认知引擎实例"""
    return CognitiveEngine(db)
