"""
Basic Chart Widgets for Expense Analysis
Simple matplotlib-based charts that work reliably
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QComboBox, QPushButton, QSpinBox, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class BasicChartWidget(QWidget):
    """Base widget for matplotlib charts"""

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent)
        self.theme = theme
        # CRITICAL FIX: Increase figure size for better visibility
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.canvas)

        # Configure canvas
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # CRITICAL FIX: Set minimum size to ensure charts are fully visible
        self.setMinimumSize(400, 300)

        # Apply theme-specific configuration
        self.apply_theme(theme)

    def apply_theme(self, theme='light'):  # Default to light theme
        """Apply theme-specific styling to the chart - FIXED: No background override"""
        self.theme = theme
        print(f"🎨 DEBUG: BasicChartWidget.apply_theme called with theme: {theme}")

        # Get theme colors
        theme_colors = self.get_theme_colors()
        print(f"🎨 DEBUG: Theme colors: {theme_colors}")

        # Apply theme to figure only, let global theme handle widget background
        self.figure.patch.set_facecolor(theme_colors['figure_facecolor'])

        # CRITICAL FIX: Remove background-color overrides to let global theme handle it
        # Only set canvas background for the chart area itself
        self.canvas.setStyleSheet("border: none;")

        # Remove widget background override - let global theme handle it
        self.setStyleSheet("")

        # Clear any existing plots and redraw with new theme
        if hasattr(self, 'figure') and self.figure.axes:
            for ax in self.figure.axes:
                ax.set_facecolor(theme_colors['axes_facecolor'])
                ax.tick_params(colors=theme_colors['text_color'])
                ax.xaxis.label.set_color(theme_colors['text_color'])
                ax.yaxis.label.set_color(theme_colors['text_color'])
                ax.title.set_color(theme_colors['text_color'])

        # Refresh the canvas
        self.canvas.draw()

    def get_theme_colors(self):
        """Get color scheme for current theme"""
        if self.theme == 'dark':
            return {
                'figure_facecolor': '#1e1e1e',
                'axes_facecolor': '#252526',
                'axes_edgecolor': '#3e3e42',
                'text_color': 'white',
                'grid_color': '#3e3e42'
            }
        elif self.theme == 'light':
            return {
                'figure_facecolor': '#ffffff',
                'axes_facecolor': '#f9f9f9',
                'axes_edgecolor': '#e0e0e0',
                'text_color': 'black',
                'grid_color': '#e0e0e0'
            }
        elif self.theme == 'colorwave':
            return {
                'figure_facecolor': '#0a0a1a',
                'axes_facecolor': '#1a1a2e',
                'axes_edgecolor': '#4a3c5a',
                'text_color': 'white',
                'grid_color': '#4a3c5a'
            }
        else:
            # Default to light theme (changed from dark)
            return {
                'figure_facecolor': '#ffffff',
                'axes_facecolor': '#f9f9f9',
                'axes_edgecolor': '#e0e0e0',
                'text_color': 'black',
                'grid_color': '#e0e0e0'
            }
        
    def clear_chart(self):
        """Clear the chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No data available', 
               ha='center', va='center', transform=ax.transAxes, 
               fontsize=14, color='gray')
        ax.axis('off')
        self.canvas.draw()


class BasicPieChartWidget(BasicChartWidget):
    """Basic pie chart widget with interactive controls"""

    def __init__(self, parent=None, theme='light'):  # CRITICAL FIX: Default to light theme
        super().__init__(parent, theme)
        self.current_data = pd.DataFrame()
        self.view_mode = 'category'  # 'category' or 'subcategory'
        self.selected_category = None
        self.setup_controls()

    def setup_controls(self):
        """Setup interactive controls"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # View mode selector
        self.view_combo = QComboBox()
        self.view_combo.addItems(['Category View', 'Sub-Category View'])
        self.view_combo.currentTextChanged.connect(self.on_view_changed)

        # Back button for sub-category view
        self.back_button = QPushButton('← Back to Categories')
        self.back_button.setEnabled(False)
        self.back_button.clicked.connect(self.go_back_to_categories)

        # Refresh button
        self.refresh_button = QPushButton('🔄 Refresh')
        self.refresh_button.clicked.connect(self.refresh_chart)

        controls_layout.addWidget(QLabel('View:'))
        controls_layout.addWidget(self.view_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.back_button)
        controls_layout.addWidget(self.refresh_button)

        # Insert controls at the top
        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Expense Distribution"):
        """Update pie chart"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        try:
            self.figure.clear()

            if self.view_mode == 'category':
                self._create_category_chart(data, title)
            else:
                self._create_subcategory_chart(data, title)

        except Exception as e:
            print(f"Error creating pie chart: {e}")
            self.clear_chart()

    def _create_category_chart(self, data: pd.DataFrame, title: str):
        """Create category-based pie chart"""
        # Aggregate by category
        category_data = data.groupby('category')['amount'].sum().sort_values(ascending=False)

        # Limit to top 8 categories for readability
        if len(category_data) > 8:
            top_categories = category_data.head(7)
            others_sum = category_data.tail(len(category_data) - 7).sum()
            if others_sum > 0:
                top_categories['Others'] = others_sum
            category_data = top_categories

        # Create pie chart
        ax = self.figure.add_subplot(111)
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_data)))

        wedges, texts, autotexts = ax.pie(
            category_data.values,
            labels=None,  # We'll add labels separately for better control
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )

        # Add title
        theme_colors = self.get_theme_colors()
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color=theme_colors['text_color'])

        # Create legend with category names and amounts
        legend_labels = [f'{cat}: ₹{amount:,.0f}' for cat, amount in category_data.items()]
        legend = ax.legend(wedges, legend_labels, title="Categories", loc="center left",
                          bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)
        # Apply theme colors to legend
        legend.get_title().set_color(theme_colors['text_color'])
        for text in legend.get_texts():
            text.set_color(theme_colors['text_color'])

        # Make percentage text visible with proper theme colors
        for autotext in autotexts:
            # Use contrasting color for percentage text
            text_color = 'white' if theme_colors['text_color'] == 'black' else 'black'
            autotext.set_color(text_color)
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
            # Use theme-appropriate background for text boxes
            bg_color = theme_colors['axes_facecolor']
            border_color = theme_colors['axes_edgecolor']
            autotext.set_bbox(dict(boxstyle="round,pad=0.3", facecolor=bg_color, alpha=0.9, edgecolor=border_color))

        plt.tight_layout()
        self.canvas.draw()

    def _create_subcategory_chart(self, data: pd.DataFrame, title: str):
        """Create sub-category based pie chart"""
        if self.selected_category:
            # Filter for selected category
            filtered_data = data[data['category'] == self.selected_category]
            if filtered_data.empty:
                self.clear_chart()
                return
            subcategory_data = filtered_data.groupby('sub_category')['amount'].sum().sort_values(ascending=False)
            chart_title = f"{title} - {self.selected_category}"
        else:
            # Show all sub-categories
            subcategory_data = data.groupby('sub_category')['amount'].sum().sort_values(ascending=False)
            chart_title = f"{title} - All Sub-Categories"

        # Limit to top 10 sub-categories
        if len(subcategory_data) > 10:
            top_subcategories = subcategory_data.head(9)
            others_sum = subcategory_data.tail(len(subcategory_data) - 9).sum()
            if others_sum > 0:
                top_subcategories['Others'] = others_sum
            subcategory_data = top_subcategories

        # Create pie chart
        ax = self.figure.add_subplot(111)
        colors = plt.cm.Pastel1(np.linspace(0, 1, len(subcategory_data)))

        wedges, texts, autotexts = ax.pie(
            subcategory_data.values,
            labels=None,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )

        # Add title
        theme_colors = self.get_theme_colors()
        ax.set_title(chart_title, fontsize=16, fontweight='bold', pad=20, color=theme_colors['text_color'])

        # Create legend
        legend_labels = [f'{subcat}: ₹{amount:,.0f}' for subcat, amount in subcategory_data.items()]
        legend = ax.legend(wedges, legend_labels, title="Sub-Categories", loc="center left",
                          bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
        # Apply theme colors to legend
        legend.get_title().set_color(theme_colors['text_color'])
        for text in legend.get_texts():
            text.set_color(theme_colors['text_color'])

        # Make percentage text visible with proper theme colors
        for autotext in autotexts:
            # Use contrasting color for percentage text
            text_color = 'white' if theme_colors['text_color'] == 'black' else 'black'
            autotext.set_color(text_color)
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
            # Use theme-appropriate background for text boxes
            bg_color = theme_colors['axes_facecolor']
            border_color = theme_colors['axes_edgecolor']
            autotext.set_bbox(dict(boxstyle="round,pad=0.3", facecolor=bg_color, alpha=0.9, edgecolor=border_color))

        plt.tight_layout()
        self.canvas.draw()

    def on_view_changed(self, view_text: str):
        """Handle view mode change"""
        if view_text == 'Category View':
            self.view_mode = 'category'
            self.selected_category = None
            self.back_button.setEnabled(False)
        else:
            self.view_mode = 'subcategory'
            self.back_button.setEnabled(self.selected_category is not None)

        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def go_back_to_categories(self):
        """Go back to category view"""
        self.view_combo.setCurrentText('Category View')

    def refresh_chart(self):
        """Refresh the chart with current data"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)


class BasicBarChartWidget(BasicChartWidget):
    """Basic bar chart widget with interactive controls"""

    def __init__(self, parent=None, theme='light'):  # CRITICAL FIX: Default to light theme
        super().__init__(parent, theme)
        self.current_data = pd.DataFrame()
        self.group_by = 'category'
        self.sort_order = 'desc'
        self.show_count = 10
        self.setup_controls()

    def setup_controls(self):
        """Setup interactive controls"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # Group by selector
        self.group_combo = QComboBox()
        self.group_combo.addItems(['Category', 'Sub-Category', 'Transaction Mode', 'Monthly'])
        self.group_combo.currentTextChanged.connect(self.on_group_changed)

        # Sort order selector
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Highest First', 'Lowest First'])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)

        # Count selector
        self.count_spin = QSpinBox()
        self.count_spin.setRange(5, 20)
        self.count_spin.setValue(10)
        self.count_spin.valueChanged.connect(self.on_count_changed)

        # Refresh button
        self.refresh_button = QPushButton('🔄 Refresh')
        self.refresh_button.clicked.connect(self.refresh_chart)

        controls_layout.addWidget(QLabel('Group By:'))
        controls_layout.addWidget(self.group_combo)
        controls_layout.addWidget(QLabel('Sort:'))
        controls_layout.addWidget(self.sort_combo)
        controls_layout.addWidget(QLabel('Show Top:'))
        controls_layout.addWidget(self.count_spin)
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_button)

        # Insert controls at the top
        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Expense Analysis"):
        """Update bar chart"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        try:
            self.figure.clear()

            # Prepare data based on grouping
            if self.group_by == 'category':
                grouped_data = data.groupby('category')['amount'].sum()
                x_label = 'Category'
            elif self.group_by == 'sub-category':
                grouped_data = data.groupby('sub_category')['amount'].sum()
                x_label = 'Sub-Category'
            elif self.group_by == 'transaction mode':
                grouped_data = data.groupby('transaction_mode')['amount'].sum()
                x_label = 'Transaction Mode'
            else:  # monthly
                data_copy = data.copy()
                data_copy['month'] = pd.to_datetime(data_copy['date']).dt.strftime('%Y-%m')
                grouped_data = data_copy.groupby('month')['amount'].sum()
                x_label = 'Month'

            # Sort data
            if self.sort_order == 'desc':
                grouped_data = grouped_data.sort_values(ascending=False)
            else:
                grouped_data = grouped_data.sort_values(ascending=True)

            # Limit to specified count
            grouped_data = grouped_data.head(self.show_count)

            # Create bar chart
            ax = self.figure.add_subplot(111)
            theme_colors = self.get_theme_colors()
            bars = ax.bar(range(len(grouped_data)), grouped_data.values,
                         color='#2E86AB', alpha=0.8, edgecolor=theme_colors['text_color'], linewidth=0.5)

            # Set title and labels with better visibility
            ax.set_title(f"{title} - Top {len(grouped_data)} by {x_label}",
                        fontsize=16, fontweight='bold', pad=20, color=theme_colors['text_color'])
            ax.set_xlabel(x_label, fontsize=12, fontweight='bold', color=theme_colors['text_color'])
            ax.set_ylabel('Amount (₹)', fontsize=12, fontweight='bold', color=theme_colors['text_color'])

            # Set x-axis labels
            ax.set_xticks(range(len(grouped_data)))
            labels = [str(label)[:15] + '...' if len(str(label)) > 15 else str(label)
                     for label in grouped_data.index]
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10, color=theme_colors['text_color'])

            # Format y-axis with better visibility
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            ax.tick_params(axis='y', labelsize=10, colors=theme_colors['text_color'])
            ax.tick_params(axis='x', labelsize=10, colors=theme_colors['text_color'])

            # Add value labels on bars with theme styling
            for bar, value in zip(bars, grouped_data.values):
                height = bar.get_height()
                # Use contrasting color for value labels
                label_color = 'white' if theme_colors['text_color'] == 'black' else 'black'
                bg_color = theme_colors['axes_facecolor']
                border_color = theme_colors['axes_edgecolor']
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'₹{value:,.0f}', ha='center', va='bottom', fontsize=9,
                       fontweight='bold', color=label_color,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor=bg_color, alpha=0.9, edgecolor=border_color))

            # Add grid for better readability
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_axisbelow(True)

            plt.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Error creating bar chart: {e}")
            self.clear_chart()

    def on_group_changed(self, group_text: str):
        """Handle group by change"""
        self.group_by = group_text.lower()
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_sort_changed(self, sort_text: str):
        """Handle sort order change"""
        self.sort_order = 'desc' if sort_text == 'Highest First' else 'asc'
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_count_changed(self, count: int):
        """Handle count change"""
        self.show_count = count
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def refresh_chart(self):
        """Refresh the chart with current data"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)


class BasicLineChartWidget(BasicChartWidget):
    """Basic line chart widget with interactive controls"""

    def __init__(self, parent=None, theme='light'):  # CRITICAL FIX: Default to light theme
        super().__init__(parent, theme)
        self.current_data = pd.DataFrame()
        self.time_period = 'daily'
        self.days_to_show = 30
        self.show_trend = True
        self.setup_controls()

    def setup_controls(self):
        """Setup interactive controls"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # Time period selector
        self.period_combo = QComboBox()
        self.period_combo.addItems(['Daily', 'Weekly', 'Monthly'])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)

        # Days to show selector
        self.days_spin = QSpinBox()
        self.days_spin.setRange(7, 90)
        self.days_spin.setValue(30)
        self.days_spin.setSuffix(' days')
        self.days_spin.valueChanged.connect(self.on_days_changed)

        # Trend line checkbox
        self.trend_check = QCheckBox('Show Trend Line')
        self.trend_check.setChecked(True)
        self.trend_check.toggled.connect(self.on_trend_toggled)

        # Refresh button
        self.refresh_button = QPushButton('🔄 Refresh')
        self.refresh_button.clicked.connect(self.refresh_chart)

        controls_layout.addWidget(QLabel('Period:'))
        controls_layout.addWidget(self.period_combo)
        controls_layout.addWidget(QLabel('Show Last:'))
        controls_layout.addWidget(self.days_spin)
        controls_layout.addWidget(self.trend_check)
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_button)

        # Insert controls at the top
        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Expense Trends"):
        """Update line chart"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        try:
            self.figure.clear()

            # Ensure date column is datetime
            data = data.copy()
            data['date'] = pd.to_datetime(data['date'])

            # Filter to recent data based on days_to_show
            cutoff_date = data['date'].max() - pd.Timedelta(days=self.days_to_show)
            recent_data = data[data['date'] >= cutoff_date]

            # Aggregate based on time period
            if self.time_period == 'daily':
                time_data = recent_data.groupby(recent_data['date'].dt.date)['amount'].sum().sort_index()
                x_label = 'Date'
            elif self.time_period == 'weekly':
                recent_data['week'] = recent_data['date'].dt.to_period('W')
                time_data = recent_data.groupby('week')['amount'].sum().sort_index()
                x_label = 'Week'
            else:  # monthly
                recent_data['month'] = recent_data['date'].dt.to_period('M')
                time_data = recent_data.groupby('month')['amount'].sum().sort_index()
                x_label = 'Month'

            if time_data.empty:
                self.clear_chart()
                return

            # Create line chart
            ax = self.figure.add_subplot(111)

            # Main line
            theme_colors = self.get_theme_colors()
            marker_edge_color = theme_colors['text_color']
            line = ax.plot(time_data.index, time_data.values, marker='o', linewidth=3,
                          markersize=6, color='#2E86AB', markerfacecolor='#A23B72',
                          markeredgecolor=marker_edge_color, markeredgewidth=2, label='Daily Expenses')

            # Add trend line if enabled
            if self.show_trend and len(time_data) > 3:
                # Calculate trend line
                x_numeric = np.arange(len(time_data))
                z = np.polyfit(x_numeric, time_data.values, 1)
                p = np.poly1d(z)
                ax.plot(time_data.index, p(x_numeric), "--", color='#F18F01',
                       linewidth=2, alpha=0.8, label='Trend')

            # Set title and labels with better visibility
            ax.set_title(f"{title} - Last {self.days_to_show} Days ({self.time_period.title()})",
                        fontsize=16, fontweight='bold', pad=20, color=theme_colors['text_color'])
            ax.set_xlabel(x_label, fontsize=12, fontweight='bold', color=theme_colors['text_color'])
            ax.set_ylabel('Amount (₹)', fontsize=12, fontweight='bold', color=theme_colors['text_color'])

            # Format axes with better visibility
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            ax.tick_params(axis='both', labelsize=10, colors=theme_colors['text_color'])

            # Rotate x-axis labels for better readability
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

            # Add grid for better readability
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)

            # Add legend if trend line is shown
            if self.show_trend and len(time_data) > 3:
                ax.legend(loc='upper left', fontsize=10)

            # Add data point labels for small datasets
            if len(time_data) <= 10:
                for i, (date, value) in enumerate(time_data.items()):
                    ax.annotate(f'₹{value:,.0f}',
                               (date, value),
                               textcoords="offset points",
                               xytext=(0,10),
                               ha='center',
                               fontsize=8,
                               bbox=dict(boxstyle="round,pad=0.3", facecolor='#252526', alpha=0.9, edgecolor='#3e3e42'))

            plt.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Error creating line chart: {e}")
            self.clear_chart()

    def on_period_changed(self, period_text: str):
        """Handle time period change"""
        self.time_period = period_text.lower()
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_days_changed(self, days: int):
        """Handle days to show change"""
        self.days_to_show = days
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_trend_toggled(self, checked: bool):
        """Handle trend line toggle"""
        self.show_trend = checked
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def refresh_chart(self):
        """Refresh the chart with current data"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)


class BasicDashboardWidget(QWidget):
    """Basic dashboard with multiple charts and interactive controls"""

    def __init__(self, parent=None, theme='light'):  # CRITICAL FIX: Accept theme parameter
        super().__init__(parent)
        self.theme = theme  # Store theme for passing to child charts
        print(f"🎨 DEBUG: BasicDashboardWidget created with theme: {theme}")
        self.current_data = pd.DataFrame()
        self.setup_ui()

    def setup_ui(self):
        """Setup the dashboard UI with scrolling capability"""
        # Main layout for the widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # CRITICAL FIX: Create scroll area to handle large content with mouse wheel support
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # CRITICAL FIX: Enable mouse wheel scrolling
        scroll_area.setFocusPolicy(Qt.WheelFocus)  # Allow scroll area to receive wheel events
        scroll_area.setAttribute(Qt.WA_AcceptTouchEvents, False)  # Disable touch to avoid conflicts

        # Create content widget that will be scrollable
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Set minimum size for content to ensure proper scrolling
        content_widget.setMinimumSize(1000, 2200)  # Increased height for 3 vertically stacked charts

        # Header with title and controls
        header_layout = QHBoxLayout()

        # Title
        title_label = QLabel("📊 Expense Analytics Dashboard")
        title_label.setAlignment(Qt.AlignLeft)
        # Note: Title color will be handled by global theme, removing hardcoded color
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")

        # Global refresh button
        self.global_refresh_button = QPushButton('🔄 Refresh All Charts')
        self.global_refresh_button.clicked.connect(self.refresh_all_charts)
        self.global_refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2E86AB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1F5F7A;
            }
        """)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.global_refresh_button)

        layout.addLayout(header_layout)

        # Summary stats section
        self.create_summary_section(layout)

        # Charts layout - CRITICAL FIX: Changed to vertical stacking for more horizontal space
        charts_layout = QVBoxLayout()

        # First chart - Pie chart (full width)
        print(f"🎨 DEBUG: Creating pie chart with theme: {self.theme}")
        self.pie_chart = BasicPieChartWidget(theme=self.theme)
        # CRITICAL FIX: Increase minimum height for better visibility
        self.pie_chart.setMinimumHeight(550)
        self.pie_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.pie_chart)

        # Second chart - Bar chart (full width)
        print(f"🎨 DEBUG: Creating bar chart with theme: {self.theme}")
        self.bar_chart = BasicBarChartWidget(theme=self.theme)
        # CRITICAL FIX: Increase minimum height for better visibility
        self.bar_chart.setMinimumHeight(550)
        self.bar_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.bar_chart)

        # Third chart - Line chart (full width)
        print(f"🎨 DEBUG: Creating line chart with theme: {self.theme}")
        self.line_chart = BasicLineChartWidget(theme=self.theme)
        # CRITICAL FIX: Increase minimum height for better visibility
        self.line_chart.setMinimumHeight(550)
        self.line_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.line_chart)

        # Store chart widgets for later event filter installation
        self.chart_widgets = [self.pie_chart, self.bar_chart, self.line_chart]

        layout.addLayout(charts_layout)

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Store scroll area reference for event filtering
        self.scroll_area = scroll_area

        # CRITICAL FIX: Install event filter recursively on all widgets to enable mouse wheel scrolling everywhere
        self._install_event_filters_recursively(content_widget)

        # CRITICAL FIX: Also install event filters on chart widgets specifically
        self._install_chart_event_filters()

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)

    def create_summary_section(self, layout):
        """Create summary statistics section"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        summary_layout = QHBoxLayout(summary_frame)

        # Create summary labels
        self.total_label = QLabel("Total: ₹0")
        self.count_label = QLabel("Transactions: 0")
        self.avg_label = QLabel("Average: ₹0")
        self.max_label = QLabel("Highest: ₹0")

        # Style summary labels
        for label in [self.total_label, self.count_label, self.avg_label, self.max_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #2E86AB;
                    padding: 5px 10px;
                    border-radius: 4px;
                    border: 1px solid #2E86AB;
                }
            """)

        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(self.count_label)
        summary_layout.addWidget(self.avg_label)
        summary_layout.addWidget(self.max_label)
        summary_layout.addStretch()

        layout.addWidget(summary_frame)

    def update_dashboard(self, data: pd.DataFrame):
        """Update all charts in the dashboard"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_dashboard()
            return

        try:
            # Update summary statistics
            self.update_summary_stats(data)

            # Update all charts
            self.pie_chart.update_chart(data, "Category Distribution")
            self.bar_chart.update_chart(data, "Top Categories")
            self.line_chart.update_chart(data, "Daily Spending Trends")

        except Exception as e:
            print(f"Error updating dashboard: {e}")
            self.clear_dashboard()

    def update_theme(self, new_theme):
        """Update theme for dashboard and all child charts - CRITICAL FIX"""
        self.theme = new_theme

        # Update all chart widgets
        if hasattr(self, 'pie_chart'):
            self.pie_chart.theme = new_theme
            self.pie_chart.apply_theme(new_theme)
        if hasattr(self, 'bar_chart'):
            self.bar_chart.theme = new_theme
            self.bar_chart.apply_theme(new_theme)
        if hasattr(self, 'line_chart'):
            self.line_chart.theme = new_theme
            self.line_chart.apply_theme(new_theme)

    def update_summary_stats(self, data: pd.DataFrame):
        """Update summary statistics"""
        try:
            total_amount = data['amount'].sum()
            transaction_count = len(data)
            avg_amount = data['amount'].mean()
            max_amount = data['amount'].max()

            self.total_label.setText(f"Total: ₹{total_amount:,.0f}")
            self.count_label.setText(f"Transactions: {transaction_count:,}")
            self.avg_label.setText(f"Average: ₹{avg_amount:,.0f}")
            self.max_label.setText(f"Highest: ₹{max_amount:,.0f}")

        except Exception as e:
            print(f"Error updating summary stats: {e}")
            self.total_label.setText("Total: ₹0")
            self.count_label.setText("Transactions: 0")
            self.avg_label.setText("Average: ₹0")
            self.max_label.setText("Highest: ₹0")

    def _install_event_filters_recursively(self, widget):
        """Install event filter recursively on all child widgets"""
        try:
            # Install event filter on the current widget
            widget.installEventFilter(self)

            # Recursively install on all child widgets
            children = widget.findChildren(QWidget)
            for child in children:
                child.installEventFilter(self)

        except Exception as e:
            print(f"Warning: Could not install event filter on widget {widget}: {e}")

    def _install_chart_event_filters(self):
        """Install event filters specifically on chart widgets and their children"""
        if hasattr(self, 'chart_widgets'):
            for chart_widget in self.chart_widgets:
                try:
                    # Install on the chart widget itself
                    chart_widget.installEventFilter(self)

                    # Install on all children of the chart widget (including matplotlib canvases)
                    for child in chart_widget.findChildren(QWidget):
                        child.installEventFilter(self)


                except Exception as e:
                    print(f"Warning: Could not install event filter on chart widget {chart_widget}: {e}")

    def wheelEvent(self, event):
        """Override wheel event to ensure scrolling works everywhere in the widget"""
        if hasattr(self, 'scroll_area'):
            # Forward wheel events directly to the scroll area
            self.scroll_area.wheelEvent(event)
            event.accept()  # Mark event as handled
        else:
            super().wheelEvent(event)

    def eventFilter(self, obj, event):
        """Event filter to enable mouse wheel scrolling over all child widgets"""
        if event.type() == QEvent.Wheel and hasattr(self, 'scroll_area'):
            # Forward wheel events to the scroll area for consistent scrolling
            self.scroll_area.wheelEvent(event)
            return True  # Event handled, prevent further propagation
        return super().eventFilter(obj, event)

    def refresh_all_charts(self):
        """Refresh all charts with current data"""
        if not self.current_data.empty:
            self.update_dashboard(self.current_data)

    def clear_dashboard(self):
        """Clear all charts and summary"""
        self.pie_chart.clear_chart()
        self.bar_chart.clear_chart()
        self.line_chart.clear_chart()

        # Clear summary stats
        self.total_label.setText("Total: ₹0")
        self.count_label.setText("Transactions: 0")
        self.avg_label.setText("Average: ₹0")
        self.max_label.setText("Highest: ₹0")
