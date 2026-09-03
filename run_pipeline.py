#!/usr/bin/env python3
"""
Werkspree Lead Pipeline - Script mode for cron.
Runs pipeline.py → warmth_scorer.py → warm_outreach.py (auto-send, user-approved).
Writes a daily report to reports/ and exits non-zero on any step failure so the
cron scheduler marks broken runs as errors instead of false successes.
"""
import subprocess
import json
import sys
import os
import urllib.request
from pathlib import Path
from datetime import datetime

WORKDIR = Path("/Users/anton/work/werkspree")
SCRAPER_DIR = WORKDIR / "scraper"
DATA_DIR = SCRAPER_DIR / "data"
REPORT_DIR = WORKDIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)
SENT_FILE = DATA_DIR / "sent_emails.json"

# Scrapling (pipeline.py, warmth_scorer.py) ist NUR in /usr/local/bin/python3
# installiert. Der Cron-Script-Runner nutzt ein anderes Python ohne scrapling
# → absolute Pfade verwenden, sonst ModuleNotFoundError (7 Fehlschläge 26.-28.08.).
# Fallback auf shutil.which("python3") falls /usr/local/bin/python3 fehlt.
import shutil
PYTHON = "/usr/local/bin/python3"
if not os.path.exists(PYTHON):
    PYTHON = shutil.which("python3") or "python3"

# Airtable CRM
AIRTABLE_BASE = "appyMLhXOMHpD5vfT"
AIRTABLE_TABLE = "tbluCUpuCPxW1GcWD"
# Die produktive Airtable-Auswahlliste enthält aktuell nur diese beiden Werte.
# Zusätzliche, in der Archivvorlage dokumentierte Statuswerte liefern dort 422
# und dürfen deshalb erst nach einer Schema-Erweiterung verwendet werden.
AIRTABLE_STATUS_VALUES = {"Neu", "Kontaktiert"}
AIRTABLE_STATUS_MAP = {
    "none": "Neu",
    "awaiting_reply": "Kontaktiert",
    "followup_sent": "Kontaktiert",
    "bounced": "Neu",
    "replied": "Kontaktiert",
    "demo_sent": "Kontaktiert",
    "proposal_sent": "Kontaktiert",
    "not_contacted": "Neu",
}
PROTECTED_CRM_STATUSES = {"Kontaktiert"}


def load_env():
    """Load ~/.hermes/.env into os.environ (without overriding existing)."""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def run_cmd(cmd, cwd=WORKDIR, timeout=600):
    """Run command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout}s: {cmd}"
    except Exception as e:
        return False, "", str(e)


def airtable_api(method, url, payload=None, token=""):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(payload).encode() if payload else None
    # Retry (bis zu 2x) bei Timeout/Netzwerkfehlern — Airtable-API ist oft langsam
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, data=data, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == 2:
                return {"error": str(e)}
    return {"error": "unreachable"}


def merge_outreach_statuses(leads, sent_file=SENT_FILE):
    """Merge locally logged outreach state into matching scored leads."""
    if not sent_file.exists():
        return 0
    try:
        sent = json.loads(sent_file.read_text())
    except (OSError, json.JSONDecodeError):
        return 0
    merged = 0
    for lead in leads:
        record = sent.get(lead.get("company_name", ""))
        if not record:
            continue
        status = record.get("response_status", "")
        if status:
            lead["response_status"] = status
            merged += 1
    return merged


def resolved_crm_status(lead, existing_fields):
    """Keep human CRM progress; otherwise use the recorded outreach state."""
    existing_status = existing_fields.get("Status", "")
    if existing_status in PROTECTED_CRM_STATUSES:
        return existing_status
    explicit_status = lead.get("crm_status")
    if explicit_status in AIRTABLE_STATUS_VALUES:
        return explicit_status
    return AIRTABLE_STATUS_MAP.get(lead.get("response_status", "none"), "Eingehend")


def sync_airtable(leads, token):
    """Upsert leads into Airtable CRM (match by Company field)."""
    if not token:
        return "Airtable sync skipped (no AIRTABLE_API_KEY in .env)"
    base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}"

    # Fetch existing records (paginated)
    existing = {}
    offset = None
    while True:
        url = base_url + "?pageSize=100"
        if offset:
            url += f"&offset={offset}"
        resp = airtable_api("GET", url, token=token)
        if "error" in resp:
            return f"Airtable read failed: {resp['error']}"
        for rec in resp.get("records", []):
            name = (rec.get("fields") or {}).get("Company", "")
            if name:
                existing[name] = rec
        offset = resp.get("offset")
        if not offset:
            break

    created = updated = 0
    for lead in leads:
        name = lead.get("company_name", "")
        if not name:
            continue
        notes = "; ".join(filter(None, [
            f"source={lead.get('source', '')}",
            f"last_checked={lead.get('last_checked', '')}",
            f"website_issue={lead.get('website_issue', '') or 'ok'}",
            f"need={lead.get('automation_need', '')}",
            f"next={lead.get('next_step', '')}",
            f"signals={','.join((lead.get('warmth_signals') or [])[:4])}",
            f"email={(lead.get('verified_email') or lead.get('email', ''))}",
        ]))
        fields = {
            "Company": name[:255],
            "Branch": lead.get("branch", ""),
            "Region": lead.get("region", ""),
            "Website": lead.get("website", ""),
            # KEIN "Email"-Feld: Die Tabelle (Table 1 / tbluCUpuCPxW1GcWD) hat
            # keine Email-Spalte — E-Mail wird in Notes abgelegt (422-Schutz).
            "Phone": lead.get("phone", ""),
            "Status": resolved_crm_status(lead, (existing.get(name) or {}).get("fields", {})),
            "Potential_Score": lead.get("warmth_score", 0),
            "Notes": notes,
        }
        fields = {k: v for k, v in fields.items() if v not in (None, "")}
        if name in existing:
            airtable_api("PATCH", f"{base_url}/{existing[name]['id']}", {"fields": fields}, token=token)
            updated += 1
        else:
            airtable_api("POST", base_url, {"fields": fields}, token=token)
            created += 1
    return f"Airtable: {created} created, {updated} updated"


def main():
    load_env()
    full_lines = []
    compact = []

    def log(msg=""):
        print(msg)
        full_lines.append(msg)

    log("=" * 50)
    log(f"WERKSPREE PIPELINE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("=" * 50)

    steps = [
        ("[1/4] pipeline.py (Scraping + Filter)", f"{PYTHON} scraper/pipeline.py"),
        ("[2/4] warmth_scorer.py (Scoring)", f"{PYTHON} scraper/warmth_scorer.py"),
        ("[3/4] warm_outreach.py (Auto-Send)", f"{PYTHON} scraper/warm_outreach.py"),
    ]
    ok_all = True
    for label, cmd in steps:
        log(f"\n{label}")
        ok, out, err = run_cmd(cmd)
        log(out or err)
        if not ok:
            log(f"ERROR: {label} failed: {err}")
            ok_all = False

    # Step 4: Airtable CRM sync
    log("\n[4/4] Airtable CRM sync")
    scored_file = DATA_DIR / "scored_leads.json"
    summary = {}
    if scored_file.exists():
        try:
            leads = json.loads(scored_file.read_text())
            outreach_merged = merge_outreach_statuses(leads)
            summary = {
                "total": len(leads),
                "deep": sum(1 for l in leads if l.get("research_depth") == "deep"),
                "demo_candidates": sum(1 for l in leads if l.get("recommended_action") == "create_demo"),
                "with_email": sum(1 for l in leads if l.get("verified_email") or l.get("email")),
            }
            msg = sync_airtable(leads, os.environ.get("AIRTABLE_API_KEY", ""))
            log(f"Outreach-Status gemerged: {outreach_merged}")
            log(msg)
        except Exception as e:
            log(f"Airtable sync failed: {e}")
            ok_all = False
    else:
        log("ERROR: scored_leads.json not found")
        ok_all = False

    # Report file (full log)
    report = "\n".join(full_lines)
    report_path = REPORT_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d')}.md"
    report_path.write_text(report)
    (REPORT_DIR / "last_report.md").write_text(report)

    # Compact stdout for chat delivery
    print("\n" + "=" * 50)
    print(f"WERKSPREE SUMMARY {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"Total Leads: {summary.get('total', '?')} | Deep: {summary.get('deep', '?')} | "
          f"Demo-Kandidaten: {summary.get('demo_candidates', '?')} | Mit E-Mail: {summary.get('with_email', '?')}")
    print(f"Full report: {report_path}")
    print(f"Exit: {'OK' if ok_all else 'FAILED'}")
    print("=" * 50)

    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
