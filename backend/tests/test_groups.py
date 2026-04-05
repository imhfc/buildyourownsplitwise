import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group, GroupMember
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestCreateGroup:
    async def test_create_group(self, client: AsyncClient, user_a: User):
        resp = await client.post(
            "/api/v1/groups",
            headers=auth_header(user_a),
            json={"name": "Trip", "description": "Japan trip"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Trip"
        assert data["default_currency"] == "TWD"
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "admin"

    async def test_create_group_no_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/groups", json={"name": "X"})
        assert resp.status_code == 403


class TestListGroups:
    async def test_list_my_groups(self, client: AsyncClient, user_a: User, group_with_members: Group):
        resp = await client.get("/api/v1/groups", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Test Group"
        assert data[0]["member_count"] == 2


class TestGetGroup:
    async def test_get_group_as_member(self, client: AsyncClient, user_a: User, group_with_members: Group):
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Group"

    async def test_get_group_non_member(self, client: AsyncClient, db, group_with_members: Group):
        outsider = await create_test_user(db, "outsider@example.com", display_name="Outsider")
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(outsider),
        )
        assert resp.status_code == 403


class TestUpdateGroup:
    async def test_update_group_as_admin(self, client: AsyncClient, user_a: User, group_with_members: Group):
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_a),
            json={"name": "Renamed Group"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Group"

    async def test_update_group_as_member_allowed(
        self, client: AsyncClient, user_b: User, group_with_members: Group
    ):
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_b),
            json={"name": "Updated by member"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated by member"


class TestDeleteGroup:
    async def test_delete_group_as_admin(self, client: AsyncClient, user_a: User, group_with_members: Group):
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 204

    async def test_delete_group_as_member_forbidden(
        self, client: AsyncClient, user_b: User, group_with_members: Group
    ):
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 403


class TestGroupMembers:
    async def test_add_member(self, client: AsyncClient, db, user_a: User, group_with_members: Group):
        new_user = await create_test_user(db, "new_member@example.com", display_name="NewMember")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(new_user.id)},
        )
        assert resp.status_code == 201

    async def test_add_member_already_exists(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_b.id)},
        )
        assert resp.status_code == 400
        assert "already a member" in resp.json()["detail"]

    async def test_add_nonexistent_user(self, client: AsyncClient, user_a: User, group_with_members: Group):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 404

    async def test_remove_member_as_admin(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 204

    async def test_remove_self(self, client: AsyncClient, user_b: User, group_with_members: Group):
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 204

    async def test_member_cannot_remove_others(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_a.id}",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 403
