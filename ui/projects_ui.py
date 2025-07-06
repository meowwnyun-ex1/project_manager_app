#!/usr/bin/env python3
"""
projects_ui.py
SDX Project Manager - Complete Enterprise Project Management Interface
Advanced project management UI with Gantt charts, analytics, and real-time collaboration
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import logging
import json

# Import project modules
from projects import ProjectManager
from tasks import TaskManager, TaskStatus, TaskPriority
from analytics import AnalyticsManager
from ui_components import UIComponents, ThemeManager
from error_handler import ErrorHandler, handle_errors

logger = logging.getLogger(__name__)


class ProjectsUI:
    """Complete Enterprise Project Management Interface"""

    def __init__(self, db_manager, theme_manager: ThemeManager):
        self.db = db_manager
        self.project_manager = ProjectManager(db_manager)
        self.task_manager = TaskManager(db_manager)
        self.analytics_manager = AnalyticsManager(db_manager)
        self.theme = theme_manager
        self.ui_components = UIComponents(theme_manager)
        self.error_handler = ErrorHandler()

    @handle_errors
    def render_projects_management(self):
        """Main projects management interface with comprehensive features"""
        st.markdown("# 🎯 จัดการโครงการ")

        # Header with quick actions
        self._render_header_actions()

        # Navigation tabs with advanced features
        tabs = st.tabs(
            [
                "📊 Dashboard",
                "📋 รายการโครงการ",
                "📈 Gantt Chart",
                "📅 Timeline",
                "💰 งบประมาณ",
                "👥 ทีม",
                "📋 รายงาน",
            ]
        )

        with tabs[0]:  # Dashboard
            self._render_projects_dashboard()

        with tabs[1]:  # Project List
            self._render_projects_list_advanced()

        with tabs[2]:  # Gantt Chart
            self._render_advanced_gantt_chart()

        with tabs[3]:  # Timeline
            self._render_project_timeline()

        with tabs[4]:  # Budget
            self._render_budget_management()

        with tabs[5]:  # Team
            self._render_team_management()

        with tabs[6]:  # Reports
            self._render_executive_reports()

    def _render_header_actions(self):
        """Render header with quick actions and search"""
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            # Global project search
            search_term = st.text_input(
                "🔍 ค้นหาโครงการ",
                placeholder="ชื่อโครงการ, รหัส, หรือคีย์เวิร์ด...",
                key="global_project_search",
            )

            if search_term:
                self._show_search_results(search_term)

        with col2:
            if st.button("➕ โครงการใหม่", type="primary", use_container_width=True):
                self._show_create_project_dialog()

        with col3:
            if st.button("📊 Analytics", type="secondary", use_container_width=True):
                self._show_analytics_modal()

        with col4:
            # Export/Import options
            with st.popover("⚙️ เครื่องมือ"):
                if st.button("📥 Import Projects"):
                    self._show_import_dialog()
                if st.button("📤 Export Data"):
                    self._export_projects_data()
                if st.button("🔄 Sync External"):
                    self._sync_external_systems()

        st.markdown("---")

    def _render_projects_dashboard(self):
        """Comprehensive projects dashboard with real-time metrics"""
        # KPI Overview
        self._render_kpi_overview()

        # Main dashboard content
        col_left, col_right = st.columns([2, 1])

        with col_left:
            # Project health overview
            st.markdown("### 📈 Project Health Overview")
            self._render_project_health_matrix()

            # Recent activities
            st.markdown("### 🔔 กิจกรรมล่าสุด")
            self._render_activity_feed()

        with col_right:
            # Quick stats
            self._render_quick_stats()

            # Upcoming deadlines
            st.markdown("### ⏰ Deadlines ที่ใกล้มา")
            self._render_upcoming_deadlines()

            # Resource allocation
            st.markdown("### 👥 การใช้ทรัพยากร")
            self._render_resource_allocation()

    def _render_kpi_overview(self):
        """Render comprehensive KPI cards"""
        try:
            # Get metrics from analytics
            metrics = self.analytics_manager.get_project_overview_metrics()

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric(
                    label="📊 โครงการทั้งหมด",
                    value=metrics.get("total_projects", 0),
                    delta=f"+{metrics.get('new_projects_this_month', 0)} เดือนนี้",
                )

            with col2:
                active_projects = metrics.get("active_projects", 0)
                total_projects = metrics.get("total_projects", 1)
                st.metric(
                    label="🔄 กำลังดำเนินการ",
                    value=active_projects,
                    delta=f"{(active_projects/total_projects*100):.1f}%",
                )

            with col3:
                completion_rate = metrics.get("completion_rate", 0)
                st.metric(
                    label="✅ อัตราสำเร็จ",
                    value=f"{completion_rate:.1f}%",
                    delta=f"{metrics.get('completion_rate_change', 0):+.1f}%",
                )

            with col4:
                budget_usage = metrics.get("budget_utilization", 0)
                st.metric(
                    label="💰 การใช้งบประมาณ",
                    value=f"{budget_usage:.1f}%",
                    delta=f"{metrics.get('budget_variance', 0):+.1f}%",
                    delta_color="inverse",
                )

            with col5:
                team_utilization = metrics.get("team_utilization", 0)
                st.metric(
                    label="👥 Utilization",
                    value=f"{team_utilization:.1f}%",
                    delta=f"{metrics.get('utilization_trend', 0):+.1f}%",
                )

        except Exception as e:
            logger.error(f"Error rendering KPI overview: {e}")
            st.error("ไม่สามารถโหลดข้อมูล KPI ได้")

    def _render_projects_list_advanced(self):
        """Advanced project list with filtering, sorting, and bulk actions"""
        # Advanced filters
        self._render_advanced_filters()

        # Bulk actions bar
        selected_projects = self._render_bulk_actions()

        # Projects table/grid view
        view_mode = st.radio(
            "มุมมอง", ["📊 การ์ด", "📋 ตาราง", "📈 Kanban"], horizontal=True
        )

        if view_mode == "📊 การ์ด":
            self._render_projects_card_view(selected_projects)
        elif view_mode == "📋 ตาราง":
            self._render_projects_table_view(selected_projects)
        else:
            self._render_projects_kanban_view()

    def _render_advanced_filters(self):
        """Render advanced filtering options"""
        with st.expander("🔍 ตัวกรองขั้นสูง", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                status_filter = st.multiselect(
                    "สถานะ",
                    options=["Planning", "Active", "On Hold", "Completed", "Cancelled"],
                    default=["Planning", "Active"],
                    key="project_status_filter",
                )

            with col2:
                priority_filter = st.multiselect(
                    "ความสำคัญ",
                    options=["Low", "Medium", "High", "Critical"],
                    key="project_priority_filter",
                )

            with col3:
                # Date range filter
                date_range = st.selectbox(
                    "ช่วงเวลา",
                    options=["ทั้งหมด", "30 วันล่าสุด", "ไตรมาสนี้", "ปีนี้", "กำหนดเอง"],
                    key="project_date_filter",
                )

            with col4:
                # Team filter
                team_filter = st.selectbox(
                    "ทีม",
                    options=["ทั้งหมด", "ทีมของฉัน", "ไม่มีผู้จัดการ"],
                    key="project_team_filter",
                )

            # Additional filters row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                budget_range = st.slider(
                    "งบประมาณ (ล้านบาท)",
                    min_value=0.0,
                    max_value=100.0,
                    value=(0.0, 100.0),
                    key="project_budget_filter",
                )

            with col2:
                health_filter = st.selectbox(
                    "สุขภาพโครงการ",
                    options=["ทั้งหมด", "ดีเยี่ยม", "ปกติ", "เสี่ยง", "วิกฤต"],
                    key="project_health_filter",
                )

            with col3:
                completion_filter = st.slider(
                    "ความคืบหน้า (%)",
                    min_value=0,
                    max_value=100,
                    value=(0, 100),
                    key="project_completion_filter",
                )

            with col4:
                tags_filter = st.text_input(
                    "Tags", placeholder="แยกด้วย comma", key="project_tags_filter"
                )

        # Apply filters button
        if st.button("🔍 ใช้ตัวกรอง", type="primary"):
            st.session_state.apply_filters = True
            st.rerun()

    def _render_bulk_actions(self) -> List[int]:
        """Render bulk actions bar and return selected project IDs"""
        if "selected_projects" not in st.session_state:
            st.session_state.selected_projects = []

        if st.session_state.selected_projects:
            selected_count = len(st.session_state.selected_projects)

            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

            with col1:
                st.info(f"เลือกแล้ว {selected_count} โครงการ")

            with col2:
                if st.button("📊 สร้างรายงาน"):
                    self._bulk_generate_reports()

            with col3:
                if st.button("🏷️ เพิ่ม Tags"):
                    self._bulk_add_tags()

            with col4:
                if st.button("👥 มอบหมาย"):
                    self._bulk_assign_manager()

            with col5:
                if st.button("❌ ยกเลิกเลือก"):
                    st.session_state.selected_projects = []
                    st.rerun()

            st.markdown("---")

        return st.session_state.selected_projects

    def _render_projects_card_view(self, selected_projects: List[int]):
        """Render projects in card view format"""
        try:
            projects = self._get_filtered_projects()

            if not projects:
                st.info("🔍 ไม่พบโครงการที่ตรงกับเงื่อนไข")
                return

            # Render projects in grid
            cols_per_row = 3
            for i in range(0, len(projects), cols_per_row):
                cols = st.columns(cols_per_row)

                for j, col in enumerate(cols):
                    if i + j < len(projects):
                        project = projects[i + j]
                        with col:
                            self._render_project_card(project, selected_projects)

        except Exception as e:
            logger.error(f"Error rendering projects card view: {e}")
            st.error("ไม่สามารถแสดงโครงการได้")

    def _render_project_card(
        self, project: Dict[str, Any], selected_projects: List[int]
    ):
        """Render individual project card"""
        try:
            project_id = project["id"]
            is_selected = project_id in selected_projects

            # Card container with selection highlight
            card_style = (
                "border: 2px solid #0066CC;"
                if is_selected
                else "border: 1px solid #ddd;"
            )

            with st.container():
                # Selection checkbox
                col1, col2 = st.columns([1, 10])

                with col1:
                    selected = st.checkbox(
                        "", value=is_selected, key=f"select_project_{project_id}"
                    )
                    if selected and project_id not in selected_projects:
                        st.session_state.selected_projects.append(project_id)
                        st.rerun()
                    elif not selected and project_id in selected_projects:
                        st.session_state.selected_projects.remove(project_id)
                        st.rerun()

                with col2:
                    # Project header
                    status_color = self._get_status_color(project.get("status"))
                    health_icon = self._get_health_icon(project.get("health_score", 75))

                    st.markdown(
                        f"""
                    <div style="{card_style} border-radius: 8px; padding: 16px; margin: 8px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #333;">{project.get('name', 'ไม่มีชื่อ')}</h4>
                            <span style="background: {status_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em;">
                                {project.get('status', 'Unknown')}
                            </span>
                        </div>
                        <p style="color: #666; margin: 8px 0;">{project.get('description', 'ไม่มีคำอธิบาย')[:100]}...</p>
                        <div style="margin: 12px 0;">
                            <div style="background: #f0f0f0; border-radius: 4px; height: 8px;">
                                <div style="background: #4CAF50; border-radius: 4px; height: 8px; width: {project.get('progress', 0)}%;"></div>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.85em;">
                                <span>ความคืบหน้า: {project.get('progress', 0):.1f}%</span>
                                <span>{health_icon} Health</span>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                            <div>
                                <div style="font-size: 0.85em; color: #666;">
                                    👤 {project.get('manager_name', 'ไม่ระบุ')}
                                </div>
                                <div style="font-size: 0.85em; color: #666;">
                                    📅 {project.get('end_date', 'ไม่กำหนด')}
                                </div>
                            </div>
                            <div style="font-size: 0.9em; font-weight: bold; color: #333;">
                                ฿{project.get('budget', 0):,.0f}
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Action buttons
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button(
                            "👁️ ดู", key=f"view_{project_id}", use_container_width=True
                        ):
                            self._show_project_details(project_id)

                    with col2:
                        if st.button(
                            "✏️ แก้ไข", key=f"edit_{project_id}", use_container_width=True
                        ):
                            self._show_edit_project_dialog(project_id)

                    with col3:
                        if st.button(
                            "📊 งาน",
                            key=f"tasks_{project_id}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_project_for_tasks = project_id
                            st.switch_page("tasks")

        except Exception as e:
            logger.error(f"Error rendering project card: {e}")

    def _render_advanced_gantt_chart(self):
        """Render advanced Gantt chart with dependencies and milestones"""
        st.markdown("### 📈 Gantt Chart - ไทม์ไลน์โครงการขั้นสูง")

        # Gantt chart controls
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            projects = self._get_all_projects()
            if not projects:
                st.warning("ไม่มีโครงการในระบบ")
                return

            selected_projects = st.multiselect(
                "เลือกโครงการ",
                options=[p["id"] for p in projects],
                format_func=lambda x: next(p["name"] for p in projects if p["id"] == x),
                default=[p["id"] for p in projects[:5]],  # Default first 5
                key="gantt_project_selection",
            )

        with col2:
            view_level = st.selectbox(
                "ระดับการแสดง",
                options=["โครงการ", "โครงการ + Milestone", "โครงการ + งาน", "ทั้งหมด"],
                key="gantt_view_level",
            )

        with col3:
            time_range = st.selectbox(
                "ช่วงเวลา",
                options=["6 เดือน", "1 ปี", "2 ปี", "ทั้งหมด"],
                key="gantt_time_range",
            )

        with col4:
            show_dependencies = st.checkbox(
                "แสดง Dependencies", value=True, key="gantt_show_dependencies"
            )

        try:
            if selected_projects:
                # Generate Gantt chart data
                gantt_data = self._prepare_gantt_data(
                    selected_projects, view_level, show_dependencies
                )

                if gantt_data:
                    # Create interactive Gantt chart
                    fig = self._create_advanced_gantt_chart(
                        gantt_data, show_dependencies
                    )
                    st.plotly_chart(
                        fig, use_container_width=True, config={"displayModeBar": True}
                    )

                    # Chart legend and controls
                    self._render_gantt_legend()

                    # Export options
                    if st.button("📥 ส่งออก Gantt Chart"):
                        self._export_gantt_chart(fig)
                else:
                    st.info("ไม่มีข้อมูลสำหรับสร้าง Gantt Chart")

        except Exception as e:
            logger.error(f"Error rendering Gantt chart: {e}")
            st.error("ไม่สามารถแสดง Gantt Chart ได้")

    def _create_advanced_gantt_chart(
        self, gantt_data: List[Dict], show_dependencies: bool
    ) -> go.Figure:
        """Create advanced Gantt chart with modern styling"""
        try:
            df = pd.DataFrame(gantt_data)

            # Create Gantt chart using plotly figure_factory
            fig = ff.create_gantt(
                df,
                colors=self._get_gantt_colors(),
                index_col="Resource",
                title="Project Gantt Chart - SDX Project Manager",
                show_colorbar=True,
                bar_width=0.3,
                showgrid_x=True,
                showgrid_y=True,
                height=max(400, len(df) * 30),
            )

            # Enhance styling
            fig.update_layout(
                title={
                    "text": "Project Timeline & Dependencies",
                    "x": 0.5,
                    "xanchor": "center",
                    "font": {"size": 20},
                },
                xaxis={
                    "title": "Timeline",
                    "showgrid": True,
                    "gridcolor": "lightgray",
                    "type": "date",
                },
                yaxis={
                    "title": "Projects & Tasks",
                    "showgrid": True,
                    "gridcolor": "lightgray",
                },
                plot_bgcolor="white",
                height=max(500, len(df) * 35),
                margin=dict(l=200, r=50, t=80, b=50),
            )

            # Add milestones if present
            self._add_milestones_to_gantt(fig, gantt_data)

            # Add dependency arrows if enabled
            if show_dependencies:
                self._add_dependency_arrows(fig, gantt_data)

            return fig

        except Exception as e:
            logger.error(f"Error creating Gantt chart: {e}")
            # Return empty figure as fallback
            return go.Figure()

    def _render_budget_management(self):
        """Render comprehensive budget management interface"""
        st.markdown("### 💰 การจัดการงบประมาณ")

        # Budget overview
        col1, col2, col3, col4 = st.columns(4)

        try:
            budget_metrics = self.analytics_manager.get_budget_metrics()

            with col1:
                st.metric(
                    "💼 งบประมาณรวม",
                    f"฿{budget_metrics.get('total_budget', 0):,.0f}",
                    f"{budget_metrics.get('budget_growth', 0):+.1f}%",
                )

            with col2:
                st.metric(
                    "💸 ใช้ไปแล้ว",
                    f"฿{budget_metrics.get('spent_amount', 0):,.0f}",
                    f"{budget_metrics.get('spent_percentage', 0):.1f}%",
                )

            with col3:
                st.metric(
                    "💳 คงเหลือ",
                    f"฿{budget_metrics.get('remaining_amount', 0):,.0f}",
                    f"{budget_metrics.get('burn_rate', 0):+.1f}% Burn Rate",
                )

            with col4:
                variance = budget_metrics.get("budget_variance", 0)
                st.metric(
                    "📊 Variance",
                    f"{variance:+.1f}%",
                    "ตามแผน" if abs(variance) < 5 else "เกินแผน",
                    delta_color="inverse" if variance > 10 else "normal",
                )

        except Exception as e:
            logger.error(f"Error getting budget metrics: {e}")
            st.error("ไม่สามารถโหลดข้อมูลงบประมาณได้")

        # Budget charts
        col_left, col_right = st.columns(2)

        with col_left:
            self._render_budget_allocation_chart()

        with col_right:
            self._render_budget_burn_rate_chart()

        # Detailed budget table
        st.markdown("#### 📋 รายละเอียดงบประมาณแต่ละโครงการ")
        self._render_detailed_budget_table()

    def _render_team_management(self):
        """Render team management and resource allocation"""
        st.markdown("### 👥 การจัดการทีมและทรัพยากร")

        # Team overview metrics
        col1, col2, col3, col4 = st.columns(4)

        try:
            team_metrics = self.analytics_manager.get_team_metrics()

            with col1:
                st.metric(
                    "👥 สมาชิกทีม",
                    team_metrics.get("total_members", 0),
                    f"+{team_metrics.get('new_members', 0)} คนใหม่",
                )

            with col2:
                utilization = team_metrics.get("average_utilization", 0)
                st.metric(
                    "⚡ Utilization",
                    f"{utilization:.1f}%",
                    f"{team_metrics.get('utilization_trend', 0):+.1f}%",
                )

            with col3:
                st.metric(
                    "🎯 Productivity",
                    f"{team_metrics.get('productivity_score', 0):.1f}",
                    f"{team_metrics.get('productivity_change', 0):+.1f}",
                )

            with col4:
                st.metric(
                    "📊 Active Projects",
                    team_metrics.get("projects_per_member", 0),
                    "โครงการ/คน",
                )

        except Exception as e:
            logger.error(f"Error getting team metrics: {e}")
            st.error("ไม่สามารถโหลดข้อมูลทีมได้")

        # Team allocation and workload
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 📊 การกระจายทีม")
            self._render_team_allocation_chart()

        with col_right:
            st.markdown("#### ⚡ ภาระงาน")
            self._render_workload_distribution()

        # Team performance table
        st.markdown("#### 📋 ประสิทธิภาพทีม")
        self._render_team_performance_table()

    def _render_executive_reports(self):
        """Render executive-level reports and analytics"""
        st.markdown("### 📋 รายงานผู้บริหาร")

        # Report configuration
        col1, col2, col3 = st.columns(3)

        with col1:
            report_type = st.selectbox(
                "ประเภทรายงาน",
                options=[
                    "Executive Summary",
                    "Project Portfolio",
                    "Budget Analysis",
                    "Resource Utilization",
                    "Performance Metrics",
                    "Risk Assessment",
                ],
                key="executive_report_type",
            )

        with col2:
            report_period = st.selectbox(
                "ช่วงเวลา",
                options=["เดือนนี้", "ไตรมาสนี้", "ปีนี้", "กำหนดเอง"],
                key="executive_report_period",
            )

        with col3:
            report_format = st.selectbox(
                "รูปแบบ",
                options=["Interactive", "PDF Export", "PowerPoint", "Excel"],
                key="executive_report_format",
            )

        # Generate report button
        if st.button("📊 สร้างรายงาน", type="primary"):
            with st.spinner("กำลังสร้างรายงาน..."):
                self._generate_executive_report(
                    report_type, report_period, report_format
                )

        # Pre-built dashboard for quick insights
        st.markdown("#### 📊 Dashboard สำหรับผู้บริหาร")

        # Executive KPIs
        self._render_executive_kpis()

        # Strategic charts
        col1, col2 = st.columns(2)

        with col1:
            self._render_project_portfolio_matrix()

        with col2:
            self._render_strategic_initiatives_progress()

    # Helper Methods
    def _get_filtered_projects(self) -> List[Dict[str, Any]]:
        """Get projects based on current filters"""
        try:
            # Get filter values from session state
            status_filter = st.session_state.get("project_status_filter", [])
            priority_filter = st.session_state.get("project_priority_filter", [])
            # Add more filters as needed

            filters = {}
            if status_filter:
                filters["status"] = status_filter
            if priority_filter:
                filters["priority"] = priority_filter

            return self.project_manager.get_projects_with_filters(filters)

        except Exception as e:
            logger.error(f"Error getting filtered projects: {e}")
            return []

    def _get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from the database"""
        try:
            return self.project_manager.get_all_projects()
        except Exception as e:
            logger.error(f"Error getting all projects: {e}")
            return []

    def _get_status_color(self, status: str) -> str:
        """Get color code for project status"""
        color_map = {
            "Planning": "#FFA500",
            "Active": "#4CAF50",
            "On Hold": "#FF5722",
            "Completed": "#2196F3",
            "Cancelled": "#9E9E9E",
        }
        return color_map.get(status, "#666666")

    def _get_health_icon(self, health_score: float) -> str:
        """Get health icon based on score"""
        if health_score >= 80:
            return "🟢"
        elif health_score >= 60:
            return "🟡"
        else:
            return "🔴"

    def _show_search_results(self, search_term: str):
        """Show search results in expandable section"""
        try:
            results = self.project_manager.search_projects(search_term)

            if results:
                with st.expander(
                    f"🔍 ผลการค้นหา ({len(results)} โครงการ)", expanded=True
                ):
                    for project in results[:5]:  # Show top 5 results
                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            st.write(f"**{project['name']}**")
                            st.caption(
                                f"สถานะ: {project['status']} | ความคืบหน้า: {project.get('progress', 0):.1f}%"
                            )

                        with col2:
                            if st.button("ดู", key=f"search_view_{project['id']}"):
                                self._show_project_details(project["id"])

                        with col3:
                            if st.button("แก้ไข", key=f"search_edit_{project['id']}"):
                                self._show_edit_project_dialog(project["id"])

        except Exception as e:
            logger.error(f"Error showing search results: {e}")

    def _show_create_project_dialog(self):
        """Show comprehensive project creation dialog"""
        with st.expander("➕ สร้างโครงการใหม่", expanded=True):
            with st.form("create_project_form", clear_on_submit=True):
                # Basic information
                st.markdown("#### 📋 ข้อมูลพื้นฐาน")
                col1, col2 = st.columns(2)

                with col1:
                    project_name = st.text_input("ชื่อโครงการ *", max_chars=255)
                    project_code = st.text_input("รหัสโครงการ", max_chars=50)
                    priority = st.selectbox(
                        "ความสำคัญ", options=["Low", "Medium", "High", "Critical"]
                    )

                with col2:
                    project_type = st.selectbox(
                        "ประเภทโครงการ",
                        options=[
                            "Software Development",
                            "Infrastructure",
                            "Research",
                            "Marketing",
                            "Other",
                        ],
                    )
                    department = st.selectbox(
                        "แผนก",
                        options=[
                            "IT",
                            "Engineering",
                            "Marketing",
                            "Finance",
                            "Operations",
                        ],
                    )
                    category = st.selectbox(
                        "หมวดหมู่",
                        options=["Internal", "External", "Customer", "Partner"],
                    )

                description = st.text_area("คำอธิบายโครงการ", height=100)

                # Timeline and budget
                st.markdown("#### 📅 กำหนดการและงบประมาณ")
                col1, col2, col3 = st.columns(3)

                with col1:
                    start_date = st.date_input("วันที่เริ่ม *", value=datetime.now().date())

                with col2:
                    end_date = st.date_input(
                        "วันที่สิ้นสุด *", value=datetime.now().date() + timedelta(days=30)
                    )

                with col3:
                    budget = st.number_input(
                        "งบประมาณ (บาท)", min_value=0, value=0, step=1000
                    )

                # Team assignment
                st.markdown("#### 👥 การมอบหมายทีม")
                col1, col2 = st.columns(2)

                with col1:
                    # In real implementation, this would load from users table
                    manager_options = {
                        "ไม่ระบุ": None,
                        "ฉัน": st.session_state.get("user", {}).get("id"),
                    }
                    manager_name = st.selectbox(
                        "ผู้จัดการโครงการ", options=list(manager_options.keys())
                    )
                    manager_id = manager_options[manager_name]

                with col2:
                    # Team members selection (multi-select)
                    team_members = st.multiselect(
                        "สมาชิกทีม",
                        options=["สมชาย ใจดี", "วิภา สมใจ", "จิรายุ เดชา", "นภา พรสวรรค์"],
                        help="เลือกสมาชิกทีมที่จะเข้าร่วมโครงการ",
                    )

                # Advanced settings
                with st.expander("⚙️ การตั้งค่าขั้นสูง", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        risk_level = st.selectbox(
                            "ระดับความเสี่ยง", options=["Low", "Medium", "High"]
                        )
                        visibility = st.selectbox(
                            "การมองเห็น", options=["Public", "Internal", "Private"]
                        )

                    with col2:
                        methodology = st.selectbox(
                            "Methodology",
                            options=["Agile", "Waterfall", "Hybrid", "Kanban"],
                        )
                        auto_notifications = st.checkbox("แจ้งเตือนอัตโนมัติ", value=True)

                # Tags and labels
                tags = st.text_input(
                    "Tags",
                    placeholder="แยกด้วย comma เช่น urgent, mobile, api",
                    help="Tags สำหรับการจัดหมวดหมู่และค้นหา",
                )

                # Custom fields
                with st.expander("📝 ฟิลด์เพิ่มเติม", expanded=False):
                    client_name = st.text_input("ชื่อลูกค้า/หน่วยงาน")
                    external_id = st.text_input("รหัสอ้างอิงภายนอก")

                # Submit button
                submitted = st.form_submit_button("🚀 สร้างโครงการ", type="primary")

                if submitted:
                    if self._validate_project_form(project_name, start_date, end_date):
                        project_data = {
                            "name": project_name,
                            "code": project_code,
                            "description": description,
                            "project_type": project_type,
                            "priority": priority,
                            "department": department,
                            "category": category,
                            "start_date": start_date,
                            "end_date": end_date,
                            "budget": budget,
                            "manager_id": manager_id,
                            "risk_level": risk_level,
                            "visibility": visibility,
                            "methodology": methodology,
                            "tags": tags,
                            "custom_fields": {
                                "client_name": client_name,
                                "external_id": external_id,
                                "auto_notifications": auto_notifications,
                            },
                            "status": "Planning",
                            "created_by": st.session_state.get("user", {}).get("id"),
                        }

                        if self._create_new_project(project_data, team_members):
                            st.success("✅ สร้างโครงการเรียบร้อยแล้ว")
                            st.rerun()
                        else:
                            st.error("❌ ไม่สามารถสร้างโครงการได้")

    def _validate_project_form(
        self, name: str, start_date: date, end_date: date
    ) -> bool:
        """Validate project form data"""
        if not name or len(name.strip()) < 3:
            st.error("❌ ชื่อโครงการต้องมีความยาวอย่างน้อย 3 ตัวอักษร")
            return False

        if start_date >= end_date:
            st.error("❌ วันที่สิ้นสุดต้องมาหลังวันที่เริ่ม")
            return False

        if end_date < datetime.now().date():
            st.error("❌ วันที่สิ้นสุดต้องเป็นอนาคต")
            return False

        return True

    def _create_new_project(
        self, project_data: Dict[str, Any], team_members: List[str]
    ) -> bool:
        """Create new project with team assignment"""
        try:
            project_id = self.project_manager.create_project(project_data)

            if project_id:
                # Add team members (in real implementation, would use user IDs)
                # self.project_manager.add_team_members(project_id, team_member_ids)

                # Create initial project structure
                self._setup_initial_project_structure(project_id)

                return True

            return False

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return False

    def _setup_initial_project_structure(self, project_id: int):
        """Setup initial project structure (milestones, default tasks, etc.)"""
        try:
            # Create default milestones
            default_milestones = [
                {
                    "name": "Project Kickoff",
                    "date": datetime.now().date() + timedelta(days=7),
                },
                {
                    "name": "Phase 1 Complete",
                    "date": datetime.now().date() + timedelta(days=30),
                },
                {
                    "name": "Project Delivery",
                    "date": datetime.now().date() + timedelta(days=90),
                },
            ]

            for milestone in default_milestones:
                # In real implementation, create milestone records
                pass

        except Exception as e:
            logger.error(f"Error setting up project structure: {e}")

    def _render_project_health_matrix(self):
        """Render project health matrix visualization"""
        try:
            projects = self._get_all_projects()

            if not projects:
                st.info("ไม่มีข้อมูลโครงการ")
                return

            # Prepare data for health matrix
            health_data = []
            for project in projects:
                health_score = project.get("health_score", 75)
                budget_utilization = project.get("budget_utilization", 50)

                health_data.append(
                    {
                        "name": project["name"],
                        "health": health_score,
                        "budget": budget_utilization,
                        "status": project.get("status", "Unknown"),
                        "progress": project.get("progress", 0),
                    }
                )

            df = pd.DataFrame(health_data)

            # Create scatter plot for health matrix
            fig = px.scatter(
                df,
                x="budget",
                y="health",
                size="progress",
                color="status",
                hover_name="name",
                title="Project Health vs Budget Utilization",
                labels={
                    "budget": "Budget Utilization (%)",
                    "health": "Health Score",
                    "progress": "Progress (%)",
                },
            )

            # Add quadrant lines
            fig.add_hline(y=70, line_dash="dash", line_color="gray", opacity=0.5)
            fig.add_vline(x=80, line_dash="dash", line_color="gray", opacity=0.5)

            # Add quadrant labels
            fig.add_annotation(
                x=40,
                y=85,
                text="Healthy & On Budget",
                showarrow=False,
                bgcolor="lightgreen",
                opacity=0.7,
            )
            fig.add_annotation(
                x=90,
                y=85,
                text="Healthy but Over Budget",
                showarrow=False,
                bgcolor="lightyellow",
                opacity=0.7,
            )
            fig.add_annotation(
                x=40,
                y=55,
                text="At Risk & On Budget",
                showarrow=False,
                bgcolor="lightcoral",
                opacity=0.7,
            )
            fig.add_annotation(
                x=90,
                y=55,
                text="At Risk & Over Budget",
                showarrow=False,
                bgcolor="red",
                opacity=0.7,
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            logger.error(f"Error rendering health matrix: {e}")
            st.error("ไม่สามารถแสดงตารางสุขภาพโครงการได้")

    def _render_activity_feed(self):
        """Render recent project activities"""
        try:
            activities = self.analytics_manager.get_recent_project_activities(limit=10)

            if activities:
                for activity in activities:
                    with st.container():
                        col1, col2 = st.columns([1, 6])

                        with col1:
                            icon = self._get_activity_icon(activity.get("type"))
                            st.markdown(
                                f"<div style='font-size: 1.5em; text-align: center;'>{icon}</div>",
                                unsafe_allow_html=True,
                            )

                        with col2:
                            st.write(f"**{activity.get('title')}**")
                            st.caption(f"{activity.get('description')}")
                            st.caption(
                                f"⏰ {activity.get('timestamp')} • 👤 {activity.get('user')}"
                            )

                        st.markdown("---")
            else:
                st.info("ไม่มีกิจกรรมล่าสุด")

        except Exception as e:
            logger.error(f"Error rendering activity feed: {e}")

    def _get_activity_icon(self, activity_type: str) -> str:
        """Get icon for activity type"""
        icons = {
            "project_created": "🎯",
            "project_updated": "✏️",
            "milestone_completed": "🏆",
            "task_completed": "✅",
            "team_member_added": "👥",
            "budget_updated": "💰",
            "status_changed": "🔄",
            "file_uploaded": "📎",
        }
        return icons.get(activity_type, "📝")

    def _render_quick_stats(self):
        """Render quick statistics widget"""
        try:
            stats = self.analytics_manager.get_quick_project_stats()

            st.markdown("### 📊 สถิติด่วน")

            # Projects by status
            st.markdown("#### สถานะโครงการ")
            for status, count in stats.get("status_distribution", {}).items():
                color = self._get_status_color(status)
                percentage = (count / stats.get("total_projects", 1)) * 100

                st.markdown(
                    f"""
                <div style="display: flex; justify-content: space-between; margin: 4px 0;">
                    <span style="color: {color};">● {status}</span>
                    <span>{count} ({percentage:.1f}%)</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Budget overview
            st.markdown("#### งบประมาณ")
            total_budget = stats.get("total_budget", 0)
            spent_budget = stats.get("spent_budget", 0)

            if total_budget > 0:
                spent_percentage = (spent_budget / total_budget) * 100
                st.progress(spent_percentage / 100)
                st.caption(
                    f"ใช้ไป ฿{spent_budget:,.0f} จาก ฿{total_budget:,.0f} ({spent_percentage:.1f}%)"
                )

        except Exception as e:
            logger.error(f"Error rendering quick stats: {e}")

    def _render_upcoming_deadlines(self):
        """Render upcoming project deadlines"""
        try:
            deadlines = self.project_manager.get_upcoming_deadlines(days_ahead=30)

            if deadlines:
                for deadline in deadlines[:5]:  # Show top 5
                    days_remaining = (deadline["due_date"] - datetime.now().date()).days

                    # Color based on urgency
                    if days_remaining <= 3:
                        color = "🔴"
                    elif days_remaining <= 7:
                        color = "🟡"
                    else:
                        color = "🟢"

                    st.markdown(
                        f"""
                    <div style="padding: 8px; border-left: 3px solid #ddd; margin: 8px 0;">
                        <div style="font-weight: bold;">{color} {deadline['name']}</div>
                        <div style="font-size: 0.9em; color: #666;">
                            📅 {deadline['due_date']} ({days_remaining} วัน)
                        </div>
                        <div style="font-size: 0.85em; color: #888;">
                            ความคืบหน้า: {deadline.get('progress', 0):.1f}%
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("ไม่มี deadline ที่ใกล้มา")

        except Exception as e:
            logger.error(f"Error rendering upcoming deadlines: {e}")

    def _render_resource_allocation(self):
        """Render resource allocation chart"""
        try:
            allocation_data = self.analytics_manager.get_resource_allocation()

            if allocation_data:
                # Create simple pie chart for resource allocation
                labels = list(allocation_data.keys())
                values = list(allocation_data.values())

                fig = px.pie(values=values, names=labels, title="การใช้ทรัพยากร")

                fig.update_traces(textposition="inside", textinfo="percent")
                fig.update_layout(height=300, showlegend=True)

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลการใช้ทรัพยากร")

        except Exception as e:
            logger.error(f"Error rendering resource allocation: {e}")

    # Placeholder methods for advanced features
    def _show_project_details(self, project_id: int):
        """Show detailed project information modal"""
        st.info(f"🚧 รายละเอียดโครงการ ID: {project_id} - กำลังพัฒนา")

    def _show_edit_project_dialog(self, project_id: int):
        """Show project editing dialog"""
        st.info(f"🚧 แก้ไขโครงการ ID: {project_id} - กำลังพัฒนา")

    def _show_analytics_modal(self):
        """Show analytics modal"""
        st.info("🚧 Analytics Modal - กำลังพัฒนา")

    def _show_import_dialog(self):
        """Show import projects dialog"""
        st.info("🚧 Import Projects - กำลังพัฒนา")

    def _export_projects_data(self):
        """Export projects data"""
        st.success("🚧 Export ข้อมูล - กำลังพัฒนา")

    def _sync_external_systems(self):
        """Sync with external systems"""
        st.info("🚧 Sync External Systems - กำลังพัฒนา")

    def _bulk_generate_reports(self):
        """Generate reports for selected projects"""
        st.info("🚧 Bulk Report Generation - กำลังพัฒนา")

    def _bulk_add_tags(self):
        """Add tags to selected projects"""
        st.info("🚧 Bulk Add Tags - กำลังพัฒนา")

    def _bulk_assign_manager(self):
        """Assign manager to selected projects"""
        st.info("🚧 Bulk Assign Manager - กำลังพัฒนา")

    def _render_projects_table_view(self, selected_projects: List[int]):
        """Render projects in table format"""
        st.info("🚧 Table View - กำลังพัฒนา")

    def _render_projects_kanban_view(self):
        """Render projects in Kanban format"""
        st.info("🚧 Kanban View - กำลังพัฒนา")

    def _prepare_gantt_data(
        self, project_ids: List[int], view_level: str, show_deps: bool
    ) -> List[Dict]:
        """Prepare data for Gantt chart"""
        # Placeholder implementation
        return []

    def _get_gantt_colors(self) -> Dict[str, str]:
        """Get color mapping for Gantt chart"""
        return {
            "Planning": "#FFA500",
            "Active": "#4CAF50",
            "On Hold": "#FF5722",
            "Completed": "#2196F3",
        }

    def _add_milestones_to_gantt(self, fig: go.Figure, data: List[Dict]):
        """Add milestones to Gantt chart"""
        pass

    def _add_dependency_arrows(self, fig: go.Figure, data: List[Dict]):
        """Add dependency arrows to Gantt chart"""
        pass

    def _render_gantt_legend(self):
        """Render Gantt chart legend"""
        st.info("🚧 Gantt Legend - กำลังพัฒนา")

    def _export_gantt_chart(self, fig: go.Figure):
        """Export Gantt chart"""
        st.success("🚧 Export Gantt - กำลังพัฒนา")

    def _render_project_timeline(self):
        """Render project timeline view"""
        st.info("🚧 Project Timeline - กำลังพัฒนา")

    def _render_budget_allocation_chart(self):
        """Render budget allocation chart"""
        st.info("🚧 Budget Allocation Chart - กำลังพัฒนา")

    def _render_budget_burn_rate_chart(self):
        """Render budget burn rate chart"""
        st.info("🚧 Budget Burn Rate - กำลังพัฒนา")

    def _render_detailed_budget_table(self):
        """Render detailed budget table"""
        st.info("🚧 Detailed Budget Table - กำลังพัฒนา")

    def _render_team_allocation_chart(self):
        """Render team allocation chart"""
        st.info("🚧 Team Allocation Chart - กำลังพัฒนา")

    def _render_workload_distribution(self):
        """Render workload distribution"""
        st.info("🚧 Workload Distribution - กำลังพัฒนา")

    def _render_team_performance_table(self):
        """Render team performance table"""
        st.info("🚧 Team Performance Table - กำลังพัฒนา")

    def _generate_executive_report(self, report_type: str, period: str, format: str):
        """Generate executive report"""
        st.success(f"🚧 สร้างรายงาน {report_type} ({format}) - กำลังพัฒนา")

    def _render_executive_kpis(self):
        """Render executive KPIs"""
        st.info("🚧 Executive KPIs - กำลังพัฒนา")

    def _render_project_portfolio_matrix(self):
        """Render project portfolio matrix"""
        st.info("🚧 Portfolio Matrix - กำลังพัฒนา")

    def _render_strategic_initiatives_progress(self):
        """Render strategic initiatives progress"""
        st.info("🚧 Strategic Initiatives - กำลังพัฒนา")
