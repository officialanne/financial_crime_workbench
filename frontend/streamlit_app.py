import streamlit as st

# Define pages
dashboard_page = st.Page(
    "pages/dashboard.py", title="Executive Dashboard", default=True
)
txn_risk_page = st.Page("pages/transactions.py", title="Transactions Risk Explorer")
network_page = st.Page("pages/network_analysis.py", title="Network Analysis")
investigation_page = st.Page("pages/investigations.py", title="Investigation Workspace")
sanctions_page = st.Page("pages/sanctions_screening.py", title="Sanctions Screening")


# Setup navigation
pg = st.navigation([dashboard_page, txn_risk_page, network_page, investigation_page, sanctions_page])

# Run the selected page
pg.run()
