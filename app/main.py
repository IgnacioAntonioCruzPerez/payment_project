from fastapi import FastAPI
from app.db.session import engine, wait_for_db
from app.api.payments import router as payments_router
from app.db.models import Base
from app.db import models 

app = FastAPI()

app.include_router(payments_router)


@app.on_event("startup")
async def on_startup():
    await wait_for_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "Payment Service Running"}