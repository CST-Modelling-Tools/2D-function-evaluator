# Visualization Tooling (Optional)

This repository keeps the C++ evaluator focused on fast JSON-in/JSON-out execution.  
Visualization is provided as separate, opt-in Python scripts under `scripts/`.

`viz.py` provides a single wrapper CLI for the most common workflows while keeping the standalone scripts available.
On Windows, `viz.bat` and `viz.ps1` are convenience launchers that automatically use the evaluator repository's `.venv` Python.

Relative `--out` paths are resolved against the user data location, not the evaluator repository:

- `extract_history.py`: relative outputs go under `--run-dir`
- plotting/animation scripts: relative outputs go next to the provided `--history` file

## What These Scripts Do

- `extract_history.py`: scans a run folder, discovers evaluation artifacts, and writes a single `history.csv`.
- `plot_trajectory.py`: draws a 2D contour of a selected function and overlays the optimization path.
- `animate_trajectory.py`: creates a trajectory animation (`.gif` or `.mp4`) over the contour map.

The scripts are best-effort across slightly different run folder/file schemas and do not require FireWorks DB access.

## Install Python Dependencies (Recommended in a venv)

PowerShell:

```powershell
python -m venv .venv-vis
.venv-vis\Scripts\Activate.ps1
pip install -r scripts/requirements.txt
```

`pillow` is included in `scripts/requirements.txt` and is required for GIF output from `animate_trajectory.py`.

## Typical Workflow

1. Run optimization with GOW (normal evaluator usage).
2. Extract history from run artifacts:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat extract --run-dir . --out history.csv --pop-size 100
```

When run from the optimization repository, this writes `history.csv` into that repository. The same relative-output behavior also works if you invoke the evaluator scripts from another working directory.

PowerShell launcher:

```powershell
& "D:\OpenSource\2D-function-evaluator\scripts\viz.ps1" extract --run-dir . --out history.csv --pop-size 100
```

Standalone:

```powershell
"D:\OpenSource\2D-function-evaluator\.venv\Scripts\python.exe" "D:\OpenSource\2D-function-evaluator\scripts\extract_history.py" --run-dir . --out history.csv --pop-size 100
```

3. Generate static trajectory plot:

```powershell
"D:\OpenSource\2D-function-evaluator\.venv\Scripts\python.exe" "D:\OpenSource\2D-function-evaluator\scripts\plot_trajectory.py" --history .\history.csv --out trajectory.png
```

4. Generate animation:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat animate --history .\history.csv --out de.gif
```

The 2D generation animation keeps its generation label and legend in fixed positions across frames for a more stable GIF.

## Evolutionary Convergence

Use `plot_convergence.py` to visualize per-generation objective statistics for evolutionary runs. It plots `best`, `median`, and `worst`, and can also overlay `best-so-far`.

If your `history.csv` already contains a `generation` column, the script uses it directly. Otherwise, provide `--pop-size` so generations can be reconstructed from `eval_index`.

Example:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat convergence --history history.csv --pop-size 100 --out convergence.png
```

Standalone:

```powershell
python scripts/plot_convergence.py --history history.csv --pop-size 100 --out convergence.png
```

## Population Diversity

Use `plot_diversity.py` to track how the population spread changes over generations. This matters for evolutionary algorithms because a gradual decrease usually indicates healthy convergence, while a sudden collapse in diversity combined with stagnant objective values often signals premature convergence.

The script can plot `std_x`, `std_y`, `spread`, and `ellipse_area` by generation. If your `history.csv` already contains a `generation` column, it uses it directly. Otherwise, provide `--pop-size` so generations can be reconstructed from `eval_index`.

Example:

```powershell
python scripts/plot_diversity.py --history history.csv --pop-size 100 --out diversity.png
```

Wrapper:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat diversity --history history.csv --pop-size 100 --out diversity.png
```

Interpretation:

- A steady decline in diversity with improving objective values usually means the search is narrowing productively.
- A sharp diversity collapse while convergence metrics flatten often means the population has clustered too early.
- Persistently high diversity late in the run can indicate weak exploitation or an overly exploratory configuration.

## Population Snapshot

