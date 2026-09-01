#!/usr/bin/env python3
"""
Werkspree Lead Pipeline (Cron-tauglich)
1. Scraped GelbeSeiten-Kategorieseite für eine Branche+Region
2. Extrahiert Firmennamen + Telefon + URL
3. Scraped Firmen-Websites /impressum + /kontakt für E-Mail-Adressen;
   NUR echte, aus dem Impressum/Kontaktseite gescrapte Adressen werden
   übernommen ("scraped"). Geratene info@-Adressen sind deaktiviert.
3b. Zweiter Pass: bestehende Leads ohne E-Mail werden mit demselben
    Verfahren erneut versucht (kleines Budget pro Lauf)
4. Filter: Nur Leads mit verifizierter Firmen-Website werden behalten.
   Booking-Portale, Branchenverzeichnisse und Bild-URLs fliegen raus.
5. Speichert alles als JSON
"""

import json, re, sys, os
from datetime import datetime
from pathlib import Path

from scrapling.fetchers import Fetcher

from email_extraction import (
    best_email,
    EMAIL_SEARCH_PATHS,
    find_gelbeseiten_profile_url,
    find_real_website_on_profile_page,
    is_real_company_website,
    contact_links_from_homepage,
)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Daily rotation: one branch per day
BRANCHES = [
    ("Elektriker", "Berlin"),
    ("Dachdecker", "Berlin"),
    ("Sanitär", "Berlin"),
    ("Steuerberater", "Berlin"),
    ("Friseur", "Berlin"),
    ("Restaurant", "Berlin"),
    ("Immobilienmakler", "Berlin"),
    ("Anwalt", "Berlin"),
    ("Versicherungsmakler", "Berlin"),
    ("Handwerksbetriebe", "Potsdam"),
    ("Elektriker", "Potsdam"),
    ("Dachdecker", "Potsdam"),
    ("Steuerberater", "Potsdam"),
    ("Restaurant", "Potsdam"),
    ("Elektriker", "Brandenburg"),
    ("Dachdecker", "Brandenburg"),
]

# Domains that are never a company's real website (booking portals,
# directories, aggregators, social, image hosts). Defense in depth on top of
# is_real_company_website from email_extraction.
BLOCKED_DOMAINS = [
    "gelbeseiten.de", "golocal.de", "yelp", "tripadvisor", "booking.com",
    "opentable", "zenchef", "quandoo", "resmio", "tebi.co", "delivery.",
    "lieferando", "facebook.com", "instagram.com", "linkedin.com", "xing.com",
    "googleusercontent.com", "google.com/maps", "wixsite.com", "webnode",
    "jimdo.com", "onepage.me", "immonet", "immobilienscout",
    "ebay-kleinanzeigen", "cylex", "firmenabc", "wer-kennt-wen", "kennstdu",
]
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico")


def scrapling_scrape(url, timeout=30):
    """Scrape a URL with Scrapling Fetcher (anti-bot, adaptive).
    Returns the Adaptor page object or None on failure."""
    try:
        page = Fetcher.get(url, timeout=timeout)
        if page.status == 200:
            return page
        return None
    except Exception:
        return None


def scrapling_scrape_text(url, timeout=30):
    """Scrape a URL and return its text content, or '' on failure."""
    page = scrapling_scrape(url, timeout)
    if page:
        return page.get_all_text()
    return ""


def scrapling_scrape_html(url, timeout=30):
    """Scrape a URL and return its HTML content, or '' on failure."""
    page = scrapling_scrape(url, timeout)
    if page:
        return page.html_content or ""
    return ""


def is_acceptable_website(website):
    """True only for a real, company-owned website (no portals, directories,
    image URLs or media subdomains)."""
    if not is_real_company_website(website or ""):
        return False
    low = website.lower()
    if any(b in low for b in BLOCKED_DOMAINS):
        return False
    if low.rstrip("/").endswith(IMAGE_EXTS):
        return False
    if re.search(r"\.(?:media|img|images|bilder|cdn)[.-]", low):
        return False
    return True


def website_issue_label(website):
    """Classify why a website URL was rejected."""
    if not website:
        return "no_website"
    low = website.lower()
    if not is_real_company_website(website):
        return "not_company_website"
    if any(b in low for b in BLOCKED_DOMAINS):
        return "portal_or_directory"
    if low.rstrip("/").endswith(IMAGE_EXTS):
        return "image_url"
    return "other"


def init_lead_fields(lead):
    """Fill the standardized CRM fields on every lead."""
    now = datetime.now().isoformat()
    lead.setdefault("source", "gelbeseiten")
    lead.setdefault("last_checked", now)
    lead.setdefault("website_issue", "")
    lead.setdefault("verified_email", lead.get("email") if lead.get("email_source") == "scraped" else "")
    lead.setdefault("automation_need", "")
    lead.setdefault("next_step", "")
    lead.setdefault("response_status", "none")
    return lead


