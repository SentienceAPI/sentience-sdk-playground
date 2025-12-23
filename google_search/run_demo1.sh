#!/bin/bash

# Run Demo 1: SDK + LLM for Google Search

cd "$(dirname "$0")"

echo "======================================================================"
echo "Running Demo 1: SDK + LLM - Google Search"
echo "======================================================================"

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run the demo
python demo1_sdk/main.py

echo ""
echo "======================================================================"
echo "Demo 1 finished. Check demo1_sdk/screenshots/ for results."
echo "======================================================================"
