"""Bloquea adquisición/entrenamiento con corpus hasta aprobar el gate REF G-0.

No realiza consultas de red ni descarga datos. El informe debe ser revisado y
actualizado explícitamente antes de autorizar cualquier adquisición.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("reports/license_audit.json"))
    args = parser.parse_args()
    audit = json.loads(args.report.read_text(encoding="utf-8"))
    gate = audit.get("gate", {})
    if gate.get("id") != "G-0":
        raise SystemExit("G-0 ausente: adquisición bloqueada.")
    if gate.get("passed") is not True or gate.get("status") != "PASS":
        raise SystemExit(
            "G-0 no aprobado: se bloquea cualquier descarga o entrenamiento "
            f"con corpus. Estado={gate.get('status')!r}; motivo={gate.get('reason', '')}"
        )
    if gate.get("downloads_authorized") is not True:
        raise SystemExit("G-0 no autoriza descargas: operación bloqueada.")
    print("G-0 PASS: adquisición autorizada por el informe versionado.")


if __name__ == "__main__":
    main()
