import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "securepass",
            "display_name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["display_name"] == "New User"

    async def test_register_duplicate_email(self, client: AsyncClient, db):
        await create_test_user(db, "dup@example.com")
        resp = await client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "password": "pass",
            "display_name": "Dup",
        })
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "pass",
            "display_name": "X",
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, db):
        await create_test_user(db, "login@example.com", "mypass", "LoginUser")
        resp = await client.post("/api/v1/auth/login", json={
            "email": "login@example.com",
            "password": "mypass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["user"]["email"] == "login@example.com"

    async def test_login_wrong_password(self, client: AsyncClient, db):
        await create_test_user(db, "wrong@example.com", "correct")
        resp = await client.post("/api/v1/auth/login", json={
            "email": "wrong@example.com",
            "password": "incorrect",
        })
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "ghost@example.com",
            "password": "pass",
        })
        assert resp.status_code == 401


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


class TestChangePassword:
    async def test_change_password_success(self, client: AsyncClient, db):
        """Email 用戶可以成功更改密碼。"""
        user = await create_test_user(db, "pwchange@example.com", "oldpass123")
        resp = await client.patch(
            "/api/v1/auth/me/password",
            headers=auth_header(user),
            json={"old_password": "oldpass123", "new_password": "newpass456"},
        )
        assert resp.status_code == 204

        # 用舊密碼登入應失敗
        login_fail = await client.post("/api/v1/auth/login", json={
            "email": "pwchange@example.com",
            "password": "oldpass123",
        })
        assert login_fail.status_code == 401

        # 用新密碼登入應成功
        login_ok = await client.post("/api/v1/auth/login", json={
            "email": "pwchange@example.com",
            "password": "newpass456",
        })
        assert login_ok.status_code == 200

    async def test_change_password_wrong_old_password(self, client: AsyncClient, db):
        """舊密碼錯誤時回傳 400。"""
        user = await create_test_user(db, "pwwrong@example.com", "correct123")
        resp = await client.patch(
            "/api/v1/auth/me/password",
            headers=auth_header(user),
            json={"old_password": "wrong", "new_password": "newpass"},
        )
        assert resp.status_code == 400

    async def test_change_password_google_user_forbidden(self, client: AsyncClient, db):
        """Google 用戶嘗試改密碼應回傳 403。"""
        from app.models.user import User
        google_user = User(
            email="google@example.com",
            display_name="Google User",
            auth_provider="google",
            auth_provider_id="google-123",
        )
        db.add(google_user)
        await db.flush()

        resp = await client.patch(
            "/api/v1/auth/me/password",
            headers=auth_header(google_user),
            json={"old_password": "any", "new_password": "any"},
        )
        assert resp.status_code == 403

    async def test_change_password_requires_auth(self, client: AsyncClient):
        """未認證時回傳 403。"""
        resp = await client.patch(
            "/api/v1/auth/me/password",
            json={"old_password": "x", "new_password": "y"},
        )
        assert resp.status_code == 403
