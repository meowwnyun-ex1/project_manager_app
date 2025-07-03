"""
pages/tasks.py
Tasks management page
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging

from modules.ui_components import (
    FormBuilder,
    CardComponent,
    DataTable,
    StatusBadge,
    NotificationManager,
    ModernModal,
    ExportManager,
)
from modules.auth import require_role, get_current_user
from modules.tasks import TaskManager, TaskStatus, TaskPriority
from utils.error_handler import handle_streamlit_errors, safe_execute
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


class TasksPage:
    """Tasks management page class"""

    def __init__(self, task_manager, project_manager, user_manager):
        self.task_manager = task_manager
        self.project_manager = project_manager
        self.user_manager = user_manager

    @handle_streamlit_errors()
    @monitor_performance("tasks_page_render")
    def show(self):
        """Show tasks management page"""
        st.title("✅ การจัดการงาน")

        # Get current user
        current_user = get_current_user()
        if not current_user:
            st.error("กรุณาเข้าสู่ระบบ")
            return

        # Action buttons
        self._show_action_buttons()

        # Show create task form if requested
        if st.session_state.get("show_new_task", False):
            self._show_create_task_form()

        # Show edit task form if requested
        if st.session_state.get("edit_task_id"):
            self._show_edit_task_form()

        # Main content
        self._show_tasks_content()

    def _show_action_buttons(self):
        """Show action buttons"""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if st.button("➕ สร้างงานใหม่", use_container_width=True, type="primary"):
                st.session_state.show_new_task = True
                st.rerun()

        with col2:
            if st.button("🔄 รีเฟรช", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        with col3:
            if st.button("📊 รายงาน", use_container_width=True):
                self._show_task_report()

    def _show_create_task_form(self):
        """Show create task form"""
        with st.expander("สร้างงานใหม่", expanded=True):
            with st.form("create_task_form", clear_on_submit=False):
                col1, col2 = st.columns(2)

                with col1:
                    # Project selection
                    projects = self._get_user_projects()
                    if projects:
                        project_options = {
                            f"{p['ProjectName']} (ID: {p['ProjectID']})": p["ProjectID"]
                            for p in projects
                        }
                        selected_project = st.selectbox(
                            "โครงการ *", list(project_options.keys())
                        )
                        project_id = project_options[selected_project]
                    else:
                        st.error("ไม่พบโครงการ กรุณาสร้างโครงการก่อน")
                        return

                    task_name = st.text_input("ชื่องาน *", placeholder="ใส่ชื่องาน")
                    priority = st.selectbox(
                        "ระดับความสำคัญ", [p.value for p in TaskPriority]
                    )
                    estimated_hours = st.number_input(
                        "เวลาที่คาดว่าจะใช้ (ชั่วโมง)", min_value=0.5, value=8.0, step=0.5
                    )

                with col2:
                    # Assignee selection
                    users = self._get_active_users()
                    if users:
                        user_options = {
                            f"{u['FirstName']} {u['LastName']} ({u['Username']})": u[
                                "UserID"
                            ]
                            for u in users
                        }
                        selected_assignee = st.selectbox(
                            "ผู้รับผิดชอบ", ["ไม่ระบุ"] + list(user_options.keys())
                        )
                        assignee_id = user_options.get(selected_assignee)
                    else:
                        assignee_id = None

                    status = st.selectbox("สถานะ", [s.value for s in TaskStatus])
                    due_date = st.date_input(
                        "วันครบกำหนด", value=date.today() + timedelta(days=7)
                    )

                description = st.text_area(
                    "รายละเอียด", placeholder="อธิบายรายละเอียดของงาน...", height=100
                )

                # Dependencies
                existing_tasks = self._get_existing_tasks(
                    project_id if "project_id" in locals() else None
                )
                dependencies = st.multiselect(
                    "งานที่ต้องทำก่อน (Dependencies)",
                    options=[
                        f"{t['TaskName']} (ID: {t['TaskID']})" for t in existing_tasks
                    ],
                    help="เลือกงานที่ต้องเสร็จสิ้นก่อนจึงจะเริ่มงานนี้ได้",
                )

                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.form_submit_button(
                        "💾 บันทึก", use_container_width=True, type="primary"
                    ):
                        if task_name and project_id:
                            self._create_task(
                                {
                                    "project_id": project_id,
                                    "task_name": task_name,
                                    "description": description,
                                    "assignee_id": assignee_id,
                                    "status": status,
                                    "priority": priority,
                                    "estimated_hours": estimated_hours,
                                    "due_date": due_date,
                                    "dependencies": dependencies,
                                }
                            )
                        else:
                            st.error("กรุณากรอกข้อมูลให้ครบถ้วน")

                with col2:
                    if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                        st.session_state.show_new_task = False
                        st.rerun()

    def _show_tasks_content(self):
        """Show main tasks content"""
        # Filters
        self._show_task_filters()

        # Tasks list
        tasks = self._get_filtered_tasks()

        if tasks:
            self._show_tasks_grid(tasks)
        else:
            st.info("🔍 ไม่พบงานที่ตรงกับเงื่อนไขการค้นหา")

    def _show_task_filters(self):
        """Show task filters"""
        with st.expander("🔍 ตัวกรองและการค้นหา", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                search_term = st.text_input(
                    "🔍 ค้นหา", placeholder="ชื่องาน, รายละเอียด..."
                )
                st.session_state.task_search = search_term

            with col2:
                status_filter = st.multiselect("สถานะ", [s.value for s in TaskStatus])
                st.session_state.task_status_filter = status_filter

            with col3:
                priority_filter = st.multiselect(
                    "ความสำคัญ", [p.value for p in TaskPriority]
                )
                st.session_state.task_priority_filter = priority_filter

            with col4:
                # Date range filter
                date_range = st.selectbox(
                    "ช่วงเวลา", ["ทั้งหมด", "วันนี้", "สัปดาห์นี้", "เดือนนี้", "เลยกำหนด"]
                )
                st.session_state.task_date_filter = date_range

    def _show_tasks_grid(self, tasks: List[Dict]):
        """Show tasks in grid layout"""
        # Group tasks by status
        task_groups = {}
        for task in tasks:
            status = task["Status"]
            if status not in task_groups:
                task_groups[status] = []
            task_groups[status].append(task)

        # Create columns for each status
        statuses = [s.value for s in TaskStatus]
        cols = st.columns(len(statuses))

        for i, status in enumerate(statuses):
            with cols[i]:
                st.subheader(f"{status}")
                st.caption(f"({len(task_groups.get(status, []))} งาน)")

                # Show tasks in this status
                for task in task_groups.get(status, []):
                    self._show_task_card(task)

    def _show_task_card(self, task: Dict):
        """Show individual task card"""
        with st.container():
            # Task header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{task['TaskName']}**")
            with col2:
                if st.button("⚙️", key=f"task_menu_{task['TaskID']}", help="ตัวเลือก"):
                    st.session_state.selected_task = task

            # Task details
            if task["ProjectName"]:
                st.caption(f"📁 {task['ProjectName']}")

            if task["AssigneeName"]:
                st.caption(f"� {task['AssigneeName']}")

            # Priority badge
            priority_colors = {
                "Low": "blue",
                "Medium": "orange",
                "High": "red",
                "Critical": "violet",
            }
            st.markdown(
                f":{priority_colors.get(task['Priority'], 'gray')}[{task['Priority']}]"
            )

            # Due date
            if task["DueDate"]:
                due_date = datetime.strptime(task["DueDate"], "%Y-%m-%d").date()
                days_left = (due_date - date.today()).days

                if days_left < 0:
                    st.error(f"⏰ เลยกำหนด {abs(days_left)} วัน")
                elif days_left == 0:
                    st.warning("⏰ ครบกำหนดวันนี้")
                elif days_left <= 3:
                    st.warning(f"⏰ เหลือ {days_left} วัน")
                else:
                    st.info(f"📅 เหลือ {days_left} วัน")

            # Progress bar
            if task.get("Progress", 0) > 0:
                st.progress(task["Progress"] / 100)
                st.caption(f"ความคืบหน้า: {task['Progress']}%")

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✏️", key=f"edit_{task['TaskID']}", help="แก้ไข"):
                    st.session_state.edit_task_id = task["TaskID"]
                    st.rerun()
            with col2:
                if st.button("💬", key=f"comment_{task['TaskID']}", help="ความคิดเห็น"):
                    self._show_task_comments(task["TaskID"])
            with col3:
                if st.button("📋", key=f"detail_{task['TaskID']}", help="รายละเอียด"):
                    self._show_task_detail(task)

            st.divider()

    def _create_task(self, task_data: Dict):
        """Create new task"""
        try:
            current_user = get_current_user()
            task_data["created_by"] = current_user["UserID"]

            result = safe_execute(
                self.task_manager.create_task,
                task_data,
                error_message="ไม่สามารถสร้างงานได้",
            )

            if result:
                st.success("✅ สร้างงานเรียบร้อยแล้ว")
                st.session_state.show_new_task = False
                st.rerun()

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            st.error("เกิดข้อผิดพลาดในการสร้างงาน")

    def _get_user_projects(self) -> List[Dict]:
        """Get projects for current user"""
        current_user = get_current_user()
        return safe_execute(
            self.project_manager.get_user_projects,
            current_user["UserID"],
            default_return=[],
        )

    def _get_active_users(self) -> List[Dict]:
        """Get active users"""
        return safe_execute(self.user_manager.get_active_users, default_return=[])

    def _get_existing_tasks(self, project_id: Optional[int]) -> List[Dict]:
        """Get existing tasks for dependency selection"""
        if not project_id:
            return []
        return safe_execute(
            self.task_manager.get_project_tasks, project_id, default_return=[]
        )

    def _get_filtered_tasks(self) -> List[Dict]:
        """Get tasks based on current filters"""
        current_user = get_current_user()
        filters = {
            "search": st.session_state.get("task_search", ""),
            "status": st.session_state.get("task_status_filter", []),
            "priority": st.session_state.get("task_priority_filter", []),
            "date_range": st.session_state.get("task_date_filter", "ทั้งหมด"),
            "user_id": current_user["UserID"],
        }

        return safe_execute(
            self.task_manager.get_filtered_tasks, filters, default_return=[]
        )

    def _show_task_detail(self, task: Dict):
        """Show task detail modal"""
        with st.expander(f"📋 รายละเอียดงาน: {task['TaskName']}", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**ข้อมูลทั่วไป**")
                st.write(f"🏷️ **ID:** {task['TaskID']}")
                st.write(f"📁 **โครงการ:** {task['ProjectName']}")
                st.write(f"📝 **รายละเอียด:** {task['Description'] or 'ไม่มี'}")
                st.write(f"⭐ **ความสำคัญ:** {task['Priority']}")
                st.write(f"📊 **สถานะ:** {task['Status']}")

            with col2:
                st.write("**ข้อมูลเวลา**")
                st.write(f"📅 **วันที่สร้าง:** {task['CreatedDate']}")
                st.write(f"⏰ **วันครบกำหนด:** {task['DueDate'] or 'ไม่ได้กำหนด'}")
                st.write(f"👤 **ผู้สร้าง:** {task['CreatorName']}")
                st.write(
                    f"👨‍💼 **ผู้รับผิดชอบ:** {task['AssigneeName'] or 'ยังไม่ได้มอบหมาย'}"
                )

                if task.get("EstimatedHours"):
                    st.write(f"⏱️ **เวลาที่คาดว่าจะใช้:** {task['EstimatedHours']} ชั่วโมง")

    def _show_task_comments(self, task_id: int):
        """Show task comments"""
        st.info("💬 ฟีเจอร์ความคิดเห็นจะพัฒนาในเวอร์ชันต่อไป")

    def _show_task_report(self):
        """Show task reports"""
        st.info("📊 ฟีเจอร์รายงานจะพัฒนาในเวอร์ชันต่อไป")
