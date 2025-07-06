#!/usr/bin/env python3
"""
utils/ui_components.py
Modern UI Components and Theme Management
Professional interface components for enterprise applications
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ThemeManager:
    """Modern theme management system"""

    @staticmethod
    def get_theme_colors():
        """Get current theme color palette"""
        return {
            "primary": "#6366f1",
            "primary_dark": "#4f46e5",
            "secondary": "#8b5cf6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "info": "#3b82f6",
            "background": "#ffffff",
            "surface": "#f8fafc",
            "text_primary": "#1e293b",
            "text_secondary": "#64748b",
            "border": "#e2e8f0",
        }

    @staticmethod
    def apply_custom_css():
        """Apply enterprise-grade CSS styling"""
        colors = ThemeManager.get_theme_colors()

        st.markdown(
            f"""
        <style>
        /* Import modern fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        /* CSS Variables */
        :root {{
            --primary-color: {colors['primary']};
            --primary-dark: {colors['primary_dark']};
            --secondary-color: {colors['secondary']};
            --success-color: {colors['success']};
            --warning-color: {colors['warning']};
            --error-color: {colors['error']};
            --info-color: {colors['info']};
            --background: {colors['background']};
            --surface: {colors['surface']};
            --text-primary: {colors['text_primary']};
            --text-secondary: {colors['text_secondary']};
            --border-color: {colors['border']};
        }}
        
        /* Global Styles */
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-feature-settings: 'cv11', 'ss01';
        }}
        
        /* Hide Streamlit Elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stDeployButton {{display: none;}}
        
        /* Enhanced Sidebar */
        .css-1d391kg {{
            background: linear-gradient(180deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            border-right: none;
            box-shadow: 4px 0 12px rgba(0,0,0,0.1);
        }}
        
        .css-1d391kg .css-17eq0hr {{
            color: white;
            font-weight: 600;
        }}
        
        /* Main Content Area */
        .main .block-container {{
            padding: 2rem;
            background: var(--surface);
            min-height: 100vh;
        }}
        
        /* Professional Cards */
        .metric-card {{
            background: var(--background);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        }}
        
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }}
        
        /* Enhanced Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39);
            text-transform: none;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
        }}
        
        .stButton > button:active {{
            transform: translateY(0);
        }}
        
        /* Status Badges */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.375rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .status-active {{
            background: rgba(16, 185, 129, 0.1);
            color: #059669;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }}
        
        .status-pending {{
            background: rgba(245, 158, 11, 0.1);
            color: #d97706;
            border: 1px solid rgba(245, 158, 11, 0.2);
        }}
        
        .status-completed {{
            background: rgba(59, 130, 246, 0.1);
            color: #2563eb;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }}
        
        .status-blocked {{
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            border: 1px solid rgba(239, 68, 68, 0.2);
        }}
        
        /* Priority Indicators */
        .priority-critical {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
        }}
        
        .priority-high {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }}
        
        .priority-medium {{
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
        }}
        
        .priority-low {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }}
        
        /* Enhanced Data Tables */
        .stDataFrame {{
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .stDataFrame table {{
            border-collapse: separate;
            border-spacing: 0;
        }}
        
        .stDataFrame th {{
            background: var(--surface);
            font-weight: 600;
            color: var(--text-primary);
            padding: 1rem;
            border-bottom: 2px solid var(--border-color);
        }}
        
        .stDataFrame td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .stDataFrame tbody tr:hover {{
            background: rgba(99, 102, 241, 0.05);
        }}
        
        /* Form Elements */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            border: 2px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {{
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }}
        
        /* Metrics */
        .metric {{
            background: var(--background);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .metric:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 800;
            color: var(--primary-color);
            line-height: 1;
            margin-bottom: 0.5rem;
        }}
        
        .metric-label {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Loading States */
        .loading-spinner {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 3rem;
        }}
        
        /* Toast Notifications */
        .stAlert {{
            border-radius: 12px;
            border: none;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        
        /* Progress Bars */
        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        }}
        
        /* Sidebar Navigation */
        .nav-item {{
            margin: 0.25rem 0;
        }}
        
        .nav-item button {{
            width: 100%;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: none;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .nav-item button:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: translateX(4px);
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding: 1rem;
            }}
            
            .metric-card {{
                padding: 1rem;
            }}
            
            .metric-value {{
                font-size: 1.5rem;
            }}
        }}
        
        /* Animation Utilities */
        .fade-in {{
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .slide-in {{
            animation: slideIn 0.3s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(-100%); }}
            to {{ transform: translateX(0); }}
        }}
        
        /* Dark Mode Support */
        @media (prefers-color-scheme: dark) {{
            :root {{
                --background: #0f172a;
                --surface: #1e293b;
                --text-primary: #f1f5f9;
                --text-secondary: #94a3b8;
                --border-color: #334155;
            }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )


class UIComponents:
    """Modern UI component library"""

    @staticmethod
    def render_metric_card(
        title: str,
        value: str,
        delta: str = None,
        delta_color: str = "normal",
        icon: str = None,
    ) -> None:
        """Render a modern metric card"""
        delta_html = ""
        if delta:
            color = (
                "#10b981"
                if delta_color == "normal"
                else "#ef4444" if delta_color == "inverse" else "#64748b"
            )
            delta_html = f'<div style="color: {color}; font-size: 0.875rem; margin-top: 0.5rem;">{delta}</div>'

        icon_html = (
            f'<div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>'
            if icon
            else ""
        )

        st.markdown(
            f"""
        <div class="metric-card">
            {icon_html}
            <div class="metric-value">{value}</div>
            <div class="metric-label">{title}</div>
            {delta_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_status_badge(status: str, size: str = "normal") -> str:
        """Render a status badge"""
        size_class = "status-badge-lg" if size == "large" else "status-badge"

        status_classes = {
            "Active": "status-active",
            "In Progress": "status-active",
            "Completed": "status-completed",
            "Done": "status-completed",
            "Pending": "status-pending",
            "Planning": "status-pending",
            "Blocked": "status-blocked",
            "Cancelled": "status-blocked",
        }

        status_class = status_classes.get(status, "status-pending")

        return f'<span class="status-badge {status_class}">{status}</span>'

    @staticmethod
    def render_priority_badge(priority: str) -> str:
        """Render a priority badge"""
        priority_classes = {
            "Critical": "priority-critical",
            "High": "priority-high",
            "Medium": "priority-medium",
            "Low": "priority-low",
        }

        priority_class = priority_classes.get(priority, "priority-medium")

        return f'<span class="status-badge {priority_class}">{priority}</span>'

    @staticmethod
    def render_progress_bar(
        value: float,
        max_value: float = 100,
        color: str = "primary",
        height: str = "8px",
    ) -> None:
        """Render a custom progress bar"""
        percentage = min((value / max_value) * 100, 100)
        colors = ThemeManager.get_theme_colors()

        color_map = {
            "primary": colors["primary"],
            "success": colors["success"],
            "warning": colors["warning"],
            "error": colors["error"],
        }

        bar_color = color_map.get(color, colors["primary"])

        st.markdown(
            f"""
        <div style="
            width: 100%;
            background: {colors['border']};
            border-radius: 4px;
            height: {height};
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                background: linear-gradient(90deg, {bar_color}, {colors['secondary']});
                height: 100%;
                transition: width 0.3s ease;
            "></div>
        </div>
        <div style="text-align: right; font-size: 0.75rem; color: {colors['text_secondary']}; margin-top: 0.25rem;">
            {value:.1f} / {max_value}
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_chart_container(
        chart, title: str = None, description: str = None
    ) -> None:
        """Render a chart with professional container"""
        container_html = '<div class="metric-card">'

        if title:
            container_html += f'<h3 style="margin: 0 0 1rem 0; color: var(--text-primary); font-weight: 600;">{title}</h3>'

        if description:
            container_html += f'<p style="margin: 0 0 1rem 0; color: var(--text-secondary); font-size: 0.875rem;">{description}</p>'

        st.markdown(container_html, unsafe_allow_html=True)
        st.plotly_chart(chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    @staticmethod
    def create_modern_chart(
        data: Dict, chart_type: str = "bar", title: str = None
    ) -> go.Figure:
        """Create a modern chart with consistent styling"""
        colors = ThemeManager.get_theme_colors()

        if chart_type == "bar":
            fig = px.bar(
                x=list(data.keys()),
                y=list(data.values()),
                title=title,
                color_discrete_sequence=[colors["primary"]],
            )
        elif chart_type == "pie":
            fig = px.pie(
                values=list(data.values()),
                names=list(data.keys()),
                title=title,
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
        elif chart_type == "line":
            fig = px.line(
                x=list(data.keys()),
                y=list(data.values()),
                title=title,
                color_discrete_sequence=[colors["primary"]],
            )
        else:
            fig = go.Figure()

        # Apply modern styling
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color=colors["text_primary"]),
            title=dict(font=dict(size=16, weight="bold")),
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=True if chart_type == "pie" else False,
        )

        if chart_type in ["bar", "line"]:
            fig.update_xaxes(gridcolor=colors["border"], showgrid=True, zeroline=False)
            fig.update_yaxes(gridcolor=colors["border"], showgrid=True, zeroline=False)

        return fig

    @staticmethod
    def render_data_table(
        data: List[Dict],
        columns: List[str] = None,
        sortable: bool = True,
        searchable: bool = True,
    ) -> None:
        """Render an enhanced data table"""
        if not data:
            st.info("ไม่มีข้อมูลที่จะแสดง")
            return

        import pandas as pd

        df = pd.DataFrame(data)

        if columns:
            df = df[columns]

        # Add search functionality
        if searchable and len(df) > 10:
            search_term = st.text_input("🔍 ค้นหา", placeholder="พิมพ์เพื่อค้นหา...")
            if search_term:
                df = df[
                    df.astype(str)
                    .apply(lambda x: x.str.contains(search_term, case=False, na=False))
                    .any(axis=1)
                ]

        # Display table
        st.markdown('<div class="data-table-container">', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    @staticmethod
    def render_timeline(events: List[Dict]) -> None:
        """Render a timeline component"""
        if not events:
            st.info("ไม่มีเหตุการณ์ที่จะแสดง")
            return

        timeline_html = '<div class="timeline">'

        for i, event in enumerate(events):
            timestamp = event.get("timestamp", "")
            title = event.get("title", "")
            description = event.get("description", "")
            type_color = event.get("type_color", "#6366f1")

            timeline_html += f"""
            <div class="timeline-item">
                <div class="timeline-marker" style="background: {type_color};"></div>
                <div class="timeline-content">
                    <div class="timeline-time">{timestamp}</div>
                    <div class="timeline-title">{title}</div>
                    <div class="timeline-description">{description}</div>
                </div>
            </div>
            """

        timeline_html += "</div>"

        # Add timeline CSS
        st.markdown(
            """
        <style>
        .timeline {
            position: relative;
            padding-left: 2rem;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 0.75rem;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--border-color);
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 2rem;
        }
        
        .timeline-marker {
            position: absolute;
            left: -2rem;
            top: 0.5rem;
            width: 1rem;
            height: 1rem;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 0 2px var(--border-color);
        }
        
        .timeline-content {
            background: var(--background);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .timeline-time {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .timeline-title {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        
        .timeline-description {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(timeline_html, unsafe_allow_html=True)

    @staticmethod
    def render_notification_toast(
        message: str, type: str = "info", duration: int = 3000
    ) -> None:
        """Render a notification toast"""
        type_colors = {
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "info": "#3b82f6",
        }

        color = type_colors.get(type, type_colors["info"])

        st.markdown(
            f"""
        <div class="notification-toast" style="
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: {color};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
        ">
            {message}
        </div>
        
        <style>
        @keyframes slideInRight {{
            from {{ transform: translateX(100%); }}
            to {{ transform: translateX(0); }}
        }}
        </style>
        
        <script>
        setTimeout(function() {{
            document.querySelector('.notification-toast').style.display = 'none';
        }}, {duration});
        </script>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_loading_spinner(message: str = "กำลังโหลด...") -> None:
        """Render a loading spinner"""
        st.markdown(
            f"""
        <div class="loading-spinner">
            <div style="
                border: 4px solid var(--border-color);
                border-top: 4px solid var(--primary-color);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin-right: 1rem;
            "></div>
            <span style="color: var(--text-secondary);">{message}</span>
        </div>
        
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )
