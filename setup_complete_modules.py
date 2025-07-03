#!/usr/bin/env python3
"""
สร้างไฟล์ modules ที่ขาดหายไปแบบด่วน
รันไฟล์นี้เพื่อสร้าง modules ทั้งหมดที่ app.py ต้องการ
"""
import os

# สร้างโฟลเดอร์
os.makedirs("modules", exist_ok=True)
os.makedirs("utils", exist_ok=True)

# modules/ui_components.py
ui_components = '''#!/usr/bin/env python3
"""
modules/ui_components.py
UI Components for DENSO Project Manager Pro
"""
import streamlit as st

class UIRenderer:
    """UI rendering utilities"""
    
    def __init__(self):
        self.theme = "default"
    
    def render_header(self, title: str, subtitle: str = None):
        """Render page header"""
        st.title(title)
        if subtitle:
            st.subheader(subtitle)
    
    def render_sidebar_nav(self, pages: list, current_page: str = None):
        """Render sidebar navigation"""
        return st.sidebar.selectbox("📌 เลือกหน้า", pages, index=0)
    
    def render_success_message(self, message: str):
        """Render success message"""
        st.success(f"✅ {message}")
    
    def render_error_message(self, message: str):
        """Render error message"""
        st.error(f"❌ {message}")
    
    def render_info_message(self, message: str):
        """Render info message"""
        st.info(f"ℹ️ {message}")
'''

# modules/projects.py
projects = '''#!/usr/bin/env python3
"""
modules/projects.py
Project Management for DENSO Project Manager Pro
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProjectManager:
    """Project management functionality"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        try:
            return self.db.execute_query("SELECT * FROM Projects ORDER BY CreatedDate DESC")
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            results = self.db.execute_query("SELECT * FROM Projects WHERE ProjectID = ?", (project_id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    def create_project(self, project_data: Dict[str, Any]) -> bool:
        """Create new project"""
        try:
            query = """
                INSERT INTO Projects (Name, Description, StartDate, EndDate, Status, Priority, Budget, ClientName, ManagerID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_non_query(query, (
                project_data.get('name'),
                project_data.get('description'),
                project_data.get('start_date'),
                project_data.get('end_date'),
                project_data.get('status', 'Planning'),
                project_data.get('priority', 'Medium'),
                project_data.get('budget'),
                project_data.get('client_name'),
                project_data.get('manager_id')
            ))
            logger.info(f"Project '{project_data.get('name')}' created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return False
'''

# modules/tasks.py
tasks = '''#!/usr/bin/env python3
"""
modules/tasks.py
Task Management for DENSO Project Manager Pro
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TaskManager:
    """Task management functionality"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks"""
        try:
            return self.db.execute_query("""
                SELECT t.*, p.Name as ProjectName, u.FirstName + ' ' + u.LastName as AssigneeName
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users u ON t.AssigneeID = u.UserID
                ORDER BY t.CreatedDate DESC
            """)
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    def get_tasks_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tasks by project ID"""
        try:
            return self.db.execute_query("""
                SELECT t.*, u.FirstName + ' ' + u.LastName as AssigneeName
                FROM Tasks t
                LEFT JOIN Users u ON t.AssigneeID = u.UserID
                WHERE t.ProjectID = ?
                ORDER BY t.CreatedDate DESC
            """, (project_id,))
        except Exception as e:
            logger.error(f"Error getting tasks for project {project_id}: {e}")
            return []
    
    def create_task(self, task_data: Dict[str, Any]) -> bool:
        """Create new task"""
        try:
            query = """
                INSERT INTO Tasks (ProjectID, Title, Description, AssigneeID, Status, Priority, StartDate, DueDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_non_query(query, (
                task_data.get('project_id'),
                task_data.get('title'),
                task_data.get('description'),
                task_data.get('assignee_id'),
                task_data.get('status', 'To Do'),
                task_data.get('priority', 'Medium'),
                task_data.get('start_date'),
                task_data.get('due_date')
            ))
            logger.info(f"Task '{task_data.get('title')}' created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return False
'''

