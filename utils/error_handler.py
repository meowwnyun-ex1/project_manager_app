#!/usr/bin/env python3
"""
utils/error_handler.py
Error handling utilities for DENSO Project Manager Pro
"""
import streamlit as st
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def safe_execute(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """
    Safely execute function with error handling
    Returns default_return if function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Function {func.__name__} failed: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return default_return


def handle_error(
    error: Exception, user_message: str = "เกิดข้อผิดพลาด", show_details: bool = False
):
    """
    Handle and display error to user
    """
    # Log the error
    logger.error(f"Error: {str(error)}")
    logger.debug(f"Traceback: {traceback.format_exc()}")

    # Show user-friendly message
    st.error(f"❌ {user_message}")

    if show_details and st.checkbox("แสดงรายละเอียดข้อผิดพลาด"):
        st.code(str(error))
        with st.expander("Stack Trace"):
            st.code(traceback.format_exc())


def database_error_handler(func):
    """
    Decorator for database operations
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation failed in {func.__name__}: {str(e)}")
            st.error("❌ เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล")
            return None

    return wrapper


def ui_error_handler(func):
    """
    Decorator for UI operations
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"UI operation failed in {func.__name__}: {str(e)}")
            st.error("❌ เกิดข้อผิดพลาดในการแสดงผล")
            return None

    return wrapper


class ErrorLogger:
    """Enhanced error logging"""

    @staticmethod
    def log_user_action(
        user_id: int, action: str, details: str = None, success: bool = True
    ):
        """Log user actions for audit trail"""
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "action": action,
                "details": details,
                "success": success,
            }
            logger.info(f"User Action: {log_data}")
        except Exception as e:
            logger.error(f"Failed to log user action: {e}")

    @staticmethod
    def log_system_event(event: str, details: str = None, level: str = "info"):
        """Log system events"""
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "details": details,
            }

            if level == "error":
                logger.error(f"System Event: {log_data}")
            elif level == "warning":
                logger.warning(f"System Event: {log_data}")
            else:
                logger.info(f"System Event: {log_data}")
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")


def validate_input(value: Any, validation_type: str, **kwargs) -> tuple[bool, str]:
    """
    Validate input data
    Returns (is_valid, error_message)
    """
    try:
        if validation_type == "required":
            if value is None or str(value).strip() == "":
                return False, "ฟิลด์นี้จำเป็นต้องกรอก"

        elif validation_type == "email":
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, str(value)):
                return False, "รูปแบบอีเมลไม่ถูกต้อง"

        elif validation_type == "length":
            min_len = kwargs.get("min_length", 0)
            max_len = kwargs.get("max_length", 999999)
            if not (min_len <= len(str(value)) <= max_len):
                return False, f"ความยาวต้องอยู่ระหว่าง {min_len}-{max_len} ตัวอักษร"

        elif validation_type == "numeric":
            try:
                float(value)
            except (ValueError, TypeError):
                return False, "ต้องเป็นตัวเลข"

        elif validation_type == "positive":
            try:
                if float(value) <= 0:
                    return False, "ต้องเป็นตัวเลขบวก"
            except (ValueError, TypeError):
                return False, "ต้องเป็นตัวเลขบวก"

        return True, ""

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, "เกิดข้อผิดพลาดในการตรวจสอบข้อมูล"


class ValidationError(Exception):
    """Custom validation error"""

    pass


class DatabaseError(Exception):
    """Custom database error"""

    pass


class AuthenticationError(Exception):
    """Custom authentication error"""

    pass


class PermissionError(Exception):
    """Custom permission error"""

    pass
