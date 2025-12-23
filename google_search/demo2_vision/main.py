"""
Demo 2: GPT-4o Vision + Playwright for Google Search

Simple test:
1. Navigate to Google
2. Search for "visiting japan"
3. Click a non-ad result
"""
import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from vision_agent import VisionAgent
from token_tracker import TokenTracker


def main():
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY not found in .env file")
        return

    # Initialize tracker and agent
    tracker = TokenTracker("Google Search Demo 2: Vision + LLM")
    agent = VisionAgent(api_key=openai_api_key, tracker=tracker)

    # Screenshot directory with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
    screenshots_dir = os.path.join(base_screenshots_dir, timestamp)
    os.makedirs(screenshots_dir, exist_ok=True)
    print(f"Screenshots will be saved to: {screenshots_dir}")

    print("\n" + "="*70)
    print("DEMO 2: GPT-4o Vision + Playwright - Google Search")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # =================================================================
        # SCENE 1: Navigate to Google & Find Search Box
        # =================================================================
        print("\n[Scene 1] Navigating to Google.com...")
        page.goto("https://www.google.com")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene1_google_home.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        # Ask Vision LLM to find search box
        prompt = """You are a UI testing assistant analyzing a screenshot for automated testing purposes.

Current Task: Identify the search input field on the Google homepage.

Instructions:
1. Analyze the provided screenshot
2. Locate the main search input field (usually center of the page)
3. Identify the center coordinates (x, y) of the search input
4. Provide precise pixel coordinates based on a 1920x1080 viewport

Response Format (JSON only):
{
  "reasoning": "brief explanation of how you identified the search input",
  "element_description": "description of the visual element",
  "coordinates": {"x": <center_x>, "y": <center_y>},
  "confidence": "high/medium/low"
}"""

        result = agent.analyze_screenshot(screenshot_path, prompt, "Scene 1: Find Search Box")

        # Click on search box with validation
        coords = result.get('coordinates') or {}
        x = coords.get('x') if isinstance(coords, dict) else None
        y = coords.get('y') if isinstance(coords, dict) else None

        if x is None or y is None:
            print(f"\n❌ ERROR: Vision LLM could not find search box. Response: {result}")
            if 'error' in result:
                print(f"LLM Error: {result['error']}")
            raise Exception("Could not find search box coordinates")

        print(f"\nClicking on search box at coordinates: ({x}, {y})")
        page.mouse.click(x, y)
        time.sleep(0.5)

        # =================================================================
        # SCENE 2: Type Search Query
        # =================================================================
        print("\n[Scene 2] Typing search query: 'visiting japan'")
        page.keyboard.type("visiting japan", delay=100)
        time.sleep(0.5)

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene2_typing.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        # Press Enter
        print("Pressing Enter...")
        page.keyboard.press("Enter")
        time.sleep(3)  # Wait for search results

        # =================================================================
        # SCENE 3: Select Non-Ad Search Result
        # =================================================================
        print("\n[Scene 3] Analyzing search results...")

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene3_search_results.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        # Ask Vision LLM to select a result
        prompt = """You are a UI testing assistant analyzing a screenshot for automated testing purposes.

Current Task: Identify a non-ad search result link about "visiting japan".

Instructions:
1. Analyze the provided screenshot showing Google search results
2. Identify organic search results (NOT sponsored/ad results)
   - Ad results usually have "Sponsored" or "Ad" labels
   - Organic results are typically in the main content area, below any ads
3. Select the FIRST clearly visible organic result related to visiting Japan
4. Locate the clickable title link (the main blue/purple heading)
5. Provide the center coordinates (x, y) for UI testing

Response Format (JSON only):
{
  "reasoning": "explanation of how you identified the organic result and avoided ads",
  "result_description": "brief description of the selected result",
  "coordinates": {"x": <center_x>, "y": <center_y>},
  "confidence": "high/medium/low",
  "is_ad": false
}"""

        result = agent.analyze_screenshot(screenshot_path, prompt, "Scene 3: Select Search Result")

        # Click on result with validation
        coords = result.get('coordinates') or {}
        x = coords.get('x') if isinstance(coords, dict) else None
        y = coords.get('y') if isinstance(coords, dict) else None

        if x is None or y is None:
            print(f"\n❌ ERROR: Vision LLM could not find search result. Response: {result}")
            if 'error' in result:
                print(f"LLM Error: {result['error']}")
            raise Exception("Could not find search result coordinates")

        print(f"\nClicking on result: {result.get('result_description', 'Unknown')}")
        print(f"Coordinates: ({x}, {y})")

        # Get URL before click
        url_before = page.url
        print(f"Current URL: {url_before}")

        page.mouse.click(x, y)
        time.sleep(3)  # Wait for navigation

        # Check if URL changed (navigation happened)
        url_after = page.url
        print(f"After click URL: {url_after}")

        if url_before == url_after:
            print("⚠️  WARNING: URL did not change - click may have failed")
            print("Trying alternative: click with force and larger delay...")
            page.mouse.click(x, y, click_count=1)
            time.sleep(3)
            url_after = page.url
            print(f"After retry URL: {url_after}")

            if url_before == url_after:
                print("❌ ERROR: Navigation failed - still on search results page")
                raise Exception("Could not navigate to result page")
        else:
            print("✅ Successfully navigated to result page")

        # =================================================================
        # SCENE 4: Verify Success
        # =================================================================
        print("\n[Scene 4] Capturing final page...")

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene4_result_page.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        print(f"\n✅ SUCCESS!")
        print(f"Final URL: {url_after}")

        time.sleep(2)

        browser.close()

    # Print token usage summary
    tracker.print_summary()
    tracker.save_to_file(os.path.join(screenshots_dir, "token_summary.json"))

    print("\n" + "="*70)
    print("DEMO 2 COMPLETE!")
    print("="*70)
    print(f"Total tokens used: {tracker.total_tokens}")
    print(f"Screenshots saved to: {screenshots_dir}")


if __name__ == "__main__":
    main()
