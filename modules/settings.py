#!/usr/bin/env python3
"""
modules/settings.py
System Settings Management for DENSO Project Manager Pro
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from typing import Dict, List, Any, Optional
import logging
import json
import os

from utils.error_handler import safe_execute, handle_error, validate_input
from utils.ui_components import UIComponents

logger = logging.getLogger(__name__)


class SettingsManager:
    """System settings management functionality"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.ui = UIComponents()

    def get_system_settings(self) -> Dict[str, Any]:
        """Get system settings"""
        try:
            # Create settings table if not exists
            self._ensure_settings_table()

            query = "SELECT SettingKey, SettingValue FROM SystemSettings"
            results = self.db.execute_query(query)

            settings = {}
            for row in results:
                try:
                    # Try to parse JSON values
                    settings[row["SettingKey"]] = json.loads(row["SettingValue"])
                except json.JSONDecodeError:
                    # If not JSON, store as string
                    settings[row["SettingKey"]] = row["SettingValue"]

            # Default settings if none exist
            if not settings:
                settings = self._get_default_settings()
                self._save_default_settings(settings)

            return settings

        except Exception as e:
            logger.error(f"Error getting system settings: {e}")
            return self._get_default_settings()

    def update_setting(self, key: str, value: Any) -> bool:
        """Update a system setting"""
        try:
            self._ensure_settings_table()

            # Convert value to JSON if needed
            if isinstance(value, (dict, list)):
                json_value = json.dumps(value)
            else:
                json_value = str(value)

            # Check if setting exists
            check_query = (
                "SELECT COUNT(*) as count FROM SystemSettings WHERE SettingKey = ?"
            )
            result = self.db.execute_query(check_query, (key,))

            if result and result[0]["count"] > 0:
                # Update existing setting
                query = "UPDATE SystemSettings SET SettingValue = ?, UpdatedDate = GETDATE() WHERE SettingKey = ?"
                self.db.execute_non_query(query, (json_value, key))
            else:
                # Insert new setting
                query = "INSERT INTO SystemSettings (SettingKey, SettingValue) VALUES (?, ?)"
                self.db.execute_non_query(query, (key, json_value))

            return True

        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False

    def backup_database(self) -> Dict[str, Any]:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backups/backup_{timestamp}.bak"

            # Ensure backup directory exists
            os.makedirs("data/backups", exist_ok=True)

            query = f"""
            BACKUP DATABASE [{st.secrets['database']['database']}] 
            TO DISK = '{os.path.abspath(backup_path)}'
            WITH FORMAT, COMPRESSION, CHECKSUM
            """

            self.db.execute_non_query(query)

            return {
                "success": True,
                "backup_path": backup_path,
                "timestamp": timestamp,
                "message": "การสำรองข้อมูลสำเร็จ",
            }

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {"success": False, "error": str(e), "message": "การสำรองข้อมูลล้มเหลว"}

    def cleanup_database(self) -> Dict[str, Any]:
        """Clean up old data"""
        try:
            cleanup_stats = {"deleted_records": 0, "actions": []}

            # Clean up old activity logs (older than 6 months)
            query = """
            DELETE FROM ActivityLogs 
            WHERE CreatedDate < DATEADD(month, -6, GETDATE())
            """

            try:
                rows_affected = self.db.execute_non_query(query)
                cleanup_stats["deleted_records"] += rows_affected
                cleanup_stats["actions"].append(
                    f"ลบ Activity Logs เก่า: {rows_affected} รายการ"
                )
            except:
                pass  # Table might not exist

            # Clean up temporary files
            temp_files_cleaned = 0
            if os.path.exists("temp"):
                for file in os.listdir("temp"):
                    try:
                        os.remove(os.path.join("temp", file))
                        temp_files_cleaned += 1
                    except:
                        pass

                cleanup_stats["actions"].append(
                    f"ลบไฟล์ชั่วคราว: {temp_files_cleaned} ไฟล์"
                )

            return {
                "success": True,
                "stats": cleanup_stats,
                "message": "ทำความสะอาดข้อมูลสำเร็จ",
            }

        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "การทำความสะอาดข้อมูลล้มเหลว",
            }

    def get_backup_files(self) -> List[Dict[str, Any]]:
        """Get list of backup files"""
        try:
            backup_dir = "data/backups"
            if not os.path.exists(backup_dir):
                return []

            backups = []
            for file in os.listdir(backup_dir):
                if file.endswith(".bak"):
                    file_path = os.path.join(backup_dir, file)
                    stat = os.stat(file_path)

                    backups.append(
                        {
                            "filename": file,
                            "path": file_path,
                            "size": stat.st_size,
                            "created_date": datetime.fromtimestamp(stat.st_ctime),
                        }
                    )

            return sorted(backups, key=lambda x: x["created_date"], reverse=True)

        except Exception as e:
            logger.error(f"Error getting backup files: {e}")
            return []

    def _ensure_settings_table(self):
        """Ensure SystemSettings table exists"""
        try:
            query = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SystemSettings' AND xtype='U')
            CREATE TABLE SystemSettings (
                SettingID INT IDENTITY(1,1) PRIMARY KEY,
                SettingKey NVARCHAR(100) UNIQUE NOT NULL,
                SettingValue NVARCHAR(MAX) NOT NULL,
                CreatedDate DATETIME DEFAULT GETDATE(),
                UpdatedDate DATETIME DEFAULT GETDATE()
            )
            """

            self.db.execute_non_query(query)

        except Exception as e:
            logger.error(f"Error creating settings table: {e}")

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default system settings"""
        return {
            "app_name": "DENSO Project Manager Pro",
            "app_version": "2.0.0",
            "theme": "light",
            "language": "th",
            "timezone": "Asia/Bangkok",
            "session_timeout": 3600,
            "max_upload_size": 50,
            "email_notifications": True,
            "auto_backup": False,
            "backup_schedule": "02:00",
            "backup_retention_days": 30,
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digits": True,
                "require_special": True,
                "history_count": 5,
            },
            "security_settings": {
                "max_login_attempts": 5,
                "lockout_duration": 900,
                "session_cookie_secure": False,
                "force_password_change": False,
            },
        }

    def _save_default_settings(self, settings: Dict[str, Any]):
        """Save default settings to database"""
        for key, value in settings.items():
            self.update_setting(key, value)


def show_settings_page(settings_manager: SettingsManager, user_data: Dict[str, Any]):
    """Show settings page"""
    ui = UIComponents()

    # Page header
    ui.render_page_header("⚙️ การตั้งค่าระบบ", "จัดการการตั้งค่าและการกำหนดค่าระบบ", "⚙️")

    # Check permissions
    if user_data["Role"] not in ["Admin", "Project Manager"]:
        st.error("❌ คุณไม่มีสิทธิ์เข้าถึงการตั้งค่าระบบ")
        return

    # Main content tabs
    if user_data["Role"] == "Admin":
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["🔧 ทั่วไป", "🔐 ความปลอดภัย", "👤 โปรไฟล์", "📧 การแจ้งเตือน", "🔄 สำรองข้อมูล"]
        )
    else:
        tab1, tab2, tab3 = st.tabs(["👤 โปรไฟล์", "📧 การแจ้งเตือน", "🔧 การตั้งค่าส่วนตัว"])

    if user_data["Role"] == "Admin":
        with tab1:
            show_general_settings(settings_manager)

        with tab2:
            show_security_settings(settings_manager)

        with tab3:
            show_profile_settings(settings_manager, user_data)

        with tab4:
            show_notification_settings(settings_manager)

        with tab5:
            show_backup_settings(settings_manager)
    else:
        with tab1:
            show_profile_settings(settings_manager, user_data)

        with tab2:
            show_notification_settings(settings_manager)

        with tab3:
            show_user_preferences(settings_manager, user_data)


def show_general_settings(settings_manager: SettingsManager):
    """Show general system settings"""
    st.subheader("🔧 การตั้งค่าทั่วไป")

    # Get current settings
    settings = safe_execute(settings_manager.get_system_settings, default_return={})

    with st.form("general_settings_form"):
        col1, col2 = st.columns(2)

        with col1:
            app_name = st.text_input(
                "ชื่อแอปพลิเคชัน",
                value=settings.get("app_name", "DENSO Project Manager Pro"),
            )

            theme = st.selectbox(
                "ธีม",
                options=["light", "dark"],
                index=0 if settings.get("theme", "light") == "light" else 1,
            )

            language = st.selectbox(
                "ภาษา",
                options=["th", "en"],
                index=0 if settings.get("language", "th") == "th" else 1,
            )

            session_timeout = st.number_input(
                "หมดเวลาเซสชัน (วินาที)",
                min_value=300,
                max_value=86400,
                value=settings.get("session_timeout", 3600),
                step=300,
            )

        with col2:
            timezone = st.selectbox(
                "เขตเวลา", options=["Asia/Bangkok", "UTC", "Asia/Tokyo"], index=0
            )

            max_upload_size = st.number_input(
                "ขนาดไฟล์อัปโหลดสูงสุด (MB)",
                min_value=1,
                max_value=500,
                value=settings.get("max_upload_size", 50),
                step=5,
            )

            email_notifications = st.checkbox(
                "เปิดการแจ้งเตือนทางอีเมล", value=settings.get("email_notifications", True)
            )

        if st.form_submit_button("💾 บันทึกการตั้งค่า", type="primary"):
            # Update settings
            updates = {
                "app_name": app_name,
                "theme": theme,
                "language": language,
                "timezone": timezone,
                "session_timeout": session_timeout,
                "max_upload_size": max_upload_size,
                "email_notifications": email_notifications,
            }

            success_count = 0
            for key, value in updates.items():
                if settings_manager.update_setting(key, value):
                    success_count += 1

            if success_count == len(updates):
                st.success("✅ บันทึกการตั้งค่าทั่วไปสำเร็จ")
                st.rerun()
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึกบางการตั้งค่า")


