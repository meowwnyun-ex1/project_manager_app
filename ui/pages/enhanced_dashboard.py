# ui/pages/enhanced_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

# Import services
from services.enhanced_db_service import get_db_service
from services.enhanced_project_service import get_project_service
from services.task_service import get_task_service
from services.user_service import get_user_service
from core.session_manager import SessionManager


class EnhancedDashboard:
    """Enhanced dashboard with real-time analytics and modern UI"""

    def __init__(self):
        self.db_service = get_db_service()
        self.project_service = get_project_service()
        self.task_service = get_task_service()
        self.user_service = get_user_service()
        self.session_manager = SessionManager()

    def render(self):
        """Render enhanced dashboard"""
        self._apply_dashboard_css()
        self._render_header()
        self._render_key_metrics()
        self._render_charts()
        self._render_recent_activity()
        self._render_quick_actions()

    def _apply_dashboard_css(self):
        """Apply modern CSS for dashboard"""
        st.markdown(
            """
        <style>
        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        
        .dashboard-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .dashboard-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .metric-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        }
        
        .metric-card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        }
        
        .metric-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #00d2ff;
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-size: 1.1rem;
            color: white;
            font-weight: 500;
        }
        
        .metric-change {
            font-size: 0.9rem;
            margin-top: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-weight: 600;
        }
        
        .metric-change.positive {
            background: rgba(16, 185, 129, 0.2);
            color: #10B981;
        }
        
        .metric-change.negative {
            background: rgba(239, 68, 68, 0.2);
            color: #EF4444;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .chart-title {
            color: white;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .activity-feed {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-height: 400px;
            overflow-y: auto;
        }
        
        .activity-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #00d2ff;
            transition: all 0.3s ease;
        }
        
        .activity-item:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateX(5px);
        }
        
        .activity-time {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
        }
        
        .activity-text {
            color: white;
            font-size: 0.95rem;
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .action-button {
            background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
            color: white;
            border: none;
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .action-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        
        .action-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .action-label {
            font-weight: 600;
            font-size: 1rem;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_header(self):
        """Render dashboard header"""
        user_name = self.session_manager.get_user_full_name()
        current_time = datetime.now().strftime("%B %d, %Y")

        st.markdown(
            f"""
        <div class="dashboard-header">
            <div class="dashboard-title">Welcome back, {user_name}! 👋</div>
            <div class="dashboard-subtitle">Here's what's happening with your projects today • {current_time}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_key_metrics(self):
        """Render key performance metrics"""
        # Get real data from services
        projects = self.project_service.get_all_projects()
        tasks = self.task_service.get_all_tasks()
        users = self.user_service.get_all_users()

        # Calculate metrics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.get("Status") == "In Progress"])
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("Status") == "Done"])
        team_members = len([u for u in users if u.get("Active")])

        # Calculate completion rate
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        # Mock change data (in real app, calculate from historical data)
        project_change = "+12%"
        task_change = "+8%"
        team_change = "+2"
        completion_change = "+5%"

        st.markdown('<div class="metric-container">', unsafe_allow_html=True)

        # Projects metric
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{total_projects}</div>
            <div class="metric-label">Total Projects</div>
            <div class="metric-change positive">{project_change} this month</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Tasks metric
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{completed_tasks}/{total_tasks}</div>
            <div class="metric-label">Tasks Completed</div>
            <div class="metric-change positive">{task_change} this week</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Team metric
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{team_members}</div>
            <div class="metric-label">Team Members</div>
            <div class="metric-change positive">{team_change} new members</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Completion rate metric
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-value">{completion_rate:.1f}%</div>
            <div class="metric-label">Completion Rate</div>
            <div class="metric-change positive">{completion_change} improved</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_charts(self):
        """Render dashboard charts"""
        col1, col2 = st.columns(2)

        with col1:
            self._render_project_status_chart()

        with col2:
            self._render_task_progress_chart()

        # Full width charts
        self._render_timeline_chart()
        self._render_team_performance_chart()

    def _render_project_status_chart(self):
        """Render project status distribution chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-title">📊 Project Status Distribution</div>',
            unsafe_allow_html=True,
        )

        projects = self.project_service.get_all_projects()

        if projects:
            # Count projects by status
            status_counts = {}
            for project in projects:
                status = project.get("Status", "Planning")
                status_counts[status] = status_counts.get(status, 0) + 1

            # Create pie chart
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=list(status_counts.keys()),
                        values=list(status_counts.values()),
                        hole=0.4,
                        marker=dict(
                            colors=[
                                "#667eea",
                                "#764ba2",
                                "#f093fb",
                                "#f5576c",
                                "#4facfe",
                            ],
                            line=dict(color="#FFFFFF", width=2),
                        ),
                    )
                ]
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No projects found")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_task_progress_chart(self):
        """Render task progress chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-title">📈 Task Progress Overview</div>',
            unsafe_allow_html=True,
        )

        tasks = self.task_service.get_all_tasks()

        if tasks:
            # Group tasks by status
            status_counts = {}
            for task in tasks:
                status = task.get("Status", "To Do")
                status_counts[status] = status_counts.get(status, 0) + 1

            # Create bar chart
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=list(status_counts.keys()),
                        y=list(status_counts.values()),
                        marker_color=[
                            "#667eea",
                            "#764ba2",
                            "#f093fb",
                            "#f5576c",
                            "#4facfe",
                        ],
                    )
                ]
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Status",
                yaxis_title="Count",
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks found")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_timeline_chart(self):
        """Render project timeline chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-title">📅 Project Timeline</div>', unsafe_allow_html=True
        )

        projects = self.project_service.get_all_projects()

        if projects:
            # Filter projects with dates
            timeline_projects = []
            for project in projects:
                if project.get("StartDate") and project.get("EndDate"):
                    timeline_projects.append(
                        {
                            "Project": project.get("ProjectName", "Untitled"),
                            "Start": project.get("StartDate"),
                            "End": project.get("EndDate"),
                            "Status": project.get("Status", "Planning"),
                        }
                    )

            if timeline_projects:
                df = pd.DataFrame(timeline_projects)

                # Create Gantt chart
                fig = px.timeline(
                    df,
                    x_start="Start",
                    x_end="End",
                    y="Project",
                    color="Status",
                    title="",
                    color_discrete_map={
                        "Planning": "#6B7280",
                        "In Progress": "#3B82F6",
                        "Completed": "#10B981",
                        "On Hold": "#F59E0B",
                        "Cancelled": "#EF4444",
                    },
                )

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    height=400,
                    margin=dict(l=20, r=20, t=20, b=20),
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No projects with timeline data found")
        else:
            st.info("No projects found")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_team_performance_chart(self):
        """Render team performance chart"""
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-title">👥 Team Performance</div>', unsafe_allow_html=True
        )

        # Get mock team performance data
        team_data = [
            {
                "Member": "John Smith",
                "Completed": 12,
                "In Progress": 3,
                "Performance": 95,
            },
            {
                "Member": "Sarah Johnson",
                "Completed": 8,
                "In Progress": 5,
                "Performance": 88,
            },
            {
                "Member": "Mike Chen",
                "Completed": 15,
                "In Progress": 2,
                "Performance": 92,
            },
            {
                "Member": "Emma Wilson",
                "Completed": 6,
                "In Progress": 4,
                "Performance": 85,
            },
            {
                "Member": "David Brown",
                "Completed": 10,
                "In Progress": 6,
                "Performance": 90,
            },
        ]

        df = pd.DataFrame(team_data)

        # Create grouped bar chart
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                name="Completed Tasks",
                x=df["Member"],
                y=df["Completed"],
                marker_color="#10B981",
            )
        )

        fig.add_trace(
            go.Bar(
                name="In Progress",
                x=df["Member"],
                y=df["In Progress"],
                marker_color="#3B82F6",
            )
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            barmode="group",
            xaxis_title="Team Members",
            yaxis_title="Tasks",
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_recent_activity(self):
        """Render recent activity feed"""
        st.markdown('<div class="activity-feed">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-title">🔔 Recent Activity</div>', unsafe_allow_html=True
        )

        # Mock recent activities
        activities = [
            {
                "time": "2 minutes ago",
                "text": '🎯 John Smith completed task "Database Migration" in Website Redesign',
            },
            {
                "time": "15 minutes ago",
                "text": '📋 Sarah Johnson created new project "Mobile App Development"',
            },
            {
                "time": "1 hour ago",
                "text": '✅ Mike Chen marked "API Integration" as completed',
            },
            {
                "time": "2 hours ago",
                "text": '👥 Emma Wilson joined project "E-commerce Platform"',
            },
            {
                "time": "3 hours ago",
                "text": '📝 David Brown updated task "User Interface Design"',
            },
            {
                "time": "4 hours ago",
                "text": '🚀 Lisa Garcia deployed "Payment System" to production',
            },
            {
                "time": "5 hours ago",
                "text": "📊 Tom Wilson generated monthly project report",
            },
            {
                "time": "6 hours ago",
                "text": "🔧 Alice Cooper fixed critical bug in authentication system",
            },
        ]

        for activity in activities:
            st.markdown(
                f"""
            <div class="activity-item">
                <div class="activity-time">{activity['time']}</div>
                <div class="activity-text">{activity['text']}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown(
            '<div class="chart-title" style="text-align: center; margin: 2rem 0;">⚡ Quick Actions</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="quick-actions">', unsafe_allow_html=True)

        # Quick action buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(
                "📝 New Project", key="quick_new_project", help="Create a new project"
            ):
                st.session_state.current_page = "projects"
                st.session_state.show_project_modal = True
                st.rerun()

        with col2:
            if st.button("✅ New Task", key="quick_new_task", help="Create a new task"):
                st.session_state.current_page = "tasks"
                st.session_state.show_task_modal = True
                st.rerun()

        with col3:
            if st.button(
                "📊 View Reports",
                key="quick_reports",
                help="View analytics and reports",
            ):
                st.session_state.current_page = "reports"
                st.rerun()

        with col4:
            if st.button(
                "👥 Team Overview", key="quick_team", help="View team performance"
            ):
                st.session_state.current_page = "team"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
