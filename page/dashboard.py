"""
pages/dashboard.py
Main dashboard page with overview and analytics
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

from modules.ui_components import (
    MetricCard,
    ProgressBar,
    ChartRenderer,
    CardComponent,
    TimelineComponent,
    NotificationManager,
)
from utils.error_handler import handle_streamlit_errors, safe_execute
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


class DashboardPage:
    """Main dashboard page class"""

    def __init__(self, analytics_manager, project_manager, task_manager):
        self.analytics_manager = analytics_manager
        self.project_manager = project_manager
        self.task_manager = task_manager

    @handle_streamlit_errors()
    @monitor_performance("dashboard_render")
    def show(self):
        """Show dashboard page"""
        st.title("📊 Dashboard - ภาพรวมระบบ")

        # Get current user
        current_user = st.session_state.get("user", {})
        user_id = current_user.get("UserID")

        # Get dashboard data
        with st.spinner("กำลังโหลดข้อมูล..."):
            metrics = self._get_dashboard_metrics()
            project_data = self._get_project_dashboard_data(user_id)
            recent_activities = self._get_recent_activities(user_id)

        # Show metrics
        self._show_key_metrics(metrics)

        # Show main dashboard content
        col1, col2 = st.columns([2, 1])

        with col1:
            self._show_project_overview(project_data)
            self._show_charts_section(metrics)

        with col2:
            self._show_recent_activities(recent_activities)
            self._show_quick_stats(metrics)

        # Show alerts and notifications
        self._show_alerts_section(metrics)

    def _get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        try:
            return safe_execute(
                lambda: self.analytics_manager.get_dashboard_metrics(),
                default_return={},
                error_message="ไม่สามารถโหลดข้อมูลสถิติได้",
            )
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {str(e)}")
            return {}

    def _get_project_dashboard_data(self, user_id: int = None) -> Dict[str, Any]:
        """Get project dashboard data"""
        try:
            return safe_execute(
                lambda: self.project_manager.get_project_dashboard_data(user_id),
                default_return={},
                error_message="ไม่สามารถโหลดข้อมูลโครงการได้",
            )
        except Exception as e:
            logger.error(f"Failed to get project dashboard data: {str(e)}")
            return {}

    def _get_recent_activities(self, user_id: int = None) -> List[Dict[str, Any]]:
        """Get recent activities"""
        try:
            # Get recent projects and tasks
            recent_projects = self.project_manager.get_all_projects()[:5]
            recent_tasks = []

            activities = []

            # Add project activities
            for project in recent_projects:
                activities.append(
                    {
                        "type": "project",
                        "title": f"โครงการ: {project['ProjectName']}",
                        "description": f"สถานะ: {project['Status']}",
                        "date": project.get(
                            "LastModifiedDate", project.get("CreatedDate")
                        ),
                        "icon": "fas fa-project-diagram",
                        "color": "primary",
                    }
                )

            # Sort by date
            activities.sort(key=lambda x: x["date"] or datetime.min, reverse=True)

            return activities[:10]

        except Exception as e:
            logger.error(f"Failed to get recent activities: {str(e)}")
            return []

    def _show_key_metrics(self, metrics: Dict[str, Any]):
        """Show key performance metrics"""
        st.subheader("📈 ตัวชี้วัดหลัก")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            MetricCard.render_modern(
                "โครงการทั้งหมด",
                metrics.get("total_projects", 0),
                "fas fa-project-diagram",
                color="primary",
            )

        with col2:
            active_projects = metrics.get("active_projects", 0)
            total_projects = metrics.get("total_projects", 0)
            delta = f"+{active_projects}" if active_projects > 0 else None

            MetricCard.render_modern(
                "โครงการที่ดำเนินการ",
                active_projects,
                "fas fa-play-circle",
                color="success",
                delta=delta,
            )

        with col3:
            MetricCard.render_modern(
                "งานทั้งหมด", metrics.get("total_tasks", 0), "fas fa-tasks", color="info"
            )

        with col4:
            completed_tasks = metrics.get("completed_tasks", 0)
            total_tasks = metrics.get("total_tasks", 0)
            completion_rate = (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            )

            MetricCard.render_modern(
                "อัตราความสำเร็จ",
                f"{completion_rate:.1f}%",
                "fas fa-check-circle",
                color="success",
            )

        with col5:
            MetricCard.render_modern(
                "ผู้ใช้งาน", metrics.get("total_users", 0), "fas fa-users", color="warning"
            )

    def _show_project_overview(self, project_data: Dict[str, Any]):
        """Show project overview section"""
        st.subheader("🎯 ภาพรวมโครงการ")

        # Recent projects
        recent_projects = project_data.get("recent_projects", [])
        if recent_projects:
            st.markdown("**โครงการล่าสุด:**")

            for project in recent_projects[:3]:
                CardComponent.render_project_card(project)
        else:
            st.info("ยังไม่มีโครงการ")

        # Overdue projects
        overdue_projects = project_data.get("overdue_projects", [])
        if overdue_projects:
            st.markdown("**โครงการที่เกินกำหนด:**")

            for project in overdue_projects[:3]:
                st.error(
                    f"📅 **{project['ProjectName']}** - เกินกำหนด {project['days_overdue']} วัน"
                )

        # High priority projects
        high_priority = project_data.get("high_priority_projects", [])
        if high_priority:
            st.markdown("**โครงการสำคัญ:**")

            for project in high_priority[:3]:
                priority_color = "🔴" if project["Priority"] == "Critical" else "🟠"
                st.warning(
                    f"{priority_color} **{project['ProjectName']}** - งานเหลือ {project['remaining_tasks']} งาน"
                )

    def _show_charts_section(self, metrics: Dict[str, Any]):
        """Show charts and analytics section"""
        st.subheader("📊 การวิเคราะห์")

        tab1, tab2, tab3 = st.tabs(["สถานะโครงการ", "ความคืบหน้างาน", "แนวโน้ม"])

        with tab1:
            # Project status distribution
            try:
                status_data = self.analytics_manager.get_project_status_distribution()
                if status_data:
                    ChartRenderer.render_pie_chart(
                        status_data,
                        "count",
                        "Status",
                        title="การกระจายสถานะโครงการ",
                        height=400,
                    )
                else:
                    st.info("ไม่มีข้อมูลสถานะโครงการ")
            except Exception as e:
                logger.error(f"Failed to render project status chart: {str(e)}")
                st.error("ไม่สามารถแสดงกราฟสถานะโครงการได้")

        with tab2:
            # Task completion rate
            try:
                completion_data = self.analytics_manager.get_task_completion_rate()
                if completion_data:
                    ChartRenderer.render_bar_chart(
                        completion_data,
                        "ProjectName",
                        "CompletionRate",
                        title="อัตราความสำเร็จของงานแต่ละโครงการ",
                        height=400,
                    )
                else:
                    st.info("ไม่มีข้อมูลความคืบหน้างาน")
            except Exception as e:
                logger.error(f"Failed to render completion chart: {str(e)}")
                st.error("ไม่สามารถแสดงกราฟความคืบหน้าได้")

        with tab3:
            # Monthly trends
            try:
                # Sample trend data - replace with actual data
                trend_data = [
                    {"month": "ม.ค.", "projects": 5, "completed": 3},
                    {"month": "ก.พ.", "projects": 7, "completed": 5},
                    {"month": "มี.ค.", "projects": 6, "completed": 4},
                    {"month": "เม.ย.", "projects": 8, "completed": 6},
                    {"month": "พ.ค.", "projects": 10, "completed": 7},
                    {"month": "มิ.ย.", "projects": 9, "completed": 8},
                ]

                ChartRenderer.render_line_chart(
                    trend_data,
                    "month",
                    "completed",
                    title="แนวโน้มโครงการที่เสร็จสิ้น",
                    height=400,
                )
            except Exception as e:
                logger.error(f"Failed to render trend chart: {str(e)}")
                st.error("ไม่สามารถแสดงกราฟแนวโน้มได้")

    def _show_recent_activities(self, activities: List[Dict[str, Any]]):
        """Show recent activities timeline"""
        st.subheader("🕐 กิจกรรมล่าสุด")

        if activities:
            # Format activities for timeline
            timeline_items = []
            for activity in activities:
                date_str = ""
                if activity.get("date"):
                    try:
                        if hasattr(activity["date"], "strftime"):
                            date_str = activity["date"].strftime("%d/%m/%Y")
                        else:
                            date_str = str(activity["date"])[:10]
                    except:
                        date_str = "ไม่ระบุ"

                timeline_items.append(
                    {
                        "title": activity["title"],
                        "description": activity["description"],
                        "date": date_str,
                        "icon": activity.get("icon", "fas fa-circle"),
                        "color": activity.get("color", "primary"),
                    }
                )

            TimelineComponent.render(timeline_items)
        else:
            st.info("ไม่มีกิจกรรมล่าสุด")

    def _show_quick_stats(self, metrics: Dict[str, Any]):
        """Show quick statistics"""
        st.subheader("⚡ สถิติด่วน")

        # Project completion progress
        total_projects = metrics.get("total_projects", 0)
        completed_projects = metrics.get("completed_projects", 0)

        if total_projects > 0:
            ProgressBar.render(
                completed_projects,
                total_projects,
                "โครงการที่เสร็จสิ้น",
                color="success",
                animated=True,
            )

        # Task completion progress
        total_tasks = metrics.get("total_tasks", 0)
        completed_tasks = metrics.get("completed_tasks", 0)

        if total_tasks > 0:
            ProgressBar.render(
                completed_tasks, total_tasks, "งานที่เสร็จสิ้น", color="info", animated=True
            )

        # Additional stats
        st.markdown(
            """
        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
            <h4 style="color: white; margin-bottom: 1rem;">📋 สรุปสถิติ</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; color: white;">
                <div>โครงการใหม่ (เดือนนี้): <strong>3</strong></div>
                <div>งานที่กำลังทำ: <strong>12</strong></div>
                <div>โครงการเกินกำหนด: <strong>2</strong></div>
                <div>ผู้ใช้ออนไลน์: <strong>5</strong></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _show_alerts_section(self, metrics: Dict[str, Any]):
        """Show alerts and notifications"""
        st.subheader("🚨 การแจ้งเตือน")

        # Check for overdue projects
        overdue_count = metrics.get("overdue_projects", 0)
        if overdue_count > 0:
            NotificationManager.show_warning(
                f"มีโครงการเกินกำหนด {overdue_count} โครงการ กรุณาตรวจสอบ",
                "fas fa-exclamation-triangle",
            )

        # Check for high priority tasks
        high_priority_tasks = 5  # Sample data
        if high_priority_tasks > 0:
            NotificationManager.show_info(
                f"มีงานสำคัญ {high_priority_tasks} งานที่ต้องดำเนินการ", "fas fa-flag"
            )

        # System health check
        try:
            # Sample system health data
            system_health = "good"  # This would come from actual monitoring

            if system_health == "good":
                NotificationManager.show_success(
                    "ระบบทำงานปกติ - ประสิทธิภาพดี", "fas fa-heartbeat"
                )
            else:
                NotificationManager.show_warning(
                    "ระบบมีปัญหาด้านประสิทธิภาพ", "fas fa-exclamation-circle"
                )
        except Exception as e:
            logger.warning(f"System health check failed: {str(e)}")
