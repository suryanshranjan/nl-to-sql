"""
app.py
------
The Streamlit user interface and the "glue" that wires every module together.

End-to-end flow when the user clicks "Generate & Run":
    1. schema_loader  -> read the live database schema
    2. llm            -> send schema + question, get SQL back
    3. sql_validator  -> make sure the SQL is a safe, read-only SELECT
    4. db             -> execute the validated SQL
    5. streamlit      -> show the SQL and the results table
"""

import streamlit as st

import db
import llm
import schema_loader
import sql_validator

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(page_title="NL → SQL", page_icon="🧮", layout="wide")
st.title("🧮 Natural Language → SQL")
st.caption(
    "Ask a question in plain English. The app reads your database schema, "
    "asks an LLM to write SQL, checks it is read-only, then runs it."
)

# ----------------------------------------------------------------------
# Sidebar: connection status, schema preview, and example questions
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("Status")

    if db.test_connection():
        st.success("Connected to PostgreSQL")
    else:
        st.error("Cannot reach PostgreSQL. Check your .env settings.")

    st.divider()
    st.subheader("Example questions")
    EXAMPLES = [
        "Show total sales",
        "Show sales by city",
        "Top 5 customers by revenue",
        "Orders placed this month",
    ]
    for example in EXAMPLES:
        st.markdown(f"- {example}")

    st.divider()
    with st.expander("View database schema"):
        try:
            st.code(schema_loader.get_schema_text(), language="text")
        except Exception as exc:  # pragma: no cover - UI safety net
            st.warning(f"Could not load schema: {exc}")

# ----------------------------------------------------------------------
# Main input
# ----------------------------------------------------------------------
question = st.text_input(
    "Your question",
    placeholder="e.g. Top 5 customers by revenue",
)

run_clicked = st.button("Generate & Run", type="primary")

if run_clicked:
    if not question.strip():
        st.warning("Please type a question first.")
        st.stop()

    # --- Step 1: load schema ------------------------------------------------
    try:
        schema_text = schema_loader.get_schema_text()
    except Exception as exc:
        st.error(f"Failed to read database schema: {exc}")
        st.stop()

    # --- Step 2: ask the LLM for SQL ---------------------------------------
    with st.spinner("Asking the LLM to write SQL..."):
        try:
            raw_sql = llm.generate_sql(schema_text, question)
        except Exception as exc:
            st.error(f"LLM request failed: {exc}")
            st.stop()

    cleaned_sql = sql_validator.clean_sql(raw_sql)

    # --- Step 3: show the SQL before running it ----------------------------
    st.subheader("Generated SQL")
    st.code(cleaned_sql, language="sql")

    # --- Step 4: validate (the safety gate) --------------------------------
    is_valid, message = sql_validator.validate_sql(cleaned_sql)
    if not is_valid:
        st.error(f"Query blocked by safety check: {message}")
        st.stop()

    # --- Step 5: execute and display ---------------------------------------
    with st.spinner("Running query..."):
        try:
            results = db.run_query(cleaned_sql)
        except Exception as exc:
            st.error(f"Query execution failed: {exc}")
            st.stop()

    st.subheader("Results")
    if results.empty:
        st.info("The query ran successfully but returned no rows.")
    else:
        st.dataframe(results, use_container_width=True)
        st.caption(f"{len(results)} row(s) returned.")
