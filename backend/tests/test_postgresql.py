"""
Personal AI OS - PostgreSQL Integration Tests
PostgreSQL 集成测试 — 真实连接 PostgreSQL + pgvector
"""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def poll_until(condition_fn, timeout_seconds=30, interval=0.5):
    """Bounded polling helper: 轮询直到条件满足或超时"""
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
    response = await client.post("/api/v1/auth/login", json={
        "email": "pg_test@test.com",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_conversation_create_and_delete(client, auth_headers):
    """测试对话创建和删除"""
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

    # 验证对话已删除（消息应为空）
    messages_response = await client.get(
        f"/api/v1/ai/conversations/{conversation_id}",
        headers=auth_headers
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) == 0


@pytest.mark.asyncio
async def test_document_upload_and_processing(client, auth_headers):
    """测试文档上传和处理 — 必须等到 COMPLETED"""
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

    # Bounded polling: 等待文档处理完成
    async def check_document_status():
        doc_response = await client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers
        )
        if doc_response.status_code == 200:
            doc_json = doc_response.json()
            status = doc_json.get("status", "")
            if status == "COMPLETED":
                return doc_json
            elif status == "FAILED":
                error_msg = doc_json.get("status_message", "Unknown error")
                pytest.fail(f"Document processing FAILED: {error_msg}")
        return None

    doc_data = await poll_until(check_document_status, timeout_seconds=60, interval=1.0)

    # 断言：必须是 COMPLETED
    assert doc_data is not None, "Document processing timed out - status never reached COMPLETED"
    assert doc_data["status"] == "COMPLETED", f"Expected COMPLETED, got {doc_data['status']}"

    # 验证 chunk_count > 0
    chunks_response = await client.get(
        f"/api/v1/knowledge/chunks/{document_id}",
        headers=auth_headers
    )
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) > 0, "No chunks created after document processing"

    # 验证搜索能召回
    search_response = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "2031"},
        headers=auth_headers,
        timeout=30
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data["total"] > 0, "Knowledge search returned no results"

    # 验证搜索结果包含正确 document_id
    found_doc = False
    for item in search_data["items"]:
        if item["document_id"] == document_id:
            found_doc = True
            break
    assert found_doc, "Search results do not contain the uploaded document"

    # 验证 AI 问答（检查是否基于知识库回答）
    chat_response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "What is the Project Aurora launch date?", "memory_enabled": False},
        headers=auth_headers,
        timeout=60
    )
    assert chat_response.status_code == 200
    answer = chat_response.json()["answer"]
    # AI 应该基于知识库回答，即使没有精确匹配也应引用来源
    sources = chat_response.json().get("sources", [])
    assert len(sources) > 0 or "2031" in answer, f"Answer neither contains '2031' nor has sources: {answer[:200]}"


@pytest.mark.asyncio
async def test_memory_lifecycle(client, auth_headers):
    """测试记忆生命周期"""
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
    """测试观点生命周期"""
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
    """测试决策生命周期"""
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
