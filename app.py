#!/usr/bin/env python3
"""
app.py
SDX Project Manager - Professional UI/UX Implementation
Modern, responsive interface with gradient design and professional authentication
"""

import streamlit as st
import logging
import sys
from pathlib import Path

# Add modules to path
current_dir = Path(__file__).parent
modules_dir = current_dir / "modules"
if str(modules_dir) not in sys.path:
    sys.path.insert(0, str(modules_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="SDX Project Manager",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/denso-innovation/sdx-project-manager",
        "Report a bug": "mailto:innovation@denso.com",
        "About": "# SDX Project Manager v2.0\nDeveloped by DENSO Innovation Team",
    },
)

# Import modules after Streamlit config
try:
    from config.database import get_database_connection, DatabaseManager
    from modules.auth import AuthenticationManager
    from modules.projects import ProjectManager
    from modules.tasks import TaskManager
    from modules.analytics import AnalyticsManager
    from modules.settings import SettingsManager
except ImportError as e:
    st.error(f"❌ Module import failed: {e}")
    st.info("📝 Run setup first: `python quick_setup.py`")
    st.stop()


# Global CSS for modern UI
def load_modern_css():
    """Load professional CSS styling"""
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
        
        /* Global Styles */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Modern Sidebar */
        .css-1d391kg {
            background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        
        .css-1d391kg .css-1v3fvcr {
            color: #e2e8f0;
        }
        
        /* Main Content Area */
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Professional Cards */
        .metric-card {
            background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        /* Professional Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px 0 rgba(59, 130, 246, 0.4);
        }
        
        /* Data Tables */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Alert Boxes */
        .stAlert {
            border-radius: 12px;
            border: none;
        }
        
        /* Input Fields */
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            padding: 0.75rem 1rem;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        /* Professional Headers */
        .page-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .page-header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 800;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .page-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        /* Status Indicators */
        .status-active {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .status-pending {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .status-completed {
            background: linear-gradient(135deg, #6366f1, #4f46e5);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        /* Modern Login */
        .login-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .login-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 3rem;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-width: 420px;
            width: 100%;
        }
        
        .login-logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 2rem;
            font-weight: 700;
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        
        .login-title {
            text-align: center;
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .login-subtitle {
            text-align: center;
            color: #64748b;
            margin-bottom: 2rem;
            font-size: 1rem;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            
            .login-card {
                margin: 1rem;
                padding: 2rem;
            }
            
            .page-header h1 {
                font-size: 2rem;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_professional_login():
    """Render professional split-screen login interface"""

    # Hide main interface elements during login
    st.markdown(
        """
    <style>
        .stSidebar {display: none;}
        .main .block-container {padding: 0; max-width: 100%;}
        
        /* Split Screen Layout */
        .login-wrapper {
            display: flex;
            min-height: 100vh;
            background: linear-gradient(135deg, #f0f2ff 0%, #e8ebff 100%);
        }
        
        .login-left {
            flex: 1;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 3rem;
            box-shadow: 2px 0 20px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .login-right {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        .login-form-container {
            width: 100%;
            max-width: 400px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 2.5rem;
        }
        
        .login-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: #1e293b;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        
        .login-subtitle {
            color: #64748b;
            font-size: 1rem;
            font-weight: 400;
        }
        
        /* Image Container */
        .image-container {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        .image-slider {
            width: 80%;
            height: 60%;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.2);
            position: relative;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .slide {
            width: 100%;
            height: 100%;
            display: none;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: rgba(255,255,255,0.7);
            background: linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        }
        
        .slide.active {
            display: flex;
        }
        
        /* Decorative elements */
        .login-right::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            animation: float 20s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }
        
        /* Form Styling */
        .stTextInput > div > div > input {
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: #f8fafc;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 1rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            width: 100%;
            margin-top: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        .stCheckbox {
            margin: 1rem 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .login-wrapper {
                flex-direction: column;
            }
            .login-left, .login-right {
                flex: none;
                height: 50vh;
            }
            .login-left {
                padding: 2rem;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Main login container
    st.markdown(
        """
    <div class="login-wrapper">
        <div class="login-left">
            <div class="login-form-container">
                <div class="login-header">
                    <h1 class="login-title">LOGIN</h1>
                    <p class="login-subtitle">เข้าสู่ระบบจัดการโครงการ SDX</p>
                </div>
            </div>
        </div>
        <div class="login-right">
            <div class="image-container">
                <div class="image-slider">
                    <div class="slide active">
                        📊<br><small style="font-size: 1rem;">Dashboard Analytics</small>
                    </div>
                    <div class="slide">
                        👥<br><small style="font-size: 1rem;">Team Collaboration</small>
                    </div>
                    <div class="slide">
                        🚀<br><small style="font-size: 1rem;">Project Management</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        
        function showSlide(n) {
            slides.forEach(slide => slide.classList.remove('active'));
            slides[n].classList.add('active');
        }
        
        function nextSlide() {
            currentSlide = (currentSlide + 1) % slides.length;
            showSlide(currentSlide);
        }
        
        // Auto slide every 3 seconds
        setInterval(nextSlide, 3000);
    </script>
    """,
        unsafe_allow_html=True,
    )

    # Login form in left container
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            "<div style='height: 200px;'></div>", unsafe_allow_html=True
        )  # Spacer

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "", placeholder="Username", label_visibility="collapsed"
            )

            password = st.text_input(
                "",
                type="password",
                placeholder="Password",
                label_visibility="collapsed",
            )

            remember_me = st.checkbox("จดจำการเข้าสู่ระบบ")

            submitted = st.form_submit_button("Login Now")

            if submitted:
                if username and password:
                    try:
                        db = get_database_connection()
                        if db:
                            # Simple authentication check
                            users = db.execute_query(
                                "SELECT * FROM Users WHERE Username = ? AND IsActive = 1",
                                (username,),
                            )

                            if users:
                                user = users[0]
                                # For demo purposes, simplified password check
                                st.session_state.authenticated = True
                                st.session_state.user = user
                                st.success(
                                    f"✅ ยินดีต้อนรับ {user['FirstName']} {user['LastName']}"
                                )
                                st.rerun()
                            else:
                                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                        else:
                            st.error("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")

                    except Exception as e:
                        logger.error(f"Login error: {e}")
                        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                else:
                    st.warning("⚠️ กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")


def render_professional_header(title: str, subtitle: str = "", icon: str = "🚀"):
    """Render professional page header"""
    st.markdown(
        f"""
    <div class="page-header">
        <h1>{icon} {title}</h1>
        {f'<p>{subtitle}</p>' if subtitle else ''}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_dashboard():
    """Render professional dashboard"""
    render_professional_header("Dashboard", "ภาพรวมโครงการและสถิติการทำงาน", "📊")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class="metric-card">
            <h3>🎯 โครงการทั้งหมด</h3>
            <h1 style="color: #3b82f6; margin: 0;">15</h1>
            <p style="color: #64748b; margin: 0;">+2 จากเดือนที่แล้ว</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="metric-card">
            <h3>🚀 งานที่เสร็จแล้ว</h3>
            <h1 style="color: #10b981; margin: 0;">128</h1>
            <p style="color: #64748b; margin: 0;">+15% อัตราการเสร็จ</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="metric-card">
            <h3>👥 ทีมงาน</h3>
            <h1 style="color: #8b5cf6; margin: 0;">6</h1>
            <p style="color: #64748b; margin: 0;">Innovation Team</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
        <div class="metric-card">
            <h3>⏰ งานที่ต้องทำ</h3>
            <h1 style="color: #f59e0b; margin: 0;">23</h1>
            <p style="color: #64748b; margin: 0;">5 งานใกล้ครบกำหนด</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Content tabs
    tab1, tab2, tab3 = st.tabs(["📈 ภาพรวมโครงการ", "📋 งานล่าสุด", "📊 สถิติทีม"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 สถานะโครงการ")
            # Mock data for demo
            import pandas as pd

            df_projects = pd.DataFrame(
                {
                    "โครงการ": [
                        "DENSO Digital Transformation",
                        "Smart Factory Automation",
                        "Innovation Lab Platform",
                        "Carbon Neutral Tech",
                        "Next-Gen Mobility",
                    ],
                    "สถานะ": [
                        "กำลังดำเนินการ",
                        "กำลังดำเนินการ",
                        "วางแผน",
                        "วางแผน",
                        "กำลังดำเนินการ",
                    ],
                    "ความคืบหน้า": [65, 45, 15, 5, 35],
                }
            )
            st.dataframe(df_projects, use_container_width=True)

        with col2:
            st.subheader("📊 การใช้งบประมาณ")
            # Budget chart would go here
            st.info("📈 การแสดงผลข้อมูลงบประมาณแบบ real-time")

    with tab2:
        st.subheader("📋 งานที่อัปเดตล่าสุด")
        # Recent tasks would go here
        st.info("🔄 งานที่มีการอัปเดตในรอบ 24 ชั่วโมงที่ผ่านมา")

    with tab3:
        st.subheader("👥 ประสิทธิภาพทีม")
        # Team analytics would go here
        st.info("📊 สถิติการทำงานและประสิทธิภาพของทีม")


def render_sidebar_navigation():
    """Render professional sidebar navigation"""
    user = st.session_state.get("user", {})

    with st.sidebar:
        # User profile section
        st.markdown(
            f"""
        <div style="text-align: center; padding: 1rem; margin-bottom: 2rem; 
                    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
                    border-radius: 12px;">
            <div style="width: 60px; height: 60px; margin: 0 auto 1rem; 
                        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 1.5rem; font-weight: 600;">
                {user.get('FirstName', 'U')[0]}
            </div>
            <h3 style="color: #e2e8f0; margin: 0; font-size: 1.1rem;">
                {user.get('FirstName', 'User')} {user.get('LastName', '')}
            </h3>
            <p style="color: #94a3b8; margin: 0; font-size: 0.9rem;">
                {user.get('Role', 'User')} • {user.get('Department', 'Team')}
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Navigation menu
        st.markdown("### 🧭 เมนูหลัก")

        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()

        if st.button("📁 โครงการ", use_container_width=True):
            st.session_state.current_page = "projects"
            st.rerun()

        if st.button("📋 งาน", use_container_width=True):
            st.session_state.current_page = "tasks"
            st.rerun()

        if st.button("👥 ทีม", use_container_width=True):
            st.session_state.current_page = "team"
            st.rerun()

        if st.button("📈 รายงาน", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()

        if user.get("Role") == "Admin":
            st.markdown("---")
            st.markdown("### ⚙️ การจัดการ")

            if st.button("🔧 ตั้งค่า", use_container_width=True):
                st.session_state.current_page = "settings"
                st.rerun()

        st.markdown("---")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def main():
    """Main application entry point"""
    try:
        # Load modern CSS
        load_modern_css()

        # Initialize session state
        if "current_page" not in st.session_state:
            st.session_state.current_page = "dashboard"

        # Check authentication
        if not st.session_state.get("authenticated", False):
            render_professional_login()
            return

        # Render main application
        render_sidebar_navigation()

        # Route to current page
        current_page = st.session_state.get("current_page", "dashboard")

        if current_page == "dashboard":
            render_dashboard()
        elif current_page == "projects":
            render_professional_header("โครงการ", "จัดการและติดตามโครงการทั้งหมด", "📁")
            st.info("🚧 หน้าโครงการกำลังพัฒนา")
        elif current_page == "tasks":
            render_professional_header("งาน", "จัดการงานและติดตามความคืบหน้า", "📋")
            st.info("🚧 หน้างานกำลังพัฒนา")
        elif current_page == "team":
            render_professional_header("ทีม", "จัดการสมาชิกทีมและสิทธิ์การเข้าถึง", "👥")
            st.info("🚧 หน้าทีมกำลังพัฒนา")
        elif current_page == "analytics":
            render_professional_header("รายงาน", "สถิติและการวิเคราะห์ข้อมูล", "📈")
            st.info("🚧 หน้ารายงานกำลังพัฒนา")
        elif current_page == "settings":
            render_professional_header("ตั้งค่า", "การตั้งค่าระบบและการกำหนดค่า", "⚙️")
            st.info("🚧 หน้าตั้งค่ากำลังพัฒนา")

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        st.info("🔄 กรุณารีเฟรชหน้าเว็บ")


if __name__ == "__main__":
    main()
