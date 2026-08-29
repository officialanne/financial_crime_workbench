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


def get_case_by_id(case_id: int) -> Optional[Dict[str, Any]]:
    """Fetch complete case dossier: linked customers, transactions, notes, and AI summaries."""
    with get_db_connection() as conn:
        case_row = conn.execute(
            """
            SELECT
                c.CaseID AS case_id,
                c.Priority AS priority,
                c.Status AS status,
                c.AssignedAnalystID AS assigned_analyst_id,
                a.Name AS analyst_name,
                a.Email AS analyst_email,
                c.CreatedAt AS created_at,
                c.ClosedAt AS closed_at,
                c.Notes AS notes,
                c.AlertID AS alert_id
            FROM Cases c
            LEFT JOIN Analyst a ON c.AssignedAnalystID = a.AnalystID
            WHERE c.CaseID = ?
            """,
            (case_id,),
        ).fetchone()

        if not case_row:
            return None

        case_data = dict(case_row)

        # Fetch linked customers
        cust_rows = conn.execute(
            """
            SELECT
                cust.CustomerID AS customer_id,
                p.Name AS name,
                p.PartyType AS party_type,
                p.CountryID AS country_id,
                cust.Occupation AS occupation,
                cust.RiskRatingName AS risk_rating_name
            FROM CaseCustomer cc
            JOIN Customer cust ON cc.CustomerID = cust.CustomerID
            JOIN Party p ON cust.PartyID = p.PartyID
            WHERE cc.CaseID = ?
            """,
            (case_id,),
        ).fetchall()

        case_data["linked_customers"] = [dict(r) for r in cust_rows]

        # Fetch linked transactions with risk scoring
        txn_rows = conn.execute(
            """
            SELECT
                t.TransactionID AS transaction_id,
                t.SenderPartyID AS sender_party_id,
                t.ReceiverPartyID AS receiver_party_id,
                t.MerchantPartyID AS merchant_party_id,
                t.Amount AS amount,
                t.CurrencyID AS currency_id,
                t.TransactionDate AS transaction_date,
                t.TransactionType AS transaction_type,
                t.OriginCountryID AS origin_country_id
            FROM CaseTransaction ct
            JOIN Transactions t ON ct.TransactionID = t.TransactionID
            WHERE ct.CaseID = ?
            """,
            (case_id,),
        ).fetchall()

        enriched_txns = []
        for r in txn_rows:
            t_dict = dict(r)
            risk = evaluate_transaction_risk(t_dict)
            t_dict["risk_score"] = risk.score
            t_dict["risk_category"] = risk.category
            t_dict["reasons"] = risk.reasons
            enriched_txns.append(t_dict)
        case_data["linked_transactions"] = enriched_txns

        # Fetch audit activity log
        act_rows = conn.execute(
            """
            SELECT
                ca.ActivityID AS activity_id,
                ca.CaseID AS case_id,
                ca.AnalystID AS analyst_id,
                a.Name AS analyst_name,
                ca.ActivityType AS activity_type,
                ca.Description AS description,
                ca.CreatedAt AS created_at
            FROM CaseActivity ca
            LEFT JOIN Analyst a ON ca.AnalystID = a.AnalystID
            WHERE ca.CaseID = ?
            ORDER BY ca.ActivityID DESC
            """,
            (case_id,),
        ).fetchall()
        case_data["activities"] = [dict(r) for r in act_rows]

        #  Fetch investigation summary if available
        summary_row = conn.execute(
            "SELECT SummaryText FROM InvestigationSummary WHERE CaseID = ? ORDER BY SummaryID DESC LIMIT 1",
            (case_id,),
        ).fetchone()
        case_data["summary_text"] = summary_row["SummaryText"] if summary_row else None

        return case_data


