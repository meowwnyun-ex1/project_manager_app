"""
🚀 Project Manager Pro v3.0 - Application Initializer
Core system initialization and health checks
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

from config.enhanced_config import EnhancedConfig
from services.enhanced_db_service import EnhancedDBService

class AppInitializer:
    """Initialize and configure the application"""
    
    def __init__(self):
        self.config = EnhancedConfig()
        self.db_service = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup application logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/app.log', mode='a')
            ]
        )
        return logging.getLogger(__name__)
    
    def initialize(self):
        """Initialize all application components"""
        try:
            self._create_directories()
            self._initialize_session_state()
            self._check_dependencies()
            self._initialize_database()
            self._apply_custom_css()
            
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Application initialization failed: {str(e)}")
            st.error(f"⚠️ Initialization Error: {str(e)}")
            raise
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            'logs',
            'uploads',
            'exports',
            'temp',
            'backups'
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.update({
                'initialized': True,
                'user_id': None,
                'username': None,
                'user_role': None,
                'authenticated': False,
                'current_page': 'dashboard',
                'theme': 'modern_dark',
                'language': 'en',
                'last_activity': datetime.now(),
                'app_version': '3.0.0',
                'notifications': [],
                'sidebar_state': 'expanded',
                'performance_metrics': {
                    'page_loads': 0,
                    'api_calls': 0,
                    'errors': 0
                }
            })
    
    def _check_dependencies(self):
        """Check system dependencies and requirements"""
        required_modules = [
            'streamlit',
            'pandas',
            'plotly',
            'bcrypt',
            'pyodbc'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            error_msg = f"Missing required modules: {', '.join(missing_modules)}"
            self.logger.error(error_msg)
            st.error(f"⚠️ {error_msg}")
            st.info("Please install missing dependencies using: pip install -r requirements.txt")
            st.stop()
    
    def _initialize_database(self):
        """Initialize database connection and schema"""
        try:
            self.db_service = EnhancedDBService()
            
            if not self.db_service.test_connection():
                st.warning("⚠️ Database connection failed. Some features may not work.")
                st.info("""
                **Database Setup Required:**
                1. Install SQL Server
                2. Create database 'ProjectManagerPro'
                3. Update connection string in .streamlit/secrets.toml
                4. Run database setup script
                """)
            else:
                self.db_service.initialize_schema()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            st.error(f"⚠️ Database Error: {str(e)}")
    
    def _apply_custom_css(self):
        """Apply custom CSS styling"""
        css = """
        <style>
        /* 🎨 Modern Professional Styling */
        
        /* Global Styles */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Sidebar Styling */
        .css-1d391kg {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Main Content Area */
        .main .block-container {
            padding: 2rem 1rem;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            margin: 1rem;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        
        /* Cards & Metrics */
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 16px 0 rgba(31, 38, 135, 0.2);
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px 0 rgba(31, 38, 135, 0.4);
            border-color: rgba(255, 255, 255, 0.4);
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 0.5rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px 0 rgba(102, 126, 234, 0.5);
        }
        
        /* Form Elements */
        .stSelectbox > div > div > div, 
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: white;
        }
        
        /* Navigation */
        .nav-item {
            transition: all 0.3s ease;
            border-radius: 10px;
            margin: 0.2rem 0;
        }
        
        .nav-item:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(5px);
        }
        
        /* Charts */
        .js-plotly-plot .plotly .modebar {
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px);
            border-radius: 8px;
        }
        
        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translate3d(0, 40px, 0);
            }
            to {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }
        
        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }
        
        /* Status Indicators */
        .status-active { color: #10B981; }
        .status-pending { color: #F59E0B; }
        .status-completed { color: #3B82F6; }
        .status-cancelled { color: #EF4444; }
        
        /* Priority Indicators */
        .priority-critical { 
            background: linear-gradient(45deg, #EF4444, #DC2626);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .priority-high { 
            background: linear-gradient(45deg, #F59E0B, #D97706);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .priority-medium { 
            background: linear-gradient(45deg, #3B82F6, #2563EB);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .priority-low { 
            background: linear-gradient(45deg, #10B981, #059669);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        /* Loading Animations */
        .loading-spinner {
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-left: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Notification Styles */
        .notification-success {
            background: linear-gradient(45deg, #10B981, #059669);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            box-shadow: 0 4px 15px 0 rgba(16, 185, 129, 0.3);
        }
        
        .notification-error {
            background: linear-gradient(45deg, #EF4444, #DC2626);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            box-shadow: 0 4px 15px 0 rgba(239, 68, 68, 0.3);
        }
        
        .notification-warning {
            background: linear-gradient(45deg, #F59E0B, #D97706);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            box-shadow: 0 4px 15px 0 rgba(245, 158, 11, 0.3);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem 0.5rem;
                margin: 0.5rem;
            }
            
            .metric-card {
                padding: 1rem;
            }
        }
        
        /* Dark Theme Support */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            }
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def get_health_status(self):
        """Get application health status"""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': st.session_state.get('app_version', '3.0.0'),
                'components': {
                    'database': self.db_service.test_connection() if self.db_service else False,
                    'session': 'authenticated' in st.session_state,
                    'theme': 'theme' in st.session_state
                }
            }
            
            # Determine overall health
            if not all(health_status['components'].values()):
                health_status['status'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }