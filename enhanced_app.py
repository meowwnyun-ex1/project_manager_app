# enhanced_app.py
import streamlit as st
import logging
from config.settings import app_config
from services.enhanced_db_service import DatabaseService
from services.auth_service import authenticate_user, register_user, logout

# Import enhanced pages
from pages import enhanced_dashboard, projects, tasks, gantt_chart
from components.navigation import render_sidebar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=app_config.PAGE_TITLE,
    page_icon=app_config.PAGE_ICON,
    layout=app_config.LAYOUT,
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-box { background-color: #d4edda; border-left: 4px solid #28a745; }
    .warning-box { background-color: #fff3cd; border-left: 4px solid #ffc107; }
    .error-box { background-color: #f8d7da; border-left: 4px solid #dc3545; }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


def initialize_app():
    """Initialize application and check database connection"""
    try:
        # Test database connection
        if DatabaseService.test_connection():
            logger.info("Database connection successful")
        else:
            st.error("ไม่สามารถเชื่อมต่อฐานข้อมูลได้ กรุณาตรวจสอบการตั้งค่า")
            st.stop()

    except Exception as e:
        logger.error(f"App initialization failed: {e}")
        st.error(f"เกิดข้อผิดพลาดในการเริ่มต้นแอปพลิเคชัน: {e}")
        st.stop()


def initialize_session_state():
    """Initialize session state variables"""
    session_keys = app_config.SESSION_KEYS

    defaults = {
        session_keys["logged_in"]: False,
        session_keys["user_id"]: None,
        session_keys["username"]: None,
        session_keys["user_role"]: None,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def render_login_page():
    """Render login and registration page"""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🔐 Project Manager")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        login_tab, register_tab = st.tabs(["เข้าสู่ระบบ", "ลงทะเบียน"])

        with login_tab:
            render_login_form()

        with register_tab:
            render_register_form()


def render_login_form():
    """Render login form"""
    with st.form("login_form", clear_on_submit=False):
        st.subheader("เข้าสู่ระบบ")

        username = st.text_input("ชื่อผู้ใช้", placeholder="กรอกชื่อผู้ใช้", max_chars=50)

        password = st.text_input("รหัสผ่าน", type="password", placeholder="กรอกรหัสผ่าน")

        login_button = st.form_submit_button(
            "เข้าสู่ระบบ", type="primary", use_container_width=True
        )

        if login_button:
            if not username or not password:
                st.error("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
                return

            if authenticate_user(username, password):
                st.success(
                    f"ยินดีต้อนรับ {st.session_state[app_config.SESSION_KEYS['username']]}!"
                )
                st.rerun()
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")


def render_register_form():
    """Render registration form"""
    with st.form("register_form", clear_on_submit=True):
        st.subheader("สร้างบัญชีใหม่")

        new_username = st.text_input(
            "ชื่อผู้ใช้ใหม่",
            placeholder="ชื่อผู้ใช้ 3-50 ตัวอักษร",
            max_chars=50,
            help="ใช้ตัวอักษร a-z, ตัวเลข 0-9 และขีดล่าง _ เท่านั้น",
        )

        col1, col2 = st.columns(2)
        with col1:
            new_password = st.text_input(
                "รหัสผ่านใหม่", type="password", placeholder="อย่างน้อย 6 ตัวอักษร"
            )

        with col2:
            confirm_password = st.text_input(
                "ยืนยันรหัสผ่าน", type="password", placeholder="ยืนยันรหัสผ่าน"
            )

        register_button = st.form_submit_button(
            "ลงทะเบียน", type="primary", use_container_width=True
        )

        if register_button:
            # Validation
            errors = []

            if not new_username:
                errors.append("กรุณากรอกชื่อผู้ใช้")
            elif len(new_username) < 3:
                errors.append("ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร")

            if not new_password:
                errors.append("กรุณากรอกรหัสผ่าน")
            elif len(new_password) < 6:
                errors.append("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")

            if new_password != confirm_password:
                errors.append("รหัสผ่านไม่ตรงกัน")

            if errors:
                for error in errors:
                    st.error(error)
                return

            # Attempt registration
            if register_user(new_username, new_password):
                st.success(f"ลงทะเบียนผู้ใช้ '{new_username}' สำเร็จ! กรุณาเข้าสู่ระบบ")
            else:
                st.error("ไม่สามารถลงทะเบียนได้ อาจมีชื่อผู้ใช้นี้อยู่แล้ว")


def render_main_app():
    """Render main application interface"""
    # Sidebar navigation
    with st.sidebar:
        render_sidebar()

        # User info
        st.markdown("---")
        username = st.session_state.get(app_config.SESSION_KEYS["username"], "Guest")
        role = st.session_state.get(app_config.SESSION_KEYS["user_role"], "")

        st.markdown(f"**ผู้ใช้:** {username}")
        st.markdown(f"**บทบาท:** {role}")

        # Logout button
        st.markdown("---")
        if st.button("ออกจากระบบ", type="secondary", use_container_width=True):
            logout()
            st.rerun()

    # Main content area
    page_selection = st.session_state.get("page_selection", "Dashboard")

    # Route to appropriate page
    if page_selection == "Dashboard":
        enhanced_dashboard.app()
    elif page_selection == "โปรเจกต์":
        projects.app()
    elif page_selection == "งาน":
        tasks.app()
    elif page_selection == "Gantt Chart":
        gantt_chart.app()
    elif page_selection == "รายงาน":
        render_reports_page()
    elif page_selection == "ตั้งค่า":
        render_settings_page()


def render_reports_page():
    """Render reports page (placeholder)"""
    st.title("📈 รายงาน")
    st.info("หน้ารายงานขั้นสูงจะถูกพัฒนาเพิ่มเติมในภายหลัง")

    st.subheader("รายงานที่วางแผนไว้")
    reports = [
        "📊 รายงานสรุปโปรเจกต์",
        "📈 รายงานประสิทธิภาพทีม",
        "📅 รายงานการใช้เวลา",
        "💰 รายงานงบประมาณ",
        "📋 รายงานความเสี่ยง",
    ]

    for report in reports:
        st.markdown(f"- {report}")


def render_settings_page():
    """Render settings page (placeholder)"""
    st.title("⚙️ ตั้งค่า")
    st.info("หน้าตั้งค่าจะถูกพัฒนาเพิ่มเติมในภายหลัง")


def main():
    """Main application entry point"""
    # Initialize app
    initialize_app()
    initialize_session_state()

    # Check authentication
    if not st.session_state[app_config.SESSION_KEYS["logged_in"]]:
        render_login_page()
    else:
        render_main_app()


if __name__ == "__main__":
    main()
