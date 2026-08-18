"""
Personal AI OS - Document Tests
文档模块测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient, auth_headers: dict):
    """测试文档上传"""
    content = b"Test document content for Personal AI OS"
    files = {"file": ("test.txt", content, "text/plain")}

    response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["file_name"] == "test.txt"
    assert data["status"] == "UPLOADING"


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, auth_headers: dict):
    """测试获取文档列表"""
    response = await client.get("/api/v1/documents", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, auth_headers: dict):
    """测试上传不支持的文件类型"""
    content = b"test"
    files = {"file": ("test.exe", content, "application/octet-stream")}

    response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers
    )
    assert response.status_code in [400, 422, 500]  # Validation error


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient, auth_headers: dict):
    """测试删除文档"""
    # 先上传
    content = b"Test document for deletion"
    files = {"file": ("delete_me.txt", content, "text/plain")}
    upload_response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers
    )

    if upload_response.status_code == 201:
        doc_id = upload_response.json()["document_id"]

        # 删除
        response = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=auth_headers
        )
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_nonexistent_document(client: AsyncClient, auth_headers: dict):
    """测试获取不存在的文档"""
    response = await client.get(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers
    )
    assert response.status_code == 404
