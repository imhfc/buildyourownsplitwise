from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.group import Group
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestExpenseSoftDelete:
    async def test_delete_expense_sets_deleted_at(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """刪除消費應設定 deleted_at 而非物理刪除。"""
        # Arrange: 先建立消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "soft delete test",
                "total_amount": "100.00",
                "paid_by": str(user_a.id),
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]

        # Act: 刪除消費
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 204

        # Assert: 驗證 DB 中仍存在但有 deleted_at
        result = await db.execute(select(Expense).where(Expense.id == expense_id))
        expense = result.scalar_one()
        assert expense.deleted_at is not None

    async def test_deleted_expense_not_in_list(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """已刪除消費不應出現在列表中。"""
        # Arrange: 建立消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "hidden expense",
                "total_amount": "200.00",
                "paid_by": str(user_a.id),
            },
        )
        expense_id = resp.json()["id"]

        # Act: 刪除消費
        await client.delete(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
        )

        # Assert: 列表不應包含已刪除的消費
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert expense_id not in ids

    async def test_delete_expense_permission_only_creator(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """只有建立者可以刪除消費。"""
        # Arrange: user_a 建立消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "created by alice",
                "total_amount": "150.00",
                "paid_by": str(user_a.id),
            },
        )
        expense_id = resp.json()["id"]

        # Act: user_b (non-creator) 嘗試刪除
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_b),
        )

        # Assert: 應回傳 403 Forbidden
        assert resp.status_code == 403


class TestGroupSoftDelete:
    async def test_delete_group_sets_deleted_at(
        self, client: AsyncClient, db: AsyncSession, user_a, group_with_members
    ):
        """刪除群組應設定 deleted_at 而非物理刪除。"""
        # Act: 刪除群組
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 204

        # Assert: 驗證 DB 中仍存在但有 deleted_at
        result = await db.execute(select(Group).where(Group.id == group_with_members.id))
        group = result.scalar_one()
        assert group.deleted_at is not None

    async def test_deleted_group_not_in_list(
        self, client: AsyncClient, user_a, group_with_members
    ):
        """已刪除群組不應出現在列表中。"""
        # Act: 刪除群組
        await client.delete(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )

        # Assert: 列表不應包含已刪除群組
        resp = await client.get("/api/v1/groups", headers=auth_header(user_a))
        assert resp.status_code == 200
        ids = [str(g["id"]) for g in resp.json()]
        assert str(group_with_members.id) not in ids

    async def test_deleted_group_members_cannot_access(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """已刪除群組的成員無法存取。"""
        # Act: user_a 刪除群組
        await client.delete(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )

        # Assert: user_b 嘗試存取已刪除群組的消費應回傳 403
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 403

    async def test_delete_group_only_admin(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """只有管理員可以刪除群組。"""
        # Act: user_b (member, not admin) 嘗試刪除群組
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_b),
        )

        # Assert: 應回傳 403 Forbidden
        assert resp.status_code == 403
