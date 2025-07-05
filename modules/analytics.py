#!/usr/bin/env python3
"""
modules/analytics.py
Analytics Manager for SDX Project Manager
Data analysis and reporting functionality
"""

import streamlit as st
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """Analytics and reporting system"""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get key metrics for dashboard"""
        try:
            metrics = {}

            # Project metrics
            metrics["total_projects"] = (
                self.db.execute_scalar("SELECT COUNT(*) FROM Projects") or 0
            )

            metrics["active_projects"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status = 'Active'"
                )
                or 0
            )

            metrics["completed_projects"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Projects WHERE Status = 'Completed'"
                )
                or 0
            )

            # Task metrics
            metrics["total_tasks"] = (
                self.db.execute_scalar("SELECT COUNT(*) FROM Tasks") or 0
            )

            metrics["completed_tasks"] = (
                self.db.execute_scalar(
                    "SELECT COUNT(*) FROM Tasks WHERE Status = 'Done'"
                )
                or 0
            )

            metrics["overdue_tasks"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Tasks 
                WHERE DueDate < GETDATE() AND Status != 'Done'
            """
                )
                or 0
            )

            # User metrics
            metrics["active_users"] = (
                self.db.execute_scalar("SELECT COUNT(*) FROM Users WHERE IsActive = 1")
                or 0
            )

            # Calculate completion rate
            if metrics["total_tasks"] > 0:
                metrics["task_completion_rate"] = round(
                    (metrics["completed_tasks"] / metrics["total_tasks"]) * 100, 1
                )
            else:
                metrics["task_completion_rate"] = 0

            # Average project progress
            metrics["avg_project_progress"] = (
                self.db.execute_scalar(
                    """
                SELECT AVG(CAST(Progress as FLOAT)) 
                FROM Projects 
                WHERE Status = 'Active'
            """
                )
                or 0
            )

            return metrics

        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return {}

    def get_project_status_distribution(self) -> List[Dict[str, Any]]:
        """Get project status distribution for pie chart"""
        try:
            data = self.db.execute_query(
                """
                SELECT 
                    Status as status,
                    COUNT(*) as count
                FROM Projects
                GROUP BY Status
                ORDER BY COUNT(*) DESC
            """
            )

            return data or []

        except Exception as e:
            logger.error(f"Error getting project status distribution: {e}")
            return []

    def get_task_priority_distribution(self) -> List[Dict[str, Any]]:
        """Get task priority distribution"""
        try:
            data = self.db.execute_query(
                """
                SELECT 
                    Priority as priority,
                    COUNT(*) as count
                FROM Tasks
                WHERE Status != 'Done'
                GROUP BY Priority
                ORDER BY 
                    CASE Priority
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Medium' THEN 3
                        WHEN 'Low' THEN 4
                    END
            """
            )

            return data or []

        except Exception as e:
            logger.error(f"Error getting task priority distribution: {e}")
            return []

    def get_monthly_completion_trend(self, months: int = 6) -> List[Dict[str, Any]]:
        """Get monthly task completion trend"""
        try:
            data = self.db.execute_query(
                """
                SELECT 
                    FORMAT(LastModifiedDate, 'yyyy-MM') as month,
                    COUNT(*) as completed_tasks
                FROM Tasks
                WHERE Status = 'Done' 
                AND LastModifiedDate >= DATEADD(month, -?, GETDATE())
                GROUP BY FORMAT(LastModifiedDate, 'yyyy-MM')
                ORDER BY month
            """,
                (months,),
            )

            return data or []

        except Exception as e:
            logger.error(f"Error getting completion trend: {e}")
            return []

    def get_user_productivity(self) -> List[Dict[str, Any]]:
        """Get user productivity metrics"""
        try:
            data = self.db.execute_query(
                """
                SELECT 
                    u.FullName as user_name,
                    COUNT(t.TaskID) as total_tasks,
                    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                    CASE 
                        WHEN COUNT(t.TaskID) > 0 THEN 
                            ROUND((SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) * 100.0) / COUNT(t.TaskID), 1)
                        ELSE 0 
                    END as completion_rate
                FROM Users u
                LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
                WHERE u.IsActive = 1
                GROUP BY u.UserID, u.FullName
                HAVING COUNT(t.TaskID) > 0
                ORDER BY completion_rate DESC
            """
            )

            return data or []

        except Exception as e:
            logger.error(f"Error getting user productivity: {e}")
            return []

    def get_project_timeline_data(self) -> List[Dict[str, Any]]:
        """Get project timeline for Gantt chart"""
        try:
            data = self.db.execute_query(
                """
                SELECT 
                    ProjectName as project,
                    StartDate as start_date,
                    EndDate as end_date,
                    Status as status,
                    Progress as progress
                FROM Projects
                WHERE StartDate IS NOT NULL AND EndDate IS NOT NULL
                ORDER BY StartDate
            """
            )

            return data or []

        except Exception as e:
            logger.error(f"Error getting timeline data: {e}")
            return []

    def get_workload_analysis(self) -> Dict[str, Any]:
        """Get team workload analysis"""
        try:
            # Users with highest workload
            high_workload = self.db.execute_query(
                """
                SELECT TOP 5
                    u.FullName as user_name,
                    COUNT(t.TaskID) as active_tasks,
                    SUM(CASE WHEN t.Priority = 'Critical' THEN 2
                             WHEN t.Priority = 'High' THEN 1.5
                             WHEN t.Priority = 'Medium' THEN 1
                             ELSE 0.5 END) as workload_score
                FROM Users u
                LEFT JOIN Tasks t ON u.UserID = t.AssignedTo AND t.Status != 'Done'
                WHERE u.IsActive = 1
                GROUP BY u.UserID, u.FullName
                ORDER BY workload_score DESC
            """
            )

            # Department workload
            dept_workload = self.db.execute_query(
                """
                SELECT 
                    u.Department,
                    COUNT(t.TaskID) as total_tasks,
                    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks
                FROM Users u
                LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
                WHERE u.IsActive = 1 AND u.Department IS NOT NULL
                GROUP BY u.Department
                ORDER BY total_tasks DESC
            """
            )

            return {
                "high_workload_users": high_workload or [],
                "department_workload": dept_workload or [],
            }

        except Exception as e:
            logger.error(f"Error getting workload analysis: {e}")
            return {"high_workload_users": [], "department_workload": []}

    def get_time_tracking_analysis(self) -> Dict[str, Any]:
        """Get time tracking analysis"""
        try:
            # Time by project
            project_time = self.db.execute_query(
                """
                SELECT 
                    p.ProjectName,
                    SUM(tt.Duration) as total_hours,
                    COUNT(DISTINCT tt.UserID) as team_members
                FROM TimeTracking tt
                JOIN Tasks t ON tt.TaskID = t.TaskID
                JOIN Projects p ON t.ProjectID = p.ProjectID
                WHERE tt.StartTime >= DATEADD(month, -3, GETDATE())
                GROUP BY p.ProjectID, p.ProjectName
                ORDER BY total_hours DESC
            """
            )

            # Time by user
            user_time = self.db.execute_query(
                """
                SELECT 
                    u.FullName,
                    SUM(tt.Duration) as total_hours,
                    COUNT(DISTINCT t.ProjectID) as projects_worked
                FROM TimeTracking tt
                JOIN Users u ON tt.UserID = u.UserID
                JOIN Tasks t ON tt.TaskID = t.TaskID
                WHERE tt.StartTime >= DATEADD(month, -1, GETDATE())
                GROUP BY u.UserID, u.FullName
                ORDER BY total_hours DESC
            """
            )

            return {"project_time": project_time or [], "user_time": user_time or []}

        except Exception as e:
            logger.error(f"Error getting time analysis: {e}")
            return {"project_time": [], "user_time": []}

    def generate_project_report(self, project_id: int) -> Dict[str, Any]:
        """Generate comprehensive project report"""
        try:
            # Project basic info
            project_info = self.db.execute_query(
                """
                SELECT 
                    p.*,
                    u.FullName as ProjectManager
                FROM Projects p
                LEFT JOIN Users u ON p.ProjectManagerID = u.UserID
                WHERE p.ProjectID = ?
            """,
                (project_id,),
            )

            if not project_info:
                return {}

            project = project_info[0]

            # Task statistics
            task_stats = self.db.execute_query(
                """
                SELECT 
                    Status,
                    COUNT(*) as count,
                    AVG(CAST(Progress as FLOAT)) as avg_progress
                FROM Tasks
                WHERE ProjectID = ?
                GROUP BY Status
            """,
                (project_id,),
            )

            # Team members
            team_members = self.db.execute_query(
                """
                SELECT 
                    u.FullName,
                    pm.Role,
                    COUNT(t.TaskID) as assigned_tasks,
                    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks
                FROM ProjectMembers pm
                JOIN Users u ON pm.UserID = u.UserID
                LEFT JOIN Tasks t ON u.UserID = t.AssignedTo AND t.ProjectID = ?
                WHERE pm.ProjectID = ? AND pm.IsActive = 1
                GROUP BY u.UserID, u.FullName, pm.Role
            """,
                (project_id, project_id),
            )

            # Time tracking
            time_summary = self.db.execute_query(
                """
                SELECT 
                    SUM(tt.Duration) as total_hours,
                    COUNT(DISTINCT tt.UserID) as contributors
                FROM TimeTracking tt
                JOIN Tasks t ON tt.TaskID = t.TaskID
                WHERE t.ProjectID = ?
            """,
                (project_id,),
            )

            return {
                "project_info": project,
                "task_statistics": task_stats or [],
                "team_members": team_members or [],
                "time_summary": time_summary[0] if time_summary else {},
            }

        except Exception as e:
            logger.error(f"Error generating project report: {e}")
            return {}

    def export_analytics_data(self, data_type: str, **filters) -> pd.DataFrame:
        """Export analytics data to DataFrame"""
        try:
            if data_type == "projects":
                query = """
                    SELECT 
                        p.ProjectName,
                        p.Status,
                        p.Priority,
                        p.Progress,
                        p.StartDate,
                        p.EndDate,
                        p.Budget,
                        u.FullName as ProjectManager
                    FROM Projects p
                    LEFT JOIN Users u ON p.ProjectManagerID = u.UserID
                """

            elif data_type == "tasks":
                query = """
                    SELECT 
                        t.TaskTitle,
                        p.ProjectName,
                        t.Status,
                        t.Priority,
                        assigned.FullName as AssignedTo,
                        t.DueDate,
                        t.Progress
                    FROM Tasks t
                    LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
                    LEFT JOIN Users assigned ON t.AssignedTo = assigned.UserID
                """

            elif data_type == "users":
                query = """
                    SELECT 
                        u.FullName,
                        u.Role,
                        u.Department,
                        COUNT(t.TaskID) as TotalTasks,
                        SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks
                    FROM Users u
                    LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
                    WHERE u.IsActive = 1
                    GROUP BY u.UserID, u.FullName, u.Role, u.Department
                """
            else:
                return pd.DataFrame()

            data = self.db.execute_query(query)
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            return pd.DataFrame()
