#!/usr/bin/env python3
"""
utils/performance_monitor.py
Enterprise Performance Monitoring & Optimization System
Real-time application performance tracking and analytics
"""

import time
import psutil
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from functools import wraps
import json
import gc
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""

    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = None


@dataclass
class SystemMetrics:
    """System resource metrics"""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    load_average: List[float]


@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""

    active_users: int
    total_requests: int
    requests_per_minute: float
    average_response_time: float
    error_rate: float
    database_connections: int
    cache_hit_rate: float
    memory_usage_mb: float


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self, operation_name: str, monitor: "PerformanceMonitor"):
        self.operation_name = operation_name
        self.monitor = monitor
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time

        self.monitor.record_timing(
            operation=self.operation_name, duration=duration, success=exc_type is None
        )


def monitor_performance(operation_name: str = None):
    """Decorator for monitoring function performance"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            perf_monitor = PerformanceMonitor.get_instance()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            with PerformanceTimer(op_name, perf_monitor):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class PerformanceMonitor:
    """Enterprise performance monitoring system"""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_manager=None):
        self.db = db_manager
        self.metrics_buffer = deque(maxlen=10000)  # In-memory buffer
        self.timing_stats = defaultdict(list)
        self.request_stats = defaultdict(int)
        self.error_stats = defaultdict(int)

        # Configuration
        self.collection_interval = 60  # seconds
        self.retention_days = 30
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "response_time": 2.0,  # seconds
            "error_rate": 5.0,  # percent
        }

        # Background monitoring
        self.monitoring_active = False
        self.monitor_thread = None

        # Metrics history for trend analysis
        self.metrics_history = defaultdict(
            lambda: deque(maxlen=1440)
        )  # 24 hours at 1-minute intervals

        self._initialize_monitoring()

    @classmethod
    def get_instance(cls, db_manager=None):
        """Singleton pattern for global access"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_manager)
            return cls._instance

    def _initialize_monitoring(self):
        """Initialize monitoring infrastructure"""
        try:
            if self.db:
                self._create_metrics_tables()
            self._start_background_monitoring()

        except Exception as e:
            logger.error(f"Error initializing performance monitoring: {e}")

    def _create_metrics_tables(self):
        """Create database tables for metrics storage"""
        try:
            # System metrics table
            system_metrics_table = """
            CREATE TABLE IF NOT EXISTS system_metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cpu_percent DECIMAL(5,2),
                memory_percent DECIMAL(5,2),
                memory_used_mb INTEGER,
                memory_available_mb INTEGER,
                disk_usage_percent DECIMAL(5,2),
                disk_free_gb DECIMAL(10,2),
                network_sent_mb DECIMAL(10,2),
                network_recv_mb DECIMAL(10,2),
                active_connections INTEGER,
                load_average JSONB
            )
            """

            # Application metrics table
            app_metrics_table = """
            CREATE TABLE IF NOT EXISTS application_metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active_users INTEGER,
                total_requests INTEGER,
                requests_per_minute DECIMAL(8,2),
                average_response_time DECIMAL(8,4),
                error_rate DECIMAL(5,2),
                database_connections INTEGER,
                cache_hit_rate DECIMAL(5,2),
                memory_usage_mb DECIMAL(10,2)
            )
            """

            # Performance timings table
            timings_table = """
            CREATE TABLE IF NOT EXISTS performance_timings (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                operation_name VARCHAR(255),
                duration_ms DECIMAL(10,4),
                success BOOLEAN,
                tags JSONB
            )
            """

            # Alerts table
            alerts_table = """
            CREATE TABLE IF NOT EXISTS performance_alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_type VARCHAR(50),
                metric_name VARCHAR(100),
                current_value DECIMAL(10,4),
                threshold_value DECIMAL(10,4),
                severity VARCHAR(20),
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP
            )
            """

            tables = [
                system_metrics_table,
                app_metrics_table,
                timings_table,
                alerts_table,
            ]
            for table_sql in tables:
                self.db.execute_query(table_sql)

            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_app_metrics_timestamp ON application_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_timings_timestamp ON performance_timings(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_timings_operation ON performance_timings(operation_name)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON performance_alerts(timestamp)",
            ]

            for index_sql in indexes:
                self.db.execute_query(index_sql)

        except Exception as e:
            logger.error(f"Error creating metrics tables: {e}")

    def _start_background_monitoring(self):
        """Start background monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self.monitor_thread.start()
            logger.info("Background performance monitoring started")

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self.collect_system_metrics()
                self._store_system_metrics(system_metrics)

                # Collect application metrics
                app_metrics = self.collect_application_metrics()
                self._store_application_metrics(app_metrics)

                # Check alerts
                self._check_alerts(system_metrics, app_metrics)

                # Cleanup old data
                self._cleanup_old_data()

                # Sleep until next collection
                time.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Short sleep on error

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024 * 1024 * 1024)

            # Network metrics
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)

            # Connection count
            try:
                active_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                active_connections = -1

            # Load average (Unix-like systems)
            try:
                load_average = (
                    list(psutil.getloadavg())
                    if hasattr(psutil, "getloadavg")
                    else [0.0, 0.0, 0.0]
                )
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_connections=active_connections,
                load_average=load_average,
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, [0, 0, 0])

    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        try:
            # Get current process metrics
            process = psutil.Process()
            app_memory_mb = process.memory_info().rss / (1024 * 1024)

            # Calculate request metrics
            total_requests = sum(self.request_stats.values())

            # Calculate requests per minute (last minute)
            current_minute = datetime.now().replace(second=0, microsecond=0)
            rpm_key = current_minute.strftime("%Y-%m-%d %H:%M")
            requests_per_minute = self.request_stats.get(rpm_key, 0)

            # Calculate average response time
            recent_timings = []
            cutoff_time = datetime.now() - timedelta(minutes=5)

            for operation, timings in self.timing_stats.items():
                recent_timings.extend(
                    [t for t in timings if t["timestamp"] > cutoff_time]
                )

            if recent_timings:
                average_response_time = sum(
                    t["duration"] for t in recent_timings
                ) / len(recent_timings)
            else:
                average_response_time = 0.0

            # Calculate error rate
            total_errors = sum(self.error_stats.values())
            error_rate = (total_errors / max(total_requests, 1)) * 100

            # Placeholder metrics (would be integrated with actual components)
            active_users = self._get_active_users_count()
            database_connections = self._get_database_connections()
            cache_hit_rate = self._get_cache_hit_rate()

            return ApplicationMetrics(
                active_users=active_users,
                total_requests=total_requests,
                requests_per_minute=requests_per_minute,
                average_response_time=average_response_time,
                error_rate=error_rate,
                database_connections=database_connections,
                cache_hit_rate=cache_hit_rate,
                memory_usage_mb=app_memory_mb,
            )

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return ApplicationMetrics(0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0)

    def record_timing(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        tags: Dict[str, str] = None,
    ):
        """Record operation timing"""
        try:
            timing_record = {
                "timestamp": datetime.now(),
                "operation": operation,
                "duration": duration,
                "success": success,
                "tags": tags or {},
            }

            # Add to in-memory stats
            if operation not in self.timing_stats:
                self.timing_stats[operation] = deque(maxlen=1000)

            self.timing_stats[operation].append(timing_record)

            # Store in database if available
            if self.db:
                self._store_timing_record(timing_record)

            # Check for slow operations
            if duration > self.alert_thresholds.get("response_time", 2.0):
                self._create_alert(
                    alert_type="slow_operation",
                    metric_name=f"response_time.{operation}",
                    current_value=duration,
                    threshold_value=self.alert_thresholds["response_time"],
                    severity="warning",
                )

        except Exception as e:
            logger.error(f"Error recording timing for {operation}: {e}")

    def record_request(self, path: str = "", method: str = "", status_code: int = 200):
        """Record HTTP request"""
        try:
            current_minute = datetime.now().replace(second=0, microsecond=0)
            minute_key = current_minute.strftime("%Y-%m-%d %H:%M")

            self.request_stats[minute_key] += 1

            # Record errors
            if status_code >= 400:
                error_key = f"{method}:{path}:{status_code}"
                self.error_stats[error_key] += 1

        except Exception as e:
            logger.error(f"Error recording request: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        try:
            system_metrics = self.collect_system_metrics()
            app_metrics = self.collect_application_metrics()

            return {
                "timestamp": datetime.now().isoformat(),
                "system": asdict(system_metrics),
                "application": asdict(app_metrics),
                "top_slow_operations": self._get_top_slow_operations(),
                "recent_alerts": self._get_recent_alerts(),
                "health_score": self._calculate_health_score(
                    system_metrics, app_metrics
                ),
            }

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}

    def get_metrics_history(
        self, metric_name: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get historical metrics data"""
        try:
            if self.db:
                return self._get_metrics_from_db(metric_name, hours)
            else:
                return self._get_metrics_from_memory(metric_name, hours)

        except Exception as e:
            logger.error(f"Error getting metrics history: {e}")
            return []

    def create_performance_alert(
        self, metric_name: str, threshold: float, comparison: str = "greater"
    ):
        """Create custom performance alert"""
        try:
            # Store alert configuration
            alert_config = {
                "metric_name": metric_name,
                "threshold": threshold,
                "comparison": comparison,
                "created_at": datetime.now(),
            }

            self.alert_thresholds[metric_name] = threshold
            logger.info(f"Created performance alert for {metric_name} > {threshold}")

        except Exception as e:
            logger.error(f"Error creating performance alert: {e}")

    def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        if not self.db:
            return

        try:
            query = """
            INSERT INTO system_metrics (
                cpu_percent, memory_percent, memory_used_mb, memory_available_mb,
                disk_usage_percent, disk_free_gb, network_sent_mb, network_recv_mb,
                active_connections, load_average
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.memory_used_mb,
                metrics.memory_available_mb,
                metrics.disk_usage_percent,
                metrics.disk_free_gb,
                metrics.network_sent_mb,
                metrics.network_recv_mb,
                metrics.active_connections,
                json.dumps(metrics.load_average),
            )

            self.db.execute_query(query, values)

        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")

    def _store_application_metrics(self, metrics: ApplicationMetrics):
        """Store application metrics in database"""
        if not self.db:
            return

        try:
            query = """
            INSERT INTO application_metrics (
                active_users, total_requests, requests_per_minute, average_response_time,
                error_rate, database_connections, cache_hit_rate, memory_usage_mb
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                metrics.active_users,
                metrics.total_requests,
                metrics.requests_per_minute,
                metrics.average_response_time,
                metrics.error_rate,
                metrics.database_connections,
                metrics.cache_hit_rate,
                metrics.memory_usage_mb,
            )

            self.db.execute_query(query, values)

        except Exception as e:
            logger.error(f"Error storing application metrics: {e}")

    def _store_timing_record(self, timing_record: Dict[str, Any]):
        """Store timing record in database"""
        if not self.db:
            return

        try:
            query = """
            INSERT INTO performance_timings (operation_name, duration_ms, success, tags)
            VALUES (%s, %s, %s, %s)
            """

            values = (
                timing_record["operation"],
                timing_record["duration"] * 1000,  # Convert to milliseconds
                timing_record["success"],
                json.dumps(timing_record["tags"]),
            )

            self.db.execute_query(query, values)

        except Exception as e:
            logger.error(f"Error storing timing record: {e}")

    def _check_alerts(
        self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics
    ):
        """Check for performance alerts"""
        try:
            # System alerts
            alerts_to_check = [
                ("cpu_percent", system_metrics.cpu_percent),
                ("memory_percent", system_metrics.memory_percent),
                ("disk_usage_percent", system_metrics.disk_usage_percent),
                ("response_time", app_metrics.average_response_time),
                ("error_rate", app_metrics.error_rate),
            ]

            for metric_name, current_value in alerts_to_check:
                threshold = self.alert_thresholds.get(metric_name)
                if threshold and current_value > threshold:
                    severity = (
                        "critical" if current_value > threshold * 1.2 else "warning"
                    )
                    self._create_alert(
                        alert_type="threshold_exceeded",
                        metric_name=metric_name,
                        current_value=current_value,
                        threshold_value=threshold,
                        severity=severity,
                    )

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def _create_alert(
        self,
        alert_type: str,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        severity: str,
    ):
        """Create performance alert"""
        try:
            if self.db:
                query = """
                INSERT INTO performance_alerts 
                (alert_type, metric_name, current_value, threshold_value, severity)
                VALUES (%s, %s, %s, %s, %s)
                """

                self.db.execute_query(
                    query,
                    (alert_type, metric_name, current_value, threshold_value, severity),
                )

            # Log alert
            logger.warning(
                f"Performance Alert [{severity.upper()}]: {metric_name} = {current_value:.2f} "
                f"(threshold: {threshold_value:.2f})"
            )

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    def _cleanup_old_data(self):
        """Clean up old metrics data"""
        if not self.db:
            return

        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            cleanup_queries = [
                ("DELETE FROM system_metrics WHERE timestamp < %s", (cutoff_date,)),
                (
                    "DELETE FROM application_metrics WHERE timestamp < %s",
                    (cutoff_date,),
                ),
                (
                    "DELETE FROM performance_timings WHERE timestamp < %s",
                    (cutoff_date,),
                ),
                (
                    "DELETE FROM performance_alerts WHERE timestamp < %s AND resolved = true",
                    (cutoff_date,),
                ),
            ]

            for query, params in cleanup_queries:
                self.db.execute_query(query, params)

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    def _get_top_slow_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top slow operations"""
        try:
            operation_averages = {}

            for operation, timings in self.timing_stats.items():
                if timings:
                    recent_timings = [
                        t
                        for t in timings
                        if t["timestamp"] > datetime.now() - timedelta(hours=1)
                    ]
                    if recent_timings:
                        avg_time = sum(t["duration"] for t in recent_timings) / len(
                            recent_timings
                        )
                        operation_averages[operation] = {
                            "operation": operation,
                            "average_duration": avg_time,
                            "call_count": len(recent_timings),
                        }

            # Sort by average duration
            top_operations = sorted(
                operation_averages.values(),
                key=lambda x: x["average_duration"],
                reverse=True,
            )

            return top_operations[:limit]

        except Exception as e:
            logger.error(f"Error getting top slow operations: {e}")
            return []

    def _get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance alerts"""
        if not self.db:
            return []

        try:
            query = """
            SELECT alert_type, metric_name, current_value, threshold_value, 
                   severity, timestamp, resolved
            FROM performance_alerts 
            ORDER BY timestamp DESC 
            LIMIT %s
            """

            results = self.db.fetch_all(query, (limit,))

            alerts = []
            for result in results:
                alerts.append(
                    {
                        "alert_type": result[0],
                        "metric_name": result[1],
                        "current_value": float(result[2]),
                        "threshold_value": float(result[3]),
                        "severity": result[4],
                        "timestamp": result[5],
                        "resolved": result[6],
                    }
                )

            return alerts

        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []

    def _calculate_health_score(
        self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics
    ) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            # Weight factors for different metrics
            weights = {
                "cpu": 0.2,
                "memory": 0.2,
                "disk": 0.1,
                "response_time": 0.3,
                "error_rate": 0.2,
            }

            # Calculate individual scores (100 = perfect, 0 = critical)
            cpu_score = max(0, 100 - system_metrics.cpu_percent)
            memory_score = max(0, 100 - system_metrics.memory_percent)
            disk_score = max(0, 100 - system_metrics.disk_usage_percent)

            # Response time score (2 seconds = 0, 0 seconds = 100)
            response_score = max(0, 100 - (app_metrics.average_response_time / 0.02))

            # Error rate score (10% = 0, 0% = 100)
            error_score = max(0, 100 - (app_metrics.error_rate * 10))

            # Calculate weighted average
            health_score = (
                cpu_score * weights["cpu"]
                + memory_score * weights["memory"]
                + disk_score * weights["disk"]
                + response_score * weights["response_time"]
                + error_score * weights["error_rate"]
            )

            return round(health_score, 1)

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0  # Default neutral score

    def _get_active_users_count(self) -> int:
        """Get active users count (placeholder)"""
        # This would integrate with session management
        return 0

    def _get_database_connections(self) -> int:
        """Get database connection count"""
        if not self.db:
            return 0

        try:
            # PostgreSQL specific query
            query = "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            result = self.db.fetch_one(query)
            return result[0] if result else 0

        except Exception:
            return 0

    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate (placeholder)"""
        # This would integrate with Redis or cache system
        return 0.0

    def _get_metrics_from_db(
        self, metric_name: str, hours: int
    ) -> List[Dict[str, Any]]:
        """Get metrics from database"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Determine which table to query based on metric name
            if metric_name.startswith("system."):
                table = "system_metrics"
                column = metric_name.replace("system.", "")
            elif metric_name.startswith("app."):
                table = "application_metrics"
                column = metric_name.replace("app.", "")
            else:
                return []

            query = f"""
            SELECT timestamp, {column} as value
            FROM {table}
            WHERE timestamp >= %s
            ORDER BY timestamp ASC
            """

            results = self.db.fetch_all(query, (cutoff_time,))

            metrics = []
            for result in results:
                metrics.append(
                    {
                        "timestamp": result[0].isoformat(),
                        "value": float(result[1]) if result[1] is not None else 0.0,
                    }
                )

            return metrics

        except Exception as e:
            logger.error(f"Error getting metrics from database: {e}")
            return []

    def _get_metrics_from_memory(
        self, metric_name: str, hours: int
    ) -> List[Dict[str, Any]]:
        """Get metrics from in-memory storage"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            history = self.metrics_history.get(metric_name, deque())

            filtered_metrics = [
                metric for metric in history if metric["timestamp"] > cutoff_time
            ]

            return filtered_metrics

        except Exception as e:
            logger.error(f"Error getting metrics from memory: {e}")
            return []

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_monitoring()


# Global performance monitor instance
performance_monitor = None


def get_performance_monitor(db_manager=None):
    """Get global performance monitor instance"""
    global performance_monitor
    if performance_monitor is None:
        performance_monitor = PerformanceMonitor(db_manager)
    return performance_monitor