def show_security_settings(settings_manager: SettingsManager):
    """Show security settings"""
    st.subheader("🔐 การตั้งค่าความปลอดภัย")

    settings = safe_execute(settings_manager.get_system_settings, default_return={})
    password_policy = settings.get("password_policy", {})
    security_settings = settings.get("security_settings", {})

    # Password Policy Settings
    st.markdown("### 🔒 นโยบายรหัสผ่าน")

    with st.form("password_policy_form"):
        col1, col2 = st.columns(2)

        with col1:
            min_length = st.number_input(
                "ความยาวขั้นต่ำ",
                min_value=4,
                max_value=32,
                value=password_policy.get("min_length", 8),
            )

            require_uppercase = st.checkbox(
                "ต้องมีตัวพิมพ์ใหญ่", value=password_policy.get("require_uppercase", True)
            )

            require_lowercase = st.checkbox(
                "ต้องมีตัวพิมพ์เล็ก", value=password_policy.get("require_lowercase", True)
            )

        with col2:
            require_digits = st.checkbox(
                "ต้องมีตัวเลข", value=password_policy.get("require_digits", True)
            )

            require_special = st.checkbox(
                "ต้องมีอักขระพิเศษ", value=password_policy.get("require_special", True)
            )

            history_count = st.number_input(
                "จำนวนรหัสผ่านเก่าที่ห้ามใช้ซ้ำ",
                min_value=0,
                max_value=10,
                value=password_policy.get("history_count", 5),
            )

        if st.form_submit_button("💾 บันทึกนโยบายรหัสผ่าน"):
            new_policy = {
                "min_length": min_length,
                "require_uppercase": require_uppercase,
                "require_lowercase": require_lowercase,
                "require_digits": require_digits,
                "require_special": require_special,
                "history_count": history_count,
            }

            if settings_manager.update_setting("password_policy", new_policy):
                st.success("✅ บันทึกนโยบายรหัสผ่านสำเร็จ")
                st.rerun()
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึก")

    st.markdown("---")

    # Login Security Settings
    st.markdown("### 🛡️ การตั้งค่าการเข้าสู่ระบบ")

    with st.form("login_security_form"):
        col1, col2 = st.columns(2)

        with col1:
            max_login_attempts = st.number_input(
                "จำนวนครั้งที่พยายามเข้าสู่ระบบผิดสูงสุด",
                min_value=3,
                max_value=10,
                value=security_settings.get("max_login_attempts", 5),
            )

            lockout_duration = st.number_input(
                "ระยะเวลาล็อค (วินาที)",
                min_value=300,
                max_value=3600,
                value=security_settings.get("lockout_duration", 900),
                step=300,
            )

        with col2:
            session_cookie_secure = st.checkbox(
                "ใช้ Secure Cookies",
                value=security_settings.get("session_cookie_secure", False),
                help="เปิดใช้งานเมื่อใช้ HTTPS",
            )

            force_password_change = st.checkbox(
                "บังคับเปลี่ยนรหัสผ่านเมื่อล็อกอินครั้งแรก",
                value=security_settings.get("force_password_change", False),
            )

        if st.form_submit_button("💾 บันทึกการตั้งค่าความปลอดภัย"):
            new_security = {
                "max_login_attempts": max_login_attempts,
                "lockout_duration": lockout_duration,
                "session_cookie_secure": session_cookie_secure,
                "force_password_change": force_password_change,
            }

            if settings_manager.update_setting("security_settings", new_security):
                st.success("✅ บันทึกการตั้งค่าความปลอดภัยสำเร็จ")
                st.rerun()
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึก")


