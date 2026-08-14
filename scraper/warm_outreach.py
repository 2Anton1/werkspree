#!/usr/bin/env python3
"""
Werkspree Warm Outreach
Sends emails to warmest leads first (warmth_score >= 6, deep research).
Auto-send is the DEFAULT (user-approved). Use --dry-run to simulate.
Uses scored_leads.json if available, falls back to leads_*.json.
"""

import json
import sys
import subprocess
import os
from datetime import datetime
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
SCRAPER_DIR = Path(__file__).parent
DATA_DIR = SCRAPER_DIR / "data"
TEMPLATES_FILE = SCRAPER_DIR / "email_templates.json"
SENT_FILE = DATA_DIR / "sent_emails.json"
SCORED_FILE = DATA_DIR / "scored_leads.json"
MAX_EMAILS_PER_DAY = 10
MIN_WARMTH_SCORE = 6


def load_scored_leads():
    """Load scored leads, sorted by warmth score descending."""
    if SCORED_FILE.exists():
        with open(SCORED_FILE) as f:
            leads = json.load(f)
        leads.sort(key=lambda x: x.get("warmth_score", 0), reverse=True)
        return leads

    # Fallback: load raw leads
    lead_files = sorted(DATA_DIR.glob("leads_*.json"))
    if not lead_files:
        return []
    with open(lead_files[-1]) as f:
        return json.load(f)


def load_sent():
    if SENT_FILE.exists():
        with open(SENT_FILE) as f:
            return json.load(f)
    return {}


def save_sent(sent):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)


