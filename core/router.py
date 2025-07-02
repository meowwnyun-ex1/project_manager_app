# core/router.py
import streamlit as st
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class Router:
    """Simple router for page navigation"""

    def __init__(self):
        self.pages = {
            "dashboard": self._render_dashboard,
            "projects": self._render_projects,
            "tasks": self._render_tasks,
            "gantt": self._render_gantt,
            "team": self._render_team,
            "reports": self._render_reports,
            "settings": self._render_settings,
        }

    def route(self) -> None:
        """Main routing logic"""
        try:
            # Get current page from session state
            current_page = st.session_state.get("current_page", "dashboard")

            # Render page
            if current_page in self.pages:
                self.pages[current_page]()
            else:
                self._render_dashboard()

        except Exception as e:
            logger.error(f"Routing error: {str(e)}")
            st.error(f"Page loading error: {str(e)}")

    def _render_dashboard(self):
        """Render dashboard page"""
        from ui.pages.enhanced_dashboard import EnhancedDashboard

        dashboard = EnhancedDashboard()
        dashboard.render()

    def _render_projects(self):
        """Render projects page"""
        try:
            from ui.pages.enhanced_projects import EnhancedProjectsPage
            from services.enhanced_db_service import get_db_service
            from services.enhanced_project_service import get_project_service

            projects_page = EnhancedProjectsPage(
                get_db_service(), get_project_service()
            )
            projects_page.render()
        except Exception as e:
            st.error(f"Error loading projects page: {str(e)}")
            st.info("Projects page coming soon")

    def _render_tasks(self):
        """Render tasks page"""
        try:
            from ui.pages.enhanced_tasks import EnhancedTasksPage
            from services.enhanced_db_service import get_db_service
            from services.task_service import get_task_service
            from services.enhanced_project_service import get_project_service

            tasks_page = EnhancedTasksPage(
                get_db_service(), get_task_service(), get_project_service()
            )
            tasks_page.render()
        except Exception as e:
            st.error(f"Error loading tasks page: {str(e)}")
            st.info("Tasks page coming soon")

    def _render_gantt(self):
        """Render gantt chart page"""
        try:
            from ui.pages.enhanced_gantt import EnhancedGanttPage
            from services.enhanced_db_service import get_db_service
            from services.task_service import get_task_service
            from services.enhanced_project_service import get_project_service

            gantt_page = EnhancedGanttPage(
                get_db_service(), get_task_service(), get_project_service()
            )
            gantt_page.render()
        except Exception as e:
            st.error(f"Error loading gantt page: {str(e)}")
            st.info("Gantt chart page coming soon")

    def _render_team(self):
        """Render team page"""
        try:
            from ui.pages.enhanced_team import render_enhanced_team

            render_enhanced_team()
        except Exception as e:
            st.error(f"Error loading team page: {str(e)}")
            st.info("Team page coming soon")

    def _render_reports(self):
        """Render reports page"""
        st.title("📈 Reports & Analytics")
        st.info("📊 Advanced reporting and analytics coming soon")

        # Sample metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Projects", "45", "5")
        with col2:
            st.metric("Completed Tasks", "234", "12")
        with col3:
            st.metric("Team Productivity", "87%", "3%")
        with col4:
            st.metric("On-time Delivery", "92%", "1%")

    def _render_settings(self):
        """Render settings page"""
        try:
            from ui.pages.enhanced_settings import render_enhanced_settings

            render_enhanced_settings()
        except Exception as e:
            st.error(f"Error loading settings page: {str(e)}")
            st.info("Settings page coming soon")
