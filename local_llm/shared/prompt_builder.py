"""
Prompt builder optimized for small local LLMs
Uses ultra-concise instructions and explicit output formats
"""
from typing import Dict, Any, List


class PromptBuilder:
    """Build optimized prompts for small LLMs"""

    # System prompts (ultra-compact)
    SYSTEM_PROMPTS = {
        "default": "You are a web automation assistant. Respond ONLY with valid JSON. No explanations.",
        "compact": "Web automation agent. Output JSON only.",
        "json": "Output valid JSON only."
    }

    @staticmethod
    def build_task_prompt(
        task_type: str,
        compressed_elements: Dict[str, Any],
        additional_context: str = ""
    ) -> str:
        """
        Build task-specific prompt optimized for small LLMs

        Args:
            task_type: One of ["find_input", "find_button", "find_link", "select_from_list"]
            compressed_elements: Compressed element data from ElementFilter
            additional_context: Additional task context

        Returns:
            Optimized prompt string
        """
        if task_type == "find_input":
            return PromptBuilder._build_find_input_prompt(
                compressed_elements,
                additional_context
            )
        elif task_type == "find_button":
            return PromptBuilder._build_find_button_prompt(
                compressed_elements,
                additional_context
            )
        elif task_type == "find_link":
            return PromptBuilder._build_find_link_prompt(
                compressed_elements,
                additional_context
            )
        elif task_type == "select_from_list":
            return PromptBuilder._build_select_from_list_prompt(
                compressed_elements,
                additional_context
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    @staticmethod
    def _build_find_input_prompt(
        elements: Dict[str, Any],
        context: str
    ) -> str:
        """Find input field (search box, text input, etc.)"""

        search_term = context or "input field"

        return f"""Task: Find the {search_term} where users can TYPE text.

Elements (format: [id] role 'text' bbox score):
{PromptBuilder._format_elements_compact(elements['elements'])}

IMPORTANT RULES:
1. ONLY select elements with role="textbox" OR role="searchbox" OR role="combobox"
2. DO NOT select links (role="link") - we need an INPUT FIELD, not a link
3. The element MUST allow typing text (it's an input box)
4. Must have clickable=true
5. Prefer highest score

Example: If you see [5] searchbox 'Search', select id 5 (the searchbox, not a link)

Output ONLY this JSON format (id must be a number):
{{
  "id": 5,
  "reasoning": "Element 5 is a searchbox where users can type"
}}

Your response:"""

    @staticmethod
    def _build_find_button_prompt(
        elements: Dict[str, Any],
        context: str
    ) -> str:
        """Find button to click"""

        button_text = context or "button"

        return f"""Task: Find the "{button_text}" button.

Elements (format: [id] role 'text' bbox score):
{PromptBuilder._format_elements_compact(elements['elements'])}

Rules:
1. Find text matching "{button_text}" (case-insensitive, partial OK)
2. Must be role="button" AND clickable=true
3. Prefer exact match over partial
4. Prefer higher score

Output JSON:
{{
  "id": <element_id>,
  "reasoning": "<why>"
}}

Your response:"""

    @staticmethod
    def _build_find_link_prompt(
        elements: Dict[str, Any],
        context: str
    ) -> str:
        """Find link to click (e.g., search result)"""

        instruction = context or "Select first link"

        return f"""Task: {instruction}

This is a Google search results page. Find the FIRST REAL SEARCH RESULT (not navigation links).

Elements (format: [id] role 'text' bbox score):
{PromptBuilder._format_elements_compact(elements['elements'])}

IMPORTANT RULES:
1. ONLY select role="link" (NOT textbox, NOT searchbox, NOT combobox)
2. DO NOT select any search box or input field - we already searched
3. AVOID links with "Ad", "Sponsored", "·", "Images", "Videos", "Shopping", "News"
4. AVOID navigation links like "Search for Images", "Sign in", "Settings"
5. SELECT a search result link - it will have descriptive text about a website
6. Prefer links in the CENTER/LEFT of the page (x between 100-800)
7. Prefer links lower on the page (y > 200)
8. Must have visible=true

Example of GOOD search result: [10] link 'Japan Travel Guide - Official Tourism...'
Example of BAD #1: [15] link 'Search for Images' (this is navigation, not a result)
Example of BAD #2: [5] searchbox 'Search' (this is the search box, not a result link)

Output ONLY this JSON format (id must be a number):
{{
  "id": 10,
  "reasoning": "Element 10 is a search result link about Japan travel"
}}

Your response:"""

    @staticmethod
    def _build_select_from_list_prompt(
        elements: Dict[str, Any],
        context: str
    ) -> str:
        """Select specific item from a list"""

        target = context or "first item"

        return f"""Task: Select "{target}" from the list.

Elements (format: [id] role 'text' bbox score):
{PromptBuilder._format_elements_compact(elements['elements'])}

Rules:
1. Match text to "{target}" (partial match OK)
2. Prefer exact match > partial match
3. Must be clickable=true
4. Prefer higher score

Output JSON:
{{
  "id": <element_id>,
  "match_quality": "<exact|partial>",
  "reasoning": "<why>"
}}

Your response:"""

    @staticmethod
    def _format_elements_compact(elements: List[Dict]) -> str:
        """
        Format elements in ultra-compact representation

        Example output:
        [42] searchbox 'Search' (100,50,600x40) score=0.95
        [43] button 'Search' (720,50,80x40) score=0.85
        """
        lines = []
        for e in elements:
            # Get bbox values safely
            bbox = e.get('bbox', {})
            x = bbox.get('x', 0)
            y = bbox.get('y', 0)
            w = bbox.get('w', 0)
            h = bbox.get('h', 0)

            # Format bbox compactly
            bbox_str = f"({x},{y},{w}x{h})"

            # Truncate and clean text
            text = e.get('text', '')[:50].replace('\n', ' ').strip()
            text_repr = f"'{text}'" if text else "''"

            # Build line
            role = e.get('role', 'unknown')[:15]  # Truncate long roles
            score = e.get('score', 0.0)

            line = f"[{e['id']}] {role:15} {text_repr:52} {bbox_str} score={score:.2f}"
            lines.append(line)

        return '\n'.join(lines)

    @staticmethod
    def get_system_prompt(variant: str = "default") -> str:
        """Get system prompt by variant"""
        return PromptBuilder.SYSTEM_PROMPTS.get(variant, PromptBuilder.SYSTEM_PROMPTS["default"])
