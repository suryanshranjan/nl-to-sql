"""
llm.py
------
Talks to the LLM. We use the official `openai` client, which also works with
ANY OpenAI-compatible endpoint (Ollama, LM Studio, Groq, Together, ...) just
by changing OPENAI_BASE_URL in the .env file.

The single job of this module: take a schema description + a user question,
and return a SQL string.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Create the client once. base_url lets us point at any compatible server.
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# The system prompt sets the rules. The {schema} placeholder is filled with
# the live schema context so the model knows the real table/column names.
PROMPT_TEMPLATE = """You are an expert PostgreSQL assistant.
Your job is to translate a user's natural language question into a single,
valid, READ-ONLY PostgreSQL SELECT query.

Rules you MUST follow:
1. Use ONLY the tables and columns described in the schema below.
2. Generate exactly ONE SELECT statement. Never use DROP, DELETE, UPDATE,
   INSERT, ALTER, TRUNCATE, or any statement that changes data.
3. Return ONLY the raw SQL query. No explanations, no markdown, no comments.
4. Prefer clear, standard PostgreSQL syntax.

Database schema:
{schema}
"""


def generate_sql(schema_text: str, question: str) -> str:
    """Ask the LLM to convert a natural-language question into SQL.

    `schema_text` comes from schema_loader.get_schema_text().
    Returns the model's raw SQL response (still needs validation).
    """
    system_prompt = PROMPT_TEMPLATE.format(schema=schema_text)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        # Low temperature -> more deterministic, less "creative" SQL.
        temperature=0,
    )

    return response.choices[0].message.content.strip()
