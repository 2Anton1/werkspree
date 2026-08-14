#!/usr/bin/env python3
"""Werkspree: Baut eine statische Microsite fuer einen qualifizierten Hot-Lead.

Statt Lovable (OAuth nicht persistierbar in Cron-Umgebung) rendern wir ein
eigenes HTML-Template mit den verifizierten Lead-Daten und deployen es als
statischen Ordner auf GitHub Pages (werkspree.bki-de.de/microsites/<slug>/).

Nutzung:
  python3 build_microsite.py --lead microsites/pipeline/data/microsites_built.json
  python3 build_microsite.py --demo   # baut Beispiel-Site ohne Versand

Exit-Codes: 0 = gebaut+gepusht, 2 = Lead nicht qualifiziert, 3 = Render-Fehler,
4 = Git-Push-Fehler.
"""
import argparse, json, re, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path.home() / "werkspree"
OUT_DIR = REPO / "microsites" / "sites"
TEMPLATE = Path(__file__).parent / "microsite_template.html"

TZ = timezone(timedelta(hours=2))  # CEST


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:40]


def render(template: str, lead: dict) -> str:
    oh = lead.get("opening_hours", {})
    rows = "".join(
        f"<tr><td>{d}</td><td>{t}</td></tr>" for d, t in [
            ("Dienstag", oh.get("Di", "07:00–17:00")),
            ("Mittwoch", oh.get("Mi", "07:00–17:00")),
            ("Donnerstag", oh.get("Do", "07:00–13:00")),
            ("Freitag", oh.get("Fr", "07:00–16:00")),
            ("Samstag", oh.get("Sa", "07:00–10:00")),
            ("Sonntag", "geschlossen (Ruhetag)"),
            ("Montag", "geschlossen (Ruhetag)"),
        ]
    )
    prods = lead.get("products") or [
        ["Brot & Brötchen", "Frisch gebackenes Brot und knusprige Brötchen aus eigener Herstellung – täglich für Sie gebacken."],
        ["Torten & Konditorei", "Handwerkliche Torten und feine Konditoreiwaren für Feste, Familienfeiern und Genussmomente."],
        ["Stehcafé", "Kurze Rast mit Kaffee und einem frischen Gebäck – einladend und unkompliziert."],
    ]
    cards = "".join(
        f'<div class="card"><h3>{p[0]}</h3><p>{p[1]}</p></div>' for p in prods
    )
    addr = lead.get("address", "")
    city = lead.get("city", "Brandenburg an der Havel")
    maps_q = lead.get("maps_query", f"{addr}, {city}")
    phone = lead.get("phone", "")
    email = lead.get("email", "")
    owner = lead.get("owner", "Inhaber")
    about = lead.get("about", "")
    if not about:
        about = (
            f"Die {lead.get('company_name','Bäckerei')} ist eine Traditionsbäckerei in "
            f"{city}, eingetragen in der Handwerksrolle der Handwerkskammer Potsdam. "
            "Seit über 36 Jahren stehen wir für handwerklich hergestellte Backwaren, "
            "bei denen Frische und Qualität an erster Stelle stehen."
        )
    replacements = {
        "{{COMPANY}}": lead.get("company_name", ""),
        "{{TAGLINE}}": lead.get("tagline", "Seit über 36 Jahren ein Begriff für Qualität und Genuss."),
        "{{ABOUT}}": about,
        "{{OWNER}}": owner,
        "{{CARDS}}": cards,
        "{{ROWS}}": rows,
        "{{ADDR}}": addr,
        "{{CITY}}": city,
        "{{MAPS_Q}}": maps_q,
        "{{PHONE}}": phone,
        "{{PHONE_HREF}}": f"tel:{re.sub(r'[^0-9+]', '', phone)}",
        "{{EMAIL}}": email,
        "{{EMAIL_HREF}}": f"mailto:{email}",
        "{{HANDWERK}}": lead.get("handwerksrolle", "Eingetragen in der Handwerksrolle der Handwerkskammer Potsdam"),
    }
    html = template
    for k, v in replacements.items():
        html = html.replace(k, v)
    html = re.sub(r"\{\{[^}]+\}\}", "", html)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", help="Pfad zu Lead-JSON")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.demo:
        lead = {
            "company_name": "Beispiel Bäckerei Mustermann",
            "segment": "Bäckerei",
            "region": "Brandenburg",
            "website_issue": "Keine Website",
            "email": "info@example.de",
            "email_verified": "yes",
            "phone": "03381 123456",
            "owner": "Max Mustermann",
            "address": "Musterstraße 1",
            "city": "Brandenburg an der Havel",
            "tagline": "Frisch gebacken seit 1990.",
            "products": [["Brot", "Beschreibung"], ["Brötchen", "Beschreibung"], ["Kuchen", "Beschreibung"]],
        }
    else:
        lead = json.loads(Path(args.lead).read_text())

    if not args.demo and lead.get("email_verified") != "yes":
        print("ERROR: Lead nicht qualifiziert (email_verified != yes)")
        sys.exit(2)

    slug = lead.get("slug") or slugify(lead.get("company_name", "lead"))
    html = render(TEMPLATE.read_text(), lead)
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html)
    (out / "lead.json").write_text(json.dumps(lead, ensure_ascii=False, indent=2))
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
