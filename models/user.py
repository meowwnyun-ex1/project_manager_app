# models/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re


@dataclass
class User:
    """User model with validation"""

    user_id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: str = "User"
    created_date: Optional[datetime] = None

    def __post_init__(self):
        """Validate user data after initialization"""
        if self.username:
            self.validate_username()
        if self.role:
            self.validate_role()

    def validate_username(self) -> bool:
        """Validate username format"""
        if not self.username:
            raise ValueError("Username is required")
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(self.username) > 50:
            raise ValueError("Username must be less than 50 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", self.username):
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )
        return True

    def validate_role(self) -> bool:
        """Validate user role"""
        from config.settings import app_config

        if self.role not in app_config.USER_ROLES:
            raise ValueError(f"Role must be one of: {app_config.USER_ROLES}")
        return True

    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength"""
        if not password:
            raise ValueError("Password is required")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(password) > 255:
            raise ValueError("Password is too long")
        return True

    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            "UserID": self.user_id,
            "Username": self.username,
            "Role": self.role,
            "CreatedDate": self.created_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from dictionary"""
        return cls(
            user_id=data.get("UserID"),
            username=data.get("Username", ""),
            password_hash=data.get("PasswordHash", ""),
            role=data.get("Role", "User"),
            created_date=data.get("CreatedDate"),
        )
