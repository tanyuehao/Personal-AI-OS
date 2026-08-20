"""
Personal AI OS - Reasoning Engine
自主推理引擎 - 独立分析 + 多步推理 + 类比推理
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.reasoning import (
    ReasoningSession, ReasoningChain, Analogy, ProactiveSuggestion,
    REASONING_TYPES, REASONING_STEP_TYPES, SUGGESTION_TYPES
)
from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision
from app.services.ai_service import create_ai_service


@dataclass
class ReasoningResult:
    """推理结果"""
    reasoning_type: str
    conclusion: str
    confidence: float
    steps: List[Dict[str, Any]]
    evidence: List[str]
    analogies: List[Dict[str, Any]]


class ReasoningEngine:
    """自主推理引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    # ========== 独立分析 ==========

    async def analyze_independently(
        self,
        user_id: str,
        query: str,
        reasoning_type: str = "analytical"
    ) -> ReasoningResult:
        """
        独立分析问题

        基于用户的知识库、记忆和观点，独立分析问题。

        Args:
            user_id: 用户 ID
            query: 分析问题
            reasoning_type: 推理类型

        Returns:
            推理结果
        """
        # 获取相关上下文
        context = await self._gather_context(user_id, query)

        # 构建分析提示词
        analysis_prompt = f"""基于以下信息，独立分析这个问题。

问题：{query}

用户的知识背景：
{context.get('knowledge', '无')}

用户的相关记忆：
{context.get('memories', '无')}

用户的相关观点：
{context.get('beliefs', '无')}

用户的历史决策：
{context.get('decisions', '无')}

请进行独立分析，提供：
1. 观察到的关键信息
2. 形成的假设
3. 支持的证据
4. 分析过程
5. 得出的结论
6. 置信度评估

以 JSON 格式返回：
{{
  "reasoning_type": "推理类型",
  "conclusion": "结论（100字以内）",
  "confidence": 0.0-1.0,
  "steps": [
    {{
      "step_number": "1",
      "step_type": "observation|hypothesis|evidence|analysis|inference|conclusion",
      "content": "步骤内容",
      "confidence": 0.0-1.0
    }}
  ],
  "evidence": ["证据1", "证据2"],
  "analogies": [
    {{
      "situation": "类似情境",
      "lesson": "经验教训",
      "similarity": 0.0-1.0
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt="你是一个专业的分析推理专家。基于用户的个人资料进行独立分析。只返回 JSON 格式的结果。",
                temperature=0.5,
                max_tokens=2000
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            return ReasoningResult(
                reasoning_type=result.get("reasoning_type", reasoning_type),
                conclusion=result.get("conclusion", ""),
                confidence=result.get("confidence", 0.5),
                steps=result.get("steps", []),
                evidence=result.get("evidence", []),
                analogies=result.get("analogies", [])
            )

        except Exception as e:
            print(f"独立分析失败: {str(e)}")
            return ReasoningResult(
                reasoning_type=reasoning_type,
                conclusion="分析失败，请稍后重试",
                confidence=0.0,
                steps=[],
                evidence=[],
                analogies=[]
            )

    async def _gather_context(self, user_id: str, query: str) -> Dict[str, str]:
        """收集分析上下文"""
        context = {}

        # 获取相关记忆
        memory_result = await self.db.execute(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            )
            .order_by(Memory.importance.desc())
            .limit(10)
        )
        memories = memory_result.scalars().all()
        context["memories"] = "\n".join([
            f"- ({m.memory_type}) {m.content[:80]}"
            for m in memories
        ]) if memories else "无"

        # 获取相关观点
        belief_result = await self.db.execute(
            select(Belief)
            .where(
                Belief.user_id == user_id,
                Belief.status == "ACTIVE"
            )
            .order_by(Belief.confidence.desc())
            .limit(10)
        )
        beliefs = belief_result.scalars().all()
        context["beliefs"] = "\n".join([
            f"- [{b.topic}] {b.content[:80]}"
            for b in beliefs
        ]) if beliefs else "无"

        # 获取历史决策
        decision_result = await self.db.execute(
            select(Decision)
            .where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc())
            .limit(5)
        )
        decisions = decision_result.scalars().all()
        context["decisions"] = "\n".join([
            f"- {d.problem}: {d.choice or '未定'}"
            for d in decisions
        ]) if decisions else "无"

        context["knowledge"] = "基于用户的知识库"  # 简化

        return context

    # ========== 多步推理 ==========

    async def multi_step_reasoning(
        self,
        user_id: str,
        query: str,
        max_steps: int = 5
    ) -> ReasoningResult:
        """
        多步推理

        将复杂问题分解为多个步骤进行推理。

        Args:
            user_id: 用户 ID
            query: 推理问题
            max_steps: 最大步骤数

        Returns:
            推理结果
        """
        # 获取上下文
        context = await self._gather_context(user_id, query)

        reasoning_prompt = f"""请对以下问题进行多步推理分析（最多 {max_steps} 步）。

