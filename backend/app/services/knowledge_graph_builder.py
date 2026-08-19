"""
Personal AI OS - Knowledge Graph Builder
知识图谱构建器 - 实体识别 + 关系推理 + 知识发现
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge_graph import (
    KnowledgeEntity, KnowledgeRelation, KnowledgeInference,
    ENTITY_TYPES, RELATION_TYPES
)
from app.models.document import Document
from app.models.knowledge import KnowledgeChunk
from app.models.memory import Memory
from app.models.belief import Belief
from app.models.decision import Decision
from app.services.ai_service import create_ai_service


@dataclass
class ExtractedEntity:
    """提取的实体"""
    name: str
    entity_type: str
    description: str
    properties: Dict[str, Any]


@dataclass
class ExtractedRelation:
    """提取的关系"""
    source_name: str
    target_name: str
    relation_type: str
    description: str
    weight: float


class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = None

    async def _get_ai_service(self):
        if self.ai_service is None:
            self.ai_service = create_ai_service()
        return self.ai_service

    async def extract_entities_from_text(
        self,
        user_id: str,
        text: str,
        source_type: str = "document",
        source_id: str = ""
    ) -> List[ExtractedEntity]:
        """
        从文本中提取实体

        Args:
            user_id: 用户 ID
            text: 文本内容
            source_type: 来源类型
            source_id: 来源ID

        Returns:
            提取的实体列表
        """
        if not text or len(text) < 10:
            return []

        # 截取前 2000 字符用于分析
        analysis_text = text[:2000]

        entity_prompt = f"""从以下文本中提取重要的实体（人物、组织、技术、概念、项目等）。

文本：
{analysis_text}

实体类型：person(人物), organization(组织), technology(技术), concept(概念), project(项目), event(事件), product(产品), method(方法), tool(工具)

请提取文本中提到的重要实体，每个实体包含：
- name: 实体名称
- type: 实体类型
- description: 实体描述（20字以内）
- properties: 属性（可选）

以 JSON 格式返回：
{{
  "entities": [
    {{
      "name": "实体名称",
      "type": "实体类型",
      "description": "描述",
      "properties": {{}}
    }}
  ]
}}

