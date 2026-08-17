#!/usr/bin/env python3
"""
Werkspree Lead Warmth Scorer
Scores leads 1-10 based on automation-readiness signals:

WARM SIGNALS:
- Website exists and is functional (not just a GelbeSeiten listing)
- No online booking/appointment system (automation opportunity)
- No chatbot/AI features (they don't have automation yet)
- Manual contact form (they process things manually)
- Job postings mentioning "Buchhaltung", "Rechnung", "Büro" (hiring for automatable tasks)
- Small team (1-10 employees, mentioned in imprint)
- Outdated website (old tech = no automation)
- Multiple locations or high customer volume indicators
- Instagram/Facebook but no WhatsApp Business
- PDF menus, price lists (could be automated)

COLD SIGNALS:
- Already has online booking system
- Already has chatbot
- Large enterprise (50+ employees)
- No website at all
- Already a tech/digital company
"""

import json
import re
import subprocess
import os
import time
from pathlib import Path

# Ensure firecrawl is in PATH (cron doesn't have ~/.local/bin)
os.environ["PATH"] = os.environ.get("PATH", "") + ":/Users/anton/.local/bin"

DATA_DIR = Path(__file__).parent / "data"
SCORED_FILE = DATA_DIR / "scored_leads.json"
CACHE_DIR = Path(__file__).parent / ".." / ".firecrawl" / "warmth"

AUTOMATION_NEEDS = {
    "Steuerberater": "Rechnungs- und Belegverarbeitung",
    "Anwalt": "Mandats- und Fristenmanagement",
    "Immobilienmakler": "Lead-Nachfassung",
    "Restaurant": "Reservierungen und Bestellungen",
    "Friseur": "Terminbuchung",
    "Elektriker": "Termin- und Angebotsanfragen",
    "Dachdecker": "Termin- und Angebotsanfragen",
    "Sanitär": "Termin- und Angebotsanfragen",
    "Handwerksbetriebe": "Termin- und Angebotsanfragen",
    "Versicherungsmakler": "Anfrage-Nachfassung",
}


def scrape_website(url, timeout=30):
    """Scrape a website and return the content."""
    if not url or "gelbeseiten.de" in url:
        return None

    cache_key = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50]
    cache_path = CACHE_DIR / f"{cache_key}.md"

    if cache_path.exists():
        return cache_path.read_text()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["firecrawl", "scrape", url, "-o", str(cache_path)],
            capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"  (Scrape-Timeout {timeout}s: {url[:60]})")
        return None
    except Exception as e:
        print(f"  (Scrape-Fehler: {e})")
        return None

    if result.returncode == 0 and cache_path.exists():
        return cache_path.read_text()
    return None


