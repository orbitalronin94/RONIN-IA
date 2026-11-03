#!/usr/bin/env python3
"""Generate a JSONL corpus using an external tutor API; never import teacher weights."""

from __future__ import annotations

import argparse
from pathlib import Path

from ronin.data.prompts import build_prompts
from ronin.data.teacher import TeacherConfig, write_teacher_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--output", type=Path, default=Path("artifacts/teacher/train.jsonl"))
    parser.add_argument(
        "--confirm-training-rights",
        action="store_true",
        help="confirm you reviewed provider and model terms for generated-data training",
    )
    args = parser.parse_args()
    config = TeacherConfig.from_env()
    written = write_teacher_dataset(
        build_prompts(args.count),
        args.output,
        config,
        confirm_training_rights=args.confirm_training_rights,
    )
    print(f"Generated {written} teacher examples at {args.output}")


if __name__ == "__main__":
    main()
