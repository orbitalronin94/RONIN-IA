"""Pruebas del constructor reproducible de pares de opacidad."""
import json

from scripts.build_obfuscation_cases import build


def test_construye_pares_y_controles_con_procedencia_y_particiones(tmp_path):
    manifest = {
        "sources": [
            {"id": source_id, "sha256": str(index) * 64}
            for index, source_id in enumerate(
                [
                    "poe-gold-bug",
                    "verne-la-jangada-fr",
                    "hypnerotomachia-poliphili-1499",
                "trithemius-steganographia-1608",
                "selenus-cryptomenytices-1624",
                    "trithemius-steganographia-1608",
                    "selenus-cryptomenytices-1624",
                ],
                start=1,
            )
        ]
    }
    manifest_path = tmp_path / "source-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "cases.jsonl"

    summary = build(manifest_path, output, noise_count=30)

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 34
    assert summary["counts_by_type"] == {"A": 2, "B": 30, "C": 1, "D": 1}
    assert summary["counts_by_label"]["NO_MESSAGE_IN_CONTROL"] == 30
    assert all(len(row["source_sha256"]) == 64 for row in rows)
    assert all(row["evidence_refs"] for row in rows)
    assert {row["split"] for row in rows} >= {"train", "validation", "test"}
    assert all(row["synthetic"] for row in rows if row["case_type"] == "B")
    assert not any(row["synthetic"] for row in rows if row["case_type"] != "B")


def test_generacion_sintetica_determinista(tmp_path):
    manifest = {
        "sources": [
            {"id": source_id, "sha256": "a" * 64}
            for source_id in (
                "poe-gold-bug",
                "verne-la-jangada-fr",
                "hypnerotomachia-poliphili-1499",
            )
        ]
    }
    source = tmp_path / "source.json"
    source.write_text(json.dumps(manifest), encoding="utf-8")
    first, second = tmp_path / "first.jsonl", tmp_path / "second.jsonl"

    build(source, first, noise_count=10)
    build(source, second, noise_count=10)

    assert first.read_bytes() == second.read_bytes()
