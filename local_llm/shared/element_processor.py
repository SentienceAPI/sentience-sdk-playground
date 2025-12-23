"""
Element filtering and compression for small context window LLMs
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RawElement:
    """Raw element from Sentience snapshot"""
    id: int
    tag: str
    role: Optional[str]
    text: str
    bbox: Dict[str, float]  # {x, y, width, height}
    attributes: Dict[str, Any]

    # Visual cues
    is_visible: bool
    is_clickable: bool
    is_primary: bool
    in_viewport: bool

    # Computed properties
    importance_score: float
    background_color: Optional[str]
    text_color: Optional[str]

    @classmethod
    def from_snapshot_element(cls, elem: Dict[str, Any], index: int) -> 'RawElement':
        """Create RawElement from snapshot dictionary"""
        visual_cues = elem.get('visual_cues', {})

        return cls(
            id=elem.get('id', index),
            tag=elem.get('tag', ''),
            role=elem.get('role'),
            text=elem.get('text', ''),
            bbox=elem.get('bbox', {}),
            attributes=elem.get('attributes', {}),
            is_visible=elem.get('in_viewport', False),
            is_clickable=visual_cues.get('is_clickable', False),
            is_primary=visual_cues.get('is_primary', False),
            in_viewport=elem.get('in_viewport', False),
            importance_score=elem.get('importance_score', 0.0),
            background_color=visual_cues.get('background_color'),
            text_color=visual_cues.get('text_color')
        )


@dataclass
class ElementSnapshot:
    """Collection of elements from page"""
    url: str
    viewport: Dict[str, int]  # {width, height}
    elements: List[RawElement]
    timestamp: float

    @classmethod
    def from_snapshot_data(cls, snapshot_data: Dict[str, Any]) -> 'ElementSnapshot':
        """Create ElementSnapshot from Sentience snapshot"""
        elements = [
            RawElement.from_snapshot_element(elem, i)
            for i, elem in enumerate(snapshot_data.get('elements', []))
        ]

        return cls(
            url=snapshot_data.get('url', ''),
            viewport=snapshot_data.get('viewport', {}),
            elements=elements,
            timestamp=snapshot_data.get('timestamp', 0.0)
        )


class ElementFilter:
    """Filter and compress elements for small context windows"""

    # Task-specific role filters
    TASK_FILTERS = {
        "find_input": {
            "include_roles": ["textbox", "searchbox", "combobox", "input", "search"],
            "exclude_roles": ["img", "image", "button", "link", "span", "div", "svg", "path", "g", "rect", "circle"]
        },
        "find_button": {
            "include_roles": ["button"],
            "exclude_roles": ["searchbox", "textbox", "link", "img", "image", "span", "div", "svg", "path"]
        },
        "find_link": {
            "include_roles": ["link", "a"],
            "exclude_roles": ["searchbox", "combobox", "button", "img", "image", "span", "div", "svg", "path", "g", "rect", "circle", "ul", "li", "navigation", "search", "heading", "main", "presentation"]
        },
        "select_from_list": {
            "include_roles": ["link", "button", "option", "listitem"],
            "exclude_roles": ["searchbox", "textbox", "img", "image", "svg", "path"]
        }
    }

    @staticmethod
    def filter_by_task(
        elements: List[RawElement],
        task_type: str,
        debug: bool = False
    ) -> List[RawElement]:
        """
        Filter elements based on task type

        Args:
            elements: All page elements
            task_type: One of ["find_input", "find_button", "find_link", "select_from_list"]
            debug: Print debug info

        Returns:
            Filtered elements relevant to task
        """
        if task_type not in ElementFilter.TASK_FILTERS:
            # No specific filter, return all
            return elements

        filter_config = ElementFilter.TASK_FILTERS[task_type]
        include_roles = filter_config.get("include_roles", [])
        exclude_roles = filter_config.get("exclude_roles", [])

        filtered = []
        excluded_count = 0
        for elem in elements:
            elem_role = (elem.role or elem.tag or "").lower().strip()

            # Check exclusions first (exact match to avoid "li" matching "link")
            if elem_role in [e.lower() for e in exclude_roles]:
                excluded_count += 1
                continue

            # Check inclusions (if specified)
            if include_roles:
                # Use exact match for strict filtering
                if elem_role in [i.lower() for i in include_roles]:
                    filtered.append(elem)
                    if debug and len(filtered) <= 10:
                        text_preview = elem.text[:40] if elem.text else "(no text)"
                        print(f"  ✅ Included: ID={elem.id} role={elem.role} text='{text_preview}'")
            else:
                filtered.append(elem)

        if debug:
            print(f"  Task filter ({task_type}): kept {len(filtered)}, excluded {excluded_count}")

        return filtered

    @staticmethod
    def filter_by_visibility(
        elements: List[RawElement],
        require_viewport: bool = True,
        require_visible: bool = True
    ) -> List[RawElement]:
        """Filter by visibility criteria"""
        filtered = []
        for elem in elements:
            if require_viewport and not elem.in_viewport:
                continue
            if require_visible and not elem.is_visible:
                continue
            filtered.append(elem)

        return filtered

    @staticmethod
    def filter_by_text_exclusion(
        elements: List[RawElement],
        exclude_patterns: List[str]
    ) -> List[RawElement]:
        """
        Filter out elements containing certain text patterns

        Args:
            elements: Elements to filter
            exclude_patterns: Text patterns to exclude (case-insensitive)

        Returns:
            Filtered elements
        """
        filtered = []
        for elem in elements:
            text_lower = elem.text.lower()
            if any(pattern.lower() in text_lower for pattern in exclude_patterns):
                continue
            filtered.append(elem)

        return filtered

    @staticmethod
    def top_k_by_importance(
        elements: List[RawElement],
        k: int = 20
    ) -> List[RawElement]:
        """Keep only top-k most important elements"""
        return sorted(
            elements,
            key=lambda e: e.importance_score,
            reverse=True
        )[:k]

    @staticmethod
    def top_k_by_position(
        elements: List[RawElement],
        k: int = 20,
        prefer_top: bool = True
    ) -> List[RawElement]:
        """
        Keep top-k elements by position

        Args:
            elements: Elements to filter
            k: Number of elements to keep
            prefer_top: If True, prefer elements at top of page (lower y)

        Returns:
            Top-k elements by position
        """
        sorted_elements = sorted(
            elements,
            key=lambda e: e.bbox.get('y', 9999) if prefer_top else e.bbox.get('x', 9999)
        )
        return sorted_elements[:k]

    @staticmethod
    def compress_element(element: RawElement) -> Dict[str, Any]:
        """
        Compress element to minimal representation

        Reduces token usage by 60-70% while keeping essential info
        """
        # Truncate long text
        text = element.text[:100] if element.text else ""

        return {
            "id": element.id,
            "role": element.role or element.tag,
            "text": text,
            "bbox": {
                "x": int(element.bbox.get("x", 0)),
                "y": int(element.bbox.get("y", 0)),
                "w": int(element.bbox.get("width", 0)),
                "h": int(element.bbox.get("height", 0))
            },
            "clickable": element.is_clickable,
            "visible": element.is_visible,
            "score": round(element.importance_score, 2)
        }

    @staticmethod
    def prepare_for_llm(
        snapshot: ElementSnapshot,
        task_type: str,
        max_elements: int = 15,
        exclude_text_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline: filter -> rank -> compress

        Args:
            snapshot: Full page snapshot
            task_type: Type of task to optimize for
            max_elements: Maximum elements to include
            exclude_text_patterns: Text patterns to exclude (e.g., ["Ad", "Sponsored"])

        Returns:
            Compressed representation for LLM
        """
        # Step 1: Filter by task
        filtered = ElementFilter.filter_by_task(
            snapshot.elements,
            task_type,
            debug=True
        )

        original_count = len(snapshot.elements)
        after_task_filter = len(filtered)

        # Step 2: Filter by visibility
        filtered = ElementFilter.filter_by_visibility(
            filtered,
            require_viewport=True,
            require_visible=True
        )

        after_visibility_filter = len(filtered)

        # Step 3: Filter by text exclusion (if specified)
        if exclude_text_patterns:
            filtered = ElementFilter.filter_by_text_exclusion(
                filtered,
                exclude_text_patterns
            )

        after_text_filter = len(filtered)

        # Step 4: Take top-k by importance
        top_elements = ElementFilter.top_k_by_importance(
            filtered,
            k=max_elements
        )

        # Step 5: Compress each element
        compressed = [
            ElementFilter.compress_element(e)
            for e in top_elements
        ]

        # Print filtering stats
        print(f"📊 Element filtering pipeline:")
        print(f"   Original: {original_count} elements")
        print(f"   After task filter: {after_task_filter} elements")
        print(f"   After visibility filter: {after_visibility_filter} elements")
        if exclude_text_patterns:
            print(f"   After text exclusion: {after_text_filter} elements")
        print(f"   Top-{max_elements}: {len(compressed)} elements")
        reduction_pct = (1 - len(compressed) / original_count) * 100 if original_count > 0 else 0
        print(f"   Reduction: {reduction_pct:.1f}%")

        return {
            "url": snapshot.url,
            "viewport": snapshot.viewport,
            "elements": compressed,
            "count": len(compressed),
            "stats": {
                "original_count": original_count,
                "final_count": len(compressed),
                "reduction_percent": reduction_pct
            }
        }
