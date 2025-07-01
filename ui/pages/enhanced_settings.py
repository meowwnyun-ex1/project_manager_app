# ui/pages/enhanced_settings.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any
import time


def apply_modern_css():
    """Apply modern CSS for settings page"""
    st.markdown(
        """
    <style>
    /* Settings Page Styles */
    .settings-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .settings-section {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .settings-section:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
        background: rgba(255, 255, 255, 0.15);
    }
    
    .settings-header {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .section-title {
        color: white;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        padding-bottom: 0.5rem;
    }
    
    .setting-item {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .setting-label {
        color: white;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .danger-zone {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        border: 2px solid #ff4757;
        animation: pulse-danger 2s infinite;
    }
    
    @keyframes pulse-danger {
        0% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 71, 87, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
    }
    
    .success-message {
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 500;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .admin-panel {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        border: 2px solid #3498db;
    }
    
    .stats-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .stats-card:hover {
        transform: scale(1.05);
        background: rgba(255, 255, 255, 0.2);
    }
    
    .stats-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d2ff;
        margin-bottom: 0.5rem;
    }
    
    .stats-label {
        color: white;
        font-size: 1rem;
        font-weight: 500;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_user_preferences():
    """Render user preferences section"""
    st.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">👤 User Preferences</div>', unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Display Name</div>', unsafe_allow_html=True
        )
        display_name = st.text_input(
            "", value=st.session_state.get("username", ""), key="display_name"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Email Notifications</div>',
            unsafe_allow_html=True,
        )
        email_notifications = st.checkbox(
            "Enable email notifications", value=True, key="email_notif"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown('<div class="setting-label">Language</div>', unsafe_allow_html=True)
        language = st.selectbox(
            "", ["English", "ไทย", "中文", "日本語"], key="language"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Time Zone</div>', unsafe_allow_html=True
        )
        timezone = st.selectbox(
            "",
            ["UTC+7 (Bangkok)", "UTC+0 (London)", "UTC-5 (New York)", "UTC+9 (Tokyo)"],
            key="timezone",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Date Format</div>', unsafe_allow_html=True
        )
        date_format = st.selectbox(
            "", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"], key="date_format"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Dashboard Theme</div>', unsafe_allow_html=True
        )
        theme = st.selectbox(
            "", ["Auto", "Light", "Dark", "Blue"], key="dashboard_theme"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("💾 Save Preferences", key="save_prefs"):
        # Save preferences logic here
        st.markdown(
            '<div class="success-message">✅ Preferences saved successfully!</div>',
            unsafe_allow_html=True,
        )
        time.sleep(1)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_security_settings():
    """Render security settings section"""
    st.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">🔐 Security Settings</div>', unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Change Password</div>', unsafe_allow_html=True
        )
        current_password = st.text_input(
            "Current Password", type="password", key="current_pwd"
        )
        new_password = st.text_input("New Password", type="password", key="new_pwd")
        confirm_password = st.text_input(
            "Confirm New Password", type="password", key="confirm_pwd"
        )

        if st.button("🔑 Change Password", key="change_pwd"):
            if new_password == confirm_password:
                # Password change logic here
                st.markdown(
                    '<div class="success-message">✅ Password changed successfully!</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.error("Passwords don't match!")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Two-Factor Authentication</div>',
            unsafe_allow_html=True,
        )
        tfa_enabled = st.checkbox("Enable 2FA", value=False, key="tfa")

        if tfa_enabled:
            st.info("📱 Scan QR code with your authenticator app")
            # Generate QR code logic here

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Session Settings</div>', unsafe_allow_html=True
        )
        session_timeout = st.selectbox(
            "Session Timeout",
            ["15 minutes", "30 minutes", "1 hour", "2 hours", "Never"],
            key="session_timeout",
        )
        auto_logout = st.checkbox(
            "Auto logout on browser close", value=True, key="auto_logout"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_notification_settings():
    """Render notification settings section"""
    st.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">� Notification Settings</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Email Notifications</div>',
            unsafe_allow_html=True,
        )

        email_task_assigned = st.checkbox(
            "New task assigned", value=True, key="email_task"
        )
        email_task_due = st.checkbox("Task due soon", value=True, key="email_due")
        email_project_update = st.checkbox(
            "Project updates", value=True, key="email_project"
        )
        email_team_mention = st.checkbox(
            "Team mentions", value=True, key="email_mention"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Push Notifications</div>',
            unsafe_allow_html=True,
        )

        push_enabled = st.checkbox(
            "Enable push notifications", value=True, key="push_enabled"
        )
        push_sound = st.checkbox("Notification sound", value=True, key="push_sound")
        push_vibration = st.checkbox("Vibration", value=True, key="push_vibration")

        st.markdown(
            '<div class="setting-label">Notification Frequency</div>',
            unsafe_allow_html=True,
        )
        frequency = st.selectbox(
            "", ["Instant", "Every 15 minutes", "Hourly", "Daily"], key="notif_freq"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_system_stats():
    """Render system statistics"""
    st.markdown('<div class="settings-section admin-panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">� System Statistics</div>', unsafe_allow_html=True
    )

    # Mock data for demo
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class="stats-card">
            <div class="stats-number">156</div>
            <div class="stats-label">Total Users</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="stats-card">
            <div class="stats-number">89</div>
            <div class="stats-label">Active Projects</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="stats-card">
            <div class="stats-number">234</div>
            <div class="stats-label">Tasks Completed</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
        <div class="stats-card">
            <div class="stats-number">95%</div>
            <div class="stats-label">System Uptime</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # System performance chart
    st.markdown(
        '<div class="setting-label">System Performance (Last 24 Hours)</div>',
        unsafe_allow_html=True,
    )

    # Generate mock performance data
    hours = list(range(24))
    cpu_usage = [20 + (i * 2) % 40 + (i % 3) * 5 for i in hours]
    memory_usage = [30 + (i * 1.5) % 30 + (i % 4) * 8 for i in hours]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=cpu_usage,
            mode="lines+markers",
            name="CPU Usage %",
            line=dict(color="#00d2ff"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=memory_usage,
            mode="lines+markers",
            name="Memory Usage %",
            line=dict(color="#ff6b6b"),
        )
    )

    fig.update_layout(
        title="System Performance",
        xaxis_title="Hour",
        yaxis_title="Usage %",
        template="plotly_dark",
        height=300,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_admin_panel():
    """Render admin panel (only for admin users)"""
    if st.session_state.get("user_role") == "Admin":
        st.markdown(
            '<div class="settings-section danger-zone">', unsafe_allow_html=True
        )
        st.markdown(
            '<div class="section-title">⚠️ Admin Panel - Danger Zone</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="setting-item">', unsafe_allow_html=True)
            st.markdown(
                '<div class="setting-label">System Maintenance</div>',
                unsafe_allow_html=True,
            )

            if st.button("🔧 Run System Maintenance", key="maintenance"):
                with st.spinner("Running system maintenance..."):
                    time.sleep(3)
                st.success("✅ System maintenance completed!")

            if st.button("🗄️ Backup Database", key="backup"):
                with st.spinner("Creating database backup..."):
                    time.sleep(2)
                st.success("✅ Database backup created!")

            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="setting-item">', unsafe_allow_html=True)
            st.markdown(
                '<div class="setting-label">Danger Zone</div>', unsafe_allow_html=True
            )

            st.warning("⚠️ These actions are irreversible!")

            if st.button("�️ Clear All Logs", key="clear_logs"):
                if st.checkbox(
                    "I understand this action is irreversible", key="confirm_logs"
                ):
                    st.success("✅ All logs cleared!")

            if st.button("💥 Reset All Settings", key="reset_settings"):
                if st.checkbox(
                    "I understand this will reset ALL settings", key="confirm_reset"
                ):
                    st.success("✅ All settings reset to default!")

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def render_api_settings():
    """Render API settings section"""
    st.markdown('<div class="settings-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">🔌 API Settings</div>', unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">API Access</div>', unsafe_allow_html=True
        )

        api_enabled = st.checkbox("Enable API access", value=False, key="api_enabled")

        if api_enabled:
            api_key = st.text_input(
                "API Key",
                value="pk_live_1234567890abcdef",
                disabled=True,
                key="api_key",
            )
            if st.button("🔄 Regenerate API Key", key="regen_api"):
                st.success("✅ New API key generated!")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="setting-item">', unsafe_allow_html=True)
        st.markdown(
            '<div class="setting-label">Rate Limiting</div>', unsafe_allow_html=True
        )

        rate_limit = st.selectbox(
            "Requests per minute", [10, 50, 100, 500, 1000], key="rate_limit"
        )
        webhook_url = st.text_input(
            "Webhook URL", placeholder="https://your-app.com/webhook", key="webhook"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_enhanced_settings():
    """Main function to render enhanced settings page"""

    # Apply modern CSS
    apply_modern_css()

    # Page header
    st.markdown(
        """
    <div class="settings-container">
        <div class="settings-header">⚙️ System Settings</div>
        <p style="color: white; text-align: center; font-size: 1.1rem; margin-bottom: 0;">
            Configure your preferences and system settings
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Settings tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "👤 User",
            "🔐 Security",
            "🔔 Notifications",
            "📊 Statistics",
            "👥 Admin",
            "🔌 API",
        ]
    )

    with tab1:
        render_user_preferences()

    with tab2:
        render_security_settings()

    with tab3:
        render_notification_settings()

    with tab4:
        render_system_stats()

    with tab5:
        render_admin_panel()

    with tab6:
        render_api_settings()

    # Footer
    st.markdown(
        """
    <div style="text-align: center; margin-top: 3rem; padding: 2rem; 
                background: rgba(255, 255, 255, 0.1); border-radius: 15px;">
        <p style="color: white; margin: 0;">
            🚀 Project Manager Pro v3.0 | Built with ❤️ using Streamlit
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


# Export the main function
__all__ = ["render_enhanced_settings"]
