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
    # Umlaute normalisieren, dann nur [a-z0-9] behalten
    import unicodedata
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:40]


def render(template: str, lead: dict) -> str:
    oh = lead.get("opening_hours", {})
    rows = "".join(
        f"<tr><td>{d}</td><td>{t}</td></tr>" for d, t in [
            ("Dienstag", oh.get("Di", "08:00–18:00")),
            ("Mittwoch", oh.get("Mi", "08:00–18:00")),
            ("Donnerstag", oh.get("Do", "08:00–18:00")),
            ("Freitag", oh.get("Fr", "08:00–18:00")),
            ("Samstag", oh.get("Sa", "08:00–13:00")),
            ("Sonntag", "geschlossen (Ruhetag)"),
            ("Montag", "geschlossen (Ruhetag)"),
        ]
    )
    # Segment-spezifische Produkte/Leistungen (KEIN Bäckerei-Default!)
    segment = (lead.get("segment") or "").lower()
    prods_map = {
        "bäckerei": [["Brot & Brötchen", "Frisch gebackenes Brot und knusprige Brötchen aus eigener Herstellung – täglich für Sie gebacken."],
                     ["Torten & Konditorei", "Handwerkliche Torten und feine Konditoreiwaren für Feste, Familienfeiern und Genussmomente."],
                     ["Stehcafé", "Kurze Rast mit Kaffee und einem frischen Gebäck – einladend und unkompliziert."]],
        "bäcker": [["Brot & Brötchen", "Frisch gebackenes Brot und knusprige Brötchen aus eigener Herstellung – täglich für Sie gebacken."],
                    ["Torten & Konditorei", "Handwerkliche Torten und feine Konditoreiwaren für Feste, Familienfeiern und Genussmomente."],
                    ["Stehcafé", "Kurze Rast mit Kaffee und einem frischen Gebäck – einladend und unkompliziert."]],
        "friseur": [["Herrenhaarschnitt", "Präzise Schnitte und klassische Rasur – individuell nach Ihrem Stil."],
                    ["Damenhaarschnitt", "Moderne Trends und zeitlose Looks, die zu Ihnen passen."],
                    ["Färbung & Pflege", "Schonende Farbtechnik und intensive Haarpflege für gesundes Volumen."]],
        "fahrschule": [["Pkw-Ausbildung", "Strukturierte Fahrausbildung von der Theorie bis zur Prüfung – geduldig und verbindlich."],
                       ["Begleitetes Fahren", "Führerschein ab 17 mit persönlicher Betreuung durch erfahrene Fahrlehrer."],
                       ["Auffrischung", "Praxisnahe Trainings für Wiedereinsteiger und Verkehrssicherheitstrainings."]],
        "elektriker": [["Installation", "Sicherheitstechnik, Unterverteilungen und Elektro-Installationen nach VDE-Norm."],
                       ["Reparatur & Wartung", "Schnelle Fehlerbehebung und vorbeugende Wartung Ihrer Anlagen."],
                       ["Notdienst", "Erreichbar bei Störungen – zügige Hilfe, wenn es brennt (im übertragenen Sinne)."]],
        "tischler": [["Möbelbau", "Maßgefertigte Möbel aus Massivholz – vom Regal bis zur Einbauküche."],
                     ["Türen & Fenster", "Passgenaue Türen, Fenster und Reparaturen mit handwerklicher Präzision."],
                     ["Restaurierung", "Wertige Holzobjekte fachgerecht aufarbeiten und erhalten."]],
        "reinigung": [["Unterhaltsreinigung", "Regelmäßige Gebäudereinigung für Büro, Praxis und Gewerbe."],
                      ["Glasreinigung", "Streifenfreie Fenster- und Glasreinigung auch in der Höhe."],
                      ["Grundreinigung", "Gründliche Erst- und Endreinigung nach Bau oder Umzug."]],
        "kosmetik": [["Gesichtsbehandlung", "Hautbild verbessernde Treatments – entspannend und wirksam."],
                     ["Wimpern & Brows", "Gezieltes Styling für einen frischen, gepflegten Look."],
                     ["Beratung", "Individuelle Hautanalyse und Produktempfehlung."]],
        "metzgerei": [["Frischfleisch", "Handwerklich zerlegtes Fleisch aus regionaler Herkunft – täglich frisch."],
                      ["Wurstwaren", "Eigenhergestellte Brat- und Kochwürste nach Hausrezept."],
                      ["Feinkost", "Salate, Aufschnitt und Partyservice für jeden Anlass."]],
        "tischlerei": [["Möbelbau", "Maßgefertigte Möbel aus Massivholz – vom Regal bis zur Einbauküche."],
                       ["Türen & Fenster", "Passgenaue Türen, Fenster und Reparaturen mit handwerklicher Präzision."],
                       ["Restaurierung", "Wertige Holzobjekte fachgerecht aufarbeiten und erhalten."]],
        "kfz": [["Inspektion", "Regelmäßige Wartung und HU/AU-Vorbereitung nach Herstellervorgabe."],
                ["Reparatur", "Motorservice, Bremsen und Fahrwerk – schnell und verbindlich."],
                ["Reifen", "Wechsel, Lagerung und Auswuchten für sichere Fahrt."]],
        "autowerkstatt": [["Inspektion", "Regelmäßige Wartung und HU/AU-Vorbereitung nach Herstellervorgabe."],
                          ["Reparatur", "Motorservice, Bremsen und Fahrwerk – schnell und verbindlich."],
                          ["Reifen", "Wechsel, Lagerung und Auswuchten für sichere Fahrt."]],
        "dachdecker": [["Dacheindeckung", "Neueindeckung und Sanierung mit Ziegel, Schiefer oder Metalldeckung."],
                       ["Dachsanierung", "Dämmung, Unterspannbahn und Gaubenbau aus einer Hand."],
                       ["Notdienst", "Schnelle Hilfe bei Sturmschäden und Undichtheiten."]],
        "sanitär": [["Installation", "Bäder, Heizungen und Rohrleitungen nach aktuellem Standard."],
                    ["Reparatur", "Verstopfungen, Undichtigkeiten und Armaturen-Tausch."],
                    ["Wartung", "Anlagencheck für effiziente und lange Lebensdauer."]],
        "gartenbau": [["Gartengestaltung", "Planung und Anlage von Beeten, Rabatten und Terrassen."],
                      ["Pflege", "Regelmäßiger Schnitt und Saisonpflege Ihrer Grünflächen."],
                      ["Baumschnitt", "Fachgerechter Schnitt und Sicherung von Gehölzen."]],
    }
    prods = lead.get("products") or prods_map.get(segment, [
        ["Leistungen", "Wir bieten unsere Kernleistungen mit handwerklicher Sorgfalt und persönlicher Betreuung."],
        ["Beratung", "Individuelle Beratung – wir nehmen uns Zeit für Ihr Anliegen."],
        ["Kontakt", "Erreichbar für Terminanfragen und Rückfragen."],
    ])
    # Normalisiere: Pipeline liefert Strings (Leistungsnamen), Map liefert [titel,beschreibung]
    norm_prods = []
    for p in prods:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            norm_prods.append([p[0], p[1]])
        elif isinstance(p, str):
            # String -> suche passende Beschreibung in prods_map, sonst generic
            desc = ""
            for seg_prods in prods_map.values():
                for tp, td in seg_prods:
                    if tp.lower() == p.lower():
                        desc = td
                        break
                if desc:
                    break
            norm_prods.append([p, desc or "Gerne informieren wir Sie detailiert zu dieser Leistung auf Anfrage."])
        else:
            continue
    cards = "".join(
        f'<div class="card"><h3>{p[0]}</h3><p>{p[1]}</p></div>' for p in norm_prods
    )
    addr = lead.get("address", "")
    city = lead.get("city", "Brandenburg an der Havel")
    maps_q = lead.get("maps_query", f"{addr}, {city}")
    phone = lead.get("phone", "")
    email = lead.get("email", "")
    owner = lead.get("owner", "Inhaber")
    about = lead.get("about", "")
    if not about:
        # Generic, segment-neutral (KEIN Bäckerei-Claim!)
        about = (
            f"{lead.get('company_name', 'Unser Betrieb')} ist ein etablierter "
            f"Handwerks- und Dienstleistungsbetrieb in {city}. "
            "Wir verbinden handwerkliche Sorgfalt mit persönlicher Kundenbetreuung "
            "und freuen uns, Sie bei Ihrem Anliegen zu unterstützen."
        )
    tagline = lead.get("tagline", "Ihr verlässlicher Partner vor Ort in " + city)
    replacements = {
        "{{COMPANY}}": lead.get("company_name", ""),
        "{{TAGLINE}}": tagline,
        "{{ABOUT}}": about,
        "{{OWNER}}": owner,
        "{{CARDS}}": cards,
        "{{SORTIMENT_CARDS}}": cards,
        "{{ROWS}}": rows,
        "{{ADDR}}": addr,
        "{{CITY}}": city,
        "{{MAPS_Q}}": maps_q,
        "{{PHONE}}": phone,
        "{{PHONE_HREF}}": f"tel:{re.sub(r'[^0-9+]', '', phone)}",
        "{{EMAIL}}": email,
        "{{EMAIL_HREF}}": f"mailto:{email}",
        "{{HANDWERK}}": lead.get("handwerksrolle", "Eingetragen im lokalen Handelsregister"),
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
