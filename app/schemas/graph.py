# Establishes Pydantic contracts for graph nodes, directed transaction edges, structural network metrics, and hub entity rankings for the API layer.
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GraphNode(BaseModel):
    id: int
    label: str
    party_type: str
    country_id: Optional[str] = None
    customer_id: Optional[int] = None
    is_sanctioned: bool = False
    degree: int = 0
    betweenness_centrality: float = 0.0
    risk_score: int = 0


class GraphEdge(BaseModel):
    source: int
    target: int
    transaction_id: int
    amount: int
    currency_id: str
    transaction_date: str
    transaction_type: Optional[str] = None
    risk_score: int = 0


class NetworkHub(BaseModel):
    party_id: int
    name: str
    party_type: str
    degree: int
    betweenness_centrality: float


class NetworkStatistics(BaseModel):
    total_nodes: int
    total_edges: int
    connected_components_count: int
    density: float
    top_hubs: List[NetworkHub]


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    statistics: NetworkStatistics
