# ui/navigation/enhanced_navigation.py
import streamlit as st
from core.session_manager import SessionManager


class EnhancedNavigation:
    """Enhanced navigation system"""

    def __init__(self):
        self.session_manager = SessionManager()

    def render(self):
        """Render enhanced navigation sidebar"""
        self._inject_navigation_css()

        with st.sidebar:
            # App header
            self._render_app_header()

            # User profile
            self._render_user_profile()

            # Navigation menu
            selected_page = self._render_navigation_menu()

            # Footer
            self._render_footer()

        return selected_page

    def _inject_navigation_css(self):
        """Inject CSS for navigation styling"""
        st.markdown(
            """
        <style>
        /* Enhanced Sidebar Styling */
        .css-1d391kg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .sidebar-content {
            padding: 1rem;
        }
        
        /* App Header */
        .nav-header {
            text-align: center;
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 1rem;
        }
        
        .nav-title {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            margin: 0;
        }
        
        .nav-subtitle {
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.8rem;
            margin: 0;
        }
        
        /* User Profile */
        .user-profile {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .user-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            margin: 0 auto 0.5rem auto;
        }
        
        .username {
            color: white;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .user-role {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.8rem;
        }
        
        /* Navigation Items */
        .nav-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .nav-item:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateX(5px);
        }
        
        .nav-item.active {
            background: rgba(255, 255, 255, 0.3);
        }
        
        /* Footer */
        .nav-footer {
            text-align: center;
            padding: 1rem 0;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            margin-top: 1rem;
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.8rem;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_app_header(self):
        """Render app header"""
        st.markdown(
            """
        <div class="nav-header">
            <h1 class="nav-title">📊 PM Pro</h1>
            <p class="nav-subtitle">v3.0</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_user_profile(self):
        """Render user profile"""
        user_name = self.session_manager.get_user_full_name()
        role = self.session_manager.get_user_role()

        # Get initials
        initials = "".join([name[0].upper() for name in user_name.split()[:2]])
        if not initials:
            initials = "U"

        st.markdown(
            f"""
        <div class="user-profile">
            <div class="user-avatar">{initials}</div>
            <div class="username">{user_name}</div>
            <div class="user-role">{role}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_navigation_menu(self) -> str:
        """Render navigation menu"""
        menu_items = [
            {"key": "dashboard", "icon": "🏠", "label": "Dashboard"},
            {"key": "projects", "icon": "📚", "label": "Projects"},
            {"key": "tasks", "icon": "✅", "label": "Tasks"},
            {"key": "gantt", "icon": "📅", "label": "Gantt Chart"},
            {"key": "team", "icon": "👥", "label": "Team"},
            {"key": "reports", "icon": "📊", "label": "Reports"},
            {"key": "settings", "icon": "⚙️", "label": "Settings"},
        ]

        current_page = self.session_manager.get_current_page()

        for item in menu_items:
            if st.button(
                f"{item['icon']} {item['label']}",
                key=f"nav_{item['key']}",
                use_container_width=True,
                type="primary" if current_page == item["key"] else "secondary",
            ):
                self.session_manager.set_current_page(item["key"])
                return item["key"]

        return current_page

    def _render_footer(self):
        """Render navigation footer"""
        if st.button("🚪 Logout", use_container_width=True):
            self.session_manager.logout_user()
            st.rerun()

        st.markdown(
            """
        <div class="nav-footer">
            © 2025 Project Manager Pro
        </div>
        """,
            unsafe_allow_html=True,
        )
