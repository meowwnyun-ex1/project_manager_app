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

    # Import services - Fixed import names
    from services.enhanced_db_service import (
        get_db_service,
    )  # This returns EnhancedDatabaseService
    from services.enhanced_auth_service import EnhancedAuthService
    from services.enhanced_project_service import get_project_service
    from services.task_service import get_task_service
    from services.user_service import get_user_service
    from services.report_service import get_report_service

    # Import UI modules
    from ui.themes.theme_manager import get_theme_manager, apply_current_theme
    from ui.auth.login_manager import LoginManager
    from ui.navigation.enhanced_navigation import EnhancedNavigation
    from ui.components.notification_system import NotificationManager

    # Import configuration
    from config.enhanced_config import EnhancedConfig

except ImportError as e:
    st.error(f"Failed to import required modules: {str(e)}")
    st.info(
        """
    **Setup Instructions:**
    
    1. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    
    2. **Setup Database Configuration:**
    - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
    - Update database connection settings
    
    3. **Create Missing Files:**
    Some service files may be incomplete. Please check:
    - `services/enhanced_project_service.py`
    - `core/error_handler.py`
    - `core/performance_monitor.py`
    - `ui/auth/login_manager.py`
    """
    )
    st.stop()


class ProjectManagerApp:
    """Main Project Manager Pro v3.0 Application"""

    def __init__(self):
        try:
            self.config = EnhancedConfig()
            self.app_initializer = AppInitializer()
            self.session_manager = SessionManager()
            self.router = Router()

            # Initialize notification system
            self.notification_manager = NotificationManager()

            # Initialize theme manager
            self.theme_manager = get_theme_manager()

            # Initialize services
            self.db_service = get_db_service()

            # Create auth service with connection string
            connection_string = self.config.get_database_connection_string()
            self.auth_service = EnhancedAuthService(connection_string)

            self.project_service = get_project_service()
            self.task_service = get_task_service()
            self.user_service = get_user_service()
            self.report_service = get_report_service()

            # UI components
            self.login_manager = LoginManager()
            self.navigation = EnhancedNavigation()

            logger.info("Project Manager Pro v3.0 initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}")
            st.error(f"Application initialization failed: {str(e)}")
            st.info("Please check your configuration and database connection.")
            raise

    def run(self):
        """Main application entry point"""
        try:
            # Start performance monitoring
            if hasattr(self, "performance_monitor"):
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
            logger.error(f"Application error: {str(e)}")
            st.error(f"An error occurred: {str(e)}")

            # Show error details in debug mode
            if self.config.is_debug():
                st.exception(e)
        finally:
            # End performance monitoring
            if hasattr(self, "performance_monitor"):
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
            self.app_initializer.initialize()

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
                - Check `.streamlit/secrets.toml` file
                - Verify server address and credentials
                
                **Setup Instructions:**
                1. Install SQL Server or SQL Server Express
                2. Create database: `ProjectManagerPro`
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

    def _setup_database(self) -> bool:
        """Setup database schema"""
        try:
            return self.db_service.setup_database()
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            st.error(f"Database setup failed: {str(e)}")
            return False

    def _check_authentication(self) -> bool:
        """Check user authentication"""
        try:
            # Check if user is already authenticated
            if self.session_manager.is_authenticated():
                return True

            # Show login page
            self._render_login_page()
            return False

        except Exception as e:
            logger.error(f"Authentication check failed: {str(e)}")
            return False

    def _render_login_page(self):
        """Render login page"""
        st.markdown(
            """
        <div style="text-align: center; padding: 2rem;">
            <h1>🚀 Project Manager Pro v3.0</h1>
            <p style="font-size: 1.2rem; color: #64748b;">
                Professional Project Management System
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Simple login form for demo
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                st.markdown("### 🔐 Login")
                username = st.text_input("Username", value="admin")
                password = st.text_input("Password", type="password", value="admin")

                if st.form_submit_button("Login", use_container_width=True):
                    # Simple demo authentication
                    if username == "admin" and password == "admin":
                        # Mock user data
                        user_data = {
                            "user_id": 1,
                            "username": "admin",
                            "role": "Admin",
                            "first_name": "Admin",
                            "last_name": "User",
                            "email": "admin@projectmanager.local",
                        }

                        if self.session_manager.login_user(user_data):
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Login failed!")
                    else:
                        st.error("Invalid credentials! Use admin/admin for demo.")

        # Demo info
        st.info(
            """
        **Demo Credentials:**
        - Username: `admin`
        - Password: `admin`
        
        **Features:**
        - Modern glassmorphism UI
        - Real-time analytics
        - Interactive Gantt charts
        - Team collaboration tools
        """
        )

    def _render_application(self):
        """Render main application interface"""
        try:
            # Use router to handle page navigation
            self.router.route()

        except Exception as e:
            logger.error(f"Application rendering error: {str(e)}")
            st.error(f"Error rendering application: {str(e)}")


def main():
    """Main entry point"""
    try:
        # Create and run application
        app = ProjectManagerApp()
        app.run()

    except Exception as e:
        st.error(f"Failed to start application: {str(e)}")
        st.info(
            """
        **Troubleshooting:**
        
        1. Check that all required files exist
        2. Verify database connection settings
        3. Install all dependencies: `pip install -r requirements.txt`
        4. Check the console for detailed error messages
        """
        )


if __name__ == "__main__":
    main()
