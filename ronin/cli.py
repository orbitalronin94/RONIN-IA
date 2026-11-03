"""Command-line entry point for RONIN-IA."""

from __future__ import annotations

import argparse
import json

from ronin.config import PROFILES, profile_dict
from ronin.models.transformer import RoninLM


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ronin", description="RONIN from-scratch LM toolkit")
    sub = parser.add_subparsers(dest="command", required=True)
    info = sub.add_parser("info", help="show validated profile configuration")
    info.add_argument("--profile", choices=sorted(PROFILES), default="tiny")
    count = sub.add_parser("count-params", help="calculate model parameters from architecture")
    count.add_argument("--profile", choices=sorted(PROFILES), default="tiny")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "info":
        print(json.dumps(profile_dict(args.profile), indent=2))
    elif args.command == "count-params":
        model_config, _ = PROFILES[args.profile]
        model = RoninLM(model_config)
        print(f"{args.profile}: {model.parameter_count:,} trainable parameters")


if __name__ == "__main__":
    main()
