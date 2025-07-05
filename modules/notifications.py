#!/usr/bin/env python3
"""
modules/notifications.py
Comprehensive Notification System for DENSO Project Manager Pro
รองรับการแจ้งเตือนแบบเรียลไทม์, อีเมล, และ in-app notifications
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Callable
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import threading
import time
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

from utils.error_handler import safe_execute, handle_error, validate_input
from utils.ui_components import UIComponents

logger = logging.getLogger(__name__)


class NotificationManager:
    """Advanced notification management system"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.ui = UIComponents()
        self.email_enabled = False
        self.notification_queue = []
        self.subscribers = defaultdict(list)  # event_type -> [user_ids]
        self.templates = {}
        self.executor = ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="notification"
        )

        # Initialize email settings
        self._init_email_settings()
        self._load_notification_templates()
        self._setup_notification_rules()

    def _init_email_settings(self):
        """Initialize email configuration"""
        try:
            if hasattr(st, "secrets") and "email" in st.secrets:
                email_config = st.secrets.email
                self.smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
                self.smtp_port = email_config.get("smtp_port", 587)
                self.smtp_username = email_config.get("smtp_username", "")
                self.smtp_password = email_config.get("smtp_password", "")
                self.from_email = email_config.get("from_email", "noreply@denso.com")
                self.from_name = email_config.get("from_name", "DENSO Project Manager")
                self.email_enabled = bool(self.smtp_username and self.smtp_password)

            logger.info(
                f"Email notifications: {'Enabled' if self.email_enabled else 'Disabled'}"
            )
        except Exception as e:
            logger.warning(f"Email configuration failed: {e}")
            self.email_enabled = False

    def _load_notification_templates(self):
        """Load notification templates"""
        self.templates = {
            "task_assigned": {
                "title": "งานใหม่ได้รับมอบหมาย",
                "in_app": 'คุณได้รับมอบหมายงาน "{task_title}" ในโครงการ "{project_name}"',
                "email_subject": "DENSO - งานใหม่ได้รับมอบหมาย",
                "email_body": """
                <h2>งานใหม่ได้รับมอบหมาย</h2>
                <p>สวัสดี {user_name},</p>
                <p>คุณได้รับมอบหมายงานใหม่:</p>
                <ul>
                    <li><strong>ชื่องาน:</strong> {task_title}</li>
                    <li><strong>โครงการ:</strong> {project_name}</li>
                    <li><strong>กำหนดส่ง:</strong> {due_date}</li>
                    <li><strong>ความสำคัญ:</strong> {priority}</li>
                </ul>
                <p>รายละเอียด: {description}</p>
                <p>กรุณาเข้าสู่ระบบเพื่อดูรายละเอียดเพิ่มเติม</p>
                """,
                "priority": "medium",
            },
            "task_due_soon": {
                "title": "งานใกล้ครบกำหนด",
                "in_app": 'งาน "{task_title}" จะครบกำหนดใน {days_remaining} วัน',
                "email_subject": "DENSO - แจ้งเตือนงานใกล้ครบกำหนด",
                "email_body": """
                <h2>งานใกล้ครบกำหนด</h2>
                <p>สวัสดี {user_name},</p>
                <p>งานต่อไปนี้ใกล้ครบกำหนดแล้ว:</p>
                <ul>
                    <li><strong>ชื่องาน:</strong> {task_title}</li>
                    <li><strong>โครงการ:</strong> {project_name}</li>
                    <li><strong>กำหนดส่ง:</strong> {due_date}</li>
                    <li><strong>เหลือเวลา:</strong> {days_remaining} วัน</li>
                </ul>
                <p>กรุณาเร่งดำเนินการให้เสร็จตามกำหนด</p>
                """,
                "priority": "high",
            },
            "task_overdue": {
                "title": "งานเลยกำหนด",
                "in_app": 'งาน "{task_title}" เลยกำหนดมาแล้ว {days_overdue} วัน',
                "email_subject": "DENSO - งานเลยกำหนด [URGENT]",
                "email_body": """
                <h2 style="color: red;">งานเลยกำหนด</h2>
                <p>สวัสดี {user_name},</p>
                <p><strong style="color: red;">งานต่อไปนี้เลยกำหนดแล้ว:</strong></p>
                <ul>
                    <li><strong>ชื่องาน:</strong> {task_title}</li>
                    <li><strong>โครงการ:</strong> {project_name}</li>
                    <li><strong>กำหนดส่ง:</strong> {due_date}</li>
                    <li><strong>เลยมา:</strong> {days_overdue} วัน</li>
                </ul>
                <p>กรุณาดำเนินการโดยด่วน หรือติดต่อผู้จัดการโครงการ</p>
                """,
                "priority": "critical",
            },
            "project_status_changed": {
                "title": "สถานะโครงการเปลี่ยนแปลง",
                "in_app": 'โครงการ "{project_name}" เปลี่ยนสถานะเป็น {new_status}',
                "email_subject": "DENSO - การอัปเดตสถานะโครงการ",
                "email_body": """
                <h2>การอัปเดตสถานะโครงการ</h2>
                <p>สวัสดี {user_name},</p>
                <p>โครงการ "{project_name}" มีการเปลี่ยนแปลงสถานะ:</p>
                <ul>
                    <li><strong>สถานะเดิม:</strong> {old_status}</li>
                    <li><strong>สถานะใหม่:</strong> {new_status}</li>
                    <li><strong>อัปเดตโดย:</strong> {updated_by}</li>
                    <li><strong>วันที่อัปเดต:</strong> {update_date}</li>
                </ul>
                <p>หมายเหตุ: {notes}</p>
                """,
                "priority": "medium",
            },
            "project_milestone": {
                "title": "บรรลุ Milestone ของโครงการ",
                "in_app": 'โครงการ "{project_name}" บรรลุ milestone: {milestone_name}',
                "email_subject": "DENSO - ความสำเร็จของโครงการ",
                "email_body": """
                <h2>🎉 ความสำเร็จของโครงการ</h2>
                <p>สวัสดี {user_name},</p>
                <p>ยินดีด้วย! โครงการ "{project_name}" ได้บรรลุ milestone สำคัญ:</p>
                <ul>
                    <li><strong>Milestone:</strong> {milestone_name}</li>
                    <li><strong>วันที่บรรลุ:</strong> {achievement_date}</li>
                    <li><strong>ความคืบหน้าโครงการ:</strong> {project_completion}%</li>
                </ul>
                <p>ขอบคุณสำหรับการทำงานที่ยอดเยี่ยม!</p>
                """,
                "priority": "low",
            },
            "team_invitation": {
                "title": "คุณได้รับเชิญเข้าร่วมทีม",
                "in_app": 'คุณได้รับเชิญให้เข้าร่วมโครงการ "{project_name}" ในฐานะ {role}',
                "email_subject": "DENSO - เชิญเข้าร่วมโครงการ",
                "email_body": """
                <h2>เชิญเข้าร่วมโครงการ</h2>
                <p>สวัสดี {user_name},</p>
                <p>คุณได้รับเชิญให้เข้าร่วมโครงการใหม่:</p>
                <ul>
                    <li><strong>โครงการ:</strong> {project_name}</li>
                    <li><strong>บทบาท:</strong> {role}</li>
                    <li><strong>เชิญโดย:</strong> {invited_by}</li>
                </ul>
                <p>รายละเอียดโครงการ: {project_description}</p>
                <p>กรุณาเข้าสู่ระบบเพื่อยอมรับการเชิญ</p>
                """,
                "priority": "medium",
            },
            "system_maintenance": {
                "title": "แจ้งบำรุงรักษาระบบ",
                "in_app": "ระบบจะปิดบำรุงรักษาวันที่ {maintenance_date} เวลา {maintenance_time}",
                "email_subject": "DENSO - แจ้งบำรุงรักษาระบบ",
                "email_body": """
                <h2>แจ้งบำรุงรักษาระบบ</h2>
                <p>เรียนผู้ใช้งานทุกท่าน,</p>
                <p>ระบบ DENSO Project Manager Pro จะปิดบำรุงรักษา:</p>
                <ul>
                    <li><strong>วันที่:</strong> {maintenance_date}</li>
                    <li><strong>เวลา:</strong> {maintenance_time}</li>
                    <li><strong>ระยะเวลา:</strong> {duration} ชั่วโมง</li>
                </ul>
                <p>เหตุผล: {reason}</p>
                <p>กรุณาจัดเก็บงานของท่านให้เรียบร้อยก่อนเวลาดังกล่าว</p>
                <p>ขออภัยในความไม่สะดวก</p>
                """,
                "priority": "high",
            },
            "weekly_summary": {
                "title": "สรุปรายงานประจำสัปดาห์",
                "in_app": "รายงานสรุปงานประจำสัปดาห์ของคุณ",
                "email_subject": "DENSO - รายงานสรุปประจำสัปดาห์",
                "email_body": """
                <h2>รายงานสรุปประจำสัปดาห์</h2>
                <p>สวัสดี {user_name},</p>
                <p>สรุปผลงานของคุณในสัปดาห์ที่ผ่านมา:</p>
                <ul>
                    <li><strong>งานที่เสร็จ:</strong> {completed_tasks} งาน</li>
                    <li><strong>งานที่กำลังทำ:</strong> {active_tasks} งาน</li>
                    <li><strong>งานที่เลยกำหนด:</strong> {overdue_tasks} งาน</li>
                    <li><strong>เวลาทำงานรวม:</strong> {total_hours} ชั่วโมง</li>
                </ul>
                <p>เป้าหมายสัปดาห์หน้า: {next_week_goals}</p>
                """,
                "priority": "low",
            },
        }

    def _setup_notification_rules(self):
        """Setup automatic notification rules"""
        self.notification_rules = {
            "task_due_reminder_days": [7, 3, 1],  # แจ้งเตือนก่อนครบกำหนด 7, 3, 1 วัน
            "overdue_reminder_days": [1, 3, 7],  # แจ้งเตือนหลังเลยกำหนด 1, 3, 7 วัน
            "enable_email_notifications": True,
            "enable_browser_notifications": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "weekend_notifications": False,
            "max_notifications_per_user_per_day": 50,
        }

    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any],
        priority: str = "medium",
        send_email: bool = True,
        schedule_time: Optional[datetime] = None,
    ) -> bool:
        """Create and send notification"""
        try:
            # Validate input
            if not self._validate_notification_data(user_id, notification_type, data):
                return False

            # Check if user exists and is active
            user = self._get_user_notification_settings(user_id)
            if not user:
                logger.warning(f"User {user_id} not found or inactive")
                return False

            # Check notification limits
            if not self._check_notification_limits(user_id):
                logger.warning(f"Notification limit exceeded for user {user_id}")
                return False

            # Get template
            template = self.templates.get(notification_type)
            if not template:
                logger.error(f"Template not found for type: {notification_type}")
                return False

            # Format messages
            title = self._format_message(template["title"], data)
            in_app_message = self._format_message(template["in_app"], data)

            # Create in-app notification
            notification_id = self._create_in_app_notification(
                user_id, notification_type, title, in_app_message, priority, data
            )

            if not notification_id:
                return False

            # Send email if enabled and requested
            if (
                send_email
                and self.email_enabled
                and user.get("email_notifications", True)
            ):
                self._schedule_email_notification(user, template, data)

            # Add to real-time queue
            self._add_to_realtime_queue(
                user_id,
                {
                    "id": notification_id,
                    "type": notification_type,
                    "title": title,
                    "message": in_app_message,
                    "priority": priority,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.info(f"Notification created: {notification_type} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return False

    def _validate_notification_data(
        self, user_id: int, notification_type: str, data: Dict
    ) -> bool:
        """Validate notification data"""
        if not isinstance(user_id, int) or user_id <= 0:
            return False

        if not notification_type or notification_type not in self.templates:
            return False

        if not isinstance(data, dict):
            return False

        return True

    def _get_user_notification_settings(self, user_id: int) -> Optional[Dict]:
        """Get user and their notification settings"""
        try:
            query = """
                SELECT u.UserID, u.Email, u.FirstName, u.LastName, u.IsActive,
                       u.NotificationSettings
                FROM Users u
                WHERE u.UserID = ? AND u.IsActive = 1
            """
            result = self.db.execute_query(query, (user_id,))

            if not result:
                return None

            user = result[0]

            # Parse notification settings
            try:
                settings = json.loads(user.get("NotificationSettings") or "{}")
            except:
                settings = {}

            user["email_notifications"] = settings.get("email_notifications", True)
            user["browser_notifications"] = settings.get("browser_notifications", True)
            user["quiet_hours"] = settings.get("quiet_hours", False)

            return user

        except Exception as e:
            logger.error(f"Error getting user notification settings: {e}")
            return None

    def _check_notification_limits(self, user_id: int) -> bool:
        """Check if user has exceeded notification limits"""
        try:
            today = date.today()
            query = """
                SELECT COUNT(*) as count
                FROM Notifications
                WHERE UserID = ? AND CAST(CreatedDate as DATE) = ?
            """
            result = self.db.execute_query(query, (user_id, today))

            if result:
                daily_count = result[0]["count"]
                max_daily = self.notification_rules[
                    "max_notifications_per_user_per_day"
                ]
                return daily_count < max_daily

            return True

        except Exception as e:
            logger.error(f"Error checking notification limits: {e}")
            return True  # Allow if check fails

    def _format_message(self, template: str, data: Dict[str, Any]) -> str:
        """Format message template with data"""
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return template

    def _create_in_app_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        priority: str,
        data: Dict,
    ) -> Optional[int]:
        """Create in-app notification"""
        try:
            query = """
                INSERT INTO Notifications (UserID, Type, Title, Message, Priority, CreatedDate, ActionUrl)
                VALUES (?, ?, ?, ?, ?, GETDATE(), ?)
            """

            action_url = data.get("action_url", "")

            self.db.execute_non_query(
                query,
                (user_id, notification_type, title, message, priority, action_url),
            )

            # Get the inserted notification ID
            id_query = "SELECT SCOPE_IDENTITY() as id"
            result = self.db.execute_query(id_query)

            return result[0]["id"] if result else None

        except Exception as e:
            logger.error(f"Error creating in-app notification: {e}")
            return None

    def _schedule_email_notification(self, user: Dict, template: Dict, data: Dict):
        """Schedule email notification for sending"""
        try:
            if not self.email_enabled:
                return

            email_data = {
                "to_email": user["Email"],
                "to_name": f"{user['FirstName']} {user['LastName']}",
                "subject": self._format_message(template["email_subject"], data),
                "body": self._format_message(template["email_body"], data),
                "user_data": user,
                "template_data": data,
            }

            # Send email in background thread
            self.executor.submit(self._send_email_notification, email_data)

        except Exception as e:
            logger.error(f"Error scheduling email notification: {e}")

    def _send_email_notification(self, email_data: Dict):
        """Send email notification"""
        try:
            if not self.email_enabled:
                return False

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_data["subject"]
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = email_data["to_email"]

            # Create HTML part
            html_body = self._create_email_html(
                email_data["body"], email_data["template_data"]
            )
            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {email_data['to_email']}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def _create_email_html(self, body: str, data: Dict) -> str:
        """Create formatted HTML email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>DENSO Project Manager Pro</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .button {{ background: #2a5298; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚗 DENSO Project Manager Pro</h1>
                <p>การแจ้งเตือนจากระบบจัดการโครงการ</p>
            </div>
            <div class="content">
                {body}
                <p style="margin-top: 30px;">
                    <a href="#" class="button">เข้าสู่ระบบ</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2024 DENSO Corporation. All rights reserved.</p>
                <p>อีเมลนี้ส่งมาจากระบบอัตโนมัติ กรุณาอย่าตอบกลับ</p>
            </div>
        </body>
        </html>
        """

    def _add_to_realtime_queue(self, user_id: int, notification: Dict):
        """Add notification to real-time queue"""
        try:
            if "notifications_queue" not in st.session_state:
                st.session_state.notifications_queue = []

            st.session_state.notifications_queue.append(
                {
                    "user_id": user_id,
                    "notification": notification,
                    "timestamp": datetime.now(),
                }
            )

            # Keep only last 100 notifications
            if len(st.session_state.notifications_queue) > 100:
                st.session_state.notifications_queue = (
                    st.session_state.notifications_queue[-100:]
                )

        except Exception as e:
            logger.error(f"Error adding to realtime queue: {e}")

    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 20,
        unread_only: bool = False,
        notification_type: str = None,
    ) -> List[Dict[str, Any]]:
        """Get user notifications"""
        try:
            query = """
                SELECT NotificationID, Type, Title, Message, IsRead, CreatedDate, 
                       Priority, ActionUrl, ActionText, ExpiresAt
                FROM Notifications
                WHERE UserID = ?
            """
            params = [user_id]

            if unread_only:
                query += " AND IsRead = 0"

            if notification_type:
                query += " AND Type = ?"
                params.append(notification_type)

            query += " ORDER BY CreatedDate DESC"

            if limit:
                query = f"SELECT TOP ({limit}) * FROM ({query}) sub"

            return self.db.execute_query(query, tuple(params))

        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            query = """
                UPDATE Notifications 
                SET IsRead = 1, ReadDate = GETDATE()
                WHERE NotificationID = ? AND UserID = ?
            """

            rows_affected = self.db.execute_non_query(query, (notification_id, user_id))
            return rows_affected > 0

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    def mark_all_read(self, user_id: int) -> bool:
        """Mark all notifications as read for user"""
        try:
            query = """
                UPDATE Notifications 
                SET IsRead = 1, ReadDate = GETDATE()
                WHERE UserID = ? AND IsRead = 0
            """

            rows_affected = self.db.execute_non_query(query, (user_id,))
            logger.info(
                f"Marked {rows_affected} notifications as read for user {user_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete notification"""
        try:
            query = "DELETE FROM Notifications WHERE NotificationID = ? AND UserID = ?"
            rows_affected = self.db.execute_non_query(query, (notification_id, user_id))
            return rows_affected > 0

        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            return False

    def get_notification_statistics(self, user_id: int = None) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            if user_id:
                query = """
                    SELECT 
                        COUNT(*) as total_notifications,
                        SUM(CASE WHEN IsRead = 0 THEN 1 ELSE 0 END) as unread_count,
                        SUM(CASE WHEN Priority = 'critical' THEN 1 ELSE 0 END) as critical_count,
                        SUM(CASE WHEN CreatedDate >= DATEADD(day, -7, GETDATE()) THEN 1 ELSE 0 END) as last_week_count
                    FROM Notifications
                    WHERE UserID = ?
                """
                result = self.db.execute_query(query, (user_id,))
            else:
                query = """
                    SELECT 
                        COUNT(*) as total_notifications,
                        SUM(CASE WHEN IsRead = 0 THEN 1 ELSE 0 END) as unread_count,
                        COUNT(DISTINCT UserID) as total_users,
                        SUM(CASE WHEN CreatedDate >= DATEADD(day, -1, GETDATE()) THEN 1 ELSE 0 END) as today_count
                    FROM Notifications
                """
                result = self.db.execute_query(query)

            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Error getting notification statistics: {e}")
            return {}

    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old notifications"""
        try:
            query = """
                DELETE FROM Notifications 
                WHERE CreatedDate < DATEADD(day, -?, GETDATE())
                OR (ExpiresAt IS NOT NULL AND ExpiresAt < GETDATE())
            """

            rows_affected = self.db.execute_non_query(query, (days_old,))
            logger.info(f"Cleaned up {rows_affected} old notifications")
            return rows_affected

        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")
            return 0

    def subscribe_to_notifications(self, user_id: int, event_type: str):
        """Subscribe user to notification type"""
        if user_id not in self.subscribers[event_type]:
            self.subscribers[event_type].append(user_id)

    def unsubscribe_from_notifications(self, user_id: int, event_type: str):
        """Unsubscribe user from notification type"""
        if user_id in self.subscribers[event_type]:
            self.subscribers[event_type].remove(user_id)

    def broadcast_notification(
        self, event_type: str, data: Dict[str, Any], exclude_users: List[int] = None
    ):
        """Broadcast notification to all subscribers"""
        try:
            exclude_users = exclude_users or []
            subscribers = [
                uid for uid in self.subscribers[event_type] if uid not in exclude_users
            ]

            for user_id in subscribers:
                self.create_notification(user_id, event_type, data, send_email=False)

            logger.info(f"Broadcasted {event_type} to {len(subscribers)} users")
            return True

        except Exception as e:
            logger.error(f"Error broadcasting notification: {e}")
            return False

    # Auto-notification triggers
    def trigger_task_assigned(
        self, task_id: int, assigned_to_id: int, assigned_by_id: int
    ):
        """Trigger notification when task is assigned"""
        try:
            # Get task and project details
            query = """
                SELECT t.Title, t.Description, t.DueDate, t.Priority,
                       p.Name as ProjectName,
                       u1.FirstName + ' ' + u1.LastName as AssignedToName,
                       u2.FirstName + ' ' + u2.LastName as AssignedByName
                FROM Tasks t
                JOIN Projects p ON t.ProjectID = p.ProjectID
                JOIN Users u1 ON t.AssignedToID = u1.UserID
                LEFT JOIN Users u2 ON t.CreatedByID = u2.UserID
                WHERE t.TaskID = ?
            """

            result = self.db.execute_query(query, (task_id,))
            if not result:
                return False

            task_data = result[0]

            notification_data = {
                "task_id": task_id,
                "task_title": task_data["Title"],
                "project_name": task_data["ProjectName"],
                "description": task_data["Description"] or "ไม่มีรายละเอียด",
                "due_date": (
                    task_data["DueDate"].strftime("%d/%m/%Y")
                    if task_data["DueDate"]
                    else "ไม่กำหนด"
                ),
                "priority": task_data["Priority"],
                "user_name": task_data["AssignedToName"],
                "assigned_by": task_data["AssignedByName"] or "ระบบ",
                "action_url": f"/tasks?task_id={task_id}",
            }

            return self.create_notification(
                assigned_to_id, "task_assigned", notification_data, priority="medium"
            )

        except Exception as e:
            logger.error(f"Error triggering task assigned notification: {e}")
            return False

    def trigger_task_due_reminders(self):
        """Check and send due date reminders"""
        try:
            reminder_days = self.notification_rules["task_due_reminder_days"]
            notifications_sent = 0

            for days in reminder_days:
                due_date = date.today() + timedelta(days=days)

                query = """
                    SELECT t.TaskID, t.Title, t.DueDate, t.AssignedToID,
                           p.Name as ProjectName,
                           u.FirstName + ' ' + u.LastName as UserName
                    FROM Tasks t
                    JOIN Projects p ON t.ProjectID = p.ProjectID
                    JOIN Users u ON t.AssignedToID = u.UserID
                    WHERE CAST(t.DueDate as DATE) = ?
                    AND t.Status NOT IN ('Done', 'Cancelled')
                    AND t.AssignedToID IS NOT NULL
                """

                tasks = self.db.execute_query(query, (due_date,))

                for task in tasks:
                    # Check if reminder already sent
                    if self._check_reminder_sent(task["TaskID"], "task_due_soon", days):
                        continue

                    notification_data = {
                        "task_id": task["TaskID"],
                        "task_title": task["Title"],
                        "project_name": task["ProjectName"],
                        "user_name": task["UserName"],
                        "due_date": task["DueDate"].strftime("%d/%m/%Y"),
                        "days_remaining": days,
                        "action_url": f'/tasks?task_id={task["TaskID"]}',
                    }

                    if self.create_notification(
                        task["AssignedToID"],
                        "task_due_soon",
                        notification_data,
                        priority="high",
                    ):
                        self._mark_reminder_sent(task["TaskID"], "task_due_soon", days)
                        notifications_sent += 1

            logger.info(f"Sent {notifications_sent} due date reminders")
            return notifications_sent

        except Exception as e:
            logger.error(f"Error sending due date reminders: {e}")
            return 0

    def trigger_overdue_reminders(self):
        """Check and send overdue reminders"""
        try:
            reminder_days = self.notification_rules["overdue_reminder_days"]
            notifications_sent = 0

            for days in reminder_days:
                overdue_date = date.today() - timedelta(days=days)

                query = """
                    SELECT t.TaskID, t.Title, t.DueDate, t.AssignedToID,
                           p.Name as ProjectName,
                           u.FirstName + ' ' + u.LastName as UserName
                    FROM Tasks t
                    JOIN Projects p ON t.ProjectID = p.ProjectID
                    JOIN Users u ON t.AssignedToID = u.UserID
                    WHERE CAST(t.DueDate as DATE) = ?
                    AND t.Status NOT IN ('Done', 'Cancelled')
                    AND t.AssignedToID IS NOT NULL
                """

                tasks = self.db.execute_query(query, (overdue_date,))

                for task in tasks:
                    # Check if reminder already sent
                    if self._check_reminder_sent(task["TaskID"], "task_overdue", days):
                        continue

                    notification_data = {
                        "task_id": task["TaskID"],
                        "task_title": task["Title"],
                        "project_name": task["ProjectName"],
                        "user_name": task["UserName"],
                        "due_date": task["DueDate"].strftime("%d/%m/%Y"),
                        "days_overdue": days,
                        "action_url": f'/tasks?task_id={task["TaskID"]}',
                    }

                    if self.create_notification(
                        task["AssignedToID"],
                        "task_overdue",
                        notification_data,
                        priority="critical",
                    ):
                        self._mark_reminder_sent(task["TaskID"], "task_overdue", days)
                        notifications_sent += 1

            logger.info(f"Sent {notifications_sent} overdue reminders")
            return notifications_sent

        except Exception as e:
            logger.error(f"Error sending overdue reminders: {e}")
            return 0

    def _check_reminder_sent(self, task_id: int, reminder_type: str, days: int) -> bool:
        """Check if reminder was already sent"""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM Notifications
                WHERE Type = ? 
                AND Message LIKE ?
                AND CreatedDate >= DATEADD(day, -1, GETDATE())
            """

            message_pattern = f"%{task_id}%{days}%"
            result = self.db.execute_query(query, (reminder_type, message_pattern))

            return result[0]["count"] > 0 if result else False

        except Exception as e:
            logger.error(f"Error checking reminder sent: {e}")
            return False

    def _mark_reminder_sent(self, task_id: int, reminder_type: str, days: int):
        """Mark that reminder was sent (implementation depends on your tracking needs)"""
        # This could be implemented as a separate tracking table
        # For now, we rely on the notification itself as the marker
        pass

    def send_weekly_summary(self, user_id: int):
        """Send weekly summary to user"""
        try:
            # Get user's weekly stats
            week_start = date.today() - timedelta(days=7)

            query = """
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN Status IN ('To Do', 'In Progress', 'Review') THEN 1 ELSE 0 END) as active_tasks,
                    SUM(CASE WHEN DueDate < GETDATE() AND Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                    SUM(CASE WHEN ActualHours IS NOT NULL THEN ActualHours ELSE 0 END) as total_hours
                FROM Tasks
                WHERE AssignedToID = ?
                AND UpdatedDate >= ?
            """

            result = self.db.execute_query(query, (user_id, week_start))
            stats = result[0] if result else {}

            # Get user info
            user_query = "SELECT FirstName, LastName FROM Users WHERE UserID = ?"
            user_result = self.db.execute_query(user_query, (user_id,))

            if not user_result:
                return False

            user_info = user_result[0]

            notification_data = {
                "user_name": f"{user_info['FirstName']} {user_info['LastName']}",
                "completed_tasks": stats.get("completed_tasks", 0),
                "active_tasks": stats.get("active_tasks", 0),
                "overdue_tasks": stats.get("overdue_tasks", 0),
                "total_hours": stats.get("total_hours", 0),
                "next_week_goals": "ดำเนินการงานตามแผนที่กำหนด",
                "action_url": "/dashboard",
            }

            return self.create_notification(
                user_id,
                "weekly_summary",
                notification_data,
                priority="low",
                send_email=True,
            )

        except Exception as e:
            logger.error(f"Error sending weekly summary: {e}")
            return False


# UI Functions for Notification Management
def show_notifications_page(
    notification_manager: NotificationManager, user_data: Dict[str, Any]
):
    """Show notifications management page"""
    ui = UIComponents()

    # Page header
    ui.render_page_header("📧 ระบบการแจ้งเตือน", "จัดการและดูการแจ้งเตือนทั้งหมด", "📧")

    # Get user notifications stats
    user_id = user_data["UserID"]
    stats = safe_execute(
        notification_manager.get_notification_statistics, user_id, default_return={}
    )

    # Stats cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("การแจ้งเตือนทั้งหมด", stats.get("total_notifications", 0))

    with col2:
        unread_count = stats.get("unread_count", 0)
        st.metric(
            "ยังไม่ได้อ่าน",
            unread_count,
            delta=f"+{unread_count}" if unread_count > 0 else None,
        )

    with col3:
        critical_count = stats.get("critical_count", 0)
        st.metric(
            "ระดับวิกฤต",
            critical_count,
            delta=f"+{critical_count}" if critical_count > 0 else None,
        )

    with col4:
        week_count = stats.get("last_week_count", 0)
        st.metric("สัปดาห์ที่แล้ว", week_count)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📬 การแจ้งเตือน", "⚙️ ตั้งค่า", "📊 สถิติ", "🔧 จัดการ"])

    with tab1:
        show_notifications_list(notification_manager, user_id)

    with tab2:
        show_notification_settings(notification_manager, user_data)

    with tab3:
        show_notification_statistics(notification_manager, user_data)

    with tab4:
        if user_data["Role"] in ["Admin", "Project Manager"]:
            show_notification_management(notification_manager, user_data)
        else:
            st.error("❌ คุณไม่มีสิทธิ์เข้าถึงการจัดการการแจ้งเตือน")


def show_notifications_list(notification_manager: NotificationManager, user_id: int):
    """Show user's notifications list"""
    st.subheader("📬 การแจ้งเตือนของคุณ")

    # Filter options
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        show_unread_only = st.checkbox("แสดงเฉพาะที่ยังไม่ได้อ่าน")

    with col2:
        if st.button("🔄 รีเฟรช"):
            st.rerun()

    with col3:
        if st.button("✅ อ่านทั้งหมด"):
            if notification_manager.mark_all_read(user_id):
                st.success("อ่านการแจ้งเตือนทั้งหมดแล้ว")
                st.rerun()

    # Get notifications
    notifications = safe_execute(
        notification_manager.get_user_notifications,
        user_id,
        limit=50,
        unread_only=show_unread_only,
        default_return=[],
    )

    if not notifications:
        st.info("🎉 ไม่มีการแจ้งเตือน" + (" ที่ยังไม่ได้อ่าน" if show_unread_only else ""))
        return

    # Display notifications
    for notification in notifications:
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 1])

            with col1:
                # Priority indicator
                priority_colors = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🟠",
                    "critical": "🔴",
                }
                priority_icon = priority_colors.get(notification["Priority"], "⚪")
                st.markdown(f"### {priority_icon}")

                # Read/Unread indicator
                if not notification["IsRead"]:
                    st.markdown("🔵 **ใหม่**")

            with col2:
                # Notification content
                st.markdown(f"**{notification['Title']}**")
                st.markdown(notification["Message"])

                # Timestamp
                created_date = notification["CreatedDate"]
                time_ago = _format_time_ago(created_date)
                st.caption(f"🕐 {time_ago}")

            with col3:
                # Actions
                if not notification["IsRead"]:
                    if st.button(
                        "✅ อ่านแล้ว", key=f"read_{notification['NotificationID']}"
                    ):
                        if notification_manager.mark_notification_read(
                            notification["NotificationID"], user_id
                        ):
                            st.rerun()

                if st.button("🗑️ ลบ", key=f"delete_{notification['NotificationID']}"):
                    if notification_manager.delete_notification(
                        notification["NotificationID"], user_id
                    ):
                        st.success("ลบการแจ้งเตือนแล้ว")
                        st.rerun()

            st.markdown("---")


