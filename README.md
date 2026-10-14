# 🧮 Natural Language → SQL

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-SQLAlchemy-4169E1?logo=postgresql&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-OpenAI--compatible-412991?logo=openai&logoColor=white)

A beginner-friendly app that lets you **ask questions about your database in
plain English**. It reads your PostgreSQL schema, asks an LLM to write the SQL,
checks that the SQL is safe (read-only), runs it, and shows the results in a
table — all in a small Streamlit web app.

**Features**
- 💬 Ask questions in plain English; get back SQL and a results table
- 🧠 Schema-aware prompting: reads live tables and columns, so the LLM uses real names
- 🛡️ Read-only guardrail: blocks `DROP`, `DELETE`, `UPDATE`, stacked statements and more
- 🔌 Works with any OpenAI-compatible LLM (OpenAI, Ollama, LM Studio, Groq, …)
- 👀 Shows the generated SQL before it runs

---

## 1. What it does (in one picture)

```
┌──────────────┐
│  You type a  │   "Top 5 customers by revenue"
│  question    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐     reads tables + columns
│  schema_loader   │ ─────────────────────────────┐
└──────┬───────────┘                               │
       │ schema text                               │
       ▼                                           │
┌──────────────────┐   schema context + question   │
│       llm        │ ◄─────────────────────────────┘
│  (OpenAI-compat) │
└──────┬───────────┘
       │ generated SQL
       ▼
┌──────────────────┐   blocks DROP/DELETE/UPDATE/…
│  sql_validator   │   allows a single SELECT only
└──────┬───────────┘
       │ safe SQL
       ▼
┌──────────────────┐
│        db        │   executes against PostgreSQL
└──────┬───────────┘
       │ rows
       ▼
┌──────────────────┐
│    Streamlit     │   shows SQL + results table
└──────────────────┘
```

---

## 2. Project structure

```
NL to SQL/
├── app.py             # Streamlit UI + glue that wires everything together
├── db.py              # PostgreSQL connection (SQLAlchemy engine) + query runner
├── schema_loader.py   # Reads tables/columns -> schema text for the LLM
├── sql_validator.py   # Safety gate: only a single read-only SELECT is allowed
├── llm.py             # Sends schema + question to the LLM, returns SQL
├── sample_data.sql    # Creates demo tables and inserts sample rows
├── requirements.txt   # Python dependencies
├── .env.example       # Template for your DB + LLM credentials
├── .gitignore         # Keeps .env, venv and caches out of git
└── README.md          # This file
```

---

## 3. Setup instructions

### Prerequisites
- Python 3.10+
- A running PostgreSQL server
- An OpenAI API key **or** any OpenAI-compatible endpoint (Ollama, LM Studio, Groq, …)

### Step 1 — Clone and install dependencies
```bash
git clone https://github.com/suryanshranjan/nl-to-sql.git
cd nl-to-sql
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2 — Create the database and load sample data
```bash
# Create the database (one time)
psql -U postgres -c "CREATE DATABASE nl_to_sql_demo;"

# Load tables + sample rows
psql -U postgres -d nl_to_sql_demo -f sample_data.sql
```

### Step 3 — Configure `.env`
Copy the template, then fill in your real values:
```bash
cp .env.example .env      # Windows: copy .env.example .env
```
```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nl_to_sql_demo
DB_USER=postgres
DB_PASSWORD=your_password

OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

> `.env` is listed in `.gitignore`, so your credentials are never committed.

> Using a local model? Point `OPENAI_BASE_URL` at it, e.g. Ollama's
> `http://localhost:11434/v1`, and set `OPENAI_MODEL` accordingly.

### Step 4 — Run the app
```bash
streamlit run app.py
```
Your browser opens at `http://localhost:8501`. Try the example questions!

---

## 4. Example questions

| Question | What it returns |
|---|---|
| Show total sales | Sum of all order amounts |
| Show sales by city | Total amount grouped by customer city |
| Top 5 customers by revenue | The 5 highest-spending customers |
| Orders placed this month | Orders with an `order_date` in the current month |

---

## 5. Key concepts explained

### Schema context — *"how the LLM knows your tables"*
The LLM has never seen your database. `schema_loader.py` inspects PostgreSQL
and produces a small text description like:

