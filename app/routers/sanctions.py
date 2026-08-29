# xposes endpoints to screen names on-demand, screen customers by ID,
# search the sanctions database, and link matches directly to investigation cases.
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.sanctions import (
    CaseSanctionLinkRequest,
    SanctionMatchResponse,
    SanctionRecordResponse,
    SanctionScreenRequest,
    SanctionScreenResponse,
)
from app.services import sanctions_service

router = APIRouter(prefix="/sanctions", tags=["Sanctions Screening"])


@router.post("/screen", response_model=SanctionScreenResponse)
def screen_entity(request: SanctionScreenRequest):
    """Screen an individual or business entity against active sanctions watchlists."""
    return sanctions_service.screen_name(
        query_name=request.query_name,
        threshold=request.threshold,
        country_id=request.country_id,
    )


@router.get("/customer/{customer_id}", response_model=SanctionScreenResponse)
def screen_customer(
    customer_id: int,
    threshold: float = Query(
        0.70, ge=0.50, le=1.0, description="Fuzzy match sensitivity threshold"
    ),
):
    """Screen a customer by Customer ID against sanctions lists."""
    return sanctions_service.screen_customer_by_id(
        customer_id=customer_id, threshold=threshold
    )


@router.get("/", response_model=List[SanctionRecordResponse])
def get_sanctions_watchlist(
    programme: Optional[str] = Query(None, description="Filter by sanctions programme"),
    source: Optional[str] = Query(None, description="Filter by watchlist source"),
    country_id: Optional[str] = Query(None, min_length=2, max_length=2),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retrieve and filter watchlist entities."""
    return sanctions_service.list_sanctions(
        programme=programme,
        source=source,
        country_id=country_id,
        limit=limit,
        offset=offset,
    )


@router.post("/link-case")
def link_sanction_to_case(link: CaseSanctionLinkRequest):
    """Attach a sanction match result to an existing case."""
    sanctions_service.link_sanction_to_case(
        case_id=link.case_id, sanction_id=link.sanction_id
    )
    return {
        "status": "success",
        "message": f"Sanction #{link.sanction_id} attached to Case #{link.case_id}",
    }
