"""
🚀 Project Manager Pro v3.0 - Enhanced Dashboard
Modern, interactive dashboard with real-time analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List

from core.session_manager import SessionManager
from services.enhanced_db_service import EnhancedDBService
from ui.components.modern_cards import ModernCards
from ui.components.interactive_charts import InteractiveCharts
from ui.components.notification_system import NotificationSystem

class EnhancedDashboard:
    """Enhanced dashboard with modern UI and real-time analytics"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.db_service = EnhancedDBService()
        self.modern_cards = ModernCards()
        self.charts = InteractiveCharts()
        self.notifications = NotificationSystem()
    
    def render(self) -> None:
        """Render the main dashboard"""
        # Page header
        self._render_header()
        
        # Quick actions and notifications
        self._render_quick_actions()
        
        # Key metrics
        self._render_key_metrics()
        
        # Charts and analytics
        self._render_analytics_section()
        
        # Recent activity and tasks
        self._render_activity_section()
        
        # Update performance metrics
        self.session_manager.update_performance_metric('dashboard_views')
    
    def _render_header(self) -> None:
        """Render dashboard header"""
        user_name = self.session_manager.get_user_full_name()
        current_time = datetime.now().strftime("%A, %B %d, %Y")
        
        st.markdown(f"""
        <div class="dashboard-header">
            <div class="header-content">
                <div class="welcome-section">
                    <h1>🏠 Welcome back, {user_name}!</h1>
                    <p class="header-subtitle">📅 {current_time}</p>
                </div>
                <div class="header-stats">
                    <div class="stat-item">
                        <span class="stat-value">{self._get_active_projects_count()}</span>
                        <span class="stat-label">Active Projects</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">{self._get_pending_tasks_count()}</span>
                        <span class="stat-label">Pending Tasks</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_quick_actions(self) -> None:
        """Render quick action buttons"""
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📁 New Project", use_container_width=True):
                st.session_state['show_new_project_modal'] = True
        
        with col2:
            if st.button("✅ New Task", use_container_width=True):
                st.session_state['show_new_task_modal'] = True
        
        with col3:
            if st.button("📊 View Reports", use_container_width=True):
                st.session_state['current_page'] = 'reports'
                st.experimental_rerun()
        
        with col4:
            if st.button("👥 Team View", use_container_width=True):
                st.session_state['current_page'] = 'team'
                st.experimental_rerun()
        
        with col5:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.experimental_rerun()
        
        # Handle modals
        self._handle_quick_action_modals()
    
    def _render_key_metrics(self) -> None:
        """Render key performance metrics"""
        st.markdown("### 📊 Key Metrics")
        
        # Get metrics data
        metrics = self._get_dashboard_metrics()
        
        # Create metric cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.modern_cards.metric_card(
                title="Total Projects",
                value=metrics['projects']['total'],
                delta=metrics['projects'].get('delta', 0),
                icon="📁",
                color="blue"
            )
        
        with col2:
            self.modern_cards.metric_card(
                title="Active Tasks",
                value=metrics['tasks']['active'],
                delta=metrics['tasks'].get('delta', 0),
                icon="✅",
                color="green"
            )
        
        with col3:
            completion_rate = self._calculate_completion_rate(metrics)
            self.modern_cards.metric_card(
                title="Completion Rate",
                value=f"{completion_rate}%",
                delta=metrics.get('completion_delta', 0),
                icon="📈",
                color="purple"
            )
        
        with col4:
            overdue_count = metrics['tasks'].get('overdue', 0)
            self.modern_cards.metric_card(
                title="Overdue Tasks",
                value=overdue_count,
                delta=metrics.get('overdue_delta', 0),
                icon="⚠️",
                color="red" if overdue_count > 0 else "green"
            )
    
    def _render_analytics_section(self) -> None:
        """Render analytics charts section"""
        st.markdown("### 📈 Analytics & Insights")
        
        # Create tabs for different analytics views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Project Overview", 
            "📈 Performance Trends", 
            "👥 Team Productivity", 
            "⏰ Timeline Analysis"
        ])
        
        with tab1:
            self._render_project_overview_charts()
        
        with tab2:
            self._render_performance_trends()
        
        with tab3:
            self._render_team_productivity()
        
        with tab4:
            self._render_timeline_analysis()
    
    def _render_project_overview_charts(self) -> None:
        """Render project overview charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Project status distribution
            status_data = self._get_project_status_data()
            if status_data:
                fig = self.charts.create_donut_chart(
                    data=status_data,
                    labels='Status',
                    values='Count',
                    title="Project Status Distribution",
                    colors=['#10B981', '#F59E0B', '#3B82F6', '#EF4444']
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Priority distribution
            priority_data = self._get_priority_distribution()
            if priority_data:
                fig = self.charts.create_bar_chart(
                    data=priority_data,
                    x='Priority',
                    y='Count',
                    title="Task Priority Distribution",
                    color='Priority',
                    color_map={
                        'Critical': '#EF4444',
                        'High': '#F59E0B',
                        'Medium': '#3B82F6',
                        'Low': '#10B981'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_performance_trends(self) -> None:
        """Render performance trend charts"""
        # Get performance data
        performance_data = self._get_performance_trends_data()
        
        if performance_data:
            # Create multi-line chart for trends
            fig = self.charts.create_line_chart(
                data=performance_data,
                x='Date',
                y='Value',
                color='Metric',
                title="Performance Trends (Last 30 Days)",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance insights
            self._render_performance_insights(performance_data)
    
    def _render_team_productivity(self) -> None:
        """Render team productivity charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Team member task completion
            team_data = self._get_team_productivity_data()
            if team_data:
                fig = self.charts.create_horizontal_bar_chart(
                    data=team_data,
                    x='Tasks_Completed',
                    y='Team_Member',
                    title="Team Member Task Completion",
                    color='Tasks_Completed',
                    color_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Workload distribution
            workload_data = self._get_workload_distribution()
            if workload_data:
                fig = self.charts.create_scatter_chart(
                    data=workload_data,
                    x='Assigned_Tasks',
                    y='Completed_Tasks',
                    size='Total_Hours',
                    title="Team Workload vs Completion",
                    hover_data=['Team_Member']
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_timeline_analysis(self) -> None:
        """Render timeline analysis"""
        # Gantt-style timeline view
        timeline_data = self._get_timeline_data()
        
        if timeline_data:
            fig = self.charts.create_gantt_chart(
                data=timeline_data,
                x_start='Start_Date',
                x_end='End_Date',
                y='Project_Name',
                color='Status',
                title="Project Timeline Overview"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Timeline insights
            self._render_timeline_insights(timeline_data)
    
    def _render_activity_section(self) -> None:
        """Render recent activity and task sections"""
        st.markdown("### 🔄 Recent Activity & Tasks")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_recent_activity()
        
        with col2:
            self._render_upcoming_tasks()
    
    def _render_recent_activity(self) -> None:
        """Render recent activity feed"""
        st.markdown("#### 📝 Recent Activity")
        
        # Get recent activity data
        activities = self._get_recent_activities()
        
        if activities:
            for activity in activities[:10]:  # Show last 10 activities
                time_ago = self._format_time_ago(activity['created_date'])
                
                st.markdown(f"""
                <div class="activity-item">
                    <div class="activity-icon">{self._get_activity_icon(activity['action'])}</div>
                    <div class="activity-content">
                        <div class="activity-text">{activity['details']}</div>
                        <div class="activity-meta">{time_ago} • {activity.get('username', 'System')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent activity found.")
    
    def _render_upcoming_tasks(self) -> None:
        """Render upcoming tasks"""
        st.markdown("#### ⏰ Upcoming Tasks")
        
        # Get upcoming tasks
        tasks = self._get_upcoming_tasks()
        
        if tasks:
            for task in tasks[:10]:  # Show next 10 tasks
                due_date = task.get('due_date')
                days_until_due = self._calculate_days_until_due(due_date) if due_date else None
                
                priority_color = self._get_priority_color(task.get('priority', 'Medium'))
                status_color = self._get_status_color(task.get('status', 'To Do'))
                
                st.markdown(f"""
                <div class="task-item">
                    <div class="task-priority" style="background-color: {priority_color}"></div>
                    <div class="task-content">
                        <div class="task-title">{task['task_name']}</div>
                        <div class="task-meta">
                            <span class="task-project">{task.get('project_name', 'No Project')}</span>
                            <span class="task-status" style="color: {status_color}">{task['status']}</span>
                            {f'<span class="task-due">Due in {days_until_due} days</span>' if days_until_due else ''}
                        </div>
                    </div>
                    <div class="task-progress">
                        <div class="progress-bar" style="width: {task.get('progress', 0)}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No upcoming tasks found.")
    
    def _handle_quick_action_modals(self) -> None:
        """Handle quick action modal dialogs"""
        # New Project Modal
        if st.session_state.get('show_new_project_modal', False):
            self._show_new_project_modal()
        
        # New Task Modal
        if st.session_state.get('show_new_task_modal', False):
            self._show_new_task_modal()
    
    def _show_new_project_modal(self) -> None:
        """Show new project creation modal"""
        with st.expander("📁 Create New Project", expanded=True):
            with st.form("quick_new_project"):
                col1, col2 = st.columns(2)
                
                with col1:
                    project_name = st.text_input("Project Name*")
                    start_date = st.date_input("Start Date")
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
                with col2:
                    client_name = st.text_input("Client Name")
                    end_date = st.date_input("End Date")
                    budget = st.number_input("Budget ($)", min_value=0.0, format="%.2f")
                
                description = st.text_area("Description")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("✅ Create Project"):
                        self._create_quick_project({
                            'project_name': project_name,
                            'description': description,
                            'start_date': start_date,
                            'end_date': end_date,
                            'priority': priority,
                            'client_name': client_name,
                            'budget': budget
                        })
                
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state['show_new_project_modal'] = False
                        st.experimental_rerun()
    
    def _show_new_task_modal(self) -> None:
        """Show new task creation modal"""
        with st.expander("✅ Create New Task", expanded=True):
            with st.form("quick_new_task"):
                # Get projects for selection
                projects = self._get_user_projects()
                project_options = {p['project_name']: p['project_id'] for p in projects}
                
                col1, col2 = st.columns(2)
                
                with col1:
                    task_name = st.text_input("Task Name*")
                    project = st.selectbox("Project*", options=list(project_options.keys()))
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                
                with col2:
                    assignee = st.selectbox("Assignee", ["Self"] + self._get_team_members())
                    due_date = st.date_input("Due Date")
                    estimated_hours = st.number_input("Estimated Hours", min_value=0.0, max_value=999.0, step=0.5)
                
                description = st.text_area("Description")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("✅ Create Task"):
                        self._create_quick_task({
                            'task_name': task_name,
                            'description': description,
                            'project_id': project_options.get(project),
                            'priority': priority,
                            'assignee': assignee,
                            'due_date': due_date,
                            'estimated_hours': estimated_hours
                        })
                
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state['show_new_task_modal'] = False
                        st.experimental_rerun()
    
    # Data fetching methods
    def _get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics from database"""
        user_id = self.session_manager.get_user_id()
        return self.db_service.get_dashboard_metrics(user_id)
    
    def _get_active_projects_count(self) -> int:
        """Get count of active projects"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT COUNT(*) as count
                FROM Projects p
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? AND p.Status IN ('Active', 'Planning') AND pm.IsActive = 1
            """, [user_id])
            
            return result.iloc[0]['count'] if not result.empty else 0
        except Exception:
            return 0
    
    def _get_pending_tasks_count(self) -> int:
        """Get count of pending tasks"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT COUNT(*) as count
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? AND t.Status IN ('To Do', 'In Progress') AND pm.IsActive = 1
            """, [user_id])
            
            return result.iloc[0]['count'] if not result.empty else 0
        except Exception:
            return 0
    
    def _calculate_completion_rate(self, metrics: Dict[str, Any]) -> int:
        """Calculate overall completion rate"""
        try:
            total_tasks = metrics['tasks']['total']
            completed_tasks = metrics['tasks']['completed']
            
            if total_tasks > 0:
                return round((completed_tasks / total_tasks) * 100)
            return 0
        except Exception:
            return 0
    
    def _get_project_status_data(self) -> List[Dict[str, Any]]:
        """Get project status distribution data"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT p.Status, COUNT(*) as Count
                FROM Projects p
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                GROUP BY p.Status
                ORDER BY Count DESC
            """, [user_id])
            
            return result.to_dict('records') if not result.empty else []
        except Exception:
            return []
    
    def _get_priority_distribution(self) -> List[Dict[str, Any]]:
        """Get task priority distribution"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT t.Priority, COUNT(*) as Count
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                GROUP BY t.Priority
                ORDER BY 
                    CASE t.Priority
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Medium' THEN 3
                        WHEN 'Low' THEN 4
                    END
            """, [user_id])
            
            return result.to_dict('records') if not result.empty else []
        except Exception:
            return []
    
    def _get_performance_trends_data(self) -> List[Dict[str, Any]]:
        """Get performance trends data for last 30 days"""
        try:
            user_id = self.session_manager.get_user_id()
            
            # Generate last 30 days of data
            dates = pd.date_range(end=datetime.now().date(), periods=30, freq='D')
            
            # Get tasks completed per day
            completed_tasks = self.db_service.execute_query("""
                SELECT CAST(t.CompletedDate AS DATE) as Date, COUNT(*) as Tasks_Completed
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? 
                AND t.CompletedDate >= DATEADD(DAY, -30, GETDATE())
                AND pm.IsActive = 1
                GROUP BY CAST(t.CompletedDate AS DATE)
            """, [user_id])
            
            # Get projects created per day
            new_projects = self.db_service.execute_query("""
                SELECT CAST(p.CreatedDate AS DATE) as Date, COUNT(*) as Projects_Created
                FROM Projects p
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? 
                AND p.CreatedDate >= DATEADD(DAY, -30, GETDATE())
                AND pm.IsActive = 1
                GROUP BY CAST(p.CreatedDate AS DATE)
            """, [user_id])
            
            # Combine data
            trend_data = []
            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                
                # Tasks completed
                tasks_count = 0
                if not completed_tasks.empty:
                    day_tasks = completed_tasks[completed_tasks['Date'] == date.date()]
                    tasks_count = day_tasks['Tasks_Completed'].sum() if not day_tasks.empty else 0
                
                trend_data.append({
                    'Date': date_str,
                    'Value': tasks_count,
                    'Metric': 'Tasks Completed'
                })
                
                # Projects created
                projects_count = 0
                if not new_projects.empty:
                    day_projects = new_projects[new_projects['Date'] == date.date()]
                    projects_count = day_projects['Projects_Created'].sum() if not day_projects.empty else 0
                
                trend_data.append({
                    'Date': date_str,
                    'Value': projects_count,
                    'Metric': 'Projects Created'
                })
            
            return trend_data
        except Exception:
            return []
    
    def _get_team_productivity_data(self) -> List[Dict[str, Any]]:
        """Get team productivity data"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT 
                    COALESCE(u.FirstName + ' ' + u.LastName, u.Username) as Team_Member,
                    COUNT(CASE WHEN t.Status = 'Completed' THEN 1 END) as Tasks_Completed,
                    COUNT(*) as Total_Tasks,
                    SUM(COALESCE(t.ActualHours, 0)) as Total_Hours
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                LEFT JOIN Users u ON t.AssigneeID = u.UserID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                AND t.CreatedDate >= DATEADD(DAY, -30, GETDATE())
                GROUP BY u.UserID, u.FirstName, u.LastName, u.Username
                HAVING COUNT(*) > 0
                ORDER BY Tasks_Completed DESC
            """, [user_id])
            
            return result.to_dict('records') if not result.empty else []
        except Exception:
            return []
    
    def _get_workload_distribution(self) -> List[Dict[str, Any]]:
        """Get workload distribution data"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT 
                    COALESCE(u.FirstName + ' ' + u.LastName, u.Username) as Team_Member,
                    COUNT(*) as Assigned_Tasks,
                    COUNT(CASE WHEN t.Status = 'Completed' THEN 1 END) as Completed_Tasks,
                    SUM(COALESCE(t.EstimatedHours, 0)) as Total_Hours
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                LEFT JOIN Users u ON t.AssigneeID = u.UserID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                GROUP BY u.UserID, u.FirstName, u.LastName, u.Username
                HAVING COUNT(*) > 0
            """, [user_id])
            
            return result.to_dict('records') if not result.empty else []
        except Exception:
            return []
    
    def _get_timeline_data(self) -> List[Dict[str, Any]]:
        """Get timeline data for projects"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT 
                    p.ProjectName as Project_Name,
                    p.StartDate as Start_Date,
                    p.EndDate as End_Date,
                    p.Status,
                    p.Progress
                FROM Projects p
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? AND pm.IsActive = 1
                AND p.StartDate IS NOT NULL AND p.EndDate IS NOT NULL
                ORDER BY p.StartDate
            """, [user_id])
            
            return result.to_dict('records') if not result.empty else []
        except Exception:
            return []
    
    def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Get recent activities"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT TOP 20
                    al.Action,
                    al.Details,
                    al.CreatedDate as created_date,
                    u.Username
                FROM ActivityLogs al
                LEFT JOIN Users u ON al.UserID = u.UserID
                WHERE al.UserID = ? OR al.ProjectID IN (
                    SELECT DISTINCT p.ProjectID 
                    FROM Projects p 
                    INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID 
                    WHERE pm.UserID = ? AND pm.IsActive = 1
                )
                ORDER BY al.CreatedDate DESC
            """, [user_id, user_id])
            
            return result.to_dict('records') if not result.empty else []
        except Exception:
            return []
    
    def _get_upcoming_tasks(self) -> List[Dict[str, Any]]:
        """Get upcoming tasks"""
        try:
            user_id = self.session_manager.get_user_id()
            result = self.db_service.execute_query("""
                SELECT 
                    t.TaskName as task_name,
                    t.Status as status,
                    t.Priority as priority,
                    t.Progress as progress,
                    t.DueDate as due_date,
                    p.ProjectName as project_name
                FROM Tasks t
                INNER JOIN Projects p ON t.ProjectID = p.ProjectID
                INNER JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID
                WHERE pm.UserID = ? 
                AND t.Status IN ('To Do', 'In Progress')
                AND pm.IsActive = 1
                ORDER BY 
                    CASE WHEN t.DueDate IS NULL THEN 1 ELSE 0 END,
                    t.DueDate ASC,
                    CASE t.Priority
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Medium' THEN 3
                        WHEN 'Low' THEN 4
                    END
            """, [user_id])
            
            return result.to_dict('records') if not result.empty else []
        except Exception:
            return []
    
    def _get_user_projects(self) -> List[Dict[str, Any]]:
        """Get user's projects for dropdowns"""
        try:
            user_id = self.session_manager.get_user_id()
            projects = self.db_service.get_projects_for_user(user_id)
            return projects
        except Exception:
            return []
    
    def _get_team_members(self) -> List[str]:
        """Get team members for dropdowns"""
        try:
            team_members = self.db_service.get_all_users()
            return [f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u['username'] 
                   for u in team_members]
        except Exception:
            return []
    
    # Helper methods
    def _format_time_ago(self, timestamp) -> str:
        """Format timestamp as time ago"""
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            now = datetime.now()
            if timestamp.tzinfo:
                now = now.replace(tzinfo=timestamp.tzinfo)
            
            diff = now - timestamp
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                return "Just now"
        except Exception:
            return "Unknown"
    
    def _calculate_days_until_due(self, due_date) -> int:
        """Calculate days until due date"""
        try:
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            today = datetime.now().date()
            return (due_date - today).days
        except Exception:
            return 0
    
    def _get_activity_icon(self, action: str) -> str:
        """Get icon for activity type"""
        icon_map = {
            'Project Created': '📁',
            'Task Created': '✅',
            'Task Completed': '🎉',
            'User Login': '🔐',
            'Comment Added': '💬',
            'File Uploaded': '📎',
            'Default': '📝'
        }
        return icon_map.get(action, icon_map['Default'])
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority level"""
        color_map = {
            'Critical': '#EF4444',
            'High': '#F59E0B',
            'Medium': '#3B82F6',
            'Low': '#10B981'
        }
        return color_map.get(priority, '#6B7280')
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        color_map = {
            'To Do': '#6B7280',
            'In Progress': '#3B82F6',
            'Completed': '#10B981',
            'Cancelled': '#EF4444'
        }
        return color_map.get(status, '#6B7280')
    
    def _create_quick_project(self, project_data: Dict[str, Any]) -> None:
        """Create project from quick action"""
        try:
            if not project_data['project_name']:
                st.error("Project name is required")
                return
            
            user_id = self.session_manager.get_user_id()
            project_id = self.db_service.create_project(project_data, user_id)
            
            if project_id:
                st.success(f"✅ Project '{project_data['project_name']}' created successfully!")
                self.session_manager.add_notification(
                    f"Project '{project_data['project_name']}' created", 
                    'success'
                )
                st.session_state['show_new_project_modal'] = False
                st.experimental_rerun()
            else:
                st.error("Failed to create project")
        except Exception as e:
            st.error(f"Error creating project: {str(e)}")
    
    def _create_quick_task(self, task_data: Dict[str, Any]) -> None:
        """Create task from quick action"""
        try:
            if not task_data['task_name'] or not task_data['project_id']:
                st.error("Task name and project are required")
                return
            
            user_id = self.session_manager.get_user_id()
            
            # Set assignee ID
            if task_data['assignee'] == 'Self':
                task_data['assignee_id'] = user_id
            else:
                # In production, implement proper user lookup
                task_data['assignee_id'] = user_id
            
            task_id = self.db_service.create_task(task_data, user_id)
            
            if task_id:
                st.success(f"✅ Task '{task_data['task_name']}' created successfully!")
                self.session_manager.add_notification(
                    f"Task '{task_data['task_name']}' created", 
                    'success'
                )
                st.session_state['show_new_task_modal'] = False
                st.experimental_rerun()
            else:
                st.error("Failed to create task")
        except Exception as e:
            st.error(f"Error creating task: {str(e)}")
    
    def _render_performance_insights(self, performance_data: List[Dict[str, Any]]) -> None:
        """Render performance insights"""
        st.markdown("#### 💡 Performance Insights")
        
        # Calculate insights from performance data
        if performance_data:
            # Example insights (customize based on your needs)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("📈 **Productivity Trend**\nTask completion rate increased by 15% this week")
            
            with col2:
                st.warning("⚠️ **Attention Needed**\n3 projects are approaching their deadlines")
            
            with col3:
                st.success("🎯 **Goal Achievement**\nMonthly targets are 85% complete")
    
    def _render_timeline_insights(self, timeline_data: List[Dict[str, Any]]) -> None:
        """Render timeline insights"""
        st.markdown("#### 📅 Timeline Insights")
        
        if timeline_data:
            # Calculate timeline metrics
            total_projects = len(timeline_data)
            on_time_projects = len([p for p in timeline_data if p.get('Progress', 0) >= 80])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Projects On Track", on_time_projects, f"out of {total_projects}")
            
            with col2:
                completion_rate = (on_time_projects / total_projects * 100) if total_projects > 0 else 0
                st.metric("Timeline Adherence", f"{completion_rate:.1f}%")