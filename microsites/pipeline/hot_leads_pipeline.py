#!/usr/bin/env python3
"""
Werkspree Microsite-Pipeline — Stufe 1: "Heißeste Leads" Scraper

Kombiniert zwei Quellen für maximale Präzision bei minimalem Verbrauch:

1. GOOGLE MAPS: Sucht z.B. "restaurant berlin mitte", extrahiert Name +
   Bewertung + Kategorie + Adresse aus der Kartenansicht. Filtert auf
   Rating >= RATING_THRESHOLD (Qualitäts-/Zahlungskraft-Proxy: gut bewertete
   Betriebe investieren in Qualität und können sich eine Website leisten).
   Für jeden Kandidaten wird die Maps-Detailseite gescraped, um zu prüfen,
   ob eine EIGENE Website existiert (nicht Google/Social/Aggregator-Links).

2. GELBESEITEN: Für Kandidaten OHNE eigene Website wird der Firmenname auf
   GelbeSeiten gesucht — dort haben auch reine "keine eigene Website"-Betriebe
   oft ein E-Mail-Kontaktfeld (mailto: Link auf der Profilseite). Das liefert
   den fehlenden Kontaktweg, ohne den wir nicht kontaktieren könnten.

Ausgabe: hot_leads.json — nur Leads, die BEIDE Kriterien erfüllen:
  - keine eigene Website (oder klar veraltete, s.u.)
  - eine gefundene E-Mail-Adresse

Diese strikte Doppelfilterung ist bewusst: sie hält die Anzahl der Leads
pro Lauf klein (typisch 1-5 aus 20 Kandidaten), was sowohl Firecrawl-Credits
als auch nachgelagerten Lovable-Verbrauch (nur für "heiße" Leads bauen!)
niedrig hält.
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

RATING_THRESHOLD = 4.4

EXCLUDE_DOMAINS = [
    "google.com", "goo.gl", "maps.app.goo.gl", "facebook.com", "instagram.com",
    "opentable.com", "tripadvisor.com", "yelp.com", "lieferando.de",
    "ubereats.com", "wolt.com", "thefork.com", "quandoo.de", "resmio.com",
    "gelbeseiten.de", "wogibtswas.de", "11880.com", "goldenpages", "linktr.ee",
    "wa.me", "whatsapp.com", "zenchef.com", "quandoo.com", "bookatable.com",
    "googleusercontent.com", "maps.google", "booking.com", "eventbrite.com",
]

GENERIC_EMAIL_BLOCKLIST = ["example", "spam", "meinungsmeister", "webmaster@", "sentry.io", "wixpress.com"]


def firecrawl_scrape(url, out_path, wait_for=4000, formats="markdown,links", timeout=60):
    result = subprocess.run(
        ["firecrawl", "scrape", url, "--wait-for", str(wait_for),
         "-f", formats, "-o", str(out_path)],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.returncode == 0


def parse_maps_search(markdown):
    """Parst die kompakte Google-Maps-Kartenansicht (/maps/search/...).
    Jeder Eintrag: [Name](maps/place-link) \n\n Name \n\n RATING \n\n Category··Address
    """
    entries = []
    blocks = re.split(r'\n(?=\[)', markdown)
    for block in blocks:
        m_link = re.search(r'\[([^\]]+)\]\((https://www\.google\.com/maps/place/[^)]+)\)', block)
        if not m_link:
            continue
        name = m_link.group(1).replace("\\", "").strip()
        place_url = m_link.group(2)
        m_rating = re.search(r'\n(\d\.\d)\n', block)
        rating = float(m_rating.group(1)) if m_rating else None
        m_cat = re.search(r'\n([^\n]+?)··([^\n]+)', block)
        category, address = "", ""
        if m_cat:
            category, address = m_cat.group(1).strip(), m_cat.group(2).strip()
            category = re.sub(r'^[\d.]+\s*$', '', category).strip() or category
        else:
            m_cat = re.search(r'\n([^\n]+?)·[^\n]*·([^\n]+)', block)
            if m_cat:
                category, address = m_cat.group(1).strip(), m_cat.group(2).strip()
        entries.append({
            "name": name, "maps_url": place_url, "rating": rating,
            "category": category, "address": address,
        })
    seen, unique = set(), []
    for e in entries:
        if e["name"] not in seen and len(e["name"]) > 2:
            seen.add(e["name"])
            unique.append(e)
    return unique


def search_maps(query, limit=20):
    url = f"https://www.google.com/maps/search/{quote(query)}"
    tmp = Path("/tmp/maps_search_tmp.json")
    if not firecrawl_scrape(url, tmp, wait_for=4500, timeout=60):
        print(f"Scrape fehlgeschlagen: {url}")
        return []
    data = json.loads(tmp.read_text())
    entries = parse_maps_search(data.get("markdown", ""))
    return entries[:limit]


def check_website_and_phone(maps_url, idx):
    """Scraped die Maps-Detailseite: externe Website (falls vorhanden) + Telefon."""
    tmp = Path(f"/tmp/place_detail_{idx}.json")
    if not firecrawl_scrape(maps_url, tmp, wait_for=3500, timeout=45):
        return None, None
    try:
        data = json.loads(tmp.read_text())
    except Exception:
        return None, None
    links = data.get("links", [])
    website, phone = None, None
    for link in links:
        low = link.lower()
        if low.startswith("tel:"):
            phone = link.replace("tel:", "")
            continue
        if low.startswith("mailto:") or any(dom in low for dom in EXCLUDE_DOMAINS):
            continue
        if low.startswith("http"):
            website = link.rstrip("/")
            break  # erster externer Link = die Website
    return website, phone


def is_outdated_website(website):
    """Sehr einfache Heuristik: wir scrapen die Startseite und suchen nach
    Signalen für eine veraltete/keine echte Firmenwebsite (reine Aggregator-
    Landingpages, Wix-Baukasten-Freebies ohne Inhalt, tote Domains)."""
    if not website:
        return True
    tmp = Path("/tmp/site_check_tmp.md")
    if not firecrawl_scrape(website, tmp, wait_for=2000, formats="markdown", timeout=30):
        return True  # nicht erreichbar = de facto keine nutzbare Website
    content = tmp.read_text().lower()
    if len(content) < 400:
        return True  # praktisch leere Seite
    outdated_signals = ["diese website wird nicht mehr betreut", "under construction",
                         "baustelle", "coming soon", "domain is for sale", "parked domain"]
    return any(s in content for s in outdated_signals)


def extract_company_details_gelbeseiten(profile_url, company_name):
    """Scraped die GelbeSeiten-Profilseite und extrahiert echte Firmendetails:
    Beschreibung, Leistungen, Öffnungszeiten, Inhaber, E-Mail (aus Impressum/Links)."""
    tmp = Path("/tmp/gs_profile_detail.json")
    if not firecrawl_scrape(profile_url, tmp, wait_for=3000, formats="markdown,html", timeout=45):
        return {}
    try:
        data = json.loads(tmp.read_text())
    except Exception:
        return {}
    md = data.get("markdown", "")
    html = data.get("html", "")
    details = {}

    # Beschreibung: Textblock nach "Über uns" / "Beschreibung" / erster längerer Absatz
    desc_m = re.search(r'(?:Über\s+uns|Bescheibung|Beschreibung|Profil)\s*[:\n-]+(.*?)(?:\n\n|\Z)', md, re.IGNORECASE | re.DOTALL)
    if desc_m:
        details["about"] = " ".join(desc_m.group(1).split())[:600]
    else:
        # erster Absatz mit >= 80 Zeichen
        for para in re.split(r'\n\s*\n', md):
            if len(para.strip()) >= 80 and not para.strip().startswith("http"):
                details["about"] = para.strip()[:600]
                break

    # Leistungen: Zeilen mit Aufzählung (•, -, *) oder "Leistungen" Abschnitt
    leist = []
    leist_m = re.search(r'Leistungen\s*[:\n-]+(.*?)(?:\n\n|\Z)', md, re.IGNORECASE | re.DOTALL)
    if leist_m:
        leist = [l.strip(" •-*–") for l in leist_m.group(1).splitlines() if l.strip()]
    if not leist:
        for line in md.splitlines():
            s = line.strip(" •-*–")
            if 3 <= len(s) <= 60 and not s.startswith("http") and s[0].isupper():
                leist.append(s)
    details["products"] = leist[:6]

    # Öffnungszeiten
    hours = {}
    for tag in ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]:
        m = re.search(rf'{tag}\w*\.?\s*[:\-]?\s*(\d{{1,2}}[:.]\d{{2}}\s*[-–]\s*\d{{1,2}}[:.]\d{{2}})', md)
        if m:
            hours[tag] = m.group(1).replace(".", ":")
    if hours:
        details["opening_hours"] = hours

    # Inhaber: "Inhaber: NAME" oder "Geschäftsführer: NAME"
    inh = re.search(r'(?:Inhaber|Geschäftsführer|Inhaberin|Geschäftsführerin)\s*[:\-]\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){0,3})', md)
    if inh:
        details["owner"] = inh.group(1).strip()

    # E-Mail: mailto: aus html, bevorzugt Impressum-Links
    emails = re.findall(r'mailto:([\w.\-+]+@[\w.\-]+\.\w{2,})', html, re.IGNORECASE)
    emails += re.findall(r'([\w.\-+]+@[\w.\-]+\.\w{2,})', md)
    block = GENERIC_EMAIL_BLOCKLIST
    emails = [e for e in emails if not any(b in e.lower() for b in block)]
    if emails:
        details["email_candidates"] = list(dict.fromkeys(emails))[:3]
    return details


def validate_email_for_company(email, company_name):
    """Prüft, ob die E-Mail plausibel zur Firma gehört.
    Heuristik: Domain-Teil enthält >= 1 Token des Firmennamens (oder umgekehrt),
    ODER die E-Mail-Local-Part enthält einen Firmen-Token.
    Gibt (is_valid, reason) zurück."""
    if not email or "@" not in email:
        return False, "keine E-Mail"
    local, domain = email.lower().split("@", 1)
    domain_base = domain.split(".")[0]  # z.B. 'tischlerei-jahn' aus 'tischlerei-jahn.de'
    comp_tokens = [t for t in re.findall(r"[a-z0-9äöüß]+", company_name.lower()) if len(t) >= 3]
    if not comp_tokens:
        return False, "Firmenname unparsebar"
    # Token im Domain-Base?
    for tok in comp_tokens:
        if tok in domain_base or tok in local:
            return True, f"Match: '{tok}' in domain/local"
    # bekannte freie Mailer -> trotzdem ok, aber als "nicht verifiziert" markieren
    free = ["gmail", "web.de", "gmx", "yahoo", "outlook", "hotmail", "icloud", "t-online", "mail.de", "freenet"]
    if any(f in domain for f in free):
        return True, "Freemailer (nicht firmenspezifisch, aber plausibel)"
    return False, f"kein Firmen-Token in '{domain}' / '{local}'"



def extract_email_from_website_imprint(website):
    """Scrapt die Website (Startseite + Impressum) und extrahiert die echte
    Firmen-E-Mail aus dem Impressum. Gibt (email, reason) zurück."""
    if not website:
        return "", "keine Website"
    # Impressum-Seite finden
    base = website.rstrip("/")
    imprint_candidates = [
        f"{base}/impressum", f"{base}/impressum.html", f"{base}/imprint",
        f"{base}/kontakt", f"{base}/ueber-uns", base,
    ]
    for url in imprint_candidates:
        tmp = Path("/tmp/imprint_check.json")
        if not firecrawl_scrape(url, tmp, wait_for=2500, formats="markdown,html", timeout=35):
            continue
        try:
            data = json.loads(tmp.read_text())
        except Exception:
            continue
        md = data.get("markdown", "")
        html = data.get("html", "")
        # E-Mail aus markdown + html (mailto:)
        emails = re.findall(r"[\w.\-+]+@[\w.\-]+\.\w{2,}", md)
        emails += re.findall(r'mailto:([\w.\-+]+@[\w.\-]+\.\w{2,})', html, re.IGNORECASE)
        emails = [e for e in emails if not any(b in e.lower() for b in GENERIC_EMAIL_BLOCKLIST)]
        if emails:
            return emails[0], f"Impressum {url}"
    return "", "keine E-Mail im Impressum"


def extract_email_from_maps(maps_url):
    """Scrapt die Google-Maps-Detailseite und extrahiert E-Mail aus dem
    Kontakt-Block (oft direkt zur Firma gehörig). Gibt (email, reason) zurück."""
    if not maps_url:
        return "", "keine Maps-URL"
    tmp = Path("/tmp/maps_email_check.json")
    if not firecrawl_scrape(maps_url, tmp, wait_for=2500, formats="markdown,html", timeout=35):
        return "", "Maps-Scrape fehlgeschlagen"
    try:
        data = json.loads(tmp.read_text())
    except Exception:
        return "", "JSON-Fehler"
    md = data.get("markdown", "")
    html = data.get("html", "")
    emails = re.findall(r"[\w.\-+]+@[\w.\-]+\.\w{2,}", md)
    emails += re.findall(r'mailto:([\w.\-+]+@[\w.\-]+\.\w{2,})', html, re.IGNORECASE)
    emails = [e for e in emails if not any(b in e.lower() for b in GENERIC_EMAIL_BLOCKLIST)]
    if emails:
        return emails[0], "Maps-Kontaktblock"
    return "", "keine E-Mail in Maps"


def find_email_and_details_on_gelbeseiten(company_name, region):
    """Sucht die GelbeSeiten-Profilseite der Firma, extrahiert echte Details
    (Beschreibung, Leistungen, Öffnungszeiten, Inhaber) UND eine verifizierte
    E-Mail. Gibt (email, details, verification_reason) zurück."""
    query = f'site:gelbeseiten.de/gsbiz/ "{company_name}" {region}'
    tmp = Path("/tmp/gs_search_tmp.md")
    result = subprocess.run(
        ["firecrawl", "search", query, "--limit", "3", "-o", str(tmp), "--json"],
        capture_output=True, text=True, timeout=45,
    )
    if result.returncode != 0 or not tmp.exists():
        return "", {}, "keine GelbeSeiten-Suche"
    try:
        results = json.loads(tmp.read_text())
    except Exception:
        return "", {}, "JSON-Fehler"
    if isinstance(results, dict) and isinstance(results.get("data"), dict):
        urls = results["data"].get("web", [])
    elif isinstance(results, dict):
        urls = results.get("results", [])
    else:
        urls = results
    company_tokens = [t.lower() for t in re.findall(r"[a-z0-9äöüß]+", company_name) if len(t) >= 3]
    ranked = []
    for r in urls if isinstance(urls, list) else []:
        u = r.get("url", "") if isinstance(r, dict) else str(r)
        title = r.get("title", "") if isinstance(r, dict) else ""
        if "gelbeseiten.de/gsbiz/" not in u:
            continue
        haystack = (u + " " + title).lower()
        match_count = sum(1 for token in company_tokens if token in haystack)
        ranked.append((match_count, u))
    if not ranked:
        return "", {}, "keine Profilseite"
    ranked.sort(reverse=True)
    profile_url = ranked[0][1]

    details = extract_company_details_gelbeseiten(profile_url, company_name)
    # E-Mail-Kandidaten aus Details, dann Validierung gegen Firmenname
    candidates = details.pop("email_candidates", [])
    for email in candidates:
        ok, reason = validate_email_for_company(email, company_name)
        if ok:
            return email, details, reason
    return "", details, "keine verifizierte E-Mail (Aggregator/Formular?)"


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 hot_leads_pipeline.py '<branche>' '<region>' [limit] [max_checks]")
        sys.exit(1)
    branch, region = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    max_checks = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    query = f"{branch} {region}"
    print(f"=== Google Maps Suche: '{query}' ===")
    entries = search_maps(query, limit=limit)
    print(f"{len(entries)} Ergebnisse gefunden")

    hot_candidates = [e for e in entries if e.get("rating") and e["rating"] >= RATING_THRESHOLD]
    print(f"{len(hot_candidates)} mit Rating >= {RATING_THRESHOLD} (Zahlungskraft-Proxy)")

    hot_leads = []
    checked = 0
    for e in hot_candidates:
        if checked >= max_checks:
            break
        checked += 1
        print(f"\n[{checked}/{min(max_checks, len(hot_candidates))}] {e['name']}")
        website, phone = check_website_and_phone(e["maps_url"], checked)
        e["phone"] = phone
        time.sleep(1.5)

        if website and not is_outdated_website(website):
            print(f"  -> hat aktuelle Website ({website}) — kein Kandidat")
            continue

        print(f"  -> keine/veraltete Website" + (f" ({website})" if website else ""))
        e["old_or_no_website"] = website or ""

        email, details, reason = find_email_and_details_on_gelbeseiten(e["name"], region)
        time.sleep(1.5)
        # Fallback: Wenn GelbeSeiten keine verifizierte E-Mail liefert, aber eine
        # (auch alte) Website existiert -> Impressum auslesen (echte Firmen-E-Mail)
        if not email and website:
            imp_email, imp_reason = extract_email_from_website_imprint(website)
            if imp_email:
                ok, v_reason = validate_email_for_company(imp_email, e["name"])
                if ok:
                    email, reason = imp_email, f"Impressum ({imp_reason}): {v_reason}"
                    details = {}  # keine GS-Details, aber echte E-Mail
        # Fallback 2: Maps-Kontaktblock (oft direkt zur Firma gehörig)
        if not email:
            maps_email, maps_reason = extract_email_from_maps(e["maps_url"])
            if maps_email:
                ok, v_reason = validate_email_for_company(maps_email, e["name"])
                if ok:
                    email, reason = maps_email, f"Maps ({maps_reason}): {v_reason}"
        if not email:
            print(f"  -> keine verifizierte E-Mail ({reason}) — verwerfen")
            continue

        print(f"  🔥 HOT LEAD: {e['name']} | {email} | verifiziert: {reason}")
        e["email"] = email
        e["email_verified"] = True
        e["email_verify_reason"] = reason
        # echte Firmendetails aus GelbeSeiten (falls vorhanden)
        for k in ("about", "products", "opening_hours", "owner"):
            if k in details and details[k]:
                e[k] = details[k]
        e["branch"] = branch
        e["region"] = region
        hot_leads.append(e)

    out = {"branch": branch, "region": region, "all_candidates": hot_candidates, "hot_leads": hot_leads}
    out_path = DATA_DIR / f"hot_leads_{branch}_{region}.json".replace(" ", "_")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"🔥 {len(hot_leads)} heiße Leads (kein/veraltete Website + E-Mail vorhanden)")
    for l in hot_leads:
        print(f"  {l['rating']}⭐ {l['name']} | {l['email']} | {l.get('phone','')}")
    print(f"\nGespeichert: {out_path}")


if __name__ == "__main__":
    main()
