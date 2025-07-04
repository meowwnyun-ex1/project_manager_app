#!/usr/bin/env python3
"""
modules/tasks.py
Task Management for DENSO Project Manager Pro
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging

from utils.error_handler import safe_execute, handle_error, validate_input
from utils.ui_components import UIComponents

logger = logging.getLogger(__name__)


class TaskManager:
    """Task management functionality"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.ui = UIComponents()

    def get_all_tasks(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all tasks with optional filters"""
        try:
            query = """
            SELECT t.TaskID, t.Title, t.Description, t.Status, t.Priority,
                   t.CreatedDate, t.DueDate, t.StartDate, t.EndDate,
                   t.EstimatedHours, t.ActualHours, t.CompletionPercentage,
                   p.Name as ProjectName, p.ProjectID,
                   assigned.FirstName + ' ' + assigned.LastName as AssignedToName,
                   creator.FirstName + ' ' + creator.LastName as CreatedByName
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            LEFT JOIN Users assigned ON t.AssignedToID = assigned.UserID
            LEFT JOIN Users creator ON t.CreatedByID = creator.UserID
            WHERE 1=1
            """

            params = []

            if filters:
                if filters.get("status") and filters["status"] != "ทั้งหมด":
                    query += " AND t.Status = ?"
                    params.append(filters["status"])

                if filters.get("priority") and filters["priority"] != "ทั้งหมด":
                    query += " AND t.Priority = ?"
                    params.append(filters["priority"])

                if filters.get("project_id"):
                    query += " AND t.ProjectID = ?"
                    params.append(filters["project_id"])

                if filters.get("assigned_to_id"):
                    query += " AND t.AssignedToID = ?"
                    params.append(filters["assigned_to_id"])

                if filters.get("overdue_only"):
                    query += " AND t.DueDate < GETDATE() AND t.Status != 'Done'"

                if filters.get("my_tasks") and filters.get("user_id"):
                    query += " AND (t.AssignedToID = ? OR t.CreatedByID = ?)"
                    params.extend([filters["user_id"], filters["user_id"]])

            query += " ORDER BY t.DueDate ASC, t.Priority DESC"

            return self.db.execute_query(query, tuple(params) if params else None)

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []

    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            query = """
            SELECT t.*, p.Name as ProjectName,
                   assigned.FirstName + ' ' + assigned.LastName as AssignedToName,
                   creator.FirstName + ' ' + creator.LastName as CreatedByName
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            LEFT JOIN Users assigned ON t.AssignedToID = assigned.UserID
            LEFT JOIN Users creator ON t.CreatedByID = creator.UserID
            WHERE t.TaskID = ?
            """

            result = self.db.execute_query(query, (task_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None

    def create_task(self, task_data: Dict[str, Any]) -> bool:
        """Create new task"""
        try:
            # Validate required fields
            required_fields = ["Title", "ProjectID", "AssignedToID", "CreatedByID"]
            for field in required_fields:
                if not task_data.get(field):
                    st.error(f"❌ กรุณากรอก {field}")
                    return False

            query = """
            INSERT INTO Tasks (Title, Description, ProjectID, AssignedToID, Status,
                             Priority, DueDate, EstimatedHours, CreatedByID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                task_data["Title"],
                task_data.get("Description", ""),
                task_data["ProjectID"],
                task_data["AssignedToID"],
                task_data.get("Status", "To Do"),
                task_data.get("Priority", "Medium"),
                task_data.get("DueDate"),
                task_data.get("EstimatedHours", 0),
                task_data["CreatedByID"],
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                st.success("✅ สร้างงานสำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถสร้างงานได้")
                return False

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def update_task(self, task_id: int, task_data: Dict[str, Any]) -> bool:
        """Update existing task"""
        try:
            query = """
            UPDATE Tasks 
            SET Title = ?, Description = ?, Status = ?, Priority = ?,
                DueDate = ?, EstimatedHours = ?, ActualHours = ?,
                CompletionPercentage = ?, UpdatedDate = GETDATE()
            WHERE TaskID = ?
            """

            params = (
                task_data["Title"],
                task_data.get("Description", ""),
                task_data["Status"],
                task_data["Priority"],
                task_data.get("DueDate"),
                task_data.get("EstimatedHours", 0),
                task_data.get("ActualHours", 0),
                task_data.get("CompletionPercentage", 0),
                task_id,
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                st.success("✅ อัพเดทงานสำเร็จ")

                # Auto-update status based on completion
                completion = task_data.get("CompletionPercentage", 0)
                if completion == 100 and task_data["Status"] != "Done":
                    self.update_task_status(task_id, "Done")
                elif completion > 0 and task_data["Status"] == "To Do":
                    self.update_task_status(task_id, "In Progress")

                return True
            else:
                st.error("❌ ไม่สามารถอัพเดทงานได้")
                return False

        except Exception as e:
            logger.error(f"Error updating task: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def update_task_status(self, task_id: int, status: str) -> bool:
        """Update task status"""
        try:
            # Update completion percentage based on status
            completion_map = {
                "To Do": 0,
                "In Progress": 25,
                "Review": 75,
                "Testing": 90,
                "Done": 100,
            }

            completion = completion_map.get(status, 0)

            query = """
            UPDATE Tasks 
            SET Status = ?, CompletionPercentage = ?,
                EndDate = CASE WHEN ? = 'Done' THEN GETDATE() ELSE EndDate END,
                UpdatedDate = GETDATE()
            WHERE TaskID = ?
            """

            rows_affected = self.db.execute_non_query(
                query, (status, completion, status, task_id)
            )
            return rows_affected > 0

        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        """Delete task"""
        try:
            query = "DELETE FROM Tasks WHERE TaskID = ?"
            rows_affected = self.db.execute_non_query(query, (task_id,))

            if rows_affected > 0:
                st.success("✅ ลบงานสำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถลบงานได้")
                return False

        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def get_tasks_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tasks for specific project"""
        return self.get_all_tasks({"project_id": project_id})

    def get_tasks_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get tasks assigned to specific user"""
        return self.get_all_tasks({"assigned_to_id": user_id})

    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks"""
        return self.get_all_tasks({"overdue_only": True})

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN Status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                SUM(CASE WHEN DueDate < GETDATE() AND Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                AVG(CAST(CompletionPercentage as FLOAT)) as avg_completion
            FROM Tasks
            """

            result = self.db.execute_query(query)
            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {}

    def get_total_tasks(self) -> int:
        """Get total number of tasks"""
        try:
            query = "SELECT COUNT(*) as count FROM Tasks"
            result = self.db.execute_query(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting total tasks: {e}")
            return 0

    def get_active_tasks_count(self) -> int:
        """Get number of active tasks"""
        try:
            query = "SELECT COUNT(*) as count FROM Tasks WHERE Status IN ('To Do', 'In Progress', 'Review', 'Testing')"
            result = self.db.execute_query(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting active tasks count: {e}")
            return 0

    def get_overdue_tasks_count(self) -> int:
        """Get number of overdue tasks"""
        try:
            query = "SELECT COUNT(*) as count FROM Tasks WHERE DueDate < GETDATE() AND Status != 'Done'"
            result = self.db.execute_query(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting overdue tasks count: {e}")
            return 0


def show_tasks_page(task_manager: TaskManager, project_manager, user_manager):
    """Show tasks management page"""
    ui = UIComponents()

    # Page header
    ui.render_page_header("✅ จัดการงาน", "สร้าง มอบหมาย และติดตามงาน", "✅")

    # Get current user
    user_data = st.session_state.user_data

    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔍 ตัวกรอง")

        # View options
        view_option = st.selectbox(
            "มุมมอง", options=["ทั้งหมด", "งานของฉัน", "งานที่เลยกำหนด", "งานที่กำลังทำ"]
        )

        status_filter = st.selectbox(
            "สถานะงาน",
            options=["ทั้งหมด", "To Do", "In Progress", "Review", "Testing", "Done"],
        )

        priority_filter = st.selectbox(
            "ระดับความสำคัญ", options=["ทั้งหมด", "Low", "Medium", "High", "Critical"]
        )

        # Get projects for filter
        projects = safe_execute(project_manager.get_all_projects, default_return=[])
        project_options = ["ทั้งหมด"] + [p["Name"] for p in projects]
        project_filter = st.selectbox("โครงการ", options=project_options)

        project_id = None
        if project_filter != "ทั้งหมด":
            selected_project = next(
                (p for p in projects if p["Name"] == project_filter), None
            )
            if selected_project:
                project_id = selected_project["ProjectID"]

        # Get users for filter
        users = safe_execute(user_manager.get_all_users, default_return=[])
        user_options = ["ทั้งหมด"] + [f"{u['FirstName']} {u['LastName']}" for u in users]
        assigned_filter = st.selectbox("ผู้รับผิดชอบ", options=user_options)

        assigned_to_id = None
        if assigned_filter != "ทั้งหมด":
            selected_user = next(
                (
                    u
                    for u in users
                    if f"{u['FirstName']} {u['LastName']}" == assigned_filter
                ),
                None,
            )
            if selected_user:
                assigned_to_id = selected_user["UserID"]

    # Build filters
    filters = {
        "status": status_filter if status_filter != "ทั้งหมด" else None,
        "priority": priority_filter if priority_filter != "ทั้งหมด" else None,
        "project_id": project_id,
        "assigned_to_id": assigned_to_id,
    }

    # Apply view-specific filters
    if view_option == "งานของฉัน":
        filters["my_tasks"] = True
        filters["user_id"] = user_data["UserID"]
    elif view_option == "งานที่เลยกำหนด":
        filters["overdue_only"] = True
    elif view_option == "งานที่กำลังทำ":
        filters["status"] = "In Progress"

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 รายการงาน", "➕ สร้างงานใหม่", "📊 สถิติงาน", "📈 แดชบอร์ดงาน"]
    )

    with tab1:
        show_tasks_list(task_manager, filters)

    with tab2:
        if user_data["Role"] in ["Admin", "Project Manager", "Team Lead"]:
            show_create_task_form(task_manager, project_manager, user_manager)
        else:
            st.error("❌ คุณไม่มีสิทธิ์สร้างงาน")

    with tab3:
        show_task_statistics(task_manager)

    with tab4:
        show_task_dashboard(task_manager, user_data)


def show_tasks_list(task_manager: TaskManager, filters: Dict[str, Any]):
    """Show tasks list with actions"""
    ui = UIComponents()

    tasks = safe_execute(task_manager.get_all_tasks, filters, default_return=[])

    if not tasks:
        st.info("ไม่มีงานที่ตรงกับเงื่อนไข")
        return

    # Search functionality
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 ค้นหางาน", placeholder="ชื่องาน, รายละเอียด...")

    # Filter tasks by search term
    if search_term:
        filtered_tasks = [
            t
            for t in tasks
            if search_term.lower() in t["Title"].lower()
            or (t["Description"] and search_term.lower() in t["Description"].lower())
        ]
    else:
        filtered_tasks = tasks

    # Display tasks
    for task in filtered_tasks:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"### {task['Title']}")
                st.markdown(f"**โครงการ:** {task.get('ProjectName', 'N/A')}")
                st.markdown(f"**ผู้รับผิดชอบ:** {task.get('AssignedToName', 'N/A')}")
                st.markdown(f"**สร้างโดย:** {task.get('CreatedByName', 'N/A')}")

                if task.get("Description"):
                    with st.expander("รายละเอียด"):
                        st.markdown(task["Description"])

                # Progress bar
                completion = task.get("CompletionPercentage", 0)
                ui.render_progress_bar(completion)

            with col2:
                st.markdown("**สถานะ**")
                st.markdown(
                    ui.render_status_badge(task["Status"]), unsafe_allow_html=True
                )

                st.markdown("**ความสำคัญ**")
                st.markdown(
                    ui.render_priority_badge(task["Priority"]), unsafe_allow_html=True
                )

            with col3:
                st.markdown("**วันที่**")
                if task["DueDate"]:
                    due_date = task["DueDate"].date()
                    st.markdown(f"กำหนดส่ง: {due_date.strftime('%d/%m/%Y')}")

                    # Check if overdue
                    if due_date < date.today() and task["Status"] != "Done":
                        days_overdue = (date.today() - due_date).days
                        st.markdown(
                            f"<span style='color: red;'>เลยกำหนด {days_overdue} วัน</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        days_remaining = (due_date - date.today()).days
                        if days_remaining >= 0:
                            st.markdown(f"เหลือ {days_remaining} วัน")

                if task.get("EstimatedHours"):
                    st.markdown(f"**ประมาณเวลา:** {task['EstimatedHours']} ชม.")
                if task.get("ActualHours"):
                    st.markdown(f"**เวลาจริง:** {task['ActualHours']} ชม.")

            with col4:
                user_data = st.session_state.user_data
                can_edit = (
                    user_data["Role"] in ["Admin", "Project Manager", "Team Lead"]
                    or user_data["UserID"] == task.get("AssignedToID")
                    or user_data["UserID"] == task.get("CreatedByID")
                )

                if can_edit:
                    # Quick status update
                    current_status = task["Status"]
                    status_options = [
                        "To Do",
                        "In Progress",
                        "Review",
                        "Testing",
                        "Done",
                    ]

                    new_status = st.selectbox(
                        "เปลี่ยนสถานะ",
                        options=status_options,
                        index=status_options.index(current_status),
                        key=f"status_{task['TaskID']}",
                    )

                    if new_status != current_status:
                        if task_manager.update_task_status(task["TaskID"], new_status):
                            st.rerun()

                    if st.button("✏️ แก้ไข", key=f"edit_{task['TaskID']}"):
                        st.session_state.edit_task_id = task["TaskID"]

                    if st.button("📊 รายละเอียด", key=f"detail_{task['TaskID']}"):
                        st.session_state.view_task_id = task["TaskID"]

                if user_data["Role"] in ["Admin", "Project Manager"]:
                    if st.button("🗑️ ลบ", key=f"delete_{task['TaskID']}"):
                        if ui.render_confirmation_dialog(
                            f"ต้องการลบงาน '{task['Title']}' หรือไม่?",
                            f"delete_task_{task['TaskID']}",
                        ):
                            task_manager.delete_task(task["TaskID"])
                            st.rerun()

            st.markdown("---")

    # Handle edit task
    if "edit_task_id" in st.session_state:
        show_edit_task_modal(
            task_manager, st.session_state.edit_task_id, project_manager, user_manager
        )

    # Handle view task details
    if "view_task_id" in st.session_state:
        show_task_details_modal(task_manager, st.session_state.view_task_id)


def show_create_task_form(task_manager: TaskManager, project_manager, user_manager):
    """Show create task form"""
    with st.form("create_task_form"):
        st.subheader("➕ สร้างงานใหม่")

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("ชื่องาน *", placeholder="ชื่องาน")

            # Get projects
            projects = safe_execute(project_manager.get_all_projects, default_return=[])
            project_options = {
                p["Name"]: p["ProjectID"]
                for p in projects
                if p["Status"] != "Cancelled"
            }

            if project_options:
                selected_project = st.selectbox(
                    "โครงการ *", options=list(project_options.keys())
                )
                project_id = project_options[selected_project]
            else:
                st.error("ไม่พบโครงการที่ใช้งานได้")
                project_id = None

            status = st.selectbox("สถานะ", options=["To Do", "In Progress", "Review"])
            due_date = st.date_input("วันกำหนดส่ง")

        with col2:
            # Get users for assignment
            users = safe_execute(user_manager.get_all_users, default_return=[])
            user_options = {
                f"{u['FirstName']} {u['LastName']}": u["UserID"]
                for u in users
                if u["IsActive"]
            }

            if user_options:
                selected_user = st.selectbox(
                    "ผู้รับผิดชอบ *", options=list(user_options.keys())
                )
                assigned_to_id = user_options[selected_user]
            else:
                st.error("ไม่พบผู้ใช้ที่สามารถมอบหมายได้")
                assigned_to_id = None

            priority = st.selectbox(
                "ระดับความสำคัญ", options=["Low", "Medium", "High", "Critical"]
            )
            estimated_hours = st.number_input(
                "ประมาณเวลา (ชั่วโมง)", min_value=0.0, value=0.0, step=0.5
            )

        description = st.text_area(
            "รายละเอียดงาน", height=100, placeholder="อธิบายรายละเอียดและเป้าหมายของงาน"
        )

        if st.form_submit_button("✅ สร้างงาน", type="primary"):
            user_data = st.session_state.user_data

            if title and project_id and assigned_to_id:
                task_data = {
                    "Title": title,
                    "Description": description,
                    "ProjectID": project_id,
                    "AssignedToID": assigned_to_id,
                    "Status": status,
                    "Priority": priority,
                    "DueDate": due_date if due_date else None,
                    "EstimatedHours": estimated_hours,
                    "CreatedByID": user_data["UserID"],
                }

                if task_manager.create_task(task_data):
                    st.rerun()
            else:
                st.error("❌ กรุณากรอกข้อมูลที่จำเป็น (*)")


def show_edit_task_modal(
    task_manager: TaskManager, task_id: int, project_manager, user_manager
):
    """Show edit task modal"""
    task = safe_execute(task_manager.get_task_by_id, task_id, default_return=None)

    if not task:
        st.error("ไม่พบงาน")
        return

    with st.expander(f"✏️ แก้ไขงาน: {task['Title']}", expanded=True):
        with st.form(f"edit_task_form_{task_id}"):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("ชื่องาน", value=task["Title"])
                status = st.selectbox(
                    "สถานะ",
                    options=["To Do", "In Progress", "Review", "Testing", "Done"],
                    index=["To Do", "In Progress", "Review", "Testing", "Done"].index(
                        task["Status"]
                    ),
                )
                due_date = st.date_input(
                    "วันกำหนดส่ง",
                    value=task["DueDate"].date() if task["DueDate"] else None,
                )
                estimated_hours = st.number_input(
                    "ประมาณเวลา (ชั่วโมง)", value=float(task.get("EstimatedHours", 0))
                )

            with col2:
                priority = st.selectbox(
                    "ระดับความสำคัญ",
                    options=["Low", "Medium", "High", "Critical"],
                    index=["Low", "Medium", "High", "Critical"].index(task["Priority"]),
                )
                actual_hours = st.number_input(
                    "เวลาจริง (ชั่วโมง)", value=float(task.get("ActualHours", 0))
                )
                completion = st.slider(
                    "ความคืบหน้า (%)", 0, 100, value=task.get("CompletionPercentage", 0)
                )

            description = st.text_area(
                "รายละเอียดงาน", value=task.get("Description", "")
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.form_submit_button("✅ บันทึกการแก้ไข", type="primary"):
                    updated_data = {
                        "Title": title,
                        "Description": description,
                        "Status": status,
                        "Priority": priority,
                        "DueDate": due_date,
                        "EstimatedHours": estimated_hours,
                        "ActualHours": actual_hours,
                        "CompletionPercentage": completion,
                    }

                    if task_manager.update_task(task_id, updated_data):
                        del st.session_state.edit_task_id
                        st.rerun()

            with col2:
                if st.form_submit_button("❌ ยกเลิก"):
                    del st.session_state.edit_task_id
                    st.rerun()


def show_task_details_modal(task_manager: TaskManager, task_id: int):
    """Show task details modal"""
    task = safe_execute(task_manager.get_task_by_id, task_id, default_return=None)

    if not task:
        st.error("ไม่พบงาน")
        return

    with st.expander(f"📊 รายละเอียดงาน: {task['Title']}", expanded=True):
        ui = UIComponents()

        # Basic info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### ข้อมูลพื้นฐาน")
            st.markdown(f"**ชื่องาน:** {task['Title']}")
            st.markdown(f"**โครงการ:** {task.get('ProjectName', 'N/A')}")
            st.markdown(f"**ผู้รับผิดชอบ:** {task.get('AssignedToName', 'N/A')}")
            st.markdown(f"**สร้างโดย:** {task.get('CreatedByName', 'N/A')}")
            st.markdown(
                f"**สถานะ:** {ui.render_status_badge(task['Status'])}",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"**ความสำคัญ:** {ui.render_priority_badge(task['Priority'])}",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown("### ข้อมูลเวลา")
            if task["CreatedDate"]:
                st.markdown(f"**วันที่สร้าง:** {task['CreatedDate'].strftime('%d/%m/%Y')}")
            if task["DueDate"]:
                st.markdown(f"**กำหนดส่ง:** {task['DueDate'].strftime('%d/%m/%Y')}")
                days_remaining = (task["DueDate"].date() - date.today()).days
                if days_remaining < 0:
                    st.markdown(f"**สถานะ:** เลยกำหนด {abs(days_remaining)} วัน")
                else:
                    st.markdown(f"**เหลือเวลา:** {days_remaining} วัน")

            if task.get("EstimatedHours"):
                st.markdown(f"**ประมาณเวลา:** {task['EstimatedHours']} ชม.")
            if task.get("ActualHours"):
                st.markdown(f"**เวลาจริง:** {task['ActualHours']} ชม.")
                if task.get("EstimatedHours", 0) > 0:
                    variance = (
                        (task["ActualHours"] - task["EstimatedHours"])
                        / task["EstimatedHours"]
                    ) * 100
                    st.markdown(f"**ส่วนต่าง:** {variance:+.1f}%")

        with col3:
            st.markdown("### ความคืบหน้า")
            completion = task.get("CompletionPercentage", 0)
            ui.render_progress_bar(completion)

            if task["StartDate"]:
                st.markdown(f"**เริ่มต้น:** {task['StartDate'].strftime('%d/%m/%Y')}")
            if task["EndDate"]:
                st.markdown(f"**สิ้นสุด:** {task['EndDate'].strftime('%d/%m/%Y')}")

        # Description
        if task.get("Description"):
            st.markdown("### รายละเอียด")
            st.markdown(task["Description"])

        if st.button("❌ ปิด", key=f"close_task_detail_{task_id}"):
            del st.session_state.view_task_id
            st.rerun()


def show_task_statistics(task_manager: TaskManager):
    """Show task statistics and charts"""
    ui = UIComponents()

    st.subheader("📊 สถิติงาน")

    # Get task statistics
    stats = safe_execute(task_manager.get_task_statistics, default_return={})

    if not stats or stats.get("total_tasks", 0) == 0:
        st.info("ไม่มีข้อมูลงาน")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_tasks = stats.get("total_tasks", 0)
        st.metric("งานทั้งหมด", total_tasks)

    with col2:
        completed_tasks = stats.get("completed_tasks", 0)
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )
        st.metric("งานเสร็จแล้ว", completed_tasks, f"{completion_rate:.1f}%")

    with col3:
        in_progress_tasks = stats.get("in_progress_tasks", 0)
        st.metric("งานที่กำลังทำ", in_progress_tasks)

    with col4:
        overdue_tasks = stats.get("overdue_tasks", 0)
        st.metric(
            "งานเลยกำหนด",
            overdue_tasks,
            delta=f"-{overdue_tasks}" if overdue_tasks > 0 else None,
        )

    # Get all tasks for detailed analysis
    all_tasks = safe_execute(task_manager.get_all_tasks, default_return=[])

    if not all_tasks:
        return

    df = pd.DataFrame(all_tasks)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("การกระจายสถานะงาน")
        if len(df) > 0:
            status_counts = df["Status"].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="สถานะงาน",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("การกระจายความสำคัญ")
        if len(df) > 0:
            priority_counts = df["Priority"].value_counts()
            colors = {
                "Low": "#28a745",
                "Medium": "#ffc107",
                "High": "#fd7e14",
                "Critical": "#dc3545",
            }
            fig = px.bar(
                x=priority_counts.index,
                y=priority_counts.values,
                title="ระดับความสำคัญของงาน",
                color=priority_counts.index,
                color_discrete_map=colors,
            )
            fig.update_layout(xaxis_title="ความสำคัญ", yaxis_title="จำนวน")
            st.plotly_chart(fig, use_container_width=True)

    # Task completion timeline
    st.subheader("Timeline งาน")
    if len(df) > 0 and "DueDate" in df.columns:
        # Filter tasks with due dates
        timeline_df = df.dropna(subset=["DueDate"]).copy()

        if len(timeline_df) > 0:
            # Add status for coloring
            timeline_df["DueDateOnly"] = timeline_df["DueDate"].dt.date
            timeline_df["IsOverdue"] = (timeline_df["DueDateOnly"] < date.today()) & (
                timeline_df["Status"] != "Done"
            )

            # Create timeline chart
            fig = px.timeline(
                timeline_df.head(20),  # Show only first 20 for readability
                x_start="CreatedDate",
                x_end="DueDate",
                y="Title",
                color="Status",
                title="Timeline งาน (20 งานแรก)",
                hover_data=["Priority", "AssignedToName"],
            )

            fig.update_layout(height=max(400, len(timeline_df.head(20)) * 30))
            st.plotly_chart(fig, use_container_width=True)

    # Workload analysis
    st.subheader("การวิเคราะห์ปริมาณงาน")
    if len(df) > 0 and "AssignedToName" in df.columns:
        col1, col2 = st.columns(2)

        with col1:
            # Tasks by assignee
            assignee_counts = df["AssignedToName"].value_counts().head(10)
            fig = px.bar(
                x=assignee_counts.values,
                y=assignee_counts.index,
                orientation="h",
                title="งานตามผู้รับผิดชอบ (10 อันดับแรก)",
            )
            fig.update_layout(xaxis_title="จำนวนงาน", yaxis_title="ผู้รับผิดชอบ")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Completion percentage distribution
            if "CompletionPercentage" in df.columns:
                completion_ranges = [
                    "0%",
                    "1-25%",
                    "26-50%",
                    "51-75%",
                    "76-99%",
                    "100%",
                ]
                completion_counts = [
                    len(df[df["CompletionPercentage"] == 0]),
                    len(
                        df[
                            (df["CompletionPercentage"] > 0)
                            & (df["CompletionPercentage"] <= 25)
                        ]
                    ),
                    len(
                        df[
                            (df["CompletionPercentage"] > 25)
                            & (df["CompletionPercentage"] <= 50)
                        ]
                    ),
                    len(
                        df[
                            (df["CompletionPercentage"] > 50)
                            & (df["CompletionPercentage"] <= 75)
                        ]
                    ),
                    len(
                        df[
                            (df["CompletionPercentage"] > 75)
                            & (df["CompletionPercentage"] < 100)
                        ]
                    ),
                    len(df[df["CompletionPercentage"] == 100]),
                ]

                fig = px.bar(
                    x=completion_ranges, y=completion_counts, title="การกระจายความคืบหน้า"
                )
                fig.update_layout(xaxis_title="ช่วงความคืบหน้า", yaxis_title="จำนวนงาน")
                st.plotly_chart(fig, use_container_width=True)


def show_task_dashboard(task_manager: TaskManager, user_data: Dict[str, Any]):
    """Show personalized task dashboard"""
    ui = UIComponents()

    st.subheader("📈 แดชบอร์ดงานส่วนตัว")

    # Get user's tasks
    my_tasks = safe_execute(
        task_manager.get_tasks_by_user, user_data["UserID"], default_return=[]
    )

    if not my_tasks:
        st.info("คุณไม่มีงานที่ได้รับมอบหมาย")
        return

    df = pd.DataFrame(my_tasks)

    # Personal metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_my_tasks = len(df)
        st.metric("งานของฉันทั้งหมด", total_my_tasks)

    with col2:
        completed_my_tasks = len(df[df["Status"] == "Done"])
        my_completion_rate = (
            (completed_my_tasks / total_my_tasks * 100) if total_my_tasks > 0 else 0
        )
        st.metric("งานที่เสร็จแล้ว", completed_my_tasks, f"{my_completion_rate:.1f}%")

    with col3:
        in_progress_my_tasks = len(df[df["Status"] == "In Progress"])
        st.metric("งานที่กำลังทำ", in_progress_my_tasks)

    with col4:
        overdue_my_tasks = len(
            df[(df["DueDate"] < pd.Timestamp.now()) & (df["Status"] != "Done")]
        )
        st.metric(
            "งานที่เลยกำหนด",
            overdue_my_tasks,
            delta=f"-{overdue_my_tasks}" if overdue_my_tasks > 0 else None,
        )

    # Upcoming deadlines
    st.subheader("⏰ งานที่ใกล้ครบกำหนด")
    upcoming_tasks = df[
        (df["DueDate"] >= pd.Timestamp.now())
        & (df["DueDate"] <= pd.Timestamp.now() + pd.Timedelta(days=7))
        & (df["Status"] != "Done")
    ].sort_values("DueDate")

    if len(upcoming_tasks) > 0:
        for _, task in upcoming_tasks.iterrows():
            days_left = (task["DueDate"].date() - date.today()).days

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{task['Title']}**")
                    st.markdown(f"โครงการ: {task.get('ProjectName', 'N/A')}")

                with col2:
                    st.markdown(
                        ui.render_priority_badge(task["Priority"]),
                        unsafe_allow_html=True,
                    )
                    ui.render_progress_bar(task.get("CompletionPercentage", 0))

                with col3:
                    if days_left == 0:
                        st.markdown("**วันนี้!**")
                    elif days_left == 1:
                        st.markdown("**พรุ่งนี้**")
                    else:
                        st.markdown(f"**เหลือ {days_left} วัน**")

                st.markdown("---")
    else:
        st.info("ไม่มีงานที่ใกล้ครบกำหนดในสัปดาห์นี้")

    # Personal productivity chart
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("ความคืบหน้างานของฉัน")
        if len(df) > 0:
            my_status_counts = df["Status"].value_counts()
            fig = px.pie(
                values=my_status_counts.values,
                names=my_status_counts.index,
                title="สถานะงานของฉัน",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("งานตามโครงการ")
        if len(df) > 0 and "ProjectName" in df.columns:
            project_counts = df["ProjectName"].value_counts()
            fig = px.bar(
                x=project_counts.values,
                y=project_counts.index,
                orientation="h",
                title="จำนวนงานในแต่ละโครงการ",
            )
            fig.update_layout(xaxis_title="จำนวนงาน", yaxis_title="โครงการ")
            st.plotly_chart(fig, use_container_width=True)
