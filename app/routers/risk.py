from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.risk import RiskAssessmentResponse, TransactionWithRiskResponse
from app.services import transaction_service

router = APIRouter(prefix="/risk", tags=["Risk Engine"])


@router.get("/transaction/{transaction_id}", response_model=RiskAssessmentResponse)
def get_transaction_risk(transaction_id: int):
    """Get full risk score, category, and triggered rules explanation for a transaction."""
    txn = transaction_service.get_transaction_by_id(transaction_id)
    if not txn:
        raise HTTPException(
            status_code=404, detail=f"Transaction {transaction_id} not found"
        )

    return {
        "transaction_id": txn["transaction_id"],
        "risk_score": txn["risk_score"],
        "risk_category": txn["risk_category"],
        "reasons": txn["reasons"],
        "triggered_rules": txn.get("triggered_rules", []),
    }


@router.get("/high", response_model=List[TransactionWithRiskResponse])
def get_high_risk_transactions(limit: int = 50):
    """Retrieve only high-risk transactions for investigation queues."""
    return transaction_service.list_transactions(limit=limit, risk_category="HIGH")
