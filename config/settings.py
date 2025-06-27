# config/settings.py
import streamlit as st
from typing import Dict, Any


class AppConfig:
    """Application configuration management"""

    # Database settings
    DB_TIMEOUT = 30
    DB_POOL_SIZE = 5

    # UI Settings
    PAGE_TITLE = "Project Manager"
    PAGE_ICON = "📊"
    LAYOUT = "wide"

    # Date formats
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    # Session keys
    SESSION_KEYS = {
        "logged_in": "logged_in",
        "user_id": "user_id",
        "username": "username",
        "user_role": "user_role",
    }

    # User roles
    USER_ROLES = ["User", "Admin", "Manager"]

    # Project statuses
    PROJECT_STATUSES = ["Planning", "In Progress", "Completed", "On Hold", "Cancelled"]

    # Task statuses
    TASK_STATUSES = ["To Do", "In Progress", "Testing", "Done", "Blocked"]

    # Colors for charts
    CHART_COLORS = {
        "primary": "#1f77b4",
        "success": "#2ca02c",
        "warning": "#ff7f0e",
        "danger": "#d62728",
        "info": "#17a2b8",
    }


class DatabaseConfig:
    """Database configuration from secrets"""

    @staticmethod
    def get_connection_string() -> str:
        """Get database connection string from Streamlit secrets"""
        try:
            conn_params = st.secrets["connections.sqlserver"]
            return (
                f"DRIVER={conn_params['driver']};"
                f"SERVER={conn_params['server']};"
                f"DATABASE={conn_params['database']};"
                f"UID={conn_params['uid']};"
                f"PWD={conn_params['pwd']}"
            )
        except KeyError as e:
            st.error(f"Missing database configuration: {e}")
            return None

    @staticmethod
    def get_connection_params() -> Dict[str, Any]:
        """Get database connection parameters"""
        try:
            return dict(st.secrets["connections.sqlserver"])
        except KeyError:
            return {}


# Global app config instance
app_config = AppConfig()
db_config = DatabaseConfig()
