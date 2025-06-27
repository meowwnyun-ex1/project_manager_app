# services/enhanced_db_service.py
import pyodbc
import streamlit as st
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from config.settings import db_config, app_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseService:
    """Enhanced database service with connection pooling and error handling"""

    _connection = None

    @classmethod
    @st.cache_resource
    def get_connection(cls):
        """Get cached database connection"""
        if cls._connection is None:
            try:
                conn_str = db_config.get_connection_string()
                if conn_str:
                    cls._connection = pyodbc.connect(
                        conn_str, timeout=app_config.DB_TIMEOUT
                    )
                    cls._connection.autocommit = False
                    logger.info("Database connection established")
                else:
                    st.error("Database configuration not found")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                st.error(f"Database connection error: {e}")

        return cls._connection

    @classmethod
    @contextmanager
    def get_cursor(cls):
        """Get database cursor with automatic cleanup"""
        conn = cls.get_connection()
        if conn:
            cursor = conn.cursor()
            try:
                yield cursor
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation failed: {e}")
                raise
            finally:
                cursor.close()

    @classmethod
    def execute_query(
        cls, query: str, params: Optional[tuple] = None, commit: bool = True
    ) -> bool:
        """Execute INSERT, UPDATE, DELETE queries"""
        try:
            with cls.get_cursor() as cursor:
                cursor.execute(query, params or ())
                if commit:
                    cls.get_connection().commit()

                logger.info(f"Query executed successfully: {query[:100]}...")
                return True

        except pyodbc.Error as e:
            logger.error(f"Query execution failed: {e}")
            st.error(f"Database error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            st.error(f"Unexpected error: {e}")
            return False

    @classmethod
    def fetch_data(
        cls, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data and return as list of dictionaries"""
        try:
            with cls.get_cursor() as cursor:
                cursor.execute(query, params or ())

                # Get column names
                columns = [column[0] for column in cursor.description]

                # Convert rows to dictionaries
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]

                logger.info(f"Fetched {len(data)} rows")
                return data

        except pyodbc.Error as e:
            logger.error(f"Data fetch failed: {e}")
            st.error(f"Database error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during fetch: {e}")
            st.error(f"Unexpected error: {e}")
            return []

    @classmethod
    def fetch_one(
        cls, query: str, params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch single row and return as dictionary"""
        try:
            with cls.get_cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()

                if row:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, row))
                return None

        except pyodbc.Error as e:
            logger.error(f"Single row fetch failed: {e}")
            st.error(f"Database error: {e}")
            return None

    @classmethod
    def execute_scalar(cls, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query and return single value"""
        try:
            with cls.get_cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                return row[0] if row else None

        except pyodbc.Error as e:
            logger.error(f"Scalar query failed: {e}")
            st.error(f"Database error: {e}")
            return None

    @classmethod
    def execute_batch(cls, query: str, params_list: List[tuple]) -> bool:
        """Execute batch operations"""
        try:
            with cls.get_cursor() as cursor:
                cursor.executemany(query, params_list)
                cls.get_connection().commit()
                logger.info(f"Batch operation completed: {len(params_list)} rows")
                return True

        except pyodbc.Error as e:
            logger.error(f"Batch operation failed: {e}")
            st.error(f"Database error: {e}")
            return False

    @classmethod
    def test_connection(cls) -> bool:
        """Test database connection"""
        try:
            result = cls.execute_scalar("SELECT 1")
            return result == 1
        except:
            return False


# Backward compatibility aliases
def get_db_connection():
    """Legacy function for backward compatibility"""
    return DatabaseService.get_connection()


def fetch_data(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility"""
    return DatabaseService.fetch_data(query, params)


def execute_query(query: str, params: Optional[tuple] = None) -> bool:
    """Legacy function for backward compatibility"""
    return DatabaseService.execute_query(query, params)
