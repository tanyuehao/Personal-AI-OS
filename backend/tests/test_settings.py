"""
Personal AI OS - Settings Tests
设置模块测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_settings(client: AsyncClient, auth_headers: dict):
    """测试获取设置"""
    response = await client.get("/api/v1/settings", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "ai_provider" in data
    assert "llm_model" in data
    assert "temperature" in data
    assert "max_tokens" in data


@pytest.mark.asyncio
async def test_update_settings(client: AsyncClient, auth_headers: dict):
    """测试更新设置"""
    response = await client.put(
        "/api/v1/settings",
        json={
            "temperature": "0.8",
            "max_tokens": "3000"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] == "0.8"
    assert data["max_tokens"] == "3000"


@pytest.mark.asyncio
async def test_get_usage_stats(client: AsyncClient, auth_headers: dict):
    """测试获取使用量统计"""
    response = await client.get("/api/v1/usage/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "rpm_limit" in data


@pytest.mark.asyncio
async def test_get_rate_limits(client: AsyncClient):
    """测试获取速率限制配置"""
    response = await client.get("/api/v1/usage/limits")
    assert response.status_code == 200
    data = response.json()
    assert "rpm_limit" in data
    assert "tpm_limit" in data
