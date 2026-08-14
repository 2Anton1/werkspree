#!/usr/bin/env python3
"""
Werkspree Microsite-Pipeline — Stufe 1: Google Maps Hot-Lead-Scraper

Scraped eine Google-Maps-Suche (z.B. "restaurant berlin mitte") und
extrahiert für jeden Treffer: Name, Kategorie, Adresse, Bewertung,
Anzahl Bewertungen, Preisklasse (€/€€/€€€).

Diese Signale bestimmen "zahlungskräftig":
- Bewertung >= 4.3 UND Anzahl Bewertungen >= 30  (etabliert, gut besucht)
- ODER Preisklasse €€ oder höher (Restaurant investiert in Erlebnis)

Danach wird für jeden Kandidaten die Maps-Detailseite gescraped, um zu
prüfen, ob eine eigene Website existiert (Domain in den extrahierten Links,
die NICHT zu google/facebook/instagram/opentable/etc. gehört).
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

EXCLUDE_DOMAINS = [
    "google.com", "goo.gl", "maps.app.goo.gl", "facebook.com", "instagram.com",
    "opentable.com", "tripadvisor.com", "yelp.com", "lieferando.de",
    "ubereats.com", "wolt.com", "thefork.com", "quandoo.de", "resmio.com",
    "gelbeseiten.de", "wogibtswas.de", "11880.com", "goldenpages",
]


def firecrawl_scrape_json(url, out_path, wait_for=4000, timeout=60):
    result = subprocess.run(
        ["firecrawl", "scrape", url, "--wait-for", str(wait_for),
         "-f", "markdown,links", "-o", str(out_path)],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.returncode == 0


def parse_search_results(markdown):
    """Parst die Google-Maps-Suchergebnisliste (Markdown) in Einträge.

    Format je Eintrag (nach 'Places'):
      [Name](https://www.google.com/maps/place/...)
      Name
      RATING(REVIEWS) · PRICE · CATEGORY
      Address...
    """
    entries = []
    # Split at each maps/place link that has visible text after it
    blocks = re.split(r'\n(?=\[)', markdown)
    for block in blocks:
        m_link = re.search(r'\[([^\]]+)\]\((https://www\.google\.com/maps/place/[^)]+)\)', block)
        if not m_link:
            continue
        name = m_link.group(1).strip()
        place_url = m_link.group(2)
        m_stats = re.search(
            r'(\d\.\d)\(([\d.,]+[Kk]?)\)\s*·\s*(€+)?\s*·?\s*([^\n]+)',
            block,
        )
        rating, reviews, price, category = None, None, "", ""
        if m_stats:
            rating = float(m_stats.group(1))
            rev_str = m_stats.group(2).replace(",", "").replace(".", "")
            if "k" in m_stats.group(2).lower():
                reviews = int(float(m_stats.group(2).lower().replace("k", "")) * 1000)
            else:
                reviews = int(rev_str) if rev_str.isdigit() else 0
            price = m_stats.group(3) or ""
            category = m_stats.group(4).strip()
        entries.append({
            "name": name,
            "maps_url": place_url,
            "rating": rating,
            "reviews": reviews,
            "price": price,
            "category": category,
        })
    # Dedup by name
    seen = set()
    unique = []
    for e in entries:
        if e["name"] not in seen and len(e["name"]) > 2:
            seen.add(e["name"])
            unique.append(e)
    return unique


def is_payment_capable(entry):
    rating = entry.get("rating") or 0
    reviews = entry.get("reviews") or 0
    price = entry.get("price") or ""
    if rating >= 4.3 and reviews >= 30:
        return True
    if len(price) >= 2:  # €€ or €€€
        return True
    return False


def get_website_from_place(maps_url, tmp_path):
    """Scraped die Maps-Detailseite und sucht nach einer externen Website."""
    if not firecrawl_scrape_json(maps_url, tmp_path, wait_for=3500, timeout=45):
        return None
    try:
        data = json.loads(tmp_path.read_text())
    except Exception:
        return None
    links = data.get("links", [])
    for link in links:
        low = link.lower()
        if low.startswith("tel:") or low.startswith("mailto:"):
            continue
        if any(dom in low for dom in EXCLUDE_DOMAINS):
            continue
        if low.startswith("http") and "google.com" not in low:
            return link.rstrip("/")
    return None


def search_maps(query, limit=20):
    url = f"https://www.google.com/maps/search/{quote(query)}"
    tmp = Path("/tmp/maps_search_tmp.md")
    if not firecrawl_scrape_json(url, tmp, wait_for=4500, timeout=60):
        print(f"Scrape fehlgeschlagen: {url}")
        return []
    try:
        data = json.loads(tmp.read_text())
        markdown = data.get("markdown", "")
    except Exception:
        markdown = tmp.read_text()
    entries = parse_search_results(markdown)
    return entries[:limit]


def enrich_with_website(entries, max_checks=15, sleep_s=2):
    """Prüft für die zahlungskräftigsten Kandidaten, ob eine eigene Website existiert."""
    candidates = [e for e in entries if is_payment_capable(e)]
    print(f"{len(candidates)} von {len(entries)} Treffern sind zahlungskräftig-verdächtig")
    checked = 0
    for e in candidates:
        if checked >= max_checks:
            e["website_checked"] = False
            continue
        tmp = Path(f"/tmp/place_detail_{checked}.json")
        website = get_website_from_place(e["maps_url"], tmp)
        e["website"] = website or ""
        e["website_checked"] = True
        print(f"  {e['name'][:35]:35s} | {'Website: ' + website if website else 'KEINE Website'}")
        checked += 1
        time.sleep(sleep_s)
    return candidates


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 maps_scraper.py '<branche>' '<region>' [limit] [max_website_checks]")
        sys.exit(1)
    branch, region = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    max_checks = int(sys.argv[4]) if len(sys.argv) > 4 else 15

    query = f"{branch} {region}"
    print(f"Google Maps Suche: '{query}'")
    entries = search_maps(query, limit=limit)
    print(f"{len(entries)} Ergebnisse geparst")

    candidates = enrich_with_website(entries, max_checks=max_checks)

    no_website = [c for c in candidates if c.get("website_checked") and not c.get("website")]
    print(f"\n🔥 Zahlungskräftig OHNE eigene Website: {len(no_website)}")
    for c in no_website:
        print(f"  {c['rating']}⭐ ({c['reviews']}) {c['price']} | {c['name']} | {c['category']}")

    out = {
        "branch": branch,
        "region": region,
        "all_entries": entries,
        "candidates": candidates,
        "no_website": no_website,
    }
    out_path = DATA_DIR / f"maps_{branch}_{region}.json".replace(" ", "_")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nGespeichert: {out_path}")


if __name__ == "__main__":
    main()
