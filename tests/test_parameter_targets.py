from ronin.config import PROFILES
from ronin.models.parameters import count_parameters


def test_profiles_are_close_to_declared_parameter_targets():
    targets = {
        "tiny": 10_000_000,
        "seed-0": 150_000_000,
        "seed-1": 1_000_000_000,
        "seed-2": 7_000_000_000,
    }
    for name, (model_config, _) in PROFILES.items():
        actual = count_parameters(model_config)
        assert abs(actual - targets[name]) / targets[name] < 0.06


def test_parameter_counter_matches_allocated_small_model():
    from ronin.models.transformer import RoninLM

    config = PROFILES["tiny"][0]
    model = RoninLM(config)
    assert count_parameters(config) == model.parameter_count
