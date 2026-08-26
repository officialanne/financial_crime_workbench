# the service queries the database and applies filters

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Union
from datetime import date

from app.services.risk_engine import evaluate_transaction_risk

# Locate database/aml.db relative to this file
DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "aml.db"


# get the database connection
def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)

    # returns rows as dictionary-like objects
    conn.row_factory = sqlite3.Row

    return conn


# get a transaction by id
def get_transaction_by_id(transaction_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single transaction by ID."""

    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT
                TransactionID AS transaction_id,
                SenderPartyID AS sender_party_id,
                ReceiverPartyID AS receiver_party_id,
                MerchantPartyID AS merchant_party_id,
                Amount AS amount,
                CurrencyID AS currency_id,
                TransactionDate AS transaction_date,
                TransactionType AS transaction_type,
                OriginCountryID AS origin_country_id
            FROM Transactions
            WHERE TransactionID = ?
            """,
            (transaction_id,),
        ).fetchone()

        if not row:
            return None

        # evalutate and store the risk scores for each transaction
        data = dict(row)
        risk = evaluate_transaction_risk(data)
        data["risk_score"] = risk.score
        data["risk_category"] = risk.category
        data["reasons"] = risk.reasons
        data["triggered_rules"] = risk.triggered_rules
        return data


# list all transactions including filters
def list_transactions(
    limit: int = 100,
    offset: int = 0,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    country: Optional[str] = None,
    party_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    currency_id: Optional[str] = None,
    txn_type: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    risk_category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter and list transactions with pagination and risk assessment."""

    query = """
        SELECT
            TransactionID AS transaction_id,
            SenderPartyID AS sender_party_id,
            ReceiverPartyID AS receiver_party_id,
            MerchantPartyID AS merchant_party_id,
            Amount AS amount,
            CurrencyID AS currency_id,
            TransactionDate AS transaction_date,
            TransactionType AS transaction_type,
            OriginCountryID AS origin_country_id
        FROM Transactions
        WHERE 1=1
    """
    params: List[Any] = []

    # amount filters
    if min_amount is not None:
        query += " AND Amount >= ?"
        params.append(min_amount)

    if max_amount is not None:
        query += " AND Amount <= ?"
        params.append(max_amount)

    # country filter
    if country is not None:
        query += " AND OriginCountryID = ?"
        params.append(country.upper())

    # party ID filter
    if party_id is not None:
        query += " AND (SenderPartyID = ? OR ReceiverPartyID = ?)"
        params.extend([party_id, party_id])

    # Customer ID filter (finds the party associated with this customer)
    if customer_id is not None:
        query += """
            AND (
                SenderPartyID IN (SELECT PartyID FROM Customer WHERE CustomerID = ?)
                OR ReceiverPartyID IN (SELECT PartyID FROM Customer WHERE CustomerID = ?)
            )
        """
        params.extend([customer_id, customer_id])

    # merchant id filter
    if merchant_id is not None:
        query += " AND MerchantPartyID = ?"
        params.append(merchant_id)

    # currency filter
    if currency_id is not None:
        query += " AND CurrencyID = ?"
        params.append(currency_id.upper())

    # transaction type filter
    if txn_type is not None:
        query += "AND TransactionType = ?"
        params.append(txn_type.upper())

    # Date range filters (supports min date, max date, or in-between)
    if start_date is not None:
        query += " AND TransactionDate >= ?"
        params.append(str(start_date))

    if end_date is not None:
        query += " AND TransactionDate <= ?"
        params.append(str(end_date))

    query += " ORDER BY TransactionDate DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        risk_eval = []
        for row in rows:
            # evaluate the risk for each row
            txn = dict(row)
            risk = evaluate_transaction_risk(txn)
            txn["risk_score"] = risk.score
            txn["risk_category"] = risk.category
            txn["reasons"] = risk.reasons

            if risk_category and (txn["risk_category"] != risk_category.upper()):
                continue

            risk_eval.append(txn)

        return [dict(row) for row in rows]
