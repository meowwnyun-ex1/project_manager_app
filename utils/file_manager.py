"""
File Management Utilities
Handles file uploads, storage, and optimization to save database space
"""

import os
import shutil
from pathlib import Path
import hashlib
from PIL import Image
import gzip
import json
from typing import Optional, Tuple

class FileManager:
    """Manages file storage with database space optimization"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.uploads_path = self.base_path / "uploads"
        self.cache_path = self.base_path / "cache"
        
        # Size thresholds (bytes)
        self.SMALL_FILE_THRESHOLD = 1024 * 1024  # 1MB
        self.LARGE_TEXT_THRESHOLD = 5000  # 5K characters
        
    def should_store_in_db(self, file_path: str, file_size: int) -> bool:
        """Determine if file should be stored in database or filesystem"""
        
        # Always store small files in database
        if file_size < self.SMALL_FILE_THRESHOLD:
            return True
            
        # Never store images in database (too large)
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        if Path(file_path).suffix.lower() in image_extensions:
            return False
            
        # Store medium-sized documents in database
        if file_size < 5 * 1024 * 1024:  # 5MB
            return True
            
        return False
        
    def optimize_image(self, image_path: str, max_width: int = 1920, 
                      max_height: int = 1080, quality: int = 85) -> str:
        """Optimize image size and quality"""
        
        try:
            with Image.open(image_path) as img:
                # Calculate new size maintaining aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save optimized image
                optimized_path = image_path.replace('.', '_optimized.')
                img.save(optimized_path, optimize=True, quality=quality)
                
                return optimized_path
                
        except Exception as e:
            print(f"Image optimization failed: {e}")
            return image_path
            
    def create_thumbnail(self, image_path: str, size: Tuple[int, int] = (300, 300)) -> str:
        """Create thumbnail for images"""
        
        try:
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                thumbnail_path = image_path.replace('.', '_thumb.')
                img.save(thumbnail_path, optimize=True, quality=80)
                
                return thumbnail_path
                
        except Exception as e:
            print(f"Thumbnail creation failed: {e}")
            return image_path
            
    def get_file_hash(self, file_path: str) -> str:
        """Generate MD5 hash for file deduplication"""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def compress_json_data(self, data: dict) -> bytes:
        """Compress JSON data before database storage"""
        
        json_str = json.dumps(data, separators=(',', ':'))
        return gzip.compress(json_str.encode('utf-8'))
        
    def decompress_json_data(self, compressed_data: bytes) -> dict:
        """Decompress JSON data from database"""
        
        json_str = gzip.decompress(compressed_data).decode('utf-8')
        return json.loads(json_str)
        
    def cleanup_temp_files(self, hours_old: int = 24):
        """Clean up temporary files older than specified hours"""
        
        import time
        temp_path = self.base_path / "temp"
        current_time = time.time()
        
        for file_path in temp_path.rglob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (hours_old * 3600):
                    file_path.unlink()
                    print(f"Cleaned up: {file_path}")