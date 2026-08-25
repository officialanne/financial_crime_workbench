# a module to generate customers and customer risk rating histories

from faker_setup import fake

RISK_RATINGS = [
    ("LOW", 1),
    ("LOW", 1),
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
    "Activity profile baseline confirmation",
]


def generate_customers(
    connection, customer_party_ids, employer_party_ids, starting_id=2001
):
    """Generates 10,000 customers with structured employment and salary profiles."""
    customer_records = []
    customer_profiles = []

    for index, party_id in enumerate(customer_party_ids):
        customer_id = starting_id + index
        occupation = fake.job()
        open_date = fake.date_between(start_date="-5y", end_date="-30d")
        risk_name, risk_number = fake.random_element(RISK_RATINGS)
        employer_party_id = fake.random_element(employer_party_ids)

        # Baseline monthly salary (between 1,500 and 15,000 in major currency units)
        salary = fake.random_int(min=1800, max=9500)

        customer_records.append(
            (
                customer_id,
                party_id,
                occupation,
                open_date,
                risk_name,
            )
        )

        customer_profiles.append(
            {
                "customer_id": customer_id,
                "party_id": party_id,
                "employer_party_id": employer_party_id,
                "salary": salary,
                "risk_name": risk_name,
                "risk_number": risk_number,
                "open_date": open_date,
            }
        )

    connection.executemany(
        """
        INSERT INTO Customer (CustomerID, PartyID, Occupation, OpenDate, RiskRatingName)
        VALUES (?, ?, ?, ?, ?)
        """,
        customer_records,
    )

    return customer_profiles


def generate_risk_rating_history(
    connection,
    customer_profiles,
    starting_id=3001,
):
    records = []
    current_id = starting_id

    for profile in customer_profiles:
        records.append(
            (
                current_id,
                profile["customer_id"],
                profile["risk_number"],
                profile["risk_name"],
                profile["open_date"],
                None,
                fake.random_element(RISK_REASONS),
                profile["open_date"],
            )
        )
        current_id += 1

    connection.executemany(
        """
        INSERT INTO CustomerRiskRatingHistory (
            RiskRatingID, CustomerID, RiskRatingNumber, RiskRatingName, EffectiveFrom, EffectiveTo, Reason, CreatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    return list(range(starting_id, current_id))
