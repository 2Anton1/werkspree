#!/usr/bin/env python3
"""Poncho enrichment stage for the Werkspree hot-lead pipeline.

Reads leads produced by the cheap Maps discovery stage, asks Poncho to
perform capped deep verification, validates the contract, blocks unsafe
records, and writes a stable run artifact. It does not build sites or send
mail; the existing cron remains draft-only.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from poncho_client import run_hot_lead_research

BASE = Path(__file__).parent
DATA = BASE / "data"
RUN = DATA / "latest_hot_leads_run.json"


def _email_is_valid_shape(email):
    return isinstance(email, str) and "@" in email and "." in email.rsplit("@", 1)[-1]


def qualify(lead: object) -> tuple[bool, str]:
    if not isinstance(lead, dict):
        return False, "lead is not an object"
    try:
        rating = float(lead.get("rating") or 0)
    except (TypeError, ValueError):
        return False, "rating is invalid"
    if rating < 4.4:
        return False, "rating below 4.4"
    if lead.get("website_status") not in ("outdated", "dead", "no_website"):
        return False, "website status is current or unclear"
    if not _email_is_valid_shape(lead.get("business_email")):
        return False, "no public business email"
    if str(lead.get("email_verified", "")).lower() != "yes":
        return False, "email is not verified"
    if not lead.get("email_source_url"):
        return False, "email source URL missing"
    return True, "qualified"


def main():
    branch = sys.argv[1] if len(sys.argv) > 1 else "restaurant"
    region = sys.argv[2] if len(sys.argv) > 2 else "Berlin"
    result = run_hot_lead_research(branch, region, max_results=20, max_detail=8)
    qualified, blocked = [], list(result.get("blocked_leads") or [])
    for lead in result.get("hot_leads") or []:
        ok, reason = qualify(lead)
        if ok:
            qualified.append(lead)
        else:
            blocked.append({"company_name": lead.get("company_name", ""), "reason": reason})
    qualified.sort(key=lambda x: (float(x.get("rating") or 0), int(x.get("review_count") or 0)), reverse=True)
    qualified = qualified[:2]
    out = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_type": "poncho_enrichment_draft_only",
        "search": {"branch": branch, "region": region, "maps_result_limit": 20, "maps_detail_page_limit": 8, "rating_threshold": 4.4},
        "maps_results": result.get("maps_results", 0),
        "maps_results_rating_qualified": None,
        "maps_detail_pages_visited": result.get("detail_pages_visited", 0),
        "qualification_candidates": len(qualified),
        "candidates": qualified,
        "blocked_leads": blocked,
        "microsites_created": [],
        "drafts_created": [],
        "lovable_invoked": False,
        "outbound_email_sent": False,
        "poncho_chat_id": result.get("poncho_chat_id"),
        "poncho_cost_usd": result.get("cost_usd"),
        "notes": "Qualified records are handed to the existing draft-only stage; this script never deploys or sends.",
    }
    DATA.mkdir(exist_ok=True)
    RUN.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"qualified": len(qualified), "blocked": len(blocked), "poncho_cost_usd": result.get("cost_usd"), "run_file": str(RUN)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

