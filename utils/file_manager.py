#!/usr/bin/env python3
"""
utils/file_manager.py
Enterprise File Management System for SDX Project Manager
Fixed version with comprehensive error handling and security
"""

import os
import uuid
import hashlib
import magic
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, BinaryIO, Union
import logging
import shutil
import zipfile
from PIL import Image
import mimetypes
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import json
import tempfile
import contextlib
from threading import Lock
import time

logger = logging.getLogger(__name__)


class FileType(Enum):
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    CODE = "code"
    DATA = "data"
    OTHER = "other"


@dataclass
class FileMetadata:
    """Enhanced file metadata with validation"""

    file_id: str
    original_name: str
    file_path: str
    file_size: int
    mime_type: str
    file_type: FileType
    checksum: str
    uploaded_by: int
    upload_date: datetime
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    virus_scan_result: Optional[str] = None
    backup_path: Optional[str] = None
    expiry_date: Optional[datetime] = None
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_type": self.file_type.value,
            "checksum": self.checksum,
            "uploaded_by": self.uploaded_by,
            "upload_date": self.upload_date.isoformat(),
            "last_accessed": (
                self.last_accessed.isoformat() if self.last_accessed else None
            ),
            "tags": self.tags,
            "is_public": self.is_public,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "virus_scan_result": self.virus_scan_result,
            "backup_path": self.backup_path,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "version": self.version,
        }


class FileSecurityError(Exception):
    """File security related errors"""

    pass


class FileQuotaError(Exception):
    """File quota exceeded errors"""

    pass


class FileValidationError(Exception):
    """File validation errors"""

    pass


