"""002 memory foundation - Phase 1A

Revision ID: 002_memory_foundation
Revises: 001_baseline
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa
from app.core.types import CompatibleUUID

revision = '002_memory_foundation'
down_revision = '001_baseline'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === STEP 1: Add new columns to memories ===
    op.add_column('memories', sa.Column('assertion_kind', sa.String(30), nullable=False, server_default="'LEGACY_UNKNOWN'"))
    op.add_column('memories', sa.Column('summary', sa.Text, nullable=True))

    # === STEP 2: Add UNIQUE constraint (required for composite FK) ===
    op.create_unique_constraint('uq_memory_user', 'memories', ['memory_id', 'user_id'])

    # === STEP 3: Add CHECK constraints on memories ===
    op.create_check_constraint('chk_memory_status', 'memories', "is_confirmed IN ('PENDING','CONFIRMED','REJECTED','ARCHIVED','SUPERSEDED')")
    op.create_check_constraint('chk_assertion_kind', 'memories', "assertion_kind IN ('USER_STATED','OBSERVED','INFERRED','LEGACY_UNKNOWN')")
    op.create_check_constraint('chk_memory_type', 'memories', "memory_type IN ('FACT','EXPERIENCE','OPINION','DECISION','PREFERENCE')")
    op.create_check_constraint('chk_memory_confidence', 'memories', 'confidence >= 0.0 AND confidence <= 1.0')
    op.create_check_constraint('chk_memory_importance', 'memories', 'importance >= 0.0 AND importance <= 1.0')

    # === STEP 4: Create memory_evidence table ===
    op.create_table(
        'memory_evidence',
        sa.Column('evidence_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('memory_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('memories.memory_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('source_type', sa.String(20), nullable=False),
        sa.Column('source_id', CompatibleUUID(as_uuid=True), nullable=True),
        sa.Column('source_span', sa.Text, nullable=True),
        sa.Column('evidence_kind', sa.String(20), nullable=False, server_default="'DIRECT_QUOTE'"),
        sa.Column('evidence_strength', sa.Float, nullable=False, server_default=sa.text('1.0')),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['memory_id', 'user_id'], ['memories.memory_id', 'memories.user_id'], name='fk_evidence_memory_user', ondelete='CASCADE'),
        sa.CheckConstraint("source_type IN ('CONVERSATION','DOCUMENT','DECISION','MANUAL','LEGACY_UNKNOWN')", name='chk_evidence_source_type'),
        sa.CheckConstraint("evidence_kind IN ('DIRECT_QUOTE','PARAPHRASE','OBSERVATION','USER_CORRECTION')", name='chk_evidence_kind'),
        sa.CheckConstraint('evidence_strength >= 0.0 AND evidence_strength <= 1.0', name='chk_evidence_strength'),
        # Provenance-shape constraint (errata C)
        sa.CheckConstraint(
            "(source_type IN ('DOCUMENT','CONVERSATION','DECISION') AND source_id IS NOT NULL) "
            "OR (source_type IN ('MANUAL','LEGACY_UNKNOWN') AND source_id IS NULL)",
            name='chk_evidence_provenance_shape'
        ),
    )
    op.create_index('ix_evidence_memory', 'memory_evidence', ['memory_id'])
    op.create_index('ix_evidence_user', 'memory_evidence', ['user_id'])
    op.create_index('ix_evidence_source', 'memory_evidence', ['source_type', 'source_id'])

    # === STEP 5: Add assertion_kind index on memories ===
    op.create_index('ix_memory_assertion_kind', 'memories', ['user_id', 'assertion_kind'])

    # === STEP 6: Legacy backfill ===
    # 6a: source_document_id NOT NULL -> DOCUMENT evidence
    op.execute("""
        INSERT INTO memory_evidence (evidence_id, memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength, created_at)
        SELECT gen_random_uuid(), memory_id, user_id, 'DOCUMENT', source_document_id, 'PARAPHRASE', 0.7, NOW()
        FROM memories WHERE source_document_id IS NOT NULL
    """)

    # 6b: source text with '对话提取' -> CONVERSATION evidence (source_id stays NULL since we can't resolve message_id)
    op.execute("""
        INSERT INTO memory_evidence (evidence_id, memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength, source_span, created_at)
        SELECT gen_random_uuid(), memory_id, user_id, 'CONVERSATION', NULL, 'PARAPHRASE', 0.6, source, NOW()
        FROM memories
        WHERE source IS NOT NULL AND source_document_id IS NULL
        AND source LIKE '%对话提取%'
    """)

    # 6c: Other source text -> LEGACY_UNKNOWN evidence
    op.execute("""
        INSERT INTO memory_evidence (evidence_id, memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength, source_span, created_at)
        SELECT gen_random_uuid(), memory_id, user_id, 'LEGACY_UNKNOWN', NULL, 'PARAPHRASE', 0.5, source, NOW()
        FROM memories
        WHERE source IS NOT NULL
        AND source_document_id IS NULL
        AND source NOT LIKE '%对话提取%'
    """)


def downgrade() -> None:
    # Drop evidence table (cascades from composite FK)
    op.drop_table('memory_evidence')

    # Drop new indexes
    op.drop_index('ix_memory_assertion_kind', 'memories')

    # Drop CHECK constraints
    op.drop_constraint('chk_memory_importance', 'memories', type_='check')
    op.drop_constraint('chk_memory_confidence', 'memories', type_='check')
    op.drop_constraint('chk_memory_type', 'memories', type_='check')
    op.drop_constraint('chk_assertion_kind', 'memories', type_='check')
    op.drop_constraint('chk_memory_status', 'memories', type_='check')

    # Drop UNIQUE constraint
    op.drop_constraint('uq_memory_user', 'memories', type_='unique')

    # Drop new columns
    op.drop_column('memories', 'summary')
    op.drop_column('memories', 'assertion_kind')
