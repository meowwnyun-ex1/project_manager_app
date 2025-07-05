# modules/__init__.py
"""
SDX Project Manager - Modules Package
Enterprise project management modules
"""

__version__ = "2.0.0"
__author__ = "Thammaphon Chittasuwanna (SDM)"
__email__ = "admin@sdx.com"

# Import main classes for easy access
try:
    from .auth import AuthenticationManager
    from .projects import ProjectManager
    from .tasks import TaskManager
    from .users import UserManager
    from .analytics import AnalyticsManager

    __all__ = [
        "AuthenticationManager",
        "ProjectManager",
        "TaskManager",
        "UserManager",
        "AnalyticsManager",
    ]

except ImportError:
    # Handle import errors gracefully during setup
    __all__ = []
