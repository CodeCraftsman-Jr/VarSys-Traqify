"""
Interactive Chart Widgets for Expense Analysis
Advanced interactive visualizations using Plotly and PyQtGraph
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QComboBox, QPushButton, QSlider, QCheckBox, QSpinBox, QDateEdit,
    QGroupBox, QGridLayout, QSplitter, QScrollArea, QTabWidget, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate
from PySide6.QtGui import QFont, QPalette
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    print("QWebEngineView not available. Interactive charts will use alternative display method.")
    WEB_ENGINE_AVAILABLE = False
    QWebEngineView = None

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

from .visualization import ExpenseDataProcessor


class PlotlyWidget(QWidget):
    """Base widget for Plotly charts embedded in Qt"""

    chart_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = 'light'  # Default to light theme
        self.setup_ui()
        self.current_data = pd.DataFrame()

    def get_theme_colors(self):
        """Get current theme colors - CRITICAL FIX for theme awareness"""
        # Try to get theme from parent or application
        app = QApplication.instance()
        theme = 'light'  # Default to light since config shows light theme

        # CRITICAL FIX: Prioritize the current_theme attribute if it exists
        if hasattr(self, 'current_theme') and self.current_theme:
            theme = self.current_theme
        elif hasattr(app, 'current_theme'):
            theme = app.current_theme
        else:
            # Try to get from main window
            main_window = None
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'config') and hasattr(widget.config, 'theme'):
                    theme = widget.config.theme
                    break

            # Fallback: check palette for theme detection
            if theme == 'light':  # Keep light as detected
                palette = app.palette() if app else QPalette()
                bg_color = palette.color(QPalette.Window)
                # Simple heuristic: if background is dark, assume dark theme
                detected_theme = 'dark' if bg_color.lightness() < 128 else 'light'
                print(f"DEBUG: Detected theme from palette: {detected_theme}, bg lightness: {bg_color.lightness()}")
                theme = detected_theme

        print(f"DEBUG: Using theme '{theme}' for expense charts")

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
        background = colors.get('background', '#ffffff')  # Default to white for light theme
        border_color = colors.get('border', '#e0e0e0')  # Default border for light theme

        print(f"DEBUG: Applying web view styling with background: {background}")

        # CRITICAL FIX: Set web view background to match theme with maximum specificity
        # This fixes the black background issue in chart containers
        self.web_view.setStyleSheet(f"""
            QWebEngineView {{
                background-color: {background} !important;
                background: {background} !important;
                border: 1px solid {border_color};
                min-height: 400px;
                min-width: 450px;
                border-radius: 4px;
            }}
            QWebEngineView * {{
                background-color: {background} !important;
                background: {background} !important;
            }}
        """)

        # NUCLEAR OPTION: Also set the web view page background
        if hasattr(self.web_view, 'page'):
            page = self.web_view.page()
            if page:
                page.setBackgroundColor(background)

    def update_theme(self, new_theme):
        """Update theme for the chart widget - CRITICAL FIX: Missing method"""
        self.current_theme = new_theme

        # Apply web view styling with new theme
        if hasattr(self, 'web_view'):
            self.apply_web_view_styling()

        # Update fallback label color if it exists
        if hasattr(self, 'fallback_label'):
            colors = self.get_theme_colors()
            text_color = colors.get('text', colors.get('text_color', '#666666'))
            self.fallback_label.setStyleSheet(f"color: {text_color}; font-size: 10px; padding: 5px;")

        # Refresh current chart with new theme
        if hasattr(self, 'current_data') and not self.current_data.empty:
            # Re-render the chart with the new theme
            if hasattr(self, 'update_chart') and callable(getattr(self, 'update_chart')):
                # For charts that have their own update_chart method
                try:
                    self.update_chart(self.current_data)
                except:
                    pass
        
    def setup_ui(self):
        """Setup the widget UI - EXPANDED: Better responsive sizing for chart visibility"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Small margins for better layout

        # CRITICAL FIX: Dynamic sizing with reasonable minimum size
        self.setMinimumSize(500, 450)  # Increased minimum height for better content visibility
        # Set size policy to expand and fill available space - CRITICAL for dynamic sizing
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if WEB_ENGINE_AVAILABLE:
            # Create web view for Plotly
            self.web_view = QWebEngineView()
            self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # CRITICAL FIX: Dynamic sizing - remove fixed constraints, use minimum for usability
            self.web_view.setMinimumSize(450, 400)  # Reasonable minimum for chart readability

            # CRITICAL FIX: Apply theme-aware styling to web view to fix black background
            # Remove hardcoded styling - let apply_web_view_styling handle theme-aware colors
            self.apply_web_view_styling()

            layout.addWidget(self.web_view)
            print("Setting up WebEngine view for", self.__class__.__name__)
        else:
            # Fallback to matplotlib-based chart
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure

            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addWidget(self.canvas)

            # Add a label to indicate fallback mode
            self.fallback_label = QLabel("📊 Fallback Chart Mode (Install PySide6-WebEngine for full interactivity)")
            self.fallback_label.setAlignment(Qt.AlignCenter)
            # Color will be set by theme
            self.fallback_label.setStyleSheet("font-size: 10px; padding: 5px;")
            layout.addWidget(self.fallback_label)

    def apply_theme_to_plotly_fig(self, fig):
        """Apply current theme colors to a Plotly figure - CRITICAL FIX for text colors"""
        colors = self.get_theme_colors()

        # CRITICAL FIX: Handle different color key formats gracefully
        # Some get_theme_colors() methods use different key names
        background = colors.get('background', colors.get('figure_facecolor', '#ffffff'))  # Default to white for light theme
        secondary_bg = colors.get('secondary_background', colors.get('axes_facecolor', '#f9f9f9'))
        text_color = colors.get('text', colors.get('text_color', '#000000'))  # Default to black for light theme
        border_color = colors.get('border', colors.get('axes_edgecolor', '#e0e0e0'))

        print(f"DEBUG: Applying Plotly theme - background: {background}, text: {text_color}")

        fig.update_layout(
            plot_bgcolor=background,  # Use same background for plot and paper
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
                font=dict(color=text_color),
                bgcolor=background,
                bordercolor=border_color
            ),
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=80, r=60, t=80, b=80, pad=10),
            autosize=True
        )
        return fig

    def generate_theme_aware_html(self, fig):
        """Generate theme-aware HTML for Plotly charts - CRITICAL FIX for chart backgrounds"""
        colors = self.get_theme_colors()
        background = colors.get('background', colors.get('figure_facecolor', '#ffffff'))  # Default to white for light theme

        print(f"DEBUG: Generating HTML with background: {background}")

        # Generate base HTML
        html_str = fig.to_html(include_plotlyjs='cdn')

        # CRITICAL FIX: Use SIMPLE CSS that doesn't interfere with chart visibility
        theme_css = f"""
        <style>
            /* Simple background fix without breaking chart elements */
            html, body {{
                background-color: {background} !important;
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
            }}

            /* Only target main containers, not chart elements */
            .plotly-graph-div {{
                background-color: {background} !important;
                width: 100% !important;
                height: 100% !important;
            }}

            /* Ensure chart is visible */
            .js-plotly-plot {{
                width: 100% !important;
                height: 100% !important;
            }}

            /* Specifically target any black or dark backgrounds */
            [style*="background-color: black"],
            [style*="background-color: #000"],
            [style*="background-color: rgb(0,0,0)"],
            [style*="background: black"],
            [style*="background: #000"],
            [style*="background: rgb(0,0,0)"] {{
                background-color: {background} !important;
                background: {background} !important;
            }}
        </style>
        """

        # Insert CSS right after <head> tag
        head_end = html_str.find('</head>')
        if head_end != -1:
            html_str = html_str[:head_end] + theme_css + html_str[head_end:]
            print(f"DEBUG: Successfully inserted CSS into HTML")
        else:
            print(f"DEBUG: Could not find </head> tag in HTML")

        # NUCLEAR OPTION: Also modify the body tag to force background
        body_start = html_str.find('<body')
        if body_start != -1:
            body_end = html_str.find('>', body_start)
            if body_end != -1:
                # Replace body tag with styled version
                new_body_tag = f'<body style="background-color: {background} !important; margin: 0; padding: 0;"'
                html_str = html_str[:body_start] + new_body_tag + html_str[body_end:]
                print(f"DEBUG: Modified body tag with background: {background}")

        return html_str

    def update_chart(self, fig):
        """Update the chart with a new Plotly figure"""
        try:
            # CRITICAL FIX: Apply theme colors to figure instead of hardcoded dark theme
            fig = self.apply_theme_to_plotly_fig(fig)

            if WEB_ENGINE_AVAILABLE and hasattr(self, 'web_view'):
                # CRITICAL FIX: Use theme-aware HTML generation
                html_str = self.generate_theme_aware_html(fig)
                self.web_view.setHtml(html_str)
                # CRITICAL FIX: Ensure the web view is visible and updated
                self.web_view.show()
                self.web_view.update()
            else:
                # Fallback to matplotlib
                self._create_matplotlib_fallback(fig)

        except Exception as e:
            self._show_error_message(str(e))

    def _create_matplotlib_fallback(self, plotly_fig):
        """Create a matplotlib version of the plotly chart"""
        if not hasattr(self, 'figure'):
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Extract data from plotly figure
        if plotly_fig.data:
            trace = plotly_fig.data[0]

            if trace.type == 'pie':
                # Create pie chart
                ax.pie(trace.values, labels=trace.labels, autopct='%1.1f%%')
                ax.set_title(plotly_fig.layout.title.text if plotly_fig.layout.title else "Chart")

            elif trace.type == 'scatter':
                # Create line/scatter plot
                ax.plot(trace.x, trace.y, marker='o' if trace.mode == 'markers' else '-')
                ax.set_xlabel(plotly_fig.layout.xaxis.title.text if plotly_fig.layout.xaxis.title else "X")
                ax.set_ylabel(plotly_fig.layout.yaxis.title.text if plotly_fig.layout.yaxis.title else "Y")
                ax.set_title(plotly_fig.layout.title.text if plotly_fig.layout.title else "Chart")

            elif trace.type == 'bar':
                # Create bar chart
                ax.bar(trace.x, trace.y)
                ax.set_xlabel(plotly_fig.layout.xaxis.title.text if plotly_fig.layout.xaxis.title else "X")
                ax.set_ylabel(plotly_fig.layout.yaxis.title.text if plotly_fig.layout.yaxis.title else "Y")
                ax.set_title(plotly_fig.layout.title.text if plotly_fig.layout.title else "Chart")

            else:
                # Generic fallback
                ax.text(0.5, 0.5, f'Chart type: {trace.type}\n(Fallback mode)',
                       ha='center', va='center', transform=ax.transAxes)

        self.canvas.draw()

    def _show_error_message(self, error_msg):
        """Show error message in appropriate widget"""
        if WEB_ENGINE_AVAILABLE and hasattr(self, 'web_view'):
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        margin: 0; padding: 20px; background-color: white;
                        font-family: Arial, sans-serif; text-align: center;
                        display: flex; align-items: center; justify-content: center;
                        height: 100vh;
                    }}
                    .error {{ color: #d32f2f; font-size: 16px; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h3>Chart Error</h3>
                    <p>Unable to display chart</p>
                    <p><small>{error_msg}</small></p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)
        elif hasattr(self, 'figure'):
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Chart Error:\n{error_msg}',
                   ha='center', va='center', transform=ax.transAxes, color='red')
            ax.axis('off')
            self.canvas.draw()

    def clear_chart(self):
        """Clear the chart"""
        try:
            if WEB_ENGINE_AVAILABLE and hasattr(self, 'web_view'):
                empty_fig = go.Figure()
                empty_fig.add_annotation(
                    text="No data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                empty_fig.update_layout(
                    showlegend=False,
                    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
                )
                # Apply theme colors to empty chart
                empty_fig = self.apply_theme_to_plotly_fig(empty_fig)
                self.update_chart(empty_fig)
            elif hasattr(self, 'figure'):
                # Clear matplotlib figure
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'No data available',
                       ha='center', va='center', transform=ax.transAxes,
                       fontsize=14, color='gray')
                ax.axis('off')
                self.canvas.draw()
        except Exception as e:
            pass  # Silently handle errors


