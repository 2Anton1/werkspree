#!/usr/bin/env python3
"""
Werkspree Microsite-Builder — AGENT v2 mit garantiertem HTML-Output.

NEU in v2:
- Strikerer Prompt: Keine Platzhalter, kein Plan-Text
- Daten-Anreicherung vor dem Build
- Fallback-Template falls LLM versagt
- Nutzt 'name' aus Places API (nicht 'company_name')
"""
import argparse
import json
import re
import sys
import urllib.request
import os
from pathlib import Path

from scrapling.fetchers import Fetcher

PIPE = Path(__file__).parent
ROOT = PIPE.parent
OUT_DIR = ROOT / "sites"

# OpenRouter
ENV_PATH = Path.home() / ".hermes" / ".env"
OPENROUTER_KEY = ""
OPENROUTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
for line in ENV_PATH.read_text().splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        OPENROUTER_KEY = line.split("=", 1)[1].strip()
    if line.startswith("OPENROUTER_MODEL="):
        OPENROUTER_MODEL = line.split("=", 1)[1].strip()


def enrich_lead(lead):
    """Anreichern der Lead-Daten aus verschiedenen Quellen."""
    name = lead.get("company_name") or lead.get("name", "")
    lead["company_name"] = name
    
    # Fehlende Felder aus GelbeSeiten versuchen
    if not lead.get("about") or not lead.get("products"):
        gs_data = scrape_gelbeseiten_for_lead(name, lead.get("region", ""))
        if gs_data:
            lead.setdefault("about", gs_data.get("about", ""))
            lead.setdefault("products", gs_data.get("products", []))
            lead.setdefault("opening_hours", gs_data.get("opening_hours", {}))
            if not lead.get("owner") and gs_data.get("owner"):
                lead["owner"] = gs_data["owner"]
    
    return lead


def scrape_gelbeseiten_for_lead(name, region):
    """Suche auf GelbeSeiten nach Firmenprofil. Nutzt Scrapling Fetcher."""
    try:
        from urllib.parse import quote
        query = f"{name} {region}"
        search_url = f"https://www.gelbeseiten.de/suche/{quote(query)}"
        page = Fetcher.get(search_url, timeout=15)
        if page.status != 200:
            return {}

        # Profil-Link finden
        for a in page.css("a[href]"):
            href = a.attrib.get("href", "")
            if "/gsbiz/" in href:
                if not href.startswith("http"):
                    href = "https://www.gelbeseiten.de" + href
                return scrape_gelbeseiten_profile(href)
    except Exception:
        pass
    return {}


def scrape_gelbeseiten_profile(url):
    """GelbeSeiten-Profil scrapen. Nutzt Scrapling Fetcher."""
    try:
        page = Fetcher.get(url, timeout=15)
        if page.status != 200:
            return {}

        details = {}

        # Beschreibung
        desc = page.css('[class*="description"]') or page.css('[class*="beschreibung"]') or page.css('[class*="profil"]')
        if desc:
            details["about"] = desc[0].get_all_text(strip=True)[:500]

        # Öffnungszeiten
        hours = {}
        text = page.get_all_text()
        for tag in ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]:
            m = re.search(rf'{tag}\w*\.?\s*[\.:-]?\s*(\d{{1,2}}[.:]\d{{2}}\s*[-–]\s*\d{{1,2}}[.:]\d{{2}})', text)
            if m:
                hours[tag] = m.group(1).replace(".", ":")
        if hours:
            details["opening_hours"] = hours

        # Inhaber
        inh = re.search(r'(?:Inhaber|Geschäftsführer)[\.:-]\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){0,3})', text)
        if inh:
            details["owner"] = inh.group(1).strip()

        return details
    except Exception:
        return {}


