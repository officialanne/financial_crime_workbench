import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import analytics_service


def test_operational_kpis():
    kpis = analytics_service.get_operational_kpis()
    assert isinstance(kpis["total_transactions"], int)
    assert kpis["total_transactions"] > 0
    assert kpis["total_volume"] > 0
    assert kpis["average_amount"] > 0


def test_risk_kpis():
    rk = analytics_service.get_risk_kpis()
    assert rk["high_risk_count"] >= 0
    assert rk["medium_risk_count"] >= 0
    assert rk["low_risk_count"] >= 0
    assert rk["total_alerts"] >= 0


def test_transaction_trends():
    trends = analytics_service.get_transaction_trends(limit=5)
    assert isinstance(trends, list)
    if trends:
        assert "period" in trends[0]
        assert "total_volume" in trends[0]


def test_top_countries():
    countries = analytics_service.get_top_countries(limit=5)
    assert isinstance(countries, list)
    assert len(countries) <= 5