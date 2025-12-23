"""
Demo 2: GPT-4o Vision + Playwright for Amazon Shopping

This demo uses GPT-4o Vision to analyze screenshots directly,
then uses Playwright to perform actions based on the vision model's decisions.
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
# Use simplified video generator (no ImageMagick/TextClip needed)
from video_generator_simple import create_demo_video


def main():
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY not found in .env file")
        return

    # Initialize tracker and agent
    tracker = TokenTracker("Demo 2: Vision + LLM")
    agent = VisionAgent(api_key=openai_api_key, tracker=tracker)

    # Screenshot directory with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
    screenshots_dir = os.path.join(base_screenshots_dir, timestamp)
    os.makedirs(screenshots_dir, exist_ok=True)
    print(f"Screenshots will be saved to: {screenshots_dir}")

    print("\n" + "="*70)
    print("DEMO 2: GPT-4o Vision + Playwright - Amazon Shopping")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # =================================================================
        # SCENE 1: Navigate to Amazon & Find Search Bar
        # =================================================================
        print("\n[Scene 1] Navigating to Amazon.com...")
        page.goto("https://www.amazon.com")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)  # Wait for page to fully load

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene1_homepage.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        # Ask Vision LLM to find search bar
        prompt = """You are a UI testing assistant analyzing a screenshot for automated testing purposes.

Current Task: Identify the search input field on the page.

Instructions:
1. Analyze the provided screenshot
2. Locate the search input field (usually near the top of the page)
3. Identify the center coordinates (x, y) of the search input
4. Provide precise pixel coordinates based on a 1920x1080 viewport

Response Format (JSON only):
{
  "reasoning": "brief explanation of how you identified the search input",
  "element_description": "description of the visual element",
  "coordinates": {"x": <center_x>, "y": <center_y>},
  "confidence": "high/medium/low"
}"""

        result = agent.analyze_screenshot(screenshot_path, prompt, "Scene 1: Find Search Bar")

        # Click on search bar with validation
        coords = result.get('coordinates', {})
        x = coords.get('x')
        y = coords.get('y')

        if x is None or y is None:
            print(f"\n❌ ERROR: Vision LLM could not find search bar. Response: {result}")
            raise Exception("Could not find search bar coordinates")

        print(f"\nClicking on search bar at coordinates: ({x}, {y})")
        page.mouse.click(x, y)
        time.sleep(1)

        # =================================================================
        # SCENE 2: Type Search Query
        # =================================================================
        print("\n[Scene 2] Typing search query: 'Christmas gift'")
        page.keyboard.type("Christmas gift", delay=100)
        time.sleep(0.5)

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene2_typing.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        # Press Enter
        print("Pressing Enter...")
        page.keyboard.press("Enter")
        time.sleep(4)  # Wait for search results

        # =================================================================
        # SCENE 3: Select Product from Search Results
        # =================================================================
        print("\n[Scene 3] Analyzing search results...")

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene3_search_results.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        # Ask Vision LLM to select a product
        prompt = """You are a UI testing assistant analyzing a screenshot for automated testing purposes.

Current Task: Identify the first product listing element in search results.

Instructions:
1. Analyze the provided screenshot
2. Identify product listing elements in the main content area
3. Locate the FIRST clearly visible product item (top-left priority)
4. Find the clickable product image or title element
5. Provide the center coordinates (x, y) for UI testing
6. Note if the item is marked as "Sponsored"

Response Format (JSON only):
{
  "reasoning": "explanation of element identification logic",
  "product_description": "brief description of identified element",
  "coordinates": {"x": <center_x>, "y": <center_y>},
  "confidence": "high/medium/low",
  "is_sponsored": true/false
}"""

        result = agent.analyze_screenshot(screenshot_path, prompt, "Scene 3: Select Product")

        # Click on product with validation
        coords = result.get('coordinates') or {}
        x = coords.get('x') if isinstance(coords, dict) else None
        y = coords.get('y') if isinstance(coords, dict) else None

        if x is None or y is None:
            print(f"\n❌ ERROR: Vision LLM could not find product. Response: {result}")
            if 'error' in result:
                print(f"LLM Error: {result['error']}")
            raise Exception("Could not find product coordinates")

        print(f"\nClicking on product: {result.get('product_description', 'Unknown')}")
        print(f"Coordinates: ({x}, {y})")

        # Get current URL before click
        url_before = page.url
        print(f"Current URL: {url_before}")

        page.mouse.click(x, y)

        # Wait for navigation (Amazon pages have continuous network activity, so use simple wait)
        print("Waiting for product page to load...")
        time.sleep(5)  # Simple wait - Amazon loads dynamically

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
                # Try clicking the first product link directly as fallback
                print("Attempting fallback: clicking first product link by selector...")
                try:
                    # Amazon product links usually have specific attributes
                    product_link = page.locator("a[href*='/dp/'], a[href*='/gp/product/']").first
                    product_link.click()
                    time.sleep(5)
                    print(f"Fallback click URL: {page.url}")
                except Exception as e:
                    print(f"Fallback click failed: {e}")
                    raise Exception("Could not navigate to product page")

        # =================================================================
        # SCENE 4: Find and Click "Add to Cart" Button
        # =================================================================
        print("\n[Scene 4] Finding 'Add to Cart' button...")

        # Increase viewport height for this scene to enable panning effect in video
        print("Increasing viewport height for better camera panning...")
        page.set_viewport_size({"width": 1920, "height": 1600})
        time.sleep(1)  # Wait for viewport to adjust

        # Take screenshot with taller viewport
        screenshot_path = os.path.join(screenshots_dir, "vision_scene4_product_details.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path} (1920x1600 for panning effect)")

        # Ask Vision LLM to find Add to Cart button
        prompt = """You are a UI testing assistant analyzing a screenshot for automated testing purposes.

