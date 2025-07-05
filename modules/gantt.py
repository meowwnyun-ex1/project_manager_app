#!/usr/bin/env python3
"""
modules/gantt.py
Professional Gantt Chart Module for DENSO Project Manager Pro
Advanced timeline visualization with interactive features
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import numpy as np
from dataclasses import dataclass
import json

from utils.ui_components import UIComponents
from utils.error_handler import safe_execute, handle_error
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


@dataclass
class GanttItem:
    """Gantt chart item data structure"""

    id: str
    name: str
    start_date: date
    end_date: date
    completion: float
    priority: str
    status: str
    resource: str
    dependencies: List[str]
    category: str
    color: str = None
    description: str = ""
    milestones: List[Dict] = None


class GanttChartManager:
    """Professional Gantt Chart Manager with advanced features"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.ui = UIComponents()
        self.color_schemes = {
            "status": {
                "Planning": "#94a3b8",
                "In Progress": "#3b82f6",
                "On Hold": "#f59e0b",
                "Completed": "#10b981",
                "Cancelled": "#ef4444",
            },
            "priority": {
                "Low": "#10b981",
                "Medium": "#3b82f6",
                "High": "#f59e0b",
                "Critical": "#ef4444",
            },
            "department": {
                "Innovation": "#8b5cf6",
                "Engineering": "#06b6d4",
                "Quality": "#10b981",
                "Manufacturing": "#f59e0b",
                "Research": "#ec4899",
            },
        }

    @monitor_performance("gantt_data_load", "gantt")
    def get_gantt_data(
        self,
        project_id: Optional[int] = None,
        date_range: Optional[Tuple[date, date]] = None,
    ) -> List[GanttItem]:
        """Load and prepare Gantt chart data"""
        try:
            # Base query for projects and tasks
            if project_id:
                projects_query = """
                    SELECT ProjectID, Name, StartDate, EndDate, Status, Priority, 
                           CompletionPercentage, ManagerID, ClientName, Description
                    FROM Projects 
                    WHERE ProjectID = ? AND Status != 'Cancelled'
                """
                projects = self.db.execute_query(projects_query, (project_id,))
            else:
                projects_query = """
                    SELECT ProjectID, Name, StartDate, EndDate, Status, Priority,
                           CompletionPercentage, ManagerID, ClientName, Description
                    FROM Projects 
                    WHERE Status != 'Cancelled'
                """
                projects = self.db.execute_query(projects_query)

            gantt_items = []

            # Process projects
            for project in projects:
                if not project["StartDate"] or not project["EndDate"]:
                    continue

                # Apply date range filter if specified
                if date_range:
                    start_filter, end_filter = date_range
                    if (
                        project["EndDate"] < start_filter
                        or project["StartDate"] > end_filter
                    ):
                        continue

                # Get project manager name
                manager_query = """
                    SELECT FirstName + ' ' + LastName as ManagerName 
                    FROM Users WHERE UserID = ?
                """
                manager_result = self.db.execute_query(
                    manager_query, (project["ManagerID"],)
                )
                manager_name = (
                    manager_result[0]["ManagerName"] if manager_result else "Unassigned"
                )

                # Create project item
                project_item = GanttItem(
                    id=f"project_{project['ProjectID']}",
                    name=f"📁 {project['Name']}",
                    start_date=(
                        project["StartDate"].date()
                        if isinstance(project["StartDate"], datetime)
                        else project["StartDate"]
                    ),
                    end_date=(
                        project["EndDate"].date()
                        if isinstance(project["EndDate"], datetime)
                        else project["EndDate"]
                    ),
                    completion=project.get("CompletionPercentage", 0),
                    priority=project.get("Priority", "Medium"),
                    status=project.get("Status", "Planning"),
                    resource=manager_name,
                    dependencies=[],
                    category="Project",
                    color=self.color_schemes["status"].get(
                        project.get("Status", "Planning")
                    ),
                    description=project.get("Description", ""),
                    milestones=[],
                )
                gantt_items.append(project_item)

                # Get tasks for this project
                tasks_query = """
                    SELECT t.TaskID, t.Title, t.StartDate, t.DueDate, t.Status, 
                           t.Priority, t.CompletionPercentage, t.Dependencies,
                           t.Description, t.EstimatedHours, t.ActualHours,
                           u.FirstName + ' ' + u.LastName as AssigneeName,
                           u.Department
                    FROM Tasks t
                    LEFT JOIN Users u ON t.AssignedToID = u.UserID
                    WHERE t.ProjectID = ? AND t.Status != 'Cancelled'
                    ORDER BY t.DueDate
                """
                tasks = self.db.execute_query(tasks_query, (project["ProjectID"],))

                for task in tasks:
                    if not task["DueDate"]:
                        continue

                    # Use StartDate if available, otherwise use project start date
                    task_start = task["StartDate"]
                    if not task_start:
                        task_start = project["StartDate"]

                    if isinstance(task_start, datetime):
                        task_start = task_start.date()
                    if isinstance(task["DueDate"], datetime):
                        task_due = task["DueDate"].date()
                    else:
                        task_due = task["DueDate"]

                    # Parse dependencies
                    dependencies = []
                    if task.get("Dependencies"):
                        try:
                            dep_ids = task["Dependencies"].split(",")
                            dependencies = [
                                f"task_{dep.strip()}" for dep in dep_ids if dep.strip()
                            ]
                        except:
                            dependencies = []

                    # Create task item
                    task_item = GanttItem(
                        id=f"task_{task['TaskID']}",
                        name=f"   ✓ {task['Title']}",
                        start_date=task_start,
                        end_date=task_due,
                        completion=task.get("CompletionPercentage", 0),
                        priority=task.get("Priority", "Medium"),
                        status=task.get("Status", "To Do"),
                        resource=task.get("AssigneeName", "Unassigned"),
                        dependencies=dependencies,
                        category="Task",
                        color=self.color_schemes["status"].get(
                            task.get("Status", "To Do")
                        ),
                        description=task.get("Description", ""),
                        milestones=[],
                    )
                    gantt_items.append(task_item)

            return gantt_items

        except Exception as e:
            logger.error(f"Error loading Gantt data: {e}")
            return []

    def create_interactive_gantt(
        self, gantt_items: List[GanttItem], view_mode: str = "months"
    ) -> go.Figure:
        """Create interactive Gantt chart with advanced features"""
        if not gantt_items:
            return self.create_empty_gantt()

        try:
            # Prepare data for Plotly
            df_data = []

            for item in gantt_items:
                # Calculate duration
                duration = (item.end_date - item.start_date).days + 1

                # Create hover text
                hover_text = f"""
                <b>{item.name}</b><br>
                <b>ระยะเวลา:</b> {item.start_date.strftime('%d/%m/%Y')} - {item.end_date.strftime('%d/%m/%Y')}<br>
                <b>ความคืบหน้า:</b> {item.completion}%<br>
                <b>สถานะ:</b> {item.status}<br>
                <b>ความสำคัญ:</b> {item.priority}<br>
                <b>ผู้รับผิดชอบ:</b> {item.resource}<br>
                <b>ระยะเวลา:</b> {duration} วัน
                """

                if item.description:
                    hover_text += f"<br><b>รายละเอียด:</b> {item.description[:100]}..."

                df_data.append(
                    {
                        "Task": item.name,
                        "Start": item.start_date,
                        "Finish": item.end_date,
                        "Completion": item.completion,
                        "Status": item.status,
                        "Priority": item.priority,
                        "Resource": item.resource,
                        "Category": item.category,
                        "Color": item.color,
                        "Duration": duration,
                        "Hover": hover_text,
                        "ID": item.id,
                    }
                )

            df = pd.DataFrame(df_data)

            # Create figure
            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Status",
                color_discrete_map=self.color_schemes["status"],
                hover_name="Task",
                hover_data={
                    "Start": True,
                    "Finish": True,
                    "Completion": True,
                    "Resource": True,
                    "Priority": True,
                    "Duration": True,
                },
                title="📈 Gantt Chart - Project Timeline",
            )

            # Enhance layout
            fig.update_layout(
                height=max(600, len(df) * 40),
                font=dict(family="Inter, sans-serif", size=12),
                title_font_size=20,
                title_font_color="#1e3c72",
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                xaxis=dict(
                    title="Timeline",
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.1)",
                    gridwidth=1,
                ),
                yaxis=dict(
                    title="",
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.1)",
                    gridwidth=1,
                    autorange="reversed",
                ),
                plot_bgcolor="white",
                paper_bgcolor="white",
            )

            # Add completion percentage annotations
            for i, row in df.iterrows():
                if row["Completion"] > 0:
                    # Calculate position for completion indicator
                    total_duration = (row["Finish"] - row["Start"]).days + 1
                    completed_duration = total_duration * (row["Completion"] / 100)
                    completion_date = row["Start"] + timedelta(days=completed_duration)

                    fig.add_shape(
                        type="line",
                        x0=completion_date,
                        x1=completion_date,
                        y0=i - 0.4,
                        y1=i + 0.4,
                        line=dict(color="rgba(0,0,0,0.6)", width=3),
                        layer="above",
                    )

                    # Add completion percentage text
                    fig.add_annotation(
                        x=completion_date,
                        y=i,
                        text=f"{row['Completion']:.0f}%",
                        showarrow=False,
                        font=dict(color="white", size=10, family="Inter"),
                        bgcolor="rgba(0,0,0,0.7)",
                        bordercolor="white",
                        borderwidth=1,
                    )

            # Add today line
            today = datetime.now().date()
            fig.add_vline(
                x=today,
                line_dash="dash",
                line_color="red",
                line_width=2,
                annotation_text="วันนี้",
                annotation_position="top",
            )

            # Add milestone markers if any
            self.add_milestones_to_gantt(fig, gantt_items)

            return fig

        except Exception as e:
            logger.error(f"Error creating Gantt chart: {e}")
            return self.create_empty_gantt()

    def create_empty_gantt(self) -> go.Figure:
        """Create empty Gantt chart placeholder"""
        fig = go.Figure()

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text="ไม่มีข้อมูลสำหรับแสดง Gantt Chart<br>กรุณาเลือกโครงการหรือช่วงเวลาที่มีข้อมูล",
            showarrow=False,
            font=dict(size=16, color="gray"),
            align="center",
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        return fig

    def add_milestones_to_gantt(
        self, fig: go.Figure, gantt_items: List[GanttItem]
    ) -> None:
        """Add milestone markers to Gantt chart"""
        try:
            for item in gantt_items:
                if item.milestones:
                    for milestone in item.milestones:
                        milestone_date = milestone.get("date")
                        milestone_name = milestone.get("name", "Milestone")

                        if milestone_date:
                            fig.add_scatter(
                                x=[milestone_date],
                                y=[item.name],
                                mode="markers",
                                marker=dict(
                                    symbol="diamond",
                                    size=15,
                                    color="gold",
                                    line=dict(color="orange", width=2),
                                ),
                                name=milestone_name,
                                hovertemplate=f"<b>{milestone_name}</b><br>วันที่: {milestone_date}<extra></extra>",
                                showlegend=False,
                            )
        except Exception as e:
            logger.error(f"Error adding milestones: {e}")

    def create_resource_timeline(self, gantt_items: List[GanttItem]) -> go.Figure:
        """Create resource utilization timeline"""
        try:
            # Group by resource
            resource_data = {}

            for item in gantt_items:
                if item.resource not in resource_data:
                    resource_data[item.resource] = []

                resource_data[item.resource].append(
                    {
                        "name": item.name,
                        "start": item.start_date,
                        "end": item.end_date,
                        "status": item.status,
                        "category": item.category,
                    }
                )

            fig = go.Figure()

            colors = px.colors.qualitative.Set3
            y_pos = 0

            for resource, tasks in resource_data.items():
                color_idx = y_pos % len(colors)

                for task in tasks:
                    fig.add_trace(
                        go.Scatter(
                            x=[task["start"], task["end"]],
                            y=[resource, resource],
                            mode="lines",
                            line=dict(color=colors[color_idx], width=8),
                            name=task["name"],
                            hovertemplate=f"<b>{task['name']}</b><br>ผู้รับผิดชอบ: {resource}<br>ระยะเวลา: {task['start']} - {task['end']}<extra></extra>",
                            showlegend=False,
                        )
                    )

                y_pos += 1

            fig.update_layout(
                title="📊 Resource Utilization Timeline",
                xaxis_title="Timeline",
                yaxis_title="Resources",
                height=max(400, len(resource_data) * 60),
                font=dict(family="Inter, sans-serif"),
                title_font_size=18,
                title_font_color="#1e3c72",
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating resource timeline: {e}")
            return self.create_empty_gantt()

    def create_critical_path_analysis(
        self, gantt_items: List[GanttItem]
    ) -> Dict[str, Any]:
        """Analyze critical path and bottlenecks"""
        try:
            analysis = {
                "critical_tasks": [],
                "bottlenecks": [],
                "resource_conflicts": [],
                "timeline_risks": [],
            }

            # Find overdue items
            today = date.today()

            for item in gantt_items:
                # Critical tasks (high priority, not completed, due soon)
                if (
                    item.priority in ["High", "Critical"]
                    and item.completion < 100
                    and item.end_date <= today + timedelta(days=7)
                ):
                    analysis["critical_tasks"].append(
                        {
                            "name": item.name,
                            "due_date": item.end_date,
                            "completion": item.completion,
                            "days_remaining": (item.end_date - today).days,
                        }
                    )

                # Timeline risks (overdue or at risk)
                if item.end_date < today and item.completion < 100:
                    analysis["timeline_risks"].append(
                        {
                            "name": item.name,
                            "due_date": item.end_date,
                            "days_overdue": (today - item.end_date).days,
                            "completion": item.completion,
                        }
                    )

            # Resource conflicts (same person assigned to overlapping tasks)
            resource_tasks = {}
            for item in gantt_items:
                if item.resource not in resource_tasks:
                    resource_tasks[item.resource] = []
                resource_tasks[item.resource].append(item)

            for resource, tasks in resource_tasks.items():
                if len(tasks) > 1:
                    # Check for overlapping tasks
                    for i, task1 in enumerate(tasks):
                        for task2 in tasks[i + 1 :]:
                            if (
                                task1.start_date <= task2.end_date
                                and task2.start_date <= task1.end_date
                            ):
                                analysis["resource_conflicts"].append(
                                    {
                                        "resource": resource,
                                        "task1": task1.name,
                                        "task2": task2.name,
                                        "overlap_start": max(
                                            task1.start_date, task2.start_date
                                        ),
                                        "overlap_end": min(
                                            task1.end_date, task2.end_date
                                        ),
                                    }
                                )

            return analysis

        except Exception as e:
            logger.error(f"Error in critical path analysis: {e}")
            return {}

    def export_gantt_data(
        self, gantt_items: List[GanttItem], format: str = "excel"
    ) -> bytes:
        """Export Gantt data to various formats"""
        try:
            # Prepare data for export
            export_data = []

            for item in gantt_items:
                export_data.append(
                    {
                        "ID": item.id,
                        "Name": item.name,
                        "Category": item.category,
                        "Start Date": item.start_date.strftime("%Y-%m-%d"),
                        "End Date": item.end_date.strftime("%Y-%m-%d"),
                        "Duration (Days)": (item.end_date - item.start_date).days + 1,
                        "Completion (%)": item.completion,
                        "Status": item.status,
                        "Priority": item.priority,
                        "Resource": item.resource,
                        "Dependencies": ", ".join(item.dependencies),
                        "Description": item.description,
                    }
                )

            df = pd.DataFrame(export_data)

            if format.lower() == "excel":
                return df.to_excel(index=False)
            elif format.lower() == "csv":
                return df.to_csv(index=False).encode("utf-8")
            else:
                return df.to_json(orient="records").encode("utf-8")

        except Exception as e:
            logger.error(f"Error exporting Gantt data: {e}")
            return b""


def show_gantt_page(project_manager, task_manager):
    """Show professional Gantt chart page"""
    ui = UIComponents()

    # Page header with breadcrumbs
    ui.render_page_header(
        "📈 Gantt Chart",
        "Professional Project Timeline & Resource Management",
        "📈",
        breadcrumbs=["Dashboard", "Project Management", "Gantt Chart"],
    )

    # Initialize Gantt manager
    gantt_manager = GanttChartManager(project_manager.db)

    # Sidebar controls
    with st.sidebar:
        st.markdown("### ⚙️ การตั้งค่า Gantt Chart")

        # Project filter
        projects = safe_execute(project_manager.get_all_projects, default_return=[])
        project_options = {"ทุกโครงการ": None}
        project_options.update({p["Name"]: p["ProjectID"] for p in projects})

        selected_project_name = st.selectbox(
            "เลือกโครงการ",
            options=list(project_options.keys()),
            help="เลือกโครงการที่ต้องการดู Gantt Chart",
        )
        selected_project_id = project_options[selected_project_name]

        # Date range filter
        st.markdown("#### 📅 ช่วงเวลา")
        use_date_filter = st.checkbox("กรองตามช่วงเวลา")

        date_range = None
        if use_date_filter:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "เริ่มต้น", value=date.today() - timedelta(days=30)
                )
            with col2:
                end_date = st.date_input(
                    "สิ้นสุด", value=date.today() + timedelta(days=90)
                )
            date_range = (start_date, end_date)

        # View options
        st.markdown("#### 👁️ ตัวเลือกการแสดงผล")

        view_mode = st.selectbox(
            "มุมมอง",
            options=["weeks", "months", "quarters"],
            index=1,
            format_func=lambda x: {
                "weeks": "รายสัปดาห์",
                "months": "รายเดือน",
                "quarters": "รายไตรมาส",
            }[x],
        )

        show_completion = st.checkbox("แสดงความคืบหน้า", value=True)
        show_resources = st.checkbox("แสดง Resource Timeline", value=False)
        show_critical_path = st.checkbox("วิเคราะห์ Critical Path", value=False)

        # Export options
        st.markdown("#### 📤 ส่งออกข้อมูล")
        export_format = st.selectbox(
            "รูปแบบไฟล์",
            options=["excel", "csv", "json"],
            format_func=lambda x: {
                "excel": "Excel (.xlsx)",
                "csv": "CSV (.csv)",
                "json": "JSON (.json)",
            }[x],
        )

        if st.button("📥 ส่งออกข้อมูล", use_container_width=True):
            st.info("ฟีเจอร์ส่งออกข้อมูลจะทำงานหลังจากสร้าง Gantt Chart")

    # Main content area
    # Load Gantt data
    with st.spinner("📊 กำลังโหลดข้อมูล Gantt Chart..."):
        gantt_items = gantt_manager.get_gantt_data(
            project_id=selected_project_id, date_range=date_range
        )

    if not gantt_items:
        ui.render_empty_state(
            "ไม่มีข้อมูลโครงการหรืองานในช่วงเวลาที่เลือก",
            "📈",
            "สร้างโครงการใหม่",
            lambda: st.session_state.update({"current_page": "projects"}),
        )
        return

    # Summary metrics
    st.markdown("### 📊 สรุปข้อมูล")

    # Calculate summary statistics
    total_projects = len([item for item in gantt_items if item.category == "Project"])
    total_tasks = len([item for item in gantt_items if item.category == "Task"])
    avg_completion = np.mean([item.completion for item in gantt_items])

    overdue_items = [
        item
        for item in gantt_items
        if item.end_date < date.today() and item.completion < 100
    ]

    ui.render_enhanced_metric_cards(
        [
            {
                "title": "โครงการ",
                "value": total_projects,
                "icon": "📁",
                "help": "จำนวนโครงการทั้งหมดใน Gantt Chart",
            },
            {
                "title": "งาน",
                "value": total_tasks,
                "icon": "✅",
                "help": "จำนวนงานทั้งหมดใน Gantt Chart",
            },
            {
                "title": "ความคืบหน้าเฉลี่ย",
                "value": f"{avg_completion:.1f}%",
                "icon": "📈",
                "delta": "ดี" if avg_completion >= 70 else "ต้องปรับปรุง",
                "delta_color": "normal" if avg_completion >= 70 else "inverse",
                "help": "ความคืบหน้าเฉลี่ยของโครงการและงาน",
            },
            {
                "title": "เลยกำหนด",
                "value": len(overdue_items),
                "icon": "⏰",
                "delta": f"-{len(overdue_items)}" if overdue_items else "0",
                "delta_color": "inverse" if overdue_items else "normal",
                "help": "จำนวนงานที่เลยกำหนดแล้ว",
            },
        ]
    )

    # Main Gantt Chart
    st.markdown("### 📈 Gantt Chart")

    with ui.render_chart_container(
        lambda: None, loading_text="กำลังสร้าง Gantt Chart..."
    ):
        gantt_fig = gantt_manager.create_interactive_gantt(gantt_items, view_mode)
        st.plotly_chart(gantt_fig, use_container_width=True)

    # Additional views based on sidebar selections
    if show_resources:
        st.markdown("### 👥 Resource Timeline")
        with ui.render_chart_container(
            lambda: None, loading_text="กำลังสร้าง Resource Timeline..."
        ):
            resource_fig = gantt_manager.create_resource_timeline(gantt_items)
            st.plotly_chart(resource_fig, use_container_width=True)

    if show_critical_path:
        st.markdown("### 🎯 Critical Path Analysis")

        analysis = gantt_manager.create_critical_path_analysis(gantt_items)

        if analysis:
            # Create tabs for different analysis views
            tab1, tab2, tab3 = st.tabs(
                ["🚨 Critical Tasks", "⚠️ Timeline Risks", "👥 Resource Conflicts"]
            )

            with tab1:
                if analysis.get("critical_tasks"):
                    ui.render_data_table(
                        analysis["critical_tasks"],
                        title="งานที่ต้องให้ความสำคัญ",
                        columns=["name", "due_date", "completion", "days_remaining"],
                    )
                else:
                    ui.render_empty_state("ไม่มีงานที่ต้องให้ความสำคัญเร่งด่วน", "✅")

            with tab2:
                if analysis.get("timeline_risks"):
                    ui.render_data_table(
                        analysis["timeline_risks"],
                        title="งานที่มีความเสี่ยงด้านเวลา",
                        columns=["name", "due_date", "days_overdue", "completion"],
                    )
                else:
                    ui.render_empty_state("ไม่มีงานที่มีความเสี่ยงด้านเวลา", "⏰")

            with tab3:
                if analysis.get("resource_conflicts"):
                    ui.render_data_table(
                        analysis["resource_conflicts"],
                        title="ความขัดแย้งการใช้ทรัพยากร",
                        columns=[
                            "resource",
                            "task1",
                            "task2",
                            "overlap_start",
                            "overlap_end",
                        ],
                    )
                else:
                    ui.render_empty_state("ไม่มีความขัดแย้งการใช้ทรัพยากร", "👥")

    # Detailed task list
    with st.expander("📋 รายละเอียดงานทั้งหมด", expanded=False):
        # Convert gantt items to table format
        table_data = []
        for item in gantt_items:
            duration = (item.end_date - item.start_date).days + 1
            table_data.append(
                {
                    "ชื่อ": item.name,
                    "ประเภท": item.category,
                    "วันเริ่มต้น": item.start_date.strftime("%d/%m/%Y"),
                    "วันสิ้นสุด": item.end_date.strftime("%d/%m/%Y"),
                    "ระยะเวลา (วัน)": duration,
                    "ความคืบหน้า (%)": f"{item.completion:.1f}%",
                    "สถานะ": item.status,
                    "ความสำคัญ": item.priority,
                    "ผู้รับผิดชอบ": item.resource,
                }
            )

        if table_data:
            ui.render_data_table(
                table_data,
                title="รายละเอียดงานทั้งหมดใน Gantt Chart",
                search=True,
                pagination=True,
                export=True,
                page_size=15,
            )

    # Quick actions
    st.markdown("### ⚡ การกระทำด่วน")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📁 สร้างโครงการใหม่", use_container_width=True):
            st.session_state.current_page = "projects"
            st.session_state.show_create_form = True
            st.rerun()

    with col2:
        if st.button("✅ สร้างงานใหม่", use_container_width=True):
            st.session_state.current_page = "tasks"
            st.session_state.show_create_form = True
            st.rerun()

    with col3:
        if st.button("📊 ดูรายงาน", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()

    with col4:
        if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
            st.rerun()

    # Tips and help section
    with st.expander("💡 เคล็ดลับการใช้งาน Gantt Chart", expanded=False):
        st.markdown(
            """
        **📈 การอ่าน Gantt Chart:**
        - แถบสีแสดงสถานะของงาน (เขียว = เสร็จ, น้ำเงิน = กำลังทำ, เหลือง = รอ, แดง = ยกเลิก)
        - เส้นดำแสดงความคืบหน้าปัจจุบัน
        - เส้นประสีแดงแสดงวันปัจจุบัน
        - สัญลักษณ์เพชรสีทองแสดง Milestone สำคัญ
        
        **🎯 การใช้งานขั้นสูง:**
        - คลิกลากเพื่อซูมช่วงเวลาที่ต้องการ
        - Hover เหนือแถบเพื่อดูรายละเอียด
        - ใช้ตัวกรองในแถบข้างเพื่อแสดงข้อมูลที่ต้องการ
        - ส่งออกข้อมูลเป็น Excel, CSV หรือ JSON
        
        **⚠️ สิ่งที่ควรระวัง:**
        - งานสีแดงคือเลยกำหนดแล้ว ต้องเร่งดำเนินการ
        - Resource Conflict หมายถึงคนเดียวกันได้รับมอบหมายงานที่ทับซ้อนกัน
        - Critical Path คืองานที่มีผลต่อกำหนดเวลาของโครงการโดยรวม
        """
        )
