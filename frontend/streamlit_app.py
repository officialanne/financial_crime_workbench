import pandas as pd
import requests
import streamlit as st

# base URL for the FastAPI backend
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Transaction Explorer | AML Workbench",
    layout="wide",
)

st.title("Transaction Explorer")
st.caption("Investigate financial flows, suspicious amounts, and transaction counterparties.")

# SIDEBAR: Query Filters
st.sidebar.header("Filter Transactions")

limit = st.sidebar.slider("Number of records", min_value=10, max_value=500, value=100, step=10)
min_amount = st.sidebar.number_input("Minimum Amount", min_value=0, value=0, step=1000)
country = st.sidebar.text_input("Origin Country Code (e.g., US, GB, AE)", max_chars=2).strip()
party_id = st.sidebar.number_input("Party ID (Sender/Receiver)", min_value=0, value=0, step=1)

# Build Query Parameters
params = {"limit": limit}
if min_amount > 0:
    params["min_amount"] = min_amount
if country:
    params["country"] = country.upper()
if party_id > 0:
    params["party_id"] = party_id


# API Call Helper
def fetch_transactions(query_params):
    try:
        response = requests.get(f"{API_BASE_URL}/transactions/", params=query_params, timeout=5)
        if response.status_code == 200:
            return response.json()
        st.error(f"API Error ({response.status_code}): {response.text}")
        return []
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to FastAPI at '{API_BASE_URL}'. Make sure Uvicorn is running.")
        return []

# MAIN CONTENT: Display Transactions
transactions_data = fetch_transactions(params)

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
    selected_id = st.number_input("Enter Transaction ID to Inspect", min_value=1, step=1, value=int(df.iloc[0]["transaction_id"]))

    if st.button("Inspect Details"):
        try:
            detail_res = requests.get(f"{API_BASE_URL}/transactions/{selected_id}", timeout=5)
            if detail_res.status_code == 200:
                txn = detail_res.json()
                st.json(txn)
            else:
                st.warning(f"Transaction ID {selected_id} not found.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching transaction: {e}")

    else:
        st.info("No transactions found matching the current filters.")