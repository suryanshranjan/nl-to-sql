"""
db.py
-----
Owns the single SQLAlchemy database connection (the "engine") and exposes
small helper functions the rest of the app uses to talk to PostgreSQL.

Why a single shared engine?
    SQLAlchemy's Engine manages a pool of connections for you. We create it
    once at import time and reuse it everywhere, instead of opening a brand
    new connection on every query.
"""

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Load variables from the .env file into the process environment.
load_dotenv()


def _build_database_url() -> str:
    """Assemble a PostgreSQL connection URL from environment variables.

    Format: postgresql+psycopg2://user:password@host:port/database
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "nl_to_sql_demo")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


# Create the engine exactly once. `pool_pre_ping` quietly checks that a
# pooled connection is still alive before handing it to us, which avoids
# "connection already closed" errors after the DB has been idle.
engine: Engine = create_engine(_build_database_url(), pool_pre_ping=True)


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine."""
    return engine


def run_query(sql: str) -> pd.DataFrame:
    """Execute a (read-only) SQL string and return the result as a DataFrame.

    NOTE: This function does NOT validate the SQL. Validation is the job of
    sql_validator.py and must happen BEFORE this is ever called.
    """
    with engine.connect() as connection:
        result = connection.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
    return pd.DataFrame(rows, columns=columns)


def test_connection() -> bool:
    """Return True if we can successfully reach the database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
