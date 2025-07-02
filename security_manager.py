# security_manager.py
"""
Enhanced Security and Authentication Manager for DENSO Project Manager
Comprehensive security features including authentication, authorization, and protection
"""

import streamlit as st
import bcrypt
import secrets
import hashlib
import hmac
import time
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User role definitions"""

    VIEWER = "Viewer"
    USER = "User"
    MANAGER = "Manager"
    ADMIN = "Admin"
    SYSTEM = "System"


class Permission(Enum):
    """Permission definitions"""

    READ_PROJECTS = "read_projects"
    CREATE_PROJECTS = "create_projects"
    UPDATE_PROJECTS = "update_projects"
    DELETE_PROJECTS = "delete_projects"

    READ_TASKS = "read_tasks"
    CREATE_TASKS = "create_tasks"
    UPDATE_TASKS = "update_tasks"
    DELETE_TASKS = "delete_tasks"

    READ_USERS = "read_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"

    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    MANAGE_SETTINGS = "manage_settings"
    SYSTEM_ADMIN = "system_admin"


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_expiry_days: int = 90

    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    session_timeout_minutes: int = 60

    enable_2fa: bool = False
    enable_password_history: int = 5
    force_password_change: bool = False


@dataclass
class SessionInfo:
    """User session information"""

    session_id: str
    user_id: int
    username: str
    role: UserRole
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    permissions: List[Permission]
    csrf_token: str
    is_authenticated: bool = True
    is_2fa_verified: bool = False


class PermissionManager:
    """Manages user permissions and role-based access control"""

    def __init__(self):
        self.role_permissions = {
            UserRole.VIEWER: [
                Permission.READ_PROJECTS,
                Permission.READ_TASKS,
                Permission.VIEW_ANALYTICS,
            ],
            UserRole.USER: [
                Permission.READ_PROJECTS,
                Permission.CREATE_PROJECTS,
                Permission.UPDATE_PROJECTS,
                Permission.READ_TASKS,
                Permission.CREATE_TASKS,
                Permission.UPDATE_TASKS,
                Permission.VIEW_ANALYTICS,
            ],
            UserRole.MANAGER: [
                Permission.READ_PROJECTS,
                Permission.CREATE_PROJECTS,
                Permission.UPDATE_PROJECTS,
                Permission.DELETE_PROJECTS,
                Permission.READ_TASKS,
                Permission.CREATE_TASKS,
                Permission.UPDATE_TASKS,
                Permission.DELETE_TASKS,
                Permission.READ_USERS,
                Permission.UPDATE_USERS,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
            ],
            UserRole.ADMIN: [perm for perm in Permission],
            UserRole.SYSTEM: [perm for perm in Permission],
        }

    def get_role_permissions(self, role: UserRole) -> List[Permission]:
        """Get permissions for a role"""
        return self.role_permissions.get(role, [])

    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        role_perms = self.get_role_permissions(user_role)
        return permission in role_perms

    def check_permission(self, session: SessionInfo, permission: Permission) -> bool:
        """Check if current session has permission"""
        if not session or not session.is_authenticated:
            return False

        return permission in session.permissions


class PasswordManager:
    """Advanced password management"""

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt(
                rounds=(
                    self.policy.bcrypt_rounds
                    if hasattr(self.policy, "bcrypt_rounds")
                    else 12
                )
            )
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against security policy"""
        errors = []

        if len(password) < self.policy.password_min_length:
            errors.append(
                f"Password must be at least {self.policy.password_min_length} characters long"
            )

        if self.policy.password_require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if self.policy.password_require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if self.policy.password_require_numbers and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")

        if self.policy.password_require_special and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("Password must contain at least one special character")

        # Check for common patterns
        if self._is_common_password(password):
            errors.append("Password is too common or predictable")

        return len(errors) == 0, errors

    def _is_common_password(self, password: str) -> bool:
        """Check if password is commonly used"""
        common_passwords = [
            "password",
            "123456",
            "password123",
            "admin",
            "user",
            "qwerty",
            "abc123",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
            "master",
            "shadow",
            "login",
            "princess",
        ]

        return password.lower() in common_passwords

    def generate_secure_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        import string

        if length < 8:
            length = 8

        # Ensure we have at least one of each required character type
        password = []

        if self.policy.password_require_uppercase:
            password.append(secrets.choice(string.ascii_uppercase))

        if self.policy.password_require_lowercase:
            password.append(secrets.choice(string.ascii_lowercase))

        if self.policy.password_require_numbers:
            password.append(secrets.choice(string.digits))

        if self.policy.password_require_special:
            password.append(secrets.choice('!@#$%^&*(),.?":{}|<>'))

        # Fill the rest with random characters
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*(),.?":{}|<>'
        for _ in range(length - len(password)):
            password.append(secrets.choice(all_chars))

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)

        return "".join(password)


