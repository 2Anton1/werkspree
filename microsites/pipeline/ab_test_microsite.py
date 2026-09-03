#!/usr/bin/env python3
"""
Werkspree Microsite-Builder v3 — A/B Test Version.

Verbesserungen v3:
- Hero-Section mit Gradient + Branchen-Icon
- Google Maps Embed (Adresse)
- Echte Öffnungszeiten als Tabelle
- Leistungen als Cards mit Icons
- Testimonials/Trust-Signal Section
- "Demo von Werkspree" Badge im Footer
- A/B-Test-Zuweisung (A=Kontrolle alt, B=verbessert v3)
"""
import argparse
import json
import re
import sys
import os
from pathlib import Path

PIPE = Path(__file__).parent
ROOT = PIPE.parent
OUT_DIR = ROOT / "sites"
DATA = PIPE / "data"

# A/B Test Config
AB_CONFIG_PATH = DATA / "ab_test_config.json"


def load_ab_config():
    if AB_CONFIG_PATH.exists():
        return json.loads(AB_CONFIG_PATH.read_text())
    return {"current_split": "b", "a_description": "Altes Template (Kontrolle)", "b_description": "Verbessertes v3 Template"}


def get_branch_colors(segment):
    colors = {
        "maler": ("#2c3e50", "#e67e22", "farbe", "🎨"),
        "elektriker": ("#1a237e", "#ffc107", "bolt", "⚡"),
        "dachdecker": ("#3e2723", "#ff9800", "home", "🏠"),
        "kosmetik": ("#880e4f", "#f48fb1", "spa", "💄"),
        "friseur": ("#4a148c", "#ce93d8", "cut", "✂️"),
        "heizung": ("#2C5F7F", "#A8C8E0", "fire", "🔥"),
        "tischler": ("#5D4037", "#A1887F", "wood", "🪵"),
        "zahnarzt": ("#4A9EAB", "#B8E0E6", "tooth", "🦷"),
        "baeckerei": ("#D4A574", "#FFF3E0", "bread", "🥖"),
        "gartenbau": ("#2E7D32", "#A5D6A7", "leaf", "🌱"),
        "reinigung": ("#1565C0", "#90CAF9", "clean", "🧹"),
        "metzgerei": ("#C62828", "#EF9A9A", "meat", "🥩"),
    }
    seg = (segment or "").lower()
    for key, val in colors.items():
        if key in seg:
            return val
    return ("#122c4d", "#1f9d74", "star", "✨")


def get_branch_services(segment):
    services = {
        "heizung": [("Heizungsbau", "Installation und Wartung von Heizungsanlagen"), ("Badsanierung", "Komplette Badrenovierung — von der Planung bis zur Montage"), ("Wartung", "Regelmäßige Wartung und Reparatur"), ("Notdienst", "Schnelle Hilfe bei Heizungsausfällen")],
        "sanitär": [("Sanitärinstallation", "Fachgerechte Installation sanitärer Anlagen"), ("Badrenovierung", "Moderne Bäder — bequem und funktional"), ("Wartung", "Regelmäßige Wartung und Reparatur")],
        "maler": [("Fassadenmalerei", "Witterungsbeständiger Außenanstrich"), ("Innenraumarbeiten", "Wände, Decken, Tapeten — sauber und präzise"), ("Lackieren", "Holz und Metall — langlebige Beschichtungen")],
        "elektriker": [("Elektroinstallation", "Sichere Installation nach VDE-Norm"), ("Reparatur", "Schnelle Fehlerbehebung und Wartung"), ("Smart Home", "Intelligente Steuerung für Licht, Heizung, Sicherheit")],
        "dachdecker": [("Dachdeckung", "Neue Dächer — langlebig und dicht"), ("Dachreparatur", "Schnelle Behebung von Undichtigkeiten"), ("Dachreinigung", "Moos und Algen entfernen — Dach pflegen")],
        "kosmetik": [("Gesichtsbehandlung", "Tiefenreinigung und Pflegemassagen"), ("Wimpern & Brows", "Lifting, Tinting und Shaping"), ("Beratung", "Individuelle Hautanalyse und Pflegeempfehlung")],
        "friseur": [("Haarschnitt", "Schnitt und Färbung nach Wunsch"), ("Styling", "Föhnfrisur und Hochsteckfrisuren"), ("Rasur", "Klassische Rasur mit Messer")],
        "tischler": [("Möbelbau", "Maßgefertigte Möbel nach Ihren Wünschen"), ("Türen & Fenster", "Reparatur und Neubau"), ("Innenausbau", "Regale, Treppen, Einbauten")],
        "zahnarzt": [("Zahnreinigung", "Professionelle Zahnreinigung"), ("Prophylaxe", "Vorsorge für gesunde Zähne"), ("Füllungen", "Hochwertige Restaurationen")],
        "gartenbau": [("Gartenpflege", "Rasenschnitt, Heckenschritt, Pflege"), ("Gartenanlage", "Neuanlage von Gärten und Beeten"), ("Pflasterarbeiten", "Wege und Terrassen")],
    }
    seg = (segment or "").lower()
    for key, val in services.items():
        if key in seg:
            return val
    return [("Leistungen", "Auf Anfrage")]