Use `plot_generation.py` to inspect the population cloud for one generation over the objective contour. It colors points by objective value, highlights the top-ranked individuals for that generation, and can mark the best point seen up to that generation.

If your `history.csv` already contains a `generation` column, the script uses it directly. Otherwise, provide `--pop-size` so generations can be reconstructed from `eval_index`.

Example:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat gen --history history.csv --pop-size 100 --gen 20 --out gen20.png
```

Standalone:

```powershell
python scripts/plot_generation.py --history history.csv --pop-size 100 --gen 20 --out gen20.png
```

## Animation (Generations)

Use `animate_generations.py` to animate the population generation by generation over the objective contour. This is the most useful view for understanding how an evolutionary optimizer moves and contracts over time.

If your `history.csv` already contains a `generation` column, the script uses it directly. Otherwise, provide `--pop-size` so generations can be reconstructed from `eval_index`.

Example:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat animate --history history.csv --pop-size 100 --out de.gif
```

Standalone:

```powershell
python scripts/animate_generations.py --history history.csv --pop-size 100 --out de.gif
```

Use `.gif` output for the most portable workflow. `.mp4` output requires `ffmpeg` installed and discoverable by matplotlib; otherwise, use GIF instead.

## Animation (Generations, 3D)

Use `animate_generations_3d.py` to animate the population over the full 3D objective surface, with each individual shown at `(x, y, objective)`. This is heavier than the 2D view, but it is useful when you want to see how the population sits on the landscape itself.

Example:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat animate3d --history history.csv --pop-size 100 --out de3d.gif
```

Standalone:

```powershell
"D:\OpenSource\2D-function-evaluator\.venv\Scripts\python.exe" "D:\OpenSource\2D-function-evaluator\scripts\animate_generations_3d.py" --history history.csv --pop-size 100 --out de3d.gif
```

## Animation (Dashboard)

Use `animate_generations_dashboard.py` to generate a synchronized dashboard GIF with three panels:

- 3D population over the objective surface
- convergence curves
- diversity curves

This is the most informative single animation when you want population motion, objective progress, and spread collapse in one place.

Example:

```powershell
D:\OpenSource\2D-function-evaluator\scripts\viz.bat dashboard --history history.csv --pop-size 100 --out dashboard.gif
```

Standalone:

```powershell
"D:\OpenSource\2D-function-evaluator\.venv\Scripts\python.exe" "D:\OpenSource\2D-function-evaluator\scripts\animate_generations_dashboard.py" --history history.csv --pop-size 100 --out dashboard.gif
```

## History Extraction Notes

`extract_history.py` discovers all `output.json` files (recursively by default), and tries to pair each with `input.json` in the same directory.

Recognized output objective fields:

- `objective`
- `metrics.f`
- `value`

Recognized output success markers:

- `status == "ok"`
- `success == true`

Recognized input parameter fields:

- `params.x`, `params.y`, `params.function`
- or `x`, `y`, `function`

Minimum CSV columns:

- `eval_index`
- `x`
- `y`
- `objective`
- `function`
- `eval_dir`
- `status`

Extra columns are included when available (`timestamp`, output file mtime).

## Bounds Selection

For plotting and animation, bounds are chosen in this order:

1. `--bounds xmin xmax ymin ymax` (explicit override)
2. Built-in recommended bounds for known evaluator functions:
   - `sphere`
   - `rosenbrock`
   - `rastrigin`
   - `ackley`
   - `himmelblau`
   - `beale`
   - `goldstein_price`
   - `mccormick`
3. If function is unknown: inferred from observed `x/y` in history with small padding.

## Troubleshooting

- Missing `output.json`: ensure `--output-name` matches your run artifacts.
- Missing/invalid `input.json`: extraction still keeps objective rows (x/y may be empty). Use `--strict` to fail instead.
- Unknown schema: use defaults first, then set `--input-name` / `--output-name` to your filenames.
- Unknown function in plotting: pass `--function NAME` explicitly.
- GIF export requires `pillow`; installing `scripts/requirements.txt` provides it.
- MP4 export requires `ffmpeg` installed and discoverable by matplotlib; otherwise use GIF output instead.
