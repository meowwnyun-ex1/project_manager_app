"""
UI Components and Rendering Module
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
from datetime import datetime


class UIRenderer:
    """UI rendering and component management"""

    def apply_styles(self):
        """Apply custom CSS styles"""
        st.markdown(
            """
        <style>
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Header gradient */
        .header-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .header-gradient::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100%" height="100%" fill="url(%23grain)"/></svg>');
            opacity: 0.3;
        }

        .header-gradient h1 {
            font-size: 3rem;
            margin: 0;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header-gradient p {
            font-size: 1.2rem;
            margin: 10px 0 0 0;
            position: relative;
            z-index: 1;
            opacity: 0.9;
        }

        /* Glass cards */
        .glass-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 12px 40px rgba(31, 38, 135, 0.25);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 60px rgba(31, 38, 135, 0.35);
        }

        /* Project cards */
        .project-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }

        .project-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }

        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
        }

        .status-planning { background: #FFA500; }
        .status-in-progress { background: #007BFF; }
        .status-review { background: #6F42C1; }
        .status-completed { background: #28A745; }
        .status-on-hold { background: #DC3545; }
        .status-cancelled { background: #6C757D; }

        /* Priority badges */
        .priority-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
            color: white;
        }

        .priority-low { background: #6C757D; }
        .priority-medium { background: #FFC107; }
        .priority-high { background: #FD7E14; }
        .priority-critical { background: #DC3545; }

        /* Enhanced buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .stButton > button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        /* Progress bars */
        .progress-container {
            background: #e5e7eb;
            border-radius: 10px;
            height: 8px;
            margin: 10px 0;
            overflow: hidden;
        }

        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #10b981 100%);
            border-radius: 10px;
            transition: width 0.3s ease;
        }

        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.1) 100%);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            margin: 10px 0;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def render_header(self):
        """Render application header"""
        st.markdown(
            """
        <div class="header-gradient">
            <h1>🚀 DENSO Project Manager Pro</h1>
            <p>Enterprise Project Management Platform</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_user_profile(self, user: Dict[str, Any]):
        """Render user profile in sidebar"""
        st.markdown(
            f"""
        <div class="glass-card" style="text-align: center;">
            <div style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 1.5rem;
                margin: 0 auto 15px auto;
            ">
                {user.get('FirstName', 'U')[0]}{user.get('LastName', 'U')[0]}
            </div>
            <h3 style="margin: 10px 0 5px 0; color: white;">{user.get('FirstName', 'Unknown')} {user.get('LastName', 'User')}</h3>
            <p style="margin: 0; color: rgba(255,255,255,0.8);"><strong>{user.get('Role', 'User')}</strong></p>
            <p style="margin: 0; color: rgba(255,255,255,0.6);">{user.get('Department', 'N/A')}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_quick_stats(self, stats: Dict[str, Any]):
        """Render quick stats in sidebar"""
        st.markdown("### 📊 Quick Stats")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Projects", stats.get("total_projects", 0))
            st.metric("Tasks", stats.get("total_tasks", 0))

        with col2:
            st.metric("Active", stats.get("active_projects", 0))
            st.metric("Users", stats.get("total_users", 0))

    def render_kpi_metrics(self, stats: Dict[str, Any]):
        """Render KPI metrics cards"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Projects",
                stats.get("total_projects", 0),
                delta=f"+{stats.get('new_projects_this_month', 0)} this month",
            )

        with col2:
            st.metric(
                "Active Projects",
                stats.get("active_projects", 0),
                delta=f"{(stats.get('active_projects', 0)/max(stats.get('total_projects', 1), 1)*100):.1f}%",
            )

        with col3:
            completion_rate = (
                stats.get("completed_tasks", 0)
                / max(stats.get("total_tasks", 1), 1)
                * 100
            )
            st.metric(
                "Task Completion",
                f"{completion_rate:.1f}%",
                delta=f"{stats.get('completed_tasks', 0)}/{stats.get('total_tasks', 0)}",
            )

        with col4:
            st.metric("Team Members", stats.get("total_users", 0))

    def render_project_status_chart(self, projects: List[Dict[str, Any]]):
        """Render project status distribution chart"""
        if not projects:
            st.info("No projects to display")
            return

        st.subheader("📊 Project Status Distribution")

        # Count projects by status
        status_counts = {}
        for project in projects:
            status = project.get("Status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Projects by Status",
                color_discrete_sequence=[
                    "#667eea",
                    "#764ba2",
                    "#f093fb",
                    "#48c6ef",
                    "#feca57",
                ],
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available")

    def render_task_priority_chart(self, tasks: List[Dict[str, Any]]):
        """Render task priority distribution chart"""
        if not tasks:
            st.info("No tasks to display")
            return

        st.subheader("🎯 Task Priority Distribution")

        # Count tasks by priority
        priority_counts = {}
        for task in tasks:
            priority = task.get("Priority", "Medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        if priority_counts:
            fig = px.bar(
                x=list(priority_counts.keys()),
                y=list(priority_counts.values()),
                title="Tasks by Priority",
                color=list(priority_counts.values()),
                color_continuous_scale="Reds",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No priority data available")

    def render_recent_projects(self, projects: List[Dict[str, Any]]):
        """Render recent projects list"""
        for project in projects:
            with st.container():
                st.markdown(
                    f"""
                <div class="project-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #2E3440;">{project.get('ProjectName', 'Unnamed')}</h4>
                            <p style="margin: 5px 0; color: #5E6C7E;">{(project.get('Description', '') or '')[:100]}...</p>
                            <small style="color: #6C757D;">Client: {project.get('ClientName', 'N/A')}</small>
                        </div>
                        <div style="text-align: right;">
                            <span class="status-badge status-{project.get('Status', 'unknown').lower().replace(' ', '-')}">{project.get('Status', 'Unknown')}</span>
                            <div style="margin-top: 10px;">
                                <strong>{project.get('Progress', 0)}% Complete</strong>
                            </div>
                        </div>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar" style="width: {project.get('Progress', 0)}%;"></div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    def render_loading_spinner(self, text: str = "Loading..."):
        """Render loading spinner with text"""
        st.markdown(
            f"""
        <div style="text-align: center; padding: 2rem;">
            <div style="
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem auto;
            "></div>
            <p style="color: #5E6C7E;">{text}</p>
        </div>
        
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

    def render_success_message(self, message: str):
        """Render success message"""
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(90deg, #28a745, #20c997);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            font-weight: 600;
        ">
            ✅ {message}
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_error_message(self, message: str):
        """Render error message"""
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(90deg, #dc3545, #e74c3c);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            font-weight: 600;
        ">
            ❌ {message}
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_info_message(self, message: str):
        """Render info message"""
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(90deg, #17a2b8, #20c997);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            font-weight: 600;
        ">
            ℹ️ {message}
        </div>
        """,
            unsafe_allow_html=True,
        )
