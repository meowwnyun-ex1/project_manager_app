# error_handler.py
"""
Advanced Error Handling and Security System for DENSO Project Manager
Comprehensive error management, logging, and security measures
"""

import streamlit as st
import logging
import traceback
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
import hashlib
import secrets
import time
from dataclasses import dataclass
from enum import Enum
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class ErrorLevel(Enum):
    """Error severity levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SecurityThreat(Enum):
    """Security threat types"""

    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    BRUTE_FORCE = "brute_force"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"


@dataclass
class ErrorDetails:
    """Error details structure"""

    error_id: str
    level: ErrorLevel
    message: str
    exception_type: str
    stack_trace: str
    timestamp: datetime
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    request_path: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    additional_data: Optional[Dict] = None


@dataclass
class SecurityEvent:
    """Security event structure"""

    event_id: str
    threat_type: SecurityThreat
    severity: str
    description: str
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    blocked: bool = False
    additional_data: Optional[Dict] = None


class SecurityValidator:
    """Security validation and threat detection"""

    def __init__(self):
        self.failed_attempts = {}
        self.blocked_ips = {}
        self.suspicious_patterns = {
            "sql_injection": [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
                r"(UNION\s+SELECT)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(\'|\")(\s*)(UNION|SELECT|INSERT|UPDATE|DELETE)",
                r"(exec\s*\()",
                r"(script\s*:)",
            ],
            "xss_attempt": [
                r"(<script[^>]*>.*?</script>)",
                r"(javascript\s*:)",
                r"(on\w+\s*=)",
                r"(<iframe[^>]*>)",
                r"(<object[^>]*>)",
                r"(eval\s*\()",
                r"(document\.(cookie|location|write))",
            ],
            "path_traversal": [r"(\.\./)", r"(\.\.\\)", r"(%2e%2e%2f)", r"(%2e%2e\\)"],
        }

    def validate_input(
        self, input_data: str, input_type: str = "general"
    ) -> tuple[bool, Optional[SecurityThreat]]:
        """Validate input for security threats"""
        try:
            if not input_data:
                return True, None

            # Check for SQL injection
            for pattern in self.suspicious_patterns["sql_injection"]:
                if re.search(pattern, input_data, re.IGNORECASE):
                    logger.warning(
                        f"SQL injection attempt detected: {input_data[:100]}"
                    )
                    return False, SecurityThreat.SQL_INJECTION

            # Check for XSS attempts
            for pattern in self.suspicious_patterns["xss_attempt"]:
                if re.search(pattern, input_data, re.IGNORECASE):
                    logger.warning(f"XSS attempt detected: {input_data[:100]}")
                    return False, SecurityThreat.XSS_ATTEMPT

            # Check for path traversal
            for pattern in self.suspicious_patterns["path_traversal"]:
                if re.search(pattern, input_data, re.IGNORECASE):
                    logger.warning(
                        f"Path traversal attempt detected: {input_data[:100]}"
                    )
                    return False, SecurityThreat.SUSPICIOUS_ACTIVITY

            return True, None

        except Exception as e:
            logger.error(f"Error validating input: {str(e)}")
            return False, SecurityThreat.SUSPICIOUS_ACTIVITY

    def validate_password(
        self, password: str, min_length: int = 8
    ) -> tuple[bool, List[str]]:
        """Validate password strength"""
        issues = []

        if len(password) < min_length:
            issues.append(f"Password must be at least {min_length} characters long")

        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            issues.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            issues.append("Password must contain at least one number")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            issues.append("Password must contain at least one special character")

        # Check for common weak passwords
        weak_passwords = [
            "password",
            "123456",
            "admin",
            "user",
            "test",
            "qwerty",
            "abc123",
            "password123",
            "admin123",
        ]

        if password.lower() in weak_passwords:
            issues.append("Password is too common and weak")

        return len(issues) == 0, issues

    def check_brute_force(self, user_id: int, ip_address: str) -> bool:
        """Check for brute force attempts"""
        try:
            key = f"{user_id}_{ip_address}"
            current_time = time.time()

            # Clean old attempts
            self._clean_old_attempts()

            # Check if IP is blocked
            if ip_address in self.blocked_ips:
                if current_time < self.blocked_ips[ip_address]:
                    return False  # Still blocked
                else:
                    del self.blocked_ips[ip_address]  # Unblock

            # Record failed attempt
            if key not in self.failed_attempts:
                self.failed_attempts[key] = []

            self.failed_attempts[key].append(current_time)

            # Check if too many attempts in short time
            recent_attempts = [
                attempt
                for attempt in self.failed_attempts[key]
                if current_time - attempt < 900  # 15 minutes
            ]

            if len(recent_attempts) >= 5:  # 5 attempts in 15 minutes
                # Block IP for 30 minutes
                self.blocked_ips[ip_address] = current_time + 1800
                logger.warning(f"IP {ip_address} blocked due to brute force attempts")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking brute force: {str(e)}")
            return True  # Allow on error to avoid false positives

    def _clean_old_attempts(self):
        """Clean old failed login attempts"""
        try:
            current_time = time.time()
            cutoff_time = current_time - 3600  # 1 hour

            # Clean failed attempts
            for key in list(self.failed_attempts.keys()):
                self.failed_attempts[key] = [
                    attempt
                    for attempt in self.failed_attempts[key]
                    if attempt > cutoff_time
                ]
                if not self.failed_attempts[key]:
                    del self.failed_attempts[key]

            # Clean expired blocks
            expired_blocks = [
                ip
                for ip, block_time in self.blocked_ips.items()
                if current_time > block_time
            ]
            for ip in expired_blocks:
                del self.blocked_ips[ip]

        except Exception as e:
            logger.error(f"Error cleaning old attempts: {str(e)}")

    def sanitize_input(self, input_data: str) -> str:
        """Sanitize input data"""
        try:
            if not input_data:
                return input_data

            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\']', "", input_data)

            # Escape special characters
            sanitized = sanitized.replace("&", "&amp;")
            sanitized = sanitized.replace("<", "&lt;")
            sanitized = sanitized.replace(">", "&gt;")

            return sanitized.strip()

        except Exception as e:
            logger.error(f"Error sanitizing input: {str(e)}")
            return ""

    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)

    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        return secrets.compare_digest(token, session_token)


class ErrorHandler:
    """Advanced error handling system"""

    def __init__(self):
        self.error_log = []
        self.security_events = []
        self.error_count = {}
        self.security_validator = SecurityValidator()
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration"""
        try:
            # Create logs directory
            os.makedirs("logs", exist_ok=True)

            # Configure error logger
            error_handler = logging.FileHandler("logs/errors.log")
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
            error_handler.setFormatter(error_formatter)

            # Configure security logger
            security_handler = logging.FileHandler("logs/security.log")
            security_handler.setLevel(logging.WARNING)
            security_formatter = logging.Formatter(
                "%(asctime)s - SECURITY - %(levelname)s - %(message)s"
            )
            security_handler.setFormatter(security_formatter)

            # Add handlers to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(error_handler)
            root_logger.addHandler(security_handler)

        except Exception as e:
            print(f"Failed to setup logging: {str(e)}")

    def handle_error(
        self,
        error: Exception,
        level: ErrorLevel = ErrorLevel.ERROR,
        additional_data: Optional[Dict] = None,
    ) -> str:
        """Handle and log errors"""
        try:
            error_id = self._generate_error_id()

            # Get error details
            error_details = ErrorDetails(
                error_id=error_id,
                level=level,
                message=str(error),
                exception_type=type(error).__name__,
                stack_trace=traceback.format_exc(),
                timestamp=datetime.now(),
                user_id=self._get_current_user_id(),
                session_id=self._get_session_id(),
                additional_data=additional_data or {},
            )

            # Log error
            self._log_error(error_details)

            # Store error
            self.error_log.append(error_details)

            # Update error count
            error_type = type(error).__name__
            self.error_count[error_type] = self.error_count.get(error_type, 0) + 1

            # Check for critical errors
            if level == ErrorLevel.CRITICAL:
                self._handle_critical_error(error_details)

            return error_id

        except Exception as e:
            # Fallback error handling
            logger.critical(f"Error handler failed: {str(e)}")
            return "ERR_HANDLER_FAILED"

    def handle_security_event(
        self,
        threat_type: SecurityThreat,
        description: str,
        severity: str = "medium",
        blocked: bool = False,
        additional_data: Optional[Dict] = None,
    ) -> str:
        """Handle security events"""
        try:
            event_id = self._generate_error_id()

            security_event = SecurityEvent(
                event_id=event_id,
                threat_type=threat_type,
                severity=severity,
                description=description,
                timestamp=datetime.now(),
                user_id=self._get_current_user_id(),
                ip_address=self._get_client_ip(),
                user_agent=self._get_user_agent(),
                blocked=blocked,
                additional_data=additional_data or {},
            )

            # Log security event
            self._log_security_event(security_event)

            # Store event
            self.security_events.append(security_event)

            # Take action based on severity
            if severity == "critical":
                self._handle_critical_security_event(security_event)

            return event_id

        except Exception as e:
            logger.critical(f"Security event handler failed: {str(e)}")
            return "SEC_HANDLER_FAILED"

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        timestamp = str(int(time.time() * 1000))
        random_part = secrets.token_hex(4)
        return f"ERR_{timestamp}_{random_part}"

    def _get_current_user_id(self) -> Optional[int]:
        """Get current user ID from session"""
        try:
            user = st.session_state.get("user")
            return user.get("UserID") if user else None
        except:
            return None

    def _get_session_id(self) -> Optional[str]:
        """Get session ID"""
        try:
            return st.session_state.get("session_id", "unknown")
        except:
            return None

    def _get_client_ip(self) -> str:
        """Get client IP address"""
        try:
            # In Streamlit, this is limited - would need reverse proxy headers
            return "127.0.0.1"  # Placeholder
        except:
            return "unknown"

    def _get_user_agent(self) -> str:
        """Get user agent"""
        try:
            # Would need access to request headers
            return "Streamlit/Unknown"  # Placeholder
        except:
            return "unknown"

    def _log_error(self, error_details: ErrorDetails):
        """Log error details"""
        log_message = (
            f"Error ID: {error_details.error_id} | "
            f"Type: {error_details.exception_type} | "
            f"Message: {error_details.message} | "
            f"User: {error_details.user_id} | "
            f"Session: {error_details.session_id}"
        )

        if error_details.level == ErrorLevel.CRITICAL:
            logger.critical(log_message)
        elif error_details.level == ErrorLevel.ERROR:
            logger.error(log_message)
        elif error_details.level == ErrorLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def _log_security_event(self, event: SecurityEvent):
        """Log security event"""
        log_message = (
            f"Security Event ID: {event.event_id} | "
            f"Threat: {event.threat_type.value} | "
            f"Severity: {event.severity} | "
            f"Description: {event.description} | "
            f"User: {event.user_id} | "
            f"IP: {event.ip_address} | "
            f"Blocked: {event.blocked}"
        )

        if event.severity == "critical":
            logger.critical(f"SECURITY CRITICAL: {log_message}")
        else:
            logger.warning(f"SECURITY: {log_message}")

    def _handle_critical_error(self, error_details: ErrorDetails):
        """Handle critical errors"""
        try:
            # Send alert notifications
            self._send_alert_notification(f"Critical Error: {error_details.error_id}")

            # Log to critical error file
            with open("logs/critical_errors.log", "a") as f:
                f.write(
                    f"{datetime.now().isoformat()}: {error_details.error_id} - {error_details.message}\n"
                )

        except Exception as e:
            logger.error(f"Failed to handle critical error: {str(e)}")

    def _handle_critical_security_event(self, event: SecurityEvent):
        """Handle critical security events"""
        try:
            # Send security alert
            self._send_alert_notification(f"Security Alert: {event.threat_type.value}")

            # Log to security incidents file
            with open("logs/security_incidents.log", "a") as f:
                f.write(
                    f"{datetime.now().isoformat()}: {event.event_id} - {event.description}\n"
                )

        except Exception as e:
            logger.error(f"Failed to handle critical security event: {str(e)}")

    def _send_alert_notification(self, message: str):
        """Send alert notification (placeholder)"""
        # In a real implementation, this would send emails, Slack messages, etc.
        logger.critical(f"ALERT: {message}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        try:
            total_errors = len(self.error_log)
            recent_errors = len(
                [
                    error
                    for error in self.error_log
                    if (datetime.now() - error.timestamp).total_seconds() < 3600
                ]
            )

            error_types = {}
            for error in self.error_log:
                error_types[error.exception_type] = (
                    error_types.get(error.exception_type, 0) + 1
                )

            return {
                "total_errors": total_errors,
                "recent_errors_1h": recent_errors,
                "error_types": error_types,
                "most_common_error": (
                    max(error_types.items(), key=lambda x: x[1])[0]
                    if error_types
                    else None
                ),
            }
        except:
            return {}

    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics"""
        try:
            total_events = len(self.security_events)
            recent_events = len(
                [
                    event
                    for event in self.security_events
                    if (datetime.now() - event.timestamp).total_seconds() < 3600
                ]
            )

            threat_types = {}
            for event in self.security_events:
                threat_types[event.threat_type.value] = (
                    threat_types.get(event.threat_type.value, 0) + 1
                )

            blocked_events = len(
                [event for event in self.security_events if event.blocked]
            )

            return {
                "total_security_events": total_events,
                "recent_events_1h": recent_events,
                "blocked_events": blocked_events,
                "threat_types": threat_types,
                "blocked_ips": len(self.security_validator.blocked_ips),
            }
        except:
            return {}


def secure_operation(operation_name: str = None):
    """Decorator for secure operations with error handling"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate inputs if they're strings
                for arg in args:
                    if isinstance(arg, str):
                        is_valid, threat = (
                            error_handler.security_validator.validate_input(arg)
                        )
                        if not is_valid:
                            error_handler.handle_security_event(
                                threat,
                                f"Invalid input in {operation_name or func.__name__}",
                            )
                            raise ValueError("Invalid input detected")

                # Execute function
                return func(*args, **kwargs)

            except Exception as e:
                # Handle error
                error_id = error_handler.handle_error(
                    e, ErrorLevel.ERROR, {"operation": operation_name or func.__name__}
                )

                # Re-raise with error ID
                raise Exception(f"Operation failed (Error ID: {error_id}): {str(e)}")

        return wrapper

    return decorator


def handle_streamlit_errors():
    """Global Streamlit error handler"""
    try:
        # Check for errors in session state
        if "last_error" in st.session_state:
            error = st.session_state.last_error
            del st.session_state.last_error

            st.error(f"⚠️ An error occurred: {error}")

            with st.expander("Error Details"):
                st.code(error)

        # Add error reporting
        if st.button("🐛 Report Bug"):
            st.info("Bug reporting feature will be available soon!")

    except Exception as e:
        st.error(f"Error handler failed: {str(e)}")


def show_security_status():
    """Show security status information"""
    try:
        security_stats = error_handler.get_security_statistics()

        if security_stats:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Security Events (24h)", security_stats.get("recent_events_1h", 0)
                )

            with col2:
                st.metric("Blocked Events", security_stats.get("blocked_events", 0))

            with col3:
                st.metric("Blocked IPs", security_stats.get("blocked_ips", 0))

            if security_stats.get("threat_types"):
                st.bar_chart(security_stats["threat_types"])

    except Exception as e:
        st.error(f"Failed to load security status: {str(e)}")


# Global error handler instance
error_handler = ErrorHandler()


# Export functions
def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    return error_handler


def get_security_validator() -> SecurityValidator:
    """Get security validator instance"""
    return error_handler.security_validator
