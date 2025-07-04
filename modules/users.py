#!/usr/bin/env python3
"""
modules/users.py
User Management for DENSO Project Manager Pro
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import logging
import re

from utils.error_handler import safe_execute, handle_error, validate_input
from utils.ui_components import UIComponents

logger = logging.getLogger(__name__)


class UserManager:
    """User management functionality"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.ui = UIComponents()

    def get_all_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            query = """
            SELECT UserID, Username, Email, FirstName, LastName, Role, 
                   Department, IsActive, CreatedDate, LastLoginDate,
                   FailedLoginAttempts, IsLocked
            FROM Users
            """

            if not include_inactive:
                query += " WHERE IsActive = 1"

            query += " ORDER BY FirstName, LastName"

            return self.db.execute_query(query)

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            query = """
            SELECT UserID, Username, Email, FirstName, LastName, Role,
                   Department, IsActive, CreatedDate, LastLoginDate,
                   FailedLoginAttempts, IsLocked, MustChangePassword
            FROM Users 
            WHERE UserID = ?
            """

            result = self.db.execute_query(query, (user_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get users by role"""
        try:
            query = """
            SELECT UserID, Username, Email, FirstName, LastName, Role,
                   Department, IsActive, CreatedDate, LastLoginDate
            FROM Users 
            WHERE Role = ? AND IsActive = 1
            ORDER BY FirstName, LastName
            """

            return self.db.execute_query(query, (role,))

        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            return []

    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create new user"""
        try:
            # Validate required fields
            required_fields = ["Username", "Email", "FirstName", "LastName", "Role"]
            for field in required_fields:
                if not user_data.get(field):
                    st.error(f"❌ กรุณากรอก {field}")
                    return False

            # Validate email format
            if not self._validate_email(user_data["Email"]):
                st.error("❌ รูปแบบอีเมลไม่ถูกต้อง")
                return False

            # Check for duplicate username/email
            if self._check_duplicate_user(user_data["Username"], user_data["Email"]):
                st.error("❌ ชื่อผู้ใช้หรืออีเมลนี้มีอยู่แล้ว")
                return False

            # Generate temporary password
            temp_password = self._generate_temp_password()

            # Hash password
            from modules.auth import AuthenticationManager

            auth_manager = AuthenticationManager(self.db)
            password_hash = auth_manager._hash_password(temp_password)

            query = """
            INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName,
                             Role, Department, MustChangePassword)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """

            params = (
                user_data["Username"],
                password_hash,
                user_data["Email"],
                user_data["FirstName"],
                user_data["LastName"],
                user_data["Role"],
                user_data.get("Department", ""),
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                st.success(f"✅ สร้างผู้ใช้สำเร็จ รหัสผ่านชั่วคราว: {temp_password}")
                return True
            else:
                st.error("❌ ไม่สามารถสร้างผู้ใช้ได้")
                return False

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Update existing user"""
        try:
            # Validate required fields
            required_fields = ["Username", "Email", "FirstName", "LastName", "Role"]
            for field in required_fields:
                if not user_data.get(field):
                    st.error(f"❌ กรุณากรอก {field}")
                    return False

            # Validate email format
            if not self._validate_email(user_data["Email"]):
                st.error("❌ รูปแบบอีเมลไม่ถูกต้อง")
                return False

            # Check for duplicate username/email (excluding current user)
            if self._check_duplicate_user(
                user_data["Username"], user_data["Email"], exclude_user_id=user_id
            ):
                st.error("❌ ชื่อผู้ใช้หรืออีเมลนี้มีอยู่แล้ว")
                return False

            query = """
            UPDATE Users 
            SET Username = ?, Email = ?, FirstName = ?, LastName = ?,
                Role = ?, Department = ?, IsActive = ?
            WHERE UserID = ?
            """

            params = (
                user_data["Username"],
                user_data["Email"],
                user_data["FirstName"],
                user_data["LastName"],
                user_data["Role"],
                user_data.get("Department", ""),
                user_data.get("IsActive", True),
                user_id,
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                st.success("✅ อัพเดทผู้ใช้สำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถอัพเดทผู้ใช้ได้")
                return False

        except Exception as e:
            logger.error(f"Error updating user: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user (soft delete)"""
        try:
            query = "UPDATE Users SET IsActive = 0 WHERE UserID = ?"
            rows_affected = self.db.execute_non_query(query, (user_id,))

            if rows_affected > 0:
                st.success("✅ ปิดใช้งานผู้ใช้สำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถปิดใช้งานผู้ใช้ได้")
                return False

        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def activate_user(self, user_id: int) -> bool:
        """Activate user"""
        try:
            query = "UPDATE Users SET IsActive = 1 WHERE UserID = ?"
            rows_affected = self.db.execute_non_query(query, (user_id,))

            if rows_affected > 0:
                st.success("✅ เปิดใช้งานผู้ใช้สำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถเปิดใช้งานผู้ใช้ได้")
                return False

        except Exception as e:
            logger.error(f"Error activating user: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def reset_user_password(self, user_id: int) -> bool:
        """Reset user password"""
        try:
            # Generate new temporary password
            temp_password = self._generate_temp_password()

            # Hash password
            from modules.auth import AuthenticationManager

            auth_manager = AuthenticationManager(self.db)
            password_hash = auth_manager._hash_password(temp_password)

            query = """
            UPDATE Users 
            SET PasswordHash = ?, MustChangePassword = 1, IsLocked = 0,
                FailedLoginAttempts = 0, LastFailedLogin = NULL
            WHERE UserID = ?
            """

            rows_affected = self.db.execute_non_query(query, (password_hash, user_id))

            if rows_affected > 0:
                st.success(f"✅ รีเซ็ตรหัสผ่านสำเร็จ รหัสผ่านใหม่: {temp_password}")
                return True
            else:
                st.error("❌ ไม่สามารถรีเซ็ตรหัสผ่านได้")
                return False

        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def unlock_user(self, user_id: int) -> bool:
        """Unlock user account"""
        try:
            query = """
            UPDATE Users 
            SET IsLocked = 0, FailedLoginAttempts = 0, LastFailedLogin = NULL
            WHERE UserID = ?
            """

            rows_affected = self.db.execute_non_query(query, (user_id,))

            if rows_affected > 0:
                st.success("✅ ปลดล็อคผู้ใช้สำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถปลดล็อคผู้ใช้ได้")
                return False

        except Exception as e:
            logger.error(f"Error unlocking user: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN IsActive = 1 THEN 1 ELSE 0 END) as active_users,
                SUM(CASE WHEN IsLocked = 1 THEN 1 ELSE 0 END) as locked_users,
                SUM(CASE WHEN LastLoginDate > DATEADD(day, -30, GETDATE()) THEN 1 ELSE 0 END) as recent_login_users
            FROM Users
            """

            result = self.db.execute_query(query)
            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}

    def get_users_by_department(self) -> Dict[str, int]:
        """Get user count by department"""
        try:
            query = """
            SELECT Department, COUNT(*) as count
            FROM Users 
            WHERE IsActive = 1 AND Department IS NOT NULL AND Department != ''
            GROUP BY Department
            ORDER BY count DESC
            """

            result = self.db.execute_query(query)
            return {row["Department"]: row["count"] for row in result}

        except Exception as e:
            logger.error(f"Error getting users by department: {e}")
            return {}

    def get_users_by_role_stats(self) -> Dict[str, int]:
        """Get user count by role"""
        try:
            query = """
            SELECT Role, COUNT(*) as count
            FROM Users 
            WHERE IsActive = 1
            GROUP BY Role
            ORDER BY count DESC
            """

            result = self.db.execute_query(query)
            return {row["Role"]: row["count"] for row in result}

        except Exception as e:
            logger.error(f"Error getting users by role: {e}")
            return {}

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _check_duplicate_user(
        self, username: str, email: str, exclude_user_id: int = None
    ) -> bool:
        """Check for duplicate username or email"""
        try:
            query = (
                "SELECT COUNT(*) as count FROM Users WHERE (Username = ? OR Email = ?)"
            )
            params = [username, email]

            if exclude_user_id:
                query += " AND UserID != ?"
                params.append(exclude_user_id)

            result = self.db.execute_query(query, tuple(params))
            return result[0]["count"] > 0 if result else False

        except Exception as e:
            logger.error(f"Error checking duplicate user: {e}")
            return False

    def _generate_temp_password(self) -> str:
        """Generate temporary password"""
        import secrets
        import string

        # Generate password with letters, digits, and special characters
        length = 12
        characters = string.ascii_letters + string.digits + "!@#$%"
        return "".join(secrets.choice(characters) for _ in range(length))


def show_users_page(user_manager: UserManager):
    """Show users management page"""
    ui = UIComponents()

    # Page header
    ui.render_page_header("👥 จัดการผู้ใช้", "สร้าง แก้ไข และจัดการผู้ใช้ในระบบ", "👥")

    # Check permissions
    user_data = st.session_state.user_data
    if user_data["Role"] not in ["Admin", "Project Manager"]:
        st.error("❌ คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        return

    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔍 ตัวกรอง")

        include_inactive = st.checkbox("แสดงผู้ใช้ที่ปิดใช้งาน")

        role_filter = st.selectbox(
            "บทบาท",
            options=[
                "ทั้งหมด",
                "Admin",
                "Project Manager",
                "Team Lead",
                "Developer",
                "User",
                "Viewer",
            ],
        )

        department_filter = st.text_input("แผนก", placeholder="กรอกชื่อแผนก...")

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 รายการผู้ใช้", "➕ สร้างผู้ใช้ใหม่", "📊 สถิติผู้ใช้", "🔐 จัดการความปลอดภัย"]
    )

    with tab1:
        show_users_list(user_manager, include_inactive, role_filter, department_filter)

    with tab2:
        if user_data["Role"] == "Admin":
            show_create_user_form(user_manager)
        else:
            st.error("❌ เฉพาะ Admin เท่านั้นที่สามารถสร้างผู้ใช้ได้")

    with tab3:
        show_user_statistics(user_manager)

    with tab4:
        if user_data["Role"] == "Admin":
            show_security_management(user_manager)
        else:
            st.error("❌ เฉพาะ Admin เท่านั้นที่สามารถจัดการความปลอดภัยได้")


def show_users_list(
    user_manager: UserManager,
    include_inactive: bool,
    role_filter: str,
    department_filter: str,
):
    """Show users list with actions"""
    ui = UIComponents()

    # Get users
    users = safe_execute(
        user_manager.get_all_users, include_inactive, default_return=[]
    )

    if not users:
        st.info("ไม่มีผู้ใช้ในระบบ")
        return

    # Apply filters
    filtered_users = users

    if role_filter != "ทั้งหมด":
        filtered_users = [u for u in filtered_users if u["Role"] == role_filter]

    if department_filter:
        filtered_users = [
            u
            for u in filtered_users
            if department_filter.lower() in (u.get("Department", "") or "").lower()
        ]

    # Search functionality
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 ค้นหาผู้ใช้", placeholder="ชื่อ, อีเมล, ชื่อผู้ใช้...")

    # Filter by search term
    if search_term:
        search_lower = search_term.lower()
        filtered_users = [
            u
            for u in filtered_users
            if (
                search_lower in u["FirstName"].lower()
                or search_lower in u["LastName"].lower()
                or search_lower in u["Username"].lower()
                or search_lower in u["Email"].lower()
            )
        ]

    # Display summary
    st.markdown(f"**พบ {len(filtered_users)} ผู้ใช้**")

    # Display users
    for user in filtered_users:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                # User info
                st.markdown(f"### {user['FirstName']} {user['LastName']}")
                st.markdown(f"**ชื่อผู้ใช้:** {user['Username']}")
                st.markdown(f"**อีเมล:** {user['Email']}")
                st.markdown(f"**แผนก:** {user.get('Department', 'N/A')}")

                # Last login
                if user["LastLoginDate"]:
                    last_login = user["LastLoginDate"].strftime("%d/%m/%Y %H:%M")
                    st.markdown(f"**เข้าระบบล่าสุด:** {last_login}")
                else:
                    st.markdown("**เข้าระบบล่าสุด:** ยังไม่เคยเข้าใช้")

            with col2:
                st.markdown("**บทบาท**")
                role_colors = {
                    "Admin": "#dc3545",
                    "Project Manager": "#fd7e14",
                    "Team Lead": "#6f42c1",
                    "Developer": "#20c997",
                    "User": "#0dcaf0",
                    "Viewer": "#6c757d",
                }
                role_color = role_colors.get(user["Role"], "#6c757d")
                st.markdown(
                    f"""
                <span style="
                    background: {role_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 15px;
                    font-size: 0.8rem;
                    font-weight: bold;
                ">
                    {user['Role']}
                </span>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown("**สถานะ**")
                if user["IsActive"]:
                    if user.get("IsLocked"):
                        st.markdown(
                            ui.render_status_badge("Locked"), unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            ui.render_status_badge("Active"), unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        ui.render_status_badge("Inactive"), unsafe_allow_html=True
                    )

            with col3:
                st.markdown("**สถิติ**")
                if user.get("FailedLoginAttempts", 0) > 0:
                    st.markdown(f"ล็อกอินผิด: {user['FailedLoginAttempts']} ครั้ง")

                # Account age
                if user["CreatedDate"]:
                    account_age = (datetime.now() - user["CreatedDate"]).days
                    st.markdown(f"อายุบัญชี: {account_age} วัน")

            with col4:
                user_data = st.session_state.user_data
                can_edit = user_data["Role"] == "Admin"

                if (
                    can_edit and user["UserID"] != user_data["UserID"]
                ):  # Can't edit own account
                    if st.button("✏️ แก้ไข", key=f"edit_user_{user['UserID']}"):
                        st.session_state.edit_user_id = user["UserID"]

                    if user["IsActive"]:
                        if st.button("🔒 ปิดใช้งาน", key=f"deactivate_{user['UserID']}"):
                            if ui.render_confirmation_dialog(
                                f"ต้องการปิดใช้งานบัญชี '{user['Username']}' หรือไม่?",
                                f"deactivate_user_{user['UserID']}",
                            ):
                                user_manager.deactivate_user(user["UserID"])
                                st.rerun()
                    else:
                        if st.button("✅ เปิดใช้งาน", key=f"activate_{user['UserID']}"):
                            user_manager.activate_user(user["UserID"])
                            st.rerun()

                    if user.get("IsLocked"):
                        if st.button("🔓 ปลดล็อค", key=f"unlock_{user['UserID']}"):
                            user_manager.unlock_user(user["UserID"])
                            st.rerun()

                    if st.button("🔑 รีเซ็ตรหัสผ่าน", key=f"reset_pwd_{user['UserID']}"):
                        if ui.render_confirmation_dialog(
                            f"ต้องการรีเซ็ตรหัสผ่านของ '{user['Username']}' หรือไม่?",
                            f"reset_password_{user['UserID']}",
                        ):
                            user_manager.reset_user_password(user["UserID"])
                            st.rerun()

                elif user["UserID"] == user_data["UserID"]:
                    st.info("บัญชีของคุณ")

            st.markdown("---")

    # Handle edit user
    if "edit_user_id" in st.session_state:
        show_edit_user_modal(user_manager, st.session_state.edit_user_id)


def show_create_user_form(user_manager: UserManager):
    """Show create user form"""
    with st.form("create_user_form"):
        st.subheader("➕ สร้างผู้ใช้ใหม่")

        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("ชื่อผู้ใช้ *", placeholder="username")
            first_name = st.text_input("ชื่อ *", placeholder="ชื่อจริง")
            role = st.selectbox(
                "บทบาท *",
                options=[
                    "User",
                    "Developer",
                    "Team Lead",
                    "Project Manager",
                    "Admin",
                    "Viewer",
                ],
            )

        with col2:
            email = st.text_input("อีเมล *", placeholder="user@denso.com")
            last_name = st.text_input("นามสกุล *", placeholder="นามสกุล")
            department = st.text_input("แผนก", placeholder="IT, Engineering, etc.")

        if st.form_submit_button("✅ สร้างผู้ใช้", type="primary"):
            if username and email and first_name and last_name and role:
                user_data = {
                    "Username": username,
                    "Email": email,
                    "FirstName": first_name,
                    "LastName": last_name,
                    "Role": role,
                    "Department": department,
                }

                if user_manager.create_user(user_data):
                    st.rerun()
            else:
                st.error("❌ กรุณากรอกข้อมูลที่จำเป็น (*)")


def show_edit_user_modal(user_manager: UserManager, user_id: int):
    """Show edit user modal"""
    user = safe_execute(user_manager.get_user_by_id, user_id, default_return=None)

    if not user:
        st.error("ไม่พบผู้ใช้")
        return

    with st.expander(f"✏️ แก้ไขผู้ใช้: {user['Username']}", expanded=True):
        with st.form(f"edit_user_form_{user_id}"):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input("ชื่อผู้ใช้", value=user["Username"])
                first_name = st.text_input("ชื่อ", value=user["FirstName"])
                role = st.selectbox(
                    "บทบาท",
                    options=[
                        "User",
                        "Developer",
                        "Team Lead",
                        "Project Manager",
                        "Admin",
                        "Viewer",
                    ],
                    index=[
                        "User",
                        "Developer",
                        "Team Lead",
                        "Project Manager",
                        "Admin",
                        "Viewer",
                    ].index(user["Role"]),
                )
                is_active = st.checkbox("เปิดใช้งาน", value=user["IsActive"])

            with col2:
                email = st.text_input("อีเมล", value=user["Email"])
                last_name = st.text_input("นามสกุล", value=user["LastName"])
                department = st.text_input("แผนก", value=user.get("Department", ""))

            col1, col2 = st.columns(2)

            with col1:
                if st.form_submit_button("✅ บันทึกการแก้ไข", type="primary"):
                    updated_data = {
                        "Username": username,
                        "Email": email,
                        "FirstName": first_name,
                        "LastName": last_name,
                        "Role": role,
                        "Department": department,
                        "IsActive": is_active,
                    }

                    if user_manager.update_user(user_id, updated_data):
                        del st.session_state.edit_user_id
                        st.rerun()

            with col2:
                if st.form_submit_button("❌ ยกเลิก"):
                    del st.session_state.edit_user_id
                    st.rerun()


def show_user_statistics(user_manager: UserManager):
    """Show user statistics and charts"""
    ui = UIComponents()

    st.subheader("📊 สถิติผู้ใช้")

    # Get user statistics
    stats = safe_execute(user_manager.get_user_statistics, default_return={})

    if not stats:
        st.info("ไม่มีข้อมูลสถิติ")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_users = stats.get("total_users", 0)
        st.metric("ผู้ใช้ทั้งหมด", total_users)

    with col2:
        active_users = stats.get("active_users", 0)
        active_rate = (active_users / total_users * 100) if total_users > 0 else 0
        st.metric("ผู้ใช้ที่ใช้งานอยู่", active_users, f"{active_rate:.1f}%")

    with col3:
        locked_users = stats.get("locked_users", 0)
        st.metric(
            "ผู้ใช้ที่ถูกล็อค",
            locked_users,
            delta=f"-{locked_users}" if locked_users > 0 else None,
        )

    with col4:
        recent_users = stats.get("recent_login_users", 0)
        recent_rate = (recent_users / active_users * 100) if active_users > 0 else 0
        st.metric("เข้าใช้ภายใน 30 วัน", recent_users, f"{recent_rate:.1f}%")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("ผู้ใช้ตามบทบาท")
        role_stats = safe_execute(
            user_manager.get_users_by_role_stats, default_return={}
        )

        if role_stats:
            roles = list(role_stats.keys())
            counts = list(role_stats.values())

            colors = {
                "Admin": "#dc3545",
                "Project Manager": "#fd7e14",
                "Team Lead": "#6f42c1",
                "Developer": "#20c997",
                "User": "#0dcaf0",
                "Viewer": "#6c757d",
            }

            fig = px.pie(values=counts, names=roles, title="การกระจายตามบทบาท")
            # Apply custom colors if available
            fig.update_traces(
                marker=dict(colors=[colors.get(role, "#6c757d") for role in roles])
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("ผู้ใช้ตามแผนก")
        dept_stats = safe_execute(
            user_manager.get_users_by_department, default_return={}
        )

        if dept_stats:
            departments = list(dept_stats.keys())
            counts = list(dept_stats.values())

            fig = px.bar(x=departments, y=counts, title="จำนวนผู้ใช้ในแต่ละแผนก")
            fig.update_layout(xaxis_title="แผนก", yaxis_title="จำนวนผู้ใช้")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลแผนก")

    # User activity timeline
    st.subheader("กิจกรรมผู้ใช้")
    users = safe_execute(user_manager.get_all_users, True, default_return=[])

    if users:
        df = pd.DataFrame(users)

        # Recent registrations
        if "CreatedDate" in df.columns:
            df["CreatedDate"] = pd.to_datetime(df["CreatedDate"])
            recent_df = df[
                df["CreatedDate"] >= pd.Timestamp.now() - pd.Timedelta(days=30)
            ]

            if len(recent_df) > 0:
                daily_registrations = recent_df.groupby(
                    recent_df["CreatedDate"].dt.date
                ).size()

                fig = px.line(
                    x=daily_registrations.index,
                    y=daily_registrations.values,
                    title="การสมัครผู้ใช้ใหม่ใน 30 วันที่ผ่านมา",
                )
                fig.update_layout(xaxis_title="วันที่", yaxis_title="จำนวนผู้ใช้ใหม่")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีผู้ใช้ใหม่ใน 30 วันที่ผ่านมา")


def show_security_management(user_manager: UserManager):
    """Show security management options"""
    ui = UIComponents()

    st.subheader("🔐 จัดการความปลอดภัย")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔒 บัญชีที่ถูกล็อค")

        # Get locked users
        users = safe_execute(user_manager.get_all_users, True, default_return=[])
        locked_users = [u for u in users if u.get("IsLocked")]

        if locked_users:
            for user in locked_users:
                with st.container():
                    st.markdown(
                        f"**{user['FirstName']} {user['LastName']}** ({user['Username']})"
                    )
                    st.markdown(f"ล็อกอินผิด: {user.get('FailedLoginAttempts', 0)} ครั้ง")

                    if st.button(f"🔓 ปลดล็อค", key=f"unlock_security_{user['UserID']}"):
                        user_manager.unlock_user(user["UserID"])
                        st.rerun()

                    st.markdown("---")
        else:
            st.info("ไม่มีบัญชีที่ถูกล็อค")

    with col2:
        st.markdown("### 🔄 การรีเซ็ตรหัสผ่านหมู่")

        st.markdown("เลือกผู้ใช้ที่ต้องการรีเซ็ตรหัสผ่าน:")

        # Get all active users
        active_users = [u for u in users if u["IsActive"] and not u.get("IsLocked")]
        user_options = [
            f"{u['FirstName']} {u['LastName']} ({u['Username']})" for u in active_users
        ]

        selected_users = st.multiselect("เลือกผู้ใช้", options=user_options)

        if selected_users and st.button("🔑 รีเซ็ตรหัสผ่านที่เลือก", type="primary"):
            if ui.render_confirmation_dialog(
                f"ต้องการรีเซ็ตรหัสผ่านของผู้ใช้ {len(selected_users)} คน หรือไม่?",
                "bulk_reset_password",
            ):
                success_count = 0
                for selected_user in selected_users:
                    # Extract username from selection
                    username = selected_user.split("(")[1].split(")")[0]
                    user = next(
                        (u for u in active_users if u["Username"] == username), None
                    )

                    if user and user_manager.reset_user_password(user["UserID"]):
                        success_count += 1

                st.success(
                    f"✅ รีเซ็ตรหัสผ่านสำเร็จ {success_count}/{len(selected_users)} คน"
                )
                st.rerun()

    st.markdown("---")

    # Security settings
    st.markdown("### ⚙️ การตั้งค่าความปลอดภัย")

    with st.expander("การตั้งค่าขั้นสูง"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**นโยบายรหัสผ่าน**")
            st.markdown("- ความยาวขั้นต่ำ: 8 ตัวอักษร")
            st.markdown("- ต้องมีตัวพิมพ์ใหญ่และเล็ก")
            st.markdown("- ต้องมีตัวเลข")
            st.markdown("- ต้องมีอักขระพิเศษ")

        with col2:
            st.markdown("**การล็อคบัญชี**")
            st.markdown("- ล็อกอินผิด: สูงสุด 5 ครั้ง")
            st.markdown("- ระยะเวลาล็อค: 15 นาที")
            st.markdown("- ปลดล็อคอัตโนมัติเมื่อหมดเวลา")

        if st.button("🔄 รีเซ็ตการตั้งค่าความปลอดภัย"):
            st.warning("ฟีเจอร์นี้อยู่ระหว่างการพัฒนา")
