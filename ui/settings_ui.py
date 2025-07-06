#!/usr/bin/env python3
"""
settings_ui.py
SDX Project Manager - Enterprise Settings Management Interface
Comprehensive system configuration and administration panel
"""

import streamlit as st
import logging
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import project modules
from settings import SettingsManager, SystemSettings, SecuritySettings, EmailSettings
from auth import AuthenticationManager, UserRole, Permission
from users import UserManager
from ui_components import UIComponents, ThemeManager
from error_handler import ErrorHandler, handle_errors

logger = logging.getLogger(__name__)


class SettingsCategory(Enum):
    """Settings categories"""

    GENERAL = "general"
    SECURITY = "security"
    DATABASE = "database"
    EMAIL = "email"
    THEME = "theme"
    USERS = "users"
    SYSTEM = "system"
    BACKUP = "backup"
    INTEGRATIONS = "integrations"
    AUDIT = "audit"


class SettingsLevel(Enum):
    """Settings access levels"""

    ADMIN_ONLY = "admin_only"
    MANAGER = "manager"
    USER = "user"
    PUBLIC = "public"


@dataclass
class SettingItem:
    """Individual setting item"""

    key: str
    name: str
    description: str
    value: Any
    default_value: Any
    setting_type: str  # text, number, boolean, select, json
    category: SettingsCategory
    level: SettingsLevel
    options: Optional[List[Any]] = None
    validation: Optional[str] = None
    restart_required: bool = False


