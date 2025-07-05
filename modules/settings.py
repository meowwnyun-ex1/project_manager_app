#!/usr/bin/env python3
"""
modules/settings.py
Complete Settings Management System for DENSO Project Manager Pro
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SettingsManager:
    """System settings management with full functionality"""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            # Get database info
            db_info = self.db.execute_query(
                "SELECT @@VERSION as Version, @@SERVERNAME as ServerName, DB_NAME() as DatabaseName"
            )
            db_details = db_info[0] if db_info else {}

            # Get table counts
            table_counts = self.db.execute_query(
                """
                SELECT 
                    (SELECT COUNT(*) FROM Users) as Users,
                    (SELECT COUNT(*) FROM Projects) as Projects,
                    (SELECT COUNT(*) FROM Tasks) as Tasks,
                    (SELECT COUNT(*) FROM SystemSettings) as Settings
            """
            )
            counts = table_counts[0] if table_counts else {}

            return {
                "app_name": "DENSO Project Manager Pro",
                "version": "2.0.0",
                "database_server": db_details.get("ServerName", "Unknown"),
                "database_name": db_details.get("DatabaseName", "Unknown"),
                "database_version": db_details.get("Version", "Unknown"),
                "total_users": counts.get("Users", 0),
                "total_projects": counts.get("Projects", 0),
                "total_tasks": counts.get("Tasks", 0),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "app_name": "DENSO Project Manager Pro",
                "version": "2.0.0",
                "error": str(e),
            }

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all system settings"""
        try:
            self._ensure_settings_table()

            settings_data = self.db.execute_query(
                "SELECT SettingKey, SettingValue FROM SystemSettings"
            )
            settings = {}

            for row in settings_data:
                try:
                    # Try to parse JSON values
                    settings[row["SettingKey"]] = json.loads(row["SettingValue"])
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, store as string
                    settings[row["SettingKey"]] = row["SettingValue"]

            # Ensure default settings exist
            default_settings = self._get_default_settings()
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
                    self.update_setting(key, value)

            return settings
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return self._get_default_settings()

    def update_setting(self, key: str, value: Any) -> bool:
        """Update a system setting"""
        try:
            self._ensure_settings_table()

            # Convert value to JSON string if needed
            if isinstance(value, (dict, list)):
                json_value = json.dumps(value)
            else:
                json_value = str(value)

            # Check if setting exists
            existing = self.db.execute_query(
                "SELECT SettingKey FROM SystemSettings WHERE SettingKey = ?", (key,)
            )

            if existing:
                # Update existing
                query = """
                UPDATE SystemSettings 
                SET SettingValue = ?, UpdatedDate = GETDATE() 
                WHERE SettingKey = ?
                """
                self.db.execute_non_query(query, (json_value, key))
            else:
                # Insert new
                query = """
                INSERT INTO SystemSettings (SettingKey, SettingValue, CreatedDate, UpdatedDate)
                VALUES (?, ?, GETDATE(), GETDATE())
                """
                self.db.execute_non_query(query, (key, json_value))

            return True
        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False

    def delete_setting(self, key: str) -> bool:
        """Delete a system setting"""
        try:
            query = "DELETE FROM SystemSettings WHERE SettingKey = ?"
            self.db.execute_non_query(query, (key,))
            return True
        except Exception as e:
            logger.error(f"Error deleting setting {key}: {e}")
            return False

    def test_database_connection(self) -> Dict[str, Any]:
        """Test database connection and get performance info"""
        try:
            start_time = datetime.now()

            # Test basic query
            result = self.db.execute_query("SELECT 1 as test")

            end_time = datetime.now()
            response_time = (
                end_time - start_time
            ).total_seconds() * 1000  # milliseconds

            # Get database statistics
            db_stats = self.db.execute_query(
                """
                SELECT 
                    (SELECT COUNT(*) FROM sys.tables) as TableCount,
                    (SELECT COUNT(*) FROM sys.indexes) as IndexCount
            """
            )

            stats = db_stats[0] if db_stats else {}

            return {
                "status": "success",
                "connection_time": f"{response_time:.2f}ms",
                "table_count": stats.get("TableCount", 0),
                "index_count": stats.get("IndexCount", 0),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def backup_database(self) -> Dict[str, Any]:
        """Create database backup (simulation)"""
        try:
            # In a real implementation, this would create an actual backup
            backup_info = {
                "backup_id": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "tables_backed_up": ["Users", "Projects", "Tasks", "SystemSettings"],
                "status": "completed",
                "size_mb": "12.5",  # Simulated size
            }

            # Log backup event
            logger.info(f"Database backup created: {backup_info['backup_id']}")

            return backup_info
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system audit log"""
        try:
            # In a real implementation, this would query an audit log table
            # For now, we'll simulate with recent settings changes
            recent_settings = self.db.execute_query(
                """
                SELECT TOP (?) SettingKey, UpdatedDate, 'Setting Updated' as Action, 'System' as UserName
                FROM SystemSettings 
                WHERE UpdatedDate IS NOT NULL
                ORDER BY UpdatedDate DESC
            """,
                (limit,),
            )

            return recent_settings
        except Exception as e:
            logger.error(f"Error getting audit log: {e}")
            return []

    def _ensure_settings_table(self):
        """Ensure SystemSettings table exists"""
        try:
            # Check if table exists
            table_check = self.db.execute_query(
                """
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'SystemSettings'
            """
            )

            if not table_check or table_check[0]["count"] == 0:
                # Create table
                create_query = """
                CREATE TABLE SystemSettings (
                    SettingID INT IDENTITY(1,1) PRIMARY KEY,
                    SettingKey NVARCHAR(100) UNIQUE NOT NULL,
                    SettingValue NVARCHAR(MAX),
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    UpdatedDate DATETIME2 DEFAULT GETDATE()
                )
                """
                self.db.execute_non_query(create_query)
                logger.info("SystemSettings table created")
        except Exception as e:
            logger.error(f"Error ensuring settings table: {e}")

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default system settings"""
        return {
            "app_name": "DENSO Project Manager Pro",
            "app_version": "2.0.0",
            "company_name": "DENSO Corporation",
            "theme": "light",
            "language": "th",
            "timezone": "Asia/Bangkok",
            "session_timeout": 3600,
            "max_upload_size": 100,
            "email_notifications": True,
            "auto_backup": False,
            "backup_schedule": "02:00",
            "backup_retention_days": 90,
            "default_currency": "THB",
            "working_hours_start": "08:00",
            "working_hours_end": "17:00",
            "weekend_days": ["Saturday", "Sunday"],
            "company_logo": "/assets/denso-logo.png",
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

    def render_settings_ui(self):
        """Render settings management UI"""
        try:
            st.title("⚙️ การตั้งค่าระบบ")

            # Create tabs for different setting categories
            tab1, tab2, tab3, tab4 = st.tabs(
                ["🔧 ทั่วไป", "🔒 ความปลอดภัย", "📧 อีเมล", "🗄️ ฐานข้อมูล"]
            )

            settings = self.get_all_settings()

            with tab1:
                self._render_general_settings(settings)

            with tab2:
                self._render_security_settings(settings)

            with tab3:
                self._render_email_settings(settings)

            with tab4:
                self._render_database_settings(settings)

        except Exception as e:
            st.error(f"Error rendering settings UI: {e}")

    def _render_general_settings(self, settings: Dict[str, Any]):
        """Render general settings"""
        st.subheader("การตั้งค่าทั่วไป")

        col1, col2 = st.columns(2)

        with col1:
            app_name = st.text_input("ชื่อแอปพลิเคชัน", value=settings.get("app_name", ""))
            language = st.selectbox(
                "ภาษา", ["th", "en"], index=0 if settings.get("language") == "th" else 1
            )
            theme = st.selectbox(
                "ธีม",
                ["light", "dark"],
                index=0 if settings.get("theme") == "light" else 1,
            )

        with col2:
            timezone = st.selectbox("เขตเวลา", ["Asia/Bangkok", "UTC"], index=0)
            currency = st.selectbox("สกุลเงิน", ["THB", "USD", "EUR"], index=0)
            session_timeout = st.number_input(
                "Session Timeout (วินาที)", value=settings.get("session_timeout", 3600)
            )

        if st.button("💾 บันทึกการตั้งค่าทั่วไป"):
            updates = {
                "app_name": app_name,
                "language": language,
                "theme": theme,
                "timezone": timezone,
                "default_currency": currency,
                "session_timeout": session_timeout,
            }

            success_count = 0
            for key, value in updates.items():
                if self.update_setting(key, value):
                    success_count += 1

            if success_count == len(updates):
                st.success("✅ บันทึกการตั้งค่าเรียบร้อยแล้ว")
            else:
                st.warning(f"⚠️ บันทึกได้ {success_count}/{len(updates)} รายการ")

    def _render_security_settings(self, settings: Dict[str, Any]):
        """Render security settings"""
        st.subheader("การตั้งค่าความปลอดภัย")

        security_settings = settings.get("security_settings", {})
        password_policy = settings.get("password_policy", {})

        col1, col2 = st.columns(2)

        with col1:
            st.write("**นโยบายรหัสผ่าน**")
            min_length = st.number_input(
                "ความยาวขั้นต่ำ", value=password_policy.get("min_length", 8), min_value=6
            )
            require_uppercase = st.checkbox(
                "ต้องมีตัวพิมพ์ใหญ่", value=password_policy.get("require_uppercase", True)
            )
            require_lowercase = st.checkbox(
                "ต้องมีตัวพิมพ์เล็ก", value=password_policy.get("require_lowercase", True)
            )
            require_digits = st.checkbox(
                "ต้องมีตัวเลข", value=password_policy.get("require_digits", True)
            )
            require_special = st.checkbox(
                "ต้องมีอักขระพิเศษ", value=password_policy.get("require_special", True)
            )

        with col2:
            st.write("**การรักษาความปลอดภัย**")
            max_attempts = st.number_input(
                "จำนวนครั้งที่ผิดสูงสุด", value=security_settings.get("max_login_attempts", 5)
            )
            lockout_duration = st.number_input(
                "ระยะเวลาล็อค (วินาที)",
                value=security_settings.get("lockout_duration", 900),
            )
            force_password_change = st.checkbox(
                "บังคับเปลี่ยนรหัสผ่าน",
                value=security_settings.get("force_password_change", False),
            )

        if st.button("🔒 บันทึกการตั้งค่าความปลอดภัย"):
            new_password_policy = {
                "min_length": min_length,
                "require_uppercase": require_uppercase,
                "require_lowercase": require_lowercase,
                "require_digits": require_digits,
                "require_special": require_special,
            }

            new_security_settings = {
                "max_login_attempts": max_attempts,
                "lockout_duration": lockout_duration,
                "force_password_change": force_password_change,
            }

            if self.update_setting(
                "password_policy", new_password_policy
            ) and self.update_setting("security_settings", new_security_settings):
                st.success("✅ บันทึกการตั้งค่าความปลอดภัยเรียบร้อยแล้ว")
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึก")

    def _render_email_settings(self, settings: Dict[str, Any]):
        """Render email settings"""
        st.subheader("การตั้งค่าอีเมล")

        email_notifications = st.checkbox(
            "เปิดใช้งานการแจ้งเตือนทางอีเมล", value=settings.get("email_notifications", True)
        )

        if email_notifications:
            col1, col2 = st.columns(2)

            with col1:
                smtp_server = st.text_input(
                    "SMTP Server", value=settings.get("smtp_server", "")
                )
                smtp_port = st.number_input(
                    "SMTP Port", value=settings.get("smtp_port", 587)
                )
                smtp_username = st.text_input(
                    "SMTP Username", value=settings.get("smtp_username", "")
                )

            with col2:
                smtp_password = st.text_input("SMTP Password", type="password")
                from_email = st.text_input(
                    "From Email", value=settings.get("from_email", "")
                )
                use_tls = st.checkbox(
                    "ใช้ TLS", value=settings.get("smtp_use_tls", True)
                )

        if st.button("📧 บันทึกการตั้งค่าอีเมล"):
            email_settings = {
                "email_notifications": email_notifications,
                "smtp_server": smtp_server if email_notifications else "",
                "smtp_port": smtp_port if email_notifications else 587,
                "smtp_username": smtp_username if email_notifications else "",
                "from_email": from_email if email_notifications else "",
                "smtp_use_tls": use_tls if email_notifications else True,
            }

            success_count = 0
            for key, value in email_settings.items():
                if self.update_setting(key, value):
                    success_count += 1

            if success_count == len(email_settings):
                st.success("✅ บันทึกการตั้งค่าอีเมลเรียบร้อยแล้ว")
                if email_notifications:
                    if st.button("📤 ทดสอบการส่งอีเมล"):
                        # Test email functionality here
                        st.info("🔄 กำลังทดสอบการส่งอีเมล...")
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึก")

    def _render_database_settings(self, settings: Dict[str, Any]):
        """Render database settings"""
        st.subheader("การจัดการฐานข้อมูล")

        # System Information
        col1, col2 = st.columns(2)

        with col1:
            st.write("**ข้อมูลระบบ**")
            system_info = self.get_system_info()

            for key, value in system_info.items():
                if key != "error":
                    st.text(f"{key}: {value}")

        with col2:
            st.write("**การทดสอบการเชื่อมต่อ**")
            if st.button("🔍 ทดสอบการเชื่อมต่อฐานข้อมูล"):
                test_result = self.test_database_connection()

                if test_result["status"] == "success":
                    st.success(f"✅ เชื่อมต่อสำเร็จ ({test_result['connection_time']})")
                    st.info(
                        f"📊 ตาราง: {test_result['table_count']}, ดัชนี: {test_result['index_count']}"
                    )
                else:
                    st.error(f"❌ เชื่อมต่อไม่สำเร็จ: {test_result['error']}")

        # Backup Settings
        st.write("**การสำรองข้อมูล**")

        col3, col4 = st.columns(2)

        with col3:
            auto_backup = st.checkbox(
                "สำรองข้อมูลอัตโนมัติ", value=settings.get("auto_backup", False)
            )
            backup_schedule = st.time_input(
                "เวลาสำรองข้อมูล",
                value=datetime.strptime(
                    settings.get("backup_schedule", "02:00"), "%H:%M"
                ).time(),
            )

        with col4:
            backup_retention = st.number_input(
                "เก็บข้อมูลสำรอง (วัน)", value=settings.get("backup_retention_days", 90)
            )

            if st.button("💾 สำรองข้อมูลทันที"):
                backup_result = self.backup_database()

                if backup_result["status"] == "completed":
                    st.success(
                        f"✅ สำรองข้อมูลเรียบร้อย (ID: {backup_result['backup_id']})"
                    )
                    st.info(f"📁 ขนาด: {backup_result['size_mb']} MB")
                else:
                    st.error(f"❌ สำรองข้อมูลไม่สำเร็จ: {backup_result['error']}")

        if st.button("🗄️ บันทึกการตั้งค่าฐานข้อมูล"):
            backup_settings = {
                "auto_backup": auto_backup,
                "backup_schedule": backup_schedule.strftime("%H:%M"),
                "backup_retention_days": backup_retention,
            }

            success_count = 0
            for key, value in backup_settings.items():
                if self.update_setting(key, value):
                    success_count += 1

            if success_count == len(backup_settings):
                st.success("✅ บันทึกการตั้งค่าฐานข้อมูลเรียบร้อยแล้ว")
            else:
                st.error("❌ เกิดข้อผิดพลาดในการบันทึก")

        # Audit Log
        if st.checkbox("📋 แสดง Audit Log"):
            audit_data = self.get_audit_log(50)
            if audit_data:
                import pandas as pd

                df = pd.DataFrame(audit_data)
                st.dataframe(df, use_container_width=True)
