"""
Expense Visualization Components
Provides reusable chart and visualization components for expense data
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPalette

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
    """Base widget for matplotlib charts"""

    chart_clicked = Signal(dict)  # Signal emitted when chart is clicked

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent)
        self.theme = theme
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)

        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        # Configure canvas
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # Apply theme-specific configuration
        self.apply_theme(theme)
        
    def apply_theme(self, theme='light'):  # Default to light theme
        """Apply theme-specific styling to the chart - FIXED: No background override"""
        self.theme = theme

        # Configure matplotlib theme globally for this widget
        configure_matplotlib_theme(theme)

        # Get theme colors
        theme_colors = self.get_theme_colors()

        # Apply theme to figure only, let global theme handle widget background
        self.figure.patch.set_facecolor(theme_colors['figure_facecolor'])

        # CRITICAL FIX: Remove background-color overrides to let global theme handle it
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
            # Default to light theme (changed from dark)
            return {
                'figure_facecolor': '#ffffff',
                'axes_facecolor': '#f9f9f9',
                'axes_edgecolor': '#e0e0e0',
                'text_color': 'black',
                'grid_color': '#e0e0e0'
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


class PieChartWidget(ChartWidget):
    """Pie chart widget for category distribution with interactive features"""

    category_clicked = Signal(str)  # Signal emitted when a category is clicked

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent, theme)
        self.data = None
        self.wedges = []
        self.category_names = []
        
    def update_chart(self, data: pd.DataFrame, value_column: str = 'amount', 
                    label_column: str = 'category', title: str = "Expense Distribution"):
        """Update pie chart with new data"""
        self.clear_chart()
        
        if data.empty:
            self._show_no_data_message(title)
            return
            
        # Aggregate data by label column
        aggregated = data.groupby(label_column)[value_column].sum().sort_values(ascending=False)
        
        # Limit to top 10 categories for readability
        if len(aggregated) > 10:
            top_categories = aggregated.head(9)
            others_sum = aggregated.tail(len(aggregated) - 9).sum()
            if others_sum > 0:
                top_categories['Others'] = others_sum
            aggregated = top_categories
        
        # Create pie chart
        ax = self.figure.add_subplot(111)

        # Get theme colors
        theme_colors = self.get_theme_colors()

        # Set axes styling based on theme
        ax.set_facecolor(theme_colors['axes_facecolor'])

        # Generate colors
        colors = sns.color_palette("husl", len(aggregated))

        # Create pie chart with enhanced styling
        wedges, texts, autotexts = ax.pie(
            aggregated.values,
            labels=aggregated.index,
            autopct=lambda pct: f'₹{aggregated.sum() * pct / 100:.0f}\n({pct:.1f}%)',
            startangle=90,
            colors=colors,
            explode=[0.05] * len(aggregated),  # Slight separation
            shadow=True,
            textprops={'fontsize': 9, 'color': theme_colors['text_color']}
        )

        # Enhance text styling with theme colors
        for text in texts:
            text.set_color(theme_colors['text_color'])
            text.set_fontsize(9)

        for autotext in autotexts:
            autotext.set_color(theme_colors['text_color'])
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)

        # Store wedges and category names for click detection
        self.wedges = wedges
        self.category_names = list(aggregated.index)

        # Make wedges clickable
        for i, wedge in enumerate(wedges):
            wedge.set_picker(True)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=theme_colors['text_color'])

        # Store data for click handling
        self.data = aggregated

        # Connect pick event
        self.canvas.mpl_connect('pick_event', self.on_wedge_click)

        self.canvas.draw()

    def on_wedge_click(self, event):
        """Handle wedge click events"""
        try:
            if event.artist in self.wedges:
                wedge_index = self.wedges.index(event.artist)
                if wedge_index < len(self.category_names):
                    category_name = self.category_names[wedge_index]
                    self.category_clicked.emit(category_name)

                    # Visual feedback - temporarily explode the clicked wedge
                    self.highlight_wedge(wedge_index)
        except Exception as e:
            print(f"Error handling wedge click: {e}")

    def highlight_wedge(self, wedge_index):
        """Highlight a specific wedge temporarily"""
        try:
            if wedge_index < len(self.wedges):
                # Reset all wedges
                for wedge in self.wedges:
                    wedge.set_edgecolor('white')
                    wedge.set_linewidth(1)

                # Highlight selected wedge
                selected_wedge = self.wedges[wedge_index]
                selected_wedge.set_edgecolor('red')
                selected_wedge.set_linewidth(3)

                self.canvas.draw()

                # Reset highlight after 2 seconds
                QTimer.singleShot(2000, self.reset_highlight)
        except Exception as e:
            print(f"Error highlighting wedge: {e}")

    def reset_highlight(self):
        """Reset wedge highlighting"""
        try:
            for wedge in self.wedges:
                wedge.set_edgecolor('white')
                wedge.set_linewidth(1)
            self.canvas.draw()
        except Exception as e:
            print(f"Error resetting highlight: {e}")
    
    def _show_no_data_message(self, title: str):
        """Show message when no data is available"""
        ax = self.figure.add_subplot(111)
        theme_colors = self.get_theme_colors()
        ax.set_facecolor(theme_colors['axes_facecolor'])
        ax.text(0.5, 0.5, 'No data available',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14, color=theme_colors['text_color'])
        ax.set_title(title, fontsize=14, fontweight='bold', color=theme_colors['text_color'])
        ax.axis('off')
        self.canvas.draw()


class BarChartWidget(ChartWidget):
    """Bar chart widget for time-based or categorical data with interactive features"""

    bar_clicked = Signal(str, float)  # Signal emitted when a bar is clicked (category, value)

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent, theme)
        self.data = None
        self.bars = []
        self.bar_labels = []
        
    def update_chart(self, data: pd.DataFrame, x_column: str, y_column: str = 'amount',
                    title: str = "Expense Analysis", x_label: str = None, y_label: str = "Amount (₹)",
                    chart_type: str = 'vertical'):
        """Update bar chart with new data"""
        self.clear_chart()
        
        if data.empty:
            self._show_no_data_message(title)
            return
        
        # Aggregate data
        if x_column == 'date':
            # For date-based charts, group by date
            aggregated = data.groupby(x_column)[y_column].sum().sort_index()
        else:
            # For categorical charts, group and sort by value
            aggregated = data.groupby(x_column)[y_column].sum().sort_values(ascending=False)
        
        # Limit to top 15 items for readability
        if len(aggregated) > 15:
            aggregated = aggregated.head(15)
        
        ax = self.figure.add_subplot(111)

        # Get theme colors
        theme_colors = self.get_theme_colors()

        # Set axes styling based on theme
        ax.set_facecolor(theme_colors['axes_facecolor'])

        # Create bar chart
        if chart_type == 'horizontal':
            bars = ax.barh(range(len(aggregated)), aggregated.values,
                          color=sns.color_palette("viridis", len(aggregated)))
            ax.set_yticks(range(len(aggregated)))
            ax.set_yticklabels(aggregated.index, fontsize=9, color=theme_colors['text_color'])
            ax.set_xlabel(y_label or "Amount (₹)", color=theme_colors['text_color'])
            ax.set_ylabel(x_label or x_column.title(), color=theme_colors['text_color'])

            # Add value labels on bars
            for i, (idx, value) in enumerate(aggregated.items()):
                ax.text(value + max(aggregated.values) * 0.01, i, f'₹{value:.0f}',
                       va='center', fontsize=8, color=theme_colors['text_color'])
        else:
            bars = ax.bar(range(len(aggregated)), aggregated.values,
                         color=sns.color_palette("viridis", len(aggregated)))
            ax.set_xticks(range(len(aggregated)))
            ax.set_xticklabels(aggregated.index, rotation=45, ha='right', fontsize=9, color=theme_colors['text_color'])
            ax.set_ylabel(y_label or "Amount (₹)", color=theme_colors['text_color'])
            ax.set_xlabel(x_label or x_column.title(), color=theme_colors['text_color'])

            # Add value labels on bars
            for i, (idx, value) in enumerate(aggregated.items()):
                ax.text(i, value + max(aggregated.values) * 0.01, f'₹{value:.0f}',
                       ha='center', va='bottom', fontsize=8, color=theme_colors['text_color'])

        # Set tick colors
        ax.tick_params(colors=theme_colors['text_color'])

        # Store bars and labels for click detection
        self.bars = bars
        self.bar_labels = list(aggregated.index)

        # Make bars clickable
        for bar in bars:
            bar.set_picker(True)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=theme_colors['text_color'])
        ax.grid(True, alpha=0.3)

        # Format y-axis for currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))

        # Store data for click handling
        self.data = aggregated

        # Connect pick event
        self.canvas.mpl_connect('pick_event', self.on_bar_click)

        plt.tight_layout()
        self.canvas.draw()

    def on_bar_click(self, event):
        """Handle bar click events"""
        try:
            if hasattr(event.artist, 'get_height'):  # Vertical bar
                bar_index = list(self.bars).index(event.artist)
                if bar_index < len(self.bar_labels):
                    label = self.bar_labels[bar_index]
                    value = event.artist.get_height()
                    self.bar_clicked.emit(label, value)
                    self.highlight_bar(bar_index)
            elif hasattr(event.artist, 'get_width'):  # Horizontal bar
                bar_index = list(self.bars).index(event.artist)
                if bar_index < len(self.bar_labels):
                    label = self.bar_labels[bar_index]
                    value = event.artist.get_width()
                    self.bar_clicked.emit(label, value)
                    self.highlight_bar(bar_index)
        except Exception as e:
            print(f"Error handling bar click: {e}")

    def highlight_bar(self, bar_index):
        """Highlight a specific bar temporarily"""
        try:
            if bar_index < len(self.bars):
                # Reset all bars
                for bar in self.bars:
                    bar.set_edgecolor('black')
                    bar.set_linewidth(1)

                # Highlight selected bar
                selected_bar = self.bars[bar_index]
                selected_bar.set_edgecolor('red')
                selected_bar.set_linewidth(3)

                self.canvas.draw()

                # Reset highlight after 2 seconds
                QTimer.singleShot(2000, self.reset_bar_highlight)
        except Exception as e:
            print(f"Error highlighting bar: {e}")

    def reset_bar_highlight(self):
        """Reset bar highlighting"""
        try:
            for bar in self.bars:
                bar.set_edgecolor('black')
                bar.set_linewidth(1)
            self.canvas.draw()
        except Exception as e:
            print(f"Error resetting bar highlight: {e}")
    
    def _show_no_data_message(self, title: str):
        """Show message when no data is available"""
        ax = self.figure.add_subplot(111)
        theme_colors = self.get_theme_colors()
        ax.set_facecolor(theme_colors['axes_facecolor'])
        ax.text(0.5, 0.5, 'No data available',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14, color=theme_colors['text_color'])
        ax.set_title(title, fontsize=14, fontweight='bold', color=theme_colors['text_color'])
        ax.axis('off')
        self.canvas.draw()


class LineChartWidget(ChartWidget):
    """Line chart widget for trend analysis"""

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent, theme)
        self.data = None
        
    def update_chart(self, data: pd.DataFrame, date_column: str = 'date', 
                    value_column: str = 'amount', title: str = "Spending Trends",
                    aggregation: str = 'daily'):
        """Update line chart with trend data"""
        self.clear_chart()
        
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
        
        # Fill area under the curve
        ax.fill_between(aggregated.index, aggregated.values, alpha=0.3, color='#2E86AB')
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_ylabel("Amount (₹)")
        ax.set_xlabel("Date")
        ax.grid(True, alpha=0.3)
        
        # Format y-axis for currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        
        # Format x-axis dates
        if aggregation == 'daily':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(aggregated) // 10)))
        elif aggregation == 'weekly':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        elif aggregation == 'monthly':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        plt.xticks(rotation=45)
        
        # Store data for click handling
        self.data = aggregated
        
        plt.tight_layout()
        self.canvas.draw()
    
    def _show_no_data_message(self, title: str):
        """Show message when no data is available"""
        ax = self.figure.add_subplot(111)
        theme_colors = self.get_theme_colors()
        ax.set_facecolor(theme_colors['axes_facecolor'])
        ax.text(0.5, 0.5, 'No data available',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14, color=theme_colors['text_color'])
        ax.set_title(title, fontsize=14, fontweight='bold', color=theme_colors['text_color'])
        ax.axis('off')
        self.canvas.draw()


class SummaryCardWidget(QFrame):
    """Summary card widget for displaying key metrics"""

    def __init__(self, title: str, value: str = "0", subtitle: str = "",
                 icon: str = "📊", parent=None, theme='light'):  # Default to light theme
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.theme = theme
        self.setup_ui()
        self.update_values(value, subtitle)

    def setup_ui(self):
        """Setup the summary card UI - APPLIED TO DO ANALYTICS APPROACH: Allow natural expansion"""
        self.setObjectName("summaryCard")
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        # APPLIED TO DO ANALYTICS APPROACH: Remove height restrictions to allow cards to expand properly
        self.setMinimumHeight(180)  # Reasonable minimum height
        self.setMinimumWidth(200)   # Reasonable minimum width
        # Remove maximum height constraint to allow natural expansion like To Do Analytics

        # APPLIED TO DO ANALYTICS APPROACH: Allow full expansion
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Apply theme-aware styling
        self.apply_theme_styling()

        layout = QVBoxLayout(self)
        # APPLIED TO DO ANALYTICS APPROACH: More generous margins for spacious professional appearance
        layout.setContentsMargins(25, 22, 25, 22)  # Increased margins for better visual breathing room
        layout.setSpacing(12)  # Increased spacing between elements for better visual hierarchy

        # Header with icon and title - APPLIED TO DO ANALYTICS APPROACH: Spacious layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)  # Increased spacing between icon and title for better separation

        # Icon - APPLIED TO DO ANALYTICS APPROACH: Larger icon for better visual impact and readability
        self.icon_label = QLabel(self.icon)
        self.icon_label.setFont(QFont("Arial", 24))  # Larger icon font for better visibility
        self.icon_label.setFixedSize(40, 40)  # Larger fixed size for better visual impact
        self.icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.icon_label)

        # Title - APPLIED TO DO ANALYTICS APPROACH: Larger font and better spacing for maximum readability
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))  # Larger font for better readability
        # Color will be set by apply_theme_styling()
        self.title_label.setWordWrap(True)  # Enable word wrapping for long titles
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # APPLIED TO DO ANALYTICS APPROACH: Add more spacing after header for better visual separation
        layout.addSpacing(15)  # Increased spacing for better visual hierarchy

        # Value - APPLIED TO DO ANALYTICS APPROACH: Maximum font size for excellent visibility and data prominence
        self.value_label = QLabel("0")
        self.value_label.setFont(QFont("Arial", 32, QFont.Bold))  # Increased from 28 to 32 for maximum prominence
        # Color will be set by apply_theme_styling()
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setWordWrap(True)  # Enable word wrapping for long values
        layout.addWidget(self.value_label)

        # APPLIED TO DO ANALYTICS APPROACH: Add more spacing after value for better visual separation
        layout.addSpacing(8)  # Increased spacing for better visual hierarchy

        # Subtitle - APPLIED TO DO ANALYTICS APPROACH: Larger font for better readability
        self.subtitle_label = QLabel("")
        self.subtitle_label.setFont(QFont("Arial", 11))  # Increased from 10 to 11 for better readability
        # Color will be set by apply_theme_styling()
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)  # Enable word wrapping for long subtitles
        layout.addWidget(self.subtitle_label)

        # APPLIED TO DO ANALYTICS APPROACH: More generous stretch for better proportions and spacing
        layout.addStretch(3)  # Increased stretch for better card proportions

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
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"color: {title_color};")
        if hasattr(self, 'value_label'):
            self.value_label.setStyleSheet(f"color: {value_color};")
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setStyleSheet(f"color: {subtitle_color};")

    def apply_theme(self, theme: str):
        """Apply new theme to the card - CRITICAL FIX: Missing method"""
        self.theme = theme
        self.apply_theme_styling()

    def update_values(self, value: str, subtitle: str = ""):
        """Update the card values"""
        self.value_label.setText(str(value))
        self.subtitle_label.setText(subtitle)

    def set_trend_color(self, trend: str):
        """Set color based on trend (positive, negative, neutral)"""
        if trend == "positive":
            self.value_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        elif trend == "negative":
            self.value_label.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.value_label.setStyleSheet("color: #333; font-weight: bold;")


class ExpenseDataProcessor:
    """Data processing utilities for expense visualizations"""

    @staticmethod
    def prepare_category_data(data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for category-based visualizations"""
        if data.empty:
            return data

        # Group by category and sum amounts
        category_data = data.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
        category_data.columns = ['category', 'total_amount', 'transaction_count', 'avg_amount']
        category_data = category_data.sort_values('total_amount', ascending=False)

        return category_data

    @staticmethod
    def prepare_time_series_data(data: pd.DataFrame, period: str = 'daily') -> pd.DataFrame:
        """Prepare data for time series visualizations"""
        if data.empty:
            return data

        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])

        if period == 'daily':
            grouped = data.groupby(data['date'].dt.date)['amount'].sum()
        elif period == 'weekly':
            grouped = data.groupby(data['date'].dt.to_period('W'))['amount'].sum()
        elif period == 'monthly':
            grouped = data.groupby(data['date'].dt.to_period('M'))['amount'].sum()
        elif period == 'yearly':
            grouped = data.groupby(data['date'].dt.year)['amount'].sum()
        else:
            grouped = data.groupby(data['date'].dt.date)['amount'].sum()

        result = pd.DataFrame({'date': grouped.index, 'amount': grouped.values})
        return result

    @staticmethod
    def calculate_summary_metrics(data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary metrics for expense data"""
        if data.empty:
            return {
                'total_amount': 0,
                'transaction_count': 0,
                'avg_amount': 0,
                'max_amount': 0,
                'min_amount': 0,
                'categories_count': 0,
                'most_expensive_category': 'N/A',
                'most_frequent_category': 'N/A'
            }

        # Validate required columns
        if 'amount' not in data.columns:
            print("WARNING: 'amount' column not found in data")
            return {
                'total_amount': 0,
                'transaction_count': len(data),
                'avg_amount': 0,
                'max_amount': 0,
                'min_amount': 0,
                'categories_count': data['category'].nunique() if 'category' in data.columns else 0,
                'most_expensive_category': 'N/A',
                'most_frequent_category': 'N/A'
            }

        # Ensure amount column is numeric
        amount_data = pd.to_numeric(data['amount'], errors='coerce')
        valid_amounts = amount_data.dropna()

        if valid_amounts.empty:
            print("WARNING: No valid numeric amounts found")
            return {
                'total_amount': 0,
                'transaction_count': len(data),
                'avg_amount': 0,
                'max_amount': 0,
                'min_amount': 0,
                'categories_count': data['category'].nunique() if 'category' in data.columns else 0,
                'most_expensive_category': 'N/A',
                'most_frequent_category': 'N/A'
            }

        metrics = {
            'total_amount': float(valid_amounts.sum()),
            'transaction_count': len(data),
            'avg_amount': float(valid_amounts.mean()),
            'max_amount': float(valid_amounts.max()),
            'min_amount': float(valid_amounts.min()),
            'categories_count': data['category'].nunique() if 'category' in data.columns else 0,
        }

        # Most expensive category (only if category column exists)
        if 'category' in data.columns:
            try:
                # Create a copy with valid amounts for category analysis
                valid_data = data[amount_data.notna()].copy()
                valid_data['amount'] = valid_amounts

                category_totals = valid_data.groupby('category')['amount'].sum()
                metrics['most_expensive_category'] = category_totals.idxmax() if not category_totals.empty else 'N/A'

                # Most frequent category
                category_counts = data['category'].value_counts()
                metrics['most_frequent_category'] = category_counts.idxmax() if not category_counts.empty else 'N/A'
            except Exception as e:
                print(f"WARNING: Error calculating category metrics: {e}")
                metrics['most_expensive_category'] = 'N/A'
                metrics['most_frequent_category'] = 'N/A'
        else:
            metrics['most_expensive_category'] = 'N/A'
            metrics['most_frequent_category'] = 'N/A'

        return metrics

    @staticmethod
    def get_spending_trends(data: pd.DataFrame, days: int = 30) -> Dict[str, Any]:
        """Calculate spending trends over specified period"""
        if data.empty:
            return {'trend': 'neutral', 'change_percent': 0, 'current_period': 0, 'previous_period': 0}

        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])

        # Get current and previous periods
        end_date = data['date'].max()
        current_start = end_date - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        current_period_data = data[data['date'] >= current_start]
        previous_period_data = data[(data['date'] >= previous_start) & (data['date'] < current_start)]

        current_total = current_period_data['amount'].sum()
        previous_total = previous_period_data['amount'].sum()

        if previous_total > 0:
            change_percent = ((current_total - previous_total) / previous_total) * 100
        else:
            change_percent = 0

        if change_percent > 5:
            trend = 'negative'  # Spending increased
        elif change_percent < -5:
            trend = 'positive'  # Spending decreased
        else:
            trend = 'neutral'

        return {
            'trend': trend,
            'change_percent': change_percent,
            'current_period': current_total,
            'previous_period': previous_total
        }

    @staticmethod
    def prepare_heatmap_data(data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for heatmap visualization (day vs hour spending patterns)"""
        if data.empty:
            return pd.DataFrame()

        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
        data['day_of_week'] = data['date'].dt.day_name()
        data['hour'] = data['date'].dt.hour

        # Create pivot table for heatmap
        heatmap_data = data.groupby(['day_of_week', 'hour'])['amount'].sum().unstack(fill_value=0)

        # Reorder days of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(day_order, fill_value=0)

        return heatmap_data

    @staticmethod
    def prepare_comparison_data(data: pd.DataFrame, compare_by: str = 'month') -> pd.DataFrame:
        """Prepare data for period-over-period comparison"""
        if data.empty:
            return pd.DataFrame()

        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])

        if compare_by == 'month':
            data['period'] = data['date'].dt.to_period('M')
        elif compare_by == 'week':
            data['period'] = data['date'].dt.to_period('W')
        elif compare_by == 'quarter':
            data['period'] = data['date'].dt.to_period('Q')
        elif compare_by == 'year':
            data['period'] = data['date'].dt.to_period('Y')
        else:
            data['period'] = data['date'].dt.to_period('M')

        # Group by period and calculate metrics
        comparison_data = data.groupby('period').agg({
            'amount': ['sum', 'mean', 'count'],
            'category': 'nunique'
        }).round(2)

        # Flatten column names
        comparison_data.columns = ['total_amount', 'avg_amount', 'transaction_count', 'unique_categories']
        comparison_data = comparison_data.reset_index()

        # Calculate period-over-period changes
        comparison_data['total_change'] = comparison_data['total_amount'].pct_change() * 100
        comparison_data['avg_change'] = comparison_data['avg_amount'].pct_change() * 100
        comparison_data['count_change'] = comparison_data['transaction_count'].pct_change() * 100

        return comparison_data

    @staticmethod
    def get_top_categories(data: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Get top N categories by spending amount"""
        if data.empty:
            return pd.DataFrame()

        category_data = data.groupby('category').agg({
            'amount': ['sum', 'mean', 'count'],
            'date': ['min', 'max']
        }).round(2)

        # Flatten column names
        category_data.columns = ['total_amount', 'avg_amount', 'transaction_count', 'first_transaction', 'last_transaction']
        category_data = category_data.reset_index()

        # Sort by total amount and get top N
        category_data = category_data.sort_values('total_amount', ascending=False).head(top_n)

        # Calculate percentage of total spending
        total_spending = data['amount'].sum()
        category_data['percentage'] = (category_data['total_amount'] / total_spending * 100).round(2)

        return category_data

    @staticmethod
    def analyze_spending_patterns(data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze spending patterns and return insights"""
        if data.empty:
            return {}

        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])
        data['day_of_week'] = data['date'].dt.day_name()
        data['month'] = data['date'].dt.month_name()
        data['hour'] = data['date'].dt.hour

        patterns = {}

        # Day of week patterns
        day_spending = data.groupby('day_of_week')['amount'].sum()
        patterns['busiest_day'] = day_spending.idxmax()
        patterns['quietest_day'] = day_spending.idxmin()
        patterns['day_spending'] = day_spending.to_dict()

        # Monthly patterns
        month_spending = data.groupby('month')['amount'].sum()
        patterns['highest_month'] = month_spending.idxmax()
        patterns['lowest_month'] = month_spending.idxmin()
        patterns['monthly_spending'] = month_spending.to_dict()

        # Time of day patterns
        hour_spending = data.groupby('hour')['amount'].sum()
        patterns['peak_hour'] = hour_spending.idxmax()
        patterns['quiet_hour'] = hour_spending.idxmin()

        # Category patterns
        category_freq = data['category'].value_counts()
        patterns['most_frequent_category'] = category_freq.index[0] if not category_freq.empty else 'N/A'
        patterns['category_frequency'] = category_freq.head(5).to_dict()

        # Amount patterns
        patterns['avg_transaction'] = data['amount'].mean()
        patterns['median_transaction'] = data['amount'].median()
        patterns['largest_transaction'] = data['amount'].max()
        patterns['smallest_transaction'] = data['amount'].min()

        # Spending consistency
        daily_spending = data.groupby(data['date'].dt.date)['amount'].sum()
        patterns['spending_volatility'] = daily_spending.std() / daily_spending.mean() if daily_spending.mean() > 0 else 0

        return patterns

    @staticmethod
    def prepare_budget_comparison(data: pd.DataFrame, budget_data: Dict[str, float]) -> pd.DataFrame:
        """Compare actual spending vs budget by category"""
        if data.empty:
            return pd.DataFrame()

        # Calculate actual spending by category
        actual_spending = data.groupby('category')['amount'].sum()

        # Create comparison DataFrame
        comparison_data = []

        for category, budget_amount in budget_data.items():
            actual_amount = actual_spending.get(category, 0)
            variance = actual_amount - budget_amount
            variance_percent = (variance / budget_amount * 100) if budget_amount > 0 else 0

            comparison_data.append({
                'category': category,
                'budget': budget_amount,
                'actual': actual_amount,
                'variance': variance,
                'variance_percent': variance_percent,
                'status': 'Over Budget' if variance > 0 else 'Under Budget' if variance < 0 else 'On Budget'
            })

        # Add categories with spending but no budget
        for category in actual_spending.index:
            if category not in budget_data:
                comparison_data.append({
                    'category': category,
                    'budget': 0,
                    'actual': actual_spending[category],
                    'variance': actual_spending[category],
                    'variance_percent': float('inf'),
                    'status': 'No Budget Set'
                })

        return pd.DataFrame(comparison_data)

    @staticmethod
    def calculate_financial_health_score(data: pd.DataFrame, income_amount: float = None) -> Dict[str, Any]:
        """Calculate a financial health score based on spending patterns"""
        if data.empty:
            return {'score': 0, 'factors': {}}

        factors = {}
        score = 100  # Start with perfect score

        # Factor 1: Spending consistency (lower volatility is better)
        daily_spending = data.groupby(pd.to_datetime(data['date']).dt.date)['amount'].sum()
        if len(daily_spending) > 1:
            volatility = daily_spending.std() / daily_spending.mean() if daily_spending.mean() > 0 else 0
            consistency_score = max(0, 100 - (volatility * 50))
            factors['spending_consistency'] = consistency_score
            score = (score + consistency_score) / 2

        # Factor 2: Category diversification (moderate diversification is good)
        category_counts = data['category'].value_counts()
        diversification = len(category_counts)
        if diversification < 3:
            diversification_score = 60  # Too few categories
        elif diversification > 15:
            diversification_score = 70  # Too many categories
        else:
            diversification_score = 90  # Good diversification

        factors['category_diversification'] = diversification_score
        score = (score + diversification_score) / 2

        # Factor 3: Income ratio (if income provided)
        if income_amount and income_amount > 0:
            total_spending = data['amount'].sum()
            spending_ratio = total_spending / income_amount

            if spending_ratio < 0.5:
                income_ratio_score = 100  # Excellent
            elif spending_ratio < 0.7:
                income_ratio_score = 80   # Good
            elif spending_ratio < 0.9:
                income_ratio_score = 60   # Fair
            else:
                income_ratio_score = 30   # Poor

            factors['income_ratio'] = income_ratio_score
            score = (score + income_ratio_score) / 2

        # Factor 4: Large transaction frequency (fewer large transactions is better)
        total_amount = data['amount'].sum()
        large_transactions = data[data['amount'] > (total_amount * 0.1)]  # Transactions > 10% of total
        large_transaction_ratio = len(large_transactions) / len(data)

        if large_transaction_ratio < 0.05:
            large_tx_score = 100
        elif large_transaction_ratio < 0.1:
            large_tx_score = 80
        elif large_transaction_ratio < 0.2:
            large_tx_score = 60
        else:
            large_tx_score = 40

        factors['large_transaction_control'] = large_tx_score
        score = (score + large_tx_score) / 2

        return {
            'score': round(score, 1),
            'factors': factors,
            'grade': 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D' if score >= 60 else 'F'
        }
