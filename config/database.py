#!/usr/bin/env python3
"""
config/database.py
Enterprise Database Manager with Connection Pooling and Production Features
Supports multiple database backends with automatic failover and monitoring
"""

import os
import logging
import time
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import streamlit as st
import sqlalchemy as sa
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
import pandas as pd
import pymssql
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management"""

    def __init__(self):
        self.load_config()

    def load_config(self):
        """Load database configuration from multiple sources"""
        # Priority: Streamlit secrets > Environment variables > Default

        # Production database settings
        self.sql_server = {
            "server": self._get_config("sql_server_host", "localhost"),
            "database": self._get_config("sql_server_db", "SDX_ProjectManager"),
            "username": self._get_config("sql_server_user", "sa"),
            "password": self._get_config("sql_server_password", "YourPassword123"),
            "port": int(self._get_config("sql_server_port", "1433")),
            "driver": "ODBC Driver 17 for SQL Server",
        }

        # SQLite fallback for development
        self.sqlite = {
            "path": self._get_config("sqlite_path", "data/sdx_project_manager.db"),
            "timeout": 30,
            "check_same_thread": False,
        }

        # Connection pool settings
        self.pool_settings = {
            "pool_size": int(self._get_config("db_pool_size", "10")),
            "max_overflow": int(self._get_config("db_max_overflow", "20")),
            "pool_timeout": int(self._get_config("db_pool_timeout", "30")),
            "pool_recycle": int(self._get_config("db_pool_recycle", "3600")),
            "pool_pre_ping": True,
        }

        # Performance settings
        self.performance = {
            "query_timeout": int(self._get_config("db_query_timeout", "30")),
            "connection_timeout": int(self._get_config("db_connection_timeout", "10")),
            "retry_attempts": int(self._get_config("db_retry_attempts", "3")),
            "retry_delay": float(self._get_config("db_retry_delay", "1.0")),
        }

    def _get_config(self, key: str, default: str) -> str:
        """Get configuration value with fallback priority"""
        # 1. Streamlit secrets
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]

        # 2. Environment variables
        env_value = os.getenv(key.upper())
        if env_value:
            return env_value

        # 3. Default value
        return default


class ConnectionPool:
    """Advanced connection pool with health monitoring"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engines = {}
        self.health_status = {}
        self.last_health_check = {}
        self.lock = threading.Lock()

    def get_engine(self, db_type: str = "auto") -> Engine:
        """Get database engine with automatic failover"""
        if db_type == "auto":
            db_type = self._determine_best_db()

        with self.lock:
            if db_type not in self.engines:
                self.engines[db_type] = self._create_engine(db_type)

            # Health check
            if self._should_health_check(db_type):
                if not self._health_check(db_type):
                    # Try alternative database
                    alt_db = "sqlite" if db_type == "sql_server" else "sql_server"
                    logger.warning(f"Switching from {db_type} to {alt_db}")
                    return self.get_engine(alt_db)

            return self.engines[db_type]

    def _determine_best_db(self) -> str:
        """Determine best available database"""
        # Try SQL Server first for production
        if self._test_sql_server_connection():
            return "sql_server"

        # Fallback to SQLite
        logger.info("Using SQLite as fallback database")
        return "sqlite"

    def _test_sql_server_connection(self) -> bool:
        """Test SQL Server connectivity"""
        try:
            import pymssql

            conn = pymssql.connect(
                server=self.config.sql_server["server"],
                user=self.config.sql_server["username"],
                password=self.config.sql_server["password"],
                database=self.config.sql_server["database"],
                timeout=5,
            )
            conn.close()
            return True
        except Exception as e:
            logger.debug(f"SQL Server connection test failed: {e}")
            return False

    def _create_engine(self, db_type: str) -> Engine:
        """Create database engine with optimized settings"""
        if db_type == "sql_server":
            # SQL Server connection string
            connection_string = (
                f"mssql+pymssql://{self.config.sql_server['username']}:"
                f"{self.config.sql_server['password']}@"
                f"{self.config.sql_server['server']}:"
                f"{self.config.sql_server['port']}/"
                f"{self.config.sql_server['database']}"
                f"?charset=utf8"
            )

            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                **self.config.pool_settings,
                echo=False,
                connect_args={
                    "timeout": self.config.performance["connection_timeout"],
                    "autocommit": True,
                },
            )

        elif db_type == "sqlite":
            # Ensure SQLite directory exists
            db_path = Path(self.config.sqlite["path"])
            db_path.parent.mkdir(parents=True, exist_ok=True)

            connection_string = f"sqlite:///{db_path}"

            engine = create_engine(
                connection_string,
                poolclass=StaticPool,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                connect_args={
                    "timeout": self.config.sqlite["timeout"],
                    "check_same_thread": self.config.sqlite["check_same_thread"],
                },
            )

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Test the engine
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Successfully created {db_type} engine")
            return engine

        except Exception as e:
            logger.error(f"Failed to create {db_type} engine: {e}")
            raise

    def _should_health_check(self, db_type: str) -> bool:
        """Check if health check is needed"""
        last_check = self.last_health_check.get(db_type, datetime.min)
        return (datetime.now() - last_check).seconds > 300  # 5 minutes

    def _health_check(self, db_type: str) -> bool:
        """Perform database health check"""
        try:
            engine = self.engines[db_type]
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()

            self.health_status[db_type] = True
            self.last_health_check[db_type] = datetime.now()
            return True

        except Exception as e:
            logger.warning(f"Health check failed for {db_type}: {e}")
            self.health_status[db_type] = False
            return False


