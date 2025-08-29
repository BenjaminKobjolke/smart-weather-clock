#!/usr/bin/env python3

import io
import requests
from PIL import Image, ImageOps
from typing import Optional, Union
from config import DisplayConfig
import os

class DisplayUploader:
    def __init__(self, base_url: str = DisplayConfig.BASE_URL):
        self.base_url = base_url
        self.timeout = DisplayConfig.TIMEOUT
        self.image_width = DisplayConfig.IMAGE_WIDTH
        self.image_height = DisplayConfig.IMAGE_HEIGHT
        self.jpeg_quality = DisplayConfig.JPEG_QUALITY
    
    def upload_image(self, 
                    slot: int,
                    image: Union[Image.Image, str, bytes],
                    filename: Optional[str] = None) -> dict:
        
        if slot not in DisplayConfig.SLOTS:
            raise ValueError(f"Slot must be one of {DisplayConfig.SLOTS}")
        
        if isinstance(image, str):
            jpeg_bytes = self._process_image_file(image)
        elif isinstance(image, Image.Image):
            jpeg_bytes = self._process_pil_image(image)
        elif isinstance(image, bytes):
            jpeg_bytes = image
        else:
            raise TypeError("Image must be a file path, PIL Image, or bytes")
        
        if filename is None:
            filename = f"file{slot}.jpg"
        elif not filename.endswith('.jpg'):
            filename = f"{filename}.jpg"
        
        return self._upload_to_display(slot, jpeg_bytes, filename)
    
    def _process_image_file(self, file_path: str) -> bytes:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        img = Image.open(file_path)
        return self._process_pil_image(img)
    
    def _process_pil_image(self, img: Image.Image) -> bytes:
        img = ImageOps.exif_transpose(img)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        w, h = img.size
        if w != self.image_width or h != self.image_height:
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((self.image_width, self.image_height), Image.Resampling.LANCZOS)
        
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=self.jpeg_quality, optimize=True)
        return buf.getvalue()
    
    def _upload_to_display(self, slot: int, jpeg_bytes: bytes, filename: str) -> dict:
        files = [
            ('imageFile', (filename, io.BytesIO(jpeg_bytes), 'image/jpeg'))
        ]
        
        try:
            response = requests.post(
                f"{self.base_url}/upload",
                files=files,
                timeout=self.timeout
            )
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'message': response.text,
                'slot': slot,
                'filename': filename
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'status_code': None,
                'message': str(e),
                'slot': slot,
                'filename': filename
            }
    
    def test_connection(self) -> bool:
        try:
            response = requests.get(
                self.base_url,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def batch_upload(self, images: dict) -> list:
        results = []
        for slot, image in images.items():
            if slot in DisplayConfig.SLOTS:
                result = self.upload_image(slot, image)
                results.append(result)
        return results