"""
Personal AI OS - PostgreSQL Integration Tests
PostgreSQL 集成测试 — canonical integration test

运行条件: DATABASE_URL 必须是 postgresql+asyncpg://
SQLite 环境跳过（无 pgvector，无法验证向量搜索召回）
"""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


def _is_postgresql():
    return "postgresql" in settings.DATABASE_URL


async def poll_until(condition_fn, timeout_seconds=30, interval=0.5):
    """Bounded polling helper"""
    elapsed = 0
    while elapsed < timeout_seconds:
        result = await condition_fn()
        if result:
            return result
        await asyncio.sleep(interval)
        elapsed += interval
    return None


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    await client.post("/api/v1/auth/register", json={
        "username": "pg_test_user", "email": "pg_test@test.com", "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "pg_test@test.com", "password": "testpass123"
    })
    if response.status_code == 200:
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    response = await client.post("/api/v1/auth/login", json={
        "email": "pg_test@test.com", "password": "testpass123"
    })
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_conversation_create_and_delete(client, auth_headers):
    """测试对话创建和删除"""
    chat_response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Test message", "memory_enabled": False},
        headers=auth_headers, timeout=60
    )
    assert chat_response.status_code == 200
    conversation_id = chat_response.json()["conversation_id"]

    messages_response = await client.get(
        f"/api/v1/ai/conversations/{conversation_id}", headers=auth_headers
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) > 0

    delete_response = await client.delete(
        f"/api/v1/ai/conversations/{conversation_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    messages_response = await client.get(
        f"/api/v1/ai/conversations/{conversation_id}", headers=auth_headers
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) == 0


@pytest.mark.asyncio
@pytest.mark.skipif(not _is_postgresql(), reason="Requires PostgreSQL + pgvector")
async def test_aurora_rag_strict(client, auth_headers):
    """
    Aurora RAG canonical test — PostgreSQL + pgvector only

    上传文档 → 处理 → chunk 验证 → 检索验证 → AI 问答 → citation 验证
    所有断言必须通过，不允许 fallback 或放宽。
    """
    # 1. 上传文档
    content = b"Project Aurora launch date is 2031-09-17."
    files = {"file": ("test_aurora.txt", content, "text/plain")}
    upload_r = await client.post(
        "/api/v1/documents/upload", files=files, headers=auth_headers, timeout=30
    )
    assert upload_r.status_code == 201
    document_id = upload_r.json()["document_id"]

    # 2. 等待处理完成
    async def check_doc():
        r = await client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
        if r.status_code == 200:
            d = r.json()
            if d["status"] == "COMPLETED": return d
            if d["status"] == "FAILED": pytest.fail(f"Doc processing FAILED: {d.get('status_message')}")
        return None

    doc_data = await poll_until(check_doc, timeout_seconds=60)
    assert doc_data is not None, "Document processing timed out — never reached COMPLETED"
    assert doc_data["status"] == "COMPLETED"

    # 3. 验证 chunk：至少 1 个 chunk，包含 2031-09-17
    chunks_r = await client.get(f"/api/v1/knowledge/chunks/{document_id}", headers=auth_headers)
    assert chunks_r.status_code == 200
    chunks = chunks_r.json()
    assert len(chunks) >= 1, "Must have at least 1 chunk after processing"
    assert any("2031-09-17" in c["content"] for c in chunks), \
        "At least one chunk must contain '2031-09-17'"

    # 4. 验证检索：搜索结果必须包含该 document_id + 正确 content
    search_r = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "2031-09-17"},
        headers=auth_headers, timeout=30
    )
    assert search_r.status_code == 200
    search_data = search_r.json()
    assert search_data["total"] >= 1, "Knowledge search must return at least 1 result"

    matched = [item for item in search_data["items"] if item["document_id"] == document_id]
    assert len(matched) >= 1, \
        f"Search results must include uploaded document_id={document_id}"
    assert any("2031" in item["content"] for item in matched), \
        "Matched chunk must contain '2031'"

    # 5. AI 问答：answer 必须包含 2031-09-17，sources 必须包含该 document_id
    chat_r = await client.post(
        "/api/v1/ai/chat",
        json={"message": "What is the Project Aurora launch date?", "memory_enabled": False},
        headers=auth_headers, timeout=60
    )
    assert chat_r.status_code == 200, f"Chat failed: {chat_r.text[:300]}"
    chat_data = chat_r.json()

    # 5a. answer 必须包含 2031-09-17
    answer = chat_data["answer"]
    assert "2031-09-17" in answer, \
        f"Answer must contain '2031-09-17', got: {answer[:200]}"

    # 5b. sources 非空
    sources = chat_data["sources"]
    assert len(sources) >= 1, "Chat response must have at least 1 source/citation"

    # 5c. 至少一条 source 指向 uploaded document_id
    cited_doc_ids = [s["document_id"] for s in sources]
    assert document_id in cited_doc_ids, \
        f"At least one source must cite document_id={document_id}, got: {cited_doc_ids}"

    # 5d. cited source 的 content 必须包含 2031
    cited = [s for s in sources if s["document_id"] == document_id]
    assert any("2031" in s["content"] for s in cited), \
        "Cited source content must contain '2031'"


