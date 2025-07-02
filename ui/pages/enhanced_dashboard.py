# ui/pages/enhanced_dashboard.py (แก้ไข import)
from ui.pages.enhanced_settings import render_enhanced_settings
from ui.pages.enhanced_team import render_enhanced_team


class EnhancedDashboard:
    def render(self):
        st.title("📊 Dashboard")
        st.info("Enhanced dashboard with real-time analytics")


# ui/pages/enhanced_reports.py
import streamlit as st


class EnhancedReports:
    def render(self):
        st.title("📈 Reports & Analytics")
        st.info("Advanced reporting and analytics coming soon")


# ui/pages/enhanced_settings.py (ใช้จากไฟล์ที่มีอยู่)
class EnhancedSettings:
    def render(self):
        render_enhanced_settings()


# ui/pages/enhanced_team.py (ใช้จากไฟล์ที่มีอยู่)
class EnhancedTeam:
    def render(self):
        render_enhanced_team()


# ui/pages/enhanced_gantt.py (แก้ไข constructor)
class EnhancedGantt:
    def __init__(self):
        from services.enhanced_db_service import get_db_service
        from services.task_service import get_task_service
        from services.enhanced_project_service import get_project_service

        self.db_service = get_db_service()
        self.task_service = get_task_service()
        self.project_service = get_project_service()

    # ... rest of the class remains the same


# ui/pages/enhanced_projects.py (แก้ไข constructor)
class EnhancedProjects:
    def __init__(self):
        from services.enhanced_db_service import get_db_service
        from services.enhanced_project_service import get_project_service

        self.db_service = get_db_service()
        self.project_service = get_project_service()

    # ... rest of the class remains the same


# ui/pages/enhanced_tasks.py (แก้ไข constructor)
class EnhancedTasks:
    def __init__(self):
        from services.enhanced_db_service import get_db_service
        from services.task_service import get_task_service
        from services.enhanced_project_service import get_project_service

        self.db_service = get_db_service()
        self.task_service = get_task_service()
        self.project_service = get_project_service()

    # ... rest of the class remains the same
