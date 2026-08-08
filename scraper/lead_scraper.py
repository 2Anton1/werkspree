#!/usr/bin/env python3
"""
Spreewerk Lead Scraper
Scraped Branchenverzeichnisse nach kleinen Unternehmen in Berlin/Brandenburg.
Speichert Leads als JSON für das CRM.
"""

import json
import csv
import os
import re
import time
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# Zielbranchen (hoher Automatisierungsbedarf)
TARGET_BRANCHES = [
    "Handwerksbetriebe",
    "Steuerberater",
    "Hautarzt",  # Praxis
    "Restaurant",
    "Café",
    "Friseur",
    "Dachdecker",
    "Elektriker",
    "Sanitär",
    "Anwalt",
    "Steuerberatung",
    "Versicherungsmakler",
    "Immobilienmakler",
    "Webdesign",
    "Werbeagentur",
]

REGIONS = [
    "Berlin",
    "Potsdam",
    "Brandenburg an der Havel",
    "Cottbus",
    "Frankfurt (Oder)",
]


def scrape_gelbeseiten(branch, region, max_results=30):
    """Scraped GelbeSeiten für eine Branche + Region."""
    from firecrawl import FirecrawlApp
    import os

    app = FirecrawlApp(api_key=os.environ.get("FIRECRAWL_API_KEY", ""))

    query = f"{branch} {region}"
    url = f"https://www.gelbeseiten.de/suche/{branch}/{region}"

    try:
        result = app.search(
            query,
            search_options={"limit": max_results, "scrapeOptions": {"formats": ["markdown"]}},
        )
        return parse_firecrawl_results(result, branch, region)
    except Exception as e:
        print(f"  ⚠ Firecrawl error for {branch} in {region}: {e}")
        return []


def parse_firecrawl_results(result, branch, region):
    """Extrahiert Firmenname, Adresse, E-Mail, Telefon aus Firecrawl-Ergebnissen."""
    leads = []

    if isinstance(result, dict) and "data" in result:
        items = result["data"]
    elif isinstance(result, list):
        items = result
    else:
        items = [result]

    for item in items:
        if not isinstance(item, dict):
            continue

        name = item.get("title", item.get("name", ""))
        url = item.get("url", item.get("link", ""))
        description = item.get("description", item.get("markdown", ""))[:500]

        # E-Mail extrahieren
        email = ""
        email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", description)
        if email_match:
            email = email_match.group()

        # Telefon extrahieren
        phone = ""
        phone_match = re.search(r"(?:Tel|Telefon|Phone)[:.\s]*([+\d][\d\s\-/()]{6,})", description)
        if phone_match:
            phone = phone_match.group(1).strip()

        if name and len(name) > 2:
            leads.append({
                "company_name": name,
                "website": url,
                "email": email,
                "phone": phone,
                "branch": branch,
                "region": region,
                "description": description[:200],
                "scraped_at": datetime.now().isoformat(),
                "status": "new",
                "potential_score": None,
                "last_contact": None,
                "notes": "",
            })

    return leads


def deduplicate(leads):
    """Entfernt Duplikate basierend auf Firmenname."""
    seen = set()
    unique = []
    for l in leads:
        key = l["company_name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(l)
    return unique


def save_leads(leads, filename=None):
    """Speichert Leads als JSON und CSV."""
    if filename is None:
        filename = f"leads_{datetime.now().strftime('%Y%m%d')}.json"

    json_path = OUTPUT_DIR / filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)

    csv_path = json_path.with_suffix(".csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if leads:
            writer = csv.DictWriter(f, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)

    print(f"  ✅ {len(leads)} Leads gespeichert: {json_path}")
    return json_path


def load_all_leads():
    """Lädt alle gespeicherten Leads."""
    all_leads = []
    for f in OUTPUT_DIR.glob("leads_*.json"):
        with open(f, "r", encoding="utf-8") as fh:
            all_leads.extend(json.load(fh))
    return deduplicate(all_leads)


def main():
    print("🚀 Spreewerk Lead Scraper")
    print(f"   Branchen: {len(TARGET_BRANCHES)}")
    print(f"   Regionen: {len(REGIONS)}")
    print()

    all_leads = []

    for branch in TARGET_BRANCHES:
        for region in REGIONS:
            print(f"📍 Scraping: {branch} in {region}...")
            leads = scrape_gelbeseiten(branch, region, max_results=20)
            all_leads.extend(leads)
            print(f"   → {len(leads)} Leads gefunden")
            time.sleep(1)  # Rate limiting

    unique = deduplicate(all_leads)
    save_leads(unique)
    print(f"\n📊 Gesamt: {len(unique)} eindeutige Leads")


if __name__ == "__main__":
    main()
