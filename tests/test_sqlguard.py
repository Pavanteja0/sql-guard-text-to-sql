import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sqlguard.app import TABLES, ask, make_db
from sqlguard.check import check_answers
from sqlguard.guard import Blocked, validate


class Fixed:
    def __init__(self, sql):
        self.sql = sql

    def translate(self, q):
        return self.sql


class T(unittest.TestCase):
    def setUp(self):
        self.db = os.path.join(tempfile.mkdtemp(), "t.db")
        make_db(self.db)

    def blocked(self, sql):
        with self.assertRaises(Blocked):
            validate(sql, TABLES)

    def test_blocks_destructive(self):
        for s in ["DROP TABLE orders", "DELETE FROM orders", "UPDATE orders SET amount=0",
                  "INSERT INTO orders VALUES (9,1,1)", "ALTER TABLE orders ADD x INT",
                  "PRAGMA table_info(orders)", "ATTACH DATABASE 'x' AS y"]:
            self.blocked(s)

    def test_blocks_stacked_and_comment_tricks(self):
        self.blocked("SELECT 1; DROP TABLE orders")
        self.blocked("/* hi */ DELETE FROM orders")
        self.blocked("SELECT * FROM sqlite_master")

    def test_blocks_unknown_table(self):
        self.blocked("SELECT * FROM employees")

    def test_keyword_inside_string_is_fine(self):
        validate("SELECT * FROM customers WHERE name = 'drop; table'", TABLES)

    def test_allows_select_join_cte(self):
        validate("SELECT c.name FROM customers c JOIN orders o ON o.customer_id=c.id", TABLES)
        validate("WITH t AS (SELECT * FROM orders) SELECT COUNT(*) FROM t", TABLES)

    def test_end_to_end_count(self):
        r = ask(self.db, "How many customers in Hyderabad?")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["rows"], [(2,)])

    def test_destructive_question_blocked(self):
        r = ask(self.db, "please drop the orders table")
        self.assertEqual(r["status"], "blocked")
        self.assertEqual(ask(self.db, "total revenue")["rows"], [(650.0,)])

    def test_readonly_connection(self):
        # even if validation were bypassed, the connection is read-only
        import sqlite3
        con = sqlite3.connect("file:%s?mode=ro" % self.db, uri=True)
        with self.assertRaises(sqlite3.OperationalError):
            con.execute("DELETE FROM orders")

    def test_mismatch_gets_low_confidence(self):
        r = ask(self.db, "How many customers in Chennai?", translator=Fixed("SELECT name FROM customers"))
        self.assertEqual(r["status"], "low_confidence")
        self.assertLess(r["confidence"], 0.7)

    def test_confidence_full_when_matching(self):
        c, _ = check_answers("total revenue", "SELECT SUM(amount) FROM orders")
        self.assertEqual(c, 1.0)


if __name__ == "__main__":
    unittest.main()
