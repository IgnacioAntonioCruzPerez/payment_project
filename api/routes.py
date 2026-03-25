from fastapi import APIRouter, HTTPException
from .schemas import PaymentCreate, PaymentResponse

router = APIRouter()

payments_db = {} 

@router.post("/payments", response_model=PaymentResponse, status_code=202)
async def create_payment(payment: PaymentCreate):
    if payment.idempotency_key in payments_db:
        return payments_db[payment.idempotency_key]
    payment_id = "pay_" + str(len(payments_db) + 1)
    payment_data = {
        "id": payment_id,
        "status": "pending",
        "amount": payment.amount,
        "currency": payment.currency,
        "description": payment.description,
        "metadata": payment.metadata,
        "webhook_url": payment.webhook_url
    }
    payments_db[payment.idempotency_key] = payment_data
    return payment_data

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str):
    for p in payments_db.values():
        if p["id"] == payment_id:
            return p
    raise HTTPException(status_code=404, detail="Payment not found")