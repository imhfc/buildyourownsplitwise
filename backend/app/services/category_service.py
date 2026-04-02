import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.category import ExpenseCategory
from app.schemas.category import CategoryCreate
from app.services.group_service import check_membership


async def list_categories(
    db: AsyncSession, group_id: uuid.UUID | None = None
) -> list[ExpenseCategory]:
    """列出分類：預設分類 + 群組自訂分類。"""
    conditions = [
        (ExpenseCategory.is_default == True) | (ExpenseCategory.group_id == group_id)
    ] if group_id else [ExpenseCategory.is_default == True]
    result = await db.execute(
        select(ExpenseCategory).where(*conditions).order_by(ExpenseCategory.name)
    )
    return list(result.scalars().all())


async def create_category(
    db: AsyncSession, user_id: uuid.UUID, data: CategoryCreate
) -> ExpenseCategory:
    """建立群組自訂分類。需驗證使用者為群組成員。"""
    if data.group_id:
        await check_membership(db, data.group_id, user_id)
    category = ExpenseCategory(
        name=data.name,
        icon=data.icon,
        color=data.color,
        group_id=data.group_id,
        is_default=False,
        created_by=user_id,
    )
    db.add(category)
    await db.flush()
    return category


async def delete_category(
    db: AsyncSession, category_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """刪除自訂分類（預設分類不可刪）。"""
    result = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Category not found")
    if category.is_default:
        raise ValidationError("Cannot delete default category")
    if category.created_by != user_id:
        raise ForbiddenError("Only creator can delete category")
    await db.delete(category)
