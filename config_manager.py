# config_manager.py
"""
Configuration and Environment Management for DENSO Project Manager
Handles application configuration, environment variables, and settings
"""

import streamlit as st
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""

    server: str
    database: str
    username: str
    password: str
    driver: str = "ODBC Driver 17 for SQL Server"
    port: int = 1433
    connection_timeout: int = 30
    command_timeout: int = 60
    encrypt: bool = True
    trust_server_certificate: bool = True


@dataclass
class CacheConfig:
    """Cache configuration"""

    max_size_mb: int = 100
    default_ttl: int = 3600
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None


@dataclass
class SecurityConfig:
    """Security configuration"""

    bcrypt_rounds: int = 12
    session_timeout: int = 3600
    max_login_attempts: int = 5
    lockout_duration: int = 900
    password_min_length: int = 8
    enable_2fa: bool = False
    session_cookie_secure: bool = False


@dataclass
class PerformanceConfig:
    """Performance configuration"""

    enable_monitoring: bool = True
    page_load_threshold: float = 2.0
    memory_threshold_mb: int = 512
    db_query_threshold: float = 1.0
    cache_hit_rate_threshold: float = 80.0
    enable_compression: bool = True


@dataclass
class NotificationConfig:
    """Notification configuration"""

    enable_notifications: bool = True
    enable_email: bool = False
    enable_slack: bool = False
    enable_teams: bool = False
    check_interval: int = 300  # 5 minutes
    max_notifications_per_user: int = 50
    default_priority: str = "medium"
    auto_mark_read_days: int = 30


@dataclass
class UIConfig:
    """UI/UX configuration"""

    theme: str = "light"  # light, dark, auto
    enable_animations: bool = True
    enable_glassmorphism: bool = True
    default_page_size: int = 20
    enable_tooltips: bool = True
    show_debug_info: bool = False
    compact_mode: bool = False


@dataclass
class AppConfig:
    """Main application configuration"""

    app_name: str = "DENSO Project Manager Pro"
    version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "production"  # development, staging, production
    secret_key: str = ""
    max_upload_size_mb: int = 50
    timezone: str = "UTC"
    language: str = "en"

    # Sub-configurations
    database: DatabaseConfig = None
    cache: CacheConfig = None
    security: SecurityConfig = None
    performance: PerformanceConfig = None
    notifications: NotificationConfig = None
    ui: UIConfig = None


