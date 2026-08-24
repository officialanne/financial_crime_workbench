# a module to populate the database

from config import (
    ANALYST_COUNT,
    ALERT_COUNT,
    ACCOUNT_COUNT,
    CASE_COUNT,
    CUSTOMER_COUNT,
    PARTY_COUNT,
    SANCTION_COUNT,
    TRANSACTION_COUNT,
)

from database import get_connection

from generators.reference import (
    generate_countries,
    generate_currencies,
    generate_analysts,
)

from generators.parties import (
    generate_parties,
)

from generators.customers import (
    generate_customers,
    generate_risk_rating_history,
)

from generators.accounts import (
    generate_accounts,
)

from generators.transactions import (
    generate_transactions,
)

from generators.sanctions import (
    generate_sanctions,
)

from generators.alerts import (
    generate_alerts,
)

from generators.cases import (
    generate_cases,
    generate_investigation_summaries,
    generate_case_activities,
)

from generators.relationships import (
    generate_case_customers,
    generate_case_sanctions,
    generate_case_transactions,
)


def main():
    connection = get_connection()

    try:
        print("Generating countries...")
        country_ids = generate_countries(connection)

        print("Generating currencies...")
        currency_ids = generate_currencies(connection)

        print("Generating analysts...")
        analyst_ids = generate_analysts(
            connection,
            ANALYST_COUNT,
        )

        print("Generating parties...")
        party_ids = generate_parties(
            connection,
            PARTY_COUNT,
            country_ids,
        )

        print("Generating sanctions...")
        sanction_ids = generate_sanctions(
            connection,
            SANCTION_COUNT,
            party_ids,
            country_ids,
        )

        print("Generating customers...")
        customer_ids = generate_customers(
            connection,
            CUSTOMER_COUNT,
            party_ids,
        )

        print("Generating risk-rating history...")
        generate_risk_rating_history(
            connection,
            customer_ids,
        )

        print("Generating accounts...")
        generate_accounts(
            connection,
            ACCOUNT_COUNT,
            party_ids,
            currency_ids,
        )

        print("Generating transactions...")
        transaction_ids = generate_transactions(
            connection,
            TRANSACTION_COUNT,
            party_ids,
            currency_ids,
            country_ids,
        )

        print("Generating alerts...")
        alert_ids = generate_alerts(
            connection,
            ALERT_COUNT,
            transaction_ids,
            customer_ids,
        )

        print("Generating cases...")
        case_ids = generate_cases(
            connection,
            CASE_COUNT,
            alert_ids,
            analyst_ids,
        )

        print("Generating investigation summaries...")
        generate_investigation_summaries(
            connection,
            case_ids,
        )

        print("Generating case activities...")
        generate_case_activities(
            connection,
            500,
            case_ids,
            analyst_ids,
        )

        print("Generating case/customer relationships...")
        generate_case_customers(
            connection,
            case_ids,
            customer_ids,
        )

        print("Generating case/sanction relationships...")
        generate_case_sanctions(
            connection,
            case_ids,
            sanction_ids,
        )

        print("Generating case/transaction relationships...")
        generate_case_transactions(
            connection,
            case_ids,
            transaction_ids,
        )

        connection.commit()

        print()
        print("Data generation completed successfully.")

    except Exception:
        connection.rollback()

        print()
        print("Data generation failed. Changes were rolled back.")

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
