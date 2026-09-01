import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_operations import get_all_expenses, get_budget


def show():
    df = get_all_expenses()

    st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(145deg, #1e293b, #111827);
            border: 1px solid #2d3b52;
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        .metric-label {
            color: #94a3b8;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 6px;
            white-space: nowrap;
        }
        .metric-value {
            color: #f8fafc;
            font-size: 24px;
            font-weight: 700;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📊 Expense Dashboard")
    st.caption("Your spending at a glance")

    if df.empty:
        st.info("No expenses recorded yet. Add your first expense to see insights here.")
        return

    current_month = datetime.now().strftime("%Y-%m")
    budget = get_budget(current_month)
    total_spent = df['amount'].sum()

    _show_metric_cards(df, budget)
    st.write("")
    _show_budget_progress(total_spent, budget)
    st.write("")
    _show_top5_expenses(df)
    st.write("")
    _show_recent_transactions(df)


def _card(col, icon, label, value):
    with col:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{icon} {label}</div>
                <div class="metric-value">{value}</div>
            </div>
        """, unsafe_allow_html=True)


def _show_metric_cards(df, budget):
    total_spent = df['amount'].sum()
    now = datetime.now()
    days_elapsed = now.day
    avg_daily = total_spent / days_elapsed if days_elapsed else 0
    top_category = df.groupby('category')['amount'].sum().idxmax()

    # Row 1 — 3 wide cards
    row1 = st.columns(3)
    _card(row1[0], "💰", "Total Expenses", f"₹{total_spent:,.2f}")
    if budget is not None:
        remaining = budget - total_spent
        _card(row1[1], "🎯", "Monthly Budget", f"₹{budget:,.2f}")
        _card(row1[2], "🏦", "Remaining", f"₹{remaining:,.2f}")
    else:
        _card(row1[1], "🎯", "Monthly Budget", "Not set")
        _card(row1[2], "🏦", "Remaining", "—")

    st.write("")

    # Row 2 — 2 wide cards
    row2 = st.columns(2)
    _card(row2[0], "📅", "Avg Daily Spend", f"₹{avg_daily:,.2f}")
    _card(row2[1], "🏆", "Top Category", top_category)


def _show_budget_progress(total_spent, budget):
    st.markdown("#### 🎯 Monthly Budget")

    if budget is None:
        st.info("No budget set for this month.")
        return

    ratio = total_spent / budget if budget > 0 else 0
    percentage_used = min(ratio, 1.0)

    st.progress(percentage_used)
    st.caption(f"{percentage_used * 100:.0f}% of budget used  •  ₹{total_spent:,.2f} of ₹{budget:,.2f}")

    if ratio >= 1.0:
        st.error(f"⚠️ Budget exceeded by ₹{total_spent - budget:,.2f}!")
    elif ratio >= 0.9:
        st.warning("⚠️ Careful — spending close to budget limit!")
    else:
        st.success(f"✅ You're on track — ₹{budget - total_spent:,.2f} remaining")


def _show_top5_expenses(df):
    st.markdown("#### 🏆 Top 5 Biggest Expenses")
    icons = {"Food": "🍔", "Travel": "🚗", "Rent": "🏠", "Shopping": "🛍️"}
    top5 = df.nlargest(5, 'amount')[['date', 'category', 'amount', 'description']].reset_index(drop=True)
    top5_display = top5.copy()
    top5_display['category'] = top5_display['category'].map(lambda c: f"{icons.get(c, '📌')} {c}")
    top5_display['amount'] = top5_display['amount'].map(lambda x: f"₹{x:,.2f}")
    top5_display.columns = ['Date', 'Category', 'Amount', 'Description']
    st.dataframe(top5_display, use_container_width=True, hide_index=True)


def _show_recent_transactions(df):
    st.markdown("#### 🕒 Recent Transactions")
    recent = df.head(10)[['date', 'category', 'description', 'amount']].copy()
    recent['amount'] = recent['amount'].map(lambda x: f"₹{x:,.2f}")
    recent.columns = ['Date', 'Category', 'Description', 'Amount']
    st.dataframe(recent, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    show()