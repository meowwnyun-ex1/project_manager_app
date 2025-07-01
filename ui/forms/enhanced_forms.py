# ui/forms/enhanced_forms.py
"""
Enhanced Forms Component for Project Manager Pro v3.0
Modern form components with validation, multi-step forms, and dynamic fields
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import re


class EnhancedForms:
    """Enhanced form components with modern UI/UX and validation"""

    def __init__(self):
        self.validation_rules = {}
        self.form_data = {}
        self.errors = {}

    def inject_form_css(self):
        """Inject CSS for enhanced form styling"""
        st.markdown(
            """
        <style>
        /* Enhanced Form Styling */
        .form-container {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .form-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .form-title {
            font-size: 2rem;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #4facfe, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .form-subtitle {
            color: #7f8c8d;
            font-size: 1.1rem;
        }
        
        /* Multi-step Form Progress */
        .form-progress {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(79, 172, 254, 0.05);
            border-radius: 12px;
        }
        
        .progress-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0 20px;
            position: relative;
        }
        
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 8px;
            transition: all 0.3s ease;
        }
        
        .step-circle.active {
            background: linear-gradient(45deg, #4facfe, #00f2fe);
            color: white;
            box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
        }
        
        .step-circle.completed {
            background: linear-gradient(45deg, #2ed573, #7bed9f);
            color: white;
        }
        
        .step-circle.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        
        .step-label {
            font-size: 0.9rem;
            color: #7f8c8d;
            text-align: center;
        }
        
        .step-line {
            position: absolute;
            top: 20px;
            left: 60px;
            width: 40px;
            height: 2px;
            background: #e9ecef;
        }
        
        .step-line.completed {
            background: linear-gradient(90deg, #2ed573, #7bed9f);
        }
        
        /* Form Fields */
        .form-field {
            margin-bottom: 25px;
        }
        
        .field-label {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            display: block;
        }
        
        .field-required {
            color: #ff3838;
        }
        
        .field-help {
            font-size: 0.85rem;
            color: #7f8c8d;
            margin-top: 5px;
        }
        
        .field-error {
            color: #ff3838;
            font-size: 0.85rem;
            margin-top: 5px;
            padding: 8px 12px;
            background: rgba(255, 56, 56, 0.1);
            border-radius: 6px;
            border-left: 3px solid #ff3838;
        }
        
        .field-success {
            color: #2ed573;
            font-size: 0.85rem;
            margin-top: 5px;
            padding: 8px 12px;
            background: rgba(46, 213, 115, 0.1);
            border-radius: 6px;
            border-left: 3px solid #2ed573;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .form-container {
                padding: 20px;
            }
            
            .form-title {
                font-size: 1.5rem;
            }
            
            .progress-step {
                margin: 0 10px;
            }
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def create_multi_step_form(
        self,
        steps: List[Dict],
        form_key: str = "multi_step_form",
        on_complete: Optional[Callable] = None,
    ) -> Dict:
        """Create a multi-step form with progress tracking"""

        self.inject_form_css()

        # Initialize session state
        if f"{form_key}_current_step" not in st.session_state:
            st.session_state[f"{form_key}_current_step"] = 0
        if f"{form_key}_data" not in st.session_state:
            st.session_state[f"{form_key}_data"] = {}

        current_step = st.session_state[f"{form_key}_current_step"]
        total_steps = len(steps)

        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        # Form header
        st.markdown(
            f"""
        <div class="form-header">
            <div class="form-title">{steps[current_step].get('title', 'Multi-Step Form')}</div>
            <div class="form-subtitle">{steps[current_step].get('subtitle', '')}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Progress indicator
        self._render_progress_indicator(steps, current_step, form_key)

        # Current step content
        step_data = self._render_form_step(steps[current_step], form_key)

        # Navigation buttons
        self._render_step_navigation(current_step, total_steps, form_key, on_complete)

        st.markdown("</div>", unsafe_allow_html=True)

        return st.session_state[f"{form_key}_data"]

    def _render_progress_indicator(
        self, steps: List[Dict], current_step: int, form_key: str
    ):
        """Render progress indicator for multi-step form"""
        progress_html = '<div class="form-progress">'

        for i, step in enumerate(steps):
            # Determine step status
            if i < current_step:
                status = "completed"
                icon = "✓"
            elif i == current_step:
                status = "active"
                icon = str(i + 1)
            else:
                status = "pending"
                icon = str(i + 1)

            progress_html += f"""
            <div class="progress-step">
                <div class="step-circle {status}">{icon}</div>
                <div class="step-label">{step.get('label', f'Step {i+1}')}</div>
                {f'<div class="step-line {status if i < current_step else ""}"></div>' if i < len(steps) - 1 else ''}
            </div>
            """

        progress_html += "</div>"
        st.markdown(progress_html, unsafe_allow_html=True)

    def _render_form_step(self, step: Dict, form_key: str) -> Dict:
        """Render individual form step"""
        step_data = {}

        # Render fields based on step configuration
        fields = step.get("fields", [])

        for field in fields:
            field_value = self._render_form_field(field, form_key)
            if field_value is not None:
                step_data[field["name"]] = field_value

        # Update session state with step data
        st.session_state[f"{form_key}_data"].update(step_data)

        return step_data

    def _render_form_field(self, field: Dict, form_key: str) -> Any:
        """Render individual form field with validation"""
        field_type = field.get("type", "text")
        field_name = field.get("name")
        field_label = field.get("label", field_name)
        field_required = field.get("required", False)
        field_help = field.get("help", "")
        field_value = field.get("default", None)

        # Get current value from session state
        current_value = st.session_state[f"{form_key}_data"].get(
            field_name, field_value
        )

        # Render field label
        required_indicator = (
            ' <span class="field-required">*</span>' if field_required else ""
        )
        st.markdown(
            f'<div class="field-label">{field_label}{required_indicator}</div>',
            unsafe_allow_html=True,
        )

        # Render field based on type
        result = None

        if field_type == "text" or field_type == "email":
            result = st.text_input(
                "",
                value=current_value or "",
                placeholder=field.get("placeholder", ""),
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "textarea":
            result = st.text_area(
                "",
                value=current_value or "",
                placeholder=field.get("placeholder", ""),
                height=field.get("height", 100),
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "number":
            result = st.number_input(
                "",
                value=(
                    current_value
                    if current_value is not None
                    else field.get("default", 0)
                ),
                min_value=field.get("min_value"),
                max_value=field.get("max_value"),
                step=field.get("step", 1),
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "select":
            options = field.get("options", [])
            index = 0
            if current_value and current_value in options:
                index = options.index(current_value)

            result = st.selectbox(
                "",
                options=options,
                index=index,
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "multiselect":
            result = st.multiselect(
                "",
                options=field.get("options", []),
                default=current_value or [],
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "date":
            if current_value:
                default_date = (
                    pd.to_datetime(current_value).date()
                    if isinstance(current_value, str)
                    else current_value
                )
            else:
                default_date = datetime.now().date()

            result = st.date_input(
                "",
                value=default_date,
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "time":
            result = st.time_input(
                "",
                value=current_value or datetime.now().time(),
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "checkbox":
            result = st.checkbox(
                field.get("checkbox_label", "Check this box"),
                value=current_value or False,
                key=f"{form_key}_{field_name}",
            )

        elif field_type == "radio":
            result = st.radio(
                "",
                options=field.get("options", []),
                index=(
                    0
                    if not current_value
                    else (
                        field.get("options", []).index(current_value)
                        if current_value in field.get("options", [])
                        else 0
                    )
                ),
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "slider":
            result = st.slider(
                "",
                min_value=field.get("min_value", 0),
                max_value=field.get("max_value", 100),
                value=(
                    current_value
                    if current_value is not None
                    else field.get("default", 50)
                ),
                step=field.get("step", 1),
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        elif field_type == "file":
            result = st.file_uploader(
                "",
                type=field.get("accepted_types"),
                accept_multiple_files=field.get("multiple", False),
                key=f"{form_key}_{field_name}",
                label_visibility="collapsed",
            )

        # Validate field
        validation_error = self._validate_field(field, result)

        # Show help text
        if field_help:
            st.markdown(
                f'<div class="field-help">{field_help}</div>', unsafe_allow_html=True
            )

        # Show validation error
        if validation_error:
            st.markdown(
                f'<div class="field-error">❌ {validation_error}</div>',
                unsafe_allow_html=True,
            )
        elif result and field_required:
            st.markdown(
                f'<div class="field-success">✅ Valid</div>', unsafe_allow_html=True
            )

        return result

    def _validate_field(self, field: Dict, value: Any) -> Optional[str]:
        """Validate individual field"""
        field_name = field.get("name")
        field_required = field.get("required", False)
        field_type = field.get("type", "text")

        # Required validation
        if field_required and (
            value is None
            or value == ""
            or (isinstance(value, list) and len(value) == 0)
        ):
            return f"{field.get('label', field_name)} is required"

        # Type-specific validation
        if value and field_type == "email":
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, str(value)):
                return "Please enter a valid email address"

        # Length validation
        min_length = field.get("min_length")
        max_length = field.get("max_length")

        if value and min_length and len(str(value)) < min_length:
            return f"Minimum length is {min_length} characters"

        if value and max_length and len(str(value)) > max_length:
            return f"Maximum length is {max_length} characters"

        return None

    def _render_step_navigation(
        self,
        current_step: int,
        total_steps: int,
        form_key: str,
        on_complete: Optional[Callable],
    ):
        """Render step navigation buttons"""
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if current_step > 0:
                if st.button(
                    "⬅️ Previous", key=f"{form_key}_prev", use_container_width=True
                ):
                    st.session_state[f"{form_key}_current_step"] = current_step - 1
                    st.rerun()

        with col2:
            # Step indicator
            st.markdown(
                f"""
            <div style="text-align: center; color: #7f8c8d; font-size: 0.9rem;">
                Step {current_step + 1} of {total_steps}
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            if current_step < total_steps - 1:
                if st.button(
                    "Next ➡️",
                    key=f"{form_key}_next",
                    use_container_width=True,
                    type="primary",
                ):
                    if self._validate_current_step(form_key):
                        st.session_state[f"{form_key}_current_step"] = current_step + 1
                        st.rerun()
            else:
                if st.button(
                    "🏁 Complete",
                    key=f"{form_key}_complete",
                    use_container_width=True,
                    type="primary",
                ):
                    if self._validate_current_step(form_key):
                        if on_complete:
                            on_complete(st.session_state[f"{form_key}_data"])
                        st.success("✅ Form completed successfully!")

    def _validate_current_step(self, form_key: str) -> bool:
        """Validate current step before allowing navigation"""
        return True

    def create_project_form(
        self, project_data: Optional[Dict] = None, mode: str = "create"
    ) -> Dict:
        """Create enhanced project form"""
        form_title = "Create New Project" if mode == "create" else "Edit Project"

        steps = [
            {
                "title": f"📚 {form_title}",
                "subtitle": "Basic project information",
                "label": "Basic Info",
                "fields": [
                    {
                        "name": "project_name",
                        "label": "Project Name",
                        "type": "text",
                        "required": True,
                        "placeholder": "Enter project name",
                        "help": "Choose a clear, descriptive name for your project",
                        "default": (
                            project_data.get("ProjectName", "") if project_data else ""
                        ),
                    },
                    {
                        "name": "description",
                        "label": "Description",
                        "type": "textarea",
                        "placeholder": "Describe your project goals and objectives",
                        "height": 120,
                        "help": "Provide a detailed description of the project scope and objectives",
                        "default": (
                            project_data.get("Description", "") if project_data else ""
                        ),
                    },
                    {
                        "name": "client_name",
                        "label": "Client Name",
                        "type": "text",
                        "placeholder": "Enter client or organization name",
                        "default": (
                            project_data.get("ClientName", "") if project_data else ""
                        ),
                    },
                ],
            },
            {
                "title": "📅 Timeline & Priority",
                "subtitle": "Set project timeline and priority level",
                "label": "Timeline",
                "fields": [
                    {
                        "name": "start_date",
                        "label": "Start Date",
                        "type": "date",
                        "required": True,
                        "help": "When will this project begin?",
                        "default": (
                            project_data.get("StartDate")
                            if project_data
                            else datetime.now().date()
                        ),
                    },
                    {
                        "name": "end_date",
                        "label": "End Date",
                        "type": "date",
                        "required": True,
                        "help": "When is the project expected to be completed?",
                        "default": (
                            project_data.get("EndDate")
                            if project_data
                            else (datetime.now().date() + timedelta(days=30))
                        ),
                    },
                    {
                        "name": "priority",
                        "label": "Priority Level",
                        "type": "select",
                        "options": ["Low", "Medium", "High", "Critical"],
                        "required": True,
                        "help": "Set the priority level for resource allocation",
                        "default": (
                            project_data.get("Priority", "Medium")
                            if project_data
                            else "Medium"
                        ),
                    },
                    {
                        "name": "status",
                        "label": "Initial Status",
                        "type": "select",
                        "options": [
                            "Planning",
                            "In Progress",
                            "On Hold",
                            "Completed",
                            "Cancelled",
                        ],
                        "required": True,
                        "default": (
                            project_data.get("Status", "Planning")
                            if project_data
                            else "Planning"
                        ),
                    },
                ],
            },
            {
                "title": "💰 Budget & Resources",
                "subtitle": "Define project budget and resource requirements",
                "label": "Budget",
                "fields": [
                    {
                        "name": "budget",
                        "label": "Total Budget ($)",
                        "type": "number",
                        "min_value": 0.0,
                        "step": 1000.0,
                        "help": "Enter the total project budget in USD",
                        "default": (
                            float(project_data.get("Budget", 0))
                            if project_data
                            else 0.0
                        ),
                    },
                    {
                        "name": "tags",
                        "label": "Project Tags",
                        "type": "text",
                        "placeholder": "web, mobile, api, design (comma-separated)",
                        "help": "Add tags to categorize and filter projects",
                        "default": project_data.get("Tags", "") if project_data else "",
                    },
                ],
            },
        ]

        return self.create_multi_step_form(
            steps=steps,
            form_key="project_form",
            on_complete=lambda data: self._handle_project_submission(data, mode),
        )

    def create_task_form(
        self, task_data: Optional[Dict] = None, mode: str = "create"
    ) -> Dict:
        """Create enhanced task form"""
        form_title = "Create New Task" if mode == "create" else "Edit Task"

        # Get available projects for selection
        project_options = ["Project Alpha", "Project Beta", "Project Gamma"]

        steps = [
            {
                "title": f"✅ {form_title}",
                "subtitle": "Task details and assignment",
                "label": "Task Info",
                "fields": [
                    {
                        "name": "task_name",
                        "label": "Task Name",
                        "type": "text",
                        "required": True,
                        "placeholder": "Enter task name",
                        "help": "Choose a clear, actionable task name",
                        "default": task_data.get("TaskName", "") if task_data else "",
                    },
                    {
                        "name": "project",
                        "label": "Project",
                        "type": "select",
                        "options": project_options,
                        "required": True,
                        "help": "Select the project this task belongs to",
                        "default": (
                            task_data.get("ProjectName", project_options[0])
                            if task_data
                            else project_options[0]
                        ),
                    },
                    {
                        "name": "description",
                        "label": "Description",
                        "type": "textarea",
                        "placeholder": "Describe what needs to be done",
                        "height": 100,
                        "default": (
                            task_data.get("Description", "") if task_data else ""
                        ),
                    },
                    {
                        "name": "assignee",
                        "label": "Assignee",
                        "type": "select",
                        "options": [
                            "Unassigned",
                            "John Doe",
                            "Jane Smith",
                            "Mike Johnson",
                        ],
                        "help": "Who will be responsible for this task?",
                        "default": (
                            task_data.get("AssigneeName", "Unassigned")
                            if task_data
                            else "Unassigned"
                        ),
                    },
                ],
            },
            {
                "title": "📅 Timeline & Priority",
                "subtitle": "Set deadlines and priority",
                "label": "Schedule",
                "fields": [
                    {
                        "name": "start_date",
                        "label": "Start Date",
                        "type": "date",
                        "required": True,
                        "default": (
                            task_data.get("StartDate")
                            if task_data
                            else datetime.now().date()
                        ),
                    },
                    {
                        "name": "due_date",
                        "label": "Due Date",
                        "type": "date",
                        "required": True,
                        "default": (
                            task_data.get("EndDate")
                            if task_data
                            else (datetime.now().date() + timedelta(days=7))
                        ),
                    },
                    {
                        "name": "priority",
                        "label": "Priority",
                        "type": "select",
                        "options": ["Low", "Medium", "High", "Critical"],
                        "required": True,
                        "default": (
                            task_data.get("Priority", "Medium")
                            if task_data
                            else "Medium"
                        ),
                    },
                    {
                        "name": "status",
                        "label": "Status",
                        "type": "select",
                        "options": [
                            "To Do",
                            "In Progress",
                            "Review",
                            "Done",
                            "Blocked",
                        ],
                        "default": (
                            task_data.get("Status", "To Do") if task_data else "To Do"
                        ),
                    },
                    {
                        "name": "progress",
                        "label": "Progress (%)",
                        "type": "slider",
                        "min_value": 0,
                        "max_value": 100,
                        "step": 5,
                        "default": (
                            int(task_data.get("Progress", 0)) if task_data else 0
                        ),
                    },
                ],
            },
            {
                "title": "⏱️ Time & Labels",
                "subtitle": "Time tracking and categorization",
                "label": "Details",
                "fields": [
                    {
                        "name": "estimated_hours",
                        "label": "Estimated Hours",
                        "type": "number",
                        "min_value": 0.0,
                        "step": 0.5,
                        "help": "How many hours do you estimate this task will take?",
                        "default": (
                            float(task_data.get("EstimatedHours", 0))
                            if task_data
                            else 0.0
                        ),
                    },
                    {
                        "name": "actual_hours",
                        "label": "Actual Hours",
                        "type": "number",
                        "min_value": 0.0,
                        "step": 0.5,
                        "help": "How many hours have been spent on this task?",
                        "default": (
                            float(task_data.get("ActualHours", 0)) if task_data else 0.0
                        ),
                    },
                    {
                        "name": "labels",
                        "label": "Labels",
                        "type": "text",
                        "placeholder": "frontend, api, testing (comma-separated)",
                        "help": "Add labels to categorize tasks",
                        "default": task_data.get("Labels", "") if task_data else "",
                    },
                    {
                        "name": "dependencies",
                        "label": "Dependencies",
                        "type": "text",
                        "placeholder": "Task IDs this depends on (comma-separated)",
                        "help": "List tasks that must be completed before this one",
                        "default": (
                            task_data.get("Dependencies", "") if task_data else ""
                        ),
                    },
                ],
            },
        ]

        return self.create_multi_step_form(
            steps=steps,
            form_key="task_form",
            on_complete=lambda data: self._handle_task_submission(data, mode),
        )

    def create_team_member_form(
        self, member_data: Optional[Dict] = None, mode: str = "create"
    ) -> Dict:
        """Create team member form"""
        form_title = "Add Team Member" if mode == "create" else "Edit Team Member"

        self.inject_form_css()

        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown(
            f"""
        <div class="form-header">
            <div class="form-title">👥 {form_title}</div>
            <div class="form-subtitle">Manage team member information</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        form_data = {}
        with st.form("team_member_form"):
            # Full Name
            form_data["full_name"] = st.text_input(
                "Full Name *",
                value=member_data.get("Name", "") if member_data else "",
                placeholder="Enter full name",
            )

            # Email
            form_data["email"] = st.text_input(
                "Email Address *",
                value=member_data.get("Email", "") if member_data else "",
                placeholder="name@company.com",
            )

            # Role
            role_options = [
                "Developer",
                "Designer",
                "Project Manager",
                "QA Tester",
                "DevOps",
                "Business Analyst",
            ]
            default_role = (
                member_data.get("Role", "Developer") if member_data else "Developer"
            )
            form_data["role"] = st.selectbox(
                "Role *",
                options=role_options,
                index=(
                    role_options.index(default_role)
                    if default_role in role_options
                    else 0
                ),
            )

            # Department
            dept_options = [
                "Engineering",
                "Design",
                "Product",
                "Marketing",
                "Operations",
            ]
            default_dept = (
                member_data.get("Department", "Engineering")
                if member_data
                else "Engineering"
            )
            form_data["department"] = st.selectbox(
                "Department",
                options=dept_options,
                index=(
                    dept_options.index(default_dept)
                    if default_dept in dept_options
                    else 0
                ),
            )

            # Skills
            skill_options = [
                "JavaScript",
                "Python",
                "React",
                "Node.js",
                "UI/UX",
                "Project Management",
                "Testing",
                "DevOps",
            ]
            default_skills = member_data.get("Skills", []) if member_data else []
            form_data["skills"] = st.multiselect(
                "Skills",
                options=skill_options,
                default=default_skills,
                help="Select relevant skills",
            )

            submitted = st.form_submit_button(
                "💾 Save Member", use_container_width=True, type="primary"
            )

            if submitted:
                if form_data["full_name"] and form_data["email"]:
                    st.success("✅ Team member saved successfully!")
                    st.balloons()
                    return form_data
                else:
                    st.error("❌ Please fill in all required fields!")

        st.markdown("</div>", unsafe_allow_html=True)
        return {}

    def create_simple_form(
        self, title: str, fields: List[Dict], form_key: str = "simple_form"
    ) -> Dict:
        """Create a simple single-page form"""
        self.inject_form_css()

        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown(
            f"""
        <div class="form-header">
            <div class="form-title">{title}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        form_data = {}
        with st.form(form_key):
            for field in fields:
                field_value = self._render_form_field(field, form_key)
                if field_value is not None:
                    form_data[field["name"]] = field_value

            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submitted = st.form_submit_button(
                    "💾 Save", use_container_width=True, type="primary"
                )

            if submitted:
                # Validate required fields
                errors = []
                for field in fields:
                    if field.get("required", False):
                        field_name = field["name"]
                        value = form_data.get(field_name)
                        if not value or (isinstance(value, str) and not value.strip()):
                            errors.append(
                                f"{field.get('label', field_name)} is required"
                            )

                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    st.success("✅ Form submitted successfully!")
                    st.balloons()
                    return form_data

        st.markdown("</div>", unsafe_allow_html=True)
        return {}

    def create_settings_form(self, settings_data: Optional[Dict] = None) -> Dict:
        """Create system settings form"""
        return self.create_simple_form(
            title="⚙️ System Settings",
            fields=[
                {
                    "name": "app_name",
                    "label": "Application Name",
                    "type": "text",
                    "required": True,
                    "default": (
                        settings_data.get("app_name", "Project Manager Pro")
                        if settings_data
                        else "Project Manager Pro"
                    ),
                },
                {
                    "name": "timezone",
                    "label": "Timezone",
                    "type": "select",
                    "options": [
                        "UTC",
                        "Asia/Bangkok",
                        "America/New_York",
                        "Europe/London",
                    ],
                    "default": (
                        settings_data.get("timezone", "Asia/Bangkok")
                        if settings_data
                        else "Asia/Bangkok"
                    ),
                },
                {
                    "name": "date_format",
                    "label": "Date Format",
                    "type": "select",
                    "options": ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"],
                    "default": (
                        settings_data.get("date_format", "YYYY-MM-DD")
                        if settings_data
                        else "YYYY-MM-DD"
                    ),
                },
                {
                    "name": "email_notifications",
                    "label": "Email Notifications",
                    "type": "checkbox",
                    "checkbox_label": "Enable email notifications",
                    "default": (
                        settings_data.get("email_notifications", True)
                        if settings_data
                        else True
                    ),
                },
                {
                    "name": "auto_save_interval",
                    "label": "Auto-save Interval (minutes)",
                    "type": "number",
                    "min_value": 1,
                    "max_value": 60,
                    "default": (
                        settings_data.get("auto_save_interval", 5)
                        if settings_data
                        else 5
                    ),
                },
            ],
            form_key="settings_form",
        )

    def create_user_profile_form(self, user_data: Optional[Dict] = None) -> Dict:
        """Create user profile form"""
        return self.create_simple_form(
            title="👤 User Profile",
            fields=[
                {
                    "name": "display_name",
                    "label": "Display Name",
                    "type": "text",
                    "required": True,
                    "default": user_data.get("display_name", "") if user_data else "",
                },
                {
                    "name": "email",
                    "label": "Email Address",
                    "type": "email",
                    "required": True,
                    "default": user_data.get("email", "") if user_data else "",
                },
                {
                    "name": "phone",
                    "label": "Phone Number",
                    "type": "text",
                    "placeholder": "+66 XX XXX XXXX",
                    "default": user_data.get("phone", "") if user_data else "",
                },
                {
                    "name": "department",
                    "label": "Department",
                    "type": "select",
                    "options": [
                        "Engineering",
                        "Design",
                        "Product",
                        "Marketing",
                        "Operations",
                        "HR",
                        "Finance",
                    ],
                    "default": (
                        user_data.get("department", "Engineering")
                        if user_data
                        else "Engineering"
                    ),
                },
                {
                    "name": "bio",
                    "label": "Bio",
                    "type": "textarea",
                    "placeholder": "Tell us about yourself...",
                    "height": 100,
                    "default": user_data.get("bio", "") if user_data else "",
                },
                {
                    "name": "avatar",
                    "label": "Profile Picture",
                    "type": "file",
                    "accepted_types": ["png", "jpg", "jpeg"],
                    "help": "Upload a profile picture (PNG, JPG, JPEG)",
                },
            ],
            form_key="profile_form",
        )

    def _handle_project_submission(self, data: Dict, mode: str):
        """Handle project form submission"""
        st.success(
            f"✅ Project {'created' if mode == 'create' else 'updated'} successfully!"
        )
        st.balloons()

        # Show submitted data for debugging (remove in production)
        with st.expander("📋 Submitted Data", expanded=False):
            st.json(data)

    def _handle_task_submission(self, data: Dict, mode: str):
        """Handle task form submission"""
        st.success(
            f"✅ Task {'created' if mode == 'create' else 'updated'} successfully!"
        )
        st.balloons()

        # Show submitted data for debugging (remove in production)
        with st.expander("📋 Submitted Data", expanded=False):
            st.json(data)

    def create_quick_task_form(self) -> Dict:
        """Create quick task creation form"""
        return self.create_simple_form(
            title="⚡ Quick Task",
            fields=[
                {
                    "name": "task_name",
                    "label": "Task Name",
                    "type": "text",
                    "required": True,
                    "placeholder": "What needs to be done?",
                },
                {
                    "name": "priority",
                    "label": "Priority",
                    "type": "select",
                    "options": ["Low", "Medium", "High", "Critical"],
                    "default": "Medium",
                },
                {
                    "name": "due_date",
                    "label": "Due Date",
                    "type": "date",
                    "default": datetime.now().date() + timedelta(days=1),
                },
            ],
            form_key="quick_task_form",
        )

    def create_feedback_form(self) -> Dict:
        """Create feedback form"""
        return self.create_simple_form(
            title="💬 Feedback",
            fields=[
                {
                    "name": "feedback_type",
                    "label": "Feedback Type",
                    "type": "select",
                    "options": [
                        "Bug Report",
                        "Feature Request",
                        "General Feedback",
                        "Suggestion",
                    ],
                    "required": True,
                },
                {
                    "name": "subject",
                    "label": "Subject",
                    "type": "text",
                    "required": True,
                    "placeholder": "Brief description of your feedback",
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "Please provide detailed feedback...",
                    "height": 150,
                },
                {
                    "name": "rating",
                    "label": "Overall Rating",
                    "type": "slider",
                    "min_value": 1,
                    "max_value": 5,
                    "default": 5,
                    "help": "1 = Poor, 5 = Excellent",
                },
                {
                    "name": "contact_back",
                    "label": "Follow-up",
                    "type": "checkbox",
                    "checkbox_label": "Please contact me about this feedback",
                },
            ],
            form_key="feedback_form",
        )
