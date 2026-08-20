#!/usr/bin/env python3
"""
Werkspree Microsite-Pipeline — Stufe 1: "Heißeste Leads" Scraper

Kombiniert Google Places API + Direct Scraper (requests + BeautifulSoup)
anstelle von Firecrawl — 0 Firecrawl-Credits nötig.

1. GOOGLE PLACES API: Sucht z.B. "restaurant berlin mitte", extrahiert Name +
   Bewertung + Adresse + Telefon + Website aus Place Details.
2. GELBESEITEN: Für Kandidaten OHNE eigene Website wird der Firmenname auf
   GelbeSeiten gesucht — dort haben auch reine "keine eigene Website"-Betriebe
   oft ein E-Mail-Kontaktfeld (mailto: Link auf der Profilseite).

Ausgabe: hot_leads.json — nur Leads, die BEIDE Kriterien erfüllen:
  - keine eigene Website (oder klar veraltete)
  - eine gefundene E-Mail-Adresse
"""
import json
import re
import sys
import time
import os
import requests
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

GENERIC_COMPANY_TOKENS = {
    "fahrschule", "fahrs", "kosmetik", "beauty", "salon", "barber", "nails",
    "malermeister", "maler", "tischlerei", "tischler", "schreinerei",
    "bäckerei", "baeckerei", "konditorei", "restaurant", "cafe", "café",
    "gastronomie", "imbiss", "reinigung", "gebaudereinigung",
    "gebäudereinigung", "physiotherapie", "physio", "zahnarzt", "zahn",
    "elektriker", "elektro", "kfz", "auto", "werkstatt", "metzgerei",
    "fleischerei", "optiker", "augenoptik", "florist", "blumen",
    "schlüsseldienst", "schluesseldienst", "heizung", "sanitär", "sanitaer",
    "gartenbau", "gmbh", "ug", "kg", "e.k.", "eg", "center", "studio",
    "service", "betrieb", "gesellschaft", "team", "schule", "institut",
    "friseur", "frisör", "frisoer", "hair", "lifestyle", "kosmetikstudio",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}

EMAIL_PATHS = ["/", "/kontakt", "/kontakt/", "/impressum", "/imprint", "/ueber-uns", "/about", "/contact"]


def load_env():
    """Load ~/.hermes/.env into os.environ."""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def is_valid_email(email):
    """Basic sanity check for email addresses."""
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
    if len(local) > 25 and not any(v in local for v in "aeiouAEIOU"):
        return False
    tld = domain.rsplit(".", 1)[-1]
    if len(tld) > 6:
        return False
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))


def search_places(query, api_key, max_results=10):
    """Google Places API Text Search."""
    if not api_key:
        return []
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key, "language": "de"}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
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
    """Google Place Details — Website + Telefon."""
    if not api_key or not place_id:
        return {}
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": api_key,
        "language": "de",
        "fields": "name,website,formatted_phone_number,formatted_address",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return {}
        data = r.json()
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


def find_email_on_website(website_url):
    """Find email on company website using Direct Scraper."""
    if not website_url or not website_url.startswith("http"):
        return "", ""
    base = website_url.rstrip("/")
    for path in EMAIL_PATHS:
        try:
            r = requests.get(base + path, headers=HEADERS, timeout=8, allow_redirects=True)
            if r.status_code != 200:
                continue
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            mailto = soup.find("a", href=re.compile(r"mailto:", re.I))
            if mailto:
                href = mailto.get("href", "")
                if href:
                    email = str(href).replace("mailto:", "").split("?")[0].strip()
                    if is_valid_email(email):
                        return email, "scraped"
            text = soup.get_text()
            emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
            for e in emails:
                if is_valid_email(e):
                    return e, "scraped"
        except Exception:
            continue
    return "", ""


