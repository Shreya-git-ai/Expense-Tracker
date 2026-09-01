import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from database.db_operations import get_all_expenses


# Columns needed for the charts
REQUIRED_COLUMNS = {"date", "amount", "category"}

# Used to keep days in Monday → Sunday order
DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

CATEGORY_COLORS = {
    "Food": "#4C7CF3",
    "Travel": "#3FC1C9",
    "Shopping": "#FF9F45",
    "Bills": "#F45B69",
    "Entertainment": "#9B6BF2",
    "Other": "#B0B7C3",
}
FALLBACK_COLORS = ["#4C7CF3", "#3FC1C9", "#FF9F45", "#F45B69", "#9B6BF2", "#B0B7C3"]


def _colors_for(labels):
    """Return a color for each label, using CATEGORY_COLORS when known."""
    colors = []
    next_fallback = 0
    for label in labels:
        if label in CATEGORY_COLORS:
            colors.append(CATEGORY_COLORS[label])
        else:
            colors.append(FALLBACK_COLORS[next_fallback % len(FALLBACK_COLORS)])
            next_fallback += 1
    return colors


def show(expenses_df=None):
    """Display all four charts"""

    # Get data from the database if no DataFrame is provided
    if expenses_df is None:
        expenses_df = get_all_expenses()

    st.subheader("📊 Charts & Analytics")

    # Handle empty data
    if expenses_df is None or expenses_df.empty:
        st.info("No expenses yet — add some to see charts here.")
        return

    # Clean the data before plotting
    cleaned_data = _clean_expenses(expenses_df)

    if cleaned_data.empty:
        st.warning("No valid expense data available for the current selection.")
        return

    # Convert dates once so all charts can use them
    cleaned_data["date"] = pd.to_datetime(
        cleaned_data["date"],
        errors="coerce"
    )

    # Remove rows with invalid dates
    cleaned_data = cleaned_data.dropna(subset=["date"])

    # Charts stacked one below another, not side by side
    _show_category_pie(cleaned_data)
    _show_monthly_trend(cleaned_data)
    _show_day_of_week_pattern(cleaned_data)
    _show_top5_categories(cleaned_data)


def _clean_expenses(expenses_df):
    """Clean the data needed for the charts."""

    # Check that all required columns are available
    if not REQUIRED_COLUMNS.issubset(expenses_df.columns):
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    # Work on a copy to protect the original DataFrame
    cleaned_data = expenses_df[
        ["date", "amount", "category"]
    ].copy()

    # Convert dates and amounts to the correct data types
    cleaned_data["date"] = pd.to_datetime(
        cleaned_data["date"],
        errors="coerce"
    )

    cleaned_data["amount"] = pd.to_numeric(
        cleaned_data["amount"],
        errors="coerce"
    )

    # Remove extra spaces from category names
    cleaned_data["category"] = (
        cleaned_data["category"]
        .astype(str)
        .str.strip()
    )

    # Remove rows with invalid dates or amounts
    cleaned_data = cleaned_data.dropna(
        subset=["date", "amount"]
    )

    # Remove empty categories
    cleaned_data = cleaned_data[
        cleaned_data["category"].ne("")
        & cleaned_data["category"].str.lower().ne("nan")
    ]

    # Expenses should not have negative amounts
    cleaned_data = cleaned_data[
        cleaned_data["amount"] >= 0
    ]

    return cleaned_data


def _show_category_pie(expenses_df):
    """Display spending distribution by category."""

    st.markdown("**Spending by Category**")

    # Find total spending for each category
    category_totals = (
        expenses_df
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    colors = _colors_for(category_totals.index)

    figure, axis = plt.subplots()

    # Pie chart with a hole in the centre = donut chart
    wedges, _texts, _autotexts = axis.pie(
        category_totals.values,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops=dict(width=0.4),
        colors=colors,
        textprops=dict(color="white")
    )

    axis.set_ylabel("")
    axis.set_title("Category-wise Spending")

    # Side legend instead of labels crowding the donut, like the reference image
    axis.legend(
        wedges,
        category_totals.index,
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
    )

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def _show_monthly_trend(expenses_df):
    """Display total spending for each month."""

    st.markdown("**Monthly Spending Trend**")

    monthly_data = expenses_df.copy()

    # Convert each date into its month
    monthly_data["month"] = (
        monthly_data["date"]
        .dt.to_period("M")
    )

    # Calculate total spending for each month
    monthly_totals = (
        monthly_data
        .groupby("month")["amount"]
        .sum()
        .sort_index()
    )

    # Convert months into readable labels
    monthly_totals.index = monthly_totals.index.astype(str)

    figure, axis = plt.subplots()

    # Bar chart makes monthly comparison easy
    monthly_totals.plot(
        kind="bar",
        ax=axis,
        color=CATEGORY_COLORS["Food"]
    )

    axis.set_xlabel("Month")
    axis.set_ylabel("Amount (₹)")
    axis.set_title("Monthly Spending Trend")

    # Rotate labels so they don't overlap
    plt.setp(
        axis.get_xticklabels(),
        rotation=45,
        ha="right"
    )

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def _show_day_of_week_pattern(expenses_df):
    """Display spending for each day of the week."""

    st.markdown("**Spending by Day of Week**")

    day_data = expenses_df.copy()

    # Get the day name from each date
    day_data["day"] = (
        day_data["date"]
        .dt.day_name()
    )

    # Calculate total spending for each day
    day_totals = (
        day_data
        .groupby("day")["amount"]
        .sum()
        .reindex(DAY_ORDER, fill_value=0)
    )

    figure, axis = plt.subplots()

    day_totals.plot(
        kind="bar",
        ax=axis,
        color=CATEGORY_COLORS["Travel"]
    )

    axis.set_xlabel("Day of Week")
    axis.set_ylabel("Amount (₹)")
    axis.set_title("Spending by Day of Week")

    # Rotate labels for readability
    plt.setp(
        axis.get_xticklabels(),
        rotation=45,
        ha="right"
    )

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def _show_top5_categories(expenses_df):
    """Display the five highest-spending categories."""

    st.markdown("**Top 5 Categories**")

    # Calculate total spending for every category
    category_totals = (
        expenses_df
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    figure, axis = plt.subplots()

    # Sort ascending so the highest value appears at the top
    sorted_totals = category_totals.sort_values()
    colors = _colors_for(sorted_totals.index)

    sorted_totals.plot(
        kind="barh",
        ax=axis,
        color=colors
    )

    axis.set_xlabel("Amount (₹)")
    axis.set_ylabel("Category")
    axis.set_title("Top 5 Categories")

    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


if __name__ == "__main__":
    """
    Creates sample data for testing the charts independently.
    """

    import numpy as np

    # Fixed seed gives the same sample data every time
    random_generator = np.random.default_rng(42)

    expense_categories = [
        "Food",
        "Transport",
        "Shopping",
        "Bills",
        "Entertainment"
    ]

    number_of_expenses = 60

    test_expenses = pd.DataFrame(
        {
            # Generate dates across three months
            "date": pd.to_datetime(
                random_generator.choice(
                    pd.date_range(
                        "2026-06-01",
                        "2026-08-31"
                    ),
                    size=number_of_expenses
                )
            ).astype(str),

            # Generate sample expense amounts
            "amount": random_generator.integers(
                50,
                3000,
                size=number_of_expenses
            ),

            # Assign each expense a category
            "category": random_generator.choice(
                expense_categories,
                size=number_of_expenses
            ),
        }
    )

    st.title("Expense Tracker — Charts Test")

    # Display the charts using the same function as the real app
    show(test_expenses)