"""測試活動 API 缺口：未讀數量、標記已讀。"""
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header


pytestmark = pytest.mark.asyncio


async def _seed_activity(db: AsyncSession, group, actor):
    log = ActivityLog(
        group_id=group.id,
        actor_id=actor.id,
        action="expense_added",
        target_type="expense",
        description="Test",
        amount=Decimal("100"),
        currency="TWD",
    )
    db.add(log)
    await db.flush()
    return log


class TestUnreadCount:
    async def test_unread_count_zero(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """無活動時回傳 0。"""
        resp = await client.get(
            "/api/v1/activities/unread-count",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    async def test_unread_count_with_activities(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        """有未讀活動時回傳正確數量。"""
        await _seed_activity(db, group_with_members, user_a)
        await _seed_activity(db, group_with_members, user_a)

        resp = await client.get(
            "/api/v1/activities/unread-count",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    async def test_unread_count_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/activities/unread-count")
        assert resp.status_code == 403


class TestMarkRead:
    async def test_mark_read(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, group_with_members: Group
    ):
        """標記已讀後 count 應為 0。"""
        await _seed_activity(db, group_with_members, user_a)

        # 確認有未讀
        resp1 = await client.get(
            "/api/v1/activities/unread-count",
            headers=auth_header(user_a),
        )
        assert resp1.json()["count"] == 1

        # 標記已讀
        resp2 = await client.post(
            "/api/v1/activities/mark-read",
            headers=auth_header(user_a),
        )
        assert resp2.status_code == 200
        assert resp2.json()["count"] == 0

        # 再次確認
        resp3 = await client.get(
            "/api/v1/activities/unread-count",
            headers=auth_header(user_a),
        )
        assert resp3.json()["count"] == 0

    async def test_mark_read_idempotent(
        self, client: AsyncClient, user_a: User, group_with_members: Group
    ):
        """無活動時標記已讀也不應報錯。"""
        resp = await client.post(
            "/api/v1/activities/mark-read",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    async def test_mark_read_only_affects_own(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group
    ):
        """user_a 標記已讀不影響 user_b 的未讀數。"""
        await _seed_activity(db, group_with_members, user_a)

        # user_a 標記已讀
        await client.post(
            "/api/v1/activities/mark-read",
            headers=auth_header(user_a),
        )

        # user_b 仍有未讀
        resp = await client.get(
            "/api/v1/activities/unread-count",
            headers=auth_header(user_b),
        )
        assert resp.json()["count"] == 1

    async def test_mark_read_no_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/activities/mark-read")
        assert resp.status_code == 403
