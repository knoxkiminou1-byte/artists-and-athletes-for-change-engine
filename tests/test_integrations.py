from aafc_engine.integrations.runtime import load_catalog, run, slug, validate_record

def test_catalog_is_one_hundred_mit():
    catalog = load_catalog()
    assert len(catalog) == 100
    assert {row["license"] for row in catalog} == {"MIT"}
    assert len({row["repo"] for row in catalog}) == 100

def test_slug_and_evidence_rule():
    assert slug("Law Offices of Nicole") == "law-offices-of-nicole"
    errors = validate_record({"status": "OWED", "evidence": ""})
    assert errors

def test_report_and_mail_do_not_invent_or_send():
    report = run("markdown_report", {"client": "LONHA", "findings": [{"title": "No H1", "evidence": "homepage", "why": "SEO", "fix": "Add one H1"}]})
    assert "Evidence only" in report["markdown"]
    preview = run("mail_preview", {"to": "owner@example.com", "subject": "Audit", "body": "Ready"})
    assert preview["preview"].startswith("DRY RUN")
