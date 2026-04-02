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


def _get_by_currency_suggestions(data: dict) -> list[dict]:
    """從分幣別回傳中取出所有 suggestions（攤平）"""
    result = []
    for group in (data.get("by_currency") or []):
        result.extend(group["suggestions"])
    return result


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
        assert data["status"] == "pending"

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


class TestConfirmSettlement:
    async def test_confirm_settlement(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        # user_a 建立結算給 user_b
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
            json={"to_user": str(user_b.id), "amount": "100", "currency": "TWD"},
        )
        settlement_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "pending"

        # user_b（收款方）確認
        confirm_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_b),
        )
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "confirmed"
        assert confirm_resp.json()["confirmed_at"] is not None

    async def test_confirm_by_non_payee_forbidden(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
            json={"to_user": str(user_b.id), "amount": "100", "currency": "TWD"},
        )
        settlement_id = create_resp.json()["id"]

        # user_a（付款方）不能自己確認
        confirm_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )
        assert confirm_resp.status_code == 403


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

    async def test_list_filter_by_status(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
            json={"to_user": str(user_b.id), "amount": "50", "currency": "TWD"},
        )
        # pending filter
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements?status=pending",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        # confirmed filter (should be empty)
        resp2 = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements?status=confirmed",
            headers=auth_header(user_a),
        )
        assert resp2.status_code == 200
        assert len(resp2.json()) == 0


class TestSettlementSuggestions:
    async def test_suggestions_empty_group(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "by_currency"
        assert data["by_currency"] == []

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
        data = resp.json()
        assert data["mode"] == "by_currency"
        suggestions = _get_by_currency_suggestions(data)
        assert len(suggestions) == 1
        # Bob owes Alice 150
        assert suggestions[0]["from_user_id"] == str(user_b.id)
        assert suggestions[0]["to_user_id"] == str(user_a.id)
        assert Decimal(suggestions[0]["amount"]) == Decimal("150")

    async def test_suggestions_after_confirmed_settlement(
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
        # Bob pays Alice 100 (pending)
        create_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "100", "currency": "TWD"},
        )
        settlement_id = create_resp.json()["id"]

        # pending settlement 不計入餘額 → Bob still owes 150
        resp_before = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
        )
        suggestions_before = _get_by_currency_suggestions(resp_before.json())
        assert len(suggestions_before) == 1
        assert Decimal(suggestions_before[0]["amount"]) == Decimal("150")

        # Alice（收款方）確認結算
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # confirmed 後 → Bob owes 50
        resp_after = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
        )
        suggestions_after = _get_by_currency_suggestions(resp_after.json())
        assert len(suggestions_after) == 1
        assert Decimal(suggestions_after[0]["amount"]) == Decimal("50")


class TestMultiCurrencySettlement:
    """測試多幣別結算"""

    async def test_suggestions_by_currency(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """分幣別模式：TWD 和 USD 費用各自獨立結算"""
        # expense 建立時需要匯率快照（即使分幣別結算不需要）
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        # Alice 付 TWD 300，均分
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Local dinner",
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
        # Bob 付 USD 10，均分
        usd_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_b),
            json={
                "description": "US snacks",
                "total_amount": "10",
                "currency": "USD",
                "paid_by": str(user_b.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )
        assert usd_resp.status_code == 201
        assert usd_resp.json()["currency"] == "USD"

        # 分幣別：TWD 組 Bob 欠 Alice 150, USD 組 Alice 欠 Bob 5
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "by_currency"
        assert len(data["by_currency"]) == 2

        by_cur = {g["currency"]: g["suggestions"] for g in data["by_currency"]}
        # TWD: Bob owes Alice 150
        assert len(by_cur["TWD"]) == 1
        assert by_cur["TWD"][0]["from_user_id"] == str(user_b.id)
        assert Decimal(by_cur["TWD"][0]["amount"]) == Decimal("150")
        # USD: Alice owes Bob 5
        assert len(by_cur["USD"]) == 1
        assert by_cur["USD"][0]["from_user_id"] == str(user_a.id)
        assert Decimal(by_cur["USD"][0]["amount"]) == Decimal("5")

    async def test_suggestions_unified_currency(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """統一幣別模式：全部轉成 TWD 計算"""
        # 插入 USD→TWD 匯率
        er = ExchangeRate(
            source_currency="USD",
            target_currency="TWD",
            rate=Decimal("32"),
            source="taiwan_bank",
            fetched_at=datetime.now(timezone.utc),
        )
        db.add(er)
        await db.flush()

        # Alice 付 TWD 300，均分
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Local dinner",
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
        # Bob 付 USD 10，均分（= TWD 320）
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_b),
            json={
                "description": "US snacks",
                "total_amount": "10",
                "currency": "USD",
                "paid_by": str(user_b.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )

        # 統一幣別 TWD：
        # Alice 淨額 = 300 - 310 = -10, Bob 淨額 = 320 - 310 = +10
        # Alice 應付 Bob TWD 10
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/suggestions",
            headers=auth_header(user_a),
            params={"unified_currency": "TWD"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "unified"
        suggestions = data["unified"]["suggestions"]
        assert len(suggestions) == 1
        assert suggestions[0]["from_user_id"] == str(user_a.id)
        assert suggestions[0]["to_user_id"] == str(user_b.id)
        assert Decimal(suggestions[0]["amount"]) == Decimal("10")
        assert suggestions[0]["currency"] == "TWD"
        # 應包含匯率資訊
        assert len(data["unified"]["exchange_rates"]) == 1
        assert data["unified"]["exchange_rates"][0]["from_currency"] == "USD"


class TestPendingSettlements:
    async def test_list_pending(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        # user_a 建立結算給 user_b
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
            json={"to_user": str(user_b.id), "amount": "100", "currency": "TWD"},
        )
        # user_b 查看待確認列表
        resp = await client.get(
            "/api/v1/settlements/pending",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["status"] == "pending"

    async def test_pending_empty_for_payer(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_a),
            json={"to_user": str(user_b.id), "amount": "100", "currency": "TWD"},
        )
        # user_a（付款方）不應看到自己建立的待確認
        resp = await client.get(
            "/api/v1/settlements/pending",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0
