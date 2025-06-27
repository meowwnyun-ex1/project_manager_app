# services/task_service.py
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date
from services.enhanced_db_service import DatabaseService
from models.task import Task
import logging

logger = logging.getLogger(__name__)


class TaskService:
    """Task service for CRUD operations"""

    @staticmethod
    def get_tasks_by_project(project_id: int) -> pd.DataFrame:
        """Get all tasks for a specific project"""
        query = """
        SELECT 
            T.TaskID, T.TaskName, T.Description, T.StartDate, T.EndDate, 
            T.Status, T.Progress, T.CreatedDate, T.ProjectID,
            U.Username AS Assignee, U.UserID AS AssigneeID
        FROM Tasks T
        LEFT JOIN Users U ON T.AssigneeID = U.UserID
        WHERE T.ProjectID = ?
        ORDER BY T.StartDate, T.TaskName
        """

        tasks = DatabaseService.fetch_data(query, (project_id,))
        df = pd.DataFrame(tasks) if tasks else pd.DataFrame()

        # Convert date columns
        if not df.empty:
            date_columns = ["StartDate", "EndDate", "CreatedDate"]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    @staticmethod
    def get_all_tasks() -> pd.DataFrame:
        """Get all tasks across all projects"""
        query = """
        SELECT 
            T.TaskID, T.TaskName, T.Description, T.StartDate, T.EndDate, 
            T.Status, T.Progress, T.CreatedDate, T.ProjectID,
            U.Username AS Assignee, U.UserID AS AssigneeID,
            P.ProjectName
        FROM Tasks T
        LEFT JOIN Users U ON T.AssigneeID = U.UserID
        LEFT JOIN Projects P ON T.ProjectID = P.ProjectID
        ORDER BY T.StartDate, P.ProjectName, T.TaskName
        """

        tasks = DatabaseService.fetch_data(query)
        df = pd.DataFrame(tasks) if tasks else pd.DataFrame()

        # Convert date columns
        if not df.empty:
            date_columns = ["StartDate", "EndDate", "CreatedDate"]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Task]:
        """Get single task by ID"""
        query = """
        SELECT TaskID, ProjectID, TaskName, Description, StartDate, EndDate, 
               AssigneeID, Status, Progress, CreatedDate
        FROM Tasks 
        WHERE TaskID = ?
        """

        data = DatabaseService.fetch_one(query, (task_id,))
        return Task.from_dict(data) if data else None

    @staticmethod
    def create_task(task_data: Dict[str, Any]) -> bool:
        """Create new task with validation"""
        try:
            # Validate using Task model
            task = Task(
                project_id=task_data["project_id"],
                task_name=task_data["task_name"],
                description=task_data.get("description", ""),
                start_date=task_data["start_date"],
                end_date=task_data["end_date"],
                assignee_id=task_data["assignee_id"],
                status=task_data.get("status", "To Do"),
                progress=task_data.get("progress", 0),
            )

            query = """
            INSERT INTO Tasks (ProjectID, TaskName, Description, StartDate, EndDate, 
                             AssigneeID, Status, Progress)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            success = DatabaseService.execute_query(
                query,
                (
                    task.project_id,
                    task.task_name,
                    task.description,
                    task.start_date,
                    task.end_date,
                    task.assignee_id,
                    task.status,
                    task.progress,
                ),
            )

            if success:
                logger.info(f"Task created: {task.task_name}")

            return success

        except ValueError as e:
            logger.error(f"Task validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Task creation failed: {e}")
            return False

    @staticmethod
    def update_task(task_id: int, task_data: Dict[str, Any]) -> bool:
        """Update existing task"""
        try:
            # Validate using Task model
            task = Task(
                task_id=task_id,
                project_id=task_data["project_id"],
                task_name=task_data["task_name"],
                description=task_data.get("description", ""),
                start_date=task_data["start_date"],
                end_date=task_data["end_date"],
                assignee_id=task_data["assignee_id"],
                status=task_data["status"],
                progress=task_data["progress"],
            )

            query = """
            UPDATE Tasks 
            SET TaskName = ?, Description = ?, StartDate = ?, EndDate = ?, 
                AssigneeID = ?, Status = ?, Progress = ?
            WHERE TaskID = ?
            """

            success = DatabaseService.execute_query(
                query,
                (
                    task.task_name,
                    task.description,
                    task.start_date,
                    task.end_date,
                    task.assignee_id,
                    task.status,
                    task.progress,
                    task_id,
                ),
            )

            if success:
                logger.info(f"Task updated: {task.task_name}")

            return success

        except ValueError as e:
            logger.error(f"Task validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Task update failed: {e}")
            return False

    @staticmethod
    def delete_task(task_id: int) -> bool:
        """Delete single task"""
        try:
            query = "DELETE FROM Tasks WHERE TaskID = ?"
            success = DatabaseService.execute_query(query, (task_id,))

            if success:
                logger.info(f"Task deleted: {task_id}")

            return success

        except Exception as e:
            logger.error(f"Task deletion failed: {e}")
            return False

    @staticmethod
    def delete_tasks_by_project(project_id: int) -> bool:
        """Delete all tasks for a project"""
        try:
            query = "DELETE FROM Tasks WHERE ProjectID = ?"
            success = DatabaseService.execute_query(query, (project_id,))

            if success:
                logger.info(f"Tasks deleted for project: {project_id}")

            return success

        except Exception as e:
            logger.error(f"Task deletion failed for project {project_id}: {e}")
            return False

    @staticmethod
    def get_task_statistics() -> Dict[str, Any]:
        """Get task statistics for dashboard"""
        try:
            # Total tasks
            total_query = "SELECT COUNT(*) FROM Tasks"
            total_tasks = DatabaseService.execute_scalar(total_query) or 0

            # Tasks by status
            status_query = """
            SELECT Status, COUNT(*) as Count 
            FROM Tasks 
            GROUP BY Status
            """
            status_data = DatabaseService.fetch_data(status_query)

            # Overdue tasks
            overdue_query = """
            SELECT COUNT(*) FROM Tasks 
            WHERE EndDate < ? AND Status NOT IN ('Done')
            """
            overdue_tasks = (
                DatabaseService.execute_scalar(overdue_query, (date.today(),)) or 0
            )

            # Average progress
            avg_progress_query = "SELECT AVG(CAST(Progress AS FLOAT)) FROM Tasks"
            avg_progress = DatabaseService.execute_scalar(avg_progress_query) or 0

            # Tasks by assignee
            assignee_query = """
            SELECT U.Username, COUNT(*) as TaskCount
            FROM Tasks T
            JOIN Users U ON T.AssigneeID = U.UserID
            GROUP BY U.Username, U.UserID
            ORDER BY TaskCount DESC
            """
            assignee_data = DatabaseService.fetch_data(assignee_query)

            return {
                "total_tasks": total_tasks,
                "overdue_tasks": overdue_tasks,
                "average_progress": round(avg_progress, 1),
                "status_distribution": status_data,
                "assignee_distribution": assignee_data,
            }

        except Exception as e:
            logger.error(f"Failed to get task statistics: {e}")
            return {}

    @staticmethod
    def get_upcoming_tasks(limit: int = 5) -> List[Dict[str, Any]]:
        """Get upcoming tasks that are due soon"""
        query = """
        SELECT TOP (?) 
            T.TaskName, T.EndDate, T.Status, T.Progress,
            U.Username AS Assignee, P.ProjectName
        FROM Tasks T
        LEFT JOIN Users U ON T.AssigneeID = U.UserID
        LEFT JOIN Projects P ON T.ProjectID = P.ProjectID
        WHERE T.Status NOT IN ('Done') AND T.EndDate >= ?
        ORDER BY T.EndDate ASC
        """

        return DatabaseService.fetch_data(query, (limit, date.today()))
