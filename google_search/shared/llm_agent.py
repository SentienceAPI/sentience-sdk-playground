"""
LLM Agent wrapper for structured JSON analysis
"""
import json
import os
from openai import OpenAI
from typing import Dict, Any
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from token_tracker import TokenTracker


class LLMAgent:
    """LLM agent for analyzing snapshot data and making decisions"""

    def __init__(self, api_key: str, tracker: TokenTracker, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=api_key)
        self.tracker = tracker
        self.model = model

    def analyze_snapshot(self, snapshot_data: Dict[str, Any], task_prompt: str, scene_name: str) -> Dict[str, Any]:
        """
        Analyze snapshot data and return decision

        Args:
            snapshot_data: Snapshot dictionary from SDK
            task_prompt: Task-specific prompt
            scene_name: Scene identifier for tracking

        Returns:
            Parsed JSON response from LLM
        """
        # Build full prompt
        full_prompt = f"""{task_prompt}

Snapshot Data:
{json.dumps(snapshot_data, indent=2)}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""

        print(f"\n{'='*70}")
        print(f"Scene: {scene_name}")
        print(f"{'='*70}")

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI agent that analyzes web page data and returns structured JSON responses."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        # Track token usage
        usage = response.usage
        self.tracker.log_interaction(
            scene=scene_name,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)
        print(f"\nLLM Decision:")
        print(json.dumps(result, indent=2))

        return result
