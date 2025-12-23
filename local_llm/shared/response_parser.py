"""
Response parser for handling LLM outputs
Handles both JSON and text responses, with robust error recovery
"""
import json
import re
from typing import Optional, Dict, Any, List
from models.base_llm import LLMResponse


class ResponseParser:
    """Parse and validate LLM responses"""

    @staticmethod
    def extract_json(response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from response, handling common issues

        Small LLMs sometimes add markdown, explanations, or malformed JSON
        This function tries multiple strategies to extract valid JSON

        Args:
            response: Raw LLM response string

        Returns:
            Parsed JSON dict or None if extraction fails
        """
        # Strategy 1: Try direct parse
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: Find JSON in markdown code blocks
        # Matches: ```json\n{...}\n``` or ```\n{...}\n```
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find any JSON object in the response
        # Matches first occurrence of {...}
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Strategy 4: Find JSON after "Your response:" or similar markers
        markers = ["Your response:", "Response:", "JSON:", "Output:"]
        for marker in markers:
            if marker in response:
                after_marker = response.split(marker, 1)[1].strip()
                try:
                    return json.loads(after_marker)
                except json.JSONDecodeError:
                    # Try finding JSON object after marker
                    match = re.search(r'\{.*\}', after_marker, re.DOTALL)
                    if match:
                        try:
                            return json.loads(match.group(0))
                        except json.JSONDecodeError:
                            continue

        return None

    @staticmethod
    def validate_element_selection(
        parsed: Dict[str, Any],
        available_ids: List[int]
    ) -> bool:
        """
        Validate that selected element ID exists

        Args:
            parsed: Parsed JSON response
            available_ids: List of valid element IDs

        Returns:
            True if valid, False otherwise
        """
        if "id" not in parsed:
            print("⚠️ Validation failed: No 'id' field in response")
            return False

        selected_id = parsed["id"]

        # Convert string to int if needed (LLMs sometimes return strings)
        if isinstance(selected_id, str):
            try:
                selected_id = int(selected_id)
                parsed["id"] = selected_id  # Update the dict
            except ValueError:
                print(f"⚠️ Validation failed: 'id' cannot be converted to int: {selected_id}")
                return False

        if not isinstance(selected_id, int):
            print(f"⚠️ Validation failed: 'id' must be int, got {type(selected_id)}")
            return False

        if selected_id not in available_ids:
            print(f"⚠️ Validation failed: ID {selected_id} not in available IDs: {available_ids}")
            return False

        return True

    @staticmethod
    def safe_parse(
        response: LLMResponse,
        available_ids: List[int],
        verbose: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Safely parse response with validation

        Args:
            response: LLMResponse object
            available_ids: List of valid element IDs
            verbose: Print debug info

        Returns:
            Parsed and validated JSON, or None if parsing/validation fails
        """
        # Extract JSON
        parsed = ResponseParser.extract_json(response.content)

        if parsed is None:
            if verbose:
                print("❌ Failed to extract JSON from response")
                print(f"   Raw response: {response.content[:200]}...")
            return None

        # Validate
        if not ResponseParser.validate_element_selection(parsed, available_ids):
            if verbose:
                print(f"❌ Validation failed for parsed response: {parsed}")
            return None

        if verbose:
            print(f"✅ Successfully parsed response: ID={parsed.get('id')}")
            if "reasoning" in parsed:
                print(f"   Reasoning: {parsed['reasoning']}")

        return parsed

    @staticmethod
    def extract_id_fallback(response: str, available_ids: List[int]) -> Optional[int]:
        """
        Fallback: Extract element ID directly from text

        Looks for patterns like "id: 42" or "[42]" in the response

        Args:
            response: Raw response string
            available_ids: Valid element IDs

        Returns:
            Extracted ID or None
        """
        # Pattern 1: "id": 42 or "id":42
        pattern = r'"id"\s*:\s*(\d+)'
        match = re.search(pattern, response)
        if match:
            id_val = int(match.group(1))
            if id_val in available_ids:
                return id_val

        # Pattern 2: 'id': 42
        pattern = r"'id'\s*:\s*(\d+)"
        match = re.search(pattern, response)
        if match:
            id_val = int(match.group(1))
            if id_val in available_ids:
                return id_val

        # Pattern 3: [42] at start of line
        pattern = r'^\[(\d+)\]'
        match = re.search(pattern, response, re.MULTILINE)
        if match:
            id_val = int(match.group(1))
            if id_val in available_ids:
                return id_val

        return None
