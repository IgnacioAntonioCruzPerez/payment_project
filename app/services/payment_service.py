from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Payment, Outbox
from app.schemas.payment import PaymentCreate

async def create_payment(
    db: AsyncSession,
    data: PaymentCreate,
    idempotency_key: str,
):

    stmt = select(Payment).where(
        Payment.idempotency_key == idempotency_key
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        return existing

    payment = Payment(
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        metadata_=data.metadata,
        webhook_url=data.webhook_url,
        idempotency_key=idempotency_key,
    )

    db.add(payment)
    await db.flush()

    event = Outbox(
        event_type="payments.new",
        payload={"payment_id": str(payment.id)}
        status="pending"
    )

    db.add(event)
    
    await db.commit()

    await db.refresh(payment)

    return payment

async def get_payment(db: AsyncSession, payment_id):
    stmt = select(Payment).where(Payment.id == payment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()