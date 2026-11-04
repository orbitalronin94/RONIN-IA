#!/usr/bin/env python3
"""Fail-fast readiness gate for the official RUN 5 training workflow.

This check intentionally runs before model/data downloads or dependency installation.
It never changes admission state and never treats source candidates as training data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

HASH_FIELDS = (
    "manifest_sha256",
    "train_sha256",
    "sensitive_scan_sha256",
    "split_manifest_sha256",
    "dedup_report_sha256",
)
MINIMUM_DEFAULT = 1 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_report(
    manifest_path: Path,
    license_audit_path: Path,
    corpus_root: Path,
) -> dict[str, Any]:
    blockers: list[str] = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    audit = json.loads(license_audit_path.read_text(encoding="utf-8"))
    policy = manifest.get("policy", {})
    libraries = manifest.get("libraries", [])
    required = int(policy.get("required_library_count", 32))
    minimum = int(policy.get("minimum_train_bytes_per_library", MINIMUM_DEFAULT))

    gate = audit.get("gate", {})
    g0_passed = (
        gate.get("id") == "G-0"
        and gate.get("passed") is True
        and gate.get("status") == "PASS"
        and gate.get("downloads_authorized") is True
    )
    if not g0_passed:
        blockers.append(
            "G-0 no autoriza adquisición: "
            + str(gate.get("reason", "informe G-0 ausente, FAIL o inválido"))
        )

    if len(libraries) != required:
        blockers.append(f"Se requieren exactamente {required} bibliotecas; hay {len(libraries)}.")
    ids = [item.get("id") for item in libraries]
    if len(ids) != len(set(ids)):
        blockers.append("Hay identificadores de biblioteca duplicados.")

    admitted = 0
    total_train_bytes = 0
    library_rows: list[dict[str, Any]] = []
    for item in libraries:
        library_id = str(item.get("id", "<sin-id>"))
        reasons: list[str] = []
        if item.get("status") != "admitted":
            reasons.append(f"status={item.get('status')!r}, no admitted")
        if item.get("training_eligible") is not True:
            reasons.append("training_eligible no es true")
        if not item.get("revision"):
            reasons.append("falta revisión inmutable")
        if not item.get("license_audit"):
            reasons.append("falta auditoría de licencia")
        for field in HASH_FIELDS:
            if not re.fullmatch(r"[0-9a-f]{64}", str(item.get(field, ""))):
                reasons.append(f"{field} ausente o inválido")
        if not item.get("quality_review"):
            reasons.append("falta quality_review")
        if item.get("source_type") == "high_knowledge_density_extraction":
            if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("selection_report_sha256", ""))):
                reasons.append("falta hash del informe HKD")
            if not item.get("human_quality_review"):
                reasons.append("falta revisión humana de muestra HKD")

        declared_bytes = int(item.get("train_bytes", 0))
        if declared_bytes < minimum:
            reasons.append(f"{declared_bytes} bytes; mínimo {minimum}")
        corpus_file = corpus_root / library_id / "train.txt"
        if not corpus_file.is_file():
            reasons.append(f"no existe {corpus_file}")
        else:
            actual_bytes = corpus_file.stat().st_size
            if actual_bytes != declared_bytes:
                reasons.append(
                    f"train.txt tiene {actual_bytes} bytes; manifiesto declara {declared_bytes}"
                )
            expected_hash = str(item.get("train_sha256", ""))
            if re.fullmatch(r"[0-9a-f]{64}", expected_hash):
                actual_hash = sha256_file(corpus_file)
                if actual_hash != expected_hash:
                    reasons.append("SHA-256 de train.txt no coincide")

        if not reasons:
            admitted += 1
            total_train_bytes += declared_bytes
        else:
            blockers.extend(f"{library_id}: {reason}" for reason in reasons)
        library_rows.append({
            "id": library_id,
            "status": item.get("status"),
            "training_eligible": item.get("training_eligible"),
            "train_bytes": declared_bytes,
            "ready": not reasons,
            "blockers": reasons,
        })

    portfolio = manifest.get("portfolio", {})
    if portfolio.get("training_eligible") is not False:
        blockers.append("Portfolio debe permanecer excluido del entrenamiento.")
    if portfolio.get("counted_as_library") is not False:
        blockers.append("Portfolio no puede contar como biblioteca.")
    if portfolio.get("role") != "retrieval_only_fallback":
        blockers.append("Portfolio debe tener rol retrieval_only_fallback.")

    ready = not blockers and admitted == required
    return {
        "schema": "ronin-run5-preflight-v1",
        "ready": ready,
        "gate_g0": {
            "passed": g0_passed,
            "status": gate.get("status"),
            "reason": gate.get("reason"),
            "downloads_authorized": gate.get("downloads_authorized") is True,
        },
        "libraries": {
            "required": required,
            "admitted_and_verified": admitted,
            "minimum_train_bytes_each": minimum,
            "total_verified_train_bytes": total_train_bytes,
            "items": library_rows,
        },
        "portfolio": {
            "training_eligible": portfolio.get("training_eligible"),
            "counted_as_library": portfolio.get("counted_as_library"),
            "role": portfolio.get("role"),
        },
        "blockers": blockers,
        "policy": "Fail-closed. No gate is bypassed and no candidate source is auto-admitted.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/sixteen_libraries.json"))
    parser.add_argument("--license-audit", type=Path, default=Path("reports/license_audit.json"))
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("reports/run5-preflight.json"))
    args = parser.parse_args()

    report = build_report(args.manifest, args.license_audit, args.corpus_root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ready": report["ready"],
        "g0_passed": report["gate_g0"]["passed"],
        "admitted_libraries": report["libraries"]["admitted_and_verified"],
        "required_libraries": report["libraries"]["required"],
        "blocker_count": len(report["blockers"]),
        "report": str(args.report),
    }, ensure_ascii=False, indent=2))
    if not report["ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
