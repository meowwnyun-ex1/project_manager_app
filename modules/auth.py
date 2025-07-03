"""
modules/auth.py
Authentication and authorization management
"""

import bcrypt
import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
import secrets
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles enumeration"""

    ADMIN = "Admin"
    PROJECT_MANAGER = "Project Manager"
    TEAM_LEAD = "Team Lead"
    DEVELOPER = "Developer"
    USER = "User"
    VIEWER = "Viewer"


class Permission(Enum):
    """Permission enumeration"""

    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"

    # Project management
    CREATE_PROJECT = "create_project"
    READ_PROJECT = "read_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"

    # Task management
    CREATE_TASK = "create_task"
    READ_TASK = "read_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"

    # System administration
    MANAGE_SETTINGS = "manage_settings"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_DATABASE = "manage_database"
    VIEW_AUDIT_LOG = "view_audit_log"


@dataclass
class LoginAttempt:
    """Login attempt tracking"""

    username: str
    ip_address: str
    timestamp: datetime
    success: bool
    user_agent: str = ""


class SecurityManager:
    """Security and password management"""

    def __init__(self):
        self.password_requirements = {
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special": True,
            "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
        }

        self.login_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt(rounds=12)
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

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {"valid": True, "errors": [], "score": 0, "suggestions": []}

        # Length check
        if len(password) < self.password_requirements["min_length"]:
            result["valid"] = False
            result["errors"].append(
                f"รหัสผ่านต้องมีอย่างน้อย {self.password_requirements['min_length']} ตัวอักษร"
            )
        else:
            result["score"] += 20

        # Uppercase check
        if self.password_requirements["require_uppercase"] and not re.search(
            r"[A-Z]", password
        ):
            result["valid"] = False
            result["errors"].append("รหัสผ่านต้องมีตัวอักษรพิมพ์ใหญ่อย่างน้อย 1 ตัว")
        else:
            result["score"] += 20

        # Lowercase check
        if self.password_requirements["require_lowercase"] and not re.search(
            r"[a-z]", password
        ):
            result["valid"] = False
            result["errors"].append("รหัสผ่านต้องมีตัวอักษรพิมพ์เล็กอย่างน้อย 1 ตัว")
        else:
            result["score"] += 20

        # Numbers check
        if self.password_requirements["require_numbers"] and not re.search(
            r"\d", password
        ):
            result["valid"] = False
            result["errors"].append("รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")
        else:
            result["score"] += 20

        # Special characters check
        if self.password_requirements["require_special"]:
            special_chars = self.password_requirements["special_chars"]
            if not re.search(f"[{re.escape(special_chars)}]", password):
                result["valid"] = False
                result["errors"].append("รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว")
            else:
                result["score"] += 20

        # Additional strength checks
        if len(password) > 12:
            result["score"] += 10

        if len(set(password)) > len(password) * 0.7:  # Character diversity
            result["score"] += 10

        # Common patterns check
        common_patterns = ["123", "abc", "password", "admin", "qwerty"]
        for pattern in common_patterns:
            if pattern.lower() in password.lower():
                result["score"] -= 10
                result["suggestions"].append(f"หลีกเลี่ยงการใช้คำที่เดาได้ง่าย เช่น '{pattern}'")

        return result

    def track_login_attempt(
        self, username: str, success: bool, ip_address: str = "", user_agent: str = ""
    ):
        """Track login attempts for security monitoring"""
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            timestamp=datetime.now(),
            success=success,
            user_agent=user_agent,
        )

        if username not in self.login_attempts:
            self.login_attempts[username] = []

        self.login_attempts[username].append(attempt)

        # Keep only recent attempts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.login_attempts[username] = [
            a for a in self.login_attempts[username] if a.timestamp > cutoff_time
        ]

    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed login attempts"""
        if username not in self.login_attempts:
            return False

        recent_attempts = [
            a
            for a in self.login_attempts[username]
            if a.timestamp > datetime.now() - self.lockout_duration
        ]

        failed_attempts = [a for a in recent_attempts if not a.success]

        return len(failed_attempts) >= self.max_attempts

    def get_lockout_time_remaining(self, username: str) -> Optional[timedelta]:
        """Get remaining lockout time"""
        if not self.is_account_locked(username):
            return None

        recent_failed = [
            a
            for a in self.login_attempts[username]
            if not a.success and a.timestamp > datetime.now() - self.lockout_duration
        ]

        if recent_failed:
            last_attempt = max(recent_failed, key=lambda x: x.timestamp)
            unlock_time = last_attempt.timestamp + self.lockout_duration
            remaining = unlock_time - datetime.now()
            return remaining if remaining.total_seconds() > 0 else None

        return None

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)


