"""
pages/projects.py
Projects management page
"""

import streamlit as st
from datetime import datetime, date
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
from utils.error_handler import handle_streamlit_errors, safe_execute
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


class ProjectsPage:
    """Projects management page class"""

    def __init__(self, project_manager, user_manager):
        self.project_manager = project_manager
        self.user_manager = user_manager

    @handle_streamlit_errors()
    @monitor_performance("projects_page_render")
    def show(self):
        """Show projects management page"""
        st.title("📁 การจัดการโครงการ")

        # Get current user
        current_user = get_current_user()
        if not current_user:
            st.error("กรุณาเข้าสู่ระบบ")
            return

        # Action buttons
        self._show_action_buttons()

        # Show create project form if requested
        if st.session_state.get("show_new_project", False):
            self._show_create_project_form()

        # Show edit project form if requested
        if st.session_state.get("edit_project_id"):
            self._show_edit_project_form()

        # Main content
        self._show_projects_content()

    def _show_action_buttons(self):
        """Show action buttons"""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        with col1:
            if st.button("➕ สร้างโครงการใหม่", use_container_width=True, type="primary"):
                st.session_state.show_new_project = True
                st.rerun()

        with col2:
            if st.button("🔄 รีเฟรช", use_container_width=True):
                # Clear cache and reload
                st.cache_data.clear()
                st.rerun()

        with col3:
            if st.button("📊 ส่งออกข้อมูล", use_container_width=True):
                self._export_projects_data()

    def _show_create_project_form(self):
        """Show create project form"""
        st.subheader("➕ สร้างโครงการใหม่")

        # Get project templates
        templates = self.project_manager.get_project_templates()
        template_options = ["ไม่ใช้เทมเพลต"] + [t.name for t in templates]

        # Get users for assignment
        users = self.user_manager.get_all_users()
        user_options = {u["UserID"]: f"{u['FirstName']} {u['LastName']}" for u in users}

        form = FormBuilder("create_project_form", modern_style=True)
        form.add_text_input(
            "ชื่อโครงการ",
            "project_name",
            required=True,
            placeholder="กรอกชื่อโครงการ",
            icon="fas fa-project-diagram",
        )
        form.add_textarea(
            "คำอธิบายโครงการ",
            "description",
            placeholder="รายละเอียดของโครงการ",
            icon="fas fa-align-left",
        )
        form.add_text_input(
            "ชื่อลูกค้า",
            "client_name",
            placeholder="ชื่อลูกค้าหรือหน่วยงาน",
            icon="fas fa-building",
        )
        form.add_select_input(
            "เทมเพลตโครงการ", "template", template_options, icon="fas fa-copy"
        )
        form.add_date_input("วันเริ่มโครงการ", "start_date", icon="fas fa-calendar-plus")
        form.add_date_input("วันสิ้นสุดโครงการ", "end_date", icon="fas fa-calendar-check")
        form.add_select_input(
            "สถานะ",
            "status",
            ["Planning", "Active", "On Hold", "Completed", "Cancelled"],
            icon="fas fa-flag",
        )
        form.add_select_input(
            "ความสำคัญ",
            "priority",
            ["Low", "Medium", "High", "Critical"],
            icon="fas fa-exclamation",
        )
        form.add_number_input(
            "งบประมาณ (บาท)",
            "budget",
            min_value=0.0,
            step=1000.0,
            icon="fas fa-money-bill",
        )

        result = form.render(
            submit_label="สร้างโครงการ", cancel_label="ยกเลิก", columns=2
        )

        if result["submitted"]:
            # Validate dates
            start_date = result["data"]["start_date"]
            end_date = result["data"]["end_date"]

            if start_date and end_date and start_date > end_date:
                NotificationManager.show_error("วันเริ่มโครงการต้องไม่เกินวันสิ้นสุด")
                return

            # Prepare project data
            project_data = {
                "name": result["data"]["project_name"],
                "description": result["data"]["description"],
                "client_name": result["data"]["client_name"],
                "start_date": start_date,
                "end_date": end_date,
                "status": result["data"]["status"],
                "priority": result["data"]["priority"],
                "budget": result["data"]["budget"],
                "created_by": st.session_state.user["UserID"],
            }

            # Add template if selected
            selected_template = result["data"]["template"]
            if selected_template != "ไม่ใช้เทมเพลต":
                project_data["template"] = selected_template

            # Create project
            project_id = safe_execute(
                lambda: self.project_manager.create_project(project_data),
                error_message="ไม่สามารถสร้างโครงการได้",
            )

            if project_id:
                NotificationManager.show_success(
                    f"สร้างโครงการ '{project_data['name']}' สำเร็จ!"
                )
                st.session_state.show_new_project = False
                st.rerun()

        elif result["cancelled"]:
            st.session_state.show_new_project = False
            st.rerun()

    def _show_edit_project_form(self):
        """Show edit project form"""
        project_id = st.session_state.get("edit_project_id")
        if not project_id:
            return

        # Get project data
        project = safe_execute(
            lambda: self.project_manager.get_project_by_id(project_id),
            error_message="ไม่สามารถโหลดข้อมูลโครงการได้",
        )

        if not project:
            st.error("ไม่พบโครงการที่ต้องการแก้ไข")
            del st.session_state["edit_project_id"]
            return

        st.subheader(f"✏️ แก้ไขโครงการ: {project['ProjectName']}")

        form = FormBuilder("edit_project_form", modern_style=True)

        # Pre-fill form with existing data
        with st.form("edit_project_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("ชื่อโครงการ", value=project["ProjectName"])
                client_name = st.text_input(
                    "ชื่อลูกค้า", value=project.get("ClientName", "")
                )
                start_date = st.date_input(
                    "วันเริ่มโครงการ", value=project.get("StartDate")
                )
                status = st.selectbox(
                    "สถานะ",
                    ["Planning", "Active", "On Hold", "Completed", "Cancelled"],
                    index=(
                        [
                            "Planning",
                            "Active",
                            "On Hold",
                            "Completed",
                            "Cancelled",
                        ].index(project["Status"])
                        if project["Status"]
                        in ["Planning", "Active", "On Hold", "Completed", "Cancelled"]
                        else 0
                    ),
                )

            with col2:
                description = st.text_area(
                    "คำอธิบาย", value=project.get("Description", ""), height=100
                )
                end_date = st.date_input("วันสิ้นสุดโครงการ", value=project.get("EndDate"))
                priority = st.selectbox(
                    "ความสำคัญ",
                    ["Low", "Medium", "High", "Critical"],
                    index=(
                        ["Low", "Medium", "High", "Critical"].index(project["Priority"])
                        if project["Priority"] in ["Low", "Medium", "High", "Critical"]
                        else 1
                    ),
                )
                budget = st.number_input(
                    "งบประมาณ (บาท)",
                    value=float(project.get("Budget", 0)),
                    min_value=0.0,
                    step=1000.0,
                )

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button(
                    "💾 บันทึกการแก้ไข", use_container_width=True, type="primary"
                )
            with col2:
                cancelled = st.form_submit_button("❌ ยกเลิก", use_container_width=True)

            if submitted:
                # Validate dates
                if start_date and end_date and start_date > end_date:
                    NotificationManager.show_error("วันเริ่มโครงการต้องไม่เกินวันสิ้นสุด")
                    return

                # Update project
                project_data = {
                    "name": name,
                    "description": description,
                    "client_name": client_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "priority": priority,
                    "budget": budget,
                }

                success = safe_execute(
                    lambda: self.project_manager.update_project(
                        project_id, project_data
                    ),
                    error_message="ไม่สามารถอัพเดทโครงการได้",
                )

                if success:
                    NotificationManager.show_success("อัพเดทโครงการสำเร็จ!")
                    del st.session_state["edit_project_id"]
                    st.rerun()

            elif cancelled:
                del st.session_state["edit_project_id"]
                st.rerun()

    def _show_projects_content(self):
        """Show main projects content"""
        # Get projects data
        with st.spinner("กำลังโหลดโครงการ..."):
            projects = safe_execute(
                lambda: self.project_manager.get_all_projects(),
                default_return=[],
                error_message="ไม่สามารถโหลดรายการโครงการได้",
            )

        if not projects:
            st.info("ยังไม่มีโครงการ กรุณาสร้างโครงการใหม่")
            return

        # Show filters
        self._show_filters()

        # Apply filters
        filtered_projects = self._apply_filters(projects)

        # Show view options
        view_mode = st.radio(
            "รูปแบบการแสดง", ["การ์ด", "ตาราง"], horizontal=True, key="project_view_mode"
        )

        if view_mode == "การ์ด":
            self._show_projects_cards(filtered_projects)
        else:
            self._show_projects_table(filtered_projects)

    def _show_filters(self):
        """Show project filters"""
        with st.expander("🔍 ตัวกรอง", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.selectbox(
                    "สถานะ",
                    [
                        "ทั้งหมด",
                        "Planning",
                        "Active",
                        "On Hold",
                        "Completed",
                        "Cancelled",
                    ],
                    key="filter_status",
                )

            with col2:
                st.selectbox(
                    "ความสำคัญ",
                    ["ทั้งหมด", "Low", "Medium", "High", "Critical"],
                    key="filter_priority",
                )

            with col3:
                st.text_input(
                    "ค้นหา", placeholder="ชื่อโครงการ, ลูกค้า...", key="filter_search"
                )

            with col4:
                st.selectbox(
                    "เรียงตาม",
                    ["วันที่สร้างล่าสุด", "ชื่อ A-Z", "ความสำคัญ", "สถานะ"],
                    key="filter_sort",
                )

    def _apply_filters(self, projects: List[Dict]) -> List[Dict]:
        """Apply filters to projects list"""
        filtered_projects = projects.copy()

        # Status filter
        status_filter = st.session_state.get("filter_status", "ทั้งหมด")
        if status_filter != "ทั้งหมด":
            filtered_projects = [
                p for p in filtered_projects if p["Status"] == status_filter
            ]

        # Priority filter
        priority_filter = st.session_state.get("filter_priority", "ทั้งหมด")
        if priority_filter != "ทั้งหมด":
            filtered_projects = [
                p for p in filtered_projects if p["Priority"] == priority_filter
            ]

        # Search filter
        search_term = st.session_state.get("filter_search", "").lower()
        if search_term:
            filtered_projects = [
                p
                for p in filtered_projects
                if search_term in p["ProjectName"].lower()
                or search_term in (p.get("ClientName", "") or "").lower()
            ]

        # Sort
        sort_option = st.session_state.get("filter_sort", "วันที่สร้างล่าสุด")
        if sort_option == "ชื่อ A-Z":
            filtered_projects.sort(key=lambda x: x["ProjectName"])
        elif sort_option == "ความสำคัญ":
            priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            filtered_projects.sort(key=lambda x: priority_order.get(x["Priority"], 4))
        elif sort_option == "สถานะ":
            filtered_projects.sort(key=lambda x: x["Status"])
        else:  # วันที่สร้างล่าสุด
            filtered_projects.sort(
                key=lambda x: x.get("CreatedDate", datetime.min), reverse=True
            )

        return filtered_projects

    def _show_projects_cards(self, projects: List[Dict]):
        """Show projects in card format"""
        st.subheader(f"📋 โครงการ ({len(projects)} โครงการ)")

        # Show projects in grid
        cols_per_row = 2
        for i in range(0, len(projects), cols_per_row):
            cols = st.columns(cols_per_row)

            for j, col in enumerate(cols):
                if i + j < len(projects):
                    project = projects[i + j]

                    with col:
                        # Custom card with action buttons
                        st.markdown('<div class="modern-card">', unsafe_allow_html=True)

                        # Card header
                        st.markdown(
                            f"""
                        <div class="card-header">
                            <div class="card-title">
                                <i class="fas fa-project-diagram"></i>
                                {project['ProjectName']}
                            </div>
                            <div>
                                <span class="status-badge status-{project['Status'].lower().replace(' ', '-')}">
                                    {project['Status']}
                                </span>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Card body
                        description = project.get("Description", "ไม่มีคำอธิบาย")
                        if len(description) > 100:
                            description = description[:100] + "..."

                        st.write(description)

                        # Progress
                        completion = project.get("CompletionPercentage", 0)
                        st.progress(completion / 100)
                        st.caption(f"ความคืบหน้า: {completion:.1f}%")

                        # Stats
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        with col_stat1:
                            st.metric("งานทั้งหมด", project.get("TaskCount", 0))
                        with col_stat2:
                            st.metric("เสร็จแล้ว", project.get("CompletedTasks", 0))
                        with col_stat3:
                            if project.get("Budget"):
                                st.metric("งบประมาณ", f"₿{project['Budget']:,.0f}")

                        # Action buttons
                        col_btn1, col_btn2, col_btn3 = st.columns(3)

                        with col_btn1:
                            if st.button(
                                "👁️",
                                key=f"view_{project['ProjectID']}",
                                help="ดูรายละเอียด",
                            ):
                                st.session_state.selected_project = project["ProjectID"]
                                st.session_state.current_page = "Tasks"
                                st.rerun()

                        with col_btn2:
                            if st.button(
                                "✏️", key=f"edit_{project['ProjectID']}", help="แก้ไข"
                            ):
                                st.session_state.edit_project_id = project["ProjectID"]
                                st.rerun()

                        with col_btn3:
                            if st.button(
                                "🗑️", key=f"delete_{project['ProjectID']}", help="ลบ"
                            ):
                                st.session_state.delete_project_id = project[
                                    "ProjectID"
                                ]
                                st.rerun()

                        # Card footer
                        st.caption(f"ผู้สร้าง: {project.get('CreatorName', 'Unknown')}")
                        if project.get("CreatedDate"):
                            st.caption(
                                f"วันที่สร้าง: {project['CreatedDate'].strftime('%d/%m/%Y')}"
                            )

                        st.markdown("</div>", unsafe_allow_html=True)

        # Handle delete confirmation
        if st.session_state.get("delete_project_id"):
            self._show_delete_confirmation()

    def _show_projects_table(self, projects: List[Dict]):
        """Show projects in table format"""
        st.subheader(f"📊 ตารางโครงการ ({len(projects)} โครงการ)")

        if not projects:
            st.info("ไม่มีโครงการที่ตรงกับเงื่อนไขการกรอง")
            return

        # Prepare data for table
        table_data = []
        for project in projects:
            table_data.append(
                {
                    "ชื่อโครงการ": project["ProjectName"],
                    "ลูกค้า": project.get("ClientName", ""),
                    "สถานะ": project["Status"],
                    "ความสำคัญ": project["Priority"],
                    "ความคืบหน้า": f"{project.get('CompletionPercentage', 0):.1f}%",
                    "งานทั้งหมด": project.get("TaskCount", 0),
                    "งานเสร็จแล้ว": project.get("CompletedTasks", 0),
                    "ผู้สร้าง": project.get("CreatorName", ""),
                    "วันที่สร้าง": (
                        project["CreatedDate"].strftime("%d/%m/%Y")
                        if project.get("CreatedDate")
                        else ""
                    ),
                    "การดำเนินการ": project["ProjectID"],
                }
            )

        # Display table
        DataTable.render(
            table_data,
            searchable=True,
            sortable=True,
            page_size=10,
            actions=[
                {
                    "label": "📊 ส่งออก Excel",
                    "callback": lambda: self._export_projects_data(),
                }
            ],
        )

        # Action buttons for selected projects
        st.markdown("**การดำเนินการ:**")
        selected_projects = st.multiselect(
            "เลือกโครงการ",
            options=[p["ProjectID"] for p in projects],
            format_func=lambda x: next(
                (p["ProjectName"] for p in projects if p["ProjectID"] == x),
                f"Project {x}",
            ),
        )

        if selected_projects:
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📊 ส่งออกที่เลือก", use_container_width=True):
                    self._export_selected_projects(selected_projects)

            with col2:
                if st.button("📁 เก็บถาวร", use_container_width=True):
                    self._archive_selected_projects(selected_projects)

            with col3:
                if st.button("🗑️ ลบที่เลือก", use_container_width=True, type="secondary"):
                    st.session_state.delete_selected_projects = selected_projects
                    st.rerun()

    def _show_delete_confirmation(self):
        """Show delete confirmation modal"""
        project_id = st.session_state.get("delete_project_id")
        if not project_id:
            return

        # Get project info
        project = safe_execute(
            lambda: self.project_manager.get_project_by_id(project_id),
            error_message="ไม่สามารถโหลดข้อมูลโครงการได้",
        )

        if not project:
            del st.session_state["delete_project_id"]
            return

        result = ModernModal.show_confirmation(
            "ยืนยันการลบโครงการ",
            f"คุณต้องการลบโครงการ '{project['ProjectName']}' หรือไม่?\n\nการดำเนินการนี้ไม่สามารถย้อนกลับได้",
            "ลบโครงการ",
            "ยกเลิก",
            danger=True,
        )

        if result is True:
            success = safe_execute(
                lambda: self.project_manager.delete_project(project_id),
                error_message="ไม่สามารถลบโครงการได้",
            )

            if success:
                NotificationManager.show_success(
                    f"ลบโครงการ '{project['ProjectName']}' สำเร็จ"
                )
                del st.session_state["delete_project_id"]
                st.rerun()

        elif result is False:
            del st.session_state["delete_project_id"]
            st.rerun()

    def _export_projects_data(self):
        """Export all projects data"""
        try:
            projects = self.project_manager.export_project_data()

            if projects:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"projects_export_{timestamp}.xlsx"

                ExportManager.export_to_excel(projects, filename)
                NotificationManager.show_success("ส่งออกข้อมูลโครงการสำเร็จ")
            else:
                NotificationManager.show_warning("ไม่มีข้อมูลโครงการให้ส่งออก")

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            NotificationManager.show_error("ไม่สามารถส่งออกข้อมูลได้")

    def _export_selected_projects(self, project_ids: List[int]):
        """Export selected projects"""
        try:
            projects = self.project_manager.export_project_data(project_ids)

            if projects:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"selected_projects_{timestamp}.xlsx"

                ExportManager.export_to_excel(projects, filename)
                NotificationManager.show_success(
                    f"ส่งออกข้อมูล {len(projects)} โครงการสำเร็จ"
                )
            else:
                NotificationManager.show_warning("ไม่มีข้อมูลโครงการที่เลือก")

        except Exception as e:
            logger.error(f"Selected export failed: {str(e)}")
            NotificationManager.show_error("ไม่สามารถส่งออกข้อมูลได้")

    def _archive_selected_projects(self, project_ids: List[int]):
        """Archive selected projects"""
        try:
            archived_count = 0

            for project_id in project_ids:
                success = self.project_manager.archive_project(project_id)
                if success:
                    archived_count += 1

            if archived_count > 0:
                NotificationManager.show_success(
                    f"เก็บถาวร {archived_count} โครงการสำเร็จ"
                )
                st.rerun()
            else:
                NotificationManager.show_error("ไม่สามารถเก็บถาวรโครงการได้")

        except Exception as e:
            logger.error(f"Archive failed: {str(e)}")
            NotificationManager.show_error("ไม่สามารถเก็บถาวรโครงการได้")
