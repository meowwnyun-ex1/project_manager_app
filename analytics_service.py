# analytics_service.py
"""
Advanced Analytics and Reporting Service for DENSO Project Manager
Provides comprehensive analytics, KPIs, and business intelligence
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class KPIMetric:
    """KPI metric structure"""

    name: str
    value: float
    target: float
    unit: str
    trend: float  # percentage change
    status: str  # 'good', 'warning', 'critical'


@dataclass
class AnalyticsReport:
    """Analytics report structure"""

    title: str
    description: str
    date_range: Tuple[datetime, datetime]
    kpis: List[KPIMetric]
    charts_data: Dict[str, Any]
    recommendations: List[str]


class AnalyticsService:
    """Service for analytics and reporting"""

    def __init__(self, db_service):
        self.db_service = db_service
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def get_project_analytics(
        self,
        project_id: Optional[int] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict:
        """Get comprehensive project analytics"""
        try:
            # Set default date range if not provided
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            analytics = {
                "summary": self._get_project_summary(project_id, date_range),
                "performance": self._get_project_performance(project_id, date_range),
                "timeline": self._get_project_timeline_data(project_id, date_range),
                "resource_utilization": self._get_resource_utilization(
                    project_id, date_range
                ),
                "budget_analysis": self._get_budget_analysis(project_id, date_range),
                "risk_analysis": self._get_risk_analysis(project_id, date_range),
            }

            return analytics
        except Exception as e:
            logger.error(f"Failed to get project analytics: {str(e)}")
            return {}

    def get_team_analytics(
        self, date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict:
        """Get team performance analytics"""
        try:
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            analytics = {
                "team_performance": self._get_team_performance_metrics(date_range),
                "workload_distribution": self._get_workload_distribution(date_range),
                "productivity_trends": self._get_productivity_trends(date_range),
                "collaboration_metrics": self._get_collaboration_metrics(date_range),
                "skill_analysis": self._get_skill_analysis(date_range),
            }

            return analytics
        except Exception as e:
            logger.error(f"Failed to get team analytics: {str(e)}")
            return {}

    def get_dashboard_kpis(self) -> List[KPIMetric]:
        """Get key performance indicators for dashboard"""
        try:
            kpis = []

            # Project completion rate
            project_completion = self._calculate_project_completion_rate()
            kpis.append(
                KPIMetric(
                    name="Project Completion Rate",
                    value=project_completion["current"],
                    target=80.0,
                    unit="%",
                    trend=project_completion["trend"],
                    status=self._get_kpi_status(
                        project_completion["current"], 80.0, "higher_better"
                    ),
                )
            )

            # Task completion rate
            task_completion = self._calculate_task_completion_rate()
            kpis.append(
                KPIMetric(
                    name="Task Completion Rate",
                    value=task_completion["current"],
                    target=90.0,
                    unit="%",
                    trend=task_completion["trend"],
                    status=self._get_kpi_status(
                        task_completion["current"], 90.0, "higher_better"
                    ),
                )
            )

            # Average project duration
            avg_duration = self._calculate_average_project_duration()
            kpis.append(
                KPIMetric(
                    name="Avg Project Duration",
                    value=avg_duration["current"],
                    target=60.0,
                    unit="days",
                    trend=avg_duration["trend"],
                    status=self._get_kpi_status(
                        avg_duration["current"], 60.0, "lower_better"
                    ),
                )
            )

            # Team utilization
            team_utilization = self._calculate_team_utilization()
            kpis.append(
                KPIMetric(
                    name="Team Utilization",
                    value=team_utilization["current"],
                    target=75.0,
                    unit="%",
                    trend=team_utilization["trend"],
                    status=self._get_kpi_status(
                        team_utilization["current"], 75.0, "optimal_range", (70.0, 85.0)
                    ),
                )
            )

            # Budget utilization
            budget_utilization = self._calculate_budget_utilization()
            kpis.append(
                KPIMetric(
                    name="Budget Utilization",
                    value=budget_utilization["current"],
                    target=80.0,
                    unit="%",
                    trend=budget_utilization["trend"],
                    status=self._get_kpi_status(
                        budget_utilization["current"],
                        80.0,
                        "optimal_range",
                        (75.0, 95.0),
                    ),
                )
            )

            return kpis
        except Exception as e:
            logger.error(f"Failed to get dashboard KPIs: {str(e)}")
            return []

    def generate_executive_report(
        self, date_range: Tuple[datetime, datetime]
    ) -> AnalyticsReport:
        """Generate executive summary report"""
        try:
            # Get KPIs
            kpis = self.get_dashboard_kpis()

            # Generate charts data
            charts_data = {
                "project_status_trend": self._get_project_status_trend(date_range),
                "resource_allocation": self._get_resource_allocation_chart(date_range),
                "budget_vs_actual": self._get_budget_vs_actual_chart(date_range),
                "timeline_performance": self._get_timeline_performance_chart(
                    date_range
                ),
            }

            # Generate recommendations
            recommendations = self._generate_recommendations(kpis, charts_data)

            report = AnalyticsReport(
                title="Executive Summary Report",
                description=f"Comprehensive analytics report for {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}",
                date_range=date_range,
                kpis=kpis,
                charts_data=charts_data,
                recommendations=recommendations,
            )

            return report
        except Exception as e:
            logger.error(f"Failed to generate executive report: {str(e)}")
            return None

    def get_project_health_score(self, project_id: int) -> Dict:
        """Calculate project health score based on multiple factors"""
        try:
            # Get project data
            project = self.db_service.get_project_by_id(project_id)
            if not project:
                return {"score": 0, "factors": {}, "status": "unknown"}

            factors = {}
            weights = {
                "timeline": 0.25,
                "budget": 0.20,
                "quality": 0.20,
                "team_performance": 0.15,
                "scope": 0.10,
                "risks": 0.10,
            }

            # Timeline factor
            factors["timeline"] = self._calculate_timeline_factor(project_id)

            # Budget factor
            factors["budget"] = self._calculate_budget_factor(project_id)

            # Quality factor (based on task completion rate and rework)
            factors["quality"] = self._calculate_quality_factor(project_id)

            # Team performance factor
            factors["team_performance"] = self._calculate_team_performance_factor(
                project_id
            )

            # Scope factor (scope creep analysis)
            factors["scope"] = self._calculate_scope_factor(project_id)

            # Risk factor
            factors["risks"] = self._calculate_risk_factor(project_id)

            # Calculate weighted score
            total_score = sum(factors[factor] * weights[factor] for factor in factors)

            # Determine status
            if total_score >= 80:
                status = "excellent"
            elif total_score >= 60:
                status = "good"
            elif total_score >= 40:
                status = "warning"
            else:
                status = "critical"

            return {
                "score": round(total_score, 1),
                "factors": factors,
                "status": status,
                "recommendations": self._get_health_recommendations(factors),
            }
        except Exception as e:
            logger.error(f"Failed to calculate project health score: {str(e)}")
            return {"score": 0, "factors": {}, "status": "unknown"}

    def get_predictive_analytics(self, project_id: Optional[int] = None) -> Dict:
        """Get predictive analytics and forecasts"""
        try:
            predictions = {}

            # Project completion prediction
            predictions["completion_forecast"] = self._predict_project_completion(
                project_id
            )

            # Budget overrun prediction
            predictions["budget_forecast"] = self._predict_budget_utilization(
                project_id
            )

            # Resource demand prediction
            predictions["resource_demand"] = self._predict_resource_demand()

            # Risk probability analysis
            predictions["risk_analysis"] = self._predict_project_risks(project_id)

            return predictions
        except Exception as e:
            logger.error(f"Failed to get predictive analytics: {str(e)}")
            return {}

    def export_analytics_data(
        self, analytics_type: str, format: str = "json", filters: Optional[Dict] = None
    ) -> Optional[bytes]:
        """Export analytics data in various formats"""
        try:
            # Get data based on type
            if analytics_type == "projects":
                data = self.get_project_analytics()
            elif analytics_type == "team":
                data = self.get_team_analytics()
            elif analytics_type == "kpis":
                data = {"kpis": [kpi.__dict__ for kpi in self.get_dashboard_kpis()]}
            else:
                return None

            # Apply filters if provided
            if filters:
                data = self._apply_filters(data, filters)

            # Export in requested format
            if format == "json":
                return json.dumps(data, default=str, indent=2).encode("utf-8")
            elif format == "csv":
                return self._export_to_csv(data)
            elif format == "excel":
                return self._export_to_excel(data)
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to export analytics data: {str(e)}")
            return None

    # Private helper methods
    def _get_project_summary(
        self, project_id: Optional[int], date_range: Tuple[datetime, datetime]
    ) -> Dict:
        """Get project summary statistics"""
        try:
            where_clause = ""
            params = []

            if project_id:
                where_clause = "WHERE p.ProjectID = ?"
                params.append(project_id)

            query = f"""
            SELECT 
                COUNT(*) as total_projects,
                SUM(CASE WHEN p.Status = 'Completed' THEN 1 ELSE 0 END) as completed_projects,
                SUM(CASE WHEN p.Status = 'In Progress' THEN 1 ELSE 0 END) as active_projects,
                SUM(CASE WHEN p.Status = 'On Hold' THEN 1 ELSE 0 END) as on_hold_projects,
                AVG(p.Progress) as avg_progress,
                SUM(ISNULL(p.Budget, 0)) as total_budget,
                SUM(ISNULL(p.ActualBudget, 0)) as total_spent
            FROM Projects p
            {where_clause}
            """

            result = self.db_service.connection_manager.execute_query(
                query, tuple(params)
            )
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Failed to get project summary: {str(e)}")
            return {}

    def _calculate_project_completion_rate(self) -> Dict:
        """Calculate project completion rate and trend"""
        try:
            # Current month
            current_month_start = datetime.now().replace(day=1)
            current_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM Projects
            WHERE CreatedDate >= ?
            """
            current_result = self.db_service.connection_manager.execute_query(
                current_query, (current_month_start,)
            )

            # Previous month
            previous_month_start = (current_month_start - timedelta(days=1)).replace(
                day=1
            )
            previous_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM Projects
            WHERE CreatedDate >= ? AND CreatedDate < ?
            """
            previous_result = self.db_service.connection_manager.execute_query(
                previous_query, (previous_month_start, current_month_start)
            )

            # Calculate rates
            current_rate = 0
            if current_result and current_result[0]["total"] > 0:
                current_rate = (
                    current_result[0]["completed"] / current_result[0]["total"]
                ) * 100

            previous_rate = 0
            if previous_result and previous_result[0]["total"] > 0:
                previous_rate = (
                    previous_result[0]["completed"] / previous_result[0]["total"]
                ) * 100

            trend = current_rate - previous_rate

            return {"current": current_rate, "previous": previous_rate, "trend": trend}
        except Exception as e:
            logger.error(f"Failed to calculate project completion rate: {str(e)}")
            return {"current": 0, "previous": 0, "trend": 0}

    def _calculate_task_completion_rate(self) -> Dict:
        """Calculate task completion rate and trend"""
        try:
            # Current week
            current_week_start = datetime.now() - timedelta(
                days=datetime.now().weekday()
            )
            current_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed
            FROM Tasks
            WHERE CreatedDate >= ?
            """
            current_result = self.db_service.connection_manager.execute_query(
                current_query, (current_week_start,)
            )

            # Previous week
            previous_week_start = current_week_start - timedelta(days=7)
            previous_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed
            FROM Tasks
            WHERE CreatedDate >= ? AND CreatedDate < ?
            """
            previous_result = self.db_service.connection_manager.execute_query(
                previous_query, (previous_week_start, current_week_start)
            )

            # Calculate rates
            current_rate = 0
            if current_result and current_result[0]["total"] > 0:
                current_rate = (
                    current_result[0]["completed"] / current_result[0]["total"]
                ) * 100

            previous_rate = 0
            if previous_result and previous_result[0]["total"] > 0:
                previous_rate = (
                    previous_result[0]["completed"] / previous_result[0]["total"]
                ) * 100

            trend = current_rate - previous_rate

            return {"current": current_rate, "previous": previous_rate, "trend": trend}
        except Exception as e:
            logger.error(f"Failed to calculate task completion rate: {str(e)}")
            return {"current": 0, "previous": 0, "trend": 0}

    def _calculate_average_project_duration(self) -> Dict:
        """Calculate average project duration and trend"""
        try:
            # Current completed projects (last 3 months)
            three_months_ago = datetime.now() - timedelta(days=90)
            current_query = """
            SELECT AVG(DATEDIFF(day, StartDate, EndDate)) as avg_duration
            FROM Projects
            WHERE Status = 'Completed' AND EndDate >= ?
            """
            current_result = self.db_service.connection_manager.execute_query(
                current_query, (three_months_ago,)
            )

            # Previous period (3-6 months ago)
            six_months_ago = datetime.now() - timedelta(days=180)
            previous_query = """
            SELECT AVG(DATEDIFF(day, StartDate, EndDate)) as avg_duration
            FROM Projects
            WHERE Status = 'Completed' AND EndDate >= ? AND EndDate < ?
            """
            previous_result = self.db_service.connection_manager.execute_query(
                previous_query, (six_months_ago, three_months_ago)
            )

            current_duration = (
                current_result[0]["avg_duration"]
                if current_result and current_result[0]["avg_duration"]
                else 0
            )
            previous_duration = (
                previous_result[0]["avg_duration"]
                if previous_result and previous_result[0]["avg_duration"]
                else 0
            )

            # Calculate trend (negative is better for duration)
            trend = (
                ((current_duration - previous_duration) / previous_duration * 100)
                if previous_duration > 0
                else 0
            )

            return {
                "current": current_duration,
                "previous": previous_duration,
                "trend": -trend,  # Negative because lower duration is better
            }
        except Exception as e:
            logger.error(f"Failed to calculate average project duration: {str(e)}")
            return {"current": 0, "previous": 0, "trend": 0}

    def _calculate_team_utilization(self) -> Dict:
        """Calculate team utilization rate"""
        try:
            # Get active users and their task assignments
            query = """
            SELECT 
                u.UserID,
                u.FirstName + ' ' + u.LastName as UserName,
                COUNT(t.TaskID) as assigned_tasks,
                SUM(CASE WHEN t.Status IN ('In Progress', 'Review') THEN 1 ELSE 0 END) as active_tasks,
                AVG(CASE WHEN t.EstimatedHours > 0 THEN t.EstimatedHours ELSE 8 END) as avg_hours
            FROM Users u
            LEFT JOIN Tasks t ON u.UserID = t.AssigneeID
            WHERE u.IsActive = 1
            GROUP BY u.UserID, u.FirstName, u.LastName
            """

            result = self.db_service.connection_manager.execute_query(query)

            if not result:
                return {"current": 0, "previous": 0, "trend": 0}

            # Calculate utilization (simplified calculation)
            total_capacity = len(result) * 40  # 40 hours per week per person
            total_assigned = sum(
                row["active_tasks"] * 8 for row in result
            )  # 8 hours per active task

            current_utilization = (
                (total_assigned / total_capacity * 100) if total_capacity > 0 else 0
            )

            # For trend, we'll use a simplified calculation (in real app, store historical data)
            previous_utilization = current_utilization * 0.95  # Simulate 5% improvement
            trend = current_utilization - previous_utilization

            return {
                "current": min(current_utilization, 100),  # Cap at 100%
                "previous": previous_utilization,
                "trend": trend,
            }
        except Exception as e:
            logger.error(f"Failed to calculate team utilization: {str(e)}")
            return {"current": 0, "previous": 0, "trend": 0}

    def _calculate_budget_utilization(self) -> Dict:
        """Calculate budget utilization rate"""
        try:
            query = """
            SELECT 
                SUM(ISNULL(Budget, 0)) as total_budget,
                SUM(ISNULL(ActualBudget, 0)) as total_spent
            FROM Projects
            WHERE Status IN ('In Progress', 'Completed')
            """

            result = self.db_service.connection_manager.execute_query(query)

            if not result or not result[0]["total_budget"]:
                return {"current": 0, "previous": 0, "trend": 0}

            current_utilization = (
                result[0]["total_spent"] / result[0]["total_budget"] * 100
            )

            # Simulate previous period data
            previous_utilization = current_utilization * 0.9
            trend = current_utilization - previous_utilization

            return {
                "current": current_utilization,
                "previous": previous_utilization,
                "trend": trend,
            }
        except Exception as e:
            logger.error(f"Failed to calculate budget utilization: {str(e)}")
            return {"current": 0, "previous": 0, "trend": 0}

    def _get_kpi_status(
        self,
        current: float,
        target: float,
        comparison_type: str,
        optimal_range: Optional[Tuple[float, float]] = None,
    ) -> str:
        """Determine KPI status based on current value vs target"""
        if comparison_type == "higher_better":
            if current >= target:
                return "good"
            elif current >= target * 0.8:
                return "warning"
            else:
                return "critical"
        elif comparison_type == "lower_better":
            if current <= target:
                return "good"
            elif current <= target * 1.2:
                return "warning"
            else:
                return "critical"
        elif comparison_type == "optimal_range" and optimal_range:
            if optimal_range[0] <= current <= optimal_range[1]:
                return "good"
            elif abs(current - target) <= target * 0.1:
                return "warning"
            else:
                return "critical"

        return "warning"

    def _get_project_status_trend(self, date_range: Tuple[datetime, datetime]) -> Dict:
        """Get project status trend over time"""
        try:
            query = """
            SELECT 
                CAST(CreatedDate as DATE) as date,
                Status,
                COUNT(*) as count
            FROM Projects
            WHERE CreatedDate BETWEEN ? AND ?
            GROUP BY CAST(CreatedDate as DATE), Status
            ORDER BY date
            """

            result = self.db_service.connection_manager.execute_query(
                query, (date_range[0], date_range[1])
            )

            # Process data for chart
            dates = list(set(row["date"].strftime("%Y-%m-%d") for row in result))
            dates.sort()

            statuses = ["Planning", "In Progress", "Review", "Completed", "On Hold"]

            chart_data = {"dates": dates, "series": []}

            for status in statuses:
                status_data = [
                    sum(
                        row["count"]
                        for row in result
                        if row["date"].strftime("%Y-%m-%d") == date
                        and row["Status"] == status
                    )
                    for date in dates
                ]
                chart_data["series"].append({"name": status, "data": status_data})

            return chart_data
        except Exception as e:
            logger.error(f"Failed to get project status trend: {str(e)}")
            return {}

    def _get_resource_allocation_chart(
        self, date_range: Tuple[datetime, datetime]
    ) -> Dict:
        """Get resource allocation chart data"""
        try:
            query = """
            SELECT 
                u.FirstName + ' ' + u.LastName as user_name,
                u.Department,
                COUNT(t.TaskID) as task_count,
                SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks
            FROM Users u
            LEFT JOIN Tasks t ON u.UserID = t.AssigneeID 
                AND t.CreatedDate BETWEEN ? AND ?
            WHERE u.IsActive = 1
            GROUP BY u.UserID, u.FirstName, u.LastName, u.Department
            ORDER BY task_count DESC
            """

            result = self.db_service.connection_manager.execute_query(
                query, (date_range[0], date_range[1])
            )

            return {
                "users": [row["user_name"] for row in result],
                "task_counts": [row["task_count"] for row in result],
                "completed_counts": [row["completed_tasks"] for row in result],
                "departments": [row["Department"] or "Unknown" for row in result],
            }
        except Exception as e:
            logger.error(f"Failed to get resource allocation chart: {str(e)}")
            return {}

    def _get_budget_vs_actual_chart(
        self, date_range: Tuple[datetime, datetime]
    ) -> Dict:
        """Get budget vs actual spending chart data"""
        try:
            query = """
            SELECT 
                ProjectName,
                ISNULL(Budget, 0) as budget,
                ISNULL(ActualBudget, 0) as actual,
                Status
            FROM Projects
            WHERE CreatedDate BETWEEN ? AND ?
            AND Budget > 0
            ORDER BY Budget DESC
            """

            result = self.db_service.connection_manager.execute_query(
                query, (date_range[0], date_range[1])
            )

            return {
                "projects": [row["ProjectName"] for row in result],
                "budgets": [float(row["budget"]) for row in result],
                "actuals": [float(row["actual"]) for row in result],
                "statuses": [row["Status"] for row in result],
            }
        except Exception as e:
            logger.error(f"Failed to get budget vs actual chart: {str(e)}")
            return {}

    def _get_timeline_performance_chart(
        self, date_range: Tuple[datetime, datetime]
    ) -> Dict:
        """Get timeline performance chart data"""
        try:
            query = """
            SELECT 
                ProjectName,
                StartDate,
                EndDate,
                Status,
                Progress,
                DATEDIFF(day, StartDate, ISNULL(EndDate, GETDATE())) as actual_duration,
                DATEDIFF(day, StartDate, EndDate) as planned_duration
            FROM Projects
            WHERE StartDate BETWEEN ? AND ?
            """

            result = self.db_service.connection_manager.execute_query(
                query, (date_range[0], date_range[1])
            )

            return {
                "projects": [row["ProjectName"] for row in result],
                "planned_durations": [row["planned_duration"] or 0 for row in result],
                "actual_durations": [row["actual_duration"] or 0 for row in result],
                "progress": [row["Progress"] or 0 for row in result],
                "statuses": [row["Status"] for row in result],
            }
        except Exception as e:
            logger.error(f"Failed to get timeline performance chart: {str(e)}")
            return {}

    def _generate_recommendations(
        self, kpis: List[KPIMetric], charts_data: Dict
    ) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []

        try:
            # Analyze KPIs for recommendations
            for kpi in kpis:
                if kpi.status == "critical":
                    if "completion rate" in kpi.name.lower():
                        recommendations.append(
                            f"🔴 Critical: {kpi.name} is at {kpi.value:.1f}%, well below target of {kpi.target:.1f}%. "
                            "Consider reviewing project methodologies and team capacity."
                        )
                    elif "duration" in kpi.name.lower():
                        recommendations.append(
                            f"🔴 Critical: Projects are taking {kpi.value:.0f} days on average, exceeding target of {kpi.target:.0f} days. "
                            "Review project scoping and resource allocation."
                        )
                elif kpi.status == "warning":
                    recommendations.append(
                        f"🟡 Warning: {kpi.name} needs attention. Current value: {kpi.value:.1f}%, Target: {kpi.target:.1f}%."
                    )

            # Resource allocation recommendations
            if "resource_allocation" in charts_data:
                resource_data = charts_data["resource_allocation"]
                if resource_data.get("task_counts"):
                    max_tasks = max(resource_data["task_counts"])
                    min_tasks = min(resource_data["task_counts"])
                    if max_tasks > min_tasks * 3:  # High variance in task distribution
                        recommendations.append(
                            "⚖️ Consider rebalancing workload - some team members have significantly more tasks than others."
                        )

            # Budget recommendations
            if "budget_vs_actual" in charts_data:
                budget_data = charts_data["budget_vs_actual"]
                if budget_data.get("budgets") and budget_data.get("actuals"):
                    over_budget_count = sum(
                        1
                        for i, actual in enumerate(budget_data["actuals"])
                        if actual > budget_data["budgets"][i] * 1.1
                    )
                    if over_budget_count > 0:
                        recommendations.append(
                            f"💰 {over_budget_count} project(s) are significantly over budget. Review cost control measures."
                        )

            # Default recommendations if none generated
            if not recommendations:
                recommendations.extend(
                    [
                        "✅ Overall performance looks good. Continue monitoring key metrics.",
                        "📈 Consider setting up automated alerts for critical KPI thresholds.",
                        "👥 Regular team check-ins can help maintain current performance levels.",
                    ]
                )

            return recommendations[:5]  # Limit to 5 recommendations
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return ["Unable to generate recommendations at this time."]

    def _calculate_timeline_factor(self, project_id: int) -> float:
        """Calculate timeline performance factor for health score"""
        try:
            query = """
            SELECT 
                StartDate,
                EndDate,
                Progress,
                Status
            FROM Projects
            WHERE ProjectID = ?
            """

            result = self.db_service.connection_manager.execute_query(
                query, (project_id,)
            )
            if not result:
                return 50.0

            project = result[0]

            # If completed, check if on time
            if project["Status"] == "Completed":
                return 90.0 if project["EndDate"] <= project["EndDate"] else 60.0

            # For active projects, check progress vs time elapsed
            if project["StartDate"] and project["EndDate"]:
                total_duration = (project["EndDate"] - project["StartDate"]).days
                elapsed_duration = (datetime.now().date() - project["StartDate"]).days

                if total_duration > 0:
                    expected_progress = (elapsed_duration / total_duration) * 100
                    actual_progress = project.get("Progress", 0)

                    # Calculate factor based on progress vs expected
                    if actual_progress >= expected_progress:
                        return min(100.0, 70 + (actual_progress - expected_progress))
                    else:
                        return max(0.0, 70 - (expected_progress - actual_progress))

            return 70.0  # Default for projects without clear timeline
        except Exception as e:
            logger.error(f"Failed to calculate timeline factor: {str(e)}")
            return 50.0

    def _calculate_budget_factor(self, project_id: int) -> float:
        """Calculate budget performance factor for health score"""
        try:
            query = """
            SELECT Budget, ActualBudget, Status
            FROM Projects
            WHERE ProjectID = ?
            """

            result = self.db_service.connection_manager.execute_query(
                query, (project_id,)
            )
            if not result or not result[0]["Budget"]:
                return 70.0  # Default if no budget info

            project = result[0]
            budget = float(project["Budget"])
            actual = float(project.get("ActualBudget", 0))

            if budget <= 0:
                return 70.0

            utilization = (actual / budget) * 100

            # Score based on budget utilization
            if utilization <= 80:
                return 100.0  # Under budget
            elif utilization <= 100:
                return 90.0  # On budget
            elif utilization <= 110:
                return 60.0  # Slightly over
            else:
                return 30.0  # Significantly over
        except Exception as e:
            logger.error(f"Failed to calculate budget factor: {str(e)}")
            return 50.0

    def _calculate_quality_factor(self, project_id: int) -> float:
        """Calculate quality factor based on task completion and rework"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN Status = 'Review' THEN 1 ELSE 0 END) as review_tasks
            FROM Tasks
            WHERE ProjectID = ?
            """

            result = self.db_service.connection_manager.execute_query(
                query, (project_id,)
            )
            if not result or result[0]["total_tasks"] == 0:
                return 70.0

            data = result[0]
            completion_rate = (data["completed_tasks"] / data["total_tasks"]) * 100
            review_rate = (data["review_tasks"] / data["total_tasks"]) * 100

            # Higher completion rate and lower review rate indicate better quality
            quality_score = completion_rate - (review_rate * 0.5)
            return max(0.0, min(100.0, quality_score))
        except Exception as e:
            logger.error(f"Failed to calculate quality factor: {str(e)}")
            return 50.0

    def _calculate_team_performance_factor(self, project_id: int) -> float:
        """Calculate team performance factor for health score"""
        try:
            query = """
            SELECT 
                COUNT(DISTINCT t.AssigneeID) as team_size,
                AVG(CASE WHEN t.Status = 'Done' THEN 1.0 ELSE 0.0 END) as completion_rate,
                COUNT(*) as total_tasks
            FROM Tasks t
            WHERE t.ProjectID = ? AND t.AssigneeID IS NOT NULL
            """

            result = self.db_service.connection_manager.execute_query(
                query, (project_id,)
            )
            if not result:
                return 70.0

            data = result[0]

            # Score based on team completion rate and engagement
            completion_rate = (data.get("completion_rate", 0) or 0) * 100

            # Bonus for having appropriate team size
            team_size = data.get("team_size", 0) or 0
            size_bonus = min(10, team_size * 2)  # Up to 10 points for team size

            return min(100.0, completion_rate + size_bonus)
        except Exception as e:
            logger.error(f"Failed to calculate team performance factor: {str(e)}")
            return 50.0

    def _calculate_scope_factor(self, project_id: int) -> float:
        """Calculate scope management factor (simplified)"""
        try:
            # Simplified calculation based on task additions over time
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN CreatedDate > (
                    SELECT DATEADD(week, 1, MIN(CreatedDate)) 
                    FROM Tasks WHERE ProjectID = ?
                ) THEN 1 END) as late_additions
            FROM Tasks
            WHERE ProjectID = ?
            """

            result = self.db_service.connection_manager.execute_query(
                query, (project_id, project_id)
            )
            if not result or result[0]["total_tasks"] == 0:
                return 80.0

            data = result[0]
            scope_creep_rate = (data["late_additions"] / data["total_tasks"]) * 100

            # Lower scope creep is better
            return max(20.0, 100.0 - scope_creep_rate)
        except Exception as e:
            logger.error(f"Failed to calculate scope factor: {str(e)}")
            return 70.0

    def _calculate_risk_factor(self, project_id: int) -> float:
        """Calculate risk factor based on overdue tasks and blockers"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN DueDate < GETDATE() AND Status NOT IN ('Done', 'Cancelled') THEN 1 ELSE 0 END) as overdue_tasks,
                SUM(CASE WHEN Status = 'Blocked' THEN 1 ELSE 0 END) as blocked_tasks
            FROM Tasks
            WHERE ProjectID = ?
            """

            result = self.db_service.connection_manager.execute_query(
                query, (project_id,)
            )
            if not result or result[0]["total_tasks"] == 0:
                return 80.0

            data = result[0]
            overdue_rate = (data["overdue_tasks"] / data["total_tasks"]) * 100
            blocked_rate = (data["blocked_tasks"] / data["total_tasks"]) * 100

            # Lower rates are better
            risk_score = 100.0 - (overdue_rate * 1.5) - (blocked_rate * 2.0)
            return max(0.0, risk_score)
        except Exception as e:
            logger.error(f"Failed to calculate risk factor: {str(e)}")
            return 70.0

    def _get_health_recommendations(self, factors: Dict) -> List[str]:
        """Generate recommendations based on health factors"""
        recommendations = []

        for factor, score in factors.items():
            if score < 50:
                if factor == "timeline":
                    recommendations.append(
                        "⏰ Focus on timeline management - consider adding resources or adjusting scope"
                    )
                elif factor == "budget":
                    recommendations.append(
                        "💰 Review budget controls - costs are exceeding planned amounts"
                    )
                elif factor == "quality":
                    recommendations.append(
                        "🎯 Implement quality checks - high rework rate detected"
                    )
                elif factor == "team_performance":
                    recommendations.append(
                        "👥 Support team performance - consider training or workload adjustment"
                    )
                elif factor == "scope":
                    recommendations.append(
                        "📋 Control scope creep - too many late additions to project"
                    )
                elif factor == "risks":
                    recommendations.append(
                        "⚠️ Address project risks - high number of overdue or blocked tasks"
                    )

        if not recommendations:
            recommendations.append("✅ Project health looks good overall")

        return recommendations


# Global analytics service instance
analytics_service = None


def get_analytics_service(db_service):
    """Get or create analytics service instance"""
    global analytics_service
    if analytics_service is None:
        analytics_service = AnalyticsService(db_service)
    return analytics_service
