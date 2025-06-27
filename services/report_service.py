# services/report_service.py
import pandas as pd
from typing import Dict, Any, Optional
from datetime import date, timedelta
from services.enhanced_db_service import DatabaseService
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """Advanced reporting and analytics service"""

    @staticmethod
    def get_project_summary_report(
        start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive project summary report"""
        try:
            # Default to last 30 days if no dates provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Projects overview
            projects_query = """
            SELECT 
                COUNT(*) as total_projects,
                COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as completed_projects,
                COUNT(CASE WHEN Status = 'In Progress' THEN 1 END) as active_projects,
                COUNT(CASE WHEN EndDate < ? AND Status NOT IN ('Completed', 'Cancelled') THEN 1 END) as overdue_projects
            FROM Projects
            WHERE CreatedDate BETWEEN ? AND ?
            """

            project_stats = DatabaseService.fetch_one(
                projects_query, (date.today(), start_date, end_date)
            )

            # Task completion rates
            task_completion_query = """
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN Status = 'Done' THEN 1 END) as completed_tasks,
                AVG(CAST(Progress AS FLOAT)) as avg_progress
            FROM Tasks T
            JOIN Projects P ON T.ProjectID = P.ProjectID
            WHERE P.CreatedDate BETWEEN ? AND ?
            """

            task_stats = DatabaseService.fetch_one(
                task_completion_query, (start_date, end_date)
            )

            # Project duration analysis
            duration_query = """
            SELECT 
                AVG(DATEDIFF(day, StartDate, EndDate)) as avg_planned_duration,
                AVG(CASE WHEN Status = 'Completed' 
                    THEN DATEDIFF(day, StartDate, GETDATE()) 
                    END) as avg_actual_duration
            FROM Projects
            WHERE CreatedDate BETWEEN ? AND ? AND StartDate IS NOT NULL
            """

            duration_stats = DatabaseService.fetch_one(
                duration_query, (start_date, end_date)
            )

            return {
                "period": {"start_date": start_date, "end_date": end_date},
                "projects": project_stats or {},
                "tasks": task_stats or {},
                "duration": duration_stats or {},
            }

        except Exception as e:
            logger.error(f"Failed to generate project summary report: {e}")
            return {}

    @staticmethod
    def get_team_performance_report() -> Dict[str, Any]:
        """Generate team performance analytics"""
        try:
            # Task distribution by assignee
            workload_query = """
            SELECT 
                U.Username,
                COUNT(T.TaskID) as total_tasks,
                COUNT(CASE WHEN T.Status = 'Done' THEN 1 END) as completed_tasks,
                AVG(CAST(T.Progress AS FLOAT)) as avg_progress,
                COUNT(CASE WHEN T.EndDate < ? AND T.Status != 'Done' THEN 1 END) as overdue_tasks
            FROM Users U
            LEFT JOIN Tasks T ON U.UserID = T.AssigneeID
            GROUP BY U.UserID, U.Username
            ORDER BY total_tasks DESC
            """

            team_workload = DatabaseService.fetch_data(workload_query, (date.today(),))

            # Project success rates by team member
            success_query = """
            SELECT 
                U.Username,
                COUNT(DISTINCT P.ProjectID) as projects_involved,
                COUNT(DISTINCT CASE WHEN P.Status = 'Completed' THEN P.ProjectID END) as completed_projects
            FROM Users U
            JOIN Tasks T ON U.UserID = T.AssigneeID
            JOIN Projects P ON T.ProjectID = P.ProjectID
            GROUP BY U.UserID, U.Username
            HAVING COUNT(DISTINCT P.ProjectID) > 0
            """

            success_rates = DatabaseService.fetch_data(success_query)

            return {"team_workload": team_workload, "success_rates": success_rates}

        except Exception as e:
            logger.error(f"Failed to generate team performance report: {e}")
            return {}

    @staticmethod
    def get_timeline_analysis(project_id: Optional[int] = None) -> Dict[str, Any]:
        """Analyze project timelines and delays"""
        try:
            base_query = """
            SELECT 
                P.ProjectName,
                P.StartDate,
                P.EndDate,
                P.Status,
                DATEDIFF(day, P.StartDate, P.EndDate) as planned_duration,
                CASE WHEN P.Status = 'Completed' 
                    THEN DATEDIFF(day, P.StartDate, GETDATE())
                    ELSE NULL 
                END as actual_duration,
                COUNT(T.TaskID) as total_tasks,
                COUNT(CASE WHEN T.Status = 'Done' THEN 1 END) as completed_tasks
            FROM Projects P
            LEFT JOIN Tasks T ON P.ProjectID = T.ProjectID
            """

            if project_id:
                query = (
                    base_query
                    + " WHERE P.ProjectID = ? GROUP BY P.ProjectID, P.ProjectName, P.StartDate, P.EndDate, P.Status"
                )
                params = (project_id,)
            else:
                query = (
                    base_query
                    + " GROUP BY P.ProjectID, P.ProjectName, P.StartDate, P.EndDate, P.Status ORDER BY P.StartDate DESC"
                )
                params = ()

            timeline_data = DatabaseService.fetch_data(query, params)

            return {"timeline_analysis": timeline_data}

        except Exception as e:
            logger.error(f"Failed to generate timeline analysis: {e}")
            return {}

    @staticmethod
    def get_resource_utilization_report() -> Dict[str, Any]:
        """Analyze resource utilization across projects"""
        try:
            # Current active projects and assigned resources
            utilization_query = """
            SELECT 
                P.ProjectName,
                P.Status,
                COUNT(DISTINCT T.AssigneeID) as assigned_users,
                COUNT(T.TaskID) as total_tasks,
                COUNT(CASE WHEN T.Status IN ('To Do', 'In Progress') THEN 1 END) as active_tasks,
                AVG(CAST(T.Progress AS FLOAT)) as avg_progress
            FROM Projects P
            LEFT JOIN Tasks T ON P.ProjectID = T.ProjectID
            WHERE P.Status IN ('Planning', 'In Progress')
            GROUP BY P.ProjectID, P.ProjectName, P.Status
            ORDER BY assigned_users DESC
            """

            current_utilization = DatabaseService.fetch_data(utilization_query)

            # User availability (users not over-allocated)
            availability_query = """
            SELECT 
                U.Username,
                COUNT(T.TaskID) as active_tasks,
                COUNT(CASE WHEN T.Status IN ('To Do', 'In Progress') THEN 1 END) as current_workload
            FROM Users U
            LEFT JOIN Tasks T ON U.UserID = T.AssigneeID
            GROUP BY U.UserID, U.Username
            ORDER BY current_workload ASC
            """

            user_availability = DatabaseService.fetch_data(availability_query)

            return {
                "project_utilization": current_utilization,
                "user_availability": user_availability,
            }

        except Exception as e:
            logger.error(f"Failed to generate resource utilization report: {e}")
            return {}

    @staticmethod
    def export_report_data(report_type: str, **kwargs) -> pd.DataFrame:
        """Export report data as DataFrame for further processing"""
        try:
            if report_type == "project_summary":
                data = ReportService.get_project_summary_report(**kwargs)
                # Convert to DataFrame format suitable for export
                return pd.DataFrame([data])

            elif report_type == "team_performance":
                data = ReportService.get_team_performance_report()
                return pd.DataFrame(data.get("team_workload", []))

            elif report_type == "timeline_analysis":
                data = ReportService.get_timeline_analysis(**kwargs)
                return pd.DataFrame(data.get("timeline_analysis", []))

            elif report_type == "resource_utilization":
                data = ReportService.get_resource_utilization_report()
                return pd.DataFrame(data.get("project_utilization", []))

            else:
                logger.warning(f"Unknown report type: {report_type}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to export report data: {e}")
            return pd.DataFrame()
