from pydantic import BaseModel
from typing import Optional, Dict

class PaymentCreate(BaseModel):
    amount: float
    currency: str
    description: str
    metadata: Optional[Dict] = {}
    webhook_url: str
    idempotency_key: str

class PaymentResponse(BaseModel):
    id: str
    status: str
    amount: float
    currency: str
    description: str
    metadata: Optional[Dict]
    webhook_url: str