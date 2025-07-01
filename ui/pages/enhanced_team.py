# ui/pages/enhanced_team.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import random


def apply_modern_css():
    """Apply modern CSS for team page"""
    st.markdown(
        """
    <style>
    /* Team Page Styles */
    .team-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .team-header {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .team-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .team-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
    }
    
    .team-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.2);
        background: rgba(255, 255, 255, 0.15);
    }
    
    .member-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        color: white;
        font-weight: 700;
        margin: 0 auto 1rem auto;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        position: relative;
    }
    
    .member-avatar.online::after {
        content: '';
        position: absolute;
        bottom: 5px;
        right: 5px;
        width: 20px;
        height: 20px;
        background: #10b981;
        border-radius: 50%;
        border: 3px solid white;
    }
    
    .member-avatar.offline::after {
        content: '';
        position: absolute;
        bottom: 5px;
        right: 5px;
        width: 20px;
        height: 20px;
        background: #ef4444;
        border-radius: 50%;
        border: 3px solid white;
    }
    
    .member-name {
        color: white;
        font-size: 1.3rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .member-role {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .member-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .stat-item {
        text-align: center;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0.75rem;
    }
    
    .stat-number {
        color: #00d2ff;
        font-size: 1.5rem;
        font-weight: 700;
        display: block;
    }
    
    .stat-label {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    
    .role-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .role-admin {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
    
    .role-manager {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }
    
    .role-developer {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
    }
    
    .role-designer {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
    }
    
    .role-user {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
        color: white;
    }
    
    .performance-chart {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .chart-title {
        color: white;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .team-action-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    .action-button {
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .action-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    
    .action-button.secondary {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
    }
    
    .action-button.success {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    .action-button.warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    
    .team-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: scale(1.05);
        background: rgba(255, 255, 255, 0.2);
    }
    
    .metric-value {
        color: #00d2ff;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: white;
        font-size: 1.1rem;
        font-weight: 500;
    }
    
    .activity-feed {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(15px);
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
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .activity-text {
        color: white;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    
    /* Modal Styles */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-content {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        max-width: 500px;
        width: 90%;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    .modal-header {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        color: #1f2937;
        text-align: center;
    }
    
    .form-group {
        margin-bottom: 1.5rem;
    }
    
    .form-label {
        display: block;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #374151;
    }
    
    .form-input {
        width: 100%;
        padding: 0.75rem 1rem;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .form-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .form-select {
        width: 100%;
        padding: 0.75rem 1rem;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        font-size: 1rem;
        background: white;
        cursor: pointer;
    }
    
    .button-group {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 2rem;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
    }
    
    .btn-secondary {
        background: #6b7280;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .btn-secondary:hover {
        background: #4b5563;
    }
    
    @media (max-width: 768px) {
        .team-metrics {
            grid-template-columns: 1fr;
        }
        
        .team-action-buttons {
            flex-direction: column;
            align-items: center;
        }
        
        .action-button {
            width: 100%;
            max-width: 300px;
        }
        
        .member-stats {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def get_sample_team_data():
    """Get sample team data"""
    return [
        {
            "id": 1,
            "name": "John Smith",
            "role": "Admin",
            "email": "john@company.com",
            "status": "online",
            "tasks_completed": 45,
            "tasks_assigned": 52,
            "projects": 8,
            "performance": 87,
            "join_date": "2023-01-15",
            "last_active": "2 minutes ago",
        },
        {
            "id": 2,
            "name": "Sarah Johnson",
            "role": "Manager",
            "email": "sarah@company.com",
            "status": "online",
            "tasks_completed": 38,
            "tasks_assigned": 41,
            "projects": 6,
            "performance": 93,
            "join_date": "2023-02-20",
            "last_active": "5 minutes ago",
        },
        {
            "id": 3,
            "name": "Mike Chen",
            "role": "Developer",
            "email": "mike@company.com",
            "status": "offline",
            "tasks_completed": 67,
            "tasks_assigned": 70,
            "projects": 4,
            "performance": 96,
            "join_date": "2023-03-10",
            "last_active": "2 hours ago",
        },
        {
            "id": 4,
            "name": "Emma Wilson",
            "role": "Designer",
            "email": "emma@company.com",
            "status": "online",
            "tasks_completed": 29,
            "tasks_assigned": 33,
            "projects": 5,
            "performance": 88,
            "join_date": "2023-04-05",
            "last_active": "1 minute ago",
        },
        {
            "id": 5,
            "name": "David Brown",
            "role": "Developer",
            "email": "david@company.com",
            "status": "offline",
            "tasks_completed": 41,
            "tasks_assigned": 45,
            "projects": 3,
            "performance": 91,
            "join_date": "2023-05-12",
            "last_active": "4 hours ago",
        },
        {
            "id": 6,
            "name": "Lisa Garcia",
            "role": "User",
            "email": "lisa@company.com",
            "status": "online",
            "tasks_completed": 23,
            "tasks_assigned": 28,
            "projects": 2,
            "performance": 82,
            "join_date": "2023-06-18",
            "last_active": "Just now",
        },
    ]


def render_team_overview():
    """Render team overview metrics"""
    team_data = get_sample_team_data()

    # Calculate metrics
    total_members = len(team_data)
    online_members = len([m for m in team_data if m["status"] == "online"])
    total_tasks = sum(m["tasks_assigned"] for m in team_data)
    completed_tasks = sum(m["tasks_completed"] for m in team_data)
    avg_performance = sum(m["performance"] for m in team_data) / total_members

    st.markdown('<div class="team-metrics">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value">{total_members}</div>
            <div class="metric-label">Team Members</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value">{online_members}</div>
            <div class="metric-label">Online Now</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        completion_rate = (
            int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        )
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value">{completion_rate}%</div>
            <div class="metric-label">Task Completion</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-value">{avg_performance:.0f}%</div>
            <div class="metric-label">Avg Performance</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_team_members():
    """Render team members grid"""
    team_data = get_sample_team_data()

    st.markdown("### 👥 Team Members")

    # Create grid layout
    cols_per_row = 3
    for i in range(0, len(team_data), cols_per_row):
        cols = st.columns(cols_per_row)

        for j, col in enumerate(cols):
            if i + j < len(team_data):
                member = team_data[i + j]
                with col:
                    render_member_card(member)


def render_member_card(member):
    """Render individual member card"""
    # Get initials for avatar
    initials = "".join([name[0] for name in member["name"].split()])

    # Role badge class
    role_class = f"role-{member['role'].lower()}"

    # Status class for avatar
    status_class = member["status"]

    # Calculate completion rate
    completion_rate = (
        int((member["tasks_completed"] / member["tasks_assigned"] * 100))
        if member["tasks_assigned"] > 0
        else 0
    )

    st.markdown(
        f"""
    <div class="team-card">
        <div class="member-avatar {status_class}">
            {initials}
        </div>
        <div class="member-name">{member['name']}</div>
        <div class="member-role">
            <span class="role-badge {role_class}">{member['role']}</span>
        </div>
        
        <div class="member-stats">
            <div class="stat-item">
                <span class="stat-number">{member['tasks_completed']}</span>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-item">
                <span class="stat-number">{completion_rate}%</span>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-item">
                <span class="stat-number">{member['projects']}</span>
                <div class="stat-label">Projects</div>
            </div>
            <div class="stat-item">
                <span class="stat-number">{member['performance']}%</span>
                <div class="stat-label">Performance</div>
            </div>
        </div>
        
        <div style="margin-top: 1rem; text-align: center;">
            <small style="color: rgba(255, 255, 255, 0.6);">
                Last active: {member['last_active']}
            </small>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_team_performance_chart():
    """Render team performance analytics"""
    st.markdown('<div class="performance-chart">', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-title">📊 Team Performance Analytics</div>',
        unsafe_allow_html=True,
    )

    team_data = get_sample_team_data()

    # Create performance comparison chart
    names = [member["name"] for member in team_data]
    performance = [member["performance"] for member in team_data]
    completion_rates = [
        (
            int((member["tasks_completed"] / member["tasks_assigned"] * 100))
            if member["tasks_assigned"] > 0
            else 0
        )
        for member in team_data
    ]

    fig = go.Figure()

    # Add performance bars
    fig.add_trace(
        go.Bar(
            name="Performance Score",
            x=names,
            y=performance,
            marker_color="#00d2ff",
            yaxis="y",
            offsetgroup=1,
        )
    )

    # Add completion rate bars
    fig.add_trace(
        go.Bar(
            name="Task Completion %",
            x=names,
            y=completion_rates,
            marker_color="#3a7bd5",
            yaxis="y2",
            offsetgroup=2,
        )
    )

    fig.update_layout(
        title="Team Member Performance Comparison",
        xaxis_title="Team Members",
        yaxis=dict(title="Performance Score", side="left"),
        yaxis2=dict(title="Completion Rate %", side="right", overlaying="y"),
        barmode="group",
        template="plotly_dark",
        height=400,
        showlegend=True,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_workload_distribution():
    """Render workload distribution chart"""
    st.markdown('<div class="performance-chart">', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-title">📈 Workload Distribution</div>',
        unsafe_allow_html=True,
    )

    team_data = get_sample_team_data()

    # Create workload pie chart
    names = [member["name"] for member in team_data]
    tasks = [member["tasks_assigned"] for member in team_data]

    fig = px.pie(
        values=tasks,
        names=names,
        title="Task Distribution Among Team Members",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    fig.update_layout(
        template="plotly_dark",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_activity_feed():
    """Render team activity feed"""
    st.markdown('<div class="activity-feed">', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-title">� Recent Team Activity</div>', unsafe_allow_html=True
    )

    # Sample activity data
    activities = [
        {
            "time": "2 minutes ago",
            "text": '🎯 <strong>Mike Chen</strong> completed task "API Integration" in Project Alpha',
        },
        {
            "time": "5 minutes ago",
            "text": "👥 <strong>Sarah Johnson</strong> assigned new task to Emma Wilson",
        },
        {
            "time": "12 minutes ago",
            "text": '📋 <strong>John Smith</strong> created new project "Mobile App Redesign"',
        },
        {
            "time": "25 minutes ago",
            "text": "✅ <strong>Emma Wilson</strong> submitted design mockups for review",
        },
        {
            "time": "1 hour ago",
            "text": "🎉 <strong>David Brown</strong> deployed new feature to production",
        },
        {
            "time": "2 hours ago",
            "text": "📝 <strong>Lisa Garcia</strong> updated project documentation",
        },
        {
            "time": "3 hours ago",
            "text": "🔧 <strong>Mike Chen</strong> fixed critical bug in payment system",
        },
        {
            "time": "4 hours ago",
            "text": "📊 <strong>Sarah Johnson</strong> generated weekly performance report",
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


def render_team_actions():
    """Render team action buttons"""
    st.markdown('<div class="team-action-buttons">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("👤 Add Member", key="add_member", help="Add new team member"):
            st.session_state.show_add_member_modal = True

    with col2:
        if st.button("📧 Send Invite", key="send_invite", help="Send invitation email"):
            st.success("✅ Invitation sent successfully!")

    with col3:
        if st.button(
            "📊 Generate Report", key="generate_report", help="Generate team report"
        ):
            with st.spinner("Generating report..."):
                time.sleep(2)
            st.success("✅ Team report generated!")

    with col4:
        if st.button(
            "⚙️ Team Settings", key="team_settings", help="Manage team settings"
        ):
            st.info("🔧 Team settings panel would open here")

    st.markdown("</div>", unsafe_allow_html=True)


def render_add_member_modal():
    """Render add member modal"""
    if st.session_state.get("show_add_member_modal", False):
        with st.form("add_member_form"):
            st.markdown("### 👤 Add New Team Member")

            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Full Name*", placeholder="John Doe")
                email = st.text_input("Email*", placeholder="john@company.com")

            with col2:
                role = st.selectbox(
                    "Role*", ["User", "Developer", "Designer", "Manager", "Admin"]
                )
                department = st.selectbox(
                    "Department", ["Engineering", "Design", "Marketing", "Sales", "HR"]
                )

            message = st.text_area(
                "Welcome Message", placeholder="Welcome to the team!"
            )

            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.form_submit_button("✅ Add Member"):
                    if name and email:
                        st.success(f"✅ {name} added to team successfully!")
                        st.session_state.show_add_member_modal = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Please fill in required fields")

            with col2:
                if st.form_submit_button("📧 Add & Invite"):
                    if name and email:
                        st.success(f"✅ {name} added and invitation sent!")
                        st.session_state.show_add_member_modal = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Please fill in required fields")

            with col3:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_add_member_modal = False
                    st.rerun()


def render_team_calendar():
    """Render team calendar view"""
    st.markdown("### � Team Calendar")

    # Create sample calendar data
    today = datetime.now()
    calendar_events = []

    for i in range(10):
        event_date = today + timedelta(days=i)
        calendar_events.append(
            {
                "date": event_date.strftime("%Y-%m-%d"),
                "day": event_date.strftime("%A"),
                "events": random.randint(0, 4),
            }
        )

    # Display calendar in grid
    cols = st.columns(5)
    for i, event in enumerate(calendar_events[:5]):
        with cols[i]:
            st.markdown(
                f"""
            <div class="team-card" style="text-align: center; padding: 1rem;">
                <div style="color: #00d2ff; font-weight: 600; margin-bottom: 0.5rem;">
                    {event['day'][:3]}
                </div>
                <div style="color: white; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
                    {event['date'].split('-')[2]}
                </div>
                <div style="color: rgba(255, 255, 255, 0.8); font-size: 0.85rem;">
                    {event['events']} events
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_enhanced_team():
    """Main function to render enhanced team page"""

    # Apply modern CSS
    apply_modern_css()

    # Page header
    st.markdown(
        """
    <div class="team-container">
        <div class="team-header">👥 Team Management</div>
        <p style="color: white; text-align: center; font-size: 1.1rem; margin-bottom: 0;">
            Manage your team members, track performance, and collaborate effectively
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Team overview metrics
    render_team_overview()

    # Team action buttons
    render_team_actions()

    # Handle add member modal
    render_add_member_modal()

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["👥 Members", "📊 Performance", "🔄 Activity", "📅 Calendar", "⚙️ Settings"]
    )

    with tab1:
        render_team_members()

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            render_team_performance_chart()
        with col2:
            render_workload_distribution()

    with tab3:
        render_activity_feed()

    with tab4:
        render_team_calendar()

        # Add some team events
        st.markdown("### 📋 Upcoming Team Events")
        events = [
            {"date": "2024-01-15", "event": "Team Sprint Planning", "time": "10:00 AM"},
            {"date": "2024-01-17", "event": "Design Review Meeting", "time": "2:00 PM"},
            {
                "date": "2024-01-20",
                "event": "Monthly Team Retrospective",
                "time": "3:00 PM",
            },
            {
                "date": "2024-01-22",
                "event": "Project Deadline - Alpha Release",
                "time": "End of Day",
            },
        ]

        for event in events:
            st.markdown(
                f"""
            <div class="team-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="color: white; font-weight: 600; margin-bottom: 0.25rem;">
                            {event['event']}
                        </div>
                        <div style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">
                            📅 {event['date']} • 🕐 {event['time']}
                        </div>
                    </div>
                    <div style="color: #00d2ff; font-size: 1.5rem;">
                        📅
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with tab5:
        st.markdown("### ⚙️ Team Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Team Preferences")
            st.selectbox("Default Project View", ["List", "Grid", "Calendar"])
            st.selectbox("Notification Frequency", ["Real-time", "Hourly", "Daily"])
            st.checkbox("Allow team members to invite others", value=True)
            st.checkbox("Require approval for new tasks", value=False)

        with col2:
            st.markdown("#### Access Control")
            st.selectbox(
                "Default Role for New Members", ["User", "Developer", "Designer"]
            )
            st.multiselect(
                "Allowed Email Domains",
                ["@company.com", "@contractor.com"],
                default=["@company.com"],
            )
            st.checkbox("Enable two-factor authentication", value=True)
            st.checkbox("Restrict access by IP address", value=False)

        if st.button("💾 Save Team Settings", key="save_team_settings"):
            st.success("✅ Team settings saved successfully!")


# Export the main function
__all__ = ["render_enhanced_team"]
