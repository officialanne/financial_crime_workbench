from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from app.services.risk_engine import evaluate_transaction_risk

DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "aml.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# querying the database for operational KPIs
def get_operational_kpis(country: Optional[str] = None) -> Dict[str, Any]:
    """Calculate high-level operational statistics using SQL aggregations."""

    query = """
        SELECT
            COUNT(*) AS total_transactions,
            COALESCE(SUM(Amount), 0) AS total_volume,
            COALESCE(AVG(Amount), 0.0) AS average_amount,
            COALESCE(MAX(Amount), 0) AS max_amount
        FROM Transactions
        WHERE 1=1
    """
    params = []
    if country:
        query += " AND OriginCountryID = ?"
        params.append(country.upper())

    with get_db_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return {
            "total_transactions": row["total_transactions"],
            "total_volume": row["total_volume"],
            "average_amount": round(row["average_amount"], 2),
            "max_amount": row["max_amount"],
        }


# querying the database for risk KPIs
def get_risk_kpis() -> Dict[str, Any]:
    """Aggregate risk profile, alert counts, and open case numbers."""

    with get_db_connection() as conn:
        # Total Alerts
        alert_count = conn.execute("SELECT COUNT(*) FROM Alert").fetchone()[0]

        # Open / In Progress Cases
        open_cases = conn.execute(
            "SELECT COUNT(*) FROM Cases WHERE Status IN ('OPEN', 'IN_PROGRESS')"
        ).fetchone()[0]

        # estimation of risk categories from high-risk scenarios and sampled recent activity
        # High value (>=50k), Structuring (9k-10k), and FATF blacklisted country transactions
        high_risk_sql = """
            SELECT COUNT(*) FROM Transactions
            WHERE Amount >= 50000 
               OR (Amount BETWEEN 9000 AND 9999)
               OR OriginCountryID IN ('IR', 'KP', 'MM', 'SY', 'RU', 'YE', 'AF', 'CU', 'SS')
               OR CurrencyID IN ('BTC', 'ETH', 'USDT', 'XMR', 'ZEC')
        """
        high_risk_count = conn.execute(high_risk_sql).fetchone()[0]
        total_txns = conn.execute("SELECT COUNT(*) FROM Transactions").fetchone()[0]

        # Approximate medium vs low based on threshold parameters
        medium_risk_sql = (
            "SELECT COUNT(*) FROM Transactions WHERE Amount BETWEEN 10000 AND 49999"
        )
        medium_risk_count = conn.execute(medium_risk_sql).fetchone()[0]
        low_risk_count = max(0, total_txns - (high_risk_count + medium_risk_count))

        return {
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "total_alerts": alert_count,
            "open_cases": open_cases,
        }


# querying the database for customer KPIs
def get_customer_kpis() -> Dict[str, Any]:
    """Retrieve total customer figures and high-risk rated customers."""

    with get_db_connection() as conn:
        total_cust = conn.execute("SELECT COUNT(*) FROM Customer").fetchone()[0]
        high_risk_cust = conn.execute(
            "SELECT COUNT(*) FROM Customer WHERE RiskRatingName = 'HIGH'"
        ).fetchone()[0]

        return {
            "total_customers": total_cust,
            "high_risk_customers": high_risk_cust,
        }


# querying the database for transaction trends
def get_transaction_trends(
    country: Optional[str] = None, limit: int = 12
) -> List[Dict[str, Any]]:
    """Aggregate volume and transaction count grouped by month."""

    query = """
        SELECT
            strftime('%Y-%m', TransactionDate) AS period,
            COUNT(*) AS transaction_count,
            SUM(Amount) AS total_volume
        FROM Transactions
        WHERE 1=1
    """
    params = []
    if country:
        query += " AND OriginCountryID = ?"
        params.append(country.upper())

    query += """
        GROUP BY period
        ORDER BY period DESC
        LIMIT ?
    """
    params.append(limit)

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        # Return in ascending chronological order for charts
        return [dict(row) for row in reversed(rows)]


# querying the database for country metrics
def get_top_countries(limit: int = 10) -> List[Dict[str, Any]]:
    """Find jurisdictions with the highest transaction concentrations."""

    query = """
        SELECT
            t.OriginCountryID AS country_id,
            COALESCE(c.DisplayName, t.OriginCountryID) AS country_name,
            COUNT(t.TransactionID) AS transaction_count,
            SUM(t.Amount) AS total_volume
        FROM Transactions t
        LEFT JOIN Countries c ON t.OriginCountryID = c.CountryID
        WHERE t.OriginCountryID IS NOT NULL
        GROUP BY t.OriginCountryID
        ORDER BY transaction_count DESC
        LIMIT ?
    """
    with get_db_connection() as conn:
        rows = conn.execute(query, (limit,)).fetchall()
        return [dict(row) for row in rows]


# retrieving a summary of all key metrics
def get_dashboard_summary(country: Optional[str] = None) -> Dict[str, Any]:
    """Compile the complete dashboard analytics payload."""

    from app.services import transaction_service

    return {
        "operational": get_operational_kpis(country=country),
        "risk": get_risk_kpis(),
        "customers": get_customer_kpis(),
        "trends": get_transaction_trends(country=country),
        "top_countries": get_top_countries(limit=10),
        "recent_high_risk": transaction_service.list_transactions(
            limit=10, risk_category="HIGH"
        ),
    }
