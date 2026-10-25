import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "sweep_fusions", "scripts/sweep_fusions.py"
)
sweep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sweep)


class SweepReproducibilityTests(unittest.TestCase):
    def test_fingerprint_is_deterministic(self):
        revisions = {sweep.BASE: "abc123", **{repo: "def456" for repo in sweep.CANDIDATES.values()}}
        self.assertEqual(
            sweep.experiment_fingerprint(revisions),
            sweep.experiment_fingerprint(revisions),
        )

    def test_fingerprint_changes_when_a_model_revision_changes(self):
        revisions = {sweep.BASE: "base-a", **{repo: "candidate-a" for repo in sweep.CANDIDATES.values()}}
        changed = dict(revisions)
        changed[sweep.BASE] = "base-b"
        self.assertNotEqual(
            sweep.experiment_fingerprint(revisions),
            sweep.experiment_fingerprint(changed),
        )

    def test_identical_structural_configs_are_compatible(self):
        config = {
            "model_type": "qwen3", "architectures": ["Qwen3ForCausalLM"],
            "hidden_size": 1024, "num_hidden_layers": 28,
            "rope_theta": 1000000.0,
        }
        self.assertTrue(sweep.config_compatibility(config, dict(config))["compatible"])

    def test_rope_configuration_mismatch_is_rejected(self):
        reference = {"model_type": "qwen3", "rope_theta": 1000000.0}
        candidate = {"model_type": "qwen3", "rope_theta": 10000.0}
        result = sweep.config_compatibility(reference, candidate)
        self.assertFalse(result["compatible"])
        self.assertIn("rope_theta", result["mismatches"])

    def test_missing_structural_config_field_is_rejected(self):
        result = sweep.config_compatibility(
            {"model_type": "qwen3", "hidden_size": 1024},
            {"model_type": "qwen3"},
        )
        self.assertFalse(result["compatible"])
        self.assertIn("hidden_size", result["missing_on_one_side"])

    def test_checkpoint_requires_completed_report_and_weights(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / sweep.EXPERIMENTAL_CHECKPOINT_NAME
            checkpoint.mkdir()
            (checkpoint / "config.json").write_text("{}", encoding="utf-8")
            (checkpoint / "model.safetensors").write_bytes(b"test")
            report = {
                "status": "completed",
                "best_beats_base_heuristic": True,
                "exported_checkpoint": str(checkpoint),
            }
            self.assertTrue(sweep.checkpoint_is_valid(report, root))
            report["status"] = "running"
            self.assertFalse(sweep.checkpoint_is_valid(report, root))

    def test_checkpoint_without_weights_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / sweep.EXPERIMENTAL_CHECKPOINT_NAME
            checkpoint.mkdir()
            (checkpoint / "config.json").write_text("{}", encoding="utf-8")
            report = {
                "status": "completed",
                "best_beats_base_heuristic": True,
                "exported_checkpoint": str(checkpoint),
            }
            self.assertFalse(sweep.checkpoint_is_valid(report, root))


if __name__ == "__main__":
    unittest.main()