def extract_listings(page):
    """Extract business listings from a GelbeSeiten category page (Scrapling Adaptor).
    Uses CSS selectors instead of fragile regex on markdown.
    Returns a list of lead dicts."""
    if not page:
        return []
    leads = []
    # GelbeSeiten listings: each company name is an h2, profile link contains gsbiz
    for h2 in page.css("h2"):
        name = h2.get_all_text().strip()
        if len(name) < 3 or name in ['Gelbe Seiten Unternehmen finden', 'Suchen']:
            continue
        # Skip navigation/header h2s
        if name.lower() in ('branchenkatalog', 'service', 'für sie', 'für sie\nenergieberatung\nneu'):
            continue

        # Walk up to the parent listing container to extract phone + profile URL
        parent = h2.parent
        detail_text = parent.get_all_text(separator=" ", strip=True) if parent else ""

        # Phone: look for tel: links within the listing
        phone = ""
        for tel_link in (parent.css('a[href^="tel:"]') if parent else []):
            href = tel_link.attrib.get("href", "")
            if href:
                phone = href.replace("tel:", "").strip()
                break
        if not phone:
            m = re.search(r'(\d{3,4}\s+[\d\s]{6,})', detail_text)
            if m:
                phone = m.group(1).strip()

        # GelbeSeiten profile URL (gsbiz link)
        gelbeseiten_url = ""
        for a in (parent.css('a[href*="gelbeseiten.de/gsbiz/"]') if parent else []):
            gelbeseiten_url = a.attrib.get("href", "")
            if gelbeseiten_url:
                break

        # External website (rare on category page — JS-driven — but check anyway)
        website = ""
        if parent:
            for a in parent.css("a[href]"):
                href = a.attrib.get("href", "")
                if (href.startswith("http") and
                        "gelbeseiten.de" not in href and
                        "ies.v4all" not in href):
                    website = href.rstrip('/"\\')
                    break

        leads.append(init_lead_fields({
            "company_name": name,
            "phone": phone,
            "gelbeseiten_url": gelbeseiten_url,
            "website": website,
            "email": "",
            "email_source": "",
            "branch": "",
            "region": "",
            "scraped_at": datetime.now().isoformat(),
            "status": "new",
        }))
    return leads


def resolve_real_website(gelbeseiten_url):
    """Findet die echte Firmen-Website über die GelbeSeiten-Profilseite
    (der 'Webseite'-Button auf der Kategorieseite hat keinen statischen
    Link, auf der Profilseite des Unternehmens steht er aber normal).
    Nutzt Scrapling CSS-Extraktion statt Markdown-Regex."""
    if not gelbeseiten_url:
        return ""
    page = scrapling_scrape(gelbeseiten_url, timeout=30)
    if not page:
        return ""
    # Auf der Profilseite gibt es externe Links mit dem Text "Website" oder "Webseite"
    for a in page.css("a[href]"):
        href = a.attrib.get("href", "")
        text = a.get_all_text().strip()
        if (href.startswith("http") and
                "gelbeseiten.de" not in href and
                text.lower() in ("website", "webseite", "homepage")):
            return href.rstrip("/")
    # Fallback: erste externe http-Link, die nicht gelbeseiten/social ist
    for a in page.css("a[href]"):
        href = a.attrib.get("href", "")
        if (href.startswith("http") and
                "gelbeseiten.de" not in href and
                not any(s in href for s in ["instagram", "facebook", "twitter",
                                            "xing.com", "linkedin.com", "apple.com",
                                            "dastelefonbuch", "dasoertliche"])):
            return href.rstrip("/")
    return ""


def get_email_from_imprint(website):
    """Scrape a company website for an email address. Tries the homepage
    first (many small sites show it directly, e.g. as a mailto: link in the
    footer), then the classic legal-page paths. Stops at the first hit."""
    if not website:
        return ""
    base = website.rstrip("/")
    urls = [base + path for path in EMAIL_SEARCH_PATHS]
    homepage = scrapling_scrape(base, timeout=30)
    if homepage:
        urls.extend(contact_links_from_homepage(homepage.html_content or "", base))
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        text = scrapling_scrape_text(url, timeout=30)
        if text:
            email = best_email(text)
            if email:
                return email
    return ""


