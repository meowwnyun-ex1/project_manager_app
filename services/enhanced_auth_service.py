# services/enhanced_auth_service.py
import streamlit as st
import hashlib
import hmac
import secrets
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import pyodbc
from dataclasses import dataclass
import jwt
import bcrypt


@dataclass
class User:
    """User data class"""

    user_id: int
    username: str
    email: str
    role: str
    active: bool
    created_date: datetime
    last_login_date: Optional[datetime] = None
    password_changed_date: Optional[datetime] = None
    profile_picture: Optional[str] = None


@dataclass
class AuthResult:
    """Authentication result data class"""

    success: bool
    user: Optional[User] = None
    message: str = ""
    token: Optional[str] = None
    expires_at: Optional[datetime] = None


class SecurityConfig:
    """Security configuration"""

    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True

    # Session settings
    SESSION_TIMEOUT_MINUTES = 30
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    # Token settings
    JWT_SECRET_KEY = "your-secret-key-change-in-production"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

    # Security headers
    SECURE_COOKIES = True
    SAME_SITE_COOKIES = "strict"


class EnhancedAuthService:
    """Enhanced authentication service with advanced security features"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.security_config = SecurityConfig()
        self._init_session_state()
        self._init_security_tracking()

    def _init_session_state(self):
        """Initialize session state variables"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user" not in st.session_state:
            st.session_state.user = None
        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = {}
        if "session_token" not in st.session_state:
            st.session_state.session_token = None
        if "last_activity" not in st.session_state:
            st.session_state.last_activity = datetime.now()

    def _init_security_tracking(self):
        """Initialize security tracking"""
        if "failed_attempts" not in st.session_state:
            st.session_state.failed_attempts = {}
        if "locked_accounts" not in st.session_state:
            st.session_state.locked_accounts = {}

    def _get_connection(self) -> pyodbc.Connection:
        """Get database connection"""
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            raise

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    def _validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []

        if len(password) < self.security_config.MIN_PASSWORD_LENGTH:
            errors.append(
                f"Password must be at least {self.security_config.MIN_PASSWORD_LENGTH} characters long"
            )

        if self.security_config.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if self.security_config.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if self.security_config.REQUIRE_NUMBERS and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")

        if self.security_config.REQUIRE_SPECIAL_CHARS and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_pattern, email) is not None

    def _generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow()
            + timedelta(hours=self.security_config.JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32),  # JWT ID for token revocation
        }

        return jwt.encode(
            payload,
            self.security_config.JWT_SECRET_KEY,
            algorithm=self.security_config.JWT_ALGORITHM,
        )

    def _verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.security_config.JWT_SECRET_KEY,
                algorithms=[self.security_config.JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        if username in st.session_state.locked_accounts:
            lock_time = st.session_state.locked_accounts[username]
            if datetime.now() - lock_time < timedelta(
                minutes=self.security_config.LOCKOUT_DURATION_MINUTES
            ):
                return True
            else:
                # Unlock account after lockout period
                del st.session_state.locked_accounts[username]
                st.session_state.failed_attempts[username] = 0

        return False

    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in st.session_state.failed_attempts:
            st.session_state.failed_attempts[username] = 0

        st.session_state.failed_attempts[username] += 1

        if (
            st.session_state.failed_attempts[username]
            >= self.security_config.MAX_FAILED_ATTEMPTS
        ):
            st.session_state.locked_accounts[username] = datetime.now()

    def _reset_failed_attempts(self, username: str):
        """Reset failed login attempts after successful login"""
        if username in st.session_state.failed_attempts:
            st.session_state.failed_attempts[username] = 0
        if username in st.session_state.locked_accounts:
            del st.session_state.locked_accounts[username]

    def _check_session_timeout(self) -> bool:
        """Check if session has timed out"""
        if "last_activity" not in st.session_state:
            return True

        time_since_activity = datetime.now() - st.session_state.last_activity
        return time_since_activity > timedelta(
            minutes=self.security_config.SESSION_TIMEOUT_MINUTES
        )

    def _update_last_activity(self):
        """Update last activity timestamp"""
        st.session_state.last_activity = datetime.now()

    def _log_security_event(self, event_type: str, username: str, details: str = ""):
        """Log security events to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO SecurityLog (EventType, Username, Details, Timestamp, IPAddress)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        event_type,
                        username,
                        details,
                        datetime.now(),
                        self._get_client_ip(),
                    ),
                )
                conn.commit()
        except Exception as e:
            # Log to application logs if database logging fails
            print(f"Failed to log security event: {e}")

    def _get_client_ip(self) -> str:
        """Get client IP address (simplified for Streamlit)"""
        # In production, you would extract this from request headers
        return "127.0.0.1"

    def register_user(
        self, username: str, email: str, password: str, role: str = "User"
    ) -> AuthResult:
        """Register a new user"""
        try:
            # Validate inputs
            if not username or not email or not password:
                return AuthResult(False, message="All fields are required")

            if not self._validate_email(email):
                return AuthResult(False, message="Invalid email format")

            is_strong, password_errors = self._validate_password_strength(password)
            if not is_strong:
                return AuthResult(
                    False,
                    message="Password requirements not met: "
                    + "; ".join(password_errors),
                )

            # Check if user already exists
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT UserID FROM Users WHERE Username = ? OR Email = ?",
                    (username, email),
                )
                if cursor.fetchone():
                    return AuthResult(False, message="Username or email already exists")

                # Hash password and create user
                hashed_password = self._hash_password(password)

                cursor.execute(
                    """
                    INSERT INTO Users (Username, Email, PasswordHash, Role, Active, CreatedDate, PasswordChangedDate)
                    VALUES (?, ?, ?, ?, 1, GETDATE(), GETDATE())
                """,
                    (username, email, hashed_password, role),
                )

                conn.commit()

                # Log registration event
                self._log_security_event(
                    "USER_REGISTERED",
                    username,
                    f"New user registered with role: {role}",
                )

                return AuthResult(True, message="User registered successfully")

        except Exception as e:
            return AuthResult(False, message=f"Registration failed: {str(e)}")

    def login(self, username: str, password: str) -> AuthResult:
        """Authenticate user login"""
        try:
            # Check if account is locked
            if self._is_account_locked(username):
                remaining_time = self.security_config.LOCKOUT_DURATION_MINUTES - int(
                    (
                        datetime.now() - st.session_state.locked_accounts[username]
                    ).total_seconds()
                    / 60
                )
                return AuthResult(
                    False,
                    message=f"Account locked. Try again in {remaining_time} minutes",
                )

            # Validate user credentials
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT UserID, Username, Email, PasswordHash, Role, Active, 
                           CreatedDate, LastLoginDate, PasswordChangedDate, ProfilePicture
                    FROM Users 
                    WHERE Username = ? AND Active = 1
                """,
                    (username,),
                )

                user_data = cursor.fetchone()

                if not user_data:
                    self._record_failed_attempt(username)
                    self._log_security_event("LOGIN_FAILED", username, "User not found")
                    return AuthResult(False, message="Invalid username or password")

                # Verify password
                if not self._verify_password(password, user_data.PasswordHash):
                    self._record_failed_attempt(username)
                    self._log_security_event(
                        "LOGIN_FAILED", username, "Invalid password"
                    )
                    return AuthResult(False, message="Invalid username or password")

                # Create user object
                user = User(
                    user_id=user_data.UserID,
                    username=user_data.Username,
                    email=user_data.Email,
                    role=user_data.Role,
                    active=user_data.Active,
                    created_date=user_data.CreatedDate,
                    last_login_date=user_data.LastLoginDate,
                    password_changed_date=user_data.PasswordChangedDate,
                    profile_picture=user_data.ProfilePicture,
                )

                # Generate JWT token
                token = self._generate_jwt_token(user)
                expires_at = datetime.utcnow() + timedelta(
                    hours=self.security_config.JWT_EXPIRATION_HOURS
                )

                # Update last login time
                cursor.execute(
                    "UPDATE Users SET LastLoginDate = GETDATE() WHERE UserID = ?",
                    (user.user_id,),
                )
                conn.commit()

                # Reset failed attempts
                self._reset_failed_attempts(username)

                # Update session state
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.session_token = token
                self._update_last_activity()

                # Log successful login
                self._log_security_event(
                    "LOGIN_SUCCESS", username, f"User logged in with role: {user.role}"
                )

                return AuthResult(
                    True,
                    user=user,
                    token=token,
                    expires_at=expires_at,
                    message="Login successful",
                )

        except Exception as e:
            self._log_security_event("LOGIN_ERROR", username, f"Login error: {str(e)}")
            return AuthResult(False, message=f"Login failed: {str(e)}")

    def logout(self) -> bool:
        """Logout current user"""
        try:
            username = (
                st.session_state.get("user", {}).username
                if st.session_state.get("user")
                else "Unknown"
            )

            # Clear session state
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.session_token = None
            st.session_state.last_activity = None

            # Log logout event
            self._log_security_event("LOGOUT", username, "User logged out")

            return True

        except Exception as e:
            print(f"Logout error: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        if not st.session_state.get("authenticated", False):
            return False

        if not st.session_state.get("user"):
            return False

        if not st.session_state.get("session_token"):
            return False

        # Check session timeout
        if self._check_session_timeout():
            self.logout()
            return False

        # Verify JWT token
        payload = self._verify_jwt_token(st.session_state.session_token)
        if not payload:
            self.logout()
            return False

        # Update last activity
        self._update_last_activity()

        return True

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        if self.is_authenticated():
            return st.session_state.user
        return None

    def change_password(self, current_password: str, new_password: str) -> AuthResult:
        """Change user password"""
        try:
            user = self.get_current_user()
            if not user:
                return AuthResult(False, message="User not authenticated")

            # Validate new password strength
            is_strong, password_errors = self._validate_password_strength(new_password)
            if not is_strong:
                return AuthResult(
                    False,
                    message="Password requirements not met: "
                    + "; ".join(password_errors),
                )

            # Verify current password
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT PasswordHash FROM Users WHERE UserID = ?", (user.user_id,)
                )
                result = cursor.fetchone()

                if not result or not self._verify_password(
                    current_password, result.PasswordHash
                ):
                    return AuthResult(False, message="Current password is incorrect")

                # Update password
                new_hashed_password = self._hash_password(new_password)
                cursor.execute(
                    """
                    UPDATE Users 
                    SET PasswordHash = ?, PasswordChangedDate = GETDATE()
                    WHERE UserID = ?
                """,
                    (new_hashed_password, user.user_id),
                )

                conn.commit()

                # Log password change
                self._log_security_event(
                    "PASSWORD_CHANGED", user.username, "Password changed successfully"
                )

                return AuthResult(True, message="Password changed successfully")

        except Exception as e:
            return AuthResult(False, message=f"Password change failed: {str(e)}")

    def reset_password(self, email: str) -> AuthResult:
        """Initiate password reset process"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT UserID, Username FROM Users WHERE Email = ? AND Active = 1",
                    (email,),
                )
                user_data = cursor.fetchone()

                if not user_data:
                    # Don't reveal if email exists for security
                    return AuthResult(
                        True, message="If the email exists, a reset link has been sent"
                    )

                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiration

                # Store reset token (you would implement a PasswordResets table)
                cursor.execute(
                    """
                    INSERT INTO PasswordResets (UserID, ResetToken, ExpiresAt, Used)
                    VALUES (?, ?, ?, 0)
                """,
                    (user_data.UserID, reset_token, expires_at),
                )

                conn.commit()

                # Log password reset request
                self._log_security_event(
                    "PASSWORD_RESET_REQUESTED",
                    user_data.Username,
                    "Password reset requested",
                )

                # In production, you would send an email with the reset link
                # For demo purposes, we'll just return success
                return AuthResult(
                    True, message="Password reset link sent to your email"
                )

        except Exception as e:
            return AuthResult(False, message=f"Password reset failed: {str(e)}")

    def validate_reset_token(self, token: str) -> Optional[int]:
        """Validate password reset token"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT UserID FROM PasswordResets 
                    WHERE ResetToken = ? AND ExpiresAt > GETDATE() AND Used = 0
                """,
                    (token,),
                )

                result = cursor.fetchone()
                return result.UserID if result else None

        except Exception:
            return None

    def reset_password_with_token(self, token: str, new_password: str) -> AuthResult:
        """Reset password using valid token"""
        try:
            user_id = self.validate_reset_token(token)
            if not user_id:
                return AuthResult(False, message="Invalid or expired reset token")

            # Validate new password strength
            is_strong, password_errors = self._validate_password_strength(new_password)
            if not is_strong:
                return AuthResult(
                    False,
                    message="Password requirements not met: "
                    + "; ".join(password_errors),
                )

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Update password
                new_hashed_password = self._hash_password(new_password)
                cursor.execute(
                    """
                    UPDATE Users 
                    SET PasswordHash = ?, PasswordChangedDate = GETDATE()
                    WHERE UserID = ?
                """,
                    (new_hashed_password, user_id),
                )

                # Mark reset token as used
                cursor.execute(
                    """
                    UPDATE PasswordResets 
                    SET Used = 1 
                    WHERE ResetToken = ?
                """,
                    (token,),
                )

                conn.commit()

                # Get username for logging
                cursor.execute(
                    "SELECT Username FROM Users WHERE UserID = ?", (user_id,)
                )
                username = cursor.fetchone().Username

                # Log password reset
                self._log_security_event(
                    "PASSWORD_RESET_COMPLETED", username, "Password reset completed"
                )

                return AuthResult(True, message="Password reset successfully")

        except Exception as e:
            return AuthResult(False, message=f"Password reset failed: {str(e)}")

    def update_user_profile(
        self, user_id: int, email: str = None, profile_picture: str = None
    ) -> AuthResult:
        """Update user profile information"""
        try:
            user = self.get_current_user()
            if not user or user.user_id != user_id:
                return AuthResult(False, message="Unauthorized")

            updates = []
            params = []

            if email:
                if not self._validate_email(email):
                    return AuthResult(False, message="Invalid email format")
                updates.append("Email = ?")
                params.append(email)

            if profile_picture:
                updates.append("ProfilePicture = ?")
                params.append(profile_picture)

            if not updates:
                return AuthResult(False, message="No updates provided")

            params.append(user_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE Users 
                    SET {', '.join(updates)}
                    WHERE UserID = ?
                """,
                    params,
                )

                conn.commit()

                # Update session user data
                if email:
                    st.session_state.user.email = email
                if profile_picture:
                    st.session_state.user.profile_picture = profile_picture

                # Log profile update
                self._log_security_event(
                    "PROFILE_UPDATED", user.username, "Profile information updated"
                )

                return AuthResult(True, message="Profile updated successfully")

        except Exception as e:
            return AuthResult(False, message=f"Profile update failed: {str(e)}")

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT UserID, Username, Email, Role, Active, 
                           CreatedDate, LastLoginDate, PasswordChangedDate, ProfilePicture
                    FROM Users 
                    WHERE UserID = ?
                """,
                    (user_id,),
                )

                user_data = cursor.fetchone()

                if user_data:
                    return User(
                        user_id=user_data.UserID,
                        username=user_data.Username,
                        email=user_data.Email,
                        role=user_data.Role,
                        active=user_data.Active,
                        created_date=user_data.CreatedDate,
                        last_login_date=user_data.LastLoginDate,
                        password_changed_date=user_data.PasswordChangedDate,
                        profile_picture=user_data.ProfilePicture,
                    )

                return None

        except Exception:
            return None

    def has_permission(self, permission: str) -> bool:
        """Check if current user has specific permission"""
        user = self.get_current_user()
        if not user:
            return False

        # Define role-based permissions
        permissions = {
            "Admin": ["*"],  # Admin has all permissions
            "Manager": [
                "view_all_projects",
                "create_project",
                "edit_project",
                "delete_project",
                "view_all_tasks",
                "create_task",
                "edit_task",
                "delete_task",
                "view_team",
                "manage_team",
                "view_reports",
            ],
            "Developer": [
                "view_assigned_projects",
                "view_all_tasks",
                "create_task",
                "edit_own_task",
                "view_team",
            ],
            "Designer": [
                "view_assigned_projects",
                "view_all_tasks",
                "create_task",
                "edit_own_task",
                "view_team",
            ],
            "User": ["view_assigned_projects", "view_own_tasks", "edit_own_task"],
        }

        user_permissions = permissions.get(user.role, [])

        # Admin has all permissions
        if "*" in user_permissions:
            return True

        return permission in user_permissions

    def require_permission(self, permission: str) -> bool:
        """Decorator-like function to require permission"""
        if not self.has_permission(permission):
            st.error("❌ You don't have permission to access this feature")
            st.stop()
        return True

    def get_security_summary(self) -> Dict:
        """Get security summary for admin dashboard"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get user counts by role
                cursor.execute(
                    """
                    SELECT Role, COUNT(*) as Count
                    FROM Users 
                    WHERE Active = 1
                    GROUP BY Role
                """
                )
                user_counts = {row.Role: row.Count for row in cursor.fetchall()}

                # Get recent security events
                cursor.execute(
                    """
                    SELECT TOP 10 EventType, Username, Timestamp, Details
                    FROM SecurityLog 
                    ORDER BY Timestamp DESC
                """
                )
                recent_events = [
                    {
                        "event_type": row.EventType,
                        "username": row.Username,
                        "timestamp": row.Timestamp,
                        "details": row.Details,
                    }
                    for row in cursor.fetchall()
                ]

                return {
                    "user_counts": user_counts,
                    "recent_events": recent_events,
                    "failed_attempts": dict(st.session_state.failed_attempts),
                    "locked_accounts": len(st.session_state.locked_accounts),
                }

        except Exception as e:
            return {"error": str(e)}


# Export the service class
__all__ = ["EnhancedAuthService", "User", "AuthResult", "SecurityConfig"]
