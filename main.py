#!/usr/bin/env python3

import sys
import argparse
from image_generator import ImageGenerator
from display_uploader import DisplayUploader
from config import DisplayConfig, ImageConfig
import utils

def create_and_upload_text(slot: int, text: str, **kwargs):
    # Extract padding values
    padding_top = kwargs.get('padding_top')
    padding_bottom = kwargs.get('padding_bottom') 
    padding_left = kwargs.get('padding_left')
    padding_right = kwargs.get('padding_right')
    
    generator = ImageGenerator(
        padding_top=padding_top,
        padding_bottom=padding_bottom,
        padding_left=padding_left,
        padding_right=padding_right
    )
    uploader = DisplayUploader()
    
    font_size = kwargs.get('font_size')
    auto_size = kwargs.get('auto_size', False)
    color_scheme = kwargs.get('color_scheme', 'default')
    font_color_str = kwargs.get('font_color')
    text_align = kwargs.get('text_align', 'center')
    save_local = kwargs.get('save_local', False)
    gradient = kwargs.get('gradient', False)
    
    # Stroke parameters
    text_stroke = kwargs.get('text_stroke', False)
    stroke_width = kwargs.get('stroke_width', 0)
    stroke_color_str = kwargs.get('stroke_color')
    no_auto_stroke = kwargs.get('no_auto_stroke', False)
    
    # HTML formatting - auto-detect or explicit
    enable_html = kwargs.get('enable_html', False)
    if not enable_html:
        # Auto-detect HTML tags in text
        enable_html = utils.has_html_tags(text)
    
    # Handle auto size
    if auto_size:
        font_size = -1  # Signal for auto-sizing
    elif font_size is None:
        font_size = ImageConfig.DEFAULT_FONT_SIZE
    
    scheme = utils.get_color_scheme(color_scheme)
    
    # Override text color if font_color is specified
    if font_color_str:
        text_color = utils.parse_color(font_color_str)
    else:
        text_color = scheme['text']
    
    # Handle stroke settings
    stroke_explicitly_requested = text_stroke or stroke_width > 0 or stroke_color_str
    
    if text_stroke and stroke_width == 0:
        stroke_width = 1  # Default stroke width when explicitly enabled
    
    stroke_color = None
    if stroke_color_str:
        stroke_color = utils.parse_color(stroke_color_str)
    
    # Enable auto stroke if explicitly requested (via --text-stroke, --stroke-width, or --stroke-color)
    # but not if --no-auto-stroke is set
    auto_stroke = stroke_explicitly_requested and not no_auto_stroke
    
    if gradient and 'gradient_end' in kwargs:
        gradient_end = utils.parse_color(kwargs['gradient_end'])
        image = generator.create_with_gradient(
            text=text,
            color1=scheme['background'],
            color2=gradient_end,
            text_color=text_color,
            font_size=font_size,
            auto_size=auto_size,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            auto_stroke=auto_stroke,
            enable_html=enable_html
        )
    else:
        image = generator.create_text_image(
            text=text,
            font_size=font_size,
            text_color=text_color,
            background_color=scheme['background'],
            alignment=text_align,
            auto_size=auto_size,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            auto_stroke=auto_stroke,
            enable_html=enable_html
        )
    
    if save_local:
        filepath = utils.save_image_locally(image, slot=slot)
        print(f"Image saved locally: {filepath}")
    
    result = uploader.upload_image(slot, image)
    
    if result['success']:
        print(f"Success: Successfully uploaded to slot {slot}")
        print(f"  Status: {result['status_code']}")
        print(f"  Response: {result['message']}")
    else:
        print(f"Error: Failed to upload to slot {slot}")
        print(f"  Error: {result['message']}")
    
    return result