def show_notification_settings(
    notification_manager: NotificationManager, user_data: Dict[str, Any]
):
    """Show notification settings"""
    st.subheader("⚙️ ตั้งค่าการแจ้งเตือน")

    # Get current settings
    try:
        current_settings = json.loads(user_data.get("NotificationSettings", "{}"))
    except:
        current_settings = {}

    with st.form("notification_settings_form"):
        st.markdown("### 📧 การแจ้งเตือนทางอีเมล")

        email_notifications = st.checkbox(
            "เปิดการแจ้งเตือนทางอีเมล",
            value=current_settings.get("email_notifications", True),
        )

        task_assigned_email = st.checkbox(
            "แจ้งเตือนเมื่อได้รับมอบหมายงาน",
            value=current_settings.get("task_assigned_email", True),
        )

        task_due_email = st.checkbox(
            "แจ้งเตือนงานใกล้ครบกำหนด", value=current_settings.get("task_due_email", True)
        )

        project_updates_email = st.checkbox(
            "แจ้งเตือนการอัปเดตโครงการ",
            value=current_settings.get("project_updates_email", True),
        )

        st.markdown("### 🔔 การแจ้งเตือนในระบบ")

        browser_notifications = st.checkbox(
            "การแจ้งเตือนบนเบราว์เซอร์",
            value=current_settings.get("browser_notifications", True),
        )

        sound_notifications = st.checkbox(
            "เสียงแจ้งเตือน", value=current_settings.get("sound_notifications", False)
        )

        st.markdown("### ⏰ ช่วงเวลาแจ้งเตือน")

        quiet_hours = st.checkbox(
            "เปิดโหมดเงียบ", value=current_settings.get("quiet_hours", False)
        )

        col1, col2 = st.columns(2)
        with col1:
            quiet_start = st.time_input("เริ่มโหมดเงียบ", value=time(22, 0))
        with col2:
            quiet_end = st.time_input("สิ้นสุดโหมดเงียบ", value=time(8, 0))

        st.markdown("### 📅 การแจ้งเตือนตามช่วงเวลา")

        weekend_notifications = st.checkbox(
            "รับการแจ้งเตือนในวันหยุดสุดสัปดาห์",
            value=current_settings.get("weekend_notifications", False),
        )

        weekly_summary = st.checkbox(
            "รับสรุปรายงานประจำสัปดาห์", value=current_settings.get("weekly_summary", True)
        )

        if st.form_submit_button("💾 บันทึกการตั้งค่า", type="primary"):
            new_settings = {
                "email_notifications": email_notifications,
                "task_assigned_email": task_assigned_email,
                "task_due_email": task_due_email,
                "project_updates_email": project_updates_email,
                "browser_notifications": browser_notifications,
                "sound_notifications": sound_notifications,
                "quiet_hours": quiet_hours,
                "quiet_start": quiet_start.strftime("%H:%M"),
                "quiet_end": quiet_end.strftime("%H:%M"),
                "weekend_notifications": weekend_notifications,
                "weekly_summary": weekly_summary,
            }

            # Update user settings
            try:
                settings_json = json.dumps(new_settings)
                query = "UPDATE Users SET NotificationSettings = ? WHERE UserID = ?"
                notification_manager.db.execute_non_query(
                    query, (settings_json, user_data["UserID"])
                )
                st.success("✅ บันทึกการตั้งค่าสำเร็จ")
                st.rerun()
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {e}")


