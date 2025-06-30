"""
🚀 Project Manager Pro v3.0 - Enhanced Configuration
Centralized configuration management
"""

import streamlit as st
import os
from pathlib import Path
from typing import Dict, Any, Optional
import toml
from datetime import timedelta

class EnhancedConfig:
    """Enhanced configuration management for Project Manager Pro"""
    
    def __init__(self):
        self.config_file = Path(".streamlit/secrets.toml")
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment"""
        config = {
            # Application Settings
            'app': {
                'name': 'Project Manager Pro',
                'version': '3.0.0',
                'environment': os.getenv('STREAMLIT_ENV', 'development'),
                'debug': os.getenv('DEBUG', 'False').lower() == 'true',
                'secret_key': os.getenv('SECRET_KEY', 'your-secret-key-here'),
                'timezone': 'UTC',
                'language': 'en'
            },
            
            # Database Configuration
            'database': {
                'driver': 'ODBC Driver 17 for SQL Server',
                'server': os.getenv('DB_SERVER', 'localhost'),
                'database': os.getenv('DB_NAME', 'ProjectManagerPro'),
                'username': os.getenv('DB_USERNAME', 'sa'),
                'password': os.getenv('DB_PASSWORD', 'YourPassword123'),
                'port': int(os.getenv('DB_PORT', '1433')),
                'trusted_connection': os.getenv('DB_TRUSTED_CONNECTION', 'no'),
                'connection_timeout': 30,
                'command_timeout': 30,
                'pool_size': 10,
                'max_overflow': 20
            },
            
            # Authentication Settings
            'auth': {
                'session_timeout': timedelta(hours=8),
                'max_login_attempts': 5,
                'lockout_duration': timedelta(minutes=30),
                'password_min_length': 8,
                'password_require_uppercase': True,
                'password_require_lowercase': True,
                'password_require_digits': True,
                'password_require_special': True,
                'password_history_count': 5,
                'cookie_name': 'project_manager_pro_auth',
                'cookie_expiry_days': 30
            },
            
            # Security Settings
            'security': {
                'bcrypt_rounds': 12,
                'csrf_protection': True,
                'secure_headers': True,
                'rate_limiting': True,
                'input_validation': True,
                'sql_injection_protection': True,
                'xss_protection': True
            },
            
            # UI/UX Settings
            'ui': {
                'theme': 'modern_dark',
                'animation_duration': 300,
                'page_transition_effect': 'fade',
                'sidebar_width': 300,
                'items_per_page': 10,
                'chart_height': 400,
                'default_chart_theme': 'plotly_dark',
                'notification_duration': 5000,
                'auto_refresh_interval': 30000
            },
            
            # Performance Settings
            'performance': {
                'cache_ttl': 300,
                'max_cache_entries': 1000,
                'query_timeout': 30,
                'file_upload_max_size': 50 * 1024 * 1024,  # 50MB
                'export_max_rows': 100000,
                'concurrent_users': 100,
                'memory_limit': '1GB'
            },
            
            # Feature Flags
            'features': {
                'gantt_charts': True,
                'time_tracking': True,
                'file_attachments': True,
                'email_notifications': True,
                'advanced_analytics': True,
                'team_collaboration': True,
                'mobile_app': False,
                'api_access': True,
                'custom_fields': True,
                'workflow_automation': False
            },
            
            # Integration Settings
            'integrations': {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'smtp_username': '',
                    'smtp_password': '',
                    'use_tls': True
                },
                'calendar': {
                    'enabled': False,
                    'provider': 'google',
                    'api_key': ''
                },
                'file_storage': {
                    'provider': 'local',
                    'path': './uploads',
                    'max_size': '50MB'
                }
            },
            
            # Logging Settings
            'logging': {
                'level': 'INFO',
                'file_path': './logs/app.log',
                'max_file_size': '10MB',
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            
            # Monitoring Settings
            'monitoring': {
                'enabled': True,
                'health_check_interval': 60,
                'performance_tracking': True,
                'error_tracking': True,
                'usage_analytics': True
            }
        }
        
        # Load from secrets.toml if available
        if self.config_file.exists():
            try:
                secrets = toml.load(self.config_file)
                config = self._merge_configs(config, secrets)
            except Exception as e:
                st.warning(f"⚠️ Could not load secrets.toml: {e}")
        
        return config
    
    def _merge_configs(self, base_config: Dict, override_config: Dict) -> Dict:
        """Recursively merge configuration dictionaries"""
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                base_config[key] = self._merge_configs(base_config[key], value)
            else:
                base_config[key] = value
        return base_config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_database_connection_string(self) -> str:
        """Get database connection string"""
        db_config = self.config['database']
        
        if db_config.get('trusted_connection', 'no').lower() == 'yes':
            connection_string = (
                f"DRIVER={{{db_config['driver']}}};"
                f"SERVER={db_config['server']},{db_config['port']};"
                f"DATABASE={db_config['database']};"
                "Trusted_Connection=yes;"
            )
        else:
            connection_string = (
                f"DRIVER={{{db_config['driver']}}};"
                f"SERVER={db_config['server']},{db_config['port']};"
                f"DATABASE={db_config['database']};"
                f"UID={db_config['username']};"
                f"PWD={db_config['password']};"
            )
        
        return connection_string
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.get('app.environment', 'development').lower() == 'production'
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('app.debug', False)
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.get('features', {})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        return self.get(f'features.{feature_name}', False)
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.get('ui', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.get('security', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.get('performance', {})
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate database configuration
        db_config = self.config['database']
        if not db_config.get('server'):
            validation_results['errors'].append("Database server not configured")
            validation_results['valid'] = False
        
        if not db_config.get('database'):
            validation_results['errors'].append("Database name not configured")
            validation_results['valid'] = False
        
        # Validate authentication configuration
        auth_config = self.config['auth']
        if not auth_config.get('session_timeout'):
            validation_results['warnings'].append("Session timeout not configured, using default")
        
        # Validate security configuration
        security_config = self.config['security']
        if security_config.get('bcrypt_rounds', 0) < 10:
            validation_results['warnings'].append("BCrypt rounds should be at least 10 for security")
        
        return validation_results
    
    def create_default_secrets_file(self) -> None:
        """Create default secrets.toml file"""
        secrets_dir = Path(".streamlit")
        secrets_dir.mkdir(exist_ok=True)
        
        default_secrets = """
# 🚀 Project Manager Pro v3.0 - Configuration File
# Copy this file to .streamlit/secrets.toml and update with your settings

[app]
name = "Project Manager Pro"
version = "3.0.0"
environment = "development"
debug = true
secret_key = "your-secret-key-here-change-in-production"

[database]
driver = "ODBC Driver 17 for SQL Server"
server = "localhost"
database = "ProjectManagerPro"
username = "sa"
password = "YourPassword123"
port = 1433
trusted_connection = "no"

[auth]
password_min_length = 8
max_login_attempts = 5
cookie_expiry_days = 30

[ui]
theme = "modern_dark"
items_per_page = 10
chart_height = 400

[features]
gantt_charts = true
time_tracking = true
advanced_analytics = true
team_collaboration = true

[integrations.email]
enabled = false
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = ""
smtp_password = ""
use_tls = true
"""
        
        with open(self.config_file, 'w') as f:
            f.write(default_secrets)