"""
Personal AI OS - Memory Tests
记忆模块测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_memory(client: AsyncClient, auth_headers: dict):
    """测试创建记忆"""
    response = await client.post(
        "/api/v1/memory",
        json={
            "content": "I prefer DeepSeek model",
            "memory_type": "PREFERENCE",
            "importance": 0.8
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "I prefer DeepSeek model"
    assert data["memory_type"] == "PREFERENCE"
    assert data["is_confirmed"] == "PENDING"


@pytest.mark.asyncio
async def test_list_memories(client: AsyncClient, auth_headers: dict):
    """测试获取记忆列表"""
    response = await client.get("/api/v1/memory", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_candidates(client: AsyncClient, auth_headers: dict):
    """测试获取候选记忆"""
    # 创建一个记忆
    await client.post(
        "/api/v1/memory",
        json={"content": "Test candidate", "memory_type": "FACT"},
        headers=auth_headers
    )

    response = await client.get("/api/v1/memory/candidates", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_confirm_memory(client: AsyncClient, auth_headers: dict):
    """测试确认记忆"""
    # 创建记忆
    create_response = await client.post(
        "/api/v1/memory",
        json={"content": "Test confirm", "memory_type": "FACT"},
        headers=auth_headers
    )
    mem_id = create_response.json()["memory_id"]

    # 确认
    response = await client.post(
        f"/api/v1/memory/{mem_id}/confirm",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["is_confirmed"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_reject_memory(client: AsyncClient, auth_headers: dict):
    """测试拒绝记忆"""
    # 创建记忆
    create_response = await client.post(
        "/api/v1/memory",
        json={"content": "Test reject", "memory_type": "FACT"},
        headers=auth_headers
    )
    mem_id = create_response.json()["memory_id"]

    # 拒绝
    response = await client.post(
        f"/api/v1/memory/{mem_id}/reject",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["is_confirmed"] == "REJECTED"


@pytest.mark.asyncio
async def test_confirm_all_memories(client: AsyncClient, auth_headers: dict):
    """测试批量确认记忆"""
    # 创建几个记忆
    for i in range(3):
        await client.post(
            "/api/v1/memory",
            json={"content": f"Test batch confirm {i}", "memory_type": "FACT"},
            headers=auth_headers
        )

    response = await client.post("/api/v1/memory/confirm-all", headers=auth_headers)
    assert response.status_code == 200
    assert "confirmed" in response.json()


@pytest.mark.asyncio
async def test_reject_all_memories(client: AsyncClient, auth_headers: dict):
    """测试批量拒绝记忆"""
    response = await client.post("/api/v1/memory/reject-all", headers=auth_headers)
    assert response.status_code == 200
    assert "rejected" in response.json()


@pytest.mark.asyncio
async def test_delete_memory(client: AsyncClient, auth_headers: dict):
    """测试删除记忆"""
    # 创建
    create_response = await client.post(
        "/api/v1/memory",
        json={"content": "Test delete", "memory_type": "FACT"},
        headers=auth_headers
    )
    mem_id = create_response.json()["memory_id"]

    # 删除
    response = await client.delete(
        f"/api/v1/memory/{mem_id}",
        headers=auth_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_memory_stats(client: AsyncClient, auth_headers: dict):
    """测试记忆统计"""
    response = await client.get("/api/v1/memory/stats/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "FACT" in data
    assert "avg_importance" in data


@pytest.mark.asyncio
async def test_search_memories(client: AsyncClient, auth_headers: dict):
    """测试搜索记忆"""
    # 创建记忆
    await client.post(
        "/api/v1/memory",
        json={"content": "Python is my favorite language", "memory_type": "PREFERENCE"},
        headers=auth_headers
    )

    response = await client.post(
        "/api/v1/memory/search",
        json={"query": "Python"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
