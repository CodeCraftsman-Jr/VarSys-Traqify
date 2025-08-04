"""
Income Visualization Module
Provides chart widgets for income data visualization
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGroupBox, QGridLayout, QPushButton, QComboBox, QSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import seaborn as sns

# Dynamic theme configuration for matplotlib
def configure_matplotlib_theme(theme='light'):  # Default to light theme
    """Configure matplotlib to match the application theme"""
    if theme == 'dark':
        plt.style.use('dark_background')
        sns.set_palette("husl")
        plt.rcParams.update({
            'figure.facecolor': '#1e1e1e',
            'axes.facecolor': '#252526',
            'axes.edgecolor': '#3e3e42',
            'axes.labelcolor': 'white',
            'text.color': 'white',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'grid.color': '#3e3e42',
            'legend.facecolor': '#252526',
            'legend.edgecolor': '#3e3e42'
        })
    elif theme == 'light':
        plt.style.use('default')
        sns.set_palette("deep")
        plt.rcParams.update({
            'figure.facecolor': '#ffffff',
            'axes.facecolor': '#f9f9f9',
            'axes.edgecolor': '#e0e0e0',
            'axes.labelcolor': 'black',
            'text.color': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black',
            'grid.color': '#e0e0e0',
            'legend.facecolor': '#f9f9f9',
            'legend.edgecolor': '#e0e0e0'
        })
    elif theme == 'colorwave':
        plt.style.use('dark_background')
        sns.set_palette("bright")
        plt.rcParams.update({
            'figure.facecolor': '#0a0a1a',
            'axes.facecolor': '#1a1a2e',
            'axes.edgecolor': '#4a3c5a',
            'axes.labelcolor': 'white',
            'text.color': 'white',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'grid.color': '#4a3c5a',
            'legend.facecolor': '#1a1a2e',
            'legend.edgecolor': '#4a3c5a'
        })

# Note: Theme configuration is now handled per-widget to support dynamic theming
# Global theme configuration removed to prevent conflicts with widget-specific themes


class ChartWidget(QWidget):
    """Base chart widget with common functionality"""
    
    chart_clicked = Signal(dict)  # Signal emitted when chart is clicked
    
    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent)
        self.theme = theme
        self.setup_ui()

    def setup_ui(self):
        """Setup the basic UI structure"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_click)

        layout.addWidget(self.canvas)

        # Apply theme-specific configuration
        self.apply_theme(self.theme)

    def apply_theme(self, theme='dark'):
        """Apply theme-specific styling to the chart"""
        self.theme = theme

        # Configure matplotlib theme globally for this widget
        configure_matplotlib_theme(theme)

        # Get theme colors
        theme_colors = self.get_theme_colors()

        # Apply theme to figure and widget styling
        self.figure.patch.set_facecolor(theme_colors['figure_facecolor'])

        # CRITICAL FIX: Remove hardcoded background colors to let global theme handle it
        # Only set canvas border, let global theme control background
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
            # Default to dark
            return {
                'figure_facecolor': '#1e1e1e',
                'axes_facecolor': '#252526',
                'axes_edgecolor': '#3e3e42',
                'text_color': 'white',
                'grid_color': '#3e3e42'
            }
        
    def on_click(self, event):
        """Handle chart click events"""
        if event.inaxes is not None:
            click_data = {
                'x': event.xdata,
                'y': event.ydata,
                'button': event.button
            }
            self.chart_clicked.emit(click_data)
    
    def clear_chart(self):
        """Clear the chart"""
        self.figure.clear()
        # Reapply theme after clearing
        theme_colors = self.get_theme_colors()
        self.figure.patch.set_facecolor(theme_colors['figure_facecolor'])
        self.canvas.draw()
    
    def save_chart(self, filename: str):
        """Save chart to file"""
        self.figure.savefig(filename, dpi=300, bbox_inches='tight')
    
    def _show_no_data_message(self, title: str):
        """Show no data message"""
        ax = self.figure.add_subplot(111)
        theme_colors = self.get_theme_colors()
        ax.set_facecolor(theme_colors['axes_facecolor'])
        ax.text(0.5, 0.5, 'No data available',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16, color=theme_colors['text_color'])
        ax.set_title(title, color=theme_colors['text_color'])
        ax.axis('off')
        self.canvas.draw()


