# Phase 1A — Memory Foundation Design Proposal

> **Status**: Design Draft — Awaiting External Review  
> **Scope**: v0.2 Reliable Memory — Foundation Layer  
> **Constraint**: No code changes. Design only.

---

## 0. Design Methodology

This document is based on two parallel analyses:

1. **25 design documents** in `docs/` — what the product vision requires
2. **Current implementation** in `backend/app/` — what actually exists today

Every design decision below is grounded in the gap between these two, not in speculative feature additions.

---

## 一、Gap Analysis

### 1.1 Current Memory Schema (真实实现)

```
Table: memories
──────────────────────────────────────────────────
memory_id        UUID PK
user_id          UUID FK → users (indexed)
memory_type      String(20) NOT NULL (indexed)  -- enum: FACT/EXPERIENCE/OPINION/DECISION/PREFERENCE
content          Text NOT NULL
source           String(255) nullable            -- free-text, e.g. "对话提取 (conversation_id: ...)"
source_document_id UUID FK → documents nullable  -- only links to Documents, not Conversations/Decisions
importance       Float default 0.5               -- range 0-1
confidence       Float default 0.8               -- range 0-1
frequency        Integer default 1               -- incremented on dedup
last_used_at     DateTime(tz) nullable
expires_at       DateTime(tz) nullable
is_confirmed     String(20) default "PENDING"    -- enum: PENDING/CONFIRMED/REJECTED
created_at       DateTime(tz) NOT NULL
updated_at       DateTime(tz) NOT NULL

Indexes: (user_id, is_confirmed), (user_id, memory_type), (user_id, importance)

Relationships:
  user → User (back_populates)
```

**What does NOT exist in the DB:**

| Missing Field | Status |
|---|---|
| `summary` | Not present |
| `embedding` | Not present — Memory has NO vector search |
| `last_accessed_at` | Column exists but never written |
| `assertion_kind` | Not present — no USER_STATED / OBSERVED / INFERRED distinction |
| `expires_at` | Column exists but never set by any code path |
| `confidence` | Column exists but always defaults to 0.8, never recalculated |
| `importance` | Column exists, only incremented by dedup (+0.1), never by scoring formula |

**What does NOT exist as a table:**

| Missing Table | Purpose (from docs) |
|---|---|
| `memory_evidence` | One Memory → Many Evidence records. First-class provenance. |
| `memory_revisions` | Track content changes (who changed what, when) |

### 1.2 Current Memory Lifecycle (真实实现)

```
Create memory → is_confirmed = "PENDING"
POST /{id}/confirm → is_confirmed = "CONFIRMED"
POST /{id}/reject  → is_confirmed = "REJECTED"
PUT /{id}          → is_confirmed can be set to ANY value (no validation)
DELETE /{id}       → hard delete from DB
```

**Missing transitions from docs:**

| Missing Transition | From Design Doc |
|---|---|
| CANDIDATE → ARCHIVED | When source document is deleted and no other evidence remains |
| CONFIRMED → ARCHIVED | Explicit user action or automatic (no evidence) |
| CONFIRMED → SUPERSEDED | When a newer memory replaces this one |
| REJECTED → CANDIDATE | User can reconsider (recover) |

### 1.3 Current Memory Search (真实实现)

```
Search: ILIKE keyword match × 0.7 + importance × 0.3
No vector/semantic search on memories
Dedup: ILIKE prefix match on first 50 chars
```

**From docs — what scoring should be:**

```
score = 0.35 × importance + 0.25 × confidence + 0.20 × recurrence + 0.20 × explicit_user_signal
```

### 1.4 Current Memory Evidence / Provenance (真实实现)

```
source: String(255) — free-text, e.g. "对话提取 (conversation_id: abc)"
source_document_id: UUID FK → documents — only for document-sourced memories
```

**From docs — what evidence should be:**

| Design Requirement | Current Status |
|---|---|
| One Memory → Many Evidence records | Not implemented (single `source` string) |
| Evidence tracks source_type + source_id | Only `source_document_id` FK, no polymorphic source |
| Evidence has evidence_kind | Not present |
| Evidence has evidence_strength | Not present |
| Evidence has source_span/quote/locator | Not present |
| Document deletion → recompute evidence → archive if empty | Not implemented |
| Cross-user evidence isolation | Not enforced at DB level |

### 1.5 Summary of Gaps

