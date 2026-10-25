import importlib.util
import tempfile
import unittest
from pathlib import Path
import json

SPEC = importlib.util.spec_from_file_location("benchmark_merge_vs_base", "scripts/benchmark_merge_vs_base.py")
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class MergeVsBaseTests(unittest.TestCase):
    def test_metric_selection_is_stable_and_prefers_normalized_accuracy(self):
        result = benchmark.select_metrics({
            "hellaswag": {"acc": 0.6, "acc_norm": 0.7, "acc_stderr": 0.01},
            "gsm8k": {"exact_match": 0.25},
        })
        self.assertEqual(result["hellaswag"], {"metric": "acc_norm", "score": 0.7})
        self.assertEqual(result["gsm8k"], {"metric": "exact_match", "score": 0.25})

    def test_comparison_delta_and_missing_tasks(self):
        result = benchmark.compare(
            {"metrics": {"a": {"metric": "acc", "score": 0.5}, "b": {"metric": "acc", "score": 0.2}}},
            {"metrics": {"a": {"metric": "acc", "score": 0.6}, "c": {"metric": "acc", "score": 0.9}}},
        )
        self.assertEqual(result["comparable_task_count"], 1)
        self.assertEqual(result["mean_delta"], 0.1)
        self.assertEqual(result["improved_tasks"], 1)
        self.assertIsNone(result["tasks"][1]["delta_merged_minus_base"])

    def test_different_metric_types_are_not_compared(self):
        result = benchmark.compare(
            {"metrics": {"a": {"metric": "acc", "score": 0.5}}},
            {"metrics": {"a": {"metric": "exact_match", "score": 0.6}}},
        )
        self.assertEqual(result["comparable_task_count"], 0)
        self.assertIsNone(result["tasks"][0]["delta_merged_minus_base"])

    def test_validation_flags_missing_and_incomparable_requested_tasks(self):
        base = {"metrics": {"a": {"metric": "acc", "score": 0.5}}}
        merged = {"metrics": {"a": {"metric": "exact_match", "score": 0.6}}}
        comparison = benchmark.compare(base, merged)
        result = benchmark.validate_comparison(base, merged, comparison, ["a", "b"])
        self.assertFalse(result["complete"])
        self.assertEqual(result["base_missing_tasks"], ["b"])
        self.assertEqual(result["merged_missing_tasks"], ["b"])
        self.assertEqual(result["incomparable_tasks"], ["a"])

    def test_validation_accepts_all_requested_comparable_tasks(self):
        base = {"metrics": {"a": {"metric": "acc", "score": 0.5}}}
        merged = {"metrics": {"a": {"metric": "acc", "score": 0.6}}}
        comparison = benchmark.compare(base, merged)
        result = benchmark.validate_comparison(base, merged, comparison, ["a"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["requested_task_count"], 1)

    def test_result_discovery_requires_results_object(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, "junk.json").write_text('{"hello": "world"}', encoding="utf-8")
            Path(temp, "results.json").write_text(json.dumps({"results": {"x": {"acc": 0.5}}}), encoding="utf-8")
            self.assertEqual(benchmark.find_results(temp)["results"]["x"]["acc"], 0.5)


if __name__ == "__main__":
    unittest.main()
