#!/usr/bin/env python3
"""
modules/tasks.py
Task Management System for SDX Project Manager
Complete task CRUD operations and Kanban-style management
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class TaskManager:
    """Complete task management system with Kanban functionality"""

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_sample_data()

    def _ensure_sample_data(self):
        """Ensure sample tasks exist for demo"""
        try:
            # Check if tasks exist
            task_count = self.db.execute_scalar("SELECT COUNT(*) FROM Tasks")

            if task_count == 0:
                # Get project IDs
                projects = self.db.execute_query("SELECT ProjectID FROM Projects")
                if not projects:
                    return

                # Create sample tasks
                sample_tasks = [
                    {
                        "title": "ออกแบบ UI Homepage",
                        "description": "สร้างการออกแบบ UI สำหรับหน้าแรกของเว็บไซต์",
                        "project_id": projects[0]["ProjectID"],
                        "status": "In Progress",
                        "priority": "High",
                        "assigned_to": 1,
                        "due_date": "2024-07-15",
                        "estimated_hours": 16,
                    },
                    {
                        "title": "พัฒนา API Authentication",
                        "description": "สร้าง API สำหรับการยืนยันตัวตนผู้ใช้งาน",
                        "project_id": (
                            projects[1]["ProjectID"]
                            if len(projects) > 1
                            else projects[0]["ProjectID"]
                        ),
                        "status": "To Do",
                        "priority": "Medium",
                        "assigned_to": 1,
                        "due_date": "2024-07-20",
                        "estimated_hours": 24,
                    },
                    {
                        "title": "ทดสอบระบบความปลอดภัย",
                        "description": "ทดสอบช่องโหว่ด้านความปลอดภัยของระบบ",
                        "project_id": projects[0]["ProjectID"],
                        "status": "Done",
                        "priority": "High",
                        "assigned_to": 1,
                        "due_date": "2024-07-05",
                        "estimated_hours": 8,
                    },
                    {
                        "title": "เขียนเอกสารคู่มือผู้ใช้",
                        "description": "สร้างคู่มือการใช้งานระบบสำหรับผู้ใช้งานทั่วไป",
                        "project_id": projects[0]["ProjectID"],
                        "status": "To Do",
                        "priority": "Low",
                        "assigned_to": 1,
                        "due_date": "2024-07-25",
                        "estimated_hours": 12,
                    },
                ]

                for task in sample_tasks:
                    self.create_task(task, create_by_system=True)

                logger.info("Sample tasks created")

        except Exception as e:
            logger.error(f"Error ensuring sample task data: {e}")

    def create_task(
        self, task_data: Dict[str, Any], create_by_system: bool = False
    ) -> Optional[int]:
        """Create new task"""
        try:
            query = """
                INSERT INTO Tasks (
                    ProjectID, TaskTitle, TaskDescription, Status, Priority,
                    AssignedTo, DueDate, EstimatedHours, CreatedBy
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            created_by = 1 if create_by_system else st.session_state.user["UserID"]

            result = self.db.execute_non_query(
                query,
                (
                    task_data["project_id"],
                    task_data["title"],
                    task_data["description"],
                    task_data["status"],
                    task_data["priority"],
                    task_data["assigned_to"],
                    task_data["due_date"],
                    task_data.get("estimated_hours", 0),
                    created_by,
                ),
            )

            if result > 0:
                task_id = self.db.execute_scalar("SELECT @@IDENTITY")
                logger.info(f"Task created with ID: {task_id}")
                return task_id

            return None

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None

    def get_all_tasks(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get all tasks with optional filters"""
        try:
            base_query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.TaskDescription,
                    t.Status,
                    t.Priority,
                    t.DueDate,
                    t.EstimatedHours,
                    t.ActualHours,
                    t.Progress,
                    p.ProjectName,
                    assigned.FullName as AssignedTo,
                    creator.FullName as CreatedBy,
                    t.CreatedDate,
                    CASE 
                        WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 
                        ELSE 0 
                    END as IsOverdue,
                    DATEDIFF(day, GETDATE(), t.DueDate) as DaysRemaining
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users assigned ON t.AssignedTo = assigned.UserID
                LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
                WHERE 1=1
            """

            params = []

            # Apply filters
            if filters:
                if filters.get("project") and filters["project"] != "ทั้งหมด":
                    base_query += " AND p.ProjectName = ?"
                    params.append(filters["project"])

                if filters.get("status") and filters["status"] != "ทั้งหมด":
                    base_query += " AND t.Status = ?"
                    params.append(filters["status"])

                if filters.get("priority") and filters["priority"] != "ทั้งหมด":
                    base_query += " AND t.Priority = ?"
                    params.append(filters["priority"])

                if filters.get("assignee") and filters["assignee"] != "ทั้งหมด":
                    base_query += " AND assigned.FullName = ?"
                    params.append(filters["assignee"])

                if filters.get("search"):
                    base_query += (
                        " AND (t.TaskTitle LIKE ? OR t.TaskDescription LIKE ?)"
                    )
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])

            base_query += " ORDER BY t.CreatedDate DESC"

            return self.db.execute_query(base_query, tuple(params) if params else None)

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []

    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            query = """
                SELECT 
                    t.*,
                    p.ProjectName,
                    assigned.FullName as AssignedTo,
                    creator.FullName as CreatedBy
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users assigned ON t.AssignedTo = assigned.UserID
                LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
                WHERE t.TaskID = ?
            """

            result = self.db.execute_query(query, (task_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None

    def update_task(self, task_id: int, task_data: Dict[str, Any]) -> bool:
        """Update task"""
        try:
            query = """
                UPDATE Tasks 
                SET TaskTitle = ?, TaskDescription = ?, Status = ?, Priority = ?,
                    AssignedTo = ?, DueDate = ?, EstimatedHours = ?, Progress = ?,
                    LastModifiedDate = GETDATE(), LastModifiedBy = ?
                WHERE TaskID = ?
            """

            result = self.db.execute_non_query(
                query,
                (
                    task_data["title"],
                    task_data["description"],
                    task_data["status"],
                    task_data["priority"],
                    task_data["assigned_to"],
                    task_data["due_date"],
                    task_data.get("estimated_hours", 0),
                    task_data.get("progress", 0),
                    st.session_state.user["UserID"],
                    task_id,
                ),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False

    def update_task_status(self, task_id: int, new_status: str) -> bool:
        """Update task status (for Kanban board)"""
        try:
            # Auto-set progress based on status
            progress_map = {"To Do": 0, "In Progress": 50, "Review": 80, "Done": 100}

            progress = progress_map.get(new_status, 0)

            query = """
                UPDATE Tasks 
                SET Status = ?, Progress = ?, LastModifiedDate = GETDATE()
                WHERE TaskID = ?
            """

            result = self.db.execute_non_query(query, (new_status, progress, task_id))
            return result > 0

        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        """Delete task"""
        try:
            result = self.db.execute_non_query(
                "DELETE FROM Tasks WHERE TaskID = ?", (task_id,)
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False

    def get_tasks_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tasks for specific project"""
        try:
            query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.Status,
                    t.Priority,
                    t.Progress,
                    t.DueDate,
                    u.FullName as AssignedTo
                FROM Tasks t
                LEFT JOIN Users u ON t.AssignedTo = u.UserID
                WHERE t.ProjectID = ?
                ORDER BY t.CreatedDate DESC
            """

            return self.db.execute_query(query, (project_id,))

        except Exception as e:
            logger.error(f"Error getting tasks for project {project_id}: {e}")
            return []

    def get_tasks_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get tasks assigned to specific user"""
        try:
            query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.Status,
                    t.Priority,
                    t.DueDate,
                    p.ProjectName
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                WHERE t.AssignedTo = ?
                ORDER BY t.DueDate ASC
            """

            return self.db.execute_query(query, (user_id,))

        except Exception as e:
            logger.error(f"Error getting tasks for user {user_id}: {e}")
            return []

    def get_kanban_board_data(
        self, project_id: Optional[int] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get tasks organized for Kanban board"""
        try:
            base_query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.TaskDescription,
                    t.Status,
                    t.Priority,
                    t.DueDate,
                    t.Progress,
                    p.ProjectName,
                    u.FullName as AssignedTo,
                    CASE 
                        WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 
                        ELSE 0 
                    END as IsOverdue
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users u ON t.AssignedTo = u.UserID
            """

            params = None
            if project_id:
                base_query += " WHERE t.ProjectID = ?"
                params = (project_id,)

            base_query += " ORDER BY t.Priority DESC, t.DueDate ASC"

            tasks = self.db.execute_query(base_query, params)

            # Organize by status
            kanban_data = {"To Do": [], "In Progress": [], "Review": [], "Done": []}

            for task in tasks:
                status = task["Status"]
                if status in kanban_data:
                    kanban_data[status].append(task)
                else:
                    # Handle any non-standard statuses
                    kanban_data["To Do"].append(task)

            return kanban_data

        except Exception as e:
            logger.error(f"Error getting Kanban data: {e}")
            return {status: [] for status in ["To Do", "In Progress", "Review", "Done"]}

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics"""
        try:
            stats = {}

            # Total tasks
            stats["total"] = self.db.execute_scalar("SELECT COUNT(*) FROM Tasks") or 0

            # Tasks by status
            status_data = self.db.execute_query(
                """
                SELECT Status, COUNT(*) as Count
                FROM Tasks 
                GROUP BY Status
            """
            )
            stats["by_status"] = {row["Status"]: row["Count"] for row in status_data}

            # Active tasks (not done)
            stats["active"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Tasks WHERE Status != 'Done'"
                )
                or 0
            )

            # Completed tasks
            stats["completed"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Tasks WHERE Status = 'Done'"
                )
                or 0
            )

            # Overdue tasks
            stats["overdue"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Tasks 
                WHERE DueDate < GETDATE() AND Status != 'Done'
            """
                )
                or 0
            )

            # Tasks due today
            stats["due_today"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Tasks 
                WHERE CAST(DueDate as DATE) = CAST(GETDATE() as DATE) AND Status != 'Done'
            """
                )
                or 0
            )

            # Tasks due this week
            stats["due_this_week"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Tasks 
                WHERE DueDate BETWEEN GETDATE() AND DATEADD(day, 7, GETDATE()) 
                AND Status != 'Done'
            """
                )
                or 0
            )

            # Average completion time
            stats["avg_completion_days"] = (
                self.db.execute_scalar(
                    """
                SELECT AVG(DATEDIFF(day, CreatedDate, LastModifiedDate))
                FROM Tasks 
                WHERE Status = 'Done' AND LastModifiedDate IS NOT NULL
            """
                )
                or 0
            )

            # Tasks by priority
            priority_data = self.db.execute_query(
                """
                SELECT Priority, COUNT(*) as Count
                FROM Tasks 
                WHERE Status != 'Done'
                GROUP BY Priority
            """
            )
            stats["by_priority"] = {
                row["Priority"]: row["Count"] for row in priority_data
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {}

    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks"""
        try:
            query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.DueDate,
                    t.Priority,
                    p.ProjectName,
                    u.FullName as AssignedTo,
                    DATEDIFF(day, t.DueDate, GETDATE()) as DaysOverdue
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users u ON t.AssignedTo = u.UserID
                WHERE t.DueDate < GETDATE() AND t.Status != 'Done'
                ORDER BY t.DueDate ASC
            """

            return self.db.execute_query(query)

        except Exception as e:
            logger.error(f"Error getting overdue tasks: {e}")
            return []

    def get_upcoming_tasks(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get tasks due in next N days"""
        try:
            query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.DueDate,
                    t.Priority,
                    p.ProjectName,
                    u.FullName as AssignedTo,
                    DATEDIFF(day, GETDATE(), t.DueDate) as DaysUntilDue
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users u ON t.AssignedTo = u.UserID
                WHERE t.DueDate BETWEEN GETDATE() AND DATEADD(day, ?, GETDATE())
                AND t.Status != 'Done'
                ORDER BY t.DueDate ASC
            """

            return self.db.execute_query(query, (days,))

        except Exception as e:
            logger.error(f"Error getting upcoming tasks: {e}")
            return []

    def update_task_progress(self, task_id: int, progress: int) -> bool:
        """Update task progress"""
        try:
            # Auto-update status based on progress
            if progress == 0:
                status = "To Do"
            elif progress < 80:
                status = "In Progress"
            elif progress < 100:
                status = "Review"
            else:
                status = "Done"

            query = """
                UPDATE Tasks 
                SET Progress = ?, Status = ?, LastModifiedDate = GETDATE()
                WHERE TaskID = ?
            """

            result = self.db.execute_non_query(query, (progress, status, task_id))
            return result > 0

        except Exception as e:
            logger.error(f"Error updating task progress: {e}")
            return False

    def assign_task(self, task_id: int, user_id: int) -> bool:
        """Assign task to user"""
        try:
            result = self.db.execute_non_query(
                """
                UPDATE Tasks 
                SET AssignedTo = ?, LastModifiedDate = GETDATE()
                WHERE TaskID = ?
            """,
                (user_id, task_id),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error assigning task: {e}")
            return False

    def log_time_entry(
        self, task_id: int, user_id: int, hours: float, description: str = ""
    ) -> bool:
        """Log time spent on task"""
        try:
            # Insert time tracking record
            result = self.db.execute_non_query(
                """
                INSERT INTO TimeTracking (TaskID, UserID, Duration, Description, StartTime)
                VALUES (?, ?, ?, ?, GETDATE())
            """,
                (task_id, user_id, hours, description),
            )

            if result > 0:
                # Update task actual hours
                self.db.execute_non_query(
                    """
                    UPDATE Tasks 
                    SET ActualHours = ISNULL(ActualHours, 0) + ?
                    WHERE TaskID = ?
                """,
                    (hours, task_id),
                )

            return result > 0

        except Exception as e:
            logger.error(f"Error logging time entry: {e}")
            return False

    def get_task_time_entries(self, task_id: int) -> List[Dict[str, Any]]:
        """Get time entries for task"""
        try:
            query = """
                SELECT 
                    tt.TimeTrackingID,
                    tt.Duration,
                    tt.Description,
                    tt.StartTime,
                    u.FullName as UserName
                FROM TimeTracking tt
                LEFT JOIN Users u ON tt.UserID = u.UserID
                WHERE tt.TaskID = ?
                ORDER BY tt.StartTime DESC
            """

            return self.db.execute_query(query, (task_id,))

        except Exception as e:
            logger.error(f"Error getting time entries: {e}")
            return []

    def get_my_tasks(
        self, user_id: int, status_filter: str = "active"
    ) -> List[Dict[str, Any]]:
        """Get tasks for current user"""
        try:
            base_query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.Status,
                    t.Priority,
                    t.DueDate,
                    t.Progress,
                    p.ProjectName,
                    CASE 
                        WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 
                        ELSE 0 
                    END as IsOverdue
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                WHERE t.AssignedTo = ?
            """

            params = [user_id]

            if status_filter == "active":
                base_query += " AND t.Status != 'Done'"
            elif status_filter == "completed":
                base_query += " AND t.Status = 'Done'"
            elif status_filter == "overdue":
                base_query += " AND t.DueDate < GETDATE() AND t.Status != 'Done'"

            base_query += " ORDER BY t.DueDate ASC"

            return self.db.execute_query(base_query, tuple(params))

        except Exception as e:
            logger.error(f"Error getting my tasks: {e}")
            return []

    def search_tasks(self, search_term: str) -> List[Dict[str, Any]]:
        """Search tasks"""
        try:
            query = """
                SELECT 
                    t.TaskID,
                    t.TaskTitle,
                    t.TaskDescription,
                    t.Status,
                    t.Priority,
                    p.ProjectName
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                WHERE t.TaskTitle LIKE ? OR t.TaskDescription LIKE ?
                ORDER BY t.TaskTitle
            """

            search_pattern = f"%{search_term}%"
            return self.db.execute_query(query, (search_pattern, search_pattern))

        except Exception as e:
            logger.error(f"Error searching tasks: {e}")
            return []

    def export_tasks_data(self, project_id: Optional[int] = None) -> pd.DataFrame:
        """Export tasks data to DataFrame"""
        try:
            base_query = """
                SELECT 
                    t.TaskID as 'รหัสงาน',
                    t.TaskTitle as 'ชื่องาน',
                    t.TaskDescription as 'รายละเอียด',
                    p.ProjectName as 'โครงการ',
                    t.Status as 'สถานะ',
                    t.Priority as 'ความสำคัญ',
                    assigned.FullName as 'ผู้รับผิดชอบ',
                    t.DueDate as 'กำหนดส่ง',
                    t.EstimatedHours as 'ชั่วโมงประมาณ',
                    t.ActualHours as 'ชั่วโมงจริง',
                    t.Progress as 'ความคืบหน้า (%)',
                    creator.FullName as 'ผู้สร้าง',
                    t.CreatedDate as 'วันที่สร้าง'
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users assigned ON t.AssignedTo = assigned.UserID
                LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
            """

            params = None
            if project_id:
                base_query += " WHERE t.ProjectID = ?"
                params = (project_id,)

            base_query += " ORDER BY t.CreatedDate DESC"

            data = self.db.execute_query(base_query, params)
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error exporting tasks: {e}")
            return pd.DataFrame()

    def get_task_completion_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get task completion trend for analytics"""
        try:
            query = """
                SELECT 
                    CAST(LastModifiedDate as DATE) as CompletionDate,
                    COUNT(*) as TasksCompleted
                FROM Tasks
                WHERE Status = 'Done' 
                AND LastModifiedDate >= DATEADD(day, -?, GETDATE())
                GROUP BY CAST(LastModifiedDate as DATE)
                ORDER BY CompletionDate
            """

            return self.db.execute_query(query, (days,))

        except Exception as e:
            logger.error(f"Error getting completion trend: {e}")
            return []

    def get_workload_by_user(self) -> List[Dict[str, Any]]:
        """Get workload distribution by user"""
        try:
            query = """
                SELECT 
                    u.FullName as UserName,
                    COUNT(t.TaskID) as TotalTasks,
                    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
                    SUM(CASE WHEN t.Status != 'Done' THEN 1 ELSE 0 END) as ActiveTasks,
                    SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as OverdueTasks
                FROM Users u
                LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
                WHERE u.IsActive = 1
                GROUP BY u.UserID, u.FullName
                ORDER BY TotalTasks DESC
            """

            return self.db.execute_query(query)

        except Exception as e:
            logger.error(f"Error getting workload data: {e}")
            return []
