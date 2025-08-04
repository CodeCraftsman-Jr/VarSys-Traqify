"""
Dashboard Widget Module
Main dashboard showing overview of all modules with enhanced visualizations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QScrollArea, QGroupBox, QProgressBar,
    QTabWidget, QSplitter, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette

import pandas as pd

from ..core.config import AppConfig
from ..core.data_manager import DataManager
from ..modules.expenses.visualization import (
    PieChartWidget, BarChartWidget, LineChartWidget, SummaryCardWidget,
    ExpenseDataProcessor
)
from ..modules.expenses.basic_charts import (
    BasicPieChartWidget, BasicBarChartWidget, BasicLineChartWidget, BasicDashboardWidget
)
from ..modules.expenses.advanced_analytics import AdvancedExpenseAnalyticsWidget
from ..modules.expenses.analytics_dashboard import ExpenseAnalyticsDashboard
from ..modules.expenses.models import ExpenseDataModel
from ..modules.income.analytics_dashboard import IncomeAnalyticsDashboard
from ..modules.income.models import IncomeDataModel
from ..modules.habits.analytics_dashboard import HabitAnalyticsDashboard
from ..modules.habits.models import HabitDataModel
from ..modules.attendance.analytics_dashboard import AttendanceAnalyticsDashboard
from ..modules.attendance.models import AttendanceDataModel
from ..modules.todo.analytics_dashboard import TodoAnalyticsDashboard
from ..modules.todos.models import TodoDataModel
from .smart_dashboard import SmartDashboardWidget


def get_theme_responsive_error_style():
    """Get theme-responsive error label style"""
    return """
    QLabel {
        font-weight: bold;
        font-size: 14px;
        color: #d32f2f;  /* Red that works on both light and dark */
        padding: 20px;
    }
    """


def get_theme_responsive_details_style():
    """Get theme-responsive details label style"""
    return """
    QLabel {
        font-size: 12px;
        padding: 20px;
        color: palette(text);  /* Use palette text color */
    }
    """


def get_theme_responsive_button_style():
    """Get theme-responsive button style"""
    return """
    QPushButton {
        padding: 10px;
        font-size: 12px;
    }
    """


def get_theme_responsive_placeholder_style():
    """Get theme-responsive placeholder text style"""
    return """
    QLabel {
        font-style: italic;
        padding: 20px;
        color: palette(text);  /* Use palette text color */
    }
    """


class StatCard(QFrame):
    """Statistics card widget for dashboard"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", parent=None):
        super().__init__(parent)

        self.setObjectName("statCard")
        # EXPANDED: Apply same sizing improvements as SummaryCardWidget
        self.setMinimumHeight(180)  # Increased from 120px to 180px
        self.setMinimumWidth(200)   # Set minimum width for better proportions
        # Remove maximum height constraint to allow natural expansion

        # Set size policy to expand and fill available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create layout with improved spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)  # More generous margins
        layout.setSpacing(8)  # Increased spacing for better visual hierarchy
        
        # Title - EXPANDED: Larger font and better spacing
        title_label = QLabel(title)
        title_label.setObjectName("statCardTitle")
        font = QFont()
        font.setPointSize(11)  # Increased from 10px to 11px
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)  # Enable word wrapping
        layout.addWidget(title_label)

        # Add spacing after title
        layout.addSpacing(8)

        # Value - EXPANDED: Much larger font for better visual hierarchy
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statCardValue")
        font = QFont()
        font.setPointSize(28)  # Increased from 24px to 28px
        font.setBold(True)
        self.value_label.setFont(font)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setWordWrap(True)  # Enable word wrapping for long values
        layout.addWidget(self.value_label)

        # Add spacing after value
        layout.addSpacing(5)
        
        # Subtitle - EXPANDED: Larger font and better spacing
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("statCardSubtitle")
            font = QFont()
            font.setPointSize(10)  # Increased from 9px to 10px
            subtitle_label.setFont(font)
            subtitle_label.setAlignment(Qt.AlignCenter)
            subtitle_label.setWordWrap(True)  # Enable word wrapping
            layout.addWidget(subtitle_label)

        # EXPANDED: More generous stretch for better proportions
        layout.addStretch(2)
    
    def update_value(self, value: str):
        """Update the card value"""
        self.value_label.setText(value)



