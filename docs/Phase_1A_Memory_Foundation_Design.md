# Phase 1A — Memory Foundation Design

> **Status**: Design Revision v2 — Awaiting External Review  
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

### 1.1 Current Memory Schema (真实实现 — 逐字段核对自 `app/models/memory.py`)

```
Table: memories
──────────────────────────────────────────────────
memory_id          UUID PK                             (line 29)
user_id            UUID FK → users NOT NULL, indexed   (line 32)
memory_type        String(20) NOT NULL, indexed        (line 35)  -- enum: FACT/EXPERIENCE/OPINION/DECISION/PREFERENCE
content            Text NOT NULL                       (line 36)
source             String(255) nullable                (line 39)  -- free-text, e.g. "对话提取 (conversation_id: ...)"
source_document_id UUID FK → documents nullable        (line 40)
importance         Float default 0.5                   (line 43)  -- range 0-1
confidence         Float default 0.8                   (line 44)  -- range 0-1
frequency          Integer default 1                   (line 45)
last_used_at       DateTime(tz) nullable               (line 48)
expires_at         DateTime(tz) nullable               (line 49)
is_confirmed       String(20) default "PENDING"        (line 52)  -- enum: PENDING/CONFIRMED/REJECTED
created_at         DateTime(tz) NOT NULL               (line 55)
updated_at         DateTime(tz) NOT NULL               (line 56)

Composite indexes (line 62-66):
  ix_memory_user_confirmed  (user_id, is_confirmed)
  ix_memory_user_type       (user_id, memory_type)
  ix_memory_user_importance (user_id, importance)
```

**Corrections from v1 (External Review Item 15):**

| v1 Claim | Actual Code | Corrected? |
|---|---|---|
| "last_accessed_at: Column exists but never written" | **No such column.** Model has `last_used_at`, not `last_accessed_at`. | Yes — v1 was wrong. |
| "expires_at: Column exists but never set by any code path" | Correct — column exists (line 49), no code writes it. | Yes. |
| "confidence: Column exists but always defaults to 0.8, never recalculated" | Correct — only default, never updated. | Yes. |
| "importance: Column exists, only incremented by dedup" | Correct — `memory_extractor.py` does `importance = min(1.0, importance + 0.1)`. | Yes. |

**What does NOT exist in the DB:**

| Missing | Status |
|---|---|
| `summary` (Text) | Not present |
| `embedding` (Vector) | Not present — Memory has NO vector search |
| `assertion_kind` (String) | Not present |
| `last_accessed_at` | **Does not exist.** `last_used_at` exists (line 48) and is the correct field. |

**What does NOT exist as a table:**

| Missing Table | Purpose (from docs) |
|---|---|
| `memory_evidence` | One Memory → Many Evidence records. First-class provenance. |

### 1.2 Current Memory Lifecycle (真实实现)

```
Create memory → is_confirmed = "PENDING"
POST /{id}/confirm → is_confirmed = "CONFIRMED"
POST /{id}/reject  → is_confirmed = "REJECTED"
PUT /{id}          → is_confirmed can be set to ANY value (no transition validation)
DELETE /{id}       → hard delete from DB
```

**Missing transitions from docs:**

| Missing | Source |
|---|---|
| CONFIRMED → ARCHIVED | Evidence cascade (document deleted, no remaining evidence) |
| ARCHIVED → PENDING | New evidence added to archived memory |

### 1.3 Current Memory Search (真实实现)

```
Search: ILIKE keyword match × 0.7 + importance × 0.3
No vector/semantic search on memories
Dedup: ILIKE prefix match on first 50 chars
```

### 1.4 Current Memory Evidence / Provenance (真实实现)

```
source: String(255) — free-text, e.g. "对话提取 (conversation_id: abc)"
source_document_id: UUID FK → documents — only links to Documents
```

| Design Requirement | Current Status |
|---|---|
| One Memory → Many Evidence records | Not implemented (single `source` string) |
| Evidence tracks source_type + source_id | Only `source_document_id` FK |
| Document deletion → evidence cascade → archive if empty | Not implemented |
| Cross-user evidence isolation | Not enforced at DB level |

### 1.5 Summary of Gaps

| Gap | Severity | Phase 1A? |
|---|---|---|
| No MemoryEvidence table | **Critical** | Yes |
| No assertion_kind distinction | **Critical** | Yes |
| No Alembic migrations (schema managed by `create_all`) | **High** | Yes |
| Lifecycle missing ARCHIVED | **High** | Yes |
| PUT allows arbitrary status transitions | **High** | Yes |
| No DB-level user isolation on evidence | **High** | Yes |
| No embedding on Memory | **Medium** | Deferred to 1B |
| Document deletion → evidence cascade | **High** | Yes |
| `summary` field missing | **Low** | Yes |
| `last_used_at` never written by recall | **Low** | Yes — write it during chat recall |

---

## 二、Schema Authority — Policy

