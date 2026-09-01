

import sqlite3
import os

# Path to the SQLite database file. Keeping it inside a data/ folder keeps
# the project root clean and makes it obvious this file is generated output,
# not source code (it's also what gets .gitignored).
DB_FOLDER = "data"
DB_PATH = os.path.join(DB_FOLDER, "expenses.db")


def get_connection():
    """
    Creates and returns a NEW SQLite connection.

    We deliberately open a fresh connection per call rather than keeping
    one global connection alive for the whole app. Streamlit can re-run
    scripts and execute in ways that don't play well with a single shared
    connection across reruns, so "open -> use -> close" per operation is
    the safer, simpler pattern here.
    """
    # Ensure the data/ folder exists before SQLite tries to create the
    # .db file inside it - avoids a "no such directory" error on first run.
    os.makedirs(DB_FOLDER, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # row_factory = sqlite3.Row makes query results behave like dictionaries
    # (row["column_name"]) instead of plain positional tuples (row[0], row[1]...).
    # This makes the code in db_operations.py far more readable, and converts
    # cleanly into pandas DataFrames.
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the expenses and budget tables if they don't already exist.

    CREATE TABLE IF NOT EXISTS is idempotent - safe to call this function
    every single time the app starts up, without wiping or duplicating
    existing data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # --- expenses table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- budget table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL UNIQUE,
            limit_amount REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()