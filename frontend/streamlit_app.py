import streamlit as st

# Define pages
txn_risk_page = st.Page("pages/transactions.py", title="Transactions Risk Explorer")

# Setup navigation
pg = st.navigation([txn_risk_page])

# Run the selected page
pg.run()
