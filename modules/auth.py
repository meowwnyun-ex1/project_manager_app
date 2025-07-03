#!/usr/bin/env python3
"""
modules/auth.py
Complete Authentication System for DENSO Project Manager Pro
"""
import logging
import hashlib
import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    user_id: int
    username: str
    role: str
    permissions: Dict[str, bool]
    login_time: datetime
    last_activity: datetime


class AuthManager:
    """Complete authentication and authorization system"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.session_timeout = 3600  # 1 hour
        self.max_failed_attempts = 5
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state variables"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user_session" not in st.session_state:
            st.session_state.user_session = None
        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = 0

    def authenticate(self, username: str, password: str) -> bool:
        """Main authentication method"""
        try:
            # Rate limiting check
            if self._is_rate_limited():
                return False

            # Get user data
            user = self._get_user_data(username)
            if not user:
                self._handle_failed_attempt()
                return False

            # Verify user status
            if not self._verify_user_status(user):
                return False

            # Verify password
            if not self._verify_password(password, user["PasswordHash"]):
                self._handle_failed_login(user["UserID"])
                self._handle_failed_attempt()
                return False

            # Success - create session
            self._create_user_session(user)
            self._update_login_success(user["UserID"])
            self._reset_failed_attempts()

            logger.info(f"User '{username}' authenticated successfully")
            return True

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def _get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user data from database"""
        try:
            users = self.db.execute_query(
                """SELECT UserID, Username, PasswordHash, Email, FirstName, LastName, 
                   Role, Department, IsActive, IsLocked, FailedLoginAttempts 
                   FROM Users WHERE Username = ?""",
                (username,),
            )
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return None

    def _verify_user_status(self, user: Dict[str, Any]) -> bool:
        """Verify user account status"""
        if not user["IsActive"]:
            st.error("🚫 บัญชีผู้ใช้ถูกปิดใช้งาน")
            return False

        if user["IsLocked"]:
            st.error("🔒 บัญชีผู้ใช้ถูกล็อค กรุณาติดต่อผู้ดูแลระบบ")
            return False

        return True

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            if BCRYPT_AVAILABLE and password_hash.startswith("$2b$"):
                return bcrypt.checkpw(
                    password.encode("utf-8"), password_hash.encode("utf-8")
                )
            else:
                # Fallback for development
                simple_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                return simple_hash == password_hash
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def _create_user_session(self, user: Dict[str, Any]):
        """Create user session"""
        permissions = self._get_user_permissions(user["Role"])

        session = UserSession(
            user_id=user["UserID"],
            username=user["Username"],
            role=user["Role"],
            permissions=permissions,
            login_time=datetime.now(),
            last_activity=datetime.now(),
        )

        st.session_state.authenticated = True
        st.session_state.user_session = session
        st.session_state.username = user["Username"]
        st.session_state.user_role = user["Role"]
        st.session_state.user_id = user["UserID"]

    def _get_user_permissions(self, role: str) -> Dict[str, bool]:
        """Get permissions based on user role"""
        permissions_map = {
            "Admin": {
                "manage_users": True,
                "manage_projects": True,
                "manage_tasks": True,
                "view_analytics": True,
                "system_settings": True,
                "database_admin": True,
                "manage_roles": True,
                "export_data": True,
            },
            "Project Manager": {
                "manage_users": False,
                "manage_projects": True,
                "manage_tasks": True,
                "view_analytics": True,
                "system_settings": False,
                "database_admin": False,
                "manage_roles": False,
                "export_data": True,
            },
            "Team Lead": {
                "manage_users": False,
                "manage_projects": False,
                "manage_tasks": True,
                "view_analytics": True,
                "system_settings": False,
                "database_admin": False,
                "manage_roles": False,
                "export_data": False,
            },
            "Developer": {
                "manage_users": False,
                "manage_projects": False,
                "manage_tasks": False,
                "view_analytics": False,
                "system_settings": False,
                "database_admin": False,
                "manage_roles": False,
                "export_data": False,
            },
            "User": {
                "manage_users": False,
                "manage_projects": False,
                "manage_tasks": False,
                "view_analytics": False,
                "system_settings": False,
                "database_admin": False,
                "manage_roles": False,
                "export_data": False,
            },
        }

        return permissions_map.get(role, permissions_map["User"])

    def _update_login_success(self, user_id: int):
        """Update successful login timestamp"""
        try:
            self.db.execute_non_query(
                "UPDATE Users SET LastLogin = GETDATE(), FailedLoginAttempts = 0 WHERE UserID = ?",
                (user_id,),
            )
        except Exception as e:
            logger.error(f"Error updating login success: {e}")

    def _handle_failed_login(self, user_id: int):
        """Handle failed login attempt in database"""
        try:
            failed_attempts = (
                self.db.execute_scalar(
                    "SELECT FailedLoginAttempts FROM Users WHERE UserID = ?", (user_id,)
                )
                or 0
            )

            failed_attempts += 1

            if failed_attempts >= self.max_failed_attempts:
                self.db.execute_non_query(
                    """UPDATE Users SET 
                       FailedLoginAttempts = ?, 
                       LastFailedLogin = GETDATE(),
                       IsLocked = 1 
                       WHERE UserID = ?""",
                    (failed_attempts, user_id),
                )
                st.error(
                    f"🔒 บัญชีถูกล็อคเนื่องจากพยายามเข้าสู่ระบบผิด {self.max_failed_attempts} ครั้ง"
                )
            else:
                self.db.execute_non_query(
                    """UPDATE Users SET 
                       FailedLoginAttempts = ?, 
                       LastFailedLogin = GETDATE() 
                       WHERE UserID = ?""",
                    (failed_attempts, user_id),
                )
                remaining = self.max_failed_attempts - failed_attempts
                st.warning(f"⚠️ รหัสผ่านไม่ถูกต้อง เหลือโอกาสอีก {remaining} ครั้ง")

        except Exception as e:
            logger.error(f"Error handling failed login: {e}")

    def _is_rate_limited(self) -> bool:
        """Check if user is rate limited"""
        if st.session_state.login_attempts >= 10:
            st.error("🚫 คุณพยายามเข้าสู่ระบบมากเกินไป กรุณารอสักครู่")
            return True
        return False

    def _handle_failed_attempt(self):
        """Handle failed attempt in session"""
        st.session_state.login_attempts += 1
        st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    def _reset_failed_attempts(self):
        """Reset failed attempts counter"""
        st.session_state.login_attempts = 0

    def logout(self):
        """Logout user and clear session"""
        if st.session_state.get("user_session"):
            username = st.session_state.user_session.username
            logger.info(f"User '{username}' logged out")

        # Clear all session data
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.session_state.authenticated = False
        st.success("✅ ออกจากระบบเรียบร้อยแล้ว")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if not st.session_state.get("authenticated", False):
            return False

        session = st.session_state.get("user_session")
        if not session:
            return False

        # Check session timeout
        if self._is_session_expired(session):
            self.logout()
            st.warning("⏰ Session หมดอายุ กรุณาเข้าสู่ระบบใหม่")
            return False

        # Update last activity
        session.last_activity = datetime.now()
        return True

    def _is_session_expired(self, session: UserSession) -> bool:
        """Check if session is expired"""
        if not session.last_activity:
            return True

        elapsed = (datetime.now() - session.last_activity).total_seconds()
        return elapsed > self.session_timeout

    def get_current_user(self) -> Optional[UserSession]:
        """Get current authenticated user"""
        if self.is_authenticated():
            return st.session_state.user_session
        return None

    def has_permission(self, permission: str) -> bool:
        """Check if current user has specific permission"""
        session = self.get_current_user()
        if not session:
            return False
        return session.permissions.get(permission, False)

    def require_permission(self, permission: str) -> bool:
        """Require specific permission (with UI feedback)"""
        if not self.has_permission(permission):
            st.error(f"🚫 คุณไม่มีสิทธิ์ในการ {permission}")
            return False
        return True

    def require_role(self, required_roles: List[str]) -> bool:
        """Require specific role(s)"""
        session = self.get_current_user()
        if not session or session.role not in required_roles:
            st.error(f"🚫 ต้องมีสิทธิ์ {', '.join(required_roles)} เท่านั้น")
            return False
        return True

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change current user's password"""
        session = self.get_current_user()
        if not session:
            return False

        try:
            # Verify old password
            user = self._get_user_data(session.username)
            if not user or not self._verify_password(
                old_password, user["PasswordHash"]
            ):
                st.error("❌ รหัสผ่านเดิมไม่ถูกต้อง")
                return False

            # Validate new password
            if not self._validate_password(new_password):
                return False

            # Hash and update new password
            new_hash = self._hash_password(new_password)
            self.db.execute_non_query(
                "UPDATE Users SET PasswordHash = ? WHERE UserID = ?",
                (new_hash, session.user_id),
            )

            st.success("✅ เปลี่ยนรหัสผ่านเรียบร้อยแล้ว")
            logger.info(f"Password changed for user '{session.username}'")
            return True

        except Exception as e:
            logger.error(f"Error changing password: {e}")
            st.error("❌ เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน")
            return False

    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            st.error("❌ รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
            return False

        if not any(c.isupper() for c in password):
            st.error("❌ รหัสผ่านต้องมีอักษรตัวใหญ่อย่างน้อย 1 ตัว")
            return False

        if not any(c.islower() for c in password):
            st.error("❌ รหัสผ่านต้องมีอักษรตัวเล็กอย่างน้อย 1 ตัว")
            return False

        if not any(c.isdigit() for c in password):
            st.error("❌ รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")
            return False

        return True

    def _hash_password(self, password: str) -> str:
        """Hash password for storage"""
        if BCRYPT_AVAILABLE:
            return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            )
        else:
            # Fallback for development
            return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def get_user_info(self, username: str = None) -> Optional[Dict[str, Any]]:
        """Get detailed user information"""
        if not username:
            session = self.get_current_user()
            username = session.username if session else None

        if not username:
            return None

        try:
            users = self.db.execute_query(
                """SELECT UserID, Username, Email, FirstName, LastName, 
                   Role, Department, IsActive, CreatedDate, LastLogin,
                   FailedLoginAttempts, IsLocked
                   FROM Users WHERE Username = ?""",
                (username,),
            )
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    def unlock_user(self, username: str) -> bool:
        """Unlock user account (admin only)"""
        if not self.require_permission("manage_users"):
            return False

        try:
            rows_affected = self.db.execute_non_query(
                """UPDATE Users SET 
                   IsLocked = 0, 
                   FailedLoginAttempts = 0,
                   LastFailedLogin = NULL 
                   WHERE Username = ?""",
                (username,),
            )

            if rows_affected > 0:
                st.success(f"✅ ปลดล็อคบัญชี '{username}' เรียบร้อยแล้ว")
                logger.info(f"User '{username}' unlocked by admin")
                return True
            else:
                st.error(f"❌ ไม่พบบัญชี '{username}'")
                return False

        except Exception as e:
            logger.error(f"Error unlocking user: {e}")
            st.error("❌ เกิดข้อผิดพลาดในการปลดล็อคบัญชี")
            return False

    def render_login_form(self):
        """Render complete login form with validation"""
        st.title("🚗 DENSO Project Manager Pro")
        st.subheader("🔐 เข้าสู่ระบบ")

        with st.form("login_form", clear_on_submit=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                username = st.text_input(
                    "👤 ชื่อผู้ใช้", placeholder="กรอกชื่อผู้ใช้", help="ใช้ชื่อผู้ใช้ที่ได้รับจากผู้ดูแลระบบ"
                )

                password = st.text_input(
                    "🔑 รหัสผ่าน",
                    type="password",
                    placeholder="กรอกรหัสผ่าน",
                    help="รหัสผ่านประกอบด้วยอักษรและตัวเลข",
                )

                col_login, col_forgot = st.columns(2)
                with col_login:
                    login_clicked = st.form_submit_button(
                        "🚀 เข้าสู่ระบบ", use_container_width=True, type="primary"
                    )

                with col_forgot:
                    if st.form_submit_button("🔄 ลืมรหัสผ่าน", use_container_width=True):
                        st.info("📧 กรุณาติดต่อผู้ดูแลระบบเพื่อรีเซ็ตรหัสผ่าน")

            with col2:
                st.markdown("### ℹ️ ข้อมูลเริ่มต้น")
                st.code("Username: admin\nPassword: admin123")
                st.caption("⚠️ กรุณาเปลี่ยนรหัสผ่านหลังเข้าใช้งานครั้งแรก")

        if login_clicked:
            if not username or not password:
                st.error("❌ กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
                return False

            with st.spinner("🔄 กำลังตรวจสอบข้อมูล..."):
                if self.authenticate(username, password):
                    st.success("✅ เข้าสู่ระบบสำเร็จ!")
                    st.rerun()
                    return True

        return False

    def render_user_menu(self):
        """Render user menu in sidebar"""
        session = self.get_current_user()
        if not session:
            return

        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👋 **{session.username}**")
            st.caption(f"🏷️ {session.role}")

            if st.button("👤 โปรไฟล์", use_container_width=True):
                self._show_profile_modal()

            if st.button("🔧 เปลี่ยนรหัสผ่าน", use_container_width=True):
                self._show_password_change_modal()

            if st.button("🚪 ออกจากระบบ", use_container_width=True):
                self.logout()
                st.rerun()

    def _show_profile_modal(self):
        """Show user profile information"""
        user_info = self.get_user_info()
        if user_info:
            st.json(
                {
                    "ชื่อผู้ใช้": user_info["Username"],
                    "อีเมล": user_info["Email"],
                    "ชื่อ": f"{user_info['FirstName']} {user_info['LastName']}",
                    "ตำแหน่ง": user_info["Role"],
                    "แผนก": user_info["Department"],
                    "เข้าสู่ระบบล่าสุด": (
                        str(user_info["LastLogin"])
                        if user_info["LastLogin"]
                        else "ไม่มีข้อมูล"
                    ),
                }
            )

    def _show_password_change_modal(self):
        """Show password change form"""
        with st.form("change_password_form"):
            st.subheader("🔧 เปลี่ยนรหัสผ่าน")

            old_password = st.text_input("รหัสผ่านเดิม", type="password")
            new_password = st.text_input("รหัสผ่านใหม่", type="password")
            confirm_password = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")

            if st.form_submit_button("🔄 เปลี่ยนรหัสผ่าน"):
                if new_password != confirm_password:
                    st.error("❌ รหัสผ่านใหม่ไม่ตรงกัน")
                elif self.change_password(old_password, new_password):
                    st.rerun()
