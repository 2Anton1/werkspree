#!/usr/bin/env python3
"""
Werkspree Gemini Microsite Builder v3 — branchenspezifisches Design.

Jede Branche bekommt einen eigenen Design-Prompt mit:
- Eigener Farbpalette (CSS-Variablen)
- Branchenspezifischen Sektionen (Galerie, Preisliste, Team, etc.)
- Eigenem Layout-Raster (nicht mehr "alle gleich")
- Typografie- und Stimm-Vorgaben
- Mobile-First Responsive Design

Fallback: branchenspezifisches Template (build_fallback_template in build_microsite.py).
"""
import json
import os
import re
import urllib.request
from pathlib import Path

try:
    from site_quality import is_valid_html as is_complete_html
except ImportError:  # Import als Paket im lokalen Testlauf
    from microsites.pipeline.site_quality import is_valid_html as is_complete_html

ENV_PATH = Path.home() / ".hermes" / ".env"
OUT_DIR = Path(__file__).parent.parent / "sites"


def load_env():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_api_key():
    load_env()
    return os.environ.get("GOOGLE_API_KEY", "")


def call_gemini(prompt, max_tokens=8000, temperature=0.4):
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode())
    if "candidates" in data and data["candidates"]:
        return data["candidates"][0]["content"]["parts"][0].get("text", "")
    return ""


# ─── Branchenspezifische Design-Profile ─────────────────────────────────────

