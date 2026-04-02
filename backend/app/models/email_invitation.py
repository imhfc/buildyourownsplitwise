import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmailInvitation(Base):
    __tablename__ = "email_invitations"
    __table_args__ = (
        Index("ix_email_invitations_email_status", "email", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id"))
    inviter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    email: Mapped[str] = mapped_column(String(255), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/accepted/declined/expired
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    group = relationship("Group")
    inviter = relationship("User", foreign_keys=[inviter_id])
