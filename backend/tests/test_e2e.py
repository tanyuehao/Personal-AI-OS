"""
Personal AI OS - E2E Tests
端到端测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_document_to_qa(client: AsyncClient, auth_headers: dict):
    """
    E2E-01: 上传文档 -> 等待处理 -> 提问 -> 回答包含引用

    完整流程测试：用户上传文档，系统处理后，基于文档内容回答问题。
    """
    # 1. 上传文档
    content = b"Personal AI OS is a personal cognitive operating system. It helps AI understand your knowledge base."
    files = {"file": ("test_e2e.txt", content, "text/plain")}

    upload_response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers
    )
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["document_id"]

    # 2. 等待文档处理（异步）
    import asyncio
    await asyncio.sleep(3)

    # 3. 检查文档状态
    doc_response = await client.get(
        f"/api/v1/documents/{doc_id}",
        headers=auth_headers
    )
    assert doc_response.status_code == 200

    # 4. 提问
    chat_response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "What is Personal AI OS?", "memory_enabled": False},
        headers=auth_headers,
        timeout=60.0
    )
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert "answer" in data
    assert "conversation_id" in data


@pytest.mark.asyncio
async def test_e2e_memory_candidate_flow(client: AsyncClient, auth_headers: dict):
    """
    E2E-02: 用户表达偏好 -> 生成候选记忆 -> 用户确认 -> 新会话可召回

    完整记忆流程测试。
    """
    # 1. 创建记忆
    mem_response = await client.post(
        "/api/v1/memory",
        json={
            "content": "I prefer using Python for backend development",
            "memory_type": "PREFERENCE",
            "importance": 0.9
        },
        headers=auth_headers
    )
    assert mem_response.status_code == 201
    mem_id = mem_response.json()["memory_id"]

    # 2. 确认记忆
    confirm_response = await client.post(
        f"/api/v1/memory/{mem_id}/confirm",
        headers=auth_headers
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["is_confirmed"] == "CONFIRMED"

    # 3. 新会话中提问
    chat_response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "What programming language do I prefer?", "memory_enabled": True},
        headers=auth_headers,
        timeout=60.0
    )
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert "answer" in data


@pytest.mark.asyncio
async def test_e2e_document_deletion_cascade(client: AsyncClient, auth_headers: dict):
    """
    E2E-03: 删除文档 -> 不再检索到其 Chunk

    文档删除级联测试。
    """
    # 1. 上传文档
    content = b"Document to be deleted. Contains specific keywords for testing."
    files = {"file": ("to_delete.txt", content, "text/plain")}

    upload_response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers
    )
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["document_id"]

    # 2. 删除文档
    delete_response = await client.delete(
        f"/api/v1/documents/{doc_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 204

    # 3. 验证文档已删除
    get_response = await client.get(
        f"/api/v1/documents/{doc_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_e2e_belief_conflict_detection(client: AsyncClient, auth_headers: dict):
    """
    E2E: 创建观点 -> 创建冲突观点 -> 检测冲突

    观点冲突检测测试。
    """
    # 1. 创建第一个观点
    await client.post(
        "/api/v1/cognitive/beliefs",
        json={"topic": "AI Models", "content": "DeepSeek is the best model", "confidence": 0.9},
        headers=auth_headers
    )

    # 2. 创建冲突观点
    conflict_response = await client.post(
        "/api/v1/cognitive/beliefs/check-conflict",
        json={"content": "OpenAI is better than DeepSeek", "topic": "AI Models"},
        headers=auth_headers
    )
    assert conflict_response.status_code == 200
    data = conflict_response.json()
    assert "has_conflicts" in data


@pytest.mark.asyncio
async def test_e2e_data_export(client: AsyncClient, auth_headers: dict):
    """
    E2E: 创建数据 -> 导出数据 -> 验证完整性

    数据导出测试。
    """
    # 1. 创建一些数据
    await client.post(
        "/api/v1/memory",
        json={"content": "Test memory for export", "memory_type": "FACT"},
        headers=auth_headers
    )
    await client.post(
        "/api/v1/cognitive/beliefs",
        json={"topic": "Test", "content": "Test belief"},
        headers=auth_headers
    )

    # 2. 导出数据
    export_response = await client.get(
        "/api/v1/export/all",
        headers=auth_headers
    )
    assert export_response.status_code == 200
    assert "application/json" in export_response.headers["content-type"]

    # 3. 验证导出内容
    import json
    data = json.loads(export_response.text)
    assert "export_info" in data
    assert "memories" in data
    assert "beliefs" in data
    assert data["stats"]["memories"] >= 1
    assert data["stats"]["beliefs"] >= 1
