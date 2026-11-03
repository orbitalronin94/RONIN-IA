"""Command-line entry point for RONIN-IA."""

from __future__ import annotations

import argparse
import json

from ronin.config import PROFILES, profile_dict
from ronin.manifest.registry import FEATURES, readiness
from ronin.models.parameters import count_parameters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ronin", description="RONIN from-scratch LM toolkit")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("info", "show validated profile configuration"),
        ("count-params", "calculate model parameters from architecture"),
        ("features", "list the canonical 50-feature registry"),
        ("readiness", "show evidence-based profile readiness"),
        ("roadmap", "show the implementation sequence"),
    ):
        command = sub.add_parser(name, help=help_text)
        if name in {"info", "count-params", "readiness"}:
            command.add_argument("--profile", choices=sorted(PROFILES), default="tiny")
        if name == "features":
            command.add_argument("--category", choices=sorted({f.category for f in FEATURES}))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "info":
        print(json.dumps(profile_dict(args.profile), indent=2))
    elif args.command == "count-params":
        model_config, _ = PROFILES[args.profile]
        count = count_parameters(model_config)
        print(f"{args.profile}: {count:,} trainable parameters (analytical, no model allocation)")
    elif args.command == "features":
        selected = [f for f in FEATURES if args.category is None or f.category == args.category]
        print(json.dumps([f.__dict__ for f in selected], indent=2, default=str))
    elif args.command == "readiness":
        print(json.dumps(readiness(args.profile), indent=2, default=str))
    elif args.command == "roadmap":
        print(
            "1. Bootstrap and CI\n"
            "2. Architecture and parameter accounting\n"
            "3. Tokenizer and licensed data pipeline\n"
            "4. Shared training, checkpoint resume and monitoring\n"
            "5. Held-out evaluation and generation regression\n"
            "6. Tiny end-to-end smoke test\n"
            "7. Measured seed-0 training, then seed-1 and seed-2"
        )


if __name__ == "__main__":
    main()
