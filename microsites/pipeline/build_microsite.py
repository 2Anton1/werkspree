#!/usr/bin/env python3
"""Werkspree: Baut eine statische Microsite fuer einen qualifizierten Hot-Lead.

Statt Lovable (OAuth nicht persistierbar in Cron-Umgebung) rendern wir ein
eigenes HTML-Template mit den verifizierten Lead-Daten und deployen es als
statischen Ordner auf GitHub Pages (werkspree.bki-de.de/microsites/<slug>/).

Nutzung:
  python3 build_microsite.py --lead microsites/pipeline/data/microsites_built.json
  python3 build_microsite.py --demo   # baut Beispiel-Site ohne Versand

Exit-Codes: 0 = gebaut, 2 = Lead nicht qualifiziert, 3 = Render-Fehler.
"""
import argparse, html as html_lib, json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

try:
    from site_quality import is_valid_html
except ImportError:  # Import als Paket im lokalen Testlauf
    from microsites.pipeline.site_quality import is_valid_html

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "microsites" / "sites"
TEMPLATE = Path(__file__).parent / "microsite_template.html"

TZ = timezone(timedelta(hours=2))  # CEST


def slugify(name: str) -> str:
    # Umlaute normalisieren, dann nur [a-z0-9] behalten
    import unicodedata
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:40]


