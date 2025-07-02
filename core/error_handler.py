# core/error_handler.py
"""
Enhanced Error Handler for Project Manager Pro v3.0
Comprehensive error handling with logging, user feedback, and recovery suggestions
"""

import streamlit as st
import logging
import traceback
import sys
from datetime import datetime
from typing import Any, Dict, Optional, List, Callable
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""

    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorHandler:
    """Enhanced error handling system with categorization and recovery suggestions"""

    def __init__(self):
        self.error_log = []
        self.max_errors = 100
        self.error_callbacks = {}
        self.recovery_strategies = self._initialize_recovery_strategies()

    def _initialize_recovery_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize recovery strategies for different error types"""
        return {
            # Database Errors
            "ConnectionError": {
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.HIGH,
                "user_message": "🔌 Database connection failed",
                "recovery_suggestions": [
                    "Check database server status",
                    "Verify connection settings in .streamlit/secrets.toml",
                    "Ensure database credentials are correct",
                    "Check network connectivity",
                ],
                "auto_retry": True,
                "retry_count": 3,
            },
            "OperationalError": {
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "💾 Database operation failed",
                "recovery_suggestions": [
                    "Check database schema",
                    "Verify data format",
                    "Check database permissions",
                ],
                "auto_retry": False,
            },
            # Authentication Errors
            "AuthenticationError": {
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "🔐 Authentication failed",
                "recovery_suggestions": [
                    "Check username and password",
                    "Verify account is active",
                    "Contact administrator if locked out",
                ],
                "auto_retry": False,
            },
            # File System Errors
            "FileNotFoundError": {
                "category": ErrorCategory.FILE_SYSTEM,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "📁 File not found",
                "recovery_suggestions": [
                    "Check file path",
                    "Verify file exists",
                    "Check file permissions",
                ],
                "auto_retry": False,
            },
            "PermissionError": {
                "category": ErrorCategory.PERMISSION,
                "severity": ErrorSeverity.HIGH,
                "user_message": "🔒 Permission denied",
                "recovery_suggestions": [
                    "Check file/folder permissions",
                    "Run with appropriate privileges",
                    "Contact system administrator",
                ],
                "auto_retry": False,
            },
            # Network Errors
            "TimeoutError": {
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "⏱️ Request timeout",
                "recovery_suggestions": [
                    "Check network connection",
                    "Try again later",
                    "Contact network administrator",
                ],
                "auto_retry": True,
                "retry_count": 2,
            },
            # Validation Errors
            "ValueError": {
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "user_message": "📝 Invalid data provided",
                "recovery_suggestions": [
                    "Check input format",
                    "Verify required fields",
                    "Review data validation rules",
                ],
                "auto_retry": False,
            },
            # Configuration Errors
            "KeyError": {
                "category": ErrorCategory.CONFIGURATION,
                "severity": ErrorSeverity.MEDIUM,
                "user_message": "⚙️ Configuration error",
                "recovery_suggestions": [
                    "Check configuration files",
                    "Verify all required settings",
                    "Reset to default configuration",
                ],
                "auto_retry": False,
            },
            # System Errors
            "MemoryError": {
                "category": ErrorCategory.SYSTEM,
                "severity": ErrorSeverity.CRITICAL,
                "user_message": "💾 Insufficient memory",
                "recovery_suggestions": [
                    "Close other applications",
                    "Restart the application",
                    "Contact system administrator",
                ],
                "auto_retry": False,
            },
        }

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle application errors with comprehensive logging and user feedback

        Args:
            error: The exception that occurred
            context: Additional context information

        Returns:
            bool: True if error was handled successfully, False otherwise
        """
        try:
            error_type = type(error).__name__
            error_message = str(error)

            # Get error strategy
            strategy = self.recovery_strategies.get(
                error_type,
                {
                    "category": ErrorCategory.UNKNOWN,
                    "severity": ErrorSeverity.MEDIUM,
                    "user_message": "❌ An unexpected error occurred",
                    "recovery_suggestions": [
                        "Try refreshing the page",
                        "Contact support if the problem persists",
                    ],
                    "auto_retry": False,
                },
            )

            # Create comprehensive error info
            error_info = {
                "timestamp": datetime.now(),
                "error_type": error_type,
                "error_message": error_message,
                "traceback": traceback.format_exc(),
                "context": context or {},
                "category": strategy["category"].value,
                "severity": strategy["severity"].value,
                "user_agent": self._get_user_agent(),
                "session_info": self._get_session_info(),
            }

            # Log error with appropriate level
            self._log_error(error_info, strategy["severity"])

            # Store error in memory
            self._store_error(error_info)

            # Show user-friendly error message
            self._show_user_error(strategy, error_info)

            # Execute callbacks if registered
            self._execute_callbacks(error_type, error_info)

            # Attempt auto-recovery if configured
            if strategy.get("auto_retry", False):
                return self._attempt_auto_recovery(error, strategy)

            return True

        except Exception as handler_error:
            # Error in error handler - log critical error
            logger.critical(f"Error handler failed: {str(handler_error)}")
            st.error(
                "💥 Critical system error occurred. Please restart the application."
            )
            return False

    def _log_error(self, error_info: Dict[str, Any], severity: ErrorSeverity) -> None:
        """Log error with appropriate level"""
        log_message = f"[{severity.value.upper()}] {error_info['error_type']}: {error_info['error_message']}"

        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra=error_info)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra=error_info)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=error_info)
        else:
            logger.info(log_message, extra=error_info)

    def _store_error(self, error_info: Dict[str, Any]) -> None:
        """Store error in memory for analysis"""
        self.error_log.append(error_info)

        # Keep only recent errors
        if len(self.error_log) > self.max_errors:
            self.error_log.pop(0)

    def _show_user_error(
        self, strategy: Dict[str, Any], error_info: Dict[str, Any]
    ) -> None:
        """Show user-friendly error message with recovery suggestions"""
        severity = strategy["severity"]
        user_message = strategy["user_message"]
        suggestions = strategy["recovery_suggestions"]

        # Choose Streamlit display method based on severity
        if severity == ErrorSeverity.CRITICAL:
            st.error(f"{user_message}")
        elif severity == ErrorSeverity.HIGH:
            st.error(f"{user_message}")
        elif severity == ErrorSeverity.MEDIUM:
            st.warning(f"{user_message}")
        else:
            st.info(f"{user_message}")

        # Show recovery suggestions in expander
        with st.expander("🔧 Troubleshooting Steps", expanded=False):
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(f"{i}. {suggestion}")

            # Add error details for debugging
            if st.session_state.get("debug_mode", False):
                st.markdown("---")
                st.markdown("**Debug Information:**")
                st.code(error_info["traceback"])
                st.json(error_info["context"])

    def _execute_callbacks(self, error_type: str, error_info: Dict[str, Any]) -> None:
        """Execute registered error callbacks"""
        if error_type in self.error_callbacks:
            try:
                self.error_callbacks[error_type](error_info)
            except Exception as callback_error:
                logger.error(f"Error callback failed: {str(callback_error)}")

    def _attempt_auto_recovery(
        self, error: Exception, strategy: Dict[str, Any]
    ) -> bool:
        """Attempt automatic error recovery"""
        max_retries = strategy.get("retry_count", 1)

        for attempt in range(max_retries):
            try:
                st.info(
                    f"🔄 Attempting recovery... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(1)  # Brief delay before retry

                # Here you would implement specific recovery logic
                # For now, just return True to indicate recovery attempt
                return True

            except Exception as retry_error:
                logger.warning(
                    f"Recovery attempt {attempt + 1} failed: {str(retry_error)}"
                )
                continue

        st.error(f"❌ Auto-recovery failed after {max_retries} attempts")
        return False

    def _get_user_agent(self) -> str:
        """Get user agent information"""
        try:
            # In Streamlit, we can't directly access browser user agent
            # This is a placeholder for the actual implementation
            return "Streamlit Application"
        except:
            return "Unknown"

    def _get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        try:
            return {
                "user_id": st.session_state.get("user_id"),
                "username": st.session_state.get("username"),
                "current_page": st.session_state.get("current_page"),
                "session_start": st.session_state.get("session_start"),
                "authenticated": st.session_state.get("authenticated", False),
            }
        except:
            return {}

    def register_error_callback(self, error_type: str, callback: Callable) -> None:
        """Register callback for specific error type"""
        self.error_callbacks[error_type] = callback

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_log:
            return {
                "total_errors": 0,
                "error_types": {},
                "severity_distribution": {},
                "category_distribution": {},
                "recent_errors": [],
            }

        # Calculate statistics
        error_types = {}
        severity_dist = {}
        category_dist = {}

        for error in self.error_log:
            # Count by type
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

            # Count by severity
            severity = error["severity"]
            severity_dist[severity] = severity_dist.get(severity, 0) + 1

            # Count by category
            category = error["category"]
            category_dist[category] = category_dist.get(category, 0) + 1

        return {
            "total_errors": len(self.error_log),
            "error_types": error_types,
            "severity_distribution": severity_dist,
            "category_distribution": category_dist,
            "recent_errors": self.error_log[-10:],  # Last 10 errors
        }

    def clear_error_log(self) -> None:
        """Clear error log"""
        self.error_log.clear()
        logger.info("Error log cleared")

    def export_error_log(self) -> str:
        """Export error log as JSON"""
        return json.dumps(self.error_log, default=str, indent=2)

    def render_error_dashboard(self) -> None:
        """Render error monitoring dashboard"""
        st.markdown("### 🚨 Error Monitoring Dashboard")

        stats = self.get_error_statistics()

        if stats["total_errors"] == 0:
            st.success("✅ No errors recorded!")
            return

        # Error summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Errors", stats["total_errors"])

        with col2:
            recent_errors = len(
                [
                    e
                    for e in self.error_log
                    if (datetime.now() - e["timestamp"]).days < 1
                ]
            )
            st.metric("Last 24 Hours", recent_errors)

        with col3:
            critical_errors = stats["severity_distribution"].get("critical", 0)
            st.metric("Critical Errors", critical_errors, delta_color="inverse")

        # Error distribution charts
        col1, col2 = st.columns(2)

        with col1:
            if stats["error_types"]:
                st.markdown("#### Error Types")
                error_df = pd.DataFrame(
                    list(stats["error_types"].items()), columns=["Type", "Count"]
                )
                st.bar_chart(error_df.set_index("Type"))

        with col2:
            if stats["severity_distribution"]:
                st.markdown("#### Severity Distribution")
                severity_df = pd.DataFrame(
                    list(stats["severity_distribution"].items()),
                    columns=["Severity", "Count"],
                )
                st.bar_chart(severity_df.set_index("Severity"))

        # Recent errors table
        st.markdown("#### Recent Errors")
        if stats["recent_errors"]:
            recent_df = pd.DataFrame(
                [
                    {
                        "Timestamp": error["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                        "Type": error["error_type"],
                        "Message": (
                            error["error_message"][:100] + "..."
                            if len(error["error_message"]) > 100
                            else error["error_message"]
                        ),
                        "Severity": error["severity"],
                    }
                    for error in reversed(stats["recent_errors"])
                ]
            )
            st.dataframe(recent_df, use_container_width=True)

        # Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Clear Error Log"):
                self.clear_error_log()
                st.success("Error log cleared!")
                st.rerun()

        with col2:
            if st.button("📥 Export Log"):
                log_data = self.export_error_log()
                st.download_button(
                    label="💾 Download JSON",
                    data=log_data,
                    file_name=f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

        with col3:
            if st.button("🔄 Refresh"):
                st.rerun()


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
    """Quick function to handle errors using global handler"""
    return get_error_handler().handle_error(error, context)


# Context manager for error handling
class ErrorContext:
    """Context manager for automatic error handling"""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.context = context
        self.error_handler = get_error_handler()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_handler.handle_error(exc_val, self.context)
            return True  # Suppress the exception
        return False


# Decorator for automatic error handling
def handle_errors(context: Optional[Dict[str, Any]] = None):
    """Decorator for automatic error handling"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, context)
                return None

        return wrapper

    return decorator


# Export main classes and functions
__all__ = [
    "ErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "get_error_handler",
    "handle_error",
    "handle_errors",
]
