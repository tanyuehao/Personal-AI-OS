"""Debug: trace exactly what happens in login + refresh"""
import httpx
import asyncio
from app.core.security import decode_token
from app.core.database import async_session_factory
from sqlalchemy import select, text
from app.models.user import RefreshToken


async def test():
    # 1. Login via HTTP
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        await client.post("/api/v1/auth/register", json={
            "username": "trace_v1", "email": "trace_v1@test.com", "password": "test123"
        })
        r = await client.post("/api/v1/auth/login", json={
            "email": "trace_v1@test.com", "password": "test123"
        })
        print(f"Login: {r.status_code}")
        if r.status_code != 200:
            return

        refresh_token = r.json()["refresh_token"]
        payload = decode_token(refresh_token)
        print(f"JWT jti: {payload.get('jti')}")
        print(f"JWT sub: {payload.get('sub')}")
        print(f"JWT type: {payload.get('type')}")

    # 2. Check DB directly
    async with async_session_factory() as session:
        # All tokens
        result = await session.execute(select(RefreshToken))
        all_tokens = result.scalars().all()
        print(f"\nTotal RefreshToken rows: {len(all_tokens)}")
        for t in all_tokens:
            print(f"  jti={t.jti[:8]}... user_id={str(t.user_id)[:8]}... used={t.is_used} revoked={t.is_revoked}")

        # Count by raw SQL
        result = await session.execute(text("SELECT COUNT(*) FROM refresh_tokens"))
        count = result.scalar()
        print(f"Raw COUNT: {count}")

    # 3. Refresh via HTTP
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        print(f"\nRefresh: {r.status_code}")
        print(f"Response: {r.text[:200]}")


if __name__ == "__main__":
    asyncio.run(test())
