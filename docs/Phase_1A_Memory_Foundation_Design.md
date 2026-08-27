# Phase 1A — Memory Foundation Design

> **Status**: Design Revision v2.1 — Awaiting External Review  
> **Scope**: v0.2 Reliable Memory — Foundation Layer  
> **Constraint**: No code changes. Design only.

---

## 0. Design Methodology

This document is based on two parallel analyses:

1. **25 design documents** in `docs/` — what the product vision requires
2. **Current implementation** in `backend/app/` — what actually exists today (verified against source code, not assumptions)

Every design decision below is grounded in the gap between these two.

---

## 一、Gap Analysis

### 1.1 Current Memory Schema (逐字段核对自 `app/models/memory.py`)

```
Table: memories
──────────────────────────────────────────────────
memory_id          UUID PK                             (line 29)
user_id            UUID FK → users NOT NULL, indexed   (line 32)
memory_type        String(20) NOT NULL, indexed        (line 35)  -- FACT/EXPERIENCE/OPINION/DECISION/PREFERENCE
content            Text NOT NULL                       (line 36)
source             String(255) nullable                (line 39)  -- free-text
source_document_id UUID FK → documents nullable        (line 40)
importance         Float default 0.5                   (line 43)  -- range 0-1
confidence         Float default 0.8                   (line 44)  -- range 0-1
frequency          Integer default 1                   (line 45)
last_used_at       DateTime(tz) nullable               (line 48)
expires_at         DateTime(tz) nullable               (line 49)
is_confirmed       String(20) default "PENDING"        (line 52)  -- PENDING/CONFIRMED/REJECTED
created_at         DateTime(tz) NOT NULL               (line 55)
updated_at         DateTime(tz) NOT NULL               (line 56)

Indexes (line 62-66):
  ix_memory_user_confirmed  (user_id, is_confirmed)
  ix_memory_user_type       (user_id, memory_type)
  ix_memory_user_importance (user_id, importance)

No composite UNIQUE(memory_id, user_id) exists.
```

**What does NOT exist in the DB:**

| Missing | Status |
|---|---|
| `summary` (Text) | Not present |
| `embedding` (Vector) | Not present — Memory has NO vector search |
| `assertion_kind` (String) | Not present |
| `UNIQUE(memory_id, user_id)` | Not present — PK is memory_id alone |

**What does NOT exist as a table:**

| Missing Table | Purpose |
|---|---|
| `memory_evidence` | One Memory → Many Evidence records. First-class provenance. |

### 1.2 Current Memory Lifecycle

```
Create memory → is_confirmed = "PENDING"
POST /{id}/confirm → is_confirmed = "CONFIRMED"
POST /{id}/reject  → is_confirmed = "REJECTED"
PUT /{id}          → is_confirmed can be set to ANY value (no validation)
DELETE /{id}       → hard delete from DB
```

### 1.3 Current Memory Search

```
Search: ILIKE keyword match × 0.7 + importance × 0.3
No vector/semantic search on memories
```

### 1.4 Current Memory Evidence / Provenance

```
source: String(255) — free-text, e.g. "对话提取 (conversation_id: abc)"
source_document_id: UUID FK → documents — only links to Documents
```

| Design Requirement | Current Status |
|---|---|
| One Memory → Many Evidence | Not implemented |
| Evidence tracks source_type + source_id | Only `source_document_id` FK |
| Source deletion → evidence cascade → archive | Not implemented |
| Cross-user evidence isolation | Not enforced at DB level |

### 1.5 Summary of Gaps

| Gap | Severity | Phase 1A? |
|---|---|---|
| No MemoryEvidence table | Critical | Yes |
| No assertion_kind | Critical | Yes |
| No Alembic migrations | High | Yes |
| Lifecycle missing ARCHIVED | High | Yes |
| PUT allows arbitrary status transitions | High | Yes |
| No DB-level evidence user isolation | High | Yes |
| No UNIQUE(memory_id, user_id) on memories | High | Yes (required for composite FK) |
| Document/message/decision delete → evidence cascade | High | Yes |
| `summary` field missing | Low | Yes |
| `last_used_at` never written by recall | Low | Yes |

---

## 二、Schema Authority — Policy

**Production runtime MUST NOT use `create_all()` / `table.create()` to modify business schema.**

### 2.1 Rules

1. **Alembic is the sole authority** for production PostgreSQL schema.
2. **`init_db()` / `create_all()` is FORBIDDEN in production.** Application startup must not auto-create, auto-stamp, or auto-run migrations.
3. **Schema upgrades** are explicit: `alembic upgrade head` by operator before deploy.
4. **SQLite** retained only as a development convenience. CI runs PostgreSQL + pgvector.
5. **`alembic stamp <revision>`** is a one-time operation on existing legacy databases, only after schema verification. Never `stamp head` when 002 is already head — stamp the specific baseline revision.

### 2.2 Alembic Bootstrap / Adoption Strategy

**Path A — Fresh Database:**
```
createdb personal_ai_os
alembic upgrade head    # Creates all tables from scratch
```

