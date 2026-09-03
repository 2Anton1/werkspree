#!/usr/bin/env python3
"""Werkspree: Microsite-Build mit Gemini als Primärgenerator, Fallback auf Template.

Reihenfolge pro Lead:
  1. Gemini (gemini_builder.generate_microsite, 3 Versuche mit Qualitätsprüfung)
  2. Bei Fehlschlag: deterministisches Template (build_microsite.py)

Exit-Codes (kompatibel mit build_microsite.py):
  0 = gebaut (Gemini ODER Template), 2 = Lead nicht qualifiziert/gesperrt,
  3 = Render-Fehler (beide Wege fehlgeschlagen).

Nutzung:
  python3 build_microsite_gemini.py --lead <lead.json>
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PIPE = Path(__file__).parent
REPO = PIPE.parent.parent
OUT_DIR = REPO / "microsites" / "sites"
BUILD_TEMPLATE = PIPE / "build_microsite.py"
TZ = timezone(timedelta(hours=2))  # CEST

from build_microsite import slugify  # gleiche Slug-Logik wie Template-Builder


def is_qualified(lead) -> bool:
    """Gleiche Qualifikations-/Opt-out-Prüfung wie build_microsite.py."""
    if not lead.get("email_verified"):
        print("ERROR: Lead nicht qualifiziert (email_verified != yes)")
        return False
    email = str(lead.get("email") or "").strip().lower()
    if not re.fullmatch(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,63}", email, re.I):
        print("ERROR: Lead nicht qualifiziert (ungueltige E-Mail)")
        return False
    optout_path = PIPE / "data" / "opt_out.json"
    if optout_path.exists():
        optout = json.loads(optout_path.read_text())
        domain = email.rsplit("@", 1)[-1]
        company = str(lead.get("company_name") or lead.get("name") or "").lower()
        if (email in {str(v).lower() for v in optout.get("emails", [])}
                or domain in {str(v).lower() for v in optout.get("domains", [])}
                or any(str(v).lower() in company for v in optout.get("companies", []))):
            print("ERROR: Lead gesperrt (Opt-out)")
            return False
    return True


def build_gemini(lead, lead_path, slug):
    """Gemini-Versuch. Schreibt bei Erfolg HTML + site_url ins lead.json."""
    from gemini_builder import generate_microsite
    out = OUT_DIR / slug
    out.mkdir(parents=True, exist_ok=True)
    index = out / "index.html"
    success = generate_microsite(lead, index)
    if not success:
        return False
    lead["site_url"] = f"https://werkspree.bki-de.de/microsites/sites/{slug}/"
    lead["built_at"] = datetime.now(TZ).isoformat()
    lead["slug"] = slug
    lead["builder"] = "gemini"
    lead_path.write_text(json.dumps(lead, ensure_ascii=False, indent=2))
    print(f"OK (Gemini): {index}")
    return True


def build_template(lead_path):
    """Fallback: deterministischer Template-Builder (macht eigene Prüfungen)."""
    print("Gemini fehlgeschlagen -> Fallback: Template-Builder")
    r = subprocess.run(
        [sys.executable, str(BUILD_TEMPLATE), "--lead", str(lead_path)],
        capture_output=True, text=True, cwd=str(PIPE),
    )
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:500])
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", required=True, help="Pfad zu Lead-JSON")
    args = ap.parse_args()

    lead_path = Path(args.lead)
    lead = json.loads(lead_path.read_text())

    if not is_qualified(lead):
        return 2

    slug = lead.get("slug") or slugify(lead.get("company_name") or lead.get("name", "lead"))

    if build_gemini(lead, lead_path, slug):
        return 0

    rc = build_template(lead_path)
    if rc == 0:
        # Template-Builder hat site_url bereits zurückgeschrieben
        return 0
    print("ERROR: Beide Build-Wege fehlgeschlagen")
    return 3


if __name__ == "__main__":
    sys.exit(main())
