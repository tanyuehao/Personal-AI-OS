"""Memory lifecycle and evidence tests for Phase 1A."""
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
    await client.post("/api/v1/auth/register", json={
        "username": "lifecycle_user", "email": "lifecycle@test.com", "password": "test123"
    })
    r = await client.post("/api/v1/auth/login", json={"email": "lifecycle@test.com", "password": "test123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_manual_create_is_user_stated_and_confirmed(client, auth_headers):
    """Manual creation -> USER_STATED + CONFIRMED."""
    r = await client.post("/api/v1/memory", json={
        "content": "I prefer Python",
        "memory_type": "PREFERENCE",
        "importance": 0.9
    }, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["is_confirmed"] == "CONFIRMED"
    assert data["assertion_kind"] == "USER_STATED"


@pytest.mark.asyncio
async def test_manual_create_has_evidence(client, auth_headers):
    """Manual creation atomically creates MANUAL evidence."""
    r = await client.post("/api/v1/memory", json={
        "content": "Test evidence",
        "memory_type": "FACT"
    }, headers=auth_headers)
    mem_id = r.json()["memory_id"]

    r = await client.get(f"/api/v1/memory/{mem_id}/evidence", headers=auth_headers)
    assert r.status_code == 200
    evidence = r.json()
    assert len(evidence) >= 1
    assert evidence[0]["source_type"] == "MANUAL"


@pytest.mark.asyncio
async def test_server_controls_assertion_kind(client, auth_headers):
    """Client cannot set assertion_kind on manual creation."""
    r = await client.post("/api/v1/memory", json={
        "content": "test",
        "memory_type": "FACT",
        "assertion_kind": "OBSERVED"  # should be ignored
    }, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["assertion_kind"] == "USER_STATED"  # server controls this


@pytest.mark.asyncio
async def test_confirm_is_idempotent(client, auth_headers):
    """Confirming already-CONFIRMED memory is idempotent."""
    r = await client.post("/api/v1/memory", json={"content": "idempotent", "memory_type": "FACT"}, headers=auth_headers)
    mem_id = r.json()["memory_id"]

    # Confirm (already CONFIRMED from manual create)
    r = await client.post(f"/api/v1/memory/{mem_id}/confirm", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["is_confirmed"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_reject_blocks_add_evidence(client, auth_headers):
    """REJECTED memory rejects evidence addition with 409."""
    # Create manual memory (CONFIRMED by default)
    r = await client.post("/api/v1/memory", json={"content": "rejected", "memory_type": "FACT"}, headers=auth_headers)
    mem_id = r.json()["memory_id"]

    # Archive by removing all evidence (CONFIRMED -> ARCHIVED)
    ev_r = await client.get(f"/api/v1/memory/{mem_id}/evidence", headers=auth_headers)
    for ev in ev_r.json():
        await client.delete(f"/api/v1/memory/{mem_id}/evidence/{ev['evidence_id']}", headers=auth_headers)

    # Add new evidence to re-activate (ARCHIVED -> PENDING)
    r = await client.post(f"/api/v1/memory/{mem_id}/evidence", json={
        "source_type": "MANUAL", "evidence_kind": "DIRECT_QUOTE"
    }, headers=auth_headers)
    assert r.status_code == 201

    # Now reject (PENDING -> REJECTED)
    r = await client.post(f"/api/v1/memory/{mem_id}/reject", headers=auth_headers)
    assert r.status_code == 200

    # Try to add evidence - should fail
    r = await client.post(f"/api/v1/memory/{mem_id}/evidence", json={
        "source_type": "MANUAL", "evidence_kind": "DIRECT_QUOTE"
    }, headers=auth_headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_add_evidence_to_archived_transitions_to_pending(client, auth_headers):
    """ARCHIVED + evidence -> PENDING."""
    r = await client.post("/api/v1/memory", json={"content": "archived", "memory_type": "FACT"}, headers=auth_headers)
    mem_id = r.json()["memory_id"]

    # Get evidence list and remove all
    ev_r = await client.get(f"/api/v1/memory/{mem_id}/evidence", headers=auth_headers)
    evidence_list = ev_r.json()
    for ev in evidence_list:
        await client.delete(f"/api/v1/memory/{mem_id}/evidence/{ev['evidence_id']}", headers=auth_headers)

    # Check status is ARCHIVED
    r = await client.get(f"/api/v1/memory/{mem_id}", headers=auth_headers)
    assert r.json()["is_confirmed"] == "ARCHIVED"

    # Add new evidence
    r = await client.post(f"/api/v1/memory/{mem_id}/evidence", json={
        "source_type": "MANUAL", "evidence_kind": "DIRECT_QUOTE"
    }, headers=auth_headers)
    assert r.status_code == 201

    # Check status is now PENDING
    r = await client.get(f"/api/v1/memory/{mem_id}", headers=auth_headers)
    assert r.json()["is_confirmed"] == "PENDING"


@pytest.mark.asyncio
async def test_add_remove_evidence_lifecycle(client, auth_headers):
    """Add and remove evidence with correct lifecycle."""
    r = await client.post("/api/v1/memory", json={"content": "test lifecycle", "memory_type": "FACT"}, headers=auth_headers)
    mem_id = r.json()["memory_id"]

    # Add evidence
    r = await client.post(f"/api/v1/memory/{mem_id}/evidence", json={
        "source_type": "MANUAL", "evidence_kind": "DIRECT_QUOTE"
    }, headers=auth_headers)
    assert r.status_code == 201

    # Remove all evidence -> ARCHIVED
    ev_r = await client.get(f"/api/v1/memory/{mem_id}/evidence", headers=auth_headers)
    for ev in ev_r.json():
        await client.delete(f"/api/v1/memory/{mem_id}/evidence/{ev['evidence_id']}", headers=auth_headers)

    r = await client.get(f"/api/v1/memory/{mem_id}", headers=auth_headers)
    assert r.json()["is_confirmed"] == "ARCHIVED"