def get_branch_icon(segment):
    seg = (segment or "").lower()
    icons = {
        "heizung": "🔥", "sanitär": "🚿", "maler": "🎨", "elektriker": "⚡",
        "dachdecker": "🏠", "kosmetik": "💄", "friseur": "✂️", "tischler": "🪵",
        "zahnarzt": "🦷", "gartenbau": "🌱", "reinigung": "🧹", "metzgerei": "🥩",
        "baeckerei": "🥖", "bäcker": "🥖",
    }
    for key, val in icons.items():
        if key in seg:
            return val
    return "✨"


def slugify(name):
    s = name.lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:40]


print("Part 1 loaded OK")

def build_v3_html(lead):
    """Verbessertes v3 HTML-Template mit Hero, Maps, Icons, Trust-Signal."""
    name = lead.get("company_name", "Ihr Betrieb")
    branch = lead.get("segment", "")
    city = lead.get("city") or lead.get("region", "")
    phone = lead.get("phone", "")
    email_addr = lead.get("email", "")
    address = lead.get("address", "")
    about = lead.get("about", "")
    owner = lead.get("owner", "")
    hours = lead.get("opening_hours", {})
    products = lead.get("products", [])
    rating = lead.get("rating", "")
    reviews = lead.get("reviews", 0)
    
    primary, accent, _, icon = get_branch_colors(branch)
    services = get_branch_services(branch)
    if products and isinstance(products[0], (list, tuple)):
        for i, p in enumerate(products[:3]):
            if i < len(services):
                services[i] = (p[0], p[1] if len(p) > 1 else services[i][1])
    
    # Phone link
    phone_link = f'<a href="tel:{phone}" class="cta-btn">📞 Anrufen: {phone}</a>' if phone else ""
    # Email link
    email_link = f'<a href="mailto:{email_addr}" class="cta-btn2">✉️ E-Mail schreiben</a>' if email_addr else ""
    
    # Opening hours
    days_map = {"Mo": "Montag", "Di": "Dienstag", "Mi": "Mittwoch", "Do": "Donnerstag", "Fr": "Freitag", "Sa": "Samstag", "So": "Sonntag"}
    hours_rows = ""
    for k in ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]:
        v = hours.get(k, hours.get(days_map.get(k, k), ""))
        if v:
            hours_rows += f"<tr><td>{days_map[k]}</td><td>{v}</td></tr>"
    if not hours_rows:
        hours_rows = '<tr><td colspan="2" style="text-align:center;color:#888;">Auf Anfrage</td></tr>'
    
    # Services cards
    cards = ""
    for title, desc in services[:6]:
        cards += f'<div class="service-card"><div class="service-icon">{icon}</div><h3>{title}</h3><p>{desc}</p></div>'
    
    # About text
    if not about:
        about = f"{name} ist ein etablierter Betrieb in {city}. Mit Fachkompetenz und regionaler Erfahrung."
    
    # Maps embed
    maps_src = f"https://maps.google.com/maps?q={address or name + ' ' + city}&output=embed"
    
    # Rating
    rating_html = ""
    if rating:
        stars = "⭐" * int(float(rating))
        rating_html = f'<div class="rating">{stars} {rating} · {reviews} Bewertungen auf Google</div>'
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} | {branch} in {city}</title>
<meta name="description" content="{name} — Ihr Fachbetrieb für {branch} in {city}. Professionelle Arbeit, faire Preise, regional verwurzelt.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Poppins:wght@600;700;800&display=swap" rel="stylesheet">
<style>
:root {{ --primary:{primary}; --accent:{accent}; --bg:#fafafa; --surface:#fff; --text:#1d2939; --muted:#666; --radius:14px; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); line-height:1.7; }}
h1,h2,h3 {{ font-family:'Poppins',sans-serif; }}
/* HERO */
.hero {{ background:linear-gradient(135deg,var(--primary),var(--accent)); color:#fff; padding:3rem 1.5rem 4rem; text-align:center; position:relative; overflow:hidden; }}
.hero h1 {{ font-size:clamp(1.8rem,5vw,3rem); margin-bottom:.5rem; }}
.hero .branch {{ font-size:1.15rem; opacity:.9; }}
.hero .city-tag {{ display:inline-block; margin-top:.8rem; background:rgba(255,255,255,.15); padding:.3rem 1rem; border-radius:20px; font-size:.9rem; }}
.hero .icon-big {{ font-size:3rem; margin-bottom:.8rem; }}
.hero .rating {{ margin-top:.8rem; font-size:.95rem; background:rgba(255,255,255,.12); padding:.4rem 1rem; border-radius:20px; display:inline-block; }}
.cta-group {{ margin-top:1.5rem; display:flex; gap:.8rem; justify-content:center; flex-wrap:wrap; }}
.cta-btn,.cta-btn2 {{ background:#fff; color:var(--primary); padding:.7rem 1.4rem; border-radius:30px; text-decoration:none; font-weight:600; font-size:.95rem; transition:transform .2s; }}
.cta-btn2 {{ background:transparent; border:2px solid rgba(255,255,255,.4); color:#fff; }}
.cta-btn:hover,.cta-btn2:hover {{ transform:translateY(-2px); }}
/* SECTIONS */
section {{ max-width:900px; margin:0 auto; padding:3rem 1.5rem; }}
h2 {{ color:var(--primary); font-size:1.6rem; margin-bottom:1rem; }}
.section-intro {{ color:var(--muted); margin-bottom:1.5rem; }}
/* ABOUT */
.about-box {{ background:var(--surface); border-radius:var(--radius); padding:2rem; box-shadow:0 2px 16px rgba(0,0,0,.05); }}
/* SERVICES */
.services-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1.2rem; }}
.service-card {{ background:var(--surface); border-radius:var(--radius); padding:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,.04); transition:transform .2s; }}
.service-card:hover {{ transform:translateY(-3px); }}
.service-icon {{ font-size:1.8rem; margin-bottom:.6rem; }}
.service-card h3 {{ color:var(--primary); font-size:1.1rem; margin-bottom:.3rem; }}
.service-card p {{ color:var(--muted); font-size:.9rem; }}
/* HOURS TABLE */
.hours-table {{ width:100%; border-collapse:collapse; background:var(--surface); border-radius:var(--radius); overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,.04); }}
.hours-table th,.hours-table td {{ padding:.7rem 1.2rem; text-align:left; }}
.hours-table tr {{ border-bottom:1px solid #f0f0f0; }}
.hours-table tr:last-child {{ border-bottom:none; }}
/* MAP */
.map-box {{ border-radius:var(--radius); overflow:hidden; box-shadow:0 2px 16px rgba(0,0,0,.08); margin-top:1rem; }}
.map-box iframe {{ width:100%; height:300px; border:0; }}
/* CONTACT */
.contact-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1.5rem; }}
.contact-item {{ background:var(--surface); border-radius:var(--radius); padding:1.5rem; box-shadow:0 2px 8px rgba(0,0,0,.03); }}
.contact-item h3 {{ color:var(--primary); font-size:1rem; margin-bottom:.5rem; }}
.contact-item a {{ color:var(--primary); text-decoration:none; }}
/* TRUST */
.trust-bar {{ background:var(--primary); color:#fff; padding:1.5rem; text-align:center; }}
.trust-bar p {{ font-size:.95rem; opacity:.9; }}
/* FOOTER */
footer {{ background:#1a1a2e; color:rgba(255,255,255,.6); padding:2rem 1.5rem; text-align:center; font-size:.85rem; }}
footer a {{ color:var(--accent); }}
.demo-badge {{ display:inline-block; background:rgba(255,255,255,.1); padding:.3rem .8rem; border-radius:20px; font-size:.8rem; margin-top:.5rem; }}
@media(max-width:600px) {{ .hero {{ padding:2rem 1rem 2.5rem; }} section {{ padding:2rem 1rem; }} }}
</style>
</head>
<body>

<!-- HERO -->
<section class="hero" style="border-radius:0;margin:0;">
  <div class="icon-big">{icon}</div>
  <h1>{name}</h1>
  <div class="branch">{branch} in {city}</div>
  <div class="city-tag">📍 {address or city}</div>
  {rating_html}
  <div class="cta-group">
    {phone_link}
    {email_link}
  </div>
</section>

<!-- ABOUT -->
<section>
  <h2>Über uns</h2>
  <div class="about-box">
    <p>{about}</p>
    {f'<p style="margin-top:1rem;"><strong>Inhaber:</strong> {owner}</p>' if owner else ''}
  </div>
</section>

<!-- SERVICES -->
<section>
  <h2>Unsere Leistungen</h2>
  <div class="services-grid">{cards}</div>
</section>

<!-- HOURS -->
<section>
  <h2>Öffnungszeiten</h2>
  <table class="hours-table"><tbody>{hours_rows}</tbody></table>
</section>

<!-- MAP -->
<section>
  <h2>Anfahrt & Standort</h2>
  <div class="map-box"><iframe src="{maps_src}" loading="lazy"></iframe></div>
</section>

<!-- CONTACT -->
<section>
  <h2>Kontakt</h2>
  <div class="contact-grid">
    <div class="contact-item">
      <h3>📍 Adresse</h3>
      <p>{address or city}</p>
    </div>
    <div class="contact-item">
      <h3>📞 Telefon</h3>
      <p>{f'<a href="tel:{phone}">{phone}</a>' if phone else 'Auf Anfrage'}</p>
    </div>
    <div class="contact-item">
      <h3>✉️ E-Mail</h3>
      <p>{f'<a href="mailto:{email_addr}">{email_addr}</a>' if email_addr else 'Auf Anfrage'}</p>
    </div>
  </div>
</section>

<!-- TRUST -->
<div class="trust-bar">
  <p>✅ Professionell · Regional verwurzelt · {branch} in {city}</p>
</div>

<!-- FOOTER -->
<footer>
  <p><strong>{name}</strong> · {city}</p>
  <div class="demo-badge">Demo-Website erstellt von Werkspree (KI-Automatisierung für kleine Unternehmen)</div>
  <p style="margin-top:.5rem;">Diese Website ist ein unverbindlicher Entwurf. <a href="mailto:info@werkspree.bki-de.de">Jetzt echte Website anfragen</a></p>
</footer>

</body>
</html>"""
    return html


def build_v1_fallback(lead):
    """Altes Template (Kontrolle A) — unverändert vom original build_fallback_template."""
    name = lead.get("company_name", "Ihr Betrieb")
    branch = lead.get("segment", "")
    city = lead.get("city") or lead.get("region", "")
    phone = lead.get("phone", "")
    email_addr = lead.get("email", "")
    address = lead.get("address", "")
    about = lead.get("about", "") or f"{name} ist ein etablierter Betrieb in {city}."
    owner = lead.get("owner", "")
    hours = lead.get("opening_hours", {})
    products = lead.get("products", [])
    phone_link = f'<a href="tel:{phone}">{phone}</a>' if phone else '<span>Auf Anfrage</span>'
    email_link = f'<a href="mailto:{email_addr}">{email_addr}</a>' if email_addr else '<span>Auf Anfrage</span>'
    hours_rows = ""
    days_map = {"Mo": "Montag", "Di": "Dienstag", "Mi": "Mittwoch", "Do": "Donnerstag", "Fr": "Freitag", "Sa": "Samstag", "So": "Sonntag"}
    for k, v in hours.items():
        hours_rows += f"<tr><td>{days_map.get(k, k)}</td><td>{v}</td></tr>"
    if not hours_rows:
        hours_rows = "<tr><td colspan='2'>Auf Anfrage</td></tr>"
    cards = ""
    if products:
        for p in products[:6]:
            if isinstance(p, (list, tuple)):
                title, desc = p[0], p[1] if len(p) > 1 else ""
            else:
                title, desc = p, ""
            cards += f'<div class="card"><h3>{title}</h3><p>{desc}</p></div>'
    else:
        cards = '<div class="card"><h3>Leistungen</h3><p>Auf Anfrage</p></div>'
    primary, accent = ("#122c4d", "#1f9d74")
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
<style>
:root {{ --primary:{primary}; --accent:{accent}; --bg:#fafafa; --surface:#fff; --text:#1d2939; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:-apple-system,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
header {{ background:linear-gradient(135deg,var(--primary),var(--accent)); color:#fff; padding:4rem 1.5rem; text-align:center; }}
header h1 {{ font-size:2.2rem; margin-bottom:.5rem; }}
section {{ max-width:900px; margin:0 auto; padding:3rem 1.5rem; }}
h2 {{ color:var(--primary); margin-bottom:1rem; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1.5rem; }}
.card {{ background:var(--surface); border-radius:12px; padding:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,.06); }}
table {{ width:100%; border-collapse:collapse; margin-top:1rem; }}
th,td {{ text-align:left; padding:.6rem; border-bottom:1px solid #eee; }}
footer {{ background:var(--primary); color:#fff; text-align:center; padding:2rem 1.5rem; font-size:.9rem; }}
</style></head><body>
<header><h1>{name}</h1><p>{branch} in {city}</p></header>
<section><h2>Über uns</h2><p>{about}</p></section>
<section><h2>Unsere Leistungen</h2><div class="cards">{cards}</div></section>
<section><h2>Öffnungszeiten</h2><table><tbody>{hours_rows}</tbody></table></section>
<section><h2>Kontakt</h2><p>{phone_link}</p><p>{email_link}</p><p>{address or city}</p></section>
<footer><p>{name} · {city}</p><p style="margin-top:.5rem;opacity:.7;">Demo-Website von Werkspree</p></footer>
</body></html>"""


def assign_ab_group(slug):
    """A/B-Zuweisung: deterministisch per slug, 50/50 Split."""
    hash_val = sum(ord(c) for c in slug) % 2
    return "a" if hash_val == 0 else "b"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", help="Pfad zu Lead-JSON")
    ap.add_argument("--force-version", choices=["a", "b"], help="A/B-Version erzwingen")
    args = ap.parse_args()
    if not args.lead:
        print("ERROR: --lead erforderlich")
        sys.exit(2)
    lead = json.loads(Path(args.lead).read_text())
    ev = lead.get("email_verified", "")
    if str(ev).lower() not in ("yes", "true", "1"):
        print("ERROR: Lead nicht verifiziert")
        sys.exit(2)
    name = lead.get("company_name") or lead.get("name", "lead")
    lead["company_name"] = name
    slug = lead.get("slug") or slugify(name)
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    
    # A/B-Zuweisung
    if args.force_version:
        ab_group = args.force_version
    else:
        ab_group = assign_ab_group(slug)
    
    print(f"  A/B-Gruppe: {ab_group.upper()} — {name}")
    
    if ab_group == "a":
        html = build_v1_fallback(lead)
        version = "v1_control"
    else:
        html = build_v3_html(lead)
        version = "v3_improved"
    
    (out / "index.html").write_text(html, encoding="utf-8")
    site_url = f"https://werkspree.bki-de.de/microsites/sites/{slug}/"
    lead["site_url"] = site_url
    lead["ab_group"] = ab_group
    lead["template_version"] = version
    lead["built_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    Path(args.lead).write_text(json.dumps(lead, ensure_ascii=False, indent=2))
    print(f"  Site gebaut ({version}): {site_url}")
    sys.exit(0)


if __name__ == "__main__":
    main()
