"""
一次性回填腳本：從 expenses 和 settlements 產生缺失的 activity_logs。

用法：
  cd backend && .venv/bin/python scripts/backfill_activity_logs.py
"""

import asyncio
import uuid

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select, func  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.database import async_session  # noqa: E402

# 必須匯入所有 model 以解析 SQLAlchemy relationships
from app.models.group import Group, GroupMember  # noqa: E402, F401
from app.models.activity_log import ActivityLog  # noqa: E402
from app.models.expense import Expense  # noqa: E402
from app.models.settlement import Settlement  # noqa: E402
from app.models.user import User  # noqa: E402


async def backfill():
    async with async_session() as db:
        # 先確認目前 activity_logs 筆數
        count_before = (await db.execute(select(func.count()).select_from(ActivityLog))).scalar_one()
        print(f"[before] activity_logs count: {count_before}")

        # --- 回填 expenses (未刪除的) ---
        expenses_result = await db.execute(
            select(Expense).where(Expense.deleted_at.is_(None))
        )
        expenses = expenses_result.scalars().all()
        expense_added = 0

        for e in expenses:
            # 檢查是否已有對應 activity log
            existing = await db.execute(
                select(ActivityLog.id).where(
                    ActivityLog.target_type == "expense",
                    ActivityLog.target_id == e.id,
                    ActivityLog.action == "expense_added",
                )
            )
            if existing.scalar_one_or_none():
                continue

            log = ActivityLog(
                id=uuid.uuid4(),
                group_id=e.group_id,
                actor_id=e.created_by,
                action="expense_added",
                target_type="expense",
                target_id=e.id,
                description=e.description,
                amount=e.total_amount,
                currency=e.currency,
                created_at=e.created_at,
            )
            db.add(log)
            expense_added += 1

        # --- 回填 settlements ---
        settlements_result = await db.execute(select(Settlement))
        settlements = settlements_result.scalars().all()
        settlement_added = 0

        # 預先載入 user display names
        user_ids = {s.to_user for s in settlements}
        if user_ids:
            users_result = await db.execute(
                select(User.id, User.display_name).where(User.id.in_(user_ids))
            )
            user_names = {row[0]: row[1] for row in users_result}
        else:
            user_names = {}

        for s in settlements:
            existing = await db.execute(
                select(ActivityLog.id).where(
                    ActivityLog.target_type == "settlement",
                    ActivityLog.target_id == s.id,
                    ActivityLog.action == "settlement_created",
                )
            )
            if existing.scalar_one_or_none():
                continue

            payee_name = user_names.get(s.to_user, "Unknown")
            log = ActivityLog(
                id=uuid.uuid4(),
                group_id=s.group_id,
                actor_id=s.from_user,
                action="settlement_created",
                target_type="settlement",
                target_id=s.id,
                amount=s.amount,
                currency=s.currency,
                extra_name=payee_name,
                created_at=s.settled_at,
            )
            db.add(log)
            settlement_added += 1

        await db.commit()

        count_after = (await db.execute(select(func.count()).select_from(ActivityLog))).scalar_one()
        print(f"[done] expense_added={expense_added}, settlement_added={settlement_added}")
        print(f"[after] activity_logs count: {count_after}")


if __name__ == "__main__":
    asyncio.run(backfill())
