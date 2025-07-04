#!/usr/bin/env python3
"""
modules/projects.py
Project Management for DENSO Project Manager Pro
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


class ProjectManager:
    """Project management functionality"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.ui = UIComponents()

    def get_all_projects(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all projects with optional filters"""
        try:
            query = """
            SELECT p.ProjectID, p.Name, p.Description, p.StartDate, p.EndDate,
                   p.Status, p.Priority, p.Budget, p.ActualCost, p.CompletionPercentage,
                   p.ClientName, p.CreatedDate, p.UpdatedDate,
                   u.FirstName + ' ' + u.LastName as ManagerName
            FROM Projects p
            LEFT JOIN Users u ON p.ManagerID = u.UserID
            WHERE 1=1
            """

            params = []

            if filters:
                if filters.get("status") and filters["status"] != "ทั้งหมด":
                    query += " AND p.Status = ?"
                    params.append(filters["status"])

                if filters.get("priority") and filters["priority"] != "ทั้งหมด":
                    query += " AND p.Priority = ?"
                    params.append(filters["priority"])

                if filters.get("manager_id"):
                    query += " AND p.ManagerID = ?"
                    params.append(filters["manager_id"])

            query += " ORDER BY p.UpdatedDate DESC"

            return self.db.execute_query(query, tuple(params) if params else None)

        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []

    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            query = """
            SELECT p.*, u.FirstName + ' ' + u.LastName as ManagerName
            FROM Projects p
            LEFT JOIN Users u ON p.ManagerID = u.UserID
            WHERE p.ProjectID = ?
            """

            result = self.db.execute_query(query, (project_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None

    def create_project(self, project_data: Dict[str, Any]) -> bool:
        """Create new project"""
        try:
            # Validate required fields
            required_fields = [
                "Name",
                "Description",
                "StartDate",
                "EndDate",
                "ManagerID",
            ]
            for field in required_fields:
                if not project_data.get(field):
                    st.error(f"❌ กรุณากรอก {field}")
                    return False

            query = """
            INSERT INTO Projects (Name, Description, StartDate, EndDate, Status, 
                                Priority, Budget, ClientName, ManagerID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                project_data["Name"],
                project_data["Description"],
                project_data["StartDate"],
                project_data["EndDate"],
                project_data.get("Status", "Planning"),
                project_data.get("Priority", "Medium"),
                project_data.get("Budget", 0),
                project_data.get("ClientName", ""),
                project_data["ManagerID"],
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                st.success("✅ สร้างโครงการสำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถสร้างโครงการได้")
                return False

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> bool:
        """Update existing project"""
        try:
            query = """
            UPDATE Projects 
            SET Name = ?, Description = ?, StartDate = ?, EndDate = ?,
                Status = ?, Priority = ?, Budget = ?, ClientName = ?,
                ManagerID = ?, UpdatedDate = GETDATE()
            WHERE ProjectID = ?
            """

            params = (
                project_data["Name"],
                project_data["Description"],
                project_data["StartDate"],
                project_data["EndDate"],
                project_data["Status"],
                project_data["Priority"],
                project_data.get("Budget", 0),
                project_data.get("ClientName", ""),
                project_data["ManagerID"],
                project_id,
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                st.success("✅ อัพเดทโครงการสำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถอัพเดทโครงการได้")
                return False

        except Exception as e:
            logger.error(f"Error updating project: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def delete_project(self, project_id: int) -> bool:
        """Delete project (soft delete)"""
        try:
            # Check if project has active tasks
            task_query = "SELECT COUNT(*) as count FROM Tasks WHERE ProjectID = ? AND Status != 'Done'"
            task_result = self.db.execute_query(task_query, (project_id,))

            if task_result and task_result[0]["count"] > 0:
                st.error("❌ ไม่สามารถลบโครงการที่มีงานที่ยังไม่เสร็จได้")
                return False

            # Update status to cancelled instead of actual delete
            query = "UPDATE Projects SET Status = 'Cancelled', UpdatedDate = GETDATE() WHERE ProjectID = ?"
            rows_affected = self.db.execute_non_query(query, (project_id,))

            if rows_affected > 0:
                st.success("✅ ยกเลิกโครงการสำเร็จ")
                return True
            else:
                st.error("❌ ไม่สามารถยกเลิกโครงการได้")
                return False

        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            return False

    def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """Get project statistics"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN DueDate < GETDATE() AND Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                AVG(CAST(CompletionPercentage as FLOAT)) as avg_completion
            FROM Tasks 
            WHERE ProjectID = ?
            """

            result = self.db.execute_query(query, (project_id,))
            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {}

    def get_total_projects(self) -> int:
        """Get total number of projects"""
        try:
            query = "SELECT COUNT(*) as count FROM Projects WHERE Status != 'Cancelled'"
            result = self.db.execute_query(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting total projects: {e}")
            return 0

    def get_active_projects_count(self) -> int:
        """Get number of active projects"""
        try:
            query = "SELECT COUNT(*) as count FROM Projects WHERE Status IN ('Planning', 'In Progress')"
            result = self.db.execute_query(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting active projects count: {e}")
            return 0


def show_projects_page(project_manager: ProjectManager, user_manager):
    """Show projects management page"""
    ui = UIComponents()

    # Page header
    ui.render_page_header("📁 จัดการโครงการ", "สร้าง แก้ไข และติดตามโครงการ", "📁")

    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔍 ตัวกรอง")

        status_filter = st.selectbox(
            "สถานะโครงการ",
            options=[
                "ทั้งหมด",
                "Planning",
                "In Progress",
                "On Hold",
                "Completed",
                "Cancelled",
            ],
        )

        priority_filter = st.selectbox(
            "ระดับความสำคัญ", options=["ทั้งหมด", "Low", "Medium", "High", "Critical"]
        )

        # Get managers for filter
        managers = safe_execute(
            user_manager.get_users_by_role, "Project Manager", default_return=[]
        )
        manager_options = ["ทั้งหมด"] + [
            f"{m['FirstName']} {m['LastName']}" for m in managers
        ]
        manager_filter = st.selectbox("ผู้จัดการโครงการ", options=manager_options)

        manager_id = None
        if manager_filter != "ทั้งหมด":
            selected_manager = next(
                (
                    m
                    for m in managers
                    if f"{m['FirstName']} {m['LastName']}" == manager_filter
                ),
                None,
            )
            if selected_manager:
                manager_id = selected_manager["UserID"]

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(
        ["📋 รายการโครงการ", "➕ สร้างโครงการใหม่", "📊 สถิติโครงการ"]
    )

    with tab1:
        show_projects_list(
            project_manager,
            {
                "status": status_filter if status_filter != "ทั้งหมด" else None,
                "priority": priority_filter if priority_filter != "ทั้งหมด" else None,
                "manager_id": manager_id,
            },
        )

    with tab2:
        user_data = st.session_state.user_data
        if user_data["Role"] in ["Admin", "Project Manager"]:
            show_create_project_form(project_manager, user_manager)
        else:
            st.error("❌ คุณไม่มีสิทธิ์สร้างโครงการ")

    with tab3:
        show_project_statistics(project_manager)


def show_projects_list(project_manager: ProjectManager, filters: Dict[str, Any]):
    """Show projects list with actions"""
    ui = UIComponents()

    projects = safe_execute(
        project_manager.get_all_projects, filters, default_return=[]
    )

    if not projects:
        st.info("ไม่มีโครงการที่ตรงกับเงื่อนไข")
        return

    # Search functionality
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 ค้นหาโครงการ", placeholder="ชื่อโครงการ, ลูกค้า...")

    # Filter projects by search term
    if search_term:
        filtered_projects = [
            p
            for p in projects
            if search_term.lower() in p["Name"].lower()
            or (p["ClientName"] and search_term.lower() in p["ClientName"].lower())
        ]
    else:
        filtered_projects = projects

    # Display projects
    for project in filtered_projects:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"### {project['Name']}")
                st.markdown(f"**ลูกค้า:** {project.get('ClientName', 'N/A')}")
                st.markdown(f"**ผู้จัดการ:** {project.get('ManagerName', 'N/A')}")
                st.markdown(f"**งบประมาณ:** {project.get('Budget', 0):,.2f} บาท")

                # Progress bar
                completion = project.get("CompletionPercentage", 0)
                ui.render_progress_bar(completion)

            with col2:
                st.markdown("**สถานะ**")
                st.markdown(
                    ui.render_status_badge(project["Status"]), unsafe_allow_html=True
                )

                st.markdown("**ความสำคัญ**")
                st.markdown(
                    ui.render_priority_badge(project["Priority"]),
                    unsafe_allow_html=True,
                )

            with col3:
                st.markdown("**วันที่**")
                if project["StartDate"]:
                    st.markdown(f"เริ่ม: {project['StartDate'].strftime('%d/%m/%Y')}")
                if project["EndDate"]:
                    st.markdown(f"สิ้นสุด: {project['EndDate'].strftime('%d/%m/%Y')}")

                # Calculate days remaining
                if project["EndDate"]:
                    days_remaining = (project["EndDate"].date() - date.today()).days
                    if days_remaining < 0:
                        st.markdown(
                            f"**เลยกำหนด {abs(days_remaining)} วัน**",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"เหลือ {days_remaining} วัน")

            with col4:
                user_data = st.session_state.user_data
                can_edit = user_data["Role"] in [
                    "Admin",
                    "Project Manager",
                ] or user_data["UserID"] == project.get("ManagerID")

                if can_edit:
                    if st.button("✏️ แก้ไข", key=f"edit_{project['ProjectID']}"):
                        st.session_state.edit_project_id = project["ProjectID"]

                    if st.button("📊 รายละเอียด", key=f"detail_{project['ProjectID']}"):
                        st.session_state.view_project_id = project["ProjectID"]

                if user_data["Role"] == "Admin":
                    if st.button("🗑️ ยกเลิก", key=f"delete_{project['ProjectID']}"):
                        if ui.render_confirmation_dialog(
                            f"ต้องการยกเลิกโครงการ '{project['Name']}' หรือไม่?",
                            f"delete_project_{project['ProjectID']}",
                        ):
                            project_manager.delete_project(project["ProjectID"])
                            st.rerun()

            st.markdown("---")

    # Handle edit project
    if "edit_project_id" in st.session_state:
        show_edit_project_modal(project_manager, st.session_state.edit_project_id)

    # Handle view project details
    if "view_project_id" in st.session_state:
        show_project_details_modal(project_manager, st.session_state.view_project_id)


def show_create_project_form(project_manager: ProjectManager, user_manager):
    """Show create project form"""
    with st.form("create_project_form"):
        st.subheader("➕ สร้างโครงการใหม่")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("ชื่อโครงการ *", placeholder="ชื่อโครงการ")
            client_name = st.text_input("ชื่อลูกค้า", placeholder="ชื่อบริษัทหรือลูกค้า")
            status = st.selectbox(
                "สถานะ", options=["Planning", "In Progress", "On Hold"]
            )
            start_date = st.date_input("วันที่เริ่มต้น *")

        with col2:
            # Get managers
            managers = safe_execute(
                user_manager.get_users_by_role, "Project Manager", default_return=[]
            )
            manager_options = {
                f"{m['FirstName']} {m['LastName']}": m["UserID"] for m in managers
            }

            if manager_options:
                selected_manager = st.selectbox(
                    "ผู้จัดการโครงการ *", options=list(manager_options.keys())
                )
                manager_id = manager_options[selected_manager]
            else:
                st.error("ไม่พบผู้จัดการโครงการในระบบ")
                manager_id = None

            priority = st.selectbox(
                "ระดับความสำคัญ", options=["Low", "Medium", "High", "Critical"]
            )
            budget = st.number_input(
                "งบประมาณ (บาท)", min_value=0.0, value=0.0, step=1000.0
            )
            end_date = st.date_input("วันที่สิ้นสุด *")

        description = st.text_area(
            "รายละเอียดโครงการ *",
            height=100,
            placeholder="อธิบายรายละเอียดและเป้าหมายของโครงการ",
        )

        if st.form_submit_button("✅ สร้างโครงการ", type="primary"):
            if name and description and start_date and end_date and manager_id:
                if end_date >= start_date:
                    project_data = {
                        "Name": name,
                        "Description": description,
                        "StartDate": start_date,
                        "EndDate": end_date,
                        "Status": status,
                        "Priority": priority,
                        "Budget": budget,
                        "ClientName": client_name,
                        "ManagerID": manager_id,
                    }

                    if project_manager.create_project(project_data):
                        st.rerun()
                else:
                    st.error("❌ วันที่สิ้นสุดต้องมากกว่าหรือเท่ากับวันที่เริ่มต้น")
            else:
                st.error("❌ กรุณากรอกข้อมูลที่จำเป็น (*)")


def show_edit_project_modal(project_manager: ProjectManager, project_id: int):
    """Show edit project modal"""
    project = safe_execute(
        project_manager.get_project_by_id, project_id, default_return=None
    )

    if not project:
        st.error("ไม่พบโครงการ")
        return

    with st.expander(f"✏️ แก้ไขโครงการ: {project['Name']}", expanded=True):
        with st.form(f"edit_project_form_{project_id}"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("ชื่อโครงการ", value=project["Name"])
                client_name = st.text_input(
                    "ชื่อลูกค้า", value=project.get("ClientName", "")
                )
                status = st.selectbox(
                    "สถานะ",
                    options=["Planning", "In Progress", "On Hold", "Completed"],
                    index=["Planning", "In Progress", "On Hold", "Completed"].index(
                        project["Status"]
                    ),
                )
                start_date = st.date_input(
                    "วันที่เริ่มต้น", value=project["StartDate"].date()
                )

            with col2:
                priority = st.selectbox(
                    "ระดับความสำคัญ",
                    options=["Low", "Medium", "High", "Critical"],
                    index=["Low", "Medium", "High", "Critical"].index(
                        project["Priority"]
                    ),
                )
                budget = st.number_input(
                    "งบประมาณ (บาท)", value=float(project.get("Budget", 0))
                )
                end_date = st.date_input("วันที่สิ้นสุด", value=project["EndDate"].date())
                completion = st.slider(
                    "ความคืบหน้า (%)",
                    0,
                    100,
                    value=project.get("CompletionPercentage", 0),
                )

            description = st.text_area(
                "รายละเอียดโครงการ", value=project.get("Description", "")
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.form_submit_button("✅ บันทึกการแก้ไข", type="primary"):
                    updated_data = {
                        "Name": name,
                        "Description": description,
                        "StartDate": start_date,
                        "EndDate": end_date,
                        "Status": status,
                        "Priority": priority,
                        "Budget": budget,
                        "ClientName": client_name,
                        "ManagerID": project["ManagerID"],  # Keep existing manager
                        "CompletionPercentage": completion,
                    }

                    if project_manager.update_project(project_id, updated_data):
                        del st.session_state.edit_project_id
                        st.rerun()

            with col2:
                if st.form_submit_button("❌ ยกเลิก"):
                    del st.session_state.edit_project_id
                    st.rerun()


def show_project_details_modal(project_manager: ProjectManager, project_id: int):
    """Show project details modal"""
    project = safe_execute(
        project_manager.get_project_by_id, project_id, default_return=None
    )

    if not project:
        st.error("ไม่พบโครงการ")
        return

    with st.expander(f"📊 รายละเอียดโครงการ: {project['Name']}", expanded=True):
        ui = UIComponents()

        # Basic info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### ข้อมูลพื้นฐาน")
            st.markdown(f"**ชื่อโครงการ:** {project['Name']}")
            st.markdown(f"**ลูกค้า:** {project.get('ClientName', 'N/A')}")
            st.markdown(f"**ผู้จัดการ:** {project.get('ManagerName', 'N/A')}")
            st.markdown(
                f"**สถานะ:** {ui.render_status_badge(project['Status'])}",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"**ความสำคัญ:** {ui.render_priority_badge(project['Priority'])}",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown("### ข้อมูลทางการเงิน")
            st.markdown(f"**งบประมาณ:** {project.get('Budget', 0):,.2f} บาท")
            st.markdown(f"**ค่าใช้จ่ายจริง:** {project.get('ActualCost', 0):,.2f} บาท")
            budget_used = (
                (project.get("ActualCost", 0) / project.get("Budget", 1)) * 100
                if project.get("Budget", 0) > 0
                else 0
            )
            st.markdown(f"**ใช้งบประมาณ:** {budget_used:.1f}%")

        with col3:
            st.markdown("### ข้อมูลเวลา")
            if project["StartDate"]:
                st.markdown(f"**วันเริ่มต้น:** {project['StartDate'].strftime('%d/%m/%Y')}")
            if project["EndDate"]:
                st.markdown(f"**วันสิ้นสุด:** {project['EndDate'].strftime('%d/%m/%Y')}")
                days_remaining = (project["EndDate"].date() - date.today()).days
                if days_remaining < 0:
                    st.markdown(f"**สถานะ:** เลยกำหนด {abs(days_remaining)} วัน")
                else:
                    st.markdown(f"**เหลือเวลา:** {days_remaining} วัน")

        # Progress
        st.markdown("### ความคืบหน้า")
        completion = project.get("CompletionPercentage", 0)
        ui.render_progress_bar(completion)

        # Description
        st.markdown("### รายละเอียด")
        st.markdown(project.get("Description", "ไม่มีรายละเอียด"))

        # Project statistics
        stats = safe_execute(
            project_manager.get_project_statistics, project_id, default_return={}
        )
        if stats:
            st.markdown("### สถิติงาน")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("งานทั้งหมด", stats.get("total_tasks", 0))
            with col2:
                st.metric("งานเสร็จแล้ว", stats.get("completed_tasks", 0))
            with col3:
                st.metric("งานเลยกำหนด", stats.get("overdue_tasks", 0))
            with col4:
                avg_completion = stats.get("avg_completion", 0) or 0
                st.metric("ความคืบหน้าเฉลี่ย", f"{avg_completion:.1f}%")

        if st.button("❌ ปิด", key=f"close_detail_{project_id}"):
            del st.session_state.view_project_id
            st.rerun()


def show_project_statistics(project_manager: ProjectManager):
    """Show project statistics and charts"""
    ui = UIComponents()

    st.subheader("📊 สถิติโครงการ")

    # Get all projects for statistics
    projects = safe_execute(project_manager.get_all_projects, default_return=[])

    if not projects:
        st.info("ไม่มีข้อมูลโครงการ")
        return

    df = pd.DataFrame(projects)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_projects = len(df)
        st.metric("โครงการทั้งหมด", total_projects)

    with col2:
        active_projects = len(df[df["Status"].isin(["Planning", "In Progress"])])
        st.metric("โครงการที่กำลังดำเนินการ", active_projects)

    with col3:
        completed_projects = len(df[df["Status"] == "Completed"])
        completion_rate = (
            (completed_projects / total_projects * 100) if total_projects > 0 else 0
        )
        st.metric("อัตราความสำเร็จ", f"{completion_rate:.1f}%")

    with col4:
        total_budget = df["Budget"].sum()
        st.metric("งบประมาณรวม", f"{total_budget:,.0f} บาท")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("การกระจายสถานะโครงการ")
        if len(df) > 0:
            status_counts = df["Status"].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="สถานะโครงการ",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("การกระจายความสำคัญ")
        if len(df) > 0:
            priority_counts = df["Priority"].value_counts()
            fig = px.bar(
                x=priority_counts.index,
                y=priority_counts.values,
                title="ระดับความสำคัญของโครงการ",
            )
            fig.update_layout(xaxis_title="ความสำคัญ", yaxis_title="จำนวน")
            st.plotly_chart(fig, use_container_width=True)

    # Timeline chart
    st.subheader("Timeline โครงการ")
    if len(df) > 0 and "StartDate" in df.columns and "EndDate" in df.columns:
        # Filter projects with valid dates
        timeline_df = df.dropna(subset=["StartDate", "EndDate"])

        if len(timeline_df) > 0:
            fig = go.Figure()

            for _, project in timeline_df.iterrows():
                fig.add_trace(
                    go.Scatter(
                        x=[project["StartDate"], project["EndDate"]],
                        y=[project["Name"], project["Name"]],
                        mode="lines+markers",
                        name=project["Name"],
                        line=dict(width=10),
                        hovertemplate=f"<b>{project['Name']}</b><br>"
                        + f"เริ่ม: {project['StartDate'].strftime('%d/%m/%Y')}<br>"
                        + f"สิ้นสุด: {project['EndDate'].strftime('%d/%m/%Y')}<br>"
                        + f"สถานะ: {project['Status']}<extra></extra>",
                    )
                )

            fig.update_layout(
                title="Timeline โครงการ",
                xaxis_title="เวลา",
                yaxis_title="โครงการ",
                height=max(400, len(timeline_df) * 50),
            )

            st.plotly_chart(fig, use_container_width=True)

    # Budget analysis
    st.subheader("การวิเคราะห์งบประมาณ")
    if len(df) > 0 and "Budget" in df.columns:
        col1, col2 = st.columns(2)

        with col1:
            # Budget by status
            budget_by_status = df.groupby("Status")["Budget"].sum()
            fig = px.bar(
                x=budget_by_status.index,
                y=budget_by_status.values,
                title="งบประมาณตามสถานะ",
            )
            fig.update_layout(xaxis_title="สถานะ", yaxis_title="งบประมาณ (บาท)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Top 10 projects by budget
            top_projects = df.nlargest(10, "Budget")
            fig = px.bar(
                top_projects,
                x="Budget",
                y="Name",
                orientation="h",
                title="โครงการที่มีงบประมาณสูงสุด 10 อันดับ",
            )
            fig.update_layout(xaxis_title="งบประมาณ (บาท)", yaxis_title="โครงการ")
            st.plotly_chart(fig, use_container_width=True)
