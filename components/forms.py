# components/forms.py
import streamlit as st
from datetime import date
from typing import Dict, List, Optional, Any
from config.settings import app_config


class BaseForm:
    """Base form component with common functionality"""

    def __init__(self, form_key: str, clear_on_submit: bool = True):
        self.form_key = form_key
        self.clear_on_submit = clear_on_submit
        self.errors = []

    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)

    def show_errors(self):
        """Display validation errors"""
        for error in self.errors:
            st.error(error)

    def clear_errors(self):
        """Clear validation errors"""
        self.errors = []


class ProjectForm(BaseForm):
    """Reusable project form component"""

    def render(
        self, initial_data: Optional[Dict[str, Any]] = None, submit_label: str = "บันทึก"
    ) -> Optional[Dict[str, Any]]:
        """Render project form and return submitted data"""

        with st.form(self.form_key, clear_on_submit=self.clear_on_submit):
            # Form fields
            project_name = st.text_input(
                "ชื่อโปรเจกต์ *",
                value=initial_data.get("ProjectName", "") if initial_data else "",
                max_chars=100,
            )

            description = st.text_area(
                "คำอธิบาย",
                value=initial_data.get("Description", "") if initial_data else "",
                height=100,
            )

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "วันที่เริ่มต้น *",
                    value=(
                        initial_data.get("StartDate", date.today())
                        if initial_data
                        else date.today()
                    ),
                )

            with col2:
                end_date = st.date_input(
                    "วันที่สิ้นสุด *",
                    value=(
                        initial_data.get("EndDate", date.today())
                        if initial_data
                        else date.today()
                    ),
                )

            status = st.selectbox(
                "สถานะ",
                options=app_config.PROJECT_STATUSES,
                index=app_config.PROJECT_STATUSES.index(
                    initial_data.get("Status", "Planning")
                    if initial_data
                    else "Planning"
                ),
            )

            submitted = st.form_submit_button(submit_label, type="primary")

            if submitted:
                # Validation
                self.clear_errors()

                if not project_name.strip():
                    self.add_error("กรุณากรอกชื่อโปรเจกต์")

                if end_date < start_date:
                    self.add_error("วันที่สิ้นสุดต้องมาหลังวันที่เริ่มต้น")

                if self.errors:
                    self.show_errors()
                    return None

                # Return form data
                return {
                    "project_name": project_name.strip(),
                    "description": description.strip(),
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                }

        return None


class TaskForm(BaseForm):
    """Reusable task form component"""

    def render(
        self,
        project_id: int,
        users: List[Dict],
        initial_data: Optional[Dict[str, Any]] = None,
        submit_label: str = "บันทึก",
    ) -> Optional[Dict[str, Any]]:
        """Render task form and return submitted data"""

        with st.form(self.form_key, clear_on_submit=self.clear_on_submit):
            # Form fields
            task_name = st.text_input(
                "ชื่องาน *",
                value=initial_data.get("TaskName", "") if initial_data else "",
                max_chars=100,
            )

            description = st.text_area(
                "คำอธิบายงาน",
                value=initial_data.get("Description", "") if initial_data else "",
                height=80,
            )

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "วันที่เริ่มต้น *",
                    value=(
                        initial_data.get("StartDate", date.today())
                        if initial_data
                        else date.today()
                    ),
                )

            with col2:
                end_date = st.date_input(
                    "วันที่สิ้นสุด *",
                    value=(
                        initial_data.get("EndDate", date.today())
                        if initial_data
                        else date.today()
                    ),
                )

            # User selection
            user_options = {user["Username"]: user["UserID"] for user in users}
            current_assignee = initial_data.get("Assignee") if initial_data else ""

            assignee_username = st.selectbox(
                "ผู้รับผิดชอบ *",
                options=list(user_options.keys()),
                index=(
                    list(user_options.keys()).index(current_assignee)
                    if current_assignee in user_options
                    else 0
                ),
            )

            col3, col4 = st.columns(2)
            with col3:
                status = st.selectbox(
                    "สถานะ",
                    options=app_config.TASK_STATUSES,
                    index=app_config.TASK_STATUSES.index(
                        initial_data.get("Status", "To Do") if initial_data else "To Do"
                    ),
                )

            with col4:
                progress = st.slider(
                    "ความคืบหน้า (%)",
                    min_value=0,
                    max_value=100,
                    value=int(initial_data.get("Progress", 0)) if initial_data else 0,
                    step=5,
                )

            submitted = st.form_submit_button(submit_label, type="primary")

            if submitted:
                # Validation
                self.clear_errors()

                if not task_name.strip():
                    self.add_error("กรุณากรอกชื่องาน")

                if not assignee_username:
                    self.add_error("กรุณาเลือกผู้รับผิดชอบ")

                if end_date < start_date:
                    self.add_error("วันที่สิ้นสุดต้องมาหลังวันที่เริ่มต้น")

                if self.errors:
                    self.show_errors()
                    return None

                # Return form data
                return {
                    "project_id": project_id,
                    "task_name": task_name.strip(),
                    "description": description.strip(),
                    "start_date": start_date,
                    "end_date": end_date,
                    "assignee_id": user_options[assignee_username],
                    "status": status,
                    "progress": progress,
                }

        return None


class UserForm(BaseForm):
    """Reusable user form component"""

    def render(
        self, submit_label: str = "ลงทะเบียน", show_role: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Render user registration form"""

        with st.form(self.form_key, clear_on_submit=self.clear_on_submit):
            username = st.text_input(
                "ชื่อผู้ใช้ *", max_chars=50, help="3-50 ตัวอักษร เฉพาะ a-z, 0-9, และ _"
            )

            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("รหัสผ่าน *", type="password", max_chars=255)
            with col2:
                confirm_password = st.text_input("ยืนยันรหัสผ่าน *", type="password")

            role = None
            if show_role:
                role = st.selectbox("บทบาท", options=app_config.USER_ROLES, index=0)

            submitted = st.form_submit_button(submit_label, type="primary")

            if submitted:
                # Validation
                self.clear_errors()

                if not username.strip():
                    self.add_error("กรุณากรอกชื่อผู้ใช้")
                elif len(username.strip()) < 3:
                    self.add_error("ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร")

                if not password:
                    self.add_error("กรุณากรอกรหัสผ่าน")
                elif len(password) < 6:
                    self.add_error("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")

                if password != confirm_password:
                    self.add_error("รหัสผ่านไม่ตรงกัน")

                if self.errors:
                    self.show_errors()
                    return None

                result = {"username": username.strip(), "password": password}

                if show_role and role:
                    result["role"] = role

                return result

        return None


# Factory functions for easy form creation
def create_project_form(form_key: str = "project_form") -> ProjectForm:
    """Factory function to create project form"""
    return ProjectForm(form_key)


def create_task_form(form_key: str = "task_form") -> TaskForm:
    """Factory function to create task form"""
    return TaskForm(form_key)


def create_user_form(form_key: str = "user_form") -> UserForm:
    """Factory function to create user form"""
    return UserForm(form_key)
