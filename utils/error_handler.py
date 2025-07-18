#!/usr/bin/env python3
"""
utils/error_handler.py
Enterprise Error Handling and Recovery System
Fixed version with comprehensive error management and user-friendly messaging
"""

import logging
import traceback
import streamlit as st
import sys
import functools
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Type, Union
from enum import Enum
from dataclasses import dataclass, field
import json
from pathlib import Path
import threading
from collections import defaultdict, deque
import psutil
import inspect

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels with numeric values for comparison"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification and handling"""

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
    PERFORMANCE = "performance"
    SECURITY = "security"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Comprehensive error information with metadata"""

    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    user_message: str
    technical_details: str
    stack_trace: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)
    error_count: int = 1
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "user_message": self.user_message,
            "technical_details": self.technical_details,
            "stack_trace": self.stack_trace,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "context": self.context,
            "recovery_suggestions": self.recovery_suggestions,
            "error_count": self.error_count,
            "first_occurrence": (
                self.first_occurrence.isoformat() if self.first_occurrence else None
            ),
            "last_occurrence": (
                self.last_occurrence.isoformat() if self.last_occurrence else None
            ),
        }


class CircuitBreaker:
    """Circuit breaker pattern for external service calls"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time < self.timeout:
                    raise Exception("Circuit breaker is OPEN")
                else:
                    self.state = "HALF_OPEN"

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"

                raise e


