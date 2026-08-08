#!/usr/bin/env python3
"""
Werkspree Lead Pipeline (Cron-tauglich)
1. Scraped GelbeSeiten-Kategorieseite für eine Branche+Region
2. Extrahiert Firmennamen + Telefon + URL
3. Scraped Firmen-Websites /impressum + /kontakt für E-Mail-Adressen;
   falls nichts gefunden wird, Fallback auf einen MX-validierten
   info@domain-Guess (als "guessed" markiert, nicht "scraped")
3b. Zweiter Pass: bestehende Leads ohne E-Mail werden mit demselben
    Verfahren erneut versucht (kleines Budget pro Lauf)
4. Speichert alles als JSON
"""

import json, re, subprocess, sys, os
from datetime import datetime
from pathlib import Path

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
        # Look for external website URL in the GS page
        web_match = re.search(r'(https?://(?!www\.gelbeseiten\.de|ies\.v4all)[^\s)"\\]+)', details)
        website = web_match.group(1).rstrip('\"') if web_match else ""
        leads.append({
            "company_name": name,
            "phone": phone,
            "gelbeseiten_url": "",
            "website": website,
            "email": "",
            "email_source": "",
            "branch": "",
            "region": "",
            "scraped_at": datetime.now().isoformat(),
            "status": "new",
        })
    return leads


def get_email_from_imprint(website):
    """Scrape /impressum of a company website to find email."""
    if not website:
        return ""
    # Try /impressum first, then /kontakt
    for path in ["/impressum", "/Impressum", "/kontakt", "/Kontakt"]:
        url = website.rstrip("/") + path
        tmp = Path("/tmp/imprint_tmp.md")
        if firecrawl_scrape(url, tmp, timeout=30):
            content = tmp.read_text()
            emails = re.findall(r'[\w.-]+@[\w.-]+\.\w{2,}', content)
            # Filter out generic emails
            for e in emails:
                if not any(x in e.lower() for x in ['example', 'spam', 'meinungsmeister', 'webmaster@']):
                    return e
    return ""


def has_mx_record(domain):
    """Check via `dig` whether a domain has mail servers configured."""
    try:
        result = subprocess.run(
            ["dig", "+short", "MX", domain],
            capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def guess_domain_email(website):
    """Fallback: guess info@domain if the impressum/kontakt scrape found nothing.
    Only returns a guess if the domain actually has mail servers (MX record) —
    a guess without that check would just increase the bounce rate."""
    if not website:
        return ""
    m = re.search(r'https?://(?:www\.)?([^/]+)', website)
    if not m:
        return ""
    domain = m.group(1).lower()
    if not has_mx_record(domain):
        return ""
    return f"info@{domain}"


def find_email(website):
    """Try to find a real email first, fall back to a validated domain guess.
    Returns (email, source) where source is 'scraped' or 'guessed' — outreach
    should be able to tell a confirmed address from an inferred one."""
    email = get_email_from_imprint(website)
    if email:
        return email, "scraped"
    guessed = guess_domain_email(website)
    if guessed:
        return guessed, "guessed"
    return "", ""


def load_existing_leads():
    """Load all existing leads."""
    all_leads = []
    for f in DATA_DIR.glob("leads_*.json"):
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
        return
    
    # Step 2: Extract listings
    new_leads = extract_listings(gs_path)
    print(f"Found {len(new_leads)} listings on GelbeSeiten")
    
    # Set branch/region
    for l in new_leads:
        l["branch"] = branch
        l["region"] = region
    
    # Step 3: Get emails from first 5 company websites (credit limit)
    for i, lead in enumerate(new_leads[:5]):
        if lead["website"]:
            email, source = find_email(lead["website"])
            lead["email"] = email
            lead["email_source"] = source
            if email:
                print(f"  Found email ({source}): {lead['company_name']} -> {email}")
            else:
                print(f"  No email: {lead['company_name']}")

    # Step 3b: Second pass — retry existing leads that never got an email
    # (previously only the current day's first 5 new leads were ever checked;
    # everyone else stayed empty forever). Small budget so we don't blow the
    # Firecrawl credit limit on retries alone.
    existing = load_existing_leads()
    retry_candidates = [l for l in existing if l.get("website") and not l.get("email")]
    for lead in retry_candidates[:5]:
        email, source = find_email(lead["website"])
        if email:
            lead["email"] = email
            lead["email_source"] = source
            print(f"  Retry found email ({source}): {lead['company_name']} -> {email}")

    # Step 4: Save
    today = datetime.now().strftime("%Y%m%d")
    all_leads = deduplicate(existing + new_leads)
    
    out_path = DATA_DIR / f"leads_{today}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_leads, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(all_leads)} total leads to {out_path}")
    print(f"New today: {len(new_leads)}")
    print(f"With email: {sum(1 for l in all_leads if l.get('email'))}")


if __name__ == "__main__":
    main()