def is_outdated_website(website):
    """Check if website is outdated/empty using Direct Scraper."""
    if not website:
        return True
    try:
        r = requests.get(website, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return True
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(strip=True).lower()
        if len(text) < 400:
            return True
        outdated_signals = ["diese website wird nicht mehr betreut", "under construction",
                            "baustelle", "coming soon", "domain is for sale", "parked domain"]
        return any(s in text for s in outdated_signals)
    except Exception:
        return True


def scrape_gelbeseiten_profile(gsbiz_url):
    """Scrape GelbeSeiten profile page using Direct Scraper."""
    if not gsbiz_url or "gelbeseiten.de" not in gsbiz_url:
        return {}
    try:
        r = requests.get(gsbiz_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        result = {}
        h1 = soup.find("h1")
        if h1:
            result["company_name"] = h1.get_text().strip()
        phone = soup.find("a", href=re.compile(r"tel:"))
        if phone:
            result["phone"] = phone.get_text().strip()
        address = soup.find("address") or soup.find(class_=re.compile(r"address", re.I))
        if address:
            result["address"] = address.get_text(separator=", ", strip=True)
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if href.startswith("http") and "gelbeseiten" not in href:
                result["website"] = href
                break
        # E-Mail
        mailto = soup.find("a", href=re.compile(r"mailto:", re.I))
        if mailto:
            href = mailto.get("href", "")
            if href:
                result["email"] = str(href).replace("mailto:", "").split("?")[0].strip()
        return result
    except Exception:
        return {}


def _norm_token(s):
    """Normalize for comparison: lowercase + Umlaut transliteration."""
    return (s.lower()
            .replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
            .replace("ß", "ss"))


def validate_email_for_company(email, company_name):
    """Check if email plausibly belongs to the company."""
    if not email or "@" not in email:
        return False, "keine E-Mail"
    local, domain = email.lower().split("@", 1)
    domain_base = domain.split(".")[0]
    comp_tokens = [t for t in re.findall(r"[a-z0-9äöüß]+", company_name.lower()) if len(t) >= 3]
    if not comp_tokens:
        return False, "Firmenname unparsebar"
    distinct = [t for t in comp_tokens if t not in GENERIC_COMPANY_TOKENS]
    if not distinct:
        return False, f"kein unterscheidender Firmen-Token in '{company_name}' (nur generisch)"
    distinct_norm = {_norm_token(t): t for t in distinct}
    domain_base_norm = _norm_token(domain_base)
    local_norm = _norm_token(local)
    for dn, orig in distinct_norm.items():
        if dn in domain_base_norm or dn in local_norm:
            return True, f"Match: '{orig}' in domain/local"
    free = ["gmail", "web.de", "gmx", "yahoo", "outlook", "hotmail", "icloud", "t-online", "mail.de", "freenet"]
    if any(f in domain for f in free):
        for dn, orig in distinct_norm.items():
            if dn in local_norm:
                return True, f"Freemailer mit Firmen-Match '{orig}' in local"
        return False, f"Freemailer '{domain}' ohne Firmen-Match im Local-Part '{local}' (falsche Zuordnung?)"
    return False, f"kein unterscheidender Firmen-Token in '{domain}' / '{local}'"


def find_email_and_details_on_gelbeseiten(company_name, region):
    """Search Gelbeseiten for company profile, extract details + verified email."""
    # Direct search on GelbeSeiten
    query = f"{company_name} {region}"
    search_url = f"https://www.gelbeseiten.de/suche/{quote(query)}"
    
    try:
        r = requests.get(search_url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return "", {}, "keine GelbeSeiten-Suche"
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Find profile links
        profile_links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/gsbiz/" in href:
                profile_links.append(href)
        
        if not profile_links:
            return "", {}, "keine Profilseite"
        
        # Scrape first profile
        profile_url = profile_links[0]
        if not profile_url.startswith("http"):
            profile_url = "https://www.gelbeseiten.de" + profile_url
        
        details = scrape_gelbeseiten_profile(profile_url)
        email = details.pop("email", "")
        
        if email:
            ok, reason = validate_email_for_company(email, company_name)
            if ok:
                return email, details, reason
        
        return "", details, "keine verifizierte E-Mail"
    except Exception as e:
        return "", {}, f"Fehler: {e}"


def main():
    load_env()
    
    if len(sys.argv) < 3:
        print("Usage: python3 hot_leads_pipeline.py '<branche>' '<region>' [limit] [max_checks]")
        sys.exit(1)
    branch, region = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    max_checks = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    query = f"{branch} {region}"
    
    print(f"=== Google Places API Suche: '{query}' ===")
    entries = search_places(query, api_key, max_results=limit)
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
        
        # Get details (website + phone)
        details = get_place_details(e["place_id"], api_key)
        website = details.get("website", "")
        phone = details.get("phone", "")
        e["phone"] = phone
        time.sleep(0.5)

        if website and not is_outdated_website(website):
            print(f"  -> hat aktuelle Website ({website}) — kein Kandidat")
            continue

        print(f"  -> keine/veraltete Website" + (f" ({website})" if website else ""))
        e["old_or_no_website"] = website or ""

        # Find email via Gelbeseiten
        email, details, reason = find_email_and_details_on_gelbeseiten(e["name"], region)
        time.sleep(0.5)
        
        # Fallback: Impressum
        if not email and website:
            imp_email, _ = find_email_on_website(website)
            if imp_email:
                ok, v_reason = validate_email_for_company(imp_email, e["name"])
                if ok:
                    email, reason = imp_email, f"Impressum: {v_reason}"
                    details = {}
        
        if not email:
            print(f"  -> keine verifizierte E-Mail ({reason}) — verwerfen")
            continue

        print(f"  🔥 HOT LEAD: {e['name']} | {email} | verifiziert: {reason}")
        e["email"] = email
        e["email_verified"] = True
        e["email_verify_reason"] = reason
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
