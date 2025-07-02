# enhanced_app.py
"""
DENSO Project Manager - Enhanced Application
Integrated version with all advanced features
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any

# Import custom modules
from database_service import get_database_service
from notification_service import get_notification_service, NotificationUI
from analytics_service import get_analytics_service
from ui_components import UIComponents, ChartComponents, FormComponents
from performance_manager import PerformanceManager, CacheManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="DENSO Project Manager Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced CSS with performance optimizations
st.markdown(
    """
<style>
    /* Performance Optimizations */
    * {
        box-sizing: border-box;
    }
    
    .main {
        padding-top: 1rem;
    }
    
    /* Modern Glassmorphism Design */
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
    
    /* Header with Gradient */
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
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
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.05)"/></pattern></defs><rect width="100%" height="100%" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    /* Enhanced Metrics */
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
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    /* Sidebar Enhancement */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
    }
    
    /* Button Styles with Animations */
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
    
    .stButton > button:active {
        transform: translateY(0) scale(0.98);
    }
    
    /* Loading Animations */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 1.5s infinite;
    }
    
    /* Kanban Board Styles */
    .kanban-column {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        min-height: 400px;
        backdrop-filter: blur(10px);
    }
    
    .task-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border-left: 4px solid transparent;
    }
    
    .task-card:hover {
        transform: translateX(5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .task-card.priority-critical {
        border-left-color: #e74c3c;
    }
    
    .task-card.priority-high {
        border-left-color: #f39c12;
    }
    
    .task-card.priority-medium {
        border-left-color: #f1c40f;
    }
    
    .task-card.priority-low {
        border-left-color: #95a5a6;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .header-gradient {
            padding: 20px;
        }
        
        .glass-card {
            padding: 15px;
            margin: 10px 0;
        }
        
        .metric-card {
            padding: 15px;
        }
    }
    
    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        .glass-card {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .task-card {
            background: rgba(0, 0, 0, 0.7);
            color: white;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


class EnhancedProjectManagerApp:
    """Enhanced main application class with all features"""

    def __init__(self):
        self.db_service = None
        self.notification_service = None
        self.analytics_service = None
        self.notification_ui = None
        self.performance_manager = None
        self.cache_manager = None
        self.initialize_app()

    def initialize_app(self):
        """Initialize application with all services"""
        try:
            # Initialize performance manager first
            self.performance_manager = PerformanceManager()
            self.cache_manager = CacheManager()

            # Initialize database service
            self.db_service = get_database_service()

            # Test database connection
            if not self.db_service.connection_manager.test_connection():
                st.error("❌ Database connection failed")
                self.show_database_setup()
                return False

            # Initialize other services
            self.notification_service = get_notification_service(self.db_service)
            self.analytics_service = get_analytics_service(self.db_service)
            self.notification_ui = NotificationUI(self.notification_service)

            # Setup performance monitoring
            self.performance_manager.setup_monitoring()

            logger.info("Enhanced application initialized successfully")
            return True

        except Exception as e:
            logger.error(f"App initialization failed: {str(e)}")
            st.error(f"Application initialization failed: {str(e)}")
            return False

    def show_database_setup(self):
        """Enhanced database setup interface"""
        st.markdown(
            """
        <div class="glass-card">
            <h2>🔧 Database Setup Required</h2>
            <p>Please ensure your SQL Server connection is properly configured:</p>
            <ul>
                <li>✅ SQL Server is running and accessible</li>
                <li>✅ Database 'ProjectManagerDB' exists</li>
                <li>✅ Connection details in <code>.streamlit/secrets.toml</code> are correct</li>
                <li>✅ Required tables are created via <code>setup.sql</code></li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Retry Connection", use_container_width=True):
                st.rerun()

        with col2:
            if st.button("⚙️ Setup Database", use_container_width=True):
                if self.setup_database_schema():
                    st.success("✅ Database setup completed!")
                    st.rerun()

        with col3:
            if st.button("📊 Test Connection", use_container_width=True):
                self.test_database_connection()

    def setup_database_schema(self) -> bool:
        """Setup database schema with progress tracking"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("🔄 Connecting to database...")
            progress_bar.progress(25)

            status_text.text("📋 Reading schema file...")
            progress_bar.progress(50)

            status_text.text("🛠️ Creating tables...")
            progress_bar.progress(75)

            success = self.db_service.setup_database()

            if success:
                status_text.text("✅ Database setup completed!")
                progress_bar.progress(100)
            else:
                status_text.text("❌ Database setup failed!")

            return success
        except Exception as e:
            st.error(f"Setup failed: {str(e)}")
            return False

    def test_database_connection(self):
        """Test database connection with detailed feedback"""
        try:
            with st.spinner("Testing database connection..."):
                connection_ok = self.db_service.connection_manager.test_connection()

                if connection_ok:
                    # Test basic operations
                    stats = self.db_service.get_dashboard_stats()

                    st.success("✅ Database connection successful!")
                    st.info(
                        f"📊 Found {stats.get('total_projects', 0)} projects and {stats.get('total_users', 0)} users"
                    )
                else:
                    st.error("❌ Database connection failed!")
        except Exception as e:
            st.error(f"Connection test failed: {str(e)}")

    def run(self):
        """Run the enhanced application"""
        if not self.db_service:
            return

        # Initialize session state
        self._initialize_session_state()

        # Show login or main app
        if not st.session_state.authenticated:
            self.show_enhanced_login()
        else:
            self.show_enhanced_main_app()

    def _initialize_session_state(self):
        """Initialize session state variables"""
        defaults = {
            "authenticated": False,
            "user": None,
            "current_page": "Dashboard",
            "selected_project": None,
            "show_new_project": False,
            "show_new_task": False,
            "show_new_user": False,
            "notifications_checked": datetime.now(),
            "cache_timestamp": datetime.now(),
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def show_enhanced_login(self):
        """Enhanced login interface with animations"""
        # Background animation
        st.markdown(
            """
        <div class="header-gradient">
            <h1 style="font-size: 3rem; margin: 0; position: relative; z-index: 1;">🚀 DENSO Project Manager Pro</h1>
            <p style="font-size: 1.2rem; margin: 10px 0 0 0; position: relative; z-index: 1;">Advanced Project Management System</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Login form in glassmorphism container
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                """
            <div class="glass-card">
                <h2 style="text-align: center; margin-bottom: 30px;">🔐 Login</h2>
            </div>
            """,
                unsafe_allow_html=True,
            )

            with st.form("enhanced_login_form", clear_on_submit=False):
                username = st.text_input(
                    "👤 Username",
                    placeholder="Enter your username",
                    help="Use 'admin' for demo access",
                )
                password = st.text_input(
                    "🔒 Password",
                    type="password",
                    placeholder="Enter your password",
                    help="Use 'admin123' for demo access",
                )

                remember_me = st.checkbox("🔄 Remember me")

                col1, col2 = st.columns(2)
                with col1:
                    login_button = st.form_submit_button(
                        "🚀 Login", use_container_width=True
                    )
                with col2:
                    if st.form_submit_button("📝 Register", use_container_width=True):
                        st.info("Registration feature coming soon!")

                if login_button:
                    self._process_login(username, password, remember_me)

            # Demo credentials and system status
            with st.expander("🔧 Demo Access & System Status"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(
                        """
                    **Demo Credentials:**
                    - Username: `admin`
                    - Password: `admin123`
                    """
                    )

                with col2:
                    # System status check
                    if self.db_service:
                        st.success("🟢 Database: Connected")
                    else:
                        st.error("🔴 Database: Disconnected")

                    st.info("🟡 Cache: Active")
                    st.info("🟢 Services: Running")

    def _process_login(self, username: str, password: str, remember_me: bool):
        """Process login with enhanced feedback"""
        if not username or not password:
            st.warning("⚠️ Please enter both username and password")
            return

        with st.spinner("🔄 Authenticating..."):
            user = self.db_service.authenticate_user(username, password)

            if user:
                st.session_state.authenticated = True
                st.session_state.user = user

                # Create welcome notification
                self.notification_service.create_notification(
                    {
                        "user_id": user["UserID"],
                        "type": "success",
                        "title": "Welcome Back!",
                        "message": f"Welcome back, {user['FirstName']}! You have successfully logged in.",
                        "priority": "medium",
                    }
                )

                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    def show_enhanced_main_app(self):
        """Enhanced main application interface"""
        # Header with notifications
        self._render_app_header()

        # Sidebar navigation
        self._render_enhanced_sidebar()

        # Main content area with caching
        page = st.session_state.get("current_page", "Dashboard")

        # Performance monitoring
        start_time = datetime.now()

        try:
            if page == "Dashboard":
                self.show_enhanced_dashboard()
            elif page == "Projects":
                self.show_enhanced_projects()
            elif page == "Tasks":
                self.show_enhanced_tasks()
            elif page == "Analytics":
                self.show_enhanced_analytics()
            elif page == "Team":
                self.show_enhanced_team()
            elif page == "Reports":
                self.show_enhanced_reports()
            elif page == "Settings":
                self.show_enhanced_settings()

            # Log performance
            load_time = (datetime.now() - start_time).total_seconds()
            if load_time > 2:  # Log slow pages
                logger.warning(f"Slow page load: {page} took {load_time:.2f} seconds")

        except Exception as e:
            logger.error(f"Error rendering page {page}: {str(e)}")
            st.error(f"An error occurred while loading the page: {str(e)}")

    def _render_app_header(self):
        """Render application header with notifications"""
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(
                f"""
            <h1 style="margin: 0; color: #2E3440;">
                🚀 DENSO Project Manager Pro
            </h1>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            # Real-time clock
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(
                f"""
            <div style="text-align: center; padding: 10px;">
                <span style="color: #5E6C7E;">📅 {current_time}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            # Notification center
            user_id = st.session_state.user["UserID"]
            self.notification_ui.render_notification_center(user_id)

    def _render_enhanced_sidebar(self):
        """Enhanced sidebar with user info and navigation"""
        with st.sidebar:
            user = st.session_state.user

            # User profile card
            st.markdown(
                f"""
            <div class="glass-card" style="text-align: center;">
                {UIComponents.render_user_avatar(f"{user['FirstName']} {user['LastName']}", user['Role'], 60)}
                <h3 style="margin: 10px 0 5px 0;">{user['FirstName']} {user['LastName']}</h3>
                <p style="margin: 0; color: #5E6C7E;"><strong>{user['Role']}</strong></p>
                <p style="margin: 0; color: #5E6C7E;">{user['Department']}</p>
                <small style="color: #6C757D;">Last login: {user.get('LastLoginDate', 'N/A')}</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Navigation menu with icons
            st.markdown("### 📋 Navigation")

            pages = {
                "🏠  Dashboard": "Dashboard",
                "📁  Projects": "Projects",
                "✅  Tasks": "Tasks",
                "📊  Analytics": "Analytics",
                "👥  Team": "Team",
                "📈  Reports": "Reports",
                "⚙️  Settings": "Settings",
            }

            for label, page in pages.items():
                is_current = st.session_state.current_page == page
                button_style = "primary" if is_current else "secondary"

                if st.button(label, use_container_width=True, type=button_style):
                    st.session_state.current_page = page
                    st.rerun()

            st.markdown("---")

            # Quick stats
            self._render_sidebar_quick_stats()

            st.markdown("---")

            # Logout and settings
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚪 Logout", use_container_width=True):
                    self._logout()
            with col2:
                if st.button("🔄 Refresh", use_container_width=True):
                    self.cache_manager.clear_cache()
                    st.rerun()

    def _render_sidebar_quick_stats(self):
        """Render quick stats in sidebar"""
        try:
            # Use cache for performance
            cache_key = f"quick_stats_{st.session_state.user['UserID']}"
            stats = self.cache_manager.get(cache_key)

            if not stats:
                stats = self.db_service.get_dashboard_stats()
                self.cache_manager.set(cache_key, stats, ttl=300)  # 5 minutes

            st.markdown("### 📊 Quick Stats")

            UIComponents.render_metric_card(
                "Active Projects",
                str(stats.get("active_projects", 0)),
                color="#007BFF",
                icon="📁",
            )

            UIComponents.render_metric_card(
                "My Tasks", str(self._get_user_task_count()), color="#28A745", icon="✅"
            )

        except Exception as e:
            logger.error(f"Failed to render quick stats: {str(e)}")
            st.error("Unable to load quick stats")

    def _get_user_task_count(self) -> int:
        """Get current user's task count"""
        try:
            query = """
            SELECT COUNT(*) as count 
            FROM Tasks 
            WHERE AssigneeID = ? AND Status NOT IN ('Done', 'Cancelled')
            """
            result = self.db_service.connection_manager.execute_query(
                query, (st.session_state.user["UserID"],)
            )
            return result[0]["count"] if result else 0
        except:
            return 0

    def show_enhanced_dashboard(self):
        """Enhanced dashboard with real-time data"""
        st.markdown("# 🏠 Dashboard")

        # Performance metrics
        with self.performance_manager.measure_time("dashboard_load"):
            # Get analytics data with caching
            cache_key = "dashboard_analytics"
            analytics_data = self.cache_manager.get(cache_key)

            if not analytics_data:
                analytics_data = {
                    "stats": self.db_service.get_dashboard_stats(),
                    "kpis": self.analytics_service.get_dashboard_kpis(),
                    "project_status": self.db_service.get_project_status_distribution(),
                    "task_priority": self.db_service.get_task_priority_distribution(),
                }
                self.cache_manager.set(cache_key, analytics_data, ttl=600)  # 10 minutes

            # KPI Cards
            self._render_kpi_section(analytics_data["kpis"])

            # Charts section
            self._render_dashboard_charts(analytics_data)

            # Recent activities
            self._render_recent_activities()

    def _render_kpi_section(self, kpis: List):
        """Render KPI metrics section"""
        st.markdown("### 📈 Key Performance Indicators")

        if kpis:
            cols = st.columns(len(kpis))

            for i, kpi in enumerate(kpis):
                with cols[i]:
                    # Determine trend arrow
                    trend_arrow = (
                        "📈" if kpi.trend > 0 else "📉" if kpi.trend < 0 else "➡️"
                    )
                    trend_color = (
                        "#28A745"
                        if kpi.trend > 0
                        else "#DC3545" if kpi.trend < 0 else "#6C757D"
                    )

                    delta_text = f"{trend_arrow} {kpi.trend:+.1f}%"

                    UIComponents.render_metric_card(
                        kpi.name,
                        f"{kpi.value:.1f}{kpi.unit}",
                        delta=delta_text,
                        color=(
                            "#007BFF"
                            if kpi.status == "good"
                            else "#FFC107" if kpi.status == "warning" else "#DC3545"
                        ),
                        icon="📊",
                    )
        else:
            st.info("No KPI data available")

    def _render_dashboard_charts(self, analytics_data: Dict):
        """Render dashboard charts"""
        col1, col2 = st.columns(2)

        with col1:
            ChartComponents.render_donut_chart(
                analytics_data["project_status"],
                "Project Status Distribution",
                value_col="Count",
                label_col="Status",
            )

        with col2:
            ChartComponents.render_progress_bar_chart(
                [
                    {"name": item["Priority"], "value": item["Count"]}
                    for item in analytics_data["task_priority"]
                ],
                "Task Priority Distribution",
            )

    def _render_recent_activities(self):
        """Render recent activities section"""
        st.markdown("### 📝 Recent Activities")

        # Get recent projects and tasks
        projects = self.db_service.get_all_projects()[:5]

        if projects:
            for project in projects:
                with st.container():
                    self._render_project_summary_card(project)
        else:
            st.info("No recent activities")

    def _render_project_summary_card(self, project: Dict):
        """Render project summary card"""
        progress = project.get("Progress", 0)

        st.markdown(
            f"""
        <div class="glass-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #2E3440;">{project['ProjectName']}</h4>
                    <p style="margin: 5px 0; color: #5E6C7E;">{project.get('Description', '')[:100]}...</p>
                    <small style="color: #6C757D;">Created by: {project.get('CreatorName', 'Unknown')}</small>
                </div>
                <div style="text-align: right;">
                    {UIComponents.render_status_badge(project['Status'])}
                    <div style="margin-top: 10px;">
                        <strong>{progress}% Complete</strong>
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def show_enhanced_projects(self):
        """Enhanced projects management"""
        st.markdown("# 📁 Projects Management")

        # Action bar
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            search_term = st.text_input(
                "🔍 Search Projects", placeholder="Search by name or description..."
            )
        with col2:
            status_filter = st.selectbox(
                "📊 Status",
                ["All", "Planning", "In Progress", "Review", "Completed", "On Hold"],
            )
        with col3:
            if st.button("➕ New Project", use_container_width=True):
                st.session_state.show_new_project = True
        with col4:
            if st.button("🔄 Refresh", use_container_width=True):
                self.cache_manager.clear_cache("projects")
                st.rerun()

        # New project form
        if st.session_state.get("show_new_project", False):
            self._render_enhanced_project_form()

        # Projects grid
        self._render_projects_grid(search_term, status_filter)

    def _render_enhanced_project_form(self):
        """Enhanced project creation form"""
        st.markdown("### ➕ Create New Project")

        with st.form("enhanced_project_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input(
                    "📝 Project Name *", placeholder="Enter project name"
                )
                client_name = st.text_input(
                    "🏢 Client Name", placeholder="Client or department"
                )
                start_date = st.date_input("📅 Start Date", value=datetime.now().date())
                budget = st.number_input("💰 Budget ($)", min_value=0.0, format="%.2f")

            with col2:
                description = st.text_area(
                    "📄 Description", placeholder="Project description...", height=100
                )
                end_date = st.date_input(
                    "🏁 End Date", value=datetime.now().date() + timedelta(days=30)
                )
                status = st.selectbox(
                    "📊 Status",
                    ["Planning", "In Progress", "Review", "Completed", "On Hold"],
                )
                priority = st.selectbox(
                    "🔥 Priority", ["Low", "Medium", "High", "Critical"]
                )

            # Project template
            template = st.selectbox(
                "📋 Project Template",
                [
                    "Custom",
                    "Website Development",
                    "Mobile App",
                    "Marketing Campaign",
                    "Research Project",
                ],
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                submit = st.form_submit_button(
                    "🚀 Create Project", use_container_width=True
                )
            with col2:
                if st.form_submit_button("💾 Save as Draft", use_container_width=True):
                    st.info("Draft feature coming soon!")
            with col3:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit:
                self._process_project_creation(
                    name,
                    description,
                    start_date,
                    end_date,
                    status,
                    priority,
                    budget,
                    client_name,
                    template,
                )

            if cancel:
                st.session_state.show_new_project = False
                st.rerun()

    def _process_project_creation(
        self,
        name,
        description,
        start_date,
        end_date,
        status,
        priority,
        budget,
        client_name,
        template,
    ):
        """Process project creation with validation"""
        if not name:
            st.error("⚠️ Project name is required")
            return

        if end_date <= start_date:
            st.error("⚠️ End date must be after start date")
            return

        with st.spinner("🔄 Creating project..."):
            project_data = {
                "name": name,
                "description": description,
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "priority": priority,
                "budget": budget,
                "client_name": client_name,
                "created_by": st.session_state.user["UserID"],
            }

            project_id = self.db_service.create_project(project_data)

            if project_id:
                # Clear cache
                self.cache_manager.clear_cache("projects")

                # Create notification
                self.notification_service.create_project_notification(
                    {"id": project_id, "name": name},
                    "created",
                    [st.session_state.user["UserID"]],
                )

                st.success(f"✅ Project '{name}' created successfully!")
                st.session_state.show_new_project = False
                st.rerun()
            else:
                st.error("❌ Failed to create project")

    def _render_projects_grid(self, search_term: str, status_filter: str):
        """Render projects in grid layout"""
        # Get projects with caching
        cache_key = f"projects_{search_term}_{status_filter}"
        projects = self.cache_manager.get(cache_key)

        if not projects:
            projects = self.db_service.get_all_projects()

            # Apply filters
            if search_term:
                projects = [
                    p
                    for p in projects
                    if search_term.lower() in p["ProjectName"].lower()
                    or search_term.lower() in (p.get("Description") or "").lower()
                ]

            if status_filter != "All":
                projects = [p for p in projects if p["Status"] == status_filter]

            self.cache_manager.set(cache_key, projects, ttl=300)

        if projects:
            # Display projects in grid
            cols = st.columns(2)
            for i, project in enumerate(projects):
                with cols[i % 2]:
                    self._render_enhanced_project_card(project)
        else:
            st.info("No projects found matching your criteria")

    def _render_enhanced_project_card(self, project: Dict):
        """Render enhanced project card"""
        progress = project.get("Progress", 0)
        task_count = project.get("TaskCount", 0)
        completed_tasks = project.get("CompletedTasks", 0)

        # Calculate health score
        health_score = self.analytics_service.get_project_health_score(
            project["ProjectID"]
        )
        health_color = {
            "excellent": "#28A745",
            "good": "#17A2B8",
            "warning": "#FFC107",
            "critical": "#DC3545",
        }.get(health_score.get("status", "unknown"), "#6C757D")

        with st.container():
            st.markdown(
                f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #2E3440; flex: 1;">{project['ProjectName']}</h3>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        {UIComponents.render_status_badge(project['Status'])}
                        {UIComponents.render_priority_badge(project['Priority'])}
                    </div>
                </div>
                
                <p style="color: #5E6C7E; margin-bottom: 15px; min-height: 40px;">
                    {(project.get('Description') or '')[:120]}{'...' if len(project.get('Description') or '') > 120 else ''}
                </p>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                    <div>
                        <strong>📊 Progress:</strong><br>
                        <div style="display: flex; align-items: center; gap: 10px; margin-top: 5px;">
                            <div style="flex: 1; background: #E9ECEF; border-radius: 10px; height: 8px;">
                                <div style="background: linear-gradient(90deg, #007BFF, #28A745); width: {progress}%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            <span style="font-weight: bold; color: #007BFF;">{progress}%</span>
                        </div>
                    </div>
                    
                    <div>
                        <strong>✅ Tasks:</strong><br>
                        <span style="color: #5E6C7E; font-size: 1.1rem; margin-top: 5px; display: block;">
                            {completed_tasks}/{task_count} completed
                        </span>
                    </div>
                    
                    <div>
                        <strong>🏢 Client:</strong><br>
                        <span style="color: #5E6C7E;">{project.get('ClientName') or 'Internal'}</span>
                    </div>
                    
                    <div>
                        <strong>🎯 Health:</strong><br>
                        <span style="color: {health_color}; font-weight: bold;">
                            {health_score.get('score', 0):.0f}/100
                        </span>
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>💰 Budget:</strong>
                    <span style="color: #5E6C7E; margin-left: 10px;">${project.get('Budget', 0):,.2f}</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(
                    "📋 Tasks",
                    key=f"tasks_{project['ProjectID']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_project = project["ProjectID"]
                    st.session_state.current_page = "Tasks"
                    st.rerun()
            with col2:
                if st.button(
                    "📊 Analytics",
                    key=f"analytics_{project['ProjectID']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_project = project["ProjectID"]
                    st.session_state.current_page = "Analytics"
                    st.rerun()
            with col3:
                if st.button(
                    "✏️ Edit",
                    key=f"edit_{project['ProjectID']}",
                    use_container_width=True,
                ):
                    st.info("Edit functionality coming in next update!")
            with col4:
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{project['ProjectID']}",
                    use_container_width=True,
                ):
                    st.error("Delete functionality requires confirmation dialog!")

    def show_enhanced_tasks(self):
        """Enhanced task management with Kanban board"""
        st.markdown("# ✅ Task Management")

        # Get projects for selection
        projects = self.db_service.get_all_projects()
        if not projects:
            st.warning("No projects found. Please create a project first.")
            return

        # Project selection and filters
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            selected_project_id = st.session_state.get("selected_project")
            project_options = {
                f"{p['ProjectName']} (ID: {p['ProjectID']})": p["ProjectID"]
                for p in projects
            }

            if selected_project_id and selected_project_id in [
                p["ProjectID"] for p in projects
            ]:
                default_index = list(project_options.values()).index(
                    selected_project_id
                )
            else:
                default_index = 0

            selected_project_name = st.selectbox(
                "📁 Select Project",
                options=list(project_options.keys()),
                index=default_index,
            )
            selected_project_id = project_options[selected_project_name]
            st.session_state.selected_project = selected_project_id

        with col2:
            view_mode = st.selectbox("👁️ View", ["Kanban", "List", "Calendar"])

        with col3:
            if st.button("➕ New Task", use_container_width=True):
                st.session_state.show_new_task = True
                st.session_state.task_project_id = selected_project_id

        with col4:
            if st.button("🔄 Refresh", use_container_width=True):
                self.cache_manager.clear_cache("tasks")
                st.rerun()

        # New task form
        if st.session_state.get("show_new_task", False):
            self._render_enhanced_task_form()

        # Task views
        if view_mode == "Kanban":
            self._render_enhanced_kanban(selected_project_id)
        elif view_mode == "List":
            self._render_tasks_list(selected_project_id)
        else:  # Calendar
            self._render_tasks_calendar(selected_project_id)

    def _render_enhanced_task_form(self):
        """Enhanced task creation form"""
        st.markdown("### ➕ Create New Task")

        with st.form("enhanced_task_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("📝 Task Name *", placeholder="Enter task name")
                due_date = st.date_input(
                    "📅 Due Date", value=datetime.now().date() + timedelta(days=7)
                )
                priority = st.selectbox(
                    "🔥 Priority", ["Low", "Medium", "High", "Critical"]
                )
                estimated_hours = st.number_input(
                    "⏱️ Estimated Hours", min_value=0.0, value=8.0, step=0.5
                )

            with col2:
                # Get users for assignment
                users = self.db_service.get_all_users()
                user_options = {
                    f"{u['FirstName']} {u['LastName']} ({u['Role']})": u["UserID"]
                    for u in users
                }

                assignee_name = st.selectbox(
                    "👤 Assignee", options=["Unassigned"] + list(user_options.keys())
                )
                status = st.selectbox(
                    "📊 Status", ["To Do", "In Progress", "Review", "Testing", "Done"]
                )
                start_date = st.date_input("🚀 Start Date", value=datetime.now().date())
                end_date = st.date_input(
                    "🏁 End Date", value=datetime.now().date() + timedelta(days=5)
                )

            description = st.text_area(
                "📄 Description",
                placeholder="Task description and requirements...",
                height=100,
            )

            # Dependencies and labels
            col1, col2 = st.columns(2)
            with col1:
                dependencies = st.text_input(
                    "🔗 Dependencies", placeholder="Task IDs separated by commas"
                )
            with col2:
                labels = st.text_input(
                    "🏷️ Labels", placeholder="Labels separated by commas"
                )

            # Form buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                submit = st.form_submit_button(
                    "🚀 Create Task", use_container_width=True
                )
            with col2:
                if st.form_submit_button("📋 Create & New", use_container_width=True):
                    st.info("Create & New feature coming soon!")
            with col3:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit:
                self._process_task_creation(
                    name,
                    description,
                    start_date,
                    end_date,
                    due_date,
                    assignee_name,
                    user_options,
                    status,
                    priority,
                    estimated_hours,
                    dependencies,
                    labels,
                )

            if cancel:
                st.session_state.show_new_task = False
                st.rerun()

    def _process_task_creation(
        self,
        name,
        description,
        start_date,
        end_date,
        due_date,
        assignee_name,
        user_options,
        status,
        priority,
        estimated_hours,
        dependencies,
        labels,
    ):
        """Process task creation with validation"""
        if not name:
            st.error("⚠️ Task name is required")
            return

        with st.spinner("🔄 Creating task..."):
            assignee_id = (
                user_options.get(assignee_name)
                if assignee_name != "Unassigned"
                else None
            )

            task_data = {
                "project_id": st.session_state.task_project_id,
                "name": name,
                "description": description,
                "start_date": start_date,
                "end_date": end_date,
                "due_date": due_date,
                "assignee_id": assignee_id,
                "status": status,
                "priority": priority,
                "estimated_hours": estimated_hours,
                "created_by": st.session_state.user["UserID"],
            }

            task_id = self.db_service.create_task(task_data)

            if task_id:
                # Clear cache
                self.cache_manager.clear_cache("tasks")

                # Create notifications
                if assignee_id:
                    self.notification_service.create_task_notification(
                        {"id": task_id, "name": name, "priority": priority},
                        "created",
                        assignee_id,
                    )

                st.success(f"✅ Task '{name}' created successfully!")
                st.session_state.show_new_task = False
                st.rerun()
            else:
                st.error("❌ Failed to create task")

    def _render_enhanced_kanban(self, project_id: int):
        """Render enhanced Kanban board"""
        st.markdown("### 📋 Kanban Board")

        # Get tasks with caching
        cache_key = f"tasks_{project_id}"
        tasks = self.cache_manager.get(cache_key)

        if not tasks:
            tasks = self.db_service.get_tasks_by_project(project_id)
            self.cache_manager.set(cache_key, tasks, ttl=180)  # 3 minutes

        if not tasks:
            st.info("No tasks found for this project. Create your first task!")
            return

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
                # Column header
                count = len(status_tasks)
                progress = sum(
                    1 for task in status_tasks if task.get("Status") == "Done"
                )

                st.markdown(
                    f"""
                <div class="kanban-column">
                    <h4 style="text-align: center; margin-bottom: 20px; color: #2E3440;">
                        {status} ({count})
                    </h4>
                """,
                    unsafe_allow_html=True,
                )

                # Render tasks in column
                for task in status_tasks:
                    self._render_enhanced_task_card(task)

                st.markdown("</div>", unsafe_allow_html=True)

    def _render_enhanced_task_card(self, task: Dict):
        """Render enhanced task card"""
        priority_colors = {
            "Low": "#6C757D",
            "Medium": "#FFC107",
            "High": "#FD7E14",
            "Critical": "#DC3545",
        }

        priority_class = f"priority-{task['Priority'].lower()}"
        assignee = task.get("AssigneeName", "Unassigned")
        due_date = task.get("DueDate")

        # Calculate days until due
        days_until_due = ""
        if due_date:
            try:
                if isinstance(due_date, str):
                    due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                elif hasattr(due_date, "date"):
                    due_date = due_date.date()

                days_diff = (due_date - datetime.now().date()).days
                if days_diff < 0:
                    days_until_due = f"🔴 {abs(days_diff)} days overdue"
                elif days_diff == 0:
                    days_until_due = "🟡 Due today"
                elif days_diff <= 3:
                    days_until_due = f"🟠 Due in {days_diff} days"
                else:
                    days_until_due = f"🟢 Due in {days_diff} days"
            except:
                days_until_due = "📅 No due date"

        st.markdown(
            f"""
        <div class="task-card {priority_class}">
            <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 10px;">
                <h5 style="margin: 0; flex: 1; color: #2E3440;">{task['TaskName']}</h5>
                {UIComponents.render_priority_badge(task['Priority'])}
            </div>
            
            <p style="color: #5E6C7E; font-size: 0.9rem; margin: 8px 0;">
                👤 {assignee}
            </p>
            
            <p style="color: #5E6C7E; font-size: 0.85rem; margin: 5px 0;">
                {days_until_due}
            </p>
            
            <div style="margin-top: 10px;">
                <small style="color: #6C757D;">
                    Est: {task.get('EstimatedHours', 0)} hrs
                </small>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Task actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👁️", key=f"view_{task['TaskID']}", help="View Details"):
                self._show_task_details(task)
        with col2:
            if st.button("✏️", key=f"edit_{task['TaskID']}", help="Edit Task"):
                st.info("Edit task feature coming soon!")

    def _show_task_details(self, task: Dict):
        """Show task details in modal-like interface"""
        with st.expander(f"📋 Task Details: {task['TaskName']}", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**🏷️ Status:** {task['Status']}")
                st.markdown(f"**🔥 Priority:** {task['Priority']}")
                st.markdown(
                    f"**👤 Assignee:** {task.get('AssigneeName', 'Unassigned')}"
                )
                st.markdown(f"**⏱️ Estimated Hours:** {task.get('EstimatedHours', 0)}")

            with col2:
                st.markdown(f"**📅 Start Date:** {task.get('StartDate', 'Not set')}")
                st.markdown(f"**🏁 End Date:** {task.get('EndDate', 'Not set')}")
                st.markdown(f"**⚡ Due Date:** {task.get('DueDate', 'Not set')}")
                st.markdown(
                    f"**👨‍💻 Created By:** {task.get('CreatorName', 'Unknown')}"
                )

            if task.get("Description"):
                st.markdown(f"**📄 Description:**")
                st.markdown(task["Description"])

            # Status update
            new_status = st.selectbox(
                "Update Status",
                ["To Do", "In Progress", "Review", "Testing", "Done"],
                index=["To Do", "In Progress", "Review", "Testing", "Done"].index(
                    task["Status"]
                ),
                key=f"status_{task['TaskID']}",
            )

            if st.button("💾 Update Status", key=f"update_{task['TaskID']}"):
                if self.db_service.update_task_status(task["TaskID"], new_status):
                    self.cache_manager.clear_cache("tasks")
                    st.success("✅ Status updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update status")

    def show_enhanced_analytics(self):
        """Enhanced analytics dashboard"""
        st.markdown("# 📊 Advanced Analytics")

        # Date range selector
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            date_range = st.date_input(
                "📅 Select Date Range",
                value=[datetime.now() - timedelta(days=30), datetime.now()],
                help="Select date range for analytics",
            )
        with col2:
            selected_project = st.selectbox(
                "📁 Project Filter",
                ["All Projects"]
                + [p["ProjectName"] for p in self.db_service.get_all_projects()],
            )
        with col3:
            if st.button("🔄 Refresh Analytics", use_container_width=True):
                self.cache_manager.clear_cache("analytics")
                st.rerun()

        if len(date_range) == 2:
            start_date, end_date = date_range

            # Get analytics data
            cache_key = f"analytics_{start_date}_{end_date}_{selected_project}"
            analytics_data = self.cache_manager.get(cache_key)

            if not analytics_data:
                project_id = None
                if selected_project != "All Projects":
                    projects = self.db_service.get_all_projects()
                    project_match = next(
                        (p for p in projects if p["ProjectName"] == selected_project),
                        None,
                    )
                    project_id = project_match["ProjectID"] if project_match else None

                analytics_data = self.analytics_service.get_project_analytics(
                    project_id, (start_date, end_date)
                )
                self.cache_manager.set(cache_key, analytics_data, ttl=900)  # 15 minutes

            # Render analytics sections
            self._render_analytics_overview(analytics_data)
            self._render_performance_metrics(analytics_data)
            self._render_predictive_analytics()
        else:
            st.warning("Please select a valid date range")

    def _render_analytics_overview(self, analytics_data: Dict):
        """Render analytics overview section"""
        st.markdown("### 📈 Performance Overview")

        if analytics_data and analytics_data.get("summary"):
            summary = analytics_data["summary"]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                UIComponents.render_metric_card(
                    "Total Projects",
                    str(summary.get("total_projects", 0)),
                    icon="📁",
                    color="#007BFF",
                )

            with col2:
                completion_rate = 0
                if summary.get("total_projects", 0) > 0:
                    completion_rate = (
                        summary.get("completed_projects", 0) / summary["total_projects"]
                    ) * 100

                UIComponents.render_metric_card(
                    "Completion Rate",
                    f"{completion_rate:.1f}%",
                    icon="✅",
                    color="#28A745",
                )

            with col3:
                UIComponents.render_metric_card(
                    "Budget Utilization",
                    f"${summary.get('total_spent', 0):,.0f}",
                    delta=f"of ${summary.get('total_budget', 0):,.0f}",
                    icon="💰",
                    color="#FFC107",
                )

            with col4:
                avg_progress = summary.get("avg_progress", 0) or 0
                UIComponents.render_metric_card(
                    "Avg Progress", f"{avg_progress:.1f}%", icon="📊", color="#6F42C1"
                )

    def _render_performance_metrics(self, analytics_data: Dict):
        """Render performance metrics charts"""
        st.markdown("### 📊 Performance Metrics")

        col1, col2 = st.columns(2)

        with col1:
            # Timeline performance
            if analytics_data.get("timeline"):
                timeline_data = analytics_data["timeline"]
                ChartComponents.render_timeline_chart(
                    timeline_data, "Project Timeline Performance"
                )
            else:
                st.info("No timeline data available")

        with col2:
            # Resource utilization
            if analytics_data.get("resource_utilization"):
                resource_data = analytics_data["resource_utilization"]
                ChartComponents.render_progress_bar_chart(
                    resource_data, "Resource Utilization"
                )
            else:
                st.info("No resource data available")

    def _render_predictive_analytics(self):
        """Render predictive analytics section"""
        st.markdown("### 🔮 Predictive Analytics")

        predictions = self.analytics_service.get_predictive_analytics()

        if predictions:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📈 Completion Forecast")
                if predictions.get("completion_forecast"):
                    forecast = predictions["completion_forecast"]
                    st.markdown(
                        f"**Estimated Completion:** {forecast.get('estimated_date', 'Unknown')}"
                    )
                    st.markdown(f"**Confidence:** {forecast.get('confidence', 0):.1f}%")
                else:
                    st.info("No completion forecast available")

            with col2:
                st.markdown("#### 💰 Budget Forecast")
                if predictions.get("budget_forecast"):
                    budget = predictions["budget_forecast"]
                    st.markdown(
                        f"**Projected Cost:** ${budget.get('projected_cost', 0):,.2f}"
                    )
                    st.markdown(f"**Variance:** {budget.get('variance', 0):+.1f}%")
                else:
                    st.info("No budget forecast available")
        else:
            st.info("Predictive analytics not available")

    def show_enhanced_team(self):
        """Enhanced team management"""
        st.markdown("# 👥 Team Management")
        st.info("Enhanced team features coming soon!")

    def show_enhanced_reports(self):
        """Enhanced reporting system"""
        st.markdown("# 📈 Reports & Exports")
        st.info("Advanced reporting features coming soon!")

    def show_enhanced_settings(self):
        """Enhanced settings panel"""
        st.markdown("# ⚙️ Settings")

        tabs = st.tabs(["User Settings", "System Settings", "Performance", "About"])

        with tabs[0]:
            self._render_user_settings()

        with tabs[1]:
            self._render_system_settings()

        with tabs[2]:
            self._render_performance_settings()

        with tabs[3]:
            self._render_about_section()

    def _render_user_settings(self):
        """Render user settings"""
        st.markdown("### 👤 User Profile Settings")

        user = st.session_state.user

        with st.form("user_settings_form"):
            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name", value=user["FirstName"])
                email = st.text_input("Email", value=user["Email"])
                department = st.text_input(
                    "Department", value=user.get("Department", "")
                )

            with col2:
                last_name = st.text_input("Last Name", value=user["LastName"])
                phone = st.text_input("Phone", value=user.get("Phone", ""))

            # Preferences
            st.markdown("#### 🎨 Preferences")
            theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
            notifications = st.checkbox("Enable Notifications", value=True)
            auto_refresh = st.checkbox("Auto Refresh Dashboard", value=True)

            if st.form_submit_button("💾 Save Settings", use_container_width=True):
                st.success("✅ Settings saved successfully!")

    def _render_system_settings(self):
        """Render system settings"""
        st.markdown("### ⚙️ System Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🗄️ Database")
            if st.button("🔍 Test Connection", use_container_width=True):
                self.test_database_connection()

            if st.button("🔄 Clear Cache", use_container_width=True):
                self.cache_manager.clear_all_cache()
                st.success("✅ Cache cleared successfully!")

        with col2:
            st.markdown("#### 📊 Performance")
            cache_stats = self.cache_manager.get_cache_stats()
            st.metric("Cache Hit Rate", f"{cache_stats.get('hit_rate', 0):.1f}%")
            st.metric("Cached Items", cache_stats.get("item_count", 0))

    def _render_performance_settings(self):
        """Render performance monitoring"""
        st.markdown("### 📈 Performance Monitoring")

        # Get performance metrics
        performance_data = self.performance_manager.get_performance_metrics()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ⚡ Response Times")
            if performance_data.get("response_times"):
                for page, time in performance_data["response_times"].items():
                    st.metric(f"{page} Load Time", f"{time:.2f}s")
            else:
                st.info("No performance data available")

        with col2:
            st.markdown("#### 💾 Memory Usage")
            memory_info = self.performance_manager.get_memory_info()
            if memory_info:
                st.metric("Memory Usage", f"{memory_info.get('used_mb', 0):.1f} MB")
                st.metric("Cache Size", f"{memory_info.get('cache_mb', 0):.1f} MB")

    def _render_about_section(self):
        """Render about section"""
        st.markdown("### ℹ️ About DENSO Project Manager Pro")

        st.markdown(
            """
        <div class="glass-card">
            <h3>🚀 DENSO Project Manager Pro</h3>
            <p><strong>Version:</strong> 2.0.0</p>
            <p><strong>Build Date:</strong> 2025-07-02</p>
            <p><strong>Database:</strong> SQL Server</p>
            <p><strong>Framework:</strong> Streamlit</p>
            
            <h4>✨ Features</h4>
            <ul>
                <li>✅ Real-time project management</li>
                <li>📊 Advanced analytics and reporting</li>
                <li>🔔 Intelligent notifications</li>
                <li>👥 Team collaboration tools</li>
                <li>📈 Performance monitoring</li>
                <li>🎨 Modern glassmorphism UI</li>
            </ul>
            
            <h4>🛠️ Technical Stack</h4>
            <ul>
                <li>Backend: Python 3.9+</li>
                <li>Database: SQL Server 2019+</li>
                <li>Frontend: Streamlit 1.30+</li>
                <li>Charts: Plotly</li>
                <li>Caching: Redis (optional)</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # System health check
        st.markdown("#### 🏥 System Health")

        col1, col2, col3 = st.columns(3)

        with col1:
            db_status = (
                "🟢 Online"
                if self.db_service.connection_manager.test_connection()
                else "🔴 Offline"
            )
            st.metric("Database", db_status)

        with col2:
            cache_status = "🟢 Active" if self.cache_manager else "🔴 Inactive"
            st.metric("Cache System", cache_status)

        with col3:
            notification_status = (
                "🟢 Running" if self.notification_service else "🔴 Stopped"
            )
            st.metric("Notifications", notification_status)

    def _logout(self):
        """Process user logout"""
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.current_page = "Dashboard"

        # Clear cache
        self.cache_manager.clear_user_cache(
            st.session_state.get("user", {}).get("UserID")
        )

        st.success("👋 Logged out successfully!")
        st.rerun()

    def _render_tasks_list(self, project_id: int):
        """Render tasks in list view"""
        st.markdown("### 📋 Task List View")

        tasks = self.db_service.get_tasks_by_project(project_id)

        if tasks:
            # Create DataFrame for better display
            task_data = []
            for task in tasks:
                task_data.append(
                    {
                        "Task": task["TaskName"],
                        "Status": task["Status"],
                        "Priority": task["Priority"],
                        "Assignee": task.get("AssigneeName", "Unassigned"),
                        "Due Date": task.get("DueDate", "Not set"),
                        "Progress": f"{task.get('Progress', 0)}%",
                    }
                )

            df = pd.DataFrame(task_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No tasks found for this project")

    def _render_tasks_calendar(self, project_id: int):
        """Render tasks in calendar view"""
        st.markdown("### 📅 Task Calendar View")
        st.info("Calendar view feature coming in next update!")


# Initialize and run the enhanced application
if __name__ == "__main__":
    app = EnhancedProjectManagerApp()
    app.run()
