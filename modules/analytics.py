#!/usr/bin/env python3
"""
modules/analytics.py
Analytics and Reporting Core Engine for DENSO Project Manager Pro
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """Core analytics engine - ไม่มี UI แค่ logic"""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_project_status_distribution(self) -> List[Dict[str, Any]]:
        """การกระจายสถานะโครงการ"""
        try:
            query = """
            SELECT Status, COUNT(*) as count
            FROM Projects
            WHERE Status != 'Cancelled'
            GROUP BY Status
            ORDER BY count DESC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting project status distribution: {e}")
            return []

    def get_task_status_distribution(self) -> List[Dict[str, Any]]:
        """การกระจายสถานะงาน"""
        try:
            query = """
            SELECT Status, COUNT(*) as count
            FROM Tasks
            GROUP BY Status
            ORDER BY count DESC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting task status distribution: {e}")
            return []

    def get_completion_rate(self) -> float:
        """อัตราความสำเร็จโครงการ"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_projects,
                SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) as completed_projects
            FROM Projects
            WHERE Status != 'Cancelled'
            """
            result = self.db.execute_query(query)
            if result and result[0]["total_projects"] > 0:
                return (
                    result[0]["completed_projects"] / result[0]["total_projects"]
                ) * 100
            return 0.0
        except Exception as e:
            logger.error(f"Error getting completion rate: {e}")
            return 0.0

    def get_progress_timeline(self, days: int = 30) -> List[Dict[str, Any]]:
        """ความคืบหน้าตามเวลา"""
        try:
            query = """
            SELECT 
                CAST(UpdatedDate as DATE) as date,
                AVG(CAST(CompletionPercentage as FLOAT)) as completion
            FROM Projects
            WHERE UpdatedDate >= DATEADD(day, -?, GETDATE())
                AND Status != 'Cancelled'
            GROUP BY CAST(UpdatedDate as DATE)
            ORDER BY date
            """
            return self.db.execute_query(query, (days,))
        except Exception as e:
            logger.error(f"Error getting progress timeline: {e}")
            return []

    def get_productivity_metrics(
        self, start_date: date = None, end_date: date = None
    ) -> Dict[str, Any]:
        """เมทริกประสิทธิภาพ"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            query = """
            SELECT 
                COUNT(DISTINCT p.ProjectID) as active_projects,
                COUNT(DISTINCT t.TaskID) as total_tasks,
                SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                AVG(CAST(p.CompletionPercentage as FLOAT)) as avg_project_completion,
                AVG(CAST(t.CompletionPercentage as FLOAT)) as avg_task_completion,
                SUM(CASE WHEN t.ActualHours IS NOT NULL THEN t.ActualHours ELSE 0 END) as total_hours_logged
            FROM Projects p
            LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
            WHERE p.Status IN ('Planning', 'In Progress')
                AND (t.CreatedDate IS NULL OR t.CreatedDate BETWEEN ? AND ?)
            """
            result = self.db.execute_query(query, (start_date, end_date))
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error getting productivity metrics: {e}")
            return {}

    def get_team_performance(self) -> List[Dict[str, Any]]:
        """ประสิทธิภาพทีม"""
        try:
            query = """
            SELECT 
                u.UserID,
                u.FirstName + ' ' + u.LastName as user_name,
                u.Role,
                u.Department,
                COUNT(t.TaskID) as total_tasks,
                SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                AVG(CAST(t.CompletionPercentage as FLOAT)) as avg_completion,
                SUM(CASE WHEN t.ActualHours IS NOT NULL THEN t.ActualHours ELSE 0 END) as total_hours
            FROM Users u
            LEFT JOIN Tasks t ON u.UserID = t.AssignedToID
            WHERE u.IsActive = 1 AND u.Role IN ('Developer', 'Team Lead', 'Project Manager')
            GROUP BY u.UserID, u.FirstName, u.LastName, u.Role, u.Department
            HAVING COUNT(t.TaskID) > 0
            ORDER BY completed_tasks DESC, avg_completion DESC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting team performance: {e}")
            return []

    def get_budget_analysis(self) -> Dict[str, Any]:
        """วิเคราะห์งบประมาณ"""
        try:
            query = """
            SELECT 
                SUM(Budget) as total_budget,
                SUM(ActualCost) as total_actual_cost,
                COUNT(*) as total_projects,
                SUM(CASE WHEN ActualCost > Budget THEN 1 ELSE 0 END) as over_budget_projects,
                AVG(Budget) as avg_budget,
                AVG(ActualCost) as avg_actual_cost
            FROM Projects
            WHERE Status != 'Cancelled' AND Budget > 0
            """
            result = self.db.execute_query(query)
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error getting budget analysis: {e}")
            return {}

    def get_workload_distribution(self) -> List[Dict[str, Any]]:
        """การกระจายปริมาณงาน"""
        try:
            query = """
            SELECT 
                u.FirstName + ' ' + u.LastName as user_name,
                u.Role,
                COUNT(t.TaskID) as task_count,
                SUM(CASE WHEN t.Status IN ('To Do', 'In Progress', 'Review') THEN 1 ELSE 0 END) as active_tasks,
                SUM(CASE WHEN t.Priority = 'Critical' THEN 1 ELSE 0 END) as critical_tasks,
                SUM(CASE WHEN t.Priority = 'High' THEN 1 ELSE 0 END) as high_priority_tasks,
                AVG(CASE WHEN t.EstimatedHours > 0 THEN t.EstimatedHours ELSE NULL END) as avg_estimated_hours,
                SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as overdue_count
            FROM Users u
            LEFT JOIN Tasks t ON u.UserID = t.AssignedToID
            WHERE u.IsActive = 1
            GROUP BY u.UserID, u.FirstName, u.LastName, u.Role
            ORDER BY active_tasks DESC, task_count DESC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting workload distribution: {e}")
            return []

    def get_quality_metrics(self) -> Dict[str, Any]:
        """เมทริกคุณภาพ"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN Status = 'Review' THEN 1 ELSE 0 END) as tasks_in_review,
                SUM(CASE WHEN Status = 'Testing' THEN 1 ELSE 0 END) as tasks_in_testing,
                SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                AVG(CASE 
                    WHEN ActualHours > 0 AND EstimatedHours > 0 THEN 
                        ABS(ActualHours - EstimatedHours) / EstimatedHours * 100
                    ELSE NULL 
                END) as avg_estimation_variance
            FROM Tasks
            WHERE CreatedDate >= DATEADD(month, -3, GETDATE())
            """
            result = self.db.execute_query(query)
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error getting quality metrics: {e}")
            return {}

    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """กิจกรรมล่าสุด"""
        try:
            query = """
            SELECT TOP (?)
                'Project Update' as activity_type,
                'Project "' + p.Name + '" was updated' as description,
                p.UpdatedDate as timestamp,
                u.FirstName + ' ' + u.LastName as user_name
            FROM Projects p
            LEFT JOIN Users u ON p.ManagerID = u.UserID
            WHERE p.UpdatedDate IS NOT NULL
            ORDER BY p.UpdatedDate DESC
            """
            return self.db.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []

    def get_kpi_summary(self) -> Dict[str, Any]:
        """KPI สรุป"""
        try:
            # รวบรวม KPI สำคัญ
            productivity = self.get_productivity_metrics()
            budget = self.get_budget_analysis()
            completion_rate = self.get_completion_rate()

            return {
                "total_projects": productivity.get("active_projects", 0),
                "completion_rate": completion_rate,
                "total_budget": budget.get("total_budget", 0),
                "budget_utilization": (
                    (budget.get("total_actual_cost", 0) / budget.get("total_budget", 1))
                    * 100
                    if budget.get("total_budget", 0) > 0
                    else 0
                ),
                "total_tasks": productivity.get("total_tasks", 0),
                "overdue_tasks": productivity.get("overdue_tasks", 0),
                "avg_completion": productivity.get("avg_project_completion", 0),
            }
        except Exception as e:
            logger.error(f"Error getting KPI summary: {e}")
            return {}

    def get_trend_analysis(self, metric: str, days: int = 30) -> List[Dict[str, Any]]:
        """วิเคราะห์แนวโน้ม"""
        try:
            if metric == "project_completion":
                return self.get_progress_timeline(days)
            elif metric == "task_completion":
                query = """
                SELECT 
                    CAST(t.UpdatedDate as DATE) as date,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    CAST(SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as FLOAT) / COUNT(*) * 100 as completion_rate
                FROM Tasks t
                WHERE t.UpdatedDate >= DATEADD(day, -?, GETDATE())
                GROUP BY CAST(t.UpdatedDate as DATE)
                ORDER BY date
                """
                return self.db.execute_query(query, (days,))
            return []
        except Exception as e:
            logger.error(f"Error getting trend analysis: {e}")
            return []

    def generate_executive_summary(self) -> Dict[str, Any]:
        """สรุปสำหรับผู้บริหาร"""
        try:
            kpi = self.get_kpi_summary()
            team_perf = self.get_team_performance()
            quality = self.get_quality_metrics()

            # คำนวณ insights
            insights = []
            recommendations = []

            # วิเคราะห์ประสิทธิภาพ
            if kpi.get("completion_rate", 0) >= 80:
                insights.append("ประสิทธิภาพการส่งมอบโครงการอยู่ในระดับดีเยี่ยม")
            elif kpi.get("completion_rate", 0) >= 60:
                insights.append("ประสิทธิภาพการส่งมอบโครงการอยู่ในระดับดี")
                recommendations.append("เพิ่มการติดตามโครงการที่มีความเสี่ยง")
            else:
                insights.append("ประสิทธิภาพการส่งมอบโครงการต้องการการปรับปรุง")
                recommendations.append("ทบทวนกระบวนการจัดการโครงการ")

            # วิเคราะห์งบประมาณ
            budget_util = kpi.get("budget_utilization", 0)
            if budget_util <= 90:
                insights.append("การใช้งบประมาณอยู่ในเกณฑ์ที่ควบคุมได้")
            elif budget_util <= 110:
                insights.append("การใช้งบประมาณใกล้เคียงกับแผน")
            else:
                insights.append("การใช้งบประมาณเกินแผน")
                recommendations.append("ปรับปรุงการควบคุมงบประมาณ")

            # วิเคราะห์ทีม
            if len(team_perf) > 0:
                avg_team_completion = np.mean(
                    [t.get("avg_completion", 0) for t in team_perf]
                )
                if avg_team_completion >= 80:
                    insights.append("ทีมมีประสิทธิภาพดีเยี่ยม")
                else:
                    insights.append("ทีมต้องการการพัฒนา")
                    recommendations.append("จัดอบรมเพิ่มทักษะทีม")

            return {
                "kpi": kpi,
                "insights": insights,
                "recommendations": recommendations,
                "team_count": len(team_perf),
                "quality_score": quality.get("avg_estimation_variance", 0),
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {}

    def get_performance_score(self, entity_type: str, entity_id: int) -> float:
        """คำนวณคะแนนประสิทธิภาพ"""
        try:
            if entity_type == "user":
                query = """
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN Status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN DueDate < GETDATE() AND Status != 'Done' THEN 1 ELSE 0 END) as overdue_tasks,
                    AVG(CAST(CompletionPercentage as FLOAT)) as avg_completion
                FROM Tasks
                WHERE AssignedToID = ?
                """
                result = self.db.execute_query(query, (entity_id,))

                if result and result[0]["total_tasks"] > 0:
                    data = result[0]
                    completion_rate = (
                        data["completed_tasks"] / data["total_tasks"]
                    ) * 100
                    on_time_rate = (
                        (data["total_tasks"] - data["overdue_tasks"])
                        / data["total_tasks"]
                    ) * 100
                    progress_score = data["avg_completion"] or 0

                    # คำนวณคะแนนรวม (เต็ม 100)
                    score = (
                        (completion_rate * 0.4)
                        + (on_time_rate * 0.3)
                        + (progress_score * 0.3)
                    )
                    return min(100, max(0, score))

            elif entity_type == "project":
                query = """
                SELECT 
                    CompletionPercentage,
                    CASE WHEN EndDate < GETDATE() AND Status != 'Completed' THEN 1 ELSE 0 END as is_overdue,
                    CASE WHEN ActualCost > Budget THEN 1 ELSE 0 END as over_budget
                FROM Projects
                WHERE ProjectID = ?
                """
                result = self.db.execute_query(query, (entity_id,))

                if result:
                    data = result[0]
                    completion = data["CompletionPercentage"] or 0
                    time_penalty = 20 if data["is_overdue"] else 0
                    budget_penalty = 15 if data["over_budget"] else 0

                    score = completion - time_penalty - budget_penalty
                    return min(100, max(0, score))

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
