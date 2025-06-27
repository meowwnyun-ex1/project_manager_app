# components/tables.py
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from utils.formatters import (
    format_date,
    format_percentage,
    format_status_badge,
    truncate_text,
)


class TableComponents:
    """Reusable table components with enhanced functionality"""

    @staticmethod
    def render_data_table(
        data: pd.DataFrame,
        title: str = "",
        searchable: bool = True,
        sortable: bool = True,
        paginated: bool = True,
        page_size: int = 10,
        column_config: Optional[Dict] = None,
    ) -> pd.DataFrame:
        """Render enhanced data table with search, sort, and pagination"""

        if data.empty:
            st.info("ไม่มีข้อมูลที่จะแสดง")
            return data

        # Title
        if title:
            st.subheader(title)

        # Search functionality
        filtered_data = data.copy()
        if searchable and len(data) > 5:
            search_term = st.text_input("🔍 ค้นหา", placeholder="กรอกคำค้นหา...")
            if search_term:
                # Search across all string columns
                string_cols = data.select_dtypes(include=["object"]).columns
                mask = (
                    data[string_cols]
                    .astype(str)
                    .apply(lambda x: x.str.contains(search_term, case=False, na=False))
                    .any(axis=1)
                )
                filtered_data = data[mask]

        # Pagination
        if paginated and len(filtered_data) > page_size:
            total_pages = (len(filtered_data) - 1) // page_size + 1
            page = st.selectbox(
                f"หน้า (แสดง {len(filtered_data)} รายการ)",
                range(1, total_pages + 1),
                format_func=lambda x: f"หน้า {x} of {total_pages}",
            )
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, len(filtered_data))
            display_data = filtered_data.iloc[start_idx:end_idx]
        else:
            display_data = filtered_data

        # Column configuration
        if column_config:
            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
            )
        else:
            st.dataframe(display_data, use_container_width=True, hide_index=True)

        return display_data

    @staticmethod
    def render_project_table(projects_df: pd.DataFrame) -> None:
        """Render formatted project table"""
        if projects_df.empty:
            st.info("ไม่มีโปรเจกต์ในระบบ")
            return

        # Format data for display
        display_df = projects_df.copy()

        # Format dates
        if "StartDate" in display_df.columns:
            display_df["StartDate"] = display_df["StartDate"].apply(format_date)
        if "EndDate" in display_df.columns:
            display_df["EndDate"] = display_df["EndDate"].apply(format_date)

        # Format status with badges
        if "Status" in display_df.columns:
            display_df["Status"] = display_df["Status"].apply(format_status_badge)

        # Truncate long descriptions
        if "Description" in display_df.columns:
            display_df["Description"] = display_df["Description"].apply(
                lambda x: truncate_text(x, 100)
            )

        # Column configuration
        column_config = {
            "ProjectID": st.column_config.NumberColumn("ID", width="small"),
            "ProjectName": st.column_config.TextColumn("ชื่อโปรเจกต์", width="medium"),
            "Description": st.column_config.TextColumn("คำอธิบาย", width="large"),
            "StartDate": st.column_config.TextColumn("วันที่เริ่ม", width="small"),
            "EndDate": st.column_config.TextColumn("วันที่สิ้นสุด", width="small"),
            "Status": st.column_config.TextColumn("สถานะ", width="small"),
        }

        TableComponents.render_data_table(
            display_df, title="📚 รายการโปรเจกต์", column_config=column_config
        )

    @staticmethod
    def render_task_table(tasks_df: pd.DataFrame) -> None:
        """Render formatted task table"""
        if tasks_df.empty:
            st.info("ไม่มีงานในระบบ")
            return

        # Format data for display
        display_df = tasks_df.copy()

        # Format dates
        date_columns = ["StartDate", "EndDate"]
        for col in date_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(format_date)

        # Format progress
        if "Progress" in display_df.columns:
            display_df["Progress"] = display_df["Progress"].apply(
                lambda x: format_percentage(x) if pd.notna(x) else "0%"
            )

        # Format status
        if "Status" in display_df.columns:
            display_df["Status"] = display_df["Status"].apply(format_status_badge)

        # Truncate task names and descriptions
        if "TaskName" in display_df.columns:
            display_df["TaskName"] = display_df["TaskName"].apply(
                lambda x: truncate_text(x, 50)
            )
        if "Description" in display_df.columns:
            display_df["Description"] = display_df["Description"].apply(
                lambda x: truncate_text(x, 80)
            )

        # Column configuration
        column_config = {
            "TaskID": st.column_config.NumberColumn("ID", width="small"),
            "TaskName": st.column_config.TextColumn("ชื่องาน", width="medium"),
            "Description": st.column_config.TextColumn("คำอธิบาย", width="large"),
            "StartDate": st.column_config.TextColumn("วันเริ่ม", width="small"),
            "EndDate": st.column_config.TextColumn("วันสิ้นสุด", width="small"),
            "Assignee": st.column_config.TextColumn("ผู้รับผิดชอบ", width="small"),
            "Status": st.column_config.TextColumn("สถานะ", width="small"),
            "Progress": st.column_config.TextColumn("ความคืบหน้า", width="small"),
        }

        TableComponents.render_data_table(
            display_df, title="✅ รายการงาน", column_config=column_config
        )

    @staticmethod
    def render_user_table(users_df: pd.DataFrame) -> None:
        """Render formatted user table"""
        if users_df.empty:
            st.info("ไม่มีผู้ใช้ในระบบ")
            return

        # Format data for display
        display_df = users_df.copy()

        # Format created date
        if "CreatedDate" in display_df.columns:
            display_df["CreatedDate"] = display_df["CreatedDate"].apply(format_date)

        # Format role with emoji
        if "Role" in display_df.columns:
            role_emoji = {"Admin": "👑", "Manager": "👨‍💼", "User": "👤"}
            display_df["Role"] = display_df["Role"].apply(
                lambda x: f"{role_emoji.get(x, '👤')} {x}"
            )

        # Column configuration
        column_config = {
            "UserID": st.column_config.NumberColumn("ID", width="small"),
            "Username": st.column_config.TextColumn("ชื่อผู้ใช้", width="medium"),
            "Role": st.column_config.TextColumn("บทบาท", width="small"),
            "CreatedDate": st.column_config.TextColumn("วันที่สร้าง", width="small"),
        }

        TableComponents.render_data_table(
            display_df, title="👥 รายการผู้ใช้", column_config=column_config
        )

    @staticmethod
    def render_actionable_table(
        data: pd.DataFrame,
        title: str = "",
        actions: List[Dict[str, Any]] = None,
        id_column: str = "ID",
    ) -> Optional[Dict[str, Any]]:
        """Render table with action buttons"""

        if data.empty:
            st.info("ไม่มีข้อมูลที่จะแสดง")
            return None

        if title:
            st.subheader(title)

        # Display the table
        st.dataframe(data, use_container_width=True, hide_index=True)

        if not actions:
            return None

        # Action section
        st.subheader("การดำเนินการ")

        # Selection
        if id_column in data.columns:
            options = {
                f"{row[id_column]} - {row.get('Name', row.get('TaskName', row.get('ProjectName', 'Item')))}": row[
                    id_column
                ]
                for _, row in data.iterrows()
            }

            selected_item = st.selectbox(
                "เลือกรายการ",
                [""] + list(options.keys()),
                format_func=lambda x: "-- เลือก --" if x == "" else x,
            )

            if selected_item and selected_item != "":
                selected_id = options[selected_item]
                selected_data = data[data[id_column] == selected_id].iloc[0].to_dict()

                # Action buttons
                cols = st.columns(len(actions))
                for i, action in enumerate(actions):
                    with cols[i]:
                        if st.button(
                            action["label"],
                            key=f"action_{action['key']}_{selected_id}",
                            type=action.get("type", "secondary"),
                        ):
                            return {
                                "action": action["key"],
                                "selected_id": selected_id,
                                "selected_data": selected_data,
                            }

        return None

    @staticmethod
    def render_summary_table(data: Dict[str, Any], title: str = "สรุปข้อมูล") -> None:
        """Render summary statistics table"""
        if not data:
            st.info("ไม่มีข้อมูลสรุป")
            return

        st.subheader(title)

        # Convert to DataFrame for display
        summary_data = []
        for key, value in data.items():
            if isinstance(value, (int, float, str)):
                summary_data.append(
                    {"รายการ": key.replace("_", " ").title(), "ค่า": str(value)}
                )

        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    @staticmethod
    def render_comparison_table(
        data1: pd.DataFrame,
        data2: pd.DataFrame,
        labels: List[str] = ["Before", "After"],
        title: str = "การเปรียบเทียบ",
    ) -> None:
        """Render side-by-side comparison table"""
        st.subheader(title)

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**{labels[0]}**")
            if not data1.empty:
                st.dataframe(data1, use_container_width=True, hide_index=True)
            else:
                st.info("ไม่มีข้อมูล")

        with col2:
            st.write(f"**{labels[1]}**")
            if not data2.empty:
                st.dataframe(data2, use_container_width=True, hide_index=True)
            else:
                st.info("ไม่มีข้อมูล")


# Helper functions for quick table rendering
def quick_project_table(projects_df: pd.DataFrame) -> None:
    """Quick project table rendering"""
    TableComponents.render_project_table(projects_df)


def quick_task_table(tasks_df: pd.DataFrame) -> None:
    """Quick task table rendering"""
    TableComponents.render_task_table(tasks_df)


def quick_user_table(users_df: pd.DataFrame) -> None:
    """Quick user table rendering"""
    TableComponents.render_user_table(users_df)
