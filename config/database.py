#!/usr/bin/env python3
"""
config/database.py
Direct SSMS Connection สำหรับ DENSO Project Manager Pro
"""
import pyodbc
import streamlit as st
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Production database configuration"""

    server: str
    database: str
    username: str
    password: str
    driver: str = "ODBC Driver 17 for SQL Server"
    connection_timeout: int = 30
    command_timeout: int = 60

    def get_connection_string(self) -> str:
        """สร้าง connection string สำหรับ SSMS"""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Connection Timeout={self.connection_timeout};"
            f"Command Timeout={self.command_timeout};"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
            f"MultipleActiveResultSets=true;"
        )


class ConnectionPool:
    """Simple connection pool for database connections"""

    def __init__(self, config: DatabaseConfig, pool_size: int = 10):
        self.config = config
        self.pool_size = pool_size
        self.connections = []
        self.lock = threading.Lock()
        self._create_pool()

    def _create_pool(self):
        """สร้าง connection pool"""
        for _ in range(self.pool_size):
            try:
                conn = pyodbc.connect(self.config.get_connection_string())
                self.connections.append(conn)
            except Exception as e:
                logger.warning(f"Failed to create connection: {e}")

    @contextmanager
    def get_connection(self):
        """ได้ connection จาก pool"""
        conn = None
        try:
            with self.lock:
                if self.connections:
                    conn = self.connections.pop()
                else:
                    conn = pyodbc.connect(self.config.get_connection_string())

            yield conn

        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    with self.lock:
                        if len(self.connections) < self.pool_size:
                            self.connections.append(conn)
                        else:
                            conn.close()
                except:
                    pass


class DatabaseManager:
    """Database manager สำหรับ DENSO Project Manager Pro"""

    def __init__(self):
        self.config = self._load_config()
        self.pool = ConnectionPool(self.config)
        self._initialized = False
        self._init_database()

    def _load_config(self) -> DatabaseConfig:
        """โหลด config จาก secrets.toml"""
        try:
            db_config = st.secrets["database"]
            return DatabaseConfig(
                server=db_config["server"],
                database=db_config["database"],
                username=db_config["username"],
                password=db_config["password"],
                driver=db_config.get("driver", "ODBC Driver 17 for SQL Server"),
                connection_timeout=db_config.get("connection_options", {}).get(
                    "connection_timeout", 30
                ),
                command_timeout=db_config.get("connection_options", {}).get(
                    "command_timeout", 60
                ),
            )
        except Exception as e:
            logger.error(f"Failed to load database config: {e}")
            raise

    def _init_database(self):
        """Initialize database และสร้างตารางถ้าจำเป็น"""
        if self._initialized:
            return

        try:
            if self.test_connection():
                self._ensure_tables_exist()
                self._create_default_data()
                self._initialized = True
                logger.info("Database initialized successfully")
            else:
                raise Exception("Database connection failed")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def test_connection(self) -> bool:
        """ทดสอบการเชื่อมต่อฐานข้อมูล"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION, GETDATE(), @@SERVERNAME")
                result = cursor.fetchone()
                logger.info(f"Database connection successful - Server: {result[2]}")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def _ensure_tables_exist(self):
        """ตรวจสอบและสร้างตารางที่จำเป็น"""
        schema_sql = """
        -- Users table
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
        CREATE TABLE Users (
            UserID INT IDENTITY(1,1) PRIMARY KEY,
            Username NVARCHAR(50) UNIQUE NOT NULL,
            PasswordHash NVARCHAR(255) NOT NULL,
            Email NVARCHAR(100) UNIQUE NOT NULL,
            FirstName NVARCHAR(50) NOT NULL,
            LastName NVARCHAR(50) NOT NULL,
            Role NVARCHAR(20) DEFAULT 'User' CHECK (Role IN ('Admin', 'Project Manager', 'Team Lead', 'Developer', 'User', 'Viewer')),
            Department NVARCHAR(50),
            IsActive BIT DEFAULT 1,
            CreatedDate DATETIME DEFAULT GETDATE(),
            LastLoginDate DATETIME,
            FailedLoginAttempts INT DEFAULT 0,
            LastFailedLogin DATETIME,
            IsLocked BIT DEFAULT 0,
            MustChangePassword BIT DEFAULT 1
        );

        -- Projects table
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
        CREATE TABLE Projects (
            ProjectID INT IDENTITY(1,1) PRIMARY KEY,
            Name NVARCHAR(100) NOT NULL,
            Description NVARCHAR(MAX),
            StartDate DATE,
            EndDate DATE,
            Status NVARCHAR(20) DEFAULT 'Planning' CHECK (Status IN ('Planning', 'In Progress', 'On Hold', 'Completed', 'Cancelled')),
            Priority NVARCHAR(10) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
            Budget DECIMAL(15,2),
            ActualCost DECIMAL(15,2) DEFAULT 0,
            CompletionPercentage INT DEFAULT 0 CHECK (CompletionPercentage BETWEEN 0 AND 100),
            ClientName NVARCHAR(100),
            ManagerID INT,
            CreatedDate DATETIME DEFAULT GETDATE(),
            UpdatedDate DATETIME DEFAULT GETDATE(),
            FOREIGN KEY (ManagerID) REFERENCES Users(UserID)
        );

        -- Tasks table
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
        CREATE TABLE Tasks (
            TaskID INT IDENTITY(1,1) PRIMARY KEY,
            ProjectID INT NOT NULL,
            Title NVARCHAR(200) NOT NULL,
            Description NVARCHAR(MAX),
            AssignedToID INT,
            Status NVARCHAR(20) DEFAULT 'To Do' CHECK (Status IN ('To Do', 'In Progress', 'Review', 'Testing', 'Done')),
            Priority NVARCHAR(10) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
            CreatedDate DATETIME DEFAULT GETDATE(),
            DueDate DATETIME,
            StartDate DATETIME,
            EndDate DATETIME,
            EstimatedHours DECIMAL(5,2),
            ActualHours DECIMAL(5,2),
            CompletionPercentage INT DEFAULT 0 CHECK (CompletionPercentage BETWEEN 0 AND 100),
            CreatedByID INT,
            UpdatedDate DATETIME DEFAULT GETDATE(),
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
            FOREIGN KEY (AssignedToID) REFERENCES Users(UserID),
            FOREIGN KEY (CreatedByID) REFERENCES Users(UserID)
        );

        -- Create indexes for better performance
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Username')
        CREATE INDEX IX_Users_Username ON Users(Username);
        
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_Status')
        CREATE INDEX IX_Projects_Status ON Projects(Status);
        
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_Status')
        CREATE INDEX IX_Tasks_Status ON Tasks(Status);
        
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_DueDate')
        CREATE INDEX IX_Tasks_DueDate ON Tasks(DueDate);
        """

        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(schema_sql)
                conn.commit()
                logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise

    def _create_default_data(self):
        """สร้างข้อมูลเริ่มต้น"""
        default_data_sql = """
        -- Insert default admin user if not exists
        IF NOT EXISTS (SELECT * FROM Users WHERE Username = 'admin')
        INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department, MustChangePassword)
        VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG', 
                'admin@denso.com', 'System', 'Administrator', 'Admin', 'IT', 1);

        -- Insert sample project manager if not exists
        IF NOT EXISTS (SELECT * FROM Users WHERE Username = 'thammaphon.c')
        INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department)
        VALUES ('thammaphon.c', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG',
                'thammaphon.c@denso.com', 'Thammaphon', 'Chattasuwanna', 'Project Manager', 'Engineering');

        -- Insert sample projects if not exists
        IF NOT EXISTS (SELECT * FROM Projects WHERE Name = 'DENSO Engine Module V2')
        INSERT INTO Projects (Name, Description, Status, Priority, Budget, ManagerID, StartDate, EndDate, CompletionPercentage)
        VALUES ('DENSO Engine Module V2', 'Next generation engine control module development', 
                'In Progress', 'High', 5000000.00, 2, '2024-01-15', '2024-12-31', 75);

        IF NOT EXISTS (SELECT * FROM Projects WHERE Name = 'Quality Control System')
        INSERT INTO Projects (Name, Description, Status, Priority, Budget, ManagerID, StartDate, EndDate, CompletionPercentage)
        VALUES ('Quality Control System', 'Automated quality control and testing system',
                'Planning', 'Critical', 3200000.00, 2, '2024-03-01', '2024-11-30', 25);
        """

        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(default_data_sql)
                conn.commit()
                logger.info("Default data created successfully")
        except Exception as e:
            logger.error(f"Default data creation failed: {e}")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute SQL query และส่งคืนผลลัพธ์"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Get column names
                columns = (
                    [column[0] for column in cursor.description]
                    if cursor.description
                    else []
                )

                # Fetch all results
                results = cursor.fetchall()

                # Convert to list of dictionaries
                return [dict(zip(columns, row)) for row in results]

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """Execute non-query SQL (INSERT, UPDATE, DELETE)"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()
                return cursor.rowcount

        except Exception as e:
            logger.error(f"Non-query execution failed: {e}")
            raise

    def get_database_info(self) -> Dict[str, Any]:
        """ข้อมูลเกี่ยวกับฐานข้อมูล"""
        try:
            info_query = """
            SELECT 
                @@SERVERNAME as ServerName,
                DB_NAME() as DatabaseName,
                @@VERSION as Version,
                GETDATE() as CurrentTime
            """

            result = self.execute_query(info_query)
            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}

    def get_table_list(self) -> List[str]:
        """รายชื่อตารางทั้งหมด"""
        try:
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """

            results = self.execute_query(query)
            return [row["TABLE_NAME"] for row in results]

        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []

    def get_table_data(
        self, table_name: str, page: int = 1, page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """ดึงข้อมูลจากตาราง"""
        try:
            offset = (page - 1) * page_size
            query = f"""
            SELECT * FROM {table_name}
            ORDER BY 1
            OFFSET {offset} ROWS
            FETCH NEXT {page_size} ROWS ONLY
            """

            return self.execute_query(query)

        except Exception as e:
            logger.error(f"Failed to get table data: {e}")
            return []

    def get_table_record_count(self, table_name: str) -> int:
        """นับจำนวนเรคอร์ดในตาราง"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.execute_query(query)
            return result[0]["count"] if result else 0

        except Exception as e:
            logger.error(f"Failed to get record count: {e}")
            return 0

    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """โครงสร้างตาราง"""
        try:
            query = """
            SELECT 
                c.COLUMN_NAME as ColumnName,
                c.DATA_TYPE as DataType,
                c.IS_NULLABLE as IsNullable,
                c.COLUMN_DEFAULT as DefaultValue,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as IsPrimaryKey,
                CASE WHEN fk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as IsForeignKey
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN (
                SELECT ku.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                WHERE tc.TABLE_NAME = ? AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
            LEFT JOIN (
                SELECT ku.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                WHERE tc.TABLE_NAME = ? AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
            ) fk ON c.COLUMN_NAME = fk.COLUMN_NAME
            WHERE c.TABLE_NAME = ?
            ORDER BY c.ORDINAL_POSITION
            """

            return self.execute_query(query, (table_name, table_name, table_name))

        except Exception as e:
            logger.error(f"Failed to get table structure: {e}")
            return []

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """สถิติตาราง"""
        try:
            query = (
                """
            SELECT 
                COUNT(*) as record_count,
                (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?) as column_count,
                (SELECT COUNT(*) FROM sys.indexes WHERE object_id = OBJECT_ID(?)) as index_count
            FROM """
                + table_name
            )

            result = self.execute_query(query, (table_name, table_name))
            stats = result[0] if result else {}

            # ดึงข้อมูลขนาดตาราง
            size_query = """
            SELECT 
                CAST(SUM(a.total_pages) * 8 / 1024.0 AS DECIMAL(10,2)) as table_size_mb
            FROM sys.tables t
            INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id
            INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
            INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
            WHERE t.name = ?
            """

            size_result = self.execute_query(size_query, (table_name,))
            if size_result:
                stats.update(size_result[0])

            return stats

        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}

    def backup_database(self, backup_path: str = None) -> Dict[str, Any]:
        """สำรองฐานข้อมูล"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"C:\\Backups\\{self.config.database}_{timestamp}.bak"

        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    BACKUP DATABASE [{self.config.database}] 
                    TO DISK = '{backup_path}'
                    WITH FORMAT, COMPRESSION, CHECKSUM
                """
                )

                return {
                    "success": True,
                    "backup_path": backup_path,
                    "timestamp": datetime.now().isoformat(),
                    "database": self.config.database,
                }

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_connection_stats(self) -> Dict[str, Any]:
        """สถิติการเชื่อมต่อ"""
        return {
            "database_info": self.get_database_info(),
            "pool_stats": (
                self.pool.get_stats() if hasattr(self.pool, "get_stats") else {}
            ),
            "initialized": self._initialized,
        }

    def close(self):
        """ปิดการเชื่อมต่อ"""
        try:
            if hasattr(self.pool, "close_all"):
                self.pool.close_all()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")


# Global instance
_db_manager = None


def get_database_manager():
    """ได้ database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
