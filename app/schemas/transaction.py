# controlling what data leaves the API when a client queries a transaction

from typing import Optional

# to handle type validation and JSON serialisation
from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    transaction_id: int
    sender_party_id: int
    receiver_party_id: int
    merchant_party_id: Optional[int] = None
    amount: int
    currency_id: str
    transaction_date: str
    transaction_type: Optional[str] = None
    origin_country_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
