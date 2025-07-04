#!/usr/bin/env python3
"""
utils/ui_components.py
Reusable UI Components for DENSO Project Manager Pro
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Callable
import base64

class UIComponents:
    """Reusable UI components for consistent design"""
    
    def __init__(self):
        self.primary_color = "#2a5298"
        self.success_color = "#28a745"
        self.warning_color = "#ffc107"
        self.danger_color = "#dc3545"
        self.info_color = "#17a2b8"
    
    def render_page_header(self, title: str, subtitle: str = None, icon: str = ""):
        """Render consistent page header"""
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h1 style="margin: 0; font-size: 2.5rem;">{icon} {title}</h1>
            {f'<p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">{subtitle}</p>' if subtitle else ''}
        </div>
        """, unsafe_allow_html=True)
    
    def render_metric_cards(self, metrics: List[Dict[str, Any]]):
        """Render metric cards in columns"""
        if not metrics:
            return
        
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                self.render_metric_card(
                    title=metric.get('title', ''),
                    value=metric.get('value', ''),
                    delta=metric.get('delta'),
                    delta_color=metric.get('delta_color', 'normal'),
                    icon=metric.get('icon', '📊')
                )
    
    def render_metric_card(self, title: str, value: str, delta: str = None, 
                          delta_color: str = "normal", icon: str = "📊"):
        """Render individual metric card"""
        delta_html = ""
        if delta:
            color = self.success_color if delta_color == "normal" else self.danger_color
            delta_html = f'<div style="color: {color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'
        
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid {self.primary_color};
            text-align: center;
            margin-bottom: 1rem;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-size: 2rem; font-weight: bold; color: {self.primary_color};">{value}</div>
            <div style="color: #666; font-size: 0.9rem; margin-top: 0.5rem;">{title}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)
    
    def render_status_badge(self, status: str, status_map: Dict[str, Dict] = None):
        """Render status badge with color coding"""
        if not status_map:
            status_map = {
                'Active': {'color': self.success_color, 'icon': '✅'},
                'Inactive': {'color': '#6c757d', 'icon': '⏸️'},
                'Planning': {'color': self.info_color, 'icon': '📋'},
                'In Progress': {'color': self.warning_color, 'icon': '🚀'},
                'Completed': {'color': self.success_color, 'icon': '✅'},
                'On Hold': {'color': '#fd7e14', 'icon': '⏸️'},
                'Cancelled': {'color': self.danger_color, 'icon': '❌'},
                'To Do': {'color': '#6c757d', 'icon': '📝'},
                'Review': {'color': '#6f42c1', 'icon': '👀'},
                'Testing': {'color': self.info_color, 'icon': '🧪'},
                'Done': {'color': self.success_color, 'icon': '✅'}
            }
        
        config = status_map.get(status, {'color': '#6c757d', 'icon': '❓'})
        
        return f"""
        <span style="
            background: {config['color']};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            display: inline-block;
        ">
            {config['icon']} {status}
        </span>
        """
    
    def render_priority_badge(self, priority: str):
        """Render priority badge"""
        priority_map = {
            'Low': {'color': self.success_color, 'icon': '🟢'},
            'Medium': {'color': self.warning_color, 'icon': '🟡'},
            'High': {'color': '#fd7e14', 'icon': '🟠'},
            'Critical': {'color': self.danger_color, 'icon': '🔴'}
        }
        
        config = priority_map.get(priority, {'color': '#6c757d', 'icon': '⚪'})
        
        return f"""
        <span style="
            background: {config['color']};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
            display: inline-block;
        ">
            {config['icon']} {priority}
        </span>
        """
    
    def render_progress_bar(self, percentage: float, show_text: bool = True):
        """Render animated progress bar"""
        color = self.success_color if percentage >= 75 else (
            self.warning_color if percentage >= 50 else self.danger_color
        )
        
        progress_html = f"""
        <div style="
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 0.5rem 0;
        ">
            <div style="
                background: {color};
                height: 100%;
                width: {percentage}%;
                border-radius: 10px;
                transition: width 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 0.8rem;
                font-weight: bold;
            ">
                {f'{percentage:.1f}%' if show_text and percentage > 10 else ''}
            </div>
        </div>
        """
        
        st.markdown(progress_html, unsafe_allow_html=True)
    
    def render_data_table(self, data: List[Dict], 
                         title: str = None,
                         actions: List[Dict] = None,
                         search: bool = True,
                         pagination: bool = True,
                         export: bool = True):
        """Render enhanced data table with actions"""
        if title:
            st.subheader(title)
        
        if not data:
            st.info("ไม่มีข้อมูลแสดง")
            return
        
        df = pd.DataFrame(data)
        
        # Search functionality
        if search and len(df) > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 ค้นหา", placeholder="กรอกคำค้นหา...")
            
            if search_term:
                # Search in all string columns
                string_cols = df.select_dtypes(include=['object']).columns
                mask = df[string_cols].astype(str).apply(
                    lambda x: x.str.contains(search_term, case=False, na=False)
                ).any(axis=1)
                df = df[mask]
        
        # Export functionality
        if export and len(df) > 0:
            with col2 if search else st.container():
                if st.button("📥 ส่งออก CSV"):
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">ดาวน์โหลดไฟล์ CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
        
        # Display table
        if len(df) > 0:
            # Add actions column if provided
            if actions:
                for i, row in df.iterrows():
                    cols = st.columns([1] + [0.15] * len(actions))
                    
                    # Display row data
                    with cols[0]:
                        st.write(row.to_dict())
                    
                    # Display action buttons
                    for j, action in enumerate(actions):
                        with cols[j + 1]:
                            if st.button(action['label'], key=f"{action['key']}_{i}"):
                                action['callback'](row)
            else:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("ไม่พบข้อมูลที่ค้นหา")
    
    def render_form_section(self, title: str, content_func: Callable):
        """Render form section with consistent styling"""
        with st.container():
            st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                border-left: 4px solid {self.primary_color};
            ">
                <h4 style="margin: 0 0 1rem 0; color: {self.primary_color};">{title}</h4>
            """, unsafe_allow_html=True)
            
            content_func()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def render_alert(self, message: str, alert_type: str = "info", dismissible: bool = True):
        """Render alert message"""
        alert_configs = {
            'success': {'color': self.success_color, 'icon': '✅'},
            'warning': {'color': self.warning_color, 'icon': '⚠️'},
            'error': {'color': self.danger_color, 'icon': '❌'},
            'info': {'color': self.info_color, 'icon': 'ℹ️'}
        }
        
        config = alert_configs.get(alert_type, alert_configs['info'])
        
        st.markdown(f"""
        <div style="
            background: {config['color']}15;
            border: 1px solid {config['color']};
            color: {config['color']};
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <strong>{config['icon']} {message}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    def render_loading_spinner(self, text: str = "กำลังโหลด..."):
        """Render loading spinner"""
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div style="
                border: 4px solid #f3f3f3;
                border-top: 4px solid {self.primary_color};
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem auto;
            "></div>
            <p>{text}</p>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def render_confirmation_dialog(self, message: str, key: str) -> bool:
        """Render confirmation dialog"""
        with st.expander("⚠️ ยืนยันการดำเนินการ", expanded=True):
            st.warning(message)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                if st.button("✅ ยืนยัน", key=f"confirm_{key}", type="primary"):
                    return True
            
            with col3:
                if st.button("❌ ยกเลิก", key=f"cancel_{key}"):
                    return False
        
        return False
    
    def render_sidebar_filter(self, title: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Render sidebar filter section"""
        with st.sidebar:
            st.markdown(f"### {title}")
            
            filters = {}
            
            for filter_name, filter_config in options.items():
                filter_type = filter_config.get('type', 'selectbox')
                label = filter_config.get('label', filter_name)
                
                if filter_type == 'selectbox':
                    filters[filter_name] = st.selectbox(
                        label,
                        options=filter_config.get('options', []),
                        index=filter_config.get('default_index', 0)
                    )
                elif filter_type == 'multiselect':
                    filters[filter_name] = st.multiselect(
                        label,
                        options=filter_config.get('options', []),
                        default=filter_config.get('default', [])
                    )
                elif filter_type == 'date_range':
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input(
                            f"{label} (เริ่ม)",
                            value=filter_config.get('default_start', date.today())
                        )
                    with col2:
                        end_date = st.date_input(
                            f"{label} (สิ้นสุด)",
                            value=filter_config.get('default_end', date.today())
                        )
                    filters[filter_name] = (start_date, end_date)
                elif filter_type == 'slider':
                    filters[filter_name] = st.slider(
                        label,
                        min_value=filter_config.get('min_value', 0),
                        max_value=filter_config.get('max_value', 100),
                        value=filter_config.get('default_value', 50)
                    )
            
            st.markdown("---")
            return filters
    
    def render_chart_container(self, chart_func: Callable, title: str = None):
        """Render chart with consistent container styling"""
        with st.container():
            if title:
                st.subheader(title)
            
            try:
                chart_func()
            except Exception as e:
                st.error(f"ไม่สามารถแสดงกราฟได้: {e}")
                st.info("ข้อมูลอาจไม่เพียงพอหรือมีปัญหาในการประมวลผล")