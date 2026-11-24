"""Does the SQL plausibly answer the question? Cheap structural checks + a confidence score."""
import re

AGG = {"how many": "count(", "total": "sum(", "average": "avg(", "avg": "avg("}


def check_answers(question, sql):
    """Return (confidence 0..1, reasons)."""
    q, s = question.lower(), sql.lower()
    conf, reasons = 1.0, []
    for phrase, fn in AGG.items():
        if phrase in q and fn not in s:
            conf -= 0.5
            reasons.append("question asks '%s' but SQL has no %s" % (phrase, fn.rstrip("(")))
    m = re.search(r"\bin ([a-z]+)\b", q)
    if m and m.group(1) not in ("total", "all") and m.group(1) not in s:
        conf -= 0.3
        reasons.append("place '%s' from the question is missing in SQL" % m.group(1))
    if "top" in q and "order by" not in s:
        conf -= 0.3
        reasons.append("'top' needs ORDER BY")
    return max(conf, 0.0), reasons
