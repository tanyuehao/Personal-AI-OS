"""
Personal AI OS - Decision Tests
决策模块测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_decision(client: AsyncClient, auth_headers: dict):
    """测试创建决策"""
    response = await client.post(
        "/api/v1/decision",
        json={
            "problem": "Choose AI model",
            "background": "Need a cost-effective model",
            "options": ["DeepSeek", "OpenAI", "Local"],
            "choice": "DeepSeek",
            "reasoning": "Best cost-performance ratio",
            "category": "tech"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["problem"] == "Choose AI model"
    assert data["choice"] == "DeepSeek"


@pytest.mark.asyncio
async def test_list_decisions(client: AsyncClient, auth_headers: dict):
    """测试获取决策列表"""
    response = await client.get("/api/v1/decision", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_decision(client: AsyncClient, auth_headers: dict):
    """测试获取决策详情"""
    # 创建
    create_response = await client.post(
        "/api/v1/decision",
        json={"problem": "Test decision"},
        headers=auth_headers
    )
    dec_id = create_response.json()["decision_id"]

    # 获取
    response = await client.get(
        f"/api/v1/decision/{dec_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["problem"] == "Test decision"


@pytest.mark.asyncio
async def test_update_decision(client: AsyncClient, auth_headers: dict):
    """测试更新决策"""
    # 创建
    create_response = await client.post(
        "/api/v1/decision",
        json={"problem": "Original problem"},
        headers=auth_headers
    )
    dec_id = create_response.json()["decision_id"]

    # 更新
    response = await client.put(
        f"/api/v1/decision/{dec_id}",
        json={"actual_result": "It worked well", "lesson": "DeepSeek is reliable"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["actual_result"] == "It worked well"


@pytest.mark.asyncio
async def test_delete_decision(client: AsyncClient, auth_headers: dict):
    """测试删除决策"""
    # 创建
    create_response = await client.post(
        "/api/v1/decision",
        json={"problem": "To be deleted"},
        headers=auth_headers
    )
    dec_id = create_response.json()["decision_id"]

    # 删除
    response = await client.delete(
        f"/api/v1/decision/{dec_id}",
        headers=auth_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_decision_stats(client: AsyncClient, auth_headers: dict):
    """测试决策统计"""
    response = await client.get("/api/v1/decision/stats/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "categories" in data