```
Table: customers
  - customer_id (INTEGER)
  - customer_name (VARCHAR)
  - city (VARCHAR)

Table: orders
  - order_id (INTEGER)
  - customer_id (INTEGER)
  - amount (NUMERIC)
  - order_date (DATE)
```

We inject that text into the prompt. Now the model writes SQL using the **real**
table and column names instead of guessing. This is the single most important
trick for getting correct SQL.

### Guardrails — *"why it can't damage your data"*
`sql_validator.py` enforces one simple rule: **allow exactly one read-only
SELECT, block everything else.** Concretely it:

- Requires the statement to start with `SELECT` (or `WITH … SELECT`).
- Rejects multiple statements (no `SELECT 1; DROP TABLE …`).
- Blocks dangerous keywords: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`,
  `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, and more.

It uses **word boundaries**, so a harmless column like `updated_at` does not
accidentally trip the `UPDATE` rule. The generated SQL is also shown to you
**before** it runs, so there are no surprises.

### The NL → SQL workflow — *"what happens on each click"*
1. **Read schema** — `schema_loader.get_schema_text()`
2. **Generate SQL** — `llm.generate_sql(schema, question)`
3. **Show SQL** — displayed in the UI before execution
4. **Validate** — `sql_validator.validate_sql(sql)` (the safety gate)
5. **Execute** — `db.run_query(sql)` against PostgreSQL
6. **Display** — results rendered as a table in Streamlit

---

## 6. How to Explain This Project in an Interview

A ready-to-use talk track. Walk through these six points in order.

### Problem statement
"Most people who need data can't write SQL. I built a tool that lets a
non-technical user ask a question in plain English and get back real,
trustworthy results from a PostgreSQL database — without ever touching SQL,
and without any risk of damaging the data."

### Architecture
"It's a small, modular Streamlit app with a clean separation of concerns.
Each responsibility lives in its own file: `db.py` owns the connection,
`schema_loader.py` describes the database, `llm.py` talks to the model,
`sql_validator.py` enforces safety, and `app.py` orchestrates the flow and
renders the UI. The pipeline is: question → schema → LLM → validate → execute
→ display. Because the pieces are decoupled, I could swap PostgreSQL for
another database or swap the LLM provider with minimal changes."

### Schema context
"The core insight is that an LLM can't see your database, so you have to
describe it. I use SQLAlchemy's inspector to pull the live tables and columns
and format them into a compact text block, which I inject into the prompt.
This grounds the model in reality — it writes SQL against the actual schema
instead of hallucinating column names. It also means the app automatically
adapts when the schema changes; there's nothing hardcoded."

### Prompt engineering
"My system prompt does three things: it sets the role ('expert PostgreSQL
assistant'), it states hard rules ('return only one read-only SELECT, output
raw SQL only, use only these tables'), and it supplies the schema context. I
set temperature to 0 for deterministic output. I also clean the response to
strip markdown code fences, since models often wrap SQL in triple backticks."

### SQL validation
"I never trust the model's output. Before any query runs, it passes through a
validator that allows exactly one read-only SELECT and blocks every
data-changing or structural keyword — DROP, DELETE, UPDATE, INSERT, ALTER,
TRUNCATE, and so on. I reject stacked statements to prevent SQL-injection-style
chaining, and I use word boundaries so legitimate column names aren't false
positives. It's a deliberately simple, auditable allow-list — defense in depth
on top of using a read-only database role in production."

### Future improvements
- **Read-only DB user** — enforce safety at the database level too, not just in code.
- **Few-shot examples** in the prompt to boost accuracy on tricky joins.
- **Result limiting** — auto-append `LIMIT` to protect against huge result sets.
- **Query history & caching** — remember past questions and reuse SQL.
- **Charts** — auto-visualize results (bar/line) when appropriate.
- **Multi-table reasoning & self-correction** — feed execution errors back to
  the LLM so it can fix its own SQL.
- **Support for more dialects** (MySQL, SQLite, BigQuery) via SQLAlchemy.

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| "Cannot reach PostgreSQL" | Check `.env` DB settings (copied from `.env.example`) and that the server is running. |
| "LLM request failed" | Verify `OPENAI_API_KEY` / `OPENAI_BASE_URL` and network access. |
| "Query blocked by safety check" | The model produced a non-SELECT query; rephrase the question. |
| Empty results | The query was valid but matched no rows — try a broader question. |