class DashboardWidget(QWidget):
    """Main dashboard widget"""
    
    def __init__(self, data_manager: DataManager, config: AppConfig, parent=None):
        super().__init__(parent)

        self.data_manager = data_manager
        self.config = config

        # Get current theme from config
        self.current_theme = getattr(config, 'theme', 'dark')

        self.setup_ui()
        self.setup_refresh_timer()
        self.refresh_data()

    def update_theme(self, new_theme):
        """Update theme for dashboard and all child components"""
        self.current_theme = new_theme
        self.config.theme = new_theme

        # Update chart widgets if they exist
        if hasattr(self, 'category_chart') and hasattr(self.category_chart, 'apply_theme'):
            self.category_chart.apply_theme(new_theme)
        if hasattr(self, 'trends_chart') and hasattr(self.trends_chart, 'apply_theme'):
            self.trends_chart.apply_theme(new_theme)
        if hasattr(self, 'monthly_chart') and hasattr(self.monthly_chart, 'apply_theme'):
            self.monthly_chart.apply_theme(new_theme)

        # Update smart dashboard if it exists
        if hasattr(self, 'smart_dashboard') and hasattr(self.smart_dashboard, 'update_theme'):
            self.smart_dashboard.update_theme(new_theme)

        # CRITICAL FIX: Update expense analytics dashboard
        if hasattr(self, 'expense_analytics_dashboard') and hasattr(self.expense_analytics_dashboard, 'update_theme'):
            self.expense_analytics_dashboard.update_theme(new_theme)

        # CRITICAL FIX: Update basic dashboard widget (fixes black chart backgrounds)
        if hasattr(self, 'basic_dashboard') and hasattr(self.basic_dashboard, 'update_theme'):
            self.basic_dashboard.update_theme(new_theme)

        # Update income analytics dashboard (already handled in main window)
        # Update other analytics dashboards
        if hasattr(self, 'habit_analytics_dashboard') and hasattr(self.habit_analytics_dashboard, 'update_theme'):
            self.habit_analytics_dashboard.update_theme(new_theme)
        if hasattr(self, 'attendance_analytics_dashboard') and hasattr(self.attendance_analytics_dashboard, 'update_theme'):
            self.attendance_analytics_dashboard.update_theme(new_theme)
        if hasattr(self, 'todo_analytics_dashboard') and hasattr(self.todo_analytics_dashboard, 'update_theme'):
            self.todo_analytics_dashboard.update_theme(new_theme)

        # Force update the widget
        self.update()

    def setup_ui(self):
        """Setup the dashboard UI with organized sub-tabs"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Create header
        self.create_header(main_layout)

        # Create main tab widget for dashboard organization
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setObjectName("dashboardMainTabs")

        # Create sub-tabs
        self.create_smart_dashboard_tab()
        self.create_expense_tracker_tab()
        self.create_expense_analytics_tab()
        self.create_income_analytics_tab()
        self.create_habit_analytics_tab()
        self.create_attendance_analytics_tab()
        self.create_todo_analytics_tab()

        main_layout.addWidget(self.main_tab_widget)

    def create_smart_dashboard_tab(self):
        """Create smart dashboard with AI insights tab"""
        try:
            # Create smart dashboard widget
            self.smart_dashboard = SmartDashboardWidget(self.data_manager, self.config)
            self.main_tab_widget.addTab(self.smart_dashboard, "🤖 Smart Dashboard")

        except Exception as e:
            print(f"Error creating smart dashboard tab: {e}")
            import traceback
            traceback.print_exc()

            # Create a placeholder if smart dashboard fails
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)

            error_label = QLabel("Smart Dashboard - Error Details")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(get_theme_responsive_error_style())

            details_label = QLabel(f"Error: {str(e)}")
            details_label.setAlignment(Qt.AlignCenter)
            details_label.setWordWrap(True)
            details_label.setStyleSheet(get_theme_responsive_details_style())

            placeholder_layout.addWidget(error_label)
            placeholder_layout.addWidget(details_label)
            placeholder_layout.addStretch()

            self.main_tab_widget.addTab(placeholder_widget, "🤖 Smart Dashboard")

    def create_income_analytics_tab(self):
        """Create income analytics tab as a main tab"""
        try:
            # Create income model
            income_model = IncomeDataModel(self.data_manager)

            # Create income analytics dashboard
            self.income_analytics_dashboard = IncomeAnalyticsDashboard(income_model, self.config)

            self.main_tab_widget.addTab(self.income_analytics_dashboard, "📈 Income Analytics")

        except Exception as e:
            print(f"Error creating income analytics tab: {e}")
            import traceback
            traceback.print_exc()

            # Create a placeholder if analytics dashboard fails
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)

            error_label = QLabel("Income Analytics - Error Details")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(get_theme_responsive_error_style())

            details_label = QLabel(f"Error: {str(e)}")
            details_label.setAlignment(Qt.AlignCenter)
            details_label.setWordWrap(True)
            details_label.setStyleSheet(get_theme_responsive_details_style())

            retry_button = QPushButton("Retry Loading Analytics")
            retry_button.clicked.connect(self.retry_income_analytics)

            placeholder_layout.addWidget(error_label)
            placeholder_layout.addWidget(details_label)
            placeholder_layout.addWidget(retry_button)
            placeholder_layout.addStretch()

            self.main_tab_widget.addTab(placeholder_widget, "📈 Income Analytics")

    def retry_income_analytics(self):
        """Retry creating the income analytics dashboard"""
        # Find and remove the current analytics tab
        for i in range(self.main_tab_widget.count()):
            if "Income Analytics" in self.main_tab_widget.tabText(i):
                self.main_tab_widget.removeTab(i)
                break

        # Recreate the analytics tab
        self.create_income_analytics_tab()



    def create_habit_analytics_tab(self):
        """Create habit analytics tab as a main tab"""
        try:
            # Create habit model
            habit_model = HabitDataModel(self.data_manager)

            # Create habit analytics dashboard
            self.habit_analytics_dashboard = HabitAnalyticsDashboard(habit_model)

            self.main_tab_widget.addTab(self.habit_analytics_dashboard, "🎯 Habit Analytics")

        except Exception as e:
            print(f"Error creating habit analytics tab: {e}")
            import traceback
            traceback.print_exc()

            # Create a placeholder if analytics dashboard fails
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)

            error_label = QLabel("Habit Analytics - Error Details")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(get_theme_responsive_error_style())

            error_details = QLabel(f"Error: {str(e)}\n\nPlease check the console for more details.")
            error_details.setAlignment(Qt.AlignCenter)
            error_details.setWordWrap(True)
            error_details.setStyleSheet(get_theme_responsive_details_style())

            retry_button = QPushButton("🔄 Retry Habit Analytics")
            retry_button.clicked.connect(self.retry_habit_analytics)
            retry_button.setStyleSheet(get_theme_responsive_button_style())

            placeholder_layout.addStretch()
            placeholder_layout.addWidget(error_label)
            placeholder_layout.addWidget(error_details)
            placeholder_layout.addWidget(retry_button)
            placeholder_layout.addStretch()

            self.main_tab_widget.addTab(placeholder_widget, "🎯 Habit Analytics")

    def retry_habit_analytics(self):
        """Retry creating the habit analytics dashboard"""
        # Find and remove the current analytics tab
        for i in range(self.main_tab_widget.count()):
            if "Habit Analytics" in self.main_tab_widget.tabText(i):
                self.main_tab_widget.removeTab(i)
                break

        # Recreate the analytics tab
        self.create_habit_analytics_tab()

    def create_attendance_analytics_tab(self):
        """Create attendance analytics tab as a main tab"""
        try:
            # Create attendance model
            attendance_model = AttendanceDataModel(self.data_manager)

            # Create attendance analytics dashboard
            self.attendance_analytics_dashboard = AttendanceAnalyticsDashboard(attendance_model)

            self.main_tab_widget.addTab(self.attendance_analytics_dashboard, "📚 Attendance Analytics")

        except Exception as e:
            print(f"Error creating attendance analytics tab: {e}")
            import traceback
            traceback.print_exc()

            # Create a placeholder if analytics dashboard fails
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)

            error_label = QLabel("Attendance Analytics - Error Details")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(get_theme_responsive_error_style())

            error_details = QLabel(f"Error: {str(e)}\n\nPlease check the console for more details.")
            error_details.setAlignment(Qt.AlignCenter)
            error_details.setWordWrap(True)
            error_details.setStyleSheet(get_theme_responsive_details_style())

            retry_button = QPushButton("🔄 Retry Attendance Analytics")
            retry_button.clicked.connect(self.retry_attendance_analytics)
            retry_button.setStyleSheet(get_theme_responsive_button_style())

            placeholder_layout.addStretch()
            placeholder_layout.addWidget(error_label)
            placeholder_layout.addWidget(error_details)
            placeholder_layout.addWidget(retry_button)
            placeholder_layout.addStretch()

            self.main_tab_widget.addTab(placeholder_widget, "📚 Attendance Analytics")

    def retry_attendance_analytics(self):
        """Retry creating the attendance analytics dashboard"""
        # Find and remove the current analytics tab
        for i in range(self.main_tab_widget.count()):
            if "Attendance Analytics" in self.main_tab_widget.tabText(i):
                self.main_tab_widget.removeTab(i)
                break

        # Recreate the analytics tab
        self.create_attendance_analytics_tab()

    def create_todo_analytics_tab(self):
        """Create to-do analytics tab as a main tab"""
        try:
            # Create to-do model
            todo_model = TodoDataModel(self.data_manager)

            # Create to-do analytics dashboard
            self.todo_analytics_dashboard = TodoAnalyticsDashboard(todo_model)

            self.main_tab_widget.addTab(self.todo_analytics_dashboard, "📋 To-Do Analytics")

        except Exception as e:
            print(f"Error creating to-do analytics tab: {e}")
            import traceback
            traceback.print_exc()

            # Create a placeholder if analytics dashboard fails
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)

            error_label = QLabel("To-Do Analytics - Error Details")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(get_theme_responsive_error_style())

            error_details = QLabel(f"Error: {str(e)}\n\nPlease check the console for more details.")
            error_details.setAlignment(Qt.AlignCenter)
            error_details.setWordWrap(True)
            error_details.setStyleSheet(get_theme_responsive_details_style())

            retry_button = QPushButton("🔄 Retry To-Do Analytics")
            retry_button.clicked.connect(self.retry_todo_analytics)
            retry_button.setStyleSheet(get_theme_responsive_button_style())

            placeholder_layout.addStretch()
            placeholder_layout.addWidget(error_label)
            placeholder_layout.addWidget(error_details)
            placeholder_layout.addWidget(retry_button)
            placeholder_layout.addStretch()

            self.main_tab_widget.addTab(placeholder_widget, "📋 To-Do Analytics")

    def retry_todo_analytics(self):
        """Retry creating the to-do analytics dashboard"""
        # Find and remove the current analytics tab
        for i in range(self.main_tab_widget.count()):
            if "To-Do Analytics" in self.main_tab_widget.tabText(i):
                self.main_tab_widget.removeTab(i)
                break

        # Recreate the analytics tab
        self.create_todo_analytics_tab()

    def create_expense_tracker_tab(self):
        """Create expense tracker tab with sub-tabs for different views"""
        expense_widget = QWidget()
        expense_layout = QVBoxLayout(expense_widget)
        expense_layout.setContentsMargins(10, 10, 10, 10)

        # Create sub-tab widget for expense tracker
        expense_tab_widget = QTabWidget()
        expense_tab_widget.setObjectName("expenseTrackerTabs")

        # Create expense sub-tabs (existing)
        self.create_expense_summary_subtab(expense_tab_widget)
        self.create_expense_charts_subtab(expense_tab_widget)
        self.create_expense_trends_subtab(expense_tab_widget)
        self.create_expense_categories_subtab(expense_tab_widget)

        # Create new basic chart sub-tabs
        self.create_basic_pie_subtab(expense_tab_widget)
        self.create_basic_bar_subtab(expense_tab_widget)
        self.create_basic_line_subtab(expense_tab_widget)
        self.create_basic_dashboard_subtab(expense_tab_widget)

        # Create advanced analytics sub-tab
        self.create_advanced_analytics_subtab(expense_tab_widget)

        expense_layout.addWidget(expense_tab_widget)
        self.main_tab_widget.addTab(expense_widget, "💰 Expense Tracker")

    def create_expense_analytics_tab(self):
        """Create expense analytics tab as a main tab"""
        try:
            # Create expense model
            expense_model = ExpenseDataModel(self.data_manager)

            # Create expense analytics dashboard
            self.expense_analytics_dashboard = ExpenseAnalyticsDashboard(expense_model, self.config)

            # CRITICAL FIX: Ensure theme is applied after dashboard creation
            if hasattr(self.expense_analytics_dashboard, 'update_theme'):
                self.expense_analytics_dashboard.update_theme(self.config.theme)

            self.main_tab_widget.addTab(self.expense_analytics_dashboard, "📊 Expense Analytics")

        except Exception as e:
            print(f"Error creating expense analytics dashboard: {e}")
            import traceback
            traceback.print_exc()

            # Create placeholder tab
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)

            error_label = QLabel("❌ Expense Analytics Dashboard Error")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 16px; font-weight: bold;")
            placeholder_layout.addWidget(error_label)

            error_details = QLabel(f"Error: {str(e)}")
            error_details.setAlignment(Qt.AlignCenter)
            error_details.setWordWrap(True)
            placeholder_layout.addWidget(error_details)

            retry_button = QPushButton("🔄 Retry")
            retry_button.clicked.connect(self.retry_expense_analytics)
            placeholder_layout.addWidget(retry_button)

            placeholder_layout.addStretch()

            self.main_tab_widget.addTab(placeholder_widget, "📊 Expense Analytics")

    def retry_expense_analytics(self):
        """Retry creating the expense analytics dashboard"""
        # Find and remove the current analytics tab
        for i in range(self.main_tab_widget.count()):
            if "Expense Analytics" in self.main_tab_widget.tabText(i):
                self.main_tab_widget.removeTab(i)
                break

        # Recreate the analytics tab
        self.create_expense_analytics_tab()

    def create_expense_summary_subtab(self, parent_tab_widget):
        """Create expense summary sub-tab"""
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        summary_layout.setSpacing(15)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add expense summary cards
        self.create_expense_summary_cards(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        summary_layout.addWidget(scroll_area)

        parent_tab_widget.addTab(summary_widget, "📋 Summary")

    def create_expense_charts_subtab(self, parent_tab_widget):
        """Create expense charts sub-tab"""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(10, 10, 10, 10)
        charts_layout.setSpacing(15)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add expense charts
        self.create_expense_charts_section(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        charts_layout.addWidget(scroll_area)

        parent_tab_widget.addTab(charts_widget, "📊 Charts")

    def create_expense_trends_subtab(self, parent_tab_widget):
        """Create expense trends sub-tab"""
        trends_widget = QWidget()
        trends_layout = QVBoxLayout(trends_widget)
        trends_layout.setContentsMargins(10, 10, 10, 10)
        trends_layout.setSpacing(15)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add expense trends
        self.create_expense_trends_section(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        trends_layout.addWidget(scroll_area)

        parent_tab_widget.addTab(trends_widget, "📈 Trends")

    def create_expense_categories_subtab(self, parent_tab_widget):
        """Create expense categories sub-tab"""
        categories_widget = QWidget()
        categories_layout = QVBoxLayout(categories_widget)
        categories_layout.setContentsMargins(10, 10, 10, 10)
        categories_layout.setSpacing(15)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Add category breakdown
        self.create_expense_categories_section(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        categories_layout.addWidget(scroll_area)

        parent_tab_widget.addTab(categories_widget, "📂 Categories")

    def create_basic_pie_subtab(self, parent_tab_widget):
        """Create basic pie chart sub-tab"""
        pie_widget = QWidget()
        pie_layout = QVBoxLayout(pie_widget)
        pie_layout.setContentsMargins(10, 10, 10, 10)

        # Create basic pie chart
        self.basic_pie_chart = BasicPieChartWidget(theme=self.current_theme)
        pie_layout.addWidget(self.basic_pie_chart)

        parent_tab_widget.addTab(pie_widget, "🥧 Pie Chart")

    def create_basic_bar_subtab(self, parent_tab_widget):
        """Create basic bar chart sub-tab"""
        bar_widget = QWidget()
        bar_layout = QVBoxLayout(bar_widget)
        bar_layout.setContentsMargins(10, 10, 10, 10)

        # Create basic bar chart
        self.basic_bar_chart = BasicBarChartWidget(theme=self.current_theme)
        bar_layout.addWidget(self.basic_bar_chart)

        parent_tab_widget.addTab(bar_widget, "📊 Bar Chart")

    def create_basic_line_subtab(self, parent_tab_widget):
        """Create basic line chart sub-tab"""
        line_widget = QWidget()
        line_layout = QVBoxLayout(line_widget)
        line_layout.setContentsMargins(10, 10, 10, 10)

        # Create basic line chart
        self.basic_line_chart = BasicLineChartWidget(theme=self.current_theme)
        line_layout.addWidget(self.basic_line_chart)

        parent_tab_widget.addTab(line_widget, "📈 Line Chart")

    def create_basic_dashboard_subtab(self, parent_tab_widget):
        """Create basic dashboard sub-tab"""
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_layout.setContentsMargins(10, 10, 10, 10)

        # Create basic dashboard - CRITICAL FIX: Pass theme to fix black backgrounds
        self.basic_dashboard = BasicDashboardWidget(theme=self.current_theme)
        dashboard_layout.addWidget(self.basic_dashboard)

        parent_tab_widget.addTab(dashboard_widget, "🎯 Dashboard")

    def create_advanced_analytics_subtab(self, parent_tab_widget):
        """Create advanced analytics sub-tab"""
        try:
            analytics_widget = QWidget()
            analytics_layout = QVBoxLayout(analytics_widget)
            analytics_layout.setContentsMargins(10, 10, 10, 10)

            # Create advanced analytics widget
            self.advanced_analytics = AdvancedExpenseAnalyticsWidget()
            analytics_layout.addWidget(self.advanced_analytics)

            parent_tab_widget.addTab(analytics_widget, "🔬 Advanced Analytics")

            # Update with current data
            self.update_advanced_analytics()

        except Exception as e:
            print(f"Error creating advanced analytics subtab: {e}")
            import traceback
            traceback.print_exc()

    def update_advanced_analytics(self):
        """Update advanced analytics with current expense data"""
        try:
            if hasattr(self, 'advanced_analytics'):
                # Get expense data
                expense_data = self.get_expense_data()

                # Sample budget data (in a real implementation, this would come from budget module)
                sample_budget = {
                    'Food': 15000,
                    'Transportation': 5000,
                    'Entertainment': 3000,
                    'Shopping': 8000,
                    'Bills': 10000
                }

                # Update analytics
                self.advanced_analytics.update_analysis(expense_data, sample_budget)
        except Exception as e:
            print(f"Error updating advanced analytics: {e}")

    def create_header(self, layout):
        """Create dashboard header"""
        header_frame = QFrame()
        header_frame.setObjectName("dashboardHeader")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Welcome message
        welcome_label = QLabel("Welcome to Your Personal Finance Dashboard")
        welcome_label.setObjectName("dashboardWelcome")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        welcome_label.setFont(font)
        header_layout.addWidget(welcome_label)

        header_layout.addStretch()

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.clicked.connect(self.refresh_dashboard)
        header_layout.addWidget(self.refresh_button)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("refreshButton")
        refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_button)
        
        layout.addWidget(header_frame)

    def create_expense_summary_cards(self, layout):
        """Create expense summary cards section"""
        # Section title
        title_label = QLabel("Expense Summary")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Create summary cards grid
        cards_frame = QFrame()
        cards_layout = QGridLayout(cards_frame)
        cards_layout.setSpacing(15)

        # Initialize summary cards
        self.summary_cards = {}

        # Total Expenses Card
        self.summary_cards['total_expenses'] = SummaryCardWidget(
            "Total Expenses", "₹0", "This Month", "💰", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['total_expenses'], 0, 0)

        # Average Daily Spending
        self.summary_cards['avg_daily'] = SummaryCardWidget(
            "Daily Average", "₹0", "Last 30 Days", "📊", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['avg_daily'], 0, 1)

        # Most Expensive Category
        self.summary_cards['top_category'] = SummaryCardWidget(
            "Top Category", "N/A", "Highest Spending", "🏆", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['top_category'], 0, 2)

        # Transaction Count
        self.summary_cards['transaction_count'] = SummaryCardWidget(
            "Transactions", "0", "This Month", "🔢", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['transaction_count'], 1, 0)

        # Spending Trend
        self.summary_cards['spending_trend'] = SummaryCardWidget(
            "Trend", "0%", "vs Last Month", "📈", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['spending_trend'], 1, 1)

        # Budget Status
        self.summary_cards['budget_status'] = SummaryCardWidget(
            "Budget", "N/A", "Monthly Status", "🎯", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['budget_status'], 1, 2)

        layout.addWidget(cards_frame)

    def create_expense_charts_section(self, layout):
        """Create expense charts section"""
        # Section title
        title_label = QLabel("Expense Charts")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Create charts container - EXPANDED: Better sizing and layout
        charts_splitter = QSplitter(Qt.Horizontal)
        charts_splitter.setMinimumHeight(450)  # Ensure adequate height for chart visibility

        # Category pie chart - EXPANDED: Responsive sizing
        self.category_pie_chart = PieChartWidget(theme=self.current_theme)
        self.category_pie_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.category_pie_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_splitter.addWidget(self.category_pie_chart)

        # Monthly bar chart - EXPANDED: Responsive sizing
        self.monthly_bar_chart = BarChartWidget(theme=self.current_theme)
        self.monthly_bar_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.monthly_bar_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_splitter.addWidget(self.monthly_bar_chart)

        # Set equal proportions with larger sizes
        charts_splitter.setSizes([500, 500])  # Increased from 400 to 500

        layout.addWidget(charts_splitter)

    def create_expense_trends_section(self, layout):
        """Create expense trends section"""
        # Section title
        title_label = QLabel("Expense Trends")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Create trends chart
        self.trends_line_chart = LineChartWidget(theme=self.current_theme)
        layout.addWidget(self.trends_line_chart)

    def create_expense_categories_section(self, layout):
        """Create expense categories breakdown section"""
        # Section title
        title_label = QLabel("Category Breakdown")
        title_label.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Create category breakdown widget
        categories_frame = QFrame()
        categories_frame.setObjectName("categoriesFrame")
        categories_layout = QVBoxLayout(categories_frame)

        # Add category breakdown content here
        # This will be populated with actual category data
        self.categories_content_label = QLabel("Category breakdown will be displayed here based on your expense data.")
        self.categories_content_label.setAlignment(Qt.AlignCenter)
        self.categories_content_label.setStyleSheet(get_theme_responsive_placeholder_style())
        categories_layout.addWidget(self.categories_content_label)

        layout.addWidget(categories_frame)

    def create_enhanced_statistics_section(self, layout):
        """Create enhanced statistics cards section with summary metrics"""
        # Section title
        stats_title = QLabel("Financial Overview")
        stats_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        stats_title.setFont(font)
        layout.addWidget(stats_title)

        # Statistics grid with enhanced cards - EXPANDED: Better spacing and layout
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_frame.setMinimumHeight(200)  # Ensure adequate height for expanded cards
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(25)  # Increased spacing between cards
        stats_layout.setContentsMargins(20, 20, 20, 20)  # More generous margins

        # Create enhanced summary cards
        self.summary_cards = {}

        # Total Expenses Card
        self.summary_cards['total_expenses'] = SummaryCardWidget(
            "Total Expenses", "₹0", "This Month", "💸", theme=self.current_theme
        )
        stats_layout.addWidget(self.summary_cards['total_expenses'], 0, 0)

        # Average Daily Spending
        self.summary_cards['avg_daily'] = SummaryCardWidget(
            "Daily Average", "₹0", "Last 30 Days", "📊", theme=self.current_theme
        )
        stats_layout.addWidget(self.summary_cards['avg_daily'], 0, 1)

        # Most Expensive Category
        self.summary_cards['top_category'] = SummaryCardWidget(
            "Top Category", "N/A", "Highest Spending", "🏆", theme=self.current_theme
        )
        stats_layout.addWidget(self.summary_cards['top_category'], 0, 2)

        # Transaction Count
        self.summary_cards['transaction_count'] = SummaryCardWidget(
            "Transactions", "0", "This Month", "🔢", theme=self.current_theme
        )
        stats_layout.addWidget(self.summary_cards['transaction_count'], 1, 0)

        # Spending Trend
        self.summary_cards['spending_trend'] = SummaryCardWidget(
            "Trend", "0%", "vs Last Month", "📈", theme=self.current_theme
        )
        stats_layout.addWidget(self.summary_cards['spending_trend'], 1, 1)

        # Budget Status
        self.summary_cards['budget_status'] = SummaryCardWidget(
            "Budget", "N/A", "Monthly Status", "🎯", theme=self.current_theme
        )
        stats_layout.addWidget(self.summary_cards['budget_status'], 1, 2)

        layout.addWidget(stats_frame)

    def create_visualization_section(self, layout):
        """Create visualization section with charts"""
        # Section title
        viz_title = QLabel("Expense Analytics")
        viz_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        viz_title.setFont(font)
        layout.addWidget(viz_title)

        # Create tab widget for different chart views - EXPANDED: Better sizing
        self.chart_tabs = QTabWidget()
        self.chart_tabs.setMinimumHeight(450)  # Increased minimum height for better chart visibility
        # Remove maximum height constraint to allow natural expansion

        # Category Distribution Tab - EXPANDED: Responsive sizing
        self.category_chart = PieChartWidget(theme=self.current_theme)
        self.category_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.category_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chart_tabs.addTab(self.category_chart, "Category Distribution")

        # Spending Trends Tab - EXPANDED: Responsive sizing
        self.trends_chart = LineChartWidget(theme=self.current_theme)
        self.trends_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.trends_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chart_tabs.addTab(self.trends_chart, "Spending Trends")

        # Monthly Comparison Tab
        self.monthly_chart = BarChartWidget(theme=self.current_theme)
        self.chart_tabs.addTab(self.monthly_chart, "Monthly Analysis")

        layout.addWidget(self.chart_tabs)

    def create_statistics_section(self, layout):
        """Create statistics cards section"""
        # Section title
        stats_title = QLabel("Overview")
        stats_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        stats_title.setFont(font)
        layout.addWidget(stats_title)
        
        # Statistics grid - EXPANDED: Better spacing and layout
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_frame.setMinimumHeight(200)  # Ensure adequate height for expanded cards
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(25)  # Increased spacing between cards
        stats_layout.setContentsMargins(20, 20, 20, 20)  # More generous margins
        
        # Create stat cards
        self.stat_cards = {}
        
        # Total Expenses
        self.stat_cards['expenses'] = StatCard(
            "Total Expenses", "₹0", "This Month"
        )
        stats_layout.addWidget(self.stat_cards['expenses'], 0, 0)
        
        # Total Income
        self.stat_cards['income'] = StatCard(
            "Total Income", "₹0", "This Month"
        )
        stats_layout.addWidget(self.stat_cards['income'], 0, 1)
        
        # Savings
        self.stat_cards['savings'] = StatCard(
            "Savings", "₹0", "This Month"
        )
        stats_layout.addWidget(self.stat_cards['savings'], 0, 2)
        
        # Habits Completed
        self.stat_cards['habits'] = StatCard(
            "Habits", "0%", "Completion Rate"
        )
        stats_layout.addWidget(self.stat_cards['habits'], 1, 0)
        
        # Attendance
        self.stat_cards['attendance'] = StatCard(
            "Attendance", "0%", "Current Semester"
        )
        stats_layout.addWidget(self.stat_cards['attendance'], 1, 1)
        
        # Active Tasks
        self.stat_cards['tasks'] = StatCard(
            "Active Tasks", "0", "Pending"
        )
        stats_layout.addWidget(self.stat_cards['tasks'], 1, 2)
        
        layout.addWidget(stats_frame)
    

    
    def create_recent_activity_section(self, layout):
        """Create recent activity section"""
        # Section title
        activity_title = QLabel("Recent Activity")
        activity_title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        activity_title.setFont(font)
        layout.addWidget(activity_title)
        
        # Activity frame
        activity_frame = QFrame()
        activity_frame.setObjectName("activityFrame")
        activity_frame.setMinimumHeight(200)
        
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(15, 15, 15, 15)
        
        # Placeholder for recent activity
        self.activity_label = QLabel("No recent activity")
        self.activity_label.setAlignment(Qt.AlignCenter)
        activity_layout.addWidget(self.activity_label)
        
        layout.addWidget(activity_frame)
    
    def setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def refresh_data(self):
        """Refresh dashboard data with enhanced visualizations"""
        try:
            # Get expense data for visualizations
            expense_data = self.get_expense_data()

            # Update summary cards with enhanced metrics
            self.update_summary_cards(expense_data)

            # Update expense tracker charts
            self.update_expense_charts(expense_data)

            # Update legacy stat cards if they exist
            self.update_legacy_stat_cards()

            # Update advanced analytics
            self.update_advanced_analytics()

            # Update activity
            if hasattr(self, 'activity_label'):
                self.activity_label.setText("Dashboard refreshed successfully with visualizations")

        except Exception as e:
            print(f"Error refreshing dashboard data: {e}")
            import traceback
            traceback.print_exc()
            # Set default values to prevent crashes
            if hasattr(self, 'summary_cards'):
                for card in self.summary_cards.values():
                    card.update_values("0", "No data")

    def update_expense_charts(self, expense_data):
        """Update expense tracker charts"""
        try:
            # Use more lenient validation - just check if we have basic data
            if expense_data.empty:
                # Clear charts if no data
                if hasattr(self, 'category_pie_chart'):
                    self.category_pie_chart.clear_chart()
                if hasattr(self, 'monthly_bar_chart'):
                    self.monthly_bar_chart.clear_chart()
                if hasattr(self, 'trends_line_chart'):
                    self.trends_line_chart.clear_chart()
                return

            # Basic validation - just ensure we have required columns
            required_columns = ['date', 'amount', 'category']
            if not all(col in expense_data.columns for col in required_columns):
                print(f"Missing required columns for charts: {required_columns}")
                return

            # Update category pie chart
            if hasattr(self, 'category_pie_chart'):
                self.category_pie_chart.update_chart(
                    expense_data,
                    value_column='amount',
                    label_column='category',
                    title="Expense Distribution by Category"
                )

            # Update monthly bar chart
            if hasattr(self, 'monthly_bar_chart'):
                # Group by month for monthly comparison
                expense_data_copy = expense_data.copy()
                expense_data_copy['month'] = expense_data_copy['date'].dt.strftime('%Y-%m')
                monthly_data = expense_data_copy.groupby('month')['amount'].sum().reset_index()

                self.monthly_bar_chart.update_chart(
                    monthly_data,
                    x_column='month',
                    y_column='amount',
                    title="Monthly Expense Comparison",
                    x_label="Month",
                    y_label="Total Expenses (₹)"
                )

            # Update trends line chart
            if hasattr(self, 'trends_line_chart'):
                self.trends_line_chart.update_chart(
                    expense_data,
                    date_column='date',
                    value_column='amount',
                    title="Daily Expense Trends",
                    aggregation='daily'
                )

            # Update new interactive charts
            self.update_interactive_charts(expense_data)

        except Exception as e:
            print(f"Error updating expense charts: {e}")

    def update_interactive_charts(self, expense_data):
        """Update all interactive charts with new data"""
        try:
            # Use a more lenient validation for interactive charts
            if expense_data.empty:
                # Clear basic charts if no data
                if hasattr(self, 'basic_pie_chart'):
                    self.basic_pie_chart.clear_chart()
                if hasattr(self, 'basic_bar_chart'):
                    self.basic_bar_chart.clear_chart()
                if hasattr(self, 'basic_line_chart'):
                    self.basic_line_chart.clear_chart()
                if hasattr(self, 'basic_dashboard'):
                    self.basic_dashboard.clear_dashboard()
                return

            # Check if we have basic required columns for charts
            required_columns = ['date', 'amount', 'category']
            if not all(col in expense_data.columns for col in required_columns):
                return

            # Use all data - don't filter out anything except completely invalid records
            valid_data = expense_data.copy()

            # Only filter out records with zero or negative amounts
            valid_data = valid_data[valid_data['amount'] > 0]

            # Fill any NaN categories with 'Uncategorized'
            valid_data['category'] = valid_data['category'].fillna('Uncategorized')
            valid_data['sub_category'] = valid_data['sub_category'].fillna('General')

            if valid_data.empty:
                return

            # Update basic pie chart
            if hasattr(self, 'basic_pie_chart'):
                self.basic_pie_chart.update_chart(
                    valid_data,
                    title="Expense Distribution by Category"
                )

            # Update basic bar chart
            if hasattr(self, 'basic_bar_chart'):
                self.basic_bar_chart.update_chart(
                    valid_data,
                    title="Top Expense Categories"
                )

            # Update basic line chart
            if hasattr(self, 'basic_line_chart'):
                self.basic_line_chart.update_chart(
                    valid_data,
                    title="Daily Expense Trends"
                )

            # Update basic dashboard
            if hasattr(self, 'basic_dashboard'):
                self.basic_dashboard.update_dashboard(valid_data)

        except Exception as e:
            print(f"Error updating interactive charts: {e}")

            if hasattr(self, 'stat_cards'):
                for key in self.stat_cards:
                    if key == 'expenses' or key == 'income' or key == 'savings':
                        self.stat_cards[key].update_value("₹0")
                    elif key == 'habits' or key == 'attendance':
                        self.stat_cards[key].update_value("0%")
                    else:
                        self.stat_cards[key].update_value("0")

            self.activity_label.setText(f"Error refreshing data: {e}")

    def get_expense_data(self):
        """Get expense data for visualizations"""
        try:
            # Import here to avoid circular imports
            from ..modules.expenses.models import ExpenseDataModel
            expense_model = ExpenseDataModel(self.data_manager)

            # Get all expenses for visualization
            all_expenses = expense_model.get_all_expenses()

            # If no data, return empty DataFrame
            if all_expenses is None or all_expenses.empty:
                return pd.DataFrame()

            return all_expenses
        except Exception as e:
            print(f"Error getting expense data: {e}")
            return pd.DataFrame()

    def update_summary_cards(self, expense_data):
        """Update summary cards with expense metrics and proper validation"""
        if not hasattr(self, 'summary_cards'):
            return

        # Check if we have valid transaction data
        if expense_data.empty or not self._has_valid_transaction_data(expense_data):
            # Set default values if no valid data
            for card in self.summary_cards.values():
                card.update_values("0", "No data")
            return

        # Calculate summary metrics
        metrics = ExpenseDataProcessor.calculate_summary_metrics(expense_data)

        # Calculate spending trends
        trends = ExpenseDataProcessor.get_spending_trends(expense_data)

        # Update cards with real data
        self.summary_cards['total_expenses'].update_values(
            f"₹{metrics['total_amount']:.0f}",
            "This Month"
        )

        # Average daily spending
        if metrics['transaction_count'] > 0:
            avg_daily = metrics['total_amount'] / 30  # Simplified for 30 days
            self.summary_cards['avg_daily'].update_values(
                f"₹{avg_daily:.0f}",
                "Last 30 Days"
            )

        # Top spending category
        self.summary_cards['top_category'].update_values(
            f"{metrics['most_expensive_category']}",
            "Highest Spending"
        )

        # Transaction count
        self.summary_cards['transaction_count'].update_values(
            f"{metrics['transaction_count']}",
            "This Month"
        )

        # Spending trend
        change_text = f"{abs(trends['change_percent']):.1f}%"
        if trends['change_percent'] > 0:
            trend_text = f"↑ {change_text}"
        elif trends['change_percent'] < 0:
            trend_text = f"↓ {change_text}"
        else:
            trend_text = f"→ {change_text}"

        self.summary_cards['spending_trend'].update_values(
            trend_text,
            "vs Last Month"
        )
        self.summary_cards['spending_trend'].set_trend_color(trends['trend'])

        # Budget status (replace categories count)
        if 'budget_status' in self.summary_cards:
            self.summary_cards['budget_status'].update_values(
                "On Track",
                "Monthly Status"
            )


    def update_legacy_stat_cards(self):
        """Update legacy stat cards for backward compatibility"""
        if not hasattr(self, 'stat_cards'):
            return

        try:
            # Get expense summary
            expense_summary = self.get_module_summary("expenses")

            # Update stat cards with real data
            if expense_summary:
                self.stat_cards['expenses'].update_value(f"₹{expense_summary.get('total_amount', 0):.0f}")
            else:
                self.stat_cards['expenses'].update_value("₹0")

            # Get income summary
            income_summary = self.get_module_summary("income")

            if income_summary:
                self.stat_cards['income'].update_value(f"₹{income_summary.get('total_earned', 0):.0f}")
                # Calculate savings (income - expenses)
                total_income = income_summary.get('total_earned', 0)
                total_expenses = expense_summary.get('total_amount', 0) if expense_summary else 0
                savings = total_income - total_expenses
                self.stat_cards['savings'].update_value(f"₹{savings:.0f}")
            else:
                self.stat_cards['income'].update_value("₹0")
                self.stat_cards['savings'].update_value("₹0")

            # Get habit summary
            habit_summary = self.get_module_summary("habits")

            if habit_summary:
                self.stat_cards['habits'].update_value(f"{habit_summary.get('today_completion_rate', 0):.0f}%")
            else:
                self.stat_cards['habits'].update_value("0%")

            # Get attendance summary
            attendance_summary = self.get_module_summary("attendance")

            if attendance_summary:
                self.stat_cards['attendance'].update_value(f"{attendance_summary.get('overall_percentage', 0):.0f}%")
            else:
                self.stat_cards['attendance'].update_value("0%")

            # Placeholder data for other modules
            self.stat_cards['tasks'].update_value("5")

        except Exception as e:
            print(f"Error updating legacy stat cards: {e}")
    
    def get_module_summary(self, module: str):
        """Get summary data for a specific module"""
        try:
            if module == "expenses":
                # Import here to avoid circular imports
                from ..modules.expenses.models import ExpenseDataModel
                expense_model = ExpenseDataModel(self.data_manager)
                return expense_model.get_expense_summary()
            elif module == "income":
                # Import here to avoid circular imports
                from ..modules.income.models import IncomeDataModel
                income_model = IncomeDataModel(self.data_manager)
                return income_model.get_income_summary()
            elif module == "habits":
                # Import here to avoid circular imports
                from ..modules.habits.models import HabitDataModel
                habit_model = HabitDataModel(self.data_manager)
                return habit_model.get_habit_summary()
            elif module == "attendance":
                # Import simplified attendance model to avoid recursion
                from ..modules.attendance.simple_models import SimpleAttendanceDataManager
                attendance_model = SimpleAttendanceDataManager(str(self.data_manager.data_dir))
                return attendance_model.get_summary()

            return self.data_manager.get_module_summary(module)
        except Exception as e:
            print(f"Error getting summary for module {module}: {e}")
            # Return empty summary to prevent crashes
            return {}

    def refresh_dashboard(self):
        """Refresh dashboard with latest data from all modules"""
        try:
            # Update financial overview with real data
            self.update_financial_overview()

            # Update recent activity
            self.update_recent_activity()

            # Update module summaries
            self.update_module_summaries()

        except Exception as e:
            print(f"Error refreshing dashboard: {e}")

    def update_financial_overview(self):
        """Update financial overview with real data"""
        try:
            total_income = 0.0
            total_expenses = 0.0
            total_investments = 0.0

            # Get expense data
            try:
                expense_df = self.data_manager.read_csv('expenses', 'expenses.csv',
                                                      ['id', 'amount', 'category', 'description', 'date'])
                if not expense_df.empty:
                    total_expenses = expense_df['amount'].sum()
            except:
                pass

            # Get income data
            try:
                income_df = self.data_manager.read_csv('income', 'income_records.csv',
                                                     ['id', 'amount', 'source', 'description', 'date'])
                if not income_df.empty:
                    total_income = income_df['amount'].sum()
            except:
                pass

            # Get investment data
            try:
                investment_df = self.data_manager.read_csv('investments', 'investments.csv',
                                                         ['id', 'current_value', 'total_investment'])
                if not investment_df.empty:
                    total_investments = investment_df['current_value'].sum()
            except:
                pass

            # Calculate savings
            total_savings = total_income - total_expenses

            # Update stat cards
            if hasattr(self, 'stat_cards'):
                self.stat_cards['expenses'].update_value(f"₹{total_expenses:,.2f}")
                self.stat_cards['income'].update_value(f"₹{total_income:,.2f}")
                self.stat_cards['savings'].update_value(f"₹{total_savings:,.2f}")
                if 'investments' in self.stat_cards:
                    self.stat_cards['investments'].update_value(f"₹{total_investments:,.2f}")

        except Exception as e:
            print(f"Error updating financial overview: {e}")

    def update_recent_activity(self):
        """Update recent activity section"""
        try:
            recent_items = []

            # Get recent expenses
            try:
                expense_df = self.data_manager.read_csv('expenses', 'expenses.csv',
                                                      ['id', 'amount', 'category', 'description', 'date'])
                if not expense_df.empty:
                    recent_expenses = expense_df.tail(3)
                    for _, row in recent_expenses.iterrows():
                        recent_items.append(f"💸 {row['description']} - ₹{row['amount']:.2f}")
            except:
                pass

            # Get recent income
            try:
                income_df = self.data_manager.read_csv('income', 'income_records.csv',
                                                     ['id', 'amount', 'source', 'description', 'date'])
                if not income_df.empty:
                    recent_income = income_df.tail(2)
                    for _, row in recent_income.iterrows():
                        recent_items.append(f"💰 {row['description']} - ₹{row['amount']:.2f}")
            except:
                pass

            # Get recent todos
            try:
                todos_df = self.data_manager.read_csv('todos', 'todo_items.csv',
                                                    ['id', 'title', 'status'])
                if not todos_df.empty:
                    recent_todos = todos_df[todos_df['status'] == 'Completed'].tail(2)
                    for _, row in recent_todos.iterrows():
                        recent_items.append(f"✅ Completed: {row['title']}")
            except:
                pass

            # Update recent activity display if it exists
            if hasattr(self, 'recent_activity_list') and recent_items:
                # Clear existing items
                for i in reversed(range(self.recent_activity_list.count())):
                    self.recent_activity_list.takeItem(i)

                # Add new items
                for item in recent_items[-5:]:  # Show last 5 items
                    self.recent_activity_list.addItem(item)

        except Exception as e:
            print(f"Error updating recent activity: {e}")

    def update_module_summaries(self):
        """Update module summary cards"""
        try:
            modules = ['expenses', 'income', 'habits', 'todos', 'investments', 'budget']

            for module in modules:
                try:
                    summary = self.get_module_summary(module)
                    # Update module-specific displays based on summary data
                    # This would be expanded based on specific module summary formats
                except Exception as e:
                    print(f"Error updating summary for {module}: {e}")

        except Exception as e:
            print(f"Error updating module summaries: {e}")

    def _has_valid_transaction_data(self, df):
        """Check if DataFrame contains valid transaction data (excluding sample/test data)"""
        if df.empty:
            return False

        # Check if we have required columns
        required_columns = ['type', 'amount', 'category']
        if not all(col in df.columns for col in required_columns):
            return False

        # Filter out sample/test data
        real_data = self._filter_out_sample_data(df)
        if real_data.empty:
            return False

        # Check if we have valid transaction types
        valid_types = ['Income', 'Credit', 'Expense', 'Debit']
        if 'type' in real_data.columns:
            valid_type_data = real_data[real_data['type'].isin(valid_types)]
            if valid_type_data.empty:
                return False

        # Check if we have valid amounts (greater than 0)
        if 'amount' in real_data.columns:
            valid_amounts = real_data[real_data['amount'] > 0]
            if valid_amounts.empty:
                return False

        # Check if we have valid categories (not empty)
        if 'category' in real_data.columns:
            valid_categories = real_data[real_data['category'].str.strip() != '']
            if valid_categories.empty:
                return False

        return True

    def _filter_out_sample_data(self, df):
        """Filter out sample/test data to only include real transactions"""
        if df.empty:
            return df

        # Create a copy to avoid modifying the original
        filtered_df = df.copy()

        # Identify sample data patterns
        sample_patterns = [
            'Sample expense',
            'Sample income',
            'Test expense',
            'Test income',
            'Sample transaction',
            'Test transaction'
        ]

        # Check notes column for sample patterns
        if 'notes' in filtered_df.columns:
            for pattern in sample_patterns:
                filtered_df = filtered_df[~filtered_df['notes'].str.contains(pattern, case=False, na=False)]

        # Check for generic subcategory patterns that indicate sample data
        if 'sub_category' in filtered_df.columns:
            sample_subcategory_patterns = [
                r'.*_sub_\d+$',  # Patterns like "Shopping_sub_3", "Entertainment_sub_1"
                r'^General$',
                r'^Test.*',
                r'^Sample.*'
            ]

            for pattern in sample_subcategory_patterns:
                filtered_df = filtered_df[~filtered_df['sub_category'].str.match(pattern, case=False, na=False)]

        # If we have very few records (less than 10% of original or less than 100),
        # and they all look like sample data, consider it invalid
        if len(filtered_df) < max(10, len(df) * 0.1):
            # Additional check: if all remaining records have very similar amounts or patterns
            if not filtered_df.empty and 'amount' in filtered_df.columns:
                # Check if amounts are suspiciously uniform (common in sample data)
                amount_variance = filtered_df['amount'].var()
                amount_mean = filtered_df['amount'].mean()

                # If variance is very low relative to mean, it might be sample data
                if amount_mean > 0 and (amount_variance / amount_mean) < 0.1:
                    return pd.DataFrame()  # Return empty - likely all sample data

        return filtered_df
