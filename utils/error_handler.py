#!/usr/bin/env python3
"""
utils/error_handler.py
Error Handling Utilities for DENSO Project Manager Pro
"""
import logging
import streamlit as st
import traceback
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling"""

    @staticmethod
    def handle_database_error(e: Exception, operation: str = "database operation"):
        """Handle database-specific errors"""
        error_msg = str(e)

        if "Login failed" in error_msg:
            st.error("🔐 ข้อผิดพลาดการเชื่อมต่อ: การยืนยันตัวตนล้มเหลว")
        elif "timeout" in error_msg.lower():
            st.error("⏱️ ข้อผิดพลาดการเชื่อมต่อ: หมดเวลารอ")
        elif "server was not found" in error_msg.lower():
            st.error("🔍 ข้อผิดพลาดการเชื่อมต่อ: ไม่พบเซิร์ฟเวอร์")
        else:
            st.error(f"💾 ข้อผิดพลาดฐานข้อมูล: {operation} ล้มเหลว")

        logger.error(f"Database error in {operation}: {error_msg}")

    @staticmethod
    def handle_validation_error(field: str, message: str):
        """Handle validation errors"""
        st.error(f"❌ {field}: {message}")
        logger.warning(f"Validation error - {field}: {message}")

    @staticmethod
    def handle_permission_error(required_permission: str):
        """Handle permission errors"""
        st.error(f"🚫 คุณไม่มีสิทธิ์ในการ {required_permission}")
        logger.warning(f"Permission denied: {required_permission}")

    @staticmethod
    def handle_general_error(e: Exception, context: str = "operation"):
        """Handle general errors"""
        st.error(f"⚠️ เกิดข้อผิดพลาดในการ {context}")
        logger.error(f"Error in {context}: {str(e)}\n{traceback.format_exc()}")


def handle_streamlit_errors(func: Callable) -> Callable:
    """Decorator for handling Streamlit errors"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_general_error(e, func.__name__)
            return None

    return wrapper


def handle_database_errors(func: Callable) -> Callable:
    """Decorator for handling database errors specifically"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_database_error(e, func.__name__)
            return None

    return wrapper


def safe_execute(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ErrorHandler.handle_general_error(e, func.__name__)
        return default_return


def get_error_handler() -> ErrorHandler:
    """Get ErrorHandler instance"""
    return ErrorHandler()


# Additional utility functions for error handling
def log_error(error: Exception, context: str = "", user_id: int = None):
    """Log error with context"""
    error_info = {
        "error": str(error),
        "context": context,
        "user_id": user_id,
        "traceback": traceback.format_exc(),
    }
    logger.error(f"Error logged: {error_info}")


def validate_required_fields(data: dict, required_fields: list) -> tuple[bool, str]:
    """Validate required fields in data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)

    if missing_fields:
        return False, f"ข้อมูลที่จำเป็นขาดหายไป: {', '.join(missing_fields)}"
    return True, ""


def handle_api_error(response, operation: str = "API call"):
    """Handle API response errors"""
    if response.status_code == 400:
        st.error(f"❌ ข้อมูลที่ส่งไม่ถูกต้อง: {operation}")
    elif response.status_code == 401:
        st.error("🔐 ไม่มีสิทธิ์เข้าถึง กรุณาเข้าสู่ระบบใหม่")
    elif response.status_code == 403:
        st.error("🚫 ไม่มีสิทธิ์ในการดำเนินการนี้")
    elif response.status_code == 404:
        st.error("🔍 ไม่พบข้อมูลที่ต้องการ")
    elif response.status_code == 500:
        st.error("⚠️ เกิดข้อผิดพลาดที่เซิร์ฟเวอร์")
    else:
        st.error(f"⚠️ เกิดข้อผิดพลาดในการ {operation}")


def create_error_toast(message: str, error_type: str = "error"):
    """Create error toast notification"""
    if error_type == "error":
        st.toast(f"❌ {message}", icon="❌")
    elif error_type == "warning":
        st.toast(f"⚠️ {message}", icon="⚠️")
    elif error_type == "info":
        st.toast(f"ℹ️ {message}", icon="ℹ️")


class DatabaseErrorHandler:
    """Specialized database error handler"""

    @staticmethod
    def handle_connection_error():
        """Handle database connection errors"""
        st.error(
            """
        🔌 **ไม่สามารถเชื่อมต่อฐานข้อมูลได้**
        
        กรุณาตรวจสอบ:
        - เซิร์ฟเวอร์ฐานข้อมูลทำงานอยู่หรือไม่
        - การตั้งค่าการเชื่อมต่อใน secrets.toml
        - Firewall และ network connectivity
        """
        )

    @staticmethod
    def handle_query_error(query: str, error: Exception):
        """Handle SQL query errors"""
        logger.error(f"Query error: {query}\nError: {str(error)}")
        st.error("❌ เกิดข้อผิดพลาดในการดึงข้อมูล")

    @staticmethod
    def handle_transaction_error(operation: str):
        """Handle transaction errors"""
        st.error(f"💾 เกิดข้อผิดพลาดในการ {operation} - ข้อมูลไม่ได้รับการบันทึก")


class ValidationErrorHandler:
    """Specialized validation error handler"""

    @staticmethod
    def handle_required_field_error(field_name: str):
        """Handle required field validation"""
        st.error(f"📝 กรุณากรอก {field_name}")

    @staticmethod
    def handle_format_error(field_name: str, expected_format: str):
        """Handle format validation errors"""
        st.error(f"📋 รูปแบบ {field_name} ไม่ถูกต้อง (ต้องการ: {expected_format})")

    @staticmethod
    def handle_length_error(
        field_name: str, min_length: int = None, max_length: int = None
    ):
        """Handle length validation errors"""
        if min_length and max_length:
            st.error(f"📏 {field_name} ต้องมีความยาว {min_length}-{max_length} ตัวอักษร")
        elif min_length:
            st.error(f"📏 {field_name} ต้องมีความยาวอย่างน้อย {min_length} ตัวอักษร")
        elif max_length:
            st.error(f"📏 {field_name} ต้องมีความยาวไม่เกิน {max_length} ตัวอักษร")


# Context manager for error handling
class ErrorContext:
    """Context manager for error handling"""

    def __init__(self, operation: str, show_spinner: bool = True):
        self.operation = operation
        self.show_spinner = show_spinner
        self.spinner = None

    def __enter__(self):
        if self.show_spinner:
            self.spinner = st.spinner(f"กำลัง{self.operation}...")
            self.spinner.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.show_spinner and self.spinner:
            self.spinner.__exit__(exc_type, exc_val, exc_tb)

        if exc_type is not None:
            ErrorHandler.handle_general_error(exc_val, self.operation)
            return True  # Suppress the exception
        return False


# Usage examples:
# @handle_database_errors
# def get_users():
#     return db.fetch_all("SELECT * FROM Users")

# with ErrorContext("โหลดข้อมูล"):
#     data = load_data()

# is_valid, error_msg = validate_required_fields(form_data, ['name', 'email'])
# if not is_valid:
#     st.error(error_msg)