**Path B — Existing Legacy Database:**
```
# Step 1: Verify current schema matches expected baseline
python -m scripts.verify_schema --database-url=postgresql+asyncpg://...

# Step 2: Only after verification passes
alembic stamp 001_baseline    # NOT stamp head — stamp the specific baseline revision

# Step 3: Apply Phase 1A migration
alembic upgrade head          # Runs 002_memory_foundation
```

**Forbidden:** `alembic stamp head` when 002_memory_foundation is already applied. Must always stamp the specific revision ID.

### 2.3 verify_schema Preflight Checks

The verification script detects before stamping:

1. **Invalid legacy statuses** — any `is_confirmed` value outside `PENDING/CONFIRMED/REJECTED`
2. **Confidence/importance out of range** — any value `< 0.0` or `> 1.0`
3. **Dangling source_document_id** — FK pointing to a non-existent document
4. **Cross-user source ownership mismatches** — `source_document_id` references a document belonging to a different user

### 2.4 Migration Tests

```python
async def test_fresh_database_migration():
    """Fresh DB → alembic upgrade head → all tables + constraints exist."""
    # Verify: users, documents, knowledge_chunks, conversations, conversation_messages,
    #         memories, beliefs, belief_history, decisions, memory_evidence tables
    # Verify: CHECK constraints active
    # Verify: composite FK on memory_evidence(memory_id, user_id) exists
    # Verify: UNIQUE(memory_id, user_id) on memories exists

async def test_legacy_database_upgrade():
    """Legacy DB → verify → stamp 001 → upgrade 002 → data preserved."""
    # 1. Create legacy DB with init_db()
    # 2. Insert test memories with various is_confirmed values
    # 3. Run schema verification script
    # 4. alembic stamp 001_baseline
    # 5. alembic upgrade head (runs 002)
    # 6. All legacy memories still exist
    # 7. assertion_kind = LEGACY_UNKNOWN for all legacy rows
    # 8. Evidence records created from source data

async def test_migration_preserves_all_memory_rows():
    """Every memory row survives migration without data loss."""
    # Pre-migration: insert 100 diverse memories
    # Post-migration: count == 100, all fields preserved

async def test_migration_idempotency():
    """Running upgrade head twice does not duplicate data or fail."""
```

### 2.5 Downgrade / Rollback

```sql
-- Downgrade: remove Phase 1A additions, keep legacy data
-- Must be symmetric with upgrade (Item 4)
DROP TABLE IF EXISTS memory_evidence;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS uq_memory_user;
ALTER TABLE memories DROP COLUMN IF EXISTS assertion_kind;
ALTER TABLE memories DROP COLUMN IF EXISTS summary;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_status;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_assertion_kind;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_confidence;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_importance;
```

---

## 三、Memory Schema v2 — Design

### 3.1 Existing Fields (保留)

All existing fields preserved. No field removed.

### 3.2 New Fields

| Field | Type | Nullable | Default | Writer | Index |
|---|---|---|---|---|---|
| `assertion_kind` | String(30) NOT NULL | NO | `LEGACY_UNKNOWN` | Manual → USER_STATED. Extraction → based on source. Legacy → LEGACY_UNKNOWN. | `(user_id, assertion_kind)` |
| `summary` | Text | YES | NULL | AI extraction pipeline or user | — |

### 3.3 New Constraints

| Constraint | Definition |
|---|---|
| `UNIQUE(memory_id, user_id)` | Required before composite FK on memory_evidence can reference it |
| `chk_memory_status` | `is_confirmed IN ('PENDING','CONFIRMED','REJECTED','ARCHIVED','SUPERSEDED')` |
| `chk_assertion_kind` | `assertion_kind IN ('USER_STATED','OBSERVED','INFERRED','LEGACY_UNKNOWN')` |
| `chk_memory_confidence` | `confidence >= 0.0 AND confidence <= 1.0` |
| `chk_memory_importance` | `importance >= 0.0 AND importance <= 1.0` |

### 3.4 assertion_kind vs confirmation — Fully Separated

These are orthogonal axes:

| Axis | Values | Meaning |
|---|---|---|
| `assertion_kind` | USER_STATED, OBSERVED, INFERRED, LEGACY_UNKNOWN | **How** the system knows this |
| `is_confirmed` | PENDING, CONFIRMED, REJECTED, ARCHIVED, SUPERSEDED | **Whether** the user has approved |

**Creation path → default assertion_kind + is_confirmed:**

| Creation Path | assertion_kind | is_confirmed | Evidence |
|---|---|---|---|
| Manual `POST /memory` | USER_STATED | CONFIRMED | MANUAL evidence atomically created |
| AI extraction from user conversation message | USER_STATED | PENDING | CONVERSATION evidence created |
| AI pattern detection from user data | OBSERVED | PENDING | CONVERSATION/DOCUMENT evidence |
| AI inference | INFERRED | PENDING | Created by inference engine (1C) |
| Legacy migration | LEGACY_UNKNOWN | Preserved | Migrated from `source` / `source_document_id` |

### 3.5 Fields NOT Added

