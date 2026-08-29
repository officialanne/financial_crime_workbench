import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import requests
import streamlit as st
from app.services import case_service

API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

st.set_page_config(page_title="Investigation Workspace | AML Workbench", layout="wide")

st.title("Investigation Case Workspace")
st.caption(
    "Manage AML cases, review linked financial evidence, document findings, and update case lifecycles."
)


# Helper Data Fetchers
def fetch_cases(status=None, priority=None):
    if API_BASE_URL:
        try:
            params = {}
            if status and status != "ALL":
                params["status"] = status
            if priority and priority != "ALL":
                params["priority"] = priority
            res = requests.get(f"{API_BASE_URL}/cases/", params=params, timeout=5)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return case_service.list_cases(
        status=None if status == "ALL" else status,
        priority=None if priority == "ALL" else priority,
    )


def fetch_case_detail(case_id: int):
    if API_BASE_URL:
        try:
            res = requests.get(f"{API_BASE_URL}/cases/{case_id}", timeout=5)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return case_service.get_case_by_id(case_id)


def fetch_analysts():
    if API_BASE_URL:
        try:
            res = requests.get(f"{API_BASE_URL}/cases/analysts", timeout=5)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException:
            pass
    return case_service.get_all_analysts()


analysts_list = fetch_analysts()
analyst_dict = {a["AnalystID"]: f"{a['Name']} ({a['Team']})" for a in analysts_list}

# Workspace Layout Tabs
tab_active, tab_queue, tab_new = st.tabs(
    [
        "Active Case Dossier",
        "Case Queue & Search",
        "Open New Case",
    ]
)

