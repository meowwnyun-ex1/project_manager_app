#!/usr/bin/env python3
"""
modules/auth.py
Authentication System for SDX Project Manager
Modern authentication with beautiful UI matching the purple gradient theme
"""

import streamlit as st
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
import base64

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Modern authentication system with enhanced security"""

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_admin_user()

    def _ensure_admin_user(self):
        """Ensure default admin user exists"""
        try:
            admin_exists = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Users WHERE Username = ?", ("admin",)
            )

            if admin_exists == 0:
                hashed_password = self._hash_password("admin123")
                self.db.execute_non_query(
                    """
                    INSERT INTO Users (Username, PasswordHash, FullName, Email, Role, IsActive)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        "admin",
                        hashed_password,
                        "System Administrator",
                        "admin@sdx.com",
                        "Admin",
                        True,
                    ),
                )
                logger.info("Default admin user created")

        except Exception as e:
            logger.error(f"Error ensuring admin user: {e}")

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except:
            return False

    def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        try:
            user_data = self.db.execute_query(
                """
                SELECT UserID, Username, PasswordHash, FullName, Email, Role, IsActive, LastLoginDate
                FROM Users 
                WHERE Username = ? AND IsActive = 1
            """,
                (username,),
            )

            if not user_data:
                return None

            user = user_data[0]

            if self._verify_password(password, user["PasswordHash"]):
                # Update last login
                self.db.execute_non_query(
                    "UPDATE Users SET LastLoginDate = GETDATE() WHERE UserID = ?",
                    (user["UserID"],),
                )

                # Remove sensitive data
                user_safe = {k: v for k, v in user.items() if k != "PasswordHash"}
                return user_safe

            return None

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def create_session_token(self, user_id: int) -> str:
        """Create secure session token"""
        token_data = (
            f"{user_id}:{datetime.now().isoformat()}:{secrets.token_urlsafe(32)}"
        )
        return base64.b64encode(token_data.encode()).decode()

    def validate_session_token(self, token: str) -> Optional[int]:
        """Validate session token and return user ID"""
        try:
            decoded = base64.b64decode(token.encode()).decode()
            parts = decoded.split(":")
            if len(parts) >= 3:
                user_id = int(parts[0])
                token_time = datetime.fromisoformat(parts[1])

                # Check if token is not expired (24 hours)
                if datetime.now() - token_time < timedelta(hours=24):
                    return user_id
            return None
        except:
            return None

    def render_modern_login_page(self):
        """Render beautiful login page with purple gradient theme"""

        # Custom CSS for modern login UI
        st.markdown(
            """
        <style>
            /* Import Google Fonts */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            .main-login-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                font-family: 'Inter', sans-serif;
            }
            
            .login-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 3rem;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
                max-width: 450px;
                width: 100%;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 2.5rem;
            }
            
            .login-logo {
                width: 80px;
                height: 80px;
                margin: 0 auto 1.5rem;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 2rem;
                font-weight: 600;
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
            }
            
            .login-title {
                font-size: 2rem;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .login-subtitle {
                color: #64748b;
                font-size: 1rem;
                font-weight: 400;
            }
            
            .login-form {
                space-y: 1.5rem;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
            }
            
            .form-label {
                display: block;
                font-size: 0.875rem;
                font-weight: 500;
                color: #374151;
                margin-bottom: 0.5rem;
            }
            
            .stTextInput > div > div > input {
                border: 2px solid #e5e7eb !important;
                border-radius: 12px !important;
                padding: 0.75rem 1rem !important;
                font-size: 1rem !important;
                transition: all 0.2s ease !important;
                background: #f9fafb !important;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
                background: white !important;
            }
            
            .login-button {
                width: 100%;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border: none;
                border-radius: 12px;
                padding: 0.875rem 1.5rem;
                font-size: 1rem;
                font-weight: 600;
                color: white;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-top: 1rem;
            }
            
            .login-button:hover {
                transform: translateY(-1px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
            }
            
            .login-footer {
                text-align: center;
                margin-top: 2rem;
                padding-top: 2rem;
                border-top: 1px solid #e5e7eb;
            }
            
            .copyright {
                color: #64748b;
                font-size: 0.875rem;
                line-height: 1.5;
            }
            
            .features-list {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
                margin-top: 2rem;
            }
            
            .feature-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                color: #64748b;
            }
            
            .feature-icon {
                width: 16px;
                height: 16px;
                color: #667eea;
            }
            
            /* Streamlit specific adjustments */
            .block-container {
                padding: 0 !important;
                max-width: none !important;
            }
            
            .stApp > header {
                display: none;
            }
            
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            /* Error message styling */
            .stAlert {
                border-radius: 12px !important;
                border: none !important;
                margin-bottom: 1rem !important;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Main login container
        st.markdown('<div class="main-login-container">', unsafe_allow_html=True)

        # Login card
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown(
                """
            <div class="login-card">
                <div class="login-header">
                    <div class="login-logo">SDX</div>
                    <h1 class="login-title">SDX | Project Manager</h1>
                    <p class="login-subtitle">เข้าสู่ระบบเพื่อจัดการโครงการของคุณ</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

            # Login form
            with st.form("login_form", clear_on_submit=False):
                st.markdown('<div class="login-form">', unsafe_allow_html=True)

                st.markdown(
                    '<label class="form-label">ชื่อผู้ใช้</label>', unsafe_allow_html=True
                )
                username = st.text_input(
                    "",
                    placeholder="กรอกชื่อผู้ใช้",
                    key="username",
                    label_visibility="collapsed",
                )

                st.markdown(
                    '<label class="form-label">รหัสผ่าน</label>', unsafe_allow_html=True
                )
                password = st.text_input(
                    "",
                    type="password",
                    placeholder="กรอกรหัสผ่าน",
                    key="password",
                    label_visibility="collapsed",
                )

                col_btn1, col_btn2 = st.columns([1, 1])

                with col_btn1:
                    remember_me = st.checkbox("จดจำการเข้าสู่ระบบ")

                with col_btn2:
                    forgot_password = st.button("ลืมรหัสผ่าน?", type="secondary")

                st.markdown("</div>", unsafe_allow_html=True)

                login_submitted = st.form_submit_button(
                    "เข้าสู่ระบบ", use_container_width=True, type="primary"
                )

            # Handle login
            if login_submitted:
                if username and password:
                    user = self.authenticate_user(username, password)

                    if user:
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.session_token = self.create_session_token(
                            user["UserID"]
                        )
                        st.session_state.last_activity = datetime.now()

                        # Store in browser if remember me
                        if remember_me:
                            st.markdown(
                                f"""
                            <script>
                                localStorage.setItem('sdx_session_token', '{st.session_state.session_token}');
                                localStorage.setItem('sdx_remember_user', 'true');
                            </script>
                            """,
                                unsafe_allow_html=True,
                            )

                        st.success("🎉 เข้าสู่ระบบสำเร็จ!")
                        st.rerun()
                    else:
                        st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                else:
                    st.warning("⚠️ กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")

            if forgot_password:
                st.info("📧 กรุณาติดต่อผู้ดูแลระบบเพื่อขอรีเซ็ตรหัสผ่าน")

            # Features and footer
            st.markdown(
                """
                <div class="features-list">
                    <div class="feature-item">
                        <span class="feature-icon">✓</span>
                        <span>จัดการโครงการ</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">✓</span>
                        <span>ติดตามงาน</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">✓</span>
                        <span>รายงานการทำงาน</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">✓</span>
                        <span>วิเคราะห์ข้อมูล</span>
                    </div>
                </div>
                
                <div class="login-footer">
                    <div class="copyright">
                        <strong>SDX | Project Manager v2.0</strong><br>
                        พัฒนาโดย <strong>Thammaphon Chittasuwanna (SDM)</strong><br>
                        Innovation Team © 2024
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    def check_authentication(self) -> bool:
        """Check if user is authenticated"""
        # Check session state first
        if st.session_state.get("authenticated", False):
            return True

        # Check browser storage for remember me
        check_storage_script = """
        <script>
            const token = localStorage.getItem('sdx_session_token');
            const remember = localStorage.getItem('sdx_remember_user');
            
            if (token && remember === 'true') {
                // Send token back to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:componentReady',
                    token: token
                }, '*');
            }
        </script>
        """

        # For now, just check session state
        return st.session_state.get("authenticated", False)

    def logout_user(self):
        """Logout user and clear session"""
        # Clear browser storage
        clear_storage_script = """
        <script>
            localStorage.removeItem('sdx_session_token');
            localStorage.removeItem('sdx_remember_user');
            localStorage.removeItem('sdx_session_data');
        </script>
        """
        st.markdown(clear_storage_script, unsafe_allow_html=True)

        # Clear session state
        keys_to_clear = ["authenticated", "user", "session_token", "last_activity"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

        st.success("👋 ออกจากระบบเรียบร้อยแล้ว")
        st.rerun()

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        return st.session_state.get("user")

    def is_admin(self) -> bool:
        """Check if current user is admin"""
        user = self.get_current_user()
        return user and user.get("Role") == "Admin"

    def require_auth(self, admin_required: bool = False):
        """Decorator-like function to require authentication"""
        if not self.check_authentication():
            self.render_modern_login_page()
            st.stop()

        if admin_required and not self.is_admin():
            st.error("🔒 ต้องมีสิทธิ์ผู้ดูแลระบบเท่านั้น")
            st.stop()

    def render_user_menu(self):
        """Render user menu in sidebar"""
        user = self.get_current_user()
        if not user:
            return

        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👤 **{user['FullName']}**")
            st.caption(f"Role: {user['Role']}")
            st.caption(f"Email: {user['Email']}")

            if st.button("🚪 ออกจากระบบ", use_container_width=True):
                self.logout_user()
