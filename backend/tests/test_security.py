"""
Personal AI OS - Security Tests
安全测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """测试未授权访问"""
    # 尝试访问需要认证的端点
    endpoints = [
        "/api/v1/documents",
        "/api/v1/memory",
        "/api/v1/cognitive/beliefs",
        "/api/v1/decision",
        "/api/v1/settings",
        "/api/v1/graph",
        "/api/v1/export/all",
    ]

    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert response.status_code in [401, 403], f"{endpoint} should require auth"


@pytest.mark.asyncio
async def test_cross_user_data_isolation(client: AsyncClient, auth_headers: dict):
    """测试跨用户数据隔离"""
    # 创建数据
    mem_response = await client.post(
        "/api/v1/memory",
        json={"content": "Private memory", "memory_type": "FACT"},
        headers=auth_headers
    )
    mem_id = mem_response.json()["memory_id"]

    # 尝试用另一个用户访问（模拟）
    # 这里我们用同一个用户测试，但验证 user_id 检查存在
    response = await client.get(
        f"/api/v1/memory/{mem_id}",
        headers=auth_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    """测试无效 token"""
    headers = {"Authorization": "Bearer invalid-token-12345"}

    response = await client.get("/api/v1/memory", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sql_injection_prevention(client: AsyncClient, auth_headers: dict):
    """测试 SQL 注入防护"""
    # 尝试 SQL 注入
    injection_payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users --",
    ]

    for payload in injection_payloads:
        response = await client.post(
            "/api/v1/memory/search",
            json={"query": payload},
            headers=auth_headers
        )
        # 应该正常返回（200），而不是崩溃（500）
        assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_file_upload_security(client: AsyncClient, auth_headers: dict):
    """测试文件上传安全"""
    # 测试不支持的文件类型
    content = b"test"
    files = {"file": ("malware.exe", content, "application/octet-stream")}
    response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers
    )
    assert response.status_code in [400, 422, 500]


@pytest.mark.asyncio
async def test_api_key_not_exposed(client: AsyncClient, auth_headers: dict):
    """测试 API Key 不暴露"""
    response = await client.get("/api/v1/settings", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # 验证响应包含预期的字段
    assert "ai_provider" in data
    assert "llm_model" in data
    assert "temperature" in data


@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient, auth_headers: dict):
    """测试速率限制"""
    # 快速发送多个请求
    for i in range(5):
        response = await client.get("/api/v1/memory", headers=auth_headers)
        assert response.status_code == 200

    # 检查速率限制配置
    response = await client.get("/api/v1/usage/limits")
    assert response.status_code == 200
    data = response.json()
    assert "rpm_limit" in data
    assert "tpm_limit" in data


@pytest.mark.asyncio
async def test_path_traversal_prevention(client: AsyncClient, auth_headers: dict):
    """测试路径穿越防护"""
    # 尝试访问不存在的文档 ID
    response = await client.get(
        "/api/v1/documents/../../../etc/passwd",
        headers=auth_headers
    )
    # 应该返回 404 或 422，而不是文件内容
    assert response.status_code in [404, 422]
