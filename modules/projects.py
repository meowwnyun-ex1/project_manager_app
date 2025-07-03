#!/usr/bin/env python3
"""
modules/projects.py
Complete Project Management System for DENSO Project Manager Pro
"""
import logging
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProjectStatus:
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


@dataclass
class ProjectPriority:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ProjectManager:
    """Complete project management functionality"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.status_options = [
            ProjectStatus.PLANNING,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.ON_HOLD,
            ProjectStatus.COMPLETED,
            ProjectStatus.CANCELLED,
        ]
        self.priority_options = [
            ProjectPriority.LOW,
            ProjectPriority.MEDIUM,
            ProjectPriority.HIGH,
            ProjectPriority.CRITICAL,
        ]

    def render_project_management(self):
        """Main project management interface"""
        st.title("📁 การจัดการโครงการ")

        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📋 รายการโครงการ", "➕ สร้างโครงการ", "📊 สถิติ", "🔍 ค้นหา"]
        )

        with tab1:
            self._render_projects_list()

        with tab2:
            self._render_create_project()

        with tab3:
            self._render_project_statistics()

        with tab4:
            self._render_project_search()

    def _render_projects_list(self):
        """Render projects list with filtering and actions"""
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            status_filter = st.selectbox(
                "🔍 กรองตามสถานะ", ["ทั้งหมด"] + self.status_options
            )

        with col2:
            sort_by = st.selectbox(
                "📊 เรียงตาม", ["วันที่สร้าง", "ชื่อโครงการ", "กำหนดส่ง", "สถานะ"]
            )

        with col3:
            items_per_page = st.selectbox("📄 แสดงต่อหน้า", [10, 25, 50, 100])

        # Get projects with filtering
        projects = self._get_projects_filtered(status_filter, sort_by)

        if projects:
            # Convert to DataFrame for better display
            df = pd.DataFrame(projects)

            # Add action buttons
            for idx, project in enumerate(projects):
                with st.expander(f"📁 {project['Name']} ({project['Status']})"):
                    self._render_project_detail(project, idx)

            # Pagination
            if len(projects) > items_per_page:
                self._render_pagination(len(projects), items_per_page)
        else:
            st.info("📝 ยังไม่มีโครงการในระบบ")

    def _render_project_detail(self, project: Dict[str, Any], index: int):
        """Render detailed project information with actions"""
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(
                f"**📋 รายละเอียด:** {project.get('Description', 'ไม่มีรายละเอียด')}"
            )
            st.markdown(f"**👤 ผู้จัดการ:** {project.get('ManagerName', 'ไม่ระบุ')}")
            st.markdown(f"**🏢 ลูกค้า:** {project.get('ClientName', 'ไม่ระบุ')}")

            # Progress calculation
            progress = self._calculate_project_progress(project["ProjectID"])
            st.progress(progress / 100)
            st.caption(f"ความคืบหน้า: {progress:.1f}%")

        with col2:
            # Status badge
            status_color = self._get_status_color(project["Status"])
            st.markdown(f"**สถานะ:** {status_color} {project['Status']}")

            # Priority badge
            priority_color = self._get_priority_color(project["Priority"])
            st.markdown(f"**ความสำคัญ:** {priority_color} {project['Priority']}")

            # Dates
            if project.get("StartDate"):
                st.markdown(f"**📅 เริ่ม:** {project['StartDate']}")
            if project.get("EndDate"):
                st.markdown(f"**📅 สิ้นสุด:** {project['EndDate']}")

                # Check if overdue
                if (
                    project["EndDate"] < date.today()
                    and project["Status"] != ProjectStatus.COMPLETED
                ):
                    st.warning("⚠️ เลยกำหนด!")

            # Budget
            if project.get("Budget"):
                st.markdown(f"**💰 งบประมาณ:** {project['Budget']:,.2f} บาท")

        # Action buttons
        col_edit, col_tasks, col_delete = st.columns(3)

        with col_edit:
            if st.button("✏️ แก้ไข", key=f"edit_{project['ProjectID']}"):
                self._show_edit_project_modal(project)

        with col_tasks:
            if st.button("📋 งาน", key=f"tasks_{project['ProjectID']}"):
                st.session_state["selected_project_id"] = project["ProjectID"]
                st.switch_page("pages/tasks.py")

        with col_delete:
            if st.button("🗑️ ลบ", key=f"delete_{project['ProjectID']}"):
                self._show_delete_confirmation(project)

    def _render_create_project(self):
        """Render create new project form"""
        st.subheader("➕ สร้างโครงการใหม่")

        with st.form("create_project_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("📁 ชื่อโครงการ *", placeholder="กรอกชื่อโครงการ")
                client_name = st.text_input("🏢 ชื่อลูกค้า", placeholder="ชื่อลูกค้าหรือหน่วยงาน")
                start_date = st.date_input("📅 วันที่เริ่ม", value=date.today())
                status = st.selectbox("📊 สถานะ", self.status_options, index=0)

            with col2:
                description = st.text_area(
                    "📋 รายละเอียด", placeholder="รายละเอียดโครงการ", height=100
                )
                budget = st.number_input(
                    "💰 งบประมาณ (บาท)", min_value=0.0, step=1000.0
                )
                end_date = st.date_input(
                    "📅 วันที่สิ้นสุด", value=date.today() + timedelta(days=30)
                )
                priority = st.selectbox("⚡ ความสำคัญ", self.priority_options, index=1)

            # Manager selection
            managers = self._get_available_managers()
            manager_options = ["ไม่ระบุ"] + [
                f"{m['FirstName']} {m['LastName']} ({m['Username']})" for m in managers
            ]
            selected_manager = st.selectbox("👤 ผู้จัดการโครงการ", manager_options)

            # Submit button
            submitted = st.form_submit_button(
                "🚀 สร้างโครงการ", use_container_width=True, type="primary"
            )

            if submitted:
                if not name:
                    st.error("❌ กรุณากรอกชื่อโครงการ")
                elif end_date < start_date:
                    st.error("❌ วันที่สิ้นสุดต้องมากกว่าวันที่เริ่ม")
                else:
                    # Get manager ID
                    manager_id = None
                    if selected_manager != "ไม่ระบุ":
                        manager_idx = manager_options.index(selected_manager) - 1
                        manager_id = managers[manager_idx]["UserID"]

                    project_data = {
                        "name": name,
                        "description": description,
                        "start_date": start_date,
                        "end_date": end_date,
                        "status": status,
                        "priority": priority,
                        "budget": budget if budget > 0 else None,
                        "client_name": client_name if client_name else None,
                        "manager_id": manager_id,
                    }

                    if self.create_project(project_data):
                        st.success("✅ สร้างโครงการเรียบร้อยแล้ว!")
                        st.rerun()

    def _render_project_statistics(self):
        """Render project statistics dashboard"""
        st.subheader("📊 สถิติโครงการ")

        # Get statistics
        stats = self._get_project_statistics()

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📁 โครงการทั้งหมด", stats["total_projects"])

        with col2:
            st.metric("🚀 กำลังดำเนินการ", stats["active_projects"])

        with col3:
            st.metric("✅ เสร็จสมบูรณ์", stats["completed_projects"])

        with col4:
            st.metric("⚠️ เลยกำหนด", stats["overdue_projects"])

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            # Status distribution pie chart
            if stats["status_distribution"]:
                st.subheader("📊 การกระจายตามสถานะ")
                df_status = pd.DataFrame(
                    list(stats["status_distribution"].items()),
                    columns=["Status", "Count"],
                )
                st.bar_chart(df_status.set_index("Status"))

        with col2:
            # Priority distribution
            if stats["priority_distribution"]:
                st.subheader("⚡ การกระจายตามความสำคัญ")
                df_priority = pd.DataFrame(
                    list(stats["priority_distribution"].items()),
                    columns=["Priority", "Count"],
                )
                st.bar_chart(df_priority.set_index("Priority"))

        # Recent projects table
        st.subheader("📅 โครงการล่าสุด")
        recent_projects = self._get_recent_projects(5)
        if recent_projects:
            df_recent = pd.DataFrame(recent_projects)
            st.dataframe(
                df_recent[["Name", "Status", "Priority", "CreatedDate"]],
                use_container_width=True,
            )

    def _render_project_search(self):
        """Render advanced project search"""
        st.subheader("🔍 ค้นหาโครงการ")

        with st.form("search_form"):
            col1, col2 = st.columns(2)

            with col1:
                search_text = st.text_input(
                    "🔍 ค้นหาข้อความ", placeholder="ชื่อโครงการ, รายละเอียด, ลูกค้า"
                )
                status_search = st.multiselect("📊 สถานะ", self.status_options)
                priority_search = st.multiselect("⚡ ความสำคัญ", self.priority_options)

            with col2:
                date_from = st.date_input(
                    "📅 จากวันที่", value=date.today() - timedelta(days=365)
                )
                date_to = st.date_input("📅 ถึงวันที่", value=date.today())
                budget_range = st.slider(
                    "💰 ช่วงงบประมาณ (บาท)", 0, 10000000, (0, 1000000), step=50000
                )

            search_clicked = st.form_submit_button("🔍 ค้นหา", use_container_width=True)

        if search_clicked:
            results = self._search_projects(
                search_text,
                status_search,
                priority_search,
                date_from,
                date_to,
                budget_range,
            )

            if results:
                st.success(f"✅ พบ {len(results)} โครงการ")
                for project in results:
                    with st.expander(f"📁 {project['Name']}"):
                        self._render_project_detail(project, 0)
            else:
                st.info("📝 ไม่พบโครงการที่ตรงกับเงื่อนไข")

    def create_project(self, project_data: Dict[str, Any]) -> bool:
        """Create new project"""
        try:
            query = """
                INSERT INTO Projects (Name, Description, StartDate, EndDate, Status, Priority, Budget, ClientName, ManagerID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_non_query(
                query,
                (
                    project_data["name"],
                    project_data["description"],
                    project_data["start_date"],
                    project_data["end_date"],
                    project_data["status"],
                    project_data["priority"],
                    project_data["budget"],
                    project_data["client_name"],
                    project_data["manager_id"],
                ),
            )

            logger.info(f"Project '{project_data['name']}' created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return False

    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> bool:
        """Update existing project"""
        try:
            query = """
                UPDATE Projects SET 
                    Name = ?, Description = ?, StartDate = ?, EndDate = ?, 
                    Status = ?, Priority = ?, Budget = ?, ClientName = ?, ManagerID = ?
                WHERE ProjectID = ?
            """
            self.db.execute_non_query(
                query,
                (
                    project_data["name"],
                    project_data["description"],
                    project_data["start_date"],
                    project_data["end_date"],
                    project_data["status"],
                    project_data["priority"],
                    project_data["budget"],
                    project_data["client_name"],
                    project_data["manager_id"],
                    project_id,
                ),
            )

            logger.info(f"Project ID {project_id} updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating project: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return False

    def delete_project(self, project_id: int) -> bool:
        """Delete project (with cascade considerations)"""
        try:
            # Check for existing tasks
            task_count = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Tasks WHERE ProjectID = ?", (project_id,)
            )

            if task_count > 0:
                st.error(f"❌ ไม่สามารถลบได้ เนื่องจากมี {task_count} งานอยู่ในโครงการ")
                return False

            # Delete project
            self.db.execute_non_query(
                "DELETE FROM Projects WHERE ProjectID = ?", (project_id,)
            )

            logger.info(f"Project ID {project_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return False

    def _get_projects_filtered(
        self, status_filter: str, sort_by: str
    ) -> List[Dict[str, Any]]:
        """Get projects with filtering and sorting"""
        try:
            base_query = """
                SELECT p.*, 
                       u.FirstName + ' ' + u.LastName as ManagerName,
                       u.Username as ManagerUsername
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
            """

            where_clause = ""
            params = []

            if status_filter != "ทั้งหมด":
                where_clause = "WHERE p.Status = ?"
                params.append(status_filter)

            # Add sorting
            order_clause = ""
            if sort_by == "ชื่อโครงการ":
                order_clause = "ORDER BY p.Name"
            elif sort_by == "กำหนดส่ง":
                order_clause = "ORDER BY p.EndDate"
            elif sort_by == "สถานะ":
                order_clause = "ORDER BY p.Status"
            else:  # วันที่สร้าง
                order_clause = "ORDER BY p.CreatedDate DESC"

            query = f"{base_query} {where_clause} {order_clause}"

            return self.db.execute_query(query, tuple(params))

        except Exception as e:
            logger.error(f"Error getting filtered projects: {e}")
            return []

    def _get_available_managers(self) -> List[Dict[str, Any]]:
        """Get list of users who can be project managers"""
        try:
            return self.db.execute_query(
                """
                SELECT UserID, Username, FirstName, LastName, Role
                FROM Users 
                WHERE IsActive = 1 AND Role IN ('Admin', 'Project Manager', 'Team Lead')
                ORDER BY FirstName, LastName
            """
            )
        except Exception as e:
            logger.error(f"Error getting managers: {e}")
            return []

    def _calculate_project_progress(self, project_id: int) -> float:
        """Calculate project progress based on completed tasks"""
        try:
            total_tasks = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Tasks WHERE ProjectID = ?", (project_id,)
                )
                or 0
            )

            if total_tasks == 0:
                return 0.0

            completed_tasks = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Tasks WHERE ProjectID = ? AND Status = 'Done'",
                    (project_id,),
                )
                or 0
            )

            return (completed_tasks / total_tasks) * 100

        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            return 0.0

    def _get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics"""
        try:
            stats = {}

            # Basic counts
            stats["total_projects"] = (
                self.db.execute_scalar("SELECT COUNT(*) FROM Projects") or 0
            )
            stats["active_projects"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status IN ('Planning', 'In Progress')"
                )
                or 0
            )
            stats["completed_projects"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status = 'Completed'"
                )
                or 0
            )
            stats["overdue_projects"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE EndDate < GETDATE() AND Status != 'Completed'"
                )
                or 0
            )

            # Status distribution
            status_data = self.db.execute_query(
                "SELECT Status, COUNT(*) as Count FROM Projects GROUP BY Status"
            )
            stats["status_distribution"] = {
                row["Status"]: row["Count"] for row in status_data
            }

            # Priority distribution
            priority_data = self.db.execute_query(
                "SELECT Priority, COUNT(*) as Count FROM Projects GROUP BY Priority"
            )
            stats["priority_distribution"] = {
                row["Priority"]: row["Count"] for row in priority_data
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {}

    def _get_recent_projects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recently created projects"""
        try:
            return self.db.execute_query(
                "SELECT TOP (?) Name, Status, Priority, CreatedDate FROM Projects ORDER BY CreatedDate DESC",
                (limit,),
            )
        except Exception as e:
            logger.error(f"Error getting recent projects: {e}")
            return []

    def _search_projects(
        self,
        search_text: str,
        status_filter: List[str],
        priority_filter: List[str],
        date_from: date,
        date_to: date,
        budget_range: tuple,
    ) -> List[Dict[str, Any]]:
        """Advanced project search"""
        try:
            where_conditions = []
            params = []

            # Text search
            if search_text:
                where_conditions.append(
                    "(p.Name LIKE ? OR p.Description LIKE ? OR p.ClientName LIKE ?)"
                )
                search_param = f"%{search_text}%"
                params.extend([search_param, search_param, search_param])

            # Status filter
            if status_filter:
                placeholders = ",".join("?" * len(status_filter))
                where_conditions.append(f"p.Status IN ({placeholders})")
                params.extend(status_filter)

            # Priority filter
            if priority_filter:
                placeholders = ",".join("?" * len(priority_filter))
                where_conditions.append(f"p.Priority IN ({placeholders})")
                params.extend(priority_filter)

            # Date range
            where_conditions.append("p.CreatedDate BETWEEN ? AND ?")
            params.extend([date_from, date_to])

            # Budget range
            if budget_range[1] > 0:
                where_conditions.append(
                    "(p.Budget BETWEEN ? AND ? OR p.Budget IS NULL)"
                )
                params.extend([budget_range[0], budget_range[1]])

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            query = f"""
                SELECT p.*, u.FirstName + ' ' + u.LastName as ManagerName
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
                {where_clause}
                ORDER BY p.CreatedDate DESC
            """

            return self.db.execute_query(query, tuple(params))

        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return []

    def _get_status_color(self, status: str) -> str:
        """Get color emoji for project status"""
        colors = {
            ProjectStatus.PLANNING: "🟡",
            ProjectStatus.IN_PROGRESS: "🔵",
            ProjectStatus.ON_HOLD: "🟠",
            ProjectStatus.COMPLETED: "🟢",
            ProjectStatus.CANCELLED: "🔴",
        }
        return colors.get(status, "⚪")

    def _get_priority_color(self, priority: str) -> str:
        """Get color emoji for project priority"""
        colors = {
            ProjectPriority.LOW: "🟢",
            ProjectPriority.MEDIUM: "🟡",
            ProjectPriority.HIGH: "🟠",
            ProjectPriority.CRITICAL: "🔴",
        }
        return colors.get(priority, "⚪")

    def _show_edit_project_modal(self, project: Dict[str, Any]):
        """Show edit project modal"""
        st.session_state[f'edit_project_{project["ProjectID"]}'] = True

        with st.form(f"edit_project_form_{project['ProjectID']}"):
            st.subheader(f"✏️ แก้ไขโครงการ: {project['Name']}")

            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("📁 ชื่อโครงการ", value=project["Name"])
                client_name = st.text_input(
                    "🏢 ชื่อลูกค้า", value=project.get("ClientName", "")
                )
                start_date = st.date_input(
                    "📅 วันที่เริ่ม", value=project.get("StartDate", date.today())
                )
                status = st.selectbox(
                    "📊 สถานะ",
                    self.status_options,
                    index=self.status_options.index(project["Status"]),
                )

            with col2:
                description = st.text_area(
                    "📋 รายละเอียด", value=project.get("Description", "")
                )
                budget = st.number_input(
                    "💰 งบประมาณ", value=float(project.get("Budget", 0))
                )
                end_date = st.date_input(
                    "📅 วันที่สิ้นสุด", value=project.get("EndDate", date.today())
                )
                priority = st.selectbox(
                    "⚡ ความสำคัญ",
                    self.priority_options,
                    index=self.priority_options.index(project["Priority"]),
                )

            # Manager selection
            managers = self._get_available_managers()
            manager_options = ["ไม่ระบุ"] + [
                f"{m['FirstName']} {m['LastName']} ({m['Username']})" for m in managers
            ]

            current_manager_idx = 0
            if project.get("ManagerID"):
                for idx, manager in enumerate(managers):
                    if manager["UserID"] == project["ManagerID"]:
                        current_manager_idx = idx + 1
                        break

            selected_manager = st.selectbox(
                "👤 ผู้จัดการโครงการ", manager_options, index=current_manager_idx
            )

            col_save, col_cancel = st.columns(2)

            with col_save:
                if st.form_submit_button(
                    "💾 บันทึก", use_container_width=True, type="primary"
                ):
                    # Get manager ID
                    manager_id = None
                    if selected_manager != "ไม่ระบุ":
                        manager_idx = manager_options.index(selected_manager) - 1
                        manager_id = managers[manager_idx]["UserID"]

                    project_data = {
                        "name": name,
                        "description": description,
                        "start_date": start_date,
                        "end_date": end_date,
                        "status": status,
                        "priority": priority,
                        "budget": budget if budget > 0 else None,
                        "client_name": client_name if client_name else None,
                        "manager_id": manager_id,
                    }

                    if self.update_project(project["ProjectID"], project_data):
                        st.success("✅ อัปเดตโครงการเรียบร้อยแล้ว!")
                        st.rerun()

            with col_cancel:
                if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                    del st.session_state[f'edit_project_{project["ProjectID"]}']
                    st.rerun()

    def _show_delete_confirmation(self, project: Dict[str, Any]):
        """Show delete confirmation dialog"""
        st.warning(f"⚠️ คุณต้องการลบโครงการ '{project['Name']}' หรือไม่?")

        col_confirm, col_cancel = st.columns(2)

        with col_confirm:
            if st.button(
                "🗑️ ยืนยันการลบ",
                key=f"confirm_delete_{project['ProjectID']}",
                type="primary",
            ):
                if self.delete_project(project["ProjectID"]):
                    st.success("✅ ลบโครงการเรียบร้อยแล้ว!")
                    st.rerun()

        with col_cancel:
            if st.button("❌ ยกเลิก", key=f"cancel_delete_{project['ProjectID']}"):
                st.rerun()

    def _render_pagination(self, total_items: int, items_per_page: int):
        """Render pagination controls"""
        total_pages = (total_items + items_per_page - 1) // items_per_page

        if "current_page" not in st.session_state:
            st.session_state.current_page = 1

        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("◀️ ก่อนหน้า") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()

        with col2:
            st.markdown(
                f"<div style='text-align: center'>หน้า {st.session_state.current_page} จาก {total_pages}</div>",
                unsafe_allow_html=True,
            )

        with col3:
            if st.button("▶️ ถัดไป") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()
