# Establishes Pydantic contracts for screening queries, confidence 
# score results, and watchlist records returned over HTTP
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SanctionScreenRequest(BaseModel):
    query_name: str = Field(..., min_length=2, description="Name of individual or company to screen")
    threshold: float = Field(0.70, ge=0.50, le=1.0, description="Fuzzy match sensitivity threshold (0.50 to 1.0)")
    country_id: Optional[str] = Field(None, max_length=2, description="Optional 2-letter country code filter")


class SanctionMatchResponse(BaseModel):
    sanction_id: int
    entity_name: str
    query_name: str
    similarity_score: float
    confidence_percentage: int
    match_type: str
    country_id: Optional[str] = None
    programme: Optional[str] = None
    source: Optional[str] = None
    listed_date: Optional[str] = None
    is_active: bool = True
    reason: str

    model_config = ConfigDict(from_attributes=True)


class SanctionScreenResponse(BaseModel):
    query_name: str
    total_matches: int
    matches: List[SanctionMatchResponse]


class SanctionRecordResponse(BaseModel):
    sanction_id: int
    party_id: Optional[int] = None
    entity_name: str
    country_id: Optional[str] = None
    programme: Optional[str] = None
    source: Optional[str] = None
    listed_date: Optional[str] = None
    delisted_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CaseSanctionLinkRequest(BaseModel):
    case_id: int
    sanction_id: int