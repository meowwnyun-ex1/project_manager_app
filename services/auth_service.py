# services/auth_service.py
import streamlit as st
import bcrypt
from services.enhanced_db_service import DatabaseService
from config.settings import app_config


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def register_user(username: str, password: str, role: str = "User") -> bool:
    """Register new user"""
    try:
        hashed_pwd = hash_password(password)
        query = "INSERT INTO Users (Username, PasswordHash, Role) VALUES (?, ?, ?)"
        return DatabaseService.execute_query(query, (username, hashed_pwd, role))
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user login"""
    query = "SELECT UserID, Username, PasswordHash, Role FROM Users WHERE Username = ?"
    user_data = DatabaseService.fetch_one(query, (username,))

    if user_data and check_password(password, user_data["PasswordHash"]):
        # Set session state
        st.session_state[app_config.SESSION_KEYS["logged_in"]] = True
        st.session_state[app_config.SESSION_KEYS["user_id"]] = user_data["UserID"]
        st.session_state[app_config.SESSION_KEYS["username"]] = user_data["Username"]
        st.session_state[app_config.SESSION_KEYS["user_role"]] = user_data["Role"]
        return True
    return False


def logout():
    """Clear user session"""
    for key in app_config.SESSION_KEYS.values():
        if key in st.session_state:
            del st.session_state[key]