**Production runtime MUST NOT use `create_all()` / `table.create()` to modify business schema.**

Current code (`app/main.py` lifespan → `init_db()` → `Base.metadata.create_all(checkfirst=True)`) creates a **dual schema authority** with Alembic. This is unacceptable for production.

### 2.1 Rules (Item 16)

1. **Alembic is the sole authority** for production PostgreSQL schema.
2. **`init_db()` / `create_all()` is FORBIDDEN in production.** Application startup must not auto-create, auto-stamp, or auto-run schema migrations.
3. **Schema upgrades** are explicit: `alembic upgrade head` executed by operator before deploy.
4. **SQLite** is retained only as a development convenience. Tests that need PostgreSQL skip on SQLite. CI runs against PostgreSQL + pgvector.
5. **`alembic stamp head`** is a one-time operation on existing legacy databases, only after schema verification.

### 2.2 Alembic Bootstrap / Adoption Strategy (Item 17)

**Two supported bootstrap paths:**

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
alembic stamp head     # Marks current schema as baseline

# Step 3: Apply Phase 1A migration
alembic upgrade head   # Adds new columns + evidence table + constraints
```

**Forbidden:** `alembic stamp head` without prior schema verification. If verification fails, migration must be written manually or autogenerate must be used.

### 2.3 Migration Tests

```python
# Test 1: Fresh database
async def test_fresh_database_migration():
    """Create empty DB → alembic upgrade head → all tables exist with correct schema."""
    # Run against a clean PostgreSQL test database
    # Verify: users, documents, knowledge_chunks, conversations, conversation_messages,
    #         memories, beliefs, belief_history, decisions, memory_evidence tables exist
    # Verify: all CHECK constraints active
    # Verify: all indexes created

# Test 2: Existing legacy database
async def test_legacy_database_upgrade():
    """Pre-existing DB with legacy memories → schema verification → stamp → upgrade → data preserved."""
    # 1. Create legacy DB with init_db() (create_all)
    # 2. Insert test memories with various is_confirmed values
    # 3. Run schema verification script
    # 4. alembic stamp head
    # 5. alembic upgrade head
    # 6. All legacy memories still exist, content/type/importance unchanged
    # 7. assertion_kind defaults to LEGACY_UNKNOWN
    # 8. Evidence records created from source data

# Test 3: Migration preserves all Memory rows
async def test_migration_preserves_all_memory_rows():
    """Every memory row must survive migration without data loss."""
    # Pre-migration: insert 100 memories with diverse data
    # Post-migration: count == 100, all fields preserved
