"""Scheduled retraining command for policy artifacts."""

from __future__ import annotations

import argparse
import time
from typing import Sequence

from src.core.persistence.storage import Storage
from src.core.training.policy_registry import PolicyRegistry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run recurring policy retraining jobs")
    parser.add_argument("--data-dir", default="data", help="Data directory containing telemetry and models")
    parser.add_argument("--interval-seconds", type=int, default=3600, help="Seconds between retraining runs")
    parser.add_argument("--once", action="store_true", help="Run one training cycle and exit")
    return parser


def run_scheduler(data_dir: str, interval_seconds: int, once: bool) -> int:
    storage = Storage(data_dir)
    registry = PolicyRegistry(storage)

    while True:
        try:
            result = registry.train_latest()
            print(
                "trained",
                result["model_id"],
                f"samples={result['sample_count']}",
                f"at={result['trained_at_utc']}",
            )
        except ValueError as exc:
            if str(exc) != "no_policy_samples":
                raise
            print("skipped no_policy_samples")

        if once:
            return 0
        time.sleep(interval_seconds)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return run_scheduler(
        data_dir=args.data_dir,
        interval_seconds=args.interval_seconds,
        once=args.once,
    )


if __name__ == "__main__":
    raise SystemExit(main())
