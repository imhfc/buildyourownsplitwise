from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


class TestActivities:
    async def test_empty_activities_no_groups(self, client: AsyncClient, user_a):
        """沒有群組時回傳空陣列。"""
        resp = await client.get("/api/v1/activities", headers=auth_header(user_a))
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_activities_include_expense(
        self, client: AsyncClient, db: AsyncSession, user_a, group_with_members
    ):
        """activity_logs 有 expense_added 紀錄時，應正確回傳。"""
        log = ActivityLog(
            group_id=group_with_members.id,
            actor_id=user_a.id,
            action="expense_added",
            target_type="expense",
            description="晚餐",
            amount=Decimal("300"),
            currency="TWD",
        )
        db.add(log)
        await db.flush()

        resp = await client.get("/api/v1/activities", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        item = next(i for i in data if i["type"] == "expense_added")
        assert item["description"] == "晚餐"
        assert item["group_name"] == group_with_members.name
        assert item["actor_name"] == user_a.display_name

    async def test_activities_include_settlement(
        self, client: AsyncClient, db: AsyncSession, user_a, user_b, group_with_members
    ):
        """activity_logs 有 settlement_created 紀錄時，應正確回傳。"""
        log = ActivityLog(
            group_id=group_with_members.id,
            actor_id=user_b.id,
            action="settlement_created",
            target_type="settlement",
            amount=Decimal("150"),
            currency="TWD",
            extra_name=user_a.display_name,
        )
        db.add(log)
        await db.flush()

        resp = await client.get("/api/v1/activities", headers=auth_header(user_a))
        assert resp.status_code == 200
        data = resp.json()
        item = next(i for i in data if i["type"] == "settlement_created")
        assert item["actor_name"] == user_b.display_name
        assert item["to_name"] == user_a.display_name

    async def test_activities_only_own_groups(
        self, client: AsyncClient, db: AsyncSession, user_a, user_c, group_with_members
    ):
        """user_c 不在群組內，看不到 group_with_members 的活動。"""
        log = ActivityLog(
            group_id=group_with_members.id,
            actor_id=user_a.id,
            action="expense_added",
            target_type="expense",
            description="秘密費用",
            amount=Decimal("100"),
            currency="TWD",
        )
        db.add(log)
        await db.flush()

        resp = await client.get("/api/v1/activities", headers=auth_header(user_c))
        assert resp.status_code == 200
        data = resp.json()
        descriptions = [i.get("description") for i in data]
        assert "秘密費用" not in descriptions

    async def test_activities_pagination(
        self, client: AsyncClient, db: AsyncSession, user_a, group_with_members
    ):
        """分頁：limit=1 只回傳 1 筆。"""
        for i in range(3):
            log = ActivityLog(
                group_id=group_with_members.id,
                actor_id=user_a.id,
                action="expense_added",
                target_type="expense",
                description=f"費用{i}",
                amount=Decimal("10"),
                currency="TWD",
            )
            db.add(log)
        await db.flush()

        resp = await client.get(
            "/api/v1/activities", headers=auth_header(user_a), params={"limit": 1}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_activities_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/activities")
        assert resp.status_code == 403
