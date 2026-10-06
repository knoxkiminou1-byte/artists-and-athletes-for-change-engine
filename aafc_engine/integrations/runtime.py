"""AAFC MIT integration runtime.

Stdlib adapters. Does not audit websites and does not send email.
"""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import uuid
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent

def load_catalog():
    whole = HERE / "catalog.json"
    if whole.exists():
        return json.loads(whole.read_text())
    rows = []
    for name in ("catalog-a.json", "catalog-b.json"):
        path = HERE / name
        if path.exists():
            rows.extend(json.loads(path.read_text()))
    if len(rows) != 100:
        raise FileNotFoundError(f"expected 100 MIT rows, found {len(rows)}")
    return rows

def slug(value):
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "item"

def sanitize(value):
    text = re.sub(r"(?is)<script.*?>.*?</script>", "", value)
    text = re.sub(r"(?is)<style.*?>.*?</style>", "", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").strip()

def validate_record(record):
    errors = []
    email = str(record.get("email") or "")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("email is not a valid address")
    url = str(record.get("url") or "")
    if url and not re.match(r"^https://", url):
        errors.append("url must be https")
    if record.get("status") in {"OWED", "EXPECTED", "OVERDUE"} and not str(record.get("evidence") or "").strip():
        errors.append("owed, expected, and overdue need evidence")
    return errors

def markdown_report(client, findings):
    lines = [f"# AAFC findings — {sanitize(client)}", "", "Evidence only. Nothing here was inferred.", ""]
    for finding in findings:
        title = sanitize(str(finding.get("title") or "Finding"))
        evidence = sanitize(str(finding.get("evidence") or ""))
        why = sanitize(str(finding.get("why") or finding.get("why_it_matters") or ""))
        fix = sanitize(str(finding.get("fix") or finding.get("recommended_fix") or ""))
        lines += [f"## {title}", "", f"- Evidence: {evidence}", f"- Why it matters: {why}", f"- Fix: {fix}", ""]
    if not findings:
        lines.append("No evidence-backed findings were supplied.")
    return "\n".join(lines).rstrip() + "\n"

def csv_ledger(rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["date", "kind", "amount", "status", "evidence", "project"])
    writer.writeheader()
    for row in rows:
        if row.get("status") in {"OWED", "EXPECTED", "OVERDUE"} and not str(row.get("evidence") or "").strip():
            raise ValueError("ledger row missing evidence")
        writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
    return buf.getvalue()

def ics_schedule(title, start, count=3):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AAFC//Studio//EN"]
    for _ in range(count):
        lines += ["BEGIN:VEVENT", f"UID:{uuid.uuid4()}@aafc", f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}", f"SUMMARY:{title}", "END:VEVENT"]
        start = start + timedelta(days=30)
    lines.append("END:VCALENDAR")
    return "\n".join(lines) + "\n"

def mail_preview(to, subject, body):
    errors = validate_record({"email": to})
    if errors:
        raise ValueError(errors[0])
    return f"DRY RUN — not sent\nTo: {to}\nSubject: {sanitize(subject)}\n\n{sanitize(body)}\n"

def run(adapter, payload):
    if adapter == "slug":
        return {"slug": slug(str(payload.get("value") or ""))}
    if adapter == "validate_record":
        return {"errors": validate_record(payload)}
    if adapter == "markdown_report":
        return {"markdown": markdown_report(str(payload.get("client") or "Client"), payload.get("findings") or [])}
    if adapter == "csv_ledger":
        return {"csv": csv_ledger(payload.get("rows") or [])}
    if adapter == "ics_schedule":
        start = date.fromisoformat(str(payload.get("start") or date.today().isoformat()))
        return {"ics": ics_schedule(str(payload.get("title") or "AAFC review"), start)}
    if adapter == "mail_preview":
        return {"preview": mail_preview(str(payload.get("to") or ""), str(payload.get("subject") or ""), str(payload.get("body") or ""))}
    if adapter == "sanitize":
        return {"text": sanitize(str(payload.get("value") or ""))}
    raise KeyError(adapter)
