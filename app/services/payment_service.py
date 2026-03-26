from app.db.models import Payment, Outbox


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

    event = Outbox(
        event_type="payments.new",
        payload={"payment_id": str(payment.id)}
    )

    db.add(event)
    
    await db.commit()

    await db.refresh(payment)

    return payment