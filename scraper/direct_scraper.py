#!/usr/bin/env python3
"""
Werkspree Direct Website Scraper — jetzt mit Scrapling.
Ersetzt requests+BeautifulSoup durch Scrapling's Fetcher (adaptiv, anti-bot).
Wird von pipeline.py als Drop-in importiert.
"""
import re
from scrapling.fetchers import Fetcher

EMAIL_PATHS = ["", "/kontakt", "/kontakt/", "/impressum", "/imprint", "/ueber-uns", "/about", "/contact"]
EMAIL_SPAM = ["example.com", "sentry.io", "wixpress.com", "localhost", "yourdomain", "test@"]

# Regex für normale E-Mail-Extraktion aus Text
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


def _is_valid_email(email):
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    if email.count("@") != 1:
        return False
    local, domain = email.split("@")
    if not local or not domain or "." not in domain:
        return False
    if len(local) > 64 or len(domain) > 50:
        return False
    tld = domain.rsplit(".", 1)[-1]
    if len(tld) > 6:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))


def _is_spam_email(email):
    low = email.lower()
    return any(s in low for s in EMAIL_SPAM)


def find_email_on_website(website_url):
    """Scrape eine Firmen-Website nach E-Mail-Adressen.
    Nutzt Scrapling Fetcher (anti-bot, adaptive Parsing).
    Gibt (email, source) zurück — source ist 'scraped' oder ''."""
    if not website_url or not website_url.startswith("http"):
        return "", ""
    base = website_url.rstrip("/")
    for path in EMAIL_PATHS:
        url = base + path
        try:
            page = Fetcher.get(url, timeout=10)
            if page.status != 200:
                continue
            # 1. mailto:-Links (höchste Zuverlässigkeit)
            for a in page.css('a[href^="mailto:"]'):
                href = a.attrib.get("href", "")
                if href:
                    email = href.replace("mailto:", "").split("?")[0].strip()
                    if _is_valid_email(email) and not _is_spam_email(email):
                        return email, "scraped"
            # 2. E-Mails im Text
            text = page.get_all_text()
            for m in _EMAIL_RE.findall(text):
                if _is_valid_email(m) and not _is_spam_email(m):
                    return m, "scraped"
        except Exception:
            continue
    return "", ""


def find_phone_on_website(website_url):
    """Scrape eine Firmen-Website nach Telefonnummern."""
    if not website_url or not website_url.startswith("http"):
        return ""
    base = website_url.rstrip("/")
    for path in ["", "/kontakt", "/kontakt/", "/impressum"]:
        try:
            page = Fetcher.get(base + path, timeout=10)
            if page.status != 200:
                continue
            # tel:-Links
            for a in page.css('a[href^="tel:"]'):
                href = a.attrib.get("href", "")
                if href:
                    phone = href.replace("tel:", "").strip()
                    if len(phone) >= 6:
                        return phone
            # Text-basierte Telefonnummer
            text = page.get_all_text()
            m = re.search(r'(?:Tel|Telefon|Phone)[\.:]?\s*([\d\s\/\+\(\)\-]{8,})', text, re.I)
            if m:
                return m.group(1).strip()
        except Exception:
            continue
    return ""


def scrape_gelbeseiten_profile(gsbiz_url):
    """Scrape eine GelbeSeiten-Profilseite und extrahiere Name, Telefon, Adresse, Website.
    Gibt ein Dict mit company_name, phone, address, website zurück."""
    if not gsbiz_url or "gelbeseiten.de" not in gsbiz_url:
        return {}
    try:
        page = Fetcher.get(gsbiz_url, timeout=15)
        if page.status != 200:
            return {}
        result = {}
        # Name (h1)
        h1 = page.css("h1")
        if h1:
            result["company_name"] = h1[0].get_all_text().strip()
        # Telefon (tel:-Link)
        for a in page.css('a[href^="tel:"]'):
            result["phone"] = a.get_all_text().strip()
            break
        # Adresse
        addr = page.css("address") or page.css('[class*="address"]')
        if addr:
            result["address"] = addr[0].get_all_text(separator=", ", strip=True)
        # Echte externe Website (nicht gelbeseiten.de)
        for a in page.css("a[href]"):
            href = a.attrib.get("href", "")
            if href.startswith("http") and "gelbeseiten" not in href:
                result["website"] = href
                break
        return result
    except Exception:
        return {}


def search_places(query, api_key, max_results=10):
    """Google Places API Text Search (unverändert — kein Scrapling)."""
    if not api_key:
        return []
    import json
    import urllib.request
    import urllib.parse
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = urllib.parse.urlencode({"query": query, "key": api_key, "language": "de"})
    try:
        req = urllib.request.Request(f"{url}?{params}")
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        if data.get("status") != "OK":
            return []
        results = []
        for place in data.get("results", [])[:max_results]:
            results.append({
                "name": place.get("name", ""),
                "address": place.get("formatted_address", ""),
                "rating": place.get("rating", 0),
                "place_id": place.get("place_id", ""),
                "types": place.get("types", []),
            })
        return results
    except Exception:
        return []


def get_place_details(place_id, api_key):
    """Google Place Details (unverändert — kein Scrapling)."""
    if not api_key or not place_id:
        return {}
    import json
    import urllib.request
    import urllib.parse
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = urllib.parse.urlencode({
        "place_id": place_id, "key": api_key, "language": "de",
        "fields": "name,website,formatted_phone_number,formatted_address",
    })
    try:
        req = urllib.request.Request(f"{url}?{params}")
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        if data.get("status") != "OK":
            return {}
        result = data.get("result", {})
        return {
            "name": result.get("name", ""),
            "website": result.get("website", ""),
            "phone": result.get("formatted_phone_number", ""),
            "address": result.get("formatted_address", ""),
        }
    except Exception:
        return {}


if __name__ == "__main__":
    test_urls = [
        "https://www.bock-versorgungstechnik.de",
        "https://www.elektro-reibsch.de",
        "https://www.efeswe.de",
    ]
    for url in test_urls:
        email, source = find_email_on_website(url)
        phone = find_phone_on_website(url)
        print(f"{url}: email={email}, phone={phone}")

    print("\n--- GelbeSeiten-Profile Test ---")
    test_gs = [
        "https://www.gelbeseiten.de/gsbiz/c2d5e0d9-315a-4383-a719-be4c4d344fb5",
        "https://www.gelbeseiten.de/gsbiz/df56e503-2c57-4fc9-b9cb-1f90c957a2de",
    ]
    for url in test_gs:
        result = scrape_gelbeseiten_profile(url)
        print(f"{url}: {result}")

    # Test Places API
    from pathlib import Path
    env_path = Path.home() / ".hermes" / ".env"
    api_key = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip().startswith("GOOGLE_PLACES_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if api_key:
        print("\n--- Google Places API Test ---")
        results = search_places("Friseur Berlin", api_key, max_results=5)
        print(f"Gefunden: {len(results)}")
        for r in results[:3]:
            print(f"  {r.get('name', '')[:40]:40} | {r.get('address', '')[:50]}")
            print(f"    rating={r.get('rating', '?')}, place_id={r.get('place_id', '')[:30]}...")

        if results:
            details = get_place_details(results[0]["place_id"], api_key)
            print(f"\nDetails fuer {results[0]['name']}:")
            print(f"  Website: {details.get('website', 'keine')}")
            print(f"  Telefon: {details.get('phone', 'kein')}")
    else:
        print("\nGOOGLE_PLACES_API_KEY nicht gefunden")