def find_email(website):
    """Scrape a real email from imprint/kontakt only. No guessed addresses —
    only confirmed addresses from the company's own legal/contact pages are
    accepted for outreach."""
    if not is_real_company_website(website):
        # Defense in depth: a gelbeseiten.de URL (e.g. stale data from before
        # the profile-page resolution existed) must never reach the guesser —
        # gelbeseiten.de itself has valid MX records, so it would "succeed"
        # with a useless info@gelbeseiten.de guess.
        return "", ""
    email = get_email_from_imprint(website)
    if email:
        return email, "scraped"
    return "", ""


def load_existing_leads():
    """Load all existing leads from daily snapshot files only
    (leads_YYYYMMDD.json — NOT leads_all_merged.json, leads_new_branches.json etc.)."""
    all_leads = []
    for f in sorted(DATA_DIR.glob("leads_*.json")):
        if not re.match(r"leads_\d{8}\.json$", f.name):
            continue
        with open(f) as fh:
            all_leads.extend(json.load(fh))
    return all_leads


def deduplicate(leads):
    seen = set()
    unique = []
    for l in leads:
        key = l["company_name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(l)
    return unique


def main():
    # Pick today's branch based on day of year
    day_of_year = datetime.now().timetuple().tm_yday
    branch, region = BRANCHES[day_of_year % len(BRANCHES)]

    print(f"Werkspree Lead Pipeline — {branch} in {region}")

    # Step 1: Scrape GelbeSeiten category page with Scrapling
    gs_url = f"https://www.gelbeseiten.de/branchen/{branch.lower()}/{region.lower()}"

    page = scrapling_scrape(gs_url, timeout=30)
    if not page:
        print(f"Failed to scrape {gs_url}")
        return 1

    # Step 2: Extract listings (Scrapling CSS-based)
    new_leads = extract_listings(page)
    print(f"Found {len(new_leads)} listings on GelbeSeiten")

    # Set branch/region
    for l in new_leads:
        l["branch"] = branch
        l["region"] = region

    # Step 3: Resolve the real company website, then find an email — for the
    # first 5 new leads (credit limit). The GelbeSeiten category page's
    # "Webseite" button has no static link, so `website` is almost always
    # still empty here; resolve it via the individual profile page first.
    for i, lead in enumerate(new_leads[:5]):
        if not is_acceptable_website(lead["website"]) and lead.get("gelbeseiten_url"):
            lead["website"] = resolve_real_website(lead["gelbeseiten_url"])
        if is_acceptable_website(lead["website"]):
            email, source = find_email(lead["website"])
            lead["email"] = email
            lead["email_source"] = source
            lead["verified_email"] = email if source == "scraped" else ""
            if email:
                print(f"  Found email ({source}): {lead['company_name']} -> {email}")
            else:
                print(f"  No email: {lead['company_name']}")
        else:
            lead["website_issue"] = website_issue_label(lead.get("website"))
            print(f"  No usable website: {lead['company_name']} ({lead['website_issue']})")

    # Step 3b: Second pass — retry existing leads that never got an email
    # (previously only the current day's first 5 new leads were ever checked;
    # everyone else stayed empty forever). Small budget so we don't spend
    # too long on retries alone. Also resolves a real website for old leads
    # that only ever had a gelbeseiten_url on file.
    existing = load_existing_leads()
    retry_candidates = [
        l for l in existing
        if not l.get("email") and (is_acceptable_website(l.get("website")) or l.get("gelbeseiten_url"))
    ]
    for lead in retry_candidates[:5]:
        if not is_acceptable_website(lead.get("website")) and lead.get("gelbeseiten_url"):
            lead["website"] = resolve_real_website(lead["gelbeseiten_url"])
        if not is_acceptable_website(lead.get("website")):
            continue
        email, source = find_email(lead["website"])
        if email:
            lead["email"] = email
            lead["email_source"] = source
            lead["verified_email"] = email if source == "scraped" else ""
            print(f"  Retry found email ({source}): {lead['company_name']} -> {email}")

    # Step 4: Normalize fields, keep only leads with a verified company
    # website (booking portals, directories and image URLs are excluded).
    all_leads = deduplicate(existing + new_leads)
    for l in all_leads:
        init_lead_fields(l)
        if l.get("email") and l.get("email_source") == "scraped":
            l["verified_email"] = l["email"]
    kept = [l for l in all_leads if is_acceptable_website(l.get("website"))]
    dropped = [l for l in all_leads if not is_acceptable_website(l.get("website"))]
    for l in dropped:
        l["website_issue"] = website_issue_label(l.get("website"))
    all_leads = kept

    today = datetime.now().strftime("%Y%m%d")
    out_path = DATA_DIR / f"leads_{today}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_leads, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_leads)} total leads (kept: verified website) to {out_path}")
    print(f"Dropped {len(dropped)} leads without verified website")
    print(f"New today: {len(new_leads)}")
    print(f"With email: {sum(1 for l in all_leads if l.get('email'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
