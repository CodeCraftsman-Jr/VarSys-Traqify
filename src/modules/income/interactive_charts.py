"""
Interactive Income Charts Module
Provides advanced interactive chart widgets using Plotly for income analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGroupBox,
    QComboBox, QSpinBox, QPushButton, QDateEdit, QCheckBox, QGridLayout,
    QScrollArea, QSplitter, QTabWidget, QApplication
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QPalette

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True

    # Try to import QWebEngineView
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        WEBENGINE_AVAILABLE = True
    except ImportError:
        WEBENGINE_AVAILABLE = False
        print("QWebEngineView not available. Interactive charts will use fallback.")

except ImportError:
    PLOTLY_AVAILABLE = False
    WEBENGINE_AVAILABLE = False
    print("Plotly not available. Interactive charts will use basic matplotlib fallback.")

# Print availability status for debugging
print(f"Income Charts: PLOTLY_AVAILABLE = {PLOTLY_AVAILABLE}")
print(f"Income Charts: WEBENGINE_AVAILABLE = {WEBENGINE_AVAILABLE}")

# Import matplotlib as fallback
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.qt_compat import QtWidgets
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
    print("Income Charts: MATPLOTLIB_AVAILABLE = True")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Income Charts: MATPLOTLIB_AVAILABLE = False")


class InteractiveChartWidget(QWidget):
    """Base class for interactive charts using Plotly"""

    def __init__(self, parent=None, theme='light'):  # Default to light theme
        super().__init__(parent)
        self.current_data = pd.DataFrame()
        self.current_theme = self._detect_current_theme(theme)  # Use improved theme detection
        self.apply_theme_styling()
        self.setup_ui()

    def _detect_current_theme(self, fallback_theme='light'):
        """Detect current theme from application or config - improved detection logic"""
        # Try to get theme from parent or application
        app = QApplication.instance()
        theme = fallback_theme  # Default to provided fallback (light)

        if hasattr(app, 'current_theme'):
            theme = app.current_theme
        elif hasattr(self, 'current_theme'):
            theme = self.current_theme
        else:
            # Try to get from main window
            main_window = None
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'config') and hasattr(widget.config, 'theme'):
                    theme = widget.config.theme
                    break

            # Fallback: check palette for theme detection
            if theme == fallback_theme:  # Only if we haven't found a theme yet
                palette = app.palette() if app else QPalette()
                bg_color = palette.color(QPalette.Window)
                # Simple heuristic: if background is dark, assume dark theme
                detected_theme = 'dark' if bg_color.lightness() < 128 else 'light'
                print(f"DEBUG: Detected theme from palette: {detected_theme}, bg lightness: {bg_color.lightness()}")
                theme = detected_theme

        print(f"DEBUG: Using theme '{theme}' for income charts")
        return theme

    def get_theme_colors(self):
        """Get theme colors for current theme"""
        if self.current_theme == 'dark':
            return {
                'background': '#1e1e1e',
                'secondary_background': '#252526',
                'controls_background': '#2d2d30',
                'border': '#3e3e42',
                'text': '#ffffff'
            }
        elif self.current_theme == 'light':
            return {
                'background': '#ffffff',
                'secondary_background': '#f9f9f9',
                'controls_background': '#f0f0f0',
                'border': '#e0e0e0',
                'text': '#000000'
            }
        elif self.current_theme == 'colorwave':
            return {
                'background': '#0a0a1a',
                'secondary_background': '#1a1a2e',
                'controls_background': '#2a2a3e',
                'border': '#4a3c5a',
                'text': '#ffffff'
            }
        else:
            # Default to light theme (changed from dark)
            return {
                'background': '#ffffff',
                'secondary_background': '#f9f9f9',
                'controls_background': '#f0f0f0',
                'border': '#e0e0e0',
                'text': '#000000'
            }

    def apply_theme_styling(self):
        """Apply theme-specific styling to the widget - FIXED: No background override"""
        colors = self.get_theme_colors()
        # CRITICAL FIX: Handle missing keys gracefully and remove background-color override
        border_color = colors.get('border', colors.get('axes_edgecolor', '#3e3e42'))
        self.setStyleSheet(f"""
            InteractiveChartWidget {{
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
        """)

        # CRITICAL FIX: Also update web view styling when theme changes
        if hasattr(self, 'web_view'):
            self.apply_web_view_styling()

    def apply_web_view_styling(self):
        """Apply theme-aware styling to the web view - CRITICAL FIX for chart container backgrounds"""
        if not hasattr(self, 'web_view'):
            return

        colors = self.get_theme_colors()
        background = colors.get('background', colors.get('figure_facecolor', '#1e1e1e'))

        # CRITICAL FIX: Set web view background to match theme
        # This fixes the black background issue in chart containers
        self.web_view.setStyleSheet(f"""
            QWebEngineView {{
                background-color: {background};
                border: none;
            }}
        """)

    def update_theme(self, new_theme):
        """Update theme for the chart widget"""
        self.current_theme = new_theme
        self.apply_theme_styling()

        # Update controls frame styling if it exists
        if hasattr(self, 'controls_frame'):
            colors = self.get_theme_colors()
            # CRITICAL FIX: Remove hardcoded background-color to let global theme handle it
            # This was causing black backgrounds in light theme!
            border_color = colors.get('border', colors.get('axes_edgecolor', '#3e3e42'))
            self.controls_frame.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {border_color};
                    border-radius: 4px;
                    padding: 5px;
                }}
            """)

    def setup_ui(self):
        """Setup the basic UI structure"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Controls section
        self.controls_frame = QFrame()
        colors = self.get_theme_colors()
        # CRITICAL FIX: Remove hardcoded background-color to let global theme handle it
        # This was causing black backgrounds in light theme!
        border_color = colors.get('border', colors.get('axes_edgecolor', '#3e3e42'))
        self.controls_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        self.controls_layout = QHBoxLayout(self.controls_frame)
        self.setup_controls()
        layout.addWidget(self.controls_frame)
        
        # Chart section
        if PLOTLY_AVAILABLE and WEBENGINE_AVAILABLE:
            print(f"Setting up WebEngine view for {self.__class__.__name__}")
            self.web_view = QWebEngineView()

            # CRITICAL FIX: Ensure minimum size for visibility
            self.setMinimumSize(300, 200)
            self.web_view.setMinimumSize(300, 200)

            # CRITICAL FIX: Add visible border to help debug visibility issues
            self.web_view.setStyleSheet("""
                QWebEngineView {
                    border: 2px solid #28a745;
                    background-color: white;
                    min-height: 200px;
                    min-width: 300px;
                }
            """)

            # CRITICAL FIX: Apply theme-aware styling to web view to fix black background
            self.apply_web_view_styling()

            layout.addWidget(self.web_view)

            # Create initial empty chart
            self._create_initial_chart()
        else:
            if not PLOTLY_AVAILABLE:
                message = "Interactive charts require Plotly. Please install plotly."
            elif not WEBENGINE_AVAILABLE:
                message = "Interactive charts require QWebEngineWidgets."
            else:
                message = "Interactive charts temporarily unavailable."

            self.chart_label = QLabel(message)
            self.chart_label.setAlignment(Qt.AlignCenter)
            # CRITICAL FIX: Use theme-aware colors with fallback for missing keys
            colors = self.get_theme_colors()
            border_color = colors.get('border', colors.get('axes_edgecolor', '#3e3e42'))
            self.chart_label.setStyleSheet(f"color: #ff9800; font-size: 12px; padding: 20px; border: 1px solid {border_color}; border-radius: 4px;")
            layout.addWidget(self.chart_label)
    
    def setup_controls(self):
        """Setup control widgets - to be implemented by subclasses"""
        pass

    def _create_initial_chart(self):
        """Create initial empty chart"""
        if PLOTLY_AVAILABLE and WEBENGINE_AVAILABLE and hasattr(self, 'web_view'):
            import plotly.graph_objects as go
            fig = go.Figure()
            # CRITICAL FIX: Use theme-aware colors for Plotly charts
            colors = self.get_theme_colors()
            fig.add_annotation(
                text=f"{self.__class__.__name__}<br>Waiting for data...",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=colors['text'])
            )
            fig.update_layout(
                title="Income Analytics Chart",
                showlegend=False,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor=colors['secondary_background'],
                paper_bgcolor=colors['background'],
                font=dict(color=colors['text'])
            )
            # CRITICAL FIX: Generate theme-aware HTML with custom body styling
            html_str = self.generate_theme_aware_html(fig)
            self.web_view.setHtml(html_str)

    def apply_theme_to_plotly_fig(self, fig):
        """Apply current theme colors to a Plotly figure - CRITICAL FIX for text colors"""
        colors = self.get_theme_colors()

        # CRITICAL FIX: Handle different color key formats gracefully
        # Some get_theme_colors() methods use different key names
        background = colors.get('background', colors.get('figure_facecolor', '#ffffff'))  # Default to white for light theme
        secondary_bg = colors.get('secondary_background', colors.get('axes_facecolor', '#f9f9f9'))  # Light gray for light theme
        text_color = colors.get('text', colors.get('text_color', '#000000'))  # Black text for light theme
        border_color = colors.get('border', colors.get('axes_edgecolor', '#e0e0e0'))  # Light border for light theme

        fig.update_layout(
            plot_bgcolor=secondary_bg,
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
                font=dict(color=text_color)
            )
        )
        return fig

    def generate_theme_aware_html(self, fig):
        """Generate theme-aware HTML for Plotly charts - CRITICAL FIX for chart backgrounds"""
        colors = self.get_theme_colors()
        background = colors.get('background', colors.get('figure_facecolor', '#ffffff'))  # Default to white for light theme

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
        </style>
        """

        # Insert the theme CSS before the closing </head> tag
        if '</head>' in html_str:
            html_str = html_str.replace('</head>', theme_css + '</head>')
        else:
            # Fallback: add at the beginning of the HTML
            html_str = theme_css + html_str

        return html_str

    def set_chart_html(self, html_str):
        """Set HTML content and ensure visibility"""
        if hasattr(self, 'web_view'):
            self.web_view.setHtml(html_str)
            # CRITICAL FIX: Ensure the web view is visible and updated
            self.web_view.show()
            self.web_view.update()

    def update_chart(self, data: pd.DataFrame):
        """Update chart with new data - to be implemented by subclasses"""
        self.current_data = data.copy()
        print(f"Updating {self.__class__.__name__} with {len(data)} rows of data")

        if data.empty:
            print(f"{self.__class__.__name__}: No data to display")
            return

        print(f"{self.__class__.__name__}: Data columns: {list(data.columns)}")
        print(f"{self.__class__.__name__}: Sample data: {data.head(1).to_dict('records')}")
    
    def export_chart(self, filename: str):
        """Export chart to file"""
        if PLOTLY_AVAILABLE and WEBENGINE_AVAILABLE and hasattr(self, 'current_fig'):
            try:
                if filename.endswith('.html'):
                    self.current_fig.write_html(filename)
                elif filename.endswith('.png'):
                    self.current_fig.write_image(filename)
                elif filename.endswith('.pdf'):
                    self.current_fig.write_image(filename)
            except Exception as e:
                print(f"Export failed: {e}")
        else:
            print("Chart export not available in fallback mode")


class InteractivePieChartWidget(InteractiveChartWidget):
    """Interactive pie chart with drill-down capability"""

    source_selected = Signal(str)

    def __init__(self, parent=None, theme='light'):
        super().__init__(parent, theme)
        self.chart_type = 'source'  # source, monthly, weekly
        self.show_percentages = True
        self.show_values = True
    
    def setup_controls(self):
        """Setup pie chart controls"""
        # Chart type selector
        type_label = QLabel("View by:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Income Source', 'Monthly', 'Weekly'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        # Display options
        self.percentages_check = QCheckBox("Show Percentages")
        self.percentages_check.setChecked(True)
        self.percentages_check.toggled.connect(self.on_display_changed)
        
        self.values_check = QCheckBox("Show Values")
        self.values_check.setChecked(True)
        self.values_check.toggled.connect(self.on_display_changed)
        
        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.clicked.connect(self.on_export_clicked)
        
        # Add to layout
        self.controls_layout.addWidget(type_label)
        self.controls_layout.addWidget(self.type_combo)
        self.controls_layout.addWidget(self.percentages_check)
        self.controls_layout.addWidget(self.values_check)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(export_btn)
    
    def on_type_changed(self, text):
        """Handle chart type change"""
        type_map = {
            'Income Source': 'source',
            'Monthly': 'monthly',
            'Weekly': 'weekly'
        }
        self.chart_type = type_map.get(text, 'source')
        self.update_chart(self.current_data)
    
    def on_display_changed(self):
        """Handle display option changes"""
        self.show_percentages = self.percentages_check.isChecked()
        self.show_values = self.values_check.isChecked()
        self.update_chart(self.current_data)
    
    def on_export_clicked(self):
        """Handle export button click"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", f"income_pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html);;PNG Files (*.png);;PDF Files (*.pdf)"
        )
        if filename:
            self.export_chart(filename)
    
    def update_chart(self, data: pd.DataFrame):
        """Update pie chart with income data"""
        super().update_chart(data)

        if data.empty:
            print(f"InteractivePieChartWidget: No data to display")
            return

        if not (PLOTLY_AVAILABLE and WEBENGINE_AVAILABLE):
            print(f"InteractivePieChartWidget: Plotly or WebEngine not available")
            return

        print(f"InteractivePieChartWidget: Creating {self.chart_type} pie chart")

        try:
            if self.chart_type == 'source':
                self._create_source_pie(data)
            elif self.chart_type == 'monthly':
                self._create_monthly_pie(data)
            elif self.chart_type == 'weekly':
                self._create_weekly_pie(data)
        except Exception as e:
            print(f"InteractivePieChartWidget: Error creating chart: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_source_pie(self, data: pd.DataFrame):
        """Create income source pie chart"""
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        source_data = []
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
                    source_data.append({'source': display_name, 'amount': total})
        
        if not source_data:
            return
        
        df = pd.DataFrame(source_data)
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=df['source'],
            values=df['amount'],
            hole=0.3,
            hovertemplate='<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>',
            textinfo='label+percent' if self.show_percentages else 'label',
            textposition='auto'
        )])
        
        fig.update_layout(
            title="Income Distribution by Source",
            font=dict(size=12),
            showlegend=True,
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_str)
    
    def _create_monthly_pie(self, data: pd.DataFrame):
        """Create monthly income pie chart"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')
        
        monthly_data = data_copy.groupby('month')['earned'].sum().reset_index()
        
        if monthly_data.empty:
            return
        
        fig = go.Figure(data=[go.Pie(
            labels=monthly_data['month'],
            values=monthly_data['earned'],
            hole=0.3,
            hovertemplate='<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>',
            textinfo='label+percent' if self.show_percentages else 'label'
        )])
        
        fig.update_layout(
            title="Income Distribution by Month",
            font=dict(size=12),
            showlegend=True,
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        html_str = fig.to_html(include_plotlyjs='cdn')
        self.web_view.setHtml(html_str)
    
    def _create_weekly_pie(self, data: pd.DataFrame):
        """Create weekly income pie chart"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['week'] = data_copy['date'].dt.strftime('%Y-W%U')
        
        weekly_data = data_copy.groupby('week')['earned'].sum().reset_index()
        
        if weekly_data.empty:
            return
        
        fig = go.Figure(data=[go.Pie(
            labels=weekly_data['week'],
            values=weekly_data['earned'],
            hole=0.3,
            hovertemplate='<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>',
            textinfo='label+percent' if self.show_percentages else 'label'
        )])
        
        fig.update_layout(
            title="Income Distribution by Week",
            font=dict(size=12),
            showlegend=True,
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_str)

    def _create_matplotlib_pie(self, data: pd.DataFrame):
        """Create matplotlib pie chart as fallback"""
        if not hasattr(self, 'figure'):
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if self.chart_type == 'source':
            # Income by source
            source_columns = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings',
                            'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
            source_data = data[source_columns].sum()
            source_data = source_data[source_data > 0]  # Only show sources with income

            if not source_data.empty:
                colors = plt.cm.Set3(np.linspace(0, 1, len(source_data)))
                wedges, texts, autotexts = ax.pie(source_data.values, labels=source_data.index,
                                                 autopct='%1.1f%%', colors=colors, startangle=90)
                ax.set_title('Income by Source', fontsize=14, fontweight='bold')

        elif self.chart_type == 'monthly':
            # Income by month
            data_copy = data.copy()
            data_copy['date'] = pd.to_datetime(data_copy['date'])
            data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')
            monthly_data = data_copy.groupby('month')['earned'].sum()

            if not monthly_data.empty:
                colors = plt.cm.Set2(np.linspace(0, 1, len(monthly_data)))
                wedges, texts, autotexts = ax.pie(monthly_data.values, labels=monthly_data.index,
                                                 autopct='%1.1f%%', colors=colors, startangle=90)
                ax.set_title('Income by Month', fontsize=14, fontweight='bold')

        else:  # weekly
            # Income by week
            data_copy = data.copy()
            data_copy['date'] = pd.to_datetime(data_copy['date'])
            data_copy['week'] = data_copy['date'].dt.strftime('%Y-W%U')
            weekly_data = data_copy.groupby('week')['earned'].sum()

            if not weekly_data.empty:
                colors = plt.cm.Set1(np.linspace(0, 1, len(weekly_data)))
                wedges, texts, autotexts = ax.pie(weekly_data.values, labels=weekly_data.index,
                                                 autopct='%1.1f%%', colors=colors, startangle=90)
                ax.set_title('Income by Week', fontsize=14, fontweight='bold')

        plt.tight_layout()
        self.canvas.draw()


class InteractiveTimeSeriesWidget(InteractiveChartWidget):
    """Interactive time series chart with zoom and pan functionality"""

    def __init__(self, parent=None, theme='light'):
        super().__init__(parent, theme)
        self.aggregation = 'daily'
        self.show_trend = True
        self.show_goals = True
    
    def setup_controls(self):
        """Setup time series controls"""
        # Aggregation selector
        agg_label = QLabel("Aggregation:")
        self.agg_combo = QComboBox()
        self.agg_combo.addItems(['Daily', 'Weekly', 'Monthly'])
        self.agg_combo.currentTextChanged.connect(self.on_aggregation_changed)
        
        # Display options
        self.trend_check = QCheckBox("Show Trend Line")
        self.trend_check.setChecked(True)
        self.trend_check.toggled.connect(self.on_display_changed)
        
        self.goals_check = QCheckBox("Show Goals")
        self.goals_check.setChecked(True)
        self.goals_check.toggled.connect(self.on_display_changed)
        
        # Date range selector
        date_label = QLabel("Date Range:")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.dateChanged.connect(self.on_date_changed)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.on_date_changed)
        
        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.clicked.connect(self.on_export_clicked)
        
        # Add to layout
        self.controls_layout.addWidget(agg_label)
        self.controls_layout.addWidget(self.agg_combo)
        self.controls_layout.addWidget(self.trend_check)
        self.controls_layout.addWidget(self.goals_check)
        self.controls_layout.addWidget(date_label)
        self.controls_layout.addWidget(self.start_date)
        self.controls_layout.addWidget(self.end_date)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(export_btn)
    
    def on_aggregation_changed(self, text):
        """Handle aggregation change"""
        self.aggregation = text.lower()
        self.update_chart(self.current_data)
    
    def on_display_changed(self):
        """Handle display option changes"""
        self.show_trend = self.trend_check.isChecked()
        self.show_goals = self.goals_check.isChecked()
        self.update_chart(self.current_data)
    
    def on_date_changed(self):
        """Handle date range change"""
        self.update_chart(self.current_data)
    
    def on_export_clicked(self):
        """Handle export button click"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", f"income_timeseries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html);;PNG Files (*.png);;PDF Files (*.pdf)"
        )
        if filename:
            self.export_chart(filename)
    
    def update_chart(self, data: pd.DataFrame):
        """Update time series chart"""
        super().update_chart(data)
        
        if not PLOTLY_AVAILABLE or data.empty:
            return
        
        # Filter by date range
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        filtered_data = data_copy[
            (data_copy['date'].dt.date >= start_date) & 
            (data_copy['date'].dt.date <= end_date)
        ]
        
        if filtered_data.empty:
            return
        
        # Aggregate data
        if self.aggregation == 'daily':
            agg_data = filtered_data.groupby(filtered_data['date'].dt.date).agg({
                'earned': 'sum',
                'goal_inc': 'mean'
            }).reset_index()
        elif self.aggregation == 'weekly':
            agg_data = filtered_data.groupby(filtered_data['date'].dt.to_period('W')).agg({
                'earned': 'sum',
                'goal_inc': 'sum'
            }).reset_index()
            agg_data['date'] = agg_data['date'].astype(str)
        elif self.aggregation == 'monthly':
            agg_data = filtered_data.groupby(filtered_data['date'].dt.to_period('M')).agg({
                'earned': 'sum',
                'goal_inc': 'sum'
            }).reset_index()
            agg_data['date'] = agg_data['date'].astype(str)
        
        # Create time series chart
        fig = go.Figure()
        
        # Add income line
        fig.add_trace(go.Scatter(
            x=agg_data['date'],
            y=agg_data['earned'],
            mode='lines+markers',
            name='Income',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8),
            hovertemplate='<b>Date:</b> %{x}<br><b>Income:</b> ₹%{y:,.0f}<extra></extra>'
        ))
        
        # Add goals line if enabled
        if self.show_goals and 'goal_inc' in agg_data.columns:
            fig.add_trace(go.Scatter(
                x=agg_data['date'],
                y=agg_data['goal_inc'],
                mode='lines',
                name='Goal',
                line=dict(color='#A23B72', width=2, dash='dash'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Goal:</b> ₹%{y:,.0f}<extra></extra>'
            ))
        
        # Add trend line if enabled
        if self.show_trend and len(agg_data) > 1:
            x_numeric = list(range(len(agg_data)))
            z = np.polyfit(x_numeric, agg_data['earned'], 1)
            trend_line = np.poly1d(z)(x_numeric)
            
            fig.add_trace(go.Scatter(
                x=agg_data['date'],
                y=trend_line,
                mode='lines',
                name='Trend',
                line=dict(color='#F44336', width=2, dash='dot'),  # Use consistent red color
                hovertemplate='<b>Trend:</b> ₹%{y:,.0f}<extra></extra>'
            ))
        
        fig.update_layout(
            title=f"Income Trends ({self.aggregation.title()})",
            xaxis_title="Date",
            yaxis_title="Income (₹)",
            hovermode='x unified',
            height=500,
            showlegend=True
        )
        
        # Enable zoom and pan
        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True)),
            dragmode='zoom'
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.set_chart_html(html_str)


