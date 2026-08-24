from faker_setup import fake

TRANSACTION_TYPES = [
    "PAYMENT",
    "WIRE",
    "TRANSFER",
    "CARD",
]


def generate_transactions(
    connection,
    count,
    party_ids,
    currency_ids,
    country_ids,
    starting_id=9001,
):
    transaction_ids = []

    for transaction_id in range(
        starting_id,
        starting_id + count,
    ):
        sender_party_id = fake.random_element(party_ids)

        receiver_party_id = fake.random_element(party_ids)

        # Make sure sender and receiver aren't the same.
        while receiver_party_id == sender_party_id:
            receiver_party_id = fake.random_element(party_ids)

        # Some transactions have a merchant, while others do not.
        if fake.boolean(chance_of_getting_true=70):
            merchant_party_id = fake.random_element(party_ids)
        else:
            merchant_party_id = None

        amount = fake.random_int(
            min=100,
            max=5000000,
        )

        currency_id = fake.random_element(currency_ids)

        transaction_date = fake.date_between(
            start_date="-1y",
            end_date="today",
        )

        transaction_type = fake.random_element(TRANSACTION_TYPES)

        origin_country_id = fake.random_element(country_ids)

        connection.execute(
            """
            INSERT INTO Transactions
                (
                    TransactionID,
                    SenderPartyID,
                    ReceiverPartyID,
                    MerchantPartyID,
                    Amount,
                    CurrencyID,
                    TransactionDate,
                    TransactionType,
                    OriginCountryID
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                sender_party_id,
                receiver_party_id,
                merchant_party_id,
                amount,
                currency_id,
                transaction_date,
                transaction_type,
                origin_country_id,
            ),
        )

        transaction_ids.append(transaction_id)

    return transaction_ids
