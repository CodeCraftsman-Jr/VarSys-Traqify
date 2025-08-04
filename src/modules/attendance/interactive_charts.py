"""
Interactive Attendance Charts Module
Provides advanced interactive chart widgets using Plotly for attendance analytics
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
print(f"Attendance Charts: PLOTLY_AVAILABLE = {PLOTLY_AVAILABLE}")
print(f"Attendance Charts: WEBENGINE_AVAILABLE = {WEBENGINE_AVAILABLE}")

# Import matplotlib as fallback
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.qt_compat import QtWidgets
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
    print("Attendance Charts: MATPLOTLIB_AVAILABLE = True")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Attendance Charts: MATPLOTLIB_AVAILABLE = False")


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

        # APPLIED TO DO ANALYTICS APPROACH: Set reasonable minimum size but allow natural expansion
        self.setMinimumSize(400, 350)  # Reasonable size for chart visibility
        # APPLIED TO DO ANALYTICS APPROACH: Allow full expansion like To Do Analytics
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Controls section
        self.controls_frame = QFrame()
        self.controls_layout = QHBoxLayout(self.controls_frame)
        self.setup_controls()
        layout.addWidget(self.controls_frame)

        # Chart section
        if PLOTLY_AVAILABLE and WEBENGINE_AVAILABLE:
            print(f"Setting up WebEngine view for {self.__class__.__name__}")
            self.web_view = QWebEngineView()

            # APPLIED TO DO ANALYTICS APPROACH: Set reasonable size for web view with natural expansion
            self.web_view.setMinimumSize(380, 300)  # Reasonable size for chart visibility
            # APPLIED TO DO ANALYTICS APPROACH: Allow full expansion like To Do Analytics
            self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
        """Create initial empty chart - EXPANDED: Better sizing for visibility"""
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
                title="Attendance Analytics Chart",
                # APPLIED TO DO ANALYTICS APPROACH: Reasonable height for chart visibility
                height=400,  # Standard height for good chart visibility
                showlegend=False,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False),
                # APPLIED TO DO ANALYTICS APPROACH: Better margins for chart content
                margin=dict(l=60, r=40, t=80, b=60)
            )

            # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
            fig = self.apply_theme_to_plotly_fig(fig)
            html_str = self.generate_theme_aware_html(fig)
            self.web_view.setHtml(html_str)

    def update_chart(self, data: pd.DataFrame):
        """Update chart with new data - to be implemented by subclasses"""
        self.current_data = data.copy() if not data.empty else pd.DataFrame()


class InteractivePieChartWidget(InteractiveChartWidget):
    """Interactive pie chart with drill-down functionality for attendance patterns"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_type = 'attendance_status'  # attendance_status, period_wise, semester_wise
        self.show_percentages = True
        self.drill_down_level = 0
        self.current_semester = None
        
    def setup_controls(self):
        """Setup pie chart specific controls"""
        # Chart type selector
        type_label = QLabel("View by:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Attendance Status', 'Period-wise', 'Semester-wise'])
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
            'Attendance Status': 'attendance_status',
            'Period-wise': 'period_wise',
            'Semester-wise': 'semester_wise'
        }
        self.chart_type = type_map.get(text, 'attendance_status')
        self.drill_down_level = 0
        self.current_semester = None
        self.drill_back_btn.setEnabled(False)
        self.update_chart(self.current_data)
    
    def on_percentages_toggled(self, checked):
        """Handle show percentages toggle"""
        self.show_percentages = checked
        self.update_chart(self.current_data)
    
    def drill_back(self):
        """Handle drill back action"""
        self.drill_down_level = 0
        self.current_semester = None
        self.drill_back_btn.setEnabled(False)
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update pie chart with attendance data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return
        
        try:
            if self.chart_type == 'attendance_status':
                self._create_attendance_status_chart(data)
            elif self.chart_type == 'period_wise':
                self._create_period_wise_chart(data)
            elif self.chart_type == 'semester_wise':
                self._create_semester_wise_chart(data)
        except Exception as e:
            print(f"Error updating pie chart: {e}")
    
    def _create_attendance_status_chart(self, data: pd.DataFrame):
        """Create pie chart by attendance status"""
        # Filter out holidays and unofficial leaves for attendance calculation
        working_data = data[(data['is_holiday'] == False) & (data['is_unofficial_leave'] == False)]
        
        if working_data.empty:
            return
        
        # Calculate attendance categories
        full_attendance = len(working_data[working_data['percentage'] == 100.0])
        partial_attendance = len(working_data[(working_data['percentage'] > 0) & (working_data['percentage'] < 100.0)])
        absent = len(working_data[working_data['percentage'] == 0.0])
        
        # Create pie chart
        labels = ['Full Attendance', 'Partial Attendance', 'Absent']
        values = [full_attendance, partial_attendance, absent]
        colors = ['#2E8B57', '#FFD700', '#DC143C']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            textinfo='label+percent' if self.show_percentages else 'label',
            marker_colors=colors,
            hovertemplate='<b>%{label}</b><br>' +
                         'Days: %{value}<br>' +
                         'Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Attendance Status Distribution",
            height=500,
            showlegend=True
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)
    
    def _create_period_wise_chart(self, data: pd.DataFrame):
        """Create pie chart by period-wise attendance"""
        # Calculate period-wise attendance
        period_stats = {}
        
        for period in range(1, 9):
            period_col = f'period_{period}'
            if period_col in data.columns:
                present_count = len(data[data[period_col] == 'Present'])
                period_stats[f'Period {period}'] = present_count
        
        if not period_stats:
            return
        
        fig = go.Figure(data=[go.Pie(
            labels=list(period_stats.keys()),
            values=list(period_stats.values()),
            textinfo='label+percent' if self.show_percentages else 'label',
            hovertemplate='<b>%{label}</b><br>' +
                         'Present Days: %{value}<br>' +
                         'Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Period-wise Attendance Distribution",
            height=500,
            showlegend=True
        )
        
        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_semester_wise_chart(self, data: pd.DataFrame):
        """Create pie chart by semester-wise attendance"""
        if 'semester' not in data.columns or 'academic_year' not in data.columns:
            return

        # Group by semester and academic year
        semester_stats = data.groupby(['semester', 'academic_year']).agg({
            'percentage': 'mean',
            'present_periods': 'sum',
            'total_periods': 'sum'
        }).round(2)

        # Create labels and values
        labels = []
        values = []

        for (semester, year), stats in semester_stats.iterrows():
            label = f"Sem {semester} ({year})"
            labels.append(label)
            values.append(stats['percentage'])

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            textinfo='label+percent' if self.show_percentages else 'label',
            hovertemplate='<b>%{label}</b><br>' +
                         'Avg Attendance: %{value:.1f}%<br>' +
                         'Percentage: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title="Semester-wise Attendance Distribution",
            height=500,
            showlegend=True
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveTimeSeriesWidget(InteractiveChartWidget):
    """Interactive time series chart with zoom and pan functionality for attendance trends"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aggregation = 'daily'
        self.show_trend = True
        self.show_threshold = True
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

        # Show trend checkbox
        self.trend_cb = QCheckBox("Show Trend")
        self.trend_cb.setChecked(True)
        self.trend_cb.toggled.connect(self.on_trend_toggled)

        # Show threshold checkbox
        self.threshold_cb = QCheckBox("Show 75% Threshold")
        self.threshold_cb.setChecked(True)
        self.threshold_cb.toggled.connect(self.on_threshold_toggled)

        # Add to layout
        self.controls_layout.addWidget(agg_label)
        self.controls_layout.addWidget(self.agg_combo)
        self.controls_layout.addWidget(range_label)
        self.controls_layout.addWidget(self.range_spin)
        self.controls_layout.addWidget(self.trend_cb)
        self.controls_layout.addWidget(self.threshold_cb)
        self.controls_layout.addStretch()

    def on_aggregation_changed(self, text):
        """Handle aggregation change"""
        self.aggregation = text.lower()
        self.update_chart(self.current_data)

    def on_range_changed(self, value):
        """Handle date range change"""
        self.date_range = value
        self.update_chart(self.current_data)

    def on_trend_toggled(self, checked):
        """Handle show trend toggle"""
        self.show_trend = checked
        self.update_chart(self.current_data)

    def on_threshold_toggled(self, checked):
        """Handle show threshold toggle"""
        self.show_threshold = checked
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update time series chart with attendance trends"""
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
                (data_copy['date'] <= end_date) &
                (data_copy['is_holiday'] == False) &
                (data_copy['is_unofficial_leave'] == False)
            ]

            if filtered_data.empty:
                return

            self._create_time_series_chart(filtered_data)
        except Exception as e:
            print(f"Error updating time series chart: {e}")

    def _create_time_series_chart(self, data: pd.DataFrame):
        """Create time series chart with attendance trends"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Attendance Percentage', 'Period-wise Attendance'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )

        # Sort data by date
        data_sorted = data.sort_values('date')

        # Add attendance percentage line
        fig.add_trace(
            go.Scatter(
                x=data_sorted['date'],
                y=data_sorted['percentage'],
                mode='lines+markers',
                name='Attendance %',
                line=dict(color='#2E8B57', width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Attendance: %{y}%<br>Present Periods: %{customdata[0]}<br>Total Periods: %{customdata[1]}<extra></extra>',
                customdata=list(zip(data_sorted['present_periods'], data_sorted['total_periods']))
            ),
            row=1, col=1
        )

        # Add 75% threshold line if enabled
        if self.show_threshold:
            fig.add_hline(
                y=75, line_dash="dash", line_color="red",
                annotation_text="75% Threshold",
                row=1, col=1
            )

        # Add trend line if enabled
        if self.show_trend and len(data_sorted) > 2:
            x_numeric = np.arange(len(data_sorted))
            z = np.polyfit(x_numeric, data_sorted['percentage'], 1)
            trend_line = np.poly1d(z)(x_numeric)

            fig.add_trace(
                go.Scatter(
                    x=data_sorted['date'],
                    y=trend_line,
                    mode='lines',
                    name='Trend',
                    line=dict(color='orange', width=1, dash='dash'),
                    hovertemplate='Trend: %{y:.1f}%<extra></extra>'
                ),
                row=1, col=1
            )

        # Add period-wise attendance bar chart
        period_attendance = []
        for period in range(1, 9):
            period_col = f'period_{period}'
            if period_col in data_sorted.columns:
                present_count = len(data_sorted[data_sorted[period_col] == 'Present'])
                period_attendance.append(present_count)
            else:
                period_attendance.append(0)

        fig.add_trace(
            go.Bar(
                x=[f'P{i}' for i in range(1, 9)],
                y=period_attendance,
                name='Period Attendance',
                marker_color='#4CAF50',
                hovertemplate='<b>Period %{x}</b><br>Present Days: %{y}<extra></extra>',
                showlegend=False
            ),
            row=2, col=1
        )

        fig.update_layout(
            title="Attendance Trends Over Time",
            height=600,
            showlegend=True
        )

        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Attendance (%)", row=1, col=1)
        fig.update_xaxes(title_text="Periods", row=2, col=1)
        fig.update_yaxes(title_text="Present Days", row=2, col=1)

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveBarChartWidget(InteractiveChartWidget):
    """Interactive bar chart with filtering options for attendance performance comparisons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_type = 'monthly_attendance'  # monthly_attendance, period_comparison, semester_comparison
        self.sort_order = 'desc'
        self.show_values = True
        self.top_n = 12

    def setup_controls(self):
        """Setup bar chart specific controls"""
        # Chart type selector
        type_label = QLabel("Chart Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Monthly Attendance', 'Period Comparison', 'Semester Comparison'])
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
        self.top_spin.setValue(12)
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
            'Monthly Attendance': 'monthly_attendance',
            'Period Comparison': 'period_comparison',
            'Semester Comparison': 'semester_comparison'
        }
        self.chart_type = type_map.get(text, 'monthly_attendance')
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
        """Update bar chart with attendance performance data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            if self.chart_type == 'monthly_attendance':
                self._create_monthly_attendance_chart(data)
            elif self.chart_type == 'period_comparison':
                self._create_period_comparison_chart(data)
            elif self.chart_type == 'semester_comparison':
                self._create_semester_comparison_chart(data)
        except Exception as e:
            print(f"Error updating bar chart: {e}")

    def _create_monthly_attendance_chart(self, data: pd.DataFrame):
        """Create bar chart showing monthly attendance rates"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month_year'] = data_copy['date'].dt.strftime('%Y-%m')

        # Filter out holidays and unofficial leaves
        working_data = data_copy[(data_copy['is_holiday'] == False) & (data_copy['is_unofficial_leave'] == False)]

        if working_data.empty:
            return

        # Calculate monthly attendance
        monthly_stats = working_data.groupby('month_year').agg({
            'percentage': 'mean',
            'present_periods': 'sum',
            'total_periods': 'sum'
        }).round(1)

        # Sort and limit
        if self.sort_order == 'desc':
            monthly_stats = monthly_stats.nlargest(self.top_n, 'percentage')
        else:
            monthly_stats = monthly_stats.nsmallest(self.top_n, 'percentage')

        fig = go.Figure(data=[go.Bar(
            x=monthly_stats.index,
            y=monthly_stats['percentage'],
            text=monthly_stats['percentage'].astype(str) + '%' if self.show_values else None,
            textposition='auto',
            marker_color='#2E8B57',
            hovertemplate='<b>%{x}</b><br>' +
                         'Attendance: %{y}%<br>' +
                         'Present Periods: %{customdata[0]}<br>' +
                         'Total Periods: %{customdata[1]}<extra></extra>',
            customdata=list(zip(
                monthly_stats['present_periods'],
                monthly_stats['total_periods']
            ))
        )])

        fig.update_layout(
            title=f"Monthly Attendance Rates (Top {self.top_n})",
            xaxis_title="Month",
            yaxis_title="Attendance (%)",
            height=500,
            showlegend=False
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_period_comparison_chart(self, data: pd.DataFrame):
        """Create bar chart comparing period-wise attendance"""
        period_stats = {}

        for period in range(1, 9):
            period_col = f'period_{period}'
            if period_col in data.columns:
                present_count = len(data[data[period_col] == 'Present'])
                total_count = len(data[data[period_col].notna()])
                attendance_rate = (present_count / total_count * 100) if total_count > 0 else 0
                period_stats[f'Period {period}'] = {
                    'attendance_rate': attendance_rate,
                    'present_count': present_count,
                    'total_count': total_count
                }

        if not period_stats:
            return

        periods = list(period_stats.keys())
        rates = [period_stats[p]['attendance_rate'] for p in periods]
        present_counts = [period_stats[p]['present_count'] for p in periods]
        total_counts = [period_stats[p]['total_count'] for p in periods]

        fig = go.Figure(data=[go.Bar(
            x=periods,
            y=rates,
            text=[f'{r:.1f}%' for r in rates] if self.show_values else None,
            textposition='auto',
            marker_color='#4CAF50',
            hovertemplate='<b>%{x}</b><br>' +
                         'Attendance Rate: %{y:.1f}%<br>' +
                         'Present Days: %{customdata[0]}<br>' +
                         'Total Days: %{customdata[1]}<extra></extra>',
            customdata=list(zip(present_counts, total_counts))
        )])

        fig.update_layout(
            title="Period-wise Attendance Comparison",
            xaxis_title="Periods",
            yaxis_title="Attendance Rate (%)",
            height=500,
            showlegend=False
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_semester_comparison_chart(self, data: pd.DataFrame):
        """Create bar chart comparing semester-wise attendance"""
        if 'semester' not in data.columns or 'academic_year' not in data.columns:
            return

        # Filter out holidays and unofficial leaves
        working_data = data[(data['is_holiday'] == False) & (data['is_unofficial_leave'] == False)]

        if working_data.empty:
            return

        # Group by semester and academic year
        semester_stats = working_data.groupby(['semester', 'academic_year']).agg({
            'percentage': 'mean',
            'present_periods': 'sum',
            'total_periods': 'sum'
        }).round(1)

        # Create labels and values
        labels = []
        values = []
        present_periods = []
        total_periods = []

        for (semester, year), stats in semester_stats.iterrows():
            label = f"Sem {semester} ({year})"
            labels.append(label)
            values.append(stats['percentage'])
            present_periods.append(stats['present_periods'])
            total_periods.append(stats['total_periods'])

        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            text=[f'{v:.1f}%' for v in values] if self.show_values else None,
            textposition='auto',
            marker_color='#9C27B0',
            hovertemplate='<b>%{x}</b><br>' +
                         'Avg Attendance: %{y:.1f}%<br>' +
                         'Present Periods: %{customdata[0]}<br>' +
                         'Total Periods: %{customdata[1]}<extra></extra>',
            customdata=list(zip(present_periods, total_periods))
        )])

        fig.update_layout(
            title="Semester-wise Attendance Comparison",
            xaxis_title="Semesters",
            yaxis_title="Average Attendance (%)",
            height=500,
            showlegend=False
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveHeatmapWidget(InteractiveChartWidget):
    """Interactive heatmap displaying attendance patterns across days/weeks/months"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.heatmap_type = 'day_month'  # day_month, weekday_month, period_day
        self.color_scale = 'RdYlGn'

    def setup_controls(self):
        """Setup heatmap specific controls"""
        # Heatmap type selector
        type_label = QLabel("Heatmap Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Day vs Month', 'Weekday vs Month', 'Period vs Day'])
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
            'Period vs Day': 'period_day'
        }
        self.heatmap_type = type_map.get(text, 'day_month')
        self.update_chart(self.current_data)

    def on_color_changed(self, text):
        """Handle color scale change"""
        self.color_scale = text
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update heatmap with attendance patterns"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            if self.heatmap_type == 'day_month':
                self._create_day_month_heatmap(data)
            elif self.heatmap_type == 'weekday_month':
                self._create_weekday_month_heatmap(data)
            elif self.heatmap_type == 'period_day':
                self._create_period_day_heatmap(data)
        except Exception as e:
            print(f"Error updating heatmap: {e}")

    def _create_day_month_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing attendance patterns by day of month vs month"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['day'] = data_copy['date'].dt.day
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        # Filter out holidays and unofficial leaves
        working_data = data_copy[(data_copy['is_holiday'] == False) & (data_copy['is_unofficial_leave'] == False)]

        if working_data.empty:
            return

        # Calculate attendance percentage for each day-month combination
        heatmap_data = working_data.groupby(['day', 'month'])['percentage'].mean().unstack(fill_value=0)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=self.color_scale,
            hoverongaps=False,
            hovertemplate='<b>Day %{y}, %{x}</b><br>Attendance: %{z:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Attendance Heatmap: Day vs Month",
            xaxis_title="Month",
            yaxis_title="Day of Month",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_weekday_month_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing attendance patterns by weekday vs month"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['weekday'] = data_copy['date'].dt.day_name()
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        # Filter out holidays and unofficial leaves
        working_data = data_copy[(data_copy['is_holiday'] == False) & (data_copy['is_unofficial_leave'] == False)]

        if working_data.empty:
            return

        # Calculate attendance percentage for each weekday-month combination
        heatmap_data = working_data.groupby(['weekday', 'month'])['percentage'].mean().unstack(fill_value=0)

        # Reorder weekdays
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(weekday_order, fill_value=0)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale=self.color_scale,
            hoverongaps=False,
            hovertemplate='<b>%{y}, %{x}</b><br>Attendance: %{z:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Attendance Heatmap: Weekday vs Month",
            xaxis_title="Month",
            yaxis_title="Day of Week",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_period_day_heatmap(self, data: pd.DataFrame):
        """Create heatmap showing attendance patterns by period vs day"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['date_str'] = data_copy['date'].dt.strftime('%Y-%m-%d')

        # Filter out holidays and unofficial leaves
        working_data = data_copy[(data_copy['is_holiday'] == False) & (data_copy['is_unofficial_leave'] == False)]

        if working_data.empty:
            return

        # Create period attendance matrix
        periods = [f'period_{i}' for i in range(1, 9)]
        available_periods = [p for p in periods if p in working_data.columns]

        if not available_periods:
            return

        # Prepare data for heatmap
        heatmap_matrix = []
        dates = sorted(working_data['date_str'].unique())

        # Limit to recent dates for readability
        if len(dates) > 30:
            dates = dates[-30:]

        for period in available_periods:
            period_data = []
            for date_str in dates:
                day_data = working_data[working_data['date_str'] == date_str]
                if not day_data.empty and period in day_data.columns:
                    present_count = len(day_data[day_data[period] == 'Present'])
                    total_count = len(day_data[day_data[period].notna()])
                    attendance_rate = (present_count / total_count * 100) if total_count > 0 else 0
                else:
                    attendance_rate = 0
                period_data.append(attendance_rate)
            heatmap_matrix.append(period_data)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_matrix,
            x=dates,
            y=[p.replace('period_', 'P') for p in available_periods],
            colorscale=self.color_scale,
            hoverongaps=False,
            hovertemplate='<b>%{y}, %{x}</b><br>Attendance: %{z:.0f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Attendance Heatmap: Period vs Day (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Period",
            height=500
        )

        # CRITICAL FIX: Apply theme colors and generate theme-aware HTML
        fig = self.apply_theme_to_plotly_fig(fig)
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveScatterPlotWidget(InteractiveChartWidget):
    """Interactive scatter plot showing correlations between attendance metrics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_metric = 'present_periods'
        self.y_metric = 'percentage'
        self.color_by = 'month'
        self.size_by = 'total_periods'

    def setup_controls(self):
        """Setup scatter plot specific controls"""
        # X-axis metric selector
        x_label = QLabel("X-Axis:")
        self.x_combo = QComboBox()
        self.x_combo.addItems(['Present Periods', 'Total Periods', 'Percentage', 'Day of Week'])
        self.x_combo.currentTextChanged.connect(self.on_x_changed)

        # Y-axis metric selector
        y_label = QLabel("Y-Axis:")
        self.y_combo = QComboBox()
        self.y_combo.addItems(['Percentage', 'Present Periods', 'Total Periods', 'Day of Month'])
        self.y_combo.currentTextChanged.connect(self.on_y_changed)

        # Color by selector
        color_label = QLabel("Color by:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(['Month', 'Weekday', 'Semester', 'Holiday Status'])
        self.color_combo.currentTextChanged.connect(self.on_color_changed)

        # Size by selector
        size_label = QLabel("Size by:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(['Total Periods', 'Present Periods', 'Percentage'])
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
            'Present Periods': 'present_periods',
            'Total Periods': 'total_periods',
            'Percentage': 'percentage',
            'Day of Week': 'day_of_week'
        }
        self.x_metric = metric_map.get(text, 'present_periods')
        self.update_chart(self.current_data)

    def on_y_changed(self, text):
        """Handle Y-axis metric change"""
        metric_map = {
            'Percentage': 'percentage',
            'Present Periods': 'present_periods',
            'Total Periods': 'total_periods',
            'Day of Month': 'day_of_month'
        }
        self.y_metric = metric_map.get(text, 'percentage')
        self.update_chart(self.current_data)

    def on_color_changed(self, text):
        """Handle color by change"""
        color_map = {
            'Month': 'month',
            'Weekday': 'weekday',
            'Semester': 'semester',
            'Holiday Status': 'holiday_status'
        }
        self.color_by = color_map.get(text, 'month')
        self.update_chart(self.current_data)

    def on_size_changed(self, text):
        """Handle size by change"""
        size_map = {
            'Total Periods': 'total_periods',
            'Present Periods': 'present_periods',
            'Percentage': 'percentage'
        }
        self.size_by = size_map.get(text, 'total_periods')
        self.update_chart(self.current_data)

    def update_chart(self, data: pd.DataFrame):
        """Update scatter plot with attendance correlation data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or not WEBENGINE_AVAILABLE or data.empty:
            return

        try:
            self._create_scatter_plot(data)
        except Exception as e:
            print(f"Error updating scatter plot: {e}")

    def _create_scatter_plot(self, data: pd.DataFrame):
        """Create scatter plot showing attendance correlations"""
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
            hover_data=['date', 'percentage', 'present_periods', 'total_periods'],
            title=f"Attendance Correlation: {self.x_metric.replace('_', ' ').title()} vs {self.y_metric.replace('_', ' ').title()}"
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
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])

        # Add derived columns
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')
        data_copy['weekday'] = data_copy['date'].dt.day_name()
        data_copy['day_of_week'] = data_copy['date'].dt.dayofweek
        data_copy['day_of_month'] = data_copy['date'].dt.day
        data_copy['holiday_status'] = data_copy['is_holiday'].map({True: 'Holiday', False: 'Working Day'})

        # Filter out holidays and unofficial leaves for main analysis
        working_data = data_copy[(data_copy['is_holiday'] == False) & (data_copy['is_unofficial_leave'] == False)]

        return working_data if not working_data.empty else data_copy
