import streamlit as st

# Define pages
txn_page = st.Page("txn.py", title="Transactions Explorer")
risk_page = st.Page("risk.py", title="Risk Explorer")

# Setup navigation
pg = st.navigation([txn_page, risk_page])

# Run the selected page
pg.run()
