@echo off
setlocal

echo --- ModuBot Windows Starter ---

set "script_dir=%~dp0"
set "VENV_DIR=%script_dir%Windows"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment not found. Creating one...
    python -m venv "%VENV_DIR%"
    echo Virtual environment created at %VENV_DIR%
)

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo Installing/updating required packages from requirements.txt...
pip install -r "%script_dir%requirements.txt"
echo Packages are up to date.

cd /d "%script_dir%"

echo Starting ModuBot...
python app.py

echo ModuBot stopped. Deactivating...
call deactivate

endlocal
pause