from pydantic import BaseModel, Field
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime
from enum import Enum
import uuid


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"


class PaymentCreate(BaseModel):
    amount: Decimal
    currency: Currency = Field(..., examples=["USD"])
    description: str
    metadata: Optional[Dict] = None
    webhook_url: str


class PaymentResponse(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: Currency
    description: str

    metadata: Optional[Dict] = Field(None, validation_alias="metadata_")

    status: PaymentStatus
    webhook_url: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }