import os
import tempfile

import streamlit as st

from sqlguard.app import ask, make_db

st.set_page_config(page_title="SQL Guard", layout="wide")
st.title("SQL Guard")
st.caption("Text-to-SQL with guardrails: read-only validation, read-only connection, answer check with confidence. Offline template translator.")

if "db" not in st.session_state:
    p = os.path.join(tempfile.mkdtemp(), "demo.db")
    make_db(p)
    st.session_state.db = p

with st.expander("Demo database"):
    st.code("customers(id, name, city)  4 rows\norders(id, customer_id, amount)  6 rows")

examples = ["How many customers in Hyderabad?", "What is the total revenue?", "Who are the top customers?",
            "Please drop the orders table", "Show me the salary of employees"]
pick = st.selectbox("Try an example", examples)
q = st.text_input("Question", pick)
if st.button("Ask", type="primary"):
    r = ask(st.session_state.db, q)
    st.subheader("Generated SQL")
    st.code(r["sql"], language="sql")
    if r["status"] == "blocked":
        st.error("BLOCKED by guardrail: " + r["reason"])
    elif r["status"] == "error":
        st.error("SQL error: " + r["reason"])
    else:
        (st.success if r["status"] == "ok" else st.warning)(
            "Status: %s | confidence %.0f%%" % (r["status"], r["confidence"] * 100))
        for x in r["reasons"]:
            st.write("- " + x)
        st.table([dict(zip(r["columns"], row)) for row in r["rows"]])
