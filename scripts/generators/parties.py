from faker_setup import fake

PARTY_TYPES = [
    "INDIVIDUAL",
    "BUSINESS",
    "MERCHANT",
    "BANK",
    "CUSTOMER",
]

# a function to generate participants in a transaction
def generate_parties(connection, count, country_ids, starting_id=1001):
    party_ids = []

    for party_id in range(starting_id, starting_id + count):
        party_type = fake.random_element(PARTY_TYPES)

        match party_type:
            case "INDIVIDUAL":
                name = fake.name()
            case "CUSTOMER":
                name = fake.name()
            case "BANK":
                name = fake.bank()
            case "BUSINESS":
                name = fake.company()
            case "CUSTOMER":
                name = fake.name()

        country_id = fake.random_element(country_ids)

        connection.execute(
            """
            INSERT INTO Party
                (PartyID, PartyType, Name, CountryID)
            VALUES (?, ?, ?, ?)
            """,
            (
                party_id,
                party_type,
                name,
                country_id,
            ),
        )

        party_ids.append(party_id)

    return party_ids