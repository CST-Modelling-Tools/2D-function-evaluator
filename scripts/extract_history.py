#!/usr/bin/env python3
"""Extract optimization history from run artifacts into a CSV file."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from output_paths import resolve_output_path


@dataclass
class EvalRow:
    eval_index: int
    x: float | None
    y: float | None
    objective: float | None
    function: str
    eval_dir: str
    status: str
    timestamp: str
    output_mtime: float
    generation: int | None = None
    individual: int | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract x/y/objective history from a run directory into CSV."
    )
    parser.add_argument("--run-dir", required=True, help="Path to run output directory.")
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV path (default: <run-dir>/history.csv).",
    )
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Search recursively for output files (default: true).",
    )
    parser.add_argument(
        "--input-name",
        default="input.json",
        help="Expected input filename inside eval folders (default: input.json).",
    )
    parser.add_argument(
        "--output-name",
        default="output.json",
        help="Expected output filename inside eval folders (default: output.json).",
    )
    parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fail on any invalid/missing entry (default: false).",
    )
    parser.add_argument(
        "--print-summary",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print parsing summary and best objective (default: true).",
    )
    parser.add_argument(
        "--pop-size",
        type=int,
        default=None,
        help="Optional population size for reconstructing generation/individual columns.",
    )
    return parser.parse_args(argv)


def safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"cannot read file: {exc}"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"
    if not isinstance(payload, dict):
        return None, "JSON root is not an object"
    return payload, None


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return number
    return None


def as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def extract_objective(output_payload: dict[str, Any]) -> float | None:
    direct = as_float(output_payload.get("objective"))
    if direct is not None:
        return direct

    metrics = output_payload.get("metrics")
    if isinstance(metrics, dict):
        metric_f = as_float(metrics.get("f"))
        if metric_f is not None:
            return metric_f

    return as_float(output_payload.get("value"))


def output_status(output_payload: dict[str, Any], objective: float | None) -> str:
    status = output_payload.get("status")
    if isinstance(status, str):
        return status

    success = output_payload.get("success")
    if isinstance(success, bool):
        return "ok" if success else "failed"

    if objective is not None:
        return "ok"
    return "unknown"


def is_success(output_payload: dict[str, Any], objective: float | None) -> bool:
    status = output_payload.get("status")
    if isinstance(status, str):
        return status.lower() == "ok"

    success = output_payload.get("success")
    if isinstance(success, bool):
        return success

    return objective is not None


def extract_inputs(input_payload: dict[str, Any] | None) -> tuple[float | None, float | None, str]:
    if not isinstance(input_payload, dict):
        return None, None, ""

    params = input_payload.get("params")
    if isinstance(params, dict):
        x = as_float(params.get("x"))
        y = as_float(params.get("y"))
        fn = as_str(params.get("function"))
        if x is not None or y is not None or fn:
            return x, y, fn

    return (
        as_float(input_payload.get("x")),
        as_float(input_payload.get("y")),
        as_str(input_payload.get("function")),
    )


def pick_timestamp(input_payload: dict[str, Any] | None, output_payload: dict[str, Any]) -> str:
    for payload in (output_payload, input_payload):
        if not isinstance(payload, dict):
            continue
        for key in ("timestamp", "time", "created_at", "evaluated_at", "finished_at"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return ""


def discover_output_files(run_dir: Path, output_name: str, recursive: bool) -> list[Path]:
    iterator = run_dir.rglob(output_name) if recursive else run_dir.glob(output_name)
    files = [p for p in iterator if p.is_file()]
    files.sort(key=lambda p: (p.stat().st_mtime_ns, str(p.relative_to(run_dir))))
    return files


def write_csv(rows: list[EvalRow], out_path: Path, include_generations: bool) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = [
            "eval_index",
            "x",
            "y",
            "objective",
            "function",
            "eval_dir",
            "status",
            "timestamp",
            "output_mtime",
        ]
        if include_generations:
            header.extend(["generation", "individual"])
        writer.writerow(header)
        for row in rows:
            values = [
                row.eval_index,
                "" if row.x is None else row.x,
                "" if row.y is None else row.y,
                "" if row.objective is None else row.objective,
                row.function,
                row.eval_dir,
                row.status,
                row.timestamp,
                row.output_mtime,
            ]
            if include_generations:
                values.extend(
                    [
                        "" if row.generation is None else row.generation,
                        "" if row.individual is None else row.individual,
                    ]
                )
            writer.writerow(values)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists() or not run_dir.is_dir():
        print(f"Error: --run-dir does not exist or is not a directory: {run_dir}", file=sys.stderr)
        return 2
    if args.pop_size is not None and args.pop_size < 1:
        print("Error: --pop-size must be >= 1", file=sys.stderr)
        return 2

    out_path = resolve_output_path(args.out, run_dir) if args.out else run_dir / "history.csv"

    output_files = discover_output_files(run_dir, args.output_name, args.recursive)
    rows: list[EvalRow] = []
    errors: list[str] = []
    skipped = 0

    for output_path in output_files:
        out_payload, out_err = safe_load_json(output_path)
        rel_dir = output_path.parent.relative_to(run_dir).as_posix()
        if out_payload is None:
            message = f"{rel_dir}: {args.output_name} {out_err}"
            if args.strict:
                errors.append(message)
            skipped += 1
            continue

        objective = extract_objective(out_payload)
        status = output_status(out_payload, objective)
        success = is_success(out_payload, objective)
        if not success:
            message = f"{rel_dir}: evaluation status is not successful ({status})"
            if args.strict:
                errors.append(message)
            skipped += 1
            continue

        input_path = output_path.parent / args.input_name
        in_payload: dict[str, Any] | None = None
        if input_path.exists():
            in_payload, in_err = safe_load_json(input_path)
            if in_payload is None:
                message = f"{rel_dir}: {args.input_name} {in_err}"
                if args.strict:
                    errors.append(message)
                    skipped += 1
                    continue
        elif args.strict:
            errors.append(f"{rel_dir}: missing {args.input_name}")
            skipped += 1
            continue

        x, y, fn = extract_inputs(in_payload)
        timestamp = pick_timestamp(in_payload, out_payload)
        rows.append(
            EvalRow(
                eval_index=0,
                x=x,
                y=y,
                objective=objective,
                function=fn,
                eval_dir=rel_dir,
                status=status,
                timestamp=timestamp,
                output_mtime=output_path.stat().st_mtime,
            )
        )

    if errors:
        print("Strict mode errors:", file=sys.stderr)
        for msg in errors[:20]:
            print(f"  - {msg}", file=sys.stderr)
        remaining = len(errors) - 20
        if remaining > 0:
            print(f"  ... and {remaining} more", file=sys.stderr)
        return 1

    for idx, row in enumerate(rows):
        row.eval_index = idx

    if args.pop_size is not None:
        for row in rows:
            if row.eval_index is None:
                continue
            row.generation = row.eval_index // args.pop_size
            row.individual = row.eval_index % args.pop_size

    write_csv(rows, out_path, include_generations=args.pop_size is not None)

    if args.print_summary:
        print(f"run_dir: {run_dir}")
        print(f"output_csv: {out_path}")
        print(f"total_output_files_found: {len(output_files)}")
        print(f"parsed_ok: {len(rows)}")
        print(f"skipped: {skipped}")
        if args.pop_size is not None:
            generations = 0
            if rows:
                known_generations = [row.generation for row in rows if row.generation is not None]
                if known_generations:
                    generations = max(known_generations) + 1
            print(f"pop_size: {args.pop_size}")
            print(f"generations: {generations}")

        with_objective = [r for r in rows if r.objective is not None]
        if with_objective:
            best = min(with_objective, key=lambda r: r.objective if r.objective is not None else float("inf"))
            print(
                "best: objective={:.12g}, x={}, y={}, eval_index={}, eval_dir={}".format(
                    best.objective if best.objective is not None else float("nan"),
                    "" if best.x is None else f"{best.x:.12g}",
                    "" if best.y is None else f"{best.y:.12g}",
                    best.eval_index,
                    best.eval_dir,
                )
            )
        else:
            print("best: unavailable (no numeric objective found)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
