"""
utils/performance_monitor.py
Performance monitoring and optimization utilities
"""

import streamlit as st
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager
import json
import os
import threading
from dataclasses import dataclass, asdict
from functools import wraps
import gc

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None
    status: str = "normal"  # normal, warning, critical

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "threshold": self.threshold,
            "status": self.status,
        }


@dataclass
class CacheItem:
    """Cache item data structure"""

    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if cache item is expired"""
        return datetime.now() > self.expires_at

    def get_age_seconds(self) -> float:
        """Get age of cache item in seconds"""
        return (datetime.now() - self.created_at).total_seconds()


class PerformanceMonitor:
    """Performance monitoring and optimization manager"""

    def __init__(self):
        self.metrics = {}
        self.performance_history = []
        self.monitoring_enabled = True
        self.start_time = time.time()

        # Performance thresholds
        self.thresholds = {
            "page_load_time": 2.0,  # seconds
            "memory_usage": 512,  # MB
            "db_query_time": 1.0,  # seconds
            "cache_hit_rate": 80.0,  # percentage
            "cpu_usage": 80.0,  # percentage
            "response_time": 0.5,  # seconds
        }

        # Initialize session state for performance tracking
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state for performance tracking"""
        if "performance_metrics" not in st.session_state:
            st.session_state.performance_metrics = {}

        if "page_load_times" not in st.session_state:
            st.session_state.page_load_times = []

        if "cache_stats" not in st.session_state:
            st.session_state.cache_stats = {"hits": 0, "misses": 0, "total_size": 0}

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager to measure execution time"""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            if self.monitoring_enabled:
                execution_time = time.time() - start_time
                end_memory = self._get_memory_usage()
                memory_delta = end_memory - start_memory

                # Record metric
                self.record_metric(
                    f"{operation_name}_time",
                    execution_time,
                    "seconds",
                    self.thresholds.get("response_time", 0.5),
                )

                # Record memory usage if significant
                if abs(memory_delta) > 10:  # 10MB threshold
                    self.record_metric(
                        f"{operation_name}_memory_delta", memory_delta, "MB"
                    )

                # Log slow operations
                if execution_time > self.thresholds.get("response_time", 0.5):
                    logger.warning(
                        f"Slow operation detected: {operation_name} took {execution_time:.2f}s"
                    )

    def record_metric(
        self, name: str, value: float, unit: str, threshold: Optional[float] = None
    ):
        """Record a performance metric"""
        try:
            # Determine status based on threshold
            status = "normal"
            if threshold:
                if value > threshold * 1.5:
                    status = "critical"
                elif value > threshold:
                    status = "warning"

            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                threshold=threshold,
                status=status,
            )

            # Store in metrics dictionary
            self.metrics[name] = metric

            # Add to history
            self.performance_history.append(metric)

            # Keep only recent history (last 1000 entries)
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]

            # Store in session state
            st.session_state.performance_metrics[name] = metric.to_dict()

        except Exception as e:
            logger.error(f"Error recording metric {name}: {str(e)}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            current_metrics = {}

            # System metrics
            current_metrics["memory_usage"] = self._get_memory_usage()
            current_metrics["cpu_usage"] = self._get_cpu_usage()
            current_metrics["uptime"] = time.time() - self.start_time

            # Cache metrics
            cache_stats = st.session_state.get("cache_stats", {})
            total_requests = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
            if total_requests > 0:
                current_metrics["cache_hit_rate"] = (
                    cache_stats.get("hits", 0) / total_requests
                ) * 100
            else:
                current_metrics["cache_hit_rate"] = 0

            # Page load time (average of recent loads)
            page_load_times = st.session_state.get("page_load_times", [])
            if page_load_times:
                recent_loads = page_load_times[-10:]  # Last 10 page loads
                current_metrics["page_load_time"] = sum(recent_loads) / len(
                    recent_loads
                )
            else:
                current_metrics["page_load_time"] = 0

            # Database metrics (if available)
            if "db_query_time" in self.metrics:
                current_metrics["db_query_time"] = self.metrics["db_query_time"].value

            return current_metrics

        except Exception as e:
            logger.error(f"Error getting current metrics: {str(e)}")
            return {}

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0.0

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {}

            # CPU information
            info["cpu"] = {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
            }

            # Memory information
            memory = psutil.virtual_memory()
            info["memory"] = {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "usage_percent": memory.percent,
                "used_gb": memory.used / (1024**3),
            }

            # Disk information
            disk = psutil.disk_usage("/" if os.name != "nt" else "C:")
            info["disk"] = {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "usage_percent": (disk.used / disk.total) * 100,
                "used_gb": disk.used / (1024**3),
            }

            # Network information (if available)
            try:
                network = psutil.net_io_counters()
                info["network"] = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                }
            except:
                info["network"] = None

            return info

        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {}

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance report for specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Filter metrics by time period
            recent_metrics = [
                metric
                for metric in self.performance_history
                if metric.timestamp > cutoff_time
            ]

            if not recent_metrics:
                return {"message": "No metrics available for the specified period"}

            # Analyze metrics
            report = {
                "period": {
                    "start": cutoff_time.isoformat(),
                    "end": datetime.now().isoformat(),
                    "hours": hours,
                },
                "summary": {
                    "total_metrics": len(recent_metrics),
                    "unique_operations": len(set(m.name for m in recent_metrics)),
                },
                "analysis": {},
            }

            # Group metrics by name
            metrics_by_name = {}
            for metric in recent_metrics:
                if metric.name not in metrics_by_name:
                    metrics_by_name[metric.name] = []
                metrics_by_name[metric.name].append(metric)

            # Analyze each metric type
            for name, metrics in metrics_by_name.items():
                values = [m.value for m in metrics]

                analysis = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "unit": metrics[0].unit,
                }

                # Count status occurrences
                statuses = [m.status for m in metrics]
                analysis["status_counts"] = {
                    "normal": statuses.count("normal"),
                    "warning": statuses.count("warning"),
                    "critical": statuses.count("critical"),
                }

                # Calculate trends (if enough data points)
                if len(values) >= 2:
                    recent_avg = sum(values[-5:]) / len(values[-5:])
                    older_avg = (
                        sum(values[:5]) / len(values[:5])
                        if len(values) >= 10
                        else sum(values[:-5]) / len(values[:-5])
                    )

                    if older_avg > 0:
                        trend_percent = ((recent_avg - older_avg) / older_avg) * 100
                        analysis["trend"] = {
                            "direction": (
                                "improving"
                                if trend_percent < -5
                                else "degrading" if trend_percent > 5 else "stable"
                            ),
                            "percentage": trend_percent,
                        }

                report["analysis"][name] = analysis

            return report

        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {"error": str(e)}

    def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization procedures"""
        try:
            optimization_results = {
                "optimizations_performed": [],
                "memory_before": self._get_memory_usage(),
                "cpu_before": self._get_cpu_usage(),
                "timestamp": datetime.now().isoformat(),
            }

            # Garbage collection
            before_objects = len(gc.get_objects())
            collected = gc.collect()
            after_objects = len(gc.get_objects())

            optimization_results["optimizations_performed"].append(
                {
                    "action": "garbage_collection",
                    "objects_before": before_objects,
                    "objects_after": after_objects,
                    "objects_collected": collected,
                }
            )

            # Clear old performance history
            if len(self.performance_history) > 500:
                removed_count = len(self.performance_history) - 500
                self.performance_history = self.performance_history[-500:]

                optimization_results["optimizations_performed"].append(
                    {"action": "clear_old_metrics", "metrics_removed": removed_count}
                )

            # Clear old session state data
            page_load_times = st.session_state.get("page_load_times", [])
            if len(page_load_times) > 50:
                removed_count = len(page_load_times) - 50
                st.session_state.page_load_times = page_load_times[-50:]

                optimization_results["optimizations_performed"].append(
                    {"action": "clear_old_page_loads", "entries_removed": removed_count}
                )

            # Record final metrics
            optimization_results["memory_after"] = self._get_memory_usage()
            optimization_results["cpu_after"] = self._get_cpu_usage()
            optimization_results["memory_saved"] = (
                optimization_results["memory_before"]
                - optimization_results["memory_after"]
            )

            logger.info(
                f"Performance optimization completed: {len(optimization_results['optimizations_performed'])} optimizations"
            )

            return optimization_results

        except Exception as e:
            logger.error(f"Performance optimization failed: {str(e)}")
            return {"error": str(e)}

    def record_page_load(self, page_name: str, load_time: float):
        """Record page load time"""
        try:
            # Add to session state
            if "page_load_times" not in st.session_state:
                st.session_state.page_load_times = []

            st.session_state.page_load_times.append(load_time)

            # Keep only recent loads
            if len(st.session_state.page_load_times) > 100:
                st.session_state.page_load_times = st.session_state.page_load_times[
                    -100:
                ]

            # Record as metric
            self.record_metric(
                f"page_load_{page_name}",
                load_time,
                "seconds",
                self.thresholds.get("page_load_time", 2.0),
            )

        except Exception as e:
            logger.error(f"Error recording page load: {str(e)}")


