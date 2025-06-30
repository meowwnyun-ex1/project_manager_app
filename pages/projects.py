# pages/projects.py
import streamlit as st
from services.enhanced_project_service import ProjectService
from components.forms import create_project_form
from components.tables import TableComponents


def app():
    st.title("📚 จัดการโปรเจกต์")

    # Quick action check
    if st.session_state.get("quick_action") == "add_project":
        st.info("💡 เพิ่มโปรเจกต์ใหม่ได้ที่ด้านล่าง")
        del st.session_state["quick_action"]

    # Add new project section
    st.subheader("➕ เพิ่มโปรเจกต์ใหม่")

    project_form = create_project_form("add_project_form")
    form_data = project_form.render(submit_label="เพิ่มโปรเจกต์")

    if form_data:
        if ProjectService.create_project(form_data):
            st.success(f"เพิ่มโปรเจกต์ '{form_data['project_name']}' สำเร็จ!")
            st.rerun()
        else:
            st.error("เกิดข้อผิดพลาดในการเพิ่มโปรเจกต์")

    st.markdown("---")

    # List all projects
    st.subheader("📋 รายการโปรเจกต์")
    projects_df = ProjectService.get_all_projects()

    if not projects_df.empty:
        # Display projects table
        TableComponents.render_project_table(projects_df)

        st.markdown("---")

        # Edit/Delete project section
        st.subheader("✏️ จัดการโปรเจกต์")

        # Create project selection options
        project_options = {
            f"{row['ProjectName']} (ID: {row['ProjectID']})": row["ProjectID"]
            for _, row in projects_df.iterrows()
        }

        selected_project = st.selectbox(
            "เลือกโปรเจกต์ที่ต้องการแก้ไข/ลบ",
            ["-- เลือกโปรเจกต์ --"] + list(project_options.keys()),
            key="project_selector",
        )

        if selected_project and selected_project != "-- เลือกโปรเจกต์ --":
            project_id = project_options[selected_project]
            project_data = (
                projects_df[projects_df["ProjectID"] == project_id].iloc[0].to_dict()
            )

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### ✏️ แก้ไขโปรเจกต์")
                edit_form = create_project_form("edit_project_form")
                updated_data = edit_form.render(
                    initial_data=project_data, submit_label="🔄 อัปเดตโปรเจกต์"
                )

                if updated_data:
                    if ProjectService.update_project(project_id, updated_data):
                        st.success(
                            f"อัปเดตโปรเจกต์ '{updated_data['project_name']}' สำเร็จ!"
                        )
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาดในการอัปเดตโปรเจกต์")

            with col2:
                st.markdown("#### 🗑️ ลบโปรเจกต์")
                st.warning("⚠️ การลบโปรเจกต์จะลบงานที่เกี่ยวข้องทั้งหมด")

                confirm_delete = st.checkbox(
                    f"ยืนยันการลบโปรเจกต์ '{project_data['ProjectName']}'",
                    key=f"confirm_delete_{project_id}",
                )

                if confirm_delete:
                    if st.button(
                        "🗑️ ลบโปรเจกต์", type="secondary", key=f"delete_btn_{project_id}"
                    ):
                        if ProjectService.delete_project(project_id):
                            st.success("ลบโปรเจกต์สำเร็จ!")
                            st.rerun()
                        else:
                            st.error("เกิดข้อผิดพลาดในการลบโปรเจกต์")

                # Project statistics
                st.markdown("#### 📊 สถิติโปรเจกต์")
                from services.task_service import TaskService

                tasks_df = TaskService.get_tasks_by_project(project_id)

                if not tasks_df.empty:
                    total_tasks = len(tasks_df)
                    completed_tasks = len(tasks_df[tasks_df["Status"] == "Done"])
                    completion_rate = (
                        (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    )

                    st.metric("งานทั้งหมด", total_tasks)
                    st.metric("งานเสร็จแล้ว", completed_tasks)
                    st.metric("ความคืบหน้า", f"{completion_rate:.1f}%")
                else:
                    st.info("ยังไม่มีงานในโปรเจกต์นี้")

    else:
        st.info("ยังไม่มีโปรเจกต์ในระบบ กรุณาเพิ่มโปรเจกต์ใหม่ด้านบน")

        # Show sample data for demonstration
        st.markdown("### 💡 ตัวอย่างโปรเจกต์")
        sample_projects = [
            "🏢 ระบบจัดการบุคลากร",
            "🛒 เว็บไซต์ E-commerce",
            "📱 แอปพลิเคชันมือถือ",
            "🔧 ระบบบำรุงรักษา",
        ]

        for project in sample_projects:
            st.markdown(f"- {project}")

        st.markdown("*เริ่มต้นด้วยการเพิ่มโปรเจกต์แรกของคุณได้เลย!*")
