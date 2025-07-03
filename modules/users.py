"""
modules/users.py
User management functionality
"""

import streamlit as st
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re

from utils.error_handler import handle_database_errors, safe_execute
from utils.performance_monitor import monitor_performance, cache_result

logger = logging.getLogger(__name__)


class UserManager:
    """Enhanced user management class"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.roles = [
            "Admin",
            "Project Manager",
            "Team Lead",
            "Developer",
            "User",
            "Viewer",
        ]
        self.departments = [
            "วิศวกรรม",
            "ผลิต",
            "คุณภาพ",
            "ขาย",
            "การตลาด",
            "HR",
            "IT",
            "การเงิน",
            "บริหาร",
            "อื่นๆ",
        ]

    @handle_database_errors
    @monitor_performance("get_all_users")
    @cache_result(ttl_minutes=5)
    def get_all_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all users with enhanced information"""
        base_query = """
        SELECT 
            u.UserID,
            u.Username,
            u.Email,
            u.FirstName,
            u.LastName,
            u.Role,
            u.Department,
            u.Phone,
            u.IsActive,
            u.CreatedDate,
            u.LastLoginDate,
            u.LastModifiedDate,
            (SELECT COUNT(*) FROM Projects WHERE CreatedBy = u.UserID) as ProjectsCreated,
            (SELECT COUNT(*) FROM Tasks WHERE AssignedTo = u.UserID) as TasksAssigned,
            (SELECT COUNT(*) FROM Tasks WHERE AssignedTo = u.UserID AND Status = 'Done') as TasksCompleted,
            (SELECT SUM(ActualHours) FROM Tasks WHERE AssignedTo = u.UserID) as TotalHours
        FROM Users u
        """

        if not include_inactive:
            base_query += " WHERE u.IsActive = 1"

        base_query += " ORDER BY u.FirstName, u.LastName"

        users = self.db_manager.execute_query(base_query)

        # Calculate additional metrics
        for user in users:
            user["FullName"] = f"{user['FirstName']} {user['LastName']}"
            user["TaskCompletionRate"] = self._calculate_completion_rate(
                user.get("TasksCompleted", 0), user.get("TasksAssigned", 0)
            )
            user["AverageHoursPerTask"] = self._calculate_avg_hours(
                user.get("TotalHours", 0), user.get("TasksCompleted", 0)
            )
            user["LastLoginFormatted"] = self._format_last_login(
                user.get("LastLoginDate")
            )

        return users

    @handle_database_errors
    @monitor_performance("create_user")
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

            # Validate email format
            if not self._validate_email(user_data["email"]):
                logger.error("Invalid email format")
                return False

            # Validate password strength
            if not self._validate_password_strength(user_data["password"]):
                logger.error("Password does not meet requirements")
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
            password_hash = bcrypt.hashpw(
                user_data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

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
                self._clear_user_cache()

            return result

        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return False

    @handle_database_errors
    @monitor_performance("update_user")
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Update existing user"""
        try:
            # Validate email format if provided
            if user_data.get("email") and not self._validate_email(user_data["email"]):
                logger.error("Invalid email format")
                return False

            # Check for duplicate username/email (excluding current user)
            if user_data.get("username") or user_data.get("email"):
                check_query = "SELECT UserID FROM Users WHERE (Username = ? OR Email = ?) AND UserID != ?"
                existing_user = self.db_manager.execute_query(
                    check_query,
                    (
                        user_data.get("username", ""),
                        user_data.get("email", ""),
                        user_id,
                    ),
                )

                if existing_user:
                    logger.error("Username or email already exists")
                    return False

            # Build update query dynamically
            update_fields = []
            params = []

            for field, column in [
                ("username", "Username"),
                ("email", "Email"),
                ("first_name", "FirstName"),
                ("last_name", "LastName"),
                ("role", "Role"),
                ("department", "Department"),
                ("phone", "Phone"),
            ]:
                if field in user_data:
                    update_fields.append(f"{column} = ?")
                    params.append(user_data[field])

            if not update_fields:
                return True  # Nothing to update

            # Add LastModifiedDate
            update_fields.append("LastModifiedDate = GETDATE()")
            params.append(user_id)

            query = f"UPDATE Users SET {', '.join(update_fields)} WHERE UserID = ?"

            result = self.db_manager.execute_non_query(query, tuple(params))

            if result:
                logger.info(f"User updated successfully: ID {user_id}")
                self._clear_user_cache()

            return result

        except Exception as e:
            logger.error(f"User update failed: {str(e)}")
            return False

    @handle_database_errors
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID with detailed information"""
        query = """
        SELECT 
            u.UserID,
            u.Username,
            u.Email,
            u.FirstName,
            u.LastName,
            u.Role,
            u.Department,
            u.Phone,
            u.IsActive,
            u.CreatedDate,
            u.LastLoginDate,
            (SELECT COUNT(*) FROM Projects WHERE CreatedBy = u.UserID) as ProjectsCreated,
            (SELECT COUNT(*) FROM Tasks WHERE AssignedTo = u.UserID) as TasksAssigned,
            (SELECT COUNT(*) FROM Tasks WHERE AssignedTo = u.UserID AND Status = 'Done') as TasksCompleted
        FROM Users u
        WHERE u.UserID = ?
        """

        users = self.db_manager.execute_query(query, (user_id,))

        if users:
            user = users[0]
            user["FullName"] = f"{user['FirstName']} {user['LastName']}"
            user["TaskCompletionRate"] = self._calculate_completion_rate(
                user.get("TasksCompleted", 0), user.get("TasksAssigned", 0)
            )
            return user

        return None

    @handle_database_errors
    def update_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """Update user password with validation"""
        try:
            # Get current password hash
            user_data = self.db_manager.execute_query(
                "SELECT PasswordHash FROM Users WHERE UserID = ?", (user_id,)
            )

            if not user_data:
                logger.error(f"User not found: {user_id}")
                return False

            # Verify current password
            if not bcrypt.checkpw(
                current_password.encode("utf-8"),
                user_data[0]["PasswordHash"].encode("utf-8"),
            ):
                logger.error("Current password is incorrect")
                return False

            # Validate new password
            if not self._validate_password_strength(new_password):
                logger.error("New password does not meet requirements")
                return False

            # Hash new password
            new_password_hash = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

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

    @handle_database_errors
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """Reset user password (admin function)"""
        try:
            # Validate new password
            if not self._validate_password_strength(new_password):
                logger.error("New password does not meet requirements")
                return False

            # Hash new password
            password_hash = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # Update password
            result = self.db_manager.execute_non_query(
                "UPDATE Users SET PasswordHash = ?, LastModifiedDate = GETDATE() WHERE UserID = ?",
                (password_hash, user_id),
            )

            if result:
                logger.info(f"Password reset for user ID: {user_id}")

            return result

        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            return False

    @handle_database_errors
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        try:
            result = self.db_manager.execute_non_query(
                "UPDATE Users SET IsActive = 0, LastModifiedDate = GETDATE() WHERE UserID = ?",
                (user_id,),
            )

            if result:
                logger.info(f"User deactivated: ID={user_id}")
                self._clear_user_cache()

            return result

        except Exception as e:
            logger.error(f"User deactivation failed: {str(e)}")
            return False

    @handle_database_errors
    def activate_user(self, user_id: int) -> bool:
        """Activate user account"""
        try:
            result = self.db_manager.execute_non_query(
                "UPDATE Users SET IsActive = 1, LastModifiedDate = GETDATE() WHERE UserID = ?",
                (user_id,),
            )

            if result:
                logger.info(f"User activated: ID={user_id}")
                self._clear_user_cache()

            return result

        except Exception as e:
            logger.error(f"User activation failed: {str(e)}")
            return False

    @handle_database_errors
    def delete_user(self, user_id: int) -> bool:
        """Delete user (only if no associated data)"""
        try:
            # Check for associated data
            associated_data = self.db_manager.execute_query(
                """
                SELECT 
                    (SELECT COUNT(*) FROM Projects WHERE CreatedBy = ?) as projects,
                    (SELECT COUNT(*) FROM Tasks WHERE AssignedTo = ? OR CreatedBy = ?) as tasks
            """,
                (user_id, user_id, user_id),
            )

            if associated_data and (
                associated_data[0]["projects"] > 0 or associated_data[0]["tasks"] > 0
            ):
                logger.warning(f"Cannot delete user {user_id}: has associated data")
                return False

            # Safe to delete
            result = self.db_manager.execute_non_query(
                "DELETE FROM Users WHERE UserID = ?", (user_id,)
            )

            if result:
                logger.info(f"User deleted: ID={user_id}")
                self._clear_user_cache()

            return result

        except Exception as e:
            logger.error(f"User deletion failed: {str(e)}")
            return False

    @handle_database_errors
    def search_users(
        self, search_term: str, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search users with filters"""
        try:
            base_query = """
            SELECT 
                u.UserID, u.Username, u.Email, u.FirstName, u.LastName,
                u.Role, u.Department, u.Phone, u.IsActive, u.CreatedDate, u.LastLoginDate
            FROM Users u
            WHERE 1=1
            """

            params = []

            # Add search term filter
            if search_term:
                base_query += " AND (u.FirstName LIKE ? OR u.LastName LIKE ? OR u.Username LIKE ? OR u.Email LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend(
                    [search_pattern, search_pattern, search_pattern, search_pattern]
                )

            # Add filters
            if filters:
                if filters.get("role"):
                    base_query += " AND u.Role = ?"
                    params.append(filters["role"])

                if filters.get("department"):
                    base_query += " AND u.Department = ?"
                    params.append(filters["department"])

                if filters.get("is_active") is not None:
                    base_query += " AND u.IsActive = ?"
                    params.append(1 if filters["is_active"] else 0)

            base_query += " ORDER BY u.FirstName, u.LastName"

            return self.db_manager.execute_query(base_query, tuple(params))

        except Exception as e:
            logger.error(f"User search failed: {str(e)}")
            return []

    @handle_database_errors
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        stats = {}

        try:
            # Basic counts
            stats["total_users"] = (
                self.db_manager.execute_scalar("SELECT COUNT(*) FROM Users") or 0
            )
            stats["active_users"] = (
                self.db_manager.execute_scalar(
                    "SELECT COUNT(*) FROM Users WHERE IsActive = 1"
                )
                or 0
            )
            stats["inactive_users"] = stats["total_users"] - stats["active_users"]

            # Role distribution
            role_query = """
            SELECT Role, COUNT(*) as count
            FROM Users
            WHERE IsActive = 1
            GROUP BY Role
            ORDER BY count DESC
            """
            stats["role_distribution"] = self.db_manager.execute_query(role_query)

            # Department distribution
            dept_query = """
            SELECT Department, COUNT(*) as count
            FROM Users
            WHERE IsActive = 1 AND Department IS NOT NULL AND Department != ''
            GROUP BY Department
            ORDER BY count DESC
            """
            stats["department_distribution"] = self.db_manager.execute_query(dept_query)

            # Recent activity
            recent_logins = (
                self.db_manager.execute_scalar(
                    """
                SELECT COUNT(*) FROM Users 
                WHERE LastLoginDate >= DATEADD(day, -7, GETDATE())
            """
                )
                or 0
            )
            stats["recent_logins"] = recent_logins

            # New users this month
            new_users = (
                self.db_manager.execute_scalar(
                    """
                SELECT COUNT(*) FROM Users 
                WHERE CreatedDate >= DATEADD(month, -1, GETDATE())
            """
                )
                or 0
            )
            stats["new_users_this_month"] = new_users

        except Exception as e:
            logger.error(f"Failed to get user statistics: {str(e)}")

        return stats

    @handle_database_errors
    def get_user_activity_log(
        self, user_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get user activity log"""
        # This would require an activity log table
        # For now, return basic info from existing tables
        query = """
        SELECT 
            'Project Created' as activity_type,
            ProjectName as activity_description,
            CreatedDate as activity_date
        FROM Projects
        WHERE CreatedBy = ? AND CreatedDate >= DATEADD(day, -?, GETDATE())
        
        UNION ALL
        
        SELECT 
            'Task Created' as activity_type,
            TaskName as activity_description,
            CreatedDate as activity_date
        FROM Tasks
        WHERE CreatedBy = ? AND CreatedDate >= DATEADD(day, -?, GETDATE())
        
        UNION ALL
        
        SELECT 
            'Task Completed' as activity_type,
            TaskName as activity_description,
            CompletedDate as activity_date
        FROM Tasks
        WHERE AssignedTo = ? AND Status = 'Done' AND CompletedDate >= DATEADD(day, -?, GETDATE())
        
        ORDER BY activity_date DESC
        """

        return self.db_manager.execute_query(
            query, (user_id, days, user_id, days, user_id, days)
        )

    def get_available_roles(self) -> List[str]:
        """Get available user roles"""
        return self.roles.copy()

    def get_available_departments(self) -> List[str]:
        """Get available departments"""
        return self.departments.copy()

    def export_user_data(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Export user data for reporting"""
        try:
            query = """
            SELECT 
                u.UserID,
                u.Username,
                u.Email,
                u.FirstName,
                u.LastName,
                u.Role,
                u.Department,
                u.Phone,
                u.IsActive,
                u.CreatedDate,
                u.LastLoginDate,
                (SELECT COUNT(*) FROM Projects WHERE CreatedBy = u.UserID) as ProjectsCreated,
                (SELECT COUNT(*) FROM Tasks WHERE AssignedTo = u.UserID) as TasksAssigned,
                (SELECT COUNT(*) FROM Tasks WHERE AssignedTo = u.UserID AND Status = 'Done') as TasksCompleted,
                (SELECT SUM(ActualHours) FROM Tasks WHERE AssignedTo = u.UserID) as TotalHours
            FROM Users u
            """

            if not include_inactive:
                query += " WHERE u.IsActive = 1"

            query += " ORDER BY u.FirstName, u.LastName"

            return self.db_manager.execute_query(query)

        except Exception as e:
            logger.error(f"User export failed: {str(e)}")
            return []

    def bulk_update_users(self, user_updates: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk update multiple users"""
        results = {"success": 0, "failed": 0}

        for update in user_updates:
            user_id = update.get("user_id")
            user_data = update.get("data", {})

            if user_id and user_data:
                if self.update_user(user_id, user_data):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            else:
                results["failed"] += 1

        return results

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False

        # Check for uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return has_upper and has_lower and has_digit and has_special

    def _calculate_completion_rate(self, completed: int, total: int) -> float:
        """Calculate task completion rate"""
        if total == 0:
            return 0.0
        return round((completed / total) * 100, 1)

    def _calculate_avg_hours(self, total_hours: float, completed_tasks: int) -> float:
        """Calculate average hours per completed task"""
        if completed_tasks == 0:
            return 0.0
        return round(total_hours / completed_tasks, 1)

    def _format_last_login(self, last_login_date) -> str:
        """Format last login date"""
        if not last_login_date:
            return "ไม่เคยเข้าสู่ระบบ"

        try:
            if isinstance(last_login_date, str):
                last_login_date = datetime.strptime(
                    last_login_date, "%Y-%m-%d %H:%M:%S"
                )

            now = datetime.now()
            diff = now - last_login_date

            if diff.days == 0:
                return "วันนี้"
            elif diff.days == 1:
                return "เมื่อวาน"
            elif diff.days < 7:
                return f"{diff.days} วันที่แล้ว"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} สัปดาห์ที่แล้ว"
            else:
                return last_login_date.strftime("%d/%m/%Y")

        except:
            return "ไม่ทราบ"

    def _clear_user_cache(self):
        """Clear user-related cache"""
        try:
            from utils.performance_monitor import get_cache_manager

            cache_manager = get_cache_manager()

            # Clear user-related cache keys
            cache_keys_to_clear = [
                key for key in cache_manager.cache.keys() if "user" in key.lower()
            ]

            for key in cache_keys_to_clear:
                cache_manager.delete(key)

        except Exception as e:
            logger.warning(f"Failed to clear user cache: {str(e)}")