问题：{query}

用户背景：
{context.get('memories', '无')}
{context.get('beliefs', '无')}
{context.get('decisions', '无')}

推理步骤要求：
1. 观察：识别关键信息
2. 假设：提出可能的解释
3. 证据：寻找支持或反对的证据
4. 分析：综合分析
5. 结论：得出最终结论

以 JSON 格式返回：
{{
  "reasoning_type": "deductive",
  "conclusion": "最终结论",
  "confidence": 0.0-1.0,
  "steps": [
    {{
      "step_number": "1",
      "step_type": "observation",
      "content": "观察到...",
      "confidence": 0.8
    }},
    {{
      "step_number": "2",
      "step_type": "hypothesis",
      "content": "假设...",
      "confidence": 0.6
    }}
  ],
  "evidence": ["证据1", "证据2"],
  "analogies": []
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": reasoning_prompt}],
                system_prompt="你是一个专业的多步推理专家。只返回 JSON 格式的结果。",
                temperature=0.5,
                max_tokens=2000
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            return ReasoningResult(
                reasoning_type=result.get("reasoning_type", "deductive"),
                conclusion=result.get("conclusion", ""),
                confidence=result.get("confidence", 0.5),
                steps=result.get("steps", []),
                evidence=result.get("evidence", []),
                analogies=result.get("analogies", [])
            )

        except Exception as e:
            print(f"多步推理失败: {str(e)}")
            return ReasoningResult(
                reasoning_type="deductive",
                conclusion="推理失败，请稍后重试",
                confidence=0.0,
                steps=[],
                evidence=[],
                analogies=[]
            )

    # ========== 类比推理 ==========

    async def analogical_reasoning(
        self,
        user_id: str,
        current_situation: str
    ) -> ReasoningResult:
        """
        类比推理

        基于历史经验，对新情况进行类比推理。

        Args:
            user_id: 用户 ID
            current_situation: 当前情境

        Returns:
            推理结果
        """
        # 获取历史决策
        decision_result = await self.db.execute(
            select(Decision)
            .where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc())
            .limit(10)
        )
        decisions = decision_result.scalars().all()

        # 获取相关记忆
        memory_result = await self.db.execute(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            )
            .order_by(Memory.importance.desc())
            .limit(10)
        )
        memories = memory_result.scalars().all()

        history_text = "\n".join([
            f"决策: {d.problem} -> {d.choice or '未定'} (结果: {d.actual_result or '未知'})"
            for d in decisions
        ]) if decisions else "无历史决策"

        memory_text = "\n".join([
            f"记忆: ({m.memory_type}) {m.content[:60]}"
            for m in memories
        ]) if memories else "无相关记忆"

        analogy_prompt = f"""基于用户的历史经验和记忆，对以下情况进行类比推理。

当前情境：{current_situation}

历史决策：
{history_text}

相关记忆：
{memory_text}

请：
1. 找出与当前情境最相似的历史经验
2. 分析相似之处和不同之处
3. 从历史经验中提取可借鉴的教训
4. 给出针对当前情境的建议

以 JSON 格式返回：
{{
  "reasoning_type": "analogical",
  "conclusion": "结论",
  "confidence": 0.0-1.0,
  "steps": [
    {{
      "step_number": "1",
      "step_type": "observation",
      "content": "观察到当前情境的特征"
    }},
    {{
      "step_number": "2",
      "step_type": "evidence",
      "content": "找到的相似历史经验"
    }},
    {{
      "step_number": "3",
      "step_type": "analysis",
      "content": "分析相似和不同之处"
    }},
    {{
      "step_number": "4",
      "step_type": "conclusion",
      "content": "结论和建议"
    }}
  ],
  "evidence": ["证据1", "证据2"],
  "analogies": [
    {{
      "situation": "历史情境",
      "lesson": "经验教训",
      "similarity": 0.8
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": analogy_prompt}],
                system_prompt="你是一个专业的类比推理专家。基于用户的历史经验进行推理。只返回 JSON 格式的结果。",
                temperature=0.5,
                max_tokens=2000
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            # 保存类比
            for analogy_data in result.get("analogies", []):
                analogy = Analogy(
                    user_id=user_id,
                    source_situation=current_situation,
                    target_situation=analogy_data.get("situation", ""),
                    similarity_score=analogy_data.get("similarity", 0.5),
                    lesson=analogy_data.get("lesson", "")
                )
                self.db.add(analogy)

            await self.db.flush()

            return ReasoningResult(
                reasoning_type="analogical",
                conclusion=result.get("conclusion", ""),
                confidence=result.get("confidence", 0.5),
                steps=result.get("steps", []),
                evidence=result.get("evidence", []),
                analogies=result.get("analogies", [])
            )

        except Exception as e:
            print(f"类比推理失败: {str(e)}")
            return ReasoningResult(
                reasoning_type="analogical",
                conclusion="类比推理失败，请稍后重试",
                confidence=0.0,
                steps=[],
                evidence=[],
                analogies=[]
            )

    # ========== 保存推理结果 ==========

    async def save_reasoning_session(
        self,
        user_id: str,
        query: str,
        result: ReasoningResult
    ) -> ReasoningSession:
        """保存推理会话"""
        session = ReasoningSession(
            user_id=user_id,
            query=query,
            reasoning_type=result.reasoning_type,
            conclusion=result.conclusion,
            confidence=result.confidence,
            reasoning_steps=result.steps,
            evidence_used=result.evidence,
            analogies_used=result.analogies
        )
        self.db.add(session)
        await self.db.flush()

        # 保存推理链
        for step in result.steps:
            chain = ReasoningChain(
                session_id=session.session_id,
                step_number=step.get("step_number", "0"),
                step_type=step.get("step_type", "analysis"),
                content=step.get("content", ""),
                confidence=step.get("confidence", 0.5),
                evidence=step.get("evidence")
            )
            self.db.add(chain)

        await self.db.flush()
        return session

    async def get_reasoning_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ReasoningSession]:
        """获取推理历史"""
        result = await self.db.execute(
            select(ReasoningSession)
            .where(ReasoningSession.user_id == user_id)
            .order_by(ReasoningSession.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_analogies(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Analogy]:
        """获取类比记录"""
        result = await self.db.execute(
            select(Analogy)
            .where(Analogy.user_id == user_id)
            .order_by(Analogy.similarity_score.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # ========== 主动建议 ==========

    async def generate_suggestions(
        self,
        user_id: str
    ) -> List[ProactiveSuggestion]:
        """
        基于推理生成主动建议

        分析用户的数据，生成有价值的建议。
        """
        # 获取上下文
        context = await self._gather_context(user_id, "")

        suggestion_prompt = f"""基于用户的个人资料，生成 3-5 条有价值的主动建议。

