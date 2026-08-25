from faker_setup import fake

PROGRAMMES = [
    "Financial Restrictions",
    "Trade Restrictions",
    "Export Restrictions",
    "Anti-Money Laundering",
    "Anti-Terrorism Financing",
    "High-Risk Proliferation Sanctions",
]

SOURCES = [
    "OFSI-CONSOLIDATED",
    "EU-FINANCIAL-SANCTIONS",
    "UN-SECURITY-COUNCIL",
    "FATF-HIGH-RISK-MONITORING",
]


def generate_sanctions(
    connection,
    count,
    sanctionable_party_ids,
    country_ids,
    starting_id=5001,
):
    """Generates sanctioned entities, linking a subset directly to generated parties."""
    records = []
    sanction_ids = []

    # Link 40% of sanctions to parties in the database
    linked_count = min(int(count * 0.4), len(sanctionable_party_ids))
    linked_parties = fake.random_elements(
        elements=sanctionable_party_ids, length=linked_count, unique=True
    )
    unlinked_count = count - linked_count

    party_assignments = list(linked_parties) + [None] * unlinked_count
    fake.random.shuffle(party_assignments)

    for offset, party_id in enumerate(party_assignments):
        sanction_id = starting_id + offset
        sanction_ids.append(sanction_id)

        entity_name = (
            fake.company() if party_id is None else f"SANCTIONED-{fake.company()}"
        )
        country_id = fake.random_element(country_ids)
        programme = fake.random_element(PROGRAMMES)
        source = fake.random_element(SOURCES)

        listed_date = fake.date_between(start_date="-4y", end_date="-60d")
        delisted_date = (
            None
            if fake.boolean(chance_of_getting_true=85)
            else fake.date_between(start_date=listed_date, end_date="today")
        )

        records.append(
            (
                sanction_id,
                party_id,
                entity_name,
                country_id,
                programme,
                source,
                listed_date,
                delisted_date,
            )
        )

    connection.executemany(
        """
        INSERT INTO Sanction (
            SanctionID, PartyID, EntityName, CountryID, Programme, Source, ListedDate, DelistedDate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    return sanction_ids
