"""
schema_loader.py
----------------
Reads the live structure of the database (tables + columns) and turns it into
a short, human-readable text block.

That text block is the "schema context" we hand to the LLM. The model cannot
see your database, so we must describe it. Without this, the LLM would only be
guessing at table and column names.
"""

from sqlalchemy import inspect

from db import get_engine


def get_schema_text() -> str:
    """Return a compact text description of every table and its columns.

    Example output:
        Table: customers
          - customer_id (INTEGER)
          - customer_name (VARCHAR)
          - city (VARCHAR)

        Table: orders
          - order_id (INTEGER)
          - customer_id (INTEGER)
          - amount (NUMERIC)
          - order_date (DATE)
    """
    inspector = inspect(get_engine())
    lines: list[str] = []

    # We only describe the default "public" schema, which is where our demo
    # tables live. `get_table_names` asks PostgreSQL for the real list.
    for table_name in inspector.get_table_names(schema="public"):
        lines.append(f"Table: {table_name}")
        for column in inspector.get_columns(table_name, schema="public"):
            col_name = column["name"]
            col_type = str(column["type"])
            lines.append(f"  - {col_name} ({col_type})")
        lines.append("")  # blank line between tables for readability

    return "\n".join(lines).strip()


if __name__ == "__main__":
    # Handy for a quick manual check: `python schema_loader.py`
    print(get_schema_text())
