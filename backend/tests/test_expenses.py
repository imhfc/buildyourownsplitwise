import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestCreateExpense:
    async def test_create_equal_split(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "Dinner"
        assert Decimal(data["total_amount"]) == Decimal("300")
        assert data["split_method"] == "equal"
        assert len(data["splits"]) == 2
        # Each person should owe 150
        amounts = sorted([Decimal(s["amount"]) for s in data["splits"]])
        assert amounts == [Decimal("150"), Decimal("150")]

    async def test_create_equal_split_odd_amount(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """Test rounding: 100 / 3 people — remainder goes to first person."""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Odd split",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        total = sum(Decimal(s["amount"]) for s in data["splits"])
        assert total == Decimal("100")

    async def test_create_exact_split(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Exact",
                "total_amount": "500",
                "paid_by": str(user_a.id),
                "split_method": "exact",
                "splits": [
                    {"user_id": str(user_a.id), "amount": "200"},
                    {"user_id": str(user_b.id), "amount": "300"},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        splits = {s["user_id"]: Decimal(s["amount"]) for s in data["splits"]}
        assert splits[str(user_a.id)] == Decimal("200")
        assert splits[str(user_b.id)] == Decimal("300")

    async def test_create_exact_split_wrong_total(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Bad exact",
                "total_amount": "500",
                "paid_by": str(user_a.id),
                "split_method": "exact",
                "splits": [
                    {"user_id": str(user_a.id), "amount": "100"},
                    {"user_id": str(user_b.id), "amount": "100"},
                ],
            },
        )
        assert resp.status_code == 400
        assert "don't add up" in resp.json()["detail"]

    async def test_create_shares_split(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Shares",
                "total_amount": "900",
                "paid_by": str(user_a.id),
                "split_method": "shares",
                "splits": [
                    {"user_id": str(user_a.id), "shares": "1"},
                    {"user_id": str(user_b.id), "shares": "2"},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        total = sum(Decimal(s["amount"]) for s in data["splits"])
        assert total == Decimal("900")

    async def test_payer_not_member(
        self, client: AsyncClient, db, user_a: User, group_with_members: Group
    ):
        outsider = await create_test_user(db, "outsider2@example.com", display_name="Outsider")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "X",
                "total_amount": "100",
                "paid_by": str(outsider.id),
            },
        )
        assert resp.status_code == 400
        assert "not a group member" in resp.json()["detail"]

    async def test_non_member_cannot_create(
        self, client: AsyncClient, db, group_with_members: Group, user_a: User
    ):
        outsider = await create_test_user(db, "out3@example.com", display_name="Out")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(outsider),
            json={
                "description": "X",
                "total_amount": "100",
                "paid_by": str(user_a.id),
            },
        )
        assert resp.status_code == 403


class TestListExpenses:
    async def test_list_empty(self, client: AsyncClient, user_a: User, group_with_members: Group):
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_expenses(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        # Create an expense first
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Lunch",
                "total_amount": "200",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestDeleteExpense:
    async def test_delete_by_creator(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "ToDelete",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [{"user_id": str(user_a.id)}, {"user_id": str(user_b.id)}],
            },
        )
        expense_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 204

    async def test_delete_by_non_creator_forbidden(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "NoDelete",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [{"user_id": str(user_a.id)}, {"user_id": str(user_b.id)}],
            },
        )
        expense_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 403