| Gap | Severity | Phase 1A? |
|---|---|---|
| No MemoryEvidence table | **Critical** | Yes |
| No assertion_kind distinction | **Critical** | Yes |
| No Alembic migrations | **High** | Yes |
| Lifecycle missing ARCHIVED/SUPERSEDED | **High** | Yes |
| PUT allows arbitrary status transitions | **High** | Yes |
| No DB-level user_id isolation constraints | **High** | Yes |
| No embedding on Memory | **Medium** | Deferred to 1B |
| Scoring formula not implemented | **Medium** | Partial (1A) |
| No memory_revisions audit trail | **Medium** | Yes (minimal) |
| Document deletion → evidence cascade | **High** | Yes |
| `summary` field missing | **Low** | Yes |
| `last_accessed_at` never written | **Low** | Yes |

---

## 二、Memory Schema v2 — Design

### 2.1 Existing Fields (保留)

All existing fields are preserved. No field is removed.

### 2.2 New Fields

| Field | Type | Nullable | Default | Why | Writer | Updater | Index |
|---|---|---|---|---|---|---|---|
| `assertion_kind` | String(20) NOT NULL | NO | `"USER_STATED"` | Distinguish user-stated facts from AI-observed patterns from AI-inferred conclusions | Extraction pipeline sets; manual creation defaults to USER_STATED | User can change (correction) | (user_id, assertion_kind) |
| `summary` | Text | YES | NULL | One-line summary for UI display and quick recall | AI extraction pipeline | User can edit | — |
| `last_accessed_at` | DateTime(tz) | YES | NULL | Track when memory was last recalled in chat | RAG recall service | Updated on each recall | — |

### 2.3 Fields Modified

| Field | Change | Rationale |
|---|---|---|
| `is_confirmed` | Rename conceptually to `status`, keep column name `is_confirmed` for backward compat | Supports: PENDING, CONFIRMED, REJECTED, ARCHIVED, SUPERSEDED |
| `source` | Deprecated — kept for backward compat but new memories should use `memory_evidence` | Migration: existing `source` text becomes a single evidence record |
| `source_document_id` | Deprecated — replaced by polymorphic evidence linking | Migration: existing FK becomes an evidence record |

### 2.4 Fields Deliberately NOT Added

| Rejected Field | Why |
|---|---|
| `embedding` (vector) | Deferred to 1B. Memory embedding requires careful model selection + recall tuning. Adding it without the retrieval pipeline is dead code. |
| `semantic_score` | Part of scoring formula, computed at query time, not stored. |
| `recurrence_count` | Same as existing `frequency`. Already tracked. |
| `decay_rate` | Already tracked in `memory_strengths` table. Don't duplicate. |

### 2.5 Three Scores — Explicit Separation

| Score | Definition | Source | Stored? | Recalculated? |
|---|---|---|---|---|
| **importance** | How important is this memory to the user's life/work? | User rating + AI estimation (0.35 weight) | Yes, in `memories.importance` | On confirmation, on feedback |
| **confidence** | How confident is the system that this memory is accurate? | Evidence count × strength (0.25 weight) | Yes, in `memories.confidence` | When evidence added/removed |
| **relevance** | How relevant is this memory to the current query? | Computed at query time (embedding similarity or keyword match) | No — ephemeral | Every query |

These three MUST NOT be conflated. `confidence` is NOT `relevance`. A memory can have high confidence (well-sourced) but zero relevance to a given query.

---

## 三、MemoryEvidence — Design

### 3.1 Rationale

From docs:
> "Memory 不能只知道'是什么'，还必须知道'为什么系统认为它是真的'。"

A Memory is a claim. Evidence is the support. One claim can have multiple supports. When supports disappear, the claim must be re-evaluated.

### 3.2 Schema

```
Table: memory_evidence
──────────────────────────────────────────────────
evidence_id       UUID PK
memory_id         UUID FK → memories NOT NULL
user_id           UUID NOT NULL          -- denormalized for isolation enforcement
source_type       String(20) NOT NULL    -- CONVERSATION / DOCUMENT / DECISION / MANUAL / CORRECTION
source_id         UUID NULL              -- FK to source entity (polymorphic — see below)
source_span       Text NULL              -- quote or locator within source (e.g. "第3段", "message_id=abc")
evidence_kind     String(20) NOT NULL    -- DIRECT_QUOTE / PARAPHRASE / OBSERVATION / USER_CORRECTION
evidence_strength Float default 1.0      -- range 0-1 (DIRECT_QUOTE=1.0, OBSERVATION=0.7, etc.)
observed_at       DateTime(tz) NULL      -- when this evidence was first observed
created_at        DateTime(tz) NOT NULL

Indexes:
  (memory_id)           -- lookup all evidence for a memory
  (user_id)             -- isolation enforcement
  (source_type, source_id) -- find all evidence from a specific source entity

Constraints:
  FK(memory_id) → memories.memory_id ON DELETE CASCADE
  user_id MUST match memory.user_id (enforced by service layer + CHECK constraint)
```

### 3.3 Source Types

