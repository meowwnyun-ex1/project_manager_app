# performance_manager.py
"""
Performance Management and Caching System for DENSO Project Manager
Handles performance monitoring, caching, and optimization
"""

import streamlit as st
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import json
import hashlib
from dataclasses import dataclass, asdict
import threading
import pickle
import os

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


@dataclass
class CacheItem:
    """Cache item data structure"""

    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    size_bytes: int = 0


class PerformanceManager:
    """Performance monitoring and optimization manager"""

    def __init__(self):
        self.metrics = {}
        self.performance_history = []
        self.monitoring_enabled = True
        self.thresholds = {
            "page_load_time": 2.0,  # seconds
            "memory_usage": 512,  # MB
            "db_query_time": 1.0,  # seconds
            "cache_hit_rate": 80.0,  # percentage
        }
        self._start_time = time.time()

    def setup_monitoring(self):
        """Setup performance monitoring"""
        try:
            # Initialize session state for performance tracking
            if "performance_metrics" not in st.session_state:
                st.session_state.performance_metrics = {}

            if "page_load_times" not in st.session_state:
                st.session_state.page_load_times = {}

            logger.info("Performance monitoring initialized")
        except Exception as e:
            logger.error(f"Failed to setup performance monitoring: {str(e)}")

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager to measure operation time"""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            self.record_metric(f"{operation_name}_time", duration, "seconds")

    def record_metric(
        self, name: str, value: float, unit: str, threshold: Optional[float] = None
    ):
        """Record a performance metric"""
        try:
            # Determine status based on threshold
            status = "normal"
            if threshold and value > threshold:
                status = "warning" if value < threshold * 1.5 else "critical"

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

            # Keep only last 1000 metrics in history
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]

            # Log critical metrics
            if status == "critical":
                logger.warning(f"Critical performance metric: {name} = {value} {unit}")

        except Exception as e:
            logger.error(f"Failed to record metric {name}: {str(e)}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            # System metrics
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()

            # Application metrics
            app_metrics = {
                "memory_usage_mb": memory_info.used / (1024 * 1024),
                "memory_percent": memory_info.percent,
                "cpu_percent": cpu_percent,
                "uptime_seconds": time.time() - self._start_time,
            }

            # Page load times from session
            page_load_times = st.session_state.get("page_load_times", {})

            # Combine all metrics
            return {
                "system_metrics": app_metrics,
                "response_times": page_load_times,
                "recorded_metrics": {
                    name: asdict(metric) for name, metric in self.metrics.items()
                },
                "performance_history": [
                    asdict(m) for m in self.performance_history[-50:]
                ],  # Last 50
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {}

    def get_memory_info(self) -> Dict[str, float]:
        """Get detailed memory information"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
                "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
                "used_mb": memory_info.rss / (1024 * 1024),
                "cache_mb": self.get_cache_memory_usage(),
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {str(e)}")
            return {}

    def get_cache_memory_usage(self) -> float:
        """Estimate cache memory usage"""
        try:
            cache_size = 0
            # Estimate session state size
            for key, value in st.session_state.items():
                if isinstance(value, (dict, list)):
                    cache_size += len(str(value).encode("utf-8"))

            return cache_size / (1024 * 1024)  # Convert to MB
        except:
            return 0.0

    def optimize_performance(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []

        try:
            metrics = self.get_performance_metrics()
            system_metrics = metrics.get("system_metrics", {})

            # Memory recommendations
            memory_percent = system_metrics.get("memory_percent", 0)
            if memory_percent > 80:
                recommendations.append(
                    "🔴 High memory usage detected. Consider clearing cache or restarting the application."
                )
            elif memory_percent > 60:
                recommendations.append(
                    "🟡 Moderate memory usage. Monitor performance closely."
                )

            # CPU recommendations
            cpu_percent = system_metrics.get("cpu_percent", 0)
            if cpu_percent > 80:
                recommendations.append(
                    "🔴 High CPU usage detected. Some operations may be slow."
                )

            # Response time recommendations
            response_times = metrics.get("response_times", {})
            slow_pages = [page for page, time in response_times.items() if time > 2.0]
            if slow_pages:
                recommendations.append(
                    f"🟡 Slow page loads detected: {', '.join(slow_pages)}"
                )

            # Cache recommendations
            cache_mb = self.get_cache_memory_usage()
            if cache_mb > 50:
                recommendations.append(
                    "💾 Large cache size detected. Consider clearing old cache entries."
                )

            if not recommendations:
                recommendations.append("✅ Performance looks good!")

            return recommendations
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {str(e)}")
            return ["❌ Unable to analyze performance"]

    def clear_performance_history(self):
        """Clear performance history"""
        self.performance_history.clear()
        self.metrics.clear()
        logger.info("Performance history cleared")


class CacheManager:
    """Advanced caching system for improved performance"""

    def __init__(self, max_size_mb: int = 100, default_ttl: int = 3600):
        self.max_size_mb = max_size_mb
        self.default_ttl = default_ttl
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0, "total_requests": 0}
        self._lock = threading.Lock()

        # Initialize session cache if not exists
        if "app_cache" not in st.session_state:
            st.session_state.app_cache = {}

        logger.info(f"Cache manager initialized with {max_size_mb}MB limit")

    def _generate_cache_key(self, key: str, user_id: Optional[int] = None) -> str:
        """Generate cache key with optional user scoping"""
        if user_id:
            return f"user_{user_id}_{key}"
        return key

    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for caching"""
        try:
            return pickle.dumps(data)
        except Exception:
            # Fallback to JSON for simple data
            return json.dumps(data, default=str).encode("utf-8")

    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize cached data"""
        try:
            return pickle.loads(data)
        except Exception:
            # Fallback from JSON
            return json.loads(data.decode("utf-8"))

    def _calculate_size(self, data: Any) -> int:
        """Calculate size of data in bytes"""
        try:
            if isinstance(data, bytes):
                return len(data)
            return len(self._serialize_data(data))
        except:
            return len(str(data).encode("utf-8"))

    def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = []

        with self._lock:
            for key, item in self.cache.items():
                if current_time > item.expires_at:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]
                self.cache_stats["evictions"] += 1

    def _enforce_size_limit(self):
        """Enforce cache size limit using LRU eviction"""
        max_bytes = self.max_size_mb * 1024 * 1024
        current_size = sum(item.size_bytes for item in self.cache.values())

        if current_size <= max_bytes:
            return

        # Sort by last access time (LRU)
        sorted_items = sorted(
            self.cache.items(), key=lambda x: (x[1].hit_count, x[1].created_at)
        )

        with self._lock:
            while current_size > max_bytes and sorted_items:
                key, item = sorted_items.pop(0)
                current_size -= item.size_bytes
                del self.cache[key]
                self.cache_stats["evictions"] += 1

    def get(self, key: str, user_id: Optional[int] = None) -> Optional[Any]:
        """Get data from cache"""
        cache_key = self._generate_cache_key(key, user_id)

        with self._lock:
            self.cache_stats["total_requests"] += 1

            # Check session cache first (faster)
            session_cache = st.session_state.get("app_cache", {})
            if cache_key in session_cache:
                item_data = session_cache[cache_key]
                if datetime.now() < item_data["expires_at"]:
                    self.cache_stats["hits"] += 1
                    return item_data["data"]
                else:
                    del session_cache[cache_key]

            # Check main cache
            if cache_key in self.cache:
                item = self.cache[cache_key]
                if datetime.now() < item.expires_at:
                    item.hit_count += 1
                    self.cache_stats["hits"] += 1
                    return item.data
                else:
                    del self.cache[cache_key]
                    self.cache_stats["evictions"] += 1

            self.cache_stats["misses"] += 1
            return None

    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
        user_id: Optional[int] = None,
    ):
        """Set data in cache"""
        cache_key = self._generate_cache_key(key, user_id)
        ttl = ttl or self.default_ttl

        try:
            # Calculate size and expiration
            size_bytes = self._calculate_size(data)
            expires_at = datetime.now() + timedelta(seconds=ttl)

            # Create cache item
            cache_item = CacheItem(
                key=cache_key,
                data=data,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=size_bytes,
            )

            with self._lock:
                # Store in main cache
                self.cache[cache_key] = cache_item

                # Store in session cache for quick access (smaller items only)
                if size_bytes < 1024 * 100:  # 100KB limit for session cache
                    session_cache = st.session_state.get("app_cache", {})
                    session_cache[cache_key] = {"data": data, "expires_at": expires_at}
                    st.session_state.app_cache = session_cache

                # Cleanup and enforce limits
                self._cleanup_expired()
                self._enforce_size_limit()

            logger.debug(f"Cached item: {cache_key} ({size_bytes} bytes, TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Failed to cache item {cache_key}: {str(e)}")

    def delete(self, key: str, user_id: Optional[int] = None):
        """Delete item from cache"""
        cache_key = self._generate_cache_key(key, user_id)

        with self._lock:
            # Remove from main cache
            if cache_key in self.cache:
                del self.cache[cache_key]

            # Remove from session cache
            session_cache = st.session_state.get("app_cache", {})
            if cache_key in session_cache:
                del session_cache[cache_key]
                st.session_state.app_cache = session_cache

    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache items matching pattern"""
        with self._lock:
            if pattern:
                # Clear specific pattern
                keys_to_remove = [key for key in self.cache.keys() if pattern in key]
                for key in keys_to_remove:
                    del self.cache[key]

                # Clear from session cache
                session_cache = st.session_state.get("app_cache", {})
                session_keys_to_remove = [
                    key for key in session_cache.keys() if pattern in key
                ]
                for key in session_keys_to_remove:
                    del session_cache[key]
                st.session_state.app_cache = session_cache

                logger.info(
                    f"Cleared {len(keys_to_remove)} cache items matching pattern: {pattern}"
                )
            else:
                # Clear all cache
                self.cache.clear()
                st.session_state.app_cache = {}
                logger.info("Cleared all cache items")

    def clear_user_cache(self, user_id: int):
        """Clear cache for specific user"""
        if user_id:
            self.clear_cache(f"user_{user_id}")

    def clear_all_cache(self):
        """Clear all cache data"""
        with self._lock:
            self.cache.clear()
            st.session_state.app_cache = {}
            self.cache_stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "total_requests": 0,
            }
        logger.info("All cache data cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.cache_stats["total_requests"]
            hit_rate = (
                (self.cache_stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )

            total_size_bytes = sum(item.size_bytes for item in self.cache.values())
            total_size_mb = total_size_bytes / (1024 * 1024)

            session_cache_size = len(st.session_state.get("app_cache", {}))

            return {
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "evictions": self.cache_stats["evictions"],
                "item_count": len(self.cache),
                "total_size_mb": total_size_mb,
                "session_cache_items": session_cache_size,
                "usage_percent": (
                    (total_size_mb / self.max_size_mb * 100)
                    if self.max_size_mb > 0
                    else 0
                ),
            }

    def get_cache_info(self) -> List[Dict[str, Any]]:
        """Get detailed cache information"""
        cache_info = []

        with self._lock:
            for key, item in self.cache.items():
                cache_info.append(
                    {
                        "key": key,
                        "size_bytes": item.size_bytes,
                        "size_mb": item.size_bytes / (1024 * 1024),
                        "created_at": item.created_at.isoformat(),
                        "expires_at": item.expires_at.isoformat(),
                        "hit_count": item.hit_count,
                        "ttl_remaining": (
                            item.expires_at - datetime.now()
                        ).total_seconds(),
                    }
                )

        # Sort by size (largest first)
        cache_info.sort(key=lambda x: x["size_bytes"], reverse=True)
        return cache_info

    def optimize_cache(self) -> List[str]:
        """Optimize cache and return recommendations"""
        recommendations = []

        try:
            stats = self.get_cache_stats()

            # Hit rate recommendations
            if stats["hit_rate"] < 50:
                recommendations.append(
                    "🔴 Low cache hit rate. Consider increasing TTL for frequently accessed data."
                )
            elif stats["hit_rate"] < 70:
                recommendations.append(
                    "🟡 Moderate cache hit rate. Review caching strategy."
                )

            # Size recommendations
            if stats["usage_percent"] > 90:
                recommendations.append(
                    "🔴 Cache nearly full. Consider increasing cache size or reducing TTL."
                )
            elif stats["usage_percent"] > 70:
                recommendations.append(
                    "🟡 Cache usage high. Monitor for performance impact."
                )

            # Eviction recommendations
            if stats["evictions"] > stats["hits"] * 0.1:
                recommendations.append(
                    "🟡 High eviction rate. Consider increasing cache size."
                )

            if not recommendations:
                recommendations.append("✅ Cache performance is optimal!")

            return recommendations
        except Exception as e:
            logger.error(f"Failed to optimize cache: {str(e)}")
            return ["❌ Unable to analyze cache performance"]


class DatabaseOptimizer:
    """Database query optimization and monitoring"""

    def __init__(self, db_service):
        self.db_service = db_service
        self.query_stats = {}

    def measure_query_performance(
        self, query_name: str, query: str, params: tuple = None
    ):
        """Measure and record database query performance"""
        start_time = time.time()

        try:
            if params:
                result = self.db_service.connection_manager.execute_query(query, params)
            else:
                result = self.db_service.connection_manager.execute_query(query)

            execution_time = time.time() - start_time

            # Record query stats
            if query_name not in self.query_stats:
                self.query_stats[query_name] = {
                    "total_executions": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "min_time": float("inf"),
                }

            stats = self.query_stats[query_name]
            stats["total_executions"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["total_executions"]
            stats["max_time"] = max(stats["max_time"], execution_time)
            stats["min_time"] = min(stats["min_time"], execution_time)

            # Log slow queries
            if execution_time > 1.0:  # 1 second threshold
                logger.warning(
                    f"Slow query detected: {query_name} took {execution_time:.2f}s"
                )

            return result

        except Exception as e:
            logger.error(f"Query {query_name} failed: {str(e)}")
            raise

    def get_query_stats(self) -> Dict[str, Any]:
        """Get database query statistics"""
        return self.query_stats

    def optimize_queries(self) -> List[str]:
        """Generate query optimization recommendations"""
        recommendations = []

        for query_name, stats in self.query_stats.items():
            if stats["avg_time"] > 0.5:  # 500ms threshold
                recommendations.append(
                    f"🔴 Slow query: {query_name} (avg: {stats['avg_time']:.2f}s). Consider adding indexes or optimizing."
                )
            elif stats["avg_time"] > 0.2:  # 200ms threshold
                recommendations.append(
                    f"🟡 Query may benefit from optimization: {query_name} (avg: {stats['avg_time']:.2f}s)"
                )

        if not recommendations:
            recommendations.append("✅ Database queries are performing well!")

        return recommendations


# Global instances
performance_manager = None
cache_manager = None
db_optimizer = None


def get_performance_manager() -> PerformanceManager:
    """Get or create performance manager instance"""
    global performance_manager
    if performance_manager is None:
        performance_manager = PerformanceManager()
    return performance_manager


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance"""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager()
    return cache_manager


def get_db_optimizer(db_service) -> DatabaseOptimizer:
    """Get or create database optimizer instance"""
    global db_optimizer
    if db_optimizer is None:
        db_optimizer = DatabaseOptimizer(db_service)
    return db_optimizer
