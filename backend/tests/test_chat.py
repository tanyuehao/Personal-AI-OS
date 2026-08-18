"""
Personal AI OS - Chat Tests
AI 聊天模块测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_basic(client: AsyncClient, auth_headers: dict):
    """测试基本聊天"""
    response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Hello", "memory_enabled": False},
        headers=auth_headers,
        timeout=60.0
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "conversation_id" in data


@pytest.mark.asyncio
async def test_chat_with_memory(client: AsyncClient, auth_headers: dict):
    """测试带记忆的聊天"""
    # 先创建一个已确认的记忆
    mem_response = await client.post(
        "/api/v1/memory",
        json={"content": "I prefer Python", "memory_type": "PREFERENCE"},
        headers=auth_headers
    )
    if mem_response.status_code == 201:
        mem_id = mem_response.json()["memory_id"]
        await client.post(f"/api/v1/memory/{mem_id}/confirm", headers=auth_headers)

    # 聊天
    response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "What programming language do I like?", "memory_enabled": True},
        headers=auth_headers,
        timeout=60.0
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient, auth_headers: dict):
    """测试获取对话列表"""
    response = await client.get("/api/v1/ai/conversations", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_conversation_history(client: AsyncClient, auth_headers: dict):
    """测试获取对话历史"""
    # 先创建一个对话
    chat_response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Test conversation"},
        headers=auth_headers,
        timeout=60.0
    )

    if chat_response.status_code == 200:
        conv_id = chat_response.json()["conversation_id"]

        response = await client.get(
            f"/api/v1/ai/conversations/{conv_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_conversation(client: AsyncClient, auth_headers: dict):
    """测试删除对话"""
    # 先创建一个对话
    chat_response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "To be deleted"},
        headers=auth_headers,
        timeout=60.0
    )

    if chat_response.status_code == 200:
        conv_id = chat_response.json()["conversation_id"]

        response = await client.delete(
            f"/api/v1/ai/conversations/{conv_id}",
            headers=auth_headers
        )
        assert response.status_code == 204
