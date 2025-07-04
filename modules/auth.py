#!/usr/bin/env python3
"""
modules/auth.py
Authentication and Authorization for DENSO Project Manager Pro
"""
import bcrypt
import logging
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import secrets
import jwt

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Enterprise authentication manager"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.password_min_length = 8

    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials"""
        try:
            # Get user data
            user_query = """
                SELECT UserID, Username, PasswordHash, Email, FirstName, LastName, 
                       Role, Department, IsActive, IsLocked, FailedLoginAttempts,
                       LastFailedLogin, MustChangePassword
                FROM Users 
                WHERE Username = ? AND IsActive = 1
            """

            users = self.db.execute_query(user_query, (username,))

            if not users:
                return {"success": False, "message": "ไม่พบชื่อผู้ใช้"}

            user = users[0]

            # Check if account is locked
            if user["IsLocked"]:
                if self._check_lockout_expired(user["LastFailedLogin"]):
                    self._unlock_user(user["UserID"])
                else:
                    return {"success": False, "message": "บัญชีถูกล็อค กรุณาลองใหม่ภายหลัง"}

            # Verify password
            if self._verify_password(password, user["PasswordHash"]):
                # Reset failed attempts
                self._reset_failed_attempts(user["UserID"])

                # Update last login
                self._update_last_login(user["UserID"])

                # Check if password change required
                if user["MustChangePassword"]:
                    return {
                        "success": True,
                        "user_data": user,
                        "must_change_password": True,
                        "message": "กรุณาเปลี่ยนรหัสผ่าน",
                    }

                return {"success": True, "user_data": user, "message": "เข้าสู่ระบบสำเร็จ"}
            else:
                # Handle failed login
                self._handle_failed_login(user["UserID"])
                return {"success": False, "message": "รหัสผ่านไม่ถูกต้อง"}

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {"success": False, "message": "เกิดข้อผิดพลาดในการเข้าสู่ระบบ"}

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    def _hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        try:
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise

    def _handle_failed_login(self, user_id: int):
        """Handle failed login attempt"""
        try:
            # Get current failed attempts
            query = "SELECT FailedLoginAttempts FROM Users WHERE UserID = ?"
            result = self.db.execute_query(query, (user_id,))

            if result:
                attempts = result[0]["FailedLoginAttempts"] + 1

                if attempts >= self.max_login_attempts:
                    # Lock account
                    self.db.execute_non_query(
                        """
                        UPDATE Users 
                        SET FailedLoginAttempts = ?, LastFailedLogin = GETDATE(), IsLocked = 1
                        WHERE UserID = ?
                    """,
                        (attempts, user_id),
                    )
                else:
                    # Update failed attempts
                    self.db.execute_non_query(
                        """
                        UPDATE Users 
                        SET FailedLoginAttempts = ?, LastFailedLogin = GETDATE()
                        WHERE UserID = ?
                    """,
                        (attempts, user_id),
                    )

        except Exception as e:
            logger.error(f"Failed to handle failed login: {e}")

    def _reset_failed_attempts(self, user_id: int):
        """Reset failed login attempts"""
        try:
            self.db.execute_non_query(
                """
                UPDATE Users 
                SET FailedLoginAttempts = 0, LastFailedLogin = NULL
                WHERE UserID = ?
            """,
                (user_id,),
            )
        except Exception as e:
            logger.error(f"Failed to reset login attempts: {e}")

    def _update_last_login(self, user_id: int):
        """Update last login timestamp"""
        try:
            self.db.execute_non_query(
                """
                UPDATE Users 
                SET LastLoginDate = GETDATE()
                WHERE UserID = ?
            """,
                (user_id,),
            )
        except Exception as e:
            logger.error(f"Failed to update last login: {e}")

    def _check_lockout_expired(self, last_failed_login: datetime) -> bool:
        """Check if lockout period has expired"""
        if not last_failed_login:
            return True

        lockout_expiry = last_failed_login + timedelta(seconds=self.lockout_duration)
        return datetime.now() > lockout_expiry

    def _unlock_user(self, user_id: int):
        """Unlock user account"""
        try:
            self.db.execute_non_query(
                """
                UPDATE Users 
                SET IsLocked = 0, FailedLoginAttempts = 0, LastFailedLogin = NULL
                WHERE UserID = ?
            """,
                (user_id,),
            )
        except Exception as e:
            logger.error(f"Failed to unlock user: {e}")

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> Dict[str, Any]:
        """Change user password"""
        try:
            # Validate new password
            if not self._validate_password(new_password):
                return {"success": False, "message": "รหัสผ่านไม่ตรงตามเงื่อนไข"}

            # Get current password
            query = "SELECT PasswordHash FROM Users WHERE UserID = ?"
            result = self.db.execute_query(query, (user_id,))

            if not result:
                return {"success": False, "message": "ไม่พบผู้ใช้"}

            current_hash = result[0]["PasswordHash"]

            # Verify old password
            if not self._verify_password(old_password, current_hash):
                return {"success": False, "message": "รหัสผ่านเดิมไม่ถูกต้อง"}

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update password
            self.db.execute_non_query(
                """
                UPDATE Users 
                SET PasswordHash = ?, MustChangePassword = 0
                WHERE UserID = ?
            """,
                (new_hash, user_id),
            )

            return {"success": True, "message": "เปลี่ยนรหัสผ่านสำเร็จ"}

        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return {"success": False, "message": "เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน"}

    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < self.password_min_length:
            return False

        # Check for at least one uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return has_upper and has_lower and has_digit and has_special

    def reset_password(self, user_id: int, new_password: str = None) -> Dict[str, Any]:
        """Reset user password (Admin only)"""
        try:
            if not new_password:
                new_password = self._generate_temp_password()

            if not self._validate_password(new_password):
                return {"success": False, "message": "รหัสผ่านไม่ตรงตามเงื่อนไข"}

            new_hash = self._hash_password(new_password)

            self.db.execute_non_query(
                """
                UPDATE Users 
                SET PasswordHash = ?, MustChangePassword = 1, IsLocked = 0, 
                    FailedLoginAttempts = 0, LastFailedLogin = NULL
                WHERE UserID = ?
            """,
                (new_hash, user_id),
            )

            return {
                "success": True,
                "message": "รีเซ็ตรหัสผ่านสำเร็จ",
                "new_password": new_password,
            }

        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            return {"success": False, "message": "เกิดข้อผิดพลาดในการรีเซ็ตรหัสผ่าน"}

    def _generate_temp_password(self) -> str:
        """Generate temporary password"""
        return secrets.token_urlsafe(12)

    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if user has required permission"""
        role_permissions = {
            "Admin": ["all"],
            "Project Manager": ["projects", "tasks", "users", "reports"],
            "Team Lead": ["tasks", "reports"],
            "Developer": ["tasks"],
            "User": ["tasks"],
            "Viewer": ["view"],
        }

        user_permissions = role_permissions.get(user_role, [])
        return "all" in user_permissions or required_permission in user_permissions

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data by ID"""
        try:
            query = """
                SELECT UserID, Username, Email, FirstName, LastName, 
                       Role, Department, IsActive, CreatedDate, LastLoginDate
                FROM Users 
                WHERE UserID = ? AND IsActive = 1
            """

            result = self.db.execute_query(query, (user_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None

    def create_session_token(self, user_id: int) -> str:
        """Create JWT session token"""
        try:
            payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(hours=8),
                "iat": datetime.utcnow(),
            }

            secret_key = st.secrets.get("app", {}).get("secret_key", "fallback-secret")
            return jwt.encode(payload, secret_key, algorithm="HS256")

        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            return None

    def verify_session_token(self, token: str) -> Optional[int]:
        """Verify JWT session token"""
        try:
            secret_key = st.secrets.get("app", {}).get("secret_key", "fallback-secret")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            return payload["user_id"]

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
