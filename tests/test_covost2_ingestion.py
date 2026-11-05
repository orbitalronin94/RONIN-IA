from scripts.ingest_covost2_translation_only import KNOWN_SPLITS, is_training_split


def test_covost_v2_training_split_matches_upstream_contract() -> None:
    assert is_training_split("train")
    assert is_training_split("train_covost")
    assert not is_training_split("dev")
    assert not is_training_split("test")
    assert not is_training_split("test_covost")


def test_covost_v2_known_split_labels_are_closed() -> None:
    assert KNOWN_SPLITS == {"train", "train_covost", "dev", "test", "test_covost"}
    assert not is_training_split("dev_covost")
    assert not is_training_split("unknown")
