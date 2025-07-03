"""
utils/error_handler.py
Enhanced error handling and logging utilities
"""

import streamlit as st
import logging
import traceback
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Callable
import os
import json
from functools import wraps


# Setup logging
def setup_logging():
    """Setup comprehensive logging configuration"""

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/errors", exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler for general logs
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # File handler for errors only
    error_handler = logging.FileHandler("logs/errors/error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    return logger


# Initialize logging
logger = setup_logging()


class ErrorHandler:
    """Comprehensive error handling class"""

    def __init__(self):
        self.error_count = 0
        self.errors_today = []
        self.max_errors_per_day = 100

    def log_error(
        self,
        error: Exception,
        context: str = "",
        user_id: str = None,
        request_data: Dict = None,
        extra_data: Dict = None,
    ):
        """Log error with comprehensive details"""
        try:
            # Get error details
            error_type = type(error).__name__
            error_message = str(error)
            error_traceback = traceback.format_exc()

            # Get user context
            current_user = user_id or self._get_current_user_id()

            # Get session context
            session_data = self._get_session_context()

            # Create error record
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "error_message": error_message,
                "context": context,
                "user_id": current_user,
                "session_data": session_data,
                "request_data": request_data or {},
                "extra_data": extra_data or {},
                "traceback": error_traceback,
                "file_info": self._get_file_info(),
                "system_info": self._get_system_info(),
            }

            # Log to file
            logger.error(f"Error in {context}: {error_message}", exc_info=True)

            # Save detailed error record
            self._save_error_record(error_record)

            # Update error count
            self.error_count += 1
            self.errors_today.append(error_record)

            # Clean old errors (keep only today's)
            self._cleanup_old_errors()

        except Exception as logging_error:
            # Fallback logging if error handler itself fails
            print(f"Error in error handler: {str(logging_error)}")
            print(f"Original error: {str(error)}")

    def _get_current_user_id(self) -> Optional[str]:
        """Get current user ID from session"""
        try:
            user = st.session_state.get("user", {})
            return str(user.get("UserID", "unknown"))
        except:
            return "unknown"

    def _get_session_context(self) -> Dict:
        """Get session context information"""
        try:
            return {
                "authenticated": st.session_state.get("authenticated", False),
                "current_page": st.session_state.get("current_page", "unknown"),
                "session_keys": (
                    list(st.session_state.keys())
                    if hasattr(st, "session_state")
                    else []
                ),
            }
        except:
            return {}

    def _get_file_info(self) -> Dict:
        """Get file and line information where error occurred"""
        try:
            tb = traceback.extract_tb(sys.exc_info()[2])
            if tb:
                last_frame = tb[-1]
                return {
                    "filename": last_frame.filename,
                    "line_number": last_frame.lineno,
                    "function_name": last_frame.name,
                    "line_content": last_frame.line,
                }
        except:
            pass

        return {}

    def _get_system_info(self) -> Dict:
        """Get system information"""
        try:
            import platform
            import psutil

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": (
                    psutil.disk_usage("/").percent
                    if os.name != "nt"
                    else psutil.disk_usage("C:").percent
                ),
            }
        except:
            return {}

    def _save_error_record(self, error_record: Dict):
        """Save detailed error record to JSON file"""
        try:
            error_file = f"logs/errors/error_{datetime.now().strftime('%Y%m%d')}.json"

            # Read existing errors
            errors = []
            if os.path.exists(error_file):
                try:
                    with open(error_file, "r", encoding="utf-8") as f:
                        errors = json.load(f)
                except:
                    errors = []

            # Add new error
            errors.append(error_record)

            # Keep only last 100 errors per day
            if len(errors) > 100:
                errors = errors[-100:]

            # Save back to file
            with open(error_file, "w", encoding="utf-8") as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"Could not save error record: {str(e)}")

    def _cleanup_old_errors(self):
        """Clean up old error records"""
        try:
            # Keep only today's errors in memory
            today = datetime.now().date()
            self.errors_today = [
                error
                for error in self.errors_today
                if datetime.fromisoformat(error["timestamp"]).date() == today
            ]

            # Remove old error files (keep last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            error_dir = "logs/errors"

            if os.path.exists(error_dir):
                for filename in os.listdir(error_dir):
                    if filename.startswith("error_") and filename.endswith(".json"):
                        try:
                            date_str = filename[6:14]  # Extract YYYYMMDD
                            file_date = datetime.strptime(date_str, "%Y%m%d")

                            if file_date < cutoff_date:
                                os.remove(os.path.join(error_dir, filename))
                        except:
                            continue

        except Exception as e:
            logger.warning(f"Error cleanup failed: {str(e)}")

    def display_error(
        self, error: Exception, context: str = "", show_details: bool = False
    ):
        """Display user-friendly error message"""
        try:
            # User-friendly error messages
            error_messages = {
                "ConnectionError": "ไม่สามารถเชื่อมต่อฐานข้อมูลได้ กรุณาตรวจสอบการเชื่อมต่อ",
                "TimeoutError": "การดำเนินการใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง",
                "PermissionError": "ไม่มีสิทธิ์ในการดำเนินการนี้",
                "FileNotFoundError": "ไม่พบไฟล์ที่ต้องการ",
                "ValueError": "ข้อมูลที่ป้อนไม่ถูกต้อง",
                "KeyError": "ข้อมูลที่ต้องการไม่พบ",
                "TypeError": "ประเภทข้อมูลไม่ถูกต้อง",
            }

            error_type = type(error).__name__
            user_message = error_messages.get(error_type, "เกิดข้อผิดพลาดไม่คาดคิด")

            # Show error to user
            st.error(f"❌ {user_message}")

            # Show context if provided
            if context:
                st.error(f"บริบท: {context}")

            # Show details for admin users
            if show_details or self._is_admin_user():
                with st.expander("รายละเอียดข้อผิดพลาด (สำหรับผู้ดูแลระบบ)"):
                    st.code(f"Error Type: {error_type}")
                    st.code(f"Error Message: {str(error)}")
                    if context:
                        st.code(f"Context: {context}")

                    # Show traceback for debugging
                    st.text("Traceback:")
                    st.code(traceback.format_exc())

        except Exception as display_error:
            # Fallback if error display itself fails
            st.error("เกิดข้อผิดพลาดร้ายแรง กรุณาติดต่อผู้ดูแลระบบ")
            logger.error(f"Error display failed: {str(display_error)}")

    def _is_admin_user(self) -> bool:
        """Check if current user is admin"""
        try:
            user = st.session_state.get("user", {})
            return user.get("Role") == "Admin"
        except:
            return False

    def get_error_stats(self) -> Dict:
        """Get error statistics"""
        try:
            today = datetime.now().date()
            today_errors = [
                error
                for error in self.errors_today
                if datetime.fromisoformat(error["timestamp"]).date() == today
            ]

            # Count by error type
            error_types = {}
            for error in today_errors:
                error_type = error.get("error_type", "Unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1

            return {
                "total_errors_today": len(today_errors),
                "total_errors_session": self.error_count,
                "error_types": error_types,
                "recent_errors": today_errors[-5:] if today_errors else [],
            }

        except Exception as e:
            logger.error(f"Error getting error stats: {str(e)}")
            return {}

    def clear_error_history(self):
        """Clear error history (admin function)"""
        try:
            self.error_count = 0
            self.errors_today = []
            logger.info("Error history cleared by admin")
        except Exception as e:
            logger.error(f"Error clearing history: {str(e)}")


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# Decorators for error handling
def handle_streamlit_errors(show_details: bool = False):
    """Decorator for handling Streamlit errors"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                context = f"Function: {func.__name__}"
                error_handler.log_error(e, context)
                error_handler.display_error(e, context, show_details)
                return None

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    default_return: Any = None,
    error_message: str = "เกิดข้อผิดพลาด",
    show_error: bool = True,
) -> Any:
    """Safely execute function with error handling"""
    try:
        return func()
    except Exception as e:
        error_handler = get_error_handler()
        context = f"Safe execute: {func.__name__ if hasattr(func, '__name__') else 'anonymous'}"
        error_handler.log_error(e, context)

        if show_error:
            st.error(f"{error_message}: {str(e)}")

        return default_return


def handle_database_errors(func: Callable) -> Callable:
    """Decorator specifically for database operation errors"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = get_error_handler()
            context = f"Database operation: {func.__name__}"
            error_handler.log_error(e, context)

            # Database-specific error messages
            error_message = "เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล"

            if "timeout" in str(e).lower():
                error_message = "การเชื่อมต่อฐานข้อมูลหมดเวลา กรุณาลองใหม่อีกครั้ง"
            elif "connection" in str(e).lower():
                error_message = "ไม่สามารถเชื่อมต่อฐานข้อมูลได้ กรุณาตรวจสอบการตั้งค่า"
            elif "permission" in str(e).lower():
                error_message = "ไม่มีสิทธิ์ในการเข้าถึงฐานข้อมูล"
            elif "syntax" in str(e).lower():
                error_message = "คำสั่ง SQL ไม่ถูกต้อง"

            st.error(f"❌ {error_message}")
            return None

    return wrapper


def handle_authentication_errors(func: Callable) -> Callable:
    """Decorator for authentication-related errors"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = get_error_handler()
            context = f"Authentication: {func.__name__}"
            error_handler.log_error(e, context)

            # Authentication-specific error messages
            if "password" in str(e).lower():
                st.error("❌ รหัสผ่านไม่ถูกต้อง")
            elif "username" in str(e).lower():
                st.error("❌ ชื่อผู้ใช้ไม่ถูกต้อง")
            elif "expired" in str(e).lower():
                st.error("❌ เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่")
            elif "permission" in str(e).lower():
                st.error("❌ ไม่มีสิทธิ์ในการเข้าถึง")
            else:
                st.error("❌ เกิดข้อผิดพลาดในการตรวจสอบสิทธิ์")

            return None

    return wrapper


def handle_file_errors(func: Callable) -> Callable:
    """Decorator for file operation errors"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = get_error_handler()
            context = f"File operation: {func.__name__}"
            error_handler.log_error(e, context)

            # File-specific error messages
            if "FileNotFoundError" in str(type(e)):
                st.error("❌ ไม่พบไฟล์ที่ต้องการ")
            elif "PermissionError" in str(type(e)):
                st.error("❌ ไม่มีสิทธิ์ในการเข้าถึงไฟล์")
            elif "size" in str(e).lower():
                st.error("❌ ไฟล์มีขนาดใหญ่เกินไป")
            elif "format" in str(e).lower() or "invalid" in str(e).lower():
                st.error("❌ รูปแบบไฟล์ไม่ถูกต้อง")
            else:
                st.error("❌ เกิดข้อผิดพลาดในการจัดการไฟล์")

            return None

    return wrapper


class ErrorReporter:
    """Error reporting and monitoring utilities"""

    @staticmethod
    def generate_error_report(
        start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        """Generate comprehensive error report"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()

            error_handler = get_error_handler()

            # Filter errors by date range
            filtered_errors = []
            for error in error_handler.errors_today:
                error_date = datetime.fromisoformat(error["timestamp"])
                if start_date <= error_date <= end_date:
                    filtered_errors.append(error)

            # Analyze errors
            total_errors = len(filtered_errors)
            error_types = {}
            error_contexts = {}
            hourly_distribution = {}
            user_errors = {}

            for error in filtered_errors:
                # Count by type
                error_type = error.get("error_type", "Unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1

                # Count by context
                context = error.get("context", "Unknown")
                error_contexts[context] = error_contexts.get(context, 0) + 1

                # Count by hour
                error_hour = datetime.fromisoformat(error["timestamp"]).hour
                hourly_distribution[error_hour] = (
                    hourly_distribution.get(error_hour, 0) + 1
                )

                # Count by user
                user_id = error.get("user_id", "unknown")
                user_errors[user_id] = user_errors.get(user_id, 0) + 1

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "summary": {
                    "total_errors": total_errors,
                    "unique_error_types": len(error_types),
                    "unique_contexts": len(error_contexts),
                    "affected_users": len(user_errors),
                },
                "analysis": {
                    "error_types": dict(
                        sorted(error_types.items(), key=lambda x: x[1], reverse=True)
                    ),
                    "error_contexts": dict(
                        sorted(error_contexts.items(), key=lambda x: x[1], reverse=True)
                    ),
                    "hourly_distribution": dict(sorted(hourly_distribution.items())),
                    "user_errors": dict(
                        sorted(user_errors.items(), key=lambda x: x[1], reverse=True)[
                            :10
                        ]
                    ),
                },
                "recent_errors": filtered_errors[-10:] if filtered_errors else [],
            }

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {}

    @staticmethod
    def export_error_report(report: Dict, filename: str = None) -> str:
        """Export error report to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"error_report_{timestamp}.json"

            filepath = os.path.join("logs", filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            return filepath

        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return ""


class HealthChecker:
    """System health monitoring"""

    @staticmethod
    def check_system_health() -> Dict:
        """Check overall system health"""
        health_status = {
            "overall_status": "healthy",
            "checks": {},
            "warnings": [],
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Check error rate
            error_handler = get_error_handler()
            error_stats = error_handler.get_error_stats()

            errors_today = error_stats.get("total_errors_today", 0)
            if errors_today > 50:
                health_status["overall_status"] = "critical"
                health_status["errors"].append(
                    f"High error rate: {errors_today} errors today"
                )
            elif errors_today > 20:
                health_status["overall_status"] = "warning"
                health_status["warnings"].append(
                    f"Elevated error rate: {errors_today} errors today"
                )

            health_status["checks"]["error_rate"] = {
                "status": (
                    "ok"
                    if errors_today <= 20
                    else "warning" if errors_today <= 50 else "critical"
                ),
                "value": errors_today,
                "message": f"{errors_today} errors today",
            }

            # Check disk space
            try:
                import psutil

                disk_usage = (
                    psutil.disk_usage("/").percent
                    if os.name != "nt"
                    else psutil.disk_usage("C:").percent
                )

                if disk_usage > 90:
                    health_status["overall_status"] = "critical"
                    health_status["errors"].append(
                        f"Critical disk usage: {disk_usage:.1f}%"
                    )
                elif disk_usage > 80:
                    if health_status["overall_status"] == "healthy":
                        health_status["overall_status"] = "warning"
                    health_status["warnings"].append(
                        f"High disk usage: {disk_usage:.1f}%"
                    )

                health_status["checks"]["disk_usage"] = {
                    "status": (
                        "ok"
                        if disk_usage <= 80
                        else "warning" if disk_usage <= 90 else "critical"
                    ),
                    "value": disk_usage,
                    "message": f"{disk_usage:.1f}% disk usage",
                }
            except:
                health_status["checks"]["disk_usage"] = {
                    "status": "unknown",
                    "message": "Unable to check disk usage",
                }

            # Check memory usage
            try:
                import psutil

                memory_usage = psutil.virtual_memory().percent

                if memory_usage > 90:
                    if health_status["overall_status"] != "critical":
                        health_status["overall_status"] = "warning"
                    health_status["warnings"].append(
                        f"High memory usage: {memory_usage:.1f}%"
                    )

                health_status["checks"]["memory_usage"] = {
                    "status": (
                        "ok"
                        if memory_usage <= 80
                        else "warning" if memory_usage <= 90 else "critical"
                    ),
                    "value": memory_usage,
                    "message": f"{memory_usage:.1f}% memory usage",
                }
            except:
                health_status["checks"]["memory_usage"] = {
                    "status": "unknown",
                    "message": "Unable to check memory usage",
                }

            # Check log file sizes
            try:
                log_files = ["logs/app.log", "logs/errors/error.log"]
                total_log_size = 0

                for log_file in log_files:
                    if os.path.exists(log_file):
                        size_mb = os.path.getsize(log_file) / (1024 * 1024)
                        total_log_size += size_mb

                if total_log_size > 100:  # 100MB
                    health_status["warnings"].append(
                        f"Large log files: {total_log_size:.1f}MB"
                    )

                health_status["checks"]["log_size"] = {
                    "status": "ok" if total_log_size <= 100 else "warning",
                    "value": total_log_size,
                    "message": f"{total_log_size:.1f}MB total log size",
                }
            except:
                health_status["checks"]["log_size"] = {
                    "status": "unknown",
                    "message": "Unable to check log file sizes",
                }

        except Exception as e:
            health_status["overall_status"] = "critical"
            health_status["errors"].append(f"Health check failed: {str(e)}")
            logger.error(f"Health check error: {str(e)}")

        return health_status

    @staticmethod
    def cleanup_logs():
        """Clean up old log files"""
        try:
            cleaned_files = 0
            total_size_cleaned = 0

            # Clean up old application logs
            if os.path.exists("logs/app.log"):
                size = os.path.getsize("logs/app.log")
                if size > 50 * 1024 * 1024:  # 50MB
                    # Archive the log
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archive_name = f"logs/app_archived_{timestamp}.log"
                    os.rename("logs/app.log", archive_name)
                    cleaned_files += 1
                    total_size_cleaned += size

            # Clean up old error files
            error_dir = "logs/errors"
            if os.path.exists(error_dir):
                cutoff_date = datetime.now() - timedelta(days=30)

                for filename in os.listdir(error_dir):
                    filepath = os.path.join(error_dir, filename)

                    if os.path.isfile(filepath):
                        file_date = datetime.fromtimestamp(os.path.getmtime(filepath))

                        if file_date < cutoff_date:
                            size = os.path.getsize(filepath)
                            os.remove(filepath)
                            cleaned_files += 1
                            total_size_cleaned += size

            logger.info(
                f"Log cleanup completed: {cleaned_files} files, {total_size_cleaned / (1024*1024):.1f}MB cleaned"
            )

            return {
                "files_cleaned": cleaned_files,
                "size_cleaned_mb": total_size_cleaned / (1024 * 1024),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Log cleanup failed: {str(e)}")
            return {
                "files_cleaned": 0,
                "size_cleaned_mb": 0,
                "success": False,
                "error": str(e),
            }


# Initialize error handling
def init_error_handling():
    """Initialize error handling system"""
    try:
        # Setup logging
        setup_logging()

        # Create error handler
        error_handler = get_error_handler()

        # Setup global exception handler for uncaught exceptions
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            error_handler.log_error(
                exc_value, "Uncaught exception", extra_data={"exc_type": str(exc_type)}
            )

        sys.excepthook = handle_exception

        logger.info("Error handling system initialized")

    except Exception as e:
        print(f"Failed to initialize error handling: {str(e)}")


# Auto-initialize when module is imported
init_error_handling()