class DatabaseManager:
    """Enterprise-grade database manager with monitoring and optimization"""

    def __init__(self):
        self.config = DatabaseConfig()
        self.pool = ConnectionPool(self.config)
        self.query_cache = {}
        self.performance_stats = {
            "total_queries": 0,
            "failed_queries": 0,
            "avg_query_time": 0.0,
            "slowest_queries": [],
        }
        self.setup_database()

    def setup_database(self):
        """Initialize database schema if needed"""
        try:
            # Check if tables exist
            if not self._tables_exist():
                logger.info("Initializing database schema...")
                self._create_schema()
                self._insert_sample_data()
                logger.info("Database schema created successfully")
            else:
                logger.info("Database schema already exists")

        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise

    def _tables_exist(self) -> bool:
        """Check if required tables exist"""
        try:
            result = self.execute_scalar(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'Users'"
            )
            return result > 0
        except:
            # For SQLite, try a different approach
            try:
                result = self.execute_scalar(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='Users'"
                )
                return result > 0
            except:
                return False

    def _create_schema(self):
        """Create database schema"""
        schema_sql = """
        -- Users table
        CREATE TABLE Users (
            UserID INTEGER PRIMARY KEY IDENTITY(1,1),
            Username NVARCHAR(50) UNIQUE NOT NULL,
            PasswordHash NVARCHAR(255) NOT NULL,
            FullName NVARCHAR(100) NOT NULL,
            Email NVARCHAR(100) UNIQUE NOT NULL,
            Role NVARCHAR(50) NOT NULL DEFAULT 'User',
            Department NVARCHAR(100),
            IsActive BIT DEFAULT 1,
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            UpdatedAt DATETIME2 DEFAULT GETDATE(),
            LastLogin DATETIME2,
            ProfileImage NVARCHAR(500),
            Phone NVARCHAR(20),
            Position NVARCHAR(100)
        );
        
        -- Projects table
        CREATE TABLE Projects (
            ProjectID INTEGER PRIMARY KEY IDENTITY(1,1),
            Name NVARCHAR(200) NOT NULL,
            Description NTEXT,
            Status NVARCHAR(50) DEFAULT 'Planning',
            Priority NVARCHAR(20) DEFAULT 'Medium',
            StartDate DATE,
            EndDate DATE,
            Budget DECIMAL(15,2),
            ActualCost DECIMAL(15,2) DEFAULT 0,
            Progress INTEGER DEFAULT 0,
            ManagerID INTEGER,
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            UpdatedAt DATETIME2 DEFAULT GETDATE(),
            IsActive BIT DEFAULT 1,
            ProjectCode NVARCHAR(20) UNIQUE,
            Category NVARCHAR(100),
            ClientName NVARCHAR(200),
            FOREIGN KEY (ManagerID) REFERENCES Users(UserID)
        );
        
        -- Tasks table
        CREATE TABLE Tasks (
            TaskID INTEGER PRIMARY KEY IDENTITY(1,1),
            ProjectID INTEGER NOT NULL,
            Title NVARCHAR(200) NOT NULL,
            Description NTEXT,
            Status NVARCHAR(50) DEFAULT 'To Do',
            Priority NVARCHAR(20) DEFAULT 'Medium',
            AssignedTo INTEGER,
            CreatedBy INTEGER,
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            UpdatedAt DATETIME2 DEFAULT GETDATE(),
            DueDate DATETIME2,
            CompletedAt DATETIME2,
            EstimatedHours DECIMAL(6,2),
            ActualHours DECIMAL(6,2),
            Progress INTEGER DEFAULT 0,
            IsActive BIT DEFAULT 1,
            TaskCode NVARCHAR(20),
            Category NVARCHAR(100),
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
            FOREIGN KEY (AssignedTo) REFERENCES Users(UserID),
            FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
        );
        
        -- Project Members table
        CREATE TABLE ProjectMembers (
            ProjectMemberID INTEGER PRIMARY KEY IDENTITY(1,1),
            ProjectID INTEGER NOT NULL,
            UserID INTEGER NOT NULL,
            Role NVARCHAR(50) DEFAULT 'Member',
            JoinedAt DATETIME2 DEFAULT GETDATE(),
            IsActive BIT DEFAULT 1,
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
            FOREIGN KEY (UserID) REFERENCES Users(UserID),
            UNIQUE(ProjectID, UserID)
        );
        
        -- Time Tracking table
        CREATE TABLE TimeTracking (
            TimeTrackingID INTEGER PRIMARY KEY IDENTITY(1,1),
            TaskID INTEGER NOT NULL,
            UserID INTEGER NOT NULL,
            StartTime DATETIME2 NOT NULL,
            EndTime DATETIME2,
            Hours DECIMAL(6,2),
            Description NVARCHAR(500),
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID),
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );
        
        -- Comments table
        CREATE TABLE Comments (
            CommentID INTEGER PRIMARY KEY IDENTITY(1,1),
            TaskID INTEGER,
            ProjectID INTEGER,
            UserID INTEGER NOT NULL,
            Content NTEXT NOT NULL,
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            UpdatedAt DATETIME2 DEFAULT GETDATE(),
            IsActive BIT DEFAULT 1,
            FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID),
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );
        
        -- Notifications table
        CREATE TABLE Notifications (
            NotificationID INTEGER PRIMARY KEY IDENTITY(1,1),
            UserID INTEGER NOT NULL,
            Title NVARCHAR(200) NOT NULL,
            Message NTEXT NOT NULL,
            Type NVARCHAR(50) DEFAULT 'Info',
            IsRead BIT DEFAULT 0,
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            ReadAt DATETIME2,
            RelatedTaskID INTEGER,
            RelatedProjectID INTEGER,
            FOREIGN KEY (UserID) REFERENCES Users(UserID),
            FOREIGN KEY (RelatedTaskID) REFERENCES Tasks(TaskID),
            FOREIGN KEY (RelatedProjectID) REFERENCES Projects(ProjectID)
        );
        
        -- System Settings table
        CREATE TABLE SystemSettings (
            SettingID INTEGER PRIMARY KEY IDENTITY(1,1),
            SettingKey NVARCHAR(100) UNIQUE NOT NULL,
            SettingValue NTEXT,
            Description NVARCHAR(500),
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            UpdatedAt DATETIME2 DEFAULT GETDATE()
        );
        
        -- Audit Log table
        CREATE TABLE AuditLog (
            AuditID INTEGER PRIMARY KEY IDENTITY(1,1),
            UserID INTEGER,
            Action NVARCHAR(100) NOT NULL,
            TableName NVARCHAR(100),
            RecordID INTEGER,
            OldValues NTEXT,
            NewValues NTEXT,
            IPAddress NVARCHAR(45),
            UserAgent NVARCHAR(500),
            CreatedAt DATETIME2 DEFAULT GETDATE(),
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );
        
        -- Create indexes for performance
        CREATE INDEX IX_Tasks_ProjectID ON Tasks(ProjectID);
        CREATE INDEX IX_Tasks_AssignedTo ON Tasks(AssignedTo);
        CREATE INDEX IX_Tasks_Status ON Tasks(Status);
        CREATE INDEX IX_Tasks_DueDate ON Tasks(DueDate);
        CREATE INDEX IX_Projects_ManagerID ON Projects(ManagerID);
        CREATE INDEX IX_Projects_Status ON Projects(Status);
        CREATE INDEX IX_ProjectMembers_ProjectID ON ProjectMembers(ProjectID);
        CREATE INDEX IX_ProjectMembers_UserID ON ProjectMembers(UserID);
        CREATE INDEX IX_Notifications_UserID ON Notifications(UserID);
        CREATE INDEX IX_Notifications_IsRead ON Notifications(IsRead);
        CREATE INDEX IX_AuditLog_UserID ON AuditLog(UserID);
        CREATE INDEX IX_AuditLog_CreatedAt ON AuditLog(CreatedAt);
        """

        # Execute schema creation
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    self.execute_query(statement)
                except Exception as e:
                    # Handle SQLite-specific adjustments
                    if "IDENTITY" in statement:
                        statement = statement.replace(
                            "INTEGER PRIMARY KEY IDENTITY(1,1)",
                            "INTEGER PRIMARY KEY AUTOINCREMENT",
                        )
                        statement = statement.replace("DATETIME2", "DATETIME")
                        statement = statement.replace("NVARCHAR", "TEXT")
                        statement = statement.replace("NTEXT", "TEXT")
                        statement = statement.replace("BIT", "INTEGER")
                        statement = statement.replace("DECIMAL", "REAL")
                        statement = statement.replace("GETDATE()", "datetime('now')")
                        try:
                            self.execute_query(statement)
                        except Exception as e2:
                            logger.warning(f"Schema creation warning: {e2}")
                    else:
                        logger.warning(f"Schema creation warning: {e}")

    def _insert_sample_data(self):
        """Insert sample data for demonstration"""
        try:
            # Create admin user
            admin_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlrjOUO6l4Tqm9G"  # admin123

            self.execute_query(
                """
            INSERT INTO Users (Username, PasswordHash, FullName, Email, Role, Department, Position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "admin",
                    admin_password,
                    "ผู้ดูแลระบบ",
                    "admin@denso.com",
                    "Admin",
                    "IT",
                    "System Administrator",
                ),
            )

            # Create sample users
            sample_users = [
                (
                    "manager",
                    admin_password,
                    "วิชัย ใจดี",
                    "wichai@denso.com",
                    "Project Manager",
                    "Innovation",
                    "Project Manager",
                ),
                (
                    "developer",
                    admin_password,
                    "สมชาย รักงาน",
                    "somchai@denso.com",
                    "Developer",
                    "IT",
                    "Senior Developer",
                ),
                (
                    "designer",
                    admin_password,
                    "นิสา สร้างสรรค์",
                    "nisa@denso.com",
                    "User",
                    "Design",
                    "UI/UX Designer",
                ),
                (
                    "analyst",
                    admin_password,
                    "ประวิทย์ วิเคราะห์",
                    "prawit@denso.com",
                    "User",
                    "Analytics",
                    "Data Analyst",
                ),
            ]

            for user in sample_users:
                try:
                    self.execute_query(
                        """
                    INSERT INTO Users (Username, PasswordHash, FullName, Email, Role, Department, Position)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        user,
                    )
                except:
                    pass  # User might already exist

            # Create sample projects
            sample_projects = [
                (
                    "Website Redesign",
                    "การออกแบบเว็บไซต์ใหม่ให้ทันสมัย",
                    "Active",
                    "High",
                    "2024-07-01",
                    "2024-12-31",
                    500000,
                    "WEB001",
                    "Web Development",
                ),
                (
                    "Mobile App",
                    "พัฒนาแอพพลิเคชันมือถือ",
                    "Planning",
                    "Medium",
                    "2024-08-01",
                    "2025-02-28",
                    800000,
                    "MOB001",
                    "Mobile Development",
                ),
                (
                    "Data Analytics Platform",
                    "ระบบวิเคราะห์ข้อมูล",
                    "Active",
                    "High",
                    "2024-06-15",
                    "2024-11-30",
                    1200000,
                    "DAT001",
                    "Data Science",
                ),
            ]

            for project in sample_projects:
                try:
                    self.execute_query(
                        """
                    INSERT INTO Projects (Name, Description, Status, Priority, StartDate, EndDate, Budget, ProjectCode, Category, ManagerID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        project + (1,),
                    )
                except:
                    pass  # Project might already exist

            # Insert system settings
            system_settings = [
                ("app_name", "SDX Project Manager", "Application name"),
                ("app_version", "2.5.0", "Application version"),
                ("default_language", "th", "Default language"),
                ("session_timeout", "3600", "Session timeout in seconds"),
                ("max_upload_size", "10", "Maximum upload size in MB"),
                ("backup_frequency", "daily", "Database backup frequency"),
            ]

            for setting in system_settings:
                try:
                    self.execute_query(
                        """
                    INSERT INTO SystemSettings (SettingKey, SettingValue, Description)
                    VALUES (?, ?, ?)
                    """,
                        setting,
                    )
                except:
                    pass  # Setting might already exist

            logger.info("Sample data inserted successfully")

        except Exception as e:
            logger.error(f"Failed to insert sample data: {e}")

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        engine = self.pool.get_engine()
        connection = None

        try:
            connection = engine.connect()
            yield connection

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise

        finally:
            if connection:
                connection.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query with performance monitoring and retry logic"""
        start_time = time.time()

        for attempt in range(self.config.performance["retry_attempts"]):
            try:
                with self.get_connection() as conn:
                    if params:
                        result = conn.execute(text(query), params)
                    else:
                        result = conn.execute(text(query))

                    # Handle different result types
                    if result.returns_rows:
                        rows = result.fetchall()
                        return [dict(row._mapping) for row in rows]
                    else:
                        conn.commit()
                        return []

            except DisconnectionError as e:
                logger.warning(f"Database disconnection (attempt {attempt + 1}): {e}")
                if attempt < self.config.performance["retry_attempts"] - 1:
                    time.sleep(self.config.performance["retry_delay"] * (attempt + 1))
                    continue
                raise

            except Exception as e:
                logger.error(f"Query execution failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.performance["retry_attempts"] - 1:
                    time.sleep(self.config.performance["retry_delay"])
                    continue
                raise

            finally:
                # Record performance metrics
                execution_time = time.time() - start_time
                self._record_performance(query, execution_time, params)

    def execute_scalar(self, query: str, params: tuple = None) -> Any:
        """Execute query and return single value"""
        try:
            with self.get_connection() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))

                return result.scalar()

        except Exception as e:
            logger.error(f"Scalar query failed: {e}")
            return None

    def execute_dataframe(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return pandas DataFrame"""
        try:
            engine = self.pool.get_engine()

            if params:
                df = pd.read_sql(query, engine, params=params)
            else:
                df = pd.read_sql(query, engine)

            return df

        except Exception as e:
            logger.error(f"DataFrame query failed: {e}")
            return pd.DataFrame()

    def _record_performance(
        self, query: str, execution_time: float, params: tuple = None
    ):
        """Record query performance metrics"""
        self.performance_stats["total_queries"] += 1

        # Update average query time
        current_avg = self.performance_stats["avg_query_time"]
        total_queries = self.performance_stats["total_queries"]
        self.performance_stats["avg_query_time"] = (
            current_avg * (total_queries - 1) + execution_time
        ) / total_queries

        # Track slow queries
        if execution_time > 1.0:  # Queries taking more than 1 second
            slow_query = {
                "query": query[:100] + "..." if len(query) > 100 else query,
                "execution_time": execution_time,
                "timestamp": datetime.now(),
                "params": str(params) if params else None,
            }

            self.performance_stats["slowest_queries"].append(slow_query)

            # Keep only last 10 slow queries
            if len(self.performance_stats["slowest_queries"]) > 10:
                self.performance_stats["slowest_queries"].pop(0)

            logger.warning(f"Slow query detected: {execution_time:.2f}s")

    def get_performance_stats(self) -> Dict:
        """Get database performance statistics"""
        return self.performance_stats.copy()

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_info = {
            "status": "unknown",
            "database_type": "unknown",
            "connection_pool": {},
            "performance": self.performance_stats,
            "last_check": datetime.now(),
        }

        try:
            # Test basic connectivity
            result = self.execute_scalar("SELECT 1")
            if result == 1:
                health_info["status"] = "healthy"

            # Determine database type
            try:
                self.execute_scalar("SELECT @@VERSION")
                health_info["database_type"] = "sql_server"
            except:
                health_info["database_type"] = "sqlite"

            # Pool information
            engine = self.pool.get_engine()
            pool = engine.pool
            health_info["connection_pool"] = {
                "size": getattr(pool, "size", lambda: "N/A")(),
                "checked_in": getattr(pool, "checkedin", lambda: "N/A")(),
                "checked_out": getattr(pool, "checkedout", lambda: "N/A")(),
                "invalid": getattr(pool, "invalid", lambda: "N/A")(),
            }

        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["error"] = str(e)
            logger.error(f"Health check failed: {e}")

        return health_info

    def backup_database(self, backup_path: str = None) -> bool:
        """Create database backup"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"data/backups/backup_{timestamp}.sql"

            # Ensure backup directory exists
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)

            # Export schema and data
            tables = [
                "Users",
                "Projects",
                "Tasks",
                "ProjectMembers",
                "TimeTracking",
                "Comments",
                "Notifications",
                "SystemSettings",
                "AuditLog",
            ]

            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(f"-- SDX Project Manager Database Backup\n")
                f.write(f"-- Created: {datetime.now()}\n\n")

                for table in tables:
                    try:
                        df = self.execute_dataframe(f"SELECT * FROM {table}")
                        if not df.empty:
                            f.write(f"-- Table: {table}\n")
                            # Convert DataFrame to SQL INSERT statements
                            for _, row in df.iterrows():
                                values = [
                                    f"'{str(v)}'" if pd.notna(v) else "NULL"
                                    for v in row
                                ]
                                f.write(
                                    f"INSERT INTO {table} VALUES ({', '.join(values)});\n"
                                )
                            f.write("\n")
                    except Exception as e:
                        logger.warning(f"Backup warning for table {table}: {e}")

            logger.info(f"Database backup created: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False


# Global connection manager instance
@st.cache_resource
def get_database_connection():
    """Get cached database connection"""
    return DatabaseManager()


# Utility functions for backward compatibility
def get_db_manager():
    """Get database manager instance"""
    return get_database_connection()
