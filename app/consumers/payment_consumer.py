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
from faststream.rabbit.annotations import RabbitMessage

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)

payments_queue = RabbitQueue(settings.PAYMENTS_QUEUE, durable=True)
payments_dlq = RabbitQueue(settings.PAYMENTS_DLQ, durable=True)

MAX_ATTEMPTS = 3


async def send_webhook_with_retry(url: str, payload: dict) -> bool:
    delay = 1
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                if 200 <= response.status_code < 300:
                    return True
                print(f"⚠️ Webhook attempt {attempt} got status {response.status_code}")
        except Exception as exc:
            print(f"⚠️ Webhook attempt {attempt} error: {exc}")
        await asyncio.sleep(delay)
        delay *= 2
    return False


async def process_payment(payment_id: str) -> dict:
    payment_uuid = uuid.UUID(payment_id)

    async with async_session() as db:
        result = await db.execute(select(Payment).where(Payment.id == payment_uuid))
        payment = result.scalar_one_or_none()
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        if payment.status == "pending":
            await asyncio.sleep(random.uniform(2, 5))
            payment.status = "succeeded" if random.random() < 0.9 else "failed"
            payment.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()
            await db.refresh(payment)

        return {
            "payment_id": str(payment.id),
            "status": payment.status,
            "webhook_url": payment.webhook_url,
            "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
        }


@broker.subscriber(payments_queue)
async def consume_payment_event(message: dict, raw_message: RabbitMessage):
    payment_id = message.get("payment_id")
    attempts = int(message.get("attempts", 1))

    print(f"📩 Received payment event: payment_id={payment_id} attempt={attempts}")

    try:
        result = await process_payment(payment_id)
        webhook_ok = await send_webhook_with_retry(result["webhook_url"], {
            "payment_id": result["payment_id"],
            "status": result["status"],
            "processed_at": result["processed_at"],
        })
        if not webhook_ok:
            raise RuntimeError("Webhook delivery failed after retries")

        await raw_message.ack()
        print(f"✅ Payment {payment_id} processed successfully")

    except Exception as exc:
        print(f"❌ Error processing payment {payment_id} (attempt {attempts}): {exc}")
        await raw_message.ack()  # always ack to prevent RabbitMQ requeue loop

        if attempts >= MAX_ATTEMPTS:
            print(f"💀 Sending payment {payment_id} to DLQ after {attempts} attempts")
            await broker.publish(
                {"original_message": message, "error": str(exc), "attempts": attempts},
                queue=payments_dlq.name,
            )
        else:
            await asyncio.sleep(2 ** attempts)  # exponential backoff before retry
            await broker.publish(
                {**message, "attempts": attempts + 1},
                queue=payments_queue.name,
            )


if __name__ == "__main__":
    asyncio.run(app.run())
