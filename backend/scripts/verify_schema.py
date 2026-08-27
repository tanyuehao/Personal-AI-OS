"""
Personal AI OS - Schema Verification Script
Verifies legacy database schema and data before Alembic stamp.

Usage:
    python -m scripts.verify_schema
    python -m scripts.verify_schema --database-url postgresql+asyncpg://...
"""
import asyncio
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


# Expected legacy schema (001_baseline)
EXPECTED_TABLES = {
    'users', 'documents', 'knowledge_chunks', 'conversations',
    'conversation_messages', 'memories', 'beliefs', 'belief_history',
    'decisions', 'refresh_tokens'
}

MEMORIES_COLUMNS = {
    'memory_id', 'user_id', 'memory_type', 'content', 'source',
    'source_document_id', 'importance', 'confidence', 'frequency',
    'last_used_at', 'expires_at', 'is_confirmed', 'created_at', 'updated_at'
}

USERS_COLUMNS = {'user_id', 'username', 'email', 'password_hash'}

VALID_STATUSES = {'PENDING', 'CONFIRMED', 'REJECTED'}


async def verify_schema(database_url: str) -> dict:
    """Run all verification checks. Returns structured result."""
    result = {
        'schema_ok': True,
        'data_ok': True,
        'errors': [],
        'warnings': [],
        'tables_found': [],
        'missing_tables': [],
    }

    engine = create_async_engine(database_url)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            # === SCHEMA VERIFICATION ===

            # 1. Check required tables
            r = await db.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables_found = {row[0] for row in r.fetchall()}
            result['tables_found'] = sorted(tables_found)
            result['missing_tables'] = sorted(EXPECTED_TABLES - tables_found)

            if result['missing_tables']:
                result['schema_ok'] = False
                result['errors'].append(f"Missing tables: {result['missing_tables']}")

            # 2. Check memories columns
            if 'memories' in tables_found:
                r = await db.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'memories' AND table_schema = 'public'"
                ))
                mem_cols = {row[0] for row in r.fetchall()}
                missing_mem_cols = MEMORIES_COLUMNS - mem_cols
                if missing_mem_cols:
                    result['schema_ok'] = False
                    result['errors'].append(f"Missing memories columns: {missing_mem_cols}")

            # 3. Check users columns
            if 'users' in tables_found:
                r = await db.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'users' AND table_schema = 'public'"
                ))
                user_cols = {row[0] for row in r.fetchall()}
                missing_user_cols = USERS_COLUMNS - user_cols
                if missing_user_cols:
                    result['schema_ok'] = False
                    result['errors'].append(f"Missing users columns: {missing_user_cols}")

            # === DATA VERIFICATION ===

            # 4. Invalid memory statuses
            if 'memories' in tables_found:
                r = await db.execute(text(
                    "SELECT DISTINCT is_confirmed FROM memories "
                    "WHERE is_confirmed IS NOT NULL"
                ))
                statuses = {row[0] for row in r.fetchall()}
                invalid_statuses = statuses - VALID_STATUSES
                if invalid_statuses:
                    result['data_ok'] = False
                    result['errors'].append(f"Invalid memory statuses found: {invalid_statuses}")

                # 5. Confidence out of range
                r = await db.execute(text(
                    "SELECT COUNT(*) FROM memories "
                    "WHERE confidence < 0.0 OR confidence > 1.0"
                ))
                bad_confidence = r.scalar()
                if bad_confidence and bad_confidence > 0:
                    result['data_ok'] = False
                    result['errors'].append(f"Confidence out of range: {bad_confidence} rows")

                # 6. Importance out of range
                r = await db.execute(text(
                    "SELECT COUNT(*) FROM memories "
                    "WHERE importance < 0.0 OR importance > 1.0"
                ))
                bad_importance = r.scalar()
                if bad_importance and bad_importance > 0:
                    result['data_ok'] = False
                    result['errors'].append(f"Importance out of range: {bad_importance} rows")

                # 7. Dangling source_document_id
                if 'documents' in tables_found:
                    r = await db.execute(text(
                        "SELECT COUNT(*) FROM memories m "
                        "LEFT JOIN documents d ON m.source_document_id = d.document_id "
                        "WHERE m.source_document_id IS NOT NULL AND d.document_id IS NULL"
                    ))
                    dangling = r.scalar()
                    if dangling and dangling > 0:
                        result['data_ok'] = False
                        result['errors'].append(f"Dangling source_document_id: {dangling} rows")

                    # 8. Cross-user source ownership
                    r = await db.execute(text(
                        "SELECT COUNT(*) FROM memories m "
                        "JOIN documents d ON m.source_document_id = d.document_id "
                        "WHERE m.user_id != d.user_id"
                    ))
                    cross_user = r.scalar()
                    if cross_user and cross_user > 0:
                        result['data_ok'] = False
                        result['errors'].append(f"Cross-user source ownership: {cross_user} rows")

    finally:
        await engine.dispose()

    return result


def main():
    parser = argparse.ArgumentParser(description='Verify legacy database schema')
    parser.add_argument('--database-url', help='PostgreSQL async URL')
    args = parser.parse_args()

    db_url = args.database_url or os.getenv('DATABASE_URL')
    if not db_url:
        print(json.dumps({'error': 'No DATABASE_URL provided'}))
        sys.exit(1)

    result = asyncio.run(verify_schema(db_url))
    print(json.dumps(result, indent=2))

    if not result['schema_ok'] or not result['data_ok']:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
