# services/enhanced_project_service.py
from typing import Dict, List, Optional, Any
from datetime import datetime
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


class ProjectStatus(Enum):
    """Project status enumeration"""

    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ProjectPriority(Enum):
    """Project priority enumeration"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Project:
    """Project data model"""

    project_id: Optional[int] = None
    project_name: str = ""
    description: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = ProjectStatus.PLANNING.value
    priority: str = ProjectPriority.MEDIUM.value
    budget: Optional[float] = None
    client_name: str = ""
    created_by: Optional[int] = None
    created_date: Optional[datetime] = None
    tags: str = ""
    progress: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class EnhancedProjectService:
    """Enhanced project management service"""

    def __init__(self):
        self.db_service = get_db_service()

    @with_db_transaction
    def create_project(self, project_data: Dict[str, Any], user_id: int = 1) -> int:
        """Create a new project"""
        try:
            # Validate required fields
            if not project_data.get("project_name") and not project_data.get(
                "ProjectName"
            ):
                raise ValueError("Project name is required")

            # Normalize field names
            normalized_data = self._normalize_project_data(project_data)

            query = """
            INSERT INTO Projects (
                ProjectName, Description, StartDate, EndDate, 
                Status, Priority, Budget, ClientName, CreatedBy, Tags
            )
            OUTPUT INSERTED.ProjectID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                normalized_data.get("project_name", ""),
                normalized_data.get("description", ""),
                normalized_data.get("start_date"),
                normalized_data.get("end_date"),
                normalized_data.get("status", ProjectStatus.PLANNING.value),
                normalized_data.get("priority", ProjectPriority.MEDIUM.value),
                normalized_data.get("budget"),
                normalized_data.get("client_name", ""),
                user_id,
                normalized_data.get("tags", ""),
            )

            result = self.db_service.execute_query(query, params)
            project_id = result[0]["ProjectID"] if result else None

            # Clear cache
            self.db_service.clear_cache("projects_")

            logger.info(f"Project created successfully: ID {project_id}")
            return project_id

        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            raise DatabaseException(f"Project creation failed: {str(e)}")

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            query = """
            SELECT 
                p.*,
                u.Username as CreatedByName,
                COUNT(t.TaskID) as TaskCount,
                COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as CompletedTasks,
                ISNULL(AVG(CAST(t.Progress as FLOAT)), 0) as AvgProgress
            FROM Projects p
            LEFT JOIN Users u ON p.CreatedBy = u.UserID
            LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
            WHERE p.ProjectID = ?
            GROUP BY p.ProjectID, p.ProjectName, p.Description, p.StartDate, p.EndDate,
                     p.Status, p.Priority, p.Budget, p.ClientName, p.CreatedBy,
                     p.CreatedDate, p.LastModifiedDate, p.Tags, p.Progress, u.Username
            """

            result = self.db_service.execute_query(query, (project_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {str(e)}")
            raise DatabaseException(f"Project retrieval failed: {str(e)}")

    @cached_query("all_projects", ttl=300)
    def get_all_projects(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all projects"""
        try:
            if user_id:
                query = """
                SELECT 
                    p.*,
                    u.Username as CreatedByName,
                    COUNT(t.TaskID) as TaskCount,
                    COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as CompletedTasks
                FROM Projects p
                LEFT JOIN Users u ON p.CreatedBy = u.UserID
                LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
                WHERE p.CreatedBy = ?
                GROUP BY p.ProjectID, p.ProjectName, p.Description, p.StartDate, p.EndDate,
                         p.Status, p.Priority, p.Budget, p.ClientName, p.CreatedBy,
                         p.CreatedDate, p.LastModifiedDate, p.Tags, p.Progress, u.Username
                ORDER BY p.CreatedDate DESC
                """
                params = (user_id,)
            else:
                query = """
                SELECT 
                    p.*,
                    u.Username as CreatedByName,
                    COUNT(t.TaskID) as TaskCount,
                    COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as CompletedTasks
                FROM Projects p
                LEFT JOIN Users u ON p.CreatedBy = u.UserID
                LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
                GROUP BY p.ProjectID, p.ProjectName, p.Description, p.StartDate, p.EndDate,
                         p.Status, p.Priority, p.Budget, p.ClientName, p.CreatedBy,
                         p.CreatedDate, p.LastModifiedDate, p.Tags, p.Progress, u.Username
                ORDER BY p.CreatedDate DESC
                """
                params = ()

            result = self.db_service.execute_query(query, params)
            return result

        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}")
            return []

    @with_db_transaction
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> bool:
        """Update existing project"""
        try:
            # Normalize field names
            normalized_data = self._normalize_project_data(project_data)

            # Build update query dynamically
            update_fields = []
            params = []

            updatable_fields = {
                "project_name": "ProjectName",
                "description": "Description",
                "start_date": "StartDate",
                "end_date": "EndDate",
                "status": "Status",
                "priority": "Priority",
                "budget": "Budget",
                "client_name": "ClientName",
                "tags": "Tags",
                "progress": "Progress",
            }

            for field_key, db_field in updatable_fields.items():
                if field_key in normalized_data:
                    update_fields.append(f"{db_field} = ?")
                    params.append(normalized_data[field_key])

            if not update_fields:
                return True

            # Add LastModifiedDate
            update_fields.append("LastModifiedDate = GETDATE()")

            query = f"""
            UPDATE Projects 
            SET {', '.join(update_fields)}
            WHERE ProjectID = ?
            """
            params.append(project_id)

            self.db_service.execute_query(query, tuple(params), fetch=False)

            # Clear cache
            self.db_service.clear_cache("projects_")

            logger.info(f"Project {project_id} updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {str(e)}")
            raise DatabaseException(f"Project update failed: {str(e)}")

    @with_db_transaction
    def delete_project(self, project_id: int) -> bool:
        """Delete project"""
        try:
            # First delete related tasks
            self.db_service.execute_query(
                "DELETE FROM Tasks WHERE ProjectID = ?", (project_id,), fetch=False
            )

            # Then delete project
            self.db_service.execute_query(
                "DELETE FROM Projects WHERE ProjectID = ?", (project_id,), fetch=False
            )

            # Clear cache
            self.db_service.clear_cache("projects_")

            logger.info(f"Project {project_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {str(e)}")
            raise DatabaseException(f"Project deletion failed: {str(e)}")

    def get_projects_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get projects by status"""
        try:
            query = """
            SELECT p.*, u.Username as CreatedByName
            FROM Projects p
            LEFT JOIN Users u ON p.CreatedBy = u.UserID
            WHERE p.Status = ?
            ORDER BY p.CreatedDate DESC
            """

            return self.db_service.execute_query(query, (status,))

        except Exception as e:
            logger.error(f"Failed to get projects by status: {str(e)}")
            return []

    def get_project_analytics(self) -> Dict[str, Any]:
        """Get project analytics"""
        try:
            # Status distribution
            status_query = """
            SELECT Status, COUNT(*) as Count
            FROM Projects
            GROUP BY Status
            ORDER BY Count DESC
            """
            status_data = self.db_service.execute_query(status_query)

            # Priority distribution
            priority_query = """
            SELECT Priority, COUNT(*) as Count
            FROM Projects
            GROUP BY Priority
            ORDER BY Count DESC
            """
            priority_data = self.db_service.execute_query(priority_query)

            # Monthly project creation
            monthly_query = """
            SELECT 
                YEAR(CreatedDate) as Year,
                MONTH(CreatedDate) as Month,
                COUNT(*) as Count
            FROM Projects
            WHERE CreatedDate >= DATEADD(MONTH, -12, GETDATE())
            GROUP BY YEAR(CreatedDate), MONTH(CreatedDate)
            ORDER BY Year, Month
            """
            monthly_data = self.db_service.execute_query(monthly_query)

            return {
                "status_distribution": status_data,
                "priority_distribution": priority_data,
                "monthly_creation": monthly_data,
            }

        except Exception as e:
            logger.error(f"Failed to get project analytics: {str(e)}")
            return {}

    def search_projects(
        self, search_term: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search projects with filters"""
        try:
            base_query = """
            SELECT p.*, u.Username as CreatedByName
            FROM Projects p
            LEFT JOIN Users u ON p.CreatedBy = u.UserID
            WHERE (p.ProjectName LIKE ? OR p.Description LIKE ? OR p.ClientName LIKE ?)
            """

            search_pattern = f"%{search_term}%"
            params = [search_pattern, search_pattern, search_pattern]

            # Apply filters
            if filters:
                if filters.get("status"):
                    base_query += " AND p.Status = ?"
                    params.append(filters["status"])

                if filters.get("priority"):
                    base_query += " AND p.Priority = ?"
                    params.append(filters["priority"])

                if filters.get("created_by"):
                    base_query += " AND p.CreatedBy = ?"
                    params.append(filters["created_by"])

            base_query += " ORDER BY p.CreatedDate DESC"

            return self.db_service.execute_query(base_query, tuple(params))

        except Exception as e:
            logger.error(f"Failed to search projects: {str(e)}")
            return []

    def get_projects_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get projects for specific user"""
        try:
            query = """
            SELECT 
                p.ProjectID,
                p.ProjectName,
                p.Status,
                p.Priority,
                p.Progress
            FROM Projects p
            WHERE p.CreatedBy = ? OR p.ProjectID IN (
                SELECT DISTINCT t.ProjectID 
                FROM Tasks t 
                WHERE t.AssigneeID = ?
            )
            ORDER BY p.ProjectName
            """

            return self.db_service.execute_query(query, (user_id, user_id))

        except Exception as e:
            logger.error(f"Failed to get projects for user {user_id}: {str(e)}")
            return []

    def _normalize_project_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize project data field names"""
        normalized = {}

        # Field name mappings
        field_mappings = {
            "ProjectName": "project_name",
            "project_name": "project_name",
            "Description": "description",
            "description": "description",
            "StartDate": "start_date",
            "start_date": "start_date",
            "EndDate": "end_date",
            "end_date": "end_date",
            "Status": "status",
            "status": "status",
            "Priority": "priority",
            "priority": "priority",
            "Budget": "budget",
            "budget": "budget",
            "ClientName": "client_name",
            "client_name": "client_name",
            "Tags": "tags",
            "tags": "tags",
            "Progress": "progress",
            "progress": "progress",
        }

        for key, value in data.items():
            normalized_key = field_mappings.get(key, key.lower())
            normalized[normalized_key] = value

        return normalized


# Global service instance
_project_service = None


def get_project_service() -> EnhancedProjectService:
    """Get global project service instance"""
    global _project_service
    if _project_service is None:
        _project_service = EnhancedProjectService()
    return _project_service


# Export classes and functions
__all__ = [
    "EnhancedProjectService",
    "Project",
    "ProjectStatus",
    "ProjectPriority",
    "get_project_service",
]
