"""
To-Do Interactive Charts Module
Provides interactive chart widgets for to-do analytics visualization
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QPushButton, QApplication, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette

# Check for optional dependencies
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class BaseInteractiveChart(QWidget):
    """Base class for interactive charts"""

    # Signal emitted when filters change
    filters_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = pd.DataFrame()
        self.setup_ui()

    def get_theme_colors(self):
        """Get current theme colors - CRITICAL FIX for theme awareness"""
        # Try to get theme from parent or application
        app = QApplication.instance()
        if hasattr(app, 'current_theme'):
            theme = app.current_theme
        else:
            # Default to checking palette for theme detection
            palette = app.palette() if app else QPalette()
            bg_color = palette.color(QPalette.Window)
            # Simple heuristic: if background is dark, assume dark theme
            theme = 'dark' if bg_color.lightness() < 128 else 'light'

        if theme == 'light':
            return {
                'background': '#ffffff',
                'secondary_background': '#f9f9f9',
                'controls_background': '#f0f0f0',
                'border': '#e0e0e0',
                'text': '#000000'
            }
        else:
            # Default to dark theme
            return {
                'background': '#1e1e1e',
                'secondary_background': '#252526',
                'controls_background': '#2d2d30',
                'border': '#3e3e42',
                'text': '#ffffff'
            }

    def apply_web_view_styling(self):
        """Apply theme-aware styling to the web view - CRITICAL FIX for chart container backgrounds"""
        if not hasattr(self, 'web_view'):
            return

        colors = self.get_theme_colors()
        background = colors.get('background', '#1e1e1e')

        # CRITICAL FIX: Set web view background to match theme
        # This fixes the black background issue in chart containers
        self.web_view.setStyleSheet(f"""
            QWebEngineView {{
                background-color: {background};
                border: none;
            }}
        """)

    def setup_ui(self):
        """Setup the basic UI structure - VERTICAL COMPACT: Reduced vertical spacing for better space efficiency"""
        self.layout = QVBoxLayout(self)
        # VERTICAL COMPACT: Reduced vertical margins from 10,10,10,10 to 5,2,5,2 (50% reduction in vertical space)
        self.layout.setContentsMargins(5, 2, 5, 2)
        # VERTICAL COMPACT: Reduce spacing between filter controls and chart
        self.layout.setSpacing(3)

        # Create filter controls container
        self.create_filter_controls()

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE:
            self.show_dependency_message()
        else:
            self.web_view = QWebEngineView()

            # SIMPLE FIX: Keep basic minimum width, remove height constraints
            self.setMinimumWidth(300)
            self.web_view.setMinimumWidth(300)
            # VERTICAL SPACE FIX: Set size policy to allow expansion but work with layout stretch
            self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # STYLING CONSISTENCY: Remove hardcoded colors and let theme-aware styling handle it
            # This ensures consistent appearance across all chart sub-tabs
            self.web_view.setStyleSheet("""
                QWebEngineView {
                    min-width: 300px;
                }
            """)

            # CRITICAL FIX: Apply theme-aware styling to web view to fix black background
            self.apply_web_view_styling()

            # VERTICAL SPACE FIX: Add web view with stretch factor 1 to take most space
            self.layout.addWidget(self.web_view, 1)

    def apply_theme_to_plotly_fig(self, fig):
        """Apply current theme colors to a Plotly figure - CRITICAL FIX for text colors"""
        colors = self.get_theme_colors()

        # CRITICAL FIX: Handle different color key formats gracefully
        # Some get_theme_colors() methods use different key names
        background = colors.get('background', colors.get('figure_facecolor', '#ffffff'))  # Default to white for light theme
        secondary_bg = colors.get('secondary_background', colors.get('axes_facecolor', '#f9f9f9'))  # Light gray for light theme
        text_color = colors.get('text', colors.get('text_color', '#000000'))  # Black text for light theme
        border_color = colors.get('border', colors.get('axes_edgecolor', '#e0e0e0'))  # Light border for light theme

        fig.update_layout(
            plot_bgcolor=secondary_bg,
            paper_bgcolor=background,
            font=dict(color=text_color),
            title_font_color=text_color,
            xaxis=dict(
                gridcolor=border_color,
                tickcolor=text_color,
                title=dict(font=dict(color=text_color))
            ),
            yaxis=dict(
                gridcolor=border_color,
                tickcolor=text_color,
                title=dict(font=dict(color=text_color))
            ),
            legend=dict(
                font=dict(color=text_color)
            )
        )
        return fig

    def generate_theme_aware_html(self, fig):
        """Generate theme-aware HTML for Plotly charts - CRITICAL FIX for chart backgrounds"""
        colors = self.get_theme_colors()
        background = colors.get('background', colors.get('figure_facecolor', '#ffffff'))  # Default to white for light theme

        # Generate base HTML
        html_str = fig.to_html(include_plotlyjs='cdn')

        # EMPTY SPACE FIX: Inject CSS to eliminate ALL extra spacing and ensure tight layout
        theme_css = f"""
        <style>
            /* EMPTY SPACE FIX: Remove ALL margins and padding to eliminate white space */
            html, body {{
                background-color: {background} !important;
                background: {background} !important;
                margin: 0 !important;
                padding: 0 !important;
                height: auto !important;
                overflow: hidden !important;
            }}

            /* EMPTY SPACE FIX: Target all Plotly containers and remove extra spacing */
            .plotly-graph-div,
            .plotly-graph-div > div,
            .js-plotly-plot,
            .plot-container,
            .svg-container {{
                background-color: {background} !important;
                background: {background} !important;
                margin: 0 !important;
                padding: 0 !important;
                height: auto !important;
            }}

            /* EMPTY SPACE FIX: Override any remaining containers and remove spacing */
            div[id*="plotly"] {{
                background-color: {background} !important;
                background: {background} !important;
                margin: 0 !important;
                padding: 0 !important;
                height: auto !important;
            }}

            /* EMPTY SPACE FIX: Ensure the main plot div takes only necessary space */
            .main-svg {{
                margin: 0 !important;
                padding: 0 !important;
            }}
        </style>
        """

        # Insert CSS right after <head> tag
        head_end = html_str.find('</head>')
        if head_end != -1:
            html_str = html_str[:head_end] + theme_css + html_str[head_end:]

        return html_str

    def set_chart_html(self, html_str):
        """Set HTML content and ensure visibility"""
        if hasattr(self, 'web_view'):
            self.web_view.setHtml(html_str)
            # CRITICAL FIX: Ensure the web view is visible and updated
            self.web_view.show()
            self.web_view.update()

    def create_filter_controls(self):
        """Create filter controls - to be overridden by subclasses"""
        pass
    
    def show_dependency_message(self):
        """Show message when dependencies are not available"""
        message_label = QLabel("📊 Interactive charts require plotly and QtWebEngine")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 20px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        self.layout.addWidget(message_label)
    
    def show_no_data_message(self):
        """Show message when no data is available"""
        if hasattr(self, 'web_view'):
            html_content = """
            <html>
            <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; 
                         display: flex; justify-content: center; align-items: center; 
                         height: 100vh; background-color: #f8f9fa;">
                <div style="text-align: center; color: #6c757d;">
                    <h3>📋 No To-Do Data Available</h3>
                    <p>Start adding tasks to see analytics!</p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(html_content)
    
    def show_error_message(self, error: str):
        """Show error message"""
        if hasattr(self, 'web_view'):
            html_content = f"""
            <html>
            <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; 
                         display: flex; justify-content: center; align-items: center; 
                         height: 100vh; background-color: #f8f9fa;">
                <div style="text-align: center; color: #dc3545;">
                    <h3>⚠️ Chart Error</h3>
                    <p>{error}</p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(html_content)
    
    def update_chart(self, data: pd.DataFrame):
        """Update chart with new data - to be implemented by subclasses"""
        pass


class InteractivePieChartWidget(BaseInteractiveChart):
    """Interactive pie chart widget for to-do status distribution"""

    def create_filter_controls(self):
        """Create filter controls for pie chart - COMPACT: Reduced spacing for better space efficiency"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        # VERTICAL SPACE FIX: Set fixed height to prevent excessive expansion
        filter_frame.setFixedHeight(35)
        filter_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_layout = QHBoxLayout(filter_frame)
        # COMPACT: Reduced margins from 10,5,10,5 to 5,3,5,3
        filter_layout.setContentsMargins(5, 3, 5, 3)
        filter_layout.setSpacing(8)  # Reduced spacing between elements

        # Chart type selector - COMPACT: Smaller font and tighter layout
        type_label = QLabel("Chart Type:")
        type_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(['Status Distribution', 'Priority Distribution', 'Category Distribution'])
        self.chart_type_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.chart_type_combo.currentTextChanged.connect(self.on_filter_changed)

        # Status filter (for category/priority charts) - COMPACT: Smaller font
        status_label = QLabel("Status Filter:")
        status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(['All Status', 'Completed', 'Pending', 'In Progress', 'Cancelled'])
        self.status_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Refresh button - COMPACT: Smaller button with reduced padding
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("font-size: 9px; padding: 3px 8px; margin: 0px;")
        refresh_btn.clicked.connect(self.on_filter_changed)

        filter_layout.addWidget(type_label)
        filter_layout.addWidget(self.chart_type_combo)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)

        # VERTICAL SPACE FIX: Add with stretch factor 0 to prevent expansion
        self.layout.addWidget(filter_frame, 0)

    def on_filter_changed(self):
        """Handle filter changes"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update pie chart with to-do data"""
        self.current_data = data.copy()
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            # Apply status filter if needed
            filtered_data = self.apply_filters(data)

            # Create chart based on selected type
            chart_type = self.chart_type_combo.currentText()
            if chart_type == 'Status Distribution':
                self.create_status_pie_chart(filtered_data)
            elif chart_type == 'Priority Distribution':
                self.create_priority_pie_chart(filtered_data)
            elif chart_type == 'Category Distribution':
                self.create_category_pie_chart(filtered_data)
        except Exception as e:
            print(f"Error updating to-do pie chart: {e}")
            self.show_error_message(str(e))

    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply current filters to data"""
        filtered_data = data.copy()

        # Apply status filter for non-status charts
        chart_type = self.chart_type_combo.currentText()
        if chart_type != 'Status Distribution':
            status_filter = self.status_filter_combo.currentText()
            if status_filter != 'All Status':
                filtered_data = filtered_data[filtered_data['status'] == status_filter]

        return filtered_data
    
    def create_status_pie_chart(self, data: pd.DataFrame):
        """Create pie chart showing task status distribution"""
        # Count tasks by status
        status_counts = data['status'].value_counts()
        
        # Define colors for different statuses
        colors = {
            'Completed': '#28a745',
            'In Progress': '#ffc107', 
            'Pending': '#6c757d',
            'Cancelled': '#dc3545'
        }
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.3,
            marker_colors=[colors.get(status, '#17a2b8') for status in status_counts.index],
            textinfo='label+percent+value',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>' +
                         'Count: %{value}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': '📊 Task Status Distribution',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            font=dict(size=12),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            ),
            # SIMPLE FIX: Reasonable chart size
            margin=dict(l=20, r=120, t=40, b=20),  # Standard margins
            height=300  # Reasonable height
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)
    
    def create_priority_pie_chart(self, data: pd.DataFrame):
        """Create pie chart showing task priority distribution"""
        # Count tasks by priority
        priority_counts = data['priority'].value_counts()
        
        # Define colors for different priorities
        colors = {
            'Urgent': '#dc3545',
            'High': '#fd7e14',
            'Medium': '#ffc107',
            'Low': '#28a745'
        }
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=priority_counts.index,
            values=priority_counts.values,
            hole=0.3,
            marker_colors=[colors.get(priority, '#17a2b8') for priority in priority_counts.index],
            textinfo='label+percent+value',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>' +
                         'Count: %{value}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': '🎯 Task Priority Distribution',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            font=dict(size=12),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            ),
            # SIMPLE FIX: Reasonable chart size
            margin=dict(l=20, r=120, t=40, b=20),  # Standard margins
            height=300  # Reasonable height
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        # STYLING CONSISTENCY: Use consistent method for setting chart HTML like other charts
        self.set_chart_html(html_content)
    
    def create_category_pie_chart(self, data: pd.DataFrame):
        """Create pie chart showing task category distribution"""
        # Count tasks by category
        category_counts = data['category'].value_counts()
        
        # Create pie chart with automatic colors
        fig = go.Figure(data=[go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            hole=0.3,
            textinfo='label+percent+value',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>' +
                         'Count: %{value}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': '📂 Task Category Distribution',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            font=dict(size=12),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            ),
            # SIMPLE FIX: Reasonable chart size
            margin=dict(l=20, r=120, t=40, b=20),  # Standard margins
            height=300  # Reasonable height
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        # STYLING CONSISTENCY: Use consistent method for setting chart HTML like other charts
        self.set_chart_html(html_content)


class InteractiveTimeSeriesWidget(BaseInteractiveChart):
    """Interactive time series widget for to-do completion trends"""

    def create_filter_controls(self):
        """Create filter controls for time series chart - COMPACT: Reduced spacing for better space efficiency"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        # COMPACT: Reduced margins from 10,5,10,5 to 5,3,5,3
        filter_layout.setContentsMargins(5, 3, 5, 3)
        filter_layout.setSpacing(6)  # Reduced spacing between elements

        # Metric selector - COMPACT: Smaller font and tighter layout
        metric_label = QLabel("Metric:")
        metric_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(['Creation & Completion', 'Creation Only', 'Completion Only', 'Cumulative Tasks'])
        self.metric_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.metric_combo.currentTextChanged.connect(self.on_filter_changed)

        # Time period selector - COMPACT: Smaller font
        period_label = QLabel("Period:")
        period_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.period_combo = QComboBox()
        self.period_combo.addItems(['Daily', 'Weekly', 'Monthly'])
        self.period_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.period_combo.currentTextChanged.connect(self.on_filter_changed)

        # Status filter - COMPACT: Smaller font
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(['All Status', 'Completed', 'Pending', 'In Progress', 'Cancelled'])
        self.status_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Priority filter - COMPACT: Smaller font
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItems(['All Priorities', 'Urgent', 'High', 'Medium', 'Low'])
        self.priority_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.priority_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Refresh button - COMPACT: Smaller button with reduced padding
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("font-size: 9px; padding: 3px 8px; margin: 0px;")
        refresh_btn.clicked.connect(self.on_filter_changed)

        filter_layout.addWidget(metric_label)
        filter_layout.addWidget(self.metric_combo)
        filter_layout.addWidget(period_label)
        filter_layout.addWidget(self.period_combo)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addWidget(priority_label)
        filter_layout.addWidget(self.priority_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)

        self.layout.addWidget(filter_frame)

    def on_filter_changed(self):
        """Handle filter changes"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update time series chart with to-do trends"""
        self.current_data = data.copy()
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            # Apply filters
            filtered_data = self.apply_filters(data)

            # Create chart based on selected metric
            metric = self.metric_combo.currentText()
            if metric == 'Creation & Completion':
                self.create_completion_trends_chart(filtered_data)
            elif metric == 'Creation Only':
                self.create_creation_trends_chart(filtered_data)
            elif metric == 'Completion Only':
                self.create_completion_only_chart(filtered_data)
            elif metric == 'Cumulative Tasks':
                self.create_cumulative_chart(filtered_data)
        except Exception as e:
            print(f"Error updating to-do time series chart: {e}")
            self.show_error_message(str(e))

    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply current filters to data"""
        filtered_data = data.copy()

        # Apply status filter
        status_filter = self.status_filter_combo.currentText()
        if status_filter != 'All Status':
            filtered_data = filtered_data[filtered_data['status'] == status_filter]

        # Apply priority filter
        priority_filter = self.priority_filter_combo.currentText()
        if priority_filter != 'All Priorities':
            filtered_data = filtered_data[filtered_data['priority'] == priority_filter]

        return filtered_data
    
    def create_completion_trends_chart(self, data: pd.DataFrame):
        """Create time series chart showing task completion trends"""
        # Prepare data for time series
        data_copy = data.copy()
        
        # Convert date columns to datetime
        for date_col in ['created_at', 'completed_at', 'due_date']:
            if date_col in data_copy.columns:
                data_copy[date_col] = pd.to_datetime(data_copy[date_col], errors='coerce')
        
        # Create daily completion counts
        completed_tasks = data_copy[data_copy['status'] == 'Completed'].copy()
        if not completed_tasks.empty and 'completed_at' in completed_tasks.columns:
            completed_tasks['completion_date'] = completed_tasks['completed_at'].dt.date
            daily_completions = completed_tasks.groupby('completion_date').size().reset_index(name='completed_count')
            daily_completions['completion_date'] = pd.to_datetime(daily_completions['completion_date'])
        else:
            daily_completions = pd.DataFrame(columns=['completion_date', 'completed_count'])
        
        # Create daily creation counts
        if 'created_at' in data_copy.columns:
            data_copy['creation_date'] = data_copy['created_at'].dt.date
            daily_creations = data_copy.groupby('creation_date').size().reset_index(name='created_count')
            daily_creations['creation_date'] = pd.to_datetime(daily_creations['creation_date'])
        else:
            daily_creations = pd.DataFrame(columns=['creation_date', 'created_count'])
        
        # Create the time series chart
        fig = go.Figure()
        
        # Add completion trend line
        if not daily_completions.empty:
            fig.add_trace(go.Scatter(
                x=daily_completions['completion_date'],
                y=daily_completions['completed_count'],
                mode='lines+markers',
                name='Tasks Completed',
                line=dict(color='#28a745', width=2),
                marker=dict(size=6),
                hovertemplate='<b>Completed Tasks</b><br>' +
                             'Date: %{x}<br>' +
                             'Count: %{y}<br>' +
                             '<extra></extra>'
            ))
        
        # Add creation trend line
        if not daily_creations.empty:
            fig.add_trace(go.Scatter(
                x=daily_creations['creation_date'],
                y=daily_creations['created_count'],
                mode='lines+markers',
                name='Tasks Created',
                line=dict(color='#007bff', width=2),
                marker=dict(size=6),
                hovertemplate='<b>Created Tasks</b><br>' +
                             'Date: %{x}<br>' +
                             'Count: %{y}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            title={
                'text': '📈 Task Creation & Completion Trends',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Date',
            yaxis_title='Number of Tasks',
            font=dict(size=12),
            showlegend=True,
            legend=dict(x=0.02, y=0.98),
            margin=dict(l=60, r=20, t=60, b=60),
            height=400,
            hovermode='x unified'
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_creation_trends_chart(self, data: pd.DataFrame):
        """Create time series chart showing only task creation trends"""
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')

        # Group by period
        period = self.period_combo.currentText()
        if period == 'Daily':
            data_copy['period'] = data_copy['created_at'].dt.date
        elif period == 'Weekly':
            data_copy['period'] = data_copy['created_at'].dt.to_period('W')
        else:  # Monthly
            data_copy['period'] = data_copy['created_at'].dt.to_period('M')

        creation_counts = data_copy.groupby('period').size().reset_index(name='count')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=creation_counts['period'],
            y=creation_counts['count'],
            mode='lines+markers',
            name='Tasks Created',
            line=dict(color='#007bff', width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title=f'📈 Task Creation Trends ({period})',
            xaxis_title='Date',
            yaxis_title='Number of Tasks Created',
            font=dict(size=12),
            height=400
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_content)

    def create_completion_only_chart(self, data: pd.DataFrame):
        """Create time series chart showing only task completion trends"""
        completed_data = data[data['status'] == 'Completed'].copy()
        if completed_data.empty or 'completed_at' not in completed_data.columns:
            self.show_no_data_message()
            return

        completed_data['completed_at'] = pd.to_datetime(completed_data['completed_at'], errors='coerce')

        # Group by period
        period = self.period_combo.currentText()
        if period == 'Daily':
            completed_data['period'] = completed_data['completed_at'].dt.date
        elif period == 'Weekly':
            completed_data['period'] = completed_data['completed_at'].dt.to_period('W')
        else:  # Monthly
            completed_data['period'] = completed_data['completed_at'].dt.to_period('M')

        completion_counts = completed_data.groupby('period').size().reset_index(name='count')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=completion_counts['period'],
            y=completion_counts['count'],
            mode='lines+markers',
            name='Tasks Completed',
            line=dict(color='#28a745', width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title=f'✅ Task Completion Trends ({period})',
            xaxis_title='Date',
            yaxis_title='Number of Tasks Completed',
            font=dict(size=12),
            height=400
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_content)

    def create_cumulative_chart(self, data: pd.DataFrame):
        """Create cumulative task count chart"""
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')
        data_copy = data_copy.sort_values('created_at')

        # Calculate cumulative counts
        data_copy['cumulative_total'] = range(1, len(data_copy) + 1)

        # Calculate cumulative completed
        completed_mask = data_copy['status'] == 'Completed'
        data_copy['cumulative_completed'] = completed_mask.cumsum()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=data_copy['created_at'],
            y=data_copy['cumulative_total'],
            mode='lines',
            name='Total Tasks',
            line=dict(color='#007bff', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=data_copy['created_at'],
            y=data_copy['cumulative_completed'],
            mode='lines',
            name='Completed Tasks',
            line=dict(color='#28a745', width=2)
        ))

        fig.update_layout(
            title='📊 Cumulative Task Progress',
            xaxis_title='Date',
            yaxis_title='Cumulative Count',
            font=dict(size=12),
            height=400
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_content)


class InteractiveBarChartWidget(BaseInteractiveChart):
    """Interactive bar chart widget for to-do performance analysis"""

    def create_filter_controls(self):
        """Create filter controls for bar chart - COMPACT: Reduced spacing for better space efficiency"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        # COMPACT: Reduced margins from 10,5,10,5 to 5,3,5,3
        filter_layout.setContentsMargins(5, 3, 5, 3)
        filter_layout.setSpacing(6)  # Reduced spacing between elements

        # Analysis type selector - COMPACT: Smaller font and tighter layout
        type_label = QLabel("Analysis:")
        type_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            'Priority vs Status', 'Category Performance', 'Time-based Analysis',
            'Status Distribution', 'Priority Distribution', 'Completion Rate by Category'
        ])
        self.analysis_type_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.analysis_type_combo.currentTextChanged.connect(self.on_filter_changed)

        # Time period selector (for time-based analysis) - COMPACT: Smaller font
        period_label = QLabel("Period:")
        period_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.period_combo = QComboBox()
        self.period_combo.addItems(['Daily', 'Weekly', 'Monthly'])
        self.period_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.period_combo.currentTextChanged.connect(self.on_filter_changed)

        # Status filter - COMPACT: Smaller font
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(['All Status', 'Completed', 'Pending', 'In Progress', 'Cancelled'])
        self.status_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Refresh button - COMPACT: Smaller button with reduced padding
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("font-size: 9px; padding: 3px 8px; margin: 0px;")
        refresh_btn.clicked.connect(self.on_filter_changed)

        filter_layout.addWidget(type_label)
        filter_layout.addWidget(self.analysis_type_combo)
        filter_layout.addWidget(period_label)
        filter_layout.addWidget(self.period_combo)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)

        self.layout.addWidget(filter_frame)

    def on_filter_changed(self):
        """Handle filter changes"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update bar chart with to-do performance data"""
        self.current_data = data.copy()
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            # Apply filters
            filtered_data = self.apply_filters(data)

            # Create chart based on selected analysis type
            analysis_type = self.analysis_type_combo.currentText()
            if analysis_type == 'Priority vs Status':
                self.create_priority_status_chart(filtered_data)
            elif analysis_type == 'Category Performance':
                self.create_category_performance_chart(filtered_data)
            elif analysis_type == 'Time-based Analysis':
                self.create_time_based_chart(filtered_data)
            elif analysis_type == 'Status Distribution':
                self.create_status_distribution_chart(filtered_data)
            elif analysis_type == 'Priority Distribution':
                self.create_priority_distribution_chart(filtered_data)
            elif analysis_type == 'Completion Rate by Category':
                self.create_completion_rate_chart(filtered_data)
        except Exception as e:
            print(f"Error updating to-do bar chart: {e}")
            self.show_error_message(str(e))

    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply current filters to data"""
        filtered_data = data.copy()

        # Apply status filter for non-status analysis
        analysis_type = self.analysis_type_combo.currentText()
        if analysis_type not in ['Priority vs Status', 'Status Distribution']:
            status_filter = self.status_filter_combo.currentText()
            if status_filter != 'All Status':
                filtered_data = filtered_data[filtered_data['status'] == status_filter]

        return filtered_data

    def create_priority_status_chart(self, data: pd.DataFrame):
        """Create bar chart showing priority vs status breakdown"""
        # Create cross-tabulation of priority and status
        priority_status = pd.crosstab(data['priority'], data['status'])

        # Define colors for different statuses
        colors = {
            'Completed': '#28a745',
            'In Progress': '#ffc107',
            'Pending': '#6c757d',
            'Cancelled': '#dc3545'
        }

        # Create grouped bar chart
        fig = go.Figure()

        for status in priority_status.columns:
            fig.add_trace(go.Bar(
                name=status,
                x=priority_status.index,
                y=priority_status[status],
                marker_color=colors.get(status, '#17a2b8'),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Priority: %{x}<br>' +
                             'Count: %{y}<br>' +
                             '<extra></extra>'
            ))

        fig.update_layout(
            title={
                'text': '📊 Task Priority vs Status Analysis',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Priority Level',
            yaxis_title='Number of Tasks',
            barmode='group',
            font=dict(size=12),
            showlegend=True,
            legend=dict(x=0.02, y=0.98),
            margin=dict(l=60, r=20, t=60, b=60),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_category_performance_chart(self, data: pd.DataFrame):
        """Create bar chart showing category performance"""
        # Calculate completion rate by category
        category_stats = data.groupby('category').agg({
            'status': ['count', lambda x: (x == 'Completed').sum()]
        }).round(2)

        category_stats.columns = ['total_tasks', 'completed_tasks']
        category_stats['completion_rate'] = (category_stats['completed_tasks'] / category_stats['total_tasks'] * 100).round(1)
        category_stats = category_stats.reset_index()

        # Create bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Total Tasks',
            x=category_stats['category'],
            y=category_stats['total_tasks'],
            marker_color='#007bff',
            yaxis='y',
            offsetgroup=1
        ))

        fig.add_trace(go.Bar(
            name='Completed Tasks',
            x=category_stats['category'],
            y=category_stats['completed_tasks'],
            marker_color='#28a745',
            yaxis='y',
            offsetgroup=2
        ))

        fig.add_trace(go.Scatter(
            name='Completion Rate (%)',
            x=category_stats['category'],
            y=category_stats['completion_rate'],
            mode='lines+markers',
            marker_color='#dc3545',
            yaxis='y2',
            line=dict(width=3)
        ))

        fig.update_layout(
            title={
                'text': '📈 Category Performance Analysis',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Category',
            yaxis=dict(title='Number of Tasks', side='left'),
            yaxis2=dict(title='Completion Rate (%)', side='right', overlaying='y'),
            font=dict(size=12),
            showlegend=True,
            legend=dict(x=0.02, y=0.98),
            margin=dict(l=60, r=60, t=60, b=60),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_time_based_chart(self, data: pd.DataFrame):
        """Create time-based analysis chart"""
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')

        # Group by period
        period = self.period_combo.currentText()
        if period == 'Daily':
            data_copy['period'] = data_copy['created_at'].dt.date
        elif period == 'Weekly':
            data_copy['period'] = data_copy['created_at'].dt.to_period('W')
        else:  # Monthly
            data_copy['period'] = data_copy['created_at'].dt.to_period('M')

        period_counts = data_copy.groupby('period').size().reset_index(name='count')

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=period_counts['period'],
            y=period_counts['count'],
            marker_color='#007bff',
            name='Tasks Created'
        ))

        fig.update_layout(
            title=f'📊 Task Creation by {period}',
            xaxis_title=period,
            yaxis_title='Number of Tasks',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_status_distribution_chart(self, data: pd.DataFrame):
        """Create status distribution bar chart"""
        status_counts = data['status'].value_counts()

        colors = {
            'Completed': '#28a745',
            'In Progress': '#ffc107',
            'Pending': '#6c757d',
            'Cancelled': '#dc3545'
        }

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=status_counts.index,
            y=status_counts.values,
            marker_color=[colors.get(status, '#17a2b8') for status in status_counts.index],
            name='Task Count'
        ))

        fig.update_layout(
            title='📊 Task Status Distribution',
            xaxis_title='Status',
            yaxis_title='Number of Tasks',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_priority_distribution_chart(self, data: pd.DataFrame):
        """Create priority distribution bar chart"""
        priority_counts = data['priority'].value_counts()

        colors = {
            'Urgent': '#dc3545',
            'High': '#fd7e14',
            'Medium': '#ffc107',
            'Low': '#28a745'
        }

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=priority_counts.index,
            y=priority_counts.values,
            marker_color=[colors.get(priority, '#17a2b8') for priority in priority_counts.index],
            name='Task Count'
        ))

        fig.update_layout(
            title='🎯 Task Priority Distribution',
            xaxis_title='Priority',
            yaxis_title='Number of Tasks',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_completion_rate_chart(self, data: pd.DataFrame):
        """Create completion rate by category chart"""
        category_completion = data.groupby('category').agg({
            'status': ['count', lambda x: (x == 'Completed').sum()]
        })
        category_completion.columns = ['total', 'completed']
        category_completion['completion_rate'] = (category_completion['completed'] / category_completion['total'] * 100).round(1)
        category_completion = category_completion.reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=category_completion['category'],
            y=category_completion['completion_rate'],
            marker_color='#28a745',
            name='Completion Rate (%)'
        ))

        fig.update_layout(
            title='✅ Completion Rate by Category',
            xaxis_title='Category',
            yaxis_title='Completion Rate (%)',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)


class InteractiveScatterPlotWidget(BaseInteractiveChart):
    """Interactive scatter plot widget for to-do correlation analysis"""

    def create_filter_controls(self):
        """Create filter controls for scatter plot - COMPACT: Reduced spacing for better space efficiency"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        # COMPACT: Reduced margins from 10,5,10,5 to 5,3,5,3
        filter_layout.setContentsMargins(5, 3, 5, 3)
        filter_layout.setSpacing(6)  # Reduced spacing between elements

        # Analysis type selector - COMPACT: Smaller font and tighter layout
        type_label = QLabel("Analysis:")
        type_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            'Estimated vs Actual Hours', 'Priority vs Timeline', 'Category vs Priority',
            'Status vs Creation Time', 'Completion Time Analysis'
        ])
        self.analysis_type_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.analysis_type_combo.currentTextChanged.connect(self.on_filter_changed)

        # Color grouping selector - COMPACT: Smaller font
        color_label = QLabel("Color By:")
        color_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.color_by_combo = QComboBox()
        self.color_by_combo.addItems(['Status', 'Priority', 'Category'])
        self.color_by_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.color_by_combo.currentTextChanged.connect(self.on_filter_changed)

        # Status filter - COMPACT: Smaller font
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(['All Status', 'Completed', 'Pending', 'In Progress', 'Cancelled'])
        self.status_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Priority filter - COMPACT: Smaller font
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItems(['All Priorities', 'Urgent', 'High', 'Medium', 'Low'])
        self.priority_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.priority_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Refresh button - COMPACT: Smaller button with reduced padding
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("font-size: 9px; padding: 3px 8px; margin: 0px;")
        refresh_btn.clicked.connect(self.on_filter_changed)

        filter_layout.addWidget(type_label)
        filter_layout.addWidget(self.analysis_type_combo)
        filter_layout.addWidget(color_label)
        filter_layout.addWidget(self.color_by_combo)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addWidget(priority_label)
        filter_layout.addWidget(self.priority_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)

        self.layout.addWidget(filter_frame)

    def on_filter_changed(self):
        """Handle filter changes"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update scatter plot with to-do correlation data"""
        self.current_data = data.copy()
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            # Apply filters
            filtered_data = self.apply_filters(data)

            # Create chart based on selected analysis type
            analysis_type = self.analysis_type_combo.currentText()
            if analysis_type == 'Estimated vs Actual Hours':
                self.create_hours_correlation_chart(filtered_data)
            elif analysis_type == 'Priority vs Timeline':
                self.create_priority_timeline_chart(filtered_data)
            elif analysis_type == 'Category vs Priority':
                self.create_category_priority_chart(filtered_data)
            elif analysis_type == 'Status vs Creation Time':
                self.create_status_time_chart(filtered_data)
            elif analysis_type == 'Completion Time Analysis':
                self.create_completion_time_chart(filtered_data)
        except Exception as e:
            print(f"Error updating to-do scatter plot: {e}")
            self.show_error_message(str(e))

    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply current filters to data"""
        filtered_data = data.copy()

        # Apply status filter
        status_filter = self.status_filter_combo.currentText()
        if status_filter != 'All Status':
            filtered_data = filtered_data[filtered_data['status'] == status_filter]

        # Apply priority filter
        priority_filter = self.priority_filter_combo.currentText()
        if priority_filter != 'All Priorities':
            filtered_data = filtered_data[filtered_data['priority'] == priority_filter]

        return filtered_data

    def create_hours_correlation_chart(self, data: pd.DataFrame):
        """Create scatter plot showing estimated vs actual hours correlation"""
        # Filter data with both estimated and actual hours
        hours_data = data[(data['estimated_hours'] > 0) | (data['actual_hours'] > 0)].copy()

        if hours_data.empty:
            # Create a scatter plot with priority vs creation date instead
            self.create_priority_timeline_chart(data)
            return

        # Define colors for different statuses
        colors = {
            'Completed': '#28a745',
            'In Progress': '#ffc107',
            'Pending': '#6c757d',
            'Cancelled': '#dc3545'
        }

        # Create scatter plot
        fig = go.Figure()

        for status in hours_data['status'].unique():
            status_data = hours_data[hours_data['status'] == status]

            fig.add_trace(go.Scatter(
                x=status_data['estimated_hours'],
                y=status_data['actual_hours'],
                mode='markers',
                name=status,
                marker=dict(
                    color=colors.get(status, '#17a2b8'),
                    size=10,
                    opacity=0.7
                ),
                text=status_data['title'],
                hovertemplate='<b>%{text}</b><br>' +
                             'Status: %{fullData.name}<br>' +
                             'Estimated: %{x} hours<br>' +
                             'Actual: %{y} hours<br>' +
                             '<extra></extra>'
            ))

        # Add diagonal line for perfect estimation
        max_hours = max(hours_data['estimated_hours'].max(), hours_data['actual_hours'].max())
        fig.add_trace(go.Scatter(
            x=[0, max_hours],
            y=[0, max_hours],
            mode='lines',
            name='Perfect Estimation',
            line=dict(dash='dash', color='gray'),
            showlegend=True
        ))

        fig.update_layout(
            title={
                'text': '⏱️ Estimated vs Actual Hours',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Estimated Hours',
            yaxis_title='Actual Hours',
            font=dict(size=12),
            showlegend=True,
            legend=dict(x=0.02, y=0.98),
            margin=dict(l=60, r=20, t=60, b=60),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_priority_timeline_chart(self, data: pd.DataFrame):
        """Create scatter plot showing priority vs timeline"""
        # Prepare data
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')

        # Map priority to numeric values for y-axis
        priority_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Urgent': 4}
        data_copy['priority_numeric'] = data_copy['priority'].map(priority_map)

        # Define colors for different statuses
        colors = {
            'Completed': '#28a745',
            'In Progress': '#ffc107',
            'Pending': '#6c757d',
            'Cancelled': '#dc3545'
        }

        # Create scatter plot
        fig = go.Figure()

        for status in data_copy['status'].unique():
            status_data = data_copy[data_copy['status'] == status]

            fig.add_trace(go.Scatter(
                x=status_data['created_at'],
                y=status_data['priority_numeric'],
                mode='markers',
                name=status,
                marker=dict(
                    color=colors.get(status, '#17a2b8'),
                    size=10,
                    opacity=0.7
                ),
                text=status_data['title'],
                hovertemplate='<b>%{text}</b><br>' +
                             'Status: %{fullData.name}<br>' +
                             'Created: %{x}<br>' +
                             'Priority: %{customdata}<br>' +
                             '<extra></extra>',
                customdata=status_data['priority']
            ))

        fig.update_layout(
            title={
                'text': '📅 Task Priority Timeline',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Creation Date',
            yaxis=dict(
                title='Priority Level',
                tickmode='array',
                tickvals=[1, 2, 3, 4],
                ticktext=['Low', 'Medium', 'High', 'Urgent']
            ),
            font=dict(size=12),
            showlegend=True,
            legend=dict(x=0.02, y=0.98),
            margin=dict(l=60, r=20, t=60, b=60),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_category_priority_chart(self, data: pd.DataFrame):
        """Create scatter plot showing category vs priority correlation"""
        # Map priority to numeric values
        priority_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Urgent': 4}
        data_copy = data.copy()
        data_copy['priority_numeric'] = data_copy['priority'].map(priority_map)

        # Map category to numeric values
        categories = data_copy['category'].unique()
        category_map = {cat: i for i, cat in enumerate(categories)}
        data_copy['category_numeric'] = data_copy['category'].map(category_map)

        # Get color grouping
        color_by = self.color_by_combo.currentText().lower()

        fig = go.Figure()

        for group in data_copy[color_by].unique():
            group_data = data_copy[data_copy[color_by] == group]

            fig.add_trace(go.Scatter(
                x=group_data['category_numeric'],
                y=group_data['priority_numeric'],
                mode='markers',
                name=str(group),
                marker=dict(size=10, opacity=0.7),
                text=group_data['title'],
                hovertemplate=f'<b>%{{text}}</b><br>Category: %{{customdata[0]}}<br>Priority: %{{customdata[1]}}<br><extra></extra>',
                customdata=list(zip(group_data['category'], group_data['priority']))
            ))

        fig.update_layout(
            title='📊 Category vs Priority Analysis',
            xaxis=dict(
                title='Category',
                tickmode='array',
                tickvals=list(range(len(categories))),
                ticktext=categories
            ),
            yaxis=dict(
                title='Priority Level',
                tickmode='array',
                tickvals=[1, 2, 3, 4],
                ticktext=['Low', 'Medium', 'High', 'Urgent']
            ),
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_status_time_chart(self, data: pd.DataFrame):
        """Create scatter plot showing status vs creation time"""
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')

        # Map status to numeric values
        status_map = {'Pending': 1, 'In Progress': 2, 'Completed': 3, 'Cancelled': 4}
        data_copy['status_numeric'] = data_copy['status'].map(status_map)

        # Get color grouping
        color_by = self.color_by_combo.currentText().lower()

        fig = go.Figure()

        for group in data_copy[color_by].unique():
            group_data = data_copy[data_copy[color_by] == group]

            fig.add_trace(go.Scatter(
                x=group_data['created_at'],
                y=group_data['status_numeric'],
                mode='markers',
                name=str(group),
                marker=dict(size=10, opacity=0.7),
                text=group_data['title']
            ))

        fig.update_layout(
            title='📅 Status vs Creation Time',
            xaxis_title='Creation Date',
            yaxis=dict(
                title='Status',
                tickmode='array',
                tickvals=[1, 2, 3, 4],
                ticktext=['Pending', 'In Progress', 'Completed', 'Cancelled']
            ),
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_completion_time_chart(self, data: pd.DataFrame):
        """Create scatter plot showing completion time analysis"""
        completed_data = data[data['status'] == 'Completed'].copy()
        if completed_data.empty:
            self.show_no_data_message()
            return

        completed_data['created_at'] = pd.to_datetime(completed_data['created_at'], errors='coerce')
        completed_data['completed_at'] = pd.to_datetime(completed_data['completed_at'], errors='coerce')
        completed_data['completion_time'] = (completed_data['completed_at'] - completed_data['created_at']).dt.total_seconds() / 3600  # hours

        # Get color grouping
        color_by = self.color_by_combo.currentText().lower()

        fig = go.Figure()

        for group in completed_data[color_by].unique():
            group_data = completed_data[completed_data[color_by] == group]

            fig.add_trace(go.Scatter(
                x=group_data['created_at'],
                y=group_data['completion_time'],
                mode='markers',
                name=str(group),
                marker=dict(size=10, opacity=0.7),
                text=group_data['title']
            ))

        fig.update_layout(
            title='⏱️ Task Completion Time Analysis',
            xaxis_title='Creation Date',
            yaxis_title='Completion Time (Hours)',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)


class InteractiveHeatmapWidget(BaseInteractiveChart):
    """Interactive heatmap widget for to-do pattern analysis"""

    def create_filter_controls(self):
        """Create filter controls for heatmap - COMPACT: Reduced spacing for better space efficiency"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        # COMPACT: Reduced margins from 10,5,10,5 to 5,3,5,3
        filter_layout.setContentsMargins(5, 3, 5, 3)
        filter_layout.setSpacing(6)  # Reduced spacing between elements

        # Pattern type selector - COMPACT: Smaller font and tighter layout
        pattern_label = QLabel("Pattern:")
        pattern_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.pattern_type_combo = QComboBox()
        self.pattern_type_combo.addItems([
            'Time Patterns (Day/Hour)', 'Category vs Priority', 'Status vs Priority',
            'Monthly Patterns', 'Weekly Patterns', 'Completion Patterns'
        ])
        self.pattern_type_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.pattern_type_combo.currentTextChanged.connect(self.on_filter_changed)

        # Status filter - COMPACT: Smaller font
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(['All Status', 'Completed', 'Pending', 'In Progress', 'Cancelled'])
        self.status_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Priority filter - COMPACT: Smaller font
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItems(['All Priorities', 'Urgent', 'High', 'Medium', 'Low'])
        self.priority_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.priority_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Refresh button - COMPACT: Smaller button with reduced padding
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("font-size: 9px; padding: 3px 8px; margin: 0px;")
        refresh_btn.clicked.connect(self.on_filter_changed)

        filter_layout.addWidget(pattern_label)
        filter_layout.addWidget(self.pattern_type_combo)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addWidget(priority_label)
        filter_layout.addWidget(self.priority_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)

        self.layout.addWidget(filter_frame)

    def on_filter_changed(self):
        """Handle filter changes"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update heatmap with to-do pattern data"""
        self.current_data = data.copy()
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            # Apply filters
            filtered_data = self.apply_filters(data)

            # Create chart based on selected pattern type
            pattern_type = self.pattern_type_combo.currentText()
            if pattern_type == 'Time Patterns (Day/Hour)':
                self.create_completion_pattern_heatmap(filtered_data)
            elif pattern_type == 'Category vs Priority':
                self.create_category_priority_heatmap(filtered_data)
            elif pattern_type == 'Status vs Priority':
                self.create_status_priority_heatmap(filtered_data)
            elif pattern_type == 'Monthly Patterns':
                self.create_monthly_patterns_heatmap(filtered_data)
            elif pattern_type == 'Weekly Patterns':
                self.create_weekly_patterns_heatmap(filtered_data)
            elif pattern_type == 'Completion Patterns':
                self.create_completion_status_heatmap(filtered_data)
        except Exception as e:
            print(f"Error updating to-do heatmap: {e}")
            self.show_error_message(str(e))

    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply current filters to data"""
        filtered_data = data.copy()

        # Apply status filter for non-status patterns
        pattern_type = self.pattern_type_combo.currentText()
        if 'Status' not in pattern_type:
            status_filter = self.status_filter_combo.currentText()
            if status_filter != 'All Status':
                filtered_data = filtered_data[filtered_data['status'] == status_filter]

        # Apply priority filter for non-priority patterns
        if 'Priority' not in pattern_type:
            priority_filter = self.priority_filter_combo.currentText()
            if priority_filter != 'All Priorities':
                filtered_data = filtered_data[filtered_data['priority'] == priority_filter]

        return filtered_data

    def create_completion_pattern_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing task completion patterns"""
        # Prepare data
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')

        # Extract day of week and hour from creation time
        data_copy['day_of_week'] = data_copy['created_at'].dt.day_name()
        data_copy['hour'] = data_copy['created_at'].dt.hour

        # Create pivot table for heatmap
        heatmap_data = data_copy.groupby(['day_of_week', 'hour']).size().reset_index(name='task_count')

        if heatmap_data.empty:
            # Create category vs priority heatmap instead
            self.create_category_priority_heatmap(data)
            return

        # Pivot for heatmap format
        heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='task_count').fillna(0)

        # Reorder days of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex(day_order, fill_value=0)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='Blues',
            hovertemplate='<b>%{y}</b><br>' +
                         'Hour: %{x}:00<br>' +
                         'Tasks Created: %{z}<br>' +
                         '<extra></extra>'
        ))

        fig.update_layout(
            title={
                'text': '🔥 Task Creation Pattern Heatmap',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            font=dict(size=12),
            margin=dict(l=100, r=20, t=60, b=60),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_category_priority_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing category vs priority distribution"""
        # Create cross-tabulation
        heatmap_data = pd.crosstab(data['category'], data['priority'])

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Viridis',
            hovertemplate='<b>%{y}</b><br>' +
                         'Priority: %{x}<br>' +
                         'Task Count: %{z}<br>' +
                         '<extra></extra>'
        ))

        fig.update_layout(
            title={
                'text': '🔥 Category vs Priority Heatmap',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Priority Level',
            yaxis_title='Category',
            font=dict(size=12),
            margin=dict(l=100, r=20, t=60, b=60),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_status_priority_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing status vs priority distribution"""
        heatmap_data = pd.crosstab(data['status'], data['priority'])

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Blues',
            hovertemplate='<b>%{y}</b><br>Priority: %{x}<br>Task Count: %{z}<br><extra></extra>'
        ))

        fig.update_layout(
            title='🔥 Status vs Priority Heatmap',
            xaxis_title='Priority Level',
            yaxis_title='Status',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_monthly_patterns_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing monthly task creation patterns"""
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')
        data_copy['month'] = data_copy['created_at'].dt.month_name()
        data_copy['year'] = data_copy['created_at'].dt.year

        heatmap_data = data_copy.groupby(['year', 'month']).size().reset_index(name='count')
        heatmap_pivot = heatmap_data.pivot(index='year', columns='month', values='count').fillna(0)

        # Reorder months
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        heatmap_pivot = heatmap_pivot.reindex(columns=month_order, fill_value=0)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='Viridis',
            hovertemplate='<b>%{y}</b><br>Month: %{x}<br>Tasks Created: %{z}<br><extra></extra>'
        ))

        fig.update_layout(
            title='🔥 Monthly Task Creation Patterns',
            xaxis_title='Month',
            yaxis_title='Year',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_weekly_patterns_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing weekly task patterns"""
        data_copy = data.copy()
        data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')
        data_copy['weekday'] = data_copy['created_at'].dt.day_name()
        data_copy['week'] = data_copy['created_at'].dt.isocalendar().week

        heatmap_data = data_copy.groupby(['week', 'weekday']).size().reset_index(name='count')
        heatmap_pivot = heatmap_data.pivot(index='week', columns='weekday', values='count').fillna(0)

        # Reorder weekdays
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_pivot = heatmap_pivot.reindex(columns=weekday_order, fill_value=0)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='Plasma',
            hovertemplate='<b>Week %{y}</b><br>Day: %{x}<br>Tasks Created: %{z}<br><extra></extra>'
        ))

        fig.update_layout(
            title='🔥 Weekly Task Creation Patterns',
            xaxis_title='Day of Week',
            yaxis_title='Week Number',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)

    def create_completion_status_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing completion patterns by category and status"""
        heatmap_data = pd.crosstab(data['category'], data['status'])

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdYlGn',
            hovertemplate='<b>%{y}</b><br>Status: %{x}<br>Task Count: %{z}<br><extra></extra>'
        ))

        fig.update_layout(
            title='🔥 Category vs Status Completion Patterns',
            xaxis_title='Status',
            yaxis_title='Category',
            font=dict(size=12),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)


class InteractiveTreemapWidget(BaseInteractiveChart):
    """Interactive treemap widget for to-do category visualization"""

    def create_filter_controls(self):
        """Create filter controls for treemap - COMPACT: Reduced spacing for better space efficiency"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        # COMPACT: Reduced margins from 10,5,10,5 to 5,3,5,3
        filter_layout.setContentsMargins(5, 3, 5, 3)
        filter_layout.setSpacing(6)  # Reduced spacing between elements

        # Hierarchy type selector - COMPACT: Smaller font and tighter layout
        hierarchy_label = QLabel("Hierarchy:")
        hierarchy_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.hierarchy_type_combo = QComboBox()
        self.hierarchy_type_combo.addItems([
            'Category → Status', 'Priority → Category', 'Status → Priority',
            'Category → Priority', 'Priority → Status', 'Status → Category'
        ])
        self.hierarchy_type_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.hierarchy_type_combo.currentTextChanged.connect(self.on_filter_changed)

        # Metric selector - COMPACT: Smaller font
        metric_label = QLabel("Size By:")
        metric_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(['Task Count', 'Estimated Hours', 'Actual Hours'])
        self.metric_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.metric_combo.currentTextChanged.connect(self.on_filter_changed)

        # Status filter - COMPACT: Smaller font
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(['All Status', 'Completed', 'Pending', 'In Progress', 'Cancelled'])
        self.status_filter_combo.setStyleSheet("font-size: 9px; padding: 2px;")
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)

        # Refresh button - COMPACT: Smaller button with reduced padding
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("font-size: 9px; padding: 3px 8px; margin: 0px;")
        refresh_btn.clicked.connect(self.on_filter_changed)

        filter_layout.addWidget(hierarchy_label)
        filter_layout.addWidget(self.hierarchy_type_combo)
        filter_layout.addWidget(metric_label)
        filter_layout.addWidget(self.metric_combo)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)

        self.layout.addWidget(filter_frame)

    def on_filter_changed(self):
        """Handle filter changes"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update treemap with to-do category data"""
        self.current_data = data.copy()
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            # Apply filters
            filtered_data = self.apply_filters(data)

            # Create treemap based on selected hierarchy
            hierarchy_type = self.hierarchy_type_combo.currentText()
            if hierarchy_type == 'Category → Status':
                self.create_category_treemap(filtered_data)
            elif hierarchy_type == 'Priority → Category':
                self.create_priority_category_treemap(filtered_data)
            elif hierarchy_type == 'Status → Priority':
                self.create_status_priority_treemap(filtered_data)
            else:
                self.create_category_treemap(filtered_data)  # Default
        except Exception as e:
            print(f"Error updating to-do treemap: {e}")
            self.show_error_message(str(e))

    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply current filters to data"""
        filtered_data = data.copy()

        # Apply status filter for non-status hierarchies
        hierarchy_type = self.hierarchy_type_combo.currentText()
        if not hierarchy_type.startswith('Status'):
            status_filter = self.status_filter_combo.currentText()
            if status_filter != 'All Status':
                filtered_data = filtered_data[filtered_data['status'] == status_filter]

        return filtered_data

    def create_category_treemap(self, data: pd.DataFrame):
        """Create treemap showing task distribution by category and status"""
        # Prepare hierarchical data
        treemap_data = data.groupby(['category', 'status']).size().reset_index(name='count')

        # Create treemap
        fig = go.Figure(go.Treemap(
            labels=treemap_data['category'] + ' - ' + treemap_data['status'],
            parents=treemap_data['category'],
            values=treemap_data['count'],
            textinfo="label+value+percent parent",
            hovertemplate='<b>%{label}</b><br>' +
                         'Tasks: %{value}<br>' +
                         'Percentage: %{percentParent}<br>' +
                         '<extra></extra>'
        ))

        fig.update_layout(
            title={
                'text': '🌳 Task Category & Status Treemap',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'family': 'Arial, sans-serif'}
            },
            font=dict(size=12),
            margin=dict(l=20, r=20, t=60, b=20),
            height=400
        )

        # STYLING CONSISTENCY: Apply theme colors and use consistent HTML generation
        fig = self.apply_theme_to_plotly_fig(fig)
        html_content = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_content)
