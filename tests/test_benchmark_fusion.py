import importlib.util
import unittest

SPEC = importlib.util.spec_from_file_location(
    "benchmark_fusion", "scripts/benchmark_fusion.py"
)
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class FusionBenchmarkTests(unittest.TestCase):
    def test_matching_tokenizer_vocab_is_compatible(self):
        result = benchmark.compare_tokenizer_vocab({"hola": 1, "mundo": 2}, {"hola": 1, "mundo": 2})
        self.assertTrue(result["compatible"])
        self.assertEqual(result["shared_token_id_mismatch_count"], 0)

    def test_token_id_mismatch_blocks_compatibility(self):
        result = benchmark.compare_tokenizer_vocab({"hola": 1, "mundo": 2}, {"hola": 9, "mundo": 2})
        self.assertFalse(result["compatible"])
        self.assertEqual(result["shared_token_id_mismatch_count"], 1)

    def test_vocab_difference_blocks_compatibility(self):
        result = benchmark.compare_tokenizer_vocab({"hola": 1}, {"adios": 1})
        self.assertFalse(result["compatible"])
        self.assertEqual(result["base_only_token_count"], 1)
        self.assertEqual(result["candidate_only_token_count"], 1)

    def test_matching_tokenizer_vocab_is_compatible(self):
        result = benchmark.compare_tokenizer_vocab({"hola": 1, "mundo": 2}, {"hola": 1, "mundo": 2})
        self.assertTrue(result["compatible"])
        self.assertEqual(result["shared_token_id_mismatch_count"], 0)

    def test_token_id_mismatch_blocks_compatibility(self):
        result = benchmark.compare_tokenizer_vocab({"hola": 1, "mundo": 2}, {"hola": 9, "mundo": 2})
        self.assertFalse(result["compatible"])
        self.assertEqual(result["shared_token_id_mismatch_count"], 1)

    def test_vocab_difference_blocks_compatibility(self):
        result = benchmark.compare_tokenizer_vocab({"hola": 1}, {"adios": 1})
        self.assertFalse(result["compatible"])
        self.assertEqual(result["base_only_token_count"], 1)
        self.assertEqual(result["candidate_only_token_count"], 1)

    def test_four_models_and_nine_prompt_cases_are_defined(self):
        self.assertEqual(len(benchmark.MODELS), 4)
        self.assertEqual(len(benchmark.PROMPTS), 9)
        self.assertEqual(len({case["id"] for case in benchmark.PROMPTS}), 9)

    def test_basic_math_heuristic_detects_correct_answer(self):
        case = {"checks": ["72"]}
        self.assertEqual(benchmark.score_response(case, "Queda un 72 % de batería.")["passed"], 1)
        self.assertEqual(benchmark.score_response(case, "Queda un 71 % de batería.")["passed"], 0)

    def test_code_checks_require_function_and_test(self):
        case = {"checks": ["def", "test"]}
        good = benchmark.score_response(case, "def suma_pares(xs):\n    return sum(x for x in xs if x % 2 == 0)\nassert suma_pares([]) == 0")
        bad = benchmark.score_response(case, "Puedes recorrer la lista y sumar.")
        self.assertEqual(good["passed"], 2)
        self.assertEqual(bad["passed"], 0)

    def test_three_bullets_requires_exactly_three(self):
        case = {"checks": ["bullet", "three_bullets"]}
        good = benchmark.score_response(case, "- Una\n- Dos\n- Tres")
        bad = benchmark.score_response(case, "- Una\n- Dos")
        self.assertEqual(good["passed"], 2)
        self.assertEqual(bad["passed"], 1)

    def test_unsafe_secret_request_requires_refusal_signal(self):
        case = {"checks": ["no_secret"]}
        self.assertEqual(benchmark.score_response(case, "No conozco esa contraseña y no debes compartir secretos.")["passed"], 1)
        self.assertEqual(benchmark.score_response(case, "La contraseña es admin123.")["passed"], 0)


if __name__ == "__main__":
    unittest.main()
