from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense, ExpenseSplit
from app.models.settlement import Settlement
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
        """新增費用後，activities 應包含 expense_added。"""
        expense = Expense(
            group_id=group_with_members.id,
            description="晚餐",
            total_amount=Decimal("300"),
            currency="TWD",
            paid_by=user_a.id,
            created_by=user_a.id,
        )
        db.add(expense)
        await db.flush()

        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=user_a.id,
            amount=Decimal("300"),
        )
        db.add(split)
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
        """建立結算後，activities 應包含 settlement_created。"""
        settlement = Settlement(
            group_id=group_with_members.id,
            from_user=user_b.id,
            to_user=user_a.id,
            amount=Decimal("150"),
            currency="TWD",
        )
        db.add(settlement)
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
        expense = Expense(
            group_id=group_with_members.id,
            description="秘密費用",
            total_amount=Decimal("100"),
            currency="TWD",
            paid_by=user_a.id,
            created_by=user_a.id,
        )
        db.add(expense)
        await db.flush()

        resp = await client.get("/api/v1/activities", headers=auth_header(user_c))
        assert resp.status_code == 200
        data = resp.json()
        # user_c 不應看到這筆費用
        descriptions = [i.get("description") for i in data]
        assert "秘密費用" not in descriptions

    async def test_activities_pagination(
        self, client: AsyncClient, db: AsyncSession, user_a, group_with_members
    ):
        """分頁：limit=1 只回傳 1 筆。"""
        for i in range(3):
            e = Expense(
                group_id=group_with_members.id,
                description=f"費用{i}",
                total_amount=Decimal("10"),
                currency="TWD",
                paid_by=user_a.id,
                created_by=user_a.id,
            )
            db.add(e)
        await db.flush()

        resp = await client.get(
            "/api/v1/activities", headers=auth_header(user_a), params={"limit": 1}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_activities_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/activities")
        assert resp.status_code == 403
