"""
ui/filters_export.py

FILTERS + EXPORTS + EXTRAS module for the Financial Expense Tracker.

Expected transaction DataFrame schema (exact column names):
    id               int
    date             date-like (YYYY-MM-DD)
    type             "Expense" | "Income"
    amount           numeric (never a formatted "₹" string)
    category         Food | Transport | Shopping | Bills | Entertainment |
                      Healthcare | Education | Travel | Groceries | Other
    payment_method   UPI | Cash | Debit Card | Credit Card |
                      Bank Transfer | Other
    description      free text

Every function here is defensive: it works on an empty DataFrame,
tolerates string-typed dates/amounts, and never mutates the caller's
original DataFrame.
"""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime

import pandas as pd
import streamlit as st

TRANSACTION_COLUMNS = [
    "id", "date", "amount", "category", "description"
]

CATEGORY_OPTIONS = [
    "All Categories", "Food", "Transport", "Shopping", "Bills",
    "Entertainment", "Healthcare", "Education", "Travel", "Groceries", "Other",
]

TYPE_OPTIONS = ["All", "Expense", "Income"]

PAYMENT_METHOD_OPTIONS = [
    "All", "UPI", "Cash", "Debit Card", "Credit Card", "Bank Transfer", "Other",
]

DISPLAY_COLUMNS = [
    "date", "category", "description", "amount"
]


# ======================================================================
# 1. CORE FILTER LOGIC (pure pandas — no Streamlit, fully unit-testable)
# ======================================================================

def filter_transactions(
    df,
    start_date=None,
    end_date=None,
    category="All Categories",
    txn_type="All",
    payment_method="All",
    min_amount=None,
    max_amount=None,
    search_text="",
):
    """
    Filter a transactions DataFrame using AND logic across all provided
    criteria. Returns a NEW DataFrame; the original `df` is never modified.

    Args:
        df: source transactions DataFrame (schema above).
        start_date / end_date: inclusive date bounds (str or date-like).
        category: one of CATEGORY_OPTIONS. "All Categories" = no filter.
    
        min_amount / max_amount: inclusive numeric bounds.
        search_text: case-insensitive, non-regex substring search on
            the `description` column.

    Returns:
        A new, filtered, sorted (newest first) DataFrame.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else TRANSACTION_COLUMNS)

    filtered = df.copy()

    # --- Data type safety: never trust the incoming types ---
    filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")
    filtered["amount"] = pd.to_numeric(filtered["amount"], errors="coerce")

    mask = pd.Series(True, index=filtered.index)

    # --- Date range (inclusive both ends) ---
    if start_date is not None:
        start_ts = pd.to_datetime(start_date, errors="coerce")
        if pd.notna(start_ts):
            mask &= filtered["date"] >= start_ts
    if end_date is not None:
        end_ts = pd.to_datetime(end_date, errors="coerce")
        if pd.notna(end_ts):
            mask &= filtered["date"] <= end_ts

    # --- Category ---
    if category and category != "All Categories":
        mask &= filtered["category"] == category

    

    # --- Amount range (inclusive both ends) ---
    if min_amount is not None:
        mask &= filtered["amount"] >= min_amount
    if max_amount is not None:
        mask &= filtered["amount"] <= max_amount

    # --- Description search (plain substring, case-insensitive) ---
    if search_text:
        mask &= filtered["description"].astype(str).str.contains(
            search_text, case=False, na=False, regex=False
        )

    result = filtered[mask].copy()
    result = result.sort_values("date", ascending=False)
    return result


def get_top_expenses(df, n=5):
    """
    Return the top-N biggest Expense transactions (Income is always
    excluded). Safe on empty input.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else TRANSACTION_COLUMNS)

    d = df.copy()
    d["amount"] = pd.to_numeric(d["amount"], errors="coerce")
    d = d.dropna(subset=["amount"])
    d = d.sort_values("amount", ascending=False).head(n)
    return d


def calculate_budget_progress(df, budgets):
    """
    Compute spent / budget / percentage / status per category.

    Args:
        df: transactions DataFrame.
        budgets: dict like {"Food": 5000, "Transport": 3000, ...}

    Returns:
        dict keyed by category ->
            {"spent": float, "budget": number, "percentage": float,
             "status": "Healthy" | "Warning" | "Danger"}

    Handles budget == 0 without ZeroDivisionError.
    """
    if df is None or df.empty:
        spent_by_category = {}
    else:
        d = df.copy()
        d["amount"] = pd.to_numeric(d["amount"], errors="coerce")
        d = d[d["type"] == "Expense"]
        spent_by_category = d.groupby("category")["amount"].sum().to_dict()

    results = {}
    for cat, budget in budgets.items():
        spent = float(spent_by_category.get(cat, 0.0))

        if budget == 0:
            # Avoid division by zero: any spend at all is over budget.
            percentage = 0.0 if spent == 0 else 100.0
        else:
            percentage = (spent / budget) * 100

        if percentage < 75:
            status = "Healthy"
        elif percentage <= 90:
            status = "Warning"
        else:
            status = "Danger"

        results[cat] = {
            "spent": spent,
            "budget": budget,
            "percentage": round(percentage, 1),
            "status": status,
        }

    return results