BRANCH_PROFILES = {
    "maler": {
        "colors": "Farbpalette: Tiefes Dunkelblau (#1B3A5F) als Primärfarbe, warmes Terrakotta (#E07A3F) als Akzent, Cremeweiß (#FAF6EF) als Hintergrund, anthrazit (#2D2419) für Text. Stil: vertrauenswürdig, handwerklich, warm.",
        "sections": "Sektionen: (1) Hero mit großem Titel + Tagline + CTA 'Kostenloses Angebot', (2) Über uns mit Inhaber-Story, (3) Leistungen als Karten-Grid (Innenanstrich, Fassaden, Tapezierarbeiten, Lackieren), (4) **Projektgalerie** mit 3-4 farbigen CSS-Blöcken als Beispiel-Projekte (verschiedene Farbmuster als Gradient-Boxes), (5) Warum wir? mit 3 USP-Karten (Erfahrung, Qualität, Termintreue), (6) Kontakt mit Adresse, Telefon, E-Mail, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: handwerklich-präzise, warm und einladend. Sanfte Schatten, abgerundete Ecken (12px), warme Gradient-Header.",
        "extras": "CSS-Visualisierung: 3-4 farbige Gradient-Boxen als 'Projektgalerie' (verschiedene Farbkombinationen als Hintergrund, z.B. blau-zu-creme, terrakotta-zu-gold).",
    },
    "friseur": {
        "colors": "Farbpalette: Dunkles Gold/Bronze (#C5A059) als Primärfarbe, tiefes Schwarz (#1A1A1A) als Kontrast, warmes Off-White (#F8F5F0) als Hintergrund. Stil: elegant, modern, edel.",
        "sections": "Sektionen: (1) Hero mit großem Titel + elegantem Untertitel + CTA 'Termin buchen', (2) Über uns mit Salon-Story, (3) **Preisliste** als elegante Tabelle mit Preis-Kategorien (Herrenhaarschnitt, Damen, Färben, Bar beard, etc.), (4) Leistungen als Karten, (5) Team/Stil mit 2-3 CSS-Avatar-Boxen (gradient circles mit Initialen), (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: edel-minimalistisch, viel Whitespace, feine Linien (1px borders), serifenbetonte Überschriften (oder font-weight 800). Bronze-Akzente auf dunklem Grund.",
        "extras": "CSS-Visualisierung: 2-3 runde Avatar-Boxen mit Gradient-Hintergrund und Initialen als 'Team'. Preisliste als gestylte Tabelle mit abwechselnden Zeilen-Hintergründen.",
    },
    "kosmetik": {
        "colors": "Farbpalette: Rosé/Pink (#D4A5A5) als Primärfarbe, tiefes Burgunder (#8B3A4A) als Akzent, warmes Cremeweiß (#FBF5F3) als Hintergrund. Stil: sanft, weiblich, luxuriös.",
        "sections": "Sektionen: (1) Hero mit sanftem Titel + Tagline + CTA 'Behandlung anfragen', (2) Über uns, (3) **Behandlungsliste** als elegante Cards (Gesichtsbehandlung, Wimpern, Brows, Maniküre), (4) **Warum wir?** mit 3 weichen Feature-Karten (Hautanalyse, Premium-Produkte, Entspannung), (5) Preisliste als Tabelle, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: sanft und luxuriös. Abgerundete Ecken (20px), sanfte Schatten, rosé Gradient-Header. Font-weight 300-400 für Body, 600 für Headers.",
        "extras": "Sanfte CSS-Wellen oder abgerundete decorative Shapes im Header-Bereich. Behandlungs-Cards mit sanften Hover-Effekten (transform: scale(1.02)).",
    },
    "fahrschule": {
        "colors": "Farbpalette: Navy (#0B1D3A) als Primärfarbe, Signal-Blau (#0066CC) als Akzent, Signal-Rot (#D9232D) für Highlights, hellblau-grau (#F0F4FA) als Hintergrund. Stil: dynamisch, vertrauenswürdig, jugendlich.",
        "sections": "Sektionen: (1) Hero mit dynamischem Titel + 'Jetzt Durchstarten' CTA, (2) Über uns mit Ausbilder-Vorstellung, (3) **Fahrzeug-Klassen** als Cards (B, A, BE, BF17, etc.), (4) **Warum wir?** mit 3 USPs (hohe Bestehensquote, moderne Fahrzeuge, flexible Zeiten), (5) **Ablauf** als nummerierte Steps (1. Anmeldung, 2. Theorie, 3. Praxis, 4. Prüfung), (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: dynamisch und klar. Klare Geometrie, kontrastreiche Buttons (weiß auf navy), Step-Counter mit großen Zahlen.",
        "extras": "Nummerierte Step-Liste mit großen Kreis-Zahlen (1, 2, 3, 4) als CSS-Circles. Fahrzeug-Klassen als Badge-Style Cards.",
    },
    "kfz": {
        "colors": "Farbpalette: Stahlgrau (#3A4A5C) als Primärfarbe, warnendes Orange/Gelb (#F5A623) als Akzent, helles Grau (#EEF1F4) als Hintergrund. Stil: technisch, kompetent, robust.",
        "sections": "Sektionen: (1) Hero mit Titel + 'Termin vereinbaren' CTA, (2) Über uns mit Werkstatt-Story, (3) **Leistungen** als Cards (Inspektion, Reparatur, Reifen, Bremsen, HU/AU), (4) **Service-Features** als Badge-Liste (Hol- und Bringservice, Leihwagen, Express-Reparatur), (5) **Ablauf** als nummerierte Steps, (6) Kontakt mit Werkstatt-Adresse, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: technisch-robust. Eckige oder leicht abgerundete Ecken (6px), kräftige Schatten, monotone Farbpalette mit gelb-orangem Akzent.",
        "extras": "Service-Badges als pill-shaped CSS-Elemente. Step-Liste mit Werkstatt-Icon-Style (CSS shapes wie Schrauben-Symbole oder Kontur-Zahlen).",
    },
    "reinigung": {
        "colors": "Farbpalette: Frisches Blau-Grün (#2E86AB) als Primärfarbe, helles Aqua (#A8DADC) als Akzent, sehr helles Grau-Weiß (#F8FAFA) als Hintergrund. Stil: sauber, frisch, zuverlässig.",
        "sections": "Sektionen: (1) Hero mit 'Frisch & Sauber' Titel + CTA 'Angebot anfragen', (2) Über uns, (3) **Leistungen** als Cards (Unterhaltsreinigung, Glasreinigung, Grundreinigung, Bauendreinigung), (4) **Warum wir?** mit 3 USPs (zertifiziert, umweltfreundlich, zuverlässig), (5) **Einsatzgebiet** als Liste von Orten/Regionen, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: sauber und hell. Viel Whitespace, sanfte Schatten, runde Ecken (12px). Blau-Grün-Gradient im Header.",
        "extras": "Sanfte CSS-Wellen im Header (SVG-Wellen oder border-radius decorative shapes). 'Zertifiziert'-Badge als CSS-Pill.",
    },
    "tischler": {
        "colors": "Farbpalette: Warmes Holz-Braun (#8B6F47) als Primärfarbe, dunkles Esche (#4A3C28) als Akzent, helles Cremeweiß (#FAF6EF) als Hintergrund. Stil: handwerklich, natürlich, massiv.",
        "sections": "Sektionen: (1) Hero mit 'Maßarbeit aus Holz' Titel + CTA 'Angebot anfragen', (2) Über uns mit Werkstatt-Story, (3) **Leistungen** als Cards (Möbelbau, Türen, Fenster, Restaurierung), (4) **Materialien** als Liste (Massivholz, Eiche, Buche, Esche), (5) **Referenzen** als CSS-Boxen mit Projekt-Beschreibungen (Gradient-Hintergründe in Holzfarben), (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: handwerklich-massiv. Warme Farben, rustikale Schatten, natürliche Texturen als CSS-Gradients (holzmuster).",
        "extras": "CSS-Holzmuster-Gradient als dekoratives Element im Header oder in Referenz-Boxen (repeating-linear-gradient für Holz-Linien-Effekt).",
    },
    "dachdecker": {
        "colors": "Farbpalette: Dunkles Schiefer-Blau (#2C3E50) als Primärfarbe, warmes Kupfer (#B87333) als Akzent, helles Grau-Weiß (#F5F5F5) als Hintergrund. Stil: robust, zuverlässig, wetterfest.",
        "sections": "Sektionen: (1) Hero mit 'Ihr Dach in besten Händen' Titel + CTA 'Kostenloses Angebot', (2) Über uns, (3) **Leistungen** als Cards (Neueindeckung, Sanierung, Reparatur, Notdienst), (4) **Dachmaterialien** als Liste (Ziegel, Schiefer, Metalldach, Flachdach), (5) **Notdienst-Hinweis** als hervorgehobene Box mit Telefon-Link, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: robust und wetterfest. Kräftige Farben, klare Linien, kontrastreiche Buttons. Notdienst-Box in Kupfer/Rot mit pulsierendem CSS-Effekt.",
        "extras": "Notdienst-Box mit CSS-Animation (pulse auf background-color). Material-Liste als Badge-Style mit CSS-Pills.",
    },
    "metzgerei": {
        "colors": "Farbpalette: Kräftiges Rot (#9B2D2D) als Primärfarbe, warmes Gold (#D4A843) als Akzent, helles Cremeweiß (#FAF6EF) als Hintergrund. Stil: traditionell, handwerklich, appetitlich.",
        "sections": "Sektionen: (1) Hero mit 'Fleisch & Wurst aus eigener Herstellung' + CTA 'Bestellen', (2) Über uns mit Traditions-Story, (3) **Sortiment** als Cards (Frischfleisch, Wurstwaren, Feinkost, Partyservice), (4) **Spezialitäten** als hervorgehobene Liste, (5) **Wo gibt's uns?** mit Adresse, (6) Öffnungszeiten, (7) Footer",
        "mood": "Stil: traditionell und warm. Kräftige Farben, klassische Typografie, appetitliche Darstellung. Karten mit warmen Hover-Effekten.",
        "extras": "Spezialitäten als große badge-artige Pills. Traditionshinweis als CSS-Banner mit Gold-Rand.",
    },
    "gartner": {
        "colors": "Farbpalette: Frisches Grün (#2D6A4F) als Primärfarbe, helles Frühlingsgrün (#95D5B2) als Akzent, warmes Sand (#F4F1DE) als Hintergrund. Stil: natürlich, lebendig, pflegerisch.",
        "sections": "Sektionen: (1) Hero mit 'Ihr Garten in besten Händen' + CTA 'Beratung anfragen', (2) Über uns, (3) **Leistungen** als Cards (Gartengestaltung, Pflege, Baumschnitt, Saisonarbeit), (4) **Pflanzenwelt** als Liste, (5) **Saisonkalender** als kleine CSS-Tabelle mit Monaten und Angeboten, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: natürlich und lebendig. Sanfte Schatten, runde Ecken (16px), Grün-Gradient im Header. Sans-serif mit weichen Lettern.",
        "extras": "Saisonkalender als gestylte Mini-Tabelle. Pflanzen-CSS-Icons (circle mit Gradient als 'Blume').",
    },
    "gartenbau": {
        "colors": "Farbpalette: Frisches Grün (#2D6A4F) als Primärfarbe, helles Frühlingsgrün (#95D5B2) als Akzent, warmes Sand (#F4F1DE) als Hintergrund. Stil: natürlich, lebendig, pflegerisch.",
        "sections": "Sektionen: (1) Hero mit 'Ihr Garten in besten Händen' + CTA 'Beratung anfragen', (2) Über uns, (3) **Leistungen** als Cards (Gartengestaltung, Pflege, Baumschnitt, Saisonarbeit), (4) **Pflanzenwelt** als Liste, (5) **Saisonkalender** als kleine CSS-Tabelle mit Monaten und Angeboten, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: natürlich und lebendig. Sanfte Schatten, runde Ecken (16px), Grün-Gradient im Header.",
        "extras": "Saisonkalender als gestylte Mini-Tabelle.",
    },
    "sanitär": {
        "colors": "Farbpalette: Stahl-Blau (#2C5F7F) als Primärfarbe, helles Wasser-Blau (#A8C8E0) als Akzent, sehr helles Grau (#F0F4F8) als Hintergrund. Stil: technisch, sauber, zuverlässig.",
        "sections": "Sektionen: (1) Hero mit 'Installation & Wartung' + CTA 'Termin anfragen', (2) Über uns, (3) **Leistungen** als Cards (Bad-Installation, Heizung, Reparatur, Wartung), (4) **Notdienst** als hervorgehobene Box mit Telefon-Link, (5) **Warum wir?** mit 3 USPs, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: technisch und sauber. Klare Linien, blaue Gradient-Header, runde Ecken (10px).",
        "extras": "Notdienst-Box mit CSS-Pulse-Animation. USP-Karten mit blauen Icon-Circles.",
    },
    "heizung": {
        "colors": "Farbpalette: Warmes Kupfer (#B87333) als Primärfarbe, dunkles Anthrazit (#2D2419) als Akzent, helles Cremeweiß (#FAF6EF) als Hintergrund. Stil: warm, technisch, zuverlässig.",
        "sections": "Sektionen: (1) Hero mit 'Wärme zuverlässig installiert' + CTA 'Angebot anfragen', (2) Über uns, (3) **Leistungen** als Cards (Heizungsbau, Wartung, Reparatur, Solar), (4) **Notdienst** als hervorgehobene Box, (5) Kontakt, (6) Öffnungszeiten, (7) Footer",
        "mood": "Stil: warm und technisch. Kupfer-Gradient-Header, klare Layout.",
        "extras": "Notdienst-Box mit pulsierendem CSS-Effekt. Wärme-CSS-Visualisierung (sanftes orangenes Glow).",
    },
    "zahnarzt": {
        "colors": "Farbpalette: Sanftes Mint-Blau (#4A9EAB) als Primärfarbe, helles Aqua (#B8E0E6) als Akzent, sehr helles Weiß (#F8FAFA) als Hintergrund. Stil: klinisch, vertrauensvoll, modern.",
        "sections": "Sektionen: (1) Hero mit 'Ihre Zahngesundheit' + CTA 'Termin buchen', (2) Über uns mit Praxis-Story, (3) **Leistungen** als Cards (Prophylaxe, Behandlung, Implantate, Ästhetik), (4) **Team** mit CSS-Avatar-Boxen, (5) **Für Patienten** mit Info-Liste, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: klinisch und vertrauensvoll. Sehr sauber, viel Whitespace, sanfte Schatten. Mint-Blau-Gradient im Header.",
        "extras": "Team-Avatare als runde CSS-Boxes mit Initialen. Für-Patienten-Liste mit Checkmark-Icons (CSS).",
    },
    "physiotherapie": {
        "colors": "Farbpalette: Sanftes Teal (#1B7A7A) als Primärfarbe, helles Mint (#A8E6CF) als Akzent, warmes Off-White (#F8F6F3) als Hintergrund. Stil: heilsam, professionell, beruhigend.",
        "sections": "Sektionen: (1) Hero mit 'Ihre Gesundheit in guten Händen' + CTA 'Termin vereinbaren', (2) Über uns, (3) **Behandlungen** als Cards (Manuelle Therapie, Lymphdrainage, Sportphysio, Ergonomie), (4) **Was wir behandeln** als Liste, (5) Team, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: beruhigend und professionell. Sanfte Farben, viel Whitespace, runde Ecken (16px). Teal-Gradient.",
        "extras": "Behandlungs-Cards mit sanften Hover-Effekten. 'Was wir behandeln' als Badge-Liste mit Mint-Pills.",
    },
    "optiker": {
        "colors": "Farbpalette: Dunkles Indigo (#3D3D6B) als Primärfarbe, helles Lilac (#B8A9D9) als Akzent, warmes Grau-Weiß (#F5F5F8) als Hintergrund. Stil: modern, klar, sehend.",
        "sections": "Sektionen: (1) Hero mit 'Klares Sicht, klarer Stil' + CTA 'Beratung', (2) Über uns, (3) **Leistungen** als Cards (Sehtest, Brillen, Kontaktlinsen, Beratung), (4) **Marken** als Logo-Liste (CSS-Boxes mit Namen), (5) Kontakt, (6) Öffnungszeiten, (7) Footer",
        "mood": "Stil: modern und klar. Klare Linien, Indigo-Gradient, serifenbetonte Überschriften.",
        "extras": "Marken-Liste als kleine CSS-Pills/Boxes. Brillen-CSS-Visualisierung (zwei verbundene Kreise).",
    },
    "bäcker": {
        "colors": "Farbpalette: Warmes Gold-Braun (#D4A843) als Primärfarbe, tiefes Braun (#6B4423) als Akzent, helles Cremeweiß (#FAF6EF) als Hintergrund. Stil: warm, traditionell, appetitlich.",
        "sections": "Sektionen: (1) Hero mit 'Frisch gebacken jeden Tag' + CTA 'Komm vorbei', (2) Über uns mit Traditions-Story, (3) **Sortiment** als Cards (Brot, Brötchen, Kuchen, Torten), (4) **Tagesangebot** als hervorgehobene Box, (5) **Stehcafé** Einladung, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: warm und traditionell. Gold-Braun-Gradient, runde Ecken, appetitliche Darstellung.",
        "extras": "Tagesangebot als hervorgehobene CSS-Box mit Gold-Rand. Traditions-Banner mit 'Seit YYYY' (falls Inhaber-Daten vorhanden).",
    },
    "schlüsseldienst": {
        "colors": "Farbpalette: Dunkles Stahlgrau (#3A3A3A) als Primärfarbe, gelb (#FFD93D) als Akzent, helles Grau (#F0F0F0) als Hintergrund. Stil: schnell, zuverlässig, Notdienst.",
        "sections": "Sektionen: (1) Hero mit 'Schnell. Zuverlässig. Vor Ort.' + CTA 'Jetzt anrufen', (2) **24h Notdienst** als hervorgehobene Box mit Telefon-Link, (3) **Leistungen** als Cards (Türöffnung, Schlossaustausch, Sicherheitstechnik, Beratung), (4) **Service-Gebiete** als Liste, (5) Kontakt, (6) Footer",
        "mood": "Stil: schnell und Notdienst-orientiert. Gelbe Akzente auf dunklem Grund, klare CTA 'Jetzt anrufen'.",
        "extras": "24h-Notdienst-Box mit pulsierender gelber CSS-Animation. Großer Telefon-CTA-Button.",
    },
    "florist": {
        "colors": "Farbpalette: Sanftes Rosé (#E8B4B8) als Primärfarbe, frisches Grün (#7CB342) als Akzent, warmes Elfenbein (#FBF5F3) als Hintergrund. Stil: natürlich, blühend, kreativ.",
        "sections": "Sektionen: (1) Hero mit 'Blumen, die Freude machen' + CTA 'Bestellen', (2) Über uns, (3) **Anlässe** als Cards (Hochzeit, Geburtstag, Trauer, Saison), (4) **Sträuße & Arrangements** als Liste, (5) **Saison-Floristik** als hervorgehobene Box, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: kreativ und blühend. Sanfte Gradient-Header, runde Ecken (20px), verspielte Typografie.",
        "extras": "Saison-Box mit wechselndem Gradient (Frühling: grün-rosé, Sommer: gelb-orange). CSS-Blumen-Dekoration (runde Gradient-Circles als 'Blüten').",
    },
    "autowerkstatt": {
        "colors": "Farbpalette: Stahlgrau (#3A4A5C) als Primärfarbe, warnendes Orange (#F5A623) als Akzent, helles Grau (#EEF1F4) als Hintergrund. Stil: technisch, kompetent, robust.",
        "sections": "Sektionen: (1) Hero mit Titel + 'Termin vereinbaren' CTA, (2) Über uns mit Werkstatt-Story, (3) **Leistungen** als Cards (Inspektion, Reparatur, Reifen, Bremsen, HU/AU), (4) **Service-Features** als Badge-Liste (Hol- und Bringservice, Leihwagen, Express), (5) **Ablauf** als nummerierte Steps, (6) Kontakt, (7) Öffnungszeiten, (8) Footer",
        "mood": "Stil: technisch-robust. Eckige oder leicht abgerundete Ecken (6px), kräftige Schatten.",
        "extras": "Service-Badges als pill-shaped CSS-Elemente. Step-Liste mit großen Zahlen-Circles.",
    },
}

