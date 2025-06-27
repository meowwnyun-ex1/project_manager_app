# pages/profile.py
import streamlit as st
import pandas as pd
from typing import Dict, Any
from services.task_service import TaskService
from services.enhanced_project_service import ProjectService
from utils.helpers import get_current_user_info, show_error
from utils.formatters import format_date
from components.charts import ChartComponents


def app():
    """User profile and personal dashboard page"""
    st.title("👤 โปรไฟล์ผู้ใช้")

    # Get current user info
    user_info = get_current_user_info()
    if not user_info:
        st.error("ไม่สามารถโหลดข้อมูลผู้ใช้ได้")
        return

    # Create tabs for different sections
    profile_tabs = st.tabs(
        ["📊 ภาพรวมส่วนตัว", "⚙️ ตั้งค่าบัญชี", "📈 สถิติการทำงาน", "📅 งานของฉัน"]
    )

    with profile_tabs[0]:
        render_personal_overview(user_info)

    with profile_tabs[1]:
        render_account_settings(user_info)

    with profile_tabs[2]:
        render_work_statistics(user_info)

    with profile_tabs[3]:
        render_my_tasks(user_info)


def render_personal_overview(user_info: Dict[str, Any]):
    """Render personal overview dashboard"""
    st.subheader(f"👋 สวัสดี, {user_info['username']}!")

    # User basic info card
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin: 1rem 0;
        ">
            <h2 style="margin: 0; color: white;">👤 ข้อมูลผู้ใช้</h2>
            <p style="margin: 0.5rem 0; font-size: 1.2rem;">"""
            + f"{user_info['username']}"
            + """</p>
            <p style="margin: 0; opacity: 0.9;">บทบาท: """
            + f"{user_info['role']}"
            + """</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Quick stats
    user_id = user_info["user_id"]

    # Get user's tasks and projects
    all_tasks = TaskService.get_all_tasks()
    user_tasks = (
        all_tasks[all_tasks["AssigneeID"] == user_id]
        if not all_tasks.empty
        else pd.DataFrame()
    )

    all_projects = ProjectService.get_all_projects()

    # Calculate metrics
    total_tasks = len(user_tasks)
    completed_tasks = (
        len(user_tasks[user_tasks["Status"] == "Done"]) if not user_tasks.empty else 0
    )
    in_progress_tasks = (
        len(user_tasks[user_tasks["Status"] == "In Progress"])
        if not user_tasks.empty
        else 0
    )

    # Projects involved in
    if not user_tasks.empty:
        involved_projects = user_tasks["ProjectID"].nunique()
    else:
        involved_projects = 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("งานทั้งหมด", total_tasks)

    with col2:
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )
        st.metric("อัตราสำเร็จ", f"{completion_rate:.1f}%")

    with col3:
        st.metric("งานที่ดำเนินการ", in_progress_tasks)

    with col4:
        st.metric("โปรเจกต์ที่เกี่ยวข้อง", involved_projects)

    # Recent activity
    st.subheader("📈 กิจกรรมล่าสุด")

    if not user_tasks.empty:
        # Recent tasks (last 5)
        recent_tasks = user_tasks.nlargest(5, "TaskID")[
            ["TaskName", "Status", "Progress", "EndDate"]
        ]
        recent_tasks["EndDate"] = recent_tasks["EndDate"].apply(format_date)
        recent_tasks["Progress"] = recent_tasks["Progress"].apply(lambda x: f"{x}%")
        recent_tasks.columns = ["ชื่องาน", "สถานะ", "ความคืบหน้า", "กำหนดเสร็จ"]

        st.dataframe(recent_tasks, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีงานที่ได้รับมอบหมาย")


def render_account_settings(user_info: Dict[str, Any]):
    """Render account settings page"""
    st.subheader("⚙️ ตั้งค่าบัญชีผู้ใช้")

    # Account information section
    st.markdown("### 📋 ข้อมูลบัญชี")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("ชื่อผู้ใช้", value=user_info["username"], disabled=True)
        st.text_input("บทบาท", value=user_info["role"], disabled=True)

    with col2:
        user_id = user_info["user_id"]
        st.text_input("รหัสผู้ใช้", value=str(user_id), disabled=True)
        st.text_input("วันที่สร้างบัญชี", value="ไม่ระบุ", disabled=True)

    # Password change section
    st.markdown("### 🔐 เปลี่ยนรหัสผ่าน")

    with st.form("change_password_form"):
        current_password = st.text_input("รหัสผ่านปัจจุบัน", type="password")
        new_password = st.text_input("รหัสผ่านใหม่", type="password")
        confirm_password = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")

        if st.form_submit_button("🔄 เปลี่ยนรหัสผ่าน", type="primary"):
            # Validation
            if not all([current_password, new_password, confirm_password]):
                show_error("กรุณากรอกข้อมูลให้ครบถ้วน")
            elif new_password != confirm_password:
                show_error("รหัสผ่านใหม่ไม่ตรงกัน")
            elif len(new_password) < 6:
                show_error("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")
            else:
                # TODO: Implement password change functionality
                st.info("🚧 ฟีเจอร์เปลี่ยนรหัสผ่านอยู่ระหว่างการพัฒนา")

    # Preferences section
    st.markdown("### 🎨 การตั้งค่าส่วนตัว")

    col1, col2 = st.columns(2)

    with col1:
        st.selectbox("ภาษา", ["ไทย", "English"], disabled=True)
        st.selectbox("เขตเวลา", ["Asia/Bangkok"], disabled=True)

    with col2:
        st.selectbox(
            "รูปแบบวันที่", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"], disabled=True
        )
        st.checkbox("การแจ้งเตือนทางอีเมล", disabled=True)

    st.info("💡 การตั้งค่าเหล่านี้จะมีผลในเวอร์ชันถัดไป")


def render_work_statistics(user_info: Dict[str, Any]):
    """Render personal work statistics"""
    st.subheader("📈 สถิติการทำงานส่วนตัว")

    user_id = user_info["user_id"]

    # Get user's task data
    all_tasks = TaskService.get_all_tasks()
    user_tasks = (
        all_tasks[all_tasks["AssigneeID"] == user_id]
        if not all_tasks.empty
        else pd.DataFrame()
    )

    if user_tasks.empty:
        st.info("ยังไม่มีข้อมูลสถิติการทำงาน")
        return

    # Task status distribution
    st.subheader("📊 การกระจายสถานะงาน")

    status_counts = user_tasks["Status"].value_counts()
    status_data = [
        {"Status": status, "Count": count} for status, count in status_counts.items()
    ]

    # Create pie chart
    charts = ChartComponents()
    fig = charts.create_status_pie_chart(status_data, title="สถานะงานของฉัน")
    st.plotly_chart(fig, use_container_width=True)

    # Progress analysis
    st.subheader("📈 วิเคราะห์ความคืบหน้า")

    col1, col2, col3 = st.columns(3)

    with col1:
        avg_progress = user_tasks["Progress"].mean()
        st.metric("ความคืบหน้าเฉลี่ย", f"{avg_progress:.1f}%")

    with col2:
        completed_tasks = len(user_tasks[user_tasks["Status"] == "Done"])
        total_tasks = len(user_tasks)
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )
        st.metric("อัตราการทำงานเสร็จ", f"{completion_rate:.1f}%")

    with col3:
        overdue_tasks = len(
            user_tasks[
                (user_tasks["EndDate"] < pd.Timestamp.now())
                & (user_tasks["Status"] != "Done")
            ]
        )
        st.metric("งานเกินกำหนด", overdue_tasks)

    # Monthly progress trend
    st.subheader("📅 แนวโน้มความคืบหน้ารายเดือน")

    # Create monthly progress data
    user_tasks["Month"] = pd.to_datetime(user_tasks["StartDate"]).dt.to_period("M")
    monthly_stats = (
        user_tasks.groupby("Month")
        .agg({"Progress": "mean", "TaskID": "count"})
        .reset_index()
    )

    if not monthly_stats.empty:
        monthly_stats["Month"] = monthly_stats["Month"].astype(str)

        # Create trend chart
        trend_data = monthly_stats.to_dict("records")
        charts = ChartComponents()
        fig = charts.create_trend_line_chart(
            trend_data, title="แนวโน้มความคืบหน้ารายเดือน", x_col="Month", y_col="Progress"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลแนวโน้มรายเดือน")

    # Performance insights
    st.subheader("💡 ข้อมูลเชิงลึกเกี่ยวกับประสิทธิภาพ")

    insights = []

    # Task completion insights
    if completion_rate >= 80:
        insights.append("🎉 ยอดเยี่ยม! คุณมีอัตราการทำงานเสร็จสูงมาก")
    elif completion_rate >= 60:
        insights.append("👍 ดีมาก! คุณทำงานได้เสร็จตามเป้าหมาย")
    else:
        insights.append("💪 ลองปรับปรุงการบริหารเวลาเพื่อเพิ่มประสิทธิภาพ")

    # Progress insights
    if avg_progress >= 80:
        insights.append("🚀 คุณมีความคืบหน้าในงานอย่างสม่ำเสมอ")
    elif avg_progress >= 50:
        insights.append("📈 ความคืบหน้าอยู่ในระดับดี ควรเพิ่มความเร็วเล็กน้อย")
    else:
        insights.append("⚡ ลองเร่งความคืบหน้าในงานที่ได้รับมอบหมาย")

    # Overdue insights
    if overdue_tasks == 0:
        insights.append("⏰ เยี่ยมมาก! ไม่มีงานเกินกำหนด")
    elif overdue_tasks <= 2:
        insights.append("⚠️ มีงานเกินกำหนดเล็กน้อย ควรจัดลำดับความสำคัญ")
    else:
        insights.append("🔥 ระวัง! มีงานเกินกำหนดหลายรายการ ควรทบทวนแผนงาน")

    for insight in insights:
        st.markdown(f"- {insight}")


def render_my_tasks(user_info: Dict[str, Any]):
    """Render user's personal task management"""
    st.subheader("📅 งานของฉัน")

    user_id = user_info["user_id"]

    # Get user's tasks
    all_tasks = TaskService.get_all_tasks()
    user_tasks = (
        all_tasks[all_tasks["AssigneeID"] == user_id]
        if not all_tasks.empty
        else pd.DataFrame()
    )

    if user_tasks.empty:
        st.info("ยังไม่มีงานที่ได้รับมอบหมาย")
        return

    # Task filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.multiselect(
            "กรองตามสถานะ",
            options=user_tasks["Status"].unique(),
            default=user_tasks["Status"].unique(),
        )

    with col2:
        project_filter = st.multiselect(
            "กรองตามโปรเจกต์",
            options=(
                user_tasks["ProjectName"].unique()
                if "ProjectName" in user_tasks.columns
                else []
            ),
            default=(
                user_tasks["ProjectName"].unique()
                if "ProjectName" in user_tasks.columns
                else []
            ),
        )

    with col3:
        sort_by = st.selectbox(
            "เรียงตาม",
            options=["EndDate", "StartDate", "Progress", "TaskName"],
            format_func=lambda x: {
                "EndDate": "วันที่กำหนดเสร็จ",
                "StartDate": "วันที่เริ่ม",
                "Progress": "ความคืบหน้า",
                "TaskName": "ชื่องาน",
            }[x],
        )

    # Apply filters
    filtered_tasks = user_tasks[
        (user_tasks["Status"].isin(status_filter))
        & (
            user_tasks["ProjectName"].isin(project_filter)
            if "ProjectName" in user_tasks.columns
            else True
        )
    ].copy()

    # Sort tasks
    if sort_by in filtered_tasks.columns:
        filtered_tasks = filtered_tasks.sort_values(sort_by)

    # Display tasks
    if filtered_tasks.empty:
        st.warning("ไม่มีงานที่ตรงกับเงื่อนไขที่เลือก")
        return

    # Task priority sections
    now = pd.Timestamp.now()

    # Overdue tasks
    overdue_tasks = filtered_tasks[
        (filtered_tasks["EndDate"] < now) & (filtered_tasks["Status"] != "Done")
    ]

    # Due soon (within 3 days)
    due_soon = filtered_tasks[
        (filtered_tasks["EndDate"] >= now)
        & (filtered_tasks["EndDate"] <= now + pd.Timedelta(days=3))
        & (filtered_tasks["Status"] != "Done")
    ]

    # Other tasks
    other_tasks = filtered_tasks[
        ~filtered_tasks.index.isin(overdue_tasks.index)
        & ~filtered_tasks.index.isin(due_soon.index)
    ]

    # Display task sections
    if not overdue_tasks.empty:
        st.markdown("### 🔴 งานเกินกำหนด")
        render_task_cards(overdue_tasks, "overdue")

    if not due_soon.empty:
        st.markdown("### 🟡 งานที่ใกล้ครบกำหนด")
        render_task_cards(due_soon, "due_soon")

    if not other_tasks.empty:
        st.markdown("### 🟢 งานอื่นๆ")
        render_task_cards(other_tasks, "normal")


