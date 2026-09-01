"""
ui/add_expense.py

Streamlit UI for adding a new expense.

Exposes a single show() function - app.py's router calls this when the
user navigates to the "Add Expense" page. This one-function-per-file
pattern means app.py never needs to know the internal details of this
page, and this file never needs to know anything about the other pages.
"""

import streamlit as st
from datetime import date

from database.db_operations import add_expense
from utils.validation import validate_expense, VALID_CATEGORIES


def show():
    st.subheader(" Add Expense")

    # st.form groups all the inputs below into ONE unit that only triggers
    # a script re-run when the submit button is clicked - not on every
    # keystroke or widget change, which is Streamlit's default behaviour
    # outside a form. This is both a performance choice and a UX choice
    # (the user's half-typed input doesn't vanish/reset mid-typing).
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            amount = st.number_input(
                "Amount (₹)", min_value=0.0, step=1.0, format="%.2f"
            )
            expense_date = st.date_input(
                "Date", value=date.today(), max_value=date.today()
            )

        with col2:
            category = st.selectbox("Category", VALID_CATEGORIES)
            description = st.text_input("Description")

        submitted = st.form_submit_button("Add Expense")

        if submitted:
            # Validate BEFORE touching the database at all. This keeps
            # invalid data from ever reaching db_operations.py, rather
            # than catching problems after an insert has already happened.
            is_valid, errors = validate_expense(
                amount, expense_date, category, description
            )

            if not is_valid:
                for error in errors:
                    st.error(error)
            else:
                # .isoformat() converts the Python date object into a
                # 'YYYY-MM-DD' string, matching exactly how dates are
                # stored in the database (see db_setup.py schema notes
                # for why this specific format was chosen).
                add_expense(
                    amount, expense_date.isoformat(), category, description
                )
                st.success("Expense added successfully!")