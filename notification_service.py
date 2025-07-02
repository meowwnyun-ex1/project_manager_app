# notification_service.py
"""
Real-time Notification Service for DENSO Project Manager
Handles notifications, alerts, and real-time updates
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification types"""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
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


@dataclass
class Notification:
    """Notification data structure"""

    id: str
    user_id: int
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    created_date: datetime
    is_read: bool = False
    read_date: Optional[datetime] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    data: Optional[Dict] = None


class NotificationService:
    """Service for managing notifications"""

    def __init__(self, db_service):
        self.db_service = db_service
        self._notification_cache = {}
        self._real_time_enabled = True

    def create_notification(self, notification_data: Dict) -> bool:
        """Create a new notification"""
        try:
            # Save to database
            success = self.db_service.create_notification(notification_data)

            if success:
                # Add to session state for real-time updates
                self._add_to_session_notifications(notification_data)
                logger.info(
                    f"Notification created for user {notification_data['user_id']}"
                )

            return success
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            return False

    def get_user_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get notifications for a specific user"""
        try:
            notifications = self.db_service.get_user_notifications(user_id, limit)

            # Enhance notifications with additional info
            for notification in notifications:
                notification["time_ago"] = self._calculate_time_ago(
                    notification["CreatedDate"]
                )
                notification["icon"] = self._get_notification_icon(notification["Type"])
                notification["color"] = self._get_notification_color(
                    notification["Type"]
                )

            return notifications
        except Exception as e:
            logger.error(f"Failed to get notifications: {str(e)}")
            return []

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            success = self.db_service.mark_notification_read(notification_id)

            if success:
                # Update session state
                self._update_session_notification_status(notification_id, user_id)
                logger.info(f"Notification {notification_id} marked as read")

            return success
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False

    def mark_all_read(self, user_id: int) -> bool:
        """Mark all notifications as read for a user"""
        try:
            query = """
            UPDATE Notifications 
            SET IsRead = 1, ReadDate = GETDATE()
            WHERE UserID = ? AND IsRead = 0
            """
            self.db_service.connection_manager.execute_non_query(query, (user_id,))

            # Clear session notifications
            if "notifications" in st.session_state:
                del st.session_state.notifications

            return True
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            return False

    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        try:
            query = "SELECT COUNT(*) as count FROM Notifications WHERE UserID = ? AND IsRead = 0"
            result = self.db_service.connection_manager.execute_query(query, (user_id,))
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"Failed to get unread count: {str(e)}")
            return 0

    def create_task_notification(
        self, task_data: Dict, action: str, user_id: int
    ) -> bool:
        """Create task-related notification"""
        try:
            action_messages = {
                "created": "New task has been assigned to you",
                "updated": "Task has been updated",
                "completed": "Task has been completed",
                "due_soon": "Task is due soon",
                "overdue": "Task is overdue",
            }

            notification_data = {
                "user_id": user_id,
                "type": "task",
                "title": f"Task: {task_data.get('name', 'Unknown')}",
                "message": action_messages.get(action, "Task notification"),
                "priority": self._get_task_priority(
                    task_data.get("priority", "Medium")
                ),
                "action_url": f"/tasks/{task_data.get('id', '')}",
                "action_text": "View Task",
            }

            return self.create_notification(notification_data)
        except Exception as e:
            logger.error(f"Failed to create task notification: {str(e)}")
            return False

    def create_project_notification(
        self, project_data: Dict, action: str, user_ids: List[int]
    ) -> bool:
        """Create project-related notification for multiple users"""
        try:
            action_messages = {
                "created": "New project has been created",
                "updated": "Project has been updated",
                "completed": "Project has been completed",
                "status_changed": "Project status has changed",
            }

            success_count = 0
            for user_id in user_ids:
                notification_data = {
                    "user_id": user_id,
                    "type": "project",
                    "title": f"Project: {project_data.get('name', 'Unknown')}",
                    "message": action_messages.get(action, "Project notification"),
                    "priority": "medium",
                    "action_url": f"/projects/{project_data.get('id', '')}",
                    "action_text": "View Project",
                }

                if self.create_notification(notification_data):
                    success_count += 1

            return success_count == len(user_ids)
        except Exception as e:
            logger.error(f"Failed to create project notifications: {str(e)}")
            return False

    def create_system_notification(
        self, title: str, message: str, priority: str = "medium"
    ) -> bool:
        """Create system-wide notification for all active users"""
        try:
            # Get all active users
            users = self.db_service.get_all_users()
            active_users = [
                user["UserID"] for user in users if user.get("IsActive", True)
            ]

            success_count = 0
            for user_id in active_users:
                notification_data = {
                    "user_id": user_id,
                    "type": "system",
                    "title": title,
                    "message": message,
                    "priority": priority,
                }

                if self.create_notification(notification_data):
                    success_count += 1

            return success_count > 0
        except Exception as e:
            logger.error(f"Failed to create system notification: {str(e)}")
            return False

    def check_due_tasks(self) -> bool:
        """Check for tasks due soon and create notifications"""
        try:
            # Get tasks due in next 24 hours
            query = """
            SELECT t.TaskID, t.TaskName, t.DueDate, t.AssigneeID, t.Priority,
                   p.ProjectName
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            WHERE t.DueDate BETWEEN GETDATE() AND DATEADD(day, 1, GETDATE())
            AND t.Status NOT IN ('Done', 'Cancelled')
            AND t.AssigneeID IS NOT NULL
            """

            due_tasks = self.db_service.connection_manager.execute_query(query)

            for task in due_tasks:
                task_data = {
                    "id": task["TaskID"],
                    "name": task["TaskName"],
                    "priority": task["Priority"],
                }

                self.create_task_notification(task_data, "due_soon", task["AssigneeID"])

            # Get overdue tasks
            overdue_query = """
            SELECT t.TaskID, t.TaskName, t.DueDate, t.AssigneeID, t.Priority,
                   p.ProjectName
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            WHERE t.DueDate < GETDATE()
            AND t.Status NOT IN ('Done', 'Cancelled')
            AND t.AssigneeID IS NOT NULL
            """

            overdue_tasks = self.db_service.connection_manager.execute_query(
                overdue_query
            )

            for task in overdue_tasks:
                task_data = {
                    "id": task["TaskID"],
                    "name": task["TaskName"],
                    "priority": task["Priority"],
                }

                self.create_task_notification(task_data, "overdue", task["AssigneeID"])

            return True
        except Exception as e:
            logger.error(f"Failed to check due tasks: {str(e)}")
            return False

    def _add_to_session_notifications(self, notification_data: Dict):
        """Add notification to session state for real-time updates"""
        if "notifications" not in st.session_state:
            st.session_state.notifications = []

        # Add to beginning of list
        st.session_state.notifications.insert(0, notification_data)

        # Keep only last 50 notifications in session
        if len(st.session_state.notifications) > 50:
            st.session_state.notifications = st.session_state.notifications[:50]

    def _update_session_notification_status(self, notification_id: int, user_id: int):
        """Update notification status in session state"""
        if "notifications" in st.session_state:
            for notification in st.session_state.notifications:
                if (
                    notification.get("id") == notification_id
                    and notification.get("user_id") == user_id
                ):
                    notification["is_read"] = True
                    notification["read_date"] = datetime.now()
                    break

    def _calculate_time_ago(self, created_date: datetime) -> str:
        """Calculate human-readable time ago"""
        try:
            if isinstance(created_date, str):
                created_date = datetime.fromisoformat(
                    created_date.replace("Z", "+00:00")
                )

            now = datetime.now()
            if created_date.tzinfo:
                now = now.replace(tzinfo=created_date.tzinfo)

            diff = now - created_date

            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        except:
            return "Unknown"

    def _get_notification_icon(self, notification_type: str) -> str:
        """Get icon for notification type"""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "task": "📋",
            "project": "📁",
            "team": "👥",
            "system": "⚙️",
        }
        return icons.get(notification_type, "📢")

    def _get_notification_color(self, notification_type: str) -> str:
        """Get color for notification type"""
        colors = {
            "info": "#17A2B8",
            "success": "#28A745",
            "warning": "#FFC107",
            "error": "#DC3545",
            "task": "#007BFF",
            "project": "#6F42C1",
            "team": "#FD7E14",
            "system": "#6C757D",
        }
        return colors.get(notification_type, "#17A2B8")

    def _get_task_priority(self, priority: str) -> str:
        """Convert task priority to notification priority"""
        priority_map = {
            "Low": "low",
            "Medium": "medium",
            "High": "high",
            "Critical": "critical",
        }
        return priority_map.get(priority, "medium")


class NotificationUI:
    """UI components for notifications"""

    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service

    def render_notification_center(self, user_id: int):
        """Render notification center widget"""
        # Get notifications
        notifications = self.notification_service.get_user_notifications(user_id)
        unread_count = self.notification_service.get_unread_count(user_id)

        # Notification button with badge
        col1, col2 = st.columns([1, 4])

        with col1:
            if unread_count > 0:
                st.markdown(
                    f"""
                <div style="
                    position: relative;
                    display: inline-block;
                ">
                    <button style="
                        background: #007BFF;
                        color: white;
                        border: none;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        font-size: 1.2rem;
                        cursor: pointer;
                        position: relative;
                    ">
                        🔔
                    </button>
                    <span style="
                        position: absolute;
                        top: -5px;
                        right: -5px;
                        background: #DC3545;
                        color: white;
                        border-radius: 50%;
                        width: 20px;
                        height: 20px;
                        font-size: 0.8rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                    ">
                        {unread_count if unread_count < 100 else '99+'}
                    </span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.button("🔔", help="Notifications")

        # Show notifications in expander
        with st.expander(
            f"🔔 Notifications ({unread_count} unread)", expanded=unread_count > 0
        ):
            if notifications:
                # Mark all as read button
                if unread_count > 0:
                    if st.button("📖 Mark All as Read", use_container_width=True):
                        if self.notification_service.mark_all_read(user_id):
                            st.success("All notifications marked as read")
                            st.rerun()

                # Render each notification
                for notification in notifications:
                    self.render_notification_item(notification, user_id)
            else:
                st.info("No notifications")

    def render_notification_item(self, notification: Dict, user_id: int):
        """Render individual notification item"""
        is_read = notification.get("IsRead", False)
        notification_id = notification.get("NotificationID")

        # Background color based on read status
        bg_color = "rgba(255, 255, 255, 0.5)" if is_read else "rgba(0, 123, 255, 0.1)"
        border_color = "#E9ECEF" if is_read else "#007BFF"

        with st.container():
            st.markdown(
                f"""
            <div style="
                background: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                transition: all 0.3s ease;
            ">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <span style="font-size: 1.2rem; margin-right: 8px;">
                                {notification.get('icon', '📢')}
                            </span>
                            <h4 style="
                                margin: 0;
                                color: #2E3440;
                                font-weight: {'600' if not is_read else '400'};
                            ">
                                {notification.get('Title', 'Notification')}
                            </h4>
                        </div>
                        
                        <p style="
                            margin: 8px 0;
                            color: #5E6C7E;
                            font-size: 0.9rem;
                        ">
                            {notification.get('Message', '')}
                        </p>
                        
                        <div style="
                            color: #6C757D;
                            font-size: 0.8rem;
                            margin-top: 8px;
                        ">
                            {notification.get('time_ago', 'Unknown time')}
                        </div>
                    </div>
                    
                    <div style="margin-left: 15px;">
                        {self._get_priority_badge(notification.get('Priority', 'medium'))}
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Action buttons
            if not is_read:
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("Mark Read", key=f"read_{notification_id}"):
                        if self.notification_service.mark_notification_read(
                            notification_id, user_id
                        ):
                            st.rerun()

            # Action URL button if available
            if notification.get("ActionUrl"):
                if st.button(
                    notification.get("ActionText", "View"),
                    key=f"action_{notification_id}",
                    help="Go to related item",
                ):
                    st.info("Navigation feature coming soon!")

    def render_notification_toast(self, notification: Dict, duration: int = 5000):
        """Render floating notification toast"""
        toast_id = f"toast_{int(time.time() * 1000)}"
        color = notification.get("color", "#17A2B8")
        icon = notification.get("icon", "📢")

        st.markdown(
            f"""
        <div id="{toast_id}" style="
            position: fixed;
            top: 80px;
            right: 20px;
            background: {color};
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            max-width: 300px;
            animation: slideInRight 0.3s ease-out;
        ">
            <div style="display: flex; align-items: start; gap: 10px;">
                <span style="font-size: 1.2rem; margin-top: 2px;">{icon}</span>
                <div style="flex: 1;">
                    <div style="font-weight: 600; margin-bottom: 5px;">
                        {notification.get('title', 'Notification')}
                    </div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">
                        {notification.get('message', '')}
                    </div>
                </div>
                <button onclick="document.getElementById('{toast_id}').remove()" style="
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 1.2rem;
                    line-height: 1;
                    opacity: 0.7;
                ">×</button>
            </div>
        </div>
        
        <script>
        setTimeout(function() {{
            var toast = document.getElementById('{toast_id}');
            if (toast) {{
                toast.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(function() {{
                    if (toast) toast.remove();
                }}, 300);
            }}
        }}, {duration});
        </script>
        
        <style>
        @keyframes slideInRight {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        @keyframes slideOutRight {{
            from {{ transform: translateX(0); opacity: 1; }}
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _get_priority_badge(self, priority: str) -> str:
        """Get HTML for priority badge"""
        priority_config = {
            "low": {"color": "#6C757D", "text": "Low"},
            "medium": {"color": "#FFC107", "text": "Medium"},
            "high": {"color": "#FD7E14", "text": "High"},
            "critical": {"color": "#DC3545", "text": "Critical"},
        }

        config = priority_config.get(priority, priority_config["medium"])

        return f"""
        <span style="
            background: {config['color']};
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        ">
            {config['text']}
        </span>
        """


class RealTimeUpdates:
    """Handle real-time updates and auto-refresh"""

    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.update_interval = 30  # seconds

    def enable_auto_refresh(self, user_id: int):
        """Enable auto-refresh for notifications"""
        if "last_notification_check" not in st.session_state:
            st.session_state.last_notification_check = datetime.now()

        # Check if enough time has passed
        now = datetime.now()
        if (
            now - st.session_state.last_notification_check
        ).seconds >= self.update_interval:
            # Check for new notifications
            unread_count = self.notification_service.get_unread_count(user_id)
            previous_count = st.session_state.get("previous_unread_count", 0)

            if unread_count > previous_count:
                # New notifications available
                st.session_state.new_notifications_available = True

                # Show toast for new notifications
                if unread_count - previous_count == 1:
                    st.success("🔔 You have a new notification!")
                else:
                    st.success(
                        f"🔔 You have {unread_count - previous_count} new notifications!"
                    )

            st.session_state.previous_unread_count = unread_count
            st.session_state.last_notification_check = now

    def check_task_deadlines(self):
        """Check for task deadlines and create notifications"""
        try:
            return self.notification_service.check_due_tasks()
        except Exception as e:
            logger.error(f"Failed to check task deadlines: {str(e)}")
            return False


def create_sample_notifications(notification_service: NotificationService):
    """Create sample notifications for demo purposes"""
    try:
        # Get admin user (assuming UserID = 1)
        sample_notifications = [
            {
                "user_id": 1,
                "type": "info",
                "title": "Welcome to DENSO Project Manager",
                "message": "Your project management system is ready to use!",
                "priority": "medium",
            },
            {
                "user_id": 1,
                "type": "task",
                "title": "Task Assignment",
                "message": 'You have been assigned a new task: "Setup Database Schema"',
                "priority": "high",
            },
            {
                "user_id": 1,
                "type": "project",
                "title": "Project Update",
                "message": 'Website Redesign project status changed to "In Progress"',
                "priority": "medium",
            },
        ]

        for notification_data in sample_notifications:
            notification_service.create_notification(notification_data)

        logger.info("Sample notifications created successfully")
    except Exception as e:
        logger.error(f"Failed to create sample notifications: {str(e)}")


# Global notification service instance
notification_service = None


def get_notification_service(db_service):
    """Get or create notification service instance"""
    global notification_service
    if notification_service is None:
        notification_service = NotificationService(db_service)
    return notification_service
