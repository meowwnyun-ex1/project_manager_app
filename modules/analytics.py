#!/usr/bin/env python3
"""
analytics_ui.py
SDX Project Manager - Enterprise Analytics Dashboard Interface
Advanced data visualization and business intelligence for project management
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Import project modules
from analytics import (
    AnalyticsManager,
    AdvancedAnalyticsEngine,
    ReportType,
    ReportConfig,
)
from ui_components import UIComponents, ThemeManager
from error_handler import ErrorHandler, handle_errors

logger = logging.getLogger(__name__)


class DashboardView(Enum):
    """Dashboard view types"""

    OVERVIEW = "overview"
    PROJECTS = "projects"
    TEAMS = "teams"
    PERFORMANCE = "performance"
    FINANCIAL = "financial"
    REPORTS = "reports"


@dataclass
class AnalyticsConfig:
    """Analytics configuration"""

    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    show_predictions: bool = True
    export_enabled: bool = True
    drill_down_enabled: bool = True


class AnalyticsUI:
    """Enterprise Analytics Dashboard Interface"""

    def __init__(self, db_manager, theme_manager: ThemeManager):
        self.db = db_manager
        self.analytics = AnalyticsManager(db_manager)
        self.advanced_analytics = AdvancedAnalyticsEngine(db_manager)
        self.theme = theme_manager
        self.ui_components = UIComponents(theme_manager)
        self.error_handler = ErrorHandler()
        self.config = AnalyticsConfig()

    @handle_errors
    def render_analytics_dashboard(self):
        """Main analytics dashboard renderer"""
        st.markdown("# 📊 แดชบอร์ดวิเคราะห์ข้อมูล")

        # Dashboard header with controls
        self._render_dashboard_header()

        # Navigation tabs
        (
            tab_overview,
            tab_projects,
            tab_teams,
            tab_performance,
            tab_financial,
            tab_reports,
        ) = st.tabs(
            [
                "📈 ภาพรวม",
                "🎯 โครงการ",
                "👥 ทีม",
                "⚡ ประสิทธิภาพ",
                "💰 การเงิน",
                "📋 รายงาน",
            ]
        )

        with tab_overview:
            self._render_overview_dashboard()

        with tab_projects:
            self._render_project_analytics()

        with tab_teams:
            self._render_team_analytics()

        with tab_performance:
            self._render_performance_analytics()

        with tab_financial:
            self._render_financial_analytics()

        with tab_reports:
            self._render_reports_dashboard()

    def _render_dashboard_header(self):
        """Render dashboard header with controls"""
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.markdown("### 🎯 ศูนย์ควบคุมโครงการ DENSO Innovation")

        with col2:
            # Date range selector
            date_range = st.selectbox(
                "ช่วงเวลา",
                options=["7 วันล่าสุด", "30 วันล่าสุด", "3 เดือนล่าสุด", "ปีนี้", "กำหนดเอง"],
                index=1,
            )

        with col3:
            # Auto refresh toggle
            auto_refresh = st.toggle("อัปเดตอัตโนมัติ", value=self.config.auto_refresh)
            self.config.auto_refresh = auto_refresh

        with col4:
            # Export button
            if st.button("📥 ส่งออกข้อมูล", type="secondary"):
                self._export_dashboard_data()

        st.markdown("---")

    def _render_overview_dashboard(self):
        """Render overview dashboard"""
        # Key Performance Indicators
        self._render_kpi_cards()

        st.markdown("---")

        # Main charts
        col_left, col_right = st.columns([2, 1])

        with col_left:
            self._render_project_timeline_chart()

        with col_right:
            self._render_status_distribution_chart()

        # Recent activity and alerts
        col1, col2 = st.columns(2)

        with col1:
            self._render_recent_activity()

        with col2:
            self._render_alerts_panel()

    def _render_kpi_cards(self):
        """Render KPI cards"""
        try:
            # Get data from analytics
            metrics = self.analytics.get_kpi_metrics()

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                total_projects = metrics.get("total_projects", 0)
                project_growth = metrics.get("project_growth", 0)
                st.metric(
                    label="📊 โครงการทั้งหมด",
                    value=total_projects,
                    delta=f"{project_growth:+.1f}%" if project_growth else None,
                )

            with col2:
                active_tasks = metrics.get("active_tasks", 0)
                task_completion_rate = metrics.get("task_completion_rate", 0)
                st.metric(
                    label="✅ งานที่ดำเนินการ",
                    value=active_tasks,
                    delta=f"{task_completion_rate:.1f}% เสร็จสิ้น",
                )

            with col3:
                team_utilization = metrics.get("team_utilization", 0)
                utilization_change = metrics.get("utilization_change", 0)
                st.metric(
                    label="👥 การใช้งานทีม",
                    value=f"{team_utilization:.1f}%",
                    delta=f"{utilization_change:+.1f}%" if utilization_change else None,
                )

            with col4:
                budget_usage = metrics.get("budget_usage", 0)
                budget_variance = metrics.get("budget_variance", 0)
                st.metric(
                    label="💰 การใช้งบประมาณ",
                    value=f"{budget_usage:.1f}%",
                    delta=f"{budget_variance:+.1f}%" if budget_variance else None,
                    delta_color="inverse",
                )

            with col5:
                quality_score = metrics.get("quality_score", 0)
                quality_trend = metrics.get("quality_trend", 0)
                st.metric(
                    label="🎯 คะแนนคุณภาพ",
                    value=f"{quality_score:.1f}/10",
                    delta=f"{quality_trend:+.2f}" if quality_trend else None,
                )

        except Exception as e:
            logger.error(f"Error rendering KPI cards: {e}")
            st.error("ไม่สามารถโหลดข้อมูล KPI ได้")

    def _render_project_timeline_chart(self):
        """Render project timeline chart"""
        st.markdown("### 📈 ไทม์ไลน์โครงการ")

        try:
            # Get timeline data
            timeline_data = self.analytics.get_project_timeline_data()

            if timeline_data:
                # Create Gantt-like timeline chart
                fig = go.Figure()

                colors = {
                    "Planning": "#FFA500",
                    "In Progress": "#4CAF50",
                    "On Hold": "#FF5722",
                    "Completed": "#2196F3",
                    "Cancelled": "#9E9E9E",
                }

                for idx, project in enumerate(timeline_data):
                    fig.add_trace(
                        go.Scatter(
                            x=[project["start_date"], project["end_date"]],
                            y=[idx, idx],
                            mode="lines+markers",
                            name=project["name"],
                            line=dict(
                                width=10, color=colors.get(project["status"], "#000")
                            ),
                            hovertemplate=f"<b>{project['name']}</b><br>"
                            + f"สถานะ: {project['status']}<br>"
                            + f"ความคืบหน้า: {project['progress']:.1f}%<br>"
                            + f"<extra></extra>",
                        )
                    )

                fig.update_layout(
                    title="ไทม์ไลน์และความคืบหน้าโครงการ",
                    xaxis_title="เวลา",
                    yaxis_title="โครงการ",
                    height=400,
                    showlegend=False,
                    hovermode="closest",
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลโครงการ")

        except Exception as e:
            logger.error(f"Error rendering timeline chart: {e}")
            st.error("ไม่สามารถโหลดกราฟไทม์ไลน์ได้")

    def _render_status_distribution_chart(self):
        """Render status distribution pie chart"""
        st.markdown("### 🎯 สถานะโครงการ")

        try:
            status_data = self.analytics.get_project_status_distribution()

            if status_data:
                fig = px.pie(
                    values=list(status_data.values()),
                    names=list(status_data.keys()),
                    title="การกระจายสถานะโครงการ",
                    color_discrete_map={
                        "Planning": "#FFA500",
                        "In Progress": "#4CAF50",
                        "On Hold": "#FF5722",
                        "Completed": "#2196F3",
                        "Cancelled": "#9E9E9E",
                    },
                )

                fig.update_traces(textposition="inside", textinfo="percent+label")
                fig.update_layout(height=300)

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลสถานะโครงการ")

        except Exception as e:
            logger.error(f"Error rendering status chart: {e}")
            st.error("ไม่สามารถโหลดกราฟสถานะได้")

    def _render_project_analytics(self):
        """Render project-specific analytics"""
        st.markdown("### 🎯 วิเคราะห์โครงการ")

        # Project selector
        projects = self.analytics.get_project_list()
        selected_projects = st.multiselect(
            "เลือกโครงการที่ต้องการวิเคราะห์",
            options=[p["id"] for p in projects],
            format_func=lambda x: next(p["name"] for p in projects if p["id"] == x),
            default=[p["id"] for p in projects[:3]],  # Default to first 3 projects
        )

        if selected_projects:
            # Project comparison charts
            col1, col2 = st.columns(2)

            with col1:
                self._render_project_progress_comparison(selected_projects)

            with col2:
                self._render_project_budget_analysis(selected_projects)

            # Detailed project metrics table
            self._render_project_metrics_table(selected_projects)

    def _render_team_analytics(self):
        """Render team analytics"""
        st.markdown("### 👥 วิเคราะห์ทีม")

        # Team performance metrics
        col1, col2 = st.columns(2)

        with col1:
            self._render_team_workload_chart()

        with col2:
            self._render_team_productivity_chart()

        # Team member performance table
        self._render_team_performance_table()

    def _render_performance_analytics(self):
        """Render performance analytics"""
        st.markdown("### ⚡ วิเคราะห์ประสิทธิภาพ")

        # Performance trend charts
        col1, col2 = st.columns(2)

        with col1:
            self._render_velocity_trend()

        with col2:
            self._render_quality_metrics()

        # Predictive analytics
        with st.expander("🔮 การพยากรณ์ (AI Powered)", expanded=False):
            self._render_predictive_analytics()

    def _render_financial_analytics(self):
        """Render financial analytics"""
        st.markdown("### 💰 วิเคราะห์การเงิน")

        # Budget vs actual
        col1, col2 = st.columns(2)

        with col1:
            self._render_budget_vs_actual()

        with col2:
            self._render_cost_breakdown()

        # ROI analysis
        self._render_roi_analysis()

    def _render_reports_dashboard(self):
        """Render reports dashboard"""
        st.markdown("### 📋 รายงานผู้บริหาร")

        # Report type selector
        report_types = {
            ReportType.PROJECT_SUMMARY: "สรุปภาพรวมโครงการ",
            ReportType.TEAM_PERFORMANCE: "ประสิทธิภาพทีม",
            ReportType.BUDGET_ANALYSIS: "วิเคราะห์งบประมาณ",
            ReportType.TIMELINE_ANALYSIS: "วิเคราะห์ไทม์ไลน์",
            ReportType.QUALITY_METRICS: "ตัวชี้วัดคุณภาพ",
            ReportType.RESOURCE_UTILIZATION: "การใช้ทรัพยากร",
        }

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            selected_report = st.selectbox(
                "เลือกประเภทรายงาน",
                options=list(report_types.keys()),
                format_func=lambda x: report_types[x],
            )

        with col2:
            start_date = st.date_input(
                "วันที่เริ่มต้น", value=date.today() - timedelta(days=30)
            )

        with col3:
            end_date = st.date_input("วันที่สิ้นสุด", value=date.today())

        # Generate report button
        if st.button("📊 สร้างรายงาน", type="primary"):
            self._generate_executive_report(selected_report, start_date, end_date)

    # Helper methods for specific charts
    def _render_project_progress_comparison(self, project_ids: List[int]):
        """Render project progress comparison"""
        try:
            data = self.analytics.get_project_progress_data(project_ids)
            if data:
                fig = px.bar(
                    x=[p["name"] for p in data],
                    y=[p["progress"] for p in data],
                    title="เปรียบเทียบความคืบหน้าโครงการ",
                    labels={"x": "โครงการ", "y": "ความคืบหน้า (%)"},
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลความคืบหน้า")
        except Exception as e:
            logger.error(f"Error rendering progress comparison: {e}")
            st.error("ไม่สามารถโหลดข้อมูลความคืบหน้าได้")

    def _render_recent_activity(self):
        """Render recent activity feed"""
        st.markdown("### 🕒 กิจกรรมล่าสุด")

        try:
            activities = self.analytics.get_recent_activities(limit=10)

            if activities:
                for activity in activities:
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            st.write(f"🔔 {activity['type']}")
                        with col2:
                            st.write(f"{activity['description']}")
                            st.caption(f"{activity['timestamp']} - {activity['user']}")
                        st.markdown("---")
            else:
                st.info("ไม่มีกิจกรรมล่าสุด")

        except Exception as e:
            logger.error(f"Error rendering recent activity: {e}")
            st.error("ไม่สามารถโหลดกิจกรรมล่าสุดได้")

    def _render_alerts_panel(self):
        """Render alerts and notifications panel"""
        st.markdown("### ⚠️ การแจ้งเตือน")

        try:
            alerts = self.analytics.get_system_alerts()

            if alerts:
                for alert in alerts:
                    alert_type = alert["severity"]
                    icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        alert_type, "ℹ️"
                    )

                    st.markdown(f"{icon} **{alert['title']}**")
                    st.write(alert["message"])
                    st.caption(f"เวลา: {alert['timestamp']}")
                    st.markdown("---")
            else:
                st.success("ไม่มีการแจ้งเตือน ทุกอย่างปกติ")

        except Exception as e:
            logger.error(f"Error rendering alerts: {e}")
            st.error("ไม่สามารถโหลดการแจ้งเตือนได้")

    def _export_dashboard_data(self):
        """Export dashboard data"""
        try:
            # Create export data
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "kpi_metrics": self.analytics.get_kpi_metrics(),
                "project_status": self.analytics.get_project_status_distribution(),
                "team_performance": self.analytics.get_team_performance_metrics(),
            }

            # Convert to JSON
            import json

            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)

            # Download button
            st.download_button(
                label="📥 ดาวน์โหลดข้อมูล (JSON)",
                data=json_data,
                file_name=f"sdx_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

            st.success("เตรียมข้อมูลสำหรับส่งออกเรียบร้อยแล้ว")

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            st.error("ไม่สามารถส่งออกข้อมูลได้")

    def _generate_executive_report(
        self, report_type: ReportType, start_date: date, end_date: date
    ):
        """Generate executive report"""
        try:
            config = ReportConfig(
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                format="interactive",
            )

            with st.spinner("กำลังสร้างรายงาน..."):
                report_data = self.advanced_analytics.generate_report(config)

                if report_data:
                    st.success("สร้างรายงานสำเร็จ!")

                    # Display report summary
                    st.markdown("### 📋 สรุปรายงาน")
                    st.write(report_data.get("summary", "ไม่มีข้อมูลสรุป"))

                    # Display charts if available
                    if "charts" in report_data:
                        for chart in report_data["charts"]:
                            st.plotly_chart(chart, use_container_width=True)

                    # Display data tables
                    if "tables" in report_data:
                        for table_name, table_data in report_data["tables"].items():
                            st.markdown(f"#### {table_name}")
                            st.dataframe(table_data, use_container_width=True)
                else:
                    st.warning("ไม่สามารถสร้างรายงานได้")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            st.error("เกิดข้อผิดพลาดในการสร้างรายงาน")

    # Additional helper methods would be implemented here...
    def _render_team_workload_chart(self):
        """Placeholder for team workload chart"""
        st.info("🚧 กราฟภาระงานทีม - กำลังพัฒนา")

    def _render_team_productivity_chart(self):
        """Placeholder for team productivity chart"""
        st.info("🚧 กราฟประสิทธิภาพทีม - กำลังพัฒนา")

    def _render_team_performance_table(self):
        """Placeholder for team performance table"""
        st.info("🚧 ตารางประสิทธิภาพทีม - กำลังพัฒนา")

    def _render_velocity_trend(self):
        """Placeholder for velocity trend"""
        st.info("🚧 แนวโน้มความเร็วในการทำงาน - กำลังพัฒนา")

    def _render_quality_metrics(self):
        """Placeholder for quality metrics"""
        st.info("🚧 ตัวชี้วัดคุณภาพ - กำลังพัฒนา")

    def _render_predictive_analytics(self):
        """Placeholder for predictive analytics"""
        st.info("🚧 การวิเคราะห์เชิงพยากรณ์ - กำลังพัฒนา")

    def _render_budget_vs_actual(self):
        """Placeholder for budget vs actual"""
        st.info("🚧 งบประมาณ vs ค่าใช้จ่ายจริง - กำลังพัฒนา")

    def _render_cost_breakdown(self):
        """Placeholder for cost breakdown"""
        st.info("🚧 การแบ่งค่าใช้จ่าย - กำลังพัฒนา")

    def _render_roi_analysis(self):
        """Placeholder for ROI analysis"""
        st.info("🚧 การวิเคราะห์ ROI - กำลังพัฒนา")

    def _render_project_budget_analysis(self, project_ids: List[int]):
        """Placeholder for project budget analysis"""
        st.info("🚧 การวิเคราะห์งบประมาณโครงการ - กำลังพัฒนา")

    def _render_project_metrics_table(self, project_ids: List[int]):
        """Placeholder for project metrics table"""
        st.info("🚧 ตารางตัวชี้วัดโครงการ - กำลังพัฒนา")
