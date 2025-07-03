#!/usr/bin/env python3
"""
config/database.py
Enterprise Database Management System สำหรับ DENSO Project Manager Pro
"""

import pyodbc
import streamlit as st
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib
from functools import wraps
import queue
import weakref
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """Enhanced database connection configuration"""

    server: str
    database: str
    username: str = ""
    password: str = ""
    driver: str = "ODBC Driver 17 for SQL Server"
    connection_timeout: int = 30
    command_timeout: int = 60
    encrypt: bool = True
    trust_server_certificate: bool = True
    mars_connection: bool = True  # Multiple Active Result Sets

    def get_connection_string(self) -> str:
        """Generate optimized connection string"""
        if self.username and self.password:
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
        else:
            conn_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"Trusted_Connection=yes;"
            )

        # Performance optimizations
        conn_str += (
            f"Connection Timeout={self.connection_timeout};"
            f"Command Timeout={self.command_timeout};"
            f"TrustServerCertificate={'yes' if self.trust_server_certificate else 'no'};"
            f"Encrypt={'yes' if self.encrypt else 'no'};"
            f"MARS_Connection={'yes' if self.mars_connection else 'no'};"
            "MultipleActiveResultSets=true;"
            "Pooling=true;"
            "Max Pool Size=100;"
            "Min Pool Size=10;"
        )

        return conn_str


