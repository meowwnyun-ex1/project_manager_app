#!/usr/bin/env python3
"""
modules/enhanced_reports.py
Advanced Analytics and Reporting System for DENSO Project Manager Pro
รองรับการวิเคราะห์ข้อมูลขั้นสูง, การสร้างรายงาน, และ Business Intelligence
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import io
import base64
from dataclasses import dataclass
from enum import Enum
import statistics
import scipy.stats as stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import warnings

warnings.filterwarnings("ignore")

from utils.error_handler import safe_execute, handle_error, validate_input
from utils.ui_components import UIComponents

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Report types enumeration"""

    PROJECT_SUMMARY = "project_summary"
    TEAM_PERFORMANCE = "team_performance"
    RESOURCE_UTILIZATION = "resource_utilization"
    BUDGET_ANALYSIS = "budget_analysis"
    TIMELINE_ANALYSIS = "timeline_analysis"
    QUALITY_METRICS = "quality_metrics"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    CUSTOM_REPORT = "custom_report"


@dataclass
class ReportConfig:
    """Report configuration"""

    report_type: ReportType
    date_range: Tuple[date, date]
    filters: Dict[str, Any]
    visualization_type: str
    export_format: str
    include_raw_data: bool = False
    include_charts: bool = True
    include_summary: bool = True


