import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestGroupBalances:
    """GET /api/v1/balances/groups/{group_id}"""

    async def test_group_balances_empty(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """無費用時回傳空的 by_currency。"""
        resp = await client.get(
            f"/api/v1/balances/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["group_id"] == str(group_with_members.id)
        assert data["group_name"] == "Test Group"
        assert data["by_currency"] == []

    async def test_group_balances_with_expense(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """建立費用後應正確回傳各人淨餘額。"""
        # Alice 付 300，均分
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
            f"/api/v1/balances/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["by_currency"]) == 1
        twd = data["by_currency"][0]
        assert twd["currency"] == "TWD"
        balances = {b["user_id"]: Decimal(b["balance"]) for b in twd["balances"]}
        assert balances[str(user_a.id)] == Decimal("150")
        assert balances[str(user_b.id)] == Decimal("-150")

    async def test_group_balances_non_member_forbidden(
        self, client: AsyncClient, db, group_with_members: Group
    ):
        """非群組成員查詢應回傳 403。"""
        outsider = await create_test_user(db, "outsider@example.com", display_name="Out")
        resp = await client.get(
            f"/api/v1/balances/groups/{group_with_members.id}",
            headers=auth_header(outsider),
        )
        assert resp.status_code == 403

    async def test_group_balances_no_auth(
        self, client: AsyncClient, group_with_members: Group
    ):
        """未認證應回傳 403。"""
        resp = await client.get(
            f"/api/v1/balances/groups/{group_with_members.id}",
        )
        assert resp.status_code == 403


class TestOverallBalances:
    """GET /api/v1/balances"""

    async def test_overall_balances_empty(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """無費用時 totals_by_currency 應為空。"""
        resp = await client.get(
            "/api/v1/balances",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["totals_by_currency"] == []
        assert len(data["by_group"]) >= 1  # user_a 至少在一個群組

    async def test_overall_balances_with_expense(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """有費用時應正確彙總各幣別的應收/應付。"""
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
            "/api/v1/balances",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["totals_by_currency"]) == 1
        twd_total = data["totals_by_currency"][0]
        assert twd_total["currency"] == "TWD"
        assert Decimal(twd_total["owed_to_you"]) == Decimal("100")
        assert Decimal(twd_total["you_owe"]) == Decimal("0")
        assert Decimal(twd_total["net_balance"]) == Decimal("100")

    async def test_overall_balances_no_auth(self, client: AsyncClient):
        """未認證應回傳 403。"""
        resp = await client.get("/api/v1/balances")
        assert resp.status_code == 403
