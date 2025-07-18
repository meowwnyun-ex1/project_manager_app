#!/usr/bin/env python3
"""
modules/auth.py
Enterprise Authentication and Authorization System
Production-ready security with comprehensive features
"""

import bcrypt
import streamlit as st
import logging
import secrets
import jwt
import hashlib
import time
import ipaddress
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import json
from pathlib import Path
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Enterprise user roles with hierarchy"""

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
    RESET_PASSWORD = "user:reset_password"

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
    APPROVE_TIMESHEETS = "time:approve"

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
    """Login attempt tracking with metadata"""

    user_id: Optional[int]
    username: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None
    session_id: Optional[str] = None
    geolocation: Optional[str] = None
    device_fingerprint: Optional[str] = None


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


@dataclass
class UserSession:
    """User session management"""

    session_id: str
    user_id: int
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True
    expires_at: Optional[datetime] = None


class PasswordPolicy:
    """Enterprise password policy with configurable rules"""

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.min_length = config.get("min_length", 12)
        self.max_length = config.get("max_length", 128)
        self.require_uppercase = config.get("require_uppercase", True)
        self.require_lowercase = config.get("require_lowercase", True)
        self.require_numbers = config.get("require_numbers", True)
        self.require_special = config.get("require_special", True)
        self.special_chars = config.get("special_chars", "!@#$%^&*()_+-=[]{}|;:,.<>?")
        self.max_repeated_chars = config.get("max_repeated_chars", 2)
        self.password_history = config.get("password_history", 12)
        self.min_age_hours = config.get("min_age_hours", 24)
        self.max_age_days = config.get("max_age_days", 90)
        self.common_passwords = self._load_common_passwords()

    def _load_common_passwords(self) -> set:
        """Load common passwords to block"""
        common = {
            "password",
            "123456",
            "12345678",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
            "master",
            "hello",
            "login",
            "pass",
            "1234567890",
        }
        return common

    def validate_password(
        self, password: str, username: str = None, old_passwords: List[str] = None
    ) -> Tuple[bool, List[str]]:
        """Comprehensive password validation"""
        errors = []

        # Length checks
        if len(password) < self.min_length:
            errors.append(f"รหัสผ่านต้องมีอย่างน้อย {self.min_length} ตัวอักษร")

        if len(password) > self.max_length:
            errors.append(f"รหัสผ่านต้องไม่เกิน {self.max_length} ตัวอักษร")

        # Character requirement checks
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("รหัสผ่านต้องมีตัวอักษรภาษาอังกฤษตัวใหญ่")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("รหัสผ่านต้องมีตัวอักษรภาษาอังกฤษตัวเล็ก")

        if self.require_numbers and not re.search(r"\d", password):
            errors.append("รหัสผ่านต้องมีตัวเลข")

        if self.require_special and not re.search(
            f"[{re.escape(self.special_chars)}]", password
        ):
            errors.append("รหัสผ่านต้องมีตัวอักษรพิเศษ")

        # Pattern checks
        if self._has_repeated_chars(password):
            errors.append(f"รหัสผ่านต้องไม่มีตัวอักษรซ้ำเกิน {self.max_repeated_chars} ตัว")

        # Common password check
        if password.lower() in self.common_passwords:
            errors.append("รหัสผ่านนี้ใช้กันทั่วไปเกินไป กรุณาเลือกรหัสผ่านที่ปลอดภัยกว่า")

        # Username similarity check
        if username and self._is_similar_to_username(password, username):
            errors.append("รหัสผ่านต้องไม่คล้ายกับชื่อผู้ใช้")

        # Password history check
        if old_passwords and self._is_in_history(password, old_passwords):
            errors.append(f"ไม่สามารถใช้รหัสผ่านเดิม {self.password_history} รหัสผ่านล่าสุด")

        # Entropy check
        if not self._has_sufficient_entropy(password):
            errors.append("รหัสผ่านมีความซับซ้อนไม่เพียงพอ")

        return len(errors) == 0, errors

    def _has_repeated_chars(self, password: str) -> bool:
        """Check for repeated characters"""
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i - 1]:
                count += 1
                if count > self.max_repeated_chars:
                    return True
            else:
                count = 1
        return False

    def _is_similar_to_username(self, password: str, username: str) -> bool:
        """Check if password is similar to username"""
        password_lower = password.lower()
        username_lower = username.lower()

        # Check if username is contained in password
        if username_lower in password_lower or password_lower in username_lower:
            return True

        # Check Levenshtein distance
        return self._levenshtein_distance(password_lower, username_lower) < 3

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _is_in_history(self, password: str, old_passwords: List[str]) -> bool:
        """Check if password is in history"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        for old_hash in old_passwords:
            if password_hash == old_hash:
                return True
        return False

    def _has_sufficient_entropy(self, password: str) -> bool:
        """Check password entropy"""
        import math

        # Calculate character space
        char_space = 0
        if re.search(r"[a-z]", password):
            char_space += 26
        if re.search(r"[A-Z]", password):
            char_space += 26
        if re.search(r"\d", password):
            char_space += 10
        if re.search(f"[{re.escape(self.special_chars)}]", password):
            char_space += len(self.special_chars)

        # Calculate entropy
        entropy = len(password) * math.log2(char_space)
        return entropy >= 50  # Minimum 50 bits of entropy

    def generate_password(self, length: int = None) -> str:
        """Generate secure password meeting policy requirements"""
        length = length or max(self.min_length, 16)

        # Character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = self.special_chars

        # Ensure at least one from each required set
        password = []
        if self.require_lowercase:
            password.append(secrets.choice(lowercase))
        if self.require_uppercase:
            password.append(secrets.choice(uppercase))
        if self.require_numbers:
            password.append(secrets.choice(digits))
        if self.require_special:
            password.append(secrets.choice(special))

        # Fill remaining length
        all_chars = ""
        if self.require_lowercase:
            all_chars += lowercase
        if self.require_uppercase:
            all_chars += uppercase
        if self.require_numbers:
            all_chars += digits
        if self.require_special:
            all_chars += special

        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        return "".join(password)


