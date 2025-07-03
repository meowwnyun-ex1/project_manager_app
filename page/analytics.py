"""
pages/analytics.py
Analytics and reporting page
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
import logging

from modules.ui_components import (
    MetricCard,
    ChartRenderer,
    CardComponent,
    ExportManager,
    NotificationManager,
)
from modules.auth import require_role, get_current_user
from modules.analytics import AnalyticsManager
from utils.error_handler import handle_streamlit_errors, safe_execute
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


class AnalyticsPage:
    """Analytics and reporting page class"""

    def __init__(self, analytics_manager, project_manager, task_manager, user_manager):
        self.analytics_manager = analytics_manager
        self.project_manager = project_manager
        self.task_manager = task_manager
        self.user_manager = user_manager

    @handle_streamlit_errors()
    @monitor_performance("analytics_page_render")
    def show(self):
        """Show analytics page"""
        st.title("📊 รายงานและการวิเคราะห์")

        # Get current user
        current_user = get_current_user()
        if not current_user:
            st.error("กรุณาเข้าสู่ระบบ")
            return

        # Check permissions
        if not self._has_analytics_permission(current_user):
            st.error("คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
            return

        # Show analytics content
        self._show_analytics_content()

    def _show_analytics_content(self):
        """Show main analytics content"""
        # Date range selector
        self._show_date_range_selector()

        # Key metrics overview
        self._show_key_metrics()

        # Charts section
        self._show_charts_section()

        # Detailed reports
        self._show_detailed_reports()

    def _show_date_range_selector(self):
        """Show date range selector"""
        st.subheader("📅 เลือกช่วงเวลา")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            start_date = st.date_input(
                "วันที่เริ่มต้น",
                value=date.today() - timedelta(days=30),
                max_value=date.today(),
            )

        with col2:
            end_date = st.date_input(
                "วันที่สิ้นสุด", value=date.today(), max_value=date.today()
            )

        with col3:
            quick_ranges = st.selectbox(
                "ช่วงเวลาด่วน",
                [
                    "กำหนดเอง",
                    "7 วันที่แล้ว",
                    "30 วันที่แล้ว",
                    "3 เดือนที่แล้ว",
                    "6 เดือนที่แล้ว",
                    "1 ปีที่แล้ว",
                ],
            )

            if quick_ranges != "กำหนดเอง":
                days_map = {
                    "7 วันที่แล้ว": 7,
                    "30 วันที่แล้ว": 30,
                    "3 เดือนที่แล้ว": 90,
                    "6 เดือนที่แล้ว": 180,
                    "1 ปีที่แล้ว": 365,
                }
                days = days_map.get(quick_ranges, 30)
                start_date = date.today() - timedelta(days=days)
                end_date = date.today()

        with col4:
            if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        # Store dates in session state
        st.session_state.analytics_start_date = start_date
        st.session_state.analytics_end_date = end_date

    def _show_key_metrics(self):
        """Show key metrics overview"""
        st.subheader("📈 ตัวชี้วัดหลัก")

        # Get metrics data
        start_date = st.session_state.get(
            "analytics_start_date", date.today() - timedelta(days=30)
        )
        end_date = st.session_state.get("analytics_end_date", date.today())

        metrics = self._get_key_metrics(start_date, end_date)

        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            self._show_metric_card(
                "โครงการทั้งหมด",
                metrics.get("total_projects", 0),
                metrics.get("projects_change", 0),
                "📁",
            )

        with col2:
            self._show_metric_card(
                "งานทั้งหมด",
                metrics.get("total_tasks", 0),
                metrics.get("tasks_change", 0),
                "✅",
            )

        with col3:
            self._show_metric_card(
                "งานที่เสร็จแล้ว",
                metrics.get("completed_tasks", 0),
                metrics.get("completed_change", 0),
                "✔️",
            )

        with col4:
            completion_rate = metrics.get("completion_rate", 0)
            self._show_metric_card(
                "อัตราความสำเร็จ",
                f"{completion_rate:.1f}%",
                metrics.get("completion_change", 0),
                "🎯",
            )

    def _show_metric_card(self, title: str, value: Any, change: float, icon: str):
        """Show individual metric card"""
        with st.container():
            st.markdown(
                f"""
            <div style="padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem; text-align: center;">
                <h3>{icon} {title}</h3>
                <h1 style="margin: 0.5rem 0; color: #1f77b4;">{value}</h1>
                <p style="margin: 0; color: {'green' if change >= 0 else 'red'};">
                    {'📈' if change > 0 else '📉' if change < 0 else '➡️'} 
                    {abs(change):.1f}% จากช่วงก่อนหน้า
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def _show_charts_section(self):
        """Show charts section"""
        st.subheader("📊 กราฟและแผนภูมิ")

        # Get chart data
        start_date = st.session_state.get("analytics_start_date")
        end_date = st.session_state.get("analytics_end_date")

        chart_data = self._get_chart_data(start_date, end_date)

        # Chart tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📈 ความคืบหน้า", "📊 สถานะงาน", "👥 ประสิทธิภาพทีม", "⏰ Timeline"]
        )

        with tab1:
            self._show_progress_charts(chart_data)

        with tab2:
            self._show_status_charts(chart_data)

        with tab3:
            self._show_team_performance_charts(chart_data)

        with tab4:
            self._show_timeline_charts(chart_data)

    def _show_progress_charts(self, data: Dict):
        """Show progress charts"""
        col1, col2 = st.columns(2)

        with col1:
            # Project progress chart
            if data.get("project_progress"):
                fig = px.bar(
                    data["project_progress"],
                    x="ProjectName",
                    y="Progress",
                    title="ความคืบหน้าโครงการ",
                    color="Progress",
                    color_continuous_scale="RdYlGn",
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลความคืบหน้าโครงการ")

        with col2:
            # Tasks completion over time
            if data.get("task_completion_timeline"):
                fig = px.line(
                    data["task_completion_timeline"],
                    x="Date",
                    y="CompletedTasks",
                    title="งานที่เสร็จสิ้นตามเวลา",
                    markers=True,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูล Timeline งานที่เสร็จสิ้น")

    def _show_status_charts(self, data: Dict):
        """Show status charts"""
        col1, col2 = st.columns(2)

        with col1:
            # Task status pie chart
            if data.get("task_status_distribution"):
                fig = px.pie(
                    data["task_status_distribution"],
                    values="Count",
                    names="Status",
                    title="การกระจายสถานะงาน",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลการกระจายสถานะงาน")

        with col2:
            # Priority distribution
            if data.get("priority_distribution"):
                fig = px.bar(
                    data["priority_distribution"],
                    x="Priority",
                    y="Count",
                    title="การกระจายความสำคัญของงาน",
                    color="Priority",
                    color_discrete_map={
                        "Low": "blue",
                        "Medium": "orange",
                        "High": "red",
                        "Critical": "darkred",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลการกระจายความสำคัญ")

    def _show_team_performance_charts(self, data: Dict):
        """Show team performance charts"""
        col1, col2 = st.columns(2)

        with col1:
            # User productivity
            if data.get("user_productivity"):
                fig = px.bar(
                    data["user_productivity"],
                    x="UserName",
                    y="CompletedTasks",
                    title="ประสิทธิภาพการทำงานของทีม",
                    color="CompletedTasks",
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลประสิทธิภาพทีม")

        with col2:
            # Average task completion time
            if data.get("avg_completion_time"):
                fig = px.bar(
                    data["avg_completion_time"],
                    x="UserName",
                    y="AvgDays",
                    title="เวลาเฉลี่ยในการทำงานเสร็จ (วัน)",
                    color="AvgDays",
                    color_continuous_scale="RdYlBu_r",
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลเวลาเฉลี่ยการทำงาน")

    def _show_timeline_charts(self, data: Dict):
        """Show timeline charts"""
        # Gantt chart for active projects
        if data.get("project_timeline"):
            fig = px.timeline(
                data["project_timeline"],
                x_start="StartDate",
                x_end="EndDate",
                y="ProjectName",
                color="Status",
                title="Timeline โครงการ",
            )
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูล Timeline โครงการ")

    def _show_detailed_reports(self):
        """Show detailed reports section"""
        st.subheader("📋 รายงานละเอียด")

        # Report type selector
        report_types = [
            "รายงานโครงการ",
            "รายงานงาน",
            "รายงานประสิทธิภาพทีม",
            "รายงานการใช้เวลา",
            "รายงานงานที่เลยกำหนด",
        ]

        selected_report = st.selectbox("เลือกประเภทรายงาน", report_types)

        # Show selected report
        if selected_report == "รายงานโครงการ":
            self._show_project_report()
        elif selected_report == "รายงานงาน":
            self._show_task_report()
        elif selected_report == "รายงานประสิทธิภาพทีม":
            self._show_team_report()
        elif selected_report == "รายงานการใช้เวลา":
            self._show_time_report()
        elif selected_report == "รายงานงานที่เลยกำหนด":
            self._show_overdue_report()

    def _show_project_report(self):
        """Show project report"""
        st.markdown("### 📁 รายงานโครงการ")

        # Get project data
        start_date = st.session_state.get("analytics_start_date")
        end_date = st.session_state.get("analytics_end_date")

        projects_data = self._get_projects_report_data(start_date, end_date)

        if projects_data:
            # Create DataFrame
            df = pd.DataFrame(projects_data)

            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Progress": st.column_config.ProgressColumn(
                        "ความคืบหน้า",
                        help="ความคืบหน้าของโครงการ",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Budget": st.column_config.NumberColumn(
                        "งบประมาณ", help="งบประมาณของโครงการ", format="฿%.2f"
                    ),
                },
            )

            # Export button
            if st.button("📤 ส่งออกรายงานโครงการ"):
                self._export_report(df, "project_report")
        else:
            st.info("ไม่มีข้อมูลโครงการในช่วงเวลาที่เลือก")

    def _show_task_report(self):
        """Show task report"""
        st.markdown("### ✅ รายงานงาน")

        # Task filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.multiselect(
                "กรองสถานะ", ["To Do", "In Progress", "Review", "Testing", "Done"]
            )

        with col2:
            priority_filter = st.multiselect(
                "กรองความสำคัญ", ["Low", "Medium", "High", "Critical"]
            )

        with col3:
            assignee_filter = st.multiselect(
                "กรองผู้รับผิดชอบ", self._get_assignee_options()
            )

        # Get task data
        tasks_data = self._get_tasks_report_data(
            status_filter, priority_filter, assignee_filter
        )

        if tasks_data:
            df = pd.DataFrame(tasks_data)
            st.dataframe(df, use_container_width=True)

            if st.button("📤 ส่งออกรายงานงาน"):
                self._export_report(df, "task_report")
        else:
            st.info("ไม่มีข้อมูลงานที่ตรงตามเงื่อนไข")

    def _show_team_report(self):
        """Show team performance report"""
        st.markdown("### 👥 รายงานประสิทธิภาพทีม")

        team_data = self._get_team_performance_data()

        if team_data:
            # Team summary
            col1, col2, col3 = st.columns(3)

            with col1:
                total_members = len(team_data)
                st.metric("สมาชิกทีมทั้งหมด", total_members)

            with col2:
                avg_tasks = sum(member["TasksCompleted"] for member in team_data) / len(
                    team_data
                )
                st.metric("งานเฉลี่ยต่อคน", f"{avg_tasks:.1f}")

            with col3:
                active_members = len([m for m in team_data if m["TasksAssigned"] > 0])
                st.metric("สมาชิกที่ทำงานอยู่", active_members)

            # Team details table
            df = pd.DataFrame(team_data)
            st.dataframe(df, use_container_width=True)

            if st.button("📤 ส่งออกรายงานทีม"):
                self._export_report(df, "team_report")
        else:
            st.info("ไม่มีข้อมูลประสิทธิภาพทีม")

    def _show_time_report(self):
        """Show time tracking report"""
        st.markdown("### ⏰ รายงานการใช้เวลา")

        time_data = self._get_time_tracking_data()

        if time_data:
            # Time summary
            col1, col2, col3 = st.columns(3)

            with col1:
                total_hours = sum(
                    item["EstimatedHours"]
                    for item in time_data
                    if item["EstimatedHours"]
                )
                st.metric("เวลาที่คาดการณ์ทั้งหมด", f"{total_hours:.1f} ชม.")

            with col2:
                completed_hours = sum(
                    item["EstimatedHours"]
                    for item in time_data
                    if item["Status"] == "Done" and item["EstimatedHours"]
                )
                st.metric("เวลาที่ใช้จริง", f"{completed_hours:.1f} ชม.")

            with col3:
                if total_hours > 0:
                    efficiency = (completed_hours / total_hours) * 100
                    st.metric("ประสิทธิภาพการใช้เวลา", f"{efficiency:.1f}%")

            # Time details
            df = pd.DataFrame(time_data)
            st.dataframe(df, use_container_width=True)

            if st.button("📤 ส่งออกรายงานเวลา"):
                self._export_report(df, "time_report")
        else:
            st.info("ไม่มีข้อมูลการใช้เวลา")

    def _show_overdue_report(self):
        """Show overdue tasks report"""
        st.markdown("### ⚠️ รายงานงานที่เลยกำหนด")

        overdue_data = self._get_overdue_tasks_data()

        if overdue_data:
            # Overdue summary
            col1, col2, col3 = st.columns(3)

            with col1:
                total_overdue = len(overdue_data)
                st.metric("งานที่เลยกำหนดทั้งหมด", total_overdue, delta_color="inverse")

            with col2:
                avg_overdue_days = sum(
                    item["DaysOverdue"] for item in overdue_data
                ) / len(overdue_data)
                st.metric(
                    "เฉลี่ยวันที่เลยกำหนด",
                    f"{avg_overdue_days:.1f} วัน",
                    delta_color="inverse",
                )

            with col3:
                critical_overdue = len(
                    [item for item in overdue_data if item["Priority"] == "Critical"]
                )
                st.metric("งานสำคัญที่เลยกำหนด", critical_overdue, delta_color="inverse")

            # Overdue details
            df = pd.DataFrame(overdue_data)

            # Style the dataframe
            def highlight_overdue(val):
                if val > 7:
                    return "background-color: #ffcccc"
                elif val > 3:
                    return "background-color: #ffffcc"
                return ""

            styled_df = df.style.applymap(highlight_overdue, subset=["DaysOverdue"])
            st.dataframe(styled_df, use_container_width=True)

            if st.button("📤 ส่งออกรายงานงานเลยกำหนด"):
                self._export_report(df, "overdue_report")
        else:
            st.success("🎉 ไม่มีงานที่เลยกำหนด!")

    # Helper methods
    def _has_analytics_permission(self, user: Dict) -> bool:
        """Check if user has analytics permission"""
        allowed_roles = ["Admin", "Project Manager", "Team Lead"]
        return user.get("Role") in allowed_roles

    def _get_key_metrics(self, start_date: date, end_date: date) -> Dict:
        """Get key metrics data"""
        return safe_execute(
            self.analytics_manager.get_key_metrics,
            start_date,
            end_date,
            default_return={},
        )

    def _get_chart_data(self, start_date: date, end_date: date) -> Dict:
        """Get chart data"""
        return safe_execute(
            self.analytics_manager.get_chart_data,
            start_date,
            end_date,
            default_return={},
        )

    def _get_projects_report_data(self, start_date: date, end_date: date) -> List[Dict]:
        """Get projects report data"""
        return safe_execute(
            self.analytics_manager.get_projects_report,
            start_date,
            end_date,
            default_return=[],
        )

    def _get_tasks_report_data(
        self, status_filter: List, priority_filter: List, assignee_filter: List
    ) -> List[Dict]:
        """Get tasks report data"""
        filters = {
            "status": status_filter,
            "priority": priority_filter,
            "assignee": assignee_filter,
        }
        return safe_execute(
            self.analytics_manager.get_tasks_report, filters, default_return=[]
        )

    def _get_team_performance_data(self) -> List[Dict]:
        """Get team performance data"""
        return safe_execute(
            self.analytics_manager.get_team_performance, default_return=[]
        )

    def _get_time_tracking_data(self) -> List[Dict]:
        """Get time tracking data"""
        return safe_execute(
            self.analytics_manager.get_time_tracking_report, default_return=[]
        )

    def _get_overdue_tasks_data(self) -> List[Dict]:
        """Get overdue tasks data"""
        return safe_execute(self.analytics_manager.get_overdue_tasks, default_return=[])

    def _get_assignee_options(self) -> List[str]:
        """Get assignee options for filtering"""
        users = safe_execute(self.user_manager.get_active_users, default_return=[])
        return [f"{user['FirstName']} {user['LastName']}" for user in users]

    def _export_report(self, df: pd.DataFrame, report_type: str):
        """Export report to CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_type}_{timestamp}.csv"

            # Convert DataFrame to CSV
            csv = df.to_csv(index=False, encoding="utf-8-sig")

            st.download_button(
                label=f"📥 ดาวน์โหลด {filename}",
                data=csv,
                file_name=filename,
                mime="text/csv",
            )

            st.success(f"✅ เตรียมไฟล์ {filename} เรียบร้อยแล้ว")

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            st.error("เกิดข้อผิดพลาดในการส่งออกรายงาน")
