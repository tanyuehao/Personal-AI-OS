"""
Personal AI OS - E2E Tests
端到端测试
"""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


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
        "username": "e2e_user",
        "email": "e2e@test.com",
        "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "e2e@test.com",
        "password": "testpass123"
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    response = await client.post("/api/v1/auth/login", json={
        "email": "e2e@test.com",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_e2e_document_to_qa(client, auth_headers):
    """
    E2E-01: 上传文档 -> 等待处理 -> 提问 -> 回答包含引用
    """
    # 上传文档
    content = b"Project Aurora launch date is 2031-09-17. The project aims to revolutionize space exploration."
    files = {"file": ("e2e_test.txt", content, "text/plain")}

    upload_response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers,
        timeout=30
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["document_id"]

    # 等待处理完成
    async def check_doc():
        doc = await client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
        if doc.status_code == 200:
            status = doc.json().get("status", "")
            if status == "COMPLETED":
                return doc.json()
            elif status == "FAILED":
                pytest.fail(f"Document processing failed: {doc.json().get('status_message')}")
        return None

    doc_data = await poll_until(check_doc, timeout_seconds=60)
    assert doc_data is not None, "Document processing timed out"
    assert doc_data["status"] == "COMPLETED"

    # 验证 chunks
    chunks = await client.get(f"/api/v1/knowledge/chunks/{document_id}", headers=auth_headers)
    assert chunks.status_code == 200
    assert len(chunks.json()) > 0

    # 搜索
    search = await client.post("/api/v1/knowledge/search", json={"query": "2031"}, headers=auth_headers, timeout=30)
    assert search.status_code == 200
    assert search.json()["total"] > 0

    # AI 问答（验证 RAG 流程完整）
    chat = await client.post("/api/v1/ai/chat", json={"message": "What is the launch date?", "memory_enabled": False}, headers=auth_headers, timeout=60)
    assert chat.status_code == 200
    chat_data = chat.json()
    assert "answer" in chat_data
    assert "conversation_id" in chat_data
    assert chat_data["answer"], "answer must not be empty"


@pytest.mark.asyncio
async def test_e2e_memory_candidate_flow(client, auth_headers):
    """
    E2E-02: 用户表达偏好 -> 生成候选记忆 -> 用户确认 -> 新会话召回并回答包含 Python

    这是 Memory baseline test：创建并确认偏好后，提问必须得到包含正确答案的回复。
    """
    # 1. 创建记忆
    mem = await client.post(
        "/api/v1/memory",
        json={"content": "I prefer Python", "memory_type": "PREFERENCE", "importance": 0.9},
        headers=auth_headers
    )
    assert mem.status_code == 201
    mem_id = mem.json()["memory_id"]

    # 2. 确认记忆（PENDING → CONFIRMED）
    confirm = await client.post(f"/api/v1/memory/{mem_id}/confirm", headers=auth_headers)
    assert confirm.status_code == 200
    assert confirm.json()["is_confirmed"] == "CONFIRMED"

    # 3. 验证记忆列表中存在
    mem_list = await client.get("/api/v1/memory", headers=auth_headers)
    assert mem_list.status_code == 200
    items = mem_list.json()["items"]
    confirmed = [m for m in items if m.get("is_confirmed") == "CONFIRMED"]
    assert any("Python" in m["content"] for m in confirmed), \
        "Confirmed memory containing 'Python' must appear in list"

    # 4. 新会话提问 — 回答必须包含 Python
    chat = await client.post(
        "/api/v1/ai/chat",
        json={"message": "What programming language do I prefer?", "memory_enabled": True},
        headers=auth_headers, timeout=60
    )
    assert chat.status_code == 200, f"Chat failed: {chat.text[:300]}"
    chat_data = chat.json()

    answer = chat_data["answer"]
    assert "Python" in answer, \
        f"Answer must contain 'Python', got: {answer[:300]}"


@pytest.mark.asyncio
async def test_e2e_belief_conflict_detection(client, auth_headers):
    """
    E2E: 创建观点 -> 检测冲突
    """
    await client.post("/api/v1/cognitive/beliefs", json={"topic": "AI", "content": "DeepSeek is best", "confidence": 0.9}, headers=auth_headers)

    conflict = await client.post("/api/v1/cognitive/beliefs/check-conflict", json={"content": "OpenAI is better", "topic": "AI"}, headers=auth_headers)
    assert conflict.status_code == 200


@pytest.mark.asyncio
async def test_e2e_data_export(client, auth_headers):
    """
    E2E: 创建数据 -> 导出 -> 验证
    """
    await client.post("/api/v1/memory", json={"content": "Export test", "memory_type": "FACT"}, headers=auth_headers)
    await client.post("/api/v1/cognitive/beliefs", json={"topic": "Test", "content": "Test belief"}, headers=auth_headers)

    export = await client.get("/api/v1/export/all", headers=auth_headers)
    assert export.status_code == 200

    import json
    data = json.loads(export.text)
    assert data["stats"]["memories"] >= 1
    assert data["stats"]["beliefs"] >= 1


@pytest.mark.asyncio
async def test_e2e_cross_module_integration(client, auth_headers):
    """
    E2E: 跨模块集成测试
    """
    # 创建记忆
    await client.post("/api/v1/memory", json={"content": "Cross-module test", "memory_type": "FACT"}, headers=auth_headers)

    # 创建观点
    await client.post("/api/v1/cognitive/beliefs", json={"topic": "Test", "content": "Test belief"}, headers=auth_headers)

    # 创建决策
    await client.post("/api/v1/decision", json={"problem": "Test decision", "choice": "Option A"}, headers=auth_headers)

    # 获取图谱
    graph = await client.get("/api/v1/graph", headers=auth_headers)
    assert graph.status_code == 200
    assert graph.json()["stats"]["total_nodes"] >= 3

    # 获取认知画像
    profile = await client.get("/api/v1/cognitive-model/profile", headers=auth_headers, timeout=120)
    assert profile.status_code == 200
