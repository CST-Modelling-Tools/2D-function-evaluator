#!/usr/bin/env python3
"""Generate contour, 3D surface, gallery, and animated GIF figures for benchmark functions.

This version uses:
- one shared colorbar in each combined contour + 3D frame
- one shared colorbar for the contour gallery
- improved spacing to avoid overlapping labels
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from functions_2d import FUNCTION_REGISTRY, get_bounds, get_function


DEFAULT_FUNCTIONS = sorted(FUNCTION_REGISTRY.keys())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate contour plots, 3D surface plots, combined frames, "
            "a contour gallery, and an optional animated GIF for benchmark functions."
        )
    )
    parser.add_argument(
        "--functions",
        nargs="+",
        default=DEFAULT_FUNCTIONS,
        help="Function names to plot. Default: all supported functions in alphabetical order.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Output directory for generated figures.",
    )
    parser.add_argument(
        "--grid",
        type=int,
        default=400,
        help="Grid resolution for evaluating each function.",
    )
    parser.add_argument(
        "--levels",
        type=int,
        default=60,
        help="Number of contour levels.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=180,
        help="Output DPI for PNG figures.",
    )
    parser.add_argument(
        "--gallery",
        action="store_true",
        help="Also generate a combined contour gallery image.",
    )
    parser.add_argument(
        "--animated-gif",
        action="store_true",
        help="Also generate an animated GIF with contour + 3D plots for each function.",
    )
    parser.add_argument(
        "--gif-duration",
        type=int,
        default=1400,
        help="Frame duration in milliseconds for the animated GIF.",
    )
    parser.add_argument(
        "--gif-loop",
        type=int,
        default=0,
        help="GIF loop count. Use 0 for infinite looping.",
    )
    return parser.parse_args()


def pretty_name(function_name: str) -> str:
    return function_name.replace("_", " ").title()


def make_surface(function_name: str, grid: int):
    fn = get_function(function_name)
    xmin, xmax, ymin, ymax = get_bounds(function_name)

    x = np.linspace(xmin, xmax, grid)
    y = np.linspace(ymin, ymax, grid)
    xx, yy = np.meshgrid(x, y)
    zz = fn(xx, yy)

    return xx, yy, zz, (xmin, xmax, ymin, ymax)


def save_contour(function_name: str, out_dir: Path, grid: int, levels: int, dpi: int) -> Path:
    xx, yy, zz, bounds = make_surface(function_name, grid)
    xmin, xmax, ymin, ymax = bounds

    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    contour = ax.contourf(xx, yy, zz, levels=levels, cmap="viridis")
    ax.contour(xx, yy, zz, levels=12, colors="white", linewidths=0.35, alpha=0.45)

    ax.set_title(f"{pretty_name(function_name)} - Contour")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")

    cbar = fig.colorbar(contour, ax=ax)
    cbar.set_label("objective")

    fig.tight_layout()
    out_path = out_dir / f"{function_name}_contour.png"
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_surface_3d(function_name: str, out_dir: Path, grid: int, dpi: int) -> Path:
    xx, yy, zz, bounds = make_surface(function_name, grid)
    xmin, xmax, ymin, ymax = bounds

    fig = plt.figure(figsize=(8.2, 6.4))
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(
        xx,
        yy,
        zz,
        cmap="viridis",
        linewidth=0,
        antialiased=True,
        rcount=min(grid, 200),
        ccount=min(grid, 200),
    )

    ax.set_title(f"{pretty_name(function_name)} - 3D Surface")
    ax.set_xlabel("x", labelpad=8)
    ax.set_ylabel("y", labelpad=8)
    ax.zaxis.set_rotate_label(False)
    ax.set_zlabel("objective", rotation=90, labelpad=10)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_box_aspect((1, 1, 0.7))
    ax.view_init(elev=30, azim=-135)

    cbar = fig.colorbar(surface, ax=ax, shrink=0.72, pad=0.08)
    cbar.set_label("objective")

    fig.tight_layout()
    out_path = out_dir / f"{function_name}_3d.png"
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _build_combined_figure(function_name: str, grid: int, levels: int):
    xx, yy, zz, bounds = make_surface(function_name, grid)
    xmin, xmax, ymin, ymax = bounds

    fig = plt.figure(figsize=(13.8, 5.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 0.05], wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    contour = ax1.contourf(xx, yy, zz, levels=levels, cmap="viridis")
    ax1.contour(xx, yy, zz, levels=12, colors="white", linewidths=0.35, alpha=0.45)
    ax1.set_title("Contour")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_xlim(xmin, xmax)
    ax1.set_ylim(ymin, ymax)
    ax1.set_aspect("equal", adjustable="box")

    ax2 = fig.add_subplot(gs[0, 1], projection="3d")
    surface = ax2.plot_surface(
        xx,
        yy,
        zz,
        cmap="viridis",
        linewidth=0,
        antialiased=True,
        rcount=min(grid, 200),
        ccount=min(grid, 200),
    )
    ax2.set_title("3D Surface")
    ax2.set_xlabel("x", labelpad=8)
    ax2.set_ylabel("y", labelpad=8)
    ax2.zaxis.set_rotate_label(False)
    ax2.set_zlabel("objective", rotation=90, labelpad=10)
    ax2.set_xlim(xmin, xmax)
    ax2.set_ylim(ymin, ymax)
    ax2.set_box_aspect((1, 1, 0.7))
    ax2.view_init(elev=30, azim=-135)

    cax = fig.add_subplot(gs[0, 2])
    cbar = fig.colorbar(surface, cax=cax)
    cbar.set_label("objective")

    fig.suptitle(pretty_name(function_name), fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    return fig


def save_combined_frame(function_name: str, out_dir: Path, grid: int, levels: int, dpi: int) -> Path:
    fig = _build_combined_figure(function_name, grid, levels)
    out_path = out_dir / f"{function_name}_frame.png"
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def figure_to_pil_image(fig, dpi: int) -> Image.Image:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    image = Image.open(buffer).convert("P", palette=Image.ADAPTIVE)
    buffer.close()
    return image


def save_gallery(functions: list[str], out_dir: Path, grid: int, levels: int, dpi: int) -> Path:
    n = len(functions)
    ncols = 2
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(11.5, 4.6 * nrows))
    axes = np.atleast_1d(axes).ravel()

    last_contour = None

    for ax, function_name in zip(axes, functions):
        xx, yy, zz, bounds = make_surface(function_name, grid)
        xmin, xmax, ymin, ymax = bounds

        last_contour = ax.contourf(xx, yy, zz, levels=levels, cmap="viridis")
        ax.contour(xx, yy, zz, levels=12, colors="white", linewidths=0.3, alpha=0.4)

        ax.set_title(pretty_name(function_name))
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal", adjustable="box")

    for ax in axes[len(functions):]:
        ax.axis("off")

    if last_contour is not None:
        cbar = fig.colorbar(
            last_contour,
            ax=axes.tolist(),
            fraction=0.025,
            pad=0.02,
        )
        cbar.set_label("objective")

    fig.suptitle("Benchmark Functions Included in the 2D Function Evaluator", fontsize=16)
    fig.tight_layout(rect=[0, 0, 0.96, 0.98])

    out_path = out_dir / "benchmark-gallery.png"
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_animated_gif(
    functions: list[str],
    out_dir: Path,
    grid: int,
    levels: int,
    dpi: int,
    duration_ms: int,
    loop: int,
) -> Path:
    ordered_functions = sorted(functions)
    frames: list[Image.Image] = []

    for function_name in ordered_functions:
        fig = _build_combined_figure(function_name, grid, levels)
        frame = figure_to_pil_image(fig, dpi=dpi)
        frames.append(frame)

    if not frames:
        raise ValueError("No frames available to build GIF.")

    out_path = out_dir / "benchmark-functions.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=loop,
        optimize=False,
        disposal=2,
    )
    return out_path


def main() -> int:
    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
    })

    args = parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    functions = sorted(args.functions)

    unknown = [name for name in functions if name not in FUNCTION_REGISTRY]
    if unknown:
        raise ValueError(f"Unknown functions: {', '.join(unknown)}")

    for function_name in functions:
        contour_path = save_contour(function_name, out_dir, args.grid, args.levels, args.dpi)
        surface_path = save_surface_3d(function_name, out_dir, args.grid, args.dpi)
        frame_path = save_combined_frame(function_name, out_dir, args.grid, args.levels, args.dpi)
        print(f"Saved {contour_path}")
        print(f"Saved {surface_path}")
        print(f"Saved {frame_path}")

    if args.gallery:
        gallery_path = save_gallery(functions, out_dir, args.grid, args.levels, args.dpi)
        print(f"Saved {gallery_path}")

    if args.animated_gif:
        gif_path = save_animated_gif(
            functions=functions,
            out_dir=out_dir,
            grid=args.grid,
            levels=args.levels,
            dpi=args.dpi,
            duration_ms=args.gif_duration,
            loop=args.gif_loop,
        )
        print(f"Saved {gif_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())