# pages/gantt_chart.py
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from services.enhanced_project_service import ProjectService
from services.task_service import TaskService


def app():
    st.title("📅 Gantt Chart")

    # Get projects
    projects_df = ProjectService.get_all_projects()
    if projects_df.empty:
        st.info("ไม่มีโปรเจกต์ กรุณาเพิ่มโปรเจกต์ก่อน")
        return

    # Project selector
    project_options = dict(zip(projects_df["ProjectName"], projects_df["ProjectID"]))
    selected_project = st.selectbox("เลือกโปรเจกต์", list(project_options.keys()))
    project_id = project_options[selected_project]

    # Get tasks
    tasks_df = TaskService.get_tasks_by_project(project_id)
    if tasks_df.empty:
        st.info(f"ไม่มีงานในโปรเจกต์ '{selected_project}'")
        return

    # Chart controls
    col1, col2 = st.columns(2)
    with col1:
        chart_type = st.radio("แสดงแบบ", ["สถานะ", "ความคืบหน้า", "ผู้รับผิดชอบ"])
    with col2:
        show_today = st.checkbox("แสดงเส้นวันนี้", True)

    # Prepare data
    chart_data = prepare_chart_data(tasks_df)
    if chart_data.empty:
        st.error("ข้อมูลวันที่ไม่ครบถ้วน")
        return

    # Create chart
    fig = create_gantt_chart(chart_data, selected_project, chart_type, show_today)
    st.plotly_chart(fig, use_container_width=True)

    # Show statistics
    show_project_stats(chart_data)


def prepare_chart_data(tasks_df):
    """Clean and prepare task data for charting"""
    df = tasks_df.copy()

    # Convert dates
    df["StartDate"] = pd.to_datetime(df["StartDate"], errors="coerce")
    df["EndDate"] = pd.to_datetime(df["EndDate"], errors="coerce")

    # Remove invalid dates
    df = df.dropna(subset=["StartDate", "EndDate"])

    # Sort by start date
    df = df.sort_values("StartDate")

    return df


def create_gantt_chart(df, project_name, chart_type, show_today):
    """Create Gantt chart based on type"""

    if chart_type == "สถานะ":
        color_col = "Status"
        color_map = {
            "To Do": "#6c757d",
            "In Progress": "#007bff",
            "Testing": "#ffc107",
            "Done": "#28a745",
            "Blocked": "#dc3545",
        }
    elif chart_type == "ความคืบหน้า":
        color_col = "Progress"
        color_map = None
    else:  # ผู้รับผิดชอบ
        color_col = "Assignee"
        color_map = None

    # Create timeline chart
    fig = px.timeline(
        df,
        x_start="StartDate",
        x_end="EndDate",
        y="TaskName",
        color=color_col,
        color_discrete_map=color_map,
        title=f"Gantt Chart: {project_name}",
        hover_data=["Progress", "Assignee", "Status"],
    )

    # Reverse Y-axis for better readability
    fig.update_yaxes(autorange="reversed")

    # Add today line
    if show_today:
        fig.add_vline(
            x=datetime.now(), line_dash="dash", line_color="red", annotation_text="วันนี้"
        )

    # Styling
    fig.update_layout(
        height=max(400, len(df) * 50),
        xaxis_title="วันที่",
        yaxis_title="งาน",
        showlegend=True,
    )

    return fig


def show_project_stats(df):
    """Display project statistics"""
    st.subheader("📊 สถิติโปรเจกต์")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_tasks = len(df)
        st.metric("งานทั้งหมด", total_tasks)

    with col2:
        completed = len(df[df["Status"] == "Done"])
        st.metric("เสร็จแล้ว", completed)

    with col3:
        if total_tasks > 0:
            completion_rate = (completed / total_tasks) * 100
            st.metric("อัตราสำเร็จ", f"{completion_rate:.1f}%")
        else:
            st.metric("อัตราสำเร็จ", "0%")

    with col4:
        avg_progress = df["Progress"].mean()
        st.metric("ความคืบหน้าเฉลี่ย", f"{avg_progress:.1f}%")

    # Timeline info
    st.subheader("⏰ ข้อมูลระยะเวลา")

    project_start = df["StartDate"].min()
    project_end = df["EndDate"].max()
    duration = (project_end - project_start).days

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**เริ่มโปรเจกต์:** {project_start.strftime('%d/%m/%Y')}")

    with col2:
        st.write(f"**สิ้นสุดโปรเจกต์:** {project_end.strftime('%d/%m/%Y')}")

    with col3:
        st.write(f"**ระยะเวลารวม:** {duration} วัน")

    # Overdue tasks warning
    today = pd.Timestamp.now()
    overdue = df[(df["EndDate"] < today) & (df["Status"] != "Done")]

    if not overdue.empty:
        st.warning(f"⚠️ มีงานเกินกำหนด {len(overdue)} งาน")

        with st.expander("ดูงานเกินกำหนด"):
            overdue_display = overdue[
                ["TaskName", "EndDate", "Assignee", "Progress"]
            ].copy()
            overdue_display["EndDate"] = overdue_display["EndDate"].dt.strftime(
                "%d/%m/%Y"
            )
            overdue_display["Progress"] = overdue_display["Progress"].astype(str) + "%"
            overdue_display.columns = ["งาน", "กำหนดเสร็จ", "ผู้รับผิดชอบ", "ความคืบหน้า"]
            st.dataframe(overdue_display, hide_index=True, use_container_width=True)
