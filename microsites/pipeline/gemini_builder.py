#!/usr/bin/env python3
"""
Werkspree Gemini Microsite Builder
Nutzt Google Gemini API (kostenlos) für professionelle Microsites.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

ENV_PATH = Path.home() / ".hermes" / ".env"
OUT_DIR = Path(__file__).parent.parent / "sites"


def load_env():
    """Load ~/.hermes/.env into os.environ."""
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_api_key():
    """Get Google API key from environment."""
    load_env()
    return os.environ.get("GOOGLE_API_KEY", "")


def call_gemini(prompt, max_tokens=4000, temperature=0.3):
    """Call Gemini API to generate content."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
    }).encode()
    
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    
    if "candidates" in data and data["candidates"]:
        return data["candidates"][0]["content"]["parts"][0].get("text", "")
    return ""


def build_prompt(lead):
    """Build the prompt for Gemini."""
    name = lead.get("company_name") or lead.get("name", "Ihr Betrieb")
    branch = lead.get("segment", "")
    city = lead.get("city") or lead.get("region", "Brandenburg")
    phone = lead.get("phone", "")
    email = lead.get("email", "")
    address = lead.get("address", "")
    about = lead.get("about", "")
    products = lead.get("products", [])
    hours = lead.get("opening_hours", {})
    owner = lead.get("owner", "")
    
    # Format products
    if products and isinstance(products[0], (list, tuple)):
        prod_text = "\n".join(f"- {p[0]}: {p[1] if len(p)>1 else ''}" for p in products[:6])
    elif products:
        prod_text = "\n".join(f"- {p}" for p in products[:6])
    else:
        prod_text = ""
    
    # Format hours
    hours_text = ""
    days_map = {"Mo": "Montag", "Di": "Dienstag", "Mi": "Mittwoch", "Do": "Donnerstag", "Fr": "Freitag", "Sa": "Samstag", "So": "Sonntag"}
    if hours:
        for k, v in hours.items():
            hours_text += f"{days_map.get(k, k)}: {v}\n"
    
    # Branch hints
    branch_hints = {
        "maler": "Farben, Streichen, Fassaden, Tapezieren, Lackieren",
        "elektriker": "Installation, Reparatur, Notdienst, Smart Home, Solar",
        "dachdecker": "DachReparatur, Dachreinigung, Dächer, Solardach",
        "kosmetik": "Gesichtsbehandlung, Wimpern, Brows, Beratung",
        "friseur": "Haarschnitt, Färbung, Styling, Rasur",
    }
    hint = branch_hints.get(branch.lower(), "")
    
    prompt = f"""Du baust eine professionelle Microsite für folgenden Betrieb:

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
Erstelle eine vollständige, professionelle HTML5-Seite mit:
- Inline CSS im <style>-Tag
- Farbpalette passend zur Branche (z.B. Maler = dunkelblau/orange)
- Sections: Header, Über uns, Leistungen (Karten), Kontakt, Footer
- Telefon als tel:-Link, E-Mail als mailto:-Link
- Mobil-optimiert
- KEINE Platzhalter, kein Lorem Ipsum, kein Markdown
- Die Antwort beginnt mit <!DOCTYPE html> und endet mit </html>"""
    return prompt


def extract_html(text):
    """Extract HTML from response."""
    if not text:
        return None
    m = re.search(r"<html[\s\S]*?</html>", text, re.IGNORECASE)
    if m:
        return m.group(0)
    m = re.search(r"<!DOCTYPE[\s\S]*?</html>", text, re.IGNORECASE)
    if m:
        return m.group(0)
    return None


def is_valid_html(html):
    """Check if response is valid HTML."""
    if not html:
        return False
    if not re.search(r"<html[\s\S]*?</html>", html, re.IGNORECASE):
        return False
    if not re.search(r"<body[\s\S]*?</body>", html, re.IGNORECASE):
        return False
    if "{{" in html or "}}" in html:
        return False
    platzhalter = ["Max Mustermann", "Musterstraße", "Hier steht", "Beispiel", "Lorem ipsum"]
    for p in platzhalter:
        if p.lower() in html.lower():
            return False
    return True


def generate_microsite(lead, output_path):
    """Generate microsite with Gemini API."""
    prompt = build_prompt(lead)
    
    for attempt in range(3):
        try:
            raw = call_gemini(prompt)
            html = extract_html(raw)
            if is_valid_html(html):
                output_path.write_text(html, encoding="utf-8")
                return True
        except Exception as e:
            print(f"  Gemini-Fehler (Versuch {attempt+1}): {e}")
    
    return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 gemini_builder.py <lead.json>")
        sys.exit(1)
    
    lead_path = Path(sys.argv[1])
    lead = json.loads(lead_path.read_text())
    
    name = lead.get("company_name") or lead.get("name", "lead")
    slug = name.lower().replace(" ", "-")[:40]
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    
    success = generate_microsite(lead, out / "index.html")
    if success:
        print(f"✓ Microsite erstellt: {out / 'index.html'}")
    else:
        print("✗ Gemini-Build fehlgeschlagen")
        sys.exit(1)
