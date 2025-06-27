# utils/formatters.py
from datetime import date, datetime
from typing import Any, Optional
import pandas as pd


def format_date(date_value: Any, format_str: str = "%Y-%m-%d") -> str:
    """Format date value to string"""
    if pd.isna(date_value) or date_value is None:
        return ""

    if isinstance(date_value, str):
        try:
            date_value = pd.to_datetime(date_value).date()
        except:
            return date_value

    if isinstance(date_value, datetime):
        date_value = date_value.date()

    if isinstance(date_value, date):
        return date_value.strftime(format_str)

    return str(date_value)


def format_datetime(datetime_value: Any, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime value to string"""
    if pd.isna(datetime_value) or datetime_value is None:
        return ""

    if isinstance(datetime_value, str):
        try:
            datetime_value = pd.to_datetime(datetime_value)
        except:
            return datetime_value

    if isinstance(datetime_value, datetime):
        return datetime_value.strftime(format_str)

    return str(datetime_value)


def format_percentage(value: Any, decimals: int = 1) -> str:
    """Format numeric value as percentage"""
    if pd.isna(value) or value is None:
        return "0%"

    try:
        numeric_value = float(value)
        return f"{numeric_value:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"


def format_currency(value: Any, currency: str = "฿", decimals: int = 2) -> str:
    """Format numeric value as currency"""
    if pd.isna(value) or value is None:
        return f"{currency}0"

    try:
        numeric_value = float(value)
        formatted = f"{numeric_value:,.{decimals}f}"
        return f"{currency}{formatted}"
    except (ValueError, TypeError):
        return f"{currency}0"


def format_duration(days: Optional[int]) -> str:
    """Format duration in days to human readable string"""
    if days is None or pd.isna(days):
        return ""

    if days == 0:
        return "วันนี้"
    elif days == 1:
        return "1 วัน"
    elif days < 0:
        return f"เกิน {abs(days)} วัน"
    else:
        return f"{days} วัน"


def format_status_badge(status: str) -> str:
    """Format status with appropriate emoji"""
    status_emoji = {
        # Project statuses
        "Planning": "📋",
        "In Progress": "🚀",
        "Completed": "✅",
        "On Hold": "⏸️",
        "Cancelled": "❌",
        # Task statuses
        "To Do": "📝",
        "Testing": "🧪",
        "Done": "✅",
        "Blocked": "🚫",
    }

    emoji = status_emoji.get(status, "📊")
    return f"{emoji} {status}"


def format_progress_bar(progress: Any, width: int = 20) -> str:
    """Create a text-based progress bar"""
    if pd.isna(progress) or progress is None:
        progress = 0

    try:
        progress = int(progress)
    except (ValueError, TypeError):
        progress = 0

    progress = max(0, min(100, progress))  # Clamp between 0-100
    filled = int(width * progress / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {progress}%"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or pd.isna(text):
        return ""

    text = str(text)
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_user_display(username: str, role: Optional[str] = None) -> str:
    """Format user display name with role"""
    if not username or pd.isna(username):
        return "ไม่ระบุ"

    if role and not pd.isna(role):
        role_emoji = {"Admin": "👑", "Manager": "👨‍💼", "User": "👤"}
        emoji = role_emoji.get(role, "👤")
        return f"{emoji} {username}"

    return username


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable string"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re

    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove multiple underscores
    filename = re.sub(r"_+", "_", filename)
    # Remove leading/trailing underscores and dots
    filename = filename.strip("_.")
    return filename or "untitled"