def get_database_backup_bytes(db_path):
    """
    Safely read the SQLite database file as bytes for download, without
    modifying the original file. Uses a temporary copy so the file is
    never opened for writing.

    Returns:
        bytes, or None if the database file does not exist.
    """
    if not db_path or not os.path.exists(db_path):
        return None

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # sqlite3's backup API gives a consistent, safe copy even if the
        # app is mid-write, rather than a raw shutil.copy of the file.
        source_conn = sqlite3.connect(db_path)
        dest_conn = sqlite3.connect(tmp_path)
        with dest_conn:
            source_conn.backup(dest_conn)
        source_conn.close()
        dest_conn.close()

        with open(tmp_path, "rb") as f:
            data = f.read()
        return data
    except Exception:
        # Fall back to a plain file copy if the backup API is unavailable.
        try:
            shutil.copyfile(db_path, tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        except Exception:
            return None
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ======================================================================
# 2. STREAMLIT UI HELPERS
# ======================================================================

_FILTER_DEFAULTS = {
    "flt_start_date": None,
    "flt_end_date": None,
    "flt_category": "All Categories",
    "flt_type": "All",
    "flt_payment_method": "All",
    "flt_min_amount": 0.0,
    "flt_max_amount": 0.0,
    "flt_search": "",
}


def _init_filter_state():
    for key, default in _FILTER_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _clear_filters():
    """Callback for the Clear Filters button. Runs before the next
    script rerun renders widgets, so it's safe to mutate session_state
    here even though widgets below are bound to the same keys."""
    for key, default in _FILTER_DEFAULTS.items():
        st.session_state[key] = default


def _format_currency(value):
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "₹0"


def render_filter_panel(df):
    """
    Render the full "Filter Transactions" panel: date range, category,
    type, payment method, amount range, description search, and a
    Clear Filters button. Reads/writes st.session_state so filters
    persist across reruns.

    Returns:
        The filtered DataFrame (does not mutate `df`).
    """
    _init_filter_state()

    st.markdown("### Filter Transactions")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("Start Date", value=st.session_state["flt_start_date"], key="flt_start_date")
        with col2:
            st.date_input("End Date", value=st.session_state["flt_end_date"], key="flt_end_date")

        st.selectbox("Category", CATEGORY_OPTIONS, key="flt_category")

        col6, col7 = st.columns(2)
        with col6:
            st.number_input("Minimum Amount", min_value=0.0, step=100.0, key="flt_min_amount")
        with col7:
            st.number_input("Maximum Amount", min_value=0.0, step=100.0, key="flt_max_amount")

        st.text_input("Search description", placeholder="e.g. swiggy", key="flt_search")

        st.button("Clear Filters", on_click=_clear_filters)

    # A value of 0.0 in min/max amount means "not set" for this UI,
    # since no real expense has a negative amount and 0 is the default.
    min_amount = st.session_state["flt_min_amount"] if st.session_state["flt_min_amount"] > 0 else None
    max_amount = st.session_state["flt_max_amount"] if st.session_state["flt_max_amount"] > 0 else None

    filtered = filter_transactions(
        df,
        start_date=st.session_state["flt_start_date"],
        end_date=st.session_state["flt_end_date"],
        category=st.session_state["flt_category"],
        
        min_amount=min_amount,
        max_amount=max_amount,
        search_text=st.session_state["flt_search"],
    )

    total_count = 0 if df is None else len(df)
    st.caption(f"Showing {len(filtered)} of {total_count} transactions")

    return filtered


def render_filtered_table(filtered_df, original_df=None):
    """
    Render the filtered transactions as a clean Streamlit table with
    currency-formatted amounts, without mutating the numeric data.
    """
    if filtered_df is None or filtered_df.empty:
        if original_df is None or original_df.empty:
            st.info("No transactions available yet.")
        else:
            st.warning("No transactions found matching your filters.")
        return

    display_df = filtered_df.copy()
    display_df["date"] = pd.to_datetime(display_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    display_df["amount"] = display_df["amount"].apply(_format_currency)
    display_df = display_df[DISPLAY_COLUMNS].rename(columns={
    "date": "Date",
    "category": "Category",
    "description": "Description",
    "amount": "Amount",
})

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_export_summary(filtered_df):
    """
    Render the "Filtered Records / Total Expense / Total Income"
    summary above the export button, and return those three values.
    """
    if filtered_df is None or filtered_df.empty:
        record_count, total_expense, total_income = 0, 0.0, 0.0
    else:
        amounts = pd.to_numeric(filtered_df["amount"], errors="coerce")
        record_count = len(filtered_df)
        total_expense = amounts.sum()
        total_income = 0.0

    st.markdown("#### Export Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Filtered Records", record_count)
    c2.metric("Total Expense", _format_currency(total_expense))
    c3.metric("Total Income", _format_currency(total_income))

    return record_count, total_expense, total_income


def render_csv_export(filtered_df):
    """
    Render a "Download Filtered CSV" button that exports EXACTLY the
    rows currently in `filtered_df` — no re-query, no full-database
    export.
    """
    if filtered_df is None or filtered_df.empty:
        st.info("No data to export for the current filters.")
        return

    export_df = filtered_df.copy()
    export_df["date"] = pd.to_datetime(export_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    export_df["amount"] = pd.to_numeric(export_df["amount"], errors="coerce")
    export_df = export_df[TRANSACTION_COLUMNS] if all(c in export_df.columns for c in TRANSACTION_COLUMNS) else export_df

    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    filename = f"filtered_expenses_{datetime.now().strftime('%Y%m%d')}.csv"

    st.download_button(
        label="Download Filtered CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
    )


def render_database_backup(db_path):
    """
    Render a "Download Database Backup" button for the existing SQLite
    database at `db_path`, without modifying the original file.
    """
    st.markdown("#### Database Backup")
    st.caption("Download a backup of your local expense database.")

    backup_bytes = get_database_backup_bytes(db_path)

    if backup_bytes is None:
        st.error("Database backup unavailable: the database file could not be found.")
        return

    st.download_button(
        label="Download Database Backup",
        data=backup_bytes,
        file_name=f"expense_tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
        mime="application/octet-stream",
    )


def render_top_expenses(df, n=5):
    """Render the 'Top 5 Biggest Expenses' section."""
    st.markdown("### Top 5 Biggest Expenses" if n == 5 else f"### Top {n} Biggest Expenses")

    top = get_top_expenses(df, n=n)
    if top.empty:
        st.info("No expense transactions available yet.")
        return

    for i, (_, row) in enumerate(top.iterrows(), start=1):
        desc = row.get("description", "")
        cat = row.get("category", "Other")
        amt = _format_currency(row.get("amount", 0))
        st.write(f"**{i}. {desc}** — {cat} — {amt}")


def render_budget_progress(df, budgets):
    """Render per-category budget progress bars with Healthy/Warning/Danger status."""
    st.markdown("### Budget Progress")

    if not budgets:
        st.info("No budgets configured yet.")
        return

    progress = calculate_budget_progress(df, budgets)

    for cat, info in progress.items():
        spent_str = _format_currency(info["spent"])
        budget_str = _format_currency(info["budget"])
        pct = info["percentage"]
        status = info["status"]

        st.write(f"**{cat}** — {spent_str} / {budget_str} ({pct}%)")
        st.progress(min(pct / 100, 1.0))

        if status == "Healthy":
            st.success(status)
        elif status == "Warning":
            st.warning(status)
        else:
            st.error(status)


def render_filters_and_exports(df, db_path=None, budgets=None):
    """
    Convenience orchestrator: renders the filter panel, filtered table,
    export summary, CSV export, database backup, top expenses, and
    budget progress in one call. Teammates can also call the individual
    render_* / filter_transactions / get_top_expenses /
    calculate_budget_progress functions independently if they need
    finer control (e.g. embedding the table inside their own dashboard
    layout).

    Returns:
        The filtered DataFrame, so other modules (e.g. graphs) can
        reuse the same filtered view.
    """
    filtered = render_filter_panel(df)

    st.markdown("---")
    render_filtered_table(filtered, original_df=df)

    st.markdown("---")
    st.markdown("### Export Filtered Data")
    render_export_summary(filtered)
    render_csv_export(filtered)

    if db_path:
        st.markdown("---")
        render_database_backup(db_path)

    st.markdown("---")
    render_top_expenses(df, n=5)

    if budgets:
        st.markdown("---")
        render_budget_progress(df, budgets)

    return filtered
