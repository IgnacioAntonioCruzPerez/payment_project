from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Outbox


async def get_pending_outbox_events(db: AsyncSession) -> list[Outbox]:
    result = await db.execute(select(Outbox).where(Outbox.status == "pending"))
    return result.scalars().all()
