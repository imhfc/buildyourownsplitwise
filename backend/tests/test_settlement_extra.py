"""補充結算測試：拒絕結算、pairwise 明細、付款提醒。"""
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

async def _create_settlement(client, group_id, from_user, to_user):
    resp = await client.post(
        f"/api/v1/groups/{group_id}/settlements",
        headers=auth_header(from_user),
        json={"to_user": str(to_user.id), "amount": "100", "currency": "TWD"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_expense(client, group_id, payer, other):
    resp = await client.post(
        f"/api/v1/groups/{group_id}/expenses",
        headers=auth_header(payer),
        json={
            "description": "Dinner",
            "total_amount": "300",
            "paid_by": str(payer.id),
            "split_method": "equal",
            "splits": [
                {"user_id": str(payer.id)},
                {"user_id": str(other.id)},
            ],
        },
    )
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# PATCH /{settlement_id}/reject
# ---------------------------------------------------------------------------

class TestRejectSettlement:
    async def test_reject_by_payee(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        settlement = await _create_settlement(client, group_with_members.id, user_a, user_b)
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement['id']}/reject",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    async def test_reject_by_payer_forbidden(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        settlement = await _create_settlement(client, group_with_members.id, user_a, user_b)
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement['id']}/reject",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 403

    async def test_reject_already_confirmed(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        settlement = await _create_settlement(client, group_with_members.id, user_a, user_b)
        # 先確認
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement['id']}/confirm",
            headers=auth_header(user_b),
        )
        # 再嘗試拒絕
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement['id']}/reject",
            headers=auth_header(user_b),
        )
        assert resp.status_code == 400

    async def test_reject_not_found(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        fake_id = uuid.uuid4()
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{fake_id}/reject",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /details (pairwise)
# ---------------------------------------------------------------------------

class TestPairwiseDetails:
    async def test_details_empty(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/details",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_details_with_expense(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        await _create_expense(client, group_with_members.id, user_a, user_b)
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/details",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["from_user_id"] == str(user_b.id)
        assert data[0]["to_user_id"] == str(user_a.id)
        assert Decimal(data[0]["amount"]) == Decimal("150")

    async def test_details_non_member_forbidden(
        self, client: AsyncClient, db, group_with_members: Group
    ):
        outsider = await create_test_user(db, "outsider@example.com", display_name="Out")
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/settlements/details",
            headers=auth_header(outsider),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /reminders
# ---------------------------------------------------------------------------

class TestPaymentReminder:
    async def test_send_reminder_success(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements/reminders",
            headers=auth_header(user_a),
            json={
                "to_user": str(user_b.id),
                "amount": "150",
                "currency": "TWD",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["from_user"] == str(user_a.id)
        assert data["to_user"] == str(user_b.id)
        assert Decimal(data["amount"]) == Decimal("150")

    async def test_remind_self_error(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements/reminders",
            headers=auth_header(user_a),
            json={
                "to_user": str(user_a.id),
                "amount": "100",
                "currency": "TWD",
            },
        )
        assert resp.status_code == 400

    async def test_remind_non_member_forbidden(
        self, client: AsyncClient, db, user_a: User, group_with_members: Group
    ):
        outsider = await create_test_user(db, "outsider@example.com", display_name="Out")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements/reminders",
            headers=auth_header(user_a),
            json={
                "to_user": str(outsider.id),
                "amount": "100",
                "currency": "TWD",
            },
        )
        assert resp.status_code == 403

    async def test_remind_rate_limit_24h(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """同一對象 24 小時內只能發一次。"""
        payload = {
            "to_user": str(user_b.id),
            "amount": "100",
            "currency": "TWD",
        }
        resp1 = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements/reminders",
            headers=auth_header(user_a),
            json=payload,
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements/reminders",
            headers=auth_header(user_a),
            json=payload,
        )
        assert resp2.status_code == 400
        assert "24 hours" in resp2.json()["detail"]