def render_task_cards(tasks_df: pd.DataFrame, priority_type: str):
    """Render task cards with different styling based on priority"""
    for _, task in tasks_df.iterrows():
        # Determine card color based on priority
        if priority_type == "overdue":
            border_color = "#dc3545"  # Red
        elif priority_type == "due_soon":
            border_color = "#ffc107"  # Yellow
        else:
            border_color = "#28a745"  # Green

        # Calculate days until due
        days_until_due = (task["EndDate"] - pd.Timestamp.now()).days

        # Create task card
        with st.container():
            st.markdown(
                f"""
            <div style="
                border-left: 4px solid {border_color};
                padding: 1rem;
                margin: 0.5rem 0;
                background-color: #f8f9fa;
                border-radius: 0 8px 8px 0;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: #333;">{task['TaskName']}</h4>
                <p style="margin: 0 0 0.5rem 0; color: #666;">โปรเจกต์: {task.get('ProjectName', 'ไม่ระบุ')}</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #666;">สถานะ: <strong>{task['Status']}</strong></span>
                    <span style="color: #666;">ความคืบหน้า: <strong>{task['Progress']}%</strong></span>
                    <span style="color: #666;">กำหนดเสร็จ: <strong>{format_date(task['EndDate'])}</strong></span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Quick action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button(f"📝 แก้ไข", key=f"edit_{task['TaskID']}"):
                    st.session_state["selected_task_id"] = task["TaskID"]
                    st.session_state["page_selection"] = "งาน"
                    st.rerun()

            with col2:
                if task["Status"] != "Done":
                    if st.button(f"✅ ทำเสร็จ", key=f"complete_{task['TaskID']}"):
                        # TODO: Implement quick task completion
                        st.success(f"งาน '{task['TaskName']}' ทำเสร็จแล้ว!")

            with col3:
                if task["Progress"] < 100:
                    new_progress = st.slider(
                        "อัปเดตความคืบหน้า",
                        0,
                        100,
                        int(task["Progress"]),
                        key=f"progress_{task['TaskID']}",
                        label_visibility="collapsed",
                    )
                    if new_progress != task["Progress"]:
                        # TODO: Implement progress update
                        st.info(f"ความคืบหน้าจะถูกอัปเดตเป็น {new_progress}%")

            with col4:
                if days_until_due < 0:
                    st.markdown("🔴 **เกินกำหนด**")
                elif days_until_due <= 1:
                    st.markdown("🟡 **ครบกำหนดเร็วๆ นี้**")
                else:
                    st.markdown(f"⏰ อีก {days_until_due} วัน")
