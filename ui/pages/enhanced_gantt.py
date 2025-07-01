# ui/pages/enhanced_gantt.py
"""
Enhanced Gantt Chart Page for Project Manager Pro v3.0
Interactive timeline, milestones, dependencies, and resource allocation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class EnhancedGanttPage:
    """Enhanced Gantt chart with interactive timeline and advanced features"""

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
        """Render the enhanced Gantt chart page"""
        # Initialize session state
        if "gantt_view" not in st.session_state:
            st.session_state.gantt_view = "timeline"
        if "selected_gantt_project" not in st.session_state:
            st.session_state.selected_gantt_project = "All Projects"
        if "show_milestones" not in st.session_state:
            st.session_state.show_milestones = True
        if "show_dependencies" not in st.session_state:
            st.session_state.show_dependencies = True

        # Inject CSS for Gantt page
        self._inject_gantt_css()

        # Page header
        self._render_page_header()

        # Gantt toolbar
        self._render_gantt_toolbar()

        # Gantt content based on view
        if st.session_state.gantt_view == "timeline":
            self._render_timeline_view()
        elif st.session_state.gantt_view == "resources":
            self._render_resource_view()
        elif st.session_state.gantt_view == "critical_path":
            self._render_critical_path()
        elif st.session_state.gantt_view == "workload":
            self._render_workload_analysis()

        # Project statistics
        self._render_project_stats()

    def _inject_gantt_css(self):
        """Inject CSS for Gantt page styling"""
        st.markdown(
            """
        <style>
        /* Gantt Page Styling */
        .gantt-header {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            color: #2c3e50;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .gantt-title {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .gantt-subtitle {
            font-size: 1.1rem;
            opacity: 0.8;
        }
        
        /* Toolbar Styling */
        .gantt-toolbar {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Chart Container */
        .chart-container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .chart-title {
            font-size: 1.3rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .chart-controls {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        /* Timeline Legend */
        .timeline-legend {
            background: linear-gradient(145deg, #f8f9fa, #ffffff);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        .legend-item {
            display: inline-flex;
            align-items: center;
            margin-right: 20px;
            margin-bottom: 5px;
        }
        
        .legend-color {
            width: 20px;
            height: 12px;
            border-radius: 4px;
            margin-right: 8px;
        }
        
        .legend-text {
            font-size: 0.9rem;
            color: #495057;
        }
        
        /* Milestone Markers */
        .milestone-marker {
            background: #ffa502;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
            display: inline-block;
            margin: 2px;
        }
        
        /* Resource Cards */
        .resource-card {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #a8edea;
            transition: all 0.3s ease;
        }
        
        .resource-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        
        .resource-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .resource-name {
            font-weight: bold;
            font-size: 1.1rem;
            color: #2c3e50;
        }
        
        .resource-utilization {
            font-size: 0.9rem;
            color: #7f8c8d;
        }
        
        .resource-tasks {
            margin-top: 15px;
        }
        
        .resource-task {
            background: rgba(168, 237, 234, 0.2);
            border-radius: 6px;
            padding: 8px 12px;
            margin-bottom: 8px;
            font-size: 0.9rem;
            border-left: 3px solid #a8edea;
        }
        
        /* Critical Path Styling */
        .critical-path-item {
            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
            color: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
        }
        
        .critical-task {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .critical-duration {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        /* Statistics Cards */
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .stat-card {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 1rem;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        /* Workload Analysis */
        .workload-member {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .member-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .member-name {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .workload-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            position: relative;
            overflow: hidden;
        }
        
        .workload-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .workload-overloaded {
            background: linear-gradient(90deg, #ff6b6b, #ee5a52);
        }
        
        .workload-normal {
            background: linear-gradient(90deg, #4facfe, #00f2fe);
        }
        
        .workload-underutilized {
            background: linear-gradient(90deg, #2ed573, #7bed9f);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .gantt-title {
                font-size: 2rem;
            }
            
            .chart-container {
                padding: 20px;
            }
            
            .stats-container {
                grid-template-columns: 1fr;
            }
            
            .legend-item {
                margin-right: 10px;
                margin-bottom: 10px;
            }
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_page_header(self):
        """Render page header"""
        st.markdown(
            """
        <div class="gantt-header">
            <div class="gantt-title">📅 Gantt Chart & Timeline</div>
            <div class="gantt-subtitle">Visualize project timelines, dependencies, and resource allocation</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_gantt_toolbar(self):
        """Render Gantt toolbar with filters and controls"""
        st.markdown('<div class="gantt-toolbar">', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

        with col1:
            # View selector
            view_options = ["timeline", "resources", "critical_path", "workload"]
            view_icons = {
                "timeline": "📊",
                "resources": "👥",
                "critical_path": "🚨",
                "workload": "⚖️",
            }
            current_view = st.session_state.gantt_view

            selected_view = st.selectbox(
                "View Type",
                view_options,
                index=view_options.index(current_view),
                format_func=lambda x: f"{view_icons[x]} {x.replace('_', ' ').title()}",
            )

            if selected_view != current_view:
                st.session_state.gantt_view = selected_view
                st.rerun()

        with col2:
            # Project filter
            projects = self.project_service.get_all_projects()
            project_options = ["All Projects"] + [
                p.get("ProjectName", f"Project {p.get('ProjectID')}") for p in projects
            ]
            selected_project = st.selectbox("Project", project_options)
            st.session_state.selected_gantt_project = selected_project

        with col3:
            # Time range
            time_ranges = [
                "Last 30 Days",
                "Next 30 Days",
                "Current Quarter",
                "All Time",
            ]
            selected_range = st.selectbox("Time Range", time_ranges, index=1)
            st.session_state.time_range = selected_range

        with col4:
            # Show milestones toggle
            show_milestones = st.checkbox(
                "Show Milestones", value=st.session_state.show_milestones
            )
            st.session_state.show_milestones = show_milestones

        with col5:
            # Show dependencies toggle
            show_dependencies = st.checkbox(
                "Show Dependencies", value=st.session_state.show_dependencies
            )
            st.session_state.show_dependencies = show_dependencies

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_timeline_view(self):
        """Render main timeline Gantt chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        # Chart header
        st.markdown(
            """
        <div class="chart-header">
            <div class="chart-title">📊 Project Timeline</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Legend
        self._render_timeline_legend()

        # Get timeline data
        timeline_data = self._get_timeline_data()

        if timeline_data:
            # Create Gantt chart
            fig = self._create_gantt_chart(timeline_data)
            st.plotly_chart(fig, use_container_width=True)

            # Add milestones if enabled
            if st.session_state.show_milestones:
                self._render_milestones()
        else:
            st.info(
                "📊 No timeline data available. Create projects and tasks to see the Gantt chart."
            )

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_timeline_legend(self):
        """Render timeline legend"""
        legend_html = """
        <div class="timeline-legend">
            <div style="font-weight: bold; margin-bottom: 10px;">Legend:</div>
        """

        # Status legend
        for status, color in self.status_colors.items():
            legend_html += f"""
            <div class="legend-item">
                <div class="legend-color" style="background-color: {color};"></div>
                <span class="legend-text">{status}</span>
            </div>
            """

        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

    def _create_gantt_chart(self, timeline_data):
        """Create interactive Gantt chart"""
        df = pd.DataFrame(timeline_data)

        # Convert dates
        df["Start"] = pd.to_datetime(df["Start"])
        df["End"] = pd.to_datetime(df["End"])

        # Create main timeline chart
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="End",
            y="Resource",
            color="Status",
            title="",
            color_discrete_map=self.status_colors,
            hover_data=["Task", "Progress", "Priority"],
        )

        # Customize layout
        fig.update_layout(
            height=max(400, len(df) * 40),
            showlegend=True,
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            font=dict(size=12),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
        )

        # Add progress overlay
        for i, row in df.iterrows():
            progress = row["Progress"] / 100
            duration = (row["End"] - row["Start"]).total_seconds()
            progress_end = row["Start"] + pd.Timedelta(seconds=duration * progress)

            fig.add_shape(
                type="rect",
                x0=row["Start"],
                x1=progress_end,
                y0=i - 0.4,
                y1=i + 0.4,
                fillcolor="rgba(46, 213, 115, 0.7)",
                line=dict(width=0),
                layer="above",
            )

        # Add today line
        today = datetime.now()
        fig.add_vline(
            x=today,
            line_dash="dash",
            line_color="red",
            annotation_text="Today",
            annotation_position="top",
        )

        return fig

    def _render_milestones(self):
        """Render project milestones"""
        st.markdown("### 🎯 Project Milestones")

        milestones = self._get_milestones()

        if milestones:
            for milestone in milestones:
                status_class = "completed" if milestone["completed"] else "upcoming"
                icon = "✅" if milestone["completed"] else "🎯"

                st.markdown(
                    f"""
                <div class="milestone-marker">
                    {icon} {milestone['name']} - {milestone['date']}
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("🎯 No milestones defined for selected projects.")

    def _render_resource_view(self):
        """Render resource allocation view"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        st.markdown(
            """
        <div class="chart-header">
            <div class="chart-title">👥 Resource Allocation</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        resources = self._get_resource_allocation()

        if resources:
            for resource in resources:
                self._render_resource_card(resource)
        else:
            st.info("👥 No resource allocation data available.")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_resource_card(self, resource):
        """Render individual resource card"""
        name = resource["name"]
        utilization = resource["utilization"]
        tasks = resource["tasks"]

        utilization_color = (
            "#ff6b6b"
            if utilization > 100
            else "#4facfe" if utilization > 80 else "#2ed573"
        )

        card_html = f"""
        <div class="resource-card">
            <div class="resource-header">
                <div class="resource-name">👤 {name}</div>
                <div class="resource-utilization" style="color: {utilization_color};">
                    {utilization}% Utilized
                </div>
            </div>
            
            <div style="background: #e9ecef; border-radius: 10px; height: 10px; margin-bottom: 15px;">
                <div style="background: {utilization_color}; height: 100%; width: {min(utilization, 100)}%; border-radius: 10px;"></div>
            </div>
            
            <div class="resource-tasks">
                <strong>Current Tasks:</strong>
        """

        for task in tasks:
            card_html += f'<div class="resource-task">• {task}</div>'

        card_html += "</div></div>"

        st.markdown(card_html, unsafe_allow_html=True)

    def _render_critical_path(self):
        """Render critical path analysis"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        st.markdown(
            """
        <div class="chart-header">
            <div class="chart-title">🚨 Critical Path Analysis</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        critical_tasks = self._get_critical_path()

        if critical_tasks:
            st.markdown(
                "### Critical Path Tasks (tasks that affect project completion date):"
            )

            for i, task in enumerate(critical_tasks):
                st.markdown(
                    f"""
                <div class="critical-path-item">
                    <div class="critical-task">{i+1}. {task['name']}</div>
                    <div class="critical-duration">Duration: {task['duration']} days | Slack: {task['slack']} days</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Critical path chart
            self._render_critical_path_chart(critical_tasks)
        else:
            st.info("🚨 No critical path data available.")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_critical_path_chart(self, critical_tasks):
        """Render critical path visualization"""
        if not critical_tasks:
            return

        # Create network diagram data
        fig = go.Figure()

        # Add critical path line
        x_coords = list(range(len(critical_tasks)))
        y_coords = [0] * len(critical_tasks)
        task_names = [task["name"] for task in critical_tasks]

        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=y_coords,
                mode="lines+markers+text",
                text=task_names,
                textposition="top center",
                line=dict(color="red", width=4),
                marker=dict(size=15, color="red"),
                name="Critical Path",
            )
        )

        fig.update_layout(
            title="Critical Path Flow",
            showlegend=False,
            height=300,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_workload_analysis(self):
        """Render team workload analysis"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        st.markdown(
            """
        <div class="chart-header">
            <div class="chart-title">⚖️ Team Workload Analysis</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        workload_data = self._get_workload_analysis()

        if workload_data:
            for member in workload_data:
                self._render_workload_member(member)

            # Workload distribution chart
            self._render_workload_chart(workload_data)
        else:
            st.info("⚖️ No workload data available.")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_workload_member(self, member):
        """Render individual team member workload"""
        name = member["name"]
        workload = member["workload"]
        capacity = member["capacity"]
        utilization = (workload / capacity * 100) if capacity > 0 else 0

        if utilization > 100:
            workload_class = "workload-overloaded"
            status = "Overloaded"
        elif utilization < 70:
            workload_class = "workload-underutilized"
            status = "Underutilized"
        else:
            workload_class = "workload-normal"
            status = "Optimal"

        st.markdown(
            f"""
        <div class="workload-member">
            <div class="member-header">
                <div class="member-name">👤 {name}</div>
                <div style="color: {'#ff6b6b' if utilization > 100 else '#2ed573' if utilization < 70 else '#4facfe'};">
                    {status} ({utilization:.1f}%)
                </div>
            </div>
            
            <div style="margin-bottom: 10px;">
                Workload: {workload}h / Capacity: {capacity}h
            </div>
            
            <div class="workload-bar">
                <div class="workload-fill {workload_class}" style="width: {min(utilization, 100)}%;"></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_workload_chart(self, workload_data):
        """Render workload distribution chart"""
        names = [member["name"] for member in workload_data]
        workloads = [member["workload"] for member in workload_data]
        capacities = [member["capacity"] for member in workload_data]

        fig = go.Figure()

        # Add capacity bars
        fig.add_trace(
            go.Bar(
                name="Capacity",
                x=names,
                y=capacities,
                marker_color="lightblue",
                opacity=0.7,
            )
        )

        # Add workload bars
        fig.add_trace(
            go.Bar(name="Current Workload", x=names, y=workloads, marker_color="blue")
        )

        fig.update_layout(
            title="Team Workload vs Capacity",
            xaxis_title="Team Members",
            yaxis_title="Hours",
            barmode="overlay",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_project_stats(self):
        """Render project statistics cards"""
        stats = self._calculate_project_stats()

        st.markdown('<div class="stats-container">', unsafe_allow_html=True)

        # Project completion rate
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{stats['completion_rate']:.1f}%</div>
            <div class="stat-label">Completion Rate</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # On-time delivery
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-icon">⏰</div>
            <div class="stat-value">{stats['on_time_rate']:.1f}%</div>
            <div class="stat-label">On-Time Delivery</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Average task duration
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-icon">📅</div>
            <div class="stat-value">{stats['avg_duration']}</div>
            <div class="stat-label">Avg Task Duration</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Team utilization
        st.markdown(
            f"""
        <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-value">{stats['team_utilization']:.1f}%</div>
            <div class="stat-label">Team Utilization</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    def _get_timeline_data(self):
        """Get timeline data for Gantt chart"""
        tasks = self.task_service.get_all_tasks()
        projects = self.project_service.get_all_projects()

        # Filter by selected project
        if st.session_state.selected_gantt_project != "All Projects":
            project_id = None
            for project in projects:
                if (
                    project.get("ProjectName")
                    == st.session_state.selected_gantt_project
                ):
                    project_id = project.get("ProjectID")
                    break

            if project_id:
                tasks = [t for t in tasks if t.get("ProjectID") == project_id]

        timeline_data = []
        for task in tasks:
            if task.get("StartDate") and task.get("EndDate"):
                # Get project name
                project_name = "Unknown Project"
                for project in projects:
                    if project.get("ProjectID") == task.get("ProjectID"):
                        project_name = project.get("ProjectName", "Unknown Project")
                        break

                timeline_data.append(
                    {
                        "Task": task.get("TaskName", "Untitled Task"),
                        "Resource": f"{project_name} - {task.get('AssigneeName', 'Unassigned')}",
                        "Start": task.get("StartDate"),
                        "End": task.get("EndDate"),
                        "Status": task.get("Status", "To Do"),
                        "Priority": task.get("Priority", "Medium"),
                        "Progress": task.get("Progress", 0),
                    }
                )

        return timeline_data

    def _get_milestones(self):
        """Get project milestones"""
        # Mock milestone data - in real implementation, this would come from database
        milestones = [
            {"name": "Project Kickoff", "date": "2025-01-15", "completed": True},
            {"name": "Phase 1 Complete", "date": "2025-02-28", "completed": False},
            {"name": "Beta Release", "date": "2025-04-15", "completed": False},
            {"name": "Final Release", "date": "2025-06-30", "completed": False},
        ]

        return milestones

    def _get_resource_allocation(self):
        """Get resource allocation data"""
        tasks = self.task_service.get_all_tasks()

        # Group tasks by assignee
        assignee_tasks = {}
        for task in tasks:
            assignee = task.get("AssigneeName", "Unassigned")
            if assignee not in assignee_tasks:
                assignee_tasks[assignee] = []
            assignee_tasks[assignee].append(task)

        resources = []
        for assignee, tasks_list in assignee_tasks.items():
            if assignee != "Unassigned":
                # Calculate utilization (mock calculation)
                total_estimated_hours = sum(
                    [task.get("EstimatedHours", 0) for task in tasks_list]
                )
                capacity_hours = 40  # 40 hours per week
                utilization = (
                    (total_estimated_hours / capacity_hours * 100)
                    if capacity_hours > 0
                    else 0
                )

                task_names = [
                    task.get("TaskName", "Untitled") for task in tasks_list[:5]
                ]  # Show first 5 tasks

                resources.append(
                    {
                        "name": assignee,
                        "utilization": min(utilization, 150),  # Cap at 150% for display
                        "tasks": task_names,
                    }
                )

        return resources

    def _get_critical_path(self):
        """Get critical path tasks"""
        # Mock critical path data - in real implementation, this would be calculated
        critical_tasks = [
            {"name": "Requirements Analysis", "duration": 5, "slack": 0},
            {"name": "System Design", "duration": 10, "slack": 0},
            {"name": "Core Development", "duration": 20, "slack": 0},
            {"name": "Integration Testing", "duration": 7, "slack": 0},
            {"name": "Deployment", "duration": 3, "slack": 0},
        ]

        return critical_tasks

    def _get_workload_analysis(self):
        """Get team workload analysis"""
        tasks = self.task_service.get_all_tasks()

        # Group by assignee and calculate workload
        assignee_workload = {}
        for task in tasks:
            assignee = task.get("AssigneeName", "Unassigned")
            if assignee != "Unassigned":
                if assignee not in assignee_workload:
                    assignee_workload[assignee] = 0
                assignee_workload[assignee] += task.get("EstimatedHours", 0)

        workload_data = []
        for assignee, workload in assignee_workload.items():
            capacity = 40  # 40 hours per week capacity
            workload_data.append(
                {"name": assignee, "workload": workload, "capacity": capacity}
            )

        return workload_data

    def _calculate_project_stats(self):
        """Calculate project statistics"""
        tasks = self.task_service.get_all_tasks()
        projects = self.project_service.get_all_projects()

        if not tasks:
            return {
                "completion_rate": 0,
                "on_time_rate": 0,
                "avg_duration": "0 days",
                "team_utilization": 0,
            }

        # Completion rate
        completed_tasks = [t for t in tasks if t.get("Status") == "Done"]
        completion_rate = (len(completed_tasks) / len(tasks) * 100) if tasks else 0

        # On-time delivery rate (mock calculation)
        on_time_tasks = len([t for t in completed_tasks if self._is_on_time(t)])
        on_time_rate = (
            (on_time_tasks / len(completed_tasks) * 100) if completed_tasks else 0
        )

        # Average task duration
        durations = []
        for task in tasks:
            if task.get("StartDate") and task.get("EndDate"):
                try:
                    start = pd.to_datetime(task.get("StartDate"))
                    end = pd.to_datetime(task.get("EndDate"))
                    duration = (end - start).days
                    durations.append(duration)
                except:
                    pass

        avg_duration = (
            f"{sum(durations) // len(durations)} days" if durations else "0 days"
        )

        # Team utilization
        workload_data = self._get_workload_analysis()
        if workload_data:
            total_workload = sum([member["workload"] for member in workload_data])
            total_capacity = sum([member["capacity"] for member in workload_data])
            team_utilization = (
                (total_workload / total_capacity * 100) if total_capacity > 0 else 0
            )
        else:
            team_utilization = 0

        return {
            "completion_rate": completion_rate,
            "on_time_rate": on_time_rate,
            "avg_duration": avg_duration,
            "team_utilization": team_utilization,
        }

    def _is_on_time(self, task):
        """Check if task was completed on time"""
        # Mock implementation - in real app, would compare actual completion date with planned
        return True  # Assume 80% of tasks are on time

    def _apply_time_filter(self, data):
        """Apply time range filter to data"""
        time_range = st.session_state.get("time_range", "All Time")

        if time_range == "All Time":
            return data

        today = datetime.now()

        if time_range == "Last 30 Days":
            start_date = today - timedelta(days=30)
            end_date = today
        elif time_range == "Next 30 Days":
            start_date = today
            end_date = today + timedelta(days=30)
        elif time_range == "Current Quarter":
            # Calculate current quarter
            quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1)
            end_date = datetime(today.year, quarter * 3 + 1, 1) - timedelta(days=1)
        else:
            return data

        # Filter data based on date range
        filtered_data = []
        for item in data:
            item_date = None
            if "Start" in item:
                try:
                    item_date = pd.to_datetime(item["Start"])
                except:
                    continue
            elif "date" in item:
                try:
                    item_date = pd.to_datetime(item["date"])
                except:
                    continue

            if item_date and start_date <= item_date <= end_date:
                filtered_data.append(item)

        return filtered_data
