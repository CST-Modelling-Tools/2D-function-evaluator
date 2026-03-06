$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir "..\.venv\Scripts\python.exe"
$vizScript = Join-Path $scriptDir "viz.py"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Expected Python interpreter not found at '$pythonExe'. Create the evaluator virtual environment first, or update the launcher path."
    exit 1
}

& $pythonExe $vizScript @args
exit $LASTEXITCODE
