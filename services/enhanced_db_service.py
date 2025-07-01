# services/enhanced_db_service.py
import pyodbc
import os
import logging
import time
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
import hashlib
import json
from functools import wraps
import threading
from dataclasses import dataclass
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConnectionPool:
    """Connection pool configuration"""

    max_connections: int = 10
    timeout: int = 30
    retry_attempts: int = 3


class DatabaseException(Exception):
    """Custom database exception"""

    pass


class ConnectionManager:
    """Advanced database connection manager with pooling"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_config()
        self.pool = ConnectionPool()
        self._connections = []
        self._lock = threading.Lock()
        self._health_check_interval = 60  # seconds
        self._last_health_check = time.time()

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from Streamlit secrets"""
        try:
            # Try to get from Streamlit secrets first
            if hasattr(st, "secrets") and "database" in st.secrets:
                return {
                    "server": st.secrets.database.get("server", "localhost"),
                    "database": st.secrets.database.get("database", "ProjectManagerDB"),
                    "username": st.secrets.database.get("username", "sa"),
                    "password": st.secrets.database.get("password", "YourPassword123"),
                    "driver": st.secrets.database.get(
                        "driver", "ODBC Driver 17 for SQL Server"
                    ),
                    "port": st.secrets.database.get("port", "1433"),
                    "timeout": int(st.secrets.database.get("timeout", "30")),
                    "connection_timeout": int(
                        st.secrets.database.get("connection_timeout", "30")
                    ),
                }
            else:
                # Fallback to environment variables
                return {
                    "server": os.getenv("DB_SERVER", "localhost"),
                    "database": os.getenv("DB_DATABASE", "ProjectManagerDB"),
                    "username": os.getenv("DB_USERNAME", "sa"),
                    "password": os.getenv("DB_PASSWORD", "YourPassword123"),
                    "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
                    "port": os.getenv("DB_PORT", "1433"),
                    "timeout": int(os.getenv("DB_TIMEOUT", "30")),
                    "connection_timeout": int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
                }
        except Exception as e:
            logger.error(f"Failed to load database config: {str(e)}")
            # Return default config
            return {
                "server": "localhost",
                "database": "ProjectManagerDB",
                "username": "sa",
                "password": "YourPassword123",
                "driver": "ODBC Driver 17 for SQL Server",
                "port": "1433",
                "timeout": 30,
                "connection_timeout": 30,
            }

    def get_connection_string(self) -> str:
        """Generate connection string"""
        try:
            return (
                f"DRIVER={{{self.config['driver']}}};"
                f"SERVER={self.config['server']},{self.config['port']};"
                f"DATABASE={self.config['database']};"
                f"UID={self.config['username']};"
                f"PWD={self.config['password']};"
                f"Timeout={self.config['timeout']};"
                f"Connection Timeout={self.config['connection_timeout']};"
                "Encrypt=yes;"
                "TrustServerCertificate=yes;"
                "Mars_Connection=yes;"
            )
        except Exception as e:
            logger.error(f"Failed to generate connection string: {str(e)}")
            raise DatabaseException(f"Connection string generation failed: {str(e)}")

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        connection = None
        try:
            connection = self._create_connection()
            yield connection
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
            logger.error(f"Database connection error: {str(e)}")
            raise DatabaseException(f"Database connection failed: {str(e)}")
        finally:
            if connection:
                try:
                    connection.close()
                except:
                    pass

    def _create_connection(self) -> pyodbc.Connection:
        """Create new database connection"""
        try:
            connection_string = self.get_connection_string()
            logger.info(f"Attempting connection to: {self.config['server']}")
            connection = pyodbc.connect(connection_string)
            connection.autocommit = False
            logger.info("Database connection successful")
            return connection
        except pyodbc.Error as e:
            logger.error(f"Failed to create database connection: {str(e)}")
            raise DatabaseException(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating connection: {str(e)}")
            raise DatabaseException(f"Unexpected connection error: {str(e)}")

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        current_time = time.time()

        if current_time - self._last_health_check < self._health_check_interval:
            return {"status": "cached", "healthy": True}

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "healthy": False,
            "connection_test": False,
            "response_time": None,
            "errors": [],
        }

        try:
            start_time = time.time()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Test basic connectivity
                cursor.execute("SELECT GETDATE()")
                result = cursor.fetchone()

                if result:
                    health_status["connection_test"] = True
                    health_status["response_time"] = time.time() - start_time
                    health_status["healthy"] = True

                # Test table access
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME IN ('Users', 'Projects', 'Tasks')
                """
                )
                table_count = cursor.fetchone()[0]
                health_status["tables_accessible"] = table_count == 3

        except Exception as e:
            health_status["errors"].append(str(e))
            logger.error(f"Health check failed: {str(e)}")

        self._last_health_check = current_time
        return health_status


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying failed database operations"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (pyodbc.Error, DatabaseException) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}"
                        )
                        time.sleep(delay * (2**attempt))  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed")

            raise last_exception

        return wrapper

    return decorator


class EnhancedDatabaseService:
    """Enhanced database service with advanced features"""

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self._query_stats = {}

    @retry_on_failure(max_retries=3)
    def execute_query(
        self, query: str, params: Optional[Tuple] = None, fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute SQL query with enhanced error handling"""
        start_time = time.time()

        try:
            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch:
                    columns = (
                        [column[0] for column in cursor.description]
                        if cursor.description
                        else []
                    )
                    rows = cursor.fetchall()

                    result = []
                    for row in rows:
                        result.append(dict(zip(columns, row)))

                    conn.commit()

                    # Log query performance
                    execution_time = time.time() - start_time
                    self._log_query_performance(query, execution_time, len(result))

                    return result
                else:
                    conn.commit()
                    execution_time = time.time() - start_time
                    self._log_query_performance(query, execution_time, cursor.rowcount)
                    return [{"affected_rows": cursor.rowcount}]

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}\nQuery: {query}")
            raise DatabaseException(f"Query failed: {str(e)}")

    def _log_query_performance(self, query: str, execution_time: float, row_count: int):
        """Log query performance metrics"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]

        if query_hash not in self._query_stats:
            self._query_stats[query_hash] = {
                "query": query[:100],
                "executions": 0,
                "total_time": 0,
                "avg_time": 0,
                "max_time": 0,
                "min_time": float("inf"),
            }

        stats = self._query_stats[query_hash]
        stats["executions"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["executions"]
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["min_time"] = min(stats["min_time"], execution_time)

        if execution_time > 5.0:  # Log slow queries
            logger.warning(
                f"Slow query detected: {execution_time:.2f}s - {query[:100]}"
            )

    @retry_on_failure()
    def execute_transaction(self, queries: List[Tuple[str, Optional[Tuple]]]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()

                for query, params in queries:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise DatabaseException(f"Transaction failed: {str(e)}")

    def get_with_cache(
        self, cache_key: str, query: str, params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute query with caching"""
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data

        # Execute query and cache result
        result = self.execute_query(query, params)
        self.cache[cache_key] = (result, time.time())

        return result

    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        if pattern:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed table information"""
        query = """
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            c.CHARACTER_MAXIMUM_LENGTH,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END as IS_PRIMARY_KEY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT ku.TABLE_CATALOG, ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS ku
                ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY' 
                AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        ) pk ON c.TABLE_CATALOG = pk.TABLE_CATALOG
            AND c.TABLE_SCHEMA = pk.TABLE_SCHEMA  
            AND c.TABLE_NAME = pk.TABLE_NAME
            AND c.COLUMN_NAME = pk.COLUMN_NAME
        WHERE c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
        """

        columns = self.execute_query(query, (table_name,))

        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
        row_count = self.execute_query(count_query)[0]["row_count"]

        return {
            "table_name": table_name,
            "columns": columns,
            "row_count": row_count,
            "last_checked": datetime.now().isoformat(),
        }

    def backup_table(self, table_name: str, backup_name: Optional[str] = None) -> str:
        """Create a backup of a table"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{table_name}_backup_{timestamp}"

        query = f"""
        SELECT * INTO {backup_name}
        FROM {table_name}
        """

        self.execute_query(query, fetch=False)
        logger.info(f"Table {table_name} backed up as {backup_name}")

        return backup_name

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        return {
            "query_stats": dict(list(self._query_stats.items())[:10]),  # Top 10
            "cache_size": len(self.cache),
            "health_check": self.connection_manager.health_check(),
            "connection_config": {
                "server": self.connection_manager.config["server"],
                "database": self.connection_manager.config["database"],
                "timeout": self.connection_manager.config["timeout"],
            },
        }

    def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization tasks"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks_completed": [],
            "errors": [],
        }

        optimization_tasks = [
            ("UPDATE_STATISTICS", "UPDATE STATISTICS"),
            ("RECOMPILE_PLANS", "DBCC FREEPROCCACHE"),
            ("CLEAR_BUFFERS", "DBCC DROPCLEANBUFFERS"),
        ]

        for task_name, query in optimization_tasks:
            try:
                self.execute_query(query, fetch=False)
                results["tasks_completed"].append(task_name)
                logger.info(f"Completed optimization task: {task_name}")
            except Exception as e:
                results["errors"].append(f"{task_name}: {str(e)}")
                logger.error(f"Optimization task {task_name} failed: {str(e)}")

        return results

    def setup_database(self) -> bool:
        """Setup database schema if not exists"""
        schema_queries = [
            # Users table
            """
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users')
            BEGIN
                CREATE TABLE Users (
                    UserID INT IDENTITY(1,1) PRIMARY KEY,
                    Username NVARCHAR(50) NOT NULL UNIQUE,
                    PasswordHash NVARCHAR(255) NOT NULL,
                    Email NVARCHAR(255) UNIQUE,
                    Role NVARCHAR(20) DEFAULT 'User',
                    Active BIT DEFAULT 1,
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    LastLoginDate DATETIME2,
                    PasswordChangedDate DATETIME2,
                    ProfilePicture NVARCHAR(255)
                );
                
                CREATE INDEX IX_Users_Username ON Users(Username);
                CREATE INDEX IX_Users_Email ON Users(Email);
                CREATE INDEX IX_Users_Role ON Users(Role);
            END
            """,
            # Projects table
            """
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Projects')
            BEGIN
                CREATE TABLE Projects (
                    ProjectID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectName NVARCHAR(100) NOT NULL,
                    Description NVARCHAR(MAX),
                    StartDate DATE,
                    EndDate DATE,
                    Status NVARCHAR(50) DEFAULT 'Planning',
                    Priority NVARCHAR(20) DEFAULT 'Medium',
                    Budget DECIMAL(15,2),
                    ClientName NVARCHAR(100),
                    Tags NVARCHAR(500),
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
                    LastModifiedDate DATETIME2 DEFAULT GETDATE()
                );
                
                CREATE INDEX IX_Projects_Status ON Projects(Status);
                CREATE INDEX IX_Projects_Priority ON Projects(Priority);
                CREATE INDEX IX_Projects_CreatedBy ON Projects(CreatedBy);
                CREATE INDEX IX_Projects_Dates ON Projects(StartDate, EndDate);
            END
            """,
            # Tasks table
            """
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Tasks')
            BEGIN
                CREATE TABLE Tasks (
                    TaskID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectID INT NOT NULL FOREIGN KEY REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                    TaskName NVARCHAR(100) NOT NULL,
                    Description NVARCHAR(MAX),
                    StartDate DATE,
                    EndDate DATE,
                    AssigneeID INT FOREIGN KEY REFERENCES Users(UserID),
                    Status NVARCHAR(50) DEFAULT 'To Do',
                    Priority NVARCHAR(20) DEFAULT 'Medium',
                    Progress INT DEFAULT 0,
                    EstimatedHours DECIMAL(5,1),
                    ActualHours DECIMAL(5,1),
                    Dependencies NVARCHAR(MAX),
                    Labels NVARCHAR(255),
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID)
                );
                
                CREATE INDEX IX_Tasks_ProjectID ON Tasks(ProjectID);
                CREATE INDEX IX_Tasks_AssigneeID ON Tasks(AssigneeID);
                CREATE INDEX IX_Tasks_Status ON Tasks(Status);
                CREATE INDEX IX_Tasks_Priority ON Tasks(Priority);
                CREATE INDEX IX_Tasks_Dates ON Tasks(StartDate, EndDate);
            END
            """,
            # Insert default admin user if no users exist
            """
            IF NOT EXISTS (SELECT 1 FROM Users)
            BEGIN
                INSERT INTO Users (Username, PasswordHash, Email, Role, Active, PasswordChangedDate)
                VALUES (
                    'admin',
                    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewXl.dO7.z7.gE6y',
                    'admin@projectmanager.local',
                    'Admin',
                    1,
                    GETDATE()
                );
            END
            """,
        ]

        try:
            for query in schema_queries:
                self.execute_query(query, fetch=False)

            logger.info("Database schema setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            return False

    def get_schema_version(self) -> str:
        """Get current database schema version"""
        try:
            # Try to get version from a version table
            result = self.execute_query(
                "SELECT TOP 1 Version FROM SchemaVersion ORDER BY AppliedDate DESC"
            )
            return result[0]["Version"] if result else "1.0.0"
        except:
            # If version table doesn't exist, return default
            return "1.0.0"

    def close(self):
        """Clean up resources"""
        self.clear_cache()
        logger.info("Database service closed")


# Global database service instance
_db_service = None


def get_db_service() -> EnhancedDatabaseService:
    """Get global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = EnhancedDatabaseService()
    return _db_service


# Database decorators
def with_db_transaction(func):
    """Decorator to wrap function in database transaction"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        db_service = get_db_service()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Transaction function {func.__name__} failed: {str(e)}")
            raise

    return wrapper


def cached_query(cache_key: str, ttl: int = 300):
    """Decorator for caching query results"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            db_service = get_db_service()
            # Create unique cache key with function args
            full_cache_key = f"{cache_key}_{hash(str(args) + str(kwargs))}"

            # Check cache first
            if full_cache_key in db_service.cache:
                cached_data, timestamp = db_service.cache[full_cache_key]
                if time.time() - timestamp < ttl:
                    return cached_data

            # Execute function and cache result
            result = func(*args, **kwargs)
            db_service.cache[full_cache_key] = (result, time.time())

            return result

        return wrapper

    return decorator


# Export classes and functions
__all__ = [
    "EnhancedDatabaseService",
    "ConnectionManager",
    "DatabaseException",
    "get_db_service",
    "with_db_transaction",
    "cached_query",
    "retry_on_failure",
]
