from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import wait_for_db
from app.api.payments import router as payments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await wait_for_db()
    yield


app = FastAPI(title="Payment Processing Service", lifespan=lifespan)

app.include_router(payments_router)


@app.get("/")
async def root():
    return {"message": "Payment Service Running"}
