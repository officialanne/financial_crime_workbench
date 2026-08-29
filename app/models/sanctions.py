# Defines the pure Python dataclasses for a watchlist record and
# a structured match result without framework dependencies
from dataclasses import dataclass
from typing import Optional


@dataclass
class SanctionRecord:
    sanction_id: int
    entity_name: str
    country_id: Optional[str]
    programme: Optional[str]
    source: Optional[str]
    listed_date: Optional[str]
    delisted_date: Optional[str] = None
    party_id: Optional[int] = None


@dataclass
class SanctionMatch:
    sanction_id: int
    entity_name: str
    query_name: str
    similarity_score: float
    confidence_percentage: int
    match_type: str
    country_id: Optional[str]
    programme: Optional[str]
    source: Optional[str]
    listed_date: Optional[str]
    is_active: bool
    reason: str
