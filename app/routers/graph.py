# show the graph and statistics enpoints via FastAPI,
# enabling microservices and the frontend to query database through network analysis
from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.graph import GraphResponse, NetworkStatistics
from app.services import graph_analysis

router = APIRouter(prefix="/graph", tags=["Network Analysis"])


@router.get("/", response_model=GraphResponse)
def get_transaction_graph(
    min_amount: Optional[int] = Query(
        None, ge=0, description="Filter by minimum amount"
    ),
    country: Optional[str] = Query(
        None, min_length=2, max_length=2, description="2-letter country code"
    ),
    risk_category: Optional[str] = Query(
        None, description="Filter by HIGH, MEDIUM, or LOW"
    ),
    customer_id: Optional[int] = Query(
        None, description="Focus on specific Customer ID"
    ),
    party_id: Optional[int] = Query(None, description="Focus on specific Party ID"),
    limit: int = Query(
        100, ge=10, le=500, description="Max transaction edges to include in graph"
    ),
):
    """Retrieve transaction network graph with nodes, edges, and centrality analytics."""
    return graph_analysis.build_network_graph(
        min_amount=min_amount,
        country=country,
        risk_category=risk_category,
        customer_id=customer_id,
        party_id=party_id,
        limit=limit,
    )


@router.get("/statistics", response_model=NetworkStatistics)
def get_network_statistics(
    min_amount: Optional[int] = Query(None, ge=0),
    country: Optional[str] = Query(None, min_length=2, max_length=2),
):
    """Retrieve macro-level network graph metrics."""
    data = graph_analysis.build_network_graph(
        min_amount=min_amount, country=country, limit=200
    )
    return data["statistics"]
