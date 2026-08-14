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


def find_email_on_gelbeseiten(company_name, region):
    """Sucht den Firmennamen auf GelbeSeiten und extrahiert eine mailto:
    E-Mail-Adresse von der Profilseite, falls vorhanden."""
    query = f'site:gelbeseiten.de/gsbiz/ "{company_name}" {region}'
    tmp = Path("/tmp/gs_search_tmp.md")
    result = subprocess.run(
        ["firecrawl", "search", query, "--limit", "3", "-o", str(tmp), "--json"],
        capture_output=True, text=True, timeout=45,
    )
    if result.returncode != 0 or not tmp.exists():
        return ""
    try:
        results = json.loads(tmp.read_text())
    except Exception:
        return ""
    # Firecrawl search --json shape: {success, data: {web: [{url, title, ...}]}}
    if isinstance(results, dict) and isinstance(results.get("data"), dict):
        urls = results["data"].get("web", [])
    elif isinstance(results, dict):
        urls = results.get("results", [])
    else:
        urls = results
    profile_url = None
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
    if ranked:
        ranked.sort(reverse=True)
        profile_url = ranked[0][1]
    if not profile_url:
        return ""
    tmp2 = Path("/tmp/gs_profile_check.json")
    if not firecrawl_scrape(profile_url, tmp2, wait_for=3000, formats="markdown,html", timeout=45):
        return ""
    try:
        data = json.loads(tmp2.read_text())
    except Exception:
        return ""
    html = data.get("html", "")
    m = re.search(r'mailto:([\w.\-+]+@[\w.\-]+\.\w{2,})', html, re.IGNORECASE)
    if not m:
        return ""
    email = m.group(1)
    if any(b in email.lower() for b in GENERIC_EMAIL_BLOCKLIST):
        return ""
    return email


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

        email = find_email_on_gelbeseiten(e["name"], region)
        time.sleep(1.5)
        if not email:
            print(f"  -> keine E-Mail über GelbeSeiten gefunden — verwerfen")
            continue

        print(f"  🔥 HOT LEAD: {e['name']} | {email}")
        e["email"] = email
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
