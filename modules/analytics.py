#!/usr/bin/env python3
"""
modules/analytics.py
SDX Project Manager - Enterprise Analytics & Reporting System
Advanced data analytics with real-time metrics and comprehensive reporting
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """รายการประเภทรายงาน"""

    PROJECT_OVERVIEW = "project_overview"
    TASK_PERFORMANCE = "task_performance"
    RESOURCE_UTILIZATION = "resource_utilization"
    BUDGET_ANALYSIS = "budget_analysis"
    TEAM_PRODUCTIVITY = "team_productivity"
    TIMELINE_ANALYSIS = "timeline_analysis"
    QUALITY_METRICS = "quality_metrics"
    EXECUTIVE_SUMMARY = "executive_summary"


@dataclass
class MetricCard:
    """การ์ดแสดงตัวชี้วัด"""

    title: str
    value: Any
    delta: Optional[float] = None
    format_type: str = "number"  # number, percentage, currency, duration
    color: str = "blue"
    icon: str = "📊"


@dataclass
class ChartConfig:
    """การกำหนดค่าแผนภูมิ"""

    chart_type: str
    title: str
    x_column: str
    y_column: str
    color_column: Optional[str] = None
    additional_params: Dict[str, Any] = None


class AnalyticsEngine:
    """เครื่องมือวิเคราะห์ข้อมูลขั้นสูง"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.color_palette = [
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

    def get_project_overview_metrics(self) -> List[MetricCard]:
        """ดึงตัวชี้วัดภาพรวมโครงการ"""
        try:
            # ข้อมูลโครงการทั้งหมด
            projects_query = """
            SELECT 
                COUNT(*) as total_projects,
                SUM(CASE WHEN Status = 'Active' THEN 1 ELSE 0 END) as active_projects,
                SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as completed_projects,
                SUM(CASE WHEN Status = 'On Hold' THEN 1 ELSE 0 END) as on_hold_projects,
                AVG(CASE WHEN Budget > 0 THEN Budget ELSE NULL END) as avg_budget,
                SUM(CASE WHEN Budget > 0 THEN Budget ELSE 0 END) as total_budget,
                SUM(CASE WHEN ActualCost > 0 THEN ActualCost ELSE 0 END) as total_spent
            FROM Projects
            """
            project_data = self.db.fetch_one(projects_query)

            # ข้อมูลงาน
            tasks_query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN Status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                SUM(CASE WHEN Status = 'To Do' THEN 1 ELSE 0 END) as todo_tasks,
                AVG(CASE WHEN Progress > 0 THEN Progress ELSE NULL END) as avg_progress
            FROM Tasks
            """
            task_data = self.db.fetch_one(tasks_query)

            # คำนวณเปอร์เซ็นต์
            completion_rate = (
                (task_data["completed_tasks"] / task_data["total_tasks"] * 100)
                if task_data["total_tasks"] > 0
                else 0
            )
            budget_utilization = (
                (project_data["total_spent"] / project_data["total_budget"] * 100)
                if project_data["total_budget"] > 0
                else 0
            )

            return [
                MetricCard(
                    title="โครงการทั้งหมด",
                    value=project_data["total_projects"],
                    icon="📁",
                    color="blue",
                ),
                MetricCard(
                    title="โครงการที่ดำเนินงาน",
                    value=project_data["active_projects"],
                    icon="🚀",
                    color="green",
                ),
                MetricCard(
                    title="อัตราความสำเร็จงาน",
                    value=completion_rate,
                    format_type="percentage",
                    icon="✅",
                    color="success",
                ),
                MetricCard(
                    title="การใช้งบประมาณ",
                    value=budget_utilization,
                    format_type="percentage",
                    icon="💰",
                    color="warning" if budget_utilization > 80 else "info",
                ),
            ]

        except Exception as e:
            logger.error(f"Error getting overview metrics: {e}")
            return []

    def get_project_performance_data(self) -> pd.DataFrame:
        """ดึงข้อมูลประสิทธิภาพโครงการ"""
        try:
            query = """
            SELECT 
                p.ProjectName,
                p.Status,
                p.Priority,
                p.Budget,
                p.ActualCost,
                p.StartDate,
                p.EndDate,
                COUNT(t.TaskID) as total_tasks,
                SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                AVG(t.Progress) as avg_progress,
                CONCAT(u.FirstName, ' ', u.LastName) as manager_name
            FROM Projects p
            LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
            LEFT JOIN Users u ON p.ManagerID = u.UserID
            GROUP BY p.ProjectID, p.ProjectName, p.Status, p.Priority, 
                     p.Budget, p.ActualCost, p.StartDate, p.EndDate,
                     u.FirstName, u.LastName
            ORDER BY p.CreatedDate DESC
            """

            df = pd.DataFrame(self.db.fetch_all(query))

            if not df.empty:
                # คำนวณตัวชี้วัดเพิ่มเติม
                df["completion_rate"] = (
                    df["completed_tasks"] / df["total_tasks"] * 100
                ).fillna(0)
                df["budget_variance"] = (
                    (df["ActualCost"] - df["Budget"]) / df["Budget"] * 100
                ).fillna(0)
                df["is_overbudget"] = df["budget_variance"] > 0

                # แปลงวันที่
                df["StartDate"] = pd.to_datetime(df["StartDate"])
                df["EndDate"] = pd.to_datetime(df["EndDate"])
                df["duration_days"] = (df["EndDate"] - df["StartDate"]).dt.days

            return df

        except Exception as e:
            logger.error(f"Error getting project performance data: {e}")
            return pd.DataFrame()

    def get_task_analytics_data(self) -> pd.DataFrame:
        """ดึงข้อมูลวิเคราะห์งาน"""
        try:
            query = """
            SELECT 
                t.TaskTitle,
                t.Status,
                t.Priority,
                t.Progress,
                t.EstimatedHours,
                t.ActualHours,
                t.DueDate,
                t.CreatedDate,
                p.ProjectName,
                CONCAT(u.FirstName, ' ', u.LastName) as assigned_user
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            LEFT JOIN Users u ON t.AssignedUserID = u.UserID
            ORDER BY t.CreatedDate DESC
            """

            df = pd.DataFrame(self.db.fetch_all(query))

            if not df.empty:
                # คำนวณตัวชี้วัดงาน
                df["time_variance"] = df["ActualHours"] - df["EstimatedHours"]
                df["efficiency"] = (
                    df["EstimatedHours"] / df["ActualHours"] * 100
                ).fillna(100)
                df["is_overdue"] = pd.to_datetime(df["DueDate"]) < datetime.now()

                # แปลงวันที่
                df["DueDate"] = pd.to_datetime(df["DueDate"])
                df["CreatedDate"] = pd.to_datetime(df["CreatedDate"])
                df["age_days"] = (datetime.now() - df["CreatedDate"]).dt.days

            return df

        except Exception as e:
            logger.error(f"Error getting task analytics data: {e}")
            return pd.DataFrame()

    def create_project_status_chart(self, df: pd.DataFrame) -> go.Figure:
        """สร้างแผนภูมิสถานะโครงการ"""
        if df.empty:
            return go.Figure()

        status_counts = df["Status"].value_counts()

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=status_counts.index,
                    values=status_counts.values,
                    hole=0.4,
                    marker_colors=self.color_palette[: len(status_counts)],
                )
            ]
        )

        fig.update_layout(
            title="การกระจายสถานะโครงการ",
            font=dict(family="Sarabun", size=14),
            showlegend=True,
            height=400,
        )

        return fig

    def create_budget_analysis_chart(self, df: pd.DataFrame) -> go.Figure:
        """สร้างแผนภูมิวิเคราะห์งบประมาณ"""
        if df.empty:
            return go.Figure()

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("งบประมาณ vs ค่าใช้จ่ายจริง", "การเบี่ยงเบนงบประมาณ"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]],
        )

        # แผนภูมิเปรียบเทียบงบประมาณ
        fig.add_trace(
            go.Bar(
                name="งบประมาณ",
                x=df["ProjectName"],
                y=df["Budget"],
                marker_color="lightblue",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                name="ค่าใช้จ่ายจริง",
                x=df["ProjectName"],
                y=df["ActualCost"],
                marker_color="orange",
            ),
            row=1,
            col=1,
        )

        # แผนภูมิการเบี่ยงเบน
        colors = ["red" if x > 0 else "green" for x in df["budget_variance"]]
        fig.add_trace(
            go.Bar(
                name="เปอร์เซ็นต์เบี่ยงเบน",
                x=df["ProjectName"],
                y=df["budget_variance"],
                marker_color=colors,
            ),
            row=1,
            col=2,
        )

        fig.update_layout(
            title="การวิเคราะห์งบประมาณโครงการ",
            font=dict(family="Sarabun", size=12),
            height=500,
        )

        return fig

    def create_task_progress_chart(self, df: pd.DataFrame) -> go.Figure:
        """สร้างแผนภูมิความคืบหน้างาน"""
        if df.empty:
            return go.Figure()

        # สร้าง stacked bar chart สำหรับความคืบหน้า
        progress_by_project = (
            df.groupby(["ProjectName", "Status"]).size().unstack(fill_value=0)
        )

        fig = go.Figure()

        status_colors = {
            "To Do": "#ff7f7f",
            "In Progress": "#ffbb78",
            "Done": "#90ee90",
        }

        for status in progress_by_project.columns:
            fig.add_trace(
                go.Bar(
                    name=status,
                    x=progress_by_project.index,
                    y=progress_by_project[status],
                    marker_color=status_colors.get(status, "#1f77b4"),
                )
            )

        fig.update_layout(
            title="ความคืบหน้างานแยกตามโครงการ",
            xaxis_title="โครงการ",
            yaxis_title="จำนวนงาน",
            barmode="stack",
            font=dict(family="Sarabun", size=12),
            height=400,
        )

        return fig

    def create_team_productivity_chart(self) -> go.Figure:
        """สร้างแผนภูมิประสิทธิภาพทีม"""
        try:
            query = """
            SELECT 
                CONCAT(u.FirstName, ' ', u.LastName) as user_name,
                u.Department,
                COUNT(t.TaskID) as total_tasks,
                SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                AVG(t.Progress) as avg_progress,
                SUM(t.ActualHours) as total_hours
            FROM Users u
            LEFT JOIN Tasks t ON u.UserID = t.AssignedUserID
            WHERE u.IsActive = 1
            GROUP BY u.UserID, u.FirstName, u.LastName, u.Department
            HAVING COUNT(t.TaskID) > 0
            ORDER BY completed_tasks DESC
            """

            df = pd.DataFrame(self.db.fetch_all(query))

            if df.empty:
                return go.Figure()

            df["completion_rate"] = (
                df["completed_tasks"] / df["total_tasks"] * 100
            ).fillna(0)

            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=(
                    "งานที่เสร็จสิ้น",
                    "อัตราความสำเร็จ (%)",
                    "ชั่วโมงการทำงาน",
                    "ความคืบหน้าเฉลี่ย",
                ),
                specs=[
                    [{"type": "bar"}, {"type": "bar"}],
                    [{"type": "bar"}, {"type": "bar"}],
                ],
            )

            # งานที่เสร็จสิ้น
            fig.add_trace(
                go.Bar(
                    x=df["user_name"],
                    y=df["completed_tasks"],
                    name="งานเสร็จ",
                    marker_color="green",
                ),
                row=1,
                col=1,
            )

            # อัตราความสำเร็จ
            fig.add_trace(
                go.Bar(
                    x=df["user_name"],
                    y=df["completion_rate"],
                    name="อัตราสำเร็จ",
                    marker_color="blue",
                ),
                row=1,
                col=2,
            )

            # ชั่วโมงการทำงาน
            fig.add_trace(
                go.Bar(
                    x=df["user_name"],
                    y=df["total_hours"],
                    name="ชั่วโมง",
                    marker_color="orange",
                ),
                row=2,
                col=1,
            )

            # ความคืบหน้าเฉลี่ย
            fig.add_trace(
                go.Bar(
                    x=df["user_name"],
                    y=df["avg_progress"],
                    name="ความคืบหน้า",
                    marker_color="purple",
                ),
                row=2,
                col=2,
            )

            fig.update_layout(
                title="การวิเคราะห์ประสิทธิภาพทีมงาน",
                font=dict(family="Sarabun", size=10),
                height=600,
                showlegend=False,
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating team productivity chart: {e}")
            return go.Figure()

    def create_timeline_analysis(self) -> go.Figure:
        """สร้างแผนภูมิวิเคราะห์ไทม์ไลน์"""
        try:
            query = """
            SELECT 
                p.ProjectName,
                p.StartDate,
                p.EndDate,
                p.Status,
                p.Priority
            FROM Projects p
            WHERE p.StartDate IS NOT NULL AND p.EndDate IS NOT NULL
            ORDER BY p.StartDate
            """

            df = pd.DataFrame(self.db.fetch_all(query))

            if df.empty:
                return go.Figure()

            df["StartDate"] = pd.to_datetime(df["StartDate"])
            df["EndDate"] = pd.to_datetime(df["EndDate"])
            df["Duration"] = (df["EndDate"] - df["StartDate"]).dt.days

            # สีตามสถานะ
            status_colors = {
                "Active": "blue",
                "Completed": "green",
                "On Hold": "orange",
                "Cancelled": "red",
            }

            fig = go.Figure()

            for i, row in df.iterrows():
                fig.add_trace(
                    go.Scatter(
                        x=[row["StartDate"], row["EndDate"]],
                        y=[i, i],
                        mode="lines+markers",
                        name=row["ProjectName"],
                        line=dict(
                            color=status_colors.get(row["Status"], "gray"), width=8
                        ),
                        marker=dict(size=10),
                        hovertemplate=f"<b>{row['ProjectName']}</b><br>"
                        + f"เริ่ม: {row['StartDate'].strftime('%Y-%m-%d')}<br>"
                        + f"สิ้นสุด: {row['EndDate'].strftime('%Y-%m-%d')}<br>"
                        + f"ระยะเวลา: {row['Duration']} วัน<br>"
                        + f"สถานะ: {row['Status']}<extra></extra>",
                    )
                )

            fig.update_layout(
                title="ไทม์ไลน์โครงการ",
                xaxis_title="วันที่",
                yaxis=dict(
                    tickmode="array",
                    tickvals=list(range(len(df))),
                    ticktext=df["ProjectName"].tolist(),
                ),
                font=dict(family="Sarabun", size=12),
                height=max(400, len(df) * 50),
                showlegend=False,
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating timeline analysis: {e}")
            return go.Figure()

    def generate_executive_summary(self) -> Dict[str, Any]:
        """สร้างสรุปผู้บริหาร"""
        try:
            # ข้อมูลภาพรวม
            project_data = self.get_project_performance_data()
            task_data = self.get_task_analytics_data()

            summary = {
                "total_projects": len(project_data),
                "active_projects": len(
                    project_data[project_data["Status"] == "Active"]
                ),
                "completed_projects": len(
                    project_data[project_data["Status"] == "Completed"]
                ),
                "total_budget": (
                    project_data["Budget"].sum() if not project_data.empty else 0
                ),
                "total_spent": (
                    project_data["ActualCost"].sum() if not project_data.empty else 0
                ),
                "budget_utilization": 0,
                "avg_completion_rate": (
                    project_data["completion_rate"].mean()
                    if not project_data.empty
                    else 0
                ),
                "overdue_tasks": (
                    len(task_data[task_data["is_overdue"]])
                    if not task_data.empty
                    else 0
                ),
                "total_tasks": len(task_data),
                "key_insights": [],
                "recommendations": [],
            }

            # คำนวณการใช้งบประมาณ
            if summary["total_budget"] > 0:
                summary["budget_utilization"] = (
                    summary["total_spent"] / summary["total_budget"]
                ) * 100

            # สร้าง insights
            if summary["budget_utilization"] > 90:
                summary["key_insights"].append("การใช้งบประมาณใกล้หมดแล้ว")
                summary["recommendations"].append("ควรตรวจสอบและจัดการงบประมาณอย่างใกล้ชิด")

            if summary["avg_completion_rate"] < 70:
                summary["key_insights"].append("อัตราความสำเร็จต่ำกว่าเป้าหมาย")
                summary["recommendations"].append("ควรทบทวนแผนการทำงานและจัดสรรทรัพยากร")

            if summary["overdue_tasks"] > 0:
                summary["key_insights"].append(
                    f"มีงานเกินกำหนด {summary['overdue_tasks']} งาน"
                )
                summary["recommendations"].append("ควรเร่งรัดการทำงานที่เกินกำหนด")

            return summary

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {}

    def export_report_data(
        self, report_type: ReportType, date_range: Tuple[date, date] = None
    ) -> pd.DataFrame:
        """ส่งออกข้อมูลรายงาน"""
        try:
            if report_type == ReportType.PROJECT_OVERVIEW:
                return self.get_project_performance_data()
            elif report_type == ReportType.TASK_PERFORMANCE:
                return self.get_task_analytics_data()
            else:
                # สำหรับรายงานอื่นๆ
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error exporting report data: {e}")
            return pd.DataFrame()


class AdvancedAnalytics:
    """เครื่องมือวิเคราะห์ขั้นสูง"""

    def __init__(self, analytics_engine: AnalyticsEngine):
        self.engine = analytics_engine

    def predict_project_completion(self, project_id: int) -> Dict[str, Any]:
        """ทำนายความสำเร็จของโครงการ"""
        try:
            # ดึงข้อมูลโครงการและงาน
            query = """
            SELECT 
                p.*,
                COUNT(t.TaskID) as total_tasks,
                SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                AVG(t.Progress) as avg_progress,
                SUM(t.EstimatedHours) as total_estimated_hours,
                SUM(t.ActualHours) as total_actual_hours
            FROM Projects p
            LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
            WHERE p.ProjectID = ?
            GROUP BY p.ProjectID
            """

            data = self.engine.db.fetch_one(query, (project_id,))

            if not data:
                return {}

            # คำนวณการทำนาย
            completion_rate = (
                (data["completed_tasks"] / data["total_tasks"])
                if data["total_tasks"] > 0
                else 0
            )

            # ประมาณการวันที่เสร็จสิ้น
            if completion_rate > 0 and data["EndDate"]:
                start_date = datetime.strptime(str(data["StartDate"]), "%Y-%m-%d")
                end_date = datetime.strptime(str(data["EndDate"]), "%Y-%m-%d")
                total_duration = (end_date - start_date).days

                elapsed_days = (datetime.now() - start_date).days
                estimated_remaining_days = (
                    (total_duration - elapsed_days) / completion_rate
                    if completion_rate > 0
                    else total_duration
                )
                predicted_completion = datetime.now() + timedelta(
                    days=estimated_remaining_days
                )
            else:
                predicted_completion = None

            return {
                "project_name": data["ProjectName"],
                "completion_rate": completion_rate * 100,
                "predicted_completion_date": (
                    predicted_completion.strftime("%Y-%m-%d")
                    if predicted_completion
                    else None
                ),
                "is_on_track": completion_rate >= 0.8,
                "risk_level": (
                    "Low"
                    if completion_rate >= 0.8
                    else "Medium" if completion_rate >= 0.5 else "High"
                ),
            }

        except Exception as e:
            logger.error(f"Error predicting project completion: {e}")
            return {}

    def calculate_roi_metrics(self) -> Dict[str, float]:
        """คำนวณ ROI และตัวชี้วัดทางการเงิน"""
        try:
            query = """
            SELECT 
                SUM(Budget) as total_budget,
                SUM(ActualCost) as total_cost,
                COUNT(*) as total_projects,
                SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as completed_projects
            FROM Projects
            WHERE Budget > 0
            """

            data = self.engine.db.fetch_one(query)

            roi = (
                ((data["total_budget"] - data["total_cost"]) / data["total_cost"] * 100)
                if data["total_cost"] > 0
                else 0
            )
            success_rate = (
                (data["completed_projects"] / data["total_projects"] * 100)
                if data["total_projects"] > 0
                else 0
            )

            return {
                "roi_percentage": roi,
                "success_rate": success_rate,
                "cost_efficiency": (
                    (data["total_budget"] / data["total_cost"])
                    if data["total_cost"] > 0
                    else 0
                ),
                "avg_project_value": (
                    data["total_budget"] / data["total_projects"]
                    if data["total_projects"] > 0
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error calculating ROI metrics: {e}")
            return {}


def format_metric_value(value: Any, format_type: str) -> str:
    """จัดรูปแบบค่าตัวชี้วัด"""
    try:
        if format_type == "percentage":
            return f"{value:.1f}%"
        elif format_type == "currency":
            return f"฿{value:,.2f}"
        elif format_type == "duration":
            return f"{int(value)} วัน"
        elif format_type == "number":
            if isinstance(value, float):
                return f"{value:,.1f}"
            else:
                return f"{value:,}"
        else:
            return str(value)
    except:
        return str(value)


def display_metric_cards(metrics: List[MetricCard], cols: int = 4):
    """แสดงการ์ดตัวชี้วัด"""
    columns = st.columns(cols)

    for i, metric in enumerate(metrics):
        with columns[i % cols]:
            formatted_value = format_metric_value(metric.value, metric.format_type)

            # แสดงเปลี่ยนแปลง (delta) ถ้ามี
            delta_text = ""
            if metric.delta is not None:
                delta_text = f" ({metric.delta:+.1f}%)"

            st.metric(
                label=f"{metric.icon} {metric.title}",
                value=formatted_value,
                delta=delta_text if metric.delta else None,
            )


def create_analytics_dashboard(analytics_engine: AnalyticsEngine):
    """สร้างแดชบอร์ดการวิเคราะห์"""
    st.title("📊 การวิเคราะห์และรายงาน")

    # Sidebar สำหรับการกรอง
    with st.sidebar:
        st.subheader("🔍 ตัวกรองข้อมูล")

        # เลือกช่วงวันที่
        date_range = st.date_input(
            "ช่วงเวลา",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            key="analytics_date_range",
        )

        # เลือกประเภทรายงาน
        report_type = st.selectbox(
            "ประเภทรายงาน",
            options=[e.value for e in ReportType],
            format_func=lambda x: {
                "project_overview": "📁 ภาพรวมโครงการ",
                "task_performance": "✅ ประสิทธิภาพงาน",
                "resource_utilization": "👥 การใช้ทรัพยากร",
                "budget_analysis": "💰 การวิเคราะห์งบประมาณ",
                "team_productivity": "🚀 ประสิทธิภาพทีม",
                "timeline_analysis": "📅 การวิเคราะห์ไทม์ไลน์",
                "quality_metrics": "⭐ ตัวชี้วัดคุณภาพ",
                "executive_summary": "📋 สรุปผู้บริหาร",
            }.get(x, x),
        )

        # ปุ่มรีเฟรชข้อมูล
        if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # แสดงตัวชี้วัดหลัก
    st.subheader("📈 ตัวชี้วัดหลัก")
    overview_metrics = analytics_engine.get_project_overview_metrics()

    if overview_metrics:
        display_metric_cards(overview_metrics)
    else:
        st.warning("ไม่พบข้อมูลตัวชี้วัด")

    st.divider()

    # แสดงรายงานตามประเภทที่เลือก
    if report_type == ReportType.PROJECT_OVERVIEW.value:
        show_project_overview_report(analytics_engine)
    elif report_type == ReportType.TASK_PERFORMANCE.value:
        show_task_performance_report(analytics_engine)
    elif report_type == ReportType.BUDGET_ANALYSIS.value:
        show_budget_analysis_report(analytics_engine)
    elif report_type == ReportType.TEAM_PRODUCTIVITY.value:
        show_team_productivity_report(analytics_engine)
    elif report_type == ReportType.TIMELINE_ANALYSIS.value:
        show_timeline_analysis_report(analytics_engine)
    elif report_type == ReportType.EXECUTIVE_SUMMARY.value:
        show_executive_summary_report(analytics_engine)


def show_project_overview_report(analytics_engine: AnalyticsEngine):
    """แสดงรายงานภาพรวมโครงการ"""
    st.subheader("📁 รายงานภาพรวมโครงการ")

    # ดึงข้อมูลโครงการ
    project_data = analytics_engine.get_project_performance_data()

    if project_data.empty:
        st.warning("ไม่พบข้อมูลโครงการ")
        return

    col1, col2 = st.columns(2)

    with col1:
        # แผนภูมิสถานะโครงการ
        status_chart = analytics_engine.create_project_status_chart(project_data)
        st.plotly_chart(status_chart, use_container_width=True)

    with col2:
        # แผนภูมิความคืบหน้า
        progress_chart = analytics_engine.create_task_progress_chart(
            analytics_engine.get_task_analytics_data()
        )
        st.plotly_chart(progress_chart, use_container_width=True)

    # ตารางข้อมูลโครงการ
    st.subheader("📋 รายละเอียดโครงการ")

    # เตรียมข้อมูลสำหรับแสดง
    display_columns = [
        "ProjectName",
        "Status",
        "Priority",
        "completion_rate",
        "Budget",
        "ActualCost",
        "budget_variance",
        "manager_name",
    ]

    if all(col in project_data.columns for col in display_columns):
        display_data = project_data[display_columns].copy()

        # จัดรูปแบบข้อมูล
        display_data["completion_rate"] = display_data["completion_rate"].apply(
            lambda x: f"{x:.1f}%"
        )
        display_data["Budget"] = display_data["Budget"].apply(
            lambda x: f"฿{x:,.2f}" if pd.notna(x) else "ไม่ระบุ"
        )
        display_data["ActualCost"] = display_data["ActualCost"].apply(
            lambda x: f"฿{x:,.2f}" if pd.notna(x) else "฿0.00"
        )
        display_data["budget_variance"] = display_data["budget_variance"].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "0.0%"
        )

        # เปลี่ยนชื่อคอลัมน์เป็นภาษาไทย
        display_data.columns = [
            "ชื่อโครงการ",
            "สถานะ",
            "ความสำคัญ",
            "ความคืบหน้า",
            "งบประมาณ",
            "ค่าใช้จ่ายจริง",
            "การเบี่ยงเบน",
            "ผู้จัดการโครงการ",
        ]

        st.dataframe(display_data, use_container_width=True, hide_index=True)


def show_task_performance_report(analytics_engine: AnalyticsEngine):
    """แสดงรายงานประสิทธิภาพงาน"""
    st.subheader("✅ รายงานประสิทธิภาพงาน")

    task_data = analytics_engine.get_task_analytics_data()

    if task_data.empty:
        st.warning("ไม่พบข้อมูลงาน")
        return

    # สถิติงาน
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_tasks = len(task_data)
        st.metric("📝 งานทั้งหมด", f"{total_tasks:,}")

    with col2:
        completed_tasks = len(task_data[task_data["Status"] == "Done"])
        st.metric("✅ งานเสร็จสิ้น", f"{completed_tasks:,}")

    with col3:
        overdue_tasks = (
            len(task_data[task_data["is_overdue"]])
            if "is_overdue" in task_data.columns
            else 0
        )
        st.metric("⏰ งานเกินกำหนด", f"{overdue_tasks:,}")

    with col4:
        avg_efficiency = (
            task_data["efficiency"].mean() if "efficiency" in task_data.columns else 100
        )
        st.metric("📊 ประสิทธิภาพเฉลี่ย", f"{avg_efficiency:.1f}%")

    # แผนภูมิสถานะงาน
    status_counts = task_data["Status"].value_counts()
    fig_status = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="การกระจายสถานะงาน",
    )
    fig_status.update_layout(font=dict(family="Sarabun"))
    st.plotly_chart(fig_status, use_container_width=True)

    # แผนภูมิความสำคัญงาน
    priority_counts = task_data["Priority"].value_counts()
    fig_priority = px.bar(
        x=priority_counts.index,
        y=priority_counts.values,
        title="จำนวนงานตามระดับความสำคัญ",
        color=priority_counts.values,
        color_continuous_scale="Reds",
    )
    fig_priority.update_layout(
        xaxis_title="ระดับความสำคัญ", yaxis_title="จำนวนงาน", font=dict(family="Sarabun")
    )
    st.plotly_chart(fig_priority, use_container_width=True)


def show_budget_analysis_report(analytics_engine: AnalyticsEngine):
    """แสดงรายงานการวิเคราะห์งบประมาณ"""
    st.subheader("💰 การวิเคราะห์งบประมาณ")

    project_data = analytics_engine.get_project_performance_data()

    if project_data.empty:
        st.warning("ไม่พบข้อมูลงบประมาณ")
        return

    # แผนภูมิวิเคราะห์งบประมาณ
    budget_chart = analytics_engine.create_budget_analysis_chart(project_data)
    st.plotly_chart(budget_chart, use_container_width=True)

    # สรุปการใช้งบประมาณ
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 สรุปงบประมาณ")
        total_budget = project_data["Budget"].sum()
        total_spent = project_data["ActualCost"].sum()
        remaining_budget = total_budget - total_spent
        utilization_rate = (total_spent / total_budget * 100) if total_budget > 0 else 0

        st.metric("💼 งบประมาณทั้งหมด", f"฿{total_budget:,.2f}")
        st.metric("💸 ใช้ไปแล้ว", f"฿{total_spent:,.2f}")
        st.metric("💰 เหลืออยู่", f"฿{remaining_budget:,.2f}")
        st.metric("📈 อัตราการใช้", f"{utilization_rate:.1f}%")

    with col2:
        st.subheader("⚠️ โครงการเกินงบประมาณ")
        overbudget_projects = (
            project_data[project_data["is_overbudget"] == True]
            if "is_overbudget" in project_data.columns
            else pd.DataFrame()
        )

        if not overbudget_projects.empty:
            for _, project in overbudget_projects.iterrows():
                st.error(
                    f"🚨 {project['ProjectName']}: เกินงบ {project['budget_variance']:.1f}%"
                )
        else:
            st.success("✅ ไม่มีโครงการที่เกินงบประมาณ")


def show_team_productivity_report(analytics_engine: AnalyticsEngine):
    """แสดงรายงานประสิทธิภาพทีม"""
    st.subheader("🚀 รายงานประสิทธิภาพทีม")

    # แผนภูมิประสิทธิภาพทีม
    team_chart = analytics_engine.create_team_productivity_chart()
    st.plotly_chart(team_chart, use_container_width=True)

    # ข้อมูลทีมงาน
    try:
        query = """
        SELECT 
            u.Department,
            COUNT(DISTINCT u.UserID) as team_size,
            COUNT(t.TaskID) as total_tasks,
            SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
            AVG(t.Progress) as avg_progress
        FROM Users u
        LEFT JOIN Tasks t ON u.UserID = t.AssignedUserID
        WHERE u.IsActive = 1
        GROUP BY u.Department
        ORDER BY completed_tasks DESC
        """

        team_data = pd.DataFrame(analytics_engine.db.fetch_all(query))

        if not team_data.empty:
            team_data["completion_rate"] = (
                team_data["completed_tasks"] / team_data["total_tasks"] * 100
            ).fillna(0)

            # แสดงตารางประสิทธิภาพแผนก
            st.subheader("📋 ประสิทธิภาพตามแผนก")

            display_data = team_data.copy()
            display_data["completion_rate"] = display_data["completion_rate"].apply(
                lambda x: f"{x:.1f}%"
            )
            display_data["avg_progress"] = display_data["avg_progress"].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
            )

            display_data.columns = [
                "แผนก",
                "จำนวนคน",
                "งานทั้งหมด",
                "งานเสร็จ",
                "ความคืบหน้าเฉลี่ย",
                "อัตราความสำเร็จ",
            ]
            st.dataframe(display_data, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลทีม: {e}")


def show_timeline_analysis_report(analytics_engine: AnalyticsEngine):
    """แสดงรายงานการวิเคราะห์ไทม์ไลน์"""
    st.subheader("📅 การวิเคราะห์ไทม์ไลน์โครงการ")

    # แผนภูมิไทม์ไลน์
    timeline_chart = analytics_engine.create_timeline_analysis()
    st.plotly_chart(timeline_chart, use_container_width=True)

    # การวิเคราะห์ขั้นสูง
    advanced_analytics = AdvancedAnalytics(analytics_engine)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔮 การทำนายโครงการ")

        # เลือกโครงการสำหรับทำนาย
        try:
            projects_query = (
                "SELECT ProjectID, ProjectName FROM Projects WHERE Status = 'Active'"
            )
            active_projects = analytics_engine.db.fetch_all(projects_query)

            if active_projects:
                project_options = {
                    p["ProjectName"]: p["ProjectID"] for p in active_projects
                }
                selected_project = st.selectbox(
                    "เลือกโครงการ", options=list(project_options.keys())
                )

                if selected_project and st.button("🔍 ทำนายผล"):
                    prediction = advanced_analytics.predict_project_completion(
                        project_options[selected_project]
                    )

                    if prediction:
                        st.success(
                            f"📊 ความคืบหน้า: {prediction['completion_rate']:.1f}%"
                        )
                        if prediction["predicted_completion_date"]:
                            st.info(
                                f"📅 คาดว่าจะเสร็จ: {prediction['predicted_completion_date']}"
                            )
                        st.write(f"⚠️ ระดับความเสี่ยง: {prediction['risk_level']}")
            else:
                st.info("ไม่มีโครงการที่กำลังดำเนินงาน")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")

    with col2:
        st.subheader("💹 ตัวชี้วัดทางการเงิน")

        roi_metrics = advanced_analytics.calculate_roi_metrics()

        if roi_metrics:
            st.metric("📈 ROI", f"{roi_metrics['roi_percentage']:.1f}%")
            st.metric("✅ อัตราความสำเร็จ", f"{roi_metrics['success_rate']:.1f}%")
            st.metric("⚡ ประสิทธิภาพต้นทุน", f"{roi_metrics['cost_efficiency']:.2f}")
            st.metric(
                "💎 มูลค่าเฉลี่ย/โครงการ", f"฿{roi_metrics['avg_project_value']:,.2f}"
            )


def show_executive_summary_report(analytics_engine: AnalyticsEngine):
    """แสดงสรุปรายงานผู้บริหาร"""
    st.subheader("📋 สรุปรายงานผู้บริหาร")

    summary = analytics_engine.generate_executive_summary()

    if not summary:
        st.warning("ไม่สามารถสร้างรายงานสรุปได้")
        return

    # ข้อมูลภาพรวม
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📁 โครงการทั้งหมด", summary["total_projects"])

    with col2:
        st.metric("🚀 โครงการที่ดำเนินงาน", summary["active_projects"])

    with col3:
        st.metric("✅ โครงการเสร็จสิ้น", summary["completed_projects"])

    with col4:
        st.metric("⏰ งานเกินกำหนด", summary["overdue_tasks"])

    # ข้อมูลทางการเงิน
    st.subheader("💰 สรุปทางการเงิน")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💼 งบประมาณรวม", f"฿{summary['total_budget']:,.2f}")

    with col2:
        st.metric("💸 ใช้ไปแล้ว", f"฿{summary['total_spent']:,.2f}")

    with col3:
        st.metric("📊 อัตราการใช้งบ", f"{summary['budget_utilization']:.1f}%")

    # ข้อมูลเชิงลึกและคำแนะนำ
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔍 ข้อมูลเชิงลึก")
        if summary["key_insights"]:
            for insight in summary["key_insights"]:
                st.info(f"💡 {insight}")
        else:
            st.success("✅ ไม่พบประเด็นที่ต้องเฝ้าระวัง")

    with col2:
        st.subheader("📝 คำแนะนำ")
        if summary["recommendations"]:
            for recommendation in summary["recommendations"]:
                st.warning(f"🎯 {recommendation}")
        else:
            st.success("✅ การดำเนินงานเป็นไปตามแผน")

    # ปุ่มส่งออกรายงาน
    st.divider()
    st.subheader("📤 ส่งออกรายงาน")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 ส่งออก Excel", use_container_width=True):
            # ส่งออกข้อมูลเป็น Excel
            project_data = analytics_engine.export_report_data(
                ReportType.PROJECT_OVERVIEW
            )
            if not project_data.empty:
                st.download_button(
                    label="💾 ดาวน์โหลด Project Report.xlsx",
                    data=project_data.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"project_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )

    with col2:
        if st.button("📋 ส่งออก PDF", use_container_width=True):
            st.info("คุณสมบัตินี้จะพัฒนาในเวอร์ชันต่อไป")

    with col3:
        if st.button("📧 ส่งอีเมล", use_container_width=True):
            st.info("คุณสมบัตินี้จะพัฒนาในเวอร์ชันต่อไป")