class InteractiveBarChartWidget(InteractiveChartWidget):
    """Interactive bar chart with filtering options"""

    def __init__(self, parent=None, theme='light'):
        super().__init__(parent, theme)
        self.chart_type = 'source'
        self.sort_order = 'desc'
        self.top_n = 15
    
    def setup_controls(self):
        """Setup bar chart controls"""
        # Chart type
        type_label = QLabel("Chart Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Income Source', 'Monthly', 'Weekly', 'Daily'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        # Sort order
        sort_label = QLabel("Sort:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Highest First', 'Lowest First'])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        
        # Top N filter
        top_n_label = QLabel("Show Top:")
        self.top_n_spin = QSpinBox()
        self.top_n_spin.setRange(5, 50)
        self.top_n_spin.setValue(15)
        self.top_n_spin.valueChanged.connect(self.on_top_n_changed)
        
        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.clicked.connect(self.on_export_clicked)
        
        # Add to layout
        self.controls_layout.addWidget(type_label)
        self.controls_layout.addWidget(self.type_combo)
        self.controls_layout.addWidget(sort_label)
        self.controls_layout.addWidget(self.sort_combo)
        self.controls_layout.addWidget(top_n_label)
        self.controls_layout.addWidget(self.top_n_spin)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(export_btn)
    
    def on_type_changed(self, text):
        """Handle chart type change"""
        type_map = {
            'Income Source': 'source',
            'Monthly': 'monthly',
            'Weekly': 'weekly',
            'Daily': 'daily'
        }
        self.chart_type = type_map.get(text, 'source')
        self.update_chart(self.current_data)
    
    def on_sort_changed(self, text):
        """Handle sort order change"""
        self.sort_order = 'desc' if text == 'Highest First' else 'asc'
        self.update_chart(self.current_data)
    
    def on_top_n_changed(self, value):
        """Handle top N change"""
        self.top_n = value
        self.update_chart(self.current_data)
    
    def on_export_clicked(self):
        """Handle export button click"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", f"income_bar_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html);;PNG Files (*.png);;PDF Files (*.pdf)"
        )
        if filename:
            self.export_chart(filename)
    
    def update_chart(self, data: pd.DataFrame):
        """Update bar chart"""
        super().update_chart(data)
        
        if not PLOTLY_AVAILABLE or data.empty:
            return
        
        if self.chart_type == 'source':
            self._create_source_bar(data)
        elif self.chart_type == 'monthly':
            self._create_monthly_bar(data)
        elif self.chart_type == 'weekly':
            self._create_weekly_bar(data)
        elif self.chart_type == 'daily':
            self._create_daily_bar(data)
    
    def _create_source_bar(self, data: pd.DataFrame):
        """Create income source bar chart"""
        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings', 
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
        
        source_data = []
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
                    source_data.append({'source': display_name, 'amount': total})
        
        if not source_data:
            return
        
        df = pd.DataFrame(source_data)
        df = df.sort_values('amount', ascending=(self.sort_order == 'asc')).head(self.top_n)
        
        fig = go.Figure(data=[go.Bar(
            x=df['source'],
            y=df['amount'],
            marker_color='#2E86AB',
            hovertemplate='<b>%{x}</b><br>Amount: ₹%{y:,.0f}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Income by Source",
            xaxis_title="Income Source",
            yaxis_title="Amount (₹)",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_monthly_bar(self, data: pd.DataFrame):
        """Create monthly income bar chart"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')
        
        monthly_data = data_copy.groupby('month')['earned'].sum().reset_index()
        monthly_data = monthly_data.sort_values('earned', ascending=(self.sort_order == 'asc')).head(self.top_n)
        
        fig = go.Figure(data=[go.Bar(
            x=monthly_data['month'],
            y=monthly_data['earned'],
            marker_color='#A23B72',
            hovertemplate='<b>%{x}</b><br>Income: ₹%{y:,.0f}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Monthly Income",
            xaxis_title="Month",
            yaxis_title="Income (₹)",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_weekly_bar(self, data: pd.DataFrame):
        """Create weekly income bar chart"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['week'] = data_copy['date'].dt.strftime('%Y-W%U')
        
        weekly_data = data_copy.groupby('week')['earned'].sum().reset_index()
        weekly_data = weekly_data.sort_values('earned', ascending=(self.sort_order == 'asc')).head(self.top_n)
        
        fig = go.Figure(data=[go.Bar(
            x=weekly_data['week'],
            y=weekly_data['earned'],
            marker_color='#F18F01',
            hovertemplate='<b>%{x}</b><br>Income: ₹%{y:,.0f}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Weekly Income",
            xaxis_title="Week",
            yaxis_title="Income (₹)",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_daily_bar(self, data: pd.DataFrame):
        """Create daily income bar chart"""
        daily_data = data.groupby('date')['earned'].sum().reset_index()
        daily_data = daily_data.sort_values('earned', ascending=(self.sort_order == 'asc')).head(self.top_n)
        
        fig = go.Figure(data=[go.Bar(
            x=daily_data['date'],
            y=daily_data['earned'],
            marker_color='#C73E1D',
            hovertemplate='<b>%{x}</b><br>Income: ₹%{y:,.0f}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Daily Income",
            xaxis_title="Date",
            yaxis_title="Income (₹)",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveScatterPlotWidget(InteractiveChartWidget):
    """Interactive scatter plot for income correlation analysis"""

    def __init__(self, parent=None, theme='light'):
        super().__init__(parent, theme)
        self.x_metric = 'earned'
        self.y_metric = 'goal_inc'
        self.color_by = 'month'

    def setup_controls(self):
        """Setup scatter plot controls"""
        # X-axis metric
        x_label = QLabel("X-Axis:")
        self.x_combo = QComboBox()
        self.x_combo.addItems(['Earned', 'Goal', 'Progress'])
        self.x_combo.currentTextChanged.connect(self.on_x_changed)

        # Y-axis metric
        y_label = QLabel("Y-Axis:")
        self.y_combo = QComboBox()
        self.y_combo.addItems(['Goal', 'Earned', 'Progress'])
        self.y_combo.setCurrentText('Goal')
        self.y_combo.currentTextChanged.connect(self.on_y_changed)

        # Color by
        color_label = QLabel("Color by:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(['Month', 'Week', 'Source'])
        self.color_combo.currentTextChanged.connect(self.on_color_changed)

        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.clicked.connect(self.on_export_clicked)

        # Add to layout
        self.controls_layout.addWidget(x_label)
        self.controls_layout.addWidget(self.x_combo)
        self.controls_layout.addWidget(y_label)
        self.controls_layout.addWidget(self.y_combo)
        self.controls_layout.addWidget(color_label)
        self.controls_layout.addWidget(self.color_combo)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(export_btn)

    def on_x_changed(self, text):
        """Handle X-axis metric change"""
        metric_map = {'Earned': 'earned', 'Goal': 'goal_inc', 'Progress': 'progress'}
        self.x_metric = metric_map.get(text, 'earned')
        self.update_chart(self.current_data)

    def on_y_changed(self, text):
        """Handle Y-axis metric change"""
        metric_map = {'Earned': 'earned', 'Goal': 'goal_inc', 'Progress': 'progress'}
        self.y_metric = metric_map.get(text, 'goal_inc')
        self.update_chart(self.current_data)

    def on_color_changed(self, text):
        """Handle color grouping change"""
        self.color_by = text.lower()
        self.update_chart(self.current_data)

    def on_export_clicked(self):
        """Handle export button click"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", f"income_scatter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html);;PNG Files (*.png);;PDF Files (*.pdf)"
        )
        if filename:
            self.export_chart(filename)

    def update_chart(self, data: pd.DataFrame):
        """Update scatter plot for correlation analysis"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or data.empty:
            return

        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])

        # Add grouping columns
        if self.color_by == 'month':
            data_copy['group'] = data_copy['date'].dt.strftime('%Y-%m')
        elif self.color_by == 'week':
            data_copy['group'] = data_copy['date'].dt.strftime('%Y-W%U')
        else:  # source - use dominant source
            income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings',
                             'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']
            data_copy['group'] = 'Other'
            for idx, row in data_copy.iterrows():
                max_source = 'Other'
                max_value = 0
                for source in income_sources:
                    if source in row and row[source] > max_value:
                        max_value = row[source]
                        max_source = source.replace('_', ' ').title()
                data_copy.loc[idx, 'group'] = max_source

        # Create scatter plot
        fig = px.scatter(
            data_copy,
            x=self.x_metric,
            y=self.y_metric,
            color='group',
            size='earned',
            hover_data=['date', 'earned', 'goal_inc', 'progress'],
            title=f"Income Correlation: {self.x_metric.title()} vs {self.y_metric.title()}"
        )

        fig.update_layout(
            height=500,
            xaxis_title=self.x_metric.replace('_', ' ').title(),
            yaxis_title=self.y_metric.replace('_', ' ').title()
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _calculate_streaks(self, data: pd.DataFrame) -> dict:
        """Calculate streaks for income data (placeholder method for compatibility)"""
        # This method is for compatibility with habit tracking widgets
        # Income data doesn't have the same streak concept as habits
        return {}


class InteractiveHeatmapWidget(InteractiveChartWidget):
    """Interactive heatmap for income patterns by time periods"""

    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent, theme)
        self.heatmap_type = 'day_month'  # day_month, weekday_month, source_month

    def setup_controls(self):
        """Setup heatmap controls"""
        # Heatmap type
        type_label = QLabel("Heatmap Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Day vs Month', 'Day of Week vs Month', 'Source vs Month'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)

        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.clicked.connect(self.on_export_clicked)

        # Add to layout
        self.controls_layout.addWidget(type_label)
        self.controls_layout.addWidget(self.type_combo)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(export_btn)

    def on_type_changed(self, text):
        """Handle heatmap type change"""
        type_map = {
            'Day vs Month': 'day_month',
            'Day of Week vs Month': 'weekday_month',
            'Source vs Month': 'source_month'
        }
        self.heatmap_type = type_map.get(text, 'day_month')
        self.update_chart(self.current_data)

    def on_export_clicked(self):
        """Handle export button click"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", f"income_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html);;PNG Files (*.png);;PDF Files (*.pdf)"
        )
        if filename:
            self.export_chart(filename)

    def update_chart(self, data: pd.DataFrame):
        """Update heatmap with income pattern data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or data.empty:
            return

        if self.heatmap_type == 'day_month':
            self._create_day_month_heatmap(data)
        elif self.heatmap_type == 'weekday_month':
            self._create_weekday_month_heatmap(data)
        elif self.heatmap_type == 'source_month':
            self._create_source_month_heatmap(data)

    def _create_day_month_heatmap(self, data: pd.DataFrame):
        """Create day vs month heatmap"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['day'] = data_copy['date'].dt.day
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        # Create pivot table
        pivot_data = data_copy.pivot_table(
            values='earned',
            index='day',
            columns='month',
            aggfunc='sum',
            fill_value=0
        )

        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='Blues',
            hoverongaps=False,
            hovertemplate='<b>Day:</b> %{y}<br><b>Month:</b> %{x}<br><b>Income:</b> ₹%{z:,.0f}<extra></extra>'
        ))

        fig.update_layout(
            title="Income Heatmap: Day vs Month",
            xaxis_title="Month",
            yaxis_title="Day of Month",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_weekday_month_heatmap(self, data: pd.DataFrame):
        """Create weekday vs month heatmap"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['weekday'] = data_copy['date'].dt.day_name()
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        # Create pivot table
        pivot_data = data_copy.pivot_table(
            values='earned',
            index='weekday',
            columns='month',
            aggfunc='sum',
            fill_value=0
        )

        # Reorder weekdays
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_data = pivot_data.reindex(weekday_order, fill_value=0)

        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='Reds',
            hoverongaps=False,
            hovertemplate='<b>Day:</b> %{y}<br><b>Month:</b> %{x}<br><b>Income:</b> ₹%{z:,.0f}<extra></extra>'
        ))

        fig.update_layout(
            title="Income Heatmap: Day of Week vs Month",
            xaxis_title="Month",
            yaxis_title="Day of Week",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_source_month_heatmap(self, data: pd.DataFrame):
        """Create source vs month heatmap"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings',
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']

        # Prepare data for heatmap
        heatmap_data = []
        for source in income_sources:
            if source in data_copy.columns:
                source_data = data_copy.groupby('month')[source].sum()
                display_name = source.replace('_', ' ').title()
                if source == 'gp_links':
                    display_name = 'GP Links'
                elif source == 'id_sales':
                    display_name = 'ID Sales'
                elif source == 'shadow_fax':
                    display_name = 'Shadow Fax'
                elif source == 'pc_repair':
                    display_name = 'PC Repair'

                for month, amount in source_data.items():
                    if amount > 0:
                        heatmap_data.append({
                            'source': display_name,
                            'month': month,
                            'amount': amount
                        })

        if not heatmap_data:
            return

        heatmap_df = pd.DataFrame(heatmap_data)
        pivot_data = heatmap_df.pivot_table(
            values='amount',
            index='source',
            columns='month',
            aggfunc='sum',
            fill_value=0
        )

        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='Greens',
            hoverongaps=False,
            hovertemplate='<b>Source:</b> %{y}<br><b>Month:</b> %{x}<br><b>Income:</b> ₹%{z:,.0f}<extra></extra>'
        ))

        fig.update_layout(
            title="Income Heatmap: Source vs Month",
            xaxis_title="Month",
            yaxis_title="Income Source",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)


