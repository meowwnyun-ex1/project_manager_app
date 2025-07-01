# ui/pages/enhanced_projects.py
"""
Enhanced Projects Management Page for Project Manager Pro v3.0
Complete CRUD operations with modern UI and advanced features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class EnhancedProjectsPage:
    """Enhanced projects management with modern UI/UX"""

    def __init__(self, db_service, project_service):
        self.db_service = db_service
        self.project_service = project_service
        self.status_colors = {
            "Planning": "#ff9f43",
            "In Progress": "#3742fa",
            "On Hold": "#f0932b",
            "Completed": "#6c5ce7",
            "Cancelled": "#a4b0be",
        }
        self.priority_colors = {
            "Critical": "#ff3838",
            "High": "#ff6b6b",
            "Medium": "#ffa502",
            "Low": "#2ed573",
        }

    def render(self):
        """Render the enhanced projects page"""
        # Initialize session state
        if "projects_view" not in st.session_state:
            st.session_state.projects_view = "grid"
        if "selected_project" not in st.session_state:
            st.session_state.selected_project = None
        if "show_project_modal" not in st.session_state:
            st.session_state.show_project_modal = False

        # Inject CSS for projects page
        self._inject_projects_css()

        # Page header
        self._render_page_header()

        # Projects toolbar
        self._render_projects_toolbar()

        # Projects content based on view
        if st.session_state.projects_view == "grid":
            self._render_projects_grid()
        elif st.session_state.projects_view == "list":
            self._render_projects_list()
        elif st.session_state.projects_view == "kanban":
            self._render_projects_kanban()
        elif st.session_state.projects_view == "timeline":
            self._render_projects_timeline()

        # Project modal
        self._render_project_modal()

        # Project details sidebar
        self._render_project_details()

    def _inject_projects_css(self):
        """Inject CSS for projects page styling"""
        st.markdown(
            """
        <style>
        /* Projects Page Styling */
        .projects-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            color: white;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .projects-title {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .projects-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        /* Toolbar Styling */
        .projects-toolbar {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Project Cards */
        .project-card {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        }
        
        .project-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .project-title {
            font-size: 1.3rem;
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
        }
        
        .project-status {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
            text-transform: uppercase;
        }
        
        .project-description {
            color: #7f8c8d;
            margin-bottom: 15px;
            line-height: 1.6;
        }
        
        .project-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .project-dates {
            font-size: 0.9rem;
            color: #7f8c8d;
        }
        
        .project-priority {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
        }
        
        .project-progress {
            margin-bottom: 15px;
        }
        
        .progress-bar {
            background: #ecf0f1;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        
        .project-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .project-team {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .team-avatar {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        
        .project-actions {
            display: flex;
            gap: 10px;
        }
        
        .action-btn {
            padding: 8px 12px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }
        
        .btn-secondary {
            background: #f8f9fa;
            color: #495057;
            border: 1px solid #dee2e6;
        }
        
        .btn-danger {
            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
            color: white;
        }
        
        /* Kanban Board */
        .kanban-board {
            display: flex;
            gap: 20px;
            overflow-x: auto;
            padding: 20px 0;
        }
        
        .kanban-column {
            min-width: 300px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .kanban-header {
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        .kanban-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            cursor: grab;
            transition: all 0.3s ease;
        }
        
        .kanban-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        }
        
        /* Timeline View */
        .timeline-container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .projects-title {
                font-size: 2rem;
            }
            
            .project-card {
                padding: 20px;
            }
            
            .kanban-board {
                flex-direction: column;
            }
            
            .kanban-column {
                min-width: 100%;
            }
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_page_header(self):
        """Render page header with stats"""
        # Get project statistics
        projects_data = self.project_service.get_all_projects()
        total_projects = len(projects_data)
        active_projects = len(
            [p for p in projects_data if p.get("Status") == "In Progress"]
        )
        completed_projects = len(
            [p for p in projects_data if p.get("Status") == "Completed"]
        )

        st.markdown(
            """
        <div class="projects-header">
            <div class="projects-title">📚 Projects Management</div>
            <div class="projects-subtitle">Manage and track all your projects in one place</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Statistics cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Projects", total_projects, "📊")

        with col2:
            st.metric("Active Projects", active_projects, "🚀")

        with col3:
            st.metric("Completed", completed_projects, "✅")

        with col4:
            completion_rate = (
                (completed_projects / total_projects * 100) if total_projects > 0 else 0
            )
            st.metric("Completion Rate", f"{completion_rate:.1f}%", "📈")

    def _render_projects_toolbar(self):
        """Render projects toolbar with actions and filters"""
        st.markdown('<div class="projects-toolbar">', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

        with col1:
            if st.button("➕ New Project", use_container_width=True, type="primary"):
                st.session_state.show_project_modal = True
                st.session_state.modal_mode = "create"
                st.session_state.selected_project = None

        with col2:
            view_options = ["grid", "list", "kanban", "timeline"]
            view_icons = {"grid": "⚏", "list": "📋", "kanban": "📌", "timeline": "📅"}
            current_view = st.session_state.projects_view

            selected_view = st.selectbox(
                "View",
                view_options,
                index=view_options.index(current_view),
                format_func=lambda x: f"{view_icons[x]} {x.title()}",
            )

            if selected_view != current_view:
                st.session_state.projects_view = selected_view
                st.rerun()

        with col3:
            # Status filter
            all_projects = self.project_service.get_all_projects()
            status_options = ["All"] + list(
                set([p.get("Status", "Planning") for p in all_projects])
            )
            selected_status = st.selectbox("Status Filter", status_options)
            st.session_state.status_filter = selected_status

        with col4:
            # Priority filter
            priority_options = ["All", "Critical", "High", "Medium", "Low"]
            selected_priority = st.selectbox("Priority Filter", priority_options)
            st.session_state.priority_filter = selected_priority

        with col5:
            # Search
            search_term = st.text_input(
                "🔍 Search Projects", placeholder="Search by name..."
            )
            st.session_state.search_term = search_term

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_projects_grid(self):
        """Render projects in grid view"""
        projects = self._get_filtered_projects()

        if not projects:
            st.info("📝 No projects found. Create your first project to get started!")
            return

        # Grid layout
        cols_per_row = 2
        for i in range(0, len(projects), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(projects):
                    with col:
                        self._render_project_card(projects[i + j])

    def _render_project_card(self, project):
        """Render individual project card"""
        project_id = project.get("ProjectID")
        project_name = project.get("ProjectName", "Untitled Project")
        description = project.get("Description", "No description available")
        status = project.get("Status", "Planning")
        priority = project.get("Priority", "Medium")
        start_date = project.get("StartDate", "")
        end_date = project.get("EndDate", "")

        # Calculate progress (mock calculation - should be based on tasks)
        progress = min(100, max(0, hash(str(project_id)) % 101))

        # Status color
        status_color = self.status_colors.get(status, "#6c5ce7")
        priority_color = self.priority_colors.get(priority, "#ffa502")

        card_html = f"""
        <div class="project-card" onclick="selectProject({project_id})">
            <div class="project-header">
                <h3 class="project-title">{project_name}</h3>
                <span class="project-status" style="background-color: {status_color};">{status}</span>
            </div>
            
            <div class="project-description">
                {description[:150]}{'...' if len(description) > 150 else ''}
            </div>
            
            <div class="project-meta">
                <div class="project-dates">
                    📅 {start_date} → {end_date}
                </div>
                <span class="project-priority" style="background-color: {priority_color};">
                    {priority}
                </span>
            </div>
            
            <div class="project-progress">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>Progress</span>
                    <span>{progress}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress}%;"></div>
                </div>
            </div>
            
            <div class="project-footer">
                <div class="project-team">
                    <div class="team-avatar">JD</div>
                    <div class="team-avatar">AB</div>
                    <span>+2</span>
                </div>
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📝 Edit", key=f"edit_{project_id}", use_container_width=True):
                st.session_state.selected_project = project
                st.session_state.show_project_modal = True
                st.session_state.modal_mode = "edit"

        with col2:
            if st.button("👁️ View", key=f"view_{project_id}", use_container_width=True):
                st.session_state.selected_project = project
                st.session_state.show_project_details = True

        with col3:
            if st.button(
                "🗑️ Delete", key=f"delete_{project_id}", use_container_width=True
            ):
                if st.session_state.get(f"confirm_delete_{project_id}", False):
                    self.project_service.delete_project(project_id)
                    st.success(f"Project '{project_name}' deleted successfully!")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{project_id}"] = True
                    st.warning("Click again to confirm deletion")

    def _render_projects_list(self):
        """Render projects in list view"""
        projects = self._get_filtered_projects()

        if not projects:
            st.info("📝 No projects found.")
            return

        # Convert to DataFrame for better display
        df = pd.DataFrame(projects)

        # Select columns to display
        display_columns = [
            "ProjectName",
            "Status",
            "Priority",
            "StartDate",
            "EndDate",
            "ClientName",
        ]
        available_columns = [col for col in display_columns if col in df.columns]

        if available_columns:
            # Configure column settings
            column_config = {
                "ProjectName": st.column_config.TextColumn(
                    "Project Name", width="large"
                ),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Priority": st.column_config.TextColumn("Priority", width="small"),
                "StartDate": st.column_config.DateColumn("Start Date"),
                "EndDate": st.column_config.DateColumn("End Date"),
                "ClientName": st.column_config.TextColumn("Client"),
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
                selected_project = projects[selected_idx]
                st.session_state.selected_project = selected_project
                st.session_state.show_project_details = True

    def _render_projects_kanban(self):
        """Render projects in Kanban board view"""
        projects = self._get_filtered_projects()

        # Group projects by status
        status_groups = {}
        for project in projects:
            status = project.get("Status", "Planning")
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(project)

        # Render Kanban columns
        statuses = ["Planning", "In Progress", "On Hold", "Completed", "Cancelled"]

        st.markdown('<div class="kanban-board">', unsafe_allow_html=True)

        cols = st.columns(len(statuses))
        for i, status in enumerate(statuses):
            with cols[i]:
                st.markdown(
                    f"""
                <div class="kanban-column">
                    <div class="kanban-header">
                        {status} ({len(status_groups.get(status, []))})
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                # Render projects in this status
                for project in status_groups.get(status, []):
                    self._render_kanban_card(project)

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_kanban_card(self, project):
        """Render project card for Kanban view"""
        project_name = project.get("ProjectName", "Untitled")
        priority = project.get("Priority", "Medium")
        priority_color = self.priority_colors.get(priority, "#ffa502")

        card_html = f"""
        <div class="kanban-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>{project_name}</strong>
                <span style="background: {priority_color}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.8rem;">
                    {priority}
                </span>
            </div>
            <div style="color: #666; font-size: 0.9rem;">
                📅 {project.get('StartDate', 'No date')}
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

    def _render_projects_timeline(self):
        """Render projects timeline view"""
        projects = self._get_filtered_projects()

        if not projects:
            st.info("📝 No projects to display in timeline.")
            return

        # Prepare data for timeline chart
        timeline_data = []
        for project in projects:
            if project.get("StartDate") and project.get("EndDate"):
                timeline_data.append(
                    {
                        "Project": project.get("ProjectName", "Untitled"),
                        "Start": project.get("StartDate"),
                        "End": project.get("EndDate"),
                        "Status": project.get("Status", "Planning"),
                        "Priority": project.get("Priority", "Medium"),
                    }
                )

        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)

            # Create Gantt chart
            fig = px.timeline(
                df_timeline,
                x_start="Start",
                x_end="End",
                y="Project",
                color="Status",
                title="Projects Timeline",
                color_discrete_map=self.status_colors,
            )

            fig.update_layout(
                height=max(400, len(timeline_data) * 40),
                showlegend=True,
                xaxis_title="Timeline",
                yaxis_title="Projects",
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No projects with valid date ranges found.")

    def _render_project_modal(self):
        """Render project creation/editing modal"""
        if not st.session_state.get("show_project_modal", False):
            return

        mode = st.session_state.get("modal_mode", "create")
        selected_project = st.session_state.get("selected_project")

        title = "📝 Create New Project" if mode == "create" else "✏️ Edit Project"

        with st.container():
            st.markdown(f"### {title}")

            # Project form
            with st.form("project_form"):
                col1, col2 = st.columns(2)

                with col1:
                    project_name = st.text_input(
                        "Project Name *",
                        value=(
                            selected_project.get("ProjectName", "")
                            if selected_project
                            else ""
                        ),
                        placeholder="Enter project name",
                    )

                    start_date = st.date_input(
                        "Start Date",
                        value=(
                            pd.to_datetime(selected_project.get("StartDate")).date()
                            if selected_project and selected_project.get("StartDate")
                            else datetime.now().date()
                        ),
                    )

                    status = st.selectbox(
                        "Status",
                        options=[
                            "Planning",
                            "In Progress",
                            "On Hold",
                            "Completed",
                            "Cancelled",
                        ],
                        index=(
                            [
                                "Planning",
                                "In Progress",
                                "On Hold",
                                "Completed",
                                "Cancelled",
                            ].index(selected_project.get("Status", "Planning"))
                            if selected_project
                            else 0
                        ),
                    )

                    budget = st.number_input(
                        "Budget ($)",
                        min_value=0.0,
                        value=(
                            float(selected_project.get("Budget", 0))
                            if selected_project
                            else 0.0
                        ),
                        step=1000.0,
                    )

                with col2:
                    client_name = st.text_input(
                        "Client Name",
                        value=(
                            selected_project.get("ClientName", "")
                            if selected_project
                            else ""
                        ),
                        placeholder="Enter client name",
                    )

                    end_date = st.date_input(
                        "End Date",
                        value=(
                            pd.to_datetime(selected_project.get("EndDate")).date()
                            if selected_project and selected_project.get("EndDate")
                            else datetime.now().date() + timedelta(days=30)
                        ),
                    )

                    priority = st.selectbox(
                        "Priority",
                        options=["Low", "Medium", "High", "Critical"],
                        index=(
                            ["Low", "Medium", "High", "Critical"].index(
                                selected_project.get("Priority", "Medium")
                            )
                            if selected_project
                            else 1
                        ),
                    )

                    tags = st.text_input(
                        "Tags",
                        value=(
                            selected_project.get("Tags", "") if selected_project else ""
                        ),
                        placeholder="web, mobile, api (comma-separated)",
                    )

                # Description
                description = st.text_area(
                    "Description",
                    value=(
                        selected_project.get("Description", "")
                        if selected_project
                        else ""
                    ),
                    placeholder="Enter project description...",
                    height=100,
                )

                # Form buttons
                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    if st.form_submit_button(
                        "💾 Save Project", use_container_width=True, type="primary"
                    ):
                        if project_name:
                            project_data = {
                                "ProjectName": project_name,
                                "Description": description,
                                "StartDate": start_date.isoformat(),
                                "EndDate": end_date.isoformat(),
                                "Status": status,
                                "Priority": priority,
                                "Budget": budget,
                                "ClientName": client_name,
                                "Tags": tags,
                            }

                            try:
                                if mode == "create":
                                    self.project_service.create_project(project_data)
                                    st.success("✅ Project created successfully!")
                                else:
                                    project_id = selected_project.get("ProjectID")
                                    self.project_service.update_project(
                                        project_id, project_data
                                    )
                                    st.success("✅ Project updated successfully!")

                                st.session_state.show_project_modal = False
                                st.rerun()

                            except Exception as e:
                                st.error(f"❌ Error saving project: {str(e)}")
                        else:
                            st.error("❌ Project name is required!")

                with col2:
                    if st.form_submit_button("🔄 Reset", use_container_width=True):
                        st.rerun()

                with col3:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.show_project_modal = False
                        st.rerun()

    def _render_project_details(self):
        """Render project details sidebar"""
        if not st.session_state.get("show_project_details", False):
            return

        selected_project = st.session_state.get("selected_project")
        if not selected_project:
            return

        with st.sidebar:
            st.markdown("### 📋 Project Details")

            # Project info
            st.markdown(f"**Name:** {selected_project.get('ProjectName', 'N/A')}")
            st.markdown(f"**Status:** {selected_project.get('Status', 'N/A')}")
            st.markdown(f"**Priority:** {selected_project.get('Priority', 'N/A')}")
            st.markdown(f"**Client:** {selected_project.get('ClientName', 'N/A')}")
            st.markdown(f"**Budget:** ${selected_project.get('Budget', 0):,.2f}")

            # Dates
            st.markdown("**Timeline:**")
            st.markdown(f"📅 Start: {selected_project.get('StartDate', 'N/A')}")
            st.markdown(f"🏁 End: {selected_project.get('EndDate', 'N/A')}")

            # Description
            if selected_project.get("Description"):
                st.markdown("**Description:**")
                st.markdown(selected_project.get("Description"))

            # Actions
            st.markdown("### ⚡ Quick Actions")

            if st.button("📝 Edit Project", use_container_width=True):
                st.session_state.show_project_modal = True
                st.session_state.modal_mode = "edit"

            if st.button("✅ View Tasks", use_container_width=True):
                st.session_state.current_page = "tasks"
                st.session_state.filter_project_id = selected_project.get("ProjectID")
                st.rerun()

            if st.button("📊 View Reports", use_container_width=True):
                st.session_state.current_page = "reports"
                st.session_state.report_project_id = selected_project.get("ProjectID")
                st.rerun()

            if st.button("❌ Close Details", use_container_width=True):
                st.session_state.show_project_details = False
                st.rerun()

    def _get_filtered_projects(self) -> List[Dict]:
        """Get filtered projects based on current filters"""
        projects = self.project_service.get_all_projects()

        # Apply status filter
        status_filter = st.session_state.get("status_filter", "All")
        if status_filter != "All":
            projects = [p for p in projects if p.get("Status") == status_filter]

        # Apply priority filter
        priority_filter = st.session_state.get("priority_filter", "All")
        if priority_filter != "All":
            projects = [p for p in projects if p.get("Priority") == priority_filter]

        # Apply search filter
        search_term = st.session_state.get("search_term", "").lower()
        if search_term:
            projects = [
                p
                for p in projects
                if search_term in p.get("ProjectName", "").lower()
                or search_term in p.get("Description", "").lower()
            ]

        return projects
