"""
Income Analytics Dashboard Module
Provides comprehensive analytics dashboard for income data with KPIs, charts, and insights
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
from PySide6.QtGui import QFont, QPalette

from .visualization import (
    SummaryCardWidget, IncomeDataProcessor
)
from .analytics_utils import IncomeAnalyticsUtils
from .advanced_analytics import AdvancedIncomeAnalyticsWidget

# Simple chart widget classes for fallback
class SimpleChartWidget(QWidget):
    """Simple chart widget that displays basic information"""

    def __init__(self, chart_type="Chart", parent=None, theme='dark'):
        super().__init__(parent)
        self.chart_type = chart_type
        self.theme = theme
        self.current_data = pd.DataFrame()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Apply theme-aware styling to the widget
        self.apply_theme_styling()

        # Title
        self.title_label = QLabel(f"📊 {self.chart_type}")
        self.title_label.setAlignment(Qt.AlignCenter)

        # Apply theme-aware styling to title
        colors = self.get_theme_colors()
        self.title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['text']}; margin: 10px;")
        layout.addWidget(self.title_label)

        # Content area - FIXED: No background override
        self.content_widget = QWidget()
        # CRITICAL FIX: Remove background-color to let global theme handle it
        # self.content_widget.setStyleSheet(f"background-color: {colors['background']}; color: {colors['text']};")
        self.content_layout = QVBoxLayout(self.content_widget)
        layout.addWidget(self.content_widget)

        # Status label
        self.status_label = QLabel("No data available")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {colors['text']}; font-size: 12px; margin: 20px;")
        self.content_layout.addWidget(self.status_label)

    def get_theme_colors(self):
        """Get theme colors for current theme"""
        if self.theme == 'dark':
            return {
                'background': '#1e1e1e',
                'secondary_background': '#252526',
                'border': '#3e3e42',
                'text': '#ffffff'
            }
        elif self.theme == 'light':
            return {
                'background': '#ffffff',
                'secondary_background': '#f9f9f9',
                'border': '#e0e0e0',
                'text': '#000000'
            }
        elif self.theme == 'colorwave':
            return {
                'background': '#0a0a1a',
                'secondary_background': '#1a1a2e',
                'border': '#4a3c5a',
                'text': '#ffffff'
            }
        else:
            # Default to light theme (changed from dark)
            return {
                'background': '#ffffff',
                'secondary_background': '#f9f9f9',
                'border': '#e0e0e0',
                'text': '#000000'
            }

    def apply_theme_styling(self):
        """Apply theme-specific styling to the widget - FIXED: No background override"""
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove background-color to let global theme handle it
        # Only set border, let global theme control background and text colors
        self.setStyleSheet(f"""
            SimplePieChartWidget {{
                border: none;
            }}
        """)

    def update_chart(self, data: pd.DataFrame):
        """Update chart with new data"""
        self.current_data = data.copy()
        self.refresh_content()

    def refresh_content(self):
        """Refresh the chart content"""
        # Clear existing content
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if self.current_data.empty:
            self.status_label = QLabel("No data available")
            self.status_label.setAlignment(Qt.AlignCenter)
            self.status_label.setStyleSheet("color: #cccccc; font-size: 12px; margin: 20px;")
            self.content_layout.addWidget(self.status_label)
            return

        # Show basic statistics
        self.show_basic_stats()

    def show_basic_stats(self):
        """Show basic statistics about the data"""
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)

        # Basic stats
        total_records = len(self.current_data)
        if 'earned' in self.current_data.columns:
            total_income = self.current_data['earned'].sum()
            avg_income = self.current_data['earned'].mean()
            max_income = self.current_data['earned'].max()
            min_income = self.current_data['earned'].min()

            stats = [
                ("📊 Total Records", f"{total_records:,}"),
                ("💰 Total Income", f"₹{total_income:,.2f}"),
                ("📈 Average Income", f"₹{avg_income:,.2f}"),
                ("🔝 Maximum Income", f"₹{max_income:,.2f}"),
                ("🔻 Minimum Income", f"₹{min_income:,.2f}")
            ]
        else:
            stats = [("📊 Total Records", f"{total_records:,}")]

        # Get theme colors for styling
        colors = self.get_theme_colors()

        for i, (label, value) in enumerate(stats):
            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"font-weight: bold; color: {colors['text']}; padding: 5px;")
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: #0e639c; font-size: 14px; padding: 5px;")

            stats_layout.addWidget(label_widget, i, 0)
            stats_layout.addWidget(value_widget, i, 1)

        self.content_layout.addWidget(stats_widget)

        # Add specific chart content
        self.add_chart_specific_content()

    def add_chart_specific_content(self):
        """Add chart-specific content - to be overridden by subclasses"""
        # Add a simple test message
        test_label = QLabel("📊 Chart content loaded successfully!")
        test_label.setAlignment(Qt.AlignCenter)

        # Apply theme-aware styling - CRITICAL FIX: Remove background override
        colors = self.get_theme_colors()
        test_label.setStyleSheet(f"color: #90ee90; font-weight: bold; padding: 10px; border: 1px solid #90ee90; border-radius: 5px; margin: 10px;")
        self.content_layout.addWidget(test_label)


class SimplePieChartWidget(SimpleChartWidget):
    """Simple pie chart widget"""

    def __init__(self, parent=None, theme='dark'):
        super().__init__("Income Distribution by Source", parent, theme)

    def add_chart_specific_content(self):
        """Add pie chart specific content"""
        if self.current_data.empty:
            return

        # Show income sources breakdown
        sources_widget = QGroupBox("Income Sources Breakdown")
        sources_layout = QVBoxLayout(sources_widget)

        # Calculate income by source
        income_sources = []
        for col in self.current_data.columns:
            if col not in ['date', 'earned', 'goal', 'notes'] and self.current_data[col].sum() > 0:
                total = self.current_data[col].sum()
                income_sources.append((col.title(), total))

        income_sources.sort(key=lambda x: x[1], reverse=True)

        for source, amount in income_sources[:10]:  # Show top 10 sources
            source_widget = QWidget()
            source_layout = QHBoxLayout(source_widget)
            source_layout.setContentsMargins(5, 2, 5, 2)

            source_label = QLabel(source)
            source_label.setStyleSheet("font-weight: bold; color: #ffffff;")
            amount_label = QLabel(f"₹{amount:,.2f}")
            amount_label.setStyleSheet("color: #0e639c;")

            source_layout.addWidget(source_label)
            source_layout.addStretch()
            source_layout.addWidget(amount_label)

            sources_layout.addWidget(source_widget)

        self.content_layout.addWidget(sources_widget)


class SimpleTimeSeriesWidget(SimpleChartWidget):
    """Simple time series widget"""

    def __init__(self, parent=None, theme='dark'):
        super().__init__("Income Trends Over Time", parent, theme)

    def add_chart_specific_content(self):
        """Add time series specific content"""
        if self.current_data.empty or 'date' not in self.current_data.columns:
            return

        # Show time-based breakdown
        trends_widget = QGroupBox("Income Trends")
        colors = self.get_theme_colors()
        trends_widget.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 13px;
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: {colors['secondary_background']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px 0 4px;
                color: {colors['text']};
                background-color: {colors['background']};
            }}
        """)
        trends_layout = QVBoxLayout(trends_widget)
        trends_layout.setSpacing(3)
        trends_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins

        # Convert date column to datetime if it's not already
        data_copy = self.current_data.copy()
        if 'date' in data_copy.columns:
            data_copy['date'] = pd.to_datetime(data_copy['date'])
            data_copy = data_copy.sort_values('date')

            # Show recent trends
            if len(data_copy) > 0:
                latest_date = data_copy['date'].max()
                earliest_date = data_copy['date'].min()

                trend_info = [
                    ("📅 Date Range", f"{earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}"),
                    ("📊 Total Days", f"{len(data_copy):,}"),
                ]

                if 'earned' in data_copy.columns:
                    recent_avg = data_copy.tail(7)['earned'].mean() if len(data_copy) >= 7 else data_copy['earned'].mean()
                    trend_info.append(("📈 Recent Average (7 days)", f"₹{recent_avg:,.2f}"))

                for label, value in trend_info:
                    info_widget = QWidget()
                    info_layout = QHBoxLayout(info_widget)
                    info_layout.setContentsMargins(3, 1, 3, 1)  # Reduced margins

                    label_widget = QLabel(label)
                    label_widget.setStyleSheet(f"""
                        font-weight: bold;
                        color: {colors['text']};
                        font-size: 14px;
                        background-color: {colors['secondary_background']};
                        padding: 2px 4px;
                    """)
                    value_widget = QLabel(value)
                    value_widget.setStyleSheet(f"""
                        color: #0e639c;
                        font-weight: bold;
                        font-size: 14px;
                        background-color: {colors['secondary_background']};
                        padding: 2px 4px;
                    """)

                    info_layout.addWidget(label_widget)
                    info_layout.addStretch()
                    info_layout.addWidget(value_widget)

                    trends_layout.addWidget(info_widget)

        self.content_layout.addWidget(trends_widget)


