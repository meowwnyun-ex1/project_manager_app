# ui/components/notification_system.py
import streamlit as st
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid


class NotificationType(Enum):
    """Notification types"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    TASK = "task"
    PROJECT = "project"
    TEAM = "team"
    SYSTEM = "system"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationManager:
    """Advanced notification management system"""

    def __init__(self):
        self.notifications = []
        self.max_notifications = 50
        self.auto_dismiss_time = 5000  # milliseconds

        # Initialize session state
        if "notifications" not in st.session_state:
            st.session_state.notifications = []
        if "notification_settings" not in st.session_state:
            st.session_state.notification_settings = {
                "sound_enabled": True,
                "push_enabled": True,
                "email_enabled": True,
                "auto_dismiss": True,
                "show_timestamps": True,
                "max_display": 5,
            }

    def add_notification(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        title: Optional[str] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        user_id: Optional[str] = None,
        persistent: bool = False,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a new notification"""

        notification_id = str(uuid.uuid4())

        notification = {
            "id": notification_id,
            "message": message,
            "type": notification_type.value,
            "priority": priority.value,
            "title": title or self._get_default_title(notification_type),
            "timestamp": datetime.now(),
            "read": False,
            "dismissed": False,
            "persistent": persistent,
            "action_url": action_url,
            "action_text": action_text,
            "user_id": user_id,
            "metadata": metadata or {},
        }

        # Add to session state
        st.session_state.notifications.insert(0, notification)

        # Limit notifications
        if len(st.session_state.notifications) > self.max_notifications:
            st.session_state.notifications = st.session_state.notifications[
                : self.max_notifications
            ]

        return notification_id

    def _get_default_title(self, notification_type: NotificationType) -> str:
        """Get default title based on notification type"""
        titles = {
            NotificationType.SUCCESS: "Success",
            NotificationType.ERROR: "Error",
            NotificationType.WARNING: "Warning",
            NotificationType.INFO: "Information",
            NotificationType.TASK: "Task Update",
            NotificationType.PROJECT: "Project Update",
            NotificationType.TEAM: "Team Notification",
            NotificationType.SYSTEM: "System Notification",
        }
        return titles.get(notification_type, "Notification")

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        for notification in st.session_state.notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                return True
        return False

    def dismiss_notification(self, notification_id: str) -> bool:
        """Dismiss a notification"""
        for i, notification in enumerate(st.session_state.notifications):
            if notification["id"] == notification_id:
                if not notification["persistent"]:
                    st.session_state.notifications.pop(i)
                else:
                    notification["dismissed"] = True
                return True
        return False

    def get_unread_count(self, user_id: Optional[str] = None) -> int:
        """Get count of unread notifications"""
        count = 0
        for notification in st.session_state.notifications:
            if not notification["read"] and not notification["dismissed"]:
                if user_id is None or notification.get("user_id") == user_id:
                    count += 1
        return count

    def get_notifications(
        self,
        limit: Optional[int] = None,
        notification_type: Optional[NotificationType] = None,
        user_id: Optional[str] = None,
        unread_only: bool = False,
    ) -> List[Dict]:
        """Get notifications with filters"""

        notifications = st.session_state.notifications.copy()

        # Apply filters
        if notification_type:
            notifications = [
                n for n in notifications if n["type"] == notification_type.value
            ]

        if user_id:
            notifications = [n for n in notifications if n.get("user_id") == user_id]

        if unread_only:
            notifications = [
                n for n in notifications if not n["read"] and not n["dismissed"]
            ]

        # Apply limit
        if limit:
            notifications = notifications[:limit]

        return notifications

    def clear_all_notifications(self, user_id: Optional[str] = None) -> int:
        """Clear all notifications"""
        if user_id:
            original_count = len(st.session_state.notifications)
            st.session_state.notifications = [
                n for n in st.session_state.notifications if n.get("user_id") != user_id
            ]
            return original_count - len(st.session_state.notifications)
        else:
            count = len(st.session_state.notifications)
            st.session_state.notifications = []
            return count