```

### 2.4 Downgrade / Rollback Strategy

```sql
# Downgrade: remove Phase 1A additions, keep legacy data
DROP TABLE IF EXISTS memory_evidence;
ALTER TABLE memories DROP COLUMN IF EXISTS assertion_kind;
ALTER TABLE memories DROP COLUMN IF EXISTS summary;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_status;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_assertion_kind;
```

**Post-downgrade:** all legacy columns and data are unaffected. `is_confirmed` reverts to unconstrained string (valid values: PENDING/CONFIRMED/REJECTED).

---

## 三、Memory Schema v2 — Design

### 3.1 Existing Fields (保留)

All existing fields preserved. No field removed.

### 3.2 New Fields

| Field | Type | Nullable | Default | Why | Writer | Updater | Index |
|---|---|---|---|---|---|---|---|
| `assertion_kind` | String(30) NOT NULL | NO | `"LEGACY_UNKNOWN"` | Distinguish epistemic status. LEGACY_UNKNOWN for pre-existing data whose origin cannot be determined. | Manual create → USER_STATED. Extraction → based on source. Legacy → LEGACY_UNKNOWN. | User correction only. | `(user_id, assertion_kind)` |
| `summary` | Text | YES | NULL | One-line summary for UI display and quick recall | AI extraction pipeline | User can edit | — |

### 3.3 assertion_kind vs confirmation — Fully Separated (Item 1)

`assertion_kind` and `is_confirmed` are orthogonal axes:

| Axis | Values | Meaning |
|---|---|---|
| `assertion_kind` | USER_STATED, OBSERVED, INFERRED, LEGACY_UNKNOWN | **How** the system knows this |
| `is_confirmed` | PENDING, CONFIRMED, REJECTED, ARCHIVED, SUPERSEDED | **Whether** the user has approved this |

A USER_STATED memory can be PENDING (if AI extracted it from conversation, not yet confirmed).
An OBSERVED memory can be CONFIRMED (if user reviewed and approved it).

**Manual creation:** `POST /memory` by user → `assertion_kind = USER_STATED`, `is_confirmed = CONFIRMED` (user typed it, so it's confirmed by definition).

**AI extraction from conversation:** `assertion_kind = USER_STATED`, `is_confirmed = PENDING` (user said it, but user hasn't reviewed the extraction yet).

### 3.4 Fields Deliberately NOT Added

| Rejected Field | Why |
|---|---|
| `embedding` (vector) | Deferred to 1B. No retrieval pipeline to use it. |
| `semantic_score` | Computed at query time, not stored. |
| `recurrence_count` | Same as existing `frequency`. |
| `decay_rate` | Tracked in `memory_strengths` table. Don't duplicate. |

### 3.5 Three Scores — Explicit Separation

| Score | Definition | Stored? | Recalculated? |
|---|---|---|---|
| **importance** | How important to user's life/work | Yes | On user feedback |
| **confidence** | System confidence in accuracy (based on evidence) | Yes | When evidence added/removed |
| **relevance** | How relevant to current query | No — ephemeral | Every query |

**Phase 1A:** `confidence` is recalculation is deferred to 1B (requires eval). Phase 1A establishes the evidence infrastructure that will power future confidence recalculation.

### 3.6 Schema Authority Note

Alembic is the sole source of truth for PostgreSQL schema (§2). The SQLAlchemy model in `app/models/memory.py` must match the Alembic migration. The model is NOT the authority — Alembic is.

---

## 四、MemoryEvidence — Design

### 4.1 Rationale

> "Memory 不能只知道'是什么'，还必须知道'为什么系统认为它是真的'。"

A Memory is a claim. Evidence is the support. One claim can have multiple supports. When supports disappear, the claim must be re-evaluated.

### 4.2 Schema

```
Table: memory_evidence
──────────────────────────────────────────────────
evidence_id       UUID PK
memory_id         UUID NOT NULL   -- FK composite with user_id (§4.6)
user_id           UUID NOT NULL   -- FK composite with memory_id (§4.6)
source_type       String(20) NOT NULL
source_id         UUID NULL       -- polymorphic reference (§4.4)
source_span       Text NULL       -- quote or locator
evidence_kind     String(20) NOT NULL DEFAULT 'DIRECT_QUOTE'
evidence_strength Float NOT NULL DEFAULT 1.0  -- range 0-1
observed_at       DateTime(tz) NULL
created_at        DateTime(tz) NOT NULL
```

### 4.3 Source Types

| source_type | source_id points to | Example |
|---|---|---|
| `CONVERSATION` | `conversation_messages.message_id` | "In message X, user said 'I prefer Python'" |
| `DOCUMENT` | `documents.document_id` | "In doc Y, section Z says 'Launch date 2031-09-17'" |
| `DECISION` | `decisions.decision_id` | "User chose Python in decision about tech stack" |
| `MANUAL` | NULL | User typed "I prefer Python" directly |
| `CORRECTION` | `conversation_messages.message_id` | User corrected AI |
| `LEGACY_UNKNOWN` | NULL | Migrated from pre-1A `source` text where origin can't be determined |

### 4.4 Polymorphic Source — Domain Operation (Item 14)

**Source deletion is a domain operation, not just SQL cascading:**

```python
def on_source_deleted(source_type: str, source_id: UUID, db: Session):
    """
    Domain operation: called when a source entity is deleted.
    NOT a database cascade — this is application-level orchestration.
    """
    # 1. Find all evidence from this source
    evidence_records = db.query(MemoryEvidence).filter(
        MemoryEvidence.source_type == source_type,
        MemoryEvidence.source_id == source_id
    ).all()

    # 2. Delete evidence records
    for ev in evidence_records:
        db.delete(ev)

    # 3. For each affected memory, re-evaluate status
    affected_memory_ids = {ev.memory_id for ev in evidence_records}
    for memory_id in affected_memory_ids:
        remaining = db.query(MemoryEvidence).filter(
            MemoryEvidence.memory_id == memory_id
        ).count()
        if remaining == 0:
            memory = db.query(Memory).get(memory_id)
            if memory.is_confirmed == "CONFIRMED":
                memory.is_confirmed = "ARCHIVED"

    db.commit()
```

**Why NOT database-level polymorphic FK:** PostgreSQL doesn't support multi-table FK. Options:

1. **Application-level validation** (chosen): Service resolves `source_id` → correct table at read/write time. DB has CHECK on `source_type` only.
2. Separate FK columns per type: Rejected — schema bloat.
3. Generic FK (table_name + id): Rejected — breaks referential integrity.

### 4.5 Evidence Lifecycle Rules

| Event | Domain Operation |
|---|---|
| **Source deleted (document)** | `on_source_deleted("DOCUMENT", doc_id, db)` |
| **Source deleted (conversation)** | `on_source_deleted("CONVERSATION", msg_id, db)` |
| **Source deleted (decision)** | `on_source_deleted("DECISION", dec_id, db)` |
| **User adds evidence** | Insert record. |
| **User removes evidence** | Delete record. Re-evaluate status (archive if 0 evidence + CONFIRMED). |
| **Multiple sources** | Each evidence is independent. |

### 4.6 Cross-User Isolation (Item 10 — Composite FK, Not Trigger)

**Design:** `memory_evidence` uses a composite FK `(memory_id, user_id)` referencing `memories(memory_id, user_id)`.

This means PostgreSQL enforces that evidence can only reference a memory belonging to the same user — without triggers.

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

    -- Composite FK: evidence must reference a memory owned by the same user
    CONSTRAINT fk_evidence_memory
        FOREIGN KEY (memory_id, user_id)
        REFERENCES memories(memory_id, user_id)
        ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_evidence_source_type
        CHECK (source_type IN ('CONVERSATION', 'DOCUMENT', 'DECISION', 'MANUAL', 'CORRECTION', 'LEGACY_UNKNOWN')),
    CONSTRAINT chk_evidence_kind
        CHECK (evidence_kind IN ('DIRECT_QUOTE', 'PARAPHRASE', 'OBSERVATION', 'USER_CORRECTION')),
    CONSTRAINT chk_evidence_strength_range
        CHECK (evidence_strength >= 0.0 AND evidence_strength <= 1.0)
);
```

