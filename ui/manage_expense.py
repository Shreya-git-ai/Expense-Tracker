"""
ui/manage_expense.py

Streamlit UI for editing and deleting existing expenses.

Exposes a single show() function, called from app.py's router, same
pattern as add_expense.py.
"""

import streamlit as st
from datetime import date, datetime

from database.db_operations import get_all_expenses, update_expense, delete_expense
from utils.validation import validate_expense, VALID_CATEGORIES


def show():
    st.subheader("✏️ Manage Expenses")

    df = get_all_expenses()

    # Guard clause: if there's no data yet, don't render selectboxes/forms
    # against an empty DataFrame - show a friendly message and exit early.
    if df.empty:
        st.info("No expenses recorded yet. Add one from the 'Add Expense' page.")
        return

    # Show the full table so the user can see every expense (and its id)
    # before deciding which one to act on.
    st.dataframe(df, use_container_width=True)

    # Build a human-readable label per row (id + category + amount + date)
    # instead of a bare list of numeric IDs - much easier for the user to
    # correctly identify which expense they actually want to edit.
    df["label"] = df.apply(
        lambda row: f"#{row['id']} - {row['category']} - ₹{row['amount']} - {row['date']}",
        axis=1,
    )
    selected_label = st.selectbox("Select an expense to edit or delete", df["label"])

    # Extract the numeric id back out of the label string, e.g. "#7 - Food..." -> 7
    selected_id = int(selected_label.split(" - ")[0].replace("#", ""))
    selected_row = df[df["id"] == selected_id].iloc[0]

    st.markdown("---")
    col1, col2 = st.columns(2)

    # ------------------------- EDIT -------------------------
    with col1:
        st.markdown("**Edit this expense**")

        new_amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            step=1.0,
            value=float(selected_row["amount"]),
            key="edit_amount",
        )

        # The database stores dates as 'YYYY-MM-DD' strings; st.date_input
        # needs an actual Python date object, so we parse it back here.
        current_date = datetime.strptime(selected_row["date"], "%Y-%m-%d").date()
        new_date = st.date_input(
            "Date", value=current_date, max_value=date.today(), key="edit_date"
        )

        new_category = st.selectbox(
            "Category",
            VALID_CATEGORIES,
            index=VALID_CATEGORIES.index(selected_row["category"])
            if selected_row["category"] in VALID_CATEGORIES
            else 0,
            key="edit_category",
        )

        new_description = st.text_input(
            "Description", value=selected_row["description"] or "", key="edit_description"
        )

        if st.button("Update Expense"):
            # Same validation function used in add_expense.py - reused here
            # rather than duplicated, so both the add and edit flows enforce
            # identical rules.
            is_valid, errors = validate_expense(
                new_amount, new_date, new_category, new_description
            )
            if not is_valid:
                for error in errors:
                    st.error(error)
            else:
                update_expense(
                    selected_id,
                    new_amount,
                    new_date.isoformat(),
                    new_category,
                    new_description,
                )
                st.success("Expense updated!")
                # st.rerun() immediately refreshes the page so the table
                # above reflects the update right away, instead of showing
                # stale data until some unrelated interaction triggers a
                # natural re-run.
                st.rerun()

    # ------------------------ DELETE ------------------------
    with col2:
        st.markdown("**Delete this expense**")
        st.warning(
            f"This will permanently delete expense #{selected_id}. "
            "This cannot be undone."
        )
        if st.button("Delete Expense", type="primary"):
            delete_expense(selected_id)
            st.success("Expense deleted.")
            st.rerun()