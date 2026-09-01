#!/usr/bin/env python3
"""Erzeugt die zwölf fehlenden, statischen Branchen-Ratgeberseiten."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGES = {
    "allgemein": ("Website für kleine Betriebe", "Professioneller Website-Baukasten für kleine Betriebe", "Leistungen verständlich zeigen, Anfragen erleichtern und online professionell auftreten.", ["klare Leistungsseiten", "mobile Darstellung", "Kontakt ohne Umwege"]),
    "baeckerei": ("Website für Bäckereien", "Eine Website für Ihre Bäckerei, die Appetit auf den nächsten Besuch macht", "Öffnungszeiten, Sortiment und Standort gehören auf eine Seite, die Kundinnen und Kunden schnell verstehen.", ["Sortiment und Spezialitäten", "Öffnungszeiten und Standort", "Anfragen für Torten und Feiern"]),
    "fahrschule": ("Website für Fahrschulen", "Mehr Klarheit für den Weg zum Führerschein", "Führerscheinklassen, Anmeldung und Kontakt übersichtlich an einem Ort – auch unterwegs auf dem Smartphone.", ["Führerscheinklassen", "Anmeldung und Ablauf", "Kontakt für Rückfragen"]),
    "gartenbau": ("Website für Gartenbau", "Gartenbau sichtbar machen: Leistungen, Einsatzgebiet und Anfrage", "Eine gute Branchen-Website zeigt, welche Arbeiten Sie übernehmen und wie Interessierte den ersten Termin anfragen.", ["Gartengestaltung und Pflege", "Saisonale Leistungen", "Einsatzgebiet und Kontakt"]),
    "immobilien": ("Website für Immobilienbüros", "Vertrauen beginnt mit einer klaren Immobilien-Website", "Dienstleistungen, Einzugsgebiet und Kontakt sollten für Eigentümer und Suchende sofort auffindbar sein.", ["Leistungsbereiche", "Region und Erreichbarkeit", "Anfrage für Beratung"]),
    "kosmetik": ("Website für Kosmetikstudios", "Ihre Kosmetikleistungen stilvoll und verständlich online zeigen", "Behandlungen, Atmosphäre und Terminwunsch lassen sich mit einer klaren, ruhigen Website überzeugend präsentieren.", ["Behandlungskategorien", "Beratung und Termin", "Mobile-first Design"]),
    "physio": ("Website für Physiotherapien", "Eine hilfreiche Website für Ihre Physiotherapiepraxis", "Patientinnen und Patienten suchen vor allem Orientierung: Behandlungsschwerpunkte, Ablauf, Erreichbarkeit und nächste Schritte.", ["Behandlungen", "Praxisinformationen", "Termin- und Kontaktweg"]),
    "reinigung": ("Website für Gebäudereinigung", "Leistungen der Gebäudereinigung auf einen Blick", "Eine sachliche Website schafft Orientierung für Büros, Praxen und Gewerbekunden und führt direkt zur Angebotsanfrage.", ["Unterhalts- und Grundreinigung", "Glas- und Sonderleistungen", "Angebot anfragen"]),
    "sanitaer": ("Website für Sanitärbetriebe", "Sanitär, Heizung und Reparatur verständlich präsentieren", "Wenn Leistungen und Erreichbarkeit klar strukturiert sind, finden Kunden schneller den passenden Kontaktweg.", ["Installation und Bad", "Reparatur und Wartung", "Notdienst-Hinweis nur bei echtem Angebot"]),
    "steuerberater": ("Website für Steuerberater", "Eine klare Website für Steuerberatung schafft Orientierung", "Leistungsschwerpunkte, Zielgruppen und Erstkontakt sollten seriös, verständlich und ohne unnötige Hürden dargestellt werden.", ["Beratungsschwerpunkte", "Mandanten-Zielgruppen", "Erstgespräch anfragen"]),
    "tischlerei": ("Website für Tischlereien", "Maßarbeit braucht eine Website mit Charakter", "Materialien, Leistungen und Arbeitsweise lassen sich auch ohne große Galerie überzeugend und ehrlich zeigen.", ["Möbelbau und Innenausbau", "Türen, Fenster und Reparatur", "Projektanfrage"]),
    "zahnarzt": ("Website für Zahnarztpraxen", "Eine vertrauensvolle Website für Ihre Zahnarztpraxis", "Patientinnen und Patienten brauchen klare Informationen zu Praxis, Behandlungsschwerpunkten und Kontaktmöglichkeiten.", ["Prophylaxe und Behandlung", "Praxis und Team", "Termin anfragen"]),
}


def page(slug, data):
    label, title, intro, benefits = data
    title_e, intro_e = html.escape(title), html.escape(intro)
    benefit_html = "".join(f"<li>{html.escape(item)}</li>" for item in benefits)
    landing = "../../website-bau/" + slug + "/"
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": intro, "inLanguage": "de-DE", "author": {"@type": "Organization", "name": "Werkspree"}, "publisher": {"@type": "Organization", "name": "Werkspree"}}
    return f'''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_e} | Werkspree</title><meta name="description" content="{intro_e}">
<link rel="canonical" href="https://werkspree.bki-de.de/blog/website-{slug}/">
<meta property="og:type" content="article"><meta property="og:title" content="{title_e}"><meta property="og:description" content="{intro_e}"><meta property="og:url" content="https://werkspree.bki-de.de/blog/website-{slug}/"><meta property="og:site_name" content="Werkspree">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<style>:root{{--ink:#17212b;--muted:#5b6873;--primary:#164b62;--accent:#d39a4d;--paper:#fbfaf7;--line:#e1e7e7}}*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background:var(--paper);font:16px/1.75 system-ui,-apple-system,sans-serif}}.wrap{{width:min(860px,calc(100% - 36px));margin:auto}}nav{{padding:18px 0;border-bottom:1px solid var(--line);background:#ffffffcc}}nav a{{color:var(--primary);font-weight:800;text-decoration:none}}header{{padding:80px 0 62px;background:linear-gradient(135deg,#edf6f4,#fff)}}.kicker{{margin:0 0 14px;color:var(--accent);font-size:.78rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}}h1,h2{{line-height:1.15;letter-spacing:-.035em}}h1{{max-width:760px;margin:0;font-size:clamp(2.5rem,6vw,4.8rem)}}h2{{margin:0 0 16px;font-size:clamp(1.8rem,4vw,2.7rem)}}.lead{{max-width:700px;margin:22px 0 0;color:var(--muted);font-size:1.18rem}}main{{padding:64px 0}}section{{padding:24px 0 54px}}.card{{padding:26px;border:1px solid var(--line);border-radius:18px;background:#fff;box-shadow:0 12px 32px #17212b0b}}ul{{padding-left:1.25rem}}li{{padding:6px 0}}.cta{{margin-top:14px;display:inline-flex;padding:13px 20px;border-radius:999px;color:#fff;background:var(--primary);font-weight:800;text-decoration:none}}footer{{padding:30px 0;color:#d5e2e2;background:#102b38;font-size:.9rem}}footer a{{color:#fff}}@media(max-width:560px){{header{{padding:60px 0 45px}}main{{padding:42px 0}}}}</style></head>
<body><nav><div class="wrap"><a href="../../">Werkspree</a> · <a href="../../website-bau/">Website-Bau</a></div></nav>
<header><div class="wrap"><p class="kicker">{html.escape(label)}</p><h1>{title_e}</h1><p class="lead">{intro_e}</p></div></header>
<main><div class="wrap"><section><h2>Was eine gute Branchen-Website leisten sollte</h2><div class="card"><ul>{benefit_html}</ul><p>Wichtig ist nicht möglichst viel Inhalt, sondern eine klare Antwort auf drei Fragen: Was bietet der Betrieb an? Für wen ist er da? Wie kann ich Kontakt aufnehmen?</p></div></section><section><h2>Inhalte, die aktuell bleiben</h2><p>Öffnungszeiten, Leistungen, Einsatzgebiet und Kontaktangaben sollten regelmäßig geprüft werden. Nur bestätigte Betriebsdaten gehören auf die öffentliche Seite. Preise, Verfügbarkeiten und Versprechen sollten nur erscheinen, wenn sie tatsächlich gelten.</p><p>Wenn zunächst nur wenige Informationen vorliegen, ist eine kompakte, ehrliche Seite besser als eine lange Seite mit erfundenen Details.</p></section><section><h2>Der nächste Schritt</h2><p>Starten Sie mit einem kostenlosen Entwurf für Ihre Branche. Sie sehen sofort, wie Leistungen, Kontakt und regionale Auffindbarkeit zusammenspielen.</p><a class="cta" href="{landing}">Branchen-Entwurf ansehen</a></section></div></main>
<footer><div class="wrap">Werkspree · <a href="../../rechnungs-ocr/">Rechnungs-OCR</a> · <a href="../../e-rechnung-pruefen/">E-Rechnung prüfen</a></div></footer></body></html>'''


for slug, data in PAGES.items():
    target = ROOT / "blog" / f"website-{slug}" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page(slug, data), encoding="utf-8")
    print(target)
