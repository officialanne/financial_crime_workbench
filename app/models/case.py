# Defines the pure Python dataclass models for an investigation case 
# and its associated activity log entries without any database or framework dependencies
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CaseActivityModel:
    activity_id: int
    case_id: int
    analyst_id: Optional[int]
    activity_type: str
    description: Optional[str]
    created_at: str


@dataclass
class CaseModel:
    case_id: int
    priority: str
    status: str
    assigned_analyst_id: Optional[int]
    created_at: str
    closed_at: Optional[str] = None
    notes: Optional[str] = None
    alert_id: Optional[int] = None
    linked_transaction_ids: List[int] = field(default_factory=list)
    linked_customer_ids: List[int] = field(default_factory=list)