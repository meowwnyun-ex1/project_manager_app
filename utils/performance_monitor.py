#!/usr/bin/env python3
"""
utils/performance_monitor.py
Performance Monitoring for SDX Project Manager
System performance tracking and optimization
"""

import time
import logging
import psutil
import streamlit as st
from functools import wraps
from datetime import datetime
from typing import Dict, Any, Callable, Optional
import threading

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """System performance monitoring and tracking"""

    def __init__(self):
        self.metrics = {}
        self.function_timings = {}
        self.system_metrics = {}
        self.start_time = time.time()
        self.request_count = 0

    def time_function(self, func_name: Optional[str] = None):
        """Decorator to measure function execution time"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise
                finally:
                    end_time = time.time()
                    execution_time = end_time - start_time

                    name = func_name or func.__name__
                    self._record_timing(name, execution_time, success)

                return result

            return wrapper

        return decorator

    def _record_timing(self, func_name: str, execution_time: float, success: bool):
        """Record function timing"""
        if func_name not in self.function_timings:
            self.function_timings[func_name] = {
                "total_time": 0,
                "call_count": 0,
                "success_count": 0,
                "min_time": float("inf"),
                "max_time": 0,
                "last_call": None,
            }

        timing = self.function_timings[func_name]
        timing["total_time"] += execution_time
        timing["call_count"] += 1
        if success:
            timing["success_count"] += 1
        timing["min_time"] = min(timing["min_time"], execution_time)
        timing["max_time"] = max(timing["max_time"], execution_time)
        timing["last_call"] = datetime.now()

        # Log slow functions (> 2 seconds)
        if execution_time > 2.0:
            logger.warning(
                f"Slow function detected: {func_name} took {execution_time:.2f}s"
            )

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)

            # Process info
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024**2)  # MB
            process_cpu = process.cpu_percent()

            return {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory_percent, 1),
                "memory_used_gb": round(memory_used_gb, 2),
                "memory_total_gb": round(memory_total_gb, 2),
                "disk_percent": round(disk_percent, 1),
                "disk_used_gb": round(disk_used_gb, 2),
                "disk_total_gb": round(disk_total_gb, 2),
                "process_memory_mb": round(process_memory, 1),
                "process_cpu_percent": round(process_cpu, 1),
                "uptime_seconds": round(time.time() - self.start_time, 1),
            }

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    def get_function_performance(self) -> Dict[str, Any]:
        """Get function performance statistics"""
        performance_data = {}

        for func_name, timing in self.function_timings.items():
            if timing["call_count"] > 0:
                avg_time = timing["total_time"] / timing["call_count"]
                success_rate = (timing["success_count"] / timing["call_count"]) * 100

                performance_data[func_name] = {
                    "avg_time": round(avg_time, 4),
                    "total_time": round(timing["total_time"], 4),
                    "call_count": timing["call_count"],
                    "success_rate": round(success_rate, 1),
                    "min_time": round(timing["min_time"], 4),
                    "max_time": round(timing["max_time"], 4),
                    "last_call": (
                        timing["last_call"].strftime("%H:%M:%S")
                        if timing["last_call"]
                        else None
                    ),
                }

        return performance_data

    def increment_request_count(self):
        """Increment request counter"""
        self.request_count += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        uptime = time.time() - self.start_time

        # Calculate average requests per minute
        if uptime > 60:
            requests_per_minute = (self.request_count / uptime) * 60
        else:
            requests_per_minute = 0

        # Get slowest functions
        slowest_functions = []
        for func_name, timing in self.function_timings.items():
            if timing["call_count"] > 0:
                avg_time = timing["total_time"] / timing["call_count"]
                slowest_functions.append({"function": func_name, "avg_time": avg_time})

        slowest_functions.sort(key=lambda x: x["avg_time"], reverse=True)

        return {
            "uptime_hours": round(uptime / 3600, 2),
            "total_requests": self.request_count,
            "requests_per_minute": round(requests_per_minute, 1),
            "total_functions_called": len(self.function_timings),
            "slowest_functions": slowest_functions[:5],
        }

    def render_performance_dashboard(self):
        """Render performance dashboard in Streamlit"""
        st.subheader("📊 System Performance Monitor")

        # System metrics
        system_metrics = self.get_system_metrics()
        if system_metrics:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "CPU Usage", f"{system_metrics.get('cpu_percent', 0)}%", delta=None
                )

            with col2:
                st.metric(
                    "Memory Usage",
                    f"{system_metrics.get('memory_percent', 0)}%",
                    delta=f"{system_metrics.get('memory_used_gb', 0):.1f}GB",
                )

            with col3:
                st.metric(
                    "Disk Usage",
                    f"{system_metrics.get('disk_percent', 0)}%",
                    delta=f"{system_metrics.get('disk_used_gb', 0):.1f}GB",
                )

            with col4:
                uptime_hours = system_metrics.get("uptime_seconds", 0) / 3600
                st.metric(
                    "Uptime",
                    f"{uptime_hours:.1f}h",
                    delta=f"{self.request_count} requests",
                )

        # Performance summary
        summary = self.get_performance_summary()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⚡ Performance Summary")
            st.write(f"**Total Functions:** {summary.get('total_functions_called', 0)}")
            st.write(f"**Requests/Min:** {summary.get('requests_per_minute', 0)}")

            # Slowest functions
            if summary.get("slowest_functions"):
                st.write("**Slowest Functions:**")
                for func in summary["slowest_functions"]:
                    st.write(f"• {func['function']}: {func['avg_time']:.3f}s")

        with col2:
            st.subheader("🔍 Function Performance")
            performance_data = self.get_function_performance()

            if performance_data:
                # Create DataFrame for display
                import pandas as pd

                perf_df = pd.DataFrame(
                    [
                        {
                            "Function": func_name,
                            "Calls": data["call_count"],
                            "Avg Time (s)": data["avg_time"],
                            "Success Rate (%)": data["success_rate"],
                            "Last Call": data["last_call"],
                        }
                        for func_name, data in performance_data.items()
                    ]
                )

                st.dataframe(perf_df, use_container_width=True)

    def log_performance_warning(self, message: str):
        """Log performance warning"""
        logger.warning(f"Performance Warning: {message}")

    def check_performance_thresholds(self):
        """Check if performance metrics exceed thresholds"""
        system_metrics = self.get_system_metrics()
        warnings = []

        # CPU threshold
        if system_metrics.get("cpu_percent", 0) > 80:
            warnings.append(f"High CPU usage: {system_metrics['cpu_percent']}%")

        # Memory threshold
        if system_metrics.get("memory_percent", 0) > 85:
            warnings.append(f"High memory usage: {system_metrics['memory_percent']}%")

        # Disk threshold
        if system_metrics.get("disk_percent", 0) > 90:
            warnings.append(f"High disk usage: {system_metrics['disk_percent']}%")

        # Slow functions
        for func_name, timing in self.function_timings.items():
            if timing["call_count"] > 0:
                avg_time = timing["total_time"] / timing["call_count"]
                if avg_time > 5.0:  # 5 seconds threshold
                    warnings.append(f"Slow function: {func_name} ({avg_time:.2f}s avg)")

        return warnings

    def optimize_suggestions(self) -> list:
        """Get optimization suggestions"""
        suggestions = []
        system_metrics = self.get_system_metrics()

        # CPU optimization
        if system_metrics.get("cpu_percent", 0) > 70:
            suggestions.append(
                "Consider optimizing database queries or caching results"
            )

        # Memory optimization
        if system_metrics.get("memory_percent", 0) > 80:
            suggestions.append(
                "Review memory usage and consider implementing data pagination"
            )

        # Function optimization
        slow_functions = []
        for func_name, timing in self.function_timings.items():
            if timing["call_count"] > 0:
                avg_time = timing["total_time"] / timing["call_count"]
                if avg_time > 2.0:
                    slow_functions.append(func_name)

        if slow_functions:
            suggestions.append(
                f"Optimize slow functions: {', '.join(slow_functions[:3])}"
            )

        return suggestions


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def monitor_performance(func_name: Optional[str] = None):
    """Decorator for monitoring function performance"""
    monitor = get_performance_monitor()
    return monitor.time_function(func_name)


def track_request():
    """Track application request"""
    monitor = get_performance_monitor()
    monitor.increment_request_count()


# Context manager for performance monitoring
class PerformanceContext:
    """Context manager for monitoring code block performance"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.monitor = get_performance_monitor()

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time = time.time() - self.start_time
            success = exc_type is None
            self.monitor._record_timing(self.operation_name, execution_time, success)


# Example usage:
# with PerformanceContext("Database Query"):
#     result = db.execute_query("SELECT * FROM Users")
