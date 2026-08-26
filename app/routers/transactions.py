# enpoints for the frontend or API consumers to search, filter, and inspect transactions

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.transaction import TransactionResponse
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    limit: int = Query(100, ge=1, le=1000, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    min_amount: Optional[int] = Query(
        None, ge=0, description="Filter by minimum amount"
    ),
    max_amount: Optional[int] = Query(
        None, ge=0, description="Filter by maximum amount"
    ),
    country: Optional[str] = Query(
        None, min_length=2, max_length=2, description="2-letter country code"
    ),
    party_id: Optional[int] = Query(None, description="Sender or receiver party ID"),
    customer_id: Optional[int] = Query(None, description="Search by Customer ID"),
    currency_id: Optional[str] = Query(
        None, min_length=3, max_length=3, description="3-letter currency code"
    ),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Retrieve transactions with optional filtering and pagination"""

    return transaction_service.list_transactions(
        limit=limit,
        offset=offset,
        min_amount=min_amount,
        max_amount=max_amount,
        country=country,
        party_id=party_id,
        customer_id=customer_id,
        currency_id=currency_id,
        start_date=start_date,
        end_date=end_date,
    )


# get transactions by id
@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int):
    """Fetch details of a single transaction by ID"""

    transaction = transaction_service.get_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=404, detail=f"Transaction {transaction_id} not found"
        )
    return transaction