class InteractivePieChartWidget(PlotlyWidget):
    """Interactive pie chart with drill-down capabilities"""
    
    category_selected = Signal(str, str)  # category, sub_category
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drill_down_level = 'category'  # 'category' or 'sub_category'
        self.selected_category = None
        self.setup_controls()
        
    def setup_controls(self):
        """Setup control widgets"""
        # Insert controls at the top
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Drill-down controls
        self.level_combo = QComboBox()
        self.level_combo.addItems(['Category View', 'Sub-Category View'])
        self.level_combo.currentTextChanged.connect(self.on_level_changed)
        
        self.back_button = QPushButton('← Back to Categories')
        self.back_button.setEnabled(False)
        self.back_button.clicked.connect(self.go_back_to_categories)
        
        controls_layout.addWidget(QLabel('View:'))
        controls_layout.addWidget(self.level_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.back_button)
        
        # Insert controls at the beginning of the layout
        self.layout().insertWidget(0, controls_frame)
    
    def update_chart(self, data: pd.DataFrame, title: str = "Expense Distribution"):
        """Update pie chart with drill-down capability"""
        print(f"DEBUG: InteractivePieChartWidget.update_chart called with {len(data)} records, title: {title}")
        self.current_data = data.copy()

        if data.empty:
            print("DEBUG: Data is empty, clearing chart")
            self.clear_chart()
            return

        print(f"DEBUG: Creating pie chart with drill_down_level: {self.drill_down_level}")
        if self.drill_down_level == 'category':
            self._create_category_pie_chart(data, title)
        else:
            self._create_subcategory_pie_chart(data, title)
        print("DEBUG: Pie chart creation completed")
    
    def _create_category_pie_chart(self, data: pd.DataFrame, title: str):
        """Create category-level pie chart"""
        # Aggregate by category
        category_data = data.groupby('category')['amount'].sum().sort_values(ascending=False)

        # Limit to top 10 categories, group others
        if len(category_data) > 10:
            top_categories = category_data.head(9)
            others_sum = category_data.tail(len(category_data) - 9).sum()
            if others_sum > 0:
                top_categories['Others'] = others_sum
            category_data = top_categories
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=category_data.index,
            values=category_data.values,
            hole=0.3,
            hovertemplate='<b>%{label}</b><br>' +
                         'Amount: ₹%{value:,.0f}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>',
            textinfo='label+percent',
            textposition='auto',
            marker=dict(
                colors=px.colors.qualitative.Set3,
                line=dict(width=2)
            )
        )])
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            font=dict(size=12),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=40, r=160, t=80, b=40)  # Increased right margin for legend, top for title
        )

        # CRITICAL FIX: Apply theme colors instead of hardcoded dark colors
        fig = self.apply_theme_to_plotly_fig(fig)

        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)
    
    def _create_subcategory_pie_chart(self, data: pd.DataFrame, title: str):
        """Create sub-category level pie chart"""
        if self.selected_category:
            # Filter data for selected category
            filtered_data = data[data['category'] == self.selected_category]
            if filtered_data.empty:
                self.clear_chart()
                return
            
            # Aggregate by sub-category
            subcategory_data = filtered_data.groupby('sub_category')['amount'].sum().sort_values(ascending=False)
            title = f"{title} - {self.selected_category}"
        else:
            # Show all sub-categories
            subcategory_data = data.groupby('sub_category')['amount'].sum().sort_values(ascending=False)
        
        # Limit to top 15 sub-categories
        if len(subcategory_data) > 15:
            top_subcategories = subcategory_data.head(14)
            others_sum = subcategory_data.tail(len(subcategory_data) - 14).sum()
            if others_sum > 0:
                top_subcategories['Others'] = others_sum
            subcategory_data = top_subcategories
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=subcategory_data.index,
            values=subcategory_data.values,
            hole=0.3,
            hovertemplate='<b>%{label}</b><br>' +
                         'Amount: ₹%{value:,.0f}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>',
            textinfo='label+percent',
            textposition='auto',
            marker=dict(
                colors=px.colors.qualitative.Pastel,
                line=dict(width=2)
            )
        )])
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            font=dict(size=12),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=40, r=160, t=80, b=40)  # Increased right margin for legend, top for title
        )

        # CRITICAL FIX: Apply theme colors instead of hardcoded colors
        fig = self.apply_theme_to_plotly_fig(fig)

        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)
    
    def on_level_changed(self, level_text: str):
        """Handle level change"""
        if level_text == 'Category View':
            self.drill_down_level = 'category'
            self.selected_category = None
            self.back_button.setEnabled(False)
        else:
            self.drill_down_level = 'sub_category'
            self.back_button.setEnabled(self.selected_category is not None)
        
        # Refresh chart with current data
        if not self.current_data.empty:
            self.update_chart(self.current_data)
    
    def go_back_to_categories(self):
        """Go back to category view"""
        self.level_combo.setCurrentText('Category View')
        self.selected_category = None
        self.back_button.setEnabled(False)
        
        # Refresh chart
        if not self.current_data.empty:
            self.update_chart(self.current_data)
    
    def drill_down_to_category(self, category: str):
        """Drill down to a specific category"""
        self.selected_category = category
        self.level_combo.setCurrentText('Sub-Category View')
        self.back_button.setEnabled(True)
        
        # Refresh chart
        if not self.current_data.empty:
            self.update_chart(self.current_data)


