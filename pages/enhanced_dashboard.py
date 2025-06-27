# pages/enhanced_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from services.enhanced_project_service import ProjectService
from services.task_service import TaskService


def app():
    """Enhanced dashboard with comprehensive project overview"""
    st.title("📊 ภาพรวมโปรเจกต์")

    # Get statistics
    project_stats = ProjectService.get_project_statistics()
    task_stats = TaskService.get_task_statistics()

    if not project_stats.get("total_projects", 0):
        st.info("ยังไม่มีโปรเจกต์ในระบบ กรุณาเพิ่มโปรเจกต์ในหน้า 'โปรเจกต์'")
        return

    # Key metrics cards
    render_metrics_cards(project_stats, task_stats)

    # Charts section
    col1, col2 = st.columns(2)

    with col1:
        render_project_status_chart(project_stats)
        render_task_progress_chart(task_stats)

    with col2:
        render_task_status_chart(task_stats)
        render_assignee_workload_chart(task_stats)

    # Upcoming tasks and alerts
    render_upcoming_tasks()
    render_alerts_section(project_stats, task_stats)


def render_metrics_cards(project_stats: dict, task_stats: dict):
    """Render key metrics in card format"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("โปรเจกต์ทั้งหมด", project_stats.get("total_projects", 0), delta=None)

    with col2:
        st.metric(
            "โปรเจกต์ที่ดำเนินการ", project_stats.get("active_projects", 0), delta=None
        )

    with col3:
        st.metric("งานทั้งหมด", task_stats.get("total_tasks", 0), delta=None)

    with col4:
        avg_progress = task_stats.get("average_progress", 0)
        st.metric("ความคืบหน้าเฉลี่ย", f"{avg_progress:.1f}%", delta=None)


def render_project_status_chart(project_stats: dict):
    """Render project status distribution chart"""
    st.subheader("สถานะโปรเจกต์")

    status_data = project_stats.get("status_distribution", [])
    if status_data:
        df = pd.DataFrame(status_data)

        fig = px.pie(
            df,
            values="Count",
            names="Status",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")

        fig.update_layout(
            showlegend=True, height=300, margin=dict(t=20, b=20, l=20, r=20)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถานะโปรเจกต์")


def render_task_status_chart(task_stats: dict):
    """Render task status distribution chart"""
    st.subheader("สถานะงาน")

    status_data = task_stats.get("status_distribution", [])
    if status_data:
        df = pd.DataFrame(status_data)

        fig = px.bar(
            df,
            x="Status",
            y="Count",
            color="Status",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )

        fig.update_layout(
            showlegend=False,
            height=300,
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis_title="สถานะ",
            yaxis_title="จำนวน",
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถานะงาน")


def render_task_progress_chart(task_stats: dict):
    """Render task progress overview"""
    st.subheader("ความคืบหน้างาน")

    # Get all tasks for progress analysis
    all_tasks = TaskService.get_all_tasks()

    if not all_tasks.empty:
        # Progress distribution
        progress_bins = [0, 25, 50, 75, 100]
        labels = ["0-25%", "26-50%", "51-75%", "76-100%"]

        all_tasks["ProgressRange"] = pd.cut(
            all_tasks["Progress"],
            bins=progress_bins,
            labels=labels,
            include_lowest=True,
        )

        progress_counts = all_tasks["ProgressRange"].value_counts().reset_index()
