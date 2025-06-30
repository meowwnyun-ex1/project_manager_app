"""
🚀 Project Manager Pro v3.0 - Router
Advanced page routing and navigation system
"""

import streamlit as st
from typing import Dict, Any, Callable
import logging

from core.session_manager import SessionManager
from ui.auth.login_manager import LoginManager
from ui.pages.enhanced_dashboard import EnhancedDashboard
from ui.pages.enhanced_projects import EnhancedProjects
from ui.pages.enhanced_tasks import EnhancedTasks
from ui.pages.enhanced_gantt import EnhancedGantt
from ui.pages.enhanced_reports import EnhancedReports
from ui.pages.enhanced_team import EnhancedTeam
from ui.pages.enhanced_settings import EnhancedSettings
from ui.navigation.enhanced_navigation import EnhancedNavigation

class Router:
    """Advanced routing system with authentication and permission checking"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.logger = logging.getLogger(__name__)
        self.navigation = EnhancedNavigation()
        
        # Define page classes
        self.pages = {
            'login': LoginManager,
            'dashboard': EnhancedDashboard,
            'projects': EnhancedProjects,
            'tasks': EnhancedTasks,
            'gantt': EnhancedGantt,
            'reports': EnhancedReports,
            'team': EnhancedTeam,
            'settings': EnhancedSettings
        }
        
        # Define page permissions
        self.page_permissions = {
            'dashboard': [],  # No special permissions required
            'projects': [],
            'tasks': [],
            'gantt': [],
            'reports': ['view_reports'],
            'team': ['manage_team'],
            'settings': ['admin_access']
        }
        
        # Define public pages (no authentication required)
        self.public_pages = {'login'}
    
    def route(self) -> None:
        """Main routing logic"""
        try:
            # Get requested page
            requested_page = self._get_requested_page()
            
            # Check authentication
            if not self._is_page_accessible(requested_page):
                self._redirect_to_login()
                return
            
            # Update session with current page
            self.session_manager.set_current_page(requested_page)
            
            # Render page
            self._render_page(requested_page)
            
        except Exception as e:
            self.logger.error(f"Routing error: {str(e)}")
            self._render_error_page(str(e))
    
    def _get_requested_page(self) -> str:
        """Get the requested page from various sources"""
        # Priority order: URL params -> session state -> default
        
        # Check URL parameters
        query_params = st.experimental_get_query_params()
        if 'page' in query_params:
            page = query_params['page'][0]
            if page in self.pages:
                return page
        
        # Check session state
        if self.session_manager.is_authenticated():
            return self.session_manager.get_current_page()
        
        # Default to login if not authenticated
        return 'login'
    
    def _is_page_accessible(self, page: str) -> bool:
        """Check if user can access the requested page"""
        # Public pages are always accessible
        if page in self.public_pages:
            return True
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            return False
        
        # Check page permissions
        required_permissions = self.page_permissions.get(page, [])
        if required_permissions:
            for permission in required_permissions:
                if not self.session_manager.has_permission(permission):
                    return False
        
        return True
    
    def _redirect_to_login(self) -> None:
        """Redirect to login page"""
        self.session_manager.set_current_page('login')
        self._render_page('login')
    
    def _render_page(self, page: str) -> None:
        """Render the requested page"""
        try:
            # Get page class
            page_class = self.pages.get(page)
            if not page_class:
                raise ValueError(f"Page '{page}' not found")
            
            # Render navigation (except for login page)
            if page != 'login' and self.session_manager.is_authenticated():
                self.navigation.render()
            
            # Create and render page instance
            page_instance = page_class()
            page_instance.render()
            
            # Update performance metrics
            self.session_manager.update_performance_metric('page_loads')
            
        except Exception as e:
            self.logger.error(f"Page rendering error for '{page}': {str(e)}")
            self._render_error_page(f"Error loading page '{page}': {str(e)}")
    
    def _render_error_page(self, error_message: str) -> None:
        """Render error page"""
        st.error("🚨 **Application Error**")
        st.error(error_message)
        
        if st.button("🏠 Return to Dashboard"):
            self.navigate_to('dashboard')
        
        if st.button("🔄 Refresh Page"):
            st.experimental_rerun()
        
        # Show error details in development
        if st.session_state.get('debug_mode', False):
            with st.expander("🐛 Debug Information"):
                st.code(error_message)
                st.json(st.session_state.to_dict())
    
    def navigate_to(self, page: str, **kwargs) -> None:
        """Navigate to a specific page"""
        try:
            if page not in self.pages:
                raise ValueError(f"Invalid page: {page}")
            
            # Check if page is accessible
            if not self._is_page_accessible(page):
                st.error("⚠️ You don't have permission to access this page.")
                return
            
            # Update URL parameters
            st.experimental_set_query_params(page=page, **kwargs)
            
            # Update session
            self.session_manager.set_current_page(page)
            
            # Trigger rerun to navigate
            st.experimental_rerun()
            
        except Exception as e:
            self.logger.error(f"Navigation error: {str(e)}")
            st.error(f"Navigation failed: {str(e)}")
    
    def get_page_url(self, page: str, **params) -> str:
        """Get URL for a specific page"""
        base_url = st.get_option("server.baseUrlPath") or ""
        query_string = f"?page={page}"
        
        if params:
            for key, value in params.items():
                query_string += f"&{key}={value}"
        
        return f"{base_url}{query_string}"
    
    def get_navigation_items(self) -> list:
        """Get navigation items based on user permissions"""
        user_role = self.session_manager.get_user_role()
        
        # Base navigation items
        nav_items = [
            {
                'name': 'Dashboard',
                'page': 'dashboard',
                'icon': '🏠',
                'description': 'Overview and metrics'
            },
            {
                'name': 'Projects',
                'page': 'projects',
                'icon': '📁',
                'description': 'Manage projects'
            },
            {
                'name': 'Tasks',
                'page': 'tasks',
                'icon': '✅',
                'description': 'Task management'
            },
            {
                'name': 'Gantt Chart',
                'page': 'gantt',
                'icon': '📊',
                'description': 'Project timeline'
            }
        ]
        
        # Add role-specific items
        if self.session_manager.has_permission('view_reports'):
            nav_items.append({
                'name': 'Reports',
                'page': 'reports',
                'icon': '📈',
                'description': 'Analytics and reports'
            })
        
        if self.session_manager.has_permission('manage_team'):
            nav_items.append({
                'name': 'Team',
                'page': 'team',
                'icon': '👥',
                'description': 'Team management'
            })
        
        if self.session_manager.has_permission('admin_access'):
            nav_items.append({
                'name': 'Settings',
                'page': 'settings',
                'icon': '⚙️',
                'description': 'System settings'
            })
        
        return nav_items
    
    def get_breadcrumbs(self) -> list:
        """Get breadcrumb navigation"""
        current_page = self.session_manager.get_current_page()
        breadcrumbs = [{'name': 'Home', 'page': 'dashboard'}]
        
        page_titles = {
            'dashboard': 'Dashboard',
            'projects': 'Projects',
            'tasks': 'Tasks',
            'gantt': 'Gantt Chart',
            'reports': 'Reports',
            'team': 'Team',
            'settings': 'Settings'
        }
        
        if current_page != 'dashboard' and current_page in page_titles:
            breadcrumbs.append({
                'name': page_titles[current_page],
                'page': current_page
            })
        
        return breadcrumbs
    
    def handle_404(self) -> None:
        """Handle 404 page not found"""
        st.error("🚨 **Page Not Found**")
        st.info("The requested page could not be found.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 Dashboard"):
                self.navigate_to('dashboard')
        
        with col2:
            if st.button("📁 Projects"):
                self.navigate_to('projects')
        
        with col3:
            if st.button("✅ Tasks"):
                self.navigate_to('tasks')
    
    def get_current_route_info(self) -> Dict[str, Any]:
        """Get information about current route"""
        current_page = self.session_manager.get_current_page()
        
        return {
            'page': current_page,
            'title': self._get_page_title(current_page),
            'permissions': self.page_permissions.get(current_page, []),
            'is_accessible': self._is_page_accessible(current_page),
            'breadcrumbs': self.get_breadcrumbs(),
            'url': self.get_page_url(current_page)
        }
    
    def _get_page_title(self, page: str) -> str:
        """Get title for a page"""
        titles = {
            'login': 'Login',
            'dashboard': 'Dashboard',
            'projects': 'Projects',
            'tasks': 'Tasks',
            'gantt': 'Gantt Chart',
            'reports': 'Reports',
            'team': 'Team',
            'settings': 'Settings'
        }
        
        return titles.get(page, page.title())
    
    def register_page(self, name: str, page_class: type, permissions: list = None) -> None:
        """Register a new page dynamically"""
        self.pages[name] = page_class
        if permissions:
            self.page_permissions[name] = permissions
        
        self.logger.info(f"Registered new page: {name}")
    
    def unregister_page(self, name: str) -> None:
        """Unregister a page"""
        if name in self.pages:
            del self.pages[name]
        if name in self.page_permissions:
            del self.page_permissions[name]
        
        self.logger.info(f"Unregistered page: {name}")
    
    def get_page_analytics(self) -> Dict[str, Any]:
        """Get page analytics data"""
        page_history = st.session_state.get('page_history', [])
        
        if not page_history:
            return {}
        
        # Calculate page metrics
        page_visits = {}
        total_time = 0
        
        for entry in page_history:
            page = entry['page']
            duration = entry.get('duration', 0)
            
            if page not in page_visits:
                page_visits[page] = {'count': 0, 'total_time': 0}
            
            page_visits[page]['count'] += 1
            page_visits[page]['total_time'] += duration
            total_time += duration
        
        # Calculate average time per page
        for page, data in page_visits.items():
            data['avg_time'] = data['total_time'] / data['count'] if data['count'] > 0 else 0
        
        return {
            'page_visits': page_visits,
            'total_session_time': total_time,
            'most_visited_page': max(page_visits.keys(), key=lambda x: page_visits[x]['count']) if page_visits else None,
            'longest_page_session': max(page_visits.keys(), key=lambda x: page_visits[x]['avg_time']) if page_visits else None
        }