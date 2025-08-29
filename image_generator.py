#!/usr/bin/env python3

import io
import os
import platform
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional, List
from config import ImageConfig, DisplayConfig
import textwrap
import utils

class ImageGenerator:
    def __init__(self, width: int = DisplayConfig.IMAGE_WIDTH, 
                 height: int = DisplayConfig.IMAGE_HEIGHT,
                 padding_top: Optional[int] = None,
                 padding_bottom: Optional[int] = None,
                 padding_left: Optional[int] = None,
                 padding_right: Optional[int] = None):
        self.width = width
        self.height = height
        self.config = ImageConfig()
        self._default_font_path = self._find_default_font()
        
        # Set individual paddings with defaults from config
        self.padding_top = padding_top if padding_top is not None else self.config.PADDING_TOP
        self.padding_bottom = padding_bottom if padding_bottom is not None else self.config.PADDING_BOTTOM
        self.padding_left = padding_left if padding_left is not None else self.config.PADDING_LEFT
        self.padding_right = padding_right if padding_right is not None else self.config.PADDING_RIGHT
    
    def _find_default_font(self) -> Optional[str]:
        """Find a suitable default TrueType font on the system"""
        system = platform.system()
        
        font_candidates = []
        if system == "Windows":
            font_candidates = [
                "C:\\Windows\\Fonts\\Arial.ttf",
                "C:\\Windows\\Fonts\\arial.ttf",
                "C:\\Windows\\Fonts\\Calibri.ttf",
                "C:\\Windows\\Fonts\\calibri.ttf",
                "C:\\Windows\\Fonts\\Verdana.ttf",
                "C:\\Windows\\Fonts\\verdana.ttf",
                "C:\\Windows\\Fonts\\Tahoma.ttf",
                "C:\\Windows\\Fonts\\tahoma.ttf",
            ]
        elif system == "Darwin":  # macOS
            font_candidates = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Avenir.ttc",
            ]
        else:  # Linux
            font_candidates = [
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            ]
        
        for font_path in font_candidates:
            if os.path.exists(font_path):
                return font_path
        
        return None
    
    def create_text_image(self, 
                         text: str,
                         font_size: Optional[int] = None,
                         text_color: Optional[Tuple[int, int, int]] = None,
                         background_color: Optional[Tuple[int, int, int]] = None,
                         font_path: Optional[str] = None,
                         alignment: str = 'center',
                         auto_size: bool = False,
                         stroke_width: int = 0,
                         stroke_color: Optional[Tuple[int, int, int]] = None,
                         auto_stroke: bool = False,
                         enable_html: bool = False) -> Image.Image:
        
        if text_color is None:
            text_color = self.config.DEFAULT_TEXT_COLOR
        if background_color is None:
            background_color = self.config.DEFAULT_BACKGROUND_COLOR
        
        # Handle auto font size
        if auto_size or font_size == -1:
            font_size = self.calculate_auto_font_size(text, font_path)
        elif font_size is None:
            font_size = self.config.DEFAULT_FONT_SIZE
        
        img = Image.new('RGB', (self.width, self.height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Try to get a TrueType font that supports size
        font = self._get_font(font_path, font_size)
        
        # Determine stroke settings
        final_stroke_width, final_stroke_color = self._calculate_stroke_settings(
            text_color, background_color, stroke_width, stroke_color, auto_stroke
        )
        
        if enable_html:
            # Parse HTML formatting and render formatted text
            segments = utils.parse_html_formatting(text)
            self._draw_formatted_text(draw, segments, font, text_color, alignment,
                                    final_stroke_width, final_stroke_color, font_path)
        else:
            # Regular text rendering
            wrapped_text = self._wrap_text(text, font, draw)
            self._draw_multiline_text(draw, wrapped_text, font, text_color, alignment, 
                                    final_stroke_width, final_stroke_color)
        
        return img
    
    def _get_font(self, font_path: Optional[str], font_size: int) -> ImageFont.FreeTypeFont:
        """Get a font that supports the specified size"""
        try:
            if font_path and os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)
            elif self._default_font_path:
                return ImageFont.truetype(self._default_font_path, font_size)
            else:
                # Try to create a sized font even without a specific path
                # PIL might find system fonts automatically
                try:
                    return ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        return ImageFont.truetype("Arial", font_size)
                    except:
                        # Last resort: use default font (won't respect size)
                        return ImageFont.load_default()
        except Exception as e:
            print(f"Warning: Could not load TrueType font, using default (size won't change): {e}")
            return ImageFont.load_default()
    
    def _calculate_stroke_settings(self, text_color: Tuple[int, int, int], 
                                 background_color: Tuple[int, int, int],
                                 stroke_width: int, stroke_color: Optional[Tuple[int, int, int]], 
                                 auto_stroke: bool) -> Tuple[int, Optional[Tuple[int, int, int]]]:
        """Calculate optimal stroke settings for text clarity"""
        
        # If stroke explicitly disabled
        if stroke_width == 0 and not auto_stroke:
            return 0, None
        
        # If stroke explicitly set
        if stroke_width > 0:
            if stroke_color is None:
                # Auto-calculate contrasting stroke color
                stroke_color = self._get_contrasting_color(text_color)
            return stroke_width, stroke_color
        
        # Auto stroke logic
        if auto_stroke:
            # Calculate contrast ratio between text and background
            contrast_ratio = self._calculate_contrast_ratio(text_color, background_color)
            
            # Enable stroke for low contrast colored text
            if contrast_ratio < 7.0 and text_color != (255, 255, 255):  # Not pure white
                auto_stroke_width = 1
                auto_stroke_color = self._get_contrasting_color(text_color)
                return auto_stroke_width, auto_stroke_color
        
        return 0, None
    
    def _calculate_contrast_ratio(self, color1: Tuple[int, int, int], 
                                color2: Tuple[int, int, int]) -> float:
        """Calculate WCAG contrast ratio between two colors"""
        def relative_luminance(rgb):
            r, g, b = [x / 255.0 for x in rgb]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        lum1 = relative_luminance(color1)
        lum2 = relative_luminance(color2)
        
        if lum1 > lum2:
            return (lum1 + 0.05) / (lum2 + 0.05)
        else:
            return (lum2 + 0.05) / (lum1 + 0.05)
    
    def _get_contrasting_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Get a contrasting color for stroke"""
        r, g, b = color
        
        # Calculate brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        
        # Return dark stroke for bright colors, light stroke for dark colors
        if brightness > 128:
            return (0, 0, 0)  # Black stroke for light colors
        else:
            return (255, 255, 255)  # White stroke for dark colors
    
    def calculate_auto_font_size(self, text: str, font_path: Optional[str] = None) -> int:
        """Calculate the optimal font size to fit text in the image"""
        min_size = self.config.MIN_AUTO_FONT_SIZE
        max_size = self.config.MAX_AUTO_FONT_SIZE
        
        # Create a temporary draw context for measurements
        temp_img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(temp_img)
        
        best_size = min_size
        # Use auto-size specific paddings
        padding_h = self.config.AUTO_SIZE_PADDING
        padding_bottom = self.config.AUTO_SIZE_PADDING_BOTTOM
        padding_top = self.config.AUTO_SIZE_PADDING
        
        # More iterations for better precision
        for _ in range(10):  # More iterations for better accuracy
            if min_size > max_size:
                break
                
            mid_size = (min_size + max_size) // 2
            font = self._get_font(font_path, mid_size)
            
            # Test if text fits at this size with custom wrapping for auto-size
            max_width = self.width - (2 * padding_h)
            wrapped_lines = self._wrap_text_for_size(text, font, draw, max_width)
            
            # Calculate total height
            total_height = 0
            actual_max_width = 0
            for line in wrapped_lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                line_width = bbox[2] - bbox[0]
                total_height += line_height
                actual_max_width = max(actual_max_width, line_width)
            
            # Add line spacing
            if len(wrapped_lines) > 1:
                total_height += (len(wrapped_lines) - 1) * self.config.LINE_SPACING
            
            # Check if it fits with individual padding
            available_height = self.height - padding_top - padding_bottom
            fits_height = total_height <= available_height
            fits_width = actual_max_width <= (self.width - 2 * padding_h)
            
            if fits_height and fits_width:
                best_size = mid_size
                min_size = mid_size + 1
            else:
                max_size = mid_size - 1
        
        return best_size
    
    def _wrap_text_for_size(self, text: str, font: ImageFont.FreeTypeFont, draw: ImageDraw.Draw, max_width: int) -> List[str]:
        """Wrap text for auto-sizing with specific max width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, add it anyway
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]
    
    def create_gradient_background(self, 
                                  color1: Tuple[int, int, int],
                                  color2: Tuple[int, int, int],
                                  direction: str = 'vertical') -> Image.Image:
        
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        if direction == 'vertical':
            for y in range(self.height):
                ratio = y / self.height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.rectangle([(0, y), (self.width, y + 1)], fill=(r, g, b))
        else:
            for x in range(self.width):
                ratio = x / self.width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.rectangle([(x, 0), (x + 1, self.height)], fill=(r, g, b))
        
        return img
    
    def create_with_gradient(self,
                           text: str,
                           color1: Tuple[int, int, int],
                           color2: Tuple[int, int, int],
                           text_color: Optional[Tuple[int, int, int]] = None,
                           font_size: Optional[int] = None,
                           font_path: Optional[str] = None,
                           direction: str = 'vertical',
                           auto_size: bool = False,
                           stroke_width: int = 0,
                           stroke_color: Optional[Tuple[int, int, int]] = None,
                           auto_stroke: bool = False,
                           enable_html: bool = False) -> Image.Image:
        
        if text_color is None:
            text_color = self.config.DEFAULT_TEXT_COLOR
        
        # Handle auto font size
        if auto_size or font_size == -1:
            font_size = self.calculate_auto_font_size(text, font_path)
        elif font_size is None:
            font_size = self.config.DEFAULT_FONT_SIZE
        
        img = self.create_gradient_background(color1, color2, direction)
        draw = ImageDraw.Draw(img)
        
        # Use the same font method as create_text_image
        font = self._get_font(font_path, font_size)
        
        # Calculate average gradient color for stroke calculation
        avg_bg = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))
        
        # Determine stroke settings
        final_stroke_width, final_stroke_color = self._calculate_stroke_settings(
            text_color, avg_bg, stroke_width, stroke_color, auto_stroke
        )
        
        if enable_html:
            # Parse HTML formatting and render formatted text
            segments = utils.parse_html_formatting(text)
            self._draw_formatted_text(draw, segments, font, text_color, 'center',
                                    final_stroke_width, final_stroke_color, font_path)
        else:
            # Regular text rendering
            wrapped_text = self._wrap_text(text, font, draw)
            self._draw_multiline_text(draw, wrapped_text, font, text_color, 'center', 
                                    final_stroke_width, final_stroke_color)
        
        return img
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, draw: ImageDraw.Draw) -> List[str]:
        max_width = self.width - (self.padding_left + self.padding_right)
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]
    
    def _draw_multiline_text(self, draw: ImageDraw.Draw, lines: List[str], 
                           font: ImageFont.FreeTypeFont, color: Tuple[int, int, int],
                           alignment: str = 'center',
                           stroke_width: int = 0,
                           stroke_color: Optional[Tuple[int, int, int]] = None):
        
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])
        
        # Calculate line spacing considering stroke width
        effective_line_spacing = self.config.LINE_SPACING + (stroke_width * 2 if stroke_width > 0 else 0)
        total_height = sum(line_heights) + (len(lines) - 1) * effective_line_spacing
        # Center vertically considering individual top/bottom padding
        available_height = self.height - self.padding_top - self.padding_bottom
        y = self.padding_top + (available_height - total_height) // 2
        
        for i, line in enumerate(lines):
            if alignment == 'justify' and len(lines) > 1 and i < len(lines) - 1:
                # Justify all lines except the last one
                self._draw_justified_line(draw, line, y, font, color, stroke_width, stroke_color)
            else:
                # Normal alignment for non-justified or last line
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if alignment == 'center' or (alignment == 'justify' and i == len(lines) - 1):
                    x = (self.width - text_width) // 2
                elif alignment == 'left':
                    x = self.padding_left
                elif alignment == 'right':
                    x = self.width - text_width - self.padding_right
                else:  # justify single line - center it
                    x = (self.width - text_width) // 2
                
                # Draw text with stroke if enabled
                if stroke_width > 0 and stroke_color:
                    draw.text((x, y), line, fill=stroke_color, font=font, stroke_width=stroke_width)
                draw.text((x, y), line, fill=color, font=font)
            
            y += line_heights[i] + effective_line_spacing
    
    def _draw_justified_line(self, draw: ImageDraw.Draw, line: str, y: int, 
                           font: ImageFont.FreeTypeFont, color: Tuple[int, int, int],
                           stroke_width: int = 0,
                           stroke_color: Optional[Tuple[int, int, int]] = None):
        """Draw a line with justified alignment"""
        words = line.split()
        if len(words) <= 1:
            # Can't justify single word, center it instead
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            # Draw with stroke if enabled
            if stroke_width > 0 and stroke_color:
                draw.text((x, y), line, fill=stroke_color, font=font, stroke_width=stroke_width)
            draw.text((x, y), line, fill=color, font=font)
            return
        
        # Calculate available width for text
        available_width = self.width - self.padding_left - self.padding_right
        
        # Calculate total width of all words
        total_word_width = 0
        word_widths = []
        for word in words:
            bbox = draw.textbbox((0, 0), word, font=font)
            word_width = bbox[2] - bbox[0]
            word_widths.append(word_width)
            total_word_width += word_width
        
        # Calculate space between words
        total_space_needed = available_width - total_word_width
        num_gaps = len(words) - 1
        
        if num_gaps > 0 and total_space_needed >= 0:
            space_per_gap = total_space_needed / num_gaps
            
            # Draw words with calculated spacing
            x = self.padding_left
            for i, word in enumerate(words):
                # Draw with stroke if enabled
                if stroke_width > 0 and stroke_color:
                    draw.text((int(x), y), word, fill=stroke_color, font=font, stroke_width=stroke_width)
                draw.text((int(x), y), word, fill=color, font=font)
                x += word_widths[i]
                if i < len(words) - 1:  # Not the last word
                    x += space_per_gap
        else:
            # Fallback to left align if justify doesn't work well
            x = self.padding_left
            current_line = ' '.join(words)
            # Draw with stroke if enabled
            if stroke_width > 0 and stroke_color:
                draw.text((x, y), current_line, fill=stroke_color, font=font, stroke_width=stroke_width)
            draw.text((x, y), current_line, fill=color, font=font)
    
    def _get_formatted_font(self, base_font_path: Optional[str], font_size: int, 
                          bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
        """Get a font with the specified formatting (bold/italic)"""
        try:
            if base_font_path and os.path.exists(base_font_path):
                # Try to find bold/italic variants of the specified font
                base_name = os.path.splitext(base_font_path)[0]
                
                if bold and italic:
                    # Try bold-italic variants
                    for suffix in ['-BoldItalic', '-BoldOblique', 'bi', 'BI']:
                        variant_path = f"{base_name}{suffix}.ttf"
                        if os.path.exists(variant_path):
                            return ImageFont.truetype(variant_path, font_size)
                elif bold:
                    # Try bold variants
                    for suffix in ['-Bold', 'b', 'B']:
                        variant_path = f"{base_name}{suffix}.ttf"
                        if os.path.exists(variant_path):
                            return ImageFont.truetype(variant_path, font_size)
                elif italic:
                    # Try italic variants
                    for suffix in ['-Italic', '-Oblique', 'i', 'I']:
                        variant_path = f"{base_name}{suffix}.ttf"
                        if os.path.exists(variant_path):
                            return ImageFont.truetype(variant_path, font_size)
                
                # Fall back to base font
                return ImageFont.truetype(base_font_path, font_size)
            
            elif self._default_font_path:
                # Use system default font with formatting
                if bold and italic:
                    # Try Arial Bold Italic or similar
                    for font_name in ["arialbi.ttf", "Arial-BoldItalic.ttf"]:
                        try:
                            return ImageFont.truetype(font_name, font_size)
                        except:
                            continue
                elif bold:
                    # Try Arial Bold or similar
                    for font_name in ["arialbd.ttf", "Arial-Bold.ttf"]:
                        try:
                            return ImageFont.truetype(font_name, font_size)
                        except:
                            continue
                elif italic:
                    # Try Arial Italic or similar
                    for font_name in ["ariali.ttf", "Arial-Italic.ttf"]:
                        try:
                            return ImageFont.truetype(font_name, font_size)
                        except:
                            continue
                
                # Fall back to default font
                return ImageFont.truetype(self._default_font_path, font_size)
        except:
            pass
        
        # Ultimate fallback to default font (won't have formatting)
        return self._get_font(base_font_path, font_size)
    
    def _draw_formatted_text(self, draw: ImageDraw.Draw, segments: List[utils.TextSegment], 
                           base_font: ImageFont.FreeTypeFont, text_color: Tuple[int, int, int],
                           alignment: str, stroke_width: int, stroke_color: Optional[Tuple[int, int, int]],
                           font_path: Optional[str]):
        """Draw text with HTML formatting support"""
        
        # Extract font size from base font
        try:
            font_size = base_font.size
        except:
            font_size = 24  # fallback
        
        # Create formatted line segments that respect word boundaries
        formatted_lines = self._wrap_formatted_text(segments, base_font, draw, font_path, font_size)
        
        # Calculate line positions
        line_heights = []
        for line_segments in formatted_lines:
            # Calculate height for this line
            max_height = 0
            for segment in line_segments:
                font = self._get_formatted_font(font_path, font_size, segment.bold, segment.italic)
                bbox = draw.textbbox((0, 0), segment.text, font=font)
                max_height = max(max_height, bbox[3] - bbox[1])
            line_heights.append(max_height)
        
        effective_line_spacing = self.config.LINE_SPACING + (stroke_width * 2 if stroke_width > 0 else 0)
        total_height = sum(line_heights) + (len(formatted_lines) - 1) * effective_line_spacing
        available_height = self.height - self.padding_top - self.padding_bottom
        y = self.padding_top + (available_height - total_height) // 2
        
        # Draw each formatted line
        for i, line_segments in enumerate(formatted_lines):
            self._draw_formatted_line_segments(draw, line_segments, y, text_color, alignment, 
                                             stroke_width, stroke_color, font_path, font_size)
            
            # Update position for next line
            y += line_heights[i] + effective_line_spacing
    
    def _wrap_formatted_text(self, segments: List[utils.TextSegment], base_font: ImageFont.FreeTypeFont, 
                           draw: ImageDraw.Draw, font_path: Optional[str], font_size: int) -> List[List[utils.TextSegment]]:
        """Wrap formatted text segments into lines, preserving formatting"""
        max_width = self.width - (self.padding_left + self.padding_right)
        lines = []
        current_line = []
        current_line_width = 0
        
        for segment in segments:
            words = segment.text.split()
            font = self._get_formatted_font(font_path, font_size, segment.bold, segment.italic)
            
            for word in words:
                # Create a segment for this word
                word_segment = utils.TextSegment(
                    text=word,
                    bold=segment.bold,
                    italic=segment.italic,
                    underline=segment.underline
                )
                
                # Calculate word width
                bbox = draw.textbbox((0, 0), word, font=font)
                word_width = bbox[2] - bbox[0]
                
                # Add space width if not the first word in line
                space_width = 0
                if current_line:
                    space_bbox = draw.textbbox((0, 0), " ", font=font)
                    space_width = space_bbox[2] - space_bbox[0]
                
                # Check if word fits on current line
                if current_line and current_line_width + space_width + word_width > max_width:
                    # Start new line
                    lines.append(current_line)
                    current_line = [word_segment]
                    current_line_width = word_width
                else:
                    # Add word to current line
                    if current_line:
                        # Add space before word (except for first word)
                        space_segment = utils.TextSegment(
                            text=" ",
                            bold=segment.bold,
                            italic=segment.italic,
                            underline=segment.underline
                        )
                        current_line.append(space_segment)
                        current_line_width += space_width
                    
                    current_line.append(word_segment)
                    current_line_width += word_width
        
        # Add the last line
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [[utils.TextSegment(text="")]]
    
    def _draw_formatted_line_segments(self, draw: ImageDraw.Draw, line_segments: List[utils.TextSegment],
                                    y: int, text_color: Tuple[int, int, int], alignment: str,
                                    stroke_width: int, stroke_color: Optional[Tuple[int, int, int]],
                                    font_path: Optional[str], font_size: int):
        """Draw a line of formatted text segments"""
        
        # Calculate total line width for alignment
        total_width = 0
        for segment in line_segments:
            font = self._get_formatted_font(font_path, font_size, segment.bold, segment.italic)
            bbox = draw.textbbox((0, 0), segment.text, font=font)
            total_width += bbox[2] - bbox[0]
        
        # Calculate starting x position based on alignment
        if alignment == 'center':
            current_x = (self.width - total_width) // 2
        elif alignment == 'left':
            current_x = self.padding_left
        elif alignment == 'right':
            current_x = self.width - total_width - self.padding_right
        else:  # justify - use center for now (could implement justify for formatted text later)
            current_x = (self.width - total_width) // 2
        
        # Draw each segment
        for segment in line_segments:
            if segment.text:  # Skip empty segments
                font = self._get_formatted_font(font_path, font_size, segment.bold, segment.italic)
                
                # Draw stroke if enabled
                if stroke_width > 0 and stroke_color:
                    draw.text((current_x, y), segment.text, fill=stroke_color, font=font, stroke_width=stroke_width)
                
                # Draw underline if needed
                if segment.underline:
                    bbox = draw.textbbox((current_x, y), segment.text, font=font)
                    underline_y = bbox[3] + 1
                    draw.line([(bbox[0], underline_y), (bbox[2], underline_y)], fill=text_color, width=1)
                
                # Draw the text
                draw.text((current_x, y), segment.text, fill=text_color, font=font)
                
                # Move x position for next segment
                bbox = draw.textbbox((current_x, y), segment.text, font=font)
                current_x = bbox[2]
    
    def _draw_formatted_line(self, draw: ImageDraw.Draw, line: str, segments: List[utils.TextSegment],
                           y: int, text_color: Tuple[int, int, int], alignment: str,
                           stroke_width: int, stroke_color: Optional[Tuple[int, int, int]],
                           font_path: Optional[str], font_size: int,
                           start_segment: int, start_char: int):
        """Draw a single line with HTML formatting"""
        
        # Calculate line width for alignment
        total_width = 0
        current_x = 0
        
        # First pass: calculate total width
        char_pos = 0
        for segment in segments:
            if char_pos + len(segment.text) <= len(line):
                # Entire segment fits in this line
                font = self._get_formatted_font(font_path, font_size, segment.bold, segment.italic)
                bbox = draw.textbbox((0, 0), segment.text, font=font)
                total_width += bbox[2] - bbox[0]
                char_pos += len(segment.text)
            else:
                # Partial segment
                remaining_chars = len(line) - char_pos
                if remaining_chars > 0:
                    text_part = segment.text[:remaining_chars]
                    font = self._get_formatted_font(font_path, font_size, segment.bold, segment.italic)
                    bbox = draw.textbbox((0, 0), text_part, font=font)
                    total_width += bbox[2] - bbox[0]
                break
        
        # Calculate starting x position based on alignment
        if alignment == 'center':
            start_x = (self.width - total_width) // 2
        elif alignment == 'left':
            start_x = self.padding_left
        elif alignment == 'right':
            start_x = self.width - total_width - self.padding_right
        else:  # justify - use center for now
            start_x = (self.width - total_width) // 2
        
        # Second pass: draw the text
        current_x = start_x
        char_pos = 0
        
        for segment in segments:
            if char_pos >= len(line):
                break
                
            if char_pos + len(segment.text) <= len(line):
                # Entire segment fits
                text_part = segment.text
                char_pos += len(segment.text)
            else:
                # Partial segment
                remaining_chars = len(line) - char_pos
                if remaining_chars <= 0:
                    break
                text_part = segment.text[:remaining_chars]
                char_pos += remaining_chars
            
            if text_part:
                font = self._get_formatted_font(font_path, font_size, segment.bold, segment.italic)
                
                # Draw stroke if enabled
                if stroke_width > 0 and stroke_color:
                    draw.text((current_x, y), text_part, fill=stroke_color, font=font, stroke_width=stroke_width)
                
                # Draw text with underline if needed
                if segment.underline:
                    # Draw underline
                    bbox = draw.textbbox((current_x, y), text_part, font=font)
                    underline_y = bbox[3] + 1
                    draw.line([(bbox[0], underline_y), (bbox[2], underline_y)], fill=text_color, width=1)
                
                # Draw the text
                draw.text((current_x, y), text_part, fill=text_color, font=font)
                
                # Move x position for next segment
                bbox = draw.textbbox((current_x, y), text_part, font=font)
                current_x = bbox[2]
    
    def to_jpeg_bytes(self, image: Image.Image, quality: int = DisplayConfig.JPEG_QUALITY) -> bytes:
        buf = io.BytesIO()
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(buf, format='JPEG', quality=quality, optimize=True)
        return buf.getvalue()