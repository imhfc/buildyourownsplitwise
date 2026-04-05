import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    auth_provider: Mapped[str] = mapped_column(String(20), default="email")  # email/google/apple/line
    auth_provider_id: Mapped[str | None] = mapped_column(String(255))
    preferred_currency: Mapped[str] = mapped_column(String(3), default="TWD")
    locale: Mapped[str] = mapped_column(String(5), default="zh-TW")
    push_token: Mapped[str | None] = mapped_column(String(255))
    color_scheme: Mapped[str] = mapped_column(String(20), default="blue")
    theme_mode: Mapped[str] = mapped_column(String(10), default="system")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    group_memberships = relationship("GroupMember", back_populates="user")
