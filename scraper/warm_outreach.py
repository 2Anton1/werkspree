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
import re
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

    # Fallback: load raw leads (daily snapshot files only)
    import re as _re
    lead_files = sorted(f for f in DATA_DIR.glob("leads_*.json") if _re.match(r"leads_\d{8}\.json$", f.name))
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
        data = json.load(f)
    # Templates are nested under "templates" in the JSON file
    return data.get("templates", data)


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

        # E-Mail-Quellen-Filter (Spam-Schutz): Nur E-Mails, die wirklich zur
        # Firma gehören. "scraped" = aus Impressum/Kontaktseite (erlaubt),
        # "guessed" = info@-Geraten → PRÜFE ob E-Mail-Domain zur Firmen-Website
        # passt (dann ist es keine echte "guess" sondern ein altes Label).
        # Fix 25.08.: HKF (info@hkf.de) und ELEKTRO REIBSCH (info@elektro-reibsch.de)
        # waren als "guessed" markiert obwohl die E-Mail-Domain zur Website passt.
        src = (lead.get("email_source") or "").lower()
        has_email = bool(lead.get("verified_email") or lead.get("email"))
        if not has_email:
            continue
        if src == "guessed":
            # Re-Classify: wenn E-Mail-Domain zur Firmen-Website-Domain passt,
            # ist es keine echte "guess" sondern ein altes Label → allow
            email_addr = lead.get("email", "")
            website = lead.get("website", "")
            if email_addr and website:
                email_domain = email_addr.split("@")[-1].lower().split(".")[-2] if "@" in email_addr else ""
                site_domain = website.lower().split("//")[-1].split("/")[0].split(".")[-2] if "//" in website else ""
                if email_domain and site_domain and email_domain in site_domain:
                    lead["email_source"] = "scraped"  # re-classify
                    lead["verified_email"] = email_addr
                else:
                    print(f"  SKIP {company}: email_source=guessed + Domain-Mismatch -> nie versenden")
                    continue
            else:
                print(f"  SKIP {company}: email_source=guessed (info@-Geraten) -> nie versenden")
                continue

        # E-Mail-Validität: offensichtlich kaputte/garbled E-Mails überspringen
        # (z.B. Mallwitz: elmcha@r-utneodegkwt-lmales.nivzrisig — Encoding-Fehler)
        email_addr = lead.get("email", "")
        if email_addr and "@" in email_addr:
            local, domain = email_addr.split("@", 1)
            # Domain muss mindestens einen Punkt und mindestens 4 Zeichen haben
            if "." not in domain or len(domain) < 4 or len(local) < 2:
                print(f"  SKIP {company}: ungültige E-Mail-Adresse ({email_addr}) -> übersprungen")
                continue
            # Local-Part darf keine ungewöhnlichen Zeichenmuster haben (Encoding-Fehler)
            if re.search(r'[^\w.\-+]', local) or len(local) > 64:
                print(f"  SKIP {company}: garbled E-Mail-Local-Part ({email_addr}) -> übersprungen")
                continue
            # TLD muss bekannt sein (verhindert Encoding-Müll wie "nivzrisig"/"decrsfe",
            # der bei jedem Lauf einen Sendeslot verbrennt und bei Strato 521 wirft).
            # Mallwitz-Fall 03.09.: elmcha@r-utneodegkwt-lmales.nivzrisig
            COMMON_TLDS = {
                "de", "com", "net", "org", "eu", "info", "biz", "online", "store",
                "site", "tech", "berlin", "gmbh", "co", "io", "ai", "app", "dev",
                "cloud", "digital", "solutions", "services", "agency", "consulting",
                "at", "ch", "uk", "nl", "fr", "it", "es", "pl", "se", "no", "dk",
                "fi", "cz", "sk", "hu", "ro", "bg", "gr", "pt", "be", "lu", "li",
                "im", "me", "tv", "cc", "ws", "xyz", "top", "club", "shop", "design",
                "marketing", "media", "systems", "management", "engineering",
                "company", "group", "team", "center", "care", "works", "build",
                "construction", "contractors", "haus", "immobilien", "kaufen",
                "versicherung", "restaurant", "cafe", "photography", "gallery",
                "fitness", "health", "dental", "law", "legal", "tax", "finance",
                "capital", "ltd", "pro", "one", "page", "link", "live", "life",
                # Deutsche/österreichische/schweizer Geo-TLDs (echte Adressen!)
                "ruhr", "bayern", "koeln", "cologne", "hamburg", "muenchen",
                "frankfurt", "stuttgart", "dortmund", "duesseldorf", "wien",
                "zuerich", "zurich", "tirol", "saarland", "nrw", "ruhr",
                "sachsen", "thueringen", "berlin",
            }
            tld = domain.rsplit(".", 1)[-1].lower()
            if tld not in COMMON_TLDS:
                print(f"  SKIP {company}: unbekannte TLD ({tld}) bei ({email_addr}) -> übersprungen")
                continue

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
                    elif status == "followup_7days_sent" and days_since >= 14:
                        lead["next_action"] = "followup_14days"
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
    # Primär: Strato SMTP via send_mail.py (wie Microsite-Pipeline, funktioniert
    # nachweislich). Gmail-OAuth (google_api.py) ist dort nur Fallback und wird
    # vom Skript selbst probiert, wenn Strato scheitert.
    send_mail_py = HERMES_HOME / ".." / "werkspree" / "microsites" / "pipeline" / "send_mail.py"
    if not send_mail_py.exists():
        send_mail_py = Path("/Users/anton/werkspree/microsites/pipeline/send_mail.py")
    cmd = [
        "python", str(send_mail_py),
        "--to", to,
        "--subject", subject,
        "--body-text", body,
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

    sent_ok = 0
    for lead in eligible:
        action = lead.get("next_action", "initial")
        template = templates.get(action, templates["initial"])

        company = lead["company_name"]
        to = lead.get("verified_email") or lead.get("email") or sent.get(company, {}).get("email", "")
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

        # A/B-Betreffzeilen (seit 03.09.): Variante deterministisch pro Firma
        # wählen (gleiche Firma -> immer gleiche Variante), damit Antwortraten
        # pro Variante später in sent_emails.json vergleichbar sind.
        import hashlib
        subject_variants = template.get("subject_variants") or []
        if subject_variants:
            variant_idx = int(hashlib.md5(company.encode("utf-8")).hexdigest(), 16) % len(subject_variants)
            subject = personalize(subject_variants[variant_idx], lead, sent)
        else:
            variant_idx = -1
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
                "subject_variant": variant_idx,
                "subject_used": subject,
            }
            sent_ok += 1
            print(f"  ✅ Sent to {company}")
        else:
            # Fehlschlag NICHT als Status speichern: Der bisherige Eintrag
            # (initial_sent/followup_3days_sent) bleibt stehen, damit der Lead
            # im nächsten Lauf erneut in den Follow-up-Zyklus kommt.
            print(f"  ❌ Failed: {output[:300]}")

    save_sent(sent)
    print(f"\nDone. {sent_ok} von {len(eligible)} Leads erfolgreich gesendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
