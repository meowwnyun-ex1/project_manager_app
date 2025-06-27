# models/task.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class Task:
    """Task model with validation"""

    task_id: Optional[int] = None
    project_id: int = 0
    task_name: str = ""
    description: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assignee_id: Optional[int] = None
    status: str = "To Do"
    progress: int = 0
    created_date: Optional[datetime] = None

    def __post_init__(self):
        """Validate task data after initialization"""
        if self.task_name:
            self.validate_name()
        if self.status:
            self.validate_status()
        if self.progress is not None:
            self.validate_progress()
        if self.start_date and self.end_date:
            self.validate_dates()
        if self.project_id:
            self.validate_project_id()

    def validate_name(self) -> bool:
        """Validate task name"""
        if not self.task_name:
            raise ValueError("Task name is required")
        if len(self.task_name.strip()) < 2:
            raise ValueError("Task name must be at least 2 characters")
        if len(self.task_name) > 100:
            raise ValueError("Task name must be less than 100 characters")
        return True

    def validate_status(self) -> bool:
        """Validate task status"""
        from config.settings import app_config

        if self.status not in app_config.TASK_STATUSES:
            raise ValueError(f"Status must be one of: {app_config.TASK_STATUSES}")
        return True

    def validate_progress(self) -> bool:
        """Validate task progress"""
        if self.progress < 0 or self.progress > 100:
            raise ValueError("Progress must be between 0 and 100")
        return True

    def validate_dates(self) -> bool:
        """Validate task dates"""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date must be after start date")
        return True

    def validate_project_id(self) -> bool:
        """Validate project ID"""
        if self.project_id <= 0:
            raise ValueError("Valid project ID is required")
        return True

    @property
    def duration_days(self) -> Optional[int]:
        """Calculate task duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if self.end_date and self.status != "Done":
            return date.today() > self.end_date
        return False

    @property
    def is_in_progress(self) -> bool:
        """Check if task is currently in progress"""
        return self.status == "In Progress"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == "Done" or self.progress == 100

    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until task is due"""
        if self.end_date:
            delta = self.end_date - date.today()
            return delta.days
        return None

    def to_dict(self) -> dict:
        """Convert task to dictionary"""
        return {
            "TaskID": self.task_id,
            "ProjectID": self.project_id,
            "TaskName": self.task_name,
            "Description": self.description,
            "StartDate": self.start_date,
            "EndDate": self.end_date,
            "AssigneeID": self.assignee_id,
            "Status": self.status,
            "Progress": self.progress,
            "CreatedDate": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary"""
        return cls(
            task_id=data.get("TaskID"),
            project_id=data.get("ProjectID", 0),
            task_name=data.get("TaskName", ""),
            description=data.get("Description", ""),
            start_date=data.get("StartDate"),
            end_date=data.get("EndDate"),
            assignee_id=data.get("AssigneeID"),
            status=data.get("Status", "To Do"),
            progress=data.get("Progress", 0),
            created_date=data.get("CreatedDate"),
        )
