from faker_setup import fake

RULES_BY_TYPE = {
    "SANCTIONED_COUNTERPARTY": "RULE-SAN-001",
    "UNUSUAL_ACTIVITY": "RULE-TXN-001",
    "HIGH_VALUE_TRANSFER": "RULE-TXN-002",
    "UNUSUAL_CROSS_BORDER": "RULE-TXN-007",
}

STATUSES = ["OPEN", "OPEN", "REVIEW", "CLOSED"]


def generate_alerts(
    connection,
    count,
    suspicious_txn_ids,
    all_txn_ids,
    customer_profiles,
    starting_id=4001,
):
    """Prioritizes alerting on the 500 suspicious transactions, plus selected regular ones."""
    records = []
    alert_ids = []
    current_id = starting_id

    customer_id_list = [p["customer_id"] for p in customer_profiles]

    # Flag suspicious transactions directly
    for txn_id in suspicious_txn_ids:
        alert_type = fake.random_element(list(RULES_BY_TYPE.keys()))
        records.append(
            (
                current_id,
                txn_id,
                fake.random_element(customer_id_list),
                alert_type,
                RULES_BY_TYPE[alert_type],
                fake.random_int(min=75, max=99),  # Elevated risk score
                fake.random_element(STATUSES),
                fake.date_between(start_date="-6m", end_date="today"),
            )
        )
        alert_ids.append(current_id)
        current_id += 1

    # Fill remaining alert volume with minor rule hits on general transactions
    remaining_alerts = max(0, count - len(suspicious_txn_ids))
    for _ in range(remaining_alerts):
        alert_type = fake.random_element(list(RULES_BY_TYPE.keys()))
        records.append(
            (
                current_id,
                fake.random_element(all_txn_ids),
                fake.random_element(customer_id_list),
                alert_type,
                RULES_BY_TYPE[alert_type],
                fake.random_int(min=20, max=65),
                fake.random_element(STATUSES),
                fake.date_between(start_date="-1y", end_date="today"),
            )
        )
        alert_ids.append(current_id)
        current_id += 1

    connection.executemany(
        """
        INSERT INTO Alert (
            AlertID, TransactionID, CustomerID, AlertType, RuleID, RiskScore, Status, CreatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    return alert_ids