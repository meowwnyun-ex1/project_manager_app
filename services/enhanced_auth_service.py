# services/enhanced_auth_service.py
import bcrypt
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import re

from .enhanced_db_service import get_db_service, DatabaseException

logger = logging.getLogger(__name__)


class EnhancedAuthService:
    """Enhanced authentication service"""

    def __init__(self, connection_string: str = None):
        self.db_service = get_db_service()
        self.max_login_attempts = 5
        self.lockout_duration = 30  # minutes

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password"""
        try:
            # Get user by username
            query = """
            SELECT UserID, Username, PasswordHash, Email, FirstName, LastName, Role, Active
            FROM Users 
            WHERE Username = ? AND Active = 1
            """

            result = self.db_service.execute_query(query, (username,))

            if not result:
                logger.warning(f"Authentication failed: User not found - {username}")
                return None

            user_data = result[0]

            # For demo purposes, allow simple password check
            if password == "admin" and username == "admin":
                # Update last login
                self._update_last_login(user_data["UserID"])

                # Remove password hash from response
                del user_data["PasswordHash"]

                logger.info(f"User authenticated successfully: {username}")
                return user_data

            # Verify password with bcrypt (if hash exists)
            if user_data.get("PasswordHash") and self._verify_password(
                password, user_data["PasswordHash"]
            ):
                # Update last login
                self._update_last_login(user_data["UserID"])

                # Remove password hash from response
                del user_data["PasswordHash"]

                logger.info(f"User authenticated successfully: {username}")
                return user_data

            logger.warning(f"Authentication failed: Invalid password - {username}")
            return None

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception:
            return False

    def _update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            query = "UPDATE Users SET LastLoginDate = GETDATE() WHERE UserID = ?"
            self.db_service.execute_query(query, (user_id,), fetch=False)
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {str(e)}")


# Global service instance
_auth_service = None


def get_auth_service() -> EnhancedAuthService:
    """Get global auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = EnhancedAuthService()
    return _auth_service
