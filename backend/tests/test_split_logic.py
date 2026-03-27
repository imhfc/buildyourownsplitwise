"""Unit tests for split calculation and debt simplification — no database needed."""

import uuid
from decimal import Decimal

import pytest

from app.core.exceptions import ValidationError
from app.services.expense_service import calculate_splits
from app.services.settlement_service import simplify_debts
from app.schemas.expense import ExpenseCreate, ExpenseSplitInput


def _make_uid() -> uuid.UUID:
    return uuid.uuid4()


class TestCalculateSplitsEqual:
    def test_even_split(self):
        uid_a, uid_b = _make_uid(), _make_uid()
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("300"),
            paid_by=uid_a,
            split_method="equal",
            splits=[
                ExpenseSplitInput(user_id=uid_a),
                ExpenseSplitInput(user_id=uid_b),
            ],
        )
        result = calculate_splits(data, [uid_a, uid_b])
        assert len(result) == 2
        total = sum(r["amount"] for r in result)
        assert total == Decimal("300")

    def test_odd_split_three_ways(self):
        uids = [_make_uid() for _ in range(3)]
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("100"),
            paid_by=uids[0],
            split_method="equal",
            splits=[ExpenseSplitInput(user_id=u) for u in uids],
        )
        result = calculate_splits(data, uids)
        total = sum(r["amount"] for r in result)
        assert total == Decimal("100")
        # First person gets the remainder
        assert result[0]["amount"] != result[1]["amount"] or result[0]["amount"] == Decimal("33.34")

    def test_equal_no_splits_uses_all_members(self):
        uids = [_make_uid() for _ in range(4)]
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("400"),
            paid_by=uids[0],
            split_method="equal",
            splits=[],  # no splits specified
        )
        result = calculate_splits(data, uids)
        assert len(result) == 4
        assert all(r["amount"] == Decimal("100") for r in result)


class TestCalculateSplitsExact:
    def test_exact_valid(self):
        uid_a, uid_b = _make_uid(), _make_uid()
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("500"),
            paid_by=uid_a,
            split_method="exact",
            splits=[
                ExpenseSplitInput(user_id=uid_a, amount=Decimal("200")),
                ExpenseSplitInput(user_id=uid_b, amount=Decimal("300")),
            ],
        )
        result = calculate_splits(data, [uid_a, uid_b])
        assert result[0]["amount"] == Decimal("200")
        assert result[1]["amount"] == Decimal("300")

    def test_exact_wrong_total_raises(self):
        uid_a, uid_b = _make_uid(), _make_uid()
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("500"),
            paid_by=uid_a,
            split_method="exact",
            splits=[
                ExpenseSplitInput(user_id=uid_a, amount=Decimal("100")),
                ExpenseSplitInput(user_id=uid_b, amount=Decimal("100")),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            calculate_splits(data, [uid_a, uid_b])
        assert "don't add up" in exc_info.value.message

    def test_exact_no_splits_raises(self):
        uid_a = _make_uid()
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("100"),
            paid_by=uid_a,
            split_method="exact",
            splits=[],
        )
        with pytest.raises(ValidationError):
            calculate_splits(data, [uid_a])


class TestCalculateSplitsShares:
    def test_shares_proportional(self):
        uid_a, uid_b, uid_c = _make_uid(), _make_uid(), _make_uid()
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("900"),
            paid_by=uid_a,
            split_method="shares",
            splits=[
                ExpenseSplitInput(user_id=uid_a, shares=Decimal("1")),
                ExpenseSplitInput(user_id=uid_b, shares=Decimal("2")),
                ExpenseSplitInput(user_id=uid_c, shares=Decimal("3")),
            ],
        )
        result = calculate_splits(data, [uid_a, uid_b, uid_c])
        total = sum(r["amount"] for r in result)
        assert total == Decimal("900")
        # 1:2:3 = 150:300:450
        amounts = [r["amount"] for r in result]
        assert amounts[0] == Decimal("150")
        assert amounts[1] == Decimal("300")

    def test_shares_no_splits_raises(self):
        uid_a = _make_uid()
        data = ExpenseCreate(
            description="Test",
            total_amount=Decimal("100"),
            paid_by=uid_a,
            split_method="shares",
            splits=[],
        )
        with pytest.raises(ValidationError):
            calculate_splits(data, [uid_a])


class TestSimplifyDebts:
    def test_simple_two_users(self):
        uid_a, uid_b = _make_uid(), _make_uid()
        balances = {uid_a: Decimal("100"), uid_b: Decimal("-100")}
        result = simplify_debts(balances)
        assert len(result) == 1
        assert result[0]["from"] == uid_b
        assert result[0]["to"] == uid_a
        assert result[0]["amount"] == Decimal("100")

    def test_three_users_minimized(self):
        uid_a, uid_b, uid_c = _make_uid(), _make_uid(), _make_uid()
        # A is owed 100, B owes 60, C owes 40
        balances = {
            uid_a: Decimal("100"),
            uid_b: Decimal("-60"),
            uid_c: Decimal("-40"),
        }
        result = simplify_debts(balances)
        assert len(result) == 2
        total_paid = sum(t["amount"] for t in result)
        assert total_paid == Decimal("100")

    def test_all_zero_no_transactions(self):
        uid_a, uid_b = _make_uid(), _make_uid()
        balances = {uid_a: Decimal("0"), uid_b: Decimal("0")}
        result = simplify_debts(balances)
        assert result == []

    def test_complex_four_users(self):
        """A paid 120 for group of 4 (each owes 30). B paid 80 for group of 4 (each owes 20).
        Net: A = +90, B = +40, C = -50, D = -50 (not realistic but tests the algorithm)."""
        uid_a, uid_b, uid_c, uid_d = _make_uid(), _make_uid(), _make_uid(), _make_uid()
        balances = {
            uid_a: Decimal("90"),
            uid_b: Decimal("40"),
            uid_c: Decimal("-60"),
            uid_d: Decimal("-70"),
        }
        result = simplify_debts(balances)
        # Total credits = 130, total debts = 130
        total_paid = sum(t["amount"] for t in result)
        assert total_paid == Decimal("130")
        # Greedy: at most 3 transactions for 4 users
        assert len(result) <= 3
