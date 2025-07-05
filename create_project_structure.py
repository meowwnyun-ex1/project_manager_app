#!/usr/bin/env python3
"""
create_project_structure.py
Create complete project folder structure for SDX Project Manager
"""

import os
from pathlib import Path


def create_project_structure():
    """Create complete project folder structure"""

    # Main project structure
    folders = [
        # Core application
        "app",
        "modules",
        "config",
        "utils",
        # Static assets
        "static/css",
        "static/js",
        "static/images/logos",
        "static/images/slides",
        "static/images/icons",
        "static/fonts",
        # Data storage (file-based to save DB space)
        "data/uploads/documents",  # PDF, Word, Excel files
        "data/uploads/images",  # User uploaded images
        "data/uploads/avatars",  # Profile pictures
        "data/exports",  # Generated reports
        "data/backups",  # Database backups
        "data/temp",  # Temporary files
        "data/cache",  # Application cache
        # Logs and monitoring
        "logs/app",
        "logs/database",
        "logs/errors",
        "logs/performance",
        # Configuration
        ".streamlit",
        "config/environments",
        "config/certificates",
        # Documentation
        "docs/api",
        "docs/user_guide",
        "docs/deployment",
        # Development
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        # Deployment
        "docker",
        "scripts",
        # Reports and analytics
        "reports/monthly",
        "reports/quarterly",
        "reports/custom",
    ]

    print("🏗️  Creating SDX Project Manager structure...")

    created_count = 0
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"📁 {folder}/")
            created_count += 1
        except Exception as e:
            print(f"❌ Failed to create {folder}: {e}")

    # Create gitkeep files for empty directories
    gitkeep_folders = [
        "data/uploads/documents",
        "data/uploads/images",
        "data/uploads/avatars",
        "data/exports",
        "data/backups",
        "data/temp",
        "data/cache",
        "logs/app",
        "logs/database",
        "logs/errors",
        "logs/performance",
        "reports/monthly",
        "reports/quarterly",
        "reports/custom",
    ]

    print("\n📄 Creating .gitkeep files...")
    for folder in gitkeep_folders:
        gitkeep_path = Path(folder) / ".gitkeep"
        try:
            gitkeep_path.write_text("# Keep this directory in Git\n")
            print(f"📝 {gitkeep_path}")
        except Exception as e:
            print(f"❌ Failed to create {gitkeep_path}: {e}")

    # Create important config files
    create_config_files()

    print(f"\n✅ Created {created_count} directories")
    print("🎯 Structure optimized for 10GB database limit")


