import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from poncho_enrichment import qualify

BASE = {
    "rating": 4.6,
    "website_status": "outdated",
    "business_email": "info@example.de",
    "email_verified": "yes",
    "email_source_url": "https://example.de/impressum",
}


def test_qualifies_verified_outdated():
    assert qualify(BASE) == (True, "qualified")


def test_accepts_no_website_and_dead():
    for status in ("no_website", "dead"):
        ok, _ = qualify({**BASE, "website_status": status})
        assert ok


def test_blocks_current_or_unclear_website():
    for status in ("current", "unclear"):
        ok, _ = qualify({**BASE, "website_status": status})
        assert not ok


def test_blocks_unverified_or_missing_email():
    for lead in ({**BASE, "email_verified": "unknown"}, {**BASE, "business_email": ""}):
        ok, _ = qualify(lead)
        assert not ok


def test_blocks_missing_source_or_low_rating():
    for lead in ({**BASE, "email_source_url": ""}, {**BASE, "rating": 4.3}):
        ok, _ = qualify(lead)
        assert not ok


def test_blocks_malformed_lead():
    for lead in (None, {}, []):
        ok, _ = qualify(lead)
        assert not ok


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} qualification tests")

