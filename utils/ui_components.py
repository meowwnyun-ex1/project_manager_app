#!/usr/bin/env python3
"""
utils/ui_components.py
Enterprise UI Components and Theme Management
Production-ready UI components with modern design
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class ThemeManager:
    """Modern theme management with enterprise colors"""

    @staticmethod
    def get_theme_colors() -> Dict[str, str]:
        """Get enterprise color palette"""
        return {
            # Primary colors
            "primary": "#6366f1",
            "primary_dark": "#4f46e5",
            "primary_light": "#a5b4fc",
            # Secondary colors
            "secondary": "#8b5cf6",
            "accent": "#06b6d4",
            # Status colors
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "info": "#3b82f6",
            # Neutral colors
            "white": "#ffffff",
            "gray_50": "#f8fafc",
            "gray_100": "#f1f5f9",
            "gray_200": "#e2e8f0",
            "gray_300": "#cbd5e1",
            "gray_400": "#94a3b8",
            "gray_500": "#64748b",
            "gray_600": "#475569",
            "gray_700": "#334155",
            "gray_800": "#1e293b",
            "gray_900": "#0f172a",
            # Background colors
            "bg_primary": "#ffffff",
            "bg_secondary": "#f8fafc",
            "bg_tertiary": "#f1f5f9",
            # Text colors
            "text_primary": "#1e293b",
            "text_secondary": "#64748b",
            "text_muted": "#94a3b8",
        }

    @staticmethod
    def apply_custom_css():
        """Apply enterprise CSS with modern design"""
        colors = ThemeManager.get_theme_colors()

        st.markdown(
            f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {{
            --primary: {colors['primary']};
            --primary-dark: {colors['primary_dark']};
            --secondary: {colors['secondary']};
            --success: {colors['success']};
            --warning: {colors['warning']};
            --error: {colors['error']};
            --info: {colors['info']};
            --bg-primary: {colors['bg_primary']};
            --bg-secondary: {colors['bg_secondary']};
            --text-primary: {colors['text_primary']};
            --text-secondary: {colors['text_secondary']};
            --gray-200: {colors['gray_200']};
        }}
        
        /* Global styles */
        .stApp {{
            font-family: 'Inter', system-ui, sans-serif;
        }}
        
        /* Hide default Streamlit elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stDeployButton {{display: none;}}
        
        /* Custom card component */
        .ui-card {{
            background: var(--bg-primary);
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid var(--gray-200);
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            transition: all 0.2s ease;
        }}
        
        .ui-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }}
        
        /* Status badges */
        .status-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .status-active {{ background: var(--success); color: white; }}
        .status-pending {{ background: var(--warning); color: white; }}
        .status-completed {{ background: var(--primary); color: white; }}
        .status-cancelled {{ background: var(--error); color: white; }}
        
        /* Button enhancements */
        .stButton > button {{
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
            border: none;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }}
        
        /* Form styling */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea {{
            border-radius: 0.5rem;
            border: 1px solid var(--gray-200);
            transition: border-color 0.2s ease;
        }}
        
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgb(99 102 241 / 0.1);
        }}
        
        /* Progress bars */
        .stProgress .st-bo {{
            background-color: var(--gray-200);
            border-radius: 9999px;
        }}
        
        .stProgress .st-bp {{
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            border-radius: 9999px;
        }}
        
        /* Metrics styling */
        .metric-container {{
            background: var(--bg-primary);
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid var(--gray-200);
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        
        .metric-label {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}
        
        .metric-delta {{
            font-size: 0.75rem;
            font-weight: 500;
        }}
        
        .metric-delta.positive {{ color: var(--success); }}
        .metric-delta.negative {{ color: var(--error); }}
        
        /* Alert styling */
        .custom-alert {{
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            border-left: 4px solid;
        }}
        
        .alert-success {{
            background: rgb(16 185 129 / 0.1);
            border-color: var(--success);
            color: #065f46;
        }}
        
        .alert-warning {{
            background: rgb(245 158 11 / 0.1);
            border-color: var(--warning);
            color: #92400e;
        }}
        
        .alert-error {{
            background: rgb(239 68 68 / 0.1);
            border-color: var(--error);
            color: #991b1b;
        }}
        
        .alert-info {{
            background: rgb(59 130 246 / 0.1);
            border-color: var(--info);
            color: #1e40af;
        }}
        
        /* Loading spinner */
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Table styling */
        .dataframe {{
            border: none !important;
            border-radius: 0.5rem !important;
            overflow: hidden !important;
        }}
        
        .dataframe th {{
            background-color: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            border: none !important;
        }}
        
        .dataframe td {{
            border: none !important;
            border-bottom: 1px solid var(--gray-200) !important;
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background: linear-gradient(180deg, var(--primary) 0%, var(--primary-dark) 100%);
        }}
        
        .css-1d391kg .css-1v0mbdj {{
            border-radius: 0.5rem;
            margin: 0.5rem;
            padding: 0.5rem;
            background: rgba(255, 255, 255, 0.1);
        }}
        
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .ui-card {{
                padding: 1rem;
                margin-bottom: 1rem;
            }}
            
            .metric-container {{
                padding: 1rem;
                margin-bottom: 1rem;
            }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )


class UIComponents:
    """Enterprise UI components library"""

    def __init__(self, theme_manager: ThemeManager = None):
        self.theme = theme_manager or ThemeManager()
        self.colors = self.theme.get_theme_colors()

    def render_metric_card(
        self,
        label: str,
        value: Union[str, int, float],
        delta: Optional[Union[str, int, float]] = None,
        delta_type: str = "neutral",
        icon: str = "",
        help_text: str = "",
    ):
        """Render enhanced metric card"""
        delta_class = ""
        delta_symbol = ""

        if delta is not None:
            if delta_type == "positive" or (
                isinstance(delta, (int, float)) and delta > 0
            ):
                delta_class = "positive"
                delta_symbol = "↗"
            elif delta_type == "negative" or (
                isinstance(delta, (int, float)) and delta < 0
            ):
                delta_class = "negative"
                delta_symbol = "↘"

        delta_html = (
            f"""
        <div class="metric-delta {delta_class}">
            {delta_symbol} {delta}
        </div>
        """
            if delta is not None
            else ""
        )

        help_html = (
            f'<div style="font-size: 0.7rem; opacity: 0.7; margin-top: 0.25rem;">{help_text}</div>'
            if help_text
            else ""
        )

        st.markdown(
            f"""
        <div class="metric-container">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
            {help_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_status_badge(self, status: str, custom_colors: Dict[str, str] = None):
        """Render status badge with color coding"""
        colors = custom_colors or {
            "active": "status-active",
            "pending": "status-pending",
            "completed": "status-completed",
            "cancelled": "status-cancelled",
        }

        badge_class = colors.get(status.lower(), "status-pending")

        st.markdown(
            f"""
        <span class="status-badge {badge_class}">{status}</span>
        """,
            unsafe_allow_html=True,
        )

    def render_progress_card(
        self,
        title: str,
        progress: float,
        total: int,
        completed: int,
        description: str = "",
    ):
        """Render progress card with visualization"""
        progress_percent = min(progress * 100, 100)

        st.markdown(
            f"""
        <div class="ui-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary);">{title}</h4>
                <span style="font-weight: 600; color: var(--primary);">{progress_percent:.1f}%</span>
            </div>
            
            <div style="background: var(--gray-200); height: 8px; border-radius: 4px; margin-bottom: 0.75rem;">
                <div style="background: linear-gradient(90deg, var(--primary), var(--secondary)); 
                           height: 100%; width: {progress_percent}%; border-radius: 4px; transition: width 0.3s ease;"></div>
            </div>
            
            <div style="display: flex; justify-content: space-between; font-size: 0.875rem; color: var(--text-secondary);">
                <span>{completed} / {total} เสร็จสิ้น</span>
                <span>{description}</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_alert(
        self,
        message: str,
        alert_type: str = "info",
        title: str = "",
        dismissible: bool = False,
    ):
        """Render custom alert component"""
        icons = {"success": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}

        icon = icons.get(alert_type, "ℹ️")
        title_html = (
            f"<div style='font-weight: 600; margin-bottom: 0.5rem;'>{icon} {title}</div>"
            if title
            else ""
        )

        st.markdown(
            f"""
        <div class="custom-alert alert-{alert_type}">
            {title_html}
            <div>{message}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_data_table(
        self,
        data: pd.DataFrame,
        title: str = "",
        search: bool = True,
        pagination: bool = True,
        page_size: int = 10,
    ):
        """Render enhanced data table"""
        if title:
            st.subheader(title)

        if data.empty:
            self.render_alert("ไม่มีข้อมูลที่จะแสดง", "info")
            return

        # Search functionality
        if search and not data.empty:
            search_term = st.text_input("🔍 ค้นหา", placeholder="พิมพ์เพื่อค้นหา...")
            if search_term:
                # Simple text search across all columns
                mask = (
                    data.astype(str)
                    .apply(lambda x: x.str.contains(search_term, case=False, na=False))
                    .any(axis=1)
                )
                data = data[mask]

        # Pagination
        if pagination and len(data) > page_size:
            total_pages = (len(data) - 1) // page_size + 1
            page = st.selectbox(
                "หน้า",
                range(1, total_pages + 1),
                format_func=lambda x: f"หน้า {x} / {total_pages}",
            )

            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            data = data.iloc[start_idx:end_idx]

        # Display table
        st.dataframe(data, use_container_width=True, hide_index=True)

        # Table info
        st.caption(f"แสดง {len(data)} รายการ")

    def render_chart_card(
        self,
        title: str,
        chart_type: str,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        color_col: str = None,
        height: int = 400,
    ):
        """Render chart in a card container"""
        st.markdown(
            f"""
        <div class="ui-card">
            <h4 style="margin: 0 0 1rem 0; color: var(--text-primary);">{title}</h4>
        """,
            unsafe_allow_html=True,
        )

        try:
            if chart_type == "bar":
                fig = px.bar(
                    data,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
            elif chart_type == "line":
                fig = px.line(
                    data,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
            elif chart_type == "pie":
                fig = px.pie(
                    data,
                    values=y_col,
                    names=x_col,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
            elif chart_type == "scatter":
                fig = px.scatter(
                    data,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
            else:
                fig = px.bar(data, x=x_col, y=y_col)

            # Update layout for better appearance
            fig.update_layout(
                height=height,
                margin=dict(l=0, r=0, t=0, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif"),
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            logger.error(f"Chart rendering failed: {e}")
            self.render_alert("ไม่สามารถแสดงแผนภูมิได้", "error")

        st.markdown("</div>", unsafe_allow_html=True)

    def render_loading_spinner(self, text: str = "กำลังโหลด..."):
        """Render loading spinner"""
        st.markdown(
            f"""
        <div style="text-align: center; padding: 2rem;">
            <div class="loading-spinner"></div>
            <div style="margin-top: 1rem; color: var(--text-secondary);">{text}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_stats_grid(self, stats: List[Dict[str, Any]], columns: int = 4):
        """Render statistics in a grid layout"""
        cols = st.columns(columns)

        for i, stat in enumerate(stats):
            with cols[i % columns]:
                self.render_metric_card(
                    label=stat.get("label", ""),
                    value=stat.get("value", ""),
                    delta=stat.get("delta"),
                    delta_type=stat.get("delta_type", "neutral"),
                    icon=stat.get("icon", ""),
                    help_text=stat.get("help", ""),
                )

    def render_timeline_item(
        self,
        title: str,
        description: str,
        timestamp: datetime,
        status: str = "completed",
        icon: str = "📅",
    ):
        """Render timeline item"""
        status_colors = {
            "completed": self.colors["success"],
            "pending": self.colors["warning"],
            "cancelled": self.colors["error"],
        }

        color = status_colors.get(status, self.colors["info"])
        time_str = timestamp.strftime("%d/%m/%Y %H:%M")

        st.markdown(
            f"""
        <div style="display: flex; align-items: flex-start; margin-bottom: 1.5rem;">
            <div style="
                background: {color}; 
                color: white; 
                width: 32px; 
                height: 32px; 
                border-radius: 50%; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                margin-right: 1rem;
                font-size: 0.875rem;
            ">{icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
                    {title}
                </div>
                <div style="color: var(--text-secondary); margin-bottom: 0.5rem;">
                    {description}
                </div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">
                    {time_str}
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_feature_card(
        self,
        title: str,
        description: str,
        icon: str,
        action_label: str = "เรียนรู้เพิ่มเติม",
        action_callback: callable = None,
    ):
        """Render feature showcase card"""
        st.markdown(
            f"""
        <div class="ui-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
            <h3 style="margin: 0 0 1rem 0; color: var(--text-primary);">{title}</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">{description}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if action_callback:
            if st.button(action_label, key=f"feature_{title}"):
                action_callback()

    def render_sidebar_user_info(self, user: Dict[str, Any]):
        """Render user info in sidebar"""
        st.markdown(
            f"""
        <div style="
            text-align: center; 
            padding: 1rem; 
            background: rgba(255,255,255,0.1); 
            border-radius: 0.5rem; 
            margin-bottom: 1rem; 
            color: white;
        ">
            <div style="
                width: 60px; 
                height: 60px; 
                background: rgba(255,255,255,0.2); 
                border-radius: 50%; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                margin: 0 auto 0.75rem auto;
                font-size: 1.5rem;
            ">👤</div>
            <div style="font-weight: 600; margin-bottom: 0.25rem;">
                {user.get('FirstName', '')} {user.get('LastName', '')}
            </div>
            <div style="opacity: 0.8; font-size: 0.875rem;">
                {user.get('Role', 'User')}
            </div>
            <div style="opacity: 0.7; font-size: 0.75rem; margin-top: 0.25rem;">
                {user.get('Department', 'N/A')}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


class ChartGenerator:
    """Chart generation utilities"""

    @staticmethod
    def create_project_status_chart(data: pd.DataFrame) -> go.Figure:
        """Create project status pie chart"""
        try:
            if data.empty:
                # Create empty chart
                fig = go.Figure()
                fig.add_annotation(
                    text="ไม่มีข้อมูลโครงการ", x=0.5, y=0.5, font_size=16, showarrow=False
                )
                return fig

            fig = px.pie(
                data,
                values="count",
                names="status",
                title="สถานะโครงการ",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )

            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(family="Inter, sans-serif"),
            )

            return fig

        except Exception as e:
            logger.error(f"Failed to create project status chart: {e}")
            return go.Figure()

    @staticmethod
    def create_progress_chart(data: pd.DataFrame) -> go.Figure:
        """Create progress bar chart"""
        try:
            fig = px.bar(
                data,
                x="progress",
                y="project_name",
                orientation="h",
                title="ความคืบหน้าโครงการ",
                color="progress",
                color_continuous_scale="Blues",
            )

            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(family="Inter, sans-serif"),
            )

            return fig

        except Exception as e:
            logger.error(f"Failed to create progress chart: {e}")
            return go.Figure()

    @staticmethod
    def create_timeline_chart(data: pd.DataFrame) -> go.Figure:
        """Create project timeline Gantt chart"""
        try:
            fig = px.timeline(
                data,
                x_start="start_date",
                x_end="end_date",
                y="project_name",
                color="status",
                title="Timeline โครงการ",
            )

            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(family="Inter, sans-serif"),
            )

            return fig

        except Exception as e:
            logger.error(f"Failed to create timeline chart: {e}")
            return go.Figure()


# Utility functions
def format_currency(amount: float, currency: str = "THB") -> str:
    """Format currency with proper localization"""
    try:
        if currency == "THB":
            return f"฿{amount:,.2f}"
        else:
            return f"{currency} {amount:,.2f}"
    except:
        return str(amount)


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage"""
    try:
        return f"{value:.{decimals}f}%"
    except:
        return str(value)


def format_thai_date(date: datetime) -> str:
    """Format date in Thai format"""
    try:
        thai_months = [
            "ม.ค.",
            "ก.พ.",
            "มี.ค.",
            "เม.ย.",
            "พ.ค.",
            "มิ.ย.",
            "ก.ค.",
            "ส.ค.",
            "ก.ย.",
            "ต.ค.",
            "พ.ย.",
            "ธ.ค.",
        ]

        day = date.day
        month = thai_months[date.month - 1]
        year = date.year + 543  # Buddhist era

        return f"{day} {month} {year}"
    except:
        return str(date)


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
