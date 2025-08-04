"""
Expense Summary Widget
Provides detailed expense summaries with filtering and sorting capabilities
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QGroupBox,
    QSplitter, QScrollArea, QCheckBox, QSpinBox, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QFont, QPalette

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .visualization import (
    PieChartWidget, BarChartWidget, LineChartWidget, SummaryCardWidget,
    ExpenseDataProcessor
)
from .models import ExpenseDataModel


class ExpenseSummaryWidget(QWidget):
    """Main expense summary widget with detailed analytics"""
    
    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.config = config
        self.expense_model = ExpenseDataModel(data_manager)

        # Get current theme from config
        self.current_theme = getattr(config, 'theme', 'dark')

        # Current filter state
        self.current_filters = {}
        self.filtered_data = pd.DataFrame()

        self.setup_ui()
        self.setup_connections()
        self.refresh_data()
        
    def setup_ui(self):
        """Setup the summary widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Apply theme-aware styling to the main widget
        self.apply_theme_styling()

        # Header
        self.create_header(layout)

        # Filter controls
        self.create_filter_controls(layout)

        # Main content area with tabs
        self.create_main_content(layout)

    def apply_theme_styling(self):
        """Apply theme-specific styling to the summary widget - FIXED: No background override"""
        # CRITICAL FIX: Remove all hardcoded background-color overrides
        # Let global theme handle all background colors
        if self.current_theme == 'dark':
            self.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #3e3e42;
                }
                QTabBar::tab {
                    color: #cccccc;
                    padding: 8px 16px;
                    border: 1px solid #3e3e42;
                }
                QTabBar::tab:selected {
                    background-color: #0e639c;
                    color: #ffffff;
                }
            """)
        elif self.current_theme == 'light':
            self.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #e0e0e0;
                }
                QTabBar::tab {
                    color: #333333;
                    padding: 8px 16px;
                    border: 1px solid #e0e0e0;
                }
                QTabBar::tab:selected {
                    background-color: #0078d4;
                    color: #ffffff;
                }
            """)
        elif self.current_theme == 'colorwave':
            self.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #4a3c5a;
                }
                QTabBar::tab {
                    color: #cccccc;
                    padding: 8px 16px;
                    border: 1px solid #4a3c5a;
                }
                QTabBar::tab:selected {
                    background-color: #e91e63;
                    color: #ffffff;
                }
            """)
        
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("Expense Summary & Analytics")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_btn)
        
        # Export button
        self.export_btn = QPushButton("📊 Export")
        self.export_btn.clicked.connect(self.export_summary)
        header_layout.addWidget(self.export_btn)
        
        layout.addWidget(header_frame)
        
    def create_filter_controls(self, layout):
        """Create filter controls section"""
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        # Date range filter
        date_frame = QFrame()
        date_layout = QVBoxLayout(date_frame)
        date_layout.addWidget(QLabel("Date Range:"))
        
        date_controls = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        date_controls.addWidget(QLabel("From:"))
        date_controls.addWidget(self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_controls.addWidget(QLabel("To:"))
        date_controls.addWidget(self.end_date)
        
        date_layout.addLayout(date_controls)
        filter_layout.addWidget(date_frame)
        
        # Category filter
        category_frame = QFrame()
        category_layout = QVBoxLayout(category_frame)
        category_layout.addWidget(QLabel("Category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        category_layout.addWidget(self.category_combo)
        filter_layout.addWidget(category_frame)
        
        # Amount range filter
        amount_frame = QFrame()
        amount_layout = QVBoxLayout(amount_frame)
        amount_layout.addWidget(QLabel("Amount Range:"))
        
        amount_controls = QHBoxLayout()
        self.min_amount = QSpinBox()
        self.min_amount.setRange(0, 999999)
        self.min_amount.setPrefix("₹")
        amount_controls.addWidget(QLabel("Min:"))
        amount_controls.addWidget(self.min_amount)
        
        self.max_amount = QSpinBox()
        self.max_amount.setRange(0, 999999)
        self.max_amount.setValue(10000)
        self.max_amount.setPrefix("₹")
        amount_controls.addWidget(QLabel("Max:"))
        amount_controls.addWidget(self.max_amount)
        
        amount_layout.addLayout(amount_controls)
        filter_layout.addWidget(amount_frame)
        
        # Apply filters button
        self.apply_filters_btn = QPushButton("Apply Filters")
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.apply_filters_btn)
        
        # Clear filters button
        self.clear_filters_btn = QPushButton("Clear Filters")
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(self.clear_filters_btn)
        
        layout.addWidget(filter_group)
        
    def create_main_content(self, layout):
        """Create main content area with tabs"""
        self.tab_widget = QTabWidget()
        
        # Summary Overview Tab
        self.create_summary_tab()
        
        # Category Analysis Tab
        self.create_category_tab()
        
        # Time Analysis Tab
        self.create_time_tab()
        
        # Detailed Data Tab
        self.create_data_tab()
        
        layout.addWidget(self.tab_widget)
        
    def create_summary_tab(self):
        """Create summary overview tab"""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        
        # Summary cards - EXPANDED: Better spacing and layout
        cards_frame = QFrame()
        cards_frame.setMinimumHeight(200)  # Ensure adequate height for expanded cards
        cards_layout = QGridLayout(cards_frame)
        cards_layout.setSpacing(25)  # Increased spacing between cards
        cards_layout.setContentsMargins(20, 20, 20, 20)  # More generous margins
        
        self.summary_cards = {}
        
        # Total Amount
        self.summary_cards['total'] = SummaryCardWidget(
            "Total Expenses", "₹0", "Selected Period", "💰", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['total'], 0, 0)

        # Average Amount
        self.summary_cards['average'] = SummaryCardWidget(
            "Average", "₹0", "Per Transaction", "📊", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['average'], 0, 1)

        # Transaction Count
        self.summary_cards['count'] = SummaryCardWidget(
            "Transactions", "0", "Total Count", "🔢", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['count'], 0, 2)

        # Top Category
        self.summary_cards['top_category'] = SummaryCardWidget(
            "Top Category", "N/A", "Highest Spending", "🏆", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['top_category'], 1, 0)

        # Most Frequent
        self.summary_cards['frequent'] = SummaryCardWidget(
            "Most Frequent", "N/A", "Category", "🔄", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['frequent'], 1, 1)

        # Categories Used
        self.summary_cards['categories'] = SummaryCardWidget(
            "Categories", "0", "Used", "📂", theme=self.current_theme
        )
        cards_layout.addWidget(self.summary_cards['categories'], 1, 2)
        
        layout.addWidget(cards_frame)
        
        # Quick insights
        insights_group = QGroupBox("Quick Insights")
        insights_layout = QVBoxLayout(insights_group)
        
        self.insights_label = QLabel("Select data to see insights...")
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        insights_layout.addWidget(self.insights_label)
        
        layout.addWidget(insights_group)
        
        self.tab_widget.addTab(summary_widget, "📊 Summary")
        
    def create_category_tab(self):
        """Create category analysis tab"""
        category_widget = QWidget()
        layout = QVBoxLayout(category_widget)
        
        # Charts for category analysis - EXPANDED: Better sizing and layout
        charts_splitter = QSplitter(Qt.Horizontal)
        charts_splitter.setMinimumHeight(450)  # Ensure adequate height for chart visibility

        # Pie chart for distribution - EXPANDED: Responsive sizing
        self.category_pie_chart = PieChartWidget(theme=self.current_theme)
        self.category_pie_chart.category_clicked.connect(self.on_category_drill_down)
        self.category_pie_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.category_pie_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_splitter.addWidget(self.category_pie_chart)

        # Bar chart for amounts - EXPANDED: Responsive sizing
        self.category_bar_chart = BarChartWidget(theme=self.current_theme)
        self.category_bar_chart.bar_clicked.connect(self.on_bar_drill_down)
        self.category_bar_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.category_bar_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_splitter.addWidget(self.category_bar_chart)
        
        layout.addWidget(charts_splitter)
        
        self.tab_widget.addTab(category_widget, "📂 Categories")
        
    def create_time_tab(self):
        """Create time analysis tab"""
        time_widget = QWidget()
        layout = QVBoxLayout(time_widget)
        
        # Time period selector
        period_frame = QFrame()
        period_layout = QHBoxLayout(period_frame)
        period_layout.addWidget(QLabel("View by:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.period_combo.currentTextChanged.connect(self.update_time_charts)
        period_layout.addWidget(self.period_combo)
        
        period_layout.addStretch()
        layout.addWidget(period_frame)
        
        # Time-based charts - EXPANDED: Responsive sizing
        self.time_line_chart = LineChartWidget(theme=self.current_theme)
        self.time_line_chart.setMinimumHeight(400)  # Ensure adequate minimum height
        self.time_line_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.time_line_chart)
        
        self.tab_widget.addTab(time_widget, "📈 Trends")
        
    def create_data_tab(self):
        """Create detailed data tab"""
        data_widget = QWidget()
        layout = QVBoxLayout(data_widget)
        
        # Search and sort controls
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        # Search
        controls_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in notes, category...")
        self.search_edit.textChanged.connect(self.filter_table)
        controls_layout.addWidget(self.search_edit)
        
        # Sort by
        controls_layout.addWidget(QLabel("Sort by:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Date", "Amount", "Category", "Notes"])
        self.sort_combo.currentTextChanged.connect(self.sort_table)
        controls_layout.addWidget(self.sort_combo)
        
        # Sort order
        self.sort_desc_check = QCheckBox("Descending")
        self.sort_desc_check.stateChanged.connect(self.sort_table)
        controls_layout.addWidget(self.sort_desc_check)
        
        controls_layout.addStretch()
        layout.addWidget(controls_frame)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.data_table)
        
        self.tab_widget.addTab(data_widget, "📋 Data")
        
    def setup_connections(self):
        """Setup signal connections"""
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(60000)  # Refresh every minute
        
        # Filter change connections
        self.start_date.dateChanged.connect(self.on_filter_changed)
        self.end_date.dateChanged.connect(self.on_filter_changed)
        self.category_combo.currentTextChanged.connect(self.on_filter_changed)
        
    def on_filter_changed(self):
        """Handle filter changes"""
        # Auto-apply filters after a short delay
        if hasattr(self, 'filter_timer'):
            self.filter_timer.stop()

        self.filter_timer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.apply_filters)
        self.filter_timer.start(500)  # 500ms delay

    def refresh_data(self):
        """Refresh all data and update displays"""
        try:
            # Get all expense data
            all_data = self.expense_model.get_all_expenses()

            if all_data is None or all_data.empty:
                self.filtered_data = pd.DataFrame()
            else:
                self.filtered_data = all_data.copy()

            # Update category filter options
            self.update_category_filter()

            # Apply current filters
            self.apply_filters()

        except Exception as e:
            print(f"Error refreshing expense summary data: {e}")
            self.filtered_data = pd.DataFrame()
            self.update_displays()

    def update_category_filter(self):
        """Update category filter dropdown"""
        try:
            current_selection = self.category_combo.currentText()
            self.category_combo.clear()
            self.category_combo.addItem("All Categories")

            if not self.filtered_data.empty and 'category' in self.filtered_data.columns:
                categories = sorted(self.filtered_data['category'].dropna().unique())
                self.category_combo.addItems(categories)

            # Restore selection if possible
            index = self.category_combo.findText(current_selection)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"Error updating category filter: {e}")

    def apply_filters(self):
        """Apply current filters to the data"""
        try:
            if self.filtered_data.empty:
                self.update_displays()
                return

            # Start with all data
            filtered = self.filtered_data.copy()

            # Apply date filter
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()

            if 'date' in filtered.columns:
                filtered['date'] = pd.to_datetime(filtered['date'])
                filtered = filtered[
                    (filtered['date'].dt.date >= start_date) &
                    (filtered['date'].dt.date <= end_date)
                ]

            # Apply category filter
            category_filter = self.category_combo.currentText()
            if category_filter != "All Categories" and 'category' in filtered.columns:
                filtered = filtered[filtered['category'] == category_filter]

            # Apply amount filter
            min_amount = self.min_amount.value()
            max_amount = self.max_amount.value()

            if 'amount' in filtered.columns:
                filtered = filtered[
                    (filtered['amount'] >= min_amount) &
                    (filtered['amount'] <= max_amount)
                ]

            # Store filtered data
            self.current_filters = {
                'start_date': start_date,
                'end_date': end_date,
                'category': category_filter,
                'min_amount': min_amount,
                'max_amount': max_amount
            }

            # Update all displays with filtered data
            self.update_displays(filtered)

        except Exception as e:
            print(f"Error applying filters: {e}")
            self.update_displays()

    def clear_filters(self):
        """Clear all filters and show all data"""
        try:
            # Reset filter controls
            self.start_date.setDate(QDate.currentDate().addDays(-30))
            self.end_date.setDate(QDate.currentDate())
            self.category_combo.setCurrentIndex(0)  # "All Categories"
            self.min_amount.setValue(0)
            self.max_amount.setValue(10000)

            # Clear current filters
            self.current_filters = {}

            # Apply filters (which will now show all data)
            self.apply_filters()

        except Exception as e:
            print(f"Error clearing filters: {e}")

    def update_displays(self, data=None):
        """Update all displays with the provided data"""
        if data is None:
            data = pd.DataFrame()

        try:
            # Update summary cards
            self.update_summary_cards(data)

            # Update charts
            self.update_charts(data)

            # Update data table
            self.update_data_table(data)

            # Update insights
            self.update_insights(data)

        except Exception as e:
            print(f"Error updating displays: {e}")

    def update_summary_cards(self, data):
        """Update summary cards with data metrics and proper validation"""
        try:
            # Check if we have valid transaction data
            if data.empty or not self._has_valid_transaction_data(data):
                # Set default values
                for card in self.summary_cards.values():
                    card.update_values("0", "No data")
                return

            # Calculate metrics
            metrics = ExpenseDataProcessor.calculate_summary_metrics(data)

            # Update cards
            self.summary_cards['total'].update_values(
                f"₹{metrics['total_amount']:.0f}",
                "Selected Period"
            )

            self.summary_cards['average'].update_values(
                f"₹{metrics['avg_amount']:.0f}",
                "Per Transaction"
            )

            self.summary_cards['count'].update_values(
                f"{metrics['transaction_count']}",
                "Total Count"
            )

            self.summary_cards['top_category'].update_values(
                f"{metrics['most_expensive_category']}",
                "Highest Spending"
            )

            self.summary_cards['frequent'].update_values(
                f"{metrics['most_frequent_category']}",
                "Most Used"
            )

            self.summary_cards['categories'].update_values(
                f"{metrics['categories_count']}",
                "Categories Used"
            )

        except Exception as e:
            print(f"Error updating summary cards: {e}")

    def update_charts(self, data):
        """Update all charts with filtered data and proper validation"""
        try:
            # Check if we have valid transaction data
            if data.empty or not self._has_valid_transaction_data(data):
                # Clear charts if no valid data
                self.category_pie_chart.clear_chart()
                self.category_bar_chart.clear_chart()
                self.time_line_chart.clear_chart()
                return

            # Update category charts
            self.category_pie_chart.update_chart(
                data,
                value_column='amount',
                label_column='category',
                title="Expense Distribution by Category"
            )

            self.category_bar_chart.update_chart(
                data,
                x_column='category',
                y_column='amount',
                title="Category Spending Analysis",
                chart_type='horizontal'
            )

            # Update time chart based on selected period
            period = self.period_combo.currentText().lower()
            self.time_line_chart.update_chart(
                data,
                date_column='date',
                value_column='amount',
                title=f"{period.title()} Spending Trends",
                aggregation=period
            )

        except Exception as e:
            print(f"Error updating charts: {e}")

    def update_data_table(self, data):
        """Update the data table with filtered data and proper validation"""
        try:
            # Check if we have valid transaction data
            if data.empty or not self._has_valid_transaction_data(data):
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
                return

            # Set up table structure
            columns = ['Date', 'Category', 'Sub-Category', 'Amount', 'Transaction Mode', 'Notes']
            self.data_table.setColumnCount(len(columns))
            self.data_table.setHorizontalHeaderLabels(columns)
            self.data_table.setRowCount(len(data))

            # Populate table
            for row, (_, record) in enumerate(data.iterrows()):
                self.data_table.setItem(row, 0, QTableWidgetItem(str(record.get('date', ''))))
                self.data_table.setItem(row, 1, QTableWidgetItem(str(record.get('category', ''))))
                self.data_table.setItem(row, 2, QTableWidgetItem(str(record.get('sub_category', ''))))
                self.data_table.setItem(row, 3, QTableWidgetItem(f"₹{record.get('amount', 0):.2f}"))
                self.data_table.setItem(row, 4, QTableWidgetItem(str(record.get('transaction_mode', ''))))
                self.data_table.setItem(row, 5, QTableWidgetItem(str(record.get('notes', ''))))

            # Resize columns to content
            self.data_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating data table: {e}")

    def update_insights(self, data):
        """Update insights section with data analysis and proper validation"""
        try:
            # Check if we have valid transaction data
            if data.empty or not self._has_valid_transaction_data(data):
                self.insights_label.setText("No expense data available for insights.")
                return

            insights = []

            # Calculate basic insights
            total_amount = data['amount'].sum()
            avg_amount = data['amount'].mean()
            transaction_count = len(data)

            insights.append(f"📊 Total of {transaction_count} transactions worth ₹{total_amount:.0f}")
            insights.append(f"💰 Average transaction amount: ₹{avg_amount:.0f}")

            # Category insights
            if 'category' in data.columns:
                top_category = data.groupby('category')['amount'].sum().idxmax()
                top_amount = data.groupby('category')['amount'].sum().max()
                insights.append(f"🏆 Highest spending category: {top_category} (₹{top_amount:.0f})")

            # Time-based insights
            if 'date' in data.columns:
                data_copy = data.copy()
                data_copy['date'] = pd.to_datetime(data_copy['date'])
                data_copy['day_of_week'] = data_copy['date'].dt.day_name()

                busiest_day = data_copy.groupby('day_of_week')['amount'].sum().idxmax()
                insights.append(f"📅 Highest spending day: {busiest_day}")

            # Amount insights
            max_transaction = data['amount'].max()
            min_transaction = data['amount'].min()
            insights.append(f"💸 Largest transaction: ₹{max_transaction:.0f}")
            insights.append(f"💵 Smallest transaction: ₹{min_transaction:.0f}")

            # Join insights
            insights_text = "\n".join(insights)
            self.insights_label.setText(insights_text)

        except Exception as e:
            print(f"Error updating insights: {e}")
            self.insights_label.setText("Error generating insights.")

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

    def update_time_charts(self):
        """Update time charts when period changes"""
        try:
            # Get current filtered data
            if hasattr(self, 'filtered_data') and not self.filtered_data.empty:
                # Re-apply filters to get current data
                self.apply_filters()
        except Exception as e:
            print(f"Error updating time charts: {e}")

    def filter_table(self):
        """Filter table based on search text"""
        try:
            search_text = self.search_edit.text().lower()

            for row in range(self.data_table.rowCount()):
                show_row = False

                # Search in all columns
                for col in range(self.data_table.columnCount()):
                    item = self.data_table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break

                self.data_table.setRowHidden(row, not show_row)

        except Exception as e:
            print(f"Error filtering table: {e}")

    def sort_table(self):
        """Sort table based on selected column and order"""
        try:
            sort_column_name = self.sort_combo.currentText()
            descending = self.sort_desc_check.isChecked()

            # Map column names to indices
            column_map = {
                'Date': 0,
                'Amount': 3,
                'Category': 1,
                'Notes': 5
            }

            if sort_column_name in column_map:
                column_index = column_map[sort_column_name]
                order = Qt.DescendingOrder if descending else Qt.AscendingOrder
                self.data_table.sortItems(column_index, order)

        except Exception as e:
            print(f"Error sorting table: {e}")

    def export_summary(self):
        """Export current summary data"""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox

            # Get current filtered data
            if not hasattr(self, 'filtered_data') or self.filtered_data.empty:
                QMessageBox.warning(self, "Export", "No data to export.")
                return

            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Expense Summary",
                f"expense_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv);;Excel Files (*.xlsx)"
            )

            if file_path:
                if file_path.endswith('.xlsx'):
                    self.filtered_data.to_excel(file_path, index=False)
                else:
                    self.filtered_data.to_csv(file_path, index=False)

                QMessageBox.information(self, "Export", f"Data exported successfully to {file_path}")

        except Exception as e:
            print(f"Error exporting summary: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")

    def on_category_drill_down(self, category_name):
        """Handle category drill-down from pie chart click"""
        try:
            # Filter data by the clicked category
            self.category_combo.setCurrentText(category_name)
            self.apply_filters()

            # Switch to data tab to show filtered results
            self.tab_widget.setCurrentIndex(3)  # Data tab

            # Show notification
            self.insights_label.setText(f"🔍 Filtered by category: {category_name}\nClick 'Clear Filters' to reset.")

        except Exception as e:
            print(f"Error in category drill-down: {e}")

    def on_bar_drill_down(self, label, value):
        """Handle bar chart drill-down"""
        try:
            # Show detailed information about the clicked bar
            info_text = f"📊 Selected: {label}\n💰 Amount: ₹{value:.2f}\n\nClick to filter by this category."

            # If it's a category, filter by it
            if hasattr(self, 'category_combo'):
                categories = [self.category_combo.itemText(i) for i in range(self.category_combo.count())]
                if label in categories:
                    self.category_combo.setCurrentText(label)
                    self.apply_filters()
                    self.tab_widget.setCurrentIndex(3)  # Switch to data tab
                    info_text += f"\n\n✅ Filtered by {label}"

            self.insights_label.setText(info_text)

        except Exception as e:
            print(f"Error in bar drill-down: {e}")

    def add_chart_tooltips(self):
        """Add tooltips to charts for better user experience"""
        try:
            # Add tooltip functionality to charts
            self.category_pie_chart.setToolTip("Click on a slice to filter by that category")
            self.category_bar_chart.setToolTip("Click on a bar to see detailed information")
            self.time_line_chart.setToolTip("Hover over points to see values")

        except Exception as e:
            print(f"Error adding chart tooltips: {e}")

    def create_quick_filter_buttons(self):
        """Create quick filter buttons for common filters"""
        try:
            # Add quick filter section to filter controls
            quick_filter_frame = QFrame()
            quick_filter_layout = QVBoxLayout(quick_filter_frame)
            quick_filter_layout.addWidget(QLabel("Quick Filters:"))

            # Common filter buttons
            filters = [
                ("Last 7 Days", lambda: self.apply_quick_date_filter(7)),
                ("Last 30 Days", lambda: self.apply_quick_date_filter(30)),
                ("This Month", lambda: self.apply_current_month_filter()),
                ("High Amount (>₹1000)", lambda: self.apply_amount_filter(1000, None)),
                ("Low Amount (<₹100)", lambda: self.apply_amount_filter(None, 100))
            ]

            for filter_name, filter_func in filters:
                btn = QPushButton(filter_name)
                btn.clicked.connect(filter_func)
                btn.setMaximumHeight(25)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e3f2fd;
                        border: 1px solid #2196f3;
                        border-radius: 3px;
                        padding: 2px 8px;
                        font-size: 9pt;
                    }
                    QPushButton:hover {
                        background-color: #bbdefb;
                    }
                """)
                quick_filter_layout.addWidget(btn)

            return quick_filter_frame

        except Exception as e:
            print(f"Error creating quick filter buttons: {e}")
            return QFrame()

    def apply_quick_date_filter(self, days):
        """Apply quick date filter for last N days"""
        try:
            end_date = QDate.currentDate()
            start_date = end_date.addDays(-days)

            self.start_date.setDate(start_date)
            self.end_date.setDate(end_date)
            self.apply_filters()

        except Exception as e:
            print(f"Error applying quick date filter: {e}")

    def apply_current_month_filter(self):
        """Apply filter for current month"""
        try:
            today = QDate.currentDate()
            start_of_month = QDate(today.year(), today.month(), 1)

            self.start_date.setDate(start_of_month)
            self.end_date.setDate(today)
            self.apply_filters()

        except Exception as e:
            print(f"Error applying current month filter: {e}")

    def apply_amount_filter(self, min_amount, max_amount):
        """Apply amount range filter"""
        try:
            if min_amount is not None:
                self.min_amount.setValue(min_amount)
            if max_amount is not None:
                self.max_amount.setValue(max_amount)

            self.apply_filters()

        except Exception as e:
            print(f"Error applying amount filter: {e}")

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        try:
            from PySide6.QtGui import QShortcut, QKeySequence

            # Refresh shortcut
            refresh_shortcut = QShortcut(QKeySequence("F5"), self)
            refresh_shortcut.activated.connect(self.refresh_data)

            # Export shortcut
            export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
            export_shortcut.activated.connect(self.export_summary)

            # Clear filters shortcut
            clear_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
            clear_shortcut.activated.connect(self.clear_filters)

        except Exception as e:
            print(f"Error setting up keyboard shortcuts: {e}")

    def update_theme(self, new_theme):
        """Update theme for summary widget and all child components"""
        self.current_theme = new_theme
        self.apply_theme_styling()

        # Update summary cards
        if hasattr(self, 'summary_cards'):
            for card in self.summary_cards.values():
                if hasattr(card, 'apply_theme'):
                    card.apply_theme(new_theme)
                elif hasattr(card, 'theme'):
                    card.theme = new_theme
                    if hasattr(card, 'apply_theme_styling'):
                        card.apply_theme_styling()

        # Update chart widgets
        chart_widgets = []
        if hasattr(self, 'pie_chart'):
            chart_widgets.append(self.pie_chart)
        if hasattr(self, 'bar_chart'):
            chart_widgets.append(self.bar_chart)
        if hasattr(self, 'line_chart'):
            chart_widgets.append(self.line_chart)
        # CRITICAL FIX: Add category tab chart widgets
        if hasattr(self, 'category_pie_chart'):
            chart_widgets.append(self.category_pie_chart)
        if hasattr(self, 'category_bar_chart'):
            chart_widgets.append(self.category_bar_chart)
        if hasattr(self, 'time_line_chart'):
            chart_widgets.append(self.time_line_chart)

        for widget in chart_widgets:
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme(new_theme)
            elif hasattr(widget, 'current_theme'):
                widget.current_theme = new_theme
                if hasattr(widget, 'update_theme'):
                    widget.update_theme(new_theme)

            # CRITICAL FIX: Force chart redraw with new theme
            if hasattr(widget, 'canvas') and hasattr(widget.canvas, 'draw'):
                widget.canvas.draw()

        # Force update all widgets to apply new theme
        self.update()
        if hasattr(self, 'tab_widget'):
            self.tab_widget.update()
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    widget.update()

        # CRITICAL FIX: Refresh charts with current data to apply new theme
        if hasattr(self, 'current_data') and not self.current_data.empty:
            self.update_charts(self.current_data)
