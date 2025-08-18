#!/bin/bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$script_dir/Linux"

echo "--- ModuBot Linux Starter ---"

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "Virtual environment activated."

echo "Installing/updating required packages from requirements.txt..."
pip install -r "$script_dir/requirements.txt"
echo "Packages are up to date."

cd "$script_dir"

echo "Starting ModuBot..."
python3 app.py

deactivate
echo "ModuBot stopped. Virtual environment deactivated."