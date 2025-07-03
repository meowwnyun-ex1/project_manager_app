"""
Team Management Module
โมดูลจัดการทีมงานแบบสมบูรณ์
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
import hashlib
import random
import string

logger = logging.getLogger(__name__)


class TeamManager:
    """Team and user management"""

    def __init__(self, db_manager):
        self.db = db_manager

    def render_page(self):
        """Render team management page"""
        st.title("👥 จัดการทีมงาน")

        # Control buttons
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.subheader("สมาชิกทีม")

        with col2:
            if st.button("👤 เพิ่มสมาชิก", use_container_width=True):
                st.session_state.show_new_member = True

        with col3:
            if st.button("📊 รายงาน", use_container_width=True):
                st.session_state.show_team_report = True

        # New member form
        if st.session_state.get("show_new_member", False):
            self._render_new_member_form()

        # Team report
        if st.session_state.get("show_team_report", False):
            self._render_team_report()

        # Load and display team members
        users = self.get_all_users()

        if users:
            self._render_team_overview(users)
            self._render_team_list(users)
        else:
            st.info("👥 ยังไม่มีสมาชิกทีม")

    def _render_new_member_form(self):
        """Render new team member form"""
        with st.expander("เพิ่มสมาชิกทีมใหม่", expanded=True):
            with st.form("new_member_form"):
                col1, col2 = st.columns(2)

                with col1:
                    username = st.text_input("ชื่อผู้ใช้ *", placeholder="username")
                    first_name = st.text_input("ชื่อ *", placeholder="ชื่อจริง")
                    email = st.text_input("อีเมล *", placeholder="email@company.com")
                    phone = st.text_input("เบอร์โทร", placeholder="หมายเลขโทรศัพท์")

                with col2:
                    password = st.text_input(
                        "รหัสผ่าน *", type="password", placeholder="รหัสผ่านชั่วคราว"
                    )
                    last_name = st.text_input("นามสกุล *", placeholder="นามสกุล")
                    department = st.selectbox(
                        "แผนก",
                        [
                            "Engineering",
                            "Marketing",
                            "Sales",
                            "HR",
                            "Finance",
                            "Operations",
                            "IT",
                            "Quality",
                            "R&D",
                            "Management",
                            "Other",
                        ],
                    )
                    role = st.selectbox("บทบาท", ["User", "Manager", "Admin"])

                # Additional fields
                col3, col4 = st.columns(2)
                with col3:
                    position = st.text_input("ตำแหน่งงาน", placeholder="ตำแหน่ง")
                    hire_date = st.date_input("วันที่เริ่มงาน", value=datetime.now().date())

                with col4:
                    salary = st.number_input("เงินเดือน", min_value=0, value=0, step=1000)
                    manager_id = st.selectbox("ผู้จัดการ", self._get_manager_options())

                col_submit, col_cancel = st.columns(2)

                with col_submit:
                    submitted = st.form_submit_button(
                        "➕ เพิ่มสมาชิก", use_container_width=True
                    )

                with col_cancel:
                    cancel = st.form_submit_button("❌ ยกเลิก", use_container_width=True)

                if submitted:
                    if not all([username, first_name, last_name, email, password]):
                        st.error("❌ กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน!")
                    else:
                        success = self.add_user(
                            {
                                "username": username,
                                "password": password,
                                "first_name": first_name,
                                "last_name": last_name,
                                "email": email,
                                "phone": phone,
                                "department": department,
                                "role": role,
                                "position": position,
                                "hire_date": hire_date,
                                "salary": salary,
                                "manager_id": (
                                    manager_id if manager_id != "ไม่มี" else None
                                ),
                            }
                        )

                        if success:
                            st.success("✅ เพิ่มสมาชิกเรียบร้อยแล้ว!")
                            st.session_state.show_new_member = False
                            st.rerun()
                        else:
                            st.error("❌ เกิดข้อผิดพลาดในการเพิ่มสมาชิก")

                if cancel:
                    st.session_state.show_new_member = False
                    st.rerun()

    def _render_team_overview(self, users: List[Dict]):
        """Render team overview stats"""
        st.subheader("📊 ภาพรวมทีม")

        # Calculate stats
        total_users = len(users)
        active_users = len([u for u in users if u.get("IsActive", True)])
        departments = list(set([u.get("Department", "Unknown") for u in users]))
        roles = list(set([u.get("Role", "User") for u in users]))

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("👥 สมาชิกทั้งหมด", total_users)

        with col2:
            st.metric("✅ ใช้งานอยู่", active_users)

        with col3:
            st.metric("🏢 แผนก", len(departments))

        with col4:
            st.metric("👤 บทบาท", len(roles))

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            # Department distribution
            dept_data = pd.DataFrame(users)
            if not dept_data.empty and "Department" in dept_data.columns:
                dept_counts = dept_data["Department"].value_counts()
                fig = px.pie(
                    values=dept_counts.values,
                    names=dept_counts.index,
                    title="การกระจายตามแผนก",
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Role distribution
            if not dept_data.empty and "Role" in dept_data.columns:
                role_counts = dept_data["Role"].value_counts()
                fig = px.bar(
                    x=role_counts.index, y=role_counts.values, title="การกระจายตามบทบาท"
                )
                st.plotly_chart(fig, use_container_width=True)

    def _render_team_list(self, users: List[Dict]):
        """Render team members list"""
        st.subheader("📋 รายชื่อสมาชิก")

        # Search and filter
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input("🔍 ค้นหา", placeholder="ชื่อ, อีเมล, แผนก...")

        with col2:
            dept_filter = st.selectbox(
                "แผนก",
                ["ทั้งหมด"] + list(set([u.get("Department", "Unknown") for u in users])),
            )

        with col3:
            role_filter = st.selectbox(
                "บทบาท", ["ทั้งหมด"] + list(set([u.get("Role", "User") for u in users]))
            )

        # Filter users
        filtered_users = users

        if search_term:
            filtered_users = [
                u
                for u in filtered_users
                if search_term.lower()
                in f"{u.get('FirstName', '')} {u.get('LastName', '')} {u.get('Email', '')} {u.get('Department', '')}".lower()
            ]

        if dept_filter != "ทั้งหมด":
            filtered_users = [
                u for u in filtered_users if u.get("Department") == dept_filter
            ]

        if role_filter != "ทั้งหมด":
            filtered_users = [u for u in filtered_users if u.get("Role") == role_filter]

        # Display users
        for user in filtered_users:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

                with col1:
                    status_icon = "✅" if user.get("IsActive", True) else "❌"
                    st.write(
                        f"{status_icon} **{user.get('FirstName', '')} {user.get('LastName', '')}**"
                    )
                    st.caption(f"@{user.get('Username', '')} • {user.get('Email', '')}")

                with col2:
                    st.write(f"🏢 {user.get('Department', 'N/A')}")
                    st.caption(f"📍 {user.get('Position', 'N/A')}")

                with col3:
                    st.write(f"👤 {user.get('Role', 'User')}")
                    if user.get("LastLogin"):
                        last_login = user["LastLogin"]
                        if isinstance(last_login, str):
                            last_login = datetime.fromisoformat(
                                last_login.replace("Z", "+00:00")
                            )
                        st.caption(f"🕐 {last_login.strftime('%d/%m/%Y')}")

                with col4:
                    if user.get("HireDate"):
                        hire_date = user["HireDate"]
                        if isinstance(hire_date, str):
                            hire_date = datetime.fromisoformat(hire_date).date()
                        st.write(f"📅 {hire_date.strftime('%d/%m/%Y')}")

                    if user.get("Phone"):
                        st.caption(f"📱 {user['Phone']}")

                with col5:
                    if st.button("✏️", key=f"edit_{user.get('UserID')}", help="แก้ไข"):
                        st.session_state.edit_user_id = user.get("UserID")
                        st.session_state.show_edit_user = True

                st.divider()

        if not filtered_users:
            st.info("🔍 ไม่พบสมาชิกที่ตรงกับเงื่อนไขการค้นหา")

        # Edit user modal
        if st.session_state.get("show_edit_user", False):
            self._render_edit_user_modal()

    def _render_edit_user_modal(self):
        """Render edit user modal"""
        user_id = st.session_state.get("edit_user_id")
        if not user_id:
            return

        user = self.get_user_by_id(user_id)
        if not user:
            st.error("ไม่พบข้อมูลผู้ใช้")
            return

        with st.expander(
            f"แก้ไขข้อมูล: {user.get('FirstName')} {user.get('LastName')}", expanded=True
        ):
            with st.form("edit_user_form"):
                col1, col2 = st.columns(2)

                with col1:
                    first_name = st.text_input("ชื่อ", value=user.get("FirstName", ""))
                    email = st.text_input("อีเมล", value=user.get("Email", ""))
                    department = st.selectbox(
                        "แผนก",
                        [
                            "Engineering",
                            "Marketing",
                            "Sales",
                            "HR",
                            "Finance",
                            "Operations",
                            "IT",
                            "Quality",
                            "R&D",
                            "Management",
                            "Other",
                        ],
                        index=(
                            [
                                "Engineering",
                                "Marketing",
                                "Sales",
                                "HR",
                                "Finance",
                                "Operations",
                                "IT",
                                "Quality",
                                "R&D",
                                "Management",
                                "Other",
                            ].index(user.get("Department", "Other"))
                            if user.get("Department")
                            in [
                                "Engineering",
                                "Marketing",
                                "Sales",
                                "HR",
                                "Finance",
                                "Operations",
                                "IT",
                                "Quality",
                                "R&D",
                                "Management",
                                "Other",
                            ]
                            else 10
                        ),
                    )
                    is_active = st.checkbox("ใช้งานอยู่", value=user.get("IsActive", True))

                with col2:
                    last_name = st.text_input("นามสกุล", value=user.get("LastName", ""))
                    phone = st.text_input("เบอร์โทร", value=user.get("Phone", ""))
                    role = st.selectbox(
                        "บทบาท",
                        ["User", "Manager", "Admin"],
                        index=(
                            ["User", "Manager", "Admin"].index(user.get("Role", "User"))
                            if user.get("Role") in ["User", "Manager", "Admin"]
                            else 0
                        ),
                    )
                    position = st.text_input("ตำแหน่ง", value=user.get("Position", ""))

                col_save, col_cancel, col_delete = st.columns(3)

                with col_save:
                    save = st.form_submit_button("💾 บันทึก", use_container_width=True)

                with col_cancel:
                    cancel = st.form_submit_button("❌ ยกเลิก", use_container_width=True)

                with col_delete:
                    delete = st.form_submit_button("🗑️ ลบ", use_container_width=True)

                if save:
                    update_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "department": department,
                        "role": role,
                        "position": position,
                        "is_active": is_active,
                    }

                    if self.update_user(user_id, update_data):
                        st.success("✅ อัปเดตข้อมูลเรียบร้อยแล้ว!")
                        st.session_state.show_edit_user = False
                        st.rerun()
                    else:
                        st.error("❌ เกิดข้อผิดพลาดในการอัปเดต")

                if cancel:
                    st.session_state.show_edit_user = False
                    st.rerun()

                if delete:
                    if st.session_state.get("confirm_delete", False):
                        if self.delete_user(user_id):
                            st.success("✅ ลบผู้ใช้เรียบร้อยแล้ว!")
                            st.session_state.show_edit_user = False
                            st.session_state.confirm_delete = False
                            st.rerun()
                        else:
                            st.error("❌ เกิดข้อผิดพลาดในการลบ")
                    else:
                        st.session_state.confirm_delete = True
                        st.warning("⚠️ คลิกลบอีกครั้งเพื่อยืนยัน")

    def _render_team_report(self):
        """Render team analytics report"""
        with st.expander("📊 รายงานทีมงาน", expanded=True):
            users = self.get_all_users()

            if not users:
                st.info("ไม่มีข้อมูลสำหรับสร้างรายงาน")
                return

            df = pd.DataFrame(users)

            # Team growth over time
            if "CreatedDate" in df.columns:
                df["CreatedDate"] = pd.to_datetime(df["CreatedDate"])
                growth_data = df.groupby(df["CreatedDate"].dt.date).size().cumsum()

                fig = px.line(
                    x=growth_data.index,
                    y=growth_data.values,
                    title="การเติบโตของทีมงาน",
                    labels={"x": "วันที่", "y": "จำนวนสมาชิก"},
                )
                st.plotly_chart(fig, use_container_width=True)

            # Department analysis
            col1, col2 = st.columns(2)

            with col1:
                if "Department" in df.columns:
                    dept_stats = df["Department"].value_counts()
                    st.subheader("สถิติตามแผนก")
                    for dept, count in dept_stats.items():
                        st.write(f"• **{dept}**: {count} คน")

            with col2:
                if "Role" in df.columns:
                    role_stats = df["Role"].value_counts()
                    st.subheader("สถิติตามบทบาท")
                    for role, count in role_stats.items():
                        st.write(f"• **{role}**: {count} คน")

            # Export button
            if st.button("📁 ส่งออกรายงาน", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ ดาวน์โหลด CSV",
                    data=csv,
                    file_name=f"team_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )

            if st.button("❌ ปิดรายงาน", use_container_width=True):
                st.session_state.show_team_report = False
                st.rerun()

    def get_all_users(self) -> List[Dict]:
        """Get all users from database"""
        try:
            query = """
            SELECT 
                UserID, Username, FirstName, LastName, Email, Phone,
                Department, Role, Position, HireDate, Salary, ManagerID,
                IsActive, LastLogin, CreatedDate, UpdatedDate
            FROM Users
            ORDER BY FirstName, LastName
            """
            results = self.db.fetch_all(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            query = """
            SELECT 
                UserID, Username, FirstName, LastName, Email, Phone,
                Department, Role, Position, HireDate, Salary, ManagerID,
                IsActive, LastLogin, CreatedDate, UpdatedDate
            FROM Users
            WHERE UserID = ?
            """
            result = self.db.fetch_one(query, (user_id,))
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    def add_user(self, user_data: Dict) -> bool:
        """Add new user to database"""
        try:
            # Check if username or email already exists
            check_query = """
            SELECT COUNT(*) as count FROM Users 
            WHERE Username = ? OR Email = ?
            """
            existing = self.db.fetch_one(
                check_query, (user_data["username"], user_data["email"])
            )

            if existing and existing["count"] > 0:
                st.error("❌ ชื่อผู้ใช้หรืออีเมลนี้มีอยู่ในระบบแล้ว")
                return False

            # Hash password
            password_hash = self._hash_password(user_data["password"])

            # Insert new user
            insert_query = """
            INSERT INTO Users (
                Username, PasswordHash, FirstName, LastName, Email, Phone,
                Department, Role, Position, HireDate, Salary, ManagerID,
                IsActive, CreatedDate, UpdatedDate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """

            values = (
                user_data["username"],
                password_hash,
                user_data["first_name"],
                user_data["last_name"],
                user_data["email"],
                user_data.get("phone", ""),
                user_data["department"],
                user_data["role"],
                user_data.get("position", ""),
                user_data.get("hire_date", datetime.now().date()),
                user_data.get("salary", 0),
                user_data.get("manager_id"),
                datetime.now(),
                datetime.now(),
            )

            self.db.execute_query(insert_query, values)
            logger.info(f"User {user_data['username']} added successfully")
            return True

        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False

    def update_user(self, user_id: int, user_data: Dict) -> bool:
        """Update user information"""
        try:
            update_query = """
            UPDATE Users SET
                FirstName = ?, LastName = ?, Email = ?, Phone = ?,
                Department = ?, Role = ?, Position = ?, IsActive = ?,
                UpdatedDate = ?
            WHERE UserID = ?
            """

            values = (
                user_data["first_name"],
                user_data["last_name"],
                user_data["email"],
                user_data.get("phone", ""),
                user_data["department"],
                user_data["role"],
                user_data.get("position", ""),
                user_data.get("is_active", True),
                datetime.now(),
                user_id,
            )

            self.db.execute_query(update_query, values)
            logger.info(f"User {user_id} updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete by setting IsActive = False)"""
        try:
            # Soft delete - just deactivate the user
            update_query = """
            UPDATE Users SET
                IsActive = 0,
                UpdatedDate = ?
            WHERE UserID = ?
            """

            self.db.execute_query(update_query, (datetime.now(), user_id))
            logger.info(f"User {user_id} deactivated successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            stats = {}

            # Total users
            total_query = "SELECT COUNT(*) as count FROM Users"
            total_result = self.db.fetch_one(total_query)
            stats["total_users"] = total_result["count"] if total_result else 0

            # Active users
            active_query = "SELECT COUNT(*) as count FROM Users WHERE IsActive = 1"
            active_result = self.db.fetch_one(active_query)
            stats["active_users"] = active_result["count"] if active_result else 0

            # Users by department
            dept_query = """
            SELECT Department, COUNT(*) as count 
            FROM Users 
            WHERE IsActive = 1 
            GROUP BY Department
            """
            dept_results = self.db.fetch_all(dept_query)
            stats["departments"] = (
                {row["Department"]: row["count"] for row in dept_results}
                if dept_results
                else {}
            )

            # Users by role
            role_query = """
            SELECT Role, COUNT(*) as count 
            FROM Users 
            WHERE IsActive = 1 
            GROUP BY Role
            """
            role_results = self.db.fetch_all(role_query)
            stats["roles"] = (
                {row["Role"]: row["count"] for row in role_results}
                if role_results
                else {}
            )

            # Recent logins (last 30 days)
            recent_query = """
            SELECT COUNT(*) as count 
            FROM Users 
            WHERE LastLogin >= ? AND IsActive = 1
            """
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_result = self.db.fetch_one(recent_query, (thirty_days_ago,))
            stats["recent_logins"] = recent_result["count"] if recent_result else 0

            return stats

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}

    def get_team_performance_metrics(self) -> Dict[str, Any]:
        """Get team performance metrics"""
        try:
            metrics = {}

            # Task completion rate by user
            task_query = """
            SELECT 
                u.FirstName + ' ' + u.LastName as FullName,
                COUNT(t.TaskID) as TotalTasks,
                SUM(CASE WHEN t.Status = 'Completed' THEN 1 ELSE 0 END) as CompletedTasks
            FROM Users u
            LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
            WHERE u.IsActive = 1
            GROUP BY u.UserID, u.FirstName, u.LastName
            """
            task_results = self.db.fetch_all(task_query)

            user_performance = []
            for row in task_results:
                total = row["TotalTasks"]
                completed = row["CompletedTasks"]
                completion_rate = (completed / total * 100) if total > 0 else 0

                user_performance.append(
                    {
                        "name": row["FullName"],
                        "total_tasks": total,
                        "completed_tasks": completed,
                        "completion_rate": completion_rate,
                    }
                )

            metrics["user_performance"] = user_performance

            # Department productivity
            dept_query = """
            SELECT 
                u.Department,
                COUNT(t.TaskID) as TotalTasks,
                SUM(CASE WHEN t.Status = 'Completed' THEN 1 ELSE 0 END) as CompletedTasks,
                AVG(DATEDIFF(day, t.CreatedDate, t.CompletedDate)) as AvgCompletionDays
            FROM Users u
            LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
            WHERE u.IsActive = 1
            GROUP BY u.Department
            """
            dept_results = self.db.fetch_all(dept_query)

            dept_productivity = []
            for row in dept_results:
                total = row["TotalTasks"]
                completed = row["CompletedTasks"]
                completion_rate = (completed / total * 100) if total > 0 else 0
                avg_days = row["AvgCompletionDays"] or 0

                dept_productivity.append(
                    {
                        "department": row["Department"],
                        "total_tasks": total,
                        "completed_tasks": completed,
                        "completion_rate": completion_rate,
                        "avg_completion_days": avg_days,
                    }
                )

            metrics["department_productivity"] = dept_productivity

            return metrics

        except Exception as e:
            logger.error(f"Error getting team performance metrics: {e}")
            return {}

    def _get_manager_options(self) -> List[str]:
        """Get list of potential managers"""
        try:
            query = """
            SELECT CONCAT(FirstName, ' ', LastName) as FullName
            FROM Users 
            WHERE Role IN ('Manager', 'Admin') AND IsActive = 1
            ORDER BY FirstName, LastName
            """
            results = self.db.fetch_all(query)
            managers = [row["FullName"] for row in results] if results else []
            return ["ไม่มี"] + managers
        except Exception as e:
            logger.error(f"Error getting managers: {e}")
            return ["ไม่มี"]

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_random_password(self, length: int = 12) -> str:
        """Generate random password"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(random.choice(characters) for _ in range(length))

    def reset_user_password(
        self, user_id: int, new_password: str = None
    ) -> tuple[bool, str]:
        """Reset user password"""
        try:
            if not new_password:
                new_password = self._generate_random_password()

            password_hash = self._hash_password(new_password)

            update_query = """
            UPDATE Users SET
                PasswordHash = ?,
                UpdatedDate = ?,
                FailedLoginAttempts = 0,
                IsLocked = 0
            WHERE UserID = ?
            """

            self.db.execute_query(
                update_query, (password_hash, datetime.now(), user_id)
            )
            logger.info(f"Password reset for user {user_id}")
            return True, new_password

        except Exception as e:
            logger.error(f"Error resetting password for user {user_id}: {e}")
            return False, ""

    def export_team_data(self, format_type: str = "csv") -> str:
        """Export team data in specified format"""
        try:
            users = self.get_all_users()

            if not users:
                return ""

            df = pd.DataFrame(users)

            # Remove sensitive columns
            sensitive_cols = ["PasswordHash", "Salary"]
            for col in sensitive_cols:
                if col in df.columns:
                    df = df.drop(columns=[col])

            if format_type.lower() == "csv":
                return df.to_csv(index=False)
            elif format_type.lower() == "json":
                return df.to_json(orient="records", indent=2)
            else:
                return df.to_string(index=False)

        except Exception as e:
            logger.error(f"Error exporting team data: {e}")
            return ""
