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
import json
import base64
from io import BytesIO

# Import project modules
from analytics import AnalyticsManager
from projects import ProjectManager
from tasks import TaskManager
from users import UserManager
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
    PREDICTIONS = "predictions"


class MetricType(Enum):
    """Metric types for analytics"""
    
    COMPLETION_RATE = "completion_rate"
    PRODUCTIVITY = "productivity"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    TIMELINE_ADHERENCE = "timeline_adherence"
    RESOURCE_UTILIZATION = "resource_utilization"


@dataclass
class AnalyticsConfig:
    """Analytics configuration"""
    
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    show_predictions: bool = True
    export_enabled: bool = True
    drill_down_enabled: bool = True
    real_time_updates: bool = True
    cache_duration: int = 300  # 5 minutes


@dataclass
class KPIMetric:
    """KPI metric data structure"""
    
    name: str
    value: float
    target: float
    unit: str
    trend: str  # "up", "down", "stable"
    change_percentage: float
    color: str = "#007bff"
    icon: str = "📊"


class AnalyticsUI:
    """Enterprise Analytics Dashboard Interface"""
    
    def __init__(self, db_manager, theme_manager: ThemeManager):
        self.db = db_manager
        self.analytics = AnalyticsManager(db_manager)
        self.project_manager = ProjectManager(db_manager)
        self.task_manager = TaskManager(db_manager)
        self.user_manager = UserManager(db_manager)
        self.theme = theme_manager
        self.ui_components = UIComponents(theme_manager)
        self.error_handler = ErrorHandler()
        self.config = AnalyticsConfig()
    
    @handle_errors
    def _render_performance_analytics(self):
        """Render performance analytics dashboard"""
        st.markdown("## ⚡ วิเคราะห์ประสิทธิภาพ")
        
        # Performance metrics
        self._render_performance_metrics()
        
        st.markdown("---")
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_velocity_chart()
            self._render_burndown_chart()
        
        with col2:
            self._render_cycle_time_analysis()
            self._render_quality_metrics()
    
    @handle_errors
    def _render_financial_analytics(self):
        """Render financial analytics dashboard"""
        st.markdown("## 💰 วิเคราะห์การเงิน")
        
        # Financial overview
        self._render_financial_overview()
        
        st.markdown("---")
        
        # Financial charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_budget_vs_actual()
            self._render_cost_breakdown()
        
        with col2:
            self._render_roi_analysis()
            self._render_resource_cost_analysis()
    
    @handle_errors
    def _render_reports_section(self):
        """Render reports section"""
        st.markdown("## 📋 รายงาน")
        
        # Report types
        report_types = [
            "รายงานสรุปโครงการ",
            "รายงานประสิทธิภาพทีม",
            "รายงานการใช้ทรัพยากร",
            "รายงานการเงิน",
            "รายงานความเสี่ยง",
            "รายงานคุณภาพ"
        ]
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_report = st.selectbox("เลือกประเภทรายงาน", report_types)
        
        with col2:
            report_format = st.selectbox("รูปแบบ", ["PDF", "Excel", "CSV"])
        
        with col3:
            if st.button("📊 สร้างรายงาน", type="primary"):
                self._generate_report(selected_report, report_format)
        
        # Recent reports
        st.markdown("### 📄 รายงานล่าสุด")
        self._render_recent_reports()
    
    @handle_errors
    def _render_predictions_analytics(self):
        """Render predictions and forecasting"""
        st.markdown("## 🔮 การคาดการณ์")
        
        if not self.config.show_predictions:
            st.info("การคาดการณ์ถูกปิดใช้งาน")
            return
        
        # Prediction models
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_completion_prediction()
            self._render_resource_demand_forecast()
        
        with col2:
            self._render_risk_prediction()
            self._render_budget_forecast()
    
    # Helper methods for data retrieval
    def _get_kpi_metrics(self) -> List[KPIMetric]:
        """Get KPI metrics data"""
        try:
            # Sample KPI data - replace with actual implementation
            return [
                KPIMetric(
                    name="อัตราเสร็จโครงการ",
                    value=85.2,
                    target=90.0,
                    unit="%",
                    trend="up",
                    change_percentage=5.3,
                    color="#28a745",
                    icon="🎯"
                ),
                KPIMetric(
                    name="ประสิทธิภาพทีม",
                    value=92.1,
                    target=95.0,
                    unit="%",
                    trend="stable",
                    change_percentage=0.8,
                    color="#007bff",
                    icon="⚡"
                ),
                KPIMetric(
                    name="คุณภาพงาน",
                    value=94.7,
                    target=95.0,
                    unit="%",
                    trend="up",
                    change_percentage=2.1,
                    color="#fd7e14",
                    icon="⭐"
                ),
                KPIMetric(
                    name="ความพึงพอใจ",
                    value=88.5,
                    target=90.0,
                    unit="%",
                    trend="down",
                    change_percentage=-1.2,
                    color="#6f42c1",
                    icon="😊"
                )
            ]
        except Exception as e:
            logger.error(f"Error getting KPI metrics: {e}")
            return []
    
    def _get_project_status_data(self) -> Dict[str, int]:
        """Get project status distribution"""
        try:
            projects = self.project_manager.get_all_projects()
            status_count = {}
            
            for project in projects:
                status = project.get("Status", "Unknown")
                status_count[status] = status_count.get(status, 0) + 1
            
            return status_count
        except Exception as e:
            logger.error(f"Error getting project status data: {e}")
            return {}
    
    def _get_task_completion_trend(self) -> Dict[str, List]:
        """Get task completion trend data"""
        try:
            # Sample trend data - replace with actual implementation
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
            completion_rates = np.random.uniform(70, 95, len(dates))
            
            return {
                "dates": dates.tolist(),
                "completion_rates": completion_rates.tolist()
            }
        except Exception as e:
            logger.error(f"Error getting task completion trend: {e}")
            return {}
    
    def _get_team_workload_data(self) -> Dict[str, List]:
        """Get team workload data"""
        try:
            # Sample workload data - replace with actual implementation
            members = ["สมชาย", "สมหญิง", "สมศักดิ์", "สมใจ", "สมพงษ์"]
            assigned_tasks = [12, 15, 8, 10, 13]
            completed_tasks = [10, 12, 7, 9, 11]
            
            return {
                "members": members,
                "assigned_tasks": assigned_tasks,
                "completed_tasks": completed_tasks
            }
        except Exception as e:
            logger.error(f"Error getting team workload data: {e}")
            return {}
    
    def _get_priority_distribution(self) -> Dict[str, int]:
        """Get task priority distribution"""
        try:
            # Sample priority data - replace with actual implementation
            return {
                "Critical": 5,
                "High": 15,
                "Medium": 25,
                "Low": 10
            }
        except Exception as e:
            logger.error(f"Error getting priority distribution: {e}")
            return {}
    
    def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Get recent activities"""
        try:
            # Sample activities data - replace with actual implementation
            return [
                {
                    "time": "10:30",
                    "type": "task_completed",
                    "description": "งาน 'พัฒนา API ใหม่' เสร็จสิ้น",
                    "user": "สมชาย"
                },
                {
                    "time": "09:15",
                    "type": "project_created",
                    "description": "สร้างโครงการ 'ระบบ CRM'",
                    "user": "สมหญิง"
                },
                {
                    "time": "08:45",
                    "type": "task_assigned",
                    "description": "มอบหมายงาน 'ทดสอบระบบ' ให้ สมศักดิ์",
                    "user": "สมใจ"
                }
            ]
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []
    
    def _get_activity_icon(self, activity_type: str) -> str:
        """Get icon for activity type"""
        icons = {
            "task_completed": "✅",
            "task_assigned": "📋",
            "project_created": "📁",
            "project_updated": "🔄",
            "user_joined": "👤",
            "comment_added": "💬"
        }
        return icons.get(activity_type, "📌")
    
    def _get_on_time_projects_count(self) -> int:
        """Get count of on-time projects"""
        try:
            # Sample implementation - replace with actual
            return 8
        except Exception as e:
            logger.error(f"Error getting on-time projects count: {e}")
            return 0
    
    # Chart rendering methods
    def _render_project_timeline_chart(self):
        """Render project timeline chart"""
        st.markdown("#### 📅 ไทม์ไลน์โครงการ")
        
        # Sample timeline data
        projects = [
            {"name": "ระบบ CRM", "start": "2024-01-01", "end": "2024-03-31", "progress": 75},
            {"name": "แอป Mobile", "start": "2024-02-01", "end": "2024-05-31", "progress": 45},
            {"name": "ระบบ Analytics", "start": "2024-03-01", "end": "2024-06-30", "progress": 20}
        ]
        
        fig = go.Figure()
        
        for i, project in enumerate(projects):
            fig.add_trace(go.Bar(
                name=project["name"],
                y=[project["name"]],
                x=[project["progress"]],
                orientation='h',
                marker=dict(color=f'hsl({i*120}, 70%, 50%)')
            ))
        
        fig.update_layout(
            title="ความคืบหน้าโครงการ",
            xaxis_title="ความคืบหน้า (%)",
            height=300,
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_project_budget_analysis(self):
        """Render project budget analysis"""
        st.markdown("#### 💰 วิเคราะห์งบประมาณ")
        
        # Sample budget data
        categories = ["บุคลากร", "เทคโนโลยี", "การตลาด", "อื่นๆ"]
        budgeted = [500000, 200000, 150000, 100000]
        actual = [520000, 180000, 140000, 90000]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='งบประมาณ',
            x=categories,
            y=budgeted,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='จริง',
            x=categories,
            y=actual,
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title="งบประมาณ vs ค่าใช้จ่ายจริง",
            yaxis_title="จำนวนเงิน (บาท)",
            barmode='group',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_project_resource_allocation(self):
        """Render project resource allocation"""
        st.markdown("#### 👥 การจัดสรรทรัพยากร")
        
        # Sample resource data
        resources = ["Developer", "Designer", "Tester", "PM", "Analyst"]
        allocated = [8, 3, 4, 2, 3]
        available = [10, 4, 5, 3, 4]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='ใช้งาน',
            x=resources,
            y=allocated,
            marker_color='orange'
        ))
        
        fig.add_trace(go.Bar(
            name='ว่าง',
            x=resources,
            y=[available[i] - allocated[i] for i in range(len(resources))],
            marker_color='lightgray'
        ))
        
        fig.update_layout(
            title="การใช้ทรัพยากรบุคคล",
            yaxis_title="จำนวนคน",
            barmode='stack',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_project_risk_assessment(self):
        """Render project risk assessment"""
        st.markdown("#### ⚠️ การประเมินความเสี่ยง")
        
        # Sample risk data
        risks = ["เทคนิค", "ตลาด", "ทรัพยากร", "เวลา", "งบประมาณ"]
        probability = [0.3, 0.2, 0.4, 0.6, 0.3]
        impact = [0.8, 0.9, 0.6, 0.7, 0.8]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=probability,
            y=impact,
            mode='markers+text',
            text=risks,
            textposition="top center",
            marker=dict(
                size=[p*i*100 for p, i in zip(probability, impact)],
                color=['red' if p*i > 0.3 else 'orange' if p*i > 0.15 else 'green' 
                       for p, i in zip(probability, impact)],
                opacity=0.7
            )
        ))
        
        fig.update_layout(
            title="แผนที่ความเสี่ยง",
            xaxis_title="ความน่าจะเป็น",
            yaxis_title="ผลกระทบ",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Team analytics methods
    def _render_team_performance_metrics(self):
        """Render team performance metrics"""
        st.markdown("### 📊 ประสิทธิภาพทีม")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_velocity = 23.5
            st.metric("Velocity เฉลี่ย", f"{avg_velocity} SP", "+2.3")
        
        with col2:
            team_satisfaction = 4.2
            st.metric("ความพึงพอใจ", f"{team_satisfaction}/5", "+0.1")
        
        with col3:
            collaboration_score = 87
            st.metric("คะแนนร่วมมือ", f"{collaboration_score}%", "+5%")
        
        with col4:
            skill_coverage = 92
            st.metric("ครอบคลุมทักษะ", f"{skill_coverage}%", "+3%")
    
    def _render_team_productivity_chart(self):
        """Render team productivity chart"""
        st.markdown("#### 📈 ผลผลิตทีม")
        
        # Sample productivity data
        weeks = ["สัปดาห์ 1", "สัปดาห์ 2", "สัปดาห์ 3", "สัปดาห์ 4"]
        story_points = [25, 28, 22, 30]
        
        fig = px.line(
            x=weeks,
            y=story_points,
            title="Story Points ที่เสร็จสิ้นต่อสัปดาห์",
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="สัปดาห์",
            yaxis_title="Story Points",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_team_collaboration_matrix(self):
        """Render team collaboration matrix"""
        st.markdown("#### 🤝 เมทริกซ์ความร่วมมือ")
        
        # Sample collaboration data
        team_members = ["สมชาย", "สมหญิง", "สมศักดิ์", "สมใจ"]
        collaboration_matrix = np.random.rand(4, 4)
        
        fig = px.imshow(
            collaboration_matrix,
            x=team_members,
            y=team_members,
            color_continuous_scale="Blues",
            title="ระดับความร่วมมือระหว่างสมาชิก"
        )
        
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_skill_distribution_chart(self):
        """Render skill distribution chart"""
        st.markdown("#### 🎯 การกระจายทักษะ")
        
        # Sample skill data
        skills = ["Python", "React", "Database", "UI/UX", "DevOps"]
        expert_count = [3, 2, 4, 1, 2]
        intermediate_count = [2, 3, 1, 3, 2]
        beginner_count = [1, 1, 1, 2, 2]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(name='Expert', x=skills, y=expert_count))
        fig.add_trace(go.Bar(name='Intermediate', x=skills, y=intermediate_count))
        fig.add_trace(go.Bar(name='Beginner', x=skills, y=beginner_count))
        
        fig.update_layout(
            title="การกระจายระดับทักษะในทีม",
            barmode='stack',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_team_satisfaction_survey(self):
        """Render team satisfaction survey results"""
        st.markdown("#### 😊 ผลสำรวจความพึงพอใจ")
        
        # Sample satisfaction data
        categories = ["สภาพแวดล้อม", "เครื่องมือ", "การจัดการ", "การเรียนรู้", "ความท้าทาย"]
        scores = [4.2, 3.8, 4.1, 4.5, 3.9]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name='คะแนนความพึงพอใจ'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            title="คะแนนความพึงพอใจในแต่ละด้าน",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance analytics methods
    def _render_performance_metrics(self):
        """Render performance metrics"""
        st.markdown("### ⚡ ตัวชี้วัดประสิทธิภาพ")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cycle_time = 5.2
            st.metric("Cycle Time เฉลี่ย", f"{cycle_time} วัน", "-0.8")
        
        with col2:
            lead_time = 8.7
            st.metric("Lead Time เฉลี่ย", f"{lead_time} วัน", "-1.2")
        
        with col3:
            throughput = 12
            st.metric("Throughput", f"{throughput} งาน/สัปดาห์", "+2")
        
        with col4:
            defect_rate = 2.1
            st.metric("Defect Rate", f"{defect_rate}%", "-0.5")
    
    def _render_velocity_chart(self):
        """Render velocity chart"""
        st.markdown("#### 🚀 Velocity Chart")
        
        # Sample velocity data
        sprints = [f"Sprint {i}" for i in range(1, 11)]
        planned = [25, 28, 22, 30, 26, 24, 29, 27, 25, 28]
        actual = [23, 25, 20, 28, 24, 22, 27, 25, 23, 26]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='วางแผน',
            x=sprints,
            y=planned,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='จริง',
            x=sprints,
            y=actual,
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title="Velocity: วางแผน vs จริง",
            xaxis_title="Sprint",
            yaxis_title="Story Points",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_burndown_chart(self):
        """Render burndown chart"""
        st.markdown("#### 📉 Burndown Chart")
        
        # Sample burndown data
        days = list(range(1, 15))
        ideal = [100 - (i * 100/14) for i in range(14)]
        actual = [100, 95, 88, 82, 78, 70, 65, 58, 52, 45, 38, 30, 20, 10]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=days,
            y=ideal,
            mode='lines',
            name='เส้นอุดมคติ',
            line=dict(dash='dash', color='gray')
        ))
        
        fig.add_trace(go.Scatter(
            x=days,
            y=actual,
            mode='lines+markers',
            name='จริง',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title="Burndown Chart - Sprint ปัจจุบัน",
            xaxis_title="วัน",
            yaxis_title="งานที่เหลือ (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_cycle_time_analysis(self):
        """Render cycle time analysis"""
        st.markdown("#### ⏱️ วิเคราะห์ Cycle Time")
        
        # Sample cycle time data
        stages = ["To Do", "In Progress", "Review", "Testing", "Done"]
        avg_time = [0.5, 3.2, 1.8, 2.1, 0.3]
        
        fig = px.bar(
            x=stages,
            y=avg_time,
            title="เวลาเฉลี่ยในแต่ละขั้นตอน",
            color=avg_time,
            color_continuous_scale="Blues"
        )
        
        fig.update_layout(
            xaxis_title="ขั้นตอน",
            yaxis_title="เวลา (วัน)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_quality_metrics(self):
        """Render quality metrics"""
        st.markdown("#### ⭐ ตัวชี้วัดคุณภาพ")
        
        # Sample quality data
        metrics = ["Code Coverage", "Bug Rate", "Customer Satisfaction", "Performance Score"]
        scores = [85, 92, 88, 91]
        targets = [90, 95, 90, 95]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='คะแนนปัจจุบัน',
            x=metrics,
            y=scores,
            marker_color='lightgreen'
        ))
        
        fig.add_trace(go.Scatter(
            name='เป้าหมาย',
            x=metrics,
            y=targets,
            mode='markers',
            marker=dict(color='red', size=10, symbol='diamond')
        ))
        
        fig.update_layout(
            title="ตัวชี้วัดคุณภาพ vs เป้าหมาย",
            yaxis_title="คะแนน (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Financial analytics methods
    def _render_financial_overview(self):
        """Render financial overview"""
        st.markdown("### 💰 ภาพรวมการเงิน")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_budget = 2500000
            st.metric("งบประมาณรวม", f"฿{total_budget:,}")
        
        with col2:
            spent = 1850000
            st.metric("ใช้ไปแล้ว", f"฿{spent:,}", f"-฿{spent-1500000:,}")
        
        with col3:
            remaining = total_budget - spent
            st.metric("คงเหลือ", f"฿{remaining:,}")
        
        with col4:
            roi = 15.2
            st.metric("ROI", f"{roi}%", "+2.1%")
    
    def _render_budget_vs_actual(self):
        """Render budget vs actual spending"""
        st.markdown("#### 📊 งบประมาณ vs รายจ่ายจริง")
        
        # Sample budget data
        months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย."]
        budget = [200000, 250000, 300000, 280000, 320000, 350000]
        actual = [180000, 240000, 320000, 260000, 310000, 330000]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=budget,
            mode='lines+markers',
            name='งบประมาณ',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=actual,
            mode='lines+markers',
            name='รายจ่ายจริง',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title="เปรียบเทียบงบประมาณกับรายจ่ายจริง",
            xaxis_title="เดือน",
            yaxis_title="จำนวนเงิน (บาท)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_cost_breakdown(self):
        """Render cost breakdown"""
        st.markdown("#### 🥧 การแบ่งค่าใช้จ่าย")
        
        # Sample cost data
        categories = ["เงินเดือน", "เทคโนโลยี", "อุปกรณ์", "การฝึกอบรม", "อื่นๆ"]
        costs = [1200000, 400000, 150000, 80000, 70000]
        
        fig = px.pie(
            values=costs,
            names=categories,
            title="การแบ่งค่าใช้จ่ายตามหมวดหมู่"
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_roi_analysis(self):
        """Render ROI analysis"""
        st.markdown("#### 📈 วิเคราะห์ ROI")
        
        # Sample ROI data
        projects = ["โครงการ A", "โครงการ B", "โครงการ C", "โครงการ D"]
        investment = [500000, 300000, 800000, 450000]
        returns = [750000, 420000, 960000, 540000]
        roi = [(r/i - 1) * 100 for r, i in zip(returns, investment)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=projects,
            y=roi,
            marker_color=['green' if r > 20 else 'orange' if r > 10 else 'red' for r in roi],
            text=[f"{r:.1f}%" for r in roi],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="ROI ของแต่ละโครงการ",
            xaxis_title="โครงการ",
            yaxis_title="ROI (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_resource_cost_analysis(self):
        """Render resource cost analysis"""
        st.markdown("#### 👥 วิเคราะห์ต้นทุนทรัพยากร")
        
        # Sample resource cost data
        resources = ["Senior Dev", "Junior Dev", "Designer", "Tester", "PM"]
        hourly_rate = [1500, 800, 1200, 900, 2000]
        hours_used = [160, 180, 120, 140, 100]
        total_cost = [r * h for r, h in zip(hourly_rate, hours_used)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=resources,
            y=total_cost,
            marker_color='lightcoral',
            text=[f"฿{c:,}" for c in total_cost],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="ต้นทุนทรัพยากรต่อเดือน",
            xaxis_title="ประเภททรัพยากร",
            yaxis_title="ต้นทุน (บาท)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Reports section methods
    def _render_recent_reports(self):
        """Render recent reports list"""
        # Sample recent reports data
        reports = [
            {"name": "รายงานสรุปโครงการ Q1", "date": "2024-03-31", "format": "PDF", "size": "2.1 MB"},
            {"name": "รายงานประสิทธิภาพทีม มี.ค.", "date": "2024-03-30", "format": "Excel", "size": "1.8 MB"},
            {"name": "รายงานการเงิน มี.ค.", "date": "2024-03-29", "format": "PDF", "size": "1.5 MB"}
        ]
        
        for report in reports:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{report['name']}**")
                    st.markdown(f"*{report['date']}*")
                
                with col2:
                    st.markdown(f"`{report['format']}`")
                
                with col3:
                    st.markdown(f"{report['size']}")
                
                with col4:
                    if st.button("📥", key=f"download_{report['name']}", help="ดาวน์โหลด"):
                        self._download_report(report['name'])
    
    def _generate_report(self, report_type: str, format: str):
        """Generate report based on type and format"""
        try:
            with st.spinner(f"กำลังสร้าง{report_type}..."):
                # Simulate report generation
                import time
                time.sleep(2)
                
                st.success(f"สร้าง{report_type} ในรูปแบบ {format} เสร็จสิ้น!")
                
                # Provide download link
                if st.button("📥 ดาวน์โหลดรายงาน"):
                    self._create_download_link(report_type, format)
                    
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            st.error("เกิดข้อผิดพลาดในการสร้างรายงาน")
    
    def _download_report(self, report_name: str):
        """Handle report download"""
        st.info(f"🚧 ฟีเจอร์ดาวน์โหลด {report_name} จะพัฒนาในเวอร์ชันถัดไป")
    
    def _create_download_link(self, report_type: str, format: str):
        """Create download link for generated report"""
        # Sample download implementation
        sample_data = f"Sample {report_type} in {format} format"
        b64 = base64.b64encode(sample_data.encode()).decode()
        
        href = f'<a href="data:file/txt;base64,{b64}" download="{report_type}.{format.lower()}">📥 คลิกเพื่อดาวน์โหลด</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    # Predictions methods
    def _render_completion_prediction(self):
        """Render project completion prediction"""
        st.markdown("#### 🎯 คาดการณ์การเสร็จสิ้น")
        
        # Sample prediction data
        projects = ["โครงการ A", "โครงการ B", "โครงการ C"]
        current_progress = [75, 45, 80]
        predicted_completion = ["2024-05-15", "2024-07-20", "2024-04-30"]
        confidence = [85, 70, 92]
        
        for i, project in enumerate(projects):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{project}**")
                    st.progress(current_progress[i] / 100)
                    st.markdown(f"ความคืบหน้า: {current_progress[i]}%")
                
                with col2:
                    st.markdown("**คาดการณ์เสร็จ**")
                    st.markdown(predicted_completion[i])
                
                with col3:
                    st.markdown("**ความมั่นใจ**")
                    color = "green" if confidence[i] > 80 else "orange" if confidence[i] > 60 else "red"
                    st.markdown(f"<span style='color:{color}'>{confidence[i]}%</span>", 
                               unsafe_allow_html=True)
    
    def _render_resource_demand_forecast(self):
        """Render resource demand forecast"""
        st.markdown("#### 👥 คาดการณ์ความต้องการทรัพยากร")
        
        # Sample forecast data
        months = ["เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค."]
        developers = [8, 10, 12, 10, 9]
        designers = [3, 4, 3, 4, 3]
        testers = [4, 5, 6, 5, 4]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=developers,
            mode='lines+markers',
            name='Developers',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=designers,
            mode='lines+markers',
            name='Designers',
            line=dict(color='green')
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=testers,
            mode='lines+markers',
            name='Testers',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title="คาดการณ์ความต้องการทรัพยากร",
            xaxis_title="เดือน",
            yaxis_title="จำนวนคน",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_risk_prediction(self):
        """Render risk prediction"""
        st.markdown("#### ⚠️ คาดการณ์ความเสี่ยง")
        
        # Sample risk prediction data
        risks = [
            {"type": "ความล่าช้า", "probability": 25, "impact": "กลาง", "timeline": "2 สัปดาห์"},
            {"type": "งบประมาณเกิน", "probability": 15, "impact": "สูง", "timeline": "1 เดือน"},
            {"type": "ทรัพยากรขาดแคลน", "probability": 35, "impact": "กลาง", "timeline": "3 สัปดาห์"}
        ]
        
        for risk in risks:
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"**{risk['type']}**")
                
                with col2:
                    prob_color = "red" if risk['probability'] > 30 else "orange" if risk['probability'] > 15 else "green"
                    st.markdown(f"<span style='color:{prob_color}'>{risk['probability']}%</span>", 
                               unsafe_allow_html=True)
                
                with col3:
                    impact_color = "red" if risk['impact'] == "สูง" else "orange"
                    st.markdown(f"<span style='color:{impact_color}'>{risk['impact']}</span>", 
                               unsafe_allow_html=True)
                
                with col4:
                    st.markdown(risk['timeline'])
    
    def _render_budget_forecast(self):
        """Render budget forecast"""
        st.markdown("#### 💰 คาดการณ์งบประมาณ")
        
        # Sample budget forecast data
        months = ["เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย."]
        planned_spending = [300000, 350000, 320000, 380000, 340000, 360000]
        forecasted_spending = [310000, 360000, 335000, 390000, 355000, 375000]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=planned_spending,
            mode='lines+markers',
            name='วางแผน',
            line=dict(color='blue', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=forecasted_spending,
            mode='lines+markers',
            name='คาดการณ์',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title="คาดการณ์การใช้งบประมาณ",
            xaxis_title="เดือน",
            yaxis_title="จำนวนเงิน (บาท)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Export functionality
    def _show_export_options(self):
        """Show export options modal"""
        with st.expander("📤 ตัวเลือกการส่งออก", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**รูปแบบไฟล์**")
                export_format = st.selectbox(
                    "เลือกรูปแบบ",
                    options=["PDF", "Excel", "CSV", "JSON"],
                    key="export_format"
                )
            
            with col2:
                st.markdown("**ข้อมูลที่ต้องการ**")
                data_options = st.multiselect(
                    "เลือกข้อมูล",
                    options=["KPIs", "โครงการ", "งาน", "ทีม", "การเงิน"],
                    default=["KPIs", "โครงการ"],
                    key="export_data"
                )
            
            with col3:
                st.markdown("**ช่วงเวลา**")
                date_range = st.selectbox(
                    "เลือกช่วงเวลา",
                    options=["30 วันล่าสุด", "3 เดือนล่าสุด", "ปีล่าสุด"],
                    key="export_date_range"
                )
            
            if st.button("📥 ส่งออกข้อมูล", type="primary"):
                self._export_analytics_data(export_format, data_options, date_range)
    
    def _export_analytics_data(self, format: str, data_options: List[str], date_range: str):
        """Export analytics data"""
        try:
            with st.spinner("กำลังเตรียมข้อมูลส่งออก..."):
                # Simulate data preparation
                import time
                time.sleep(2)
                
                # Create sample export data
                export_data = {
                    "timestamp": datetime.now().isoformat(),
                    "format": format,
                    "data_types": data_options,
                    "date_range": date_range
                }
                
                # Create download
                if format == "JSON":
                    data_str = json.dumps(export_data, ensure_ascii=False, indent=2)
                    b64 = base64.b64encode(data_str.encode('utf-8')).decode()
                    filename = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                else:
                    data_str = f"Analytics Export - {format}\nGenerated: {datetime.now()}"
                    b64 = base64.b64encode(data_str.encode('utf-8')).decode()
                    filename = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format.lower()}"
                
                href = f'<a href="data:file/{format.lower()};base64,{b64}" download="{filename}">📥 คลิกเพื่อดาวน์โหลดไฟล์</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("เตรียมไฟล์ส่งออกเรียบร้อย!")
                
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            st.error("เกิดข้อผิดพลาดในการส่งออกข้อมูล")


# Advanced Analytics Components
class AdvancedAnalyticsComponents:
    """Advanced analytics components for deep insights"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.analytics = AnalyticsManager(db_manager)
    
    def render_predictive_analytics(self):
        """Render predictive analytics dashboard"""
        st.markdown("### 🔮 การวิเคราะห์เชิงทำนาย")
        
        # Machine learning insights
        self._render_ml_insights()
        
        # Trend analysis
        self._render_trend_analysis()
        
        # Anomaly detection
        self._render_anomaly_detection()
    
    def _render_ml_insights(self):
        """Render machine learning insights"""
        st.markdown("#### 🤖 ข้อมูลเชิงลึกจาก AI")
        
        insights = [
            "ทีม A มีแนวโน้มจะทำงานเสร็จล่าช้า 15% จากกำหนด",
            "โครงการประเภท 'พัฒนาระบบ' มักใช้เวลานานกว่าที่ประมาณการ 20%",
            "การมอบหมายงานในวันจันทร์มีโอกาสเสร็จตรงเวลาสูงสุด",
            "ทีมที่มีสมาชิก 5-7 คนมีประสิทธิภาพสูงสุด"
        ]
        
        for insight in insights:
            st.info(f"💡 {insight}")
    
    def _render_trend_analysis(self):
        """Render trend analysis"""
        st.markdown("#### 📈 การวิเคราะห์แนวโน้ม")
        
        # Sample trend data
        metrics = ["ประสิทธิภาพ", "คุณภาพ", "ความพึงพอใจ"]
        trends = ["เพิ่มขึ้น", "คงที่", "ลดลง"]
        changes = ["+5.2%", "0.1%", "-2.1%"]
        
        for metric, trend, change in zip(metrics, trends, changes):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{metric}**")
            
            with col2:
                trend_color = "green" if trend == "เพิ่มขึ้น" else "red" if trend == "ลดลง" else "gray"
                st.markdown(f"<span style='color:{trend_color}'>{trend}</span>", 
                           unsafe_allow_html=True)
            
            with col3:
                change_color = "green" if change.startswith("+") else "red"
                st.markdown(f"<span style='color:{change_color}'>{change}</span>", 
                           unsafe_allow_html=True)
    
    def _render_anomaly_detection(self):
        """Render anomaly detection results"""
        st.markdown("#### 🚨 การตรวจจับความผิดปกติ")
        
        anomalies = [
            {"type": "การใช้เวลา", "description": "งาน ID #1234 ใช้เวลานานผิดปกติ", "severity": "กลาง"},
            {"type": "ทรัพยากร", "description": "ทีม B ขาดแคลนสมาชิก", "severity": "สูง"},
            {"type": "คุณภาพ", "description": "จำนวน Bug เพิ่มขึ้นผิดปกติ", "severity": "กลาง"}
        ]
        
        for anomaly in anomalies:
            severity_color = "red" if anomaly["severity"] == "สูง" else "orange"
            
            st.warning(f"⚠️ **{anomaly['type']}**: {anomaly['description']} (ระดับ: {anomaly['severity']})")


