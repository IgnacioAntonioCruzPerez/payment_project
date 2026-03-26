from pydantic import BaseModel, Field
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime
import uuid


class PaymentCreate(BaseModel):
    amount: Decimal
    currency: str = Field(..., examples=["USD"])
    description: str
    metadata: Optional[Dict] = None
    webhook_url: str


class PaymentResponse(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    description: str
    metadata: Optional[Dict]
    status: str
    webhook_url: str
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True