# Default für unbekannte Branchen
DEFAULT_PROFILE = {
    "colors": "Farbpalette: Professonelles Dunkelblau (#1B3A5F) als Primärfarbe, warmes Gold (#D4A843) als Akzent, helles Cremeweiß (#FAF6EF) als Hintergrund, anthrazit (#2D2419) für Text. Stil: professionell, vertrauenswürdig.",
    "sections": "Sektionen: (1) Hero mit großem Titel + Tagline + CTA, (2) Über uns, (3) **Leistungen** als Cards-Grid, (4) **Warum wir?** mit 3 USP-Karten (Erfahrung, Qualität, Termintreue), (5) Kontakt mit Adresse, Telefon, E-Mail, (6) Öffnungszeiten, (7) Footer. Jede Sektion hat eigene Überschrift und klare visuelle Trennung.",
    "mood": "Stil: professionell und modern. Sanfte Schatten, abgerundete Ecken (12px), Gradient-Header. Klare visuelle Hierarchie mit großen H1, mittleren H2, gut lesbarem Body-Text.",
    "extras": "USP-Karten mit Icon-Circles (CSS). Hover-Effekte auf Cards (transform: scale(1.02), transition 0.3s).",
}


def get_profile(branch):
    """Liefert das branchenspezifische Design-Profil."""
    b = (branch or "").lower().strip()
    # Match gegen Keys (auch Teil-Matches)
    for key, profile in BRANCH_PROFILES.items():
        if key in b:
            return profile
    return DEFAULT_PROFILE


