# services/user_service.py
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import bcrypt
import re
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from .enhanced_db_service import (
    get_db_service,
    with_db_transaction,
    cached_query,
    DatabaseException,
)

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User role enumeration"""

    ADMIN = "Admin"
    MANAGER = "Manager"
    USER = "User"
    VIEWER = "Viewer"


@dataclass
class User:
    """User data model"""

    user_id: Optional[int] = None
    username: str = ""
    email: str = ""
    role: str = UserRole.USER.value
    active: bool = True
    created_date: Optional[datetime] = None
    last_login_date: Optional[datetime] = None
    password_changed_date: Optional[datetime] = None
    profile_picture: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class UserService:
    """Enhanced user management service"""

    def __init__(self):
        self.db_service = get_db_service()
        self.password_min_length = 8
        self.password_complexity = True
        self.max_login_attempts = 5
        self.lockout_duration = 30  # minutes

    @with_db_transaction
    def create_user(
        self, user_data: Dict[str, Any], created_by_user_id: Optional[int] = None
    ) -> int:
        """Create a new user"""
        try:
            # Validate required fields
            required_fields = ["username", "email", "password"]
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    raise ValueError(f"Required field '{field}' is missing")

            # Validate username
            if not self._validate_username(user_data["username"]):
                raise ValueError("Invalid username format")

            # Check username uniqueness
            if self._username_exists(user_data["username"]):
                raise ValueError("Username already exists")

            # Validate email
            if not self._validate_email(user_data["email"]):
                raise ValueError("Invalid email format")

            # Check email uniqueness
            if self._email_exists(user_data["email"]):
                raise ValueError("Email already exists")

            # Validate password
            if not self._validate_password(user_data["password"]):
                raise ValueError("Password does not meet complexity requirements")

            # Hash password
            password_hash = self._hash_password(user_data["password"])

            # Validate role
            role = user_data.get("role", UserRole.USER.value)
            if role not in [r.value for r in UserRole]:
                raise ValueError("Invalid user role")

            # Insert user
            query = """
            INSERT INTO Users (
                Username, PasswordHash, Email, Role, Active,
                PasswordChangedDate, ProfilePicture
            )
            OUTPUT INSERTED.UserID
            VALUES (?, ?, ?, ?, ?, GETDATE(), ?)
            """

            params = (
                user_data["username"].strip(),
                password_hash,
                user_data["email"].strip().lower(),
                role,
                user_data.get("active", True),
                user_data.get("profile_picture"),
            )

            result = self.db_service.execute_query(query, params)
            user_id = result[0]["UserID"]

            # Clear cache
            self.db_service.clear_cache("users_")

            logger.info(
                f"User created successfully: ID {user_id}, Username: {user_data['username']}"
            )
            return user_id

        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise DatabaseException(f"User creation failed: {str(e)}")

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with username/password"""
        try:
            # Get user by username
            query = """
            SELECT UserID, Username, PasswordHash, Email, Role, Active,
                   LastLoginDate, PasswordChangedDate
            FROM Users 
            WHERE Username = ? AND Active = 1
            """

            result = self.db_service.execute_query(query, (username.strip(),))

            if not result:
                logger.warning(f"Authentication failed: User not found - {username}")
                return None

            user_data = result[0]

            # Verify password
            if not self._verify_password(password, user_data["PasswordHash"]):
                logger.warning(f"Authentication failed: Invalid password - {username}")
                return None

            # Update last login
            self._update_last_login(user_data["UserID"])

            # Remove password hash from response
            del user_data["PasswordHash"]

            logger.info(f"User authenticated successfully: {username}")
            return user_data

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            query = """
            SELECT UserID, Username, Email, Role, Active,
                   CreatedDate, LastLoginDate, PasswordChangedDate,
                   ProfilePicture
            FROM Users 
            WHERE UserID = ?
            """

            result = self.db_service.execute_query(query, (user_id,))

            if result:
                user_data = result[0]

                # Add additional user statistics
                user_data["stats"] = self._get_user_statistics(user_id)
                user_data["permissions"] = self._get_user_permissions(user_data["Role"])

                return user_data

            return None

        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            raise DatabaseException(f"User retrieval failed: {str(e)}")

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            query = """
            SELECT UserID, Username, Email, Role, Active,
                   CreatedDate, LastLoginDate, PasswordChangedDate,
                   ProfilePicture
            FROM Users 
            WHERE Username = ?
            """

            result = self.db_service.execute_query(query, (username.strip(),))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {str(e)}")
            raise DatabaseException(f"User retrieval failed: {str(e)}")

    @cached_query("all_users", ttl=300)
    def get_all_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            base_query = """
            SELECT UserID, Username, Email, Role, Active,
                   CreatedDate, LastLoginDate, PasswordChangedDate,
                   ProfilePicture
            FROM Users
            """

            params = []

            if not include_inactive:
                base_query += " WHERE Active = 1"

            base_query += " ORDER BY CreatedDate DESC"

            result = self.db_service.execute_query(base_query, tuple(params))

            # Add statistics for each user
            for user in result:
                user["stats"] = self._get_user_statistics(user["UserID"])

            return result

        except Exception as e:
            logger.error(f"Failed to get all users: {str(e)}")
            raise DatabaseException(f"User retrieval failed: {str(e)}")

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get users by role"""
        try:
            query = """
            SELECT UserID, Username, Email, Role, Active,
                   CreatedDate, LastLoginDate, ProfilePicture
            FROM Users 
            WHERE Role = ? AND Active = 1
            ORDER BY Username
            """

            result = self.db_service.execute_query(query, (role,))
            return result

        except Exception as e:
            logger.error(f"Failed to get users by role {role}: {str(e)}")
            raise DatabaseException(f"User retrieval failed: {str(e)}")

    @with_db_transaction
    def update_user(
        self, user_id: int, user_data: Dict[str, Any], updated_by_user_id: int
    ) -> bool:
        """Update existing user"""
        try:
            # Validate user exists
            existing_user = self.get_user(user_id)
            if not existing_user:
                raise ValueError("User does not exist")

            # Build update query dynamically
            update_fields = []
            params = []

            # Fields that can be updated
            updatable_fields = {
                "username": "Username",
                "email": "Email",
                "role": "Role",
                "active": "Active",
                "profile_picture": "ProfilePicture",
            }

            for field_key, db_field in updatable_fields.items():
                if field_key in user_data:
                    value = user_data[field_key]

                    # Validate specific fields
                    if field_key == "username":
                        if not self._validate_username(value):
                            raise ValueError("Invalid username format")
                        if value != existing_user["Username"] and self._username_exists(
                            value
                        ):
                            raise ValueError("Username already exists")

                    if field_key == "email":
                        if not self._validate_email(value):
                            raise ValueError("Invalid email format")
                        if value != existing_user["Email"] and self._email_exists(
                            value
                        ):
                            raise ValueError("Email already exists")
                        value = value.strip().lower()

                    if field_key == "role" and value not in [r.value for r in UserRole]:
                        raise ValueError("Invalid user role")

                    update_fields.append(f"{db_field} = ?")
                    params.append(value)

            if not update_fields:
                return True  # Nothing to update

            query = f"""
            UPDATE Users 
            SET {', '.join(update_fields)}
            WHERE UserID = ?
            """
            params.append(user_id)

            self.db_service.execute_query(query, tuple(params), fetch=False)

            # Clear cache
            self.db_service.clear_cache("users_")

            logger.info(
                f"User {user_id} updated successfully by user {updated_by_user_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise DatabaseException(f"User update failed: {str(e)}")

    @with_db_transaction
    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        try:
            # Get current password hash
            query = "SELECT PasswordHash FROM Users WHERE UserID = ?"
            result = self.db_service.execute_query(query, (user_id,))

            if not result:
                raise ValueError("User not found")

            current_hash = result[0]["PasswordHash"]

            # Verify old password
            if not self._verify_password(old_password, current_hash):
                raise ValueError("Current password is incorrect")

            # Validate new password
            if not self._validate_password(new_password):
                raise ValueError("New password does not meet complexity requirements")

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update password
            update_query = """
            UPDATE Users 
            SET PasswordHash = ?, PasswordChangedDate = GETDATE()
            WHERE UserID = ?
            """

            self.db_service.execute_query(
                update_query, (new_hash, user_id), fetch=False
            )

            logger.info(f"Password changed successfully for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {str(e)}")
            raise DatabaseException(f"Password change failed: {str(e)}")

    @with_db_transaction
    def reset_password(
        self, user_id: int, new_password: str, reset_by_user_id: int
    ) -> bool:
        """Reset user password (admin function)"""
        try:
            # Validate new password
            if not self._validate_password(new_password):
                raise ValueError("New password does not meet complexity requirements")

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update password
            query = """
            UPDATE Users 
            SET PasswordHash = ?, PasswordChangedDate = GETDATE()
            WHERE UserID = ?
            """

            self.db_service.execute_query(query, (new_hash, user_id), fetch=False)

            logger.info(f"Password reset for user {user_id} by user {reset_by_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset password for user {user_id}: {str(e)}")
            raise DatabaseException(f"Password reset failed: {str(e)}")

    @with_db_transaction
    def deactivate_user(self, user_id: int, deactivated_by_user_id: int) -> bool:
        """Deactivate user account"""
        try:
            query = "UPDATE Users SET Active = 0 WHERE UserID = ?"
            self.db_service.execute_query(query, (user_id,), fetch=False)

            # Clear cache
            self.db_service.clear_cache("users_")

            logger.info(f"User {user_id} deactivated by user {deactivated_by_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {str(e)}")
            raise DatabaseException(f"User deactivation failed: {str(e)}")

    @with_db_transaction
    def activate_user(self, user_id: int, activated_by_user_id: int) -> bool:
        """Activate user account"""
        try:
            query = "UPDATE Users SET Active = 1 WHERE UserID = ?"
            self.db_service.execute_query(query, (user_id,), fetch=False)

            # Clear cache
            self.db_service.clear_cache("users_")

            logger.info(f"User {user_id} activated by user {activated_by_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to activate user {user_id}: {str(e)}")
            raise DatabaseException(f"User activation failed: {str(e)}")

    @with_db_transaction
    def delete_user(self, user_id: int, deleted_by_user_id: int) -> bool:
        """Delete user account (hard delete)"""
        try:
            # Check if user exists
            existing_user = self.get_user(user_id)
            if not existing_user:
                raise ValueError("User does not exist")

            # Delete user (cascade will handle related records)
            query = "DELETE FROM Users WHERE UserID = ?"
            self.db_service.execute_query(query, (user_id,), fetch=False)

            # Clear cache
            self.db_service.clear_cache("users_")

            logger.info(f"User {user_id} deleted by user {deleted_by_user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise DatabaseException(f"User deletion failed: {str(e)}")

    def search_users(
        self, search_query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search users with advanced filtering"""
        try:
            base_query = """
            SELECT UserID, Username, Email, Role, Active,
                   CreatedDate, LastLoginDate, ProfilePicture
            FROM Users
            WHERE (
                Username LIKE ? OR
                Email LIKE ?
            )
            """

            search_pattern = f"%{search_query}%"
            params = [search_pattern, search_pattern]

            # Apply filters
            if filters:
                if filters.get("role"):
                    base_query += " AND Role = ?"
                    params.append(filters["role"])

                if filters.get("active") is not None:
                    base_query += " AND Active = ?"
                    params.append(1 if filters["active"] else 0)

                if filters.get("created_after"):
                    base_query += " AND CreatedDate >= ?"
                    params.append(filters["created_after"])

                if filters.get("last_login_after"):
                    base_query += " AND LastLoginDate >= ?"
                    params.append(filters["last_login_after"])

            base_query += " ORDER BY Username"

            result = self.db_service.execute_query(base_query, tuple(params))

            # Add statistics for each user
            for user in result:
                user["stats"] = self._get_user_statistics(user["UserID"])
                user["relevance_score"] = self._calculate_user_relevance(
                    user, search_query
                )

            # Sort by relevance
            result.sort(key=lambda x: x["relevance_score"], reverse=True)

            return result

        except Exception as e:
            logger.error(f"Failed to search users: {str(e)}")
            raise DatabaseException(f"User search failed: {str(e)}")

    def get_user_analytics(
        self, date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        try:
            base_query = """
            SELECT 
                Role,
                Active,
                CreatedDate,
                LastLoginDate
            FROM Users
            WHERE 1=1
            """

            params = []

            if date_range:
                base_query += " AND CreatedDate BETWEEN ? AND ?"
                params.extend(date_range)

            users = self.db_service.execute_query(base_query, tuple(params))

            if not users:
                return self._empty_user_analytics()

            # Calculate analytics
            analytics = {
                "total_users": len(users),
                "active_users": len([u for u in users if u["Active"]]),
                "inactive_users": len([u for u in users if not u["Active"]]),
                "role_distribution": self._calculate_role_distribution(users),
                "activity_metrics": self._calculate_activity_metrics(users),
                "growth_metrics": self._calculate_growth_metrics(users),
                "login_analytics": self._calculate_login_analytics(users),
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            raise DatabaseException(f"User analytics failed: {str(e)}")

    def get_team_members(
        self, project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get team members for a project or all active users"""
        try:
            if project_id:
                # Get users assigned to project tasks
                query = """
                SELECT DISTINCT 
                    u.UserID, u.Username, u.Email, u.Role, u.ProfilePicture,
                    COUNT(t.TaskID) as TaskCount,
                    AVG(CAST(t.Progress as FLOAT)) as AvgProgress
                FROM Users u
                INNER JOIN Tasks t ON u.UserID = t.AssigneeID
                WHERE t.ProjectID = ? AND u.Active = 1
                GROUP BY u.UserID, u.Username, u.Email, u.Role, u.ProfilePicture
                ORDER BY u.Username
                """
                params = (project_id,)
            else:
                # Get all active users
                query = """
                SELECT 
                    u.UserID, u.Username, u.Email, u.Role, u.ProfilePicture,
                    COUNT(t.TaskID) as TaskCount,
                    ISNULL(AVG(CAST(t.Progress as FLOAT)), 0) as AvgProgress
                FROM Users u
                LEFT JOIN Tasks t ON u.UserID = t.AssigneeID
                WHERE u.Active = 1
                GROUP BY u.UserID, u.Username, u.Email, u.Role, u.ProfilePicture
                ORDER BY u.Username
                """
                params = ()

            result = self.db_service.execute_query(query, params)

            # Add additional team member data
            for member in result:
                member["workload_level"] = self._calculate_workload_level(
                    member["TaskCount"]
                )
                member["performance_score"] = self._calculate_performance_score(member)

            return result

        except Exception as e:
            logger.error(f"Failed to get team members: {str(e)}")
            raise DatabaseException(f"Team member retrieval failed: {str(e)}")

    # Helper methods
    def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        if not username or len(username) < 3 or len(username) > 50:
            return False

        # Allow alphanumeric, underscore, and hyphen
        pattern = r"^[a-zA-Z0-9_-]+$"
        return re.match(pattern, username) is not None

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email:
            return False

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _validate_password(self, password: str) -> bool:
        """Validate password complexity"""
        if not password or len(password) < self.password_min_length:
            return False

        if not self.password_complexity:
            return True

        # Check for at least one uppercase, lowercase, digit, and special character
        checks = [
            any(c.isupper() for c in password),  # Uppercase
            any(c.islower() for c in password),  # Lowercase
            any(c.isdigit() for c in password),  # Digit
            any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),  # Special char
        ]

        return sum(checks) >= 3  # At least 3 out of 4 criteria

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except:
            return False

    def _username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        try:
            query = "SELECT COUNT(*) as count FROM Users WHERE Username = ?"
            result = self.db_service.execute_query(query, (username.strip(),))
            return result[0]["count"] > 0
        except:
            return False

    def _email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        try:
            query = "SELECT COUNT(*) as count FROM Users WHERE Email = ?"
            result = self.db_service.execute_query(query, (email.strip().lower(),))
            return result[0]["count"] > 0
        except:
            return False

    def _update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            query = "UPDATE Users SET LastLoginDate = GETDATE() WHERE UserID = ?"
            self.db_service.execute_query(query, (user_id,), fetch=False)
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {str(e)}")

    def _get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            # Get project and task counts
            stats_query = """
            SELECT 
                COUNT(DISTINCT p.ProjectID) as ProjectsCreated,
                COUNT(DISTINCT t.TaskID) as TasksAssigned,
                COUNT(DISTINCT CASE WHEN t.Status = 'Done' THEN t.TaskID END) as TasksCompleted,
                ISNULL(AVG(CAST(t.Progress as FLOAT)), 0) as AvgTaskProgress
            FROM Users u
            LEFT JOIN Projects p ON u.UserID = p.CreatedBy
            LEFT JOIN Tasks t ON u.UserID = t.AssigneeID
            WHERE u.UserID = ?
            """

            result = self.db_service.execute_query(stats_query, (user_id,))
            stats = result[0] if result else {}

            # Calculate completion rate
            tasks_assigned = stats.get("TasksAssigned", 0)
            tasks_completed = stats.get("TasksCompleted", 0)
            completion_rate = (
                (tasks_completed / tasks_assigned * 100) if tasks_assigned > 0 else 0
            )

            return {
                "projects_created": stats.get("ProjectsCreated", 0),
                "tasks_assigned": tasks_assigned,
                "tasks_completed": tasks_completed,
                "completion_rate": round(completion_rate, 2),
                "avg_task_progress": round(stats.get("AvgTaskProgress", 0), 2),
            }

        except Exception as e:
            logger.error(f"Failed to get user statistics for {user_id}: {str(e)}")
            return {
                "projects_created": 0,
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "completion_rate": 0,
                "avg_task_progress": 0,
            }

    def _get_user_permissions(self, role: str) -> Dict[str, bool]:
        """Get user permissions based on role"""
        permissions = {
            UserRole.ADMIN.value: {
                "can_create_projects": True,
                "can_edit_projects": True,
                "can_delete_projects": True,
                "can_manage_users": True,
                "can_view_analytics": True,
                "can_manage_settings": True,
                "can_assign_tasks": True,
                "can_view_all_projects": True,
            },
            UserRole.MANAGER.value: {
                "can_create_projects": True,
                "can_edit_projects": True,
                "can_delete_projects": False,
                "can_manage_users": False,
                "can_view_analytics": True,
                "can_manage_settings": False,
                "can_assign_tasks": True,
                "can_view_all_projects": True,
            },
            UserRole.USER.value: {
                "can_create_projects": False,
                "can_edit_projects": False,
                "can_delete_projects": False,
                "can_manage_users": False,
                "can_view_analytics": False,
                "can_manage_settings": False,
                "can_assign_tasks": False,
                "can_view_all_projects": False,
            },
            UserRole.VIEWER.value: {
                "can_create_projects": False,
                "can_edit_projects": False,
                "can_delete_projects": False,
                "can_manage_users": False,
                "can_view_analytics": False,
                "can_manage_settings": False,
                "can_assign_tasks": False,
                "can_view_all_projects": False,
            },
        }

        return permissions.get(role, permissions[UserRole.USER.value])

    def _calculate_role_distribution(
        self, users: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate role distribution"""
        distribution = {}
        for user in users:
            role = user.get("Role", "Unknown")
            distribution[role] = distribution.get(role, 0) + 1
        return distribution

    def _calculate_activity_metrics(
        self, users: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate user activity metrics"""
        now = datetime.now()

        # Users who logged in within different timeframes
        last_day = len(
            [
                u
                for u in users
                if u.get("LastLoginDate") and (now - u["LastLoginDate"]).days <= 1
            ]
        )
        last_week = len(
            [
                u
                for u in users
                if u.get("LastLoginDate") and (now - u["LastLoginDate"]).days <= 7
            ]
        )
        last_month = len(
            [
                u
                for u in users
                if u.get("LastLoginDate") and (now - u["LastLoginDate"]).days <= 30
            ]
        )

        return {
            "active_last_day": last_day,
            "active_last_week": last_week,
            "active_last_month": last_month,
            "never_logged_in": len([u for u in users if not u.get("LastLoginDate")]),
        }

    def _calculate_growth_metrics(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate user growth metrics"""
        now = datetime.now()

        # New users in different timeframes
        new_last_day = len(
            [
                u
                for u in users
                if u.get("CreatedDate") and (now - u["CreatedDate"]).days <= 1
            ]
        )
        new_last_week = len(
            [
                u
                for u in users
                if u.get("CreatedDate") and (now - u["CreatedDate"]).days <= 7
            ]
        )
        new_last_month = len(
            [
                u
                for u in users
                if u.get("CreatedDate") and (now - u["CreatedDate"]).days <= 30
            ]
        )

        return {
            "new_users_last_day": new_last_day,
            "new_users_last_week": new_last_week,
            "new_users_last_month": new_last_month,
        }

    def _calculate_login_analytics(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate login analytics"""
        users_with_login = [u for u in users if u.get("LastLoginDate")]

        if not users_with_login:
            return {
                "avg_days_since_last_login": 0,
                "users_with_recent_activity": 0,
                "dormant_users": len(users),
            }

        now = datetime.now()
        days_since_login = [(now - u["LastLoginDate"]).days for u in users_with_login]

        avg_days = sum(days_since_login) / len(days_since_login)
        recent_activity = len([d for d in days_since_login if d <= 7])
        dormant_users = len([d for d in days_since_login if d > 30])

        return {
            "avg_days_since_last_login": round(avg_days, 2),
            "users_with_recent_activity": recent_activity,
            "dormant_users": dormant_users,
        }

    def _calculate_user_relevance(
        self, user: Dict[str, Any], search_query: str
    ) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = search_query.lower()

        # Username match (highest weight)
        username = (user.get("Username") or "").lower()
        if query_lower in username:
            score += 10.0
            if username.startswith(query_lower):
                score += 5.0

        # Email match
        email = (user.get("Email") or "").lower()
        if query_lower in email:
            score += 5.0

        return score

    def _calculate_workload_level(self, task_count: int) -> str:
        """Calculate workload level based on task count"""
        if task_count == 0:
            return "Available"
        elif task_count <= 3:
            return "Light"
        elif task_count <= 7:
            return "Moderate"
        elif task_count <= 12:
            return "Heavy"
        else:
            return "Overloaded"

    def _calculate_performance_score(self, member: Dict[str, Any]) -> float:
        """Calculate performance score for team member"""
        task_count = member.get("TaskCount", 0)
        avg_progress = member.get("AvgProgress", 0)

        if task_count == 0:
            return 0.0

        # Base score from average progress
        score = avg_progress

        # Bonus for having tasks assigned
        if task_count > 0:
            score += min(task_count * 2, 20)  # Max 20 bonus points

        return min(score, 100.0)  # Cap at 100

    def _empty_user_analytics(self) -> Dict[str, Any]:
        """Return empty user analytics structure"""
        return {
            "total_users": 0,
            "active_users": 0,
            "inactive_users": 0,
            "role_distribution": {},
            "activity_metrics": {
                "active_last_day": 0,
                "active_last_week": 0,
                "active_last_month": 0,
                "never_logged_in": 0,
            },
            "growth_metrics": {
                "new_users_last_day": 0,
                "new_users_last_week": 0,
                "new_users_last_month": 0,
            },
            "login_analytics": {
                "avg_days_since_last_login": 0,
                "users_with_recent_activity": 0,
                "dormant_users": 0,
            },
        }


# Global user service instance
_user_service = None


def get_user_service() -> UserService:
    """Get global user service instance"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service


# Export classes and functions
__all__ = ["UserService", "User", "UserRole", "get_user_service"]
