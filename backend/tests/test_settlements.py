import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestCreateSettlement:
    async def test_create_settlement(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
            json={
                "to_user": str(user_b.id),
                "amount": "150",
                "currency": "TWD",
                "note": "Paid back",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["from_user"] == str(user_a.id)
        assert data["to_user"] == str(user_b.id)
        assert Decimal(data["amount"]) == Decimal("150")

    async def test_create_settlement_non_member(
        self, client: AsyncClient, db, group_with_members: Group, user_b: User
    ):
        outsider = await create_test_user(db, "out_s@example.com", display_name="OutS")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(outsider),
            json={
                "to_user": str(user_b.id),
                "amount": "100",
                "currency": "TWD",
            },
        )
        assert resp.status_code == 403


class TestListSettlements:
    async def test_list_empty(self, client: AsyncClient, user_a: User, group_with_members: Group):
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_settlements(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
            json={"to_user": str(user_b.id), "amount": "50", "currency": "TWD"},
        )
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestSettlementSuggestions:
    async def test_suggestions_empty_group(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_suggestions_with_expense(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        # Alice pays 300, split equally between Alice and Bob
        await client.post(
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
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        suggestions = resp.json()
        assert len(suggestions) == 1
        # Bob owes Alice 150
        assert suggestions[0]["from_user_id"] == str(user_b.id)
        assert suggestions[0]["to_user_id"] == str(user_a.id)
        assert Decimal(suggestions[0]["amount"]) == Decimal("150")

    async def test_suggestions_after_partial_settlement(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        # Alice pays 300, split equally
        await client.post(
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
        # Bob pays Alice 100
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "100", "currency": "TWD"},
        )
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        suggestions = resp.json()
        assert len(suggestions) == 1
        # Bob still owes Alice 50
        assert Decimal(suggestions[0]["amount"]) == Decimal("50")
