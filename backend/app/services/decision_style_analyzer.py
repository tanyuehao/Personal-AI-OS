"""
Personal AI OS - Decision Style Analyzer
决策风格分析器 - 建模用户思维方式和决策模式
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.decision import Decision
from app.models.decision_style import DecisionStyle, DecisionPattern
from app.models.memory import Memory
from app.models.belief import Belief
from app.services.ai_service import create_ai_service


# 决策风格类型定义
DECISION_STYLES = {
    "analytical": {
        "name": "分析型",
        "description": "喜欢收集大量信息，系统性地分析所有选项，基于数据和逻辑做出决策",
        "indicators": ["深度分析", "数据驱动", "系统性思考", "风险评估"]
    },
    "intuitive": {
        "name": "直觉型",
        "description": "依赖直觉和经验快速做出决策，相信第一反应",
        "indicators": ["快速决策", "经验驱动", "信任直觉", "模式识别"]
    },
    "directive": {
        "name": "指令型",
        "description": "果断、自信，快速做出决策并执行，不纠结细节",
        "indicators": ["果断决策", "快速执行", "自信", "结果导向"]
    },
    "conceptual": {
        "name": "概念型",
        "description": "关注长远愿景和创新可能性，喜欢探索新想法",
        "indicators": ["创新思维", "长远视角", "探索性", "开放性"]
    },
    "behavioral": {
        "name": "行为型",
        "description": "重视人际关系和团队协作，考虑决策对他人的影响",
        "indicators": ["协作导向", "人际敏感", "团队考虑", "沟通优先"]
    },
    "hesitant": {
        "name": "犹豫型",
        "description": "在决策时犹豫不决，需要更多信息才能做出选择",
        "indicators": ["信息收集", "延迟决策", "风险厌恶", "完美主义"]
    }
}


@dataclass
class StyleAnalysisResult:
    """风格分析结果"""
    risk_tolerance: float
    analysis_depth: float
    decisiveness: float
    collaboration: float
    time_preference: float
    evidence_reliance: float
    intuition_ratio: float
    emotional_influence: float
    primary_style: str
    secondary_style: str
    style_description: str
    patterns: List[Dict[str, Any]]


class DecisionStyleAnalyzer:
    """决策风格分析器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def analyze_user_style(self, user_id: str) -> StyleAnalysisResult:
        """
        分析用户的决策风格

        基于用户的所有决策记录，分析其决策模式和风格。
        """
        # 获取所有决策
        result = await self.db.execute(
            select(Decision).where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc())
        )
        decisions = result.scalars().all()

        # 获取相关记忆
        memory_result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            ).order_by(Memory.importance.desc()).limit(30)
        )
        memories = memory_result.scalars().all()

        # 获取观点
        belief_result = await self.db.execute(
            select(Belief).where(
                Belief.user_id == user_id,
                Belief.status == "ACTIVE"
            )
        )
        beliefs = belief_result.scalars().all()

        # 如果没有决策记录，返回默认风格
        if not decisions:
            return StyleAnalysisResult(
                risk_tolerance=0.5,
                analysis_depth=0.5,
                decisiveness=0.5,
                collaboration=0.5,
                time_preference=0.5,
                evidence_reliance=0.5,
                intuition_ratio=0.5,
                emotional_influence=0.5,
                primary_style="analytical",
                secondary_style="intuitive",
                style_description="暂无足够数据进行分析",
                patterns=[]
            )

        # 使用 AI 分析决策风格
        decisions_text = "\n".join([
            f"- 问题: {d.problem}\n  选择: {d.choice or '未定'}\n  理由: {d.reasoning or '未提供'}\n  风险: {d.risk or '未评估'}"
            for d in decisions[:20]
        ])

        memories_text = "\n".join([
            f"- ({m.memory_type}) {m.content[:80]}"
            for m in memories[:10]
        ])

        beliefs_text = "\n".join([
            f"- [{b.topic}] {b.content[:80]}"
            for b in beliefs[:10]
        ])

        analysis_prompt = f"""基于以下决策记录、记忆和观点，分析用户的决策风格。

决策记录：
{decisions_text}

相关记忆：
{memories_text}

用户观点：
{beliefs_text}

请分析以下维度（每个维度 0.0-1.0）：

1. risk_tolerance (风险偏好): 0=极度保守，1=极度冒险
2. analysis_depth (分析深度): 0=直觉决策，1=深度分析
3. decisiveness (果断程度): 0=犹豫不决，1=非常果断
4. collaboration (协作倾向): 0=独立决策，1=依赖协作
5. time_preference (时间偏好): 0=短期导向，1=长期导向
6. evidence_reliance (证据依赖): 0=依赖经验，1=依赖数据
7. intuition_ratio (直觉比例): 0=纯分析，1=纯直觉
8. emotional_influence (情绪影响): 0=冷静理性，1=情绪化

同时识别：
- primary_style: 主要决策风格（analytical/intuitive/directive/conceptual/behavioral/hesitant）
- secondary_style: 次要决策风格
- style_description: 风格描述（50字以内）
- patterns: 具体的决策模式（至少2个）

以 JSON 格式返回：
{{
  "risk_tolerance": 0.0-1.0,
  "analysis_depth": 0.0-1.0,
  "decisiveness": 0.0-1.0,
  "collaboration": 0.0-1.0,
  "time_preference": 0.0-1.0,
  "evidence_reliance": 0.0-1.0,
  "intuition_ratio": 0.0-1.0,
  "emotional_influence": 0.0-1.0,
  "primary_style": "风格类型",
  "secondary_style": "风格类型",
  "style_description": "50字以内描述",
  "patterns": [
    {{
      "type": "模式类型",
      "name": "模式名称",
      "description": "模式描述",
      "confidence": 0.0-1.0
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt="你是一个专业的决策分析专家。只返回 JSON 格式的结果。",
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

            return StyleAnalysisResult(
                risk_tolerance=result.get("risk_tolerance", 0.5),
                analysis_depth=result.get("analysis_depth", 0.5),
                decisiveness=result.get("decisiveness", 0.5),
                collaboration=result.get("collaboration", 0.5),
                time_preference=result.get("time_preference", 0.5),
                evidence_reliance=result.get("evidence_reliance", 0.5),
                intuition_ratio=result.get("intuition_ratio", 0.5),
                emotional_influence=result.get("emotional_influence", 0.5),
                primary_style=result.get("primary_style", "analytical"),
                secondary_style=result.get("secondary_style", "intuitive"),
                style_description=result.get("style_description", ""),
                patterns=result.get("patterns", [])
            )

        except Exception as e:
            print(f"决策风格分析失败: {str(e)}")
            return StyleAnalysisResult(
                risk_tolerance=0.5,
                analysis_depth=0.5,
                decisiveness=0.5,
                collaboration=0.5,
                time_preference=0.5,
                evidence_reliance=0.5,
                intuition_ratio=0.5,
                emotional_influence=0.5,
                primary_style="analytical",
                secondary_style="intuitive",
                style_description="分析失败，请稍后重试",
                patterns=[]
            )

    async def save_style_analysis(
        self,
        user_id: str,
        analysis: StyleAnalysisResult
    ) -> DecisionStyle:
        """保存决策风格分析结果"""
        # 检查是否已存在
        result = await self.db.execute(
            select(DecisionStyle).where(DecisionStyle.user_id == user_id)
        )
        style = result.scalar_one_or_none()

        if style:
            # 更新现有记录
            style.risk_tolerance = analysis.risk_tolerance
            style.analysis_depth = analysis.analysis_depth
            style.decisiveness = analysis.decisiveness
            style.collaboration = analysis.collaboration
            style.time_preference = analysis.time_preference
            style.evidence_reliance = analysis.evidence_reliance
            style.intuition_ratio = analysis.intuition_ratio
            style.emotional_influence = analysis.emotional_influence
            style.primary_style = analysis.primary_style
            style.secondary_style = analysis.secondary_style
            style.style_description = analysis.style_description
            style.last_analyzed_at = datetime.now(timezone.utc)
        else:
            # 创建新记录
            style = DecisionStyle(
                user_id=user_id,
                risk_tolerance=analysis.risk_tolerance,
                analysis_depth=analysis.analysis_depth,
                decisiveness=analysis.decisiveness,
                collaboration=analysis.collaboration,
                time_preference=analysis.time_preference,
                evidence_reliance=analysis.evidence_reliance,
                intuition_ratio=analysis.intuition_ratio,
                emotional_influence=analysis.emotional_influence,
                primary_style=analysis.primary_style,
                secondary_style=analysis.secondary_style,
                style_description=analysis.style_description,
                last_analyzed_at=datetime.now(timezone.utc)
            )
            self.db.add(style)

        # 保存模式
        for pattern in analysis.patterns:
            # 检查模式是否已存在
            pattern_result = await self.db.execute(
                select(DecisionPattern).where(
                    DecisionPattern.user_id == user_id,
                    DecisionPattern.pattern_name == pattern.get("name", "")
                )
            )
            existing_pattern = pattern_result.scalar_one_or_none()

            if not existing_pattern:
                new_pattern = DecisionPattern(
                    user_id=user_id,
                    pattern_type=pattern.get("type", ""),
                    pattern_name=pattern.get("name", ""),
                    description=pattern.get("description", ""),
                    confidence=pattern.get("confidence", 0.7)
                )
                self.db.add(new_pattern)

        await self.db.flush()
        await self.db.refresh(style)

        return style

    async def get_user_style(self, user_id: str) -> Optional[DecisionStyle]:
        """获取用户的决策风格"""
        result = await self.db.execute(
            select(DecisionStyle).where(DecisionStyle.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_patterns(self, user_id: str) -> List[DecisionPattern]:
        """获取用户的决策模式"""
        result = await self.db.execute(
            select(DecisionPattern).where(
                DecisionPattern.user_id == user_id
            ).order_by(DecisionPattern.confidence.desc())
        )
        return result.scalars().all()

    async def get_style_recommendations(
        self,
        user_id: str,
        decision_context: str
    ) -> List[str]:
        """
        基于用户风格提供决策建议

        Args:
            user_id: 用户 ID
            decision_context: 决策上下文

        Returns:
            建议列表
        """
        style = await self.get_user_style(user_id)
        if not style:
            return ["暂无足够的决策数据，无法提供个性化建议"]

        style_info = DECISION_STYLES.get(style.primary_style, {})

        prompt = f"""基于用户的决策风格，为以下决策场景提供建议。

用户决策风格：
- 主要风格: {style_info.get('name', style.primary_style)}
- 风险偏好: {style.risk_tolerance:.2f} (0=保守, 1=冒险)
- 分析深度: {style.analysis_depth:.2f} (0=直觉, 1=分析)
- 果断程度: {style.decisiveness:.2f} (0=犹豫, 1=果断)
- 证据依赖: {style.evidence_reliance:.2f} (0=经验, 1=数据)

决策场景：{decision_context}

请提供 3 条针对性的建议，帮助用户发挥优势、避免盲点。"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="你是一个专业的决策教练。",
                temperature=0.5,
                max_tokens=500
            )

            # 解析建议
            lines = response.content.strip().split("\n")
            recommendations = [line.strip().lstrip("0123456789.、- ") for line in lines if line.strip()][:3]

            return recommendations if recommendations else ["建议生成失败，请稍后重试"]

        except Exception:
            return ["建议生成失败，请稍后重试"]


def get_decision_style_analyzer(db: AsyncSession) -> DecisionStyleAnalyzer:
    """获取决策风格分析器实例"""
    return DecisionStyleAnalyzer(db)