| source_type | source_id points to | Example |
|---|---|---|
| `CONVERSATION` | `conversation_messages.message_id` | "In message X, user said 'I prefer Python'" |
| `DOCUMENT` | `documents.document_id` | "In doc Y, section Z says 'Launch date 2031-09-17'" |
| `DECISION` | `decisions.decision_id` | "User chose Python in decision about tech stack" |
| `MANUAL` | NULL (user entered directly) | User typed "I prefer Python" in memory form |
| `CORRECTION` | `conversation_messages.message_id` | User corrected AI: "No, it's Python not Java" |

### 3.4 Polymorphic Source — Implementation

Instead of 5 separate FK columns, use a single `source_id` with `source_type` discriminator. Service layer resolves the FK at read time.

**Why NOT polymorphic FK at DB level:** PostgreSQL doesn't natively support multi-table FK. Options:

1. **Application-level validation** (chosen): Service layer ensures `source_id` references the correct table for the given `source_type`. DB has `CHECK` constraint on `source_type` values only.

2. **Separate FK columns per type**: Rejected — schema bloat, nulls everywhere.

3. **Generic FK (table_name + id)**: Rejected — breaks referential integrity.

### 3.5 Evidence Lifecycle Rules

| Event | Rule |
|---|---|
| **Source deleted (document)** | Find all evidence with `source_type=DOCUMENT, source_id=deleted_doc_id`. Remove those evidence records. If memory has 0 remaining evidence → set `status=ARCHIVED` (not delete). |
| **Source deleted (conversation)** | Find evidence with `source_type=CONVERSATION, source_id=deleted_msg_id`. Remove. Same cascade rule. |
| **Source deleted (decision)** | Find evidence with `source_type=DECISION, source_id=deleted_dec_id`. Remove. Same cascade rule. |
| **User adds evidence** | Insert record. Recalculate `confidence`. |
| **User removes evidence** | Delete record. Recalculate `confidence`. If 0 evidence → suggest archive. |
| **Multiple sources** | Each evidence is independent. More sources = higher confidence. |

### 3.6 Confidence Recalculation

When evidence changes, `confidence` is updated:

```
If evidence_count == 0: confidence = 0.0, suggest ARCHIVED
If evidence_count == 1: confidence = evidence_strength × 0.6
If evidence_count == 2: confidence = avg(evidence_strengths) × 0.8
If evidence_count >= 3: confidence = avg(evidence_strengths) × 0.95
```

The multiplier increases with evidence count (corroboration effect).

### 3.7 Cross-User Isolation

- `user_id` is denormalized on every evidence record
- Service layer ALWAYS filters by `user_id`
- DB CHECK constraint: `user_id` on `memory_evidence` must match `user_id` on the linked `memory_id` (enforced via trigger or application-level check on every write)

---

## 四、Epistemic / Assertion Kind — Design

### 4.1 Three Kinds

| Kind | Definition | Example | Confirmation Policy |
|---|---|---|---|
| `USER_STATED` | User explicitly said or wrote this | "I prefer Python" | Default for manual creation. Auto-confirmed if user typed it. |
| `OBSERVED` | System observed a pattern from user's data | "4 of your last 5 projects use Python" | Starts as CANDIDATE. Requires user confirmation. |
| `INFERRED` | AI concluded this from combining evidence | "You may prefer Python for backend development" | Starts as CANDIDATE. Lower confidence ceiling (max 0.7). Requires user confirmation. |

### 4.2 Policy Matrix

| Policy | USER_STATED | OBSERVED | INFERRED |
|---|---|---|---|
| **Initial status** | CONFIRMED (user typed it) | PENDING (candidate) | PENDING (candidate) |
| **Confidence ceiling** | 1.0 | 0.9 | 0.7 |
| **Can auto-confirm?** | Yes (manual creation) | No | No |
| **Retrieval priority** | Highest | Medium | Lowest |
| **UI badge** | "User stated" | "Observed" | "AI inference" |
| **Deletion behavior** | User deletes → hard delete | User deletes → hard delete | User deletes → hard delete + learn preference |
| **Correction behavior** | User edits → create revision | User rejects → mark rejected | User rejects → increase negative signal |

### 4.3 Extraction Pipeline Assignment

| Source | Default assertion_kind |
|---|---|
| User manually creates memory | `USER_STATED` |
| AI extracts from user's conversation message | `USER_STATED` (user said it) |
| AI extracts from AI assistant message | `OBSERVED` (AI observed from context) |
| AI pattern detection across conversations | `OBSERVED` |
| AI inference from combining multiple sources | `INFERRED` |

---

## 五、Memory Lifecycle State Machine

### 5.1 States