class SimpleBarChartWidget(SimpleChartWidget):
    """Simple bar chart widget"""

    def __init__(self, parent=None):
        super().__init__("Monthly Income Analysis", parent)

    def add_chart_specific_content(self):
        """Add bar chart specific content"""
        if self.current_data.empty or 'date' not in self.current_data.columns:
            return

        # Show monthly breakdown
        monthly_widget = QGroupBox("Monthly Breakdown")
        monthly_layout = QVBoxLayout(monthly_widget)

        # Convert date and group by month
        data_copy = self.current_data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month'] = data_copy['date'].dt.to_period('M')

        if 'earned' in data_copy.columns:
            monthly_income = data_copy.groupby('month')['earned'].sum().sort_index(ascending=False)

            for month, income in monthly_income.head(12).items():  # Show last 12 months
                month_widget = QWidget()
                month_layout = QHBoxLayout(month_widget)
                month_layout.setContentsMargins(5, 2, 5, 2)

                month_label = QLabel(str(month))
                month_label.setStyleSheet("font-weight: bold; color: #ffffff;")
                income_label = QLabel(f"₹{income:,.2f}")
                income_label.setStyleSheet("color: #0e639c;")

                month_layout.addWidget(month_label)
                month_layout.addStretch()
                month_layout.addWidget(income_label)

                monthly_layout.addWidget(month_widget)

        self.content_layout.addWidget(monthly_widget)