def create_case(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new case, attach initial evidence, and record audit activity."""

    today_str = date.today().isoformat()

    with get_db_connection() as conn:
        # Determine next ID
        max_id_row = conn.execute(
            "SELECT COALESCE(MAX(CaseID), 6000) FROM Cases"
        ).fetchone()
        new_case_id = max_id_row[0] + 1

        conn.execute(
            """
            INSERT INTO Cases (CaseID, Priority, Status, AssignedAnalystID, CreatedAt, ClosedAt, Notes, AlertID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_case_id,
                case_data.get("priority", "HIGH"),
                case_data.get("status", "OPEN"),
                case_data.get("assigned_analyst_id"),
                today_str,
                None,
                case_data.get("notes"),
                case_data.get("alert_id"),
            ),
        )

        # Attach initial transactions
        for tx_id in case_data.get("initial_transaction_ids", []):
            conn.execute(
                "INSERT OR IGNORE INTO CaseTransaction (CaseID, TransactionID) VALUES (?, ?)",
                (new_case_id, tx_id),
            )

        # Attach initial customers
        for cust_id in case_data.get("initial_customer_ids", []):
            conn.execute(
                "INSERT OR IGNORE INTO CaseCustomer (CaseID, CustomerID) VALUES (?, ?)",
                (new_case_id, cust_id),
            )

        # Record CASE_OPENED activity
        max_act_id = (
            conn.execute(
                "SELECT COALESCE(MAX(ActivityID), 8000) FROM CaseActivity"
            ).fetchone()[0]
            + 1
        )
        conn.execute(
            """
            INSERT INTO CaseActivity (ActivityID, CaseID, AnalystID, ActivityType, Description, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                max_act_id,
                new_case_id,
                case_data.get("assigned_analyst_id"),
                "CASE_OPENED",
                f"Investigation opened with priority {case_data.get('priority', 'HIGH')}.",
                today_str,
            ),
        )
        conn.commit()

    return get_case_by_id(new_case_id) or {}


def update_case(case_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update case status, priority, or assigned analyst, updating lifecycle dates."""

    with get_db_connection() as conn:
        current = conn.execute(
            "SELECT * FROM Cases WHERE CaseID = ?", (case_id,)
        ).fetchone()
        if not current:
            return None

        new_status = updates.get("status") or current["Status"]
        new_priority = updates.get("priority") or current["Priority"]
        new_analyst = (
            updates.get("assigned_analyst_id")
            if "assigned_analyst_id" in updates
            else current["AssignedAnalystID"]
        )
        new_notes = (
            updates.get("notes")
            if updates.get("notes") is not None
            else current["Notes"]
        )

        closed_at = current["ClosedAt"]
        if new_status == "CLOSED" and current["Status"] != "CLOSED":
            closed_at = date.today().isoformat()
        elif new_status != "CLOSED":
            closed_at = None

        conn.execute(
            """
            UPDATE Cases
            SET Priority = ?, Status = ?, AssignedAnalystID = ?, Notes = ?, ClosedAt = ?
            WHERE CaseID = ?
            """,
            (new_priority, new_status, new_analyst, new_notes, closed_at, case_id),
        )

        # Record activity if status changed
        if new_status != current["Status"]:
            max_act_id = (
                conn.execute(
                    "SELECT COALESCE(MAX(ActivityID), 8000) FROM CaseActivity"
                ).fetchone()[0]
                + 1
            )
            act_type = "CASE_CLOSED" if new_status == "CLOSED" else "STATUS_UPDATED"
            conn.execute(
                """
                INSERT INTO CaseActivity (ActivityID, CaseID, AnalystID, ActivityType, Description, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    max_act_id,
                    case_id,
                    new_analyst,
                    act_type,
                    f"Case status transition from {current['Status']} to {new_status}.",
                    date.today().isoformat(),
                ),
            )

        conn.commit()

    return get_case_by_id(case_id)


def add_case_activity(case_id: int, activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a timestamped investigation note or audit action to a case."""

    today_str = date.today().isoformat()
    with get_db_connection() as conn:
        max_act_id = (
            conn.execute(
                "SELECT COALESCE(MAX(ActivityID), 8000) FROM CaseActivity"
            ).fetchone()[0]
            + 1
        )
        conn.execute(
            """
            INSERT INTO CaseActivity (ActivityID, CaseID, AnalystID, ActivityType, Description, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                max_act_id,
                case_id,
                activity_data.get("analyst_id"),
                activity_data.get("activity_type", "NOTE_ADDED"),
                activity_data.get("description"),
                today_str,
            ),
        )
        conn.commit()

    return {
        "activity_id": max_act_id,
        "case_id": case_id,
        "analyst_id": activity_data.get("analyst_id"),
        "activity_type": activity_data.get("activity_type", "NOTE_ADDED"),
        "description": activity_data.get("description"),
        "created_at": today_str,
    }


def link_transaction_to_case(case_id: int, transaction_id: int) -> bool:
    """Associate a suspicious transaction with an ongoing case."""
    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO CaseTransaction (CaseID, TransactionID) VALUES (?, ?)",
            (case_id, transaction_id),
        )
        conn.commit()
    return True


def link_customer_to_case(case_id: int, customer_id: int) -> bool:
    """Associate a customer with an ongoing case."""
    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO CaseCustomer (CaseID, CustomerID) VALUES (?, ?)",
            (case_id, customer_id),
        )
        conn.commit()
    return True


def get_all_analysts() -> List[Dict[str, Any]]:
    """Retrieve active compliance analysts for assignment dropdowns."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT AnalystID, Name, Email, Team, Active FROM Analyst WHERE Active = 'Y'"
        ).fetchall()
        return [dict(r) for r in rows]
