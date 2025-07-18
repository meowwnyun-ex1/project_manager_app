#!/usr/bin/env python3
"""
app.py
SDX Project Manager - Enterprise Application
โครงการหลักของระบบจัดการโครงการขององค์กร
"""

import streamlit as st
import logging
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Performance tracking
APP_START_TIME = time.time()

# ตั้งค่า path สำหรับ modules
CURRENT_DIR = Path(__file__).parent
MODULES_DIR = CURRENT_DIR / "modules"
CONFIG_DIR = CURRENT_DIR / "config"
UTILS_DIR = CURRENT_DIR / "utils"

# เพิ่ม paths เข้า sys.path
for directory in [MODULES_DIR, CONFIG_DIR, UTILS_DIR]:
    if directory.exists() and str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

# สร้าง directories ที่จำเป็น
required_dirs = ["logs", "data", "data/uploads", "data/cache", "data/temp"]
for dir_name in required_dirs:
    (CURRENT_DIR / dir_name).mkdir(parents=True, exist_ok=True)

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(CURRENT_DIR / "logs" / "app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Streamlit page config
st.set_page_config(
    page_title="SDX Project Manager | DENSO Innovation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://denso-innovation.com/help",
        "Report a bug": "mailto:innovation@denso.com",
        "About": "SDX Project Manager v2.5 | DENSO Innovation Team",
    },
)


# Import modules ด้วย error handling
def import_modules():
    """Import จำเป็นโมดูลด้วย error handling"""
    try:
        # Core modules
        from database import DatabaseManager
        from auth import (
            AuthenticationManager,
            init_session_state,
            get_current_user,
            is_admin,
        )

        # UI modules
        from ui_components import ThemeManager
        from error_handler import global_error_handler

        return {
            "DatabaseManager": DatabaseManager,
            "AuthenticationManager": AuthenticationManager,
            "ThemeManager": ThemeManager,
            "init_session_state": init_session_state,
            "get_current_user": get_current_user,
            "is_admin": is_admin,
            "error_handler": global_error_handler,
        }

    except ImportError as e:
        st.error(f"❌ **Import Error**: {str(e)}")
        st.code(
            """
        แก้ไขปัญหา:
        1. pip install -r requirements.txt
        2. ตรวจสอบไฟล์ modules ทั้งหมดมีอยู่
        3. ตรวจสอบ database connection
        """
        )
        st.stop()


