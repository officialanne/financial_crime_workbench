import streamlit as st

# Define pages
dashboard_page = st.Page(
    "pages/dashboard.py", title="Executive Dashboard", default=True
)
txn_risk_page = st.Page("pages/transactions.py", title="Transactions Risk Explorer")


# Setup navigation
pg = st.navigation([dashboard_page, txn_risk_page])

# Run the selected page
pg.run()
