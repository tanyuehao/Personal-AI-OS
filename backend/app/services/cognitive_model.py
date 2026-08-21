"""
Personal AI OS - Unified Cognitive Model
统一认知模型 - 融合所有模块数据，建立用户深度画像
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision
from app.models.document import Document
from app.models.conversation import Conversation
from app.services.ai_service import create_ai_service


@dataclass
class CognitiveProfile:
    """用户认知画像"""
    # 身份信息
    user_id: str
    
    # 知识图谱
    knowledge_domains: List[str] = field(default_factory=list)
    knowledge_depth: Dict[str, float] = field(default_factory=dict)
    
    # 思维模式
    thinking_style: str = ""
    decision_style: str = ""
    communication_style: str = ""
    learning_style: str = ""
    
    # 价值观
    core_values: List[str] = field(default_factory=list)
    priorities: Dict[str, float] = field(default_factory=dict)
    
    # 行为模式
    work_patterns: List[str] = field(default_factory=list)
    habits: List[str] = field(default_factory=list)
    
    # 情感特征
    emotional_tendency: str = ""
    stress_response: str = ""
    motivation_drivers: List[str] = field(default_factory=list)
    
    # 社交特征
    collaboration_style: str = ""
    communication_preference: str = ""
    
    # 成长轨迹
    growth_areas: List[str] = field(default_factory=list)
    recent_changes: List[str] = field(default_factory=list)
    
    # 综合评估
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    # 置信度
    confidence: float = 0.5
    last_updated: str = ""


class UnifiedCognitiveModel:
    """统一认知模型"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def build_cognitive_profile(self, user_id: str) -> CognitiveProfile:
        """
        构建用户认知画像

        融合所有模块的数据，建立对用户的深度理解。
        """
        # 收集所有数据
        data = await self._collect_all_data(user_id)

        # 使用 AI 分析生成认知画像
        profile = await self._analyze_cognitive_profile(user_id, data)

        return profile

    async def _collect_all_data(self, user_id: str) -> Dict[str, Any]:
        """收集所有模块的数据"""
        data = {}

        # 1. 记忆
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            ).order_by(Memory.importance.desc()).limit(30)
        )
        memories = result.scalars().all()
        data["memories"] = [
            {"type": m.memory_type, "content": m.content, "importance": m.importance}
            for m in memories
        ]

        # 2. 观点
        result = await self.db.execute(
            select(Belief).where(
                Belief.user_id == user_id,
                Belief.status == "ACTIVE"
            ).order_by(Belief.confidence.desc()).limit(20)
        )
        beliefs = result.scalars().all()
        data["beliefs"] = [
            {"topic": b.topic, "content": b.content, "confidence": b.confidence}
            for b in beliefs
        ]

        # 3. 决策
        result = await self.db.execute(
            select(Decision).where(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc()).limit(20)
        )
        decisions = result.scalars().all()
        data["decisions"] = [
            {"problem": d.problem, "choice": d.choice, "reasoning": d.reasoning, "risk": d.risk}
            for d in decisions
        ]

        # 4. 文档
        result = await self.db.execute(
            select(Document).where(Document.user_id == user_id)
            .order_by(Document.created_at.desc()).limit(10)
        )
        documents = result.scalars().all()
        data["documents"] = [
            {"name": d.file_name, "type": d.file_type, "summary": (d.summary or "")[:200]}
            for d in documents
        ]

        # 5. 对话
        result = await self.db.execute(
            select(Conversation.title).where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc()).limit(20)
        )
        conversations = result.scalars().all()
        data["conversations"] = [c[0] for c in conversations if c[0]]

        # 6. 决策风格
        from app.models.decision_style import DecisionStyle
        result = await self.db.execute(
            select(DecisionStyle).where(DecisionStyle.user_id == user_id)
        )
        style = result.scalar_one_or_none()
        if style:
            data["decision_style"] = {
                "risk_tolerance": style.risk_tolerance,
                "analysis_depth": style.analysis_depth,
                "decisiveness": style.decisiveness,
                "collaboration": style.collaboration,
                "primary_style": style.primary_style
            }

        # 7. 沟通风格
        from app.models.communication_style import CommunicationStyle
        result = await self.db.execute(
            select(CommunicationStyle).where(CommunicationStyle.user_id == user_id)
        )
        comm_style = result.scalar_one_or_none()
        if comm_style:
            data["communication_style"] = {
                "formality": comm_style.formality,
                "directness": comm_style.directness,
                "verbosity": comm_style.verbosity,
                "humor": comm_style.humor
            }

        return data

    async def _analyze_cognitive_profile(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> CognitiveProfile:
        """使用 AI 分析生成认知画像"""

        # 构建分析提示词
        memories_text = "\n".join([
            f"- ({m['type']}) {m['content']}"
            for m in data.get("memories", [])[:15]
        ])

        beliefs_text = "\n".join([
            f"- [{b['topic']}] {b['content']}"
            for b in data.get("beliefs", [])[:10]
        ])

        decisions_text = "\n".join([
            f"- {d['problem']}: {d['choice'] or '未定'} (理由: {d['reasoning'] or '无'})"
            for d in data.get("decisions", [])[:10]
        ])

        docs_text = "\n".join([
            f"- {d['name']} ({d['type']}): {d['summary'][:100]}"
            for d in data.get("documents", [])[:10]
        ])

        style_info = data.get("decision_style", {})
        comm_info = data.get("communication_style", {})

        analysis_prompt = f"""基于以下所有数据，构建一个完整的用户认知画像。

用户的记忆：
{memories_text or '无'}

用户的观点：
{beliefs_text or '无'}

用户的决策：
{decisions_text or '无'}

用户的文档：
{docs_text or '无'}

用户的对话话题：
{', '.join(data.get('conversations', [])[:10]) or '无'}

决策风格：
- 风险偏好: {style_info.get('risk_tolerance', 0.5)}
- 分析深度: {style_info.get('analysis_depth', 0.5)}
- 果断程度: {style_info.get('decisiveness', 0.5)}
- 主要风格: {style_info.get('primary_style', '未知')}

沟通风格：
- 正式度: {comm_info.get('formality', 0.5)}
- 直接度: {comm_info.get('directness', 0.5)}
- 详细度: {comm_info.get('verbosity', 0.5)}

请构建完整的认知画像，包含：

1. knowledge_domains: 用户的知识领域列表
2. thinking_style: 思维风格（一句话描述）
3. decision_style: 决策风格（一句话描述）
4. communication_style: 沟通风格（一句话描述）
5. learning_style: 学习风格（一句话描述）
6. core_values: 核心价值观列表（3-5个）
7. priorities: 优先级排序（字典，key是领域，value是0-1的优先级）
8. work_patterns: 工作模式列表
9. habits: 习惯列表
10. emotional_tendency: 情感倾向（一句话）
11. motivation_drivers: 动机驱动列表（3-5个）
12. collaboration_style: 协作风格（一句话）
13. growth_areas: 成长领域列表
14. recent_changes: 近期变化列表
15. strengths: 优势列表（3-5个）
16. weaknesses: 劣势列表（3-5个）
17. opportunities: 机会列表（3-5个）
18. confidence: 整体置信度（0-1）

以 JSON 格式返回。"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt="你是一个专业的认知心理学家和用户画像专家。基于所有可用数据构建深度用户画像。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=2000
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            return CognitiveProfile(
                user_id=user_id,
                knowledge_domains=result.get("knowledge_domains", []),
                thinking_style=result.get("thinking_style", ""),
                decision_style=result.get("decision_style", ""),
                communication_style=result.get("communication_style", ""),
                learning_style=result.get("learning_style", ""),
                core_values=result.get("core_values", []),
                priorities=result.get("priorities", {}),
                work_patterns=result.get("work_patterns", []),
                habits=result.get("habits", []),
                emotional_tendency=result.get("emotional_tendency", ""),
                motivation_drivers=result.get("motivation_drivers", []),
                collaboration_style=result.get("collaboration_style", ""),
                growth_areas=result.get("growth_areas", []),
                recent_changes=result.get("recent_changes", []),
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                opportunities=result.get("opportunities", []),
                confidence=result.get("confidence", 0.5),
                last_updated=datetime.now(timezone.utc).isoformat()
            )

        except Exception as e:
            print(f"认知画像分析失败: {str(e)}")
            return CognitiveProfile(user_id=user_id)

    async def get_cognitive_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户认知画像（返回字典格式）"""
        profile = await self.build_cognitive_profile(user_id)

        return {
            "user_id": profile.user_id,
            "knowledge_domains": profile.knowledge_domains,
            "thinking_style": profile.thinking_style,
            "decision_style": profile.decision_style,
            "communication_style": profile.communication_style,
            "learning_style": profile.learning_style,
            "core_values": profile.core_values,
            "priorities": profile.priorities,
            "work_patterns": profile.work_patterns,
            "habits": profile.habits,
            "emotional_tendency": profile.emotional_tendency,
            "motivation_drivers": profile.motivation_drivers,
            "collaboration_style": profile.collaboration_style,
            "growth_areas": profile.growth_areas,
            "recent_changes": profile.recent_changes,
            "strengths": profile.strengths,
            "weaknesses": profile.weaknesses,
            "opportunities": profile.opportunities,
            "confidence": profile.confidence,
            "last_updated": profile.last_updated
        }

    async def get_user_summary(self, user_id: str) -> str:
        """获取用户摘要（自然语言）"""
        profile = await self.build_cognitive_profile(user_id)

        summary_parts = []
        if profile.thinking_style:
            summary_parts.append(f"思维风格：{profile.thinking_style}")
        if profile.decision_style:
            summary_parts.append(f"决策风格：{profile.decision_style}")
        if profile.communication_style:
            summary_parts.append(f"沟通风格：{profile.communication_style}")
        if profile.core_values:
            summary_parts.append(f"核心价值：{'、'.join(profile.core_values[:3])}")
        if profile.strengths:
            summary_parts.append(f"优势：{'、'.join(profile.strengths[:3])}")
        if profile.growth_areas:
            summary_parts.append(f"成长领域：{'、'.join(profile.growth_areas[:3])}")

        return "；".join(summary_parts) if summary_parts else "暂无足够数据生成摘要"


def get_cognitive_model(db: AsyncSession) -> UnifiedCognitiveModel:
    """获取统一认知模型实例"""
    return UnifiedCognitiveModel(db)