@pytest.mark.asyncio
async def test_memory_lifecycle(client, auth_headers):
    """测试记忆生命周期 — Phase 1A: manual create goes directly to CONFIRMED"""
    create_r = await client.post("/api/v1/memory",
        json={"content": "Test memory", "memory_type": "FACT", "importance": 0.8},
        headers=auth_headers
    )
    assert create_r.status_code == 201
    memory_id = create_r.json()["memory_id"]
    # Phase 1A: manual creation is USER_STATED + CONFIRMED (not PENDING)
    assert create_r.json()["is_confirmed"] == "CONFIRMED"
    assert create_r.json()["assertion_kind"] == "USER_STATED"

    # Confirm is idempotent on CONFIRMED
    confirm_r = await client.post(f"/api/v1/memory/{memory_id}/confirm", headers=auth_headers)
    assert confirm_r.status_code == 200
    assert confirm_r.json()["is_confirmed"] == "CONFIRMED"

    # Verify evidence was atomically created
    ev_r = await client.get(f"/api/v1/memory/{memory_id}/evidence", headers=auth_headers)
    assert ev_r.status_code == 200
    assert len(ev_r.json()) >= 1
    assert ev_r.json()[0]["source_type"] == "MANUAL"

    delete_r = await client.delete(f"/api/v1/memory/{memory_id}", headers=auth_headers)
    assert delete_r.status_code == 204


@pytest.mark.asyncio
async def test_belief_lifecycle(client, auth_headers):
    """测试观点生命周期"""
    create_r = await client.post("/api/v1/cognitive/beliefs",
        json={"topic": "Test", "content": "Test belief", "confidence": 0.9},
        headers=auth_headers
    )
    assert create_r.status_code == 201
    belief_id = create_r.json()["belief_id"]

    get_r = await client.get(f"/api/v1/cognitive/beliefs/{belief_id}", headers=auth_headers)
    assert get_r.status_code == 200

    delete_r = await client.delete(f"/api/v1/cognitive/beliefs/{belief_id}", headers=auth_headers)
    assert delete_r.status_code == 204


@pytest.mark.asyncio
async def test_decision_lifecycle(client, auth_headers):
    """测试决策生命周期"""
    create_r = await client.post("/api/v1/decision",
        json={"problem": "Test", "choice": "Option A", "reasoning": "Good"},
        headers=auth_headers
    )
    assert create_r.status_code == 201
    dec_id = create_r.json()["decision_id"]

    get_r = await client.get(f"/api/v1/decision/{dec_id}", headers=auth_headers)
    assert get_r.status_code == 200

    delete_r = await client.delete(f"/api/v1/decision/{dec_id}", headers=auth_headers)
    assert delete_r.status_code == 204
