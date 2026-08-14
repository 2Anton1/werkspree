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

import json, re, subprocess, sys, os
from datetime import datetime
from pathlib import Path

# Ensure firecrawl is in PATH (cron doesn't have ~/.local/bin)
FIRECRAWL_PATH = "/Users/anton/.local/bin/firecrawl"
os.environ["PATH"] = os.environ.get("PATH", "") + ":/Users/anton/.local/bin"

from email_extraction import (
    best_email,
    EMAIL_SEARCH_PATHS,
    find_gelbeseiten_profile_url,
    find_real_website_on_profile_page,
    is_real_company_website,
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


def firecrawl_scrape(url, output_path, timeout=60):
    """Scrape a URL with firecrawl CLI."""
    result = subprocess.run(
        ["firecrawl", "scrape", url, "-o", str(output_path)],
        capture_output=True, text=True, timeout=timeout
    )
    return result.returncode == 0


def firecrawl_search(query, output_path, limit=10):
    """Search with firecrawl CLI."""
    result = subprocess.run(
        ["firecrawl", "search", query, "--limit", str(limit), "-o", str(output_path), "--json"],
        capture_output=True, text=True, timeout=60
    )
    return result.returncode == 0


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


def extract_listings(gs_path):
    """Extract business listings from GelbeSeiten markdown."""
    content = Path(gs_path).read_text()
    listings = re.findall(
        r'\*\*([^*]+)\*\*[\\]+.*?\n(.*?)(?=\*\*[^*]+\*\*[\\]|$)',
        content, re.DOTALL
    )
    leads = []
    for name, details in listings:
        name = name.strip().rstrip('\\').strip()
        if len(name) < 3 or name in ['Gelbe Seiten Unternehmen finden', 'Suchen']:
            continue
        phone = ""
        phone_match = re.search(r'(\d{3,4}\s+[\d\s]{6,})', details)
        if phone_match:
            phone = phone_match.group(1).strip()
        # Look for external website URL in the GS page (any gelbeseiten.de
        # subdomain is excluded, not just "www." -- the profile page itself
        # is not the company's real website). This almost never finds
        # anything on the category page -- the per-listing "Webseite" button
        # there is JS-driven with no static href. It's kept as a free/cheap
        # first attempt; the real resolution path is the GelbeSeiten profile
        # page (see gelbeseiten_url + resolve_real_website below).
        web_match = re.search(
            r'(https?://(?!(?:[\w-]+\.)?gelbeseiten\.de|ies\.v4all)[^\s)"\\]+)',
            details, re.IGNORECASE
        )
        website = web_match.group(1).rstrip('\\"') if web_match else ""
        leads.append(init_lead_fields({
            "company_name": name,
            "phone": phone,
            "gelbeseiten_url": find_gelbeseiten_profile_url(details),
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
    Link, auf der Profilseite des Unternehmens steht er aber normal)."""
    if not gelbeseiten_url:
        return ""
    tmp = Path("/tmp/gsbiz_tmp.md")
    if firecrawl_scrape(gelbeseiten_url, tmp, timeout=30):
        return find_real_website_on_profile_page(tmp.read_text())
    return ""


def get_email_from_imprint(website):
    """Scrape a company website for an email address. Tries the homepage
    first (many small sites show it directly, e.g. as a mailto: link in the
    footer), then the classic legal-page paths. Stops at the first hit."""
    if not website:
        return ""
    base = website.rstrip("/")
    for path in EMAIL_SEARCH_PATHS:
        url = base + path
        tmp = Path("/tmp/imprint_tmp.md")
        if firecrawl_scrape(url, tmp, timeout=30):
            content = tmp.read_text()
            email = best_email(content)
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

    # Step 1: Scrape GelbeSeiten category page
    gs_url = f"https://www.gelbeseiten.de/branchen/{branch.lower()}/{region.lower()}"
    gs_path = Path(f"/tmp/gs_{branch}_{region}.md")

    if not firecrawl_scrape(gs_url, gs_path):
        print(f"Failed to scrape {gs_url}")
        return 1

    # Step 2: Extract listings
    new_leads = extract_listings(gs_path)
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
    # everyone else stayed empty forever). Small budget so we don't blow the
    # Firecrawl credit limit on retries alone. Also resolves a real website
    # for old leads that only ever had a gelbeseiten_url on file.
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
