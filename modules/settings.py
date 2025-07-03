"""
modules/settings.py
Settings management module - Simplified version
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

            # Clear cache
            self._clear_cache(key)
            return True

        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False

    def get_system_settings(self) -> Dict[str, Any]:
        """Get all system settings"""
        try:
            query = """
            SELECT SettingKey, SettingValue, DataType
            FROM Settings
            WHERE Category = 'System' OR Category IS NULL
            ORDER BY SettingKey
            """

            results = self.db_manager.fetch_all(query)

            settings = {}
            for row in results:
                value = self._parse_setting_value(row["SettingValue"], row["DataType"])
                # Clean key names
                key = row["SettingKey"].replace("system_", "").replace("app_", "")
                settings[key] = value

            return settings

        except Exception as e:
            logger.error(f"Error getting system settings: {e}")
            return {}

    def get_security_settings(self) -> Dict[str, Any]:
        """Get security settings"""
        try:
            query = """
            SELECT SettingKey, SettingValue, DataType
            FROM Settings
            WHERE Category = 'Security'
            ORDER BY SettingKey
            """

            results = self.db_manager.fetch_all(query)

            settings = {}
            for row in results:
                value = self._parse_setting_value(row["SettingValue"], row["DataType"])
                key = row["SettingKey"].replace("security_", "")
                settings[key] = value

            return settings

        except Exception as e:
            logger.error(f"Error getting security settings: {e}")
            return {}

    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        try:
            query = """
            SELECT SettingKey, SettingValue, DataType
            FROM Settings
            WHERE Category = 'Notifications'
            ORDER BY SettingKey
            """

            results = self.db_manager.fetch_all(query)

            settings = {}
            for row in results:
                value = self._parse_setting_value(row["SettingValue"], row["DataType"])
                key = row["SettingKey"].replace("notification_", "")
                settings[key] = value

            return settings

        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")
            return {}

    def get_backup_settings(self) -> Dict[str, Any]:
        """Get backup settings"""
        try:
            query = """
            SELECT SettingKey, SettingValue, DataType
            FROM Settings
            WHERE Category = 'Backup'
            ORDER BY SettingKey
            """

            results = self.db_manager.fetch_all(query)

            settings = {}
            for row in results:
                value = self._parse_setting_value(row["SettingValue"], row["DataType"])
                key = row["SettingKey"].replace("backup_", "")
                settings[key] = value

            return settings

        except Exception as e:
            logger.error(f"Error getting backup settings: {e}")
            return {}

    def update_system_settings(
        self, settings: Dict[str, Any], user_id: int = None
    ) -> bool:
        """Update multiple system settings"""
        try:
            for key, value in settings.items():
                setting_key = f"system_{key}" if not key.startswith("system_") else key
                if not self.set_setting(setting_key, value, user_id):
                    return False

            logger.info(f"System settings updated by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating system settings: {e}")
            return False

    def update_security_settings(
        self, settings: Dict[str, Any], user_id: int = None
    ) -> bool:
        """Update security settings"""
        try:
            for key, value in settings.items():
                setting_key = (
                    f"security_{key}" if not key.startswith("security_") else key
                )
                if not self.set_setting(setting_key, value, user_id):
                    return False

            logger.info(f"Security settings updated by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating security settings: {e}")
            return False

    def update_notification_settings(
        self, settings: Dict[str, Any], user_id: int = None
    ) -> bool:
        """Update notification settings"""
        try:
            for key, value in settings.items():
                setting_key = (
                    f"notification_{key}"
                    if not key.startswith("notification_")
                    else key
                )
                if not self.set_setting(setting_key, value, user_id):
                    return False

            logger.info(f"Notification settings updated by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            return False

    def update_backup_settings(
        self, settings: Dict[str, Any], user_id: int = None
    ) -> bool:
        """Update backup settings"""
        try:
            for key, value in settings.items():
                setting_key = f"backup_{key}" if not key.startswith("backup_") else key
                if not self.set_setting(setting_key, value, user_id):
                    return False

            logger.info(f"Backup settings updated by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating backup settings: {e}")
            return False

    def send_test_email(self, to_email: str) -> bool:
        """Send test email"""
        try:
            # Get email settings
            smtp_server = self.get_setting("notification_smtp_server", "smtp.gmail.com")
            smtp_port = self.get_setting("notification_smtp_port", 587)
            smtp_username = self.get_setting("notification_smtp_username", "")
            smtp_password = self.get_setting("notification_smtp_password", "")
            from_email = self.get_setting(
                "notification_from_email", "noreply@denso.com"
            )
            use_tls = self.get_setting("notification_use_tls", True)

            if not all([smtp_server, smtp_username, smtp_password, from_email]):
                logger.error("Email settings incomplete")
                return False

            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = "DENSO Project Manager - Test Email"

            body = f"""
            <html>
            <body>
                <h2>🧪 Test Email from DENSO Project Manager</h2>
                <p>This is a test email to verify that your email configuration is working correctly.</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Status:</strong> ✅ Email configuration is working!</p>
                <hr>
                <p><small>This is an automated test message from DENSO Project Manager Pro.</small></p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, "html"))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Test email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False

    def get_backup_info(self) -> Dict[str, Any]:
        """Get backup information"""
        try:
            # Check if SystemBackups table exists
            query = """
            SELECT TOP 1 BackupDate, BackupSize, BackupType 
            FROM SystemBackups 
            ORDER BY BackupDate DESC
            """

            last_backup = self.db_manager.fetch_one(query)

            backup_count_query = "SELECT COUNT(*) as Count FROM SystemBackups"
            backup_count_result = self.db_manager.fetch_one(backup_count_query)
            backup_count = backup_count_result["Count"] if backup_count_result else 0

            return {
                "last_backup": (
                    last_backup["BackupDate"].strftime("%Y-%m-%d %H:%M:%S")
                    if last_backup and last_backup["BackupDate"]
                    else "ยังไม่เคย"
                ),
                "backup_size": (
                    last_backup["BackupSize"] / (1024 * 1024)
                    if last_backup and last_backup["BackupSize"]
                    else 0
                ),
                "backup_count": backup_count,
                "backup_type": last_backup["BackupType"] if last_backup else "N/A",
            }

        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return {
                "last_backup": "ยังไม่เคย",
                "backup_size": 0,
                "backup_count": 0,
                "backup_type": "N/A",
            }

    def create_backup(self, backup_type: str = "manual") -> bool:
        """Create system backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"denso_pm_backup_{timestamp}.bak"
            backup_path = os.path.join("data", "backups", backup_filename)

            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            # Simple backup simulation (in real implementation, use proper database backup)
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(f"# DENSO Project Manager Backup\n")
                f.write(f"# Created: {datetime.now()}\n")
                f.write(f"# Type: {backup_type}\n")

            # Get file size
            backup_size = os.path.getsize(backup_path)

            # Record backup in database
            query = """
            INSERT INTO SystemBackups (BackupDate, BackupType, BackupPath, BackupSize, CreatedBy)
            VALUES (?, ?, ?, ?, ?)
            """

            self.db_manager.execute_query(
                query, (datetime.now(), backup_type, backup_path, backup_size, 1)
            )

            logger.info(f"Backup created successfully: {backup_filename}")
            return True

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False

    def get_backup_files(self) -> List[Dict]:
        """Get list of backup files"""
        try:
            query = """
            SELECT BackupID, BackupDate, BackupType, BackupPath, BackupSize
            FROM SystemBackups
            ORDER BY BackupDate DESC
            """

            results = self.db_manager.fetch_all(query)

            backup_files = []
            for row in results:
                backup_files.append(
                    {
                        "id": row["BackupID"],
                        "filename": os.path.basename(row["BackupPath"]),
                        "created_date": row["BackupDate"].strftime("%Y-%m-%d %H:%M:%S"),
                        "type": row["BackupType"],
                        "size": row["BackupSize"] / (1024 * 1024),  # Convert to MB
                        "path": row["BackupPath"],
                    }
                )

            return backup_files

        except Exception as e:
            logger.error(f"Error getting backup files: {e}")
            return []

    def cleanup_database(self) -> bool:
        """Cleanup database"""
        try:
            # Clean old audit logs (older than 90 days)
            cleanup_date = datetime.now() - timedelta(days=90)
            query1 = "DELETE FROM AuditLog WHERE ActionDate < ?"
            self.db_manager.execute_query(query1, (cleanup_date,))

            # Clean old login attempts
            query2 = "DELETE FROM LoginAttempts WHERE AttemptDate < ?"
            self.db_manager.execute_query(query2, (cleanup_date,))

            logger.info("Database cleanup completed")
            return True

        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            return False

    def check_database_integrity(self) -> Dict[str, Any]:
        """Check database integrity"""
        try:
            query = """
            SELECT 
                (SELECT COUNT(*) FROM Users) as UserCount,
                (SELECT COUNT(*) FROM Projects) as ProjectCount,
                (SELECT COUNT(*) FROM Tasks) as TaskCount,
                (SELECT COUNT(*) FROM Settings) as SettingsCount
            """

            result = self.db_manager.fetch_one(query)

            if result:
                return {
                    "status": "ok",
                    "message": "Database integrity check passed",
                    "details": {
                        "user_count": result["UserCount"],
                        "project_count": result["ProjectCount"],
                        "task_count": result["TaskCount"],
                        "settings_count": result["SettingsCount"],
                    },
                }
            else:
                return {
                    "status": "error",
                    "message": "Unable to perform integrity check",
                }

        except Exception as e:
            logger.error(f"Error checking database integrity: {e}")
            return {"status": "error", "message": f"Integrity check failed: {str(e)}"}

    def analyze_database(self) -> Dict[str, Any]:
        """Analyze database performance and usage"""
        try:
            analysis = {}

            # Basic statistics
            stats_query = """
            SELECT 
                'Users' as TableName, COUNT(*) as RecordCount FROM Users
            UNION ALL
            SELECT 'Projects', COUNT(*) FROM Projects
            UNION ALL
            SELECT 'Tasks', COUNT(*) FROM Tasks
            UNION ALL
            SELECT 'Comments', COUNT(*) FROM Comments
            """

            stats = self.db_manager.fetch_all(stats_query)

            analysis["table_statistics"] = [
                {"table": row["TableName"], "count": row["RecordCount"]}
                for row in stats
            ]

            # Growth analysis
            growth_query = """
            SELECT 
                COUNT(CASE WHEN CreatedDate >= DATEADD(day, -30, GETDATE()) THEN 1 END) as Last30Days,
                COUNT(CASE WHEN CreatedDate >= DATEADD(day, -7, GETDATE()) THEN 1 END) as Last7Days
            FROM (
                SELECT CreatedDate FROM Users
                UNION ALL
                SELECT CreatedDate FROM Projects
                UNION ALL
                SELECT CreatedDate FROM Tasks
            ) as combined
            """

            growth = self.db_manager.fetch_one(growth_query)
            if growth:
                analysis["growth_stats"] = {
                    "new_records_30_days": growth["Last30Days"],
                    "new_records_7_days": growth["Last7Days"],
                }

            analysis["recommendations"] = [
                "Regular backup maintenance",
                "Monitor storage usage",
                "Review user activity patterns",
            ]

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing database: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    # Private helper methods
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
        """Clear cache for specific key or all keys"""
        if key:
            self._setting_cache.pop(key, None)
            self._cache_expiry.pop(key, None)
        else:
            self._setting_cache.clear()
            self._cache_expiry.clear()

    def _parse_setting_value(self, value: str, data_type: str) -> Any:
        """Parse setting value based on data type"""
        try:
            if data_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif data_type == "number":
                try:
                    return int(value)
                except ValueError:
                    return float(value)
            elif data_type == "json":
                return json.loads(value)
            else:
                return value

        except Exception as e:
            logger.error(f"Error parsing setting value: {e}")
            return value

    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from value"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, (dict, list)):
            return "json"
        else:
            return "string"
