"""
Investment Data Loading Widget
Provides comprehensive progress tracking with progress bars and status indicators
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QFrame, QGridLayout, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QPalette


class DataCategoryWidget(QWidget):
    """Widget for displaying individual data category progress"""
    
    def __init__(self, category_name: str, display_name: str):
        super().__init__()
        self.category_name = category_name
        self.display_name = display_name
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the category widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Status icon
        self.status_icon = QLabel("⏳")
        self.status_icon.setFixedWidth(20)
        layout.addWidget(self.status_icon)
        
        # Category name
        self.name_label = QLabel(self.display_name)
        self.name_label.setMinimumWidth(120)
        layout.addWidget(self.name_label)
        
        # Status text
        self.status_label = QLabel("Waiting...")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Timestamp
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(self.time_label)
    
    def set_status(self, status: str, icon: str = "⏳", color: str = "#666"):
        """Update the status of this category"""
        self.status_icon.setText(icon)
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color};")
        self.time_label.setText(datetime.now().strftime("%H:%M:%S"))
    
    def set_loading(self):
        """Set loading state"""
        self.set_status("Loading...", "🔄", "#2196F3")
    
    def set_success(self, message: str = "Completed"):
        """Set success state"""
        self.set_status(message, "✅", "#4CAF50")
    
    def set_error(self, message: str = "Failed"):
        """Set error state"""
        self.set_status(message, "❌", "#F44336")
    
    def set_cached(self, message: str = "From cache"):
        """Set cached data state"""
        self.set_status(message, "💾", "#FF9800")

    def set_stale(self, message: str = "Stale data"):
        """Set stale data state"""
        self.set_status(message, "⚠️", "#FF5722")

    def set_network_error(self, message: str = "Network error"):
        """Set network error state"""
        self.set_status(message, "🌐❌", "#F44336")


class InvestmentLoadingWidget(QWidget):
    """Comprehensive loading widget with progress tracking"""
    
    # Signals
    cancel_requested = Signal()
    
    def __init__(self, symbol: str, fund_name: str):
        super().__init__()
        self.symbol = symbol
        self.fund_name = fund_name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Progress tracking
        self.start_time = datetime.now()
        self.category_widgets = {}
        self.estimated_time = 30  # seconds
        
        # Data categories with display names
        self.categories = {
            'real_time': 'Real-time Data',
            'historical': 'Historical Prices',
            'performance': 'Performance Metrics',
            'financial': 'Financial Data',
            'portfolio': 'Portfolio Info',
            'regulatory': 'Regulatory Filings',
            'dividend': 'Dividend Data',
            'fees': 'Fees & Expenses'
        }
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """Setup the loading widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.create_header(layout)
        
        # Main progress bar
        self.create_main_progress(layout)
        
        # Category progress section
        self.create_category_progress(layout)
        
        # Time and status info
        self.create_status_info(layout)
        
        # Action buttons
        self.create_action_buttons(layout)
    
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel(f"📊 Loading Investment Data")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Symbol and name
        symbol_label = QLabel(f"{self.fund_name} ({self.symbol})")
        symbol_label.setFont(QFont("Arial", 12))
        symbol_label.setAlignment(Qt.AlignCenter)
        symbol_label.setStyleSheet("color: #666; margin: 5px;")
        header_layout.addWidget(symbol_label)
        
        layout.addWidget(header_frame)
    
    def create_main_progress(self, layout):
        """Create main progress bar section"""
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.StyledPanel)
        progress_layout = QVBoxLayout(progress_frame)
        
        # Overall progress label
        self.overall_status_label = QLabel("Initializing...")
        self.overall_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.overall_status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.overall_status_label)
        
        # Main progress bar
        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setMinimum(0)
        self.main_progress_bar.setMaximum(100)
        self.main_progress_bar.setValue(0)
        self.main_progress_bar.setTextVisible(True)
        self.main_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.main_progress_bar)
        
        layout.addWidget(progress_frame)
    
    def create_category_progress(self, layout):
        """Create category progress section"""
        category_frame = QFrame()
        category_frame.setFrameStyle(QFrame.StyledPanel)
        category_layout = QVBoxLayout(category_frame)
        
        # Section title
        section_title = QLabel("📋 Data Categories")
        section_title.setFont(QFont("Arial", 11, QFont.Bold))
        category_layout.addWidget(section_title)
        
        # Scroll area for categories
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Create category widgets
        for category_key, display_name in self.categories.items():
            category_widget = DataCategoryWidget(category_key, display_name)
            self.category_widgets[category_key] = category_widget
            scroll_layout.addWidget(category_widget)
        
        scroll_area.setWidget(scroll_widget)
        category_layout.addWidget(scroll_area)
        
        layout.addWidget(category_frame)
    
    def create_status_info(self, layout):
        """Create status information section"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QGridLayout(status_frame)
        
        # Elapsed time
        status_layout.addWidget(QLabel("Elapsed Time:"), 0, 0)
        self.elapsed_time_label = QLabel("00:00")
        self.elapsed_time_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        status_layout.addWidget(self.elapsed_time_label, 0, 1)
        
        # Estimated remaining
        status_layout.addWidget(QLabel("Est. Remaining:"), 0, 2)
        self.remaining_time_label = QLabel("--:--")
        self.remaining_time_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        status_layout.addWidget(self.remaining_time_label, 0, 3)
        
        # Data source
        status_layout.addWidget(QLabel("Data Source:"), 1, 0)
        self.data_source_label = QLabel("Local Storage + API")
        self.data_source_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.data_source_label, 1, 1)
        
        # Network status
        status_layout.addWidget(QLabel("Network:"), 1, 2)
        self.network_status_label = QLabel("Checking...")
        self.network_status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.network_status_label, 1, 3)

        # Data freshness
        status_layout.addWidget(QLabel("Data Freshness:"), 2, 0)
        self.freshness_label = QLabel("Checking...")
        self.freshness_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.freshness_label, 2, 1)

        # Cache status
        status_layout.addWidget(QLabel("Cache Status:"), 2, 2)
        self.cache_status_label = QLabel("Loading...")
        self.cache_status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.cache_status_label, 2, 3)

        layout.addWidget(status_frame)
    
    def create_action_buttons(self, layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def setup_timer(self):
        """Setup timer for updating elapsed time"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_display)
        self.timer.start(1000)  # Update every second
    
    def update_time_display(self):
        """Update elapsed and remaining time display"""
        elapsed = datetime.now() - self.start_time
        elapsed_seconds = int(elapsed.total_seconds())
        
        # Format elapsed time
        elapsed_minutes = elapsed_seconds // 60
        elapsed_secs = elapsed_seconds % 60
        self.elapsed_time_label.setText(f"{elapsed_minutes:02d}:{elapsed_secs:02d}")
        
        # Estimate remaining time based on progress
        progress = self.main_progress_bar.value()
        if progress > 5:  # Only estimate after some progress
            estimated_total = (elapsed_seconds * 100) / progress
            remaining_seconds = max(0, int(estimated_total - elapsed_seconds))
            remaining_minutes = remaining_seconds // 60
            remaining_secs = remaining_seconds % 60
            self.remaining_time_label.setText(f"{remaining_minutes:02d}:{remaining_secs:02d}")
        else:
            self.remaining_time_label.setText("--:--")
    
    def update_progress(self, progress: int, status: str):
        """Update main progress bar and status"""
        self.main_progress_bar.setValue(progress)
        self.overall_status_label.setText(status)
    
    def update_category_status(self, category: str, success: bool, message: str = ""):
        """Update status for a specific category"""
        if category in self.category_widgets:
            widget = self.category_widgets[category]
            if success:
                widget.set_success(message or "Completed")
            else:
                widget.set_error(message or "Failed")
    
    def set_category_loading(self, category: str):
        """Set a category to loading state"""
        if category in self.category_widgets:
            self.category_widgets[category].set_loading()
    
    def set_category_cached(self, category: str, message: str = ""):
        """Set a category to cached state"""
        if category in self.category_widgets:
            self.category_widgets[category].set_cached(message or "From cache")
    
    def set_network_status(self, status: str, color: str = "#666"):
        """Update network status"""
        self.network_status_label.setText(status)
        self.network_status_label.setStyleSheet(f"color: {color};")
    
    def set_completed(self):
        """Set the loading as completed"""
        self.update_progress(100, "✅ Data loading completed!")
        self.cancel_button.setText("Close")
        self.timer.stop()
    
    def set_cancelled(self):
        """Set the loading as cancelled"""
        self.update_progress(0, "❌ Loading cancelled")
        self.cancel_button.setText("Close")
        self.timer.stop()
    
    def set_error(self, error_message: str):
        """Set error state"""
        self.update_progress(0, f"❌ Error: {error_message}")
        self.cancel_button.setText("Close")
        self.timer.stop()

    def update_freshness_info(self, freshness_info: dict):
        """Update data freshness information"""
        try:
            fresh_count = 0
            stale_count = 0
            total_count = len(freshness_info)

            for category, info in freshness_info.items():
                if info.get('is_stale', True):
                    stale_count += 1
                else:
                    fresh_count += 1

            if total_count == 0:
                self.freshness_label.setText("No data")
                self.freshness_label.setStyleSheet("color: #999;")
            elif stale_count == 0:
                self.freshness_label.setText("All fresh")
                self.freshness_label.setStyleSheet("color: #4CAF50;")
            elif fresh_count == 0:
                self.freshness_label.setText("All stale")
                self.freshness_label.setStyleSheet("color: #F44336;")
            else:
                self.freshness_label.setText(f"{fresh_count} fresh, {stale_count} stale")
                self.freshness_label.setStyleSheet("color: #FF9800;")

        except Exception as e:
            self.freshness_label.setText("Error")
            self.freshness_label.setStyleSheet("color: #F44336;")

    def update_cache_status(self, cached_categories: int, total_categories: int):
        """Update cache status information"""
        try:
            if total_categories == 0:
                self.cache_status_label.setText("No data")
                self.cache_status_label.setStyleSheet("color: #999;")
            elif cached_categories == total_categories:
                self.cache_status_label.setText("All cached")
                self.cache_status_label.setStyleSheet("color: #4CAF50;")
            elif cached_categories == 0:
                self.cache_status_label.setText("No cache")
                self.cache_status_label.setStyleSheet("color: #F44336;")
            else:
                self.cache_status_label.setText(f"{cached_categories}/{total_categories} cached")
                self.cache_status_label.setStyleSheet("color: #FF9800;")

        except Exception as e:
            self.cache_status_label.setText("Error")
            self.cache_status_label.setStyleSheet("color: #F44336;")

    def show_detailed_error(self, error_type: str, error_details: str):
        """Show detailed error information"""
        error_text = f"❌ {error_type}\n\nDetails: {error_details}\n\nTroubleshooting:\n"

        if "network" in error_type.lower() or "connection" in error_details.lower():
            error_text += "• Check your internet connection\n"
            error_text += "• Try again in a few moments\n"
            error_text += "• Some data may be available from cache"
        elif "symbol" in error_details.lower():
            error_text += "• Verify the symbol is correct\n"
            error_text += "• Try using the full symbol (e.g., RELIANCE.NS)\n"
            error_text += "• Check if the symbol is listed on supported exchanges"
        elif "api" in error_details.lower() or "rate" in error_details.lower():
            error_text += "• API rate limit may have been exceeded\n"
            error_text += "• Wait a few minutes before trying again\n"
            error_text += "• Consider using cached data if available"
        else:
            error_text += "• Try refreshing the data\n"
            error_text += "• Check the application logs for more details\n"
            error_text += "• Contact support if the problem persists"

        self.update_progress(0, error_text)

    def set_category_network_error(self, category: str, error_message: str = ""):
        """Set a category to network error state"""
        if category in self.category_widgets:
            message = error_message or "Network error - using cache"
            self.category_widgets[category].set_network_error(message)

    def set_category_stale(self, category: str, age_info: str = ""):
        """Set a category to stale data state"""
        if category in self.category_widgets:
            message = f"Stale data{' - ' + age_info if age_info else ''}"
            self.category_widgets[category].set_stale(message)
