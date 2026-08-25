from faker_setup import fake

TRANSACTION_TYPES = [
    "PAYMENT",
    "WIRE",
    "TRANSFER",
    "CARD",
]


def generate_transactions(
    connection,
    customer_profiles,
    party_catalog,
    sanction_party_ids,
    currency_ids,
    country_ids,
    normal_count=99500,
    suspicious_count=500,
    starting_id=9001,
):
    records = []
    suspicious_txn_ids = []
    current_id = starting_id

    customer_parties = party_catalog["customer"]
    employer_parties = party_catalog["employer"]
    merchant_parties = party_catalog["merchant"]
    crypto_parties = party_catalog["crypto"]
    bank_parties = party_catalog["bank"]
    foreign_parties = party_catalog["foreign"]

    # REALISTIC NORMAL TRANSACTIONS (99,500)
    shopping_count = 50000
    salary_count = 15000
    transfer_count = 15000
    cash_count = 10000
    intl_count = 6500
    crypto_count = normal_count - (
        shopping_count + salary_count + transfer_count + cash_count + intl_count
    )

    # Shopping / POS / E-commerce
    for _ in range(shopping_count):
        records.append(
            (
                current_id,
                fake.random_element(customer_parties),
                fake.random_element(merchant_parties),
                fake.random_element(merchant_parties),
                fake.random_int(min=5, max=450),  # Everyday retail amount
                fake.random_element(currency_ids),
                fake.date_between(start_date="-1y", end_date="today"),
                "CARD",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Salary Payments (Employer -> Customer)
    for _ in range(salary_count):
        profile = fake.random_element(customer_profiles)
        records.append(
            (
                current_id,
                profile["employer_party_id"],
                profile["party_id"],
                None,
                profile["salary"],
                "EUR" if "EUR" in currency_ids else currency_ids[0],
                fake.date_between(start_date="-1y", end_date="today"),
                "TRANSFER",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Domestic P2P Transfers (Customer -> Customer)
    for _ in range(transfer_count):
        sender = fake.random_element(customer_parties)
        receiver = fake.random_element(customer_parties)
        while receiver == sender:
            receiver = fake.random_element(customer_parties)

        records.append(
            (
                current_id,
                sender,
                receiver,
                None,
                fake.random_int(min=20, max=1200),
                fake.random_element(currency_ids),
                fake.date_between(start_date="-1y", end_date="today"),
                "PAYMENT",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Cash Deposits (Bank Cash Point -> Customer Account)
    for _ in range(cash_count):
        records.append(
            (
                current_id,
                fake.random_element(bank_parties),
                fake.random_element(customer_parties),
                None,
                fake.random_int(min=50, max=1800),
                fake.random_element(currency_ids),
                fake.date_between(start_date="-1y", end_date="today"),
                "TRANSFER",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Legitimate International Payments
    for _ in range(intl_count):
        records.append(
            (
                current_id,
                fake.random_element(customer_parties),
                fake.random_element(foreign_parties),
                None,
                fake.random_int(min=100, max=3500),
                fake.random_element(currency_ids),
                fake.date_between(start_date="-1y", end_date="today"),
                "WIRE",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Normal Crypto Purchases
    for _ in range(crypto_count):
        records.append(
            (
                current_id,
                fake.random_element(customer_parties),
                fake.random_element(crypto_parties),
                fake.random_element(crypto_parties),
                fake.random_int(min=50, max=2000),
                fake.random_element(currency_ids),
                fake.date_between(start_date="-1y", end_date="today"),
                "TRANSFER",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # SUSPICIOUS TRANSACTIONS (500)
    # Sanctions hits (125)
    valid_sanction_parties = [p for p in sanction_party_ids if p is not None]
    for _ in range(125):
        suspicious_txn_ids.append(current_id)
        target_sanction_party = (
            fake.random_element(valid_sanction_parties)
            if valid_sanction_parties
            else fake.random_element(foreign_parties)
        )
        records.append(
            (
                current_id,
                fake.random_element(customer_parties),
                target_sanction_party,
                None,
                fake.random_int(min=12000, max=250000),
                fake.random_element(currency_ids),
                fake.date_between(start_date="-6m", end_date="today"),
                "WIRE",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Structuring / Smurfing just under 10,000 reporting threshold (125)
    for _ in range(125):
        suspicious_txn_ids.append(current_id)
        structured_amount = fake.random_int(min=9100, max=9950)
        records.append(
            (
                current_id,
                fake.random_element(bank_parties),
                fake.random_element(customer_parties),
                None,
                structured_amount,
                fake.random_element(currency_ids),
                fake.date_between(start_date="-6m", end_date="today"),
                "TRANSFER",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Rapid Crypto Layering / High-volume Exits (125)
    for _ in range(125):
        suspicious_txn_ids.append(current_id)
        records.append(
            (
                current_id,
                fake.random_element(customer_parties),
                fake.random_element(crypto_parties),
                fake.random_element(crypto_parties),
                fake.random_int(min=45000, max=750000),
                fake.random_element(currency_ids),
                fake.date_between(start_date="-3m", end_date="today"),
                "WIRE",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Anomalous High-Value Offshore Flight (125)
    for _ in range(125):
        suspicious_txn_ids.append(current_id)
        records.append(
            (
                current_id,
                fake.random_element(customer_parties),
                fake.random_element(foreign_parties),
                None,
                fake.random_int(min=250000, max=3000000),
                fake.random_element(currency_ids),
                fake.date_between(start_date="-6m", end_date="today"),
                "WIRE",
                fake.random_element(country_ids),
            )
        )
        current_id += 1

    # Bulk insert all 100,000 transactions
    connection.executemany(
        """
        INSERT INTO Transactions (
            TransactionID, SenderPartyID, ReceiverPartyID, MerchantPartyID,
            Amount, CurrencyID, TransactionDate, TransactionType, OriginCountryID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    all_txn_ids = list(range(starting_id, current_id))
    return all_txn_ids, suspicious_txn_ids
