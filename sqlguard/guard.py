"""Static guardrails for generated SQL: allow a single read-only SELECT on known tables."""
import re
import sqlite3

FORBIDDEN = {"insert", "update", "delete", "drop", "alter", "create", "replace", "attach",
             "detach", "pragma", "vacuum", "reindex", "truncate", "grant", "load_extension"}


class Blocked(Exception):
    pass


def _strip(sql):
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return sql.strip()


def _strip_strings(sql):
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def validate(sql, allowed_tables):
    s = _strip(sql)
    if not s:
        raise Blocked("empty query")
    body = _strip_strings(s).rstrip(";").strip()
    if ";" in body:
        raise Blocked("multiple statements")
    low = body.lower()
    if not (low.startswith("select") or low.startswith("with")):
        raise Blocked("only SELECT is allowed")
    words = set(re.findall(r"[a-z_]+", low))
    bad = words & FORBIDDEN
    if bad:
        raise Blocked("forbidden keyword: " + sorted(bad)[0])
    used = set(re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", low))
    ctes = set(re.findall(r"\b([a-z_][a-z0-9_]*)\s+as\s*\(", low))
    unknown = used - set(t.lower() for t in allowed_tables) - ctes
    if unknown:
        raise Blocked("unknown table: " + sorted(unknown)[0])
    if "sqlite_master" in low:
        raise Blocked("schema tables are off limits")
    return s.rstrip(';').strip()


def run_readonly(db_path, sql, allowed_tables, limit=100):
    safe = validate(sql, allowed_tables)
    uri = "file:%s?mode=ro" % db_path
    con = sqlite3.connect(uri, uri=True)
    try:
        cur = con.execute(safe)
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchmany(limit)
    finally:
        con.close()
