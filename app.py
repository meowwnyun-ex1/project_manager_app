#!/usr/bin/env python3
"""
DENSO Project Manager Pro - Enhanced Enterprise Application
ระบบที่ปรับปรุงประสิทธิภาพและความเสถียรสำหรับระดับ Enterprise
"""

import streamlit as st
import sys
import os
import time
import logging
import traceback
import gc
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache, wraps
from typing import Dict, Any, Optional

# Performance-optimized page config
st.set_page_config(
    page_title="DENSO Project Manager Pro",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "DENSO Project Manager Pro v2.0 Enterprise"},
)

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class PerformanceTracker:
    """ติดตามประสิทธิภาพระบบแบบ real-time"""

    def __init__(self):
        self.start_time = time.time()
        self.page_loads = {}
        self.operations = {}

    def track_operation(self, name: str, duration: float):
        """บันทึกเวลาการทำงานของแต่ละ operation"""
        if name not in self.operations:
            self.operations[name] = []
        self.operations[name].append(duration)
        if len(self.operations[name]) > 10:  # Keep last 10 only
            self.operations[name] = self.operations[name][-10:]

    def get_avg_time(self, name: str) -> float:
        """คำนวณเวลาเฉลี่ย"""
        times = self.operations.get(name, [])
        return sum(times) / len(times) if times else 0.0


class EnhancedCache:
    """ระบบ cache ที่มีประสิทธิภาพสูง"""

    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str, default=None):
        """ดึงข้อมูลจาก cache"""
        if key in self.cache:
            # Check TTL
            if time.time() - self.timestamps[key] < self.ttl:
                self.hits += 1
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.timestamps[key]

        self.misses += 1
        return default

    def set(self, key: str, value: Any):
        """เก็บข้อมูลใน cache"""
        # Evict if full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """สถิติ cache performance"""
        total = self.hits + self.misses
        return {
            "hit_rate": (self.hits / total * 100) if total > 0 else 0,
            "size": len(self.cache),
            "max_size": self.max_size,
        }