class AdvancedAnalyticsEngine:
    """Advanced analytics and reporting engine"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.ui = UIComponents()
        self.cache = {}  # Simple caching mechanism
        self.report_templates = {}
        self._init_report_templates()

    def _init_report_templates(self):
        """Initialize report templates"""
        self.report_templates = {
            ReportType.PROJECT_SUMMARY: {
                "title": "รายงานสรุปโครงการ",
                "description": "ภาพรวมสถานะและความคืบหน้าของโครงการ",
                "charts": [
                    "status_distribution",
                    "progress_timeline",
                    "budget_vs_actual",
                ],
                "metrics": [
                    "total_projects",
                    "completion_rate",
                    "budget_variance",
                    "timeline_variance",
                ],
            },
            ReportType.TEAM_PERFORMANCE: {
                "title": "รายงานประสิทธิภาพทีม",
                "description": "การประเมินผลงานและประสิทธิภาพของทีม",
                "charts": [
                    "team_productivity",
                    "workload_distribution",
                    "performance_trends",
                ],
                "metrics": [
                    "productivity_score",
                    "task_completion_rate",
                    "quality_score",
                    "efficiency_index",
                ],
            },
            ReportType.RESOURCE_UTILIZATION: {
                "title": "รายงานการใช้ทรัพยากร",
                "description": "การวิเคราะห์การใช้ทรัพยากรและค่าใช้จ่าย",
                "charts": [
                    "resource_allocation",
                    "cost_breakdown",
                    "utilization_trends",
                ],
                "metrics": [
                    "utilization_rate",
                    "cost_efficiency",
                    "resource_allocation_index",
                ],
            },
            ReportType.BUDGET_ANALYSIS: {
                "title": "รายงานการวิเคราะห์งบประมาณ",
                "description": "การติดตามและวิเคราะห์งบประมาณโครงการ",
                "charts": ["budget_vs_actual", "cost_trends", "budget_variance"],
                "metrics": [
                    "budget_variance",
                    "cost_performance_index",
                    "budget_utilization",
                ],
            },
            ReportType.TIMELINE_ANALYSIS: {
                "title": "รายงานการวิเคราะห์ไทม์ไลน์",
                "description": "การติดตามเวลาและความล่าช้าของโครงการ",
                "charts": ["timeline_gantt", "delay_analysis", "milestone_tracking"],
                "metrics": [
                    "schedule_performance_index",
                    "average_delay",
                    "on_time_delivery_rate",
                ],
            },
            ReportType.QUALITY_METRICS: {
                "title": "รายงานคุณภาพ",
                "description": "การประเมินคุณภาพของงานและโครงการ",
                "charts": ["quality_trends", "defect_analysis", "rework_metrics"],
                "metrics": [
                    "quality_score",
                    "defect_rate",
                    "rework_percentage",
                    "customer_satisfaction",
                ],
            },
            ReportType.PREDICTIVE_ANALYSIS: {
                "title": "รายงานการวิเคราะห์เชิงพยากรณ์",
                "description": "การพยากรณ์และแนวโน้มในอนาคต",
                "charts": ["forecast_timeline", "risk_analysis", "trend_prediction"],
                "metrics": ["completion_forecast", "budget_forecast", "risk_score"],
            },
        }

    def generate_comprehensive_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate comprehensive report based on configuration"""
        try:
            report_data = {
                "metadata": {
                    "report_type": config.report_type.value,
                    "generated_at": datetime.now(),
                    "date_range": config.date_range,
                    "filters": config.filters,
                },
                "summary": {},
                "metrics": {},
                "charts": {},
                "raw_data": {},
                "insights": [],
                "recommendations": [],
            }

            # Generate data based on report type
            if config.report_type == ReportType.PROJECT_SUMMARY:
                report_data.update(self._generate_project_summary_report(config))
            elif config.report_type == ReportType.TEAM_PERFORMANCE:
                report_data.update(self._generate_team_performance_report(config))
            elif config.report_type == ReportType.RESOURCE_UTILIZATION:
                report_data.update(self._generate_resource_utilization_report(config))
            elif config.report_type == ReportType.BUDGET_ANALYSIS:
                report_data.update(self._generate_budget_analysis_report(config))
            elif config.report_type == ReportType.TIMELINE_ANALYSIS:
                report_data.update(self._generate_timeline_analysis_report(config))
            elif config.report_type == ReportType.QUALITY_METRICS:
                report_data.update(self._generate_quality_metrics_report(config))
            elif config.report_type == ReportType.PREDICTIVE_ANALYSIS:
                report_data.update(self._generate_predictive_analysis_report(config))

            # Generate insights and recommendations
            report_data["insights"] = self._generate_insights(report_data)
            report_data["recommendations"] = self._generate_recommendations(report_data)

            return report_data

        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {"error": str(e)}

    def _generate_project_summary_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate project summary report"""
        try:
            start_date, end_date = config.date_range

            # Get project data
            query = """
                SELECT p.ProjectID, p.Name, p.Status, p.Priority, p.Budget, p.ActualCost,
                       p.CompletionPercentage, p.StartDate, p.EndDate, p.CreatedDate,
                       p.ClientName, u.FirstName + ' ' + u.LastName as ManagerName,
                       COUNT(t.TaskID) as TotalTasks,
                       SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
                       SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as OverdueTasks,
                       AVG(CASE WHEN t.ActualHours > 0 AND t.EstimatedHours > 0 
                           THEN ABS(t.ActualHours - t.EstimatedHours) / t.EstimatedHours * 100 
                           ELSE NULL END) as AvgEstimationVariance
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
                LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
                WHERE p.CreatedDate BETWEEN ? AND ?
                GROUP BY p.ProjectID, p.Name, p.Status, p.Priority, p.Budget, p.ActualCost,
                         p.CompletionPercentage, p.StartDate, p.EndDate, p.CreatedDate,
                         p.ClientName, u.FirstName, u.LastName
                ORDER BY p.CreatedDate DESC
            """

            projects_data = self.db.execute_query(query, (start_date, end_date))

            if not projects_data:
                return {"summary": {"message": "ไม่มีข้อมูลโครงการในช่วงเวลาที่เลือก"}}

            df = pd.DataFrame(projects_data)

            # Calculate summary metrics
            summary = {
                "total_projects": len(df),
                "active_projects": len(
                    df[df["Status"].isin(["Planning", "In Progress"])]
                ),
                "completed_projects": len(df[df["Status"] == "Completed"]),
                "on_hold_projects": len(df[df["Status"] == "On Hold"]),
                "cancelled_projects": len(df[df["Status"] == "Cancelled"]),
                "total_budget": df["Budget"].sum(),
                "total_actual_cost": df["ActualCost"].sum(),
                "avg_completion_rate": df["CompletionPercentage"].mean(),
                "budget_variance": (
                    (
                        (df["ActualCost"].sum() - df["Budget"].sum())
                        / df["Budget"].sum()
                        * 100
                    )
                    if df["Budget"].sum() > 0
                    else 0
                ),
                "total_tasks": df["TotalTasks"].sum(),
                "total_completed_tasks": df["CompletedTasks"].sum(),
                "total_overdue_tasks": df["OverdueTasks"].sum(),
            }

            # Generate charts
            charts = {}

            # Status distribution
            status_counts = df["Status"].value_counts()
            charts["status_distribution"] = {
                "type": "pie",
                "data": {
                    "labels": status_counts.index.tolist(),
                    "values": status_counts.values.tolist(),
                },
                "title": "การกระจายสถานะโครงการ",
            }

            # Progress vs Budget
            charts["progress_vs_budget"] = {
                "type": "scatter",
                "data": {
                    "x": df["CompletionPercentage"].tolist(),
                    "y": df["Budget"].tolist(),
                    "text": df["Name"].tolist(),
                    "size": df["TotalTasks"].tolist(),
                },
                "title": "ความคืบหน้า vs งบประมาณ",
            }

            # Priority distribution
            priority_counts = df["Priority"].value_counts()
            charts["priority_distribution"] = {
                "type": "bar",
                "data": {
                    "x": priority_counts.index.tolist(),
                    "y": priority_counts.values.tolist(),
                },
                "title": "การกระจายตามความสำคัญ",
            }

            return {
                "summary": summary,
                "charts": charts,
                "raw_data": {"projects": projects_data},
            }

        except Exception as e:
            logger.error(f"Error generating project summary report: {e}")
            return {"error": str(e)}

    def _generate_team_performance_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate team performance report"""
        try:
            start_date, end_date = config.date_range

            # Get team performance data
            query = """
                SELECT u.UserID, u.FirstName + ' ' + u.LastName as UserName, u.Role, u.Department,
                       COUNT(t.TaskID) as TotalTasks,
                       SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
                       SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as OverdueTasks,
                       AVG(CAST(t.CompletionPercentage as FLOAT)) as AvgCompletion,
                       SUM(CASE WHEN t.ActualHours IS NOT NULL THEN t.ActualHours ELSE 0 END) as TotalHours,
                       AVG(CASE WHEN t.ActualHours > 0 AND t.EstimatedHours > 0 
                           THEN ABS(t.ActualHours - t.EstimatedHours) / t.EstimatedHours * 100 
                           ELSE NULL END) as EstimationAccuracy,
                       COUNT(DISTINCT t.ProjectID) as ProjectsWorkedOn
                FROM Users u
                LEFT JOIN Tasks t ON u.UserID = t.AssignedToID 
                    AND t.CreatedDate BETWEEN ? AND ?
                WHERE u.IsActive = 1 AND u.Role IN ('Developer', 'Team Lead', 'Project Manager')
                GROUP BY u.UserID, u.FirstName, u.LastName, u.Role, u.Department
                HAVING COUNT(t.TaskID) > 0
                ORDER BY CompletedTasks DESC, AvgCompletion DESC
            """

            team_data = self.db.execute_query(query, (start_date, end_date))

            if not team_data:
                return {"summary": {"message": "ไม่มีข้อมูลทีมในช่วงเวลาที่เลือก"}}

            df = pd.DataFrame(team_data)

            # Calculate performance scores
            df["CompletionRate"] = (df["CompletedTasks"] / df["TotalTasks"]) * 100
            df["OnTimeRate"] = (
                (df["TotalTasks"] - df["OverdueTasks"]) / df["TotalTasks"]
            ) * 100
            df["ProductivityScore"] = (
                df["CompletionRate"] * 0.4
                + df["OnTimeRate"] * 0.3
                + df["AvgCompletion"] * 0.3
            )

            # Summary metrics
            summary = {
                "total_team_members": len(df),
                "avg_completion_rate": df["CompletionRate"].mean(),
                "avg_productivity_score": df["ProductivityScore"].mean(),
                "total_hours_logged": df["TotalHours"].sum(),
                "avg_estimation_accuracy": df["EstimationAccuracy"].mean(),
                "top_performer": (
                    df.loc[df["ProductivityScore"].idxmax(), "UserName"]
                    if len(df) > 0
                    else None
                ),
                "most_tasks_completed": (
                    df.loc[df["CompletedTasks"].idxmax(), "UserName"]
                    if len(df) > 0
                    else None
                ),
            }

            # Generate charts
            charts = {}

            # Team productivity comparison
            charts["team_productivity"] = {
                "type": "bar",
                "data": {
                    "x": df["UserName"].tolist(),
                    "y": df["ProductivityScore"].tolist(),
                },
                "title": "คะแนนประสิทธิภาพทีม",
            }

            # Workload distribution
            charts["workload_distribution"] = {
                "type": "bar",
                "data": {"x": df["UserName"].tolist(), "y": df["TotalTasks"].tolist()},
                "title": "การกระจายปริมาณงาน",
            }

            # Completion rate vs On-time rate
            charts["completion_vs_ontime"] = {
                "type": "scatter",
                "data": {
                    "x": df["CompletionRate"].tolist(),
                    "y": df["OnTimeRate"].tolist(),
                    "text": df["UserName"].tolist(),
                    "size": df["TotalTasks"].tolist(),
                },
                "title": "อัตราความสำเร็จ vs การส่งตรงเวลา",
            }

            return {
                "summary": summary,
                "charts": charts,
                "raw_data": {"team_performance": team_data},
            }

        except Exception as e:
            logger.error(f"Error generating team performance report: {e}")
            return {"error": str(e)}

    def _generate_budget_analysis_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate budget analysis report with advanced financial metrics"""
        try:
            start_date, end_date = config.date_range

            # Get budget data
            query = """
                SELECT p.ProjectID, p.Name, p.Budget, p.ActualCost, p.Status,
                       p.StartDate, p.EndDate, p.CompletionPercentage,
                       CASE WHEN p.Budget > 0 THEN (p.ActualCost / p.Budget) * 100 ELSE 0 END as BudgetUtilization,
                       CASE WHEN p.Budget > 0 THEN ((p.ActualCost - p.Budget) / p.Budget) * 100 ELSE 0 END as BudgetVariance,
                       DATEDIFF(day, p.StartDate, GETDATE()) as ProjectAgeInDays,
                       CASE WHEN p.EndDate IS NOT NULL 
                            THEN DATEDIFF(day, p.StartDate, p.EndDate) 
                            ELSE NULL END as PlannedDurationInDays
                FROM Projects p
                WHERE p.CreatedDate BETWEEN ? AND ?
                AND p.Budget > 0
                ORDER BY p.Budget DESC
            """

            budget_data = self.db.execute_query(query, (start_date, end_date))

            if not budget_data:
                return {"summary": {"message": "ไม่มีข้อมูลงบประมาณในช่วงเวลาที่เลือก"}}

            df = pd.DataFrame(budget_data)

            # Calculate advanced financial metrics
            df["CostPerformanceIndex"] = df.apply(
                lambda row: (
                    (row["CompletionPercentage"] / 100 * row["Budget"])
                    / row["ActualCost"]
                    if row["ActualCost"] > 0
                    else 0
                ),
                axis=1,
            )

            df["EarnedValue"] = df["CompletionPercentage"] / 100 * df["Budget"]
            df["ScheduleVariance"] = df["EarnedValue"] - (
                df["CompletionPercentage"] / 100 * df["Budget"]
            )

            # ROI calculation (simplified)
            df["ProjectROI"] = df.apply(
                lambda row: (
                    ((row["Budget"] - row["ActualCost"]) / row["ActualCost"] * 100)
                    if row["ActualCost"] > 0
                    else 0
                ),
                axis=1,
            )

            # Summary metrics
            summary = {
                "total_budget": df["Budget"].sum(),
                "total_actual_cost": df["ActualCost"].sum(),
                "total_variance": df["Budget"].sum() - df["ActualCost"].sum(),
                "avg_budget_utilization": df["BudgetUtilization"].mean(),
                "avg_cost_performance_index": df["CostPerformanceIndex"].mean(),
                "projects_over_budget": len(df[df["BudgetVariance"] > 0]),
                "projects_under_budget": len(df[df["BudgetVariance"] < 0]),
                "highest_variance_project": (
                    df.loc[df["BudgetVariance"].abs().idxmax(), "Name"]
                    if len(df) > 0
                    else None
                ),
                "most_efficient_project": (
                    df.loc[df["CostPerformanceIndex"].idxmax(), "Name"]
                    if len(df) > 0
                    else None
                ),
                "avg_roi": df["ProjectROI"].mean(),
            }

            # Generate charts
            charts = {}

            # Budget vs Actual
            charts["budget_vs_actual"] = {
                "type": "bar",
                "data": {
                    "x": df["Name"].tolist(),
                    "y1": df["Budget"].tolist(),
                    "y2": df["ActualCost"].tolist(),
                },
                "title": "งบประมาณ vs ค่าใช้จ่ายจริง",
            }

            # Cost Performance Index
            charts["cost_performance_index"] = {
                "type": "bar",
                "data": {
                    "x": df["Name"].tolist(),
                    "y": df["CostPerformanceIndex"].tolist(),
                },
                "title": "ดัชนีประสิทธิภาพค่าใช้จ่าย (CPI)",
            }

            # Budget variance distribution
            variance_ranges = [
                "< -20%",
                "-20% to -10%",
                "-10% to 0%",
                "0% to 10%",
                "10% to 20%",
                "> 20%",
            ]
            variance_counts = [
                len(df[df["BudgetVariance"] < -20]),
                len(df[(df["BudgetVariance"] >= -20) & (df["BudgetVariance"] < -10)]),
                len(df[(df["BudgetVariance"] >= -10) & (df["BudgetVariance"] < 0)]),
                len(df[(df["BudgetVariance"] >= 0) & (df["BudgetVariance"] < 10)]),
                len(df[(df["BudgetVariance"] >= 10) & (df["BudgetVariance"] < 20)]),
                len(df[df["BudgetVariance"] >= 20]),
            ]

            charts["budget_variance_distribution"] = {
                "type": "bar",
                "data": {"x": variance_ranges, "y": variance_counts},
                "title": "การกระจายของความแปรปรวนงบประมาณ",
            }

            return {
                "summary": summary,
                "charts": charts,
                "raw_data": {"budget_analysis": budget_data},
            }

        except Exception as e:
            logger.error(f"Error generating budget analysis report: {e}")
            return {"error": str(e)}

    def _generate_predictive_analysis_report(
        self, config: ReportConfig
    ) -> Dict[str, Any]:
        """Generate predictive analysis report using machine learning"""
        try:
            start_date, end_date = config.date_range

            # Get historical data for prediction
            query = """
                SELECT p.ProjectID, p.Name, p.Budget, p.ActualCost, p.CompletionPercentage,
                       p.StartDate, p.EndDate, p.Status, p.Priority,
                       COUNT(t.TaskID) as TotalTasks,
                       SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
                       AVG(CASE WHEN t.ActualHours > 0 THEN t.ActualHours ELSE NULL END) as AvgTaskHours,
                       DATEDIFF(day, p.StartDate, GETDATE()) as ProjectAgeInDays,
                       CASE WHEN p.EndDate IS NOT NULL 
                            THEN DATEDIFF(day, p.StartDate, p.EndDate) 
                            ELSE NULL END as PlannedDurationInDays
                FROM Projects p
                LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
                WHERE p.StartDate >= DATEADD(month, -12, ?)
                GROUP BY p.ProjectID, p.Name, p.Budget, p.ActualCost, p.CompletionPercentage,
                         p.StartDate, p.EndDate, p.Status, p.Priority
                HAVING COUNT(t.TaskID) > 0
                ORDER BY p.StartDate
            """

            historical_data = self.db.execute_query(query, (start_date,))

            if len(historical_data) < 10:
                return {
                    "summary": {
                        "message": "ข้อมูลไม่เพียงพอสำหรับการวิเคราะห์เชิงพยากรณ์ (ต้องการอย่างน้อย 10 โครงการ)"
                    }
                }

            df = pd.DataFrame(historical_data)

            # Prepare data for machine learning
            df_ml = df.copy()

            # Feature engineering
            df_ml["TaskDensity"] = df_ml["TotalTasks"] / df_ml[
                "ProjectAgeInDays"
            ].replace(0, 1)
            df_ml["BudgetPerTask"] = df_ml["Budget"] / df_ml["TotalTasks"].replace(0, 1)
            df_ml["CompletionRate"] = df_ml["CompletedTasks"] / df_ml[
                "TotalTasks"
            ].replace(0, 1)

            # Encode categorical variables
            priority_mapping = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
            df_ml["PriorityScore"] = df_ml["Priority"].map(priority_mapping).fillna(2)

            # Select features for prediction
            feature_columns = [
                "Budget",
                "TotalTasks",
                "ProjectAgeInDays",
                "TaskDensity",
                "BudgetPerTask",
                "PriorityScore",
                "AvgTaskHours",
            ]

            # Remove rows with missing values
            df_clean = df_ml.dropna(subset=feature_columns + ["CompletionPercentage"])

            if len(df_clean) < 5:
                return {"summary": {"message": "ข้อมูลที่สมบูรณ์ไม่เพียงพอสำหรับการวิเคราะห์"}}

            X = df_clean[feature_columns]
            y = df_clean["CompletionPercentage"]

            # Train completion prediction model
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model = LinearRegression()
            model.fit(X_scaled, y)

            # Make predictions for active projects
            active_projects_query = """
                SELECT p.ProjectID, p.Name, p.Budget, p.ActualCost, p.CompletionPercentage,
                       p.StartDate, p.EndDate, p.Status, p.Priority,
                       COUNT(t.TaskID) as TotalTasks,
                       SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
                       AVG(CASE WHEN t.ActualHours > 0 THEN t.ActualHours ELSE NULL END) as AvgTaskHours,
                       DATEDIFF(day, p.StartDate, GETDATE()) as ProjectAgeInDays
                FROM Projects p
                LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
                WHERE p.Status IN ('Planning', 'In Progress')
                GROUP BY p.ProjectID, p.Name, p.Budget, p.ActualCost, p.CompletionPercentage,
                         p.StartDate, p.EndDate, p.Status, p.Priority
            """

            active_data = self.db.execute_query(active_projects_query)

            predictions = []
            if active_data:
                df_active = pd.DataFrame(active_data)

                # Prepare active projects data
                df_active["TaskDensity"] = df_active["TotalTasks"] / df_active[
                    "ProjectAgeInDays"
                ].replace(0, 1)
                df_active["BudgetPerTask"] = df_active["Budget"] / df_active[
                    "TotalTasks"
                ].replace(0, 1)
                df_active["PriorityScore"] = (
                    df_active["Priority"].map(priority_mapping).fillna(2)
                )

                # Fill missing AvgTaskHours with median
                df_active["AvgTaskHours"] = df_active["AvgTaskHours"].fillna(
                    df_clean["AvgTaskHours"].median()
                )

                X_active = df_active[feature_columns]
                X_active_scaled = scaler.transform(X_active)

                predicted_completion = model.predict(X_active_scaled)

                for i, row in df_active.iterrows():
                    current_completion = row["CompletionPercentage"]
                    predicted_final = max(predicted_completion[i], current_completion)

                    # Estimate remaining time based on current progress rate
                    if current_completion > 0 and row["ProjectAgeInDays"] > 0:
                        completion_rate_per_day = (
                            current_completion / row["ProjectAgeInDays"]
                        )
                        if completion_rate_per_day > 0:
                            remaining_completion = 100 - current_completion
                            estimated_days_remaining = (
                                remaining_completion / completion_rate_per_day
                            )
                        else:
                            estimated_days_remaining = None
                    else:
                        estimated_days_remaining = None

                    predictions.append(
                        {
                            "project_name": row["Name"],
                            "current_completion": current_completion,
                            "predicted_completion": predicted_final,
                            "estimated_days_remaining": estimated_days_remaining,
                            "risk_level": (
                                "High"
                                if predicted_final < 80
                                else "Medium" if predicted_final < 95 else "Low"
                            ),
                        }
                    )

            # Calculate model performance
            y_pred = model.predict(X_scaled)
            r2 = r2_score(y, y_pred)

            # Risk analysis
            risk_factors = self._analyze_risk_factors(df_clean)

            # Generate forecasts
            forecasts = self._generate_forecasts(df_clean)

            summary = {
                "model_accuracy": r2,
                "total_predictions": len(predictions),
                "high_risk_projects": len(
                    [p for p in predictions if p["risk_level"] == "High"]
                ),
                "avg_predicted_completion": (
                    np.mean([p["predicted_completion"] for p in predictions])
                    if predictions
                    else 0
                ),
                "completion_forecast_next_30_days": forecasts.get(
                    "completion_forecast", 0
                ),
                "budget_forecast_next_30_days": forecasts.get("budget_forecast", 0),
            }

            # Generate charts
            charts = {}

            # Prediction accuracy
            charts["prediction_accuracy"] = {
                "type": "scatter",
                "data": {
                    "x": y.tolist(),
                    "y": y_pred.tolist(),
                    "title": f"ความแม่นยำของแบบจำลอง (R² = {r2:.3f})",
                },
            }

            # Risk distribution
            if predictions:
                risk_counts = {}
                for pred in predictions:
                    risk_level = pred["risk_level"]
                    risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

                charts["risk_distribution"] = {
                    "type": "pie",
                    "data": {
                        "labels": list(risk_counts.keys()),
                        "values": list(risk_counts.values()),
                    },
                    "title": "การกระจายระดับความเสี่ยง",
                }

            # Feature importance
            feature_importance = np.abs(model.coef_)
            charts["feature_importance"] = {
                "type": "bar",
                "data": {"x": feature_columns, "y": feature_importance.tolist()},
                "title": "ความสำคัญของปัจจัยต่างๆ",
            }

            return {
                "summary": summary,
                "charts": charts,
                "predictions": predictions,
                "risk_factors": risk_factors,
                "forecasts": forecasts,
                "raw_data": {
                    "historical_data": historical_data,
                    "active_projects": active_data,
                },
            }

        except Exception as e:
            logger.error(f"Error generating predictive analysis report: {e}")
            return {"error": str(e)}

    def _analyze_risk_factors(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze risk factors from historical data"""
        try:
            risk_factors = []

            # Budget overrun risk
            budget_overruns = df[df["ActualCost"] > df["Budget"]]
            if len(budget_overruns) > 0:
                overrun_rate = len(budget_overruns) / len(df) * 100
                risk_factors.append(
                    {
                        "factor": "Budget Overrun",
                        "risk_level": (
                            "High"
                            if overrun_rate > 30
                            else "Medium" if overrun_rate > 15 else "Low"
                        ),
                        "probability": overrun_rate,
                        "description": f"{overrun_rate:.1f}% ของโครงการมีค่าใช้จ่ายเกินงบประมาณ",
                    }
                )

            # Schedule delay risk
            schedule_delays = df[
                df["ProjectAgeInDays"] > df["PlannedDurationInDays"]
            ].dropna()
            if len(schedule_delays) > 0:
                delay_rate = (
                    len(schedule_delays)
                    / len(df.dropna(subset=["PlannedDurationInDays"]))
                    * 100
                )
                risk_factors.append(
                    {
                        "factor": "Schedule Delay",
                        "risk_level": (
                            "High"
                            if delay_rate > 40
                            else "Medium" if delay_rate > 20 else "Low"
                        ),
                        "probability": delay_rate,
                        "description": f"{delay_rate:.1f}% ของโครงการมีความล่าช้าจากแผน",
                    }
                )

            # Low completion rate risk
            low_completion = df[df["CompletionPercentage"] < 50]
            if len(low_completion) > 0:
                low_completion_rate = len(low_completion) / len(df) * 100
                risk_factors.append(
                    {
                        "factor": "Low Completion Rate",
                        "risk_level": (
                            "High"
                            if low_completion_rate > 25
                            else "Medium" if low_completion_rate > 15 else "Low"
                        ),
                        "probability": low_completion_rate,
                        "description": f"{low_completion_rate:.1f}% ของโครงการมีความคืบหน้าต่ำกว่า 50%",
                    }
                )

            return risk_factors

        except Exception as e:
            logger.error(f"Error analyzing risk factors: {e}")
            return []

    def _generate_forecasts(self, df: pd.DataFrame) -> Dict[str, float]:
        """Generate forecasts for next period"""
        try:
            forecasts = {}

            # Completion rate forecast
            if len(df) >= 3:
                recent_completions = df.nlargest(5, "ProjectAgeInDays")[
                    "CompletionPercentage"
                ]
                forecasts["completion_forecast"] = recent_completions.mean()

            # Budget trend forecast
            if len(df) >= 3:
                budget_utilization = (df["ActualCost"] / df["Budget"]).dropna()
                forecasts["budget_forecast"] = budget_utilization.mean() * 100

            return forecasts

        except Exception as e:
            logger.error(f"Error generating forecasts: {e}")
            return {}

    def _generate_insights(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate insights from report data"""
        insights = []

        try:
            summary = report_data.get("summary", {})

            # Budget insights
            if "budget_variance" in summary:
                variance = summary["budget_variance"]
                if variance > 10:
                    insights.append(
                        f"🔴 งบประมาณเกินแผน {variance:.1f}% - ต้องการการควบคุมค่าใช้จ่ายที่เข้มงวดขึ้น"
                    )
                elif variance < -10:
                    insights.append(
                        f"🟢 งบประมาณต่ำกว่าแผน {abs(variance):.1f}% - มีประสิทธิภาพในการควบคุมค่าใช้จ่าย"
                    )

            # Completion rate insights
            if "avg_completion_rate" in summary:
                completion_rate = summary["avg_completion_rate"]
                if completion_rate > 80:
                    insights.append(
                        f"🟢 อัตราความสำเร็จสูง ({completion_rate:.1f}%) - ทีมมีประสิทธิภาพดีเยี่ยม"
                    )
                elif completion_rate < 60:
                    insights.append(
                        f"🔴 อัตราความสำเร็จต่ำ ({completion_rate:.1f}%) - ต้องการการปรับปรุงกระบวนการ"
                    )

            # Team performance insights
            if "avg_productivity_score" in summary:
                productivity = summary["avg_productivity_score"]
                if productivity > 85:
                    insights.append(
                        f"🟢 ประสิทธิภาพทีมสูง ({productivity:.1f}) - ทีมทำงานได้ดีเยี่ยม"
                    )
                elif productivity < 70:
                    insights.append(
                        f"🔴 ประสิทธิภาพทีมต่ำ ({productivity:.1f}) - ต้องการการพัฒนาทักษะ"
                    )

            # Overdue tasks insights
            if "total_overdue_tasks" in summary and "total_tasks" in summary:
                if summary["total_tasks"] > 0:
                    overdue_rate = (
                        summary["total_overdue_tasks"] / summary["total_tasks"]
                    ) * 100
                    if overdue_rate > 15:
                        insights.append(
                            f"🔴 งานเลยกำหนดสูง ({overdue_rate:.1f}%) - ต้องการการจัดการเวลาที่ดีขึ้น"
                        )

            # Predictive insights
            if "high_risk_projects" in summary:
                high_risk = summary["high_risk_projects"]
                if high_risk > 0:
                    insights.append(
                        f"⚠️ มีโครงการเสี่ยงสูง {high_risk} โครงการ - ต้องการการติดตามใกล้ชิด"
                    )

        except Exception as e:
            logger.error(f"Error generating insights: {e}")

        return insights

    def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        try:
            summary = report_data.get("summary", {})
            insights = report_data.get("insights", [])

            # Budget recommendations
            if any("เกินแผน" in insight for insight in insights):
                recommendations.extend(
                    [
                        "💰 ทบทวนกระบวนการควบคุมงบประมาณและการอนุมัติค่าใช้จ่าย",
                        "📊 ติดตั้งระบบการแจ้งเตือนเมื่อค่าใช้จ่ายใกล้เกินงบประมาณ",
                        "🔍 วิเคราะห์สาเหตุการใช้จ่ายเกินในโครงการที่ผ่านมา",
                    ]
                )

            # Performance recommendations
            if any("ประสิทธิภาพต่ำ" in insight for insight in insights):
                recommendations.extend(
                    [
                        "📚 จัดอบรมเพิ่มทักษะให้ทีมในด้านที่จำเป็น",
                        "⚡ ปรับปรุงเครื่องมือและกระบวนการทำงาน",
                        "👥 พิจารณาการกระจายภาระงานใหม่",
                    ]
                )

            # Timeline recommendations
            if any("เลยกำหนด" in insight for insight in insights):
                recommendations.extend(
                    [
                        "📅 ปรับปรุงการประมาณเวลาและการวางแผนโครงการ",
                        "🚨 ตั้งระบบการแจ้งเตือนก่อนครบกำหนด",
                        "🔄 ทบทวนขั้นตอนการทำงานเพื่อเพิ่มประสิทธิภาพ",
                    ]
                )

            # Quality recommendations
            if "quality_score" in summary and summary["quality_score"] < 80:
                recommendations.extend(
                    [
                        "✅ เพิ่มขั้นตอนการตรวจสอบคุณภาพ",
                        "📝 ปรับปรุงเอกสารและมาตรฐานการทำงาน",
                        "🔧 ลงทุนในเครื่องมือช่วยตรวจสอบคุณภาพ",
                    ]
                )

            # Risk management recommendations
            if "high_risk_projects" in summary and summary["high_risk_projects"] > 0:
                recommendations.extend(
                    [
                        "⚠️ จัดทำแผนการจัดการความเสี่ยงสำหรับโครงการเสี่ยงสูง",
                        "👁️ เพิ่มความถี่ในการติดตามโครงการเสี่ยง",
                        "🛡️ ปรับแผนสำรองสำหรับโครงการที่มีปัญหา",
                    ]
                )

            # General recommendations
            if len(recommendations) == 0:
                recommendations.extend(
                    [
                        "✅ ประสิทธิภาพการทำงานอยู่ในเกณฑ์ดี ควรรักษามาตรฐานไว้",
                        "📈 พิจารณาการขยายขนาดทีมหรือโครงการ",
                        "🎯 ตั้งเป้าหมายที่ท้าทายขึ้นสำหรับการปรับปรุงต่อไป",
                    ]
                )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")

        return recommendations

    def generate_executive_dashboard(
        self, date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Generate executive-level dashboard with KPIs"""
        try:
            config = ReportConfig(
                report_type=ReportType.EXECUTIVE_DASHBOARD,
                date_range=date_range,
                filters={},
                visualization_type="dashboard",
                export_format="html",
            )

            # Collect data from multiple report types
            project_data = self._generate_project_summary_report(config)
            team_data = self._generate_team_performance_report(config)
            budget_data = self._generate_budget_analysis_report(config)

            # Executive KPIs
            executive_kpis = {
                "financial_health": {
                    "total_budget": budget_data.get("summary", {}).get(
                        "total_budget", 0
                    ),
                    "budget_variance": budget_data.get("summary", {}).get(
                        "total_variance", 0
                    ),
                    "cost_efficiency": budget_data.get("summary", {}).get(
                        "avg_cost_performance_index", 0
                    ),
                    "roi": budget_data.get("summary", {}).get("avg_roi", 0),
                },
                "operational_health": {
                    "project_completion_rate": project_data.get("summary", {}).get(
                        "avg_completion_rate", 0
                    ),
                    "on_time_delivery": 100
                    - (
                        project_data.get("summary", {}).get("total_overdue_tasks", 0)
                        / max(project_data.get("summary", {}).get("total_tasks", 1), 1)
                        * 100
                    ),
                    "team_productivity": team_data.get("summary", {}).get(
                        "avg_productivity_score", 0
                    ),
                    "active_projects": project_data.get("summary", {}).get(
                        "active_projects", 0
                    ),
                },
                "strategic_health": {
                    "portfolio_growth": self._calculate_portfolio_growth(date_range),
                    "innovation_index": self._calculate_innovation_index(date_range),
                    "client_satisfaction": self._calculate_client_satisfaction(
                        date_range
                    ),
                    "market_position": self._calculate_market_position(date_range),
                },
            }

            # Risk assessment
            risk_assessment = self._generate_executive_risk_assessment(date_range)

            # Strategic recommendations
            strategic_recommendations = self._generate_strategic_recommendations(
                executive_kpis, risk_assessment
            )

            return {
                "kpis": executive_kpis,
                "risk_assessment": risk_assessment,
                "strategic_recommendations": strategic_recommendations,
                "project_summary": project_data,
                "team_summary": team_data,
                "budget_summary": budget_data,
            }

        except Exception as e:
            logger.error(f"Error generating executive dashboard: {e}")
            return {"error": str(e)}

    def _calculate_portfolio_growth(self, date_range: Tuple[date, date]) -> float:
        """Calculate portfolio growth rate"""
        try:
            start_date, end_date = date_range
            prev_start = start_date - timedelta(days=(end_date - start_date).days)

            current_query = "SELECT COUNT(*) as count FROM Projects WHERE CreatedDate BETWEEN ? AND ?"
            previous_query = "SELECT COUNT(*) as count FROM Projects WHERE CreatedDate BETWEEN ? AND ?"

            current_count = self.db.execute_query(
                current_query, (start_date, end_date)
            )[0]["count"]
            previous_count = self.db.execute_query(
                previous_query, (prev_start, start_date)
            )[0]["count"]

            if previous_count > 0:
                return ((current_count - previous_count) / previous_count) * 100
            return 0

        except Exception as e:
            logger.error(f"Error calculating portfolio growth: {e}")
            return 0

    def _calculate_innovation_index(self, date_range: Tuple[date, date]) -> float:
        """Calculate innovation index based on project types and technologies"""
        try:
            # This is a simplified calculation - in reality, you'd have more sophisticated metrics
            start_date, end_date = date_range

            query = """
                SELECT COUNT(*) as innovative_projects
                FROM Projects
                WHERE CreatedDate BETWEEN ? AND ?
                AND (Name LIKE '%AI%' OR Name LIKE '%Machine Learning%' OR Name LIKE '%Innovation%' 
                     OR Name LIKE '%Digital%' OR Name LIKE '%Automation%')
            """

            total_query = "SELECT COUNT(*) as total FROM Projects WHERE CreatedDate BETWEEN ? AND ?"

            innovative_count = self.db.execute_query(query, (start_date, end_date))[0][
                "innovative_projects"
            ]
            total_count = self.db.execute_query(total_query, (start_date, end_date))[0][
                "total"
            ]

            if total_count > 0:
                return (innovative_count / total_count) * 100
            return 0

        except Exception as e:
            logger.error(f"Error calculating innovation index: {e}")
            return 0

    def _calculate_client_satisfaction(self, date_range: Tuple[date, date]) -> float:
        """Calculate client satisfaction score"""
        try:
            # Simplified calculation based on project completion and quality
            start_date, end_date = date_range

            query = """
                SELECT AVG(CAST(CompletionPercentage as FLOAT)) as avg_completion
                FROM Projects
                WHERE CreatedDate BETWEEN ? AND ?
                AND Status = 'Completed'
            """

            result = self.db.execute_query(query, (start_date, end_date))
            return (
                result[0]["avg_completion"]
                if result and result[0]["avg_completion"]
                else 75.0
            )

        except Exception as e:
            logger.error(f"Error calculating client satisfaction: {e}")
            return 75.0

    def _calculate_market_position(self, date_range: Tuple[date, date]) -> float:
        """Calculate market position score"""
        try:
            # Simplified calculation - in reality, you'd use external market data
            start_date, end_date = date_range

            # Base score on project diversity and success rate
            query = """
                SELECT 
                    COUNT(DISTINCT ClientName) as unique_clients,
                    AVG(CAST(CompletionPercentage as FLOAT)) as avg_completion,
                    COUNT(*) as total_projects
                FROM Projects
                WHERE CreatedDate BETWEEN ? AND ?
            """

            result = self.db.execute_query(query, (start_date, end_date))
            if result and result[0]["total_projects"] > 0:
                unique_clients = result[0]["unique_clients"] or 1
                avg_completion = result[0]["avg_completion"] or 0

                # Market position score based on client diversity and project success
                diversity_score = min(
                    unique_clients * 10, 50
                )  # Max 50 points for diversity
                success_score = (avg_completion / 100) * 50  # Max 50 points for success

                return diversity_score + success_score

            return 50.0  # Neutral position

        except Exception as e:
            logger.error(f"Error calculating market position: {e}")
            return 50.0

    def _generate_executive_risk_assessment(
        self, date_range: Tuple[date, date]
    ) -> Dict[str, Any]:
        """Generate executive-level risk assessment"""
        try:
            start_date, end_date = date_range

            # Financial risks
            budget_query = """
                SELECT 
                    COUNT(*) as total_projects,
                    SUM(CASE WHEN ActualCost > Budget THEN 1 ELSE 0 END) as over_budget_projects,
                    AVG(CASE WHEN Budget > 0 THEN (ActualCost - Budget) / Budget * 100 ELSE 0 END) as avg_variance
                FROM Projects
                WHERE CreatedDate BETWEEN ? AND ?
                AND Budget > 0
            """

            budget_result = self.db.execute_query(budget_query, (start_date, end_date))

            # Operational risks
            timeline_query = """
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN DueDate < GETDATE() AND Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks
                FROM Tasks t
                JOIN Projects p ON t.ProjectID = p.ProjectID
                WHERE p.CreatedDate BETWEEN ? AND ?
            """

            timeline_result = self.db.execute_query(
                timeline_query, (start_date, end_date)
            )

            # Calculate risk scores
            financial_risk = "Low"
            operational_risk = "Low"

            if budget_result and budget_result[0]["total_projects"] > 0:
                over_budget_rate = (
                    budget_result[0]["over_budget_projects"]
                    / budget_result[0]["total_projects"]
                ) * 100
                if over_budget_rate > 30:
                    financial_risk = "High"
                elif over_budget_rate > 15:
                    financial_risk = "Medium"

            if timeline_result and timeline_result[0]["total_tasks"] > 0:
                overdue_rate = (
                    timeline_result[0]["overdue_tasks"]
                    / timeline_result[0]["total_tasks"]
                ) * 100
                if overdue_rate > 20:
                    operational_risk = "High"
                elif overdue_rate > 10:
                    operational_risk = "Medium"

            return {
                "financial_risk": financial_risk,
                "operational_risk": operational_risk,
                "strategic_risk": "Medium",  # Would be calculated based on market conditions
                "overall_risk_score": self._calculate_overall_risk_score(
                    financial_risk, operational_risk
                ),
            }

        except Exception as e:
            logger.error(f"Error generating executive risk assessment: {e}")
            return {"error": str(e)}

    def _calculate_overall_risk_score(
        self, financial_risk: str, operational_risk: str
    ) -> int:
        """Calculate overall risk score from 1-100"""
        risk_scores = {"Low": 20, "Medium": 50, "High": 80}

        financial_score = risk_scores.get(financial_risk, 50)
        operational_score = risk_scores.get(operational_risk, 50)

        return int((financial_score + operational_score) / 2)

    def _generate_strategic_recommendations(
        self, kpis: Dict, risk_assessment: Dict
    ) -> List[str]:
        """Generate strategic recommendations for executives"""
        recommendations = []

        try:
            financial_health = kpis.get("financial_health", {})
            operational_health = kpis.get("operational_health", {})
            strategic_health = kpis.get("strategic_health", {})

            # Financial recommendations
            if (
                financial_health.get("budget_variance", 0) < -100000
            ):  # Significant under-budget
                recommendations.append("💼 พิจารณาการลงทุนเพิ่มเติมในโครงการใหม่หรือการขยายทีม")
            elif financial_health.get("cost_efficiency", 1) < 0.8:
                recommendations.append("💰 ปรับปรุงประสิทธิภาพการใช้งบประมาณและควบคุมค่าใช้จ่าย")

            # Operational recommendations
            if operational_health.get("team_productivity", 0) > 90:
                recommendations.append(
                    "🚀 ทีมมีประสิทธิภาพสูง - พิจารณาขยายขนาดโครงการหรือรับงานใหม่"
                )
            elif operational_health.get("on_time_delivery", 0) < 80:
                recommendations.append("⏰ ปรับปรุงกระบวนการจัดการเวลาและการวางแผนโครงการ")

            # Strategic recommendations
            if strategic_health.get("innovation_index", 0) < 30:
                recommendations.append("🧬 เพิ่มการลงทุนในโครงการนวัตกรรมและเทคโนโลยีใหม่")

            if strategic_health.get("portfolio_growth", 0) < 10:
                recommendations.append("📈 พัฒนากลยุทธ์การเติบโตและขยายตลาด")

            # Risk-based recommendations
            if risk_assessment.get("overall_risk_score", 50) > 70:
                recommendations.append("⚠️ จัดทำแผนจัดการความเสี่ยงเชิงรุกและเพิ่มการติดตาม")

        except Exception as e:
            logger.error(f"Error generating strategic recommendations: {e}")

        return recommendations

    def export_report(
        self, report_data: Dict[str, Any], format_type: str = "pdf"
    ) -> str:
        """Export report to various formats"""
        try:
            if format_type.lower() == "pdf":
                return self._export_to_pdf(report_data)
            elif format_type.lower() == "excel":
                return self._export_to_excel(report_data)
            elif format_type.lower() == "json":
                return self._export_to_json(report_data)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return None

    def _export_to_pdf(self, report_data: Dict[str, Any]) -> str:
        """Export report to PDF format"""
        # Implementation would use libraries like reportlab or weasyprint
        # This is a simplified version
        try:
            import json

            # Create a simple HTML version that can be converted to PDF
            html_content = self._generate_html_report(report_data)

            # In a real implementation, you'd use a PDF generation library
            # For now, return the HTML content
            return html_content

        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            return None

    def _export_to_excel(self, report_data: Dict[str, Any]) -> str:
        """Export report to Excel format"""
        try:
            import io
            import base64

            # Create Excel file in memory
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Summary sheet
                if "summary" in report_data:
                    summary_df = pd.DataFrame([report_data["summary"]])
                    summary_df.to_excel(writer, sheet_name="Summary", index=False)

                # Raw data sheets
                if "raw_data" in report_data:
                    for sheet_name, data in report_data["raw_data"].items():
                        if data:
                            df = pd.DataFrame(data)
                            df.to_excel(
                                writer, sheet_name=sheet_name[:31], index=False
                            )  # Excel sheet name limit

            # Get the Excel content as base64
            output.seek(0)
            excel_content = base64.b64encode(output.read()).decode()

            return excel_content

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return None

    def _export_to_json(self, report_data: Dict[str, Any]) -> str:
        """Export report to JSON format"""
        try:
            import json
            from datetime import datetime, date

            def json_serializer(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            return json.dumps(
                report_data, default=json_serializer, indent=2, ensure_ascii=False
            )

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return None

    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML report"""
        try:
            metadata = report_data.get("metadata", {})
            summary = report_data.get("summary", {})
            insights = report_data.get("insights", [])
            recommendations = report_data.get("recommendations", [])

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>DENSO Project Manager Pro - Analytics Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    .header {{ background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; text-align: center; border-radius: 8px; }}
                    .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                    .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
                    .insight {{ background: #e3f2fd; padding: 10px; margin: 5px 0; border-left: 4px solid #2196f3; }}
                    .recommendation {{ background: #f3e5f5; padding: 10px; margin: 5px 0; border-left: 4px solid #9c27b0; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🚗 DENSO Project Manager Pro</h1>
                    <h2>รายงานการวิเคราะห์ข้อมูล</h2>
                    <p>สร้างเมื่อ: {metadata.get('generated_at', datetime.now()).strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                
                <div class="section">
                    <h3>📊 สรุปผลการดำเนินงาน</h3>
                    {''.join([f'<div class="metric"><strong>{k}:</strong> {v}</div>' for k, v in summary.items()])}
                </div>
                
                <div class="section">
                    <h3>💡 ข้อมูลเชิงลึก</h3>
                    {''.join([f'<div class="insight">{insight}</div>' for insight in insights])}
                </div>
                
                <div class="section">
                    <h3>🎯 ข้อเสนอแนะ</h3>
                    {''.join([f'<div class="recommendation">{rec}</div>' for rec in recommendations])}
                </div>
                
                <div class="section">
                    <h3>📈 สถิติรายละเอียด</h3>
                    <p>รายงานนี้สร้างขึ้นจากข้อมูลในระบบ DENSO Project Manager Pro</p>
                    <p>สำหรับข้อมูลเพิ่มเติม กรุณาติดต่อทีม Innovation Team</p>
                </div>
                
                <footer style="margin-top: 50px; text-align: center; color: #666;">
                    <p>© 2024 DENSO Corporation. All rights reserved.</p>
                </footer>
            </body>
            </html>
            """

            return html_content

        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return "<html><body><h1>Error generating report</h1></body></html>"


# UI Functions for Advanced Analytics
def show_analytics_page(analytics_manager: AdvancedAnalyticsEngine):
    """Show advanced analytics page"""
    ui = UIComponents()

    # Page header
    ui.render_page_header(
        "📈 Advanced Analytics & Reports", "การวิเคราะห์ข้อมูลขั้นสูงและการสร้างรายงาน", "📈"
    )

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Executive Dashboard",
            "📋 Standard Reports",
            "🔮 Predictive Analytics",
            "📈 Custom Analysis",
            "📤 Export & Sharing",
        ]
    )

    with tab1:
        show_executive_dashboard(analytics_manager)

    with tab2:
        show_standard_reports(analytics_manager)

    with tab3:
        show_predictive_analytics(analytics_manager)

    with tab4:
        show_custom_analysis(analytics_manager)

    with tab5:
        show_export_sharing(analytics_manager)


