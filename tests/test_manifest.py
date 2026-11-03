from ronin.manifest.registry import FEATURES, readiness, validate_registry


def test_registry_has_exactly_fifty_features_in_expected_groups():
    validate_registry()
    assert len(FEATURES) == 50


def test_readiness_counts_only_features_with_evidence():
    report = readiness("tiny")
    assert report["eligible"] > 0
    assert report["implemented_with_evidence"] > 0
    assert report["implemented_with_evidence"] + report["planned"] + report["blocked"] == report["eligible"]


def test_readiness_rejects_unknown_profile():
    try:
        readiness("unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown profile should fail")
