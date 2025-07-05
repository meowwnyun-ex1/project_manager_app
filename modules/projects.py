#!/usr/bin/env python3
"""
modules/projects.py
Project Management System for SDX Project Manager
Complete CRUD operations and project tracking
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class ProjectManager:
    """Complete project management system"""

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_sample_data()

    def _ensure_sample_data(self):
        """Ensure sample projects exist for demo"""
        try:
            # Check if projects exist
            project_count = self.db.execute_scalar("SELECT COUNT(*) FROM Projects")

            if project_count == 0:
                # Create sample projects
                sample_projects = [
                    {
                        "name": "Website Redesign",
                        "description": "Complete redesign of company website with modern UI/UX",
                        "status": "Active",
                        "priority": "High",
                        "start_date": "2024-01-15",
                        "end_date": "2024-03-15",
                        "budget": 150000,
                        "manager_id": 1,
                    },
                    {
                        "name": "Mobile App Development",
                        "description": "Native mobile application for iOS and Android",
                        "status": "Active",
                        "priority": "Medium",
                        "start_date": "2024-02-01",
                        "end_date": "2024-06-01",
                        "budget": 300000,
                        "manager_id": 1,
                    },
                    {
                        "name": "Data Migration Project",
                        "description": "Migration of legacy data to new cloud infrastructure",
                        "status": "Completed",
                        "priority": "High",
                        "start_date": "2023-11-01",
                        "end_date": "2024-01-31",
                        "budget": 80000,
                        "manager_id": 1,
                    },
                ]

                for project in sample_projects:
                    self.create_project(project, create_by_system=True)

                logger.info("Sample projects created")

        except Exception as e:
            logger.error(f"Error ensuring sample data: {e}")

    def create_project(
        self, project_data: Dict[str, Any], create_by_system: bool = False
    ) -> Optional[int]:
        """Create new project"""
        try:
            query = """
                INSERT INTO Projects (
                    ProjectName, Description, Status, Priority, 
                    StartDate, EndDate, Budget, ProjectManagerID, CreatedBy
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            created_by = 1 if create_by_system else st.session_state.user["UserID"]

            result = self.db.execute_non_query(
                query,
                (
                    project_data["name"],
                    project_data["description"],
                    project_data["status"],
                    project_data["priority"],
                    project_data["start_date"],
                    project_data["end_date"],
                    project_data["budget"],
                    project_data["manager_id"],
                    created_by,
                ),
            )

            if result > 0:
                # Get the new project ID
                project_id = self.db.execute_scalar("SELECT @@IDENTITY")
                logger.info(f"Project created with ID: {project_id}")
                return project_id

            return None

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None

    def get_all_projects(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get all projects with optional filters"""
        try:
            base_query = """
                SELECT 
                    p.ProjectID,
                    p.ProjectName,
                    p.Description,
                    p.Status,
                    p.Priority,
                    p.StartDate,
                    p.EndDate,
                    p.Budget,
                    p.Progress,
                    u.FullName as ProjectManager,
                    p.CreatedDate,
                    DATEDIFF(day, GETDATE(), p.EndDate) as DaysRemaining
                FROM Projects p
                LEFT JOIN Users u ON p.ProjectManagerID = u.UserID
                WHERE 1=1
            """

            params = []

            # Apply filters
            if filters:
                if filters.get("status") and filters["status"] != "ทั้งหมด":
                    base_query += " AND p.Status = ?"
                    params.append(filters["status"])

                if filters.get("priority") and filters["priority"] != "ทั้งหมด":
                    base_query += " AND p.Priority = ?"
                    params.append(filters["priority"])

                if filters.get("search"):
                    base_query += " AND (p.ProjectName LIKE ? OR p.Description LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])

            base_query += " ORDER BY p.CreatedDate DESC"

            return self.db.execute_query(base_query, tuple(params) if params else None)

        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []

    def get_project_by_id(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            query = """
                SELECT 
                    p.*,
                    u.FullName as ProjectManager,
                    creator.FullName as CreatedByName
                FROM Projects p
                LEFT JOIN Users u ON p.ProjectManagerID = u.UserID
                LEFT JOIN Users creator ON p.CreatedBy = creator.UserID
                WHERE p.ProjectID = ?
            """

            result = self.db.execute_query(query, (project_id,))
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None

    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> bool:
        """Update project"""
        try:
            query = """
                UPDATE Projects 
                SET ProjectName = ?, Description = ?, Status = ?, Priority = ?,
                    StartDate = ?, EndDate = ?, Budget = ?, ProjectManagerID = ?,
                    Progress = ?, LastModifiedDate = GETDATE(), LastModifiedBy = ?
                WHERE ProjectID = ?
            """

            result = self.db.execute_non_query(
                query,
                (
                    project_data["name"],
                    project_data["description"],
                    project_data["status"],
                    project_data["priority"],
                    project_data["start_date"],
                    project_data["end_date"],
                    project_data["budget"],
                    project_data["manager_id"],
                    project_data.get("progress", 0),
                    st.session_state.user["UserID"],
                    project_id,
                ),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False

    def delete_project(self, project_id: int) -> bool:
        """Delete project (soft delete)"""
        try:
            # Check if project has tasks
            task_count = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Tasks WHERE ProjectID = ?", (project_id,)
            )

            if task_count > 0:
                # Soft delete - mark as cancelled
                result = self.db.execute_non_query(
                    "UPDATE Projects SET Status = 'Cancelled' WHERE ProjectID = ?",
                    (project_id,),
                )
            else:
                # Hard delete if no tasks
                result = self.db.execute_non_query(
                    "DELETE FROM Projects WHERE ProjectID = ?", (project_id,)
                )

            return result > 0

        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False

    def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        try:
            stats = {}

            # Total projects
            stats["total"] = (
                self.db.execute_scalar("SELECT COUNT(*) FROM Projects") or 0
            )

            # Projects by status
            status_data = self.db.execute_query(
                """
                SELECT Status, COUNT(*) as Count
                FROM Projects 
                GROUP BY Status
            """
            )
            stats["by_status"] = {row["Status"]: row["Count"] for row in status_data}

            # Active projects
            stats["active"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status = 'Active'"
                )
                or 0
            )

            # Completed projects
            stats["completed"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status = 'Completed'"
                )
                or 0
            )

            # Overdue projects
            stats["overdue"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Projects 
                WHERE EndDate < GETDATE() AND Status != 'Completed'
            """
                )
                or 0
            )

            # Average progress
            stats["avg_progress"] = (
                self.db.execute_scalar(
                    "SELECT AVG(CAST(Progress as FLOAT)) FROM Projects WHERE Status = 'Active'"
                )
                or 0
            )

            # Total budget
            stats["total_budget"] = (
                self.db.execute_scalar("SELECT SUM(Budget) FROM Projects") or 0
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting project statistics: {e}")
            return {}

    def get_project_timeline_data(self) -> List[Dict[str, Any]]:
        """Get data for timeline chart"""
        try:
            query = """
                SELECT 
                    ProjectName as project,
                    StartDate as start_date,
                    EndDate as end_date,
                    Status as status,
                    Progress
                FROM Projects
                WHERE Status != 'Cancelled'
                ORDER BY StartDate
            """

            return self.db.execute_query(query)

        except Exception as e:
            logger.error(f"Error getting timeline data: {e}")
            return []

    def get_project_progress_data(self) -> List[Dict[str, Any]]:
        """Get data for progress chart"""
        try:
            query = """
                SELECT 
                    ProjectName as name,
                    Progress as progress
                FROM Projects
                WHERE Status = 'Active'
                ORDER BY Progress DESC
            """

            return self.db.execute_query(query)

        except Exception as e:
            logger.error(f"Error getting progress data: {e}")
            return []

    def add_project_member(
        self, project_id: int, user_id: int, role: str = "Member"
    ) -> bool:
        """Add member to project"""
        try:
            # Check if already member
            existing = self.db.execute_scalar(
                """
                SELECT COUNT(*) FROM ProjectMembers 
                WHERE ProjectID = ? AND UserID = ?
            """,
                (project_id, user_id),
            )

            if existing > 0:
                return False  # Already a member

            result = self.db.execute_non_query(
                """
                INSERT INTO ProjectMembers (ProjectID, UserID, Role, JoinedDate)
                VALUES (?, ?, ?, GETDATE())
            """,
                (project_id, user_id, role),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error adding project member: {e}")
            return False

    def remove_project_member(self, project_id: int, user_id: int) -> bool:
        """Remove member from project"""
        try:
            result = self.db.execute_non_query(
                """
                DELETE FROM ProjectMembers 
                WHERE ProjectID = ? AND UserID = ?
            """,
                (project_id, user_id),
            )

            return result > 0

        except Exception as e:
            logger.error(f"Error removing project member: {e}")
            return False

    def get_project_members(self, project_id: int) -> List[Dict[str, Any]]:
        """Get project members"""
        try:
            query = """
                SELECT 
                    pm.UserID,
                    u.FullName,
                    u.Email,
                    pm.Role,
                    pm.JoinedDate
                FROM ProjectMembers pm
                JOIN Users u ON pm.UserID = u.UserID
                WHERE pm.ProjectID = ?
                ORDER BY pm.JoinedDate
            """

            return self.db.execute_query(query, (project_id,))

        except Exception as e:
            logger.error(f"Error getting project members: {e}")
            return []

    def update_project_progress(self, project_id: int, progress: int) -> bool:
        """Update project progress"""
        try:
            # Auto-complete if progress is 100%
            new_status = "Completed" if progress >= 100 else None

            if new_status:
                query = """
                    UPDATE Projects 
                    SET Progress = ?, Status = ?, LastModifiedDate = GETDATE()
                    WHERE ProjectID = ?
                """
                result = self.db.execute_non_query(
                    query, (progress, new_status, project_id)
                )
            else:
                query = """
                    UPDATE Projects 
                    SET Progress = ?, LastModifiedDate = GETDATE()
                    WHERE ProjectID = ?
                """
                result = self.db.execute_non_query(query, (progress, project_id))

            return result > 0

        except Exception as e:
            logger.error(f"Error updating project progress: {e}")
            return False

    def get_recent_projects(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent projects"""
        try:
            query = """
                SELECT TOP (?) 
                    ProjectID,
                    ProjectName,
                    Status,
                    Progress,
                    CreatedDate
                FROM Projects
                ORDER BY CreatedDate DESC
            """

            return self.db.execute_query(query, (limit,))

        except Exception as e:
            logger.error(f"Error getting recent projects: {e}")
            return []

    def search_projects(self, search_term: str) -> List[Dict[str, Any]]:
        """Search projects"""
        try:
            query = """
                SELECT 
                    ProjectID,
                    ProjectName,
                    Description,
                    Status,
                    Priority
                FROM Projects
                WHERE ProjectName LIKE ? OR Description LIKE ?
                ORDER BY ProjectName
            """

            search_pattern = f"%{search_term}%"
            return self.db.execute_query(query, (search_pattern, search_pattern))

        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return []

    def export_projects_data(self) -> pd.DataFrame:
        """Export projects data to DataFrame"""
        try:
            query = """
                SELECT 
                    p.ProjectID as 'รหัสโครงการ',
                    p.ProjectName as 'ชื่อโครงการ',
                    p.Description as 'รายละเอียด',
                    p.Status as 'สถานะ',
                    p.Priority as 'ความสำคัญ',
                    p.StartDate as 'วันที่เริ่ม',
                    p.EndDate as 'วันที่สิ้นสุด',
                    p.Budget as 'งบประมาณ',
                    p.Progress as 'ความคืบหน้า (%)',
                    u.FullName as 'ผู้จัดการโครงการ',
                    p.CreatedDate as 'วันที่สร้าง'
                FROM Projects p
                LEFT JOIN Users u ON p.ProjectManagerID = u.UserID
                ORDER BY p.CreatedDate DESC
            """

            data = self.db.execute_query(query)
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error exporting projects: {e}")
            return pd.DataFrame()
