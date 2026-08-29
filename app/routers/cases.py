# Exposes the complete Case Management REST API for querying case queues,
# creating cases, updating workflow transitions, appending investigation notes,
# and attaching evidence records.
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.case import (
    CaseActivityCreate,
    CaseActivityResponse,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseListItemResponse,
    CaseUpdateRequest,
)
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["Case Management"])


@router.get("/", response_model=List[CaseListItemResponse])
def get_cases(
    status: Optional[str] = Query(
        None, description="Filter by OPEN, IN_PROGRESS, CLOSED"
    ),
    priority: Optional[str] = Query(
        None, description="Filter by LOW, MEDIUM, HIGH, CRITICAL"
    ),
    analyst_id: Optional[int] = Query(
        None, description="Filter by assigned Analyst ID"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List investigation cases with evidence counts and filtering."""
    return case_service.list_cases(
        status=status,
        priority=priority,
        analyst_id=analyst_id,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=CaseDetailResponse, status_code=201)
def create_case(case_in: CaseCreateRequest):
    """Create a new investigation case and attach initial evidence."""
    created = case_service.create_case(case_in.model_dump())
    if not created:
        raise HTTPException(
            status_code=400, detail="Could not create investigation case."
        )
    return created


@router.get("/analysts", response_model=List[Dict[str, Any]])
def list_analysts():
    """Retrieve active compliance analysts."""
    return case_service.get_all_analysts()


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case_details(case_id: int):
    """Fetch complete case dossier including linked transactions, customers, and activity log."""
    case_data = case_service.get_case_by_id(case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail=f"Case #{case_id} not found.")
    return case_data


@router.patch("/{case_id}", response_model=CaseDetailResponse)
def update_case(case_id: int, updates: CaseUpdateRequest):
    """Update case status, priority, notes, or assigned analyst."""
    updated = case_service.update_case(case_id, updates.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Case #{case_id} not found.")
    return updated


@router.post("/{case_id}/activities", response_model=CaseActivityResponse)
def add_case_note(case_id: int, activity_in: CaseActivityCreate):
    """Add a timestamped investigation note or audit activity to a case."""
    case_exists = case_service.get_case_by_id(case_id)
    if not case_exists:
        raise HTTPException(status_code=404, detail=f"Case #{case_id} not found.")
    return case_service.add_case_activity(case_id, activity_in.model_dump())


@router.post("/{case_id}/transactions/{transaction_id}")
def link_transaction(case_id: int, transaction_id: int):
    """Attach a suspicious transaction to an ongoing case."""
    case_service.link_transaction_to_case(case_id, transaction_id)
    return {
        "status": "success",
        "message": f"Transaction #{transaction_id} attached to Case #{case_id}",
    }


@router.post("/{case_id}/customers/{customer_id}")
def link_customer(case_id: int, customer_id: int):
    """Attach a customer to an ongoing case."""
    case_service.link_customer_to_case(case_id, customer_id)
    return {
        "status": "success",
        "message": f"Customer #{customer_id} attached to Case #{case_id}",
    }
