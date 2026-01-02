#!/bin/bash
# Script to run veille_tech with virtual environment

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating it..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the main script with all arguments passed through
python main.py "$@"