| State | Meaning |
|---|---|
| `PENDING` | Candidate awaiting user decision. Not used in recall. |
| `CONFIRMED` | User approved. Used in recall. Full confidence. |
| `REJECTED` | User explicitly rejected. Not used in recall. Hidden from UI. |
| `ARCHIVED` | Source evidence was removed (e.g. document deleted). Not used in recall. Preserved for audit. Can be restored if new evidence added. |
| `SUPERSEDED` | Replaced by a newer version of the same memory. Not used in recall. Audit trail preserved. |

### 5.2 State Machine

```
                    ┌──────────────────────────────────────────────────┐
                    │                                                  │
                    ▼                                                  │
              ┌──────────┐                                            │
    create →  │ PENDING  │ ──── confirm ──────→ ┌────────────┐        │
              └──────────┘                      │ CONFIRMED  │        │
                    │                           └────────────┘        │
                    │ reject          │ archive         │ supersede   │
                    ▼                 ▼                 ▼             │
              ┌──────────┐    ┌──────────┐      ┌────────────┐       │
              │ REJECTED │    │ ARCHIVED │      │ SUPERSEDED │       │
              └──────────┘    └──────────┘      └────────────┘       │
                    │                 │                                │
                    │ (no transition  │ restore (add new evidence)    │
                    │  out of this    │───────────────────────────────┘
                    │  state)         │
                    └─────────────────┘
```

### 5.3 Legal Transitions

| From | To | Trigger | Permission |
|---|---|---|---|
| (new) | PENDING | AI extraction or manual creation | System / User |
| PENDING | CONFIRMED | `POST /{id}/confirm` or `POST /confirm-all` | User only |
| PENDING | REJECTED | `POST /{id}/reject` or `POST /reject-all` | User only |
| CONFIRMED | ARCHIVED | Source evidence cascade (document deleted, no remaining evidence) | System (automatic) |
| CONFIRMED | SUPERSEDED | New memory replaces old (same topic, updated info) | System (dedup pipeline) or User |
| ARCHIVED | CONFIRMED | Add new evidence (e.g. new document supports same claim) | User only |

### 5.4 Illegal Transitions (rejected by service layer)

| From | To | Why |
|---|---|---|
| REJECTED | CONFIRMED | Must go through PENDING first (user must re-evaluate) |
| REJECTED | ARCHIVED | No evidence to remove from a rejected memory |
| SUPERSEDED | CONFIRMED | Superseded is terminal for that version; use the new version |
| ARCHIVED | REJECTED | Archived is not rejection; it's evidence removal |
| CONFIRMED | PENDING | Cannot un-confirm (use SUPERSEDED if replacing) |

### 5.5 Delete vs Archive

| Action | Delete | Archive |
|---|---|---|
| DB record | Removed from `memories` | Stays in `memories` with `status=ARCHIVED` |
| Evidence | CASCADE deleted | Evidence records removed, memory preserved |
| Audit | Lost | Preserved |
| Recall | Invisible | Invisible |
| Restore | Impossible | Possible (add evidence → CONFIRMED) |
| Use case | User explicitly wants it gone | Source removed, but claim may return |

---

## 六、Database Invariants

### 6.1 Constraints

```sql
-- 1. Memory must belong to user
ALTER TABLE memories ADD CONSTRAINT fk_memory_user
    FOREIGN KEY (user_id) REFERENCES users(user_id);

-- 2. Evidence must belong to same user as memory (service-level + trigger)
CREATE OR REPLACE FUNCTION check_evidence_user_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_id != (SELECT user_id FROM memories WHERE memory_id = NEW.memory_id) THEN
        RAISE EXCEPTION 'Evidence user_id must match memory user_id';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_evidence_user_check
    BEFORE INSERT OR UPDATE ON memory_evidence
    FOR EACH ROW EXECUTE FUNCTION check_evidence_user_match();

-- 3. Status must be valid
ALTER TABLE memories ADD CONSTRAINT chk_memory_status
    CHECK (is_confirmed IN ('PENDING', 'CONFIRMED', 'REJECTED', 'ARCHIVED', 'SUPERSEDED'));

-- 4. assertion_kind must be valid
ALTER TABLE memories ADD CONSTRAINT chk_assertion_kind
    CHECK (assertion_kind IN ('USER_STATED', 'OBSERVED', 'INFERRED'));

-- 5. source_type must be valid
ALTER TABLE memory_evidence ADD CONSTRAINT chk_evidence_source_type
    CHECK (source_type IN ('CONVERSATION', 'DOCUMENT', 'DECISION', 'MANUAL', 'CORRECTION'));

-- 6. evidence_kind must be valid
ALTER TABLE memory_evidence ADD CONSTRAINT chk_evidence_kind
    CHECK (evidence_kind IN ('DIRECT_QUOTE', 'PARAPHRASE', 'OBSERVATION', 'USER_CORRECTION'));

-- 7. Confidence range
ALTER TABLE memories ADD CONSTRAINT chk_confidence_range
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- 8. Importance range
ALTER TABLE memories ADD CONSTRAINT chk_importance_range
    CHECK (importance >= 0.0 AND importance <= 1.0);

-- 9. Evidence strength range
ALTER TABLE memory_evidence ADD CONSTRAINT chk_evidence_strength_range
    CHECK (evidence_strength >= 0.0 AND evidence_strength <= 1.0);

-- 10. Timestamps must be UTC (application-level, not DB constraint)
-- PostgreSQL TIMESTAMPTZ handles this naturally.
```