class IncomePieChartWidget(ChartWidget):
    """Pie chart widget for income source distribution with interactive features"""

    source_clicked = Signal(str)  # Signal emitted when a source is clicked

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent, theme)
        self.data = None
        self.wedges = []
        self.source_names = []
        
    def update_chart(self, data: pd.DataFrame, title: str = "Income Distribution by Source"):
        """Update pie chart with income source data"""
        self.clear_chart()
        
        if data.empty:
            self._show_no_data_message(title)
            return
        
        # Income source columns (excluding metadata columns)
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        # Calculate total for each source
        source_totals = {}
        for source in income_sources:
            if source in data.columns:
                total = data[source].sum()
                if total > 0:
                    # Format source names for display
                    display_name = source.replace('_', ' ').title()
                    if source == 'gp_links':
                        display_name = 'GP Links'
                    elif source == 'id_sales':
                        display_name = 'ID Sales'
                    elif source == 'shadow_fax':
                        display_name = 'Shadow Fax'
                    elif source == 'pc_repair':
                        display_name = 'PC Repair'
                    source_totals[display_name] = total
        
        if not source_totals:
            self._show_no_data_message(title)
            return
        
        # Sort by value
        sorted_sources = dict(sorted(source_totals.items(), key=lambda x: x[1], reverse=True))
        
        # Limit to top 8 sources for readability
        if len(sorted_sources) > 8:
            top_sources = dict(list(sorted_sources.items())[:7])
            others_sum = sum(list(sorted_sources.values())[7:])
            if others_sum > 0:
                top_sources['Others'] = others_sum
            sorted_sources = top_sources
        
        ax = self.figure.add_subplot(111)

        # Get theme colors
        theme_colors = self.get_theme_colors()

        # Set axes background
        ax.set_facecolor(theme_colors['axes_facecolor'])

        # Create pie chart
        labels = list(sorted_sources.keys())
        values = list(sorted_sources.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                         startangle=90, colors=colors,
                                         explode=[0.05] * len(labels))

        # Store wedges and names for click detection
        self.wedges = wedges
        self.source_names = labels

        # Enhance text appearance with theme colors
        for autotext in autotexts:
            autotext.set_color(theme_colors['text_color'])
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)

        for text in texts:
            text.set_fontsize(10)
            text.set_color(theme_colors['text_color'])

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=theme_colors['text_color'])

        # Add total amount in center with theme-aware styling
        total_amount = sum(values)
        ax.text(0, 0, f'Total\n₹{total_amount:,.0f}',
                horizontalalignment='center', verticalalignment='center',
                fontsize=12, fontweight='bold', color=theme_colors['text_color'],
                bbox=dict(boxstyle="round,pad=0.3", facecolor=theme_colors['axes_facecolor'],
                         alpha=0.9, edgecolor=theme_colors['axes_edgecolor']))
        
        self.canvas.draw()


