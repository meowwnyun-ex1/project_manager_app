"""
🚀 Project Manager Pro v3.0 - Main Entry Point
Modern, Professional Project Management System
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Core imports
from core.app_initializer import AppInitializer
from core.session_manager import SessionManager
from core.router import Router
from core.error_handler import ErrorHandler
from ui.themes.theme_manager import ThemeManager

# Page configuration
st.set_page_config(
    page_title="Project Manager Pro v3.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.projectmanagerpro.com',
        'Report a bug': 'https://github.com/projectmanagerpro/issues',
        'About': """
        # Project Manager Pro v3.0 🚀
        
        **Professional Project Management System**
        
        - Modern UI/UX with Glassmorphism
        - Real-time Analytics & Reporting
        - Team Collaboration Features
        - Advanced Gantt Charts
        - SQL Server Integration
        
        Built with ❤️ using Streamlit & Python
        """
    }
)

def main():
    """Main application entry point"""
    try:
        # Initialize error handler
        error_handler = ErrorHandler()
        
        with error_handler.handle_errors():
            # Initialize core systems
            app_initializer = AppInitializer()
            session_manager = SessionManager()
            theme_manager = ThemeManager()
            router = Router()
            
            # Initialize app
            app_initializer.initialize()
            
            # Apply theme
            theme_manager.apply_theme()
            
            # Initialize session
            session_manager.initialize_session()
            
            # Route to appropriate page
            router.route()
            
    except Exception as e:
        st.error(f"⚠️ Application Error: {str(e)}")
        st.info("Please refresh the page or contact support if the issue persists.")
        
        # Show error details in development
        if os.getenv("STREAMLIT_ENV") == "development":
            st.exception(e)

if __name__ == "__main__":
    main()