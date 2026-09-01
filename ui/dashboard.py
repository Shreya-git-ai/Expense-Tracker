import streamlit as st
import pandas as pd


def show():
    df = get_expenses()
    budget_limit = get_budget_for_month()

    # --- Custom styling ---
    st.markdown("""
        <style>
        .main-title {
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }
        .subtitle {
            color: #94a3b8;
            font-size: 15px;
            margin-bottom: 24px;
        }
        .metric-card {
            background: linear-gradient(145deg, #1e293b, #111827);
            border: 1px solid #2d3b52;
            border-radius: 16px;
            padding: 22px 20px;
            text-align: left;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            transition: transform 0.15s ease;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            border-color: #38bdf8;
        }
        .metric-icon {
            font-size: 22px;
            margin-bottom: 8px;
        }
        .metric-label {
            color: #94a3b8;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 4px;
        }
        .metric-value {
            color: #f8fafc;
            font-size: 26px;
            font-weight: 700;
        }
        .budget-card {
            background: linear-gradient(145deg, #1e293b, #111827);
            border: 1px solid #2d3b52;
            border-radius: 16px;
            padding: 24px 28px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }
        .budget-status-ok {
            color: #4ade80;
            font-weight: 700;
            font-size: 16px;
        }
        .budget-status-over {
            color: #f87171;
            font-weight: 700;
            font-size: 16px;
        }
        .section-title {
            font-size: 19px;
            font-weight: 700;
            margin-top: 4px;
            margin-bottom: 14px;
            color: #f8fafc;
        }
        [data-testid="stProgress"] > div > div {
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">📊 Expense Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Track, analyze, and stay on budget</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("No expenses recorded yet.")
        return

    total = df['amount'].sum()
    avg = df['amount'].mean()
    highest = df['amount'].max()

    # --- Metric cards ---
    col1, col2, col3 = st.columns(3)
    cards = [
        (col1, "💰", "Total Spend", f"₹{total:,.0f}"),
        (col2, "📊", "Average Spend", f"₹{avg:,.0f}"),
        (col3, "🔺", "Highest Expense", f"₹{highest:,.0f}"),
    ]
    for col, icon, label, value in cards:
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
            """, unsafe_allow_html=True)

    st.write("")

    # --- Budget card ---
    st.markdown('<div class="section-title">🎯 Monthly Budget</div>', unsafe_allow_html=True)
    if budget_limit and budget_limit > 0:
        spent_pct = min(total / budget_limit, 1.0)
        remaining = budget_limit - total
        status_class = "budget-status-ok" if remaining >= 0 else "budget-status-over"
        status_text = (
            f"✅ ₹{remaining:,.2f} remaining"
            if remaining >= 0
            else f"⚠️ Over budget by ₹{-remaining:,.2f}"
        )
        st.markdown(f"""
            <div class="budget-card">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <span style="color:#cbd5e1;">₹{total:,.2f} of ₹{budget_limit:,.2f}</span>
                    <span class="{status_class}">{status_text}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.progress(spent_pct)
    else:
        st.warning("No budget set for this month.")

    st.write("")

    # --- Top 5 biggest expenses ---
    st.markdown('<div class="section-title">🏆 Top 5 Biggest Expenses</div>', unsafe_allow_html=True)
    icons = {"Food": "🍔", "Travel": "🚗", "Rent": "🏠", "Shopping": "🛍️"}
    top5 = df.nlargest(5, 'amount')[['date', 'category', 'amount', 'description']].reset_index(drop=True)
    top5_display = top5.copy()
    top5_display['category'] = top5_display['category'].map(lambda c: f"{icons.get(c, '📌')} {c}")
    top5_display['amount'] = top5_display['amount'].map(lambda x: f"₹{x:,.2f}")
    st.dataframe(top5_display, width='stretch', hide_index=True)


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