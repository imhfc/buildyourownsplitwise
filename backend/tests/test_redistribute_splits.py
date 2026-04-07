"""Tests for redistribute_equal_splits_for_new_member.

When a new member joins a group, all "full-group equal split" expenses should
be recalculated to include the new member. Manually-selected equal splits and
non-equal split methods should remain unchanged.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestRedistributeOnAddMember:
    """Tests for redistribution triggered by POST /groups/{id}/members."""

    async def test_full_group_equal_split_redistributed(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """全員均分消費在新成員加入後，splits 應包含新成員且重新計算金額。"""
        # 建立一筆全員均分消費（A + B，300 / 2 = 150 each）
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "300",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]

        # 新增 user_c 到群組
        user_c = await create_test_user(db, "charlie-redist@example.com", "Charlie")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_c.id)},
        )
        assert resp.status_code == 201

        # 查詢該消費，splits 應為 3 人，金額 300 / 3 = 100 each
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        expenses = resp.json()
        target = next(e for e in expenses if e["id"] == expense_id)
        assert len(target["splits"]) == 3

        split_amounts = sorted([Decimal(s["amount"]) for s in target["splits"]])
        assert sum(split_amounts) == Decimal("300")
        assert split_amounts == [Decimal("100"), Decimal("100"), Decimal("100")]

        # 確認新成員在 splits 中
        split_user_ids = {s["user_id"] for s in target["splits"]}
        assert str(user_c.id) in split_user_ids

    async def test_manual_selected_equal_split_not_affected(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, user_c: User, group_with_members: Group,
    ):
        """手動指定分帳對象的均分消費，新成員加入後不應被影響。"""
        # 先加入 user_c 讓群組有 3 人
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_c.id)},
        )
        assert resp.status_code == 201

        # 建立一筆只指定 A + B 均分的消費（3 人群組但只選 2 人）
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Partial equal",
                "total_amount": "200",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]

        # 新增 user_d 到群組
        user_d = await create_test_user(db, "dave-redist@example.com", "Dave")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_d.id)},
        )
        assert resp.status_code == 201

        # 查詢該消費，splits 應仍為 2 人（A + B），不受影響
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        expenses = resp.json()
        target = next(e for e in expenses if e["id"] == expense_id)
        assert len(target["splits"]) == 2
        split_user_ids = {s["user_id"] for s in target["splits"]}
        assert str(user_d.id) not in split_user_ids

    async def test_exact_split_not_affected(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """非均分消費（exact）新成員加入後不應被影響。"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Exact split",
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
        expense_id = resp.json()["id"]

        # 新增 user_c
        user_c = await create_test_user(db, "charlie-exact@example.com", "Charlie")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_c.id)},
        )
        assert resp.status_code == 201

        # 查詢該消費，splits 仍為 2 人，金額不變
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        expenses = resp.json()
        target = next(e for e in expenses if e["id"] == expense_id)
        assert len(target["splits"]) == 2
        amounts = {s["user_id"]: Decimal(s["amount"]) for s in target["splits"]}
        assert amounts[str(user_a.id)] == Decimal("200")
        assert amounts[str(user_b.id)] == Decimal("300")

    async def test_ratio_split_not_affected(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """非均分消費（ratio）新成員加入後不應被影響。"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Ratio split",
                "total_amount": "900",
                "paid_by": str(user_a.id),
                "split_method": "ratio",
                "splits": [
                    {"user_id": str(user_a.id), "shares": "1"},
                    {"user_id": str(user_b.id), "shares": "2"},
                ],
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]

        user_c = await create_test_user(db, "charlie-ratio@example.com", "Charlie")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_c.id)},
        )
        assert resp.status_code == 201

        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        expenses = resp.json()
        target = next(e for e in expenses if e["id"] == expense_id)
        assert len(target["splits"]) == 2

    async def test_shares_split_not_affected(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """非均分消費（shares 按份數）新成員加入後不應被影響。"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Shares split",
                "total_amount": "1000",
                "paid_by": str(user_a.id),
                "split_method": "shares",
                "splits": [
                    {"user_id": str(user_a.id), "shares": "3"},
                    {"user_id": str(user_b.id), "shares": "7"},
                ],
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]

        user_c = await create_test_user(db, "charlie-shares@example.com", "Charlie")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_c.id)},
        )
        assert resp.status_code == 201

        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        expenses = resp.json()
        target = next(e for e in expenses if e["id"] == expense_id)
        assert len(target["splits"]) == 2
        amounts = {s["user_id"]: Decimal(s["amount"]) for s in target["splits"]}
        assert amounts[str(user_a.id)] == Decimal("300")
        assert amounts[str(user_b.id)] == Decimal("700")

    async def test_odd_amount_redistribution(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """均分不整除時，尾差歸第一人，總和仍等於 total_amount。"""
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Odd amount",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]

        user_c = await create_test_user(db, "charlie-odd@example.com", "Charlie")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_c.id)},
        )
        assert resp.status_code == 201

        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        expenses = resp.json()
        target = next(e for e in expenses if e["id"] == expense_id)
        assert len(target["splits"]) == 3
        total = sum(Decimal(s["amount"]) for s in target["splits"])
        assert total == Decimal("100")

    async def test_multiple_equal_expenses_all_redistributed(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """多筆全員均分消費都會被重新分配。"""
        expense_ids = []
        for desc, amt in [("Lunch", "600"), ("Taxi", "300")]:
            resp = await client.post(
                f"/api/v1/groups/{group_with_members.id}/expenses",
                headers=auth_header(user_a),
                json={
                    "description": desc,
                    "total_amount": amt,
                    "paid_by": str(user_a.id),
                    "split_method": "equal",
                },
            )
            assert resp.status_code == 201
            expense_ids.append(resp.json()["id"])

        user_c = await create_test_user(db, "charlie-multi@example.com", "Charlie")
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/members",
            headers=auth_header(user_a),
            json={"user_id": str(user_c.id)},
        )
        assert resp.status_code == 201

        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        expenses = resp.json()

        for eid in expense_ids:
            target = next(e for e in expenses if e["id"] == eid)
            assert len(target["splits"]) == 3
            total = sum(Decimal(s["amount"]) for s in target["splits"])
            assert total == Decimal(target["total_amount"])


