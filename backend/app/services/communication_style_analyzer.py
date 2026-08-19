"""
Personal AI OS - Communication Style Analyzer
沟通风格和语言习惯分析器
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.communication_style import (
    CommunicationStyle, LanguageHabit, ConversationPattern,
    COMMUNICATION_STYLES, LANGUAGE_HABIT_TYPES, CONVERSATION_PATTERN_TYPES
)
from app.models.conversation import Conversation, ConversationMessage
from app.services.ai_service import create_ai_service


@dataclass
class StyleAnalysisResult:
    """风格分析结果"""
    formality: float
    directness: float
    emotional_expression: float
    verbosity: float
    humor: float
    professionalism: float
    question_asking: float
    preferred_mode: str
    response_length: str
    language_habits: List[Dict[str, Any]]
    conversation_patterns: List[Dict[str, Any]]


class CommunicationStyleAnalyzer:
    """沟通风格分析器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def analyze_user_style(
        self,
        user_id: str,
        max_messages: int = 100
    ) -> StyleAnalysisResult:
        """
        分析用户的沟通风格

        基于用户的对话历史，分析其沟通方式和语言习惯。
        """
        # 获取用户的消息
        result = await self.db.execute(
            select(ConversationMessage)
            .join(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(max_messages)
        )
        messages = result.scalars().all()

        # 只取用户的消息
        user_messages = [m.content for m in messages if m.role == "user"]

        if not user_messages:
            return self._get_default_style()

        # 合并消息用于分析
        all_text = "\n".join(user_messages[:50])

        style_prompt = f"""分析以下用户消息，评估其沟通风格。

用户消息（最近50条）：
{all_text[:3000]}

请评估以下维度（每个维度 0.0-1.0）：

1. formality (正式程度): 0=非常口语化，1=非常正式
2. directness (直接程度): 0=委婉含蓄，1=直接了当
3. emotional_expression (情感表达): 0=冷静理性，1=情感丰富
4. verbosity (详细程度): 0=简洁明了，1=详细冗长
5. humor (幽默感): 0=严肃认真，1=幽默风趣
6. professionalism (专业性): 0=随意聊天，1=专业严谨
7. question_asking (提问倾向): 0=很少提问，1=经常提问

同时分析：
- preferred_mode: 沟通偏好（文字/语音/混合）
- response_length: 回复长度偏好（简短/适中/详细）

以 JSON 格式返回：
{{
  "formality": 0.0-1.0,
  "directness": 0.0-1.0,
  "emotional_expression": 0.0-1.0,
  "verbosity": 0.0-1.0,
  "humor": 0.0-1.0,
  "professionalism": 0.0-1.0,
  "question_asking": 0.0-1.0,
  "preferred_mode": "文字|语音|混合",
  "response_length": "简短|适中|详细"
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": style_prompt}],
                system_prompt="你是一个专业的沟通风格分析专家。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=800
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            style_data = json.loads(content)

            # 提取语言习惯
            habits = await self._extract_language_habits(user_messages[:30])

            # 提取对话模式
            patterns = await self._extract_conversation_patterns(user_messages[:30])

            return StyleAnalysisResult(
                formality=style_data.get("formality", 0.5),
                directness=style_data.get("directness", 0.5),
                emotional_expression=style_data.get("emotional_expression", 0.5),
                verbosity=style_data.get("verbosity", 0.5),
                humor=style_data.get("humor", 0.5),
                professionalism=style_data.get("professionalism", 0.5),
                question_asking=style_data.get("question_asking", 0.5),
                preferred_mode=style_data.get("preferred_mode", "文字"),
                response_length=style_data.get("response_length", "适中"),
                language_habits=habits,
                conversation_patterns=patterns
            )

        except Exception as e:
            print(f"沟通风格分析失败: {str(e)}")
            return self._get_default_style()

    async def _extract_language_habits(
        self,
        messages: List[str]
    ) -> List[Dict[str, Any]]:
        """提取语言习惯"""
        if not messages:
            return []

        text = "\n".join(messages[:20])

        habit_prompt = f"""分析以下用户消息，提取语言习惯。

用户消息：
{text[:2000]}

请提取以下类型的语言习惯：
1. vocabulary: 词汇偏好（喜欢用的词）
2. phrase: 常用短语
3. sentence_pattern: 句式模式
4. greeting: 问候方式
5. closing: 结束语
6. filler: 填充词
7. emphasis: 强调方式

以 JSON 格式返回：
{{
  "habits": [
    {{
      "type": "习惯类型",
      "name": "习惯名称",
      "pattern": "模式描述",
      "frequency": 0.0-1.0,
      "examples": ["示例1", "示例2"]
    }}
  ]
}}

如果没有明显习惯，返回空列表 {{"habits": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": habit_prompt}],
                system_prompt="你是一个专业的语言分析助手。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=800
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content).get("habits", [])

        except Exception:
            return []

    async def _extract_conversation_patterns(
        self,
        messages: List[str]
    ) -> List[Dict[str, Any]]:
        """提取对话模式"""
        if not messages:
            return []

        text = "\n".join(messages[:20])

        pattern_prompt = f"""分析以下用户消息，提取对话模式。

用户消息：
{text[:2000]}

请识别以下对话模式：
1. greeting: 开场模式（如何开始对话）
2. question_asking: 提问模式（如何提问）
3. explanation: 解释模式（如何解释）
4. agreement: 同意模式（如何表示同意）
5. disagreement: 反对模式（如何表示反对）
6. request: 请求模式（如何提出请求）
7. gratitude: 感谢模式（如何表示感谢）

以 JSON 格式返回：
{{
  "patterns": [
    {{
      "type": "模式类型",
      "name": "模式名称",
      "description": "模式描述",
      "examples": ["示例1", "示例2"],
      "confidence": 0.0-1.0
    }}
  ]
}}

如果没有明显模式，返回空列表 {{"patterns": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": pattern_prompt}],
                system_prompt="你是一个专业的对话分析助手。只返回 JSON 格式的结果。",
                temperature=0.3,
                max_tokens=800
            )

            import json
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content).get("patterns", [])

        except Exception:
            return []

    def _get_default_style(self) -> StyleAnalysisResult:
        """获取默认风格"""
        return StyleAnalysisResult(
            formality=0.5,
            directness=0.5,
            emotional_expression=0.5,
            verbosity=0.5,
            humor=0.5,
            professionalism=0.5,
            question_asking=0.5,
            preferred_mode="文字",
            response_length="适中",
            language_habits=[],
            conversation_patterns=[]
        )

    async def save_style_analysis(
        self,
        user_id: str,
        analysis: StyleAnalysisResult
    ) -> CommunicationStyle:
        """保存沟通风格分析结果"""
        # 检查是否已存在
        result = await self.db.execute(
            select(CommunicationStyle).where(CommunicationStyle.user_id == user_id)
        )
        style = result.scalar_one_or_none()

        if style:
            style.formality = analysis.formality
            style.directness = analysis.directness
            style.emotional_expression = analysis.emotional_expression
            style.verbosity = analysis.verbosity
            style.humor = analysis.humor
            style.professionalism = analysis.professionalism
            style.question_asking = analysis.question_asking
            style.preferred_mode = analysis.preferred_mode
            style.response_length = analysis.response_length
            style.last_analyzed_at = datetime.now(timezone.utc)
        else:
            style = CommunicationStyle(
                user_id=user_id,
                formality=analysis.formality,
                directness=analysis.directness,
                emotional_expression=analysis.emotional_expression,
                verbosity=analysis.verbosity,
                humor=analysis.humor,
                professionalism=analysis.professionalism,
                question_asking=analysis.question_asking,
                preferred_mode=analysis.preferred_mode,
                response_length=analysis.response_length,
                last_analyzed_at=datetime.now(timezone.utc)
            )
            self.db.add(style)

        # 保存语言习惯
        for habit_data in analysis.language_habits:
            existing = await self.db.execute(
                select(LanguageHabit).where(
                    LanguageHabit.user_id == user_id,
                    LanguageHabit.habit_name == habit_data.get("name", "")
                )
            )
            if not existing.scalar_one_or_none():
                habit = LanguageHabit(
                    user_id=user_id,
                    habit_type=habit_data.get("type", ""),
                    habit_name=habit_data.get("name", ""),
                    pattern=habit_data.get("pattern", ""),
                    frequency=habit_data.get("frequency", 0.5),
                    examples=habit_data.get("examples", [])
                )
                self.db.add(habit)

        # 保存对话模式
        for pattern_data in analysis.conversation_patterns:
            existing = await self.db.execute(
                select(ConversationPattern).where(
                    ConversationPattern.user_id == user_id,
                    ConversationPattern.pattern_name == pattern_data.get("name", "")
                )
            )
            if not existing.scalar_one_or_none():
                pattern = ConversationPattern(
                    user_id=user_id,
                    pattern_type=pattern_data.get("type", ""),
                    pattern_name=pattern_data.get("name", ""),
                    description=pattern_data.get("description", ""),
                    examples=pattern_data.get("examples", []),
                    confidence=pattern_data.get("confidence", 0.7)
                )
                self.db.add(pattern)

        await self.db.flush()
        return style

    async def get_user_style(self, user_id: str) -> Optional[CommunicationStyle]:
        """获取用户的沟通风格"""
        result = await self.db.execute(
            select(CommunicationStyle).where(CommunicationStyle.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_language_habits(self, user_id: str) -> List[LanguageHabit]:
        """获取用户的语言习惯"""
        result = await self.db.execute(
            select(LanguageHabit).where(
                LanguageHabit.user_id == user_id
            ).order_by(LanguageHabit.frequency.desc())
        )
        return result.scalars().all()

    async def get_conversation_patterns(self, user_id: str) -> List[ConversationPattern]:
        """获取用户的对话模式"""
        result = await self.db.execute(
            select(ConversationPattern).where(
                ConversationPattern.user_id == user_id
            ).order_by(ConversationPattern.confidence.desc())
        )
        return result.scalars().all()

    def generate_system_prompt_addition(self, style: CommunicationStyle) -> str:
        """
        基于沟通风格生成系统提示词补充

        用于个性化 AI 回答
        """
        parts = []

        # 正式程度
        if style.formality > 0.7:
            parts.append("使用正式、专业的语言")
        elif style.formality < 0.3:
            parts.append("使用轻松、口语化的语言")

        # 直接程度
        if style.directness > 0.7:
            parts.append("直接回答，不要绕弯子")
        elif style.directness < 0.3:
            parts.append("委婉表达，注意措辞")

        # 情感表达
        if style.emotional_expression > 0.7:
            parts.append("适当表达情感和同理心")
        elif style.emotional_expression < 0.3:
            parts.append("保持冷静理性的语气")

        # 详细程度
        if style.verbosity > 0.7:
            parts.append("提供详细的解释和背景信息")
        elif style.verbosity < 0.3:
            parts.append("回答简洁明了，避免冗长")

        # 幽默感
        if style.humor > 0.7:
            parts.append("适当加入幽默元素")
        elif style.humor < 0.3:
            parts.append("保持严肃认真的语气")

        # 专业性
        if style.professionalism > 0.7:
            parts.append("使用专业术语和严谨的表达")
        elif style.professionalism < 0.3:
            parts.append("使用通俗易懂的语言")

        if parts:
            return "沟通风格要求：" + "；".join(parts) + "。"
        return ""


def get_communication_style_analyzer(db: AsyncSession) -> CommunicationStyleAnalyzer:
    """获取沟通风格分析器实例"""
    return CommunicationStyleAnalyzer(db)
