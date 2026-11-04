"""Valida estructuralmente el informe G-0 sin descargar corpus."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ronin.epistemic.license_audit import validate_license_audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/license_audit.json"),
    )
    args = parser.parse_args()
    audit = json.loads(args.report.read_text(encoding="utf-8"))
    validate_license_audit(audit)
    gate = audit["gate"]
    print(
        json.dumps(
            {
                "report": str(args.report),
                "gate": gate["id"],
                "status": gate["status"],
                "downloads_authorized": gate["downloads_authorized"],
                "sources": len(audit["sources"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
