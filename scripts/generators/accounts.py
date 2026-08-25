from faker_setup import fake

ACCOUNT_TYPES = [
    "CURRENT",
    "SAVINGS",
    "BUSINESS",
]


def generate_accounts(
    connection,
    customer_party_ids,
    currency_ids,
    starting_id=1,
):
    account_records = []
    account_ids = []
    account_no_counter = 10000000

    for index, party_id in enumerate(customer_party_ids):
        account_id = f"ACC-{starting_id + index:06d}"
        account_ids.append(account_id)

        account_no = account_no_counter + index
        account_type = fake.random_element(ACCOUNT_TYPES)
        currency_id = fake.random_element(currency_ids)
        status = "OPEN" if fake.boolean(chance_of_getting_true=90) else "CLOSED"
        open_date = fake.date_between(start_date="-5y", end_date="-30d")
        close_date = (
            fake.date_between(start_date=open_date, end_date="today")
            if status == "CLOSED"
            else None
        )

        account_records.append(
            (
                account_id,
                party_id,
                account_no,
                account_type,
                currency_id,
                open_date,
                close_date,
                status,
            )
        )

    connection.executemany(
        """
        INSERT INTO Account (
            AccountID, PartyID, AccountNo, AccountType, CurrencyID, OpenDate, CloseDate, Status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        account_records,
    )

    return account_ids
