import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exchange_rate import ExchangeRate
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


class TestMultiCurrencyExpense:
    """測試多幣別消費功能：建立不同幣別的費用，驗證匯率快照和 base_amount。"""

    async def test_create_expense_with_foreign_currency(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """建立日圓消費，應自動查匯率並回傳 base_amount（約當台幣）。"""
        er = ExchangeRate(
            source_currency="JPY",
            target_currency="TWD",
            rate=Decimal("0.22"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Tokyo Ramen",
                "total_amount": "1000",
                "currency": "JPY",
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
        assert data["currency"] == "JPY"
        assert data["base_currency"] == "TWD"
        assert Decimal(data["exchange_rate_to_base"]) == Decimal("0.22")
        # base_amount = 1000 * 0.22 = 220
        assert Decimal(data["base_amount"]) == Decimal("220")

    async def test_create_expense_same_as_group_currency(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """群組預設幣別的消費，exchange_rate_to_base 應為 1，base_amount = total_amount。"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Local lunch",
                "total_amount": "500",
                "currency": "TWD",
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
        assert data["currency"] == "TWD"
        assert data["base_currency"] == "TWD"
        assert Decimal(data["exchange_rate_to_base"]) == Decimal("1")
        assert Decimal(data["base_amount"]) == Decimal("500")

    async def test_create_expense_usd_in_twd_group(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """建立美金消費，驗證匯率正確轉換。"""
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32.5"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "US dinner",
                "total_amount": "100",
                "currency": "USD",
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
        assert data["currency"] == "USD"
        assert Decimal(data["exchange_rate_to_base"]) == Decimal("32.5")
        # base_amount = 100 * 32.5 = 3250
        assert Decimal(data["base_amount"]) == Decimal("3250")

    async def test_update_expense_change_currency_ratio_split(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """編輯消費時切換幣別 + 改用 ratio split，應不會拋出 MissingGreenlet。"""
        # 建立 GBP→TWD 匯率紀錄
        er = ExchangeRate(
            source_currency="GBP",
            target_currency="TWD",
            rate=Decimal("41.5"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        # 先建立一筆 TWD 的 equal split 消費
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Initial expense",
                "total_amount": "300",
                "currency": "TWD",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )
        assert create_resp.status_code == 201
        expense_id = create_resp.json()["id"]

        # 用 PATCH 更新：改幣別為 GBP，split_method 改為 ratio
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
            json={
                "currency": "GBP",
                "total_amount": "100",
                "split_method": "ratio",
                "splits": [
                    {"user_id": str(user_a.id), "shares": "60"},
                    {"user_id": str(user_b.id), "shares": "40"},
                ],
            },
        )

        assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}: {update_resp.json()}"
        data = update_resp.json()
        assert data["currency"] == "GBP"
        assert data["split_method"] == "ratio"
        assert Decimal(data["total_amount"]) == Decimal("100")
        # 驗證兩個 split 加起來等於 total_amount
        total_splits = sum(Decimal(s["amount"]) for s in data["splits"])
        assert total_splits == Decimal("100")
        # 驗證每個 split 都有 user_display_name（不為空或 null）
        for split in data["splits"]:
            assert "user_display_name" in split
            assert split["user_display_name"] is not None
            assert split["user_display_name"] != ""

    async def test_update_expense_change_currency_shares_split(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """編輯消費時切換幣別 + 改用 shares split，應不會拋出 MissingGreenlet。"""
        # 建立 USD→TWD 匯率紀錄
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        # 先建立一筆 TWD 的 equal split 消費
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Initial expense",
                "total_amount": "600",
                "currency": "TWD",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )
        assert create_resp.status_code == 201
        expense_id = create_resp.json()["id"]

        # 用 PATCH 更新：改幣別為 USD，split_method 改為 shares
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
            json={
                "currency": "USD",
                "total_amount": "50",
                "split_method": "shares",
                "splits": [
                    {"user_id": str(user_a.id), "shares": "1"},
                    {"user_id": str(user_b.id), "shares": "2"},
                ],
            },
        )

        assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}: {update_resp.json()}"
        data = update_resp.json()
        assert data["currency"] == "USD"
        assert data["split_method"] == "shares"
        assert Decimal(data["total_amount"]) == Decimal("50")
        # 驗證兩個 split 加起來等於 total_amount
        total_splits = sum(Decimal(s["amount"]) for s in data["splits"])
        assert total_splits == Decimal("50")
        # 驗證每個 split 都有 user_display_name
        for split in data["splits"]:
            assert "user_display_name" in split
            assert split["user_display_name"] is not None
            assert split["user_display_name"] != ""

    async def test_update_expense_change_currency_equal_split(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """編輯消費時切換幣別但保持 equal split（對照組）。"""
        # 建立 JPY→TWD 匯率紀錄
        er = ExchangeRate(
            source_currency="JPY",
            target_currency="TWD",
            rate=Decimal("0.25"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        # 先建立一筆 TWD 的 equal split 消費
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Initial expense",
                "total_amount": "200",
                "currency": "TWD",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )
        assert create_resp.status_code == 201
        expense_id = create_resp.json()["id"]

        # 用 PATCH 更新：改幣別為 JPY，保持 equal split
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
            json={
                "currency": "JPY",
                "total_amount": "1000",
            },
        )

        assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}: {update_resp.json()}"
        data = update_resp.json()
        assert data["currency"] == "JPY"
        assert data["split_method"] == "equal"
        assert Decimal(data["total_amount"]) == Decimal("1000")
        # 驗證兩個 split 各為 500
        splits = sorted([Decimal(s["amount"]) for s in data["splits"]])
        assert splits == [Decimal("500"), Decimal("500")]
        # 驗證每個 split 都有 user_display_name
        for split in data["splits"]:
            assert "user_display_name" in split
            assert split["user_display_name"] is not None
            assert split["user_display_name"] != ""
