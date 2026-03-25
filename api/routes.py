from sqlalchemy import select
from .db import AsyncSessionLocal
from .models import Payment

@router.post("/payments", response_model=PaymentResponse, status_code=202)
async def create_payment(payment: PaymentCreate):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.idempotency_key == payment.idempotency_key
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        new_payment = Payment(
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata,
            webhook_url=payment.webhook_url,
            idempotency_key=payment.idempotency_key
        )

        session.add(new_payment)
        await session.commit()
        await session.refresh(new_payment)

        return new_payment