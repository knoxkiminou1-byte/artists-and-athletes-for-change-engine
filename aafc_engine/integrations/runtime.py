"""AAFC MIT integration runtime.

Stdlib adapters so the operator studio works with no extra install.
Optional MIT packages are declared in requirements-integrations.txt and
are never imported unless present. This module does not audit websites
and does not send email.
"""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
import uuid
import zipfile
from datetime import date, timedelta
from pathlib import Path

CATALOG_PATH = Path(__file__).with_name("catalog.json")

def load_catalog():
    return json.loads(CATALOG_PATH.read_text())

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
    amount = record.get("amount")
    if amount is not None and not isinstance(amount, (int, float)):
        errors.append("amount must be a number")
    if record.get("status") in {"OWED", "EXPECTED", "OVERDUE"} and not str(record.get("evidence") or "").strip():
        errors.append("owed, expected, and overdue need evidence")
    return errors

def plain_language(amount, days):
    money = f"${amount:,.2f}"
    when = "today" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"
    return f"{money} due {when}"

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
    for n in range(count):
        day = start + timedelta(days=30 * n)
        lines += ["BEGIN:VEVENT", f"UID:{uuid.uuid4()}@aafc", f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}", f"SUMMARY:{title}", "END:VEVENT"]
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
    if adapter == "plain_language":
        return {"text": plain_language(float(payload.get("amount") or 0), int(payload.get("days") or 0))}
    if adapter == "sanitize":
        return {"text": sanitize(str(payload.get("value") or ""))}
    if adapter == "mail_preview":
        return {"preview": mail_preview(str(payload.get("to") or ""), str(payload.get("subject") or ""), str(payload.get("body") or ""))}
    raise KeyError(adapter)