def upload_file(slot: int, file_path: str):
    uploader = DisplayUploader()
    
    result = uploader.upload_image(slot, file_path)
    
    if result['success']:
        print(f"Success: Successfully uploaded {file_path} to slot {slot}")
        print(f"  Status: {result['status_code']}")
        print(f"  Response: {result['message']}")
    else:
        print(f"Error: Failed to upload {file_path} to slot {slot}")
        print(f"  Error: {result['message']}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Generate and upload images to display device')
    
    # Main arguments with proper flags
    parser.add_argument('--slot', type=int, choices=[1, 2, 3, 4, 5], default=1,
                       help='Display slot number (default: 1)')
    parser.add_argument('--text', type=str,
                       help='Text to display (if not provided, use --file)')
    parser.add_argument('--file', type=str,
                       help='Image file to upload (alternative to --text)')
    
    # Font and styling
    parser.add_argument('--font-size', type=str, default='auto',
                       help='Font size (number or "auto", default: auto)')
    parser.add_argument('--font-color', type=str,
                       help='Text color (name, hex, or r,g,b format)')
    parser.add_argument('--color-scheme', type=str, default='default',
                       choices=list(ImageConfig.COLOR_SCHEMES.keys()),
                       help='Color scheme (default: default)')
    parser.add_argument('--text-align', type=str, default='center',
                       choices=['left', 'center', 'right', 'justify'],
                       help='Text alignment (default: center)')
    
    # Text stroke options
    parser.add_argument('--text-stroke', action='store_true',
                       help='Enable text stroke/outline (auto-enabled for colored text)')
    parser.add_argument('--stroke-width', type=int, default=0,
                       help='Stroke width in pixels (default: 0=auto)')
    parser.add_argument('--stroke-color', type=str,
                       help='Stroke color (name, hex, or r,g,b)')
    parser.add_argument('--no-auto-stroke', action='store_true',
                       help='Disable automatic stroke for colored text')
    
    # HTML formatting
    parser.add_argument('--html', action='store_true',
                       help='Enable HTML formatting (supports <b>, <i>, <u> tags)')
    # Keep --alignment for backward compatibility
    parser.add_argument('--alignment', type=str, dest='text_align_legacy',
                       choices=['left', 'center', 'right', 'justify'],
                       help=argparse.SUPPRESS)  # Hidden for backward compatibility
    
    # Padding arguments
    parser.add_argument('--padding-top', type=int,
                       help=f'Top padding (default: {ImageConfig.PADDING_TOP})')
    parser.add_argument('--padding-bottom', type=int,
                       help=f'Bottom padding (default: {ImageConfig.PADDING_BOTTOM})')
    parser.add_argument('--padding-left', type=int,
                       help=f'Left padding (default: {ImageConfig.PADDING_LEFT})')
    parser.add_argument('--padding-right', type=int,
                       help=f'Right padding (default: {ImageConfig.PADDING_RIGHT})')
    parser.add_argument('--padding', type=int,
                       help='Set all paddings at once')
    
    # Gradient options
    parser.add_argument('--gradient', action='store_true',
                       help='Use gradient background')
    parser.add_argument('--gradient-end', type=str,
                       help='End color for gradient (hex or r,g,b)')
    
    # Other options
    parser.add_argument('--save-local', action='store_true',
                       help='Save image locally before uploading')
    parser.add_argument('--base-url', type=str, default=DisplayConfig.BASE_URL,
                       help=f'Display device URL (default: {DisplayConfig.BASE_URL})')
    
    args = parser.parse_args()
    
    # Handle legacy mode (backward compatibility)
    if len(sys.argv) == 3 and not sys.argv[1].startswith('--'):
        try:
            slot = int(sys.argv[1])
            if 1 <= slot <= 5:
                if sys.argv[2].endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    print("Legacy mode: uploading file")
                    upload_file(slot, sys.argv[2])
                    return
                else:
                    # Legacy text mode: python main.py <slot> text "<text>"
                    pass
        except ValueError:
            pass
    
    # Legacy text mode with 4 args: python main.py <slot> text "<text>"
    if len(sys.argv) == 4 and not sys.argv[1].startswith('--'):
        try:
            slot = int(sys.argv[1])
            if 1 <= slot <= 5 and sys.argv[2] == 'text':
                print("Legacy mode: generating text")
                create_and_upload_text(slot=slot, text=sys.argv[3])
                return
        except ValueError:
            pass
    
    if args.base_url:
        DisplayConfig.BASE_URL = args.base_url
    
    # Validate that either text or file is provided
    if not args.text and not args.file:
        parser.error("Either --text or --file must be provided")
    
    if args.text and args.file:
        parser.error("Cannot use both --text and --file")
    
    # Handle padding
    padding_top = args.padding_top
    padding_bottom = args.padding_bottom
    padding_left = args.padding_left
    padding_right = args.padding_right
    
    # If --padding is set, override individual values
    if args.padding is not None:
        padding_top = padding_top or args.padding
        padding_bottom = padding_bottom or args.padding
        padding_left = padding_left or args.padding
        padding_right = padding_right or args.padding
    
    if args.text:
        # Parse font size
        auto_size = False
        font_size = None
        if args.font_size.lower() == 'auto':
            auto_size = True
        else:
            try:
                font_size = int(args.font_size)
            except ValueError:
                print(f"Invalid font-size: {args.font_size}. Using auto.")
                auto_size = True
        
        # Handle both --text-align and legacy --alignment
        text_align = args.text_align
        if hasattr(args, 'text_align_legacy') and args.text_align_legacy:
            text_align = args.text_align_legacy
        
        create_and_upload_text(
            slot=args.slot,
            text=args.text,
            font_size=font_size,
            auto_size=auto_size,
            font_color=args.font_color,
            color_scheme=args.color_scheme,
            text_align=text_align,
            save_local=args.save_local,
            gradient=args.gradient,
            gradient_end=args.gradient_end,
            padding_top=padding_top,
            padding_bottom=padding_bottom,
            padding_left=padding_left,
            padding_right=padding_right,
            text_stroke=args.text_stroke,
            stroke_width=args.stroke_width,
            stroke_color=args.stroke_color,
            no_auto_stroke=args.no_auto_stroke,
            enable_html=args.html
        )
    elif args.file:
        upload_file(args.slot, args.file)

if __name__ == "__main__":
    main()