class IncomeBarChartWidget(ChartWidget):
    """Bar chart widget for income analysis with filtering options"""

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent, theme)
        self.chart_type = 'monthly'  # monthly, weekly, daily, source
        
    def update_chart(self, data: pd.DataFrame, chart_type: str = 'monthly',
                    title: str = "Income Analysis", top_n: int = 15):
        """Update bar chart with income data"""
        self.clear_chart()
        self.chart_type = chart_type
        
        if data.empty:
            self._show_no_data_message(title)
            return
        
        ax = self.figure.add_subplot(111)

        # Get theme colors and apply to axes
        theme_colors = self.get_theme_colors()
        ax.set_facecolor(theme_colors['axes_facecolor'])

        if chart_type == 'monthly':
            self._create_monthly_chart(ax, data, title)
        elif chart_type == 'weekly':
            self._create_weekly_chart(ax, data, title)
        elif chart_type == 'daily':
            self._create_daily_chart(ax, data, title, top_n)
        elif chart_type == 'source':
            self._create_source_chart(ax, data, title, top_n)
        
        self.canvas.draw()
    
    def _create_monthly_chart(self, ax, data: pd.DataFrame, title: str):
        """Create monthly income bar chart"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month'] = data_copy['date'].dt.to_period('M')

        monthly_data = data_copy.groupby('month')['earned'].sum().sort_index()

        # Get theme colors
        theme_colors = self.get_theme_colors()

        bars = ax.bar(range(len(monthly_data)), monthly_data.values,
                     color='#2E86AB', alpha=0.8)

        ax.set_xlabel('Month', color=theme_colors['text_color'])
        ax.set_ylabel('Income (₹)', color=theme_colors['text_color'])
        ax.set_title(title, color=theme_colors['text_color'])
        ax.set_xticks(range(len(monthly_data)))
        ax.set_xticklabels([str(month) for month in monthly_data.index], rotation=45, color=theme_colors['text_color'])
        ax.tick_params(colors=theme_colors['text_color'])

        # Add value labels on bars
        for bar, value in zip(bars, monthly_data.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'₹{value:,.0f}', ha='center', va='bottom', fontsize=9, color=theme_colors['text_color'])
    
    def _create_weekly_chart(self, ax, data: pd.DataFrame, title: str):
        """Create weekly income bar chart"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['week'] = data_copy['date'].dt.to_period('W')
        
        weekly_data = data_copy.groupby('week')['earned'].sum().sort_index()
        
        bars = ax.bar(range(len(weekly_data)), weekly_data.values, 
                     color='#A23B72', alpha=0.8)
        
        ax.set_xlabel('Week')
        ax.set_ylabel('Income (₹)')
        ax.set_title(title)
        ax.set_xticks(range(len(weekly_data)))
        ax.set_xticklabels([f'W{i+1}' for i in range(len(weekly_data))], rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, weekly_data.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'₹{value:,.0f}', ha='center', va='bottom', fontsize=9)
    
    def _create_daily_chart(self, ax, data: pd.DataFrame, title: str, top_n: int):
        """Create daily income bar chart"""
        daily_data = data.groupby('date')['earned'].sum().sort_values(ascending=False)
        
        if len(daily_data) > top_n:
            daily_data = daily_data.head(top_n)
        
        bars = ax.bar(range(len(daily_data)), daily_data.values, 
                     color='#F18F01', alpha=0.8)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Income (₹)')
        ax.set_title(title)
        ax.set_xticks(range(len(daily_data)))
        ax.set_xticklabels([str(date) for date in daily_data.index], rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, daily_data.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'₹{value:,.0f}', ha='center', va='bottom', fontsize=8)
    
    def _create_source_chart(self, ax, data: pd.DataFrame, title: str, top_n: int):
        """Create income source bar chart"""
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        source_totals = {}
        for source in income_sources:
            if source in data.columns:
                total = data[source].sum()
                if total > 0:
                    display_name = source.replace('_', ' ').title()
                    if source == 'gp_links':
                        display_name = 'GP Links'
                    elif source == 'id_sales':
                        display_name = 'ID Sales'
                    elif source == 'shadow_fax':
                        display_name = 'Shadow Fax'
                    elif source == 'pc_repair':
                        display_name = 'PC Repair'
                    source_totals[display_name] = total
        
        if not source_totals:
            self._show_no_data_message(title)
            return
        
        # Sort and limit
        sorted_sources = dict(sorted(source_totals.items(), key=lambda x: x[1], reverse=True))
        if len(sorted_sources) > top_n:
            sorted_sources = dict(list(sorted_sources.items())[:top_n])
        
        bars = ax.bar(range(len(sorted_sources)), list(sorted_sources.values()), 
                     color='#C73E1D', alpha=0.8)
        
        ax.set_xlabel('Income Source')
        ax.set_ylabel('Income (₹)')
        ax.set_title(title)
        ax.set_xticks(range(len(sorted_sources)))
        ax.set_xticklabels(list(sorted_sources.keys()), rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, value in zip(bars, sorted_sources.values()):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                   f'₹{value:,.0f}', ha='center', va='bottom', fontsize=9)