def performance_monitor(operation_name: str):
    """Decorator สำหรับติดตามประสิทธิภาพ"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if "perf_tracker" in st.session_state:
                    st.session_state.perf_tracker.track_operation(
                        operation_name, duration
                    )

                # Log slow operations
                if duration > 2.0:
                    logger.warning(f"Slow operation {operation_name}: {duration:.2f}s")

        return wrapper

    return decorator


@lru_cache(maxsize=None)
def lazy_import_modules():
    """Import modules แบบ lazy loading"""
    try:
        from database_env_switcher import (
            render_environment_selector,
            get_database_manager_with_env,
        )
        from modules.auth import AuthManager
        from modules.ui_components import UIRenderer
        from modules.projects import ProjectManager
        from modules.tasks import TaskManager
        from modules.analytics import AnalyticsManager
        from modules.settings import SettingsManager
        from modules.users import UserManager
        from modules.team import TeamManager
        from utils.performance_monitor import PerformanceMonitor

        return {
            "env_selector": render_environment_selector,
            "get_db": get_database_manager_with_env,
            "managers": {
                "auth": AuthManager,
                "ui": UIRenderer,
                "projects": ProjectManager,
                "tasks": TaskManager,
                "analytics": AnalyticsManager,
                "settings": SettingsManager,
                "users": UserManager,
                "team": TeamManager,
                "performance": PerformanceMonitor,
            },
        }
    except ImportError as e:
        logger.error(f"Module import failed: {e}")
        return None


class DENSOProjectManagerPro:
    """DENSO Project Manager Pro - Enhanced Enterprise Version"""

    def __init__(self):
        """Initialize application with optimized performance"""
        self.init_start = time.time()
        self._init_session_state()
        self._init_performance_tracking()
        self._init_cache()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="denso")

        logger.info("Application initialization started")

    def _init_session_state(self):
        """Initialize session state with defaults"""
        defaults = {
            "initialized": False,
            "authenticated": False,
            "current_page": "Dashboard",
            "current_user": None,
            "last_activity": time.time(),
            "managers_loaded": False,
            "performance_mode": True,
            "auto_refresh": False,
            "theme": "professional",
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _init_performance_tracking(self):
        """Initialize performance tracking"""
        if "perf_tracker" not in st.session_state:
            st.session_state.perf_tracker = PerformanceTracker()

    def _init_cache(self):
        """Initialize caching system"""
        if "app_cache" not in st.session_state:
            st.session_state.app_cache = EnhancedCache()

    @performance_monitor("lazy_load_managers")
    def _lazy_load_managers(self):
        """Load managers only when needed"""
        if st.session_state.get("managers_loaded", False):
            return True

        try:
            modules = lazy_import_modules()
            if not modules:
                raise ImportError("Failed to load required modules")

            # Database manager
            try:
                self.db_manager = modules["get_db"]()
            except Exception as e:
                logger.warning(f"Environment switcher failed: {e}, using fallback")
                from config.database import get_database_manager

                self.db_manager = get_database_manager()

            # Initialize all managers
            managers = modules["managers"]
            self.auth_manager = managers["auth"](self.db_manager)
            self.ui_renderer = managers["ui"]()
            self.project_manager = managers["projects"](self.db_manager)
            self.task_manager = managers["tasks"](self.db_manager)
            self.analytics_manager = managers["analytics"](self.db_manager)
            self.settings_manager = managers["settings"](self.db_manager)
            self.user_manager = managers["users"](self.db_manager)
            self.team_manager = managers["team"](self.db_manager)
            self.performance_monitor = managers["performance"]()

            # Store in session state
            st.session_state.managers = {
                "db": self.db_manager,
                "auth": self.auth_manager,
                "projects": self.project_manager,
                "tasks": self.task_manager,
                "analytics": self.analytics_manager,
                "settings": self.settings_manager,
                "users": self.user_manager,
                "team": self.team_manager,
                "performance": self.performance_monitor,
            }

            st.session_state.managers_loaded = True

            init_time = time.time() - self.init_start
            logger.info(f"Managers loaded successfully in {init_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Manager loading failed: {e}")
            return False

    def run(self):
        """Main application runner"""
        page_start = time.time()

        try:
            # Session timeout check
            self._check_session_timeout()

            # Lazy load managers
            if not st.session_state.get("managers_loaded", False):
                with st.spinner("🔄 กำลังโหลดระบบ..."):
                    if not self._lazy_load_managers():
                        self._render_loading_error()
                        return

            # Render sidebar
            self._render_sidebar()

            # Authentication check
            if not self._handle_authentication():
                return

            # Main content
            self._render_main_content()

            # Footer
            self._render_footer()

        except Exception as e:
            self._handle_runtime_error(e)
        finally:
            # Performance tracking
            page_time = time.time() - page_start
            st.session_state.perf_tracker.track_operation("page_render", page_time)

            # Memory cleanup if needed
            if page_time > 3.0:
                self._cleanup_memory()

    def _check_session_timeout(self):
        """Check and handle session timeout"""
        current_time = time.time()
        last_activity = st.session_state.get("last_activity", current_time)

        if current_time - last_activity > 3600:  # 1 hour timeout
            st.session_state.clear()
            st.warning("⏰ Session หมดอายุ กรุณาเข้าสู่ระบบใหม่")
            st.stop()

        st.session_state.last_activity = current_time

    def _render_sidebar(self):
        """Render enhanced sidebar"""
        with st.sidebar:
            # Header
            st.markdown("# 🚗 DENSO PM Pro")
            st.markdown("### Enterprise Edition")

            # Environment selector
            try:
                modules = lazy_import_modules()
                if modules and "env_selector" in modules:
                    modules["env_selector"]()
            except:
                pass

            # System status
            self._render_system_status()

            # Navigation
            self._render_navigation()

            # Quick actions
            self._render_quick_actions()

    def _render_system_status(self):
        """Render system status indicators"""
        st.markdown("#### ⚡ System Status")

        col1, col2 = st.columns(2)

        # Performance metrics
        avg_load = st.session_state.perf_tracker.get_avg_time("page_render")
        cache_stats = st.session_state.app_cache.get_stats()

        with col1:
            load_indicator = (
                "🟢" if avg_load < 1.0 else "🟡" if avg_load < 3.0 else "🔴"
            )
            st.metric("Load Time", f"{avg_load:.1f}s", delta=load_indicator)

        with col2:
            hit_rate = cache_stats["hit_rate"]
            cache_indicator = "🟢" if hit_rate > 80 else "🟡" if hit_rate > 60 else "🔴"
            st.metric("Cache Hit", f"{hit_rate:.0f}%", delta=cache_indicator)

        # Database status
        db_status = (
            "🟢 Connected" if st.session_state.get("managers_loaded") else "🟡 Loading"
        )
        st.markdown(f"**Database:** {db_status}")

        # Auto-refresh toggle
        st.session_state.auto_refresh = st.toggle("Auto Refresh", value=False)

    def _render_navigation(self):
        """Render navigation menu"""
        st.markdown("#### 📋 Navigation")

        pages = {
            "📊 Dashboard": "Dashboard",
            "📁 Projects": "Projects",
            "✅ Tasks": "Tasks",
            "👥 Team": "Team",
            "📈 Analytics": "Analytics",
            "⚙️ Settings": "Settings",
            "🔧 Admin": "Admin",
        }

        current_page = st.session_state.current_page
        selected = st.radio(
            "เลือกหน้า",
            list(pages.keys()),
            index=list(pages.values()).index(current_page),
            label_visibility="collapsed",
        )

        new_page = pages[selected]
        if new_page != current_page:
            st.session_state.current_page = new_page
            st.rerun()

    def _render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("#### 🚀 Quick Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Project", use_container_width=True):
                st.session_state.current_page = "Projects"
                st.session_state.show_new_project = True
                st.rerun()

        with col2:
            if st.button("➕ Task", use_container_width=True):
                st.session_state.current_page = "Tasks"
                st.session_state.show_new_task = True
                st.rerun()

    def _handle_authentication(self) -> bool:
        """Handle authentication with caching"""
        # Check cache first
        auth_cached = st.session_state.app_cache.get("auth_status")
        if auth_cached is not None:
            return auth_cached

        if st.session_state.authenticated:
            st.session_state.app_cache.set("auth_status", True)
            return True

        # Show login form
        self._render_login()
        return False

    def _render_login(self):
        """Render optimized login form"""
        st.title("🚗 DENSO Project Manager Pro")
        st.markdown("### เข้าสู่ระบบ Enterprise Edition")

        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                username = st.text_input("👤 Username", placeholder="ชื่อผู้ใช้")
                password = st.text_input(
                    "🔒 Password", type="password", placeholder="รหัสผ่าน"
                )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    login_btn = st.form_submit_button(
                        "🔑 เข้าสู่ระบบ", type="primary", use_container_width=True
                    )

                with col_btn2:
                    demo_btn = st.form_submit_button(
                        "🎯 Demo", use_container_width=True
                    )

                if demo_btn:
                    username, password = "admin", "admin123"
                    login_btn = True

                if login_btn and username and password:
                    # Simple authentication for demo
                    if username == "admin" and password == "admin123":
                        st.session_state.authenticated = True
                        st.session_state.current_user = {
                            "username": username,
                            "name": "System Administrator",
                            "role": "Admin",
                        }
                        st.session_state.app_cache.set("auth_status", True)
                        st.success("✅ เข้าสู่ระบบสำเร็จ!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    def _render_main_content(self):
        """Render main content based on current page"""
        current_page = st.session_state.current_page

        page_functions = {
            "Dashboard": self._render_dashboard,
            "Projects": self._render_projects,
            "Tasks": self._render_tasks,
            "Team": self._render_team,
            "Analytics": self._render_analytics,
            "Settings": self._render_settings,
            "Admin": self._render_admin,
        }

        if current_page in page_functions:
            try:
                page_functions[current_page]()
            except Exception as e:
                logger.error(f"Page {current_page} error: {e}")
                self._render_page_error(current_page, e)
        else:
            st.error(f"ไม่พบหน้า {current_page}")

    @performance_monitor("dashboard_render")
    def _render_dashboard(self):
        """Render optimized dashboard"""
        st.title("📊 DENSO Project Manager Dashboard")

        # KPI Row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Projects", "12", delta="2")
        with col2:
            st.metric("Active Tasks", "45", delta="8")
        with col3:
            st.metric("Team Members", "24", delta="1")
        with col4:
            st.metric("Completion Rate", "78%", delta="5%")

        # Content tabs
        tab1, tab2, tab3 = st.tabs(["📈 Overview", "🔥 Active", "⚡ Performance"])

        with tab1:
            self._render_overview_charts()

        with tab2:
            self._render_active_items()

        with tab3:
            self._render_performance_dashboard()

    def _render_overview_charts(self):
        """Render overview charts"""
        import pandas as pd
        import plotly.express as px

        # Mock data for demo
        data = pd.DataFrame(
            {
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "Projects": [8, 10, 12, 15, 14, 12],
                "Tasks": [120, 145, 168, 180, 175, 165],
            }
        )

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(data, x="Month", y="Projects", title="Project Trends")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(data, x="Month", y="Tasks", title="Task Volume")
            st.plotly_chart(fig, use_container_width=True)

    def _render_active_items(self):
        """Render active projects and tasks"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📁 Active Projects")
            projects = [
                {"name": "DENSO Engine Module V2", "progress": 75},
                {"name": "Quality Control System", "progress": 45},
                {"name": "IoT Integration", "progress": 90},
            ]

            for proj in projects:
                st.markdown(f"**{proj['name']}**")
                st.progress(proj["progress"] / 100)
                st.markdown(f"Progress: {proj['progress']}%")
                st.divider()

        with col2:
            st.subheader("✅ Recent Tasks")
            tasks = [
                {"title": "Design Review Phase 1", "assignee": "Thammaphon C."},
                {"title": "Prototype Testing", "assignee": "Engineering Team"},
                {"title": "Documentation Update", "assignee": "Technical Writer"},
            ]

            for task in tasks:
                st.markdown(f"**{task['title']}**")
                st.markdown(f"👤 {task['assignee']}")
                st.divider()

    def _render_performance_dashboard(self):
        """Render performance monitoring dashboard"""
        st.subheader("⚡ System Performance")

        # Performance metrics
        perf_tracker = st.session_state.perf_tracker
        cache_stats = st.session_state.app_cache.get_stats()

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_render = perf_tracker.get_avg_time("page_render")
            st.metric("Avg Page Load", f"{avg_render:.2f}s")

        with col2:
            st.metric("Cache Hit Rate", f"{cache_stats['hit_rate']:.0f}%")

        with col3:
            uptime = time.time() - perf_tracker.start_time
            st.metric("Uptime", f"{uptime/60:.0f} min")

        # Performance chart
        if perf_tracker.operations:
            st.subheader("📊 Operation Performance")
            perf_data = []
            for op, times in perf_tracker.operations.items():
                avg_time = sum(times) / len(times)
                perf_data.append({"Operation": op, "Avg Time (s)": avg_time})

            if perf_data:
                import pandas as pd
                import plotly.express as px

                df = pd.DataFrame(perf_data)
                fig = px.bar(
                    df, x="Operation", y="Avg Time (s)", title="Average Operation Times"
                )
                st.plotly_chart(fig, use_container_width=True)

    def _render_projects(self):
        """Render projects page"""
        st.title("📁 Project Management")

        if hasattr(self, "project_manager"):
            try:
                self.project_manager.render_project_management()
            except Exception as e:
                logger.error(f"Project manager error: {e}")
                st.error("🚨 เกิดข้อผิดพลาดในระบบโครงการ")
        else:
            st.info("🔄 กำลังโหลดระบบจัดการโครงการ...")

    def _render_tasks(self):
        """Render tasks page"""
        st.title("✅ Task Management")

        if hasattr(self, "task_manager"):
            try:
                self.task_manager.render_task_management()
            except Exception as e:
                logger.error(f"Task manager error: {e}")
                st.error("🚨 เกิดข้อผิดพลาดในระบบงาน")
        else:
            st.info("🔄 กำลังโหลดระบบจัดการงาน...")

    def _render_team(self):
        """Render team page"""
        st.title("👥 Team Management")

        if hasattr(self, "team_manager"):
            try:
                self.team_manager.render_page()
            except Exception as e:
                logger.error(f"Team manager error: {e}")
                st.error("🚨 เกิดข้อผิดพลาดในระบบทีม")
        else:
            st.info("🔄 กำลังโหลดระบบจัดการทีม...")

    def _render_analytics(self):
        """Render analytics page"""
        st.title("📈 Analytics & Reports")

        if hasattr(self, "analytics_manager"):
            try:
                self.analytics_manager.render_analytics()
            except Exception as e:
                logger.error(f"Analytics manager error: {e}")
                st.error("🚨 เกิดข้อผิดพลาดในระบบรายงาน")
        else:
            st.info("🔄 กำลังโหลดระบบรายงาน...")

    def _render_settings(self):
        """Render settings page"""
        st.title("⚙️ System Settings")

        if hasattr(self, "settings_manager"):
            try:
                self.settings_manager.render_settings()
            except Exception as e:
                logger.error(f"Settings manager error: {e}")
                st.error("🚨 เกิดข้อผิดพลาดในระบบตั้งค่า")
        else:
            st.info("🔄 กำลังโหลดระบบตั้งค่า...")

    def _render_admin(self):
        """Render admin page"""
        st.title("🔧 System Administration")
        st.info("🔄 ระบบ Admin กำลังพัฒนา")

    def _render_page_error(self, page_name: str, error: Exception):
        """Render page error with recovery options"""
        st.title(f"🚨 ข้อผิดพลาดในหน้า {page_name}")
        st.error(f"เกิดข้อผิดพลาดขณะโหลดหน้า {page_name}")

        with st.expander("🔍 รายละเอียดข้อผิดพลาด"):
            st.code(str(error))

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 ลองใหม่", use_container_width=True):
                st.rerun()

        with col2:
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.current_page = "Dashboard"
                st.rerun()

        with col3:
            if st.button("🧹 Clear Cache", use_container_width=True):
                st.session_state.app_cache = EnhancedCache()
                st.rerun()

    def _render_loading_error(self):
        """Render loading error page"""
        st.title("🚨 ข้อผิดพลาดในการโหลดระบบ")
        st.error("ไม่สามารถโหลด modules ที่จำเป็นได้")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 ลองใหม่", type="primary", use_container_width=True):
                st.session_state.managers_loaded = False
                st.rerun()

        with col2:
            if st.button("📞 ติดต่อ Support", use_container_width=True):
                st.info("กรุณาติดต่อ: support@denso.com")

    def _render_footer(self):
        """Render performance footer"""
        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("**🚗 DENSO PM Pro v2.0**")

        with col2:
            avg_load = st.session_state.perf_tracker.get_avg_time("page_render")
            st.markdown(f"**⚡ Load:** {avg_load:.2f}s")

        with col3:
            cache_stats = st.session_state.app_cache.get_stats()
            st.markdown(f"**📊 Cache:** {cache_stats['hit_rate']:.0f}%")

        with col4:
            st.markdown(f"**🕒 Updated:** {datetime.now().strftime('%H:%M:%S')}")

    def _cleanup_memory(self):
        """Cleanup memory for better performance"""
        try:
            # Clear expired cache
            cache = st.session_state.app_cache
            current_time = time.time()
            expired_keys = []

            for key, timestamp in cache.timestamps.items():
                if current_time - timestamp > cache.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                cache.cache.pop(key, None)
                cache.timestamps.pop(key, None)

            # Force garbage collection
            gc.collect()

            logger.info(
                f"Memory cleanup: removed {len(expired_keys)} expired cache items"
            )

        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")

    def _handle_runtime_error(self, error: Exception):
        """Handle runtime errors gracefully"""
        logger.error(f"Runtime error: {error}")

        st.title("🚨 ข้อผิดพลาดระบบ")
        st.error("เกิดข้อผิดพลาดที่ไม่คาดคิด")

        with st.expander("🔍 รายละเอียดเทคนิค"):
            st.code(traceback.format_exc())

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 รีเฟรชแอป", type="primary", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        with col2:
            if st.button("🏠 กลับหน้าหลัก", use_container_width=True):
                st.session_state.current_page = "Dashboard"
                st.rerun()


