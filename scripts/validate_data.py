from database import get_connection

TABLES = [
    "Analyst",
    "Countries",
    "Currency",
    "Party",
    "Sanction",
    "Transactions",
    "Account",
    "Customer",
    "CustomerRiskRatingHistory",
    "Alert",
    "Cases",
    "InvestigationSummary",
    "CaseActivity",
    "CaseCustomer",
    "CaseSanction",
    "CaseTransaction",
]


def print_row_counts(connection):
    print("ROW COUNTS")
    print("-" * 40)

    for table in TABLES:
        result = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()

        count = result[0]

        print(f"{table:35} {count}")


def check_foreign_keys(connection):
    print()
    print("FOREIGN KEY CHECK")
    print("-" * 40)

    results = connection.execute("PRAGMA foreign_key_check").fetchall()

    if not results:
        print("No foreign-key violations found.")
    else:
        print("Foreign-key violations found:")

        for result in results:
            print(result)


def check_duplicate_emails(connection):
    print()
    print("DUPLICATE EMAIL CHECK")
    print("-" * 40)

    duplicates = connection.execute("""
        SELECT Email, COUNT(*)
        FROM Analyst
        GROUP BY Email
        HAVING COUNT(*) > 1
        """).fetchall()

    if not duplicates:
        print("No duplicate analyst emails.")
    else:
        for email, count in duplicates:
            print(email, count)


def check_duplicate_account_numbers(connection):
    print()
    print("DUPLICATE ACCOUNT NUMBER CHECK")
    print("-" * 40)

    duplicates = connection.execute("""
        SELECT AccountNo, COUNT(*)
        FROM Account
        GROUP BY AccountNo
        HAVING COUNT(*) > 1
        """).fetchall()

    if not duplicates:
        print("No duplicate account numbers.")
    else:
        for account_no, count in duplicates:
            print(account_no, count)


def check_transaction_parties(connection):
    print()
    print("TRANSACTION PARTY CHECK")
    print("-" * 40)

    invalid = connection.execute("""
        SELECT TransactionID
        FROM Transactions
        WHERE SenderPartyID = ReceiverPartyID
        """).fetchall()

    if not invalid:
        print("All transactions have different senders and receivers.")
    else:
        print("Transactions with identical sender/receiver:")

        for transaction in invalid:
            print(transaction[0])


def check_case_dates(connection):
    print()
    print("CASE DATE CHECK")
    print("-" * 40)

    invalid = connection.execute("""
        SELECT CaseID
        FROM Cases
        WHERE ClosedAt IS NOT NULL
          AND ClosedAt < CreatedAt
        """).fetchall()

    if not invalid:
        print("All case dates are valid.")
    else:
        print("Invalid case dates:")

        for case in invalid:
            print(case[0])


def main():
    connection = get_connection()

    try:
        print_row_counts(connection)
        check_foreign_keys(connection)
        check_duplicate_emails(connection)
        check_duplicate_account_numbers(connection)
        check_transaction_parties(connection)
        check_case_dates(connection)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
