# pages/tasks.py
import streamlit as st
from services.enhanced_project_service import ProjectService
from services.task_service import TaskService
from services.user_service import UserService
from components.forms import create_task_form
from components.tables import TableComponents


def app():
    st.title("✅ จัดการงาน")

    # Quick action check
    if st.session_state.get("quick_action") == "add_task":
        st.info("💡 เพิ่มงานใหม่ได้ที่ด้านล่าง")
        del st.session_state["quick_action"]

    # Get required data
    projects_df = ProjectService.get_all_projects()
    users_data = UserService.get_all_users()

    if projects_df.empty:
        st.warning("⚠️ ไม่มีโปรเจกต์ในระบบ กรุณาเพิ่มโปรเจกต์ก่อนจึงจะสามารถเพิ่มงานได้")
        if st.button("➕ ไปเพิ่มโปรเจกต์"):
            st.session_state["page_selection"] = "โปรเจกต์"
            st.rerun()
        return

    if not users_data:
        st.warning("⚠️ ไม่มีผู้ใช้ในระบบ ไม่สามารถมอบหมายงานได้")
        return

    # Project selection for task management
    st.subheader("📋 เลือกโปรเจกต์")
    project_options = {
        row["ProjectName"]: row["ProjectID"] for _, row in projects_df.iterrows()
    }

    selected_project_name = st.selectbox(
        "เลือกโปรเจกต์สำหรับจัดการงาน",
        list(project_options.keys()),
        key="task_project_selector",
    )

    selected_project_id = project_options[selected_project_name]

    # Add new task section
    st.subheader(f"➕ เพิ่มงานใหม่สำหรับ: {selected_project_name}")

    task_form = create_task_form("add_task_form")
    form_data = task_form.render(
        project_id=selected_project_id, users=users_data, submit_label="เพิ่มงาน"
    )

    if form_data:
        if TaskService.create_task(form_data):
            st.success(f"เพิ่มงาน '{form_data['task_name']}' สำเร็จ!")
            st.rerun()
        else:
            st.error("เกิดข้อผิดพลาดในการเพิ่มงาน")

    st.markdown("---")

    # Display tasks for selected project
    st.subheader(f"📝 รายการงานของโปรเจกต์: {selected_project_name}")

    tasks_df = TaskService.get_tasks_by_project(selected_project_id)

    if not tasks_df.empty:
        # Task filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.multiselect(
                "กรองตามสถานะ",
                options=tasks_df["Status"].unique(),
                default=tasks_df["Status"].unique(),
                key="task_status_filter",
            )

        with col2:
            assignee_filter = st.multiselect(
                "กรองตามผู้รับผิดชอบ",
                options=tasks_df["Assignee"].dropna().unique(),
                default=tasks_df["Assignee"].dropna().unique(),
                key="task_assignee_filter",
            )

        with col3:
            sort_by = st.selectbox(
                "เรียงตาม",
                ["EndDate", "StartDate", "Progress", "TaskName"],
                format_func=lambda x: {
                    "EndDate": "วันที่กำหนดเสร็จ",
                    "StartDate": "วันที่เริ่ม",
                    "Progress": "ความคืบหน้า",
                    "TaskName": "ชื่องาน",
                }[x],
                key="task_sort_selector",
            )

        # Apply filters
        filtered_tasks = tasks_df[
            (tasks_df["Status"].isin(status_filter))
            & (tasks_df["Assignee"].isin(assignee_filter))
        ].copy()

        if sort_by in filtered_tasks.columns:
            filtered_tasks = filtered_tasks.sort_values(sort_by)

        # Display filtered tasks
        if not filtered_tasks.empty:
            TableComponents.render_task_table(filtered_tasks)

            # Task management section
            st.markdown("---")
            st.subheader("✏️ จัดการงาน")

            # Task selection for edit/delete
            task_options = {
                f"{row['TaskName']} (ID: {row['TaskID']})": row["TaskID"]
                for _, row in filtered_tasks.iterrows()
            }

            selected_task = st.selectbox(
                "เลือกงานที่ต้องการแก้ไข/ลบ",
                ["-- เลือกงาน --"] + list(task_options.keys()),
                key="task_management_selector",
            )

            if selected_task and selected_task != "-- เลือกงาน --":
                task_id = task_options[selected_task]
                task_data = (
                    filtered_tasks[filtered_tasks["TaskID"] == task_id]
                    .iloc[0]
                    .to_dict()
                )

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("#### ✏️ แก้ไขงาน")
                    edit_form = create_task_form("edit_task_form")
                    updated_data = edit_form.render(
                        project_id=selected_project_id,
                        users=users_data,
                        initial_data=task_data,
                        submit_label="🔄 อัปเดตงาน",
                    )

                    if updated_data:
                        if TaskService.update_task(task_id, updated_data):
                            st.success(f"อัปเดตงาน '{updated_data['task_name']}' สำเร็จ!")
                            st.rerun()
                        else:
                            st.error("เกิดข้อผิดพลาดในการอัปเดตงาน")

                with col2:
                    st.markdown("#### 🗑️ ลบงาน")
                    st.warning("⚠️ การลบงานไม่สามารถยกเลิกได้")

                    confirm_delete = st.checkbox(
                        f"ยืนยันการลบงาน '{task_data['TaskName']}'",
                        key=f"confirm_delete_task_{task_id}",
                    )

                    if confirm_delete:
                        if st.button(
                            "🗑️ ลบงาน",
                            type="secondary",
                            key=f"delete_task_btn_{task_id}",
                        ):
                            if TaskService.delete_task(task_id):
                                st.success("ลบงานสำเร็จ!")
                                st.rerun()
                            else:
                                st.error("เกิดข้อผิดพลาดในการลบงาน")

                    # Task details
                    st.markdown("#### 📊 รายละเอียดงาน")
                    st.write(f"**สถานะ:** {task_data['Status']}")
                    st.write(f"**ความคืบหน้า:** {task_data['Progress']}%")
                    st.write(f"**ผู้รับผิดชอบ:** {task_data['Assignee']}")

                    # Progress update shortcut
                    if task_data["Status"] != "Done":
                        st.markdown("#### ⚡ อัปเดตด่วน")
                        new_progress = st.slider(
                            "ความคืบหน้า",
                            0,
                            100,
                            int(task_data["Progress"]),
                            key=f"quick_progress_{task_id}",
                        )

                        if st.button(
                            "💾 บันทึกความคืบหน้า", key=f"save_progress_{task_id}"
                        ):
                            quick_update_data = task_data.copy()
                            quick_update_data.update(
                                {
                                    "project_id": selected_project_id,
                                    "task_name": task_data["TaskName"],
                                    "description": task_data["Description"],
                                    "start_date": task_data["StartDate"],
                                    "end_date": task_data["EndDate"],
                                    "assignee_id": task_data["AssigneeID"],
                                    "status": (
                                        "Done"
                                        if new_progress == 100
                                        else task_data["Status"]
                                    ),
                                    "progress": new_progress,
                                }
                            )

                            if TaskService.update_task(task_id, quick_update_data):
                                st.success("อัปเดตความคืบหน้าสำเร็จ!")
                                st.rerun()
        else:
            st.warning("ไม่มีงานที่ตรงกับเงื่อนไขที่เลือก")

    else:
        st.info(f"ยังไม่มีงานสำหรับโปรเจกต์ '{selected_project_name}' กรุณาเพิ่มงานใหม่ด้านบน")

        # Show sample tasks for guidance
        st.markdown("### 💡 ตัวอย่างงาน")
        sample_tasks = [
            "📋 วิเคราะห์ความต้องการ",
            "🎨 ออกแบบ UI/UX",
            "💻 พัฒนาระบบ Backend",
            "🌐 พัฒนาระบบ Frontend",
            "🧪 ทดสอบระบบ",
            "📚 เขียน Documentation",
            "🚀 Deploy ระบบ",
        ]

        for task in sample_tasks:
            st.markdown(f"- {task}")

    # Quick statistics
    if not tasks_df.empty:
        st.markdown("---")
        st.subheader("📈 สถิติงานโปรเจกต์")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_tasks = len(tasks_df)
            st.metric("งานทั้งหมด", total_tasks)

        with col2:
            completed_tasks = len(tasks_df[tasks_df["Status"] == "Done"])
            st.metric("งานเสร็จแล้ว", completed_tasks)

        with col3:
            if total_tasks > 0:
                completion_rate = (completed_tasks / total_tasks) * 100
                st.metric("อัตราความสำเร็จ", f"{completion_rate:.1f}%")
            else:
                st.metric("อัตราความสำเร็จ", "0%")

        with col4:
            avg_progress = tasks_df["Progress"].mean()
            st.metric("ความคืบหน้าเฉลี่ย", f"{avg_progress:.1f}%")
