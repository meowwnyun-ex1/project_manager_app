"""
pages/database_admin.py
Database administration page
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json

from modules.ui_components import (
    CardComponent,
    DataTable,
    NotificationManager,
    ModernModal,
)
from modules.auth import require_role, get_current_user
from config.database import DatabaseManager
from utils.error_handler import handle_streamlit_errors, safe_execute
from utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)


class DatabaseAdminPage:
    """Database administration page class"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    @handle_streamlit_errors()
    @monitor_performance("database_admin_page_render")
    @require_role(["Admin"])
    def show(self):
        """Show database administration page"""
        st.title("🗄️ การจัดการฐานข้อมูล")

        # Get current user
        current_user = get_current_user()
        if not current_user:
            st.error("กรุณาเข้าสู่ระบบ")
            return

        # Check admin permission
        if current_user.get("Role") != "Admin":
            st.error("⚠️ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
            return

        # Warning message
        st.warning(
            "⚠️ **คำเตือน:** หน้านี้มีฟังก์ชันที่อาจส่งผลต่อฐานข้อมูลทั้งหมด กรุณาใช้งานด้วยความระมัดระวัง"
        )

        # Admin tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📊 ภาพรวม", "📋 ตาราง", "🔍 Query", "🔄 การดำเนินการ", "📈 การตรวจสอบ"]
        )

        with tab1:
            self._show_database_overview()

        with tab2:
            self._show_table_management()

        with tab3:
            self._show_query_interface()

        with tab4:
            self._show_database_operations()

        with tab5:
            self._show_monitoring_tools()

    def _show_database_overview(self):
        """Show database overview"""
        st.subheader("📊 ภาพรวมฐานข้อมูล")

        # Get database statistics
        db_stats = self._get_database_statistics()

        if db_stats:
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "ขนาดฐานข้อมูล", f"{db_stats.get('database_size_mb', 0):.1f} MB"
                )

            with col2:
                st.metric("จำนวนตาราง", db_stats.get("table_count", 0))

            with col3:
                st.metric("จำนวนเร็กคอร์ดทั้งหมด", f"{db_stats.get('total_records', 0):,}")

            with col4:
                st.metric("การเชื่อมต่อที่ใช้งาน", db_stats.get("active_connections", 0))

            # Table statistics
            st.markdown("### 📋 สถิติตาราง")

            table_stats = db_stats.get("table_statistics", [])
            if table_stats:
                df = pd.DataFrame(table_stats)
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "TableName": "ชื่อตาราง",
                        "RecordCount": st.column_config.NumberColumn(
                            "จำนวนเร็กคอร์ด", format="%d"
                        ),
                        "SizeMB": st.column_config.NumberColumn(
                            "ขนาด (MB)", format="%.2f"
                        ),
                        "LastUpdated": "อัปเดตล่าสุด",
                    },
                )
            else:
                st.info("ไม่สามารถโหลดสถิติตารางได้")

            # Connection status
            st.markdown("### 🔗 สถานะการเชื่อมต่อ")

            connection_info = self._get_connection_info()
            if connection_info:
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**เซิร์ฟเวอร์:** {connection_info.get('server', 'N/A')}")
                    st.write(f"**ฐานข้อมูล:** {connection_info.get('database', 'N/A')}")
                    st.write(f"**เวอร์ชัน:** {connection_info.get('version', 'N/A')}")

                with col2:
                    st.write(
                        f"**สถานะ:** {'🟢 เชื่อมต่อสำเร็จ' if connection_info.get('connected') else '🔴 ไม่สามารถเชื่อมต่อได้'}"
                    )
                    st.write(f"**Ping:** {connection_info.get('ping_ms', 0)} ms")
                    st.write(f"**อัปไทม์:** {connection_info.get('uptime', 'N/A')}")

        else:
            st.error("ไม่สามารถโหลดข้อมูลภาพรวมฐานข้อมูลได้")

    def _show_table_management(self):
        """Show table management interface"""
        st.subheader("📋 การจัดการตาราง")

        # Get table list
        tables = self._get_table_list()

        if tables:
            # Table selector
            col1, col2 = st.columns([2, 1])

            with col1:
                selected_table = st.selectbox("เลือกตาราง", tables)

            with col2:
                if st.button("🔄 รีเฟรช", use_container_width=True):
                    st.rerun()

            if selected_table:
                # Table actions
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("👁️ ดูข้อมูล", use_container_width=True):
                        st.session_state.view_table_data = selected_table

                with col2:
                    if st.button("🏗️ โครงสร้าง", use_container_width=True):
                        st.session_state.view_table_structure = selected_table

                with col3:
                    if st.button("📊 สถิติ", use_container_width=True):
                        st.session_state.view_table_stats = selected_table

                with col4:
                    if st.button("🔧 ดัชนี", use_container_width=True):
                        st.session_state.view_table_indexes = selected_table

                # Show table data if requested
                if st.session_state.get("view_table_data") == selected_table:
                    self._show_table_data(selected_table)

                # Show table structure if requested
                if st.session_state.get("view_table_structure") == selected_table:
                    self._show_table_structure(selected_table)

                # Show table statistics if requested
                if st.session_state.get("view_table_stats") == selected_table:
                    self._show_table_statistics(selected_table)

                # Show table indexes if requested
                if st.session_state.get("view_table_indexes") == selected_table:
                    self._show_table_indexes(selected_table)

    def _show_query_interface(self):
        """Show SQL query interface"""
        st.subheader("🔍 อินเทอร์เฟซ Query")

        # Query input
        st.markdown("### ✏️ เขียน SQL Query")

        # Predefined queries
        col1, col2 = st.columns([3, 1])

        with col1:
            query_text = st.text_area(
                "SQL Query",
                height=200,
                placeholder="SELECT * FROM Users WHERE IsActive = 1;",
                help="กรุณาใช้คำสั่ง SQL ด้วยความระมัดระวัง",
            )

        with col2:
            st.markdown("**ตัวอย่าง Query:**")

            sample_queries = {
                "ผู้ใช้ที่ใช้งานอยู่": "SELECT * FROM Users WHERE IsActive = 1;",
                "โครงการที่กำลังดำเนินการ": "SELECT * FROM Projects WHERE Status IN ('Planning', 'In Progress');",
                "งานที่เลยกำหนด": "SELECT * FROM Tasks WHERE DueDate < GETDATE() AND Status != 'Done';",
                "สถิติผู้ใช้": "SELECT Role, COUNT(*) as Count FROM Users GROUP BY Role;",
                "ข้อมูล Log 24 ชม": "SELECT TOP 100 * FROM AuditLog WHERE ActionDate > DATEADD(day, -1, GETDATE()) ORDER BY ActionDate DESC;",
            }

            for name, query in sample_queries.items():
                if st.button(name, key=f"sample_{name}", use_container_width=True):
                    st.session_state.selected_query = query
                    st.rerun()

        # Apply selected query
        if st.session_state.get("selected_query"):
            query_text = st.session_state.selected_query
            st.session_state.selected_query = None

        # Query execution controls
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            read_only = st.checkbox(
                "อ่านอย่างเดียว (Read-only)", value=True, help="ป้องกันการแก้ไขข้อมูล"
            )

        with col2:
            limit_results = st.number_input(
                "จำกัดผลลัพธ์", min_value=10, max_value=1000, value=100
            )

        # Execute query
        if st.button("▶️ รัน Query", type="primary"):
            if query_text.strip():
                self._execute_query(query_text, read_only, limit_results)
            else:
                st.error("กรุณาใส่ SQL Query")

        # Query history
        st.markdown("### 📜 ประวัติ Query")

        query_history = self._get_query_history()
        if query_history:
            for i, history_item in enumerate(query_history[-10:]):  # Show last 10
                with st.expander(
                    f"🕒 {history_item['timestamp']} - {history_item['query'][:50]}..."
                ):
                    st.code(history_item["query"], language="sql")
                    if history_item.get("success"):
                        st.success(
                            f"✅ สำเร็จ - {history_item.get('rows_affected', 0)} แถว"
                        )
                    else:
                        st.error(
                            f"❌ ข้อผิดพลาด: {history_item.get('error', 'Unknown error')}"
                        )

    def _show_database_operations(self):
        """Show database operations"""
        st.subheader("🔄 การดำเนินการฐานข้อมูล")

        # Backup operations
        st.markdown("### 💾 การสำรองข้อมูล")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔄 สำรองข้อมูล")

            backup_type = st.radio(
                "ประเภทการสำรอง",
                ["Full Backup", "Differential Backup", "Transaction Log Backup"],
            )

            include_schema = st.checkbox("รวมโครงสร้างตาราง", value=True)
            include_data = st.checkbox("รวมข้อมูล", value=True)
            compress_backup = st.checkbox("บีบอัดไฟล์", value=True)

            if st.button("🔄 เริ่มสำรองข้อมูล", type="primary"):
                self._create_database_backup(
                    backup_type, include_schema, include_data, compress_backup
                )

        with col2:
            st.markdown("#### 📂 ไฟล์สำรองที่มีอยู่")

            backup_files = self._get_backup_files()
            if backup_files:
                for backup in backup_files[-5:]:  # Show last 5
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        st.write(f"📁 {backup['filename']}")
                        st.caption(f"ขนาด: {backup['size_mb']:.1f} MB")
                    with col_b:
                        st.write(backup["created_date"])
                    with col_c:
                        if st.button(
                            "📥", key=f"download_backup_{backup['id']}", help="ดาวน์โหลด"
                        ):
                            self._download_backup_file(backup["id"])
            else:
                st.info("ไม่มีไฟล์สำรอง")

        # Maintenance operations
        st.markdown("---")
        st.markdown("### 🛠️ การบำรุงรักษา")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🧹 ทำความสะอาด")

            if st.button("🗑️ ลบ Log เก่า", use_container_width=True):
                days = st.number_input("ลบ Log เก่ากว่า (วัน)", min_value=7, value=30)
                if st.button("ยืนยันการลบ", type="primary"):
                    self._cleanup_old_logs(days)

            if st.button("🧽 ทำความสะอาดตารางชั่วคราว", use_container_width=True):
                self._cleanup_temp_tables()

        with col2:
            st.markdown("#### 🔧 ปรับปรุงประสิทธิภาพ")

            if st.button("📊 อัปเดตสถิติ", use_container_width=True):
                self._update_database_statistics()

            if st.button("🔄 สร้างดัชนีใหม่", use_container_width=True):
                self._rebuild_indexes()

        with col3:
            st.markdown("#### ✅ ตรวจสอบ")

            if st.button("🔍 ตรวจสอบความสมบูรณ์", use_container_width=True):
                self._check_database_integrity()

            if st.button("📈 วิเคราะห์ฐานข้อมูล", use_container_width=True):
                self._analyze_database_performance()

        # User management operations
        st.markdown("---")
        st.markdown("### 👥 จัดการผู้ใช้ระดับฐานข้อมูล")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔐 สิทธิ์การเข้าถึง")

            db_users = self._get_database_users()
            if db_users:
                selected_db_user = st.selectbox("เลือกผู้ใช้ฐานข้อมูล", db_users)

                if selected_db_user:
                    user_permissions = self._get_user_permissions(selected_db_user)
                    st.write(f"**สิทธิ์ของ {selected_db_user}:**")
                    for permission in user_permissions:
                        st.write(f"- {permission}")

        with col2:
            st.markdown("#### 📊 การใช้งาน")

            active_sessions = self._get_active_sessions()
            st.metric("เซสชันที่ใช้งานอยู่", len(active_sessions))

            if active_sessions:
                for session in active_sessions[:5]:  # Show top 5
                    st.write(
                        f"👤 {session['user']} - {session['status']} ({session['duration']})"
                    )

    def _show_monitoring_tools(self):
        """Show monitoring and performance tools"""
        st.subheader("📈 เครื่องมือตรวจสอบ")

        # Performance metrics
        st.markdown("### ⚡ ตัวชี้วัดประสิทธิภาพ")

        perf_metrics = self._get_performance_metrics()

        if perf_metrics:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "CPU Usage",
                    f"{perf_metrics.get('cpu_usage', 0):.1f}%",
                    delta=f"{perf_metrics.get('cpu_delta', 0):+.1f}%",
                )

            with col2:
                st.metric(
                    "Memory Usage",
                    f"{perf_metrics.get('memory_usage', 0):.1f}%",
                    delta=f"{perf_metrics.get('memory_delta', 0):+.1f}%",
                )

            with col3:
                st.metric(
                    "Disk I/O",
                    f"{perf_metrics.get('disk_io', 0):.1f} MB/s",
                    delta=f"{perf_metrics.get('disk_delta', 0):+.1f}",
                )

            with col4:
                st.metric(
                    "Network",
                    f"{perf_metrics.get('network', 0):.1f} MB/s",
                    delta=f"{perf_metrics.get('network_delta', 0):+.1f}",
                )

        # Query performance
        st.markdown("### 🐌 Query ที่ใช้เวลานาน")

        slow_queries = self._get_slow_queries()
        if slow_queries:
            df = pd.DataFrame(slow_queries)
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "query": st.column_config.TextColumn("SQL Query", width="large"),
                    "duration_ms": st.column_config.NumberColumn(
                        "ระยะเวลา (ms)", format="%d"
                    ),
                    "execution_count": st.column_config.NumberColumn(
                        "จำนวนครั้ง", format="%d"
                    ),
                    "last_executed": "ครั้งล่าสุด",
                },
            )
        else:
            st.info("ไม่พบ Query ที่ใช้เวลานาน")

        # Error logs
        st.markdown("### ❌ Log ข้อผิดพลาด")

        error_logs = self._get_error_logs()
        if error_logs:
            for error in error_logs[-10:]:  # Show last 10 errors
                with st.expander(f"🔴 {error['timestamp']} - {error['error_type']}"):
                    st.write(f"**ข้อความ:** {error['message']}")
                    st.write(f"**รายละเอียด:** {error['details']}")
                    if error.get("query"):
                        st.code(error["query"], language="sql")
        else:
            st.success("✅ ไม่พบข้อผิดพลาด")

        # Real-time monitoring
        st.markdown("### 🔄 การตรวจสอบแบบเรียลไทม์")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔄 เริ่มการตรวจสอบ", type="primary"):
                self._start_realtime_monitoring()

        with col2:
            if st.button("⏹️ หยุดการตรวจสอบ"):
                self._stop_realtime_monitoring()

        # Monitoring charts (placeholder)
        if st.session_state.get("monitoring_active", False):
            st.info("📊 กราฟการตรวจสอบแบบเรียลไทม์จะแสดงที่นี่")
            # Here you would implement real-time charts using plotly or other charting libraries

    # Helper methods for database operations
    def _get_database_statistics(self) -> Dict:
        """Get database statistics"""
        return safe_execute(self.db_manager.get_database_statistics, default_return={})

    def _get_connection_info(self) -> Dict:
        """Get database connection information"""
        return safe_execute(self.db_manager.get_connection_info, default_return={})

    def _get_table_list(self) -> List[str]:
        """Get list of tables"""
        return safe_execute(self.db_manager.get_table_list, default_return=[])

    def _show_table_data(self, table_name: str):
        """Show table data"""
        st.markdown(f"### 👁️ ข้อมูลในตาราง: {table_name}")

        # Pagination controls
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            page_size = st.selectbox("แสดงต่อหน้า", [10, 25, 50, 100], index=1)

        with col2:
            page_number = st.number_input("หน้าที่", min_value=1, value=1)

        # Get table data
        table_data = safe_execute(
            self.db_manager.get_table_data,
            table_name,
            page_number,
            page_size,
            default_return=[],
        )

        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)

            # Record count
            total_records = safe_execute(
                self.db_manager.get_table_record_count, table_name, default_return=0
            )
            st.caption(f"แสดง {len(table_data)} จาก {total_records} เร็กคอร์ด")
        else:
            st.info("ไม่มีข้อมูลในตาราง")

    def _show_table_structure(self, table_name: str):
        """Show table structure"""
        st.markdown(f"### 🏗️ โครงสร้างตาราง: {table_name}")

        structure = safe_execute(
            self.db_manager.get_table_structure, table_name, default_return=[]
        )

        if structure:
            df = pd.DataFrame(structure)
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "ColumnName": "ชื่อคอลัมน์",
                    "DataType": "ประเภทข้อมูล",
                    "IsNullable": st.column_config.CheckboxColumn("อนุญาต NULL"),
                    "DefaultValue": "ค่าเริ่มต้น",
                    "IsPrimaryKey": st.column_config.CheckboxColumn("Primary Key"),
                    "IsForeignKey": st.column_config.CheckboxColumn("Foreign Key"),
                },
            )
        else:
            st.error("ไม่สามารถโหลดโครงสร้างตารางได้")

    def _show_table_statistics(self, table_name: str):
        """Show table statistics"""
        st.markdown(f"### 📊 สถิติตาราง: {table_name}")

        stats = safe_execute(
            self.db_manager.get_table_statistics, table_name, default_return={}
        )

        if stats:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("จำนวนเร็กคอร์ด", f"{stats.get('record_count', 0):,}")
                st.metric("ขนาดตาราง", f"{stats.get('table_size_mb', 0):.2f} MB")

            with col2:
                st.metric("จำนวนคอลัมน์", stats.get("column_count", 0))
                st.metric("จำนวนดัชนี", stats.get("index_count", 0))

            with col3:
                st.metric("อัปเดตล่าสุด", stats.get("last_updated", "N/A"))
                st.metric(
                    "Fragmentation", f"{stats.get('fragmentation_percent', 0):.1f}%"
                )

    def _show_table_indexes(self, table_name: str):
        """Show table indexes"""
        st.markdown(f"### 🔧 ดัชนีของตาราง: {table_name}")

        indexes = safe_execute(
            self.db_manager.get_table_indexes, table_name, default_return=[]
        )

        if indexes:
            df = pd.DataFrame(indexes)
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "IndexName": "ชื่อดัชนี",
                    "IndexType": "ประเภท",
                    "Columns": "คอลัมน์",
                    "IsUnique": st.column_config.CheckboxColumn("Unique"),
                    "IsPrimary": st.column_config.CheckboxColumn("Primary"),
                    "FragmentationPercent": st.column_config.ProgressColumn(
                        "Fragmentation %", min_value=0, max_value=100
                    ),
                },
            )
        else:
            st.info("ไม่มีดัชนี")

    def _execute_query(self, query: str, read_only: bool, limit: int):
        """Execute SQL query"""
        try:
            if read_only and not query.strip().upper().startswith("SELECT"):
                st.error("❌ ในโหมด Read-only สามารถใช้คำสั่ง SELECT เท่านั้น")
                return

            # Add limit if it's a SELECT query
            if (
                query.strip().upper().startswith("SELECT")
                and "LIMIT" not in query.upper()
                and "TOP" not in query.upper()
            ):
                query = f"SELECT TOP {limit} * FROM ({query}) AS limited_query"

            result = safe_execute(
                self.db_manager.execute_query,
                query,
                error_message="ไม่สามารถรัน Query ได้",
            )

            if result is not None:
                if isinstance(result, list) and result:
                    # Show results as dataframe
                    df = pd.DataFrame(result)
                    st.success(f"✅ Query สำเร็จ - พบ {len(result)} แถว")
                    st.dataframe(df, use_container_width=True)

                    # Option to download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 ดาวน์โหลดผลลัพธ์ (.csv)",
                        data=csv,
                        file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
                else:
                    st.success("✅ Query ดำเนินการสำเร็จ")

                # Save to query history
                self._save_query_history(query, True)

        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            self._save_query_history(query, False, str(e))

    def _get_query_history(self) -> List[Dict]:
        """Get query execution history"""
        return st.session_state.get("query_history", [])

    def _save_query_history(self, query: str, success: bool, error: str = None):
        """Save query to history"""
        if "query_history" not in st.session_state:
            st.session_state.query_history = []

        history_item = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "success": success,
            "error": error,
        }

        st.session_state.query_history.append(history_item)

        # Keep only last 50 queries
        if len(st.session_state.query_history) > 50:
            st.session_state.query_history = st.session_state.query_history[-50:]

    # Additional helper methods would be implemented here for various database operations
    def _create_database_backup(
        self, backup_type: str, include_schema: bool, include_data: bool, compress: bool
    ):
        """Create database backup"""
        st.info("🔄 การสำรองข้อมูลจะใช้เวลาสักครู่...")
        # Implementation would go here

    def _get_backup_files(self) -> List[Dict]:
        """Get list of backup files"""
        return safe_execute(self.db_manager.get_backup_files, default_return=[])

    def _get_performance_metrics(self) -> Dict:
        """Get database performance metrics"""
        return safe_execute(self.db_manager.get_performance_metrics, default_return={})

    def _get_slow_queries(self) -> List[Dict]:
        """Get slow running queries"""
        return safe_execute(self.db_manager.get_slow_queries, default_return=[])

    def _get_error_logs(self) -> List[Dict]:
        """Get database error logs"""
        return safe_execute(self.db_manager.get_error_logs, default_return=[])

    def _start_realtime_monitoring(self):
        """Start real-time monitoring"""
        st.session_state.monitoring_active = True
        st.success("🔄 เริ่มการตรวจสอบแบบเรียลไทม์")

    def _stop_realtime_monitoring(self):
        """Stop real-time monitoring"""
        st.session_state.monitoring_active = False
        st.info("⏹️ หยุดการตรวจสอบแบบเรียลไทม์")
