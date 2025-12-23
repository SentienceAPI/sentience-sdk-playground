#!/bin/bash

# Run Demo 2: Vision + LLM for Google Search

cd "$(dirname "$0")"

echo "======================================================================"
echo "Running Demo 2: Vision + LLM - Google Search"
echo "======================================================================"

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run the demo
python demo2_vision/main.py

echo ""
echo "======================================================================"
echo "Demo 2 finished. Check demo2_vision/screenshots/ for results."
echo "======================================================================"
