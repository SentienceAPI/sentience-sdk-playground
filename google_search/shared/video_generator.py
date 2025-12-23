"""
Video generation with MoviePy 1.x
"""
from moviepy.editor import (
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    VideoFileClip,
    clips_array
)
import os
from typing import Dict, Any


def create_demo_video(screenshots_dir: str, token_summary: Dict[str, Any], output_path: str):
    """
    Create a video from screenshots with token usage overlay

    Args:
        screenshots_dir: Directory containing scene screenshots
        token_summary: Token tracking summary from TokenTracker
        output_path: Output video file path
    """
    print(f"\nCreating video from screenshots in {screenshots_dir}...")

    # Get all screenshots in order
    screenshot_files = sorted([
        f for f in os.listdir(screenshots_dir)
        if f.endswith('.png')
    ])

    if not screenshot_files:
        print(f"No screenshots found in {screenshots_dir}")
        return

    print(f"Found {len(screenshot_files)} screenshots")
    clips = []

    # Create clips for each scene (3 seconds per scene)
    for i, screenshot_file in enumerate(screenshot_files):
        img_path = os.path.join(screenshots_dir, screenshot_file)
        print(f"  Processing {screenshot_file}...")

        # Create image clip (3 seconds duration)
        img_clip = ImageClip(img_path, duration=3.0)

        # Extract scene info from filename
        scene_name = screenshot_file.replace('.png', '').replace('_', ' ').title()

        # Get token usage for this scene
        scene_tokens = 0
        for interaction in token_summary['interactions']:
            # Match scene number or name
            if f"scene {i+1}" in interaction['scene'].lower() or \
               scene_name.lower() in interaction['scene'].lower():
                scene_tokens = interaction['total']
                break

        # Create token overlay text
        if scene_tokens > 0:
            token_text = f"Tokens: {scene_tokens}"
        else:
            token_text = "No LLM call"

        # Create text clip for scene label (top)
        scene_label = TextClip(
            scene_name,
            fontsize=40,
            color='white',
            bg_color='black',
            size=(1920, 60),
            method='caption',
            align='West'
        ).set_position(('left', 'top')).set_duration(3.0)

        # Create text clip for token usage (top-right corner)
        token_label = TextClip(
            token_text,
            fontsize=36,
            color='yellow',
            bg_color='rgba(0,0,0,0.7)',
            size=(300, 50),
            method='caption',
            align='East'
        ).set_position((1600, 70)).set_duration(3.0)

        # Composite scene label + token label on image
        composite = CompositeVideoClip([img_clip, scene_label, token_label])
        clips.append(composite)

    # Create summary screen at the end (5 seconds)
    print("  Creating summary screen...")
    summary_text = f"""{token_summary['demo_name']}

Total Tokens: {token_summary['total_tokens']}
Prompt Tokens: {token_summary['total_prompt_tokens']}
Completion Tokens: {token_summary['total_completion_tokens']}

Average per Scene: {token_summary['average_per_scene']:.1f}"""

    summary_clip = TextClip(
        summary_text,
        fontsize=48,
        color='white',
        bg_color='black',
        size=(1920, 1080),
        method='caption',
        align='center'
    ).set_duration(5.0)

    clips.append(summary_clip)

    # Concatenate all clips
    print("  Concatenating clips...")
    final_video = concatenate_videoclips(clips, method="compose")

    # Write video file
    print(f"  Writing video to {output_path}...")
    final_video.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio=False,
        preset='medium'
    )

    print(f"\n✅ Video created: {output_path}")


def create_side_by_side_comparison(demo1_video: str, demo2_video: str, output_path: str):
    """
    Create side-by-side comparison video

    Args:
        demo1_video: Path to Demo 1 video (SDK)
        demo2_video: Path to Demo 2 video (Vision)
        output_path: Output comparison video path
    """
    print(f"\nCreating side-by-side comparison video...")

    # Load both videos
    print("  Loading videos...")
    clip1 = VideoFileClip(demo1_video)
    clip2 = VideoFileClip(demo2_video)

    # Resize to half width for side-by-side
    print("  Resizing clips...")
    clip1_resized = clip1.resize(width=960)
    clip2_resized = clip2.resize(width=960)

    # Create side-by-side layout
    print("  Creating side-by-side layout...")
    final_clip = clips_array([[clip1_resized, clip2_resized]])

    # Add title overlay
    title = TextClip(
        "SDK + LLM (Left) vs Vision + LLM (Right)",
        fontsize=50,
        color='white',
        bg_color='black',
        size=(1920, 80)
    ).set_position(('center', 'top')).set_duration(final_clip.duration)

    final_with_title = CompositeVideoClip([final_clip, title])

    # Write comparison video
    print(f"  Writing comparison video to {output_path}...")
    final_with_title.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio=False,
        preset='medium'
    )

    print(f"\n✅ Comparison video created: {output_path}")
