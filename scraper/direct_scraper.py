#!/usr/bin/env python3
"""
Werkspree Direct Website Scraper
Ersatz fuer firecrawl_scrape() — nutzt requests + BeautifulSoup.
"""
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}

EMAIL_PATHS = ["/", "/kontakt", "/kontakt/", "/impressum", "/imprint", "/ueber-uns", "/about", "/contact"]
EMAIL_SPAM = ["example.com", "sentry.io", "wixpress.com", "localhost", "yourdomain", "test@"]

def is_valid_email(email):
    if not email or not isinstance(email, str): return False
    email = email.strip()
    if email.count("@") != 1: return False
    local, domain = email.split("@")
    if not local or not domain or "." not in domain: return False
    if len(local) > 64 or len(domain) > 50: return False
    if len(local) > 25 and not any(v in local for v in "aeiouAEIOU"): return False
    tld = domain.rsplit(".", 1)[-1]
    if len(tld) > 6: return False
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))

def is_spam_email(email):
    low = email.lower()
    return any(s in low for s in EMAIL_SPAM)

def find_email_on_website(website_url):
    if not website_url or not website_url.startswith("http"): return "", ""
    base = website_url.rstrip("/")
    for path in EMAIL_PATHS:
        try:
            r = requests.get(base + path, headers=HEADERS, timeout=8, allow_redirects=True)
            if r.status_code != 200: continue
            soup = BeautifulSoup(r.text, "html.parser")
            mailto = soup.find("a", href=re.compile(r"mailto:", re.I))
            if mailto:
                href = mailto.get("href", "")
                if href:
                    email = str(href).replace("mailto:", "").split("?")[0].strip()
                    if is_valid_email(email) and not is_spam_email(email): return email, "scraped"
            text = soup.get_text()
            emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
            for e in emails:
                if is_valid_email(e) and not is_spam_email(e): return e, "scraped"
        except: continue
    return "", ""

def find_phone_on_website(website_url):
    if not website_url or not website_url.startswith("http"): return ""
    base = website_url.rstrip("/")
    for path in ["/", "/kontakt", "/kontakt/", "/impressum"]:
        try:
            r = requests.get(base + path, headers=HEADERS, timeout=8)
            if r.status_code != 200: continue
            soup = BeautifulSoup(r.text, "html.parser")
            tel = soup.find("a", href=re.compile(r"tel:", re.I))
            if tel:
                href = tel.get("href", "")
                if href:
                    phone = str(href).replace("tel:", "").strip()
                    if len(phone) >= 6: return phone
            text = soup.get_text()
            phones = re.search(r"(?:Tel|Telefon|Phone)[\.:]?\s*([\d\s\/\+\(\)\-]{8,})", text, re.I)
            if phones: return phones.group(1).strip()
        except: continue
    return ""

def scrape_gelbeseiten_profile(gsbiz_url):
    if not gsbiz_url or "gelbeseiten.de" not in gsbiz_url: return {}
    try:
        r = requests.get(gsbiz_url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return {}
        soup = BeautifulSoup(r.text, "html.parser")
        result = {}
        h1 = soup.find("h1")
        if h1: result["company_name"] = h1.get_text().strip()
        phone = soup.find("a", href=re.compile(r"tel:"))
        if phone: result["phone"] = phone.get_text().strip()
        address = soup.find("address") or soup.find(class_=re.compile(r"address", re.I))
        if address: result["address"] = address.get_text(separator=", ", strip=True)
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if href.startswith("http") and "gelbeseiten" not in href:
                result["website"] = href
                break
        return result
    except: return {}

def search_places(query, api_key, max_results=10):
    """Google Places API Text Search."""
    if not api_key: return []
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key, "language": "de"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200: return []
        data = r.json()
        if data.get("status") != "OK": return []
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
    except: return []

def get_place_details(place_id, api_key):
    """Google Place Details."""
    if not api_key or not place_id: return {}
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": place_id, "key": api_key, "language": "de",
              "fields": "name,website,formatted_phone_number,formatted_address"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200: return {}
        data = r.json()
        if data.get("status") != "OK": return {}
        result = data.get("result", {})
        return {"name": result.get("name", ""), "website": result.get("website", ""),
                "phone": result.get("formatted_phone_number", ""),
                "address": result.get("formatted_address", "")}
    except: return {}

if __name__ == "__main__":
    test_urls = ["https://www.bock-versorgungstechnik.de", "https://www.elektro-reibsch.de", "https://www.efeswe.de"]
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
