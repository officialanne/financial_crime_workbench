# the service queries the database and applies filters

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

# Locate database/aml.db relative to this file
DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "aml.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)

    # returns rows as dictionary-like objects
    conn.row_factory = sqlite3.Row

    return conn


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

        return dict(row) if row else None


def list_transactions(
    limit: int = 100,
    offset: int = 0,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    country: Optional[str] = None,
    party_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Filter and list transactions with pagination."""

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

    if min_amount is not None:
        query += " AND Amount >= ?"
        params.append(min_amount)

    if max_amount is not None:
        query += " AND Amount <= ?"
        params.append(max_amount)

    if country is not None:
        query += " AND OriginCountryID = ?"
        params.append(country.upper())

    if party_id is not None:
        query += " AND (SenderPartyID = ? OR ReceiverPartyID = ?)"
        params.extend([party_id, party_id])

    query += " ORDER BY TransactionDate DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


# TODO:
# services and then router
# add customerID to above (through party id) as a separate one (just like by transaction ID)
# add transaction date to above
