#!/usr/bin/env python3
"""
modules/auth.py
Enterprise Authentication and Authorization System
Production-ready security with role-based access control
"""

import bcrypt
import streamlit as st
import logging
import secrets
import jwt
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import ipaddress
from functools import wraps

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Enterprise user roles"""

    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin"
    PROJECT_MANAGER = "Project Manager"
    TEAM_LEAD = "Team Lead"
    SENIOR_DEVELOPER = "Senior Developer"
    DEVELOPER = "Developer"
    DESIGNER = "Designer"
    ANALYST = "Analyst"
    USER = "User"
    VIEWER = "Viewer"
    GUEST = "Guest"


class Permission(Enum):
    """Granular permission system"""

    # User Management
    CREATE_USER = "user:create"
    READ_USER = "user:read"
    UPDATE_USER = "user:update"
    DELETE_USER = "user:delete"
    MANAGE_ROLES = "user:manage_roles"

    # Project Management
    CREATE_PROJECT = "project:create"
    READ_PROJECT = "project:read"
    UPDATE_PROJECT = "project:update"
    DELETE_PROJECT = "project:delete"
    MANAGE_PROJECT_MEMBERS = "project:manage_members"
    ARCHIVE_PROJECT = "project:archive"

    # Task Management
    CREATE_TASK = "task:create"
    READ_TASK = "task:read"
    UPDATE_TASK = "task:update"
    DELETE_TASK = "task:delete"
    ASSIGN_TASK = "task:assign"
    CHANGE_TASK_STATUS = "task:change_status"

    # Time Tracking
    TRACK_TIME = "time:track"
    VIEW_TIME_REPORTS = "time:view_reports"
    EDIT_TIME_ENTRIES = "time:edit"

    # Analytics & Reporting
    VIEW_ANALYTICS = "analytics:view"
    CREATE_REPORTS = "analytics:create_reports"
    EXPORT_DATA = "analytics:export"
    VIEW_FINANCIAL_DATA = "analytics:financial"

    # System Administration
    MANAGE_SETTINGS = "system:settings"
    VIEW_AUDIT_LOG = "system:audit"
    MANAGE_DATABASE = "system:database"
    BACKUP_RESTORE = "system:backup"
    MANAGE_INTEGRATIONS = "system:integrations"

    # File Management
    UPLOAD_FILES = "files:upload"
    DELETE_FILES = "files:delete"
    MANAGE_FILE_PERMISSIONS = "files:permissions"


@dataclass
class LoginAttempt:
    """Login attempt tracking"""

    user_id: Optional[int]
    username: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SecurityEvent:
    """Security event logging"""

    event_type: str
    user_id: Optional[int]
    ip_address: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: datetime
    additional_data: Optional[Dict] = None


class PasswordPolicy:
    """Enterprise password policy"""

    def __init__(self):
        self.min_length = 8
        self.max_length = 128
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special = True
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        self.max_repeated_chars = 3
        self.password_history = 5
        self.min_age_hours = 24
        self.max_age_days = 90

    def validate_password(
        self, password: str, username: str = None
    ) -> Tuple[bool, List[str]]:
        """Validate password against policy"""
        errors = []

        if len(password) < self.min_length:
            errors.append(f"รหัสผ่านต้องมีอย่างน้อย {self.min_length} ตัวอักษร")

        if len(password) > self.max_length:
            errors.append(f"รหัสผ่านต้องไม่เกิน {self.max_length} ตัวอักษร")

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("รหัสผ่านต้องมีตัวอักษรภาษาอังกฤษตัวใหญ่")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("รหัสผ่านต้องมีตัวอักษรภาษาอังกฤษตัวเล็ก")

        if self.require_numbers and not re.search(r"\d", password):
            errors.append("รหัสผ่านต้องมีตัวเลข")

        if self.require_special and not re.search(
            f"[{re.escape(self.special_chars)}]", password
        ):
            errors.append("รหัสผ่านต้องมีอักขระพิเศษ")

        # Check for repeated characters
        if self._has_repeated_chars(password, self.max_repeated_chars):
            errors.append(f"รหัสผ่านต้องไม่มีตัวอักษรซ้ำกันเกิน {self.max_repeated_chars} ตัว")

        # Check against username
        if username and username.lower() in password.lower():
            errors.append("รหัสผ่านต้องไม่ใช้ชื่อผู้ใช้งาน")

        # Check common passwords
        if self._is_common_password(password):
            errors.append("รหัสผ่านนี้ใช้กันทั่วไป กรุณาเลือกรหัสผ่านที่ปลอดภัยกว่า")

        return len(errors) == 0, errors

    def _has_repeated_chars(self, password: str, max_repeated: int) -> bool:
        """Check for repeated characters"""
        count = 1
        prev_char = password[0] if password else ""

        for char in password[1:]:
            if char == prev_char:
                count += 1
                if count > max_repeated:
                    return True
            else:
                count = 1
                prev_char = char

        return False

    def _is_common_password(self, password: str) -> bool:
        """Check against common passwords"""
        common_passwords = {
            "password",
            "12345678",
            "qwerty123",
            "admin123",
            "password123",
            "123456789",
            "welcome123",
            "letmein",
            "changeme",
            "monkey123",
            "dragon123",
            "master123",
        }
        return password.lower() in common_passwords


class SecurityManager:
    """Advanced security management"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.failed_attempts = {}  # IP -> count
        self.blocked_ips = set()
        self.session_tokens = {}  # token -> user_data
        self.password_policy = PasswordPolicy()
        self.jwt_secret = self._get_jwt_secret()

    def _get_jwt_secret(self) -> str:
        """Get or generate JWT secret"""
        try:
            secret = self.db.execute_scalar(
                "SELECT SettingValue FROM SystemSettings WHERE SettingKey = ?",
                ("jwt_secret",),
            )
            if not secret:
                secret = secrets.token_urlsafe(64)
                self.db.execute_query(
                    "INSERT INTO SystemSettings (SettingKey, SettingValue, Description) VALUES (?, ?, ?)",
                    ("jwt_secret", secret, "JWT signing secret"),
                )
            return secret
        except:
            return secrets.token_urlsafe(64)

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except:
            return False

    def generate_session_token(self, user_data: Dict) -> str:
        """Generate secure session token"""
        payload = {
            "user_id": user_data["UserID"],
            "username": user_data["Username"],
            "role": user_data["Role"],
            "exp": datetime.utcnow() + timedelta(hours=8),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        self.session_tokens[token] = user_data
        return token

    def validate_session_token(self, token: str) -> Optional[Dict]:
        """Validate session token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return self.session_tokens.get(token)
        except jwt.ExpiredSignatureError:
            if token in self.session_tokens:
                del self.session_tokens[token]
            return None
        except jwt.InvalidTokenError:
            return None

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips

    def block_ip(self, ip_address: str, duration_minutes: int = 30):
        """Block IP address"""
        self.blocked_ips.add(ip_address)
        # In production, implement timed blocks

    def record_failed_attempt(self, ip_address: str, username: str):
        """Record failed login attempt"""
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []

        self.failed_attempts[ip_address].append(
            {"username": username, "timestamp": datetime.now()}
        )

        # Block after 5 failed attempts
        if len(self.failed_attempts[ip_address]) >= 5:
            self.block_ip(ip_address)
            logger.warning(f"IP blocked due to failed attempts: {ip_address}")

    def log_security_event(self, event: SecurityEvent):
        """Log security event"""
        try:
            self.db.execute_query(
                """
                INSERT INTO AuditLog (UserID, Action, TableName, IPAddress, CreatedAt, UserAgent)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    event.user_id,
                    f"SECURITY_{event.event_type}",
                    "Security",
                    event.ip_address,
                    event.timestamp,
                    f"{event.severity}: {event.description}",
                ),
            )

            if event.severity in ["HIGH", "CRITICAL"]:
                logger.warning(f"Security event: {event.description}")

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")