class PermissionManager:
    """Permission and role management"""

    def __init__(self):
        # Define role permissions
        self.role_permissions = {
            UserRole.ADMIN: [p for p in Permission],  # All permissions
            UserRole.PROJECT_MANAGER: [
                Permission.CREATE_USER,
                Permission.READ_USER,
                Permission.UPDATE_USER,
                Permission.CREATE_PROJECT,
                Permission.READ_PROJECT,
                Permission.UPDATE_PROJECT,
                Permission.DELETE_PROJECT,
                Permission.CREATE_TASK,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.DELETE_TASK,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_AUDIT_LOG,
            ],
            UserRole.TEAM_LEAD: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.UPDATE_PROJECT,
                Permission.CREATE_TASK,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
                Permission.DELETE_TASK,
                Permission.VIEW_ANALYTICS,
            ],
            UserRole.DEVELOPER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
            ],
            UserRole.USER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
                Permission.UPDATE_TASK,
            ],
            UserRole.VIEWER: [
                Permission.READ_USER,
                Permission.READ_PROJECT,
                Permission.READ_TASK,
            ],
        }

    def get_user_permissions(self, role: str) -> List[Permission]:
        """Get permissions for a user role"""
        try:
            user_role = UserRole(role)
            return self.role_permissions.get(user_role, [])
        except ValueError:
            logger.warning(f"Unknown user role: {role}")
            return []

    def user_has_permission(self, user_role: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user_role)
        return permission in user_permissions

    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""

        def decorator(func):
            def wrapper(*args, **kwargs):
                if not st.session_state.get("authenticated", False):
                    st.error("❌ กรุณาเข้าสู่ระบบ")
                    return None

                user_role = st.session_state.get("user", {}).get("Role", "User")

                if not self.user_has_permission(user_role, permission):
                    st.error("❌ คุณไม่มีสิทธิ์ในการดำเนินการนี้")
                    return None

                return func(*args, **kwargs)

            return wrapper

        return decorator


