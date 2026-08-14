#!/usr/bin/env python3
"""Werkspree zentraler Mail-Versand.

Primär: Strato SMTP (kontakt@werkspree.bki-de.de)
Fallback: Gmail OAuth (a2807d@gmail.com, Pseudonym Finn Werksby)

Usage:
  python3 send_mail.py --to EMPFAENGER --subject BETREFF --body DATEI.txt
  python3 send_mail.py --to EMPFAENGER --subject BETREFF --body-text "..." [--html]
  python3 send_mail.py --json microsite_payload.json   # Microsite-Draft-Mail
"""
import os, sys, json, argparse, smtplib, ssl, base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

ENV = Path.home() / '.hermes' / '.env'

def load_env():
    env = {}
    if ENV.exists():
        for line in ENV.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                env[k.strip()] = v.strip()
    return env

def load_gmail_token():
    p = Path.home() / '.hermes' / 'google_token.json'
    return p if p.exists() else None

def send_strato(to, subject, body, html=False, env=None):
    env = env or load_env()
    host = env.get('WERKSPREE_SMTP_HOST')
    user = env.get('WERKSPREE_SMTP_USER')
    pwd  = env.get('WERKSPREE_SMTP_PASS')
    port = int(env.get('WERKSPREE_SMTP_PORT', '465'))
    use_ssl = env.get('WERKSPREE_SMTP_SSL', 'true').lower() == 'true'
    from_addr = env.get('WERKSPREE_SMTP_FROM', user)
    if not (host and user and pwd):
        raise RuntimeError("Strato-Credentials unvollständig (WERKSPREE_SMTP_PASS fehlt?)")
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"Finn Werksby <{from_addr}>"
    msg['To'] = to
    msg.attach(MIMEText(body, 'html' if html else 'plain', 'utf-8'))
    if use_ssl:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=ctx) as s:
            s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
    return f"strato:{from_addr}"

def send_gmail(to, subject, body, html=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    tok = load_gmail_token()
    if not tok:
        raise RuntimeError("Kein Gmail-Token")
    creds = Credentials.from_authorized_user_file(str(tok))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    service = build('gmail', 'v1', credentials=creds)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = "Finn Werksby <a2807d@gmail.com>"
    msg['To'] = to
    msg.attach(MIMEText(body, 'html' if html else 'plain', 'utf-8'))
    raw = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    res = service.users().messages().send(userId='me', body=raw).execute()
    return f"gmail:{res['id']}"

def send(to, subject, body, html=False):
    env = load_env()
    try:
        return send_strato(to, subject, body, html, env)
    except Exception as e:
        sys.stderr.write(f"[WARN] Strato fehlgeschlagen: {e}\n")
        return send_gmail(to, subject, body, html)

def microsite_mail(lead):
    url = lead['site_url']
    name = lead['company_name']
    subject = f"Kostenlose Demo-Website für {name} — fertig zum Ansehen"
    body = f"""Guten Tag,

wir haben für {name} eine kostenlose Demo-Website erstellt — als Beispiel, wie Ihr Betrieb online noch besser präsentiert werden kann.

Ansehen: {url}

Die Seite ist ein Entwurf, kein fertiges Produkt. Wenn Sie möchten, passen wir sie an Ihr Sortiment, Ihre Öffnungszeiten und Ihr Erscheinungsbild an — oder bauen etwas ganz anderes (z.B. automatische Rechnungsprüfung, Termin- oder Anfrageformulare).

Bei Interesse einfach antworten oder anrufen. Falls nicht — ignorieren Sie diese Mail einfach, keine weitere Nachricht folgt.

Viele Grüße
Finn Werksby
Werkspree — KI-Automatisierung für Handwerks- und Dienstleistungsbetriebe
"""
    return subject, body

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--to', required=False)
    ap.add_argument('--subject', required=False)
    ap.add_argument('--body', required=False)
    ap.add_argument('--body-text', required=False)
    ap.add_argument('--html', action='store_true')
    ap.add_argument('--json', required=False, help='Microsite-Lead-JSON mit site_url+company_name')
    args = ap.parse_args()

    if args.json:
        lead = json.loads(Path(args.json).read_text())
        subject, body = microsite_mail(lead)
        to = lead['email']
        rid = send(to, subject, body)
        print(f"GESENDET via {rid} -> {to}")
    elif args.to and (args.body or args.body_text):
        body = Path(args.body).read_text() if args.body else args.body_text
        rid = send(args.to, args.subject, body, args.html)
        print(f"GESENDET via {rid} -> {args.to}")
    else:
        ap.print_help()
        sys.exit(1)
