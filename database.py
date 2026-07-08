"""
database.py
-----------
Small SQLite wrapper that acts as our persistent "inventory array".

Using SQLite (instead of a plain Python list) means the data survives
server restarts, but it is still exposed to the rest of the app as
simple list-of-dict "rows" so it behaves like an in-memory array of
inventory items.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")


def get_connection():
    """Return a new SQLite connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the items table if it does not already exist."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            barcode     TEXT,
            brand       TEXT,
            category    TEXT,
            quantity    INTEGER NOT NULL DEFAULT 0,
            price       REAL NOT NULL DEFAULT 0.0,
            description TEXT,
            image_url   TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def row_to_dict(row):
    return dict(row) if row is not None else None


def reset_db():
    """Utility used by the test-suite to guarantee a clean database."""
    conn = get_connection()
    conn.execute("DROP TABLE IF EXISTS items")
    conn.commit()
    conn.close()
    init_db()