def show_executive_dashboard(analytics_manager: AdvancedAnalyticsEngine):
    """Show executive dashboard"""
    st.subheader("📊 Executive Dashboard")

    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        start_date = st.date_input("วันที่เริ่มต้น", value=date.today() - timedelta(days=90))

    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", value=date.today())

    with col3:
        if st.button("🔄 อัปเดต"):
            st.rerun()

    if start_date >= end_date:
        st.error("วันที่เริ่มต้นต้องน้อยกว่าวันที่สิ้นสุด")
        return

    # Generate executive dashboard
    with st.spinner("กำลังสร้าง Executive Dashboard..."):
        dashboard_data = safe_execute(
            analytics_manager.generate_executive_dashboard,
            (start_date, end_date),
            default_return={},
        )

    if "error" in dashboard_data:
        st.error(f"ไม่สามารถสร้าง Dashboard ได้: {dashboard_data['error']}")
        return

    # Display KPIs
    if "kpis" in dashboard_data:
        kpis = dashboard_data["kpis"]

        st.markdown("### 💼 Financial Health")
        col1, col2, col3, col4 = st.columns(4)

        financial = kpis.get("financial_health", {})
        with col1:
            st.metric("งบประมาณรวม", f"{financial.get('total_budget', 0):,.0f} บาท")
        with col2:
            variance = financial.get("budget_variance", 0)
            st.metric(
                "ส่วนต่างงบประมาณ",
                f"{variance:,.0f} บาท",
                delta=f"{variance:+,.0f}" if variance != 0 else None,
            )
        with col3:
            st.metric("ประสิทธิภาพค่าใช้จ่าย", f"{financial.get('cost_efficiency', 0):.2f}")
        with col4:
            st.metric("ROI เฉลี่ย", f"{financial.get('roi', 0):.1f}%")

        st.markdown("### ⚙️ Operational Health")
        col1, col2, col3, col4 = st.columns(4)

        operational = kpis.get("operational_health", {})
        with col1:
            completion = operational.get("project_completion_rate", 0)
            st.metric(
                "อัตราความสำเร็จ",
                f"{completion:.1f}%",
                delta=f"{completion-80:+.1f}%" if completion != 80 else None,
            )
        with col2:
            on_time = operational.get("on_time_delivery", 0)
            st.metric(
                "การส่งมอบตรงเวลา",
                f"{on_time:.1f}%",
                delta=f"{on_time-90:+.1f}%" if on_time != 90 else None,
            )
        with col3:
            productivity = operational.get("team_productivity", 0)
            st.metric("ประสิทธิภาพทีม", f"{productivity:.1f}")
        with col4:
            st.metric("โครงการที่ดำเนินการ", operational.get("active_projects", 0))

        st.markdown("### 🎯 Strategic Health")
        col1, col2, col3, col4 = st.columns(4)

        strategic = kpis.get("strategic_health", {})
        with col1:
            growth = strategic.get("portfolio_growth", 0)
            st.metric("การเติบโตพอร์ตโฟลิโอ", f"{growth:+.1f}%")
        with col2:
            innovation = strategic.get("innovation_index", 0)
            st.metric("Innovation Index", f"{innovation:.1f}%")
        with col3:
            satisfaction = strategic.get("client_satisfaction", 0)
            st.metric("ความพึงพอใจลูกค้า", f"{satisfaction:.1f}%")
        with col4:
            market_pos = strategic.get("market_position", 0)
            st.metric("ตำแหน่งตลาด", f"{market_pos:.1f}")

    # Risk Assessment
    if "risk_assessment" in dashboard_data:
        st.markdown("### ⚠️ Risk Assessment")
        risk_data = dashboard_data["risk_assessment"]

        col1, col2, col3, col4 = st.columns(4)

        def get_risk_color(risk_level):
            colors = {"Low": "green", "Medium": "orange", "High": "red"}
            return colors.get(risk_level, "gray")

        with col1:
            financial_risk = risk_data.get("financial_risk", "Unknown")
            st.markdown(
                f"**Financial Risk:** <span style='color: {get_risk_color(financial_risk)}'>{financial_risk}</span>",
                unsafe_allow_html=True,
            )

        with col2:
            operational_risk = risk_data.get("operational_risk", "Unknown")
            st.markdown(
                f"**Operational Risk:** <span style='color: {get_risk_color(operational_risk)}'>{operational_risk}</span>",
                unsafe_allow_html=True,
            )

        with col3:
            strategic_risk = risk_data.get("strategic_risk", "Unknown")
            st.markdown(
                f"**Strategic Risk:** <span style='color: {get_risk_color(strategic_risk)}'>{strategic_risk}</span>",
                unsafe_allow_html=True,
            )

        with col4:
            overall_score = risk_data.get("overall_risk_score", 50)
            risk_level = (
                "Low"
                if overall_score < 30
                else "Medium" if overall_score < 70 else "High"
            )
            st.metric(
                "Overall Risk Score",
                f"{overall_score}/100",
                delta=f"Risk Level: {risk_level}",
            )

    # Strategic Recommendations
    if "strategic_recommendations" in dashboard_data:
        st.markdown("### 🎯 Strategic Recommendations")
        recommendations = dashboard_data["strategic_recommendations"]

        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")


