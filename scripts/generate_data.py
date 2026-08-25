# a module to populate the database

from config import (
    ACCOUNT_COUNT,
    ALERT_COUNT,
    ANALYST_COUNT,
    BANK_BRANCH_COUNT,
    CASE_ACTIVITY_COUNT,
    CASE_COUNT,
    CRYPTO_COUNT,
    CUSTOMER_COUNT,
    EMPLOYER_COUNT,
    FOREIGN_PARTY_COUNT,
    MERCHANT_COUNT,
    NORMAL_TRANSACTION_COUNT,
    SANCTION_COUNT,
    SUSPICIOUS_TRANSACTION_COUNT,
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
        print("Generating reference data (countries, currencies, analysts)...")
        country_ids = generate_countries(connection)
        currency_ids = generate_currencies(connection)
        analyst_ids = generate_analysts(connection, ANALYST_COUNT)

        print("Generating structured party cohorts...")
        party_catalog = generate_parties(
            connection,
            customer_count=CUSTOMER_COUNT,
            employer_count=EMPLOYER_COUNT,
            merchant_count=MERCHANT_COUNT,
            crypto_count=CRYPTO_COUNT,
            bank_count=BANK_BRANCH_COUNT,
            foreign_count=FOREIGN_PARTY_COUNT,
            country_ids=country_ids,
        )

        print("Generating 100 sanctioned entities...")
        sanctionable_pool = party_catalog["foreign"] + party_catalog["crypto"]
        sanction_ids = generate_sanctions(
            connection,
            count=SANCTION_COUNT,
            sanctionable_party_ids=sanctionable_pool,
            country_ids=country_ids,
        )

        print("Generating 10,000 customers & risk history...")
        customer_profiles = generate_customers(
            connection,
            customer_party_ids=party_catalog["customer"],
            employer_party_ids=party_catalog["employer"],
        )
        generate_risk_rating_history(connection, customer_profiles)

        print("Generating customer accounts...")
        generate_accounts(
            connection,
            customer_party_ids=party_catalog["customer"],
            currency_ids=currency_ids,
        )

        print("Generating 100,000 transactions (including 500 suspicious)...")
        all_txn_ids, suspicious_txn_ids = generate_transactions(
            connection,
            customer_profiles=customer_profiles,
            party_catalog=party_catalog,
            sanction_party_ids=sanctionable_pool,
            currency_ids=currency_ids,
            country_ids=country_ids,
            normal_count=NORMAL_TRANSACTION_COUNT,
            suspicious_count=SUSPICIOUS_TRANSACTION_COUNT,
        )

        print("Generating alerts, cases, and summaries...")
        alert_ids = generate_alerts(
            connection,
            count=ALERT_COUNT,
            suspicious_txn_ids=suspicious_txn_ids,
            all_txn_ids=all_txn_ids,
            customer_profiles=customer_profiles,
        )

        case_ids = generate_cases(
            connection,
            count=CASE_COUNT,
            alert_ids=alert_ids,
            analyst_ids=analyst_ids,
        )

        generate_investigation_summaries(connection, case_ids)
        generate_case_activities(
            connection,
            count=CASE_ACTIVITY_COUNT,
            case_ids=case_ids,
            analyst_ids=analyst_ids,
        )

        print("Generating case relationship mappings...")
        customer_ids = [p["customer_id"] for p in customer_profiles]
        generate_case_customers(connection, case_ids, customer_ids)
        generate_case_sanctions(connection, case_ids, sanction_ids)
        generate_case_transactions(connection, case_ids, suspicious_txn_ids)

        connection.commit()

        print("\nData generation completed successfully.")

    except Exception:
        connection.rollback()

        print("\nData generation failed. Changes were rolled back.")

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
