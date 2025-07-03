"""
modules/analytics.py
Analytics and reporting functionality
"""

import streamlit as st
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import plotly.express as px
import plotly.graph_objects as go

from utils.error_handler import handle_database_errors, safe_execute
from utils.performance_monitor import monitor_performance, cache_result

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """Analytics and reporting manager"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    @handle_database_errors
    @monitor_performance("get_dashboard_metrics")
    @cache_result(ttl_minutes=10)
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get key metrics for dashboard"""
        metrics = {}

        try:
            # Total projects
            metrics["total_projects"] = (
                self.db_manager.execute_scalar("SELECT COUNT(*) FROM Projects") or 0
            )

            # Active projects
            metrics["active_projects"] = (
                self.db_manager.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status = 'Active'"
                )
                or 0
            )

            # Completed projects
            metrics["completed_projects"] = (
                self.db_manager.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status = 'Completed'"
                )
                or 0
            )

            # Total tasks
            metrics["total_tasks"] = (
                self.db_manager.execute_scalar("SELECT COUNT(*) FROM Tasks") or 0
            )

            # Completed tasks
            metrics["completed_tasks"] = (
                self.db_manager.execute_scalar(
                    "SELECT COUNT(*) FROM Tasks WHERE Status = 'Done'"
                )
                or 0
            )

            # Overdue projects
            metrics["overdue_projects"] = (
                self.db_manager.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE EndDate < GETDATE() AND Status NOT IN ('Completed', 'Cancelled')"
                )
                or 0
            )

            # Total users
            metrics["total_users"] = (
                self.db_manager.execute_scalar(
                    "SELECT COUNT(*) FROM Users WHERE IsActive = 1"
                )
                or 0
            )

            # Budget totals
            budget_data = self.db_manager.execute_query(
                """
                SELECT 
                    SUM(Budget) as total_budget,
                    AVG(Budget) as avg_budget
                FROM Projects 
                WHERE Budget > 0
            """
            )

            if budget_data and budget_data[0]:
                metrics["total_budget"] = budget_data[0].get("total_budget", 0) or 0
                metrics["avg_budget"] = budget_data[0].get("avg_budget", 0) or 0
            else:
                metrics["total_budget"] = 0
                metrics["avg_budget"] = 0

            logger.info("Dashboard metrics retrieved successfully")

        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {str(e)}")
            # Return default metrics on error
            metrics = {
                "total_projects": 0,
                "active_projects": 0,
                "completed_projects": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "overdue_projects": 0,
                "total_users": 0,
                "total_budget": 0,
                "avg_budget": 0,
            }

        return metrics

    @handle_database_errors
    @cache_result(ttl_minutes=15)
    def get_project_status_distribution(self) -> List[Dict[str, Any]]:
        """Get project status distribution"""
        query = """
        SELECT Status, COUNT(*) as count
        FROM Projects
        GROUP BY Status
        ORDER BY count DESC
        """
        return self.db_manager.execute_query(query)

    @handle_database_errors
    @cache_result(ttl_minutes=15)
    def get_task_completion_rate(self) -> List[Dict[str, Any]]:
        """Get task completion rate by project"""
        query = """
        SELECT p.ProjectName,
               COUNT(t.TaskID) as TotalTasks,
               SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
               CASE 
                   WHEN COUNT(t.TaskID) > 0 
                   THEN CAST(SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) * 100.0 / COUNT(t.TaskID) as DECIMAL(5,2))
                   ELSE 0 
               END as CompletionRate
        FROM Projects p
        LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
        GROUP BY p.ProjectID, p.ProjectName
        HAVING COUNT(t.TaskID) > 0
        ORDER BY CompletionRate DESC
        """
        return self.db_manager.execute_query(query)

    @handle_database_errors
    def get_monthly_project_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly project creation trends"""
        query = """
        SELECT 
            FORMAT(CreatedDate, 'yyyy-MM') as month,
            COUNT(*) as projects_created,
            SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as projects_completed
        FROM Projects
        WHERE CreatedDate >= DATEADD(month, -?, GETDATE())
        GROUP BY FORMAT(CreatedDate, 'yyyy-MM')
        ORDER BY month
        """
        return self.db_manager.execute_query(query, (months,))

    @handle_database_errors
    def get_task_priority_distribution(self) -> List[Dict[str, Any]]:
        """Get task priority distribution"""
        query = """
        SELECT Priority, COUNT(*) as count
        FROM Tasks
        GROUP BY Priority
        ORDER BY 
            CASE Priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                WHEN 'Low' THEN 4 
                ELSE 5 
            END
        """
        return self.db_manager.execute_query(query)

    @handle_database_errors
    def get_user_productivity_stats(self) -> List[Dict[str, Any]]:
        """Get user productivity statistics"""
        query = """
        SELECT 
            u.FirstName + ' ' + u.LastName as UserName,
            COUNT(t.TaskID) as TotalTasks,
            SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
            SUM(ISNULL(t.ActualHours, 0)) as TotalHours,
            AVG(ISNULL(t.ActualHours, 0)) as AvgHours,
            CASE 
                WHEN COUNT(t.TaskID) > 0 
                THEN CAST(SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) * 100.0 / COUNT(t.TaskID) as DECIMAL(5,2))
                ELSE 0 
            END as CompletionRate
        FROM Users u
        LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
        WHERE u.IsActive = 1
        GROUP BY u.UserID, u.FirstName, u.LastName
        HAVING COUNT(t.TaskID) > 0
        ORDER BY CompletionRate DESC, TotalTasks DESC
        """
        return self.db_manager.execute_query(query)

    @handle_database_errors
    def get_project_budget_analysis(self) -> Dict[str, Any]:
        """Get project budget analysis"""
        query = """
        SELECT 
            COUNT(*) as total_projects,
            SUM(Budget) as total_budget,
            AVG(Budget) as avg_budget,
            MIN(Budget) as min_budget,
            MAX(Budget) as max_budget,
            STDEV(Budget) as budget_std_dev
        FROM Projects
        WHERE Budget > 0
        """

        result = self.db_manager.execute_query(query)

        if result and result[0]:
            return result[0]
        else:
            return {
                "total_projects": 0,
                "total_budget": 0,
                "avg_budget": 0,
                "min_budget": 0,
                "max_budget": 0,
                "budget_std_dev": 0,
            }

    @handle_database_errors
    def get_time_tracking_analysis(self) -> Dict[str, Any]:
        """Get time tracking analysis"""
        query = """
        SELECT 
            COUNT(*) as total_tasks_with_time,
            SUM(EstimatedHours) as total_estimated,
            SUM(ActualHours) as total_actual,
            AVG(EstimatedHours) as avg_estimated,
            AVG(ActualHours) as avg_actual,
            SUM(CASE WHEN ActualHours > EstimatedHours THEN 1 ELSE 0 END) as over_estimate_count,
            CASE 
                WHEN SUM(EstimatedHours) > 0 
                THEN (SUM(ActualHours) / SUM(EstimatedHours)) * 100 
                ELSE 0 
            END as time_accuracy_rate
        FROM Tasks
        WHERE EstimatedHours > 0 OR ActualHours > 0
        """

        result = self.db_manager.execute_query(query)

        if result and result[0]:
            return result[0]
        else:
            return {
                "total_tasks_with_time": 0,
                "total_estimated": 0,
                "total_actual": 0,
                "avg_estimated": 0,
                "avg_actual": 0,
                "over_estimate_count": 0,
                "time_accuracy_rate": 0,
            }

    @handle_database_errors
    def get_overdue_analysis(self) -> Dict[str, Any]:
        """Get overdue projects and tasks analysis"""
        # Overdue projects
        overdue_projects_query = """
        SELECT 
            ProjectID,
            ProjectName,
            EndDate,
            DATEDIFF(day, EndDate, GETDATE()) as DaysOverdue,
            Status,
            Priority
        FROM Projects
        WHERE EndDate < GETDATE() AND Status NOT IN ('Completed', 'Cancelled')
        ORDER BY DaysOverdue DESC
        """

        # Overdue tasks
        overdue_tasks_query = """
        SELECT 
            t.TaskID,
            t.TaskName,
            t.DueDate,
            DATEDIFF(day, t.DueDate, GETDATE()) as DaysOverdue,
            t.Status,
            t.Priority,
            p.ProjectName,
            u.FirstName + ' ' + u.LastName as AssignedToName
        FROM Tasks t
        LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
        LEFT JOIN Users u ON t.AssignedTo = u.UserID
        WHERE t.DueDate < GETDATE() AND t.Status != 'Done'
        ORDER BY DaysOverdue DESC
        """

        return {
            "overdue_projects": self.db_manager.execute_query(overdue_projects_query),
            "overdue_tasks": self.db_manager.execute_query(overdue_tasks_query),
        }

    @handle_database_errors
    def get_department_performance(self) -> List[Dict[str, Any]]:
        """Get performance by department"""
        query = """
        SELECT 
            u.Department,
            COUNT(DISTINCT u.UserID) as UserCount,
            COUNT(t.TaskID) as TotalTasks,
            SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
            COUNT(DISTINCT p.ProjectID) as ProjectsInvolved,
            SUM(ISNULL(t.ActualHours, 0)) as TotalHours,
            CASE 
                WHEN COUNT(t.TaskID) > 0 
                THEN CAST(SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) * 100.0 / COUNT(t.TaskID) as DECIMAL(5,2))
                ELSE 0 
            END as CompletionRate
        FROM Users u
        LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
        LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
        WHERE u.IsActive = 1 AND u.Department IS NOT NULL AND u.Department != ''
        GROUP BY u.Department
        ORDER BY CompletionRate DESC, TotalTasks DESC
        """
        return self.db_manager.execute_query(query)

    def generate_project_report(self, project_id: int) -> Dict[str, Any]:
        """Generate comprehensive project report"""
        try:
            report = {}

            # Project basic info
            project_query = """
            SELECT p.*, u.FirstName + ' ' + u.LastName as CreatorName
            FROM Projects p
            LEFT JOIN Users u ON p.CreatedBy = u.UserID
            WHERE p.ProjectID = ?
            """
            project_data = self.db_manager.execute_query(project_query, (project_id,))

            if not project_data:
                return {"error": "Project not found"}

            report["project_info"] = project_data[0]

            # Task statistics
            task_stats_query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN Status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                SUM(CASE WHEN DueDate < GETDATE() AND Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                SUM(ISNULL(EstimatedHours, 0)) as total_estimated_hours,
                SUM(ISNULL(ActualHours, 0)) as total_actual_hours,
                AVG(ISNULL(EstimatedHours, 0)) as avg_estimated_hours,
                AVG(ISNULL(ActualHours, 0)) as avg_actual_hours
            FROM Tasks
            WHERE ProjectID = ?
            """
            task_stats = self.db_manager.execute_query(task_stats_query, (project_id,))
            report["task_statistics"] = task_stats[0] if task_stats else {}

            # Task status distribution
            task_status_query = """
            SELECT Status, COUNT(*) as count
            FROM Tasks
            WHERE ProjectID = ?
            GROUP BY Status
            ORDER BY count DESC
            """
            report["task_status_distribution"] = self.db_manager.execute_query(
                task_status_query, (project_id,)
            )

            # Task priority distribution
            task_priority_query = """
            SELECT Priority, COUNT(*) as count
            FROM Tasks
            WHERE ProjectID = ?
            GROUP BY Priority
            ORDER BY 
                CASE Priority 
                    WHEN 'Critical' THEN 1 
                    WHEN 'High' THEN 2 
                    WHEN 'Medium' THEN 3 
                    WHEN 'Low' THEN 4 
                    ELSE 5 
                END
            """
            report["task_priority_distribution"] = self.db_manager.execute_query(
                task_priority_query, (project_id,)
            )

            # Team members
            team_query = """
            SELECT DISTINCT
                u.UserID,
                u.FirstName + ' ' + u.LastName as UserName,
                u.Department,
                COUNT(t.TaskID) as TaskCount,
                SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
                SUM(ISNULL(t.ActualHours, 0)) as TotalHours
            FROM Users u
            INNER JOIN Tasks t ON u.UserID = t.AssignedTo
            WHERE t.ProjectID = ?
            GROUP BY u.UserID, u.FirstName, u.LastName, u.Department
            ORDER BY TaskCount DESC
            """
            report["team_members"] = self.db_manager.execute_query(
                team_query, (project_id,)
            )

            # Timeline data
            timeline_query = """
            SELECT 
                TaskName,
                StartDate,
                DueDate,
                CompletedDate,
                Status,
                AssignedTo,
                u.FirstName + ' ' + u.LastName as AssignedToName
            FROM Tasks t
            LEFT JOIN Users u ON t.AssignedTo = u.UserID
            WHERE t.ProjectID = ?
            ORDER BY ISNULL(StartDate, CreatedDate)
            """
            report["timeline"] = self.db_manager.execute_query(
                timeline_query, (project_id,)
            )

            return report

        except Exception as e:
            logger.error(f"Failed to generate project report: {str(e)}")
            return {"error": str(e)}

    def export_analytics_data(
        self, report_type: str, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Export analytics data for external use"""
        try:
            if report_type == "projects_summary":
                return self._export_projects_summary(filters)
            elif report_type == "tasks_summary":
                return self._export_tasks_summary(filters)
            elif report_type == "user_productivity":
                return self.get_user_productivity_stats()
            elif report_type == "department_performance":
                return self.get_department_performance()
            else:
                return []

        except Exception as e:
            logger.error(f"Export failed for {report_type}: {str(e)}")
            return []

    def _export_projects_summary(
        self, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Export projects summary data"""
        query = """
        SELECT 
            p.ProjectID,
            p.ProjectName,
            p.Status,
            p.Priority,
            p.StartDate,
            p.EndDate,
            p.Budget,
            p.ClientName,
            u.FirstName + ' ' + u.LastName as ProjectManager,
            COUNT(t.TaskID) as TotalTasks,
            SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
            SUM(ISNULL(t.EstimatedHours, 0)) as TotalEstimatedHours,
            SUM(ISNULL(t.ActualHours, 0)) as TotalActualHours,
            CASE 
                WHEN COUNT(t.TaskID) > 0 
                THEN CAST(SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) * 100.0 / COUNT(t.TaskID) as DECIMAL(5,2))
                ELSE 0 
            END as CompletionRate
        FROM Projects p
        LEFT JOIN Users u ON p.CreatedBy = u.UserID
        LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
        GROUP BY p.ProjectID, p.ProjectName, p.Status, p.Priority, p.StartDate, p.EndDate, 
                 p.Budget, p.ClientName, u.FirstName, u.LastName
        ORDER BY p.CreatedDate DESC
        """
        return self.db_manager.execute_query(query)

    def _export_tasks_summary(
        self, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Export tasks summary data"""
        query = """
        SELECT 
            t.TaskID,
            t.TaskName,
            t.Status,
            t.Priority,
            t.StartDate,
            t.DueDate,
            t.CompletedDate,
            t.EstimatedHours,
            t.ActualHours,
            p.ProjectName,
            u1.FirstName + ' ' + u1.LastName as AssignedTo,
            u2.FirstName + ' ' + u2.LastName as CreatedBy,
            CASE 
                WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 'Yes'
                ELSE 'No'
            END as IsOverdue
        FROM Tasks t
        LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
        LEFT JOIN Users u1 ON t.AssignedTo = u1.UserID
        LEFT JOIN Users u2 ON t.CreatedBy = u2.UserID
        ORDER BY t.CreatedDate DESC
        """
        return self.db_manager.execute_query(query)
