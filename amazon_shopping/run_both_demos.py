"""
Master script to run both demos and create comparison video
"""
import os
import sys
import subprocess

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from video_generator import create_side_by_side_comparison


def run_demo(demo_name: str, demo_path: str):
    """Run a demo script"""
    print("\n" + "="*70)
    print(f"Running {demo_name}...")
    print("="*70)

    try:
        result = subprocess.run(
            [sys.executable, os.path.join(demo_path, "main.py")],
            cwd=demo_path,
            check=True
        )
        print(f"\n✅ {demo_name} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {demo_name} failed with error: {e}")
        return False


def main():
    print("\n" + "="*80)
    print(" "*20 + "AMAZON SHOPPING DEMO - COMPARISON")
    print("="*80)
    print("\nThis script will:")
    print("1. Run Demo 1 (SDK + LLM)")
    print("2. Run Demo 2 (Vision + LLM)")
    print("3. Generate side-by-side comparison video")
    print("\n" + "="*80)

    input("\nPress Enter to start Demo 1 (SDK + LLM)...")

    # Run Demo 1
    demo1_success = run_demo(
        "Demo 1 (SDK + LLM)",
        os.path.join(os.path.dirname(__file__), "demo1_sdk_llm")
    )

    if not demo1_success:
        print("\n⚠️ Demo 1 failed. Continuing to Demo 2...")

    input("\nPress Enter to start Demo 2 (Vision + LLM)...")

    # Run Demo 2
    demo2_success = run_demo(
        "Demo 2 (Vision + LLM)",
        os.path.join(os.path.dirname(__file__), "demo2_vision_llm")
    )

    if not demo2_success:
        print("\n⚠️ Demo 2 failed.")

    # Generate comparison video if both demos have videos
    demo1_video = os.path.join(os.path.dirname(__file__), "demo1_sdk_llm", "video", "demo1_sdk_final.mp4")
    demo2_video = os.path.join(os.path.dirname(__file__), "demo2_vision_llm", "video", "demo2_vision_final.mp4")

    if os.path.exists(demo1_video) and os.path.exists(demo2_video):
        print("\n" + "="*80)
        print("Generating side-by-side comparison video...")
        print("="*80)

        comparison_output = os.path.join(os.path.dirname(__file__), "comparison_video.mp4")

        try:
            create_side_by_side_comparison(demo1_video, demo2_video, comparison_output)
            print(f"\n✅ Comparison video created: {comparison_output}")
        except Exception as e:
            print(f"\n⚠️ Comparison video generation failed: {e}")
    else:
        print("\n⚠️ Cannot create comparison video - one or both demo videos are missing")

    # Print summary
    print("\n" + "="*80)
    print(" "*30 + "SUMMARY")
    print("="*80)
    print(f"Demo 1 (SDK + LLM):    {'✅ Success' if demo1_success else '❌ Failed'}")
    print(f"Demo 2 (Vision + LLM): {'✅ Success' if demo2_success else '❌ Failed'}")

    if os.path.exists(demo1_video):
        print(f"\nDemo 1 video: {demo1_video}")
    if os.path.exists(demo2_video):
        print(f"Demo 2 video: {demo2_video}")
    if os.path.exists(comparison_output):
        print(f"Comparison video: {comparison_output}")

    print("\n" + "="*80)
    print("ALL DEMOS COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
