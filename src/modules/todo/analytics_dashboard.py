"""
To-Do Analytics Dashboard
Main dashboard widget for comprehensive to-do tracking analytics
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

from ..todos.models import TodoDataModel
from .analytics_utils import calculate_todo_statistics, get_todo_insights
from .interactive_charts import (
    InteractivePieChartWidget,
    InteractiveTimeSeriesWidget,
    InteractiveBarChartWidget,
    InteractiveScatterPlotWidget,
    InteractiveHeatmapWidget,
    InteractiveTreemapWidget
)
from ..expenses.visualization import SummaryCardWidget


class TodoAnalyticsDashboard(QWidget):
    """Main to-do analytics dashboard with comprehensive visualizations"""
    
    def __init__(self, todo_model: TodoDataModel, parent=None):
        super().__init__(parent)
        
        self.todo_model = todo_model
        self.current_data = pd.DataFrame()
        self.analytics_stats = {}
        
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
        title_label = QLabel("📋 To-Do Analytics Dashboard")
        title_label.setObjectName("dashboardTitle")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        # Status filter
        status_label = QLabel("Status Filter:")
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(['All Tasks', 'Completed', 'Pending', 'In Progress', 'Cancelled'])
        self.status_filter_combo.setCurrentText('All Tasks')
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)
        
        # Priority filter
        priority_label = QLabel("Priority Filter:")
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItems(['All Priorities', 'Urgent', 'High', 'Medium', 'Low'])
        self.priority_filter_combo.setCurrentText('All Priorities')
        self.priority_filter_combo.currentTextChanged.connect(self.on_filter_changed)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        header_layout.addWidget(self.status_filter_combo)
        header_layout.addWidget(priority_label)
        header_layout.addWidget(self.priority_filter_combo)
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
        self.create_advanced_tab()
        
        layout.addWidget(self.tab_widget)
    
    def create_overview_tab(self):
        """Create overview tab with KPIs and summary"""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setContentsMargins(10, 10, 10, 10)
        overview_layout.setSpacing(15)
        
        # Create scroll area
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
        
        content_layout.addStretch()
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
    
    def create_advanced_tab(self):
        """Create advanced analytics tab"""
        advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(advanced_widget)
        advanced_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create advanced chart sub-tabs
        advanced_tabs = QTabWidget()
        
        # Heatmap Tab
        self.heatmap_chart = InteractiveHeatmapWidget()
        advanced_tabs.addTab(self.heatmap_chart, "🔥 Heatmaps")
        
        # Treemap Tab
        self.treemap_chart = InteractiveTreemapWidget()
        advanced_tabs.addTab(self.treemap_chart, "🌳 Treemaps")
        
        advanced_layout.addWidget(advanced_tabs)
        self.tab_widget.addTab(advanced_widget, "🔬 Advanced Analytics")
    
    def create_kpi_section(self, layout):
        """Create KPI cards section"""
        # Section title
        kpi_title = QLabel("Key Performance Indicators")
        kpi_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        kpi_title.setFont(font)
        layout.addWidget(kpi_title)
        
        # KPI cards grid - expanded layout for better visual appeal
        kpi_frame = QFrame()
        kpi_frame.setObjectName("kpiFrame")
        # CRITICAL FIX: Remove height restrictions to allow cards to expand properly
        kpi_frame.setMinimumHeight(200)  # Increased minimum height for more spacious layout
        # Remove maximum height constraint to allow natural expansion
        kpi_layout = QGridLayout(kpi_frame)
        kpi_layout.setSpacing(25)  # Increased spacing between cards for better visual separation
        kpi_layout.setContentsMargins(20, 20, 20, 20)  # More generous margins around the grid
        
        # Create KPI cards
        self.kpi_cards = {}
        
        # Total Tasks Card
        self.kpi_cards['total_tasks'] = SummaryCardWidget(
            "Total Tasks", "0", "All Tasks", "📋"
        )
        
        # Completion Rate Card
        self.kpi_cards['completion_rate'] = SummaryCardWidget(
            "Completion Rate", "0%", "Overall", "✅"
        )
        
        # Pending Tasks Card
        self.kpi_cards['pending_tasks'] = SummaryCardWidget(
            "Pending Tasks", "0", "To Complete", "⏳"
        )
        
        # Overdue Tasks Card
        self.kpi_cards['overdue_tasks'] = SummaryCardWidget(
            "Overdue Tasks", "0", "Past Due", "⚠️"
        )
        
        # In Progress Card
        self.kpi_cards['in_progress'] = SummaryCardWidget(
            "In Progress", "0", "Active Tasks", "🔄"
        )
        
        # Average Hours Card
        self.kpi_cards['avg_hours'] = SummaryCardWidget(
            "Avg. Hours", "0.0", "Per Task", "⏱️"
        )
        
        # Add cards to grid
        kpi_layout.addWidget(self.kpi_cards['total_tasks'], 0, 0)
        kpi_layout.addWidget(self.kpi_cards['completion_rate'], 0, 1)
        kpi_layout.addWidget(self.kpi_cards['pending_tasks'], 0, 2)
        kpi_layout.addWidget(self.kpi_cards['overdue_tasks'], 1, 0)
        kpi_layout.addWidget(self.kpi_cards['in_progress'], 1, 1)
        kpi_layout.addWidget(self.kpi_cards['avg_hours'], 1, 2)
        
        layout.addWidget(kpi_frame)
    
    def create_quick_charts_section(self, layout):
        """Create quick charts section - EXPANDED: Responsive sizing for full chart visibility"""
        # Section title
        charts_title = QLabel("Quick Analytics")
        charts_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        charts_title.setFont(font)
        layout.addWidget(charts_title)

        # Charts container - SIMPLE FIX: Remove excessive minimum height constraint
        charts_frame = QFrame()
        charts_frame.setObjectName("chartsFrame")
        # SIMPLE FIX: Remove minimum height constraint to eliminate empty white space
        # Let the charts determine their own natural size
        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setSpacing(20)  # Increased spacing for better visual separation
        charts_layout.setContentsMargins(15, 15, 15, 15)  # Add margins for better layout

        # Create responsive charts - VERTICAL SPACE FIX: Use Minimum height policy
        self.mini_pie_chart = InteractivePieChartWidget()
        # VERTICAL SPACE FIX: Expand horizontally but only take minimum vertical space needed
        self.mini_pie_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.mini_bar_chart = InteractiveBarChartWidget()
        # VERTICAL SPACE FIX: Expand horizontally but only take minimum vertical space needed
        self.mini_bar_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        charts_layout.addWidget(self.mini_pie_chart)
        charts_layout.addWidget(self.mini_bar_chart)
        
        layout.addWidget(charts_frame)
    
    def create_insights_section(self, layout):
        """Create insights and recommendations section"""
        # Section title
        insights_title = QLabel("Insights & Recommendations")
        insights_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        insights_title.setFont(font)
        layout.addWidget(insights_title)
        
        # Insights container
        self.insights_frame = QFrame()
        self.insights_frame.setObjectName("insightsFrame")
        self.insights_layout = QVBoxLayout(self.insights_frame)
        self.insights_layout.setContentsMargins(15, 15, 15, 15)
        self.insights_layout.setSpacing(10)
        
        layout.addWidget(self.insights_frame)
    
    def setup_connections(self):
        """Setup signal connections"""
        pass
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh all data and update visualizations"""
        try:
            # Get to-do data
            all_records = self.todo_model.get_all_todos()
            
            if not all_records.empty:
                # Apply filters
                self.current_data = self.apply_filters(all_records)
            else:
                self.current_data = pd.DataFrame()
            
            # Calculate analytics
            self.analytics_stats = calculate_todo_statistics(self.current_data)
            
            # Update UI components
            self.update_kpi_cards()
            self.update_charts()
            self.update_insights()
            
        except Exception as e:
            print(f"Error refreshing to-do analytics data: {e}")
            import traceback
            traceback.print_exc()
    
    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply status and priority filters to data"""
        filtered_data = data.copy()
        
        # Apply status filter
        status_filter = self.status_filter_combo.currentText()
        if status_filter != 'All Tasks':
            filtered_data = filtered_data[filtered_data['status'] == status_filter]
        
        # Apply priority filter
        priority_filter = self.priority_filter_combo.currentText()
        if priority_filter != 'All Priorities':
            filtered_data = filtered_data[filtered_data['priority'] == priority_filter]
        
        return filtered_data

    def update_kpi_cards(self):
        """Update KPI cards with current statistics"""
        if not self.analytics_stats:
            return

        try:
            # Total Tasks
            total_tasks = self.analytics_stats.get('total_tasks', 0)
            self.kpi_cards['total_tasks'].update_values(
                str(total_tasks),
                "All Tasks"
            )

            # Completion Rate
            completion_rate = self.analytics_stats.get('completion_rate', 0)
            self.kpi_cards['completion_rate'].update_values(
                f"{completion_rate:.1f}%",
                "Overall"
            )

            # Pending Tasks
            pending_tasks = self.analytics_stats.get('pending_tasks', 0)
            self.kpi_cards['pending_tasks'].update_values(
                str(pending_tasks),
                "To Complete"
            )

            # Overdue Tasks
            overdue_tasks = self.analytics_stats.get('overdue_tasks', 0)
            self.kpi_cards['overdue_tasks'].update_values(
                str(overdue_tasks),
                "Past Due"
            )

            # In Progress
            in_progress = self.analytics_stats.get('in_progress_tasks', 0)
            self.kpi_cards['in_progress'].update_values(
                str(in_progress),
                "Active Tasks"
            )

            # Average Hours
            hours_analysis = self.analytics_stats.get('hours_analysis', {})
            avg_hours = hours_analysis.get('average_estimated_hours', 0)
            self.kpi_cards['avg_hours'].update_values(
                f"{avg_hours:.1f}",
                "Per Task"
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
            self.heatmap_chart.update_chart(self.current_data)
            self.treemap_chart.update_chart(self.current_data)

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
            insights = get_todo_insights(self.current_data)

            if not insights:
                no_insights_label = QLabel("No insights available. Start adding tasks to see recommendations!")
                no_insights_label.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
                self.insights_layout.addWidget(no_insights_label)
                return

            # Add insights
            for insight in insights:
                insight_label = QLabel(insight)
                insight_label.setWordWrap(True)
                insight_label.setStyleSheet("""
                    QLabel {
                        background-color: #f0f8ff;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                        padding: 10px;
                        margin: 2px;
                        font-size: 12px;
                    }
                """)
                self.insights_layout.addWidget(insight_label)

            self.insights_layout.addStretch()

        except Exception as e:
            print(f"Error updating insights: {e}")

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get summary of current analytics for external use"""
        return {
            'total_tasks': self.analytics_stats.get('total_tasks', 0),
            'completed_tasks': self.analytics_stats.get('completed_tasks', 0),
            'pending_tasks': self.analytics_stats.get('pending_tasks', 0),
            'in_progress_tasks': self.analytics_stats.get('in_progress_tasks', 0),
            'overdue_tasks': self.analytics_stats.get('overdue_tasks', 0),
            'completion_rate': self.analytics_stats.get('completion_rate', 0),
            'overdue_rate': self.analytics_stats.get('overdue_rate', 0),
            'hours_analysis': self.analytics_stats.get('hours_analysis', {}),
            'productivity_metrics': self.analytics_stats.get('productivity_metrics', {})
        }
