import os
import sys
from pathlib import Path

# add project root to sys.path so the app imports work in Streamlit Cloud
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import requests
import streamlit as st
from app.services import transaction_service

# base URL for the FastAPI backend
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(
    page_title="Transaction & Risk Explorer | AML Workbench",
    layout="wide",
)

st.title("Transaction & Risk Intelligence Explorer")
st.caption(
    "Investigate financial movements, filter risk queues, and inspect explainable AML indicators."
)

# SIDEBAR: Query Filters
st.sidebar.header("Filter & Search Transactions")

# limit the number of records shown
limit = st.sidebar.slider(
    "Records to Load", min_value=10, max_value=1000, value=100, step=10
)

# Risk filter
risk_filter = st.sidebar.selectbox("Risk Category", ["ALL", "HIGH", "MEDIUM", "LOW"])


# entity filters
st.sidebar.subheader("Entity & Search")
party_id = st.sidebar.number_input(
    "Party ID (Sender/Receiver)", min_value=0, value=0, step=1
)
customer_id = st.sidebar.number_input(
    "Customer ID (e.g. 2001)", min_value=0, value=0, step=1
)
merchant_id = st.sidebar.number_input("Merchant ID", min_value=0, value=0, step=1)

# transaction filters
st.sidebar.subheader("Transaction Filters")
min_amount = st.sidebar.number_input("Minimum Amount", min_value=0, value=0, step=1000)
max_amount = st.sidebar.number_input("Maximum Amount", min_value=0, value=0, step=1000)
country = st.sidebar.text_input(
    "Origin Country Code (e.g., US, GB, AE)", max_chars=2
).strip()
currency_id = st.sidebar.text_input(
    "Fiat or Crypto Currency Code (e.g., GBP, USD, BTC)", max_chars=3
).strip()
txn_type = st.sidebar.text_input("Type of Transaction (e.g., CARD, WIRE)")

# date range filter
st.sidebar.subheader("Date Filter")
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(),
    help="Select a single date, or click two dates to select a range.",
)

start_date_str = None
end_date_str = None
if isinstance(date_range, tuple) or isinstance(date_range, list):
    if len(date_range) == 1:
        start_date_str = str(date_range[0])
    elif len(date_range) == 2:
        start_date_str = str(date_range[0])
        end_date_str = str(date_range[1])

# Build Query Parameters
filter_params = {
    "limit": limit,
    "min_amount": min_amount if min_amount > 0 else None,
    "max_amount": max_amount if max_amount > 0 else None,
    "country": country.upper() if country else None,
    "party_id": party_id if party_id > 0 else None,
    "customer_id": customer_id if customer_id > 0 else None,
    "merchant_id": merchant_id if merchant_id > 0 else None,
    "currency_id": currency_id.upper() if currency_id else None,
    "txn_type": txn_type.upper() if txn_type else None,
    "start_date": start_date_str,
    "end_date": end_date_str,
    "risk_category": None if risk_filter == "ALL" else risk_filter,
}


# Unified Data Fetcher
def get_transactions_data(filters):
    # If a remote API URL is specified, query it over HTTP
    if API_BASE_URL:
        try:
            params = {k: v for k, v in filters.items() if v is not None}
            res = requests.get(
                f"{API_BASE_URL}/transactions/", params=params, timeout=5
            )
            if res.status_code == 200:
                return res.json()
            st.error(f"API Error: {res.status_code}")
            return []
        except requests.exceptions.RequestException as e:
            st.warning(
                f"Could not reach API at {API_BASE_URL}. Falling back to internal service."
            )

    # Standalone / Cloud fallback (queries SQLite via transaction_service)
    return transaction_service.list_transactions(**filters)


def get_single_transaction(txn_id: int):
    if API_BASE_URL:
        try:
            res = requests.get(f"{API_BASE_URL}/transactions/{txn_id}", timeout=5)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return transaction_service.get_transaction_by_id(txn_id)


# MAIN CONTENT: Display Transactions
transactions_data = get_transactions_data(filter_params)

if transactions_data:
    df = pd.DataFrame(transactions_data)

    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions Found", len(df))
    col2.metric("Total Volume", f"{df['amount'].sum():,}")
    high_count = (df["risk_category"] == "HIGH").sum()
    col3.metric("High Risk Items", high_count)
    col4.metric("Avg Risk Score", f"{df['risk_score'].mean():.1f}/100")

    # Data Table
    st.subheader("Transaction Ledger")
    st.dataframe(
        df,
        width="stretch",
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score", format="%d", min_value=0, max_value=100
            ),
            "risk_category": "Level",
            "transaction_id": "Txn ID",
            "sender_party_id": "Sender ID",
            "receiver_party_id": "Receiver ID",
            "merchant_party_id": "Merchant ID",
            "amount": st.column_config.NumberColumn("Amount", format="%d"),
            "currency_id": "Currency",
            "transaction_date": "Date",
            "transaction_type": "Type",
            "origin_country_id": "Country",
        },
        column_order=[
            "risk_score",
            "risk_category",
            "transaction_id",
            "amount",
            "currency_id",
            "origin_country_id",
            "sender_party_id",
            "receiver_party_id",
            "merchant_party_id",
            "transaction_date",
        ],
    )

    # Transaction Detail Inspector
    st.divider()
    st.subheader("Transaction Detail & AML Risk Inspector")
    txn_id_options = df["transaction_id"].tolist()
    selected_id = st.selectbox(
        "Select a Transaction from the ledger to inspect:", txn_id_options
    )

    if selected_id:
        detail = get_single_transaction(selected_id)
        if detail:
            cat = detail.get("risk_category", "LOW")
            score = detail.get("risk_score", 0)

            # Left column: Risk Badge & Reasons | Right column: Transaction Specs
            col_risk, col_meta = st.columns([1, 1])

            with col_risk:
                if cat == "HIGH":
                    st.error(f"### HIGH RISK (Score: {score}/100)")
                elif cat == "MEDIUM":
                    st.warning(f"### MEDIUM RISK (Score: {score}/100)")
                else:
                    st.success(f"### LOW RISK (Score: {score}/100)")

                rules = detail.get("triggered_rules", [])
                if rules:
                    st.markdown("**Triggered Risk Rules:**")
                    for r in rules:
                        st.markdown(
                            f"- **{r['rule_name']}** (`+{r['points']} pts`): {r['reason']}"
                        )
                else:
                    st.info(
                        "No suspicious rules triggered. Activity consistent with normal profile."
                    )

            with col_meta:
                st.markdown("#### Transaction Summary")
                st.write(
                    f"**Amount:** {detail.get('amount', 0):,} {detail.get('currency_id', '')}"
                )
                st.write(f"**Type:** {detail.get('transaction_type', 'N/A')}")
                st.write(f"**Date:** {detail.get('transaction_date', 'N/A')}")
                st.write(
                    f"**Origin Country:** {detail.get('origin_country_id', 'N/A')}"
                )
                st.write(f"**Sender Party ID:** {detail.get('sender_party_id')}")
                st.write(f"**Receiver Party ID:** {detail.get('receiver_party_id')}")

            with st.expander("View Raw JSON Schema Data"):
                st.json(detail)
else:
    st.info("No transactions found matching the current filters.")