如果没有值得提取的实体，返回空列表 {{"entities": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": entity_prompt}],
                system_prompt="你是一个专业的信息提取助手。只返回 JSON 格式的结果。",
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

            entities = []
            for item in result.get("entities", []):
                entities.append(ExtractedEntity(
                    name=item.get("name", ""),
                    entity_type=item.get("type", "concept"),
                    description=item.get("description", ""),
                    properties=item.get("properties", {})
                ))

            return entities

        except Exception as e:
            print(f"实体提取失败: {str(e)}")
            return []

    async def discover_relations(
        self,
        user_id: str,
        entities: List[KnowledgeEntity]
    ) -> List[ExtractedRelation]:
        """
        发现实体之间的关系

        Args:
            user_id: 用户 ID
            entities: 实体列表

        Returns:
            发现的关系列表
        """
        if len(entities) < 2:
            return []

        entity_list = "\n".join([
            f"[{e.name}] ({e.entity_type}) - {e.description or '无描述'}"
            for e in entities[:30]
        ])

        relation_prompt = f"""分析以下实体列表，发现它们之间的关系。

实体列表：
{entity_list}

关系类型：uses(使用), creates(创建), belongs_to(属于), depends_on(依赖), related_to(相关), part_of(组成部分), used_in(用于), contradicts(矛盾), supports(支持), evolves_from(演化自)

请发现实体之间的关系，每个关系包含：
- source: 源实体名称
- target: 目标实体名称
- type: 关系类型
- description: 关系描述
- weight: 关系强度（0-1）

以 JSON 格式返回：
{{
  "relations": [
    {{
      "source": "源实体",
      "target": "目标实体",
      "type": "关系类型",
      "description": "描述",
      "weight": 0.8
    }}
  ]
}}

如果没有发现关系，返回空列表 {{"relations": []}}"""

        try:
            ai_service = await self._get_ai_service()
            response = await ai_service.chat(
                messages=[{"role": "user", "content": relation_prompt}],
                system_prompt="你是一个专业的知识图谱分析助手。只返回 JSON 格式的结果。",
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

            # 构建实体名称到ID的映射
            entity_map = {e.name: e.entity_id for e in entities}

            relations = []
            for item in result.get("relations", []):
                source_name = item.get("source", "")
                target_name = item.get("target", "")

                if source_name in entity_map and target_name in entity_map:
                    relations.append(ExtractedRelation(
                        source_name=source_name,
                        target_name=target_name,
                        relation_type=item.get("type", "related_to"),
                        description=item.get("description", ""),
                        weight=item.get("weight", 0.5)
                    ))

            return relations

        except Exception as e:
            print(f"关系发现失败: {str(e)}")
            return []

    async def build_graph_from_documents(
        self,
        user_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        从文档构建知识图谱

        Args:
            user_id: 用户 ID
            limit: 处理文档数量限制

        Returns:
            构建结果
        """
        # 获取文档
        result = await self.db.execute(
            select(Document).where(Document.user_id == user_id).limit(limit)
        )
        documents = result.scalars().all()

        all_entities = []
        all_relations = []

        for doc in documents:
            # 获取文档内容
            if doc.content:
                # 提取实体
                entities = await self.extract_entities_from_text(
                    user_id, doc.content, "document", str(doc.document_id)
                )

                # 保存实体
                for entity_data in entities:
                    # 检查是否已存在
                    existing = await self.db.execute(
                        select(KnowledgeEntity).where(
                            KnowledgeEntity.user_id == user_id,
                            KnowledgeEntity.name == entity_data.name,
                            KnowledgeEntity.entity_type == entity_data.entity_type
                        )
                    )
                    existing_entity = existing.scalar_one_or_none()

                    if existing_entity:
                        # 更新提及次数
                        count = int(existing_entity.mention_count) + 1
                        existing_entity.mention_count = str(count)
                        existing_entity.importance = min(1.0, existing_entity.importance + 0.1)
                        all_entities.append(existing_entity)
                    else:
                        # 创建新实体
                        new_entity = KnowledgeEntity(
                            user_id=user_id,
                            name=entity_data.name,
                            entity_type=entity_data.entity_type,
                            description=entity_data.description,
                            properties=entity_data.properties,
                            source_type="document",
                            source_id=str(doc.document_id)
                        )
                        self.db.add(new_entity)
                        await self.db.flush()
                        all_entities.append(new_entity)

        # 发现关系
        if len(all_entities) >= 2:
            relations = await self.discover_relations(user_id, all_entities)

            for rel_data in relations:
                # 获取源和目标实体ID
                source_result = await self.db.execute(
                    select(KnowledgeEntity).where(
                        KnowledgeEntity.user_id == user_id,
                        KnowledgeEntity.name == rel_data.source_name
                    ).limit(1)
                )
                source = source_result.scalar_one_or_none()

                target_result = await self.db.execute(
                    select(KnowledgeEntity).where(
                        KnowledgeEntity.user_id == user_id,
                        KnowledgeEntity.name == rel_data.target_name
                    ).limit(1)
                )
                target = target_result.scalar_one_or_none()

                if source and target:
                    # 检查关系是否已存在
                    existing_rel = await self.db.execute(
                        select(KnowledgeRelation).where(
                            KnowledgeRelation.user_id == user_id,
                            KnowledgeRelation.source_entity_id == source.entity_id,
                            KnowledgeRelation.target_entity_id == target.entity_id,
                            KnowledgeRelation.relation_type == rel_data.relation_type
                        )
                    )
                    if not existing_rel.scalar_one_or_none():
                        new_relation = KnowledgeRelation(
                            user_id=user_id,
                            source_entity_id=source.entity_id,
                            target_entity_id=target.entity_id,
                            relation_type=rel_data.relation_type,
                            description=rel_data.description,
                            weight=rel_data.weight,
                            source_type="document"
                        )
                        self.db.add(new_relation)
                        all_relations.append(new_relation)

        await self.db.flush()

        return {
            "entities_created": len(all_entities),
            "relations_created": len(all_relations)
        }

    async def get_graph_data(
        self,
        user_id: str,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取知识图谱数据

        Args:
            user_id: 用户 ID
            entity_type: 实体类型过滤
            limit: 返回数量限制

        Returns:
            图谱数据
        """
        # 获取实体
        query = select(KnowledgeEntity).where(KnowledgeEntity.user_id == user_id)
        if entity_type:
            query = query.where(KnowledgeEntity.entity_type == entity_type)
        query = query.order_by(KnowledgeEntity.importance.desc()).limit(limit)

        result = await self.db.execute(query)
        entities = result.scalars().all()

        # 获取关系
        entity_ids = [e.entity_id for e in entities]
        if entity_ids:
            rel_result = await self.db.execute(
                select(KnowledgeRelation).where(
                    KnowledgeRelation.user_id == user_id,
                    KnowledgeRelation.source_entity_id.in_(entity_ids)
                )
            )
            relations = rel_result.scalars().all()
        else:
            relations = []

        return {
            "nodes": [
                {
                    "id": str(e.entity_id),
                    "label": e.name,
                    "type": e.entity_type,
                    "description": e.description,
                    "importance": e.importance,
                    "mention_count": int(e.mention_count)
                }
                for e in entities
            ],
            "edges": [
                {
                    "source": str(r.source_entity_id),
                    "target": str(r.target_entity_id),
                    "label": RELATION_TYPES.get(r.relation_type, r.relation_type),
                    "weight": r.weight,
                    "description": r.description
                }
                for r in relations
            ],
            "stats": {
                "total_entities": len(entities),
                "total_relations": len(relations),
                "entity_types": {t: len([e for e in entities if e.entity_type == t]) for t in ENTITY_TYPES}
            }
        }

    async def find_entity_connections(
        self,
        user_id: str,
        entity_name: str
    ) -> Dict[str, Any]:
        """
        查找实体的所有连接

        Args:
            user_id: 用户 ID
            entity_name: 实体名称

        Returns:
            连接信息
        """
        # 查找实体
        result = await self.db.execute(
            select(KnowledgeEntity).where(
                KnowledgeEntity.user_id == user_id,
                KnowledgeEntity.name == entity_name
            ).limit(1)
        )
        entity = result.scalar_one_or_none()

        if not entity:
            return {"error": "实体不存在"}

        # 查找相关关系
        outgoing = await self.db.execute(
            select(KnowledgeRelation).where(
                KnowledgeRelation.source_entity_id == entity.entity_id
            )
        )
        incoming = await self.db.execute(
            select(KnowledgeRelation).where(
                KnowledgeRelation.target_entity_id == entity.entity_id
            )
        )

        outgoing_relations = outgoing.scalars().all()
        incoming_relations = incoming.scalars().all()

        # 获取相关实体
        connected_entity_ids = set()
        for r in outgoing_relations:
            connected_entity_ids.add(r.target_entity_id)
        for r in incoming_relations:
            connected_entity_ids.add(r.source_entity_id)

        if connected_entity_ids:
            entities_result = await self.db.execute(
                select(KnowledgeEntity).where(
                    KnowledgeEntity.entity_id.in_(connected_entity_ids)
                )
            )
            connected_entities = {str(e.entity_id): e.name for e in entities_result.scalars().all()}
        else:
            connected_entities = {}

        return {
            "entity": {
                "name": entity.name,
                "type": entity.entity_type,
                "description": entity.description,
                "importance": entity.importance
            },
            "outgoing": [
                {
                    "target": connected_entities.get(str(r.target_entity_id), "未知"),
                    "relation": RELATION_TYPES.get(r.relation_type, r.relation_type),
                    "weight": r.weight
                }
                for r in outgoing_relations
            ],
            "incoming": [
                {
                    "source": connected_entities.get(str(r.source_entity_id), "未知"),
                    "relation": RELATION_TYPES.get(r.relation_type, r.relation_type),
                    "weight": r.weight
                }
                for r in incoming_relations
            ],
            "connection_count": len(outgoing_relations) + len(incoming_relations)
        }


def get_knowledge_graph_builder(db: AsyncSession) -> KnowledgeGraphBuilder:
    """获取知识图谱构建器实例"""
    return KnowledgeGraphBuilder(db)
