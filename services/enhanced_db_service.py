"""
🚀 Project Manager Pro v3.0 - Enhanced Database Service
Comprehensive database operations with SQL Server integration
"""

import streamlit as st
import pyodbc
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
from contextlib import contextmanager

from config.enhanced_config import EnhancedConfig

class EnhancedDBService:
    """Enhanced database service with comprehensive SQL Server integration"""
    
    def __init__(self):
        self.config = EnhancedConfig()
        self.connection_string = self.config.get_database_connection_string()
        self.logger = logging.getLogger(__name__)
        self._connection_pool = []
        
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = pyodbc.connect(
                self.connection_string,
                timeout=self.config.get('database.connection_timeout', 30)
            )
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_schema(self) -> bool:
        """Initialize database schema with all required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create Users table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
                CREATE TABLE Users (
                    UserID INT IDENTITY(1,1) PRIMARY KEY,
                    Username NVARCHAR(50) NOT NULL UNIQUE,
                    PasswordHash NVARCHAR(255) NOT NULL,
                    Email NVARCHAR(255) UNIQUE,
                    FirstName NVARCHAR(50),
                    LastName NVARCHAR(50),
                    Role NVARCHAR(20) DEFAULT 'User',
                    Active BIT DEFAULT 1,
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    LastLoginDate DATETIME2,
                    PasswordChangedDate DATETIME2,
                    ProfilePicture NVARCHAR(255),
                    Phone NVARCHAR(20),
                    Department NVARCHAR(50),
                    JobTitle NVARCHAR(100),
                    FailedLoginAttempts INT DEFAULT 0,
                    LockedUntil DATETIME2,
                    LastModifiedDate DATETIME2 DEFAULT GETDATE()
                )
                """)
                
                # Create Projects table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
                CREATE TABLE Projects (
                    ProjectID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectName NVARCHAR(100) NOT NULL,
                    Description NVARCHAR(MAX),
                    StartDate DATE,
                    EndDate DATE,
                    Status NVARCHAR(50) DEFAULT 'Planning',
                    Priority NVARCHAR(20) DEFAULT 'Medium',
                    Budget DECIMAL(15,2),
                    ActualCost DECIMAL(15,2) DEFAULT 0,
                    ClientName NVARCHAR(100),
                    ClientEmail NVARCHAR(255),
                    Tags NVARCHAR(500),
                    Progress INT DEFAULT 0,
                    EstimatedHours DECIMAL(8,2),
                    ActualHours DECIMAL(8,2) DEFAULT 0,
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
                    LastModifiedDate DATETIME2 DEFAULT GETDATE(),
                    LastModifiedBy INT FOREIGN KEY REFERENCES Users(UserID),
                    CompletedDate DATETIME2,
                    IsTemplate BIT DEFAULT 0,
                    TemplateID INT,
                    Color NVARCHAR(7) DEFAULT '#667eea'
                )
                """)
                
                # Create Tasks table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
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
                    ActualHours DECIMAL(5,1) DEFAULT 0,
                    Dependencies NVARCHAR(MAX),
                    Labels NVARCHAR(255),
                    ParentTaskID INT FOREIGN KEY REFERENCES Tasks(TaskID),
                    Order_Index INT DEFAULT 0,
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    CreatedBy INT FOREIGN KEY REFERENCES Users(UserID),
                    LastModifiedDate DATETIME2 DEFAULT GETDATE(),
                    LastModifiedBy INT FOREIGN KEY REFERENCES Users(UserID),
                    CompletedDate DATETIME2,
                    DueDate DATE,
                    IsRecurring BIT DEFAULT 0,
                    RecurrencePattern NVARCHAR(100)
                )
                """)
                
                # Create Project Members table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ProjectMembers' AND xtype='U')
                CREATE TABLE ProjectMembers (
                    ProjectMemberID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectID INT NOT NULL FOREIGN KEY REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                    UserID INT NOT NULL FOREIGN KEY REFERENCES Users(UserID) ON DELETE CASCADE,
                    Role NVARCHAR(50) DEFAULT 'Member',
                    JoinedDate DATETIME2 DEFAULT GETDATE(),
                    IsActive BIT DEFAULT 1,
                    UNIQUE(ProjectID, UserID)
                )
                """)
                
                # Create Comments table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Comments' AND xtype='U')
                CREATE TABLE Comments (
                    CommentID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectID INT FOREIGN KEY REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                    TaskID INT FOREIGN KEY REFERENCES Tasks(TaskID) ON DELETE CASCADE,
                    UserID INT NOT NULL FOREIGN KEY REFERENCES Users(UserID),
                    Comment NVARCHAR(MAX) NOT NULL,
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    LastModifiedDate DATETIME2,
                    IsDeleted BIT DEFAULT 0
                )
                """)
                
                # Create Time Logs table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TimeLogs' AND xtype='U')
                CREATE TABLE TimeLogs (
                    TimeLogID INT IDENTITY(1,1) PRIMARY KEY,
                    TaskID INT NOT NULL FOREIGN KEY REFERENCES Tasks(TaskID) ON DELETE CASCADE,
                    UserID INT NOT NULL FOREIGN KEY REFERENCES Users(UserID),
                    StartTime DATETIME2 NOT NULL,
                    EndTime DATETIME2,
                    Duration DECIMAL(5,2),
                    Description NVARCHAR(500),
                    LogDate DATE DEFAULT CAST(GETDATE() AS DATE),
                    CreatedDate DATETIME2 DEFAULT GETDATE(),
                    IsBillable BIT DEFAULT 1
                )
                """)
                
                # Create Attachments table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Attachments' AND xtype='U')
                CREATE TABLE Attachments (
                    AttachmentID INT IDENTITY(1,1) PRIMARY KEY,
                    ProjectID INT FOREIGN KEY REFERENCES Projects(ProjectID) ON DELETE CASCADE,
                    TaskID INT FOREIGN KEY REFERENCES Tasks(TaskID) ON DELETE CASCADE,
                    FileName NVARCHAR(255) NOT NULL,
                    FilePath NVARCHAR(500) NOT NULL,
                    FileSize BIGINT,
                    FileType NVARCHAR(50),
                    UploadedBy INT NOT NULL FOREIGN KEY REFERENCES Users(UserID),
                    UploadedDate DATETIME2 DEFAULT GETDATE(),
                    IsDeleted BIT DEFAULT 0
                )
                """)
                
                # Create Activity Logs table
                cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ActivityLogs' AND xtype='U')
                CREATE TABLE ActivityLogs (
                    ActivityLogID INT IDENTITY(1,1) PRIMARY KEY,
                    UserID INT NOT NULL FOREIGN KEY REFERENCES Users(UserID),
                    ProjectID INT FOREIGN KEY REFERENCES Projects(ProjectID),
                    TaskID INT FOREIGN KEY REFERENCES Tasks(TaskID),
                    Action NVARCHAR(100) NOT NULL,
                    Details NVARCHAR(MAX),
                    IPAddress NVARCHAR(45),
                    UserAgent NVARCHAR(500),
                    CreatedDate DATETIME2 DEFAULT GETDATE()
                )
                """)
                
                # Create performance indexes
                self._create_indexes(cursor)
                
                # Insert default admin user if not exists
                self._create_default_admin(cursor)
                
                conn.commit()
                self.logger.info("Database schema initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Schema initialization failed: {str(e)}")
            return False
    
    def _create_indexes(self, cursor) -> None:
        """Create performance indexes"""
        indexes = [
            "CREATE INDEX IX_Projects_Status ON Projects(Status)",
            "CREATE INDEX IX_Projects_CreatedBy ON Projects(CreatedBy)",
            "CREATE INDEX IX_Tasks_ProjectID ON Tasks(ProjectID)",
            "CREATE INDEX IX_Tasks_AssigneeID ON Tasks(AssigneeID)",
            "CREATE INDEX IX_Tasks_Status ON Tasks(Status)",
            "CREATE INDEX IX_TimeLogs_TaskID ON TimeLogs(TaskID)",
            "CREATE INDEX IX_TimeLogs_UserID ON TimeLogs(UserID)",
            "CREATE INDEX IX_ActivityLogs_UserID ON ActivityLogs(UserID)",
            "CREATE INDEX IX_ActivityLogs_ProjectID ON ActivityLogs(ProjectID)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception:
                # Index may already exist
                pass
    
    def _create_default_admin(self, cursor) -> None:
        """Create default admin user"""
        try:
            # Check if admin user exists
            cursor.execute("SELECT COUNT(*) FROM Users WHERE Username = 'admin'")
            if cursor.fetchone()[0] == 0:
                # Create default admin user
                import bcrypt
                password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute("""
                INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Active)
                VALUES ('admin', ?, 'admin@projectmanagerpro.com', 'System', 'Administrator', 'Admin', 1)
                """, password_hash)
                
                self.logger.info("Default admin user created: admin/admin123")
        except Exception as e:
            self.logger.error(f"Failed to create default admin user: {str(e)}")
    
    # User Management Methods
    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Hash password
                import bcrypt
                password_hash = bcrypt.hashpw(
                    user_data['password'].encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                cursor.execute("""
                INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Phone, Department, JobTitle)
                OUTPUT INSERTED.UserID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data['username'],
                    password_hash,
                    user_data.get('email'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('role', 'User'),
                    user_data.get('phone'),
                    user_data.get('department'),
                    user_data.get('job_title')
                ))
                
                user_id = cursor.fetchone()[0]
                conn.commit()
                
                # Log activity
                self.log_activity(user_id, None, None, 'User Created', f"User {user_data['username']} created")
                
                return user_id
                
        except Exception as e:
            self.logger.error(f"User creation failed: {str(e)}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT UserID, Username, PasswordHash, Email, FirstName, LastName, Role, Active, FailedLoginAttempts, LockedUntil
                FROM Users 
                WHERE Username = ? AND Active = 1
                """, username)
                
                user = cursor.fetchone()
                if not user:
                    return None
                
                # Check if account is locked
                if user.LockedUntil and user.LockedUntil > datetime.now():
                    return None
                
                # Verify password
                import bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), user.PasswordHash.encode('utf-8')):
                    # Successful login - reset failed attempts and update last login
                    cursor.execute("""
                    UPDATE Users 
                    SET LastLoginDate = GETDATE(), FailedLoginAttempts = 0, LockedUntil = NULL
                    WHERE UserID = ?
                    """, user.UserID)
                    
                    conn.commit()
                    
                    # Log successful login
                    self.log_activity(user.UserID, None, None, 'Login Success', f"User {username} logged in")
                    
                    return {
                        'user_id': user.UserID,
                        'username': user.Username,
                        'email': user.Email,
                        'first_name': user.FirstName,
                        'last_name': user.LastName,
                        'role': user.Role
                    }
                else:
                    # Failed login - increment failed attempts
                    failed_attempts = user.FailedLoginAttempts + 1
                    locked_until = None
                    
                    if failed_attempts >= self.config.get('auth.max_login_attempts', 5):
                        locked_until = datetime.now() + self.config.get('auth.lockout_duration', timedelta(minutes=30))
                    
                    cursor.execute("""
                    UPDATE Users 
                    SET FailedLoginAttempts = ?, LockedUntil = ?
                    WHERE UserID = ?
                    """, (failed_attempts, locked_until, user.UserID))
                    
                    conn.commit()
                    
                    # Log failed login
                    self.log_activity(user.UserID, None, None, 'Login Failed', f"Failed login attempt for {username}")
                    
                    return None
                    
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT UserID, Username, Email, FirstName, LastName, Role, Phone, Department, JobTitle, CreatedDate, LastLoginDate
                FROM Users 
                WHERE UserID = ? AND Active = 1
                """, user_id)
                
                user = cursor.fetchone()
                if user:
                    return {
                        'user_id': user.UserID,
                        'username': user.Username,
                        'email': user.Email,
                        'first_name': user.FirstName,
                        'last_name': user.LastName,
                        'role': user.Role,
                        'phone': user.Phone,
                        'department': user.Department,
                        'job_title': user.JobTitle,
                        'created_date': user.CreatedDate,
                        'last_login_date': user.LastLoginDate
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Get user by ID failed: {str(e)}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql("""
                SELECT UserID, Username, Email, FirstName, LastName, Role, Department, JobTitle, CreatedDate, LastLoginDate
                FROM Users 
                WHERE Active = 1
                ORDER BY LastName, FirstName
                """, conn)
                
                return df.to_dict('records')
                
        except Exception as e:
            self.logger.error(f"Get all users failed: {str(e)}")
            return []
    
    # Project Management Methods
    def create_project(self, project_data: Dict[str, Any], user_id: int) -> Optional[int]:
        """Create a new project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO Projects (ProjectName, Description, StartDate, EndDate, Status, Priority, Budget, ClientName, ClientEmail, Tags, CreatedBy, LastModifiedBy)
                OUTPUT INSERTED.ProjectID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_data['project_name'],
                    project_data.get('description'),
                    project_data.get('start_date'),
                    project_data.get('end_date'),
                    project_data.get('status', 'Planning'),
                    project_data.get('priority', 'Medium'),
                    project_data.get('budget'),
                    project_data.get('client_name'),
                    project_data.get('client_email'),
                    project_data.get('tags'),
                    user_id,
                    user_id
                ))
                
                project_id = cursor.fetchone()[0]
                
                # Add creator as project member with Manager role
                cursor.execute("""
                INSERT INTO ProjectMembers (ProjectID, UserID, Role)
                VALUES (?, ?, 'Manager')
                """, (project_id, user_id))
                
                conn.commit()
                
                # Log activity
                self.log_activity(user_id, project_id, None, 'Project Created', f"Project {project_data['project_name']} created")
                
                return project_id
                
        except Exception as e:
            self.logger.error(f"Project creation failed: {str(e)}")
            return None
    
    def get_projects_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all projects for a user"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql("""
                SELECT DISTINCT p.ProjectID, p.ProjectName, p.Description, p.StartDate, p.EndDate, 
                       p.Status, p.Priority, p.Budget, p.ActualCost, p.Progress, p.ClientName,
                       p.CreatedDate, u.Username as CreatedByName, pm.Role as UserRole
                FROM Projects p
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                LEFT JOIN Users u ON p.CreatedBy = u.UserID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                ORDER BY p.LastModifiedDate DESC
                """, conn, params=[user_id])
                
                return df.to_dict('records')
                
        except Exception as e:
            self.logger.error(f"Get projects for user failed: {str(e)}")
            return []
    
    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT p.*, u.Username as CreatedByName
                FROM Projects p
                LEFT JOIN Users u ON p.CreatedBy = u.UserID
                WHERE p.ProjectID = ?
                """, project_id)
                
                project = cursor.fetchone()
                if project:
                    return {
                        'project_id': project.ProjectID,
                        'project_name': project.ProjectName,
                        'description': project.Description,
                        'start_date': project.StartDate,
                        'end_date': project.EndDate,
                        'status': project.Status,
                        'priority': project.Priority,
                        'budget': project.Budget,
                        'actual_cost': project.ActualCost,
                        'progress': project.Progress,
                        'client_name': project.ClientName,
                        'client_email': project.ClientEmail,
                        'tags': project.Tags,
                        'created_date': project.CreatedDate,
                        'created_by_name': project.CreatedByName
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Get project by ID failed: {str(e)}")
            return None
    
    # Task Management Methods
    def create_task(self, task_data: Dict[str, Any], user_id: int) -> Optional[int]:
        """Create a new task"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO Tasks (ProjectID, TaskName, Description, StartDate, EndDate, AssigneeID, Status, Priority, EstimatedHours, CreatedBy, LastModifiedBy)
                OUTPUT INSERTED.TaskID
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data['project_id'],
                    task_data['task_name'],
                    task_data.get('description'),
                    task_data.get('start_date'),
                    task_data.get('end_date'),
                    task_data.get('assignee_id'),
                    task_data.get('status', 'To Do'),
                    task_data.get('priority', 'Medium'),
                    task_data.get('estimated_hours'),
                    user_id,
                    user_id
                ))
                
                task_id = cursor.fetchone()[0]
                conn.commit()
                
                # Log activity
                self.log_activity(user_id, task_data['project_id'], task_id, 'Task Created', f"Task {task_data['task_name']} created")
                
                return task_id
                
        except Exception as e:
            self.logger.error(f"Task creation failed: {str(e)}")
            return None
    
    def get_tasks_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a project"""
        try:
            with self.get_connection() as conn:
                df = pd.read_sql("""
                SELECT t.*, u1.Username as AssigneeName, u2.Username as CreatedByName
                FROM Tasks t
                LEFT JOIN Users u1 ON t.AssigneeID = u1.UserID
                LEFT JOIN Users u2 ON t.CreatedBy = u2.UserID
                WHERE t.ProjectID = ?
                ORDER BY t.Order_Index, t.CreatedDate
                """, conn, params=[project_id])
                
                return df.to_dict('records')
                
        except Exception as e:
            self.logger.error(f"Get tasks for project failed: {str(e)}")
            return []
    
    def update_task_progress(self, task_id: int, progress: int, user_id: int) -> bool:
        """Update task progress"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update progress and status if completed
                status = 'Completed' if progress == 100 else 'In Progress' if progress > 0 else 'To Do'
                completed_date = datetime.now() if progress == 100 else None
                
                cursor.execute("""
                UPDATE Tasks 
                SET Progress = ?, Status = ?, CompletedDate = ?, LastModifiedDate = GETDATE(), LastModifiedBy = ?
                WHERE TaskID = ?
                """, (progress, status, completed_date, user_id, task_id))
                
                conn.commit()
                
                # Log activity
                self.log_activity(user_id, None, task_id, 'Task Progress Updated', f"Progress updated to {progress}%")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Update task progress failed: {str(e)}")
            return False
    
    # Analytics Methods
    def get_dashboard_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard metrics for user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get project metrics
                cursor.execute("""
                SELECT 
                    COUNT(*) as total_projects,
                    SUM(CASE WHEN Status = 'Active' THEN 1 ELSE 0 END) as active_projects,
                    SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as completed_projects,
                    AVG(CAST(Progress as FLOAT)) as avg_progress
                FROM Projects p
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                """, user_id)
                
                project_metrics = cursor.fetchone()
                
                # Get task metrics
                cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN Status = 'To Do' THEN 1 ELSE 0 END) as todo_tasks,
                    SUM(CASE WHEN Status = 'In Progress' THEN 1 ELSE 0 END) as inprogress_tasks,
                    SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN DueDate < CAST(GETDATE() AS DATE) AND Status != 'Completed' THEN 1 ELSE 0 END) as overdue_tasks
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                """, user_id)
                
                task_metrics = cursor.fetchone()
                
                return {
                    'projects': {
                        'total': project_metrics.total_projects or 0,
                        'active': project_metrics.active_projects or 0,
                        'completed': project_metrics.completed_projects or 0,
                        'avg_progress': round(project_metrics.avg_progress or 0, 1)
                    },
                    'tasks': {
                        'total': task_metrics.total_tasks or 0,
                        'todo': task_metrics.todo_tasks or 0,
                        'in_progress': task_metrics.inprogress_tasks or 0,
                        'completed': task_metrics.completed_tasks or 0,
                        'overdue': task_metrics.overdue_tasks or 0
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Get dashboard metrics failed: {str(e)}")
            return {'projects': {}, 'tasks': {}}
    
    def log_activity(self, user_id: int, project_id: Optional[int], task_id: Optional[int], action: str, details: str) -> None:
        """Log user activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO ActivityLogs (UserID, ProjectID, TaskID, Action, Details)
                VALUES (?, ?, ?, ?, ?)
                """, (user_id, project_id, task_id, action, details))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Activity logging failed: {str(e)}")
    
    def execute_query(self, query: str, params: List = None) -> pd.DataFrame:
        """Execute custom query and return DataFrame"""
        try:
            with self.get_connection() as conn:
                return pd.read_sql(query, conn, params=params or [])
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return pd.DataFrame()
    
    def execute_non_query(self, query: str, params: List = None) -> bool:
        """Execute non-query SQL command"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or [])
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Non-query execution failed: {str(e)}")
            return False