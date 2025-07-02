# services/enhanced_auth_service.py
import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from .enhanced_db_service import get_db_service, DatabaseException

logger = logging.getLogger(__name__)


class AuthenticationService:
    def __init__(self):
        self.db_service = get_db_service()
        self.jwt_secret = "your-secret-key"
        self.token_expiry = timedelta(hours=24)

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        try:
            query = "SELECT UserID, Username, PasswordHash, Email, Role, Active FROM Users WHERE Username = ? AND Active = 1"
            result = self.db_service.execute_query(query, (username,))

            if not result:
                return None

            user = result[0]

            if bcrypt.checkpw(
                password.encode("utf-8"), user["PasswordHash"].encode("utf-8")
            ):
                # Update last login
                update_query = (
                    "UPDATE Users SET LastLoginDate = GETDATE() WHERE UserID = ?"
                )
                self.db_service.execute_query(
                    update_query, (user["UserID"],), fetch=False
                )

                # Remove password hash
                del user["PasswordHash"]
                return user

            return None

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    def create_user(
        self, username: str, password: str, email: str, role: str = "User"
    ) -> bool:
        """Create new user"""
        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            query = """
            INSERT INTO Users (Username, PasswordHash, Email, Role, Active, PasswordChangedDate)
            VALUES (?, ?, ?, ?, 1, GETDATE())
            """

            self.db_service.execute_query(
                query, (username, password_hash, email, role), fetch=False
            )
            return True

        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return False


def get_auth_service() -> AuthenticationService:
    return AuthenticationService()
