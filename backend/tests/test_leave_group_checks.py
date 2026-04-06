import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense, ExpenseSplit
from app.models.group import Group, GroupMember
from app.models.settlement import Settlement
from app.models.user import User
from tests.conftest import auth_header, create_test_user


pytestmark = pytest.mark.asyncio


class TestCannotLeaveWithUnsettledBalance:
    """Test that members cannot leave/be removed if they have unsettled balance in any currency."""

    async def test_cannot_leave_with_unsettled_balance(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """Create expense (user_a pays 100 TWD, user_b owes 50), user_b tries to leave → 422"""
        # Arrange: Create expense where user_a pays 100, split equally (50 each)
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )

        # Act: user_b tries to leave
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_b),
        )

        # Assert
        assert response.status_code == 422
        assert "unsettled balance" in response.json()["detail"].lower()

    async def test_cannot_remove_member_with_unsettled_balance(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """Same setup, admin (user_a) tries to remove user_b → 422"""
        # Arrange: Create expense where user_a pays 100, split equally
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )

        # Act: admin tries to remove user_b
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_a),
        )

        # Assert
        assert response.status_code == 422
        assert "unsettled balance" in response.json()["detail"].lower()


class TestCannotLeaveWithPendingSettlement:
    """Test that members cannot leave if they have pending settlements."""

    async def test_cannot_leave_with_pending_settlement(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """Create pending settlement, user_b tries to leave → 422"""
        # Arrange: Create pending settlement from user_a to user_b
        settlement = Settlement(
            group_id=group_with_members.id,
            from_user=user_a.id,
            to_user=user_b.id,
            amount=Decimal("50.00"),
            currency="TWD",
            status="pending",
        )
        db.add(settlement)
        await db.flush()

        # Act: user_b tries to leave
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_b),
        )

        # Assert
        assert response.status_code == 422
        assert "pending settlement" in response.json()["detail"].lower()

    async def test_cannot_leave_with_pending_settlement_as_payer(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """Pending settlement where user_b is the payer."""
        # Arrange: Create pending settlement from user_b to user_a
        settlement = Settlement(
            group_id=group_with_members.id,
            from_user=user_b.id,
            to_user=user_a.id,
            amount=Decimal("75.00"),
            currency="TWD",
            status="pending",
        )
        db.add(settlement)
        await db.flush()

        # Act: user_b tries to leave
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_b),
        )

        # Assert
        assert response.status_code == 422
        assert "pending settlement" in response.json()["detail"].lower()


class TestCannotLeaveAsOnlyAdmin:
    """Test that the only admin cannot leave if other members exist."""

    async def test_cannot_leave_as_only_admin(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """user_a (only admin) with user_b (member) tries to leave → 422"""
        # Arrange: group_with_members has user_a as admin, user_b as member
        # (Already set up by fixture)

        # Act: user_a tries to leave
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_a.id}",
            headers=auth_header(user_a),
        )

        # Assert
        assert response.status_code == 422
        assert "only admin" in response.json()["detail"].lower()

    async def test_admin_can_leave_if_multiple_admins(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """If group has 2+ admins, one can leave."""
        # Arrange: Promote user_b to admin
        from sqlalchemy import select

        result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_with_members.id,
                GroupMember.user_id == user_b.id,
            )
        )
        member_b = result.scalar_one()
        member_b.role = "admin"
        await db.flush()

        # Act: user_a tries to leave (now there are 2 admins)
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_a.id}",
            headers=auth_header(user_a),
        )

        # Assert: Should succeed (no longer the only admin)
        assert response.status_code == 204

    async def test_admin_can_leave_if_alone(
        self, client: AsyncClient, db: AsyncSession, user_a: User
    ):
        """If group has only 1 member (the admin), they can leave."""
        # Arrange: Create a fresh group with only user_a
        group = Group(name="Solo Group", description="Only one member", created_by=user_a.id)
        db.add(group)
        await db.flush()

        member_a = GroupMember(group_id=group.id, user_id=user_a.id, role="admin")
        db.add(member_a)
        await db.flush()

        # Act: user_a tries to leave their solo group
        response = await client.delete(
            f"/api/v1/groups/{group.id}/members/{user_a.id}",
            headers=auth_header(user_a),
        )

        # Assert: Should succeed (sole member)
        assert response.status_code == 204


class TestCanLeaveAfterBalanceSettled:
    """Test that after settling balance via confirmed settlement, member can leave."""

    async def test_can_leave_after_balance_settled_via_settlement(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """Create expense (100 TWD, split equally), then create confirmed settlement to zero balance."""
        # Arrange: Create expense where user_a pays 100, split equally (50 each)
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )

        # Now user_b owes 50 to user_a
        # Create a confirmed settlement from user_b to user_a for 50 to zero the balance
        settlement = Settlement(
            group_id=group_with_members.id,
            from_user=user_b.id,
            to_user=user_a.id,
            amount=Decimal("50.00"),
            currency="TWD",
            status="confirmed",
        )
        db.add(settlement)
        await db.flush()

        # Act: user_b tries to leave (balance now zero)
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_b),
        )

        # Assert: Should succeed (no unsettled balance, no pending settlements)
        assert response.status_code == 204

    async def test_can_leave_after_balance_zero_from_two_expenses(
        self, client: AsyncClient, db: AsyncSession, user_a: User, user_b: User, group_with_members: Group
    ):
        """Test leaving when both payer and payee owe each other (net zero)."""
        # Arrange: Two expenses that cancel each other out
        # user_a pays 100, user_b gets 50; user_b pays 100, user_a gets 50
        # This results in net zero for both

        # Expense 1: user_a pays 100, split equally (50 each)
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_a),
            json={
                "description": "Dinner",
                "total_amount": "100",
                "paid_by": str(user_a.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )

        # Expense 2: user_b pays 100, split equally (50 each)
        await client.post(
            f"/api/v1/groups/{group_with_members.id}/expenses",
            headers=auth_header(user_b),
            json={
                "description": "Lunch",
                "total_amount": "100",
                "paid_by": str(user_b.id),
                "split_method": "equal",
                "splits": [
                    {"user_id": str(user_a.id)},
                    {"user_id": str(user_b.id)},
                ],
            },
        )

        # Now balances should be net zero for both
        # (each owes 50 and is owed 50, net = 0)

        # Act: user_b tries to leave
        response = await client.delete(
            f"/api/v1/groups/{group_with_members.id}/members/{user_b.id}",
            headers=auth_header(user_b),
        )

        # Assert: Should succeed (net balance is zero)
        assert response.status_code == 204
