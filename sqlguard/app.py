import sqlite3

from .check import check_answers
from .guard import Blocked, run_readonly
from .translate import RuleTranslator

TABLES = ["customers", "orders"]


def make_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, city TEXT);
    CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL);
    INSERT INTO customers VALUES (1,'Asha','Hyderabad'),(2,'Ravi','Bangalore'),(3,'Meena','Hyderabad'),(4,'Kiran','Chennai');
    INSERT INTO orders VALUES (1,1,120.0),(2,1,80.0),(3,2,300.0),(4,3,50.0),(5,4,75.0),(6,2,25.0);
    """)
    con.commit()
    con.close()


def ask(db_path, question, translator=None, min_conf=0.7):
    sql = (translator or RuleTranslator()).translate(question)
    try:
        cols, rows = run_readonly(db_path, sql, TABLES)
    except Blocked as e:
        return {"sql": sql, "status": "blocked", "reason": str(e)}
    except sqlite3.Error as e:
        return {"sql": sql, "status": "error", "reason": str(e)}
    conf, reasons = check_answers(question, sql)
    status = "ok" if conf >= min_conf else "low_confidence"
    return {"sql": sql, "status": status, "confidence": round(conf, 2), "reasons": reasons,
            "columns": cols, "rows": rows}


if __name__ == "__main__":
    import sys
    import tempfile, os
    p = os.path.join(tempfile.mkdtemp(), "demo.db")
    make_db(p)
    print(ask(p, " ".join(sys.argv[1:]) or "How many customers in Hyderabad?"))