class SessionManager:
    """Manages user sessions and authentication"""

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.active_sessions = {}
        self.failed_login_attempts = {}
        self.locked_accounts = {}
        self.permission_manager = PermissionManager()

    def create_session(
        self, user: Dict[str, Any], ip_address: str = "", user_agent: str = ""
    ) -> SessionInfo:
        """Create new user session"""
        try:
            session_id = self._generate_session_id()
            csrf_token = self._generate_csrf_token()

            user_role = UserRole(user.get("Role", "User"))
            permissions = self.permission_manager.get_role_permissions(user_role)

            session = SessionInfo(
                session_id=session_id,
                user_id=user["UserID"],
                username=user["Username"],
                role=user_role,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                ip_address=ip_address,
                user_agent=user_agent,
                permissions=permissions,
                csrf_token=csrf_token,
            )

            # Store session
            self.active_sessions[session_id] = session

            # Update session state
            st.session_state.session_info = session
            st.session_state.session_id = session_id

            logger.info(
                f"Session created for user {user['Username']} (ID: {session_id})"
            )
            return session

        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise

    def validate_session(self, session_id: str) -> Optional[SessionInfo]:
        """Validate and refresh session"""
        try:
            if session_id not in self.active_sessions:
                return None

            session = self.active_sessions[session_id]

            # Check session timeout
            if self._is_session_expired(session):
                self.destroy_session(session_id)
                return None

            # Update last activity
            session.last_activity = datetime.now()

            return session

        except Exception as e:
            logger.error(f"Session validation failed: {str(e)}")
            return None

    def destroy_session(self, session_id: str):
        """Destroy user session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                del self.active_sessions[session_id]

                logger.info(
                    f"Session destroyed for user {session.username} (ID: {session_id})"
                )

            # Clear session state
            if "session_info" in st.session_state:
                del st.session_state.session_info
            if "session_id" in st.session_state:
                del st.session_state.session_id

        except Exception as e:
            logger.error(f"Failed to destroy session: {str(e)}")

    def check_login_attempts(self, username: str, ip_address: str) -> bool:
        """Check if login attempts are within limits"""
        try:
            key = f"{username}_{ip_address}"
            current_time = datetime.now()

            # Clean old attempts
            self._clean_old_attempts()

            # Check if account is locked
            if username in self.locked_accounts:
                if current_time < self.locked_accounts[username]:
                    return False  # Account still locked
                else:
                    del self.locked_accounts[username]  # Unlock account

            # Check failed attempts
            if key in self.failed_login_attempts:
                attempts = self.failed_login_attempts[key]
                recent_attempts = [
                    attempt
                    for attempt in attempts
                    if (current_time - attempt).total_seconds() < 900  # 15 minutes
                ]

                if len(recent_attempts) >= self.policy.max_login_attempts:
                    # Lock account
                    lockout_until = current_time + timedelta(
                        minutes=self.policy.lockout_duration_minutes
                    )
                    self.locked_accounts[username] = lockout_until

                    logger.warning(
                        f"Account {username} locked due to failed login attempts"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking login attempts: {str(e)}")
            return True  # Allow on error

    def record_failed_login(self, username: str, ip_address: str):
        """Record failed login attempt"""
        try:
            key = f"{username}_{ip_address}"

            if key not in self.failed_login_attempts:
                self.failed_login_attempts[key] = []

            self.failed_login_attempts[key].append(datetime.now())

            logger.warning(f"Failed login attempt for {username} from {ip_address}")

        except Exception as e:
            logger.error(f"Error recording failed login: {str(e)}")

    def clear_failed_attempts(self, username: str):
        """Clear failed login attempts for user"""
        try:
            keys_to_remove = [
                key
                for key in self.failed_login_attempts.keys()
                if key.startswith(f"{username}_")
            ]
            for key in keys_to_remove:
                del self.failed_login_attempts[key]

        except Exception as e:
            logger.error(f"Error clearing failed attempts: {str(e)}")

    def get_active_sessions(self) -> List[SessionInfo]:
        """Get all active sessions"""
        return list(self.active_sessions.values())

    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)

    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(24)

    def _is_session_expired(self, session: SessionInfo) -> bool:
        """Check if session is expired"""
        timeout = timedelta(minutes=self.policy.session_timeout_minutes)
        return datetime.now() - session.last_activity > timeout

    def _clean_old_attempts(self):
        """Clean old failed login attempts"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=1)

            for key in list(self.failed_login_attempts.keys()):
                self.failed_login_attempts[key] = [
                    attempt
                    for attempt in self.failed_login_attempts[key]
                    if attempt > cutoff_time
                ]
                if not self.failed_login_attempts[key]:
                    del self.failed_login_attempts[key]

        except Exception as e:
            logger.error(f"Error cleaning old attempts: {str(e)}")


