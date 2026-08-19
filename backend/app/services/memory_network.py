"""
Personal AI OS - Memory Network Service
记忆网络服务 - 遗忘曲线 + 记忆强化 + 联想召回
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.memory import Memory
from app.models.memory_network import (
    MemoryAssociation, MemoryStrength, MemoryCluster,
    ASSOCIATION_TYPES
)
from app.services.ai_service import create_ai_service


@dataclass
class MemoryScore:
    """记忆评分"""
    memory_id: str
    content: str
    strength: float
    decay: float
    association_count: int
    last_accessed: Optional[str]


class MemoryNetwork:
    """记忆网络服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    # ========== 遗忘曲线 ==========

    def calculate_forgetting_curve(
        self,
        base_strength: float,
        time_since_last_review: float,  # 小时
        decay_rate: float = 0.1
    ) -> float:
        """
        计算遗忘曲线（艾宾浩斯遗忘曲线简化版）

        S(t) = S0 * e^(-λt)

        Args:
            base_strength: 基础强度 (0-1)
            time_since_last_review: 距离上次复习的时间（小时）
            decay_rate: 衰减速率

        Returns:
            当前强度 (0-1)
        """
        current_strength = base_strength * math.exp(-decay_rate * time_since_last_review / 24)
        return max(0.0, min(1.0, current_strength))

    async def update_memory_strengths(self, user_id: str):
        """
        更新所有记忆的强度（考虑遗忘曲线）

        应该定期调用（如每天一次）
        """
        # 获取所有记忆强度记录
        result = await self.db.execute(
            select(MemoryStrength).where(MemoryStrength.user_id == user_id)
        )
        strengths = result.scalars().all()

        now = datetime.now(timezone.utc)

        for strength in strengths:
            # 计算距离上次复习的时间
            if strength.last_reviewed:
                hours_since_review = (now - strength.last_reviewed).total_seconds() / 3600
            else:
                hours_since_review = (now - strength.created_at).total_seconds() / 3600

            # 计算当前强度
            current = self.calculate_forgetting_curve(
                strength.base_strength,
                hours_since_review,
                strength.decay_rate
            )

            strength.current_strength = current

        await self.db.flush()

    async def get_memory_strength(
        self,
        user_id: str,
        memory_id: str
    ) -> Optional[MemoryStrength]:
        """获取记忆强度"""
        result = await self.db.execute(
            select(MemoryStrength).where(
                MemoryStrength.user_id == user_id,
                MemoryStrength.memory_id == memory_id
            )
        )
        return result.scalar_one_or_none()

    async def ensure_memory_strength(
        self,
        user_id: str,
        memory_id: str
    ) -> MemoryStrength:
        """确保记忆有强度记录"""
        strength = await self.get_memory_strength(user_id, memory_id)

        if not strength:
            strength = MemoryStrength(
                user_id=user_id,
                memory_id=memory_id,
                base_strength=0.5,
                current_strength=0.5,
                decay_rate=0.1
            )
            self.db.add(strength)
            await self.db.flush()

        return strength

    # ========== 记忆强化 ==========

    async def reinforce_memory(
        self,
        user_id: str,
        memory_id: str,
        reinforcement: float = 0.1
    ):
        """
        强化记忆（复习后调用）

        Args:
            user_id: 用户 ID
            memory_id: 记忆 ID
            reinforcement: 强化程度 (0-0.5)
        """
        strength = await self.ensure_memory_strength(user_id, memory_id)

        # 增加基础强度
        strength.base_strength = min(1.0, strength.base_strength + reinforcement)

        # 更新当前强度
        strength.current_strength = strength.base_strength

        # 更新复习信息
        strength.last_reviewed = datetime.now(timezone.utc)
        review_count = int(strength.review_count) + 1
        strength.review_count = str(review_count)

        # 根据复习次数调整衰减速率（间隔重复效应）
        # 复习越多，衰减越慢
        strength.decay_rate = max(0.01, 0.1 / (1 + review_count * 0.1))

        await self.db.flush()

    async def batch_reinforce_memories(
        self,
        user_id: str,
        memory_ids: List[str],
        reinforcement: float = 0.1
    ):
        """批量强化记忆"""
        for memory_id in memory_ids:
            await self.reinforce_memory(user_id, memory_id, reinforcement)

    # ========== 联想召回 ==========

    async def create_association(
        self,
        user_id: str,
        source_memory_id: str,
        target_memory_id: str,
        association_type: str = "semantic",
        strength: float = 1.0,
        context: str = ""
    ) -> MemoryAssociation:
        """创建记忆关联"""
        # 检查是否已存在
        result = await self.db.execute(
            select(MemoryAssociation).where(
                MemoryAssociation.user_id == user_id,
                MemoryAssociation.source_memory_id == source_memory_id,
                MemoryAssociation.target_memory_id == target_memory_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 增强现有关联
            existing.strength = min(1.0, existing.strength + 0.1)
            existing.last_activated = datetime.now(timezone.utc)
            return existing

        # 创建新关联
        association = MemoryAssociation(
            user_id=user_id,
            source_memory_id=source_memory_id,
            target_memory_id=target_memory_id,
            association_type=association_type,
            strength=strength,
            context=context,
            last_activated=datetime.now(timezone.utc)
        )
        self.db.add(association)
        await self.db.flush()
        return association

    async def recall_associations(
        self,
        user_id: str,
        memory_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        联想召回 - 基于一个记忆召回相关记忆

        Args:
            user_id: 用户 ID
            memory_id: 记忆 ID
            limit: 返回数量

        Returns:
            相关记忆列表
        """
        # 查找出边关联
        outgoing_result = await self.db.execute(
            select(MemoryAssociation).where(
                MemoryAssociation.source_memory_id == memory_id
            ).order_by(MemoryAssociation.strength.desc()).limit(limit)
        )
        outgoing = outgoing_result.scalars().all()

        # 查找入边关联
        incoming_result = await self.db.execute(
            select(MemoryAssociation).where(
                MemoryAssociation.target_memory_id == memory_id
            ).order_by(MemoryAssociation.strength.desc()).limit(limit)
        )
        incoming = incoming_result.scalars().all()

        # 合并并去重
        associated_memory_ids = set()
        associations = []

        for assoc in outgoing:
            if assoc.target_memory_id not in associated_memory_ids:
                associated_memory_ids.add(assoc.target_memory_id)
                associations.append({
                    "memory_id": str(assoc.target_memory_id),
                    "association_type": assoc.association_type,
                    "strength": assoc.strength,
                    "direction": "outgoing",
                    "context": assoc.context
                })

        for assoc in incoming:
            if assoc.source_memory_id not in associated_memory_ids:
                associated_memory_ids.add(assoc.source_memory_id)
                associations.append({
                    "memory_id": str(assoc.source_memory_id),
                    "association_type": assoc.association_type,
                    "strength": assoc.strength,
                    "direction": "incoming",
                    "context": assoc.context
                })

        # 按强度排序
        associations.sort(key=lambda x: x["strength"], reverse=True)

        # 获取记忆内容
        if associated_memory_ids:
            memory_result = await self.db.execute(
                select(Memory).where(
                    Memory.memory_id.in_(associated_memory_ids)
                )
            )
            memory_map = {str(m.memory_id): m for m in memory_result.scalars().all()}

            for assoc in associations:
                mem = memory_map.get(assoc["memory_id"])
                if mem:
                    assoc["content"] = mem.content
                    assoc["memory_type"] = mem.memory_type
                    assoc["importance"] = mem.importance

        return associations[:limit]

    # ========== 记忆聚类 ==========

    async def cluster_memories(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        将相似记忆分组

        Args:
            user_id: 用户 ID

        Returns:
            聚类列表
        """
        # 获取所有已确认的记忆
        result = await self.db.execute(
            select(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            ).order_by(Memory.importance.desc())
        )
        memories = result.scalars().all()

        if len(memories) < 3:
            return []

        # 使用 AI 进行聚类
        memory_list = "\n".join([
            f"[{m.memory_id}] ({m.memory_type}) {m.content[:60]}"
            for m in memories[:50]
        ])

        cluster_prompt = f"""将以下记忆按主题或类型进行分组。

记忆列表：
{memory_list}

请将记忆分成 3-5 个聚类，每个聚类包含：
- name: 聚类名称
- type: 聚类类型（topic/temporal/emotional/decision/preference）
- description: 聚类描述
- memory_ids: 包含的记忆ID列表

以 JSON 格式返回：
{{
  "clusters": [
    {{
      "name": "聚类名称",
      "type": "类型",
      "description": "描述",
      "memory_ids": ["id1", "id2"]
    }}
  ]
}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": cluster_prompt}],
                system_prompt="你是一个专业的记忆管理助手。只返回 JSON 格式的结果。",
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

            # 保存聚类
            clusters = []
            for item in result.get("clusters", []):
                cluster = MemoryCluster(
                    user_id=user_id,
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    cluster_type=item.get("type", "topic"),
                    memory_ids=item.get("memory_ids", []),
                    memory_count=str(len(item.get("memory_ids", [])))
                )
                self.db.add(cluster)
                clusters.append({
                    "name": cluster.name,
                    "type": cluster.cluster_type,
                    "description": cluster.description,
                    "memory_count": len(cluster.memory_ids)
                })

            await self.db.flush()
            return clusters

        except Exception as e:
            print(f"记忆聚类失败: {str(e)}")
            return []

    # ========== 记忆网络统计 ==========

    async def get_network_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆网络统计"""
        # 记忆数量
        memory_result = await self.db.execute(
            select(func.count()).select_from(Memory).where(
                Memory.user_id == user_id,
                Memory.is_confirmed == "CONFIRMED"
            )
        )
        memory_count = memory_result.scalar() or 0

        # 关联数量
        assoc_result = await self.db.execute(
            select(func.count()).select_from(MemoryAssociation).where(
                MemoryAssociation.user_id == user_id
            )
        )
        assoc_count = assoc_result.scalar() or 0

        # 聚类数量
        cluster_result = await self.db.execute(
            select(func.count()).select_from(MemoryCluster).where(
                MemoryCluster.user_id == user_id
            )
        )
        cluster_count = cluster_result.scalar() or 0

        # 平均强度
        strength_result = await self.db.execute(
            select(func.avg(MemoryStrength.current_strength)).where(
                MemoryStrength.user_id == user_id
            )
        )
        avg_strength = strength_result.scalar() or 0.5

        return {
            "total_memories": memory_count,
            "total_associations": assoc_count,
            "total_clusters": cluster_count,
            "avg_strength": round(float(avg_strength), 2),
            "network_density": round(assoc_count / max(memory_count * (memory_count - 1) / 2, 1), 4)
        }


def get_memory_network(db: AsyncSession) -> MemoryNetwork:
    """获取记忆网络服务实例"""
    return MemoryNetwork(db)
