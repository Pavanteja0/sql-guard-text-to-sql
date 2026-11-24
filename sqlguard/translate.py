"""Question -> SQL. `RuleTranslator` is an offline stand-in (pattern templates).
Swap in an LLM with the same `translate(question) -> sql` interface."""
import re


class RuleTranslator:
    def translate(self, q):
        ql = q.lower()
        if re.search(r"how many customers", ql):
            m = re.search(r"in (\w+)", ql)
            if m and m.group(1) not in ("total", "all"):
                return "SELECT COUNT(*) FROM customers WHERE city = '%s'" % m.group(1).title()
            return "SELECT COUNT(*) FROM customers"
        if "total revenue" in ql:
            return "SELECT SUM(amount) FROM orders"
        if "top" in ql and "customer" in ql:
            return ("SELECT c.name, SUM(o.amount) AS total FROM customers c JOIN orders o "
                    "ON o.customer_id = c.id GROUP BY c.name ORDER BY total DESC LIMIT 3")
        if "average order" in ql:
            return "SELECT AVG(amount) FROM orders"
        if "delete" in ql or "drop" in ql:
            return "DROP TABLE orders"
        if "salary" in ql:
            return "SELECT salary FROM employees"
        if "cities" in ql:
            return "SELECT DISTINCT city FROM customers"
        return "SELECT name FROM customers"