def score_lead(lead, website_content=None):
    """Score a lead 1-10 for automation readiness."""
    score = 0
    signals = []

    # 1. Has own website (not just GelbeSeiten) = +2
    website = lead.get("website", "")
    if website and "gelbeseiten.de" not in website:
        score += 2
        signals.append("has_own_website")
    else:
        signals.append("no_own_website")

    # 2. Has email = +1 (directly contactable)
    if lead.get("verified_email") or lead.get("email"):
        score += 1
        signals.append("has_email")

    # 3. Analyze website content for warmth signals
    if website_content:
        content_lower = website_content.lower()

        # Has contact form but no online booking = warm
        if any(w in content_lower for w in ["kontaktformular", "kontakt form", "contact form"]):
            if not any(w in content_lower for w in ["online termin", "online buchen", "booking", "termin buchen", "reservierung online"]):
                score += 2
                signals.append("manual_contact_form")
            else:
                score -= 1
                signals.append("has_online_booking")

        # Has online booking = already automated (cold)
        if any(w in content_lower for w in ["online termin", "online buchen", "booking system", "termin buchen", "reservierung online", "tablecheck", "opentable"]):
            score -= 2
            signals.append("already_has_online_booking")

        # Has chatbot = already has some automation (cold for chatbot, warm for other)
        if any(w in content_lower for w in ["chatbot", "chat-bot", "ki-assistent", "künstliche intelligenz"]):
            score -= 1
            signals.append("already_has_chatbot")
        else:
            score += 1
            signals.append("no_chatbot")

        # Mentions manual processes = warm
        if any(w in content_lower for w in ["rechnung", "buchhaltung", "buchhalter", "faktura", "kontoauszug"]):
            score += 1
            signals.append("mentions_accounting")

        # Has WhatsApp but maybe not Business = warm
        if any(w in content_lower for w in ["whatsapp"]):
            if "whatsapp business" not in content_lower:
                score += 1
                signals.append("has_whatsapp_not_business")

        # No WhatsApp at all = automation opportunity
        if "whatsapp" not in content_lower and lead.get("branch") in ["Restaurant", "Friseur", "Handwerk"]:
            score += 1
            signals.append("no_whatsapp")

        # Small team (1-10) = warm (can't afford dedicated staff)
        if any(w in content_lower for w in ["kleinbetrieb", "familienbetrieb", "inhabergeführt", "1-10 mitarbeiter", "handwerk"]):
            score += 1
            signals.append("small_business")

        # Large company (50+) = cold for our pricing
        if any(w in content_lower for w in ["über 50 mitarbeiter", "100 mitarbeiter", "konzern", "großunternehmen"]):
            score -= 2
            signals.append("large_company")

        # Outdated website signals (old CMS, no SSL, etc.) = warm
        if any(w in content_lower for w in ["wordpress", "typo3", "joomla", "contao"]):
            if "wp-" in content_lower or "wp-content" in content_lower:
                score += 1
                signals.append("outdated_cms")

        # Has PDF menus/price lists = warm (could be automated)
        if any(w in content_lower for w in [".pdf", "speisekarte pdf", "preisliste pdf", "download"]):
            score += 1
            signals.append("has_pdf_documents")

        # Social media but no automation = warm
        if any(w in content_lower for w in ["instagram", "facebook"]):
            if "social media automation" not in content_lower:
                score += 1
                signals.append("social_media_no_automation")

    # 4. Branch-based scoring
    branch = lead.get("branch", "")
    high_automation_branches = {
        "Steuerberater": 3,  # heavy invoicing/document processing
        "Elektriker": 2,
        "Dachdecker": 2,
        "Sanitär": 2,
        "Handwerksbetriebe": 2,
        "Restaurant": 2,  # reservations, orders
        "Immobilienmakler": 3,  # lead management
        "Anwalt": 2,
        "Friseur": 1,
    }
    branch_bonus = high_automation_branches.get(branch, 1)
    score += branch_bonus
    signals.append(f"branch_bonus_{branch}_{branch_bonus}")

    # 5. Region scoring (Berlin = more likely to adopt AI)
    if lead.get("region") == "Berlin":
        score += 1
        signals.append("berlin_tech_savvy")

    # Clamp to 1-10
    score = max(1, min(10, score))

    return score, signals


