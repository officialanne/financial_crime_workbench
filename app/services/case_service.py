from datetime import date
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from app.services.risk_engine import evaluate_transaction_risk

DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "aml.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def list_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    analyst_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List investigation cases with evidence counts and analyst metadata."""
    query = """
        SELECT
            c.CaseID AS case_id,
            c.Priority AS priority,
            c.Status AS status,
            c.AssignedAnalystID AS assigned_analyst_id,
            a.Name AS analyst_name,
            c.CreatedAt AS created_at,
            c.ClosedAt AS closed_at,
            c.Notes AS notes,
            c.AlertID AS alert_id,
            (SELECT COUNT(*) FROM CaseTransaction ct WHERE ct.CaseID = c.CaseID) AS transaction_count,
            (SELECT COUNT(*) FROM CaseCustomer cc WHERE cc.CaseID = c.CaseID) AS customer_count
        FROM Cases c
        LEFT JOIN Analyst a ON c.AssignedAnalystID = a.AnalystID
        WHERE 1=1
    """
    params: List[Any] = []
    
    if status:
        query += " AND c.Status = ?"
        params.append(status.upper())

    if priority:
        query += " AND c.Priority = ?"
        params.append(priority.upper())

    if analyst_id:
        query += " AND c.AssignedAnalystID = ?"
        params.append(analyst_id)

    query += " ORDER BY c.CaseID DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]



