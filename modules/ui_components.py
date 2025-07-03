#!/usr/bin/env python3
"""
modules/ui_components.py
Enterprise UI Components สำหรับ DENSO Project Manager Pro
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import logging
from dataclasses import dataclass
from functools import wraps
import json

logger = logging.getLogger(__name__)


@dataclass
class ComponentTheme:
    """Theme configuration for UI components"""

    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    success_color: str = "#2ca02c"
    warning_color: str = "#ff7f0e"
    danger_color: str = "#d62728"
    background_color: str = "#f8f9fa"
    text_color: str = "#333333"


class UIRenderer:
    """Enterprise-grade UI rendering system"""

    def __init__(self, theme: Optional[ComponentTheme] = None):
        self.theme = theme or ComponentTheme()
        self._component_cache = {}

    def render_page_header(
        self,
        title: str,
        subtitle: str = None,
        icon: str = None,
        actions: List[Dict] = None,
    ):
        """Render enhanced page header with actions"""
        col1, col2 = st.columns([3, 1])

        with col1:
            if icon:
                st.title(f"{icon} {title}")
            else:
                st.title(title)

            if subtitle:
                st.markdown(f"*{subtitle}*")

        with col2:
            if actions:
                for action in actions:
                    if st.button(
                        action.get("label", "Action"),
                        key=action.get("key"),
                        type=action.get("type", "secondary"),
                        use_container_width=True,
                    ):
                        if action.get("callback"):
                            action["callback"]()


class MetricCard:
    """Professional metric display card"""

    @staticmethod
    def render(
        title: str,
        value: str,
        delta: str = None,
        delta_color: str = "normal",
        icon: str = None,
    ):
        """Render metric card with enhanced styling"""
        container = st.container()

        with container:
            if icon:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(
                        f"<div style='font-size: 2em; text-align: center;'>{icon}</div>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.metric(title, value, delta, delta_color)
            else:
                st.metric(title, value, delta, delta_color)


class StatusBadge:
    """Status badge component with colors"""

    STATUS_COLORS = {
        "active": "🟢",
        "inactive": "🔴",
        "pending": "🟡",
        "completed": "✅",
        "in_progress": "🔵",
        "planning": "⚪",
        "on_hold": "🟠",
        "cancelled": "❌",
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢",
        "critical": "🚨",
    }

    @staticmethod
    def render(status: str, text: str = None) -> str:
        """Render status badge with appropriate color"""
        display_text = text or status.title()
        icon = StatusBadge.STATUS_COLORS.get(status.lower(), "⚪")
        return f"{icon} {display_text}"


class ProgressBar:
    """Enhanced progress bar component"""

    @staticmethod
    def render(
        value: float, max_value: float = 100, label: str = None, color: str = None
    ):
        """Render progress bar with custom styling"""
        percentage = (value / max_value) * 100

        if label:
            st.markdown(f"**{label}**")

        # Color based on percentage
        if not color:
            if percentage >= 80:
                color = "#2ca02c"  # Green
            elif percentage >= 60:
                color = "#ff7f0e"  # Orange
            else:
                color = "#d62728"  # Red

        st.progress(percentage / 100)
        st.markdown(f"{percentage:.1f}% ({value:.0f}/{max_value:.0f})")


class DataTable:
    """Advanced data table with sorting and filtering"""

    @staticmethod
    def render(
        data: List[Dict],
        columns: List[str] = None,
        searchable: bool = True,
        sortable: bool = True,
        actions: List[Dict] = None,
        page_size: int = 10,
    ):
        """Render enhanced data table"""

        if not data:
            st.info("ไม่มีข้อมูลในตาราง")
            return

        df = pd.DataFrame(data)

        if columns:
            df = df[columns]

        # Search functionality
        if searchable:
            search_term = st.text_input("🔍 ค้นหา", key="table_search")
            if search_term:
                # Search across all string columns
                mask = (
                    df.astype(str)
                    .apply(lambda x: x.str.contains(search_term, case=False, na=False))
                    .any(axis=1)
                )
                df = df[mask]

        # Display table
        if sortable:
            df = st.dataframe(df, use_container_width=True, height=400)
        else:
            st.dataframe(df, use_container_width=True, height=400)

        # Actions
        if actions:
            st.markdown("**Actions:**")
            cols = st.columns(len(actions))
            for i, action in enumerate(actions):
                with cols[i]:
                    if st.button(
                        action.get("label", "Action"), key=f"table_action_{i}"
                    ):
                        if action.get("callback"):
                            action["callback"]()


class ChartRenderer:
    """Professional chart rendering system"""

    @staticmethod
    def render_kpi_chart(data: Dict[str, float], title: str = "KPI Overview"):
        """Render KPI gauge charts"""
        fig = go.Figure()

        for i, (label, value) in enumerate(data.items()):
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=value,
                    domain={"row": 0, "column": i},
                    title={"text": label},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgray"},
                            {"range": [50, 80], "color": "gray"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 90,
                        },
                    },
                )
            )

        fig.update_layout(
            title=title,
            grid={"rows": 1, "columns": len(data), "pattern": "independent"},
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_trend_chart(
        data: pd.DataFrame, x_col: str, y_col: str, title: str = "Trend Analysis"
    ):
        """Render trend line chart"""
        fig = px.line(data, x=x_col, y=y_col, title=title, markers=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_distribution_chart(data: List[str], title: str = "Distribution"):
        """Render pie chart for distributions"""
        value_counts = pd.Series(data).value_counts()

        fig = px.pie(values=value_counts.values, names=value_counts.index, title=title)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


class CardComponent:
    """Reusable card component"""

    @staticmethod
    def render(
        title: str, content: str = None, actions: List[Dict] = None, status: str = None
    ):
        """Render card with optional actions"""

        with st.container():
            # Header
            col1, col2 = st.columns([3, 1])

            with col1:
                if status:
                    st.markdown(f"### {title} {StatusBadge.render(status)}")
                else:
                    st.markdown(f"### {title}")

            with col2:
                if actions:
                    for action in actions:
                        if st.button(
                            action.get("label", "Action"),
                            key=action.get("key"),
                            type=action.get("type", "secondary"),
                        ):
                            if action.get("callback"):
                                action["callback"]()

            # Content
            if content:
                st.markdown(content)

            st.markdown("---")


class FormBuilder:
    """Dynamic form builder"""

    @staticmethod
    def render_form(
        fields: List[Dict], form_key: str = "dynamic_form", submit_label: str = "Submit"
    ) -> Dict[str, Any]:
        """Render dynamic form based on field configuration"""

        form_data = {}

        with st.form(form_key):
            for field in fields:
                field_type = field.get("type", "text")
                field_key = field.get("key")
                field_label = field.get("label", field_key)
                field_required = field.get("required", False)
                field_help = field.get("help")

                label = f"{field_label}{'*' if field_required else ''}"

                if field_type == "text":
                    form_data[field_key] = st.text_input(
                        label, value=field.get("default", ""), help=field_help
                    )

                elif field_type == "textarea":
                    form_data[field_key] = st.text_area(
                        label, value=field.get("default", ""), help=field_help
                    )

                elif field_type == "number":
                    form_data[field_key] = st.number_input(
                        label, value=field.get("default", 0), help=field_help
                    )

                elif field_type == "select":
                    options = field.get("options", [])
                    form_data[field_key] = st.selectbox(
                        label,
                        options,
                        index=field.get("default_index", 0),
                        help=field_help,
                    )

                elif field_type == "multiselect":
                    options = field.get("options", [])
                    form_data[field_key] = st.multiselect(
                        label,
                        options,
                        default=field.get("default", []),
                        help=field_help,
                    )

                elif field_type == "date":
                    form_data[field_key] = st.date_input(
                        label, value=field.get("default"), help=field_help
                    )

                elif field_type == "checkbox":
                    form_data[field_key] = st.checkbox(
                        label, value=field.get("default", False), help=field_help
                    )

            submitted = st.form_submit_button(submit_label, type="primary")

            if submitted:
                # Validate required fields
                errors = []
                for field in fields:
                    if field.get("required") and not form_data.get(field["key"]):
                        errors.append(f"กรุณากรอก {field.get('label', field['key'])}")

                if errors:
                    for error in errors:
                        st.error(error)
                    return None

                return form_data

        return None


class NotificationManager:
    """Notification system"""

    @staticmethod
    def success(message: str, duration: int = 3):
        """Show success notification"""
        st.success(f"✅ {message}")

    @staticmethod
    def error(message: str, duration: int = 5):
        """Show error notification"""
        st.error(f"❌ {message}")

    @staticmethod
    def warning(message: str, duration: int = 4):
        """Show warning notification"""
        st.warning(f"⚠️ {message}")

    @staticmethod
    def info(message: str, duration: int = 3):
        """Show info notification"""
        st.info(f"ℹ️ {message}")


class TimelineComponent:
    """Timeline visualization component"""

    @staticmethod
    def render(events: List[Dict], title: str = "Timeline"):
        """Render timeline of events"""
        st.subheader(title)

        for event in events:
            date = event.get("date", "")
            title = event.get("title", "")
            description = event.get("description", "")
            status = event.get("status", "")

            with st.container():
                col1, col2 = st.columns([1, 4])

                with col1:
                    st.markdown(f"**{date}**")
                    if status:
                        st.markdown(StatusBadge.render(status))

                with col2:
                    st.markdown(f"**{title}**")
                    if description:
                        st.markdown(description)

                st.markdown("---")


class FilterPanel:
    """Advanced filtering panel"""

    @staticmethod
    def render(filters: List[Dict], key_prefix: str = "filter") -> Dict[str, Any]:
        """Render filter panel and return filter values"""

        filter_values = {}

        with st.expander("🔍 ตัวกรอง", expanded=False):
            cols = st.columns(len(filters))

            for i, filter_config in enumerate(filters):
                with cols[i]:
                    filter_type = filter_config.get("type", "select")
                    filter_key = filter_config.get("key")
                    filter_label = filter_config.get("label", filter_key)

                    if filter_type == "select":
                        options = ["ทั้งหมด"] + filter_config.get("options", [])
                        selected = st.selectbox(
                            filter_label, options, key=f"{key_prefix}_{filter_key}"
                        )
                        filter_values[filter_key] = (
                            None if selected == "ทั้งหมด" else selected
                        )

                    elif filter_type == "multiselect":
                        options = filter_config.get("options", [])
                        selected = st.multiselect(
                            filter_label, options, key=f"{key_prefix}_{filter_key}"
                        )
                        filter_values[filter_key] = selected if selected else None

                    elif filter_type == "date_range":
                        col_start, col_end = st.columns(2)
                        with col_start:
                            start_date = st.date_input(
                                "วันที่เริ่ม", key=f"{key_prefix}_{filter_key}_start"
                            )
                        with col_end:
                            end_date = st.date_input(
                                "วันที่สิ้นสุด", key=f"{key_prefix}_{filter_key}_end"
                            )
                        filter_values[filter_key] = {
                            "start": start_date,
                            "end": end_date,
                        }

        return filter_values


class ModernModal:
    """Modern modal dialog system"""

    @staticmethod
    def show(
        title: str,
        content: Callable,
        show_condition: bool = True,
        width: str = "medium",
    ):
        """Show modal dialog"""

        if show_condition:
            with st.expander(f"📋 {title}", expanded=True):
                content()


class ExportButton:
    """Data export functionality"""

    @staticmethod
    def render(
        data: Any,
        filename: str,
        file_format: str = "csv",
        button_label: str = "📥 ส่งออกข้อมูล",
    ):
        """Render export button with multiple formats"""

        if file_format == "csv" and isinstance(data, (list, pd.DataFrame)):
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = data

            csv_data = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label=button_label,
                data=csv_data,
                file_name=f"{filename}.csv",
                mime="text/csv",
            )

        elif file_format == "json":
            if isinstance(data, pd.DataFrame):
                json_data = data.to_json(orient="records", force_ascii=False)
            else:
                json_data = json.dumps(data, ensure_ascii=False, indent=2)

            st.download_button(
                label=button_label,
                data=json_data.encode("utf-8"),
                file_name=f"{filename}.json",
                mime="application/json",
            )


# Utility functions for common UI patterns
def render_loading_spinner(message: str = "กำลังโหลด..."):
    """Show loading spinner with message"""
    with st.spinner(message):
        return True


def render_empty_state(
    message: str = "ไม่มีข้อมูล", icon: str = "📭", suggestion: str = None
):
    """Render empty state with icon and suggestion"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            f"""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
            <h3>{message}</h3>
            {f'<p style="color: #666;">{suggestion}</p>' if suggestion else ''}
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_confirmation_dialog(
    message: str, confirm_label: str = "ยืนยัน", cancel_label: str = "ยกเลิก"
) -> Optional[bool]:
    """Render confirmation dialog"""
    st.warning(message)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button(confirm_label, type="primary", key="confirm_yes"):
            return True

    with col2:
        if st.button(cancel_label, key="confirm_no"):
            return False

    return None