def warm_leads(leads, max_scrape=20):
    """Score all leads, scrape warmest ones first."""
    # First pass: score without website content
    scored = []
    for lead in leads:
        score, signals = score_lead(lead)
        scored.append({
            **lead,
            "warmth_score": score,
            "warmth_signals": signals,
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["warmth_score"], reverse=True)

    # Second pass: scrape top N websites for deeper scoring
    scraped_count = 0
    for lead in scored:
        if scraped_count >= max_scrape:
            break
        website = lead.get("website", "")
        if website and "gelbeseiten.de" not in website:
            print(f"  Scraping: {lead['company_name'][:30]}... ", end="")
            content = scrape_website(website)
            if content:
                # Re-score with content
                score, signals = score_lead(lead, content)
                lead["warmth_score"] = score
                lead["warmth_signals"] = signals
                lead["website_scraped"] = True
                print(f"score={score}")
            else:
                print("failed")
            scraped_count += 1
            time.sleep(0.5)

    return scored


def build_research_plan(leads, max_deep=10, max_demo=2):
    """Cheap-first hybrid plan.

    All leads receive deterministic screening metadata. Only the highest-scoring
    leads are marked for deep research, keeping expensive enrichment bounded.
    At most `max_demo` demo candidates (with verified email) per run.
    """
    ranked = sorted(
        (dict(lead) for lead in leads),
        key=lambda lead: (lead.get("warmth_score", 0), bool(lead.get("verified_email") or lead.get("email"))),
        reverse=True,
    )
    plan = []
    demo_count = 0
    for index, lead in enumerate(ranked):
        score = lead.get("warmth_score", 0)
        has_email = bool(lead.get("verified_email") or lead.get("email"))
        lead["automation_need"] = AUTOMATION_NEEDS.get(lead.get("branch", ""), "Büroprozesse")
        if demo_count < max_demo and score >= 6 and has_email:
            lead["research_depth"] = "deep"
            lead["recommended_action"] = "create_demo"
            lead["next_step"] = "Demo-Website bauen + E-Mail senden"
            demo_count += 1
        elif index < max_deep and score >= 5:
            lead["research_depth"] = "deep"
            lead["recommended_action"] = "contact"
            lead["next_step"] = "E-Mail senden"
        elif score >= 4:
            lead["research_depth"] = "light"
            lead["recommended_action"] = "review"
            lead["next_step"] = "Bewerten"
        else:
            lead["research_depth"] = "screened"
            lead["recommended_action"] = "archive"
            lead["next_step"] = "Archivieren"
        plan.append(lead)
    return plan


def main():
    print("=" * 60)
    print("Werkspree Lead Warmth Scorer")
    print("=" * 60)

    # Load latest leads (daily snapshot files only — leads_YYYYMMDD.json.
    # leads_all_merged.json / leads_new_branches.json are legacy experiment
    # files and must never be picked up by the glob.)
    lead_files = sorted(f for f in DATA_DIR.glob("leads_*.json") if re.match(r"leads_\d{8}\.json$", f.name))
    if not lead_files:
        print("No leads found!")
        return 1

    with open(lead_files[-1]) as f:
        leads = json.load(f)

    print(f"Loaded {len(leads)} leads from {lead_files[-1].name}")

    # Score leads
    print(f"\nScoring leads (scraping top 20 websites)...")
    scored = warm_leads(leads, max_scrape=20)

    # Bounded hybrid plan: cheap screening for all, at most 2 demo candidates
    # and deep research only for the highest-scoring leads.
    scored = build_research_plan(scored, max_deep=10, max_demo=2)

    # Save
    with open(SCORED_FILE, "w", encoding="utf-8") as f:
        json.dump(scored, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")

    score_dist = {}
    for l in scored:
        s = l["warmth_score"]
        score_dist[s] = score_dist.get(s, 0) + 1

    print(f"\nScore distribution:")
    for s in sorted(score_dist.keys(), reverse=True):
        bar = "█" * score_dist[s]
        print(f"  {s:2d}: {bar} ({score_dist[s]})")

    # Top 15 warmest
    print(f"\nTop 15 warmest leads:")
    for l in scored[:15]:
        email = l.get("verified_email") or l.get("email", "")
        email_str = f" ✉ {email}" if email else ""
        signals = ", ".join(l.get("warmth_signals", [])[:3])
        print(f"  [{l['warmth_score']}/10] {l['company_name'][:35]:35s} | {l['branch']:15s} | {l['region']:8s}{email_str} | {signals}")

    # Demo candidates
    demos = [l for l in scored if l.get("recommended_action") == "create_demo"]
    print(f"\n🎯 Demo candidates this run (max 2): {len(demos)}")
    for l in demos:
        print(f"  [{l['warmth_score']}/10] {l['company_name']} | {l.get('verified_email') or l.get('email')} | {l.get('automation_need')}")

    # Warm leads with email ready for outreach
    warm_with_email = [l for l in scored if l["warmth_score"] >= 5 and (l.get("verified_email") or l.get("email"))]
    print(f"\n🔥 Warm leads with email (ready for outreach): {len(warm_with_email)}")
    for l in warm_with_email:
        print(f"  [{l['warmth_score']}/10] {l['company_name']} | {l.get('verified_email') or l.get('email')}")

    # Warm leads needing website scrape for email
    warm_needs_email = [l for l in scored if l["warmth_score"] >= 5 and not (l.get("verified_email") or l.get("email")) and l.get("website") and "gelbeseiten" not in l.get("website", "")]
    print(f"\n🔥 Warm leads needing email extraction: {len(warm_needs_email)}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
