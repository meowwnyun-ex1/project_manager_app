"""
pages/settings.py
System settings page
"""

import streamlit as st
from datetime import datetime, time
from typing import Dict, List, Any, Optional
import logging
import json

from modules.ui_components import (
    FormBuilder,
    CardComponent,
    NotificationManager,
    ModernModal,
)
from modules.auth import require_role, get_current_user
from modules.settings import SettingsManager
from utils.error_handler import handle_streamlit_errors, safe_execute
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


class SettingsPage:
    """System settings page class"""

    def __init__(self, settings_manager, user_manager):
        self.settings_manager = settings_manager
        self.user_manager = user_manager

    @handle_streamlit_errors()
    @monitor_performance("settings_page_render")
    def show(self):
        """Show settings page"""
        st.title("⚙️ การตั้งค่าระบบ")

        # Get current user
        current_user = get_current_user()
        if not current_user:
            st.error("กรุณาเข้าสู่ระบบ")
            return

        # Settings tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["🔧 ทั่วไป", "🔐 ความปลอดภัย", "👤 โปรไฟล์", "📧 การแจ้งเตือน", "🔄 สำรองข้อมูล"]
        )

        with tab1:
            self._show_general_settings()

        with tab2:
            self._show_security_settings()

        with tab3:
            self._show_profile_settings()

        with tab4:
            self._show_notification_settings()

        with tab5:
            self._show_backup_settings()

    def _show_general_settings(self):
        """Show general system settings"""
        st.subheader("🔧 การตั้งค่าทั่วไป")

        # Only admins can modify system settings
        current_user = get_current_user()
        is_admin = current_user.get("Role") == "Admin"

        if not is_admin:
            st.info("💡 เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถแก้ไขการตั้งค่าระบบได้")

        # Get current settings
        settings = self._get_system_settings()

        with st.form("general_settings"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🎨 ลักษณะและการแสดงผล")

                app_name = st.text_input(
                    "ชื่อแอปพลิเคชัน",
                    value=settings.get("app_name", "DENSO Project Manager Pro"),
                    disabled=not is_admin,
                )

                theme = st.selectbox(
                    "ธีม",
                    ["auto", "light", "dark"],
                    index=["auto", "light", "dark"].index(
                        settings.get("default_theme", "auto")
                    ),
                    disabled=not is_admin,
                )

                language = st.selectbox(
                    "ภาษา",
                    ["th", "en"],
                    index=["th", "en"].index(settings.get("default_language", "th")),
                    disabled=not is_admin,
                )

                items_per_page = st.number_input(
                    "จำนวนรายการต่อหน้า",
                    min_value=5,
                    max_value=100,
                    value=int(settings.get("items_per_page", 20)),
                    disabled=not is_admin,
                )

            with col2:
                st.markdown("#### 🔄 ระบบ")

                maintenance_mode = st.checkbox(
                    "เปิดโหมดบำรุงรักษา",
                    value=settings.get("maintenance_mode", False),
                    disabled=not is_admin,
                    help="เมื่อเปิดโหมดนี้ จะมีเฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าใช้งานได้",
                )

                auto_backup = st.checkbox(
                    "สำรองข้อมูลอัตโนมัติ",
                    value=settings.get("auto_backup_enabled", True),
                    disabled=not is_admin,
                )

                backup_time = st.time_input(
                    "เวลาสำรองข้อมูล",
                    value=time(2, 0),  # 2:00 AM default
                    disabled=not is_admin or not auto_backup,
                )

                max_upload_size = st.number_input(
                    "ขนาดไฟล์อัปโหลดสูงสุด (MB)",
                    min_value=1,
                    max_value=500,
                    value=int(settings.get("max_upload_size", 50)),
                    disabled=not is_admin,
                )

            st.markdown("#### 📊 การทำงาน")

            col1, col2 = st.columns(2)

            with col1:
                session_timeout = st.number_input(
                    "หมดเวลาเซสชัน (นาที)",
                    min_value=15,
                    max_value=480,
                    value=int(settings.get("session_timeout", 60)),
                    disabled=not is_admin,
                )

                enable_notifications = st.checkbox(
                    "เปิดการแจ้งเตือน",
                    value=settings.get("enable_notifications", True),
                    disabled=not is_admin,
                )

            with col2:
                log_level = st.selectbox(
                    "ระดับการบันทึก Log",
                    ["DEBUG", "INFO", "WARNING", "ERROR"],
                    index=["DEBUG", "INFO", "WARNING", "ERROR"].index(
                        settings.get("log_level", "INFO")
                    ),
                    disabled=not is_admin,
                )

                enable_audit_log = st.checkbox(
                    "เปิดการบันทึกการตรวจสอบ",
                    value=settings.get("enable_audit_log", True),
                    disabled=not is_admin,
                )

            if is_admin:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.form_submit_button("💾 บันทึกการตั้งค่า", type="primary"):
                        new_settings = {
                            "app_name": app_name,
                            "default_theme": theme,
                            "default_language": language,
                            "items_per_page": items_per_page,
                            "maintenance_mode": maintenance_mode,
                            "auto_backup_enabled": auto_backup,
                            "backup_time": backup_time.strftime("%H:%M"),
                            "max_upload_size": max_upload_size,
                            "session_timeout": session_timeout,
                            "enable_notifications": enable_notifications,
                            "log_level": log_level,
                            "enable_audit_log": enable_audit_log,
                        }

                        if self._update_system_settings(new_settings):
                            st.success("✅ บันทึกการตั้งค่าเรียบร้อยแล้ว")
                            st.rerun()

    def _show_security_settings(self):
        """Show security settings"""
        st.subheader("🔐 การตั้งค่าความปลอดภัย")

        current_user = get_current_user()
        is_admin = current_user.get("Role") == "Admin"

        # Get security settings
        security_settings = self._get_security_settings()

        with st.form("security_settings"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🔑 รหัสผ่าน")

                password_min_length = st.number_input(
                    "ความยาวรหัสผ่านขั้นต่ำ",
                    min_value=6,
                    max_value=20,
                    value=int(security_settings.get("password_min_length", 8)),
                    disabled=not is_admin,
                )

                require_uppercase = st.checkbox(
                    "ต้องมีตัวพิมพ์ใหญ่",
                    value=security_settings.get("require_uppercase", True),
                    disabled=not is_admin,
                )

                require_lowercase = st.checkbox(
                    "ต้องมีตัวพิมพ์เล็ก",
                    value=security_settings.get("require_lowercase", True),
                    disabled=not is_admin,
                )

                require_numbers = st.checkbox(
                    "ต้องมีตัวเลข",
                    value=security_settings.get("require_numbers", True),
                    disabled=not is_admin,
                )

                require_special = st.checkbox(
                    "ต้องมีอักขระพิเศษ",
                    value=security_settings.get("require_special", True),
                    disabled=not is_admin,
                )

            with col2:
                st.markdown("#### 🛡️ การเข้าสู่ระบบ")

                max_login_attempts = st.number_input(
                    "จำนวนครั้งที่ล็อกอินผิดสูงสุด",
                    min_value=3,
                    max_value=10,
                    value=int(security_settings.get("max_login_attempts", 5)),
                    disabled=not is_admin,
                )

                lockout_duration = st.number_input(
                    "ระยะเวลาล็อคบัญชี (นาที)",
                    min_value=5,
                    max_value=60,
                    value=int(security_settings.get("lockout_duration", 15)),
                    disabled=not is_admin,
                )

                force_password_change = st.number_input(
                    "บังคับเปลี่ยนรหัสผ่านทุก (วัน)",
                    min_value=30,
                    max_value=365,
                    value=int(security_settings.get("password_expiry_days", 90)),
                    disabled=not is_admin,
                )

                two_factor_auth = st.checkbox(
                    "เปิดใช้งาน Two-Factor Authentication",
                    value=security_settings.get("enable_2fa", False),
                    disabled=not is_admin,
                )

            if is_admin:
                if st.form_submit_button("🔐 บันทึกการตั้งค่าความปลอดภัย", type="primary"):
                    new_security_settings = {
                        "password_min_length": password_min_length,
                        "require_uppercase": require_uppercase,
                        "require_lowercase": require_lowercase,
                        "require_numbers": require_numbers,
                        "require_special": require_special,
                        "max_login_attempts": max_login_attempts,
                        "lockout_duration": lockout_duration,
                        "password_expiry_days": force_password_change,
                        "enable_2fa": two_factor_auth,
                    }

                    if self._update_security_settings(new_security_settings):
                        st.success("✅ บันทึกการตั้งค่าความปลอดภัยเรียบร้อยแล้ว")
                        st.rerun()

    def _show_profile_settings(self):
        """Show user profile settings"""
        st.subheader("👤 การตั้งค่าโปรไฟล์")

        current_user = get_current_user()
        user_data = self._get_user_profile(current_user["UserID"])

        if not user_data:
            st.error("ไม่สามารถโหลดข้อมูลโปรไฟล์ได้")
            return

        with st.form("profile_settings"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📝 ข้อมูลส่วนตัว")

                first_name = st.text_input("ชื่อ", value=user_data.get("FirstName", ""))
                last_name = st.text_input("นามสกุล", value=user_data.get("LastName", ""))
                email = st.text_input("อีเมล", value=user_data.get("Email", ""))
                phone = st.text_input("เบอร์โทรศัพท์", value=user_data.get("Phone", ""))

            with col2:
                st.markdown("#### 🎨 การตั้งค่าส่วนบุคคล")

                user_theme = st.selectbox(
                    "ธีมที่ต้องการ", ["ใช้การตั้งค่าระบบ", "สว่าง", "มืด"], index=0
                )

                user_language = st.selectbox(
                    "ภาษา", ["ใช้การตั้งค่าระบบ", "ไทย", "English"], index=0
                )

                timezone = st.selectbox(
                    "เขตเวลา",
                    ["Asia/Bangkok", "UTC", "Asia/Tokyo", "America/New_York"],
                    index=0,
                )

                date_format = st.selectbox(
                    "รูปแบบวันที่", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"], index=0
                )

            st.markdown("#### 🔔 การแจ้งเตือน")

            col1, col2 = st.columns(2)

            with col1:
                email_notifications = st.checkbox(
                    "รับแจ้งเตือนทางอีเมล", value=user_data.get("EmailNotifications", True)
                )

                task_reminders = st.checkbox(
                    "แจ้งเตือนเมื่องานใกล้ครบกำหนด",
                    value=user_data.get("TaskReminders", True),
                )

            with col2:
                project_updates = st.checkbox(
                    "แจ้งเตือนการอัปเดตโครงการ",
                    value=user_data.get("ProjectUpdates", True),
                )

                system_announcements = st.checkbox(
                    "แจ้งเตือนประกาศระบบ",
                    value=user_data.get("SystemAnnouncements", True),
                )

            col1, col2 = st.columns([1, 3])
            with col1:
                if st.form_submit_button("💾 บันทึกโปรไฟล์", type="primary"):
                    profile_data = {
                        "user_id": current_user["UserID"],
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "user_theme": user_theme,
                        "user_language": user_language,
                        "timezone": timezone,
                        "date_format": date_format,
                        "email_notifications": email_notifications,
                        "task_reminders": task_reminders,
                        "project_updates": project_updates,
                        "system_announcements": system_announcements,
                    }

                    if self._update_user_profile(profile_data):
                        st.success("✅ บันทึกโปรไฟล์เรียบร้อยแล้ว")
                        st.rerun()

        # Password change section
        st.markdown("---")
        st.markdown("#### 🔑 เปลี่ยนรหัสผ่าน")

        with st.form("change_password"):
            col1, col2, col3 = st.columns(3)

            with col1:
                current_password = st.text_input("รหัสผ่านปัจจุบัน", type="password")

            with col2:
                new_password = st.text_input("รหัสผ่านใหม่", type="password")

            with col3:
                confirm_password = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")
