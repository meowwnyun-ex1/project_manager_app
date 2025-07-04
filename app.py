#!/usr/bin/env python3
"""
app.py
DENSO Project Manager Pro - Main Application
Enterprise-grade project management system
"""
import streamlit as st
import sys
import os
import logging
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import modules
try:
    from config.database import get_database_manager
    from modules.auth import AuthenticationManager
    from modules.projects import ProjectManager
    from modules.tasks import TaskManager
    from modules.users import UserManager
    from modules.analytics import AnalyticsManager
    from modules.settings import SettingsManager
    from utils.ui_components import UIComponents
    from utils.error_handler import safe_execute, handle_error
except ImportError as e:
    st.error(f"ไม่พบโมดูลที่จำเป็น: {e}")
    st.stop()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="DENSO Project Manager Pro",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS - Optimized for screen scaling
st.markdown(
    """
<style>
    /* Main layout optimization */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Compact header */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        font-size: 1.8rem;
        margin: 0;
        font-weight: 600;
    }
    
    .main-header p {
        font-size: 0.9rem;
        margin: 0.3rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Login form styling */
    .login-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        max-width: 400px;
        margin: 0 auto;
    }
    
    .login-title {
        text-align: center;
        color: #1e3c72;
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
    }
    
    /* Status indicators */
    .status-active { color: #28a745; font-weight: 500; }
    .status-pending { color: #ffc107; font-weight: 500; }
    .status-overdue { color: #dc3545; font-weight: 500; }
    
    /* Sidebar optimization */
    .sidebar-nav {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
    }
    
    .sidebar-nav h4 {
        color: #1e3c72;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    .sidebar-nav p {
        font-size: 0.85rem;
        margin: 0.2rem 0;
        color: #666;
    }
    
    /* Compact metrics */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 0.8rem;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Form elements */
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 0.6rem;
    }
    
    .stTextInput input:focus {
        border-color: #2a5298;
        box-shadow: 0 0 0 2px rgba(42, 82, 152, 0.1);
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 8px;
        border: none;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    }
    
    .stButton button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Chart containers */
    .js-plotly-plot {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 1.5rem; }
        .main-header p { font-size: 0.8rem; }
        .login-container { padding: 1.5rem; }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


class DENSOProjectManager:
    """Main application class"""

    def __init__(self):
        self.init_session_state()
        self.db_manager = self.init_database()
        self.auth_manager = AuthenticationManager(self.db_manager)
        self.ui = UIComponents()

        # Initialize managers
        self.project_manager = ProjectManager(self.db_manager)
        self.task_manager = TaskManager(self.db_manager)
        self.user_manager = UserManager(self.db_manager)
        self.analytics_manager = AnalyticsManager(self.db_manager)
        self.settings_manager = SettingsManager(self.db_manager)

    def init_session_state(self):
        """Initialize session state variables"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user_data" not in st.session_state:
            st.session_state.user_data = None
        if "current_page" not in st.session_state:
            st.session_state.current_page = "dashboard"

    def init_database(self):
        """Initialize database connection"""
        try:
            return get_database_manager()
        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้: {e}")
            st.info("🔧 กรุณาตรวจสอบ .streamlit/secrets.toml และการเชื่อมต่อ SQL Server")
            st.stop()

    def show_login_page(self):
        """Show clean login page without sample credentials"""
        # Compact header
        st.markdown(
            """
        <div class="main-header">
            <h1>🚗 DENSO Project Manager Pro</h1>
            <p>ระบบจัดการโครงการสำหรับ DENSO Corporation</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Centered login form
        col1, col2, col3 = st.columns([1, 1.5, 1])

        with col2:
            st.markdown(
                """
                <div class="login-container">
                    <div class="login-title">🔐 เข้าสู่ระบบ</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form"):
                username = st.text_input(
                    "👤 ชื่อผู้ใช้",
                    placeholder="กรอกชื่อผู้ใช้ของคุณ",
                    help="ใช้ชื่อผู้ใช้ที่ได้รับจากผู้ดูแลระบบ",
                )
                password = st.text_input(
                    "🔒 รหัสผ่าน",
                    type="password",
                    placeholder="กรอกรหัสผ่านของคุณ",
                    help="ใช้รหัสผ่านที่ได้รับจากผู้ดูแลระบบ",
                )
                remember_me = st.checkbox("จดจำการเข้าสู่ระบบ")

                if st.form_submit_button(
                    "เข้าสู่ระบบ", use_container_width=True, type="primary"
                ):
                    if username and password:
                        result = safe_execute(
                            self.auth_manager.authenticate_user,
                            username,
                            password,
                            default_return={"success": False, "message": "เกิดข้อผิดพลาด"},
                        )

                        if result["success"]:
                            st.session_state.authenticated = True
                            st.session_state.user_data = result["user_data"]
                            st.success("✅ เข้าสู่ระบบสำเร็จ")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['message']}")
                    else:
                        st.warning("⚠️ กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")

        # Help section
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info(
                """
                **🆘 ต้องการความช่วยเหลือ?**
                
                📞 ติดต่อทีม DENSO Innovation Team  
                📧 Email: innovation.team@denso.com  
                🕐 เวลาทำการ: จันทร์-ศุกร์ 08:00-17:00
                """
            )

    def show_sidebar_navigation(self):
        """Show compact sidebar navigation"""
        user_data = st.session_state.user_data

        with st.sidebar:
            # Compact user info
            st.markdown(
                f"""
            <div class="sidebar-nav">
                <h4>👤 {user_data['FirstName']} {user_data['LastName']}</h4>
                <p><strong>ตำแหน่ง:</strong> {user_data['Role']}</p>
                <p><strong>แผนก:</strong> {user_data.get('Department', 'N/A')}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Navigation menu
            st.markdown("### 📋 เมนูหลัก")

            pages = {
                "dashboard": "📊 แดชบอร์ด",
                "projects": "📁 จัดการโครงการ",
                "tasks": "✅ จัดการงาน",
                "analytics": "📈 รายงานและการวิเคราะห์",
                "users": "👥 จัดการผู้ใช้",
                "settings": "⚙️ ตั้งค่าระบบ",
            }

            # Add database admin for admin users
            if user_data["Role"] == "Admin":
                pages["database"] = "🗄️ จัดการฐานข้อมูล"

            selected_page = st.selectbox(
                "เลือกหน้า",
                options=list(pages.keys()),
                format_func=lambda x: pages[x],
                index=list(pages.keys()).index(st.session_state.current_page),
            )

            if selected_page != st.session_state.current_page:
                st.session_state.current_page = selected_page
                st.rerun()

            st.markdown("---")

            # Compact quick stats
            st.markdown("### 📊 สถิติด่วน")
            self.show_quick_stats()

            st.markdown("---")

            # Logout button
            if st.button("🚪 ออกจากระบบ", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    def show_quick_stats(self):
        """Show compact quick statistics in sidebar"""
        try:
            # Get quick stats
            total_projects = safe_execute(
                self.project_manager.get_total_projects, default_return=0
            )

            active_tasks = safe_execute(
                self.task_manager.get_active_tasks_count, default_return=0
            )

            overdue_tasks = safe_execute(
                self.task_manager.get_overdue_tasks_count, default_return=0
            )

            # Compact metrics
            st.metric("📁 โครงการ", total_projects)
            st.metric("✅ งานที่ทำ", active_tasks)
            st.metric(
                "⏰ เลยกำหนด",
                overdue_tasks,
                delta=f"-{overdue_tasks}" if overdue_tasks > 0 else None,
            )

        except Exception as e:
            st.error(f"ไม่สามารถโหลดสถิติได้: {e}")

    def show_dashboard(self):
        """Show compact main dashboard"""
        # Compact header
        st.markdown(
            """
        <div class="main-header">
            <h1>📊 แดชบอร์ด DENSO Project Manager Pro</h1>
            <p>ภาพรวมการดำเนินงานโครงการ</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Key metrics in compact layout
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_projects = safe_execute(
                self.project_manager.get_total_projects, default_return=0
            )
            st.metric("📁 โครงการทั้งหมด", total_projects)

        with col2:
            active_projects = safe_execute(
                self.project_manager.get_active_projects_count, default_return=0
            )
            st.metric("🚀 กำลังดำเนินการ", active_projects)

        with col3:
            total_tasks = safe_execute(
                self.task_manager.get_total_tasks, default_return=0
            )
            st.metric("✅ งานทั้งหมด", total_tasks)

        with col4:
            completion_rate = safe_execute(
                self.analytics_manager.get_completion_rate, default_return=0
            )
            st.metric("📈 อัตราสำเร็จ", f"{completion_rate:.1f}%")

        # Charts in compact layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 สถานะโครงการ")
            project_status_data = safe_execute(
                self.analytics_manager.get_project_status_distribution,
                default_return=[],
            )

            if project_status_data:
                df = pd.DataFrame(project_status_data)
                fig = px.pie(
                    df,
                    values="count",
                    names="status",
                    title="การกระจายสถานะโครงการ",
                    height=350,
                )
                fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลโครงการ")

        with col2:
            st.subheader("📈 ความคืบหน้า")
            progress_data = safe_execute(
                self.analytics_manager.get_progress_timeline, default_return=[]
            )

            if progress_data:
                df = pd.DataFrame(progress_data)
                fig = px.line(
                    df, x="date", y="completion", title="ความคืบหน้าโครงการ", height=350
                )
                fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลความคืบหน้า")

        # Compact recent activities
        st.subheader("🕒 กิจกรรมล่าสุด")
        recent_activities = safe_execute(
            self.analytics_manager.get_recent_activities, limit=5, default_return=[]
        )

        if recent_activities:
            for i, activity in enumerate(recent_activities):
                if i < 3:  # Show only 3 activities to save space
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(
                            f"**{activity.get('activity_type', 'N/A')}** - {activity.get('description', 'N/A')}"
                        )
                    with col2:
                        st.markdown(f"*{activity.get('user_name', 'N/A')}*")
            if len(recent_activities) > 3:
                st.markdown(f"*และอีก {len(recent_activities) - 3} กิจกรรม...*")
        else:
            st.info("ไม่มีกิจกรรมล่าสุด")

    def show_projects_page(self):
        """Show projects management page"""
        from modules.projects import show_projects_page

        show_projects_page(self.project_manager, self.user_manager)

    def show_tasks_page(self):
        """Show tasks management page"""
        from modules.tasks import show_tasks_page

        show_tasks_page(self.task_manager, self.project_manager, self.user_manager)

    def show_analytics_page(self):
        """Show analytics and reports page"""
        from modules.analytics import show_analytics_page

        show_analytics_page(self.analytics_manager)

    def show_users_page(self):
        """Show users management page"""
        user_data = st.session_state.user_data
        if user_data["Role"] not in ["Admin", "Project Manager"]:
            st.error("❌ คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
            return

        from modules.users import show_users_page

        show_users_page(self.user_manager)

    def show_settings_page(self):
        """Show settings page"""
        from modules.settings import show_settings_page

        show_settings_page(self.settings_manager, st.session_state.user_data)

    def show_database_page(self):
        """Show database admin page"""
        user_data = st.session_state.user_data
        if user_data["Role"] != "Admin":
            st.error("❌ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
            return

        from modules.database_admin import show_database_admin_page

        show_database_admin_page(self.db_manager)

    def run(self):
        """Run the main application"""
        try:
            if not st.session_state.authenticated:
                self.show_login_page()
            else:
                self.show_sidebar_navigation()

                # Route to appropriate page
                page = st.session_state.current_page

                if page == "dashboard":
                    self.show_dashboard()
                elif page == "projects":
                    self.show_projects_page()
                elif page == "tasks":
                    self.show_tasks_page()
                elif page == "analytics":
                    self.show_analytics_page()
                elif page == "users":
                    self.show_users_page()
                elif page == "settings":
                    self.show_settings_page()
                elif page == "database":
                    self.show_database_page()
                else:
                    st.error("ไม่พบหน้าที่ร้องขอ")

        except Exception as e:
            handle_error(e, "เกิดข้อผิดพลาดในระบบ")


def main():
    """Main entry point"""
    try:
        app = DENSOProjectManager()
        app.run()
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการเริ่มต้นระบบ: {e}")
        st.info("🔧 กรุณาตรวจสอบการติดตั้งและการตั้งค่า")
        logger.error(f"Application startup failed: {e}")


if __name__ == "__main__":
    main()
