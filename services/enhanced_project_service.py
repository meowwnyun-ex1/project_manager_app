# services/enhanced_project_service.py
import pandas as pd
from typing import Dict, Any, Optional
from datetime import date
from services.enhanced_db_service import DatabaseService
from models.project import Project
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    """Enhanced project service with validation and error handling"""

    @staticmethod
    def get_all_projects() -> pd.DataFrame:
        """Get all projects as DataFrame"""
        query = """
        SELECT 
            ProjectID, ProjectName, Description, StartDate, EndDate, Status, CreatedDate
        FROM Projects 
        ORDER BY CreatedDate DESC
        """

        projects = DatabaseService.fetch_data(query)
        df = pd.DataFrame(projects) if projects else pd.DataFrame()

        # Convert date columns
        if not df.empty:
            date_columns = ["StartDate", "EndDate", "CreatedDate"]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    @staticmethod
    def get_project_by_id(project_id: int) -> Optional[Project]:
        """Get single project by ID"""
        query = """
        SELECT ProjectID, ProjectName, Description, StartDate, EndDate, Status, CreatedDate
        FROM Projects 
        WHERE ProjectID = ?
        """

        data = DatabaseService.fetch_one(query, (project_id,))
        return Project.from_dict(data) if data else None

    @staticmethod
    def create_project(project_data: Dict[str, Any]) -> bool:
        """Create new project with validation"""
        try:
            # Validate using Project model
            project = Project(
                project_name=project_data["project_name"],
                description=project_data.get("description", ""),
                start_date=project_data["start_date"],
                end_date=project_data["end_date"],
                status=project_data.get("status", "Planning"),
            )

            query = """
            INSERT INTO Projects (ProjectName, Description, StartDate, EndDate, Status)
            VALUES (?, ?, ?, ?, ?)
            """

            success = DatabaseService.execute_query(
                query,
                (
                    project.project_name,
                    project.description,
                    project.start_date,
                    project.end_date,
                    project.status,
                ),
            )

            if success:
                logger.info(f"Project created: {project.project_name}")

            return success

        except ValueError as e:
            logger.error(f"Project validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return False

    @staticmethod
    def update_project(project_id: int, project_data: Dict[str, Any]) -> bool:
        """Update existing project"""
        try:
            # Validate using Project model
            project = Project(
                project_id=project_id,
                project_name=project_data["project_name"],
                description=project_data.get("description", ""),
                start_date=project_data["start_date"],
                end_date=project_data["end_date"],
                status=project_data["status"],
            )

            query = """
            UPDATE Projects 
            SET ProjectName = ?, Description = ?, StartDate = ?, EndDate = ?, Status = ?
            WHERE ProjectID = ?
            """

            success = DatabaseService.execute_query(
                query,
                (
                    project.project_name,
                    project.description,
                    project.start_date,
                    project.end_date,
                    project.status,
                    project_id,
                ),
            )

            if success:
                logger.info(f"Project updated: {project.project_name}")

            return success

        except ValueError as e:
            logger.error(f"Project validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Project update failed: {e}")
            return False

    @staticmethod
    def delete_project(project_id: int) -> bool:
        """Delete project and related tasks"""
        try:
            # Delete tasks first (or rely on CASCADE DELETE)
            TaskService.delete_tasks_by_project(project_id)

            query = "DELETE FROM Projects WHERE ProjectID = ?"
            success = DatabaseService.execute_query(query, (project_id,))

            if success:
                logger.info(f"Project deleted: {project_id}")

            return success

        except Exception as e:
            logger.error(f"Project deletion failed: {e}")
            return False

    @staticmethod
    def get_project_statistics() -> Dict[str, Any]:
        """Get project statistics for dashboard"""
        try:
            # Total projects
            total_query = "SELECT COUNT(*) FROM Projects"
            total_projects = DatabaseService.execute_scalar(total_query) or 0

            # Projects by status
            status_query = """
            SELECT Status, COUNT(*) as Count 
            FROM Projects 
            GROUP BY Status
            """
            status_data = DatabaseService.fetch_data(status_query)

            # Active projects
            active_query = """
            SELECT COUNT(*) FROM Projects 
            WHERE Status IN ('Planning', 'In Progress')
            """
            active_projects = DatabaseService.execute_scalar(active_query) or 0

            # Overdue projects
            overdue_query = """
            SELECT COUNT(*) FROM Projects 
            WHERE EndDate < ? AND Status NOT IN ('Completed', 'Cancelled')
            """
            overdue_projects = (
                DatabaseService.execute_scalar(overdue_query, (date.today(),)) or 0
            )

            return {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "overdue_projects": overdue_projects,
                "status_distribution": status_data,
            }

        except Exception as e:
            logger.error(f"Failed to get project statistics: {e}")
            return {}


# Import TaskService to avoid circular imports
from services.task_service import TaskService
