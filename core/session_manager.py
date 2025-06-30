"""
🚀 Project Manager Pro v3.0 - Session Manager
Advanced session management with security features
"""

import streamlit as st
import hashlib
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from config.enhanced_config import EnhancedConfig

class SessionManager:
    """Advanced session management with security and performance features"""
    
    def __init__(self):
        self.config = EnhancedConfig()
        self.logger = logging.getLogger(__name__)
        self.session_timeout = self.config.get('auth.session_timeout', timedelta(hours=8))
        self.cookie_name = self.config.get('auth.cookie_name', 'project_manager_pro_auth')
    
    def initialize_session(self) -> None:
        """Initialize session state with default values"""
        if 'session_initialized' not in st.session_state:
            st.session_state.update({
                'session_initialized': True,
                'authenticated': False,
                'user_id': None,
                'username': None,
                'user_role': None,
                'first_name': None,
                'last_name': None,
                'email': None,
                'login_time': None,
                'last_activity': datetime.now(),
                'session_token': None,
                'current_page': 'dashboard',
                'theme': self.config.get('ui.theme', 'modern_dark'),
                'language': 'en',
                'notifications': [],
                'sidebar_collapsed': False,
                'page_history': [],
                'user_preferences': {},
                'temp_data': {},
                'csrf_token': self._generate_csrf_token(),
                'performance_metrics': {
                    'page_loads': 0,
                    'api_calls': 0,
                    'errors': 0,
                    'session_start': datetime.now()
                }
            })
            
            self.logger.info("Session initialized")
    
    def login_user(self, user_data: Dict[str, Any]) -> bool:
        """Login user and establish session"""
        try:
            session_token = self._generate_session_token(user_data['user_id'])
            
            st.session_state.update({
                'authenticated': True,
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'user_role': user_data['role'],
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'login_time': datetime.now(),
                'last_activity': datetime.now(),
                'session_token': session_token
            })
            
            # Store session data securely
            self._store_session_data(session_token, user_data)
            
            self.logger.info(f"User {user_data['username']} logged in successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
    
    def logout_user(self) -> None:
        """Logout user and clear session"""
        try:
            username = st.session_state.get('username', 'Unknown')
            
            # Clear session token
            if 'session_token' in st.session_state:
                self._clear_session_data(st.session_state['session_token'])
            
            # Reset session state
            for key in list(st.session_state.keys()):
                if key not in ['session_initialized', 'theme', 'language']:
                    del st.session_state[key]
            
            # Reinitialize basic session
            self.initialize_session()
            
            self.logger.info(f"User {username} logged out")
            
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated and session is valid"""
        try:
            if not st.session_state.get('authenticated', False):
                return False
            
            # Check session timeout
            if self._is_session_expired():
                self.logout_user()
                return False
            
            # Update last activity
            st.session_state['last_activity'] = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication check failed: {str(e)}")
            return False
    
    def _is_session_expired(self) -> bool:
        """Check if session has expired"""
        if 'last_activity' not in st.session_state:
            return True
        
        last_activity = st.session_state['last_activity']
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        
        return datetime.now() - last_activity > self.session_timeout
    
    def _generate_session_token(self, user_id: int) -> str:
        """Generate secure session token"""
        timestamp = str(time.time())
        user_str = str(user_id)
        secret = self.config.get('app.secret_key', 'default-secret')
        
        token_data = f"{user_str}:{timestamp}:{secret}"
        return hashlib.sha256(token_data.encode()).hexdigest()
    
    def _generate_csrf_token(self) -> str:
        """Generate CSRF protection token"""
        timestamp = str(time.time())
        random_data = str(hash(timestamp))
        secret = self.config.get('app.secret_key', 'default-secret')
        
        csrf_data = f"{timestamp}:{random_data}:{secret}"
        return hashlib.md5(csrf_data.encode()).hexdigest()
    
    def _store_session_data(self, token: str, user_data: Dict[str, Any]) -> None:
        """Store session data securely (in production, use Redis or database)"""
        try:
            # In production, this should be stored in Redis or database
            # For now, storing in session state with encryption
            session_data = {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'role': user_data['role'],
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + self.session_timeout).isoformat()
            }
            
            # Store encrypted session data
            encrypted_data = self._encrypt_session_data(session_data)
            if 'session_store' not in st.session_state:
                st.session_state['session_store'] = {}
            st.session_state['session_store'][token] = encrypted_data
            
        except Exception as e:
            self.logger.error(f"Session storage failed: {str(e)}")
    
    def _clear_session_data(self, token: str) -> None:
        """Clear stored session data"""
        try:
            if 'session_store' in st.session_state and token in st.session_state['session_store']:
                del st.session_state['session_store'][token]
        except Exception as e:
            self.logger.error(f"Session clear failed: {str(e)}")
    
    def _encrypt_session_data(self, data: Dict[str, Any]) -> str:
        """Encrypt session data (simplified version)"""
        try:
            # In production, use proper encryption like Fernet
            import base64
            json_data = json.dumps(data)
            encoded_data = base64.b64encode(json_data.encode()).decode()
            return encoded_data
        except Exception:
            return json.dumps(data)
    
    def _decrypt_session_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt session data"""
        try:
            import base64
            decoded_data = base64.b64decode(encrypted_data.encode()).decode()
            return json.loads(decoded_data)
        except Exception:
            return json.loads(encrypted_data)
    
    def get_user_id(self) -> Optional[int]:
        """Get current user ID"""
        return st.session_state.get('user_id')
    
    def get_username(self) -> Optional[str]:
        """Get current username"""
        return st.session_state.get('username')
    
    def get_user_role(self) -> Optional[str]:
        """Get current user role"""
        return st.session_state.get('user_role')
    
    def get_user_full_name(self) -> str:
        """Get user's full name"""
        first_name = st.session_state.get('first_name', '')
        last_name = st.session_state.get('last_name', '')
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return st.session_state.get('username', 'User')
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        user_role = self.get_user_role()
        
        role_permissions = {
            'Admin': ['create_user', 'delete_user', 'manage_projects', 'view_all_data', 'system_settings'],
            'Manager': ['manage_projects', 'assign_tasks', 'view_team_data', 'generate_reports'],
            'User': ['view_own_data', 'update_tasks', 'create_tasks']
        }
        
        return permission in role_permissions.get(user_role, [])
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.get_user_role() == 'Admin'
    
    def is_manager(self) -> bool:
        """Check if current user is manager or admin"""
        return self.get_user_role() in ['Admin', 'Manager']
    
    def set_current_page(self, page: str) -> None:
        """Set current page and update history"""
        current_page = st.session_state.get('current_page')
        if current_page != page:
            # Add to page history
            if 'page_history' not in st.session_state:
                st.session_state['page_history'] = []
            
            st.session_state['page_history'].append({
                'page': current_page,
                'timestamp': datetime.now(),
                'duration': (datetime.now() - st.session_state.get('page_start_time', datetime.now())).total_seconds()
            })
            
            # Keep only last 10 pages in history
            if len(st.session_state['page_history']) > 10:
                st.session_state['page_history'] = st.session_state['page_history'][-10:]
        
        st.session_state['current_page'] = page
        st.session_state['page_start_time'] = datetime.now()
    
    def get_current_page(self) -> str:
        """Get current page"""
        return st.session_state.get('current_page', 'dashboard')
    
    def add_notification(self, message: str, notification_type: str = 'info', duration: int = 5000) -> None:
        """Add notification to session"""
        if 'notifications' not in st.session_state:
            st.session_state['notifications'] = []
        
        notification = {
            'id': len(st.session_state['notifications']),
            'message': message,
            'type': notification_type,
            'timestamp': datetime.now(),
            'duration': duration,
            'read': False
        }
        
        st.session_state['notifications'].append(notification)
        
        # Keep only last 20 notifications
        if len(st.session_state['notifications']) > 20:
            st.session_state['notifications'] = st.session_state['notifications'][-20:]
    
    def get_notifications(self, unread_only: bool = False) -> list:
        """Get notifications"""
        notifications = st.session_state.get('notifications', [])
        
        if unread_only:
            return [n for n in notifications if not n.get('read', False)]
        
        return notifications
    
    def mark_notification_read(self, notification_id: int) -> None:
        """Mark notification as read"""
        notifications = st.session_state.get('notifications', [])
        for notification in notifications:
            if notification.get('id') == notification_id:
                notification['read'] = True
                break
    
    def clear_notifications(self) -> None:
        """Clear all notifications"""
        st.session_state['notifications'] = []
    
    def set_user_preference(self, key: str, value: Any) -> None:
        """Set user preference"""
        if 'user_preferences' not in st.session_state:
            st.session_state['user_preferences'] = {}
        
        st.session_state['user_preferences'][key] = value
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        return st.session_state.get('user_preferences', {}).get(key, default)
    
    def set_temp_data(self, key: str, value: Any) -> None:
        """Set temporary data (cleared on logout)"""
        if 'temp_data' not in st.session_state:
            st.session_state['temp_data'] = {}
        
        st.session_state['temp_data'][key] = value
    
    def get_temp_data(self, key: str, default: Any = None) -> Any:
        """Get temporary data"""
        return st.session_state.get('temp_data', {}).get(key, default)
    
    def clear_temp_data(self) -> None:
        """Clear all temporary data"""
        st.session_state['temp_data'] = {}
    
    def update_performance_metric(self, metric: str, increment: int = 1) -> None:
        """Update performance metrics"""
        if 'performance_metrics' not in st.session_state:
            st.session_state['performance_metrics'] = {}
        
        current_value = st.session_state['performance_metrics'].get(metric, 0)
        st.session_state['performance_metrics'][metric] = current_value + increment
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = st.session_state.get('performance_metrics', {})
        
        # Calculate session duration
        session_start = metrics.get('session_start', datetime.now())
        if isinstance(session_start, str):
            session_start = datetime.fromisoformat(session_start)
        
        metrics['session_duration'] = (datetime.now() - session_start).total_seconds()
        
        return metrics
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get comprehensive session information"""
        return {
            'authenticated': self.is_authenticated(),
            'user_id': self.get_user_id(),
            'username': self.get_username(),
            'user_role': self.get_user_role(),
            'full_name': self.get_user_full_name(),
            'login_time': st.session_state.get('login_time'),
            'last_activity': st.session_state.get('last_activity'),
            'current_page': self.get_current_page(),
            'session_duration': self.get_performance_metrics().get('session_duration', 0),
            'notifications_count': len(self.get_notifications(unread_only=True)),
            'theme': st.session_state.get('theme'),
            'language': st.session_state.get('language')
        }
    
    def cleanup_expired_sessions(self) -> None:
        """Cleanup expired session data"""
        try:
            if 'session_store' in st.session_state:
                current_time = datetime.now()
                expired_tokens = []
                
                for token, encrypted_data in st.session_state['session_store'].items():
                    try:
                        session_data = self._decrypt_session_data(encrypted_data)
                        expires_at = datetime.fromisoformat(session_data.get('expires_at', ''))
                        
                        if current_time > expires_at:
                            expired_tokens.append(token)
                    except Exception:
                        expired_tokens.append(token)  # Remove corrupted data
                
                # Remove expired sessions
                for token in expired_tokens:
                    del st.session_state['session_store'][token]
                
                if expired_tokens:
                    self.logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")
                    
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {str(e)}")