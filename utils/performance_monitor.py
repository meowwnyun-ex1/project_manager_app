#!/usr/bin/env python3
"""
utils/performance_monitor.py
Enterprise-grade Performance Monitoring สำหรับ DENSO Project Manager Pro
"""

import streamlit as st
import time
import psutil
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from contextlib import contextmanager
import threading
from dataclasses import dataclass, field
from functools import wraps, lru_cache
import gc
import sys
from collections import deque, defaultdict
import weakref
from concurrent.futures import ThreadPoolExecutor
import statistics
import pickle
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Enhanced performance metric with smart analysis"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None
    status: str = "normal"
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "threshold": self.threshold,
            "status": self.status,
            "category": self.category,
            "metadata": self.metadata,
            "age_seconds": (datetime.now() - self.timestamp).total_seconds(),
        }

    def is_critical(self) -> bool:
        return self.status == "critical"

    def is_expired(self, ttl: int = 300) -> bool:
        return (datetime.now() - self.timestamp).total_seconds() > ttl


@dataclass
class CacheItem:
    """Enterprise cache item with intelligent eviction"""

    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    size_bytes: int = 0
    access_pattern: List[float] = field(default_factory=list)
    priority_score: float = 1.0

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def record_access(self):
        current_time = time.time()
        self.hit_count += 1
        self.access_pattern.append(current_time)

        # Keep last 10 accesses only
        if len(self.access_pattern) > 10:
            self.access_pattern = self.access_pattern[-10:]

        # Update priority score
        if len(self.access_pattern) >= 2:
            time_span = self.access_pattern[-1] - self.access_pattern[0]
            if time_span > 0:
                frequency = len(self.access_pattern) / time_span
                self.priority_score = frequency * self.hit_count

    def calculate_eviction_score(self) -> float:
        """Lower score = higher eviction priority"""
        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        size_mb = self.size_bytes / (1024 * 1024)

        return self.priority_score / (age_hours + size_mb + 1)


