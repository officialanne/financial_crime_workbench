# Creates the interactive Streamlit network interface using PyVis.
# Nodes are colour-coded by party type (Individual, Business, Bank, Crypto, Sanctioned Entity)
# and sized by Betweenness Centrality to visually highlight money mules and layering hubs
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from pyvis.network import Network
import requests
import streamlit as st
import streamlit.components.v1 as components
from app.services import graph_analysis

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(page_title="Network Analysis | AML Workbench", layout="wide")

st.title("Financial Transaction Network Analysis")
st.caption(
    "Detect money laundering rings, mule accounts, layering chains, and intermediary hubs using link analysis."
)

# Sidebar: Network query filters
st.sidebar.header("Network Filters")

# filters
risk_filter = st.sidebar.selectbox(
    "Risk Priority", ["ALL", "HIGH", "MEDIUM", "LOW"], index=0
)
min_amount = st.sidebar.number_input(
    "Min Transfer Amount (£)", min_value=0, value=5000, step=1000
)
country = (
    st.sidebar.text_input("Origin Country (e.g., US, RU, AE)", max_chars=2)
    .strip()
    .upper()
)
customer_id = st.sidebar.number_input(
    "Target Customer ID (0 = All)", min_value=0, value=0, step=1
)
party_id = st.sidebar.number_input(
    "Target Party ID (0 = All)", min_value=0, value=0, step=1
)
limit = st.sidebar.slider(
    "Max Transaction Edges", min_value=20, max_value=300, value=80, step=10
)

# parameters for creating the graph
graph_params = {
    "min_amount": min_amount if min_amount > 0 else None,
    "country": country if country else None,
    "risk_category": None if risk_filter == "ALL" else risk_filter,
    "customer_id": customer_id if customer_id > 0 else None,
    "party_id": party_id if party_id > 0 else None,
    "limit": limit,
}


# Data Fetcher
def fetch_graph_data(params):
    if API_BASE_URL:
        try:
            p = {k: v for k, v in params.items() if v is not None}
            res = requests.get(f"{API_BASE_URL}/graph/", params=p, timeout=8)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return graph_analysis.build_network_graph(**params)


# saving the data
graph_data = fetch_graph_data(graph_params)
nodes = graph_data.get("nodes", [])
edges = graph_data.get("edges", [])
stats = graph_data.get("statistics", {})

# Top Network KPI Ribbon
col1, col2, col3, col4 = st.columns(4)
col1.metric("Network Entities (Nodes)", stats.get("total_nodes", 0))
col2.metric("Transfers (Edges)", stats.get("total_edges", 0))
col3.metric("Disconnected Clusters", stats.get("connected_components_count", 0))
col4.metric("Graph Density", f"{stats.get('density', 0.0):.4f}")

st.divider()


# PyVis interactive graph construction
col_graph, col_hubs = st.columns([3, 1])

with col_graph:
    st.subheader("Interactive Entity Relationship Graph")
    st.caption(
        "Drag nodes, zoom to inspect connections, or hover over entities to view metadata."
    )

    if nodes and edges:
        # Initialise PyVis network
        net = Network(
            height="580px",
            width="100%",
            directed=True,
            bgcolor="#111827",
            font_color="#F3F4F6",
        )

        # Configure physics for readable spacing
        net.force_atlas_2based(
            gravity=-50,
            central_gravity=0.01,
            spring_length=100,
            spring_strength=0.08,
            damping=0.4,
        )

        # Node Colour Palette based on Entity Type
        TYPE_COLOURS = {
            "INDIVIDUAL": "#3B82F6",  # Blue
            "BUSINESS": "#8B5CF6",  # Purple
            "MERCHANT": "#06B6D4",  # Cyan
            "BANK": "#10B981",  # Green
            "CRYPTO": "#F59E0B",  # Amber
        }

        # Add Nodes
        for n in nodes:
            is_sanctioned = n.get("is_sanctioned", False)
            ptype = n.get("party_type", "INDIVIDUAL")

            # Determine colour & shape
            if is_sanctioned:
                colour = "#EF4444"  # Red
                shape = "diamond"
                size = 28
            else:
                colour = TYPE_COLOURS.get(ptype, "#6B7280")
                shape = "dot"
                # Size proportionally to Betweenness Centrality (bridges)
                size = 14 + int(n.get("betweenness_centrality", 0.0) * 80)

            title_tooltip = f"""
            <b>{n['label']}</b><br>
            Party ID: {n['id']}<br>
            Type: {ptype}<br>
            Country: {n.get('country_id') or 'N/A'}<br>
            Betweenness Centrality: {n.get('betweenness_centrality', 0.0):.4f}<br>
            Connections (Degree): {n.get('degree', 0)}
            """
            if is_sanctioned:
                title_tooltip += "<br><b style='color:red;'> SANCTIONED ENTITY</b>"

            net.add_node(
                n["id"],
                label=f"{n['label'][:16]}..",
                title=title_tooltip,
                color=colour,
                shape=shape,
                size=size,
            )

        # Add Edges
        for e in edges:
            risk = e.get("risk_score", 0)
            edge_colour = (
                "#EF4444" if risk >= 60 else ("#F59E0B" if risk >= 30 else "#4B5563")
            )
            width = 2.5 if risk >= 60 else 1.2

            net.add_edge(
                e["source"],
                e["target"],
                title=f"Txn #{e['transaction_id']}: £{e['amount']:,} {e['currency_id']} ({e['transaction_date']})",
                color=edge_colour,
                width=width,
                arrows="to",
            )

        # Generate and render HTML
        html_data = net.generate_html()
        components.iframe(html_data, height=600, scrolling=False)
    else:
        st.info("No transaction relationships match current filter thresholds.")

with col_hubs:
    st.subheader("🎯 Bridge Hubs & Mules")
    st.caption(
        "Entities with high betweenness centrality acting as flow intermediaries."
    )

    hubs = stats.get("top_hubs", [])
    if hubs:
        for idx, h in enumerate(hubs, start=1):
            st.markdown(f"**{idx}. {h['name']}**")
            st.write(f"- Type: `{h['party_type']}` | ID: `{h['party_id']}`")
            st.write(
                f"- Connections: `{h['degree']}` | Bridge Centrality: `{h['betweenness_centrality']:.4f}`"
            )
            st.divider()
    else:
        st.write("No prominent intermediary hubs detected.")

# 3. Legend & Node Colour Guide
st.subheader("🎨 Entity Legend")
l1, l2, l3, l4, l5, l6 = st.columns(6)
l1.markdown("🔵 **Individual**")
l2.markdown("🟣 **Business**")
l3.markdown("🟢 **Bank Terminal**")
l4.markdown("🟡 **Crypto / VASP**")
l5.markdown("🔴 **Sanctioned Entity**")
l6.markdown("➡️ **Red Edge = High Risk Txn**")
