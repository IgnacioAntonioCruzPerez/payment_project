import asyncio
import httpx
import random
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.config import settings
from app.db.models import Payment
from app.db.session import async_session
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)
payments_queue = RabbitQueue(settings.PAYMENTS_QUEUE, durable=True)
payments_dlq = RabbitQueue(settings.PAYMENTS_DLQ, durable=True)


async def send_webhook_with_retry(url: str, payload: dict) -> bool:
    delay = 1
    for attempt in range(1, 4):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                if 200 <= response.status_code < 300:
                    return True
                print(f"Webhook status {response.status_code} attempt {attempt}")
        except Exception as exc:
            print(f"Webhook error attempt {attempt}: {exc}")
        await asyncio.sleep(delay)
        delay *= 2
    return False


async def process_payment_event(data: dict) -> None:
    payment_id = data.get("payment_id")
    if not payment_id:
        raise ValueError("payment_id is required")
    payment_uuid = uuid.UUID(str(payment_id))

    async with async_session() as db:
        result = await db.execute(select(Payment).where(Payment.id == payment_uuid))
        payment = result.scalar_one_or_none()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        # Keep processing idempotent: if already finalized, skip re-processing
        if payment.status == "pending":
            await asyncio.sleep(random.uniform(2, 5))
            status = "succeeded" if random.random() < 0.9 else "failed"
            payment.status = status
            payment.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()
            await db.refresh(payment)

        # Capture values while session is still open
        webhook_url = payment.webhook_url
        webhook_payload = {
            "payment_id": str(payment.id),
            "status": payment.status,
            "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
        }

    webhook_ok = await send_webhook_with_retry(webhook_url, webhook_payload)
    if not webhook_ok:
        raise RuntimeError("webhook delivery failed after retries")


@broker.subscriber(payments_queue)
async def consume_payment_event(message: dict):
    attempts = int(message.get("attempts", 1))
    try:
        print(f"📩 Received payment event: {message} | attempt={attempts}")
        await process_payment_event(message)
    except Exception as exc:
        print(f"❌ Processing error: {exc}")
        if attempts >= 3:
            await broker.publish(
                {
                    "original_message": message,
                    "error": str(exc),
                    "attempts": attempts,
                },
                queue=payments_dlq.name,
            )
            return

        await broker.publish(
            {
                **message,
                "attempts": attempts + 1,
            },
            queue=payments_queue.name,
        )

if __name__ == "__main__":
    asyncio.run(app.run())