def show_profile_settings(settings_manager: SettingsManager, user_data: Dict[str, Any]):
    """Show user profile settings"""
    st.subheader("👤 การตั้งค่าโปรไฟล์")

    # User information
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ข้อมูลส่วนตัว")
        st.markdown(f"**ชื่อ:** {user_data['FirstName']} {user_data['LastName']}")
        st.markdown(f"**ชื่อผู้ใช้:** {user_data['Username']}")
        st.markdown(f"**อีเมล:** {user_data['Email']}")
        st.markdown(f"**บทบาท:** {user_data['Role']}")
        st.markdown(f"**แผนก:** {user_data.get('Department', 'N/A')}")

    with col2:
        st.markdown("### สถิติการใช้งาน")
        if user_data.get("LastLoginDate"):
            last_login = user_data["LastLoginDate"].strftime("%d/%m/%Y %H:%M")
            st.markdown(f"**เข้าสู่ระบบล่าสุด:** {last_login}")
        else:
            st.markdown("**เข้าสู่ระบบล่าสุด:** ครั้งแรก")

        if user_data.get("CreatedDate"):
            created_date = user_data["CreatedDate"].strftime("%d/%m/%Y")
            account_age = (datetime.now() - user_data["CreatedDate"]).days
            st.markdown(f"**สร้างบัญชี:** {created_date}")
            st.markdown(f"**อายุบัญชี:** {account_age} วัน")

    st.markdown("---")

    # Change password
    st.markdown("### 🔐 เปลี่ยนรหัสผ่าน")

    with st.form("change_password_form"):
        current_password = st.text_input("รหัสผ่านปัจจุบัน", type="password")
        new_password = st.text_input("รหัสผ่านใหม่", type="password")
        confirm_password = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")

        if st.form_submit_button("🔑 เปลี่ยนรหัสผ่าน"):
            if not all([current_password, new_password, confirm_password]):
                st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน")
            elif new_password != confirm_password:
                st.error("❌ รหัสผ่านใหม่ไม่ตรงกัน")
            elif len(new_password) < 8:
                st.error("❌ รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
            else:
                # Change password logic would go here
                try:
                    from modules.auth import AuthenticationManager

                    auth_manager = AuthenticationManager(settings_manager.db)

                    result = auth_manager.change_password(
                        user_data["UserID"], current_password, new_password
                    )

                    if result["success"]:
                        st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ")
                    else:
                        st.error(f"❌ {result['message']}")

                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")


def show_notification_settings(settings_manager: SettingsManager):
    """Show notification settings"""
    st.subheader("📧 การตั้งค่าการแจ้งเตือน")

    settings = safe_execute(settings_manager.get_system_settings, default_return={})

    # Email notification settings
    with st.form("notification_settings_form"):
        st.markdown("### 📬 การแจ้งเตือนทางอีเมล")

        col1, col2 = st.columns(2)

        with col1:
            email_notifications = st.checkbox(
                "เปิดการแจ้งเตือนทางอีเมล", value=settings.get("email_notifications", True)
            )

            task_assignment_notify = st.checkbox("แจ้งเตือนเมื่อได้รับมอบหมายงาน", value=True)

            task_due_notify = st.checkbox("แจ้งเตือนงานที่ใกล้ครบกำหนด", value=True)

            project_update_notify = st.checkbox("แจ้งเตือนการอัปเดตโครงการ", value=True)

        with col2:
            daily_summary = st.checkbox("ส่งสรุปรายวัน", value=False)

            weekly_report = st.checkbox("ส่งรายงานรายสัปดาห์", value=False)

            system_maintenance = st.checkbox("แจ้งเตือนการบำรุงรักษาระบบ", value=True)

        st.markdown("### ⏰ เวลาการส่งการแจ้งเตือน")

        col1, col2 = st.columns(2)

        with col1:
            daily_summary_time = st.time_input("เวลาส่งสรุปรายวัน", value=time(8, 0))

        with col2:
            due_reminder_hours = st.number_input(
                "แจ้งเตือนก่อนครบกำหนด (ชั่วโมง)", min_value=1, max_value=168, value=24
            )

        if st.form_submit_button("💾 บันทึกการตั้งค่าการแจ้งเตือน"):
            notification_settings = {
                "email_notifications": email_notifications,
                "task_assignment_notify": task_assignment_notify,
                "task_due_notify": task_due_notify,
                "project_update_notify": project_update_notify,
                "daily_summary": daily_summary,
                "weekly_report": weekly_report,
                "system_maintenance": system_maintenance,
                "daily_summary_time": daily_summary_time.strftime("%H:%M"),
                "due_reminder_hours": due_reminder_hours,
            }

            if settings_manager.update_setting(
                "notification_settings", notification_settings
            ):
                st.success("✅ บันทึกการตั้งค่าการแจ้งเตือนสำเร็จ")
                st.rerun()
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึก")


def show_backup_settings(settings_manager: SettingsManager):
    """Show backup and maintenance settings"""
    st.subheader("🔄 การสำรองข้อมูลและบำรุงรักษา")

    settings = safe_execute(settings_manager.get_system_settings, default_return={})

    # Backup settings
    st.markdown("### 💾 การตั้งค่าการสำรองข้อมูล")

    with st.form("backup_settings_form"):
        col1, col2 = st.columns(2)

        with col1:
            auto_backup = st.checkbox(
                "การสำรองข้อมูลอัตโนมัติ", value=settings.get("auto_backup", False)
            )

            backup_schedule = st.time_input("เวลาสำรองข้อมูลอัตโนมัติ", value=time(2, 0))

        with col2:
            backup_retention_days = st.number_input(
                "เก็บไฟล์สำรองข้อมูล (วัน)",
                min_value=7,
                max_value=365,
                value=settings.get("backup_retention_days", 30),
            )

            compression_level = st.selectbox(
                "ระดับการบีบอัด", options=["None", "Normal", "High"], index=1
            )

        if st.form_submit_button("💾 บันทึกการตั้งค่าการสำรองข้อมูล"):
            backup_settings = {
                "auto_backup": auto_backup,
                "backup_schedule": backup_schedule.strftime("%H:%M"),
                "backup_retention_days": backup_retention_days,
                "compression_level": compression_level,
            }

            for key, value in backup_settings.items():
                settings_manager.update_setting(key, value)

            st.success("✅ บันทึกการตั้งค่าการสำรองข้อมูลสำเร็จ")
            st.rerun()

    st.markdown("---")

    # Manual backup and maintenance
    st.markdown("### 🛠️ การดำเนินการด้วยตนเอง")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 สำรองข้อมูลทันที", type="primary"):
            with st.spinner("กำลังสำรองข้อมูล..."):
                result = settings_manager.backup_database()

                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    st.info(f"ไฟล์สำรอง: {result['backup_path']}")
                else:
                    st.error(f"❌ {result['message']}")

    with col2:
        if st.button("🧹 ทำความสะอาดข้อมูล"):
            with st.spinner("กำลังทำความสะอาดข้อมูล..."):
                result = settings_manager.cleanup_database()

                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    for action in result["stats"]["actions"]:
                        st.info(f"• {action}")
                else:
                    st.error(f"❌ {result['message']}")

    with col3:
        if st.button("📊 ตรวจสอบระบบ"):
            st.info("ฟีเจอร์การตรวจสอบระบบกำลังพัฒนา")

    # Backup files list
    st.markdown("### 📁 ไฟล์สำรองข้อมูล")

    backup_files = safe_execute(settings_manager.get_backup_files, default_return=[])

    if backup_files:
        for backup in backup_files[:10]:  # Show last 10 backups
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.markdown(f"**{backup['filename']}**")

            with col2:
                st.markdown(f"{backup['size'] / 1024 / 1024:.1f} MB")

            with col3:
                st.markdown(backup["created_date"].strftime("%d/%m/%Y %H:%M"))

            with col4:
                if st.button("📥", key=f"download_{backup['filename']}"):
                    st.info("ฟีเจอร์ดาวน์โหลดกำลังพัฒนา")
    else:
        st.info("ไม่พบไฟล์สำรองข้อมูล")


def show_user_preferences(settings_manager: SettingsManager, user_data: Dict[str, Any]):
    """Show user-specific preferences"""
    st.subheader("🔧 การตั้งค่าส่วนตัว")

    # User preferences
    with st.form("user_preferences_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🎨 การแสดงผล")

            dashboard_layout = st.selectbox(
                "รูปแบบแดชบอร์ด", options=["แบบกะทัดรัด", "แบบรายละเอียด", "แบบกราฟ"]
            )

            items_per_page = st.selectbox(
                "รายการต่อหน้า", options=[10, 25, 50, 100], index=1
            )

            show_completed_tasks = st.checkbox("แสดงงานที่เสร็จแล้วในรายการ", value=False)

        with col2:
            st.markdown("### 📊 การแจ้งเตือนส่วนตัว")

            desktop_notifications = st.checkbox("การแจ้งเตือนบนเดสก์ท็อป", value=True)

            sound_notifications = st.checkbox("เสียงแจ้งเตือน", value=False)

            auto_refresh = st.checkbox("รีเฟรชหน้าอัตโนมัติ", value=True)

        if st.form_submit_button("💾 บันทึกการตั้งค่าส่วนตัว"):
            preferences = {
                "dashboard_layout": dashboard_layout,
                "items_per_page": items_per_page,
                "show_completed_tasks": show_completed_tasks,
                "desktop_notifications": desktop_notifications,
                "sound_notifications": sound_notifications,
                "auto_refresh": auto_refresh,
            }

            # Save user preferences (would typically save to user-specific settings)
            user_pref_key = f"user_preferences_{user_data['UserID']}"
            if settings_manager.update_setting(user_pref_key, preferences):
                st.success("✅ บันทึกการตั้งค่าส่วนตัวสำเร็จ")
                st.rerun()
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึก")
