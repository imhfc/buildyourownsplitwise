import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id"))
    description: Mapped[str] = mapped_column(String(300))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="TWD")
    exchange_rate_to_base: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("1.0"))
    base_currency: Mapped[str] = mapped_column(String(3), default="TWD")
    paid_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    split_method: Mapped[str] = mapped_column(String(20), default="equal")  # equal/ratio/exact/shares
    receipt_image_url: Mapped[str | None] = mapped_column(String(500))
    ocr_data: Mapped[dict | None] = mapped_column(JSONB)
    note: Mapped[str | None] = mapped_column(Text)
    expense_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    group = relationship("Group", back_populates="expenses")
    payer = relationship("User", foreign_keys=[paid_by])
    creator = relationship("User", foreign_keys=[created_by])
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("expenses.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    shares: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))  # for ratio/shares split

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User")