def render(template: str, lead: dict) -> str:
    def esc(value):
        return html_lib.escape(str(value or "").strip(), quote=True)

    segment = (lead.get("segment") or lead.get("branch") or "Allgemein").strip()
    segment_lower = segment.lower()
    city = str(lead.get("city") or lead.get("region") or "Berlin und Brandenburg").strip()
    company = str(lead.get("company_name") or lead.get("name") or "Ihr Betrieb").strip()
    phone = str(lead.get("phone") or "").strip()
    email = str(lead.get("email") or "").strip()
    address = str(lead.get("address") or city).strip()
    maps_query = str(lead.get("maps_query") or f"{address}, {city}").strip()

    def normalized_tokens(value):
        import unicodedata
        value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii").lower()
        return {token for token in re.findall(r"[a-z0-9]+", value) if len(token) >= 3}

    # Alte Datensätze können durch eine falsche Zuordnung eine formal gültige,
    # aber fremde Adresse enthalten. Solche Adressen werden nicht auf der
    # öffentlichen Demo wiederholt; der Lead selbst bleibt für die Prüfung
    # erhalten.
    company_tokens = normalized_tokens(company) | normalized_tokens(segment)
    email_tokens = normalized_tokens(email.replace("@", " "))
    if email and company_tokens.isdisjoint(email_tokens):
        email = ""

    palettes = {
        "bäckerei": ("#7b3f25", "#4d2519", "#d69b45", "#fbf0dc"),
        "bäcker": ("#7b3f25", "#4d2519", "#d69b45", "#fbf0dc"),
        "friseur": ("#73552d", "#241d18", "#c39a53", "#f5eee5"),
        "kosmetik": ("#a0445b", "#5b2638", "#df9aaa", "#fdf0f3"),
        "fahrschule": ("#1764a0", "#0b2945", "#e05a47", "#edf4fa"),
        "elektriker": ("#1f5f85", "#12344b", "#f0b429", "#edf5f7"),
        "kfz": ("#46596c", "#202d38", "#eea62a", "#edf1f4"),
        "reinigung": ("#187d83", "#124b56", "#6cc7bd", "#eaf8f6"),
        "tischler": ("#8a5a32", "#4b3020", "#c99358", "#f6eee5"),
        "tischlerei": ("#8a5a32", "#4b3020", "#c99358", "#f6eee5"),
        "dachdecker": ("#43596d", "#263541", "#c27a42", "#edf1f3"),
        "sanitär": ("#286b91", "#17415c", "#77bdd8", "#edf7fa"),
        "gartenbau": ("#3d805d", "#204b3a", "#91c98e", "#eef7ed"),
        "zahnarzt": ("#3e8e9a", "#20505d", "#8acbd0", "#edf8f8"),
        "physiotherapie": ("#347f7f", "#225252", "#9bd5c5", "#edf8f4"),
    }
    primary, primary_dark, accent, accent_soft = next((v for k, v in palettes.items() if k in segment_lower), ("#246b80", "#163f50", "#75b9a5", "#edf7f4"))

    descriptions = {
        "bäckerei": ["Brot & Brötchen", "Kuchen & Torten", "Kaffee & Gebäck"],
        "bäcker": ["Brot & Brötchen", "Kuchen & Torten", "Kaffee & Gebäck"],
        "friseur": ["Haarschnitt", "Farbe & Pflege", "Styling & Beratung"],
        "kosmetik": ["Gesichtsbehandlungen", "Wimpern & Brows", "Hautpflege-Beratung"],
        "fahrschule": ["Pkw-Ausbildung", "Begleitetes Fahren", "Auffrischung"],
        "elektriker": ["Installation", "Reparatur & Wartung", "Sicherheitscheck"],
        "kfz": ["Inspektion", "Reparatur", "Reifen & HU/AU"],
        "reinigung": ["Unterhaltsreinigung", "Glasreinigung", "Grundreinigung"],
        "tischler": ["Möbelbau", "Türen & Fenster", "Restaurierung"],
        "tischlerei": ["Möbelbau", "Türen & Fenster", "Restaurierung"],
        "dachdecker": ["Dacheindeckung", "Dachsanierung", "Reparatur & Notdienst"],
        "sanitär": ["Bad & Installation", "Reparatur", "Wartung"],
        "gartenbau": ["Gartengestaltung", "Pflege", "Baumschnitt"],
        "zahnarzt": ["Prophylaxe", "Zahnbehandlung", "Ästhetik"],
        "physiotherapie": ["Manuelle Therapie", "Lymphdrainage", "Sportphysiotherapie"],
    }
    default_descriptions = ["Beratung", "Leistung nach Bedarf", "Persönlicher Service"]
    product_copy = {
        "Brot & Brötchen": "Frische Backwaren für den Alltag und besondere Anlässe.",
        "Haarschnitt": "Ein Schnitt, der zu Ihrem Stil und Ihrem Alltag passt.",
        "Gesichtsbehandlungen": "Individuelle Behandlungen mit Zeit für Beratung und Pflege.",
        "Pkw-Ausbildung": "Strukturiert von der Theorie bis zur praktischen Prüfung.",
        "Installation": "Sorgfältige Lösungen für sichere und zuverlässige Technik.",
        "Inspektion": "Wartung und Vorbereitung für eine sichere, planbare Fahrt.",
        "Unterhaltsreinigung": "Regelmäßige Reinigung für ein gepflegtes Arbeitsumfeld.",
        "Möbelbau": "Individuelle Maßarbeit mit Blick auf Material und Funktion.",
        "Dacheindeckung": "Wetterfeste Arbeit für Schutz, Substanz und Werterhalt.",
        "Bad & Installation": "Durchdachte Lösungen für Bad, Wasser und Wärme.",
        "Gartengestaltung": "Grünflächen, die zu Ort, Nutzung und Jahreszeit passen.",
    }

    def clean_products(raw):
        result = []
        noise = {"suchen", "finden", "service", "website", "e-mail", "email", "gratis anrufen", "meinen standort verwenden"}
        for product in raw or []:
            if isinstance(product, (list, tuple)) and len(product) >= 2:
                title, desc = str(product[0]).strip(), str(product[1]).strip()
            elif isinstance(product, str):
                title, desc = product.strip(), ""
            else:
                continue
            if not title or title.lower() in noise or title.lower().startswith(("jetzt geschlossen", "öffnet ")) or "gelbe seiten" in title.lower():
                continue
            if title not in [p[0] for p in result]:
                result.append((title, desc or product_copy.get(title, "Gerne informieren wir Sie zu dieser Leistung auf Anfrage.")))
        return result[:6]

    products = clean_products(lead.get("products"))
    if not products:
        names = next((v for k, v in descriptions.items() if k in segment_lower), default_descriptions)
        products = [(name, product_copy.get(name, f"Gerne informieren wir Sie zu {name.lower()} auf Anfrage.")) for name in names]
    cards = "".join(f'<article class="service-card"><h3>{esc(title)}</h3><p>{esc(desc)}</p></article>' for title, desc in products)

    about = str(lead.get("about") or "").strip()
    if not about or "![" in about or "](" in about or "gelbe seiten" in about.lower() or ("traditionsbäckerei" in about.lower() and "bäck" not in segment_lower):
        about = f"{company} steht in {city} für sorgfältige Arbeit, persönliche Beratung und verlässliche Absprachen. Sprechen Sie uns an – wir klären Ihr Anliegen direkt und finden eine passende Lösung."
    tagline = str(lead.get("tagline") or f"Verlässliche Leistungen für {city} und Umgebung.").strip()
    owner = str(lead.get("owner") or "Auf Anfrage").strip()
    email_display = esc(email) if email else "Auf Anfrage"
    email_link = f'<a href="mailto:{esc(email)}">{email_display}</a>' if email else "Auf Anfrage"
    phone_href = f"tel:{re.sub(r'[^0-9+]', '', phone)}" if phone else "#kontakt"
    phone_display = esc(phone) if phone else "Auf Anfrage"
    hours = lead.get("opening_hours") or {}
    day_names = [("Mo", "Montag"), ("Di", "Dienstag"), ("Mi", "Mittwoch"), ("Do", "Donnerstag"), ("Fr", "Freitag"), ("Sa", "Samstag"), ("So", "Sonntag")]
    rows = "".join(f"<tr><td>{day}</td><td>{esc(hours.get(key, 'Auf Anfrage'))}</td></tr>" for key, day in day_names)
    maps_href = f"https://www.google.com/maps/search/?api=1&query={quote(maps_query)}"
    replacements = {
        "{{COMPANY}}": esc(company), "{{BRANCH}}": esc(segment), "{{CITY}}": esc(city),
        "{{INITIAL}}": esc(company[:1].upper()), "{{DESCRIPTION}}": esc(f"{company} – {segment} in {city}."),
        "{{PRIMARY}}": primary, "{{PRIMARY_DARK}}": primary_dark, "{{ACCENT}}": accent, "{{ACCENT_SOFT}}": accent_soft,
        "{{TAGLINE}}": esc(tagline), "{{ADDRESS}}": esc(address), "{{ABOUT}}": esc(about),
        "{{PHONE_HREF}}": phone_href, "{{PHONE_DISP}}": phone_display, "{{EMAIL_DISPLAY}}": email_display,
        "{{EMAIL_LINK}}": email_link, "{{OWNER}}": esc(owner), "{{SERVICE_CARDS}}": cards,
        "{{HOURS_ROWS}}": rows, "{{MAPS_HREF}}": html_lib.escape(maps_href, quote=True),
        "{{YEAR}}": str(datetime.now(TZ).year),
    }
    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)
    if not is_valid_html(html):
        raise ValueError("Gerendertes Microsite-HTML ist unvollständig")
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", help="Pfad zu Lead-JSON")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.demo:
        lead = {
            "company_name": "Demo Bäckerei",
            "segment": "Bäckerei",
            "region": "Brandenburg",
            "website_issue": "Keine Website",
            "email": "info@example.de",
            "email_verified": "yes",
            "phone": "03381 123456",
            "owner": "Anna Berg",
            "address": "Hauptstraße 1",
            "city": "Brandenburg an der Havel",
            "tagline": "Frisch gebacken seit 1990.",
            "products": [["Brot", "Beschreibung"], ["Brötchen", "Beschreibung"], ["Kuchen", "Beschreibung"]],
        }
    else:
        if not args.lead:
            ap.error("--lead oder --demo erforderlich")
        lead = json.loads(Path(args.lead).read_text())

    if not args.demo and not lead.get("email_verified"):
        print("ERROR: Lead nicht qualifiziert (email_verified != yes)")
        sys.exit(2)
    if not args.demo:
        email = str(lead.get("email") or "").strip().lower()
        if not re.fullmatch(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63}", email, re.I):
            print("ERROR: Lead nicht qualifiziert (ungueltige E-Mail)")
            sys.exit(2)
        optout_path = TEMPLATE.parent / "data" / "opt_out.json"
        if optout_path.exists():
            optout = json.loads(optout_path.read_text())
            domain = email.rsplit("@", 1)[-1]
            company = str(lead.get("company_name") or lead.get("name") or "").lower()
            if email in {str(v).lower() for v in optout.get("emails", [])} or domain in {str(v).lower() for v in optout.get("domains", [])} or any(str(v).lower() in company for v in optout.get("companies", [])):
                print("ERROR: Lead gesperrt (Opt-out)")
                sys.exit(2)

    slug = lead.get("slug") or slugify(lead.get("company_name") or lead.get("name", "lead"))
    html = render(TEMPLATE.read_text(), lead)
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html)
    # Lead-Daten bleiben in microsites/pipeline/data/ und werden nicht als
    # öffentlich abrufbare Begleitdatei neben der Website abgelegt.
    print(f"INFO: Site gebaut -> {out/'index.html'}")

    # Kein Push hier — der Orchestrator (run_microsite_pipeline.py) pushed
    # zentral, damit der Sandbox-Git-Context genutzt wird.

    base = "https://werkspree.bki-de.de/microsites/sites"
    url = f"{base}/{slug}/"
    print(f"INFO: Live-URL: {url}")
    lead["site_url"] = url
    lead["built_at"] = datetime.now(TZ).isoformat()
    lead["slug"] = slug
    src = Path(args.lead) if args.lead else None
    if src:
        src.write_text(json.dumps(lead, ensure_ascii=False, indent=2))
    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
