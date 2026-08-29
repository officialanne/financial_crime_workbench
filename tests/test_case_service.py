import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import case_service


def test_list_cases():
    cases = case_service.list_cases(limit=10)
    assert isinstance(cases, list)
    if cases:
        assert "case_id" in cases[0]
        assert "status" in cases[0]
        assert "priority" in cases[0]


def test_create_and_update_case_lifecycle():
    # 1. Create a case
    new_case_payload = {
        "priority": "CRITICAL",
        "status": "OPEN",
        "assigned_analyst_id": 1,
        "notes": "Test case for smurfing and money laundering.",
        "initial_transaction_ids": [9001],
        "initial_customer_ids": [2001],
    }
    case = case_service.create_case(new_case_payload)
    case_id = case["case_id"]

    assert case_id is not None
    assert case["priority"] == "CRITICAL"
    assert case["status"] == "OPEN"
    assert len(case["linked_transactions"]) >= 1
    assert len(case["linked_customers"]) >= 1

    # 2. Add an investigation note
    activity = case_service.add_case_activity(
        case_id,
        {
            "analyst_id": 1,
            "activity_type": "NOTE_ADDED",
            "description": "Destination account verified as high-risk entity.",
        },
    )
    assert activity["activity_id"] is not None

    # 3. Update status to CLOSED
    updated = case_service.update_case(case_id, {"status": "CLOSED"})
    assert updated["status"] == "CLOSED"
    assert updated["closed_at"] is not None