**This requires `memories` to have a composite UNIQUE on `(memory_id, user_id)`** — which it already does (PK + FK).

**DB-level failure test (Item 18):**
```python
async def test_evidence_rejects_cross_user_insert():
    """Inserting evidence with mismatched user_id must fail at DB level."""
    # memory.user_id = A
    # evidence.user_id = B, evidence.memory_id = memory_id
    # PostgreSQL MUST reject: FK violation on (memory_id, user_id) composite
    # This is NOT a service-level check — it's enforced by the DB constraint
```

---

## 五、Epistemic / Assertion Kind — Design (Item 1)

### 5.1 Four Values (Item 1 — LEGACY_UNKNOWN added)

| Kind | Definition | Example |
|---|---|---|
| `USER_STATED` | User explicitly said or wrote this | "I prefer Python" |
| `OBSERVED` | System observed a pattern from user's data | "4 of your last 5 projects use Python" |
| `INFERRED` | AI concluded this from combining evidence | "You may prefer Python for backend" |
| `LEGACY_UNKNOWN` | Pre-1A memory whose epistemic origin cannot be determined | Any migrated memory without clear source |

### 5.2 Policy Matrix

| Policy | USER_STATED | OBSERVED | INFERRED | LEGACY_UNKNOWN |
|---|---|---|---|---|
| **Initial status** | Depends on creation path (see §5.3) | PENDING | PENDING | PRESERVED (whatever is_confirmed was) |
| **Confidence ceiling** | 1.0 | 0.9 | 0.7 | N/A |
| **Retrieval priority** | Highest | Medium | Lowest | Lowest |
| **UI badge** | "User stated" | "Observed" | "AI inference" | No badge |
| **Can confirm directly?** | Only if manual creation | No | No | N/A |

### 5.3 Confirmation Lifecycle Is Separated from assertion_kind (Item 1)

**Manual creation (`POST /memory` by user):**
→ `assertion_kind = USER_STATED`, `is_confirmed = CONFIRMED` (user typed it, confirmed by definition)

**AI extraction from conversation user message:**
→ `assertion_kind = USER_STATED`, `is_confirmed = PENDING` (user said it, but extraction not yet reviewed)

**AI extraction from AI assistant message:**
→ `assertion_kind = OBSERVED`, `is_confirmed = PENDING`

**AI pattern detection:**
→ `assertion_kind = OBSERVED`, `is_confirmed = PENDING`

**AI inference:**
→ `assertion_kind = INFERRED`, `is_confirmed = PENDING`

**Legacy migration:**
→ `assertion_kind = LEGACY_UNKNOWN`, `is_confirmed` = preserved as-is

---

## 六、Memory Lifecycle State Machine

### 6.1 States

| State | Meaning |
|---|---|
| `PENDING` | Candidate awaiting user decision. Not used in recall. |
| `CONFIRMED` | User approved. Used in recall. |
| `REJECTED` | User explicitly rejected. Not used in recall. Hidden from UI. |
| `ARCHIVED` | Source evidence was removed. Not used in recall. Preserved for audit. |
| `SUPERSEDED` | Reserved for Phase 1C (Item 18 — enum value only, no transitions). |

### 6.2 State Machine (Item 18 — ARCHIVED + evidence → PENDING, not CONFIRMED)

```
                    ┌───────────────────────────────────────────────────┐
                    │                                                   │
                    ▼                                                   │
              ┌──────────┐                                             │
    create →  │ PENDING  │ ──── confirm ──────→ ┌────────────┐         │
              └──────────┘                      │ CONFIRMED  │         │
                    │                           └────────────┘         │
                    │ reject          │ archive                        │
                    ▼                 ▼                                │
              ┌──────────┐    ┌──────────┐                            │
              │ REJECTED │    │ ARCHIVED │ ── add evidence → ─────────┘
              └──────────┘    └──────────┘     (becomes PENDING)
```

