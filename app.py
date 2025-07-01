# app.py - Main Entry Point for Project Manager Pro v3.0
import streamlit as st
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Import core modules
try:
    from core.app_initializer import AppInitializer
    from core.session_manager import SessionManager
    from core.router import Router
    from core.error_handler import ErrorHandler
    from core.performance_monitor import PerformanceMonitor

    # Import services
    from services.enhanced_db_service import get_db_service
    from services.enhanced_auth_service import get_auth_service
    from services.enhanced_project_service import get_project_service
    from services.task_service import get_task_service
    from services.user_service import get_user_service
    from services.report_service import get_report_service

    # Import UI modules
    from ui.themes.theme_manager import get_theme_manager, apply_current_theme
    from ui.auth.login_manager import LoginManager
    from ui.navigation.enhanced_navigation import EnhancedNavigation
    from ui.components.notification_system import NotificationSystem

    # Import configuration
    from config.enhanced_config import get_config

except ImportError as e:
    st.error(f"Failed to import required modules: {str(e)}")
    st.stop()


class ProjectManagerApp:
    """Main Project Manager Pro v3.0 Application"""

    def __init__(self):
        self.config = get_config()
        self.app_initializer = AppInitializer()
        self.session_manager = SessionManager()
        self.router = Router()
        self.error_handler = ErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        self.theme_manager = get_theme_manager()
        self.notification_system = NotificationSystem()

        # Initialize services
        self.db_service = get_db_service()
        self.auth_service = get_auth_service()
        self.project_service = get_project_service()
        self.task_service = get_task_service()
        self.user_service = get_user_service()
        self.report_service = get_report_service()

        # UI components
        self.login_manager = LoginManager()
        self.navigation = EnhancedNavigation()

        logger.info("Project Manager Pro v3.0 initialized successfully")

    def run(self):
        """Main application entry point"""
        try:
            # Start performance monitoring
            self.performance_monitor.start_request()

            # Initialize application
            if not self._initialize_app():
                return

            # Apply theme
            apply_current_theme()

            # Check authentication
            if not self._check_authentication():
                return

            # Render main application
            self._render_application()

        except Exception as e:
            self.error_handler.handle_error(e)
        finally:
            # End performance monitoring
            self.performance_monitor.end_request()

    def _initialize_app(self) -> bool:
        """Initialize application and check prerequisites"""
        try:
            # Set page configuration
            st.set_page_config(
                page_title="Project Manager Pro v3.0",
                page_icon="🚀",
                layout="wide",
                initial_sidebar_state="expanded",
            )

            # Initialize app components
            if not self.app_initializer.initialize():
                st.error(
                    "Failed to initialize application. Please check system requirements."
                )
                return False

            # Initialize session
            self.session_manager.initialize_session()

            # Test database connection
            if not self._test_database_connection():
                return False

            return True

        except Exception as e:
            logger.error(f"App initialization failed: {str(e)}")
            st.error(f"Application initialization failed: {str(e)}")
            return False

    def _test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.db_service.connection_manager.test_connection():
                st.error(
                    """
                ### 🔴 Database Connection Failed
                
                Please ensure SQL Server is running and connection details are correct.
                
                **Connection Settings:**
                - Server: localhost
                - Database: ProjectManagerDB
                - Check `.streamlit/secrets.toml` file
                
                **Setup Instructions:**
                1. Install SQL Server or SQL Server Express
                2. Create database: `ProjectManagerDB`
                3. Update connection settings in secrets.toml
                4. Run setup script to create tables
                """
                )

                if st.button("🔄 Retry Connection"):
                    st.rerun()

                if st.button("⚙️ Setup Database"):
                    if self._setup_database():
                        st.success("Database setup completed!")
                        st.rerun()

                return False

            return True

        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            st.error(f"Database connection error: {str(e)}")
            return False