class IncomeAnalyticsDashboard(QWidget):
    """Comprehensive income analytics dashboard with multiple chart types and KPIs"""
    
    data_export_requested = Signal(str)  # Signal for data export requests
    
    def __init__(self, income_model, config=None, parent=None):
        super().__init__(parent)
        self.income_model = income_model
        self.config = config
        self.current_data = pd.DataFrame()
        self.ui_initialized = False

        # Get current theme from config
        self.current_theme = getattr(config, 'theme', 'dark') if config else 'dark'

        # Set minimum size and apply theme-aware styling
        self.setMinimumSize(800, 600)
        self.apply_theme_styling()

        # Initialize UI immediately for dashboard tab usage
        try:
            print("Setting up Income Analytics Dashboard UI...")

            # Test the data manager path immediately
            file_path = income_model.data_manager.get_file_path("income", "income_records.csv")
            print(f"Income Analytics: Data file path: {file_path}")
            print(f"Income Analytics: File exists: {file_path.exists()}")

            self.setup_ui()
            self.setup_refresh_timer()
            self.ui_initialized = True  # Set this before refresh_data

            # Apply theme after UI is fully initialized
            self.apply_theme_styling()
            print("Income Analytics: About to call refresh_data...")
            self.refresh_data()
            print("Income Analytics Dashboard initialized successfully")

            # Test data loading
            self.test_data_loading()
        except Exception as e:
            print(f"Error initializing IncomeAnalyticsDashboard: {e}")
            import traceback
            traceback.print_exc()

            # Create a simple error display
            self.create_error_display(str(e))

    def apply_theme_styling(self):
        """Apply theme-specific styling to the dashboard - FIXED: No background override"""
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove background-color to let global theme handle it
        # Only set border, let global theme control background and text colors
        self.setStyleSheet(f"""
            IncomeAnalyticsDashboard {{
                border: 1px solid {colors['border']};
            }}
        """)

    def update_theme(self, new_theme):
        """Update theme for the dashboard and all child components"""
        self.current_theme = new_theme
        self.apply_theme_styling()

        # Update all child components that support theme changes
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setStyleSheet(self.get_chart_tabs_style())

        # Update interactive charts if they exist
        if hasattr(self, 'pie_chart') and hasattr(self.pie_chart, 'update_theme'):
            self.pie_chart.update_theme(new_theme)
        if hasattr(self, 'time_series_chart') and hasattr(self.time_series_chart, 'update_theme'):
            self.time_series_chart.update_theme(new_theme)
        if hasattr(self, 'bar_chart') and hasattr(self.bar_chart, 'update_theme'):
            self.bar_chart.update_theme(new_theme)
        if hasattr(self, 'scatter_chart') and hasattr(self.scatter_chart, 'update_theme'):
            self.scatter_chart.update_theme(new_theme)

        # Update mini charts
        if hasattr(self, 'mini_pie_chart') and hasattr(self.mini_pie_chart, 'apply_theme'):
            self.mini_pie_chart.apply_theme(new_theme)
        if hasattr(self, 'mini_time_series') and hasattr(self.mini_time_series, 'apply_theme'):
            self.mini_time_series.apply_theme(new_theme)

        # Update advanced analytics if it exists
        if hasattr(self, 'advanced_analytics') and hasattr(self.advanced_analytics, 'set_theme'):
            self.advanced_analytics.set_theme(new_theme)

        # Update KPI cards
        self.update_kpi_cards_theme(new_theme)

        # Update insights text area - FIXED: No background override
        if hasattr(self, 'insights_text'):
            colors = self.get_theme_colors()
            # CRITICAL FIX: Remove background-color to let global theme handle it
            self.insights_text.setStyleSheet(f"""
                QTextEdit {{
                    border: 1px solid {colors['border']};
                    border-radius: 4px;
                    padding: 8px;
                }}
            """)

        # Refresh the UI to apply new styles
        self.refresh_ui_styles()

        # Force update all widgets to apply new theme
        self.update()
        if hasattr(self, 'tab_widget'):
            self.tab_widget.update()
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    widget.update()

    def update_kpi_cards_theme(self, new_theme):
        """Update theme for all KPI cards"""
        kpi_cards = [
            'total_income_card', 'avg_daily_card', 'best_day_card',
            'goal_achievement_card', 'current_month_card', 'streak_card'
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

    def refresh_ui_styles(self):
        """Refresh UI styles for all components - FIXED: Include chart sub-tabs"""
        # Re-apply styles to existing widgets
        if hasattr(self, 'tab_widget'):
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    # Update overview tab styling
                    if i == 0:  # Overview tab
                        widget.setStyleSheet(self.get_overview_widget_style())
                    # Update charts tab styling
                    elif i == 1:  # Charts tab
                        widget.setStyleSheet(self.get_content_widget_style())

                        # CRITICAL FIX: Also update chart sub-tabs styling
                        # Find the chart_tabs QTabWidget inside the charts tab
                        for child in widget.findChildren(QTabWidget):
                            if child != self.tab_widget:  # Don't update the main tab widget
                                child.setStyleSheet(self.get_chart_tabs_style())

    def get_theme_colors(self):
        """Get theme colors for current theme"""
        if self.current_theme == 'dark':
            return {
                'background': '#1e1e1e',
                'secondary_background': '#252526',
                'border': '#3e3e42',
                'text': '#ffffff'
            }
        elif self.current_theme == 'light':
            return {
                'background': '#ffffff',
                'secondary_background': '#f9f9f9',
                'border': '#e0e0e0',
                'text': '#000000'
            }
        elif self.current_theme == 'colorwave':
            return {
                'background': '#0a0a1a',
                'secondary_background': '#1a1a2e',
                'border': '#4a3c5a',
                'text': '#ffffff'
            }
        else:
            # Default to dark theme
            return {
                'background': '#1e1e1e',
                'secondary_background': '#252526',
                'border': '#3e3e42',
                'text': '#ffffff'
            }

    def get_overview_widget_style(self):
        """Get theme-aware styling for overview widget - FIXED: No background override"""
        # CRITICAL FIX: Remove background-color to let global theme handle it
        # This was overriding the global theme for the entire overview content!
        return ""

    def get_content_widget_style(self):
        """Get theme-aware styling for content widget - FIXED: No background override"""
        # CRITICAL FIX: Remove background-color to let global theme handle it
        # This was overriding the global theme for the entire content area!
        return ""

    def get_scroll_area_style(self):
        """Get theme-aware styling for scroll area - FIXED: No background override"""
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove background-color to let global theme handle it
        return f"""
            QScrollArea {{
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {colors['secondary_background']};
                border: 1px solid {colors['border']};
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors['border']};
                border-radius: 6px;
            }}
        """

    def get_chart_tabs_style(self):
        """Get theme-aware styling for chart tabs - FIXED: No background override"""
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove background-color overrides to let global theme handle it
        # This was causing black backgrounds in chart sub-tabs!
        return f"""
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
            }}
            QTabBar::tab {{
                color: {colors['text']};
                padding: 8px 16px;
                border: 1px solid {colors['border']};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: #0e639c;
                color: {colors['text']};
            }}
            QTabBar::tab:hover {{
                background-color: {colors['border']};
            }}
        """

    def get_group_box_style(self):
        """Get theme-aware styling for group boxes - FIXED: No background override"""
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove background-color to let global theme handle it
        # This was the main cause of black backgrounds in KPI section!
        return f"""
            QGroupBox {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """

    def test_data_loading(self):
        """Test method to verify data loading works"""
        try:
            print("Income Analytics: Testing data loading...")
            all_data = self.income_model.get_all_income_records()
            print(f"Income Analytics: Test - Retrieved {len(all_data) if all_data is not None and not all_data.empty else 0} records")

            if all_data is not None and not all_data.empty:
                print("Income Analytics: Test - Sample record:")
                print(f"Income Analytics: Test - Data type: {type(all_data)}")
                print(f"Income Analytics: Test - Columns: {list(all_data.columns)}")
                print(f"Income Analytics: Test - First row: {all_data.iloc[0].to_dict()}")
            else:
                print("Income Analytics: Test - No records found or DataFrame is empty")

        except Exception as e:
            print(f"Income Analytics: Test - Error loading data: {e}")
            import traceback
            traceback.print_exc()

    def create_error_display(self, error_message):
        """Create a simple error display when initialization fails"""
        layout = QVBoxLayout(self)

        error_label = QLabel("❌ Income Analytics Dashboard Error")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("font-size: 18px; font-weight: bold; color: red; margin: 20px;")
        layout.addWidget(error_label)

        details_label = QLabel(f"Error: {error_message}")
        details_label.setAlignment(Qt.AlignCenter)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #cccccc; font-size: 12px; margin: 10px;")
        layout.addWidget(details_label)

        retry_button = QPushButton("Retry Initialization")
        retry_button.clicked.connect(self.retry_initialization)
        layout.addWidget(retry_button)

    def retry_initialization(self):
        """Retry initializing the dashboard"""
        try:
            # Clear existing layout
            for i in reversed(range(self.layout().count())):
                child = self.layout().itemAt(i).widget()
                if child:
                    child.setParent(None)

            # Retry initialization
            self.setup_ui()
            self.setup_refresh_timer()
            self.refresh_data()
            self.ui_initialized = True
            print("Income Analytics Dashboard retry successful")
        except Exception as e:
            print(f"Retry failed: {e}")

    def showEvent(self, event):
        """Initialize UI when widget is first shown"""
        super().showEvent(event)

        if not self.ui_initialized:
            try:
                self.setup_ui()
                self.setup_refresh_timer()
                self.refresh_data()
                self.ui_initialized = True
            except Exception as e:
                print(f"Error initializing income analytics dashboard: {e}")
                import traceback
                traceback.print_exc()
                # Create a simple fallback UI
                self.setup_fallback_ui(str(e))
                self.ui_initialized = True

    def setup_fallback_ui(self, error_message):
        """Setup a simple fallback UI when full analytics fails"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Income Analytics Dashboard")
        title_label.setObjectName("dashboardTitle")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Error message
        error_label = QLabel(f"Initialization Error: {error_message}")
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: red; margin: 10px 0;")
        layout.addWidget(error_label)

        # Basic stats if possible
        try:
            self.add_basic_stats(layout)
        except:
            pass

        layout.addStretch()

    def add_basic_stats(self, layout):
        """Add basic statistics without complex charts"""
        try:
            # Get basic income data
            all_data = self.income_model.get_all_income_records()
            if all_data:
                df = pd.DataFrame([record.to_dict() for record in all_data])

                # Calculate basic stats
                total_income = df['earned'].sum()
                avg_daily = df['earned'].mean()
                record_count = len(df)

                stats_label = QLabel(f"""
                Basic Statistics:
                • Total Records: {record_count}
                • Total Income: ₹{total_income:,.0f}
                • Average Daily: ₹{avg_daily:,.0f}

                Note: Full analytics features require proper initialization.
                """)
                colors = self.get_theme_colors()
                stats_label.setStyleSheet(f"background-color: {colors['secondary_background']}; color: {colors['text']}; padding: 15px; border-radius: 5px; border: 1px solid {colors['border']};")
                layout.addWidget(stats_label)
        except Exception as e:
            error_stats = QLabel(f"Could not load basic statistics: {e}")
            error_stats.setStyleSheet("color: orange;")
            layout.addWidget(error_stats)

    def setup_ui(self):
        """Setup the dashboard UI"""
        print("Creating Income Analytics Dashboard layout...")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Add a simple test label first
        test_label = QLabel("🎯 Income Analytics Dashboard Loading...")
        test_label.setAlignment(Qt.AlignCenter)
        colors = self.get_theme_colors()
        test_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #0e639c; padding: 20px; background-color: {colors['secondary_background']}; border: 2px solid #0e639c; border-radius: 5px;")
        layout.addWidget(test_label)

        try:
            print("Creating header...")
            # Header with controls
            self.create_header(layout)

            print("Creating main content...")
            # Main content with tabs
            self.create_main_content(layout)

            # Hide the test label since dashboard is working
            test_label.hide()

        except Exception as e:
            print(f"Error in setup_ui: {e}")
            test_label.setText(f"❌ Setup Error: {str(e)}")
            test_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #ff6b6b; padding: 10px; background-color: {colors['secondary_background']}; border: 2px solid #ff6b6b; border-radius: 5px;")
            raise
    
    def create_header(self, layout):
        """Create dashboard header with controls"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("Income Analytics Dashboard")
        title_label.setObjectName("dashboardTitle")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Date range selector
        date_label = QLabel("Date Range:")
        self.start_date = QDateEdit()
        # Set start date to 3 months ago to show recent data by default
        from datetime import datetime, timedelta
        three_months_ago = datetime.now().date() - timedelta(days=90)
        self.start_date.setDate(QDate(three_months_ago))
        self.start_date.dateChanged.connect(self.on_date_range_changed)

        self.end_date = QDateEdit()
        # Set end date to today to show current data
        self.end_date.setDate(QDate(datetime.now().date()))
        self.end_date.dateChanged.connect(self.on_date_range_changed)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        
        # Export button
        export_btn = QPushButton("Export Data")
        export_btn.clicked.connect(self.on_export_clicked)
        
        header_layout.addWidget(date_label)
        header_layout.addWidget(self.start_date)
        header_layout.addWidget(self.end_date)
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(export_btn)
        
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

        # Apply theme-aware styling to overview widget
        overview_widget.setStyleSheet(self.get_overview_widget_style())

        overview_layout = QVBoxLayout(overview_widget)
        overview_layout.setContentsMargins(10, 10, 10, 10)
        overview_layout.setSpacing(15)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Apply theme-aware styling to scroll area
        scroll_area.setStyleSheet(self.get_scroll_area_style())

        content_widget = QWidget()

        # Apply theme-aware styling to content widget
        content_widget.setStyleSheet(self.get_content_widget_style())

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

        # Apply theme-aware styling to charts widget
        charts_widget.setStyleSheet(self.get_content_widget_style())

        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(5, 5, 5, 5)

        # Create a simple working chart display
        chart_label = QLabel("📈 Income Analytics Charts")
        chart_label.setObjectName("chartTitle")
        chart_label.setAlignment(Qt.AlignCenter)

        # Apply theme-aware styling to chart label
        colors = self.get_theme_colors()
        chart_label.setStyleSheet(f"font-size: 18px; font-weight: bold; margin: 10px; color: {colors['text']};")
        charts_layout.addWidget(chart_label)

        # Create chart sub-tabs
        chart_tabs = QTabWidget()

        # Apply theme-aware styling to chart tabs
        chart_tabs.setStyleSheet(self.get_chart_tabs_style())

        # Import Interactive chart widgets
        from .interactive_charts import (
            InteractivePieChartWidget, InteractiveTimeSeriesWidget,
            InteractiveBarChartWidget, InteractiveScatterPlotWidget
        )

        # Pie Chart Tab
        try:
            print("Creating InteractivePieChartWidget...")
            self.pie_chart = InteractivePieChartWidget(theme=self.current_theme)
            chart_tabs.addTab(self.pie_chart, "🥧 Pie Charts")
            print("Pie chart widget created successfully")
        except Exception as e:
            print(f"Error creating interactive pie chart: {e}")
            import traceback
            traceback.print_exc()
            pie_placeholder = self.create_placeholder_widget("Pie Chart", "📊 Pie chart visualization")
            chart_tabs.addTab(pie_placeholder, "🥧 Pie Charts")

        # Time Series Tab
        try:
            print("Creating InteractiveTimeSeriesWidget...")
            self.time_series_chart = InteractiveTimeSeriesWidget(theme=self.current_theme)
            chart_tabs.addTab(self.time_series_chart, "📈 Time Series")
            print("Time series chart widget created successfully")
        except Exception as e:
            print(f"Error creating interactive time series chart: {e}")
            import traceback
            traceback.print_exc()
            time_placeholder = self.create_placeholder_widget("Time Series", "📈 Time series visualization")
            chart_tabs.addTab(time_placeholder, "📈 Time Series")

        # Bar Chart Tab
        try:
            print("Creating InteractiveBarChartWidget...")
            self.bar_chart = InteractiveBarChartWidget(theme=self.current_theme)
            chart_tabs.addTab(self.bar_chart, "📊 Bar Charts")
            print("Bar chart widget created successfully")
        except Exception as e:
            print(f"Error creating interactive bar chart: {e}")
            import traceback
            traceback.print_exc()
            bar_placeholder = self.create_placeholder_widget("Bar Chart", "📊 Bar chart visualization")
            chart_tabs.addTab(bar_placeholder, "📊 Bar Charts")

        # Scatter Plot Tab
        try:
            print("Creating InteractiveScatterPlotWidget...")
            self.scatter_chart = InteractiveScatterPlotWidget(theme=self.current_theme)
            chart_tabs.addTab(self.scatter_chart, "🔍 Scatter Plot")
            print("Scatter plot widget created successfully")
        except Exception as e:
            print(f"Error creating interactive scatter plot: {e}")
            import traceback
            traceback.print_exc()
            scatter_placeholder = self.create_placeholder_widget("Scatter Plot", "📊 Scatter plot visualization")
            chart_tabs.addTab(scatter_placeholder, "🔍 Scatter Plot")

        charts_layout.addWidget(chart_tabs)
        self.tab_widget.addTab(charts_widget, "📈 Interactive Charts")
    
    def create_advanced_tab(self):
        """Create advanced analytics tab with enhanced income analytics"""
        try:
            # Create advanced analytics widget
            self.advanced_analytics = AdvancedIncomeAnalyticsWidget()
            self.tab_widget.addTab(self.advanced_analytics, "🔬 Advanced Analytics")

            # Update with current data
            self.update_advanced_analytics()

        except Exception as e:
            print(f"Error creating advanced analytics tab: {e}")
            import traceback
            traceback.print_exc()

            # Create placeholder if advanced analytics fails
            placeholder_widget = QWidget()
            placeholder_layout = QVBoxLayout(placeholder_widget)

            error_label = QLabel("Advanced Analytics - Error Details")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("font-weight: bold; color: red; font-size: 14px;")

            details_label = QLabel(f"Error: {str(e)}")
            details_label.setAlignment(Qt.AlignCenter)
            details_label.setWordWrap(True)
            details_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px;")

            placeholder_layout.addWidget(error_label)
            placeholder_layout.addWidget(details_label)
            placeholder_layout.addStretch()

            self.tab_widget.addTab(placeholder_widget, "🔬 Advanced Analytics")

    def update_advanced_analytics(self):
        """Update advanced analytics with current income and expense data"""
        try:
            if hasattr(self, 'advanced_analytics') and hasattr(self, 'income_model'):
                # Get income data
                income_data = self.current_data

                # Get expense data (if available)
                expense_data = None
                try:
                    from ..expenses.models import ExpenseDataModel
                    expense_model = ExpenseDataModel(self.income_model.data_manager)
                    expense_data = expense_model.get_expense_data()
                except Exception as e:
                    print(f"Could not load expense data for flow analysis: {e}")

                # Update analytics
                self.advanced_analytics.update_analysis(income_data, expense_data)
        except Exception as e:
            print(f"Error updating advanced analytics: {e}")

    def create_placeholder_widget(self, title: str, message: str) -> QWidget:
        """Create a placeholder widget for features not yet implemented"""
        placeholder = QWidget()
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove background-color override to let global theme handle it
        placeholder.setStyleSheet(f"border: 1px solid {colors['border']}; border-radius: 4px;")
        layout = QVBoxLayout(placeholder)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("placeholderTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Message
        message_label = QLabel(message)
        message_label.setObjectName("placeholderMessage")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("color: #cccccc; font-size: 14px; margin: 20px;")
        layout.addWidget(message_label)

        # Add some sample data display
        if not self.current_data.empty:
            data_info = QLabel(f"📊 Data Available: {len(self.current_data)} income records")
            data_info.setAlignment(Qt.AlignCenter)
            data_info.setStyleSheet("color: #0e639c; font-size: 12px; font-weight: bold; margin: 10px;")
            layout.addWidget(data_info)

            # Show some basic stats
            if 'earned' in self.current_data.columns:
                total_income = self.current_data['earned'].sum()
                avg_income = self.current_data['earned'].mean()
                stats_label = QLabel(f"💰 Total Income: ₹{total_income:,.2f}\n📈 Average: ₹{avg_income:,.2f}")
                stats_label.setAlignment(Qt.AlignCenter)
                stats_label.setStyleSheet("color: #ffffff; font-size: 11px; margin: 10px;")
                layout.addWidget(stats_label)

        layout.addStretch()
        return placeholder

    def showEvent(self, event):
        """Handle show event to refresh data when tab becomes visible"""
        super().showEvent(event)
        if self.ui_initialized:
            # Force refresh data when the tab is shown
            self.refresh_data()

    def create_kpi_section(self, layout):
        """Create KPI cards section"""
        kpi_frame = QGroupBox("Key Performance Indicators")

        # Apply theme-aware styling to KPI frame
        kpi_frame.setStyleSheet(self.get_group_box_style())

        kpi_layout = QGridLayout(kpi_frame)
        kpi_layout.setSpacing(15)
        
        # Create KPI cards
        self.total_income_card = SummaryCardWidget("Total Income", "₹0", theme=self.current_theme)
        self.avg_daily_card = SummaryCardWidget("Average Daily", "₹0", theme=self.current_theme)
        self.best_day_card = SummaryCardWidget("Best Day", "₹0", theme=self.current_theme)
        self.goal_achievement_card = SummaryCardWidget("Goal Achievement", "0%", theme=self.current_theme)
        self.current_month_card = SummaryCardWidget("This Month", "₹0", theme=self.current_theme)
        self.streak_card = SummaryCardWidget("Current Streak", "0 days", theme=self.current_theme)
        
        # Add cards to grid
        kpi_layout.addWidget(self.total_income_card, 0, 0)
        kpi_layout.addWidget(self.avg_daily_card, 0, 1)
        kpi_layout.addWidget(self.best_day_card, 0, 2)
        kpi_layout.addWidget(self.goal_achievement_card, 1, 0)
        kpi_layout.addWidget(self.current_month_card, 1, 1)
        kpi_layout.addWidget(self.streak_card, 1, 2)
        
        layout.addWidget(kpi_frame)
    
    def create_quick_charts_section(self, layout):
        """Create quick charts section - EXPANDED: Responsive sizing for full chart visibility"""
        charts_frame = QGroupBox("Quick Visualizations")

        # Apply theme-aware styling to charts frame
        charts_frame.setStyleSheet(self.get_group_box_style())

        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setSpacing(20)  # Increased spacing for better visual separation
        charts_layout.setContentsMargins(15, 15, 15, 15)  # Add margins for better layout

        # Mini pie chart for sources - CRITICAL FIX: Remove size constraints
        self.mini_pie_chart = SimplePieChartWidget(theme=self.current_theme)
        # Remove setMaximumHeight to allow natural chart sizing
        self.mini_pie_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.mini_pie_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.mini_pie_chart)

        # Mini time series for trends - CRITICAL FIX: Remove size constraints
        self.mini_time_series = SimpleTimeSeriesWidget(theme=self.current_theme)
        # Remove setMaximumHeight and setMinimumHeight constraints
        self.mini_time_series.setMinimumHeight(400)  # Ensure adequate minimum height
        self.mini_time_series.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.mini_time_series)

        layout.addWidget(charts_frame)
    
    def create_insights_section(self, layout):
        """Create insights section"""
        insights_frame = QGroupBox("Smart Insights")

        # Apply theme-aware styling to insights frame
        insights_frame.setStyleSheet(self.get_group_box_style())

        insights_layout = QVBoxLayout(insights_frame)

        self.insights_text = QTextEdit()
        self.insights_text.setMaximumHeight(150)
        self.insights_text.setReadOnly(True)
        self.insights_text.setPlainText("Loading insights...")

        # Apply theme-aware styling to insights text - FIXED: No background override
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove background-color to let global theme handle it
        self.insights_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
            }}
        """)

        insights_layout.addWidget(self.insights_text)
        layout.addWidget(insights_frame)
    
    def setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
    
    def on_date_range_changed(self):
        """Handle date range change"""
        self.refresh_data()
    
    def on_export_clicked(self):
        """Handle export button click with enhanced options"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLabel

        if self.current_data.empty:
            QMessageBox.warning(self, "Export", "No data to export.")
            return

        # Create export options dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Options")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)

        # Export type selection
        layout.addWidget(QLabel("Select export format:"))
        csv_check = QCheckBox("CSV (Raw Data)")
        excel_check = QCheckBox("Excel (Comprehensive Report)")
        excel_check.setChecked(True)

        layout.addWidget(csv_check)
        layout.addWidget(excel_check)

        # Include options
        layout.addWidget(QLabel("\nInclude in export:"))
        include_stats = QCheckBox("Summary Statistics")
        include_insights = QCheckBox("Insights Report")
        include_trends = QCheckBox("Trend Analysis")

        include_stats.setChecked(True)
        include_insights.setChecked(True)
        include_trends.setChecked(True)

        layout.addWidget(include_stats)
        layout.addWidget(include_insights)
        layout.addWidget(include_trends)

        # Buttons
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export")
        cancel_btn = QPushButton("Cancel")

        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        def on_export():
            dialog.accept()
            self._perform_enhanced_export(
                csv_check.isChecked(),
                excel_check.isChecked(),
                include_stats.isChecked(),
                include_insights.isChecked(),
                include_trends.isChecked()
            )

        export_btn.clicked.connect(on_export)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def _perform_enhanced_export(self, export_csv: bool, export_excel: bool,
                                include_stats: bool, include_insights: bool, include_trends: bool):
        """Perform enhanced export with selected options"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if export_excel:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Excel Report",
                f"income_analytics_report_{timestamp}.xlsx",
                "Excel Files (*.xlsx)"
            )

            if filename:
                try:
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        # Main data
                        self.current_data.to_excel(writer, sheet_name='Raw Data', index=False)

                        if include_stats:
                            # Summary statistics
                            stats = IncomeAnalyticsUtils.calculate_comprehensive_stats(self.current_data)
                            stats_df = pd.DataFrame([stats])
                            stats_df.to_excel(writer, sheet_name='Statistics', index=False)

                        if include_trends:
                            # Trend analysis
                            weekly_trends = IncomeAnalyticsUtils.get_income_trends(self.current_data, 'weekly')
                            monthly_trends = IncomeAnalyticsUtils.get_income_trends(self.current_data, 'monthly')

                            weekly_trends.to_excel(writer, sheet_name='Weekly Trends', index=False)
                            monthly_trends.to_excel(writer, sheet_name='Monthly Trends', index=False)

                        if include_insights:
                            # Insights report
                            insights_report = IncomeAnalyticsUtils.generate_insights_report(self.current_data)

                            # Create insights dataframe
                            insights_data = []
                            for i, insight in enumerate(insights_report['insights']):
                                insights_data.append({'Type': 'Insight', 'Content': insight})
                            for i, recommendation in enumerate(insights_report['recommendations']):
                                insights_data.append({'Type': 'Recommendation', 'Content': recommendation})

                            if insights_data:
                                insights_df = pd.DataFrame(insights_data)
                                insights_df.to_excel(writer, sheet_name='Insights', index=False)

                    QMessageBox.information(self, "Export Complete", f"Excel report exported successfully to:\n{filename}")

                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"Failed to export Excel report: {str(e)}")

        if export_csv:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export CSV Data",
                f"income_data_{timestamp}.csv",
                "CSV Files (*.csv)"
            )

            if filename:
                try:
                    self.current_data.to_csv(filename, index=False)
                    QMessageBox.information(self, "Export Complete", f"CSV data exported successfully to:\n{filename}")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"Failed to export CSV data: {str(e)}")
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        # Don't refresh if UI hasn't been initialized yet
        if not self.ui_initialized:
            print("Income Analytics: UI not initialized yet, skipping refresh")
            return

        try:
            print("Income Analytics: Starting data refresh...")

            # Create test data if no real data is available
            test_data = {
                'date': ['2025-06-25', '2025-07-06', '2025-07-11'],
                'zomato': [200.0, 200.0, 500.0],
                'swiggy': [100.0, 200.0, 0.0],
                'shadow_fax': [50.0, 150.0, 100.0],
                'pc_repair': [10.0, 0.0, 0.0],
                'settings': [0.0, 50.0, 0.0],
                'youtube': [0.0, 20.0, 0.0],
                'gp_links': [0.0, 0.0, 0.0],
                'id_sales': [0.0, 500.0, 0.0],
                'other_sources': [0.0, 0.0, 0.0],
                'extra_work': [0.0, 300.0, 0.0],
                'earned': [360.0, 1420.0, 600.0],
                'status': ['In Progress', 'Exceeded', 'In Progress'],
                'goal_inc': [733.33, 709.68, 709.68],
                'progress': [49.09, 200.09, 84.55],
                'extra': [0.0, 710.32, 0.0],
                'notes': ['', '', ''],
                'created_at': ['2025-06-25', '2025-07-06', '2025-07-11'],
                'updated_at': ['2025-06-25', '2025-07-06', '2025-07-11']
            }

            # Try to get real data first
            try:
                # Get date range
                start_date = self.start_date.date().toPython()
                end_date = self.end_date.date().toPython()
                print(f"Income Analytics: Date range: {start_date} to {end_date}")

                # Get income data
                all_data = self.income_model.get_all_income_records()
                print(f"Income Analytics: Retrieved data type: {type(all_data)}")
                print(f"Income Analytics: Retrieved {len(all_data) if all_data is not None and not all_data.empty else 0} total records")

                if all_data is not None and not all_data.empty:
                    # all_data is already a DataFrame from the model
                    df = all_data.copy()
                    df['date'] = pd.to_datetime(df['date'])
                    print(f"Income Analytics: DataFrame has {len(df)} rows")
                    print(f"Income Analytics: DataFrame columns: {list(df.columns)}")
                    print(f"Income Analytics: Sample dates: {df['date'].head().tolist()}")

                    # Filter by date range
                    filtered_df = df[
                        (df['date'].dt.date >= start_date) &
                        (df['date'].dt.date <= end_date)
                    ].copy()

                    print(f"Income Analytics: Filtered data has {len(filtered_df)} rows")

                    # If no data in range, show all data
                    if filtered_df.empty:
                        print("Income Analytics: No data in date range, showing all available data")
                        print(f"Income Analytics: Available dates: {df['date'].dt.date.tolist()}")
                        self.current_data = df.copy()
                    else:
                        self.current_data = filtered_df
                else:
                    raise Exception("No real data available - DataFrame is None or empty")

            except Exception as data_error:
                print(f"Income Analytics: Error loading real data: {data_error}")
                print("Income Analytics: Using test data instead...")

                # Use test data
                self.current_data = pd.DataFrame(test_data)
                self.current_data['date'] = pd.to_datetime(self.current_data['date'])

            if not self.current_data.empty:
                print(f"Income Analytics: Final data has {len(self.current_data)} rows")
                print(f"Income Analytics: Sample data columns: {list(self.current_data.columns)}")
                print(f"Income Analytics: Sample earned values: {self.current_data['earned'].head().tolist()}")

            # Update all components
            print("Income Analytics: Updating KPIs...")
            self.update_kpis()
            print("Income Analytics: Updating charts...")
            self.update_charts()
            print("Income Analytics: Updating insights...")
            self.update_insights()
            print("Income Analytics: Updating advanced analytics...")
            self.update_advanced_analytics()
            print("Income Analytics: Data refresh completed successfully")

        except Exception as e:
            print(f"Error refreshing dashboard data: {e}")
            import traceback
            traceback.print_exc()
    
    def update_kpis(self):
        """Update KPI cards"""
        if self.current_data.empty:
            return
        
        stats = IncomeDataProcessor.calculate_summary_stats(self.current_data)
        
        self.total_income_card.update_value(f"₹{stats['total_income']:,.0f}")
        self.avg_daily_card.update_value(f"₹{stats['average_daily']:,.0f}")
        self.best_day_card.update_value(f"₹{stats['best_day']:,.0f}")
        self.goal_achievement_card.update_value(f"{stats['goal_achievement_rate']:.1f}%")
        self.current_month_card.update_value(f"₹{stats['current_month']:,.0f}")
        
        # Calculate streak
        streak_days = self._calculate_streak()
        self.streak_card.update_value(f"{streak_days} days")
    
    def update_charts(self):
        """Update all charts with current data"""
        print(f"Income Analytics: update_charts called with data shape: {self.current_data.shape if not self.current_data.empty else 'empty'}")

        if self.current_data.empty:
            print("Income Analytics: No data to update charts with")
            return

        # Update interactive charts with correct method signature
        try:
            if hasattr(self, 'pie_chart') and hasattr(self.pie_chart, 'update_chart'):
                print("Income Analytics: Updating pie chart...")
                self.pie_chart.update_chart(self.current_data)
                print("Income Analytics: Pie chart updated successfully")
            else:
                print("Income Analytics: Pie chart not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating pie chart: {e}")

        try:
            if hasattr(self, 'time_series_chart') and hasattr(self.time_series_chart, 'update_chart'):
                print("Income Analytics: Updating time series chart...")
                self.time_series_chart.update_chart(self.current_data)
                print("Income Analytics: Time series chart updated successfully")
            else:
                print("Income Analytics: Time series chart not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating time series chart: {e}")

        try:
            if hasattr(self, 'bar_chart') and hasattr(self.bar_chart, 'update_chart'):
                print("Income Analytics: Updating bar chart...")
                self.bar_chart.update_chart(self.current_data)
                print("Income Analytics: Bar chart updated successfully")
            else:
                print("Income Analytics: Bar chart not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating bar chart: {e}")

        try:
            if hasattr(self, 'scatter_chart') and hasattr(self.scatter_chart, 'update_chart'):
                print("Income Analytics: Updating scatter plot...")
                self.scatter_chart.update_chart(self.current_data)
                print("Income Analytics: Scatter plot updated successfully")
            else:
                print("Income Analytics: Scatter plot not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating scatter plot: {e}")

        # Update Advanced Analytics charts
        try:
            if hasattr(self, 'heatmap_chart') and hasattr(self.heatmap_chart, 'update_chart'):
                print("Income Analytics: Updating advanced heatmap...")
                self.heatmap_chart.update_chart(self.current_data)
                print("Income Analytics: Advanced heatmap updated successfully")
            else:
                print("Income Analytics: Advanced heatmap not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating advanced heatmap: {e}")

        try:
            if hasattr(self, 'treemap_chart') and hasattr(self.treemap_chart, 'update_chart'):
                print("Income Analytics: Updating advanced treemap...")
                self.treemap_chart.update_chart(self.current_data)
                print("Income Analytics: Advanced treemap updated successfully")
            else:
                print("Income Analytics: Advanced treemap not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating advanced treemap: {e}")

        # Update mini charts if they exist
        try:
            if hasattr(self, 'mini_pie_chart') and hasattr(self.mini_pie_chart, 'update_chart'):
                print("Income Analytics: Updating mini pie chart...")
                self.mini_pie_chart.update_chart(self.current_data)
                print("Income Analytics: Mini pie chart updated successfully")
            else:
                print("Income Analytics: Mini pie chart not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating mini pie chart: {e}")

        try:
            if hasattr(self, 'mini_time_series') and hasattr(self.mini_time_series, 'update_chart'):
                print("Income Analytics: Updating mini time series...")
                self.mini_time_series.update_chart(self.current_data)
                print("Income Analytics: Mini time series updated successfully")
            else:
                print("Income Analytics: Mini time series not available or missing update_chart method")
        except Exception as e:
            print(f"Error updating mini time series: {e}")
    
    def update_insights(self):
        """Update insights section"""
        if self.current_data.empty:
            self.insights_text.setPlainText("No data available for insights.")
            return
        
        insights = self._generate_insights()
        self.insights_text.setPlainText("\n".join(insights))
    
    def _calculate_streak(self) -> int:
        """Calculate current goal achievement streak"""
        if self.current_data.empty:
            return 0
        
        # Sort by date descending
        sorted_data = self.current_data.sort_values('date', ascending=False)
        
        streak = 0
        for _, row in sorted_data.iterrows():
            if row['progress'] >= 100:  # Goal achieved
                streak += 1
            else:
                break
        
        return streak
    
    def _generate_insights(self) -> List[str]:
        """Generate smart insights from income data using enhanced analytics"""
        try:
            insights_report = IncomeAnalyticsUtils.generate_insights_report(self.current_data)

            # Combine insights and recommendations
            all_insights = []
            all_insights.extend(insights_report.get('insights', []))

            # Add recommendations as insights with different formatting
            recommendations = insights_report.get('recommendations', [])
            if recommendations:
                all_insights.append("💡 Recommendations:")
                for rec in recommendations:
                    all_insights.append(f"   • {rec}")

            return all_insights if all_insights else ["No insights available for the current data range."]

        except Exception as e:
            return [f"Unable to generate insights: {str(e)}"]
