import asyncio
from sqlalchemy import select, text
from app.db.session import async_session
from app.db.models import Outbox
from app.messaging.publisher import publish_message

async def wait_for_db():
    for i in range(30): 
        try:
            async with async_session() as db:
                await db.execute(text("SELECT 1"))
            print("✅ DB connected")
            return
        except Exception as e:
            print(f"⏳ DB not ready... retry {i} | {e}")
            await asyncio.sleep(2)

    raise Exception("❌ DB not ready after retries")


async def process_outbox():
    try:
        async with async_session() as db:
            result = await db.execute(
                select(Outbox).where(Outbox.status == "pending")
            )
            events = result.scalars().all()

            if not events:
                print("📭 No pending events")
                return

            for event in events:
                try:
                    print(f"📤 Publishing event: {event.id}")

                    await publish_message(event.payload)

                    event.status = "sent"
                    event.attempts += 1

                except Exception as e:
                    print(f"❌ Failed event {event.id}: {e}")
                    event.attempts += 1

            await db.commit()

    except Exception as e:
        print(f"❌ process_outbox error: {e}")

async def main():
    await wait_for_db()

    print("🚀 Outbox worker started")

    while True:
        await process_outbox()
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())