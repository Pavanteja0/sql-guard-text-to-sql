# SQL Guard: text-to-SQL with guardrails

Turns a plain-English question into SQL, refuses anything that is not a safe read, runs it on a read-only connection, and attaches a confidence score based on whether the SQL matches the question.

## Layers
1. **Validator** (`sqlguard/guard.py`): strips comments, allows one SELECT/WITH statement only, blocks write/DDL/PRAGMA/ATTACH keywords (keywords inside string literals are ignored), only known tables, no `sqlite_master`.
2. **Read-only execution**: SQLite opened with `mode=ro`, so a write fails even if validation were bypassed (tested).
3. **Answer check** (`sqlguard/check.py`): rule-based. Flags SQL that lacks COUNT/SUM/AVG when the question asks for one, drops a place named in the question, or lacks ORDER BY for "top". Confidence drops, status becomes `low_confidence` below 0.7.

## Honest scope
- The default translator is an offline set of templates, so the demo runs with no API key. The interface is `translate(question) -> sql`, so an LLM can be plugged in. No live LLM run has been done.
- The answer check is a heuristic, not proof of correctness. The demo DB is tiny (4 customers, 6 orders).

## Run
    python -m unittest discover -s tests     # 10 tests
    python -m sqlguard.app "How many customers in Hyderabad?"

Tests cover: DROP/DELETE/UPDATE/INSERT/ALTER/PRAGMA/ATTACH blocked, stacked statements, comment tricks, unknown tables, keywords inside strings, read-only connection, mismatch -> low confidence.
Standard library only.

## Demo and try it
- **Live app, no install:** https://pavan-sql-guard.streamlit.app (free hosting, may take a few seconds to wake up)
- Demo video with voiceover (45 s): [demo/demo.mp4](demo/demo.mp4)
- Run the Streamlit app yourself on any machine with Python 3.10+:

      git clone https://github.com/Pavanteja0/sql-guard-text-to-sql
      cd sql-guard-text-to-sql
      pip install -r requirements.txt
      streamlit run app.py