class FileManager:
    """Enterprise-grade file management system with comprehensive security"""

    def __init__(self, db_manager, config: Dict[str, Any]):
        self.db = db_manager
        self.config = config
        self.base_path = Path(config.get("upload_path", "./uploads"))
        self.max_file_size = config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        self.max_total_size = config.get(
            "max_total_size", 10 * 1024 * 1024 * 1024
        )  # 10GB
        self.allowed_extensions = set(config.get("allowed_extensions", []))
        self.blocked_extensions = set(
            config.get(
                "blocked_extensions",
                ["exe", "bat", "cmd", "com", "pif", "scr", "vbs", "js", "jar"],
            )
        )
        self.virus_scan_enabled = config.get("virus_scan_enabled", False)
        self.image_optimization = config.get("image_optimization", True)
        self.enable_backup = config.get("enable_backup", True)
        self.retention_days = config.get("retention_days", 365)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = Lock()

        # Initialize directories with proper permissions
        self._init_directories()

        # File type mappings
        self.type_mappings = {
            "image": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff"],
            "document": [
                "pdf",
                "doc",
                "docx",
                "xls",
                "xlsx",
                "ppt",
                "pptx",
                "txt",
                "rtf",
                "odt",
            ],
            "video": ["mp4", "avi", "mov", "wmv", "flv", "webm", "mkv", "m4v"],
            "audio": ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"],
            "archive": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"],
            "code": [
                "py",
                "js",
                "html",
                "css",
                "sql",
                "json",
                "xml",
                "yaml",
                "yml",
                "md",
            ],
            "data": ["csv", "tsv", "json", "xml", "yaml", "yml", "log"],
        }

    def _init_directories(self) -> None:
        """Initialize directory structure with security"""
        try:
            directories = [
                self.base_path,
                self.base_path / "documents",
                self.base_path / "images",
                self.base_path / "videos",
                self.base_path / "archives",
                self.base_path / "temp",
                self.base_path / "quarantine",
                self.base_path / "backup",
            ]

            for dir_path in directories:
                dir_path.mkdir(parents=True, exist_ok=True)
                # Set secure permissions (owner read/write only)
                os.chmod(dir_path, 0o750)

            logger.info(f"File management directories initialized at {self.base_path}")

        except Exception as e:
            logger.error(f"Failed to initialize directories: {e}")
            raise

    def _get_file_type(self, filename: str, mime_type: str) -> FileType:
        """Determine file type from extension and MIME type"""
        try:
            extension = Path(filename).suffix.lower().lstrip(".")

            for file_type, extensions in self.type_mappings.items():
                if extension in extensions:
                    return FileType(file_type)

            # Fallback to MIME type analysis
            if mime_type.startswith("image/"):
                return FileType.IMAGE
            elif mime_type.startswith("video/"):
                return FileType.VIDEO
            elif mime_type.startswith("audio/"):
                return FileType.AUDIO
            elif mime_type.startswith("text/"):
                return FileType.DOCUMENT

            return FileType.OTHER

        except Exception:
            return FileType.OTHER

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum for file integrity"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            raise

    def _validate_file_security(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> bool:
        """Comprehensive file security validation"""
        try:
            # Extension validation
            extension = Path(filename).suffix.lower().lstrip(".")
            if extension in self.blocked_extensions:
                raise FileSecurityError(f"File extension '{extension}' is not allowed")

            if self.allowed_extensions and extension not in self.allowed_extensions:
                raise FileSecurityError(
                    f"File extension '{extension}' is not in allowed list"
                )

            # Size validation
            if len(file_content) > self.max_file_size:
                raise FileValidationError(f"File size exceeds maximum allowed size")

            # MIME type validation
            if not mime_type or mime_type == "application/octet-stream":
                detected_mime = magic.from_buffer(file_content, mime=True)
                if detected_mime != mime_type:
                    logger.warning(
                        f"MIME type mismatch: declared={mime_type}, detected={detected_mime}"
                    )

            # Basic malware signature check
            suspicious_patterns = [
                b"eval(",
                b"exec(",
                b"system(",
                b"shell_exec(",
                b"<script",
                b"javascript:",
                b"vbscript:",
                b"<?php",
                b"<%",
                b"${",
                b"#{",
            ]

            file_content_lower = file_content.lower()
            for pattern in suspicious_patterns:
                if pattern in file_content_lower:
                    raise FileSecurityError(f"Suspicious content detected in file")

            return True

        except (FileSecurityError, FileValidationError):
            raise
        except Exception as e:
            logger.error(f"File security validation failed: {e}")
            raise FileSecurityError(f"File validation failed: {str(e)}")

    def _check_quota(self, user_id: int, file_size: int) -> bool:
        """Check if user has sufficient quota"""
        try:
            # Get current usage
            query = """
                SELECT COALESCE(SUM(file_size), 0) as total_size 
                FROM files 
                WHERE uploaded_by = ? AND deleted_at IS NULL
            """
            result = self.db.execute(query, (user_id,)).fetchone()
            current_usage = result[0] if result else 0

            if current_usage + file_size > self.max_total_size:
                raise FileQuotaError(f"Storage quota exceeded")

            return True

        except Exception as e:
            logger.error(f"Quota check failed: {e}")
            return False

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: int,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        tags: List[str] = None,
        is_public: bool = False,
    ) -> FileMetadata:
        """Upload file with comprehensive validation and processing"""

        upload_start = time.time()
        temp_file_path = None

        try:
            # Sanitize filename
            safe_filename = self._sanitize_filename(filename)

            # Detect MIME type
            mime_type = magic.from_buffer(file_content, mime=True)

            # Security validation
            self._validate_file_security(file_content, safe_filename, mime_type)

            # Quota check
            self._check_quota(user_id, len(file_content))

            # Generate unique file ID and paths
            file_id = str(uuid.uuid4())
            file_type = self._get_file_type(safe_filename, mime_type)

            # Create directory structure
            type_dir = self.base_path / file_type.value
            type_dir.mkdir(exist_ok=True)

            final_path = type_dir / f"{file_id}_{safe_filename}"

            # Write file to temporary location first
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = Path(temp_file.name)
                temp_file.write(file_content)

            # Calculate checksum
            checksum = self._calculate_checksum(temp_file_path)

            # Check for duplicates
            existing_file = await self._check_duplicate(checksum, user_id)
            if existing_file:
                temp_file_path.unlink()
                logger.info(
                    f"Duplicate file detected, returning existing: {existing_file.file_id}"
                )
                return existing_file

            # Move to final location
            shutil.move(str(temp_file_path), str(final_path))
            os.chmod(final_path, 0o640)

            # Image optimization
            if file_type == FileType.IMAGE and self.image_optimization:
                await self._optimize_image(final_path)

            # Create backup if enabled
            backup_path = None
            if self.enable_backup:
                backup_path = await self._create_backup(final_path, file_id)

            # Create metadata
            metadata = FileMetadata(
                file_id=file_id,
                original_name=filename,
                file_path=str(final_path),
                file_size=len(file_content),
                mime_type=mime_type,
                file_type=file_type,
                checksum=checksum,
                uploaded_by=user_id,
                upload_date=datetime.now(),
                tags=tags or [],
                is_public=is_public,
                project_id=project_id,
                task_id=task_id,
                backup_path=backup_path,
                expiry_date=datetime.now() + timedelta(days=self.retention_days),
            )

            # Save to database
            await self._save_metadata(metadata)

            # Log successful upload
            upload_time = time.time() - upload_start
            logger.info(f"File uploaded successfully: {file_id} in {upload_time:.2f}s")

            return metadata

        except Exception as e:
            # Cleanup on failure
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
            logger.error(f"File upload failed: {e}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security"""
        # Remove path separators and dangerous characters
        import re

        safe_name = re.sub(r'[<>:"/\\|?*]', "_", filename)
        safe_name = re.sub(r"\.+", ".", safe_name)  # Remove multiple dots
        safe_name = safe_name.strip(". ")  # Remove leading/trailing dots and spaces

        # Limit length
        if len(safe_name) > 255:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[: 255 - len(ext)] + ext

        return safe_name or "unnamed_file"

    async def _check_duplicate(
        self, checksum: str, user_id: int
    ) -> Optional[FileMetadata]:
        """Check for duplicate files by checksum"""
        try:
            query = """
                SELECT * FROM files 
                WHERE checksum = ? AND uploaded_by = ? AND deleted_at IS NULL
                LIMIT 1
            """
            result = self.db.execute(query, (checksum, user_id)).fetchone()

            if result:
                return FileMetadata(
                    file_id=result[0],
                    original_name=result[1],
                    file_path=result[2],
                    file_size=result[3],
                    mime_type=result[4],
                    file_type=FileType(result[5]),
                    checksum=result[6],
                    uploaded_by=result[7],
                    upload_date=datetime.fromisoformat(result[8]),
                    # Add other fields as needed
                )

            return None

        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return None

    async def _optimize_image(self, image_path: Path) -> None:
        """Optimize image files for web usage"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Resize if too large
                max_dimension = 2048
                if max(img.size) > max_dimension:
                    img.thumbnail(
                        (max_dimension, max_dimension), Image.Resampling.LANCZOS
                    )

                # Save with optimization
                img.save(image_path, optimize=True, quality=85, progressive=True)

            logger.info(f"Image optimized: {image_path}")

        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")

    async def _create_backup(self, file_path: Path, file_id: str) -> str:
        """Create backup copy of uploaded file"""
        try:
            backup_dir = self.base_path / "backup"
            backup_path = backup_dir / f"{file_id}_backup{file_path.suffix}"

            shutil.copy2(file_path, backup_path)
            return str(backup_path)

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None

    async def _save_metadata(self, metadata: FileMetadata) -> None:
        """Save file metadata to database"""
        try:
            query = """
                INSERT INTO files (
                    file_id, original_name, file_path, file_size, mime_type,
                    file_type, checksum, uploaded_by, upload_date, tags,
                    is_public, project_id, task_id, backup_path, expiry_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute(
                query,
                (
                    metadata.file_id,
                    metadata.original_name,
                    metadata.file_path,
                    metadata.file_size,
                    metadata.mime_type,
                    metadata.file_type.value,
                    metadata.checksum,
                    metadata.uploaded_by,
                    metadata.upload_date.isoformat(),
                    json.dumps(metadata.tags),
                    metadata.is_public,
                    metadata.project_id,
                    metadata.task_id,
                    metadata.backup_path,
                    metadata.expiry_date.isoformat() if metadata.expiry_date else None,
                ),
            )

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise

    async def get_file(self, file_id: str, user_id: int) -> Tuple[bytes, FileMetadata]:
        """Retrieve file with access control"""
        try:
            # Get metadata with permission check
            metadata = await self._get_file_metadata(file_id, user_id)
            if not metadata:
                raise FileNotFoundError(f"File not found or access denied: {file_id}")

            # Read file content
            file_path = Path(metadata.file_path)
            if not file_path.exists():
                logger.error(f"File not found on disk: {file_path}")
                raise FileNotFoundError(f"File not found on disk")

            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()

            # Update last accessed
            await self._update_last_accessed(file_id)

            return content, metadata

        except Exception as e:
            logger.error(f"File retrieval failed: {e}")
            raise

    async def _get_file_metadata(
        self, file_id: str, user_id: int
    ) -> Optional[FileMetadata]:
        """Get file metadata with access control"""
        try:
            query = """
                SELECT * FROM files 
                WHERE file_id = ? AND (uploaded_by = ? OR is_public = 1) 
                AND deleted_at IS NULL
            """
            result = self.db.execute(query, (file_id, user_id)).fetchone()

            if not result:
                return None

            return FileMetadata(
                file_id=result[0],
                original_name=result[1],
                file_path=result[2],
                file_size=result[3],
                mime_type=result[4],
                file_type=FileType(result[5]),
                checksum=result[6],
                uploaded_by=result[7],
                upload_date=datetime.fromisoformat(result[8]),
                # Add other fields as needed
            )

        except Exception as e:
            logger.error(f"Metadata retrieval failed: {e}")
            return None

    async def _update_last_accessed(self, file_id: str) -> None:
        """Update last accessed timestamp"""
        try:
            query = "UPDATE files SET last_accessed = ? WHERE file_id = ?"
            self.db.execute(query, (datetime.now().isoformat(), file_id))
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update last accessed: {e}")

    async def delete_file(
        self, file_id: str, user_id: int, permanent: bool = False
    ) -> bool:
        """Delete file with soft/hard delete options"""
        try:
            # Get file metadata
            metadata = await self._get_file_metadata(file_id, user_id)
            if not metadata:
                return False

            if permanent:
                # Hard delete - remove file and database record
                file_path = Path(metadata.file_path)
                if file_path.exists():
                    file_path.unlink()

                # Remove backup if exists
                if metadata.backup_path:
                    backup_path = Path(metadata.backup_path)
                    if backup_path.exists():
                        backup_path.unlink()

                # Delete from database
                query = "DELETE FROM files WHERE file_id = ?"
                self.db.execute(query, (file_id,))
            else:
                # Soft delete - mark as deleted
                query = "UPDATE files SET deleted_at = ? WHERE file_id = ?"
                self.db.execute(query, (datetime.now().isoformat(), file_id))

            self.db.commit()
            logger.info(f"File {'permanently ' if permanent else ''}deleted: {file_id}")
            return True

        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False

    async def cleanup_expired_files(self) -> int:
        """Clean up expired files based on retention policy"""
        try:
            cleanup_count = 0
            current_time = datetime.now()

            # Get expired files
            query = """
                SELECT file_id, file_path, backup_path 
                FROM files 
                WHERE expiry_date < ? AND deleted_at IS NULL
            """
            expired_files = self.db.execute(
                query, (current_time.isoformat(),)
            ).fetchall()

            for file_record in expired_files:
                file_id, file_path, backup_path = file_record

                try:
                    # Remove file
                    if file_path and Path(file_path).exists():
                        Path(file_path).unlink()

                    # Remove backup
                    if backup_path and Path(backup_path).exists():
                        Path(backup_path).unlink()

                    # Mark as deleted
                    update_query = "UPDATE files SET deleted_at = ? WHERE file_id = ?"
                    self.db.execute(update_query, (current_time.isoformat(), file_id))
                    cleanup_count += 1

                except Exception as e:
                    logger.error(f"Failed to cleanup file {file_id}: {e}")

            self.db.commit()
            logger.info(f"Cleaned up {cleanup_count} expired files")
            return cleanup_count

        except Exception as e:
            logger.error(f"Cleanup process failed: {e}")
            return 0

    def get_storage_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            base_query = """
                SELECT 
                    COUNT(*) as file_count,
                    SUM(file_size) as total_size,
                    file_type,
                    COUNT(CASE WHEN is_public = 1 THEN 1 END) as public_files
                FROM files 
                WHERE deleted_at IS NULL
            """

            params = []
            if user_id:
                base_query += " AND uploaded_by = ?"
                params.append(user_id)

            base_query += " GROUP BY file_type"

            results = self.db.execute(base_query, params).fetchall()

            stats = {
                "total_files": 0,
                "total_size": 0,
                "public_files": 0,
                "by_type": {},
            }

            for row in results:
                file_count, total_size, file_type, public_files = row
                stats["total_files"] += file_count
                stats["total_size"] += total_size or 0
                stats["public_files"] += public_files or 0
                stats["by_type"][file_type] = {
                    "count": file_count,
                    "size": total_size or 0,
                }

            # Add quota information if user-specific
            if user_id:
                stats["quota_used_percent"] = (
                    stats["total_size"] / self.max_total_size
                ) * 100
                stats["quota_remaining"] = self.max_total_size - stats["total_size"]

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
