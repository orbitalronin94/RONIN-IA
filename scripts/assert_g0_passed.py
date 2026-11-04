"""Evalúa G-0 en modo fail-closed sin descargar ni inspeccionar textos."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("reports/license_audit.json"))
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Escribe authorized=true/false para condicionar jobs posteriores de Actions.",
    )
    args = parser.parse_args()
    audit = json.loads(args.report.read_text(encoding="utf-8"))
    gate = audit.get("gate", {})
    authorized = (
        gate.get("id") == "G-0"
        and gate.get("passed") is True
        and gate.get("status") == "PASS"
        and gate.get("downloads_authorized") is True
    )
    if args.github_output:
        args.github_output.parent.mkdir(parents=True, exist_ok=True)
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"authorized={'true' if authorized else 'false'}\n")
    if not authorized:
        reason = gate.get("reason", "G-0 ausente o inválido")
        print(f"G-0 no aprobado; adquisición y entrenamiento con las colecciones candidatas cubiertas por este informe bloqueados: {reason}")
        if not args.github_output:
            raise SystemExit(1)
        return
    print("G-0 PASS: adquisición autorizada por el informe versionado.")


if __name__ == "__main__":
    main()
