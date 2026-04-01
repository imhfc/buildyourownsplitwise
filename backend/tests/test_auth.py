import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestMe:
    async def test_get_me(self, client: AsyncClient, db):
        user = await create_test_user(db, "me@example.com")
        resp = await client.get("/api/v1/auth/me", headers=auth_header(user))
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"

    async def test_get_me_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403

    async def test_update_me(self, client: AsyncClient, db):
        user = await create_test_user(db, "upd@example.com")
        resp = await client.patch(
            "/api/v1/auth/me",
            headers=auth_header(user),
            json={"display_name": "Updated Name", "preferred_currency": "USD"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"
        assert resp.json()["preferred_currency"] == "USD"


class TestRemovedEndpoints:
    """Verify that password-based auth endpoints no longer exist."""

    async def test_register_removed(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "securepass",
            "display_name": "New User",
        })
        assert resp.status_code in (404, 405)

    async def test_login_removed(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "pass",
        })
        assert resp.status_code in (404, 405)

    async def test_change_password_removed(self, client: AsyncClient, db):
        user = await create_test_user(db, "pw@example.com")
        resp = await client.patch(
            "/api/v1/auth/me/password",
            headers=auth_header(user),
            json={"old_password": "x", "new_password": "y"},
        )
        assert resp.status_code in (404, 405)
