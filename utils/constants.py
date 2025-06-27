# utils/constants.py
"""
Application constants and enums
"""

from enum import Enum

# Application Information
APP_NAME = "Project Manager"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Enhanced Project Management System"


# Database Constants
class DatabaseConstants:
    """Database related constants"""

    DEFAULT_TIMEOUT = 30
    MAX_RETRY_ATTEMPTS = 3
    CONNECTION_POOL_SIZE = 5

    # Table Names
    USERS_TABLE = "Users"
    PROJECTS_TABLE = "Projects"
    TASKS_TABLE = "Tasks"


# User Roles
class UserRole(Enum):
    """User role enumeration"""

    USER = "User"
    MANAGER = "Manager"
    ADMIN = "Admin"


USER_ROLE_PERMISSIONS = {
    UserRole.USER: [
        "view_projects",
        "view_tasks",
        "update_own_tasks",
        "view_dashboard",
    ],
    UserRole.MANAGER: [
        "view_projects",
        "create_projects",
        "update_projects",
        "view_tasks",
        "create_tasks",
        "update_tasks",
        "view_dashboard",
        "view_reports",
    ],
    UserRole.ADMIN: [
        "view_projects",
        "create_projects",
        "update_projects",
        "delete_projects",
        "view_tasks",
        "create_tasks",
        "update_tasks",
        "delete_tasks",
        "view_dashboard",
        "view_reports",
        "manage_users",
        "system_settings",
    ],
}


# Project Status
class ProjectStatus(Enum):
    """Project status enumeration"""

    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    CANCELLED = "Cancelled"


PROJECT_STATUS_COLORS = {
    ProjectStatus.PLANNING: "#6c757d",  # Gray
    ProjectStatus.IN_PROGRESS: "#007bff",  # Blue
    ProjectStatus.COMPLETED: "#28a745",  # Green
    ProjectStatus.ON_HOLD: "#ffc107",  # Yellow
    ProjectStatus.CANCELLED: "#dc3545",  # Red
}


# Task Status
class TaskStatus(Enum):
    """Task status enumeration"""

    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    TESTING = "Testing"
    DONE = "Done"
    BLOCKED = "Blocked"


TASK_STATUS_COLORS = {
    TaskStatus.TODO: "#6c757d",  # Gray
    TaskStatus.IN_PROGRESS: "#007bff",  # Blue
    TaskStatus.TESTING: "#ffc107",  # Yellow
    TaskStatus.DONE: "#28a745",  # Green
    TaskStatus.BLOCKED: "#dc3545",  # Red
}


# Priority Levels
class Priority(Enum):
    """Priority level enumeration"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


PRIORITY_COLORS = {
    Priority.LOW: "#28a745",  # Green
    Priority.MEDIUM: "#ffc107",  # Yellow
    Priority.HIGH: "#fd7e14",  # Orange
    Priority.CRITICAL: "#dc3545",  # Red
}


# File Upload Constants
class FileConstants:
    """File upload related constants"""

    MAX_FILE_SIZE_MB = 10
    ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif"]
    ALLOWED_DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx", "txt", "md"]
    ALLOWED_SPREADSHEET_EXTENSIONS = ["xls", "xlsx", "csv"]

    ALL_ALLOWED_EXTENSIONS = (
        ALLOWED_IMAGE_EXTENSIONS
        + ALLOWED_DOCUMENT_EXTENSIONS
        + ALLOWED_SPREADSHEET_EXTENSIONS
    )


# UI Constants
class UIConstants:
    """User interface related constants"""

    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    # Chart Colors
    CHART_COLORS = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]

    # Status Icons
    STATUS_ICONS = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "pending": "⏳",
    }


# Date and Time Constants
class DateTimeConstants:
    """Date and time related constants"""

    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DISPLAY_DATE_FORMAT = "%d/%m/%Y"
    DISPLAY_DATETIME_FORMAT = "%d/%m/%Y %H:%M"

    # Report periods
    REPORT_PERIODS = {"today": 1, "week": 7, "month": 30, "quarter": 90, "year": 365}


# Validation Constants
class ValidationConstants:
    """Validation related constants"""

    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50
    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 255

    MAX_PROJECT_NAME_LENGTH = 100
    MAX_TASK_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000

    # Progress limits
    MIN_PROGRESS = 0
    MAX_PROGRESS = 100


# API Constants (for future API development)
class APIConstants:
    """API related constants"""

    API_VERSION = "v1"
    API_PREFIX = f"/api/{API_VERSION}"

    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute

    # Response codes
    SUCCESS_CODE = 200
    CREATED_CODE = 201
    BAD_REQUEST_CODE = 400
    UNAUTHORIZED_CODE = 401
    FORBIDDEN_CODE = 403
    NOT_FOUND_CODE = 404
    SERVER_ERROR_CODE = 500


# Error Messages
ERROR_MESSAGES = {
    "required_field": "This field is required",
    "invalid_format": "Invalid format",
    "database_error": "Database operation failed",
    "permission_denied": "Permission denied",
    "user_not_found": "User not found",
    "project_not_found": "Project not found",
    "task_not_found": "Task not found",
    "invalid_credentials": "Invalid username or password",
    "duplicate_username": "Username already exists",
    "file_too_large": "File size exceeds limit",
    "invalid_file_type": "Invalid file type",
}

# Success Messages
SUCCESS_MESSAGES = {
    "user_created": "User created successfully",
    "user_updated": "User updated successfully",
    "user_deleted": "User deleted successfully",
    "project_created": "Project created successfully",
    "project_updated": "Project updated successfully",
    "project_deleted": "Project deleted successfully",
    "task_created": "Task created successfully",
    "task_updated": "Task updated successfully",
    "task_deleted": "Task deleted successfully",
    "login_success": "Login successful",
    "logout_success": "Logout successful",
}

# Navigation Menu Items
MENU_ITEMS = [
    {
        "label": "📊 Dashboard",
        "key": "dashboard",
        "icon": "📊",
        "description": "ภาพรวมโปรเจกต์",
    },
    {
        "label": "📚 โปรเจกต์",
        "key": "projects",
        "icon": "📚",
        "description": "จัดการโปรเจกต์",
    },
    {"label": "✅ งาน", "key": "tasks", "icon": "✅", "description": "จัดการงาน"},
    {
        "label": "📅 Gantt Chart",
        "key": "gantt",
        "icon": "📅",
        "description": "แผนงานโปรเจกต์",
    },
    {
        "label": "📈 รายงาน",
        "key": "reports",
        "icon": "📈",
        "description": "รายงานและวิเคราะห์",
    },
    {"label": "⚙️ ตั้งค่า", "key": "settings", "icon": "⚙️", "description": "การตั้งค่าระบบ"},
]

# Quick Actions
QUICK_ACTIONS = [
    {
        "label": "➕ เพิ่มโปรเจกต์",
        "action": "add_project",
        "icon": "➕",
        "color": "primary",
    },
    {"label": "📝 เพิ่มงาน", "action": "add_task", "icon": "📝", "color": "secondary"},
]
