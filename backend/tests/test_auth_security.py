"""
Personal AI OS - Auth Rotation Tests
P0: 完整的 refresh token rotation 生命周期验证

测试覆盖：
1. T1→T2 rotation
2. T1 replay → family revoke
3. T2 也必须 401（family revoke 级联）
4. logout → old token 401
5. 多次 login 不冲突
6. JWT.jti === DB.jti
7. malformed / expired token
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


# ─── helper ───────────────────────────────────────────────

async def _register_and_login(client, username, email, password="test123"):
    """注册并登录，返回 {access_token, refresh_token}"""
    await client.post("/api/v1/auth/register", json={
        "username": username, "email": email, "password": password
    })
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.text}"
    return r.json()


async def _db_token_count():
    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken))
        return len(r.scalars().all())


async def _db_tokens_for_user(user_id):
    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))
        return r.scalars().all()


# ─── 1. T1 → T2 rotation ─────────────────────────────────

@pytest.mark.asyncio
async def test_rotation_t1_to_t2(client):
    """登录获得 T1，refresh 获得 T2，T1 ≠ T2，T1 标记为 used"""
    tokens = await _register_and_login(client, "rot1", "rot1@test.com")
    t1 = tokens["refresh_token"]
    t1_payload = decode_token(t1)

    # T1 → T2
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 200
    t2 = r.json()["refresh_token"]
    t2_payload = decode_token(t2)

    # T1 ≠ T2
    assert t1 != t2, "T2 must differ from T1"

    # JWT.jti must differ
    assert t1_payload["jti"] != t2_payload["jti"], "JWT jti must rotate"

    # T1's DB record must be is_used=True
    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken).where(RefreshToken.jti == t1_payload["jti"]))
        t1_db = r.scalar_one_or_none()
    assert t1_db is not None
    assert t1_db.is_used is True, "T1 must be marked used in DB"
    assert t1_db.is_revoked is False, "T1 must NOT be revoked (normal rotation)"

    # T2's DB record must be is_used=False
    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken).where(RefreshToken.jti == t2_payload["jti"]))
        t2_db = r.scalar_one_or_none()
    assert t2_db is not None
    assert t2_db.is_used is False
    assert t2_db.is_revoked is False


# ─── 2. T1 replay → family revoke ────────────────────────

@pytest.mark.asyncio
async def test_replay_revokes_family(client):
    """T1 refresh → T2，再次使用 T1（replay），整个 family 必须被 revoke"""
    tokens = await _register_and_login(client, "replay1", "replay1@test.com")
    t1 = tokens["refresh_token"]
    t1_jti = decode_token(t1)["jti"]

    # T1 → T2
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 200
    t2 = r.json()["refresh_token"]
    t2_jti = decode_token(t2)["jti"]

    # T1 replay → 401
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 401, "T1 replay must be rejected"

    # T1's family in DB: all tokens must be revoked
    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken).where(RefreshToken.jti == t1_jti))
        t1_db = r.scalar_one_or_none()
        family = t1_db.token_family

        r2 = await s.execute(
            select(RefreshToken).where(RefreshToken.token_family == family)
        )
        family_tokens = r2.scalars().all()

    assert len(family_tokens) >= 2, "Family must contain at least T1 and T2"
    for t in family_tokens:
        assert t.is_revoked is True, f"Token {t.jti[:8]}... in family must be revoked after replay"


# ─── 3. T2 → 401 after replay ────────────────────────────

@pytest.mark.asyncio
async def test_t2_dead_after_replay(client):
    """T1→T2，replay T1 后 T2 也必须 401"""
    tokens = await _register_and_login(client, "t2dead", "t2dead@test.com")
    t1 = tokens["refresh_token"]

    # T1 → T2
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 200
    t2 = r.json()["refresh_token"]

    # replay T1
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 401

    # T2 must also be dead
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t2})
    assert r.status_code == 401, "T2 must be 401 after family revoke"


# ─── 4. logout → old token 401 ───────────────────────────

@pytest.mark.asyncio
async def test_logout_invalidates_token(client):
    """Logout 后 refresh token 必须 401"""
    tokens = await _register_and_login(client, "logout1", "logout1@test.com")
    t1 = tokens["refresh_token"]
    access = tokens["access_token"]

    # logout (JSON body)
    r = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": t1},
        headers={"Authorization": f"Bearer {access}"}
    )
    assert r.status_code == 200

    # T1 must be 401
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 401, "Token must be invalidated after logout"

    # verify DB: token is_revoked=True
    t1_jti = decode_token(t1)["jti"]
    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken).where(RefreshToken.jti == t1_jti))
        db_t = r.scalar_one_or_none()
    assert db_t is not None
    assert db_t.is_revoked is True, "DB record must be revoked after logout"


@pytest.mark.asyncio
async def test_logout_then_different_login_works(client):
    """Logout 后用同一用户重新 login，新 token 必须有效"""
    await client.post("/api/v1/auth/register", json={
        "username": "logout2", "email": "logout2@test.com", "password": "test123"
    })

    # login #1
    r1 = await client.post("/api/v1/auth/login", json={"email": "logout2@test.com", "password": "test123"})
    t1 = r1.json()["refresh_token"]
    a1 = r1.json()["access_token"]

    # logout #1
    await client.post("/api/v1/auth/logout",
        json={"refresh_token": t1},
        headers={"Authorization": f"Bearer {a1}"}
    )

    # login #2 — new session, new tokens
    r2 = await client.post("/api/v1/auth/login", json={"email": "logout2@test.com", "password": "test123"})
    assert r2.status_code == 200
    t2 = r2.json()["refresh_token"]
    assert t2 != t1, "New login must produce different token"

    # T2 must work
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t2})
    assert r.status_code == 200, "New token from fresh login must be valid"


# ─── 5. 多次 login 不冲突 ────────────────────────────────

@pytest.mark.asyncio
async def test_multiple_logins_independent(client):
    """登录 3 次获得 T1/T2/T3，各自独立，互不干扰"""
    await client.post("/api/v1/auth/register", json={
        "username": "multi1", "email": "multi1@test.com", "password": "test123"
    })

    # login #1
    r1 = await client.post("/api/v1/auth/login", json={"email": "multi1@test.com", "password": "test123"})
    t1 = r1.json()["refresh_token"]

    # login #2
    r2 = await client.post("/api/v1/auth/login", json={"email": "multi1@test.com", "password": "test123"})
    t2 = r2.json()["refresh_token"]

    # login #3
    r3 = await client.post("/api/v1/auth/login", json={"email": "multi1@test.com", "password": "test123"})
    t3 = r3.json()["refresh_token"]

    # all 3 tokens are different
    assert len({t1, t2, t3}) == 3, "Three logins must produce three unique tokens"

    # T1 refresh works, T2 and T3 unaffected
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 200, "T1 must be valid"

    # T1 is now dead
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 401, "T1 dead after use"

    # T2 and T3 still independent and valid
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t2})
    assert r.status_code == 200, "T2 must still be valid"

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t3})
    assert r.status_code == 200, "T3 must still be valid"


# ─── 6. JWT.jti === DB.jti ───────────────────────────────

@pytest.mark.asyncio
async def test_jwt_jti_matches_db_jti(client):
    """JWT payload 中的 jti 必须与 DB refresh_tokens.jti 完全一致"""
    tokens = await _register_and_login(client, "jti1", "jti1@test.com")
    rt = tokens["refresh_token"]
    payload = decode_token(rt)

    assert payload["jti"] is not None, "JWT must contain jti"
    assert payload["type"] == "refresh"
    assert payload["sub"] is not None

    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken).where(RefreshToken.jti == payload["jti"]))
        db_rec = r.scalar_one_or_none()

    assert db_rec is not None, f"DB must contain token with jti={payload['jti']}"
    assert str(db_rec.user_id) == payload["sub"]
    assert db_rec.jti == payload["jti"]
    assert db_rec.is_used is False
    assert db_rec.is_revoked is False


@pytest.mark.asyncio
async def test_rotation_new_jti_matches_db(client):
    """Refresh 后新 token 的 JWT.jti 也必须匹配 DB"""
    tokens = await _register_and_login(client, "jti2", "jti2@test.com")
    t1 = tokens["refresh_token"]

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": t1})
    assert r.status_code == 200
    t2 = r.json()["refresh_token"]
    t2_payload = decode_token(t2)

    async with async_session_factory() as s:
        r = await s.execute(select(RefreshToken).where(RefreshToken.jti == t2_payload["jti"]))
        db_rec = r.scalar_one_or_none()

    assert db_rec is not None, f"DB must contain new token with jti={t2_payload['jti']}"
    assert db_rec.jti == t2_payload["jti"]
    assert db_rec.is_used is False


# ─── 7. malformed / expired ───────────────────────────────

@pytest.mark.asyncio
async def test_malformed_token_rejected(client):
    """格式错误的 refresh token 必须 401"""
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-valid-jwt"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_empty_token_rejected(client):
    """空 refresh token 必须 400"""
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": ""})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_access_token_as_refresh_rejected(client):
    """access token 不能当 refresh token 用"""
    tokens = await _register_and_login(client, "wrongtype", "wrongtype@test.com")
    access = tokens["access_token"]

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert r.status_code == 401, "access token must not work as refresh token"


@pytest.mark.asyncio
async def test_expired_refresh_token_rejected(client):
    """过期的 refresh token 必须 401"""
    from datetime import datetime, timedelta, timezone

    tokens = await _register_and_login(client, "expired1", "expired1@test.com")
    rt = tokens["refresh_token"]
    payload = decode_token(rt)

    # 手动将 DB 中的 expires_at 设为过去时间
    async with async_session_factory() as s:
        result = await s.execute(
            select(RefreshToken).where(RefreshToken.jti == payload["jti"])
        )
        db_token = result.scalar_one_or_none()
        assert db_token is not None
        db_token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await s.commit()

    # 使用过期 token → 必须 401
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert r.status_code == 401, "Expired refresh token must be rejected"