Current Task: Identify a button element with text "Add to Cart" on a product page.

Instructions:
1. Analyze the provided screenshot
2. Locate the button with text "Add to Cart" (typically orange/yellow colored)
3. Distinguish it from other buttons like "Buy Now" if present
4. Provide the center coordinates (x, y) for UI testing
5. Ensure the button is fully visible

Response Format (JSON only):
{
  "reasoning": "explanation of how you identified the button element",
  "button_description": "visual description (color, text, position)",
  "coordinates": {"x": <center_x>, "y": <center_y>},
  "confidence": "high/medium/low",
  "other_buttons_nearby": ["list of nearby button texts"]
}"""

        result = agent.analyze_screenshot(screenshot_path, prompt, "Scene 4: Add to Cart", viewport_width=1920, viewport_height=1600)

        # Click Add to Cart with validation
        coords = result.get('coordinates') or {}
        x = coords.get('x') if isinstance(coords, dict) else None
        y = coords.get('y') if isinstance(coords, dict) else None

        if x is None or y is None:
            print(f"\n❌ ERROR: Vision LLM could not find Add to Cart button")
            print(f"Response: {result}")
            if 'error' in result:
                print(f"LLM Error: {result['error']}")
            print("Attempting to find button using selector fallback...")
            # Fallback: try to find button by selector
            try:
                add_to_cart_btn = page.locator("#add-to-cart-button").first
                add_to_cart_btn.click()
                print("✅ Clicked using selector fallback")
            except Exception as e:
                print(f"Fallback also failed: {e}")
                raise Exception("Could not click Add to Cart button")
        else:
            print(f"\nClicking 'Add to Cart' button")
            print(f"Coordinates: ({x}, {y})")
            page.mouse.click(x, y)

        time.sleep(3)

        # =================================================================
        # SCENE 5: Verify Success
        # =================================================================
        print("\n[Scene 5] Verifying cart addition...")

        # Take screenshot
        screenshot_path = os.path.join(screenshots_dir, "vision_scene5_confirmation.png")
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"Screenshot saved: {screenshot_path}")

        # Ask Vision LLM to verify
        prompt = """You are a UI testing assistant verifying UI state for automated testing purposes.

Current Task: Verify if a success confirmation is displayed on the page.

Instructions:
1. Analyze the provided screenshot
2. Look for visual confirmation indicators:
   - Success overlay/modal with confirmation message
   - Cart icon in header with updated count
   - Green checkmark or success indicator
3. Determine if success indicators are present

Response Format (JSON only):
{
  "success": true/false,
  "reasoning": "explanation of what visual cues were found",
  "confirmation_elements": ["list of visual confirmations found"],
  "cart_count": "number shown in cart icon if visible or empty string"
}"""

        result = agent.analyze_screenshot(screenshot_path, prompt, "Scene 5: Verify Success")

        if result.get('success'):
            print(f"\n✅ SUCCESS: {result.get('reasoning')}")
            print(f"Confirmations: {', '.join(result.get('confirmation_elements', []))}")
        else:
            print(f"\n❌ FAILED: {result.get('reasoning')}")

        time.sleep(2)

        browser.close()

    # Print token usage summary
    tracker.print_summary()
    tracker.save_to_file(os.path.join(screenshots_dir, "token_summary.json"))

    # Generate video
    print("\n" + "="*70)
    print("Generating video with token overlay...")
    print("="*70)
    video_output = os.path.join(os.path.dirname(__file__), "video", "demo2_vision_final.mp4")
    os.makedirs(os.path.dirname(video_output), exist_ok=True)

    try:
        create_demo_video(screenshots_dir, tracker.get_summary(), video_output)
    except Exception as e:
        print(f"Warning: Video generation failed: {e}")
        print("Screenshots and data are still available in the screenshots directory")

    print("\n" + "="*70)
    print("DEMO 2 COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
