#!/usr/bin/env python3
"""
config/database.py
Enterprise Database Manager
Production-ready database connection and management
"""

import logging
import pyodbc
import sqlite3
import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import threading
import time
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Enterprise database manager with connection pooling and failover"""

    def __init__(self):
        self.connection = None
        self.connection_pool = []
        self.max_pool_size = 10
        self.current_pool_size = 0
        self._lock = threading.Lock()
        self.connection_string = self._get_connection_string()
        self.db_type = self._detect_db_type()

        # Initialize connection
        self._initialize_connection()

    def _get_connection_string(self) -> str:
        """Get database connection string from secrets"""
        try:
            # Try to get from Streamlit secrets first
            if hasattr(st, "secrets"):
                db_config = st.secrets.get("database", {})
                if db_config:
                    if "mssql" in db_config:
                        return self._build_mssql_connection(db_config["mssql"])
                    elif "sqlite" in db_config:
                        return db_config["sqlite"]["path"]

            # Fallback to SQLite
            db_path = Path("data/sdx_project_manager.db")
            db_path.parent.mkdir(exist_ok=True)
            return str(db_path)

        except Exception as e:
            logger.warning(f"Failed to get connection string: {e}")
            # Emergency fallback
            return "data/emergency.db"

    def _build_mssql_connection(self, config: Dict[str, str]) -> str:
        """Build SQL Server connection string"""
        driver = config.get("driver", "ODBC Driver 17 for SQL Server")
        server = config.get("server", "localhost")
        database = config.get("database", "SDXProjectManager")
        username = config.get("username", "")
        password = config.get("password", "")

        if username and password:
            return f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes"
        else:
            return f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes"

    def _detect_db_type(self) -> str:
        """Detect database type from connection string"""
        if "DRIVER" in self.connection_string.upper():
            return "mssql"
        elif self.connection_string.endswith(".db"):
            return "sqlite"
        else:
            return "sqlite"  # Default fallback

    def _initialize_connection(self):
        """Initialize database connection with retry logic"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                if self.db_type == "mssql":
                    self.connection = pyodbc.connect(
                        self.connection_string, timeout=30, autocommit=False
                    )
                else:
                    self.connection = sqlite3.connect(
                        self.connection_string, timeout=30.0, check_same_thread=False
                    )
                    self.connection.row_factory = sqlite3.Row
                    # Enable foreign keys
                    self.connection.execute("PRAGMA foreign_keys = ON")

                # Test connection
                if self.test_connection():
                    logger.info(f"Database connected successfully ({self.db_type})")
                    self._create_tables_if_not_exist()
                    return

            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    # Final fallback to in-memory SQLite
                    logger.warning("Using in-memory SQLite as last resort")
                    self.connection = sqlite3.connect(
                        ":memory:", check_same_thread=False
                    )
                    self.connection.row_factory = sqlite3.Row
                    self.db_type = "sqlite"
                    self._create_tables_if_not_exist()

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            cursor = self.connection.cursor()
            if self.db_type == "mssql":
                cursor.execute("SELECT 1")
            else:
                cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def _create_tables_if_not_exist(self):
        """Create essential tables if they don't exist"""
        try:
            # Users table
            users_sql = (
                """
            CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username VARCHAR(50) UNIQUE NOT NULL,
                PasswordHash VARCHAR(255) NOT NULL,
                Email VARCHAR(100) UNIQUE NOT NULL,
                FirstName VARCHAR(50) NOT NULL,
                LastName VARCHAR(50) NOT NULL,
                Role VARCHAR(50) DEFAULT 'User',
                Department VARCHAR(100),
                Phone VARCHAR(20),
                IsActive BOOLEAN DEFAULT 1,
                CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                LastLoginDate DATETIME,
                PasswordChangedAt DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
                if self.db_type == "sqlite"
                else """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
            CREATE TABLE Users (
                UserID INT IDENTITY(1,1) PRIMARY KEY,
                Username NVARCHAR(50) UNIQUE NOT NULL,
                PasswordHash NVARCHAR(255) NOT NULL,
                Email NVARCHAR(100) UNIQUE NOT NULL,
                FirstName NVARCHAR(50) NOT NULL,
                LastName NVARCHAR(50) NOT NULL,
                Role NVARCHAR(50) DEFAULT 'User',
                Department NVARCHAR(100),
                Phone NVARCHAR(20),
                IsActive BIT DEFAULT 1,
                CreatedDate DATETIME2 DEFAULT GETDATE(),
                LastLoginDate DATETIME2,
                PasswordChangedAt DATETIME2 DEFAULT GETDATE()
            )
            """
            )

            # Projects table
            projects_sql = (
                """
            CREATE TABLE IF NOT EXISTS Projects (
                ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProjectName VARCHAR(200) NOT NULL,
                Description TEXT,
                Status VARCHAR(50) DEFAULT 'Planning',
                Priority VARCHAR(20) DEFAULT 'Medium',
                StartDate DATE,
                EndDate DATE,
                Budget DECIMAL(15,2),
                ActualCost DECIMAL(15,2) DEFAULT 0,
                ManagerID INTEGER,
                CreatedBy INTEGER,
                CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                UpdatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ManagerID) REFERENCES Users(UserID),
                FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
            )
            """
                if self.db_type == "sqlite"
                else """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
            CREATE TABLE Projects (
                ProjectID INT IDENTITY(1,1) PRIMARY KEY,
                ProjectName NVARCHAR(200) NOT NULL,
                Description NTEXT,
                Status NVARCHAR(50) DEFAULT 'Planning',
                Priority NVARCHAR(20) DEFAULT 'Medium',
                StartDate DATE,
                EndDate DATE,
                Budget DECIMAL(15,2),
                ActualCost DECIMAL(15,2) DEFAULT 0,
                ManagerID INT,
                CreatedBy INT,
                CreatedDate DATETIME2 DEFAULT GETDATE(),
                UpdatedDate DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (ManagerID) REFERENCES Users(UserID),
                FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
            )
            """
            )

            # Tasks table
            tasks_sql = (
                """
            CREATE TABLE IF NOT EXISTS Tasks (
                TaskID INTEGER PRIMARY KEY AUTOINCREMENT,
                ProjectID INTEGER NOT NULL,
                TaskTitle VARCHAR(200) NOT NULL,
                Description TEXT,
                Status VARCHAR(50) DEFAULT 'To Do',
                Priority VARCHAR(20) DEFAULT 'Medium',
                AssignedTo INTEGER,
                EstimatedHours DECIMAL(8,2),
                ActualHours DECIMAL(8,2) DEFAULT 0,
                DueDate DATE,
                CreatedBy INTEGER,
                CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                UpdatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
                FOREIGN KEY (AssignedTo) REFERENCES Users(UserID),
                FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
            )
            """
                if self.db_type == "sqlite"
                else """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
            CREATE TABLE Tasks (
                TaskID INT IDENTITY(1,1) PRIMARY KEY,
                ProjectID INT NOT NULL,
                TaskTitle NVARCHAR(200) NOT NULL,
                Description NTEXT,
                Status NVARCHAR(50) DEFAULT 'To Do',
                Priority NVARCHAR(20) DEFAULT 'Medium',
                AssignedTo INT,
                EstimatedHours DECIMAL(8,2),
                ActualHours DECIMAL(8,2) DEFAULT 0,
                DueDate DATE,
                CreatedBy INT,
                CreatedDate DATETIME2 DEFAULT GETDATE(),
                UpdatedDate DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
                FOREIGN KEY (AssignedTo) REFERENCES Users(UserID),
                FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
            )
            """
            )

            # Execute table creation
            cursor = self.connection.cursor()
            cursor.execute(users_sql)
            cursor.execute(projects_sql)
            cursor.execute(tasks_sql)
            self.connection.commit()
            cursor.close()

            # Insert default admin user if no users exist
            self._create_default_admin()

            logger.info("Database tables created/verified successfully")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def _create_default_admin(self):
        """Create default admin user if no users exist"""
        try:
            # Check if any users exist
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Users")
            user_count = cursor.fetchone()[0]

            if user_count == 0:
                # Create default admin
                import bcrypt

                password_hash = bcrypt.hashpw(
                    "admin123".encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")

                insert_sql = """
                INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                cursor.execute(
                    insert_sql,
                    (
                        "admin",
                        password_hash,
                        "admin@denso.com",
                        "System",
                        "Administrator",
                        "Admin",
                        "IT",
                    ),
                )

                self.connection.commit()
                logger.info("Default admin user created")

            cursor.close()

        except Exception as e:
            logger.error(f"Failed to create default admin: {e}")

    def execute(self, query: str, params: tuple = None) -> Any:
        """Execute SQL query with parameters"""
        try:
            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.connection.rollback()
            raise

    def fetchone(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch single row"""
        try:
            cursor = self.execute(query, params)
            row = cursor.fetchone()
            cursor.close()

            if row:
                if self.db_type == "sqlite":
                    return dict(row)
                else:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, row))
            return None

        except Exception as e:
            logger.error(f"Fetchone failed: {e}")
            return None

    def fetchall(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows"""
        try:
            cursor = self.execute(query, params)
            rows = cursor.fetchall()

            if rows:
                if self.db_type == "sqlite":
                    result = [dict(row) for row in rows]
                else:
                    columns = [column[0] for column in cursor.description]
                    result = [dict(zip(columns, row)) for row in rows]
                cursor.close()
                return result

            cursor.close()
            return []

        except Exception as e:
            logger.error(f"Fetchall failed: {e}")
            return []

    def execute_query(self, query: str, params: tuple = None) -> bool:
        """Execute query and commit"""
        try:
            cursor = self.execute(query, params)
            self.connection.commit()
            cursor.close()
            return True

        except Exception as e:
            logger.error(f"Execute query failed: {e}")
            self.connection.rollback()
            return False

    def get_dataframe(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Get query results as pandas DataFrame"""
        try:
            if params:
                return pd.read_sql_query(query, self.connection, params=params)
            else:
                return pd.read_sql_query(query, self.connection)

        except Exception as e:
            logger.error(f"DataFrame query failed: {e}")
            return pd.DataFrame()

    def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> bool:
        """Bulk insert data"""
        try:
            if not data:
                return True

            # Get column names from first record
            columns = list(data[0].keys())
            placeholders = ", ".join(["?" for _ in columns])

            query = (
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            )

            cursor = self.connection.cursor()

            # Convert data to tuples
            values = [tuple(record[col] for col in columns) for record in data]

            if self.db_type == "sqlite":
                cursor.executemany(query, values)
            else:
                cursor.fast_executemany = True
                cursor.executemany(query, values)

            self.connection.commit()
            cursor.close()

            logger.info(f"Bulk inserted {len(data)} records into {table}")
            return True

        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            self.connection.rollback()
            return False

    def backup_database(self, backup_path: str = None) -> bool:
        """Create database backup"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"data/backups/backup_{timestamp}.db"

            # Ensure backup directory exists
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)

            if self.db_type == "sqlite":
                # SQLite backup
                backup_conn = sqlite3.connect(backup_path)
                self.connection.backup(backup_conn)
                backup_conn.close()
            else:
                # SQL Server backup would require different approach
                logger.warning("SQL Server backup not implemented in this version")
                return False

            logger.info(f"Database backed up to: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table information"""
        try:
            if self.db_type == "sqlite":
                query = f"PRAGMA table_info({table_name})"
            else:
                query = f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                """

            cursor = self.execute(query)
            columns = cursor.fetchall()
            cursor.close()

            return {
                "table_name": table_name,
                "columns": [dict(col) for col in columns] if columns else [],
            }

        except Exception as e:
            logger.error(f"Get table info failed: {e}")
            return {"table_name": table_name, "columns": []}

    def optimize_database(self):
        """Optimize database performance"""
        try:
            cursor = self.connection.cursor()

            if self.db_type == "sqlite":
                # SQLite optimization
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")
                cursor.execute("PRAGMA optimize")
            else:
                # SQL Server optimization
                cursor.execute("UPDATE STATISTICS")

            self.connection.commit()
            cursor.close()

            logger.info("Database optimized successfully")

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")

    def close(self):
        """Close database connection"""
        try:
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Failed to close connection: {e}")

    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close()


# Singleton instance
_db_instance = None
_db_lock = threading.Lock()


def get_database_manager() -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_instance

    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = DatabaseManager()

    return _db_instance


# Database health check
def check_database_health() -> Dict[str, Any]:
    """Check database health status"""
    try:
        db = get_database_manager()

        # Test basic connectivity
        connected = db.test_connection()

        # Get basic stats
        stats = {}
        if connected:
            try:
                # Count users
                users_count = db.fetchone("SELECT COUNT(*) as count FROM Users")
                stats["users_count"] = users_count["count"] if users_count else 0

                # Count projects
                projects_count = db.fetchone("SELECT COUNT(*) as count FROM Projects")
                stats["projects_count"] = (
                    projects_count["count"] if projects_count else 0
                )

                # Count tasks
                tasks_count = db.fetchone("SELECT COUNT(*) as count FROM Tasks")
                stats["tasks_count"] = tasks_count["count"] if tasks_count else 0

            except Exception as e:
                logger.warning(f"Failed to get stats: {e}")
                stats = {"error": str(e)}

        return {
            "connected": connected,
            "db_type": db.db_type,
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
        }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
