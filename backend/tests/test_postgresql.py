"""
Personal AI OS - PostgreSQL Integration Tests
PostgreSQL 集成测试
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
async def auth_headers(client):
    """获取认证 headers"""
    await client.post("/api/v1/auth/register", json={
        "username": "pg_test_user",
        "email": "pg_test@test.com",
        "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "pg_test@test.com",
        "password": "testpass123"
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    # 如果注册失败，尝试登录
    response = await client.post("/api/v1/auth/login", json={
        "email": "pg_test@test.com",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_conversation_create_and_delete(client, auth_headers):
    """测试对话创建和删除（PostgreSQL 兼容）"""
    # 创建对话
    chat_response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Test message for delete", "memory_enabled": False},
        headers=auth_headers,
        timeout=60
    )
    assert chat_response.status_code == 200
    conversation_id = chat_response.json()["conversation_id"]

    # 验证对话存在
    messages_response = await client.get(
        f"/api/v1/ai/conversations/{conversation_id}",
        headers=auth_headers
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) > 0

    # 删除对话
    delete_response = await client.delete(
        f"/api/v1/ai/conversations/{conversation_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204

    # 验证对话已删除
    messages_response = await client.get(
        f"/api/v1/ai/conversations/{conversation_id}",
        headers=auth_headers
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) == 0


@pytest.mark.asyncio
async def test_document_upload_and_search(client, auth_headers):
    """测试文档上传和搜索（PostgreSQL 兼容）"""
    # 上传文档
    content = b"Project Aurora launch date is 2031-09-17."
    files = {"file": ("test_aurora.txt", content, "text/plain")}

    upload_response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers,
        timeout=30
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["document_id"]

    # 等待处理
    import asyncio
    await asyncio.sleep(10)

    # 验证文档状态
    doc_response = await client.get(
        f"/api/v1/documents/{document_id}",
        headers=auth_headers
    )
    assert doc_response.status_code == 200
    doc_data = doc_response.json()
    # 文档应该在处理中或已完成
    assert doc_data["status"] in ["UPLOADING", "PROCESSING", "COMPLETED"]

    # 如果文档已处理完成，测试搜索
    if doc_data["status"] == "COMPLETED":
        search_response = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "launch date 2031"},
            headers=auth_headers,
            timeout=30
        )
        assert search_response.status_code == 200


@pytest.mark.asyncio
async def test_memory_lifecycle(client, auth_headers):
    """测试记忆生命周期（PostgreSQL 兼容）"""
    # 创建记忆
    create_response = await client.post(
        "/api/v1/memory",
        json={
            "content": "Test memory for PostgreSQL",
            "memory_type": "FACT",
            "importance": 0.8
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    memory_id = create_response.json()["memory_id"]
    assert create_response.json()["is_confirmed"] == "PENDING"

    # 确认记忆
    confirm_response = await client.post(
        f"/api/v1/memory/{memory_id}/confirm",
        headers=auth_headers
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["is_confirmed"] == "CONFIRMED"

    # 删除记忆
    delete_response = await client.delete(
        f"/api/v1/memory/{memory_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_belief_lifecycle(client, auth_headers):
    """测试观点生命周期（PostgreSQL 兼容）"""
    # 创建观点
    create_response = await client.post(
        "/api/v1/cognitive/beliefs",
        json={
            "topic": "PostgreSQL Test",
            "content": "PostgreSQL is reliable",
            "confidence": 0.9
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    belief_id = create_response.json()["belief_id"]

    # 获取观点
    get_response = await client.get(
        f"/api/v1/cognitive/beliefs/{belief_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["content"] == "PostgreSQL is reliable"

    # 删除观点
    delete_response = await client.delete(
        f"/api/v1/cognitive/beliefs/{belief_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_decision_lifecycle(client, auth_headers):
    """测试决策生命周期（PostgreSQL 兼容）"""
    # 创建决策
    create_response = await client.post(
        "/api/v1/decision",
        json={
            "problem": "PostgreSQL adoption",
            "choice": "Use PostgreSQL",
            "reasoning": "Better for production"
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    decision_id = create_response.json()["decision_id"]

    # 获取决策
    get_response = await client.get(
        f"/api/v1/decision/{decision_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["choice"] == "Use PostgreSQL"

    # 删除决策
    delete_response = await client.delete(
        f"/api/v1/decision/{decision_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204
