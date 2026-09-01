"""
utils/validation.py

All input validation logic for expenses, kept in one place so:
  - it can be explained/tested independently of the UI or the database
  - db_operations.py stays focused purely on persistence, not business rules
  - the UI layer calls these functions BEFORE hitting the database, so bad
    data is rejected immediately with clear feedback, instead of silently
    entering (or crashing) the database layer
"""

from datetime import date

# Master list of allowed categories, defined ONCE here. add_expense.py,
# manage_expense.py, and categorizer.py (if built) should all import this
# same list rather than each hard-coding their own copy - this avoids the
# categories going out of sync across files.
VALID_CATEGORIES = [
    "Food", "Transport", "Rent", "Shopping",
    "Bills", "Entertainment", "Other"
]


def validate_amount(amount):
    """
    An expense amount must be a positive number greater than zero.
    A 0 or negative expense doesn't make sense in this app's context.

    Returns: (is_valid: bool, error_message: str or None)
    """
    if amount is None:
        return False, "Amount is required."
    if amount <= 0:
        return False, "Amount must be greater than 0."
    return True, None


def validate_date(expense_date):
    """
    An expense date cannot be in the future - you can't log money you
    haven't spent yet. Streamlit's st.date_input already returns a Python
    date object directly, so no string parsing is needed here.

    Returns: (is_valid: bool, error_message: str or None)
    """
    if expense_date is None:
        return False, "Date is required."
    if expense_date > date.today():
        return False, "Date cannot be in the future."
    return True, None


def validate_description(description):
    """
    Description must contain actual text, not be empty or just whitespace.
    .strip() specifically handles the case where a user types only spaces
    and hits submit, which would otherwise slip past a simple != "" check.

    Returns: (is_valid: bool, error_message: str or None)
    """
    if description is None or description.strip() == "":
        return False, "Description cannot be empty."
    return True, None


def validate_category(category):
    """
    Category must be one of the predefined VALID_CATEGORIES. This is an
    application-level constraint (SQLite itself has no ENUM type), which
    is exactly why this check lives here rather than in the database schema.

    Returns: (is_valid: bool, error_message: str or None)
    """
    if category not in VALID_CATEGORIES:
        return False, f"Category must be one of: {', '.join(VALID_CATEGORIES)}."
    return True, None


def validate_expense(amount, expense_date, category, description):
    """
    Runs ALL individual validation checks together for one expense entry.

    This is the ONE function the UI layer actually calls - it internally
    calls each individual validate_*() function and collects every error
    into a single list, so the user sees ALL problems with their input at
    once (rather than fixing one error, resubmitting, and hitting the next).

    Returns: (is_valid: bool, errors: list[str])
        is_valid is True only if there are zero errors.
    """
    errors = []

    is_valid, msg = validate_amount(amount)
    if not is_valid:
        errors.append(msg)

    is_valid, msg = validate_date(expense_date)
    if not is_valid:
        errors.append(msg)

    is_valid, msg = validate_category(category)
    if not is_valid:
        errors.append(msg)

    is_valid, msg = validate_description(description)
    if not is_valid:
        errors.append(msg)

    return (len(errors) == 0), errors