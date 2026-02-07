#!/bin/bash
# Startup script for Valentine's Candy Machine

cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the backend server
echo "Starting Valentine's Candy Machine..."
python backend/main.py
