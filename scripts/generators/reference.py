from faker_setup import fake

# creating a reference for countries, currencies, and teams
COUNTRIES = [
    ("NL", "NLD", 528, "Netherlands"),
    ("DE", "DEU", 276, "Germany"),
    ("GB", "GBR", 826, "United Kingdom"),
    ("US", "USA", 840, "United States"),
    ("FR", "FRA", 250, "France"),
    ("BE", "BEL", 56, "Belgium"),
    ("ES", "ESP", 724, "Spain"),
    ("IT", "ITA", 380, "Italy"),
    ("IE", "IRL", 372, "Ireland"),
    ("CH", "CHE", 756, "Switzerland"),
    ("SE", "SWE", 752, "Sweden"),
    ("NO", "NOR", 578, "Norway"),
    ("DK", "DNK", 208, "Denmark"),
    ("FI", "FIN", 246, "Finland"),
    ("CA", "CAN", 124, "Canada"),
    ("AU", "AUS", 36, "Australia"),
    ("JP", "JPN", 392, "Japan"),
    ("SG", "SGP", 702, "Singapore"),
    ("AE", "ARE", 784, "United Arab Emirates"),
    ("IN", "IND", 356, "India"),
]


CURRENCIES = [
    ("EUR", 978, "Euro", "FIAT", 2),
    ("USD", 840, "US Dollar", "FIAT", 2),
    ("GBP", 826, "Pound Sterling", "FIAT", 2),
    ("CHF", 756, "Swiss Franc", "FIAT", 2),
    ("JPY", 392, "Japanese Yen", "FIAT", 0),
    ("CAD", 124, "Canadian Dollar", "FIAT", 2),
    ("AUD", 36, "Australian Dollar", "FIAT", 2),
    ("SEK", 752, "Swedish Krona", "FIAT", 2),
    ("NOK", 578, "Norwegian Krone", "FIAT", 2),
    ("DKK", 208, "Danish Krone", "FIAT", 2),
]


TEAMS = [
    "AML",
    "Financial Crime",
    "Fraud",
    "Compliance",
]

ACTIVE = ["Y", "Y", "Y", "N"]


# generate countries
def generate_countries(connection):
    country_ids = []

    for country in COUNTRIES:
        connection.execute(
            """
            INSERT INTO Countries
                (CountryID, CodeAlphaThree, NumericCode, DisplayName)
            VALUES (?, ?, ?, ?)
            """,
            country,
        )

        country_ids.append(country[0])
    return country_ids


# generate currencies
def generate_currencies(connection):
    currency_ids = []

    for currency in CURRENCIES:
        connection.execute(
            """
            INSERT INTO Currency
                (CurrencyID, CurrencyCode, Name, CurrencyType, DecimalPlaces)
            VALUES (?, ?, ?, ?, ?)
            """,
            currency,
        )

        currency_ids.append(currency[0])

    return currency_ids


# generate analysts
def generate_analysts(connection, count):
    analyst_ids = []

    for analyst_id in range(1, count + 1):
        name = fake.name()
        email = fake.unique.email()
        team = fake.random_element(TEAMS)
        active = fake.random_element(ACTIVE)

        connection.execute(
            """
            INSERT INTO Analyst
                (AnalystID, Name, Email, Team, Active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                analyst_id,
                name,
                email,
                team,
                active,
            ),
        )

        analyst_ids.append(analyst_id)
    return analyst_ids
