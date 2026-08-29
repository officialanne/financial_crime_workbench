# Creates the Streamlit Sanctions Screening interface featuring real-time fuzzy search,
# confidence badges, source attribution, and direct one-click attachment of sanction hits
# to open investigation cases.
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import requests
import streamlit as st
from app.services import case_service, sanctions_service
from typing import Optional

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(page_title="Sanctions Screening | AML Workbench", layout="wide")

st.title("Sanctions & Watchlist Screening")
st.caption(
    "Screen customers and counterparties against global watchlists (OFSI, UN, EU, OFAC) with fuzzy matching."
)

tab_screen, tab_watchlist = st.tabs(["Screen Entity / Customer", "Watchlist Directory"])


# Helper Data Fetchers
def run_screening(name: str, threshold: float, country: Optional[str] = None):
    if API_BASE_URL:
        try:
            payload = {
                "query_name": name,
                "threshold": threshold,
                "country_id": country or None,
            }
            res = requests.post(
                f"{API_BASE_URL}/sanctions/screen", json=payload, timeout=5
            )
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return sanctions_service.screen_name(name, threshold=threshold, country_id=country)


def fetch_sanctions_list(country=None, source=None):
    if API_BASE_URL:
        try:
            params = {}
            if country:
                params["country_id"] = country
            if source and source != "ALL":
                params["source"] = source
            res = requests.get(f"{API_BASE_URL}/sanctions/", params=params, timeout=5)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return sanctions_service.list_sanctions(
        country_id=country, source=None if source == "ALL" else source
    )


# SCREEN ENTITY OR CUSTOMER
with tab_screen:
    st.subheader("Screen an Individual or Company")

    col_input, col_thresh = st.columns([3, 1])
    search_name = col_input.text_input(
        "Enter Target Name to Screen",
        value="",
        placeholder="e.g. Vladimir, Blackstone, or John Smith",
    )
    threshold = col_thresh.slider(
        "Match Sensitivity Threshold",
        min_value=50,
        max_value=100,
        value=70,
        step=5,
        help="Lower values catch typos and aliases; higher values require closer spelling.",
    )

    country_filter = (
        st.text_input(
            "Filter by Jurisdiction (Optional 2-letter Country Code)", max_chars=2
        )
        .strip()
        .upper()
    )

    screen_btn = st.button("Run Sanctions Screening", type="primary")

    if screen_btn and search_name:
        result = run_screening(
            search_name,
            threshold=threshold / 100.0,
            country=country_filter if country_filter else None,
        )
        matches = result.get("matches", [])

        st.divider()

        if matches:
            st.warning(
                f"Found {len(matches)} potential sanction match(es) for **{search_name}**:"
            )

            # Case options to allow direct attachment
            cases = case_service.list_cases(status="OPEN")
            case_options = [c["case_id"] for c in cases]

            for idx, m in enumerate(matches, start=1):
                conf = m["confidence_percentage"]
                badge = "🔴 HIGH CONFIDENCE" if conf >= 85 else "🟡 POSSIBLE MATCH"

                with st.expander(
                    f"{idx}. {m['entity_name']} — {badge} ({conf}% Match)",
                    expanded=(idx == 1),
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Matched Name:** `{m['entity_name']}`")
                        st.markdown(f"**Match Type:** `{m['match_type']}`")
                        st.markdown(f"**Confidence Score:** `{conf}%`")
                        st.markdown(f"**Reason:** {m['reason']}")
                    with c2:
                        st.markdown(
                            f"**Watchlist Source:** `{m.get('source') or 'Consolidated List'}`"
                        )
                        st.markdown(
                            f"**Sanctions Programme:** `{m.get('programme') or 'General Restrictions'}`"
                        )
                        st.markdown(f"**Country:** `{m.get('country_id') or 'N/A'}`")
                        st.markdown(
                            f"**Listed Date:** `{m.get('listed_date') or 'N/A'}`"
                        )
                        # st.markdown(f"**Delisted Date:** `{m.get('delisted_dste') or 'N/A'}`")

                    # Attach to Case Action
                    if case_options:
                        st.write("---")
                        col_case, col_action = st.columns([2, 1])
                        target_case = col_case.selectbox(
                            "Attach evidence to Case #:",
                            case_options,
                            key=f"case_select_{m['sanction_id']}",
                        )
                        if col_action.button(
                            "Attach to Case", key=f"attach_{m['sanction_id']}"
                        ):
                            sanctions_service.link_sanction_to_case(
                                target_case, m["sanction_id"]
                            )
                            case_service.add_case_activity(
                                target_case,
                                {
                                    "analyst_id": 1,
                                    "activity_type": "SANCTIONS_MATCH",
                                    "description": f"Sanctions match confirmed: '{m['entity_name']}' ({conf}% match) under {m.get('programme')}.",
                                },
                            )
                            st.success(
                                f"Sanction record #{m['sanction_id']} attached to Case #{target_case}."
                            )
        else:
            st.success(
                f"✅ No sanction matches found for **{search_name}** at {threshold}% threshold."
            )

# WATCHLIST DIRECTORY
with tab_watchlist:
    st.subheader("Sanctions Master Database")

    col_src, col_c = st.columns(2)
    source_choice = col_src.selectbox(
        "Watchlist Source",
        [
            "ALL",
            "OFSI-CONSOLIDATED",
            "EU-FINANCIAL-SANCTIONS",
            "UN-SECURITY-COUNCIL",
            "FATF-HIGH-RISK-MONITORING",
        ],
    )
    c_code = (
        col_c.text_input("Country Code", max_chars=2, key="watch_country")
        .strip()
        .upper()
    )

    records = fetch_sanctions_list(
        country=c_code if c_code else None, source=source_choice
    )

    if records:
        df_sanct = pd.DataFrame(records)
        st.dataframe(
            df_sanct,
            use_container_width=True,
            column_config={
                "sanction_id": "Sanction ID",
                "entity_name": "Sanctioned Entity Name",
                "country_id": "Jurisdiction",
                "programme": "Programme",
                "source": "Watchlist Authority",
                "listed_date": "Listed Date",
                "delisted_date": "Delisted Date",
            },
            column_order=[
                "sanction_id",
                "entity_name",
                "programme",
                "source",
                "country_id",
                "listed_date",
                "delisted_date",
            ],
        )
    else:
        st.info("No sanctions records match the current filters.")
