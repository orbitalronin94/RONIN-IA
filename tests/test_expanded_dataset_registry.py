from pathlib import Path

from scripts.validate_expanded_dataset_registry import validate


REGISTRY = Path(__file__).parents[1] / "data/datasets/catalog/expanded-domain-registry.json"

def test_expanded_registry_is_32_domains_and_64_candidate_libraries():
    assert validate(REGISTRY) == []
