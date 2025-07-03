"""
modules/settings.py
Settings management module - Complete implementation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)


class SettingsManager:
    """Settings management class"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._setting_cache = {}
        self._cache_expiry = {}
        self.cache_duration = 300  # 5 minutes

    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """Get a single setting value"""
        # Check cache first
        if self._is_cached(key):
            return self._setting_cache[key]

        try:
            query = """
            SELECT SettingValue, DataType 
            FROM Settings 
            WHERE SettingKey = ?
            """

            result = self.db_manager.fetch_one(query, (key,))

            if result:
                value = self._parse_setting_value(
                    result["SettingValue"], result["DataType"]
                )
                self._cache_setting(key, value)
                return value
            else:
                return default_value

        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default_value

    def set_setting(self, key: str, value: Any, user_id: int = None) -> bool:
        """Set a setting value"""
        try:
            # Check if setting exists
            existing = self.db_manager.fetch_one(
                "SELECT SettingKey FROM Settings WHERE SettingKey = ?", (key,)
            )

            data_type = self._infer_data_type(value)
            serialized_value = str(value)

            if existing:
                # Update existing setting
                query = """
                UPDATE Settings 
                SET SettingValue = ?, DataType = ?, UpdatedDate = ?
                WHERE SettingKey = ?
                """
                self.db_manager.execute_query(
                    query, (serialized_value, data_type, datetime.now(), key)
                )
            else:
                # Create new setting
                query = """
                INSERT INTO Settings (SettingKey, SettingValue, DataType, Category, CreatedDate)
                VALUES (?, ?, ?, 'System', ?)
                """
                self.db_manager.execute_query(
                    query, (key, serialized_value, data_type, datetime.now())
                )

            # Clear cache for this key
            self._clear_cache(key)
            logger.info(f"Setting {key} updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False

    def get_all_settings(self, category: str = None) -> Dict[str, Any]:
        """Get all settings or settings by category"""
        try:
            if category:
                query = "SELECT SettingKey, SettingValue, DataType FROM Settings WHERE Category = ?"
                results = self.db_manager.fetch_all(query, (category,))
            else:
                query = "SELECT SettingKey, SettingValue, DataType FROM Settings"
                results = self.db_manager.fetch_all(query)

            settings = {}
            for row in results:
                value = self._parse_setting_value(row["SettingValue"], row["DataType"])
                settings[row["SettingKey"]] = value
                # Cache the setting
                self._cache_setting(row["SettingKey"], value)

            return settings

        except Exception as e:
            logger.error(f"Error getting all settings: {e}")
            return {}

    def update_multiple_settings(
        self, settings: Dict[str, Any], user_id: int = None
    ) -> bool:
        """Update multiple settings at once"""
        try:
            for key, value in settings.items():
                if not self.set_setting(key, value, user_id):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error updating multiple settings: {e}")
            return False

    def delete_setting(self, key: str) -> bool:
        """Delete a setting"""
        try:
            query = "DELETE FROM Settings WHERE SettingKey = ?"
            self.db_manager.execute_query(query, (key,))
            self._clear_cache(key)
            logger.info(f"Setting {key} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting setting {key}: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        try:
            # Delete all existing settings
            self.db_manager.execute_query("DELETE FROM Settings")

            # Insert default settings
            defaults = self._get_default_settings()
            for key, value in defaults.items():
                self.set_setting(key, value)

            # Clear all cache
            self._setting_cache.clear()
            self._cache_expiry.clear()

            logger.info("Settings reset to defaults successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False

    def cleanup_database(self) -> bool:
        """Clean up old data and optimize database"""
        try:
            # Delete old audit logs (older than 90 days)
            cutoff_date = datetime.now() - timedelta(days=90)

            queries = [
                "DELETE FROM AuditLogs WHERE CreatedDate < ?",
                "DELETE FROM Notifications WHERE CreatedDate < ? AND IsRead = 1",
                "DELETE FROM ActivityLog WHERE CreatedDate < ?",
            ]

            for query in queries:
                self.db_manager.execute_query(query, (cutoff_date,))

            logger.info("Database cleanup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            return False

    def _is_cached(self, key: str) -> bool:
        """Check if setting is cached and not expired"""
        if key not in self._setting_cache:
            return False

        if key not in self._cache_expiry:
            return False

        return datetime.now() < self._cache_expiry[key]

    def _cache_setting(self, key: str, value: Any):
        """Cache a setting value"""
        self._setting_cache[key] = value
        self._cache_expiry[key] = datetime.now() + timedelta(
            seconds=self.cache_duration
        )

    def _clear_cache(self, key: str = None):
        """Clear cache for specific key or all cache"""
        if key:
            self._setting_cache.pop(key, None)
            self._cache_expiry.pop(key, None)
        else:
            self._setting_cache.clear()
            self._cache_expiry.clear()

    def _parse_setting_value(self, value: str, data_type: str) -> Any:
        """Parse setting value based on data type"""
        try:
            if data_type == "bool":
                return value.lower() in ("true", "1", "yes", "on")
            elif data_type == "int":
                return int(value)
            elif data_type == "float":
                return float(value)
            elif data_type == "json":
                return json.loads(value)
            elif data_type == "list":
                return json.loads(value) if value.startswith("[") else value.split(",")
            else:
                return value
        except Exception as e:
            logger.error(f"Error parsing setting value {value} as {data_type}: {e}")
            return value

    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from value"""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (list, tuple)):
            return "json"
        elif isinstance(value, dict):
            return "json"
        else:
            return "string"

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            # Application settings
            "app_name": "DENSO Project Manager Pro",
            "app_version": "1.0.0",
            "default_theme": "auto",
            "default_language": "th",
            # System settings
            "maintenance_mode": False,
            "session_timeout": 60,
            "items_per_page": 20,
            "max_upload_size": 50,
            # Security settings
            "max_login_attempts": 5,
            "password_min_length": 8,
            "password_require_uppercase": True,
            "password_require_lowercase": True,
            "password_require_numbers": True,
            "password_require_symbols": True,
            # Backup settings
            "auto_backup_enabled": True,
            "backup_time": "02:00",
            "backup_retention_days": 30,
            # Notification settings
            "enable_notifications": True,
            "enable_email_notifications": True,
            "notification_email": "",
            # Performance settings
            "log_level": "INFO",
            "enable_audit_log": True,
            "cache_enabled": True,
            "cache_duration": 300,
        }

    def send_test_email(self, email_settings: Dict[str, str]) -> bool:
        """Send a test email with given settings"""
        try:
            smtp_server = email_settings.get("smtp_server")
            smtp_port = int(email_settings.get("smtp_port", 587))
            email_user = email_settings.get("email_user")
            email_password = email_settings.get("email_password")
            test_recipient = email_settings.get("test_recipient")

            if not all([smtp_server, email_user, email_password, test_recipient]):
                return False

            # Create message
            msg = MIMEMultipart()
            msg["From"] = email_user
            msg["To"] = test_recipient
            msg["Subject"] = "DENSO Project Manager - Test Email"

            body = """
            นี่คืออีเมลทดสอบจากระบบ DENSO Project Manager Pro
            
            หากคุณได้รับอีเมลนี้ แสดงว่าการตั้งค่าอีเมลถูกต้อง
            
            ขอบคุณ
            ทีม DENSO Project Manager
            """

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Test email sent successfully to {test_recipient}")
            return True

        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False
