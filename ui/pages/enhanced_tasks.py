# ui/pages/enhanced_tasks.py
"""
Enhanced Tasks Management Page for Project Manager Pro v3.0
Kanban board, drag & drop, progress tracking, and dependencies
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class EnhancedTasksPage:
    """Enhanced task management with Kanban board and advanced features"""

    def __init__(self, db_service, task_service, project_service):
        self.db_service = db_service
        self.task_service = task_service
        self.project_service = project_service
        self.status_colors = {
            "To Do": "#ff9f43",
            "In Progress": "#3742fa",
            "Review": "#f0932b",
            "Done": "#6c5ce7",
            "Blocked": "#ff3838",
        }
        self.priority_colors = {
            "Critical": "#ff3838",
            "High": "#ff6b6b",
            "Medium": "#ffa502",
            "Low": "#2ed573",
        }

    def render(self):
        """Render the enhanced tasks page"""
        # Initialize session state
        if "tasks_view" not in st.session_state:
            st.session_state.tasks_view = "kanban"
        if "selected_task" not in st.session_state:
            st.session_state.selected_task = None
        if "show_task_modal" not in st.session_state:
            st.session_state.show_task_modal = False
        if "kanban_columns" not in st.session_state:
            st.session_state.kanban_columns = ["To Do", "In Progress", "Review", "Done"]

        # Inject CSS for tasks page
        self._inject_tasks_css()

        # Page header
        self._render_page_header()

        # Tasks toolbar
        self._render_tasks_toolbar()

        # Tasks content based on view
        if st.session_state.tasks_view == "kanban":
            self._render_kanban_board()
        elif st.session_state.tasks_view == "list":
            self._render_tasks_list()
        elif st.session_state.tasks_view == "calendar":
            self._render_tasks_calendar()
        elif st.session_state.tasks_view == "dependencies":
            self._render_dependencies_view()

        # Task modal
        self._render_task_modal()

        # Task details sidebar
        self._render_task_details()

    def _inject_tasks_css(self):
        """Inject CSS for tasks page styling"""
        st.markdown(
            """
        <style>
        /* Tasks Page Styling */
        .tasks-header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            color: white;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .tasks-title {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        /* Kanban Board Styling */
        .kanban-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .kanban-board {
            display: flex;
            gap: 20px;
            overflow-x: auto;
            padding: 20px 0;
            min-height: 600px;
        }
        
        .kanban-column {
            min-width: 300px;
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        
        .kanban-column:hover {
            border-color: rgba(79, 172, 254, 0.3);
            transform: translateY(-2px);
        }
        
        .kanban-column.drag-over {
            border-color: #4facfe;
            background: rgba(79, 172, 254, 0.1);
        }
        
        .kanban-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
            color: #2c3e50;
        }
        
        .column-title {
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .task-count {
            background: linear-gradient(45deg, #4facfe, #00f2fe);
            color: white;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .add-task-btn {
            background: none;
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #6c757d;
            text-align: center;
            margin-bottom: 15px;
        }
        
        .add-task-btn:hover {
            border-color: #4facfe;
            color: #4facfe;
            background: rgba(79, 172, 254, 0.05);
        }
        
        /* Task Cards */
        .task-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            cursor: grab;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
            position: relative;
            overflow: hidden;
        }
        
        .task-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        
        .task-card:active {
            cursor: grabbing;
            transform: rotate(5deg);
        }
        
        .task-card.dragging {
            opacity: 0.8;
            transform: rotate(5deg) scale(1.05);
            z-index: 1000;
        }
        
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }
        
        .task-title {
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
            flex: 1;
            margin-right: 10px;
        }
        
        .task-priority {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: bold;
            color: white;
            text-transform: uppercase;
        }
        
        .task-description {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        
        .task-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-size: 0.8rem;
            color: #6c757d;
        }
        
        .task-assignee {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .assignee-avatar {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 10px;
            font-weight: bold;
        }
        
        .task-progress {
            margin-bottom: 10px;
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 6px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            transition: width 0.3s ease;
        }
        
        .task-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: #6c757d;
        }
        
        .task-labels {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }
        
        .task-label {
            background: rgba(79, 172, 254, 0.1);
            color: #4facfe;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 500;
        }
        
        .task-due-date {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .task-due-date.overdue {
            color: #ff3838;
            font-weight: bold;
        }
        
        .task-due-date.due-soon {
            color: #ffa502;
            font-weight: bold;
        }
        
        /* Task Actions */
        .task-actions {
            position: absolute;
            top: 10px;
            right: 10px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .task-card:hover .task-actions {
            opacity: 1;
        }
        
        .action-btn {
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            margin-left: 5px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .action-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        /* Dependencies View */
        .dependencies-container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .dependency-item {
            background: linear-gradient(145deg, #f8f9fa, #ffffff);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #4facfe;
            transition: all 0.3s ease;
        }
        
        .dependency-item:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        
        /* Calendar View */
        .calendar-container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .calendar-day {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 10px;
            min-height: 100px;
            transition: all 0.3s ease;
        }
        
        .calendar-day:hover {
            background: rgba(79, 172, 254, 0.05);
            border-color: #4facfe;
        }
        
        .calendar-task {
            background: linear-gradient(45deg, #4facfe, #00f2fe);
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            margin-bottom: 4px;
            cursor: pointer;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .kanban-board {
                flex-direction: column;
            }
            
            .kanban-column {
                min-width: 100%;
                margin-bottom: 20px;
            }
            
            .tasks-title {
                font-size: 2rem;
            }
        }
        
        /* Dark theme support */
        @media (prefers-color-scheme: dark) {
            .kanban-column {
                background: linear-gradient(145deg, #2c3e50, #34495e);
                color: white;
            }
            
            .task-card {
                background: #34495e;
                color: white;
            }
            
            .kanban-header {
                color: white;
                border-bottom-color: #485563;
            }
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_page_header(self):
        """Render page header with task statistics"""
        # Get task statistics
        tasks_data = self.task_service.get_all_tasks()
        total_tasks = len(tasks_data)
        completed_tasks = len([t for t in tasks_data if t.get("Status") == "Done"])
        in_progress_tasks = len(
            [t for t in tasks_data if t.get("Status") == "In Progress"]
        )
        overdue_tasks = len([t for t in tasks_data if self._is_overdue(t)])

        st.markdown(
            """
        <div class="tasks-header">
            <div class="tasks-title">✅ Task Management</div>
            <div class="tasks-subtitle">Organize and track your team's work efficiently</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Statistics cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Tasks", total_tasks, "📝")

        with col2:
            st.metric("In Progress", in_progress_tasks, "🚀")

        with col3:
            st.metric("Completed", completed_tasks, "✅")

        with col4:
            st.metric("Overdue", overdue_tasks, "⚠️" if overdue_tasks > 0 else "✅")

    def _render_tasks_toolbar(self):
        """Render tasks toolbar with actions and filters"""
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

        with col1:
            if st.button("➕ New Task", use_container_width=True, type="primary"):
                st.session_state.show_task_modal = True
                st.session_state.modal_mode = "create"
                st.session_state.selected_task = None

        with col2:
            view_options = ["kanban", "list", "calendar", "dependencies"]
            view_icons = {
                "kanban": "📌",
                "list": "📋",
                "calendar": "📅",
                "dependencies": "🔗",
            }
            current_view = st.session_state.tasks_view

            selected_view = st.selectbox(
                "View",
                view_options,
                index=view_options.index(current_view),
                format_func=lambda x: f"{view_icons[x]} {x.title()}",
            )

            if selected_view != current_view:
                st.session_state.tasks_view = selected_view
                st.rerun()

        with col3:
            # Project filter
            projects = self.project_service.get_all_projects()
            project_options = ["All Projects"] + [
                p.get("ProjectName", f"Project {p.get('ProjectID')}") for p in projects
            ]
            selected_project = st.selectbox("Project Filter", project_options)
            st.session_state.project_filter = selected_project

        with col4:
            # Assignee filter
            all_tasks = self.task_service.get_all_tasks()
            assignees = list(
                set([t.get("AssigneeName", "Unassigned") for t in all_tasks])
            )
            assignee_options = ["All Assignees"] + assignees
            selected_assignee = st.selectbox("Assignee Filter", assignee_options)
            st.session_state.assignee_filter = selected_assignee

        with col5:
            # Search
            search_term = st.text_input(
                "🔍 Search Tasks", placeholder="Search tasks..."
            )
            st.session_state.search_term = search_term

    def _render_kanban_board(self):
        """Render Kanban board with drag & drop functionality"""
        st.markdown('<div class="kanban-container">', unsafe_allow_html=True)

        # Get filtered tasks
        tasks = self._get_filtered_tasks()

        # Group tasks by status
        status_groups = {}
        for status in st.session_state.kanban_columns:
            status_groups[status] = [t for t in tasks if t.get("Status") == status]

        # Add 'Blocked' status if there are blocked tasks
        blocked_tasks = [t for t in tasks if t.get("Status") == "Blocked"]
        if blocked_tasks:
            status_groups["Blocked"] = blocked_tasks
            if "Blocked" not in st.session_state.kanban_columns:
                st.session_state.kanban_columns.append("Blocked")

        st.markdown('<div class="kanban-board">', unsafe_allow_html=True)

        # Render columns
        cols = st.columns(len(st.session_state.kanban_columns))
        for i, status in enumerate(st.session_state.kanban_columns):
            with cols[i]:
                self._render_kanban_column(status, status_groups.get(status, []))

        st.markdown("</div></div>", unsafe_allow_html=True)

        # Handle drag & drop (simulation with buttons)
        self._handle_task_status_updates()

    def _render_kanban_column(self, status: str, tasks: List[Dict]):
        """Render individual Kanban column"""
        status_icons = {
            "To Do": "📝",
            "In Progress": "🚀",
            "Review": "👀",
            "Done": "✅",
            "Blocked": "🚫",
        }

        icon = status_icons.get(status, "📋")
        task_count = len(tasks)

        st.markdown(
            f"""
        <div class="kanban-column">
            <div class="kanban-header">
                <div class="column-title">
                    {icon} {status}
                    <div class="task-count">{task_count}</div>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )

        # Add task button
        if st.button(
            f"➕ Add Task", key=f"add_task_{status}", use_container_width=True
        ):
            st.session_state.show_task_modal = True
            st.session_state.modal_mode = "create"
            st.session_state.default_status = status

        # Render tasks in this column
        for task in tasks:
            self._render_task_card(task, status)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_task_card(self, task: Dict, current_status: str):
        """Render individual task card"""
        task_id = task.get("TaskID")
        task_name = task.get("TaskName", "Untitled Task")
        description = task.get("Description", "")
        priority = task.get("Priority", "Medium")
        progress = task.get("Progress", 0)
        assignee = task.get("AssigneeName", "Unassigned")
        due_date = task.get("EndDate", "")
        labels = task.get("Labels", "").split(",") if task.get("Labels") else []

        # Priority color
        priority_color = self.priority_colors.get(priority, "#ffa502")

        # Due date status
        due_status = self._get_due_date_status(due_date)
        due_class = (
            "overdue"
            if due_status == "overdue"
            else "due-soon" if due_status == "due-soon" else ""
        )

        # Assignee initials
        assignee_initials = (
            "".join([name[0].upper() for name in assignee.split()[:2]])
            if assignee != "Unassigned"
            else "UN"
        )

        # Labels HTML
        labels_html = "".join(
            [
                f'<span class="task-label">{label.strip()}</span>'
                for label in labels
                if label.strip()
            ]
        )

        card_html = f"""
        <div class="task-card" data-task-id="{task_id}">
            <div class="task-header">
                <h4 class="task-title">{task_name}</h4>
                <span class="task-priority" style="background-color: {priority_color};">
                    {priority}
                </span>
            </div>
            
            {f'<div class="task-description">{description[:100]}{"..." if len(description) > 100 else ""}</div>' if description else ''}
            
            {f'<div class="task-labels">{labels_html}</div>' if labels_html else ''}
            
            <div class="task-meta">
                <div class="task-assignee">
                    <div class="assignee-avatar">{assignee_initials}</div>
                    <span>{assignee}</span>
                </div>
            </div>
            
            <div class="task-progress">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="font-size: 0.8rem;">Progress</span>
                    <span style="font-size: 0.8rem; font-weight: bold;">{progress}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress}%;"></div>
                </div>
            </div>
            
            <div class="task-footer">
                <div class="task-due-date {due_class}">
                    📅 {due_date if due_date else 'No due date'}
                </div>
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Task actions
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("👁️", key=f"view_{task_id}", help="View Details"):
                st.session_state.selected_task = task
                st.session_state.show_task_details = True

        with col2:
            if st.button("📝", key=f"edit_{task_id}", help="Edit Task"):
                st.session_state.selected_task = task
                st.session_state.show_task_modal = True
                st.session_state.modal_mode = "edit"

        with col3:
            # Move task to next status
            next_status = self._get_next_status(current_status)
            if next_status:
                if st.button("➡️", key=f"move_{task_id}", help=f"Move to {next_status}"):
                    self.task_service.update_task_status(task_id, next_status)
                    st.rerun()

        with col4:
            if st.button("🗑️", key=f"delete_{task_id}", help="Delete Task"):
                if st.session_state.get(f"confirm_delete_task_{task_id}", False):
                    self.task_service.delete_task(task_id)
                    st.success(f"Task '{task_name}' deleted!")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_task_{task_id}"] = True
                    st.warning("Click again to confirm")

    def _render_tasks_list(self):
        """Render tasks in list view"""
        tasks = self._get_filtered_tasks()

        if not tasks:
            st.info("📝 No tasks found.")
            return

        # Convert to DataFrame
        df = pd.DataFrame(tasks)

        # Select and configure columns
        display_columns = [
            "TaskName",
            "Status",
            "Priority",
            "Progress",
            "AssigneeName",
            "EndDate",
            "ProjectName",
        ]
        available_columns = [col for col in display_columns if col in df.columns]

        if available_columns:
            column_config = {
                "TaskName": st.column_config.TextColumn("Task Name", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Priority": st.column_config.TextColumn("Priority", width="small"),
                "Progress": st.column_config.ProgressColumn(
                    "Progress", min_value=0, max_value=100
                ),
                "AssigneeName": st.column_config.TextColumn("Assignee"),
                "EndDate": st.column_config.DateColumn("Due Date"),
                "ProjectName": st.column_config.TextColumn("Project"),
            }

            # Display dataframe with selection
            selected_rows = st.dataframe(
                df[available_columns],
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            # Handle row selection
            if selected_rows and selected_rows.selection.rows:
                selected_idx = selected_rows.selection.rows[0]
                selected_task = tasks[selected_idx]
                st.session_state.selected_task = selected_task
                st.session_state.show_task_details = True

    def _render_tasks_calendar(self):
        """Render tasks in calendar view"""
        st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
        st.markdown("### 📅 Tasks Calendar")

        tasks = self._get_filtered_tasks()

        # Create calendar data
        calendar_data = []
        for task in tasks:
            if task.get("EndDate"):
                calendar_data.append(
                    {
                        "Task": task.get("TaskName", "Untitled"),
                        "Date": task.get("EndDate"),
                        "Status": task.get("Status", "To Do"),
                        "Priority": task.get("Priority", "Medium"),
                        "Assignee": task.get("AssigneeName", "Unassigned"),
                    }
                )

        if calendar_data:
            df_calendar = pd.DataFrame(calendar_data)
            df_calendar["Date"] = pd.to_datetime(df_calendar["Date"])

            # Create timeline chart
            fig = px.timeline(
                df_calendar,
                x_start="Date",
                x_end="Date",
                y="Task",
                color="Status",
                title="Tasks Timeline",
                color_discrete_map=self.status_colors,
            )

            fig.update_layout(height=max(400, len(calendar_data) * 30), showlegend=True)

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📅 No tasks with due dates found.")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_dependencies_view(self):
        """Render task dependencies view"""
        st.markdown('<div class="dependencies-container">', unsafe_allow_html=True)
        st.markdown("### 🔗 Task Dependencies")

        tasks = self._get_filtered_tasks()

        # Find tasks with dependencies
        dependent_tasks = [t for t in tasks if t.get("Dependencies")]

        if dependent_tasks:
            for task in dependent_tasks:
                task_name = task.get("TaskName", "Untitled")
                dependencies = task.get("Dependencies", "").split(",")

                st.markdown(
                    f"""
                <div class="dependency-item">
                    <strong>{task_name}</strong>
                    <br>
                    <small>Depends on: {', '.join([dep.strip() for dep in dependencies if dep.strip()])}</small>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("🔗 No task dependencies found.")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_task_modal(self):
        """Render task creation/editing modal"""
        if not st.session_state.get("show_task_modal", False):
            return

        mode = st.session_state.get("modal_mode", "create")
        selected_task = st.session_state.get("selected_task")

        title = "📝 Create New Task" if mode == "create" else "✏️ Edit Task"

        with st.container():
            st.markdown(f"### {title}")

            # Task form
            with st.form("task_form"):
                col1, col2 = st.columns(2)

                with col1:
                    task_name = st.text_input(
                        "Task Name *",
                        value=(
                            selected_task.get("TaskName", "") if selected_task else ""
                        ),
                        placeholder="Enter task name",
                    )

                    # Project selection
                    projects = self.project_service.get_all_projects()
                    project_options = [
                        (
                            p.get("ProjectID"),
                            p.get("ProjectName", f"Project {p.get('ProjectID')}"),
                        )
                        for p in projects
                    ]
                    project_names = [name for _, name in project_options]
                    project_ids = [pid for pid, _ in project_options]

                    current_project_id = (
                        selected_task.get("ProjectID") if selected_task else None
                    )
                    default_project_index = 0
                    if current_project_id and current_project_id in project_ids:
                        default_project_index = project_ids.index(current_project_id)

                    selected_project_name = st.selectbox(
                        "Project *", project_names, index=default_project_index
                    )
                    selected_project_id = project_ids[
                        project_names.index(selected_project_name)
                    ]

                    start_date = st.date_input(
                        "Start Date",
                        value=(
                            pd.to_datetime(selected_task.get("StartDate")).date()
                            if selected_task and selected_task.get("StartDate")
                            else datetime.now().date()
                        ),
                    )

                    status = st.selectbox(
                        "Status",
                        options=["To Do", "In Progress", "Review", "Done", "Blocked"],
                        index=(
                            ["To Do", "In Progress", "Review", "Done", "Blocked"].index(
                                selected_task.get("Status", "To Do")
                            )
                            if selected_task
                            else 0
                        ),
                    )

                    estimated_hours = st.number_input(
                        "Estimated Hours",
                        min_value=0.0,
                        value=(
                            float(selected_task.get("EstimatedHours", 0))
                            if selected_task
                            else 0.0
                        ),
                        step=0.5,
                    )

                with col2:
                    # Assignee selection (mock data for now)
                    assignee_options = [
                        "Unassigned",
                        "John Doe",
                        "Jane Smith",
                        "Mike Johnson",
                        "Sarah Wilson",
                    ]
                    current_assignee = (
                        selected_task.get("AssigneeName", "Unassigned")
                        if selected_task
                        else "Unassigned"
                    )
                    if current_assignee not in assignee_options:
                        assignee_options.append(current_assignee)

                    assignee = st.selectbox(
                        "Assignee",
                        assignee_options,
                        index=assignee_options.index(current_assignee),
                    )

                    end_date = st.date_input(
                        "Due Date",
                        value=(
                            pd.to_datetime(selected_task.get("EndDate")).date()
                            if selected_task and selected_task.get("EndDate")
                            else datetime.now().date() + timedelta(days=7)
                        ),
                    )

                    priority = st.selectbox(
                        "Priority",
                        options=["Low", "Medium", "High", "Critical"],
                        index=(
                            ["Low", "Medium", "High", "Critical"].index(
                                selected_task.get("Priority", "Medium")
                            )
                            if selected_task
                            else 1
                        ),
                    )

                    progress = st.slider(
                        "Progress (%)",
                        min_value=0,
                        max_value=100,
                        value=(
                            int(selected_task.get("Progress", 0))
                            if selected_task
                            else 0
                        ),
                        step=5,
                    )

                    actual_hours = st.number_input(
                        "Actual Hours",
                        min_value=0.0,
                        value=(
                            float(selected_task.get("ActualHours", 0))
                            if selected_task
                            else 0.0
                        ),
                        step=0.5,
                    )

                # Description
                description = st.text_area(
                    "Description",
                    value=selected_task.get("Description", "") if selected_task else "",
                    placeholder="Enter task description...",
                    height=100,
                )

                # Labels and Dependencies
                col1, col2 = st.columns(2)
                with col1:
                    labels = st.text_input(
                        "Labels",
                        value=selected_task.get("Labels", "") if selected_task else "",
                        placeholder="frontend, api, testing (comma-separated)",
                    )

                with col2:
                    dependencies = st.text_input(
                        "Dependencies",
                        value=(
                            selected_task.get("Dependencies", "")
                            if selected_task
                            else ""
                        ),
                        placeholder="Task IDs this depends on (comma-separated)",
                    )

                # Form buttons
                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    if st.form_submit_button(
                        "💾 Save Task", use_container_width=True, type="primary"
                    ):
                        if task_name and selected_project_id:
                            task_data = {
                                "TaskName": task_name,
                                "ProjectID": selected_project_id,
                                "Description": description,
                                "StartDate": start_date.isoformat(),
                                "EndDate": end_date.isoformat(),
                                "Status": status,
                                "Priority": priority,
                                "Progress": progress,
                                "EstimatedHours": estimated_hours,
                                "ActualHours": actual_hours,
                                "Labels": labels,
                                "Dependencies": dependencies,
                                "AssigneeName": assignee,  # This would be AssigneeID in real implementation
                            }

                            try:
                                if mode == "create":
                                    self.task_service.create_task(task_data)
                                    st.success("✅ Task created successfully!")
                                else:
                                    task_id = selected_task.get("TaskID")
                                    self.task_service.update_task(task_id, task_data)
                                    st.success("✅ Task updated successfully!")

                                st.session_state.show_task_modal = False
                                st.rerun()

                            except Exception as e:
                                st.error(f"❌ Error saving task: {str(e)}")
                        else:
                            st.error("❌ Task name and project are required!")

                with col2:
                    if st.form_submit_button("🔄 Reset", use_container_width=True):
                        st.rerun()

                with col3:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.show_task_modal = False
                        st.rerun()

    def _render_task_details(self):
        """Render task details sidebar"""
        if not st.session_state.get("show_task_details", False):
            return

        selected_task = st.session_state.get("selected_task")
        if not selected_task:
            return

        with st.sidebar:
            st.markdown("### 📋 Task Details")

            # Task info
            st.markdown(f"**Name:** {selected_task.get('TaskName', 'N/A')}")
            st.markdown(f"**Status:** {selected_task.get('Status', 'N/A')}")
            st.markdown(f"**Priority:** {selected_task.get('Priority', 'N/A')}")
            st.markdown(
                f"**Assignee:** {selected_task.get('AssigneeName', 'Unassigned')}"
            )
            st.markdown(f"**Progress:** {selected_task.get('Progress', 0)}%")

            # Progress bar
            progress = selected_task.get("Progress", 0)
            st.progress(progress / 100)

            # Dates and time
            st.markdown("**Timeline:**")
            st.markdown(f"📅 Start: {selected_task.get('StartDate', 'N/A')}")
            st.markdown(f"🏁 Due: {selected_task.get('EndDate', 'N/A')}")

            # Time tracking
            estimated = selected_task.get("EstimatedHours", 0)
            actual = selected_task.get("ActualHours", 0)
            st.markdown(f"⏱️ Estimated: {estimated}h")
            st.markdown(f"⏰ Actual: {actual}h")

            # Description
            if selected_task.get("Description"):
                st.markdown("**Description:**")
                st.markdown(selected_task.get("Description"))

            # Labels
            if selected_task.get("Labels"):
                st.markdown("**Labels:**")
                labels = selected_task.get("Labels", "").split(",")
                for label in labels:
                    if label.strip():
                        st.markdown(f"• {label.strip()}")

            # Dependencies
            if selected_task.get("Dependencies"):
                st.markdown("**Dependencies:**")
                deps = selected_task.get("Dependencies", "").split(",")
                for dep in deps:
                    if dep.strip():
                        st.markdown(f"• Task {dep.strip()}")

            # Actions
            st.markdown("### ⚡ Quick Actions")

            if st.button("📝 Edit Task", use_container_width=True):
                st.session_state.show_task_modal = True
                st.session_state.modal_mode = "edit"

            if st.button("📈 Update Progress", use_container_width=True):
                new_progress = st.slider(
                    "Progress", 0, 100, progress, key="progress_update"
                )
                if st.button("Update", key="update_progress"):
                    self.task_service.update_task_progress(
                        selected_task.get("TaskID"), new_progress
                    )
                    st.success("Progress updated!")
                    st.rerun()

            if st.button("➡️ Change Status", use_container_width=True):
                current_status = selected_task.get("Status", "To Do")
                status_options = ["To Do", "In Progress", "Review", "Done", "Blocked"]
                new_status = st.selectbox(
                    "New Status",
                    status_options,
                    index=status_options.index(current_status),
                    key="status_update",
                )
                if st.button("Update Status", key="update_status"):
                    self.task_service.update_task_status(
                        selected_task.get("TaskID"), new_status
                    )
                    st.success(f"Status changed to {new_status}!")
                    st.rerun()

            if st.button("❌ Close Details", use_container_width=True):
                st.session_state.show_task_details = False
                st.rerun()

    def _get_filtered_tasks(self) -> List[Dict]:
        """Get filtered tasks based on current filters"""
        tasks = self.task_service.get_all_tasks()

        # Apply project filter
        project_filter = st.session_state.get("project_filter", "All Projects")
        if project_filter != "All Projects":
            # Get project ID by name
            projects = self.project_service.get_all_projects()
            project_id = None
            for project in projects:
                if project.get("ProjectName") == project_filter:
                    project_id = project.get("ProjectID")
                    break

            if project_id:
                tasks = [t for t in tasks if t.get("ProjectID") == project_id]

        # Apply assignee filter
        assignee_filter = st.session_state.get("assignee_filter", "All Assignees")
        if assignee_filter != "All Assignees":
            tasks = [t for t in tasks if t.get("AssigneeName") == assignee_filter]

        # Apply search filter
        search_term = st.session_state.get("search_term", "").lower()
        if search_term:
            tasks = [
                t
                for t in tasks
                if search_term in t.get("TaskName", "").lower()
                or search_term in t.get("Description", "").lower()
            ]

        return tasks

    def _handle_task_status_updates(self):
        """Handle task status updates from Kanban board"""
        # This is a simplified version - in a real app, you'd implement proper drag & drop
        pass

    def _get_next_status(self, current_status: str) -> Optional[str]:
        """Get the next status in the workflow"""
        status_flow = {
            "To Do": "In Progress",
            "In Progress": "Review",
            "Review": "Done",
            "Blocked": "To Do",
        }
        return status_flow.get(current_status)

    def _is_overdue(self, task: Dict) -> bool:
        """Check if a task is overdue"""
        end_date = task.get("EndDate")
        if not end_date:
            return False

        try:
            due_date = pd.to_datetime(end_date).date()
            today = datetime.now().date()
            return due_date < today and task.get("Status") != "Done"
        except:
            return False

    def _get_due_date_status(self, due_date: str) -> str:
        """Get due date status (overdue, due-soon, normal)"""
        if not due_date:
            return "normal"

        try:
            due = pd.to_datetime(due_date).date()
            today = datetime.now().date()
            days_until_due = (due - today).days

            if days_until_due < 0:
                return "overdue"
            elif days_until_due <= 2:
                return "due-soon"
            else:
                return "normal"
        except:
            return "normal"