class IncomeLineChartWidget(ChartWidget):
    """Line chart widget for income trends over time with zoom and pan functionality"""

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent, theme)
        self.aggregation = 'daily'  # daily, weekly, monthly
        
    def update_chart(self, data: pd.DataFrame, aggregation: str = 'daily',
                    title: str = "Income Trends", date_column: str = 'date',
                    value_column: str = 'earned'):
        """Update line chart with income trend data"""
        self.clear_chart()
        self.aggregation = aggregation
        
        if data.empty:
            self._show_no_data_message(title)
            return
        
        # Ensure date column is datetime
        data = data.copy()
        data[date_column] = pd.to_datetime(data[date_column])
        
        # Aggregate data based on period
        if aggregation == 'daily':
            aggregated = data.groupby(data[date_column].dt.date)[value_column].sum()
        elif aggregation == 'weekly':
            aggregated = data.groupby(data[date_column].dt.to_period('W'))[value_column].sum()
        elif aggregation == 'monthly':
            aggregated = data.groupby(data[date_column].dt.to_period('M'))[value_column].sum()
        else:
            aggregated = data.groupby(data[date_column].dt.date)[value_column].sum()
        
        ax = self.figure.add_subplot(111)
        
        # Create line chart
        ax.plot(aggregated.index, aggregated.values, marker='o', linewidth=2, 
                markersize=6, color='#2E86AB', markerfacecolor='#A23B72')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Income (₹)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis based on aggregation
        if aggregation == 'daily':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        elif aggregation == 'weekly':
            ax.set_xticklabels([f'W{i+1}' for i in range(len(aggregated))], rotation=45)
        elif aggregation == 'monthly':
            ax.set_xticklabels([str(month) for month in aggregated.index], rotation=45)
        
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add trend line
        if len(aggregated) > 1:
            z = np.polyfit(range(len(aggregated)), aggregated.values, 1)
            p = np.poly1d(z)
            ax.plot(aggregated.index, p(range(len(aggregated))), "--", 
                   color='red', alpha=0.8, linewidth=1, label='Trend')
            ax.legend()
        
        self.canvas.draw()


