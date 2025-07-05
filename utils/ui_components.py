#!/usr/bin/env python3
"""
utils/ui_components.py
UI Components & Helpers for SDX Project Manager
Modern purple gradient theme components
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any, Optional


class UIComponents:
    """Modern UI components with SDX theme"""

    @staticmethod
    def load_custom_css():
        """Load custom CSS for SDX theme"""
        st.markdown(
            """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            :root {
                --primary: #667eea;
                --secondary: #764ba2;
                --accent: #f093fb;
                --success: #10b981;
                --warning: #f59e0b;
                --error: #ef4444;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --bg-primary: #f8fafc;
                --bg-secondary: #ffffff;
                --border: #e2e8f0;
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            
            .main {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                font-family: 'Inter', sans-serif;
            }
            
            .main-header {
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                color: white;
                padding: 2rem 2rem 3rem;
                margin: -1rem -1rem 2rem;
                border-radius: 0 0 20px 20px;
                box-shadow: var(--shadow);
            }
            
            .main-header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                margin: 0;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .main-header p {
                font-size: 1.125rem;
                margin: 0.5rem 0 0;
                opacity: 0.9;
            }
            
            .metric-card {
                background: var(--bg-secondary);
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
                transition: transform 0.2s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
            }
            
            .metric-value {
                font-size: 2.5rem;
                font-weight: 700;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0;
            }
            
            .metric-label {
                color: var(--text-secondary);
                font-size: 0.875rem;
                font-weight: 500;
                margin: 0.5rem 0 0;
            }
            
            .status-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .status-active { background: #dcfce7; color: #166534; }
            .status-pending { background: #fef3c7; color: #92400e; }
            .status-completed { background: #dbeafe; color: #1e40af; }
            .status-cancelled { background: #fee2e2; color: #991b1b; }
            
            .priority-high { background: #fee2e2; color: #991b1b; }
            .priority-medium { background: #fef3c7; color: #92400e; }
            .priority-low { background: #dcfce7; color: #166534; }
            
            .sidebar .sidebar-content {
                background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .stSelectbox > div > div {
                border-radius: 12px;
                border: 2px solid var(--border);
            }
            
            .stButton > button {
                border-radius: 12px;
                border: none;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                color: white;
                font-weight: 600;
                transition: all 0.2s ease;
            }
            
            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            .data-table {
                background: var(--bg-secondary);
                border-radius: 16px;
                overflow: hidden;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
            }
            
            .chart-container {
                background: var(--bg-secondary);
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_header(title: str, subtitle: str = ""):
        """Render main page header"""
        st.markdown(
            f"""
        <div class="main-header">
            <h1>{title}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_metric_card(
        label: str, value: Any, delta: Optional[str] = None, icon: str = "📊"
    ):
        """Render metric card"""
        delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""

        return st.markdown(
            f"""
        <div class="metric-card">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.5rem;">{icon}</span>
                <div style="flex: 1;">
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                    {delta_html}
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_status_badge(status: str) -> str:
        """Render status badge"""
        status_map = {
            "Active": ("status-active", "🟢"),
            "Pending": ("status-pending", "🟡"),
            "Completed": ("status-completed", "🔵"),
            "Cancelled": ("status-cancelled", "🔴"),
            "In Progress": ("status-active", "🟢"),
            "On Hold": ("status-pending", "🟡"),
        }

        css_class, icon = status_map.get(status, ("status-pending", "⚪"))
        return f'<span class="status-badge {css_class}">{icon} {status}</span>'

    @staticmethod
    def render_priority_badge(priority: str) -> str:
        """Render priority badge"""
        priority_map = {
            "High": ("priority-high", "🔴"),
            "Medium": ("priority-medium", "🟡"),
            "Low": ("priority-low", "🟢"),
        }

        css_class, icon = priority_map.get(priority, ("priority-low", "⚪"))
        return f'<span class="status-badge {css_class}">{icon} {priority}</span>'

    @staticmethod
    def create_progress_chart(
        data: List[Dict[str, Any]], title: str = "Project Progress"
    ):
        """Create progress chart"""
        if not data:
            return st.info("ไม่มีข้อมูลสำหรับแสดงผล")

        df = pd.DataFrame(data)

        fig = px.bar(
            df,
            x="name",
            y="progress",
            title=title,
            color="progress",
            color_continuous_scale=["#fee2e2", "#fef3c7", "#dcfce7"],
            text="progress",
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_family="Inter",
            title_font_size=16,
            title_font_color="#1e293b",
            showlegend=False,
        )

        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_xaxes(title_text="", tickangle=45)
        fig.update_yaxes(title_text="Progress (%)", range=[0, 100])

        return fig

    @staticmethod
    def create_status_pie_chart(
        data: List[Dict[str, Any]], title: str = "Status Distribution"
    ):
        """Create status pie chart"""
        if not data:
            return st.info("ไม่มีข้อมูลสำหรับแสดงผล")

        df = pd.DataFrame(data)

        colors = ["#667eea", "#764ba2", "#f093fb", "#c471ed"]

        fig = px.pie(
            df,
            values="count",
            names="status",
            title=title,
            color_discrete_sequence=colors,
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_family="Inter",
            title_font_size=16,
            title_font_color="#1e293b",
        )

        return fig

    @staticmethod
    def create_timeline_chart(
        data: List[Dict[str, Any]], title: str = "Project Timeline"
    ):
        """Create Gantt-style timeline chart"""
        if not data:
            return st.info("ไม่มีข้อมูลสำหรับแสดงผล")

        df = pd.DataFrame(data)

        fig = px.timeline(
            df,
            x_start="start_date",
            x_end="end_date",
            y="project",
            color="status",
            title=title,
            color_discrete_map={
                "Active": "#667eea",
                "Completed": "#10b981",
                "Pending": "#f59e0b",
                "Cancelled": "#ef4444",
            },
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_family="Inter",
            title_font_size=16,
            title_font_color="#1e293b",
            xaxis_title="Timeline",
            yaxis_title="Projects",
        )

        return fig

    @staticmethod
    def render_data_table(
        data: List[Dict[str, Any]], columns: List[str], title: str = ""
    ):
        """Render data table with custom styling"""
        if not data:
            return st.info("ไม่มีข้อมูลสำหรับแสดงผล")

        df = pd.DataFrame(data)

        if title:
            st.subheader(title)

        # Apply custom styling to dataframe
        styled_df = df.style.set_table_styles(
            [
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", "#667eea"),
                        ("color", "white"),
                        ("font-weight", "bold"),
                        ("border", "none"),
                    ],
                },
                {
                    "selector": "tbody td",
                    "props": [("border", "1px solid #e2e8f0"), ("padding", "0.75rem")],
                },
                {
                    "selector": "table",
                    "props": [
                        ("border-collapse", "collapse"),
                        ("border-radius", "8px"),
                        ("overflow", "hidden"),
                    ],
                },
            ]
        )

        return st.dataframe(styled_df, use_container_width=True)

    @staticmethod
    def render_notification(message: str, type: str = "info", icon: str = ""):
        """Render notification with custom styling"""
        type_styles = {
            "success": ("#dcfce7", "#166534", "✅"),
            "warning": ("#fef3c7", "#92400e", "⚠️"),
            "error": ("#fee2e2", "#991b1b", "❌"),
            "info": ("#dbeafe", "#1e40af", "ℹ️"),
        }

        bg_color, text_color, default_icon = type_styles.get(type, type_styles["info"])
        display_icon = icon or default_icon

        st.markdown(
            f"""
        <div style="
            background: {bg_color};
            color: {text_color};
            padding: 1rem 1.5rem;
            border-radius: 12px;
            border-left: 4px solid {text_color};
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 500;
        ">
            <span style="font-size: 1.25rem;">{display_icon}</span>
            <span>{message}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_loading_spinner(text: str = "กำลังโหลด..."):
        """Render loading spinner"""
        return st.markdown(
            f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            padding: 2rem;
            color: #64748b;
        ">
            <div style="
                width: 20px;
                height: 20px;
                border: 2px solid #e2e8f0;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
            <span>{text}</span>
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

    @staticmethod
    def render_empty_state(title: str, message: str, icon: str = "📋"):
        """Render empty state"""
        return st.markdown(
            f"""
        <div style="
            text-align: center;
            padding: 4rem 2rem;
            color: #64748b;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
            <h3 style="color: #1e293b; margin-bottom: 0.5rem;">{title}</h3>
            <p style="font-size: 1.125rem;">{message}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def create_sidebar_navigation():
        """Create sidebar navigation"""
        st.sidebar.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            margin: -1rem -1rem 2rem;
            padding: 2rem 1rem;
            text-align: center;
            color: white;
        ">
            <h2 style="margin: 0; font-size: 1.5rem;">SDX</h2>
            <p style="margin: 0.5rem 0 0; opacity: 0.9;">Project Manager</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        return st.sidebar.selectbox(
            "เลือกหน้า",
            ["🏠 หน้าหลัก", "📊 โครงการ", "✅ งาน", "👥 ผู้ใช้", "📈 รายงาน", "⚙️ ตั้งค่า"],
            label_visibility="collapsed",
        )

    @staticmethod
    def render_footer():
        """Render footer"""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.caption("**SDX | Project Manager v2.0**")
        with col2:
            st.caption(f"🕐 อัปเดต: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        with col3:
            st.caption("**Thammaphon Chittasuwanna (SDM) | Innovation**")
