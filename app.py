#!/usr/bin/env python3
"""
app.py
SDX Project Manager - Enterprise-Grade Application
Professional UI/UX with real database integration and production-ready features
"""

import streamlit as st
import logging
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime
import time

# Performance monitoring
start_time = time.time()

# Add modules to path
current_dir = Path(__file__).parent
modules_dir = current_dir / "modules"
config_dir = current_dir / "config"
utils_dir = current_dir / "utils"

for path in [modules_dir, config_dir, utils_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Ensure log directory exists
log_dir = current_dir / "logs"
log_dir.mkdir(exist_ok=True)

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Streamlit page configuration - Production optimized
st.set_page_config(
    page_title="SDX Project Manager | DENSO Innovation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://denso-innovation.com/sdx-help",
        "Report a bug": "mailto:innovation@denso.com",
        "About": """
        # SDX Project Manager v2.5 Enterprise
        
        🏢 **DENSO Innovation Team**  
        📧 innovation@denso.com  
        🌐 denso-innovation.com
        
        **Features:**
        - Enterprise Authentication
        - Real-time Project Tracking
        - Advanced Analytics
        - Multi-language Support
        - Production Database
        """,
    },
)

# Import modules with error handling
try:
    from database import DatabaseManager
    from auth import AuthenticationManager, UserRole
    from projects import ProjectManager
    from tasks import TaskManager
    from analytics import AnalyticsManager
    from settings import SettingsManager
    from ui_components import UIComponents, ThemeManager
    from error_handler import ErrorHandler
    from performance_monitor import PerformanceMonitor
except ImportError as e:
    st.error(f"❌ **Module Import Error**")
    st.code(f"Error: {str(e)}")
    st.info("💡 **Quick Fix:** Run `python setup_environment.py` first")
    st.stop()

# Initialize error handler
error_handler = ErrorHandler()


