#!/usr/bin/env python3
"""
utils/file_manager.py
Enterprise File Management System for SDX Project Manager
"""

import os
import uuid
import hashlib
import magic
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, BinaryIO
import logging
import shutil
import zipfile
from PIL import Image
import mimetypes
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor

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
    tags: List[str] = None
    is_public: bool = False
    project_id: Optional[int] = None
    task_id: Optional[int] = None


class FileManager:
    """Enterprise-grade file management system"""

    def __init__(self, db_manager, config: Dict[str, Any]):
        self.db = db_manager
        self.config = config
        self.base_path = Path(config.get("upload_path", "./uploads"))
        self.max_file_size = config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        self.allowed_extensions = config.get("allowed_extensions", [])
        self.virus_scan_enabled = config.get("virus_scan_enabled", False)
        self.image_optimization = config.get("image_optimization", True)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Initialize directories
        self._init_directories()

        # File type mappings
        self.type_mappings = {
            "image": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"],
            "document": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"],
            "video": ["mp4", "avi", "mov", "wmv", "flv", "webm"],
            "audio": ["mp3", "wav", "flac", "aac", "ogg"],
            "archive": ["zip", "rar", "7z", "tar", "gz"],
            "code": ["py", "js", "html", "css", "sql", "json", "xml", "yaml"],
            "data": ["csv", "json", "xml", "sql", "log"],
        }

    def _init_directories(self):
        """Initialize required directories"""
        directories = ["uploads", "temp", "thumbnails", "processed", "quarantine"]

        for dir_name in directories:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        user_id: int,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        tags: List[str] = None,
        is_public: bool = False,
    ) -> Dict[str, Any]:
        """Upload file with comprehensive validation and processing"""

        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())

            # Validate file
            validation_result = await self._validate_file(file_data, filename)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Determine file type
            file_extension = Path(filename).suffix.lower().lstrip(".")
            file_type = self._get_file_type(file_extension)
            mime_type = validation_result["mime_type"]

            # Generate secure filename
            secure_filename = self._generate_secure_filename(filename, file_id)
            file_path = self.base_path / "uploads" / secure_filename

            # Calculate checksum
            file_data.seek(0)
            checksum = hashlib.sha256(file_data.read()).hexdigest()
            file_data.seek(0)

            # Check for duplicates
            duplicate_check = await self._check_duplicate(checksum, user_id)
            if duplicate_check:
                return {
                    "success": True,
                    "file_id": duplicate_check["file_id"],
                    "message": "File already exists",
                    "duplicate": True,
                }

            # Save file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_data.read())

            # Get file size
            file_size = file_path.stat().st_size

            # Create metadata
            metadata = FileMetadata(
                file_id=file_id,
                original_name=filename,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=mime_type,
                file_type=file_type,
                checksum=checksum,
                uploaded_by=user_id,
                upload_date=datetime.now(),
                tags=tags or [],
                is_public=is_public,
                project_id=project_id,
                task_id=task_id,
            )

            # Save to database
            db_result = await self._save_metadata_to_db(metadata)
            if not db_result["success"]:
                # Cleanup file if DB save fails
                file_path.unlink(missing_ok=True)
                return {"success": False, "error": "Database save failed"}

            # Post-processing
            await self._post_process_file(metadata)

            return {
                "success": True,
                "file_id": file_id,
                "filename": secure_filename,
                "size": file_size,
                "type": file_type.value,
                "url": self._generate_file_url(file_id),
            }

        except Exception as e:
            logger.error(f"File upload error: {e}")
            return {"success": False, "error": str(e)}

    async def _validate_file(
        self, file_data: BinaryIO, filename: str
    ) -> Dict[str, Any]:
        """Comprehensive file validation"""

        # Size check
        file_data.seek(0, 2)  # Seek to end
        size = file_data.tell()
        file_data.seek(0)  # Reset

        if size > self.max_file_size:
            return {
                "valid": False,
                "error": f"File too large. Max size: {self.max_file_size / 1024 / 1024:.1f}MB",
            }

        # Extension check
        extension = Path(filename).suffix.lower().lstrip(".")
        if self.allowed_extensions and extension not in self.allowed_extensions:
            return {
                "valid": False,
                "error": f'File type not allowed. Allowed: {", ".join(self.allowed_extensions)}',
            }

        # MIME type detection
        file_data.seek(0)
        file_header = file_data.read(1024)
        file_data.seek(0)

        try:
            mime_type = magic.from_buffer(file_header, mime=True)
        except:
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Security checks
        if await self._has_malicious_content(file_header, filename):
            return {
                "valid": False,
                "error": "File contains potentially malicious content",
            }

        # Virus scan (if enabled)
        if self.virus_scan_enabled:
            virus_result = await self._virus_scan(file_data)
            if not virus_result["clean"]:
                return {"valid": False, "error": "Virus detected"}

        return {"valid": True, "mime_type": mime_type}

    async def _has_malicious_content(self, file_header: bytes, filename: str) -> bool:
        """Check for malicious content patterns"""

        # Check for executable signatures
        malicious_signatures = [
            b"MZ",  # Windows PE
            b"\x7fELF",  # Linux ELF
            b"\xfe\xed\xfa",  # macOS Mach-O
            b"#!/bin/",  # Script shebangs
            b"<?php",  # PHP
            b"<script",  # JavaScript
        ]

        for signature in malicious_signatures:
            if file_header.startswith(signature):
                return True

        # Check filename for suspicious extensions
        suspicious_extensions = [".exe", ".bat", ".cmd", ".scr", ".vbs", ".js", ".jar"]
        return any(filename.lower().endswith(ext) for ext in suspicious_extensions)

    async def _virus_scan(self, file_data: BinaryIO) -> Dict[str, Any]:
        """Virus scanning (placeholder for external scanner integration)"""
        # In production, integrate with ClamAV or similar
        return {"clean": True, "scan_result": "No threats detected"}

    def _get_file_type(self, extension: str) -> FileType:
        """Determine file type from extension"""
        for file_type, extensions in self.type_mappings.items():
            if extension in extensions:
                return FileType(file_type)
        return FileType.OTHER

    def _generate_secure_filename(self, original_name: str, file_id: str) -> str:
        """Generate secure filename with UUID"""
        extension = Path(original_name).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{file_id[:8]}{extension}"

    async def _check_duplicate(
        self, checksum: str, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Check for duplicate files"""
        query = """
            SELECT FileID, OriginalName, FilePath 
            FROM Files 
            WHERE Checksum = ? AND UploadedBy = ?
        """

        result = self.db.execute_query(query, (checksum, user_id))
        return result[0] if result else None

    async def _save_metadata_to_db(self, metadata: FileMetadata) -> Dict[str, Any]:
        """Save file metadata to database"""
        try:
            query = """
                INSERT INTO Files (
                    FileID, OriginalName, FilePath, FileSize, MimeType, FileType,
                    Checksum, UploadedBy, UploadDate, Tags, IsPublic, ProjectID, TaskID
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            tags_json = ",".join(metadata.tags) if metadata.tags else ""

            self.db.execute_non_query(
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
                    metadata.upload_date,
                    tags_json,
                    metadata.is_public,
                    metadata.project_id,
                    metadata.task_id,
                ),
            )

            return {"success": True}

        except Exception as e:
            logger.error(f"Database save error: {e}")
            return {"success": False, "error": str(e)}

    async def _post_process_file(self, metadata: FileMetadata):
        """Post-process uploaded file"""

        if metadata.file_type == FileType.IMAGE:
            await self._process_image(metadata)
        elif metadata.file_type == FileType.DOCUMENT:
            await self._extract_document_metadata(metadata)
        elif metadata.file_type == FileType.ARCHIVE:
            await self._process_archive(metadata)

    async def _process_image(self, metadata: FileMetadata):
        """Process image files (thumbnails, optimization)"""
        try:
            if not self.image_optimization:
                return

            with Image.open(metadata.file_path) as img:
                # Create thumbnail
                thumbnail_path = (
                    self.base_path / "thumbnails" / f"{metadata.file_id}_thumb.jpg"
                )

                # Create thumbnail while maintaining aspect ratio
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)

                # Update database with thumbnail path
                update_query = "UPDATE Files SET ThumbnailPath = ? WHERE FileID = ?"
                self.db.execute_non_query(
                    update_query, (str(thumbnail_path), metadata.file_id)
                )

        except Exception as e:
            logger.error(f"Image processing error: {e}")

    async def _extract_document_metadata(self, metadata: FileMetadata):
        """Extract metadata from documents"""
        # Placeholder for document processing (PyPDF2, python-docx, etc.)
        pass

    async def _process_archive(self, metadata: FileMetadata):
        """Process archive files"""
        # Placeholder for archive processing
        pass

    def _generate_file_url(self, file_id: str) -> str:
        """Generate secure file access URL"""
        return f"/api/files/{file_id}"

    async def get_file(self, file_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get file information and check permissions"""

        query = """
            SELECT f.*, u.FirstName, u.LastName
            FROM Files f
            JOIN Users u ON f.UploadedBy = u.UserID
            WHERE f.FileID = ?
        """

        result = self.db.execute_query(query, (file_id,))
        if not result:
            return None

        file_info = result[0]

        # Check permissions
        if not self._check_file_access(file_info, user_id):
            return None

        # Update last accessed
        await self._update_last_accessed(file_id)

        return {
            "file_id": file_info["FileID"],
            "original_name": file_info["OriginalName"],
            "file_size": file_info["FileSize"],
            "mime_type": file_info["MimeType"],
            "file_type": file_info["FileType"],
            "upload_date": file_info["UploadDate"],
            "uploaded_by": f"{file_info['FirstName']} {file_info['LastName']}",
            "is_public": file_info["IsPublic"],
            "tags": file_info["Tags"].split(",") if file_info["Tags"] else [],
        }

    def _check_file_access(self, file_info: Dict[str, Any], user_id: int) -> bool:
        """Check if user has access to file"""

        # Public files
        if file_info["IsPublic"]:
            return True

        # Owner access
        if file_info["UploadedBy"] == user_id:
            return True

        # Project/Task member access
        if file_info["ProjectID"]:
            # Check if user is project member
            member_query = """
                SELECT 1 FROM ProjectMembers 
                WHERE ProjectID = ? AND UserID = ?
            """
            member_result = self.db.execute_query(
                member_query, (file_info["ProjectID"], user_id)
            )
            if member_result:
                return True

        return False

    async def _update_last_accessed(self, file_id: str):
        """Update last accessed timestamp"""
        query = "UPDATE Files SET LastAccessed = GETDATE() WHERE FileID = ?"
        self.db.execute_non_query(query, (file_id,))

    async def delete_file(self, file_id: str, user_id: int) -> Dict[str, Any]:
        """Delete file with permission checks"""

        # Get file info
        file_info = await self.get_file(file_id, user_id)
        if not file_info:
            return {"success": False, "error": "File not found or access denied"}

        try:
            # Get file path from database
            path_query = "SELECT FilePath, ThumbnailPath FROM Files WHERE FileID = ?"
            path_result = self.db.execute_query(path_query, (file_id,))

            if path_result:
                file_path = Path(path_result[0]["FilePath"])
                thumbnail_path = path_result[0]["ThumbnailPath"]

                # Delete physical files
                file_path.unlink(missing_ok=True)
                if thumbnail_path:
                    Path(thumbnail_path).unlink(missing_ok=True)

            # Delete from database
            delete_query = "DELETE FROM Files WHERE FileID = ?"
            self.db.execute_non_query(delete_query, (file_id,))

            return {"success": True, "message": "File deleted successfully"}

        except Exception as e:
            logger.error(f"File deletion error: {e}")
            return {"success": False, "error": str(e)}

    async def list_files(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        file_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """List files with filtering and pagination"""

        # Build query
        where_conditions = ["(f.UploadedBy = ? OR f.IsPublic = 1)"]
        params = [user_id]

        if project_id:
            where_conditions.append("f.ProjectID = ?")
            params.append(project_id)

        if file_type:
            where_conditions.append("f.FileType = ?")
            params.append(file_type)

        where_clause = " AND ".join(where_conditions)

        # Count query
        count_query = f"""
            SELECT COUNT(*) as total
            FROM Files f
            WHERE {where_clause}
        """

        count_result = self.db.execute_query(count_query, params)
        total = count_result[0]["total"] if count_result else 0

        # Data query with pagination
        offset = (page - 1) * per_page

        data_query = f"""
            SELECT f.*, u.FirstName, u.LastName
            FROM Files f
            JOIN Users u ON f.UploadedBy = u.UserID
            WHERE {where_clause}
            ORDER BY f.UploadDate DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        params.extend([offset, per_page])
        files = self.db.execute_query(data_query, params)

        # Format results
        formatted_files = []
        for file_info in files:
            formatted_files.append(
                {
                    "file_id": file_info["FileID"],
                    "original_name": file_info["OriginalName"],
                    "file_size": file_info["FileSize"],
                    "file_type": file_info["FileType"],
                    "upload_date": file_info["UploadDate"],
                    "uploaded_by": f"{file_info['FirstName']} {file_info['LastName']}",
                    "is_public": file_info["IsPublic"],
                    "url": self._generate_file_url(file_info["FileID"]),
                }
            )

        return {
            "files": formatted_files,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            },
        }

    async def cleanup_orphaned_files(self) -> Dict[str, Any]:
        """Clean up orphaned files and database entries"""

        cleaned_files = 0
        cleaned_db_entries = 0

        try:
            # Get all files from database
            db_files = self.db.execute_query("SELECT FileID, FilePath FROM Files")

            # Check physical files
            for file_info in db_files:
                file_path = Path(file_info["FilePath"])
                if not file_path.exists():
                    # Remove database entry
                    self.db.execute_non_query(
                        "DELETE FROM Files WHERE FileID = ?", (file_info["FileID"],)
                    )
                    cleaned_db_entries += 1

            # Check for physical files without database entries
            upload_dir = self.base_path / "uploads"
            for file_path in upload_dir.glob("*"):
                if file_path.is_file():
                    # Extract file ID from filename
                    filename = file_path.name
                    # Check if exists in database
                    check_query = "SELECT 1 FROM Files WHERE FilePath LIKE ?"
                    result = self.db.execute_query(check_query, (f"%{filename}%",))

                    if not result:
                        # Orphaned file
                        file_path.unlink(missing_ok=True)
                        cleaned_files += 1

            return {
                "success": True,
                "cleaned_files": cleaned_files,
                "cleaned_db_entries": cleaned_db_entries,
            }

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return {"success": False, "error": str(e)}

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""

        try:
            # Database stats
            stats_query = """
                SELECT 
                    COUNT(*) as total_files,
                    SUM(FileSize) as total_size,
                    AVG(FileSize) as avg_size,
                    FileType,
                    COUNT(*) as type_count
                FROM Files
                GROUP BY FileType
            """

            type_stats = self.db.execute_query(stats_query)

            # Overall stats
            overall_query = """
                SELECT 
                    COUNT(*) as total_files,
                    SUM(FileSize) as total_size,
                    AVG(FileSize) as avg_size
                FROM Files
            """

            overall = self.db.execute_query(overall_query)[0]

            # Disk usage
            upload_dir = self.base_path / "uploads"
            disk_usage = sum(
                f.stat().st_size for f in upload_dir.glob("**/*") if f.is_file()
            )

            return {
                "total_files": overall["total_files"],
                "total_size": overall["total_size"],
                "avg_file_size": overall["avg_size"],
                "disk_usage": disk_usage,
                "type_breakdown": type_stats,
            }

        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}