用户的知识背景：
{context.get('knowledge', '无')}

用户的相关记忆：
{context.get('memories', '无')}

用户的相关观点：
{context.get('beliefs', '无')}

用户的历史决策：
{context.get('decisions', '无')}

请生成建议，每条建议包含：
- title: 标题
- description: 描述
- type: 类型（action/learning/decision/improvement/exploration）
- priority: 优先级（high/medium/low）
- confidence: 置信度
- reasoning: 推理过程
- actions: 行动项列表

以 JSON 格式返回：
{{
  "suggestions": [
    {{
      "title": "建议标题",
      "description": "建议描述",
      "type": "建议类型",
      "priority": "优先级",
      "confidence": 0.0-1.0,
      "reasoning": "推理过程",
      "actions": ["行动1", "行动2"]
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": suggestion_prompt}],
                system_prompt="你是一个专业的建议生成专家。基于用户的个人资料生成有价值的建议。只返回 JSON 格式的结果。",
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

            suggestions = []
            for item in result.get("suggestions", []):
                suggestion = ProactiveSuggestion(
                    user_id=user_id,
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    suggestion_type=item.get("type", "action"),
                    priority=item.get("priority", "medium"),
                    confidence=item.get("confidence", 0.5),
                    reasoning=item.get("reasoning", ""),
                    action_items=item.get("actions", [])
                )
                self.db.add(suggestion)
                suggestions.append(suggestion)

            await self.db.flush()
            return suggestions

        except Exception as e:
            print(f"建议生成失败: {str(e)}")
            return []

    async def get_user_suggestions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ProactiveSuggestion]:
        """获取用户的主动建议"""
        result = await self.db.execute(
            select(ProactiveSuggestion)
            .where(
                ProactiveSuggestion.user_id == user_id,
                ProactiveSuggestion.is_dismissed == False
            )
            .order_by(ProactiveSuggestion.confidence.desc())
            .limit(limit)
        )
        return result.scalars().all()


def get_reasoning_engine(db: AsyncSession) -> ReasoningEngine:
    """获取推理引擎实例"""
    return ReasoningEngine(db)
