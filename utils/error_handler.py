#!/usr/bin/env python3
"""
utils/error_handler.py
Enterprise Error Handling and Recovery System
Comprehensive error management with logging and user-friendly messaging
"""

import logging
import traceback
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import json
import sys

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""

    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    PERMISSION = "permission"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    EXTERNAL_API = "external_api"
    BUSINESS_LOGIC = "business_logic"
    UI_RENDERING = "ui_rendering"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Comprehensive error information"""

    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    user_message: str
    technical_details: str
    stack_trace: str
    user_id: Optional[int]
    session_id: Optional[str]
    context: Dict[str, Any]
    recovery_suggestions: List[str]


class ErrorHandler:
    """Enterprise error handling system"""

    def __init__(self):
        self.error_cache = {}
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.user_messages = self._initialize_user_messages()

    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, List[str]]:
        """Initialize recovery strategies for each error category"""
        return {
            ErrorCategory.DATABASE: [
                "ตรวจสอบการเชื่อมต่อฐานข้อมูล",
                "ลองใหม่อีกครั้งในอีกสักครู่",
                "ติดต่อทีม IT หากปัญหายังคงอยู่",
            ],
            ErrorCategory.AUTHENTICATION: [
                "ตรวจสอบชื่อผู้ใช้และรหัสผ่าน",
                "ลองเข้าสู่ระบบใหม่อีกครั้ง",
                "ติดต่อผู้ดูแลระบบหากลืมรหัสผ่าน",
            ],
            ErrorCategory.VALIDATION: [
                "ตรวจสอบข้อมูลที่กรอกให้ถูกต้อง",
                "อ่านคำแนะนำในแต่ละฟิลด์",
                "ลองกรอกข้อมูลใหม่",
            ],
            ErrorCategory.PERMISSION: [
                "ตรวจสอบสิทธิ์การเข้าถึง",
                "ติดต่อผู้ดูแลระบบเพื่อขอสิทธิ์",
                "ลองเข้าถึงในฐานะผู้ใช้อื่น",
            ],
            ErrorCategory.NETWORK: [
                "ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต",
                "ลองรีเฟรชหน้าเว็บ",
                "รอสักครู่แล้วลองใหม่",
            ],
            ErrorCategory.FILE_SYSTEM: [
                "ตรวจสอบขนาดไฟล์และรูปแบบ",
                "ลองอัปโหลดไฟล์ใหม่",
                "ตรวจสอบพื้นที่จัดเก็บ",
            ],
        }

    def _initialize_user_messages(self) -> Dict[str, str]:
        """Initialize user-friendly error messages"""
        return {
            "database_connection": "ไม่สามารถเชื่อมต่อฐานข้อมูลได้ กรุณาลองใหม่อีกครั้ง",
            "authentication_failed": "การเข้าสู่ระบบไม่สำเร็จ กรุณาตรวจสอบชื่อผู้ใช้และรหัสผ่าน",
            "permission_denied": "คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้",
            "validation_error": "ข้อมูลที่กรอกไม่ถูกต้อง กรุณาตรวจสอบและลองใหม่",
            "file_upload_error": "เกิดข้อผิดพลาดในการอัปโหลดไฟล์",
            "network_error": "เกิดข้อผิดพลาดในการเชื่อมต่อ กรุณาตรวจสอบอินเทอร์เน็ต",
            "server_error": "เกิดข้อผิดพลาดในเซิร์ฟเวอร์ กรุณาลองใหม่ภายหลัง",
            "unknown_error": "เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ กรุณาติดต่อผู้ดูแลระบบ",
        }

    def handle_error(
        self,
        error: Exception,
        context: str = None,
        user_id: int = None,
        show_to_user: bool = True,
    ) -> ErrorInfo:
        """Main error handling method"""
        try:
            # Generate unique error ID
            error_id = self._generate_error_id()

            # Classify error
            category = self._classify_error(error)
            severity = self._determine_severity(error, category)

            # Extract error information
            error_message = str(error)
            stack_trace = traceback.format_exc()

            # Generate user-friendly message
            user_message = self._generate_user_message(error, category)

            # Get recovery suggestions
            recovery_suggestions = self.recovery_strategies.get(
                category, ["ลองรีเฟรชหน้าเว็บ", "ติดต่อผู้ดูแลระบบหากปัญหายังคงอยู่"]
            )

            # Create error info
            error_info = ErrorInfo(
                error_id=error_id,
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                message=error_message,
                user_message=user_message,
                technical_details=stack_trace,
                stack_trace=stack_trace,
                user_id=user_id,
                session_id=st.session_state.get("session_id"),
                context={"context": context, "error_type": type(error).__name__},
                recovery_suggestions=recovery_suggestions,
            )

            # Log error
            self._log_error(error_info)

            # Show to user if requested
            if show_to_user:
                self._display_error_to_user(error_info)

            # Store in cache for debugging
            self.error_cache[error_id] = error_info

            return error_info

        except Exception as handler_error:
            # Fallback error handling
            logger.critical(f"Error handler failed: {handler_error}")
            self._display_fallback_error()
            return None

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into appropriate category"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        # Database errors
        if any(
            keyword in error_message
            for keyword in ["database", "connection", "sqlite", "sql"]
        ):
            return ErrorCategory.DATABASE

        # Authentication errors
        if any(
            keyword in error_message
            for keyword in ["authentication", "login", "password", "unauthorized"]
        ):
            return ErrorCategory.AUTHENTICATION

        # Validation errors
        if any(
            keyword in error_message
            for keyword in ["validation", "invalid", "required", "format"]
        ):
            return ErrorCategory.VALIDATION

        # Permission errors
        if any(
            keyword in error_message
            for keyword in ["permission", "access", "forbidden", "denied"]
        ):
            return ErrorCategory.PERMISSION

        # Network errors
        if any(
            keyword in error_message
            for keyword in ["network", "timeout", "connection refused", "unreachable"]
        ):
            return ErrorCategory.NETWORK

        # File system errors
        if any(
            keyword in error_message
            for keyword in ["file", "directory", "path", "upload"]
        ):
            return ErrorCategory.FILE_SYSTEM

        # Streamlit/UI errors
        if "streamlit" in error_message or "st." in error_message:
            return ErrorCategory.UI_RENDERING

        return ErrorCategory.UNKNOWN

    def _determine_severity(
        self, error: Exception, category: ErrorCategory
    ) -> ErrorSeverity:
        """Determine error severity level"""
        error_message = str(error).lower()

        # Critical errors
        if category == ErrorCategory.DATABASE and "connection" in error_message:
            return ErrorSeverity.CRITICAL

        if any(keyword in error_message for keyword in ["system", "critical", "fatal"]):
            return ErrorSeverity.CRITICAL

        # High severity errors
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.PERMISSION]:
            return ErrorSeverity.HIGH

        if any(
            keyword in error_message
            for keyword in ["security", "breach", "unauthorized"]
        ):
            return ErrorSeverity.HIGH

        # Medium severity errors
        if category in [ErrorCategory.VALIDATION, ErrorCategory.BUSINESS_LOGIC]:
            return ErrorSeverity.MEDIUM

        # Default to low severity
        return ErrorSeverity.LOW

    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        error_message = str(error).lower()

        # Specific error messages
        if "database" in error_message or "connection" in error_message:
            return self.user_messages["database_connection"]

        if "login" in error_message or "password" in error_message:
            return self.user_messages["authentication_failed"]

        if "permission" in error_message or "access" in error_message:
            return self.user_messages["permission_denied"]

        if "validation" in error_message or "invalid" in error_message:
            return self.user_messages["validation_error"]

        if "file" in error_message or "upload" in error_message:
            return self.user_messages["file_upload_error"]

        if "network" in error_message or "timeout" in error_message:
            return self.user_messages["network_error"]

        # Category-based messages
        category_messages = {
            ErrorCategory.DATABASE: self.user_messages["database_connection"],
            ErrorCategory.AUTHENTICATION: self.user_messages["authentication_failed"],
            ErrorCategory.PERMISSION: self.user_messages["permission_denied"],
            ErrorCategory.VALIDATION: self.user_messages["validation_error"],
            ErrorCategory.FILE_SYSTEM: self.user_messages["file_upload_error"],
            ErrorCategory.NETWORK: self.user_messages["network_error"],
        }

        return category_messages.get(category, self.user_messages["unknown_error"])

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        import uuid

        return f"ERR_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}"

    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error with appropriate level"""
        log_message = (
            f"[{error_info.error_id}] {error_info.category.value}: {error_info.message}"
        )

        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(
                log_message,
                extra={
                    "error_id": error_info.error_id,
                    "category": error_info.category.value,
                    "user_id": error_info.user_id,
                    "stack_trace": error_info.stack_trace,
                },
            )
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(
                log_message,
                extra={
                    "error_id": error_info.error_id,
                    "category": error_info.category.value,
                    "user_id": error_info.user_id,
                },
            )
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(
                log_message,
                extra={
                    "error_id": error_info.error_id,
                    "category": error_info.category.value,
                },
            )
        else:
            logger.info(
                log_message,
                extra={
                    "error_id": error_info.error_id,
                    "category": error_info.category.value,
                },
            )

    def _display_error_to_user(self, error_info: ErrorInfo) -> None:
        """Display error to user with appropriate styling"""
        if error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            st.error(f"❌ **{error_info.user_message}**")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ **{error_info.user_message}**")
        else:
            st.info(f"ℹ️ **{error_info.user_message}**")

        # Show recovery suggestions
        if error_info.recovery_suggestions:
            with st.expander("💡 วิธีแก้ไข"):
                for suggestion in error_info.recovery_suggestions:
                    st.write(f"• {suggestion}")

        # Show error ID for support
        st.caption(f"รหัสข้อผิดพลาด: `{error_info.error_id}`")

    def _display_fallback_error(self) -> None:
        """Display fallback error when error handler fails"""
        st.error("🔧 เกิดข้อผิดพลาดร้ายแรงในระบบ กรุณาติดต่อผู้ดูแลระบบทันที")
        st.caption(f"เวลาที่เกิดข้อผิดพลาด: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """Safely execute a function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, context=f"Function: {func.__name__}")
            return None

    def retry_on_error(
        self, func: Callable, max_retries: int = 3, delay: float = 1.0, *args, **kwargs
    ) -> Any:
        """Retry function execution on error"""
        import time

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    self.handle_error(
                        e,
                        context=f"Function: {func.__name__} (after {max_retries} retries)",
                    )
                    return None
                else:
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}"
                    )
                    time.sleep(delay * (attempt + 1))  # Exponential backoff

        return None

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        try:
            stats = {
                "total_errors": len(self.error_cache),
                "by_category": {},
                "by_severity": {},
                "recent_errors": [],
            }

            for error_info in self.error_cache.values():
                # Count by category
                category = error_info.category.value
                stats["by_category"][category] = (
                    stats["by_category"].get(category, 0) + 1
                )

                # Count by severity
                severity = error_info.severity.value
                stats["by_severity"][severity] = (
                    stats["by_severity"].get(severity, 0) + 1
                )

                # Recent errors (last 10)
                if len(stats["recent_errors"]) < 10:
                    stats["recent_errors"].append(
                        {
                            "error_id": error_info.error_id,
                            "timestamp": error_info.timestamp.isoformat(),
                            "category": category,
                            "severity": severity,
                            "message": error_info.user_message,
                        }
                    )

            return stats

        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return {}

    def clear_error_cache(self) -> None:
        """Clear error cache"""
        self.error_cache.clear()
        logger.info("Error cache cleared")

    def export_error_report(self) -> str:
        """Export error report as JSON"""
        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "statistics": self.get_error_statistics(),
                "errors": [],
            }

            for error_info in self.error_cache.values():
                report["errors"].append(
                    {
                        "error_id": error_info.error_id,
                        "timestamp": error_info.timestamp.isoformat(),
                        "severity": error_info.severity.value,
                        "category": error_info.category.value,
                        "message": error_info.message,
                        "user_message": error_info.user_message,
                        "context": error_info.context,
                        "user_id": error_info.user_id,
                    }
                )

            return json.dumps(report, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to export error report: {e}")
            return "{}"


# Global error handler instance
error_handler = ErrorHandler()


def handle_streamlit_errors():
    """Decorator for handling Streamlit function errors"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    e, context=f"Streamlit function: {func.__name__}"
                )
                return None

        return wrapper

    return decorator


def safe_streamlit_operation(operation_name: str = "Unknown"):
    """Context manager for safe Streamlit operations"""

    class SafeOperation:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                error_handler.handle_error(
                    exc_val, context=f"Streamlit operation: {operation_name}"
                )
                return True  # Suppress the exception
            return False

    return SafeOperation()


# Example usage functions
def validate_user_input(input_value: Any, validation_rules: Dict) -> Tuple[bool, str]:
    """Validate user input with comprehensive error handling"""
    try:
        # Validation logic here
        if not input_value:
            raise ValueError("Input value is required")

        # Add more validation rules
        return True, "Validation passed"

    except Exception as e:
        error_info = error_handler.handle_error(
            e, context="Input validation", show_to_user=False
        )
        return False, error_info.user_message if error_info else "Validation failed"


def safe_database_operation(db_func: Callable, *args, **kwargs) -> Any:
    """Safely execute database operations"""
    return error_handler.retry_on_error(
        db_func, max_retries=3, delay=1.0, *args, **kwargs
    )
