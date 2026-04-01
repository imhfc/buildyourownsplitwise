import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestCreateInvite:
    """Test POST /api/v1/groups/{group_id}/invite"""

    async def test_create_invite_as_member(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """Member呼叫應該成功，回傳 invite_token 和 created_at"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "invite_token" in data
        assert "created_at" in data
        assert len(data["invite_token"]) == 32  # token_hex(16) = 32 chars

    async def test_create_invite_idempotent(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """重複呼叫應該回傳同一個 token（冪等）"""
        # 第一次呼叫
        resp1 = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp1.status_code == 200
        token1 = resp1.json()["invite_token"]

        # 第二次呼叫
        resp2 = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp2.status_code == 200
        token2 = resp2.json()["invite_token"]

        assert token1 == token2

    async def test_create_invite_non_member_forbidden(
        self, client: AsyncClient, db: AsyncSession, group_with_members: Group
    ):
        """非成員呼叫應該回傳 403"""
        outsider = await create_test_user(db, "outsider@example.com", display_name="Outsider")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(outsider),
        )
        assert resp.status_code == 403

    async def test_create_invite_no_auth(self, client: AsyncClient, group_with_members: Group):
        """未認證應該回傳 403"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
        )
        assert resp.status_code == 403

    async def test_create_invite_for_nonexistent_group(
        self, client: AsyncClient, user_a: User
    ):
        """非存在的群組應該回傳 403"""
        import uuid
        fake_group_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/groups/{fake_group_id}/invite",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 403


class TestRevokeInvite:
    """Test DELETE /api/v1/groups/{group_id}/invite"""

    async def test_revoke_invite_as_admin(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """Admin 呼叫應該成功，回傳 204"""
        # 先建立 invite token
        resp_create = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_create.status_code == 200
        token_before = resp_create.json()["invite_token"]

        # 撤銷 token
        resp_revoke = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_revoke.status_code == 204

        # 確認 token 已被撤銷（嘗試用舊 token 應該失敗）
        resp_info = await client.get(
            f"/api/v1/invite/{token_before}",
            headers=auth_header(user_a),
        )
        assert resp_info.status_code == 404

    async def test_revoke_invite_as_member_forbidden(
        self, client: AsyncClient, user_b: User, group_with_members: Group
    ):
        """Member 呼叫應該回傳 403"""
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 403

    async def test_revoke_invite_no_auth(self, client: AsyncClient, group_with_members: Group):
        """未認證應該回傳 403"""
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/invite",
        )
        assert resp.status_code == 403


class TestRegenerateInvite:
    """Test POST /api/v1/groups/{group_id}/invite/regenerate"""

    async def test_regenerate_invite_as_admin(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """Admin 呼叫應該成功，回傳新 token（與舊的不同）"""
        # 建立第一個 token
        resp1 = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp1.status_code == 200
        token1 = resp1.json()["invite_token"]

        # 重新生成 token
        resp_regen = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite/regenerate",
            headers=auth_header(user_a),
        )
        assert resp_regen.status_code == 200
        token2 = resp_regen.json()["invite_token"]

        # 確認新舊 token 不同
        assert token1 != token2
        assert len(token2) == 32

        # 確認舊 token 已失效
        resp_old_info = await client.get(
            f"/api/v1/invite/{token1}",
            headers=auth_header(user_a),
        )
        assert resp_old_info.status_code == 404

        # 確認新 token 有效
        resp_new_info = await client.get(
            f"/api/v1/invite/{token2}",
            headers=auth_header(user_a),
        )
        assert resp_new_info.status_code == 200

    async def test_regenerate_invite_as_member_forbidden(
        self, client: AsyncClient, user_b: User, group_with_members: Group
    ):
        """Member 呼叫應該回傳 403"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite/regenerate",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 403

    async def test_regenerate_invite_no_auth(
        self, client: AsyncClient, group_with_members: Group
    ):
        """未認證應該回傳 403"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite/regenerate",
        )
        assert resp.status_code == 403


