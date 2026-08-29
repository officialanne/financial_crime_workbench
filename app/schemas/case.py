# Establishes Pydantic contracts for case creation payloads, lifecycle updates, activity notes,
# and full evidence dossiers returned by the API
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.risk import TransactionWithRiskResponse


class CaseCreateRequest(BaseModel):
    priority: str = "HIGH"
    status: str = "OPEN"
    assigned_analyst_id: Optional[int] = 1
    notes: Optional[str] = None
    alert_id: Optional[int] = None
    initial_transaction_ids: Optional[List[int]] = []
    initial_customer_ids: Optional[List[int]] = []


class CaseUpdateRequest(BaseModel):
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_analyst_id: Optional[int] = None
    notes: Optional[str] = None


class CaseActivityCreate(BaseModel):
    analyst_id: Optional[int] = None
    activity_type: str = "NOTE_ADDED"
    description: str


class CaseActivityResponse(BaseModel):
    activity_id: int
    case_id: int
    analyst_id: Optional[int] = None
    analyst_name: Optional[str] = None
    activity_type: str
    description: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class LinkedCustomerResponse(BaseModel):
    customer_id: int
    name: str
    party_type: str
    country_id: Optional[str] = None
    occupation: Optional[str] = None
    risk_rating_name: Optional[str] = None


class CaseListItemResponse(BaseModel):
    case_id: int
    priority: str
    status: str
    assigned_analyst_id: Optional[int] = None
    analyst_name: Optional[str] = None
    created_at: str
    closed_at: Optional[str] = None
    notes: Optional[str] = None
    alert_id: Optional[int] = None
    transaction_count: int = 0
    customer_count: int = 0


class CaseDetailResponse(BaseModel):
    case_id: int
    priority: str
    status: str
    assigned_analyst_id: Optional[int] = None
    analyst_name: Optional[str] = None
    analyst_email: Optional[str] = None
    created_at: str
    closed_at: Optional[str] = None
    notes: Optional[str] = None
    alert_id: Optional[int] = None
    linked_customers: List[LinkedCustomerResponse] = []
    linked_transactions: List[TransactionWithRiskResponse] = []
    activities: List[CaseActivityResponse] = []
    summary_text: Optional[str] = None
