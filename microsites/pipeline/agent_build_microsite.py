#!/usr/bin/env python3
"""Werkspree Microsite-Builder — AGENT-Modus.

Statt eines starren Templates baut dieser Agent pro Lead eine EIGENSTÄNDIGE,
ansprechende Microsite. Er bekommt die echten Lead-Daten (Firma, Branche, Stadt,
Telefon, Öffnungszeiten, evtl. Beschreibung aus GelbeSeiten) und lässt ein LLM
eine vollständige, in sich geschlossene HTML-Datei generieren — mit passender
Farbskala, Struktur und Inhalten für GENAU diesen Betrieb.

Input:  Lead-JSON (--lead)
Output: microsites/sites/<slug>/index.html  +  site_url im Lead-JSON

Modell: OpenRouter (günstiges Modell, siehe OPENROUTER_MODEL).
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

PIPE = Path(__file__).parent
ROOT = PIPE.parent  # .../microsites
OUT_DIR = ROOT / "sites"  # .../microsites/sites

# OpenRouter-Config aus .env
import os
ENV_PATH = Path.home() / ".hermes" / ".env"
OPENROUTER_KEY = ""
OPENROUTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"  # einzig verfuegbares Modell mit diesem Key
for line in ENV_PATH.read_text().splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        OPENROUTER_KEY = line.split("=", 1)[1].strip()
    if line.startswith("OPENROUTER_MODEL="):
        OPENROUTER_MODEL = line.split("=", 1)[1].strip()


SYSTEM_PROMPT = """Du bist ein erfahrener Webdesigner für kleine Handwerks- und Dienstleistungsbetriebe in Brandenburg/Berlin.
Baue eine einzelne, in sich geschlossene HTML-Datei (eine Datei, alles inline: CSS im <style>, kein externes JS, keine externen Fonts/Libraries außer Google Fonts optional).
Die Seite muss ansprechend, modern, mobil-optimiert sein und GENAU zu diesem einen Betrieb passen.

WICHTIG — Design-Anforderungen:
- Wähle eine FARBPALETTE, die zur Branche passt UND EINZIGARTIG ist (z.B. Kosmetik = sanfte Pastell/Rosé-Töne, Kfz = dunkel/technisch/Orange, Reinigung = frisches Cyan/Weiß, Friseur = modern/Violett).
  Verwende NICHT die Standard-Bäckerei-Farben (cream/brown/gold) — die sind verboten.
- EIGENE, kreative CSS-Struktur (kein Copy-Paste eines Templates). Header, Sections, Cards, Footer selbst gestalten.
- Klare Sections: Header mit Firmenname + Tagline, Über-uns (mit dem echten Text), Leistungen (als Karten mit Titel+Beschreibung), Öffnungszeiten (Tabelle), Kontakt (Adresse, Telefon-Tel-Link, E-Mail-Mailto-Link).
- Footer mit "Demo-Website von Werkspree (KI-Automatisierung)".

INHALTE:
- Nutze NUR die echten Lead-Daten. Wenn "Beschreibung" oder "Leistungen" offensichtlicher Spam/Menü-Text ist (z.B. "Suchen", "Service", "Gelbe Seiten", "FÜR SIE", "Ratgeber", Logo-Alt-Texte), DANN IGNORIERE diese und schreibe stattdessen eine kurze, plausible, branchentypische Beschreibung selbst.
- Keine Platzhalter wie {{XYZ}} — alle Inhalte echt füllen.
- Kein englischer Text, keine erfundenen Zitate, keine Fake-Bewertungen, keine erfundenen Inhaber.
- Reine, valide HTML5. Kein Markdown, kein Code-Block-Wrapper.

Gib NUR den HTML-Code zurück, sonst nichts."""


def build_prompt(lead):
    name = lead.get("company_name", "Ihr Betrieb")
    branch = lead.get("segment", "")
    city = lead.get("city", lead.get("region", "Brandenburg"))
    phone = lead.get("phone", "")
    email = lead.get("email", "")
    address = lead.get("address", "")
    about = lead.get("about", "")
    products = lead.get("products", [])
    hours = lead.get("opening_hours", {})
    owner = lead.get("owner", "")

    prod_text = ""
    if products:
        if isinstance(products[0], (list, tuple)):
            prod_text = ", ".join(p[0] for p in products)
        else:
            prod_text = ", ".join(products)

    hours_text = ""
    if hours:
        days = {"Mo": "Montag", "Di": "Dienstag", "Mi": "Mittwoch", "Do": "Donnerstag",
                "Fr": "Freitag", "Sa": "Samstag", "So": "Sonntag"}
        for k, v in hours.items():
            hours_text += f"{days.get(k, k)}: {v}\n"

    user = f"""Firmenname: {name}
Branche: {branch}
Stadt: {city}
Inhaber: {owner or '—'}
Adresse: {address or '—'}
Telefon: {phone or '—'}
E-Mail: {email or '—'}

Beschreibung (echt, aus GelbeSeiten, falls leer: erfinde eine kurze, plausible, branchentypische Beschreibung):
{about or '—'}

Leistungen/Sortiment: {prod_text or '—'}

Öffnungszeiten:
{hours_text or '—'}

Baue die Microsite."""
    return user


def call_openrouter(system, user):
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY nicht gesetzt")
    body = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
        "max_tokens": 4000,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://werkspree.bki-de.de",
            "X-Title": "Werkspree Microsite Agent",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def extract_html(text):
    # Falls Modell doch Code-Block wrapt
    m = re.search(r"<html[\s\S]*?</html>", text, re.IGNORECASE)
    if m:
        return m.group(0)
    if "<!DOCTYPE" in text or "<html" in text:
        return text
    return text


def slugify(name):
    s = name.lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:40]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", help="Pfad zu Lead-JSON")
    args = ap.parse_args()
    if not args.lead:
        print("ERROR: --lead erforderlich")
        sys.exit(2)
    lead = json.loads(Path(args.lead).read_text())

    # Qualifizierungs-Check (Sicherheit, falls direkt aufgerufen)
    if lead.get("email_verified") != "yes":
        print("ERROR: Lead nicht verifiziert")
        sys.exit(2)

    slug = lead.get("slug") or slugify(lead.get("company_name", "lead"))
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)

    print(f"  Agent baut Site für: {lead.get('company_name')} (Branch: {lead.get('segment')})")
    user_prompt = build_prompt(lead)
    try:
        html = call_openrouter(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"  Agent-Fehler: {e}")
        sys.exit(2)

    html = extract_html(html)
    if "{{" in html or "}}" in html:
        print("  WARN: Template-Platzhalter übrig — Builder unvollständig")
        sys.exit(2)

    (out / "index.html").write_text(html, encoding="utf-8")
    site_url = f"https://werkspree.bki-de.de/microsites/sites/{slug}/"
    lead["site_url"] = site_url
    Path(args.lead).write_text(json.dumps(lead, ensure_ascii=False, indent=2))
    print(f"  Site gebaut: {out / 'index.html'} -> {site_url}")
    sys.exit(0)


if __name__ == "__main__":
    main()
