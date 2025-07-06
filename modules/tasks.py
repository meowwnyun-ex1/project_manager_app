#!/usr/bin/env python3
"""
modules/tasks.py
SDX Project Manager - Complete Enterprise Task Management System
Full-featured task tracking with Kanban, dependencies, time tracking, and comprehensive analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration with workflow support"""

    BACKLOG = "Backlog"
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    TESTING = "Testing"
    DONE = "Done"
    BLOCKED = "Blocked"
    CANCELLED = "Cancelled"


class TaskPriority(Enum):
    """Task priority levels with numeric values for sorting"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TaskType(Enum):
    """Task type classification for better organization"""

    FEATURE = "Feature"
    BUG = "Bug"
    IMPROVEMENT = "Improvement"
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    SUBTASK = "Subtask"
    SPIKE = "Spike"


class WorkType(Enum):
    """Work type for time tracking"""

    DEVELOPMENT = "Development"
    TESTING = "Testing"
    DESIGN = "Design"
    DOCUMENTATION = "Documentation"
    REVIEW = "Review"
    MEETING = "Meeting"
    RESEARCH = "Research"
    DEPLOYMENT = "Deployment"


@dataclass
class TaskMetrics:
    """Comprehensive task performance metrics"""

    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    blocked_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0
    average_completion_time: float = 0.0
    total_estimated_hours: float = 0.0
    total_actual_hours: float = 0.0
    efficiency_ratio: float = 0.0
    velocity_points: int = 0
    burndown_remaining: float = 0.0


@dataclass
class TaskDependency:
    """Task dependency with relationship details"""

    task_id: int
    depends_on_task_id: int
    dependency_type: str
    lag_days: int = 0
    is_hard_dependency: bool = True
    created_at: datetime = None
    created_by: int = None


@dataclass
class TimeEntry:
    """Time tracking entry with comprehensive details"""

    task_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    description: str
    work_type: str
    billable: bool = True
    date_logged: datetime = None


class TaskManager:
    """Complete enterprise task management system with full CRUD and analytics"""

    def __init__(self, db_manager):
        self.db = db_manager
        self.priority_weights = {
            TaskPriority.CRITICAL.value: 4,
            TaskPriority.HIGH.value: 3,
            TaskPriority.MEDIUM.value: 2,
            TaskPriority.LOW.value: 1,
        }
        self._initialize_complete_schema()

    def _initialize_complete_schema(self):
        """Initialize complete database schema for task management"""
        try:
            # Enhanced tasks table with all enterprise features
            tasks_table = """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                task_type VARCHAR(50) DEFAULT 'Task',
                status VARCHAR(50) NOT NULL DEFAULT 'Backlog',
                priority VARCHAR(20) NOT NULL DEFAULT 'Medium',
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                assignee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                reporter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                
                -- Time tracking
                estimated_hours DECIMAL(8,2),
                actual_hours DECIMAL(8,2) DEFAULT 0,
                remaining_hours DECIMAL(8,2),
                
                -- Dates
                start_date DATE,
                due_date DATE,
                completed_date DATE,
                
                -- Agile fields
                story_points INTEGER,
                sprint_id INTEGER,
                epic_id INTEGER,
                
                -- Classification
                component VARCHAR(255),
                fix_version VARCHAR(100),
                affects_version VARCHAR(100),
                resolution VARCHAR(100),
                environment VARCHAR(100),
                
                -- Metadata
                tags TEXT,
                labels JSONB DEFAULT '[]',
                custom_fields JSONB DEFAULT '{}',
                
                -- Progress tracking
                progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
                
                -- External references
                external_id VARCHAR(255),
                external_url TEXT,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                CONSTRAINT valid_dates CHECK (
                    (start_date IS NULL OR due_date IS NULL OR start_date <= due_date) AND
                    (completed_date IS NULL OR created_at::date <= completed_date)
                )
            )
            """

            # Task dependencies with advanced relationship management
            dependencies_table = """
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                depends_on_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                dependency_type VARCHAR(50) DEFAULT 'finish_to_start',
                lag_days INTEGER DEFAULT 0,
                lead_days INTEGER DEFAULT 0,
                is_hard_dependency BOOLEAN DEFAULT TRUE,
                percentage_complete_required INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                notes TEXT,
                UNIQUE(task_id, depends_on_task_id),
                CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id)
            )
            """

            # Enhanced comments with rich features
            comments_table = """
            CREATE TABLE IF NOT EXISTS task_comments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                parent_comment_id INTEGER REFERENCES task_comments(id) ON DELETE CASCADE,
                comment_text TEXT NOT NULL,
                comment_type VARCHAR(50) DEFAULT 'comment',
                is_internal BOOLEAN DEFAULT FALSE,
                is_edited BOOLEAN DEFAULT FALSE,
                mentions JSONB DEFAULT '[]',
                attachments JSONB DEFAULT '[]',
                reactions JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                edited_at TIMESTAMP,
                edited_by INTEGER REFERENCES users(id) ON DELETE SET NULL
            )
            """

            # Comprehensive time tracking
            time_logs_table = """
            CREATE TABLE IF NOT EXISTS task_time_logs (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_minutes INTEGER,
                description TEXT,
                work_type VARCHAR(50) DEFAULT 'Development',
                billable BOOLEAN DEFAULT TRUE,
                hourly_rate DECIMAL(10,2),
                date_logged DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Timer support
                is_timer_entry BOOLEAN DEFAULT FALSE,
                timer_started_at TIMESTAMP,
                
                -- Location tracking (optional)
                location VARCHAR(255),
                ip_address INET,
                
                CONSTRAINT valid_time_entry CHECK (
                    (end_time IS NULL OR start_time <= end_time) AND
                    (duration_minutes IS NULL OR duration_minutes >= 0) AND
                    (end_time IS NOT NULL OR duration_minutes IS NOT NULL)
                )
            )
            """

            # File attachments with versioning
            attachments_table = """
            CREATE TABLE IF NOT EXISTS task_attachments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                filename VARCHAR(500) NOT NULL,
                original_filename VARCHAR(500) NOT NULL,
                file_path TEXT NOT NULL,
                file_size BIGINT,
                mime_type VARCHAR(150),
                file_hash VARCHAR(64),
                thumbnail_path TEXT,
                version INTEGER DEFAULT 1,
                uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                
                -- Access control
                is_public BOOLEAN DEFAULT TRUE,
                access_level VARCHAR(50) DEFAULT 'team',
                
                -- Metadata
                description TEXT,
                tags JSONB DEFAULT '[]'
            )
            """

            # Task watchers/subscribers with preferences
            watchers_table = """
            CREATE TABLE IF NOT EXISTS task_watchers (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                notification_preferences JSONB DEFAULT '{"email": true, "slack": false, "mobile": false}',
                watch_type VARCHAR(50) DEFAULT 'all',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_id, user_id)
            )
            """

            # Comprehensive audit trail
            history_table = """
            CREATE TABLE IF NOT EXISTS task_history (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action VARCHAR(100) NOT NULL,
                field_name VARCHAR(100),
                old_value TEXT,
                new_value TEXT,
                change_summary TEXT,
                change_reason TEXT,
                automated BOOLEAN DEFAULT FALSE,
                ip_address INET,
                user_agent TEXT,
                session_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Batch change tracking
                batch_id UUID,
                change_set_id INTEGER
            )
            """

            # Workflow transitions configuration
            workflow_table = """
            CREATE TABLE IF NOT EXISTS task_workflow_transitions (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                from_status VARCHAR(50),
                to_status VARCHAR(50) NOT NULL,
                transition_name VARCHAR(100) NOT NULL,
                conditions JSONB DEFAULT '{}',
                required_fields JSONB DEFAULT '[]',
                auto_assign_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
                notification_template VARCHAR(100),
                post_transition_actions JSONB DEFAULT '[]',
                is_active BOOLEAN DEFAULT TRUE,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            # Task labels for categorization
            labels_table = """
            CREATE TABLE IF NOT EXISTS task_labels (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                color VARCHAR(7) DEFAULT '#0066CC',
                description TEXT,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                is_global BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, project_id)
            )
            """

            # Task-Label relationship
            task_labels_table = """
            CREATE TABLE IF NOT EXISTS task_label_assignments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                label_id INTEGER REFERENCES task_labels(id) ON DELETE CASCADE,
                assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_id, label_id)
            )
            """

            # Execute all table creations
            tables = [
                tasks_table,
                dependencies_table,
                comments_table,
                time_logs_table,
                attachments_table,
                watchers_table,
                history_table,
                workflow_table,
                labels_table,
                task_labels_table,
            ]

            for table_sql in tables:
                self.db.execute_query(table_sql)

            # Create comprehensive indexes for performance
            self._create_performance_indexes()

            # Initialize default workflow and labels
            self._initialize_default_workflow()
            self._initialize_default_labels()

        except Exception as e:
            logger.error(f"Error initializing task schema: {e}")
            raise

    def _create_performance_indexes(self):
        """Create comprehensive indexes for optimal performance"""
        indexes = [
            # Core task indexes
            "CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_assignee_status ON tasks(assignee_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_due_date_status ON tasks(due_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_task_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_sprint ON tasks(sprint_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_epic ON tasks(epic_id)",
            # Full-text search indexes
            "CREATE INDEX IF NOT EXISTS idx_tasks_title_gin ON tasks USING gin(to_tsvector('english', title))",
            "CREATE INDEX IF NOT EXISTS idx_tasks_description_gin ON tasks USING gin(to_tsvector('english', description))",
            # JSON field indexes
            "CREATE INDEX IF NOT EXISTS idx_tasks_labels_gin ON tasks USING gin(labels)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_custom_fields_gin ON tasks USING gin(custom_fields)",
            # Dependency indexes
            "CREATE INDEX IF NOT EXISTS idx_dependencies_task_id ON task_dependencies(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_dependencies_depends_on ON task_dependencies(depends_on_task_id)",
            "CREATE INDEX IF NOT EXISTS idx_dependencies_type ON task_dependencies(dependency_type)",
            # Time tracking indexes
            "CREATE INDEX IF NOT EXISTS idx_time_logs_task_user ON task_time_logs(task_id, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_time_logs_date ON task_time_logs(date_logged)",
            "CREATE INDEX IF NOT EXISTS idx_time_logs_billable ON task_time_logs(billable)",
            # Comment indexes
            "CREATE INDEX IF NOT EXISTS idx_comments_task_created ON task_comments(task_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_comments_user ON task_comments(user_id)",
            # History indexes
            "CREATE INDEX IF NOT EXISTS idx_history_task_action ON task_history(task_id, action)",
            "CREATE INDEX IF NOT EXISTS idx_history_created ON task_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_history_user ON task_history(user_id)",
            # Attachment indexes
            "CREATE INDEX IF NOT EXISTS idx_attachments_task ON task_attachments(task_id) WHERE is_deleted = FALSE",
            "CREATE INDEX IF NOT EXISTS idx_attachments_hash ON task_attachments(file_hash)",
            # Watcher indexes
            "CREATE INDEX IF NOT EXISTS idx_watchers_user ON task_watchers(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_watchers_task ON task_watchers(task_id)",
            # Label indexes
            "CREATE INDEX IF NOT EXISTS idx_label_assignments_task ON task_label_assignments(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_label_assignments_label ON task_label_assignments(label_id)",
        ]

        for index_sql in indexes:
            try:
                self.db.execute_query(index_sql)
            except Exception as e:
                logger.warning(f"Could not create index: {e}")

    def _initialize_default_workflow(self):
        """Initialize default workflow transitions"""
        try:
            # Check if workflow already exists
            check_query = "SELECT COUNT(*) FROM task_workflow_transitions"
            result = self.db.fetch_one(check_query)

            if result and result[0] > 0:
                return

            # Default workflow transitions
            transitions = [
                (None, "Backlog", "To Do", "Plan Task", 1),
                ("Backlog", "To Do", "Start Planning", 2),
                ("Backlog", "Cancelled", "Cancel Task", 99),
                ("To Do", "In Progress", "Start Work", 3),
                ("To Do", "Blocked", "Block Task", 98),
                ("In Progress", "Review", "Submit for Review", 4),
                ("In Progress", "Blocked", "Block Task", 97),
                ("In Progress", "To Do", "Return to Backlog", 96),
                ("Review", "Testing", "Approve for Testing", 5),
                ("Review", "In Progress", "Request Changes", 95),
                ("Testing", "Done", "Mark Complete", 6),
                ("Testing", "In Progress", "Reopen for Fixes", 94),
                ("Blocked", "To Do", "Unblock Task", 7),
                ("Blocked", "In Progress", "Resume Work", 8),
                ("Done", "Testing", "Reopen for Testing", 93),
                (None, "Cancelled", "Cancel Task", 100),
            ]

            query = """
            INSERT INTO task_workflow_transitions 
            (from_status, to_status, transition_name, display_order)
            VALUES (%s, %s, %s, %s)
            """

            for from_status, to_status, name, order in transitions:
                self.db.execute_query(query, (from_status, to_status, name, order))

        except Exception as e:
            logger.error(f"Error initializing workflow: {e}")

    def _initialize_default_labels(self):
        """Initialize default task labels"""
        try:
            default_labels = [
                ("bug", "#FF5722", "Bug fixes and error corrections"),
                ("feature", "#4CAF50", "New feature development"),
                ("enhancement", "#2196F3", "Improvements to existing features"),
                ("documentation", "#9C27B0", "Documentation updates"),
                ("urgent", "#FF9800", "Urgent priority tasks"),
                ("blocked", "#795548", "Tasks that are blocked"),
                ("review", "#607D8B", "Tasks under review"),
                ("testing", "#00BCD4", "Testing related tasks"),
            ]

            query = """
            INSERT INTO task_labels (name, color, description, is_global)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (name, project_id) DO NOTHING
            """

            for name, color, description in default_labels:
                self.db.execute_query(query, (name, color, description))

        except Exception as e:
            logger.error(f"Error initializing labels: {e}")

    # Core CRUD Operations
    def create_task(
        self, task_data: Dict[str, Any], user_id: int = None
    ) -> Optional[int]:
        """Create new task with comprehensive validation and audit"""
        try:
            # Validate required fields
            if not task_data.get("title"):
                raise ValueError("Task title is required")

            # Set defaults
            task_data.setdefault("task_type", TaskType.TASK.value)
            task_data.setdefault("status", TaskStatus.BACKLOG.value)
            task_data.setdefault("priority", TaskPriority.MEDIUM.value)
            task_data.setdefault("reporter_id", user_id)

            # Validate parent task
            if task_data.get("parent_task_id"):
                if not self._validate_parent_task(
                    task_data["parent_task_id"], task_data.get("project_id")
                ):
                    raise ValueError("Invalid parent task")

            # Calculate remaining hours
            estimated = task_data.get("estimated_hours")
            if estimated:
                task_data["remaining_hours"] = estimated

            query = """
            INSERT INTO tasks (
                title, description, task_type, status, priority, project_id,
                assignee_id, reporter_id, parent_task_id, estimated_hours, remaining_hours,
                start_date, due_date, story_points, sprint_id, epic_id, component,
                environment, tags, labels, custom_fields, external_id, external_url
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """

            values = (
                task_data["title"],
                task_data.get("description"),
                task_data["task_type"],
                task_data["status"],
                task_data["priority"],
                task_data["project_id"],
                task_data.get("assignee_id"),
                task_data["reporter_id"],
                task_data.get("parent_task_id"),
                task_data.get("estimated_hours"),
                task_data.get("remaining_hours"),
                task_data.get("start_date"),
                task_data.get("due_date"),
                task_data.get("story_points"),
                task_data.get("sprint_id"),
                task_data.get("epic_id"),
                task_data.get("component"),
                task_data.get("environment"),
                task_data.get("tags"),
                json.dumps(task_data.get("labels", [])),
                json.dumps(task_data.get("custom_fields", {})),
                task_data.get("external_id"),
                task_data.get("external_url"),
            )

            result = self.db.fetch_one(query, values)
            task_id = result[0] if result else None

            if task_id:
                # Create audit log
                self._log_task_history(
                    task_id,
                    user_id,
                    "created",
                    change_summary=f"Task '{task_data['title']}' created",
                )

                # Add watchers
                self._add_default_watchers(
                    task_id, user_id, task_data.get("assignee_id")
                )

                # Process labels
                if task_data.get("labels"):
                    self._assign_labels(task_id, task_data["labels"], user_id)

            return task_id

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None

    def get_task(
        self, task_id: int, include_relations: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get complete task with all related information"""
        try:
            query = """
            SELECT t.*,
                   p.name as project_name,
                   u1.username as assignee_username, u1.display_name as assignee_display_name,
                   u2.username as reporter_username, u2.display_name as reporter_display_name,
                   pt.title as parent_task_title,
                   (SELECT COUNT(*) FROM tasks WHERE parent_task_id = t.id) as subtask_count,
                   (SELECT COUNT(*) FROM task_comments WHERE task_id = t.id) as comment_count,
                   (SELECT SUM(duration_minutes) FROM task_time_logs WHERE task_id = t.id) as total_logged_minutes
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN users u1 ON t.assignee_id = u1.id
            LEFT JOIN users u2 ON t.reporter_id = u2.id
            LEFT JOIN tasks pt ON t.parent_task_id = pt.id
            WHERE t.id = %s
            """

            result = self.db.fetch_one(query, (task_id,))
            if not result:
                return None

            # Map basic task data
            task = self._map_task_result_extended(result)

            if include_relations:
                # Get all related data
                task.update(
                    {
                        "dependencies": self.get_task_dependencies(task_id),
                        "dependent_tasks": self.get_dependent_tasks(task_id),
                        "comments": self.get_task_comments(task_id, limit=50),
                        "time_logs": self.get_task_time_logs(task_id, limit=20),
                        "attachments": self.get_task_attachments(task_id),
                        "watchers": self.get_task_watchers(task_id),
                        "subtasks": self.get_subtasks(task_id),
                        "history": self.get_task_history(task_id, limit=20),
                        "assigned_labels": self.get_task_assigned_labels(task_id),
                    }
                )

            return task

        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None

    def update_task(
        self, task_id: int, task_data: Dict[str, Any], user_id: int = None
    ) -> bool:
        """Update task with comprehensive change tracking"""
        try:
            current_task = self.get_task(task_id, include_relations=False)
            if not current_task:
                return False

            update_fields = []
            values = []
            changes = []

            # Define updatable fields with validation
            updatable_fields = {
                "title": self._validate_title,
                "description": lambda x: True,
                "task_type": lambda x: x in [t.value for t in TaskType],
                "status": self._validate_status_transition,
                "priority": lambda x: x in [p.value for p in TaskPriority],
                "assignee_id": self._validate_user_exists,
                "parent_task_id": lambda x: self._validate_parent_task(
                    x, current_task["project_id"]
                ),
                "estimated_hours": lambda x: x is None
                or (isinstance(x, (int, float)) and x >= 0),
                "remaining_hours": lambda x: x is None
                or (isinstance(x, (int, float)) and x >= 0),
                "start_date": lambda x: True,
                "due_date": lambda x: True,
                "story_points": lambda x: x is None or (isinstance(x, int) and x >= 0),
                "sprint_id": lambda x: True,
                "epic_id": lambda x: True,
                "component": lambda x: True,
                "environment": lambda x: True,
                "tags": lambda x: True,
                "progress_percentage": lambda x: x is None or (0 <= x <= 100),
                "external_id": lambda x: True,
                "external_url": lambda x: True,
            }

            # Process each field
            for field, validator in updatable_fields.items():
                if field in task_data:
                    new_value = task_data[field]
                    old_value = current_task.get(field)

                    # Special validation for status changes
                    if field == "status" and new_value != old_value:
                        if not self._is_valid_status_transition(old_value, new_value):
                            raise ValueError(
                                f"Invalid status transition: {old_value} -> {new_value}"
                            )

                    # Validate the new value
                    if not validator(new_value):
                        raise ValueError(f"Invalid value for {field}: {new_value}")

                    if new_value != old_value:
                        update_fields.append(f"{field} = %s")
                        values.append(new_value)
                        changes.append(
                            {
                                "field": field,
                                "old_value": old_value,
                                "new_value": new_value,
                            }
                        )

            # Handle JSON fields
            json_fields = ["labels", "custom_fields"]
            for field in json_fields:
                if field in task_data:
                    new_value = task_data[field]
                    old_value = current_task.get(field, [] if field == "labels" else {})

                    if new_value != old_value:
                        update_fields.append(f"{field} = %s")
                        values.append(json.dumps(new_value))
                        changes.append(
                            {
                                "field": field,
                                "old_value": old_value,
                                "new_value": new_value,
                            }
                        )

            if not update_fields:
                return True  # No changes

            # Handle special status-based logic
            status_change = next((c for c in changes if c["field"] == "status"), None)
            if status_change:
                new_status = status_change["new_value"]
                if new_status == TaskStatus.DONE.value:
                    update_fields.append("completed_date = %s")
                    update_fields.append("progress_percentage = %s")
                    values.extend([datetime.now().date(), 100])
                elif (
                    new_status == TaskStatus.IN_PROGRESS.value
                    and not current_task.get("start_date")
                ):
                    update_fields.append("start_date = %s")
                    values.append(datetime.now().date())

            # Always update timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(task_id)

            # Execute update
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %s"
            affected_rows = self.db.execute_query(query, values)

            if affected_rows > 0:
                # Log all changes
                for change in changes:
                    self._log_task_history(
                        task_id,
                        user_id,
                        "field_updated",
                        field_name=change["field"],
                        old_value=(
                            str(change["old_value"])
                            if change["old_value"] is not None
                            else None
                        ),
                        new_value=(
                            str(change["new_value"])
                            if change["new_value"] is not None
                            else None
                        ),
                    )

                # Update calculated fields
                self._update_calculated_fields(task_id)

                return True

            return False

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False

    def delete_task(
        self, task_id: int, user_id: int = None, force: bool = False
    ) -> bool:
        """Delete task with validation and cleanup"""
        try:
            task = self.get_task(task_id, include_relations=False)
            if not task:
                return False

            # Check for dependencies
            if not force:
                subtask_count = self.db.fetch_one(
                    "SELECT COUNT(*) FROM tasks WHERE parent_task_id = %s", (task_id,)
                )[0]

                if subtask_count > 0:
                    raise ValueError(
                        f"Cannot delete task: has {subtask_count} subtasks. Use force=True to override."
                    )

                dependent_count = self.db.fetch_one(
                    "SELECT COUNT(*) FROM task_dependencies WHERE depends_on_task_id = %s",
                    (task_id,),
                )[0]

                if dependent_count > 0:
                    raise ValueError(
                        f"Cannot delete task: {dependent_count} tasks depend on it. Use force=True to override."
                    )

            # Log deletion before actual deletion
            self._log_task_history(
                task_id,
                user_id,
                "deleted",
                change_summary=f"Task '{task['title']}' deleted",
            )

            # Soft delete approach - mark as deleted instead of hard delete
            query = """
            UPDATE tasks 
            SET status = 'Cancelled', 
                updated_at = CURRENT_TIMESTAMP,
                custom_fields = custom_fields || '{"deleted": true, "deleted_at": "%s", "deleted_by": %s}'::jsonb
            WHERE id = %s
            """

            affected_rows = self.db.execute_query(
                query, (datetime.now().isoformat(), user_id, task_id)
            )

            return affected_rows > 0

        except Exception as e:
            logger.error(f"Error updating actual hours for task {task_id}: {e}")

    def _update_calculated_fields(self, task_id: int):
        """Update calculated fields like progress, remaining hours, etc."""
        try:
            # Update actual hours from time logs
            self._update_task_actual_hours(task_id)

            # Update remaining hours based on actual vs estimated
            query = """
            UPDATE tasks 
            SET remaining_hours = GREATEST(0, COALESCE(estimated_hours, 0) - COALESCE(actual_hours, 0))
            WHERE id = %s AND remaining_hours IS NOT NULL
            """
            self.db.execute_query(query, (task_id,))

        except Exception as e:
            logger.error(f"Error updating calculated fields for task {task_id}: {e}")

    def _add_default_watchers(
        self, task_id: int, creator_id: int, assignee_id: int = None
    ):
        """Add default watchers to a task"""
        try:
            # Add creator as watcher
            if creator_id:
                self.add_task_watcher(task_id, creator_id)

            # Add assignee as watcher if different from creator
            if assignee_id and assignee_id != creator_id:
                self.add_task_watcher(task_id, assignee_id)

        except Exception as e:
            logger.error(f"Error adding default watchers: {e}")

    def _get_time_logged_today(self, task_id: int) -> int:
        """Get minutes logged today for a task"""
        try:
            query = """
            SELECT COALESCE(SUM(duration_minutes), 0)
            FROM task_time_logs 
            WHERE task_id = %s AND date_logged = CURRENT_DATE
            """
            result = self.db.fetch_one(query, (task_id,))
            return result[0] if result else 0
        except:
            return 0

    def _assign_labels(self, task_id: int, label_names: List[str], user_id: int = None):
        """Assign labels to a task"""
        try:
            for label_name in label_names:
                # Get or create label
                label_query = """
                INSERT INTO task_labels (name, is_global) 
                VALUES (%s, TRUE) 
                ON CONFLICT (name, project_id) DO NOTHING
                RETURNING id
                """
                label_result = self.db.fetch_one(label_query, (label_name,))

                if not label_result:
                    # Get existing label
                    label_result = self.db.fetch_one(
                        "SELECT id FROM task_labels WHERE name = %s AND is_global = TRUE",
                        (label_name,),
                    )

                if label_result:
                    label_id = label_result[0]
                    # Assign label to task
                    assign_query = """
                    INSERT INTO task_label_assignments (task_id, label_id, assigned_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (task_id, label_id) DO NOTHING
                    """
                    self.db.execute_query(assign_query, (task_id, label_id, user_id))

        except Exception as e:
            logger.error(f"Error assigning labels: {e}")

    def _notify_mentioned_users(
        self, task_id: int, comment_id: int, mentioned_users: List[int]
    ):
        """Notify users mentioned in comments"""
        try:
            # Add mentioned users as watchers
            for user_id in mentioned_users:
                self.add_task_watcher(task_id, user_id)

            # Here you would integrate with notification system
            # For now, just log the mention
            logger.info(
                f"Users {mentioned_users} mentioned in task {task_id} comment {comment_id}"
            )

        except Exception as e:
            logger.error(f"Error notifying mentioned users: {e}")

    # Additional Methods for Complete Enterprise Functionality
    def get_subtasks(self, parent_task_id: int) -> List[Dict[str, Any]]:
        """Get all subtasks of a parent task"""
        try:
            query = """
            SELECT t.*, u.username as assignee_username, u.display_name as assignee_display_name
            FROM tasks t
            LEFT JOIN users u ON t.assignee_id = u.id
            WHERE t.parent_task_id = %s
            ORDER BY t.created_at
            """

            results = self.db.fetch_all(query, (parent_task_id,))

            subtasks = []
            for result in results:
                subtasks.append(self._map_task_result_extended(result))

            return subtasks

        except Exception as e:
            logger.error(f"Error getting subtasks for {parent_task_id}: {e}")
            return []

    def get_task_history(self, task_id: int, limit: int = None) -> List[Dict[str, Any]]:
        """Get complete task change history"""
        try:
            query = """
            SELECT th.*, u.username, u.display_name
            FROM task_history th
            LEFT JOIN users u ON th.user_id = u.id
            WHERE th.task_id = %s
            ORDER BY th.created_at DESC
            """

            params = [task_id]
            if limit:
                query += " LIMIT %s"
                params.append(limit)

            results = self.db.fetch_all(query, params)

            history = []
            for result in results:
                history.append(
                    {
                        "id": result[0],
                        "task_id": result[1],
                        "user_id": result[2],
                        "action": result[3],
                        "field_name": result[4],
                        "old_value": result[5],
                        "new_value": result[6],
                        "change_summary": result[7],
                        "change_reason": result[8],
                        "automated": result[9],
                        "ip_address": result[10],
                        "user_agent": result[11],
                        "session_id": result[12],
                        "created_at": result[13],
                        "batch_id": result[14],
                        "change_set_id": result[15],
                        "username": result[16],
                        "display_name": result[17],
                    }
                )

            return history

        except Exception as e:
            logger.error(f"Error getting history for task {task_id}: {e}")
            return []

    def get_task_attachments(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all task attachments"""
        try:
            query = """
            SELECT ta.*, u.username, u.display_name
            FROM task_attachments ta
            JOIN users u ON ta.uploaded_by = u.id
            WHERE ta.task_id = %s AND ta.is_deleted = FALSE
            ORDER BY ta.uploaded_at DESC
            """

            results = self.db.fetch_all(query, (task_id,))

            attachments = []
            for result in results:
                attachments.append(
                    {
                        "id": result[0],
                        "task_id": result[1],
                        "filename": result[2],
                        "original_filename": result[3],
                        "file_path": result[4],
                        "file_size": result[5],
                        "mime_type": result[6],
                        "file_hash": result[7],
                        "thumbnail_path": result[8],
                        "version": result[9],
                        "uploaded_by": result[10],
                        "uploaded_at": result[11],
                        "is_deleted": result[12],
                        "deleted_at": result[13],
                        "deleted_by": result[14],
                        "is_public": result[15],
                        "access_level": result[16],
                        "description": result[17],
                        "tags": json.loads(result[18]) if result[18] else [],
                        "uploader_username": result[19],
                        "uploader_display_name": result[20],
                    }
                )

            return attachments

        except Exception as e:
            logger.error(f"Error getting attachments for task {task_id}: {e}")
            return []

    def add_task_watcher(
        self, task_id: int, user_id: int, preferences: Dict[str, bool] = None
    ) -> bool:
        """Add user as task watcher with notification preferences"""
        try:
            if not preferences:
                preferences = {"email": True, "slack": False, "mobile": False}

            query = """
            INSERT INTO task_watchers (task_id, user_id, notification_preferences)
            VALUES (%s, %s, %s)
            ON CONFLICT (task_id, user_id) DO UPDATE SET
            notification_preferences = EXCLUDED.notification_preferences
            """

            self.db.execute_query(query, (task_id, user_id, json.dumps(preferences)))
            return True

        except Exception as e:
            logger.error(f"Error adding task watcher: {e}")
            return False

    def get_task_watchers(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all task watchers"""
        try:
            query = """
            SELECT tw.*, u.username, u.display_name, u.email
            FROM task_watchers tw
            JOIN users u ON tw.user_id = u.id
            WHERE tw.task_id = %s
            ORDER BY tw.created_at
            """

            results = self.db.fetch_all(query, (task_id,))

            watchers = []
            for result in results:
                watchers.append(
                    {
                        "id": result[0],
                        "task_id": result[1],
                        "user_id": result[2],
                        "notification_preferences": (
                            json.loads(result[3]) if result[3] else {}
                        ),
                        "watch_type": result[4],
                        "created_at": result[5],
                        "username": result[6],
                        "display_name": result[7],
                        "email": result[8],
                    }
                )

            return watchers

        except Exception as e:
            logger.error(f"Error getting watchers for task {task_id}: {e}")
            return []

    def get_task_assigned_labels(self, task_id: int) -> List[Dict[str, Any]]:
        """Get labels assigned to a task"""
        try:
            query = """
            SELECT tl.*, tla.assigned_at, u.username as assigned_by_username
            FROM task_label_assignments tla
            JOIN task_labels tl ON tla.label_id = tl.id
            LEFT JOIN users u ON tla.assigned_by = u.id
            WHERE tla.task_id = %s
            ORDER BY tla.assigned_at
            """

            results = self.db.fetch_all(query, (task_id,))

            labels = []
            for result in results:
                labels.append(
                    {
                        "id": result[0],
                        "name": result[1],
                        "color": result[2],
                        "description": result[3],
                        "project_id": result[4],
                        "is_global": result[5],
                        "created_by": result[6],
                        "created_at": result[7],
                        "assigned_at": result[8],
                        "assigned_by_username": result[9],
                    }
                )

            return labels

        except Exception as e:
            logger.error(f"Error getting assigned labels for task {task_id}: {e}")
            return []

    def get_overdue_tasks(
        self, project_id: int = None, assignee_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get overdue tasks with comprehensive filtering"""
        try:
            query = """
            SELECT t.*, p.name as project_name, u.username as assignee_username
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN users u ON t.assignee_id = u.id
            WHERE t.due_date < CURRENT_DATE 
            AND t.status NOT IN (%s, %s)
            """

            params = [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]

            if project_id:
                query += " AND t.project_id = %s"
                params.append(project_id)

            if assignee_id:
                query += " AND t.assignee_id = %s"
                params.append(assignee_id)

            query += """
            ORDER BY 
                CASE t.priority 
                    WHEN 'Critical' THEN 4 
                    WHEN 'High' THEN 3 
                    WHEN 'Medium' THEN 2 
                    WHEN 'Low' THEN 1 
                END DESC,
                t.due_date ASC
            """

            results = self.db.fetch_all(query, params)

            tasks = []
            for result in results:
                task_dict = self._map_task_result_extended(result)
                task_dict["project_name"] = result[32] if len(result) > 32 else None
                task_dict["assignee_username"] = (
                    result[33] if len(result) > 33 else None
                )
                task_dict["days_overdue"] = (
                    datetime.now().date() - task_dict["due_date"]
                ).days
                tasks.append(task_dict)

            return tasks

        except Exception as e:
            logger.error(f"Error getting overdue tasks: {e}")
            return []

    def get_task_metrics(
        self,
        project_id: int = None,
        user_id: int = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> TaskMetrics:
        """Get comprehensive task metrics and analytics"""
        try:
            base_conditions = ["1=1"]
            params = []

            if project_id:
                base_conditions.append("project_id = %s")
                params.append(project_id)

            if user_id:
                base_conditions.append("assignee_id = %s")
                params.append(user_id)

            if start_date:
                base_conditions.append("created_at >= %s")
                params.append(start_date)

            if end_date:
                base_conditions.append("created_at <= %s")
                params.append(end_date)

            where_clause = " AND ".join(base_conditions)

            # Get comprehensive metrics
            metrics_query = f"""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN status = 'Done' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN status = 'In Progress' THEN 1 END) as in_progress_tasks,
                COUNT(CASE WHEN status = 'Blocked' THEN 1 END) as blocked_tasks,
                COUNT(CASE WHEN due_date < CURRENT_DATE AND status NOT IN ('Done', 'Cancelled') THEN 1 END) as overdue_tasks,
                COALESCE(SUM(estimated_hours), 0) as total_estimated_hours,
                COALESCE(SUM(actual_hours), 0) as total_actual_hours,
                COALESCE(SUM(story_points), 0) as velocity_points,
                COALESCE(SUM(CASE WHEN status NOT IN ('Done', 'Cancelled') THEN remaining_hours END), 0) as burndown_remaining
            FROM tasks 
            WHERE {where_clause}
            """

            result = self.db.fetch_one(metrics_query, params)

            if result:
                metrics = TaskMetrics(
                    total_tasks=result[0],
                    completed_tasks=result[1],
                    in_progress_tasks=result[2],
                    blocked_tasks=result[3],
                    overdue_tasks=result[4],
                    total_estimated_hours=float(result[5]),
                    total_actual_hours=float(result[6]),
                    velocity_points=result[7],
                    burndown_remaining=float(result[8]),
                )

                # Calculate derived metrics
                if metrics.total_tasks > 0:
                    metrics.completion_rate = (
                        metrics.completed_tasks / metrics.total_tasks
                    ) * 100

                if metrics.total_estimated_hours > 0:
                    metrics.efficiency_ratio = (
                        metrics.total_actual_hours / metrics.total_estimated_hours
                    )

                # Calculate average completion time
                completion_time_query = f"""
                SELECT AVG(EXTRACT(EPOCH FROM (completed_date::timestamp - created_at)) / 3600) 
                FROM tasks 
                WHERE {where_clause} AND status = 'Done' AND completed_date IS NOT NULL
                """

                completion_result = self.db.fetch_one(completion_time_query, params)
                if completion_result and completion_result[0]:
                    metrics.average_completion_time = float(completion_result[0])

                return metrics

            return TaskMetrics()

        except Exception as e:
            logger.error(f"Error getting task metrics: {e}")
            return TaskMetrics()

    def get_active_task_count(self) -> int:
        """Get count of active tasks across all projects"""
        try:
            query = """
            SELECT COUNT(*) FROM tasks 
            WHERE status IN (%s, %s, %s)
            """
            result = self.db.fetch_one(
                query,
                (
                    TaskStatus.TODO.value,
                    TaskStatus.IN_PROGRESS.value,
                    TaskStatus.REVIEW.value,
                ),
            )
            return result[0] if result else 0

        except Exception as e:
            logger.error(f"Error getting active task count: {e}")
            return 0

    def move_task_status(
        self, task_id: int, new_status: str, user_id: int, comment: str = None
    ) -> bool:
        """Move task status with workflow validation and optional comment"""
        try:
            current_task = self.get_task(task_id, include_relations=False)
            if not current_task:
                return False

            current_status = current_task["status"]

            # Check if transition is valid
            if not self._is_valid_status_transition(current_status, new_status):
                raise ValueError(
                    f"Invalid transition: {current_status} -> {new_status}"
                )

            # Check dependencies for certain transitions
            if new_status == TaskStatus.IN_PROGRESS.value:
                if not self._check_dependencies_completed(task_id):
                    raise ValueError("Cannot start task: dependencies not completed")

            # Update status
            success = self.update_task(task_id, {"status": new_status}, user_id)

            # Add status change comment if provided
            if success and comment:
                self.add_task_comment(
                    task_id, user_id, comment, comment_type="status_change"
                )

            return success

        except Exception as e:
            logger.error(f"Error moving task status: {e}")
            return False

    def _check_dependencies_completed(self, task_id: int) -> bool:
        """Check if all hard dependencies are completed"""
        try:
            query = """
            SELECT COUNT(*) FROM task_dependencies td
            JOIN tasks t ON td.depends_on_task_id = t.id
            WHERE td.task_id = %s 
            AND td.is_hard_dependency = TRUE
            AND (t.status != %s OR t.progress_percentage < td.percentage_complete_required)
            """
            result = self.db.fetch_one(query, (task_id, TaskStatus.DONE.value))
            return result[0] == 0 if result else True
        except:
            return True

    def search_tasks(
        self, search_text: str, project_id: int = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Full-text search across tasks"""
        try:
            query = """
            SELECT t.*, p.name as project_name,
                   ts_rank(to_tsvector('english', t.title || ' ' || COALESCE(t.description, '')), 
                           plainto_tsquery('english', %s)) as rank
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE to_tsvector('english', t.title || ' ' || COALESCE(t.description, '')) @@ plainto_tsquery('english', %s)
            """

            params = [search_text, search_text]

            if project_id:
                query += " AND t.project_id = %s"
                params.append(project_id)

            query += " ORDER BY rank DESC, t.updated_at DESC LIMIT %s"
            params.append(limit)

            results = self.db.fetch_all(query, params)

            tasks = []
            for result in results:
                task_dict = self._map_task_result_extended(result)
                task_dict["project_name"] = result[32] if len(result) > 32 else None
                task_dict["search_rank"] = float(result[33]) if len(result) > 33 else 0
                tasks.append(task_dict)

            return tasks

        except Exception as e:
            logger.error(f"Error searching tasks: {e}")
            return []

    def get_task_statistics(self, project_id: int = None) -> Dict[str, Any]:
        """Get comprehensive task statistics"""
        try:
            base_conditions = ["1=1"]
            params = []

            if project_id:
                base_conditions.append("project_id = %s")
                params.append(project_id)

            where_clause = " AND ".join(base_conditions)

            # Status distribution
            status_query = f"""
            SELECT status, COUNT(*) 
            FROM tasks 
            WHERE {where_clause}
            GROUP BY status
            """
            status_results = self.db.fetch_all(status_query, params)

            # Priority distribution
            priority_query = f"""
            SELECT priority, COUNT(*) 
            FROM tasks 
            WHERE {where_clause}
            GROUP BY priority
            """
            priority_results = self.db.fetch_all(priority_query, params)

            # Type distribution
            type_query = f"""
            SELECT task_type, COUNT(*) 
            FROM tasks 
            WHERE {where_clause}
            GROUP BY task_type
            """
            type_results = self.db.fetch_all(type_query, params)

            # Time statistics
            time_query = f"""
            SELECT 
                AVG(actual_hours) as avg_actual_hours,
                AVG(estimated_hours) as avg_estimated_hours,
                SUM(actual_hours) as total_actual_hours,
                SUM(estimated_hours) as total_estimated_hours
            FROM tasks 
            WHERE {where_clause} AND estimated_hours IS NOT NULL
            """
            time_result = self.db.fetch_one(time_query, params)

            return {
                "status_distribution": dict(status_results),
                "priority_distribution": dict(priority_results),
                "type_distribution": dict(type_results),
                "time_statistics": (
                    {
                        "avg_actual_hours": (
                            float(time_result[0]) if time_result[0] else 0
                        ),
                        "avg_estimated_hours": (
                            float(time_result[1]) if time_result[1] else 0
                        ),
                        "total_actual_hours": (
                            float(time_result[2]) if time_result[2] else 0
                        ),
                        "total_estimated_hours": (
                            float(time_result[3]) if time_result[3] else 0
                        ),
                    }
                    if time_result
                    else {}
                ),
            }

        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {}
            (f"Error deleting task {task_id}: {e}")
            return False

    # Advanced Query Methods
    def get_tasks_by_project(
        self,
        project_id: int,
        filters: Dict[str, Any] = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC",
        limit: int = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get tasks with advanced filtering and sorting"""
        try:
            base_query = """
            SELECT t.*,
                   u1.username as assignee_username, u1.display_name as assignee_display_name,
                   u2.username as reporter_username, u2.display_name as reporter_display_name,
                   pt.title as parent_task_title,
                   (SELECT COUNT(*) FROM tasks WHERE parent_task_id = t.id) as subtask_count
            FROM tasks t
            LEFT JOIN users u1 ON t.assignee_id = u1.id
            LEFT JOIN users u2 ON t.reporter_id = u2.id
            LEFT JOIN tasks pt ON t.parent_task_id = pt.id
            WHERE t.project_id = %s
            """

            params = [project_id]

            # Apply filters
            if filters:
                filter_conditions = []

                if filters.get("status"):
                    if isinstance(filters["status"], list):
                        placeholders = ",".join(["%s"] * len(filters["status"]))
                        filter_conditions.append(f"t.status IN ({placeholders})")
                        params.extend(filters["status"])
                    else:
                        filter_conditions.append("t.status = %s")
                        params.append(filters["status"])

                if filters.get("assignee_id"):
                    filter_conditions.append("t.assignee_id = %s")
                    params.append(filters["assignee_id"])

                if filters.get("priority"):
                    if isinstance(filters["priority"], list):
                        placeholders = ",".join(["%s"] * len(filters["priority"]))
                        filter_conditions.append(f"t.priority IN ({placeholders})")
                        params.extend(filters["priority"])
                    else:
                        filter_conditions.append("t.priority = %s")
                        params.append(filters["priority"])

                if filters.get("task_type"):
                    filter_conditions.append("t.task_type = %s")
                    params.append(filters["task_type"])

                if filters.get("due_date_from"):
                    filter_conditions.append("t.due_date >= %s")
                    params.append(filters["due_date_from"])

                if filters.get("due_date_to"):
                    filter_conditions.append("t.due_date <= %s")
                    params.append(filters["due_date_to"])

                if filters.get("search_text"):
                    filter_conditions.append(
                        "(t.title ILIKE %s OR t.description ILIKE %s OR t.tags ILIKE %s)"
                    )
                    search_term = f"%{filters['search_text']}%"
                    params.extend([search_term, search_term, search_term])

                if filters.get("labels"):
                    filter_conditions.append("t.labels ?| %s")
                    params.append(filters["labels"])

                if filters.get("overdue_only"):
                    filter_conditions.append(
                        "t.due_date < CURRENT_DATE AND t.status NOT IN ('Done', 'Cancelled')"
                    )

                if filters.get("unassigned_only"):
                    filter_conditions.append("t.assignee_id IS NULL")

                if filter_conditions:
                    base_query += " AND " + " AND ".join(filter_conditions)

            # Add sorting
            valid_sort_fields = [
                "created_at",
                "updated_at",
                "title",
                "priority",
                "due_date",
                "status",
                "assignee_username",
                "estimated_hours",
            ]

            if sort_by in valid_sort_fields:
                if sort_by == "priority":
                    # Custom priority sorting
                    base_query += f"""
                    ORDER BY 
                        CASE t.priority 
                            WHEN 'Critical' THEN 4 
                            WHEN 'High' THEN 3 
                            WHEN 'Medium' THEN 2 
                            WHEN 'Low' THEN 1 
                        END {sort_order},
                        t.created_at DESC
                    """
                else:
                    base_query += f" ORDER BY t.{sort_by} {sort_order}"
            else:
                base_query += " ORDER BY t.created_at DESC"

            # Add pagination
            if limit:
                base_query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])

            results = self.db.fetch_all(base_query, params)

            tasks = []
            for result in results:
                tasks.append(self._map_task_result_extended(result))

            return tasks

        except Exception as e:
            logger.error(f"Error getting tasks for project {project_id}: {e}")
            return []

    def get_tasks_by_assignee(
        self,
        user_id: int,
        include_completed: bool = False,
        project_filter: int = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get tasks assigned to a user with comprehensive details"""
        try:
            query = """
            SELECT t.*, p.name as project_name,
                   u2.username as reporter_username, u2.display_name as reporter_display_name,
                   (SELECT COUNT(*) FROM tasks WHERE parent_task_id = t.id) as subtask_count
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN users u2 ON t.reporter_id = u2.id
            WHERE t.assignee_id = %s
            """

            params = [user_id]

            if not include_completed:
                query += " AND t.status NOT IN (%s, %s)"
                params.extend([TaskStatus.DONE.value, TaskStatus.CANCELLED.value])

            if project_filter:
                query += " AND t.project_id = %s"
                params.append(project_filter)

            query += """
            ORDER BY 
                CASE t.priority 
                    WHEN 'Critical' THEN 4 
                    WHEN 'High' THEN 3 
                    WHEN 'Medium' THEN 2 
                    WHEN 'Low' THEN 1 
                END DESC,
                t.due_date ASC NULLS LAST,
                t.created_at DESC
            """

            if limit:
                query += " LIMIT %s"
                params.append(limit)

            results = self.db.fetch_all(query, params)

            tasks = []
            for result in results:
                task_dict = self._map_task_result_extended(result)
                task_dict["project_name"] = result[29] if len(result) > 29 else None
                tasks.append(task_dict)

            return tasks

        except Exception as e:
            logger.error(f"Error getting tasks for user {user_id}: {e}")
            return []

    def get_kanban_board_data(
        self, project_id: int, filters: Dict[str, Any] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get tasks organized for Kanban board with filtering"""
        try:
            # Get all tasks for project with filters
            tasks = self.get_tasks_by_project(project_id, filters)

            # Organize by status
            kanban_data = {status.value: [] for status in TaskStatus}

            for task in tasks:
                status = task["status"]
                if status in kanban_data:
                    # Add additional info for Kanban display
                    task["time_logged_today"] = self._get_time_logged_today(task["id"])
                    task["is_overdue"] = (
                        task["due_date"]
                        and task["due_date"] < datetime.now().date()
                        and task["status"]
                        not in [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]
                    )
                    kanban_data[status].append(task)

            return kanban_data

        except Exception as e:
            logger.error(f"Error getting Kanban data for project {project_id}: {e}")
            return {}

    # Dependency Management
    def add_task_dependency(
        self,
        task_id: int,
        depends_on_task_id: int,
        dependency_type: str = "finish_to_start",
        lag_days: int = 0,
        is_hard: bool = True,
        user_id: int = None,
        notes: str = None,
    ) -> bool:
        """Add task dependency with comprehensive validation"""
        try:
            # Validate tasks exist and are in same project
            task_query = "SELECT project_id FROM tasks WHERE id = %s"
            task_result = self.db.fetch_one(task_query, (task_id,))
            depends_on_result = self.db.fetch_one(task_query, (depends_on_task_id,))

            if not task_result or not depends_on_result:
                raise ValueError("One or both tasks do not exist")

            if task_result[0] != depends_on_result[0]:
                raise ValueError("Tasks must be in the same project")

            # Check for circular dependencies
            if self._creates_circular_dependency(task_id, depends_on_task_id):
                raise ValueError("This dependency would create a circular reference")

            query = """
            INSERT INTO task_dependencies 
            (task_id, depends_on_task_id, dependency_type, lag_days, is_hard_dependency, created_by, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (task_id, depends_on_task_id) 
            DO UPDATE SET 
                dependency_type = EXCLUDED.dependency_type,
                lag_days = EXCLUDED.lag_days,
                is_hard_dependency = EXCLUDED.is_hard_dependency,
                notes = EXCLUDED.notes
            """

            self.db.execute_query(
                query,
                (
                    task_id,
                    depends_on_task_id,
                    dependency_type,
                    lag_days,
                    is_hard,
                    user_id,
                    notes,
                ),
            )

            # Log the change
            self._log_task_history(
                task_id,
                user_id,
                "dependency_added",
                change_summary=f"Added dependency on task #{depends_on_task_id} ({dependency_type})",
            )

            return True

        except Exception as e:
            logger.error(f"Error adding task dependency: {e}")
            return False

    def remove_task_dependency(
        self, task_id: int, depends_on_task_id: int, user_id: int = None
    ) -> bool:
        """Remove task dependency"""
        try:
            query = "DELETE FROM task_dependencies WHERE task_id = %s AND depends_on_task_id = %s"
            affected_rows = self.db.execute_query(query, (task_id, depends_on_task_id))

            if affected_rows > 0:
                self._log_task_history(
                    task_id,
                    user_id,
                    "dependency_removed",
                    change_summary=f"Removed dependency on task #{depends_on_task_id}",
                )

            return affected_rows > 0

        except Exception as e:
            logger.error(f"Error removing task dependency: {e}")
            return False

    def get_task_dependencies(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all dependencies for a task"""
        try:
            query = """
            SELECT td.*, t.title, t.status, t.priority, t.progress_percentage,
                   u.username as created_by_username
            FROM task_dependencies td
            JOIN tasks t ON td.depends_on_task_id = t.id
            LEFT JOIN users u ON td.created_by = u.id
            WHERE td.task_id = %s
            ORDER BY td.created_at
            """

            results = self.db.fetch_all(query, (task_id,))

            dependencies = []
            for result in results:
                dependencies.append(
                    {
                        "id": result[0],
                        "task_id": result[1],
                        "depends_on_task_id": result[2],
                        "dependency_type": result[3],
                        "lag_days": result[4],
                        "lead_days": result[5],
                        "is_hard_dependency": result[6],
                        "percentage_complete_required": result[7],
                        "created_at": result[8],
                        "created_by": result[9],
                        "notes": result[10],
                        "depends_on_title": result[11],
                        "depends_on_status": result[12],
                        "depends_on_priority": result[13],
                        "depends_on_progress": result[14],
                        "created_by_username": result[15],
                    }
                )

            return dependencies

        except Exception as e:
            logger.error(f"Error getting dependencies for task {task_id}: {e}")
            return []

    def get_dependent_tasks(self, task_id: int) -> List[Dict[str, Any]]:
        """Get tasks that depend on this task"""
        try:
            query = """
            SELECT td.*, t.title, t.status, t.priority, t.assignee_id,
                   u1.username as assignee_username,
                   u2.username as created_by_username
            FROM task_dependencies td
            JOIN tasks t ON td.task_id = t.id
            LEFT JOIN users u1 ON t.assignee_id = u1.id
            LEFT JOIN users u2 ON td.created_by = u2.id
            WHERE td.depends_on_task_id = %s
            ORDER BY td.created_at
            """

            results = self.db.fetch_all(query, (task_id,))

            dependents = []
            for result in results:
                dependents.append(
                    {
                        "id": result[0],
                        "task_id": result[1],
                        "depends_on_task_id": result[2],
                        "dependency_type": result[3],
                        "lag_days": result[4],
                        "lead_days": result[5],
                        "is_hard_dependency": result[6],
                        "percentage_complete_required": result[7],
                        "created_at": result[8],
                        "created_by": result[9],
                        "notes": result[10],
                        "task_title": result[11],
                        "task_status": result[12],
                        "task_priority": result[13],
                        "task_assignee_id": result[14],
                        "assignee_username": result[15],
                        "created_by_username": result[16],
                    }
                )

            return dependents

        except Exception as e:
            logger.error(f"Error getting dependent tasks for {task_id}: {e}")
            return []

    # Time Tracking
    def log_time(
        self,
        task_id: int,
        user_id: int,
        start_time: datetime,
        end_time: datetime = None,
        duration_minutes: int = None,
        description: str = "",
        work_type: str = "Development",
        billable: bool = True,
        hourly_rate: float = None,
    ) -> bool:
        """Log time with comprehensive tracking"""
        try:
            # Calculate duration if not provided
            if duration_minutes is None and end_time:
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
            elif duration_minutes is None:
                raise ValueError("Either end_time or duration_minutes must be provided")

            # Validate duration
            if duration_minutes <= 0:
                raise ValueError("Duration must be positive")

            query = """
            INSERT INTO task_time_logs 
            (task_id, user_id, start_time, end_time, duration_minutes, 
             description, work_type, billable, hourly_rate, date_logged)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """

            result = self.db.fetch_one(
                query,
                (
                    task_id,
                    user_id,
                    start_time,
                    end_time,
                    duration_minutes,
                    description,
                    work_type,
                    billable,
                    hourly_rate,
                    start_time.date(),
                ),
            )

            if result:
                # Update task actual hours
                self._update_task_actual_hours(task_id)

                # Log activity
                hours = duration_minutes / 60
                self._log_task_history(
                    task_id,
                    user_id,
                    "time_logged",
                    change_summary=f"Logged {hours:.2f} hours ({work_type})",
                )

                return True

            return False

        except Exception as e:
            logger.error(f"Error logging time for task {task_id}: {e}")
            return False

    def get_task_time_logs(
        self,
        task_id: int,
        user_filter: int = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """Get time logs with filtering"""
        try:
            query = """
            SELECT ttl.*, u.username, u.display_name
            FROM task_time_logs ttl
            JOIN users u ON ttl.user_id = u.id
            WHERE ttl.task_id = %s
            """

            params = [task_id]

            if user_filter:
                query += " AND ttl.user_id = %s"
                params.append(user_filter)

            if date_from:
                query += " AND ttl.date_logged >= %s"
                params.append(date_from.date())

            if date_to:
                query += " AND ttl.date_logged <= %s"
                params.append(date_to.date())

            query += " ORDER BY ttl.start_time DESC"

            if limit:
                query += " LIMIT %s"
                params.append(limit)

            results = self.db.fetch_all(query, params)

            time_logs = []
            for result in results:
                time_logs.append(
                    {
                        "id": result[0],
                        "task_id": result[1],
                        "user_id": result[2],
                        "start_time": result[3],
                        "end_time": result[4],
                        "duration_minutes": result[5],
                        "description": result[6],
                        "work_type": result[7],
                        "billable": result[8],
                        "hourly_rate": float(result[9]) if result[9] else None,
                        "date_logged": result[10],
                        "created_at": result[11],
                        "updated_at": result[12],
                        "username": result[16],
                        "display_name": result[17],
                    }
                )

            return time_logs

        except Exception as e:
            logger.error(f"Error getting time logs for task {task_id}: {e}")
            return []

    # Comments and Communication
    def add_task_comment(
        self,
        task_id: int,
        user_id: int,
        comment_text: str,
        comment_type: str = "comment",
        is_internal: bool = False,
        parent_comment_id: int = None,
        mentions: List[int] = None,
    ) -> bool:
        """Add comment with mentions and threading support"""
        try:
            # Process mentions
            mention_data = []
            if mentions:
                # Validate mentioned users exist
                for mentioned_user_id in mentions:
                    user_check = self.db.fetch_one(
                        "SELECT id FROM users WHERE id = %s", (mentioned_user_id,)
                    )
                    if user_check:
                        mention_data.append(mentioned_user_id)

            query = """
            INSERT INTO task_comments 
            (task_id, user_id, parent_comment_id, comment_text, comment_type, is_internal, mentions)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """

            result = self.db.fetch_one(
                query,
                (
                    task_id,
                    user_id,
                    parent_comment_id,
                    comment_text,
                    comment_type,
                    is_internal,
                    json.dumps(mention_data),
                ),
            )

            if result:
                comment_id = result[0]

                # Log activity
                self._log_task_history(
                    task_id,
                    user_id,
                    "comment_added",
                    change_summary=f"Added {comment_type}: {comment_text[:50]}...",
                )

                # Add commenter as watcher if not already
                self.add_task_watcher(task_id, user_id)

                # Notify mentioned users
                if mention_data:
                    self._notify_mentioned_users(task_id, comment_id, mention_data)

                return True

            return False

        except Exception as e:
            logger.error(f"Error adding task comment: {e}")
            return False

    def get_task_comments(
        self, task_id: int, include_internal: bool = True, limit: int = None
    ) -> List[Dict[str, Any]]:
        """Get task comments with threading support"""
        try:
            query = """
            SELECT tc.*, u.username, u.display_name,
                   (SELECT COUNT(*) FROM task_comments WHERE parent_comment_id = tc.id) as reply_count
            FROM task_comments tc
            JOIN users u ON tc.user_id = u.id
            WHERE tc.task_id = %s
            """

            params = [task_id]

            if not include_internal:
                query += " AND tc.is_internal = FALSE"

            query += " ORDER BY tc.created_at ASC"

            if limit:
                query += " LIMIT %s"
                params.append(limit)

            results = self.db.fetch_all(query, params)

            comments = []
            for result in results:
                comments.append(
                    {
                        "id": result[0],
                        "task_id": result[1],
                        "user_id": result[2],
                        "parent_comment_id": result[3],
                        "comment_text": result[4],
                        "comment_type": result[5],
                        "is_internal": result[6],
                        "is_edited": result[7],
                        "mentions": json.loads(result[8]) if result[8] else [],
                        "attachments": json.loads(result[9]) if result[9] else [],
                        "reactions": json.loads(result[10]) if result[10] else {},
                        "created_at": result[11],
                        "updated_at": result[12],
                        "edited_at": result[13],
                        "edited_by": result[14],
                        "username": result[15],
                        "display_name": result[16],
                        "reply_count": result[17],
                    }
                )

            return comments

        except Exception as e:
            logger.error(f"Error getting comments for task {task_id}: {e}")
            return []

    # Helper and Utility Methods
    def _map_task_result_extended(self, result: tuple) -> Dict[str, Any]:
        """Map extended database result to task dictionary"""
        return {
            "id": result[0],
            "title": result[1],
            "description": result[2],
            "task_type": result[3],
            "status": result[4],
            "priority": result[5],
            "project_id": result[6],
            "assignee_id": result[7],
            "reporter_id": result[8],
            "parent_task_id": result[9],
            "estimated_hours": float(result[10]) if result[10] else None,
            "actual_hours": float(result[11]) if result[11] else 0.0,
            "remaining_hours": float(result[12]) if result[12] else None,
            "start_date": result[13],
            "due_date": result[14],
            "completed_date": result[15],
            "story_points": result[16],
            "sprint_id": result[17],
            "epic_id": result[18],
            "component": result[19],
            "fix_version": result[20],
            "affects_version": result[21],
            "resolution": result[22],
            "environment": result[23],
            "tags": result[24],
            "labels": json.loads(result[25]) if result[25] else [],
            "custom_fields": json.loads(result[26]) if result[26] else {},
            "progress_percentage": result[27] or 0,
            "external_id": result[28],
            "external_url": result[29],
            "created_at": result[30],
            "updated_at": result[31],
            # Joined fields
            "project_name": result[32] if len(result) > 32 else None,
            "assignee_username": result[33] if len(result) > 33 else None,
            "assignee_display_name": result[34] if len(result) > 34 else None,
            "reporter_username": result[35] if len(result) > 35 else None,
            "reporter_display_name": result[36] if len(result) > 36 else None,
            "parent_task_title": result[37] if len(result) > 37 else None,
            "subtask_count": result[38] if len(result) > 38 else 0,
            "comment_count": result[39] if len(result) > 39 else 0,
            "total_logged_minutes": result[40] if len(result) > 40 else 0,
        }

    def _validate_title(self, title: str) -> bool:
        """Validate task title"""
        return title and len(title.strip()) >= 3 and len(title) <= 500

    def _validate_status_transition(self, new_status: str) -> bool:
        """Validate if status value is valid"""
        return new_status in [s.value for s in TaskStatus]

    def _validate_user_exists(self, user_id: int) -> bool:
        """Validate user exists"""
        if user_id is None:
            return True
        try:
            result = self.db.fetch_one("SELECT id FROM users WHERE id = %s", (user_id,))
            return result is not None
        except:
            return False

    def _validate_parent_task(self, parent_task_id: int, project_id: int) -> bool:
        """Validate parent task belongs to same project"""
        if parent_task_id is None:
            return True
        try:
            result = self.db.fetch_one(
                "SELECT project_id FROM tasks WHERE id = %s", (parent_task_id,)
            )
            return result and result[0] == project_id
        except:
            return False

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Check if status transition is valid according to workflow"""
        try:
            query = """
            SELECT COUNT(*) FROM task_workflow_transitions 
            WHERE (from_status = %s OR from_status IS NULL) 
            AND to_status = %s AND is_active = TRUE
            """
            result = self.db.fetch_one(query, (current_status, new_status))
            return result[0] > 0 if result else False
        except:
            return True  # Allow transition if check fails

    def _creates_circular_dependency(
        self, task_id: int, depends_on_task_id: int
    ) -> bool:
        """Check for circular dependency using recursive CTE"""
        try:
            query = """
            WITH RECURSIVE dependency_chain AS (
                SELECT depends_on_task_id as task_id, 1 as depth
                FROM task_dependencies
                WHERE task_id = %s
                
                UNION ALL
                
                SELECT td.depends_on_task_id, dc.depth + 1
                FROM task_dependencies td
                JOIN dependency_chain dc ON td.task_id = dc.task_id
                WHERE dc.depth < 50  -- Prevent infinite recursion
            )
            SELECT COUNT(*) FROM dependency_chain WHERE task_id = %s
            """

            result = self.db.fetch_one(query, (depends_on_task_id, task_id))
            return result[0] > 0 if result else False

        except Exception as e:
            logger.error(f"Error checking circular dependency: {e}")
            return True  # Assume circular to be safe

    def _log_task_history(
        self,
        task_id: int,
        user_id: int,
        action: str,
        field_name: str = None,
        old_value: str = None,
        new_value: str = None,
        change_summary: str = None,
        automated: bool = False,
    ):
        """Log task history for audit trail"""
        try:
            query = """
            INSERT INTO task_history 
            (task_id, user_id, action, field_name, old_value, new_value, 
             change_summary, automated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.db.execute_query(
                query,
                (
                    task_id,
                    user_id,
                    action,
                    field_name,
                    old_value,
                    new_value,
                    change_summary,
                    automated,
                ),
            )
        except Exception as e:
            logger.error(f"Error logging task history: {e}")

    def _update_task_actual_hours(self, task_id: int):
        """Update task actual hours from time logs"""
        try:
            query = """
            UPDATE tasks 
            SET actual_hours = (
                SELECT COALESCE(SUM(duration_minutes), 0) / 60.0
                FROM task_time_logs 
                WHERE task_id = %s
            )
            WHERE id = %s
            """
            self.db.execute_query(query, (task_id, task_id))
        except Exception as e:
            logger.error