def show_standard_reports(analytics_manager: AdvancedAnalyticsEngine):
    """Show standard reports"""
    st.subheader("📋 Standard Reports")

    # Report configuration
    col1, col2 = st.columns([2, 1])

    with col1:
        report_type = st.selectbox(
            "เลือกประเภทรายงาน",
            options=[
                ReportType.PROJECT_SUMMARY,
                ReportType.TEAM_PERFORMANCE,
                ReportType.BUDGET_ANALYSIS,
                ReportType.TIMELINE_ANALYSIS,
                ReportType.QUALITY_METRICS,
                ReportType.RESOURCE_UTILIZATION,
            ],
            format_func=lambda x: analytics_manager.report_templates[x]["title"],
        )

    with col2:
        visualization_type = st.selectbox(
            "รูปแบบการแสดงผล",
            options=["charts", "tables", "mixed"],
            format_func=lambda x: {"charts": "กราฟ", "tables": "ตาราง", "mixed": "ผสม"}[
                x
            ],
        )

    # Date range and filters
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("วันที่เริ่มต้น", value=date.today() - timedelta(days=30))

    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", value=date.today())

    # Advanced filters
    with st.expander("🔍 ตัวกรองขั้นสูง"):
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.multiselect(
                "สถานะโครงการ",
                options=[
                    "Planning",
                    "In Progress",
                    "On Hold",
                    "Completed",
                    "Cancelled",
                ],
                default=["Planning", "In Progress", "Completed"],
            )

        with col2:
            priority_filter = st.multiselect(
                "ความสำคัญ",
                options=["Low", "Medium", "High", "Critical"],
                default=["Low", "Medium", "High", "Critical"],
            )

        with col3:
            budget_range = st.slider(
                "ช่วงงบประมาณ (ล้านบาท)",
                min_value=0.0,
                max_value=50.0,
                value=(0.0, 50.0),
                step=0.5,
            )

    # Generate report button
    if st.button("📊 สร้างรายงาน", type="primary"):
        config = ReportConfig(
            report_type=report_type,
            date_range=(start_date, end_date),
            filters={
                "status": status_filter,
                "priority": priority_filter,
                "budget_min": budget_range[0] * 1000000,
                "budget_max": budget_range[1] * 1000000,
            },
            visualization_type=visualization_type,
            export_format="html",
        )

        with st.spinner("กำลังสร้างรายงาน..."):
            report_data = safe_execute(
                analytics_manager.generate_comprehensive_report,
                config,
                default_return={},
            )

        if "error" in report_data:
            st.error(f"ไม่สามารถสร้างรายงานได้: {report_data['error']}")
            return

        # Display report results
        display_report_results(report_data, visualization_type)


