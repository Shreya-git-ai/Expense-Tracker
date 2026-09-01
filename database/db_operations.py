
import pandas as pd
from database.db_setup import get_connection


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def add_expense(amount, date, category, description):
    """
    Inserts a new expense row into the database.

    Parameters are expected to already be validated (see utils/validation.py)
    BEFORE this function is called. This function does not re-validate -
    it focuses purely on the database write. Keeping "is this data okay?"
    and "save this data" as separate concerns makes both pieces easier to
    test, reuse, and explain independently.

    date is expected as a string in 'YYYY-MM-DD' format (see db_setup.py
    schema notes for why this format was chosen).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO expenses (amount, date, category, description)
        VALUES (?, ?, ?, ?)
        """,
        (amount, date, category, description),
    )
    # ? placeholders (not f-strings) are used deliberately - this is
    # parameterized query syntax, which prevents SQL injection and is
    # the standard safe way to pass values into a query.
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def get_all_expenses():
    """
    Fetches ALL expenses and returns them as a pandas DataFrame,
    most recent date first.

    Returning a DataFrame here (rather than raw sqlite Row objects) is a
    deliberate choice: every other part of the app - dashboard stats,
    charts, filters - is built on pandas. Converting ONCE at this single
    data-access point avoids repeating pd.DataFrame(...) conversion logic
    all over the codebase.
    """
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    conn.close()
    return df


def get_expense_by_id(expense_id):
    """
    Fetches a single expense row by its id, as a plain Python dict.
    Used by the "Manage Expenses" UI to pre-fill the edit form with
    the currently selected expense's existing values.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    row = cursor.fetchone()
    conn.close()
    # dict(row) converts a sqlite3.Row into a normal dict; return None
    # cleanly if no matching row was found instead of letting the caller
    # deal with a sqlite3.Row that might be None.
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_expense(expense_id, amount, date, category, description):
    """
    Updates an existing expense row identified by expense_id.

    This performs a FULL update (every field is overwritten), not a
    partial patch. That's a deliberate simplicity choice - partial updates
    would need extra logic to detect which fields actually changed, which
    isn't worth the complexity for this project's scope.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE expenses
        SET amount = ?, date = ?, category = ?, description = ?
        WHERE id = ?
        """,
        (amount, date, category, description, expense_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_expense(expense_id):
    """
    Deletes a single expense row by id.

    This is a HARD delete - the row is permanently removed. Soft-delete /
    undo functionality was considered and deliberately left out of MVP
    scope to keep the delete flow simple and bug-free within the time
    budget (see project plan doc, "Undo/Soft Delete" -> OPTIONAL, not built).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# BUDGET OPERATIONS
# ---------------------------------------------------------------------------

def set_budget(month, limit_amount):
    """
    Sets (or updates, if one already exists) the budget limit for a given
    month, in 'YYYY-MM' format.

    Uses INSERT OR REPLACE together with a subquery that looks up any
    existing row's id for this month. This relies on the UNIQUE constraint
    on the `month` column (see db_setup.py): if a budget for this month
    already exists, its id is found and that row is replaced in place;
    if not, the subquery returns NULL and a brand-new row is inserted.
    This avoids writing manual "SELECT to check existence, then decide
    INSERT vs UPDATE" branching logic in Python.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO budget (id, month, limit_amount)
        VALUES (
            (SELECT id FROM budget WHERE month = ?),
            ?, ?
        )
        """,
        (month, month, limit_amount),
    )
    conn.commit()
    conn.close()


def get_budget(month):
    """
    Returns the budget limit (a float) for the given month ('YYYY-MM'),
    or None if no budget has been set for that month yet.

    Returning None (rather than 0) when no budget exists is intentional -
    it lets the dashboard distinguish between "budget explicitly set to 0"
    and "no budget set at all", and show a different message for each.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT limit_amount FROM budget WHERE month = ?", (month,))
    row = cursor.fetchone()
    conn.close()
    return row["limit_amount"] if row else None