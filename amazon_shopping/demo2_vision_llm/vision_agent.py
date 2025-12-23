"""
Vision LLM Agent wrapper for screenshot analysis with GPT-4o
"""
import json
import os
import base64
from openai import OpenAI
from typing import Dict, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from token_tracker import TokenTracker


class VisionAgent:
    """Vision LLM agent for analyzing screenshots and making decisions"""

    def __init__(self, api_key: str, tracker: TokenTracker, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.tracker = tracker
        self.model = model

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_screenshot(self, image_path: str, task_prompt: str, scene_name: str, viewport_width: int = 1920, viewport_height: int = 1080) -> Dict[str, Any]:
        """
        Analyze screenshot and return decision

        Args:
            image_path: Path to screenshot image
            task_prompt: Task-specific prompt
            scene_name: Scene identifier for tracking
            viewport_width: Viewport width in pixels (default: 1920)
            viewport_height: Viewport height in pixels (default: 1080)

        Returns:
            Parsed JSON response from LLM
        """
        print(f"\n{'='*70}")
        print(f"Scene: {scene_name}")
        print(f"{'='*70}")
        print(f"Analyzing screenshot: {image_path}")

        # Encode image
        base64_image = self.encode_image(image_path)

        # Build full prompt
        full_prompt = f"""{task_prompt}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation outside the JSON.
The viewport size is {viewport_width}x{viewport_height}. Provide coordinates relative to this viewport."""

        # Call OpenAI Vision API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a UI testing assistant that analyzes web page screenshots for automated testing purposes. You identify UI elements and return structured JSON responses with precise coordinates."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": full_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        # Track token usage
        usage = response.usage
        self.tracker.log_interaction(
            scene=scene_name,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens
        )

        # Parse response with error handling
        message_content = response.choices[0].message.content

        if message_content is None:
            # Check for refusal
            refusal = response.choices[0].message.refusal
            finish_reason = response.choices[0].finish_reason

            error_msg = f"Vision LLM returned empty response.\n"
            error_msg += f"Finish reason: {finish_reason}\n"
            if refusal:
                error_msg += f"Refusal: {refusal}\n"

            print(f"\n❌ ERROR: {error_msg}")
            print(f"Full response: {response}")

            # Return a safe default structure
            return {
                "error": error_msg,
                "coordinates": None,
                "reasoning": "LLM returned empty response"
            }

        try:
            result = json.loads(message_content)
            print(f"\nVision LLM Decision:")
            print(json.dumps(result, indent=2))
            return result
        except json.JSONDecodeError as e:
            print(f"\n❌ ERROR: Failed to parse JSON response: {e}")
            print(f"Raw content: {message_content}")
            return {
                "error": f"JSON parse error: {e}",
                "coordinates": None,
                "reasoning": "Failed to parse LLM response"
            }