def build_prompt(lead):
    name = lead.get("company_name", "Ihr Betrieb")
    branch = lead.get("segment", "")
    city = lead.get("city") or lead.get("region", "Brandenburg")
    phone = lead.get("phone", "")
    email = lead.get("email", "")
    address = lead.get("address", "")
    about = lead.get("about", "")
    products = lead.get("products", [])
    hours = lead.get("opening_hours", {})
    owner = lead.get("owner", "")
    
    # Produkte formatieren
    if products and isinstance(products[0], (list, tuple)):
        prod_text = "\n".join(f"- {p[0]}: {p[1] if len(p)>1 else ''}" for p in products[:6])
    elif products:
        prod_text = "\n".join(f"- {p}" for p in products[:6])
    else:
        prod_text = ""
    
    # Öffnungszeiten formatieren
    hours_text = ""
    days_map = {"Mo": "Montag", "Di": "Dienstag", "Mi": "Mittwoch", "Do": "Donnerstag", "Fr": "Freitag", "Sa": "Samstag", "So": "Sonntag"}
    if hours:
        for k, v in hours.items():
            hours_text += f"{days_map.get(k, k)}: {v}\n"
    
    # Branchen-Hinweise
    branch_hints = {
        "maler": "Farben, Streichen, Fassaden, Tapezieren, Lackieren",
        "elektriker": "Installation, Reparatur, Notdienst, Smart Home, Solar",
        "dachdecker": "DachReparatur, Dachreinigung, Dächer, Solardach",
        "kosmetik": "Gesichtsbehandlung, Wimpern, Brows, Beratung",
        "friseur": "Haarschnitt, Färbung, Styling, Rasur",
    }
    hint = branch_hints.get(branch.lower(), "")
    
    user = f"""Du baust eine professionelle Microsite für folgenden Betrieb:

**Firma:** {name}
**Branche:** {branch} {f'(Typische Leistungen: {hint})' if hint else ''}
**Stadt:** {city}
**Adresse:** {address or 'Nicht verfügbar'}
**Telefon:** {phone or 'Nicht verfügbar'}
**E-Mail:** {email or 'Nicht verfügbar'}
**Inhaber:** {owner or 'Nicht verfügbar'}

**Über uns (echter Text):**
{about or 'Nicht verfügbar'}

**Leistungen:**
{prod_text or 'Nicht verfügbar'}

**Öffnungszeiten:**
{hours_text or 'Nicht verfügbar'}

---
BAUE JETZT die HTML-Seite. Fülle ALLE Felder mit den echten Daten oben.
Wenn ein Feld "Nicht verfügbar" ist, lass es weg oder schreibe "Auf Anfrage".
KEINE Platzhalter wie {{XYZ}}, "Hier steht...", "Beispiel..."."""
    return user


SYSTEM_PROMPT = """Du bist Webdesigner. Baue eine vollständige HTML5-Seite (deutsch, mobil-optimiert, inline CSS).

REGELN:
1. Antworte AUSSCHLIESSLICH mit HTML — beginnt mit <!DOCTYPE html>, endet mit </html>
2. KEIN Markdown, KEIN Code-Block (```), KEIN Plan, KEIN Text außerhalb des HTML
3. Nutze die ECHTEN Daten aus der Anfrage — KEINE Platzhalter, KEINE Erfindungen
4. Wenn Daten fehlen: weglassen oder "Auf Anfrage" schreiben — NIE "Max Mustermann" oder "Musterstraße"
5. Farbpalette passend zur Branche wählen
6. Sections: Header, Über uns, Leistungen (Karten), Kontakt, Footer mit "Demo-Website von Werkspree"
7. Telefon als tel:-Link, E-Mail als mailto:-Link"""


def call_openrouter(system, user):
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY nicht gesetzt")
    body = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
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
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def extract_html(text):
    """Extrahiere HTML aus der Antwort."""
    if not text:
        return None
    # Suche <html>...</html>
    m = re.search(r"<html[\s\S]*?</html>", text, re.IGNORECASE)
    if m:
        return m.group(0)
    # Suche <!DOCTYPE ... </html>
    m = re.search(r"<!DOCTYPE[\s\S]*?</html>", text, re.IGNORECASE)
    if m:
        return m.group(0)
    return None


def is_valid_html(html):
    """Prüfe ob echtes HTML (kein Plan-Text)."""
    if not html:
        return False
    if not re.search(r"<html[\s\S]*?</html>", html, re.IGNORECASE):
        return False
    if not re.search(r"<body[\s\S]*?</body>", html, re.IGNORECASE):
        return False
    if "{{" in html or "}}" in html:
        return False
    # Prüfe auf typische Platzhalter
    platzhalter = ["Max Mustermann", "Musterstraße", "Hier steht", "Beispiel", "Lorem ipsum"]
    for p in platzhalter:
        if p.lower() in html.lower():
            return False
    return True


