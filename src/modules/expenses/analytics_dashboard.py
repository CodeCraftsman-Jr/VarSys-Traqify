"""
Expense Analytics Dashboard Module
Provides comprehensive analytics dashboard for expense data with KPIs, charts, and insights
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QGroupBox, QPushButton, QComboBox, QDateEdit, QCheckBox, QScrollArea,
    QTabWidget, QSplitter, QSpinBox, QProgressBar, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont
from PySide6.QtGui import QFont, QPalette

from .models import ExpenseDataModel
from .analytics_utils import calculate_expense_statistics, get_expense_insights
from .interactive_charts import (
    InteractivePieChartWidget,
    InteractiveTimeSeriesWidget,
    InteractiveBarChartWidget,
    InteractiveScatterPlotWidget,
    InteractiveHeatmapWidget,
    InteractiveDashboardWidget
)
from .visualization import SummaryCardWidget, PieChartWidget, BarChartWidget, LineChartWidget
from .basic_charts import BasicPieChartWidget, BasicBarChartWidget, BasicLineChartWidget


class ExpenseAnalyticsDashboard(QWidget):
    """Comprehensive expense analytics dashboard with multiple chart types and KPIs"""
    
    data_export_requested = Signal(str)  # Signal for data export requests
    
    def __init__(self, expense_model, config=None, parent=None):
        super().__init__(parent)
        self.expense_model = expense_model
        self.config = config
        self.current_data = pd.DataFrame()
        self.ui_initialized = False

        # Get current theme from config
        self.current_theme = getattr(config, 'theme', 'light') if config else 'light'

        # CRITICAL FIX: Increased minimum size to accommodate larger chart margins
        self.setMinimumSize(1000, 700)  # Increased to provide more space for charts with larger margins
        self.apply_theme_styling()

        # Initialize UI immediately for dashboard tab usage
        try:
            print("Setting up Expense Analytics Dashboard UI...")

            # Test the data manager path immediately
            file_path = expense_model.data_manager.get_file_path("expenses", "expenses.csv")
            print(f"Expense Analytics: Data file path: {file_path}")
            print(f"Expense Analytics: File exists: {file_path.exists()}")

            self.setup_ui()
            self.setup_refresh_timer()
            self.ui_initialized = True  # Set this before refresh_data

            # Apply theme after UI is fully initialized
            self.apply_theme_styling()
            print("Expense Analytics: About to call refresh_data...")
            self.refresh_data()
            print("Expense Analytics Dashboard initialized successfully")

        except Exception as e:
            print(f"Error initializing Expense Analytics Dashboard: {e}")
            import traceback
            traceback.print_exc()

    def apply_theme_styling(self):
        """Apply theme-aware styling to the dashboard"""
        if not hasattr(self, 'current_theme'):
            self.current_theme = 'light'

        if self.current_theme == 'light':
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
        elif self.current_theme == 'dark':
            self.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555555;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)

    def setup_ui(self):
        """Setup the analytics dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with controls
        self.create_header(layout)

        # Main content with tabs
        self.create_main_content(layout)

    def create_header(self, layout):
        """Create header with title and controls"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)

        # Title
        title_label = QLabel("💰 Expense Analytics Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Date range selector
        header_layout.addWidget(QLabel("Date Range:"))
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems([
            "Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 3 Months",
            "Current Month", "Last 6 Months", "All Time"
        ])
        self.date_range_combo.setCurrentText("Last 3 Months")  # CRITICAL FIX: Show last 3 months by default
        self.date_range_combo.currentTextChanged.connect(self.on_date_range_changed)
        header_layout.addWidget(self.date_range_combo)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)

        # Export button
        export_btn = QPushButton("📊 Export")
        export_btn.clicked.connect(self.on_export_clicked)
        header_layout.addWidget(export_btn)

        layout.addWidget(header_frame)

    def create_main_content(self, layout):
        """Create main content area with tabs"""
        self.tab_widget = QTabWidget()

        # Overview tab with KPIs and summary charts
        self.create_overview_tab()

        # Category analysis tab
        self.create_category_tab()

        # Time analysis tab
        self.create_time_tab()

        # Advanced analytics tab
        self.create_advanced_tab()

        layout.addWidget(self.tab_widget)

    def create_overview_tab(self):
        """Create overview tab with KPIs and summary - APPLIED TO DO ANALYTICS LAYOUT APPROACH"""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setContentsMargins(10, 10, 10, 10)
        overview_layout.setSpacing(15)

        # CRITICAL FIX: Create scroll area like To Do Analytics to prevent chart visibility issues
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add title and description - CRITICAL FIX: Missing title and description in Overview tab
        title_label = QLabel("💰 Expense Overview")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        # CRITICAL FIX: Ensure text is visible in all themes with fallback colors
        title_label.setStyleSheet("""
            color: #2c3e50;
            margin-bottom: 10px;
            padding: 5px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(title_label)

        desc_label = QLabel("Comprehensive overview of your expense data with key performance indicators and interactive charts")
        desc_label.setObjectName("sectionDescription")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #7f8c8d;
            margin-bottom: 15px;
            font-size: 14px;
            padding: 0px 0px 10px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(desc_label)

        # KPI Cards
        self.create_kpi_section(content_layout)

        # Add section title for interactive charts - CRITICAL FIX: Add section title for better organization
        charts_title = QLabel("Interactive Analytics")
        charts_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        charts_title.setFont(font)
        charts_title.setStyleSheet("color: #34495e; margin-top: 20px; margin-bottom: 10px;")
        content_layout.addWidget(charts_title)

        # Interactive dashboard with mini charts
        self.interactive_dashboard = InteractiveDashboardWidget()
        # Set theme on the dashboard widget
        if hasattr(self.interactive_dashboard, 'current_theme'):
            self.interactive_dashboard.current_theme = self.current_theme
        content_layout.addWidget(self.interactive_dashboard)

        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        overview_layout.addWidget(scroll_area)

        self.tab_widget.addTab(overview_widget, "📊 Overview")

    def create_category_tab(self):
        """Create category analysis tab with fallback charts - APPLIED TO DO ANALYTICS LAYOUT APPROACH"""
        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        category_layout.setContentsMargins(10, 10, 10, 10)
        category_layout.setSpacing(15)

        # CRITICAL FIX: Create scroll area like To Do Analytics to prevent chart visibility issues
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add title and description - CRITICAL FIX: Improved styling for better visibility
        title_label = QLabel("📂 Category Analysis")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        # CRITICAL FIX: Ensure text is visible in all themes with fallback colors
        title_label.setStyleSheet("""
            color: #2c3e50;
            margin-bottom: 10px;
            padding: 5px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(title_label)

        desc_label = QLabel("Analyze your spending patterns across different expense categories")
        desc_label.setObjectName("sectionDescription")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #7f8c8d;
            margin-bottom: 15px;
            font-size: 14px;
            padding: 0px 0px 10px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(desc_label)

        # Category charts with fallback - APPLIED TO DO ANALYTICS APPROACH: Allow natural expansion
        charts_splitter = QSplitter(Qt.Horizontal)

        # Try interactive charts first, fallback to basic charts
        try:
            # Interactive pie chart
            print("Creating InteractivePieChartWidget...")
            self.category_pie_chart = InteractivePieChartWidget()
            if hasattr(self.category_pie_chart, 'current_theme'):
                self.category_pie_chart.current_theme = self.current_theme
            charts_splitter.addWidget(self.category_pie_chart)
            print(f"✓ Created category pie chart: {self.category_pie_chart.__class__.__name__}")

            # Interactive bar chart
            print("Creating InteractiveBarChartWidget...")
            self.category_bar_chart = InteractiveBarChartWidget()
            if hasattr(self.category_bar_chart, 'current_theme'):
                self.category_bar_chart.current_theme = self.current_theme
            charts_splitter.addWidget(self.category_bar_chart)
            print(f"✓ Created category bar chart: {self.category_bar_chart.__class__.__name__}")

            print("Category tab: Using interactive charts")
        except Exception as e:
            print(f"Category tab: Interactive charts failed, using fallback: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to basic charts
            self.category_pie_chart = PieChartWidget(theme=self.current_theme)
            self.category_bar_chart = BarChartWidget(theme=self.current_theme)
            charts_splitter.addWidget(self.category_pie_chart)
            charts_splitter.addWidget(self.category_bar_chart)
            print(f"✓ Using fallback charts: {self.category_pie_chart.__class__.__name__}, {self.category_bar_chart.__class__.__name__}")

        content_layout.addWidget(charts_splitter)

        # Add summary section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; margin-top: 10px;")
        summary_layout = QVBoxLayout(summary_frame)

        self.category_summary_label = QLabel("Category insights will appear here after data loads...")
        self.category_summary_label.setWordWrap(True)
        summary_layout.addWidget(self.category_summary_label)

        content_layout.addWidget(summary_frame)

        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        category_layout.addWidget(scroll_area)

        self.tab_widget.addTab(category_widget, "📂 Categories")

    def create_time_tab(self):
        """Create time analysis tab with fallback charts - APPLIED TO DO ANALYTICS LAYOUT APPROACH"""
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setContentsMargins(10, 10, 10, 10)
        time_layout.setSpacing(15)

        # CRITICAL FIX: Create scroll area like To Do Analytics to prevent chart visibility issues
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add title and description - CRITICAL FIX: Improved styling for better visibility
        title_label = QLabel("📈 Time Analysis")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        # CRITICAL FIX: Ensure text is visible in all themes with fallback colors
        title_label.setStyleSheet("""
            color: #2c3e50;
            margin-bottom: 10px;
            padding: 5px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(title_label)

        desc_label = QLabel("Track your spending trends and patterns over time")
        desc_label.setObjectName("sectionDescription")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #7f8c8d;
            margin-bottom: 15px;
            font-size: 14px;
            padding: 0px 0px 10px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(desc_label)

        # Time series chart with fallback - APPLIED TO DO ANALYTICS APPROACH: Allow natural expansion
        try:
            print("Creating InteractiveTimeSeriesWidget...")
            self.time_series_chart = InteractiveTimeSeriesWidget()
            if hasattr(self.time_series_chart, 'current_theme'):
                self.time_series_chart.current_theme = self.current_theme
            content_layout.addWidget(self.time_series_chart)
            print(f"✓ Created time series chart: {self.time_series_chart.__class__.__name__}")
        except Exception as e:
            print(f"Time tab: Interactive time series failed, using fallback: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to basic line chart
            self.time_series_chart = LineChartWidget(theme=self.current_theme)
            content_layout.addWidget(self.time_series_chart)
            print(f"✓ Using fallback time series: {self.time_series_chart.__class__.__name__}")

        # Heatmap with fallback (or simple text summary)
        try:
            print("Creating InteractiveHeatmapWidget...")
            self.time_heatmap = InteractiveHeatmapWidget()
            if hasattr(self.time_heatmap, 'current_theme'):
                self.time_heatmap.current_theme = self.current_theme
            content_layout.addWidget(self.time_heatmap)
            print(f"✓ Created heatmap: {self.time_heatmap.__class__.__name__}")
        except Exception as e:
            print(f"Time tab: Interactive heatmap failed, using text summary: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to text-based pattern summary
            pattern_frame = QFrame()
            pattern_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px;")
            pattern_layout = QVBoxLayout(pattern_frame)

            pattern_title = QLabel("📊 Spending Patterns")
            pattern_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            pattern_layout.addWidget(pattern_title)

            self.time_heatmap = QLabel("Time-based spending patterns will appear here after data loads...")
            self.time_heatmap.setWordWrap(True)
            pattern_layout.addWidget(self.time_heatmap)

            content_layout.addWidget(pattern_frame)
            print("✓ Using text-based time patterns fallback")

        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        time_layout.addWidget(scroll_area)

        self.tab_widget.addTab(time_widget, "📈 Time Analysis")

    def create_advanced_tab(self):
        """Create advanced analytics tab with comprehensive analysis - APPLIED TO DO ANALYTICS LAYOUT APPROACH"""
        advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(advanced_widget)
        advanced_layout.setContentsMargins(10, 10, 10, 10)
        advanced_layout.setSpacing(15)

        # CRITICAL FIX: Create scroll area like To Do Analytics to prevent chart visibility issues
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add title and description - CRITICAL FIX: Improved styling for better visibility
        title_label = QLabel("🔬 Advanced Analytics")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        # CRITICAL FIX: Ensure text is visible in all themes with fallback colors
        title_label.setStyleSheet("""
            color: #2c3e50;
            margin-bottom: 10px;
            padding: 5px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(title_label)

        desc_label = QLabel("Deep insights, correlations, and advanced spending analysis")
        desc_label.setObjectName("sectionDescription")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #7f8c8d;
            margin-bottom: 15px;
            font-size: 14px;
            padding: 0px 0px 10px 0px;
            background-color: transparent;
            border: none;
        """)
        content_layout.addWidget(desc_label)

        # Create tabbed advanced content - APPLIED TO DO ANALYTICS APPROACH: Allow natural expansion
        advanced_tabs = QTabWidget()

        # Correlation Analysis Tab
        correlation_widget = QWidget()
        correlation_layout = QVBoxLayout(correlation_widget)

        try:
            print("Creating InteractiveScatterPlotWidget...")
            self.scatter_plot = InteractiveScatterPlotWidget()
            if hasattr(self.scatter_plot, 'current_theme'):
                self.scatter_plot.current_theme = self.current_theme
            correlation_layout.addWidget(self.scatter_plot)
            print(f"✓ Created scatter plot: {self.scatter_plot.__class__.__name__}")
        except Exception as e:
            print(f"Advanced tab: Interactive scatter plot failed, using text analysis: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to text-based correlation analysis
            correlation_frame = QFrame()
            correlation_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px;")
            correlation_frame_layout = QVBoxLayout(correlation_frame)

            self.scatter_plot = QLabel("Correlation analysis will appear here after data loads...")
            self.scatter_plot.setWordWrap(True)
            correlation_frame_layout.addWidget(self.scatter_plot)
            correlation_layout.addWidget(correlation_frame)
            print("✓ Using text-based correlation analysis fallback")

        advanced_tabs.addTab(correlation_widget, "📊 Correlations")

        # Insights Tab
        insights_widget = QWidget()
        insights_layout = QVBoxLayout(insights_widget)

        insights_frame = QFrame()
        insights_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px;")
        insights_frame_layout = QVBoxLayout(insights_frame)

        insights_title = QLabel("💡 Advanced Insights")
        insights_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        insights_frame_layout.addWidget(insights_title)

        self.advanced_insights_label = QLabel("Advanced insights and recommendations will appear here after data loads...")
        self.advanced_insights_label.setWordWrap(True)
        insights_frame_layout.addWidget(self.advanced_insights_label)

        insights_layout.addWidget(insights_frame)
        advanced_tabs.addTab(insights_widget, "💡 Insights")

        # Statistics Tab
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)

        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px;")
        stats_frame_layout = QVBoxLayout(stats_frame)

        stats_title = QLabel("📈 Statistical Analysis")
        stats_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        stats_frame_layout.addWidget(stats_title)

        self.advanced_stats_label = QLabel("Statistical analysis will appear here after data loads...")
        self.advanced_stats_label.setWordWrap(True)
        stats_frame_layout.addWidget(self.advanced_stats_label)

        stats_layout.addWidget(stats_frame)
        advanced_tabs.addTab(stats_widget, "📈 Statistics")

        content_layout.addWidget(advanced_tabs)

        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        advanced_layout.addWidget(scroll_area)

        self.tab_widget.addTab(advanced_widget, "🔬 Advanced")

    def create_kpi_section(self, layout):
        """Create KPI cards section - APPLIED TO DO ANALYTICS LAYOUT APPROACH"""
        kpi_frame = QFrame()
        kpi_frame.setObjectName("kpiFrame")
        # CRITICAL FIX: Dynamic sizing - allow cards to expand based on content
        kpi_frame.setMinimumHeight(180)  # Reasonable minimum height for usability
        # Remove maximum height constraint to allow natural expansion based on content
        kpi_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        kpi_layout = QGridLayout(kpi_frame)
        kpi_layout.setSpacing(25)  # Increased spacing between cards for better visual separation
        kpi_layout.setContentsMargins(20, 20, 20, 20)  # More generous margins around the grid

        # Create KPI cards
        self.total_expenses_card = SummaryCardWidget(
            "Total Expenses", "₹0", "Selected Period", "💰", theme=self.current_theme
        )
        kpi_layout.addWidget(self.total_expenses_card, 0, 0)

        self.avg_daily_card = SummaryCardWidget(
            "Daily Average", "₹0", "Per Day", "📊", theme=self.current_theme
        )
        kpi_layout.addWidget(self.avg_daily_card, 0, 1)

        self.transaction_count_card = SummaryCardWidget(
            "Transactions", "0", "Total Count", "🔢", theme=self.current_theme
        )
        kpi_layout.addWidget(self.transaction_count_card, 0, 2)

        self.top_category_card = SummaryCardWidget(
            "Top Category", "N/A", "Highest Spending", "🏷️", theme=self.current_theme
        )
        kpi_layout.addWidget(self.top_category_card, 1, 0)

        self.largest_expense_card = SummaryCardWidget(
            "Largest Expense", "₹0", "Single Transaction", "💸", theme=self.current_theme
        )
        kpi_layout.addWidget(self.largest_expense_card, 1, 1)

        self.spending_trend_card = SummaryCardWidget(
            "Trend", "0%", "vs Previous Period", "📈", theme=self.current_theme
        )
        kpi_layout.addWidget(self.spending_trend_card, 1, 2)

        layout.addWidget(kpi_frame)

    def setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes

    def on_date_range_changed(self):
        """Handle date range change"""
        self.refresh_data()

    def on_export_clicked(self):
        """Handle export button click"""
        if self.current_data.empty:
            return
        
        # Emit signal for export
        self.data_export_requested.emit("expense_analytics")

    def refresh_data(self):
        """Refresh dashboard data"""
        if not self.ui_initialized:
            return

        try:
            print("Refreshing expense analytics data...")

            # Get date range
            date_range = self.date_range_combo.currentText()
            start_date, end_date = self._get_date_range(date_range)

            # CRITICAL FIX: For "All Time", get all expenses directly to ensure we get all data
            if date_range == "All Time":
                print("Loading ALL expense data (no date filtering)")
                all_data = self.expense_model.get_all_expenses()
                # Filter for expenses only
                if not all_data.empty and 'type' in all_data.columns:
                    self.current_data = all_data[all_data['type'] == 'Expense']
                    print(f"Loaded {len(self.current_data)} expense records from all data")
                else:
                    self.current_data = all_data
            else:
                # Get expense data with date range filtering
                self.current_data = self.expense_model.get_expenses_by_date_range(start_date, end_date)

            print(f"Loaded {len(self.current_data)} expense records for date range {start_date} to {end_date}")

            # Debug: Show sample data if available
            if not self.current_data.empty:
                print("Sample expense data:")
                print(self.current_data[['date', 'category', 'amount', 'type']].head())
                print(f"Unique categories: {self.current_data['category'].unique()}")
                print(f"Date range in data: {self.current_data['date'].min()} to {self.current_data['date'].max()}")
            else:
                print("No expense data found - checking if there's any data at all...")
                all_data = self.expense_model.get_all_expenses()
                print(f"Total records in database: {len(all_data)}")
                if not all_data.empty and 'type' in all_data.columns:
                    type_counts = all_data['type'].value_counts()
                    print(f"Record types: {type_counts.to_dict()}")
                    if 'date' in all_data.columns:
                        all_data['date'] = pd.to_datetime(all_data['date'])
                        print(f"Date range in all data: {all_data['date'].min()} to {all_data['date'].max()}")
                        print(f"Requested date range: {start_date} to {end_date}")
            
            # Update all components
            self.update_kpis()
            self.update_charts()

            # If no data, show empty state
            if self.current_data.empty:
                self._update_empty_state()

        except Exception as e:
            print(f"Error refreshing expense analytics data: {e}")
            import traceback
            traceback.print_exc()
            # Show error state
            self._update_empty_state()

    def _get_date_range(self, range_text):
        """Get start and end dates for the selected range"""
        today = date.today()
        
        if range_text == "Last 7 Days":
            start_date = today - timedelta(days=7)
        elif range_text == "Last 30 Days":
            start_date = today - timedelta(days=30)
        elif range_text == "Last 90 Days":
            start_date = today - timedelta(days=90)
        elif range_text == "Last 3 Months":
            start_date = today - timedelta(days=90)  # 3 months ≈ 90 days
        elif range_text == "Current Month":
            start_date = today.replace(day=1)
        elif range_text == "Last 6 Months":
            start_date = today - timedelta(days=180)
        else:  # All Time
            start_date = date(2020, 1, 1)  # Far back date
            
        return start_date, today

    def update_kpis(self):
        """Update KPI cards"""
        if self.current_data.empty:
            return
        
        # Calculate metrics
        total_expenses = self.current_data['amount'].sum()
        avg_daily = total_expenses / max(len(self.current_data['date'].unique()), 1)
        transaction_count = len(self.current_data)
        top_category = self.current_data.groupby('category')['amount'].sum().idxmax()
        largest_expense = self.current_data['amount'].max()
        
        # Update cards
        self.total_expenses_card.update_values(f"₹{total_expenses:,.0f}", "Selected Period")
        self.avg_daily_card.update_values(f"₹{avg_daily:,.0f}", "Per Day")
        self.transaction_count_card.update_values(f"{transaction_count}", "Total Count")
        self.top_category_card.update_values(top_category, "Highest Spending")
        self.largest_expense_card.update_values(f"₹{largest_expense:,.0f}", "Single Transaction")
        self.spending_trend_card.update_values("0%", "vs Previous Period")  # TODO: Calculate trend

    def update_charts(self):
        """Update all charts with current data - ENHANCED with fallback content"""
        if self.current_data.empty:
            self._update_empty_state()
            return

        print(f"Updating charts with {len(self.current_data)} records...")

        # CRITICAL FIX: Ensure theme is applied to all widgets before updating charts
        self.update_theme(self.current_theme)

        # Update interactive dashboard
        if hasattr(self, 'interactive_dashboard'):
            try:
                self.interactive_dashboard.update_dashboard(self.current_data)
                print("Updated interactive dashboard")
            except Exception as e:
                print(f"Error updating interactive dashboard: {e}")

        # Update category charts
        self._update_category_charts()

        # Update time analysis charts
        self._update_time_charts()

        # Update advanced analytics
        self._update_advanced_analytics()

    def _update_category_charts(self):
        """Update category analysis charts and content"""
        try:
            # Update category pie chart
            if hasattr(self, 'category_pie_chart'):
                # Check if it's an interactive chart widget (expects 2 params) or basic chart widget (expects 4 params)
                if hasattr(self.category_pie_chart, '__class__') and 'Interactive' in self.category_pie_chart.__class__.__name__:
                    # Interactive chart widget - expects (data, title)
                    self.category_pie_chart.update_chart(self.current_data, "Expense Distribution by Category")
                else:
                    # Basic chart widget - expects (data, x_column, y_column, title)
                    self.category_pie_chart.update_chart(self.current_data, "category", "amount", "Expense Distribution by Category")
                print("Updated category pie chart")

            # Update category bar chart
            if hasattr(self, 'category_bar_chart'):
                # Check if it's an interactive chart widget (expects 2 params) or basic chart widget (expects 4 params)
                if hasattr(self.category_bar_chart, '__class__') and 'Interactive' in self.category_bar_chart.__class__.__name__:
                    # Interactive chart widget - expects (data, title)
                    self.category_bar_chart.update_chart(self.current_data, "Category Spending Analysis")
                else:
                    # Basic chart widget - expects (data, x_column, y_column, title)
                    self.category_bar_chart.update_chart(self.current_data, "category", "amount", "Category Spending Analysis")
                print("Updated category bar chart")

            # Update category summary
            if hasattr(self, 'category_summary_label'):
                summary_text = self._generate_category_summary()
                self.category_summary_label.setText(summary_text)
                print("Updated category summary")

        except Exception as e:
            print(f"Error updating category charts: {e}")
            import traceback
            traceback.print_exc()

    def _update_time_charts(self):
        """Update time analysis charts and content"""
        try:
            # Update time series chart
            if hasattr(self, 'time_series_chart'):
                # Check if it's an interactive chart widget (expects 2 params) or basic chart widget (expects 4 params)
                if hasattr(self.time_series_chart, '__class__') and 'Interactive' in self.time_series_chart.__class__.__name__:
                    # Interactive chart widget - expects (data, title)
                    self.time_series_chart.update_chart(self.current_data, "Expense Trends Over Time")
                else:
                    # Basic chart widget - expects (data, x_column, y_column, title)
                    self.time_series_chart.update_chart(self.current_data, "date", "amount", "Expense Trends Over Time")
                print("Updated time series chart")

            # Update heatmap or pattern analysis
            if hasattr(self, 'time_heatmap'):
                # Check if it's an interactive chart widget (expects 2 params) or text widget
                if hasattr(self.time_heatmap, '__class__') and 'Interactive' in self.time_heatmap.__class__.__name__:
                    # Interactive chart widget - expects (data, title)
                    self.time_heatmap.update_chart(self.current_data, "Spending Patterns Heatmap")
                elif hasattr(self.time_heatmap, 'setText'):
                    # Handle text-based fallback
                    pattern_text = self._generate_time_patterns()
                    self.time_heatmap.setText(pattern_text)
                print("Updated time heatmap/patterns")

        except Exception as e:
            print(f"Error updating time charts: {e}")
            import traceback
            traceback.print_exc()

    def _update_advanced_analytics(self):
        """Update advanced analytics content"""
        try:
            # Update scatter plot or correlation analysis
            if hasattr(self, 'scatter_plot'):
                # Check if it's an interactive chart widget (expects 2 params) or text widget
                if hasattr(self.scatter_plot, '__class__') and 'Interactive' in self.scatter_plot.__class__.__name__:
                    # Interactive chart widget - expects (data, title)
                    self.scatter_plot.update_chart(self.current_data, "Expense Correlation Analysis")
                elif hasattr(self.scatter_plot, 'setText'):
                    # Handle text-based fallback
                    correlation_text = self._generate_correlation_analysis()
                    self.scatter_plot.setText(correlation_text)
                print("Updated scatter plot/correlations")

            # Update advanced insights
            if hasattr(self, 'advanced_insights_label'):
                insights_text = self._generate_advanced_insights()
                self.advanced_insights_label.setText(insights_text)
                print("Updated advanced insights")

            # Update advanced statistics
            if hasattr(self, 'advanced_stats_label'):
                stats_text = self._generate_advanced_statistics()
                self.advanced_stats_label.setText(stats_text)
                print("Updated advanced statistics")

        except Exception as e:
            print(f"Error updating advanced analytics: {e}")
            import traceback
            traceback.print_exc()

    def _update_empty_state(self, error_message=None):
        """Update UI when no data is available"""
        if error_message:
            empty_message = f"Error loading data: {error_message}"
        else:
            # Get date range for more specific message
            date_range = self.date_range_combo.currentText() if hasattr(self, 'date_range_combo') else "selected period"
            empty_message = f"No expense data found for {date_range}. Try selecting a different date range or add some expenses to see analytics."

        # Update category summary
        if hasattr(self, 'category_summary_label'):
            self.category_summary_label.setText(f"📂 Category Analysis\n\n{empty_message}")

        # Update time patterns
        if hasattr(self, 'time_heatmap') and hasattr(self.time_heatmap, 'setText'):
            self.time_heatmap.setText(f"📈 Time Analysis\n\n{empty_message}")

        # Update advanced content
        if hasattr(self, 'scatter_plot') and hasattr(self.scatter_plot, 'setText'):
            self.scatter_plot.setText(f"🔬 Correlation Analysis\n\n{empty_message}")
        if hasattr(self, 'advanced_insights_label'):
            self.advanced_insights_label.setText(f"💡 Advanced Insights\n\n{empty_message}")
        if hasattr(self, 'advanced_stats_label'):
            self.advanced_stats_label.setText(f"📊 Statistical Analysis\n\n{empty_message}")

        # Clear charts if they exist
        for chart_attr in ['category_pie_chart', 'category_bar_chart', 'time_series_chart']:
            if hasattr(self, chart_attr):
                chart = getattr(self, chart_attr)
                if hasattr(chart, 'clear_chart'):
                    chart.clear_chart()

    def _generate_category_summary(self):
        """Generate category analysis summary text"""
        try:
            if self.current_data.empty:
                return "No data available for category analysis."

            # Calculate category statistics
            category_totals = self.current_data.groupby('category')['amount'].sum().sort_values(ascending=False)
            total_spending = self.current_data['amount'].sum()

            summary_lines = ["📊 Category Analysis Summary:", ""]

            # Top categories
            top_3 = category_totals.head(3)
            summary_lines.append("🏆 Top Spending Categories:")
            for i, (category, amount) in enumerate(top_3.items(), 1):
                percentage = (amount / total_spending) * 100
                summary_lines.append(f"  {i}. {category}: ₹{amount:,.0f} ({percentage:.1f}%)")

            summary_lines.append("")
            summary_lines.append(f"📈 Total Categories: {len(category_totals)}")
            summary_lines.append(f"💰 Average per Category: ₹{category_totals.mean():,.0f}")

            return "\n".join(summary_lines)

        except Exception as e:
            return f"Error generating category summary: {e}"

    def _generate_time_patterns(self):
        """Generate time-based spending patterns text"""
        try:
            if self.current_data.empty:
                return "No data available for time pattern analysis."

            # Ensure date column is datetime
            data = self.current_data.copy()
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                data['weekday'] = data['date'].dt.day_name()
                data['month'] = data['date'].dt.strftime('%B')

                summary_lines = ["📅 Time Pattern Analysis:", ""]

                # Weekday patterns
                weekday_totals = data.groupby('weekday')['amount'].sum().sort_values(ascending=False)
                summary_lines.append("📊 Spending by Day of Week:")
                for day, amount in weekday_totals.head(3).items():
                    summary_lines.append(f"  • {day}: ₹{amount:,.0f}")

                summary_lines.append("")

                # Monthly patterns
                if len(data['month'].unique()) > 1:
                    monthly_totals = data.groupby('month')['amount'].sum().sort_values(ascending=False)
                    summary_lines.append("📈 Spending by Month:")
                    for month, amount in monthly_totals.head(3).items():
                        summary_lines.append(f"  • {month}: ₹{amount:,.0f}")

                return "\n".join(summary_lines)
            else:
                return "Date information not available for pattern analysis."

        except Exception as e:
            return f"Error generating time patterns: {e}"

    def _generate_correlation_analysis(self):
        """Generate correlation analysis text"""
        try:
            if self.current_data.empty:
                return "No data available for correlation analysis."

            summary_lines = ["🔍 Correlation Analysis:", ""]

            # Amount vs frequency correlation
            category_stats = self.current_data.groupby('category').agg({
                'amount': ['sum', 'mean', 'count']
            }).round(2)

            category_stats.columns = ['total', 'avg_amount', 'frequency']
            category_stats = category_stats.sort_values('total', ascending=False)

            summary_lines.append("📊 Category Spending Patterns:")
            for category in category_stats.head(5).index:
                stats = category_stats.loc[category]
                summary_lines.append(f"  • {category}:")
                summary_lines.append(f"    Total: ₹{stats['total']:,.0f}")
                summary_lines.append(f"    Average: ₹{stats['avg_amount']:,.0f}")
                summary_lines.append(f"    Frequency: {stats['frequency']} transactions")
                summary_lines.append("")

            return "\n".join(summary_lines)

        except Exception as e:
            return f"Error generating correlation analysis: {e}"

    def _generate_advanced_insights(self):
        """Generate advanced insights text"""
        try:
            insights = get_expense_insights(self.current_data)
            if not insights:
                return "No advanced insights available."

            insight_lines = ["💡 Advanced Insights:", ""]
            for insight in insights[:5]:  # Show top 5 insights
                insight_lines.append(f"• {insight}")

            return "\n".join(insight_lines)

        except Exception as e:
            return f"Error generating advanced insights: {e}"

    def _generate_advanced_statistics(self):
        """Generate advanced statistics text"""
        try:
            if self.current_data.empty:
                return "No data available for statistical analysis."

            stats = calculate_expense_statistics(self.current_data)

            stats_lines = ["📈 Statistical Analysis:", ""]
            stats_lines.append(f"📊 Total Transactions: {stats.get('transaction_count', 0)}")
            stats_lines.append(f"💰 Total Amount: ₹{stats.get('total_expenses', 0):,.0f}")
            stats_lines.append(f"📈 Average Transaction: ₹{stats.get('average_expense', 0):,.0f}")
            stats_lines.append(f"📉 Median Transaction: ₹{self.current_data['amount'].median():,.0f}")
            stats_lines.append(f"📊 Standard Deviation: ₹{self.current_data['amount'].std():,.0f}")
            stats_lines.append("")
            stats_lines.append(f"🏆 Largest Transaction: ₹{stats.get('largest_expense', 0):,.0f}")
            stats_lines.append(f"🎯 Most Frequent Category: {stats.get('top_category', 'N/A')}")

            return "\n".join(stats_lines)

        except Exception as e:
            return f"Error generating advanced statistics: {e}"

    def update_theme(self, new_theme):
        """Update theme for all components"""
        self.current_theme = new_theme
        self.apply_theme_styling()

        # Update all chart widgets
        for widget in [self.interactive_dashboard, self.category_pie_chart,
                      self.category_bar_chart, self.time_series_chart,
                      self.time_heatmap, self.scatter_plot]:
            if hasattr(widget, 'current_theme'):
                widget.current_theme = new_theme
            if hasattr(widget, 'update_theme'):
                widget.update_theme(new_theme)

        # Update KPI cards
        kpi_cards = [
            'total_expenses_card', 'avg_daily_card', 'transaction_count_card',
            'top_category_card', 'largest_expense_card', 'spending_trend_card'
        ]

        for card_name in kpi_cards:
            if hasattr(self, card_name):
                card = getattr(self, card_name)
                if hasattr(card, 'apply_theme'):
                    card.apply_theme(new_theme)
                elif hasattr(card, 'theme'):
                    card.theme = new_theme
                    if hasattr(card, 'apply_theme_styling'):
                        card.apply_theme_styling()

        # Force update all widgets to apply new theme
        self.update()
        if hasattr(self, 'tab_widget'):
            self.tab_widget.update()
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    widget.update()