def show_predictive_analytics(analytics_manager: AdvancedAnalyticsEngine):
    """Show predictive analytics"""
    st.subheader("🔮 Predictive Analytics")

    st.info("🤖 ระบบการวิเคราะห์เชิงพยากรณ์ใช้ Machine Learning เพื่อคาดการณ์แนวโน้มและความเสี่ยง")

    # Configuration
    col1, col2 = st.columns(2)

    with col1:
        prediction_type = st.selectbox(
            "ประเภทการพยากรณ์",
            options=[
                "project_completion",
                "budget_forecast",
                "risk_assessment",
                "resource_planning",
            ],
            format_func=lambda x: {
                "project_completion": "พยากรณ์ความสำเร็จโครงการ",
                "budget_forecast": "พยากรณ์งบประมาณ",
                "risk_assessment": "ประเมินความเสี่ยง",
                "resource_planning": "วางแผนทรัพยากร",
            }[x],
        )

    with col2:
        forecast_period = st.selectbox(
            "ช่วงเวลาพยากรณ์", options=[30, 60, 90, 180], format_func=lambda x: f"{x} วัน"
        )

    # Date range for historical data
    st.markdown("### 📅 ข้อมูลย้อนหลังสำหรับการเรียนรู้")
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("เริ่มจาก", value=date.today() - timedelta(days=365))

    with col2:
        end_date = st.date_input("ถึง", value=date.today())

    if st.button("🔮 สร้างการพยากรณ์", type="primary"):
        config = ReportConfig(
            report_type=ReportType.PREDICTIVE_ANALYSIS,
            date_range=(start_date, end_date),
            filters={
                "forecast_period": forecast_period,
                "prediction_type": prediction_type,
            },
            visualization_type="charts",
            export_format="html",
        )

        with st.spinner("กำลังวิเคราะห์และสร้างการพยากรณ์..."):
            report_data = safe_execute(
                analytics_manager.generate_comprehensive_report,
                config,
                default_return={},
            )

        if "error" in report_data:
            st.error(f"ไม่สามารถสร้างการพยากรณ์ได้: {report_data['error']}")
            return

        # Display predictions
        if "predictions" in report_data:
            st.markdown("### 📈 ผลการพยากรณ์")

            predictions = report_data["predictions"]
            if predictions:
                df_pred = pd.DataFrame(predictions)

                # Summary metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    avg_predicted = df_pred["predicted_completion"].mean()
                    st.metric("ความสำเร็จเฉลี่ยที่คาดการณ์", f"{avg_predicted:.1f}%")

                with col2:
                    high_risk_count = len(df_pred[df_pred["risk_level"] == "High"])
                    st.metric("โครงการเสี่ยงสูง", high_risk_count)

                with col3:
                    avg_remaining = df_pred["estimated_days_remaining"].dropna().mean()
                    if not pd.isna(avg_remaining):
                        st.metric("เวลาเหลือเฉลี่ย", f"{avg_remaining:.0f} วัน")

                # Detailed predictions table
                st.markdown("### 📋 รายละเอียดการพยากรณ์")

                # Format the dataframe for display
                display_df = df_pred.copy()
                display_df["predicted_completion"] = display_df[
                    "predicted_completion"
                ].round(1)
                display_df["current_completion"] = display_df[
                    "current_completion"
                ].round(1)

                # Rename columns to Thai
                display_df = display_df.rename(
                    columns={
                        "project_name": "โครงการ",
                        "current_completion": "ความคืบหน้าปัจจุบัน (%)",
                        "predicted_completion": "ความสำเร็จที่คาดการณ์ (%)",
                        "estimated_days_remaining": "วันที่เหลือ (วัน)",
                        "risk_level": "ระดับความเสี่ยง",
                    }
                )

                st.dataframe(display_df, use_container_width=True)

        # Display risk factors
        if "risk_factors" in report_data:
            st.markdown("### ⚠️ ปัจจัยความเสี่ยง")

            risk_factors = report_data["risk_factors"]
            for risk in risk_factors:
                risk_color = {"Low": "green", "Medium": "orange", "High": "red"}.get(
                    risk["risk_level"], "gray"
                )

                st.markdown(
                    f"""
                **{risk['factor']}** - <span style='color: {risk_color}'>{risk['risk_level']} Risk</span>  
                📊 ความน่าจะเป็น: {risk['probability']:.1f}%  
                📝 {risk['description']}
                """,
                    unsafe_allow_html=True,
                )

        # Model performance
        if "summary" in report_data and "model_accuracy" in report_data["summary"]:
            accuracy = report_data["summary"]["model_accuracy"]
            st.markdown(f"### 🎯 ประสิทธิภาพของแบบจำลอง")
            st.metric("ความแม่นยำ (R²)", f"{accuracy:.3f}")

            if accuracy > 0.8:
                st.success("🎉 แบบจำลองมีความแม่นยำสูง")
            elif accuracy > 0.6:
                st.warning("⚠️ แบบจำลองมีความแม่นยำปานกลาง")
            else:
                st.error("❌ แบบจำลองมีความแม่นยำต่ำ - ต้องการข้อมูลเพิ่มเติม")


