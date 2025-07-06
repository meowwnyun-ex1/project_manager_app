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
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) UNIQUE NOT NULL,
                value TEXT,
                setting_type VARCHAR(50) NOT NULL,
                category VARCHAR(100) DEFAULT 'General',
                subcategory VARCHAR(100) DEFAULT 'general',
                is_system BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            # Settings audit log
            audit_table = """
            CREATE TABLE IF NOT EXISTS setting_audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username VARCHAR(255),
                action VARCHAR(50),
                setting_key VARCHAR(255),
                old_value TEXT,
                new_value TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT
            )
            """

            # Settings backup table
            backup_table = """
            CREATE TABLE IF NOT EXISTS settings_backup (
                id SERIAL PRIMARY KEY,
                backup_name VARCHAR(255),
                backup_data JSONB,
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
                help_text="เวอร์ชันระบบสำหรับการอ้างอิง",
                display_order=2,
            ),
            SettingDefinition(
                key="company_name",
                display_name="ชื่อบริษัท",
                description="ชื่อองค์กรที่ใช้ระบบ",
                setting_type=SettingType.STRING,
                default_value="DENSO Innovation",
                category="Application",
                subcategory="basic",
                help_text="ชื่อบริษัทที่จะแสดงในรายงานและเอกสาร",
                display_order=3,
            ),
            SettingDefinition(
                key="default_language",
                display_name="ภาษาเริ่มต้น",
                description="ภาษาที่ใช้ในระบบ",
                setting_type=SettingType.STRING,
                default_value="th",
                category="Application",
                subcategory="localization",
                validation_rules={"pattern": r"^(th|en)$"},
                help_text="ตัวเลือก: th (ไทย), en (อังกฤษ)",
                display_order=4,
            ),
            SettingDefinition(
                key="default_timezone",
                display_name="เขตเวลาเริ่มต้น",
                description="เขตเวลาที่ใช้ในระบบ",
                setting_type=SettingType.STRING,
                default_value="Asia/Bangkok",
                category="Application",
                subcategory="localization",
                help_text="เขตเวลาสำหรับการแสดงวันที่และเวลา",
                display_order=5,
            ),
        ]

        # Security Settings
        security_definitions = [
            SettingDefinition(
                key="session_timeout",
                display_name="หมดเวลาเซสชัน (นาที)",
                description="เวลาหมดอายุเซสชันผู้ใช้",
                setting_type=SettingType.INTEGER,
                default_value=480,
                category="Security",
                subcategory="authentication",
                validation_rules={"min_value": 30, "max_value": 1440},
                help_text="ระหว่าง 30-1440 นาที (0.5-24 ชั่วโมง)",
                display_order=10,
            ),
            SettingDefinition(
                key="password_min_length",
                display_name="ความยาวรหัสผ่านขั้นต่ำ",
                description="จำนวนตัวอักษรขั้นต่ำของรหัสผ่าน",
                setting_type=SettingType.INTEGER,
                default_value=8,
                category="Security",
                subcategory="password",
                validation_rules={"min_value": 6, "max_value": 32},
                help_text="แนะนำ 8-16 ตัวอักษร",
                display_order=11,
            ),
            SettingDefinition(
                key="password_require_uppercase",
                display_name="ต้องมีตัวพิมพ์ใหญ่",
                description="รหัสผ่านต้องมีตัวอักษรพิมพ์ใหญ่",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Security",
                subcategory="password",
                display_order=12,
            ),
            SettingDefinition(
                key="password_require_numbers",
                display_name="ต้องมีตัวเลข",
                description="รหัสผ่านต้องมีตัวเลข",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Security",
                subcategory="password",
                display_order=13,
            ),
            SettingDefinition(
                key="max_login_attempts",
                display_name="จำนวนการเข้าสู่ระบบสูงสุด",
                description="จำนวนครั้งที่พยายามเข้าสู่ระบบก่อนล็อก",
                setting_type=SettingType.INTEGER,
                default_value=5,
                category="Security",
                subcategory="authentication",
                validation_rules={"min_value": 3, "max_value": 10},
                help_text="แนะนำ 3-5 ครั้ง",
                display_order=14,
            ),
            SettingDefinition(
                key="enable_2fa",
                display_name="เปิดใช้ 2FA",
                description="การยืนยันตัวตน 2 ขั้นตอน",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category="Security",
                subcategory="authentication",
                help_text="เพิ่มความปลอดภัยด้วยการยืนยัน 2 ขั้นตอน",
                display_order=15,
            ),
        ]

        # Database Settings
        db_definitions = [
            SettingDefinition(
                key="db_pool_size",
                display_name="Database Pool Size",
                description="จำนวน connection pool",
                setting_type=SettingType.INTEGER,
                default_value=10,
                category="Database",
                subcategory="performance",
                validation_rules={"min_value": 5, "max_value": 100},
                help_text="จำนวน connection ที่เปิดพร้อมกัน",
                display_order=20,
            ),
            SettingDefinition(
                key="db_timeout",
                display_name="Database Timeout (วินาที)",
                description="หมดเวลาการเชื่อมต่อฐานข้อมูล",
                setting_type=SettingType.INTEGER,
                default_value=30,
                category="Database",
                subcategory="performance",
                validation_rules={"min_value": 10, "max_value": 300},
                help_text="เวลารอการตอบสนองจากฐานข้อมูล",
                display_order=21,
            ),
            SettingDefinition(
                key="enable_query_logging",
                display_name="เปิด Query Logging",
                description="บันทึกการ query ฐานข้อมูล",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category="Database",
                subcategory="monitoring",
                help_text="อาจส่งผลต่อประสิทธิภาพ",
                display_order=22,
            ),
        ]

        # Email Settings
        email_definitions = [
            SettingDefinition(
                key="smtp_host",
                display_name="SMTP Server",
                description="เซิร์ฟเวอร์ส่งอีเมล",
                setting_type=SettingType.STRING,
                default_value="smtp.gmail.com",
                category="Email",
                subcategory="smtp",
                validation_rules={"pattern": r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
                help_text="ที่อยู่เซิร์ฟเวอร์ SMTP",
                display_order=30,
            ),
            SettingDefinition(
                key="smtp_port",
                display_name="SMTP Port",
                description="พอร์ตเซิร์ฟเวอร์อีเมล",
                setting_type=SettingType.INTEGER,
                default_value=587,
                category="Email",
                subcategory="smtp",
                validation_rules={"min_value": 1, "max_value": 65535},
                help_text="พอร์ตมาตรฐาน: 25, 465, 587",
                display_order=31,
            ),
            SettingDefinition(
                key="smtp_use_tls",
                display_name="ใช้ TLS",
                description="เปิดใช้การเข้ารหัส TLS",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Email",
                subcategory="smtp",
                help_text="แนะนำให้เปิดเพื่อความปลอดภัย",
                display_order=32,
            ),
            SettingDefinition(
                key="from_email",
                display_name="อีเมลผู้ส่ง",
                description="อีเมลที่ใช้ส่งจากระบบ",
                setting_type=SettingType.EMAIL,
                default_value="noreply@denso-innovation.com",
                category="Email",
                subcategory="general",
                help_text="อีเมลที่จะแสดงเป็นผู้ส่ง",
                display_order=33,
            ),
        ]

        # Notification Settings
        notification_definitions = [
            SettingDefinition(
                key="enable_email_notifications",
                display_name="เปิดการแจ้งเตือนอีเมล",
                description="ส่งการแจ้งเตือนทางอีเมล",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Notifications",
                subcategory="email",
                display_order=40,
            ),
            SettingDefinition(
                key="slack_webhook_url",
                display_name="Slack Webhook URL",
                description="URL สำหรับส่งการแจ้งเตือน Slack",
                setting_type=SettingType.URL,
                default_value="",
                category="Notifications",
                subcategory="slack",
                is_required=False,
                is_sensitive=True,
                help_text="URL webhook จาก Slack app",
                display_order=41,
            ),
            SettingDefinition(
                key="enable_slack_notifications",
                display_name="เปิดการแจ้งเตือน Slack",
                description="ส่งการแจ้งเตือนไป Slack",
                setting_type=SettingType.BOOLEAN,
                default_value=False,
                category="Notifications",
                subcategory="slack",
                display_order=42,
            ),
        ]

        # Performance Settings
        performance_definitions = [
            SettingDefinition(
                key="cache_timeout",
                display_name="Cache Timeout (วินาที)",
                description="เวลาหมดอายุ cache",
                setting_type=SettingType.INTEGER,
                default_value=300,
                category="Performance",
                subcategory="caching",
                validation_rules={"min_value": 60, "max_value": 3600},
                help_text="เวลาเก็บข้อมูลใน cache",
                display_order=50,
            ),
            SettingDefinition(
                key="enable_compression",
                display_name="เปิดการบีบอัดข้อมูล",
                description="บีบอัดข้อมูลเพื่อลดขนาด",
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category="Performance",
                subcategory="optimization",
                help_text="ช่วยลดเวลาโหลดหน้าเว็บ",
                display_order=51,
            ),
            SettingDefinition(
                key="max_file_upload_size",
                display_name="ขนาดไฟล์อัปโหลดสูงสุด (MB)",
                description="ขนาดไฟล์สูงสุดที่อนุญาต",
                setting_type=SettingType.INTEGER,
                default_value=50,
                category="Performance",
                subcategory="uploads",
                validation_rules={"min_value": 1, "max_value": 1000},
                help_text="ขนาดไฟล์ในหน่วย MB",
                display_order=52,
            ),
        ]

        # Combine all definitions
        all_definitions = (
            app_definitions
            + security_definitions
            + db_definitions
            + email_definitions
            + notification_definitions
            + performance_definitions
        )

        for definition in all_definitions:
            definitions[definition.key] = definition

        return definitions

    def _ensure_default_settings(self):
        """Ensure all default settings exist in database"""
        try:
            for key, definition in self.setting_definitions.items():
                existing = self.get_setting(key)
                if existing is None:
                    self.create_setting(
                        key=key,
                        value=definition.default_value,
                        setting_type=definition.setting_type.value,
                        category=definition.category,
                        subcategory=definition.subcategory,
                        is_system=definition.is_system,
                    )
        except Exception as e:
            logger.error(f"Error ensuring default settings: {e}")

    def get_setting(self, key: str) -> Optional[Dict[str, Any]]:
        """Get setting by key"""
        try:
            query = "SELECT * FROM settings WHERE key = %s"
            result = self.db.fetch_one(query, (key,))

            if result:
                return {
                    "id": result[0],
                    "key": result[1],
                    "value": self._deserialize_value(result[2], result[3]),
                    "setting_type": result[3],
                    "category": result[4],
                    "subcategory": result[5],
                    "is_system": result[6],
                    "created_at": result[7],
                    "updated_at": result[8],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return None

    def get_setting_value(self, key: str, default=None) -> Any:
        """Get setting value only"""
        setting = self.get_setting(key)
        if setting:
            return setting["value"]

        definition = self.setting_definitions.get(key)
        if definition:
            return definition.default_value

        return default

    def update_setting(self, key: str, value: Any, user_info: Dict = None) -> bool:
        """Update setting with audit trail"""
        try:
            definition = self.setting_definitions.get(key)
            if not definition:
                logger.error(f"Setting definition not found: {key}")
                return False

            # Get old value for audit
            old_setting = self.get_setting(key)
            old_value = old_setting["value"] if old_setting else None

            # Validate value
            if not self._validate_value(value, definition):
                return False

            # Serialize value
            serialized_value = self._serialize_value(value, definition.setting_type)

            query = """
            UPDATE settings 
            SET value = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE key = %s
            """

            affected_rows = self.db.execute_query(query, (serialized_value, key))

            if affected_rows > 0:
                # Log change
                self._log_setting_change(key, old_value, value, user_info)
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False

    def create_setting(
        self,
        key: str,
        value: Any,
        setting_type: str,
        category: str = "General",
        subcategory: str = "general",
        is_system: bool = False,
    ) -> bool:
        """Create new setting"""
        try:
            serialized_value = self._serialize_value(value, SettingType(setting_type))

            query = """
            INSERT INTO settings (key, value, setting_type, category, subcategory, is_system)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            self.db.execute_query(
                query,
                (key, serialized_value, setting_type, category, subcategory, is_system),
            )
            return True

        except Exception as e:
            logger.error(f"Error creating setting {key}: {e}")
            return False

    def get_settings_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all settings in a category"""
        try:
            query = """
            SELECT * FROM settings 
            WHERE category = %s 
            ORDER BY subcategory, key
            """
            results = self.db.fetch_all(query, (category,))

            settings = []
            for result in results:
                setting_dict = {
                    "id": result[0],
                    "key": result[1],
                    "value": self._deserialize_value(result[2], result[3]),
                    "setting_type": result[3],
                    "category": result[4],
                    "subcategory": result[5],
                    "is_system": result[6],
                    "created_at": result[7],
                    "updated_at": result[8],
                }
                # Add definition info
                definition = self.setting_definitions.get(result[1])
                if definition:
                    setting_dict.update(
                        {
                            "display_name": definition.display_name,
                            "description": definition.description,
                            "help_text": definition.help_text,
                            "is_sensitive": definition.is_sensitive,
                            "validation_rules": definition.validation_rules,
                        }
                    )
                settings.append(setting_dict)

            return settings

        except Exception as e:
            logger.error(f"Error getting settings for category {category}: {e}")
            return []

    def get_setting_definition(self, key: str) -> Optional[SettingDefinition]:
        """Get setting definition"""
        return self.setting_definitions.get(key)

    def get_all_categories(self) -> List[str]:
        """Get all setting categories"""
        return list(set(d.category for d in self.setting_definitions.values()))

    def _validate_value(self, value: Any, definition: SettingDefinition) -> bool:
        """Validate setting value"""
        try:
            if definition.is_required and (value is None or value == ""):
                logger.error(f"Setting {definition.key} is required")
                return False

            if definition.setting_type == SettingType.EMAIL:
                if value and not re.match(
                    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", str(value)
                ):
                    logger.error(f"Invalid email format: {value}")
                    return False

            elif definition.setting_type == SettingType.URL:
                if value and not re.match(r"^https?://.*", str(value)):
                    logger.error(f"Invalid URL format: {value}")
                    return False

            elif definition.setting_type == SettingType.JSON:
                if value:
                    try:
                        json.loads(value)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON format: {value}")
                        return False

            if definition.validation_rules:
                rules = definition.validation_rules

                if definition.setting_type == SettingType.STRING:
                    if (
                        rules.get("min_length")
                        and len(str(value)) < rules["min_length"]
                    ):
                        return False
                    if (
                        rules.get("max_length")
                        and len(str(value)) > rules["max_length"]
                    ):
                        return False
                    if rules.get("pattern") and not re.match(
                        rules["pattern"], str(value)
                    ):
                        return False

                elif definition.setting_type in [
                    SettingType.INTEGER,
                    SettingType.FLOAT,
                ]:
                    if (
                        rules.get("min_value") is not None
                        and value < rules["min_value"]
                    ):
                        return False
                    if (
                        rules.get("max_value") is not None
                        and value > rules["max_value"]
                    ):
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating value: {e}")
            return False

    def _serialize_value(self, value: Any, setting_type: SettingType) -> str:
        """Serialize value for storage"""
        if value is None:
            return ""

        if setting_type == SettingType.JSON:
            return json.dumps(value)
        elif setting_type == SettingType.BOOLEAN:
            return "true" if value else "false"
        else:
            return str(value)

    def _deserialize_value(self, value: str, setting_type: str) -> Any:
        """Deserialize value from storage"""
        if not value:
            return None

        try:
            setting_type_enum = SettingType(setting_type)

            if setting_type_enum == SettingType.INTEGER:
                return int(value)
            elif setting_type_enum == SettingType.FLOAT:
                return float(value)
            elif setting_type_enum == SettingType.BOOLEAN:
                return value.lower() == "true"
            elif setting_type_enum == SettingType.JSON:
                return json.loads(value)
            else:
                return value

        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error deserializing value {value}: {e}")
            return value

    def _log_setting_change(
        self, key: str, old_value: Any, new_value: Any, user_info: Dict = None
    ):
        """Log setting changes for audit"""
        try:
            if not user_info:
                user_info = {}

            # Don't log sensitive values
            definition = self.setting_definitions.get(key)
            if definition and definition.is_sensitive:
                old_value = "[HIDDEN]"
                new_value = "[HIDDEN]"

            query = """
            INSERT INTO setting_audit_log 
            (user_id, username, action, setting_key, old_value, new_value, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.db.execute_query(
                query,
                (
                    user_info.get("user_id"),
                    user_info.get("username"),
                    "update",
                    key,
                    str(old_value) if old_value is not None else None,
                    str(new_value) if new_value is not None else None,
                    user_info.get("ip_address"),
                    user_info.get("user_agent"),
                ),
            )

        except Exception as e:
            logger.error(f"Error logging setting change: {e}")

    def export_settings_backup(self, backup_name: str = None) -> Dict[str, Any]:
        """Export settings for backup"""
        try:
            query = "SELECT key, value, setting_type, category FROM settings"
            results = self.db.fetch_all(query)

            backup = {
                "timestamp": datetime.now().isoformat(),
                "version": "2.5.0",
                "backup_name": backup_name
                or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "settings": {},
            }

            for result in results:
                key, value, setting_type, category = result
                definition = self.setting_definitions.get(key)

                # Skip sensitive settings in backup
                if definition and definition.is_sensitive:
                    continue

                backup["settings"][key] = {
                    "value": self._deserialize_value(value, setting_type),
                    "type": setting_type,
                    "category": category,
                }

            return backup

        except Exception as e:
            logger.error(f"Error exporting settings backup: {e}")
            return {}

    def get_audit_logs(
        self, start_date=None, end_date=None, user_filter=None, limit=100
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filters"""
        try:
            query = "SELECT * FROM setting_audit_log WHERE 1=1"
            params = []

            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)

            if user_filter:
                query += " AND username ILIKE %s"
                params.append(f"%{user_filter}%")

            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)

            results = self.db.fetch_all(query, params)

            logs = []
            for result in results:
                logs.append(
                    {
                        "id": result[0],
                        "timestamp": result[1],
                        "user_id": result[2],
                        "username": result[3],
                        "action": result[4],
                        "setting_key": result[5],
                        "old_value": result[6],
                        "new_value": result[7],
                        "ip_address": result[8],
                        "user_agent": result[9],
                    }
                )

            return logs

        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