class SmartCache:
    """High-performance cache with intelligent management"""

    def __init__(self, max_size_mb: int = 100, default_ttl: int = 300):
        self.cache: Dict[str, CacheItem] = {}
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size": 0,
            "operations": 0,
        }
        self._lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache")

    def get(self, key: str) -> Any:
        """Get item with smart access tracking"""
        with self._lock:
            self.stats["operations"] += 1

            if key in self.cache:
                item = self.cache[key]

                if item.is_expired():
                    self._remove_item(key)
                    self.stats["misses"] += 1
                    return None

                item.record_access()
                self.stats["hits"] += 1
                return item.data

            self.stats["misses"] += 1
            return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Set item with intelligent eviction"""
        try:
            with self._lock:
                ttl = ttl or self.default_ttl

                # Calculate data size
                try:
                    size_bytes = len(pickle.dumps(data))
                except:
                    size_bytes = sys.getsizeof(data)

                # Check if eviction needed
                if self._needs_eviction(size_bytes):
                    self._smart_eviction(size_bytes)

                # Create cache item
                expires_at = datetime.now() + timedelta(seconds=ttl)
                item = CacheItem(
                    key=key,
                    data=data,
                    created_at=datetime.now(),
                    expires_at=expires_at,
                    size_bytes=size_bytes,
                )

                # Remove old item if exists
                if key in self.cache:
                    self._remove_item(key)

                self.cache[key] = item
                self.stats["total_size"] += size_bytes

                return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def _needs_eviction(self, new_size: int) -> bool:
        return (self.stats["total_size"] + new_size) > self.max_size_bytes

    def _smart_eviction(self, needed_space: int):
        """Intelligent LRU + priority-based eviction"""
        if not self.cache:
            return

        # Sort by eviction score (lowest first)
        items_by_score = sorted(
            self.cache.items(), key=lambda x: x[1].calculate_eviction_score()
        )

        freed_space = 0
        evicted_count = 0

        for key, item in items_by_score:
            if freed_space >= needed_space:
                break

            freed_space += item.size_bytes
            self._remove_item(key)
            evicted_count += 1

        self.stats["evictions"] += evicted_count
        logger.debug(
            f"Smart eviction: freed {freed_space} bytes, evicted {evicted_count} items"
        )

    def _remove_item(self, key: str):
        """Remove item and update stats"""
        if key in self.cache:
            self.stats["total_size"] -= self.cache[key].size_bytes
            del self.cache[key]

    def clear_expired(self):
        """Background cleanup of expired items"""

        def cleanup():
            with self._lock:
                expired_keys = [
                    key for key, item in self.cache.items() if item.is_expired()
                ]

                for key in expired_keys:
                    self._remove_item(key)

                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")

        self.executor.submit(cleanup)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_ops = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_ops * 100) if total_ops > 0 else 0

        return {
            "hit_rate": hit_rate,
            "total_items": len(self.cache),
            "total_size_mb": self.stats["total_size"] / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "usage_percent": (self.stats["total_size"] / self.max_size_bytes * 100),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "operations_total": self.stats["operations"],
        }


class AdvancedPerformanceMonitor:
    """Enterprise performance monitoring with predictive analytics"""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.history: deque = deque(maxlen=1000)
        self.trends: Dict[str, List[float]] = defaultdict(lambda: deque(maxlen=50))
        self.start_time = time.time()
        self.monitoring_enabled = True

        # Enhanced thresholds
        self.thresholds = {
            "page_load": {"warning": 1.0, "critical": 3.0},
            "db_query": {"warning": 0.5, "critical": 2.0},
            "memory_usage": {"warning": 70.0, "critical": 90.0},
            "cpu_usage": {"warning": 80.0, "critical": 95.0},
            "cache_hit_rate": {"warning": 60.0, "critical": 40.0},
            "response_time": {"warning": 0.5, "critical": 2.0},
        }

        self.executor = ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="perf-monitor"
        )
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state for performance tracking"""
        if "performance_data" not in st.session_state:
            st.session_state.performance_data = {
                "metrics": {},
                "alerts": [],
                "system_health": "good",
            }

    @contextmanager
    def measure(self, operation: str, category: str = "general"):
        """Context manager for measuring operation performance"""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            duration = time.time() - start_time
            memory_used = self._get_memory_usage() - start_memory

            # Record metric
            self.record_metric(
                name=operation,
                value=duration,
                unit="seconds",
                category=category,
                metadata={"memory_delta": memory_used},
            )

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        category: str = "general",
        metadata: Dict = None,
    ):
        """Record performance metric with trend analysis"""
        if not self.monitoring_enabled:
            return

        # Determine status
        status = self._calculate_status(name, value, category)

        # Create metric
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            threshold=self._get_threshold(name, category),
            status=status,
            category=category,
            metadata=metadata or {},
        )

        # Store and update trends
        self.metrics[name] = metric
        self.history.append(metric)
        self.trends[name].append(value)

        # Update session state
        st.session_state.performance_data["metrics"][name] = metric.to_dict()

        # Generate alerts for critical metrics
        if status == "critical":
            self._generate_alert(metric)

        # Background trend analysis
        if len(self.trends[name]) >= 10:
            self.executor.submit(self._analyze_trend, name)

    def _calculate_status(self, name: str, value: float, category: str) -> str:
        """Calculate metric status based on thresholds"""
        threshold_key = name.replace("_time", "").replace("_usage", "_usage")
        thresholds = self.thresholds.get(threshold_key, {})

        if not thresholds:
            return "normal"

        if value >= thresholds.get("critical", float("inf")):
            return "critical"
        elif value >= thresholds.get("warning", float("inf")):
            return "warning"

        return "normal"

    def _get_threshold(self, name: str, category: str) -> Optional[float]:
        """Get warning threshold for metric"""
        threshold_key = name.replace("_time", "").replace("_usage", "_usage")
        return self.thresholds.get(threshold_key, {}).get("warning")

    def _generate_alert(self, metric: PerformanceMetric):
        """Generate performance alert"""
        alert = {
            "timestamp": metric.timestamp.isoformat(),
            "type": "performance",
            "severity": metric.status,
            "message": f"Critical performance issue: {metric.name} = {metric.value} {metric.unit}",
            "metric": metric.to_dict(),
        }

        # Add to session state alerts
        if "alerts" not in st.session_state.performance_data:
            st.session_state.performance_data["alerts"] = []

        st.session_state.performance_data["alerts"].insert(0, alert)

        # Keep only last 20 alerts
        if len(st.session_state.performance_data["alerts"]) > 20:
            st.session_state.performance_data["alerts"] = (
                st.session_state.performance_data["alerts"][:20]
            )

        logger.warning(f"Performance Alert: {alert['message']}")

    def _analyze_trend(self, metric_name: str):
        """Analyze metric trend for predictions"""
        try:
            values = list(self.trends[metric_name])
            if len(values) < 10:
                return

            # Simple trend analysis
            recent_avg = statistics.mean(values[-5:])
            older_avg = statistics.mean(values[-10:-5])

            if older_avg > 0:
                trend_pct = ((recent_avg - older_avg) / older_avg) * 100

                # Predict if trend continues
                if abs(trend_pct) > 20:  # Significant trend
                    direction = "increasing" if trend_pct > 0 else "decreasing"
                    logger.info(
                        f"Trend detected for {metric_name}: {direction} by {abs(trend_pct):.1f}%"
                    )

        except Exception as e:
            logger.error(f"Trend analysis error for {metric_name}: {e}")

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Disk metrics
            disk = psutil.disk_usage("/")

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024 * 1024)

            # Record metrics
            self.record_metric("memory_usage", memory.percent, "%", "system")
            self.record_metric("cpu_usage", cpu_percent, "%", "system")
            self.record_metric("process_memory", process_memory, "MB", "system")

            return {
                "memory_usage_mb": memory_mb,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "disk_usage_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "process_memory_mb": process_memory,
                "load_average": (
                    os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
                ),
            }

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    def optimize_performance(self) -> Dict[str, Any]:
        """Advanced performance optimization"""
        results = {
            "optimizations": [],
            "before": self._get_performance_snapshot(),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 1. Garbage collection
            before_objects = len(gc.get_objects())
            collected = gc.collect()
            after_objects = len(gc.get_objects())

            if collected > 0:
                results["optimizations"].append(
                    {
                        "type": "garbage_collection",
                        "objects_before": before_objects,
                        "objects_after": after_objects,
                        "objects_collected": collected,
                    }
                )

            # 2. Clear old metrics
            if len(self.history) > 500:
                old_count = len(self.history)
                self.history = deque(list(self.history)[-500:], maxlen=1000)
                results["optimizations"].append(
                    {
                        "type": "metrics_cleanup",
                        "metrics_removed": old_count - len(self.history),
                    }
                )

            # 3. Session state cleanup
            if hasattr(st, "session_state"):
                cleaned = self._cleanup_session_state()
                if cleaned > 0:
                    results["optimizations"].append(
                        {"type": "session_cleanup", "items_removed": cleaned}
                    )

            # 4. Cache optimization
            cache_manager = get_cache_manager()
            if hasattr(cache_manager, "clear_expired"):
                cache_manager.clear_expired()
                results["optimizations"].append(
                    {"type": "cache_cleanup", "status": "completed"}
                )

            results["after"] = self._get_performance_snapshot()

        except Exception as e:
            logger.error(f"Performance optimization error: {e}")
            results["error"] = str(e)

        return results

    def _get_performance_snapshot(self) -> Dict[str, float]:
        """Get current performance snapshot"""
        return {
            "memory_mb": self._get_memory_usage(),
            "cpu_percent": psutil.cpu_percent() if psutil else 0,
            "timestamp": time.time(),
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            return psutil.virtual_memory().used / (1024 * 1024)
        except:
            return 0.0

    def _cleanup_session_state(self) -> int:
        """Clean up old session state data"""
        cleaned = 0
        current_time = time.time()

        try:
            # Clean old temporary data
            keys_to_remove = []
            for key in st.session_state.keys():
                if key.startswith("temp_"):
                    if hasattr(st.session_state[key], "timestamp"):
                        if (
                            current_time - st.session_state[key]["timestamp"] > 600
                        ):  # 10 minutes
                            keys_to_remove.append(key)

            for key in keys_to_remove:
                del st.session_state[key]
                cleaned += 1

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")

        return cleaned

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_minutes": (time.time() - self.start_time) / 60,
            "system_metrics": self.get_system_metrics(),
            "cache_stats": get_cache_manager().get_statistics(),
            "recent_metrics": [m.to_dict() for m in list(self.history)[-10:]],
            "alerts_count": len(st.session_state.performance_data.get("alerts", [])),
            "trends_analysis": self._get_trends_summary(),
            "recommendations": self._generate_recommendations(),
        }

    def _get_trends_summary(self) -> Dict[str, Any]:
        """Get trends summary for all metrics"""
        trends = {}
        for name, values in self.trends.items():
            if len(values) >= 5:
                recent = statistics.mean(list(values)[-3:])
                older = (
                    statistics.mean(list(values)[-6:-3]) if len(values) >= 6 else recent
                )

                trend_direction = "stable"
                if recent > older * 1.1:
                    trend_direction = "increasing"
                elif recent < older * 0.9:
                    trend_direction = "decreasing"

                trends[name] = {
                    "direction": trend_direction,
                    "current_avg": recent,
                    "samples": len(values),
                }

        return trends

    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        # Analyze system metrics
        system_metrics = self.get_system_metrics()

        if system_metrics.get("memory_percent", 0) > 80:
            recommendations.append(
                "💾 High memory usage detected - consider increasing available RAM or optimizing memory-intensive operations"
            )

        if system_metrics.get("cpu_percent", 0) > 80:
            recommendations.append(
                "⚡ High CPU usage detected - review CPU-intensive operations and consider load balancing"
            )

        # Analyze cache performance
        cache_stats = get_cache_manager().get_statistics()
        if cache_stats.get("hit_rate", 100) < 70:
            recommendations.append(
                "🗄️ Low cache hit rate - review caching strategy and TTL settings"
            )

        # Analyze trends
        trends = self._get_trends_summary()
        for metric, trend in trends.items():
            if trend["direction"] == "increasing" and "time" in metric:
                recommendations.append(
                    f"📈 {metric} showing increasing trend - investigate potential performance degradation"
                )

        if not recommendations:
            recommendations.append("✅ System performance is within normal parameters")

        return recommendations


# Performance decorators for enterprise usage
def monitor_performance(operation_name: str, category: str = "general"):
    """Decorator for automatic performance monitoring"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.measure(operation_name, category):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator for intelligent result caching"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
                cache_key = hashlib.md5(str(key_parts).encode()).hexdigest()

            # Try cache first
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


# Global instances
_performance_monitor = None
_cache_manager = None


def get_performance_monitor() -> AdvancedPerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = AdvancedPerformanceMonitor()
    return _performance_monitor


def get_cache_manager() -> SmartCache:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = SmartCache()
    return _cache_manager


def init_performance_system():
    """Initialize performance monitoring system"""
    try:
        monitor = get_performance_monitor()
        cache = get_cache_manager()

        # Store in session state
        if hasattr(st, "session_state"):
            st.session_state.performance_monitor = monitor
            st.session_state.cache_manager = cache

        logger.info("Performance monitoring system initialized")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize performance system: {e}")
        return False


# Auto-initialize when imported
init_performance_system()