def show_custom_analysis(analytics_manager: AdvancedAnalyticsEngine):
    """Show custom analysis tools"""
    st.subheader("📈 Custom Analysis")

    st.info("🔧 เครื่องมือวิเคราะห์แบบกำหนดเองสำหรับการวิเคราะห์เฉพาะทาง")

    analysis_type = st.selectbox(
        "เลือกประเภทการวิเคราะห์",
        options=[
            "correlation_analysis",
            "trend_analysis",
            "comparative_analysis",
            "clustering_analysis",
        ],
        format_func=lambda x: {
            "correlation_analysis": "การวิเคราะห์ความสัมพันธ์",
            "trend_analysis": "การวิเคราะห์แนวโน้ม",
            "comparative_analysis": "การวิเคราะห์เปรียบเทียบ",
            "clustering_analysis": "การวิเคราะห์การจัดกลุ่ม",
        }[x],
    )

    if analysis_type == "correlation_analysis":
        show_correlation_analysis(analytics_manager)
    elif analysis_type == "trend_analysis":
        show_trend_analysis(analytics_manager)
    elif analysis_type == "comparative_analysis":
        show_comparative_analysis(analytics_manager)
    elif analysis_type == "clustering_analysis":
        show_clustering_analysis(analytics_manager)


def show_correlation_analysis(analytics_manager: AdvancedAnalyticsEngine):
    """Show correlation analysis"""
    st.markdown("### 🔗 การวิเคราะห์ความสัมพันธ์")

    # Variable selection
    col1, col2 = st.columns(2)

    variables = [
        "budget",
        "completion_percentage",
        "team_size",
        "project_duration",
        "task_count",
        "priority_score",
    ]

    with col1:
        x_variable = st.selectbox(
            "ตัวแปร X",
            options=variables,
            format_func=lambda x: {
                "budget": "งบประมาณ",
                "completion_percentage": "ความคืบหน้า",
                "team_size": "ขนาดทีม",
                "project_duration": "ระยะเวลาโครงการ",
                "task_count": "จำนวนงาน",
                "priority_score": "คะแนนความสำคัญ",
            }[x],
        )

    with col2:
        y_variable = st.selectbox(
            "ตัวแปร Y",
            options=variables,
            format_func=lambda x: {
                "budget": "งบประมาณ",
                "completion_percentage": "ความคืบหน้า",
                "team_size": "ขนาดทีม",
                "project_duration": "ระยะเวลาโครงการ",
                "task_count": "จำนวนงาน",
                "priority_score": "คะแนนความสำคัญ",
            }[x],
        )

    if st.button("📊 วิเคราะห์ความสัมพันธ์"):
        # This would be implemented with actual data analysis
        st.info("การวิเคราะห์ความสัมพันธ์จะถูกพัฒนาในเวอร์ชันถัดไป")