| Rejected | Why |
|---|---|
| `embedding` | Deferred to 1B |
| `semantic_score` | Computed at query time |
| `recurrence_count` | Same as `frequency` |
| `decay_rate` | In `memory_strengths` table |

### 3.6 Three Scores — Explicit Separation

| Score | Definition | Stored? |
|---|---|---|
| **importance** | How important to user's life/work | Yes |
| **confidence** | System confidence in accuracy (based on evidence) — **calibration deferred to 1B** | Yes (raw value, no formula in 1A) |
| **relevance** | How relevant to current query | No — ephemeral |

---

## 四、MemoryEvidence — Design

### 4.1 Rationale

> "Memory 不能只知道'是什么'，还必须知道'为什么系统认为它是真的'。"

### 4.2 Schema

```
Table: memory_evidence
──────────────────────────────────────────────────
evidence_id       UUID PK
memory_id         UUID NOT NULL
user_id           UUID NOT NULL
source_type       VARCHAR(20) NOT NULL
source_id         UUID NULL
source_span       Text NULL
evidence_kind     VARCHAR(20) NOT NULL DEFAULT 'DIRECT_QUOTE'
evidence_strength FLOAT NOT NULL DEFAULT 1.0  -- range 0-1
observed_at       DateTime(tz) NULL
created_at        DateTime(tz) NOT NULL
```

### 4.3 Source Types

| source_type | source_id points to | Example |
|---|---|---|
| `CONVERSATION` | `conversation_messages.message_id` | "In message X, user said 'I prefer Python'" |
| `DOCUMENT` | `documents.document_id` | "In doc Y, section Z says '2031-09-17'" |
| `DECISION` | `decisions.decision_id` | "User chose Python in decision about tech stack" |
| `MANUAL` | NULL | User typed "I prefer Python" directly |
| `LEGACY_UNKNOWN` | NULL | Migrated from pre-1A `source` text where origin can't be determined |

**Removed:** `CORRECTION` from source_type. User corrections use `source_type=CONVERSATION` with `evidence_kind=USER_CORRECTION`.

### 4.4 Evidence Kinds

| evidence_kind | Meaning | Default strength |
|---|---|---|
| `DIRECT_QUOTE` | Exact quote from source | 1.0 |
| `PARAPHRASE` | Summarized from source | 0.7 |
| `OBSERVATION` | Pattern observed across data | 0.6 |
| `USER_CORRECTION` | User corrected AI output | 0.9 |

### 4.5 Polymorphic Source — Domain Operations

Source deletion is an application-level domain operation executed within the caller's AsyncSession transaction. It does NOT commit internally.

```python
async def on_source_deleted(
    source_type: str, source_id: UUID, db: AsyncSession
):
    """
    Domain operation: called within an existing transaction when a source
    entity is deleted. Caller controls commit/rollback.
    """
    # 1. Find all evidence from this source
    result = await db.execute(
        select(MemoryEvidence).where(
            MemoryEvidence.source_type == source_type,
            MemoryEvidence.source_id == source_id
        )
    )
    evidence_records = result.scalars().all()

    # 2. Delete evidence records
    for ev in evidence_records:
        await db.delete(ev)

    # 3. For each affected memory, re-evaluate status
    affected_memory_ids = {ev.memory_id for ev in evidence_records}
    for mid in affected_memory_ids:
        remaining = await db.execute(
            select(func.count()).select_from(MemoryEvidence)
            .where(MemoryEvidence.memory_id == mid)
        )
        if remaining.scalar() == 0:
            mem_result = await db.execute(
                select(Memory).where(Memory.memory_id == mid)
            )
            memory = mem_result.scalar_one_or_none()
            if memory and memory.is_confirmed == "CONFIRMED":
                memory.is_confirmed = "ARCHIVED"
            elif memory and memory.is_confirmed == "PENDING":
                memory.is_confirmed = "ARCHIVED"

    # No commit — caller's transaction handles commit/rollback
```

### 4.6 Deletion Paths

| Deleted Entity | Service Method | Domain Operation |
|---|---|---|
| **Document** | `document_service.delete_document()` | `on_source_deleted("DOCUMENT", doc_id, db)` |
| **ConversationMessage** | `chat_service.delete_message()` | `on_source_deleted("CONVERSATION", msg_id, db)` |
| **Decision** | `decision_service.delete_decision()` | `on_source_deleted("DECISION", dec_id, db)` |

All three deletion paths call the same domain operation within their transaction.

### 4.7 Cross-User Isolation — Two Layers (Item 8)

**DB invariant (composite FK):**
```sql
CONSTRAINT fk_evidence_memory
    FOREIGN KEY (memory_id, user_id)
    REFERENCES memories(memory_id, user_id)
    ON DELETE CASCADE
```
This prevents inserting evidence with a `user_id` that doesn't match the memory's owner. If `memory.user_id = A` and `evidence.user_id = B`, PostgreSQL rejects the INSERT at the DB level.

**Service invariant (source entity ownership):**
When adding evidence, the service must verify that the source entity (document, message, decision) also belongs to the same user. This is NOT enforced by DB constraints (polymorphic FK), only by service logic.

