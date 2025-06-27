# components/charts.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any


class ChartComponents:
    """Reusable chart components for the application"""

    @staticmethod
    def create_status_pie_chart(
        data: List[Dict],
        title: str = "Status Distribution",
        value_col: str = "Count",
        name_col: str = "Status",
    ) -> go.Figure:
        """Create a pie chart for status distribution"""
        if not data:
            return go.Figure().add_annotation(text="No data available", showarrow=False)

        df = pd.DataFrame(data)

        fig = px.pie(
            df,
            values=value_col,
            names=name_col,
            title=title,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
        )

        fig.update_layout(
            showlegend=True, height=350, margin=dict(t=50, b=20, l=20, r=20)
        )

        return fig

    @staticmethod
    def create_progress_bar_chart(
        data: List[Dict],
        title: str = "Progress Overview",
        x_col: str = "Name",
        y_col: str = "Progress",
    ) -> go.Figure:
        """Create a horizontal bar chart for progress tracking"""
        if not data:
            return go.Figure().add_annotation(text="No data available", showarrow=False)

        df = pd.DataFrame(data)

        # Color coding based on progress
        colors = []
        for progress in df[y_col]:
            if progress >= 80:
                colors.append("#28a745")  # Green
            elif progress >= 50:
                colors.append("#ffc107")  # Yellow
            elif progress >= 25:
                colors.append("#fd7e14")  # Orange
            else:
                colors.append("#dc3545")  # Red

        fig = go.Figure(
            data=[
                go.Bar(
                    y=df[x_col],
                    x=df[y_col],
                    orientation="h",
                    marker_color=colors,
                    text=[f"{p}%" for p in df[y_col]],
                    textposition="auto",
                    hovertemplate="<b>%{y}</b><br>Progress: %{x}%<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title="Progress (%)",
            yaxis_title="",
            height=max(300, len(df) * 30),
            margin=dict(t=50, b=20, l=100, r=20),
        )

        return fig

    @staticmethod
    def create_timeline_gantt(
        data: List[Dict], title: str = "Project Timeline"
    ) -> go.Figure:
        """Create a Gantt chart for project timeline"""
        if not data:
            return go.Figure().add_annotation(text="No data available", showarrow=False)

        df = pd.DataFrame(data)

        # Convert dates
        df["StartDate"] = pd.to_datetime(df["StartDate"])
        df["EndDate"] = pd.to_datetime(df["EndDate"])

        fig = px.timeline(
            df,
            x_start="StartDate",
            x_end="EndDate",
            y="TaskName",
            color="Status",
            title=title,
            color_discrete_map={
                "To Do": "#6c757d",
                "In Progress": "#007bff",
                "Testing": "#ffc107",
                "Done": "#28a745",
                "Blocked": "#dc3545",
            },
        )

        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            height=max(400, len(df) * 40), margin=dict(t=50, b=20, l=150, r=20)
        )

        return fig

    @staticmethod
    def create_metric_cards(metrics: Dict[str, Any]) -> None:
        """Create metric cards layout"""
        cols = st.columns(len(metrics))

        for i, (label, value) in enumerate(metrics.items()):
            with cols[i]:
                if isinstance(value, dict):
                    st.metric(
                        label=value.get("label", label),
                        value=value.get("value", 0),
                        delta=value.get("delta"),
                    )
                else:
                    st.metric(label=label, value=value)

    @staticmethod
    def create_workload_chart(
        data: List[Dict], title: str = "Team Workload"
    ) -> go.Figure:
        """Create a stacked bar chart for team workload"""
        if not data:
            return go.Figure().add_annotation(text="No data available", showarrow=False)

        df = pd.DataFrame(data)

        fig = go.Figure()

        # Add bars for different task types
        task_types = ["completed_tasks", "active_tasks", "overdue_tasks"]
        colors = ["#28a745", "#007bff", "#dc3545"]
        names = ["Completed", "Active", "Overdue"]

        for task_type, color, name in zip(task_types, colors, names):
            if task_type in df.columns:
                fig.add_trace(
                    go.Bar(
                        name=name,
                        x=df["Username"],
                        y=df[task_type],
                        marker_color=color,
                        hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y}}<extra></extra>",
                    )
                )

        fig.update_layout(
            title=title,
            barmode="stack",
            xaxis_title="Team Members",
            yaxis_title="Number of Tasks",
            height=400,
            margin=dict(t=50, b=20, l=20, r=20),
        )

        return fig

    @staticmethod
    def create_trend_line_chart(
        data: List[Dict],
        title: str = "Trend Analysis",
        x_col: str = "Date",
        y_col: str = "Value",
    ) -> go.Figure:
        """Create a line chart for trend analysis"""
        if not data:
            return go.Figure().add_annotation(text="No data available", showarrow=False)

        df = pd.DataFrame(data)
        df[x_col] = pd.to_datetime(df[x_col])

        fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)

        fig.update_traces(line=dict(width=3), marker=dict(size=8))

        fig.update_layout(
            height=350, margin=dict(t=50, b=20, l=20, r=20), hovermode="x unified"
        )

        return fig

    @staticmethod
    def create_heatmap(
        data: pd.DataFrame, title: str = "Activity Heatmap"
    ) -> go.Figure:
        """Create a heatmap visualization"""
        if data.empty:
            return go.Figure().add_annotation(text="No data available", showarrow=False)

        fig = go.Figure(
            data=go.Heatmap(
                z=data.values,
                x=data.columns,
                y=data.index,
                colorscale="Viridis",
                hoverongaps=False,
            )
        )

        fig.update_layout(title=title, height=400, margin=dict(t=50, b=20, l=100, r=20))

        return fig


def render_chart(chart_type: str, data: Any, **kwargs) -> None:
    """Render chart in Streamlit"""
    charts = ChartComponents()

    if chart_type == "pie":
        fig = charts.create_status_pie_chart(data, **kwargs)
    elif chart_type == "progress_bar":
        fig = charts.create_progress_bar_chart(data, **kwargs)
    elif chart_type == "gantt":
        fig = charts.create_timeline_gantt(data, **kwargs)
    elif chart_type == "workload":
        fig = charts.create_workload_chart(data, **kwargs)
    elif chart_type == "trend":
        fig = charts.create_trend_line_chart(data, **kwargs)
    elif chart_type == "heatmap":
        fig = charts.create_heatmap(data, **kwargs)
    else:
        st.error(f"Unknown chart type: {chart_type}")
        return

    st.plotly_chart(fig, use_container_width=True)
