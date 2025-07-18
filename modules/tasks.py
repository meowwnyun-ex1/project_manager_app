#!/usr/bin/env python3
"""
modules/tasks.py
SDX Project Manager - Complete Enterprise Task Management System
Full-featured task tracking with Kanban, dependencies, time tracking, and comprehensive analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration with workflow support"""

    BACKLOG = "Backlog"
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    TESTING = "Testing"
    DONE = "Done"
    BLOCKED = "Blocked"
    CANCELLED = "Cancelled"


class TaskPriority(Enum):
    """Task priority levels with numeric values for sorting"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TaskType(Enum):
    """Task type classification for better organization"""

    FEATURE = "Feature"
    BUG = "Bug"
    IMPROVEMENT = "Improvement"
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    SUBTASK = "Subtask"
    SPIKE = "Spike"


class WorkType(Enum):
    """Work type for time tracking"""

    DEVELOPMENT = "Development"
    TESTING = "Testing"
    DESIGN = "Design"
    DOCUMENTATION = "Documentation"
    REVIEW = "Review"
    MEETING = "Meeting"
    RESEARCH = "Research"
    DEPLOYMENT = "Deployment"


@dataclass
class TaskMetrics:
    """Comprehensive task performance metrics"""

    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    blocked_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0
    average_completion_time: float = 0.0
    total_estimated_hours: float = 0.0
    total_actual_hours: float = 0.0
    efficiency_ratio: float = 0.0
    velocity_points: int = 0
    burndown_remaining: float = 0.0


@dataclass
class TaskDependency:
    """Task dependency with relationship details"""

    task_id: int
    depends_on_task_id: int
    dependency_type: str
    lag_days: int = 0
    is_hard_dependency: bool = True
    created_at: datetime = None
    created_by: int = None


@dataclass
class TimeEntry:
    """Time tracking entry with comprehensive details"""

    task_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    description: str
    work_type: str
    billable: bool = True
    date_logged: datetime = None


class TaskManager:
    """Comprehensive Enterprise Task Management System"""

    def __init__(self, db_manager):
        self.db = db_manager

        # Task workflow definitions
        self.status_transitions = {
            TaskStatus.BACKLOG.value: [TaskStatus.TODO.value],
            TaskStatus.TODO.value: [
                TaskStatus.IN_PROGRESS.value,
                TaskStatus.BLOCKED.value,
            ],
            TaskStatus.IN_PROGRESS.value: [
                TaskStatus.REVIEW.value,
                TaskStatus.TESTING.value,
                TaskStatus.BLOCKED.value,
                TaskStatus.DONE.value,
            ],
            TaskStatus.REVIEW.value: [
                TaskStatus.IN_PROGRESS.value,
                TaskStatus.TESTING.value,
                TaskStatus.DONE.value,
            ],
            TaskStatus.TESTING.value: [
                TaskStatus.IN_PROGRESS.value,
                TaskStatus.DONE.value,
                TaskStatus.BLOCKED.value,
            ],
            TaskStatus.BLOCKED.value: [
                TaskStatus.TODO.value,
                TaskStatus.IN_PROGRESS.value,
            ],
            TaskStatus.DONE.value: [TaskStatus.IN_PROGRESS.value],  # For reopening
            TaskStatus.CANCELLED.value: [],
        }

        # Priority weights for sorting
        self.priority_weights = {
            TaskPriority.CRITICAL.value: 4,
            TaskPriority.HIGH.value: 3,
            TaskPriority.MEDIUM.value: 2,
            TaskPriority.LOW.value: 1,
        }

    # =============================================================================
    # Core Task CRUD Operations
    # =============================================================================

    def create_task(self, task_data: Dict[str, Any], created_by: int) -> Dict[str, Any]:
        """Create new task with comprehensive validation"""
        try:
            # Validate required fields
            required_fields = ["Title", "ProjectID"]
            for field in required_fields:
                if field not in task_data or not task_data[field]:
                    raise ValueError(f"Required field missing: {field}")

            # Set defaults
            task_data.update(
                {
                    "Status": task_data.get("Status", TaskStatus.TODO.value),
                    "Priority": task_data.get("Priority", TaskPriority.MEDIUM.value),
                    "Type": task_data.get("Type", TaskType.TASK.value),
                    "EstimatedHours": task_data.get("EstimatedHours", 0),
                    "ActualHours": task_data.get("ActualHours", 0),
                    "CompletionPercentage": task_data.get("CompletionPercentage", 0),
                    "CreatedBy": created_by,
                    "CreatedAt": datetime.now(),
                    "UpdatedAt": datetime.now(),
                }
            )

            # Generate task ID if not provided
            if "TaskCode" not in task_data:
                task_data["TaskCode"] = self._generate_task_code(task_data["ProjectID"])

            # Validate business rules
            self._validate_task_business_rules(task_data)

            # Insert task
            query = """
                INSERT INTO Tasks (
                    TaskCode, Title, Description, ProjectID, AssignedTo, Status, 
                    Priority, Type, EstimatedHours, DueDate, MilestoneID,
                    Tags, CompletionPercentage, CreatedBy, CreatedAt, UpdatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = [
                task_data["TaskCode"],
                task_data["Title"],
                task_data.get("Description", ""),
                task_data["ProjectID"],
                task_data.get("AssignedTo"),
                task_data["Status"],
                task_data["Priority"],
                task_data["Type"],
                task_data["EstimatedHours"],
                task_data.get("DueDate"),
                task_data.get("MilestoneID"),
                task_data.get("Tags", ""),
                task_data["CompletionPercentage"],
                task_data["CreatedBy"],
                task_data["CreatedAt"],
                task_data["UpdatedAt"],
            ]

            task_id = self.db.execute_query(query, params, return_id=True)

            # Handle dependencies if provided
            if task_data.get("Dependencies"):
                self._create_task_dependencies(
                    task_id, task_data["Dependencies"], created_by
                )

            # Log activity
            self._log_task_activity(
                task_id,
                created_by,
                "TASK_CREATED",
                f"Task '{task_data['Title']}' created",
            )

            return self.get_task_by_id(task_id)

        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise

    def get_task_by_id(
        self, task_id: int, include_details: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get task with comprehensive details"""
        try:
            query = """
                SELECT t.*, 
                       p.Name as ProjectName,
                       a.FirstName + ' ' + a.LastName as AssignedToName,
                       c.FirstName + ' ' + c.LastName as CreatedByName,
                       m.Name as MilestoneName
                FROM Tasks t
                LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                LEFT JOIN Users a ON t.AssignedTo = a.UserID
                LEFT JOIN Users c ON t.CreatedBy = c.UserID
                LEFT JOIN ProjectMilestones m ON t.MilestoneID = m.MilestoneID
                WHERE t.TaskID = ?
            """

            result = self.db.fetch_one(query, [task_id])
            if not result:
                return None

            task = dict(result)

            if include_details:
                # Add comprehensive details
                task["Dependencies"] = self.get_task_dependencies(task_id)
                task["Subtasks"] = self.get_task_subtasks(task_id)
                task["TimeEntries"] = self.get_task_time_entries(task_id)
                task["Comments"] = self.get_task_comments(task_id)
                task["Attachments"] = self.get_task_attachments(task_id)
                task["ActivityLog"] = self.get_task_activity(task_id, limit=10)

                # Calculate derived metrics
                task["TimeSpent"] = self._calculate_time_spent(task_id)
                task["ProgressStatus"] = self._calculate_task_progress_status(task)
                task["IsOverdue"] = self._is_task_overdue(task)
                task["CanTransitionTo"] = self._get_allowed_status_transitions(
                    task["Status"]
                )

            return task

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {str(e)}")
            return None

    def update_task(
        self, task_id: int, updates: Dict[str, Any], updated_by: int
    ) -> bool:
        """Update task with validation and audit trail"""
        try:
            # Get current task for comparison
            current_task = self.get_task_by_id(task_id, include_details=False)
            if not current_task:
                raise ValueError(f"Task {task_id} not found")

            # Validate status transitions
            if "Status" in updates:
                self._validate_status_transition(
                    current_task["Status"], updates["Status"]
                )

            # Build update query dynamically
            set_clauses = []
            params = []

            allowed_fields = [
                "Title",
                "Description",
                "AssignedTo",
                "Status",
                "Priority",
                "Type",
                "EstimatedHours",
                "ActualHours",
                "DueDate",
                "MilestoneID",
                "Tags",
                "CompletionPercentage",
            ]

            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)

            if not set_clauses:
                return False

            # Auto-update completion percentage based on status
            if "Status" in updates and "CompletionPercentage" not in updates:
                completion = self._get_status_completion_percentage(updates["Status"])
                set_clauses.append("CompletionPercentage = ?")
                params.append(completion)
                updates["CompletionPercentage"] = completion

            # Add audit fields
            set_clauses.extend(["UpdatedBy = ?", "UpdatedAt = ?"])
            params.extend([updated_by, datetime.now()])
            params.append(task_id)

            query = f"UPDATE Tasks SET {', '.join(set_clauses)} WHERE TaskID = ?"

            self.db.execute_query(query, params)

            # Handle status-specific actions
            self._handle_status_change_actions(
                task_id, current_task["Status"], updates.get("Status"), updated_by
            )

            # Log changes
            self._log_task_changes(task_id, current_task, updates, updated_by)

            # Update project progress if needed
            self._update_project_progress(current_task["ProjectID"])

            return True

        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {str(e)}")
            return False

    def delete_task(self, task_id: int, deleted_by: int) -> bool:
        """Delete task with dependency validation"""
        try:
            # Check for dependencies
            dependents = self.get_tasks_depending_on(task_id)
            if dependents:
                raise ValueError(
                    f"Cannot delete task: {len(dependents)} tasks depend on it"
                )

            # Soft delete
            query = """
                UPDATE Tasks 
                SET Status = 'Cancelled',
                    UpdatedBy = ?, 
                    UpdatedAt = ?,
                    DeletedAt = ?
                WHERE TaskID = ?
            """

            self.db.execute_query(
                query, [deleted_by, datetime.now(), datetime.now(), task_id]
            )

            # Archive related data
            self._archive_task_data(task_id)

            # Log activity
            self._log_task_activity(
                task_id, deleted_by, "TASK_DELETED", "Task deleted and archived"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {str(e)}")
            return False

    # =============================================================================
    # Kanban Board Operations
    # =============================================================================

    def get_kanban_board(
        self, project_id: int, filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get Kanban board with tasks organized by status columns"""
        try:
            # Build WHERE clause
            where_conditions = ["t.ProjectID = ?", "t.Status != 'Cancelled'"]
            params = [project_id]

            if filters:
                if filters.get("assigned_to"):
                    where_conditions.append("t.AssignedTo = ?")
                    params.append(filters["assigned_to"])

                if filters.get("priority"):
                    where_conditions.append("t.Priority = ?")
                    params.append(filters["priority"])

                if filters.get("milestone"):
                    where_conditions.append("t.MilestoneID = ?")
                    params.append(filters["milestone"])

                if filters.get("tags"):
                    where_conditions.append("t.Tags LIKE ?")
                    params.append(f"%{filters['tags']}%")

            where_clause = "WHERE " + " AND ".join(where_conditions)

            # Get tasks with details
            query = f"""
                SELECT t.TaskID, t.TaskCode, t.Title, t.Description, t.Status,
                       t.Priority, t.Type, t.EstimatedHours, t.ActualHours,
                       t.CompletionPercentage, t.DueDate, t.Tags,
                       a.FirstName + ' ' + a.LastName as AssignedToName,
                       a.UserID as AssignedToID,
                       m.Name as MilestoneName,
                       (SELECT COUNT(*) FROM Tasks st WHERE st.ParentTaskID = t.TaskID) as SubtaskCount,
                       (SELECT COUNT(*) FROM TaskComments tc WHERE tc.TaskID = t.TaskID) as CommentCount
                FROM Tasks t
                LEFT JOIN Users a ON t.AssignedTo = a.UserID
                LEFT JOIN ProjectMilestones m ON t.MilestoneID = m.MilestoneID
                {where_clause}
                ORDER BY 
                    CASE t.Priority 
                        WHEN 'Critical' THEN 4
                        WHEN 'High' THEN 3
                        WHEN 'Medium' THEN 2
                        WHEN 'Low' THEN 1
                    END DESC,
                    t.DueDate ASC,
                    t.CreatedAt ASC
            """

            tasks = self.db.fetch_all(query, params)

            # Organize tasks by status columns
            board = {"columns": {}, "task_counts": {}, "metrics": {}}

            # Initialize columns
            for status in TaskStatus:
                board["columns"][status.value] = []
                board["task_counts"][status.value] = 0

            # Organize tasks into columns
            for task in tasks:
                task_dict = dict(task)
                task_dict["IsOverdue"] = self._is_task_overdue(task_dict)
                task_dict["PriorityWeight"] = self.priority_weights.get(
                    task_dict["Priority"], 1
                )

                status = task_dict["Status"]
                board["columns"][status].append(task_dict)
                board["task_counts"][status] += 1

            # Calculate board metrics
            board["metrics"] = self._calculate_board_metrics(tasks)

            return board

        except Exception as e:
            logger.error(f"Failed to get Kanban board: {str(e)}")
            return {"columns": {}, "task_counts": {}, "metrics": {}}

    def move_task_to_column(self, task_id: int, new_status: str, moved_by: int) -> bool:
        """Move task to different Kanban column with validation"""
        try:
            # Get current task
            task = self.get_task_by_id(task_id, include_details=False)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # Validate transition
            self._validate_status_transition(task["Status"], new_status)

            # Update task status
            return self.update_task(task_id, {"Status": new_status}, moved_by)

        except Exception as e:
            logger.error(f"Failed to move task to column: {str(e)}")
            return False

    # =============================================================================
    # Task Dependencies
    # =============================================================================

    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get tasks that this task depends on"""
        try:
            query = """
                SELECT td.*, t.Title as DependsOnTitle, t.Status as DependsOnStatus
                FROM TaskDependencies td
                JOIN Tasks t ON td.DependsOnTaskID = t.TaskID
                WHERE td.TaskID = ?
                ORDER BY td.CreatedAt
            """

            dependencies = self.db.fetch_all(query, [task_id])
            return [dict(dep) for dep in dependencies]

        except Exception as e:
            logger.error(f"Failed to get task dependencies: {str(e)}")
            return []

    def get_tasks_depending_on(self, task_id: int) -> List[Dict[str, Any]]:
        """Get tasks that depend on this task"""
        try:
            query = """
                SELECT td.*, t.Title, t.Status
                FROM TaskDependencies td
                JOIN Tasks t ON td.TaskID = t.TaskID
                WHERE td.DependsOnTaskID = ?
                ORDER BY td.CreatedAt
            """

            dependents = self.db.fetch_all(query, [task_id])
            return [dict(dep) for dep in dependents]

        except Exception as e:
            logger.error(f"Failed to get dependent tasks: {str(e)}")
            return []

    def add_task_dependency(
        self,
        task_id: int,
        depends_on_task_id: int,
        dependency_type: str = "finish_to_start",
        lag_days: int = 0,
        created_by: int = None,
    ) -> bool:
        """Add dependency between tasks"""
        try:
            # Validate no circular dependencies
            if self._creates_circular_dependency(task_id, depends_on_task_id):
                raise ValueError("This dependency would create a circular reference")

            # Check if dependency already exists
            existing = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM TaskDependencies WHERE TaskID = ? AND DependsOnTaskID = ?",
                [task_id, depends_on_task_id],
            )

            if existing["count"] > 0:
                return False  # Already exists

            query = """
                INSERT INTO TaskDependencies 
                (TaskID, DependsOnTaskID, DependencyType, LagDays, CreatedBy, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                [
                    task_id,
                    depends_on_task_id,
                    dependency_type,
                    lag_days,
                    created_by,
                    datetime.now(),
                ],
            )

            # Log activity
            self._log_task_activity(
                task_id,
                created_by,
                "DEPENDENCY_ADDED",
                f"Added dependency on task {depends_on_task_id}",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to add task dependency: {str(e)}")
            return False

    def remove_task_dependency(
        self, task_id: int, depends_on_task_id: int, removed_by: int
    ) -> bool:
        """Remove dependency between tasks"""
        try:
            query = (
                "DELETE FROM TaskDependencies WHERE TaskID = ? AND DependsOnTaskID = ?"
            )

            self.db.execute_query(query, [task_id, depends_on_task_id])

            # Log activity
            self._log_task_activity(
                task_id,
                removed_by,
                "DEPENDENCY_REMOVED",
                f"Removed dependency on task {depends_on_task_id}",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to remove task dependency: {str(e)}")
            return False

    # =============================================================================
    # Time Tracking
    # =============================================================================

    def start_time_tracking(
        self,
        task_id: int,
        user_id: int,
        description: str = "",
        work_type: str = WorkType.DEVELOPMENT.value,
    ) -> int:
        """Start time tracking for a task"""
        try:
            # Stop any active time tracking for this user
            self.stop_active_time_tracking(user_id)

            query = """
                INSERT INTO TimeTracking 
                (TaskID, UserID, StartTime, Description, WorkType, Status)
                VALUES (?, ?, ?, ?, ?, 'Active')
            """

            tracking_id = self.db.execute_query(
                query,
                [task_id, user_id, datetime.now(), description, work_type],
                return_id=True,
            )

            # Update task status if not already in progress
            task = self.get_task_by_id(task_id, include_details=False)
            if task and task["Status"] == TaskStatus.TODO.value:
                self.update_task(
                    task_id, {"Status": TaskStatus.IN_PROGRESS.value}, user_id
                )

            return tracking_id

        except Exception as e:
            logger.error(f"Failed to start time tracking: {str(e)}")
            raise

    def stop_time_tracking(self, tracking_id: int, user_id: int) -> bool:
        """Stop specific time tracking session"""
        try:
            # Get current tracking session
            tracking = self.db.fetch_one(
                "SELECT * FROM TimeTracking WHERE TrackingID = ? AND UserID = ? AND Status = 'Active'",
                [tracking_id, user_id],
            )

            if not tracking:
                return False

            end_time = datetime.now()
            start_time = tracking["StartTime"]
            duration_minutes = int((end_time - start_time).total_seconds() / 60)

            # Update tracking record
            query = """
                UPDATE TimeTracking 
                SET EndTime = ?, DurationMinutes = ?, Status = 'Completed'
                WHERE TrackingID = ?
            """

            self.db.execute_query(query, [end_time, duration_minutes, tracking_id])

            # Update task actual hours
            self._update_task_actual_hours(tracking["TaskID"])

            return True

        except Exception as e:
            logger.error(f"Failed to stop time tracking: {str(e)}")
            return False

    def stop_active_time_tracking(self, user_id: int) -> bool:
        """Stop all active time tracking for user"""
        try:
            # Get active tracking sessions
            active_sessions = self.db.fetch_all(
                "SELECT TrackingID FROM TimeTracking WHERE UserID = ? AND Status = 'Active'",
                [user_id],
            )

            for session in active_sessions:
                self.stop_time_tracking(session["TrackingID"], user_id)

            return True

        except Exception as e:
            logger.error(f"Failed to stop active time tracking: {str(e)}")
            return False

    def get_task_time_entries(self, task_id: int) -> List[Dict[str, Any]]:
        """Get time tracking entries for a task"""
        try:
            query = """
                SELECT tt.*, u.FirstName + ' ' + u.LastName as UserName
                FROM TimeTracking tt
                JOIN Users u ON tt.UserID = u.UserID
                WHERE tt.TaskID = ?
                ORDER BY tt.StartTime DESC
            """

            entries = self.db.fetch_all(query, [task_id])
            return [dict(entry) for entry in entries]

        except Exception as e:
            logger.error(f"Failed to get time entries: {str(e)}")
            return []

    # =============================================================================
    # Task Comments and Collaboration
    # =============================================================================

    def add_task_comment(
        self, task_id: int, comment: str, user_id: int, comment_type: str = "comment"
    ) -> int:
        """Add comment to task"""
        try:
            query = """
                INSERT INTO TaskComments 
                (TaskID, UserID, Comment, CommentType, CreatedAt)
                VALUES (?, ?, ?, ?, ?)
            """

            comment_id = self.db.execute_query(
                query,
                [task_id, user_id, comment, comment_type, datetime.now()],
                return_id=True,
            )

            # Log activity
            self._log_task_activity(
                task_id, user_id, "COMMENT_ADDED", f"Added comment: {comment[:50]}..."
            )

            return comment_id

        except Exception as e:
            logger.error(f"Failed to add task comment: {str(e)}")
            raise

    def get_task_comments(self, task_id: int) -> List[Dict[str, Any]]:
        """Get task comments with user details"""
        try:
            query = """
                SELECT tc.*, u.FirstName + ' ' + u.LastName as UserName
                FROM TaskComments tc
                JOIN Users u ON tc.UserID = u.UserID
                WHERE tc.TaskID = ?
                ORDER BY tc.CreatedAt ASC
            """

            comments = self.db.fetch_all(query, [task_id])
            return [dict(comment) for comment in comments]

        except Exception as e:
            logger.error(f"Failed to get task comments: {str(e)}")
            return []

    # =============================================================================
    # Task Analytics and Reporting
    # =============================================================================

    def get_task_metrics(
        self,
        project_id: int = None,
        user_id: int = None,
        date_range: Tuple[datetime, datetime] = None,
    ) -> TaskMetrics:
        """Get comprehensive task metrics"""
        try:
            metrics = TaskMetrics()

            # Build WHERE clause
            where_conditions = ["t.Status != 'Cancelled'"]
            params = []

            if project_id:
                where_conditions.append("t.ProjectID = ?")
                params.append(project_id)

            if user_id:
                where_conditions.append("t.AssignedTo = ?")
                params.append(user_id)

            if date_range:
                where_conditions.append("t.CreatedAt BETWEEN ? AND ?")
                params.extend(date_range)

            where_clause = "WHERE " + " AND ".join(where_conditions)

            # Get basic task counts
            query = f"""
                SELECT 
                    COUNT(*) as TotalTasks,
                    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
                    SUM(CASE WHEN t.Status IN ('In Progress', 'Review', 'Testing') THEN 1 ELSE 0 END) as InProgressTasks,
                    SUM(CASE WHEN t.Status = 'Blocked' THEN 1 ELSE 0 END) as BlockedTasks,
                    SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as OverdueTasks,
                    SUM(COALESCE(t.EstimatedHours, 0)) as TotalEstimatedHours,
                    SUM(COALESCE(t.ActualHours, 0)) as TotalActualHours,
                    AVG(CASE WHEN t.Status = 'Done' AND t.CompletedAt IS NOT NULL 
                             THEN DATEDIFF(day, t.CreatedAt, t.CompletedAt) END) as AvgCompletionDays
                FROM Tasks t
                {where_clause}
            """

            result = self.db.fetch_one(query, params)

            if result:
                metrics.total_tasks = result["TotalTasks"]
                metrics.completed_tasks = result["CompletedTasks"]
                metrics.in_progress_tasks = result["InProgressTasks"]
                metrics.blocked_tasks = result["BlockedTasks"]
                metrics.overdue_tasks = result["OverdueTasks"]
                metrics.total_estimated_hours = result["TotalEstimatedHours"]
                metrics.total_actual_hours = result["TotalActualHours"]
                metrics.average_completion_time = result["AvgCompletionDays"] or 0.0

                # Calculate derived metrics
                if metrics.total_tasks > 0:
                    metrics.completion_rate = (
                        metrics.completed_tasks / metrics.total_tasks
                    ) * 100

                if metrics.total_estimated_hours > 0:
                    metrics.efficiency_ratio = (
                        metrics.total_actual_hours / metrics.total_estimated_hours
                    )

            # Calculate velocity and burndown
            if project_id:
                metrics.velocity_points = self._calculate_project_velocity(project_id)
                metrics.burndown_remaining = self._calculate_burndown_remaining(
                    project_id
                )

            return metrics

        except Exception as e:
            logger.error(f"Failed to get task metrics: {str(e)}")
            return TaskMetrics()

    def get_burndown_chart_data(
        self, project_id: int, sprint_days: int = 14
    ) -> Dict[str, Any]:
        """Get burndown chart data for project"""
        try:
            # Get project start date and calculate sprint dates
            project = self.db.fetch_one(
                "SELECT StartDate FROM Projects WHERE ProjectID = ?", [project_id]
            )
            if not project:
                return {}

            start_date = datetime.strptime(project["StartDate"], "%Y-%m-%d").date()
            end_date = start_date + timedelta(days=sprint_days)

            # Get total estimated hours
            total_hours = (
                self.db.fetch_one(
                    "SELECT SUM(EstimatedHours) as total FROM Tasks WHERE ProjectID = ? AND Status != 'Cancelled'",
                    [project_id],
                )["total"]
                or 0
            )

            # Calculate daily remaining hours
            chart_data = {
                "dates": [],
                "ideal_remaining": [],
                "actual_remaining": [],
                "completed_hours": [],
            }

            current_date = start_date
            daily_burn = total_hours / sprint_days if sprint_days > 0 else 0

            while current_date <= min(end_date, datetime.now().date()):
                # Ideal burndown
                days_elapsed = (current_date - start_date).days
                ideal_remaining = max(0, total_hours - (daily_burn * days_elapsed))

                # Actual completed hours up to this date
                completed_query = """
                    SELECT SUM(EstimatedHours) as completed
                    FROM Tasks 
                    WHERE ProjectID = ? AND Status = 'Done' 
                    AND CompletedAt <= ?
                """
                completed_result = self.db.fetch_one(
                    completed_query, [project_id, current_date]
                )
                completed_hours = completed_result["completed"] or 0
                actual_remaining = max(0, total_hours - completed_hours)

                chart_data["dates"].append(current_date.isoformat())
                chart_data["ideal_remaining"].append(ideal_remaining)
                chart_data["actual_remaining"].append(actual_remaining)
                chart_data["completed_hours"].append(completed_hours)

                current_date += timedelta(days=1)

            return chart_data

        except Exception as e:
            logger.error(f"Failed to get burndown chart data: {str(e)}")
            return {}

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _generate_task_code(self, project_id: int) -> str:
        """Generate unique task code"""
        try:
            # Get project code
            project = self.db.fetch_one(
                "SELECT ProjectCode FROM Projects WHERE ProjectID = ?", [project_id]
            )
            project_code = (
                project["ProjectCode"][:8] if project else f"PROJ{project_id}"
            )

            # Get next sequence number
            query = """
                SELECT COUNT(*) + 1 as NextNum
                FROM Tasks 
                WHERE ProjectID = ?
            """
            result = self.db.fetch_one(query, [project_id])
            next_num = result["NextNum"] if result else 1

            return f"{project_code}-T{next_num:04d}"

        except Exception as e:
            logger.error(f"Failed to generate task code: {str(e)}")
            return f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _validate_task_business_rules(self, task_data: Dict[str, Any]):
        """Validate task business rules"""
        # Due date validation
        if task_data.get("DueDate"):
            due_date = datetime.strptime(task_data["DueDate"], "%Y-%m-%d").date()
            if due_date < datetime.now().date():
                raise ValueError("Due date cannot be in the past")

        # Estimated hours validation
        if task_data.get("EstimatedHours", 0) < 0:
            raise ValueError("Estimated hours cannot be negative")

        # Assignment validation
        if task_data.get("AssignedTo"):
            # Check if user exists and is active
            user = self.db.fetch_one(
                "SELECT Status FROM Users WHERE UserID = ?", [task_data["AssignedTo"]]
            )
            if not user or user["Status"] != "Active":
                raise ValueError("Cannot assign task to inactive user")

    def _validate_status_transition(self, current_status: str, new_status: str):
        """Validate if status transition is allowed"""
        if current_status == new_status:
            return  # No change

        allowed_transitions = self.status_transitions.get(current_status, [])
        if new_status not in allowed_transitions:
            raise ValueError(
                f"Invalid status transition from {current_status} to {new_status}"
            )

    def _get_allowed_status_transitions(self, current_status: str) -> List[str]:
        """Get allowed status transitions for current status"""
        return self.status_transitions.get(current_status, [])

    def _get_status_completion_percentage(self, status: str) -> int:
        """Get default completion percentage for status"""
        status_percentages = {
            TaskStatus.BACKLOG.value: 0,
            TaskStatus.TODO.value: 0,
            TaskStatus.IN_PROGRESS.value: 25,
            TaskStatus.REVIEW.value: 75,
            TaskStatus.TESTING.value: 90,
            TaskStatus.DONE.value: 100,
            TaskStatus.BLOCKED.value: -1,  # Keep current percentage
            TaskStatus.CANCELLED.value: 0,
        }
        return status_percentages.get(status, 0)

    def _handle_status_change_actions(
        self, task_id: int, old_status: str, new_status: str, user_id: int
    ):
        """Handle actions when task status changes"""
        if not new_status or old_status == new_status:
            return

        # Completion actions
        if new_status == TaskStatus.DONE.value:
            self.db.execute_query(
                "UPDATE Tasks SET CompletedAt = ?, CompletedBy = ? WHERE TaskID = ?",
                [datetime.now(), user_id, task_id],
            )

            # Stop any active time tracking
            self.stop_active_time_tracking_for_task(task_id)

        # In progress actions
        elif (
            new_status == TaskStatus.IN_PROGRESS.value
            and old_status == TaskStatus.TODO.value
        ):
            self.db.execute_query(
                "UPDATE Tasks SET StartedAt = ?, StartedBy = ? WHERE TaskID = ?",
                [datetime.now(), user_id, task_id],
            )

    def _calculate_time_spent(self, task_id: int) -> float:
        """Calculate total time spent on task in hours"""
        try:
            result = self.db.fetch_one(
                "SELECT SUM(DurationMinutes) as total FROM TimeTracking WHERE TaskID = ?",
                [task_id],
            )
            total_minutes = result["total"] or 0
            return total_minutes / 60.0
        except Exception:
            return 0.0

    def _calculate_task_progress_status(self, task: Dict[str, Any]) -> str:
        """Calculate task progress status"""
        if task["Status"] == TaskStatus.DONE.value:
            return "Completed"
        elif task["Status"] == TaskStatus.BLOCKED.value:
            return "Blocked"
        elif self._is_task_overdue(task):
            return "Overdue"
        elif task["Status"] == TaskStatus.IN_PROGRESS.value:
            return "In Progress"
        else:
            return "Pending"

    def _is_task_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if task is overdue"""
        if not task.get("DueDate") or task["Status"] == TaskStatus.DONE.value:
            return False

        try:
            due_date = datetime.strptime(task["DueDate"], "%Y-%m-%d").date()
            return datetime.now().date() > due_date
        except Exception:
            return False

    def _calculate_board_metrics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Kanban board metrics"""
        metrics = {
            "total_tasks": len(tasks),
            "completion_rate": 0,
            "average_cycle_time": 0,
            "blocked_tasks": 0,
            "overdue_tasks": 0,
        }

        completed_tasks = sum(
            1 for task in tasks if task["Status"] == TaskStatus.DONE.value
        )
        if metrics["total_tasks"] > 0:
            metrics["completion_rate"] = (
                completed_tasks / metrics["total_tasks"]
            ) * 100

        metrics["blocked_tasks"] = sum(
            1 for task in tasks if task["Status"] == TaskStatus.BLOCKED.value
        )
        metrics["overdue_tasks"] = sum(
            1 for task in tasks if self._is_task_overdue(dict(task))
        )

        return metrics

    def _update_task_actual_hours(self, task_id: int):
        """Update task actual hours from time tracking"""
        try:
            result = self.db.fetch_one(
                "SELECT SUM(DurationMinutes) as total FROM TimeTracking WHERE TaskID = ?",
                [task_id],
            )
            total_minutes = result["total"] or 0
            actual_hours = total_minutes / 60.0

            self.db.execute_query(
                "UPDATE Tasks SET ActualHours = ? WHERE TaskID = ?",
                [actual_hours, task_id],
            )

        except Exception as e:
            logger.error(f"Failed to update task actual hours: {str(e)}")

    def _update_project_progress(self, project_id: int):
        """Update project progress based on task completion"""
        try:
            # Calculate project completion percentage
            result = self.db.fetch_one(
                """
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks
                FROM Tasks 
                WHERE ProjectID = ? AND Status != 'Cancelled'
            """,
                [project_id],
            )

            if result and result["total_tasks"] > 0:
                completion_percentage = (
                    result["completed_tasks"] / result["total_tasks"]
                ) * 100

                self.db.execute_query(
                    "UPDATE Projects SET CompletionPercentage = ? WHERE ProjectID = ?",
                    [completion_percentage, project_id],
                )

        except Exception as e:
            logger.error(f"Failed to update project progress: {str(e)}")

    def _creates_circular_dependency(
        self, task_id: int, depends_on_task_id: int
    ) -> bool:
        """Check if adding dependency would create circular reference"""
        try:
            # Use recursive CTE to check for circular dependencies
            query = """
                WITH DependencyChain AS (
                    SELECT DependsOnTaskID as TaskID, 1 as Level
                    FROM TaskDependencies
                    WHERE TaskID = ?
                    
                    UNION ALL
                    
                    SELECT td.DependsOnTaskID, dc.Level + 1
                    FROM TaskDependencies td
                    JOIN DependencyChain dc ON td.TaskID = dc.TaskID
                    WHERE dc.Level < 10  -- Prevent infinite recursion
                )
                SELECT COUNT(*) as count
                FROM DependencyChain
                WHERE TaskID = ?
            """

            result = self.db.fetch_one(query, [depends_on_task_id, task_id])
            return result["count"] > 0

        except Exception as e:
            logger.error(f"Failed to check circular dependency: {str(e)}")
            return True  # Err on the side of caution

    def _archive_task_data(self, task_id: int):
        """Archive task-related data"""
        try:
            # Archive time tracking
            self.db.execute_query(
                "UPDATE TimeTracking SET Status = 'Archived' WHERE TaskID = ?",
                [task_id],
            )

            # Archive comments
            self.db.execute_query(
                "UPDATE TaskComments SET IsArchived = 1 WHERE TaskID = ?", [task_id]
            )

        except Exception as e:
            logger.error(f"Failed to archive task data: {str(e)}")

    def _log_task_activity(
        self, task_id: int, user_id: int, activity_type: str, description: str
    ):
        """Log task activity for audit trail"""
        try:
            query = """
                INSERT INTO TaskActivity 
                (TaskID, UserID, ActivityType, Description, ActivityDate)
                VALUES (?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query, [task_id, user_id, activity_type, description, datetime.now()]
            )

        except Exception as e:
            logger.error(f"Failed to log task activity: {str(e)}")

    def _log_task_changes(
        self, task_id: int, old_data: Dict, new_data: Dict, changed_by: int
    ):
        """Log detailed task changes"""
        try:
            changes = []
            for field, new_value in new_data.items():
                old_value = old_data.get(field)
                if old_value != new_value:
                    changes.append(f"{field}: '{old_value}' → '{new_value}'")

            if changes:
                description = f"Updated: {', '.join(changes)}"
                self._log_task_activity(
                    task_id, changed_by, "TASK_UPDATED", description
                )

        except Exception as e:
            logger.error(f"Failed to log task changes: {str(e)}")

    def get_task_activity(self, task_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task activity log"""
        try:
            query = """
                SELECT ta.*, u.FirstName + ' ' + u.LastName as UserName
                FROM TaskActivity ta
                LEFT JOIN Users u ON ta.UserID = u.UserID
                WHERE ta.TaskID = ?
                ORDER BY ta.ActivityDate DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """

            activities = self.db.fetch_all(query, [task_id, limit])
            return [dict(activity) for activity in activities]

        except Exception as e:
            logger.error(f"Failed to get task activity: {str(e)}")
            return []

    def get_task_subtasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get subtasks for a parent task"""
        try:
            query = """
                SELECT TaskID, TaskCode, Title, Status, Priority, 
                       AssignedTo, CompletionPercentage, DueDate
                FROM Tasks 
                WHERE ParentTaskID = ? AND Status != 'Cancelled'
                ORDER BY Priority DESC, CreatedAt ASC
            """

            subtasks = self.db.fetch_all(query, [task_id])
            return [dict(subtask) for subtask in subtasks]

        except Exception as e:
            logger.error(f"Failed to get subtasks: {str(e)}")
            return []

    def get_task_attachments(self, task_id: int) -> List[Dict[str, Any]]:
        """Get task attachments"""
        try:
            query = """
                SELECT ta.*, u.FirstName + ' ' + u.LastName as UploadedByName
                FROM TaskAttachments ta
                LEFT JOIN Users u ON ta.UploadedBy = u.UserID
                WHERE ta.TaskID = ?
                ORDER BY ta.UploadedAt DESC
            """

            attachments = self.db.fetch_all(query, [task_id])
            return [dict(attachment) for attachment in attachments]

        except Exception as e:
            logger.error(f"Failed to get task attachments: {str(e)}")
            return []

    def stop_active_time_tracking_for_task(self, task_id: int):
        """Stop all active time tracking for a specific task"""
        try:
            active_sessions = self.db.fetch_all(
                "SELECT TrackingID, UserID FROM TimeTracking WHERE TaskID = ? AND Status = 'Active'",
                [task_id],
            )

            for session in active_sessions:
                self.stop_time_tracking(session["TrackingID"], session["UserID"])

        except Exception as e:
            logger.error(f"Failed to stop active time tracking for task: {str(e)}")

    def _calculate_project_velocity(self, project_id: int) -> int:
        """Calculate project velocity in story points"""
        try:
            # Get completed story points in last 2 weeks
            two_weeks_ago = datetime.now() - timedelta(weeks=2)
            result = self.db.fetch_one(
                """
                SELECT SUM(StoryPoints) as velocity
                FROM Tasks 
                WHERE ProjectID = ? AND Status = 'Done' 
                AND CompletedAt >= ?
            """,
                [project_id, two_weeks_ago],
            )

            return result["velocity"] or 0

        except Exception as e:
            logger.error(f"Failed to calculate project velocity: {str(e)}")
            return 0

    def _calculate_burndown_remaining(self, project_id: int) -> float:
        """Calculate remaining work for burndown chart"""
        try:
            result = self.db.fetch_one(
                """
                SELECT SUM(EstimatedHours) as remaining
                FROM Tasks 
                WHERE ProjectID = ? AND Status NOT IN ('Done', 'Cancelled')
            """,
                [project_id],
            )

            return result["remaining"] or 0.0

        except Exception as e:
            logger.error(f"Failed to calculate burndown remaining: {str(e)}")
            return 0.0
