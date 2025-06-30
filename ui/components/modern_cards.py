"""
🚀 Project Manager Pro v3.0 - Modern Cards
Beautiful, interactive card components with glassmorphism design
"""

import streamlit as st
from typing import Any, Optional, Dict, List
import plotly.graph_objects as go

class ModernCards:
    """Modern card components with glassmorphism and animations"""
    
    def __init__(self):
        self._apply_card_styles()
    
    def _apply_card_styles(self) -> None:
        """Apply CSS styles for modern cards"""
        st.markdown("""
        <style>
        /* Modern Card Styles */
        .modern-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .modern-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 16px 48px 0 rgba(31, 38, 135, 0.5);
            border-color: rgba(255, 255, 255, 0.4);
        }
        
        .modern-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--card-accent-color, #667eea), transparent);
            border-radius: 20px 20px 0 0;
        }
        
        /* Metric Card */
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            text-align: center;
        }
        
        .metric-card:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.5);
        }
        
        .metric-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            display: block;
            animation: pulse 2s infinite;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
            margin: 0.5rem 0;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        
        .metric-title {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .metric-delta {
            font-size: 0.9rem;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-weight: 600;
            display: inline-block;
            margin-top: 0.5rem;
        }
        
        .metric-delta.positive {
            background: rgba(16, 185, 129, 0.2);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .metric-delta.negative {
            background: rgba(239, 68, 68, 0.2);
            color: #EF4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .metric-delta.neutral {
            background: rgba(107, 114, 128, 0.2);
            color: #6B7280;
            border: 1px solid rgba(107, 114, 128, 0.3);
        }
        
        /* Status Card */
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border-radius: 15px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .status-card:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateX(5px);
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
            animation: pulse 2s infinite;
        }
        
        .status-content {
            flex: 1;
        }
        
        .status-title {
            font-weight: 600;
            color: white;
            margin-bottom: 0.25rem;
        }
        
        .status-subtitle {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
        }
        
        /* Progress Card */
        .progress-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .progress-title {
            font-weight: 600;
            color: white;
            font-size: 1.1rem;
        }
        
        .progress-percentage {
            font-weight: 700;
            color: white;
            font-size: 1.2rem;
        }
        
        .progress-bar-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            height: 12px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-bar {
            height: 100%;
            border-radius: 10px;
            background: linear-gradient(90deg, #10B981, #059669);
            transition: width 1s ease-in-out;
            position: relative;
        }
        
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        
        /* Info Card */
        .info-card {
            background: rgba(59, 130, 246, 0.1);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            position: relative;
        }
        
        .info-card::before {
            content: 'ℹ️';
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.5rem;
        }
        
        .warning-card {
            background: rgba(245, 158, 11, 0.1);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            position: relative;
        }
        
        .warning-card::before {
            content: '⚠️';
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.5rem;
        }
        
        .success-card {
            background: rgba(16, 185, 129, 0.1);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            position: relative;
        }
        
        .success-card::before {
            content: '✅';
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.5rem;
        }
        
        .error-card {
            background: rgba(239, 68, 68, 0.1);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            position: relative;
        }
        
        .error-card::before {
            content: '❌';
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 1.5rem;
        }
        
        /* Animations */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translate3d(0, 40px, 0);
            }
            to {
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }
        }
        
        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }
        
        /* Color Variants */
        .card-blue { --card-accent-color: #3B82F6; }
        .card-green { --card-accent-color: #10B981; }
        .card-purple { --card-accent-color: #8B5CF6; }
        .card-red { --card-accent-color: #EF4444; }
        .card-yellow { --card-accent-color: #F59E0B; }
        .card-pink { --card-accent-color: #EC4899; }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .modern-card, .metric-card, .progress-card {
                padding: 1rem;
                margin: 0.5rem 0;
            }
            
            .metric-value {
                font-size: 2rem;
            }
            
            .metric-icon {
                font-size: 2rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def metric_card(self, title: str, value: Any, delta: Optional[float] = None, 
                   icon: str = "📊", color: str = "blue") -> None:
        """Create a modern metric card with glassmorphism effect"""
        
        # Format delta
        delta_class = "neutral"
        delta_text = ""
        if delta is not None:
            if delta > 0:
                delta_class = "positive"
                delta_text = f"↗️ +{delta}"
            elif delta < 0:
                delta_class = "negative"
                delta_text = f"↘️ {delta}"
            else:
                delta_class = "neutral"
                delta_text = "➡️ No change"
        
        st.markdown(f"""
        <div class="metric-card card-{color} fade-in-up">
            <div class="metric-icon">{icon}</div>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-delta {delta_class}">{delta_text}</div>' if delta is not None else ''}
        </div>
        """, unsafe_allow_html=True)
    
    def status_card(self, title: str, subtitle: str, status: str = "active", 
                   icon: str = "🔵") -> None:
        """Create a status indicator card"""
        
        status_colors = {
            "active": "#10B981",
            "pending": "#F59E0B", 
            "completed": "#3B82F6",
            "cancelled": "#EF4444",
            "warning": "#F59E0B"
        }
        
        color = status_colors.get(status, "#6B7280")
        
        st.markdown(f"""
        <div class="status-card fade-in-up">
            <div class="status-indicator" style="background-color: {color}"></div>
            <div class="status-content">
                <div class="status-title">{icon} {title}</div>
                <div class="status-subtitle">{subtitle}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def progress_card(self, title: str, progress: int, subtitle: str = "", 
                     color: str = "green") -> None:
        """Create a progress card with animated progress bar"""
        
        color_gradients = {
            "green": "linear-gradient(90deg, #10B981, #059669)",
            "blue": "linear-gradient(90deg, #3B82F6, #2563EB)",
            "purple": "linear-gradient(90deg, #8B5CF6, #7C3AED)",
            "red": "linear-gradient(90deg, #EF4444, #DC2626)",
            "yellow": "linear-gradient(90deg, #F59E0B, #D97706)"
        }
        
        gradient = color_gradients.get(color, color_gradients["green"])
        
        st.markdown(f"""
        <div class="progress-card fade-in-up">
            <div class="progress-header">
                <div class="progress-title">{title}</div>
                <div class="progress-percentage">{progress}%</div>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {progress}%; background: {gradient}"></div>
            </div>
            {f'<p style="margin-top: 0.5rem; color: rgba(255,255,255,0.8); font-size: 0.9rem;">{subtitle}</p>' if subtitle else ''}
        </div>
        """, unsafe_allow_html=True)
    
    def info_card(self, content: str, card_type: str = "info") -> None:
        """Create an information card with different types"""
        
        st.markdown(f"""
        <div class="{card_type}-card fade-in-up">
            {content}
        </div>
        """, unsafe_allow_html=True)
    
    def feature_card(self, title: str, description: str, icon: str = "⭐", 
                    features: List[str] = None, action_text: str = None,
                    color: str = "blue") -> None:
        """Create a feature showcase card"""
        
        features_html = ""
        if features:
            features_html = "<ul style='margin: 1rem 0; padding-left: 1.5rem;'>"
            for feature in features:
                features_html += f"<li style='margin: 0.5rem 0; color: rgba(255,255,255,0.9);'>{feature}</li>"
            features_html += "</ul>"
        
        action_html = ""
        if action_text:
            action_html = f"""
            <div style="margin-top: 1.5rem;">
                <button style="
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 0.75rem 2rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                ">{action_text}</button>
            </div>
            """
        
        st.markdown(f"""
        <div class="modern-card card-{color} fade-in-up">
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
                <h3 style="color: white; margin-bottom: 1rem; font-size: 1.5rem;">{title}</h3>
                <p style="color: rgba(255,255,255,0.8); margin-bottom: 1rem; line-height: 1.6;">{description}</p>
                {features_html}
                {action_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def stats_grid(self, stats: List[Dict[str, Any]], columns: int = 4) -> None:
        """Create a grid of statistics cards"""
        
        cols = st.columns(columns)
        
        for i, stat in enumerate(stats):
            with cols[i % columns]:
                self.metric_card(
                    title=stat.get('title', 'Metric'),
                    value=stat.get('value', 0),
                    delta=stat.get('delta'),
                    icon=stat.get('icon', '📊'),
                    color=stat.get('color', 'blue')
                )
    
    def comparison_card(self, title: str, current_value: Any, previous_value: Any,
                       label_current: str = "Current", label_previous: str = "Previous",
                       icon: str = "📊") -> None:
        """Create a comparison card showing current vs previous values"""
        
        # Calculate change
        try:
            if isinstance(current_value, (int, float)) and isinstance(previous_value, (int, float)):
                change = current_value - previous_value
                change_percent = (change / previous_value * 100) if previous_value != 0 else 0
                
                if change > 0:
                    change_color = "#10B981"
                    change_icon = "↗️"
                elif change < 0:
                    change_color = "#EF4444"
                    change_icon = "↘️"
                else:
                    change_color = "#6B7280"
                    change_icon = "➡️"
                
                change_text = f"{change_icon} {change:+.1f} ({change_percent:+.1f}%)"
            else:
                change_text = ""
                change_color = "#6B7280"
        except:
            change_text = ""
            change_color = "#6B7280"
        
        st.markdown(f"""
        <div class="modern-card fade-in-up">
            <div style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <h4 style="color: white; margin-bottom: 1rem;">{title}</h4>
                
                <div style="display: flex; justify-content: space-around; margin-bottom: 1rem;">
                    <div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 0.25rem;">{label_current}</div>
                        <div style="color: white; font-size: 1.8rem; font-weight: 700;">{current_value}</div>
                    </div>
                    <div>
                        <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 0.25rem;">{label_previous}</div>
                        <div style="color: rgba(255,255,255,0.8); font-size: 1.5rem; font-weight: 600;">{previous_value}</div>
                    </div>
                </div>
                
                {f'<div style="color: {change_color}; font-weight: 600; font-size: 1rem;">{change_text}</div>' if change_text else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def team_member_card(self, name: str, role: str, avatar: str = "👤",
                        tasks_completed: int = 0, tasks_total: int = 0,
                        status: str = "active") -> None:
        """Create a team member card"""
        
        completion_rate = (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0
        
        status_colors = {
            "active": "#10B981",
            "away": "#F59E0B",
            "busy": "#EF4444",
            "offline": "#6B7280"
        }
        
        status_color = status_colors.get(status, "#6B7280")
        
        st.markdown(f"""
        <div class="modern-card fade-in-up">
            <div style="text-align: center;">
                <div style="position: relative; display: inline-block; margin-bottom: 1rem;">
                    <div style="font-size: 3rem;">{avatar}</div>
                    <div style="
                        position: absolute;
                        bottom: 0;
                        right: 0;
                        width: 16px;
                        height: 16px;
                        background-color: {status_color};
                        border-radius: 50%;
                        border: 2px solid white;
                    "></div>
                </div>
                
                <h4 style="color: white; margin-bottom: 0.25rem; font-size: 1.2rem;">{name}</h4>
                <p style="color: rgba(255,255,255,0.7); margin-bottom: 1rem; font-size: 0.9rem;">{role}</p>
                
                <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: rgba(255,255,255,0.8); font-size: 0.9rem;">Tasks</span>
                        <span style="color: white; font-weight: 600;">{tasks_completed}/{tasks_total}</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 5px; height: 6px; overflow: hidden;">
                        <div style="
                            background: linear-gradient(90deg, #10B981, #059669);
                            height: 100%;
                            width: {completion_rate}%;
                            transition: width 1s ease-in-out;
                        "></div>
                    </div>
                    <div style="text-align: center; margin-top: 0.5rem; color: rgba(255,255,255,0.8); font-size: 0.8rem;">
                        {completion_rate:.1f}% Complete
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def notification_card(self, message: str, notification_type: str = "info",
                         title: str = None, timestamp: str = None,
                         dismissible: bool = True) -> None:
        """Create a notification card"""
        
        type_configs = {
            "info": {"color": "#3B82F6", "icon": "ℹ️"},
            "success": {"color": "#10B981", "icon": "✅"},
            "warning": {"color": "#F59E0B", "icon": "⚠️"},
            "error": {"color": "#EF4444", "icon": "❌"}
        }
        
        config = type_configs.get(notification_type, type_configs["info"])
        
        title_html = f'<h5 style="color: white; margin-bottom: 0.5rem;">{config["icon"]} {title}</h5>' if title else ''
        timestamp_html = f'<div style="color: rgba(255,255,255,0.6); font-size: 0.8rem; margin-top: 0.5rem;">{timestamp}</div>' if timestamp else ''
        
        dismiss_html = '''
        <button style="
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            color: rgba(255,255,255,0.6);
            cursor: pointer;
            font-size: 1.2rem;
        " onclick="this.parentElement.style.display='none'">×</button>
        ''' if dismissible else ''
        
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border: 1px solid {config['color']};
            border-left: 4px solid {config['color']};
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            position: relative;
            animation: fadeInUp 0.6s ease-out;
        ">
            {dismiss_html}
            {title_html}
            <div style="color: rgba(255,255,255,0.9); line-height: 1.5;">{message}</div>
            {timestamp_html}
        </div>
        """, unsafe_allow_html=True)