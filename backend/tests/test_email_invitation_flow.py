"""測試 email 邀請完整流程：建立、查詢待處理、用 token 回應、用 ID 回應。"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_invitation import EmailInvitation
from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _create_email_invitation(db, group, inviter, email="invited@example.com"):
    """直接在 DB 建立一筆 pending email invitation，回傳 EmailInvitation。"""
    now = datetime.now(timezone.utc)
    inv = EmailInvitation(
        group_id=group.id,
        inviter_id=inviter.id,
        email=email,
        token=f"tok-{uuid.uuid4().hex[:16]}",
        status="pending",
        created_at=now,
        expires_at=now + timedelta(days=7),
    )
    db.add(inv)
    await db.flush()
    return inv


# ---------------------------------------------------------------------------
# GET /invite/email/pending
# ---------------------------------------------------------------------------

class TestGetPendingInvitations:
    async def test_no_pending(
        self, client: AsyncClient, user_a: User
    ):
        resp = await client.get(
            "/api/v1/invite/email/pending",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_has_pending(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group
    ):
        """user_b 有 email，建立邀請後應出現在 pending 列表。"""
        await _create_email_invitation(db, group_with_members, user_a, email="bob@example.com")
        resp = await client.get(
            "/api/v1/invite/email/pending",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        data = resp.json()[0]
        assert data["group_name"] == "Test Group"
        assert data["inviter_name"] == user_a.display_name

    async def test_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/invite/email/pending")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /invite/email/by-token/{token}
# ---------------------------------------------------------------------------

class TestGetByToken:
    async def test_valid_token(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group
    ):
        inv = await _create_email_invitation(db, group_with_members, user_a, email="bob@example.com")
        resp = await client.get(
            f"/api/v1/invite/email/by-token/{inv.token}",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["group_name"] == "Test Group"

    async def test_invalid_token(
        self, client: AsyncClient, user_a: User
    ):
        resp = await client.get(
            "/api/v1/invite/email/by-token/nonexistent-token",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 404

    async def test_expired_token(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group
    ):
        """過期的邀請應回傳 400。"""
        now = datetime.now(timezone.utc)
        inv = EmailInvitation(
            group_id=group_with_members.id,
            inviter_id=user_a.id,
            email="bob@example.com",
            token=f"expired-{uuid.uuid4().hex[:12]}",
            status="pending",
            created_at=now - timedelta(days=14),
            expires_at=now - timedelta(days=1),
        )
        db.add(inv)
        await db.flush()

        resp = await client.get(
            f"/api/v1/invite/email/by-token/{inv.token}",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /invite/email/by-token/{token}/respond
# ---------------------------------------------------------------------------

class TestRespondByToken:
    async def test_accept_by_token(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        """用 token 接受邀請，應加入群組。"""
        new_user = await create_test_user(db, "newguy@example.com", display_name="NewGuy")
        inv = await _create_email_invitation(db, group_with_members, user_a, email="newguy@example.com")

        resp = await client.post(
            f"/api/v1/invite/email/by-token/{inv.token}/respond",
            headers=auth_header(new_user),
            json={"action": "accept"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["group_id"] == str(group_with_members.id)

    async def test_decline_by_token(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        new_user = await create_test_user(db, "decline@example.com", display_name="Decliner")
        inv = await _create_email_invitation(db, group_with_members, user_a, email="decline@example.com")

        resp = await client.post(
            f"/api/v1/invite/email/by-token/{inv.token}/respond",
            headers=auth_header(new_user),
            json={"action": "decline"},
        )
        assert resp.status_code == 200
        assert "declined" in resp.json()["detail"].lower()

    async def test_respond_wrong_email(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        """email 不符的使用者不能回應。"""
        wrong_user = await create_test_user(db, "wrong@example.com", display_name="Wrong")
        inv = await _create_email_invitation(db, group_with_members, user_a, email="correct@example.com")

        resp = await client.post(
            f"/api/v1/invite/email/by-token/{inv.token}/respond",
            headers=auth_header(wrong_user),
            json={"action": "accept"},
        )
        assert resp.status_code == 403

    async def test_respond_invalid_token(
        self, client: AsyncClient, user_a: User
    ):
        resp = await client.post(
            "/api/v1/invite/email/by-token/bad-token/respond",
            headers=auth_header(user_a),
            json={"action": "accept"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /invite/email/{invitation_id}/respond
# ---------------------------------------------------------------------------

class TestRespondById:
    async def test_accept_by_id(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        new_user = await create_test_user(db, "byid@example.com", display_name="ByID")
        inv = await _create_email_invitation(db, group_with_members, user_a, email="byid@example.com")

        resp = await client.post(
            f"/api/v1/invite/email/{inv.id}/respond",
            headers=auth_header(new_user),
            json={"action": "accept"},
        )
        assert resp.status_code == 200
        assert resp.json()["group_id"] == str(group_with_members.id)

    async def test_decline_by_id(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        new_user = await create_test_user(db, "byid2@example.com", display_name="ByID2")
        inv = await _create_email_invitation(db, group_with_members, user_a, email="byid2@example.com")

        resp = await client.post(
            f"/api/v1/invite/email/{inv.id}/respond",
            headers=auth_header(new_user),
            json={"action": "decline"},
        )
        assert resp.status_code == 200

    async def test_respond_not_found(
        self, client: AsyncClient, user_a: User
    ):
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/invite/email/{fake_id}/respond",
            headers=auth_header(user_a),
            json={"action": "accept"},
        )
        assert resp.status_code == 404

    async def test_respond_already_accepted(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        """已接受的邀請再回應應報錯。"""
        new_user = await create_test_user(db, "dup@example.com", display_name="Dup")
        inv = await _create_email_invitation(db, group_with_members, user_a, email="dup@example.com")

        # 第一次接受
        await client.post(
            f"/api/v1/invite/email/{inv.id}/respond",
            headers=auth_header(new_user),
            json={"action": "accept"},
        )
        # 第二次應失敗
        resp = await client.post(
            f"/api/v1/invite/email/{inv.id}/respond",
            headers=auth_header(new_user),
            json={"action": "accept"},
        )
        assert resp.status_code == 400
