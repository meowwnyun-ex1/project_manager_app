#!/usr/bin/env python3
"""
utils/error_handler.py
Error Handling Utilities for SDX Project Manager
Comprehensive error management and user-friendly error display
"""

import streamlit as st
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Enhanced error handling with user-friendly messages"""

    def __init__(self):
        self.error_count = 0
        self.last_error_time = None

    def log_error(self, error: Exception, context: str = "") -> None:
        """Log error with context"""
        self.error_count += 1
        self.last_error_time = datetime.now()

        error_msg = f"Error in {context}: {str(error)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")

    def show_user_error(self, message: str, error_type: str = "error") -> None:
        """Show user-friendly error message"""
        if error_type == "error":
            st.error(f"❌ {message}")
        elif error_type == "warning":
            st.warning(f"⚠️ {message}")
        elif error_type == "info":
            st.info(f"ℹ️ {message}")

    def get_friendly_error_message(self, error: Exception) -> str:
        """Convert technical error to user-friendly message"""
        error_str = str(error).lower()

        # Database connection errors
        if "connection" in error_str or "server" in error_str:
            return "ไม่สามารถเชื่อมต่อฐานข้อมูลได้ กรุณาตรวจสอบการเชื่อมต่อ"

        # SQL errors
        elif "syntax" in error_str or "invalid" in error_str:
            return "เกิดข้อผิดพลาดในการประมวลผลข้อมูล กรุณาลองใหม่อีกครั้ง"

        # Permission errors
        elif "permission" in error_str or "access" in error_str:
            return "คุณไม่มีสิทธิ์ในการดำเนินการนี้"

        # File errors
        elif "file" in error_str or "directory" in error_str:
            return "เกิดข้อผิดพลาดในการจัดการไฟล์"

        # Network errors
        elif "timeout" in error_str or "network" in error_str:
            return "การเชื่อมต่อใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง"

        # Validation errors
        elif "validation" in error_str or "constraint" in error_str:
            return "ข้อมูลที่กรอกไม่ถูกต้อง กรุณาตรวจสอบและลองใหม่"

        # Default message
        else:
            return "เกิดข้อผิดพลาดที่ไม่คาดคิด กรุณาติดต่อผู้ดูแลระบบ"


# Global error handler instance
error_handler = ErrorHandler()


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.log_error(e, func.__name__)
        error_handler.show_user_error(error_handler.get_friendly_error_message(e))
        return None


def handle_error(context: str = ""):
    """Decorator for error handling"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = context or func.__name__
                error_handler.log_error(e, error_context)
                error_handler.show_user_error(
                    error_handler.get_friendly_error_message(e)
                )
                return None

        return wrapper

    return decorator


def handle_database_error(func: Callable) -> Callable:
    """Specific decorator for database operations"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.log_error(e, f"Database operation: {func.__name__}")

            # Show specific database error message
            if "connection" in str(e).lower():
                st.error("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
                st.info("💡 กรุณาตรวจสอบ:")
                st.info("• การตั้งค่าในไฟล์ .streamlit/secrets.toml")
                st.info("• การเชื่อมต่อเครือข่าย")
                st.info("• สถานะของ SQL Server")
            else:
                st.error("❌ เกิดข้อผิดพลาดในการจัดการข้อมูล")

            return None

    return wrapper


def handle_auth_error(func: Callable) -> Callable:
    """Specific decorator for authentication operations"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.log_error(e, f"Authentication: {func.__name__}")
            st.error("❌ เกิดข้อผิดพลาดในการยืนยันตัวตน")
            st.info("กรุณาลองเข้าสู่ระบบใหม่อีกครั้ง")
            return None

    return wrapper


def show_error_details(error: Exception, show_technical: bool = False) -> None:
    """Show detailed error information"""
    with st.expander("รายละเอียดข้อผิดพลาด", expanded=False):
        st.write(f"**ประเภท:** {type(error).__name__}")
        st.write(f"**ข้อความ:** {str(error)}")
        st.write(f"**เวลา:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if show_technical:
            st.text("**Technical Details:**")
            st.code(traceback.format_exc())


def validate_input(value: Any, validation_type: str, field_name: str = "") -> bool:
    """Validate input with user-friendly error messages"""
    try:
        if validation_type == "required" and not value:
            st.error(f"❌ {field_name} จำเป็นต้องกรอก")
            return False

        elif validation_type == "email" and value:
            import re

            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
                st.error(f"❌ รูปแบบอีเมลไม่ถูกต้อง")
                return False

        elif validation_type == "phone" and value:
            import re

            if not re.match(r"^[0-9\-\s\+\(\)]+$", value):
                st.error(f"❌ รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง")
                return False

        elif validation_type == "number" and value:
            try:
                float(value)
            except ValueError:
                st.error(f"❌ {field_name} ต้องเป็นตัวเลข")
                return False

        elif validation_type == "date" and value:
            try:
                if isinstance(value, str):
                    datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                st.error(f"❌ รูปแบบวันที่ไม่ถูกต้อง (YYYY-MM-DD)")
                return False

        return True

    except Exception as e:
        logger.error(f"Validation error: {e}")
        st.error("❌ เกิดข้อผิดพลาดในการตรวจสอบข้อมูล")
        return False


def create_error_report() -> dict:
    """Create error report for debugging"""
    return {
        "total_errors": error_handler.error_count,
        "last_error": error_handler.last_error_time,
        "timestamp": datetime.now(),
    }


def reset_error_counter() -> None:
    """Reset error counter"""
    error_handler.error_count = 0
    error_handler.last_error_time = None


# Utility functions for common operations
def try_parse_int(value: str, default: int = 0) -> int:
    """Safely parse integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def try_parse_float(value: str, default: float = 0.0) -> float:
    """Safely parse float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_get_dict_value(data: dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        return default


def safe_format_date(date_obj: Any, format_str: str = "%Y-%m-%d") -> str:
    """Safely format date"""
    try:
        if isinstance(date_obj, str):
            return date_obj
        return date_obj.strftime(format_str)
    except (AttributeError, ValueError):
        return "ไม่ระบุ"


# Context manager for error handling
class ErrorContext:
    """Context manager for handling errors in code blocks"""

    def __init__(self, operation_name: str, show_user_message: bool = True):
        self.operation_name = operation_name
        self.show_user_message = show_user_message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_handler.log_error(exc_val, self.operation_name)
            if self.show_user_message:
                error_handler.show_user_error(
                    error_handler.get_friendly_error_message(exc_val)
                )
        return True  # Suppress the exception


# Example usage:
# with ErrorContext("Database connection"):
#     database_operation()
