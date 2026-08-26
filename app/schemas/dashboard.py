from typing import Dict, List, Optional
from pydantic import BaseModel
from app.schemas.risk import TransactionWithRiskResponse

class OperationalKPIs(BaseModel):
    total_transactions: int
    total_volume: int
    average_amount: float
    max_amount: int

class RiskKPIs(BaseModel):
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_alerts: int
    open_cases: int

class CustomerKPIs(BaseModel):
    total_customers: int
    high_risk_customers: int

class TimeSeriesPoint(BaseModel):
    period: str
    transaction_count: int
    total_volume: int

class CountryMetric(BaseModel):
    country_id: str
    country_name: Optional[str] = None
    transaction_count: int
    total_volume: int

class DashboardSummaryResponse(BaseModel):
    operational: OperationalKPIs
    risk: RiskKPIs
    customers: CustomerKPIs
    trends: List[TimeSeriesPoint]
    top_countries: List[CountryMetric]
    recent_high_risk: List[TransactionWithRiskResponse]

