#!/usr/bin/env python3
"""Unified CLI wrapper for optional visualization scripts."""

from __future__ import annotations

import argparse

import animate_generations
import extract_history
import plot_convergence
import plot_generation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified wrapper for visualization utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands: list[tuple[str, str, callable]] = [
        ("extract", "Extract history CSV from run artifacts.", extract_history.main),
        ("convergence", "Plot best/median/worst objective by generation.", plot_convergence.main),
        ("gen", "Plot one population snapshot for a selected generation.", plot_generation.main),
        ("animate", "Animate evolutionary populations across generations.", animate_generations.main),
    ]

    for name, help_text, func in commands:
        subparser = subparsers.add_parser(name, help=help_text)
        subparser.set_defaults(func=func)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, forwarded = parser.parse_known_args(argv)
    return int(args.func(forwarded))


if __name__ == "__main__":
    raise SystemExit(main())
