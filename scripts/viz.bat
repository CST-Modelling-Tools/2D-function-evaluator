@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
set "VIZ_PY=%SCRIPT_DIR%viz.py"

if not exist "%PYTHON_EXE%" (
    echo Error: expected Python interpreter not found at "%PYTHON_EXE%".
    echo Create the evaluator virtual environment first, or update the launcher path.
    exit /b 1
)

"%PYTHON_EXE%" "%VIZ_PY%" %*
