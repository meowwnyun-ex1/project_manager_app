# utils/__init__.py
"""
SDX Project Manager - Utilities Package
Helper functions and utilities
"""

__version__ = "2.0.0"

# Import utility classes
try:
    from .ui_components import UIComponents
    from .error_handler import ErrorHandler, safe_execute, handle_error
    from .performance_monitor import PerformanceMonitor, get_performance_monitor

    __all__ = [
        "UIComponents",
        "ErrorHandler",
        "safe_execute",
        "handle_error",
        "PerformanceMonitor",
        "get_performance_monitor",
    ]

except ImportError:
    # Handle import errors gracefully during setup
    __all__ = []