class ConfigManager:
    """Configuration management system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = AppConfig()
        self._load_configuration()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Try multiple locations
        possible_paths = [
            "config.yaml",
            "config.yml",
            ".streamlit/config.yaml",
            "configs/app_config.yaml",
            os.path.expanduser("~/.denso_pm/config.yaml"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Return default path if none found
        return "config.yaml"

    def _load_configuration(self):
        """Load configuration from various sources"""
        try:
            # 1. Load from YAML file
            self._load_from_file()

            # 2. Load from Streamlit secrets
            self._load_from_streamlit_secrets()

            # 3. Load from environment variables
            self._load_from_environment()

            # 4. Validate configuration
            self._validate_configuration()

            logger.info(f"Configuration loaded successfully from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            # Use default configuration
            self._load_default_configuration()

    def _load_from_file(self):
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file not found: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                config_data = yaml.safe_load(file) or {}

            # Update configuration with file data
            self._update_config_from_dict(config_data)

        except Exception as e:
            logger.error(f"Failed to load configuration from file: {str(e)}")

    def _load_from_streamlit_secrets(self):
        """Load configuration from Streamlit secrets.toml"""
        try:
            # Database configuration
            if hasattr(st.secrets, "database"):
                db_secrets = st.secrets.database
                self.config.database = DatabaseConfig(
                    server=db_secrets.get("server", ""),
                    database=db_secrets.get("database", ""),
                    username=db_secrets.get("username", ""),
                    password=db_secrets.get("password", ""),
                    driver=db_secrets.get("driver", "ODBC Driver 17 for SQL Server"),
                )

                # Connection options
                if hasattr(st.secrets.database, "connection_options"):
                    options = st.secrets.database.connection_options
                    self.config.database.connection_timeout = options.get(
                        "connection_timeout", 30
                    )
                    self.config.database.command_timeout = options.get(
                        "command_timeout", 60
                    )

            # App configuration
            if hasattr(st.secrets, "app"):
                app_secrets = st.secrets.app
                self.config.debug = app_secrets.get("debug", False)
                self.config.log_level = app_secrets.get("log_level", "INFO")
                self.config.secret_key = app_secrets.get("secret_key", "")
                self.config.max_upload_size_mb = app_secrets.get("max_upload_size", 50)

            # Security configuration
            if hasattr(st.secrets, "security"):
                sec_secrets = st.secrets.security
                if not self.config.security:
                    self.config.security = SecurityConfig()

                self.config.security.bcrypt_rounds = sec_secrets.get(
                    "bcrypt_rounds", 12
                )
                self.config.security.session_timeout = sec_secrets.get(
                    "session_timeout", 3600
                )
                self.config.security.max_login_attempts = sec_secrets.get(
                    "max_login_attempts", 5
                )
                self.config.security.password_min_length = sec_secrets.get(
                    "password_min_length", 8
                )

            logger.info("Configuration loaded from Streamlit secrets")

        except Exception as e:
            logger.warning(f"Failed to load from Streamlit secrets: {str(e)}")

    def _load_from_environment(self):
        """Load configuration from environment variables"""
        try:
            # Database environment variables
            if os.getenv("DB_SERVER"):
                if not self.config.database:
                    self.config.database = DatabaseConfig(
                        server="", database="", username="", password=""
                    )

                self.config.database.server = os.getenv(
                    "DB_SERVER", self.config.database.server
                )
                self.config.database.database = os.getenv(
                    "DB_DATABASE", self.config.database.database
                )
                self.config.database.username = os.getenv(
                    "DB_USERNAME", self.config.database.username
                )
                self.config.database.password = os.getenv(
                    "DB_PASSWORD", self.config.database.password
                )

            # App environment variables
            self.config.debug = (
                os.getenv("DEBUG", str(self.config.debug)).lower() == "true"
            )
            self.config.log_level = os.getenv("LOG_LEVEL", self.config.log_level)
            self.config.environment = os.getenv("ENVIRONMENT", self.config.environment)
            self.config.secret_key = os.getenv("SECRET_KEY", self.config.secret_key)

            # Cache configuration
            if os.getenv("REDIS_HOST"):
                if not self.config.cache:
                    self.config.cache = CacheConfig()

                self.config.cache.redis_enabled = True
                self.config.cache.redis_host = os.getenv("REDIS_HOST", "localhost")
                self.config.cache.redis_port = int(os.getenv("REDIS_PORT", "6379"))
                self.config.cache.redis_password = os.getenv("REDIS_PASSWORD")

            logger.info("Configuration loaded from environment variables")

        except Exception as e:
            logger.warning(f"Failed to load from environment: {str(e)}")

    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        try:
            # App configuration
            if "app" in config_data:
                app_data = config_data["app"]
                for key, value in app_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

            # Database configuration
            if "database" in config_data:
                db_data = config_data["database"]
                self.config.database = DatabaseConfig(**db_data)

            # Cache configuration
            if "cache" in config_data:
                cache_data = config_data["cache"]
                self.config.cache = CacheConfig(**cache_data)

            # Security configuration
            if "security" in config_data:
                sec_data = config_data["security"]
                self.config.security = SecurityConfig(**sec_data)

            # Performance configuration
            if "performance" in config_data:
                perf_data = config_data["performance"]
                self.config.performance = PerformanceConfig(**perf_data)

            # Notifications configuration
            if "notifications" in config_data:
                notif_data = config_data["notifications"]
                self.config.notifications = NotificationConfig(**notif_data)

            # UI configuration
            if "ui" in config_data:
                ui_data = config_data["ui"]
                self.config.ui = UIConfig(**ui_data)

        except Exception as e:
            logger.error(f"Failed to update configuration from dictionary: {str(e)}")

    def _load_default_configuration(self):
        """Load default configuration"""
        self.config = AppConfig(
            database=DatabaseConfig(
                server="localhost",
                database="ProjectManagerDB",
                username="",
                password="",
            ),
            cache=CacheConfig(),
            security=SecurityConfig(),
            performance=PerformanceConfig(),
            notifications=NotificationConfig(),
            ui=UIConfig(),
        )
        logger.info("Default configuration loaded")

    def _validate_configuration(self):
        """Validate configuration parameters"""
        errors = []

        try:
            # Validate database configuration
            if self.config.database:
                if not self.config.database.server:
                    errors.append("Database server is required")
                if not self.config.database.database:
                    errors.append("Database name is required")
                if not self.config.database.username:
                    errors.append("Database username is required")

            # Validate security configuration
            if self.config.security:
                if (
                    self.config.security.bcrypt_rounds < 4
                    or self.config.security.bcrypt_rounds > 16
                ):
                    errors.append("BCrypt rounds must be between 4 and 16")
                if self.config.security.password_min_length < 6:
                    errors.append("Password minimum length must be at least 6")

            # Validate cache configuration
            if self.config.cache:
                if self.config.cache.max_size_mb < 10:
                    errors.append("Cache size must be at least 10MB")
                if self.config.cache.default_ttl < 60:
                    errors.append("Default TTL must be at least 60 seconds")

            if errors:
                logger.warning(
                    f"Configuration validation warnings: {'; '.join(errors)}"
                )
            else:
                logger.info("Configuration validation passed")

        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")

    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self.config

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.config.database or DatabaseConfig(
            server="localhost", database="ProjectManagerDB", username="", password=""
        )

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        return self.config.cache or CacheConfig()

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.config.security or SecurityConfig()

    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration"""
        return self.config.performance or PerformanceConfig()

    def get_notification_config(self) -> NotificationConfig:
        """Get notification configuration"""
        return self.config.notifications or NotificationConfig()

    def get_ui_config(self) -> UIConfig:
        """Get UI configuration"""
        return self.config.ui or UIConfig()

    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.config.debug

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.config.environment == "production"

    def save_configuration(self, config_path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            save_path = config_path or self.config_path

            # Convert configuration to dictionary
            config_dict = {
                "app": {
                    "app_name": self.config.app_name,
                    "version": self.config.version,
                    "debug": self.config.debug,
                    "log_level": self.config.log_level,
                    "environment": self.config.environment,
                    "max_upload_size_mb": self.config.max_upload_size_mb,
                    "timezone": self.config.timezone,
                    "language": self.config.language,
                }
            }

            # Add sub-configurations
            if self.config.database:
                config_dict["database"] = asdict(self.config.database)
                # Don't save password in plain text
                config_dict["database"]["password"] = "***HIDDEN***"

            if self.config.cache:
                config_dict["cache"] = asdict(self.config.cache)
                # Don't save Redis password
                if config_dict["cache"].get("redis_password"):
                    config_dict["cache"]["redis_password"] = "***HIDDEN***"

            if self.config.security:
                config_dict["security"] = asdict(self.config.security)

            if self.config.performance:
                config_dict["performance"] = asdict(self.config.performance)

            if self.config.notifications:
                config_dict["notifications"] = asdict(self.config.notifications)

            if self.config.ui:
                config_dict["ui"] = asdict(self.config.ui)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save to YAML file
            with open(save_path, "w", encoding="utf-8") as file:
                yaml.dump(config_dict, file, default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to {save_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            return False

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            self._update_config_from_dict(updates)
            self._validate_configuration()
            logger.info("Configuration updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to update configuration: {str(e)}")
            return False

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._load_default_configuration()
        logger.info("Configuration reset to defaults")

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display"""
        return {
            "app_info": {
                "name": self.config.app_name,
                "version": self.config.version,
                "environment": self.config.environment,
                "debug_mode": self.config.debug,
            },
            "database": {
                "server": (
                    self.config.database.server
                    if self.config.database
                    else "Not configured"
                ),
                "database": (
                    self.config.database.database
                    if self.config.database
                    else "Not configured"
                ),
                "driver": (
                    self.config.database.driver
                    if self.config.database
                    else "Not configured"
                ),
            },
            "features": {
                "caching_enabled": bool(self.config.cache),
                "notifications_enabled": (
                    self.config.notifications.enable_notifications
                    if self.config.notifications
                    else False
                ),
                "performance_monitoring": (
                    self.config.performance.enable_monitoring
                    if self.config.performance
                    else False
                ),
                "animations_enabled": (
                    self.config.ui.enable_animations if self.config.ui else True
                ),
            },
            "security": {
                "session_timeout": (
                    self.config.security.session_timeout
                    if self.config.security
                    else 3600
                ),
                "max_login_attempts": (
                    self.config.security.max_login_attempts
                    if self.config.security
                    else 5
                ),
                "password_min_length": (
                    self.config.security.password_min_length
                    if self.config.security
                    else 8
                ),
            },
        }

    def export_config_template(
        self, template_path: str = "config_template.yaml"
    ) -> bool:
        """Export configuration template"""
        try:
            template = {
                "app": {
                    "app_name": "DENSO Project Manager Pro",
                    "version": "2.0.0",
                    "debug": False,
                    "log_level": "INFO",
                    "environment": "production",
                    "max_upload_size_mb": 50,
                    "timezone": "UTC",
                    "language": "en",
                },
                "database": {
                    "server": "your_server_address",
                    "database": "ProjectManagerDB",
                    "username": "your_username",
                    "password": "your_password",
                    "driver": "ODBC Driver 17 for SQL Server",
                    "port": 1433,
                    "connection_timeout": 30,
                    "command_timeout": 60,
                },
                "cache": {
                    "max_size_mb": 100,
                    "default_ttl": 3600,
                    "redis_enabled": False,
                    "redis_host": "localhost",
                    "redis_port": 6379,
                },
                "security": {
                    "bcrypt_rounds": 12,
                    "session_timeout": 3600,
                    "max_login_attempts": 5,
                    "lockout_duration": 900,
                    "password_min_length": 8,
                },
                "performance": {
                    "enable_monitoring": True,
                    "page_load_threshold": 2.0,
                    "memory_threshold_mb": 512,
                    "db_query_threshold": 1.0,
                    "cache_hit_rate_threshold": 80.0,
                },
                "notifications": {
                    "enable_notifications": True,
                    "check_interval": 300,
                    "max_notifications_per_user": 50,
                    "default_priority": "medium",
                },
                "ui": {
                    "theme": "light",
                    "enable_animations": True,
                    "enable_glassmorphism": True,
                    "default_page_size": 20,
                    "compact_mode": False,
                },
            }

            with open(template_path, "w", encoding="utf-8") as file:
                yaml.dump(template, file, default_flow_style=False, indent=2)

            logger.info(f"Configuration template exported to {template_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export configuration template: {str(e)}")
            return False


# Global configuration manager instance
config_manager = None


def get_config_manager() -> ConfigManager:
    """Get or create configuration manager instance"""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager()
    return config_manager


def get_config() -> AppConfig:
    """Get current application configuration"""
    return get_config_manager().get_config()


def is_debug() -> bool:
    """Check if debug mode is enabled"""
    return get_config_manager().is_debug()


def is_production() -> bool:
    """Check if running in production environment"""
    return get_config_manager().is_production()