```python
# Service check: source entity ownership
if source_type == "DOCUMENT":
    doc = await db.get(Document, source_id)
    if doc.user_id != memory.user_id:
        raise HTTPException(403, "Source document belongs to another user")
```

### 4.8 Cross-User Source Tests (Item 8)

```python
async def test_evidence_rejects_cross_user_memory():
    """DB-level: evidence with wrong user_id rejected by composite FK."""
    # memory.user_id = A
    # INSERT evidence(user_id=B, memory_id=memory.id) → IntegrityError

async def test_evidence_rejects_cross_user_document():
    """Service-level: cannot add evidence from another user's document."""
    # memory belongs to user A
    # document belongs to user B
    # POST /memory/{id}/evidence with doc from user B → 403

async def test_evidence_rejects_cross_user_conversation():
    """Service-level: cannot add evidence from another user's message."""
    # memory belongs to user A
    # message belongs to user B
    # → 403

async def test_evidence_rejects_cross_user_decision():
    """Service-level: cannot add evidence from another user's decision."""
    # memory belongs to user A
    # decision belongs to user B
    # → 403
```

---

## 五、Epistemic / Assertion Kind — Design

### 5.1 Four Values

| Kind | Definition | Source |
|---|---|---|
| `USER_STATED` | User explicitly said or wrote this | User message in conversation, or manual creation |
| `OBSERVED` | System observed a pattern from user-owned data | Documents, conversation history (user side only) |
| `INFERRED` | AI concluded this from combining evidence | Deferred to 1C — inference engine |
| `LEGACY_UNKNOWN` | Pre-1A memory, epistemic origin undetermined | Migration default |

### 5.2 OBSERVED Derivation Rule (Item 9)

OBSERVED evidence MUST derive from **user-owned source data** — user's documents, user's conversation messages (user side), user's decisions.

**Assistant messages are NOT a valid source for OBSERVED.** The assistant's output is AI-generated, not user data. Extracting memory from assistant messages would conflate AI output with user evidence.

| Extraction from | Valid assertion_kind |
|---|---|
| User's message in conversation | USER_STATED |
| User's document | OBSERVED (if pattern detected) |
| User's message in document | OBSERVED (if pattern detected) |
| User's decision record | OBSERVED |
| AI assistant's response | **No memory extraction** (in 1A) |

### 5.3 Policy Matrix

| Policy | USER_STATED | OBSERVED | INFERRED | LEGACY_UNKNOWN |
|---|---|---|---|---|
| Initial status | See §3.3 | PENDING | PENDING | Preserved |
| Retrieval priority | Highest | Medium | Lowest | Lowest |
| UI badge | "User stated" | "Observed" | "AI inference" | No badge |

---

## 六、Memory Lifecycle State Machine

### 6.1 States

| State | Meaning |
|---|---|
| `PENDING` | Candidate awaiting user decision. Not used in recall. |
| `CONFIRMED` | User approved. Used in recall. |
| `REJECTED` | User explicitly rejected. Not used in recall. |
| `ARCHIVED` | Source evidence removed. Not used in recall. Preserved for audit. |
| `SUPERSEDED` | Reserved for 1C. Enum value only, no transitions in 1A. |

### 6.2 State Machine

```
                    ┌───────────────────────────────────────────────┐
                    │                                               │
                    ▼                                               │
              ┌──────────┐                                         │
    create →  │ PENDING  │ ──── confirm ──────→ ┌────────────┐     │
              └──────────┘                      │ CONFIRMED  │     │
                    │                           └────────────┘     │
                    │ reject          │ archive                    │
                    ▼                 ▼                            │
              ┌──────────┐    ┌──────────┐                        │
              │ REJECTED │    │ ARCHIVED │ ── add evidence → ─────┘
              └──────────┘    └──────────┘     (becomes PENDING)
```

### 6.3 Legal Transitions

| From | To | Trigger | Who |
|---|---|---|---|
| (new) | PENDING | AI extraction, legacy migration | System |
| (new, manual) | CONFIRMED | `POST /memory` | User |
| PENDING | CONFIRMED | `POST /{id}/confirm` | User |
| PENDING | REJECTED | `POST /{id}/reject` | User |
| CONFIRMED | ARCHIVED | Evidence cascade (0 evidence remains) | System |
| PENDING | ARCHIVED | Evidence cascade (0 evidence remains) | System |
| ARCHIVED | PENDING | New evidence added | System / User |

### 6.4 Illegal Transitions

| From | To | Why |
|---|---|---|
| REJECTED | CONFIRMED | Must re-evaluate (go through PENDING) |
| ARCHIVED | CONFIRMED | New evidence → PENDING, user must re-evaluate |
| CONFIRMED | PENDING | Cannot un-confirm |
| (any) | SUPERSEDED | Reserved for 1C |

### 6.5 PENDING Loses Last Evidence (Item 14)

When a PENDING memory loses its last evidence (source deleted), it transitions to ARCHIVED — same as CONFIRMED. Rationale: PENDING memories with no evidence are neither confirmed nor rejected; archiving them preserves them for audit without polluting the candidate queue.