def apply_notification_css():
    """Apply modern CSS for notifications"""
    st.markdown(
        """
    <style>
    /* Notification System Styles */
    .notification-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        pointer-events: none;
    }
    
    .notification-toast {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 15px;
        padding: 1rem 1.5rem;
        margin-bottom: 10px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        pointer-events: auto;
        animation: slideInRight 0.3s ease-out;
        transition: all 0.3s ease;
    }
    
    .notification-toast:hover {
        transform: translateX(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
    }
    
    .notification-toast.success {
        border-left: 4px solid #10b981;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    .notification-toast.error {
        border-left: 4px solid #ef4444;
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    .notification-toast.warning {
        border-left: 4px solid #f59e0b;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    .notification-toast.info {
        border-left: 4px solid #3b82f6;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    .notification-toast.task {
        border-left: 4px solid #8b5cf6;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    .notification-toast.project {
        border-left: 4px solid #06b6d4;
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    .notification-toast.team {
        border-left: 4px solid #ec4899;
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    .notification-toast.system {
        border-left: 4px solid #6b7280;
        background: linear-gradient(135deg, rgba(107, 114, 128, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .notification-title {
        font-weight: 600;
        font-size: 0.9rem;
        color: #1f2937;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .notification-time {
        font-size: 0.75rem;
        color: #6b7280;
    }
    
    .notification-message {
        font-size: 0.85rem;
        color: #374151;
        line-height: 1.4;
        margin-bottom: 0.5rem;
    }
    
    .notification-actions {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
    }
    
    .notification-action {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .notification-action:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    .notification-close {
        background: none;
        border: none;
        color: #6b7280;
        font-size: 1.2rem;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.2s ease;
    }
    
    .notification-close:hover {
        background: rgba(107, 114, 128, 0.1);
        color: #374151;
    }
    
    /* Notification Center Styles */
    .notification-center {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .notification-center-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    .notification-center-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .notification-badge {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-weight: 600;
        min-width: 20px;
        text-align: center;
    }
    
    .notification-list {
        max-height: 400px;
        overflow-y: auto;
        padding-right: 0.5rem;
    }
    
    .notification-item {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border: 1px solid rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .notification-item:hover {
        background: rgba(255, 255, 255, 0.9);
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    .notification-item.unread {
        border-left: 4px solid #3b82f6;
        background: rgba(59, 130, 246, 0.05);
    }
    
    .notification-filters {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    
    .filter-button {
        background: rgba(59, 130, 246, 0.1);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .filter-button.active {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-color: transparent;
    }
    
    .filter-button:hover {
        background: rgba(59, 130, 246, 0.2);
    }
    
    .filter-button.active:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
    }
    
    .empty-notifications {
        text-align: center;
        padding: 3rem 1rem;
        color: #6b7280;
    }
    
    .empty-notifications-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .notification-container {
            left: 10px;
            right: 10px;
            top: 10px;
            max-width: none;
        }
        
        .notification-toast {
            margin-bottom: 8px;
        }
        
        .notification-center {
            margin: 0.5rem;
            padding: 1rem;
        }
        
        .notification-filters {
            justify-content: center;
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def show_toast_notification(
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    duration: int = 5000,
    title: Optional[str] = None,
    action_text: Optional[str] = None,
    action_callback: Optional[callable] = None,
):
    """Show a toast notification"""

    # Get icon for notification type
    icons = {
        NotificationType.SUCCESS: "✅",
        NotificationType.ERROR: "❌",
        NotificationType.WARNING: "⚠️",
        NotificationType.INFO: "ℹ️",
        NotificationType.TASK: "📋",
        NotificationType.PROJECT: "📁",
        NotificationType.TEAM: "👥",
        NotificationType.SYSTEM: "⚙️",
    }

    icon = icons.get(notification_type, "ℹ️")
    display_title = title or notification_type.value.title()

    # Create notification HTML
    toast_html = f"""
    <div class="notification-toast {notification_type.value}" id="toast-{uuid.uuid4()}">
        <div class="notification-header">
            <div class="notification-title">
                {icon} {display_title}
            </div>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
        <div class="notification-message">{message}</div>
    """

    if action_text and action_callback:
        toast_html += f"""
        <div class="notification-actions">
            <button class="notification-action" onclick="{action_callback}">{action_text}</button>
        </div>
        """

    toast_html += "</div>"

    # Auto-dismiss script
    toast_html += f"""
    <script>
        setTimeout(function() {{
            const toast = document.querySelector('.notification-toast:last-child');
            if (toast) {{
                toast.style.animation = 'slideOutRight 0.3s ease-out';
                setTimeout(() => toast.remove(), 300);
            }}
        }}, {duration});
    </script>
    """

    st.markdown(toast_html, unsafe_allow_html=True)


def render_notification_center(notification_manager: NotificationManager):
    """Render the notification center"""

    st.markdown('<div class="notification-center">', unsafe_allow_html=True)

    # Header
    unread_count = notification_manager.get_unread_count()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
        <div class="notification-center-title">
            🔔 Notifications
            {f'<span class="notification-badge">{unread_count}</span>' if unread_count > 0 else ''}
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        if st.button("🗑️ Clear All", key="clear_all_notifications"):
            cleared = notification_manager.clear_all_notifications()
            show_toast_notification(
                f"Cleared {cleared} notifications", NotificationType.SUCCESS
            )
            st.rerun()

    # Filters
    st.markdown('<div class="notification-filters">', unsafe_allow_html=True)

    filter_cols = st.columns(6)
    filters = ["All", "Unread", "Tasks", "Projects", "Team", "System"]
    selected_filter = st.session_state.get("notification_filter", "All")

    for i, filter_name in enumerate(filters):
        with filter_cols[i]:
            if st.button(filter_name, key=f"filter_{filter_name.lower()}"):
                st.session_state.notification_filter = filter_name
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Get filtered notifications
    if selected_filter == "All":
        notifications = notification_manager.get_notifications(limit=20)
    elif selected_filter == "Unread":
        notifications = notification_manager.get_notifications(
            unread_only=True, limit=20
        )
    else:
        notification_type = getattr(NotificationType, selected_filter.upper(), None)
        notifications = notification_manager.get_notifications(
            notification_type=notification_type, limit=20
        )

    # Notification list
    st.markdown('<div class="notification-list">', unsafe_allow_html=True)

    if not notifications:
        st.markdown(
            """
        <div class="empty-notifications">
            <div class="empty-notifications-icon">📭</div>
            <h3>No notifications found</h3>
            <p>You're all caught up!</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        for notification in notifications:
            render_notification_item(notification, notification_manager)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_notification_item(
    notification: Dict, notification_manager: NotificationManager
):
    """Render individual notification item"""

    # Get icon for notification type
    icons = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "task": "📋",
        "project": "📁",
        "team": "👥",
        "system": "⚙️",
    }

    icon = icons.get(notification["type"], "ℹ️")
    unread_class = "unread" if not notification["read"] else ""

    # Format timestamp
    time_ago = format_time_ago(notification["timestamp"])

    with st.container():
        col1, col2, col3 = st.columns([1, 6, 1])

        with col1:
            st.markdown(
                f"<div style='font-size: 1.5rem; text-align: center;'>{icon}</div>",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
            <div class="notification-item {unread_class}">
                <div class="notification-header">
                    <div class="notification-title">{notification['title']}</div>
                    <div class="notification-time">{time_ago}</div>
                </div>
                <div class="notification-message">{notification['message']}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            if st.button("✓", key=f"read_{notification['id']}", help="Mark as read"):
                notification_manager.mark_as_read(notification["id"])
                st.rerun()

            if st.button("🗑️", key=f"delete_{notification['id']}", help="Delete"):
                notification_manager.dismiss_notification(notification["id"])
                st.rerun()


def format_time_ago(timestamp: datetime) -> str:
    """Format timestamp as time ago"""
    now = datetime.now()
    diff = now - timestamp

    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"


def create_sample_notifications(notification_manager: NotificationManager):
    """Create sample notifications for demo"""

    # Add sample notifications
    notification_manager.add_notification(
        "New task assigned: Update project documentation",
        NotificationType.TASK,
        NotificationPriority.HIGH,
        title="Task Assignment",
    )

    notification_manager.add_notification(
        "Project 'Website Redesign' deadline approaching in 3 days",
        NotificationType.PROJECT,
        NotificationPriority.MEDIUM,
        title="Deadline Reminder",
    )

    notification_manager.add_notification(
        "John Doe commented on your task",
        NotificationType.TEAM,
        NotificationPriority.LOW,
        title="New Comment",
    )

    notification_manager.add_notification(
        "System maintenance scheduled for tonight at 2 AM",
        NotificationType.SYSTEM,
        NotificationPriority.HIGH,
        title="Maintenance Notice",
    )

    notification_manager.add_notification(
        "Successfully exported project report",
        NotificationType.SUCCESS,
        NotificationPriority.LOW,
        title="Export Complete",
    )


# Quick notification functions for easy use
def success(message: str, title: str = "Success"):
    """Show success notification"""
    show_toast_notification(message, NotificationType.SUCCESS, title=title)


def error(message: str, title: str = "Error"):
    """Show error notification"""
    show_toast_notification(message, NotificationType.ERROR, title=title)


def warning(message: str, title: str = "Warning"):
    """Show warning notification"""
    show_toast_notification(message, NotificationType.WARNING, title=title)


def info(message: str, title: str = "Information"):
    """Show info notification"""
    show_toast_notification(message, NotificationType.INFO, title=title)


def task_notification(message: str, title: str = "Task Update"):
    """Show task notification"""
    show_toast_notification(message, NotificationType.TASK, title=title)


def project_notification(message: str, title: str = "Project Update"):
    """Show project notification"""
    show_toast_notification(message, NotificationType.PROJECT, title=title)


# Export classes and functions
__all__ = [
    "NotificationManager",
    "NotificationType",
    "NotificationPriority",
    "apply_notification_css",
    "show_toast_notification",
    "render_notification_center",
    "success",
    "error",
    "warning",
    "info",
    "task_notification",
    "project_notification",
]
