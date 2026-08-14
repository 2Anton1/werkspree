#!/usr/bin/env python3
"""Werkspree: Versendet die Microsite-Draft-Mail an einen qualifizierten Lead.

Nutzt Gmail OAuth (google_token.json) zum Senden im Namen von "Finn Werksby"
(a2807d@gmail.com). Token-Pfad flexibel: sucht in ~/.hermes/google_token.json
oder ./google_token.json. Kein External-Modul außer stdlib + google-auth falls
vorhanden; fällt auf manuellen HTTP-Refresh zurueck.

Nutzung:
    python3 send_microsite_mail.py
liest die letzte erfolgreiche Microsite aus data/microsites_built.json und
versendet an die verifizierte E-Mail (idempotent via microsite_sent_emails.json).
"""
import json
import os
import base64
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from email.mime.text import MIMEText

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
BUILT = DATA / "microsites_built.json"
SENT = DATA / "microsite_sent_emails.json"
TEMPLATE = BASE / "email_templates_microsite.json"

# Token + Credentials
TOKEN_PATHS = [
    Path.home() / ".hermes" / "google_token.json",
    BASE / "google_token.json",
    Path.home() / "google_token.json",
]
SENDER = "Finn Werksby <a2807d@gmail.com>"


def find_token():
    for p in TOKEN_PATHS:
        if p.exists():
            return p
    return None


def get_access_token(token_path):
    """Liest gespeichertes OAuth-Token; refreshes falls abgelaufen (best effort)."""
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
    # Refresh via Google endpoint
    if refresh and client_id and client_secret:
        body = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
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
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())


def load_sent():
    if SENT.exists():
        return json.loads(SENT.read_text())
    return {}


def main():
    if not BUILT.exists():
        print("Keine microsites_built.json gefunden.")
        return
    built = json.loads(BUILT.read_text())
    # Letzten erfolgreichen Build finden
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
    url = target["site_url"]
    to = target.get("email")
    if not to:
        print("Keine Ziel-E-Mail im Build-Datensatz.")
        return

    sent = load_sent()
    key = f"{company}||{to}"
    if key in sent:
        print(f"Bereits versendet an {to} ({sent[key].get('sent_at')}) — übersprungen.")
        return

    tpl = json.loads(TEMPLATE.read_text())["microsite_draft"]
    subject = tpl["subject"].replace("{company_name}", company)
    body = tpl["body"].replace("{company_name}", company).replace("{site_url}", url)
    # Opt-out-Satz sicherstellen
    if "abmelden" not in body.lower():
        body += "\n\nSie möchten keine weiteren Mails? Antworten Sie einfach mit 'Bitte keine Mails mehr'."

    token_path = find_token()
    if not token_path:
        print("Kein google_token.json gefunden — Versand nicht möglich.")
        return
    access = get_access_token(token_path)
    if not access:
        print("Kein gültiges Access-Token.")
        return

    print(f"Versende Microsite-Draft-Mail an {to} ...")
    try:
        res = send_gmail(access, to, subject, body)
        msg_id = res.get("id")
        sent[key] = {
            "company_name": company,
            "email": to,
            "site_url": url,
            "subject": subject,
            "sent_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
            "gmail_message_id": msg_id,
            "status": "sent",
        }
        SENT.write_text(json.dumps(sent, indent=2, ensure_ascii=False))
        print(f"  ✅ Gesendet. Gmail-Message-ID: {msg_id}")
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP-Fehler {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        print(f"  ❌ Fehler: {e}")


if __name__ == "__main__":
    main()
