#!/bin/bash
# Quick start script for Local LLM demo
# Auto-downloads Qwen 2.5 3B model on first run

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "========================================================================"
echo "  Local LLM Demo - Google Search with Qwen 2.5 3B"
echo "========================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "demos/google_search.py" ]; then
    echo -e "${RED}❌ Error: demos/google_search.py not found${NC}"
    echo "Please run this script from the local_llm directory"
    exit 1
fi

# Step 1: Check disk space
echo -e "${BLUE}Step 1: Checking disk space...${NC}"
available_space=$(df -h . | tail -1 | awk '{print $4}')
echo "Available space: $available_space"
echo ""

# Check if we have at least 6GB free (rough check)
if command -v python3 &> /dev/null; then
    python3 check_cache_sizes.py 2>/dev/null || true
    echo ""
fi

read -p "Continue? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Cancelled by user"
    exit 0
fi

# Step 2: Check if dependencies are installed
echo ""
echo -e "${BLUE}Step 2: Checking dependencies...${NC}"

if ! python3 -c "import transformers" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies not installed${NC}"
    echo ""
    read -p "Install dependencies now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "Installing dependencies..."
        pip3 install -r requirements.txt
        echo -e "${GREEN}✅ Dependencies installed${NC}"
    else
        echo -e "${RED}❌ Cannot run without dependencies${NC}"
        echo "Install manually: pip3 install -r requirements.txt"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Step 3: Check if model is cached
echo ""
echo -e "${BLUE}Step 3: Checking for cached model...${NC}"

model_cache="$HOME/.cache/huggingface/hub"
if [ -d "$model_cache" ] && [ "$(ls -A $model_cache)" ]; then
    echo -e "${GREEN}✅ Hugging Face cache found${NC}"
    echo "Location: $model_cache"
    cache_size=$(du -sh "$model_cache" 2>/dev/null | cut -f1)
    echo "Size: $cache_size"
else
    echo -e "${YELLOW}⚠️  Model not cached - will download on first run${NC}"
    echo "Download size: ~6 GB (Qwen 2.5 3B)"
    echo "Download time: 5-15 minutes (one-time only)"
    echo ""
    read -p "Continue with download? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Cancelled by user"
        exit 0
    fi
fi

# Step 4: Run the demo
echo ""
echo -e "${BLUE}Step 4: Running demo...${NC}"
echo "========================================================================"
echo ""

# Check for virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the demo
python3 demos/google_search.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo -e "${GREEN}✅ Demo completed successfully!${NC}"
    echo "========================================================================"
    echo ""
    echo "Output location:"
    ls -td google_search_*/screenshots/*/ 2>/dev/null | head -1 | xargs -I {} echo "  {}"
    echo ""
    echo "To run again: ./run_demo.sh"
    echo "To compare models: python3 compare_models.py"
else
    echo ""
    echo "========================================================================"
    echo -e "${RED}❌ Demo failed${NC}"
    echo "========================================================================"
    echo ""
    echo "Common issues:"
    echo "  1. Not enough disk space - Run: python3 check_cache_sizes.py"
    echo "  2. Missing dependencies - Run: pip3 install -r requirements.txt"
    echo "  3. GPU out of memory - Edit demos/google_search.py and set load_in_4bit=True"
    echo ""
    exit 1
fi
