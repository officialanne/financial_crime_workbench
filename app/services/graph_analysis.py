# transform the database rows into a directed graph, centrality metrics, and detect isolated communities
# pulls filtered transaction edges, maps entity metadata (types, countries, sanctions)
# and computes graph metrics: Betweenness Centrality (identifying money mules / bridge hubs) and Connected Components (identifying isolated laundering rings).
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Set
import networkx as nx

from app.services.risk_engine import evaluate_transaction_risk

DATABASE_PATH = Path(__file__).resolve().parents[2] / "database" / "aml.db"


# get the database connection
def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# create a network graph using the database
def build_network_graph(
    min_amount: Optional[int] = None,
    country: Optional[str] = None,
    risk_category: Optional[str] = None,
    customer_id: Optional[int] = None,
    party_id: Optional[int] = None,
    limit: int = 150,
) -> Dict[str, Any]:
    """
    Constructs a directed NetworkX graph from transactions and computes
    network metrics (Degree Centrality, Betweenness, Connected Components).
    """

    query = """
        SELECT
            t.TransactionID AS transaction_id,
            t.SenderPartyID AS sender_party_id,
            t.ReceiverPartyID AS receiver_party_id,
            t.Amount AS amount,
            t.CurrencyID AS currency_id,
            t.TransactionDate AS transaction_date,
            t.TransactionType AS transaction_type,
            t.OriginCountryID AS origin_country_id
        FROM Transactions t
        WHERE 1=1
    """
    params: List[Any] = []

    if min_amount is not None:
        query += " AND t.Amount >= ?"
        params.append(min_amount)

    if country:
        query += " AND t.OriginCountryID = ?"
        params.append(country.upper())

    if party_id is not None:
        query += " AND (t.SenderPartyID = ? OR t.ReceiverPartyID = ?)"
        params.extend([party_id, party_id])

    if customer_id is not None:
        query += """
            AND (
                t.SenderPartyID IN (SELECT PartyID FROM Customer WHERE CustomerID = ?)
                OR t.ReceiverPartyID IN (SELECT PartyID FROM Customer WHERE CustomerID = ?)
            )
        """
        params.extend([customer_id, customer_id])

    query += " ORDER BY t.TransactionDate DESC LIMIT ?"
    params.append(limit)

    with get_db_connection() as conn:
        txns = conn.execute(query, params).fetchall()

        # if nothing is returned
        if not txns:
            return {
                "nodes": [],
                "edges": [],
                "statistics": {
                    "total_nodes": 0,
                    "total_edges": 0,
                    "connected_components_count": 0,
                    "density": 0.0,
                    "top_hubs": [],
                },
            }

        # collect unique party IDs involved in the transactions
        party_ids: Set[int] = set()
        for row in txns:
            party_ids.add(row["sender_party_id"])
            party_ids.add(row["receiver_party_id"])

        # query party, customer, and sanction data for detailed nodes
        placeholders = ",".join("?" for _ in party_ids)
        party_query = f"""
            SELECT
                p.PartyID,
                p.Name,
                p.PartyType,
                p.CountryID,
                c.CustomerID,
                s.SanctionID IS NOT NULL AS is_sanctioned
            FROM Party p
            LEFT JOIN Customer c ON p.PartyID = c.PartyID
            LEFT JOIN Sanction s ON p.PartyID = s.PartyID
            WHERE p.PartyID IN ({placeholders})
        """
        parties_data = {
            r["PartyID"]: dict(r)
            for r in conn.execute(party_query, list(party_ids)).fetchall()
        }

        # build networkx directed graph
        G = nx.DiGraph()

        # create the nodes
        for pid in party_ids:
            p_meta = parties_data.get(pid, {})
            G.add_node(
                pid,
                label=p_meta.get("Name", f"Party #{pid}"),
                party_type=p_meta.get("PartyType", "UNKNOWN"),
                country_id=p_meta.get("CountryID", ""),
                customer_id=p_meta.get("CustomerID"),
                is_sanctioned=bool(p_meta.get("is_sanctioned", False)),
            )

        # create the edges
        edge_list: List[Dict[str, Any]] = []
        for row in txns:
            t_dict = dict(row)
            risk = evaluate_transaction_risk(t_dict)

            # apply risk filter if requested
            if risk_category and risk_category != risk_category.upper():
                continue

            # retriveing senders and receivers in each transaction
            u = t_dict["sender_party_id"]
            v = t_dict["receiver_party_id"]

            G.add_edge(
                u,
                v,
                transaction_id=t_dict["transaction_id"],
                amount=t_dict["amount"],
                currency=t_dict["currency_id"],
                date=t_dict["transaction_date"],
                risk_score=risk.score,
            )

        # Compute Network Centrality & Component Metrics
        betweenness = nx.betweenness_centrality(G) if len(G) > 0 else {}
        degrees = dict(G.degree())
        comp_count = nx.number_weakly_connected_components(G) if len(G) > 0 else 0
        density = round(nx.density(G), 4) if len(G) > 0 else 0.0

        # format the nodes
        nodes_list: List[Dict[str, Any]] = []
        for node_id, attrs in G.nodes(data=True):
            b_score = round(betweenness.get(node_id, 0.0), 4)
            deg = degrees.get(node_id, 0)
            nodes_list.append(
                {
                    "id": node_id,
                    "label": attrs.get("label", str(node_id)),
                    "party_type": attrs.get("party_type", "UNKNOWN"),
                    "country_id": attrs.get("country_id"),
                    "customer_id": attrs.get("customer_id"),
                    "is_sanctioned": attrs.get("is_sanctioned", False),
                    "degree": deg,
                    "betweenness_centrality": b_score,
                    "risk_score": (
                        80 if attrs.get("is_sanctioned") else int(b_score * 100)
                    ),
                }
            )

        # rank top hubs / intermediaries (high betweenness & degree)
        sorted_hubs = sorted(
            nodes_list,
            key=lambda x: (x["betweenness_centrality"], x["degree"]),
            reverse=True,
        )[:5]

        top_hubs = [
            {
                "party_id": h["id"],
                "name": h["label"],
                "party_type": h["party_type"],
                "degree": h["degree"],
                "betweenness_centrality": h["betweenness_centrality"],
            }
            for h in sorted_hubs
        ]

        # return the graph response
        return {
            "nodes": nodes_list,
            "edges": edge_list,
            "statistics": {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "connected_components_count": comp_count,
                "density": density,
                "top_hubs": top_hubs,
            },
        }