class SecurityManager:
    """Enterprise security management"""

    def __init__(self, db_manager=None):
        self.db = db_manager
        self.password_policy = PasswordPolicy()
        self.failed_attempts = defaultdict(list)
        self.locked_accounts = {}
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.session_timeout = timedelta(hours=8)
        self.active_sessions = {}
        self._lock = threading.Lock()

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with strong salt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        with self._lock:
            if username in self.locked_accounts:
                lock_time = self.locked_accounts[username]
                if datetime.now() - lock_time > self.lockout_duration:
                    # Unlock account
                    del self.locked_accounts[username]
                    if username in self.failed_attempts:
                        del self.failed_attempts[username]
                    return False
                return True
            return False

    def track_failed_attempt(self, username: str, ip_address: str) -> None:
        """Track failed login attempt"""
        with self._lock:
            now = datetime.now()

            # Clean old attempts (older than lockout duration)
            cutoff = now - self.lockout_duration
            self.failed_attempts[username] = [
                attempt
                for attempt in self.failed_attempts[username]
                if attempt["timestamp"] > cutoff
            ]

            # Add new attempt
            self.failed_attempts[username].append(
                {"timestamp": now, "ip_address": ip_address}
            )

            # Check if should lock account
            if len(self.failed_attempts[username]) >= self.max_attempts:
                self.locked_accounts[username] = now
                logger.warning(f"Account locked due to failed attempts: {username}")

    def track_successful_login(self, username: str) -> None:
        """Track successful login and clear failed attempts"""
        with self._lock:
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            if username in self.locked_accounts:
                del self.locked_accounts[username]

    def create_session(self, user_id: int, ip_address: str, user_agent: str) -> str:
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now()

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=now + self.session_timeout,
        )

        self.active_sessions[session_id] = session

        # Store in database if available
        if self.db:
            self._save_session_to_db(session)

        return session_id

    def validate_session(
        self, session_id: str, ip_address: str = None
    ) -> Optional[UserSession]:
        """Validate session and update activity"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        now = datetime.now()

        # Check if session expired
        if session.expires_at and now > session.expires_at:
            self.invalidate_session(session_id)
            return None

        # Check IP consistency (optional security measure)
        if ip_address and session.ip_address != ip_address:
            logger.warning(f"IP address mismatch for session {session_id}")
            # Could invalidate session here for strict security

        # Update last activity
        session.last_activity = now
        session.expires_at = now + self.session_timeout

        return session

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_active = False
            del self.active_sessions[session_id]

            # Update database
            if self.db:
                self._invalidate_session_in_db(session_id)

            return True
        return False

    def invalidate_user_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user"""
        count = 0
        sessions_to_remove = []

        for session_id, session in self.active_sessions.items():
            if session.user_id == user_id:
                sessions_to_remove.append(session_id)
                count += 1

        for session_id in sessions_to_remove:
            self.invalidate_session(session_id)

        return count

    def _save_session_to_db(self, session: UserSession) -> None:
        """Save session to database"""
        try:
            query = """
                INSERT INTO user_sessions (
                    session_id, user_id, created_at, last_activity,
                    ip_address, user_agent, expires_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute(
                query,
                (
                    session.session_id,
                    session.user_id,
                    session.created_at.isoformat(),
                    session.last_activity.isoformat(),
                    session.ip_address,
                    session.user_agent,
                    session.expires_at.isoformat() if session.expires_at else None,
                    session.is_active,
                ),
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save session to database: {e}")

    def _invalidate_session_in_db(self, session_id: str) -> None:
        """Invalidate session in database"""
        try:
            query = "UPDATE user_sessions SET is_active = 0 WHERE session_id = ?"
            self.db.execute(query, (session_id,))
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to invalidate session in database: {e}")

    def log_security_event(self, event: SecurityEvent) -> None:
        """Log security event"""
        try:
            logger.info(f"Security event: {event.event_type} - {event.description}")

            if self.db:
                query = """
                    INSERT INTO security_events (
                        event_type, user_id, ip_address, description,
                        severity, timestamp, additional_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                self.db.execute(
                    query,
                    (
                        event.event_type,
                        event.user_id,
                        event.ip_address,
                        event.description,
                        event.severity,
                        event.timestamp.isoformat(),
                        (
                            json.dumps(event.additional_data)
                            if event.additional_data
                            else None
                        ),
                    ),
                )
                self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        now = datetime.now()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if session.expires_at and now > session.expires_at:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.invalidate_session(session_id)

        return len(expired_sessions)


class PermissionManager:
    """Role-based access control manager"""

    def __init__(self):
        self.role_permissions = self._initialize_permissions()

    def _initialize_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-based permissions matrix"""
        return {
            UserRole.SUPER_ADMIN: list(Permission),
            UserRole.ADMIN: [
                Permission.CREATE_USER,
                Permission.READ_USER,
                Permission.UPDATE_USER,
                Permission.MANAGE_ROLES,
                Permission.RESET_PASSWORD,
                Permission.CREATE_PROJECT,
                Permission.READ_PROJECT,
                Permission.UPDATE_PROJECT,
                Permission.DELETE_PROJECT,
                Permission.MANAGE_PROJECT_MEMBERS,
                Permission.ARCHIVE_PROJECT,
                Permission.CREATE_TASK,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.DELETE_TASK,
                Permission.ASSIGN_TASK,
                Permission.CHANGE_TASK_STATUS,
                Permission.VIEW_TIME_REPORTS,
                Permission.EDIT_TIME_ENTRIES,
                Permission.APPROVE_TIMESHEETS,
                Permission.VIEW_ANALYTICS,
                Permission.CREATE_REPORTS,
                Permission.EXPORT_DATA,
                Permission.VIEW_FINANCIAL_DATA,
                Permission.MANAGE_SETTINGS,
                Permission.VIEW_AUDIT_LOG,
                Permission.BACKUP_RESTORE,
                Permission.UPLOAD_FILES,
                Permission.DELETE_FILES,
                Permission.MANAGE_FILE_PERMISSIONS,
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
                Permission.APPROVE_TIMESHEETS,
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
                Permission.CREATE_REPORTS,
                Permission.EXPORT_DATA,
                Permission.TRACK_TIME,
            ],
            UserRole.USER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
                Permission.TRACK_TIME,
            ],
            UserRole.VIEWER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
            ],
            UserRole.GUEST: [Permission.READ_PROJECT],
        }

    def user_has_permission(self, user_role: str, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        try:
            role_enum = UserRole(user_role)
            return permission in self.role_permissions.get(role_enum, [])
        except ValueError:
            logger.warning(f"Unknown user role: {user_role}")
            return False

    def get_user_permissions(self, user_role: str) -> List[Permission]:
        """Get all permissions for a user role"""
        try:
            role_enum = UserRole(user_role)
            return self.role_permissions.get(role_enum, [])
        except ValueError:
            return []

    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not st.session_state.get("authenticated", False):
                    st.error("❌ กรุณาเข้าสู่ระบบ")
                    st.stop()

                user = st.session_state.get("user", {})
                user_role = user.get("Role", "Guest")

                if not self.user_has_permission(user_role, permission):
                    st.error("❌ คุณไม่มีสิทธิ์ในการดำเนินการนี้")
                    st.stop()

                return func(*args, **kwargs)

            return wrapper

        return decorator


class AuthenticationManager:
    """Main authentication manager"""

    def __init__(self, db_manager, config: Dict[str, Any] = None):
        self.db = db_manager
        self.config = config or {}
        self.security = SecurityManager(db_manager)
        self.permissions = PermissionManager()

        # JWT configuration
        self.jwt_secret = self.config.get("jwt_secret", secrets.token_urlsafe(32))
        self.jwt_algorithm = "HS256"
        self.jwt_expiry = timedelta(hours=8)

    def authenticate_user(
        self, username: str, password: str, ip_address: str = "", user_agent: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with comprehensive security"""
        try:
            # Check if account is locked
            if self.security.is_account_locked(username):
                logger.warning(f"Login attempt on locked account: {username}")
                st.error("⚠️ บัญชีถูกล็อกชั่วคราว กรุณาลองใหม่ภายหลัง")
                return None

            # Get user from database
            query = """
                SELECT UserID, Username, PasswordHash, Email, FirstName, LastName, 
                       Role, Department, Phone, IsActive, LastLoginDate, PasswordChangedAt
                FROM Users 
                WHERE Username = ? AND IsActive = 1
            """

            result = self.db.execute(query, (username,)).fetchone()

            if not result:
                self.security.track_failed_attempt(username, ip_address)
                logger.warning(f"Login attempt with non-existent username: {username}")
                return None

            user = dict(result)

            # Verify password
            if not self.security.verify_password(password, user["PasswordHash"]):
                self.security.track_failed_attempt(username, ip_address)
                logger.warning(f"Failed password for user: {username}")
                return None

            # Check password expiry
            if self._is_password_expired(user.get("PasswordChangedAt")):
                st.warning("⚠️ รหัสผ่านหมดอายุ กรุณาเปลี่ยนรหัสผ่าน")
                # Could redirect to password change page

            # Track successful login
            self.security.track_successful_login(username)

            # Create session
            session_id = self.security.create_session(
                user["UserID"], ip_address, user_agent
            )

            # Update last login
            self._update_last_login(user["UserID"], ip_address)

            # Log security event
            self.security.log_security_event(
                SecurityEvent(
                    event_type="USER_LOGIN",
                    user_id=user["UserID"],
                    ip_address=ip_address,
                    description=f"Successful login for user {username}",
                    severity="LOW",
                    timestamp=datetime.now(),
                )
            )

            # Remove sensitive data
            user.pop("PasswordHash", None)
            user["SessionID"] = session_id

            logger.info(f"Successful login: {username}")
            return user

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def _is_password_expired(self, password_changed_at: str) -> bool:
        """Check if password has expired"""
        if not password_changed_at:
            return True

        try:
            changed_date = datetime.fromisoformat(password_changed_at)
            expiry_date = changed_date + timedelta(
                days=self.security.password_policy.max_age_days
            )
            return datetime.now() > expiry_date
        except Exception:
            return True

    def _update_last_login(self, user_id: int, ip_address: str) -> None:
        """Update user's last login information"""
        try:
            query = """
                UPDATE Users 
                SET LastLoginDate = ?, LastLoginIP = ?
                WHERE UserID = ?
            """
            self.db.execute(query, (datetime.now().isoformat(), ip_address, user_id))
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update last login: {e}")

    def create_user(self, user_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Create new user with validation"""
        try:
            # Validate required fields
            required_fields = [
                "username",
                "password",
                "email",
                "first_name",
                "last_name",
                "role",
            ]
            for field in required_fields:
                if not user_data.get(field):
                    return False, f"Missing required field: {field}"

            # Validate password strength
            is_valid, errors = self.security.password_policy.validate_password(
                user_data["password"], user_data["username"]
            )
            if not is_valid:
                return False, "; ".join(errors)

            # Check if username or email already exists
            check_query = "SELECT UserID FROM Users WHERE Username = ? OR Email = ?"
            existing = self.db.execute(
                check_query, (user_data["username"], user_data["email"])
            ).fetchone()

            if existing:
                return False, "Username or email already exists"

            # Validate role
            try:
                UserRole(user_data["role"])
            except ValueError:
                return False, f"Invalid role: {user_data['role']}"

            # Hash password
            password_hash = self.security.hash_password(user_data["password"])

            # Insert user
            insert_query = """
                INSERT INTO Users (
                    Username, PasswordHash, Email, FirstName, LastName,
                    Role, Department, Phone, IsActive, CreatedDate, PasswordChangedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute(
                insert_query,
                (
                    user_data["username"],
                    password_hash,
                    user_data["email"],
                    user_data["first_name"],
                    user_data["last_name"],
                    user_data["role"],
                    user_data.get("department", ""),
                    user_data.get("phone", ""),
                    True,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            self.db.commit()

            logger.info(f"User created successfully: {user_data['username']}")
            return True, "User created successfully"

        except Exception as e:
            logger.error(f"User creation error: {e}")
            return False, f"Failed to create user: {str(e)}"

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> Tuple[bool, str]:
        """Change user password with validation"""
        try:
            # Get current user
            query = "SELECT Username, PasswordHash FROM Users WHERE UserID = ?"
            result = self.db.execute(query, (user_id,)).fetchone()

            if not result:
                return False, "User not found"

            username, current_hash = result

            # Verify old password
            if not self.security.verify_password(old_password, current_hash):
                return False, "Current password is incorrect"

            # Get password history
            history_query = """
                SELECT password_hash FROM password_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """
            history = self.db.execute(
                history_query, (user_id, self.security.password_policy.password_history)
            ).fetchall()

            old_hashes = [row[0] for row in history]

            # Validate new password
            is_valid, errors = self.security.password_policy.validate_password(
                new_password, username, old_hashes
            )

            if not is_valid:
                return False, "; ".join(errors)

            # Hash new password
            new_hash = self.security.hash_password(new_password)

            # Update password
            update_query = """
                UPDATE Users 
                SET PasswordHash = ?, PasswordChangedAt = ?
                WHERE UserID = ?
            """
            self.db.execute(
                update_query, (new_hash, datetime.now().isoformat(), user_id)
            )

            # Store in password history
            history_insert = """
                INSERT INTO password_history (user_id, password_hash, created_at)
                VALUES (?, ?, ?)
            """
            self.db.execute(
                history_insert, (user_id, current_hash, datetime.now().isoformat())
            )

            self.db.commit()

            # Invalidate all user sessions
            self.security.invalidate_user_sessions(user_id)

            logger.info(f"Password changed for user ID: {user_id}")
            return True, "Password changed successfully"

        except Exception as e:
            logger.error(f"Password change error: {e}")
            return False, f"Failed to change password: {str(e)}"

    def logout_user(self, session_id: str) -> bool:
        """Logout user and invalidate session"""
        try:
            success = self.security.invalidate_session(session_id)

            if success:
                # Clear Streamlit session state
                for key in list(st.session_state.keys()):
                    if key.startswith(("authenticated", "user", "session")):
                        del st.session_state[key]

                logger.info(f"User logged out: {session_id}")

            return success

        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information by ID"""
        try:
            query = """
                SELECT UserID, Username, Email, FirstName, LastName,
                       Role, Department, Phone, IsActive, CreatedDate, LastLoginDate
                FROM Users 
                WHERE UserID = ?
            """
            result = self.db.execute(query, (user_id,)).fetchone()

            if result:
                return dict(result)
            return None

        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None

    def update_user(
        self, user_id: int, update_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update user information"""
        try:
            # Build dynamic update query
            allowed_fields = [
                "Email",
                "FirstName",
                "LastName",
                "Role",
                "Department",
                "Phone",
                "IsActive",
            ]
            update_fields = []
            update_values = []

            for field, value in update_data.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)

            if not update_fields:
                return False, "No valid fields to update"

            # Validate role if being updated
            if "Role" in update_data:
                try:
                    UserRole(update_data["Role"])
                except ValueError:
                    return False, f"Invalid role: {update_data['Role']}"

            update_values.append(user_id)

            query = f"UPDATE Users SET {', '.join(update_fields)} WHERE UserID = ?"
            self.db.execute(query, update_values)
            self.db.commit()

            logger.info(f"User updated: {user_id}")
            return True, "User updated successfully"

        except Exception as e:
            logger.error(f"Update user error: {e}")
            return False, f"Failed to update user: {str(e)}"

    def delete_user(self, user_id: int, soft_delete: bool = True) -> Tuple[bool, str]:
        """Delete user (soft or hard delete)"""
        try:
            if soft_delete:
                query = (
                    "UPDATE Users SET IsActive = 0, DeletedDate = ? WHERE UserID = ?"
                )
                self.db.execute(query, (datetime.now().isoformat(), user_id))
            else:
                # Hard delete - remove from database
                query = "DELETE FROM Users WHERE UserID = ?"
                self.db.execute(query, (user_id,))

            # Invalidate all user sessions
            self.security.invalidate_user_sessions(user_id)

            self.db.commit()

            logger.info(
                f"User {'deactivated' if soft_delete else 'deleted'}: {user_id}"
            )
            return (
                True,
                f"User {'deactivated' if soft_delete else 'deleted'} successfully",
            )

        except Exception as e:
            logger.error(f"Delete user error: {e}")
            return False, f"Failed to delete user: {str(e)}"

    def generate_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Generate JWT token for API access"""
        try:
            payload = {
                "user_id": user_data["UserID"],
                "username": user_data["Username"],
                "role": user_data["Role"],
                "exp": datetime.utcnow() + self.jwt_expiry,
                "iat": datetime.utcnow(),
                "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            return token

        except Exception as e:
            logger.error(f"JWT generation error: {e}")
            return None

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            return None

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics for monitoring"""
        try:
            stats = {
                "active_sessions": len(self.security.active_sessions),
                "locked_accounts": len(self.security.locked_accounts),
                "failed_attempts_last_hour": 0,
                "successful_logins_last_hour": 0,
                "password_changes_last_day": 0,
                "security_events_last_day": 0,
            }

            if self.db:
                # Get recent statistics from database
                hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
                day_ago = (datetime.now() - timedelta(days=1)).isoformat()

                # Failed attempts last hour
                failed_query = """
                    SELECT COUNT(*) FROM login_attempts 
                    WHERE success = 0 AND timestamp > ?
                """
                result = self.db.execute(failed_query, (hour_ago,)).fetchone()
                stats["failed_attempts_last_hour"] = result[0] if result else 0

                # Successful logins last hour
                success_query = """
                    SELECT COUNT(*) FROM login_attempts 
                    WHERE success = 1 AND timestamp > ?
                """
                result = self.db.execute(success_query, (hour_ago,)).fetchone()
                stats["successful_logins_last_hour"] = result[0] if result else 0

                # Password changes last day
                password_query = """
                    SELECT COUNT(*) FROM password_history 
                    WHERE created_at > ?
                """
                result = self.db.execute(password_query, (day_ago,)).fetchone()
                stats["password_changes_last_day"] = result[0] if result else 0

                # Security events last day
                events_query = """
                    SELECT COUNT(*) FROM security_events 
                    WHERE timestamp > ?
                """
                result = self.db.execute(events_query, (day_ago,)).fetchone()
                stats["security_events_last_day"] = result[0] if result else 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get security stats: {e}")
            return {}


# Streamlit session management functions
def init_session_state():
    """Initialize Streamlit session state"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None


def require_authentication():
    """Decorator/function to require authentication"""
    if not st.session_state.get("authenticated", False):
        st.error("❌ กรุณาเข้าสู่ระบบ")
        st.stop()


def require_role(*allowed_roles):
    """Decorator to require specific roles"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            require_authentication()

            user = st.session_state.get("user", {})
            user_role = user.get("Role", "Guest")

            if user_role not in allowed_roles:
                st.error("❌ คุณไม่มีสิทธิ์ในการเข้าถึงหน้านี้")
                st.stop()

            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user"""
    if st.session_state.get("authenticated", False):
        return st.session_state.get("user")
    return None


def get_current_user_id() -> Optional[int]:
    """Get current user ID"""
    user = get_current_user()
    return user.get("UserID") if user else None


def get_current_user_role() -> str:
    """Get current user role"""
    user = get_current_user()
    return user.get("Role", "Guest") if user else "Guest"


def is_admin() -> bool:
    """Check if current user is admin"""
    return get_current_user_role() in ["Super Admin", "Admin"]


def is_project_manager() -> bool:
    """Check if current user is project manager or higher"""
    return get_current_user_role() in ["Super Admin", "Admin", "Project Manager"]


def is_team_lead() -> bool:
    """Check if current user is team lead or higher"""
    return get_current_user_role() in [
        "Super Admin",
        "Admin",
        "Project Manager",
        "Team Lead",
    ]


def has_permission(permission: Permission) -> bool:
    """Check if current user has specific permission"""
    user_role = get_current_user_role()
    permission_manager = PermissionManager()
    return permission_manager.user_has_permission(user_role, permission)


# Password utilities
def generate_secure_password(length: int = 16) -> str:
    """Generate secure password"""
    policy = PasswordPolicy()
    return policy.generate_password(length)


def validate_password_strength(
    password: str, username: str = None
) -> Tuple[bool, List[str]]:
    """Validate password strength"""
    policy = PasswordPolicy()
    return policy.validate_password(password, username)


# Security monitoring
def log_security_event(
    event_type: str,
    description: str,
    severity: str = "LOW",
    additional_data: Dict[str, Any] = None,
):
    """Log security event"""
    try:
        from utils.error_handler import global_error_handler

        user = get_current_user()
        user_id = user.get("UserID") if user else None

        # Get IP address (simplified)
        ip_address = st.session_state.get("client_ip", "127.0.0.1")

        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            description=description,
            severity=severity,
            timestamp=datetime.now(),
            additional_data=additional_data,
        )

        # If we have access to security manager, log it properly
        if hasattr(st.session_state, "auth_manager"):
            st.session_state.auth_manager.security.log_security_event(event)
        else:
            # Fallback to basic logging
            logger.warning(f"Security event: {event_type} - {description}")

    except Exception as e:
        logger.error(f"Failed to log security event: {e}")


# Session management utilities
def extend_session():
    """Extend current user session"""
    try:
        if hasattr(st.session_state, "auth_manager") and st.session_state.get(
            "session_id"
        ):
            ip_address = st.session_state.get("client_ip", "127.0.0.1")
            st.session_state.auth_manager.security.validate_session(
                st.session_state.session_id, ip_address
            )
    except Exception as e:
        logger.error(f"Failed to extend session: {e}")


def cleanup_expired_sessions():
    """Clean up expired sessions"""
    try:
        if hasattr(st.session_state, "auth_manager"):
            cleaned = st.session_state.auth_manager.security.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {e}")


# IP and security utilities
def get_client_ip() -> str:
    """Get client IP address"""
    try:
        # In Streamlit, getting real IP is tricky
        # This is a simplified version
        return st.session_state.get("client_ip", "127.0.0.1")
    except Exception:
        return "127.0.0.1"


def is_ip_whitelisted(ip_address: str, whitelist: List[str]) -> bool:
    """Check if IP is in whitelist"""
    try:
        for allowed_ip in whitelist:
            if "/" in allowed_ip:  # CIDR notation
                if ipaddress.ip_address(ip_address) in ipaddress.ip_network(allowed_ip):
                    return True
            else:  # Single IP
                if ip_address == allowed_ip:
                    return True
        return False
    except Exception:
        return False


# Rate limiting utilities
class RateLimiter:
    """Simple rate limiter for login attempts"""

    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window = timedelta(minutes=window_minutes)
        self.attempts = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        with self._lock:
            now = datetime.now()

            # Clean old attempts
            cutoff = now - self.window
            self.attempts[identifier] = [
                attempt for attempt in self.attempts[identifier] if attempt > cutoff
            ]

            # Check if under limit
            if len(self.attempts[identifier]) >= self.max_attempts:
                return False

            # Record this attempt
            self.attempts[identifier].append(now)
            return True

    def reset(self, identifier: str) -> None:
        """Reset attempts for identifier"""
        with self._lock:
            if identifier in self.attempts:
                del self.attempts[identifier]


# Global rate limiter instance
login_rate_limiter = RateLimiter()


# Export all major classes and functions
__all__ = [
    "UserRole",
    "Permission",
    "LoginAttempt",
    "SecurityEvent",
    "UserSession",
    "PasswordPolicy",
    "SecurityManager",
    "PermissionManager",
    "AuthenticationManager",
    "init_session_state",
    "require_authentication",
    "require_role",
    "get_current_user",
    "get_current_user_id",
    "get_current_user_role",
    "is_admin",
    "is_project_manager",
    "is_team_lead",
    "has_permission",
    "generate_secure_password",
    "validate_password_strength",
    "log_security_event",
    "extend_session",
    "cleanup_expired_sessions",
    "get_client_ip",
    "is_ip_whitelisted",
    "RateLimiter",
    "login_rate_limiter",
]
