"""
Visual Unavailability Cards System
Creates informative cards to display when data is unavailable in investment tabs
"""

import logging
from datetime import datetime
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QTextEdit, QGroupBox, QListWidget,
    QListWidgetItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QPixmap

from .data_availability_analyzer import UnavailabilityInfo, SeverityLevel


class UnavailabilityCard(QFrame):
    """A card widget that displays detailed information about why data is unavailable"""
    
    retry_requested = Signal()
    symbol_suggestion_clicked = Signal(str)
    
    def __init__(self, unavailability_info: UnavailabilityInfo, parent=None):
        super().__init__(parent)
        self.unavailability_info = unavailability_info
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Set up the card UI"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        self.create_header_section(layout)
        
        # Description section
        self.create_description_section(layout)
        
        # Actionable guidance section
        if self.unavailability_info.actionable_guidance:
            self.create_guidance_section(layout)
        
        # Alternative sources section
        if self.unavailability_info.alternative_sources:
            self.create_alternatives_section(layout)
        
        # Symbol suggestions section
        if self.unavailability_info.symbol_suggestions:
            self.create_suggestions_section(layout)
        
        # Action buttons section
        self.create_action_buttons_section(layout)
        
        # Footer with metadata
        self.create_footer_section(layout)
    
    def create_header_section(self, layout: QVBoxLayout):
        """Create the header section with icon and title"""
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(self.unavailability_info.icon)
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(40, 40)
        header_layout.addWidget(icon_label)
        
        # Title and severity
        title_layout = QVBoxLayout()
        
        title_label = QLabel(self.unavailability_info.title)
        title_font = QFont("Arial", 14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        # Severity indicator
        severity_label = QLabel(f"Severity: {self.unavailability_info.severity.value.title()}")
        severity_font = QFont("Arial", 10)
        severity_label.setFont(severity_font)
        severity_label.setStyleSheet(self.get_severity_style())
        title_layout.addWidget(severity_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
    
    def create_description_section(self, layout: QVBoxLayout):
        """Create the description section"""
        desc_label = QLabel("Description:")
        desc_font = QFont("Arial", 11)
        desc_font.setBold(True)
        desc_label.setFont(desc_font)
        layout.addWidget(desc_label)
        
        desc_text = QLabel(self.unavailability_info.description)
        desc_text.setWordWrap(True)
        desc_text.setFont(QFont("Arial", 10))
        desc_text.setStyleSheet("color: #555; margin-left: 10px; margin-bottom: 10px;")
        layout.addWidget(desc_text)
    
    def create_guidance_section(self, layout: QVBoxLayout):
        """Create the actionable guidance section"""
        guidance_group = QGroupBox("💡 What You Can Do")
        guidance_font = QFont("Arial", 11)
        guidance_font.setBold(True)
        guidance_group.setFont(guidance_font)
        guidance_layout = QVBoxLayout(guidance_group)
        
        guidance_list = QListWidget()
        guidance_list.setMaximumHeight(120)
        
        for guidance in self.unavailability_info.actionable_guidance:
            item = QListWidgetItem(f"• {guidance}")
            item.setFont(QFont("Arial", 10))
            guidance_list.addItem(item)
        
        guidance_layout.addWidget(guidance_list)
        layout.addWidget(guidance_group)
    
    def create_alternatives_section(self, layout: QVBoxLayout):
        """Create the alternative sources section"""
        alt_group = QGroupBox("🔄 Alternative Data Sources")
        alt_font = QFont("Arial", 11)
        alt_font.setBold(True)
        alt_group.setFont(alt_font)
        alt_layout = QVBoxLayout(alt_group)
        
        alt_list = QListWidget()
        alt_list.setMaximumHeight(100)
        
        for source in self.unavailability_info.alternative_sources:
            item = QListWidgetItem(f"• {source}")
            item.setFont(QFont("Arial", 10))
            alt_list.addItem(item)
        
        alt_layout.addWidget(alt_list)
        layout.addWidget(alt_group)
    
    def create_suggestions_section(self, layout: QVBoxLayout):
        """Create the symbol suggestions section"""
        sugg_group = QGroupBox("🔍 Symbol Suggestions")
        sugg_font = QFont("Arial", 11)
        sugg_font.setBold(True)
        sugg_group.setFont(sugg_font)
        sugg_layout = QVBoxLayout(sugg_group)
        
        for suggestion in self.unavailability_info.symbol_suggestions:
            if suggestion.startswith("Try"):
                # This is a general suggestion, not a clickable symbol
                sugg_label = QLabel(f"• {suggestion}")
                sugg_label.setFont(QFont("Arial", 10))
                sugg_label.setStyleSheet("color: #666; margin: 2px;")
                sugg_layout.addWidget(sugg_label)
            else:
                # This is a clickable symbol suggestion
                sugg_button = QPushButton(suggestion)
                sugg_button.setFont(QFont("Arial", 10))
                sugg_button.setStyleSheet("""
                    QPushButton {
                        background-color: #e3f2fd;
                        border: 1px solid #2196f3;
                        border-radius: 4px;
                        padding: 5px 10px;
                        text-align: left;
                        margin: 2px;
                    }
                    QPushButton:hover {
                        background-color: #bbdefb;
                    }
                """)
                sugg_button.clicked.connect(lambda checked, s=suggestion: self.symbol_suggestion_clicked.emit(s))
                sugg_layout.addWidget(sugg_button)
        
        layout.addWidget(sugg_group)
    
    def create_action_buttons_section(self, layout: QVBoxLayout):
        """Create the action buttons section"""
        button_layout = QHBoxLayout()
        
        # Retry button (if retry suggestion exists)
        if self.unavailability_info.retry_suggestion:
            retry_button = QPushButton("🔄 Retry Fetch")
            retry_font = QFont("Arial", 10)
            retry_font.setBold(True)
            retry_button.setFont(retry_font)
            retry_button.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            retry_button.clicked.connect(self.retry_requested.emit)
            button_layout.addWidget(retry_button)
        
        button_layout.addStretch()
        
        if button_layout.count() > 1:  # Only add if there are actual buttons
            layout.addLayout(button_layout)
    
    def create_footer_section(self, layout: QVBoxLayout):
        """Create the footer section with metadata"""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.HLine)
        footer_frame.setStyleSheet("color: #ccc;")
        layout.addWidget(footer_frame)
        
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(5)
        
        # Expected availability
        if self.unavailability_info.expected_availability:
            exp_label = QLabel(f"ℹ️ {self.unavailability_info.expected_availability}")
            exp_label.setFont(QFont("Arial", 9))
            exp_label.setStyleSheet("color: #666;")
            footer_layout.addWidget(exp_label)
        
        # Last successful fetch
        if self.unavailability_info.last_successful_fetch:
            last_fetch_label = QLabel(f"🕒 Last successful fetch: {self.unavailability_info.last_successful_fetch}")
            last_fetch_label.setFont(QFont("Arial", 9))
            last_fetch_label.setStyleSheet("color: #666;")
            footer_layout.addWidget(last_fetch_label)
        
        # Data sources attempted
        if self.unavailability_info.data_sources_attempted:
            sources_text = ", ".join(self.unavailability_info.data_sources_attempted)
            sources_label = QLabel(f"📊 Sources attempted: {sources_text}")
            sources_label.setFont(QFont("Arial", 9))
            sources_label.setStyleSheet("color: #666;")
            sources_label.setWordWrap(True)
            footer_layout.addWidget(sources_label)
        
        # Retry suggestion
        if self.unavailability_info.retry_suggestion:
            retry_label = QLabel(f"💡 {self.unavailability_info.retry_suggestion}")
            retry_font = QFont("Arial", 9)
            retry_font.setItalic(True)
            retry_label.setFont(retry_font)
            retry_label.setStyleSheet("color: #2196f3;")
            retry_label.setWordWrap(True)
            footer_layout.addWidget(retry_label)
        
        if footer_layout.count() > 0:
            layout.addLayout(footer_layout)
    
    def get_severity_style(self) -> str:
        """Get CSS style based on severity level"""
        if self.unavailability_info.severity == SeverityLevel.ERROR:
            return "color: #f44336; font-weight: bold;"
        elif self.unavailability_info.severity == SeverityLevel.WARNING:
            return "color: #ff9800; font-weight: bold;"
        else:  # INFO
            return "color: #2196f3; font-weight: bold;"
    
    def apply_styling(self):
        """Apply overall styling to the card"""
        if self.unavailability_info.severity == SeverityLevel.ERROR:
            border_color = "#f44336"
        elif self.unavailability_info.severity == SeverityLevel.WARNING:
            border_color = "#ff9800"
        else:  # INFO
            border_color = "#2196f3"

        self.setStyleSheet(f"""
            UnavailabilityCard {{
                border: 2px solid {border_color};
                border-radius: 8px;
                margin: 10px;
            }}
        """)


class UnavailabilityContainer(QScrollArea):
    """Container widget for unavailability cards"""
    
    retry_requested = Signal()
    symbol_suggestion_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the container UI"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        self.setWidget(self.content_widget)
    
    def show_unavailability_info(self, unavailability_info: UnavailabilityInfo):
        """Show unavailability information in a card"""
        # Clear existing content
        self.clear_content()
        
        # Create and add unavailability card
        card = UnavailabilityCard(unavailability_info)
        card.retry_requested.connect(self.retry_requested.emit)
        card.symbol_suggestion_clicked.connect(self.symbol_suggestion_clicked.emit)
        
        self.content_layout.addWidget(card)
        self.content_layout.addStretch()
    
    def clear_content(self):
        """Clear all content from the container"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
