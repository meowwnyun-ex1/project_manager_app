# services/user_service.py
from typing import List, Dict, Any, Optional
from services.enhanced_db_service import DatabaseService
from models.user import User
import logging

logger = logging.getLogger(__name__)


class UserService:
    """User management service"""

    @staticmethod
    def get_all_users() -> List[Dict[str, Any]]:
        """Get all users for dropdowns and assignments"""
        query = "SELECT UserID, Username, Role FROM Users ORDER BY Username"
        return DatabaseService.fetch_data(query)

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        query = "SELECT UserID, Username, PasswordHash, Role, CreatedDate FROM Users WHERE UserID = ?"
        data = DatabaseService.fetch_one(query, (user_id,))
        return User.from_dict(data) if data else None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        query = "SELECT UserID, Username, PasswordHash, Role, CreatedDate FROM Users WHERE Username = ?"
        data = DatabaseService.fetch_one(query, (username,))
        return User.from_dict(data) if data else None

    @staticmethod
    def update_user_role(user_id: int, new_role: str) -> bool:
        """Update user role (Admin function)"""
        try:
            # Validate role
            from config.settings import app_config

            if new_role not in app_config.USER_ROLES:
                logger.error(f"Invalid role: {new_role}")
                return False

            query = "UPDATE Users SET Role = ? WHERE UserID = ?"
            success = DatabaseService.execute_query(query, (new_role, user_id))

            if success:
                logger.info(f"User role updated: {user_id} -> {new_role}")

            return success

        except Exception as e:
            logger.error(f"Failed to update user role: {e}")
            return False

    @staticmethod
    def get_user_statistics() -> Dict[str, Any]:
        """Get user statistics"""
        try:
            # Total users
            total_query = "SELECT COUNT(*) FROM Users"
            total_users = DatabaseService.execute_scalar(total_query) or 0

            # Users by role
            role_query = "SELECT Role, COUNT(*) as Count FROM Users GROUP BY Role"
            role_data = DatabaseService.fetch_data(role_query)

            # Recently registered users (last 30 days)
            recent_query = """
            SELECT COUNT(*) FROM Users 
            WHERE CreatedDate >= DATEADD(day, -30, GETDATE())
            """
            recent_users = DatabaseService.execute_scalar(recent_query) or 0

            return {
                "total_users": total_users,
                "recent_users": recent_users,
                "role_distribution": role_data,
            }

        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return {}

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Delete user (Admin function)"""
        try:
            # Note: This might need cascade handling for foreign keys
            query = "DELETE FROM Users WHERE UserID = ?"
            success = DatabaseService.execute_query(query, (user_id,))

            if success:
                logger.info(f"User deleted: {user_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False