### 6.3 Legal Transitions

| From | To | Trigger | Permission |
|---|---|---|---|
| (new) | PENDING | AI extraction, or legacy migration | System |
| (new, manual) | CONFIRMED | `POST /memory` by user | User |
| PENDING | CONFIRMED | `POST /{id}/confirm` | User |
| PENDING | REJECTED | `POST /{id}/reject` | User |
| CONFIRMED | ARCHIVED | Evidence cascade (source deleted, 0 evidence remains) | System (automatic) |
| ARCHIVED | PENDING | New evidence added (item 18: not directly to CONFIRMED) | System / User |

### 6.4 Illegal Transitions

| From | To | Why |
|---|---|---|
| REJECTED | CONFIRMED | Must re-evaluate (go through PENDING) |
| REJECTED | ARCHIVED | No evidence relationship |
| ARCHIVED | CONFIRMED | New evidence → PENDING, user must re-evaluate |
| CONFIRMED | PENDING | Cannot un-confirm |
| (any) | SUPERSEDED | Reserved for Phase 1C (no transitions allowed in 1A) |

### 6.5 Delete vs Archive

| Action | Delete | Archive |
|---|---|---|
| DB record | Removed from `memories` | Stays with `is_confirmed = ARCHIVED` |
| Evidence | Hard deleted | Evidence records removed, memory preserved |
| Audit | Lost | Preserved |
| Recall | Invisible | Invisible |
| Restore | Impossible | Possible via add evidence → PENDING → user confirm |

---

## 七、Database Invariants

### 7.1 Constraints

```sql
-- 1. Memory user FK (existing, enforce)
ALTER TABLE memories ADD CONSTRAINT fk_memory_user
    FOREIGN KEY (user_id) REFERENCES users(user_id);

-- 2. Evidence composite FK — enforces user ownership at DB level
-- (§4.6 above, composite FK on memory_id + user_id)

-- 3. Status valid values
ALTER TABLE memories ADD CONSTRAINT chk_memory_status
    CHECK (is_confirmed IN ('PENDING', 'CONFIRMED', 'REJECTED', 'ARCHIVED', 'SUPERSEDED'));

-- 4. assertion_kind valid values
ALTER TABLE memories ADD CONSTRAINT chk_assertion_kind
    CHECK (assertion_kind IN ('USER_STATED', 'OBSERVED', 'INFERRED', 'LEGACY_UNKNOWN'));

-- 5-8. Evidence constraints (§4.6 above)

-- 9. Confidence range
ALTER TABLE memories ADD CONSTRAINT chk_confidence_range
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- 10. Importance range
ALTER TABLE memories ADD CONSTRAINT chk_importance_range
    CHECK (importance >= 0.0 AND importance <= 1.0);
```

### 7.2 Indexes

```sql
-- Existing (keep, no duplicates — Item 18)
-- ix_memory_user_confirmed already exists on (user_id, is_confirmed)
-- ix_memory_user_type already exists on (user_id, memory_type)
-- ix_memory_user_importance already exists on (user_id, importance)

-- New
CREATE INDEX ix_memory_assertion_kind ON memories (user_id, assertion_kind);
CREATE INDEX ix_evidence_memory ON memory_evidence (memory_id);
CREATE INDEX ix_evidence_user ON memory_evidence (user_id);
CREATE INDEX ix_evidence_source ON memory_evidence (source_type, source_id);
```

---

## 八、Migration Strategy

### 8.1 Bootstrap Paths (§2.2)

- **Fresh DB**: `alembic upgrade head` creates everything.
- **Legacy DB**: `verify_schema` → `alembic stamp head` → `alembic upgrade head`.

### 8.2 Phase 1A Migration (`002_memory_foundation.py`)

