"""
Personal AI OS - Smarter Engine
比你更聪明引擎 - 盲区发现 + 反面论证 + 跨领域综合 + 最优实践 + 决策优化
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision
from app.services.ai_service import create_ai_service


@dataclass
class BlindSpot:
    """盲区"""
    area: str
    description: str
    impact: str
    suggestion: str
    confidence: float


@dataclass
class CounterArgument:
    """反面论证"""
    original_claim: str
    counter_claim: str
    evidence: List[str]
    strength: float  # 反面论证的强度 0-1
    recommendation: str


@dataclass
class CrossDomainInsight:
    """跨领域洞察"""
    domain_a: str
    domain_b: str
    connection: str
    insight: str
    value: str


@dataclass
class BestPractice:
    """最佳实践"""
    area: str
    practice: str
    description: str
    source: str
    applicability: float  # 适用度 0-1


@dataclass
class DecisionOptimization:
    """决策优化"""
    original_decision: str
    alternative: str
    reasoning: str
    expected_improvement: str
    confidence: float


class SmarterEngine:
    """比你更聪明引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def _gather_user_context(self, user_id: str) -> Dict[str, str]:
        """收集用户上下文"""
        context = {}

        # 获取记忆
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            ).order_by(Memory.importance.desc()).limit(20)
        )
        memories = result.scalars().all()
        context["memories"] = "\n".join([f"- ({m.memory_type}) {m.content}" for m in memories])

        # 获取观点
        result = await self.db.execute(
            select(Belief).where(
                Belief.user_id == user_id,
                Belief.status == "ACTIVE"
            ).order_by(Belief.confidence.desc()).limit(15)
        )
        beliefs = result.scalars().all()
        context["beliefs"] = "\n".join([f"- [{b.topic}] {b.content} (可信度: {b.confidence})" for b in beliefs])

        # 获取决策
        result = await self.db.execute(
            select(Decision).where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc()).limit(10)
        )
        decisions = result.scalars().all()
        context["decisions"] = "\n".join([
            f"- {d.problem}: {d.choice or '未定'} (理由: {d.reasoning or '无'})"
            for d in decisions
        ])

        return context

    # ========== 盲区发现 ==========

    async def find_blind_spots(self, user_id: str) -> List[BlindSpot]:
        """
        发现用户的思维盲区

        分析用户的知识、观点和决策，找出可能的盲点。
        """
        context = await self._gather_user_context(user_id)

        prompt = f"""分析以下用户的知识、观点和决策，找出可能的思维盲区。

用户的记忆：
{context.get('memories', '无')}

用户的观点：
{context.get('beliefs', '无')}

用户的决策：
{context.get('decisions', '无')}

请找出 3-5 个可能的盲区，每个盲区包含：
- area: 盲区领域
- description: 盲区描述
- impact: 如果不注意会有什么影响
- suggestion: 如何弥补这个盲区
- confidence: 置信度（0-1）

以 JSON 格式返回：
{{
  "blind_spots": [
    {{
      "area": "领域",
      "description": "描述",
      "impact": "影响",
      "suggestion": "建议",
      "confidence": 0.8
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="你是一个专业的思维分析专家。找出用户可能忽视的角度。只返回 JSON 格式的结果。",
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

            return [
                BlindSpot(
                    area=item.get("area", ""),
                    description=item.get("description", ""),
                    impact=item.get("impact", ""),
                    suggestion=item.get("suggestion", ""),
                    confidence=item.get("confidence", 0.5)
                )
                for item in result.get("blind_spots", [])
            ]

        except Exception as e:
            print(f"盲区发现失败: {str(e)}")
            return []

    # ========== 反面论证 ==========

    async def generate_counter_arguments(
        self,
        user_id: str,
        claim: str
    ) -> List[CounterArgument]:
        """
        生成反面论证

        对用户的观点提出反面论据。
        """
        context = await self._gather_user_context(user_id)

        prompt = f"""对以下观点提出反面论据和质疑。

用户的观点：{claim}

用户的背景：
{context.get('beliefs', '无')}

请提出 2-3 个有力的反面论据，每个包含：
- counter_claim: 反面观点
- evidence: 支持反面观点的证据（至少2条）
- strength: 反面论证的强度（0-1）
- recommendation: 建议（如何平衡正反面）

