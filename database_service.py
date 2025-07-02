# database_service.py
"""
Enhanced Database Service for SSMS Connection
Handles all database operations with proper connection management
"""

import pyodbc
import streamlit as st
import logging
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
import time
import hashlib
import bcrypt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections with connection pooling"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection_string = self._build_connection_string()
        self._connection_cache = {}

    def _build_connection_string(self) -> str:
        """Build ODBC connection string from config"""
        return (
            f"Driver={{{self.config.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
            f"Server={self.config['server']},{self.config.get('port', 1433)};"
            f"Database={self.config['database']};"
            f"UID={self.config['username']};"
            f"PWD={self.config['password']};"
            f"Connection Timeout={self.config.get('connection_timeout', 30)};"
            f"Command Timeout={self.config.get('command_timeout', 60)};"
            "TrustServerCertificate=yes;"
            "Encrypt=yes;"
        )

    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup"""
        connection = None
        try:
            connection = pyodbc.connect(self.connection_string)
            connection.autocommit = False
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def execute_query(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute SELECT query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def execute_non_query(self, query: str, params: Tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Non-query execution failed: {str(e)}")
            raise


class DatabaseService:
    """Main database service class"""

    def __init__(self):
        self.connection_manager = None
        self._initialize_from_secrets()

    def _initialize_from_secrets(self):
        """Initialize database connection from Streamlit secrets"""
        try:
            db_config = {
                "server": st.secrets["database"]["server"],
                "database": st.secrets["database"]["database"],
                "username": st.secrets["database"]["username"],
                "password": st.secrets["database"]["password"],
                "driver": st.secrets["database"]["driver"],
                "connection_timeout": st.secrets["database"]["connection_options"][
                    "connection_timeout"
                ],
                "command_timeout": st.secrets["database"]["connection_options"][
                    "command_timeout"
                ],
            }
            self.connection_manager = DatabaseConnectionManager(db_config)
            logger.info("Database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {str(e)}")
            raise

    def setup_database(self) -> bool:
        """Setup database schema from SQL file"""
        try:
            # Read setup.sql file
            with open("setup.sql", "r", encoding="utf-8") as file:
                sql_content = file.read()

            # Split by GO statements
            sql_statements = [
                stmt.strip() for stmt in sql_content.split("GO") if stmt.strip()
            ]

            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                for statement in sql_statements:
                    if statement and not statement.startswith("--"):
                        cursor.execute(statement)
                conn.commit()

            logger.info("Database schema setup completed")
            return True
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            return False

    # User Management Methods
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user login"""
        query = """
        SELECT UserID, Username, PasswordHash, Email, FirstName, LastName, 
               Role, Department, IsActive, LastLoginDate
        FROM Users 
        WHERE Username = ? AND IsActive = 1
        """
        try:
            results = self.connection_manager.execute_query(query, (username,))
            if results:
                user = results[0]
                if bcrypt.checkpw(
                    password.encode("utf-8"), user["PasswordHash"].encode("utf-8")
                ):
                    # Update last login
                    self.update_user_last_login(user["UserID"])
                    return user
            return None
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    def create_user(self, user_data: Dict) -> bool:
        """Create new user"""
        query = """
        INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, 
                          Role, Department, Phone, Avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            password_hash = bcrypt.hashpw(
                user_data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            params = (
                user_data["username"],
                password_hash,
                user_data["email"],
                user_data["first_name"],
                user_data["last_name"],
                user_data.get("role", "User"),
                user_data.get("department", ""),
                user_data.get("phone", ""),
                user_data.get("avatar", ""),
            )

            self.connection_manager.execute_non_query(query, params)
            return True
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return False

    def update_user_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        query = "UPDATE Users SET LastLoginDate = GETDATE() WHERE UserID = ?"
        try:
            self.connection_manager.execute_non_query(query, (user_id,))
        except Exception as e:
            logger.error(f"Failed to update last login: {str(e)}")

    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        query = """
        SELECT UserID, Username, Email, FirstName, LastName, Role, 
               Department, IsActive, CreatedDate, LastLoginDate
        FROM Users 
        ORDER BY FirstName, LastName
        """
        try:
            return self.connection_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    # Project Management Methods
    def get_all_projects(self) -> List[Dict]:
        """Get all projects with creator info"""
        query = """
        SELECT p.*, u.FirstName + ' ' + u.LastName as CreatorName,
               (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID) as TaskCount,
               (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID AND Status = 'Done') as CompletedTasks
        FROM Projects p
        LEFT JOIN Users u ON p.CreatedBy = u.UserID
        ORDER BY p.CreatedDate DESC
        """
        try:
            return self.connection_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}")
            return []

    def create_project(self, project_data: Dict) -> Optional[int]:
        """Create new project"""
        query = """
        INSERT INTO Projects (ProjectName, Description, StartDate, EndDate, 
                             Status, Priority, Budget, ClientName, CreatedBy)
        OUTPUT INSERTED.ProjectID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        project_data["name"],
                        project_data.get("description", ""),
                        project_data.get("start_date"),
                        project_data.get("end_date"),
                        project_data.get("status", "Planning"),
                        project_data.get("priority", "Medium"),
                        project_data.get("budget", 0),
                        project_data.get("client_name", ""),
                        project_data["created_by"],
                    ),
                )
                result = cursor.fetchone()
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Project creation failed: {str(e)}")
            return None

    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """Get project by ID"""
        query = """
        SELECT p.*, u.FirstName + ' ' + u.LastName as CreatorName
        FROM Projects p
        LEFT JOIN Users u ON p.CreatedBy = u.UserID
        WHERE p.ProjectID = ?
        """
        try:
            results = self.connection_manager.execute_query(query, (project_id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get project: {str(e)}")
            return None

    # Task Management Methods
    def get_tasks_by_project(self, project_id: int) -> List[Dict]:
        """Get all tasks for a project"""
        query = """
        SELECT t.*, u.FirstName + ' ' + u.LastName as AssigneeName,
               c.FirstName + ' ' + c.LastName as CreatorName
        FROM Tasks t
        LEFT JOIN Users u ON t.AssigneeID = u.UserID
        LEFT JOIN Users c ON t.CreatedBy = c.UserID
        WHERE t.ProjectID = ?
        ORDER BY t.CreatedDate DESC
        """
        try:
            return self.connection_manager.execute_query(query, (project_id,))
        except Exception as e:
            logger.error(f"Failed to get tasks: {str(e)}")
            return []

    def create_task(self, task_data: Dict) -> Optional[int]:
        """Create new task"""
        query = """
        INSERT INTO Tasks (ProjectID, TaskName, Description, StartDate, EndDate, 
                          DueDate, AssigneeID, Status, Priority, EstimatedHours, CreatedBy)
        OUTPUT INSERTED.TaskID
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        task_data["project_id"],
                        task_data["name"],
                        task_data.get("description", ""),
                        task_data.get("start_date"),
                        task_data.get("end_date"),
                        task_data.get("due_date"),
                        task_data.get("assignee_id"),
                        task_data.get("status", "To Do"),
                        task_data.get("priority", "Medium"),
                        task_data.get("estimated_hours", 0),
                        task_data["created_by"],
                    ),
                )
                result = cursor.fetchone()
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Task creation failed: {str(e)}")
            return None

    def update_task_status(self, task_id: int, status: str) -> bool:
        """Update task status"""
        query = (
            "UPDATE Tasks SET Status = ?, LastModifiedDate = GETDATE() WHERE TaskID = ?"
        )
        try:
            self.connection_manager.execute_non_query(query, (status, task_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")
            return False

    # Dashboard Analytics Methods
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        try:
            stats = {}

            # Total projects
            result = self.connection_manager.execute_query(
                "SELECT COUNT(*) as count FROM Projects"
            )
            stats["total_projects"] = result[0]["count"] if result else 0

            # Active projects
            result = self.connection_manager.execute_query(
                "SELECT COUNT(*) as count FROM Projects WHERE Status IN ('Planning', 'In Progress')"
            )
            stats["active_projects"] = result[0]["count"] if result else 0

            # Total tasks
            result = self.connection_manager.execute_query(
                "SELECT COUNT(*) as count FROM Tasks"
            )
            stats["total_tasks"] = result[0]["count"] if result else 0

            # Completed tasks
            result = self.connection_manager.execute_query(
                "SELECT COUNT(*) as count FROM Tasks WHERE Status = 'Done'"
            )
            stats["completed_tasks"] = result[0]["count"] if result else 0

            # Total users
            result = self.connection_manager.execute_query(
                "SELECT COUNT(*) as count FROM Users WHERE IsActive = 1"
            )
            stats["total_users"] = result[0]["count"] if result else 0

            return stats
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {str(e)}")
            return {}

    def get_project_status_distribution(self) -> List[Dict]:
        """Get project status distribution for charts"""
        query = """
        SELECT Status, COUNT(*) as Count
        FROM Projects
        GROUP BY Status
        ORDER BY Count DESC
        """
        try:
            return self.connection_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get project status distribution: {str(e)}")
            return []

    def get_task_priority_distribution(self) -> List[Dict]:
        """Get task priority distribution"""
        query = """
        SELECT Priority, COUNT(*) as Count
        FROM Tasks
        GROUP BY Priority
        ORDER BY 
            CASE Priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
            END
        """
        try:
            return self.connection_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get task priority distribution: {str(e)}")
            return []

    # Notification Methods
    def create_notification(self, notification_data: Dict) -> bool:
        """Create notification"""
        query = """
        INSERT INTO Notifications (UserID, Type, Title, Message, Priority)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.connection_manager.execute_non_query(
                query,
                (
                    notification_data["user_id"],
                    notification_data.get("type", "info"),
                    notification_data["title"],
                    notification_data["message"],
                    notification_data.get("priority", "medium"),
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            return False

    def get_user_notifications(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user notifications"""
        query = """
        SELECT TOP (?) NotificationID, Type, Title, Message, IsRead, 
               CreatedDate, Priority
        FROM Notifications
        WHERE UserID = ?
        ORDER BY CreatedDate DESC
        """
        try:
            return self.connection_manager.execute_query(query, (limit, user_id))
        except Exception as e:
            logger.error(f"Failed to get notifications: {str(e)}")
            return []

    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        query = """
        UPDATE Notifications 
        SET IsRead = 1, ReadDate = GETDATE()
        WHERE NotificationID = ?
        """
        try:
            self.connection_manager.execute_non_query(query, (notification_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False


# Global database service instance
db_service = None


def get_database_service() -> DatabaseService:
    """Get or create database service instance"""
    global db_service
    if db_service is None:
        db_service = DatabaseService()
    return db_service