class CacheManager:
    """Advanced caching system for performance optimization"""

    def __init__(self, max_size_mb: int = 100, default_ttl_minutes: int = 30):
        self.cache = {}
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "total_size": 0}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """Get item from cache"""
        with self._lock:
            if key in self.cache:
                item = self.cache[key]

                # Check if expired
                if item.is_expired():
                    del self.cache[key]
                    self.stats["misses"] += 1
                    self._update_session_stats()
                    return None

                # Update hit count and stats
                item.hit_count += 1
                self.stats["hits"] += 1
                self._update_session_stats()

                return item.data

            self.stats["misses"] += 1
            self._update_session_stats()
            return None

    def set(self, key: str, data: Any, ttl_minutes: Optional[int] = None) -> bool:
        """Set item in cache"""
        try:
            with self._lock:
                # Calculate expiration time
                ttl = (
                    timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
                )
                expires_at = datetime.now() + ttl

                # Estimate data size
                try:
                    import sys

                    size_bytes = sys.getsizeof(data)
                except:
                    size_bytes = 1024  # Default estimate

                # Check if we need to evict items
                self._ensure_space(size_bytes)

                # Create cache item
                item = CacheItem(
                    key=key,
                    data=data,
                    created_at=datetime.now(),
                    expires_at=expires_at,
                    size_bytes=size_bytes,
                )

                # Remove old item if exists
                if key in self.cache:
                    old_item = self.cache[key]
                    self.stats["total_size"] -= old_item.size_bytes

                # Add new item
                self.cache[key] = item
                self.stats["total_size"] += size_bytes

                self._update_session_stats()
                return True

        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self._lock:
            if key in self.cache:
                item = self.cache[key]
                self.stats["total_size"] -= item.size_bytes
                del self.cache[key]
                self._update_session_stats()
                return True
            return False

    def clear(self):
        """Clear all cache items"""
        with self._lock:
            self.cache.clear()
            self.stats["total_size"] = 0
            self._update_session_stats()

    def _ensure_space(self, needed_bytes: int):
        """Ensure enough space for new item"""
        # Check if we need to make space
        if self.stats["total_size"] + needed_bytes > self.max_size_bytes:
            # Sort items by last access time and size
            items_by_priority = sorted(
                self.cache.items(),
                key=lambda x: (x[1].hit_count, -x[1].get_age_seconds()),
            )

            # Remove items until we have enough space
            for key, item in items_by_priority:
                if self.stats["total_size"] + needed_bytes <= self.max_size_bytes:
                    break

                self.stats["total_size"] -= item.size_bytes
                del self.cache[key]
                self.stats["evictions"] += 1

    def _update_session_stats(self):
        """Update session state cache stats"""
        try:
            st.session_state.cache_stats = {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "total_size": self.stats["total_size"],
            }
        except:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (
                (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "hit_rate": hit_rate,
                "total_size_mb": self.stats["total_size"] / (1024 * 1024),
                "item_count": len(self.cache),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
            }

    def cleanup_expired(self) -> int:
        """Clean up expired cache items"""
        with self._lock:
            expired_keys = []

            for key, item in self.cache.items():
                if item.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                item = self.cache[key]
                self.stats["total_size"] -= item.size_bytes
                del self.cache[key]

            return len(expired_keys)


class QueryOptimizer:
    """Database query optimization utilities"""

    def __init__(self):
        self.query_stats = {}
        self.slow_queries = []
        self.optimization_suggestions = []

    def track_query(self, query: str, execution_time: float, result_count: int = 0):
        """Track database query performance"""
        try:
            # Normalize query for tracking
            normalized_query = self._normalize_query(query)

            if normalized_query not in self.query_stats:
                self.query_stats[normalized_query] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float("inf"),
                    "max_time": 0,
                    "avg_time": 0,
                    "last_executed": None,
                }

            stats = self.query_stats[normalized_query]
            stats["count"] += 1
            stats["total_time"] += execution_time
            stats["min_time"] = min(stats["min_time"], execution_time)
            stats["max_time"] = max(stats["max_time"], execution_time)
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["last_executed"] = datetime.now()

            # Track slow queries
            if execution_time > 1.0:  # Queries slower than 1 second
                self.slow_queries.append(
                    {
                        "query": query[:200] + "..." if len(query) > 200 else query,
                        "execution_time": execution_time,
                        "result_count": result_count,
                        "timestamp": datetime.now(),
                    }
                )

                # Keep only recent slow queries
                if len(self.slow_queries) > 50:
                    self.slow_queries = self.slow_queries[-50:]

                # Generate optimization suggestion
                self._suggest_optimization(
                    normalized_query, execution_time, result_count
                )

        except Exception as e:
            logger.error(f"Query tracking error: {str(e)}")

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent tracking"""
        try:
            # Convert to uppercase and remove extra whitespace
            normalized = " ".join(query.upper().split())

            # Replace parameter placeholders with generic placeholder
            import re

            normalized = re.sub(r"\?|\$\d+|:\w+", "?", normalized)

            # Replace string literals with placeholder
            normalized = re.sub(r"'[^']*'", "'?'", normalized)

            # Replace numeric literals with placeholder
            normalized = re.sub(r"\b\d+\b", "?", normalized)

            return normalized

        except:
            return query[:100]  # Fallback

    def _suggest_optimization(
        self, query: str, execution_time: float, result_count: int
    ):
        """Generate optimization suggestions for slow queries"""
        try:
            suggestions = []

            # Check for missing indexes
            if "WHERE" in query and execution_time > 2.0:
                suggestions.append("Consider adding indexes on WHERE clause columns")

            # Check for SELECT *
            if "SELECT *" in query:
                suggestions.append("Avoid SELECT * - specify only needed columns")

            # Check for large result sets
            if result_count > 1000:
                suggestions.append("Consider pagination for large result sets")

            # Check for complex JOINs
            join_count = query.count("JOIN")
            if join_count > 3:
                suggestions.append(
                    "Complex JOINs detected - consider query restructuring"
                )

            # Check for subqueries
            if "SELECT" in query[query.find("SELECT") + 6 :]:
                suggestions.append("Subqueries detected - consider JOINs or EXISTS")

            if suggestions:
                self.optimization_suggestions.append(
                    {
                        "query": query[:100],
                        "execution_time": execution_time,
                        "suggestions": suggestions,
                        "timestamp": datetime.now(),
                    }
                )

                # Keep only recent suggestions
                if len(self.optimization_suggestions) > 20:
                    self.optimization_suggestions = self.optimization_suggestions[-20:]

        except Exception as e:
            logger.error(f"Optimization suggestion error: {str(e)}")

    def get_query_report(self) -> Dict[str, Any]:
        """Get comprehensive query performance report"""
        try:
            # Sort queries by various metrics
            slowest_queries = sorted(
                self.query_stats.items(), key=lambda x: x[1]["max_time"], reverse=True
            )[:10]

            most_frequent = sorted(
                self.query_stats.items(), key=lambda x: x[1]["count"], reverse=True
            )[:10]

            highest_total_time = sorted(
                self.query_stats.items(), key=lambda x: x[1]["total_time"], reverse=True
            )[:10]

            return {
                "summary": {
                    "total_queries": len(self.query_stats),
                    "slow_queries": len(self.slow_queries),
                    "optimization_suggestions": len(self.optimization_suggestions),
                },
                "slowest_queries": [
                    {
                        "query": query[:100],
                        "max_time": stats["max_time"],
                        "avg_time": stats["avg_time"],
                        "count": stats["count"],
                    }
                    for query, stats in slowest_queries
                ],
                "most_frequent": [
                    {
                        "query": query[:100],
                        "count": stats["count"],
                        "avg_time": stats["avg_time"],
                        "total_time": stats["total_time"],
                    }
                    for query, stats in most_frequent
                ],
                "highest_total_time": [
                    {
                        "query": query[:100],
                        "total_time": stats["total_time"],
                        "count": stats["count"],
                        "avg_time": stats["avg_time"],
                    }
                    for query, stats in highest_total_time
                ],
                "recent_slow_queries": self.slow_queries[-10:],
                "optimization_suggestions": self.optimization_suggestions[-10:],
            }

        except Exception as e:
            logger.error(f"Query report error: {str(e)}")
            return {}


# Performance decorators
def monitor_performance(operation_name: str = None):
    """Decorator to monitor function performance"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or func.__name__

            # Get performance monitor
            if "performance_monitor" in st.session_state:
                monitor = st.session_state.performance_monitor
            else:
                monitor = PerformanceMonitor()
                st.session_state.performance_monitor = monitor

            with monitor.measure_time(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_result(ttl_minutes: int = 30, key_func: Callable = None):
    """Decorator to cache function results"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager
            if "cache_manager" not in st.session_state:
                st.session_state.cache_manager = CacheManager()

            cache_manager = st.session_state.cache_manager

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl_minutes)

            return result

        return wrapper

    return decorator


# Global instances
_performance_monitor = None
_cache_manager = None
_query_optimizer = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_query_optimizer() -> QueryOptimizer:
    """Get global query optimizer instance"""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer


def init_performance_monitoring():
    """Initialize performance monitoring system"""
    try:
        # Initialize global instances
        monitor = get_performance_monitor()
        cache = get_cache_manager()
        optimizer = get_query_optimizer()

        # Store in session state if available
        try:
            st.session_state.performance_monitor = monitor
            st.session_state.cache_manager = cache
            st.session_state.query_optimizer = optimizer
        except:
            pass  # Session state might not be available yet

        logger.info("Performance monitoring initialized")

    except Exception as e:
        logger.error(f"Failed to initialize performance monitoring: {str(e)}")


# Auto-initialize when module is imported
init_performance_monitoring()
