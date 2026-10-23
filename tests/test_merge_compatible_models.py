import importlib.util
import unittest

SPEC = importlib.util.spec_from_file_location(
    "merge_compatible_models", "scripts/merge_compatible_models.py"
)
merger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(merger)


class MergeCompatibilityTests(unittest.TestCase):
    def test_identical_tokenizer_vocab_is_compatible(self):
        self.assertTrue(
            merger.vocab_compatibility({"hola": 0, "mundo": 1}, {"hola": 0, "mundo": 1})["compatible"]
        )

    def test_different_token_ids_are_rejected(self):
        result = merger.vocab_compatibility({"hola": 0, "mundo": 1}, {"hola": 4, "mundo": 1})
        self.assertFalse(result["compatible"])
        self.assertEqual(result["shared_id_mismatches"], 1)

    def test_different_token_sets_are_rejected(self):
        result = merger.vocab_compatibility({"hola": 0}, {"adios": 0})
        self.assertFalse(result["compatible"])
        self.assertEqual(result["base_only"], 1)
        self.assertEqual(result["candidate_only"], 1)


if __name__ == "__main__":
    unittest.main()
