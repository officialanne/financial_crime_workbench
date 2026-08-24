# a module to generate customers and customer risk rating histories

from datetime import date, timedelta

from faker_setup import fake

RISK_RATINGS = [
    ("LOW", 1),
    ("MEDIUM", 2),
    ("HIGH", 3),
]

RISK_REASONS = [
    "Initial customer assessment",
    "Increased transaction activity",
    "Change in customer profile",
    "Increased international exposure",
    "Periodic risk review",
]


def generate_customers(connection, count, party_ids, starting_id=2001):
    if count > len(party_ids):
        raise ValueError("Cannot create more customers than available parties.")

    selected_party_ids = fake.random_elements(
        elements=party_ids,
        length=count,
        unique=True,
    )

    customer_ids = []

    for customer_id, party_id in zip(
        range(starting_id, starting_id + count),
        selected_party_ids,
    ):
        occupation = fake.job()
        open_date = fake.date_between(
            start_date="-5y",
            end_date="-30d",
        )

        risk_name, _ = fake.random_element(RISK_RATINGS)

        connection.execute(
            """
            INSERT INTO Customer
                (CustomerID, PartyID, Occupation, OpenDate, RiskRatingName)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                party_id,
                occupation,
                open_date,
                risk_name,
            ),
        )

        customer_ids.append(customer_id)

    return customer_ids


def generate_risk_rating_history(
    connection,
    customer_ids,
    starting_id=3001,
):
    risk_rating_ids = []
    risk_rating_id = starting_id

    for customer_id in customer_ids:
        rating_name, rating_number = fake.random_element(RISK_RATINGS)

        effective_from = fake.date_between(
            start_date="-5y",
            end_date="-30d",
        )

        risk_reason = fake.random_element(RISK_REASONS)

        connection.execute(
            """
            INSERT INTO CustomerRiskRatingHistory
                (
                    RiskRatingID,
                    CustomerID,
                    RiskRatingNumber,
                    RiskRatingName,
                    EffectiveFrom,
                    EffectiveTo,
                    Reason,
                    CreatedAt
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                risk_rating_id,
                customer_id,
                rating_number,
                rating_name,
                effective_from,
                None,
                risk_reason,
                effective_from,
            ),
        )

        risk_rating_ids.append(risk_rating_id)
        risk_rating_id += 1

    return risk_rating_ids