def load_templates():
    with open(TEMPLATES_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_eligible_leads(leads, sent):
    """Get warmest leads not yet contacted, prioritized by score."""
    today = datetime.now().strftime("%Y-%m-%d")
    sent_today = sum(1 for v in sent.values() if v.get("last_sent", "").startswith(today))
    remaining = MAX_EMAILS_PER_DAY - sent_today
    if remaining <= 0:
        return []

    # First: new leads (initial contact), sorted by warmth
    eligible = []
    for lead in leads:
        company = lead["company_name"]
        score = lead.get("warmth_score", 0)

        if company not in sent:
            if score >= MIN_WARMTH_SCORE and lead.get("research_depth") == "deep":
                lead["next_action"] = "initial"
                eligible.append(lead)
        else:
            # Check for follow-ups
            status = sent[company].get("status")
            last_sent = sent[company].get("last_sent", "")
            if last_sent:
                try:
                    sent_date = datetime.fromisoformat(last_sent)
                    days_since = (datetime.now() - sent_date).days

                    if status == "initial_sent" and days_since >= 3:
                        lead["next_action"] = "followup_3days"
                        eligible.append(lead)
                    elif status == "followup_3days_sent" and days_since >= 7:
                        lead["next_action"] = "followup_7days"
                        eligible.append(lead)
                except Exception:
                    pass

        if len(eligible) >= remaining:
            break

    return eligible


def personalize(template, lead, sent_data=None):
    if sent_data is None:
        sent_data = {}

    # Generate warmth-specific intro
    score = lead.get("warmth_score", 0)
    signals = lead.get("warmth_signals", [])

    warmth_intro = ""
    if "manual_contact_form" in signals:
        warmth_intro = "Ich habe gesehen, dass Sie auf Ihrer Website ein Kontaktformular nutzen — ein Bereich, den wir oft als erstes automatisieren können."
    elif "no_whatsapp" in signals:
        warmth_intro = f"Für {lead.get('branch','Ihre Branche')} ist eine schnelle Kundenkommunikation besonders wichtig. Ein WhatsApp-KI-Assistent könnte hier sofort Entlastung schaffen."
    elif "mentions_accounting" in signals:
        warmth_intro = "Auf Ihrer Website habe ich Hinweise auf manuelle Buchhaltungsprozesse gefunden — ein klassischer Bereich, in dem KI-Automatisierung sofort Zeit spart."

    replacements = {
        "{company_name}": lead.get("company_name", "Ihr Unternehmen"),
        "{branch}": lead.get("branch", "Ihre Branche"),
        "{region}": lead.get("region", "Berlin"),
        "{first_contact_date}": sent_data.get(lead.get("company_name", ""), {}).get("last_sent", "kürzlich")[:10] if lead.get("company_name", "") in sent_data else "kürzlich",
        "{warmth_intro}": warmth_intro,
    }
    for key, value in replacements.items():
        template = template.replace(key, str(value))
    return template


def send_email(to, subject, body):
    cmd = [
        "python", str(HERMES_HOME / "skills/productivity/google-workspace/scripts/google_api.py"),
        "gmail", "send",
        "--to", to,
        "--subject", subject,
        "--body", body,
        "--from", '"Finn Werksby" <a2807d@gmail.com>',
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except Exception as e:
        return False, str(e)


def hunter_verify(emails):
    """Optionally verify up to 8 emails with Hunter.io if HUNTER_API_KEY is set.
    Returns a set of emails confirmed valid/acceptable, or None when no key is
    configured (verification is skipped and sending proceeds)."""
    key = os.environ.get("HUNTER_API_KEY", "")
    if not key or not emails:
        return None  # no verification configured
    import urllib.request
    import urllib.parse
    verified = set()
    for email in emails[:8]:
        try:
            q = urllib.parse.urlencode({"email": email, "api_key": key})
            with urllib.request.urlopen(f"https://api.hunter.io/v2/email-verifier?{q}", timeout=15) as r:
                data = json.loads(r.read())
            status = data.get("data", {}).get("status", "")
            if status in ("valid", "acceptable"):
                verified.add(email)
            else:
                print(f"  Hunter: {email} -> {status} (skip)")
        except Exception as e:
            print(f"  Hunter check failed for {email}: {e}")
    return verified


def main():
    # Auto-send is the default (user-approved). Use --dry-run to simulate.
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY-RUN MODE: no emails will be sent.")

    print("=" * 60)
    print("Werkspree Warm Outreach Engine")
    print("=" * 60)

    leads = load_scored_leads()
    print(f"Total scored leads: {len(leads)}")

    warm = [l for l in leads if l.get("warmth_score", 0) >= MIN_WARMTH_SCORE]
    deep = [l for l in warm if l.get("research_depth") == "deep"]
    print(f"Hot leads (score >= {MIN_WARMTH_SCORE}, deep research): {len(deep)}")

    sent = load_sent()
    print(f"Already contacted: {len(sent)}")

    eligible = get_eligible_leads(leads, sent)
    print(f"Eligible to contact today: {len(eligible)}")

    if not eligible:
        print("No leads to contact today. Done.")
        return 0

    # Optional Hunter verification for the top 8 eligible leads (only if a
    # HUNTER_API_KEY exists in ~/.hermes/.env).
    if not dry_run:
        verified = hunter_verify([l.get("verified_email") or l.get("email") for l in eligible if l.get("verified_email") or l.get("email")])
        if verified is not None:
            before = len(eligible)
            eligible = [l for l in eligible if (l.get("verified_email") or l.get("email")) in verified]
            print(f"Hunter verification: {before} -> {len(eligible)} eligible")

    templates = load_templates()

    for lead in eligible:
        action = lead.get("next_action", "initial")
        template = templates.get(action, templates["initial"])

        company = lead["company_name"]
        to = lead.get("verified_email") or lead.get("email", "")
        score = lead.get("warmth_score", 0)

        if not to:
            print(f"  SKIP {company}: no email")
            continue

        # Inject warmth intro into template
        template_copy = dict(template)
        if "{warmth_intro}" not in template_copy["body"]:
            # Insert warmth intro after first line
            lines = template_copy["body"].split("\n", 2)
            template_copy["body"] = lines[0] + "\n\n{warmth_intro}\n" + (lines[1] if len(lines) > 1 else "")

        subject = personalize(template_copy["subject"], lead, sent)
        body = personalize(template_copy["body"], lead, sent)

        if dry_run:
            print(f"\n  [DRY] [{score}/10] {action} -> {company} ({to})")
            print(f"    Subject: {subject}")
            continue

        print(f"\n  [{score}/10] Sending {action} to {company} ({to})...")
        success, output = send_email(to, subject, body)

        if success:
            sent[company] = {
                "status": f"{action}_sent",
                "last_sent": datetime.now().isoformat(),
                "email": to,
                "branch": lead.get("branch", ""),
                "region": lead.get("region", ""),
                "warmth_score": score,
                "response_status": "awaiting_reply" if action == "initial" else "followup_sent",
            }
            print(f"  ✅ Sent to {company}")
        else:
            sent[company] = {
                "status": f"{action}_failed",
                "last_sent": datetime.now().isoformat(),
                "email": to,
                "branch": lead.get("branch", ""),
                "region": lead.get("region", ""),
                "warmth_score": score,
                "response_status": "bounced",
                "error": output[:200],
            }
            print(f"  ❌ Failed: {output[:200]}")

    save_sent(sent)
    print(f"\nDone. Sent to {len(eligible)} leads today.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
