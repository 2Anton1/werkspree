import unittest
from email_extraction import (
    find_emails_in_text,
    best_email,
    find_gelbeseiten_profile_url,
    find_real_website_on_profile_page,
    is_real_company_website,
)


class TestFindEmailsInText(unittest.TestCase):
    def test_plain_email(self):
        self.assertEqual(best_email("Kontakt: info@firma.de"), "info@firma.de")

    def test_mailto_link_preferred_over_plain(self):
        text = 'Schreiben Sie uns: <a href="mailto:kontakt@firma.de">Mail</a> oder info@andere-firma.de'
        self.assertEqual(best_email(text), "kontakt@firma.de")

    def test_obfuscated_at_dot(self):
        self.assertEqual(best_email("info [at] firma [dot] de"), "info@firma.de")

    def test_obfuscated_compact(self):
        self.assertEqual(best_email("info(at)firma(dot)de"), "info@firma.de")

    def test_obfuscated_spaced_words(self):
        self.assertEqual(best_email("Kontakt: info at firma dot de"), "info@firma.de")

    def test_generic_blocklisted_addresses_are_skipped(self):
        self.assertEqual(best_email("webmaster@firma.de"), "")
        self.assertEqual(best_email("test@example.com"), "")

    def test_no_email_returns_empty(self):
        self.assertEqual(best_email("Diese Seite enthaelt keine Kontaktdaten."), "")
        self.assertEqual(best_email(""), "")
        self.assertEqual(best_email(None), "")

    def test_multiple_emails_deduplicated(self):
        text = "info@firma.de steht hier zweimal: info@firma.de"
        self.assertEqual(find_emails_in_text(text), ["info@firma.de"])


class TestFindGelbeseitenProfileUrl(unittest.TestCase):
    def test_extracts_profile_link_from_listing_block(self):
        # Reale Struktur einer GelbeSeiten-Kategorieseite (Firecrawl-Markdown):
        details = (
            '\\\n\\\nElektroinstallationen]'
            '(https://www.gelbeseiten.de/gsbiz/c8d1de24-3efc-4429-a0d3-eff63484a56e)\n\n'
            'E-MailChat starten\n\nBuckower Chaussee 82,\n12277 Berlin'
        )
        self.assertEqual(
            find_gelbeseiten_profile_url(details),
            'https://www.gelbeseiten.de/gsbiz/c8d1de24-3efc-4429-a0d3-eff63484a56e',
        )

    def test_no_profile_link_returns_empty(self):
        self.assertEqual(find_gelbeseiten_profile_url('kein Link hier'), '')
        self.assertEqual(find_gelbeseiten_profile_url(''), '')


class TestFindRealWebsiteOnProfilePage(unittest.TestCase):
    def test_extracts_website_from_profile_markdown(self):
        # Der Kategorie-"Webseite"-Button hat keinen statischen Link (JS-gesteuert);
        # auf der Profilseite selbst steht der echte Link als normaler Markdown-Link.
        markdown = (
            'Einiges an Text...\n'
            '[Website](http://www.elektro-bs.de/ "http://www.elektro-bs.de")\n'
            'mehr Text...\n'
            '[Webseite](http://www.elektro-bs.de/)\n'
        )
        self.assertEqual(find_real_website_on_profile_page(markdown), 'http://www.elektro-bs.de')

    def test_no_website_link_returns_empty(self):
        self.assertEqual(find_real_website_on_profile_page('keine Webseite hier'), '')
        self.assertEqual(find_real_website_on_profile_page(''), '')


class TestIsRealCompanyWebsite(unittest.TestCase):
    def test_gelbeseiten_url_is_not_a_real_website(self):
        self.assertFalse(is_real_company_website(
            'https://www.gelbeseiten.de/gsbiz/8a257ebc-b80d-4e90-836c-5ed20e996965'
        ))

    def test_gelbeseiten_case_insensitive(self):
        self.assertFalse(is_real_company_website('https://WWW.GELBESEITEN.DE/gsbiz/xyz'))

    def test_empty_or_none_is_not_real(self):
        self.assertFalse(is_real_company_website(''))
        self.assertFalse(is_real_company_website(None))

    def test_real_domain_is_real(self):
        self.assertTrue(is_real_company_website('https://www.elektro-bs.de'))


if __name__ == "__main__":
    unittest.main()
