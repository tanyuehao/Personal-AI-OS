"""
Personal AI OS - Cross-user Isolation Tests
跨用户数据隔离测试 — BLOCKER
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def user_a(client):
    """User A - 创建数据的用户"""
    await client.post("/api/v1/auth/register", json={
        "username": "user_a_iso", "email": "user_a_iso@test.com", "password": "pass_a123"
    })
    r = await client.post("/api/v1/auth/login", json={"email": "user_a_iso@test.com", "password": "pass_a123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def user_b(client):
    """User B - 尝试访问 User A 数据的用户"""
    await client.post("/api/v1/auth/register", json={
        "username": "user_b_iso", "email": "user_b_iso@test.com", "password": "pass_b123"
    })
    r = await client.post("/api/v1/auth/login", json={"email": "user_b_iso@test.com", "password": "pass_b123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ========== Document Isolation ==========

@pytest.mark.asyncio
async def test_document_isolation_get(client, user_a, user_b):
    """User B 无法 GET User A 的文档"""
    # User A 创建文档
    files = {"file": ("private.txt", b"A's private document", "text/plain")}
    r = await client.post("/api/v1/documents/upload", files=files, headers=user_a, timeout=30)
    assert r.status_code == 201
    doc_id = r.json()["document_id"]

    # User B 尝试获取
    r = await client.get(f"/api/v1/documents/{doc_id}", headers=user_b)
    assert r.status_code == 404, f"User B should not access User A's document, got {r.status_code}"

    # User B 尝试下载
    r = await client.get(f"/api/v1/documents/{doc_id}/download", headers=user_b)
    assert r.status_code == 404, f"User B should not download User A's document"

    # User B 尝试删除
    r = await client.delete(f"/api/v1/documents/{doc_id}", headers=user_b)
    assert r.status_code == 404, f"User B should not delete User A's document"


@pytest.mark.asyncio
async def test_knowledge_search_isolation(client, user_a, user_b):
    """Knowledge search 不返回 User A 的 chunk"""
    # User A 上传文档
    files = {"file": ("search_test.txt", b"Unique keyword: AURORA_KEYWORD_12345", "text/plain")}
    r = await client.post("/api/v1/documents/upload", files=files, headers=user_a, timeout=30)
    assert r.status_code == 201

    # User B 搜索
    r = await client.post("/api/v1/knowledge/search", json={"query": "AURORA_KEYWORD_12345"}, headers=user_b, timeout=30)
    assert r.status_code == 200
    assert r.json()["total"] == 0, "User B should not find User A's chunks"


# ========== Memory Isolation ==========

@pytest.mark.asyncio
async def test_memory_isolation(client, user_a, user_b):
    """User B 无法访问 User A 的记忆"""
    # User A 创建记忆
    r = await client.post("/api/v1/memory", json={"content": "A's private memory", "memory_type": "FACT"}, headers=user_a)
    mem_id = r.json()["memory_id"]

    # User B 尝试获取
    r = await client.get(f"/api/v1/memory/{mem_id}", headers=user_b)
    assert r.status_code == 404

    # User B 尝试删除
    r = await client.delete(f"/api/v1/memory/{mem_id}", headers=user_b)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_memory_search_isolation(client, user_a, user_b):
    """Memory search 不返回 User A 的记忆"""
    await client.post("/api/v1/memory", json={"content": "AURORA_MEMORY_KEYWORD_99999", "memory_type": "FACT"}, headers=user_a)

    r = await client.post("/api/v1/memory/search", json={"query": "AURORA_MEMORY_KEYWORD_99999"}, headers=user_b)
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ========== Belief Isolation ==========

@pytest.mark.asyncio
async def test_belief_isolation(client, user_a, user_b):
    """User B 无法访问 User A 的观点"""
    r = await client.post("/api/v1/cognitive/beliefs", json={"topic": "Private", "content": "A's belief"}, headers=user_a)
    belief_id = r.json()["belief_id"]

    r = await client.get(f"/api/v1/cognitive/beliefs/{belief_id}", headers=user_b)
    assert r.status_code == 404

    r = await client.delete(f"/api/v1/cognitive/beliefs/{belief_id}", headers=user_b)
    assert r.status_code == 404


# ========== Decision Isolation ==========

@pytest.mark.asyncio
async def test_decision_isolation(client, user_a, user_b):
    """User B 无法访问 User A 的决策"""
    r = await client.post("/api/v1/decision", json={"problem": "A's private decision"}, headers=user_a)
    dec_id = r.json()["decision_id"]

    r = await client.get(f"/api/v1/decision/{dec_id}", headers=user_b)
    assert r.status_code == 404

    r = await client.delete(f"/api/v1/decision/{dec_id}", headers=user_b)
    assert r.status_code == 404


# ========== Conversation Isolation ==========

@pytest.mark.asyncio
async def test_conversation_isolation(client, user_a, user_b):
    """User B 无法访问 User A 的对话"""
    r = await client.post("/api/v1/ai/chat", json={"message": "A's private chat"}, headers=user_a, timeout=60)
    conv_id = r.json()["conversation_id"]

    # User B 尝试获取对话消息
    r = await client.get(f"/api/v1/ai/conversations/{conv_id}", headers=user_b)
    assert r.status_code == 200
    assert len(r.json()) == 0, "User B should not see User A's messages"

    # User B 尝试删除对话
    r = await client.delete(f"/api/v1/ai/conversations/{conv_id}", headers=user_b)
    assert r.status_code == 404


# ========== Export Isolation ==========

@pytest.mark.asyncio
async def test_export_isolation(client, user_a, user_b):
    """User B 导出的数据不包含 User A 的数据"""
    await client.post("/api/v1/memory", json={"content": "A's export data", "memory_type": "FACT"}, headers=user_a)

    r = await client.get("/api/v1/export/stats", headers=user_b)
    assert r.status_code == 200
    assert r.json()["memories"] == 0, "User B's export should not contain User A's memories"
