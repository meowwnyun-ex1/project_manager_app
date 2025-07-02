# services/enhanced_db_service.py
import streamlit as st
import pyodbc
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps
import time
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class DatabaseException(Exception):
    """Custom database exception"""

    pass


class ConnectionManager:
    """Database connection manager with pooling"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.last_ping = None

    def get_connection(self):
        """Get database connection with retry logic"""
        if not self.connection or not self._is_connection_alive():
            self._create_connection()
        return self.connection

    def _create_connection(self):
        """Create new database connection"""
        try:
            self.connection = pyodbc.connect(self.connection_string, timeout=30)
            self.last_ping = datetime.now()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise DatabaseException(f"Database connection failed: {str(e)}")

    def _is_connection_alive(self) -> bool:
        """Check if connection is still alive"""
        if not self.connection:
            return False

        try:
            # Check if connection is older than 5 minutes
            if self.last_ping and (datetime.now() - self.last_ping).seconds > 300:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.last_ping = datetime.now()
            return True
        except Exception:
            return False

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def close(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


def with_db_transaction(func):
    """Decorator for database transactions"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        instance = args[0] if args else None
        if not instance or not hasattr(instance, "connection_manager"):
            return func(*args, **kwargs)

        conn = None
        try:
            conn = instance.connection_manager.get_connection()
            result = func(*args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Transaction failed: {str(e)}")
            raise

    return wrapper


def cached_query(cache_key: str, ttl: int = 300):
    """Decorator for caching query results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Simple in-memory cache using session state
            cache = st.session_state.get("query_cache", {})

            # Create full cache key
            full_key = f"{cache_key}_{hash(str(args) + str(kwargs))}"

            # Check cache
            if full_key in cache:
                cached_data, timestamp = cache[full_key]
                if (datetime.now() - timestamp).seconds < ttl:
                    return cached_data

            # Execute function and cache result
            result = func(*args, **kwargs)

            # Store in cache
            if "query_cache" not in st.session_state:
                st.session_state.query_cache = {}

            st.session_state.query_cache[full_key] = (result, datetime.now())

            return result

        return wrapper

    return decorator


class EnhancedDBService:
    """Enhanced database service with connection pooling and caching"""

    def __init__(self, connection_string: str = None):
        if not connection_string:
            connection_string = self._get_connection_string()

        self.connection_manager = ConnectionManager(connection_string)
        self.cache = {}

    def _get_connection_string(self) -> str:
        """Get connection string from secrets"""
        try:
            db_config = st.secrets.get("database", {})

            if db_config.get("trusted_connection", "no").lower() == "yes":
                return (
                    f"DRIVER={{{db_config.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
                    f"SERVER={db_config.get('server', 'localhost')},{db_config.get('port', 1433)};"
                    f"DATABASE={db_config.get('database', 'ProjectManagerDB')};"
                    "Trusted_Connection=yes;"
                )
            else:
                return (
                    f"DRIVER={{{db_config.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
                    f"SERVER={db_config.get('server', 'localhost')},{db_config.get('port', 1433)};"
                    f"DATABASE={db_config.get('database', 'ProjectManagerDB')};"
                    f"UID={db_config.get('username', 'sa')};"
                    f"PWD={db_config.get('password', '')};"
                )
        except Exception as e:
            logger.error(f"Failed to get connection string: {str(e)}")
            # Default connection string for development
            return (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=localhost,1433;"
                "DATABASE=ProjectManagerDB;"
                "UID=sa;"
                "PWD=YourPassword123;"
            )

    def execute_query(
        self, query: str, params: tuple = None, fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            conn = self.connection_manager.get_connection()
            cursor = conn.cursor()

            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch:
                # Get column names
                columns = (
                    [column[0] for column in cursor.description]
                    if cursor.description
                    else []
                )

                # Fetch all rows
                rows = cursor.fetchall()

                # Convert to list of dictionaries
                result = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = value
                    result.append(row_dict)

                cursor.close()
                return result
            else:
                cursor.close()
                return []

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseException(f"Query failed: {str(e)}")

    def setup_database(self) -> bool:
        """Setup database schema"""
        try:
            schema_queries = [
                # Users table
                """
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
                CREATE TABLE Users (
                    UserID INT IDENTITY(1,1) PRIMARY KEY,
                    Username NVARCHAR(100) UNIQUE NOT NULL,
                    PasswordHash NVARCHAR(255) NOT NULL,
                    Email NVARCHAR(255) UNIQUE NOT NULL,
                    FirstName NVARCHAR(100),
                    LastName NVARCHAR(100),
                    Role NVARCHAR(50) DEFAULT 'User',
                    Active BIT DEFAULT 1,
                    CreatedDate DATETIME DEFAULT GETDATE(),
                    LastLoginDate DATETIME,
                    PasswordChangedDate DATETIME,
                    ProfilePicture NVARCHAR(500)
                )
                """,
                # Projects table
                """
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
                CREATE TABLE Projects (
                    ProjectID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectName NVARCHAR(200) NOT NULL,
                    Description NTEXT,
                    StartDate DATE,
                    EndDate DATE,
                    Status NVARCHAR(50) DEFAULT 'Planning',
                    Priority NVARCHAR(50) DEFAULT 'Medium',
                    Budget DECIMAL(18,2),
                    ClientName NVARCHAR(200),
                    CreatedBy INT,
                    CreatedDate DATETIME DEFAULT GETDATE(),
                    LastModifiedDate DATETIME DEFAULT GETDATE(),
                    Tags NVARCHAR(500),
                    Progress INT DEFAULT 0,
                    FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
                )
                """,
                # Tasks table
                """
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
                CREATE TABLE Tasks (
                    TaskID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectID INT NOT NULL,
                    TaskName NVARCHAR(200) NOT NULL,
                    Description NTEXT,
                    StartDate DATE,
                    EndDate DATE,
                    AssigneeID INT,
                    Status NVARCHAR(50) DEFAULT 'To Do',
                    Priority NVARCHAR(50) DEFAULT 'Medium',
                    Progress INT DEFAULT 0,
                    EstimatedHours DECIMAL(8,2),
                    ActualHours DECIMAL(8,2),
                    Dependencies NVARCHAR(500),
                    Labels NVARCHAR(500),
                    CreatedBy INT,
                    CreatedDate DATETIME DEFAULT GETDATE(),
                    LastModifiedDate DATETIME DEFAULT GETDATE(),
                    CompletedDate DATETIME,
                    DueDate DATE,
                    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
                    FOREIGN KEY (AssigneeID) REFERENCES Users(UserID),
                    FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
                )
                """,
                # Insert default admin user
                """
                IF NOT EXISTS (SELECT * FROM Users WHERE Username = 'admin')
                INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role)
                VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG', 'admin@projectmanager.local', 'Admin', 'User', 'Admin')
                """,
            ]

            for query in schema_queries:
                self.execute_query(query, fetch=False)

            logger.info("Database schema setup completed")
            return True

        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            return False

    def get_dashboard_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard metrics for user"""
        try:
            # Get project counts
            project_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN Status = 'In Progress' THEN 1 END) as active,
                    COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as completed
                FROM Projects 
                WHERE CreatedBy = ?
            """
            project_result = self.execute_query(project_query, (user_id,))
            projects = (
                project_result[0]
                if project_result
                else {"total": 0, "active": 0, "completed": 0}
            )

            # Get task counts
            task_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN Status IN ('To Do', 'In Progress') THEN 1 END) as active,
                    COUNT(CASE WHEN Status = 'Done' THEN 1 END) as completed,
                    COUNT(CASE WHEN DueDate < GETDATE() AND Status != 'Done' THEN 1 END) as overdue
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                WHERE p.CreatedBy = ?
            """
            task_result = self.execute_query(task_query, (user_id,))
            tasks = (
                task_result[0]
                if task_result
                else {"total": 0, "active": 0, "completed": 0, "overdue": 0}
            )

            return {"projects": projects, "tasks": tasks}

        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {str(e)}")
            return {
                "projects": {"total": 0, "active": 0, "completed": 0},
                "tasks": {"total": 0, "active": 0, "completed": 0, "overdue": 0},
            }

    def clear_cache(self, pattern: str = None):
        """Clear query cache"""
        if pattern:
            # Clear specific pattern
            keys_to_remove = [
                key
                for key in st.session_state.get("query_cache", {}).keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del st.session_state.query_cache[key]
        else:
            # Clear all cache
            if "query_cache" in st.session_state:
                st.session_state.query_cache = {}


# Global service instance
_db_service = None


def get_db_service() -> EnhancedDBService:
    """Get global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = EnhancedDBService()
    return _db_service