class DataEncryption:
    """Data encryption and decryption utilities"""

    def __init__(self, key: Optional[bytes] = None):
        if key:
            self.key = key
        else:
            self.key = self._generate_key()

        self.cipher = Fernet(self.key)

    def _generate_key(self) -> bytes:
        """Generate encryption key"""
        return Fernet.generate_key()

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt_data(self, data: str) -> str:
        """Encrypt data"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded_data)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise

    def encrypt_sensitive_fields(
        self, data: Dict[str, Any], fields: List[str]
    ) -> Dict[str, Any]:
        """Encrypt sensitive fields in dictionary"""
        try:
            encrypted_data = data.copy()

            for field in fields:
                if field in encrypted_data and encrypted_data[field]:
                    encrypted_data[field] = self.encrypt_data(
                        str(encrypted_data[field])
                    )

            return encrypted_data

        except Exception as e:
            logger.error(f"Field encryption failed: {str(e)}")
            return data

    def decrypt_sensitive_fields(
        self, data: Dict[str, Any], fields: List[str]
    ) -> Dict[str, Any]:
        """Decrypt sensitive fields in dictionary"""
        try:
            decrypted_data = data.copy()

            for field in fields:
                if field in decrypted_data and decrypted_data[field]:
                    decrypted_data[field] = self.decrypt_data(decrypted_data[field])

            return decrypted_data

        except Exception as e:
            logger.error(f"Field decryption failed: {str(e)}")
            return data


class SecurityManager:
    """Main security manager class"""

    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()
        self.password_manager = PasswordManager(self.policy)
        self.session_manager = SessionManager(self.policy)
        self.permission_manager = PermissionManager()
        self.data_encryption = DataEncryption()
        self._initialize_security()

    def _initialize_security(self):
        """Initialize security components"""
        try:
            # Set up security headers (would be done at server level in production)
            logger.info("Security manager initialized")
        except Exception as e:
            logger.error(f"Security initialization failed: {str(e)}")

    def authenticate_user(
        self, username: str, password: str, ip_address: str = "", user_agent: str = ""
    ) -> Tuple[bool, Optional[SessionInfo], str]:
        """Authenticate user and create session"""
        try:
            # Check login attempts
            if not self.session_manager.check_login_attempts(username, ip_address):
                return (
                    False,
                    None,
                    "Account temporarily locked due to too many failed attempts",
                )

            # Validate credentials (this would interface with your database)
            user = self._validate_credentials(username, password)

            if not user:
                self.session_manager.record_failed_login(username, ip_address)
                return False, None, "Invalid username or password"

            # Check if account is active
            if not user.get("IsActive", True):
                return False, None, "Account is disabled"

            # Clear failed attempts on successful login
            self.session_manager.clear_failed_attempts(username)

            # Create session
            session = self.session_manager.create_session(user, ip_address, user_agent)

            logger.info(f"User {username} authenticated successfully")
            return True, session, "Authentication successful"

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False, None, "Authentication error occurred"

    def _validate_credentials(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Validate user credentials against database"""
        # This would interface with your database service
        # For now, return None to indicate invalid credentials
        return None

    def logout_user(self, session_id: str):
        """Logout user and destroy session"""
        try:
            self.session_manager.destroy_session(session_id)
            logger.info("User logged out successfully")
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")

    def check_permission(self, permission: Permission) -> bool:
        """Check if current user has permission"""
        try:
            session = st.session_state.get("session_info")
            if not session:
                return False

            return self.permission_manager.check_permission(session, permission)

        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            return False

    def require_permission(self, permission: Permission) -> bool:
        """Require permission or show error"""
        if not self.check_permission(permission):
            st.error("🔒 You don't have permission to perform this action")
            return False
        return True

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        try:
            session = st.session_state.get("session_info")
            if session and session.is_authenticated:
                return {
                    "user_id": session.user_id,
                    "username": session.username,
                    "role": session.role.value,
                    "permissions": [perm.value for perm in session.permissions],
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get current user: {str(e)}")
            return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        try:
            session = st.session_state.get("session_info")
            if not session:
                return False

            # Validate session
            validated_session = self.session_manager.validate_session(
                session.session_id
            )
            return validated_session is not None

        except Exception as e:
            logger.error(f"Authentication check failed: {str(e)}")
            return False

    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> Tuple[bool, str]:
        """Change user password"""
        try:
            # Validate old password
            if not self._validate_credentials(username, old_password):
                return False, "Current password is incorrect"

            # Validate new password strength
            is_valid, errors = self.password_manager.validate_password_strength(
                new_password
            )
            if not is_valid:
                return False, "; ".join(errors)

            # Hash new password
            new_hash = self.password_manager.hash_password(new_password)

            # Update password in database (placeholder)
            # self._update_password_in_db(username, new_hash)

            logger.info(f"Password changed for user {username}")
            return True, "Password changed successfully"

        except Exception as e:
            logger.error(f"Password change failed: {str(e)}")
            return False, "Password change failed"

    def generate_password_reset_token(self, username: str) -> Optional[str]:
        """Generate password reset token"""
        try:
            # Create token with expiration
            payload = {
                "username": username,
                "exp": datetime.utcnow() + timedelta(hours=1),
                "type": "password_reset",
            }

            # Use a secret key for JWT (should be from config)
            secret_key = "your-secret-key"  # Get from config
            token = jwt.encode(payload, secret_key, algorithm="HS256")

            logger.info(f"Password reset token generated for {username}")
            return token

        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            return None

    def validate_password_reset_token(self, token: str) -> Optional[str]:
        """Validate password reset token"""
        try:
            secret_key = "your-secret-key"  # Get from config
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])

            if payload.get("type") != "password_reset":
                return None

            return payload.get("username")

        except jwt.ExpiredSignatureError:
            logger.warning("Password reset token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid password reset token")
            return None
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None

    def get_security_audit_log(self) -> List[Dict[str, Any]]:
        """Get security audit log"""
        try:
            audit_events = []

            # Active sessions
            for session in self.session_manager.get_active_sessions():
                audit_events.append(
                    {
                        "event_type": "active_session",
                        "username": session.username,
                        "role": session.role.value,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "ip_address": session.ip_address,
                    }
                )

            # Failed login attempts
            for key, attempts in self.session_manager.failed_login_attempts.items():
                username, ip = key.split("_", 1)
                audit_events.append(
                    {
                        "event_type": "failed_login_attempts",
                        "username": username,
                        "ip_address": ip,
                        "attempt_count": len(attempts),
                        "last_attempt": attempts[-1].isoformat() if attempts else None,
                    }
                )

            # Locked accounts
            for username, locked_until in self.session_manager.locked_accounts.items():
                audit_events.append(
                    {
                        "event_type": "locked_account",
                        "username": username,
                        "locked_until": locked_until.isoformat(),
                    }
                )

            return audit_events

        except Exception as e:
            logger.error(f"Failed to get security audit log: {str(e)}")
            return []

    def cleanup_expired_sessions(self):
        """Cleanup expired sessions"""
        try:
            current_time = datetime.now()
            expired_sessions = []

            for session_id, session in self.session_manager.active_sessions.items():
                if self.session_manager._is_session_expired(session):
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                self.session_manager.destroy_session(session_id)

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        except Exception as e:
            logger.error(f"Session cleanup failed: {str(e)}")


# Decorators for permission checking
def require_auth(func):
    """Decorator to require authentication"""

    def wrapper(*args, **kwargs):
        if not security_manager.is_authenticated():
            st.error("🔒 Authentication required")
            return None
        return func(*args, **kwargs)

    return wrapper


def require_permission(permission: Permission):
    """Decorator to require specific permission"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not security_manager.check_permission(permission):
                st.error(f"🔒 Permission required: {permission.value}")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: UserRole):
    """Decorator to require specific role"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            session = st.session_state.get("session_info")
            if not session or session.role != role:
                st.error(f"🔒 Role required: {role.value}")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Global security manager instance
security_manager = SecurityManager()


# Export functions
def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    return security_manager


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user"""
    return security_manager.get_current_user()


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return security_manager.is_authenticated()


def check_permission(permission: Permission) -> bool:
    """Check if current user has permission"""
    return security_manager.check_permission(permission)