def show_notification_statistics(
    notification_manager: NotificationManager, user_data: Dict[str, Any]
):
    """Show notification statistics"""
    st.subheader("📊 สถิติการแจ้งเตือน")

    user_id = user_data["UserID"]

    # Get detailed statistics
    try:
        # Last 30 days statistics
        query = """
            SELECT 
                CAST(CreatedDate as DATE) as date,
                COUNT(*) as count,
                SUM(CASE WHEN IsRead = 1 THEN 1 ELSE 0 END) as read_count
            FROM Notifications
            WHERE UserID = ? 
            AND CreatedDate >= DATEADD(day, -30, GETDATE())
            GROUP BY CAST(CreatedDate as DATE)
            ORDER BY date DESC
        """

        daily_stats = notification_manager.db.execute_query(query, (user_id,))

        if daily_stats:
            df = pd.DataFrame(daily_stats)
            df["date"] = pd.to_datetime(df["date"])

            # Daily notifications chart
            import plotly.express as px

            fig = px.line(
                df, x="date", y="count", title="การแจ้งเตือนรายวันใน 30 วันที่ผ่านมา"
            )
            fig.update_layout(xaxis_title="วันที่", yaxis_title="จำนวนการแจ้งเตือน")
            st.plotly_chart(fig, use_container_width=True)

        # Notification types statistics
        type_query = """
            SELECT Type, COUNT(*) as count
            FROM Notifications
            WHERE UserID = ?
            AND CreatedDate >= DATEADD(month, -3, GETDATE())
            GROUP BY Type
            ORDER BY count DESC
        """

        type_stats = notification_manager.db.execute_query(type_query, (user_id,))

        if type_stats:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### ประเภทการแจ้งเตือน (3 เดือนที่ผ่านมา)")
                df_types = pd.DataFrame(type_stats)
                fig = px.pie(
                    df_types, values="count", names="Type", title="การกระจายตามประเภท"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("### รายละเอียดตามประเภท")
                for stat in type_stats:
                    st.metric(_format_notification_type(stat["Type"]), stat["count"])

    except Exception as e:
        st.error(f"ไม่สามารถโหลดสถิติได้: {e}")


def show_notification_management(
    notification_manager: NotificationManager, user_data: Dict[str, Any]
):
    """Show notification management for admins"""
    st.subheader("🔧 จัดการการแจ้งเตือน")

    # System-wide statistics
    st.markdown("### 📊 สถิติระบบ")
    system_stats = safe_execute(
        notification_manager.get_notification_statistics, default_return={}
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("การแจ้งเตือนทั้งหมด", system_stats.get("total_notifications", 0))
    with col2:
        st.metric("ยังไม่ได้อ่าน", system_stats.get("unread_count", 0))
    with col3:
        st.metric("ผู้ใช้ทั้งหมด", system_stats.get("total_users", 0))
    with col4:
        st.metric("วันนี้", system_stats.get("today_count", 0))

    st.markdown("---")

    # Send custom notification
    st.markdown("### 📤 ส่งการแจ้งเตือนกำหนดเอง")

    with st.form("send_custom_notification"):
        col1, col2 = st.columns(2)

        with col1:
            # Get users list
            users_query = "SELECT UserID, FirstName + ' ' + LastName as FullName FROM Users WHERE IsActive = 1 ORDER BY FullName"
            users = notification_manager.db.execute_query(users_query)
            user_options = {f"{u['FullName']}": u["UserID"] for u in users}

            selected_users = st.multiselect(
                "เลือกผู้รับ",
                options=list(user_options.keys()),
                help="เลือกผู้ใช้ที่ต้องการส่งการแจ้งเตือน",
            )

        with col2:
            notification_type = st.selectbox(
                "ประเภทการแจ้งเตือน",
                options=list(notification_manager.templates.keys()),
                format_func=_format_notification_type,
            )

            priority = st.selectbox(
                "ระดับความสำคัญ", options=["low", "medium", "high", "critical"], index=1
            )

        title = st.text_input("หัวข้อ")
        message = st.text_area("ข้อความ", height=100)
        send_email = st.checkbox("ส่งอีเมลด้วย", value=True)

        if st.form_submit_button("📤 ส่งการแจ้งเตือน", type="primary"):
            if selected_users and title and message:
                sent_count = 0
                for user_name in selected_users:
                    user_id = user_options[user_name]

                    custom_data = {
                        "title": title,
                        "message": message,
                        "user_name": user_name,
                        "sent_by": f"{user_data['FirstName']} {user_data['LastName']}",
                    }

                    if notification_manager.create_notification(
                        user_id,
                        notification_type,
                        custom_data,
                        priority=priority,
                        send_email=send_email,
                    ):
                        sent_count += 1

                st.success(f"✅ ส่งการแจ้งเตือนให้ {sent_count} คน")
            else:
                st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน")

    st.markdown("---")

    # Cleanup tools
    st.markdown("### 🧹 เครื่องมือทำความสะอาด")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗑️ ลบการแจ้งเตือนเก่า (30 วัน)"):
            deleted_count = notification_manager.cleanup_old_notifications(30)
            st.success(f"ลบการแจ้งเตือนเก่า {deleted_count} รายการ")

    with col2:
        if st.button("🔄 ส่งการแจ้งเตือนครบกำหนด"):
            sent_count = notification_manager.trigger_task_due_reminders()
            st.success(f"ส่งการแจ้งเตือนครบกำหนด {sent_count} รายการ")

    with col3:
        if st.button("⚠️ ส่งการแจ้งเตือนเลยกำหนด"):
            sent_count = notification_manager.trigger_overdue_reminders()
            st.success(f"ส่งการแจ้งเตือนเลยกำหนด {sent_count} รายการ")


def _format_time_ago(timestamp: datetime) -> str:
    """Format timestamp to human-readable time ago"""
    try:
        now = datetime.now()
        diff = now - timestamp

        if diff.days > 0:
            return f"{diff.days} วันที่แล้ว"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ชั่วโมงที่แล้ว"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} นาทีที่แล้ว"
        else:
            return "เมื่อสักครู่"
    except:
        return "ไม่ทราบเวลา"


def _format_notification_type(notification_type: str) -> str:
    """Format notification type for display"""
    type_map = {
        "task_assigned": "📋 มอบหมายงาน",
        "task_due_soon": "⏰ ใกล้ครบกำหนด",
        "task_overdue": "🚨 เลยกำหนด",
        "project_status_changed": "📁 สถานะโครงการ",
        "project_milestone": "🎯 Milestone",
        "team_invitation": "👥 เชิญเข้าทีม",
        "system_maintenance": "🔧 บำรุงรักษา",
        "weekly_summary": "📊 สรุปรายสัปดาห์",
    }
    return type_map.get(notification_type, notification_type)
