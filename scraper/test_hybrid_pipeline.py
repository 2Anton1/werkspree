import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import warmth_scorer


class HybridPipelineTests(unittest.TestCase):
    def test_research_plan_selects_deep_only_for_top_leads(self):
        leads = [
            {"company_name": "cold", "warmth_score": 3, "email": ""},
            {"company_name": "warm", "warmth_score": 6, "email": "a@example.de"},
            {"company_name": "hot", "warmth_score": 9, "email": "b@example.de"},
        ]
        plan = warmth_scorer.build_research_plan(leads, max_deep=2)
        self.assertEqual([x["company_name"] for x in plan[:2]], ["hot", "warm"])
        self.assertEqual(plan[0]["research_depth"], "deep")
        self.assertEqual(plan[1]["research_depth"], "deep")
        self.assertEqual(plan[2]["research_depth"], "screened")

    def test_research_plan_marks_non_selected_leads_as_screened(self):
        leads = [{"company_name": "cold", "warmth_score": 3, "email": ""}]
        plan = warmth_scorer.build_research_plan(leads, max_deep=2)
        self.assertEqual(plan[0]["research_depth"], "screened")
        self.assertEqual(plan[0]["recommended_action"], "archive")


if __name__ == "__main__":
    unittest.main()
