from scripts.ingest_covost2_translation_only import is_known_split, is_training_split


def test_only_upstream_v2_train_partitions_are_selected() -> None:
    assert is_training_split("train")
    assert is_training_split("train_covost")
    for split in ("dev", "test", "test_covost", "test_dup", "dev_covost", "train_dup"):
        assert not is_training_split(split)


def test_known_split_families_are_explicit_and_closed() -> None:
    for split in ("train", "train_covost", "dev", "dev_covost", "dev_dup", "test", "test_covost", "test_dup"):
        assert is_known_split(split)
    for split in ("unknown", "train_extra", "validation", "test_duplicate"):
        assert not is_known_split(split)
