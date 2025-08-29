#!/usr/bin/env python3

import os
import re
from datetime import datetime
from typing import Tuple, List, Optional, NamedTuple
from config import ImageConfig

class TextSegment(NamedTuple):
    """Represents a segment of text with formatting"""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False

def parse_color(color_str: str) -> Tuple[int, int, int]:
    color_str = color_str.strip().lower()
    
    # Check named colors first
    if color_str in ImageConfig.COLORS:
        return ImageConfig.COLORS[color_str]
    
    # Check color schemes
    if color_str in ImageConfig.COLOR_SCHEMES:
        return ImageConfig.COLOR_SCHEMES[color_str]['text']
    
    # Parse hex colors
    if color_str.startswith('#'):
        color_str = color_str[1:]
        if len(color_str) == 6:
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return (r, g, b)
    
    # Parse RGB format
    if ',' in color_str:
        parts = color_str.split(',')
        if len(parts) == 3:
            try:
                r = int(parts[0].strip())
                g = int(parts[1].strip())
                b = int(parts[2].strip())
                if all(0 <= val <= 255 for val in [r, g, b]):
                    return (r, g, b)
            except ValueError:
                pass
    
    return ImageConfig.DEFAULT_TEXT_COLOR

def get_color_scheme(scheme_name: str) -> dict:
    if scheme_name in ImageConfig.COLOR_SCHEMES:
        return ImageConfig.COLOR_SCHEMES[scheme_name]
    return ImageConfig.COLOR_SCHEMES['default']

def parse_font_size(size_str: str) -> int:
    size_str = size_str.strip().lower()
    
    if size_str in ImageConfig.FONT_SIZES:
        return ImageConfig.FONT_SIZES[size_str]
    
    try:
        size = int(size_str)
        if 8 <= size <= 100:
            return size
    except ValueError:
        pass
    
    return ImageConfig.DEFAULT_FONT_SIZE

def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)

def save_image_locally(image, directory: str = "generated_images", 
                      prefix: str = "img", slot: Optional[int] = None) -> str:
    os.makedirs(directory, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if slot:
        filename = f"{prefix}_slot{slot}_{timestamp}.jpg"
    else:
        filename = f"{prefix}_{timestamp}.jpg"
    
    filepath = os.path.join(directory, filename)
    image.save(filepath, 'JPEG', quality=70)
    
    return filepath

def validate_slot(slot: int) -> bool:
    return slot in [1, 2, 3, 4, 5]

def list_available_fonts() -> List[str]:
    font_dirs = [
        "C:\\Windows\\Fonts",
        "/usr/share/fonts",
        "/System/Library/Fonts",
        "/usr/local/share/fonts"
    ]
    
    fonts = []
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            for file in os.listdir(font_dir):
                if file.endswith(('.ttf', '.otf')):
                    fonts.append(os.path.join(font_dir, file))
    
    return fonts

def parse_html_formatting(text: str) -> List[TextSegment]:
    """Parse basic HTML formatting tags and return text segments with formatting info"""
    if not text or '<' not in text:
        return [TextSegment(text=text)]
    
    # Stack to track nested formatting
    format_stack = []
    segments = []
    current_text = ""
    
    # Regular expression to match HTML tags
    tag_pattern = r'<(/?)([biu])\s*/?>'
    
    last_pos = 0
    for match in re.finditer(tag_pattern, text, re.IGNORECASE):
        # Add text before the tag
        if match.start() > last_pos:
            current_text += text[last_pos:match.start()]
        
        is_closing = bool(match.group(1))  # True if </tag>
        tag_name = match.group(2).lower()
        
        if not is_closing:
            # Opening tag - flush current text if any, then start new formatting
            if current_text:
                segments.append(TextSegment(
                    text=current_text,
                    bold='b' in format_stack,
                    italic='i' in format_stack,
                    underline='u' in format_stack
                ))
                current_text = ""
            format_stack.append(tag_name)
        else:
            # Closing tag - flush current text with formatting, then remove from stack
            if current_text:
                segments.append(TextSegment(
                    text=current_text,
                    bold='b' in format_stack,
                    italic='i' in format_stack,
                    underline='u' in format_stack
                ))
                current_text = ""
            if tag_name in format_stack:
                format_stack.remove(tag_name)
        
        last_pos = match.end()
    
    # Add remaining text
    if last_pos < len(text):
        current_text += text[last_pos:]
    
    if current_text:
        segments.append(TextSegment(
            text=current_text,
            bold='b' in format_stack,
            italic='i' in format_stack,
            underline='u' in format_stack
        ))
    
    return segments if segments else [TextSegment(text=text)]

def has_html_tags(text: str) -> bool:
    """Check if text contains HTML formatting tags"""
    if not text:
        return False
    return bool(re.search(r'<[biu].*?>', text, re.IGNORECASE))

def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text, keeping only the content"""
    return re.sub(r'<[^>]+>', '', text)

def split_text_into_lines(text: str, max_chars_per_line: int = 20) -> List[str]:
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        if current_length + word_length + len(current_line) <= max_chars_per_line:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines