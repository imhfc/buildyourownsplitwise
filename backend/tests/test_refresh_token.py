"""Tests for refresh token mechanism."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from tests.conftest import auth_header, create_test_user

pytestmark = pytest.mark.asyncio


class TestRefreshToken:
    async def test_register_returns_refresh_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "refresh_reg@example.com",
            "password": "securepass",
            "display_name": "Refresh User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"

    async def test_login_returns_refresh_token(self, client: AsyncClient, db):
        await create_test_user(db, "refresh_login@example.com", "mypass", "LoginRefresh")
        resp = await client.post("/api/v1/auth/login", json={
            "email": "refresh_login@example.com",
            "password": "mypass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]

    async def test_refresh_success(self, client: AsyncClient, db):
        user = await create_test_user(db, "refresh_ok@example.com", "pass", "RefreshOK")
        refresh_token = create_refresh_token(str(user.id))

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["user"]["email"] == "refresh_ok@example.com"

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid-token-value",
        })
        assert resp.status_code == 401

    async def test_refresh_with_access_token_fails(self, client: AsyncClient, db):
        """An access token should not be usable as a refresh token."""
        user = await create_test_user(db, "no_access_as_refresh@example.com")
        access_token = create_access_token(str(user.id))

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token,
        })
        assert resp.status_code == 401

    async def test_new_access_token_works(self, client: AsyncClient, db):
        """After refreshing, the new access token should be usable."""
        user = await create_test_user(db, "refresh_flow@example.com", "pass", "FlowUser")
        refresh_token = create_refresh_token(str(user.id))

        refresh_resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        new_access = refresh_resp.json()["access_token"]

        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "refresh_flow@example.com"
