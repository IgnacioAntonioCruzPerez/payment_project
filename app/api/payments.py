from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import create_payment, get_payment
from app.core.config import settings

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("", response_model=PaymentResponse, status_code=202)
async def create_payment_endpoint(
    payload: PaymentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    _: None = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    payment = await create_payment(db, payload, idempotency_key)
    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_endpoint(
    payment_id: str,
    _: None = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    payment = await get_payment(db, payment_id)

    if not payment:
        raise HTTPException(404, "Payment not found")

    return payment