### 6.6 Confirm Idempotency / Regression (Item 15)

- **Confirming an already-CONFIRMED memory:** Returns the memory unchanged (idempotent, 200 OK). Not an error.
- **Confirming a manually created memory (already CONFIRMED):** Same — idempotent.
- **Regression:** The existing `test_e2e_memory_candidate_flow` creates a PENDING memory, confirms it, and verifies recall. This test MUST continue to pass unchanged. The confirm endpoint must accept PENDING → CONFIRMED transition and return 200.

### 6.7 Manual Creation Creates Evidence Atomically (Item 12)

`POST /memory` by user MUST atomically:
1. Create the memory record with `assertion_kind=USER_STATED`, `is_confirmed=CONFIRMED`
2. Create a `MANUAL` evidence record with `evidence_kind=DIRECT_QUOTE`
3. Both happen in one transaction — no partial state

### 6.8 Delete vs Archive

| Action | Delete | Archive |
|---|---|---|
| DB record | Removed | Stays with `is_confirmed = ARCHIVED` |
| Evidence | Hard deleted | Evidence removed, memory preserved |
| Audit | Lost | Preserved |
| Restore | Impossible | Via evidence + PENDING → user confirm |

---

## 七、Database Invariants

### 7.1 Constraints

```sql
-- 1. UNIQUE(memory_id, user_id) on memories — required for composite FK
ALTER TABLE memories ADD CONSTRAINT uq_memory_user
    UNIQUE (memory_id, user_id);

-- 2. Evidence composite FK — enforces user ownership at DB level
-- (see §4.9 below for full CREATE TABLE)

-- 3. Status
ALTER TABLE memories ADD CONSTRAINT chk_memory_status
    CHECK (is_confirmed IN ('PENDING','CONFIRMED','REJECTED','ARCHIVED','SUPERSEDED'));

-- 4. assertion_kind
ALTER TABLE memories ADD CONSTRAINT chk_assertion_kind
    CHECK (assertion_kind IN ('USER_STATED','OBSERVED','INFERRED','LEGACY_UNKNOWN'));

-- 5. Confidence range
ALTER TABLE memories ADD CONSTRAINT chk_memory_confidence
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- 6. Importance range
ALTER TABLE memories ADD CONSTRAINT chk_memory_importance
    CHECK (importance >= 0.0 AND importance <= 1.0);
```

### 7.2 Evidence Table DDL

```sql
CREATE TABLE memory_evidence (
    evidence_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id         UUID NOT NULL,
    user_id           UUID NOT NULL,
    source_type       VARCHAR(20) NOT NULL,
    source_id         UUID,
    source_span       TEXT,
    evidence_kind     VARCHAR(20) NOT NULL DEFAULT 'DIRECT_QUOTE',
    evidence_strength FLOAT NOT NULL DEFAULT 1.0,
    observed_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_evidence_memory
        FOREIGN KEY (memory_id, user_id)
        REFERENCES memories(memory_id, user_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_evidence_source_type
        CHECK (source_type IN ('CONVERSATION','DOCUMENT','DECISION','MANUAL','LEGACY_UNKNOWN')),
    CONSTRAINT chk_evidence_kind
        CHECK (evidence_kind IN ('DIRECT_QUOTE','PARAPHRASE','OBSERVATION','USER_CORRECTION')),
    CONSTRAINT chk_evidence_strength
        CHECK (evidence_strength >= 0.0 AND evidence_strength <= 1.0)
);
```

### 7.3 Indexes

```sql
-- Existing (keep)
-- ix_memory_user_confirmed  (user_id, is_confirmed)
-- ix_memory_user_type       (user_id, memory_type)
-- ix_memory_user_importance (user_id, importance)

-- New
CREATE INDEX ix_memory_assertion_kind ON memories (user_id, assertion_kind);
CREATE INDEX ix_evidence_memory ON memory_evidence (memory_id);
CREATE INDEX ix_evidence_user ON memory_evidence (user_id);
CREATE INDEX ix_evidence_source ON memory_evidence (source_type, source_id);
```

---

## 八、Migration Strategy

### 8.1 Phase 1A Migration (`002_memory_foundation.py`)

