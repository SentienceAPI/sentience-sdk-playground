"""
Token usage tracking for LLM agent demos
"""
from typing import List, Dict, Any


class TokenTracker:
    """Track token usage across multiple LLM interactions"""

    def __init__(self, demo_name: str):
        self.demo_name = demo_name
        self.interactions: List[Dict[str, Any]] = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0

    def log_interaction(self, scene: str, prompt_tokens: int, completion_tokens: int):
        """Log a single LLM interaction"""
        total = prompt_tokens + completion_tokens
        self.interactions.append({
            "scene": scene,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total": total
        })
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total

        print(f"  Token usage: {total} (prompt: {prompt_tokens}, completion: {completion_tokens})")

    def get_summary(self) -> Dict[str, Any]:
        """Get complete token usage summary"""
        return {
            "demo_name": self.demo_name,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "interactions": self.interactions,
            "average_per_scene": self.total_tokens / len(self.interactions) if self.interactions else 0
        }

    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()
        print(f"\n{'='*70}")
        print(f"Token Usage Summary: {summary['demo_name']}")
        print(f"{'='*70}")
        for interaction in summary['interactions']:
            print(f"{interaction['scene']:40} {interaction['total']:8} tokens")
        print(f"{'='*70}")
        print(f"{'Total Prompt Tokens:':40} {summary['total_prompt_tokens']:8}")
        print(f"{'Total Completion Tokens:':40} {summary['total_completion_tokens']:8}")
        print(f"{'TOTAL TOKENS:':40} {summary['total_tokens']:8}")
        print(f"{'Average per Scene:':40} {summary['average_per_scene']:8.1f}")
        print(f"{'='*70}\n")

    def save_to_file(self, filepath: str):
        """Save summary to JSON file"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)
        print(f"Token summary saved to: {filepath}")
