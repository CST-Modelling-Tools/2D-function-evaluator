"""Helpers for resolving visualization outputs relative to user data locations."""

from __future__ import annotations

from pathlib import Path


def resolve_output_path(output: str | None, base_dir: Path) -> Path | None:
    """Resolve relative output paths against the user-facing data directory."""
    if output is None:
        return None

    out_path = Path(output)
    if out_path.is_absolute():
        return out_path
    return (base_dir / out_path).resolve()
