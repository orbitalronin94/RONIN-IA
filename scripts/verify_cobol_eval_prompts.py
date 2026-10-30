#!/usr/bin/env python3
"""Verify COBOL-derived model prompts against compiled GnuCOBOL fixtures."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=30, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("cobol-prompt-oracle-report.json"))
    args = parser.parse_args()
    root = args.source_root.resolve()
    dataset = json.loads if False else None
    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    cases = [row for row in rows if row.get("oracle_source_path")]
    if not cases:
        raise SystemExit("No COBOL oracle cases found in model prompt dataset")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    results = []
    for case in cases:
        source = (root / case["oracle_source_path"]).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise SystemExit("Missing or unsafe oracle fixture: " + case["oracle_source_path"])
        with tempfile.TemporaryDirectory(prefix="ronin-cobol-oracle-") as tmp:
            work = Path(tmp)
            binary = work / "reference"
            compiled = run(["cobc", "-x", "-I", str(source.parent), "-o", str(binary), str(source)], cwd=root)
            if compiled.returncode != 0:
                results.append({"id": case["id"], "status": "compile_failed",
                                "stderr": compiled.stderr.decode("utf-8", "replace")[-2000:]})
                continue
            executed = run([str(binary)], cwd=work)
            expected = case["oracle_expected_stdout"].encode("utf-8")
            exact = executed.stdout == expected and executed.returncode == 0
            results.append({
                "id": case["id"],
                "source_path": case["oracle_source_path"],
                "status": "pass" if exact else "mismatch",
                "expected_stdout_hex": expected.hex(),
                "actual_stdout_hex": executed.stdout.hex(),
                "expected_returncode": 0,
                "actual_returncode": executed.returncode,
            })
    report = {
        "schema_version": 1,
        "oracle": "GnuCOBOL",
        "source_repo": "orbitalronin94/cobol2py",
        "source_revision": revision,
        "cases": results,
        "passed": sum(row["status"] == "pass" for row in results),
        "total": len(results),
    }
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