### 6.2 Indexes

```sql
-- Existing (keep)
CREATE INDEX ix_memory_user_confirmed ON memories (user_id, is_confirmed);
CREATE INDEX ix_memory_user_type ON memories (user_id, memory_type);
CREATE INDEX ix_memory_user_importance ON memories (user_id, importance);

-- New
CREATE INDEX ix_memory_assertion_kind ON memories (user_id, assertion_kind);
CREATE INDEX ix_memory_status ON memories (user_id, is_confirmed);  -- alias for readability
CREATE INDEX ix_evidence_memory ON memory_evidence (memory_id);
CREATE INDEX ix_evidence_user ON memory_evidence (user_id);
CREATE INDEX ix_evidence_source ON memory_evidence (source_type, source_id);
```

---

## 七、Migration Strategy

### 7.1 Alembic Setup

Current state: No Alembic version files exist. Tables created via `init_db()` with `create_all(checkfirst=True)`.

Step 1: Generate initial migration from current schema (`alembic revision --autogenerate`).
Step 2: Stamp it as applied (`alembic stamp head`).
Step 3: Create the Phase 1A migration.

### 7.2 Phase 1A Migration (`002_memory_foundation.py`)

```sql
-- Step 1: Add new columns to memories
ALTER TABLE memories ADD COLUMN assertion_kind VARCHAR(20) NOT NULL DEFAULT 'USER_STATED';
ALTER TABLE memories ADD COLUMN summary TEXT;

-- Step 2: Create memory_evidence table
CREATE TABLE memory_evidence (
    evidence_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id      UUID NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    user_id        UUID NOT NULL REFERENCES users(user_id),
    source_type    VARCHAR(20) NOT NULL,
    source_id      UUID,
    source_span    TEXT,
    evidence_kind  VARCHAR(20) NOT NULL DEFAULT 'DIRECT_QUOTE',
    evidence_strength FLOAT NOT NULL DEFAULT 1.0,
    observed_at    TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_evidence_memory ON memory_evidence (memory_id);
CREATE INDEX ix_evidence_user ON memory_evidence (user_id);
CREATE INDEX ix_evidence_source ON memory_evidence (source_type, source_id);

-- Step 3: Migrate existing source data → evidence records
-- For each memory with source_document_id NOT NULL:
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength)
SELECT memory_id, user_id, 'DOCUMENT', source_document_id, 'PARAPHRASE', 0.7
FROM memories WHERE source_document_id IS NOT NULL;

-- For each memory with source text but no source_document_id:
INSERT INTO memory_evidence (memory_id, user_id, source_type, source_id, evidence_kind, evidence_strength)
SELECT memory_id, user_id, 'MANUAL', NULL, 'DIRECT_QUOTE', 1.0
WHERE source IS NOT NULL AND source_document_id IS NULL;

-- Step 4: Add CHECK constraints
ALTER TABLE memories ADD CONSTRAINT chk_memory_status
    CHECK (is_confirmed IN ('PENDING', 'CONFIRMED', 'REJECTED', 'ARCHIVED', 'SUPERSEDED'));
ALTER TABLE memories ADD CONSTRAINT chk_assertion_kind
    CHECK (assertion_kind IN ('USER_STATED', 'OBSERVED', 'INFERRED'));
ALTER TABLE memory_evidence ADD CONSTRAINT chk_evidence_source_type
    CHECK (source_type IN ('CONVERSATION', 'DOCUMENT', 'DECISION', 'MANUAL', 'CORRECTION'));
ALTER TABLE memory_evidence ADD CONSTRAINT chk_evidence_kind
    CHECK (evidence_kind IN ('DIRECT_QUOTE', 'PARAPHRASE', 'OBSERVATION', 'USER_CORRECTION'));

-- Step 5: Add trigger for cross-user evidence isolation
-- (see §6.1 above)
```

### 7.3 Rollback Strategy