class AuthenticationManager:
    """Enterprise authentication manager"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.security = SecurityManager(db_manager)
        self.role_permissions = self._initialize_permissions()

    def _initialize_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-based permissions"""
        return {
            UserRole.SUPER_ADMIN: list(Permission),
            UserRole.ADMIN: [
                Permission.CREATE_USER,
                Permission.READ_USER,
                Permission.UPDATE_USER,
                Permission.CREATE_PROJECT,
                Permission.READ_PROJECT,
                Permission.UPDATE_PROJECT,
                Permission.DELETE_PROJECT,
                Permission.MANAGE_PROJECT_MEMBERS,
                Permission.CREATE_TASK,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.DELETE_TASK,
                Permission.ASSIGN_TASK,
                Permission.VIEW_ANALYTICS,
                Permission.CREATE_REPORTS,
                Permission.EXPORT_DATA,
                Permission.MANAGE_SETTINGS,
                Permission.VIEW_AUDIT_LOG,
                Permission.UPLOAD_FILES,
                Permission.DELETE_FILES,
            ],
            UserRole.PROJECT_MANAGER: [
                Permission.READ_USER,
                Permission.CREATE_PROJECT,
                Permission.READ_PROJECT,
                Permission.UPDATE_PROJECT,
                Permission.MANAGE_PROJECT_MEMBERS,
                Permission.CREATE_TASK,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.ASSIGN_TASK,
                Permission.CHANGE_TASK_STATUS,
                Permission.VIEW_TIME_REPORTS,
                Permission.VIEW_ANALYTICS,
                Permission.CREATE_REPORTS,
                Permission.EXPORT_DATA,
                Permission.UPLOAD_FILES,
            ],
            UserRole.TEAM_LEAD: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.UPDATE_PROJECT,
                Permission.CREATE_TASK,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.ASSIGN_TASK,
                Permission.CHANGE_TASK_STATUS,
                Permission.TRACK_TIME,
                Permission.VIEW_TIME_REPORTS,
                Permission.UPLOAD_FILES,
            ],
            UserRole.SENIOR_DEVELOPER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.CREATE_TASK,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.TRACK_TIME,
                Permission.UPLOAD_FILES,
            ],
            UserRole.DEVELOPER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.TRACK_TIME,
                Permission.UPLOAD_FILES,
            ],
            UserRole.DESIGNER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.TRACK_TIME,
                Permission.UPLOAD_FILES,
            ],
            UserRole.ANALYST: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_TIME_REPORTS,
                Permission.EXPORT_DATA,
            ],
            UserRole.USER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.TRACK_TIME,
            ],
            UserRole.VIEWER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
            ],
            UserRole.GUEST: [Permission.READ_PROJECT, Permission.READ_TASK],
        }

    def register_user(self, user_data: Dict) -> Tuple[bool, str]:
        """Register new user with validation"""
        try:
            # Validate required fields
            required_fields = ["username", "password", "email", "full_name"]
            for field in required_fields:
                if not user_data.get(field):
                    return False, f"กรุณากรอก {field}"

            # Validate password
            is_valid, errors = self.security.password_policy.validate_password(
                user_data["password"], user_data["username"]
            )
            if not is_valid:
                return False, ". ".join(errors)

            # Check username uniqueness
            existing_user = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Username = ?",
                (user_data["username"],),
            )
            if existing_user > 0:
                return False, "ชื่อผู้ใช้งานนี้มีคนใช้แล้ว"

            # Check email uniqueness
            existing_email = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Email = ?", (user_data["email"],)
            )
            if existing_email > 0:
                return False, "อีเมลนี้มีคนใช้แล้ว"

            # Hash password
            password_hash = self.security.hash_password(user_data["password"])

            # Insert user
            self.db.execute_query(
                """
                INSERT INTO Users (Username, PasswordHash, FullName, Email, Role, Department, Position, Phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_data["username"],
                    password_hash,
                    user_data["full_name"],
                    user_data["email"],
                    user_data.get("role", "User"),
                    user_data.get("department", ""),
                    user_data.get("position", ""),
                    user_data.get("phone", ""),
                ),
            )

            logger.info(f"User registered: {user_data['username']}")
            return True, "สร้างบัญชีผู้ใช้สำเร็จ"

        except Exception as e:
            logger.error(f"User registration failed: {e}")
            return False, "เกิดข้อผิดพลาดในการสร้างบัญชี"

    def login(
        self,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Optional[Dict]:
        """Authenticate user with security checks"""
        try:
            if not ip_address:
                ip_address = "127.0.0.1"

            # Check if IP is blocked
            if self.security.is_ip_blocked(ip_address):
                return None

            # Get user data
            user = self.db.execute_query(
                "SELECT * FROM Users WHERE Username = ? AND IsActive = 1", (username,)
            )

            if not user:
                self.security.record_failed_attempt(ip_address, username)
                self._log_login_attempt(
                    None, username, ip_address, False, "User not found"
                )
                return None

            user = user[0]

            # Verify password
            if not self.security.verify_password(password, user["PasswordHash"]):
                self.security.record_failed_attempt(ip_address, username)
                self._log_login_attempt(
                    user["UserID"], username, ip_address, False, "Invalid password"
                )
                return None

            # Update last login
            self.db.execute_query(
                "UPDATE Users SET LastLogin = ? WHERE UserID = ?",
                (datetime.now(), user["UserID"]),
            )

            # Log successful login
            self._log_login_attempt(user["UserID"], username, ip_address, True)

            # Clear failed attempts for this IP
            if ip_address in self.security.failed_attempts:
                del self.security.failed_attempts[ip_address]

            logger.info(f"Successful login: {username} from {ip_address}")
            return user

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return None

    def _log_login_attempt(
        self,
        user_id: Optional[int],
        username: str,
        ip_address: str,
        success: bool,
        failure_reason: str = None,
    ):
        """Log login attempt"""
        try:
            self.db.execute_query(
                """
                INSERT INTO AuditLog (UserID, Action, IPAddress, UserAgent, CreatedAt)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    f"LOGIN_{'SUCCESS' if success else 'FAILURE'}",
                    ip_address,
                    f"User: {username}"
                    + (f" | Reason: {failure_reason}" if failure_reason else ""),
                    datetime.now(),
                ),
            )
        except Exception as e:
            logger.error(f"Failed to log login attempt: {e}")

    def logout(self, user_id: int, session_token: str = None):
        """Logout user and cleanup session"""
        try:
            if session_token and session_token in self.security.session_tokens:
                del self.security.session_tokens[session_token]

            self.db.execute_query(
                """
                INSERT INTO AuditLog (UserID, Action, CreatedAt)
                VALUES (?, ?, ?)
            """,
                (user_id, "LOGOUT", datetime.now()),
            )

            logger.info(f"User logged out: {user_id}")

        except Exception as e:
            logger.error(f"Logout failed: {e}")

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> Tuple[bool, str]:
        """Change user password with validation"""
        try:
            # Get current user
            user = self.db.execute_query(
                "SELECT * FROM Users WHERE UserID = ?", (user_id,)
            )

            if not user:
                return False, "ไม่พบผู้ใช้งาน"

            user = user[0]

            # Verify old password
            if not self.security.verify_password(old_password, user["PasswordHash"]):
                return False, "รหัสผ่านเดิมไม่ถูกต้อง"

            # Validate new password
            is_valid, errors = self.security.password_policy.validate_password(
                new_password, user["Username"]
            )
            if not is_valid:
                return False, ". ".join(errors)

            # Hash new password
            new_hash = self.security.hash_password(new_password)

            # Update password
            self.db.execute_query(
                "UPDATE Users SET PasswordHash = ?, UpdatedAt = ? WHERE UserID = ?",
                (new_hash, datetime.now(), user_id),
            )

            # Log password change
            self.db.execute_query(
                """
                INSERT INTO AuditLog (UserID, Action, CreatedAt)
                VALUES (?, ?, ?)
            """,
                (user_id, "PASSWORD_CHANGE", datetime.now()),
            )

            logger.info(f"Password changed for user: {user_id}")
            return True, "เปลี่ยนรหัสผ่านสำเร็จ"

        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return False, "เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน"

    def get_user_permissions(self, role: str) -> List[Permission]:
        """Get permissions for user role"""
        try:
            user_role = UserRole(role)
            return self.role_permissions.get(user_role, [])
        except ValueError:
            logger.warning(f"Unknown role: {role}")
            return []

    def has_permission(self, user_role: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user_role)
        return permission in user_permissions

    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not st.session_state.get("authenticated"):
                    st.error("❌ กรุณาเข้าสู่ระบบ")
                    return None

                user_role = st.session_state.get("user_role")
                if not self.has_permission(user_role, permission):
                    st.error("❌ คุณไม่มีสิทธิ์ในการดำเนินการนี้")
                    return None

                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_users_by_role(self, role: str) -> List[Dict]:
        """Get users by role"""
        try:
            users = self.db.execute_query(
                "SELECT * FROM Users WHERE Role = ? AND IsActive = 1 ORDER BY FullName",
                (role,),
            )
            return users
        except Exception as e:
            logger.error(f"Failed to get users by role: {e}")
            return []

    def get_user_activity(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get user activity from audit log"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            activities = self.db.execute_query(
                """
                SELECT * FROM AuditLog 
                WHERE UserID = ? AND CreatedAt >= ?
                ORDER BY CreatedAt DESC
                LIMIT 50
            """,
                (user_id, since_date),
            )

            return activities
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return []

    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        try:
            # Failed login attempts in last 24 hours
            since_24h = datetime.now() - timedelta(hours=24)
            failed_logins = self.db.execute_scalar(
                """
                SELECT COUNT(*) FROM AuditLog 
                WHERE Action = 'LOGIN_FAILURE' AND CreatedAt >= ?
            """,
                (since_24h,),
            )

            # Active sessions
            active_sessions = len(self.security.session_tokens)

            # Blocked IPs
            blocked_ips = len(self.security.blocked_ips)

            # Recent security events
            recent_events = self.db.execute_query(
                """
                SELECT * FROM AuditLog 
                WHERE Action LIKE 'SECURITY_%' 
                ORDER BY CreatedAt DESC 
                LIMIT 10
            """
            )

            return {
                "failed_logins_24h": failed_logins or 0,
                "active_sessions": active_sessions,
                "blocked_ips": blocked_ips,
                "recent_events": recent_events or [],
            }

        except Exception as e:
            logger.error(f"Failed to get security dashboard: {e}")
            return {
                "failed_logins_24h": 0,
                "active_sessions": 0,
                "blocked_ips": 0,
                "recent_events": [],
            }
