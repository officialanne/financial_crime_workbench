# defining a python representation of a transaction record as stored in the database
from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    transaction_id: int
    sender_party_id: int
    receiver_party_id: int
    amount: int
    currency_id: str
    transaction_date: str
    transaction_type: Optional[str] = None
    merchant_party_id: Optional[int] = None
    origin_country_id: Optional[str] = None
