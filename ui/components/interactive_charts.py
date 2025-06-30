"""
🚀 Project Manager Pro v3.0 - Interactive Charts
Beautiful, interactive charts with modern design
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

class InteractiveCharts:
    """Interactive chart components with modern styling"""
    
    def __init__(self):
        self.color_palette = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'info': '#3B82F6',
            'purple': '#8B5CF6',
            'pink': '#EC4899'
        }
        
        self.chart_template = {
            'layout': {
                'plot_bgcolor': 'rgba(0,0,0,0)',
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'font': {
                    'color': 'white',
                    'family': 'Segoe UI, Arial, sans-serif'
                },
                'title': {
                    'font': {
                        'size': 18,
                        'color': 'white'
                    },
                    'x': 0.5,
                    'xanchor': 'center'
                },
                'xaxis': {
                    'gridcolor': 'rgba(255,255,255,0.1)',
                    'zerolinecolor': 'rgba(255,255,255,0.2)',
                    'color': 'rgba(255,255,255,0.8)'
                },
                'yaxis': {
                    'gridcolor': 'rgba(255,255,255,0.1)',
                    'zerolinecolor': 'rgba(255,255,255,0.2)',
                    'color': 'rgba(255,255,255,0.8)'
                },
                'legend': {
                    'font': {'color': 'white'},
                    'bgcolor': 'rgba(255,255,255,0.1)',
                    'bordercolor': 'rgba(255,255,255,0.2)',
                    'borderwidth': 1
                },
                'margin': {'l': 50, 'r': 50, 't': 80, 'b': 50}
            }
        }
    
    def create_line_chart(self, data: List[Dict[str, Any]], x: str, y: str, 
                         color: str = None, title: str = "Line Chart",
                         markers: bool = False, smooth: bool = True) -> go.Figure:
        """Create an interactive line chart"""
        
        df = pd.DataFrame(data)
        
        if color:
            fig = px.line(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                markers=markers,
                line_shape='spline' if smooth else 'linear'
            )
        else:
            fig = px.line(
                df, 
                x=x, 
                y=y, 
                title=title,
                markers=markers,
                line_shape='spline' if smooth else 'linear'
            )
        
        # Apply custom styling
        fig.update_layout(self.chart_template['layout'])
        
        # Add hover effects
        fig.update_traces(
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         f'{x}: %{{x}}<br>' +
                         f'{y}: %{{y}}<br>' +
                         '<extra></extra>',
            line=dict(width=3),
            marker=dict(size=8) if markers else {}
        )
        
        # Add gradient fill
        if not color:
            fig.update_traces(
                fill='tonexty' if len(fig.data) > 1 else 'tozeroy',
                fillcolor='rgba(102, 126, 234, 0.1)'
            )
        
        return fig
    
    def create_bar_chart(self, data: List[Dict[str, Any]], x: str, y: str,
                        color: str = None, title: str = "Bar Chart",
                        color_map: Dict[str, str] = None,
                        orientation: str = 'vertical') -> go.Figure:
        """Create an interactive bar chart"""
        
        df = pd.DataFrame(data)
        
        if orientation == 'horizontal':
            fig = px.bar(
                df, 
                x=y, 
                y=x, 
                color=color,
                title=title,
                orientation='h',
                color_discrete_map=color_map
            )
        else:
            fig = px.bar(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                color_discrete_map=color_map
            )
        
        # Apply custom styling
        fig.update_layout(self.chart_template['layout'])
        
        # Add hover effects and styling
        fig.update_traces(
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         f'{x}: %{{x}}<br>' +
                         f'{y}: %{{y}}<br>' +
                         '<extra></extra>',
            marker=dict(
                line=dict(color='rgba(255,255,255,0.2)', width=1),
                opacity=0.8
            )
        )
        
        # Add gradient effect
        if not color:
            fig.update_traces(
                marker=dict(
                    color=list(range(len(df))),
                    colorscale=[[0, self.color_palette['primary']], 
                               [1, self.color_palette['secondary']]],
                    opacity=0.8
                )
            )
        
        return fig
    
    def create_horizontal_bar_chart(self, data: List[Dict[str, Any]], x: str, y: str,
                                   color: str = None, title: str = "Horizontal Bar Chart",
                                   color_scale: str = 'viridis') -> go.Figure:
        """Create a horizontal bar chart"""
        return self.create_bar_chart(data, x, y, color, title, 
                                   orientation='horizontal')
    
    def create_donut_chart(self, data: List[Dict[str, Any]], labels: str, values: str,
                          title: str = "Donut Chart", colors: List[str] = None,
                          hole_size: float = 0.4) -> go.Figure:
        """Create an interactive donut chart"""
        
        df = pd.DataFrame(data)
        
        fig = go.Figure(data=[go.Pie(
            labels=df[labels],
            values=df[values],
            hole=hole_size,
            marker=dict(
                colors=colors or [
                    self.color_palette['primary'],
                    self.color_palette['success'],
                    self.color_palette['warning'],
                    self.color_palette['error'],
                    self.color_palette['info'],
                    self.color_palette['purple']
                ],
                line=dict(color='rgba(255,255,255,0.2)', width=2)
            ),
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(color='white', size=12),
            hovertemplate='<b>%{label}</b><br>' +
                         'Value: %{value}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>'
        )])
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=True,
            legend=dict(
                font=dict(color='white'),
                bgcolor='rgba(255,255,255,0.1)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            )
        )
        
        return fig
    
    def create_scatter_chart(self, data: List[Dict[str, Any]], x: str, y: str,
                           size: str = None, color: str = None,
                           title: str = "Scatter Chart",
                           hover_data: List[str] = None) -> go.Figure:
        """Create an interactive scatter chart"""
        
        df = pd.DataFrame(data)
        
        fig = px.scatter(
            df,
            x=x,
            y=y,
            size=size,
            color=color,
            title=title,
            hover_data=hover_data,
            color_continuous_scale='viridis'
        )
        
        # Apply custom styling
        fig.update_layout(self.chart_template['layout'])
        
        # Update traces for better visibility
        fig.update_traces(
            marker=dict(
                opacity=0.7,
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            ),
            hovertemplate='<b>%{hovertext}</b><br>' +
                         f'{x}: %{{x}}<br>' +
                         f'{y}: %{{y}}<br>' +
                         (f'{size}: %{{marker.size}}<br>' if size else '') +
                         '<extra></extra>'
        )
        
        return fig
    
    def create_gantt_chart(self, data: List[Dict[str, Any]], x_start: str, x_end: str,
                          y: str, color: str = None, title: str = "Gantt Chart") -> go.Figure:
        """Create a Gantt chart for project timelines"""
        
        df = pd.DataFrame(data)
        
        # Convert dates to datetime if they're strings
        if df[x_start].dtype == 'object':
            df[x_start] = pd.to_datetime(df[x_start])
        if df[x_end].dtype == 'object':
            df[x_end] = pd.to_datetime(df[x_end])
        
        fig = go.Figure()
        
        # Color mapping for different statuses
        status_colors = {
            'Planning': '#6B7280',
            'Active': '#3B82F6',
            'In Progress': '#F59E0B',
            'Completed': '#10B981',
            'On Hold': '#EF4444',
            'Cancelled': '#DC2626'
        }
        
        for i, row in df.iterrows():
            color_val = status_colors.get(row.get(color, 'Active'), '#3B82F6')
            
            fig.add_trace(go.Scatter(
                x=[row[x_start], row[x_end], row[x_end], row[x_start], row[x_start]],
                y=[i-0.4, i-0.4, i+0.4, i+0.4, i-0.4],
                fill='toself',
                fillcolor=color_val,
                line=dict(color=color_val, width=2),
                name=row[y],
                hovertemplate=f'<b>{row[y]}</b><br>' +
                             f'Start: {row[x_start].strftime("%Y-%m-%d")}<br>' +
                             f'End: {row[x_end].strftime("%Y-%m-%d")}<br>' +
                             f'Status: {row.get(color, "N/A")}<br>' +
                             '<extra></extra>',
                showlegend=False
            ))
        
        # Update layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            xaxis=dict(
                title='Timeline',
                gridcolor='rgba(255,255,255,0.1)',
                color='rgba(255,255,255,0.8)'
            ),
            yaxis=dict(
                title='Projects',
                tickvals=list(range(len(df))),
                ticktext=df[y].tolist(),
                gridcolor='rgba(255,255,255,0.1)',
                color='rgba(255,255,255,0.8)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            margin=dict(l=50, r=50, t=80, b=50),
            height=max(400, len(df) * 50 + 100)
        )
        
        return fig
    
    def create_heatmap(self, data: List[Dict[str, Any]], x: str, y: str, z: str,
                      title: str = "Heatmap", color_scale: str = 'viridis') -> go.Figure:
        """Create an interactive heatmap"""
        
        df = pd.DataFrame(data)
        
        # Pivot data for heatmap
        heatmap_data = df.pivot(index=y, columns=x, values=z)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=color_scale,
            hovertemplate=f'<b>{x}: %{{x}}</b><br>' +
                         f'{y}: %{{y}}<br>' +
                         f'{z}: %{{z}}<br>' +
                         '<extra></extra>',
            colorbar=dict(
                title=z,
                titlefont=dict(color='white'),
                tickfont=dict(color='white')
            )
        ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            xaxis=dict(
                title=x,
                color='rgba(255,255,255,0.8)',
                tickangle=45
            ),
            yaxis=dict(
                title=y,
                color='rgba(255,255,255,0.8)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            margin=dict(l=100, r=50, t=80, b=100)
        )
        
        return fig
    
    def create_area_chart(self, data: List[Dict[str, Any]], x: str, y: str,
                         color: str = None, title: str = "Area Chart",
                         stacked: bool = False) -> go.Figure:
        """Create an interactive area chart"""
        
        df = pd.DataFrame(data)
        
        if color and stacked:
            fig = px.area(df, x=x, y=y, color=color, title=title)
        elif color:
            fig = px.line(df, x=x, y=y, color=color, title=title)
            fig.update_traces(fill='tonexty')
        else:
            fig = px.area(df, x=x, y=y, title=title)
        
        # Apply custom styling
        fig.update_layout(self.chart_template['layout'])
        
        # Update traces for better visibility
        fig.update_traces(
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         f'{x}: %{{x}}<br>' +
                         f'{y}: %{{y}}<br>' +
                         '<extra></extra>',
            line=dict(width=2),
            fillcolor='rgba(102, 126, 234, 0.3)' if not color else None
        )
        
        return fig
    
    def create_radial_chart(self, data: List[Dict[str, Any]], theta: str, r: str,
                           title: str = "Radial Chart", color: str = None) -> go.Figure:
        """Create a radial/polar chart"""
        
        df = pd.DataFrame(data)
        
        if color:
            fig = px.line_polar(df, theta=theta, r=r, color=color, 
                               line_close=True, title=title)
        else:
            fig = px.line_polar(df, theta=theta, r=r, line_close=True, title=title)
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                angularaxis=dict(
                    color='rgba(255,255,255,0.8)',
                    gridcolor='rgba(255,255,255,0.1)'
                ),
                radialaxis=dict(
                    color='rgba(255,255,255,0.8)',
                    gridcolor='rgba(255,255,255,0.1)'
                )
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        fig.update_traces(
            fill='toself',
            fillcolor='rgba(102, 126, 234, 0.3)',
            line=dict(color=self.color_palette['primary'], width=3)
        )
        
        return fig
    
    def create_waterfall_chart(self, data: List[Dict[str, Any]], x: str, y: str,
                              title: str = "Waterfall Chart") -> go.Figure:
        """Create a waterfall chart for cumulative analysis"""
        
        df = pd.DataFrame(data)
        
        # Calculate cumulative values
        cumulative = []
        running_total = 0
        
        for i, value in enumerate(df[y]):
            if i == 0:
                cumulative.append(value)
                running_total = value
            else:
                cumulative.append(running_total + value)
                running_total += value
        
        fig = go.Figure()
        
        # Add bars
        for i, (label, value, cum_value) in enumerate(zip(df[x], df[y], cumulative)):
            color = self.color_palette['success'] if value >= 0 else self.color_palette['error']
            
            if i == 0:
                # First bar starts from zero
                fig.add_trace(go.Bar(
                    x=[label],
                    y=[value],
                    name=label,
                    marker_color=color,
                    showlegend=False,
                    hovertemplate=f'<b>{label}</b><br>Value: {value}<br><extra></extra>'
                ))
            else:
                # Subsequent bars start from previous cumulative
                prev_cum = cumulative[i-1]
                fig.add_trace(go.Bar(
                    x=[label],
                    y=[value],
                    base=prev_cum if value >= 0 else prev_cum + value,
                    name=label,
                    marker_color=color,
                    showlegend=False,
                    hovertemplate=f'<b>{label}</b><br>Value: {value}<br>Cumulative: {cum_value}<br><extra></extra>'
                ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            xaxis=dict(
                title=x,
                color='rgba(255,255,255,0.8)',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                title=y,
                color='rgba(255,255,255,0.8)',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_multi_axis_chart(self, data: List[Dict[str, Any]], x: str, 
                               y1: str, y2: str, title: str = "Multi-Axis Chart",
                               y1_type: str = 'bar', y2_type: str = 'line') -> go.Figure:
        """Create a chart with multiple y-axes"""
        
        df = pd.DataFrame(data)
        
        # Create subplots with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add first trace
        if y1_type == 'bar':
            fig.add_trace(
                go.Bar(
                    x=df[x],
                    y=df[y1],
                    name=y1,
                    marker_color=self.color_palette['primary'],
                    opacity=0.8
                ),
                secondary_y=False
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=df[x],
                    y=df[y1],
                    name=y1,
                    line=dict(color=self.color_palette['primary'], width=3),
                    mode='lines+markers'
                ),
                secondary_y=False
            )
        
        # Add second trace
        if y2_type == 'bar':
            fig.add_trace(
                go.Bar(
                    x=df[x],
                    y=df[y2],
                    name=y2,
                    marker_color=self.color_palette['secondary'],
                    opacity=0.8
                ),
                secondary_y=True
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=df[x],
                    y=df[y2],
                    name=y2,
                    line=dict(color=self.color_palette['secondary'], width=3),
                    mode='lines+markers'
                ),
                secondary_y=True
            )
        
        # Update axes
        fig.update_xaxes(
            title_text=x,
            color='rgba(255,255,255,0.8)',
            gridcolor='rgba(255,255,255,0.1)'
        )
        fig.update_yaxes(
            title_text=y1,
            secondary_y=False,
            color='rgba(255,255,255,0.8)',
            gridcolor='rgba(255,255,255,0.1)'
        )
        fig.update_yaxes(
            title_text=y2,
            secondary_y=True,
            color='rgba(255,255,255,0.8)',
            gridcolor='rgba(255,255,255,0.1)'
        )
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            legend=dict(
                font=dict(color='white'),
                bgcolor='rgba(255,255,255,0.1)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_treemap(self, data: List[Dict[str, Any]], labels: str, values: str,
                      parents: str = None, title: str = "Treemap") -> go.Figure:
        """Create an interactive treemap"""
        
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Treemap(
            labels=df[labels],
            values=df[values],
            parents=df[parents] if parents else [""] * len(df),
            textinfo="label+value+percent parent",
            textfont=dict(color='white', size=12),
            marker=dict(
                colorscale='viridis',
                line=dict(color='rgba(255,255,255,0.2)', width=2)
            ),
            hovertemplate='<b>%{label}</b><br>' +
                         'Value: %{value}<br>' +
                         'Percentage: %{percentParent}<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_funnel_chart(self, data: List[Dict[str, Any]], x: str, y: str,
                           title: str = "Funnel Chart") -> go.Figure:
        """Create a funnel chart"""
        
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Funnel(
            y=df[y],
            x=df[x],
            textinfo="value+percent initial",
            textfont=dict(color='white', size=14),
            marker=dict(
                color=[self.color_palette['primary'], self.color_palette['info'],
                      self.color_palette['success'], self.color_palette['warning']],
                line=dict(color='rgba(255,255,255,0.2)', width=2)
            ),
            hovertemplate='<b>%{y}</b><br>' +
                         'Value: %{x}<br>' +
                         'Percentage: %{percentInitial}<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_gauge_chart(self, value: float, max_value: float = 100,
                          title: str = "Gauge Chart", 
                          color_ranges: List[Dict] = None) -> go.Figure:
        """Create a gauge chart for KPIs"""
        
        if not color_ranges:
            color_ranges = [
                {"range": [0, 30], "color": self.color_palette['error']},
                {"range": [30, 70], "color": self.color_palette['warning']},
                {"range": [70, 100], "color": self.color_palette['success']}
            ]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'color': 'white', 'size': 18}},
            delta={'reference': max_value * 0.8, 'increasing': {'color': self.color_palette['success']}},
            gauge={
                'axis': {
                    'range': [None, max_value],
                    'tickcolor': 'white',
                    'tickfont': {'color': 'white'}
                },
                'bar': {'color': self.color_palette['primary']},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': 'rgba(255,255,255,0.1)'},
                    {'range': [max_value * 0.5, max_value], 'color': 'rgba(255,255,255,0.05)'}
                ],
                'threshold': {
                    'line': {'color': self.color_palette['error'], 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                },
                'borderwidth': 2,
                'bordercolor': 'rgba(255,255,255,0.2)'
            }
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            margin=dict(l=50, r=50, t=80, b=50),
            height=400
        )
        
        return fig
    
    def create_sankey_diagram(self, data: List[Dict[str, Any]], 
                             source: str, target: str, value: str,
                             title: str = "Sankey Diagram") -> go.Figure:
        """Create a Sankey diagram for flow visualization"""
        
        df = pd.DataFrame(data)
        
        # Get unique nodes
        nodes = list(set(df[source].tolist() + df[target].tolist()))
        node_indices = {node: i for i, node in enumerate(nodes)}
        
        # Create source and target indices
        source_indices = [node_indices[src] for src in df[source]]
        target_indices = [node_indices[tgt] for tgt in df[target]]
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="rgba(255,255,255,0.2)", width=0.5),
                label=nodes,
                color=[self.color_palette['primary']] * len(nodes)
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=df[value].tolist(),
                color=['rgba(102, 126, 234, 0.3)'] * len(df)
            )
        )])
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            font=dict(color='white', family='Segoe UI, Arial, sans-serif', size=12),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def add_annotations(self, fig: go.Figure, annotations: List[Dict[str, Any]]) -> go.Figure:
        """Add custom annotations to any chart"""
        
        for annotation in annotations:
            fig.add_annotation(
                x=annotation.get('x', 0),
                y=annotation.get('y', 0),
                text=annotation.get('text', ''),
                showarrow=annotation.get('showarrow', True),
                arrowhead=annotation.get('arrowhead', 2),
                arrowsize=annotation.get('arrowsize', 1),
                arrowwidth=annotation.get('arrowwidth', 2),
                arrowcolor=annotation.get('arrowcolor', 'white'),
                font=dict(
                    color=annotation.get('font_color', 'white'),
                    size=annotation.get('font_size', 12)
                ),
                bgcolor=annotation.get('bgcolor', 'rgba(0,0,0,0.7)'),
                bordercolor=annotation.get('bordercolor', 'rgba(255,255,255,0.2)'),
                borderwidth=annotation.get('borderwidth', 1)
            )
        
        return fig
    
    def create_3d_scatter(self, data: List[Dict[str, Any]], x: str, y: str, z: str,
                         color: str = None, size: str = None,
                         title: str = "3D Scatter Plot") -> go.Figure:
        """Create a 3D scatter plot"""
        
        df = pd.DataFrame(data)
        
        fig = px.scatter_3d(
            df, x=x, y=y, z=z, color=color, size=size, title=title,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='white'), x=0.5),
            scene=dict(
                xaxis=dict(
                    title=x,
                    color='rgba(255,255,255,0.8)',
                    gridcolor='rgba(255,255,255,0.1)',
                    backgroundcolor='rgba(0,0,0,0)'
                ),
                yaxis=dict(
                    title=y,
                    color='rgba(255,255,255,0.8)',
                    gridcolor='rgba(255,255,255,0.1)',
                    backgroundcolor='rgba(0,0,0,0)'
                ),
                zaxis=dict(
                    title=z,
                    color='rgba(255,255,255,0.8)',
                    gridcolor='rgba(255,255,255,0.1)',
                    backgroundcolor='rgba(0,0,0,0)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Segoe UI, Arial, sans-serif'),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig