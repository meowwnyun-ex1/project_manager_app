"""
Tasks Management Module
"""

import streamlit as st
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TaskManager:
    """Task management and CRUD operations"""

    def __init__(self, db_manager):
        self.db = db_manager

    def render_page(self):
        """Render tasks management page"""
        st.title("✅ Task Management")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Your Tasks")

        with col2:
            if st.button("➕ New Task", use_container_width=True):
                st.session_state.show_new_task = True

        # New task form
        if st.session_state.get("show_new_task", False):
            self._render_new_task_form()

        # Load and display tasks
        tasks = self.get_all_tasks()

        if tasks:
            self._render_task_filters_and_list(tasks)
        else:
            st.info("📝 No tasks found. Create your first task using the button above!")

    def _render_new_task_form(self):
        """Render new task creation form"""
        with st.expander("Create New Task", expanded=True):
            with st.form("new_task_form", clear_on_submit=False):
                # Get projects for selection
                projects = self._get_projects_for_selection()

                col1, col2 = st.columns(2)

                with col1:
                    # Project selection
                    if projects:
                        project_options = {
                            f"{p['ProjectName']} (ID: {p['ProjectID']})": p["ProjectID"]
                            for p in projects
                        }
                        selected_project_name = st.selectbox(
                            "Project *", list(project_options.keys())
                        )
                        project_id = project_options[selected_project_name]
                    else:
                        st.error(
                            "No projects available. Please create a project first."
                        )
                        return

                    task_name = st.text_input(
                        "Task Name *", placeholder="Enter task name"
                    )
                    description = st.text_area(
                        "Description", placeholder="Task description"
                    )

                with col2:
                    # Get users for assignment
                    users = self._get_users_for_selection()
                    user_options = {
                        f"{u['FirstName']} {u['LastName']} ({u['Role']})": u["UserID"]
                        for u in users
                    }

                    assignee_name = st.selectbox(
                        "Assignee", ["Unassigned"] + list(user_options.keys())
                    )
                    status = st.selectbox(
                        "Status", ["To Do", "In Progress", "Review", "Testing", "Done"]
                    )
                    priority = st.selectbox(
                        "Priority", ["Low", "Medium", "High", "Critical"]
                    )

                col3, col4 = st.columns(2)
                with col3:
                    due_date = st.date_input(
                        "Due Date", value=datetime.now().date() + timedelta(days=7)
                    )
                    estimated_hours = st.number_input(
                        "Estimated Hours", min_value=0.0, step=0.5, value=8.0
                    )

                with col4:
                    start_date = st.date_input(
                        "Start Date", value=datetime.now().date()
                    )
                    end_date = st.date_input(
                        "End Date", value=datetime.now().date() + timedelta(days=5)
                    )

                col_submit, col_cancel = st.columns(2)

                with col_submit:
                    submitted = st.form_submit_button(
                        "🚀 Create Task", use_container_width=True
                    )

                with col_cancel:
                    cancel = st.form_submit_button(
                        "❌ Cancel", use_container_width=True
                    )

                if submitted:
                    if not task_name.strip():
                        st.error("❌ Task name is required!")
                    else:
                        # Get current user ID
                        user_id = st.session_state.user["UserID"]
                        assignee_id = (
                            user_options.get(assignee_name)
                            if assignee_name != "Unassigned"
                            else None
                        )

                        task_data = {
                            "project_id": project_id,
                            "task_name": task_name.strip(),
                            "description": description.strip(),
                            "assignee_id": assignee_id,
                            "status": status,
                            "priority": priority,
                            "due_date": due_date,
                            "start_date": start_date,
                            "end_date": end_date,
                            "estimated_hours": estimated_hours,
                            "created_by": user_id,
                        }

                        with st.spinner("🔄 Creating task..."):
                            success, message = self.create_task(task_data)

                            if success:
                                st.success(
                                    f"✅ Task '{task_name}' created successfully!"
                                )
                                st.session_state.show_new_task = False
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to create task: {message}")

                if cancel:
                    st.session_state.show_new_task = False
                    st.rerun()

    def _render_task_filters_and_list(self, tasks: List[Dict[str, Any]]):
        """Render task filters and task list"""
        st.info(f"📊 Found {len(tasks)} tasks in database")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + list(set([t["Status"] for t in tasks if t.get("Status")])),
            )

        with col2:
            priority_filter = st.selectbox(
                "Filter by Priority",
                ["All"]
                + list(set([t["Priority"] for t in tasks if t.get("Priority")])),
            )

        with col3:
            project_filter = st.selectbox(
                "Filter by Project",
                ["All"]
                + list(set([t["ProjectName"] for t in tasks if t.get("ProjectName")])),
            )

        # Apply filters
        filtered_tasks = self._apply_filters(
            tasks, status_filter, priority_filter, project_filter
        )

        # View options
        view_mode = st.radio("View Mode", ["List", "Kanban"], horizontal=True)

        if view_mode == "Kanban":
            self._render_kanban_view(filtered_tasks)
        else:
            self._render_task_list(filtered_tasks)

    def _apply_filters(
        self,
        tasks: List[Dict[str, Any]],
        status_filter: str,
        priority_filter: str,
        project_filter: str,
    ) -> List[Dict[str, Any]]:
        """Apply filters to task list"""
        filtered = tasks

        if status_filter != "All":
            filtered = [t for t in filtered if t.get("Status") == status_filter]

        if priority_filter != "All":
            filtered = [t for t in filtered if t.get("Priority") == priority_filter]

        if project_filter != "All":
            filtered = [t for t in filtered if t.get("ProjectName") == project_filter]

        return filtered

    def _render_task_list(self, tasks: List[Dict[str, Any]]):
        """Render tasks in list view"""
        for task in tasks:
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(
                        f"""
                    <div class="project-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <h4 style="margin: 0 0 10px 0; color: #2E3440;">{task.get('TaskName', 'Unnamed Task')}</h4>
                                <p style="color: #5E6C7E; margin-bottom: 10px;">{task.get('Description', 'No description')}</p>
                                
                                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                                    <div>
                                        <strong>📁 Project:</strong> {task.get('ProjectName', 'Unknown')}
                                    </div>
                                    <div>
                                        <strong>👤 Assignee:</strong> {task.get('AssigneeName', 'Unassigned')}
                                    </div>
                                    <div>
                                        <strong>📅 Due Date:</strong> {task.get('DueDate', 'Not set')}
                                    </div>
                                    <div>
                                        <strong>⏱️ Hours:</strong> {task.get('EstimatedHours', 0)} est / {task.get('ActualHours', 0)} actual
                                    </div>
                                </div>
                            </div>
                            
                            <div style="margin-left: 20px; text-align: right;">
                                <span class="status-badge status-{task.get('Status', 'unknown').lower().replace(' ', '-')}">{task.get('Status', 'Unknown')}</span><br><br>
                                <span class="priority-badge priority-{task.get('Priority', 'medium').lower()}">{task.get('Priority', 'Medium')}</span>
                            </div>
                        </div>
                        
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {task.get('Progress', 0)}%;"></div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                with col2:
                    # Action buttons
                    if st.button(
                        "📝 Update",
                        key=f"update_{task.get('TaskID', 0)}",
                        help="Update Task Status",
                    ):
                        self._show_task_update_form(task)

    def _render_kanban_view(self, tasks: List[Dict[str, Any]]):
        """Render tasks in Kanban board view"""
        st.subheader("📋 Kanban Board")

        # Group tasks by status
        task_groups = {
            "To Do": [],
            "In Progress": [],
            "Review": [],
            "Testing": [],
            "Done": [],
        }

        for task in tasks:
            status = task.get("Status", "To Do")
            if status in task_groups:
                task_groups[status].append(task)

        # Create columns for Kanban
        cols = st.columns(5)

        for i, (status, status_tasks) in enumerate(task_groups.items()):
            with cols[i]:
                st.markdown(f"### {status} ({len(status_tasks)})")

                for task in status_tasks:
                    # Calculate due date status
                    due_status = self._get_due_date_status(task.get("DueDate"))

                    st.markdown(
                        f"""
                    <div class="project-card" style="margin: 10px 0; padding: 15px;">
                        <h5 style="margin: 0 0 10px 0; color: #2E3440;">{task.get('TaskName', 'Unnamed')}</h5>
                        <p style="font-size: 0.9rem; color: #5E6C7E; margin: 5px 0;">
                            👤 {task.get('AssigneeName', 'Unassigned')}
                        </p>
                        <p style="font-size: 0.85rem; color: #5E6C7E; margin: 5px 0;">
                            {due_status}
                        </p>
                        <div style="margin-top: 10px;">
                            <span class="priority-badge priority-{task.get('Priority', 'medium').lower()}">{task.get('Priority', 'Medium')}</span>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

    def _show_task_update_form(self, task: Dict[str, Any]):
        """Show task update form"""
        with st.popover("Update Task Status"):
            new_status = st.selectbox(
                "Status",
                ["To Do", "In Progress", "Review", "Testing", "Done"],
                index=["To Do", "In Progress", "Review", "Testing", "Done"].index(
                    task.get("Status", "To Do")
                ),
            )

            progress = st.slider(
                "Progress (%)",
                min_value=0,
                max_value=100,
                value=task.get("Progress", 0),
            )

            if st.button("💾 Update"):
                success = self.update_task_status(
                    task.get("TaskID"), new_status, progress
                )
                if success:
                    st.success("✅ Task updated!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Failed to update task")

    def _get_due_date_status(self, due_date) -> str:
        """Get due date status text"""
        if not due_date:
            return "📅 No due date"

        try:
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            elif hasattr(due_date, "date"):
                due_date = due_date.date()

            days_diff = (due_date - datetime.now().date()).days

            if days_diff < 0:
                return f"🔴 {abs(days_diff)} days overdue"
            elif days_diff == 0:
                return "🟡 Due today"
            elif days_diff <= 3:
                return f"🟠 Due in {days_diff} days"
            else:
                return f"🟢 Due in {days_diff} days"
        except:
            return "📅 Invalid date"

    def _get_projects_for_selection(self) -> List[Dict[str, Any]]:
        """Get projects for task assignment"""
        try:
            query = "SELECT ProjectID, ProjectName FROM Projects WHERE Status != 'Completed' ORDER BY ProjectName"
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}")
            return []

    def _get_users_for_selection(self) -> List[Dict[str, Any]]:
        """Get users for task assignment"""
        try:
            query = """
            SELECT UserID, FirstName, LastName, Role 
            FROM Users 
            WHERE IsActive = 1 
            ORDER BY FirstName, LastName
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from database"""
        try:
            query = """
            SELECT 
                t.TaskID,
                t.ProjectID,
                t.TaskName,
                t.Description,
                t.Status,
                t.Priority,
                t.Progress,
                t.DueDate,
                t.StartDate,
                t.EndDate,
                t.EstimatedHours,
                t.ActualHours,
                t.CreatedDate,
                p.ProjectName,
                ISNULL(u.FirstName + ' ' + u.LastName, 'Unassigned') as AssigneeName
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            LEFT JOIN Users u ON t.AssigneeID = u.UserID
            ORDER BY t.CreatedDate DESC
            """

            results = self.db.execute_query(query)
            logger.info(f"✅ Loaded {len(results)} tasks")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to load tasks: {str(e)}")
            return []

    def create_task(self, task_data: Dict[str, Any]) -> tuple[bool, str]:
        """Create a new task"""
        try:
            query = """
            INSERT INTO Tasks (
                ProjectID, TaskName, Description, StartDate, EndDate, DueDate,
                AssigneeID, Status, Priority, EstimatedHours, CreatedBy,
                CreatedDate, LastModifiedDate, Progress
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE(), 0)
            """

            params = (
                task_data["project_id"],
                task_data["task_name"],
                task_data["description"],
                task_data["start_date"],
                task_data["end_date"],
                task_data["due_date"],
                task_data["assignee_id"],
                task_data["status"],
                task_data["priority"],
                task_data["estimated_hours"],
                task_data["created_by"],
            )

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                logger.info(f"✅ Created task: {task_data['task_name']}")
                return True, "Task created successfully"
            else:
                return False, "No rows affected"

        except Exception as e:
            logger.error(f"❌ Failed to create task: {str(e)}")
            return False, str(e)

    def update_task_status(
        self, task_id: int, status: str, progress: int = None
    ) -> bool:
        """Update task status and progress"""
        try:
            if progress is not None:
                query = """
                UPDATE Tasks 
                SET Status = ?, Progress = ?, LastModifiedDate = GETDATE()
                WHERE TaskID = ?
                """
                params = (status, progress, task_id)
            else:
                query = """
                UPDATE Tasks 
                SET Status = ?, LastModifiedDate = GETDATE()
                WHERE TaskID = ?
                """
                params = (status, task_id)

            rows_affected = self.db.execute_non_query(query, params)

            if rows_affected > 0:
                logger.info(f"✅ Updated task {task_id} status to {status}")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Failed to update task status: {str(e)}")
            return False

    def get_tasks_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tasks for specific project"""
        try:
            query = """
            SELECT 
                t.TaskID, t.TaskName, t.Description, t.Status, t.Priority,
                t.Progress, t.DueDate, t.EstimatedHours, t.ActualHours,
                ISNULL(u.FirstName + ' ' + u.LastName, 'Unassigned') as AssigneeName
            FROM Tasks t
            LEFT JOIN Users u ON t.AssigneeID = u.UserID
            WHERE t.ProjectID = ?
            ORDER BY t.CreatedDate DESC
            """

            return self.db.execute_query(query, (project_id,))

        except Exception as e:
            logger.error(f"Failed to get tasks by project: {str(e)}")
            return []

    def get_tasks_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get tasks assigned to user"""
        try:
            query = """
            SELECT 
                t.TaskID, t.TaskName, t.Description, t.Status, t.Priority,
                t.Progress, t.DueDate, t.EstimatedHours, t.ActualHours,
                p.ProjectName
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            WHERE t.AssigneeID = ?
            ORDER BY t.DueDate ASC, t.Priority DESC
            """

            return self.db.execute_query(query, (user_id,))

        except Exception as e:
            logger.error(f"Failed to get tasks by user: {str(e)}")
            return []
