from faker_setup import fake

ACCOUNT_TYPES = [
    "CURRENT",
    "SAVINGS",
    "BUSINESS",
]

ACCOUNT_STATUSES = [
    "OPEN",
    "OPEN",
    "OPEN",
    "CLOSED",
]


def generate_accounts(
    connection,
    count,
    party_ids,
    currency_ids,
    starting_id=1,
):
    account_ids = []
    used_account_numbers = set()

    for number in range(count):
        account_id = f"ACC-{starting_id + number:05d}"

        party_id = fake.random_element(party_ids)
        currency_id = fake.random_element(currency_ids)

        account_no = fake.random_int(
            min=10000000,
            max=99999999,
        )

        while account_no in used_account_numbers:
            account_no = fake.random_int(
                min=10000000,
                max=99999999,
            )

        used_account_numbers.add(account_no)

        account_type = fake.random_element(ACCOUNT_TYPES)
        status = fake.random_element(ACCOUNT_STATUSES)

        open_date = fake.date_between(
            start_date="-5y",
            end_date="-30d",
        )

        if status == "CLOSED":
            close_date = fake.date_between(
                start_date=open_date,
                end_date="today",
            )
        else:
            close_date = None

        connection.execute(
            """
            INSERT INTO Account
                (
                    AccountID,
                    PartyID,
                    AccountNo,
                    AccountType,
                    CurrencyID,
                    OpenDate,
                    CloseDate,
                    Status
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                party_id,
                account_no,
                account_type,
                currency_id,
                open_date,
                close_date,
                status,
            ),
        )

        account_ids.append(account_id)

    return account_ids
