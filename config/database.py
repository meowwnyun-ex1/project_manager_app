"""
config/database.py
Database configuration and connection management
"""

import pyodbc
import streamlit as st
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
import threading
from contextlib import contextmanager

# Set up logging for this module
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration class, loading settings from Streamlit secrets."""

    server: str
    database: str
    username: str
    password: str
    driver: str = "ODBC Driver 17 for SQL Server"
    connection_timeout: int = 30  # Timeout for establishing a connection
    command_timeout: int = 60  # Timeout for executing a command/query

    @classmethod
    def from_secrets(cls) -> "DatabaseConfig":
        """
        Creates a DatabaseConfig instance from Streamlit secrets.toml.
        Raises ValueError if essential database configuration is missing.
        """
        try:
            db_config = st.secrets["database"]
            # Extract main database credentials
            server = db_config["server"]
            database = db_config["database"]
            username = db_config["username"]
            password = db_config["password"]
            driver = db_config.get("driver", "ODBC Driver 17 for SQL Server")

            # Extract connection options with defaults
            connection_options = db_config.get("connection_options", {})
            connection_timeout = connection_options.get("connection_timeout", 30)
            command_timeout = connection_options.get("command_timeout", 60)

            return cls(
                server=server,
                database=database,
                username=username,
                password=password,
                driver=driver,
                connection_timeout=connection_timeout,
                command_timeout=command_timeout,
            )
        except KeyError as e:
            logger.error(f"Missing database configuration in secrets.toml: {e}")
            raise ValueError(
                f"Required database setting '{e.args[0]}' not found in secrets.toml."
            )
        except Exception as e:
            logger.error(f"Failed to load database config from secrets: {str(e)}")
            raise ValueError("An error occurred while loading database configuration.")

    def get_connection_string(self) -> str:
        """
        Generates the ODBC connection string based on the configuration.
        Includes TrustServerCertificate=yes for development/local environments.
        """
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"  # IMPORTANT: Use 'no' and properly validate certificates in production!
            f"Connection Timeout={self.connection_timeout};"
        )


class ConnectionPool:
    """
    A simple connection pool for managing pyodbc database connections.
    This helps reuse connections and manage resource efficiently in a Streamlit app.
    """

    def __init__(self, config: DatabaseConfig, max_connections: int = 5):
        self.config = config
        self.max_connections = max_connections
        self.connections: List[pyodbc.Connection] = []
        self.lock = threading.Lock()
        self.connection_count = 0  # Tracks total active connections (in-use + in-pool)

    def get_connection(self) -> pyodbc.Connection:
        """
        Retrieves a database connection from the pool. If no connections are available
        and the maximum limit hasn't been reached, a new connection is created.
        Sets the command timeout on the connection before returning it.
        """
        with self.lock:
            if self.connections:
                conn = self.connections.pop()
                # Set command timeout directly on the connection object
                conn.timeout = self.config.command_timeout
                return conn

            if self.connection_count < self.max_connections:
                try:
                    conn = pyodbc.connect(
                        self.config.get_connection_string(),
                        timeout=self.config.connection_timeout,  # This is the connection timeout
                    )
                    # Set command timeout on the newly created connection
                    conn.timeout = self.config.command_timeout
                    self.connection_count += 1
                    logger.debug(
                        f"Created new database connection. Total: {self.connection_count}"
                    )
                    return conn
                except Exception as e:
                    logger.error(f"Failed to create new database connection: {str(e)}")
                    raise Exception(f"Failed to establish database connection: {e}")
            else:
                logger.warning("Connection pool exhausted. No available connections.")
                raise Exception(
                    "Database connection pool exhausted. Please try again later."
                )

    def return_connection(self, conn: pyodbc.Connection):
        """
        Returns a connection to the pool for reuse. If the pool is full,
        the connection is closed.
        """
        with self.lock:
            if len(self.connections) < self.max_connections:
                self.connections.append(conn)
                logger.debug("Connection returned to pool.")
            else:
                try:
                    conn.close()
                    self.connection_count -= 1
                    logger.debug("Connection closed (pool full).")
                except pyodbc.Error as e:
                    logger.warning(
                        f"Error closing connection returned to full pool: {e}"
                    )
                except Exception as e:
                    logger.error(f"Unexpected error closing connection: {e}")

    def close_all(self):
        """Closes all connections currently held in the pool."""
        with self.lock:
            for conn in self.connections:
                try:
                    conn.close()
                except pyodbc.Error as e:
                    logger.warning(f"Error closing a pooled connection: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error closing a pooled connection: {e}")
            self.connections.clear()
            self.connection_count = 0
            logger.info("All pooled connections closed.")


class DatabaseManager:
    """
    Manages database operations, including connection pooling,
    initialization, and various query execution methods.
    """

    def __init__(self):
        """
        Initializes the database manager, loads configuration,
        and performs initial database setup if required.
        """
        self.config: Optional[DatabaseConfig] = None
        self.pool: Optional[ConnectionPool] = None
        self._initialized = False

        try:
            self.config = DatabaseConfig.from_secrets()
            self.pool = ConnectionPool(self.config)
            self._init_database()
            logger.info("DatabaseManager initialized successfully.")
        except Exception as e:
            logger.critical(f"FATAL: DatabaseManager initialization failed: {e}")
            # Reraise to prevent the application from starting without a working DB
            raise

    def _init_database(self):
        """
        Performs initial database setup: checks connection, ensures DB exists,
        creates tables from setup.sql, and inserts default data.
        """
        if self._initialized:
            logger.debug("Database already initialized, skipping.")
            return

        logger.info("Starting database initialization process...")
        try:
            self.test_connection()  # Test overall connectivity
            self._ensure_database_exists()
            self._create_tables()
            self._insert_default_data()
            self._initialized = True
            logger.info("Database initialization process completed.")
        except Exception as e:
            logger.error(f"Database initialization failed at a critical step: {e}")
            raise  # Re-raise to stop further execution if setup fails

    def test_connection(self) -> bool:
        """
        Tests the database connection by executing a simple query.
        Returns True if successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                logger.info("Database connection test successful.")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

    @contextmanager
    def get_connection(self):
        """
        Context manager to acquire and automatically release a database connection
        from the connection pool. Handles rollback on exceptions.
        """
        conn = None
        try:
            conn = self.pool.get_connection()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()  # Rollback on error if connection is active
                    logger.warning("Transaction rolled back due to error.")
                except pyodbc.Error as rb_e:
                    logger.error(f"Error during transaction rollback: {rb_e}")
            logger.error(f"Error acquiring or using database connection: {e}")
            raise  # Re-raise the original exception
        finally:
            if conn:
                self.pool.return_connection(conn)

    def _ensure_database_exists(self):
        """
        Connects to the master database to check if ProjectManagerDB exists.
        If not, it attempts to create it.
        """
        try:
            # Create a separate config for connecting to the master database
            master_config = DatabaseConfig(
                server=self.config.server,
                database="master",  # Connect to master to create/check DB
                username=self.config.username,
                password=self.config.password,
                driver=self.config.driver,
                connection_timeout=self.config.connection_timeout,
                # command_timeout is not critical for master connection
            )

            master_conn_str = master_config.get_connection_string()

            # Connect to master with a direct connection (not from pool)
            with pyodbc.connect(
                master_conn_str, timeout=master_config.connection_timeout
            ) as conn:
                cursor = conn.cursor()

                # Check if the target database exists
                cursor.execute(
                    "SELECT name FROM master.sys.databases WHERE name = ?",
                    (self.config.database,),
                )
                if not cursor.fetchone():
                    # Create the database if it doesn't exist
                    logger.info(
                        f"Database '{self.config.database}' not found. Attempting to create..."
                    )
                    try:
                        cursor.execute(
                            f"CREATE DATABASE [{self.config.database}] COLLATE SQL_Latin1_General_CP1_CI_AS"
                        )
                        conn.commit()  # Commit the CREATE DATABASE command
                        logger.info(
                            f"Database '{self.config.database}' created successfully."
                        )
                    except pyodbc.Error as e:
                        # Handle specific errors for CREATE DATABASE (e.g., permissions)
                        logger.critical(
                            f"Failed to create database '{self.config.database}': {e}"
                        )
                        raise Exception(
                            f"Database creation failed. Please check permissions and server status: {e}"
                        )
                else:
                    logger.info(f"Database '{self.config.database}' already exists.")

        except Exception as e:
            logger.error(
                f"Could not ensure database exists or connect to master: {str(e)}"
            )
            raise  # Re-raise to halt initialization if master connection or DB creation fails

    def _create_tables(self):
        """
        Reads and executes the 'setup.sql' script to create all necessary tables,
        indexes, and views. Handles 'GO' statements for batch execution.
        """
        logger.info("Creating database tables and objects from setup.sql...")
        try:
            with open("setup.sql", "r", encoding="utf-8") as f:
                sql_script = f.read()

            with self.get_connection() as conn:
                # Set autocommit to True for this specific setup process.
                # This ensures each batch (separated by GO) is committed independently,
                # which helps with variable scope issues and simplifies error recovery for setup.
                conn.autocommit = True
                cursor = conn.cursor()

                # Split the script by 'GO' to execute batches
                # Ensure splitting handles 'GO' on its own line and case insensitivity
                batches = [
                    batch.strip()
                    for batch in sql_script.split("\nGO\n")
                    if batch.strip()
                ]

                for i, batch in enumerate(batches):
                    if batch:
                        try:
                            cursor.execute(batch)
                            logger.debug(f"Successfully executed SQL batch {i+1}.")
                        except pyodbc.Error as e:
                            sqlstate = e.args[0]
                            # Log specific SQLSTATE for variable re-declaration as warning
                            if sqlstate == "42000":
                                logger.warning(
                                    f"SQL batch execution warning (Batch {i+1}, SQLSTATE {sqlstate}): "
                                    f"Variable re-declaration or similar issue. Details: {str(e)} "
                                    f"Batch start: {batch[:100]}..."
                                )
                            else:
                                # For other errors, log as critical and re-raise
                                logger.critical(
                                    f"SQL batch execution FAILED (Batch {i+1}, SQLSTATE {sqlstate}): "
                                    f"Details: {str(e)} - Batch start: {batch[:200]}..."
                                )
                                raise  # Re-raise critical SQL errors to stop setup
                        except Exception as e:
                            logger.critical(
                                f"Unexpected error during SQL batch execution (Batch {i+1}): "
                                f"Details: {str(e)} - Batch start: {batch[:200]}..."
                            )
                            raise  # Re-raise other unexpected errors

            logger.info(
                "Database tables and objects created successfully from setup.sql."
            )

        except FileNotFoundError:
            logger.warning(
                "setup.sql file not found. Attempting to create tables manually (limited schema)."
            )
            # Fallback to manual creation if setup.sql is missing.
            # Note: This manual creation is a *simplified* version compared to setup.sql.
            self._create_tables_manually()
        except Exception as e:
            logger.error(
                f"Failed to create tables from setup.sql: {str(e)}. Attempting manual creation as fallback."
            )
            # Fallback to manual creation if setup.sql execution fails for other reasons.
            self._create_tables_manually()

    def _create_tables_manually(self):
        """
        Fallback method to create a minimal set of core tables if setup.sql fails or is not found.
        This provides a basic operational database but lacks many features from setup.sql.
        """
        logger.warning("Executing manual table creation (limited schema).")
        tables_sql = [
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
                Department NVARCHAR(100),
                IsActive BIT DEFAULT 1,
                CreatedDate DATETIME DEFAULT GETDATE(),
                LastLoginDate DATETIME
            )
            """,
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
                CreatedBy INT NOT NULL,
                CreatedDate DATETIME DEFAULT GETDATE(),
                FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
            CREATE TABLE Tasks (
                TaskID INT IDENTITY(1,1) PRIMARY KEY,
                ProjectID INT NOT NULL,
                TaskName NVARCHAR(200) NOT NULL,
                Description NTEXT,
                AssigneeID INT,
                Status NVARCHAR(50) DEFAULT 'To Do',
                Priority NVARCHAR(50) DEFAULT 'Medium',
                DueDate DATE,
                CreatedBy INT NOT NULL,
                CreatedDate DATETIME DEFAULT GETDATE(),
                FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                FOREIGN KEY (AssigneeID) REFERENCES Users(UserID),
                FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
            )
            """,
        ]

        try:
            with self.get_connection() as conn:
                conn.autocommit = True  # Ensure each statement commits
                cursor = conn.cursor()

                for table_sql in tables_sql:
                    try:
                        cursor.execute(table_sql)
                        logger.debug(
                            f"Manually created table batch: {table_sql[:50]}..."
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to manually create table: {str(e)} - SQL: {table_sql[:100]}..."
                        )
                        raise  # Re-raise to indicate manual creation failed too

            logger.info("Minimal tables created manually.")

        except Exception as e:
            logger.critical(f"FATAL: Manual table creation failed: {str(e)}")
            raise

    def _insert_default_data(self):
        """
        Inserts default data such as the admin user and initial settings
        if they do not already exist in the database.
        """
        logger.info("Inserting default data...")
        try:
            # Check if admin user exists before inserting
            # Note: execute_query handles the cursor.timeout correctly now
            admin_exists_result = self.execute_query(
                "SELECT COUNT(*) as count FROM Users WHERE Username = 'admin'"
            )

            # Check for empty result or count == 0
            admin_count = admin_exists_result[0]["count"] if admin_exists_result else 0

            if admin_count == 0:
                # Dynamically import bcrypt to avoid import errors if not installed
                try:
                    import bcrypt
                except ImportError:
                    logger.error(
                        "bcrypt library not found. Cannot hash password for admin user. Please install bcrypt (`pip install bcrypt`)."
                    )
                    # Fallback to a placeholder or raise a critical error
                    raise ImportError(
                        "bcrypt is required for password hashing. Please install it."
                    )

                # Hash the default password
                password_hash = bcrypt.hashpw(
                    "admin123".encode("utf-8"),
                    bcrypt.gensalt(rounds=st.secrets["security"]["bcrypt_rounds"]),
                ).decode(
                    "utf-8"
                )  # Use bcrypt rounds from secrets

                # Insert default admin user
                self.execute_non_query(
                    """
                    INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department, IsActive)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "admin",
                        password_hash,
                        "admin@denso.com",
                        "System",
                        "Administrator",
                        "Admin",
                        "IT",
                        1,
                    ),
                )
                logger.info(
                    "Default admin user created (username: admin, password: admin123)."
                )
            else:
                logger.info("Admin user 'admin' already exists, skipping insertion.")

            logger.info("Default data insertion process completed.")

        except Exception as e:
            logger.warning(f"Could not insert default data: {str(e)}")

    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query and returns results as a list of dictionaries.
        Logs slow queries.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # cursor.timeout is no longer set here, it's set on the connection itself

                start_time = time.time()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Get column names from cursor description
                columns = (
                    [column[0] for column in cursor.description]
                    if cursor.description
                    else []
                )

                # Fetch all results and convert to list of dictionaries
                results = []
                for row in cursor.fetchall():
                    row_dict = {columns[i]: value for i, value in enumerate(row)}
                    results.append(row_dict)

                execution_time = time.time() - start_time
                if execution_time > 1.0:
                    logger.warning(
                        f"Slow query detected: {execution_time:.2f}s - Query: {query[:100]}..."
                    )

                return results

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)} - Query: {query[:100]}...")
            raise  # Re-raise the exception after logging

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        Executes INSERT, UPDATE, DELETE queries.
        Returns True on success, False on failure.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # cursor.timeout is no longer set here

                start_time = time.time()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                conn.commit()  # Commit changes for non-query operations

                execution_time = time.time() - start_time
                if execution_time > 1.0:
                    logger.warning(
                        f"Slow non-query detected: {execution_time:.2f}s - Query: {query[:100]}..."
                    )

                return True

        except Exception as e:
            logger.error(
                f"Non-query execution failed: {str(e)} - Query: {query[:100]}..."
            )
            # Do not return False silently; re-raise to allow proper error handling upstream
            raise

    def execute_scalar(self, query: str, params: Optional[tuple] = None) -> Any:
        """
        Executes a query and returns a single scalar value (e.g., COUNT(*)).
        Returns None if no rows or value.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # cursor.timeout is no longer set here

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                row = cursor.fetchone()
                return row[0] if row else None

        except Exception as e:
            logger.error(
                f"Scalar query execution failed: {str(e)} - Query: {query[:100]}..."
            )
            raise

    def execute_insert_with_id(
        self, query: str, params: Optional[tuple] = None
    ) -> Optional[int]:
        """
        Executes an INSERT query and attempts to return the newly generated ID.
        Assumes primary key is named '{TableName}ID'.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # cursor.timeout is no longer set here

                # Modify query to return inserted ID for SQL Server (using OUTPUT)
                # This logic is an attempt to inject OUTPUT, but it's more robust
                # to ensure the original query already has it or use SCOPE_IDENTITY()
                # in a separate query immediately after.
                # For this setup, we'll assume the original query might not have OUTPUT,
                # so we try to modify or suggest adding a subsequent SELECT SCOPE_IDENTITY().

                modified_query = query
                # Simple check for common INSERT INTO (col1,...) VALUES (...)
                if (
                    "OUTPUT INSERTED." not in query.upper()
                    and "VALUES" in query.upper()
                ):
                    # Attempt to find table name and inject OUTPUT clause
                    import re

                    match = re.search(
                        r"INSERT INTO\s+\[?(\w+)\]?\s*\(", query, re.IGNORECASE
                    )
                    if match:
                        table_name = match.group(1)
                        # Assume PK is TableNameID (common convention)
                        pk_name = f"{table_name}ID"
                        # Insert OUTPUT clause right after the INTO TableName
                        modified_query = query.replace(
                            f"INSERT INTO {table_name}",
                            f"INSERT INTO {table_name} OUTPUT INSERTED.{pk_name}",
                            1,
                        )
                        logger.debug(
                            f"Modified INSERT query to include OUTPUT clause: {modified_query[:100]}..."
                        )
                    else:
                        logger.warning(
                            "Could not automatically add OUTPUT clause to INSERT query. Ensure query includes 'OUTPUT INSERTED.ID' or fetch SCOPE_IDENTITY() separately."
                        )
                        pass  # proceed with original query

                if params:
                    cursor.execute(modified_query, params)
                else:
                    cursor.execute(modified_query)

                # Try to fetch the ID. If OUTPUT was added/present, it's fetchone().
                row = cursor.fetchone()
                inserted_id = row[0] if row else None

                conn.commit()
                return inserted_id

        except Exception as e:
            logger.error(f"Insert with ID failed: {str(e)} - Query: {query[:100]}...")
            raise

    def bulk_insert(self, query: str, data: List[tuple]) -> bool:
        """
        Executes a bulk insert operation using `executemany`.
        Returns True on success, False on failure.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # cursor.timeout is no longer set here

                cursor.executemany(query, data)
                conn.commit()

                logger.info(f"Bulk insert completed: {len(data)} records.")
                return True

        except Exception as e:
            logger.error(f"Bulk insert failed: {str(e)}")
            raise

    def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """
        Executes multiple database operations within a single transaction.
        All operations succeed or all are rolled back.
        `operations` is a list of dicts, e.g., `{'query': '...', 'params': (...) }`
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # cursor.timeout is no longer set here

                # Disable autocommit for manual transaction management
                conn.autocommit = False

                try:
                    for i, operation in enumerate(operations):
                        query = operation["query"]
                        params = operation.get("params")

                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)
                        logger.debug(
                            f"Executed transaction operation {i+1}: {query[:50]}..."
                        )

                    conn.commit()  # Commit all operations if no errors occurred
                    logger.info(
                        f"Transaction completed successfully: {len(operations)} operations."
                    )
                    return True

                except Exception as e:
                    conn.rollback()  # Rollback on any error
                    logger.error(
                        f"Transaction failed, rolled back: {str(e)} - Operation: {query[:100]}..."
                    )
                    raise  # Re-raise the exception
                finally:
                    conn.autocommit = True  # Restore autocommit to default for the pool

        except Exception as e:
            logger.error(f"Transaction execution failed: {str(e)}")
            raise

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Retrieves schema information for a given table."""
        query = """
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query, (table_name,))

    def get_database_stats(self) -> Dict[str, Any]:
        """Retrieves general statistics about the database."""
        stats = {}
        tables = [
            "Users",
            "Projects",
            "Tasks",
            "ProjectMembers",
            "TimeTracking",
            "Comments",
            "Notifications",
            "FileAttachments",
            "AuditLog",
            "Settings",
        ]  # Ensure all tables are included

        try:
            for table in tables:
                try:
                    count = self.execute_scalar(
                        f"SELECT COUNT(*) FROM [{table}]"
                    )  # Use brackets for safety
                    stats[f"{table.lower()}_count"] = count or 0
                except Exception as e:
                    logger.warning(f"Could not get count for table {table}: {e}")
                    stats[f"{table.lower()}_count"] = 0

            # Database size
            try:
                size_query = """
                SELECT
                    SUM(size * 8.0 / 1024) as SizeMB
                FROM sys.master_files
                WHERE database_id = DB_ID(?)
                """
                size_mb = self.execute_scalar(size_query, (self.config.database,))
                stats["database_size_mb"] = round(size_mb or 0, 2)
            except Exception as e:
                logger.warning(f"Could not get database size: {e}")
                stats["database_size_mb"] = 0

            # Active connections (to this specific database)
            try:
                conn_query = """
                SELECT COUNT(*)
                FROM sys.dm_exec_sessions
                WHERE database_id = DB_ID(?) AND original_db_name = ?
                """
                active_connections = self.execute_scalar(
                    conn_query, (self.config.database, self.config.database)
                )
                stats["active_connections"] = active_connections or 0
            except Exception as e:
                logger.warning(f"Could not get active connections: {e}")
                stats["active_connections"] = 0

        except Exception as e:
            logger.error(f"Failed to get overall database stats: {str(e)}")

        return stats

    def backup_database(self, backup_path: str) -> bool:
        """
        Creates a full database backup to the specified path.
        Requires appropriate file system permissions for the SQL Server service account.
        """
        try:
            # Ensure the path uses SQL Server's path format (usually Windows paths)
            # And SQL Server service account needs write access to this path.
            # >>> แก้ไขตรงนี้เพื่อแก้ SyntaxError: f-string expression part cannot include a backslash
            sql_server_backup_path = backup_path.replace("/", "\\")

            backup_query = f"""
            BACKUP DATABASE [{self.config.database}]
            TO DISK = '{sql_server_backup_path}' -- Ensure path is Windows-style for SQL Server
            WITH FORMAT, COMPRESSION, STATS = 10;
            """
            logger.info(f"Attempting database backup to: {backup_path}")
            result = self.execute_non_query(backup_query)
            if result:
                logger.info(f"Database backup created successfully: {backup_path}")
            return result

        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise  # Re-raise for clearer error indication

    def optimize_database(self) -> bool:
        """
        Optimizes database performance by updating statistics and reorganizing indexes.
        """
        logger.info("Starting database optimization process...")
        try:
            optimization_queries = [
                # UPDATE STATISTICS can be run without specific table names for all tables,
                # or specify tables for more granular control.
                "EXEC sp_updatestats;",  # Updates statistics for all tables in current DB
                # DBCC UPDATEUSAGE corrects page and row counts.
                "DBCC UPDATEUSAGE(0);",
                # Reorganize/Rebuild indexes. Reorganize is less intrusive than rebuild.
                # For critical performance, you might run ALTER INDEX ALL ... REBUILD WITH (ONLINE = ON)
                # but it requires Enterprise Edition for ONLINE=ON.
                "ALTER INDEX ALL ON Users REORGANIZE;",
                "ALTER INDEX ALL ON Projects REORGANIZE;",
                "ALTER INDEX ALL ON Tasks REORGANIZE;",
                "ALTER INDEX ALL ON ProjectMembers REORGANIZE;",
                "ALTER INDEX ALL ON TimeTracking REORGANIZE;",
                "ALTER INDEX ALL ON Comments REORGANIZE;",
                "ALTER INDEX ALL ON Notifications REORGANIZE;",
                "ALTER INDEX ALL ON FileAttachments REORGANIZE;",
                "ALTER INDEX ALL ON AuditLog REORGANIZE;",
                "ALTER INDEX ALL ON Settings REORGANIZE;",
            ]

            with self.get_connection() as conn:
                conn.autocommit = True  # Ensure each optimization command commits
                cursor = conn.cursor()

                for i, query in enumerate(optimization_queries):
                    try:
                        cursor.execute(query)
                        logger.debug(
                            f"Executed optimization query {i+1}: {query[:50]}..."
                        )
                    except Exception as e:
                        logger.warning(f"Optimization query failed: {query} - {str(e)}")
                        # Do not raise here, as one failed optimization step should not
                        # necessarily stop the entire process. Log and continue.

            logger.info("Database optimization completed.")
            return True

        except Exception as e:
            logger.error(f"Overall database optimization process failed: {str(e)}")
            return False

    def close(self):
        """Closes the database manager and all underlying connections in the pool."""
        if self.pool:
            try:
                self.pool.close_all()
            except Exception as e:
                logger.error(f"Error closing DatabaseManager: {str(e)}")

    def __del__(self):
        """Destructor to ensure connections are closed when the object is garbage collected."""
        self.close()


# Global database manager instance (singleton pattern for Streamlit apps)
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """
    Returns the global singleton instance of DatabaseManager.
    This ensures only one connection pool and database manager is active.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