def show_export_sharing(analytics_manager: AdvancedAnalyticsEngine):
    """Show export and sharing options"""
    st.subheader("📤 Export & Sharing")

    st.markdown("### 📁 รูปแบบการส่งออก")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export to PDF"):
            st.info("การส่งออก PDF จะถูกพัฒนาในเวอร์ชันถัดไป")

    with col2:
        if st.button("📊 Export to Excel"):
            st.info("การส่งออก Excel จะถูกพัฒนาในเวอร์ชันถัดไป")

    with col3:
        if st.button("🔗 Generate Shareable Link"):
            st.info("การสร้างลิงก์แชร์จะถูกพัฒนาในเวอร์ชันถัดไป")

    st.markdown("### 📧 การแชร์อัตโนมัติ")

    with st.expander("ตั้งค่าการส่งรายงานอัตโนมัติ"):
        col1, col2 = st.columns(2)

        with col1:
            st.multiselect("ผู้รับ", options=["thammaphon.c@denso.com", "admin@denso.com"])
            st.selectbox("ความถี่", options=["รายวัน", "รายสัปดาห์", "รายเดือน"])

        with col2:
            st.selectbox("รูปแบบรายงาน", options=["สรุปผู้บริหาร", "รายละเอียดเต็ม"])
            st.time_input("เวลาส่ง", value=time(9, 0))


def display_report_results(report_data: Dict[str, Any], visualization_type: str):
    """Display report results"""
    if "summary" in report_data and report_data["summary"]:
        st.markdown("### 📊 สรุปผลลัพธ์")

        summary = report_data["summary"]
        if isinstance(summary, dict):
            # Display metrics in columns
            cols = st.columns(min(len(summary), 4))
            for i, (key, value) in enumerate(summary.items()):
                if i < len(cols):
                    with cols[i % len(cols)]:
                        if isinstance(value, (int, float)):
                            if "percentage" in key.lower() or "rate" in key.lower():
                                st.metric(
                                    key.replace("_", " ").title(), f"{value:.1f}%"
                                )
                            elif "budget" in key.lower() or "cost" in key.lower():
                                st.metric(
                                    key.replace("_", " ").title(), f"{value:,.0f} บาท"
                                )
                            else:
                                st.metric(
                                    key.replace("_", " ").title(), f"{value:,.0f}"
                                )
                        else:
                            st.metric(key.replace("_", " ").title(), str(value))

    # Display insights
    if "insights" in report_data and report_data["insights"]:
        st.markdown("### 💡 ข้อมูลเชิงลึก")
        for insight in report_data["insights"]:
            st.info(insight)

    # Display recommendations
    if "recommendations" in report_data and report_data["recommendations"]:
        st.markdown("### 🎯 ข้อเสนอแนะ")
        for i, recommendation in enumerate(report_data["recommendations"], 1):
            st.markdown(f"{i}. {recommendation}")

    # Display charts (simplified for demo)
    if (
        "charts" in report_data
        and report_data["charts"]
        and visualization_type in ["charts", "mixed"]
    ):
        st.markdown("### 📈 กราฟและแผนภูมิ")

        charts = report_data["charts"]
        chart_cols = st.columns(min(len(charts), 2))

        for i, (chart_name, chart_data) in enumerate(charts.items()):
            with chart_cols[i % len(chart_cols)]:
                st.markdown(f"**{chart_data.get('title', chart_name)}**")

                if chart_data.get("type") == "pie" and "data" in chart_data:
                    data = chart_data["data"]
                    if "labels" in data and "values" in data:
                        fig = px.pie(values=data["values"], names=data["labels"])
                        st.plotly_chart(fig, use_container_width=True)

                elif chart_data.get("type") == "bar" and "data" in chart_data:
                    data = chart_data["data"]
                    if "x" in data and "y" in data:
                        fig = px.bar(x=data["x"], y=data["y"])
                        st.plotly_chart(fig, use_container_width=True)

                elif chart_data.get("type") == "scatter" and "data" in chart_data:
                    data = chart_data["data"]
                    if "x" in data and "y" in data:
                        fig = px.scatter(
                            x=data["x"],
                            y=data["y"],
                            text=data.get("text", None),
                            size=data.get("size", None),
                        )
                        st.plotly_chart(fig, use_container_width=True)


def show_trend_analysis(analytics_manager: AdvancedAnalyticsEngine):
    """Show trend analysis"""
    st.markdown("### 📈 การวิเคราะห์แนวโน้ม")
    st.info("การวิเคราะห์แนวโน้มจะถูกพัฒนาในเวอร์ชันถัดไป")


def show_comparative_analysis(analytics_manager: AdvancedAnalyticsEngine):
    """Show comparative analysis"""
    st.markdown("### 🔄 การวิเคราะห์เปรียบเทียบ")

    # Comparison type selection
    comparison_type = st.selectbox(
        "ประเภทการเปรียบเทียบ",
        options=[
            "period_comparison",
            "team_comparison",
            "project_comparison",
            "department_comparison",
        ],
        format_func=lambda x: {
            "period_comparison": "เปรียบเทียบช่วงเวลา",
            "team_comparison": "เปรียบเทียบทีม",
            "project_comparison": "เปรียบเทียบโครงการ",
            "department_comparison": "เปรียบเทียบแผนก",
        }[x],
    )

    if comparison_type == "period_comparison":
        st.markdown("#### 📅 เปรียบเทียบช่วงเวลา")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**ช่วงเวลาที่ 1**")
            period1_start = st.date_input(
                "เริ่มต้น", value=date.today() - timedelta(days=60), key="p1_start"
            )
            period1_end = st.date_input(
                "สิ้นสุด", value=date.today() - timedelta(days=30), key="p1_end"
            )

        with col2:
            st.markdown("**ช่วงเวลาที่ 2**")
            period2_start = st.date_input(
                "เริ่มต้น", value=date.today() - timedelta(days=30), key="p2_start"
            )
            period2_end = st.date_input("สิ้นสุด", value=date.today(), key="p2_end")

        metrics_to_compare = st.multiselect(
            "เลือกเมทริกที่ต้องการเปรียบเทียบ",
            options=[
                "completion_rate",
                "budget_utilization",
                "team_productivity",
                "on_time_delivery",
            ],
            default=["completion_rate", "budget_utilization"],
            format_func=lambda x: {
                "completion_rate": "อัตราความสำเร็จ",
                "budget_utilization": "การใช้งบประมาณ",
                "team_productivity": "ประสิทธิภาพทีม",
                "on_time_delivery": "การส่งมอบตรงเวลา",
            }[x],
        )

        if st.button("📊 เปรียบเทียบ"):
            with st.spinner("กำลังวิเคราะห์และเปรียบเทียบ..."):
                # This would contain actual comparison logic
                st.success("การเปรียบเทียบเสร็จสิ้น!")

                # Mock comparison results
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("อัตราความสำเร็จ", "75.2%", delta="5.2%")

                with col2:
                    st.metric("การใช้งบประมาณ", "92.1%", delta="-3.1%")

                with col3:
                    st.metric("ประสิทธิภาพทีม", "8.4", delta="0.7")

                # Trend chart
                st.markdown("### 📈 แนวโน้มการเปรียบเทียบ")

                # Mock data for demonstration
                dates = pd.date_range(start=period1_start, end=period2_end, freq="D")
                mock_data = pd.DataFrame(
                    {
                        "date": dates,
                        "completion_rate": np.random.normal(75, 5, len(dates)),
                        "budget_utilization": np.random.normal(90, 3, len(dates)),
                    }
                )

                fig = px.line(
                    mock_data,
                    x="date",
                    y=["completion_rate", "budget_utilization"],
                    title="การเปรียบเทียบเมทริกตามเวลา",
                )
                st.plotly_chart(fig, use_container_width=True)

    elif comparison_type == "team_comparison":
        st.markdown("#### 👥 เปรียบเทียบทีม")

        # Team selection
        teams_to_compare = st.multiselect(
            "เลือกทีมที่ต้องการเปรียบเทียบ",
            options=[
                "Innovation Team",
                "Development Team",
                "Quality Team",
                "DevOps Team",
            ],
            default=["Innovation Team", "Development Team"],
        )

        comparison_metrics = st.multiselect(
            "เลือกเมทริกการเปรียบเทียบ",
            options=[
                "productivity",
                "quality_score",
                "delivery_time",
                "task_completion",
            ],
            default=["productivity", "quality_score"],
            format_func=lambda x: {
                "productivity": "ประสิทธิภาพ",
                "quality_score": "คะแนนคุณภาพ",
                "delivery_time": "เวลาส่งมอบ",
                "task_completion": "การเสร็จสิ้นงาน",
            }[x],
        )

        if st.button("📊 เปรียบเทียบทีม"):
            st.info("การเปรียบเทียบทีมจะถูกพัฒนาในเวอร์ชันถัดไป")

    elif comparison_type == "project_comparison":
        st.markdown("#### 📁 เปรียบเทียบโครงการ")

        # Project selection interface
        col1, col2 = st.columns(2)

        with col1:
            project_categories = st.multiselect(
                "หมวดหมู่โครงการ",
                options=["Innovation", "Development", "Research", "Implementation"],
                default=["Innovation", "Development"],
            )

        with col2:
            comparison_period = st.selectbox(
                "ช่วงเวลาเปรียบเทียบ",
                options=["last_3_months", "last_6_months", "last_year", "custom"],
                format_func=lambda x: {
                    "last_3_months": "3 เดือนที่ผ่านมา",
                    "last_6_months": "6 เดือนที่ผ่านมา",
                    "last_year": "ปีที่ผ่านมา",
                    "custom": "กำหนดเอง",
                }[x],
            )

        if comparison_period == "custom":
            col1, col2 = st.columns(2)
            with col1:
                custom_start = st.date_input(
                    "วันที่เริ่มต้น", value=date.today() - timedelta(days=90)
                )
            with col2:
                custom_end = st.date_input("วันที่สิ้นสุด", value=date.today())

        if st.button("📊 เปรียบเทียบโครงการ"):
            st.info("การเปรียบเทียบโครงการจะถูกพัฒนาในเวอร์ชันถัดไป")

    else:  # department_comparison
        st.markdown("#### 🏢 เปรียบเทียบแผนก")

        departments = st.multiselect(
            "เลือกแผนกที่ต้องการเปรียบเทียบ",
            options=["Innovation", "Engineering", "Quality", "Operations", "IT"],
            default=["Innovation", "Engineering"],
        )

        department_metrics = st.multiselect(
            "เมทริกการเปรียบเทียบ",
            options=[
                "project_count",
                "completion_rate",
                "budget_efficiency",
                "resource_utilization",
            ],
            default=["project_count", "completion_rate"],
            format_func=lambda x: {
                "project_count": "จำนวนโครงการ",
                "completion_rate": "อัตราความสำเร็จ",
                "budget_efficiency": "ประสิทธิภาพงบประมาณ",
                "resource_utilization": "การใช้ทรัพยากร",
            }[x],
        )

        if st.button("📊 เปรียบเทียบแผนก"):
            st.info("การเปรียบเทียบแผนกจะถูกพัฒนาในเวอร์ชันถัดไป")


