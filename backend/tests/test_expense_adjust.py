"""
測試已結清消費的調整功能（adjusted_from_id）。

當使用者嘗試更新一筆已結清的消費時，系統會：
1. 軟刪除原始消費
2. 建立一筆新消費取代之
3. 新消費的 adjusted_from_id 指向原始消費 ID
4. 記錄 expense_adjusted activity
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestAdjustSettledExpense:
    """已結清消費調整的完整流程測試"""

    async def test_update_settled_expense_creates_new_expense(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """完整流程：建立消費 → 結算 → 確認 → 調整
        驗證：
        - 回傳的消費是新 ID
        - adjusted_from_id 指向原始 ID
        - 原消費被軟刪除（不出現在列表中）
        """
        # 步驟 1: user_a 建立消費 300 元均分（user_a 150, user_b 150）
        expense_resp = await client.post(
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
        assert expense_resp.status_code == 201
        original_expense_id = uuid.UUID(expense_resp.json()["id"])
        assert expense_resp.json()["adjusted_from_id"] is None

        # 步驟 2: user_b 建立結算 150 TWD 給 user_a（清償欠款）
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={
                "to_user": str(user_a.id),
                "amount": "150",
                "currency": "TWD",
            },
        )
        assert settlement_resp.status_code == 201
        settlement_id = uuid.UUID(settlement_resp.json()["id"])

        # 步驟 3: user_a（收款方）確認結算
        confirm_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )
        assert confirm_resp.status_code == 200

        # 步驟 4: user_a 更新原消費的 description
        # 由於消費已被結清，應該走 adjust 流程
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_expense_id}",
            headers=auth_header(user_a),
            json={"description": "Dinner (updated)"},
        )
        assert update_resp.status_code == 200
        updated_data = update_resp.json()

        # 驗證：新消費 ID 不同於原始 ID
        new_expense_id = uuid.UUID(updated_data["id"])
        assert new_expense_id != original_expense_id

        # 驗證：新消費的 adjusted_from_id 指向原始消費
        assert updated_data["adjusted_from_id"] == str(original_expense_id)

        # 驗證：新消費的描述已更新
        assert updated_data["description"] == "Dinner (updated)"

        # 驗證：列表中不含原始消費（已軟刪除）
        list_resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert list_resp.status_code == 200
        expense_ids = [uuid.UUID(e["id"]) for e in list_resp.json()]
        assert original_expense_id not in expense_ids
        assert new_expense_id in expense_ids

    async def test_update_unsettled_expense_updates_in_place(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """對照組：未結清的消費應該原地更新（不創建新消費）

        驗證：
        - 回傳同一個 expense ID
        - adjusted_from_id 仍為 None
        """
        # 步驟 1: 建立消費（不結算）
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Lunch",
                "total_amount": "200",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert expense_resp.status_code == 201
        original_expense_id = uuid.UUID(expense_resp.json()["id"])

        # 步驟 2: 更新（無結算）
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_expense_id}",
            headers=auth_header(user_a),
            json={"description": "Lunch (updated)"},
        )
        assert update_resp.status_code == 200
        updated_data = update_resp.json()

        # 驗證：ID 保持不變（原地更新）
        assert uuid.UUID(updated_data["id"]) == original_expense_id

        # 驗證：adjusted_from_id 為 None
        assert updated_data["adjusted_from_id"] is None

        # 驗證：描述已更新
        assert updated_data["description"] == "Lunch (updated)"

    async def test_adjust_settled_expense_preserves_fields(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """沖銷重建時保留未修改的欄位

        驗證：
        - note、expense_date、total_amount 等未修改的欄位被保留
        """
        from datetime import date

        # 步驟 1: 建立有 note 和 expense_date 的消費
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "note": "Great restaurant",
                "expense_date": "2026-04-01",
            },
        )
        assert expense_resp.status_code == 201
        original_expense_id = uuid.UUID(expense_resp.json()["id"])

        # 步驟 2-3: 完成結算
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "150", "currency": "TWD"},
        )
        settlement_id = uuid.UUID(settlement_resp.json()["id"])
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # 步驟 4: 只更新 description，其他欄位保留
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_expense_id}",
            headers=auth_header(user_a),
            json={"description": "Dinner (special occasion)"},
        )
        assert update_resp.status_code == 200
        updated_data = update_resp.json()

        # 驗證：未修改的欄位被保留
        assert updated_data["note"] == "Great restaurant"
        assert updated_data["expense_date"] == "2026-04-01"
        assert Decimal(updated_data["total_amount"]) == Decimal("300")

    async def test_adjust_settled_expense_changes_amount(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """調整已結清消費的金額

        驗證：
        - 新消費的金額正確
        - splits 根據新金額重新計算
        """
        # 步驟 1: 建立 300 元消費
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        original_expense_id = uuid.UUID(expense_resp.json()["id"])

        # 步驟 2-3: 結算
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "150", "currency": "TWD"},
        )
        settlement_id = uuid.UUID(settlement_resp.json()["id"])
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # 步驟 4: 改金額為 400
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_expense_id}",
            headers=auth_header(user_a),
            json={"total_amount": "400"},
        )
        assert update_resp.status_code == 200
        updated_data = update_resp.json()

        # 驗證：新金額
        assert Decimal(updated_data["total_amount"]) == Decimal("400")

        # 驗證：splits 重新計算（平分 400）
        split_amounts = [Decimal(s["amount"]) for s in updated_data["splits"]]
        assert sum(split_amounts) == Decimal("400")
        # 均分 400 給 2 人 = 200 each
        assert all(amt == Decimal("200") for amt in split_amounts)

    async def test_adjust_settled_expense_logs_expense_adjusted(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """驗證調整已結清消費時記錄 expense_adjusted activity

        驗證：
        - ActivityLog 中存在 action == "expense_adjusted" 的紀錄
        """
        # 步驟 1: 建立消費
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        original_expense_id = uuid.UUID(expense_resp.json()["id"])

        # 步驟 2-3: 結算
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "150", "currency": "TWD"},
        )
        settlement_id = uuid.UUID(settlement_resp.json()["id"])
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # 步驟 4: 調整
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_expense_id}",
            headers=auth_header(user_a),
            json={"description": "Dinner (adjusted)"},
        )
        assert update_resp.status_code == 200

        # 驗證：查詢 ActivityLog
        activity_result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.group_id == group_with_members.id,
                ActivityLog.action == "expense_adjusted",
            )
        )
        activities = activity_result.scalars().all()
        assert len(activities) > 0

        # 驗證活動記錄的內容
        adjusted_activity = activities[-1]  # 最新的調整記錄
        assert adjusted_activity.action == "expense_adjusted"
        assert adjusted_activity.actor_id == user_a.id
        assert adjusted_activity.description == "Dinner (adjusted)"
        assert Decimal(adjusted_activity.amount) == Decimal("300")

    async def test_delete_settled_expense_forbidden(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """已結清消費不能被刪除

        驗證：
        - DELETE 已結清消費回傳 400 ValidationError
        """
        # 步驟 1: 建立消費
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        original_expense_id = uuid.UUID(expense_resp.json()["id"])

        # 步驟 2-3: 結算
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "150", "currency": "TWD"},
        )
        settlement_id = uuid.UUID(settlement_resp.json()["id"])
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # 步驟 4: 嘗試刪除已結清消費
        delete_resp = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_expense_id}",
            headers=auth_header(user_a),
        )
        assert delete_resp.status_code == 400
        assert "settled" in delete_resp.json()["detail"].lower()

    async def test_adjusted_from_id_in_response(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """驗證回應中的 adjusted_from_id 欄位

        驗證：
        - 一般消費：adjusted_from_id is None
        - 調整後消費：adjusted_from_id 有值
        """
        # 步驟 1: 建立消費
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert expense_resp.status_code == 201
        original_id = uuid.UUID(expense_resp.json()["id"])

        # 驗證：新消費的 adjusted_from_id 為 None
        assert expense_resp.json()["adjusted_from_id"] is None

        # 步驟 2-3: 結算
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "150", "currency": "TWD"},
        )
        settlement_id = uuid.UUID(settlement_resp.json()["id"])
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # 步驟 4: 調整
        update_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_id}",
            headers=auth_header(user_a),
            json={"description": "Updated"},
        )
        assert update_resp.status_code == 200

        # 驗證：新消費的 adjusted_from_id 指向原始消費
        adjusted_id = uuid.UUID(update_resp.json()["id"])
        assert update_resp.json()["adjusted_from_id"] == str(original_id)
        assert adjusted_id != original_id

    async def test_get_settled_expense_detail_direct_access(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """直接查詢已軟刪除的原始消費應該 404

        驗證：
        - GET /expenses/{original_id} 回傳 404（因為已軟刪除）
        """
        # 步驟 1: 建立消費
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        original_id = uuid.UUID(expense_resp.json()["id"])

        # 步驟 2-3: 結算
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "150", "currency": "TWD"},
        )
        settlement_id = uuid.UUID(settlement_resp.json()["id"])
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # 步驟 4: 調整
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_id}",
            headers=auth_header(user_a),
            json={"description": "Updated"},
        )

        # 步驟 5: 直接查詢原始消費
        get_resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_id}",
            headers=auth_header(user_a),
        )
        assert get_resp.status_code == 404

    async def test_adjusted_expense_updates_in_place_on_subsequent_edit(
        self, client: AsyncClient, user_a: User, user_b: User, group_with_members: Group
    ):
        """調整後的消費在後續修改時走原地更新（因為 created_at > confirmed_at）

        調整後的消費有新的 created_at，所以 check_expense_settled 會返回 False。
        因此後續修改會走原地更新路徑，而不是再次調整。

        驗證：
        - 第一次修改：creates new expense（adjusted_from_id 指向原始）
        - 第二次修改：updates in place（ID 不變，adjusted_from_id 仍指向原始）
        """
        # 步驟 1: 建立消費
        expense_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        original_id = uuid.UUID(expense_resp.json()["id"])

        # 步驟 2-3: 結算
        settlement_resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={"to_user": str(user_a.id), "amount": "150", "currency": "TWD"},
        )
        settlement_id = uuid.UUID(settlement_resp.json()["id"])
        await client.patch(
            f"/api/v1/groups/{group_with_members.id}/settlements/{settlement_id}/confirm",
            headers=auth_header(user_a),
        )

        # 步驟 4: 第一次調整
        first_adjust_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{original_id}",
            headers=auth_header(user_a),
            json={"description": "Updated 1"},
        )
        assert first_adjust_resp.status_code == 200
        first_adjusted_id = uuid.UUID(first_adjust_resp.json()["id"])
        assert first_adjust_resp.json()["adjusted_from_id"] == str(original_id)

        # 步驟 5: 第二次修改調整後的消費
        # 由於調整後的消費 created_at 是新時間，不會被視為已結清
        # 因此會走原地更新，ID 保持不變
        second_edit_resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{first_adjusted_id}",
            headers=auth_header(user_a),
            json={"description": "Updated 2"},
        )
        assert second_edit_resp.status_code == 200
        second_edit_id = uuid.UUID(second_edit_resp.json()["id"])

        # 驗證：第二次修改是原地更新
        assert second_edit_id == first_adjusted_id
        # adjusted_from_id 仍指向原始消費
        assert second_edit_resp.json()["adjusted_from_id"] == str(original_id)
        # 描述已更新
        assert second_edit_resp.json()["description"] == "Updated 2"
