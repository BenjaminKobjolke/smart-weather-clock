#!/usr/bin/env python3

class DisplayConfig:
    BASE_URL = "http://192.168.10.154"
    TIMEOUT = 10
    IMAGE_WIDTH = 240
    IMAGE_HEIGHT = 240
    JPEG_QUALITY = 70
    SLOTS = [1, 2, 3, 4, 5]

class ImageConfig:
    DEFAULT_BACKGROUND_COLOR = (0, 0, 0)
    DEFAULT_TEXT_COLOR = (255, 255, 255)
    DEFAULT_FONT_SIZE = 24
    PADDING = 0  # Legacy single padding value
    LINE_SPACING = 10  # Increased from 5 for better readability
    
    # Individual padding configuration
    PADDING_TOP = 0
    PADDING_BOTTOM = 25  # Extra space for IP address display
    PADDING_LEFT = 0
    PADDING_RIGHT = 0
    
    # Auto font size configuration
    MIN_AUTO_FONT_SIZE = 10
    MAX_AUTO_FONT_SIZE = 200  # Increased max size for better space usage
    AUTO_SIZE_ITERATIONS = 2
    AUTO_SIZE_PADDING = 10  # Smaller padding for auto-sized text
    AUTO_SIZE_PADDING_BOTTOM = 35  # Extra bottom padding for auto-sized text
    
    FONT_SIZES = {
        'small': 18,
        'medium': 24,
        'large': 32,
        'xlarge': 48
    }
    
    # Named colors for easy reference
    COLORS = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'pink': (255, 192, 203),
        'lime': (50, 205, 50),
        'navy': (0, 0, 128),
        'gray': (128, 128, 128),
        'silver': (192, 192, 192),
        'brown': (165, 42, 42),
        'gold': (255, 215, 0),
        'turquoise': (64, 224, 208)
    }
    
    COLOR_SCHEMES = {
        'default': {
            'background': (0, 0, 0),
            'text': (255, 255, 255)
        },
        'blue': {
            'background': (0, 50, 100),
            'text': (255, 255, 255)
        },
        'green': {
            'background': (0, 80, 40),
            'text': (255, 255, 255)
        },
        'red': {
            'background': (100, 20, 20),
            'text': (255, 255, 255)
        },
        'light': {
            'background': (240, 240, 240),
            'text': (20, 20, 20)
        },
        'purple': {
            'background': (60, 20, 80),
            'text': (255, 200, 255)
        }
    }