```sql
-- Reverse migration:
-- 1. Drop trigger
DROP TRIGGER IF EXISTS trg_evidence_user_check ON memory_evidence;
DROP FUNCTION IF EXISTS check_evidence_user_match();

-- 2. Drop evidence table (cascades to constraints)
DROP TABLE IF EXISTS memory_evidence;

-- 3. Drop new columns from memories
ALTER TABLE memories DROP COLUMN IF EXISTS assertion_kind;
ALTER TABLE memories DROP COLUMN IF EXISTS summary;

-- 4. Drop check constraints
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_memory_status;
ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_assertion_kind;

-- Existing data in memories table is UNAFFECTED by rollback.
```

### 7.4 Data Preservation

| Existing Data | Migration Action | After Migration |
|---|---|---|
| `memory.source` text | Copied to `memory_evidence` as MANUAL evidence | Column kept (deprecated), evidence table has structured record |
| `memory.source_document_id` FK | Copied to `memory_evidence` as DOCUMENT evidence | Column kept (deprecated), FK preserved |
| `memory.is_confirmed = PENDING/CONFIRMED/REJECTED` | Unchanged | Still valid values; ARCHIVED/SUPERSEDED are new additions |
| All other fields | Unchanged | — |

**No data is deleted. No existing field is removed.**

---

## 八、Backward Compatibility

### 8.1 API Compatibility

| Endpoint | Change | Breaking? |
|---|---|---|
| `POST /memory` | New optional field `assertion_kind` (default: USER_STATED) | No — additive |
| `GET /memory` | Response adds `assertion_kind`, `summary` fields | No — additive |
| `GET /memory/{id}` | Response adds `assertion_kind`, `summary` | No — additive |
| `PUT /memory/{id}` | `is_confirmed` now validates transitions (ARCHIVED, SUPERSEDED added) | **Soft breaking** — arbitrary status writes now validated |
| `POST /memory/{id}/confirm` | No change | No |
| `POST /memory/{id}/reject` | No change | No |
| `POST /memory/search` | No change | No |

**New endpoints (additive):**

| Endpoint | Purpose |
|---|---|
| `GET /memory/{id}/evidence` | List evidence for a memory |
| `POST /memory/{id}/evidence` | Add evidence to a memory |
| `DELETE /memory/{id}/evidence/{evidence_id}` | Remove evidence |
| `POST /memory/{id}/archive` | Archive a memory |
| `POST /memory/{id}/restore` | Restore archived memory |

### 8.2 Frontend Compatibility

| Component | Impact |
|---|---|
| Memory list page | Works unchanged. New fields (`assertion_kind`, `summary`) appear but don't break layout. |
| Memory detail page | Works unchanged. Can show badge for assertion_kind. |
| Confirm/reject flow | Works unchanged. ARCHIVED memories hidden from candidate list. |
| Memory search | Works unchanged. |
| Chat recall | Works unchanged. |

### 8.3 Test Compatibility

| Test | Impact |
|---|---|
| `test_create_memory` | Passes (assertion_kind defaults to USER_STATED) |
| `test_list_memories` | Passes (new fields in response) |
| `test_search_memories` | Passes (search unchanged) |
| `test_e2e_memory_candidate_flow` | Passes (confirm/reject unchanged) |
| All auth/security/isolation tests | Unaffected |

---

## 九、Phase 1A Tests — Design

### 9.1 Migration Test

```python
async def test_migration_preserves_existing_memories():
    """Pre-migration memories must survive migration with data intact."""
    # 1. Create memories with various is_confirmed values before migration
    # 2. Run migration
    # 3. Verify all memories exist with original content, type, importance
    # 4. Verify assertion_kind defaults to USER_STATED
    # 5. Verify evidence records created from source_document_id / source text
```

### 9.2 Lifecycle Tests

```python
async def test_lifecycle_pending_to_confirmed():
    """PENDING → CONFIRMED via POST /confirm"""
    memory = create_memory(status=PENDING)
    result = confirm_memory(memory.id)
    assert result.status == "CONFIRMED"

async def test_lifecycle_pending_to_rejected():
    """PENDING → REJECTED via POST /reject"""
    memory = create_memory(status=PENDING)
    result = reject_memory(memory.id)
    assert result.status == "REJECTED"

async def test_lifecycle_confirmed_to_archived():
    """CONFIRMED → ARCHIVED when last evidence removed"""
    memory = create_memory_with_evidence(count=1)
    delete_source_evidence(memory.id)
    result = get_memory(memory.id)
    assert result.status == "ARCHIVED"

async def test_lifecycle_archived_to_confirmed():
    """ARCHIVED → CONFIRMED when new evidence added"""
    memory = create_memory(status=ARCHIVED)
    add_evidence(memory.id, source_type="DOCUMENT")
    assert memory.status == "CONFIRMED"

async def test_illegal_transition_rejected_to_confirmed():
    """REJECTED → CONFIRMED must fail (no direct path)"""
    memory = create_memory(status=REJECTED)
    with pytest.raises(HTTPException, match="400"):
        confirm_memory(memory.id)  # must go through PENDING

async def test_illegal_transition_confirmed_to_pending():
    """CONFIRMED → PENDING must fail (cannot un-confirm)"""
    memory = create_memory(status=CONFIRMED)
    with pytest.raises(HTTPException, match="400"):
        update_memory(memory.id, is_confirmed="PENDING")
```

