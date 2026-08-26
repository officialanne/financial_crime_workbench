import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from app.services import analytics_service

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(
    page_title="Executive Dashboard | AML Workbench",
    layout="wide",
)

st.title("Financial Crime Executive Dashboard")
st.caption(
    "Macro-level operational metrics, risk distributions, and suspicious transaction queues."
)

# Sidebar: Global Filter
st.sidebar.header("Dashboard Filters")
country_filter = (
    st.sidebar.text_input("Filter by Country Code (e.g., US, GB, AE)", max_chars=2)
    .strip()
    .upper()
)
if not country_filter:
    country_filter = None


# Data Fetcher
def fetch_dashboard_data(country=None):
    if API_BASE_URL:
        try:
            params = {"country": country} if country else {}
            res = requests.get(f"{API_BASE_URL}/dashboard/", params=params, timeout=5)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    # using python analytics service
    return analytics_service.get_dashboard_summary(country=country)


data = fetch_dashboard_data(country=country_filter)

# Executive KPI Summary Cards
op = data["operational"]
rk = data["risk"]
cu = data["customers"]

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Transactions", f"{op["total_transactions"]:,}")
kpi2.metric("Total Volume (£)", f"£{op['total_volume']:,}")
kpi3.metric("High-Risk Transactions", f"{rk['high_risk_count']:,}")
kpi4.metric("Open Cases / Alerts", f"{rk['open_cases']} / {rk['total_alerts']}")

st.divider()


# Charts Row: Velocity Trends & Risk Distribution
col_trend, col_risk = st.columns([3, 2])

with col_trend:
    st.subheader("Monthly Transaction Volume & Count")
    trends_data = data.get("trends", [])
    if trends_data:
        df_trends = pd.DataFrame(trends_data)
        fig_trend = px.line(
            df_trends,
            x="period",
            y="total_volume",
            markers=True,
            title="Transaction Volume Trend (£)",
            labels={"period": "Month", "total_volume": "Total Volume (£)"},
        )
        fig_trend.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=320)
        st.plotly_chart(fig_trend, width="stretch")
    else:
        st.info("No trend data available for current filter.")

with col_risk:
    st.subheader("Risk Tier Breakdown")
    risk_df = pd.DataFrame(
        {
            "Category": ["High Risk", "Medium Risk", "Low Risk"],
            "Count": [
                rk["high_risk_count"],
                rk["medium_risk_count"],
                rk["low_risk_count"],
            ],
        }
    )
    fig_donut = px.pie(
        risk_df,
        names="Category",
        values="Count",
        hole=0.45,
        color="Category",
        color_discrete_map={
            "High Risk": "#EF4444",
            "Medium Risk": "#F59E0B",
            "Low Risk": "#10B981",
        },
    )
    fig_donut.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
    st.plotly_chart(fig_donut, width="stretch")

# Charts Row: Geographical Analytics
col_geo, col_amt = st.columns([3, 2])

with col_geo:
    st.subheader("Top Active Jurisdictions")
    country_data = data.get("top_countries", [])
    if country_data:
        df_countries = pd.DataFrame(country_data)
        fig_country = px.bar(
            df_countries,
            x="transaction_count",
            y="country_name",
            orientation="h",
            labels={"transaction_count": "Transactions", "country_name": "Country"},
            color="transaction_count",
            color_continuous_scale="Blues",
        )
        fig_country.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=320,
        )
        st.plotly_chart(fig_country, width="stretch")
    else:
        st.info("No country statistics available.")

with col_amt:
    st.subheader("Customer Risk Profile")
    cust_df = pd.DataFrame(
        {
            "Classification": ["Standard Risk Customers", "High Risk Rated (EDD)"],
            "Count": [
                cu["total_customers"] - cu["high_risk_customers"],
                cu["high_risk_customers"],
            ],
        }
    )
    fig_cust = px.bar(
        cust_df,
        x="Classification",
        y="Count",
        color="Classification",
        color_discrete_map={
            "Standard Risk Customers": "#3B82F6",
            "High Risk Rated (EDD)": "#DC2626",
        },
    )
    fig_cust.update_layout(
        margin=dict(l=10, r=10, t=30, b=10), height=320, showlegend=False
    )
    st.plotly_chart(fig_cust, width="stretch")


# Actionable Table: Recent High-Risk Transactions
st.divider()
st.subheader("Priority High-Risk Queue")
st.caption("Transactions requiring immediate review based on triggered AML rules.")

recent_high = data.get("recent_high_risk", [])
if recent_high:
    df_high = pd.DataFrame(recent_high)
    st.dataframe(
        df_high,
        width="stretch",
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score", format="%d", min_value=0, max_value=100
            ),
            "risk_category": "Level",
            "transaction_id": "Txn ID",
            "amount": st.column_config.NumberColumn("Amount", format="%d"),
            "currency_id": "Currency",
            "origin_country_id": "Country",
            "transaction_date": "Date",
            "reasons": "Triggered AML Rules",
        },
        column_order=[
            "risk_score",
            "risk_category",
            "transaction_id",
            "amount",
            "currency_id",
            "origin_country_id",
            "reasons",
            "transaction_date",
        ],
    )
else:
    st.success("No high-risk transactions pending review.")
