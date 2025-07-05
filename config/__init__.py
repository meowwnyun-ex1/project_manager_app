# config/__init__.py
"""
SDX Project Manager - Configuration Package
Database and application configuration
"""

__version__ = "2.0.0"

# Import configuration classes
try:
    from .database import DatabaseManager, get_database_manager

    __all__ = ["DatabaseManager", "get_database_manager"]

except ImportError:
    # Handle import errors gracefully during setup
    __all__ = []
