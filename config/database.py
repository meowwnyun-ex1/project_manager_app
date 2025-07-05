#!/usr/bin/env python3
"""
config/database.py
Database Connection Manager for SDX Project Manager
"""

import pyodbc
import streamlit as st
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Simple database manager for SQL Server"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None

    def get_connection(self):
        """Get database connection"""
        try:
            if not self._connection or self._connection.closed:
                self._connection = pyodbc.connect(self.connection_string)
                self._connection.autocommit = True
            return self._connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None

    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute SELECT query and return results"""
        try:
            conn = self.get_connection()
            if not conn:
                return []

            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def execute_non_query(self, query: str, params: tuple = None) -> bool:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            cursor.close()
            return True

        except Exception as e:
            logger.error(f"Non-query execution failed: {e}")
            return False

    def execute_scalar(self, query: str, params: tuple = None):
        """Execute query and return single value"""
        try:
            conn = self.get_connection()
            if not conn:
                return None

            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            result = cursor.fetchone()
            cursor.close()

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Scalar execution failed: {e}")
            return None


def get_database_connection() -> Optional[DatabaseManager]:
    """Get database connection using Streamlit secrets"""
    try:
        # Get database config from secrets
        db_config = st.secrets.get("database", {})

        if not db_config:
            logger.error("Database configuration not found in secrets")
            return None

        # Build connection string
        server = db_config.get("server", "(localdb)\\MSSQLLocalDB")
        database = db_config.get("database", "SDXProjectManager")
        driver = db_config.get("driver", "{ODBC Driver 17 for SQL Server}")

        # Check for Windows Authentication
        if db_config.get("trusted_connection", "").lower() == "yes":
            connection_string = (
                f"DRIVER={driver};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
            )
        else:
            username = db_config.get("username", "")
            password = db_config.get("password", "")
            connection_string = (
                f"DRIVER={driver};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
            )

        # Create and test connection
        db_manager = DatabaseManager(connection_string)
        test_conn = db_manager.get_connection()

        if test_conn:
            logger.info("Database connection successful")
            return db_manager
        else:
            logger.error("Database connection test failed")
            return None

    except Exception as e:
        logger.error(f"Database connection setup failed: {e}")
        return None


# Legacy functions for compatibility
def execute_query(query: str, params: tuple = None) -> list:
    """Execute query using global connection"""
    db = get_database_connection()
    if db:
        return db.execute_query(query, params)
    return []


def execute_non_query(query: str, params: tuple = None) -> bool:
    """Execute non-query using global connection"""
    db = get_database_connection()
    if db:
        return db.execute_non_query(query, params)
    return False
