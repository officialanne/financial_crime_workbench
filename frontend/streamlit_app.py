import os
import sys
from pathlib import Path

# add project root to sys.path so the app imports work in Streamlit Cloud
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import requests
import streamlit as st
from app.services import transaction_service

# base URL for the FastAPI backend
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(
    page_title="Transaction Explorer | AML Workbench",
    layout="wide",
)

st.title("Transaction Explorer")
st.caption(
    "Investigate financial flows, suspicious amounts, and transaction counterparties."
)

# SIDEBAR: Query Filters
st.sidebar.header("Filter Transactions")

limit = st.sidebar.slider(
    "Number of records", min_value=10, max_value=1000, value=100, step=10
)

# amount and country filters
st.sidebar.subheader("Transaction Properties")
min_amount = st.sidebar.number_input("Minimum Amount", min_value=0, value=0, step=1000)
max_amount = st.sidebar.number_input("Maximum Amount", min_value=0, value=0, step=1000)
country = st.sidebar.text_input(
    "Origin Country Code (e.g., US, GB, AE)", max_chars=2
).strip()

# customer and party search
customer_id = st.sidebar.number_input("Customer ID (e.g. 2001)", min_value=0, value=0, step=1)
party_id = st.sidebar.number_input(
    "Party ID (Sender/Receiver)", min_value=0, value=0, step=1
)

# date range filter
st.sidebar.subheader("Date Range")
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
    "start_date": start_date_str,
    "end_date": end_date_str,
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
    col1, col2, col3 = st.columns(3)
    col1.metric("Transactions Displayed", len(df))
    col2.metric("Total Volume", f"{df['amount'].sum():,}")
    col3.metric("Max Amount", f"{df['amount'].max():,}")

    # Data Table
    st.subheader("Transaction Records")
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
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
    )

    # Transaction Detail Inspector
    st.divider()
    st.subheader("Inspect Single Transaction")
    selected_id = st.number_input(
        "Enter Transaction ID to Inspect",
        min_value=1,
        step=1,
        value=int(df.iloc[0]["transaction_id"]),
    )

    if st.button("Inspect Details"):
        try:
            detail_res = requests.get(
                f"{API_BASE_URL}/transactions/{selected_id}", timeout=5
            )
            if detail_res.status_code == 200:
                txn = detail_res.json()
                st.json(txn)
            else:
                st.warning(f"Transaction ID {selected_id} not found.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching transaction: {e}")

    else:
        st.info("No transactions found matching the current filters.")