```sql
-- Step 1: Add new columns
ALTER TABLE memories ADD COLUMN assertion_kind VARCHAR(30) NOT NULL DEFAULT 'LEGACY_UNKNOWN';
ALTER TABLE memories ADD COLUMN summary TEXT;

-- Step 2: Create evidence table with composite FK (§4.6)
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
    CONSTRAINT fk_evidence_memory FOREIGN KEY (memory_id, user_id)
        REFERENCES memories(memory_id, user_id) ON DELETE CASCADE,
    CONSTRAINT chk_evidence_source_type CHECK (source_type IN ('CONVERSATION','DOCUMENT','DECISION','MANUAL','CORRECTION','LEGACY_UNKNOWN')),
    CONSTRAINT chk_evidence_kind CHECK (evidence_kind IN ('DIRECT_QUOTE','PARAPHRASE','OBSERVATION','USER_CORRECTION')),
    CONSTRAINT chk_evidence_strength_range CHECK (evidence_strength >= 0.0 AND evidence_strength <= 1.0)
);

-- Step 3: Migrate legacy source → evidence
-- source_document_id NOT NULL → DOCUMENT evidence
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength)
SELECT memory_id, user_id, 'DOCUMENT', source_document_id, 'PARAPHRASE', 0.7
FROM memories WHERE source_document_id IS NOT NULL;

-- source text parseable as conversation → CONVERSATION evidence
-- source text like "对话提取 (conversation_id: xxx)" → CONVERSATION, source_id=NULL
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength, source_span)
SELECT memory_id, user_id, 'LEGACY_UNKNOWN', NULL, 'PARAPHRASE', 0.5, source
FROM memories
WHERE source IS NOT NULL AND source_document_id IS NULL
AND source NOT LIKE '%对话提取%';  -- those that can't be reliably parsed

-- source text parseable as conversation reference → CONVERSATION evidence
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength, source_span)
SELECT memory_id, user_id, 'CONVERSATION', NULL, 'PARAPHRASE', 0.6, source
FROM memories
WHERE source LIKE '%对话提取%';

-- Step 4: Add CHECK constraints
ALTER TABLE memories ADD CONSTRAINT chk_memory_status
    CHECK (is_confirmed IN ('PENDING','CONFIRMED','REJECTED','ARCHIVED','SUPERSEDED'));
ALTER TABLE memories ADD CONSTRAINT chk_assertion_kind
    CHECK (assertion_kind IN ('USER_STATED','OBSERVED','INFERRED','LEGACY_UNKNOWN'));
```

### 8.3 Data Preservation

| Existing Data | Migration Action | After Migration |
|---|---|---|
| `memory.source` with `source_document_id` | → DOCUMENT evidence | Column kept (deprecated) |
| `memory.source` with "对话提取" text | → CONVERSATION evidence | Column kept |
| `memory.source` with other text | → LEGACY_UNKNOWN evidence | Column kept |
| `memory.source = NULL` | No evidence created | — |
| `memory.is_confirmed = PENDING/CONFIRMED/REJECTED` | Unchanged | Still valid |

**No data deleted. No existing field removed.**

### 8.4 Rollback

```sql
DROP TABLE IF EXISTS memory_evidence;
ALTER TABLE memories DROP COLUMN IF EXISTS assertion_kind;
ALTER TABLE memories DROP COLUMN IF EXISTS summary;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_status;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_assertion_kind;
```

---

## 九、Backward Compatibility

### 9.1 API

| Endpoint | Change | Breaking? |
|---|---|---|
| `POST /memory` | New optional field `assertion_kind` (default: USER_STATED for manual) | No |
| `GET /memory` | Response adds `assertion_kind`, `summary` | No |
| `PUT /memory/{id}` | `is_confirmed` now validates transitions | Soft — arbitrary writes rejected |
| `POST /memory/{id}/confirm` | No change | No |
| `POST /memory/{id}/reject` | No change | No |

**New endpoints:**

| Endpoint | Purpose |
|---|---|
| `GET /memory/{id}/evidence` | List evidence |
| `POST /memory/{id}/evidence` | Add evidence |
| `DELETE /memory/{id}/evidence/{evidence_id}` | Remove evidence |
| `POST /memory/{id}/archive` | Archive |

### 9.2 Frontend

All existing components work unchanged. New fields are additive.

### 9.3 Tests

All existing tests pass unchanged. `test_create_memory` passes because `assertion_kind` defaults to USER_STATED. `test_e2e_memory_candidate_flow` passes because confirm/reject logic is unchanged.

---

## 十、Phase 1A Behavioral Tests (Item 18)

### 10.1 Migration Tests

```python
async def test_fresh_database_migration():
    """Fresh DB → alembic upgrade head → all tables + constraints exist."""
    # Verify: users, documents, knowledge_chunks, memories, memory_evidence
    # Verify: CHECK constraints active
    # Verify: composite FK on memory_evidence(memory_id, user_id) exists

async def test_legacy_database_upgrade():
    """Legacy DB → verify → stamp → upgrade → data preserved."""
    # Pre-existing memories survive
    # assertion_kind = LEGACY_UNKNOWN for all legacy rows
    # Evidence records created from source data

async def test_migration_preserves_all_memory_rows():
    """Every memory row survives migration."""
    # Insert 100 diverse memories
    # Run migration
    # Count still 100, all fields preserved
```

### 10.2 Lifecycle Tests

