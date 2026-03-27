import asyncio
from sqlalchemy import select, text
from app.db.session import async_session
from app.db.models import Outbox
from app.core.config import settings
from faststream.rabbit import RabbitBroker, RabbitQueue

MAX_ATTEMPTS = 3
POLL_INTERVAL = 5

broker = RabbitBroker(settings.RABBITMQ_URL)
payments_queue = RabbitQueue(settings.PAYMENTS_QUEUE, durable=True)


async def wait_for_db():
    for i in range(30):
        try:
            async with async_session() as db:
                await db.execute(text("SELECT 1"))
            print("✅ DB connected")
            return
        except Exception as e:
            print(f"⏳ DB not ready, retry {i}: {e}")
            await asyncio.sleep(2)
    raise RuntimeError("❌ DB not ready after retries")


async def process_outbox():
    try:
        async with async_session() as db:
            result = await db.execute(
                select(Outbox).where(Outbox.status == "pending")
            )
            events = result.scalars().all()

            if not events:
                return

            for event in events:
                if event.attempts >= MAX_ATTEMPTS:
                    event.status = "dead"
                    continue
                try:
                    print(f"📤 Publishing outbox event {event.id}")
                    await broker.publish(event.payload, queue=payments_queue.name)
                    event.status = "sent"
                    event.attempts += 1
                except Exception as e:
                    print(f"❌ Failed to publish event {event.id}: {e}")
                    event.attempts += 1
                    if event.attempts >= MAX_ATTEMPTS:
                        event.status = "dead"

            await db.commit()

    except Exception as e:
        print(f"❌ process_outbox error: {e}")


async def main():
    await wait_for_db()

    async with broker:
        print("🚀 Outbox worker started")
        while True:
            await process_outbox()
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
