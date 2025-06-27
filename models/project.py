# models/project.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class Project:
    """Project model with validation"""

    project_id: Optional[int] = None
    project_name: str = ""
    description: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "Planning"
    created_date: Optional[datetime] = None

    def __post_init__(self):
        """Validate project data after initialization"""
        if self.project_name:
            self.validate_name()
        if self.status:
            self.validate_status()
        if self.start_date and self.end_date:
            self.validate_dates()

    def validate_name(self) -> bool:
        """Validate project name"""
        if not self.project_name:
            raise ValueError("Project name is required")
        if len(self.project_name.strip()) < 2:
            raise ValueError("Project name must be at least 2 characters")
        if len(self.project_name) > 100:
            raise ValueError("Project name must be less than 100 characters")
        return True

    def validate_status(self) -> bool:
        """Validate project status"""
        from config.settings import app_config

        if self.status not in app_config.PROJECT_STATUSES:
            raise ValueError(f"Status must be one of: {app_config.PROJECT_STATUSES}")
        return True

    def validate_dates(self) -> bool:
        """Validate project dates"""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date must be after start date")
        return True

    @property
    def duration_days(self) -> Optional[int]:
        """Calculate project duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    @property
    def is_active(self) -> bool:
        """Check if project is currently active"""
        return self.status in ["Planning", "In Progress"]

    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue"""
        if self.end_date and self.status not in ["Completed", "Cancelled"]:
            return date.today() > self.end_date
        return False

    def to_dict(self) -> dict:
        """Convert project to dictionary"""
        return {
            "ProjectID": self.project_id,
            "ProjectName": self.project_name,
            "Description": self.description,
            "StartDate": self.start_date,
            "EndDate": self.end_date,
            "Status": self.status,
            "CreatedDate": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Create Project from dictionary"""
        return cls(
            project_id=data.get("ProjectID"),
            project_name=data.get("ProjectName", ""),
            description=data.get("Description", ""),
            start_date=data.get("StartDate"),
            end_date=data.get("EndDate"),
            status=data.get("Status", "Planning"),
            created_date=data.get("CreatedDate"),
        )