class InteractiveTimeSeriesWidget(PlotlyWidget):
    """Interactive time-series chart with zoom and pan"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aggregation_level = 'daily'
        self.setup_controls()
        
    def setup_controls(self):
        """Setup control widgets"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Aggregation level
        self.aggregation_combo = QComboBox()
        self.aggregation_combo.addItems(['Daily', 'Weekly', 'Monthly'])
        self.aggregation_combo.currentTextChanged.connect(self.on_aggregation_changed)
        
        # Date range controls
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        self.apply_filter_btn = QPushButton('Apply Filter')
        self.apply_filter_btn.clicked.connect(self.apply_date_filter)
        
        controls_layout.addWidget(QLabel('Aggregation:'))
        controls_layout.addWidget(self.aggregation_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel('From:'))
        controls_layout.addWidget(self.start_date)
        controls_layout.addWidget(QLabel('To:'))
        controls_layout.addWidget(self.end_date)
        controls_layout.addWidget(self.apply_filter_btn)
        
        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Expense Trends Over Time"):
        """Update time-series chart with zoom and pan capabilities"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        # Ensure date column is datetime
        data = data.copy()
        data['date'] = pd.to_datetime(data['date'])

        # Apply date filtering if needed
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        data = data[(data['date'].dt.date >= start_date) & (data['date'].dt.date <= end_date)]

        if data.empty:
            self.clear_chart()
            return

        # Aggregate data based on level
        if self.aggregation_level == 'daily':
            aggregated = data.groupby(data['date'].dt.date)['amount'].sum()
            x_values = aggregated.index
            date_format = '%Y-%m-%d'
        elif self.aggregation_level == 'weekly':
            data['week'] = data['date'].dt.to_period('W')
            aggregated = data.groupby('week')['amount'].sum()
            x_values = [str(week) for week in aggregated.index]
            date_format = 'Week %U, %Y'
        else:  # monthly
            data['month'] = data['date'].dt.to_period('M')
            aggregated = data.groupby('month')['amount'].sum()
            x_values = [str(month) for month in aggregated.index]
            date_format = '%Y-%m'

        # Create line chart with multiple traces for better analysis
        fig = go.Figure()

        # Main trend line
        fig.add_trace(go.Scatter(
            x=x_values,
            y=aggregated.values,
            mode='lines+markers',
            name='Total Expenses',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=6, color='#A23B72'),
            hovertemplate='<b>Date:</b> %{x}<br>' +
                         '<b>Amount:</b> ₹%{y:,.0f}<br>' +
                         '<extra></extra>'
        ))

        # Add moving average if daily data
        if self.aggregation_level == 'daily' and len(aggregated) > 7:
            moving_avg = aggregated.rolling(window=7, center=True).mean()
            fig.add_trace(go.Scatter(
                x=x_values,
                y=moving_avg.values,
                mode='lines',
                name='7-Day Moving Average',
                line=dict(color='#F18F01', width=2, dash='dash'),
                hovertemplate='<b>Date:</b> %{x}<br>' +
                             '<b>7-Day Avg:</b> ₹%{y:,.0f}<br>' +
                             '<extra></extra>'
            ))

        # Update layout with zoom and pan capabilities
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis=dict(
                title=f'{self.aggregation_level.title()} Period',
                showgrid=True,
                rangeslider=dict(visible=True),
                type='date' if self.aggregation_level == 'daily' else 'category'
            ),
            yaxis=dict(
                title='Amount (₹)',
                showgrid=True,
                tickformat=',.0f'
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=80, r=40, t=120, b=80)  # Increased all margins, especially top for legend
        )

        # CRITICAL FIX: Apply theme colors instead of hardcoded colors
        fig = self.apply_theme_to_plotly_fig(fig)

        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def on_aggregation_changed(self, level_text: str):
        """Handle aggregation level change"""
        self.aggregation_level = level_text.lower()

        # Refresh chart with current data
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def apply_date_filter(self):
        """Apply date range filter"""
        if not self.current_data.empty:
            self.update_chart(self.current_data)


class InteractiveBarChartWidget(PlotlyWidget):
    """Interactive bar chart with filtering capabilities"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_type = 'category'
        self.sort_order = 'desc'
        self.show_top_n = 15
        self.setup_controls()

    def setup_controls(self):
        """Setup control widgets"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # Chart type
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Category', 'Sub-Category', 'Transaction Mode', 'Monthly'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        # Sort order
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Highest First', 'Lowest First'])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)

        # Top N filter
        self.top_n_spin = QSpinBox()
        self.top_n_spin.setRange(5, 50)
        self.top_n_spin.setValue(15)
        self.top_n_spin.valueChanged.connect(self.on_top_n_changed)

        controls_layout.addWidget(QLabel('Group By:'))
        controls_layout.addWidget(self.type_combo)
        controls_layout.addWidget(QLabel('Sort:'))
        controls_layout.addWidget(self.sort_combo)
        controls_layout.addWidget(QLabel('Show Top:'))
        controls_layout.addWidget(self.top_n_spin)
        controls_layout.addStretch()

        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Expense Analysis"):
        """Update bar chart with filtering capabilities"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        # Prepare data based on chart type
        if self.chart_type == 'category':
            aggregated = data.groupby('category')['amount'].sum()
            x_label = 'Category'
        elif self.chart_type == 'sub-category':
            aggregated = data.groupby('sub_category')['amount'].sum()
            x_label = 'Sub-Category'
        elif self.chart_type == 'transaction mode':
            aggregated = data.groupby('transaction_mode')['amount'].sum()
            x_label = 'Transaction Mode'
        else:  # monthly
            data_copy = data.copy()
            data_copy['month'] = pd.to_datetime(data_copy['date']).dt.strftime('%Y-%m')
            aggregated = data_copy.groupby('month')['amount'].sum()
            x_label = 'Month'

        # Sort data
        if self.sort_order == 'desc':
            aggregated = aggregated.sort_values(ascending=False)
        else:
            aggregated = aggregated.sort_values(ascending=True)

        # Limit to top N
        if len(aggregated) > self.show_top_n:
            aggregated = aggregated.head(self.show_top_n)

        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=aggregated.index,
            y=aggregated.values,
            marker=dict(
                color=aggregated.values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Amount (₹)")
            ),
            hovertemplate='<b>%{x}</b><br>' +
                         'Amount: ₹%{y:,.0f}<br>' +
                         '<extra></extra>',
            text=[f'₹{val:,.0f}' for val in aggregated.values],
            textposition='auto'
        )])

        fig.update_layout(
            title=dict(text=f"{title} - {x_label}", x=0.5, font=dict(size=16)),
            xaxis=dict(
                title=x_label,
                tickangle=-45 if len(aggregated) > 8 else 0
            ),
            yaxis=dict(
                title='Amount (₹)',
                tickformat=',.0f'
            ),
            showlegend=False,
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=80, r=40, t=100, b=150)  # Increased all margins, especially bottom for rotated labels
        )

        # CRITICAL FIX: Apply theme colors instead of hardcoded colors
        fig = self.apply_theme_to_plotly_fig(fig)

        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def on_type_changed(self, type_text: str):
        """Handle chart type change"""
        self.chart_type = type_text.lower()

        # Refresh chart with current data
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_sort_changed(self, sort_text: str):
        """Handle sort order change"""
        self.sort_order = 'desc' if sort_text == 'Highest First' else 'asc'

        # Refresh chart with current data
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_top_n_changed(self, value: int):
        """Handle top N change"""
        self.show_top_n = value

        # Refresh chart with current data
        if not self.current_data.empty:
            self.update_chart(self.current_data)


