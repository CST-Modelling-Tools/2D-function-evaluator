"""Shared 2D objective functions and plotting bounds used by visualization scripts."""

from __future__ import annotations

from typing import Callable

import numpy as np

Bounds = tuple[float, float, float, float]
Function2D = Callable[[np.ndarray, np.ndarray], np.ndarray]


def sphere(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return (x * x) + (y * y)


def rosenbrock(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    a = 1.0 - x
    b = y - (x * x)
    return (a * a) + (100.0 * b * b)


def rastrigin(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return 20.0 + ((x * x) - 10.0 * np.cos(2.0 * np.pi * x)) + ((y * y) - 10.0 * np.cos(2.0 * np.pi * y))


def ackley(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    a = 20.0
    b = 0.2
    sum_sq = 0.5 * ((x * x) + (y * y))
    sum_cos = 0.5 * (np.cos(2.0 * np.pi * x) + np.cos(2.0 * np.pi * y))
    return -a * np.exp(-b * np.sqrt(sum_sq)) - np.exp(sum_cos) + a + np.exp(1.0)


def himmelblau(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    a = (x * x) + y - 11.0
    b = x + (y * y) - 7.0
    return (a * a) + (b * b)


def beale(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    t1 = 1.5 - x + x * y
    t2 = 2.25 - x + x * y * y
    t3 = 2.625 - x + x * y * y * y
    return (t1 * t1) + (t2 * t2) + (t3 * t3)


def goldstein_price(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    a = x + y + 1.0
    b = 19.0 - 14.0 * x + 3.0 * x * x - 14.0 * y + 6.0 * x * y + 3.0 * y * y
    c = 2.0 * x - 3.0 * y
    d = 18.0 - 32.0 * x + 12.0 * x * x + 48.0 * y - 36.0 * x * y + 27.0 * y * y
    return (1.0 + (a * a) * b) * (30.0 + (c * c) * d)


def mccormick(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.sin(x + y) + (x - y) * (x - y) - 1.5 * x + 2.5 * y + 1.0


# Keep the plotting scripts aligned with the evaluator's function registry.
BOUNDS_BY_FUNCTION: dict[str, Bounds] = {
    "sphere": (-5.0, 5.0, -5.0, 5.0),
    "rosenbrock": (-2.0, 2.0, -1.0, 3.0),
    "rastrigin": (-5.12, 5.12, -5.12, 5.12),
    "ackley": (-5.0, 5.0, -5.0, 5.0),
    "himmelblau": (-6.0, 6.0, -6.0, 6.0),
    "beale": (-4.5, 4.5, -4.5, 4.5),
    "goldstein_price": (-2.0, 2.0, -2.0, 2.0),
    "mccormick": (-1.5, 4.0, -3.0, 4.0),
}

FUNCTION_REGISTRY: dict[str, Function2D] = {
    "sphere": sphere,
    "rosenbrock": rosenbrock,
    "rastrigin": rastrigin,
    "ackley": ackley,
    "himmelblau": himmelblau,
    "beale": beale,
    "goldstein_price": goldstein_price,
    "mccormick": mccormick,
}


def _supported_names() -> str:
    return ", ".join(sorted(FUNCTION_REGISTRY))


def get_function(name: str) -> Function2D:
    try:
        return FUNCTION_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown function '{name}'. Supported functions: {_supported_names()}") from exc


def get_bounds(name: str) -> Bounds:
    try:
        return BOUNDS_BY_FUNCTION[name]
    except KeyError as exc:
        raise ValueError(f"Unknown function '{name}'. Supported functions: {_supported_names()}") from exc


def infer_bounds_from_points(
    xs: np.ndarray | list[float],
    ys: np.ndarray | list[float],
    padding_ratio: float = 0.1,
) -> Bounds:
    x_arr = np.asarray(xs, dtype=float)
    y_arr = np.asarray(ys, dtype=float)
    if x_arr.size == 0 or y_arr.size == 0:
        raise ValueError("Cannot infer bounds from history: missing x/y values.")

    xmin = float(np.min(x_arr))
    xmax = float(np.max(x_arr))
    ymin = float(np.min(y_arr))
    ymax = float(np.max(y_arr))
    dx = max(1e-6, xmax - xmin)
    dy = max(1e-6, ymax - ymin)
    return (
        xmin - padding_ratio * dx,
        xmax + padding_ratio * dx,
        ymin - padding_ratio * dy,
        ymax + padding_ratio * dy,
    )
