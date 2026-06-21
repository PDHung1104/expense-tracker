import sqlite3
import os
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "expenses.db")

DEFAULT_CATEGORIES = ["grocery", "medicine", "transportation", "miscellaneous"]


def _ensure_data_dir():
    """Create the data directory if it doesn't exist.

    This is called before any database operation to guarantee the parent
    directory for the SQLite file exists, avoiding "unable to open database"
    errors on first run.
    """
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_db():
    """Yield a sqlite3 connection with automatic commit/rollback and cleanup.

    Every database operation in the app uses this context manager so that
    connection handling (opening, committing on success, rolling back on
    failure, closing) is centralized in one place. Row objects are enabled
    so query results can be accessed by column name (row["name"]) rather
    than by numeric index.
    """
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables and seed default categories. Safe to call repeatedly.

    Called once on application startup (via the FastAPI lifespan handler).
    Uses IF NOT EXISTS so subsequent calls are no-ops, and INSERT OR IGNORE
    so the default category seed doesn't duplicate on restart.
    """
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_default INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT DEFAULT '',
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # Seed default categories (ignore if they already exist)
    for name in DEFAULT_CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name, is_default) VALUES (?, 1)",
            (name,),
        )

    conn.commit()
    conn.close()
