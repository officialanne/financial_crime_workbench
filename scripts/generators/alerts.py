from faker_setup import fake

ALERT_TYPES = [
    "HIGH_VALUE_TRANSFER",
    "UNUSUAL_ACTIVITY",
    "SANCTIONS_PROXIMITY",
    "SANCTIONED_COUNTERPARTY",
    "UNUSUAL_CROSS_BORDER",
]

ALERT_STATUSES = [
    "OPEN",
    "OPEN",
    "REVIEW",
    "CLOSED",
]

RULES = [
    "RULE-TXN-001",
    "RULE-TXN-002",
    "RULE-SAN-001",
    "RULE-SAN-002",
    "RULE-TXN-007",
]


def generate_alerts(
    connection,
    count,
    transaction_ids,
    customer_ids,
    starting_id=4001,
):
    alert_ids = []

    for alert_id in range(
        starting_id,
        starting_id + count,
    ):
        transaction_id = fake.random_element(transaction_ids)

        customer_id = fake.random_element(customer_ids)

        alert_type = fake.random_element(ALERT_TYPES)

        rule_id = fake.random_element(RULES)

        risk_score = fake.random_int(
            min=1,
            max=100,
        )

        status = fake.random_element(ALERT_STATUSES)

        created_at = fake.date_between(
            start_date="-1y",
            end_date="today",
        )

        connection.execute(
            """
            INSERT INTO Alert
                (
                    AlertID,
                    TransactionID,
                    CustomerID,
                    AlertType,
                    RuleID,
                    RiskScore,
                    Status,
                    CreatedAt
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                transaction_id,
                customer_id,
                alert_type,
                rule_id,
                risk_score,
                status,
                created_at,
            ),
        )

        alert_ids.append(alert_id)

    return alert_ids
