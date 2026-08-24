# module to handle many-to-man tables

from faker_setup import fake


def generate_case_customers(
    connection,
    case_ids,
    customer_ids,
):
    relationships = set()

    target_count = min(
        len(case_ids) * 2,
        500,
    )

    while len(relationships) < target_count:
        case_id = fake.random_element(case_ids)
        customer_id = fake.random_element(customer_ids)

        relationships.add((case_id, customer_id))

    for case_id, customer_id in relationships:
        connection.execute(
            """
            INSERT INTO CaseCustomer
                (CaseID, CustomerID)
            VALUES (?, ?)
            """,
            (
                case_id,
                customer_id,
            ),
        )

    return relationships


def generate_case_sanctions(
    connection,
    case_ids,
    sanction_ids,
):
    relationships = set()

    target_count = min(
        len(case_ids),
        len(sanction_ids),
        200,
    )

    while len(relationships) < target_count:
        case_id = fake.random_element(case_ids)
        sanction_id = fake.random_element(sanction_ids)

        relationships.add((case_id, sanction_id))

    for case_id, sanction_id in relationships:
        connection.execute(
            """
            INSERT INTO CaseSanction
                (CaseID, SanctionID)
            VALUES (?, ?)
            """,
            (
                case_id,
                sanction_id,
            ),
        )

    return relationships


def generate_case_transactions(
    connection,
    case_ids,
    transaction_ids,
):
    relationships = set()

    target_count = min(
        len(case_ids) * 2,
        len(transaction_ids),
        300,
    )

    while len(relationships) < target_count:
        case_id = fake.random_element(case_ids)
        transaction_id = fake.random_element(transaction_ids)

        relationships.add((case_id, transaction_id))

    for case_id, transaction_id in relationships:
        connection.execute(
            """
            INSERT INTO CaseTransaction
                (CaseID, TransactionID)
            VALUES (?, ?)
            """,
            (
                case_id,
                transaction_id,
            ),
        )

    return relationships
