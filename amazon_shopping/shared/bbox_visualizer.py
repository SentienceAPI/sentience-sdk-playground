"""
Bounding Box Visualizer for API Elements

Draws colored bounding boxes and labels on screenshots to visualize
the filtered elements returned by the Sentience API.
"""
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List
import os


def visualize_api_elements(screenshot_path: str, snapshot_data: Dict[str, Any], output_path: str = None) -> str:
    """
    Draw bounding boxes on screenshot for all API-filtered elements

    Args:
        screenshot_path: Path to the original screenshot
        snapshot_data: The snapshot data from API (contains 'elements' array)
        output_path: Optional output path. If None, will add '_annotated' suffix

    Returns:
        Path to the annotated image
    """
    # Load image
    img = Image.open(screenshot_path)
    draw = ImageDraw.Draw(img, 'RGBA')

    # Load fonts (try multiple locations for cross-platform compatibility)
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "C:\\Windows\\Fonts\\arial.ttf",  # Windows
    ]

    font_large = None
    font_small = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_large = ImageFont.truetype(font_path, 14)
                font_small = ImageFont.truetype(font_path, 11)
                break
            except:
                pass

    # Fallback to default font
    if font_large is None:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Get elements from snapshot
    elements = snapshot_data.get('elements', [])

    # Draw bounding boxes for each element
    for element in elements:
        bbox = element.get('bbox', {})
        x = bbox.get('x', 0)
        y = bbox.get('y', 0)
        width = bbox.get('width', 0)
        height = bbox.get('height', 0)

        # Get visual cues
        visual_cues = element.get('visual_cues', {})
        is_primary = visual_cues.get('is_primary', False)
        is_clickable = visual_cues.get('is_clickable', False)

        # Choose color based on element properties
        if is_primary:
            # Primary elements: Eye-catching gold/yellow with thicker border
            border_color = (255, 215, 0, 255)  # Gold
            border_width = 4
            fill_color = (255, 215, 0, 40)  # Semi-transparent gold fill
        elif is_clickable:
            # Clickable elements: Green border
            border_color = (0, 255, 0, 255)  # Bright green
            border_width = 2
            fill_color = (0, 255, 0, 20)  # Very light green fill
        else:
            # Non-clickable elements: Light blue border
            border_color = (100, 150, 255, 200)  # Light blue
            border_width = 1
            fill_color = (100, 150, 255, 15)  # Very light blue fill

        # Draw semi-transparent fill
        draw.rectangle(
            [(x, y), (x + width, y + height)],
            fill=fill_color,
            outline=None
        )

        # Draw border
        draw.rectangle(
            [(x, y), (x + width, y + height)],
            outline=border_color,
            width=border_width
        )

        # Prepare label text
        text = element.get('text', '').strip()
        role = element.get('role', '')

        # Truncate long text
        if len(text) > 30:
            text = text[:27] + "..."

        # Create label with role and text
        if text and role:
            label = f"{role}: {text}"
        elif text:
            label = text
        elif role:
            label = role
        else:
            label = f"id:{element.get('id', '?')}"

        # Draw label with background
        # Position label above the bbox if there's space, otherwise below
        label_padding = 2

        # Get text bounding box
        try:
            text_bbox = draw.textbbox((0, 0), label, font=font_small)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except:
            # Fallback for older PIL versions
            text_width = len(label) * 7
            text_height = 12

        # Determine label position
        if y > text_height + 10:
            # Place above bbox
            label_y = y - text_height - 4
        else:
            # Place below bbox
            label_y = y + height + 2

        label_x = max(0, min(x, img.width - text_width - label_padding * 2))

        # Draw label background (semi-transparent)
        label_bg_color = (0, 0, 0, 180)  # Dark background
        draw.rectangle(
            [
                (label_x, label_y),
                (label_x + text_width + label_padding * 2, label_y + text_height + label_padding * 2)
            ],
            fill=label_bg_color
        )

        # Draw label text
        text_color = (255, 255, 255, 255) if not is_primary else (255, 215, 0, 255)
        draw.text(
            (label_x + label_padding, label_y + label_padding),
            label,
            fill=text_color,
            font=font_small
        )

    # Add legend in top-left corner
    legend_x = 10
    legend_y = 10
    legend_items = [
        ("PRIMARY", (255, 215, 0, 255), "Gold border = is_primary"),
        ("CLICKABLE", (0, 255, 0, 255), "Green border = is_clickable"),
        ("OTHER", (100, 150, 255, 200), "Blue border = other elements")
    ]

    for i, (label, color, description) in enumerate(legend_items):
        item_y = legend_y + i * 20

        # Draw legend background
        draw.rectangle(
            [(legend_x, item_y), (legend_x + 250, item_y + 16)],
            fill=(0, 0, 0, 180)
        )

        # Draw color box
        draw.rectangle(
            [(legend_x + 5, item_y + 4), (legend_x + 20, item_y + 12)],
            fill=color,
            outline=color
        )

        # Draw description
        draw.text(
            (legend_x + 25, item_y + 2),
            description,
            fill=(255, 255, 255, 255),
            font=font_small
        )

    # Determine output path
    if output_path is None:
        base, ext = os.path.splitext(screenshot_path)
        output_path = f"{base}_annotated{ext}"

    # Save annotated image
    img.save(output_path)
    print(f"  Saved annotated screenshot: {output_path}")

    return output_path