class InteractiveScatterPlotWidget(PlotlyWidget):
    """Interactive scatter plot for correlation analysis"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_metric = 'amount'
        self.y_metric = 'frequency'
        self.color_by = 'category'
        self.setup_controls()

    def setup_controls(self):
        """Setup control widgets"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # X-axis metric
        self.x_combo = QComboBox()
        self.x_combo.addItems(['Amount', 'Frequency', 'Average Amount'])
        self.x_combo.currentTextChanged.connect(self.on_x_changed)

        # Y-axis metric
        self.y_combo = QComboBox()
        self.y_combo.addItems(['Frequency', 'Amount', 'Average Amount'])
        self.y_combo.setCurrentText('Frequency')
        self.y_combo.currentTextChanged.connect(self.on_y_changed)

        # Color by
        self.color_combo = QComboBox()
        self.color_combo.addItems(['Category', 'Transaction Mode', 'Month'])
        self.color_combo.currentTextChanged.connect(self.on_color_changed)

        controls_layout.addWidget(QLabel('X-Axis:'))
        controls_layout.addWidget(self.x_combo)
        controls_layout.addWidget(QLabel('Y-Axis:'))
        controls_layout.addWidget(self.y_combo)
        controls_layout.addWidget(QLabel('Color By:'))
        controls_layout.addWidget(self.color_combo)
        controls_layout.addStretch()

        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Expense Correlation Analysis"):
        """Update scatter plot for correlation analysis"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        # Prepare data for scatter plot
        if self.color_by == 'category':
            group_col = 'category'
        elif self.color_by == 'transaction mode':
            group_col = 'transaction_mode'
        else:  # month
            data_copy = data.copy()
            data_copy['month'] = pd.to_datetime(data_copy['date']).dt.strftime('%Y-%m')
            group_col = 'month'
            data = data_copy

        # Aggregate data by group
        agg_data = data.groupby(group_col).agg({
            'amount': ['sum', 'mean', 'count']
        }).round(2)

        agg_data.columns = ['total_amount', 'avg_amount', 'frequency']
        agg_data = agg_data.reset_index()

        # Determine x and y values
        x_values = self._get_metric_values(agg_data, self.x_metric)
        y_values = self._get_metric_values(agg_data, self.y_metric)

        # Create scatter plot
        fig = go.Figure(data=[go.Scatter(
            x=x_values,
            y=y_values,
            mode='markers',
            marker=dict(
                size=agg_data['frequency'] * 2,  # Size based on frequency
                color=agg_data['total_amount'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Total Amount (₹)"),
                sizemode='diameter',
                sizeref=2.*max(agg_data['frequency'])/40**2,
                sizemin=4,
                line=dict(width=2)
            ),
            text=agg_data[group_col],
            hovertemplate='<b>%{text}</b><br>' +
                         f'{self.x_metric.title()}: %{{x:,.0f}}<br>' +
                         f'{self.y_metric.title()}: %{{y:,.0f}}<br>' +
                         'Total Amount: ₹%{marker.color:,.0f}<br>' +
                         'Frequency: %{marker.size}<br>' +
                         '<extra></extra>'
        )])

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis=dict(
                title=f'{self.x_metric.title()}',
                showgrid=True
            ),
            yaxis=dict(
                title=f'{self.y_metric.title()}',
                showgrid=True
            ),
            showlegend=False,
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=80, r=80, t=100, b=80)
        )

        # CRITICAL FIX: Apply theme colors instead of hardcoded colors
        fig = self.apply_theme_to_plotly_fig(fig)

        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _get_metric_values(self, data: pd.DataFrame, metric: str):
        """Get values for a specific metric"""
        if metric == 'amount':
            return data['total_amount']
        elif metric == 'frequency':
            return data['frequency']
        else:  # average amount
            return data['avg_amount']

    def on_x_changed(self, metric_text: str):
        """Handle X-axis metric change"""
        self.x_metric = metric_text.lower()
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_y_changed(self, metric_text: str):
        """Handle Y-axis metric change"""
        self.y_metric = metric_text.lower()
        if not self.current_data.empty:
            self.update_chart(self.current_data)

    def on_color_changed(self, color_text: str):
        """Handle color grouping change"""
        self.color_by = color_text.lower()
        if not self.current_data.empty:
            self.update_chart(self.current_data)


class InteractiveHeatmapWidget(PlotlyWidget):
    """Interactive heatmap for spending patterns"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.heatmap_type = 'category_month'
        self.setup_controls()

    def setup_controls(self):
        """Setup control widgets"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # Heatmap type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            'Category vs Month',
            'Category vs Day of Week',
            'Transaction Mode vs Month',
            'Hour vs Day of Week'
        ])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        controls_layout.addWidget(QLabel('Heatmap Type:'))
        controls_layout.addWidget(self.type_combo)
        controls_layout.addStretch()

        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Spending Patterns Heatmap"):
        """Update heatmap for spending patterns"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        # Prepare data based on heatmap type
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])

        if self.heatmap_type == 'category_month':
            data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')
            pivot_data = data_copy.pivot_table(
                values='amount', index='category', columns='month',
                aggfunc='sum', fill_value=0
            )
            x_label, y_label = 'Month', 'Category'

        elif self.heatmap_type == 'category_day':
            data_copy['day_of_week'] = data_copy['date'].dt.day_name()
            pivot_data = data_copy.pivot_table(
                values='amount', index='category', columns='day_of_week',
                aggfunc='sum', fill_value=0
            )
            # Reorder days of week
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot_data = pivot_data.reindex(columns=[day for day in day_order if day in pivot_data.columns])
            x_label, y_label = 'Day of Week', 'Category'

        elif self.heatmap_type == 'transaction_mode_month':
            data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')
            pivot_data = data_copy.pivot_table(
                values='amount', index='transaction_mode', columns='month',
                aggfunc='sum', fill_value=0
            )
            x_label, y_label = 'Month', 'Transaction Mode'

        else:  # hour_day
            # Extract hour from date (assuming we have time info, otherwise use random hours for demo)
            data_copy['hour'] = data_copy['date'].dt.hour
            data_copy['day_of_week'] = data_copy['date'].dt.day_name()
            pivot_data = data_copy.pivot_table(
                values='amount', index='hour', columns='day_of_week',
                aggfunc='sum', fill_value=0
            )
            # Reorder days of week
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot_data = pivot_data.reindex(columns=[day for day in day_order if day in pivot_data.columns])
            x_label, y_label = 'Day of Week', 'Hour of Day'

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='Viridis',
            hoverongaps=False,
            hovertemplate='<b>%{y}</b> - <b>%{x}</b><br>' +
                         'Amount: ₹%{z:,.0f}<br>' +
                         '<extra></extra>',
            colorbar=dict(title="Amount (₹)")
        ))

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis=dict(title=x_label, side='bottom'),
            yaxis=dict(title=y_label),
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=120, r=80, t=100, b=120)  # Extra margins for heatmap labels
        )

        # CRITICAL FIX: Apply theme colors instead of hardcoded colors
        fig = self.apply_theme_to_plotly_fig(fig)

        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def on_type_changed(self, type_text: str):
        """Handle heatmap type change"""
        type_mapping = {
            'Category vs Month': 'category_month',
            'Category vs Day of Week': 'category_day',
            'Transaction Mode vs Month': 'transaction_mode_month',
            'Hour vs Day of Week': 'hour_day'
        }
        self.heatmap_type = type_mapping.get(type_text, 'category_month')

        if not self.current_data.empty:
            self.update_chart(self.current_data)


