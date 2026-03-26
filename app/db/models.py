import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Numeric, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(String)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(default="pending")

    idempotency_key: Mapped[str] = mapped_column(String, unique=True)

    webhook_url: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    processed_at: Mapped[datetime] = mapped_column(nullable=True)