# Load enhanced CSS and themes
def load_professional_css():
    """Load enterprise-grade CSS styling"""
    try:
        css_file = current_dir / "static" / "css" / "enterprise.css"
        if css_file.exists():
            with open(css_file, "r", encoding="utf-8") as f:
                custom_css = f.read()
        else:
            custom_css = ""

        st.markdown(
            f"""
        <style>
        /* Enterprise Theme */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        :root {{
            --primary-color: #6366f1;
            --primary-dark: #4f46e5;
            --secondary-color: #8b5cf6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --background-primary: #ffffff;
            --background-secondary: #f8fafc;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }}
        
        /* Global Styles */
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-feature-settings: 'cv11', 'ss01';
            font-variation-settings: 'opsz' 32;
        }}
        
        /* Hide Streamlit Default Elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stDeployButton {{display: none;}}
        
        /* Enhanced Sidebar */
        .css-1d391kg {{
            background: linear-gradient(180deg, 
                var(--primary-color) 0%, 
                var(--primary-dark) 100%);
            border-right: 1px solid var(--border-color);
        }}
        
        .css-1d391kg .css-17eq0hr {{
            color: white;
            font-weight: 600;
        }}
        
        /* Main Content Area */
        .main {{
            background: var(--background-secondary);
            padding: 2rem;
        }}
        
        /* Card Components */
        .metric-card {{
            background: var(--background-primary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        /* Professional Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-sm);
        }}
        
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}
        
        /* Status Badges */
        .status-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .status-active {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .status-pending {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .status-completed {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        /* Data Tables */
        .stDataFrame {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        /* Loading States */
        .loading-spinner {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .main {{
                padding: 1rem;
            }}
            
            .metric-card {{
                padding: 1rem;
            }}
        }}
        
        /* Dark Mode Support */
        @media (prefers-color-scheme: dark) {{
            :root {{
                --background-primary: #1e293b;
                --background-secondary: #0f172a;
                --text-primary: #f1f5f9;
                --text-secondary: #94a3b8;
                --border-color: #334155;
            }}
        }}
        
        {custom_css}
        </style>
        """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        logger.error(f"CSS loading error: {e}")
        st.error("⚠️ Styling partially loaded")


# Initialize session state
def initialize_session_state():
    """Initialize session state with enterprise defaults"""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "username": None,
        "user_role": None,
        "user_department": None,
        "current_page": "dashboard",
        "theme": "professional",
        "language": "th",
        "last_activity": datetime.now(),
        "session_timeout": 3600,  # 1 hour
        "notifications": [],
        "performance_data": {},
        "error_count": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Session timeout check
def check_session_timeout():
    """Check and handle session timeout"""
    if st.session_state.authenticated:
        time_elapsed = (datetime.now() - st.session_state.last_activity).seconds
        if time_elapsed > st.session_state.session_timeout:
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.warning("🔒 Session expired. Please login again.")
            st.rerun()
        else:
            st.session_state.last_activity = datetime.now()


# Enhanced authentication UI
def render_login_page():
    """Render enterprise-grade login page"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: var(--primary-color); font-weight: 800; font-size: 2.5rem;">
                🚀 SDX Project Manager
            </h1>
            <p style="color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 2rem;">
                DENSO Innovation Team | Enterprise Edition
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Login form
        with st.container():
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                st.markdown("### 🔐 เข้าสู่ระบบ")

                username = st.text_input(
                    "👤 ชื่อผู้ใช้งาน",
                    placeholder="กรอกชื่อผู้ใช้งาน",
                    help="ใช้ username ที่ได้รับจากทีม IT",
                )

                password = st.text_input(
                    "🔑 รหัสผ่าน",
                    type="password",
                    placeholder="กรอกรหัสผ่าน",
                    help="รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร",
                )

                col_login, col_forgot = st.columns([1, 1])
                with col_login:
                    submit_button = st.form_submit_button(
                        "🚀 เข้าสู่ระบบ", use_container_width=True
                    )

                with col_forgot:
                    if st.form_submit_button("🔄 ลืมรหัสผ่าน"):
                        st.info("📧 กรุณาติดต่อทีม IT: innovation@denso.com")

                if submit_button and username and password:
                    try:
                        # Initialize auth manager
                        auth_manager = AuthenticationManager(db_manager)

                        # Attempt login
                        user = auth_manager.login(username, password)

                        if user:
                            st.session_state.authenticated = True
                            st.session_state.user_id = user["UserID"]
                            st.session_state.username = user["Username"]
                            st.session_state.user_role = user["Role"]
                            st.session_state.user_department = user.get(
                                "Department", "N/A"
                            )
                            st.session_state.last_activity = datetime.now()

                            logger.info(f"Successful login: {username}")
                            st.success(f"✅ ยินดีต้อนรับ {user.get('FullName', username)}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                            logger.warning(f"Failed login attempt: {username}")

                    except Exception as e:
                        error_handler.handle_error(e, "Authentication Error")
                        st.error("🔧 เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้ง")

            st.markdown("</div>", unsafe_allow_html=True)

        # Demo credentials
        with st.expander("🔍 ข้อมูลสำหรับทดสอบ"):
            st.markdown(
                """
            **Admin Account:**
            - Username: `admin`
            - Password: `admin123`
            - Role: Administrator
            
            **User Account:**
            - Username: `user`
            - Password: `user123`
            - Role: User
            
            **Manager Account:**
            - Username: `manager`
            - Password: `manager123`
            - Role: Project Manager
            """
            )


# Enhanced sidebar navigation
def render_sidebar():
    """Render professional sidebar navigation"""
    with st.sidebar:
        # User info header
        st.markdown(
            f"""
        <div style="
            background: rgba(255,255,255,0.1);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <h3 style="color: white; margin: 0;">
                👤 {st.session_state.username}
            </h3>
            <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">
                {st.session_state.user_role} | {st.session_state.user_department}
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Navigation menu
        st.markdown("### 📋 เมนูหลัก")

        menu_items = [
            ("🏠", "dashboard", "แดชบอร์ด"),
            ("📊", "projects", "โครงการ"),
            ("✅", "tasks", "งาน"),
            ("👥", "team", "ทีม"),
            ("📈", "analytics", "รายงาน"),
            ("⚙️", "settings", "ตั้งค่า"),
        ]

        for icon, key, label in menu_items:
            if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("➕ โครงการใหม่", use_container_width=True):
            st.session_state.current_page = "projects"
            st.session_state.action = "create_project"
            st.rerun()

        if st.button("📝 งานใหม่", use_container_width=True):
            st.session_state.current_page = "tasks"
            st.session_state.action = "create_task"
            st.rerun()

        st.markdown("---")

        # Performance info
        performance_monitor = PerformanceMonitor()
        perf_data = performance_monitor.get_current_stats()

        st.markdown("### 📊 System Status")
        st.metric("CPU Usage", f"{perf_data.get('cpu_percent', 0):.1f}%")
        st.metric("Memory", f"{perf_data.get('memory_percent', 0):.1f}%")

        # Logout button
        st.markdown("---")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ["performance_data"]:
                    del st.session_state[key]
            st.rerun()


# Enhanced dashboard
def render_dashboard():
    """Render enterprise dashboard with real-time data"""
    st.markdown("# 🏠 แดชบอร์ด SDX Project Manager")
    st.markdown("---")

    try:
        # Load managers
        project_manager = ProjectManager(db_manager)
        task_manager = TaskManager(db_manager)
        analytics_manager = AnalyticsManager(db_manager)

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_projects = project_manager.get_project_count()
            st.metric(
                label="📊 โครงการทั้งหมด", value=total_projects, delta="+2 จากเดือนก่อน"
            )

        with col2:
            active_tasks = task_manager.get_active_task_count()
            st.metric(
                label="✅ งานที่ดำเนินการ", value=active_tasks, delta="+5 จากสัปดาห์ก่อน"
            )

        with col3:
            team_members = analytics_manager.get_team_member_count()
            st.metric(label="👥 สมาชิกทีม", value=team_members, delta="+1 สมาชิกใหม่")

        with col4:
            completion_rate = analytics_manager.get_completion_rate()
            st.metric(
                label="🎯 อัตราความสำเร็จ", value=f"{completion_rate:.1f}%", delta="+2.3%"
            )

        st.markdown("---")

        # Charts and analytics
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown("### 📈 ภาพรวมโครงการ")

            # Project status chart
            project_data = analytics_manager.get_project_status_distribution()
            if project_data:
                import plotly.express as px

                fig = px.pie(
                    values=list(project_data.values()),
                    names=list(project_data.keys()),
                    title="การกระจายสถานะโครงการ",
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("### 🔔 การแจ้งเตือน")

            # Recent notifications
            notifications = [
                "📝 งาน 'ออกแบบ UI' ใกล้ครบกำหนด",
                "✅ โครงการ 'Website Redesign' อัปเดต",
                "👤 สมาชิกใหม่เข้าร่วมทีม",
                "📊 รายงานประจำสัปดาห์พร้อมแล้ว",
            ]

            for notif in notifications[:4]:
                st.info(notif)

        # Recent activity
        st.markdown("### 📋 กิจกรรมล่าสุด")

        recent_activities = analytics_manager.get_recent_activities(limit=10)
        if recent_activities:
            for activity in recent_activities:
                with st.container():
                    col_time, col_activity = st.columns([1, 4])
                    with col_time:
                        st.caption(activity.get("timestamp", "N/A"))
                    with col_activity:
                        st.write(activity.get("description", "N/A"))
        else:
            st.info("ไม่มีกิจกรรมล่าสุด")

    except Exception as e:
        error_handler.handle_error(e, "Dashboard Error")
        st.error("❌ เกิดข้อผิดพลาดในการโหลดแดชบอร์ด")


# Initialize database connection
@st.cache_resource
def get_db_manager():
    """Initialize database manager with connection pooling"""
    try:
        return DatabaseManager()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        st.error("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
        st.stop()


# Main application flow
def main():
    """Main application entry point"""
    try:
        # Load CSS and initialize
        load_professional_css()
        initialize_session_state()

        # Global database manager
        global db_manager
        db_manager = get_db_manager()

        # Session timeout check
        check_session_timeout()

        # Render appropriate interface
        if not st.session_state.authenticated:
            render_login_page()
        else:
            # Authenticated interface
            render_sidebar()

            # Main content area
            if st.session_state.current_page == "dashboard":
                render_dashboard()
            elif st.session_state.current_page == "projects":
                from projects_ui import render_projects_page

                render_projects_page(db_manager)
            elif st.session_state.current_page == "tasks":
                from tasks_ui import render_tasks_page

                render_tasks_page(db_manager)
            elif st.session_state.current_page == "analytics":
                from analytics_ui import render_analytics_page

                render_analytics_page(db_manager)
            elif st.session_state.current_page == "settings":
                from settings_ui import render_settings_page

                render_settings_page(db_manager)
            else:
                st.error(f"❌ ไม่พบหน้า: {st.session_state.current_page}")

        # Performance logging
        load_time = time.time() - start_time
        if load_time > 2.0:
            logger.warning(f"Slow page load: {load_time:.2f}s")

    except Exception as e:
        error_handler.handle_error(e, "Application Error")
        st.error("🔧 เกิดข้อผิดพลาดระบบ กรุณาลองใหม่อีกครั้ง")


if __name__ == "__main__":
    main()