```python
async def test_lifecycle_pending_to_confirmed():
    """PENDING → CONFIRMED"""
    memory = create_memory(status=PENDING)
    confirm_memory(memory.id)
    assert get_memory(memory.id).is_confirmed == "CONFIRMED"

async def test_lifecycle_manual_create_goes_directly_confirmed():
    """Manual user creation → USER_STATED + CONFIRMED (not PENDING)"""
    memory = create_memory(content="I prefer Python", assertion_kind="USER_STATED")
    assert memory.is_confirmed == "CONFIRMED"
    assert memory.assertion_kind == "USER_STATED"

async def test_lifecycle_ai_extracted_is_pending():
    """AI extraction from conversation → USER_STATED + PENDING"""
    memory = extract_memory_from_conversation(user_said="I prefer Python")
    assert memory.is_confirmed == "PENDING"
    assert memory.assertion_kind == "USER_STATED"

async def test_lifecycle_confirmed_to_archived():
    """CONFIRMED → ARCHIVED when last evidence removed"""
    memory = create_memory_with_evidence(count=1)
    remove_evidence(memory.id)
    assert get_memory(memory.id).is_confirmed == "ARCHIVED"

async def test_lifecycle_archived_to_pending():
    """ARCHIVED + new evidence → PENDING (not directly CONFIRMED)"""
    memory = create_memory(status=ARCHIVED)
    add_evidence(memory.id, source_type="DOCUMENT")
    assert get_memory(memory.id).is_confirmed == "PENDING"  # NOT CONFIRMED

async def test_illegal_transition_rejected_to_confirmed():
    """REJECTED → CONFIRMED must fail"""
    memory = create_memory(status=REJECTED)
    with pytest.raises(HTTPException, match="400"):
        confirm_memory(memory.id)

async def test_illegal_transition_confirmed_to_pending():
    """CONFIRMED → PENDING must fail"""
    memory = create_memory(status=CONFIRMED)
    with pytest.raises(HTTPException, match="400"):
        update_memory_status(memory.id, "PENDING")

async def test_illegal_transition_to_superseded():
    """Any → SUPERSEDED must fail in Phase 1A"""
    memory = create_memory(status=CONFIRMED)
    with pytest.raises(HTTPException, match="400"):
        update_memory_status(memory.id, "SUPERSEDED")
```

### 10.3 Evidence Tests

```python
async def test_memory_multiple_evidence():
    """Memory can have evidence from different sources."""
    memory = create_memory()
    add_evidence(memory.id, source_type="DOCUMENT", doc_id=doc1)
    add_evidence(memory.id, source_type="CONVERSATION", msg_id=msg1)
    assert len(list_evidence(memory.id)) == 2

async def test_evidence_user_isolation_service():
    """Service layer rejects cross-user evidence."""
    memory_a = create_memory_as_user_a()
    with pytest.raises(HTTPException, match="403"):
        add_evidence_as_user_b(memory_a.id)

async def test_evidence_user_isolation_db():
    """DB-level: composite FK rejects cross-user evidence even without service layer."""
    # Directly INSERT evidence with memory_id from user A, user_id = user B
    # PostgreSQL MUST reject: FK violation on composite (memory_id, user_id)
    with pytest.raises(Exception):  # IntegrityError
        raw_db_execute(
            "INSERT INTO memory_evidence (memory_id, user_id, source_type, evidence_kind) "
            "VALUES (:mid, :uid, 'MANUAL', 'DIRECT_QUOTE')",
            {"mid": memory_a_id, "uid": user_b_id}
        )

async def test_evidence_cascade_document_delete():
    """Document delete → evidence removed → memory archives if no evidence."""
    memory = create_memory_with_document_evidence(doc_id)
    delete_document(doc_id)
    assert len(list_evidence(memory.id)) == 0
    assert get_memory(memory.id).is_confirmed == "ARCHIVED"

async def test_evidence_cascade_preserves_with_other_evidence():
    """Document delete → evidence removed, but memory stays CONFIRMED if other evidence."""
    memory = create_memory_with_two_evidence(doc_id_1, doc_id_2)
    delete_document(doc_id_1)
    assert len(list_evidence(memory.id)) == 1
    assert get_memory(memory.id).is_confirmed == "CONFIRMED"

async def test_provenance_traceable():
    """From memory, trace to source document."""
    memory = create_memory_with_document_evidence(doc_id)
    evidence = list_evidence(memory.id)
    assert evidence[0].source_type == "DOCUMENT"
    assert evidence[0].source_id == doc_id
```

### 10.4 Regression Test

```python
async def test_memory_baseline_regression():
    """Phase 0 baseline MUST pass unchanged."""
    mem = create_memory(content="I prefer Python", type="PREFERENCE", importance=0.9)
    confirm_memory(mem.id)
    chat = send_chat("What programming language do I prefer?", memory_enabled=True)
    assert "Python" in chat.answer
```

---

## 十一、NOT IN SCOPE (Item 19)

Phase 1A will NOT implement:

| Excluded | Reason |
|---|---|
| Memory embedding | Deferred to 1B — requires retrieval pipeline design |
| Semantic retrieval | Deferred to 1B |
| Reranker | Deferred to 1B |
| LLM deduplication | Deferred to 1C |
| Contradiction detection | Deferred to 1C |
| Automatic revision / superseding | Deferred to 1C |
| Reflection (offline clustering, conflict detection) | Deferred to 1D |
| Prediction / proactive AI | Deferred to 1E |
| Agent / autonomous action | Deferred to 1E |
| Dashboard redesign | Deferred to 1F |
| New Cognitive Engine | Deferred to 1G |
| Memory Engine 2.0 full implementation | Deferred to 1G |
| Confidence formula implementation | Deferred to 1B (needs eval) |
| MemoryRevision table | Deferred to 1C |

