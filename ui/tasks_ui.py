#!/usr/bin/env python3
"""
tasks_ui.py
SDX Project Manager - Enterprise Task Management Interface
Professional Kanban board, task tracking, and comprehensive task management
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date, time
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import json

# Import project modules
from tasks import TaskManager, TaskStatus, TaskPriority, TaskType, WorkType
from projects import ProjectManager
from users import UserManager
from ui_components import UIComponents, ThemeManager
from error_handler import ErrorHandler, handle_errors

logger = logging.getLogger(__name__)


class TaskViewMode(Enum):
    """Task view modes"""

    KANBAN = "kanban"
    LIST = "list"
    CALENDAR = "calendar"
    TIMELINE = "timeline"


class TaskFilter(Enum):
    """Task filter types"""

    ALL = "all"
    MY_TASKS = "my_tasks"
    OVERDUE = "overdue"
    THIS_WEEK = "this_week"
    HIGH_PRIORITY = "high_priority"
    BLOCKED = "blocked"


@dataclass
class TaskUIConfig:
    """Task UI configuration"""

    auto_refresh: bool = True
    refresh_interval: int = 60  # seconds
    kanban_columns: List[str] = None
    show_avatars: bool = True
    show_time_tracking: bool = True
    drag_drop_enabled: bool = True

    def __post_init__(self):
        if self.kanban_columns is None:
            self.kanban_columns = [
                "Backlog",
                "To Do",
                "In Progress",
                "Review",
                "Testing",
                "Done",
            ]


class TasksUI:
    """Enterprise Task Management Interface"""

    def __init__(self, db_manager, theme_manager: ThemeManager):
        self.db = db_manager
        self.task_manager = TaskManager(db_manager)
        self.project_manager = ProjectManager(db_manager)
        self.user_manager = UserManager(db_manager)
        self.theme = theme_manager
        self.ui_components = UIComponents(theme_manager)
        self.error_handler = ErrorHandler()
        self.config = TaskUIConfig()

    @handle_errors
    def render_tasks_page(self):
        """Main tasks page renderer"""
        st.markdown("# ✅ จัดการงาน")

        # Page header with controls
        self._render_page_header()

        # View mode selector
        view_mode = self._render_view_selector()

        # Main content based on view mode
        if view_mode == TaskViewMode.KANBAN:
            self._render_kanban_board()
        elif view_mode == TaskViewMode.LIST:
            self._render_task_list()
        elif view_mode == TaskViewMode.CALENDAR:
            self._render_task_calendar()
        elif view_mode == TaskViewMode.TIMELINE:
            self._render_task_timeline()

    def _render_page_header(self):
        """Render page header with controls"""
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.markdown("### 📋 จัดการและติดตามงานทั้งหมด")

        with col2:
            if st.button("➕ สร้างงานใหม่", type="primary"):
                self._show_create_task_modal()

        with col3:
            if st.button("📊 สถิติงาน"):
                self._show_task_analytics()

        with col4:
            if st.button("⚙️ ตั้งค่า"):
                self._show_task_settings()

    def _render_view_selector(self) -> TaskViewMode:
        """Render view mode selector"""
        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            # Filter selector
            filter_option = st.selectbox(
                "🔍 กรอง",
                options=[
                    "ทั้งหมด",
                    "งานของฉัน",
                    "เลยกำหนด",
                    "สัปดาห์นี้",
                    "ความสำคัญสูง",
                    "งานติดขัด",
                ],
                key="task_filter",
            )

            # Store filter in session state
            st.session_state.task_filter = self._map_filter_option(filter_option)

        with col2:
            # Project selector
            projects = self.project_manager.get_all_projects()
            project_names = ["ทุกโครงการ"] + [p["Name"] for p in projects]
            selected_project = st.selectbox(
                "📁 โครงการ", options=project_names, key="project_filter"
            )

            if selected_project != "ทุกโครงการ":
                project_id = next(
                    (p["ID"] for p in projects if p["Name"] == selected_project), None
                )
                st.session_state.selected_project_id = project_id
            else:
                st.session_state.selected_project_id = None

        with col3:
            # View mode selector
            view_mode = st.selectbox(
                "👁️ มุมมอง",
                options=["📋 Kanban", "📝 รายการ", "📅 ปฏิทิน", "📈 ไทม์ไลน์"],
                key="view_mode",
            )

            return self._map_view_mode(view_mode)

    def _map_filter_option(self, option: str) -> TaskFilter:
        """Map filter option to enum"""
        mapping = {
            "ทั้งหมด": TaskFilter.ALL,
            "งานของฉัน": TaskFilter.MY_TASKS,
            "เลยกำหนด": TaskFilter.OVERDUE,
            "สัปดาห์นี้": TaskFilter.THIS_WEEK,
            "ความสำคัญสูง": TaskFilter.HIGH_PRIORITY,
            "งานติดขัด": TaskFilter.BLOCKED,
        }
        return mapping.get(option, TaskFilter.ALL)

    def _map_view_mode(self, option: str) -> TaskViewMode:
        """Map view mode option to enum"""
        mapping = {
            "📋 Kanban": TaskViewMode.KANBAN,
            "📝 รายการ": TaskViewMode.LIST,
            "📅 ปฏิทิน": TaskViewMode.CALENDAR,
            "📈 ไทม์ไลน์": TaskViewMode.TIMELINE,
        }
        return mapping.get(option, TaskViewMode.KANBAN)

    @handle_errors
    def _render_kanban_board(self):
        """Render Kanban board view"""
        st.markdown("---")
        st.markdown("### 📋 Kanban Board")

        # Get filtered tasks
        tasks = self._get_filtered_tasks()

        if not tasks:
            st.info("ไม่มีงานที่ตรงกับเงื่อนไข")
            return

        # Organize tasks by status
        kanban_data = self._organize_tasks_by_status(tasks)

        # Render Kanban columns
        columns = st.columns(len(self.config.kanban_columns))

        for idx, status in enumerate(self.config.kanban_columns):
            with columns[idx]:
                self._render_kanban_column(status, kanban_data.get(status, []))

    def _render_kanban_column(self, status: str, tasks: List[Dict[str, Any]]):
        """Render individual Kanban column"""
        # Column header
        task_count = len(tasks)
        header_color = self._get_status_color(status)

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, {header_color}20, {header_color}40); 
                        padding: 10px; border-radius: 10px; margin-bottom: 10px; 
                        border-left: 4px solid {header_color};">
                <h4 style="margin: 0; color: {header_color};">
                    {status} ({task_count})
                </h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tasks in column
        for task in tasks:
            self._render_task_card(task)

        # Add task button
        if st.button(f"➕ เพิ่มงานใน {status}", key=f"add_task_{status}"):
            self._show_quick_task_form(status)

    def _render_task_card(self, task: Dict[str, Any]):
        """Render individual task card"""
        # Determine card styling
        priority_color = self._get_priority_color(task["Priority"])
        is_overdue = self._is_task_overdue(task)

        # Card styling
        card_style = f"""
        background: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 4px solid {priority_color};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        """

        if is_overdue:
            card_style += "border: 2px solid #ff4444;"

        with st.container():
            st.markdown(f'<div style="{card_style}">', unsafe_allow_html=True)

            # Task title and priority
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{task['Title']}**")
            with col2:
                priority_badge = self.ui_components.render_priority_badge(
                    task["Priority"]
                )
                st.markdown(priority_badge, unsafe_allow_html=True)

            # Task details
            if task.get("Description"):
                description = (
                    task["Description"][:50] + "..."
                    if len(task["Description"]) > 50
                    else task["Description"]
                )
                st.markdown(f"*{description}*")

            # Task metadata
            col1, col2 = st.columns(2)
            with col1:
                if task.get("AssignedToName"):
                    st.markdown(f"👤 {task['AssignedToName']}")
                if task.get("DueDate"):
                    due_date = task["DueDate"].strftime("%d/%m/%Y")
                    st.markdown(f"📅 {due_date}")

            with col2:
                if task.get("EstimatedHours"):
                    st.markdown(f"⏱️ {task['EstimatedHours']}h")
                if task.get("ProjectName"):
                    st.markdown(f"📁 {task['ProjectName']}")

            # Progress bar
            if task.get("ProgressPercentage"):
                progress = task["ProgressPercentage"] / 100
                st.progress(progress)
                st.markdown(
                    f"<small>{task['ProgressPercentage']}% สำเร็จ</small>",
                    unsafe_allow_html=True,
                )

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("👁️", key=f"view_{task['ID']}", help="ดูรายละเอียด"):
                    self._show_task_details(task["ID"])
            with col2:
                if st.button("✏️", key=f"edit_{task['ID']}", help="แก้ไข"):
                    self._show_edit_task_modal(task["ID"])
            with col3:
                if st.button("⏱️", key=f"time_{task['ID']}", help="บันทึกเวลา"):
                    self._show_time_tracking_modal(task["ID"])

            st.markdown("</div>", unsafe_allow_html=True)

    def _render_task_list(self):
        """Render list view of tasks"""
        st.markdown("---")
        st.markdown("### 📝 รายการงาน")

        # Get filtered tasks
        tasks = self._get_filtered_tasks()

        if not tasks:
            st.info("ไม่มีงานที่ตรงกับเงื่อนไข")
            return

        # Search functionality
        search_term = st.text_input(
            "🔍 ค้นหางาน", placeholder="ชื่องาน, รายละเอียด, ผู้รับผิดชอบ..."
        )

        # Filter tasks by search
        if search_term:
            tasks = [
                t
                for t in tasks
                if search_term.lower() in t["Title"].lower()
                or (
                    t.get("Description")
                    and search_term.lower() in t["Description"].lower()
                )
                or (
                    t.get("AssignedToName")
                    and search_term.lower() in t["AssignedToName"].lower()
                )
            ]

        # Sort options
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "เรียงตาม", options=["วันที่สร้าง", "กำหนดส่ง", "ความสำคัญ", "สถานะ", "ชื่องาน"]
            )
        with col2:
            sort_order = st.selectbox("ลำดับ", options=["ล่าสุดก่อน", "เก่าสุดก่อน"])

        # Sort tasks
        tasks = self._sort_tasks(tasks, sort_by, sort_order)

        # Pagination
        items_per_page = 20
        total_pages = (len(tasks) + items_per_page - 1) // items_per_page

        if total_pages > 1:
            page = st.selectbox("หน้า", options=list(range(1, total_pages + 1)), index=0)
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            tasks = tasks[start_idx:end_idx]

        # Render task table
        self._render_task_table(tasks)

    def _render_task_table(self, tasks: List[Dict[str, Any]]):
        """Render tasks in table format"""
        if not tasks:
            return

        # Create DataFrame
        df_data = []
        for task in tasks:
            df_data.append(
                {
                    "ID": task["ID"],
                    "ชื่องาน": task["Title"],
                    "โครงการ": task.get("ProjectName", "N/A"),
                    "ผู้รับผิดชอบ": task.get("AssignedToName", "N/A"),
                    "สถานะ": task["Status"],
                    "ความสำคัญ": task["Priority"],
                    "กำหนดส่ง": (
                        task["DueDate"].strftime("%d/%m/%Y")
                        if task.get("DueDate")
                        else "N/A"
                    ),
                    "ความคืบหน้า": f"{task.get('ProgressPercentage', 0)}%",
                    "เวลาประมาณ": f"{task.get('EstimatedHours', 0)}h",
                    "เวลาจริง": f"{task.get('ActualHours', 0)}h",
                }
            )

        df = pd.DataFrame(df_data)

        # Configure column display
        column_config = {
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "ชื่องาน": st.column_config.TextColumn("ชื่องาน", width="large"),
            "โครงการ": st.column_config.TextColumn("โครงการ", width="medium"),
            "ผู้รับผิดชอบ": st.column_config.TextColumn("ผู้รับผิดชอบ", width="medium"),
            "สถานะ": st.column_config.TextColumn("สถานะ", width="small"),
            "ความสำคัญ": st.column_config.TextColumn("ความสำคัญ", width="small"),
            "กำหนดส่ง": st.column_config.TextColumn("กำหนดส่ง", width="small"),
            "ความคืบหน้า": st.column_config.TextColumn("ความคืบหน้า", width="small"),
            "เวลาประมาณ": st.column_config.TextColumn("เวลาประมาณ", width="small"),
            "เวลาจริง": st.column_config.TextColumn("เวลาจริง", width="small"),
        }

        # Display table with selection
        selected_rows = st.dataframe(
            df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

        # Bulk actions for selected rows
        if selected_rows and len(selected_rows.selection.rows) > 0:
            self._render_bulk_actions(selected_rows.selection.rows, tasks)

    def _render_bulk_actions(
        self, selected_indices: List[int], tasks: List[Dict[str, Any]]
    ):
        """Render bulk action buttons"""
        st.markdown("### การดำเนินการแบบกลุ่ม")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✅ อัพเดทสถานะ"):
                self._show_bulk_status_update(selected_indices, tasks)

        with col2:
            if st.button("👤 มอบหมาย"):
                self._show_bulk_assignment(selected_indices, tasks)

        with col3:
            if st.button("📅 กำหนดเวลา"):
                self._show_bulk_due_date_update(selected_indices, tasks)

        with col4:
            if st.button("🗑️ ลบ", type="secondary"):
                self._show_bulk_delete_confirmation(selected_indices, tasks)

    def _render_task_calendar(self):
        """Render calendar view of tasks"""
        st.markdown("---")
        st.markdown("### 📅 ปฏิทินงาน")

        # Calendar implementation would go here
        # This is a placeholder for calendar functionality
        st.info("🚧 การแสดงผลแบบปฏิทินจะพัฒนาในเวอร์ชันถัดไป")

        # Show tasks by date
        tasks = self._get_filtered_tasks()
        tasks_by_date = self._group_tasks_by_date(tasks)

        # Simple date-based display
        for task_date, date_tasks in tasks_by_date.items():
            with st.expander(f"📅 {task_date} ({len(date_tasks)} งาน)"):
                for task in date_tasks:
                    self._render_task_summary(task)

    def _render_task_timeline(self):
        """Render timeline view of tasks"""
        st.markdown("---")
        st.markdown("### 📈 ไทม์ไลน์งาน")

        # Get tasks with dates
        tasks = self._get_filtered_tasks()
        tasks_with_dates = [t for t in tasks if t.get("DueDate")]

        if not tasks_with_dates:
            st.info("ไม่มีงานที่มีกำหนดส่งเพื่อแสดงในไทม์ไลน์")
            return

        # Create timeline chart
        self._render_timeline_chart(tasks_with_dates)

    def _render_timeline_chart(self, tasks: List[Dict[str, Any]]):
        """Render Gantt-style timeline chart"""
        # Prepare data for timeline
        timeline_data = []

        for task in tasks:
            start_date = task.get("CreatedDate", datetime.now())
            end_date = task.get("DueDate", datetime.now())

            timeline_data.append(
                {
                    "Task": task["Title"],
                    "Start": start_date,
                    "Finish": end_date,
                    "Resource": task.get("AssignedToName", "ไม่ระบุ"),
                    "Status": task["Status"],
                    "Priority": task["Priority"],
                }
            )

        # Create Gantt chart
        if timeline_data:
            df = pd.DataFrame(timeline_data)

            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Status",
                title="ไทม์ไลน์งาน",
                hover_data=["Resource", "Priority"],
            )

            fig.update_layout(
                height=max(400, len(tasks) * 30), xaxis_title="เวลา", yaxis_title="งาน"
            )

            st.plotly_chart(fig, use_container_width=True)

    # Helper methods
    def _get_filtered_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks based on current filters"""
        try:
            # Build filters
            filters = {}

            # Project filter
            if (
                hasattr(st.session_state, "selected_project_id")
                and st.session_state.selected_project_id
            ):
                filters["project_id"] = st.session_state.selected_project_id

            # Task filter
            task_filter = getattr(st.session_state, "task_filter", TaskFilter.ALL)

            if task_filter == TaskFilter.MY_TASKS:
                current_user = st.session_state.get("user_data", {})
                filters["assigned_to"] = current_user.get("UserID")
            elif task_filter == TaskFilter.OVERDUE:
                filters["overdue_only"] = True
            elif task_filter == TaskFilter.THIS_WEEK:
                filters["this_week"] = True
            elif task_filter == TaskFilter.HIGH_PRIORITY:
                filters["priority"] = "High"
            elif task_filter == TaskFilter.BLOCKED:
                filters["status"] = "Blocked"

            # Get tasks
            return self.task_manager.get_all_tasks(filters)

        except Exception as e:
            logger.error(f"Error getting filtered tasks: {e}")
            st.error("เกิดข้อผิดพลาดในการโหลดข้อมูลงาน")
            return []

    def _organize_tasks_by_status(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Organize tasks by status for Kanban board"""
        organized = {status: [] for status in self.config.kanban_columns}

        for task in tasks:
            status = task["Status"]
            if status in organized:
                organized[status].append(task)

        return organized

    def _get_status_color(self, status: str) -> str:
        """Get color for task status"""
        colors = {
            "Backlog": "#6c757d",
            "To Do": "#007bff",
            "In Progress": "#ffc107",
            "Review": "#fd7e14",
            "Testing": "#20c997",
            "Done": "#28a745",
            "Blocked": "#dc3545",
            "Cancelled": "#6c757d",
        }
        return colors.get(status, "#6c757d")

    def _get_priority_color(self, priority: str) -> str:
        """Get color for task priority"""
        colors = {
            "Low": "#28a745",
            "Medium": "#ffc107",
            "High": "#fd7e14",
            "Critical": "#dc3545",
        }
        return colors.get(priority, "#6c757d")

    def _is_task_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if task is overdue"""
        if not task.get("DueDate"):
            return False

        return task["DueDate"] < datetime.now().date() and task["Status"] not in [
            "Done",
            "Cancelled",
        ]

    def _sort_tasks(
        self, tasks: List[Dict[str, Any]], sort_by: str, sort_order: str
    ) -> List[Dict[str, Any]]:
        """Sort tasks based on criteria"""
        reverse = sort_order == "ล่าสุดก่อน"

        if sort_by == "วันที่สร้าง":
            return sorted(
                tasks, key=lambda x: x.get("CreatedDate", datetime.min), reverse=reverse
            )
        elif sort_by == "กำหนดส่ง":
            return sorted(
                tasks, key=lambda x: x.get("DueDate", date.max), reverse=reverse
            )
        elif sort_by == "ความสำคัญ":
            priority_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            return sorted(
                tasks,
                key=lambda x: priority_order.get(x["Priority"], 0),
                reverse=reverse,
            )
        elif sort_by == "สถานะ":
            return sorted(tasks, key=lambda x: x["Status"], reverse=reverse)
        elif sort_by == "ชื่องาน":
            return sorted(tasks, key=lambda x: x["Title"], reverse=reverse)

        return tasks

    def _group_tasks_by_date(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group tasks by due date"""
        grouped = {}

        for task in tasks:
            if task.get("DueDate"):
                date_str = task["DueDate"].strftime("%d/%m/%Y")
                if date_str not in grouped:
                    grouped[date_str] = []
                grouped[date_str].append(task)

        return dict(sorted(grouped.items()))

    def _render_task_summary(self, task: Dict[str, Any]):
        """Render brief task summary"""
        priority_badge = self.ui_components.render_priority_badge(task["Priority"])
        status_badge = self.ui_components.render_status_badge(task["Status"])

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{task['Title']}**")
            if task.get("AssignedToName"):
                st.markdown(f"👤 {task['AssignedToName']}")

        with col2:
            st.markdown(priority_badge, unsafe_allow_html=True)

        with col3:
            st.markdown(status_badge, unsafe_allow_html=True)

    # Modal functions (placeholders for detailed implementations)
    def _show_create_task_modal(self):
        """Show create task modal"""
        # Implementation would be here
        st.info("🚧 ฟีเจอร์สร้างงานจะพัฒนาในขั้นตอนถัดไป")

    def _show_edit_task_modal(self, task_id: int):
        """Show edit task modal"""
        st.info(f"🚧 ฟีเจอร์แก้ไขงาน ID: {task_id} จะพัฒนาในขั้นตอนถัดไป")

    def _show_task_details(self, task_id: int):
        """Show detailed task view"""
        st.info(f"🚧 ฟีเจอร์ดูรายละเอียดงาน ID: {task_id} จะพัฒนาในขั้นตอนถัดไป")

    def _show_time_tracking_modal(self, task_id: int):
        """Show time tracking modal"""
        st.info(f"🚧 ฟีเจอร์บันทึกเวลา ID: {task_id} จะพัฒนาในขั้นตอนถัดไป")

    def _show_quick_task_form(self, status: str):
        """Show quick task creation form"""
        st.info(f"🚧 ฟีเจอร์สร้างงานเร็วในสถานะ {status} จะพัฒนาในขั้นตอนถัดไป")

    def _show_task_analytics(self):
        """Show task analytics"""
        st.info("🚧 ฟีเจอร์สถิติงานจะพัฒนาในขั้นตอนถัดไป")

    def _show_task_settings(self):
        """Show task settings"""
        st.info("🚧 ฟีเจอร์ตั้งค่างานจะพัฒนาในขั้นตอนถัดไป")

    # Bulk action methods (placeholders)
    def _show_bulk_status_update(
        self, selected_indices: List[int], tasks: List[Dict[str, Any]]
    ):
        """Show bulk status update modal"""
        st.info("🚧 ฟีเจอร์อัพเดทสถานะแบบกลุ่มจะพัฒนาในขั้นตอนถัดไป")

    def _show_bulk_assignment(
        self, selected_indices: List[int], tasks: List[Dict[str, Any]]
    ):
        """Show bulk assignment modal"""
        st.info("🚧 ฟีเจอร์มอบหมายงานแบบกลุ่มจะพัฒนาในขั้นตอนถัดไป")

    def _show_bulk_due_date_update(
        self, selected_indices: List[int], tasks: List[Dict[str, Any]]
    ):
        """Show bulk due date update modal"""
        st.info("🚧 ฟีเจอร์กำหนดเวลาแบบกลุ่มจะพัฒนาในขั้นตอนถัดไป")

    def _show_bulk_delete_confirmation(
        self, selected_indices: List[int], tasks: List[Dict[str, Any]]
    ):
        """Show bulk delete confirmation"""
        st.info("🚧 ฟีเจอร์ลบงานแบบกลุ่มจะพัฒนาในขั้นตอนถัดไป")


# Main render function
def render_tasks_ui(db_manager, theme_manager: ThemeManager):
    """Main function to render tasks UI"""
    try:
        tasks_ui = TasksUI(db_manager, theme_manager)
        tasks_ui.render_tasks_page()
    except Exception as e:
        logger.error(f"Error rendering tasks UI: {e}")
        st.error("เกิดข้อผิดพลาดในการแสดงผลหน้าจัดการงาน")


# Advanced Task Management Components
class AdvancedTaskComponents:
    """Advanced task management components"""

    def __init__(self, db_manager, theme_manager: ThemeManager):
        self.db = db_manager
        self.task_manager = TaskManager(db_manager)
        self.theme = theme_manager
        self.ui_components = UIComponents(theme_manager)

    def render_task_dependencies_view(self, task_id: int):
        """Render task dependencies visualization"""
        st.markdown("### 🔗 การพึ่งพาระหว่างงาน")

        # Get task dependencies
        dependencies = self.task_manager.get_task_dependencies(task_id)

        if not dependencies:
            st.info("งานนี้ไม่มีการพึ่งพาระหว่างงานอื่น")
            return

        # Create dependency graph
        self._render_dependency_graph(dependencies)

    def _render_dependency_graph(self, dependencies: List[Dict[str, Any]]):
        """Render dependency graph using Plotly"""
        # Implementation for dependency visualization
        st.info("🚧 กราฟการพึ่งพาระหว่างงานจะพัฒนาในเวอร์ชันถัดไป")

    def render_time_tracking_dashboard(self, user_id: Optional[int] = None):
        """Render time tracking dashboard"""
        st.markdown("### ⏱️ แดชบอร์ดบันทึกเวลา")

        # Time tracking metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            today_hours = self._get_today_hours(user_id)
            st.metric("เวลาวันนี้", f"{today_hours:.1f}h")

        with col2:
            week_hours = self._get_week_hours(user_id)
            st.metric("เวลาสัปดาห์นี้", f"{week_hours:.1f}h")

        with col3:
            month_hours = self._get_month_hours(user_id)
            st.metric("เวลาเดือนนี้", f"{month_hours:.1f}h")

        with col4:
            efficiency = self._get_efficiency_ratio(user_id)
            st.metric("ประสิทธิภาพ", f"{efficiency:.1%}")

        # Time tracking chart
        self._render_time_tracking_chart(user_id)

    def _get_today_hours(self, user_id: Optional[int]) -> float:
        """Get hours logged today"""
        # Implementation for getting today's hours
        return 6.5  # Placeholder

    def _get_week_hours(self, user_id: Optional[int]) -> float:
        """Get hours logged this week"""
        # Implementation for getting week's hours
        return 32.5  # Placeholder

    def _get_month_hours(self, user_id: Optional[int]) -> float:
        """Get hours logged this month"""
        # Implementation for getting month's hours
        return 145.0  # Placeholder

    def _get_efficiency_ratio(self, user_id: Optional[int]) -> float:
        """Get efficiency ratio (actual vs estimated)"""
        # Implementation for calculating efficiency
        return 0.85  # Placeholder

    def _render_time_tracking_chart(self, user_id: Optional[int]):
        """Render time tracking chart"""
        # Generate sample data for demonstration
        dates = pd.date_range(start="2024-01-01", end="2024-01-14", freq="D")
        hours = np.random.uniform(4, 10, len(dates))

        fig = px.bar(
            x=dates,
            y=hours,
            title="บันทึกเวลาในช่วง 2 สัปดาห์ที่ผ่านมา",
            labels={"x": "วันที่", "y": "ชั่วโมง"},
        )

        fig.update_layout(xaxis_title="วันที่", yaxis_title="ชั่วโมง", showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

    def render_task_workload_analysis(self):
        """Render workload analysis for team members"""
        st.markdown("### 📊 การวิเคราะห์ภาระงาน")

        # Get team workload data
        workload_data = self._get_team_workload_data()

        if not workload_data:
            st.info("ไม่มีข้อมูลภาระงานในขณะนี้")
            return

        # Create workload chart
        fig = go.Figure()

        members = [w["member_name"] for w in workload_data]
        current_load = [w["current_hours"] for w in workload_data]
        capacity = [w["capacity_hours"] for w in workload_data]

        fig.add_trace(
            go.Bar(
                name="ภาระงานปัจจุบัน", x=members, y=current_load, marker_color="lightblue"
            )
        )

        fig.add_trace(
            go.Bar(name="ความสามารถ", x=members, y=capacity, marker_color="darkblue")
        )

        fig.update_layout(
            title="การเปรียบเทียบภาระงานกับความสามารถ",
            xaxis_title="สมาชิกทีม",
            yaxis_title="ชั่วโมง",
            barmode="group",
        )

        st.plotly_chart(fig, use_container_width=True)

        # Workload recommendations
        self._render_workload_recommendations(workload_data)

    def _get_team_workload_data(self) -> List[Dict[str, Any]]:
        """Get team workload data"""
        # Sample data - replace with actual implementation
        return [
            {"member_name": "สมชาย", "current_hours": 35, "capacity_hours": 40},
            {"member_name": "สมหญิง", "current_hours": 42, "capacity_hours": 40},
            {"member_name": "สมศักดิ์", "current_hours": 28, "capacity_hours": 40},
            {"member_name": "สมใจ", "current_hours": 38, "capacity_hours": 40},
        ]

    def _render_workload_recommendations(self, workload_data: List[Dict[str, Any]]):
        """Render workload recommendations"""
        st.markdown("### 💡 คำแนะนำการจัดสรรงาน")

        for member in workload_data:
            utilization = member["current_hours"] / member["capacity_hours"]

            if utilization > 1.0:
                st.warning(
                    f"⚠️ {member['member_name']}: ภาระงานเกินกำลัง ({utilization:.1%})"
                )
            elif utilization < 0.7:
                st.info(
                    f"💡 {member['member_name']}: สามารถรับงานเพิ่มได้ ({utilization:.1%})"
                )
            else:
                st.success(
                    f"✅ {member['member_name']}: ภาระงานเหมาะสม ({utilization:.1%})"
                )


# Task Performance Analytics
class TaskPerformanceAnalytics:
    """Task performance analytics and insights"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.task_manager = TaskManager(db_manager)

    def get_task_completion_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get task completion trends"""
        # Implementation for completion trends
        return {
            "completion_rate": 0.85,
            "average_completion_time": 5.2,
            "trend": "increasing",
        }

    def get_team_productivity_metrics(self) -> Dict[str, Any]:
        """Get team productivity metrics"""
        # Implementation for productivity metrics
        return {
            "tasks_per_person_per_day": 2.3,
            "average_task_size": "Medium",
            "velocity_trend": "stable",
        }

    def get_bottleneck_analysis(self) -> List[Dict[str, Any]]:
        """Analyze workflow bottlenecks"""
        # Implementation for bottleneck analysis
        return [
            {"stage": "Review", "avg_duration": 2.5, "bottleneck_score": 0.8},
            {"stage": "Testing", "avg_duration": 1.8, "bottleneck_score": 0.6},
        ]


# Export functionality
def export_tasks_data(tasks: List[Dict[str, Any]], format: str = "excel") -> bytes:
    """Export tasks data in various formats"""
    if format == "excel":
        # Create Excel export
        df = pd.DataFrame(tasks)
        # Implementation for Excel export
        return b""  # Placeholder
    elif format == "csv":
        # Create CSV export
        df = pd.DataFrame(tasks)
        return df.to_csv(index=False).encode("utf-8")
    elif format == "json":
        # Create JSON export
        return json.dumps(tasks, ensure_ascii=False, indent=2).encode("utf-8")

    return b""
