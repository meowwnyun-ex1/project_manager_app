#!/usr/bin/env python3
"""
Dynamic Database Environment Switcher
สลับ environment ได้ทันทีโดยไม่ต้องแก้โค้ด
"""

import streamlit as st
import os
import socket
from typing import Dict, Any


class DatabaseEnvironmentManager:
    """จัดการ environment switching แบบ dynamic"""

    def __init__(self):
        self.environments = {
            "local": {
                "name": "🏠 Local Development",
                "server": "(localdb)\\MSSQLLocalDB",
                "database": "ProjectManagerDB",
                "username": "",
                "password": "",
                "driver": "ODBC Driver 17 for SQL Server",
                "description": "LocalDB • Windows Auth • Fast startup",
                "icon": "🏠",
                "color": "green",
            },
            "production": {
                "name": "🏢 Production Server",
                "server": "10.73.148.27",
                "database": "ProjectManagerDB",
                "username": "TS00029",
                "password": "Thammaphon@TS00029",
                "driver": "ODBC Driver 17 for SQL Server",
                "description": "Remote Server • SQL Auth • Network required",
                "icon": "🏢",
                "color": "blue",
            },
        }

    def auto_detect_environment(self) -> str:
        """Auto-detect environment ตาม hostname"""
        try:
            hostname = socket.gethostname().lower()
            if any(keyword in hostname for keyword in ["server", "prod", "denso"]):
                return "production"
            return "local"
        except:
            return "local"

    def get_current_environment(self) -> str:
        """Get current selected environment"""
        # Priority: Session State > Environment Variable > Auto-detect
        if "db_environment" in st.session_state:
            return st.session_state.db_environment

        env_var = os.getenv("DB_ENVIRONMENT")
        if env_var in self.environments:
            return env_var

        return self.auto_detect_environment()

    def set_environment(self, env: str):
        """Set environment in session state"""
        if env in self.environments:
            st.session_state.db_environment = env
            os.environ["DB_ENVIRONMENT"] = env
            return True
        return False

    def get_config(self, env: str = None) -> Dict[str, Any]:
        """Get database config for environment"""
        if not env:
            env = self.get_current_environment()
        return self.environments.get(env, self.environments["local"])

    def render_environment_selector(self):
        """Render environment selector in sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔌 Database Environment")

        current_env = self.get_current_environment()
        current_config = self.get_config(current_env)

        # Current status
        st.sidebar.info(f"**Active:** {current_config['icon']} {current_env.title()}")

        # Environment buttons
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button(
                "🏠 Local",
                key="btn_local",
                use_container_width=True,
                type="primary" if current_env == "local" else "secondary",
            ):
                self.set_environment("local")
                st.rerun()

        with col2:
            if st.button(
                "🏢 Production",
                key="btn_prod",
                use_container_width=True,
                type="primary" if current_env == "production" else "secondary",
            ):
                self.set_environment("production")
                st.rerun()

        # Test connection button
        if st.sidebar.button("🔍 Test Connection", use_container_width=True):
            self.test_current_connection()

    def test_current_connection(self):
        """Test current environment connection"""
        current_env = self.get_current_environment()
        config = self.get_config(current_env)

        with st.sidebar:
            with st.spinner(f"Testing {current_env}..."):
                success = self._test_connection(config)

                if success:
                    st.success(f"✅ {current_env.title()} connected!")
                else:
                    st.error(f"❌ {current_env.title()} failed!")

    def _test_connection(self, config: Dict[str, Any]) -> bool:
        """Test database connection"""
        try:
            import pyodbc

            # Build connection string
            if config["username"] and config["password"]:
                conn_str = (
                    f"DRIVER={{{config['driver']}}};"
                    f"SERVER={config['server']};"
                    f"DATABASE={config['database']};"
                    f"UID={config['username']};"
                    f"PWD={config['password']};"
                    f"TrustServerCertificate=yes;"
                    f"Connection Timeout=10;"
                )
            else:
                conn_str = (
                    f"DRIVER={{{config['driver']}}};"
                    f"SERVER={config['server']};"
                    f"DATABASE={config['database']};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes;"
                    f"Connection Timeout=10;"
                )

            # Test connection
            conn = pyodbc.connect(conn_str)
            conn.close()
            return True

        except Exception as e:
            st.sidebar.error(f"Error: {str(e)[:100]}...")
            return False

    def get_connection_string(self, env: str = None) -> str:
        """Get connection string for current environment"""
        config = self.get_config(env)

        if config["username"] and config["password"]:
            return (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['username']};"
                f"PWD={config['password']};"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=30;"
            )
        else:
            return (
                f"DRIVER={{{config['driver']}}};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=30;"
            )


# Global instance
_env_manager = None


def get_environment_manager() -> DatabaseEnvironmentManager:
    """Get global environment manager instance"""
    global _env_manager
    if _env_manager is None:
        _env_manager = DatabaseEnvironmentManager()
    return _env_manager


def get_current_database_config() -> Dict[str, Any]:
    """Get current database configuration"""
    env_manager = get_environment_manager()
    return env_manager.get_config()


def render_environment_selector():
    """Render environment selector (call in main app)"""
    env_manager = get_environment_manager()
    env_manager.render_environment_selector()


# Integration with existing database.py
def get_database_manager_with_env():
    """Get DatabaseManager with current environment"""
    from config.database import get_database_manager

    # ใช้ get_database_manager() ปกติ - ไม่ส่ง force_environment
    return get_database_manager()


# Usage Example in app.py:
"""
# Add to app.py imports:
from database_env_switcher import render_environment_selector, get_database_manager_with_env

# Add to sidebar in main app:
render_environment_selector()

# Replace database manager initialization:
self.db_manager = get_database_manager_with_env()
"""
