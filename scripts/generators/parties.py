from faker_setup import fake

PARTY_TYPES = [
    "INDIVIDUAL",
    "BUSINESS",
    "MERCHANT",
    "BANK",
    "CUSTOMER",
]


# a function to generate participants in a transaction
def generate_parties(
    connection,
    customer_count,
    employer_count,
    merchant_count,
    crypto_count,
    bank_count,
    foreign_count,
    country_ids,
    starting_id=1001,
):
    """Generates structured party pools by role and bulk inserts them."""

    party_records = []
    party_catalog = {
        "customer": [],
        "employer": [],
        "merchant": [],
        "crypto": [],
        "bank": [],
        "foreign": [],
    }

    current_id = starting_id

    # 1. Customer Individual Parties
    for _ in range(customer_count):
        party_catalog["customer"].append(current_id)
        party_records.append(
            (
                current_id,
                "INDIVIDUAL",
                fake.name(),
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # 2. Employer / Corporate Parties
    for _ in range(employer_count):
        party_catalog["employer"].append(current_id)
        party_records.append(
            (
                current_id,
                "BUSINESS",
                f"{fake.company()} {fake.company_suffix()}",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # 3. Retail & Online Merchants
    for _ in range(merchant_count):
        party_catalog["merchant"].append(current_id)
        party_records.append(
            (
                current_id,
                "MERCHANT",
                f"{fake.company()} Retail",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # 4. Crypto Exchanges / VASPs
    crypto_suffixes = [
        "Exchange",
        "Crypto",
        "Digital Assets",
        "PayVASP",
        "Token Gateway",
    ]
    for _ in range(crypto_count):
        party_catalog["crypto"].append(current_id)
        party_records.append(
            (
                current_id,
                "BUSINESS",
                f"{fake.last_name()} {fake.random_element(crypto_suffixes)}",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # 5. Bank Cash Terminals / Branches
    for _ in range(bank_count):
        party_catalog["bank"].append(current_id)
        party_records.append(
            (
                current_id,
                "BANK",
                f"{fake.bank()} Branch #{fake.random_int(100, 999)}",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # 6. Foreign / Offshore Counterparties
    for _ in range(foreign_count):
        party_catalog["foreign"].append(current_id)
        party_records.append(
            (
                current_id,
                "BUSINESS",
                f"{fake.company()} International",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    connection.executemany(
        """
        INSERT INTO Party (PartyID, PartyType, Name, CountryID)
        VALUES (?, ?, ?, ?)
        """,
        party_records,
    )

    return party_catalog
