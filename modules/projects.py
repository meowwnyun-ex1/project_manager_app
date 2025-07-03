"""
Projects Management Module
"""

import streamlit as st
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProjectManager:
    """Project management and CRUD operations"""

    def __init__(self, db_manager):
        self.db = db_manager

    def render_page(self):
        """Render projects management page"""
        st.title("📁 Project Management")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Your Projects")

        with col2:
            if st.button("➕ New Project", use_container_width=True):
                st.session_state.show_new_project = True

        # New project form
        if st.session_state.get("show_new_project", False):
            self._render_new_project_form()

        # Load and display projects
        projects = self.get_all_projects()

        if projects:
            self._render_project_filters_and_list(projects)
        else:
            st.info(
                "📋 No projects found. Create your first project using the button above!"
            )

    def _render_new_project_form(self):
        """Render new project creation form"""
        with st.expander("Create New Project", expanded=True):
            with st.form("new_project_form", clear_on_submit=False):
                col1, col2 = st.columns(2)

                with col1:
                    name = st.text_input(
                        "Project Name *", placeholder="Enter project name"
                    )
                    description = st.text_area(
                        "Description", placeholder="Project description"
                    )
                    client_name = st.text_input(
                        "Client Name", placeholder="Client or department"
                    )

                with col2:
                    status = st.selectbox(
                        "Status",
                        ["Planning", "In Progress", "Review", "Completed", "On Hold"],
                    )
                    priority = st.selectbox(
                        "Priority", ["Low", "Medium", "High", "Critical"]
                    )
                    budget = st.number_input(
                        "Budget ($)", min_value=0.0, step=1000.0, value=0.0
                    )

                col3, col4 = st.columns(2)
                with col3:
                    start_date = st.date_input(
                        "Start Date", value=datetime.now().date()
                    )
                with col4:
                    end_date = st.date_input(
                        "End Date", value=datetime.now().date() + timedelta(days=30)
                    )

                col_submit, col_cancel = st.columns(2)

                with col_submit:
                    submitted = st.form_submit_button(
                        "🚀 Create Project", use_container_width=True
                    )

                with col_cancel:
                    cancel = st.form_submit_button(
                        "❌ Cancel", use_container_width=True
                    )

                if submitted:
                    if not name.strip():
                        st.error("❌ Project name is required!")
                    elif end_date <= start_date:
                        st.error("❌ End date must be after start date!")
                    else:
                        # Get current user ID
                        user_id = st.session_state.user["UserID"]

                        project_data = {
                            "name": name.strip(),
                            "description": description.strip(),
                            "client_name": client_name.strip(),
                            "status": status,
                            "priority": priority,
                            "budget": budget,
                            "start_date": start_date,
                            "end_date": end_date,
                            "created_by": user_id,
                        }

                        with st.spinner("🔄 Creating project..."):
                            success, message = self.create_project(project_data)

                            if success:
                                st.success(f"✅ Project '{name}' created successfully!")
                                st.session_state.show_new_project = False
                                # Clear cache and rerun
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to create project: {message}")

                if cancel:
                    st.session_state.show_new_project = False
                    st.rerun()

    def _render_project_filters_and_list(self, projects: List[Dict[str, Any]]):
        """Render project filters and project list"""
        st.info(f"📊 Found {len(projects)} projects in database")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + list(set([p["Status"] for p in projects if p.get("Status")])),
            )

        with col2:
            priority_filter = st.selectbox(
                "Filter by Priority",
                ["All"]
                + list(set([p["Priority"] for p in projects if p.get("Priority")])),
            )

        with col3:
            search = st.text_input("Search Projects", placeholder="Search by name...")

        # Apply filters
        filtered_projects = self._apply_filters(
            projects, status_filter, priority_filter, search
        )

        # Display projects
        self._render_project_cards(filtered_projects)

    def _apply_filters(
        self,
        projects: List[Dict[str, Any]],
        status_filter: str,
        priority_filter: str,
        search: str,
    ) -> List[Dict[str, Any]]:
        """Apply filters to project list"""
        filtered = projects

        if status_filter != "All":
            filtered = [p for p in filtered if p.get("Status") == status_filter]

        if priority_filter != "All":
            filtered = [p for p in filtered if p.get("Priority") == priority_filter]

        if search:
            filtered = [
                p
                for p in filtered
                if search.lower() in p.get("ProjectName", "").lower()
            ]

        return filtered

    def _render_project_cards(self, projects: List[Dict[str, Any]]):
        """Render project cards"""
        for project in projects:
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(
                        f"""
                    <div class="project-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0 0 10px 0; color: #2E3440;">{project.get('ProjectName', 'Unnamed Project')}</h3>
                                <p style="color: #5E6C7E; margin-bottom: 15px;">{project.get('Description', 'No description')}</p>
                                
                                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 15px;">
                                    <div>
                                        <strong>📅 Timeline:</strong><br>
                                        {project.get('StartDate', 'N/A')} - {project.get('EndDate', 'N/A')}
                                    </div>
                                    <div>
                                        <strong>🏢 Client:</strong><br>
                                        {project.get('ClientName', 'Internal')}
                                    </div>
                                    <div>
                                        <strong>💰 Budget:</strong><br>
                                        ${project.get('Budget', 0):,.2f}
                                    </div>
                                    <div>
                                        <strong>📈 Progress:</strong><br>
                                        {project.get('Progress', 0)}%
                                    </div>
                                </div>
                            </div>
                            
                            <div style="margin-left: 20px; text-align: right;">
                                <span class="status-badge status-{project.get('Status', 'unknown').lower().replace(' ', '-')}">{project.get('Status', 'Unknown')}</span><br><br>
                                <span class="priority-badge priority-{project.get('Priority', 'medium').lower()}">{project.get('Priority', 'Medium')}</span>
                            </div>
                        </div>
                        
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {project.get('Progress', 0)}%;"></div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with col2:
                    # Action buttons
                    col_edit, col_delete = st.columns(2)

                    with col_edit:
                        if st.button(
                            "✏️",
                            key=f"edit_{project.get('ProjectID', 0)}",
                            help="Edit Project",
                        ):
                            st.session_state.edit_project_id = project.get("ProjectID")
                            st.info("Edit functionality coming soon!")

                    with col_delete:
                        if st.button(
                            "🗑️",
                            key=f"delete_{project.get('ProjectID', 0)}",
                            help="Delete Project",
                        ):
                            if st.session_state.get(
                                f"confirm_delete_{project.get('ProjectID', 0)}", False
                            ):
                                success = self.delete_project(project.get("ProjectID"))
                                if success:
                                    st.success("✅ Project deleted!")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete project")
                            else:
                                st.session_state[
                                    f"confirm_delete_{project.get('ProjectID', 0)}"
                                ] = True
                                st.warning("Click again to confirm deletion")

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from database"""
        try:
            query = """
            SELECT 
                ProjectID,
                ProjectName,
                Description,
                StartDate,
                EndDate,
                Status,
                Priority,
                Progress,
                Budget,
                ActualBudget,
                ClientName,
                CreatedDate,
                LastModifiedDate,
                CreatedBy
            FROM Projects
            ORDER BY CreatedDate DESC
            """

            results = self.db.execute_query(query)
            logger.info(f"✅ Loaded {len(results)} projects")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to load projects: {str(e)}")
            return []

    def create_project(self, project_data: Dict[str, Any]) -> tuple[bool, str]:
        """Create a new project"""
        try:
            query = """
            INSERT INTO Projects (
                ProjectName, Description, StartDate, EndDate, Status, Priority,
                Budget, ClientName, CreatedBy, CreatedDate, LastModifiedDate,
                Progress, HealthScore
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE(), 0, 80)
            """

            params = (
                project_data["name"],
                project_data["description"],
                project_data["start_date"],
                project_data["end_date"],
                project_data["status"],
                project_data["priority"],
                project_data["budget"],
                project_data["client_name"],
                project_data["created_by"],
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                logger.info(f"✅ Created project: {project_data['name']}")
                return True, "Project created successfully"
            else:
                return False, "No rows affected"

        except Exception as e:
            logger.error(f"❌ Failed to create project: {str(e)}")
            return False, str(e)

    def update_project(
        self, project_id: int, project_data: Dict[str, Any]
    ) -> tuple[bool, str]:
        """Update existing project"""
        try:
            query = """
            UPDATE Projects SET
                ProjectName = ?, Description = ?, StartDate = ?, EndDate = ?,
                Status = ?, Priority = ?, Budget = ?, ClientName = ?,
                LastModifiedDate = GETDATE()
            WHERE ProjectID = ?
            """

            params = (
                project_data["name"],
                project_data["description"],
                project_data["start_date"],
                project_data["end_date"],
                project_data["status"],
                project_data["priority"],
                project_data["budget"],
                project_data["client_name"],
                project_id,
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                logger.info(f"✅ Updated project ID: {project_id}")
                return True, "Project updated successfully"
            else:
                return False, "Project not found or no changes made"

        except Exception as e:
            logger.error(f"❌ Failed to update project: {str(e)}")
            return False, str(e)

    def delete_project(self, project_id: int) -> bool:
        """Delete project"""
        try:
            # Check if project has tasks
            task_count = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Tasks WHERE ProjectID = ?", (project_id,)
            )

            if task_count > 0:
                logger.warning(
                    f"Cannot delete project {project_id} - has {task_count} tasks"
                )
                return False

            # Delete project
            rows_affected = self.db.execute_non_query(
                "DELETE FROM Projects WHERE ProjectID = ?", (project_id,)
            )

            if rows_affected > 0:
                logger.info(f"✅ Deleted project ID: {project_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Failed to delete project: {str(e)}")
            return False

    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            query = """
            SELECT 
                ProjectID, ProjectName, Description, StartDate, EndDate,
                Status, Priority, Progress, Budget, ActualBudget, ClientName,
                CreatedDate, LastModifiedDate, CreatedBy
            FROM Projects
            WHERE ProjectID = ?
            """

            results = self.db.execute_query(query, (project_id,))
            return results[0] if results else None

        except Exception as e:
            logger.error(f"Failed to get project by ID: {str(e)}")
            return None

    def get_projects_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get projects created by user"""
        try:
            query = """
            SELECT 
                ProjectID, ProjectName, Description, StartDate, EndDate,
                Status, Priority, Progress, Budget, ClientName, CreatedDate
            FROM Projects
            WHERE CreatedBy = ?
            ORDER BY CreatedDate DESC
            """

            return self.db.execute_query(query, (user_id,))

        except Exception as e:
            logger.error(f"Failed to get projects by user: {str(e)}")
            return []

    def update_project_progress(self, project_id: int, progress: int) -> bool:
        """Update project progress percentage"""
        try:
            query = """
            UPDATE Projects 
            SET Progress = ?, LastModifiedDate = GETDATE()
            WHERE ProjectID = ?
            """

            rows_affected = self.db.execute_non_query(query, (progress, project_id))

            if rows_affected > 0:
                logger.info(f"Updated progress for project {project_id} to {progress}%")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update project progress: {str(e)}")
            return False