class TestGetInviteInfo:
    """Test GET /api/v1/invite/{token}"""

    async def test_get_invite_info_valid_token(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """有效 token 應該回傳群組基本資訊"""
        # 建立 token
        resp_create = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_create.status_code == 200
        token = resp_create.json()["invite_token"]

        # 查詢 invite info
        resp_info = await client.get(
            f"/api/v1/invite/{token}",
            headers=auth_header(user_a),
        )
        assert resp_info.status_code == 200
        data = resp_info.json()
        assert data["group_id"] == str(group_with_members.id)
        assert data["group_name"] == "Test Group"
        assert data["group_description"] == "For testing"
        assert data["member_count"] == 2  # user_a + user_b

    async def test_get_invite_info_invalid_token(
        self, client: AsyncClient, user_a: User
    ):
        """無效 token 應該回傳 404"""
        resp = await client.get(
            f"/api/v1/invite/invalid_token_123456789",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 404

    async def test_get_invite_info_no_auth(self, client: AsyncClient):
        """未認證應該回傳 403"""
        resp = await client.get(
            f"/api/v1/invite/any_token",
        )
        assert resp.status_code == 403


class TestAcceptInvite:
    """Test POST /api/v1/invite/{token}/accept"""

    async def test_accept_invite_non_member(
        self, client: AsyncClient, db: AsyncSession, user_a: User, group_with_members: Group
    ):
        """有效 token + 非成員應該成功，回傳 group_id"""
        # 建立 token
        resp_create = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_create.status_code == 200
        token = resp_create.json()["invite_token"]

        # 建立新使用者
        outsider = await create_test_user(db, "outsider@example.com", display_name="Outsider")

        # 接受邀請
        resp_accept = await client.post(
            f"/api/v1/invite/{token}/accept",
            headers=auth_header(outsider),
        )
        assert resp_accept.status_code == 200
        data = resp_accept.json()
        assert data["group_id"] == str(group_with_members.id)

    async def test_accept_invite_already_member(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """已是成員應該回傳 409 Conflict"""
        # 建立 token
        resp_create = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_create.status_code == 200
        token = resp_create.json()["invite_token"]

        # user_a 已經是成員，嘗試再次接受邀請
        resp_accept = await client.post(
            f"/api/v1/invite/{token}/accept",
            headers=auth_header(user_a),
        )
        assert resp_accept.status_code == 409

    async def test_accept_invite_invalid_token(
        self, client: AsyncClient, user_a: User
    ):
        """無效 token 應該回傳 404"""
        resp = await client.post(
            f"/api/v1/invite/invalid_token_123456789/accept",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 404

    async def test_accept_invite_no_auth(self, client: AsyncClient):
        """未認證應該回傳 403"""
        resp = await client.post(
            f"/api/v1/invite/any_token/accept",
        )
        assert resp.status_code == 403

    async def test_accept_invite_revoked_token(
        self, client: AsyncClient, db: AsyncSession, user_a: User, group_with_members: Group
    ):
        """撤銷的 token 應該無法使用"""
        # 建立 token
        resp_create = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_create.status_code == 200
        token = resp_create.json()["invite_token"]

        # 撤銷 token
        resp_revoke = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_revoke.status_code == 204

        # 建立新使用者
        outsider = await create_test_user(db, "outsider@example.com", display_name="Outsider")

        # 嘗試用撤銷的 token 接受邀請，應該失敗
        resp_accept = await client.post(
            f"/api/v1/invite/{token}/accept",
            headers=auth_header(outsider),
        )
        assert resp_accept.status_code == 404


class TestInviteWorkflow:
    """Integration tests for complete invite workflow"""

    async def test_complete_invite_workflow(
        self, client: AsyncClient, db: AsyncSession, user_a: User, group_with_members: Group
    ):
        """完整的邀請流程：建立 → 查詢 → 接受"""
        # Step 1: Admin 建立邀請 token
        resp_create = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp_create.status_code == 200
        token = resp_create.json()["invite_token"]

        # Step 2: 未認證使用者查詢邀請資訊（需要認證）
        new_user = await create_test_user(db, "newmember@example.com", display_name="NewMember")
        resp_info = await client.get(
            f"/api/v1/invite/{token}",
            headers=auth_header(new_user),
        )
        assert resp_info.status_code == 200
        invite_info = resp_info.json()
        assert invite_info["group_name"] == "Test Group"

        # Step 3: 新使用者接受邀請
        resp_accept = await client.post(
            f"/api/v1/invite/{token}/accept",
            headers=auth_header(new_user),
        )
        assert resp_accept.status_code == 200

        # Step 4: 驗證新使用者已加入群組
        resp_get_group = await client.get(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(new_user),
        )
        assert resp_get_group.status_code == 200
        group_data = resp_get_group.json()
        member_count = len(group_data["members"])
        assert member_count == 3  # user_a + user_b + new_user

    async def test_invite_link_expires_after_regenerate(
        self, client: AsyncClient, db: AsyncSession, user_a: User, group_with_members: Group
    ):
        """舊的邀請 token 在重新生成後應該失效"""
        # Step 1: 建立第一個 token
        resp1 = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp1.status_code == 200
        token1 = resp1.json()["invite_token"]

        # Step 2: 重新生成 token
        resp_regen = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite/regenerate",
            headers=auth_header(user_a),
        )
        assert resp_regen.status_code == 200
        token2 = resp_regen.json()["invite_token"]

        # Step 3: 建立新使用者，嘗試用舊 token
        outsider = await create_test_user(db, "outsider@example.com", display_name="Outsider")
        resp_old = await client.post(
            f"/api/v1/invite/{token1}/accept",
            headers=auth_header(outsider),
        )
        assert resp_old.status_code == 404

        # Step 4: 用新 token 應該成功
        resp_new = await client.post(
            f"/api/v1/invite/{token2}/accept",
            headers=auth_header(outsider),
        )
        assert resp_new.status_code == 200
