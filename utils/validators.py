# utils/validators.py
import re
from datetime import date, datetime
from typing import Any, List, Union
import pandas as pd


class ValidationError(Exception):
    """Custom validation error"""

    pass


class Validators:
    """Collection of validation functions"""

    @staticmethod
    def validate_required(value: Any, field_name: str = "Field") -> bool:
        """Validate that a field is not empty"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required")
        return True

    @staticmethod
    def validate_string_length(
        value: str,
        min_length: int = 0,
        max_length: int = None,
        field_name: str = "Field",
    ) -> bool:
        """Validate string length"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")

        length = len(value.strip())

        if length < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters"
            )

        if max_length and length > max_length:
            raise ValidationError(
                f"{field_name} must be less than {max_length} characters"
            )

        return True

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        if not username:
            raise ValidationError("Username is required")

        username = username.strip()

        # Length check
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")
        if len(username) > 50:
            raise ValidationError("Username must be less than 50 characters")

        # Pattern check (alphanumeric and underscore only)
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores"
            )

        # Cannot start with number
        if username[0].isdigit():
            raise ValidationError("Username cannot start with a number")

        return True

    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength"""
        if not password:
            raise ValidationError("Password is required")

        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters")

        if len(password) > 255:
            raise ValidationError("Password is too long (max 255 characters)")

        # Check for at least one letter and one number (optional but recommended)
        # if not re.search(r'[A-Za-z]', password):
        #     raise ValidationError("Password must contain at least one letter")
        # if not re.search(r'\d', password):
        #     raise ValidationError("Password must contain at least one number")

        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            raise ValidationError("Email is required")

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")

        return True

    @staticmethod
    def validate_date(date_value: Any, field_name: str = "Date") -> bool:
        """Validate date value"""
        if date_value is None:
            raise ValidationError(f"{field_name} is required")

        if isinstance(date_value, str):
            try:
                date_value = pd.to_datetime(date_value).date()
            except:
                raise ValidationError(f"Invalid {field_name} format")

        if not isinstance(date_value, (date, datetime)):
            raise ValidationError(f"{field_name} must be a valid date")

        return True

    @staticmethod
    def validate_date_range(
        start_date: Any, end_date: Any, allow_same_day: bool = True
    ) -> bool:
        """Validate date range"""
        Validators.validate_date(start_date, "Start date")
        Validators.validate_date(end_date, "End date")

        # Convert to date objects if needed
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).date()
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date).date()

        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        if allow_same_day:
            if end_date < start_date:
                raise ValidationError("End date must be on or after start date")
        else:
            if end_date <= start_date:
                raise ValidationError("End date must be after start date")

        return True

    @staticmethod
    def validate_numeric_range(
        value: Union[int, float],
        min_value: float = None,
        max_value: float = None,
        field_name: str = "Value",
    ) -> bool:
        """Validate numeric value within range"""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")

        if min_value is not None and value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}")

        return True

    @staticmethod
    def validate_progress(progress: Any) -> bool:
        """Validate progress percentage (0-100)"""
        return Validators.validate_numeric_range(progress, 0, 100, "Progress")

    @staticmethod
    def validate_choice(
        value: Any, choices: List[Any], field_name: str = "Value"
    ) -> bool:
        """Validate that value is in allowed choices"""
        if value not in choices:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(map(str, choices))}"
            )
        return True

    @staticmethod
    def validate_project_status(status: str) -> bool:
        """Validate project status"""
        from config.settings import app_config

        return Validators.validate_choice(
            status, app_config.PROJECT_STATUSES, "Project status"
        )

    @staticmethod
    def validate_task_status(status: str) -> bool:
        """Validate task status"""
        from config.settings import app_config

        return Validators.validate_choice(
            status, app_config.TASK_STATUSES, "Task status"
        )

    @staticmethod
    def validate_user_role(role: str) -> bool:
        """Validate user role"""
        from config.settings import app_config

        return Validators.validate_choice(role, app_config.USER_ROLES, "User role")

    @staticmethod
    def validate_file_upload(
        uploaded_file: Any, allowed_types: List[str] = None, max_size_mb: float = 10
    ) -> bool:
        """Validate uploaded file"""
        if uploaded_file is None:
            raise ValidationError("No file uploaded")

        # Check file type
        if allowed_types:
            file_type = uploaded_file.type
            if file_type not in allowed_types:
                raise ValidationError(
                    f"File type {file_type} not allowed. Allowed types: {', '.join(allowed_types)}"
                )

        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValidationError(
                f"File size ({file_size_mb:.1f}MB) exceeds limit ({max_size_mb}MB)"
            )

        return True


class FormValidator:
    """Form validation helper class"""

    def __init__(self):
        self.errors = []

    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)

    def validate_field(self, validator_func, *args, **kwargs):
        """Validate a field and collect errors"""
        try:
            validator_func(*args, **kwargs)
        except ValidationError as e:
            self.add_error(str(e))

    def is_valid(self) -> bool:
        """Check if form is valid (no errors)"""
        return len(self.errors) == 0

    def get_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self.errors

    def clear_errors(self):
        """Clear validation errors"""
        self.errors = []


# Quick validation functions
def quick_validate_project_data(data: dict) -> List[str]:
    """Quick validation for project data"""
    validator = FormValidator()

    validator.validate_field(
        Validators.validate_required, data.get("project_name"), "Project name"
    )
    validator.validate_field(
        Validators.validate_string_length,
        data.get("project_name", ""),
        2,
        100,
        "Project name",
    )

    if data.get("start_date") and data.get("end_date"):
        validator.validate_field(
            Validators.validate_date_range, data["start_date"], data["end_date"]
        )

    if data.get("status"):
        validator.validate_field(Validators.validate_project_status, data["status"])

    return validator.get_errors()


def quick_validate_task_data(data: dict) -> List[str]:
    """Quick validation for task data"""
    validator = FormValidator()

    validator.validate_field(
        Validators.validate_required, data.get("task_name"), "Task name"
    )
    validator.validate_field(
        Validators.validate_string_length,
        data.get("task_name", ""),
        2,
        100,
        "Task name",
    )

    if data.get("start_date") and data.get("end_date"):
        validator.validate_field(
            Validators.validate_date_range, data["start_date"], data["end_date"]
        )

    if data.get("progress") is not None:
        validator.validate_field(Validators.validate_progress, data["progress"])

    if data.get("status"):
        validator.validate_field(Validators.validate_task_status, data["status"])

    return validator.get_errors()


def quick_validate_user_data(data: dict) -> List[str]:
    """Quick validation for user data"""
    validator = FormValidator()

    validator.validate_field(Validators.validate_username, data.get("username", ""))
    validator.validate_field(Validators.validate_password, data.get("password", ""))

    if data.get("role"):
        validator.validate_field(Validators.validate_user_role, data["role"])

    return validator.get_errors()
