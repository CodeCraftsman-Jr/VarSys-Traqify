"""
Attendance Analytics Dashboard
Main dashboard widget for comprehensive attendance tracking analytics
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGroupBox,
    QScrollArea, QTabWidget, QGridLayout, QSplitter, QPushButton,
    QDateEdit, QComboBox, QSpinBox, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QPalette

from .models import AttendanceDataModel
from .analytics_utils import calculate_attendance_statistics, get_attendance_insights
from .interactive_charts import (
    InteractivePieChartWidget,
    InteractiveTimeSeriesWidget,
    InteractiveBarChartWidget,
    InteractiveScatterPlotWidget,
    InteractiveHeatmapWidget
)
from ..expenses.visualization import SummaryCardWidget


class AttendanceAnalyticsDashboard(QWidget):
    """Main attendance analytics dashboard with comprehensive visualizations"""
    
    def __init__(self, attendance_model: AttendanceDataModel, parent=None):
        super().__init__(parent)
        
        self.attendance_model = attendance_model
        self.current_data = pd.DataFrame()
        self.analytics_stats = {}
        self.current_theme = 'light'  # CRITICAL FIX: Initialize theme to prevent black bars
        
        self.setup_ui()
        self.setup_connections()
        self.refresh_data()
        
        # Setup auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Create header
        self.create_header(layout)
        
        # Create main content
        self.create_main_content(layout)
    
    def create_header(self, layout):
        """Create dashboard header with title and controls"""
        header_frame = QFrame()
        header_frame.setObjectName("dashboardHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Title
        title_label = QLabel("📚 Attendance Analytics Dashboard")
        title_label.setObjectName("dashboardTitle")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        # Date range selector
        date_label = QLabel("Date Range:")
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems(['Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'Current Semester', 'All Time'])
        self.date_range_combo.setCurrentText('All Time')
        self.date_range_combo.currentTextChanged.connect(self.on_date_range_changed)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(date_label)
        header_layout.addWidget(self.date_range_combo)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(header_frame)
    
    def create_main_content(self, layout):
        """Create main content area with tabs"""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("analyticsTabWidget")
        
        # Create tabs
        self.create_overview_tab()
        self.create_charts_tab()
        
        layout.addWidget(self.tab_widget)
    
    def create_overview_tab(self):
        """Create overview tab with KPIs and summary - APPLIED TO DO ANALYTICS LAYOUT APPROACH"""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setContentsMargins(10, 10, 10, 10)
        overview_layout.setSpacing(15)

        # CRITICAL FIX: Create scroll area like To Do Analytics to prevent overlapping
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # KPI Cards
        self.create_kpi_section(content_layout)

        # Quick Charts
        self.create_quick_charts_section(content_layout)

        # Insights Section
        self.create_insights_section(content_layout)

        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        overview_layout.addWidget(scroll_area)

        self.tab_widget.addTab(overview_widget, "📊 Overview")
    
    def create_charts_tab(self):
        """Create charts tab with interactive visualizations"""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create chart sub-tabs
        chart_tabs = QTabWidget()
        
        # Pie Chart Tab
        self.pie_chart = InteractivePieChartWidget()
        chart_tabs.addTab(self.pie_chart, "🥧 Pie Charts")
        
        # Time Series Tab
        self.time_series_chart = InteractiveTimeSeriesWidget()
        chart_tabs.addTab(self.time_series_chart, "📈 Time Series")
        
        # Bar Chart Tab
        self.bar_chart = InteractiveBarChartWidget()
        chart_tabs.addTab(self.bar_chart, "📊 Bar Charts")
        
        # Scatter Plot Tab
        self.scatter_chart = InteractiveScatterPlotWidget()
        chart_tabs.addTab(self.scatter_chart, "🔍 Scatter Plot")
        
        charts_layout.addWidget(chart_tabs)
        self.tab_widget.addTab(charts_widget, "📈 Interactive Charts")
    

    
    def create_kpi_section(self, layout):
        """Create KPI cards section - APPLIED TO DO ANALYTICS APPROACH"""
        # Section title
        kpi_title = QLabel("Key Performance Indicators")
        kpi_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        kpi_title.setFont(font)
        layout.addWidget(kpi_title)

        # KPI cards grid - APPLIED TO DO ANALYTICS LAYOUT: Remove height restrictions
        kpi_frame = QFrame()
        kpi_frame.setObjectName("kpiFrame")
        # CRITICAL FIX: Remove height restrictions to allow cards to expand properly like To Do Analytics
        kpi_frame.setMinimumHeight(200)  # Increased minimum height for more spacious layout
        # Remove maximum height constraint to allow natural expansion like To Do Analytics
        kpi_layout = QGridLayout(kpi_frame)
        kpi_layout.setSpacing(25)  # Increased spacing between cards for better visual separation
        kpi_layout.setContentsMargins(20, 20, 20, 20)  # More generous margins around the grid
        
        # Create KPI cards
        self.kpi_cards = {}
        
        # Overall Attendance Rate Card
        self.kpi_cards['attendance_rate'] = SummaryCardWidget(
            "Attendance Rate", "0%", "Overall", "📚"
        )
        
        # Working Days Card
        self.kpi_cards['working_days'] = SummaryCardWidget(
            "Working Days", "0", "Total Days", "📅"
        )
        
        # Present Days Card
        self.kpi_cards['present_days'] = SummaryCardWidget(
            "Present Days", "0", "Days Attended", "✅"
        )
        
        # This Month Card
        self.kpi_cards['month_progress'] = SummaryCardWidget(
            "This Month", "0%", "Attendance Rate", "📊"
        )
        
        # This Week Card
        self.kpi_cards['week_progress'] = SummaryCardWidget(
            "This Week", "0%", "Attendance Rate", "📈"
        )
        
        # Period Attendance Card
        self.kpi_cards['period_attendance'] = SummaryCardWidget(
            "Period Attendance", "0%", "Overall Periods", "⏰"
        )
        
        # Add cards to grid
        kpi_layout.addWidget(self.kpi_cards['attendance_rate'], 0, 0)
        kpi_layout.addWidget(self.kpi_cards['working_days'], 0, 1)
        kpi_layout.addWidget(self.kpi_cards['present_days'], 0, 2)
        kpi_layout.addWidget(self.kpi_cards['month_progress'], 1, 0)
        kpi_layout.addWidget(self.kpi_cards['week_progress'], 1, 1)
        kpi_layout.addWidget(self.kpi_cards['period_attendance'], 1, 2)
        
        layout.addWidget(kpi_frame)
    
    def create_quick_charts_section(self, layout):
        """Create quick charts section - APPLIED TO DO ANALYTICS APPROACH"""
        # Section title
        charts_title = QLabel("Quick Analytics")
        charts_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        charts_title.setFont(font)
        layout.addWidget(charts_title)

        # Charts container - APPLIED TO DO ANALYTICS FIX: Remove excessive minimum height constraint
        charts_frame = QFrame()
        charts_frame.setObjectName("chartsFrame")
        # APPLIED TO DO ANALYTICS FIX: Remove minimum height constraint to eliminate empty white space
        # Let the charts determine their own natural size
        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setSpacing(20)  # Increased spacing for better visual separation
        charts_layout.setContentsMargins(15, 15, 15, 15)  # Add margins for better layout

        # Create responsive charts - APPLIED TO DO ANALYTICS VERTICAL SPACE FIX: Use Minimum height policy
        self.mini_pie_chart = InteractivePieChartWidget()
        # APPLIED TO DO ANALYTICS VERTICAL SPACE FIX: Expand horizontally but only take minimum vertical space needed
        self.mini_pie_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.mini_bar_chart = InteractiveBarChartWidget()
        # APPLIED TO DO ANALYTICS VERTICAL SPACE FIX: Expand horizontally but only take minimum vertical space needed
        self.mini_bar_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        charts_layout.addWidget(self.mini_pie_chart)
        charts_layout.addWidget(self.mini_bar_chart)

        layout.addWidget(charts_frame)
    
    def create_insights_section(self, layout):
        """Create insights and recommendations section - APPLIED TO DO ANALYTICS APPROACH"""
        # Section title
        insights_title = QLabel("Insights & Recommendations")
        insights_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        insights_title.setFont(font)
        layout.addWidget(insights_title)

        # Insights container - APPLIED TO DO ANALYTICS APPROACH
        self.insights_frame = QFrame()
        self.insights_frame.setObjectName("insightsFrame")
        self.insights_layout = QVBoxLayout(self.insights_frame)
        self.insights_layout.setContentsMargins(15, 15, 15, 15)
        self.insights_layout.setSpacing(10)

        layout.addWidget(self.insights_frame)
    
    def setup_connections(self):
        """Setup signal connections"""
        pass
    
    def on_date_range_changed(self, range_text):
        """Handle date range change"""
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh all data and update visualizations"""
        try:
            # Get date range
            range_days = self.get_date_range_days()

            # Get attendance data
            all_records = self.attendance_model.get_all_records()

            if not all_records.empty:
                # Filter by date range
                all_records['date'] = pd.to_datetime(all_records['date'])

                # Apply date range filter based on selection
                if self.date_range_combo.currentText() == 'All Time':
                    self.current_data = all_records
                else:
                    end_date = pd.Timestamp.now()
                    start_date = end_date - pd.Timedelta(days=range_days)

                    filtered_data = all_records[
                        (all_records['date'] >= start_date) &
                        (all_records['date'] <= end_date)
                    ]

                    # If no data in the selected range, use all data
                    if filtered_data.empty:
                        self.current_data = all_records
                    else:
                        self.current_data = filtered_data
            else:
                self.current_data = pd.DataFrame()

            # Calculate analytics
            self.analytics_stats = calculate_attendance_statistics(self.current_data)

            # Update UI components
            self.update_kpi_cards()
            self.update_charts()
            self.update_insights()

        except Exception as e:
            print(f"Error refreshing attendance analytics data: {e}")
            import traceback
            traceback.print_exc()
    
    def get_date_range_days(self) -> int:
        """Get number of days for current date range selection"""
        range_map = {
            'Last 7 Days': 7,
            'Last 30 Days': 30,
            'Last 90 Days': 90,
            'Current Semester': 120,  # Approximate semester length
            'All Time': 365 * 10  # 10 years as "all time"
        }
        return range_map.get(self.date_range_combo.currentText(), 30)

    def update_kpi_cards(self):
        """Update KPI cards with current statistics"""
        if not self.analytics_stats:
            return

        try:
            # Overall Attendance Rate
            attendance_rate = self.analytics_stats.get('overall_attendance_rate', 0)
            self.kpi_cards['attendance_rate'].update_values(
                f"{attendance_rate:.1f}%",
                "Overall"
            )

            # Working Days
            working_days = self.analytics_stats.get('working_days', 0)
            self.kpi_cards['working_days'].update_values(
                str(working_days),
                "Total Days"
            )

            # Present Days
            present_days = self.analytics_stats.get('present_days', 0)
            self.kpi_cards['present_days'].update_values(
                str(present_days),
                "Days Attended"
            )

            # This Month
            month_stats = self.analytics_stats.get('current_month', {})
            month_rate = month_stats.get('attendance_rate', 0)
            self.kpi_cards['month_progress'].update_values(
                f"{month_rate:.1f}%",
                "Attendance Rate"
            )

            # This Week
            week_stats = self.analytics_stats.get('current_week', {})
            week_rate = week_stats.get('attendance_rate', 0)
            self.kpi_cards['week_progress'].update_values(
                f"{week_rate:.1f}%",
                "Attendance Rate"
            )

            # Period Attendance
            period_rate = self.analytics_stats.get('period_attendance_rate', 0)
            self.kpi_cards['period_attendance'].update_values(
                f"{period_rate:.1f}%",
                "Overall Periods"
            )

        except Exception as e:
            print(f"Error updating KPI cards: {e}")

    def update_charts(self):
        """Update all chart widgets with current data"""
        if self.current_data.empty:
            return

        try:
            # Update main charts
            self.pie_chart.update_chart(self.current_data)
            self.time_series_chart.update_chart(self.current_data)
            self.bar_chart.update_chart(self.current_data)
            self.scatter_chart.update_chart(self.current_data)

            # Update mini charts
            self.mini_pie_chart.update_chart(self.current_data)
            self.mini_bar_chart.update_chart(self.current_data)

        except Exception as e:
            print(f"Error updating charts: {e}")
            import traceback
            traceback.print_exc()

    def update_insights(self):
        """Update insights section with recommendations"""
        try:
            # Clear existing insights
            for i in reversed(range(self.insights_layout.count())):
                child = self.insights_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # Generate new insights
            insights = get_attendance_insights(self.current_data)

            # DEBUGGING: Add a test insight to verify text visibility
            if not insights or len(insights) == 0:
                insights = ["🧪 TEST: This is a test insight to verify text visibility in light theme."]

            if not insights:
                no_insights_label = QLabel("No insights available. Start tracking attendance to see recommendations!")
                no_insights_label.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
                self.insights_layout.addWidget(no_insights_label)
                return

            # Add insights with theme-aware styling
            for insight in insights:
                insight_label = QLabel(insight)
                insight_label.setWordWrap(True)
                insight_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Make text selectable for debugging
                insight_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Ensure proper alignment
                # CRITICAL FIX: Use theme-aware styling instead of hardcoded dark theme
                insight_label.setStyleSheet(self.get_insight_label_style())
                # Debug: Print insight text to verify content
                print(f"DEBUG: Adding insight: {insight[:50]}...")
                self.insights_layout.addWidget(insight_label)

            self.insights_layout.addStretch()

        except Exception as e:
            print(f"Error updating insights: {e}")

    def get_insight_label_style(self):
        """Get theme-aware styling for insight labels - CRITICAL FIX for black bars"""
        if self.current_theme == 'dark':
            return """
                QLabel {
                    background-color: #252526 !important;
                    border: 1px solid #3e3e42 !important;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 2px;
                    font-size: 12px !important;
                    color: #ffffff !important;
                    font-weight: normal !important;
                }
            """
        elif self.current_theme == 'colorwave':
            return """
                QLabel {
                    background-color: #1a1a2e !important;
                    border: 1px solid #4a3c5a !important;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 2px;
                    font-size: 12px !important;
                    color: #ffffff !important;
                    font-weight: normal !important;
                }
            """
        else:  # light theme - ENHANCED FIX for text visibility
            return """
                QLabel {
                    background-color: #f8f9fa !important;
                    border: 1px solid #dee2e6 !important;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 2px;
                    font-size: 13px !important;
                    color: #000000 !important;
                    font-weight: normal !important;
                    font-family: Arial, sans-serif !important;
                    text-align: left !important;
                    min-height: 20px !important;
                }
            """

    def update_theme(self, new_theme):
        """Update theme for all components - CRITICAL FIX for insights styling"""
        self.current_theme = new_theme

        # Update all chart widgets
        for widget in [self.pie_chart, self.time_series_chart, self.bar_chart,
                      self.scatter_chart, self.heatmap_chart]:
            if hasattr(widget, 'current_theme'):
                widget.current_theme = new_theme
            if hasattr(widget, 'update_theme'):
                widget.update_theme(new_theme)

        # Update mini charts
        for widget in [self.mini_pie_chart, self.mini_bar_chart]:
            if hasattr(widget, 'current_theme'):
                widget.current_theme = new_theme
            if hasattr(widget, 'update_theme'):
                widget.update_theme(new_theme)

        # CRITICAL FIX: Refresh insights with new theme styling
        self.update_insights()

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get summary of current analytics for external use"""
        return {
            'overall_attendance_rate': self.analytics_stats.get('overall_attendance_rate', 0),
            'working_days': self.analytics_stats.get('working_days', 0),
            'present_days': self.analytics_stats.get('present_days', 0),
            'absent_days': self.analytics_stats.get('absent_days', 0),
            'period_attendance_rate': self.analytics_stats.get('period_attendance_rate', 0),
            'current_month': self.analytics_stats.get('current_month', {}),
            'current_week': self.analytics_stats.get('current_week', {}),
            'data_range': self.analytics_stats.get('date_range', {})
        }
