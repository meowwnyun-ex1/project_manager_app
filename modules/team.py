"""
Team Management Module
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TeamManager:
    """Team and user management"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def render_page(self):
        """Render team management page"""
        st.title("👥 Team Management")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Team Members")
        
        with col2:
            if st.button("👤 Add Member", use_container_width=True):
                st.session_state.show_new_member = True
        
        # New member form
        if st.session_state.get('show_new_member', False):
            self._render_new_member_form()
        
        # Load and display team members
        users = self.get_all_users()
        
        if users:
            self._render_team_overview(users)
            self._render_team_list(users)
        else:
            st.info("👥 No team members found.")
    
    def _render_new_member_form(self):
        """Render new team member form"""
        with st.expander("Add New Team Member", expanded=True):
            with st.form("new_member_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    username = st.text_input("Username *", placeholder="Enter username")
                    first_name = st.text_input("First Name *", placeholder="First name")
                    email = st.text_input("Email *", placeholder="email@company.com")
                    phone = st.text_input("Phone", placeholder="Phone number")
                
                with col2:
                    password = st.text_input("Password *", type="password", placeholder="Temporary password")
                    last_name = st.text_input("Last Name *", placeholder="Last name")
                    department = st.selectbox("Department", [
                        "Engineering", "Marketing", "Sales", "HR", "Finance", 
                        "Operations", "IT", "Quality", "R&D", "Other"
                    ])
                    role = st.selectbox("Role", ["User", "Manager", "Admin"])
                
                col_submit, col_cancel = st.columns(2)
                
                with col_submit:
                    submitted = st.form_submit_button("➕ Add Member", use_container_width=True)
                
                with col_cancel:
                    cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submitted:
                    if not all([username, first_name, last_name, email, password]):
                        st.error("❌ Please fill in all required fields!")
                    else:
                        member_data = {
                            'username': username.strip(),
                            'password': password,
                            'email': email.strip(),
                            'first_name': first_name.strip(),
                            'last_name': last_name.strip(),
                            'department': department,
                            'role': role,
                            'phone': phone.strip()
                        }
                        
                        with st.spinner("🔄 Adding team member..."):
                            success, message = self.create_user(member_data)
                            
                            if success:
                                st.success(f"✅ Team member '{first_name} {last_name}' added successfully!")
                                st.session_state.show_new_member = False
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to add member: {message}")
                
                if cancel:
                    st.session_state.show_new_member = False
                    st.rerun()
    
    def _render_team_overview(self, users: List[Dict[str, Any]]):
        """Render team overview statistics"""
        st.subheader("📊 Team Overview")
        
        # Calculate statistics
        total_members = len(users)
        departments = set(user.get('Department', 'Unknown') for user in users)
        roles = set(user.get('Role', 'User') for user in users)
        active_members = len([u for u in users if u.get('IsActive', True)])
        
        # Recent logins (last 7 days)
        recent_logins = 0
        for user in users:
            last_login = user.get('LastLoginDate')
            if last_login:
                try:
                    if isinstance(last_login, str):
                        last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    days_ago = (datetime.now() - last_login).days
                    if days_ago <= 7:
                        recent_logins += 1
                except:
                    pass
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Members", total_members)
        
        with col2:
            st.metric("Departments", len(departments))
        
        with col3:
            st.metric("Roles", len(roles))
        
        with col4:
            st.metric("Recent Logins", f"{recent_logins} (7 days)")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_department_chart(users)
        
        with col2:
            self._render_role_chart(users)
    
    def _render_department_chart(self, users: List[Dict[str, Any]]):
        """Render department distribution chart"""
        st.markdown("#### Department Distribution")
        
        # Count by department
        dept_counts = {}
        for user in users:
            dept = user.get('Department', 'Unknown')
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        if dept_counts:
            fig = px.pie(
                values=list(dept_counts.values()),
                names=list(dept_counts.keys()),
                color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#48c6ef', '#feca57']
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_role_chart(self, users: List[Dict[str, Any]]):
        """Render role distribution chart"""
        st.markdown("#### Role Distribution")
        
        # Count by role
        role_counts = {}
        for user in users:
            role = user.get('Role', 'User')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        if role_counts:
            fig = px.bar(
                x=list(role_counts.keys()),
                y=list(role_counts.values()),
                color=list(role_counts.values()),
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_team_list(self, users: List[Dict[str, Any]]):
        """Render team member list"""
        st.subheader("👥 Team Members")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dept_filter = st.selectbox(
                "Filter by Department",
                ["All"] + list(set([u.get('Department', 'Unknown') for u in users]))
            )
        
        with col2:
            role_filter = st.selectbox(
                "Filter by Role",
                ["All"] + list(set([u.get('Role',