import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)


async def wait_for_db():
    for i in range(10): 
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda conn: None)
            print("✅ DB connected")
            return
        except Exception:
            print(f"⏳ DB not ready... retry {i}")
            await asyncio.sleep(2)

    raise Exception("❌ DB connection failed")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session