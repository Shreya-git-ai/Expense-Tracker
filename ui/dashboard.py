import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_operations import get_all_expenses, get_budget, set_budget


def generate_insights(df: pd.DataFrame) -> list[str]:
    insights = []
    if df.empty:
        return ["Add some expenses to see insights here!"]

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    months = sorted(df['month'].unique())
    current_month = months[-1]
    current_df = df[df['month'] == current_month]

    if len(months) >= 2:
        prev_df = df[df['month'] == months[-2]]
        curr_total = current_df['amount'].sum()
        prev_total = prev_df['amount'].sum()
        if prev_total > 0:
            pct_change = ((curr_total - prev_total) / prev_total) * 100
            direction = "more" if pct_change > 0 else "less"
            insights.append(
                f"📊 You spent **{abs(pct_change):.0f}% {direction}** this month "
                f"(Rs.{curr_total:,.0f}) vs last month (Rs.{prev_total:,.0f})."
            )

    if not current_df.empty:
        cat_totals = current_df.groupby('category')['amount'].sum()
        top_cat = cat_totals.idxmax()
        top_amount = cat_totals.max()
        total = current_df['amount'].sum()
        insights.append(
            f"🏆 **{top_cat}** is your top category this month — "
            f"Rs.{top_amount:,.0f} ({(top_amount/total)*100:.0f}% of total)."
        )
        biggest = current_df.loc[current_df['amount'].idxmax()]
        insights.append(
            f"💥 Largest single expense: Rs.{biggest['amount']:,.0f} "
            f"on {biggest['category']} ({biggest['date'].strftime('%d %b')})."
        )
        days_elapsed = (datetime.now() - current_df['date'].min()).days + 1
        daily_avg = current_df['amount'].sum() / max(days_elapsed, 1)
        insights.append(f"📈 At this pace, projected monthly spend: **Rs.{daily_avg*30:,.0f}**.")

    return insights


def show():
    df = get_all_expenses()

    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        .metric-card {
            background: linear-gradient(145deg, #1e293b, #111827);
            border: 1px solid #2d3b52;
            border-radius: 14px;
            padding: 22px 24px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #6366f1;
        }
        .metric-label {
            color: #94a3b8;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.3px;
            text-transform: uppercase;
            margin-bottom: 8px;
            white-space: nowrap;
        }
        .metric-value {
            color: #f8fafc;
            font-size: 26px;
            font-weight: 700;
        }

        .insight-card {
            background: #1e293b;
            border-left: 4px solid #6366f1;
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 10px;
            color: #f1f5f9;
            font-size: 15px;
        }

        .section-header {
            font-size: 22px;
            font-weight: 700;
            color: #f8fafc;
            margin-top: 8px;
            margin-bottom: 4px;
        }
        .section-sub {
            color: #94a3b8;
            font-size: 14px;
            margin-bottom: 16px;
        }

        hr.section-divider {
            border: none;
            border-top: 1px solid #2d3b52;
            margin: 36px 0 28px 0;
        }

        /* Sidebar polish */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a, #1e293b);
            border-right: 1px solid #2d3b52;
        }
        section[data-testid="stSidebar"] h1 {
            color: #f8fafc;
            font-size: 20px;
        }
        section[data-testid="stSidebar"] label {
            color: #cbd5e1;
            font-size: 15px;
            padding: 8px 0px;
        }
        section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
            gap: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">📊 Expense Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Your spending at a glance</div>', unsafe_allow_html=True)

    if df.empty:
        st.info("No expenses recorded yet. Add your first expense to see insights here.")
        return

    current_month = datetime.now().strftime("%Y-%m")
    budget = get_budget(current_month)
    total_spent = df['amount'].sum()

    _show_metric_cards(df, budget)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    _show_insights(df)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    _show_budget_progress(total_spent, budget, current_month)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        _show_top5_expenses(df)
    with col_b:
        _show_recent_transactions(df)


def _card(col, label, value):
    with col:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
        """, unsafe_allow_html=True)


def _show_metric_cards(df, budget):
    total_spent = df['amount'].sum()
    now = datetime.now()
    days_elapsed = now.day
    avg_daily = total_spent / days_elapsed if days_elapsed else 0
    top_category = df.groupby('category')['amount'].sum().idxmax()

    row1 = st.columns(3, gap="medium")
    _card(row1[0], "💰 Total Expenses", f"Rs.{total_spent:,.2f}")
    if budget is not None:
        remaining = budget - total_spent
        _card(row1[1], "🎯 Monthly Budget", f"Rs.{budget:,.2f}")
        _card(row1[2], "🏦 Remaining", f"Rs.{remaining:,.2f}")
    else:
        _card(row1[1], "🎯 Monthly Budget", "Not set")
        _card(row1[2], "🏦 Remaining", "--")

    st.write("")

    row2 = st.columns(2, gap="medium")
    _card(row2[0], "📅 Avg Daily Spend", f"Rs.{avg_daily:,.2f}")
    _card(row2[1], "🏆 Top Category", top_category)


def _show_insights(df):
    st.markdown('<div class="section-header" style="font-size:19px;">💡 Smart Insights</div>', unsafe_allow_html=True)
    for insight in generate_insights(df):
        st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)


def _show_budget_progress(total_spent, budget, current_month):
    st.markdown('<div class="section-header" style="font-size:19px;">🎯 Monthly Budget</div>', unsafe_allow_html=True)

    if budget is None:
        st.info("No budget set for this month yet.")
    else:
        ratio = total_spent / budget if budget > 0 else 0
        percentage_used = min(ratio, 1.0)

        st.progress(percentage_used)
        st.caption(f"{percentage_used * 100:.0f}% of budget used  -  Rs.{total_spent:,.2f} of Rs.{budget:,.2f}")

        if ratio >= 1.0:
            st.error(f"Budget exceeded by Rs.{total_spent - budget:,.2f}!")
        elif ratio >= 0.9:
            st.warning("Careful - spending close to budget limit!")
        else:
            st.success(f"You're on track - Rs.{budget - total_spent:,.2f} remaining")

    with st.expander("Set or update this month's budget"):
        with st.form("set_budget_form"):
            new_budget = st.number_input(
                "Budget amount (Rs.)",
                min_value=0.0,
                step=100.0,
                value=float(budget) if budget else 0.0
            )
            submitted = st.form_submit_button("Save Budget")
            if submitted:
                if new_budget <= 0:
                    st.error("Budget must be greater than zero.")
                else:
                    set_budget(current_month, new_budget)
                    st.success(f"Budget for {current_month} set to Rs.{new_budget:,.2f}")
                    st.rerun()


def _show_top5_expenses(df):
    st.markdown('<div class="section-header" style="font-size:17px;">🏆 Top 5 Biggest Expenses</div>', unsafe_allow_html=True)
    top5 = df.nlargest(5, 'amount')[['date', 'category', 'amount', 'description']].reset_index(drop=True)
    top5_display = top5.copy()
    top5_display['amount'] = top5_display['amount'].map(lambda x: f"Rs.{x:,.2f}")
    top5_display.columns = ['Date', 'Category', 'Amount', 'Description']
    st.dataframe(top5_display, use_container_width=True, hide_index=True)


def _show_recent_transactions(df):
    st.markdown('<div class="section-header" style="font-size:17px;">🕒 Recent Transactions</div>', unsafe_allow_html=True)
    recent = df.head(10)[['date', 'category', 'description', 'amount']].copy()
    recent['amount'] = recent['amount'].map(lambda x: f"Rs.{x:,.2f}")
    recent.columns = ['Date', 'Category', 'Description', 'Amount']
    st.dataframe(recent, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    show()