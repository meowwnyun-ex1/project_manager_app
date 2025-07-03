#!/usr/bin/env python3
"""
DENSO Project Manager Pro - Main Application Runner
Entry point for the application with modular structure
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta  # Import timedelta here
import logging
import time  # Added for time.sleep

# Add project modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from config.database import get_database_manager  # Use the singleton function
from modules.auth import AuthManager
from modules.ui_components import UIRenderer
from modules.projects import ProjectManager
from modules.tasks import TaskManager
from modules.analytics import AnalyticsManager
from modules.settings import SettingsManager
from modules.users import UserManager
from utils.error_handler import handle_streamlit_errors, get_error_handler
from utils.performance_monitor import PerformanceMonitor

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
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "DENSO Project Manager Pro",
    },
)


class DENSOProjectManager:
    """Main application class"""

    def __init__(self):
        """Initialize application"""
        try:
            # Initialize managers (using get_database_manager for singleton)
            self.db_manager = get_database_manager()
            self.auth_manager = AuthManager(self.db_manager)
            self.ui_renderer = UIRenderer()
            self.project_manager = ProjectManager(self.db_manager)
            self.task_manager = TaskManager(self.db_manager)
            self.analytics_manager = AnalyticsManager(self.db_manager)
            self.settings_manager = SettingsManager(self.db_manager)
            self.user_manager = UserManager(self.db_manager)
            self.performance_monitor = PerformanceMonitor()

            # Initialize session state
            self._initialize_session_state()

            logger.info("DENSO Project Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            st.error(f"ไม่สามารถเริ่มต้นระบบได้: {str(e)}")
            # If initialization fails, terminate Streamlit gracefully
            st.stop()

    def _initialize_session_state(self):
        """Initialize session state variables"""
        defaults = {
            "authenticated": False,
            "user": None,
            "current_page": "Dashboard",
            "show_new_project": False,
            "show_new_task": False,
            "show_new_user": False,
            "selected_project": None,
            "selected_task": None,
            "theme": "light",
            "language": "th",
            "last_activity": datetime.now(),
            "show_register": False,  # Ensure this is initialized
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @handle_streamlit_errors
    def run(self):
        """Main application runner"""
        try:
            # Start performance monitoring
            with self.performance_monitor.measure_time("app_render"):

                # Apply CSS styles
                self.ui_renderer.apply_styles()

                # Check session timeout
                self._check_session_timeout()

                # Check authentication
                if not st.session_state.authenticated:
                    self._show_login_page()
                else:
                    self._show_main_application()

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error("เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้ง")

    def _check_session_timeout(self):
        """Check session timeout"""
        if st.session_state.authenticated:
            last_activity = st.session_state.get("last_activity", datetime.now())
            timeout_minutes = 60  # 1 hour timeout

            if datetime.now() - last_activity > timedelta(minutes=timeout_minutes):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.warning("เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่")
                st.rerun()
            else:
                st.session_state.last_activity = datetime.now()

    def _show_login_page(self):
        """Show login page"""
        # Show header
        self.ui_renderer.show_header()

        # Login form
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            with st.container():
                st.markdown(
                    """
                <div class="login-container">
                    <h2 style="text-align: center; margin-bottom: 2rem;">🔐 เข้าสู่ระบบ</h2>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                with st.form("login_form"):
                    username = st.text_input(
                        "👤 ชื่อผู้ใช้",
                        placeholder="กรอกชื่อผู้ใช้",
                        help="ใช้ชื่อผู้ใช้ที่ได้รับจากผู้ดูแลระบบ",
                    )
                    password = st.text_input(
                        "🔒 รหัสผ่าน",
                        type="password",
                        placeholder="กรอกรหัสผ่าน",
                        help="รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร",
                    )

                    remember_me = st.checkbox("จดจำการเข้าสู่ระบบ")

                    col1_form, col2_form = st.columns(
                        2
                    )  # Renamed to avoid conflict with outer columns
                    with col1_form:
                        login_button = st.form_submit_button(
                            "🚀 เข้าสู่ระบบ", use_container_width=True, type="primary"
                        )
                    with col2_form:
                        register_button = st.form_submit_button(
                            "📝 สมัครสมาชิก", use_container_width=True
                        )

                    if login_button:
                        self._handle_login(username, password, remember_me)

                    if register_button:
                        st.session_state.show_register = True
                        st.rerun()

                # Show registration form if needed
                if st.session_state.get("show_register", False):
                    self._show_registration_form()

    def _handle_login(self, username: str, password: str, remember_me: bool):
        """Handle login process"""
        if not username or not password:
            st.error("⚠️ กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            return

        with st.spinner("กำลังตรวจสอบข้อมูล..."):
            user = self.auth_manager.authenticate_user(username, password)

            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.last_activity = datetime.now()

                if remember_me:
                    # Set longer session for remember me (logic for this would need to be implemented, e.g., using cookies)
                    # For a Streamlit app, "remember me" usually implies a longer session timeout.
                    # As of now, `st.session_state` resets on app rerun/tab close.
                    # Advanced "remember me" might involve server-side tokens or browser cookies managed outside st.session_state.
                    st.session_state.remember_login = True
                    logger.info(
                        "Remember Me is checked, consider extending session timeout logic if needed."
                    )

                st.success("✅ เข้าสู่ระบบสำเร็จ!")
                time.sleep(1)  # Brief pause for user feedback
                st.rerun()
            else:
                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    def _show_registration_form(self):
        """Show user registration form"""
        st.markdown("---")
        st.subheader("📝 สมัครสมาชิกใหม่")

        with st.form("register_form"):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input("👤 ชื่อผู้ใช้", help="ใช้เป็น ID สำหรับเข้าสู่ระบบ")
                email = st.text_input("📧 อีเมล", help="อีเมลสำหรับติดต่อ")
                first_name = st.text_input("👨 ชื่อ")
                department = st.selectbox(
                    "🏢 แผนก",
                    [
                        "Acounting & Planning",
                        "AR & AS",
                        "Corporate Planning Center",
                        "General Affairs & CSR",
                        "Information Security",
                        "Innovation",
                        "Maintenance",
                        "Production Control",
                        "Production Engineering",
                        "Purchasing",
                        "Quality Assurance",
                        "Quality Control",
                        "Safety & Environment",
                        "Strategic Production",
                        "WH Logistics",
                        "อื่นๆ",
                    ],
                )

            with col2:
                password = st.text_input(
                    "🔒 รหัสผ่าน", type="password", help="อย่างน้อย 8 ตัวอักษร"
                )
                confirm_password = st.text_input("🔒 ยืนยันรหัสผ่าน", type="password")
                last_name = st.text_input("👨 นามสกุล")
                phone = st.text_input("📱 เบอร์โทรศัพท์", help="เลขหมายโทรศัพท์มือถือ")

            # Terms and conditions
            accept_terms = st.checkbox(
                "✅ ฉันยอมรับเงื่อนไขการใช้งาน", help="จำเป็นต้องยอมรับเพื่อสมัครสมาชิก"
            )

            col1_reg, col2_reg = st.columns(2)  # Renamed to avoid conflict
            with col1_reg:
                submit_button = st.form_submit_button(
                    "✅ สมัครสมาชิก", use_container_width=True, type="primary"
                )
            with col2_reg:
                cancel_button = st.form_submit_button(
                    "❌ ยกเลิก", use_container_width=True
                )

            if submit_button:
                self._handle_registration(
                    {
                        "username": username,
                        "password": password,
                        "confirm_password": confirm_password,
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "department": department,
                        "phone": phone,
                        "accept_terms": accept_terms,
                    }
                )

            if cancel_button:
                st.session_state.show_register = False
                st.rerun()

    def _handle_registration(self, form_data: dict):
        """Handle user registration"""
        # Validation
        errors = []

        if not all(
            [
                form_data["username"],
                form_data["email"],
                form_data["first_name"],
                form_data["last_name"],
                form_data["password"],
                form_data["confirm_password"],
            ]
        ):
            errors.append("กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน")

        if form_data["password"] != form_data["confirm_password"]:
            errors.append("รหัสผ่านไม่ตรงกัน")

        if len(form_data["password"]) < 8:
            errors.append("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")

        if not form_data["accept_terms"]:
            errors.append("กรุณายอมรับเงื่อนไขการใช้งาน")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
            return

        # Create user
        user_data = {
            "username": form_data["username"],
            "password": form_data["password"],
            "email": form_data["email"],
            "first_name": form_data["first_name"],
            "last_name": form_data["last_name"],
            "department": form_data["department"],
            "phone": form_data["phone"],
            "role": "User",  # Default role
        }

        if self.user_manager.create_user(user_data):
            st.success("✅ สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
            st.session_state.show_register = False
            st.rerun()
        else:
            st.error("❌ ไม่สามารถสมัครสมาชิกได้ ชื่อผู้ใช้หรืออีเมลอาจถูกใช้แล้ว")

    def _show_main_application(self):
        """Show main application interface"""
        # Show sidebar
        self._show_sidebar()

        # Show main content based on current page
        page = st.session_state.current_page

        # Performance monitoring for page loads
        with self.performance_monitor.measure_time(f"page_{page.lower()}"):

            if page == "Dashboard":
                from pages.dashboard import DashboardPage

                dashboard = DashboardPage(
                    self.analytics_manager, self.project_manager, self.task_manager
                )
                dashboard.show()

            elif page == "Projects":
                from pages.projects import ProjectsPage

                projects = ProjectsPage(self.project_manager, self.user_manager)
                projects.show()

            elif page == "Tasks":
                from pages.tasks import TasksPage

                tasks = TasksPage(
                    self.task_manager, self.project_manager, self.user_manager
                )
                tasks.show()

            elif page == "Analytics":
                from pages.analytics import AnalyticsPage

                analytics = AnalyticsPage(self.analytics_manager)
                analytics.show()

            elif page == "Users":
                from pages.users import UsersPage

                users = UsersPage(self.user_manager, self.auth_manager)
                users.show()

            elif page == "Settings":
                from pages.settings import SettingsPage

                settings = SettingsPage(self.settings_manager)
                settings.show()

            elif page == "Database Admin":
                # Only allow Admin or Project Manager roles to access Database Admin page
                if st.session_state.user.get("Role") in ["Admin", "Project Manager"]:
                    from pages.database_admin import DatabaseAdminPage

                    db_admin = DatabaseAdminPage(self.db_manager)
                    db_admin.show()
                else:
                    st.warning("คุณไม่มีสิทธิ์เข้าถึงหน้านี้.")
                    st.session_state.current_page = "Dashboard"  # Redirect to dashboard
                    st.rerun()

    def _show_sidebar(self):
        """Show sidebar navigation"""
        with st.sidebar:
            # User info
            self.ui_renderer.show_user_info(st.session_state.user)

            # Navigation menu
            self.ui_renderer.show_navigation_menu()

            # Quick actions
            self.ui_renderer.show_quick_actions()

            # Performance info (for admins)
            if st.session_state.user and st.session_state.user.get("Role") in [
                "Admin",
                "Project Manager",
            ]:
                self.ui_renderer.show_performance_info(self.performance_monitor)

            # Logout
            if st.button("🚪 ออกจากระบบ", use_container_width=True, type="secondary"):
                self._handle_logout()

    def _handle_logout(self):
        """Handle user logout"""
        # Log the logout
        logger.info(
            f"User {st.session_state.user.get('Username', 'Unknown')} logged out"
        )

        # Clear session state
        for key in list(st.session_state.keys()):
            # Keep theme and language preferences upon logout
            if key not in ["theme", "language"]:
                del st.session_state[key]

        st.success("✅ ออกจากระบบเรียบร้อยแล้ว")
        st.rerun()


def main():
    """Main function"""
    try:
        # Initialize and run application
        app = DENSOProjectManager()
        app.run()

    except Exception as e:
        logger.error(f"Critical application error: {str(e)}")
        st.error("เกิดข้อผิดพลาดร้ายแรง กรุณาติดต่อผู้ดูแลระบบ")

        # Show error details for admins
        if st.session_state.get("user", {}).get("Role") == "Admin":
            with st.expander("รายละเอียดข้อผิดพลาด (Admin Only)"):
                st.code(str(e))


if __name__ == "__main__":
    main()