class InteractiveTreemapWidget(InteractiveChartWidget):
    """Interactive treemap for hierarchical income data visualization"""

    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent, theme)
        self.hierarchy_type = 'source_month'  # source_month, month_source

    def setup_controls(self):
        """Setup treemap controls"""
        # Hierarchy type
        hierarchy_label = QLabel("Hierarchy:")
        self.hierarchy_combo = QComboBox()
        self.hierarchy_combo.addItems(['Source → Month', 'Month → Source'])
        self.hierarchy_combo.currentTextChanged.connect(self.on_hierarchy_changed)

        # Export button
        export_btn = QPushButton("Export Chart")
        export_btn.clicked.connect(self.on_export_clicked)

        # Add to layout
        self.controls_layout.addWidget(hierarchy_label)
        self.controls_layout.addWidget(self.hierarchy_combo)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(export_btn)

    def on_hierarchy_changed(self, text):
        """Handle hierarchy type change"""
        self.hierarchy_type = 'source_month' if text == 'Source → Month' else 'month_source'
        self.update_chart(self.current_data)

    def on_export_clicked(self):
        """Handle export button click"""
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", f"income_treemap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html);;PNG Files (*.png);;PDF Files (*.pdf)"
        )
        if filename:
            self.export_chart(filename)

    def update_chart(self, data: pd.DataFrame):
        """Update treemap with hierarchical income data"""
        super().update_chart(data)

        if not PLOTLY_AVAILABLE or data.empty:
            return

        if self.hierarchy_type == 'source_month':
            self._create_source_month_treemap(data)
        else:
            self._create_month_source_treemap(data)

    def _create_source_month_treemap(self, data: pd.DataFrame):
        """Create source → month treemap"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings',
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']

        # Prepare hierarchical data
        treemap_data = []

        # Add root
        treemap_data.append({
            'ids': 'Total',
            'labels': 'Total Income',
            'parents': '',
            'values': data_copy['earned'].sum()
        })

        # Add sources as first level
        for source in income_sources:
            if source in data_copy.columns:
                total = data_copy[source].sum()
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

                    treemap_data.append({
                        'ids': source,
                        'labels': display_name,
                        'parents': 'Total',
                        'values': total
                    })

                    # Add months as second level for each source
                    monthly_data = data_copy.groupby('month')[source].sum()
                    for month, amount in monthly_data.items():
                        if amount > 0:
                            treemap_data.append({
                                'ids': f'{source}_{month}',
                                'labels': month,
                                'parents': source,
                                'values': amount
                            })

        if len(treemap_data) <= 1:
            return

        treemap_df = pd.DataFrame(treemap_data)

        fig = go.Figure(go.Treemap(
            ids=treemap_df['ids'],
            labels=treemap_df['labels'],
            parents=treemap_df['parents'],
            values=treemap_df['values'],
            branchvalues="total",
            hovertemplate='<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Percentage: %{percentParent}<extra></extra>'
        ))

        fig.update_layout(
            title="Income Treemap: Source → Month",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)

    def _create_month_source_treemap(self, data: pd.DataFrame):
        """Create month → source treemap"""
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy['date'])
        data_copy['month'] = data_copy['date'].dt.strftime('%Y-%m')

        income_sources = ['zomato', 'swiggy', 'shadow_fax', 'pc_repair', 'settings',
                         'youtube', 'gp_links', 'id_sales', 'other_sources', 'extra_work']

        # Prepare hierarchical data
        treemap_data = []

        # Add root
        treemap_data.append({
            'ids': 'Total',
            'labels': 'Total Income',
            'parents': '',
            'values': data_copy['earned'].sum()
        })

        # Add months as first level
        monthly_totals = data_copy.groupby('month')['earned'].sum()
        for month, total in monthly_totals.items():
            if total > 0:
                treemap_data.append({
                    'ids': month,
                    'labels': month,
                    'parents': 'Total',
                    'values': total
                })

                # Add sources as second level for each month
                month_data = data_copy[data_copy['month'] == month]
                for source in income_sources:
                    if source in month_data.columns:
                        amount = month_data[source].sum()
                        if amount > 0:
                            display_name = source.replace('_', ' ').title()
                            if source == 'gp_links':
                                display_name = 'GP Links'
                            elif source == 'id_sales':
                                display_name = 'ID Sales'
                            elif source == 'shadow_fax':
                                display_name = 'Shadow Fax'
                            elif source == 'pc_repair':
                                display_name = 'PC Repair'

                            treemap_data.append({
                                'ids': f'{month}_{source}',
                                'labels': display_name,
                                'parents': month,
                                'values': amount
                            })

        if len(treemap_data) <= 1:
            return

        treemap_df = pd.DataFrame(treemap_data)

        fig = go.Figure(go.Treemap(
            ids=treemap_df['ids'],
            labels=treemap_df['labels'],
            parents=treemap_df['parents'],
            values=treemap_df['values'],
            branchvalues="total",
            hovertemplate='<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Percentage: %{percentParent}<extra></extra>'
        ))

        fig.update_layout(
            title="Income Treemap: Month → Source",
            height=500
        )

        # CRITICAL FIX: Apply theme colors to ensure proper text colors
        fig = self.apply_theme_to_plotly_fig(fig)

        self.current_fig = fig
        # CRITICAL FIX: Use theme-aware HTML generation
        html_str = self.generate_theme_aware_html(fig)
        self.web_view.setHtml(html_str)
