#!/usr/bin/env python3
"""
Werkspree Outreach Script
- Loads leads from scraper output
- Generates personalized emails using templates
- Sends via Gmail API (google_api.py)
- Tracks contact status
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

HERMES_HOME = os.path.expanduser("~/.hermes")
GAPI = f"python {HERMES_HOME}/skills/productivity/google-workspace/scripts/google_api.py"
SCRAPER_DIR = Path(__file__).parent
LEADS_DIR = SCRAPER_DIR / "data"
TEMPLATES_FILE = SCRAPER_DIR / "email_templates.json"
SENT_FILE = SCRAPER_DIR / "data" / "sent_emails.json"
MAX_EMAILS_PER_DAY = 10


def load_leads():
    """Load all leads from JSON files."""
    all_leads = []
    for f in LEADS_DIR.glob("leads_*.json"):
        with open(f) as fh:
            all_leads.extend(json.load(fh))
    # Deduplicate by company_name
    seen = set()
    unique = []
    for l in all_leads:
        key = l["company_name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(l)
    return unique


def load_sent():
    """Load sent email tracking."""
    if SENT_FILE.exists():
        with open(SENT_FILE) as f:
            return json.load(f)
    return {}


def save_sent(sent):
    """Save sent email tracking."""
    SENT_FILE.parent.mkdir(exist_ok=True)
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f, indent=2, ensure_ascii=False)


def load_templates():
    """Load email templates."""
    with open(TEMPLATES_FILE) as f:
        return json.load(f)["templates"]


def get_eligible_leads(leads, sent):
    """Get leads that haven't been contacted yet."""
    today = datetime.now().strftime("%Y-%m-%d")
    sent_today = sum(1 for v in sent.values() if v.get("last_sent", "").startswith(today))

    if sent_today >= MAX_EMAILS_PER_DAY:
        print(f"Already sent {sent_today} emails today (limit: {MAX_EMAILS_PER_DAY}). Stopping.")
        return []

    eligible = []
    for lead in leads:
        company = lead["company_name"]
        if company in sent:
            status = sent[company].get("status")
            last_sent = sent[company].get("last_sent", "")
            if status == "initial_sent":
                # Check if 3 days passed for follow-up
                sent_date = datetime.strptime(last_sent[:10], "%Y-%m-%d")
                if (datetime.now() - sent_date).days >= 3:
                    lead["next_action"] = "followup_3days"
                    eligible.append(lead)
            elif status == "followup_3days_sent":
                sent_date = datetime.strptime(last_sent[:10], "%Y-%m-%d")
                if (datetime.now() - sent_date).days >= 7:
                    lead["next_action"] = "followup_7days"
                    eligible.append(lead)
            # If already sent final followup, skip
        else:
            lead["next_action"] = "initial"
            eligible.append(lead)

    remaining_quota = MAX_EMAILS_PER_DAY - sent_today
    return eligible[:remaining_quota]


def personalize(template, lead, sent_data=None):
    """Replace placeholders in template with lead data."""
    if sent_data is None:
        sent_data = {}
    replacements = {
        "{company_name}": lead.get("company_name", "Ihr Unternehmen"),
        "{branch}": lead.get("branch", "Ihre Branche"),
        "{region}": lead.get("region", "Berlin"),
        "{first_contact_date}": sent_data.get(lead.get("company_name", ""), {}).get("last_sent", "kürzlich")[:10] if lead.get("company_name", "") in sent_data else "kürzlich",
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value))
    return result


def send_email(to, subject, body):
    """Send email via Gmail API."""
    cmd = [
        "python", f"{HERMES_HOME}/skills/productivity/google-workspace/scripts/google_api.py",
        "gmail", "send",
        "--to", to,
        "--subject", subject,
        "--body", body,
        "--from", '"Finn Werksby" <a2807d@gmail.com>',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0, result.stdout + result.stderr


def main():
    # Outbound cold email is disabled by default. Use --send only after
    # documented consent/legal review and an explicit operator decision.
    if "--send" not in sys.argv:
        print("Outbound email disabled: lead collection and CRM preparation only.")
        print("Use --send only after consent/legal review.")
        return

    print("=" * 60)
    print("Werkspree Outreach Engine")
    print("=" * 60)

    leads = load_leads()
    print(f"Total leads: {len(leads)}")

    sent = load_sent()
    print(f"Already contacted: {len(sent)}")

    eligible = get_eligible_leads(leads, sent)
    print(f"Eligible to contact today: {len(eligible)}")

    if not eligible:
        print("No leads to contact today. Done.")
        return

    templates = load_templates()

    for lead in eligible:
        action = lead.get("next_action", "initial")
        template = templates.get(action, templates["initial"])

        company = lead["company_name"]
        to = lead.get("email", "")
        if not to:
            print(f"  SKIP {company}: no email address")
            continue

        subject = personalize(template["subject"], lead, sent)
        body = personalize(template["body"], lead, sent)

        print(f"\n  Sending {action} to {company} ({to})...")
        success, output = send_email(to, subject, body)

        if success:
            sent[company] = {
                "status": f"{action}_sent",
                "last_sent": datetime.now().isoformat(),
                "email": to,
                "branch": lead.get("branch", ""),
                "region": lead.get("region", ""),
            }
            print(f"  OK: {company}")
        else:
            print(f"  FAIL: {company}: {output[:200]}")

    save_sent(sent)
    print(f"\nDone. Sent to {len(eligible)} leads today.")


if __name__ == "__main__":
    main()
