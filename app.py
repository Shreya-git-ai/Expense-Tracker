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

st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💰 Expense Tracker")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "Add Expense",
        "Manage Expenses",
        "Charts",
        "Filters & Export",
    ],
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