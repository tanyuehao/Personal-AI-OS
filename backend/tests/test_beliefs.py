"""
Personal AI OS - Belief Tests
观点模块测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_belief(client: AsyncClient, auth_headers: dict):
    """测试创建观点"""
    response = await client.post(
        "/api/v1/cognitive/beliefs",
        json={
            "topic": "AI Models",
            "content": "DeepSeek is the best value model",
            "confidence": 0.9
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["topic"] == "AI Models"
    assert data["confidence"] == 0.9


@pytest.mark.asyncio
async def test_list_beliefs(client: AsyncClient, auth_headers: dict):
    """测试获取观点列表"""
    response = await client.get("/api/v1/cognitive/beliefs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_belief(client: AsyncClient, auth_headers: dict):
    """测试获取观点详情"""
    # 创建
    create_response = await client.post(
        "/api/v1/cognitive/beliefs",
        json={"topic": "Test", "content": "Test content"},
        headers=auth_headers
    )
    belief_id = create_response.json()["belief_id"]

    # 获取
    response = await client.get(
        f"/api/v1/cognitive/beliefs/{belief_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["topic"] == "Test"


@pytest.mark.asyncio
async def test_update_belief(client: AsyncClient, auth_headers: dict):
    """测试更新观点"""
    # 创建
    create_response = await client.post(
        "/api/v1/cognitive/beliefs",
        json={"topic": "Update Test", "content": "Original content"},
        headers=auth_headers
    )
    belief_id = create_response.json()["belief_id"]

    # 更新
    response = await client.put(
        f"/api/v1/cognitive/beliefs/{belief_id}",
        json={"content": "Updated content", "change_reason": "New evidence"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated content"


@pytest.mark.asyncio
async def test_delete_belief(client: AsyncClient, auth_headers: dict):
    """测试删除观点"""
    # 创建
    create_response = await client.post(
        "/api/v1/cognitive/beliefs",
        json={"topic": "Delete Test", "content": "To be deleted"},
        headers=auth_headers
    )
    belief_id = create_response.json()["belief_id"]

    # 删除
    response = await client.delete(
        f"/api/v1/cognitive/beliefs/{belief_id}",
        headers=auth_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_belief_history(client: AsyncClient, auth_headers: dict):
    """测试获取观点历史"""
    # 创建
    create_response = await client.post(
        "/api/v1/cognitive/beliefs",
        json={"topic": "History Test", "content": "Original"},
        headers=auth_headers
    )
    belief_id = create_response.json()["belief_id"]

    # 更新几次
    for i in range(3):
        await client.put(
            f"/api/v1/cognitive/beliefs/{belief_id}",
            json={"content": f"Version {i+1}", "change_reason": f"Update {i+1}"},
            headers=auth_headers
        )

    # 获取历史
    response = await client.get(
        f"/api/v1/cognitive/beliefs/{belief_id}/history",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_get_timeline(client: AsyncClient, auth_headers: dict):
    """测试获取时间线"""
    # 创建几个观点
    for topic, content in [("AI", "AI is great"), ("Work", "Remote work is good")]:
        await client.post(
            "/api/v1/cognitive/beliefs",
            json={"topic": topic, "content": content},
            headers=auth_headers
        )

    response = await client.get("/api/v1/cognitive/beliefs/timeline", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "timeline" in data
    assert len(data["timeline"]) >= 2
