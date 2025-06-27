# components/navigation.py
import streamlit as st
from typing import List, Dict, Any


def render_sidebar():
    """Render application sidebar navigation"""

    # App logo/header
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(
            "https://www.streamlit.io/images/brand/streamlit-mark-color.svg", width=40
        )
    with col2:
        st.markdown("### Project Manager")

    st.markdown("---")

    # Navigation menu
    menu_items = [
        {"label": "📊 Dashboard", "key": "Dashboard", "description": "ภาพรวมโปรเจกต์"},
        {"label": "📚 โปรเจกต์", "key": "โปรเจกต์", "description": "จัดการโปรเจกต์"},
        {"label": "✅ งาน", "key": "งาน", "description": "จัดการงาน"},
        {
            "label": "📅 Gantt Chart",
            "key": "Gantt Chart",
            "description": "แผนงานโปรเจกต์",
        },
        {"label": "📈 รายงาน", "key": "รายงาน", "description": "รายงานและวิเคราะห์"},
        {"label": "⚙️ ตั้งค่า", "key": "ตั้งค่า", "description": "การตั้งค่าระบบ"},
    ]

    # Current page selection
    current_page = st.session_state.get("page_selection", "Dashboard")

    st.markdown("### 📋 เมนูหลัก")

    # Render menu items
    for item in menu_items:
        # Create button for each menu item
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button(
                item["label"],
                key=f"nav_{item['key']}",
                help=item["description"],
                use_container_width=True,
                type="primary" if current_page == item["key"] else "secondary",
            ):
                st.session_state["page_selection"] = item["key"]
                st.rerun()

        # Show active indicator
        if current_page == item["key"]:
            with col2:
                st.markdown("🔹")

    st.markdown("---")

    # Quick actions section
    render_quick_actions()

    # App status section
    render_app_status()


def render_quick_actions():
    """Render quick action buttons"""
    st.markdown("### ⚡ ดำเนินการด่วน")

    quick_actions = [
        {"label": "➕ เพิ่มโปรเจกต์", "action": "add_project", "color": "primary"},
        {"label": "📝 เพิ่มงาน", "action": "add_task", "color": "secondary"},
    ]

    for action in quick_actions:
        if st.button(
            action["label"],
            key=f"quick_{action['action']}",
            use_container_width=True,
            type=action["color"],
        ):
            handle_quick_action(action["action"])


def handle_quick_action(action: str):
    """Handle quick action button clicks"""
    if action == "add_project":
        st.session_state["page_selection"] = "โปรเจกต์"
        st.session_state["quick_action"] = "add_project"
        st.rerun()
    elif action == "add_task":
        st.session_state["page_selection"] = "งาน"
        st.session_state["quick_action"] = "add_task"
        st.rerun()


def render_app_status():
    """Render application status indicators"""
    st.markdown("### 📡 สถานะระบบ")

    # Database connection status
    from services.enhanced_db_service import DatabaseService

    try:
        db_status = DatabaseService.test_connection()
        if db_status:
            st.success("🟢 ฐานข้อมูลเชื่อมต่อปกติ")
        else:
            st.error("🔴 ฐานข้อมูลขัดข้อง")
    except:
        st.warning("🟡 ไม่สามารถตรวจสอบฐานข้อมูลได้")

    # Show app version
    st.markdown("---")
    st.caption("Project Manager v2.0")
    st.caption("Enhanced Edition")


def render_breadcrumb(items: List[str]):
    """Render breadcrumb navigation"""
    if not items:
        return

    breadcrumb_html = " > ".join([f"<span>{item}</span>" for item in items])
    st.markdown(
        f"<div class='breadcrumb'>{breadcrumb_html}</div>", unsafe_allow_html=True
    )


def render_page_header(title: str, subtitle: str = "", icon: str = ""):
    """Render consistent page header"""
    header_html = f"""
    <div class="page-header">
        <h1>{icon} {title}</h1>
        {f"<p class='subtitle'>{subtitle}</p>" if subtitle else ""}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_action_buttons(actions: List[Dict[str, Any]]):
    """Render action buttons in a row"""
    if not actions:
        return

    cols = st.columns(len(actions))

    for i, action in enumerate(actions):
        with cols[i]:
            if st.button(
                action["label"],
                key=action.get("key", f"action_{i}"),
                type=action.get("type", "secondary"),
                help=action.get("help", ""),
                use_container_width=True,
            ):
                if "callback" in action and callable(action["callback"]):
                    action["callback"]()


def render_status_indicator(status: str, label: str = ""):
    """Render status indicator with appropriate color"""
    status_colors = {
        "success": "🟢",
        "warning": "🟡",
        "error": "🔴",
        "info": "🔵",
        "planning": "📋",
        "in_progress": "🚀",
        "completed": "✅",
        "on_hold": "⏸️",
        "cancelled": "❌",
    }

    icon = status_colors.get(status.lower().replace(" ", "_"), "⚪")
    display_text = f"{icon} {label}" if label else icon

    return st.markdown(display_text)
