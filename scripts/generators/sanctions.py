from faker_setup import fake

PROGRAMMES = [
    "Financial Restrictions",
    "Trade Restrictions",
    "Export Restrictions",
    "Anti-Money Laundering",
]

SOURCES = [
    "TEST-LIST-A",
    "TEST-LIST-B",
    "INTERNAL-SANCTIONS-DATA",
    "FICTIONAL-REGULATOR",
]


def generate_sanctions(
    connection,
    count,
    party_ids,
    country_ids,
    starting_id=5001,
):
    sanction_ids = []

    for sanction_id in range(
        starting_id,
        starting_id + count,
    ):
        # Around 70% of sanctions are linked to a Party.
        if fake.boolean(chance_of_getting_true=70):
            party_id = fake.random_element(party_ids)
        else:
            party_id = None

        country_id = fake.random_element(country_ids)

        entity_name = fake.company()

        programme = fake.random_element(PROGRAMMES)
        source = fake.random_element(SOURCES)

        listed_date = fake.date_between(
            start_date="-5y",
            end_date="-30d",
        )

        # Some sanctions are still active.
        if fake.boolean(chance_of_getting_true=80):
            delisted_date = None
        else:
            delisted_date = fake.date_between(
                start_date=listed_date,
                end_date="today",
            )

        connection.execute(
            """
            INSERT INTO Sanction
                (
                    SanctionID,
                    PartyID,
                    EntityName,
                    CountryID,
                    Programme,
                    Source,
                    ListedDate,
                    DelistedDate
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sanction_id,
                party_id,
                entity_name,
                country_id,
                programme,
                source,
                listed_date,
                delisted_date,
            ),
        )

        sanction_ids.append(sanction_id)

    return sanction_ids
