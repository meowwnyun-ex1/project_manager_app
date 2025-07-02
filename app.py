# app.py - Enhanced Main Entry Point for Project Manager Pro v3.0
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
    from services.enhanced_auth_service import EnhancedAuthService
    from services.enhanced_project_service import get_project_service
    from services.task_service import get_task_service
    from services.user_service import get_user_service
    from services.report_service import get_report_service

    # Import UI modules
    from ui.themes.theme_manager import get_theme_manager, apply_current_theme
    from ui.auth.login_manager import LoginManager
    from ui.navigation.enhanced_navigation import EnhancedNavigation
    from ui.components.notification_system import (
        NotificationManager,
        apply_notification_css,
        create_sample_notifications,
    )

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
    
    3. **Check Missing Files:**
    Some service files may be incomplete. Please verify all imports are working.
    """
    )
    st.stop()


class ProjectManagerApp:
    """Enhanced Project Manager Pro v3.0 Application"""

    def __init__(self):
        try:
            # Initialize configuration
            self.config = EnhancedConfig()

            # Initialize core components
            self.app_initializer = AppInitializer()
            self.session_manager = SessionManager()
            self.router = Router()
            self.error_handler = ErrorHandler()
            self.performance_monitor = PerformanceMonitor()

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
            self.performance_monitor.start_request()

            # Initialize application
            if not self._initialize_app():
                return

            # Apply notification CSS
            apply_notification_css()

            # Apply theme
            apply_current_theme()

            # Check authentication
            if not self._check_authentication():
                return

            # Render main application
            self._render_application()

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            self.error_handler.handle_error(e)

            # Show error details in debug mode
            if self.config.is_debug():
                st.exception(e)
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
                menu_items={
                    "Get Help": "https://docs.projectmanagerpro.com",
                    "Report a bug": "https://github.com/projectmanagerpro/issues",
                    "About": """
                    # Project Manager Pro v3.0
                    
                    **Enterprise-grade project management platform**
                    
                    Features:
                    - Modern glassmorphism UI
                    - Real-time collaboration
                    - Advanced analytics
                    - Team management
                    - Gantt charts
                    """,
                },
            )

            # Initialize app components
            self.app_initializer.initialize()

            # Initialize session
            self.session_manager.initialize_session()

            # Test database connection
            if not self._test_database_connection():
                return False

            # Create sample notifications for demo
            if self.config.is_debug():
                create_sample_notifications(self.notification_manager)

            return True

        except Exception as e:
            logger.error(f"App initialization failed: {str(e)}")
            st.error(f"Application initialization failed: {str(e)}")
            return False

    def _test_database_connection(self) -> bool:
        """Test database connection with enhanced feedback"""
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

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Retry Connection", use_container_width=True):
                        st.rerun()

                with col2:
                    if st.button("⚙️ Setup Database", use_container_width=True):
                        if self._setup_database():
                            st.success("Database setup completed!")
                            st.rerun()

                return False

            logger.info("Database connection successful")
            return True

        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            st.error(f"Database connection error: {str(e)}")
            return False

    def _setup_database(self) -> bool:
        """Setup database schema with progress feedback"""
        try:
            with st.spinner("Setting up database schema..."):
                success = self.db_service.setup_database()

                if success:
                    st.success("✅ Database schema created successfully!")

                    # Create default admin user if not exists
                    try:
                        admin_data = {
                            "username": "admin",
                            "email": "admin@projectmanager.local",
                            "password": "admin123",  # Should be changed on first login
                            "role": "Admin",
                        }

                        # Check if admin user already exists
                        existing_user = self.user_service.get_user_by_username("admin")
                        if not existing_user:
                            self.user_service.create_user(admin_data)
                            st.info("🔑 Default admin user created (admin/admin123)")

                    except Exception as e:
                        logger.warning(f"Could not create default admin user: {str(e)}")

                    return True
                else:
                    st.error("❌ Database setup failed!")
                    return False

        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            st.error(f"Database setup failed: {str(e)}")
            return False

    def _check_authentication(self) -> bool:
        """Check user authentication with enhanced login UI"""
        try:
            # Check if user is already authenticated
            if self.session_manager.is_authenticated():
                return True

            # Show enhanced login page
            self._render_login_page()
            return False

        except Exception as e:
            logger.error(f"Authentication check failed: {str(e)}")
            return False

    def _render_login_page(self):
        """Render enhanced login page"""
        # Apply theme to login page
        apply_current_theme()

        # Use the enhanced login manager
        self.login_manager.render()

    def _render_application(self):
        """Render main application interface"""
        try:
            # Render navigation sidebar
            selected_page = self.navigation.render()

            # Update current page in session
            if selected_page:
                self.session_manager.set_current_page(selected_page)

            # Render notification center in sidebar (optional)
            if st.sidebar.button("🔔 Notifications"):
                st.session_state.show_notifications = not st.session_state.get(
                    "show_notifications", False
                )

            # Show notifications if requested
            if st.session_state.get("show_notifications", False):
                with st.sidebar:
                    from ui.components.notification_system import (
                        render_notification_center,
                    )

                    render_notification_center(self.notification_manager)

            # Main content area
            with st.container():
                # Use enhanced router to handle page navigation
                self.router.route()

            # Footer
            self._render_footer()

        except Exception as e:
            logger.error(f"Application rendering error: {str(e)}")
            self.error_handler.handle_error(e)

    def _render_footer(self):
        """Render application footer"""
        st.markdown("---")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(
                """
            **🚀 Project Manager Pro v3.0**  
            Enterprise-grade project management platform
            """
            )

        with col2:
            # Performance metrics (if debug mode)
            if self.config.is_debug():
                metrics = self.performance_monitor.get_current_metrics()
                st.markdown(
                    f"""
                **⚡ Performance:**  
                Response Time: {metrics.get('avg_response_time', 0):.2f}s | 
                Memory: {metrics.get('memory_usage', 0):.1f}MB
                """
                )

        with col3:
            # Theme toggle
            if st.button("🎨 Themes"):
                st.session_state.show_theme_customizer = not st.session_state.get(
                    "show_theme_customizer", False
                )

        # Theme customizer modal
        if st.session_state.get("show_theme_customizer", False):
            with st.expander("🎨 Theme Customizer", expanded=True):
                self.theme_manager.render_theme_customizer()


def main():
    """Main entry point with enhanced error handling"""
    try:
        # Create and run application
        app = ProjectManagerApp()
        app.run()

    except Exception as e:
        logger.critical(f"Critical application error: {str(e)}")

        st.error(f"Critical Error: {str(e)}")

        st.info(
            """
        **Troubleshooting Steps:**
        
        1. **Check Dependencies:**
           ```bash
           pip install -r requirements.txt
           ```
        
        2. **Verify Database Connection:**
           - Ensure SQL Server is running
           - Check `.streamlit/secrets.toml` configuration
           - Test database connectivity
        
        3. **Check File Structure:**
           - Verify all required files exist
           - Check import paths
           - Ensure proper directory structure
        
        4. **Debug Mode:**
           - Set `debug = true` in configuration
           - Check logs in `app.log`
           - Review console for detailed error messages
        
        5. **Reset Application:**
           - Clear browser cache
           - Restart Streamlit server
           - Reset session state
        """
        )

        # Debug information
        with st.expander("🐛 Debug Information"):
            st.text(f"Python Version: {sys.version}")
            st.text(f"Working Directory: {os.getcwd()}")
            st.text(f"Error Time: {datetime.now()}")

            # System information
            st.text("Environment Variables:")
            for key, value in os.environ.items():
                if "streamlit" in key.lower() or "python" in key.lower():
                    st.text(f"  {key}: {value}")


if __name__ == "__main__":
    main()