def main():
    """Main application entry point with enhanced error handling"""
    try:
        # Set optimal environment variables
        os.environ.setdefault("DB_ENVIRONMENT", "local")
        os.environ.setdefault("STREAMLIT_SERVER_RUN_ON_SAVE", "false")

        # Initialize application
        app_start = time.time()
        logger.info("🚀 Starting DENSO Project Manager Pro...")

        app = DENSOProjectManagerPro()
        app.run()

        # Log startup performance
        startup_time = time.time() - app_start
        if startup_time > 3.0:
            logger.warning(f"Slow startup: {startup_time:.2f}s")
        else:
            logger.info(f"Application started successfully in {startup_time:.2f}s")

    except KeyboardInterrupt:
        logger.info("Application stopped by user")

    except Exception as e:
        logger.critical(f"Critical application failure: {e}")

        # Emergency UI for critical failures
        st.title("🚨 ระบบขัดข้องร้ายแรง")
        st.error("ระบบพบข้อผิดพลาดร้ายแรงและไม่สามารถดำเนินการต่อได้")

        # Show error details
        with st.expander("🔍 รายละเอียดข้อผิดพลาด"):
            st.code(traceback.format_exc())

        # Emergency options
        st.markdown("### 🆘 ตัวเลือกฉุกเฉิน")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "🔄 Emergency Restart", type="primary", use_container_width=True
            ):
                st.session_state.clear()
                st.rerun()

        with col2:
            if st.button("📞 ติดต่อ IT Support", use_container_width=True):
                st.markdown(
                    """
                **🔧 ฝ่าย IT Support:**
                - Tel: ext. 1234
                - Email: support@denso.com
                - Line: @denso-it
                """
                )

        with col3:
            if st.button("📋 ดาวน์โหลด Error Log", use_container_width=True):
                error_log = {
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "session_info": {
                        "session_id": id(st.session_state),
                        "user_agent": st.context.headers.get("user-agent", "Unknown"),
                        "session_state_size": len(st.session_state),
                    },
                }

                import json

                st.download_button(
                    label="💾 Download Error Report",
                    data=json.dumps(error_log, indent=2, ensure_ascii=False),
                    file_name=f"denso_error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

        # System status information
        st.markdown("### 📊 ข้อมูลระบบ")

        try:
            import psutil

            system_info = {
                "CPU Usage": f"{psutil.cpu_percent()}%",
                "Memory Usage": f"{psutil.virtual_memory().percent}%",
                "Available Memory": f"{psutil.virtual_memory().available / (1024**3):.1f} GB",
                "Python Version": sys.version.split()[0],
                "Streamlit Version": st.__version__,
            }

            for key, value in system_info.items():
                st.metric(key, value)

        except ImportError:
            st.info("ไม่สามารถดึงข้อมูลระบบได้ (psutil not available)")

    finally:
        # Final cleanup
        try:
            gc.collect()
            logger.info("Application shutdown completed")
        except:
            pass


if __name__ == "__main__":
    main()
