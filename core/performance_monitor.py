# core/performance_monitor.py
import time
import psutil
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Application performance monitoring system"""

    def __init__(self):
        self.start_time = None
        self.metrics = {
            "request_count": 0,
            "total_response_time": 0,
            "avg_response_time": 0,
            "max_response_time": 0,
            "min_response_time": float("inf"),
            "memory_usage": 0,
            "cpu_usage": 0,
        }
        self.request_history = []
        self.max_history = 100

    def start_request(self):
        """Start monitoring a request"""
        self.start_time = time.time()

    def end_request(self):
        """End request monitoring and update metrics"""
        if self.start_time:
            response_time = time.time() - self.start_time
            self._update_metrics(response_time)
            self.start_time = None

    def _update_metrics(self, response_time: float):
        """Update performance metrics"""
        self.metrics["request_count"] += 1
        self.metrics["total_response_time"] += response_time
        self.metrics["avg_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["request_count"]
        )
        self.metrics["max_response_time"] = max(
            self.metrics["max_response_time"], response_time
        )
        self.metrics["min_response_time"] = min(
            self.metrics["min_response_time"], response_time
        )

        # System metrics
        try:
            process = psutil.Process()
            self.metrics["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
            self.metrics["cpu_usage"] = process.cpu_percent()
        except:
            pass

        # Store request history
        self.request_history.append(
            {
                "timestamp": datetime.now(),
                "response_time": response_time,
                "memory_usage": self.metrics["memory_usage"],
                "cpu_usage": self.metrics["cpu_usage"],
            }
        )

        # Keep only recent history
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate detailed performance report"""
        return {
            "current_metrics": self.get_current_metrics(),
            "request_history": self.request_history[-10:],  # Last 10 requests
            "system_info": self._get_system_info(),
        }

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total
                / 1024
                / 1024
                / 1024,  # GB
                "memory_available": psutil.virtual_memory().available
                / 1024
                / 1024
                / 1024,  # GB
                "disk_usage": psutil.disk_usage("/").percent,
            }
        except:
            return {}
