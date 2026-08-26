# tests/test_risk_engine.py
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.risk_engine import evaluate_transaction_risk


def test_normal_low_value_transaction():
    txn = {
        "amount": 250,
        "origin_country_id": "GB",
        "currency_id": "GBP",
    }
    result = evaluate_transaction_risk(txn)
    assert result.score == 0
    assert result.category == "LOW"
    assert len(result.triggered_rules) == 0


def test_structuring_transaction():
    txn = {
        "amount": 9500,
        "origin_country_id": "US",
        "currency_id": "USD",
    }
    result = evaluate_transaction_risk(txn)
    assert result.score == 30
    assert result.category == "MEDIUM"
    assert any(r["rule_id"] == "RULE_STRUCTURING" for r in result.triggered_rules)


def test_high_risk_country_and_crypto():
    txn = {
        "amount": 20000,
        "origin_country_id": "RU",
        "currency_id": "XMR",
    }
    result = evaluate_transaction_risk(txn)
    assert result.score == 95
    assert result.category == "HIGH"
    assert len(result.reasons) == 4


def test_score_caps_at_100():
    txn = {
        "amount": 250000,  # +45
        "origin_country_id": "IR",  # +35
        "currency_id": "BTC",  # +25
    }
    result = evaluate_transaction_risk(txn)
    assert result.score == 100
    assert result.category == "HIGH"
