#!/usr/bin/env python3
"""Werkspree A/B-Test E-Mail-Sender.

Wählt zufällig ein Template aus den Varianten:
- ab_test_a (verbessert, persönlich)
- ab_test_b1 (Preis-Vergleich + Social Proof)
- ab_test_b2 (Kontrast / Persönlich / Warum ich)
- ab_test_b3 (Problembewusst + Direkt)

Und verfolgt, welche Variante an welchen Lead gesendet wurde.
"""
import json
import os
import base64
import urllib.request
import urllib.error
import urllib.parse
import random
import sys
from pathlib import Path
from email.mime.text import MIMEText

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
BUILT = DATA / "microsites_built.json"
SENT = DATA / "microsite_sent_emails.json"
TEMPLATE = BASE / "email_templates_microsite.json"
AB_LOG = DATA / "ab_test_results.json"

TOKEN_PATHS = [
    Path.home() / ".hermes" / "google_token.json",
    BASE / "google_token.json",
    Path.home() / "google_token.json",
]
SENDER = "Finn Werksby <a2807d@gmail.com>"

# Templates für A/B-Test (b1-b3 + a)
AB_TEMPLATES = ["ab_test_a", "ab_test_b1", "ab_test_b2", "ab_test_b3"]


def find_token():
    for p in TOKEN_PATHS:
        if p.exists():
            return p
    return None


def get_access_token(token_path):
    raw = json.loads(token_path.read_text())
    access = raw.get("access_token")
    refresh = raw.get("refresh_token")
    client_id = raw.get("client_id")
    client_secret = raw.get("client_secret")
    exp = raw.get("expiry") or raw.get("expires_at") or raw.get("expires_in")
    import time
    expired = False
    if isinstance(exp, (int, float)):
        expired = time.time() >= float(exp) - 60
    if access and not expired:
        return access
    if refresh and client_id and client_secret:
        body = urllib.parse.urlencode({
            "client_id": client_id, "client_secret": client_secret,
            "refresh_token": refresh, "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token",
            data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            resp = urllib.request.urlopen(req, timeout=30).read()
            tok = json.loads(resp)
            new_access = tok["access_token"]
            raw["access_token"] = new_access
            if "expires_in" in tok:
                raw["expiry"] = time.time() + tok["expires_in"]
            token_path.write_text(json.dumps(raw, indent=2))
            return new_access
        except Exception as e:
            print(f"  [WARN] Token-Refresh fehlgeschlagen: {e}")
    return access


def send_gmail(access_token, to, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to
    msg["from"] = SENDER
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = json.dumps({"raw": raw}).encode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=payload,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())


def load_sent():
    if SENT.exists():
        return json.loads(SENT.read_text())
    return {}


def load_ab_log():
    if AB_LOG.exists():
        return json.loads(AB_LOG.read_text())
    return {"sends": [], "stats": {}}


def save_ab_log(log):
    # Stats aktualisieren
    stats = {}
    for s in log["sends"]:
        tpl = s.get("template", "unknown")
        if tpl not in stats:
            stats[tpl] = {"sent": 0, "opens": 0, "replies": 0}
        stats[tpl]["sent"] += 1
    log["stats"] = stats
    AB_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))


def load_opt_out():
    opt = DATA / "opt_out.json"
    if opt.exists():
        return json.loads(opt.read_text())
    return {"emails": [], "domains": [], "companies": []}


def is_opted_out(email, company):
    opt = load_opt_out()
    email_lower = (email or "").lower()
    company_lower = (company or "").lower()
    if email_lower in [e.lower() for e in opt.get("emails", [])]:
        return True
    domain = email_lower.split("@")[-1] if "@" in email_lower else ""
    if domain in [d.lower() for d in opt.get("domains", [])]:
        return True
    if company_lower in [c.lower() for c in opt.get("companies", [])]:
        return True
    return False


def pick_template(lead_slug):
    """Wählt ein Template per Zufall — aber weighted: a=25%, b1=25%, b2=25%, b3=25%."""
    return random.choice(AB_TEMPLATES)


def main():
    if not BUILT.exists():
        print("Keine microsites_built.json gefunden.")
        return
    built = json.loads(BUILT.read_text())
    items = built if isinstance(built, list) else [built]
    target = None
    for it in reversed(items):
        if it.get("success") and it.get("site_url") and it.get("email_verified") == "yes":
            target = it
            break
    if not target:
        print("Kein erfolgreicher, qualifizierter Build mit E-Mail gefunden.")
        return

    company = target.get("company_name", "Ihr Unternehmen")
    url = target.get("site_url", "")
    to = target.get("email", "")
    region = target.get("region") or target.get("city", "Ihrer Region")
    slug = target.get("slug", company.lower()[:20])
    if not to:
        print("Keine Ziel-E-Mail im Build-Datensatz.")
        return

    # Opt-out prüfen
    if is_opted_out(to, company):
        print(f"⚠️  {company} ({to}) ist auf der Opt-out-Liste — übersprungen.")
        return

    # Schon gesendet?
    sent = load_sent()
    key = f"{company}||{to}"
    if key in sent:
        print(f"Bereits versendet an {to} ({sent[key].get('sent_at')}) — übersprungen.")
        return

    # Template wählen
    template_key = pick_template(slug)
    templates = json.loads(TEMPLATE.read_text())
    tpl = templates[template_key]
    
    subject = tpl["subject"].replace("{COMPANY}", company).replace("{REGION}", region)
    body = tpl["body"].replace("{COMPANY}", company).replace("{REGION}", region).replace("{SITE_URL}", url)
    if "opt_out" in tpl:
        body += f"\n\n{tpl['opt_out']}"

    token_path = find_token()
    if not token_path:
        print("Kein google_token.json gefunden — Versand nicht möglich.")
        return
    access = get_access_token(token_path)
    if not access:
        print("Kein gültiges Access-Token.")
        return

    print(f"Versende A/B-Test-Mail ({template_key}) an {to} ...")
    try:
        res = send_gmail(access, to, subject, body)
        msg_id = res.get("id")
        import datetime
        now = datetime.datetime.now().isoformat(timespec="seconds")
        sent[key] = {
            "company_name": company, "email": to, "site_url": url,
            "subject": subject, "sent_at": now, "gmail_message_id": msg_id,
            "status": "sent", "template": template_key, "ab_group": "b" if template_key.startswith("ab_test_b") else "a",
        }
        SENT.write_text(json.dumps(sent, indent=2, ensure_ascii=False))
        
        # A/B-Log aktualisieren
        ab_log = load_ab_log()
        ab_log["sends"].append({
            "company": company, "email": to, "template": template_key,
            "sent_at": now, "subject": subject, "gmail_message_id": msg_id,
        })
        save_ab_log(ab_log)
        
        print(f"  ✅ Gesendet ({template_key}). Gmail-ID: {msg_id}")
        print(f"  📊 A/B-Statistik: {json.dumps(ab_log['stats'], ensure_ascii=False)}")
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP-Fehler {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        print(f"  ❌ Fehler: {e}")


if __name__ == "__main__":
    main()
