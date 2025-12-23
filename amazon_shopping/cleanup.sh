#!/bin/bash
# Clean up screenshots and videos from previous demo runs

echo "Cleaning up old demo outputs..."

# Demo 1 cleanup
if [ -d "demo1_sdk_llm/screenshots" ]; then
    echo "  Removing Demo 1 screenshots..."
    rm -rf demo1_sdk_llm/screenshots/*
fi

if [ -d "demo1_sdk_llm/video" ]; then
    echo "  Removing Demo 1 videos..."
    rm -rf demo1_sdk_llm/video/*
fi

# Demo 2 cleanup
if [ -d "demo2_vision_llm/screenshots" ]; then
    echo "  Removing Demo 2 screenshots..."
    rm -rf demo2_vision_llm/screenshots/*
fi

if [ -d "demo2_vision_llm/video" ]; then
    echo "  Removing Demo 2 videos..."
    rm -rf demo2_vision_llm/video/*
fi

# Comparison video cleanup
if [ -f "comparison_video.mp4" ]; then
    echo "  Removing comparison video..."
    rm comparison_video.mp4
fi

echo "✅ Cleanup complete! Ready for fresh demo run."
echo ""
echo "Run your demos with:"
echo "  ./run_demo1.sh"
echo "  ./run_demo2.sh"
echo "  ./run_both.sh"
