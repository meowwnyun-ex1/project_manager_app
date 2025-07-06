# SDX Project Manager

📁 SDX-PROJECT-MANAGER/
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 .gitignore
├── 📄 app.py # Main Streamlit application
├── 📄 clear_cache.py # Utility to clear Python cache
├── 📄 generate_keys.py # Security key generator
├── 📄 generate_bcrypt.py # Password hash generator
│
├── 📁 .streamlit/
│ ├── 📄 config.toml # Streamlit configuration
│ └── 📄 secrets.toml # Database credentials & secrets
│
├── 📁 config/
│ ├── 📄 **init**.py
│ ├── 📄 database.py # Database connection manager
│ ├── 📄 app_config.yaml # Application configuration
│ ├── 📄 database_config.yaml # Database optimization settings
│ └── 📄 file_config.yaml # File upload settings
│
├── 📁 modules/
│ ├── 📄 **init**.py
│ ├── 📄 auth.py # Authentication system
│ ├── 📄 projects.py # Project management
│ ├── 📄 tasks.py # Task management
│ ├── 📄 users.py # User management
│ ├── 📄 team.py # Team collaboration
│ ├── 📄 analytics.py # Data analytics & reporting
│ ├── 📄 notifications.py # Notification system
│ ├── 📄 settings.py # System settings
│ ├── 📄 enhanced_reports.py # Advanced analytics
│ └── 📄 gantt.py # Gantt chart visualization
│
├── 📁 utils/
│ ├── 📄 **init**.py
│ ├── 📄 ui_components.py # UI components & theme
│ ├── 📄 error_handler.py # Error handling utilities
│ ├── 📄 performance_monitor.py # Performance monitoring
│ └── 📄 file_manager.py # File management utilities
│
├── 📁 sql/
│ ├── 📄 setup.sql # Database schema creation
│ ├── 📄 insert_sample_data.sql # DENSO Innovation Team data
│ └── 📄 add_admin_user.sql # Admin user creation
│
├── 📁 static/
│ ├── 📄 config.json # Static file configuration
│ ├── 📁 images/
│ │ ├── 📄 denso-logo.png
│ │ └── 📄 sdx-banner.jpg
│ ├── 📁 css/
│ │ └── 📄 custom.css # Custom styling
│ └── 📁 js/
│ └── 📄 utils.js # JavaScript utilities
│
├── 📁 data/
│ ├── 📁 uploads/ # File uploads
│ ├── 📁 cache/ # Cached files
│ ├── 📁 exports/ # Exported reports
│ ├── 📁 backups/ # Database backups
│ └── 📁 temp/ # Temporary files
│
├── 📁 logs/
│ ├── 📄 app.log # Application logs
│ ├── 📄 error.log # Error logs
│ └── 📄 performance.log # Performance logs
│
├── 📁 tests/
│ ├── 📄 **init**.py
│ ├── 📄 test_database.py # Database tests
│ ├── 📄 test_auth.py # Authentication tests
│ └── 📄 test_performance.py # Performance tests
│
├── 📁 docs/
│ ├── 📄 README_THAI.md # Thai documentation
│ ├── 📄 DATABASE_SCHEMA.md # Database documentation
│ ├── 📄 API_REFERENCE.md # API documentation
│ ├── 📄 DEPLOYMENT_GUIDE.md # Deployment guide
│ └── 📄 USER_MANUAL.md # User manual
│
└── 📁 scripts/
├── 📄 setup_database.py # Database setup script
├── 📄 backup_database.py # Backup script
├── 📄 migrate_data.py # Data migration
└── 📄 performance_check.py # Performance monitoring script

═══════════════════════════════════════════════════════════════════

🔧 KEY FILES BREAKDOWN:

📄 CORE APPLICATION FILES:
• app.py - Main Streamlit app with professional UI
• requirements.txt - All Python dependencies
• .streamlit/secrets.toml - Database connection & security keys

📄 CONFIGURATION:
• config/database.py - Database connection management
• config/app_config.yaml - Application settings
• .streamlit/config.toml - Streamlit-specific settings

📄 MODULES (Business Logic):
• modules/auth.py - JWT authentication & password security
• modules/projects.py - Project CRUD & management
• modules/tasks.py - Task management & Kanban board
• modules/analytics.py - Data analytics & reporting
• modules/gantt.py - Gantt chart visualization

📄 UTILITIES:
• utils/ui_components.py - Modern UI components with purple theme
• utils/error_handler.py - Comprehensive error handling
• utils/performance_monitor.py - System performance tracking

📄 DATABASE:
• sql/setup.sql - Complete database schema
• sql/insert_sample_data.sql - DENSO Innovation Team data
• sql/add_admin_user.sql - Admin user creation

📄 SECURITY:
• generate_keys.py - Security key generation
• generate_bcrypt.py - Password hash generation

═══════════════════════════════════════════════════════════════════

🎯 FEATURES INCLUDED:

✅ Modern Professional UI with Purple Gradient Theme
✅ Complete Authentication System (bcrypt + JWT)
✅ Project & Task Management with Kanban Board
✅ Interactive Gantt Charts
✅ Advanced Analytics & Reporting
✅ Real-time Notifications
✅ File Upload & Management
✅ Performance Monitoring
✅ Comprehensive Error Handling
✅ Database Optimization
✅ Multi-language Support (Thai/English)
✅ Role-based Access Control
✅ Data Export (Excel, CSV, PDF)
✅ System Settings Management

🏢 DENSO-SPECIFIC FEATURES:
✅ Innovation Team Member Profiles
✅ Real DENSO Project Data
✅ Department-based Organization
✅ DENSO Branding & Theme
✅ Thai Language Interface

💾 TECH STACK:
• Frontend: Streamlit + Custom CSS + Plotly
• Backend: Python + SQLAlchemy + bcrypt
• Database: SQL Server + LocalDB support
• Authentication: JWT + Session management
• Visualization: Plotly + Gantt charts
• Performance: psutil monitoring
• Security: bcrypt + CSRF protection

📊 DATABASE TABLES:
• Users, Projects, Tasks, ProjectMembers
• TimeTracking, Comments, Notifications
• SystemSettings, Audit logs

🚀 QUICK START:

1. pip install -r requirements.txt
2. Update .streamlit/secrets.toml
3. Run sql/setup.sql
4. streamlit run app.py
5. Login: admin/admin123

📋 ADMIN CREDENTIALS:
• Username: admin
• Password: admin123
• Role: Admin
• Department: IT