# Real-time Analytics
class RealTimeAnalytics:
    """Real-time analytics and monitoring"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def render_real_time_dashboard(self):
        """Render real-time monitoring dashboard"""
        st.markdown("### ⚡ การติดตามแบบเรียลไทม์")
        
        # Auto-refresh placeholder
        placeholder = st.empty()
        
        with placeholder.container():
            # Current active users
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                active_users = self._get_active_users_count()
                st.metric("ผู้ใช้ออนไลน์", active_users, "+2")
            
            with col2:
                active_tasks = self._get_active_tasks_count()
                st.metric("งานที่ดำเนินการ", active_tasks, "+1")
            
            with col3:
                completed_today = self._get_completed_today_count()
                st.metric("เสร็จวันนี้", completed_today, "+3")
            
            with col4:
                system_load = self._get_system_load()
                st.metric("โหลดระบบ", f"{system_load}%", "-5%")
            
            # Real-time activity feed
            self._render_activity_feed()
    
    def _get_active_users_count(self) -> int:
        """Get count of currently active users"""
        return 12  # Placeholder
    
    def _get_active_tasks_count(self) -> int:
        """Get count of active tasks"""
        return 45  # Placeholder
    
    def _get_completed_today_count(self) -> int:
        """Get count of tasks completed today"""
        return 8  # Placeholder
    
    def _get_system_load(self) -> float:
        """Get current system load percentage"""
        return 67.5  # Placeholder
    
    def _render_activity_feed(self):
        """Render real-time activity feed"""
        st.markdown("#### 📡 กิจกรรมแบบเรียลไทม์")
        
        activities = [
            {"time": "2 นาทีที่แล้ว", "action": "สมชาย เสร็จสิ้นงาน 'ทดสอบระบบ'"},
            {"time": "5 นาทีที่แล้ว", "action": "สมหญิง สร้างงานใหม่ 'ออกแบบ UI'"},
            {"time": "8 นาทีที่แล้ว", "action": "สมศักดิ์ อัพเดทสถานะงาน"},
            {"time": "12 นาทีที่แล้ว", "action": "สมใจ เข้าสู่ระบบ"}
        ]
        
        for activity in activities:
            st.markdown(f"🕐 **{activity['time']}** - {activity['action']}")


# Main render function
def render_analytics_ui(db_manager, theme_manager: ThemeManager):
    """Main function to render analytics UI"""
    try:
        analytics_ui = AnalyticsUI(db_manager, theme_manager)
        analytics_ui.render_analytics_dashboard()
    except Exception as e:
        logger.error(f"Error rendering analytics UI: {e}")
        st.error("เกิดข้อผิดพลาดในการแสดงผลแดชบอร์ดวิเคราะห์")


# Data export utilities
def export_analytics_to_excel(data: Dict[str, Any]) -> bytes:
    """Export analytics data to Excel format"""
    try:
        # Create Excel workbook
        from io import BytesIO
        import pandas as pd
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write different data sheets
            for sheet_name, sheet_data in data.items():
                if isinstance(sheet_data, list):
                    df = pd.DataFrame(sheet_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        return b""


def export_analytics_to_pdf(data: Dict[str, Any]) -> bytes:
    """Export analytics data to PDF format"""
    try:
        # PDF generation would be implemented here
        # Using libraries like reportlab or weasyprint
        return b"Sample PDF content"
        
    except Exception as e:
        logger.error(f"Error exporting to PDF: {e}")
        return b""

def render_analytics_dashboard(self):
        """Main analytics dashboard renderer"""
        st.markdown("# 📊 แดชบอร์ดวิเคราะห์ข้อมูล")
        
        # Dashboard header with controls
        self._render_dashboard_header()
        
        # Navigation tabs
        tabs = st.tabs([
            "🏠 ภาพรวม",
            "📁 โครงการ", 
            "👥 ทีมงาน",
            "⚡ ประสิทธิภาพ",
            "💰 การเงิน",
            "📋 รายงาน",
            "🔮 การคาดการณ์"
        ])
        
        with tabs[0]:
            self._render_overview_dashboard()
        
        with tabs[1]:
            self._render_projects_analytics()
        
        with tabs[2]:
            self._render_teams_analytics()
        
        with tabs[3]:
            self._render_performance_analytics()
        
        with tabs[4]:
            self._render_financial_analytics()
        
        with tabs[5]:
            self._render_reports_section()
        
        with tabs[6]:
            self._render_predictions_analytics()
    
def _render_dashboard_header(self):
        """Render dashboard header with controls"""
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown("### 📈 ข้อมูลเชิงลึกและการวิเคราะห์")
        
        with col2:
            # Date range selector
            date_range = st.selectbox(
                "📅 ช่วงเวลา",
                options=["7 วันล่าสุด", "30 วันล่าสุด", "3 เดือนล่าสุด", "ปีล่าสุด", "กำหนดเอง"],
                index=1
            )
            st.session_state.analytics_date_range = date_range
        
        with col3:
            # Auto refresh toggle
            auto_refresh = st.checkbox("🔄 อัพเดทอัตโนมัติ", value=self.config.auto_refresh)
            if auto_refresh:
                st.rerun()
        
        with col4:
            # Export button
            if st.button("📤 ส่งออกรายงาน"):
                self._show_export_options()
    
                @handle_errors
def _render_overview_dashboard(self):
        """Render overview dashboard"""
        st.markdown("## 🏠 ภาพรวมองค์กร")
        
        # Key Performance Indicators
        self._render_kpi_section()
        
        st.markdown("---")
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_project_status_chart()
            self._render_task_completion_trend()
        
        with col2:
            self._render_team_workload_chart()
            self._render_priority_distribution()
        
        # Bottom section
        st.markdown("---")
        self._render_recent_activities()
    
def _render_kpi_section(self):
        """Render Key Performance Indicators"""
        st.markdown("### 📊 ตัวชี้วัดหลัก (KPIs)")
        
        # Get KPI data
        kpis = self._get_kpi_metrics()
        
        # Render KPI cards
        cols = st.columns(len(kpis))
        
        for i, kpi in enumerate(kpis):
            with cols[i]:
                self._render_kpi_card(kpi)
    
def _render_kpi_card(self, kpi: KPIMetric):
        """Render individual KPI card"""
        # Determine trend arrow and color
        if kpi.trend == "up":
            trend_arrow = "↗️"
            trend_color = "#28a745"
        elif kpi.trend == "down":
            trend_arrow = "↘️"
            trend_color = "#dc3545"
        else:
            trend_arrow = "➡️"
            trend_color = "#6c757d"
        
        # Progress calculation
        progress = min(kpi.value / kpi.target, 1.0) if kpi.target > 0 else 0
        
        # Card HTML
        card_html = f"""
        <div style="
            background: linear-gradient(135deg, {kpi.color}20, {kpi.color}10);
            border-left: 4px solid {kpi.color};
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 10px;">{kpi.icon}</span>
                <h4 style="margin: 0; color: {kpi.color};">{kpi.name}</h4>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #333;">{kpi.value:.1f}{kpi.unit}</h2>
                    <small style="color: #666;">เป้าหมาย: {kpi.target:.1f}{kpi.unit}</small>
                </div>
                <div style="text-align: right;">
                    <span style="color: {trend_color}; font-size: 20px;">{trend_arrow}</span>
                    <br>
                    <small style="color: {trend_color};">{kpi.change_percentage:+.1f}%</small>
                </div>
            </div>
            
            <div style="margin-top: 10px;">
                <div style="
                    background: #e9ecef; 
                    border-radius: 10px; 
                    height: 6px; 
                    overflow: hidden;
                ">
                    <div style="
                        background: {kpi.color}; 
                        height: 100%; 
                        width: {progress * 100:.1f}%;
                        transition: width 0.3s ease;
                    "></div>
                </div>
                <small style="color: #666;">{progress * 100:.1f}% ของเป้าหมาย</small>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
    
