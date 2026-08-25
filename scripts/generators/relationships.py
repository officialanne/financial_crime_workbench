# module to handle many-to-man tables

from faker_setup import fake


def generate_case_customers(
    connection,
    case_ids,
    customer_ids,
):
    relationships = set()

    target_count = min(len(case_ids) * 2, len(customer_ids), 800)

    while len(relationships) < target_count:
        relationships.add(
            (fake.random_element(case_ids), fake.random_element(customer_ids))
        )

    connection.executemany(
        "INSERT INTO CaseCustomer (CaseID, CustomerID) VALUES (?, ?)",
        list(relationships),
    )
    return relationships


def generate_case_sanctions(connection, case_ids, sanction_ids):
    relationships = set()
    target_count = min(len(case_ids), len(sanction_ids), 200)

    while len(relationships) < target_count:
        relationships.add(
            (fake.random_element(case_ids), fake.random_element(sanction_ids))
        )

    connection.executemany(
        "INSERT INTO CaseSanction (CaseID, SanctionID) VALUES (?, ?)",
        list(relationships),
    )
    return relationships


def generate_case_transactions(connection, case_ids, transaction_ids):
    relationships = set()
    target_count = min(len(case_ids) * 2, len(transaction_ids), 800)

    while len(relationships) < target_count:
        relationships.add(
            (fake.random_element(case_ids), fake.random_element(transaction_ids))
        )

    connection.executemany(
        "INSERT INTO CaseTransaction (CaseID, TransactionID) VALUES (?, ?)",
        list(relationships),
    )
    return relationships
