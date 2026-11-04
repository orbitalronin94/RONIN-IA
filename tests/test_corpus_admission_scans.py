import json
import subprocess
import sys
from pathlib import Path


def test_sensitive_scanner_reports_types_without_printing_secret_values(tmp_path: Path):
    source = tmp_path / "train.txt"
    source.write_text("Contact admin@example.org or use api_key=abcdefghijklmnop123456.\n", encoding="utf-8")
    report = tmp_path / "scan.json"
    result = subprocess.run([
        sys.executable, "scripts/scan_corpus_sensitive_content.py",
        "--input", str(source), "--report", str(report), "--fail-on-findings"
    ], capture_output=True, text=True, check=False)
    assert result.returncode == 2
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["total_findings"] >= 2
    assert "admin@example.org" not in result.stdout
    assert "abcdefghijklmnop123456" not in result.stdout


def test_cross_library_overlap_audit_requires_all_sixteen_files(tmp_path: Path):
    for name in (
        "mathematics", "logic_epistemology", "philosophy", "physics",
        "chemistry", "biology_medicine", "computer_science",
        "law_economics_social_sciences", "mathematics_hkd",
        "logic_epistemology_hkd", "philosophy_hkd", "physics_hkd",
        "chemistry_hkd", "biology_medicine_hkd", "computer_science_hkd",
        "law_economics_social_sciences_hkd",
    ):
        path = tmp_path / name / "train.txt"
        path.parent.mkdir()
        path.write_text("A mathematical theorem is proven from axioms.\n", encoding="utf-8")
    report = tmp_path / "overlap.json"
    result = subprocess.run([
        sys.executable, "scripts/audit_sixteen_library_overlap.py",
        "--corpus-root", str(tmp_path), "--report", str(report)
    ], capture_output=True, text=True, check=False)
    assert result.returncode == 2
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["libraries_found"] == 16
    assert data["exact_cross_library_duplicates"]
