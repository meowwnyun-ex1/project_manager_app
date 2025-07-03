#!/usr/bin/env python3
"""
Smart Database Environment Switcher
Auto-fallback system with health checking
"""

import streamlit as st
import pyodbc
import time
import socket
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DatabaseEnvironment:
    """Database environment configuration"""

    name: str
    server: str
    database: str
    username: str = ""
    password: str = ""
    driver: str = "ODBC Driver 17 for SQL Server"
    timeout: int = 10
    description: str = ""
    priority: int = 1  # 1 = highest priority


class SmartDatabaseManager:
    """Smart database manager with auto-fallback"""

    def __init__(self):
        self.environments = self._setup_environments()
        self.current_env = None
        self.health_cache = {}
        self.cache_duration = 30  # seconds

    def _setup_environments(self) -> Dict[str, DatabaseEnvironment]:
        """Setup all available database environments"""
        environments = {}

        # Local Development (Priority 1)
        environments["local"] = DatabaseEnvironment(
            name="Local Development",
            server="(localdb)\\MSSQLLocalDB",
            database="ProjectManagerDB",
            username="",
            password="",
            timeout=10,
            description="LocalDB • Fast • Development",
            priority=1,
        )

        # Production Server (Priority 2)
        environments["production"] = DatabaseEnvironment(
            name="Production Server",
            server="10.73.148.27",
            database="ProjectManagerDB",
            username="TS00029",
            password="Thammaphon@TS00029",
            timeout=15,
            description="Remote Server • Secure • Production Data",
            priority=2,
        )

        # SQLite Fallback (Priority 3)
        environments["sqlite"] = DatabaseEnvironment(
            name="SQLite Fallback",
            server="sqlite:///data/fallback.db",
            database="fallback.db",
            username="",
            password="",
            timeout=5,
            description="Local File • Always Available • Limited Features",
            priority=3,
        )

        return environments

    def test_environment_health(self, env_name: str) -> Tuple[bool, str, float]:
        """Test environment health with detailed results"""

        # Check cache first
        cache_key = f"health_{env_name}"
        if cache_key in self.health_cache:
            cached_time, result = self.health_cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return result

        env = self.environments.get(env_name)
        if not env:
            return False, "Environment not found", 0

        start_time = time.time()

        try:
            # Special handling for SQLite
            if env_name == "sqlite":
                return self._test_sqlite_health(env)

            # Test SQL Server connection
            if env.username and env.password:
                conn_str = (
                    f"DRIVER={{{env.driver}}};"
                    f"SERVER={env.server};"
                    f"DATABASE={env.database};"
                    f"UID={env.username};"
                    f"PWD={env.password};"
                    f"TrustServerCertificate=yes;"
                    f"Connection Timeout={env.timeout};"
                )
            else:
                conn_str = (
                    f"DRIVER={{{env.driver}}};"
                    f"SERVER={env.server};"
                    f"DATABASE={env.database};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes;"
                    f"Connection Timeout={env.timeout};"
                )

            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]

                response_time = time.time() - start_time
                result = (True, f"Connected: {version[:30]}...", response_time)

                # Cache successful result
                self.health_cache[cache_key] = (time.time(), result)
                return result

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)

            # Categorize error types
            if "timeout" in error_msg.lower():
                error_type = "Connection timeout"
            elif "login failed" in error_msg.lower():
                error_type = "Authentication failed"
            elif "server was not found" in error_msg.lower():
                error_type = "Server not found"
            else:
                error_type = "Connection error"

            result = (False, f"{error_type}: {error_msg[:50]}...", response_time)

            # Cache failed result for shorter time
            self.health_cache[cache_key] = (time.time(), result)
            return result

    def _test_sqlite_health(self, env: DatabaseEnvironment) -> Tuple[bool, str, float]:
        """Test SQLite fallback health"""
        start_time = time.time()
        try:
            import sqlite3
            import os

            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)

            # Test SQLite connection
            conn = sqlite3.connect("data/fallback.db", timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            conn.close()

            response_time = time.time() - start_time
            return (True, f"SQLite {version} ready", response_time)

        except Exception as e:
            response_time = time.time() - start_time
            return (False, f"SQLite error: {str(e)[:30]}...", response_time)

    def find_best_environment(self) -> Optional[str]:
        """Find the best available environment"""

        # Test all environments
        results = {}
        for env_name in self.environments:
            healthy, message, response_time = self.test_environment_health(env_name)
            results[env_name] = {
                "healthy": healthy,
                "message": message,
                "response_time": response_time,
                "priority": self.environments[env_name].priority,
            }

        # Find best healthy environment by priority
        healthy_envs = [
            (name, data) for name, data in results.items() if data["healthy"]
        ]

        if not healthy_envs:
            logger.error("No healthy database environments found!")
            return None

        # Sort by priority (lower number = higher priority)
        healthy_envs.sort(key=lambda x: x[1]["priority"])
        best_env = healthy_envs[0][0]

        logger.info(
            f"Selected environment: {best_env} (response: {results[best_env]['response_time']:.2f}s)"
        )
        return best_env

    def get_connection_config(self, env_name: str = None) -> Optional[Dict[str, Any]]:
        """Get connection configuration for environment"""

        if not env_name:
            env_name = self.find_best_environment()

        if not env_name:
            return None

        env = self.environments[env_name]
        self.current_env = env_name

        return {
            "name": env.name,
            "server": env.server,
            "database": env.database,
            "username": env.username,
            "password": env.password,
            "driver": env.driver,
            "timeout": env.timeout,
            "environment": env_name,
        }

    def render_environment_dashboard(self):
        """Render environment health dashboard"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔌 Database Health")

        # Test all environments
        for env_name, env in self.environments.items():
            with st.sidebar:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{env_name.title()}**")

                with col2:
                    if st.button("🔍", key=f"test_{env_name}", help="Test connection"):
                        with st.spinner("Testing..."):
                            healthy, message, response_time = (
                                self.test_environment_health(env_name)
                            )

                            if healthy:
                                st.success(f"✅ {response_time:.1f}s")
                            else:
                                st.error("❌ Failed")

                # Show cached status
                cache_key = f"health_{env_name}"
                if cache_key in self.health_cache:
                    _, (healthy, message, response_time) = self.health_cache[cache_key]

                    if healthy:
                        st.markdown(f"✅ {message[:25]}... ({response_time:.1f}s)")
                    else:
                        st.markdown(f"❌ {message[:25]}...")
                else:
                    st.markdown("⚪ Not tested")

        # Current environment status
        if self.current_env:
            current_env = self.environments[self.current_env]
            st.sidebar.info(f"**Active:** {current_env.name}")

        # Force environment selection
        st.sidebar.markdown("---")
        selected_env = st.sidebar.selectbox(
            "Force Environment:",
            ["Auto"] + list(self.environments.keys()),
            key="force_environment",
        )

        if selected_env != "Auto":
            return selected_env

        return None

    def setup_local_database(self):
        """Setup LocalDB if not running"""
        try:
            import subprocess

            st.info("🔧 Setting up LocalDB...")

            # Check if LocalDB is installed
            result = subprocess.run(
                ["sqllocaldb", "info"], capture_output=True, text=True
            )

            if result.returncode == 0:
                # Start MSSQLLocalDB
                subprocess.run(
                    ["sqllocaldb", "start", "MSSQLLocalDB"], capture_output=True
                )

                # Create database if needed
                conn_str = (
                    "DRIVER={ODBC Driver 17 for SQL Server};"
                    "SERVER=(localdb)\\MSSQLLocalDB;"
                    "Trusted_Connection=yes;"
                )

                try:
                    with pyodbc.connect(conn_str) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT name FROM sys.databases WHERE name = 'ProjectManagerDB'"
                        )

                        if not cursor.fetchone():
                            cursor.execute("CREATE DATABASE ProjectManagerDB")
                            st.success("✅ LocalDB database created!")
                        else:
                            st.success("✅ LocalDB ready!")

                except Exception as e:
                    st.warning(f"⚠️ LocalDB setup issue: {e}")

            else:
                st.warning("⚠️ LocalDB not installed. Using fallback options.")

        except Exception as e:
            st.error(f"❌ LocalDB setup failed: {e}")


# Global instance
_smart_db_manager = None


def get_smart_database_manager() -> SmartDatabaseManager:
    """Get global smart database manager"""
    global _smart_db_manager
    if _smart_db_manager is None:
        _smart_db_manager = SmartDatabaseManager()
    return _smart_db_manager


def get_best_database_config() -> Optional[Dict[str, Any]]:
    """Get best available database configuration"""
    manager = get_smart_database_manager()
    return manager.get_connection_config()


def render_database_dashboard():
    """Render database health dashboard"""
    manager = get_smart_database_manager()
    forced_env = manager.render_environment_dashboard()

    if forced_env:
        return manager.get_connection_config(forced_env)

    return manager.get_connection_config()