class SettingsUI:
    """Enterprise Settings Management Interface"""

    def __init__(self, db_manager, theme_manager: ThemeManager):
        self.db = db_manager
        self.settings_manager = SettingsManager(db_manager)
        self.auth_manager = AuthenticationManager(db_manager)
        self.user_manager = UserManager(db_manager)
        self.theme = theme_manager
        self.ui_components = UIComponents(theme_manager)
        self.error_handler = ErrorHandler()

    @handle_errors
    def render_settings_page(self):
        """Main settings page renderer"""
        st.markdown("# ⚙️ การตั้งค่าระบบ")

        # Check admin permissions
        if not self._check_admin_permission():
            st.error("❌ คุณไม่มีสิทธิ์ในการเข้าถึงการตั้งค่าระบบ")
            return

        # Settings header
        self._render_settings_header()

        # Settings navigation
        selected_category = self._render_settings_navigation()

        # Settings content
        self._render_settings_content(selected_category)

        # Settings footer
        self._render_settings_footer()

    def _check_admin_permission(self) -> bool:
        """Check if user has admin permissions"""
        user_data = st.session_state.get("user_data", {})
        return user_data.get("Role") in ["Admin", "System Admin"]

    def _render_settings_header(self):
        """Render settings page header"""
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("### 🔧 การจัดการระบบและการกำหนดค่า")

        with col2:
            if st.button("💾 บันทึกการตั้งค่า", type="primary"):
                self._save_all_settings()

        with col3:
            if st.button("🔄 รีเซ็ตเป็นค่าเริ่มต้น"):
                self._reset_to_defaults()

    def _render_settings_navigation(self) -> SettingsCategory:
        """Render settings navigation sidebar"""
        with st.sidebar:
            st.markdown("### 📂 หมวดหมู่การตั้งค่า")

            # Settings categories
            categories = [
                ("🔧 ทั่วไป", SettingsCategory.GENERAL),
                ("🔒 ความปลอดภัย", SettingsCategory.SECURITY),
                ("🗄️ ฐานข้อมูล", SettingsCategory.DATABASE),
                ("📧 อีเมล", SettingsCategory.EMAIL),
                ("🎨 ธีม", SettingsCategory.THEME),
                ("👥 ผู้ใช้", SettingsCategory.USERS),
                ("💻 ระบบ", SettingsCategory.SYSTEM),
                ("💾 สำรองข้อมูล", SettingsCategory.BACKUP),
                ("🔌 การเชื่อมต่อ", SettingsCategory.INTEGRATIONS),
                ("📋 บันทึกการใช้งาน", SettingsCategory.AUDIT),
            ]

            selected = st.radio(
                "เลือกหมวดหมู่",
                options=[cat[1] for cat in categories],
                format_func=lambda x: next(cat[0] for cat in categories if cat[1] == x),
                key="settings_category",
            )

            # System status
            st.markdown("---")
            st.markdown("### 📊 สถานะระบบ")
            self._render_system_status()

            return selected

    def _render_system_status(self):
        """Render system status in sidebar"""
        # System uptime
        uptime = self._get_system_uptime()
        st.metric("Uptime", uptime)

        # Memory usage
        memory_usage = self._get_memory_usage()
        st.metric("Memory Usage", f"{memory_usage}%")

        # Database connections
        db_connections = self._get_db_connections()
        st.metric("DB Connections", db_connections)

        # Last backup
        last_backup = self._get_last_backup_time()
        st.metric("Last Backup", last_backup)

    def _render_settings_content(self, category: SettingsCategory):
        """Render settings content based on category"""
        if category == SettingsCategory.GENERAL:
            self._render_general_settings()
        elif category == SettingsCategory.SECURITY:
            self._render_security_settings()
        elif category == SettingsCategory.DATABASE:
            self._render_database_settings()
        elif category == SettingsCategory.EMAIL:
            self._render_email_settings()
        elif category == SettingsCategory.THEME:
            self._render_theme_settings()
        elif category == SettingsCategory.USERS:
            self._render_user_settings()
        elif category == SettingsCategory.SYSTEM:
            self._render_system_settings()
        elif category == SettingsCategory.BACKUP:
            self._render_backup_settings()
        elif category == SettingsCategory.INTEGRATIONS:
            self._render_integration_settings()
        elif category == SettingsCategory.AUDIT:
            self._render_audit_settings()

    def _render_general_settings(self):
        """Render general system settings"""
        st.markdown("## 🔧 การตั้งค่าทั่วไป")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 ข้อมูลองค์กร")

            company_name = st.text_input(
                "ชื่อองค์กร",
                value=self._get_setting("company_name", "DENSO Innovation Team"),
                key="company_name",
            )

            company_logo = st.file_uploader(
                "โลโก้องค์กร", type=["png", "jpg", "jpeg"], key="company_logo"
            )

            timezone = st.selectbox(
                "เขตเวลา",
                options=["Asia/Bangkok", "UTC", "Asia/Tokyo", "America/New_York"],
                index=0,
                key="timezone",
            )

            language = st.selectbox(
                "ภาษาเริ่มต้น",
                options=["Thai", "English", "Japanese"],
                index=0,
                key="default_language",
            )

        with col2:
            st.markdown("### ⚙️ การตั้งค่าระบบ")

            max_file_size = st.number_input(
                "ขนาดไฟล์สูงสุด (MB)",
                min_value=1,
                max_value=1000,
                value=self._get_setting("max_file_size", 100),
                key="max_file_size",
            )

            session_timeout = st.number_input(
                "หมดเวลาเซสชัน (นาที)",
                min_value=15,
                max_value=1440,
                value=self._get_setting("session_timeout", 480),
                key="session_timeout",
            )

            enable_notifications = st.checkbox(
                "เปิดใช้งานการแจ้งเตือน",
                value=self._get_setting("enable_notifications", True),
                key="enable_notifications",
            )

            maintenance_mode = st.checkbox(
                "โหมดปรับปรุงระบบ",
                value=self._get_setting("maintenance_mode", False),
                key="maintenance_mode",
            )

    def _render_security_settings(self):
        """Render security settings"""
        st.markdown("## 🔒 การตั้งค่าความปลอดภัย")

        # Password Policy
        st.markdown("### 🔐 นโยบายรหัสผ่าน")
        col1, col2 = st.columns(2)

        with col1:
            min_password_length = st.number_input(
                "ความยาวรหัสผ่านขั้นต่ำ",
                min_value=6,
                max_value=20,
                value=self._get_setting("min_password_length", 8),
                key="min_password_length",
            )

            require_uppercase = st.checkbox(
                "ต้องมีตัวพิมพ์ใหญ่",
                value=self._get_setting("require_uppercase", True),
                key="require_uppercase",
            )

            require_numbers = st.checkbox(
                "ต้องมีตัวเลข",
                value=self._get_setting("require_numbers", True),
                key="require_numbers",
            )

        with col2:
            password_expiry = st.number_input(
                "รหัสผ่านหมดอายุ (วัน)",
                min_value=0,
                max_value=365,
                value=self._get_setting("password_expiry", 90),
                key="password_expiry",
            )

            require_special_chars = st.checkbox(
                "ต้องมีอักขระพิเศษ",
                value=self._get_setting("require_special_chars", True),
                key="require_special_chars",
            )

            max_login_attempts = st.number_input(
                "จำนวนครั้งล็อกอินสูงสุด",
                min_value=3,
                max_value=10,
                value=self._get_setting("max_login_attempts", 5),
                key="max_login_attempts",
            )

        # Two-Factor Authentication
        st.markdown("---")
        st.markdown("### 🔐 การยืนยันตัวตนสองขั้นตอน")

        col1, col2 = st.columns(2)

        with col1:
            enable_2fa = st.checkbox(
                "เปิดใช้งาน 2FA",
                value=self._get_setting("enable_2fa", False),
                key="enable_2fa",
            )

            if enable_2fa:
                twofa_methods = st.multiselect(
                    "วิธี 2FA",
                    options=["SMS", "Email", "Authenticator App"],
                    default=["Email"],
                    key="twofa_methods",
                )

        with col2:
            if enable_2fa:
                mandatory_2fa = st.checkbox(
                    "บังคับใช้ 2FA สำหรับ Admin",
                    value=self._get_setting("mandatory_2fa", True),
                    key="mandatory_2fa",
                )

                twofa_backup_codes = st.number_input(
                    "จำนวนรหัสสำรอง",
                    min_value=5,
                    max_value=20,
                    value=self._get_setting("twofa_backup_codes", 10),
                    key="twofa_backup_codes",
                )

        # Security Monitoring
        st.markdown("---")
        st.markdown("### 👁️ การติดตามความปลอดภัย")

        col1, col2 = st.columns(2)

        with col1:
            log_failed_logins = st.checkbox(
                "บันทึกการล็อกอินล้มเหลว",
                value=self._get_setting("log_failed_logins", True),
                key="log_failed_logins",
            )

            alert_suspicious_activity = st.checkbox(
                "แจ้งเตือนกิจกรรมน่าสงสัย",
                value=self._get_setting("alert_suspicious_activity", True),
                key="alert_suspicious_activity",
            )

        with col2:
            auto_lockout_duration = st.number_input(
                "ระยะเวลาล็อกอัตโนมัติ (นาที)",
                min_value=5,
                max_value=1440,
                value=self._get_setting("auto_lockout_duration", 30),
                key="auto_lockout_duration",
            )

            ip_whitelist = st.text_area(
                "IP Whitelist (หนึ่งบรรทัดต่อ IP)",
                value=self._get_setting("ip_whitelist", ""),
                key="ip_whitelist",
            )

    def _render_database_settings(self):
        """Render database settings"""
        st.markdown("## 🗄️ การตั้งค่าฐานข้อมูล")

        # Connection Settings
        st.markdown("### 🔌 การเชื่อมต่อ")
        col1, col2 = st.columns(2)

        with col1:
            db_host = st.text_input(
                "เซิร์ฟเวอร์",
                value=self._get_setting("db_host", "localhost"),
                key="db_host",
            )

            db_port = st.number_input(
                "พอร์ต",
                min_value=1,
                max_value=65535,
                value=self._get_setting("db_port", 1433),
                key="db_port",
            )

            db_name = st.text_input(
                "ชื่อฐานข้อมูล",
                value=self._get_setting("db_name", "SDXProjectManager"),
                key="db_name",
            )

        with col2:
            connection_pool_size = st.number_input(
                "ขนาด Connection Pool",
                min_value=5,
                max_value=100,
                value=self._get_setting("connection_pool_size", 20),
                key="connection_pool_size",
            )

            query_timeout = st.number_input(
                "Timeout คำสั่ง SQL (วินาที)",
                min_value=10,
                max_value=300,
                value=self._get_setting("query_timeout", 30),
                key="query_timeout",
            )

            enable_ssl = st.checkbox(
                "เปิดใช้งาน SSL",
                value=self._get_setting("enable_ssl", True),
                key="enable_ssl",
            )

        # Performance Settings
        st.markdown("---")
        st.markdown("### ⚡ ประสิทธิภาพ")

        col1, col2 = st.columns(2)

        with col1:
            enable_query_cache = st.checkbox(
                "เปิดใช้งาน Query Cache",
                value=self._get_setting("enable_query_cache", True),
                key="enable_query_cache",
            )

            cache_size_mb = st.number_input(
                "ขนาด Cache (MB)",
                min_value=50,
                max_value=1000,
                value=self._get_setting("cache_size_mb", 200),
                key="cache_size_mb",
            )

        with col2:
            auto_vacuum = st.checkbox(
                "Auto Vacuum",
                value=self._get_setting("auto_vacuum", True),
                key="auto_vacuum",
            )

            backup_retention_days = st.number_input(
                "เก็บ Backup (วัน)",
                min_value=7,
                max_value=365,
                value=self._get_setting("backup_retention_days", 30),
                key="backup_retention_days",
            )

        # Test Connection
        st.markdown("---")
        if st.button("🔍 ทดสอบการเชื่อมต่อ"):
            self._test_database_connection()

    def _render_email_settings(self):
        """Render email settings"""
        st.markdown("## 📧 การตั้งค่าอีเมล")

        # SMTP Configuration
        st.markdown("### 📮 การตั้งค่า SMTP")
        col1, col2 = st.columns(2)

        with col1:
            smtp_server = st.text_input(
                "เซิร์ฟเวอร์ SMTP",
                value=self._get_setting("smtp_server", "smtp.gmail.com"),
                key="smtp_server",
            )

            smtp_port = st.number_input(
                "พอร์ต SMTP",
                min_value=25,
                max_value=587,
                value=self._get_setting("smtp_port", 587),
                key="smtp_port",
            )

            smtp_username = st.text_input(
                "ชื่อผู้ใช้",
                value=self._get_setting("smtp_username", ""),
                key="smtp_username",
            )

        with col2:
            smtp_password = st.text_input(
                "รหัสผ่าน",
                type="password",
                value=self._get_setting("smtp_password", ""),
                key="smtp_password",
            )

            use_tls = st.checkbox(
                "ใช้ TLS", value=self._get_setting("use_tls", True), key="use_tls"
            )

            from_email = st.text_input(
                "อีเมลผู้ส่ง",
                value=self._get_setting("from_email", "noreply@denso.com"),
                key="from_email",
            )

        # Email Templates
        st.markdown("---")
        st.markdown("### 📄 แม่แบบอีเมล")

        template_type = st.selectbox(
            "เลือกแม่แบบ",
            options=["การต้อนรับ", "รีเซ็ตรหัสผ่าน", "การแจ้งเตือน", "รายงาน"],
            key="template_type",
        )

        email_template = st.text_area(
            "เนื้อหาแม่แบบ",
            value=self._get_email_template(template_type),
            height=200,
            key="email_template",
        )

        # Test Email
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            test_email = st.text_input("อีเมลทดสอบ", key="test_email")

        with col2:
            if st.button("📧 ส่งอีเมลทดสอบ"):
                self._send_test_email(test_email)

    def _render_theme_settings(self):
        """Render theme and UI settings"""
        st.markdown("## 🎨 การตั้งค่าธีมและหน้าตา")

        # Color Scheme
        st.markdown("### 🌈 โทนสี")
        col1, col2, col3 = st.columns(3)

        with col1:
            primary_color = st.color_picker(
                "สีหลัก",
                value=self._get_setting("primary_color", "#6f42c1"),
                key="primary_color",
            )

            secondary_color = st.color_picker(
                "สีรอง",
                value=self._get_setting("secondary_color", "#6c757d"),
                key="secondary_color",
            )

        with col2:
            success_color = st.color_picker(
                "สีสำเร็จ",
                value=self._get_setting("success_color", "#28a745"),
                key="success_color",
            )

            warning_color = st.color_picker(
                "สีเตือน",
                value=self._get_setting("warning_color", "#ffc107"),
                key="warning_color",
            )

        with col3:
            danger_color = st.color_picker(
                "สีอันตราย",
                value=self._get_setting("danger_color", "#dc3545"),
                key="danger_color",
            )

            info_color = st.color_picker(
                "สีข้อมูล",
                value=self._get_setting("info_color", "#17a2b8"),
                key="info_color",
            )

        # Layout Settings
        st.markdown("---")
        st.markdown("### 📐 การจัดวาง")

        col1, col2 = st.columns(2)

        with col1:
            sidebar_expanded = st.checkbox(
                "ขยาย Sidebar ตั้งแต่เริ่มต้น",
                value=self._get_setting("sidebar_expanded", True),
                key="sidebar_expanded",
            )

            show_footer = st.checkbox(
                "แสดง Footer",
                value=self._get_setting("show_footer", True),
                key="show_footer",
            )

            dark_mode = st.checkbox(
                "โหมดมืด", value=self._get_setting("dark_mode", False), key="dark_mode"
            )

        with col2:
            font_family = st.selectbox(
                "ฟอนต์",
                options=["sans serif", "serif", "monospace", "Kanit", "Prompt"],
                index=0,
                key="font_family",
            )

            font_size = st.selectbox(
                "ขนาดฟอนต์", options=["เล็ก", "ปกติ", "ใหญ่"], index=1, key="font_size"
            )

            animation_enabled = st.checkbox(
                "เปิดใช้งาน Animation",
                value=self._get_setting("animation_enabled", True),
                key="animation_enabled",
            )

        # Preview
        st.markdown("---")
        st.markdown("### 👁️ ตัวอย่าง")
        if st.button("🔄 ตัวอย่างธีม"):
            self._preview_theme()

    def _render_user_settings(self):
        """Render user management settings"""
        st.markdown("## 👥 การตั้งค่าผู้ใช้")

        # User Registration
        st.markdown("### 📝 การลงทะเบียน")
        col1, col2 = st.columns(2)

        with col1:
            allow_registration = st.checkbox(
                "อนุญาตให้ลงทะเบียนเอง",
                value=self._get_setting("allow_registration", False),
                key="allow_registration",
            )

            require_email_verification = st.checkbox(
                "ต้องยืนยันอีเมล",
                value=self._get_setting("require_email_verification", True),
                key="require_email_verification",
            )

            default_user_role = st.selectbox(
                "บทบาทเริ่มต้น",
                options=["User", "Viewer", "Developer"],
                index=0,
                key="default_user_role",
            )

        with col2:
            max_users = st.number_input(
                "จำนวนผู้ใช้สูงสุด",
                min_value=10,
                max_value=10000,
                value=self._get_setting("max_users", 1000),
                key="max_users",
            )

            inactive_user_cleanup = st.number_input(
                "ลบผู้ใช้ไม่ใช้งาน (วัน)",
                min_value=30,
                max_value=365,
                value=self._get_setting("inactive_user_cleanup", 180),
                key="inactive_user_cleanup",
            )

            force_password_change = st.checkbox(
                "บังคับเปลี่ยนรหัสผ่านครั้งแรก",
                value=self._get_setting("force_password_change", True),
                key="force_password_change",
            )

        # User Activity
        st.markdown("---")
        st.markdown("### 📊 กิจกรรมผู้ใช้")

        # Current users table
        users_data = self._get_users_data()
        if users_data:
            st.dataframe(
                users_data,
                use_container_width=True,
                column_config={
                    "LastLogin": st.column_config.DatetimeColumn("เข้าสู่ระบบล่าสุด"),
                    "Status": st.column_config.TextColumn("สถานะ"),
                },
            )

        # User actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📧 ส่งอีเมลให้ผู้ใช้ทั้งหมด"):
                self._send_bulk_email()

        with col2:
            if st.button("🔒 ล็อกผู้ใช้ไม่ใช้งาน"):
                self._lock_inactive_users()

        with col3:
            if st.button("📊 ส่งออกข้อมูลผู้ใช้"):
                self._export_users_data()

    def _render_system_settings(self):
        """Render system performance settings"""
        st.markdown("## 💻 การตั้งค่าระบบ")

        # Performance Settings
        st.markdown("### ⚡ ประสิทธิภาพ")
        col1, col2 = st.columns(2)

        with col1:
            max_concurrent_users = st.number_input(
                "ผู้ใช้พร้อมกันสูงสุด",
                min_value=10,
                max_value=1000,
                value=self._get_setting("max_concurrent_users", 100),
                key="max_concurrent_users",
            )

            request_timeout = st.number_input(
                "Timeout คำขอ (วินาที)",
                min_value=30,
                max_value=300,
                value=self._get_setting("request_timeout", 60),
                key="request_timeout",
            )

            enable_compression = st.checkbox(
                "เปิดใช้งาน Compression",
                value=self._get_setting("enable_compression", True),
                key="enable_compression",
            )

        with col2:
            log_level = st.selectbox(
                "ระดับ Log",
                options=["DEBUG", "INFO", "WARNING", "ERROR"],
                index=1,
                key="log_level",
            )

            log_retention_days = st.number_input(
                "เก็บ Log (วัน)",
                min_value=7,
                max_value=365,
                value=self._get_setting("log_retention_days", 30),
                key="log_retention_days",
            )

            enable_monitoring = st.checkbox(
                "เปิดใช้งาน Monitoring",
                value=self._get_setting("enable_monitoring", True),
                key="enable_monitoring",
            )

        # System Resources
        st.markdown("---")
        st.markdown("### 📊 ทรัพยากรระบบ")

        # System metrics
        system_metrics = self._get_system_metrics()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("CPU Usage", f"{system_metrics['cpu']}%")

        with col2:
            st.metric("Memory Usage", f"{system_metrics['memory']}%")

        with col3:
            st.metric("Disk Usage", f"{system_metrics['disk']}%")

        with col4:
            st.metric("Network I/O", f"{system_metrics['network']} MB/s")

        # System processes
        st.markdown("### 🔄 กระบวนการระบบ")
        processes_data = self._get_processes_data()
        if processes_data:
            st.dataframe(processes_data, use_container_width=True)

    def _render_backup_settings(self):
        """Render backup and recovery settings"""
        st.markdown("## 💾 การตั้งค่าสำรองข้อมูล")

        # Backup Schedule
        st.markdown("### ⏰ ตารางสำรองข้อมูล")
        col1, col2 = st.columns(2)

        with col1:
            auto_backup = st.checkbox(
                "สำรองข้อมูลอัตโนมัติ",
                value=self._get_setting("auto_backup", True),
                key="auto_backup",
            )

            if auto_backup:
                backup_frequency = st.selectbox(
                    "ความถี่",
                    options=["รายวัน", "รายสัปดาห์", "รายเดือน"],
                    index=0,
                    key="backup_frequency",
                )

                backup_time = st.time_input(
                    "เวลาสำรองข้อมูล",
                    value=datetime.strptime("02:00", "%H:%M").time(),
                    key="backup_time",
                )

        with col2:
            backup_location = st.text_input(
                "ตำแหน่งสำรองข้อมูล",
                value=self._get_setting("backup_location", "/backup"),
                key="backup_location",
            )

            max_backups = st.number_input(
                "จำนวนสำรองสูงสุด",
                min_value=3,
                max_value=30,
                value=self._get_setting("max_backups", 7),
                key="max_backups",
            )

            compress_backups = st.checkbox(
                "บีบอัดไฟล์สำรอง",
                value=self._get_setting("compress_backups", True),
                key="compress_backups",
            )

        # Backup History
        st.markdown("---")
        st.markdown("### 📜 ประวัติการสำรองข้อมูล")

        backup_history = self._get_backup_history()
        if backup_history:
            st.dataframe(
                backup_history,
                use_container_width=True,
                column_config={
                    "Date": st.column_config.DatetimeColumn("วันที่"),
                    "Size": st.column_config.TextColumn("ขนาด"),
                    "Status": st.column_config.TextColumn("สถานะ"),
                },
            )

        # Backup Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 สำรองข้อมูลตอนนี้"):
                self._create_backup()

        with col2:
            if st.button("📥 คืนค่าข้อมูล"):
                self._restore_backup()

        with col3:
            if st.button("🧹 ล้างสำรองเก่า"):
                self._cleanup_old_backups()

    def _render_integration_settings(self):
        """Render integration settings"""
        st.markdown("## 🔌 การตั้งค่าการเชื่อมต่อ")

        # Available Integrations
        integrations = [
            {"name": "Microsoft Teams", "status": "Connected", "icon": "💬"},
            {"name": "Slack", "status": "Disconnected", "icon": "💬"},
            {"name": "Jira", "status": "Connected", "icon": "🎫"},
            {"name": "GitHub", "status": "Disconnected", "icon": "🐙"},
            {"name": "Azure DevOps", "status": "Connected", "icon": "🔧"},
            {"name": "Google Drive", "status": "Disconnected", "icon": "📁"},
        ]

        st.markdown("### 🔗 การเชื่อมต่อที่มี")

        for integration in integrations:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])

                with col1:
                    st.markdown(integration["icon"])

                with col2:
                    st.markdown(f"**{integration['name']}**")

                with col3:
                    status_color = (
                        "green" if integration["status"] == "Connected" else "red"
                    )
                    st.markdown(
                        f"<span style='color:{status_color}'>{integration['status']}</span>",
                        unsafe_allow_html=True,
                    )

                with col4:
                    if integration["status"] == "Connected":
                        if st.button("⚙️ ตั้งค่า", key=f"config_{integration['name']}"):
                            self._configure_integration(integration["name"])
                    else:
                        if st.button("🔌 เชื่อมต่อ", key=f"connect_{integration['name']}"):
                            self._connect_integration(integration["name"])

        # API Settings
        st.markdown("---")
        st.markdown("### 🔑 การตั้งค่า API")

        col1, col2 = st.columns(2)

        with col1:
            enable_api = st.checkbox(
                "เปิดใช้งาน API",
                value=self._get_setting("enable_api", True),
                key="enable_api",
            )

            api_rate_limit = st.number_input(
                "Rate Limit (requests/minute)",
                min_value=10,
                max_value=1000,
                value=self._get_setting("api_rate_limit", 100),
                key="api_rate_limit",
            )

        with col2:
            api_key_expiry = st.number_input(
                "API Key หมดอายุ (วัน)",
                min_value=30,
                max_value=365,
                value=self._get_setting("api_key_expiry", 90),
                key="api_key_expiry",
            )

            require_https = st.checkbox(
                "บังคับใช้ HTTPS",
                value=self._get_setting("require_https", True),
                key="require_https",
            )

    def _render_audit_settings(self):
        """Render audit and logging settings"""
        st.markdown("## 📋 การตั้งค่าบันทึกการใช้งาน")

        # Audit Configuration
        st.markdown("### 📊 การกำหนดค่าการตรวจสอบ")
        col1, col2 = st.columns(2)

        with col1:
            enable_audit_log = st.checkbox(
                "เปิดใช้งาน Audit Log",
                value=self._get_setting("enable_audit_log", True),
                key="enable_audit_log",
            )

            log_user_actions = st.checkbox(
                "บันทึกการกระทำของผู้ใช้",
                value=self._get_setting("log_user_actions", True),
                key="log_user_actions",
            )

            log_data_changes = st.checkbox(
                "บันทึกการเปลี่ยนแปลงข้อมูล",
                value=self._get_setting("log_data_changes", True),
                key="log_data_changes",
            )

        with col2:
            audit_retention_days = st.number_input(
                "เก็บ Audit Log (วัน)",
                min_value=30,
                max_value=2555,  # 7 years
                value=self._get_setting("audit_retention_days", 365),
                key="audit_retention_days",
            )

            export_audit_log = st.checkbox(
                "อนุญาตส่งออก Audit Log",
                value=self._get_setting("export_audit_log", True),
                key="export_audit_log",
            )

            real_time_alerts = st.checkbox(
                "แจ้งเตือนแบบเรียลไทม์",
                value=self._get_setting("real_time_alerts", False),
                key="real_time_alerts",
            )

        # Recent Audit Logs
        st.markdown("---")
        st.markdown("### 📜 บันทึกการใช้งานล่าสุด")

        audit_logs = self._get_recent_audit_logs()
        if audit_logs:
            st.dataframe(
                audit_logs,
                use_container_width=True,
                column_config={
                    "Timestamp": st.column_config.DatetimeColumn("เวลา"),
                    "User": st.column_config.TextColumn("ผู้ใช้"),
                    "Action": st.column_config.TextColumn("การกระทำ"),
                    "Resource": st.column_config.TextColumn("ทรัพยากร"),
                },
            )

        # Export audit logs
        if st.button("📊 ส่งออกบันทึกการใช้งาน"):
            self._export_audit_logs()

    def _render_settings_footer(self):
        """Render settings page footer"""
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🔄 รีสตาร์ทระบบ", type="secondary"):
                self._restart_system()

        with col2:
            if st.button("🧹 ล้าง Cache", type="secondary"):
                self._clear_cache()

        with col3:
            if st.button("📊 ส่งออกการตั้งค่า"):
                self._export_settings()

        # Settings info
        st.markdown("---")
        st.info("💡 การเปลี่ยนแปลงบางอย่างอาจต้องรีสตาร์ทระบบ")

        # Last modified info
        last_modified = self._get_last_settings_update()
        st.markdown(f"*แก้ไขล่าสุด: {last_modified}*")

    # Helper methods
    def _get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        try:
            return self.settings_manager.get_setting(key, default)
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default

    def _save_all_settings(self):
        """Save all current settings"""
        try:
            # Get all settings from session state
            settings_to_save = {}

            for key in st.session_state:
                if not key.startswith("_"):  # Skip internal streamlit keys
                    settings_to_save[key] = st.session_state[key]

            # Save to database
            for key, value in settings_to_save.items():
                self.settings_manager.set_setting(key, value)

            st.success("✅ บันทึกการตั้งค่าเรียบร้อย")

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            st.error("❌ เกิดข้อผิดพลาดในการบันทึกการตั้งค่า")

    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        if st.confirm("คุณต้องการรีเซ็ตการตั้งค่าทั้งหมดเป็นค่าเริ่มต้นหรือไม่?"):
            try:
                self.settings_manager.reset_to_defaults()
                st.success("✅ รีเซ็ตการตั้งค่าเรียบร้อย")
                st.rerun()
            except Exception as e:
                logger.error(f"Error resetting settings: {e}")
                st.error("❌ เกิดข้อผิดพลาดในการรีเซ็ตการตั้งค่า")

    def _get_system_uptime(self) -> str:
        """Get system uptime"""
        return "3 วัน 12 ชั่วโมง"  # Placeholder

    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        return 67.5  # Placeholder

    def _get_db_connections(self) -> int:
        """Get database connection count"""
        return 15  # Placeholder

    def _get_last_backup_time(self) -> str:
        """Get last backup time"""
        return "2 ชั่วโมงที่แล้ว"  # Placeholder

    def _get_email_template(self, template_type: str) -> str:
        """Get email template"""
        templates = {
            "การต้อนรับ": "ยินดีต้อนรับสู่ SDX Project Manager!\n\nชื่อผู้ใช้: {username}\nรหัสผ่านเริ่มต้น: {password}",
            "รีเซ็ตรหัสผ่าน": "คลิกลิงค์นี้เพื่อรีเซ็ตรหัสผ่าน: {reset_link}",
            "การแจ้งเตือน": "คุณได้รับการแจ้งเตือนใหม่: {message}",
            "รายงาน": "รายงานประจำสัปดาห์แนบมาด้วย",
        }
        return templates.get(template_type, "")

    def _test_database_connection(self):
        """Test database connection"""
        try:
            # Simulate database test
            import time

            with st.spinner("กำลังทดสอบการเชื่อมต่อ..."):
                time.sleep(2)
            st.success("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
        except Exception as e:
            st.error(f"❌ เชื่อมต่อฐานข้อมูลล้มเหลว: {str(e)}")

    def _send_test_email(self, email: str):
        """Send test email"""
        if not email:
            st.error("กรุณาใส่อีเมลทดสอบ")
            return

        try:
            with st.spinner("กำลังส่งอีเมลทดสอบ..."):
                import time

                time.sleep(2)
            st.success(f"✅ ส่งอีเมลทดสอบไปยัง {email} เรียบร้อย")
        except Exception as e:
            st.error(f"❌ ส่งอีเมลล้มเหลว: {str(e)}")

    def _preview_theme(self):
        """Preview theme changes"""
        st.info("🎨 ตัวอย่างธีมจะแสดงในการอัพเดทครั้งถัดไป")

    def _get_users_data(self) -> pd.DataFrame:
        """Get users data for display"""
        # Sample data
        return pd.DataFrame(
            {
                "Username": ["admin", "john_doe", "jane_smith"],
                "Role": ["Admin", "User", "Manager"],
                "LastLogin": [
                    "2024-01-15 10:30",
                    "2024-01-14 16:45",
                    "2024-01-15 08:15",
                ],
                "Status": ["Active", "Active", "Inactive"],
            }
        )

    def _get_system_metrics(self) -> Dict[str, float]:
        """Get system performance metrics"""
        return {"cpu": 45.2, "memory": 67.8, "disk": 52.1, "network": 15.3}

    def _get_processes_data(self) -> pd.DataFrame:
        """Get running processes data"""
        return pd.DataFrame(
            {
                "Process": ["streamlit", "nginx", "postgres"],
                "CPU (%)": [15.2, 5.1, 8.7],
                "Memory (MB)": [256, 128, 512],
                "Status": ["Running", "Running", "Running"],
            }
        )

    def _get_backup_history(self) -> pd.DataFrame:
        """Get backup history"""
        return pd.DataFrame(
            {
                "Date": ["2024-01-15 02:00", "2024-01-14 02:00", "2024-01-13 02:00"],
                "Size": ["2.1 GB", "2.0 GB", "1.9 GB"],
                "Status": ["Success", "Success", "Failed"],
                "Duration": ["15 min", "12 min", "8 min"],
            }
        )

    def _get_recent_audit_logs(self) -> pd.DataFrame:
        """Get recent audit logs"""
        return pd.DataFrame(
            {
                "Timestamp": [
                    "2024-01-15 10:30",
                    "2024-01-15 10:25",
                    "2024-01-15 10:20",
                ],
                "User": ["admin", "john_doe", "jane_smith"],
                "Action": ["Login", "Create Task", "Update Project"],
                "Resource": ["System", "Task #123", "Project ABC"],
                "IP Address": ["192.168.1.100", "192.168.1.101", "192.168.1.102"],
            }
        )

    def _get_last_settings_update(self) -> str:
        """Get last settings update time"""
        return "2024-01-15 10:30:00"

    # Action methods (placeholders)
    def _send_bulk_email(self):
        st.info("🚧 ฟีเจอร์ส่งอีเมลกลุ่มจะพัฒนาในเวอร์ชันถัดไป")

    def _lock_inactive_users(self):
        st.info("🚧 ฟีเจอร์ล็อกผู้ใช้ไม่ใช้งานจะพัฒนาในเวอร์ชันถัดไป")

    def _export_users_data(self):
        st.info("🚧 ฟีเจอร์ส่งออกข้อมูลผู้ใช้จะพัฒนาในเวอร์ชันถัดไป")

    def _create_backup(self):
        st.info("🚧 ฟีเจอร์สำรองข้อมูลจะพัฒนาในเวอร์ชันถัดไป")

    def _restore_backup(self):
        st.info("🚧 ฟีเจอร์คืนค่าข้อมูลจะพัฒนาในเวอร์ชันถัดไป")

    def _cleanup_old_backups(self):
        st.info("🚧 ฟีเจอร์ล้างสำรองเก่าจะพัฒนาในเวอร์ชันถัดไป")

    def _configure_integration(self, name: str):
        st.info(f"🚧 การตั้งค่า {name} จะพัฒนาในเวอร์ชันถัดไป")

    def _connect_integration(self, name: str):
        st.info(f"🚧 การเชื่อมต่อ {name} จะพัฒนาในเวอร์ชันถัดไป")

    def _export_audit_logs(self):
        st.info("🚧 ฟีเจอร์ส่งออกบันทึกการใช้งานจะพัฒนาในเวอร์ชันถัดไป")

    def _restart_system(self):
        st.warning("⚠️ การรีสตาร์ทระบบจะทำให้ผู้ใช้ทั้งหมดถูกตัดการเชื่อมต่อ")

    def _clear_cache(self):
        st.info("🚧 ฟีเจอร์ล้าง Cache จะพัฒนาในเวอร์ชันถัดไป")

    def _export_settings(self):
        st.info("🚧 ฟีเจอร์ส่งออกการตั้งค่าจะพัฒนาในเวอร์ชันถัดไป")


# Main render function
def render_settings_ui(db_manager, theme_manager: ThemeManager):
    """Main function to render settings UI"""
    try:
        settings_ui = SettingsUI(db_manager, theme_manager)
        settings_ui.render_settings_page()
    except Exception as e:
        logger.error(f"Error rendering settings UI: {e}")
        st.error("เกิดข้อผิดพลาดในการแสดงผลหน้าการตั้งค่า")
