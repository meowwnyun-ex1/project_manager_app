"""
🚀 Project Manager Pro v3.0 - Enhanced Authentication Service
Comprehensive authentication and user management
"""

import streamlit as st
import bcrypt
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from services.enhanced_db_service import EnhancedDBService
from config.enhanced_config import EnhancedConfig

class EnhancedAuthService:
    """Enhanced authentication service with security features"""
    
    def __init__(self):
        self.db_service = EnhancedDBService()
        self.config = EnhancedConfig()
        self.logger = logging.getLogger(__name__)
        
        # Authentication settings
        self.max_login_attempts = self.config.get('auth.max_login_attempts', 5)
        self.lockout_duration = self.config.get('auth.lockout_duration', timedelta(minutes=30))
        self.password_min_length = self.config.get('auth.password_min_length', 8)
        self.password_history_count = self.config.get('auth.password_history_count', 5)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with enhanced security checks"""
        try:
            # Input validation
            if not self._validate_login_input(username, password):
                return None
            
            # Check for SQL injection attempts
            if self._detect_sql_injection(username) or self._detect_sql_injection(password):
                self.logger.warning(f"SQL injection attempt detected for username: {username}")
                return None
            
            # Authenticate with database
            user_data = self.db_service.authenticate_user(username, password)
            
            if user_data:
                # Log successful authentication
                self.logger.info(f"Successful authentication for user: {username}")
                
                # Update user's last login
                self._update_last_login(user_data['user_id'])
                
                return user_data
            else:
                # Log failed authentication
                self.logger.warning(f"Failed authentication attempt for username: {username}")
                return None
                
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """Create new user with validation"""
        try:
            # Validate user data
            validation_errors = self._validate_user_data(user_data)
            if validation_errors:
                self.logger.warning(f"User creation validation failed: {validation_errors}")
                return None
            
            # Check if username or email already exists
            if self._user_exists(user_data['username'], user_data.get('email')):
                self.logger.warning(f"User creation failed - username/email exists: {user_data['username']}")
                return None
            
            # Hash password
            if not self._validate_password_strength(user_data['password']):
                self.logger.warning("User creation failed - weak password")
                return None
            
            # Create user in database
            user_id = self.db_service.create_user(user_data)
            
            if user_id:
                self.logger.info(f"User created successfully: {user_data['username']} (ID: {user_id})")
                
                # Send welcome notification (if email service is configured)
                self._send_welcome_notification(user_data)
                
                return user_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"User creation error: {str(e)}")
            return None
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password with validation"""
        try:
            # Get current user data
            user = self.db_service.get_user_by_id(user_id)
            if not user:
                return False
            
            # Verify current password
            if not self._verify_current_password(user_id, current_password):
                self.logger.warning(f"Password change failed - incorrect current password for user ID: {user_id}")
                return False
            
            # Validate new password strength
            if not self._validate_password_strength(new_password):
                self.logger.warning(f"Password change failed - weak new password for user ID: {user_id}")
                return False
            
            # Check password history
            if self._is_password_in_history(user_id, new_password):
                self.logger.warning(f"Password change failed - password in history for user ID: {user_id}")
                return False
            
            # Hash new password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update password in database
            success = self.db_service.execute_non_query("""
                UPDATE Users 
                SET PasswordHash = ?, PasswordChangedDate = GETDATE()
                WHERE UserID = ?
            """, [password_hash, user_id])
            
            if success:
                # Add to password history
                self._add_to_password_history(user_id, password_hash)
                
                # Log password change
                self.db_service.log_activity(user_id, None, None, 'Password Changed', 'User changed password')
                
                self.logger.info(f"Password changed successfully for user ID: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Password change error: {str(e)}")
            return False
    
    def reset_password(self, username_or_email: str) -> bool:
        """Reset user password (admin function)"""
        try:
            # Find user by username or email
            user = self._find_user_by_username_or_email(username_or_email)
            if not user:
                return False
            
            # Generate temporary password
            temp_password = self._generate_temporary_password()
            password_hash = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update password and set force change flag
            success = self.db_service.execute_non_query("""
                UPDATE Users 
                SET PasswordHash = ?, PasswordChangedDate = GETDATE(), ForcePasswordChange = 1
                WHERE UserID = ?
            """, [password_hash, user['user_id']])
            
            if success:
                # Send password reset notification
                self._send_password_reset_notification(user, temp_password)
                
                # Log password reset
                self.db_service.log_activity(user['user_id'], None, None, 'Password Reset', 'Password reset by admin')
                
                self.logger.info(f"Password reset for user: {user['username']}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Password reset error: {str(e)}")
            return False
    
    def lock_user_account(self, user_id: int, reason: str = "Administrative action") -> bool:
        """Lock user account"""
        try:
            success = self.db_service.execute_non_query("""
                UPDATE Users 
                SET Active = 0, LockedUntil = DATEADD(YEAR, 1, GETDATE())
                WHERE UserID = ?
            """, [user_id])
            
            if success:
                # Log account lock
                self.db_service.log_activity(user_id, None, None, 'Account Locked', reason)
                self.logger.info(f"Account locked for user ID: {user_id}, Reason: {reason}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Account lock error: {str(e)}")
            return False
    
    def unlock_user_account(self, user_id: int) -> bool:
        """Unlock user account"""
        try:
            success = self.db_service.execute_non_query("""
                UPDATE Users 
                SET Active = 1, LockedUntil = NULL, FailedLoginAttempts = 0
                WHERE UserID = ?
            """, [user_id])
            
            if success:
                # Log account unlock
                self.db_service.log_activity(user_id, None, None, 'Account Unlocked', 'Account unlocked by admin')
                self.logger.info(f"Account unlocked for user ID: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Account unlock error: {str(e)}")
            return False
    
    def get_user_security_info(self, user_id: int) -> Dict[str, Any]:
        """Get user security information"""
        try:
            user_info = self.db_service.execute_query("""
                SELECT Username, Email, Active, FailedLoginAttempts, LockedUntil, 
                       LastLoginDate, PasswordChangedDate, CreatedDate
                FROM Users 
                WHERE UserID = ?
            """, [user_id])
            
            if not user_info.empty:
                user_data = user_info.iloc[0].to_dict()
                
                # Get recent login attempts
                recent_attempts = self.db_service.execute_query("""
                    SELECT TOP 10 Action, Details, IPAddress, CreatedDate
                    FROM ActivityLogs 
                    WHERE UserID = ? AND Action LIKE '%Login%'
                    ORDER BY CreatedDate DESC
                """, [user_id])
                
                return {
                    'user_info': user_data,
                    'recent_attempts': recent_attempts.to_dict('records') if not recent_attempts.empty else [],
                    'account_status': self._get_account_status(user_data),
                    'password_age': (datetime.now() - user_data.get('PasswordChangedDate', datetime.now())).days,
                    'account_age': (datetime.now() - user_data.get('CreatedDate', datetime.now())).days
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Get user security info error: {str(e)}")
            return {}
    
    def validate_session_token(self, token: str, user_id: int) -> bool:
        """Validate session token"""
        try:
            # In production, implement proper token validation
            # This is a simplified version
            return token is not None and len(token) > 0
        except Exception as e:
            self.logger.error(f"Token validation error: {str(e)}")
            return False
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions based on role"""
        try:
            user = self.db_service.get_user_by_id(user_id)
            if not user:
                return []
            
            role = user.get('role', 'User')
            
            # Define role-based permissions
            role_permissions = {
                'Admin': [
                    'create_user', 'delete_user', 'manage_users', 'manage_projects', 
                    'delete_projects', 'view_all_data', 'system_settings', 'manage_team',
                    'view_reports', 'admin_access', 'manage_permissions'
                ],
                'Manager': [
                    'manage_projects', 'assign_tasks', 'view_team_data', 'manage_team',
                    'generate_reports', 'view_reports', 'create_projects'
                ],
                'User': [
                    'view_own_data', 'update_tasks', 'create_tasks', 'view_assigned_projects'
                ]
            }
            
            return role_permissions.get(role, [])
            
        except Exception as e:
            self.logger.error(f"Get user permissions error: {str(e)}")
            return []
    
    # Private helper methods
    def _validate_login_input(self, username: str, password: str) -> bool:
        """Validate login input"""
        if not username or not password:
            return False
        
        if len(username) > 50 or len(password) > 255:
            return False
        
        return True
    
    def _detect_sql_injection(self, input_string: str) -> bool:
        """Basic SQL injection detection"""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"[';\"](.*)[';\"]\s*(OR|AND)",
            r"\/\*.*\*\/",
            r"--\s*.*",
            r"(\b(EXEC|EXECUTE)\b)",
            r"(\b(SP_|XP_)\w+)",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_user_data(self, user_data: Dict[str, Any]) -> List[str]:
        """Validate user creation data"""
        errors = []
        
        # Required fields
        required_fields = ['username', 'password', 'email']
        for field in required_fields:
            if not user_data.get(field):
                errors.append(f"{field} is required")
        
        # Username validation
        username = user_data.get('username', '')
        if username:
            if len(username) < 3 or len(username) > 50:
                errors.append("Username must be 3-50 characters")
            if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
                errors.append("Username contains invalid characters")
        
        # Email validation
        email = user_data.get('email', '')
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append("Invalid email format")
        
        # Password validation
        password = user_data.get('password', '')
        if password and not self._validate_password_strength(password):
            errors.append("Password does not meet strength requirements")
        
        return errors
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < self.password_min_length:
            return False
        
        # Check for required character types
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        required_types = sum([
            self.config.get('auth.password_require_uppercase', True) and has_upper,
            self.config.get('auth.password_require_lowercase', True) and has_lower,
            self.config.get('auth.password_require_digits', True) and has_digit,
            self.config.get('auth.password_require_special', True) and has_special
        ])
        
        return required_types >= 3  # At least 3 out of 4 character types
    
    def _user_exists(self, username: str, email: str = None) -> bool:
        """Check if user exists by username or email"""
        try:
            query = "SELECT COUNT(*) as count FROM Users WHERE Username = ?"
            params = [username]
            
            if email:
                query += " OR Email = ?"
                params.append(email)
            
            result = self.db_service.execute_query(query, params)
            return result.iloc[0]['count'] > 0 if not result.empty else False
            
        except Exception as e:
            self.logger.error(f"User existence check error: {str(e)}")
            return True  # Err on the side of caution
    
    def _update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        try:
            self.db_service.execute_non_query("""
                UPDATE Users 
                SET LastLoginDate = GETDATE()
                WHERE UserID = ?
            """, [user_id])
        except Exception as e:
            self.logger.error(f"Update last login error: {str(e)}")
    
    def _verify_current_password(self, user_id: int, current_password: str) -> bool:
        """Verify user's current password"""
        try:
            result = self.db_service.execute_query("""
                SELECT PasswordHash FROM Users WHERE UserID = ?
            """, [user_id])
            
            if not result.empty:
                stored_hash = result.iloc[0]['PasswordHash']
                return bcrypt.checkpw(current_password.encode('utf-8'), stored_hash.encode('utf-8'))
            
            return False
            
        except Exception as e:
            self.logger.error(f"Password verification error: {str(e)}")
            return False
    
    def _is_password_in_history(self, user_id: int, new_password: str) -> bool:
        """Check if password was used recently"""
        try:
            # In production, implement password history table
            # For now, just check current password
            return self._verify_current_password(user_id, new_password)
            
        except Exception as e:
            self.logger.error(f"Password history check error: {str(e)}")
            return False
    
    def _add_to_password_history(self, user_id: int, password_hash: str) -> None:
        """Add password to history (simplified implementation)"""
        try:
            # In production, implement proper password history table
            # This is a placeholder for the concept
            pass
        except Exception as e:
            self.logger.error(f"Add to password history error: {str(e)}")
    
    def _generate_temporary_password(self) -> str:
        """Generate temporary password"""
        import secrets
        import string
        
        # Generate 12 character password with mixed case, digits, and symbols
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Ensure it has required character types
        password = password[:8] + 'A1!' + password[8:]
        
        return password
    
    def _find_user_by_username_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find user by username or email"""
        try:
            result = self.db_service.execute_query("""
                SELECT UserID, Username, Email, FirstName, LastName
                FROM Users 
                WHERE Username = ? OR Email = ?
            """, [identifier, identifier])
            
            if not result.empty:
                return result.iloc[0].to_dict()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Find user error: {str(e)}")
            return None
    
    def _get_account_status(self, user_data: Dict[str, Any]) -> str:
        """Get account status description"""
        if not user_data.get('Active', True):
            return 'Inactive'
        
        locked_until = user_data.get('LockedUntil')
        if locked_until and locked_until > datetime.now():
            return 'Locked'
        
        failed_attempts = user_data.get('FailedLoginAttempts', 0)
        if failed_attempts >= self.max_login_attempts:
            return 'Temporarily Locked'
        
        return 'Active'
    
    def _send_welcome_notification(self, user_data: Dict[str, Any]) -> None:
        """Send welcome notification to new user"""
        try:
            # In production, implement email service integration
            self.logger.info(f"Welcome notification should be sent to: {user_data.get('email')}")
        except Exception as e:
            self.logger.error(f"Welcome notification error: {str(e)}")
    
    def _send_password_reset_notification(self, user_data: Dict[str, Any], temp_password: str) -> None:
        """Send password reset notification"""
        try:
            # In production, implement email service integration
            self.logger.info(f"Password reset notification should be sent to: {user_data.get('email')}")
            self.logger.info(f"Temporary password: {temp_password}")
        except Exception as e:
            self.logger.error(f"Password reset notification error: {str(e)}")
    
    def get_security_audit_log(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get security audit log"""
        try:
            result = self.db_service.execute_query("""
                SELECT al.*, u.Username
                FROM ActivityLogs al
                INNER JOIN Users u ON al.UserID = u.UserID
                WHERE al.CreatedDate >= DATEADD(DAY, -?, GETDATE())
                AND al.Action IN ('Login Success', 'Login Failed', 'Password Changed', 'Account Locked', 'Account Unlocked')
                ORDER BY al.CreatedDate DESC
            """, [days])
            
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            self.logger.error(f"Security audit log error: {str(e)}")
            return []
    
    def get_failed_login_attempts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent failed login attempts"""
        try:
            result = self.db_service.execute_query("""
                SELECT al.*, u.Username
                FROM ActivityLogs al
                LEFT JOIN Users u ON al.UserID = u.UserID
                WHERE al.CreatedDate >= DATEADD(HOUR, -?, GETDATE())
                AND al.Action = 'Login Failed'
                ORDER BY al.CreatedDate DESC
            """, [hours])
            
            return result.to_dict('records') if not result.empty else []
            
        except Exception as e:
            self.logger.error(f"Failed login attempts error: {str(e)}")
            return []