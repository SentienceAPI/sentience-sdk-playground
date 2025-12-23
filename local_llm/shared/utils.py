"""
Shared utilities for local LLM demos
Handles screenshots, videos, and timestamp-based organization
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class TimestampedFolder:
    """Manage timestamped output folders for organizing demo runs"""

    def __init__(self, base_dir: str, demo_name: str):
        """
        Initialize timestamped folder manager

        Args:
            base_dir: Base directory for outputs
            demo_name: Name of the demo (e.g., "google_search")
        """
        self.base_dir = Path(base_dir)
        self.demo_name = demo_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = self.base_dir / demo_name / "screenshots" / self.timestamp

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / demo_name / "video").mkdir(parents=True, exist_ok=True)

        print(f"📁 Created output directory: {self.output_dir}")

    def get_screenshot_path(self, scene_name: str, suffix: str = "") -> str:
        """
        Get path for a screenshot

        Args:
            scene_name: Name of the scene (e.g., "scene1_homepage")
            suffix: Optional suffix (e.g., "_annotated")

        Returns:
            Full path to screenshot file
        """
        filename = f"{scene_name}{suffix}.png"
        return str(self.output_dir / filename)

    def get_data_path(self, scene_name: str) -> str:
        """Get path for saving scene data (JSON)"""
        filename = f"{scene_name}_data.json"
        return str(self.output_dir / filename)

    def get_video_path(self, video_name: str = "final") -> str:
        """Get path for video output"""
        video_dir = self.base_dir / self.demo_name / "video"
        return str(video_dir / f"{video_name}_{self.timestamp}.mp4")

    def save_json(self, data: Dict[str, Any], scene_name: str):
        """Save JSON data for a scene"""
        path = self.get_data_path(scene_name)
        with open(path, 'w') as f:
            json.dump(data, indent=2, fp=f)
        print(f"💾 Saved data: {path}")

    def list_screenshots(self) -> list[str]:
        """List all screenshots in chronological order"""
        screenshots = sorted(
            [str(p) for p in self.output_dir.glob("*.png") if not p.name.endswith("_annotated.png")]
        )
        return screenshots


class ScreenshotManager:
    """Manage screenshot capture and saving"""

    @staticmethod
    def capture_and_save(
        browser,
        output_path: str,
        full_page: bool = False
    ) -> str:
        """
        Capture screenshot and save to path

        Args:
            browser: Sentience browser or Playwright page
            output_path: Path to save screenshot
            full_page: Whether to capture full page

        Returns:
            Path to saved screenshot
        """
        # Handle both Sentience browser and Playwright page
        if hasattr(browser, 'page'):
            page = browser.page
        else:
            page = browser

        page.screenshot(path=output_path, full_page=full_page)
        print(f"📸 Screenshot saved: {output_path}")
        return output_path

    @staticmethod
    def capture_with_highlight(
        browser,
        output_path: str,
        bbox: Optional[Dict[str, float]] = None,
        color: str = "red",
        width: int = 4
    ) -> str:
        """
        Capture screenshot with highlighted element

        Args:
            browser: Browser instance
            output_path: Path to save screenshot
            bbox: Bounding box to highlight {x, y, width, height}
            color: Highlight color
            width: Border width

        Returns:
            Path to saved screenshot
        """
        if bbox:
            # Inject highlight via JavaScript
            if hasattr(browser, 'page'):
                page = browser.page
            else:
                page = browser

            page.evaluate(f"""
                (bbox) => {{
                    const div = document.createElement('div');
                    div.style.position = 'absolute';
                    div.style.left = bbox.x + 'px';
                    div.style.top = bbox.y + 'px';
                    div.style.width = bbox.width + 'px';
                    div.style.height = bbox.height + 'px';
                    div.style.border = '{width}px solid {color}';
                    div.style.pointerEvents = 'none';
                    div.style.zIndex = '99999';
                    div.id = 'sentience-highlight';
                    document.body.appendChild(div);
                }}
            """, bbox)

        # Take screenshot
        path = ScreenshotManager.capture_and_save(browser, output_path)

        # Remove highlight
        if bbox:
            if hasattr(browser, 'page'):
                page = browser.page
            else:
                page = browser

            page.evaluate("""
                () => {
                    const highlight = document.getElementById('sentience-highlight');
                    if (highlight) highlight.remove();
                }
            """)

        return path


class TokenTracker:
    """Track token usage across LLM calls"""

    def __init__(self, demo_name: str):
        """
        Initialize token tracker

        Args:
            demo_name: Name of the demo
        """
        self.demo_name = demo_name
        self.interactions = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0

    def log_interaction(
        self,
        scene: str,
        prompt_tokens: int,
        completion_tokens: int,
        model_name: str = "unknown"
    ):
        """
        Log a single LLM interaction

        Args:
            scene: Scene identifier
            prompt_tokens: Input tokens used
            completion_tokens: Output tokens generated
            model_name: Name of the model used
        """
        total = prompt_tokens + completion_tokens

        self.interactions.append({
            "scene": scene,
            "model": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total": total
        })

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total

        print(f"📊 {scene}: {total} tokens (prompt: {prompt_tokens}, completion: {completion_tokens})")

    def get_summary(self) -> Dict[str, Any]:
        """Get complete token usage summary"""
        return {
            "demo_name": self.demo_name,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "interactions": self.interactions,
            "num_interactions": len(self.interactions),
            "average_per_scene": self.total_tokens / len(self.interactions) if self.interactions else 0
        }

    def print_summary(self):
        """Print formatted summary to console"""
        summary = self.get_summary()

        print(f"\n{'='*70}")
        print(f"Token Usage Summary: {summary['demo_name']}")
        print(f"{'='*70}")

        for interaction in summary['interactions']:
            model_info = f" ({interaction['model']})" if interaction['model'] != "unknown" else ""
            print(f"{interaction['scene']:35} {interaction['total']:8} tokens{model_info}")

        print(f"{'='*70}")
        print(f"{'Total Prompt Tokens:':35} {summary['total_prompt_tokens']:8}")
        print(f"{'Total Completion Tokens:':35} {summary['total_completion_tokens']:8}")
        print(f"{'TOTAL TOKENS:':35} {summary['total_tokens']:8}")
        print(f"{'Average per Scene:':35} {summary['average_per_scene']:8.1f}")
        print(f"{'='*70}\n")

    def save_to_file(self, output_path: str):
        """Save token usage summary to JSON file"""
        summary = self.get_summary()
        with open(output_path, 'w') as f:
            json.dump(summary, fp=f, indent=2)
        print(f"💾 Token summary saved: {output_path}")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count

    Args:
        text: Input text

    Returns:
        Estimated token count (rough approximation)
    """
    # Rough heuristic: ~4 characters per token
    return len(text) // 4
