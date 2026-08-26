from typing import List, Optional
from fastapi import APIRouter, Query
from app.schemas.dashboard import (
    CountryMetric,
    DashboardSummaryResponse,
    OperationalKPIs,
    RiskKPIs,
    TimeSeriesPoint,
)
from app.services import analytics_service

router = APIRouter(prefix="/dashboard", tags=["Analytics & Dashboard"])

@router.get("/", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    country: Optional[str] = Query(None, min_length=2, max_length=2, description="Filter summary by country code")
):
    """Retrive full executive dashboard summary with KPIs, trends, and risk metrics"""
    return analytics_service.get_dashboard_summary(country=country)

@router.get("/operational", response_model=OperationalKPIs)
def get_operational_metrics(country: Optional[str] = None):
    """Retrieve operational transaction KPIs."""
    return analytics_service.get_operational_kpis(country=country)


@router.get("/risk", response_model=RiskKPIs)
def get_risk_metrics():
    """Retrieve overall AML risk distribution and alert/case numbers."""
    return analytics_service.get_risk_kpis()


@router.get("/trends", response_model=List[TimeSeriesPoint])
def get_transaction_trends(country: Optional[str] = None, limit: int = 12):
    """Retrieve monthly transaction trends over time."""
    return analytics_service.get_transaction_trends(country=country, limit=limit)


@router.get("/countries", response_model=List[CountryMetric])
def get_top_countries(limit: int = 10):
    """Retrieve top transaction destination/origin countries."""
    return analytics_service.get_top_countries(limit=limit)