class AuthManager:
    """Main authentication manager"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.security_manager = SecurityManager()
        self.permission_manager = PermissionManager()

    def authenticate_user(
        self, username: str, password: str, ip_address: str = "", user_agent: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with enhanced security"""
        try:
            # Check if account is locked
            if self.security_manager.is_account_locked(username):
                remaining = self.security_manager.get_lockout_time_remaining(username)
                if remaining:
                    minutes = int(remaining.total_seconds() / 60)
                    logger.warning(f"Login attempt on locked account: {username}")
                    st.error(f"⚠️ บัญชีถูกล็อก กรุณารอ {minutes} นาที")
                    return None

            # Get user from database
            query = """
            SELECT UserID, Username, PasswordHash, Email, FirstName, LastName, 
                   Role, Department, Phone, IsActive, LastLoginDate
            FROM Users 
            WHERE Username = ? AND IsActive = 1
            """

            users = self.db_manager.execute_query(query, (username,))

            if not users:
                # Track failed attempt
                self.security_manager.track_login_attempt(
                    username, False, ip_address, user_agent
                )
                logger.warning(f"Login attempt with non-existent username: {username}")
                return None

            user = users[0]

            # Verify password
            if not self.security_manager.verify_password(
                password, user["PasswordHash"]
            ):
                # Track failed attempt
                self.security_manager.track_login_attempt(
                    username, False, ip_address, user_agent
                )
                logger.warning(f"Failed login attempt for user: {username}")
                return None

            # Track successful attempt
            self.security_manager.track_login_attempt(
                username, True, ip_address, user_agent
            )

            # Update last login
            self.update_user_last_login(user["UserID"], ip_address)

            # Remove password hash from returned user data
            user.pop("PasswordHash", None)

            logger.info(f"Successful login: {username}")
            return user

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create new user with validation"""
        try:
            # Validate required fields
            required_fields = [
                "username",
                "password",
                "email",
                "first_name",
                "last_name",
            ]
            for field in required_fields:
                if not user_data.get(field):
                    logger.error(f"Missing required field: {field}")
                    return False

            # Validate password strength
            password_validation = self.security_manager.validate_password_strength(
                user_data["password"]
            )
            if not password_validation["valid"]:
                logger.error(
                    f"Password validation failed: {password_validation['errors']}"
                )
                return False

            # Check if username or email already exists
            existing_user = self.db_manager.execute_query(
                "SELECT UserID FROM Users WHERE Username = ? OR Email = ?",
                (user_data["username"], user_data["email"]),
            )

            if existing_user:
                logger.error(
                    f"User already exists: {user_data['username']} or {user_data['email']}"
                )
                return False

            # Hash password
            password_hash = self.security_manager.hash_password(user_data["password"])

            # Insert user
            query = """
            INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, 
                              Role, Department, Phone, CreatedDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """

            params = (
                user_data["username"],
                password_hash,
                user_data["email"],
                user_data["first_name"],
                user_data["last_name"],
                user_data.get("role", "User"),
                user_data.get("department", ""),
                user_data.get("phone", ""),
            )

            result = self.db_manager.execute_non_query(query, params)

            if result:
                logger.info(f"User created successfully: {user_data['username']}")

            return result

        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return False

    def update_user_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """Update user password with validation"""
        try:
            # Get current user
            user = self.db_manager.execute_query(
                "SELECT PasswordHash FROM Users WHERE UserID = ?", (user_id,)
            )

            if not user:
                return False

            # Verify current password
            if not self.security_manager.verify_password(
                current_password, user[0]["PasswordHash"]
            ):
                logger.warning(f"Invalid current password for user ID: {user_id}")
                return False

            # Validate new password
            password_validation = self.security_manager.validate_password_strength(
                new_password
            )
            if not password_validation["valid"]:
                logger.error(
                    f"New password validation failed: {password_validation['errors']}"
                )
                return False

            # Hash new password
            new_password_hash = self.security_manager.hash_password(new_password)

            # Update password
            result = self.db_manager.execute_non_query(
                "UPDATE Users SET PasswordHash = ?, LastModifiedDate = GETDATE() WHERE UserID = ?",
                (new_password_hash, user_id),
            )

            if result:
                logger.info(f"Password updated for user ID: {user_id}")

            return result

        except Exception as e:
            logger.error(f"Password update failed: {str(e)}")
            return False

    def update_user_last_login(self, user_id: int, ip_address: str = ""):
        """Update user's last login timestamp"""
        try:
            self.db_manager.execute_non_query(
                "UPDATE Users SET LastLoginDate = GETDATE() WHERE UserID = ?",
                (user_id,),
            )

            # Log login activity (could be stored in audit table)
            logger.info(f"User login recorded: ID={user_id}, IP={ip_address}")

        except Exception as e:
            logger.error(f"Failed to update last login: {str(e)}")

    def reset_password(self, username: str, new_password: str) -> bool:
        """Reset user password (admin function)"""
        try:
            # Validate new password
            password_validation = self.security_manager.validate_password_strength(
                new_password
            )
            if not password_validation["valid"]:
                return False

            # Hash new password
            password_hash = self.security_manager.hash_password(new_password)

            # Update password
            result = self.db_manager.execute_non_query(
                "UPDATE Users SET PasswordHash = ?, LastModifiedDate = GETDATE() WHERE Username = ?",
                (password_hash, username),
            )

            if result:
                logger.info(f"Password reset for user: {username}")

            return result

        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            return False

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        try:
            result = self.db_manager.execute_non_query(
                "UPDATE Users SET IsActive = 0, LastModifiedDate = GETDATE() WHERE UserID = ?",
                (user_id,),
            )

            if result:
                logger.info(f"User deactivated: ID={user_id}")

            return result

        except Exception as e:
            logger.error(f"User deactivation failed: {str(e)}")
            return False

    def activate_user(self, user_id: int) -> bool:
        """Activate user account"""
        try:
            result = self.db_manager.execute_non_query(
                "UPDATE Users SET IsActive = 1, LastModifiedDate = GETDATE() WHERE UserID = ?",
                (user_id,),
            )

            if result:
                logger.info(f"User activated: ID={user_id}")

            return result

        except Exception as e:
            logger.error(f"User activation failed: {str(e)}")
            return False

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (excluding password hashes)"""
        query = """
        SELECT UserID, Username, Email, FirstName, LastName, Role, 
               Department, Phone, IsActive, CreatedDate, LastLoginDate
        FROM Users 
        ORDER BY FirstName, LastName
        """

        try:
            return self.db_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = """
        SELECT UserID, Username, Email, FirstName, LastName, Role, 
               Department, Phone, IsActive, CreatedDate, LastLoginDate
        FROM Users 
        WHERE UserID = ?
        """

        try:
            users = self.db_manager.execute_query(query, (user_id,))
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {str(e)}")
            return None

    def get_login_attempts(
        self, username: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get login attempts for monitoring"""
        attempts = []

        if username:
            user_attempts = self.security_manager.login_attempts.get(username, [])
        else:
            user_attempts = []
            for user_attempts_list in self.security_manager.login_attempts.values():
                user_attempts.extend(user_attempts_list)

        # Sort by timestamp (newest first)
        user_attempts.sort(key=lambda x: x.timestamp, reverse=True)

        # Convert to dict format and limit results
        for attempt in user_attempts[:limit]:
            attempts.append(
                {
                    "username": attempt.username,
                    "ip_address": attempt.ip_address,
                    "timestamp": attempt.timestamp,
                    "success": attempt.success,
                    "user_agent": attempt.user_agent,
                }
            )

        return attempts

    def check_session_validity(self) -> bool:
        """Check if current session is valid"""
        if not st.session_state.get("authenticated", False):
            return False

        # Check session timeout
        last_activity = st.session_state.get("last_activity")
        if last_activity:
            timeout_minutes = 60  # 1 hour
            if datetime.now() - last_activity > timedelta(minutes=timeout_minutes):
                return False

        return True

    def has_permission(self, permission: Permission) -> bool:
        """Check if current user has permission"""
        if not st.session_state.get("authenticated", False):
            return False

        user_role = st.session_state.get("user", {}).get("Role", "User")
        return self.permission_manager.user_has_permission(user_role, permission)

    def require_permission(self, permission: Permission):
        """Decorator to require permission"""
        return self.permission_manager.require_permission(permission)

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        stats = {
            "total_users": 0,
            "active_users": 0,
            "locked_accounts": 0,
            "failed_logins_24h": 0,
            "successful_logins_24h": 0,
            "recent_login_attempts": [],
        }

        try:
            # Get user counts from database
            total_users = self.db_manager.execute_scalar("SELECT COUNT(*) FROM Users")
            active_users = self.db_manager.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE IsActive = 1"
            )

            stats["total_users"] = total_users or 0
            stats["active_users"] = active_users or 0

            # Count locked accounts
            locked_count = 0
            for username in self.security_manager.login_attempts:
                if self.security_manager.is_account_locked(username):
                    locked_count += 1
            stats["locked_accounts"] = locked_count

            # Count login attempts in last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            failed_count = 0
            success_count = 0

            for username, attempts in self.security_manager.login_attempts.items():
                for attempt in attempts:
                    if attempt.timestamp > cutoff_time:
                        if attempt.success:
                            success_count += 1
                        else:
                            failed_count += 1

            stats["failed_logins_24h"] = failed_count
            stats["successful_logins_24h"] = success_count

            # Get recent attempts
            stats["recent_login_attempts"] = self.get_login_attempts(limit=10)

        except Exception as e:
            logger.error(f"Failed to get security stats: {str(e)}")

        return stats


# Helper functions for common authentication checks
def require_auth():
    """Decorator to require authentication"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get("authenticated", False):
                st.error("❌ กรุณาเข้าสู่ระบบ")
                st.stop()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*allowed_roles):
    """Decorator to require specific roles"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get("authenticated", False):
                st.error("❌ กรุณาเข้าสู่ระบบ")
                st.stop()

            user_role = st.session_state.get("user", {}).get("Role", "User")
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


def is_admin() -> bool:
    """Check if current user is admin"""
    user = get_current_user()
    return user and user.get("Role") == "Admin"


def is_project_manager() -> bool:
    """Check if current user is project manager or admin"""
    user = get_current_user()
    return user and user.get("Role") in ["Admin", "Project Manager"]
