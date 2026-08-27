"""001 baseline - full legacy schema

Revision ID: 001_baseline
Revises:
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa
from app.core.types import CompatibleUUID, CompatibleJSON

revision = '001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        'users',
        sa.Column('user_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('avatar', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )

    # --- documents ---
    op.create_table(
        'documents',
        sa.Column('document_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer, server_default=sa.text('0')),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'UPLOADING'")),
        sa.Column('status_message', sa.Text, nullable=True),
        sa.Column('metadata_', CompatibleJSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # --- knowledge_chunks ---
    op.create_table(
        'knowledge_chunks',
        sa.Column('chunk_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('documents.document_id'), nullable=False, index=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', sa.Text, nullable=True),  # Placeholder for VECTOR; pgvector requires extension
        sa.Column('topic', sa.String(100), nullable=True),
        sa.Column('tags', CompatibleJSON(), nullable=True),
        sa.Column('metadata_', CompatibleJSON(), nullable=True),
        sa.Column('chunk_index', sa.Integer, server_default=sa.text('0')),
        sa.Column('start_page', sa.Integer, nullable=True),
        sa.Column('end_page', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_chunk_document_index', 'knowledge_chunks', ['document_id', 'chunk_index'])

    # --- conversations ---
    op.create_table(
        'conversations',
        sa.Column('conversation_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- conversation_messages ---
    op.create_table(
        'conversation_messages',
        sa.Column('message_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('conversations.conversation_id'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('sources', CompatibleJSON(), nullable=True),
        sa.Column('metadata_', CompatibleJSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- memories (legacy schema) ---
    op.create_table(
        'memories',
        sa.Column('memory_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('memory_type', sa.String(20), nullable=False, index=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('source_document_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('documents.document_id', ondelete='SET NULL'), nullable=True),
        sa.Column('importance', sa.Float, server_default=sa.text('0.5')),
        sa.Column('confidence', sa.Float, server_default=sa.text('0.8')),
        sa.Column('frequency', sa.Integer, server_default=sa.text('1')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_confirmed', sa.String(20), server_default=sa.text("'PENDING'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_memory_user_confirmed', 'memories', ['user_id', 'is_confirmed'])
    op.create_index('ix_memory_user_type', 'memories', ['user_id', 'memory_type'])
    op.create_index('ix_memory_user_importance', 'memories', ['user_id', 'importance'])

    # --- beliefs ---
    op.create_table(
        'beliefs',
        sa.Column('belief_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('confidence', sa.Float, server_default=sa.text('0.7')),
        sa.Column('supporting_evidence', CompatibleJSON(), nullable=True),
        sa.Column('opposing_evidence', CompatibleJSON(), nullable=True),
        sa.Column('evolution_history', CompatibleJSON(), nullable=True),
        sa.Column('status', sa.String(20), server_default=sa.text("'ACTIVE'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_belief_user_status', 'beliefs', ['user_id', 'status'])

    # --- belief_history ---
    op.create_table(
        'belief_history',
        sa.Column('history_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('belief_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('beliefs.belief_id'), nullable=False, index=True),
        sa.Column('old_content', sa.Text, nullable=False),
        sa.Column('new_content', sa.Text, nullable=False),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- decisions ---
    op.create_table(
        'decisions',
        sa.Column('decision_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('problem', sa.Text, nullable=False),
        sa.Column('background', sa.Text, nullable=True),
        sa.Column('options', CompatibleJSON(), nullable=True),
        sa.Column('choice', sa.Text, nullable=True),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('risk', sa.Text, nullable=True),
        sa.Column('expected_result', sa.Text, nullable=True),
        sa.Column('actual_result', sa.Text, nullable=True),
        sa.Column('lesson', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', CompatibleJSON(), nullable=True),
        sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- refresh_tokens ---
    op.create_table(
        'refresh_tokens',
        sa.Column('token_id', CompatibleUUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', CompatibleUUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False, index=True),
        sa.Column('jti', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('token_family', sa.String(100), nullable=False, index=True),
        sa.Column('is_used', sa.Boolean, server_default=sa.text('false')),
        sa.Column('is_revoked', sa.Boolean, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('decisions')
    op.drop_table('belief_history')
    op.drop_table('beliefs')
    op.drop_index('ix_memory_user_importance', 'memories')
    op.drop_index('ix_memory_user_type', 'memories')
    op.drop_index('ix_memory_user_confirmed', 'memories')
    op.drop_table('memories')
    op.drop_table('conversation_messages')
    op.drop_table('conversations')
    op.drop_index('ix_chunk_document_index', 'knowledge_chunks')
    op.drop_table('knowledge_chunks')
    op.drop_table('documents')
    op.drop_table('users')
