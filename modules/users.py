#!/usr/bin/env python3
"""
modules/users.py
User Management System for SDX Project Manager
Complete user CRUD operations and role management
"""

import streamlit as st
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import re

logger = logging.getLogger(__name__)


class UserManager:
    """Complete user management system with role-based access"""

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_sample_data()

    def _ensure_sample_data(self):
        """Ensure sample users exist for demo"""
        try:
            # Check if users other than admin exist
            user_count = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Username != 'admin'"
            )

            if user_count == 0:
                # Create sample users
                sample_users = [
                    {
                        "username": "john.doe",
                        "password": "password123",
                        "full_name": "John Doe",
                        "email": "john.doe@sdx.com",
                        "role": "Project Manager",
                        "department": "Development",
                        "phone": "081-234-5678",
                    },
                    {
                        "username": "jane.smith",
                        "password": "password123",
                        "full_name": "Jane Smith",
                        "email": "jane.smith@sdx.com",
                        "role": "Developer",
                        "department": "Development",
                        "phone": "081-345-6789",
                    },
                    {
                        "username": "mike.wilson",
                        "password": "password123",
                        "full_name": "Mike Wilson",
                        "email": "mike.wilson@sdx.com",
                        "role": "Designer",
                        "department": "Design",
                        "phone": "081-456-7890",
                    },
                    {
                        "username": "sarah.johnson",
                        "password": "password123",
                        "full_name": "Sarah Johnson",
                        "email": "sarah.johnson@sdx.com",
                        "role": "QA Tester",
                        "department": "Quality Assurance",
                        "phone": "081-567-8901",
                    },
                ]

                for user in sample_users:
                    self.create_user(user, create_by_system=True)

                logger.info("Sample users created")

        except Exception as e:
            logger.error(f"Error ensuring sample user data: {e}")

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {"valid": True, "errors": []}

        if len(password) < 8:
            result["errors"].append("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")

        if not re.search(r"[A-Z]", password):
            result["errors"].append("รหัสผ่านต้องมีตัวอักษรตัวใหญ่อย่างน้อย 1 ตัว")

        if not re.search(r"[a-z]", password):
            result["errors"].append("รหัสผ่านต้องมีตัวอักษรตัวเล็กอย่างน้อย 1 ตัว")

        if not re.search(r"\d", password):
            result["errors"].append("รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")

        if result["errors"]:
            result["valid"] = False

        return result

    def create_user(
        self, user_data: Dict[str, Any], create_by_system: bool = False
    ) -> Optional[int]:
        """Create new user"""
        try:
            # Validate email
            if not self._validate_email(user_data["email"]):
                raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")

            # Check if username exists
            existing_user = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Username = ?",
                (user_data["username"],),
            )

            if existing_user > 0:
                raise ValueError("ชื่อผู้ใช้นี้มีอยู่แล้ว")

            # Check if email exists
            existing_email = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Email = ?", (user_data["email"],)
            )

            if existing_email > 0:
                raise ValueError("อีเมลนี้มีอยู่แล้ว")

            # Validate password (skip for system creation)
            if not create_by_system:
                password_validation = self._validate_password(user_data["password"])
                if not password_validation["valid"]:
                    raise ValueError("; ".join(password_validation["errors"]))

            # Hash password
            hashed_password = self._hash_password(user_data["password"])

            # Insert user
            query = """
                INSERT INTO Users (
                    Username, PasswordHash, FullName, Email, Role, 
                    Department, PhoneNumber, IsActive, CreatedBy
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            created_by = 1 if create_by_system else st.session_state.user["UserID"]

            result = self.db.execute_non_query(
                query,
                (
                    user_data["username"],
                    hashed_password,
                    user_data["full_name"],
                    user_data["email"],
                    user_data["role"],
                    user_data.get("department", ""),
                    user_data.get("phone", ""),
                    True,  # IsActive
                    created_by,
                ),
            )

            if result > 0:
                user_id = self.db.execute_scalar("SELECT @@IDENTITY")
                logger.info(f"User created with ID: {user_id}")
                return user_id

            return None

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def get_all_users(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get all users with optional filters"""
        try:
            base_query = """
                SELECT 
                    u.UserID,
                    u.Username,
                    u.FullName,
                    u.Email,
                    u.Role,
                    u.Department,
                    u.PhoneNumber,
                    u.IsActive,
                    u.LastLoginDate,
                    u.CreatedDate,
                    creator.FullName as CreatedBy,
                    CASE 
                        WHEN u.LastLoginDate >= DATEADD(minute, -30, GETDATE()) THEN 1 
                        ELSE 0 
                    END as IsOnline
                FROM Users u
                LEFT JOIN Users creator ON u.CreatedBy = creator.UserID
                WHERE 1=1
            """

            params = []

            # Apply filters
            if filters:
                if filters.get("role") and filters["role"] != "ทั้งหมด":
                    base_query += " AND u.Role = ?"
                    params.append(filters["role"])

                if filters.get("department") and filters["department"] != "ทั้งหมด":
                    base_query += " AND u.Department = ?"
                    params.append(filters["department"])

                if filters.get("status") == "active":
                    base_query += " AND u.IsActive = 1"
                elif filters.get("status") == "inactive":
                    base_query += " AND u.IsActive = 0"

                if filters.get("search"):
                    base_query += " AND (u.FullName LIKE ? OR u.Email LIKE ? OR u.Username LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term, search_term])

            base_query += " ORDER BY u.CreatedDate DESC"

            return self.db.execute_query(base_query, tuple(params) if params else None)

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            query = """
                SELECT 
                    u.*,
                    creator.FullName as CreatedBy
                FROM Users u
                LEFT JOIN Users creator ON u.CreatedBy = creator.UserID
                WHERE u.UserID = ?
            """

            result = self.db.execute_query(query, (user_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Update user information"""
        try:
            # Validate email
            if not self._validate_email(user_data["email"]):
                raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")

            # Check if email exists for other users
            existing_email = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Email = ? AND UserID != ?",
                (user_data["email"], user_id),
            )

            if existing_email > 0:
                raise ValueError("อีเมลนี้มีอยู่แล้ว")

            query = """
                UPDATE Users 
                SET FullName = ?, Email = ?, Role = ?, Department = ?, 
                    PhoneNumber = ?, IsActive = ?, LastModifiedDate = GETDATE(),
                    LastModifiedBy = ?
                WHERE UserID = ?
            """

            result = self.db.execute_non_query(
                query,
                (
                    user_data["full_name"],
                    user_data["email"],
                    user_data["role"],
                    user_data.get("department", ""),
                    user_data.get("phone", ""),
                    user_data.get("is_active", True),
                    st.session_state.user["UserID"],
                    user_id,
                ),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        try:
            # Get current password hash
            current_hash = self.db.execute_scalar(
                "SELECT PasswordHash FROM Users WHERE UserID = ?", (user_id,)
            )

            if not current_hash:
                raise ValueError("ไม่พบผู้ใช้งาน")

            # Verify current password
            if not bcrypt.checkpw(
                current_password.encode("utf-8"), current_hash.encode("utf-8")
            ):
                raise ValueError("รหัสผ่านปัจจุบันไม่ถูกต้อง")

            # Validate new password
            password_validation = self._validate_password(new_password)
            if not password_validation["valid"]:
                raise ValueError("; ".join(password_validation["errors"]))

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update password
            result = self.db.execute_non_query(
                """
                UPDATE Users 
                SET PasswordHash = ?, LastModifiedDate = GETDATE(),
                    LastModifiedBy = ?
                WHERE UserID = ?
            """,
                (new_hash, st.session_state.user["UserID"], user_id),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            raise

    def reset_password(self, user_id: int, new_password: str) -> bool:
        """Reset user password (admin only)"""
        try:
            # Validate new password
            password_validation = self._validate_password(new_password)
            if not password_validation["valid"]:
                raise ValueError("; ".join(password_validation["errors"]))

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update password
            result = self.db.execute_non_query(
                """
                UPDATE Users 
                SET PasswordHash = ?, LastModifiedDate = GETDATE(),
                    LastModifiedBy = ?
                WHERE UserID = ?
            """,
                (new_hash, st.session_state.user["UserID"], user_id),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error resetting password for user {user_id}: {e}")
            raise

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user (soft delete)"""
        try:
            result = self.db.execute_non_query(
                """
                UPDATE Users 
                SET IsActive = 0, LastModifiedDate = GETDATE(),
                    LastModifiedBy = ?
                WHERE UserID = ?
            """,
                (st.session_state.user["UserID"], user_id),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e}")
            return False

    def activate_user(self, user_id: int) -> bool:
        """Activate user"""
        try:
            result = self.db.execute_non_query(
                """
                UPDATE Users 
                SET IsActive = 1, LastModifiedDate = GETDATE(),
                    LastModifiedBy = ?
                WHERE UserID = ?
            """,
                (st.session_state.user["UserID"], user_id),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error activating user {user_id}: {e}")
            return False

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            stats = {}

            # Total users
            stats["total"] = self.db.execute_scalar("SELECT COUNT(*) FROM Users") or 0

            # Active users
            stats["active"] = (
                self.db.execute_scalar("SELECT COUNT(*) FROM Users WHERE IsActive = 1")
                or 0
            )

            # Inactive users
            stats["inactive"] = (
                self.db.execute_scalar("SELECT COUNT(*) FROM Users WHERE IsActive = 0")
                or 0
            )

            # Online users (logged in within 30 minutes)
            stats["online"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Users 
                WHERE LastLoginDate >= DATEADD(minute, -30, GETDATE())
            """
                )
                or 0
            )

            # Users by role
            role_data = self.db.execute_query(
                """
                SELECT Role, COUNT(*) as Count
                FROM Users 
                WHERE IsActive = 1
                GROUP BY Role
            """
            )
            stats["by_role"] = {row["Role"]: row["Count"] for row in role_data}

            # Users by department
            dept_data = self.db.execute_query(
                """
                SELECT Department, COUNT(*) as Count
                FROM Users 
                WHERE IsActive = 1 AND Department IS NOT NULL AND Department != ''
                GROUP BY Department
            """
            )
            stats["by_department"] = {
                row["Department"]: row["Count"] for row in dept_data
            }

            # New users this month
            stats["new_this_month"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Users 
                WHERE CreatedDate >= DATEADD(month, -1, GETDATE())
            """
                )
                or 0
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}

    def get_available_roles(self) -> List[str]:
        """Get list of available roles"""
        return [
            "Admin",
            "Project Manager",
            "Developer",
            "Designer",
            "QA Tester",
            "Business Analyst",
            "DevOps Engineer",
            "Product Owner",
            "Scrum Master",
            "Team Lead",
        ]

    def get_available_departments(self) -> List[str]:
        """Get list of available departments"""
        return [
            "Development",
            "Design",
            "Quality Assurance",
            "Product Management",
            "DevOps",
            "Business Analysis",
            "Marketing",
            "Sales",
            "Human Resources",
            "Finance",
            "Operations",
        ]

    def search_users(self, search_term: str) -> List[Dict[str, Any]]:
        """Search users"""
        try:
            query = """
                SELECT 
                    UserID,
                    Username,
                    FullName,
                    Email,
                    Role,
                    Department
                FROM Users
                WHERE IsActive = 1 
                AND (FullName LIKE ? OR Email LIKE ? OR Username LIKE ?)
                ORDER BY FullName
            """

            search_pattern = f"%{search_term}%"
            return self.db.execute_query(
                query, (search_pattern, search_pattern, search_pattern)
            )

        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []

    def get_user_activity_log(
        self, user_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get user activity log"""
        try:
            # This is a simplified version - in a real system you'd have proper audit logging
            activities = []

            # Get recent projects created/modified
            projects = self.db.execute_query(
                """
                SELECT 'Project' as Type, ProjectName as Item, 
                       'Created' as Action, CreatedDate as Date
                FROM Projects 
                WHERE CreatedBy = ? AND CreatedDate >= DATEADD(day, -?, GETDATE())
                UNION ALL
                SELECT 'Project' as Type, ProjectName as Item,
                       'Modified' as Action, LastModifiedDate as Date
                FROM Projects 
                WHERE LastModifiedBy = ? AND LastModifiedDate >= DATEADD(day, -?, GETDATE())
                ORDER BY Date DESC
            """,
                (user_id, days, user_id, days),
            )

            activities.extend(projects)

            # Get recent tasks created/modified
            tasks = self.db.execute_query(
                """
                SELECT 'Task' as Type, TaskTitle as Item,
                       'Created' as Action, CreatedDate as Date
                FROM Tasks 
                WHERE CreatedBy = ? AND CreatedDate >= DATEADD(day, -?, GETDATE())
                UNION ALL
                SELECT 'Task' as Type, TaskTitle as Item,
                       'Modified' as Action, LastModifiedDate as Date
                FROM Tasks 
                WHERE LastModifiedBy = ? AND LastModifiedDate >= DATEADD(day, -?, GETDATE())
                ORDER BY Date DESC
            """,
                (user_id, days, user_id, days),
            )

            activities.extend(tasks)

            # Sort by date
            activities.sort(
                key=lambda x: x["Date"] if x["Date"] else datetime.min, reverse=True
            )

            return activities[:50]  # Limit to 50 recent activities

        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return []

    def export_users_data(self) -> pd.DataFrame:
        """Export users data to DataFrame"""
        try:
            query = """
                SELECT 
                    u.UserID as 'รหัสผู้ใช้',
                    u.Username as 'ชื่อผู้ใช้',
                    u.FullName as 'ชื่อ-นามสกุล',
                    u.Email as 'อีเมล',
                    u.Role as 'บทบาท',
                    u.Department as 'แผนก',
                    u.PhoneNumber as 'เบอร์โทร',
                    CASE WHEN u.IsActive = 1 THEN 'Active' ELSE 'Inactive' END as 'สถานะ',
                    u.LastLoginDate as 'เข้าสู่ระบบล่าสุด',
                    u.CreatedDate as 'วันที่สร้าง'
                FROM Users u
                ORDER BY u.CreatedDate DESC
            """

            data = self.db.execute_query(query)
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error exporting users: {e}")
            return pd.DataFrame()

    def get_users_for_assignment(self) -> List[Dict[str, Any]]:
        """Get active users for task/project assignment"""
        try:
            query = """
                SELECT 
                    UserID,
                    FullName,
                    Role,
                    Department
                FROM Users
                WHERE IsActive = 1
                ORDER BY FullName
            """

            return self.db.execute_query(query)

        except Exception as e:
            logger.error(f"Error getting users for assignment: {e}")
            return []

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            result = self.db.execute_non_query(
                """
                UPDATE Users 
                SET LastLoginDate = GETDATE()
                WHERE UserID = ?
            """,
                (user_id,),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
