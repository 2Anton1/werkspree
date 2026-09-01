import unittest

try:
    from .build_microsite import TEMPLATE, render, slugify
    from .gemini_builder import is_valid_html
except ImportError:  # unittest discover -s microsites/pipeline
    from build_microsite import TEMPLATE, render, slugify
    from gemini_builder import is_valid_html


class MicrositeBuildTests(unittest.TestCase):
    def test_render_uses_matching_fields_and_segment_content(self):
        template = TEMPLATE.read_text()
        lead = {
            "company_name": "Fahrschule <Nord>",
            "segment": "Fahrschule",
            "city": "Brandenburg an der Havel",
            "address": "Fahrweg 1",
            "phone": "+49 172 123456",
            "email": "info@nord.example",
            "about": "Traditionsbäckerei und ![falsches Markdown]",
            "products": ["Suchen", "Website"],
            "opening_hours": {"Mo": "09:00–17:00"},
        }
        result = render(template, lead)
        self.assertIn("Fahrschule &lt;Nord&gt;", result)
        self.assertIn("Pkw-Ausbildung", result)
        self.assertIn("tel:+49172123456", result)
        self.assertIn("mailto:info@nord.example", result)
        self.assertNotIn("Traditionsbäckerei", result)
        self.assertNotIn("{{", result)

    def test_slug_is_ascii_and_stable(self):
        self.assertEqual(slugify("Fahrschule Ä & Co."), "fahrschule-a-co")

    def test_truncated_llm_document_is_rejected(self):
        self.assertFalse(is_valid_html("<!doctype html><html><head><style>body{"))


if __name__ == "__main__":
    unittest.main()