# modules/analytics.py
analytics = '''#!/usr/bin/env python3
"""
modules/analytics.py
Analytics Manager for DENSO Project Manager Pro
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Analytics and reporting functionality"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = {}
            stats['total_projects'] = self.db.execute_scalar("SELECT COUNT(*) FROM Projects") or 0
            stats['total_tasks'] = self.db.execute_scalar("SELECT COUNT(*) FROM Tasks") or 0
            stats['total_users'] = self.db.execute_scalar("SELECT COUNT(*) FROM Users WHERE IsActive = 1") or 0
            stats['overdue_tasks'] = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Tasks WHERE DueDate < GETDATE() AND Status != 'Done'"
            ) or 0
            return stats
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    def get_project_progress(self) -> List[Dict[str, Any]]:
        """Get project progress data"""
        try:
            return self.db.execute_query("""
                SELECT 
                    p.Name,
                    p.Status,
                    COUNT(t.TaskID) as TotalTasks,
                    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks
                FROM Projects p
                LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
                GROUP BY p.ProjectID, p.Name, p.Status
            """)
        except Exception as e:
            logger.error(f"Error getting project progress: {e}")
            return []
'''

# modules/settings.py
settings = '''#!/usr/bin/env python3
"""
modules/settings.py
Settings Manager for DENSO Project Manager Pro
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SettingsManager:
    """System settings management"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "app_name": "DENSO Project Manager Pro",
            "version": "2.0.0",
            "environment": self.db.config.environment,
            "database": self.db.config.database,
            "server": self.db.config.server
        }
    
    def test_database_connection(self) -> bool:
        """Test database connection"""
        return self.db.test_connection()
'''

# modules/users.py
users = '''#!/usr/bin/env python3
"""
modules/users.py
User Management for DENSO Project Manager Pro
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class UserManager:
    """User management functionality"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            return self.db.execute_query("""
                SELECT UserID, Username, Email, FirstName, LastName, Role, Department, IsActive, CreatedDate, LastLogin
                FROM Users
                ORDER BY CreatedDate DESC
            """)
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM Users WHERE Username = ?", 
                (username,)
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
'''

# utils/error_handler.py
error_handler = '''#!/usr/bin/env python3
"""
utils/error_handler.py
Error Handling Utilities for DENSO Project Manager Pro
"""
import logging
import streamlit as st
from functools import wraps

logger = logging.getLogger(__name__)

def handle_streamlit_errors(func):
    """Decorator for handling Streamlit errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            st.error(f"เกิดข้อผิดพลาด: {str(e)}")
            return None
    return wrapper

def get_error_handler():
    """Get error handler instance"""
    return handle_streamlit_errors
'''

# utils/performance_monitor.py
performance_monitor = '''#!/usr/bin/env python3
"""
utils/performance_monitor.py
Performance Monitoring for DENSO Project Manager Pro
"""
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    def __init__(self):
        self.metrics = {}
    
    def time_function(self, func_name: str = None):
        """Decorator to time function execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                execution_time = end_time - start_time
                name = func_name or func.__name__
                
                logger.info(f"Function '{name}' executed in {execution_time:.4f} seconds")
                self.metrics[name] = execution_time
                
                return result
            return wrapper
        return decorator
    
    def get_metrics(self):
        """Get performance metrics"""
        return self.metrics
'''

# สร้างไฟล์ทั้งหมด
files = {
    "modules/ui_components.py": ui_components,
    "modules/projects.py": projects,
    "modules/tasks.py": tasks,
    "modules/analytics.py": analytics,
    "modules/settings.py": settings,
    "modules/users.py": users,
    "utils/error_handler.py": error_handler,
    "utils/performance_monitor.py": performance_monitor,
}

print("🔧 Creating missing modules...")

for file_path, content in files.items():
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Created: {file_path}")
    except Exception as e:
        print(f"❌ Error creating {file_path}: {e}")

# สร้าง __init__.py files
init_files = ["modules/__init__.py", "utils/__init__.py"]
for init_file in init_files:
    try:
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("# Package initialization")
        print(f"✅ Created: {init_file}")
    except Exception as e:
        print(f"❌ Error creating {init_file}: {e}")

print("\n🎉 All modules created successfully!")
print("▶️ Ready to run: streamlit run app.py")
