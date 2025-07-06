#!/usr/bin/env python3
"""
modules/projects.py
Enterprise Project Management System
Advanced project tracking with financial management and resource allocation
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Project status enumeration"""

    DRAFT = "Draft"
    PLANNING = "Planning"
    ACTIVE = "Active"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ARCHIVED = "Archived"


class ProjectPriority(Enum):
    """Project priority levels"""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ProjectCategory(Enum):
    """Project categories"""

    WEB_DEVELOPMENT = "Web Development"
    MOBILE_DEVELOPMENT = "Mobile Development"
    DATA_SCIENCE = "Data Science"
    AI_ML = "AI/ML"
    INFRASTRUCTURE = "Infrastructure"
    RESEARCH = "Research"
    MARKETING = "Marketing"
    BUSINESS = "Business"
    OTHER = "Other"


@dataclass
class ProjectMetrics:
    """Project performance metrics"""

    budget_utilization: float
    schedule_performance: float
    resource_utilization: float
    quality_score: float
    risk_score: float
    team_satisfaction: float


class ProjectManager:
    """Enterprise project management system"""

    def __init__(self, db_manager):
        self.db = db_manager
        self._ensure_sample_data()

    def _ensure_sample_data(self):
        """Initialize sample projects if database is empty"""
        try:
            project_count = self.db.execute_scalar("SELECT COUNT(*) FROM Projects")

            if project_count == 0:
                # Create sample projects
                sample_projects = [
                    {
                        "name": "เว็บไซต์บริษัทใหม่",
                        "description": "พัฒนาเว็บไซต์บริษัทด้วยเทคโนโลยีใหม่ เน้น UX/UI ที่ทันสมัย",
                        "status": "Active",
                        "priority": "High",
                        "start_date": "2024-07-01",
                        "end_date": "2024-12-31",
                        "budget": 800000,
                        "category": "Web Development",
                        "project_code": "WEB2024001",
                    },
                    {
                        "name": "แอปพลิเคชันมือถือ DENSO",
                        "description": "แอปมือถือสำหรับพนักงาน DENSO เพื่อจัดการงานและสื่อสาร",
                        "status": "Planning",
                        "priority": "Medium",
                        "start_date": "2024-08-15",
                        "end_date": "2025-03-15",
                        "budget": 1200000,
                        "category": "Mobile Development",
                        "project_code": "MOB2024001",
                    },
                    {
                        "name": "ระบบวิเคราะห์ข้อมูล AI",
                        "description": "พัฒนาระบบ AI สำหรับวิเคราะห์ข้อมูลการผลิตและคาดการณ์แนวโน้ม",
                        "status": "Active",
                        "priority": "Critical",
                        "start_date": "2024-06-01",
                        "end_date": "2024-11-30",
                        "budget": 2000000,
                        "category": "AI/ML",
                        "project_code": "AI2024001",
                    },
                    {
                        "name": "ระบบ ERP ใหม่",
                        "description": "ปรับปรุงระบบ ERP เพื่อรองรับการเติบโตของธุรกิจ",
                        "status": "Planning",
                        "priority": "High",
                        "start_date": "2024-09-01",
                        "end_date": "2025-06-30",
                        "budget": 3500000,
                        "category": "Business",
                        "project_code": "ERP2024001",
                    },
                    {
                        "name": "โครงการวิจัยและพัฒนา IoT",
                        "description": "วิจัยและพัฒนาเทคโนโลยี IoT สำหรับโรงงานอัจฉริยะ",
                        "status": "Active",
                        "priority": "Medium",
                        "start_date": "2024-05-15",
                        "end_date": "2024-12-15",
                        "budget": 1500000,
                        "category": "Research",
                        "project_code": "IOT2024001",
                    },
                ]

                for project in sample_projects:
                    try:
                        self.create_project(project, manager_id=1)
                    except Exception as e:
                        logger.warning(f"Sample project creation failed: {e}")

                logger.info("Sample projects created successfully")

        except Exception as e:
            logger.error(f"Sample data initialization failed: {e}")

    def create_project(
        self, project_data: Dict[str, Any], manager_id: int
    ) -> Tuple[bool, str, Optional[int]]:
        """Create new project with validation"""
        try:
            # Validate required fields
            required_fields = [
                "name",
                "description",
                "start_date",
                "end_date",
                "budget",
            ]
            for field in required_fields:
                if not project_data.get(field):
                    return False, f"กรุณากรอก {field}", None

            # Validate dates
            try:
                start_date = datetime.strptime(
                    str(project_data["start_date"]), "%Y-%m-%d"
                )
                end_date = datetime.strptime(str(project_data["end_date"]), "%Y-%m-%d")

                if end_date <= start_date:
                    return False, "วันที่สิ้นสุดต้องมากกว่าวันที่เริ่มต้น", None

            except ValueError:
                return False, "รูปแบบวันที่ไม่ถูกต้อง", None

            # Validate budget
            try:
                budget = float(project_data["budget"])
                if budget <= 0:
                    return False, "งบประมาณต้องมากกว่า 0", None
            except (ValueError, TypeError):
                return False, "งบประมาณไม่ถูกต้อง", None

            # Generate project code if not provided
            project_code = project_data.get("project_code")
            if not project_code:
                project_code = self._generate_project_code(
                    project_data.get("category", "OTHER")
                )

            # Check project code uniqueness
            existing_code = self.db.execute_scalar(
                "SELECT COUNT(*) FROM Projects WHERE ProjectCode = ?", (project_code,)
            )
            if existing_code > 0:
                return False, "รหัสโครงการนี้มีอยู่แล้ว", None

            # Insert project
            project_id = self.db.execute_scalar(
                """
                INSERT INTO Projects (
                    Name, Description, Status, Priority, StartDate, EndDate,
                    Budget, ManagerID, ProjectCode, Category, ClientName, CreatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING ProjectID
            """,
                (
                    project_data["name"],
                    project_data["description"],
                    project_data.get("status", "Planning"),
                    project_data.get("priority", "Medium"),
                    project_data["start_date"],
                    project_data["end_date"],
                    budget,
                    manager_id,
                    project_code,
                    project_data.get("category", "Other"),
                    project_data.get("client_name", ""),
                    datetime.now(),
                ),
            )

            # If using SQLite, get the last inserted row ID
            if not project_id:
                project_id = self.db.execute_scalar("SELECT last_insert_rowid()")

            # Add project manager as team member
            self.add_project_member(project_id, manager_id, "Project Manager")

            # Log project creation
            self._log_project_activity(
                project_id,
                manager_id,
                "PROJECT_CREATED",
                f"โครงการ '{project_data['name']}' ถูกสร้างแล้ว",
            )

            logger.info(f"Project created: {project_data['name']} (ID: {project_id})")
            return True, "สร้างโครงการสำเร็จ", project_id

        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return False, "เกิดข้อผิดพลาดในการสร้างโครงการ", None

    def _generate_project_code(self, category: str) -> str:
        """Generate unique project code"""
        try:
            # Get category prefix
            category_prefixes = {
                "Web Development": "WEB",
                "Mobile Development": "MOB",
                "Data Science": "DATA",
                "AI/ML": "AI",
                "Infrastructure": "INFRA",
                "Research": "RES",
                "Marketing": "MKT",
                "Business": "BIZ",
            }

            prefix = category_prefixes.get(category, "PROJ")
            year = datetime.now().year

            # Get next sequence number
            last_code = self.db.execute_scalar(
                """
                SELECT ProjectCode FROM Projects 
                WHERE ProjectCode LIKE ? 
                ORDER BY ProjectCode DESC 
                LIMIT 1
            """,
                (f"{prefix}{year}%",),
            )

            if last_code:
                try:
                    sequence = int(last_code[-3:]) + 1
                except:
                    sequence = 1
            else:
                sequence = 1

            return f"{prefix}{year}{sequence:03d}"

        except Exception as e:
            logger.error(f"Project code generation failed: {e}")
            return f"PROJ{datetime.now().year}{datetime.now().month:02d}{datetime.now().day:02d}"

    def update_project(
        self, project_id: int, project_data: Dict[str, Any], user_id: int
    ) -> Tuple[bool, str]:
        """Update project with validation and audit trail"""
        try:
            # Get current project data
            current_project = self.get_project_by_id(project_id)
            if not current_project:
                return False, "ไม่พบโครงการ"

            # Validate dates if provided
            if "start_date" in project_data and "end_date" in project_data:
                try:
                    start_date = datetime.strptime(
                        str(project_data["start_date"]), "%Y-%m-%d"
                    )
                    end_date = datetime.strptime(
                        str(project_data["end_date"]), "%Y-%m-%d"
                    )

                    if end_date <= start_date:
                        return False, "วันที่สิ้นสุดต้องมากกว่าวันที่เริ่มต้น"

                except ValueError:
                    return False, "รูปแบบวันที่ไม่ถูกต้อง"

            # Validate budget if provided
            if "budget" in project_data:
                try:
                    budget = float(project_data["budget"])
                    if budget <= 0:
                        return False, "งบประมาณต้องมากกว่า 0"
                except (ValueError, TypeError):
                    return False, "งบประมาณไม่ถูกต้อง"

            # Build update query dynamically
            update_fields = []
            params = []

            updateable_fields = {
                "name": "Name",
                "description": "Description",
                "status": "Status",
                "priority": "Priority",
                "start_date": "StartDate",
                "end_date": "EndDate",
                "budget": "Budget",
                "actual_cost": "ActualCost",
                "progress": "Progress",
                "category": "Category",
                "client_name": "ClientName",
            }

            for field, db_field in updateable_fields.items():
                if field in project_data:
                    update_fields.append(f"{db_field} = ?")
                    params.append(project_data[field])

            if not update_fields:
                return False, "ไม่มีข้อมูลที่ต้องอัพเดท"

            # Add update timestamp
            update_fields.append("UpdatedAt = ?")
            params.append(datetime.now())
            params.append(project_id)

            # Execute update
            query = (
                f"UPDATE Projects SET {', '.join(update_fields)} WHERE ProjectID = ?"
            )
            self.db.execute_query(query, tuple(params))

            # Log changes
            changes = []
            for field in updateable_fields:
                if field in project_data:
                    old_value = current_project.get(updateable_fields[field])
                    new_value = project_data[field]
                    if old_value != new_value:
                        changes.append(f"{field}: {old_value} → {new_value}")

            if changes:
                self._log_project_activity(
                    project_id,
                    user_id,
                    "PROJECT_UPDATED",
                    f"อัพเดทโครงการ: {', '.join(changes)}",
                )

            logger.info(f"Project updated: {project_id}")
            return True, "อัพเดทโครงการสำเร็จ"

        except Exception as e:
            logger.error(f"Project update failed: {e}")
            return False, "เกิดข้อผิดพลาดในการอัพเดทโครงการ"

    def delete_project(self, project_id: int, user_id: int) -> Tuple[bool, str]:
        """Soft delete project (mark as inactive)"""
        try:
            # Check if project exists
            project = self.get_project_by_id(project_id)
            if not project:
                return False, "ไม่พบโครงการ"

            # Check if project has active tasks
            active_tasks = self.db.execute_scalar(
                """
                SELECT COUNT(*) FROM Tasks 
                WHERE ProjectID = ? AND Status NOT IN ('Done', 'Cancelled') AND IsActive = 1
            """,
                (project_id,),
            )

            if active_tasks > 0:
                return (
                    False,
                    f"ไม่สามารถลบโครงการได้ เนื่องจากมีงานที่ยังไม่เสร็จ {active_tasks} งาน",
                )

            # Soft delete project
            self.db.execute_query(
                """
                UPDATE Projects SET IsActive = 0, UpdatedAt = ? WHERE ProjectID = ?
            """,
                (datetime.now(), project_id),
            )

            # Deactivate project members
            self.db.execute_query(
                """
                UPDATE ProjectMembers SET IsActive = 0 WHERE ProjectID = ?
            """,
                (project_id,),
            )

            # Log deletion
            self._log_project_activity(
                project_id,
                user_id,
                "PROJECT_DELETED",
                f"โครงการ '{project['Name']}' ถูกลบแล้ว",
            )

            logger.info(f"Project soft deleted: {project_id}")
            return True, "ลบโครงการสำเร็จ"

        except Exception as e:
            logger.error(f"Project deletion failed: {e}")
            return False, "เกิดข้อผิดพลาดในการลบโครงการ"

    def get_all_projects(
        self,
        user_id: int = None,
        status_filter: str = None,
        include_inactive: bool = False,
    ) -> List[Dict]:
        """Get all projects with optional filtering"""
        try:
            query = """
                SELECT p.*, u.FullName as ManagerName,
                       (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID AND IsActive = 1) as TaskCount,
                       (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID AND Status = 'Done' AND IsActive = 1) as CompletedTasks,
                       (SELECT COUNT(*) FROM ProjectMembers WHERE ProjectID = p.ProjectID AND IsActive = 1) as TeamSize
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
                WHERE 1=1
            """
            params = []

            # Filter by active status
            if not include_inactive:
                query += " AND p.IsActive = 1"

            # Filter by status
            if status_filter and status_filter != "All":
                query += " AND p.Status = ?"
                params.append(status_filter)

            # Filter by user access (if user is not admin)
            if user_id:
                user_role = self._get_user_role(user_id)
                if user_role not in ["Admin", "Super Admin"]:
                    query += """ AND (p.ManagerID = ? OR 
                                EXISTS (SELECT 1 FROM ProjectMembers WHERE ProjectID = p.ProjectID AND UserID = ? AND IsActive = 1))"""
                    params.extend([user_id, user_id])

            query += " ORDER BY p.CreatedAt DESC"

            projects = self.db.execute_query(query, tuple(params))

            # Calculate additional metrics
            for project in projects:
                project["CompletionRate"] = 0
                if project["TaskCount"] > 0:
                    project["CompletionRate"] = (
                        project["CompletedTasks"] / project["TaskCount"]
                    ) * 100

                # Calculate budget utilization
                project["BudgetUtilization"] = 0
                if project["Budget"] and project["Budget"] > 0:
                    actual_cost = project.get("ActualCost", 0) or 0
                    project["BudgetUtilization"] = (
                        actual_cost / project["Budget"]
                    ) * 100

                # Calculate days remaining
                if project["EndDate"]:
                    try:
                        end_date = datetime.strptime(
                            str(project["EndDate"])[:10], "%Y-%m-%d"
                        )
                        days_remaining = (end_date - datetime.now()).days
                        project["DaysRemaining"] = max(0, days_remaining)
                    except:
                        project["DaysRemaining"] = 0
                else:
                    project["DaysRemaining"] = 0

            return projects

        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []

    def get_project_by_id(self, project_id: int) -> Optional[Dict]:
        """Get project by ID with detailed information"""
        try:
            project = self.db.execute_query(
                """
                SELECT p.*, u.FullName as ManagerName, u.Email as ManagerEmail
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
                WHERE p.ProjectID = ?
            """,
                (project_id,),
            )

            if not project:
                return None

            project = project[0]

            # Get project members
            members = self.db.execute_query(
                """
                SELECT pm.*, u.FullName, u.Email, u.Position, u.Department
                FROM ProjectMembers pm
                JOIN Users u ON pm.UserID = u.UserID
                WHERE pm.ProjectID = ? AND pm.IsActive = 1
                ORDER BY pm.Role, u.FullName
            """,
                (project_id,),
            )

            project["Members"] = members

            # Get project tasks summary
            task_summary = self.db.execute_query(
                """
                SELECT Status, COUNT(*) as Count
                FROM Tasks
                WHERE ProjectID = ? AND IsActive = 1
                GROUP BY Status
            """,
                (project_id,),
            )

            project["TaskSummary"] = {
                item["Status"]: item["Count"] for item in task_summary
            }

            # Get recent activities
            activities = self.db.execute_query(
                """
                SELECT al.*, u.FullName
                FROM AuditLog al
                LEFT JOIN Users u ON al.UserID = u.UserID
                WHERE al.RecordID = ? AND al.TableName = 'Projects'
                ORDER BY al.CreatedAt DESC
                LIMIT 10
            """,
                (project_id,),
            )

            project["RecentActivities"] = activities

            return project

        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return None

    def add_project_member(
        self, project_id: int, user_id: int, role: str = "Member"
    ) -> Tuple[bool, str]:
        """Add member to project"""
        try:
            # Check if already a member
            existing = self.db.execute_scalar(
                """
                SELECT COUNT(*) FROM ProjectMembers 
                WHERE ProjectID = ? AND UserID = ? AND IsActive = 1
            """,
                (project_id, user_id),
            )

            if existing > 0:
                return False, "ผู้ใช้นี้เป็นสมาชิกโครงการอยู่แล้ว"

            # Add member
            self.db.execute_query(
                """
                INSERT INTO ProjectMembers (ProjectID, UserID, Role, JoinedAt)
                VALUES (?, ?, ?, ?)
            """,
                (project_id, user_id, role, datetime.now()),
            )

            # Get user name for logging
            user_name = self.db.execute_scalar(
                "SELECT FullName FROM Users WHERE UserID = ?", (user_id,)
            )

            self._log_project_activity(
                project_id, user_id, "MEMBER_ADDED", f"เพิ่มสมาชิก: {user_name} ({role})"
            )

            logger.info(f"Member added to project {project_id}: {user_id}")
            return True, "เพิ่มสมาชิกสำเร็จ"

        except Exception as e:
            logger.error(f"Failed to add project member: {e}")
            return False, "เกิดข้อผิดพลาดในการเพิ่มสมาชิก"

    def remove_project_member(
        self, project_id: int, user_id: int, removed_by: int
    ) -> Tuple[bool, str]:
        """Remove member from project"""
        try:
            # Check if project manager
            project = self.get_project_by_id(project_id)
            if project and project["ManagerID"] == user_id:
                return False, "ไม่สามารถลบผู้จัดการโครงการได้"

            # Remove member
            self.db.execute_query(
                """
                UPDATE ProjectMembers SET IsActive = 0 
                WHERE ProjectID = ? AND UserID = ?
            """,
                (project_id, user_id),
            )

            # Get user name for logging
            user_name = self.db.execute_scalar(
                "SELECT FullName FROM Users WHERE UserID = ?", (user_id,)
            )

            self._log_project_activity(
                project_id, removed_by, "MEMBER_REMOVED", f"ลบสมาชิก: {user_name}"
            )

            logger.info(f"Member removed from project {project_id}: {user_id}")
            return True, "ลบสมาชิกสำเร็จ"

        except Exception as e:
            logger.error(f"Failed to remove project member: {e}")
            return False, "เกิดข้อผิดพลาดในการลบสมาชิก"

    def get_project_count(self, status: str = None) -> int:
        """Get total project count"""
        try:
            if status:
                return (
                    self.db.execute_scalar(
                        "SELECT COUNT(*) FROM Projects WHERE Status = ? AND IsActive = 1",
                        (status,),
                    )
                    or 0
                )
            else:
                return (
                    self.db.execute_scalar(
                        "SELECT COUNT(*) FROM Projects WHERE IsActive = 1"
                    )
                    or 0
                )
        except Exception as e:
            logger.error(f"Failed to get project count: {e}")
            return 0

    def get_projects_by_manager(self, manager_id: int) -> List[Dict]:
        """Get projects managed by specific user"""
        try:
            return self.db.execute_query(
                """
                SELECT * FROM Projects 
                WHERE ManagerID = ? AND IsActive = 1
                ORDER BY CreatedAt DESC
            """,
                (manager_id,),
            )
        except Exception as e:
            logger.error(f"Failed to get projects by manager: {e}")
            return []

    def get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics"""
        try:
            stats = {}

            # Status distribution
            status_dist = self.db.execute_query(
                """
                SELECT Status, COUNT(*) as Count
                FROM Projects WHERE IsActive = 1
                GROUP BY Status
            """
            )
            stats["status_distribution"] = {
                item["Status"]: item["Count"] for item in status_dist
            }

            # Priority distribution
            priority_dist = self.db.execute_query(
                """
                SELECT Priority, COUNT(*) as Count
                FROM Projects WHERE IsActive = 1
                GROUP BY Priority
            """
            )
            stats["priority_distribution"] = {
                item["Priority"]: item["Count"] for item in priority_dist
            }

            # Category distribution
            category_dist = self.db.execute_query(
                """
                SELECT Category, COUNT(*) as Count
                FROM Projects WHERE IsActive = 1
                GROUP BY Category
            """
            )
            stats["category_distribution"] = {
                item["Category"]: item["Count"] for item in category_dist
            }

            # Budget analytics
            budget_stats = self.db.execute_query(
                """
                SELECT 
                    SUM(Budget) as TotalBudget,
                    SUM(ActualCost) as TotalActualCost,
                    AVG(Budget) as AvgBudget,
                    COUNT(*) as ProjectCount
                FROM Projects WHERE IsActive = 1
            """
            )

            if budget_stats:
                stats["budget_analytics"] = budget_stats[0]

                total_budget = budget_stats[0]["TotalBudget"] or 0
                total_actual = budget_stats[0]["TotalActualCost"] or 0

                stats["budget_analytics"]["BudgetUtilization"] = (
                    (total_actual / total_budget * 100) if total_budget > 0 else 0
                )

            # Timeline analytics
            timeline_stats = self.db.execute_query(
                """
                SELECT 
                    COUNT(CASE WHEN EndDate < DATE('now') AND Status != 'Completed' THEN 1 END) as OverdueProjects,
                    COUNT(CASE WHEN EndDate BETWEEN DATE('now') AND DATE('now', '+30 days') THEN 1 END) as ProjectsDueSoon,
                    COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as CompletedProjects
                FROM Projects WHERE IsActive = 1
            """
            )

            if timeline_stats:
                stats["timeline_analytics"] = timeline_stats[0]

            return stats

        except Exception as e:
            logger.error(f"Failed to get project statistics: {e}")
            return {}

    def get_project_metrics(self, project_id: int) -> ProjectMetrics:
        """Calculate comprehensive project metrics"""
        try:
            project = self.get_project_by_id(project_id)
            if not project:
                return ProjectMetrics(0, 0, 0, 0, 0, 0)

            # Budget utilization
            budget_utilization = 0
            if project["Budget"] and project["Budget"] > 0:
                actual_cost = project.get("ActualCost", 0) or 0
                budget_utilization = min((actual_cost / project["Budget"]) * 100, 100)

            # Schedule performance (based on progress vs elapsed time)
            schedule_performance = 0
            if project["StartDate"] and project["EndDate"]:
                try:
                    start_date = datetime.strptime(
                        str(project["StartDate"])[:10], "%Y-%m-%d"
                    )
                    end_date = datetime.strptime(
                        str(project["EndDate"])[:10], "%Y-%m-%d"
                    )
                    total_days = (end_date - start_date).days
                    elapsed_days = (datetime.now() - start_date).days

                    if total_days > 0 and elapsed_days > 0:
                        expected_progress = min((elapsed_days / total_days) * 100, 100)
                        actual_progress = project.get("Progress", 0) or 0
                        schedule_performance = (
                            (actual_progress / expected_progress * 100)
                            if expected_progress > 0
                            else 0
                        )
                except:
                    schedule_performance = 0

            # Resource utilization (based on team size vs tasks)
            resource_utilization = 0
            team_size = len(project.get("Members", []))
            task_count = sum(project.get("TaskSummary", {}).values())
            if team_size > 0:
                resource_utilization = min(
                    (task_count / team_size) * 20, 100
                )  # Assume 5 tasks per person is 100%

            # Quality score (based on completed vs total tasks)
            quality_score = 0
            completed_tasks = project.get("TaskSummary", {}).get("Done", 0)
            total_tasks = sum(project.get("TaskSummary", {}).values())
            if total_tasks > 0:
                quality_score = (completed_tasks / total_tasks) * 100

            # Risk score (based on delays, budget overrun, etc.)
            risk_score = 0
            if project["DaysRemaining"] < 0:  # Overdue
                risk_score += 30
            if budget_utilization > 90:  # Budget almost exhausted
                risk_score += 25
            if schedule_performance < 80:  # Behind schedule
                risk_score += 25
            if team_size < 2:  # Small team risk
                risk_score += 20

            risk_score = min(risk_score, 100)

            # Team satisfaction (placeholder - would be from surveys)
            team_satisfaction = 85  # Default good score

            return ProjectMetrics(
                budget_utilization=budget_utilization,
                schedule_performance=schedule_performance,
                resource_utilization=resource_utilization,
                quality_score=quality_score,
                risk_score=risk_score,
                team_satisfaction=team_satisfaction,
            )

        except Exception as e:
            logger.error(f"Failed to calculate project metrics: {e}")
            return ProjectMetrics(0, 0, 0, 0, 0, 0)

    def _get_user_role(self, user_id: int) -> str:
        """Get user role"""
        try:
            return (
                self.db.execute_scalar(
                    "SELECT Role FROM Users WHERE UserID = ?", (user_id,)
                )
                or "User"
            )
        except:
            return "User"

    def _log_project_activity(
        self, project_id: int, user_id: int, action: str, description: str
    ):
        """Log project activity to audit trail"""
        try:
            self.db.execute_query(
                """
                INSERT INTO AuditLog (UserID, Action, TableName, RecordID, NewValues, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (user_id, action, "Projects", project_id, description, datetime.now()),
            )
        except Exception as e:
            logger.error(f"Failed to log project activity: {e}")

    def export_projects_to_excel(self, projects: List[Dict]) -> bytes:
        """Export projects to Excel format"""
        try:
            df = pd.DataFrame(projects)

            # Select and rename columns for export
            export_columns = {
                "ProjectCode": "รหัสโครงการ",
                "Name": "ชื่อโครงการ",
                "Description": "คำอธิบาย",
                "Status": "สถานะ",
                "Priority": "ความสำคัญ",
                "Category": "หมวดหมู่",
                "StartDate": "วันที่เริ่มต้น",
                "EndDate": "วันที่สิ้นสุด",
                "Budget": "งบประมาณ",
                "ActualCost": "ค่าใช้จ่ายจริง",
                "Progress": "ความคืบหน้า (%)",
                "ManagerName": "ผู้จัดการโครงการ",
                "TeamSize": "จำนวนสมาชิก",
                "TaskCount": "จำนวนงาน",
                "CompletedTasks": "งานที่เสร็จแล้ว",
            }

            # Filter and rename columns
            df_export = df.reindex(columns=list(export_columns.keys())).rename(
                columns=export_columns
            )

            # Format data
            if "วันที่เริ่มต้น" in df_export.columns:
                df_export["วันที่เริ่มต้น"] = pd.to_datetime(
                    df_export["วันที่เริ่มต้น"]
                ).dt.strftime("%d/%m/%Y")
            if "วันที่สิ้นสุด" in df_export.columns:
                df_export["วันที่สิ้นสุด"] = pd.to_datetime(df_export["วันที่สิ้นสุด"]).dt.strftime(
                    "%d/%m/%Y"
                )
            if "งบประมาณ" in df_export.columns:
                df_export["งบประมาณ"] = df_export["งบประมาณ"].apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) else ""
                )
            if "ค่าใช้จ่ายจริง" in df_export.columns:
                df_export["ค่าใช้จ่ายจริง"] = df_export["ค่าใช้จ่ายจริง"].apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) else "0"
                )

            # Export to Excel
            from io import BytesIO

            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_export.to_excel(writer, sheet_name="โครงการ", index=False)

                # Format worksheet
                worksheet = writer.sheets["โครงการ"]

                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter

                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass

                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

                # Add header formatting
                from openpyxl.styles import Font, PatternFill

                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(
                    start_color="366092", end_color="366092", fill_type="solid"
                )

                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill

            return output.getvalue()

        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return b""

    def search_projects(self, search_term: str, user_id: int = None) -> List[Dict]:
        """Search projects by name, description, or project code"""
        try:
            search_pattern = f"%{search_term}%"

            query = """
                SELECT p.*, u.FullName as ManagerName
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
                WHERE p.IsActive = 1 AND (
                    p.Name LIKE ? OR 
                    p.Description LIKE ? OR 
                    p.ProjectCode LIKE ? OR
                    p.Category LIKE ?
                )
            """
            params = [search_pattern, search_pattern, search_pattern, search_pattern]

            # Filter by user access if needed
            if user_id:
                user_role = self._get_user_role(user_id)
                if user_role not in ["Admin", "Super Admin"]:
                    query += """ AND (p.ManagerID = ? OR 
                                EXISTS (SELECT 1 FROM ProjectMembers WHERE ProjectID = p.ProjectID AND UserID = ? AND IsActive = 1))"""
                    params.extend([user_id, user_id])

            query += " ORDER BY p.Name"

            return self.db.execute_query(query, tuple(params))

        except Exception as e:
            logger.error(f"Project search failed: {e}")
            return []

    def get_project_dashboard_data(self, user_id: int = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data for projects"""
        try:
            dashboard_data = {}

            # Basic counts
            dashboard_data["total_projects"] = self.get_project_count()
            dashboard_data["active_projects"] = self.get_project_count("Active")
            dashboard_data["completed_projects"] = self.get_project_count("Completed")
            dashboard_data["overdue_projects"] = (
                self.db.execute_scalar(
                    """
                SELECT COUNT(*) FROM Projects 
                WHERE EndDate < DATE('now') AND Status != 'Completed' AND IsActive = 1
            """
                )
                or 0
            )

            # Recent projects
            dashboard_data["recent_projects"] = self.db.execute_query(
                """
                SELECT p.*, u.FullName as ManagerName
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
                WHERE p.IsActive = 1
                ORDER BY p.CreatedAt DESC
                LIMIT 5
            """
            )

            # Projects by status
            status_data = self.db.execute_query(
                """
                SELECT Status, COUNT(*) as Count
                FROM Projects WHERE IsActive = 1
                GROUP BY Status
            """
            )
            dashboard_data["projects_by_status"] = {
                item["Status"]: item["Count"] for item in status_data
            }

            # Budget overview
            budget_data = self.db.execute_query(
                """
                SELECT 
                    SUM(Budget) as TotalBudget,
                    SUM(COALESCE(ActualCost, 0)) as TotalSpent,
                    COUNT(*) as ProjectCount
                FROM Projects WHERE IsActive = 1
            """
            )

            if budget_data and budget_data[0]["TotalBudget"]:
                dashboard_data["budget_overview"] = budget_data[0]
                dashboard_data["budget_overview"]["BudgetUtilization"] = (
                    (budget_data[0]["TotalSpent"] / budget_data[0]["TotalBudget"]) * 100
                    if budget_data[0]["TotalBudget"] > 0
                    else 0
                )
            else:
                dashboard_data["budget_overview"] = {
                    "TotalBudget": 0,
                    "TotalSpent": 0,
                    "ProjectCount": 0,
                    "BudgetUtilization": 0,
                }

            # Top performing projects (by completion rate)
            dashboard_data["top_projects"] = self.db.execute_query(
                """
                SELECT p.Name, p.Progress, p.Status, u.FullName as ManagerName
                FROM Projects p
                LEFT JOIN Users u ON p.ManagerID = u.UserID
                WHERE p.IsActive = 1 AND p.Status = 'Active'
                ORDER BY p.Progress DESC
                LIMIT 5
            """
            )

            # Project timeline (next 30 days)
            dashboard_data["upcoming_deadlines"] = self.db.execute_query(
                """
                SELECT Name, EndDate, Status, Priority
                FROM Projects
                WHERE IsActive = 1 AND EndDate BETWEEN DATE('now') AND DATE('now', '+30 days')
                ORDER BY EndDate ASC
                LIMIT 10
            """
            )

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}

    def clone_project(
        self, project_id: int, new_name: str, manager_id: int
    ) -> Tuple[bool, str, Optional[int]]:
        """Clone existing project with new name"""
        try:
            # Get original project
            original_project = self.get_project_by_id(project_id)
            if not original_project:
                return False, "ไม่พบโครงการต้นฉบับ", None

            # Create new project data
            new_project_data = {
                "name": new_name,
                "description": f"คัดลอกจาก: {original_project['Name']}\n{original_project['Description']}",
                "status": "Planning",
                "priority": original_project["Priority"],
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                "budget": original_project["Budget"],
                "category": original_project["Category"],
                "client_name": original_project.get("ClientName", ""),
            }

            # Create cloned project
            success, message, new_project_id = self.create_project(
                new_project_data, manager_id
            )

            if success and new_project_id:
                # Clone project members
                for member in original_project.get("Members", []):
                    if member["UserID"] != manager_id:  # Skip manager as already added
                        self.add_project_member(
                            new_project_id, member["UserID"], member["Role"]
                        )

                # Log cloning
                self._log_project_activity(
                    new_project_id,
                    manager_id,
                    "PROJECT_CLONED",
                    f"คัดลอกจากโครงการ: {original_project['Name']}",
                )

                logger.info(f"Project cloned: {project_id} -> {new_project_id}")
                return True, "คัดลอกโครงการสำเร็จ", new_project_id

            return success, message, new_project_id

        except Exception as e:
            logger.error(f"Project cloning failed: {e}")
            return False, "เกิดข้อผิดพลาดในการคัดลอกโครงการ", None

    def archive_project(self, project_id: int, user_id: int) -> Tuple[bool, str]:
        """Archive completed project"""
        try:
            project = self.get_project_by_id(project_id)
            if not project:
                return False, "ไม่พบโครงการ"

            if project["Status"] not in ["Completed", "Cancelled"]:
                return False, "สามารถเก็บถาวรได้เฉพาะโครงการที่เสร็จสิ้นหรือยกเลิกแล้ว"

            # Update status to archived
            self.db.execute_query(
                """
                UPDATE Projects SET Status = 'Archived', UpdatedAt = ? WHERE ProjectID = ?
            """,
                (datetime.now(), project_id),
            )

            # Log archiving
            self._log_project_activity(
                project_id,
                user_id,
                "PROJECT_ARCHIVED",
                f"โครงการ '{project['Name']}' ถูกเก็บถาวรแล้ว",
            )

            logger.info(f"Project archived: {project_id}")
            return True, "เก็บถาวรโครงการสำเร็จ"

        except Exception as e:
            logger.error(f"Project archiving failed: {e}")
            return False, "เกิดข้อผิดพลาดในการเก็บถาวรโครงการ"

    def restore_project(self, project_id: int, user_id: int) -> Tuple[bool, str]:
        """Restore archived project"""
        try:
            project = self.get_project_by_id(project_id)
            if not project:
                return False, "ไม่พบโครงการ"

            if project["Status"] != "Archived":
                return False, "สามารถคืนค่าได้เฉพาะโครงการที่เก็บถาวรแล้ว"

            # Restore to active status
            self.db.execute_query(
                """
                UPDATE Projects SET Status = 'Active', UpdatedAt = ? WHERE ProjectID = ?
            """,
                (datetime.now(), project_id),
            )

            # Log restoration
            self._log_project_activity(
                project_id,
                user_id,
                "PROJECT_RESTORED",
                f"โครงการ '{project['Name']}' ถูกคืนค่าแล้ว",
            )

            logger.info(f"Project restored: {project_id}")
            return True, "คืนค่าโครงการสำเร็จ"

        except Exception as e:
            logger.error(f"Project restoration failed: {e}")
            return False, "เกิดข้อผิดพลาดในการคืนค่าโครงการ"
