#!/usr/bin/env python3
"""Deterministic smoke test for the Automation Starter demo.

This test deliberately performs no network calls, sends no email and writes no
CRM data. It proves the documented starter input produces a useful lead score
and the fields consumed by the outreach/CRM stages.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scraper"))
from warmth_scorer import score_lead  # noqa: E402


class AutomationStarterDemoTest(unittest.TestCase):
    def test_contact_form_lead_is_actionable(self):
        lead = {
            "company_name": "Demo Elektro Berlin",
            "branch": "Elektriker",
            "region": "Berlin",
            "website": "https://demo-elektro.example",
            "verified_email": "kontakt@demo-elektro.example",
        }
        website_text = (
            "Kontaktformular für Angebotsanfragen. Leistungen: Installation, "
            "Wartung und Photovoltaik. Keine Online-Terminbuchung."
        )
        score, signals = score_lead(lead, website_text)
        self.assertGreaterEqual(score, 6)
        self.assertIn("has_email", signals)
        self.assertIn("branch_bonus_Elektriker_2", signals)


if __name__ == "__main__":
    unittest.main()
