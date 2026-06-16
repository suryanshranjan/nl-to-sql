"""
sql_validator.py
----------------
The safety gate. An LLM can be tricked (or can simply make a mistake) and
produce a destructive query. Before ANY generated SQL touches the database,
it must pass through `validate_sql`.

Our rule is deliberately strict and easy to reason about:
    "Allow exactly one read-only SELECT statement. Block everything else."

This is a guardrail, not a full SQL parser. Keeping it simple makes it easy
to audit and hard to get wrong.
"""

import re

# Any statement containing one of these keywords is rejected outright.
# These cover data destruction (DROP/DELETE/TRUNCATE), data mutation
# (UPDATE/INSERT), and structural changes (ALTER/CREATE).
BLOCKED_KEYWORDS = [
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "MERGE",
    "REPLACE",
    "CALL",
    "EXEC",
    "EXECUTE",
]


def clean_sql(sql: str) -> str:
    """Strip whitespace, surrounding code fences, and a trailing semicolon.

    LLMs love to wrap answers in ```sql ... ``` fences, so we remove those
    too and return a bare statement ready for inspection / execution.
    """
    cleaned = sql.strip()

    # Remove ```sql ... ``` or ``` ... ``` markdown fences if present.
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned).strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    # Drop a single trailing semicolon so the checks below see a clean string.
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    return cleaned


def validate_sql(sql: str) -> tuple[bool, str]:
    """Check that `sql` is a single, safe, read-only SELECT statement.

    Returns a (is_valid, message) pair:
        (True,  "OK")                     -> safe to run
        (False, "<reason it was blocked>") -> do NOT run
    """
    cleaned = clean_sql(sql)

    if not cleaned:
        return False, "The query is empty."

    upper = cleaned.upper()

    # 1) Must START with SELECT (or a WITH ... SELECT common table expression).
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "Only SELECT queries are allowed."

    # 2) Reject multiple statements (e.g. "SELECT 1; DROP TABLE users").
    #    After clean_sql there should be no internal semicolons left.
    if ";" in cleaned:
        return False, "Multiple SQL statements are not allowed."

    # 3) Reject any blocked keyword. We use word boundaries (\b) so that a
    #    column named "updated_at" does not trip the "UPDATE" rule.
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            return False, f"Blocked keyword detected: {keyword}"

    return True, "OK"
