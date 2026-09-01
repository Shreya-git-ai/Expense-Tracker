"""
app.py

Main Streamlit entry point. This file ONLY handles navigation/routing
between pages - no business logic lives here. Each page's actual UI code
lives in its own file under ui/, exposing either a show() function
(add_expense, manage_expense, dashboard, charts) or, in the case of
filters_export, a render_filters_and_exports(df, db_path) function.

KNOWN ISSUE (flagged, not yet fixed as of this commit):
ui/filters_export.py references df["type"] and df["payment_method"]
columns that do NOT exist in our locked schema (see database/db_setup.py -
expenses table has no "type" or "payment_method" column; this app only
tracks expenses, not income, and never scoped a payment method field).
Calling render_filters_and_exports() will raise a KeyError until that
file is updated to match the actual schema.

Until Member D fixes this, the Filters & Export page is wrapped in a
try/except below so a bug on THAT page doesn't take down the entire app
during a demo. The other four pages are unaffected and fully working.
"""

import streamlit as st
from database.db_setup import init_db, DB_PATH
from database.db_operations import get_all_expenses
from ui import add_expense, manage_expense, dashboard, charts, filters_export

# Create the database tables on startup (safe to call every run - see
# db_setup.py, CREATE TABLE IF NOT EXISTS is idempotent).
init_db()
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #1e293b);
        border-right: 1px solid #2d3b52;
    }
    section[data-testid="stSidebar"] h1 {
        color: #f8fafc;
        font-size: 20px;
    }
    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
        font-size: 15px;
        padding: 8px 0px;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 4px;
    }
    </style>
""", unsafe_allow_html=True)
st.set_page_config(page_title="Expense Tracker", layout="wide")

# --- GLOBAL STYLES: applied on every page, not just Dashboard ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Sidebar polish - global so it's consistent across all pages */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #1e293b);
        border-right: 1px solid #2d3b52;
    }
    section[data-testid="stSidebar"] label {
        color: #cbd5e1;
        font-size: 15px;
        padding: 8px 0px;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 4px;
    }

    /* Global input styling - keeps Filters/Manage/Add pages consistent */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #1e293b !important;
        border: 1px solid #2d3b52 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
    }

    button[kind="secondary"], button[kind="primary"] {
        border-radius: 8px !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #2d3b52;
    }
    </style>
""", unsafe_allow_html=True)

st.title("FinTrack")

# --- Sidebar branding + nav ---
st.sidebar.markdown("""
    <div style="padding: 8px 0 20px 0;">
        <div style="font-size: 20px; font-weight: 700; color: #f8fafc;">Expense Tracker</div>
        <div style="font-size: 13px; color: #94a3b8;">Track. Analyze. Save.</div>
    </div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "",
    [
        "Dashboard",
        "Add Expense",
        "Manage Expenses",
        "Charts",
        "Filters & Export",
    ],
    label_visibility="collapsed",
)

if page == "Dashboard":
    dashboard.show()

elif page == "Add Expense":
    add_expense.show()

elif page == "Manage Expenses":
    manage_expense.show()

elif page == "Charts":
    charts.show()

elif page == "Filters & Export":
    # Wrapped defensively: filters_export.py currently assumes a "type"
    # and "payment_method" column that don't exist in our schema (see
    # module docstring above). This try/except prevents that bug from
    # crashing the whole app - it isolates the failure to just this page
    # so Dashboard/Add/Manage/Charts stay usable during testing and demo.
    try:
        df = get_all_expenses()
        filters_export.render_filters_and_exports(df, db_path=DB_PATH)
    except KeyError as e:
        st.error(
            f"Filters & Export page has a bug: missing column {e}. "
            "This page expects 'type' and 'payment_method' columns that "
            "aren't part of our database schema. Needs a fix in "
            "ui/filters_export.py before this page will work."
        )