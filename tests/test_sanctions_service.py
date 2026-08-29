import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import sanctions_service


def test_exact_name_matching():
    result = sanctions_service.screen_name("Blackstone Trading Ltd", threshold=0.80)
    assert isinstance(result["matches"], list)


def test_case_insensitive_matching():
    score = sanctions_service.compute_name_similarity("john smith", "JOHN SMITH")
    assert score == 1.0


def test_fuzzy_name_matching():
    # Minor spelling variation
    score = sanctions_service.compute_name_similarity("Mohammed Ali", "Mohammad Ali")
    assert score >= 0.85


def test_unrelated_name_no_match():
    score = sanctions_service.compute_name_similarity("Alice Cooper", "Dmitri Volkov")
    assert score < 0.40


def test_customer_screening():
    res = sanctions_service.screen_customer_by_id(customer_id=2001, threshold=0.70)
    assert "query_name" in res
    assert "matches" in res