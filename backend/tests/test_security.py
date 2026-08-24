"""
Personal AI OS - Security Tests
安全测试
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
async def user_a_headers(client):
    """User A credentials"""
    await client.post("/api/v1/auth/register", json={
        "username": "user_a", "email": "user_a@test.com", "password": "pass_a123"
    })
    r = await client.post("/api/v1/auth/login", json={"email": "user_a@test.com", "password": "pass_a123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def user_b_headers(client):
    """User B credentials"""
    await client.post("/api/v1/auth/register", json={
        "username": "user_b", "email": "user_b@test.com", "password": "pass_b123"
    })
    r = await client.post("/api/v1/auth/login", json={"email": "user_b@test.com", "password": "pass_b123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """测试未授权访问"""
    endpoints = ["/api/v1/documents", "/api/v1/memory", "/api/v1/settings"]
    for ep in endpoints:
        r = await client.get(ep)
        assert r.status_code in [401, 403], f"{ep} should require auth"


@pytest.mark.asyncio
async def test_invalid_token(client):
    """测试无效 token"""
    headers = {"Authorization": "Bearer invalid-token"}
    r = await client.get("/api/v1/memory", headers=headers)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_cross_user_memory_isolation(client, user_a_headers, user_b_headers):
    """测试跨用户记忆隔离"""
    # User A 创建记忆
    r = await client.post("/api/v1/memory", json={"content": "A's private memory", "memory_type": "FACT"}, headers=user_a_headers)
    mem_id = r.json()["memory_id"]

    # User B 尝试访问
    r = await client.get(f"/api/v1/memory/{mem_id}", headers=user_b_headers)
    assert r.status_code == 404, "User B should not access User A's memory"

    # User B 尝试删除
    r = await client.delete(f"/api/v1/memory/{mem_id}", headers=user_b_headers)
    assert r.status_code == 404, "User B should not delete User A's memory"


@pytest.mark.asyncio
async def test_cross_user_belief_isolation(client, user_a_headers, user_b_headers):
    """测试跨用户观点隔离"""
    r = await client.post("/api/v1/cognitive/beliefs", json={"topic": "Private", "content": "A's belief"}, headers=user_a_headers)
    belief_id = r.json()["belief_id"]

    r = await client.get(f"/api/v1/cognitive/beliefs/{belief_id}", headers=user_b_headers)
    assert r.status_code == 404

    r = await client.delete(f"/api/v1/cognitive/beliefs/{belief_id}", headers=user_b_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_decision_isolation(client, user_a_headers, user_b_headers):
    """测试跨用户决策隔离"""
    r = await client.post("/api/v1/decision", json={"problem": "Private decision"}, headers=user_a_headers)
    dec_id = r.json()["decision_id"]

    r = await client.get(f"/api/v1/decision/{dec_id}", headers=user_b_headers)
    assert r.status_code == 404

    r = await client.delete(f"/api/v1/decision/{dec_id}", headers=user_b_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_conversation_isolation(client, user_a_headers, user_b_headers):
    """测试跨用户对话隔离"""
    r = await client.post("/api/v1/ai/chat", json={"message": "Private chat", "memory_enabled": False}, headers=user_a_headers, timeout=60)
    if r.status_code == 200:
        conv_id = r.json().get("conversation_id")
        if conv_id:
            r = await client.get(f"/api/v1/ai/conversations/{conv_id}", headers=user_b_headers)
            assert r.status_code == 200
            assert len(r.json()) == 0, "User B should not see User A's messages"


@pytest.mark.asyncio
async def test_sql_injection_prevention(client, user_a_headers):
    """测试 SQL 注入防护"""
    payloads = ["'; DROP TABLE users; --", "1' OR '1'='1", "admin'--"]
    for payload in payloads:
        r = await client.post("/api/v1/memory/search", json={"query": payload}, headers=user_a_headers)
        assert r.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_rate_limiting(client):
    """测试速率限制"""
    r = await client.get("/api/v1/usage/limits")
    assert r.status_code == 200
    data = r.json()
    assert "rpm_limit" in data
    assert "tpm_limit" in data


@pytest.mark.asyncio
async def test_api_key_not_exposed(client, user_a_headers):
    """测试 API Key 不暴露"""
    r = await client.get("/api/v1/settings", headers=user_a_headers)
    assert r.status_code == 200
    data = r.json()
    # API Key 应该被加密存储
    sf_key = data.get("siliconflow_api_key", "")
    if sf_key:
        assert "****" in sf_key or len(sf_key) < 10
