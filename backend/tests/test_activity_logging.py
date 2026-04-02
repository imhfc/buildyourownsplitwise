from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestExpenseActivityLogging:
    async def test_create_expense_logs_activity(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """建立消費後應自動產生 expense_added 活動紀錄。"""
        # Act: 建立消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "dinner",
                "total_amount": "500.00",
                "paid_by": str(user_a.id),
            },
        )
        assert resp.status_code == 201

        # Assert: 驗證活動紀錄被建立
        result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.group_id == group_with_members.id,
                ActivityLog.action == "expense_added",
            )
            .order_by(ActivityLog.created_at.desc())
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.description == "dinner"
        assert log.amount == Decimal("500.00")
        assert log.actor_id == user_a.id
        assert log.target_type == "expense"

    async def test_delete_expense_logs_activity(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """刪除消費後應自動產生 expense_deleted 活動紀錄。"""
        # Arrange: 建立消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "to_delete",
                "total_amount": "100.00",
                "paid_by": str(user_a.id),
            },
        )
        expense_id = resp.json()["id"]

        # Act: 刪除消費
        await client.delete(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
        )

        # Assert: 驗證刪除活動紀錄
        result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.group_id == group_with_members.id,
                ActivityLog.action == "expense_deleted",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.description == "to_delete"
        assert log.amount == Decimal("100.00")

    async def test_update_expense_logs_activity(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """更新消費後應自動產生 expense_updated 活動紀錄。"""
        # Arrange: 建立消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "lunch",
                "total_amount": "200.00",
                "paid_by": str(user_a.id),
            },
        )
        expense_id = resp.json()["id"]

        # Act: 更新消費描述
        resp = await client.patch(
            f"/api/v1/groups/{group_with_members.id}/expenses/{expense_id}",
            headers=auth_header(user_a),
            json={"description": "updated lunch"},
        )
        assert resp.status_code == 200

        # Assert: 驗證更新活動紀錄
        result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.group_id == group_with_members.id,
                ActivityLog.action == "expense_updated",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.description == "updated lunch"
        assert log.actor_id == user_a.id

    async def test_create_expense_with_splits_logs_activity(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """建立含分配方式的消費應正確記錄金額。"""
        # Act: 建立均分消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "team lunch",
                "total_amount": "300.00",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert resp.status_code == 201

        # Assert: 驗證活動紀錄記錄了正確的金額
        result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.group_id == group_with_members.id,
                ActivityLog.action == "expense_added",
                ActivityLog.description == "team lunch",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.amount == Decimal("300.00")


class TestSettlementActivityLogging:
    async def test_create_settlement_logs_activity(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """建立結算後應自動產生 settlement_created 活動紀錄。"""
        # Act: user_b 支付給 user_a
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={
                "to_user": str(user_a.id),
                "amount": "150.00",
                "currency": "TWD",
            },
        )
        assert resp.status_code == 201

        # Assert: 驗證結算活動紀錄
        result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.group_id == group_with_members.id,
                ActivityLog.action == "settlement_created",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.amount == Decimal("150.00")
        assert log.actor_id == user_b.id
        assert log.target_type == "settlement"
        assert log.extra_name == "Alice"  # payee display name

    async def test_settlement_activity_includes_payee_name(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """結算活動紀錄應包含收款人名稱。"""
        # Act: 建立結算
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/settlements",
            headers=auth_header(user_b),
            json={
                "to_user": str(user_a.id),
                "amount": "250.00",
                "currency": "TWD",
            },
        )

        # Assert: 驗證 extra_name 欄位包含收款人名稱
        result = await db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.group_id == group_with_members.id,
                ActivityLog.action == "settlement_created",
            )
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.extra_name == "Alice"


class TestActivitiesAPI:
    async def test_list_activities_includes_expense_creation(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """透過 API 建立消費後，/api/v1/activities 應包含對應紀錄。"""
        # Act: 建立消費
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "via api",
                "total_amount": "100.00",
                "paid_by": str(user_a.id),
            },
        )

        # Assert: 列表應包含該活動
        resp = await client.get("/api/v1/activities", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(a["description"] == "via api" for a in data)

    async def test_activities_show_actor_info(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """活動列表應包含操作者資訊。"""
        # Act: user_b 建立消費
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_b),
            json={
                "description": "by bob",
                "total_amount": "50.00",
                "paid_by": str(user_b.id),
            },
        )

        # Assert: 活動應顯示 Bob 為操作者
        resp = await client.get("/api/v1/activities", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        activity = next((a for a in data if a["description"] == "by bob"), None)
        assert activity is not None
        assert activity["actor_name"] == "Bob"

    async def test_activities_pagination(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """活動列表應支援分頁。"""
        # Arrange: 建立多筆消費
        for i in range(5):
            await client.post(
                f"/api/v1/groups/{group_with_members.id}/expenses",
                headers=auth_header(user_a),
                json={
                    "description": f"expense_{i}",
                    "total_amount": "50.00",
                    "paid_by": str(user_a.id),
                },
            )

        # Act: 分頁查詢
        resp = await client.get(
            "/api/v1/activities?skip=0&limit=2",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        data = resp.json()

        # Assert: 應只返回 2 筆
        assert len(data) <= 2

    async def test_activities_excluded_deleted_groups(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """已刪除群組的活動不應出現在使用者的活動列表中。"""
        # Arrange: 在群組中建立消費
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "before delete",
                "total_amount": "100.00",
                "paid_by": str(user_a.id),
            },
        )

        # Act: 刪除群組
        await client.delete(
            f"/api/v1/groups/{group_with_members.id}",
            headers=auth_header(user_a),
        )

        # Assert: 活動列表不應包含已刪除群組的活動
        resp = await client.get("/api/v1/activities", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        # 這個特定消費的活動不應出現（只有建立消費和刪除群組操作的紀錄）
        activity = next(
            (a for a in data if a.get("description") == "before delete"),
            None,
        )
        # 因為群組被刪除了，該消費的活動應該被過濾掉
        # （check_membership 時會檢查 Group.deleted_at.is_(None)）
        assert activity is None or activity.get("group_id") is None

    async def test_unread_count_api(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """未讀活動計數 API 應正確運作。"""
        # Act: 建立消費
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "new expense",
                "total_amount": "75.00",
                "paid_by": str(user_a.id),
            },
        )

        # Assert: 獲取未讀計數
        resp = await client.get("/api/v1/activities/unread-count", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        # 應至少有 1 筆未讀（新建立的消費）
        assert data["count"] >= 1

    async def test_mark_activities_read(
        self, client: AsyncClient, user_a, user_b, group_with_members
    ):
        """標記活動為已讀應正確更新 last_read_at。"""
        # Arrange: 建立消費
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "mark read test",
                "total_amount": "100.00",
                "paid_by": str(user_a.id),
            },
        )

        # Act: 標記為已讀
        resp = await client.post("/api/v1/activities/mark-read", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        # 標記後未讀計數應為 0
        assert data["count"] == 0

        # Assert: 驗證後續新活動會被計為未讀
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "after mark read",
                "total_amount": "50.00",
                "paid_by": str(user_a.id),
            },
        )

        resp = await client.get("/api/v1/activities/unread-count", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        # 新活動應被計為未讀
        assert data["count"] >= 1