class ErrorHandler:
    """Enterprise error handling system with comprehensive features"""

    def __init__(self, db_manager=None, config: Dict[str, Any] = None):
        self.db = db_manager
        self.config = config or {}
        self.error_cache = {}
        self.error_history = deque(maxlen=1000)
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.user_messages = self._initialize_user_messages()
        self.circuit_breakers = {}
        self.performance_threshold = self.config.get(
            "performance_threshold", 5.0
        )  # seconds
        self.max_errors_per_minute = self.config.get("max_errors_per_minute", 10)
        self.error_counts = defaultdict(list)
        self._lock = threading.Lock()

        # Initialize error logging
        self._setup_error_logging()

    def _setup_error_logging(self) -> None:
        """Setup comprehensive error logging"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # Create error-specific logger
            error_logger = logging.getLogger("error_handler")
            error_logger.setLevel(logging.ERROR)

            # File handler for errors
            error_file_handler = logging.FileHandler(
                log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
            )
            error_file_handler.setLevel(logging.ERROR)

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            error_file_handler.setFormatter(formatter)
            error_logger.addHandler(error_file_handler)

        except Exception as e:
            logger.warning(f"Failed to setup error logging: {e}")

    def _initialize_recovery_strategies(self) -> Dict[ErrorCategory, List[str]]:
        """Initialize recovery strategies for each error category"""
        return {
            ErrorCategory.DATABASE: [
                "ตรวจสอบการเชื่อมต่อฐานข้อมูล",
                "รีสตาร์ทการเชื่อมต่อฐานข้อมูล",
                "ตรวจสอบ SQL query ที่ใช้",
                "ตรวจสอบพื้นที่ฐานข้อมูล",
                "ติดต่อ DBA หากปัญหาไม่หาย",
            ],
            ErrorCategory.AUTHENTICATION: [
                "ล็อกเอาต์และล็อกอินใหม่",
                "ล้างคุกกี้เบราว์เซอร์",
                "ตรวจสอบรหัสผ่าน",
                "ติดต่อผู้ดูแลระบบหากยังไม่ได้",
            ],
            ErrorCategory.VALIDATION: [
                "ตรวจสอบรูปแบบข้อมูลที่ป้อน",
                "ตรวจสอบขนาดไฟล์",
                "ตรวจสอบประเภทไฟล์ที่อนุญาต",
                "ลองใหม่อีกครั้งด้วยข้อมูลที่ถูกต้อง",
            ],
            ErrorCategory.PERMISSION: [
                "ตรวจสอบสิทธิ์การเข้าถึง",
                "ติดต่อผู้ดูแลระบบเพื่อขอสิทธิ์",
                "ตรวจสอบบทบาทผู้ใช้งาน",
            ],
            ErrorCategory.NETWORK: [
                "ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต",
                "ลองรีเฟรชหน้าเว็บ",
                "รอสักครู่แล้วลองใหม่",
                "ตรวจสอบ VPN หากใช้งาน",
            ],
            ErrorCategory.FILE_SYSTEM: [
                "ตรวจสอบพื้นที่ว่างในระบบ",
                "ตรวจสอบสิทธิ์การเขียนไฟล์",
                "ลองอัปโหลดไฟล์ใหม่",
                "ติดต่อผู้ดูแลระบบ",
            ],
            ErrorCategory.EXTERNAL_API: [
                "ตรวจสอบการเชื่อมต่อเซอร์วิสภายนอก",
                "รอสักครู่แล้วลองใหม่",
                "ตรวจสอบ API key หากมี",
                "ใช้ฟีเจอร์อื่นในระหว่างนี้",
            ],
            ErrorCategory.BUSINESS_LOGIC: [
                "ตรวจสอบข้อมูลที่ป้อน",
                "ตรวจสอบลำดับการทำงาน",
                "อ่านคู่มือการใช้งาน",
                "ติดต่อฝ่ายสนับสนุน",
            ],
            ErrorCategory.UI_RENDERING: [
                "รีเฟรชหน้าเว็บ",
                "ล้างแคชเบราว์เซอร์",
                "ลองใช้เบราว์เซอร์อื่น",
                "ตรวจสอบ JavaScript ในเบราว์เซอร์",
            ],
            ErrorCategory.CONFIGURATION: [
                "ตรวจสอบการตั้งค่าระบบ",
                "รีสตาร์ทแอปพลิเคชัน",
                "ติดต่อผู้ดูแลระบบ",
                "ตรวจสอบไฟล์ config",
            ],
            ErrorCategory.PERFORMANCE: [
                "รอสักครู่แล้วลองใหม่",
                "ลดขนาดข้อมูลที่ประมวลผล",
                "ปิดแท็บอื่นๆ ในเบราว์เซอร์",
                "ติดต่อผู้ดูแลระบบหากช้าต่อเนื่อง",
            ],
            ErrorCategory.SECURITY: [
                "ตรวจสอบสิทธิ์การเข้าถึง",
                "ล็อกเอาต์และล็อกอินใหม่",
                "ติดต่อผู้ดูแลระบบทันที",
                "เปลี่ยนรหัสผ่านหากจำเป็น",
            ],
            ErrorCategory.UNKNOWN: [
                "รีเฟรชหน้าเว็บ",
                "ลองใหม่อีกครั้ง",
                "รีสตาร์ทเบราว์เซอร์",
                "ติดต่อฝ่ายสนับสนุนพร้อมรายละเอียดข้อผิดพลาด",
            ],
        }

    def _initialize_user_messages(self) -> Dict[ErrorCategory, str]:
        """Initialize user-friendly error messages"""
        return {
            ErrorCategory.DATABASE: "เกิดปัญหาการเชื่อมต่อฐานข้อมูล กรุณาลองใหม่อีกครั้ง",
            ErrorCategory.AUTHENTICATION: "ปัญหาการยืนยันตัวตน กรุณาล็อกอินใหม่",
            ErrorCategory.VALIDATION: "ข้อมูลที่ป้อนไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง",
            ErrorCategory.PERMISSION: "คุณไม่มีสิทธิ์เข้าถึงฟีเจอร์นี้",
            ErrorCategory.NETWORK: "ปัญหาการเชื่อมต่อเครือข่าย กรุณาตรวจสอบอินเทอร์เน็ต",
            ErrorCategory.FILE_SYSTEM: "เกิดปัญหาในการจัดการไฟล์",
            ErrorCategory.EXTERNAL_API: "ไม่สามารถเชื่อมต่อบริการภายนอกได้ขณะนี้",
            ErrorCategory.BUSINESS_LOGIC: "เกิดข้อผิดพลาดในกระบวนการทำงาน",
            ErrorCategory.UI_RENDERING: "เกิดปัญหาการแสดงผล กรุณารีเฟรชหน้าเว็บ",
            ErrorCategory.CONFIGURATION: "เกิดปัญหาการตั้งค่าระบบ",
            ErrorCategory.PERFORMANCE: "ระบบทำงานช้าผิดปกติ กรุณารอสักครู่",
            ErrorCategory.SECURITY: "ตรวจพบปัญหาความปลอดภัย กรุณาติดต่อผู้ดูแลระบบ",
            ErrorCategory.UNKNOWN: "เกิดข้อผิดพลาดที่ไม่คาดคิด กรุณาลองใหม่อีกครั้ง",
        }

    def _categorize_error(
        self, exception: Exception, context: Dict[str, Any] = None
    ) -> ErrorCategory:
        """Categorize error based on exception type and context"""
        exception_name = type(exception).__name__.lower()
        error_message = str(exception).lower()

        # Database errors
        if any(
            keyword in exception_name
            for keyword in ["database", "sql", "connection", "cursor"]
        ):
            return ErrorCategory.DATABASE

        # Authentication errors
        if any(
            keyword in exception_name
            for keyword in ["auth", "login", "credential", "token"]
        ):
            return ErrorCategory.AUTHENTICATION

        # Validation errors
        if any(
            keyword in exception_name
            for keyword in ["validation", "value", "type", "format"]
        ):
            return ErrorCategory.VALIDATION

        # Permission errors
        if any(
            keyword in exception_name
            for keyword in ["permission", "access", "forbidden", "unauthorized"]
        ):
            return ErrorCategory.PERMISSION

        # Network errors
        if any(
            keyword in exception_name
            for keyword in ["connection", "network", "timeout", "http"]
        ):
            return ErrorCategory.NETWORK

        # File system errors
        if any(keyword in exception_name for keyword in ["file", "io", "os", "path"]):
            return ErrorCategory.FILE_SYSTEM

        # Performance errors
        if any(
            keyword in error_message for keyword in ["timeout", "slow", "memory", "cpu"]
        ):
            return ErrorCategory.PERFORMANCE

        # Security errors
        if any(
            keyword in error_message
            for keyword in ["security", "attack", "malicious", "suspicious"]
        ):
            return ErrorCategory.SECURITY

        return ErrorCategory.UNKNOWN

    def _determine_severity(
        self, exception: Exception, category: ErrorCategory
    ) -> ErrorSeverity:
        """Determine error severity based on exception and category"""
        exception_name = type(exception).__name__.lower()

        # Critical errors
        critical_indicators = ["security", "corruption", "data loss", "system failure"]
        if any(
            indicator in str(exception).lower() for indicator in critical_indicators
        ):
            return ErrorSeverity.CRITICAL

        # High severity
        if category in [
            ErrorCategory.DATABASE,
            ErrorCategory.SECURITY,
            ErrorCategory.AUTHENTICATION,
        ]:
            return ErrorSeverity.HIGH

        # Medium severity
        if category in [
            ErrorCategory.PERMISSION,
            ErrorCategory.BUSINESS_LOGIC,
            ErrorCategory.EXTERNAL_API,
        ]:
            return ErrorSeverity.MEDIUM

        # Low severity (UI, validation, etc.)
        return ErrorSeverity.LOW

    def _check_rate_limiting(self, category: ErrorCategory) -> bool:
        """Check if error rate limiting should be applied"""
        current_time = time.time()

        # Clean old entries
        minute_ago = current_time - 60
        self.error_counts[category] = [
            timestamp
            for timestamp in self.error_counts[category]
            if timestamp > minute_ago
        ]

        # Check if rate limit exceeded
        if len(self.error_counts[category]) >= self.max_errors_per_minute:
            return True

        # Add current error
        self.error_counts[category].append(current_time)
        return False

    def handle_error(
        self,
        exception: Exception,
        context: Dict[str, Any] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        show_to_user: bool = True,
        auto_recover: bool = True,
    ) -> ErrorInfo:
        """Comprehensive error handling with context and recovery"""

        try:
            # Generate error ID
            error_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now()

            # Categorize and assess severity
            category = self._categorize_error(exception, context)
            severity = self._determine_severity(exception, category)

            # Check rate limiting
            if self._check_rate_limiting(category):
                logger.warning(f"Rate limit exceeded for {category.value} errors")

            # Get stack trace
            stack_trace = traceback.format_exc()

            # Create error info
            error_info = ErrorInfo(
                error_id=error_id,
                timestamp=timestamp,
                severity=severity,
                category=category,
                message=str(exception),
                user_message=self.user_messages.get(category, "เกิดข้อผิดพลาดที่ไม่คาดคิด"),
                technical_details=f"{type(exception).__name__}: {str(exception)}",
                stack_trace=stack_trace,
                user_id=user_id,
                session_id=session_id or self._get_session_id(),
                context=context or {},
                recovery_suggestions=self.recovery_strategies.get(category, []),
            )

            # Store error info
            self._store_error_info(error_info)

            # Log error
            self._log_error(error_info)

            # Show to user if requested
            if show_to_user:
                self._display_error_to_user(error_info)

            # Attempt auto-recovery
            if auto_recover:
                self._attempt_recovery(error_info)

            # Send notifications for critical errors
            if severity == ErrorSeverity.CRITICAL:
                self._send_critical_error_notification(error_info)

            return error_info

        except Exception as e:
            # Fallback error handling
            logger.critical(f"Error handler itself failed: {e}")
            self._fallback_error_display(exception)
            return None

    def _store_error_info(self, error_info: ErrorInfo) -> None:
        """Store error information in cache and database"""
        try:
            # Store in memory cache
            self.error_cache[error_info.error_id] = error_info
            self.error_history.append(error_info)

            # Store in database if available
            if self.db:
                self._save_error_to_database(error_info)

        except Exception as e:
            logger.error(f"Failed to store error info: {e}")

    def _save_error_to_database(self, error_info: ErrorInfo) -> None:
        """Save error information to database"""
        try:
            query = """
                INSERT INTO error_logs (
                    error_id, timestamp, severity, category, message, 
                    user_message, technical_details, stack_trace, 
                    user_id, session_id, context, recovery_suggestions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute(
                query,
                (
                    error_info.error_id,
                    error_info.timestamp.isoformat(),
                    error_info.severity.value,
                    error_info.category.value,
                    error_info.message,
                    error_info.user_message,
                    error_info.technical_details,
                    error_info.stack_trace,
                    error_info.user_id,
                    error_info.session_id,
                    json.dumps(error_info.context),
                    json.dumps(error_info.recovery_suggestions),
                ),
            )

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to save error to database: {e}")

    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error with appropriate level"""
        log_message = (
            f"[{error_info.error_id}] {error_info.category.value}: {error_info.message}"
        )

        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def _display_error_to_user(self, error_info: ErrorInfo) -> None:
        """Display user-friendly error message"""
        try:
            # Determine display style based on severity
            if error_info.severity == ErrorSeverity.CRITICAL:
                st.error(f"🚨 **ข้อผิดพลาดร้ายแรง**")
                st.error(f"📝 {error_info.user_message}")
                st.error(f"🆔 รหัสข้อผิดพลาด: `{error_info.error_id}`")

            elif error_info.severity == ErrorSeverity.HIGH:
                st.error(f"❌ **เกิดข้อผิดพลาด**")
                st.error(f"📝 {error_info.user_message}")
                st.info(f"🆔 รหัสข้อผิดพลาด: `{error_info.error_id}`")

            elif error_info.severity == ErrorSeverity.MEDIUM:
                st.warning(f"⚠️ **คำเตือน**")
                st.warning(f"📝 {error_info.user_message}")

            else:
                st.info(f"ℹ️ {error_info.user_message}")

            # Show recovery suggestions
            if error_info.recovery_suggestions:
                with st.expander("💡 วิธีแก้ไขปัญหา", expanded=False):
                    for i, suggestion in enumerate(error_info.recovery_suggestions, 1):
                        st.write(f"{i}. {suggestion}")

            # Show technical details for developers (in development mode)
            if self.config.get("debug_mode", False):
                with st.expander("🔧 รายละเอียดทางเทคนิค (สำหรับนักพัฒนา)", expanded=False):
                    st.code(error_info.technical_details)
                    st.text_area("Stack Trace", error_info.stack_trace, height=200)

        except Exception as e:
            logger.error(f"Failed to display error to user: {e}")
            self._fallback_error_display(Exception(error_info.message))

    def _fallback_error_display(self, exception: Exception) -> None:
        """Fallback error display when main error handling fails"""
        st.error("🚨 เกิดข้อผิดพลาดร้ายแรงในระบบ")
        st.error(f"📝 {str(exception)}")
        st.info("กรุณาติดต่อผู้ดูแลระบบ")

    def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt automatic error recovery"""
        try:
            recovery_successful = False

            # Category-specific recovery attempts
            if error_info.category == ErrorCategory.DATABASE:
                recovery_successful = self._recover_database_connection()
            elif error_info.category == ErrorCategory.NETWORK:
                recovery_successful = self._recover_network_connection()
            elif error_info.category == ErrorCategory.FILE_SYSTEM:
                recovery_successful = self._recover_file_system()

            if recovery_successful:
                logger.info(f"Auto-recovery successful for error {error_info.error_id}")
                st.success("✅ ระบบได้แก้ไขปัญหาโดยอัตโนมัติแล้ว")

            return recovery_successful

        except Exception as e:
            logger.error(f"Auto-recovery failed: {e}")
            return False

    def _recover_database_connection(self) -> bool:
        """Attempt to recover database connection"""
        try:
            if self.db:
                # Try to reconnect
                self.db.reconnect()
                return True
        except Exception:
            pass
        return False

    def _recover_network_connection(self) -> bool:
        """Attempt to recover network connection"""
        try:
            import requests

            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _recover_file_system(self) -> bool:
        """Attempt to recover file system issues"""
        try:
            # Check disk space
            disk_usage = psutil.disk_usage("/")
            free_space_gb = disk_usage.free / (1024**3)

            if free_space_gb < 1:  # Less than 1GB
                logger.warning("Low disk space detected")
                return False

            return True
        except Exception:
            return False

    def _send_critical_error_notification(self, error_info: ErrorInfo) -> None:
        """Send notifications for critical errors"""
        try:
            # Log critical error
            logger.critical(
                f"CRITICAL ERROR: {error_info.error_id} - {error_info.message}"
            )

            # In production, this would send emails/Slack notifications
            # For now, just log it
            critical_log = {
                "error_id": error_info.error_id,
                "timestamp": error_info.timestamp.isoformat(),
                "message": error_info.message,
                "user_id": error_info.user_id,
                "context": error_info.context,
            }

            logger.critical(f"Critical error details: {json.dumps(critical_log)}")

        except Exception as e:
            logger.error(f"Failed to send critical error notification: {e}")

    def _get_session_id(self) -> str:
        """Get current session ID"""
        try:
            if hasattr(st, "session_state") and hasattr(st.session_state, "session_id"):
                return st.session_state.session_id
            return f"session_{int(time.time())}"
        except Exception:
            return f"session_{int(time.time())}"

    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            recent_errors = [
                error for error in self.error_history if error.timestamp > cutoff_time
            ]

            stats = {
                "total_errors": len(recent_errors),
                "by_severity": {},
                "by_category": {},
                "by_hour": [0] * 24,
                "top_errors": [],
            }

            # Count by severity
            for severity in ErrorSeverity:
                stats["by_severity"][severity.value] = len(
                    [e for e in recent_errors if e.severity == severity]
                )

            # Count by category
            for category in ErrorCategory:
                stats["by_category"][category.value] = len(
                    [e for e in recent_errors if e.category == category]
                )

            # Count by hour
            for error in recent_errors:
                hour = error.timestamp.hour
                stats["by_hour"][hour] += 1

            # Top errors by frequency
            error_messages = {}
            for error in recent_errors:
                key = f"{error.category.value}:{error.message[:50]}"
                error_messages[key] = error_messages.get(key, 0) + 1

            stats["top_errors"] = sorted(
                error_messages.items(), key=lambda x: x[1], reverse=True
            )[:10]

            return stats

        except Exception as e:
            logger.error(f"Failed to get error stats: {e}")
            return {}

    def clear_error_history(self, hours: int = 168) -> int:
        """Clear old error history (default: 1 week)"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            original_count = len(self.error_history)
            self.error_history = deque(
                [
                    error
                    for error in self.error_history
                    if error.timestamp > cutoff_time
                ],
                maxlen=1000,
            )

            cleared_count = original_count - len(self.error_history)
            logger.info(f"Cleared {cleared_count} old error records")

            return cleared_count

        except Exception as e:
            logger.error(f"Failed to clear error history: {e}")
            return 0


def error_handler_decorator(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    show_to_user: bool = True,
    auto_recover: bool = True,
):
    """Decorator for automatic error handling"""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = ErrorHandler()

                # Get context from function
                context = {
                    "function_name": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                }

                error_handler.handle_error(
                    exception=e,
                    context=context,
                    show_to_user=show_to_user,
                    auto_recover=auto_recover,
                )

                # Re-raise for critical errors
                if severity == ErrorSeverity.CRITICAL:
                    raise

                return None

        return wrapper

    return decorator


def performance_monitor(threshold: float = 5.0):
    """Decorator to monitor function performance"""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time > threshold:
                    error_handler = ErrorHandler()
                    context = {
                        "function_name": func.__name__,
                        "execution_time": execution_time,
                        "threshold": threshold,
                    }

                    error_handler.handle_error(
                        exception=Exception(
                            f"Performance threshold exceeded: {execution_time:.2f}s"
                        ),
                        context=context,
                        show_to_user=False,
                    )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {func.__name__} failed after {execution_time:.2f}s: {e}"
                )
                raise

        return wrapper

    return decorator


# Global error handler instance
global_error_handler = ErrorHandler()


def handle_streamlit_errors():
    """Setup global Streamlit error handling"""

    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        global_error_handler.handle_error(
            exception=exc_value,
            context={"exc_type": exc_type.__name__},
            show_to_user=True,
        )

    sys.excepthook = exception_handler