# ACTIVE CASE DOSSIER & EVIDENCE TAB
with tab_active:
    all_cases_summary = fetch_cases()
    if all_cases_summary:
        case_options = [c["case_id"] for c in all_cases_summary]
        selected_case_id = st.selectbox(
            "Select Case ID to Review:",
            options=case_options,
            format_func=lambda x: f"Case #{x} - {next((c['status'] for c in all_cases_summary if c['case_id'] == x), '')} (Priority: {next((c['priority'] for c in all_cases_summary if c['case_id'] == x), '')})",
        )

        case = fetch_case_detail(selected_case_id)
        if case:
            # Case Header Banner
            status_colours = {"OPEN": "🔴", "IN_PROGRESS": "🟡", "CLOSED": "🟢"}
            st.markdown(
                f"### Case #{case['case_id']} | {status_colours.get(case['status'], '⚪')} Status: `{case['status']}` | Priority: `{case['priority']}`"
            )

            # Metadata Ribbon
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Assigned Analyst", case.get("analyst_name") or "Unassigned")
            m2.metric("Date Created", case.get("created_at") or "N/A")
            m3.metric("Date Closed", case.get("closed_at") or "Active (Open)")
            m4.metric(
                "Origin Alert ID",
                f"#{case['alert_id']}" if case.get("alert_id") else "Manual Review",
            )

            st.divider()

            # Lifecycle & Status Update Controls
            with st.expander("Update Case Status / Assignment"):
                u_col1, u_col2, u_col3 = st.columns(3)
                new_st = u_col1.selectbox(
                    "Change Status",
                    ["OPEN", "IN_PROGRESS", "CLOSED"],
                    index=["OPEN", "IN_PROGRESS", "CLOSED"].index(case["status"]),
                )
                new_pr = u_col2.selectbox(
                    "Change Priority",
                    ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    index=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(case["priority"]),
                )

                analyst_ids = list(analyst_dict.keys())
                curr_analyst_idx = (
                    analyst_ids.index(case["assigned_analyst_id"])
                    if case.get("assigned_analyst_id") in analyst_ids
                    else 0
                )
                new_an = u_col3.selectbox(
                    "Reassign Analyst",
                    analyst_ids,
                    index=curr_analyst_idx,
                    format_func=lambda x: analyst_dict.get(x, f"Analyst {x}"),
                )

                if st.button("Save Case Changes"):
                    update_payload = {
                        "status": new_st,
                        "priority": new_pr,
                        "assigned_analyst_id": new_an,
                    }
                    if API_BASE_URL:
                        requests.patch(
                            f"{API_BASE_URL}/cases/{case['case_id']}",
                            json=update_payload,
                        )
                    else:
                        case_service.update_case(case["case_id"], update_payload)
                    st.success(f"Case #{case['case_id']} updated successfully!")
                    st.rerun()

            # Evidence Dossier (Tabs for Evidence, Notes, Timeline)
            ev_tab1, ev_tab2, ev_tab3, ev_tab4 = st.tabs(
                [
                    "Linked Transactions",
                    "Linked Customers",
                    "Investigation Notes & Audit Log",
                    "AI Summary Preview",
                ]
            )

            with ev_tab1:
                st.subheader("Suspicious Transactions Attached to Case")
                txns = case.get("linked_transactions", [])
                if txns:
                    df_txns = pd.DataFrame(txns)
                    st.dataframe(
                        df_txns,
                        use_container_width=True,
                        column_config={
                            "risk_score": st.column_config.ProgressColumn(
                                "Risk", format="%d", min_value=0, max_value=100
                            ),
                            "risk_category": "Level",
                            "transaction_id": "Txn ID",
                            "amount": st.column_config.NumberColumn(
                                "Amount", format="%d"
                            ),
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
                    st.info("No transactions attached to this case yet.")

                # Form to attach transaction
                with st.popover("Attach Transaction by ID"):
                    tx_to_add = st.number_input(
                        "Transaction ID", min_value=1, step=1, value=9001
                    )
                    if st.button("Attach Transaction"):
                        case_service.link_transaction_to_case(
                            case["case_id"], tx_to_add
                        )
                        st.success(f"Transaction #{tx_to_add} attached.")
                        st.rerun()

            with ev_tab2:
                st.subheader("Target Customers Linked to Case")
                custs = case.get("linked_customers", [])
                if custs:
                    df_custs = pd.DataFrame(custs)
                    st.dataframe(
                        df_custs,
                        use_container_width=True,
                        column_config={
                            "customer_id": "Customer ID",
                            "name": "Customer Name",
                            "party_type": "Entity Type",
                            "country_id": "Jurisdiction",
                            "occupation": "Occupation",
                            "risk_rating_name": "KYC Risk Rating",
                        },
                    )
                else:
                    st.info("No customers linked to this case yet.")

                with st.popover("Attach Customer by ID"):
                    cust_to_add = st.number_input(
                        "Customer ID", min_value=1, step=1, value=2001
                    )
                    if st.button("Attach Customer"):
                        case_service.link_customer_to_case(case["case_id"], cust_to_add)
                        st.success(f"Customer #{cust_to_add} attached.")
                        st.rerun()

            with ev_tab3:
                st.subheader("Investigation Timeline & Audit Trail")

                # New Note Form
                with st.form("new_note_form"):
                    note_text = st.text_area("Add Investigation Finding / Action Note:")
                    act_type = st.selectbox(
                        "Activity Type",
                        ["NOTE_ADDED", "REVIEW", "DOCUMENT_REQUEST", "ESCALATION"],
                    )
                    submit_note = st.form_submit_button("Record Action")

                    if submit_note and note_text:
                        note_payload = {
                            "analyst_id": case.get("assigned_analyst_id") or 1,
                            "activity_type": act_type,
                            "description": note_text,
                        }
                        if API_BASE_URL:
                            requests.post(
                                f"{API_BASE_URL}/cases/{case['case_id']}/activities",
                                json=note_payload,
                            )
                        else:
                            case_service.add_case_activity(
                                case["case_id"], note_payload
                            )
                        st.success("Note appended to investigation audit log.")
                        st.rerun()

                # Activity Log Feed
                activities = case.get("activities", [])
                if activities:
                    for act in activities:
                        st.markdown(
                            f"**{act['created_at']}** — `{act['activity_type']}` by **{act.get('analyst_name') or 'Analyst'}**\n\n"
                            f"> {act.get('description') or 'No details provided.'}"
                        )
                        st.divider()
                else:
                    st.info("No notes or activity logs recorded for this case.")

            with ev_tab4:
                st.subheader("Investigation Summary")
                if case.get("summary_text"):
                    st.info(case["summary_text"])
                else:
                    st.write(
                        "No AI or executive summary generated yet (Will be enabled in Phase 13)."
                    )
    else:
        st.info("No cases available.")

# CASE QUEUE & TRIAGE TAB
with tab_queue:
    st.subheader("Case Queue")
    f_col1, f_col2 = st.columns(2)
    q_status = f_col1.selectbox(
        "Filter by Status", ["ALL", "OPEN", "IN_PROGRESS", "CLOSED"], index=0
    )
    q_priority = f_col2.selectbox(
        "Filter by Priority", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"], index=0
    )

    queue_data = fetch_cases(status=q_status, priority=q_priority)
    if queue_data:
        df_queue = pd.DataFrame(queue_data)
        st.dataframe(
            df_queue,
            use_container_width=True,
            column_config={
                "case_id": "Case ID",
                "priority": "Priority",
                "status": "Status",
                "analyst_name": "Assigned Analyst",
                "created_at": "Opened Date",
                "transaction_count": "Transactions",
                "customer_count": "Customers",
            },
            column_order=[
                "case_id",
                "status",
                "priority",
                "analyst_name",
                "transaction_count",
                "customer_count",
                "created_at",
            ],
        )
    else:
        st.info("No cases matching the selected queue filter.")

# OPEN NEW CASE TAB
with tab_new:
    st.subheader("Open a New Investigation")
    with st.form("create_case_form"):
        c_col1, c_col2 = st.columns(2)
        c_priority = c_col1.selectbox(
            "Initial Priority", ["HIGH", "CRITICAL", "MEDIUM", "LOW"]
        )
        c_analyst = c_col2.selectbox(
            "Assign Lead Analyst",
            list(analyst_dict.keys()),
            format_func=lambda x: analyst_dict.get(x),
        )

        c_notes = st.text_area(
            "Case Hypothesis / Reason for Investigation",
            "Unusual transaction velocity and high-value outbound transfers identified.",
        )
        c_init_txn = st.number_input(
            "Initial Suspicious Transaction ID (0 = None)",
            min_value=0,
            value=9001,
            step=1,
        )
        c_init_cust = st.number_input(
            "Initial Target Customer ID (0 = None)", min_value=0, value=2001, step=1
        )

        create_submitted = st.form_submit_button("Create Investigation Case")
        if create_submitted:
            payload = {
                "priority": c_priority,
                "status": "OPEN",
                "assigned_analyst_id": c_analyst,
                "notes": c_notes,
                "initial_transaction_ids": [c_init_txn] if c_init_txn > 0 else [],
                "initial_customer_ids": [c_init_cust] if c_init_cust > 0 else [],
            }
            if API_BASE_URL:
                res = requests.post(f"{API_BASE_URL}/cases/", json=payload)
                new_case = res.json() if res.status_code == 201 else None
            else:
                new_case = case_service.create_case(payload)

            if new_case:
                st.success(f"Case #{new_case['case_id']} created successfully!")
                st.rerun()
            else:
                st.error("Failed to create case.")
