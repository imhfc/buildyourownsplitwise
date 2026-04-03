"""測試費用單筆查詢 (GET) 和編輯 (PATCH) 端點 — 補充 test_expenses.py 的缺口。"""
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _create_expense(client, group_id, user_a, user_b):
    """快速建立一筆均分費用，回傳 expense JSON。"""
    resp = await client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=auth_header(user_a),
        json={
            "description": "Test Expense",
            "total_amount": "400",
            "paid_by": str(user_a.id),
            "split_method": "equal",
            "splits": [
                {"user_id": str(user_a.id)},
                {"user_id": str(user_b.id)},
            ],
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# GET /{expense_id}
# ---------------------------------------------------------------------------

class TestGetExpense:
    async def test_get_expense_success(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        expense = await _create_expense(client, group_with_members.id, user_a, user_b)
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense['id']}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == expense["id"]
        assert data["description"] == "Test Expense"
        assert len(data["splits"]) == 2

    async def test_get_expense_by_other_member(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """群組內其他成員也能查詢。"""
        expense = await _create_expense(client, group_with_members.id, user_a, user_b)
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense['id']}",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 200

    async def test_get_expense_not_found(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        fake_id = uuid.uuid4()
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses/{fake_id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 404

    async def test_get_expense_non_member_forbidden(
        self, client: AsyncClient, db, user_a: User, user_b: User, group_with_members: Group
    ):
        expense = await _create_expense(client, group_with_members.id, user_a, user_b)
        outsider = await create_test_user(db, "outsider@example.com", display_name="Out")
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense['id']}",
            headers=auth_header(outsider),
        )
        assert resp.status_code == 403

    async def test_get_expense_no_auth(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        expense = await _create_expense(client, group_with_members.id, user_a, user_b)
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense['id']}",
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /{expense_id}
# ---------------------------------------------------------------------------

class TestUpdateExpense:
    async def test_update_description(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        expense = await _create_expense(client, group_with_members.id, user_a, user_b)
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense['id']}",
            headers=auth_header(user_a),
            json={"description": "Updated Expense"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated Expense"

    async def test_update_amount_recalculates_splits(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        expense = await _create_expense(client, group_with_members.id, user_a, user_b)
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense['id']}",
            headers=auth_header(user_a),
            json={"total_amount": "600"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["total_amount"]) == Decimal("600")
        total_splits = sum(Decimal(s["amount"]) for s in data["splits"])
        assert total_splits == Decimal("600")

    async def test_update_not_found(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        fake_id = uuid.uuid4()
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{fake_id}",
            headers=auth_header(user_a),
            json={"description": "Nope"},
        )
        assert resp.status_code == 404

    async def test_update_by_uninvolved_member_forbidden(
        self, client: AsyncClient, db, user_a: User, user_b: User, group_with_members: Group
    ):
        """非付款人也非分攤者的第三人不能編輯。"""
        from app.models.group import GroupMember
        user_c = await create_test_user(db, "charlie2@example.com", display_name="Charlie")
        member_c = GroupMember(group_id=group_with_members.id, user_id=user_c.id, role="member")
        db.add(member_c)
        await db.flush()

        expense = await _create_expense(client, group_with_members.id, user_a, user_b)
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense['id']}",
            headers=auth_header(user_c),
            json={"description": "Hack"},
        )
        assert resp.status_code == 403
