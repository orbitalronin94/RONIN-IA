import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score_model_eval.py"
SPEC = importlib.util.spec_from_file_location("score_model_eval", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ModelEvalScorerTests(unittest.TestCase):
    def test_exact_and_json_scores(self):
        self.assertTrue(MODULE.score_case({"scoring": "exact", "expected": "42"}, " 42\n"))
        self.assertFalse(MODULE.score_case({"scoring": "exact", "expected": "42"}, "forty two"))
        self.assertTrue(MODULE.score_case({"scoring": "json_exact", "expected": "{\"ok\":true}"}, '{ "ok": true }'))
        self.assertFalse(MODULE.score_case({"scoring": "json_exact", "expected": "{\"ok\":true}"}, "not json"))

    def test_human_review_is_not_scored(self):
        self.assertIsNone(MODULE.score_case({"scoring": "human_review"}, "any text"))

    def test_evaluate_reports_missing_and_latency(self):
        dataset = [
            {"id": "a", "language": "es", "category": "math", "expected": "42", "scoring": "exact"},
            {"id": "b", "language": "es", "category": "summary", "expected": None, "scoring": "human_review"},
            {"id": "c", "language": "en", "category": "math", "expected": "12", "scoring": "exact"},
        ]
        predictions = [
            {"case_id": "a", "output": "42", "latency_ms": 100},
            {"case_id": "b", "output": "Resumen correcto", "latency_ms": 300},
        ]
        report = MODULE.evaluate(dataset, predictions)
        self.assertEqual(report["deterministic_scored"], 2)
        self.assertEqual(report["deterministic_correct"], 1)
        self.assertEqual(report["deterministic_accuracy"], 0.5)
        self.assertEqual(report["latency_ms"]["median"], 200)
        self.assertEqual(report["cases"][2]["status"], "missing")

    def test_unknown_and_duplicate_ids_fail(self):
        dataset = [{"id": "a", "scoring": "exact", "expected": "x"}]
        with self.assertRaisesRegex(ValueError, "Unknown case_id"):
            MODULE.evaluate(dataset, [{"case_id": "z", "output": "x"}])
        with self.assertRaisesRegex(ValueError, "Duplicate prediction"):
            MODULE.evaluate(dataset, [{"case_id": "a", "output": "x"}, {"case_id": "a", "output": "x"}])


if __name__ == "__main__":
    unittest.main()
