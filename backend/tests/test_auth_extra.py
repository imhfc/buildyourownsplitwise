"""補充 auth 測試：lookup 端點。"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestLookupUser:
    """GET /api/v1/auth/lookup?email=..."""

    async def test_lookup_existing_user(
        self, client: AsyncClient, db, user_a: User
    ):
        resp = await client.get(
            "/api/v1/auth/lookup",
            headers=auth_header(user_a),
            params={"email": "alice@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert data["display_name"] == "Alice"

    async def test_lookup_nonexistent_user(
        self, client: AsyncClient, db, user_a: User
    ):
        resp = await client.get(
            "/api/v1/auth/lookup",
            headers=auth_header(user_a),
            params={"email": "nobody@example.com"},
        )
        assert resp.status_code == 404

    async def test_lookup_no_auth(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/lookup",
            params={"email": "test@example.com"},
        )
        assert resp.status_code == 403