**Phase 1A delivers:** Memory Claim + Evidence + Lifecycle + Provenance + DB Invariants + Migration Foundation.

---

## 十二、Proposed Architecture

```
User
  │
  ├── Memory
  │     ├── assertion_kind: USER_STATED | OBSERVED | INFERRED | LEGACY_UNKNOWN
  │     ├── is_confirmed: PENDING | CONFIRMED | REJECTED | ARCHIVED | SUPERSEDED(1A-only-enum)
  │     │
  │     ├── MemoryEvidence[0..N]
  │     │     ├── source_type → DOCUMENT / CONVERSATION / DECISION / MANUAL / CORRECTION / LEGACY_UNKNOWN
  │     │     └── Composite FK (memory_id, user_id) → memories(memory_id, user_id)
  │     │
  │     └── last_used_at (existing, write during recall)
  │
  ├── Belief (existing, no 1A changes)
  └── Decision (existing, no 1A changes)
```

### Layer Responsibilities

| Layer | Responsibility |
|---|---|
| **API Router** | Request parsing, auth, response serialization |
| **Service** | Lifecycle transitions, evidence cascade domain operations, user isolation |
| **Database** | CHECK constraints, composite FK, indexes |

---

## 十三、Implementation Plan

### 13.1 Files to Modify

| File | Changes |
|---|---|
| `app/models/memory.py` | Add `assertion_kind`, `summary`. Update CHECK constraint. |
| `app/models/__init__.py` | Import `MemoryEvidence`. |
| `app/schemas/memory.py` | Add fields to create/update/response schemas. |
| `app/api/memory.py` | Status transition validation. Evidence endpoints. Archive endpoint. |
| `app/services/rag_service.py` | Write `last_used_at` on recall. Filter ARCHIVED/SUPERSEDED. |
| `app/services/memory_extractor.py` | Set `assertion_kind` + `source_type` during extraction. |
| `app/services/document_service.py` | Call `on_source_deleted()` on document delete. |
| `app/main.py` | Remove `init_db()` call (production uses Alembic only). |
| `tests/test_memory.py` | Add lifecycle, evidence tests. |

### 13.2 Files to Add

| File | Purpose |
|---|---|
| `app/models/evidence.py` | `MemoryEvidence` model |
| `alembic/versions/001_baseline.py` | Baseline migration (stamp existing schema) |
| `alembic/versions/002_memory_foundation.py` | Phase 1A migration |
| `scripts/verify_schema.py` | Schema verification for legacy DB adoption |
| `tests/test_memory_lifecycle.py` | Lifecycle transition tests |
| `tests/test_memory_evidence.py` | Evidence CRUD + cascade + DB isolation tests |
| `tests/test_migration.py` | Migration preservation tests |

### 13.3 Implementation Order

```
1. Alembic bootstrap (baseline migration + verify script)
2. Models (MemoryEvidence + Memory updates)
3. Phase 1A migration
4. Lifecycle transition validation + tests
5. Evidence CRUD API + tests
6. Document delete → evidence cascade domain operation
7. RAG service: last_used_at write + filter archived
8. Memory extractor: set assertion_kind + source_type
9. Full regression test suite
10. Remove init_db() production path
```

### 13.4 Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Migration on production DB | **High** | Schema verification before stamp. Tested on DB copy. Rollback tested. |
| Composite FK (memory_id, user_id) requires memories PK match | **Low** | memories PK is memory_id alone; composite unique is guaranteed by PK + FK. Verified in migration test. |
| Legacy source parsing is imperfect | **Medium** | Unknown origins → LEGACY_UNKNOWN. No data lost. |

### 13.5 Acceptance Criteria

1. **Migration**: Both fresh DB and legacy DB paths work. All existing memories preserved.
2. **Lifecycle**: Legal transitions succeed. Illegal transitions rejected (400). SUPERSEDED blocked in 1A.
3. **Evidence**: Multiple evidence per memory. DB-level cross-user rejection via composite FK.
4. **Cascade**: Document delete → evidence removed → CONFIRMED → ARCHIVED (if 0 evidence). CONFIRMED stays if other evidence exists.
5. **ARCHIVED + evidence → PENDING** (not CONFIRMED).
6. **assertion_kind**: Manual = USER_STATED + CONFIRMED. AI extraction = USER_STATED/OBSERVED + PENDING. Legacy = LEGACY_UNKNOWN.
7. **Regression**: `I prefer Python → confirm → chat → Python` PASSES.
8. **Existing tests**: All pass unchanged.
9. **No scope creep**: No embedding, no dedup, no reflection, no confidence formula.

---

*Design Revision v2 — Awaiting External Review.*
