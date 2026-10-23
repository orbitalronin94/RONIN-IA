import importlib.util
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "audit_fusion_candidates", "scripts/audit_fusion_candidates.py"
)
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


class FusionAuditTests(unittest.TestCase):
    def test_candidate_count_and_base_reference(self):
        self.assertEqual(len(audit_module.CANDIDATES), 24)
        self.assertEqual(audit_module.CANDIDATES["qwen3_base"], "Qwen/Qwen3-0.6B")

    def test_weight_filter_excludes_adapter_and_gguf(self):
        self.assertTrue(audit_module.is_full_weight_file("model.safetensors"))
        self.assertTrue(audit_module.is_full_weight_file("pytorch_model.bin"))
        self.assertFalse(audit_module.is_full_weight_file("adapter_model.safetensors"))
        self.assertFalse(audit_module.is_full_weight_file("adapter_config.json"))
        self.assertFalse(audit_module.is_full_weight_file("model.gguf"))
        self.assertFalse(audit_module.is_full_weight_file("model-lora.safetensors"))

    def test_candidate_metadata_and_config_are_read(self):
        api_data = {
            "sha": "abc123",
            "siblings": [
                {"rfilename": "model.safetensors"},
                {"rfilename": "tokenizer.json"},
                {"rfilename": "config.json"},
            ],
            "cardData": {"license": "apache-2.0", "base_model": "Qwen/Qwen3-0.6B"},
        }
        config = {
            "model_type": "qwen3",
            "architectures": ["Qwen3ForCausalLM"],
            "hidden_size": 1024,
            "intermediate_size": 3072,
            "num_hidden_layers": 28,
            "num_attention_heads": 16,
            "num_key_value_heads": 8,
            "head_dim": 128,
            "vocab_size": 151936,
            "tie_word_embeddings": True,
        }
        with patch.object(audit_module, "get_json", side_effect=[api_data, config]):
            result = audit_module.audit("example/model")
        self.assertEqual(result["revision"], "abc123")
        self.assertEqual(result["license"], "apache-2.0")
        self.assertTrue(result["has_full_weight_file"])
        self.assertIn("tokenizer.json", result["tokenizer_files"])
        self.assertEqual(result["config"]["hidden_size"], 1024)
        self.assertEqual(result["errors"], [])

    def test_api_failure_is_reported_not_silently_accepted(self):
        with patch.object(audit_module, "get_json", side_effect=OSError("offline")):
            result = audit_module.audit("example/model")
        self.assertTrue(result["errors"])
        self.assertIn("Error consultando Hugging Face API", result["errors"][0])

    def test_adapter_or_gguf_only_is_not_full_weights(self):
        api_data = {
            "sha": "abc123",
            "siblings": [{"rfilename": "adapter_model.safetensors"}, {"rfilename": "model.gguf"}],
            "cardData": {"license": "apache-2.0"},
        }
        config = {"model_type": "qwen3"}
        with patch.object(audit_module, "get_json", side_effect=[api_data, config]):
            result = audit_module.audit("example/model")
        self.assertFalse(result["has_full_weight_file"])
        self.assertTrue(any("archivo de pesos completo" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
