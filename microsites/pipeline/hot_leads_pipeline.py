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
from pathlib import Path
from urllib.parse import quote

from scrapling.fetchers import Fetcher

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
    """Google Place Details — Website + Telefon."""
    if not api_key or not place_id:
        return {}
    import urllib.request
    import urllib.parse
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = urllib.parse.urlencode({
        "place_id": place_id,
        "key": api_key,
        "language": "de",
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


def find_email_on_website(website_url):
    """Find email on company website using Scrapling Fetcher."""
    if not website_url or not website_url.startswith("http"):
        return "", ""
    base = website_url.rstrip("/")
    for path in EMAIL_PATHS:
        try:
            page = Fetcher.get(base + path, timeout=10)
            if page.status != 200:
                continue
            # mailto links
            for a in page.css('a[href^="mailto:"]'):
                href = a.attrib.get("href", "")
                if href:
                    email = href.replace("mailto:", "").split("?")[0].strip()
                    if is_valid_email(email):
                        return email, "scraped"
            # emails in text
            text = page.get_all_text()
            emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
            for e in emails:
                if is_valid_email(e):
                    return e, "scraped"
        except Exception:
            continue
    return "", ""


def is_outdated_website(website):
    """Check if website is outdated/empty using Scrapling Fetcher."""
    if not website:
        return True
    try:
        page = Fetcher.get(website, timeout=10)
        if page.status != 200:
            return True
        text = page.get_all_text().lower()
        if len(text) < 400:
            return True
        outdated_signals = ["diese website wird nicht mehr betreut", "under construction",
                            "baustelle", "coming soon", "domain is for sale", "parked domain"]
        return any(s in text for s in outdated_signals)
    except Exception:
        return True


def is_low_quality_website(website):
    """
    Check if website is of low quality (good enough for Microsite replacement).

    Criteria:
    - No SSL (HTTP only)
    - Very short content (< 800 words)
    - No contact page / imprint
    - Free hosting platforms (Wix Free, Jimdo, WordPress.com, Weebly, etc.)
    - Only Facebook/social media as "website"

    Returns: True if website is low quality (Microsite makes sense)
    """
    if not website:
        return True

    # HTTP only = low quality
    if website.startswith("http://"):
        return True

    # Check for free hosting platforms
    low_quality_domains = [
        "wixsite.com", "jimdo.com", "weebly.com", "wordpress.com", "mozello.com",
        "site123.com", "webnode.at", "webnode.com", "webnode.de",
        "one.com", "oneandone.com", " ionos.com", "ionos.at", "1und1.de",
        "1und1.com", "home.pl", "home.eu", "fortishosting.com",
    ]
    domain = website.split("//")[-1].split("/")[0].lower()
    if any(lqd in domain for lqd in low_quality_domains):
        return True

    try:
        page = Fetcher.get(website, timeout=10)
        if page.status != 200:
            return True
        text = page.get_all_text().lower()

        # Very short content
        words = text.split()
        if len(words) < 150:
            return True

        # No contact/imprint links
        links = [a.attrib.get("href", "").lower() for a in page.css("a[href]")]
        has_contact = any(p in " ".join(links) for p in ["/kontakt", "/impressum", "/contact", "/imprint", "/about", "/ueber"])
        has_phone = any("tel:" in l for l in links)

        if not has_contact and not has_phone:
            return True

        return False
    except Exception:
        return True


def check_website_quality(website):
    """
    Comprehensive website quality check.
    Returns: (quality_score, quality_label, needs_microsite)

    quality_score: 0-10
    quality_label: "high", "medium", "low", "none"
    needs_microsite: True if Microsite makes sense
    """
    if not website:
        return 0, "none", True

    score = 10
    issues = []

    # HTTP = -3
    if website.startswith("http://"):
        score -= 3
        issues.append("no-ssl")

    # Free hosting = -4
    domain = website.split("//")[-1].split("/")[0].lower()
    free_hosting = ["wixsite.com", "jimdo.com", "weebly.com", "wordpress.com", "webnode"]
    if any(fh in domain for fh in free_hosting):
        score -= 4
        issues.append("free-hosting")

    try:
        page = Fetcher.get(website, timeout=10)
        if page.status != 200:
            return 0, "none", True

        text = page.get_all_text().lower()
        words = text.split()

        # Short content
        if len(words) < 150:
            score -= 3
            issues.append("short-content")
        elif len(words) < 500:
            score -= 1
            issues.append("medium-content")

        # No contact
        links = [a.attrib.get("href", "").lower() for a in page.css("a[href]")]
        has_contact = any(p in " ".join(links) for p in ["/kontakt", "/impressum", "/contact", "/imprint"])
        has_phone = any("tel:" in l for l in links)

        if not has_contact:
            score -= 2
            issues.append("no-contact")
        if not has_phone:
            score -= 1
            issues.append("no-phone")

        # No images
        if len(page.css("img")) < 2:
            score -= 1
            issues.append("no-images")

    except Exception:
        return 0, "none", True

    score = max(0, score)

    if score >= 7:
        label = "high"
    elif score >= 4:
        label = "medium"
    else:
        label = "low"

    needs_microsite = score < 6

    return score, label, needs_microsite


def scrape_gelbeseiten_profile(gsbiz_url):
    """Scrape GelbeSeiten profile page using Scrapling Fetcher."""
    if not gsbiz_url or "gelbeseiten.de" not in gsbiz_url:
        return {}
    try:
        page = Fetcher.get(gsbiz_url, timeout=15)
        if page.status != 200:
            return {}
        result = {}
        h1 = page.css("h1")
        if h1:
            result["company_name"] = h1[0].get_all_text().strip()
        for a in page.css('a[href^="tel:"]'):
            result["phone"] = a.get_all_text().strip()
            break
        addr = page.css("address") or page.css('[class*="address"]')
        if addr:
            result["address"] = addr[0].get_all_text(separator=", ", strip=True)
        for a in page.css("a[href]"):
            href = a.attrib.get("href", "")
            if href.startswith("http") and "gelbeseiten" not in href:
                result["website"] = href
                break
        # E-Mail
        for a in page.css('a[href^="mailto:"]'):
            href = a.attrib.get("href", "")
            if href:
                result["email"] = href.replace("mailto:", "").split("?")[0].strip()
                break
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
    """Search Gelbeseiten for company profile, extract details + verified email.
    Uses Scrapling Fetcher instead of requests+BS4."""
    query = f"{company_name} {region}"
    search_url = f"https://www.gelbeseiten.de/suche/{quote(query)}"

    try:
        page = Fetcher.get(search_url, timeout=15)
        if page.status != 200:
            return "", {}, "keine GelbeSeiten-Suche"

        # Find profile links
        profile_links = []
        for a in page.css("a[href]"):
            href = a.attrib.get("href", "")
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
    website_stats = {"high": 0, "medium": 0, "low": 0, "none": 0}
    
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

        if website:
            # Check website quality
            score, quality, needs_microsite = check_website_quality(website)
            website_stats[quality] += 1
            print(f"  -> Website: {website}")
            print(f"     Qualität: {quality} ({score}/10), Microsite sinnvoll: {needs_microsite}")
            
            if not needs_microsite:
                print(f"     -> hochwertige Website — kein Kandidat")
                continue
            
            e["website_quality"] = quality
            e["website_quality_score"] = score
        else:
            website_stats["none"] += 1
            print(f"  -> keine Website")
            e["website_quality"] = "none"
            e["website_quality_score"] = 0

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
        
        # Fallback 2: Gelbeseiten-Suche verbessern
        if not email:
            # Suche auf GelbeSeiten nach Profil
            gs_email, gs_details, gs_reason = find_email_and_details_on_gelbeseiten(e["name"], region)
            if gs_email:
                email, details, reason = gs_email, gs_details, gs_reason
        
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
    print(f"🔥 {len(hot_leads)} heiße Leads (Website-Qualität niedrig + E-Mail vorhanden)")
    for l in hot_leads:
        print(f"  {l.get('rating', '?')}⭐ {l.get('name', '')} | {l.get('email', '')} | {l.get('phone', '')}")
    print(f"\nGespeichert: {out_path}")


if __name__ == "__main__":
    main()
