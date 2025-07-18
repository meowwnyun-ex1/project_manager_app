#!/usr/bin/env python3
"""
modules/projects.py
SDX Project Manager - Complete Enterprise Project Management System
Advanced project lifecycle management with portfolio analytics, resource optimization, and strategic alignment
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re
from decimal import Decimal

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Project status with complete workflow support"""

    PLANNING = "Planning"
    ACTIVE = "Active"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ARCHIVED = "Archived"


class ProjectPriority(Enum):
    """Strategic project priorities"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
    STRATEGIC = "Strategic"


class ProjectType(Enum):
    """Project classification for portfolio management"""

    DEVELOPMENT = "Development"
    MAINTENANCE = "Maintenance"
    RESEARCH = "Research"
    INFRASTRUCTURE = "Infrastructure"
    COMPLIANCE = "Compliance"
    INNOVATION = "Innovation"


class ProjectCategory(Enum):
    """Business category classification"""

    AUTOMOTIVE = "Automotive"
    IOT = "IoT"
    AI_ML = "AI/ML"
    ROBOTICS = "Robotics"
    INFRASTRUCTURE = "Infrastructure"
    DIGITAL_TRANSFORMATION = "Digital Transformation"


class RiskLevel(Enum):
    """Project risk assessment levels"""

    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


@dataclass
class ProjectMetrics:
    """Comprehensive project performance metrics"""

    budget_allocated: Decimal = Decimal("0")
    budget_spent: Decimal = Decimal("0")
    budget_remaining: Decimal = Decimal("0")
    budget_variance: float = 0.0

    progress_percentage: float = 0.0
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_in_progress: int = 0
    tasks_overdue: int = 0

    team_size: int = 0
    team_utilization: float = 0.0
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    efficiency_ratio: float = 0.0

    milestone_completion: float = 0.0
    schedule_variance: int = 0  # days
    risk_score: float = 0.0
    quality_score: float = 0.0


@dataclass
class ProjectStakeholder:
    """Project stakeholder information"""

    user_id: int
    role: str  # Project Manager, Sponsor, Team Member, Client
    responsibility: str
    authority_level: str  # High, Medium, Low
    communication_preference: str
    added_date: datetime = None


@dataclass
class ProjectMilestone:
    """Project milestone with dependencies"""

    id: Optional[int] = None
    project_id: int = None
    name: str = ""
    description: str = ""
    due_date: date = None
    completion_date: Optional[date] = None
    status: str = "Pending"  # Pending, In Progress, Completed, Delayed
    deliverables: List[str] = None
    dependencies: List[int] = None  # Milestone IDs
    budget_allocation: Decimal = Decimal("0")
    created_by: int = None
    created_at: datetime = None


@dataclass
class ProjectRisk:
    """Project risk assessment and mitigation"""

    id: Optional[int] = None
    project_id: int = None
    risk_category: str = ""  # Technical, Schedule, Budget, Resource, External
    description: str = ""
    probability: float = 0.0  # 0-1
    impact: float = 0.0  # 0-1
    risk_score: float = 0.0  # probability * impact
    mitigation_strategy: str = ""
    contingency_plan: str = ""
    owner_id: int = None
    status: str = "Open"  # Open, Mitigated, Closed
    created_at: datetime = None
    updated_at: datetime = None


class ProjectManager:
    """Comprehensive Enterprise Project Management System"""

    def __init__(self, db_manager):
        self.db = db_manager

    # =============================================================================
    # Core Project CRUD Operations
    # =============================================================================

    def create_project(
        self, project_data: Dict[str, Any], created_by: int
    ) -> Dict[str, Any]:
        """Create new project with comprehensive setup"""
        try:
            # Validate required fields
            required_fields = [
                "Name",
                "Description",
                "StartDate",
                "EndDate",
                "ProjectManager",
            ]
            for field in required_fields:
                if field not in project_data or not project_data[field]:
                    raise ValueError(f"Required field missing: {field}")

            # Set defaults
            project_data.update(
                {
                    "Status": project_data.get("Status", ProjectStatus.PLANNING.value),
                    "Priority": project_data.get(
                        "Priority", ProjectPriority.MEDIUM.value
                    ),
                    "Type": project_data.get("Type", ProjectType.DEVELOPMENT.value),
                    "Category": project_data.get(
                        "Category", ProjectCategory.DEVELOPMENT.value
                    ),
                    "Budget": project_data.get("Budget", 0),
                    "RiskLevel": project_data.get("RiskLevel", RiskLevel.MEDIUM.value),
                    "CreatedBy": created_by,
                    "CreatedAt": datetime.now(),
                    "UpdatedAt": datetime.now(),
                }
            )

            # Generate project code if not provided
            if "ProjectCode" not in project_data:
                project_data["ProjectCode"] = self._generate_project_code(
                    project_data.get("Category", "DEV"),
                    project_data.get("Type", "PROJ"),
                )

            # Insert project
            query = """
                INSERT INTO Projects (
                    ProjectCode, Name, Description, StartDate, EndDate, 
                    Status, Priority, Type, Category, Budget, RiskLevel,
                    ProjectManager, CreatedBy, CreatedAt, UpdatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = [
                project_data["ProjectCode"],
                project_data["Name"],
                project_data["Description"],
                project_data["StartDate"],
                project_data["EndDate"],
                project_data["Status"],
                project_data["Priority"],
                project_data["Type"],
                project_data["Category"],
                project_data["Budget"],
                project_data["RiskLevel"],
                project_data["ProjectManager"],
                project_data["CreatedBy"],
                project_data["CreatedAt"],
                project_data["UpdatedAt"],
            ]

            project_id = self.db.execute_query(query, params, return_id=True)

            # Create initial project setup
            self._initialize_project_setup(project_id, created_by)

            # Log activity
            self._log_project_activity(
                project_id,
                created_by,
                "PROJECT_CREATED",
                f"Project '{project_data['Name']}' created",
            )

            return self.get_project_by_id(project_id)

        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            raise

    def get_project_by_id(
        self, project_id: int, include_metrics: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get project with comprehensive details"""
        try:
            query = """
                SELECT p.*, 
                       pm.FirstName + ' ' + pm.LastName as ProjectManagerName,
                       cb.FirstName + ' ' + cb.LastName as CreatedByName
                FROM Projects p
                LEFT JOIN Users pm ON p.ProjectManager = pm.UserID
                LEFT JOIN Users cb ON p.CreatedBy = cb.UserID
                WHERE p.ProjectID = ?
            """

            result = self.db.fetch_one(query, [project_id])
            if not result:
                return None

            project = dict(result)

            if include_metrics:
                # Add comprehensive metrics
                project["Metrics"] = self.get_project_metrics(project_id)
                project["TeamMembers"] = self.get_project_team_members(project_id)
                project["Milestones"] = self.get_project_milestones(project_id)
                project["Risks"] = self.get_project_risks(project_id)
                project["RecentActivity"] = self.get_project_activity(
                    project_id, limit=10
                )

            return project

        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {str(e)}")
            return None

    def update_project(
        self, project_id: int, updates: Dict[str, Any], updated_by: int
    ) -> bool:
        """Update project with audit trail"""
        try:
            # Get current project for comparison
            current_project = self.get_project_by_id(project_id, include_metrics=False)
            if not current_project:
                raise ValueError(f"Project {project_id} not found")

            # Build update query dynamically
            set_clauses = []
            params = []

            allowed_fields = [
                "Name",
                "Description",
                "StartDate",
                "EndDate",
                "Status",
                "Priority",
                "Type",
                "Category",
                "Budget",
                "RiskLevel",
                "ProjectManager",
                "CompletionPercentage",
            ]

            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)

            if not set_clauses:
                return False

            # Add audit fields
            set_clauses.extend(["UpdatedBy = ?", "UpdatedAt = ?"])
            params.extend([updated_by, datetime.now()])
            params.append(project_id)

            query = f"UPDATE Projects SET {', '.join(set_clauses)} WHERE ProjectID = ?"

            self.db.execute_query(query, params)

            # Log changes
            self._log_project_changes(project_id, current_project, updates, updated_by)

            return True

        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {str(e)}")
            return False

    def delete_project(self, project_id: int, deleted_by: int) -> bool:
        """Soft delete project with cascade handling"""
        try:
            # Check if project can be deleted
            if not self._can_delete_project(project_id):
                raise ValueError("Project cannot be deleted - has active dependencies")

            # Archive related data
            self._archive_project_data(project_id)

            # Soft delete
            query = """
                UPDATE Projects 
                SET Status = 'Archived', 
                    UpdatedBy = ?, 
                    UpdatedAt = ?,
                    DeletedAt = ?
                WHERE ProjectID = ?
            """

            self.db.execute_query(
                query, [deleted_by, datetime.now(), datetime.now(), project_id]
            )

            # Log activity
            self._log_project_activity(
                project_id,
                deleted_by,
                "PROJECT_DELETED",
                "Project archived and deleted",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {str(e)}")
            return False

    # =============================================================================
    # Project Listing and Search
    # =============================================================================

    def get_projects_list(
        self, filters: Dict[str, Any] = None, page: int = 1, page_size: int = 50
    ) -> Dict[str, Any]:
        """Get paginated projects list with advanced filtering"""
        try:
            # Build WHERE clause
            where_conditions = ["p.Status != 'Archived'"]
            params = []

            if filters:
                if filters.get("status"):
                    where_conditions.append("p.Status = ?")
                    params.append(filters["status"])

                if filters.get("priority"):
                    where_conditions.append("p.Priority = ?")
                    params.append(filters["priority"])

                if filters.get("category"):
                    where_conditions.append("p.Category = ?")
                    params.append(filters["category"])

                if filters.get("project_manager"):
                    where_conditions.append("p.ProjectManager = ?")
                    params.append(filters["project_manager"])

                if filters.get("search"):
                    search_term = f"%{filters['search']}%"
                    where_conditions.append(
                        "(p.Name LIKE ? OR p.Description LIKE ? OR p.ProjectCode LIKE ?)"
                    )
                    params.extend([search_term, search_term, search_term])

                if filters.get("date_range"):
                    start_date, end_date = filters["date_range"]
                    where_conditions.append("p.StartDate BETWEEN ? AND ?")
                    params.extend([start_date, end_date])

            where_clause = "WHERE " + " AND ".join(where_conditions)

            # Count total records
            count_query = f"""
                SELECT COUNT(*) as total
                FROM Projects p
                {where_clause}
            """
            total_count = self.db.fetch_one(count_query, params)["total"]

            # Get paginated results
            offset = (page - 1) * page_size
            query = f"""
                SELECT p.ProjectID, p.ProjectCode, p.Name, p.Description, 
                       p.StartDate, p.EndDate, p.Status, p.Priority, 
                       p.Category, p.Budget, p.CompletionPercentage,
                       pm.FirstName + ' ' + pm.LastName as ProjectManagerName,
                       (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID) as TaskCount,
                       (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID AND Status = 'Completed') as CompletedTasks,
                       p.CreatedAt, p.UpdatedAt
                FROM Projects p
                LEFT JOIN Users pm ON p.ProjectManager = pm.UserID
                {where_clause}
                ORDER BY p.Priority DESC, p.StartDate DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """

            params.extend([offset, page_size])
            projects = self.db.fetch_all(query, params)

            # Calculate additional metrics for each project
            for project in projects:
                project_dict = dict(project)
                project_dict["ProgressStatus"] = self._calculate_progress_status(
                    project_dict
                )
                project_dict["HealthScore"] = self._calculate_health_score(project_dict)
                project_dict["DaysRemaining"] = self._calculate_days_remaining(
                    project_dict["EndDate"]
                )

            return {
                "projects": [dict(p) for p in projects],
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size,
            }

        except Exception as e:
            logger.error(f"Failed to get projects list: {str(e)}")
            return {
                "projects": [],
                "total_count": 0,
                "page": 1,
                "page_size": page_size,
                "total_pages": 0,
            }

    # =============================================================================
    # Project Metrics and Analytics
    # =============================================================================

    def get_project_metrics(self, project_id: int) -> ProjectMetrics:
        """Get comprehensive project performance metrics"""
        try:
            metrics = ProjectMetrics()

            # Budget metrics
            project = self.get_project_by_id(project_id, include_metrics=False)
            if project:
                metrics.budget_allocated = Decimal(str(project.get("Budget", 0)))

                # Calculate spent budget from time tracking and expenses
                spent_query = """
                    SELECT COALESCE(SUM(Hours * HourlyRate), 0) as TotalSpent
                    FROM TimeTracking tt
                    JOIN Users u ON tt.UserID = u.UserID
                    WHERE tt.ProjectID = ?
                """
                spent_result = self.db.fetch_one(spent_query, [project_id])
                metrics.budget_spent = Decimal(str(spent_result.get("TotalSpent", 0)))
                metrics.budget_remaining = (
                    metrics.budget_allocated - metrics.budget_spent
                )

                if metrics.budget_allocated > 0:
                    metrics.budget_variance = float(
                        (metrics.budget_spent / metrics.budget_allocated - 1) * 100
                    )

            # Task metrics
            task_query = """
                SELECT 
                    COUNT(*) as TotalTasks,
                    SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as CompletedTasks,
                    SUM(CASE WHEN Status IN ('In Progress', 'Review', 'Testing') THEN 1 ELSE 0 END) as InProgressTasks,
                    SUM(CASE WHEN DueDate < GETDATE() AND Status != 'Completed' THEN 1 ELSE 0 END) as OverdueTasks,
                    SUM(COALESCE(EstimatedHours, 0)) as TotalEstimatedHours,
                    SUM(COALESCE(ActualHours, 0)) as TotalActualHours
                FROM Tasks 
                WHERE ProjectID = ?
            """
            task_result = self.db.fetch_one(task_query, [project_id])

            if task_result:
                metrics.tasks_total = task_result["TotalTasks"]
                metrics.tasks_completed = task_result["CompletedTasks"]
                metrics.tasks_in_progress = task_result["InProgressTasks"]
                metrics.tasks_overdue = task_result["OverdueTasks"]
                metrics.estimated_hours = task_result["TotalEstimatedHours"] or 0
                metrics.actual_hours = task_result["TotalActualHours"] or 0

                if metrics.tasks_total > 0:
                    metrics.progress_percentage = (
                        metrics.tasks_completed / metrics.tasks_total
                    ) * 100

                if metrics.estimated_hours > 0:
                    metrics.efficiency_ratio = (
                        metrics.actual_hours / metrics.estimated_hours
                    )

            # Team metrics
            team_query = """
                SELECT COUNT(DISTINCT UserID) as TeamSize
                FROM ProjectTeamMembers 
                WHERE ProjectID = ? AND Status = 'Active'
            """
            team_result = self.db.fetch_one(team_query, [project_id])
            metrics.team_size = team_result["TeamSize"] if team_result else 0

            # Milestone progress
            milestone_query = """
                SELECT 
                    COUNT(*) as TotalMilestones,
                    SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as CompletedMilestones
                FROM ProjectMilestones 
                WHERE ProjectID = ?
            """
            milestone_result = self.db.fetch_one(milestone_query, [project_id])
            if milestone_result and milestone_result["TotalMilestones"] > 0:
                metrics.milestone_completion = (
                    milestone_result["CompletedMilestones"]
                    / milestone_result["TotalMilestones"]
                ) * 100

            # Risk assessment
            risk_query = """
                SELECT AVG(RiskScore) as AvgRiskScore
                FROM ProjectRisks 
                WHERE ProjectID = ? AND Status = 'Open'
            """
            risk_result = self.db.fetch_one(risk_query, [project_id])
            metrics.risk_score = (
                risk_result["AvgRiskScore"]
                if risk_result and risk_result["AvgRiskScore"]
                else 0
            )

            # Calculate schedule variance
            if project:
                planned_progress = self._calculate_planned_progress(
                    project["StartDate"], project["EndDate"]
                )
                metrics.schedule_variance = int(
                    (metrics.progress_percentage - planned_progress)
                    * (
                        datetime.strptime(project["EndDate"], "%Y-%m-%d").date()
                        - datetime.strptime(project["StartDate"], "%Y-%m-%d").date()
                    ).days
                    / 100
                )

            return metrics

        except Exception as e:
            logger.error(f"Failed to get project metrics: {str(e)}")
            return ProjectMetrics()

    # =============================================================================
    # Project Team Management
    # =============================================================================

    def get_project_team_members(self, project_id: int) -> List[Dict[str, Any]]:
        """Get project team members with roles and metrics"""
        try:
            query = """
                SELECT ptm.*, u.FirstName, u.LastName, u.Email, u.Role as UserRole,
                       u.Department, u.HourlyRate,
                       (SELECT SUM(Hours) FROM TimeTracking 
                        WHERE ProjectID = ptm.ProjectID AND UserID = ptm.UserID) as TotalHours,
                       (SELECT COUNT(*) FROM Tasks 
                        WHERE ProjectID = ptm.ProjectID AND AssignedTo = ptm.UserID) as AssignedTasks,
                       (SELECT COUNT(*) FROM Tasks 
                        WHERE ProjectID = ptm.ProjectID AND AssignedTo = ptm.UserID 
                        AND Status = 'Completed') as CompletedTasks
                FROM ProjectTeamMembers ptm
                JOIN Users u ON ptm.UserID = u.UserID
                WHERE ptm.ProjectID = ? AND ptm.Status = 'Active'
                ORDER BY ptm.Role, u.LastName, u.FirstName
            """

            members = self.db.fetch_all(query, [project_id])
            return [dict(member) for member in members]

        except Exception as e:
            logger.error(
                f"Failed to get team members for project {project_id}: {str(e)}"
            )
            return []

    def add_team_member(
        self,
        project_id: int,
        user_id: int,
        role: str,
        allocation_percentage: float,
        added_by: int,
    ) -> bool:
        """Add team member to project"""
        try:
            # Check if already exists
            existing_query = """
                SELECT COUNT(*) as count 
                FROM ProjectTeamMembers 
                WHERE ProjectID = ? AND UserID = ? AND Status = 'Active'
            """
            existing = self.db.fetch_one(existing_query, [project_id, user_id])

            if existing["count"] > 0:
                # Update existing member
                update_query = """
                    UPDATE ProjectTeamMembers 
                    SET Role = ?, AllocationPercentage = ?, UpdatedAt = ?
                    WHERE ProjectID = ? AND UserID = ? AND Status = 'Active'
                """
                self.db.execute_query(
                    update_query,
                    [role, allocation_percentage, datetime.now(), project_id, user_id],
                )
            else:
                # Add new member
                insert_query = """
                    INSERT INTO ProjectTeamMembers 
                    (ProjectID, UserID, Role, AllocationPercentage, Status, AddedBy, AddedAt)
                    VALUES (?, ?, ?, ?, 'Active', ?, ?)
                """
                self.db.execute_query(
                    insert_query,
                    [
                        project_id,
                        user_id,
                        role,
                        allocation_percentage,
                        added_by,
                        datetime.now(),
                    ],
                )

            # Log activity
            user_info = self.db.fetch_one(
                "SELECT FirstName, LastName FROM Users WHERE UserID = ?", [user_id]
            )
            user_name = (
                f"{user_info['FirstName']} {user_info['LastName']}"
                if user_info
                else f"User {user_id}"
            )

            self._log_project_activity(
                project_id,
                added_by,
                "TEAM_MEMBER_ADDED",
                f"Added {user_name} as {role}",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to add team member: {str(e)}")
            return False

    # =============================================================================
    # Project Milestones
    # =============================================================================

    def get_project_milestones(self, project_id: int) -> List[Dict[str, Any]]:
        """Get project milestones with progress tracking"""
        try:
            query = """
                SELECT pm.*, 
                       u.FirstName + ' ' + u.LastName as CreatedByName,
                       (SELECT COUNT(*) FROM Tasks WHERE MilestoneID = pm.MilestoneID) as TaskCount,
                       (SELECT COUNT(*) FROM Tasks WHERE MilestoneID = pm.MilestoneID AND Status = 'Completed') as CompletedTasks
                FROM ProjectMilestones pm
                LEFT JOIN Users u ON pm.CreatedBy = u.UserID
                WHERE pm.ProjectID = ?
                ORDER BY pm.DueDate, pm.Name
            """

            milestones = self.db.fetch_all(query, [project_id])

            # Add calculated fields
            for milestone in milestones:
                milestone_dict = dict(milestone)
                milestone_dict["ProgressPercentage"] = (
                    self._calculate_milestone_progress(milestone_dict)
                )
                milestone_dict["IsOverdue"] = self._is_milestone_overdue(milestone_dict)
                milestone_dict["DaysRemaining"] = self._calculate_days_remaining(
                    milestone_dict["DueDate"]
                )

            return [dict(m) for m in milestones]

        except Exception as e:
            logger.error(f"Failed to get milestones for project {project_id}: {str(e)}")
            return []

    def create_milestone(self, milestone_data: Dict[str, Any], created_by: int) -> int:
        """Create project milestone"""
        try:
            query = """
                INSERT INTO ProjectMilestones 
                (ProjectID, Name, Description, DueDate, Status, BudgetAllocation, CreatedBy, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = [
                milestone_data["ProjectID"],
                milestone_data["Name"],
                milestone_data.get("Description", ""),
                milestone_data["DueDate"],
                milestone_data.get("Status", "Pending"),
                milestone_data.get("BudgetAllocation", 0),
                created_by,
                datetime.now(),
            ]

            milestone_id = self.db.execute_query(query, params, return_id=True)

            # Log activity
            self._log_project_activity(
                milestone_data["ProjectID"],
                created_by,
                "MILESTONE_CREATED",
                f"Created milestone: {milestone_data['Name']}",
            )

            return milestone_id

        except Exception as e:
            logger.error(f"Failed to create milestone: {str(e)}")
            raise

    # =============================================================================
    # Project Risks
    # =============================================================================

    def get_project_risks(self, project_id: int) -> List[Dict[str, Any]]:
        """Get project risks with current status"""
        try:
            query = """
                SELECT pr.*, 
                       u.FirstName + ' ' + u.LastName as OwnerName,
                       cb.FirstName + ' ' + cb.LastName as CreatedByName
                FROM ProjectRisks pr
                LEFT JOIN Users u ON pr.OwnerID = u.UserID
                LEFT JOIN Users cb ON pr.CreatedBy = cb.UserID
                WHERE pr.ProjectID = ?
                ORDER BY pr.RiskScore DESC, pr.CreatedAt DESC
            """

            risks = self.db.fetch_all(query, [project_id])
            return [dict(risk) for risk in risks]

        except Exception as e:
            logger.error(f"Failed to get risks for project {project_id}: {str(e)}")
            return []

    def create_risk(self, risk_data: Dict[str, Any], created_by: int) -> int:
        """Create project risk"""
        try:
            # Calculate risk score
            probability = risk_data.get("Probability", 0.5)
            impact = risk_data.get("Impact", 0.5)
            risk_score = probability * impact

            query = """
                INSERT INTO ProjectRisks 
                (ProjectID, RiskCategory, Description, Probability, Impact, RiskScore,
                 MitigationStrategy, ContingencyPlan, OwnerID, Status, CreatedBy, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = [
                risk_data["ProjectID"],
                risk_data.get("RiskCategory", "Technical"),
                risk_data["Description"],
                probability,
                impact,
                risk_score,
                risk_data.get("MitigationStrategy", ""),
                risk_data.get("ContingencyPlan", ""),
                risk_data.get("OwnerID"),
                risk_data.get("Status", "Open"),
                created_by,
                datetime.now(),
            ]

            risk_id = self.db.execute_query(query, params, return_id=True)

            # Log activity
            self._log_project_activity(
                risk_data["ProjectID"],
                created_by,
                "RISK_CREATED",
                f"Created risk: {risk_data['Description'][:50]}...",
            )

            return risk_id

        except Exception as e:
            logger.error(f"Failed to create risk: {str(e)}")
            raise

    # =============================================================================
    # Portfolio Analytics
    # =============================================================================

    def get_portfolio_overview(self) -> Dict[str, Any]:
        """Get comprehensive portfolio overview"""
        try:
            overview = {}

            # Project counts by status
            status_query = """
                SELECT Status, COUNT(*) as Count
                FROM Projects 
                WHERE Status != 'Archived'
                GROUP BY Status
            """
            overview["project_counts"] = {
                row["Status"]: row["Count"] for row in self.db.fetch_all(status_query)
            }

            # Budget summary
            budget_query = """
                SELECT 
                    SUM(Budget) as TotalBudget,
                    AVG(CompletionPercentage) as AvgProgress,
                    COUNT(*) as TotalProjects
                FROM Projects 
                WHERE Status != 'Archived'
            """
            budget_result = self.db.fetch_one(budget_query)
            overview["budget_summary"] = dict(budget_result) if budget_result else {}

            # Risk distribution
            risk_query = """
                SELECT RiskLevel, COUNT(*) as Count
                FROM Projects 
                WHERE Status NOT IN ('Completed', 'Archived')
                GROUP BY RiskLevel
            """
            overview["risk_distribution"] = {
                row["RiskLevel"]: row["Count"] for row in self.db.fetch_all(risk_query)
            }

            # Recent activity
            activity_query = """
                SELECT TOP 10 * FROM ProjectActivity 
                ORDER BY ActivityDate DESC
            """
            overview["recent_activity"] = [
                dict(row) for row in self.db.fetch_all(activity_query)
            ]

            return overview

        except Exception as e:
            logger.error(f"Failed to get portfolio overview: {str(e)}")
            return {}

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _generate_project_code(self, category: str, project_type: str) -> str:
        """Generate unique project code"""
        try:
            prefix = f"{category[:3].upper()}-{project_type[:3].upper()}"
            year = datetime.now().year

            # Get next sequence number
            query = """
                SELECT COUNT(*) + 1 as NextNum
                FROM Projects 
                WHERE ProjectCode LIKE ? AND YEAR(CreatedAt) = ?
            """
            result = self.db.fetch_one(query, [f"{prefix}-{year}%", year])
            next_num = result["NextNum"] if result else 1

            return f"{prefix}-{year}-{next_num:03d}"

        except Exception as e:
            logger.error(f"Failed to generate project code: {str(e)}")
            return f"PROJ-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _initialize_project_setup(self, project_id: int, created_by: int):
        """Initialize default project setup"""
        try:
            # Create default milestones
            default_milestones = [
                {
                    "Name": "Project Kickoff",
                    "Description": "Project initiation and planning",
                    "Status": "Pending",
                },
                {
                    "Name": "Design Phase",
                    "Description": "System design and architecture",
                    "Status": "Pending",
                },
                {
                    "Name": "Development Phase",
                    "Description": "Core development and implementation",
                    "Status": "Pending",
                },
                {
                    "Name": "Testing Phase",
                    "Description": "Quality assurance and testing",
                    "Status": "Pending",
                },
                {
                    "Name": "Deployment",
                    "Description": "Production deployment and go-live",
                    "Status": "Pending",
                },
            ]

            for i, milestone in enumerate(default_milestones):
                milestone_data = {
                    "ProjectID": project_id,
                    "Name": milestone["Name"],
                    "Description": milestone["Description"],
                    "DueDate": (datetime.now() + timedelta(weeks=(i + 1) * 2)).date(),
                    "Status": milestone["Status"],
                }
                self.create_milestone(milestone_data, created_by)

            # Add project manager as team member
            project = self.get_project_by_id(project_id, include_metrics=False)
            if project and project.get("ProjectManager"):
                self.add_team_member(
                    project_id,
                    project["ProjectManager"],
                    "Project Manager",
                    100.0,
                    created_by,
                )

        except Exception as e:
            logger.error(f"Failed to initialize project setup: {str(e)}")

    def _can_delete_project(self, project_id: int) -> bool:
        """Check if project can be safely deleted"""
        try:
            # Check for active tasks
            task_count = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM Tasks WHERE ProjectID = ? AND Status NOT IN ('Completed', 'Cancelled')",
                [project_id],
            )

            if task_count["count"] > 0:
                return False

            # Check for time tracking entries
            time_count = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM TimeTracking WHERE ProjectID = ?",
                [project_id],
            )

            # Allow deletion but archive time tracking
            return True

        except Exception as e:
            logger.error(f"Failed to check project deletion eligibility: {str(e)}")
            return False

    def _archive_project_data(self, project_id: int):
        """Archive project-related data before deletion"""
        try:
            # Archive tasks
            self.db.execute_query(
                "UPDATE Tasks SET Status = 'Archived' WHERE ProjectID = ? AND Status != 'Completed'",
                [project_id],
            )

            # Archive team memberships
            self.db.execute_query(
                "UPDATE ProjectTeamMembers SET Status = 'Archived' WHERE ProjectID = ?",
                [project_id],
            )

        except Exception as e:
            logger.error(f"Failed to archive project data: {str(e)}")

    def _log_project_activity(
        self, project_id: int, user_id: int, activity_type: str, description: str
    ):
        """Log project activity for audit trail"""
        try:
            query = """
                INSERT INTO ProjectActivity 
                (ProjectID, UserID, ActivityType, Description, ActivityDate)
                VALUES (?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query, [project_id, user_id, activity_type, description, datetime.now()]
            )

        except Exception as e:
            logger.error(f"Failed to log project activity: {str(e)}")

    def _log_project_changes(
        self, project_id: int, old_data: Dict, new_data: Dict, changed_by: int
    ):
        """Log detailed project changes"""
        try:
            changes = []
            for field, new_value in new_data.items():
                old_value = old_data.get(field)
                if old_value != new_value:
                    changes.append(f"{field}: '{old_value}' → '{new_value}'")

            if changes:
                description = f"Updated: {', '.join(changes)}"
                self._log_project_activity(
                    project_id, changed_by, "PROJECT_UPDATED", description
                )

        except Exception as e:
            logger.error(f"Failed to log project changes: {str(e)}")

    def _calculate_progress_status(self, project: Dict[str, Any]) -> str:
        """Calculate project progress status"""
        try:
            completion = project.get("CompletionPercentage", 0)
            end_date = datetime.strptime(project["EndDate"], "%Y-%m-%d").date()
            today = datetime.now().date()

            if completion >= 100:
                return "Completed"
            elif today > end_date:
                return "Overdue"
            elif completion >= 75:
                return "On Track"
            elif completion >= 50:
                return "At Risk"
            else:
                return "Behind Schedule"

        except Exception:
            return "Unknown"

    def _calculate_health_score(self, project: Dict[str, Any]) -> float:
        """Calculate project health score (0-100)"""
        try:
            score = 0

            # Progress vs timeline (40%)
            completion = project.get("CompletionPercentage", 0)
            planned_progress = self._calculate_planned_progress(
                project["StartDate"], project["EndDate"]
            )
            progress_score = (
                min(100, (completion / max(planned_progress, 1)) * 100)
                if planned_progress > 0
                else 0
            )
            score += progress_score * 0.4

            # Task completion rate (30%)
            if project.get("TaskCount", 0) > 0:
                task_score = (
                    project.get("CompletedTasks", 0) / project["TaskCount"]
                ) * 100
                score += task_score * 0.3

            # Schedule adherence (20%)
            end_date = datetime.strptime(project["EndDate"], "%Y-%m-%d").date()
            today = datetime.now().date()
            if today <= end_date:
                score += 20  # On time

            # Budget (10%) - assume healthy if no budget overrun
            score += 10

            return min(100, max(0, score))

        except Exception:
            return 50.0  # Default average score

    def _calculate_planned_progress(self, start_date: str, end_date: str) -> float:
        """Calculate planned progress percentage based on timeline"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            today = datetime.now().date()

            if today <= start:
                return 0.0
            elif today >= end:
                return 100.0
            else:
                total_days = (end - start).days
                elapsed_days = (today - start).days
                return (elapsed_days / total_days) * 100 if total_days > 0 else 0.0

        except Exception:
            return 0.0

    def _calculate_days_remaining(self, end_date_str: str) -> int:
        """Calculate days remaining until end date"""
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (end_date - today).days
        except Exception:
            return 0

    def _calculate_milestone_progress(self, milestone: Dict[str, Any]) -> float:
        """Calculate milestone progress percentage"""
        try:
            if milestone["Status"] == "Completed":
                return 100.0

            task_count = milestone.get("TaskCount", 0)
            completed_tasks = milestone.get("CompletedTasks", 0)

            if task_count > 0:
                return (completed_tasks / task_count) * 100
            else:
                # Base on status
                status_progress = {
                    "Pending": 0,
                    "In Progress": 50,
                    "Completed": 100,
                    "Delayed": 25,
                }
                return status_progress.get(milestone["Status"], 0)

        except Exception:
            return 0.0

    def _is_milestone_overdue(self, milestone: Dict[str, Any]) -> bool:
        """Check if milestone is overdue"""
        try:
            if milestone["Status"] == "Completed":
                return False

            due_date = datetime.strptime(milestone["DueDate"], "%Y-%m-%d").date()
            return datetime.now().date() > due_date

        except Exception:
            return False

    def get_project_activity(
        self, project_id: int, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get project activity log"""
        try:
            query = """
                SELECT pa.*, u.FirstName + ' ' + u.LastName as UserName
                FROM ProjectActivity pa
                LEFT JOIN Users u ON pa.UserID = u.UserID
                WHERE pa.ProjectID = ?
                ORDER BY pa.ActivityDate DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """

            activities = self.db.fetch_all(query, [project_id, limit])
            return [dict(activity) for activity in activities]

        except Exception as e:
            logger.error(f"Failed to get project activity: {str(e)}")
            return []
