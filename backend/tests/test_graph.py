"""
Personal AI OS - Graph Tests
知识图谱模块测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_graph_data(client: AsyncClient, auth_headers: dict):
    """测试获取图谱数据"""
    response = await client.get("/api/v1/graph", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "stats" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)


@pytest.mark.asyncio
async def test_graph_with_data(client: AsyncClient, auth_headers: dict):
    """测试有数据时的图谱"""
    # 创建一些数据
    await client.post(
        "/api/v1/memory",
        json={"content": "Test memory for graph", "memory_type": "FACT"},
        headers=auth_headers
    )
    await client.post(
        "/api/v1/cognitive/beliefs",
        json={"topic": "Test", "content": "Test belief"},
        headers=auth_headers
    )

    response = await client.get("/api/v1/graph", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) >= 2
