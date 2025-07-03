"""
pages/users.py
User management page
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import logging
import re

from modules.ui_components import (
    FormBuilder,
    CardComponent,
    DataTable,
    StatusBadge,
    NotificationManager,
    ModernModal,
)
from modules.auth import require_role, get_current_user, UserRole
from modules.users import UserManager
from utils.error_handler import handle_streamlit_errors, safe_execute
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


class UsersPage:
    """User management page class"""

    def __init__(self, user_manager, auth_manager):
        self.user_manager = user_manager
        self.auth_manager = auth_manager

    @handle_streamlit_errors()
    @monitor_performance("users_page_render")
    @require_role(["Admin", "Project Manager"])
    def show(self):
        """Show user management page"""
        st.title("👥 การจัดการผู้ใช้")

        # Get current user
        current_user = get_current_user()
        if not current_user:
            st.error("กรุณาเข้าสู่ระบบ")
            return

        # Action buttons
        self._show_action_buttons()

        # Show create user form if requested
        if st.session_state.get("show_new_user", False):
            self._show_create_user_form()

        # Show edit user form if requested
        if st.session_state.get("edit_user_id"):
            self._show_edit_user_form()

        # Main content
        self._show_users_content()

    def _show_action_buttons(self):
        """Show action buttons"""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if st.button("➕ เพิ่มผู้ใช้ใหม่", use_container_width=True, type="primary"):
                st.session_state.show_new_user = True
                st.rerun()

        with col2:
            if st.button("🔄 รีเฟรช", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        with col3:
            if st.button("📊 สถิติผู้ใช้", use_container_width=True):
                self._show_user_statistics()

    def _show_create_user_form(self):
        """Show create user form"""
        with st.expander("เพิ่มผู้ใช้ใหม่", expanded=True):
            with st.form("create_user_form", clear_on_submit=False):
                st.markdown("### 📝 ข้อมูลผู้ใช้")

                col1, col2 = st.columns(2)

                with col1:
                    username = st.text_input(
                        "ชื่อผู้ใช้ *",
                        placeholder="ตัวอักษรภาษาอังกฤษและตัวเลขเท่านั้น",
                        help="ชื่อผู้ใช้จะใช้สำหรับเข้าสู่ระบบ",
                    )

                    first_name = st.text_input("ชื่อ *", placeholder="ชื่อจริง")

                    email = st.text_input(
                        "อีเมล *",
                        placeholder="user@denso.com",
                        help="อีเมลต้องเป็นรูปแบบที่ถูกต้อง",
                    )

                    role = st.selectbox(
                        "บทบาท *",
                        [role.value for role in UserRole],
                        help="บทบาทจะกำหนดสิทธิ์การเข้าถึงระบบ",
                    )

                with col2:
                    password = st.text_input(
                        "รหัสผ่าน *", type="password", help="รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
                    )

                    last_name = st.text_input("นามสกุล *", placeholder="นามสกุล")

                    phone = st.text_input("เบอร์โทรศัพท์", placeholder="08X-XXX-XXXX")

                    department = st.selectbox(
                        "แผนก",
                        [
                            "IT",
                            "Engineering",
                            "Production",
                            "Quality",
                            "Sales",
                            "Marketing",
                            "HR",
                            "Finance",
                            "Management",
                        ],
                    )

                # Additional fields
                st.markdown("### 🔧 การตั้งค่าเพิ่มเติม")

                col1, col2, col3 = st.columns(3)

                with col1:
                    is_active = st.checkbox("เปิดใช้งานบัญชี", value=True)

                with col2:
                    send_welcome_email = st.checkbox("ส่งอีเมลต้อนรับ", value=True)

                with col3:
                    require_password_change = st.checkbox(
                        "บังคับเปลี่ยนรหัสผ่านเมื่อเข้าสู่ระบบครั้งแรก", value=True
                    )

                # Form buttons
                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    if st.form_submit_button(
                        "💾 สร้างผู้ใช้", use_container_width=True, type="primary"
                    ):
                        if self._validate_user_form(
                            username, email, password, first_name, last_name
                        ):
                            self._create_user(
                                {
                                    "username": username,
                                    "password": password,
                                    "email": email,
                                    "first_name": first_name,
                                    "last_name": last_name,
                                    "phone": phone,
                                    "role": role,
                                    "department": department,
                                    "is_active": is_active,
                                    "send_welcome_email": send_welcome_email,
                                    "require_password_change": require_password_change,
                                }
                            )

                with col2:
                    if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                        st.session_state.show_new_user = False
                        st.rerun()

    def _show_users_content(self):
        """Show main users content"""
        # Search and filters
        self._show_user_filters()

        # Users list
        users = self._get_filtered_users()

        if users:
            self._show_users_table(users)
        else:
            st.info("🔍 ไม่พบผู้ใช้ที่ตรงกับเงื่อนไขการค้นหา")

    def _show_user_filters(self):
        """Show user filters"""
        with st.expander("🔍 ตัวกรองและการค้นหา", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                search_term = st.text_input("🔍 ค้นหา", placeholder="ชื่อ, อีเมล, ชื่อผู้ใช้...")
                st.session_state.user_search = search_term

            with col2:
                role_filter = st.multiselect("บทบาท", [role.value for role in UserRole])
                st.session_state.user_role_filter = role_filter

            with col3:
                department_filter = st.multiselect(
                    "แผนก",
                    [
                        "IT",
                        "Engineering",
                        "Production",
                        "Quality",
                        "Sales",
                        "Marketing",
                        "HR",
                        "Finance",
                        "Management",
                    ],
                )
                st.session_state.user_department_filter = department_filter

            with col4:
                status_filter = st.selectbox("สถานะ", ["ทั้งหมด", "เปิดใช้งาน", "ปิดใช้งาน"])
                st.session_state.user_status_filter = status_filter

    def _show_users_table(self, users: List[Dict]):
        """Show users table"""
        st.subheader(f"👥 ผู้ใช้ทั้งหมด ({len(users)} คน)")

        # Create dataframe for better display
        import pandas as pd

        df_data = []
        for user in users:
            df_data.append(
                {
                    "ID": user["UserID"],
                    "ชื่อผู้ใช้": user["Username"],
                    "ชื่อ-นามสกุล": f"{user['FirstName']} {user['LastName']}",
                    "อีเมล": user["Email"],
                    "บทบาท": user["Role"],
                    "แผนก": user.get("Department", "-"),
                    "สถานะ": "🟢 เปิดใช้งาน" if user["IsActive"] else "🔴 ปิดใช้งาน",
                    "เข้าสู่ระบบล่าสุด": (
                        user.get("LastLoginDate", "ยังไม่เคย")[:10]
                        if user.get("LastLoginDate")
                        else "ยังไม่เคย"
                    ),
                }
            )

        df = pd.DataFrame(df_data)

        # Display table with actions
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        # Handle row selection
        if event.selection and event.selection.rows:
            selected_row = event.selection.rows[0]
            selected_user_id = df.iloc[selected_row]["ID"]
            st.session_state.selected_user_id = selected_user_id

            # Show action buttons for selected user
            self._show_user_actions(selected_user_id, users)

    def _show_user_actions(self, user_id: int, users: List[Dict]):
        """Show actions for selected user"""
        selected_user = next((u for u in users if u["UserID"] == user_id), None)
        if not selected_user:
            return

        st.markdown(
            f"**การดำเนินการสำหรับ: {selected_user['FirstName']} {selected_user['LastName']}**"
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("✏️ แก้ไข", key=f"edit_{user_id}"):
                st.session_state.edit_user_id = user_id
                st.rerun()

        with col2:
            if st.button("🔑 รีเซ็ตรหัสผ่าน", key=f"reset_{user_id}"):
                self._reset_user_password(user_id)

        with col3:
            status_text = "🔴 ปิดใช้งาน" if selected_user["IsActive"] else "🟢 เปิดใช้งาน"
            if st.button(status_text, key=f"toggle_{user_id}"):
                self._toggle_user_status(user_id, not selected_user["IsActive"])

        with col4:
            if st.button("📊 ดูสถิติ", key=f"stats_{user_id}"):
                self._show_user_detailed_stats(user_id)

        with col5:
            current_user = get_current_user()
            if current_user["Role"] == "Admin" and user_id != current_user["UserID"]:
                if st.button("🗑️ ลบ", key=f"delete_{user_id}"):
                    self._show_delete_confirmation(user_id)

    def _show_user_statistics(self):
        """Show user statistics"""
        with st.expander("📊 สถิติผู้ใช้", expanded=True):
            stats = self._get_user_statistics()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("ผู้ใช้ทั้งหมด", stats.get("total_users", 0))

            with col2:
                st.metric("ผู้ใช้ที่เปิดใช้งาน", stats.get("active_users", 0))

            with col3:
                st.metric("ผู้ใช้ที่เข้าสู่ระบบในสัปดาห์นี้", stats.get("weekly_active", 0))

            with col4:
                st.metric("ผู้ใช้ใหม่เดือนนี้", stats.get("new_this_month", 0))

    def _validate_user_form(
        self, username: str, email: str, password: str, first_name: str, last_name: str
    ) -> bool:
        """Validate user form data"""
        if not all([username, email, password, first_name, last_name]):
            st.error("❌ กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน")
            return False

        # Validate username
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            st.error("❌ ชื่อผู้ใช้ต้องประกอบด้วยตัวอักษรภาษาอังกฤษ ตัวเลข และ _ เท่านั้น")
            return False

        # Validate email
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            st.error("❌ รูปแบบอีเมลไม่ถูกต้อง")
            return False

        # Validate password
        if len(password) < 8:
            st.error("❌ รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
            return False

        return True

    def _create_user(self, user_data: Dict):
        """Create new user"""
        try:
            current_user = get_current_user()
            user_data["created_by"] = current_user["UserID"]

            result = safe_execute(
                self.user_manager.create_user,
                user_data,
                error_message="ไม่สามารถสร้างผู้ใช้ได้",
            )

            if result:
                st.success("✅ สร้างผู้ใช้เรียบร้อยแล้ว")
                st.session_state.show_new_user = False

                if user_data.get("send_welcome_email"):
                    st.info("📧 ส่งอีเมลต้อนรับแล้ว")

                st.rerun()

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            st.error("เกิดข้อผิดพลาดในการสร้างผู้ใช้")

    def _reset_user_password(self, user_id: int):
        """Reset user password"""
        with st.form(f"reset_password_{user_id}"):
            st.warning("🔑 รีเซ็ตรหัสผ่าน")

            new_password = st.text_input("รหัสผ่านใหม่", type="password")
            confirm_password = st.text_input("ยืนยันรหัสผ่าน", type="password")
            force_change = st.checkbox("บังคับเปลี่ยนรหัสผ่านเมื่อเข้าสู่ระบบครั้งถัดไป", value=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🔑 รีเซ็ตรหัสผ่าน", type="primary"):
                    if new_password and new_password == confirm_password:
                        if len(new_password) >= 8:
                            result = safe_execute(
                                self.user_manager.reset_password,
                                user_id,
                                new_password,
                                force_change,
                                error_message="ไม่สามารถรีเซ็ตรหัสผ่านได้",
                            )
                            if result:
                                st.success("✅ รีเซ็ตรหัสผ่านเรียบร้อยแล้ว")
                        else:
                            st.error("❌ รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
                    else:
                        st.error("❌ รหัสผ่านไม่ตรงกัน")

            with col2:
                if st.form_submit_button("❌ ยกเลิก"):
                    st.rerun()

    def _toggle_user_status(self, user_id: int, new_status: bool):
        """Toggle user active status"""
        try:
            result = safe_execute(
                self.user_manager.update_user_status,
                user_id,
                new_status,
                error_message="ไม่สามารถเปลี่ยนสถานะได้",
            )

            if result:
                status_text = "เปิดใช้งาน" if new_status else "ปิดใช้งาน"
                st.success(f"✅ {status_text}บัญชีผู้ใช้เรียบร้อยแล้ว")
                st.rerun()

        except Exception as e:
            logger.error(f"Error toggling user status: {e}")
            st.error("เกิดข้อผิดพลาดในการเปลี่ยนสถานะ")

    def _show_user_detailed_stats(self, user_id: int):
        """Show detailed user statistics"""
        with st.expander(f"📊 สถิติผู้ใช้ ID: {user_id}", expanded=True):
            stats = self._get_user_detailed_stats(user_id)

            if stats:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**📁 โครงการ**")
                    st.metric("โครงการที่สร้าง", stats.get("projects_created", 0))
                    st.metric("โครงการที่มีส่วนร่วม", stats.get("projects_involved", 0))

                with col2:
                    st.markdown("**✅ งาน**")
                    st.metric("งานที่ได้รับมอบหมาย", stats.get("tasks_assigned", 0))
                    st.metric("งานที่เสร็จสิ้น", stats.get("tasks_completed", 0))
                    completion_rate = (
                        stats.get("tasks_completed", 0)
                        / max(stats.get("tasks_assigned", 1), 1)
                    ) * 100
                    st.metric("อัตราความสำเร็จ", f"{completion_rate:.1f}%")

                with col3:
                    st.markdown("**🕒 กิจกรรม**")
                    st.metric("เข้าสู่ระบบครั้งล่าสุด", stats.get("last_login", "ยังไม่เคย"))
                    st.metric("จำนวนครั้งที่เข้าสู่ระบบ", stats.get("login_count", 0))
                    st.metric("ความคิดเห็นที่โพสต์", stats.get("comments_posted", 0))
            else:
                st.info("ไม่มีข้อมูลสถิติ")

    def _show_delete_confirmation(self, user_id: int):
        """Show delete confirmation dialog"""
        with st.form(f"delete_user_{user_id}"):
            st.error("⚠️ คำเตือน: การลบผู้ใช้")
            st.write("การลบผู้ใช้จะไม่สามารถกู้คืนได้ และจะส่งผลต่อ:")
            st.write("- โครงการที่ผู้ใช้เป็นเจ้าของ")
            st.write("- งานที่ผู้ใช้รับผิดชอบ")
            st.write("- ความคิดเห็นและกิจกรรมต่างๆ")

            confirm_text = st.text_input("พิมพ์ 'DELETE' เพื่อยืนยันการลบ")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🗑️ ลบผู้ใช้", type="primary"):
                    if confirm_text == "DELETE":
                        result = safe_execute(
                            self.user_manager.delete_user,
                            user_id,
                            error_message="ไม่สามารถลบผู้ใช้ได้",
                        )
                        if result:
                            st.success("✅ ลบผู้ใช้เรียบร้อยแล้ว")
                            st.rerun()
                    else:
                        st.error("❌ กรุณาพิมพ์ 'DELETE' เพื่อยืนยัน")

            with col2:
                if st.form_submit_button("❌ ยกเลิก"):
                    st.rerun()

    def _show_edit_user_form(self):
        """Show edit user form"""
        user_id = st.session_state.get("edit_user_id")
        if not user_id:
            return

        user_data = self._get_user_by_id(user_id)
        if not user_data:
            st.error("ไม่พบข้อมูลผู้ใช้")
            return

        with st.expander(f"แก้ไขผู้ใช้: {user_data['Username']}", expanded=True):
            with st.form("edit_user_form"):
                st.markdown("### ✏️ แก้ไขข้อมูลผู้ใช้")

                col1, col2 = st.columns(2)

                with col1:
                    username = st.text_input(
                        "ชื่อผู้ใช้", value=user_data["Username"], disabled=True
                    )
                    first_name = st.text_input("ชื่อ", value=user_data["FirstName"])
                    email = st.text_input("อีเมล", value=user_data["Email"])
                    role = st.selectbox(
                        "บทบาท",
                        [role.value for role in UserRole],
                        index=[role.value for role in UserRole].index(
                            user_data["Role"]
                        ),
                    )

                with col2:
                    last_name = st.text_input("นามสกุล", value=user_data["LastName"])
                    phone = st.text_input(
                        "เบอร์โทรศัพท์", value=user_data.get("Phone", "")
                    )
                    department = st.selectbox(
                        "แผนก",
                        [
                            "IT",
                            "Engineering",
                            "Production",
                            "Quality",
                            "Sales",
                            "Marketing",
                            "HR",
                            "Finance",
                            "Management",
                        ],
                        index=[
                            "IT",
                            "Engineering",
                            "Production",
                            "Quality",
                            "Sales",
                            "Marketing",
                            "HR",
                            "Finance",
                            "Management",
                        ].index(user_data.get("Department", "IT")),
                    )
                    is_active = st.checkbox("เปิดใช้งานบัญชี", value=user_data["IsActive"])

                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary"):
                        updated_data = {
                            "user_id": user_id,
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": email,
                            "phone": phone,
                            "role": role,
                            "department": department,
                            "is_active": is_active,
                        }

                        if self._update_user(updated_data):
                            st.success("✅ อัปเดตข้อมูลผู้ใช้เรียบร้อยแล้ว")
                            st.session_state.edit_user_id = None
                            st.rerun()

                with col2:
                    if st.form_submit_button("❌ ยกเลิก"):
                        st.session_state.edit_user_id = None
                        st.rerun()

    # Helper methods
    def _get_filtered_users(self) -> List[Dict]:
        """Get users based on current filters"""
        filters = {
            "search": st.session_state.get("user_search", ""),
            "role": st.session_state.get("user_role_filter", []),
            "department": st.session_state.get("user_department_filter", []),
            "status": st.session_state.get("user_status_filter", "ทั้งหมด"),
        }

        return safe_execute(
            self.user_manager.get_filtered_users, filters, default_return=[]
        )

    def _get_user_statistics(self) -> Dict:
        """Get user statistics"""
        return safe_execute(self.user_manager.get_user_statistics, default_return={})

    def _get_user_detailed_stats(self, user_id: int) -> Dict:
        """Get detailed statistics for specific user"""
        return safe_execute(
            self.user_manager.get_user_detailed_stats, user_id, default_return={}
        )

    def _get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user data by ID"""
        return safe_execute(
            self.user_manager.get_user_by_id, user_id, default_return=None
        )

    def _update_user(self, user_data: Dict) -> bool:
        """Update user data"""
        try:
            result = safe_execute(
                self.user_manager.update_user,
                user_data,
                error_message="ไม่สามารถอัปเดตข้อมูลผู้ใช้ได้",
            )
            return bool(result)

        except Exception as e:
            logger.error(f"Error updating user: {e}")
            st.error("เกิดข้อผิดพลาดในการอัปเดตข้อมูล")
            return False
