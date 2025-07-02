# ui_components.py
"""
Advanced UI Components for DENSO Project Manager
Reusable components with modern design
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import base64


class UIComponents:
    """Collection of reusable UI components"""

    @staticmethod
    def render_metric_card(
        title: str,
        value: str,
        delta: str = None,
        color: str = "#007BFF",
        icon: str = "📊",
    ):
        """Render modern metric card"""
        delta_html = ""
        if delta:
            delta_color = "#28A745" if not delta.startswith("-") else "#DC3545"
            delta_html = f"""
            <div style="
                color: {delta_color};
                font-size: 0.9rem;
                font-weight: 600;
                margin-top: 5px;
            ">
                {delta}
            </div>
            """

        st.markdown(
            f"""
        <div style="
            background: linear-gradient(135deg, {color}20 0%, {color}10 100%);
            border-left: 4px solid {color};
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
        ">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 1.5rem; margin-right: 10px;">{icon}</span>
                <h4 style="margin: 0; color: #2E3440; font-weight: 600;">{title}</h4>
            </div>
            <div style="
                font-size: 2.5rem;
                font-weight: bold;
                color: {color};
                margin: 10px 0;
            ">
                {value}
            </div>
            {delta_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_progress_card(
        title: str, current: int, total: int, color: str = "#007BFF", icon: str = "📈"
    ):
        """Render progress card with animated progress bar"""
        percentage = (current / total * 100) if total > 0 else 0

        st.markdown(
            f"""
        <div style="
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        ">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.5rem; margin-right: 10px;">{icon}</span>
                    <h4 style="margin: 0; color: #2E3440;">{title}</h4>
                </div>
                <span style="
                    background: {color};
                    color: white;
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 0.9rem;
                    font-weight: 600;
                ">
                    {current}/{total}
                </span>
            </div>
            
            <div style="margin-bottom: 10px;">
                <div style="
                    background: #E9ECEF;
                    border-radius: 10px;
                    height: 12px;
                    overflow: hidden;
                ">
                    <div style="
                        background: linear-gradient(90deg, {color} 0%, {color}80 100%);
                        width: {percentage}%;
                        height: 100%;
                        border-radius: 10px;
                        transition: width 0.3s ease;
                        animation: progressAnimation 1s ease-out;
                    "></div>
                </div>
            </div>
            
            <div style="text-align: right; color: #5E6C7E; font-weight: 600;">
                {percentage:.1f}% Complete
            </div>
        </div>
        
        <style>
        @keyframes progressAnimation {{
            from {{ width: 0%; }}
            to {{ width: {percentage}%; }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_status_badge(status: str, status_config: Dict = None):
        """Render status badge with predefined colors"""
        default_config = {
            "Planning": {"color": "#FFA500", "icon": "📋"},
            "In Progress": {"color": "#007BFF", "icon": "🔄"},
            "Review": {"color": "#6F42C1", "icon": "👀"},
            "Testing": {"color": "#17A2B8", "icon": "🧪"},
            "Completed": {"color": "#28A745", "icon": "✅"},
            "Done": {"color": "#28A745", "icon": "✅"},
            "On Hold": {"color": "#DC3545", "icon": "⏸️"},
            "Cancelled": {"color": "#6C757D", "icon": "❌"},
            "Blocked": {"color": "#DC3545", "icon": "🚫"},
            "To Do": {"color": "#6C757D", "icon": "📝"},
        }

        config = status_config or default_config
        status_info = config.get(status, {"color": "#6C757D", "icon": "📄"})

        return f"""
        <span style="
            background: {status_info['color']};
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        ">
            {status_info['icon']} {status}
        </span>
        """

    @staticmethod
    def render_priority_badge(priority: str):
        """Render priority badge"""
        priority_config = {
            "Low": {"color": "#6C757D", "icon": "🔽"},
            "Medium": {"color": "#FFC107", "icon": "➖"},
            "High": {"color": "#FD7E14", "icon": "🔺"},
            "Critical": {"color": "#DC3545", "icon": "🔥"},
        }

        config = priority_config.get(priority, {"color": "#6C757D", "icon": "❓"})

        return f"""
        <span style="
            background: {config['color']};
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 3px;
        ">
            {config['icon']} {priority}
        </span>
        """

    @staticmethod
    def render_user_avatar(user_name: str, role: str = "", size: int = 40):
        """Render user avatar with initials"""
        initials = "".join([name[0].upper() for name in user_name.split() if name])[:2]

        # Color based on name hash
        colors = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#96CEB4",
            "#FECA57",
            "#FF9FF3",
            "#54A0FF",
        ]
        color = colors[hash(user_name) % len(colors)]

        return f"""
        <div style="
            width: {size}px;
            height: {size}px;
            border-radius: 50%;
            background: {color};
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: {size//2.5}px;
            margin-right: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        " title="{user_name} ({role})">
            {initials}
        </div>
        """

    @staticmethod
    def render_action_button(
        label: str,
        icon: str,
        color: str = "#007BFF",
        key: str = None,
        disabled: bool = False,
    ):
        """Render modern action button"""
        button_id = key or label.lower().replace(" ", "_")
        disabled_style = "opacity: 0.6; cursor: not-allowed;" if disabled else ""

        return st.markdown(
            f"""
        <style>
        .action-btn-{button_id} {{
            background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 20px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            {disabled_style}
        }}
        
        .action-btn-{button_id}:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            background: linear-gradient(135deg, {color}dd 0%, {color} 100%);
        }}
        </style>
        
        <button class="action-btn-{button_id}" {'disabled' if disabled else ''}>
            {icon} {label}
        </button>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_notification_toast(
        message: str, type: str = "info", duration: int = 5000
    ):
        """Render notification toast"""
        type_config = {
            "success": {"color": "#28A745", "icon": "✅"},
            "error": {"color": "#DC3545", "icon": "❌"},
            "warning": {"color": "#FFC107", "icon": "⚠️"},
            "info": {"color": "#17A2B8", "icon": "ℹ️"},
        }

        config = type_config.get(type, type_config["info"])

        st.markdown(
            f"""
        <div id="toast-{type}" style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: {config['color']};
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease-out;
        ">
            <span style="font-size: 1.2rem;">{config['icon']}</span>
            <span>{message}</span>
        </div>
        
        <script>
        setTimeout(function() {{
            document.getElementById('toast-{type}').style.animation = 'slideOut 0.3s ease-in';
            setTimeout(function() {{
                document.getElementById('toast-{type}').remove();
            }}, 300);
        }}, {duration});
        </script>
        
        <style>
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        @keyframes slideOut {{
            from {{ transform: translateX(0); opacity: 1; }}
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )


class ChartComponents:
    """Collection of chart components"""

    @staticmethod
    def render_donut_chart(
        data: List[Dict], title: str, value_col: str = "value", label_col: str = "label"
    ):
        """Render modern donut chart"""
        if not data:
            st.info(f"No data available for {title}")
            return

        df = pd.DataFrame(data)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df[label_col],
                    values=df[value_col],
                    hole=0.4,
                    textinfo="label+percent",
                    textposition="outside",
                    marker=dict(
                        colors=px.colors.qualitative.Set3,
                        line=dict(color="#FFFFFF", width=2),
                    ),
                )
            ]
        )

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=18, color="#2E3440")),
            showlegend=True,
            legend=dict(
                orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.01
            ),
            margin=dict(t=60, b=20, l=20, r=120),
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_progress_bar_chart(data: List[Dict], title: str):
        """Render horizontal progress bar chart"""
        if not data:
            st.info(f"No data available for {title}")
            return

        df = pd.DataFrame(data)

        fig = go.Figure()

        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57"]

        for i, row in df.iterrows():
            fig.add_trace(
                go.Bar(
                    y=[row["name"]],
                    x=[row["value"]],
                    orientation="h",
                    name=row["name"],
                    marker=dict(color=colors[i % len(colors)], cornerradius=5),
                    text=[f"{row['value']}%"],
                    textposition="inside",
                    textfont=dict(color="white", size=12),
                )
            )

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=18, color="#2E3440")),
            showlegend=False,
            xaxis=dict(
                title="Progress (%)",
                range=[0, 100],
                showgrid=True,
                gridcolor="rgba(0,0,0,0.1)",
            ),
            yaxis=dict(title="", showgrid=False),
            margin=dict(t=60, b=40, l=100, r=40),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_timeline_chart(data: List[Dict], title: str):
        """Render Gantt-style timeline chart"""
        if not data:
            st.info(f"No data available for {title}")
            return

        df = pd.DataFrame(data)

        # Convert dates
        df["Start"] = pd.to_datetime(df["start_date"])
        df["Finish"] = pd.to_datetime(df["end_date"])
        df["Duration"] = (df["Finish"] - df["Start"]).dt.days

        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="name",
            color="status",
            title=title,
            color_discrete_map={
                "Planning": "#FFA500",
                "In Progress": "#007BFF",
                "Completed": "#28A745",
                "On Hold": "#DC3545",
            },
        )

        fig.update_layout(
            height=400,
            margin=dict(t=60, b=40, l=100, r=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)"),
            yaxis=dict(showgrid=False),
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_area_chart(data: List[Dict], title: str, x_col: str, y_col: str):
        """Render modern area chart"""
        if not data:
            st.info(f"No data available for {title}")
            return

        df = pd.DataFrame(data)

        fig = px.area(
            df, x=x_col, y=y_col, title=title, color_discrete_sequence=["#007BFF"]
        )

        fig.update_traces(
            fill="tonexty",
            fillcolor="rgba(0, 123, 255, 0.1)",
            line=dict(color="#007BFF", width=3),
        )

        fig.update_layout(
            height=350,
            margin=dict(t=60, b=40, l=40, r=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True, gridcolor="rgba(0,0,0,0.1)", title_font=dict(size=14)
            ),
            yaxis=dict(
                showgrid=True, gridcolor="rgba(0,0,0,0.1)", title_font=dict(size=14)
            ),
            title=dict(x=0.5, font=dict(size=18, color="#2E3440")),
        )

        st.plotly_chart(fig, use_container_width=True)


class FormComponents:
    """Collection of form components"""

    @staticmethod
    def render_date_range_picker(label: str, key: str):
        """Render date range picker"""
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(f"{label} - Start", key=f"{key}_start")
        with col2:
            end_date = st.date_input(f"{label} - End", key=f"{key}_end")

        return start_date, end_date

    @staticmethod
    def render_multi_select_with_search(
        label: str, options: List[str], key: str, placeholder: str = "Select options..."
    ):
        """Render multi-select with search functionality"""
        return st.multiselect(
            label,
            options=options,
            key=key,
            placeholder=placeholder,
            help="Start typing to search options",
        )

    @staticmethod
    def render_file_uploader_with_preview(
        label: str, file_types: List[str], key: str, multiple: bool = False
    ):
        """Render file uploader with preview"""
        uploaded_files = st.file_uploader(
            label, type=file_types, key=key, accept_multiple_files=multiple
        )

        if uploaded_files:
            if isinstance(uploaded_files, list):
                for file in uploaded_files:
                    UIComponents.render_file_preview(file)
            else:
                UIComponents.render_file_preview(uploaded_files)

        return uploaded_files

    @staticmethod
    def render_file_preview(uploaded_file):
        """Render file preview"""
        file_size = len(uploaded_file.getvalue()) / 1024  # KB

        st.markdown(
            f"""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            border: 2px dashed #007BFF;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            text-align: center;
        ">
            <div style="font-size: 2rem; margin-bottom: 10px;">📄</div>
            <div style="font-weight: 600; color: #2E3440;">{uploaded_file.name}</div>
            <div style="color: #5E6C7E; font-size: 0.9rem;">
                Size: {file_size:.1f} KB | Type: {uploaded_file.type}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