```sql
-- === STEP 1: Add new columns ===
ALTER TABLE memories ADD COLUMN assertion_kind VARCHAR(30) NOT NULL DEFAULT 'LEGACY_UNKNOWN';
ALTER TABLE memories ADD COLUMN summary TEXT;

-- === STEP 2: Add UNIQUE constraint (required for composite FK) ===
ALTER TABLE memories ADD CONSTRAINT uq_memory_user UNIQUE (memory_id, user_id);

-- === STEP 3: Add CHECK constraints on memories ===
ALTER TABLE memories ADD CONSTRAINT chk_memory_status
    CHECK (is_confirmed IN ('PENDING','CONFIRMED','REJECTED','ARCHIVED','SUPERSEDED'));
ALTER TABLE memories ADD CONSTRAINT chk_assertion_kind
    CHECK (assertion_kind IN ('USER_STATED','OBSERVED','INFERRED','LEGACY_UNKNOWN'));
ALTER TABLE memories ADD CONSTRAINT chk_memory_confidence
    CHECK (confidence >= 0.0 AND confidence <= 1.0);
ALTER TABLE memories ADD CONSTRAINT chk_memory_importance
    CHECK (importance >= 0.0 AND importance <= 1.0);

-- === STEP 4: Create memory_evidence table ===
CREATE TABLE memory_evidence (
    evidence_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id         UUID NOT NULL,
    user_id           UUID NOT NULL,
    source_type       VARCHAR(20) NOT NULL,
    source_id         UUID,
    source_span       TEXT,
    evidence_kind     VARCHAR(20) NOT NULL DEFAULT 'DIRECT_QUOTE',
    evidence_strength FLOAT NOT NULL DEFAULT 1.0,
    observed_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_evidence_memory
        FOREIGN KEY (memory_id, user_id)
        REFERENCES memories(memory_id, user_id) ON DELETE CASCADE,
    CONSTRAINT chk_evidence_source_type
        CHECK (source_type IN ('CONVERSATION','DOCUMENT','DECISION','MANUAL','LEGACY_UNKNOWN')),
    CONSTRAINT chk_evidence_kind
        CHECK (evidence_kind IN ('DIRECT_QUOTE','PARAPHRASE','OBSERVATION','USER_CORRECTION')),
    CONSTRAINT chk_evidence_strength
        CHECK (evidence_strength >= 0.0 AND evidence_strength <= 1.0)
);
CREATE INDEX ix_evidence_memory ON memory_evidence (memory_id);
CREATE INDEX ix_evidence_user ON memory_evidence (user_id);
CREATE INDEX ix_evidence_source ON memory_evidence (source_type, source_id);

-- === STEP 5: Legacy backfill ===
-- 5a. source_document_id NOT NULL → DOCUMENT evidence
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength)
SELECT memory_id, user_id, 'DOCUMENT', source_document_id, 'PARAPHRASE', 0.7
FROM memories WHERE source_document_id IS NOT NULL;

-- 5b. source text matches "对话提取" pattern → CONVERSATION evidence (only if conversation_id extractable)
-- Note: source_span preserved for audit, source_id set only if conversation_id parseable
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength, source_span)
SELECT memory_id, user_id, 'CONVERSATION', NULL, 'PARAPHRASE', 0.6, source
FROM memories
WHERE source IS NOT NULL AND source_document_id IS NULL
AND source LIKE '%对话提取%';

-- 5c. Other source text → LEGACY_UNKNOWN evidence (preserves original text)
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength, source_span)
SELECT memory_id, user_id, 'LEGACY_UNKNOWN', NULL, 'PARAPHRASE', 0.5, source
FROM memories
WHERE source IS NOT NULL
AND source_document_id IS NULL
AND source NOT LIKE '%对话提取%';
```

### 8.2 Downgrade (Symmetric)

```sql
DROP TABLE IF EXISTS memory_evidence;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS uq_memory_user;
ALTER TABLE memories DROP COLUMN IF EXISTS assertion_kind;
ALTER TABLE memories DROP COLUMN IF EXISTS summary;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_status;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_assertion_kind;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_confidence;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_importance;
```

### 8.3 Data Preservation

| Existing Data | Migration | After |
|---|---|---|
| `source_document_id` set | → DOCUMENT evidence | Column kept (deprecated) |
| `source` with "对话提取" | → CONVERSATION evidence | Column kept |
| `source` with other text | → LEGACY_UNKNOWN evidence | Column kept |
| `source = NULL, source_document_id = NULL` | No evidence created | — |
| `is_confirmed` values | Unchanged | Still valid under new CHECK |

---

## 九、Backward Compatibility

### 9.1 API

| Endpoint | Change | Breaking? |
|---|---|---|
| `POST /memory` | New optional `assertion_kind`. Atomically creates MANUAL evidence. | No |
| `GET /memory` | Response adds `assertion_kind`, `summary` | No |
| `PUT /memory/{id}` | `is_confirmed` now validates transitions | Soft |
| `POST /memory/{id}/confirm` | No change | No |
| `POST /memory/{id}/reject` | No change | No |

**New endpoints:**

| Endpoint | Purpose |
|---|---|
| `GET /memory/{id}/evidence` | List evidence |
| `POST /memory/{id}/evidence` | Add evidence |
| `DELETE /memory/{id}/evidence/{evidence_id}` | Remove evidence |

**Removed from 1A scope:** `POST /memory/{id}/archive` — ARCHIVED is only a system state (evidence-loss), not user-triggered (Item 13).

### 9.2 Frontend

All existing components work unchanged. New fields additive.

### 9.3 Tests

All existing tests pass. `test_create_memory` passes (assertion_kind defaults). `test_e2e_memory_candidate_flow` passes (confirm/reject unchanged).

---

## 十、Phase 1A Behavioral Tests

### 10.1 Migration Tests

```python
async def test_fresh_database_migration():
    """Fresh DB → alembic upgrade head → all tables + constraints + indexes."""

async def test_legacy_database_upgrade():
    """Legacy DB → verify_schema → stamp 001_baseline → upgrade → data preserved + evidence created."""

async def test_migration_preserves_all_memory_rows():
    """100 diverse memories → migration → 100 preserved, all fields intact."""

async def test_migration_idempotency():
    """Running upgrade head twice does not duplicate or fail."""
```

### 10.2 verify_schema Preflight Tests

```python
async def test_verify_rejects_invalid_status():
    """Legacy memory with is_confirmed='BANANA' → verification fails."""

async def test_verify_rejects_out_of_range_confidence():
    """Legacy memory with confidence=5.0 → verification fails."""

async def test_verify_rejects_out_of_range_importance():
    """Legacy memory with importance=-0.3 → verification fails."""

async def test_verify_rejects_dangling_source_document():
    """Legacy memory with source_document_id pointing to deleted document → verification fails."""

async def test_verify_rejects_cross_user_source():
    """Legacy memory with source_document_id pointing to another user's document → verification fails."""
```

### 10.3 Lifecycle Tests

```python
async def test_lifecycle_manual_create_is_confirmed():
    """POST /memory by user → USER_STATED + CONFIRMED + MANUAL evidence created."""

async def test_manual_create_confirm_is_idempotent():
    """Confirming an already-CONFIRMED memory → 200, no change."""

async def test_lifecycle_ai_extracted_is_pending():
    """AI extraction from user message → USER_STATED + PENDING."""

async def test_lifecycle_confirmed_to_archived_on_evidence_loss():
    """CONFIRMED + last evidence removed → ARCHIVED."""

async def test_lifecycle_pending_to_archived_on_evidence_loss():
    """PENDING + last evidence removed → ARCHIVED (Item 14)."""

async def test_lifecycle_archived_to_pending():
    """ARCHIVED + new evidence → PENDING (not CONFIRMED)."""

async def test_illegal_rejected_to_confirmed():
    """REJECTED → CONFIRMED → 400."""

async def test_illegal_confirmed_to_pending():
    """CONFIRMED → PENDING → 400."""

async def test_illegal_to_superseded():
    """Any → SUPERSEDED → 400 in 1A."""
```

### 10.4 Evidence Tests

```python
async def test_memory_multiple_evidence():
    """Memory has DOCUMENT + CONVERSATION evidence."""

async def test_evidence_cascade_document_delete():
    """Document delete → evidence removed → CONFIRMED → ARCHIVED."""

async def test_evidence_cascade_preserves_with_other():
    """Document delete → evidence removed, but CONFIRMED stays (other evidence exists)."""

async def test_evidence_cascade_conversation_delete():
    """ConversationMessage delete → evidence removed → cascade."""

async def test_evidence_cascade_decision_delete():
    """Decision delete → evidence removed → cascade."""

async def test_provenance_traceable():
    """From memory, trace to source document via evidence."""
```

### 10.5 Cross-User Isolation Tests

```python
async def test_db_rejects_cross_user_evidence():
    """INSERT evidence(memory_id=A, user_id=B) → DB IntegrityError (composite FK)."""

async def test_service_rejects_cross_user_document():
    """Add evidence from another user's document → 403."""

async def test_service_rejects_cross_user_conversation():
    """Add evidence from another user's message → 403."""

async def test_service_rejects_cross_user_decision():
    """Add evidence from another user's decision → 403."""
```

### 10.6 last_used_at Test (Item 16)

```python
async def test_last_used_at_written_on_recall():
    """Memory included in chat context → last_used_at updated."""
    mem = create_memory_and_confirm()
    assert mem.last_used_at is None
    chat = send_chat("question that triggers memory recall", memory_enabled=True)
    refreshed = get_memory(mem.id)
    assert refreshed.last_used_at is not None

async def test_last_used_at_not_written_when_excluded():
    """Memory NOT included in chat context → last_used_at unchanged."""
    mem = create_memory_and_confirm()
    send_chat("question unrelated to memory", memory_enabled=True)
    refreshed = get_memory(mem.id)
    assert refreshed.last_used_at is None
```

### 10.7 Regression Test

```python
async def test_memory_baseline_regression():
    """Phase 0 baseline MUST pass unchanged."""
    mem = create_memory(content="I prefer Python", type="PREFERENCE", importance=0.9)
    confirm_memory(mem.id)
    chat = send_chat("What programming language do I prefer?", memory_enabled=True)
    assert "Python" in chat.answer
```

---

## 十一、NOT IN SCOPE

Phase 1A will NOT implement:

| Excluded | Reason |
|---|---|
| Memory embedding | Deferred 1B |
| Semantic retrieval | Deferred 1B |
| Reranker | Deferred 1B |
| Confidence formula / calibration | Deferred 1B (needs eval) |
| LLM deduplication | Deferred 1C |
| Contradiction detection | Deferred 1C |
| Automatic revision / superseding | Deferred 1C |
| MemoryRevision table | Deferred 1C |
| Reflection | Deferred 1D |
| Prediction / proactive AI | Deferred 1E |
| Agent | Deferred 1E |
| Dashboard redesign | Deferred 1F |
| New Cognitive Engine | Deferred 1G |
| Memory Engine 2.0 | Deferred 1G |
| User-driven archive (POST archive) | ARCHIVED is system-only in 1A |

