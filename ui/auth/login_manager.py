# ui/auth/login_manager.py
import streamlit as st
from services.enhanced_auth_service import get_auth_service
from core.session_manager import SessionManager


class LoginManager:
    """Enhanced login manager with modern UI"""

    def __init__(self):
        self.auth_service = get_auth_service()
        self.session_manager = SessionManager()

    def render(self):
        """Render login page"""
        self._inject_login_css()

        # Main login container
        st.markdown(
            """
        <div class="login-container">
            <div class="login-card">
                <div class="login-header">
                    <div class="app-logo">🚀</div>
                    <h1 class="app-title">Project Manager Pro</h1>
                    <p class="app-subtitle">v3.0 Enterprise Edition</p>
                </div>
                
                <div class="login-form">
        """,
            unsafe_allow_html=True,
        )

        # Login form
        with st.form("login_form"):
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown(
                '<label class="form-label">👤 Username</label>', unsafe_allow_html=True
            )
            username = st.text_input(
                "",
                placeholder="Enter your username",
                value="admin",
                key="login_username",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown(
                '<label class="form-label">🔐 Password</label>', unsafe_allow_html=True
            )
            password = st.text_input(
                "",
                type="password",
                placeholder="Enter your password",
                value="admin",
                key="login_password",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            # Remember me option
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            remember_me = st.checkbox("Remember me", key="remember_me")
            st.markdown("</div>", unsafe_allow_html=True)

            # Submit button
            submitted = st.form_submit_button("🔑 Sign In", use_container_width=True)

            if submitted:
                if username and password:
                    user = self.auth_service.authenticate_user(username, password)
                    if user:
                        if self.session_manager.login_user(user):
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Login failed!")
                    else:
                        st.error("❌ Invalid credentials!")
                else:
                    st.error("❌ Please enter username and password")

        # Demo credentials info
        st.markdown(
            """
                </div>
                
                <div class="demo-info">
                    <h4>🎮 Demo Credentials</h4>
                    <div class="demo-credential">
                        <strong>Username:</strong> admin<br>
                        <strong>Password:</strong> admin
                    </div>
                </div>
                
                <div class="features-preview">
                    <h4>✨ Features</h4>
                    <div class="feature-list">
                        <div class="feature-item">🎨 Modern glassmorphism UI</div>
                        <div class="feature-item">📊 Real-time analytics</div>
                        <div class="feature-item">📅 Interactive Gantt charts</div>
                        <div class="feature-item">👥 Team collaboration</div>
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _inject_login_css(self):
        """Inject CSS for login page"""
        st.markdown(
            """
        <style>
        /* Login Page Styles */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
        }
        
        .login-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 3rem;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: fadeInUp 0.6s ease-out;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .app-logo {
            font-size: 4rem;
            margin-bottom: 1rem;
            animation: bounce 1s;
        }
        
        .app-title {
            color: white;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .app-subtitle {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1rem;
            margin-bottom: 0;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            color: white;
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .demo-info {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem;
            margin-top: 2rem;
            text-align: center;
        }
        
        .demo-info h4 {
            color: white;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        .demo-credential {
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        .features-preview {
            margin-top: 1.5rem;
            text-align: center;
        }
        
        .features-preview h4 {
            color: white;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        .feature-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }
        
        .feature-item {
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.85rem;
            padding: 0.5rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        
        /* Streamlit form styling overrides */
        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 12px !important;
            color: white !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: rgba(255, 255, 255, 0.6) !important;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2) !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: rgba(255, 255, 255, 0.6) !important;
        }
        
        .stCheckbox > label {
            color: white !important;
            font-size: 0.9rem !important;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(0, 210, 255, 0.4) !important;
        }
        
        .stForm {
            border: none !important;
            background: none !important;
        }
        
        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes bounce {
            0%, 20%, 53%, 80%, 100% {
                transform: translateY(0);
            }
            40%, 43% {
                transform: translateY(-10px);
            }
            70% {
                transform: translateY(-5px);
            }
            90% {
                transform: translateY(-2px);
            }
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .login-container {
                padding: 1rem;
            }
            
            .login-card {
                padding: 2rem;
            }
            
            .app-title {
                font-size: 1.5rem;
            }
            
            .feature-list {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
            unsafe_allow_html=True,
        )
