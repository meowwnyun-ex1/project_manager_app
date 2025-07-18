#!/usr/bin/env python3
"""
modules/settings.py
SDX Project Manager - Complete Settings Management Core
Enterprise-grade configuration system with validation and audit
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
import streamlit as st

logger = logging.getLogger(__name__)


class SettingType(Enum):
    """Setting data types enumeration"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    EMAIL = "email"
    URL = "url"
    PASSWORD = "password"
    SELECT = "select"
    MULTISELECT = "multiselect"
    TEXTAREA = "textarea"
    COLOR = "color"
    TIME = "time"
    DATE = "date"


@dataclass
class SettingDefinition:
    """Complete setting definition with all properties"""

    key: str
    display_name: str
    description: str
    setting_type: SettingType
    default_value: Any
    is_required: bool = True
    is_sensitive: bool = False
    validation_rules: Dict[str, Any] = None
    category: str = "General"
    subcategory: str = "general"
    is_system: bool = False
    help_text: str = ""
    display_order: int = 0
    options: List[str] = None  # For SELECT/MULTISELECT types
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    depends_on: Optional[str] = None  # Conditional settings


class SettingsManager:
    """Complete enterprise settings management system"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.setting_definitions = self._initialize_all_definitions()
        self._create_tables()
        self._ensure_default_settings()

    def _create_tables(self):
        """Create all settings-related tables"""
        try:
            # Main settings table
            settings_table = """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                setting_type TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                subcategory TEXT DEFAULT 'general',
                is_system BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            # Settings audit log
            audit_table = """
            CREATE TABLE IF NOT EXISTS setting_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                setting_key TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                user_agent TEXT
            )
            """

            # Settings backup table
            backup_table = """
            CREATE TABLE IF NOT EXISTS settings_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_name TEXT,
                backup_data TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            for table_sql in [settings_table, audit_table, backup_table]:
                self.db.execute_query(table_sql)

            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)",
                "CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category)",
                "CREATE INDEX IF NOT EXISTS idx_audit_setting_key ON setting_audit_log(setting_key)",
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON setting_audit_log(timestamp)",
            ]

            for index_sql in indexes:
                self.db.execute_query(index_sql)

        except Exception as e:
            logger.error(f"Error creating settings tables: {e}")

    def _initialize_all_definitions(self) -> Dict[str, SettingDefinition]:
        """Initialize complete system setting definitions"""
        definitions = {}

        # Application Settings
        app_definitions = [
            SettingDefinition(
                key="app_name",
                display_name="ชื่อแอปพลิเคชัน",
                description="ชื่อที่แสดงในหัวเรื่องและส่วนติดต่อ",
                setting_type=SettingType.STRING,
                default_value="SDX Project Manager",
                category="Application",
                subcategory="basic",
                is_system=True,
                help_text="ชื่อนี้จะแสดงในทุกหน้าของระบบ",
                display_order=1,
            ),
            SettingDefinition(
                key="app_version",
                display_name="เวอร์ชันแอปพลิเคชัน",
                description="เวอร์ชันปัจจุบันของระบบ",
                setting_type=SettingType.STRING,
                default_value="2.5.0",
                category="Application",
                subcategory="basic",
                is_system=True,
                help_text="เวอร์ชันจะอัพเดทอัตโนมัติ",
                display_order=2,
            ),
            SettingDefinition(
                key="company_name",
                display_name="ชื่อบริษัท/องค์กร",
                description="ชื่อบริษัทหรือองค์กรที่ใช้ระบบ",
                setting_type=SettingType.STRING,
                default_value="DENSO Corporation",
                category="Application",
                subcategory="basic",
                help_text="ชื่อจะแสดงในรายงานและเอกสารต่างๆ",
                display_order=3,
            ),
            SettingDefinition(
                key="app_theme",
                display_name="ธีมของแอปพลิเคชัน",
                description="เลือกธีมสีของระบบ",
                setting_type=SettingType.SELECT,
                default_value="blue",
                options=["blue", "green", "red", "purple", "orange", "dark"],
                category="Application",
                subcategory="appearance",
                help_text="ธีมจะเปลี่ยนสีหลักของระบบ",
                display_order=4,
            ),
            SettingDefinition(
                key="timezone",
                display_name="เขตเวลา",
                description="เขตเวลาที่ใช้ในระบบ",
                setting_type=SettingType.SELECT,
                default_value="Asia/Bangkok",
                options=[
                    "Asia/Bangkok",
                    "Asia/Tokyo",
                    "Asia/Seoul",
                    "Asia/Singapore",
                    "Europe/London",
                    "US/Eastern",
                    "US/Central",
                    "US/Mountain",
                    "US/Pacific",
                ],
                category="Application",
                subcategory="localization",
                help_text="กำหนดเขตเวลาสำหรับการแสดงวันที่และเวลา",
                display_order=5,
            ),
            SettingDefinition(
                key="language",
                display_name="ภาษา",
                description="ภาษาหลักของระบบ",
                setting_type=SettingType.SELECT,
                default_value="th",
                options=["th", "en", "ja", "ko"],
                category="Application",
                subcategory="localization",
                help_text="เลือกภาษาที่ใช้ในระบบ",
                display_order=6,
            ),
        ]

        # Security Settings
        security_definitions = [
            SettingDefinition(
                key="session_timeout",
                display_name="หมดเวลาเซสชัน (นาที)",
                description="เวลาที่เซสชันจะหมดอายุ",
                setting_type=SettingType.INTEGER,
                default_value=480,  # 8 hours
                min_value=30,
                max_value=1440,
                category="Security",
                subcategory="authentication",
                help_text="ระบบจะล็อกเอาต์อัตโนมัติเมื่อหมดเวลา",
                display_order=10,
            ),
            SettingDefinition(
                key="password_min_length",
                display_name="ความยาวรหัสผ่านขั้นต่ำ",
                description="จำนวนตัวอักษรขั้นต่ำของรหัสผ่าน",
                setting_type=SettingType.INTEGER,
                default_value=8,
                min_value=4,
                max_value=50,
                category="Security",
                subcategory="password",
                help_text="รหัสผ่านต้องมีความยาวอย่างน้อยตามจำนวนที่กำหนด",
                display_order=11,
            ),
            SettingDefinition(
                key="password_require_uppercase",
                display_name="ต้องมีตัวอักษรใหญ่",
                description="รหัสผ่านต้องมีตัวอักษรพิมพ์ใหญ่",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Security",
                subcategory="password",
                help_text="รหัสผ่านต้องมีตัวอักษร A-Z อย่างน้อย 1 ตัว",
                display_order=12,
            ),
            SettingDefinition(
                key="password_require_lowercase",
                display_name="ต้องมีตัวอักษรเล็ก",
                description="รหัสผ่านต้องมีตัวอักษรพิมพ์เล็ก",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Security",
                subcategory="password",
                help_text="รหัสผ่านต้องมีตัวอักษร a-z อย่างน้อย 1 ตัว",
                display_order=13,
            ),
            SettingDefinition(
                key="password_require_numbers",
                display_name="ต้องมีตัวเลข",
                description="รหัสผ่านต้องมีตัวเลข",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Security",
                subcategory="password",
                help_text="รหัสผ่านต้องมีตัวเลข 0-9 อย่างน้อย 1 ตัว",
                display_order=14,
            ),
            SettingDefinition(
                key="password_require_special",
                display_name="ต้องมีอักขระพิเศษ",
                description="รหัสผ่านต้องมีอักขระพิเศษ",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Security",
                subcategory="password",
                help_text="รหัสผ่านต้องมีอักขระพิเศษ เช่น !@#$%",
                display_order=15,
            ),
            SettingDefinition(
                key="max_login_attempts",
                display_name="จำนวนครั้งล็อกอินสูงสุด",
                description="จำนวนครั้งที่พยายามล็อกอินผิดก่อนบล็อค",
                setting_type=SettingType.INTEGER,
                default_value=5,
                min_value=3,
                max_value=10,
                category="Security",
                subcategory="authentication",
                help_text="หลังจากล็อกอินผิดตามจำนวนนี้ บัญชีจะถูกล็อค",
                display_order=16,
            ),
            SettingDefinition(
                key="enable_2fa",
                display_name="เปิดใช้ 2FA",
                description="เปิดใช้การยืนยันตัวตน 2 ขั้นตอน",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category="Security",
                subcategory="authentication",
                help_text="เพิ่มความปลอดภัยด้วยการยืนยันตัวตน 2 ขั้นตอน",
                display_order=17,
            ),
        ]

        # System Settings
        system_definitions = [
            SettingDefinition(
                key="max_file_size",
                display_name="ขนาดไฟล์สูงสุด (MB)",
                description="ขนาดไฟล์สูงสุดที่อัพโหลดได้",
                setting_type=SettingType.INTEGER,
                default_value=10,
                min_value=1,
                max_value=100,
                category="System",
                subcategory="file_management",
                help_text="กำหนดขนาดไฟล์สูงสุดที่ผู้ใช้สามารถอัพโหลดได้",
                display_order=20,
            ),
            SettingDefinition(
                key="allowed_file_types",
                display_name="ประเภทไฟล์ที่อนุญาต",
                description="ประเภทไฟล์ที่สามารถอัพโหลดได้",
                setting_type=SettingType.MULTISELECT,
                default_value=[
                    "pdf",
                    "doc",
                    "docx",
                    "xls",
                    "xlsx",
                    "jpg",
                    "png",
                    "gif",
                ],
                options=[
                    "pdf",
                    "doc",
                    "docx",
                    "xls",
                    "xlsx",
                    "ppt",
                    "pptx",
                    "txt",
                    "csv",
                    "jpg",
                    "jpeg",
                    "png",
                    "gif",
                    "bmp",
                    "zip",
                    "rar",
                    "mp4",
                    "avi",
                ],
                category="System",
                subcategory="file_management",
                help_text="เลือกประเภทไฟล์ที่ผู้ใช้สามารถอัพโหลดได้",
                display_order=21,
            ),
            SettingDefinition(
                key="backup_enabled",
                display_name="เปิดใช้การสำรองข้อมูล",
                description="เปิดใช้การสำรองข้อมูลอัตโนมัติ",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="System",
                subcategory="backup",
                help_text="ระบบจะสำรองข้อมูลอัตโนมัติตามช่วงเวลาที่กำหนด",
                display_order=22,
            ),
            SettingDefinition(
                key="backup_interval",
                display_name="ช่วงเวลาสำรองข้อมูล (ชั่วโมง)",
                description="ความถี่ในการสำรองข้อมูล",
                setting_type=SettingType.INTEGER,
                default_value=24,
                min_value=1,
                max_value=168,  # 1 week
                category="System",
                subcategory="backup",
                depends_on="backup_enabled",
                help_text="กำหนดช่วงเวลาที่ระบบจะทำการสำรองข้อมูล",
                display_order=23,
            ),
            SettingDefinition(
                key="log_retention_days",
                display_name="เก็บล็อกกี่วัน",
                description="จำนวนวันที่เก็บล็อกระบบ",
                setting_type=SettingType.INTEGER,
                default_value=90,
                min_value=7,
                max_value=365,
                category="System",
                subcategory="logging",
                help_text="ล็อกที่เก่ากว่านี้จะถูกลบอัตโนมัติ",
                display_order=24,
            ),
            SettingDefinition(
                key="debug_mode",
                display_name="โหมดดีบัก",
                description="เปิดใช้โหมดดีบักสำหรับการแก้ไขปัญหา",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category="System",
                subcategory="development",
                help_text="เปิดใช้เฉพาะเมื่อต้องการแก้ไขปัญหา",
                display_order=25,
            ),
        ]

        # Notification Settings
        notification_definitions = [
            SettingDefinition(
                key="notifications_enabled",
                display_name="เปิดใช้การแจ้งเตือน",
                description="เปิดใช้ระบบการแจ้งเตือน",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Notifications",
                subcategory="general",
                help_text="เปิด/ปิดการแจ้งเตือนทั้งหมด",
                display_order=30,
            ),
            SettingDefinition(
                key="email_notifications",
                display_name="แจ้งเตือนทางอีเมล",
                description="ส่งการแจ้งเตือนทางอีเมล",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Notifications",
                subcategory="email",
                depends_on="notifications_enabled",
                help_text="ส่งการแจ้งเตือนสำคัญทางอีเมล",
                display_order=31,
            ),
            SettingDefinition(
                key="smtp_server",
                display_name="เซิร์ฟเวอร์ SMTP",
                description="ที่อยู่เซิร์ฟเวอร์ SMTP สำหรับส่งอีเมล",
                setting_type=SettingType.STRING,
                default_value="smtp.gmail.com",
                category="Notifications",
                subcategory="email",
                depends_on="email_notifications",
                help_text="ใส่ที่อยู่เซิร์ฟเวอร์ SMTP ของคุณ",
                display_order=32,
            ),
            SettingDefinition(
                key="smtp_port",
                display_name="พอร์ต SMTP",
                description="หมายเลขพอร์ตของเซิร์ฟเวอร์ SMTP",
                setting_type=SettingType.INTEGER,
                default_value=587,
                min_value=1,
                max_value=65535,
                category="Notifications",
                subcategory="email",
                depends_on="email_notifications",
                help_text="พอร์ต 587 สำหรับ TLS, 465 สำหรับ SSL",
                display_order=33,
            ),
            SettingDefinition(
                key="smtp_username",
                display_name="ชื่อผู้ใช้ SMTP",
                description="ชื่อผู้ใช้สำหรับการเข้าสู่ระบบ SMTP",
                setting_type=SettingType.STRING,
                default_value="",
                category="Notifications",
                subcategory="email",
                depends_on="email_notifications",
                help_text="ชื่อผู้ใช้หรืออีเมลสำหรับ SMTP",
                display_order=34,
            ),
            SettingDefinition(
                key="smtp_password",
                display_name="รหัสผ่าน SMTP",
                description="รหัสผ่านสำหรับการเข้าสู่ระบบ SMTP",
                setting_type=SettingType.PASSWORD,
                default_value="",
                category="Notifications",
                subcategory="email",
                is_sensitive=True,
                depends_on="email_notifications",
                help_text="รหัสผ่านหรือ App Password สำหรับ SMTP",
                display_order=35,
            ),
        ]

        # Performance Settings
        performance_definitions = [
            SettingDefinition(
                key="cache_enabled",
                display_name="เปิดใช้แคช",
                description="เปิดใช้การแคชเพื่อเพิ่มประสิทธิภาพ",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Performance",
                subcategory="caching",
                help_text="แคชช่วยให้ระบบทำงานเร็วขึ้น",
                display_order=40,
            ),
            SettingDefinition(
                key="cache_ttl",
                display_name="อายุแคช (นาที)",
                description="ระยะเวลาที่แคชจะหมดอายุ",
                setting_type=SettingType.INTEGER,
                default_value=60,
                min_value=1,
                max_value=1440,
                category="Performance",
                subcategory="caching",
                depends_on="cache_enabled",
                help_text="แคชจะหมดอายุและถูกสร้างใหม่หลังจากเวลานี้",
                display_order=41,
            ),
            SettingDefinition(
                key="pagination_size",
                display_name="จำนวนรายการต่อหน้า",
                description="จำนวนรายการที่แสดงในแต่ละหน้า",
                setting_type=SettingType.INTEGER,
                default_value=20,
                min_value=5,
                max_value=100,
                category="Performance",
                subcategory="display",
                help_text="จำนวนรายการที่แสดงในตาราง",
                display_order=42,
            ),
            SettingDefinition(
                key="chart_animation",
                display_name="เปิดใช้แอนิเมชันกราฟ",
                description="เปิดใช้แอนิเมชันในกราฟและแผนภูมิ",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Performance",
                subcategory="display",
                help_text="แอนิเมชันอาจทำให้ช้าในอุปกรณ์เก่า",
                display_order=43,
            ),
        ]

        # Integration Settings
        integration_definitions = [
            SettingDefinition(
                key="api_enabled",
                display_name="เปิดใช้ API",
                description="เปิดใช้ REST API สำหรับการเชื่อมต่อภายนอก",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category="Integration",
                subcategory="api",
                help_text="อนุญาตให้ระบบภายนอกเข้าถึงข้อมูลผ่าน API",
                display_order=50,
            ),
            SettingDefinition(
                key="api_rate_limit",
                display_name="จำกัดอัตรา API (ต่อนาที)",
                description="จำนวนคำขอ API สูงสุดต่อนาที",
                setting_type=SettingType.INTEGER,
                default_value=100,
                min_value=10,
                max_value=1000,
                category="Integration",
                subcategory="api",
                depends_on="api_enabled",
                help_text="จำกัดจำนวนคำขอเพื่อป้องกันการใช้งานมากเกินไป",
                display_order=51,
            ),
            SettingDefinition(
                key="webhook_enabled",
                display_name="เปิดใช้ Webhook",
                description="เปิดใช้การส่งข้อมูลไปยังระบบภายนอก",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category="Integration",
                subcategory="webhook",
                help_text="ส่งการแจ้งเตือนไปยัง URL ภายนอกเมื่อมีเหตุการณ์",
                display_order=52,
            ),
            SettingDefinition(
                key="webhook_url",
                display_name="URL Webhook",
                description="URL ปลายทางสำหรับส่ง webhook",
                setting_type=SettingType.URL,
                default_value="",
                category="Integration",
                subcategory="webhook",
                depends_on="webhook_enabled",
                help_text="URL ที่จะรับข้อมูล webhook",
                display_order=53,
            ),
        ]

        # รวมนิยามทั้งหมด
        all_definitions = (
            app_definitions
            + security_definitions
            + system_definitions
            + notification_definitions
            + performance_definitions
            + integration_definitions
        )

        for definition in all_definitions:
            definitions[definition.key] = definition

        return definitions

    def _ensure_default_settings(self):
        """Ensure all default settings exist in database"""
        try:
            for key, definition in self.setting_definitions.items():
                existing = self.get_setting(key, default=None)
                if existing is None:
                    self.set_setting(
                        key=key,
                        value=definition.default_value,
                        setting_type=definition.setting_type.value,
                        category=definition.category,
                        subcategory=definition.subcategory,
                        is_system=definition.is_system,
                    )
        except Exception as e:
            logger.error(f"Error ensuring default settings: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value with type conversion"""
        try:
            query = "SELECT value, setting_type FROM settings WHERE key = ?"
            result = self.db.fetch_one(query, (key,))

            if not result:
                return default

            value, setting_type = result["value"], result["setting_type"]

            # Convert value based on type
            return self._convert_value(value, setting_type)

        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default

    def set_setting(
        self,
        key: str,
        value: Any,
        setting_type: str = None,
        category: str = None,
        subcategory: str = None,
        is_system: bool = False,
        user_id: int = None,
    ) -> bool:
        """Set setting value with validation and audit"""
        try:
            # Validate setting if definition exists
            if key in self.setting_definitions:
                definition = self.setting_definitions[key]
                if not self._validate_setting_value(definition, value):
                    return False

                if setting_type is None:
                    setting_type = definition.setting_type.value
                if category is None:
                    category = definition.category
                if subcategory is None:
                    subcategory = definition.subcategory

            # Get old value for audit
            old_value = self.get_setting(key)

            # Convert value to string for storage
            value_str = self._value_to_string(value, setting_type)

            # Insert or update setting
            query = """
            INSERT OR REPLACE INTO settings 
            (key, value, setting_type, category, subcategory, is_system, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """

            self.db.execute_query(
                query,
                (
                    key,
                    value_str,
                    setting_type or "string",
                    category or "General",
                    subcategory or "general",
                    is_system,
                ),
            )

            # Log change
            self._log_setting_change(
                key=key, old_value=old_value, new_value=value, user_id=user_id
            )

            return True

        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False

    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category"""
        try:
            query = """
            SELECT key, value, setting_type 
            FROM settings 
            WHERE category = ?
            ORDER BY key
            """

            results = self.db.fetch_all(query, (category,))
            settings = {}

            for row in results:
                key = row["key"]
                value = self._convert_value(row["value"], row["setting_type"])
                settings[key] = value

            return settings

        except Exception as e:
            logger.error(f"Error getting settings for category {category}: {e}")
            return {}

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings grouped by category"""
        try:
            query = """
            SELECT key, value, setting_type, category, subcategory
            FROM settings
            ORDER BY category, subcategory, key
            """

            results = self.db.fetch_all(query)
            settings = {}

            for row in results:
                category = row["category"]
                subcategory = row["subcategory"]
                key = row["key"]
                value = self._convert_value(row["value"], row["setting_type"])

                if category not in settings:
                    settings[category] = {}
                if subcategory not in settings[category]:
                    settings[category][subcategory] = {}

                settings[category][subcategory][key] = value

            return settings

        except Exception as e:
            logger.error(f"Error getting all settings: {e}")
            return {}

    def _convert_value(self, value: str, setting_type: str) -> Any:
        """Convert string value to appropriate type"""
        if value is None:
            return None

        try:
            if setting_type == SettingType.BOOLEAN.value:
                return value.lower() in ("true", "1", "yes", "on")
            elif setting_type == SettingType.INTEGER.value:
                return int(value)
            elif setting_type == SettingType.FLOAT.value:
                return float(value)
            elif setting_type == SettingType.JSON.value:
                return json.loads(value)
            elif setting_type == SettingType.MULTISELECT.value:
                return json.loads(value) if value.startswith("[") else [value]
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            return value

    def _value_to_string(self, value: Any, setting_type: str) -> str:
        """Convert value to string for storage"""
        if value is None:
            return ""

        if setting_type in [SettingType.JSON.value, SettingType.MULTISELECT.value]:
            return json.dumps(value, ensure_ascii=False)
        elif setting_type == SettingType.BOOLEAN.value:
            return "true" if value else "false"
        else:
            return str(value)

    def _validate_setting_value(
        self, definition: SettingDefinition, value: Any
    ) -> bool:
        """Validate setting value against definition"""
        try:
            # Required check
            if definition.is_required and (value is None or value == ""):
                return False

            # Type-specific validation
            if definition.setting_type == SettingType.EMAIL:
                pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                return re.match(pattern, str(value)) is not None

            elif definition.setting_type == SettingType.URL:
                pattern = r"^https?://[^\s/$.?#].[^\s]*"
                return re.match(pattern, str(value)) is not None

            elif definition.setting_type == SettingType.INTEGER:
                try:
                    int_val = int(value)
                    if (
                        definition.min_value is not None
                        and int_val < definition.min_value
                    ):
                        return False
                    if (
                        definition.max_value is not None
                        and int_val > definition.max_value
                    ):
                        return False
                except ValueError:
                    return False

            elif definition.setting_type == SettingType.FLOAT:
                try:
                    float_val = float(value)
                    if (
                        definition.min_value is not None
                        and float_val < definition.min_value
                    ):
                        return False
                    if (
                        definition.max_value is not None
                        and float_val > definition.max_value
                    ):
                        return False
                except ValueError:
                    return False

            elif definition.setting_type == SettingType.SELECT:
                if definition.options and value not in definition.options:
                    return False

            elif definition.setting_type == SettingType.MULTISELECT:
                if definition.options and isinstance(value, list):
                    for item in value:
                        if item not in definition.options:
                            return False

            return True

        except Exception as e:
            logger.error(f"Error validating setting: {e}")
            return False

    def _log_setting_change(
        self, key: str, old_value: Any, new_value: Any, user_id: int = None
    ):
        """Log setting change to audit table"""
        try:
            username = "system"
            if user_id and "username" in st.session_state:
                username = st.session_state.username

            query = """
            INSERT INTO setting_audit_log 
            (user_id, username, action, setting_key, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (user_id, username, "UPDATE", key, str(old_value), str(new_value)),
            )

        except Exception as e:
            logger.error(f"Error logging setting change: {e}")

    def backup_settings(self, backup_name: str, user_id: int = None) -> bool:
        """Create settings backup"""
        try:
            settings = self.get_all_settings()
            backup_data = json.dumps(settings, ensure_ascii=False, indent=2)

            query = """
            INSERT INTO settings_backup (backup_name, backup_data, created_by)
            VALUES (?, ?, ?)
            """

            self.db.execute_query(query, (backup_name, backup_data, user_id))
            return True

        except Exception as e:
            logger.error(f"Error creating settings backup: {e}")
            return False

    def restore_settings(self, backup_id: int, user_id: int = None) -> bool:
        """Restore settings from backup"""
        try:
            # Get backup data
            query = "SELECT backup_data FROM settings_backup WHERE id = ?"
            result = self.db.fetch_one(query, (backup_id,))

            if not result:
                return False

            backup_data = json.loads(result["backup_data"])

            # Restore settings
            for category, subcategories in backup_data.items():
                for subcategory, settings in subcategories.items():
                    for key, value in settings.items():
                        if key in self.setting_definitions:
                            definition = self.setting_definitions[key]
                            self.set_setting(
                                key=key,
                                value=value,
                                setting_type=definition.setting_type.value,
                                category=category,
                                subcategory=subcategory,
                                user_id=user_id,
                            )

            return True

        except Exception as e:
            logger.error(f"Error restoring settings: {e}")
            return False

    def reset_to_defaults(self, user_id: int = None) -> bool:
        """Reset all settings to default values"""
        try:
            for key, definition in self.setting_definitions.items():
                self.set_setting(
                    key=key,
                    value=definition.default_value,
                    setting_type=definition.setting_type.value,
                    category=definition.category,
                    subcategory=definition.subcategory,
                    is_system=definition.is_system,
                    user_id=user_id,
                )

            return True

        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False


# UI Functions for Settings Management
def create_settings_ui(settings_manager: SettingsManager):
    """Create settings management UI"""
    st.title("⚙️ การตั้งค่าระบบ")

    # Sidebar for category selection
    with st.sidebar:
        st.subheader("หมวดหมู่การตั้งค่า")

        categories = {
            "Application": "🖥️ แอปพลิเคชัน",
            "Security": "🔒 ความปลอดภัย",
            "System": "🔧 ระบบ",
            "Notifications": "🔔 การแจ้งเตือน",
            "Performance": "⚡ ประสิทธิภาพ",
            "Integration": "🔗 การเชื่อมต่อ",
        }

        selected_category = st.selectbox(
            "เลือกหมวดหมู่",
            options=list(categories.keys()),
            format_func=lambda x: categories[x],
        )

        st.divider()

        # Management actions
        st.subheader("การจัดการ")

        if st.button("💾 สำรองข้อมูลการตั้งค่า", use_container_width=True):
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if settings_manager.backup_settings(backup_name):
                st.success("สำรองข้อมูลสำเร็จ!")
            else:
                st.error("เกิดข้อผิดพลาดในการสำรองข้อมูล")

        if st.button("🔄 รีเซ็ตเป็นค่าเริ่มต้น", use_container_width=True):
            if st.session_state.get("confirm_reset", False):
                if settings_manager.reset_to_defaults():
                    st.success("รีเซ็ตการตั้งค่าสำเร็จ!")
                    st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการรีเซ็ต")
                st.session_state.confirm_reset = False
            else:
                st.session_state.confirm_reset = True
                st.warning("คลิกอีกครั้งเพื่อยืนยันการรีเซ็ต")

    # Main content area
    st.subheader(f"{categories[selected_category]}")

    # Get settings for selected category
    category_settings = {}
    for key, definition in settings_manager.setting_definitions.items():
        if definition.category == selected_category:
            if definition.subcategory not in category_settings:
                category_settings[definition.subcategory] = []
            category_settings[definition.subcategory].append((key, definition))

    # Display settings by subcategory
    for subcategory, settings_list in category_settings.items():
        with st.expander(f"📂 {subcategory.replace('_', ' ').title()}", expanded=True):

            # Sort by display order
            settings_list.sort(key=lambda x: x[1].display_order)

            for key, definition in settings_list:
                current_value = settings_manager.get_setting(
                    key, definition.default_value
                )

                # Check dependencies
                if definition.depends_on:
                    dependency_value = settings_manager.get_setting(
                        definition.depends_on, False
                    )
                    if not dependency_value:
                        continue

                # Create input based on setting type
                new_value = create_setting_input(definition, current_value)

                # Update setting if changed
                if new_value != current_value:
                    if settings_manager.set_setting(
                        key=key,
                        value=new_value,
                        user_id=st.session_state.get("user_id"),
                    ):
                        st.success(f"อัพเดท '{definition.display_name}' สำเร็จ!")
                        st.rerun()
                    else:
                        st.error(f"เกิดข้อผิดพลาดในการอัพเดท '{definition.display_name}'")


def create_setting_input(definition: SettingDefinition, current_value: Any) -> Any:
    """Create appropriate input widget based on setting type"""
    key = f"setting_{definition.key}"

    if definition.setting_type == SettingType.BOOLEAN:
        return st.checkbox(
            definition.display_name,
            value=bool(current_value),
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.INTEGER:
        return st.number_input(
            definition.display_name,
            value=(
                int(current_value)
                if current_value is not None
                else definition.default_value
            ),
            min_value=definition.min_value,
            max_value=definition.max_value,
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.FLOAT:
        return st.number_input(
            definition.display_name,
            value=(
                float(current_value)
                if current_value is not None
                else definition.default_value
            ),
            min_value=definition.min_value,
            max_value=definition.max_value,
            format="%.2f",
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.SELECT:
        index = 0
        if current_value in definition.options:
            index = definition.options.index(current_value)

        return st.selectbox(
            definition.display_name,
            options=definition.options,
            index=index,
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.MULTISELECT:
        default_values = current_value if isinstance(current_value, list) else []
        return st.multiselect(
            definition.display_name,
            options=definition.options,
            default=default_values,
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.PASSWORD:
        return st.text_input(
            definition.display_name,
            value=current_value if current_value else "",
            type="password",
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.TEXTAREA:
        return st.text_area(
            definition.display_name,
            value=current_value if current_value else "",
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.COLOR:
        return st.color_picker(
            definition.display_name,
            value=current_value if current_value else "#000000",
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.DATE:
        try:
            date_value = (
                datetime.strptime(current_value, "%Y-%m-%d").date()
                if current_value
                else datetime.now().date()
            )
        except:
            date_value = datetime.now().date()

        return st.date_input(
            definition.display_name,
            value=date_value,
            help=definition.help_text,
            key=key,
        )

    elif definition.setting_type == SettingType.TIME:
        try:
            time_value = (
                datetime.strptime(current_value, "%H:%M:%S").time()
                if current_value
                else datetime.now().time()
            )
        except:
            time_value = datetime.now().time()

        return st.time_input(
            definition.display_name,
            value=time_value,
            help=definition.help_text,
            key=key,
        )

    else:  # STRING, EMAIL, URL, etc.
        return st.text_input(
            definition.display_name,
            value=current_value if current_value else "",
            help=definition.help_text,
            key=key,
        )


def show_settings_audit_log(settings_manager: SettingsManager):
    """Show settings audit log"""
    st.subheader("📋 ประวัติการเปลี่ยนแปลงการตั้งค่า")

    try:
        query = """
        SELECT timestamp, username, action, setting_key, old_value, new_value
        FROM setting_audit_log
        ORDER BY timestamp DESC
        LIMIT 100
        """

        audit_data = settings_manager.db.fetch_all(query)

        if audit_data:
            df = pd.DataFrame(audit_data)
            df.columns = ["เวลา", "ผู้ใช้", "การกระทำ", "การตั้งค่า", "ค่าเก่า", "ค่าใหม่"]

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("ไม่มีประวัติการเปลี่ยนแปลง")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดประวัติ: {e}")


def show_settings_backup_management(settings_manager: SettingsManager):
    """Show settings backup management"""
    st.subheader("💾 การจัดการการสำรองข้อมูลการตั้งค่า")

    # Create new backup
    col1, col2 = st.columns([2, 1])

    with col1:
        backup_name = st.text_input(
            "ชื่อการสำรองข้อมูล",
            value=f"Manual_Backup_{datetime.now().strftime('%Y%m%d_%H%M')}",
        )

    with col2:
        if st.button("💾 สร้างการสำรองข้อมูล", use_container_width=True):
            if settings_manager.backup_settings(backup_name):
                st.success("สร้างการสำรองข้อมูลสำเร็จ!")
                st.rerun()
            else:
                st.error("เกิดข้อผิดพลาดในการสร้างการสำรองข้อมูล")

    st.divider()

    # Show existing backups
    try:
        query = """
        SELECT id, backup_name, created_at, created_by
        FROM settings_backup
        ORDER BY created_at DESC
        """

        backups = settings_manager.db.fetch_all(query)

        if backups:
            st.subheader("📂 การสำรองข้อมูลที่มีอยู่")

            for backup in backups:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    st.write(f"**{backup['backup_name']}**")

                with col2:
                    st.write(backup["created_at"])

                with col3:
                    if st.button(
                        "🔄", key=f"restore_{backup['id']}", help="กู้คืนการตั้งค่า"
                    ):
                        if settings_manager.restore_settings(backup["id"]):
                            st.success("กู้คืนการตั้งค่าสำเร็จ!")
                            st.rerun()
                        else:
                            st.error("เกิดข้อผิดพลาดในการกู้คืน")

                with col4:
                    if st.button(
                        "🗑️", key=f"delete_{backup['id']}", help="ลบการสำรองข้อมูล"
                    ):
                        delete_query = "DELETE FROM settings_backup WHERE id = ?"
                        settings_manager.db.execute_query(delete_query, (backup["id"],))
                        st.success("ลบการสำรองข้อมูลสำเร็จ!")
                        st.rerun()

                st.divider()
        else:
            st.info("ไม่มีการสำรองข้อมูล")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดการสำรองข้อมูล: {e}")


def export_settings_config(settings_manager: SettingsManager):
    """Export settings as configuration file"""
    try:
        settings = settings_manager.get_all_settings()

        # Create configuration structure
        config = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "version": "2.5.0",
                "app_name": "SDX Project Manager",
            },
            "settings": settings,
        }

        config_json = json.dumps(config, ensure_ascii=False, indent=2)

        st.download_button(
            label="📥 ดาวน์โหลดไฟล์การตั้งค่า",
            data=config_json,
            file_name=f"sdx_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการส่งออก: {e}")


def import_settings_config(settings_manager: SettingsManager):
    """Import settings from configuration file"""
    uploaded_file = st.file_uploader(
        "📤 อัพโหลดไฟล์การตั้งค่า", type=["json"], help="เลือกไฟล์ JSON ที่ส่งออกจากระบบ"
    )

    if uploaded_file is not None:
        try:
            config_data = json.load(uploaded_file)

            if "settings" in config_data:
                settings = config_data["settings"]

                # Import settings
                imported_count = 0
                for category, subcategories in settings.items():
                    for subcategory, category_settings in subcategories.items():
                        for key, value in category_settings.items():
                            if key in settings_manager.setting_definitions:
                                definition = settings_manager.setting_definitions[key]
                                if settings_manager.set_setting(
                                    key=key,
                                    value=value,
                                    setting_type=definition.setting_type.value,
                                    category=category,
                                    subcategory=subcategory,
                                ):
                                    imported_count += 1

                st.success(f"นำเข้าการตั้งค่าสำเร็จ {imported_count} รายการ!")
                st.rerun()
            else:
                st.error("ไฟล์ไม่ถูกต้อง: ไม่พบข้อมูลการตั้งค่า")

        except json.JSONDecodeError:
            st.error("ไฟล์ไม่ถูกต้อง: รูปแบบ JSON ผิดพลาด")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการนำเข้า: {e}")


def create_advanced_settings_ui(settings_manager: SettingsManager):
    """Create advanced settings management UI"""
    st.title("🔧 การตั้งค่าขั้นสูง")

    tabs = st.tabs(
        ["⚙️ การตั้งค่าหลัก", "📋 ประวัติการเปลี่ยนแปลง", "💾 การสำรองข้อมูล", "📤 นำเข้า/ส่งออก"]
    )

    with tabs[0]:
        create_settings_ui(settings_manager)

    with tabs[1]:
        show_settings_audit_log(settings_manager)

    with tabs[2]:
        show_settings_backup_management(settings_manager)

    with tabs[3]:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📤 ส่งออกการตั้งค่า")
            export_settings_config(settings_manager)

        with col2:
            st.subheader("📥 นำเข้าการตั้งค่า")
            import_settings_config(settings_manager)
