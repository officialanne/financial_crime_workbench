# frontend/streamlit_app.py
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import requests
import streamlit as st
from app.services import transaction_service

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(
    page_title="Risk & Transaction Explorer | AML Workbench",
    layout="wide",
)

st.title("Transaction Risk Explorer")
st.caption(
    "Prioritize AML investigations using explainable, rule-based risk intelligence."
)

# -------------------------------------------------------------------
# Sidebar: Query Filters
# -------------------------------------------------------------------
st.sidebar.header("Filters & Search")

# Risk filter
risk_filter = st.sidebar.selectbox("Risk Category", ["ALL", "HIGH", "MEDIUM", "LOW"])

# Customer & Party search
customer_id = st.sidebar.number_input(
    "Customer ID (e.g. 2001)", min_value=0, value=0, step=1
)
party_id = st.sidebar.number_input("Party ID", min_value=0, value=0, step=1)
merchant_id = st.sidebar.number_input("Merchant ID", min_value=0, value=0, step=1)

# Property filters
st.sidebar.subheader("Transaction Properties")
min_amount = st.sidebar.number_input("Minimum Amount", min_value=0, value=0, step=1000)
max_amount = st.sidebar.number_input("Maximum Amount", min_value=0, value=0, step=1000)
country = st.sidebar.text_input(
    "Origin Country Code (e.g., US, RU, AE)", max_chars=2
).strip()
currency_id = st.sidebar.text_input(
    "Currency Code (e.g., GBP, USD, BTC, XMR)", max_chars=4
).strip()
txn_type = st.sidebar.text_input("Transaction Type (e.g., CARD, WIRE, TRANSFER)")

# Date range
st.sidebar.subheader("Date Range")
date_range = st.sidebar.date_input("Select Date Range", value=())

start_date_str = None
end_date_str = None
if isinstance(date_range, tuple) or isinstance(date_range, list):
    if len(date_range) == 1:
        start_date_str = str(date_range[0])
    elif len(date_range) == 2:
        start_date_str = str(date_range[0])
        end_date_str = str(date_range[1])

limit = st.sidebar.slider(
    "Records to Load", min_value=10, max_value=1000, value=100, step=10
)

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


def get_transactions_data(filters):
    if API_BASE_URL:
        try:
            params = {k: v for k, v in filters.items() if v is not None}
            res = requests.get(
                f"{API_BASE_URL}/transactions/", params=params, timeout=5
            )
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return transaction_service.list_transactions(**filters)


def get_transaction_risk_detail(txn_id: int):
    if API_BASE_URL:
        try:
            res = requests.get(f"{API_BASE_URL}/risk/transaction/{txn_id}", timeout=5)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return transaction_service.get_transaction_by_id(txn_id)


# Main UI
transactions_data = get_transactions_data(filter_params)

if transactions_data:
    df = pd.DataFrame(transactions_data)

    # Top KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", len(df))
    c2.metric("Total Volume", f"{df['amount'].sum():,}")
    high_count = (df["risk_category"] == "HIGH").sum()
    c3.metric("High Risk Flags", high_count)
    c4.metric("Average Risk Score", f"{df['risk_score'].mean():.1f}/100")

    # Data Table with Progress Bar for Risk Score
    st.subheader("Transaction Risk Queue")
    st.dataframe(
        df,
        width="stretch",
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score", format="%d", min_value=0, max_value=100
            ),
            "risk_category": "Risk Level",
            "transaction_id": "Txn ID",
            "sender_party_id": "Sender",
            "receiver_party_id": "Receiver",
            "amount": st.column_config.NumberColumn("Amount", format="%d"),
            "currency_id": "Currency",
            "origin_country_id": "Country",
            "transaction_date": "Date",
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
            "transaction_date",
        ],
    )

    # Explainable Risk Inspector
    st.divider()
    st.subheader("Explainable Risk Assessment Inspector")
    selected_id = st.number_input(
        "Enter Transaction ID to Inspect",
        min_value=1,
        step=1,
        value=int(df.iloc[0]["transaction_id"]),
    )

    if st.button("Analyze Risk Breakdown"):
        detail = get_transaction_risk_detail(selected_id)
        if detail:
            cat = detail.get("risk_category", "LOW")
            score = detail.get("risk_score", 0)

            # Visual badge indicator
            if cat == "HIGH":
                st.error(f"### HIGH RISK (Score: {score}/100)")
            elif cat == "MEDIUM":
                st.warning(f"### MEDIUM RISK (Score: {score}/100)")
            else:
                st.success(f"### LOW RISK (Score: {score}/100)")

            rules = detail.get("triggered_rules", [])
            if rules:
                st.write("**Triggered Indicators:**")
                for r in rules:
                    st.markdown(
                        f"- **{r['rule_name']}** (`+{r['points']} pts`): {r['reason']}"
                    )
            else:
                st.write(
                    "No suspicious AML risk indicators triggered. Normal activity profile."
                )

            with st.expander("Raw Transaction Data"):
                st.json(detail)
        else:
            st.warning(f"Transaction {selected_id} not found.")
else:
    st.info("No transactions found matching the current criteria.")