---

## 十二、Proposed Architecture

```
User
  │
  ├── Memory
  │     ├── assertion_kind: USER_STATED | OBSERVED | INFERRED | LEGACY_UNKNOWN
  │     ├── is_confirmed: PENDING | CONFIRMED | REJECTED | ARCHIVED | SUPERSEDED(1A-enum-only)
  │     ├── last_used_at (written during chat recall when memory is packed into context)
  │     │
  │     ├── UNIQUE(memory_id, user_id)
  │     │
  │     └── MemoryEvidence[0..N]
  │           ├── source_type → DOCUMENT | CONVERSATION | DECISION | MANUAL | LEGACY_UNKNOWN
  │           ├── evidence_kind → DIRECT_QUOTE | PARAPHRASE | OBSERVATION | USER_CORRECTION
  │           ├── Composite FK (memory_id, user_id) → memories(memory_id, user_id)
  │           └── Service validates source entity belongs to same user
  │
  ├── Belief (existing, no 1A changes)
  └── Decision (existing, no 1A changes)
```

---

## 十三、Implementation Plan

### 13.1 Files to Modify

| File | Changes |
|---|---|
| `app/models/memory.py` | Add `assertion_kind`, `summary`. Add `UNIQUE(memory_id, user_id)`. |
| `app/models/__init__.py` | Import `MemoryEvidence`. |
| `app/schemas/memory.py` | Add fields to create/update/response schemas. |
| `app/api/memory.py` | Status transition validation. Evidence endpoints. Manual creation atomically creates evidence. Remove archive endpoint. |
| `app/services/rag_service.py` | Write `last_used_at` when memory is packed into context. Filter ARCHIVED. |
| `app/services/memory_extractor.py` | Set `assertion_kind` + `source_type`. Only extract from user-side data. |
| `app/services/document_service.py` | Call `on_source_deleted()` on document delete. |
| `app/services/chat_service.py` | Call `on_source_deleted()` on message delete. |
| `app/services/decision_service.py` | Call `on_source_deleted()` on decision delete. |
| `app/main.py` | Remove `init_db()` for production (Alembic only). |
| `scripts/verify_schema.py` | Preflight checks (§2.3). |

### 13.2 Files to Add

| File | Purpose |
|---|---|
| `app/models/evidence.py` | `MemoryEvidence` model |
| `alembic/versions/001_baseline.py` | Baseline (stamp existing schema) |
| `alembic/versions/002_memory_foundation.py` | Phase 1A migration |
| `scripts/verify_schema.py` | Schema verification for legacy adoption |
| `tests/test_memory_lifecycle.py` | Lifecycle + confirm idempotency tests |
| `tests/test_memory_evidence.py` | Evidence CRUD + cascade + cross-user tests |
| `tests/test_migration.py` | Migration preservation + preflight tests |

### 13.3 Implementation Order

```
1. Alembic bootstrap (001 baseline + verify_schema script)
2. Models (UNIQUE constraint + MemoryEvidence + Memory updates)
3. 002 migration
4. Lifecycle transition validation + tests
5. Evidence CRUD API + manual creation atomicity + tests
6. Source deletion domain operations (Document, ConversationMessage, Decision)
7. RAG service: last_used_at write + filter archived
8. Memory extractor: only extract from user-side data
9. Full regression test suite
10. Remove init_db() production path
```

### 13.4 Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Migration on production DB | High | Schema verification before stamp. DB copy tested. Rollback tested. |
| Legacy source parsing imperfect | Medium | Unknown → LEGACY_UNKNOWN. No data lost. |
| Composite FK requires UNIQUE first | Low | Added to migration Step 2, before Step 4. |

### 13.5 Acceptance Criteria

1. **Migration**: Fresh DB and legacy DB paths work. All memories preserved.
2. **Schema Authority**: Alembic sole authority. No `create_all()` in production.
3. **Lifecycle**: Legal transitions succeed. Illegal rejected. SUPERSEDED blocked. PENDING/CONFIRMED → ARCHIVED on evidence loss. ARCHIVED + evidence → PENDING.
4. **Evidence**: Multiple evidence per memory. DB composite FK rejects cross-user evidence. Service rejects cross-user source entities.
5. **Atomic manual creation**: `POST /memory` creates memory + MANUAL evidence atomically.
6. **Deletion cascade**: Document/ConversationMessage/Decision delete → evidence cascade → archive if 0 evidence.
7. **last_used_at**: Written only when memory is packed into chat context.
8. **Regression**: `I prefer Python → confirm → chat → Python` PASSES.
9. **Existing tests**: All pass unchanged.
10. **No scope creep**: No embedding, no confidence formula, no superseding, no user-driven archive, no reflection.

---

*Design Revision v2.1 — Awaiting External Review.*