def create_config_files():
    """Create essential configuration files"""

    configs = {
        # File upload configuration
        "config/file_config.yaml": """
# File Upload Configuration
file_upload:
  max_file_size_mb: 50
  allowed_extensions:
    documents: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
    images: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    archives: ['.zip', '.rar', '.7z']
  
  # Storage strategy (file = local storage, db = database blob)
  storage_strategy:
    small_files: 'db'      # < 1MB store in database
    large_files: 'file'    # >= 1MB store as files
    images: 'file'         # Always store images as files
    
  # Image optimization
  image_optimization:
    thumbnails: true
    max_width: 1920
    max_height: 1080
    quality: 85
    
  # Auto cleanup
  cleanup:
    temp_files_after_hours: 24
    cache_files_after_days: 7
    old_backups_after_days: 30
""",
        # Database optimization config
        "config/database_config.yaml": """
# Database Configuration for Space Optimization
database:
  # Connection settings
  connection:
    pool_size: 5
    max_overflow: 10
    pool_timeout: 30
    
  # Space optimization
  optimization:
    # Store large text as files instead of database
    large_text_threshold_chars: 5000
    
    # Compress data before storing
    compress_json_data: true
    compress_log_data: true
    
    # Auto-archive old data
    archive_policy:
      completed_projects_after_months: 12
      old_logs_after_months: 3
      temp_data_after_days: 7
      
  # Backup strategy
  backup:
    auto_backup: true
    backup_schedule: "0 2 * * *"  # Daily at 2 AM
    retention_days: 30
    compress_backups: true
""",
        # Static files configuration
        "static/config.json": """
{
  "cdn": {
    "use_cdn": false,
    "base_url": "https://cdn.denso.com/sdx/"
  },
  "cache": {
    "static_files_cache_days": 30,
    "image_cache_days": 7
  },
  "compression": {
    "enable_gzip": true,
    "minify_css": true,
    "minify_js": true
  }
}
""",
        # File management utilities
        "utils/file_manager.py": '''
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
''',
        # .gitignore for data folders
        "data/.gitignore": """
# Ignore all uploaded files but keep structure
uploads/**/*
!uploads/*/.gitkeep

# Ignore generated exports and backups
exports/**/*
!exports/.gitkeep

backups/**/*
!backups/.gitkeep

# Ignore cache and temp files
cache/**/*
temp/**/*

# Keep logs structure but ignore log files
logs/**/*.log
logs/**/*.txt
""",
        # README for project structure
        "README_STRUCTURE.md": """
# SDX Project Manager - Folder Structure

## 📁 Project Organization

### Core Application
- `app/` - Main application entry point
- `modules/` - Business logic modules  
- `config/` - Configuration files
- `utils/` - Utility functions

### Static Assets (for UI)
- `static/css/` - Stylesheets
- `static/js/` - JavaScript files
- `static/images/logos/` - Company logos
- `static/images/slides/` - Login page slideshow
- `static/images/icons/` - UI icons
- `static/fonts/` - Custom fonts

### Data Storage (File-based to save DB space)
- `data/uploads/documents/` - PDF, Word, Excel files
- `data/uploads/images/` - User uploaded images  
- `data/uploads/avatars/` - Profile pictures
- `data/exports/` - Generated reports (CSV, PDF)
- `data/backups/` - Database backups
- `data/temp/` - Temporary processing files
- `data/cache/` - Application cache

### Logs & Monitoring  
- `logs/app/` - Application logs
- `logs/database/` - Database operation logs
- `logs/errors/` - Error logs
- `logs/performance/` - Performance monitoring

### Development & Deployment
- `tests/` - Unit and integration tests
- `docker/` - Docker configurations
- `scripts/` - Deployment and utility scripts
- `docs/` - Documentation

## 🎯 Space Optimization Strategy

### Database (10GB Limit)
- **Store in DB**: Small files < 1MB, metadata, structured data
- **Store as Files**: Large documents, images, exports
- **Compression**: JSON data, logs, backups
- **Auto-cleanup**: Temp files, old logs, cached data

### File Storage Guidelines
- **Images**: Always store as files, auto-optimize, create thumbnails
- **Documents**: Store large files (>1MB) as files, small files in DB
- **Exports**: Generate as files, auto-cleanup after 30 days
- **Logs**: Compress and rotate, keep 3 months max

### Best Practices
- Use file deduplication (MD5 hashes)
- Implement auto-cleanup routines
- Compress backups
- Monitor disk usage
- Regular maintenance tasks

## 🔧 Configuration Files
- `config/file_config.yaml` - File upload settings
- `config/database_config.yaml` - DB optimization settings
- `static/config.json` - Static file settings
- `utils/file_manager.py` - File management utilities
""",
    }

    print("\n📝 Creating configuration files...")
    for file_path, content in configs.items():
        try:
            # Create parent directory if needed
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"📄 {file_path}")

        except Exception as e:
            print(f"❌ Failed to create {file_path}: {e}")


if __name__ == "__main__":
    create_project_structure()

    print("\n" + "=" * 60)
    print("🎉 SDX Project Manager structure created!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("1. Copy your images to static/images/")
    print("2. Configure database connection")
    print("3. Run: python app.py")
    print("\n📊 Optimized for 10GB database limit:")
    print("• Small files (<1MB) → Database")
    print("• Large files (≥1MB) → File system")
    print("• Images → Always files + thumbnails")
    print("• Auto-cleanup enabled")
    print("\n🔧 See README_STRUCTURE.md for details")