def build_fallback_template(lead):
    """Fallback: Statisches Template mit echten Daten (garantiert funktionsfähig)."""
    name = lead.get("company_name", "Ihr Betrieb")
    branch = lead.get("segment", "")
    city = lead.get("city") or lead.get("region", "")
    phone = lead.get("phone", "")
    email = lead.get("email", "")
    address = lead.get("address", "")
    about = lead.get("about", "") or f"{name} ist ein etablierter Betrieb in {city}."
    owner = lead.get("owner", "")
    hours = lead.get("opening_hours", {})
    products = lead.get("products", [])
    
    # Telefon-Link
    phone_link = f'<a href="tel:{phone}">{phone}</a>' if phone else '<span>Auf Anfrage</span>'
    email_link = f'<a href="mailto:{email}">{email}</a>' if email else '<span>Auf Anfrage</span>'
    
    # Öffnungszeiten-Tabelle
    hours_rows = ""
    days_map = {"Mo": "Montag", "Di": "Dienstag", "Mi": "Mittwoch", "Do": "Donnerstag", "Fr": "Freitag", "Sa": "Samstag", "So": "Sonntag"}
    for k, v in hours.items():
        hours_rows += f"<tr><td>{days_map.get(k, k)}</td><td>{v}</td></tr>\n"
    if not hours_rows:
        hours_rows = "<tr><td colspan='2'>Auf Anfrage</td></tr>"
    
    # Produkte-Karten
    cards = ""
    if products:
        for p in products[:6]:
            if isinstance(p, (list, tuple)):
                title, desc = p[0], p[1] if len(p) > 1 else ""
            else:
                title, desc = p, ""
            cards += f'<div class="card"><h3>{title}</h3><p>{desc}</p></div>\n'
    else:
        cards = '<div class="card"><h3>Leistungen</h3><p> Auf Anfrage</p></div>'
    
    # Branchen-Farben
    branch_colors = {
        "maler": ("#2c3e50", "#e67e22"),
        "elektriker": ("#1a237e", "#ffc107"),
        "dachdecker": ("#3e2723", "#ff9800"),
        "kosmetik": ("#880e4f", "#f48fb1"),
        "friseur": ("#4a148c", "#ce93d8"),
    }
    primary, accent = branch_colors.get(branch.lower(), ("#122c4d", "#1f9d74"))
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>
<style>
:root {{ --primary: {primary}; --accent: {accent}; --bg: #fafafa; --surface: #fff; --text: #1d2939; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
header {{ background:linear-gradient(135deg,var(--primary),var(--accent)); color:#fff; padding:4rem 1.5rem; text-align:center; }}
header h1 {{ font-size:2.2rem; margin-bottom:.5rem; }}
header p {{ font-size:1.2rem; opacity:.95; }}
.cta {{ margin-top:1.5rem; display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; }}
.btn {{ background:#fff; color:var(--primary); padding:.7rem 1.4rem; border-radius:30px; text-decoration:none; font-weight:600; }}
section {{ max-width:900px; margin:0 auto; padding:3rem 1.5rem; }}
h2 {{ color:var(--primary); margin-bottom:1rem; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1.5rem; }}
.card {{ background:var(--surface); border-radius:12px; padding:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,.06); }}
.card h3 {{ color:var(--accent); margin-bottom:.5rem; }}
table {{ width:100%; border-collapse:collapse; margin-top:1rem; }}
th,td {{ text-align:left; padding:.6rem; border-bottom:1px solid #eee; }}
.contact-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:2rem; }}
footer {{ background:var(--primary); color:#fff; text-align:center; padding:2rem 1.5rem; font-size:.9rem; }}
a {{ color:var(--primary); }}
</style>
</head>
<body>
<header>
  <h1>{name}</h1>
  <p>{branch} in {city}</p>
  <div class="cta">
    <a class="btn" href="tel:{phone}">Anrufen</a>
    <a class="btn" href="#kontakt">Kontakt</a>
  </div>
</header>
<section>
  <h2>Über uns</h2>
  <p>{about}</p>
</section>
<section>
  <h2>Unsere Leistungen</h2>
  <div class="cards">{cards}</div>
</section>
<section>
  <h2>Öffnungszeiten</h2>
  <table><tbody>{hours_rows}</tbody></table>
</section>
<section id="kontakt">
  <h2>Kontakt & Anfahrt</h2>
  <div class="contact-grid">
    <div>
      <p><strong>Adresse</strong></p>
      <p>{address or city}</p>
      {"<p style='margin-top:1rem;'><strong>Inhaber:</strong> " + owner + "</p>" if owner else ""}
    </div>
    <div>
      <p><strong>Direktkontakt</strong></p>
      <p>{phone_link}</p>
      <p>{email_link}</p>
    </div>
  </div>
</section>
<footer>
  <p>{name} · {city}</p>
  <p style="margin-top:1rem; opacity:.7;">Demo-Website von Werkspree (KI-Automatisierung)</p>
</footer>
</body>
</html>"""
    return html


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
    
    # Qualifizierungs-Check
    ev = lead.get("email_verified", "")
    if str(ev).lower() not in ("yes", "true", "1"):
        print("ERROR: Lead nicht verifiziert")
        sys.exit(2)
    
    # Name sicherstellen
    name = lead.get("company_name") or lead.get("name", "lead")
    lead["company_name"] = name
    
    slug = lead.get("slug") or slugify(name)
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    
    print(f"  Agent baut Site für: {name} (Branch: {lead.get('segment', '')})")
    
    # Daten anreichern
    print("  Anreichern der Lead-Daten...")
    lead = enrich_lead(lead)
    
    # Build (Fallback Template - garantiert funktionsfähig mit echten Daten)
    html = build_fallback_template(lead)
    source = "Fallback-Template"
    
    (out / "index.html").write_text(html, encoding="utf-8")
    site_url = f"https://werkspree.bki-de.de/microsites/sites/{slug}/"
    lead["site_url"] = site_url
    Path(args.lead).write_text(json.dumps(lead, ensure_ascii=False, indent=2))
    print(f"  Site gebaut: {out / 'index.html'} -> {site_url}")
    sys.exit(0)


if __name__ == "__main__":
    main()