以 JSON 格式返回：
{{
  "counter_arguments": [
    {{
      "counter_claim": "反面观点",
      "evidence": ["证据1", "证据2"],
      "strength": 0.8,
      "recommendation": "建议"
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="你是一个批判性思维专家。提出有力的反面论据帮助用户全面思考。只返回 JSON 格式的结果。",
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

            return [
                CounterArgument(
                    original_claim=claim,
                    counter_claim=item.get("counter_claim", ""),
                    evidence=item.get("evidence", []),
                    strength=item.get("strength", 0.5),
                    recommendation=item.get("recommendation", "")
                )
                for item in result.get("counter_arguments", [])
            ]

        except Exception as e:
            print(f"反面论证失败: {str(e)}")
            return []

    # ========== 跨领域综合 ==========

    async def find_cross_domain_insights(
        self,
        user_id: str
    ) -> List[CrossDomainInsight]:
        """
        发现跨领域洞察

        连接用户不同领域的知识，发现新的联系。
        """
        context = await self._gather_user_context(user_id)

        prompt = f"""分析用户的知识，找出不同领域之间的联系和洞察。

用户的记忆：
{context.get('memories', '无')}

用户的观点：
{context.get('beliefs', '无')}

用户的决策：
{context.get('decisions', '无')}

请找出 2-3 个跨领域的洞察，每个包含：
- domain_a: 领域A
- domain_b: 领域B
- connection: 两者之间的联系
- insight: 从中得出的洞察
- value: 这个洞察的价值

以 JSON 格式返回：
{{
  "insights": [
    {{
      "domain_a": "领域A",
      "domain_b": "领域B",
      "connection": "联系",
      "insight": "洞察",
      "value": "价值"
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="你是一个跨领域综合分析专家。发现不同知识领域之间的联系。只返回 JSON 格式的结果。",
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

            return [
                CrossDomainInsight(
                    domain_a=item.get("domain_a", ""),
                    domain_b=item.get("domain_b", ""),
                    connection=item.get("connection", ""),
                    insight=item.get("insight", ""),
                    value=item.get("value", "")
                )
                for item in result.get("insights", [])
            ]

        except Exception as e:
            print(f"跨领域分析失败: {str(e)}")
            return []

    # ========== 最优实践推荐 ==========

    async def recommend_best_practices(
        self,
        user_id: str,
        area: str = ""
    ) -> List[BestPractice]:
        """
        推荐最佳实践

        基于用户的情况，推荐行业最佳实践。
        """
        context = await self._gather_user_context(user_id)

        prompt = f"""基于用户的情况，推荐相关的最佳实践。

用户的记忆：
{context.get('memories', '无')}

用户的观点：
{context.get('beliefs', '无')}

{'关注领域：' + area if area else '请根据用户的情况推荐相关领域'}

请推荐 3-5 个最佳实践，每个包含：
- area: 领域
- practice: 实践名称
- description: 详细描述
- source: 来源（行业标准/知名公司/研究等）
- applicability: 适用度（0-1）

以 JSON 格式返回：
{{
  "practices": [
    {{
      "area": "领域",
      "practice": "实践名称",
      "description": "描述",
      "source": "来源",
      "applicability": 0.8
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="你是一个行业最佳实践顾问。推荐最有效的方法和实践。只返回 JSON 格式的结果。",
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

            return [
                BestPractice(
                    area=item.get("area", ""),
                    practice=item.get("practice", ""),
                    description=item.get("description", ""),
                    source=item.get("source", ""),
                    applicability=item.get("applicability", 0.5)
                )
                for item in result.get("practices", [])
            ]

        except Exception as e:
            print(f"最佳实践推荐失败: {str(e)}")
            return []

    # ========== 决策优化 ==========

    async def optimize_decision(
        self,
        user_id: str,
        decision_problem: str,
        current_choice: str = ""
    ) -> List[DecisionOptimization]:
        """
        优化决策

        分析用户的决策，给出更好的替代方案。
        """
        context = await self._gather_user_context(user_id)

        prompt = f"""分析以下决策，给出更好的替代方案。

决策问题：{decision_problem}
当前选择：{current_choice or '未定'}

用户的背景：
{context.get('memories', '无')}
{context.get('decisions', '无')}

请给出 2-3 个替代方案，每个包含：
- alternative: 替代方案
- reasoning: 选择理由
- expected_improvement: 预期改进
- confidence: 置信度（0-1）

以 JSON 格式返回：
{{
  "optimizations": [
    {{
      "alternative": "替代方案",
      "reasoning": "理由",
      "expected_improvement": "预期改进",
      "confidence": 0.8
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="你是一个决策优化专家。基于用户的情况给出更好的替代方案。只返回 JSON 格式的结果。",
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

            return [
                DecisionOptimization(
                    original_decision=decision_problem,
                    alternative=item.get("alternative", ""),
                    reasoning=item.get("reasoning", ""),
                    expected_improvement=item.get("expected_improvement", ""),
                    confidence=item.get("confidence", 0.5)
                )
                for item in result.get("optimizations", [])
            ]

        except Exception as e:
            print(f"决策优化失败: {str(e)}")
            return []


def get_smarter_engine(db: AsyncSession) -> SmarterEngine:
    """获取比你更聪明引擎实例"""
    return SmarterEngine(db)
