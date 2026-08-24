"""
Personal AI OS - Test Fixtures
测试公共 fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """初始化测试数据库"""
    await init_db()


@pytest.fixture
async def client():
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client):
    """获取认证 headers"""
    # 尝试注册
    reg_response = await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "testpass123"
    })

    # 登录
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@test.com",
        "password": "testpass123"
    })

    if response.status_code == 200 and "access_token" in response.json():
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    # 如果登录失败，用测试账号
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@personalai.com",
        "password": "admin123"
    })

    if response.status_code == 200 and "access_token" in response.json():
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    raise Exception("无法获取认证 token")