### 9.3 Evidence Tests

```python
async def test_memory_has_multiple_evidence():
    """A memory can have multiple evidence records from different sources."""
    memory = create_memory()
    add_evidence(memory.id, source_type="DOCUMENT", doc_id=doc1)
    add_evidence(memory.id, source_type="CONVERSATION", msg_id=msg1)
    evidence = list_evidence(memory.id)
    assert len(evidence) == 2

async def test_evidence_user_isolation():
    """User B cannot add evidence to User A's memory."""
    memory_a = create_memory_as_user_a()
    with pytest.raises(HTTPException, match="403"):
        add_evidence_as_user_b(memory_a.id)

async def test_evidence_cascade_on_document_delete():
    """Deleting a document removes its evidence; memory archives if no evidence remains."""
    memory = create_memory_with_document_evidence(doc_id)
    delete_document(doc_id)
    evidence = list_evidence(memory.id)
    assert len(evidence) == 0
    memory = get_memory(memory.id)
    assert memory.status == "ARCHIVED"

async def test_evidence_cascade_preserves_memory_with_other_evidence():
    """Deleting a document removes its evidence but memory stays CONFIRMED if other evidence exists."""
    memory = create_memory_with_two_evidence(doc_id_1, doc_id_2)
    delete_document(doc_id_1)
    evidence = list_evidence(memory.id)
    assert len(evidence) == 1
    memory = get_memory(memory.id)
    assert memory.status == "CONFIRMED"

async def test_provenance_traceable():
    """From a memory, you can trace back to its source documents/conversations."""
    memory = create_memory_with_document_evidence(doc_id)
    evidence = list_evidence(memory.id)
    assert evidence[0].source_type == "DOCUMENT"
    assert evidence[0].source_id == doc_id
```

### 9.4 Regression Test (Must PASS)

```python
async def test_memory_baseline_regression():
    """Phase 0 baseline: create preference → confirm → chat recall → answer contains Python."""
    # This is the EXISTING test_e2e_memory_candidate_flow.
    # It MUST continue to pass without modification.
    mem = create_memory(content="I prefer Python", type="PREFERENCE", importance=0.9)
    confirm_memory(mem.id)
    chat = send_chat("What programming language do I prefer?", memory_enabled=True)
    assert "Python" in chat.answer
```

---

## 十、NOT IN SCOPE

Phase 1A will NOT implement:

| Excluded | Deferred To |
|---|---|
| Semantic Memory retrieval (embedding on Memory) | 1B |
| Advanced embedding retrieval | 1B |
| LLM deduplication (AI-based) | 1C |
| Contradiction detection | 1C |
| Automatic revision / superseding | 1C |
| Reflection (offline clustering, conflict detection) | 1D |
| Belief evolution enhancements | 1D |
| Prediction / proactive AI | 1E |
| Agent / autonomous action | 1E |
| Knowledge graph enhancements | 1F |
| Memory Graph (visual) | 1F |
| New dashboard | 1F |
| New Cognitive Engine | 1G |
| Memory Engine 2.0 full implementation | 1G |
| Major UI redesign | 1F |
| `memory_strengths` / `memory_associations` / `memory_clusters` changes | Deferred |

---

## 十一、Proposed Architecture (Phase 1A After Completion)

```
User
  │
  ├── Memory (with assertion_kind, summary, last_accessed_at)
  │     │
  │     ├── MemoryEvidence[0..N]
  │     │     ├── source_type = DOCUMENT → Document
  │     │     ├── source_type = CONVERSATION → ConversationMessage
  │     │     ├── source_type = DECISION → Decision
  │     │     ├── source_type = MANUAL → (no FK)
  │     │     └── source_type = CORRECTION → ConversationMessage
  │     │
  │     └── status lifecycle:
  │           PENDING → CONFIRMED / REJECTED
  │           CONFIRMED → ARCHIVED (evidence cascade)
  │           ARCHIVED → CONFIRMED (new evidence)
  │
  ├── Belief (existing, no changes in 1A)
  └── Decision (existing, no changes in 1A)
```

### Layer Responsibilities

| Layer | Responsibility |
|---|---|
| **API Router** | Request parsing, auth, response serialization. No business logic. |
| **Service** | Lifecycle transitions, evidence cascade, confidence recalculation, user isolation checks. |
| **Repository** (optional) | If query complexity warrants it. Otherwise, service calls ORM directly. |
| **Database** | CHECK constraints, FK constraints, trigger for cross-user isolation, indexes. |

