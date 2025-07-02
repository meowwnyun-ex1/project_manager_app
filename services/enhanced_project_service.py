# services/enhanced_project_service.py
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
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
    client_name: Optional[str] = None
    tags: Optional[str] = None
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


class EnhancedProjectService:
    """Enhanced project management service"""

    def __init__(self):
        self.db_service = get_db_service()

    @with_db_transaction
    def create_project(self, project_data: Dict[str, Any], user_id: int) -> int:
        """Create a new project"""
        try:
            # Validate required fields
            required_fields = ["project_name"]
            for field in required_fields:
                if field not in project_data or not project_data[field]:
                    raise ValueError(f"Required field '{field}' is missing")

            # Validate dates
            start_date = project_data.get("start_date")
            end_date = project_data.get("end_date")
            if start_date and end_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(
                        start_date.replace("Z", "+00:00")
                    )
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

                if start_date > end_date:
                    raise ValueError("Start date cannot be after end date")

            # Prepare project data
            project = Project(
                project_name=project_data["project_name"][:100],  # Limit length
                description=project_data.get("description", ""),
                start_date=start_date,
                end_date=end_date,
                status=project_data.get("status", ProjectStatus.PLANNING.value),
                priority=project_data.get("priority", ProjectPriority.MEDIUM.value),
                budget=project_data.get("budget"),
                client_name=project_data.get("client_name"),
                tags=project_data.get("tags"),
                created_by=user_id,
            )

            # Insert project
            query = """
            INSERT INTO Projects (
                ProjectName, Description, StartDate, EndDate, Status, Priority,
                Budget, ClientName, Tags, CreatedBy
            )
            OUTPUT INSERTED.ProjectID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                project.project_name,
                project.description,
                project.start_date,
                project.end_date,
                project.status,
                project.priority,
                project.budget,
                project.client_name,
                project.tags,
                project.created_by,
            )

            result = self.db_service.execute_query(query, params)
            project_id = result[0]["ProjectID"]

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
                     p.Status, p.Priority, p.Budget, p.ClientName, p.Tags, 
                     p.CreatedDate, p.CreatedBy, u.Username
            """

            result = self.db_service.execute_query(query, (project_id,))

            if result:
                project_data = result[0]
                project_data["completion_rate"] = self._calculate_completion_rate(
                    project_data
                )
                project_data["health_score"] = self._calculate_health_score(
                    project_data
                )
                project_data["is_overdue"] = self._is_project_overdue(project_data)
                return project_data

            return None

        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {str(e)}")
            raise DatabaseException(f"Project retrieval failed: {str(e)}")

    @cached_query("all_projects", ttl=300)
    def get_all_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all projects"""
        try:
            base_query = """
            SELECT 
                p.*,
                u.Username as CreatedByName,
                COUNT(t.TaskID) as TaskCount,
                COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as CompletedTasks,
                ISNULL(AVG(CAST(t.Progress as FLOAT)), 0) as AvgProgress
            FROM Projects p
            LEFT JOIN Users u ON p.CreatedBy = u.UserID
            LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
            """

            params = []

            if status:
                base_query += " WHERE p.Status = ?"
                params.append(status)

            base_query += """
            GROUP BY p.ProjectID, p.ProjectName, p.Description, p.StartDate, p.EndDate,
                     p.Status, p.Priority, p.Budget, p.ClientName, p.Tags, 
                     p.CreatedDate, p.CreatedBy, u.Username
            ORDER BY p.CreatedDate DESC
            """

            result = self.db_service.execute_query(base_query, tuple(params))

            # Enhance each project with additional data
            for project in result:
                project["completion_rate"] = self._calculate_completion_rate(project)
                project["health_score"] = self._calculate_health_score(project)
                project["is_overdue"] = self._is_project_overdue(project)

            return result

        except Exception as e:
            logger.error(f"Failed to get all projects: {str(e)}")
            raise DatabaseException(f"Project retrieval failed: {str(e)}")

    @with_db_transaction
    def update_project(
        self, project_id: int, project_data: Dict[str, Any], user_id: int
    ) -> bool:
        """Update existing project"""
        try:
            # Validate project exists
            existing_project = self.get_project(project_id)
            if not existing_project:
                raise ValueError("Project does not exist")

            # Build update query dynamically
            update_fields = []
            params = []

            # Fields that can be updated
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
            }

            for field_key, db_field in updatable_fields.items():
                if field_key in project_data:
                    value = project_data[field_key]

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
            UPDATE Projects 
            SET {', '.join(update_fields)}
            WHERE ProjectID = ?
            """
            params.append(project_id)

            self.db_service.execute_query(query, tuple(params), fetch=False)

            # Clear cache
            self.db_service.clear_cache("projects_")

            logger.info(f"Project {project_id} updated successfully by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {str(e)}")
            raise DatabaseException(f"Project update failed: {str(e)}")

    @with_db_transaction
    def delete_project(self, project_id: int, user_id: int) -> bool:
        """Delete project"""
        try:
            # Check if project exists
            existing_project = self.get_project(project_id)
            if not existing_project:
                raise ValueError("Project does not exist")

            # Delete project (cascade will handle related records)
            query = "DELETE FROM Projects WHERE ProjectID = ?"
            self.db_service.execute_query(query, (project_id,), fetch=False)

            # Clear cache
            self.db_service.clear_cache("projects_")

            logger.info(f"Project {project_id} deleted by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {str(e)}")
            raise DatabaseException(f"Project deletion failed: {str(e)}")

    def get_project_analytics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive project analytics"""
        try:
            base_query = """
            SELECT 
                Status,
                Priority,
                Budget,
                StartDate,
                EndDate,
                CreatedDate
            FROM Projects
            WHERE 1=1
            """

            params = []

            if project_id:
                base_query += " AND ProjectID = ?"
                params.append(project_id)

            projects = self.db_service.execute_query(base_query, tuple(params))

            if not projects:
                return self._empty_analytics()

            # Calculate analytics
            analytics = {
                "total_projects": len(projects),
                "status_distribution": self._calculate_status_distribution(projects),
                "priority_distribution": self._calculate_priority_distribution(
                    projects
                ),
                "budget_analysis": self._calculate_budget_analysis(projects),
                "timeline_analysis": self._calculate_timeline_analysis(projects),
                "completion_metrics": self._calculate_completion_metrics(projects),
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to get project analytics: {str(e)}")
            raise DatabaseException(f"Analytics calculation failed: {str(e)}")

    def search_projects(
        self, search_query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search projects with advanced filtering"""
        try:
            base_query = """
            SELECT 
                p.*,
                u.Username as CreatedByName,
                COUNT(t.TaskID) as TaskCount
            FROM Projects p
            LEFT JOIN Users u ON p.CreatedBy = u.UserID
            LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
            WHERE (
                p.ProjectName LIKE ? OR 
                p.Description LIKE ? OR
                p.ClientName LIKE ? OR
                p.Tags LIKE ?
            )
            """

            search_pattern = f"%{search_query}%"
            params = [search_pattern, search_pattern, search_pattern, search_pattern]

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

                if filters.get("date_from"):
                    base_query += " AND p.CreatedDate >= ?"
                    params.append(filters["date_from"])

                if filters.get("date_to"):
                    base_query += " AND p.CreatedDate <= ?"
                    params.append(filters["date_to"])

            base_query += """
            GROUP BY p.ProjectID, p.ProjectName, p.Description, p.StartDate, p.EndDate,
                     p.Status, p.Priority, p.Budget, p.ClientName, p.Tags, 
                     p.CreatedDate, p.CreatedBy, u.Username
            ORDER BY p.CreatedDate DESC
            """

            result = self.db_service.execute_query(base_query, tuple(params))

            # Enhance search results
            for project in result:
                project["relevance_score"] = self._calculate_relevance_score(
                    project, search_query
                )

            # Sort by relevance
            result.sort(key=lambda x: x["relevance_score"], reverse=True)

            return result

        except Exception as e:
            logger.error(f"Failed to search projects: {str(e)}")
            raise DatabaseException(f"Project search failed: {str(e)}")

    # Helper methods
    def _calculate_completion_rate(self, project: Dict[str, Any]) -> float:
        """Calculate project completion rate"""
        task_count = project.get("TaskCount", 0)
        completed_tasks = project.get("CompletedTasks", 0)

        if task_count > 0:
            return round((completed_tasks / task_count) * 100, 2)
        return 0.0

    def _calculate_health_score(self, project: Dict[str, Any]) -> float:
        """Calculate project health score"""
        score = 0.0

        # Progress score (40%)
        avg_progress = project.get("AvgProgress", 0)
        score += (avg_progress / 100) * 40

        # Timeline performance (30%)
        if not self._is_project_overdue(project):
            score += 30

        # Task completion rate (30%)
        completion_rate = self._calculate_completion_rate(project)
        score += (completion_rate / 100) * 30

        return round(score, 2)

    def _is_project_overdue(self, project: Dict[str, Any]) -> bool:
        """Check if project is overdue"""
        end_date = project.get("EndDate")
        status = project.get("Status")

        if not end_date or status in ["Completed", "Cancelled"]:
            return False

        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        return datetime.now() > end_date

    def _calculate_status_distribution(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate status distribution"""
        distribution = {}
        for project in projects:
            status = project.get("Status", "Unknown")
            distribution[status] = distribution.get(status, 0) + 1
        return distribution

    def _calculate_priority_distribution(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate priority distribution"""
        distribution = {}
        for project in projects:
            priority = project.get("Priority", "Unknown")
            distribution[priority] = distribution.get(priority, 0) + 1
        return distribution

    def _calculate_budget_analysis(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate budget analysis"""
        budgets = [p.get("Budget", 0) for p in projects if p.get("Budget")]

        if not budgets:
            return {
                "total_budget": 0,
                "avg_budget": 0,
                "max_budget": 0,
                "min_budget": 0,
            }

        return {
            "total_budget": sum(budgets),
            "avg_budget": sum(budgets) / len(budgets),
            "max_budget": max(budgets),
            "min_budget": min(budgets),
        }

    def _calculate_timeline_analysis(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate timeline analysis"""
        now = datetime.now()

        overdue_projects = len([p for p in projects if self._is_project_overdue(p)])
        upcoming_deadlines = len(
            [
                p
                for p in projects
                if p.get("EndDate")
                and isinstance(p["EndDate"], datetime)
                and p["EndDate"] > now
                and (p["EndDate"] - now).days <= 7
            ]
        )

        return {
            "overdue_projects": overdue_projects,
            "upcoming_deadlines": upcoming_deadlines,
            "total_projects": len(projects),
        }

    def _calculate_completion_metrics(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate completion metrics"""
        completed_projects = len(
            [p for p in projects if p.get("Status") == "Completed"]
        )
        in_progress_projects = len(
            [p for p in projects if p.get("Status") == "In Progress"]
        )

        return {
            "completed_projects": completed_projects,
            "in_progress_projects": in_progress_projects,
            "completion_percentage": (
                (completed_projects / len(projects) * 100) if projects else 0
            ),
        }

    def _calculate_relevance_score(
        self, project: Dict[str, Any], search_query: str
    ) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = search_query.lower()

        # Project name match (highest weight)
        project_name = (project.get("ProjectName") or "").lower()
        if query_lower in project_name:
            score += 10.0
            if project_name.startswith(query_lower):
                score += 5.0

        # Description match
        description = (project.get("Description") or "").lower()
        if query_lower in description:
            score += 5.0

        # Client name match
        client_name = (project.get("ClientName") or "").lower()
        if query_lower in client_name:
            score += 3.0

        # Tags match
        tags = (project.get("Tags") or "").lower()
        if query_lower in tags:
            score += 3.0

        return score

    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            "total_projects": 0,
            "status_distribution": {},
            "priority_distribution": {},
            "budget_analysis": {
                "total_budget": 0,
                "avg_budget": 0,
                "max_budget": 0,
                "min_budget": 0,
            },
            "timeline_analysis": {
                "overdue_projects": 0,
                "upcoming_deadlines": 0,
                "total_projects": 0,
            },
            "completion_metrics": {
                "completed_projects": 0,
                "in_progress_projects": 0,
                "completion_percentage": 0,
            },
        }


# Global project service instance
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
