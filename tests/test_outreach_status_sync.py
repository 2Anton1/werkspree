import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_pipeline.py"
SPEC = importlib.util.spec_from_file_location("werkspree_run_pipeline", MODULE_PATH)
PIPELINE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PIPELINE)


class OutreachStatusSyncTest(unittest.TestCase):
    def test_merges_recorded_outreach_state_by_company(self):
        leads = [
            {"company_name": "Kontakt GmbH", "response_status": "none"},
            {"company_name": "Ohne Versand", "response_status": "none"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            sent_file = Path(directory) / "sent_emails.json"
            sent_file.write_text(json.dumps({
                "Kontakt GmbH": {"response_status": "followup_sent"},
            }))
            self.assertEqual(PIPELINE.merge_outreach_statuses(leads, sent_file), 1)

        self.assertEqual(leads[0]["response_status"], "followup_sent")
        self.assertEqual(leads[1]["response_status"], "none")

    def test_keeps_existing_contact_status(self):
        lead = {"response_status": "followup_sent"}
        self.assertEqual(
            PIPELINE.resolved_crm_status(lead, {"Status": "Kontaktiert"}),
            "Kontaktiert",
        )

    def test_maps_sent_status_when_no_human_progress_exists(self):
        lead = {"response_status": "awaiting_reply"}
        self.assertEqual(PIPELINE.resolved_crm_status(lead, {"Status": "Neu"}), "Kontaktiert")


if __name__ == "__main__":
    unittest.main()
