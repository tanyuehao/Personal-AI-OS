"""
Personal AI OS - Self-Transcendence Engine
自我超越闭环引擎 - 串联所有模块形成持续进化循环

循环流程：
感知 → 理解 → 预测 → 规划 → 行动 → 学习 → 改进 → 感知...
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.ai_service import create_ai_service


@dataclass
class CycleResult:
    """循环结果"""
    cycle_id: str
    cycle_type: str
    phase_results: Dict[str, Any]
    insights: List[str]
    improvements: List[str]
    next_actions: List[str]
    confidence: float
    timestamp: str


class SelfTranscendenceEngine:
    """
    自我超越闭环引擎

    串联所有模块形成持续进化循环：
    1. 感知 (Perceive) - 上下文感知，了解用户当前状态
    2. 理解 (Understand) - 认知模型，理解用户深层特征
    3. 预测 (Predict) - 预测用户下一步需求
    4. 规划 (Plan) - 自主行动规划
    5. 行动 (Act) - 执行行动计划
    6. 学习 (Learn) - 持续学习从交互中获取新知识
    7. 改进 (Improve) - 比你更聪明引擎，发现盲区并改进
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def run_full_cycle(self, user_id: str) -> CycleResult:
        """
        运行完整的自我超越循环

        串联所有模块，形成一次完整的感知-理解-预测-规划-行动-学习-改进循环。
        """
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        phase_results = {}
        all_insights = []
        all_improvements = []
        all_next_actions = []

        # ========== Phase 1: 感知 ==========
        print("[Cycle] Phase 1: 感知...")
        try:
            from app.services.context_awareness import get_context_awareness_engine
            context_engine = get_context_awareness_engine(self.db)
            context = await context_engine.get_current_context(user_id)
            phase_results["perceive"] = {
                "mood": context.current_mood,
                "energy": context.energy_level,
                "focus": len(context.active_focus),
                "activities": len(context.recent_activities)
            }
            all_insights.append(f"当前状态: {context.current_mood}, 精力: {context.energy_level:.0%}")
        except Exception as e:
            phase_results["perceive"] = {"error": str(e)}

        # ========== Phase 2: 理解 ==========
        print("[Cycle] Phase 2: 理解...")
        try:
            from app.services.cognitive_model import get_cognitive_model
            model = get_cognitive_model(self.db)
            profile = await model.build_cognitive_profile(user_id)
            phase_results["understand"] = {
                "thinking_style": profile.thinking_style,
                "decision_style": profile.decision_style,
                "strengths": len(profile.strengths),
                "weaknesses": len(profile.weaknesses)
            }
            all_insights.append(f"认知画像置信度: {profile.confidence:.0%}")
        except Exception as e:
            phase_results["understand"] = {"error": str(e)}

        # ========== Phase 3: 预测 ==========
        print("[Cycle] Phase 3: 预测...")
        try:
            from app.services.prediction_engine import get_prediction_engine
            pred_engine = get_prediction_engine(self.db)
            predictions = await pred_engine.predict_needs(user_id)
            await pred_engine.save_predictions(user_id, predictions)
            phase_results["predict"] = {
                "predictions_count": len(predictions),
                "top_prediction": predictions[0].title if predictions else "无"
            }
            if predictions:
                all_next_actions.append(predictions[0].suggested_action)
        except Exception as e:
            phase_results["predict"] = {"error": str(e)}

        # ========== Phase 4: 规划 ==========
        print("[Cycle] Phase 4: 规划...")
        try:
            from app.services.autonomous_action import get_autonomous_action_engine
            action_engine = get_autonomous_action_engine(self.db)

            # 基于预测生成行动计划
            if predictions:
                plan = await action_engine.plan_action(
                    user_id,
                    f"基于预测: {predictions[0].title}",
                    predictions[0].description
                )
                phase_results["plan"] = {
                    "plan_title": plan.title,
                    "steps": len(plan.steps),
                    "requires_approval": plan.requires_approval
                }
            else:
                phase_results["plan"] = {"message": "无预测，跳过规划"}
        except Exception as e:
            phase_results["plan"] = {"error": str(e)}

        # ========== Phase 5: 行动 ==========
        print("[Cycle] Phase 5: 行动...")
        try:
            # 获取最近的已批准计划
            from app.services.autonomous_action import get_autonomous_action_engine
            action_engine = get_autonomous_action_engine(self.db)
            pending = await action_engine.get_pending_approvals(user_id)

            if pending:
                # 批准并执行第一个计划
                plan = pending[0]
                await action_engine.approve_action(user_id, plan.plan_id)
                result = await action_engine.execute_action(user_id, plan.plan_id)
                phase_results["act"] = {
                    "executed_plan": plan.title,
                    "status": result.status
                }
            else:
                phase_results["act"] = {"message": "无待执行计划"}
        except Exception as e:
            phase_results["act"] = {"error": str(e)}

        # ========== Phase 6: 学习 ==========
        print("[Cycle] Phase 6: 学习...")
        try:
            from app.services.continuous_learning import get_continuous_learning_engine
            learning_engine = get_continuous_learning_engine(self.db)
            stats = await learning_engine.get_learning_stats(user_id)
            phase_results["learn"] = {
                "total_events": stats["total_learning_events"],
                "preferences": stats["total_preferences"],
                "corrections": stats["total_corrections"]
            }
        except Exception as e:
            phase_results["learn"] = {"error": str(e)}

        # ========== Phase 7: 改进 ==========
        print("[Cycle] Phase 7: 改进...")
        try:
            from app.services.smarter_engine import get_smarter_engine
            smarter = get_smarter_engine(self.db)

            # 发现盲区
            blind_spots = await smarter.find_blind_spots(user_id)
            for spot in blind_spots[:2]:
                all_improvements.append(f"盲区: {spot.area} - {spot.suggestion}")

            # 跨领域洞察
            cross_insights = await smarter.find_cross_domain_insights(user_id)
            for insight in cross_insights[:2]:
                all_improvements.append(f"跨领域: {insight.domain_a} ↔ {insight.domain_b}")

            phase_results["improve"] = {
                "blind_spots": len(blind_spots),
                "cross_insights": len(cross_insights)
            }
        except Exception as e:
            phase_results["improve"] = {"error": str(e)}

        # ========== 生成综合洞察 ==========
        try:
            ai_service = await self._get_ai_service()

            summary_prompt = f"""基于以下循环结果，生成综合洞察和改进建议。

循环结果：
{chr(10).join([f"- {k}: {v}" for k, v in phase_results.items()])}

已有洞察：
{chr(10).join([f"- {i}" for i in all_insights])}

已有改进：
{chr(10).join([f"- {i}" for i in all_improvements])}

请生成：
1. 3-5 条综合洞察
2. 3-5 条改进建议
3. 3-5 个下一步行动

以 JSON 格式返回：
{{
  "insights": ["洞察1", "洞察2"],
  "improvements": ["改进1", "改进2"],
  "next_actions": ["行动1", "行动2"],
  "confidence": 0.8
}}"""

            response = await ai_service.chat(
                messages=[{"role": "user", "content": summary_prompt}],
                system_prompt="你是一个系统分析师。基于循环结果生成综合洞察。只返回 JSON 格式的结果。",
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
            all_insights.extend(result.get("insights", []))
            all_improvements.extend(result.get("improvements", []))
            all_next_actions.extend(result.get("next_actions", []))
            confidence = result.get("confidence", 0.7)

        except Exception:
            confidence = 0.5

        return CycleResult(
            cycle_id=cycle_id,
            cycle_type="full",
            phase_results=phase_results,
            insights=all_insights[:5],
            improvements=all_improvements[:5],
            next_actions=all_next_actions[:5],
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def get_cycle_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取循环历史"""
        # 这里可以存储循环历史到数据库
        # 目前返回最近的模拟数据
        return []

    async def get_system_health(self, user_id: str) -> Dict[str, Any]:
        """获取系统健康状态"""
        modules_status = {}

        # 检查各个模块
        modules = [
            ("认知模型", "cognitive_model"),
            ("上下文感知", "context_awareness"),
            ("预测引擎", "prediction_engine"),
            ("自主行动", "autonomous_action"),
            ("持续学习", "continuous_learning"),
            ("比你聪明", "smarter_engine"),
            ("决策风格", "decision_style_analyzer"),
            ("沟通风格", "communication_style_analyzer"),
        ]

        for name, module_name in modules:
            try:
                module = __import__(f"app.services.{module_name}", fromlist=[module_name])
                modules_status[name] = "✅ 正常"
            except Exception as e:
                modules_status[name] = f"❌ 异常: {str(e)[:50]}"

        return {
            "modules": modules_status,
            "total_modules": len(modules),
            "healthy_modules": sum(1 for v in modules_status.values() if "✅" in v),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def get_self_transcendence_engine(db: AsyncSession) -> SelfTranscendenceEngine:
    """获取自我超越闭环引擎实例"""
    return SelfTranscendenceEngine(db)
