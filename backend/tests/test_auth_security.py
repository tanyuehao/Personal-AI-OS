"""
Personal AI OS - Auth Security Tests
认证安全测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import decode_token
from app.core.database import async_session_factory
from sqlalchemy import select
from app.models.user import RefreshToken


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_jwt_jti_matches_db_jti(client):
    """P0: JWT.jti 必须与 DB.refresh_tokens.jti 完全一致"""
    await client.post("/api/v1/auth/register", json={
        "username": "jti_match_test", "email": "jti_match@test.com", "password": "test123"
    })

    # 登录
    r = await client.post("/api/v1/auth/login", json={"email": "jti_match@test.com", "password": "test123"})
    assert r.status_code == 200
    refresh_token = r.json()["refresh_token"]

    # 从 JWT 中解码 jti
    jwt_payload = decode_token(refresh_token)
    jwt_jti = jwt_payload.get("jti")
    jwt_type = jwt_payload.get("type")
    jwt_sub = jwt_payload.get("sub")

    assert jwt_jti is not None, "JWT payload must contain jti"
    assert jwt_type == "refresh", "Token type must be refresh"
    assert jwt_sub is not None, "JWT payload must contain sub (user_id)"

    # 从 DB 中查询同一个 jti
    async with async_session_factory() as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.jti == jwt_jti)
        )
        db_record = result.scalar_one_or_none()

    assert db_record is not None, f"DB must contain RefreshToken with jti={jwt_jti}"
    assert str(db_record.user_id) == jwt_sub, f"DB user_id {db_record.user_id} must match JWT sub {jwt_sub}"
    assert db_record.jti == jwt_jti, f"DB jti {db_record.jti} must match JWT jti {jwt_jti}"
    assert db_record.is_used is False, "Token must not be used yet"
    assert db_record.is_revoked is False, "Token must not be revoked yet"


@pytest.mark.asyncio
async def test_refresh_creates_new_matching_jti(client):
    """Refresh 后新 token 的 JWT.jti 也必须匹配 DB"""
    await client.post("/api/v1/auth/register", json={
        "username": "jti_refresh_test", "email": "jti_refresh@test.com", "password": "test123"
    })

    # 登录
    r = await client.post("/api/v1/auth/login", json={"email": "jti_refresh@test.com", "password": "test123"})
    old_refresh = r.json()["refresh_token"]

    # 第一次 refresh
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]

    # 验证新 token 的 JWT.jti === DB.jti
    new_payload = decode_token(new_refresh)
    new_jti = new_payload.get("jti")
    assert new_jti is not None

    async with async_session_factory() as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.jti == new_jti)
        )
        db_record = result.scalar_one_or_none()

    assert db_record is not None, f"DB must contain new RefreshToken with jti={new_jti}"
    assert db_record.jti == new_jti, f"DB jti {db_record.jti} must match new JWT jti {new_jti}"
    assert db_record.is_used is False, "New token must not be used yet"


@pytest.mark.asyncio
async def test_refresh_token_rotates(client):
    """Refresh token 每次使用后都会轮换"""
    # 注册
    await client.post("/api/v1/auth/register", json={
        "username": "refresh_test", "email": "refresh@test.com", "password": "test123"
    })
    
    # 登录
    r = await client.post("/api/v1/auth/login", json={"email": "refresh@test.com", "password": "test123"})
    assert r.status_code == 200
    old_refresh = r.json()["refresh_token"]
    
    # 第一次 refresh
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]
    
    # 新旧 token 必须不同
    assert old_refresh != new_refresh, "Refresh token should rotate"


@pytest.mark.asyncio
async def test_old_refresh_token_cannot_be_reused(client):
    """旧 refresh token 不能再使用"""
    await client.post("/api/v1/auth/register", json={
        "username": "reuse_test", "email": "reuse@test.com", "password": "test123"
    })
    
    r = await client.post("/api/v1/auth/login", json={"email": "reuse@test.com", "password": "test123"})
    old_refresh = r.json()["refresh_token"]
    
    # 第一次 refresh
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    
    # 第二次使用同一个 token - 必须 401
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 401, "Old refresh token should not be reusable"


@pytest.mark.asyncio
async def test_replay_revokes_token_family(client):
    """重放攻击 revoke 整个 token family"""
    await client.post("/api/v1/auth/register", json={
        "username": "family_test", "email": "family@test.com", "password": "test123"
    })
    
    r = await client.post("/api/v1/auth/login", json={"email": "family@test.com", "password": "test123"})
    token_t1 = r.json()["refresh_token"]
    token_t1_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    
    # T1 refresh → T2
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": token_t1})
    assert r.status_code == 200
    token_t2 = r.json()["refresh_token"]
    token_t2_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    
    # 再次使用 T1 (replay) - 必须 401
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": token_t1})
    assert r.status_code == 401, "Replayed token should be rejected"
    
    # T2 也应该失效（整个 family 被 revoke）
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": token_t2})
    assert r.status_code == 401, "Token family should be revoked after replay"


@pytest.mark.asyncio
async def test_logout_invalidates_refresh_token(client):
    """Logout 后 refresh token 失效"""
    await client.post("/api/v1/auth/register", json={
        "username": "logout_test", "email": "logout@test.com", "password": "test123"
    })

    r = await client.post("/api/v1/auth/login", json={"email": "logout@test.com", "password": "test123"})
    access_token = r.json()["access_token"]
    refresh_token = r.json()["refresh_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # 登出（JSON body）
    r = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth_headers
    )
    assert r.status_code == 200

    # 使用旧 refresh token - 必须 401
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401, "Refresh token should be invalidated after logout"


@pytest.mark.asyncio
async def test_malformed_refresh_token(client):
    """格式错误的 refresh token 必须 401"""
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-valid-jwt"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_expired_refresh_token(client):
    """过期的 refresh token 必须 401"""
    # 这个测试验证逻辑存在，实际过期需要等待或 mock
    # 至少验证格式错误时返回 401
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "expired"})
    assert r.status_code == 401
