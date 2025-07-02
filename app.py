# app.py
"""
🚀 DENSO Project Manager Pro - Main Application Entry Point
Enterprise-grade project management platform with modern UI/UX and real-time collaboration

Version: 2.0.0
Author: DENSO Development Team
License: Proprietary
"""

import streamlit as st
import sys
import os
import logging
from datetime import datetime
import traceback

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import application modules
try:
    from enhanced_app import EnhancedProjectManagerApp
    from database_service import get_database_service
    from config_manager import get_config_manager
    from error_handler import get_error_handler, handle_streamlit_errors
    from performance_manager import get_performance_manager
except ImportError as e:
    st.error(f"❌ Failed to import required modules: {str(e)}")
    st.stop()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application configuration
APP_CONFIG = {
    "page_title": "DENSO Project Manager Pro",
    "page_icon": "🚀",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        "Get Help": "https://denso.com/support",
        "Report a bug": "https://denso.com/support/bug-report",
        "About": """
        # DENSO Project Manager Pro v2.0.0
        
        **Enterprise Project Management Platform**
        
        Features:
        - 📊 Real-time Analytics
        - 👥 Team Collaboration  
        - 📈 Performance Monitoring
        - 🔒 Advanced Security
        - 📱 Responsive Design
        
        © 2025 DENSO Corporation
        """,
    },
}