class TestRedistributeLargeGroup:
    """Tests for redistribution in large groups (15 -> 18 members, added one by one)."""

    async def test_15_to_18_members_sequential(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """15人群組逐一增加到18人，全員均分消費每次都正確重新分配。"""
        # 先把群組擴到 15 人（已有 A + B = 2 人，再加 13 人）
        members = [user_a, user_b]
        for i in range(13):
            u = await create_test_user(db, f"user-lg-{i}@example.com", f"User{i}")
            resp = await client.post(
                f"/api/v1/groups/{group_with_members.id}/members",
                headers=auth_header(user_a),
                json={"user_id": str(u.id)},
            )
            assert resp.status_code == 201
            members.append(u)
        assert len(members) == 15

        # 建立全員均分消費（15 人均分 1500 = 100 each）
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Big dinner",
                "total_amount": "1500",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]
        assert len(resp.json()["splits"]) == 15

        # 逐一加入 3 人（15 -> 16 -> 17 -> 18），每次驗證
        for i in range(3):
            new_user = await create_test_user(db, f"new-lg-{i}@example.com", f"New{i}")
            resp = await client.post(
                f"/api/v1/groups/{group_with_members.id}/members",
                headers=auth_header(user_a),
                json={"user_id": str(new_user.id)},
            )
            assert resp.status_code == 201
            members.append(new_user)

            expected_count = len(members)

            resp = await client.get(
                f"/api/v1/groups/{group_with_members.id}/expenses",
                headers=auth_header(user_a),
            )
            assert resp.status_code == 200
            target = next(e for e in resp.json() if e["id"] == expense_id)

            # splits 人數應等於當前群組成員數
            assert len(target["splits"]) == expected_count, (
                f"After adding member #{expected_count}: "
                f"expected {expected_count} splits, got {len(target['splits'])}"
            )

            # 總和必須等於 total_amount
            total = sum(Decimal(s["amount"]) for s in target["splits"])
            assert total == Decimal("1500"), (
                f"After adding member #{expected_count}: "
                f"split total {total} != 1500"
            )

            # 新成員必須在 splits 中
            split_user_ids = {s["user_id"] for s in target["splits"]}
            assert str(new_user.id) in split_user_ids

        # 最終驗證：18 人均分 1500
        assert len(members) == 18
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
        )
        target = next(e for e in resp.json() if e["id"] == expense_id)
        assert len(target["splits"]) == 18
        amounts = [Decimal(s["amount"]) for s in target["splits"]]
        assert sum(amounts) == Decimal("1500")
        # 1500 / 18 = 83.33... 尾差歸第一人
        per_person = Decimal("83.33")
        remainder = Decimal("1500") - per_person * 18
        assert sorted(amounts).count(per_person) >= 17  # 至少 17 人是 83.33


class TestRedistributeOnInviteAccept:
    """Tests for redistribution triggered by accepting an invite link."""

    async def test_invite_accept_redistributes_equal_splits(
        self, client: AsyncClient, db: AsyncSession,
        user_a: User, user_b: User, group_with_members: Group,
    ):
        """透過邀請連結加入也會觸發均分重新分配。"""
        # 建立全員均分消費
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Hotel",
                "total_amount": "900",
                "paid_by": str(user_a.id),
                "split_method": "equal",
            },
        )
        assert resp.status_code == 201
        expense_id = resp.json()["id"]

        # 建立邀請連結
        resp = await client.post(
            f"/api/v1/groups/{group_with_members.id}/invite",
            headers=auth_header(user_a),
        )
        assert resp.status_code == 200
        invite_token = resp.json()["invite_token"]

        # user_c 透過邀請連結加入
        user_c = await create_test_user(db, "charlie-invite@example.com", "Charlie")
        resp = await client.post(
            f"/api/v1/invite/{invite_token}/accept",
            headers=auth_header(user_c),
        )
        assert resp.status_code == 200

        # 驗證 splits 已重新分配為 3 人
        resp = await client.get(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_c),
        )
        assert resp.status_code == 200
        expenses = resp.json()
        target = next(e for e in expenses if e["id"] == expense_id)
        assert len(target["splits"]) == 3

        split_amounts = sorted([Decimal(s["amount"]) for s in target["splits"]])
        assert split_amounts == [Decimal("300"), Decimal("300"), Decimal("300")]
        assert sum(split_amounts) == Decimal("900")

        split_user_ids = {s["user_id"] for s in target["splits"]}
        assert str(user_c.id) in split_user_ids
