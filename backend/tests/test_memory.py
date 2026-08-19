"""
Personal AI OS - Memory Tests
记忆模块测试
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
    """获取认证头"""
    # 注册用户
    await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    
    # 登录
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_memory(client, auth_headers):
    """测试创建记忆"""
    response = await client.post(
        "/api/v1/memory",
        json={
            "content": "我更看重长期现金流",
            "memory_type": "PREFERENCE",
            "importance": 0.7
        },
        headers=auth_headers
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["content"] == "我更看重长期现金流"
    assert data["memory_type"] == "PREFERENCE"


@pytest.mark.asyncio
async def test_list_memories(client, auth_headers):
    """测试获取记忆列表"""
    response = await client.get(
        "/api/v1/memory",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_search_memories(client, auth_headers):
    """测试搜索记忆"""
    # 先创建记忆
    await client.post(
        "/api/v1/memory",
        json={
            "content": "我喜欢用 Python 开发",
            "memory_type": "PREFERENCE",
            "importance": 0.6
        },
        headers=auth_headers
    )
    
    # 搜索
    response = await client.post(
        "/api/v1/memory/search",
        json={"query": "Python"},
        headers=auth_headers
    )
    assert response.status_code == 200