class ConnectionPool:
    """High-performance database connection pool"""

    def __init__(self, config: ConnectionConfig, pool_size: int = 10):
        self.config = config
        self.pool_size = pool_size
        self.pool = queue.Queue(maxsize=pool_size)
        self.active_connections = 0
        self.total_connections = 0
        self.stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "connections_failed": 0,
            "active_queries": 0,
        }
        self._lock = threading.RLock()
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool with pre-created connections"""
        for _ in range(min(3, self.pool_size)):  # Pre-create 3 connections
            try:
                conn = self._create_connection()
                self.pool.put(conn)
                self.total_connections += 1
            except Exception as e:
                logger.error(f"Failed to pre-create connection: {e}")

    def _create_connection(self):
        """Create new database connection with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = pyodbc.connect(
                    self.config.get_connection_string(),
                    timeout=self.config.connection_timeout,
                )
                conn.timeout = self.config.command_timeout
                self.stats["connections_created"] += 1
                return conn

            except Exception as e:
                if attempt == max_retries - 1:
                    self.stats["connections_failed"] += 1
                    raise
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff

    @contextmanager
    def get_connection(self):
        """Get connection from pool with automatic return"""
        conn = None
        try:
            # Try to get existing connection
            try:
                conn = self.pool.get_nowait()
                self.stats["connections_reused"] += 1
            except queue.Empty:
                # Create new if pool is empty and under limit
                if self.total_connections < self.pool_size:
                    conn = self._create_connection()
                    with self._lock:
                        self.total_connections += 1
                else:
                    # Wait for available connection
                    conn = self.pool.get(timeout=10)

            # Test connection
            if not self._test_connection(conn):
                conn.close()
                conn = self._create_connection()

            with self._lock:
                self.active_connections += 1

            yield conn

        except Exception as e:
            logger.error(f"Connection pool error: {e}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
            raise
        finally:
            if conn:
                try:
                    # Return connection to pool
                    self.pool.put_nowait(conn)
                except queue.Full:
                    # Pool is full, close connection
                    conn.close()
                    with self._lock:
                        self.total_connections -= 1

                with self._lock:
                    self.active_connections = max(0, self.active_connections - 1)

    def _test_connection(self, conn) -> bool:
        """Test if connection is still valid"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            "pool_size": self.pool_size,
            "active_connections": self.active_connections,
            "total_connections": self.total_connections,
            "available_connections": self.pool.qsize(),
            "stats": self.stats.copy(),
        }

    def close_all(self):
        """Close all connections in pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                pass
        self.total_connections = 0
        self.active_connections = 0


class QueryCache:
    """Intelligent query result caching"""

    def __init__(self, max_size: int = 500, default_ttl: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._lock = threading.RLock()

    def _generate_key(self, query: str, params: Tuple = None) -> str:
        """Generate cache key from query and parameters"""
        content = query.strip().lower()
        if params:
            content += str(params)
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, query: str, params: Tuple = None) -> Optional[List[Dict]]:
        """Get cached query result"""
        key = self._generate_key(query, params)

        with self._lock:
            if key in self.cache:
                entry = self.cache[key]

                # Check TTL
                if time.time() - entry["timestamp"] < entry["ttl"]:
                    entry["access_count"] += 1
                    self.access_times[key] = time.time()
                    self.stats["hits"] += 1
                    return entry["data"]
                else:
                    # Expired
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]

            self.stats["misses"] += 1
            return None

    def set(self, query: str, data: List[Dict], params: Tuple = None, ttl: int = None):
        """Cache query result"""
        key = self._generate_key(query, params)
        ttl = ttl or self.default_ttl

        with self._lock:
            # Evict if necessary
            if len(self.cache) >= self.max_size:
                self._evict_lru()

            self.cache[key] = {
                "data": data,
                "timestamp": time.time(),
                "ttl": ttl,
                "access_count": 1,
                "query_hash": key[:8],
            }
            self.access_times[key] = time.time()

    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return

        lru_key = min(self.access_times.keys(), key=self.access_times.get)
        del self.cache[lru_key]
        del self.access_times[lru_key]
        self.stats["evictions"] += 1

    def clear(self):
        """Clear all cached entries"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0

        return {
            "hit_rate": hit_rate,
            "size": len(self.cache),
            "max_size": self.max_size,
            **self.stats,
        }


class DatabaseManager:
    """Enterprise database manager with advanced features"""

    def __init__(self, environment: str = "auto"):
        self.environment = environment
        self.config = self._load_config()
        self.pool = ConnectionPool(self.config, pool_size=15)
        self.query_cache = QueryCache(max_size=1000, default_ttl=600)
        self.executor = ThreadPoolExecutor(
            max_workers=5, thread_name_prefix="db-worker"
        )
        self._initialized = False
        self._schema_version = None

        # Performance monitoring
        self.query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "avg_query_time": 0.0,
        }

        self._init_database()
        logger.info(f"DatabaseManager initialized for {environment} environment")

    def _load_config(self) -> ConnectionConfig:
        """Load database configuration from secrets"""
        try:
            if self.environment == "auto":
                self.environment = self._detect_environment()

            # Load from Streamlit secrets
            db_config = st.secrets.get(f"database_{self.environment}", {})

            if not db_config:
                # Fallback to production config
                db_config = st.secrets.get("database_production", {})
                if not db_config:
                    raise ValueError("No database configuration found")

            return ConnectionConfig(
                server=db_config["server"],
                database=db_config["database"],
                username=db_config.get("username", ""),
                password=db_config.get("password", ""),
                driver=db_config.get("driver", "ODBC Driver 17 for SQL Server"),
                connection_timeout=db_config.get("connection_timeout", 30),
                command_timeout=db_config.get("command_timeout", 60),
            )

        except Exception as e:
            logger.error(f"Failed to load database config: {e}")
            raise

    def _detect_environment(self) -> str:
        """Auto-detect environment based on configuration"""
        try:
            # Check if local database is available
            if "database_local" in st.secrets:
                local_config = st.secrets["database_local"]
                if "(localdb)" in local_config.get("server", "").lower():
                    return "local"

            # Default to production
            return "production"

        except:
            return "production"

    def _init_database(self):
        """Initialize database with comprehensive setup"""
        if self._initialized:
            return

        try:
            # Test connectivity
            if not self.test_connection():
                raise Exception("Database connection test failed")

            # Ensure database exists
            self._ensure_database_exists()

            # Create/update schema
            self._setup_schema()

            # Insert default data
            self._setup_default_data()

            # Update performance statistics
            self._update_query_stats()

            self._initialized = True
            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Test database connectivity with detailed diagnostics"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION, GETDATE(), @@SERVERNAME")
                result = cursor.fetchone()

                if result:
                    logger.info(f"Database connection successful - Server: {result[2]}")
                    return True

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

        return False

    def _ensure_database_exists(self):
        """Ensure target database exists"""
        try:
            # Connect to master database first
            master_config = ConnectionConfig(
                server=self.config.server,
                database="master",
                username=self.config.username,
                password=self.config.password,
                driver=self.config.driver,
            )

            conn = pyodbc.connect(master_config.get_connection_string())
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(
                "SELECT database_id FROM sys.databases WHERE name = ?",
                (self.config.database,),
            )

            if not cursor.fetchone():
                # Create database with optimized settings
                cursor.execute(
                    f"""
                    CREATE DATABASE [{self.config.database}]
                    COLLATE SQL_Latin1_General_CP1_CI_AS
                """
                )
                logger.info(f"Database {self.config.database} created")

            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Database creation failed: {e}")
            raise

    def _setup_schema(self):
        """Setup comprehensive database schema"""
        schema_sql = """
        -- Users table with enhanced security
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
        CREATE TABLE Users (
            UserID int IDENTITY(1,1) PRIMARY KEY,
            Username nvarchar(50) UNIQUE NOT NULL,
            PasswordHash nvarchar(255) NOT NULL,
            Email nvarchar(100) UNIQUE NOT NULL,
            FirstName nvarchar(50),
            LastName nvarchar(50),
            Role nvarchar(20) NOT NULL DEFAULT 'User',
            Department nvarchar(50),
            IsActive bit NOT NULL DEFAULT 1,
            CreatedDate datetime2 NOT NULL DEFAULT GETDATE(),
            LastLogin datetime2,
            FailedLoginAttempts int NOT NULL DEFAULT 0,
            LastFailedLogin datetime2,
            IsLocked bit NOT NULL DEFAULT 0,
            CONSTRAINT CK_Users_Role CHECK (Role IN ('Admin', 'Project Manager', 'Team Lead', 'Developer', 'User'))
        );

        -- Projects table with advanced tracking
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
        CREATE TABLE Projects (
            ProjectID int IDENTITY(1,1) PRIMARY KEY,
            Name nvarchar(100) NOT NULL,
            Description nvarchar(MAX),
            StartDate date,
            EndDate date,
            Status nvarchar(20) NOT NULL DEFAULT 'Planning',
            Priority nvarchar(10) NOT NULL DEFAULT 'Medium',
            Budget decimal(15,2),
            ActualCost decimal(15,2) DEFAULT 0,
            ClientName nvarchar(100),
            ManagerID int,
            CreatedDate datetime2 NOT NULL DEFAULT GETDATE(),
            ModifiedDate datetime2 NOT NULL DEFAULT GETDATE(),
            CompletionPercentage int DEFAULT 0,
            EstimatedHours int DEFAULT 0,
            ActualHours int DEFAULT 0,
            FOREIGN KEY (ManagerID) REFERENCES Users(UserID),
            CONSTRAINT CK_Projects_Status CHECK (Status IN ('Planning', 'In Progress', 'On Hold', 'Completed', 'Cancelled')),
            CONSTRAINT CK_Projects_Priority CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
            CONSTRAINT CK_Projects_Completion CHECK (CompletionPercentage BETWEEN 0 AND 100)
        );

        -- Tasks table with detailed tracking
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
        CREATE TABLE Tasks (
            TaskID int IDENTITY(1,1) PRIMARY KEY,
            ProjectID int NOT NULL,
            Title nvarchar(200) NOT NULL,
            Description nvarchar(MAX),
            AssigneeID int,
            CreatedByID int,
            Status nvarchar(20) NOT NULL DEFAULT 'To Do',
            Priority nvarchar(10) NOT NULL DEFAULT 'Medium',
            StartDate date,
            DueDate date,
            CompletedDate date,
            EstimatedHours decimal(5,2),
            ActualHours decimal(5,2),
            CompletionPercentage int DEFAULT 0,
            CreatedDate datetime2 NOT NULL DEFAULT GETDATE(),
            ModifiedDate datetime2 NOT NULL DEFAULT GETDATE(),
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
            FOREIGN KEY (AssigneeID) REFERENCES Users(UserID),
            FOREIGN KEY (CreatedByID) REFERENCES Users(UserID),
            CONSTRAINT CK_Tasks_Status CHECK (Status IN ('To Do', 'In Progress', 'Review', 'Done', 'Blocked')),
            CONSTRAINT CK_Tasks_Priority CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
            CONSTRAINT CK_Tasks_Completion CHECK (CompletionPercentage BETWEEN 0 AND 100)
        );

        -- Project Members table for team assignments
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ProjectMembers' AND xtype='U')
        CREATE TABLE ProjectMembers (
            ProjectID int NOT NULL,
            UserID int NOT NULL,
            Role nvarchar(50) NOT NULL DEFAULT 'Member',
            AssignedDate datetime2 NOT NULL DEFAULT GETDATE(),
            PRIMARY KEY (ProjectID, UserID),
            FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
            FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
        );

        -- Task Comments for collaboration
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TaskComments' AND xtype='U')
        CREATE TABLE TaskComments (
            CommentID int IDENTITY(1,1) PRIMARY KEY,
            TaskID int NOT NULL,
            UserID int NOT NULL,
            Comment nvarchar(MAX) NOT NULL,
            CreatedDate datetime2 NOT NULL DEFAULT GETDATE(),
            FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );

        -- Audit Log for security and compliance
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AuditLog' AND xtype='U')
        CREATE TABLE AuditLog (
            LogID int IDENTITY(1,1) PRIMARY KEY,
            UserID int,
            Action nvarchar(100) NOT NULL,
            TableName nvarchar(50),
            RecordID int,
            OldValues nvarchar(MAX),
            NewValues nvarchar(MAX),
            IPAddress nvarchar(45),
            UserAgent nvarchar(500),
            CreatedDate datetime2 NOT NULL DEFAULT GETDATE(),
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );

        -- Performance indexes for enterprise scale
        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_ProjectID_Status')
        CREATE INDEX IX_Tasks_ProjectID_Status ON Tasks(ProjectID, Status);

        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_AssigneeID_Status')
        CREATE INDEX IX_Tasks_AssigneeID_Status ON Tasks(AssigneeID, Status);

        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_Status_Priority')
        CREATE INDEX IX_Projects_Status_Priority ON Projects(Status, Priority);

        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Username_IsActive')
        CREATE INDEX IX_Users_Username_IsActive ON Users(Username, IsActive);

        IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AuditLog_UserID_CreatedDate')
        CREATE INDEX IX_AuditLog_UserID_CreatedDate ON AuditLog(UserID, CreatedDate);
        """

        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                # Execute schema in batches
                for statement in schema_sql.split(";\n\n"):
                    if statement.strip():
                        cursor.execute(statement)
                conn.commit()

            logger.info("Database schema setup completed")

        except Exception as e:
            logger.error(f"Schema setup failed: {e}")
            raise

    def _setup_default_data(self):
        """Insert default administrative data"""
        default_data_sql = """
        -- Insert default admin user if not exists
        IF NOT EXISTS (SELECT * FROM Users WHERE Username = 'admin')
        INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department)
        VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG', 
                'admin@denso.com', 'System', 'Administrator', 'Admin', 'IT');

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

            logger.info("Default data setup completed")

        except Exception as e:
            logger.error(f"Default data setup failed: {e}")

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        with self.pool.get_connection() as conn:
            yield conn

    def execute_query(
        self,
        query: str,
        params: Tuple = None,
        use_cache: bool = True,
        cache_ttl: int = 300,
    ) -> List[Dict[str, Any]]:
        """Execute query with caching and performance monitoring"""
        start_time = time.time()

        try:
            # Check cache first for SELECT queries
            if use_cache and query.strip().upper().startswith("SELECT"):
                cached_result = self.query_cache.get(query, params)
                if cached_result is not None:
                    return cached_result

            # Execute query
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Fetch results for SELECT queries
                if query.strip().upper().startswith("SELECT"):
                    columns = [column[0] for column in cursor.description]
                    results = []

                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))

                    # Cache results
                    if (
                        use_cache and len(results) < 10000
                    ):  # Don't cache very large results
                        self.query_cache.set(query, results, params, cache_ttl)

                    return results
                else:
                    # For non-SELECT queries, return affected rows
                    conn.commit()
                    return [{"affected_rows": cursor.rowcount}]

        except Exception as e:
            self.query_stats["failed_queries"] += 1
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            # Update performance statistics
            execution_time = time.time() - start_time
            self._update_query_performance(execution_time)

    def execute_batch(
        self, queries: List[Tuple[str, Tuple]], use_transaction: bool = True
    ) -> List[Any]:
        """Execute multiple queries in batch with optional transaction"""
        results = []

        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                if use_transaction:
                    cursor.execute("BEGIN TRANSACTION")

                for query, params in queries:
                    try:
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)

                        if query.strip().upper().startswith("SELECT"):
                            columns = [column[0] for column in cursor.description]
                            rows = cursor.fetchall()
                            results.append([dict(zip(columns, row)) for row in rows])
                        else:
                            results.append(cursor.rowcount)

                    except Exception as e:
                        if use_transaction:
                            cursor.execute("ROLLBACK TRANSACTION")
                        raise

                if use_transaction:
                    cursor.execute("COMMIT TRANSACTION")
                else:
                    conn.commit()

                return results

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise

    def _update_query_performance(self, execution_time: float):
        """Update query performance statistics"""
        self.query_stats["total_queries"] += 1

        if execution_time > 2.0:  # Slow query threshold
            self.query_stats["slow_queries"] += 1

        # Update running average
        total = self.query_stats["total_queries"]
        current_avg = self.query_stats["avg_query_time"]
        self.query_stats["avg_query_time"] = (
            (current_avg * (total - 1)) + execution_time
        ) / total

    def _update_query_stats(self):
        """Update overall query statistics"""
        try:
            # This could be expanded to include more detailed DB statistics
            pass
        except Exception as e:
            logger.error(f"Failed to update query stats: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive database performance statistics"""
        return {
            "connection_pool": self.pool.get_stats(),
            "query_cache": self.query_cache.get_stats(),
            "query_performance": self.query_stats.copy(),
            "environment": self.environment,
            "database": self.config.database,
            "server": self.config.server,
        }

    def optimize_database(self) -> Dict[str, Any]:
        """Perform database optimization tasks"""
        optimization_results = {
            "tasks_completed": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()

                # Update statistics
                cursor.execute("UPDATE STATISTICS")
                optimization_results["tasks_completed"].append("Statistics updated")

                # Rebuild fragmented indexes
                cursor.execute(
                    """
                    SELECT OBJECT_NAME(OBJECT_ID) AS TableName, 
                           name AS IndexName,
                           avg_fragmentation_in_percent
                    FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
                    INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
                    WHERE avg_fragmentation_in_percent > 30 AND ips.index_id > 0
                """
                )

                fragmented_indexes = cursor.fetchall()
                for table_name, index_name, fragmentation in fragmented_indexes:
                    try:
                        cursor.execute(
                            f"ALTER INDEX [{index_name}] ON [{table_name}] REBUILD"
                        )
                        optimization_results["tasks_completed"].append(
                            f"Rebuilt index {index_name} on {table_name} (was {fragmentation:.1f}% fragmented)"
                        )
                    except Exception as e:
                        optimization_results["warnings"].append(
                            f"Failed to rebuild {index_name}: {e}"
                        )

                conn.commit()

                # Clear query cache to ensure fresh data
                self.query_cache.clear()
                optimization_results["tasks_completed"].append("Query cache cleared")

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            optimization_results["warnings"].append(f"Optimization error: {e}")

        return optimization_results

    def backup_database(self, backup_path: Optional[str] = None) -> Dict[str, Any]:
        """Create database backup"""
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

    def close(self):
        """Clean shutdown of database manager"""
        try:
            self.executor.shutdown(wait=True, timeout=10)
            self.pool.close_all()
            logger.info("Database manager closed successfully")
        except Exception as e:
            logger.error(f"Error closing database manager: {e}")


# Global database manager instance
_database_manager = None


def get_database_manager(environment: str = "auto") -> DatabaseManager:
    """Get global database manager instance"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager(environment)
    return _database_manager


# Query helper decorators
def with_db_connection(func):
    """Decorator to provide database connection to function"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        db_manager = get_database_manager()
        return func(db_manager, *args, **kwargs)

    return wrapper


def cached_query(ttl: int = 300):
    """Decorator for caching query results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db_manager = get_database_manager()
            # Implementation would depend on specific function signature
            return func(*args, **kwargs)

        return wrapper

    return decorator
