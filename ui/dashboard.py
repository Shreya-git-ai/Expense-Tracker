import streamlit as st
import pandas as pd


def show():
    df = get_expenses()
    budget_limit = get_budget_for_month()

    st.header("📊 Dashboard")

    # --- Summary metrics ---
    if df.empty:
        st.info("No expenses recorded yet.")
        return

    total = df['amount'].sum()
    avg = df['amount'].mean()
    highest = df['amount'].max()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Spend", f"₹{total:,.2f}")
    col2.metric("Average Spend", f"₹{avg:,.2f}")
    col3.metric("Highest Expense", f"₹{highest:,.2f}")

    # --- Budget progress ---
    st.subheader("Monthly Budget")
    if budget_limit and budget_limit > 0:
        spent_pct = min(total / budget_limit, 1.0)
        st.progress(spent_pct)
        remaining = budget_limit - total
        if remaining >= 0:
            st.write(f"₹{total:,.2f} / ₹{budget_limit:,.2f} spent — ₹{remaining:,.2f} remaining")
        else:
            st.write(f"₹{total:,.2f} / ₹{budget_limit:,.2f} spent — over budget by ₹{-remaining:,.2f}")
    else:
        st.warning("No budget set for this month.")

    # --- Top 5 biggest expenses ---
    st.subheader("Top 5 Biggest Expenses")
    top5 = df.nlargest(5, 'amount')[['date', 'category', 'amount', 'description']]
    st.table(top5)


# ---------------------------------------------------------
# MOCK DATA — remove once Member A's db_operations.py is ready
# ---------------------------------------------------------
def get_expenses():
    return pd.DataFrame({
        'date': ['2025-06-01', '2025-06-05', '2025-06-10', '2025-06-15'],
        'category': ['Food', 'Travel', 'Rent', 'Shopping'],
        'amount': [500, 1200, 8000, 2500],
        'description': ['Lunch', 'Cab', 'June rent', 'Clothes']
    })


def get_budget_for_month():
    return 10000
if __name__ == "__main__":
    show()
