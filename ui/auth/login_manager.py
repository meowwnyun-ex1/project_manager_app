# ui/auth/login_manager.py
import streamlit as st
from services.enhanced_auth_service import get_auth_service


class LoginManager:
    def __init__(self):
        self.auth_service = get_auth_service()

    def render_login_form(self) -> bool:
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if username and password:
                    user = self.auth_service.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        st.success("Login successful!")
                        return True
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Please enter username and password")
        return False


# ui/navigation/enhanced_navigation.py
import streamlit as st
from streamlit_option_menu import option_menu


class EnhancedNavigation:
    def render_navigation(self) -> str:
        with st.sidebar:
            selected = option_menu(
                "Navigation",
                ["Dashboard", "Projects", "Tasks", "Settings"],
                icons=["speedometer2", "folder", "check-square", "gear"],
                menu_icon="cast",
                default_index=0,
            )
            return selected.lower()


# ui/components/notification_system.py
import streamlit as st


class NotificationSystem:
    def render_notifications(self):
        pass  # Placeholder

    def get_unread_count(self) -> int:
        return 0  # Placeholder


# config/enhanced_config.py
def get_config():
    return {"debug_mode": True, "app_name": "Project Manager Pro v3.0"}
