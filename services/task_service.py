# services/task_service.py
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from .enhanced_db_service import (
    get_db_service,
    with_db_transaction,
    cached_query,
    DatabaseException,
)

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""

    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "In Review"
    TESTING = "Testing"
    DONE = "Done"
    CANCELLED = "Cancelled"
    BLOCKED = "Blocked"


class TaskPriority(Enum):
    """Task priority enumeration"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Task:
    """Task data model"""

    task_id: Optional[int] = None
    project_id: int = None
    task_name: str = ""
    description: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    status: str = TaskStatus.TODO.value
    priority: str = TaskPriority.MEDIUM.value
    progress: int = 0
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: Optional[str] = None
    labels: Optional[str] = None
    created_date: Optional[datetime] = None
    created_by: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class TaskService:
    """Enhanced task management service"""

    def __init__(self):
        self.db_service = get_db_service()

    @with_db_transaction
    def create_task(self, task_data: Dict[str, Any], user_id: int) -> int:
        """Create a new task"""
        try:
            # Validate required fields
            required_fields = ["project_id", "task_name"]
            for field in required_fields:
                if field not in task_data or not task_data[field]:
                    raise ValueError(f"Required field '{field}' is missing")

            # Validate project exists
            if not self._project_exists(task_data["project_id"]):
                raise ValueError("Project does not exist")

            # Validate assignee if provided
            if task_data.get("assignee_id") and not self._user_exists(
                task_data["assignee_id"]
            ):
                raise ValueError("Assignee user does not exist")

            # Validate dates
            start_date = task_data.get("start_date")
            end_date = task_data.get("end_date")
            if start_date and end_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(
                        start_date.replace("Z", "+00:00")
                    )
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

                if start_date > end_date:
                    raise ValueError("Start date cannot be after end date")

            # Validate progress
            progress = task_data.get("progress", 0)
            if not (0 <= progress <= 100):
                raise ValueError("Progress must be between 0 and 100")

            # Prepare task data
            task = Task(
                project_id=task_data["project_id"],
                task_name=task_data["task_name"][:100],  # Limit length
                description=task_data.get("description", ""),
                start_date=start_date,
                end_date=end_date,
                assignee_id=task_data.get("assignee_id"),
                status=task_data.get("status", TaskStatus.TODO.value),
                priority=task_data.get("priority", TaskPriority.MEDIUM.value),
                progress=progress,
                estimated_hours=task_data.get("estimated_hours"),
                actual_hours=task_data.get("actual_hours"),
                dependencies=task_data.get("dependencies"),
                labels=task_data.get("labels"),
                created_by=user_id,
            )

            # Insert task
            query = """
            INSERT INTO Tasks (
                ProjectID, TaskName, Description, StartDate, EndDate,
                AssigneeID, Status, Priority, Progress, EstimatedHours,
                ActualHours, Dependencies, Labels, CreatedBy
            )
            OUTPUT INSERTED.TaskID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                task.project_id,
                task.task_name,
                task.description,
                task.start_date,
                task.end_date,
                task.assignee_id,
                task.status,
                task.priority,
                task.progress,
                task.estimated_hours,
                task.actual_hours,
                task.dependencies,
                task.labels,
                task.created_by,
            )

            result = self.db_service.execute_query(query, params)
            task_id = result[0]["TaskID"]

            # Clear cache
            self.db_service.clear_cache("tasks_")

            logger.info(f"Task created successfully: ID {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise DatabaseException(f"Task creation failed: {str(e)}")

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            query = """
            SELECT 
                t.*,
                u.Username as AssigneeName,
                p.ProjectName,
                creator.Username as CreatedByName
            FROM Tasks t
            LEFT JOIN Users u ON t.AssigneeID = u.UserID
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
            WHERE t.TaskID = ?
            """

            result = self.db_service.execute_query(query, (task_id,))

            if result:
                task_data = result[0]
                task_data["time_tracking"] = self._calculate_time_metrics(task_data)
                task_data["dependencies_list"] = self._parse_dependencies(
                    task_data.get("Dependencies")
                )
                task_data["labels_list"] = self._parse_labels(task_data.get("Labels"))
                return task_data

            return None

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {str(e)}")
            raise DatabaseException(f"Task retrieval failed: {str(e)}")

    @cached_query("tasks_by_project", ttl=300)
    def get_tasks_by_project(
        self, project_id: int, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all tasks for a project"""
        try:
            base_query = """
            SELECT 
                t.*,
                u.Username as AssigneeName,
                creator.Username as CreatedByName
            FROM Tasks t
            LEFT JOIN Users u ON t.AssigneeID = u.UserID
            LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
            WHERE t.ProjectID = ?
            """

            params = [project_id]

            if status:
                base_query += " AND t.Status = ?"
                params.append(status)

            base_query += " ORDER BY t.Priority DESC, t.CreatedDate DESC"

            result = self.db_service.execute_query(base_query, tuple(params))

            # Enhance each task with additional data
            for task in result:
                task["time_tracking"] = self._calculate_time_metrics(task)
                task["dependencies_list"] = self._parse_dependencies(
                    task.get("Dependencies")
                )
                task["labels_list"] = self._parse_labels(task.get("Labels"))
                task["overdue"] = self._is_task_overdue(task)

            return result

        except Exception as e:
            logger.error(f"Failed to get tasks for project {project_id}: {str(e)}")
            raise DatabaseException(f"Task retrieval failed: {str(e)}")

    def get_tasks_by_assignee(
        self, assignee_id: int, include_completed: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all tasks assigned to a user"""
        try:
            base_query = """
            SELECT 
                t.*,
                p.ProjectName,
                creator.Username as CreatedByName
            FROM Tasks t
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
            WHERE t.AssigneeID = ?
            """

            params = [assignee_id]

            if not include_completed:
                base_query += " AND t.Status NOT IN ('Done', 'Cancelled')"

            base_query += " ORDER BY t.Priority DESC, t.EndDate ASC"

            result = self.db_service.execute_query(base_query, tuple(params))

            # Enhance tasks
            for task in result:
                task["time_tracking"] = self._calculate_time_metrics(task)
                task["overdue"] = self._is_task_overdue(task)
                task["urgency_score"] = self._calculate_urgency_score(task)

            return result

        except Exception as e:
            logger.error(f"Failed to get tasks for assignee {assignee_id}: {str(e)}")
            raise DatabaseException(f"Task retrieval failed: {str(e)}")

    @with_db_transaction
    def update_task(
        self, task_id: int, task_data: Dict[str, Any], user_id: int
    ) -> bool:
        """Update existing task"""
        try:
            # Validate task exists
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError("Task does not exist")

            # Build update query dynamically
            update_fields = []
            params = []

            # Fields that can be updated
            updatable_fields = {
                "task_name": "TaskName",
                "description": "Description",
                "start_date": "StartDate",
                "end_date": "EndDate",
                "assignee_id": "AssigneeID",
                "status": "Status",
                "priority": "Priority",
                "progress": "Progress",
                "estimated_hours": "EstimatedHours",
                "actual_hours": "ActualHours",
                "dependencies": "Dependencies",
                "labels": "Labels",
            }

            for field_key, db_field in updatable_fields.items():
                if field_key in task_data:
                    value = task_data[field_key]

                    # Validate specific fields
                    if field_key == "progress" and not (0 <= value <= 100):
                        raise ValueError("Progress must be between 0 and 100")

                    if (
                        field_key == "assignee_id"
                        and value
                        and not self._user_exists(value)
                    ):
                        raise ValueError("Assignee user does not exist")

                    if field_key in ["start_date", "end_date"] and isinstance(
                        value, str
                    ):
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

                    update_fields.append(f"{db_field} = ?")
                    params.append(value)

            if not update_fields:
                return True  # Nothing to update

            # Add LastModifiedDate
            update_fields.append("LastModifiedDate = GETDATE()")

            query = f"""
            UPDATE Tasks 
            SET {', '.join(update_fields)}
            WHERE TaskID = ?
            """
            params.append(task_id)

            self.db_service.execute_query(query, tuple(params), fetch=False)

            # Auto-update progress based on status
            self._auto_update_progress(task_id, task_data.get("status"))

            # Clear cache
            self.db_service.clear_cache("tasks_")

            logger.info(f"Task {task_id} updated successfully by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {str(e)}")
            raise DatabaseException(f"Task update failed: {str(e)}")

    def update_progress(self, task_id: int, progress: int, user_id: int) -> bool:
        """Update task progress"""
        try:
            if not (0 <= progress <= 100):
                raise ValueError("Progress must be between 0 and 100")

            # Auto-update status based on progress
            status = None
            if progress == 0:
                status = TaskStatus.TODO.value
            elif progress == 100:
                status = TaskStatus.DONE.value
            elif progress > 0:
                status = TaskStatus.IN_PROGRESS.value

            update_data = {"progress": progress}
            if status:
                update_data["status"] = status

            return self.update_task(task_id, update_data, user_id)

        except Exception as e:
            logger.error(f"Failed to update progress for task {task_id}: {str(e)}")
            raise DatabaseException(f"Progress update failed: {str(e)}")

    @with_db_transaction
    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete task"""
        try:
            # Check if task exists
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError("Task does not exist")

            # Delete task
            query = "DELETE FROM Tasks WHERE TaskID = ?"
            self.db_service.execute_query(query, (task_id,), fetch=False)

            # Clear cache
            self.db_service.clear_cache("tasks_")

            logger.info(f"Task {task_id} deleted by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {str(e)}")
            raise DatabaseException(f"Task deletion failed: {str(e)}")

    def get_task_analytics(
        self,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive task analytics"""
        try:
            base_query = """
            SELECT 
                Status,
                Priority,
                Progress,
                EstimatedHours,
                ActualHours,
                StartDate,
                EndDate,
                CreatedDate,
                AssigneeID
            FROM Tasks
            WHERE 1=1
            """

            params = []

            if project_id:
                base_query += " AND ProjectID = ?"
                params.append(project_id)

            if assignee_id:
                base_query += " AND AssigneeID = ?"
                params.append(assignee_id)

            if date_range:
                base_query += " AND CreatedDate BETWEEN ? AND ?"
                params.extend(date_range)

            tasks = self.db_service.execute_query(base_query, tuple(params))

            if not tasks:
                return self._empty_analytics()

            # Calculate analytics
            analytics = {
                "total_tasks": len(tasks),
                "status_distribution": self._calculate_status_distribution(tasks),
                "priority_distribution": self._calculate_priority_distribution(tasks),
                "completion_metrics": self._calculate_completion_metrics(tasks),
                "time_metrics": self._calculate_time_analytics(tasks),
                "overdue_tasks": self._calculate_overdue_metrics(tasks),
                "productivity_metrics": self._calculate_productivity_metrics(tasks),
                "trend_analysis": self._calculate_trends(tasks),
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get task analytics: {str(e)}")
            raise DatabaseException(f"Analytics calculation failed: {str(e)}")

    def get_kanban_board(self, project_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get tasks organized for Kanban board view"""
        try:
            tasks = self.get_tasks_by_project(project_id)

            # Group tasks by status
            kanban_board = {
                TaskStatus.TODO.value: [],
                TaskStatus.IN_PROGRESS.value: [],
                TaskStatus.REVIEW.value: [],
                TaskStatus.TESTING.value: [],
                TaskStatus.DONE.value: [],
                TaskStatus.BLOCKED.value: [],
            }

            for task in tasks:
                status = task.get("Status", TaskStatus.TODO.value)
                if status in kanban_board:
                    # Add Kanban-specific data
                    task["card_color"] = self._get_priority_color(task.get("Priority"))
                    task["days_in_status"] = self._calculate_days_in_status(task)
                    task["blocking_issues"] = self._check_blocking_issues(task)

                    kanban_board[status].append(task)

            return kanban_board

        except Exception as e:
            logger.error(
                f"Failed to get Kanban board for project {project_id}: {str(e)}"
            )
            raise DatabaseException(f"Kanban board retrieval failed: {str(e)}")

    def search_tasks(
        self, search_query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search tasks with advanced filtering"""
        try:
            base_query = """
            SELECT 
                t.*,
                u.Username as AssigneeName,
                p.ProjectName,
                creator.Username as CreatedByName
            FROM Tasks t
            LEFT JOIN Users u ON t.AssigneeID = u.UserID
            LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
            LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
            WHERE (
                t.TaskName LIKE ? OR 
                t.Description LIKE ? OR
                t.Labels LIKE ?
            )
            """

            search_pattern = f"%{search_query}%"
            params = [search_pattern, search_pattern, search_pattern]

            # Apply filters
            if filters:
                if filters.get("project_id"):
                    base_query += " AND t.ProjectID = ?"
                    params.append(filters["project_id"])

                if filters.get("status"):
                    base_query += " AND t.Status = ?"
                    params.append(filters["status"])

                if filters.get("priority"):
                    base_query += " AND t.Priority = ?"
                    params.append(filters["priority"])

                if filters.get("assignee_id"):
                    base_query += " AND t.AssigneeID = ?"
                    params.append(filters["assignee_id"])

                if filters.get("date_from"):
                    base_query += " AND t.CreatedDate >= ?"
                    params.append(filters["date_from"])

                if filters.get("date_to"):
                    base_query += " AND t.CreatedDate <= ?"
                    params.append(filters["date_to"])

            base_query += " ORDER BY t.Priority DESC, t.CreatedDate DESC"

            result = self.db_service.execute_query(base_query, tuple(params))

            # Enhance search results
            for task in result:
                task["relevance_score"] = self._calculate_relevance_score(
                    task, search_query
                )
                task["time_tracking"] = self._calculate_time_metrics(task)

            # Sort by relevance
            result.sort(key=lambda x: x["relevance_score"], reverse=True)

            return result

        except Exception as e:
            logger.error(f"Failed to search tasks: {str(e)}")
            raise DatabaseException(f"Task search failed: {str(e)}")

    # Helper methods
    def _project_exists(self, project_id: int) -> bool:
        """Check if project exists"""
        try:
            query = "SELECT COUNT(*) as count FROM Projects WHERE ProjectID = ?"
            result = self.db_service.execute_query(query, (project_id,))
            return result[0]["count"] > 0
        except:
            return False

    def _user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        try:
            query = "SELECT COUNT(*) as count FROM Users WHERE UserID = ?"
            result = self.db_service.execute_query(query, (user_id,))
            return result[0]["count"] > 0
        except:
            return False

    def _calculate_time_metrics(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate time-related metrics for a task"""
        metrics = {
            "estimated_hours": task.get("EstimatedHours") or 0,
            "actual_hours": task.get("ActualHours") or 0,
            "variance_hours": 0,
            "efficiency_percentage": 100,
            "days_remaining": None,
            "is_overdue": False,
        }

        # Calculate variance
        if metrics["estimated_hours"] > 0:
            metrics["variance_hours"] = (
                metrics["actual_hours"] - metrics["estimated_hours"]
            )
            metrics["efficiency_percentage"] = (
                metrics["estimated_hours"] / metrics["actual_hours"]
            ) * 100

        # Calculate days remaining
        end_date = task.get("EndDate")
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            now = datetime.now()
            if end_date > now:
                metrics["days_remaining"] = (end_date - now).days
            else:
                metrics["is_overdue"] = True
                metrics["days_overdue"] = (now - end_date).days

        return metrics

    def _parse_dependencies(self, dependencies_str: Optional[str]) -> List[int]:
        """Parse dependencies string to list of task IDs"""
        if not dependencies_str:
            return []

        try:
            return [
                int(x.strip())
                for x in dependencies_str.split(",")
                if x.strip().isdigit()
            ]
        except:
            return []

    def _parse_labels(self, labels_str: Optional[str]) -> List[str]:
        """Parse labels string to list"""
        if not labels_str:
            return []

        return [label.strip() for label in labels_str.split(",") if label.strip()]

    def _is_task_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if task is overdue"""
        end_date = task.get("EndDate")
        status = task.get("Status")

        if not end_date or status in [
            TaskStatus.DONE.value,
            TaskStatus.CANCELLED.value,
        ]:
            return False

        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        return datetime.now() > end_date

    def _calculate_urgency_score(self, task: Dict[str, Any]) -> int:
        """Calculate urgency score for task prioritization"""
        score = 0

        # Priority contribution
        priority_scores = {
            TaskPriority.CRITICAL.value: 40,
            TaskPriority.HIGH.value: 30,
            TaskPriority.MEDIUM.value: 20,
            TaskPriority.LOW.value: 10,
        }
        score += priority_scores.get(task.get("Priority"), 10)

        # Due date contribution
        end_date = task.get("EndDate")
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            days_until_due = (end_date - datetime.now()).days
            if days_until_due < 0:  # Overdue
                score += 50
            elif days_until_due <= 1:  # Due today/tomorrow
                score += 30
            elif days_until_due <= 7:  # Due this week
                score += 20

        # Progress contribution (less progress = more urgent)
        progress = task.get("Progress", 0)
        if progress < 25:
            score += 20
        elif progress < 50:
            score += 10

        return min(score, 100)  # Cap at 100

    def _auto_update_progress(self, task_id: int, status: Optional[str]):
        """Auto-update progress based on status"""
        if not status:
            return

        progress_map = {
            TaskStatus.TODO.value: 0,
            TaskStatus.IN_PROGRESS.value: 25,
            TaskStatus.REVIEW.value: 75,
            TaskStatus.TESTING.value: 90,
            TaskStatus.DONE.value: 100,
            TaskStatus.CANCELLED.value: 0,
        }

        if status in progress_map:
            query = "UPDATE Tasks SET Progress = ? WHERE TaskID = ?"
            self.db_service.execute_query(
                query, (progress_map[status], task_id), fetch=False
            )

    def _calculate_status_distribution(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate status distribution"""
        distribution = {}
        for task in tasks:
            status = task.get("Status", "Unknown")
            distribution[status] = distribution.get(status, 0) + 1
        return distribution

    def _calculate_priority_distribution(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate priority distribution"""
        distribution = {}
        for task in tasks:
            priority = task.get("Priority", "Unknown")
            distribution[priority] = distribution.get(priority, 0) + 1
        return distribution

    def _calculate_completion_metrics(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate completion metrics"""
        total_tasks = len(tasks)
        completed_tasks = len(
            [t for t in tasks if t.get("Status") == TaskStatus.DONE.value]
        )
        in_progress_tasks = len(
            [t for t in tasks if t.get("Status") == TaskStatus.IN_PROGRESS.value]
        )

        avg_progress = (
            sum(t.get("Progress", 0) for t in tasks) / total_tasks
            if total_tasks > 0
            else 0
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            ),
            "average_progress": round(avg_progress, 2),
        }

    def _calculate_time_analytics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate time-related analytics"""
        estimated_total = sum(t.get("EstimatedHours", 0) for t in tasks)
        actual_total = sum(t.get("ActualHours", 0) for t in tasks)

        return {
            "total_estimated_hours": estimated_total,
            "total_actual_hours": actual_total,
            "time_variance": actual_total - estimated_total,
            "efficiency_rate": (
                (estimated_total / actual_total * 100) if actual_total > 0 else 100
            ),
        }

    def _calculate_overdue_metrics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overdue task metrics"""
        overdue_tasks = [t for t in tasks if self._is_task_overdue(t)]

        return {
            "overdue_count": len(overdue_tasks),
            "overdue_percentage": (
                (len(overdue_tasks) / len(tasks) * 100) if tasks else 0
            ),
            "critical_overdue": len(
                [
                    t
                    for t in overdue_tasks
                    if t.get("Priority") == TaskPriority.CRITICAL.value
                ]
            ),
        }

    def _calculate_productivity_metrics(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate productivity metrics"""
        # Implementation for productivity calculations
        return {
            "tasks_per_day": 0,  # Would need date range
            "average_completion_time": 0,  # Would need completion dates
            "velocity": 0,  # Story points or task count per sprint
        }

    def _calculate_trends(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend analysis"""
        # Implementation for trend calculations
        return {
            "completion_trend": "stable",
            "velocity_trend": "increasing",
            "quality_trend": "improving",
        }

    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            "total_tasks": 0,
            "status_distribution": {},
            "priority_distribution": {},
            "completion_metrics": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_rate": 0,
                "average_progress": 0,
            },
            "time_metrics": {
                "total_estimated_hours": 0,
                "total_actual_hours": 0,
                "time_variance": 0,
                "efficiency_rate": 100,
            },
            "overdue_tasks": {
                "overdue_count": 0,
                "overdue_percentage": 0,
                "critical_overdue": 0,
            },
        }

    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority level"""
        colors = {
            TaskPriority.CRITICAL.value: "#ef4444",
            TaskPriority.HIGH.value: "#f97316",
            TaskPriority.MEDIUM.value: "#eab308",
            TaskPriority.LOW.value: "#22c55e",
        }
        return colors.get(priority, "#6b7280")

    def _calculate_days_in_status(self, task: Dict[str, Any]) -> int:
        """Calculate days task has been in current status"""
        # This would require status change tracking
        return 0  # Placeholder

    def _check_blocking_issues(self, task: Dict[str, Any]) -> List[str]:
        """Check for blocking issues"""
        issues = []

        if self._is_task_overdue(task):
            issues.append("Overdue")

        dependencies = self._parse_dependencies(task.get("Dependencies"))
        if dependencies:
            # Check if dependencies are completed
            # This would require checking dependency status
            issues.append("Has dependencies")

        return issues

    def _calculate_relevance_score(
        self, task: Dict[str, Any], search_query: str
    ) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = search_query.lower()

        # Title match (highest weight)
        task_name = (task.get("TaskName") or "").lower()
        if query_lower in task_name:
            score += 10.0
            if task_name.startswith(query_lower):
                score += 5.0

        # Description match
        description = (task.get("Description") or "").lower()
        if query_lower in description:
            score += 5.0

        # Labels match
        labels = (task.get("Labels") or "").lower()
        if query_lower in labels:
            score += 3.0

        return score


# Global task service instance
_task_service = None


def get_task_service() -> TaskService:
    """Get global task service instance"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


# Export classes and functions
__all__ = ["TaskService", "Task", "TaskStatus", "TaskPriority", "get_task_service"]
