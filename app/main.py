from fastapi import FastAPI
from app.db.session import wait_for_db
from app.api.payments import router as payments_router

app = FastAPI()

app.include_router(payments_router)


@app.on_event("startup")
async def on_startup():
    await wait_for_db()


@app.get("/")
async def root():
    return {"message": "Payment Service Running"}