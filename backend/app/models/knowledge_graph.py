"""
Personal AI OS - Knowledge Graph Model
知识图谱模型 - 实体、关系、知识推理
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index
from app.core.types import CompatibleJSON as JSONB, CompatibleUUID as UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class KnowledgeEntity(Base):
    """知识实体表 - 从文档和对话中提取的实体"""
    __tablename__ = "knowledge_entities"

    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 实体信息
    name = Column(String(255), nullable=False)          # 实体名称
    entity_type = Column(String(50), nullable=False)    # 实体类型
    description = Column(Text, nullable=True)           # 实体描述
    properties = Column(JSONB, nullable=True)           # 实体属性

    # 来源
    source_type = Column(String(50), nullable=True)     # 来源类型：document, conversation, memory
    source_id = Column(String(255), nullable=True)      # 来源ID

    # 统计
    mention_count = Column(String(20), default="1")     # 被提及次数
    importance = Column(Float, default=0.5)             # 重要性 0-1

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 索引
    __table_args__ = (
        Index("ix_entity_user_type", "user_id", "entity_type"),
        Index("ix_entity_user_name", "user_id", "name"),
    )

    def __repr__(self):
        return f"<KnowledgeEntity {self.name}: {self.entity_type}>"


class KnowledgeRelation(Base):
    """知识关系表 - 实体之间的关系"""
    __tablename__ = "knowledge_relations"

    relation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 关系信息
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entities.entity_id"), nullable=False, index=True)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entities.entity_id"), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False)   # 关系类型
    description = Column(Text, nullable=True)             # 关系描述
    weight = Column(Float, default=1.0)                  # 关系强度 0-1

    # 来源
    source_type = Column(String(50), nullable=True)      # 来源类型
    source_id = Column(String(255), nullable=True)       # 来源ID

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 关联关系
    source_entity = relationship("KnowledgeEntity", foreign_keys=[source_entity_id], backref="outgoing_relations")
    target_entity = relationship("KnowledgeEntity", foreign_keys=[target_entity_id], backref="incoming_relations")

    # 索引
    __table_args__ = (
        Index("ix_relation_user_type", "user_id", "relation_type"),
        Index("ix_relation_source", "source_entity_id"),
        Index("ix_relation_target", "target_entity_id"),
    )

    def __repr__(self):
        return f"<KnowledgeRelation {self.source_entity_id} -> {self.target_entity_id}: {self_relation_type}>"


class KnowledgeInference(Base):
    """知识推理表 - 基于图谱的推理结果"""
    __tablename__ = "knowledge_inferences"

    inference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    # 推理信息
    query = Column(Text, nullable=False)                 # 推理查询
    conclusion = Column(Text, nullable=False)            # 推理结论
    confidence = Column(Float, default=0.7)              # 置信度
    evidence = Column(JSONB, nullable=True)              # 证据链
    reasoning_path = Column(JSONB, nullable=True)        # 推理路径

    # 时间戳
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<KnowledgeInference {self.query[:50]}>"


# 实体类型定义
ENTITY_TYPES = {
    "person": "人物",
    "organization": "组织",
    "technology": "技术",
    "concept": "概念",
    "project": "项目",
    "event": "事件",
    "location": "地点",
    "product": "产品",
    "method": "方法",
    "tool": "工具",
}

# 关系类型定义
RELATION_TYPES = {
    "uses": "使用",
    "creates": "创建",
    "belongs_to": "属于",
    "depends_on": "依赖",
    "related_to": "相关",
    "part_of": "组成部分",
    "created_by": "由...创建",
    "used_in": "用于",
    "contradicts": "矛盾",
    "supports": "支持",
    "evolves_from": "演化自",
    "competes_with": "竞争",
}
