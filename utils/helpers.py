# utils/helpers.py
import streamlit as st
import pandas as pd
import hashlib
import secrets
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from utils.constants import ERROR_MESSAGES, SUCCESS_MESSAGES


def show_success(message: str, key: Optional[str] = None):
    """Display success message"""
    if key and key in SUCCESS_MESSAGES:
        message = SUCCESS_MESSAGES[key]
    st.success(message)


def show_error(message: str, key: Optional[str] = None):
    """Display error message"""
    if key and key in ERROR_MESSAGES:
        message = ERROR_MESSAGES[key]
    st.error(message)


def show_warning(message: str):
    """Display warning message"""
    st.warning(message)


def show_info(message: str):
    """Display info message"""
    st.info(message)


def generate_session_token() -> str:
    """Generate secure session token"""
    return secrets.token_urlsafe(32)


def hash_string(text: str) -> str:
    """Generate SHA-256 hash of string"""
    return hashlib.sha256(text.encode()).hexdigest()


def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with default"""
    return dictionary.get(key, default)


def safe_convert_to_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_convert_to_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_convert_to_date(value: Any) -> Optional[date]:
    """Safely convert value to date"""
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def calculate_progress_percentage(completed: int, total: int) -> float:
    """Calculate progress percentage"""
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 1)


def calculate_days_between(start_date: date, end_date: date) -> int:
    """Calculate number of days between two dates"""
    if not start_date or not end_date:
        return 0
    return (end_date - start_date).days


def is_overdue(end_date: date, status: str) -> bool:
    """Check if item is overdue"""
    if not end_date or status in ["Done", "Completed", "Cancelled"]:
        return False
    return date.today() > end_date


def get_status_color(status: str, status_type: str = "project") -> str:
    """Get color code for status"""
    from utils.constants import PROJECT_STATUS_COLORS, TASK_STATUS_COLORS

    if status_type == "project":
        colors = PROJECT_STATUS_COLORS
    else:
        colors = TASK_STATUS_COLORS

    # Find matching enum value
    for enum_val in colors.keys():
        if enum_val.value == status:
            return colors[enum_val]

    return "#6c757d"  # Default gray


def get_urgency_level(days_until_due: int) -> str:
    """Get urgency level based on days until due"""
    if days_until_due < 0:
        return "overdue"
    elif days_until_due <= 1:
        return "critical"
    elif days_until_due <= 3:
        return "high"
    elif days_until_due <= 7:
        return "medium"
    else:
        return "low"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean DataFrame by removing null values and formatting"""
    if df.empty:
        return df

    # Fill null values appropriately
    df = df.copy()

    # Fill string columns with empty string
    string_cols = df.select_dtypes(include=["object"]).columns
    df[string_cols] = df[string_cols].fillna("")

    # Fill numeric columns with 0
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df


def paginate_dataframe(df: pd.DataFrame, page: int, page_size: int) -> pd.DataFrame:
    """Paginate DataFrame"""
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return df.iloc[start_idx:end_idx]


def search_dataframe(
    df: pd.DataFrame, search_term: str, search_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """Search DataFrame across specified columns"""
    if df.empty or not search_term:
        return df

    if search_columns is None:
        # Search all string columns
        search_columns = df.select_dtypes(include=["object"]).columns.tolist()

    # Create search mask
    mask = pd.Series([False] * len(df))

    for col in search_columns:
        if col in df.columns:
            mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)

    return df[mask]


def generate_report_filename(report_type: str, extension: str = "csv") -> str:
    """Generate filename for report export"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{report_type}_report_{timestamp}.{extension}"


def validate_session_state() -> bool:
    """Validate if user session is valid"""
    from config.settings import app_config

    required_keys = [
        app_config.SESSION_KEYS["logged_in"],
        app_config.SESSION_KEYS["user_id"],
        app_config.SESSION_KEYS["username"],
    ]

    for key in required_keys:
        if key not in st.session_state or not st.session_state[key]:
            return False

    return True


def get_current_user_info() -> Dict[str, Any]:
    """Get current user information from session"""
    from config.settings import app_config

    if not validate_session_state():
        return {}

    return {
        "user_id": st.session_state.get(app_config.SESSION_KEYS["user_id"]),
        "username": st.session_state.get(app_config.SESSION_KEYS["username"]),
        "role": st.session_state.get(app_config.SESSION_KEYS["user_role"]),
    }


def check_permission(required_permission: str) -> bool:
    """Check if current user has required permission"""
    from utils.constants import USER_ROLE_PERMISSIONS, UserRole

    user_info = get_current_user_info()
    if not user_info:
        return False

    user_role_str = user_info.get("role", "User")

    # Find matching role enum
    user_role = None
    for role in UserRole:
        if role.value == user_role_str:
            user_role = role
            break

    if not user_role:
        return False

    permissions = USER_ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in permissions


def create_backup_data(data: Dict[str, Any]) -> str:
    """Create backup data string"""
    import json

    timestamp = datetime.now().isoformat()
    backup = {"timestamp": timestamp, "data": data}
    return json.dumps(backup, default=str, indent=2)


def parse_backup_data(backup_string: str) -> Optional[Dict[str, Any]]:
    """Parse backup data string"""
    import json

    try:
        backup = json.loads(backup_string)
        return backup.get("data")
    except json.JSONDecodeError:
        return None


def get_app_statistics() -> Dict[str, Any]:
    """Get general application statistics"""
    from services.enhanced_project_service import ProjectService
    from services.task_service import TaskService
    from services.user_service import UserService

    try:
        project_stats = ProjectService.get_project_statistics()
        task_stats = TaskService.get_task_statistics()
        user_stats = UserService.get_user_statistics()

        return {
            "projects": project_stats,
            "tasks": task_stats,
            "users": user_stats,
            "last_updated": datetime.now(),
        }
    except Exception:
        return {}


def render_loading_spinner(message: str = "กำลังโหลด..."):
    """Render loading spinner with message"""
    with st.spinner(message):
        st.empty()


def create_download_link(
    data: Union[pd.DataFrame, str], filename: str, file_type: str = "csv"
) -> None:
    """Create download link for data"""
    if isinstance(data, pd.DataFrame):
        if file_type == "csv":
            csv_data = data.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label=f"📥 ดาวน์โหลด {filename}",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
            )
        elif file_type == "excel":
            # For Excel, would need to use BytesIO
            pass
    elif isinstance(data, str):
        st.download_button(
            label=f"📥 ดาวน์โหลด {filename}",
            data=data,
            file_name=filename,
            mime="text/plain",
        )
