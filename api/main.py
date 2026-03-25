from fastapi import FastAPI
from .routes import router

app = FastAPI(title="Payment Service")
app.include_router(router, prefix="/api/v1")