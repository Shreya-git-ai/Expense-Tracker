# 💰 Smart Expense Tracker

A Python-based personal expense tracker with graphical analytics, built as
a college project (B.Tech CSE).

Track daily expenses, set monthly budgets, and visualize spending patterns
through an interactive dashboard — built entirely with Python, Streamlit,
SQLite, and Pandas.

---

## 📌 Features

- **Add / Edit / Delete Expenses** — full CRUD with input validation
- **Category-based tracking** — Food, Transport, Rent, Shopping, Bills,
  Entertainment, Other
- **Dashboard** — total spend, average daily spend, highest spending
  category, budget progress
- **Monthly Budget** — set a budget per month, track remaining balance
- **Graphical Analytics**
  - Category-wise spending (donut chart)
  - Monthly spending trend (bar chart)
  - Spending by day of week (bar chart)
  - Top 5 spending categories (horizontal bar chart)
- **Filters** — filter expenses by date range and/or category
- **CSV Export** — export the currently filtered view
- **Input Validation** — rejects negative amounts, empty descriptions,
  and future-dated entries before they ever reach the database

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.10+ | Core requirement of the project |
| UI | Streamlit | Fast to build, pure-Python UI, no separate frontend needed |
| Database | SQLite (`sqlite3`) | File-based, zero-config, perfect for a single-user local app |
| Data handling | Pandas | Grouping, aggregation, filtering — all built on DataFrames |
| Visualization | Matplotlib | Integrates directly with Pandas; simple to explain line-by-line |

No external APIs, no authentication, no ML/AI — every feature is rule-based
and fully explainable, by design.

---

## 📂 Project Structure

```
expense-tracker/
│
├── app.py                  # Main entry point — navigation/routing only
├── requirements.txt
├── .gitignore
│
├── database/
│   ├── db_setup.py         # DB connection + table creation (schema lives here)
│   └── db_operations.py    # All CRUD + budget operations
│
├── ui/
│   ├── add_expense.py      # Add expense form
│   ├── manage_expense.py   # Edit/delete UI
│   ├── dashboard.py        # Metric cards, budget progress, recent transactions
│   ├── charts.py           # All 4 analytics charts
│   └── filters_export.py   # Filters + CSV export + DB backup
│
├── utils/
│   ├── validation.py       # Input validation rules
│   └── categorizer.py      # (optional) rule-based category auto-suggestion
│
└── data/
    └── expenses.db         # SQLite database file (auto-created, gitignored)
```

Each page in `ui/` exposes a single `show()` function. `app.py` only
imports and routes between them — no business logic lives in `app.py`
itself.

---

## 🚀 Setup & Run

### 1. Clone the repository
```bash
git clone <repo-url>
cd expense-tracker
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`. The SQLite database
(`data/expenses.db`) is created automatically on first run — no manual
setup needed.

---

## 🗄️ Database Schema

**`expenses` table**

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PRIMARY KEY AUTOINCREMENT | Unique row identifier |
| amount | REAL NOT NULL | Expense amount |
| date | TEXT NOT NULL | Stored as ISO format `'YYYY-MM-DD'` |
| category | TEXT NOT NULL | One of the predefined categories |
| description | TEXT | Optional note |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Auto-stamped on insert |

**`budget` table**

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PRIMARY KEY AUTOINCREMENT | Unique row identifier |
| month | TEXT NOT NULL UNIQUE | Format `'YYYY-MM'`, one budget per month |
| limit_amount | REAL NOT NULL | Budget ceiling for that month |

> Full reasoning behind every schema decision (why SQLite, why dates are
> stored as TEXT, why categories aren't a separate normalized table, etc.)
> is documented as comments directly in `database/db_setup.py`.

---

## 👥 Team & Work Division

| Member | Responsibility | Files |
|---|---|---|
| **A** | Database & Core Backend | `database/db_setup.py`, `database/db_operations.py`, `ui/add_expense.py`, `ui/manage_expense.py`, `utils/validation.py` |
| **B** | Dashboard & Budget | `ui/dashboard.py` |
| **C** | Charts & Analytics | `ui/charts.py` |
| **D** | Filters, Export & Extras | `ui/filters_export.py`, `utils/categorizer.py` |

Each member owns a complete vertical slice — database access up through
UI — so merge conflicts stay minimal and everyone can independently
explain their portion during viva.

---

## 🎯 Design Principles

This project was deliberately scoped to be **fully explainable and
demo-ready within a fixed development window**, rather than
feature-maximal. Key trade-offs made on purpose:

- **Rule-based logic over ML/AI** — e.g. category suggestions (if built)
  use a keyword dictionary, not a trained model, so behavior is fully
  transparent.
- **Matplotlib over Plotly** — less flashy, but every chart line is easy
  to walk through in viva.
- **No authentication / multi-user support** — out of scope for a
  single-team local demo.
- **Hard delete, no undo** — kept simple and bug-free within the time
  budget rather than adding session-state complexity.

---

## 📄 License

Built for academic/college project purposes.