def _render_project_status_chart(self):
        """Render project status distribution chart"""
        st.markdown("#### 📁 สถานะโครงการ")
        
        # Get project status data
        project_data = self._get_project_status_data()
        
        if not project_data:
            st.info("ไม่มีข้อมูลโครงการ")
            return
        
        # Create pie chart
        fig = px.pie(
            values=list(project_data.values()),
            names=list(project_data.keys()),
            title="การกระจายสถานะโครงการ",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>จำนวน: %{value}<br>เปอร์เซ็นต์: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            height=400,
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_task_completion_trend(self):
        """Render task completion trend chart"""
        st.markdown("#### ✅ แนวโน้มการทำงานเสร็จ")
        
        # Get completion trend data
        trend_data = self._get_task_completion_trend()
        
        if not trend_data:
            st.info("ไม่มีข้อมูลแนวโน้ม")
            return
        
        # Create line chart
        fig = px.line(
            x=trend_data["dates"],
            y=trend_data["completion_rates"],
            title="อัตราการทำงานเสร็จ (30 วันล่าสุด)",
            labels={'x': 'วันที่', 'y': 'อัตราเสร็จ (%)'}
        )
        
        fig.update_traces(
            line=dict(color='#007bff', width=3),
            mode='lines+markers'
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="วันที่",
            yaxis_title="อัตราเสร็จ (%)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_team_workload_chart(self):
        """Render team workload chart"""
        st.markdown("#### 👥 ภาระงานทีม")
        
        # Get team workload data
        workload_data = self._get_team_workload_data()
        
        if not workload_data:
            st.info("ไม่มีข้อมูลภาระงาน")
            return
        
        # Create horizontal bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='งานที่ได้รับมอบหมาย',
            y=workload_data["members"],
            x=workload_data["assigned_tasks"],
            orientation='h',
            marker=dict(color='lightblue')
        ))
        
        fig.add_trace(go.Bar(
            name='งานที่เสร็จแล้ว',
            y=workload_data["members"],
            x=workload_data["completed_tasks"],
            orientation='h',
            marker=dict(color='darkblue')
        ))
        
        fig.update_layout(
            title="ภาระงานของสมาชิกทีม",
            xaxis_title="จำนวนงาน",
            yaxis_title="สมาชิกทีม",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_priority_distribution(self):
        """Render task priority distribution"""
        st.markdown("#### 🎯 การกระจายความสำคัญงาน")
        
        # Get priority data
        priority_data = self._get_priority_distribution()
        
        if not priority_data:
            st.info("ไม่มีข้อมูลความสำคัญ")
            return
        
        # Create donut chart
        fig = go.Figure(data=[go.Pie(
            labels=list(priority_data.keys()),
            values=list(priority_data.values()),
            hole=.3
        )])
        
        fig.update_traces(
            hoverinfo="label+percent",
            textinfo="value+percent",
            textfont_size=12,
            marker=dict(
                colors=['#dc3545', '#fd7e14', '#ffc107', '#28a745'],
                line=dict(color='#FFFFFF', width=2)
            )
        )
        
        fig.update_layout(
            title="การกระจายความสำคัญของงาน",
            height=400,
            annotations=[dict(text='งานทั้งหมด', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recent_activities(self):
        """Render recent activities timeline"""
        st.markdown("### 📈 กิจกรรมล่าสุด")
        
        # Get recent activities
        activities = self._get_recent_activities()
        
        if not activities:
            st.info("ไม่มีกิจกรรมล่าสุด")
            return
        
        # Display activities in timeline format
        for activity in activities[:10]:  # Show last 10 activities
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    st.markdown(f"**{activity['time']}**")
                
                with col2:
                    icon = self._get_activity_icon(activity['type'])
                    st.markdown(f"{icon} {activity['description']}")
                
                with col3:
                    st.markdown(f"*{activity['user']}*")
    
    @handle_errors
    def _render_projects_analytics(self):
        """Render projects analytics dashboard"""
        st.markdown("## 📁 วิเคราะห์โครงการ")
        
        # Project selector
        projects = self.project_manager.get_all_projects()
        project_names = ["ทุกโครงการ"] + [p["Name"] for p in projects]
        selected_project = st.selectbox(
            "เลือกโครงการ",
            options=project_names
        )
        
        # Project metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_projects = len(projects)
            st.metric("โครงการทั้งหมด", total_projects)
        
        with col2:
            active_projects = len([p for p in projects if p.get("Status") == "Active"])
            st.metric("โครงการที่ดำเนินการ", active_projects)
        
        with col3:
            completed_projects = len([p for p in projects if p.get("Status") == "Completed"])
            completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
            st.metric("อัตราเสร็จ", f"{completion_rate:.1f}%")
        
        with col4:
            on_time_projects = self._get_on_time_projects_count()
            st.metric("ตรงเวลา", f"{on_time_projects}/{total_projects}")
        
        st.markdown("---")
        
        # Project charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_project_timeline_chart()
            self._render_project_budget_analysis()
        
        with col2:
            self._render_project_resource_allocation()
            self._render_project_risk_assessment()
    
    @handle_errors
    def _render_teams_analytics(self):
        """Render teams analytics dashboard"""
        st.markdown("## 👥 วิเคราะห์ทีมงาน")
        
        # Team performance metrics
        self._render_team_performance_metrics()
        
        st.markdown("---")
        
        # Team charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_team_productivity_chart()
            self._render_team_collaboration_matrix()
        
        with col2:
            self._render_skill_distribution_chart()
            self._render_team_satisfaction_survey()
    
    @handle_errors
    def _render_performance_analytics(self):
        """Render performance analytics dashboard"""
        st.markdown("## ⚡ วิเคราะห์ประสิทธิภาพ")
        
        # Performance metrics
        self._render_performance_metrics()
        
        st.markdown("---")
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_kpi_trends_chart()
            self._render_team_performance_comparison()
        
        with col2:
            self._render_individual_performance_analysis()
            self._render_workload_distribution_chart()