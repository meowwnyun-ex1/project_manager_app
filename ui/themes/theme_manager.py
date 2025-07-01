# ui/themes/theme_manager.py
import streamlit as st
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json


class ThemeMode(Enum):
    """Theme modes"""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ColorScheme(Enum):
    """Color schemes"""

    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    PINK = "pink"
    ORANGE = "orange"
    TEAL = "teal"
    INDIGO = "indigo"
    RED = "red"


class ThemeManager:
    """Advanced theme management system"""

    def __init__(self):
        self.themes = self._load_themes()
        self.current_theme = self._get_current_theme()

        # Initialize session state
        if "theme_mode" not in st.session_state:
            st.session_state.theme_mode = ThemeMode.AUTO.value
        if "color_scheme" not in st.session_state:
            st.session_state.color_scheme = ColorScheme.BLUE.value
        if "custom_theme" not in st.session_state:
            st.session_state.custom_theme = {}

    def _load_themes(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined themes"""
        return {
            "light": {
                "primary_color": "#3b82f6",
                "secondary_color": "#64748b",
                "success_color": "#10b981",
                "warning_color": "#f59e0b",
                "error_color": "#ef4444",
                "info_color": "#06b6d4",
                "background_color": "#ffffff",
                "surface_color": "#f8fafc",
                "text_color": "#1f2937",
                "text_secondary": "#6b7280",
                "border_color": "#e5e7eb",
                "shadow_color": "rgba(0, 0, 0, 0.1)",
                "glass_background": "rgba(255, 255, 255, 0.9)",
                "glass_border": "rgba(255, 255, 255, 0.2)",
            },
            "dark": {
                "primary_color": "#60a5fa",
                "secondary_color": "#94a3b8",
                "success_color": "#34d399",
                "warning_color": "#fbbf24",
                "error_color": "#f87171",
                "info_color": "#22d3ee",
                "background_color": "#0f172a",
                "surface_color": "#1e293b",
                "text_color": "#f1f5f9",
                "text_secondary": "#94a3b8",
                "border_color": "#334155",
                "shadow_color": "rgba(0, 0, 0, 0.3)",
                "glass_background": "rgba(15, 23, 42, 0.9)",
                "glass_border": "rgba(255, 255, 255, 0.1)",
            },
        }

    def _get_current_theme(self) -> Dict[str, Any]:
        """Get current theme based on mode"""
        mode = st.session_state.get("theme_mode", ThemeMode.AUTO.value)

        if mode == ThemeMode.AUTO.value:
            # Auto-detect based on system preference (simplified)
            mode = ThemeMode.LIGHT.value

        base_theme = self.themes.get(mode, self.themes["light"])

        # Apply color scheme
        color_scheme = st.session_state.get("color_scheme", ColorScheme.BLUE.value)
        themed_colors = self._apply_color_scheme(base_theme, color_scheme)

        # Apply custom overrides
        custom_theme = st.session_state.get("custom_theme", {})
        themed_colors.update(custom_theme)

        return themed_colors

    def _apply_color_scheme(
        self, base_theme: Dict[str, Any], scheme: str
    ) -> Dict[str, Any]:
        """Apply color scheme to base theme"""

        color_schemes = {
            ColorScheme.BLUE.value: {
                "primary_color": "#3b82f6",
                "primary_gradient": "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
                "secondary_gradient": "linear-gradient(135deg, #64748b 0%, #475569 100%)",
                "accent_color": "#3b82f6",
            },
            ColorScheme.GREEN.value: {
                "primary_color": "#10b981",
                "primary_gradient": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                "secondary_gradient": "linear-gradient(135deg, #6b7280 0%, #4b5563 100%)",
                "accent_color": "#10b981",
            },
            ColorScheme.PURPLE.value: {
                "primary_color": "#8b5cf6",
                "primary_gradient": "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",
                "secondary_gradient": "linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)",
                "accent_color": "#8b5cf6",
            },
            ColorScheme.PINK.value: {
                "primary_color": "#ec4899",
                "primary_gradient": "linear-gradient(135deg, #ec4899 0%, #db2777 100%)",
                "secondary_gradient": "linear-gradient(135deg, #f472b6 0%, #ec4899 100%)",
                "accent_color": "#ec4899",
            },
            ColorScheme.ORANGE.value: {
                "primary_color": "#f97316",
                "primary_gradient": "linear-gradient(135deg, #f97316 0%, #ea580c 100%)",
                "secondary_gradient": "linear-gradient(135deg, #fb923c 0%, #f97316 100%)",
                "accent_color": "#f97316",
            },
            ColorScheme.TEAL.value: {
                "primary_color": "#14b8a6",
                "primary_gradient": "linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)",
                "secondary_gradient": "linear-gradient(135deg, #5eead4 0%, #2dd4bf 100%)",
                "accent_color": "#14b8a6",
            },
            ColorScheme.INDIGO.value: {
                "primary_color": "#6366f1",
                "primary_gradient": "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                "secondary_gradient": "linear-gradient(135deg, #a5b4fc 0%, #818cf8 100%)",
                "accent_color": "#6366f1",
            },
            ColorScheme.RED.value: {
                "primary_color": "#ef4444",
                "primary_gradient": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
                "secondary_gradient": "linear-gradient(135deg, #f87171 0%, #ef4444 100%)",
                "accent_color": "#ef4444",
            },
        }

        scheme_colors = color_schemes.get(scheme, color_schemes[ColorScheme.BLUE.value])

        # Update base theme with scheme colors
        updated_theme = base_theme.copy()
        updated_theme.update(scheme_colors)

        return updated_theme

    def set_theme_mode(self, mode: ThemeMode):
        """Set theme mode"""
        st.session_state.theme_mode = mode.value
        self.current_theme = self._get_current_theme()

    def set_color_scheme(self, scheme: ColorScheme):
        """Set color scheme"""
        st.session_state.color_scheme = scheme.value
        self.current_theme = self._get_current_theme()

    def update_custom_theme(self, custom_colors: Dict[str, str]):
        """Update custom theme colors"""
        if "custom_theme" not in st.session_state:
            st.session_state.custom_theme = {}

        st.session_state.custom_theme.update(custom_colors)
        self.current_theme = self._get_current_theme()

    def get_theme_css(self) -> str:
        """Generate CSS for current theme"""
        theme = self.current_theme

        return f"""
        <style>
        :root {{
            --primary-color: {theme['primary_color']};
            --secondary-color: {theme['secondary_color']};
            --success-color: {theme['success_color']};
            --warning-color: {theme['warning_color']};
            --error-color: {theme['error_color']};
            --info-color: {theme['info_color']};
            --background-color: {theme['background_color']};
            --surface-color: {theme['surface_color']};
            --text-color: {theme['text_color']};
            --text-secondary: {theme['text_secondary']};
            --border-color: {theme['border_color']};
            --shadow-color: {theme['shadow_color']};
            --glass-background: {theme['glass_background']};
            --glass-border: {theme['glass_border']};
            --primary-gradient: {theme.get('primary_gradient', f'linear-gradient(135deg, {theme["primary_color"]} 0%, {theme["primary_color"]} 100%)')};
            --secondary-gradient: {theme.get('secondary_gradient', f'linear-gradient(135deg, {theme["secondary_color"]} 0%, {theme["secondary_color"]} 100%)')};
            --accent-color: {theme.get('accent_color', theme['primary_color'])};
        }}
        
        /* Global Theme Styles */
        .stApp {{
            background: var(--background-color);
            color: var(--text-color);
        }}
        
        /* Hide Streamlit default styling */
        .stDeployButton {{
            display: none;
        }}
        
        header[data-testid="stHeader"] {{
            display: none;
        }}
        
        .stAppHeader {{
            display: none;
        }}
        
        /* Modern Glass Card */
        .glass-card {{
            background: var(--glass-background);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            box-shadow: 0 8px 32px var(--shadow-color);
            padding: 2rem;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }}
        
        .glass-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 16px 48px var(--shadow-color);
        }}
        
        .glass-card.compact {{
            padding: 1rem;
            border-radius: 16px;
        }}
        
        /* Modern Buttons */
        .modern-button {{
            background: var(--primary-gradient);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            text-decoration: none;
            display: inline-block;
        }}
        
        .modern-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }}
        
        .modern-button.secondary {{
            background: var(--secondary-gradient);
        }}
        
        .modern-button.success {{
            background: linear-gradient(135deg, var(--success-color) 0%, var(--success-color) 100%);
        }}
        
        .modern-button.warning {{
            background: linear-gradient(135deg, var(--warning-color) 0%, var(--warning-color) 100%);
        }}
        
        .modern-button.error {{
            background: linear-gradient(135deg, var(--error-color) 0%, var(--error-color) 100%);
        }}
        
        .modern-button.outline {{
            background: transparent;
            border: 2px solid var(--primary-color);
            color: var(--primary-color);
        }}
        
        .modern-button.outline:hover {{
            background: var(--primary-color);
            color: white;
        }}
        
        /* Modern Navigation */
        .nav-item {{
            background: var(--glass-background);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border: 1px solid var(--glass-border);
            padding: 1rem;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
            cursor: pointer;
            color: var(--text-color);
            text-decoration: none;
            display: block;
        }}
        
        .nav-item:hover {{
            background: var(--primary-gradient);
            color: white;
            transform: translateX(10px);
        }}
        
        .nav-item.active {{
            background: var(--primary-gradient);
            color: white;
            box-shadow: 0 4px 16px var(--shadow-color);
        }}
        
        .nav-icon {{
            margin-right: 0.75rem;
            font-size: 1.25rem;
        }}
        
        /* Modern Forms */
        .modern-form-group {{
            margin-bottom: 1.5rem;
        }}
        
        .modern-label {{
            color: var(--text-color);
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: block;
        }}
        
        .modern-input {{
            background: var(--glass-background);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            width: 100%;
            color: var(--text-color);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }}
        
        .modern-input:focus {{
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(var(--accent-color), 0.1);
        }}
        
        .modern-textarea {{
            background: var(--glass-background);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            width: 100%;
            color: var(--text-color);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            min-height: 100px;
            resize: vertical;
        }}
        
        .modern-select {{
            background: var(--glass-background);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            width: 100%;
            color: var(--text-color);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }}
        
        /* Modern Cards */
        .metric-card {{
            background: var(--glass-background);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            border: 1px solid var(--glass-border);
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-gradient);
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 12px 32px var(--shadow-color);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 0.5rem;
        }}
        
        .metric-label {{
            color: var(--text-secondary);
            font-weight: 500;
        }}
        
        .metric-change {{
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}
        
        .metric-change.positive {{
            color: var(--success-color);
        }}
        
        .metric-change.negative {{
            color: var(--error-color);
        }}
        
        /* Project Cards */
        .project-card {{
            background: var(--glass-background);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            border: 1px solid var(--glass-border);
            padding: 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px var(--shadow-color);
        }}
        
        .project-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 32px var(--shadow-color);
        }}
        
        .project-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }}
        
        .project-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-color);
            margin: 0;
        }}
        
        .project-description {{
            color: var(--text-secondary);
            margin: 0.5rem 0 1rem 0;
            line-height: 1.5;
        }}
        
        .project-meta {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        
        .project-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
        }}
        
        /* Task Cards */
        .task-card {{
            background: var(--glass-background);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border: 1px solid var(--glass-border);
            padding: 1rem;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .task-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 8px 24px var(--shadow-color);
        }}
        
        .task-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.5rem;
        }}
        
        .task-title {{
            font-weight: 600;
            color: var(--text-color);
            margin: 0;
        }}
        
        .task-meta {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
            margin-top: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        
        /* Status Indicators */
        .status-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-success {{
            background: linear-gradient(135deg, var(--success-color) 0%, var(--success-color) 100%);
            color: white;
        }}
        
        .status-warning {{
            background: linear-gradient(135deg, var(--warning-color) 0%, var(--warning-color) 100%);
            color: white;
        }}
        
        .status-error {{
            background: linear-gradient(135deg, var(--error-color) 0%, var(--error-color) 100%);
            color: white;
        }}
        
        .status-info {{
            background: linear-gradient(135deg, var(--info-color) 0%, var(--info-color) 100%);
            color: white;
        }}
        
        .status-planning {{
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
        }}
        
        .status-active {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color) 100%);
            color: white;
        }}
        
        .status-completed {{
            background: linear-gradient(135deg, var(--success-color) 0%, var(--success-color) 100%);
            color: white;
        }}
        
        .status-on-hold {{
            background: linear-gradient(135deg, var(--warning-color) 0%, var(--warning-color) 100%);
            color: white;
        }}
        
        .status-cancelled {{
            background: linear-gradient(135deg, var(--error-color) 0%, var(--error-color) 100%);
            color: white;
        }}
        
        /* Priority Indicators */
        .priority-critical {{
            color: var(--error-color);
            font-weight: 700;
        }}
        
        .priority-high {{
            color: var(--warning-color);
            font-weight: 600;
        }}
        
        .priority-medium {{
            color: var(--info-color);
            font-weight: 500;
        }}
        
        .priority-low {{
            color: var(--success-color);
            font-weight: 400;
        }}
        
        /* Progress Bars */
        .progress-container {{
            background: var(--surface-color);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin: 0.5rem 0;
            position: relative;
        }}
        
        .progress-bar {{
            height: 100%;
            background: var(--primary-gradient);
            border-radius: 10px;
            transition: width 0.5s ease;
            position: relative;
        }}
        
        .progress-bar.success {{
            background: linear-gradient(135deg, var(--success-color) 0%, var(--success-color) 100%);
        }}
        
        .progress-bar.warning {{
            background: linear-gradient(135deg, var(--warning-color) 0%, var(--warning-color) 100%);
        }}
        
        .progress-bar.error {{
            background: linear-gradient(135deg, var(--error-color) 0%, var(--error-color) 100%);
        }}
        
        .progress-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }}
        
        /* Modern Tables */
        .modern-table {{
            background: var(--glass-background);
            backdrop-filter: blur(20px);
            border-radius: 16px;
            border: 1px solid var(--glass-border);
            overflow: hidden;
            box-shadow: 0 8px 32px var(--shadow-color);
            width: 100%;
        }}
        
        .table-header {{
            background: var(--primary-gradient);
            color: white;
            padding: 1rem;
            font-weight: 600;
        }}
        
        .table-row {{
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }}
        
        .table-row:hover {{
            background: rgba(var(--accent-color), 0.05);
        }}
        
        .table-row:last-child {{
            border-bottom: none;
        }}
        
        /* Loading States */
        .loading-spinner {{
            border: 3px solid var(--border-color);
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }}
        
        .loading-skeleton {{
            background: linear-gradient(90deg, var(--surface-color) 25%, var(--border-color) 50%, var(--surface-color) 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: 8px;
            height: 1rem;
        }}
        
        /* Notifications */
        .notification {{
            padding: 1rem 1.5rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            box-shadow: 0 4px 16px var(--shadow-color);
            animation: slideInRight 0.3s ease-out;
        }}
        
        .notification.success {{
            background: var(--success-color);
            color: white;
        }}
        
        .notification.warning {{
            background: var(--warning-color);
            color: white;
        }}
        
        .notification.error {{
            background: var(--error-color);
            color: white;
        }}
        
        .notification.info {{
            background: var(--info-color);
            color: white;
        }}
        
        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes slideInRight {{
            from {{
                opacity: 0;
                transform: translateX(30px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{
                transform: scale(1);
            }}
            50% {{
                transform: scale(1.05);
            }}
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        @keyframes loading {{
            0% {{
                background-position: 200% 0;
            }}
            100% {{
                background-position: -200% 0;
            }}
        }}
        
        @keyframes bounce {{
            0%, 20%, 53%, 80%, 100% {{
                transform: translateY(0);
            }}
            40%, 43% {{
                transform: translateY(-10px);
            }}
            70% {{
                transform: translateY(-5px);
            }}
            90% {{
                transform: translateY(-2px);
            }}
        }}
        
        .fade-in-up {{
            animation: fadeInUp 0.6s ease-out;
        }}
        
        .slide-in-right {{
            animation: slideInRight 0.5s ease-out;
        }}
        
        .pulse {{
            animation: pulse 2s infinite;
        }}
        
        .bounce {{
            animation: bounce 1s;
        }}
        
        /* Theme Toggle */
        .theme-toggle {{
            background: var(--glass-background);
            backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: 25px;
            padding: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            background: var(--primary-gradient);
            color: white;
        }}
        
        /* Sidebar Customization */
        .css-1d391kg {{
            background: var(--glass-background);
            backdrop-filter: blur(20px);
        }}
        
        .css-1lcbmhc {{
            background: var(--glass-background);
            backdrop-filter: blur(20px);
        }}
        
        /* Streamlit Widget Customization */
        .stSelectbox > div > div {{
            background: var(--glass-background);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
        }}
        
        .stTextInput > div > div > input {{
            background: var(--glass-background);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            color: var(--text-color);
        }}
        
        .stTextArea > div > div > textarea {{
            background: var(--glass-background);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            color: var(--text-color);
        }}
        
        .stButton > button {{
            background: var(--primary-gradient);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px var(--shadow-color);
        }}
        
        .stMetric {{
            background: var(--glass-background);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid var(--glass-border);
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .glass-card {{
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 16px;
            }}
            
            .metric-value {{
                font-size: 2rem;
            }}
            
            .modern-button {{
                padding: 0.625rem 1.25rem;
                font-size: 0.875rem;
            }}
            
            .project-card, .task-card {{
                padding: 1rem;
            }}
            
            .nav-item {{
                padding: 0.75rem;
            }}
        }}
        
        /* Dark mode specific adjustments */
        [data-theme="dark"] {{
            .glass-card {{
                background: rgba(15, 23, 42, 0.9);
                border-color: rgba(255, 255, 255, 0.1);
            }}
            
            .modern-input {{
                background: rgba(30, 41, 59, 0.8);
                border-color: rgba(255, 255, 255, 0.1);
                color: #f1f5f9;
            }}
        }}
        </style>
        """

    def apply_theme(self):
        """Apply the current theme"""
        css = self.get_theme_css()
        st.markdown(css, unsafe_allow_html=True)

    def render_theme_customizer(self):
        """Render theme customization interface"""
        st.markdown("## 🎨 Theme Customizer")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Theme Mode")
            current_mode = st.session_state.get("theme_mode", ThemeMode.AUTO.value)

            mode_options = {
                ThemeMode.LIGHT.value: "☀️ Light",
                ThemeMode.DARK.value: "🌙 Dark",
                ThemeMode.AUTO.value: "🔄 Auto",
            }

            selected_mode = st.selectbox(
                "Select theme mode",
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options[x],
                index=list(mode_options.keys()).index(current_mode),
                key="theme_mode_selector",
            )

            if selected_mode != current_mode:
                self.set_theme_mode(ThemeMode(selected_mode))
                st.rerun()

        with col2:
            st.markdown("### Color Scheme")
            current_scheme = st.session_state.get(
                "color_scheme", ColorScheme.BLUE.value
            )

            scheme_options = {
                ColorScheme.BLUE.value: "💙 Blue",
                ColorScheme.GREEN.value: "💚 Green",
                ColorScheme.PURPLE.value: "💜 Purple",
                ColorScheme.PINK.value: "💗 Pink",
                ColorScheme.ORANGE.value: "🧡 Orange",
                ColorScheme.TEAL.value: "🩵 Teal",
                ColorScheme.INDIGO.value: "💙 Indigo",
                ColorScheme.RED.value: "❤️ Red",
            }

            selected_scheme = st.selectbox(
                "Select color scheme",
                options=list(scheme_options.keys()),
                format_func=lambda x: scheme_options[x],
                index=list(scheme_options.keys()).index(current_scheme),
                key="color_scheme_selector",
            )

            if selected_scheme != current_scheme:
                self.set_color_scheme(ColorScheme(selected_scheme))
                st.rerun()

        # Theme Preview
        self._render_theme_preview()

        # Custom Colors
        self._render_custom_colors()

        # Reset Button
        if st.button("🔄 Reset to Default", key="reset_theme"):
            st.session_state.theme_mode = ThemeMode.AUTO.value
            st.session_state.color_scheme = ColorScheme.BLUE.value
            st.session_state.custom_theme = {}
            st.success("Theme reset to default!")
            st.rerun()

    def _render_theme_preview(self):
        """Render theme preview"""
        st.markdown("### 👀 Theme Preview")

        # Apply current theme CSS
        self.apply_theme()

        # Preview cards
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                """
            <div class="metric-card">
                <div class="metric-value">156</div>
                <div class="metric-label">Total Projects</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                """
            <div class="metric-card">
                <div class="metric-value">89%</div>
                <div class="metric-label">Completion Rate</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                """
            <div class="metric-card">
                <div class="metric-value">24</div>
                <div class="metric-label">Team Members</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Status indicators preview
        st.markdown("#### Status Indicators")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                '<span class="status-badge status-success">✅ Complete</span>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                '<span class="status-badge status-warning">⚠️ In Progress</span>',
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                '<span class="status-badge status-error">❌ Overdue</span>',
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                '<span class="status-badge status-info">ℹ️ Pending</span>',
                unsafe_allow_html=True,
            )

        # Progress bar preview
        st.markdown("#### Progress Bars")
        for i, (label, value) in enumerate(
            [("Project A", 75), ("Project B", 45), ("Project C", 90)]
        ):
            st.markdown(
                f"""
            <div style="margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="color: var(--text-color);">{label}</span>
                    <span style="color: var(--text-secondary);">{value}%</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {value}%;">
                        <div class="progress-text">{value}%</div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def _render_custom_colors(self):
        """Render custom color picker"""
        st.markdown("### 🎨 Custom Colors")

        with st.expander("Advanced Color Customization"):
            col1, col2 = st.columns(2)

            with col1:
                primary_color = st.color_picker(
                    "Primary Color",
                    value=self.current_theme["primary_color"],
                    key="custom_primary",
                )

                success_color = st.color_picker(
                    "Success Color",
                    value=self.current_theme["success_color"],
                    key="custom_success",
                )

                error_color = st.color_picker(
                    "Error Color",
                    value=self.current_theme["error_color"],
                    key="custom_error",
                )

            with col2:
                secondary_color = st.color_picker(
                    "Secondary Color",
                    value=self.current_theme["secondary_color"],
                    key="custom_secondary",
                )

                warning_color = st.color_picker(
                    "Warning Color",
                    value=self.current_theme["warning_color"],
                    key="custom_warning",
                )

                info_color = st.color_picker(
                    "Info Color",
                    value=self.current_theme["info_color"],
                    key="custom_info",
                )

            if st.button("Apply Custom Colors", key="apply_custom"):
                custom_colors = {
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                    "success_color": success_color,
                    "warning_color": warning_color,
                    "error_color": error_color,
                    "info_color": info_color,
                    "accent_color": primary_color,
                }

                self.update_custom_theme(custom_colors)
                st.success("Custom colors applied!")
                st.rerun()

    def get_theme_toggle_widget(self) -> str:
        """Get theme toggle widget HTML"""
        current_mode = st.session_state.get("theme_mode", ThemeMode.AUTO.value)

        icons = {
            ThemeMode.LIGHT.value: "☀️",
            ThemeMode.DARK.value: "🌙",
            ThemeMode.AUTO.value: "🔄",
        }

        return f"""
        <div class="theme-toggle" onclick="toggleTheme()">
            <span>{icons[current_mode]}</span>
            <span>{current_mode.title()}</span>
        </div>
        
        <script>
        function toggleTheme() {{
            // Toggle theme logic would go here
            // This would need to integrate with Streamlit's session state
        }}
        </script>
        """

    def export_theme(self) -> str:
        """Export current theme as JSON"""
        theme_data = {
            "mode": st.session_state.get("theme_mode"),
            "color_scheme": st.session_state.get("color_scheme"),
            "custom_theme": st.session_state.get("custom_theme", {}),
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(theme_data, indent=2)

    def import_theme(self, theme_json: str) -> bool:
        """Import theme from JSON"""
        try:
            theme_data = json.loads(theme_json)

            if "mode" in theme_data:
                st.session_state.theme_mode = theme_data["mode"]
            if "color_scheme" in theme_data:
                st.session_state.color_scheme = theme_data["color_scheme"]
            if "custom_theme" in theme_data:
                st.session_state.custom_theme = theme_data["custom_theme"]

            self.current_theme = self._get_current_theme()
            return True

        except Exception as e:
            return False


def render_theme_selector():
    """Render a simple theme selector widget"""
    theme_manager = ThemeManager()

    st.markdown("### 🎨 Theme Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("☀️ Light", key="theme_light"):
            theme_manager.set_theme_mode(ThemeMode.LIGHT)
            st.rerun()

    with col2:
        if st.button("🌙 Dark", key="theme_dark"):
            theme_manager.set_theme_mode(ThemeMode.DARK)
            st.rerun()

    with col3:
        if st.button("🔄 Auto", key="theme_auto"):
            theme_manager.set_theme_mode(ThemeMode.AUTO)
            st.rerun()

    # Color scheme selector
    st.markdown("#### Color Scheme")
    scheme_cols = st.columns(4)
    schemes = [
        (ColorScheme.BLUE, "💙", "Blue"),
        (ColorScheme.GREEN, "💚", "Green"),
        (ColorScheme.PURPLE, "💜", "Purple"),
        (ColorScheme.PINK, "💗", "Pink"),
    ]

    for i, (scheme, icon, name) in enumerate(schemes):
        with scheme_cols[i]:
            if st.button(f"{icon} {name}", key=f"scheme_{scheme.value}"):
                theme_manager.set_color_scheme(scheme)
                st.rerun()


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_current_theme():
    """Apply current theme to the page"""
    theme_manager = get_theme_manager()
    theme_manager.apply_theme()


# Export classes and functions
__all__ = [
    "ThemeManager",
    "ThemeMode",
    "ColorScheme",
    "render_theme_selector",
    "get_theme_manager",
    "apply_current_theme",
]