# ─── Prompt-Bau ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Du bist ein professioneller Webdesigner. Du erstellst vollständige, eigenständige HTML5-Seiten mit inline CSS.

ABSOLUTE REGELN:
1. Antworte AUSSCHLIESSLICH mit HTML — beginnt mit <!DOCTYPE html>, endet mit </html>
2. KEIN Markdown, KEIN Code-Block (```), KEIN Plan, KEIN Text außerhalb des HTML
3. Nutze die ECHTEN Daten aus der Anfrage — KEINE Platzhalter, KEINE Erfindungen
4. Wenn Daten fehlen: weglassen oder "Auf Anfrage" — NIE "Max Mustermann" oder "Musterstraße"
5. ALLES inline in einer einzigen HTML-Datei — <style> im <head>, kein externes CSS, kein JS
6. Mobil-optimiert: viewport meta, responsive grid/flex, max-width Container
7. Schöne Typografie: Google Fonts (Inter oder Poppins via <link>), klare Hierarchie
8. Telefon als <a href="tel:...">, E-Mail als <a href="mailto:...">
9. Im Footer: "© 2026 {Firma}. Demo-Website erstellt von Werkspree — KI-Automatisierung für kleine Unternehmen"
10. Responsive Breakpoints bei 768px und 480px
11. Hover-Effekte auf interaktiven Elementen (transition, transform)
12. Sanfte Animationen (nur CSS, kein JavaScript)"""


def build_prompt(lead):
    """Baut einen branchenspezifischen Prompt für Gemini."""
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

    profile = get_profile(branch)

    # Produkte formatieren
    if products and isinstance(products[0], (list, tuple)):
        prod_text = "\n".join(f"- {p[0]}: {p[1] if len(p) > 1 else ''}" for p in products[:6])
    elif products:
        prod_text = "\n".join(f"- {p}" for p in products[:6])
    else:
        prod_text = ""

    # Öffnungszeiten
    hours_text = ""
    days_map = {"Mo": "Montag", "Di": "Dienstag", "Mi": "Mittwoch",
                "Do": "Donnerstag", "Fr": "Freitag", "Sa": "Samstag", "So": "Sonntag"}
    if hours:
        for k, v in hours.items():
            hours_text += f"{days_map.get(k, k)}: {v}\n"

    prompt = f"""Erstelle eine professionelle, individuell gestaltete Microsite für folgenden Betrieb:

**Firma:** {name}
**Branche:** {branch}
**Stadt:** {city}
**Adresse:** {address or 'Nicht verfügbar'}
**Telefon:** {phone or 'Nicht verfügbar'}
**E-Mail:** {email or 'Nicht verfügbar'}
**Inhaber:** {owner or 'Nicht verfügbar'}

**Über uns (echter Text, verwende ihn!):**
{about or 'Nicht verfügbar — schreibe einen kurzen, professionellen Text basierend auf Branche und Stadt.'}

**Leistungen (verwende diese als echte Daten; falls leer, zeige keine erfundenen Details):**
{prod_text or 'Nicht verfügbar — verwende nur eine neutrale Rubrik "Leistungen auf Anfrage".'}

**Öffnungszeiten:**
{hours_text or 'Nicht verfügbar — schreibe typische Öffnungszeiten für diese Branche.'}

---

DESIGN-VORGABEN FÜR DIESE BRANCHE:

{profile['colors']}

{profile['sections']}

{profile['mood']}

{profile['extras']}

---

Erstelle JETZT die vollständige HTML5-Seite. Die Seite soll:
- Professionell und ansprechend aussehen — keine generische Vorlage
- Echten branchenspezifischen Charakter haben (nicht alle Branchen gleich!)
- Mobil-optimiert sein (responsive grid/flex, viewport meta)
- Google Fonts nutzen (Inter für Body, Poppins oder Montserrat für Überschriften)
- Sanfte CSS-Animationen und Hover-Effekte
- Eine klare CTA-Schaltfläche im Hero-Bereich
- Kontakt-Sektion mit tel: und mailto: Links
- Footer mit Copyright und Werkspree-Hinweis

Beginne mit <!DOCTYPE html> und enden mit </html>. KEIN Text außerhalb des HTML."""

    return prompt


def extract_html(text):
    if not text:
        return None
    # Bevorzugt: vollständiges Dokument
    m = re.search(r"<!DOCTYPE[^>]*>[\s\S]*?</html>", text, re.IGNORECASE)
    if m:
        return m.group(0)
    m = re.search(r"<html[\s\S]*?</html>", text, re.IGNORECASE)
    if m:
        return "<!DOCTYPE html>\n" + m.group(0)
    return None


def is_valid_html(html):
    return is_complete_html(html, minimum_chars=3000)


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
            else:
                print(f"  Gemini-Versuch {attempt+1}: HTML invalid (size={len(html) if html else 0})")
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
    words = name.split()[:3]
    s = " ".join(words).lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:30]
    slug = lead.get("slug") or (s if s else "site")
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)

    success = generate_microsite(lead, out / "index.html")
    if success:
        site_url = f"https://werkspree.bki-de.de/microsites/sites/{slug}/"
        lead["site_url"] = site_url
        lead_path.write_text(json.dumps(lead, ensure_ascii=False, indent=2))
        print(f"✓ Microsite erstellt: {out / 'index.html'}")
        print(f"✓ Site-URL: {site_url}")
    else:
        print("✗ Gemini-Build fehlgeschlagen")
        sys.exit(1)