def show_clustering_analysis(analytics_manager: AdvancedAnalyticsEngine):
    """Show clustering analysis"""
    st.markdown("### 🎯 การวิเคราะห์การจัดกลุ่ม")

    st.info("🤖 ใช้ Machine Learning เพื่อจัดกลุ่มโครงการ/ทีม/งานตามลักษณะที่คล้ายกัน")

    # Clustering configuration
    col1, col2 = st.columns(2)

    with col1:
        clustering_target = st.selectbox(
            "เป้าหมายการจัดกลุ่ม",
            options=["projects", "teams", "tasks", "users"],
            format_func=lambda x: {
                "projects": "โครงการ",
                "teams": "ทีม",
                "tasks": "งาน",
                "users": "ผู้ใช้",
            }[x],
        )

    with col2:
        num_clusters = st.slider("จำนวนกลุ่มที่ต้องการ", min_value=2, max_value=10, value=3)

    # Feature selection for clustering
    st.markdown("#### 🔧 เลือกลักษณะสำหรับการจัดกลุ่ม")

    if clustering_target == "projects":
        features = st.multiselect(
            "ลักษณะโครงการ",
            options=[
                "budget",
                "duration",
                "team_size",
                "complexity",
                "priority",
                "completion_rate",
                "risk_level",
            ],
            default=["budget", "duration", "team_size"],
            format_func=lambda x: {
                "budget": "งบประมาณ",
                "duration": "ระยะเวลา",
                "team_size": "ขนาดทีม",
                "complexity": "ความซับซ้อน",
                "priority": "ความสำคัญ",
                "completion_rate": "อัตราความสำเร็จ",
                "risk_level": "ระดับความเสี่ยง",
            }[x],
        )

    elif clustering_target == "teams":
        features = st.multiselect(
            "ลักษณะทีม",
            options=[
                "productivity",
                "quality_score",
                "experience_level",
                "workload",
                "collaboration_score",
                "innovation_index",
            ],
            default=["productivity", "quality_score", "experience_level"],
            format_func=lambda x: {
                "productivity": "ประสิทธิภาพ",
                "quality_score": "คะแนนคุณภาพ",
                "experience_level": "ระดับประสบการณ์",
                "workload": "ปริมาณงาน",
                "collaboration_score": "คะแนนการทำงานร่วมกัน",
                "innovation_index": "ดัชนีนวัตกรรม",
            }[x],
        )

    elif clustering_target == "tasks":
        features = st.multiselect(
            "ลักษณะงาน",
            options=[
                "estimated_hours",
                "actual_hours",
                "complexity",
                "priority",
                "dependencies",
                "skill_requirements",
            ],
            default=["estimated_hours", "complexity", "priority"],
            format_func=lambda x: {
                "estimated_hours": "เวลาที่ประมาณ",
                "actual_hours": "เวลาจริง",
                "complexity": "ความซับซ้อน",
                "priority": "ความสำคัญ",
                "dependencies": "การพึ่งพาอาศัย",
                "skill_requirements": "ความต้องการทักษะ",
            }[x],
        )

    else:  # users
        features = st.multiselect(
            "ลักษณะผู้ใช้",
            options=[
                "experience",
                "productivity",
                "quality_score",
                "collaboration",
                "learning_ability",
                "leadership",
            ],
            default=["experience", "productivity", "quality_score"],
            format_func=lambda x: {
                "experience": "ประสบการณ์",
                "productivity": "ประสิทธิภาพ",
                "quality_score": "คะแนนคุณภาพ",
                "collaboration": "การทำงานร่วมกัน",
                "learning_ability": "ความสามารถในการเรียนรู้",
                "leadership": "ภาวะผู้นำ",
            }[x],
        )

    # Advanced clustering options
    with st.expander("⚙️ ตัวเลือกขั้นสูง"):
        algorithm = st.selectbox(
            "อัลกอริทึมการจัดกลุ่ม",
            options=["kmeans", "hierarchical", "dbscan"],
            format_func=lambda x: {
                "kmeans": "K-Means",
                "hierarchical": "Hierarchical Clustering",
                "dbscan": "DBSCAN",
            }[x],
        )

        standardize_features = st.checkbox("ปรับมาตรฐานข้อมูล", value=True)

        if algorithm == "dbscan":
            eps = st.slider(
                "Epsilon (ระยะห่าง)", min_value=0.1, max_value=2.0, value=0.5, step=0.1
            )
            min_samples = st.slider("ตัวอย่างขั้นต่ำ", min_value=2, max_value=20, value=5)

    # Run clustering analysis
    if st.button("🎯 เริ่มการวิเคราะห์การจัดกลุ่ม", type="primary"):
        if not features:
            st.error("กรุณาเลือกลักษณะสำหรับการจัดกลุ่มอย่างน้อย 1 รายการ")
            return

        with st.spinner("กำลังวิเคราะห์การจัดกลุ่ม..."):
            # Mock clustering results for demonstration
            time.sleep(2)  # Simulate processing time

            st.success("การวิเคราะห์การจัดกลุ่มเสร็จสิ้น!")

            # Mock results
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("จำนวนกลุ่ม", num_clusters)

            with col2:
                st.metric("Silhouette Score", "0.72")

            with col3:
                st.metric("ความแม่นยำ", "85.3%")

            # Cluster visualization (mock)
            st.markdown("### 📊 การแสดงผลการจัดกลุ่ม")

            # Generate mock data for visualization
            np.random.seed(42)
            n_points = 100
            mock_data = pd.DataFrame(
                {
                    "x": np.random.randn(n_points),
                    "y": np.random.randn(n_points),
                    "cluster": np.random.randint(0, num_clusters, n_points),
                    "name": [f"{clustering_target[:-1]}_{i}" for i in range(n_points)],
                }
            )

            fig = px.scatter(
                mock_data,
                x="x",
                y="y",
                color="cluster",
                hover_data=["name"],
                title=f"การจัดกลุ่ม{clustering_target}",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Cluster characteristics
            st.markdown("### 🔍 ลักษณะของแต่ละกลุ่ม")

            for i in range(num_clusters):
                with st.expander(f"กลุ่มที่ {i+1}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**ลักษณะเด่น:**")
                        if clustering_target == "projects":
                            st.markdown("- งบประมาณขนาดกลาง")
                            st.markdown("- ระยะเวลาปานกลาง")
                            st.markdown("- ทีมขนาดเล็กถึงกลาง")
                        elif clustering_target == "teams":
                            st.markdown("- ประสิทธิภาพสูง")
                            st.markdown("- คุณภาพดี")
                            st.markdown("- ประสบการณ์มาก")

                    with col2:
                        st.markdown("**คำแนะนำ:**")
                        st.markdown("- เหมาะสำหรับโครงการประเภท X")
                        st.markdown("- ควรพัฒนาทักษะ Y")
                        st.markdown("- เพิ่มประสิทธิภาพด้าน Z")

            # Actionable insights
            st.markdown("### 💡 ข้อเสนะแนะเชิงปฏิบัติ")

            insights = [
                f"🎯 สามารถจัดกลุ่ม{clustering_target}เป็น {num_clusters} กลุ่มหลักตามลักษณะที่คล้ายกัน",
                f"📊 กลุ่มที่มีประสิทธิภาพสูงสุดควรเป็นแบบอย่างสำหรับกลุ่มอื่น",
                f"🔧 กลุ่มที่มีปัญหาควรได้รับการสนับสนุนและพัฒนาเพิ่มเติม",
                f"⚡ การจัดสรรทรัพยากรควรพิจารณาจากลักษณะของแต่ละกลุ่ม",
            ]

            for insight in insights:
                st.info(insight)


# Helper Functions
def format_number(value: float, format_type: str = "general") -> str:
    """Format numbers for display"""
    if pd.isna(value):
        return "N/A"

    if format_type == "currency":
        return f"{value:,.0f} บาท"
    elif format_type == "percentage":
        return f"{value:.1f}%"
    elif format_type == "decimal":
        return f"{value:.2f}"
    else:
        return f"{value:,.0f}"


def create_metric_card(
    title: str, value: Any, delta: Any = None, format_type: str = "general"
) -> str:
    """Create HTML metric card"""
    formatted_value = (
        format_number(value, format_type)
        if isinstance(value, (int, float))
        else str(value)
    )

    delta_html = ""
    if delta is not None:
        delta_color = "green" if delta > 0 else "red" if delta < 0 else "gray"
        delta_symbol = "+" if delta > 0 else ""
        delta_html = f'<div style="color: {delta_color}; font-size: 0.8rem;">{delta_symbol}{delta}</div>'

    return f"""
    <div style="
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem;
    ">
        <div style="font-size: 1.5rem; font-weight: bold; color: #2a5298;">{formatted_value}</div>
        <div style="color: #666; font-size: 0.9rem;">{title}</div>
        {delta_html}
    </div>
    """


def generate_insights_from_data(data: Dict[str, Any]) -> List[str]:
    """Generate automatic insights from data"""
    insights = []

    try:
        # This would contain sophisticated logic to generate insights
        # For now, returning mock insights
        insights = [
            "📈 ประสิทธิภาพโดยรวมเพิ่มขึ้น 15% เมื่อเทียบกับเดือนที่แล้ว",
            "⚠️ พบโครงการที่มีความเสี่ยงสูง 3 โครงการ ต้องการการติดตามใกล้ชิด",
            "💰 การใช้งบประมาณอยู่ในเกณฑ์ที่ควบคุมได้ มีประสิทธิภาพดี",
            "👥 ทีมพัฒนามีประสิทธิภาพสูงสุด ควรขยายขนาดทีม",
            "🎯 อัตราการส่งมอบตรงเวลาปรับตัวดีขึ้น แต่ยังต้องพัฒนาต่อ",
        ]
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        insights = ["ไม่สามารถสร้าง insights อัตโนมัติได้ในขณะนี้"]

    return insights


def generate_recommendations_from_insights(insights: List[str]) -> List[str]:
    """Generate recommendations based on insights"""
    recommendations = []

    try:
        # Mock recommendations based on insights
        recommendations = [
            "🚀 ขยายทีมพัฒนาเพิ่ม 2-3 คน เพื่อรองรับโครงการที่เพิ่มขึ้น",
            "📊 ติดตั้งระบบการแจ้งเตือนสำหรับโครงการเสี่ยงสูง",
            "💡 จัดอบรมเพิ่มทักษะการจัดการเวลาให้ทีม",
            "🔄 ปรับปรุงกระบวนการตรวจสอบคุณภาพ",
            "📈 ตั้งเป้าหมายใหม่สำหรับไตรมาสหน้า",
        ]
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        recommendations = ["ไม่สามารถสร้างคำแนะนำอัตโนมัติได้ในขณะนี้"]

    return recommendations


# Export this for use in other modules
__all__ = [
    "AdvancedAnalyticsEngine",
    "ReportType",
    "ReportConfig",
    "show_analytics_page",
    "show_executive_dashboard",
    "show_standard_reports",
    "show_predictive_analytics",
    "show_custom_analysis",
    "show_export_sharing",
]
