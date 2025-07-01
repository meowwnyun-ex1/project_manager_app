# services/report_service.py
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from enum import Enum
import io
import csv

from .enhanced_db_service import get_db_service, cached_query, DatabaseException

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Report type enumeration"""

    PROJECT_SUMMARY = "project_summary"
    TASK_ANALYTICS = "task_analytics"
    TEAM_PERFORMANCE = "team_performance"
    TIME_TRACKING = "time_tracking"
    BUDGET_ANALYSIS = "budget_analysis"
    PRODUCTIVITY = "productivity"
    TREND_ANALYSIS = "trend_analysis"
    CUSTOM = "custom"


class ExportFormat(Enum):
    """Export format enumeration"""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


@dataclass
class ReportConfig:
    """Report configuration"""

    report_type: ReportType
    date_range: Optional[Tuple[datetime, datetime]] = None
    project_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None
    include_inactive: bool = False
    group_by: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class ReportService:
    """Enhanced reporting and analytics service"""

    def __init__(self):
        self.db_service = get_db_service()

    def generate_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate report based on configuration"""
        try:
            report_generators = {
                ReportType.PROJECT_SUMMARY: self._generate_project_summary_report,
                ReportType.TASK_ANALYTICS: self._generate_task_analytics_report,
                ReportType.TEAM_PERFORMANCE: self._generate_team_performance_report,
                ReportType.TIME_TRACKING: self._generate_time_tracking_report,
                ReportType.BUDGET_ANALYSIS: self._generate_budget_analysis_report,
                ReportType.PRODUCTIVITY: self._generate_productivity_report,
                ReportType.TREND_ANALYSIS: self._generate_trend_analysis_report,
            }

            generator = report_generators.get(config.report_type)
            if not generator:
                raise ValueError(f"Unsupported report type: {config.report_type}")

            report_data = generator(config)

            # Add metadata
            report_data["metadata"] = {
                "report_type": config.report_type.value,
                "generated_at": datetime.now().isoformat(),
                "date_range": {
                    "start": (
                        config.date_range[0].isoformat() if config.date_range else None
                    ),
                    "end": (
                        config.date_range[1].isoformat() if config.date_range else None
                    ),
                },
                "filters_applied": config.filters or {},
                "total_records": self._count_total_records(report_data),
            }

            logger.info(f"Report generated successfully: {config.report_type.value}")
            return report_data

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            raise DatabaseException(f"Report generation failed: {str(e)}")

    def _generate_project_summary_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate project summary report"""
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
            p.ClientName,
            p.CreatedDate,
            u.Username as CreatedBy,
            COUNT(t.TaskID) as TotalTasks,
            COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as CompletedTasks,
            ISNULL(AVG(CAST(t.Progress as FLOAT)), 0) as AvgProgress,
            SUM(ISNULL(t.EstimatedHours, 0)) as TotalEstimatedHours,
            SUM(ISNULL(t.ActualHours, 0)) as TotalActualHours
        FROM Projects p
        LEFT JOIN Users u ON p.CreatedBy = u.UserID
        LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
        WHERE 1=1
        """

        params = []

        # Apply filters
        if config.project_ids:
            placeholders = ",".join(["?" for _ in config.project_ids])
            base_query += f" AND p.ProjectID IN ({placeholders})"
            params.extend(config.project_ids)

        if config.date_range:
            base_query += " AND p.CreatedDate BETWEEN ? AND ?"
            params.extend(config.date_range)

        if config.filters:
            if config.filters.get("status"):
                base_query += " AND p.Status = ?"
                params.append(config.filters["status"])

            if config.filters.get("priority"):
                base_query += " AND p.Priority = ?"
                params.append(config.filters["priority"])

        base_query += """
        GROUP BY p.ProjectID, p.ProjectName, p.Description, p.Status, p.Priority,
                 p.StartDate, p.EndDate, p.Budget, p.ClientName, p.CreatedDate, u.Username
        ORDER BY p.CreatedDate DESC
        """

        projects = self.db_service.execute_query(base_query, tuple(params))

        # Calculate summary statistics
        summary = self._calculate_project_summary_stats(projects)

        # Calculate health scores
        for project in projects:
            project["health_score"] = self._calculate_project_health_score(project)
            project["completion_rate"] = (
                (project["CompletedTasks"] / project["TotalTasks"] * 100)
                if project["TotalTasks"] > 0
                else 0
            )
            project["time_variance"] = (
                project["TotalActualHours"] - project["TotalEstimatedHours"]
            )
            project["is_overdue"] = self._is_project_overdue(project)

        return {
            "projects": projects,
            "summary": summary,
            "charts": self._generate_project_charts(projects),
        }

    def _generate_task_analytics_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate task analytics report"""
        base_query = """
        SELECT 
            t.TaskID,
            t.TaskName,
            t.Status,
            t.Priority,
            t.Progress,
            t.StartDate,
            t.EndDate,
            t.EstimatedHours,
            t.ActualHours,
            t.CreatedDate,
            p.ProjectName,
            assignee.Username as AssigneeName,
            creator.Username as CreatedBy
        FROM Tasks t
        LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
        LEFT JOIN Users assignee ON t.AssigneeID = assignee.UserID
        LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
        WHERE 1=1
        """

        params = []

        # Apply filters
        if config.project_ids:
            placeholders = ",".join(["?" for _ in config.project_ids])
            base_query += f" AND t.ProjectID IN ({placeholders})"
            params.extend(config.project_ids)

        if config.user_ids:
            placeholders = ",".join(["?" for _ in config.user_ids])
            base_query += f" AND t.AssigneeID IN ({placeholders})"
            params.extend(config.user_ids)

        if config.date_range:
            base_query += " AND t.CreatedDate BETWEEN ? AND ?"
            params.extend(config.date_range)

        base_query += " ORDER BY t.CreatedDate DESC"

        tasks = self.db_service.execute_query(base_query, tuple(params))

        # Calculate analytics
        analytics = {
            "status_distribution": self._calculate_status_distribution(tasks),
            "priority_distribution": self._calculate_priority_distribution(tasks),
            "completion_metrics": self._calculate_completion_metrics(tasks),
            "time_analysis": self._calculate_time_analysis(tasks),
            "assignee_workload": self._calculate_assignee_workload(tasks),
            "overdue_analysis": self._calculate_overdue_analysis(tasks),
        }

        return {
            "tasks": tasks,
            "analytics": analytics,
            "charts": self._generate_task_charts(tasks, analytics),
        }

    def _generate_team_performance_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate team performance report"""
        base_query = """
        SELECT 
            u.UserID,
            u.Username,
            u.Email,
            u.Role,
            COUNT(t.TaskID) as TasksAssigned,
            COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as TasksCompleted,
            ISNULL(AVG(CAST(t.Progress as FLOAT)), 0) as AvgProgress,
            SUM(ISNULL(t.EstimatedHours, 0)) as TotalEstimatedHours,
            SUM(ISNULL(t.ActualHours, 0)) as TotalActualHours,
            COUNT(DISTINCT t.ProjectID) as ProjectsInvolved
        FROM Users u
        LEFT JOIN Tasks t ON u.UserID = t.AssigneeID
        WHERE u.Active = 1
        """

        params = []

        if config.user_ids:
            placeholders = ",".join(["?" for _ in config.user_ids])
            base_query += f" AND u.UserID IN ({placeholders})"
            params.extend(config.user_ids)

        if config.date_range:
            base_query += " AND t.CreatedDate BETWEEN ? AND ?"
            params.extend(config.date_range)

        base_query += """
        GROUP BY u.UserID, u.Username, u.Email, u.Role
        ORDER BY TasksCompleted DESC, AvgProgress DESC
        """

        team_members = self.db_service.execute_query(base_query, tuple(params))

        # Calculate performance metrics
        for member in team_members:
            member["completion_rate"] = (
                (member["TasksCompleted"] / member["TasksAssigned"] * 100)
                if member["TasksAssigned"] > 0
                else 0
            )
            member["efficiency_score"] = self._calculate_efficiency_score(member)
            member["workload_level"] = self._get_workload_level(member["TasksAssigned"])
            member["time_variance"] = (
                member["TotalActualHours"] - member["TotalEstimatedHours"]
            )

        # Calculate team summary
        team_summary = self._calculate_team_summary(team_members)

        return {
            "team_members": team_members,
            "team_summary": team_summary,
            "performance_rankings": self._calculate_performance_rankings(team_members),
            "charts": self._generate_team_charts(team_members),
        }

    def _generate_time_tracking_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate time tracking report"""
        base_query = """
        SELECT 
            t.TaskID,
            t.TaskName,
            t.EstimatedHours,
            t.ActualHours,
            t.StartDate,
            t.EndDate,
            t.CreatedDate,
            p.ProjectName,
            u.Username as AssigneeName
        FROM Tasks t
        LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
        LEFT JOIN Users u ON t.AssigneeID = u.UserID
        WHERE t.EstimatedHours IS NOT NULL OR t.ActualHours IS NOT NULL
        """

        params = []

        if config.project_ids:
            placeholders = ",".join(["?" for _ in config.project_ids])
            base_query += f" AND t.ProjectID IN ({placeholders})"
            params.extend(config.project_ids)

        if config.user_ids:
            placeholders = ",".join(["?" for _ in config.user_ids])
            base_query += f" AND t.AssigneeID IN ({placeholders})"
            params.extend(config.user_ids)

        if config.date_range:
            base_query += " AND t.CreatedDate BETWEEN ? AND ?"
            params.extend(config.date_range)

        base_query += " ORDER BY t.CreatedDate DESC"

        time_entries = self.db_service.execute_query(base_query, tuple(params))

        # Calculate time analytics
        time_analytics = {
            "total_estimated_hours": sum(
                entry.get("EstimatedHours", 0) for entry in time_entries
            ),
            "total_actual_hours": sum(
                entry.get("ActualHours", 0) for entry in time_entries
            ),
            "variance_analysis": self._calculate_time_variance_analysis(time_entries),
            "efficiency_metrics": self._calculate_time_efficiency_metrics(time_entries),
            "project_breakdown": self._calculate_project_time_breakdown(time_entries),
            "user_breakdown": self._calculate_user_time_breakdown(time_entries),
        }

        return {
            "time_entries": time_entries,
            "analytics": time_analytics,
            "charts": self._generate_time_charts(time_entries, time_analytics),
        }

    def _generate_budget_analysis_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate budget analysis report"""
        base_query = """
        SELECT 
            p.ProjectID,
            p.ProjectName,
            p.Budget,
            p.Status,
            SUM(ISNULL(t.ActualHours, 0)) as TotalHours
        FROM Projects p
        LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
        WHERE p.Budget IS NOT NULL AND p.Budget > 0
        """

        params = []

        if config.project_ids:
            placeholders = ",".join(["?" for _ in config.project_ids])
            base_query += f" AND p.ProjectID IN ({placeholders})"
            params.extend(config.project_ids)

        if config.date_range:
            base_query += " AND p.CreatedDate BETWEEN ? AND ?"
            params.extend(config.date_range)

        base_query += " GROUP BY p.ProjectID, p.ProjectName, p.Budget, p.Status ORDER BY p.Budget DESC"

        budget_data = self.db_service.execute_query(base_query, tuple(params))

        # Assume hourly rate for cost calculation (this could be configurable)
        hourly_rate = 75.0  # Default hourly rate

        for project in budget_data:
            project["estimated_cost"] = project["TotalHours"] * hourly_rate
            project["budget_variance"] = project["Budget"] - project["estimated_cost"]
            project["budget_utilization"] = (
                (project["estimated_cost"] / project["Budget"] * 100)
                if project["Budget"] > 0
                else 0
            )
            project["status_indicator"] = self._get_budget_status(
                project["budget_utilization"]
            )

        # Calculate summary
        budget_summary = {
            "total_budget": sum(p["Budget"] for p in budget_data),
            "total_estimated_cost": sum(p["estimated_cost"] for p in budget_data),
            "total_variance": sum(p["budget_variance"] for p in budget_data),
            "avg_utilization": (
                sum(p["budget_utilization"] for p in budget_data) / len(budget_data)
                if budget_data
                else 0
            ),
            "projects_over_budget": len(
                [p for p in budget_data if p["budget_variance"] < 0]
            ),
            "projects_under_budget": len(
                [p for p in budget_data if p["budget_variance"] > 0]
            ),
        }

        return {
            "budget_data": budget_data,
            "summary": budget_summary,
            "charts": self._generate_budget_charts(budget_data, budget_summary),
        }

    def _generate_productivity_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate productivity report"""
        # Get productivity metrics over time
        base_query = """
        SELECT 
            CAST(t.CreatedDate as DATE) as Date,
            COUNT(t.TaskID) as TasksCreated,
            COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as TasksCompleted,
            ISNULL(AVG(CAST(t.Progress as FLOAT)), 0) as AvgProgress,
            COUNT(DISTINCT t.AssigneeID) as ActiveUsers
        FROM Tasks t
        WHERE t.CreatedDate IS NOT NULL
        """

        params = []

        if config.date_range:
            base_query += " AND t.CreatedDate BETWEEN ? AND ?"
            params.extend(config.date_range)

        if config.project_ids:
            placeholders = ",".join(["?" for _ in config.project_ids])
            base_query += f" AND t.ProjectID IN ({placeholders})"
            params.extend(config.project_ids)

        base_query += " GROUP BY CAST(t.CreatedDate as DATE) ORDER BY Date DESC"

        daily_metrics = self.db_service.execute_query(base_query, tuple(params))

        # Calculate productivity trends
        productivity_trends = self._calculate_productivity_trends(daily_metrics)

        # Get team productivity by user
        user_productivity = self._get_user_productivity_metrics(config)

        return {
            "daily_metrics": daily_metrics,
            "trends": productivity_trends,
            "user_productivity": user_productivity,
            "charts": self._generate_productivity_charts(
                daily_metrics, productivity_trends
            ),
        }

    def _generate_trend_analysis_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate trend analysis report"""
        # Analyze trends over different time periods
        trends = {
            "project_trends": self._analyze_project_trends(config),
            "task_trends": self._analyze_task_trends(config),
            "team_trends": self._analyze_team_trends(config),
            "performance_trends": self._analyze_performance_trends(config),
        }

        return {
            "trends": trends,
            "insights": self._generate_trend_insights(trends),
            "predictions": self._generate_trend_predictions(trends),
            "charts": self._generate_trend_charts(trends),
        }

    def export_report(
        self, report_data: Dict[str, Any], format_type: ExportFormat
    ) -> bytes:
        """Export report in specified format"""
        try:
            exporters = {
                ExportFormat.JSON: self._export_json,
                ExportFormat.CSV: self._export_csv,
                ExportFormat.EXCEL: self._export_excel,
            }

            exporter = exporters.get(format_type)
            if not exporter:
                raise ValueError(f"Unsupported export format: {format_type}")

            return exporter(report_data)

        except Exception as e:
            logger.error(f"Failed to export report: {str(e)}")
            raise DatabaseException(f"Report export failed: {str(e)}")

    def _export_json(self, report_data: Dict[str, Any]) -> bytes:
        """Export report as JSON"""
        # Convert datetime objects to strings for JSON serialization
        json_data = self._serialize_for_json(report_data)
        return json.dumps(json_data, indent=2, ensure_ascii=False).encode("utf-8")

    def _export_csv(self, report_data: Dict[str, Any]) -> bytes:
        """Export report as CSV"""
        output = io.StringIO()

        # Extract main data table
        main_data = None
        if "projects" in report_data:
            main_data = report_data["projects"]
        elif "tasks" in report_data:
            main_data = report_data["tasks"]
        elif "team_members" in report_data:
            main_data = report_data["team_members"]
        elif "time_entries" in report_data:
            main_data = report_data["time_entries"]

        if main_data and len(main_data) > 0:
            fieldnames = main_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(main_data)

        return output.getvalue().encode("utf-8")

    def _export_excel(self, report_data: Dict[str, Any]) -> bytes:
        """Export report as Excel (placeholder - would need openpyxl)"""
        # This would require openpyxl library
        # For now, return CSV format
        return self._export_csv(report_data)

    # Helper methods for calculations
    def _calculate_project_summary_stats(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate project summary statistics"""
        if not projects:
            return {}

        total_projects = len(projects)
        completed_projects = len([p for p in projects if p["Status"] == "Completed"])
        total_budget = sum(p.get("Budget", 0) for p in projects)
        avg_completion = sum(p.get("AvgProgress", 0) for p in projects) / total_projects

        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "completion_rate": (
                (completed_projects / total_projects * 100) if total_projects > 0 else 0
            ),
            "total_budget": total_budget,
            "avg_completion": round(avg_completion, 2),
            "overdue_projects": len(
                [p for p in projects if self._is_project_overdue(p)]
            ),
        }

    def _calculate_project_health_score(self, project: Dict[str, Any]) -> float:
        """Calculate project health score"""
        score = 0.0

        # Progress score (40%)
        progress = project.get("AvgProgress", 0)
        score += (progress / 100) * 40

        # Time performance (30%)
        if not self._is_project_overdue(project):
            score += 30

        # Task completion rate (30%)
        total_tasks = project.get("TotalTasks", 0)
        completed_tasks = project.get("CompletedTasks", 0)
        if total_tasks > 0:
            completion_rate = completed_tasks / total_tasks
            score += completion_rate * 30

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
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate status distribution"""
        distribution = {}
        for item in items:
            status = item.get("Status", "Unknown")
            distribution[status] = distribution.get(status, 0) + 1
        return distribution

    def _calculate_priority_distribution(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate priority distribution"""
        distribution = {}
        for item in items:
            priority = item.get("Priority", "Unknown")
            distribution[priority] = distribution.get(priority, 0) + 1
        return distribution

    def _calculate_completion_metrics(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate completion metrics"""
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("Status") == "Done"])
        avg_progress = (
            sum(t.get("Progress", 0) for t in tasks) / total_tasks
            if total_tasks > 0
            else 0
        )

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            ),
            "average_progress": round(avg_progress, 2),
        }

    def _calculate_time_analysis(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate time analysis"""
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

    def _calculate_assignee_workload(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate assignee workload"""
        workload = {}
        for task in tasks:
            assignee = task.get("AssigneeName", "Unassigned")
            workload[assignee] = workload.get(assignee, 0) + 1
        return workload

    def _calculate_overdue_analysis(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overdue analysis"""
        now = datetime.now()
        overdue_tasks = []

        for task in tasks:
            end_date = task.get("EndDate")
            status = task.get("Status")

            if end_date and status not in ["Done", "Cancelled"]:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

                if now > end_date:
                    overdue_tasks.append(task)

        return {
            "overdue_count": len(overdue_tasks),
            "overdue_percentage": (
                (len(overdue_tasks) / len(tasks) * 100) if tasks else 0
            ),
            "critical_overdue": len(
                [t for t in overdue_tasks if t.get("Priority") == "Critical"]
            ),
        }

    def _calculate_efficiency_score(self, member: Dict[str, Any]) -> float:
        """Calculate efficiency score for team member"""
        tasks_assigned = member.get("TasksAssigned", 0)
        tasks_completed = member.get("TasksCompleted", 0)
        avg_progress = member.get("AvgProgress", 0)

        if tasks_assigned == 0:
            return 0.0

        completion_rate = tasks_completed / tasks_assigned
        efficiency = (completion_rate * 0.6) + (avg_progress / 100 * 0.4)

        return round(efficiency * 100, 2)

    def _get_workload_level(self, task_count: int) -> str:
        """Get workload level description"""
        if task_count == 0:
            return "Available"
        elif task_count <= 3:
            return "Light"
        elif task_count <= 7:
            return "Moderate"
        elif task_count <= 12:
            return "Heavy"
        else:
            return "Overloaded"

    def _calculate_team_summary(
        self, team_members: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate team summary statistics"""
        if not team_members:
            return {}

        total_members = len(team_members)
        total_tasks = sum(m.get("TasksAssigned", 0) for m in team_members)
        total_completed = sum(m.get("TasksCompleted", 0) for m in team_members)
        avg_efficiency = (
            sum(m.get("efficiency_score", 0) for m in team_members) / total_members
        )

        return {
            "total_members": total_members,
            "total_tasks_assigned": total_tasks,
            "total_tasks_completed": total_completed,
            "team_completion_rate": (
                (total_completed / total_tasks * 100) if total_tasks > 0 else 0
            ),
            "average_efficiency": round(avg_efficiency, 2),
            "top_performer": (
                max(team_members, key=lambda x: x.get("efficiency_score", 0))[
                    "Username"
                ]
                if team_members
                else None
            ),
        }

    def _calculate_performance_rankings(
        self, team_members: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate performance rankings"""
        # Sort by efficiency score descending
        sorted_members = sorted(
            team_members, key=lambda x: x.get("efficiency_score", 0), reverse=True
        )

        rankings = []
        for i, member in enumerate(sorted_members[:10]):  # Top 10
            rankings.append(
                {
                    "rank": i + 1,
                    "username": member["Username"],
                    "efficiency_score": member.get("efficiency_score", 0),
                    "tasks_completed": member.get("TasksCompleted", 0),
                    "completion_rate": member.get("completion_rate", 0),
                }
            )

        return rankings

    def _serialize_for_json(self, obj):
        """Serialize object for JSON export"""
        if isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def _count_total_records(self, report_data: Dict[str, Any]) -> int:
        """Count total records in report"""
        count = 0
        for key, value in report_data.items():
            if isinstance(value, list):
                count += len(value)
        return count

    # Chart generation methods (would integrate with plotting libraries)
    def _generate_project_charts(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate chart data for projects"""
        return {
            "status_chart": self._calculate_status_distribution(projects),
            "priority_chart": self._calculate_priority_distribution(projects),
            "timeline_chart": self._generate_timeline_data(projects),
        }

    def _generate_task_charts(
        self, tasks: List[Dict[str, Any]], analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate chart data for tasks"""
        return {
            "status_distribution": analytics["status_distribution"],
            "priority_distribution": analytics["priority_distribution"],
            "assignee_workload": analytics["assignee_workload"],
        }

    def _generate_team_charts(
        self, team_members: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate chart data for team"""
        return {
            "efficiency_distribution": {
                m["Username"]: m.get("efficiency_score", 0) for m in team_members
            },
            "workload_distribution": {
                m["Username"]: m.get("TasksAssigned", 0) for m in team_members
            },
        }

    def _generate_timeline_data(
        self, projects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate timeline data for Gantt charts"""
        timeline_data = []
        for project in projects:
            timeline_data.append(
                {
                    "name": project["ProjectName"],
                    "start": project.get("StartDate"),
                    "end": project.get("EndDate"),
                    "progress": project.get("AvgProgress", 0),
                }
            )
        return timeline_data

    # Placeholder methods for complex analytics (would need more implementation)
    def _calculate_time_variance_analysis(
        self, time_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate time variance analysis"""
        return {"placeholder": "variance_analysis"}

    def _calculate_time_efficiency_metrics(
        self, time_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate time efficiency metrics"""
        return {"placeholder": "efficiency_metrics"}

    def _calculate_project_time_breakdown(
        self, time_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate project time breakdown"""
        return {"placeholder": "project_breakdown"}

    def _calculate_user_time_breakdown(
        self, time_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate user time breakdown"""
        return {"placeholder": "user_breakdown"}

    def _generate_time_charts(
        self, time_entries: List[Dict[str, Any]], analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate time tracking charts"""
        return {"placeholder": "time_charts"}

    def _get_budget_status(self, utilization: float) -> str:
        """Get budget status indicator"""
        if utilization < 50:
            return "Under Budget"
        elif utilization < 90:
            return "On Track"
        elif utilization < 110:
            return "At Risk"
        else:
            return "Over Budget"

    def _generate_budget_charts(
        self, budget_data: List[Dict[str, Any]], summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate budget analysis charts"""
        return {"placeholder": "budget_charts"}

    def _calculate_productivity_trends(
        self, daily_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate productivity trends"""
        return {"placeholder": "productivity_trends"}

    def _get_user_productivity_metrics(
        self, config: ReportConfig
    ) -> List[Dict[str, Any]]:
        """Get user productivity metrics"""
        return [{"placeholder": "user_productivity"}]

    def _generate_productivity_charts(
        self, daily_metrics: List[Dict[str, Any]], trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate productivity charts"""
        return {"placeholder": "productivity_charts"}

    def _analyze_project_trends(self, config: ReportConfig) -> Dict[str, Any]:
        """Analyze project trends"""
        return {"placeholder": "project_trends"}

    def _analyze_task_trends(self, config: ReportConfig) -> Dict[str, Any]:
        """Analyze task trends"""
        return {"placeholder": "task_trends"}

    def _analyze_team_trends(self, config: ReportConfig) -> Dict[str, Any]:
        """Analyze team trends"""
        return {"placeholder": "team_trends"}

    def _analyze_performance_trends(self, config: ReportConfig) -> Dict[str, Any]:
        """Analyze performance trends"""
        return {"placeholder": "performance_trends"}

    def _generate_trend_insights(self, trends: Dict[str, Any]) -> List[str]:
        """Generate trend insights"""
        return ["Insight 1", "Insight 2", "Insight 3"]

    def _generate_trend_predictions(self, trends: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend predictions"""
        return {"placeholder": "predictions"}

    def _generate_trend_charts(self, trends: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend charts"""
        return {"placeholder": "trend_charts"}


# Global report service instance
_report_service = None


def get_report_service() -> ReportService:
    """Get global report service instance"""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service


# Export classes and functions
__all__ = [
    "ReportService",
    "ReportType",
    "ExportFormat",
    "ReportConfig",
    "get_report_service",
]