**No new Manager / Engine / Analyzer abstractions in 1A.** The existing `MemoryService` handles memory CRUD. Evidence operations are added to the same service. If evidence cascade logic grows complex, it can be extracted to `EvidenceService` — but only if the function exceeds ~200 lines or is independently testable.

---

## 十二、Implementation Plan

### 12.1 Files to Modify

| File | Changes |
|---|---|
| `app/models/memory.py` | Add `assertion_kind`, `summary` columns. Update `is_confirmed` CHECK. |
| `app/models/__init__.py` | Import `MemoryEvidence` model. |
| `app/schemas/memory.py` | Add `assertion_kind`, `summary` to create/update/response schemas. |
| `app/api/memory.py` | Add status transition validation. Add evidence endpoints. Add archive/restore. |
| `app/services/memory_service.py` | (New file — or extend existing service logic in `api/memory.py`). Evidence cascade logic. Confidence recalculation. |
| `app/services/rag_service.py` | Update `last_accessed_at` on recall. Filter ARCHIVED/SUPERSEDED from recall. |
| `app/services/memory_extractor.py` | Set `assertion_kind` during extraction. Set `source_type` correctly. |
| `app/services/document_service.py` | On document delete: trigger evidence cascade → archive if no evidence. |
| `tests/test_memory.py` | Add lifecycle, evidence, isolation, regression tests. |
| `tests/test_e2e.py` | Verify baseline regression still passes. |

### 12.2 Files to Add

| File | Purpose |
|---|---|
| `app/models/evidence.py` | `MemoryEvidence` SQLAlchemy model. |
| `alembic/versions/002_memory_foundation.py` | Alembic migration for new columns + evidence table + constraints. |
| `tests/test_memory_lifecycle.py` | Dedicated lifecycle transition tests. |
| `tests/test_memory_evidence.py` | Dedicated evidence CRUD + cascade tests. |

### 12.3 Alembic Migration

See §7.2 for full SQL.

1. Generate baseline migration from current schema
2. Create `002_memory_foundation.py`:
   - Add `assertion_kind`, `summary` to `memories`
   - Create `memory_evidence` table
   - Migrate existing `source` / `source_document_id` → evidence records
   - Add CHECK constraints
   - Add trigger for cross-user isolation

### 12.4 Tests

| Test File | Tests |
|---|---|
| `test_memory_lifecycle.py` | 6 tests: legal transitions, illegal transitions, delete vs archive |
| `test_memory_evidence.py` | 5 tests: CRUD, user isolation, cascade on delete, provenance traceable |
| `test_memory.py` (existing) | 3 existing tests — must pass unchanged |
| `test_e2e.py` | 1 regression test — must pass unchanged |

### 12.5 Implementation Order

```
1. Models (MemoryEvidence + Memory updates)
2. Alembic setup (generate baseline + Phase 1A migration)
3. Evidence CRUD API + tests
4. Lifecycle transition validation + tests
5. Document delete → evidence cascade
6. RAG service: last_accessed_at + filter archived
7. Memory extractor: set assertion_kind + source_type
8. Full regression test suite
9. Documentation update
```

### 12.6 Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Migration breaks existing data | **High** | Test on copy of production DB first. Rollback script tested. No field removed. |
| Evidence cascade triggers on every document delete (perf) | **Medium** | Evidence table indexed on (source_type, source_id). Cascade is O(evidence_count) not O(memory_count). |
| Frontend breaks on new response fields | **Low** | New fields are additive. Old fields preserved. Frontend uses Optional types. |
| SQLite tests can't validate PostgreSQL triggers | **Medium** | Trigger is PostgreSQL-only. SQLite tests validate service-level isolation. CI tests validate DB-level. |
| Cross-user isolation trigger may slow writes | **Low** | Single-row lookup per INSERT. Negligible on modern hardware. |

### 12.7 Acceptance Criteria

Phase 1A is ACCEPTED when:

1. **Migration**: All existing memories survive migration. Evidence records created from source data.
2. **Lifecycle**: All legal transitions succeed. All illegal transitions are rejected with 400.
3. **Evidence**: Memory can have multiple evidence records. User isolation enforced at DB level.
4. **Cascade**: Document delete → evidence removed → memory archives if no evidence remains. Memory stays CONFIRMED if other evidence exists.
5. **Provenance**: From any memory, trace back to source document/conversation/decision.
6. **Regression**: `I prefer Python → confirm → chat → answer contains Python` PASSES.
7. **Existing tests**: All 56+ existing tests PASS without modification.
8. **No scope creep**: No embedding, no AI dedup, no reflection, no new dashboard.

---

*End of Phase 1A Design Proposal. Awaiting External Review.*
