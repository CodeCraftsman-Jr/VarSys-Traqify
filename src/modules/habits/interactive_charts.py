"""
Interactive Habit Charts Module
Provides advanced interactive chart widgets using Plotly for habit analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGroupBox,
    QComboBox, QSpinBox, QPushButton, QDateEdit, QCheckBox, QGridLayout,
    QScrollArea, QSplitter, QTabWidget, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QPalette

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True

    # Try to import QWebEngineView
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        WEBENGINE_AVAILABLE = True
    except ImportError:
        WEBENGINE_AVAILABLE = False
        print("QWebEngineView not available. Interactive charts will use fallback.")

except ImportError:
    PLOTLY_AVAILABLE = False
    WEBENGINE_AVAILABLE = False
    print("Plotly not available. Interactive charts will use basic matplotlib fallback.")

# Print availability status for debugging
print(f"Habit Charts: PLOTLY_AVAILABLE = {PLOTLY_AVAILABLE}")
print(f"Habit Charts: WEBENGINE_AVAILABLE = {WEBENGINE_AVAILABLE}")

# Import matplotlib as fallback
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.qt_compat import QtWidgets
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
    print("Habit Charts: MATPLOTLIB_AVAILABLE = True")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Habit Charts: MATPLOTLIB_AVAILABLE = False")


class InteractiveChartWidget(QWidget):
    """Base class for interactive charts using Plotly"""

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
        elif theme == 'dark':
            return {
                'background': '#1e1e1e',
                'secondary_background': '#252526',
                'controls_background': '#2d2d30',
                'border': '#3e3e42',
                'text': '#ffffff'
            }
        elif theme == 'colorwave':
            return {
                'background': '#0a0a1a',
                'secondary_background': '#1a1a2e',
                'controls_background': '#2d2d30',
                'border': '#4a3c5a',
                'text': '#ffffff'
            }
        else:
            # Default to light theme
            return {
                'background': '#ffffff',
                'secondary_background': '#f9f9f9',
                'controls_background': '#f0f0f0',
                'border': '#e0e0e0',
                'text': '#000000'
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
        """Setup the basic UI structure - APPLIED TO DO ANALYTICS APPROACH"""
        layout = QVBoxLayout(self)
        # APPLIED TO DO ANALYTICS APPROACH: Moderate margins for proper chart presentation
        layout.setContentsMargins(10, 10, 10, 10)

        # Controls section
        self.controls_frame = QFrame()
        self.controls_layout = QHBoxLayout(self.controls_frame)
        self.setup_controls()
        layout.addWidget(self.controls_frame)

        # APPLIED TO DO ANALYTICS APPROACH: Set reasonable minimum size but allow natural expansion
        self.setMinimumSize(400, 350)  # Reasonable size for chart visibility
        # APPLIED TO DO ANALYTICS APPROACH: Allow full expansion like To Do Analytics
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Chart section
        if PLOTLY_AVAILABLE and WEBENGINE_AVAILABLE:
            print(f"Setting up WebEngine view for {self.__class__.__name__}")
            self.web_view = QWebEngineView()

            # APPLIED TO DO ANALYTICS APPROACH: Set reasonable size for web view with natural expansion
            self.web_view.setMinimumSize(380, 300)  # Reasonable size for chart visibility
            # APPLIED TO DO ANALYTICS APPROACH: Allow full expansion like To Do Analytics
            self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # CRITICAL FIX: Add visible border to help debug visibility issues
            self.web_view.setStyleSheet("""
                QWebEngineView {
                    border: 2px solid #6f42c1;
                    background-color: white;
                    min-height: 300px;
                    min-width: 380px;
                }
            """)

            # CRITICAL FIX: Apply theme-aware styling to web view to fix black background
            self.apply_web_view_styling()

            layout.addWidget(self.web_view)

            # Create initial empty chart
            self._create_initial_chart()
        else:
            if not PLOTLY_AVAILABLE:
                message = "Interactive charts require Plotly. Please install plotly."
            elif not WEBENGINE_AVAILABLE:
                message = "Interactive charts require QWebEngineWidgets."
            else:
                message = "Interactive charts temporarily unavailable."

            self.chart_label = QLabel(message)
            self.chart_label.setAlignment(Qt.AlignCenter)
            self.chart_label.setStyleSheet("color: orange; font-size: 12px; padding: 20px;")
            layout.addWidget(self.chart_label)

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

        # CRITICAL FIX: Inject STRONGER theme-aware CSS to override ALL Plotly styling
        theme_css = f"""
        <style>
            /* CRITICAL: Override ALL possible background sources with maximum specificity */
            html, body {{
                background-color: {background} !important;
                background: {background} !important;
                margin: 0 !important;
                padding: 0 !important;
            }}

            /* Target all Plotly containers */
            .plotly-graph-div,
            .plotly-graph-div > div,
            .js-plotly-plot,
            .plot-container,
            .svg-container {{
                background-color: {background} !important;
                background: {background} !important;
            }}

            /* Override any remaining containers */
            div[id*="plotly"] {{
                background-color: {background} !important;
                background: {background} !important;
            }}
        </style>
        """

        # Insert CSS right after <head> tag
        head_end = html_str.find('</head>')
        if head_end != -1:
            html_str = html_str[:head_end] + theme_css + html_str[head_end:]

        return html_str

    def setup_controls(self):
        """Setup control widgets - to be implemented by subclasses"""
        pass

    def _create_initial_chart(self):
        """Create initial empty chart"""
        if PLOTLY_AVAILABLE and WEBENGINE_AVAILABLE:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="Habit Analytics Chart",
                height=400,
                showlegend=False,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False)
            )
            
            # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
            fig = self.apply_theme_to_plotly_fig(fig)
            html_str = self.generate_theme_aware_html(fig)
            self.web_view.setHtml(html_str)

    def update_chart(self, data: pd.DataFrame):
        """Update chart with new data - to be implemented by subclasses"""
        self.current_data = data.copy() if not data.empty else pd.DataFrame()


class InteractivePieChartWidget(InteractiveChartWidget):
    """Interactive pie chart with drill-down functionality for habit completion rates"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_type = 'category'  # category, habit, completion_status
        self.show_percentages = True
        self.drill_down_level = 0
        self.current_category = None
        
    def setup_controls(self):
        """Setup pie chart specific controls"""
        # Chart type selector
        type_label = QLabel("View by:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Category', 'Individual Habits', 'Completion Status'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        # Show percentages checkbox
        self.percentages_cb = QCheckBox("Show Percentages")
        self.percentages_cb.setChecked(True)
        self.percentages_cb.toggled.connect(self.on_percentages_toggled)
        
        # Drill down controls
        self.drill_label = QLabel("Drill Down:")
        self.drill_back_btn = QPushButton("← Back")
        self.drill_back_btn.clicked.connect(self.drill_back)
        self.drill_back_btn.setEnabled(False)
        
        # Add to layout
        self.controls_layout.addWidget(type_label)
        self.controls_layout.addWidget(self.type_combo)
        self.controls_layout.addWidget(self.percentages_cb)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.drill_label)
        self.controls_layout.addWidget(self.drill_back_btn)
    
    def on_type_changed(self, text):
        """Handle chart type change"""
        type_map = {
            'Category': 'category',
            'Individual Habits': 'habit',
            'Completion Status': 'completion_status'
        }
        self.chart_type = type_map.get(text, 'category')
        self.drill_down_level = 0
        self.current_category = None
        self.drill_back_btn.setEnabled(False)
        self.update_chart(self.current_data)
    
    def on_percentages_toggled(self, checked):
        """Handle show percentages toggle"""
        self.show_percentages = checked
        self.update_chart(self.current_data)
    
    def drill_back(self):
        """Handle drill back action"""
        self.drill_down_level = 0
        self.current_category = None
        self.drill_back_btn.setEnabled(False)
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update pie chart with habit completion data"""
        super().update_chart(data)
        
        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return
        
        try:
            if self.chart_type == 'category':
                self._create_category_chart(data)
            elif self.chart_type == 'habit':
                self._create_habit_chart(data)
            elif self.chart_type == 'completion_status':
                self._create_completion_status_chart(data)
        except Exception as e:
            print(f"Error updating pie chart: {e}")
    
    def _create_category_chart(self, data: pd.DataFrame):
        """Create pie chart by habit categories"""
        # Group by category and calculate completion rates
        if 'category' not in data.columns:
            # If no category info, create a simple completion chart
            self._create_completion_status_chart(data)
            return
            
        category_stats = data.groupby('category').agg({
            'is_completed': ['count', 'sum'],
            'habit_name': 'nunique'
        }).round(2)
        
        category_stats.columns = ['total_records', 'completed_records', 'unique_habits']
        category_stats['completion_rate'] = (category_stats['completed_records'] / category_stats['total_records'] * 100).round(1)
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=category_stats.index,
            values=category_stats['completion_rate'],
            textinfo='label+percent' if self.show_percentages else 'label',
            hovertemplate='<b>%{label}</b><br>' +
                         'Completion Rate: %{value}%<br>' +
                         'Habits: %{customdata[0]}<br>' +
                         'Total Records: %{customdata[1]}<br>' +
                         'Completed: %{customdata[2]}<extra></extra>',
            customdata=list(zip(
                category_stats['unique_habits'],
                category_stats['total_records'],
                category_stats['completed_records']
            ))
        )])
        
        fig.update_layout(
            title="Habit Completion Rate by Category",
            height=500,
            showlegend=True
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)
    
    def _create_habit_chart(self, data: pd.DataFrame):
        """Create pie chart by individual habits"""
        habit_stats = data.groupby('habit_name').agg({
            'is_completed': ['count', 'sum']
        }).round(2)
        
        habit_stats.columns = ['total_records', 'completed_records']
        habit_stats['completion_rate'] = (habit_stats['completed_records'] / habit_stats['total_records'] * 100).round(1)
        
        # Limit to top 10 habits for readability
        habit_stats = habit_stats.nlargest(10, 'completion_rate')
        
        fig = go.Figure(data=[go.Pie(
            labels=habit_stats.index,
            values=habit_stats['completion_rate'],
            textinfo='label+percent' if self.show_percentages else 'label',
            hovertemplate='<b>%{label}</b><br>' +
                         'Completion Rate: %{value}%<br>' +
                         'Total Records: %{customdata[0]}<br>' +
                         'Completed: %{customdata[1]}<extra></extra>',
            customdata=list(zip(
                habit_stats['total_records'],
                habit_stats['completed_records']
            ))
        )])
        
        fig.update_layout(
            title="Top 10 Habits by Completion Rate",
            height=500,
            showlegend=True
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)
    
    def _create_completion_status_chart(self, data: pd.DataFrame):
        """Create pie chart by completion status"""
        completed_count = len(data[data['is_completed'] == True])
        not_completed_count = len(data[data['is_completed'] == False])
        
        fig = go.Figure(data=[go.Pie(
            labels=['Completed', 'Not Completed'],
            values=[completed_count, not_completed_count],
            textinfo='label+percent' if self.show_percentages else 'label',
            colors=['#2E8B57', '#DC143C'],
            hovertemplate='<b>%{label}</b><br>' +
                         'Count: %{value}<br>' +
                         'Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Overall Habit Completion Status",
            height=500,
            showlegend=True
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveTimeSeriesWidget(InteractiveChartWidget):
    """Interactive time series chart with zoom and pan functionality for habit streaks and trends"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aggregation = 'daily'
        self.show_streaks = True
        self.show_trend = True
        self.date_range = 30  # days

    def setup_controls(self):
        """Setup time series specific controls"""
        # Aggregation selector
        agg_label = QLabel("Aggregation:")
        self.agg_combo = QComboBox()
        self.agg_combo.addItems(['Daily', 'Weekly', 'Monthly'])
        self.agg_combo.currentTextChanged.connect(self.on_aggregation_changed)

        # Date range selector
        range_label = QLabel("Date Range:")
        self.range_spin = QSpinBox()
        self.range_spin.setRange(7, 365)
        self.range_spin.setValue(30)
        self.range_spin.setSuffix(" days")
        self.range_spin.valueChanged.connect(self.on_range_changed)

        # Show streaks checkbox
        self.streaks_cb = QCheckBox("Show Streaks")
        self.streaks_cb.setChecked(True)
        self.streaks_cb.toggled.connect(self.on_streaks_toggled)

        # Show trend checkbox
        self.trend_cb = QCheckBox("Show Trend")
        self.trend_cb.setChecked(True)
        self.trend_cb.toggled.connect(self.on_trend_toggled)

        # Add to layout
        self.controls_layout.addWidget(agg_label)
        self.controls_layout.addWidget(self.agg_combo)
        self.controls_layout.addWidget(range_label)
        self.controls_layout.addWidget(self.range_spin)
        self.controls_layout.addWidget(self.streaks_cb)
        self.controls_layout.addWidget(self.trend_cb)
        self.controls_layout.addStretch()

    def on_aggregation_changed(self, text):
        """Handle aggregation change"""
        self.aggregation = text.lower()
        self.update_chart(self.current_data)

    def on_range_changed(self, value):
        """Handle date range change"""
        self.date_range = value
        self.update_chart(self.current_data)

    def on_streaks_toggled(self, checked):
        """Handle show streaks toggle"""
        self.show_streaks = checked
        self.update_chart(self.current_data)

    def on_trend_toggled(self, checked):
        """Handle show trend toggle"""
        self.show_trend = checked
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update time series chart with habit completion trends"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            # Filter data by date range
            end_date = pd.Timestamp.now()
            start_date = end_date - pd.Timedelta(days=self.date_range)

            data_copy = data.copy()
            data_copy['date'] = pd.to_datetime(data_copy['date'])
            filtered_data = data_copy[
                (data_copy['date'] >= start_date) &
                (data_copy['date'] <= end_date)
            ]

            if filtered_data.empty:
                return

            self._create_time_series_chart(filtered_data)
        except Exception as e:
            print(f"Error updating time series chart: {e}")

    def _create_time_series_chart(self, data: pd.DataFrame):
        """Create time series chart with habit completion trends"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Completion Rate', 'Habit Streaks'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )

        # Aggregate data based on selected aggregation
        if self.aggregation == 'daily':
            time_group = data.groupby(data['date'].dt.date)
        elif self.aggregation == 'weekly':
            time_group = data.groupby(data['date'].dt.to_period('W'))
        else:  # monthly
            time_group = data.groupby(data['date'].dt.to_period('M'))

        # Calculate completion rates
        completion_stats = time_group.agg({
            'is_completed': ['count', 'sum']
        })
        completion_stats.columns = ['total', 'completed']
        completion_stats['completion_rate'] = (completion_stats['completed'] / completion_stats['total'] * 100).round(1)

        # Add completion rate line
        fig.add_trace(
            go.Scatter(
                x=completion_stats.index,
                y=completion_stats['completion_rate'],
                mode='lines+markers',
                name='Completion Rate',
                line=dict(color='#2E8B57', width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Completion Rate: %{y}%<br>Completed: %{customdata[0]}<br>Total: %{customdata[1]}<extra></extra>',
                customdata=list(zip(completion_stats['completed'], completion_stats['total']))
            ),
            row=1, col=1
        )

        # Add trend line if enabled
        if self.show_trend and len(completion_stats) > 2:
            x_numeric = np.arange(len(completion_stats))
            z = np.polyfit(x_numeric, completion_stats['completion_rate'], 1)
            trend_line = np.poly1d(z)(x_numeric)

            fig.add_trace(
                go.Scatter(
                    x=completion_stats.index,
                    y=trend_line,
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', width=1, dash='dash'),
                    hovertemplate='Trend: %{y:.1f}%<extra></extra>'
                ),
                row=1, col=1
            )

        # Add streak information if enabled
        if self.show_streaks:
            # Calculate streaks for each habit
            habit_streaks = self._calculate_streaks(data)

            for habit_name, streak_data in habit_streaks.items():
                fig.add_trace(
                    go.Bar(
                        x=[habit_name],
                        y=[streak_data['current_streak']],
                        name=f'{habit_name} Streak',
                        hovertemplate=f'<b>{habit_name}</b><br>Current Streak: {streak_data["current_streak"]} days<br>Best Streak: {streak_data["best_streak"]} days<extra></extra>',
                        showlegend=False
                    ),
                    row=2, col=1
                )

        fig.update_layout(
            title="Habit Completion Trends Over Time",
            height=600,
            showlegend=True
        )

        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Completion Rate (%)", row=1, col=1)
        fig.update_xaxes(title_text="Habits", row=2, col=1)
        fig.update_yaxes(title_text="Streak (days)", row=2, col=1)

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _calculate_streaks(self, data: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """Calculate current and best streaks for each habit"""
        streaks = {}

        for habit_name in data['habit_name'].unique():
            habit_data = data[data['habit_name'] == habit_name].sort_values('date')

            current_streak = 0
            best_streak = 0
            temp_streak = 0

            for _, record in habit_data.iterrows():
                if record['is_completed']:
                    temp_streak += 1
                    best_streak = max(best_streak, temp_streak)
                else:
                    temp_streak = 0

            # Current streak is the last consecutive completed days
            recent_data = habit_data.tail(30)  # Last 30 days
            for _, record in recent_data[::-1].iterrows():
                if record['is_completed']:
                    current_streak += 1
                else:
                    break

            streaks[habit_name] = {
                'current_streak': current_streak,
                'best_streak': best_streak
            }

        return streaks


class InteractiveBarChartWidget(InteractiveChartWidget):
    """Interactive bar chart with filtering options for habit performance comparisons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_type = 'completion_rate'  # completion_rate, streak_comparison, category_performance
        self.sort_order = 'desc'
        self.show_values = True
        self.top_n = 10

    def setup_controls(self):
        """Setup bar chart specific controls"""
        # Chart type selector
        type_label = QLabel("Chart Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Completion Rate', 'Streak Comparison', 'Category Performance'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        # Sort order selector
        sort_label = QLabel("Sort:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Descending', 'Ascending'])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)

        # Top N selector
        top_label = QLabel("Show Top:")
        self.top_spin = QSpinBox()
        self.top_spin.setRange(5, 50)
        self.top_spin.setValue(10)
        self.top_spin.valueChanged.connect(self.on_top_changed)

        # Show values checkbox
        self.values_cb = QCheckBox("Show Values")
        self.values_cb.setChecked(True)
        self.values_cb.toggled.connect(self.on_values_toggled)

        # Add to layout
        self.controls_layout.addWidget(type_label)
        self.controls_layout.addWidget(self.type_combo)
        self.controls_layout.addWidget(sort_label)
        self.controls_layout.addWidget(self.sort_combo)
        self.controls_layout.addWidget(top_label)
        self.controls_layout.addWidget(self.top_spin)
        self.controls_layout.addWidget(self.values_cb)
        self.controls_layout.addStretch()

    def on_type_changed(self, text):
        """Handle chart type change"""
        type_map = {
            'Completion Rate': 'completion_rate',
            'Streak Comparison': 'streak_comparison',
            'Category Performance': 'category_performance'
        }
        self.chart_type = type_map.get(text, 'completion_rate')
        self.update_chart(self.current_data)

    def on_sort_changed(self, text):
        """Handle sort order change"""
        self.sort_order = 'desc' if text == 'Descending' else 'asc'
        self.update_chart(self.current_data)

    def on_top_changed(self, value):
        """Handle top N change"""
        self.top_n = value
        self.update_chart(self.current_data)

    def on_values_toggled(self, checked):
        """Handle show values toggle"""
        self.show_values = checked
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update bar chart with habit performance data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            if self.chart_type == 'completion_rate':
                self._create_completion_rate_chart(data)
            elif self.chart_type == 'streak_comparison':
                self._create_streak_comparison_chart(data)
            elif self.chart_type == 'category_performance':
                self._create_category_performance_chart(data)
        except Exception as e:
            print(f"Error updating bar chart: {e}")

    def _create_completion_rate_chart(self, data: pd.DataFrame):
        """Create bar chart showing habit completion rates"""
        habit_stats = data.groupby('habit_name').agg({
            'is_completed': ['count', 'sum']
        }).round(2)

        habit_stats.columns = ['total_records', 'completed_records']
        habit_stats['completion_rate'] = (habit_stats['completed_records'] / habit_stats['total_records'] * 100).round(1)

        # Sort and limit
        if self.sort_order == 'desc':
            habit_stats = habit_stats.nlargest(self.top_n, 'completion_rate')
        else:
            habit_stats = habit_stats.nsmallest(self.top_n, 'completion_rate')

        fig = go.Figure(data=[go.Bar(
            x=habit_stats.index,
            y=habit_stats['completion_rate'],
            text=habit_stats['completion_rate'].astype(str) + '%' if self.show_values else None,
            textposition='auto',
            marker_color='#2E8B57',
            hovertemplate='<b>%{x}</b><br>' +
                         'Completion Rate: %{y}%<br>' +
                         'Total Records: %{customdata[0]}<br>' +
                         'Completed: %{customdata[1]}<extra></extra>',
            customdata=list(zip(
                habit_stats['total_records'],
                habit_stats['completed_records']
            ))
        )])

        fig.update_layout(
            title=f"Top {self.top_n} Habits by Completion Rate",
            xaxis_title="Habits",
            yaxis_title="Completion Rate (%)",
            height=500,
            showlegend=False
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_streak_comparison_chart(self, data: pd.DataFrame):
        """Create bar chart comparing habit streaks"""
        streaks = self._calculate_streaks(data)

        if not streaks:
            return

        habit_names = list(streaks.keys())[:self.top_n]
        current_streaks = [streaks[name]['current_streak'] for name in habit_names]
        best_streaks = [streaks[name]['best_streak'] for name in habit_names]

        fig = go.Figure(data=[
            go.Bar(
                name='Current Streak',
                x=habit_names,
                y=current_streaks,
                text=current_streaks if self.show_values else None,
                textposition='auto',
                marker_color='#4CAF50'
            ),
            go.Bar(
                name='Best Streak',
                x=habit_names,
                y=best_streaks,
                text=best_streaks if self.show_values else None,
                textposition='auto',
                marker_color='#FF9800'
            )
        ])

        fig.update_layout(
            title="Habit Streak Comparison",
            xaxis_title="Habits",
            yaxis_title="Streak (days)",
            height=500,
            barmode='group'
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_category_performance_chart(self, data: pd.DataFrame):
        """Create bar chart showing category performance"""
        if 'category' not in data.columns:
            # Fallback to completion rate chart
            self._create_completion_rate_chart(data)
            return

        category_stats = data.groupby('category').agg({
            'is_completed': ['count', 'sum'],
            'habit_name': 'nunique'
        }).round(2)

        category_stats.columns = ['total_records', 'completed_records', 'unique_habits']
        category_stats['completion_rate'] = (category_stats['completed_records'] / category_stats['total_records'] * 100).round(1)

        # Sort and limit
        if self.sort_order == 'desc':
            category_stats = category_stats.nlargest(self.top_n, 'completion_rate')
        else:
            category_stats = category_stats.nsmallest(self.top_n, 'completion_rate')

        fig = go.Figure(data=[go.Bar(
            x=category_stats.index,
            y=category_stats['completion_rate'],
            text=category_stats['completion_rate'].astype(str) + '%' if self.show_values else None,
            textposition='auto',
            marker_color='#9C27B0',
            hovertemplate='<b>%{x}</b><br>' +
                         'Completion Rate: %{y}%<br>' +
                         'Unique Habits: %{customdata[0]}<br>' +
                         'Total Records: %{customdata[1]}<br>' +
                         'Completed: %{customdata[2]}<extra></extra>',
            customdata=list(zip(
                category_stats['unique_habits'],
                category_stats['total_records'],
                category_stats['completed_records']
            ))
        )])

        fig.update_layout(
            title="Category Performance Comparison",
            xaxis_title="Categories",
            yaxis_title="Completion Rate (%)",
            height=500,
            showlegend=False
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveScatterPlotWidget(InteractiveChartWidget):
    """Interactive scatter plot showing correlations between different habits"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_metric = 'completion_rate'
        self.y_metric = 'streak_length'
        self.color_by = 'category'
        self.size_by = 'total_records'

    def setup_controls(self):
        """Setup scatter plot specific controls"""
        # X-axis metric selector
        x_label = QLabel("X-Axis:")
        self.x_combo = QComboBox()
        self.x_combo.addItems(['Completion Rate', 'Streak Length', 'Total Records', 'Days Active'])
        self.x_combo.currentTextChanged.connect(self.on_x_changed)

        # Y-axis metric selector
        y_label = QLabel("Y-Axis:")
        self.y_combo = QComboBox()
        self.y_combo.addItems(['Streak Length', 'Completion Rate', 'Total Records', 'Days Active'])
        self.y_combo.currentTextChanged.connect(self.on_y_changed)

        # Color by selector
        color_label = QLabel("Color by:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(['Category', 'Habit Name', 'Completion Status'])
        self.color_combo.currentTextChanged.connect(self.on_color_changed)

        # Size by selector
        size_label = QLabel("Size by:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(['Total Records', 'Completion Rate', 'Streak Length'])
        self.size_combo.currentTextChanged.connect(self.on_size_changed)

        # Add to layout
        self.controls_layout.addWidget(x_label)
        self.controls_layout.addWidget(self.x_combo)
        self.controls_layout.addWidget(y_label)
        self.controls_layout.addWidget(self.y_combo)
        self.controls_layout.addWidget(color_label)
        self.controls_layout.addWidget(self.color_combo)
        self.controls_layout.addWidget(size_label)
        self.controls_layout.addWidget(self.size_combo)
        self.controls_layout.addStretch()

    def on_x_changed(self, text):
        """Handle X-axis metric change"""
        metric_map = {
            'Completion Rate': 'completion_rate',
            'Streak Length': 'streak_length',
            'Total Records': 'total_records',
            'Days Active': 'days_active'
        }
        self.x_metric = metric_map.get(text, 'completion_rate')
        self.update_chart(self.current_data)

    def on_y_changed(self, text):
        """Handle Y-axis metric change"""
        metric_map = {
            'Completion Rate': 'completion_rate',
            'Streak Length': 'streak_length',
            'Total Records': 'total_records',
            'Days Active': 'days_active'
        }
        self.y_metric = metric_map.get(text, 'streak_length')
        self.update_chart(self.current_data)

    def on_color_changed(self, text):
        """Handle color by change"""
        color_map = {
            'Category': 'category',
            'Habit Name': 'habit_name',
            'Completion Status': 'completion_status'
        }
        self.color_by = color_map.get(text, 'category')
        self.update_chart(self.current_data)

    def on_size_changed(self, text):
        """Handle size by change"""
        size_map = {
            'Total Records': 'total_records',
            'Completion Rate': 'completion_rate',
            'Streak Length': 'streak_length'
        }
        self.size_by = size_map.get(text, 'total_records')
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update scatter plot with habit correlation data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            self._create_scatter_plot(data)
        except Exception as e:
            print(f"Error updating scatter plot: {e}")

    def _create_scatter_plot(self, data: pd.DataFrame):
        """Create scatter plot showing habit correlations"""
        # Prepare data for scatter plot
        scatter_data = self._prepare_scatter_data(data)

        if scatter_data.empty:
            return

        # Create scatter plot
        fig = px.scatter(
            scatter_data,
            x=self.x_metric,
            y=self.y_metric,
            color=self.color_by if self.color_by in scatter_data.columns else None,
            size=self.size_by if self.size_by in scatter_data.columns else None,
            hover_data=['habit_name', 'completion_rate', 'streak_length', 'total_records'],
            title=f"Habit Correlation: {self.x_metric.replace('_', ' ').title()} vs {self.y_metric.replace('_', ' ').title()}"
        )

        fig.update_layout(
            height=500,
            xaxis_title=self.x_metric.replace('_', ' ').title(),
            yaxis_title=self.y_metric.replace('_', ' ').title()
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _prepare_scatter_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for scatter plot visualization"""
        # Calculate metrics for each habit
        habit_metrics = []

        for habit_name in data['habit_name'].unique():
            habit_data = data[data['habit_name'] == habit_name]

            total_records = len(habit_data)
            completed_records = len(habit_data[habit_data['is_completed'] == True])
            completion_rate = (completed_records / total_records * 100) if total_records > 0 else 0

            # Calculate streak
            streaks = self._calculate_streaks(habit_data)
            streak_length = streaks.get(habit_name, {}).get('best_streak', 0)

            # Calculate days active
            if not habit_data.empty:
                habit_data_copy = habit_data.copy()
                habit_data_copy['date'] = pd.to_datetime(habit_data_copy['date'])
                days_active = (habit_data_copy['date'].max() - habit_data_copy['date'].min()).days + 1
            else:
                days_active = 0

            # Get category if available
            category = habit_data.iloc[0].get('category', 'Unknown') if not habit_data.empty else 'Unknown'

            # Determine completion status
            completion_status = 'High' if completion_rate >= 80 else 'Medium' if completion_rate >= 50 else 'Low'

            habit_metrics.append({
                'habit_name': habit_name,
                'completion_rate': completion_rate,
                'streak_length': streak_length,
                'total_records': total_records,
                'days_active': days_active,
                'category': category,
                'completion_status': completion_status
            })

        return pd.DataFrame(habit_metrics)


class InteractiveHeatmapWidget(InteractiveChartWidget):
    """Interactive heatmap displaying habit completion patterns across days/weeks/months"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.heatmap_type = 'day_month'  # day_month, weekday_month, habit_day
        self.color_scale = 'RdYlGn'

    def setup_controls(self):
        """Setup heatmap specific controls"""
        # Heatmap type selector
        type_label = QLabel("Heatmap Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Day vs Month', 'Weekday vs Month', 'Habit vs Day'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        # Color scale selector
        color_label = QLabel("Color Scale:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(['RdYlGn', 'Viridis', 'Blues', 'Reds', 'Plasma'])
        self.color_combo.currentTextChanged.connect(self.on_color_changed)

        # Add to layout
        self.controls_layout.addWidget(type_label)
        self.controls_layout.addWidget(self.type_combo)
        self.controls_layout.addWidget(color_label)
        self.controls_layout.addWidget(self.color_combo)
        self.controls_layout.addStretch()

    def on_type_changed(self, text):
        """Handle heatmap type change"""
        type_map = {
            'Day vs Month': 'day_month',
            'Weekday vs Month': 'weekday_month',
            'Habit vs Day': 'habit_day'
        }
        self.heatmap_type = type_map.get(text, 'day_month')
        self.update_chart(self.current_data)

    def on_color_changed(self, text):
        """Handle color scale change"""
        self.color_scale = text
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update heatmap with habit completion patterns"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            if self.heatmap_type == 'day_month':
                self._create_day_month_heatmap(data)
            elif self.heatmap_type == 'weekday_month':
                self._create_weekday_month_heatmap(data)
            elif self.heatmap_type == 'habit_day':
                self._create_habit_day_heatmap(data)
        except Exception as e:
            print(f"Error updating heatmap: {e}")

    def _create_day_month_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing completion patterns by day of month vs month"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['day'] = data_copy['date'].dt.day
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        # Calculate completion rate for each day-month combination
        heatmap_data = data_copy.groupby(['day', 'month'])['is_completed'].mean().unstack(fill_value=0) * 100

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=self.color_scale,
            hoverongaps=False,
            hovertemplate='<b>Day %{y}, %{x}</b><br>Completion Rate: %{z:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Habit Completion Heatmap: Day vs Month",
            xaxis_title="Month",
            yaxis_title="Day of Month",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_weekday_month_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing completion patterns by weekday vs month"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['weekday'] = data_copy['date'].dt.day_name()
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        # Calculate completion rate for each weekday-month combination
        heatmap_data = data_copy.groupby(['weekday', 'month'])['is_completed'].mean().unstack(fill_value=0) * 100

        # Reorder weekdays
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(weekday_order, fill_value=0)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=self.color_scale,
            hoverongaps=False,
            hovertemplate='<b>%{y}, %{x}</b><br>Completion Rate: %{z:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Habit Completion Heatmap: Weekday vs Month",
            xaxis_title="Month",
            yaxis_title="Day of Week",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_habit_day_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing completion patterns by habit vs day"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['date_str'] = data_copy['date'].dt.strftime('%Y-%m-%d')

        # Calculate completion status for each habit-day combination
        heatmap_data = data_copy.pivot_table(
            index='habit_name',
            columns='date_str',
            values='is_completed',
            fill_value=0,
            aggfunc='mean'
        ) * 100

        # Limit to recent dates for readability
        if heatmap_data.shape[1] > 30:
            heatmap_data = heatmap_data.iloc[:, -30:]

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=self.color_scale,
            hoverongaps=False,
            hovertemplate='<b>%{y}</b><br>Date: %{x}<br>Completion: %{z:.0f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Habit Completion Heatmap: Habit vs Day (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Habit",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveTreemapWidget(InteractiveChartWidget):
    """Interactive treemap for hierarchical visualization of habit categories and subcategories"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hierarchy_type = 'category_habit'  # category_habit, status_category, frequency_habit
        self.value_metric = 'completion_rate'

    def setup_controls(self):
        """Setup treemap specific controls"""
        # Hierarchy type selector
        hierarchy_label = QLabel("Hierarchy:")
        self.hierarchy_combo = QComboBox()
        self.hierarchy_combo.addItems(['Category → Habit', 'Status → Category', 'Frequency → Habit'])
        self.hierarchy_combo.currentTextChanged.connect(self.on_hierarchy_changed)

        # Value metric selector
        value_label = QLabel("Size by:")
        self.value_combo = QComboBox()
        self.value_combo.addItems(['Completion Rate', 'Total Records', 'Streak Length'])
        self.value_combo.currentTextChanged.connect(self.on_value_changed)

        # Add to layout
        self.controls_layout.addWidget(hierarchy_label)
        self.controls_layout.addWidget(self.hierarchy_combo)
        self.controls_layout.addWidget(value_label)
        self.controls_layout.addWidget(self.value_combo)
        self.controls_layout.addStretch()

    def on_hierarchy_changed(self, text):
        """Handle hierarchy type change"""
        hierarchy_map = {
            'Category → Habit': 'category_habit',
            'Status → Category': 'status_category',
            'Frequency → Habit': 'frequency_habit'
        }
        self.hierarchy_type = hierarchy_map.get(text, 'category_habit')
        self.update_chart(self.current_data)

    def on_value_changed(self, text):
        """Handle value metric change"""
        value_map = {
            'Completion Rate': 'completion_rate',
            'Total Records': 'total_records',
            'Streak Length': 'streak_length'
        }
        self.value_metric = value_map.get(text, 'completion_rate')
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update treemap with hierarchical habit data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            if self.hierarchy_type == 'category_habit':
                self._create_category_habit_treemap(data)
            elif self.hierarchy_type == 'status_category':
                self._create_status_category_treemap(data)
            elif self.hierarchy_type == 'frequency_habit':
                self._create_frequency_habit_treemap(data)
        except Exception as e:
            print(f"Error updating treemap: {e}")

    def _create_category_habit_treemap(self, data: pd.DataFrame):
        """Create treemap with category → habit hierarchy"""
        # Prepare treemap data
        treemap_data = self._prepare_treemap_data(data, ['category', 'habit_name'])

        if treemap_data.empty:
            return

        fig = go.Figure(go.Treemap(
            labels=treemap_data['labels'],
            parents=treemap_data['parents'],
            values=treemap_data['values'],
            textinfo="label+value+percent parent",
            hovertemplate='<b>%{label}</b><br>Value: %{value:.1f}<br>Percent of Parent: %{percentParent}<extra></extra>'
        ))

        fig.update_layout(
            title=f"Habit Treemap: Category → Habit (by {self.value_metric.replace('_', ' ').title()})",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _prepare_treemap_data(self, data: pd.DataFrame, hierarchy_cols: List[str]) -> pd.DataFrame:
        """Prepare data for treemap visualization"""
        labels = []
        parents = []
        values = []

        # Calculate metrics for each habit
        habit_stats = data.groupby('habit_name').agg({
            'is_completed': ['count', 'sum']
        })
        habit_stats.columns = ['total_records', 'completed_records']
        habit_stats['completion_rate'] = (habit_stats['completed_records'] / habit_stats['total_records'] * 100).round(1)

        # Add streaks
        streaks = self._calculate_streaks(data)
        habit_stats['streak_length'] = [streaks.get(name, {}).get('best_streak', 0) for name in habit_stats.index]

        # Create hierarchy
        if len(hierarchy_cols) >= 2:
            # Group by first level (e.g., category)
            first_level_groups = data.groupby(hierarchy_cols[0])

            for group_name, group_data in first_level_groups:
                # Add parent node
                labels.append(group_name)
                parents.append("")

                # Calculate parent value
                if self.value_metric == 'completion_rate':
                    parent_value = (len(group_data[group_data['is_completed'] == True]) / len(group_data) * 100) if len(group_data) > 0 else 0
                elif self.value_metric == 'total_records':
                    parent_value = len(group_data)
                else:  # streak_length
                    parent_value = sum([streaks.get(name, {}).get('best_streak', 0) for name in group_data['habit_name'].unique()])

                values.append(parent_value)

                # Add child nodes
                for habit_name in group_data[hierarchy_cols[1]].unique():
                    labels.append(habit_name)
                    parents.append(group_name)

                    if habit_name in habit_stats.index:
                        child_value = habit_stats.loc[habit_name, self.value_metric]
                    else:
                        child_value = 0

                    values.append(child_value)

        return pd.DataFrame({
            'labels': labels,
            'parents': parents,
            'values': values
        })

    def _create_status_category_treemap(self, data: pd.DataFrame):
        """Create treemap with completion status → category hierarchy"""
        # Add completion status to data
        data_copy = data.copy()
        habit_completion_rates = data_copy.groupby('habit_name')['is_completed'].mean() * 100

        def get_status(habit_name):
            rate = habit_completion_rates.get(habit_name, 0)
            return 'High (80%+)' if rate >= 80 else 'Medium (50-79%)' if rate >= 50 else 'Low (<50%)'

        data_copy['completion_status'] = data_copy['habit_name'].apply(get_status)

        # Prepare treemap data
        treemap_data = self._prepare_treemap_data(data_copy, ['completion_status', 'category'])

        if treemap_data.empty:
            return

        fig = go.Figure(go.Treemap(
            labels=treemap_data['labels'],
            parents=treemap_data['parents'],
            values=treemap_data['values'],
            textinfo="label+value+percent parent",
            hovertemplate='<b>%{label}</b><br>Value: %{value:.1f}<br>Percent of Parent: %{percentParent}<extra></extra>'
        ))

        fig.update_layout(
            title=f"Habit Treemap: Status → Category (by {self.value_metric.replace('_', ' ').title()})",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_frequency_habit_treemap(self, data: pd.DataFrame):
        """Create treemap with frequency → habit hierarchy"""
        # Use frequency if available, otherwise default to 'Daily'
        if 'frequency' not in data.columns:
            data_copy = data.copy()
            data_copy['frequency'] = 'Daily'
        else:
            data_copy = data.copy()

        # Prepare treemap data
        treemap_data = self._prepare_treemap_data(data_copy, ['frequency', 'habit_name'])

        if treemap_data.empty:
            return

        fig = go.Figure(go.Treemap(
            labels=treemap_data['labels'],
            parents=treemap_data['parents'],
            values=treemap_data['values'],
            textinfo="label+value+percent parent",
            hovertemplate='<b>%{label}</b><br>Value: %{value:.1f}<br>Percent of Parent: %{percentParent}<extra></extra>'
        ))

        fig.update_layout(
            title=f"Habit Treemap: Frequency → Habit (by {self.value_metric.replace('_', ' ').title()})",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)
