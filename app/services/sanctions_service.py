# implements fuzzy and token-overlap string matching algorithms with confidence scoring,
# customer profile screening, and watchlist querying in the database
from difflib import SequenceMatcher
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional

DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "aml.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalise_text(text: str) -> str:
    """normalise text by converting to lowercase and stripping punctuation/prefixes."""
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    clean = re.sub(r"\bsanctioned\b", "", clean)
    return " ".join(clean.split())


def compute_name_similarity(query: str, target: str) -> float:
    """
    Computes hybrid similarity (exact, token-set overlap, and sequence ratio)
    between a query name and a sanctioned entity name.
    """
    q_norm = normalise_text(query)
    t_norm = normalise_text(target)

    if not q_norm or not t_norm:
        return 0.0

    # 1. Exact or Case-Insensitive Match
    if q_norm == t_norm:
        return 1.0

    # 2. Sequence Levenshtein-like Ratio
    seq_ratio = SequenceMatcher(None, q_norm, t_norm).ratio()

    # 3. Token-set Overlap (e.g., 'Ahmed Hassan' inside 'Hassan, Ahmed Trading LLC')
    q_tokens = set(q_norm.split())
    t_tokens = set(t_norm.split())

    if q_tokens and q_tokens.issubset(t_tokens):
        token_coverage = len(q_tokens) / len(t_tokens)
        token_score = 0.80 + (0.20 * token_coverage)
        return max(seq_ratio, token_score)

    return round(seq_ratio, 4)


def screen_name(
    query_name: str,
    threshold: float = 0.70,
    country_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Screens an entity/individual against the Sanctions watchlist table.
    Returns matched records sorted by confidence.
    """
    query = """
        SELECT
            SanctionID AS sanction_id,
            PartyID AS party_id,
            EntityName AS entity_name,
            CountryID AS country_id,
            Programme AS programme,
            Source AS source,
            ListedDate AS listed_date,
            DelistedDate AS delisted_date
        FROM Sanction
        WHERE 1=1
    """
    params: List[Any] = []
    if country_id:
        query += " AND CountryID = ?"
        params.append(country_id.upper())

    with get_db_connection() as conn:
        records = conn.execute(query, params).fetchall()

    matches: List[Dict[str, Any]] = []

    for row in records:
        entity_name = row["entity_name"] or ""
        score = compute_name_similarity(query_name, entity_name)

        if score >= threshold:
            confidence = int(score * 100)
            is_active = row["delisted_date"] is None

            if score >= 0.98:
                match_type = "EXACT_MATCH"
                reason = "Exact match against official watchlist identifier."
            elif score >= 0.85:
                match_type = "STRONG_MATCH"
                reason = f"High lexical similarity ({confidence}%) with minor spelling/token variations."
            else:
                match_type = "POSSIBLE_MATCH"
                reason = f"Partial name resemblance ({confidence}%). Review required to rule out false positive."

            matches.append(
                {
                    "sanction_id": row["sanction_id"],
                    "entity_name": entity_name,
                    "query_name": query_name,
                    "similarity_score": score,
                    "confidence_percentage": confidence,
                    "match_type": match_type,
                    "country_id": row["country_id"],
                    "programme": row["programme"],
                    "source": row["source"],
                    "listed_date": row["listed_date"],
                    "is_active": is_active,
                    "reason": reason,
                }
            )

    # Sort matches by highest confidence score
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "query_name": query_name,
        "total_matches": len(matches),
        "matches": matches,
    }


def screen_customer_by_id(customer_id: int, threshold: float = 0.70) -> Dict[str, Any]:
    """Retrieves customer name from database and screens against sanctions."""
    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT p.Name, p.CountryID
            FROM Customer c
            JOIN Party p ON c.PartyID = p.PartyID
            WHERE c.CustomerID = ?
            """,
            (customer_id,),
        ).fetchone()

        if not row:
            return {
                "query_name": f"Customer #{customer_id}",
                "total_matches": 0,
                "matches": [],
            }

        return screen_name(
            row["Name"], threshold=threshold, country_id=row["CountryID"]
        )


def list_sanctions(
    programme: Optional[str] = None,
    source: Optional[str] = None,
    country_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List and filter watchlist records."""
    query = """
        SELECT
            SanctionID AS sanction_id,
            PartyID AS party_id,
            EntityName AS entity_name,
            CountryID AS country_id,
            Programme AS programme,
            Source AS source,
            ListedDate AS listed_date,
            DelistedDate AS delisted_date
        FROM Sanction
        WHERE 1=1
    """
    params: List[Any] = []
    if programme:
        query += " AND Programme = ?"
        params.append(programme)
    if source:
        query += " AND Source = ?"
        params.append(source)
    if country_id:
        query += " AND CountryID = ?"
        params.append(country_id.upper())

    query += " ORDER BY SanctionID ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def link_sanction_to_case(case_id: int, sanction_id: int) -> bool:
    """Attaches a confirmed sanction match to an ongoing case."""
    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO CaseSanction (CaseID, SanctionID) VALUES (?, ?)",
            (case_id, sanction_id),
        )
        conn.commit()
    return True