class SummaryCardWidget(QFrame):
    """Summary card widget for displaying key metrics"""

    def __init__(self, title: str, value: str = "₹0", subtitle: str = "", parent=None, theme='light'):  # Default to light theme
        super().__init__(parent)
        self.title = title
        self.theme = theme
        self.value = value
        self.subtitle = subtitle
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the card UI - EXPANDED: Spacious layout for better visual appeal"""
        # EXPANDED: Significantly larger dimensions for better use of space
        self.setMinimumHeight(180)  # Much larger minimum height
        self.setMinimumWidth(200)   # Set minimum width for better proportions
        # Remove maximum height constraint to allow natural expansion

        # Set size policy to expand and fill available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        # EXPANDED: More generous margins for spacious feel
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)  # Increased spacing between elements for better visual hierarchy

        # Title - EXPANDED: Larger font and better spacing
        title_label = QLabel(self.title)
        title_label.setObjectName("summaryCardTitle")
        title_font = QFont()
        title_font.setPointSize(11)  # Larger font for better readability
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)  # Enable word wrapping
        layout.addWidget(title_label)

        # Add spacing after title
        layout.addSpacing(8)

        # Value - EXPANDED: Much larger font for better visual hierarchy
        self.value_label = QLabel(self.value)
        self.value_label.setObjectName("summaryCardValue")
        value_font = QFont()
        value_font.setPointSize(28)  # Much larger font for prominence
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setWordWrap(True)  # Enable word wrapping for long values
        layout.addWidget(self.value_label)

        # Add spacing after value
        layout.addSpacing(5)

        # Subtitle - EXPANDED: Larger font and better spacing
        self.subtitle_label = QLabel(self.subtitle if self.subtitle else "")
        self.subtitle_label.setObjectName("summaryCardSubtitle")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)  # Larger subtitle font
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)  # Enable word wrapping
        layout.addWidget(self.subtitle_label)

        # EXPANDED: More generous stretch for better proportions
        layout.addStretch(2)

        # Set frame style
        self.setFrameStyle(QFrame.Box)
        self.setObjectName("summaryCard")

        # Apply theme styling
        self.apply_theme_styling()

    def apply_theme_styling(self):
        """Apply theme-specific styling to the summary card - FIXED: No hardcoded background colors"""
        # CRITICAL FIX: Remove hardcoded background colors to let global theme handle styling
        # Only set borders and hover effects, let the global theme control background colors
        if self.theme == 'dark':
            self.setStyleSheet("""
                QFrame#summaryCard {
                    border: 2px solid #3e3e42;
                    border-radius: 8px;
                    padding: 10px;
                }
                QFrame#summaryCard:hover {
                    border-color: #0e639c;
                }
            """)
            # Apply dark theme text colors
            self._apply_text_colors('#cccccc', '#ffffff', '#aaaaaa')
        elif self.theme == 'light':
            self.setStyleSheet("""
                QFrame#summaryCard {
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px;
                }
                QFrame#summaryCard:hover {
                    border-color: #0078d4;
                }
            """)
            # Apply light theme text colors
            self._apply_text_colors('#666666', '#333333', '#888888')
        elif self.theme == 'colorwave':
            self.setStyleSheet("""
                QFrame#summaryCard {
                    border: 2px solid #4a3c5a;
                    border-radius: 8px;
                    padding: 10px;
                }
                QFrame#summaryCard:hover {
                    border-color: #e91e63;
                }
            """)
            # Apply colorwave theme text colors (light colors for dark background)
            self._apply_text_colors('#e0e0e0', '#ffffff', '#d0d0d0')

    def _apply_text_colors(self, title_color, value_color, subtitle_color):
        """Apply text colors to all text elements"""
        # Find title label by object name
        title_labels = self.findChildren(QLabel, "summaryCardTitle")
        if title_labels:
            title_labels[0].setStyleSheet(f"color: {title_color};")

        # Apply colors to value and subtitle labels
        if hasattr(self, 'value_label'):
            self.value_label.setStyleSheet(f"color: {value_color};")
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setStyleSheet(f"color: {subtitle_color};")

    def apply_theme(self, theme: str):
        """Apply new theme to the card - CRITICAL FIX: Missing method"""
        self.theme = theme
        self.apply_theme_styling()

    def update_value(self, value: str, subtitle: str = None):
        """Update the card value and subtitle"""
        self.value_label.setText(value)
        if subtitle is not None:
            self.subtitle = subtitle
            self.subtitle_label.setText(subtitle)

    def update_values(self, value: str, subtitle: str = ""):
        """Update the card values - consistent interface with other modules"""
        self.value_label.setText(str(value))
        self.subtitle_label.setText(subtitle)


class IncomeDataProcessor:
    """Utility class for processing income data for visualization"""
    
    @staticmethod
    def calculate_summary_stats(data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics for income data"""
        if data.empty:
            return {
                'total_income': 0,
                'average_daily': 0,
                'best_day': 0,
                'total_days': 0,
                'goal_achievement_rate': 0,
                'current_month': 0,
                'current_week': 0
            }
        
        # Basic stats
        total_income = data['earned'].sum()
        average_daily = data['earned'].mean()
        best_day = data['earned'].max()
        total_days = len(data)
        
        # Goal achievement rate
        goals_met = len(data[data['progress'] >= 100])
        goal_achievement_rate = (goals_met / total_days * 100) if total_days > 0 else 0
        
        # Current month and week
        today = date.today()
        current_month_data = data[pd.to_datetime(data['date']).dt.month == today.month]
        current_month = current_month_data['earned'].sum()
        
        # Current week (last 7 days)
        week_ago = today - timedelta(days=7)
        current_week_data = data[pd.to_datetime(data['date']) >= pd.Timestamp(week_ago)]
        current_week = current_week_data['earned'].sum()
        
        return {
            'total_income': float(total_income),
            'average_daily': float(average_daily),
            'best_day': float(best_day),
            'total_days': total_days,
            'goal_achievement_rate': float(goal_achievement_rate),
            'current_month': float(current_month),
            'current_week': float(current_week)
        }
    
    @staticmethod
    def get_top_income_sources(data: pd.DataFrame, top_n: int = 5) -> Dict[str, float]:
        """Get top income sources"""
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        source_totals = {}
        for source in income_sources:
            if source in data.columns:
                total = data[source].sum()
                if total > 0:
                    display_name = source.replace('_', ' ').title()
                    if source == 'gp_links':
                        display_name = 'GP Links'
                    elif source == 'id_sales':
                        display_name = 'ID Sales'
                    elif source == 'shadow_fax':
                        display_name = 'Shadow Fax'
                    elif source == 'pc_repair':
                        display_name = 'PC Repair'
                    source_totals[display_name] = float(total)
        
        # Sort and return top N
        sorted_sources = dict(sorted(source_totals.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_sources.items())[:top_n])
