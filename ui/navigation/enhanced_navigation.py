# ui/navigation/enhanced_navigation.py
"""
Enhanced Navigation System for Project Manager Pro v3.0
Modern sidebar navigation with hover effects, user profile, and theme switching
"""

import streamlit as st
from typing import Dict, List, Optional
import time
from datetime import datetime

class EnhancedNavigation:
    """Enhanced navigation system with modern UI/UX"""
    
    def __init__(self):
        self.navigation_items = {
            "dashboard": {
                "icon": "🏠",
                "label": "Dashboard",
                "description": "Overview & Analytics"
            },
            "projects": {
                "icon": "📚",
                "label": "Projects",
                "description": "Manage Projects"
            },
            "tasks": {
                "icon": "✅",
                "label": "Tasks",
                "description": "Task Management"
            },
            "gantt": {
                "icon": "📅",
                "label": "Gantt Chart",
                "description": "Timeline View"
            },
            "team": {
                "icon": "👥",
                "label": "Team",
                "description": "Team Management"
            },
            "reports": {
                "icon": "📊",
                "label": "Reports",
                "description": "Analytics & Reports"
            },
            "settings": {
                "icon": "⚙️",
                "label": "Settings",
                "description": "System Settings"
            }
        }
        
    def render_navigation(self) -> str:
        """Render enhanced navigation sidebar"""
        # Initialize session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        if 'theme' not in st.session_state:
            st.session_state.theme = 'light'
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
            
        # Custom CSS for enhanced navigation
        self._inject_navigation_css()
        
        with st.sidebar:
            # App Header
            self._render_app_header()
            
            # User Profile Section
            self._render_user_profile()
            
            # Navigation Menu
            selected_page = self._render_navigation_menu()
            
            # Theme Switcher
            self._render_theme_switcher()
            
            # Notification Center
            self._render_notification_center()
            
            # Footer
            self._render_sidebar_footer()
            
        return selected_page
    
    def _inject_navigation_css(self):
        """Inject CSS for enhanced navigation styling"""
        st.markdown("""
        <style>
        /* Enhanced Sidebar Styling */
        .stSidebar > div:first-child {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            margin: 10px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* App Header */
        .app-header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
        }
        
        .app-title {
            font-size: 24px;
            font-weight: bold;
            color: white;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .app-subtitle {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.8);
            margin: 5px 0 0 0;
        }
        
        /* User Profile Card */
        .user-profile {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .user-profile:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        
        .user-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: white;
            margin: 0 auto 10px auto;
        }
        
        .user-info {
            text-align: center;
            color: white;
        }
        
        .username {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .user-role {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        /* Navigation Items */
        .nav-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            margin-bottom: 8px;
            transition: all 0.3s ease;
            border: 1px solid transparent;
            cursor: pointer;
        }
        
        .nav-item:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateX(5px);
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .nav-item.active {
            background: rgba(255, 255, 255, 0.2);
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        
        .nav-content {
            display: flex;
            align-items: center;
            padding: 12px 15px;
            color: white;
            text-decoration: none;
        }
        
        .nav-icon {
            font-size: 20px;
            margin-right: 12px;
            min-width: 30px;
        }
        
        .nav-text {
            flex: 1;
        }
        
        .nav-label {
            font-weight: 500;
            margin-bottom: 2px;
        }
        
        .nav-description {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        /* Theme Switcher */
        .theme-switcher {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        
        .theme-toggle {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            color: white;
        }
        
        /* Notification Center */
        .notification-center {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .notification-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
            margin-bottom: 10px;
        }
        
        .notification-badge {
            background: #ff4757;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
        
        .notification-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            color: white;
            font-size: 12px;
        }
        
        /* Sidebar Footer */
        .sidebar-footer {
            text-align: center;
            padding: 20px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.6);
            font-size: 12px;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .nav-description {
                display: none;
            }
            
            .user-profile {
                padding: 10px;
            }
            
            .nav-content {
                padding: 10px 12px;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_app_header(self):
        """Render application header"""
        st.markdown("""
        <div class="app-header">
            <h1 class="app-title">📊 ProjectManager Pro</h1>
            <p class="app-subtitle">v3.0 Enterprise Edition</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_user_profile(self):
        """Render user profile section"""
        user = st.session_state.get('user', {})
        username = user.get('username', 'Guest User')
        role = user.get('role', 'Visitor')
        
        # Get user initials for avatar
        initials = ''.join([name[0].upper() for name in username.split()[:2]])
        if not initials:
            initials = 'GU'
            
        st.markdown(f"""
        <div class="user-profile">
            <div class="user-avatar">{initials}</div>
            <div class="user-info">
                <div class="username">{username}</div>
                <div class="user-role">{role}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # User actions dropdown
        with st.expander("👤 Profile Actions", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Edit Profile", use_container_width=True):
                    st.session_state.show_profile_modal = True
            with col2:
                if st.button("🚪 Logout", use_container_width=True):
                    self._handle_logout()
    
    def _render_navigation_menu(self) -> str:
        """Render navigation menu items"""
        st.markdown("### 🧭 Navigation")
        
        selected_page = st.session_state.current_page
        
        for page_key, page_info in self.navigation_items.items():
            is_active = page_key == selected_page
            active_class = "active" if is_active else ""
            
            # Create clickable navigation item
            nav_html = f"""
            <div class="nav-item {active_class}" onclick="selectPage('{page_key}')">
                <div class="nav-content">
                    <div class="nav-icon">{page_info['icon']}</div>
                    <div class="nav-text">
                        <div class="nav-label">{page_info['label']}</div>
                        <div class="nav-description">{page_info['description']}</div>
                    </div>
                </div>
            </div>
            """
            
            st.markdown(nav_html, unsafe_allow_html=True)
            
            # Handle page selection with button (fallback for onclick)
            if st.button(f"{page_info['icon']} {page_info['label']}", 
                        key=f"nav_{page_key}", 
                        use_container_width=True,
                        type="primary" if is_active else "secondary"):
                st.session_state.current_page = page_key
                selected_page = page_key
                st.rerun()
        
        return selected_page
    
    def _render_theme_switcher(self):
        """Render theme switcher"""
        st.markdown("### 🎨 Theme")
        
        current_theme = st.session_state.get('theme', 'light')
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("☀️ Light", 
                        use_container_width=True,
                        type="primary" if current_theme == 'light' else "secondary"):
                st.session_state.theme = 'light'
                st.rerun()
        
        with col2:
            if st.button("🌙 Dark", 
                        use_container_width=True,
                        type="primary" if current_theme == 'dark' else "secondary"):
                st.session_state.theme = 'dark'
                st.rerun()
    
    def _render_notification_center(self):
        """Render notification center"""
        notifications = st.session_state.get('notifications', [])
        unread_count = len([n for n in notifications if not n.get('read', False)])
        
        st.markdown("### 🔔 Notifications")
        
        if unread_count > 0:
            st.markdown(f"""
            <div class="notification-header">
                <span>Recent Updates</span>
                <div class="notification-badge">{unread_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show recent notifications
            for notification in notifications[-3:]:  # Show last 3
                icon = "🔴" if not notification.get('read', False) else "⚪"
                st.markdown(f"""
                <div class="notification-item">
                    {icon} {notification.get('message', 'New notification')}
                    <br><small>{notification.get('time', 'Just now')}</small>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("📋 View All Notifications", use_container_width=True):
                st.session_state.show_notifications_modal = True
        else:
            st.markdown("✅ No new notifications")
    
    def _render_sidebar_footer(self):
        """Render sidebar footer"""
        current_time = datetime.now().strftime("%H:%M")
        st.markdown(f"""
        <div class="sidebar-footer">
            <div>🕐 {current_time}</div>
            <div>© 2025 ProjectManager Pro</div>
            <div>Made with ❤️ by AI</div>
        </div>
        """, unsafe_allow_html=True)
    
    def _handle_logout(self):
        """Handle user logout"""
        # Clear session state
        keys_to_clear = ['user', 'authenticated', 'current_page']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Add logout notification
        self.add_notification("👋 Successfully logged out!", "success")
        
        # Rerun to redirect to login
        st.rerun()
    
    def add_notification(self, message: str, notification_type: str = "info"):
        """Add a new notification"""
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        notification = {
            'message': message,
            'type': notification_type,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'read': False
        }
        
        st.session_state.notifications.append(notification)
        
        # Keep only last 50 notifications
        if len(st.session_state.notifications) > 50:
            st.session_state.notifications = st.session_state.notifications[-50:]
    
    def get_current_page(self) -> str:
        """Get current active page"""
        return st.session_state.get('current_page', 'dashboard')
    
    def set_current_page(self, page: str):
        """Set current active page"""
        if page in self.navigation_items:
            st.session_state.current_page = page
    
    def get_user_permissions(self) -> Dict[str, bool]:
        """Get user permissions based on role"""
        user = st.session_state.get('user', {})
        role = user.get('role', 'User')
        
        permissions = {
            'can_create_projects': role in ['Admin', 'Manager'],
            'can_delete_projects': role == 'Admin',
            'can_manage_users': role == 'Admin',
            'can_view_reports': role in ['Admin', 'Manager'],
            'can_edit_settings': role == 'Admin'
        }
        
        return permissions

# JavaScript for enhanced interactions
st.markdown("""
<script>
function selectPage(pageKey) {
    // This would be handled by Streamlit's component system
    console.log('Selected page:', pageKey);
}

// Add smooth scrolling and animations
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to navigation items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });
        
        item.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.transform = 'translateX(0)';
            }
        });
    });
});
</script>
""", unsafe_allow_html=True)