def configure_streamlit():
    """Configure Streamlit application settings"""
    try:
        st.set_page_config(**APP_CONFIG)

        # Hide Streamlit branding
        hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)

        # Custom CSS for enhanced styling
        custom_css = """
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global font family */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        /* Main container styling */
        .main {
            padding-top: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #2E3440 0%, #3B4252 100%);
        }
        
        /* Loading animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stApp > div {
            animation: fadeIn 0.6s ease-out;
        }
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

        logger.info("Streamlit configuration applied successfully")

    except Exception as e:
        logger.error(f"Failed to configure Streamlit: {str(e)}")
        st.error("Configuration error occurred")


def check_system_requirements():
    """Check system requirements and dependencies"""
    requirements_met = True
    issues = []

    try:
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 9):
            requirements_met = False
            issues.append(
                f"Python 3.9+ required (current: {python_version.major}.{python_version.minor})"
            )

        # Check required modules
        required_modules = [
            "streamlit",
            "pandas",
            "plotly",
            "pyodbc",
            "bcrypt",
            "pydantic",
            "yaml",
            "psutil",
        ]

        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
                requirements_met = False

        if missing_modules:
            issues.append(f"Missing modules: {', '.join(missing_modules)}")

        # Check database connectivity
        try:
            db_service = get_database_service()
            if not db_service.connection_manager.test_connection():
                requirements_met = False
                issues.append("Database connection failed")
        except Exception as e:
            requirements_met = False
            issues.append(f"Database check failed: {str(e)}")

        return requirements_met, issues

    except Exception as e:
        logger.error(f"System requirements check failed: {str(e)}")
        return False, [f"Requirements check error: {str(e)}"]


def show_system_status():
    """Display system status and health information"""
    st.sidebar.markdown("---")

    with st.sidebar.expander("🏥 System Status", expanded=False):
        # System health indicators
        requirements_met, issues = check_system_requirements()

        if requirements_met:
            st.success("🟢 All systems operational")
        else:
            st.error("🔴 System issues detected")
            for issue in issues:
                st.error(f"• {issue}")

        # Performance metrics
        try:
            performance_manager = get_performance_manager()
            metrics = performance_manager.get_performance_metrics()

            if metrics:
                st.metric(
                    "Memory Usage",
                    f"{metrics.get('system_metrics', {}).get('memory_percent', 0):.1f}%",
                )
                st.metric(
                    "CPU Usage",
                    f"{metrics.get('system_metrics', {}).get('cpu_percent', 0):.1f}%",
                )
        except Exception as e:
            st.warning(f"Performance metrics unavailable: {str(e)}")

        # Last updated
        st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")


def show_loading_screen():
    """Show application loading screen"""
    loading_container = st.empty()

    with loading_container.container():
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown(
                """
            <div style="text-align: center; padding: 50px;">
                <h1 style="color: white; font-size: 3rem; margin-bottom: 20px;">
                    🚀 DENSO Project Manager Pro
                </h1>
                <div style="color: rgba(255,255,255,0.8); font-size: 1.2rem; margin-bottom: 30px;">
                    Loading your workspace...
                </div>
                <div style="background: rgba(255,255,255,0.2); height: 4px; border-radius: 2px; overflow: hidden;">
                    <div style="background: white; height: 100%; width: 0%; animation: loading 2s ease-in-out infinite;">
                    </div>
                </div>
            </div>
            
            <style>
            @keyframes loading {
                0% { width: 0%; }
                50% { width: 70%; }
                100% { width: 100%; }
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

    return loading_container


def handle_application_error(error: Exception, context: str = ""):
    """Handle application-level errors"""
    error_handler = get_error_handler()
    error_id = error_handler.handle_error(
        error, additional_data={"context": context, "user_agent": "Streamlit"}
    )

    st.error(
        f"""
    ### ❌ Application Error
    
    An unexpected error occurred while {context}.
    
    **Error ID:** `{error_id}`
    
    **What you can do:**
    1. Refresh the page and try again
    2. Check your internet connection
    3. Contact support if the problem persists
    
    **Error Details:** {str(error)}
    """
    )

    # Show error details in expander for debugging
    with st.expander("🔧 Technical Details", expanded=False):
        st.code(traceback.format_exc())


def initialize_application():
    """Initialize the main application"""
    try:
        # Show loading screen
        loading_container = show_loading_screen()

        # Check system requirements
        requirements_met, issues = check_system_requirements()

        if not requirements_met:
            loading_container.empty()
            st.error("### ❌ System Requirements Not Met")
            for issue in issues:
                st.error(f"• {issue}")

            st.markdown(
                """
            ### 🔧 How to Fix:
            1. **Install missing dependencies:** `pip install -r requirements.txt`
            2. **Check database connection:** Verify `.streamlit/secrets.toml`
            3. **Update Python:** Ensure Python 3.9+ is installed
            4. **Contact Support:** If issues persist
            """
            )
            st.stop()

        # Initialize configuration manager
        config_manager = get_config_manager()
        config = config_manager.get_config()

        # Initialize performance manager
        performance_manager = get_performance_manager()
        performance_manager.setup_monitoring()

        # Initialize enhanced application
        app = EnhancedProjectManagerApp()

        # Clear loading screen
        loading_container.empty()

        return app, config

    except Exception as e:
        handle_application_error(e, "initializing the application")
        st.stop()


def show_maintenance_mode():
    """Show maintenance mode screen"""
    st.markdown(
        """
    <div style="text-align: center; padding: 100px 20px;">
        <h1 style="color: white; font-size: 3rem; margin-bottom: 30px;">
            🔧 Under Maintenance
        </h1>
        <div style="color: rgba(255,255,255,0.9); font-size: 1.3rem; margin-bottom: 40px;">
            We're updating the system to serve you better.
        </div>
        <div style="color: rgba(255,255,255,0.7); font-size: 1rem;">
            Expected completion: 30 minutes<br>
            Thank you for your patience.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_error_boundary():
    """Show error boundary for unhandled exceptions"""
    st.markdown(
        """
    <div style="text-align: center; padding: 100px 20px;">
        <h1 style="color: #ff6b6b; font-size: 3rem; margin-bottom: 30px;">
            ⚠️ Something Went Wrong
        </h1>
        <div style="color: rgba(255,255,255,0.9); font-size: 1.2rem; margin-bottom: 40px;">
            An unexpected error occurred. Please try refreshing the page.
        </div>
        <button onclick="window.location.reload()" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.1rem;
            cursor: pointer;
            margin-right: 15px;
        ">
            🔄 Refresh Page
        </button>
        <button onclick="window.location.href='mailto:support@denso.com'" style="
            background: transparent;
            color: white;
            border: 2px solid white;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.1rem;
            cursor: pointer;
        ">
            📧 Contact Support
        </button>
    </div>
    """,
        unsafe_allow_html=True,
    )


def main():
    """Main application entry point"""
    try:
        # Configure Streamlit
        configure_streamlit()

        # Initialize session state for error tracking
        if "error_count" not in st.session_state:
            st.session_state.error_count = 0

        # Check for maintenance mode
        config_manager = get_config_manager()
        if config_manager.get_config().environment == "maintenance":
            show_maintenance_mode()
            return

        # Error boundary - if too many errors, show error screen
        if st.session_state.error_count > 5:
            show_error_boundary()
            return

        # Initialize and run application
        app, config = initialize_application()

        # Show system status in sidebar
        show_system_status()

        # Handle Streamlit errors
        handle_streamlit_errors()

        # Run the main application
        with get_performance_manager().measure_time("main_app_execution"):
            app.run()

        # Log successful execution
        logger.info("Application executed successfully")

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        st.info("👋 Application stopped by user")

    except SystemExit:
        logger.info("Application system exit")
        pass

    except Exception as e:
        # Increment error count
        st.session_state.error_count += 1

        # Log critical error
        logger.critical(f"Critical application error: {str(e)}")
        logger.critical(traceback.format_exc())

        # Handle error
        handle_application_error(e, "running the main application")

        # If too many errors, suggest restart
        if st.session_state.error_count > 3:
            st.warning(
                """
            ### ⚠️ Multiple Errors Detected
            
            The application has encountered several errors. Consider:
            1. Refreshing the page completely
            2. Clearing browser cache
            3. Checking system requirements
            4. Contacting technical support
            """
            )


def health_check():
    """Application health check endpoint"""
    try:
        # Test database connection
        db_service = get_database_service()
        db_healthy = db_service.connection_manager.test_connection()

        # Test performance manager
        performance_manager = get_performance_manager()
        perf_healthy = performance_manager is not None

        # Overall health
        healthy = db_healthy and perf_healthy

        status = {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "components": {
                "database": "healthy" if db_healthy else "unhealthy",
                "performance_manager": "healthy" if perf_healthy else "unhealthy",
            },
        }

        return status

    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


if __name__ == "__main__":
    try:
        # Set up logging for production
        if os.getenv("ENVIRONMENT") == "production":
            logging.basicConfig(
                level=logging.WARNING,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
            )

        # Check if running health check
        if len(sys.argv) > 1 and sys.argv[1] == "--health":
            health_status = health_check()
            print(f"Health Status: {health_status['status']}")
            sys.exit(0 if health_status["status"] == "healthy" else 1)

        # Run main application
        main()

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