# โหลด CSS และ styling
def load_enterprise_css():
    """โหลด enterprise CSS styling"""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');
    
    /* Global Variables */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --surface: #ffffff;
        --background: #f8fafc;
        --text: #1e293b;
        --text-muted: #64748b;
        --border: #e2e8f0;
    }
    
    /* Typography */
    .stApp {
        font-family: 'Noto Sans Thai', system-ui, sans-serif;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Header styling */
    .app-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        padding: 1.5rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 1rem 1rem;
        color: white;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    
    /* Cards */
    .metric-card {
        background: var(--surface);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
    }
    
    .status-active { background: var(--success); color: white; }
    .status-pending { background: var(--warning); color: white; }
    .status-completed { background: var(--primary); color: white; }
    
    /* Buttons */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--primary) 0%, var(--primary-dark) 100%);
    }
    
    /* Forms */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 0.5rem;
        border: 1px solid var(--border);
    }
    
    /* Loading */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid var(--primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .app-header {
            padding: 1rem;
            margin: -1rem -1rem 1rem -1rem;
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


# Session state management
def initialize_session():
    """เริ่มต้น session state"""
    defaults = {
        "authenticated": False,
        "user": None,
        "current_page": "dashboard",
        "managers": None,
        "login_time": None,
        "theme": "light",
        "language": "th",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Manager instances
@st.cache_resource
def get_managers():
    """สร้าง manager instances"""
    try:
        modules = import_modules()

        db_manager = modules["DatabaseManager"]()
        auth_manager = modules["AuthenticationManager"](db_manager)

        return {
            "db": db_manager,
            "auth": auth_manager,
            "error_handler": modules["error_handler"],
        }
    except Exception as e:
        logger.error(f"Failed to initialize managers: {e}")
        raise


# App header
def render_header():
    """แสดง header ของแอป"""
    st.markdown(
        f"""
    <div class="app-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin: 0; font-size: 2rem; font-weight: 700;">
                    🚀 SDX Project Manager
                </h1>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                    ระบบจัดการโครงการองค์กร | DENSO Innovation
                </p>
            </div>
            <div style="text-align: right;">
                <div style="opacity: 0.8;">📅 {datetime.now().strftime('%d/%m/%Y')}</div>
                <div style="opacity: 0.7; font-size: 0.9rem;">⏰ {datetime.now().strftime('%H:%M')}</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# Login page
def render_login():
    """หน้าเข้าสู่ระบบ"""
    st.markdown(
        """
    <div style="max-width: 400px; margin: 2rem auto; padding: 2rem; 
         background: white; border-radius: 1rem; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);">
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #1e293b; margin-bottom: 0.5rem;">🔐 เข้าสู่ระบบ</h2>
            <p style="color: #64748b;">SDX Project Manager</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("👤 ชื่อผู้ใช้", placeholder="กรอกชื่อผู้ใช้")
        password = st.text_input("🔑 รหัสผ่าน", type="password", placeholder="กรอกรหัสผ่าน")

        col1, col2 = st.columns(2)
        with col1:
            remember = st.checkbox("จดจำการเข้าสู่ระบบ")
        with col2:
            forgot = st.button("ลืมรหัสผ่าน?", type="secondary")

        login_btn = st.form_submit_button(
            "🚀 เข้าสู่ระบบ", type="primary", use_container_width=True
        )

        if login_btn:
            if not username or not password:
                st.error("❌ กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
                return

            with st.spinner("🔄 กำลังตรวจสอบ..."):
                managers = st.session_state.get("managers")
                if not managers:
                    st.error("❌ ระบบยังไม่พร้อม กรุณาลองใหม่")
                    return

                user = managers["auth"].authenticate_user(
                    username=username,
                    password=password,
                    ip_address="127.0.0.1",
                    user_agent="",
                )

                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.login_time = datetime.now()
                    st.success(
                        f"✅ ยินดีต้อนรับ {user.get('FirstName', '')} {user.get('LastName', '')}!"
                    )
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    st.markdown("</div>", unsafe_allow_html=True)

    # Demo credentials
    st.info(
        """
    **🎯 ข้อมูลทดสอบ:**
    - Admin: `admin` / `admin123`
    - Manager: `manager` / `manager123`
    - User: `user` / `user123`
    """
    )


# Navigation sidebar
def render_sidebar():
    """แสดง sidebar navigation"""
    modules = import_modules()
    user = modules["get_current_user"]()
    is_admin_user = modules["is_admin"]()

    if not user:
        return

    with st.sidebar:
        # User info
        st.markdown(
            f"""
        <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.1); 
             border-radius: 0.5rem; margin-bottom: 1rem; color: white;">
            <div style="font-size: 1.1rem; font-weight: 600;">
                👤 {user.get('FirstName', '')} {user.get('LastName', '')}
            </div>
            <div style="opacity: 0.8; font-size: 0.9rem;">{user.get('Role', 'User')}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Navigation menu
        pages = {
            "🏠 แดชบอร์ด": "dashboard",
            "📊 โครงการ": "projects",
            "✅ งาน": "tasks",
            "📈 รายงาน": "analytics",
            "📁 ไฟล์": "files",
        }

        if is_admin_user:
            pages.update({"👥 ผู้ใช้": "users", "⚙️ ตั้งค่า": "settings"})

        selected = st.selectbox(
            "📍 เมนูหลัก",
            options=list(pages.keys()),
            index=list(pages.values()).index(st.session_state.current_page),
        )

        st.session_state.current_page = pages[selected]

        # Quick actions
        st.markdown("---")
        st.markdown("**🚀 การดำเนินการด่วน**")

        if st.button("➕ โครงการใหม่", use_container_width=True):
            st.session_state.show_new_project = True

        if st.button("📝 งานใหม่", use_container_width=True):
            st.session_state.show_new_task = True

        # System info
        st.markdown("---")
        st.markdown("**📊 ข้อมูลระบบ**")

        load_time = time.time() - APP_START_TIME
        st.metric("⚡ เวลาโหลด", f"{load_time:.2f}s")

        if st.session_state.login_time:
            duration = datetime.now() - st.session_state.login_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            st.metric("🕐 เวลาออนไลน์", f"{int(hours)}:{int(minutes):02d}")

        # Logout
        st.markdown("---")
        if st.button("🚪 ออกจากระบบ", type="primary", use_container_width=True):
            # Clear session
            for key in list(st.session_state.keys()):
                if key.startswith(("authenticated", "user", "login")):
                    del st.session_state[key]
            st.rerun()


# Dashboard
def render_dashboard():
    """แสดงหน้า dashboard หลัก"""
    modules = import_modules()
    user = modules["get_current_user"]()

    if not user:
        return

    # Welcome section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
        ### 👋 สวัสดี, {user.get('FirstName', '')} {user.get('LastName', '')}
        **บทบาท:** {user.get('Role', 'User')} | **แผนก:** {user.get('Department', 'N/A')}
        """
        )

    with col2:
        if st.button("🔄 รีเฟรช", type="secondary"):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # Key metrics
    try:
        managers = st.session_state.get("managers")
        if managers:
            # Sample metrics (replace with real data)
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📊 โครงการทั้งหมด", "12", "+2")
            with col2:
                st.metric("✅ งานเสร็จสิ้น", "48", "+8")
            with col3:
                st.metric("⏳ งานค้างอยู่", "15", "-3")
            with col4:
                st.metric("👥 สมาชิกทีม", "25", "+1")

    except Exception as e:
        st.error("ไม่สามารถโหลดข้อมูลได้")
        logger.error(f"Dashboard metrics error: {e}")

    # Charts and activity
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 สถิติโครงการ")
        st.info("แผนภูมิจะแสดงเมื่อมีข้อมูล")

    with col2:
        st.subheader("🔔 กิจกรรมล่าสุด")

        # Sample activities
        activities = [
            {"desc": "โครงการ A อัพเดทสถานะ", "time": "5 นาทีที่แล้ว"},
            {"desc": "งาน B ได้รับการมอบหมาย", "time": "1 ชั่วโมงที่แล้ว"},
            {"desc": "รายงาน C ถูกส่ง", "time": "2 ชั่วโมงที่แล้ว"},
        ]

        for activity in activities:
            st.markdown(
                f"""
            <div class="metric-card" style="margin-bottom: 0.5rem; padding: 1rem;">
                <div style="font-weight: 500;">{activity['desc']}</div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">
                    📅 {activity['time']}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )


# Page router
def render_page_content():
    """จัดการการแสดงหน้าต่างๆ"""
    page = st.session_state.current_page

    if page == "dashboard":
        render_dashboard()
    elif page == "projects":
        st.subheader("📊 จัดการโครงการ")
        st.info("หน้าจัดการโครงการ - กำลังพัฒนา")
    elif page == "tasks":
        st.subheader("✅ จัดการงาน")
        st.info("หน้าจัดการงาน - กำลังพัฒนา")
    elif page == "analytics":
        st.subheader("📈 รายงานและวิเคราะห์")
        st.info("หน้ารายงาน - กำลังพัฒนา")
    elif page == "files":
        st.subheader("📁 จัดการไฟล์")
        st.info("หน้าจัดการไฟล์ - กำลังพัฒนา")
    elif page == "users":
        st.subheader("👥 จัดการผู้ใช้")
        st.info("หน้าจัดการผู้ใช้ - กำลังพัฒนา")
    elif page == "settings":
        st.subheader("⚙️ ตั้งค่าระบบ")
        st.info("หน้าตั้งค่า - กำลังพัฒนา")
    else:
        st.error("❌ ไม่พบหน้าที่ร้องขอ")


# Main application
def main():
    """ฟังก์ชันหลักของแอปพลิเคชัน"""
    try:
        # Initialize components
        load_enterprise_css()
        initialize_session()

        # Import modules
        modules = import_modules()
        modules["init_session_state"]()

        # Initialize managers
        if "managers" not in st.session_state or st.session_state.managers is None:
            with st.spinner("🔄 กำลังเริ่มต้นระบบ..."):
                st.session_state.managers = get_managers()

        # Render application
        if not st.session_state.authenticated:
            render_login()
        else:
            render_header()
            render_sidebar()
            render_page_content()

        # Performance footer
        load_time = time.time() - APP_START_TIME
        if load_time > 2.0:
            logger.warning(f"Slow page load: {load_time:.2f}s")

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(
            f"""
        🚨 **ข้อผิดพลาดระบบ**
        
        {str(e)}
        
        **วิธีแก้ไข:**
        1. ตรวจสอบการเชื่อมต่อฐานข้อมูล
        2. pip install -r requirements.txt
        3. ตรวจสอบไฟล์ configuration
        4. ดูรายละเอียดใน logs/app.log
        """
        )


# Health check
def health_check():
    """ตรวจสอบสถานะระบบ"""
    try:
        managers = st.session_state.get("managers")
        db_status = managers["db"].test_connection() if managers else False

        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Application entry point
if __name__ == "__main__":
    try:
        main()

        # Log completion
        total_time = time.time() - APP_START_TIME
        logger.info(f"Application loaded in {total_time:.2f}s")

    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        st.error("🚨 ไม่สามารถเริ่มต้นแอปพลิเคชันได้")
    finally:
        # Cleanup
        try:
            if "managers" in st.session_state and st.session_state.managers:
                if hasattr(st.session_state.managers.get("db"), "close"):
                    st.session_state.managers["db"].close()
        except Exception:
            pass