class InteractiveTreemapWidget(PlotlyWidget):
    """Interactive treemap for hierarchical category breakdown"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.show_subcategories = True
        self.setup_controls()

    def setup_controls(self):
        """Setup control widgets"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # Show subcategories toggle
        self.subcategory_check = QCheckBox('Show Sub-Categories')
        self.subcategory_check.setChecked(True)
        self.subcategory_check.toggled.connect(self.on_subcategory_toggled)

        controls_layout.addWidget(self.subcategory_check)
        controls_layout.addStretch()

        self.layout().insertWidget(0, controls_frame)

    def update_chart(self, data: pd.DataFrame, title: str = "Category Breakdown Treemap"):
        """Update treemap for hierarchical category breakdown"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_chart()
            return

        if self.show_subcategories:
            # Create hierarchical treemap with categories and sub-categories
            treemap_data = []

            # Add root
            total_amount = data['amount'].sum()
            treemap_data.append({
                'ids': 'Total',
                'labels': 'Total Expenses',
                'parents': '',
                'values': total_amount
            })

            # Add categories
            category_totals = data.groupby('category')['amount'].sum()
            for category, amount in category_totals.items():
                treemap_data.append({
                    'ids': f'cat_{category}',
                    'labels': category,
                    'parents': 'Total',
                    'values': amount
                })

            # Add sub-categories
            subcategory_totals = data.groupby(['category', 'sub_category'])['amount'].sum()
            for (category, subcategory), amount in subcategory_totals.items():
                treemap_data.append({
                    'ids': f'subcat_{category}_{subcategory}',
                    'labels': subcategory,
                    'parents': f'cat_{category}',
                    'values': amount
                })

            # Convert to DataFrame for easier handling
            treemap_df = pd.DataFrame(treemap_data)

            fig = go.Figure(go.Treemap(
                ids=treemap_df['ids'],
                labels=treemap_df['labels'],
                parents=treemap_df['parents'],
                values=treemap_df['values'],
                branchvalues="total",
                hovertemplate='<b>%{label}</b><br>' +
                             'Amount: ₹%{value:,.0f}<br>' +
                             'Percentage: %{percentParent}<br>' +
                             '<extra></extra>',
                maxdepth=3,
                pathbar=dict(visible=True)
            ))

        else:
            # Simple treemap with only categories
            category_data = data.groupby('category')['amount'].sum().sort_values(ascending=False)

            fig = go.Figure(go.Treemap(
                labels=category_data.index,
                values=category_data.values,
                parents=[''] * len(category_data),
                hovertemplate='<b>%{label}</b><br>' +
                             'Amount: ₹%{value:,.0f}<br>' +
                             'Percentage: %{percentParent}<br>' +
                             '<extra></extra>',
                textinfo="label+value+percent parent",
                pathbar=dict(visible=False)
            ))

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            # CRITICAL FIX: Increased margins to prevent label truncation
            margin=dict(l=40, r=40, t=80, b=40)
        )

        # CRITICAL FIX: Apply theme colors instead of hardcoded colors
        fig = self.apply_theme_to_plotly_fig(fig)

        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def on_subcategory_toggled(self, checked: bool):
        """Handle subcategory toggle"""
        self.show_subcategories = checked

        if not self.current_data.empty:
            self.update_chart(self.current_data)


class InteractiveDashboardWidget(QWidget):
    """Interactive dashboard with multiple small widgets and KPIs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = 'light'  # Default to light theme
        self.current_data = pd.DataFrame()
        self.setup_ui()

    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Create scroll area for dashboard content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # KPI Cards Section
        self.create_kpi_section(content_layout)

        # Mini Charts Section
        self.create_mini_charts_section(content_layout)

        # Quick Insights Section
        self.create_insights_section(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def create_kpi_section(self, layout):
        """Create KPI cards section"""
        kpi_frame = QGroupBox("Key Performance Indicators")
        kpi_layout = QGridLayout(kpi_frame)
        kpi_layout.setSpacing(15)

        # Create KPI cards
        self.kpi_cards = {}

        # Total Expenses
        self.kpi_cards['total'] = self.create_kpi_card(
            "Total Expenses", "₹0", "This Period", "#2E86AB"
        )
        kpi_layout.addWidget(self.kpi_cards['total'], 0, 0)

        # Average Transaction
        self.kpi_cards['average'] = self.create_kpi_card(
            "Average Transaction", "₹0", "Per Transaction", "#A23B72"
        )
        kpi_layout.addWidget(self.kpi_cards['average'], 0, 1)

        # Transaction Count
        self.kpi_cards['count'] = self.create_kpi_card(
            "Total Transactions", "0", "Count", "#F18F01"
        )
        kpi_layout.addWidget(self.kpi_cards['count'], 0, 2)

        # Top Category
        self.kpi_cards['top_category'] = self.create_kpi_card(
            "Top Category", "N/A", "Highest Spending", "#C73E1D"
        )
        kpi_layout.addWidget(self.kpi_cards['top_category'], 1, 0)

        # Most Frequent Mode
        self.kpi_cards['frequent_mode'] = self.create_kpi_card(
            "Most Used Mode", "N/A", "Transaction Mode", "#7209B7"
        )
        kpi_layout.addWidget(self.kpi_cards['frequent_mode'], 1, 1)

        # Daily Average
        self.kpi_cards['daily_avg'] = self.create_kpi_card(
            "Daily Average", "₹0", "Per Day", "#16537E"
        )
        kpi_layout.addWidget(self.kpi_cards['daily_avg'], 1, 2)

        layout.addWidget(kpi_frame)

    def create_kpi_card(self, title: str, value: str, subtitle: str, color: str):
        """Create a KPI card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 10px;
                background-color: #252526;
                color: #ffffff;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")

        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18px;")

        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: gray; font-size: 10px;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)

        # Store labels for updates
        card.title_label = title_label
        card.value_label = value_label
        card.subtitle_label = subtitle_label

        return card

    def create_mini_charts_section(self, layout):
        """Create mini charts section"""
        charts_frame = QGroupBox("Quick Charts")
        charts_layout = QGridLayout(charts_frame)
        charts_layout.setSpacing(15)

        # Mini pie chart - CRITICAL FIX: Remove fixed height constraint for dynamic sizing
        self.mini_pie = PlotlyWidget()
        self.mini_pie.current_theme = self.current_theme  # Pass theme to child widget
        # Remove setMaximumHeight to allow dynamic sizing based on content
        self.mini_pie.setMinimumHeight(350)  # Set reasonable minimum height
        self.mini_pie.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.mini_pie, 0, 0)

        # Mini bar chart - CRITICAL FIX: Remove fixed height constraint for dynamic sizing
        self.mini_bar = PlotlyWidget()
        self.mini_bar.current_theme = self.current_theme  # Pass theme to child widget
        # Remove setMaximumHeight to allow dynamic sizing based on content
        self.mini_bar.setMinimumHeight(350)  # Set reasonable minimum height
        self.mini_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.mini_bar, 0, 1)

        # Mini line chart - CRITICAL FIX: Remove fixed height constraint for dynamic sizing
        self.mini_line = PlotlyWidget()
        self.mini_line.current_theme = self.current_theme  # Pass theme to child widget
        # Remove setMaximumHeight to allow dynamic sizing based on content
        self.mini_line.setMinimumHeight(350)  # Set reasonable minimum height
        self.mini_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.mini_line, 1, 0, 1, 2)

        layout.addWidget(charts_frame)

    def create_insights_section(self, layout):
        """Create insights section"""
        insights_frame = QGroupBox("Quick Insights")
        insights_layout = QVBoxLayout(insights_frame)

        self.insights_label = QLabel("Loading insights...")
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")

        insights_layout.addWidget(self.insights_label)
        layout.addWidget(insights_frame)

    def update_theme(self, new_theme):
        """Update theme for dashboard and all child widgets"""
        self.current_theme = new_theme

        # Update child PlotlyWidget instances
        for widget in [self.mini_pie, self.mini_bar, self.mini_line]:
            if hasattr(widget, 'current_theme'):
                widget.current_theme = new_theme

    def update_dashboard(self, data: pd.DataFrame):
        """Update the entire dashboard with new data"""
        self.current_data = data.copy()

        if data.empty:
            self.clear_dashboard()
            return

        # Update KPIs
        self.update_kpis(data)

        # Update mini charts
        self.update_mini_charts(data)

        # Update insights
        self.update_insights(data)

    def update_kpis(self, data: pd.DataFrame):
        """Update KPI cards"""
        try:
            # Calculate metrics
            total_amount = data['amount'].sum()
            avg_amount = data['amount'].mean()
            transaction_count = len(data)

            # Top category
            top_category = data.groupby('category')['amount'].sum().idxmax()

            # Most frequent transaction mode
            most_frequent_mode = data['transaction_mode'].mode().iloc[0] if not data['transaction_mode'].mode().empty else 'N/A'

            # Daily average (assuming data spans multiple days)
            date_range = (pd.to_datetime(data['date']).max() - pd.to_datetime(data['date']).min()).days + 1
            daily_avg = total_amount / max(date_range, 1)

            # Update cards
            self.kpi_cards['total'].value_label.setText(f"₹{total_amount:,.0f}")
            self.kpi_cards['average'].value_label.setText(f"₹{avg_amount:,.0f}")
            self.kpi_cards['count'].value_label.setText(f"{transaction_count}")
            self.kpi_cards['top_category'].value_label.setText(top_category)
            self.kpi_cards['frequent_mode'].value_label.setText(most_frequent_mode)
            self.kpi_cards['daily_avg'].value_label.setText(f"₹{daily_avg:,.0f}")

        except Exception as e:
            print(f"Error updating KPIs: {e}")

    def update_mini_charts(self, data: pd.DataFrame):
        """Update mini charts"""
        try:
            # Mini pie chart - top 5 categories
            category_data = data.groupby('category')['amount'].sum().sort_values(ascending=False).head(5)

            pie_fig = go.Figure(data=[go.Pie(
                labels=category_data.index,
                values=category_data.values,
                hole=0.4,
                showlegend=False,
                textinfo='label+percent',
                textposition='auto'
            )])
            pie_fig.update_layout(
                title="Top 5 Categories",
                # CRITICAL FIX: Increased margins to prevent label truncation
                margin=dict(l=40, r=40, t=60, b=40),
                # CRITICAL FIX: Remove fixed height to allow dynamic sizing based on content
                autosize=True  # Enable automatic sizing based on container
            )
            self.mini_pie.update_chart(pie_fig)

            # Mini bar chart - monthly spending
            data_copy = data.copy()
            data_copy['month'] = pd.to_datetime(data_copy['date']).dt.strftime('%Y-%m')
            monthly_data = data_copy.groupby('month')['amount'].sum().tail(6)  # Last 6 months

            bar_fig = go.Figure(data=[go.Bar(
                x=monthly_data.index,
                y=monthly_data.values,
                marker_color='#2E86AB'
            )])
            bar_fig.update_layout(
                title="Monthly Spending",
                xaxis_title="Month",
                yaxis_title="Amount (₹)",
                # CRITICAL FIX: Increased margins to prevent label truncation
                margin=dict(l=60, r=40, t=60, b=60),
                # CRITICAL FIX: Remove fixed height to allow dynamic sizing based on content
                autosize=True  # Enable automatic sizing based on container
            )
            self.mini_bar.update_chart(bar_fig)

            # Mini line chart - daily trend (last 30 days)
            data_copy = data.copy()
            data_copy['date'] = pd.to_datetime(data_copy['date'])
            daily_data = data_copy.groupby(data_copy['date'].dt.date)['amount'].sum().tail(30)

            line_fig = go.Figure(data=[go.Scatter(
                x=daily_data.index,
                y=daily_data.values,
                mode='lines+markers',
                line=dict(color='#A23B72', width=2),
                marker=dict(size=4)
            )])
            line_fig.update_layout(
                title="Daily Spending Trend (Last 30 Days)",
                xaxis_title="Date",
                yaxis_title="Amount (₹)",
                # CRITICAL FIX: Increased margins to prevent label truncation
                margin=dict(l=60, r=40, t=60, b=60),
                # CRITICAL FIX: Remove fixed height to allow dynamic sizing based on content
                autosize=True  # Enable automatic sizing based on container
            )
            self.mini_line.update_chart(line_fig)

        except Exception as e:
            print(f"Error updating mini charts: {e}")

    def update_insights(self, data: pd.DataFrame):
        """Update insights text"""
        try:
            insights = []

            # Spending trend
            if len(data) > 1:
                recent_data = data.tail(len(data)//2)
                older_data = data.head(len(data)//2)
                recent_avg = recent_data['amount'].mean()
                older_avg = older_data['amount'].mean()

                if recent_avg > older_avg * 1.1:
                    insights.append("📈 Your spending has increased recently.")
                elif recent_avg < older_avg * 0.9:
                    insights.append("📉 Your spending has decreased recently.")
                else:
                    insights.append("📊 Your spending pattern is relatively stable.")

            # Top spending day
            data_copy = data.copy()
            data_copy['day_of_week'] = pd.to_datetime(data_copy['date']).dt.day_name()
            top_day = data_copy.groupby('day_of_week')['amount'].sum().idxmax()
            insights.append(f"📅 You spend the most on {top_day}s.")

            # Category insights
            category_counts = data['category'].value_counts()
            if len(category_counts) > 0:
                most_frequent_category = category_counts.index[0]
                insights.append(f"🏷️ Most frequent category: {most_frequent_category}")

            # Transaction mode insight
            mode_amounts = data.groupby('transaction_mode')['amount'].sum()
            if len(mode_amounts) > 0:
                preferred_mode = mode_amounts.idxmax()
                insights.append(f"💳 Preferred payment mode: {preferred_mode}")

            self.insights_label.setText("\n".join(insights))

        except Exception as e:
            print(f"Error updating insights: {e}")
            self.insights_label.setText("Unable to generate insights at this time.")

    def clear_dashboard(self):
        """Clear all dashboard elements"""
        # Clear KPIs
        for card in self.kpi_cards.values():
            card.value_label.setText("₹0" if "₹" in card.value_label.text() else "0")

        # Clear mini charts
        self.mini_pie.clear_chart()
        self.mini_bar.clear_chart()
        self.mini_line.clear_chart()

        # Clear insights
        self.insights_label.setText("No data available for insights.")
