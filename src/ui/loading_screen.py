#!/usr/bin/env python3
"""
Loading Screen Module
Provides a comprehensive loading screen with progress tracking and animations
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QFrame, QApplication, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, QSequentialAnimationGroup, Signal, QThread
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QPen


class LoadingScreen(QWidget):
    """
    Modern loading screen with progress tracking and animations
    """

    # Signals
    loading_complete = Signal()
    progress_updated = Signal(int, str)  # progress, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Loading state
        self.current_progress = 0
        self.loading_steps = {}
        self.total_steps = 0
        self.completed_steps = 0

        # Animation components
        self.animations = QParallelAnimationGroup()
        self.fade_animation = None

        # Theme support
        self.current_theme = 'dark'  # Default theme

        # Setup UI
        self.setup_ui()
        self.setup_animations()

        # Auto-hide timer (fallback)
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.force_close)
        
    def setup_ui(self):
        """Setup the enhanced loading screen UI with better visibility and layout"""
        # Window properties - generous size for comfortable spacing and excellent readability
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(800, 650)  # Larger size to accommodate generous spacing

        # Center on screen
        self.center_on_screen()

        # Main layout - no padding for cleaner look
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create main container with enhanced styling for better text visibility
        self.main_container = QFrame()
        self.main_container.setObjectName("mainContainer")
        # Initial styling will be applied by apply_theme_styling()
        main_layout.addWidget(self.main_container)

        # Content layout with generous spacing for excellent readability
        content_layout = QVBoxLayout(self.main_container)
        content_layout.setContentsMargins(40, 35, 40, 25)  # Generous margins all around
        content_layout.setSpacing(25)  # Much more spacing between major sections

        # Logo/Title section
        self.setup_header(content_layout)

        # Progress section
        self.setup_progress_section(content_layout)

        # Status section
        self.setup_status_section(content_layout)

        # Footer section
        self.setup_footer(content_layout)

        # Apply initial theme styling
        self.apply_theme_styling()

    def setup_header(self, layout):
        """Setup clean header with excellent text visibility and proper spacing"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(20)  # Much more generous spacing between header elements

        # Simple, clean app icon with generous size
        self.icon_label = QLabel("💰")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 32))  # Larger, more prominent icon
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedHeight(45)  # More height for better spacing
        self.icon_label.setObjectName("iconLabel")
        # Styling will be applied by apply_theme_styling()
        header_layout.addWidget(self.icon_label)

        # App title with excellent visibility and generous spacing
        self.title_label = QLabel("Personal Finance Dashboard")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))  # Larger, more prominent title
        self.title_label.setFixedHeight(35)  # More height for better spacing
        self.title_label.setObjectName("titleLabel")
        # Styling will be applied by apply_theme_styling()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label)

        # Clean version label with generous spacing
        self.version_label = QLabel("Version 1.0.0")
        self.version_label.setFont(QFont("Segoe UI", 12))  # Larger, more readable font
        self.version_label.setFixedHeight(25)  # More height for better spacing
        self.version_label.setObjectName("versionLabel")
        # Styling will be applied by apply_theme_styling()
        self.version_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.version_label)

        layout.addLayout(header_layout)
        
    def setup_progress_section(self, layout):
        """Setup enhanced progress section with better visibility and compact spacing"""
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(18)  # Generous spacing for excellent visual separation

        # Progress percentage label with enhanced visibility and generous spacing
        self.progress_percentage = QLabel("0%")
        self.progress_percentage.setFont(QFont("Segoe UI", 20, QFont.Bold))  # Larger, more prominent font
        self.progress_percentage.setFixedHeight(45)  # More height for better spacing
        self.progress_percentage.setObjectName("progressPercentage")
        # Styling will be applied by apply_theme_styling()
        self.progress_percentage.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_percentage)

        # Enhanced progress bar with better visibility
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(16)  # Taller progress bar for better visibility
        self.progress_bar.setObjectName("progressBar")
        # Styling will be applied by apply_theme_styling()
        progress_layout.addWidget(self.progress_bar)

        layout.addLayout(progress_layout)

    def setup_status_section(self, layout):
        """Setup enhanced status section with detailed loading information and compact spacing"""
        status_layout = QVBoxLayout()
        status_layout.setSpacing(15)  # Generous spacing for excellent readability

        # Main status label with enhanced visibility and generous spacing
        self.status_label = QLabel("Initializing application...")
        self.status_label.setFont(QFont("Segoe UI", 14, QFont.Medium))  # Larger, more readable font
        self.status_label.setFixedHeight(35)  # More height for better spacing
        self.status_label.setObjectName("statusLabel")
        # Styling will be applied by apply_theme_styling()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        # Detailed status label with enhanced contrast and generous spacing
        self.detail_label = QLabel("Please wait while components are loaded...")
        self.detail_label.setFont(QFont("Segoe UI", 12))  # Larger, more readable font
        self.detail_label.setFixedHeight(30)  # More height for better spacing
        self.detail_label.setObjectName("detailLabel")
        # Styling will be applied by apply_theme_styling()
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setWordWrap(True)
        status_layout.addWidget(self.detail_label)

        # Add detailed loading steps list
        self.setup_loading_steps_section(status_layout)

        layout.addLayout(status_layout)

    def setup_loading_steps_section(self, parent_layout):
        """Setup detailed loading steps display with proper height"""
        # Container for loading steps with better styling and adequate size
        steps_container = QFrame()
        steps_container.setObjectName("stepsContainer")
        # Styling will be applied by apply_theme_styling()
        steps_container.setFixedHeight(160)  # Much more height for comfortable loading details display

        steps_layout = QVBoxLayout(steps_container)
        steps_layout.setContentsMargins(15, 10, 15, 10)  # Generous margins for better spacing
        steps_layout.setSpacing(8)  # More spacing between elements

        # Title for loading steps with generous styling
        steps_title = QLabel("Loading Details:")
        steps_title.setFont(QFont("Segoe UI", 12, QFont.Bold))  # Larger, more prominent font
        steps_title.setFixedHeight(25)  # More height for better spacing
        steps_title.setObjectName("stepsTitle")
        # Styling will be applied by apply_theme_styling()
        steps_layout.addWidget(steps_title)

        # Enhanced scrollable area for loading steps
        from PySide6.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setObjectName("scrollArea")
        # Styling will be applied by apply_theme_styling()

        # Widget to contain the loading steps with proper initialization
        self.steps_widget = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_widget)
        self.steps_layout.setContentsMargins(5, 5, 5, 5)
        self.steps_layout.setSpacing(3)
        self.steps_layout.addStretch()  # Push items to top

        self.scroll_area.setWidget(self.steps_widget)
        steps_layout.addWidget(self.scroll_area)

        parent_layout.addWidget(steps_container)

        # Initialize loading steps tracking with proper defaults
        self.loading_steps_labels = []
        self.current_step_index = 0

        # Add initial placeholder to show the section is working
        self.add_loading_step("Initializing loading system...", "complete")
        
    def setup_footer(self, layout):
        """Setup clean footer section with comfortable spacing"""
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(8)  # Comfortable spacing for better visual balance

        # Simple loading dots without container borders - more compact
        dots_layout = QHBoxLayout()
        dots_layout.addStretch()

        # Create clean animated dots with smaller size
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setFont(QFont("Segoe UI", 14))  # Larger, more visible dots
            dot.setFixedHeight(20)  # More height for better spacing
            dot.setObjectName(f"dot_{i}")
            # Styling will be applied by apply_theme_styling()
            dot.setAlignment(Qt.AlignCenter)
            self.dots.append(dot)
            dots_layout.addWidget(dot)

        dots_layout.addStretch()
        footer_layout.addLayout(dots_layout)

        # Clean footer text with comfortable spacing
        self.footer_text = QLabel("© 2025 Traqify")  # Updated year and shortened text
        self.footer_text.setFont(QFont("Segoe UI", 10))  # Larger, more readable font
        self.footer_text.setFixedHeight(20)  # More height for better spacing
        self.footer_text.setObjectName("footerText")
        # Styling will be applied by apply_theme_styling()
        self.footer_text.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(self.footer_text)

        layout.addLayout(footer_layout)
        
    def setup_animations(self):
        """Setup modern loading animations"""
        # Enhanced dots animation
        self.dots_timer = QTimer()
        self.dots_timer.timeout.connect(self.animate_dots)
        self.dots_timer.start(400)  # Faster animation
        self.dots_state = 0

        # Fade in animation with smoother transition
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(800)  # Longer, smoother fade
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Add subtle scale animation for the main container
        self.scale_animation = QPropertyAnimation(self.main_container, b"geometry")
        self.scale_animation.setDuration(800)
        self.scale_animation.setEasingCurve(QEasingCurve.OutBack)
        
    def center_on_screen(self):
        """Center the loading screen on the primary screen"""
        if QApplication.instance():
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                x = (screen_geometry.width() - self.width()) // 2
                y = (screen_geometry.height() - self.height()) // 2
                self.move(x, y)
                
    def animate_dots(self):
        """Animate the clean loading dots"""
        # Simple, clean animation patterns
        patterns = [
            [1.0, 0.4, 0.4],  # First dot bright
            [0.4, 1.0, 0.4],  # Second dot bright
            [0.4, 0.4, 1.0],  # Third dot bright
            [0.6, 0.6, 0.6],  # All medium
        ]

        if hasattr(self, 'dots') and self.dots:
            pattern = patterns[self.dots_state % len(patterns)]
            colors = self.get_theme_colors()
            # Extract RGB values from text color for opacity animation
            text_color = colors['text_color']
            if text_color.startswith('#'):
                # Convert hex to RGB
                hex_color = text_color.lstrip('#')
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                base_color = f"{r}, {g}, {b}"
            else:
                # Default to white if parsing fails
                base_color = "255, 255, 255"

            for i, dot in enumerate(self.dots):
                opacity = pattern[i]
                dot.setStyleSheet(f"""
                    QLabel {{
                        color: rgba({base_color}, {opacity});
                        background: transparent;
                        padding: 0 4px;
                        border: none;
                    }}
                """)

        self.dots_state = (self.dots_state + 1) % len(patterns)

    def show_loading(self):
        """Show the loading screen with fade-in animation"""
        # Force reset progress to 0 before showing
        self.current_progress = 0

        # Force reset the progress bar to 0
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.setValue(0)

        # Reset percentage label to 0%
        if hasattr(self, 'progress_percentage') and self.progress_percentage:
            self.progress_percentage.setText("0%")

        self.show()
        self.raise_()
        self.activateWindow()

        # Force immediate UI update before animations
        QApplication.processEvents()

        # Force repaint to ensure visual update
        self.repaint()
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.repaint()
        if hasattr(self, 'progress_percentage') and self.progress_percentage:
            self.progress_percentage.repaint()

        # Start fade-in animation
        self.fade_in_animation.start()

        # Start auto-hide timer (60 seconds fallback - increased for slow initialization)
        self.auto_hide_timer.start(60000)

        # Process events to ensure immediate display
        QApplication.processEvents()

    def add_loading_step(self, step_text: str, status: str = "pending"):
        """Add a new loading step to the detailed view with enhanced visibility"""
        if not hasattr(self, 'steps_layout') or not self.steps_layout:
            return  # Safety check

        step_label = QLabel()
        step_label.setFont(QFont("Segoe UI", 10))  # Slightly larger font
        step_label.setWordWrap(True)
        step_label.setMinimumHeight(20)  # Ensure minimum height for visibility

        # Set initial status
        self.update_step_status(step_label, step_text, status)

        # Insert before the stretch
        self.steps_layout.insertWidget(self.steps_layout.count() - 1, step_label)
        self.loading_steps_labels.append(step_label)

        # Auto-scroll to bottom with improved logic
        QApplication.processEvents()
        if hasattr(self, 'scroll_area') and self.scroll_area:
            QTimer.singleShot(50, self._scroll_to_bottom)  # Delayed scroll for better reliability

    def _scroll_to_bottom(self):
        """Helper method to scroll to bottom"""
        if hasattr(self, 'scroll_area') and self.scroll_area:
            scrollbar = self.scroll_area.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())

    def update_step_status(self, label: QLabel, text: str, status: str):
        """Update the status of a loading step with enhanced styling"""
        if status == "pending":
            icon = "⏳"
            color = "#f0f0f0"
            bg_color = "rgba(255, 255, 255, 0.05)"
        elif status == "loading":
            icon = "🔄"
            color = "#81C784"
            bg_color = "rgba(129, 199, 132, 0.1)"
        elif status == "complete":
            icon = "✅"
            color = "#4CAF50"
            bg_color = "rgba(76, 175, 80, 0.1)"
        elif status == "error":
            icon = "❌"
            color = "#f44336"
            bg_color = "rgba(244, 67, 54, 0.1)"
        else:
            icon = "⏳"
            color = "#f0f0f0"
            bg_color = "rgba(255, 255, 255, 0.05)"

        label.setText(f"{icon} {text}")
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background: {bg_color};
                padding: 4px 8px;
                border: none;
                border-radius: 4px;
                margin: 1px 0;
                font-weight: bold;
            }}
        """)

    def update_current_step(self, step_text: str, status: str = "loading"):
        """Update the current loading step"""
        if self.current_step_index < len(self.loading_steps_labels):
            label = self.loading_steps_labels[self.current_step_index]
            self.update_step_status(label, step_text, status)

            if status == "complete":
                self.current_step_index += 1

    def complete_current_step(self, step_text: str):
        """Mark the current step as complete and move to next"""
        self.update_current_step(step_text, "complete")

    def update_progress(self, progress: int, message: str = "", detail: str = "", step_detail: str = ""):
        """Update the loading progress with enhanced detailed information and better reliability"""
        # Ensure progress is within valid range
        self.current_progress = max(0, min(100, progress))

        # Ensure the loading screen is visible and on top
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()

        # Update progress bar with validation
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.setValue(self.current_progress)
            self.progress_bar.repaint()  # Force immediate visual update

        # Update percentage label with enhanced styling
        if hasattr(self, 'progress_percentage') and self.progress_percentage:
            self.progress_percentage.setText(f"{self.current_progress}%")
            self.progress_percentage.repaint()  # Force immediate visual update
            # Keep the enhanced styling from setup_progress_section

        # Update status messages with validation
        if message and hasattr(self, 'status_label') and self.status_label:
            self.status_label.setText(message)

        if detail and hasattr(self, 'detail_label') and self.detail_label:
            self.detail_label.setText(detail)

        # Add or update detailed step if provided
        if step_detail:
            try:
                if progress < 100:
                    self.add_loading_step(step_detail, "loading")
                else:
                    self.add_loading_step(step_detail, "complete")
            except Exception as e:
                self.logger.debug(f"Error adding loading step: {e}")

        # Emit signal for external listeners
        self.progress_updated.emit(self.current_progress, message)

        # Process events to update UI immediately
        QApplication.processEvents()

        # Show completion effect when complete
        if self.current_progress >= 100:
            self.show_completion_effect()
            # Don't auto-close - let the main application control when to close

    def show_completion_effect(self):
        """Show enhanced completion effect with better visibility"""
        if hasattr(self, 'progress_percentage') and self.progress_percentage:
            self.progress_percentage.setText("✓ Complete!")
            self.progress_percentage.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4CAF50, stop:0.5 #66BB6A, stop:1 #4CAF50);
                    padding: 10px 20px;
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    font-weight: bold;
                }
            """)

        # Add final completion step
        self.add_loading_step("Application ready!", "complete")

    def complete_loading_step(self, step_id: str, message: str = ""):
        """Mark a loading step as complete (legacy method for compatibility)"""
        if hasattr(self, 'loading_steps') and step_id in self.loading_steps and not self.loading_steps[step_id]['completed']:
            self.loading_steps[step_id]['completed'] = True
            self.completed_steps += self.loading_steps[step_id]['weight']

            # Calculate progress
            if self.total_steps > 0:
                progress = int((self.completed_steps / self.total_steps) * 100)
            else:
                progress = 100

            # Update display
            display_message = message or self.loading_steps[step_id]['description']
            self.update_progress(progress, f"✓ {display_message}")

    def close_loading(self):
        """Close the loading screen with fade-out animation"""
        # Stop timers
        self.dots_timer.stop()
        self.auto_hide_timer.stop()

        # Create fade-out animation
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_animation.finished.connect(self.hide)
        self.fade_out_animation.finished.connect(self.loading_complete.emit)

        self.fade_out_animation.start()

    def close_when_ready(self):
        """Close the loading screen when main window is ready"""
        # Stop the auto-hide timer since we're manually controlling closure
        self.auto_hide_timer.stop()

        # Show completion effect if not already shown
        if self.current_progress >= 100:
            self.show_completion_effect()

        # Wait a moment to show completion, then close
        QTimer.singleShot(800, self.close_loading)

    def force_close(self):
        """Force close the loading screen (fallback)"""
        self.logger.warning("Loading screen force closed due to timeout")
        self.close_loading()

    def get_theme_colors(self):
        """Get theme-specific colors"""
        if self.current_theme == 'dark':
            return {
                'background_gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e3c72, stop:0.5 #2a5298, stop:1 #1e3c72)',
                'border_color': 'rgba(255, 255, 255, 0.1)',
                'text_color': '#ffffff',
                'secondary_text_color': '#e8e8e8',
                'tertiary_text_color': '#f0f0f0',
                'footer_text_color': '#c0c0c0',
                'progress_border': 'rgba(255, 255, 255, 0.3)',
                'progress_background': 'rgba(255, 255, 255, 0.1)',
                'progress_chunk': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d4, stop:0.5 #106ebe, stop:1 #005a9e)',
                'container_background': 'rgba(0, 0, 0, 0.3)',
                'container_border': 'rgba(255, 255, 255, 0.2)'
            }
        elif self.current_theme == 'light':
            return {
                'background_gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f0f8ff, stop:0.5 #e6f3ff, stop:1 #f0f8ff)',
                'border_color': 'rgba(0, 0, 0, 0.1)',
                'text_color': '#333333',
                'secondary_text_color': '#555555',
                'tertiary_text_color': '#444444',
                'footer_text_color': '#666666',
                'progress_border': 'rgba(0, 0, 0, 0.3)',
                'progress_background': 'rgba(0, 0, 0, 0.1)',
                'progress_chunk': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d4, stop:0.5 #106ebe, stop:1 #005a9e)',
                'container_background': 'rgba(255, 255, 255, 0.8)',
                'container_border': 'rgba(0, 0, 0, 0.2)'
            }
        elif self.current_theme == 'colorwave':
            return {
                'background_gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:0.5 #764ba2, stop:1 #667eea)',
                'border_color': 'rgba(255, 255, 255, 0.2)',
                'text_color': '#ffffff',
                'secondary_text_color': '#f0f0f0',
                'tertiary_text_color': '#e8e8e8',
                'footer_text_color': '#d0d0d0',
                'progress_border': 'rgba(255, 255, 255, 0.4)',
                'progress_background': 'rgba(255, 255, 255, 0.2)',
                'progress_chunk': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e91e63, stop:0.5 #ad1457, stop:1 #880e4f)',
                'container_background': 'rgba(0, 0, 0, 0.4)',
                'container_border': 'rgba(255, 255, 255, 0.3)'
            }
        else:
            # Default to dark theme
            return self.get_theme_colors()

    def apply_theme(self, theme: str):
        """Apply theme to loading screen"""
        self.current_theme = theme
        self.apply_theme_styling()

    def apply_theme_styling(self):
        """Apply theme-specific styling to all components"""
        colors = self.get_theme_colors()

        # Update main container
        if hasattr(self, 'main_container'):
            self.main_container.setStyleSheet(f"""
                QFrame {{
                    background: {colors['background_gradient']};
                    border-radius: 16px;
                    border: 2px solid {colors['border_color']};
                }}
            """)

        # Update all text labels
        self._update_text_styling(colors)

        # Update progress bar
        self._update_progress_styling(colors)

        # Update containers
        self._update_container_styling(colors)

    def set_version(self, version: str):
        """Set the application version displayed"""
        self.version_label.setText(f"Version {version}")

    def set_title(self, title: str):
        """Set the application title displayed"""
        self.title_label.setText(title)

    def _update_text_styling(self, colors):
        """Update text element styling"""
        if hasattr(self, 'icon_label'):
            self.icon_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text_color']};
                    background: transparent;
                    padding: 2px;
                }}
            """)

        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text_color']};
                    background: transparent;
                    padding: 0px;
                    border: none;
                }}
            """)

        if hasattr(self, 'version_label'):
            self.version_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['secondary_text_color']};
                    background: transparent;
                    padding: 0px;
                    border: none;
                }}
            """)

        if hasattr(self, 'status_label'):
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text_color']};
                    background: {colors['container_background']};
                    padding: 4px 8px;
                    border: none;
                    border-radius: 4px;
                }}
            """)

        if hasattr(self, 'detail_label'):
            self.detail_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['tertiary_text_color']};
                    background: {colors['container_background']};
                    padding: 3px 6px;
                    border: none;
                    border-radius: 3px;
                }}
            """)

        if hasattr(self, 'footer_text'):
            self.footer_text.setStyleSheet(f"""
                QLabel {{
                    color: {colors['footer_text_color']};
                    background: transparent;
                    padding: 4px 0;
                    border: none;
                }}
            """)

    def _update_progress_styling(self, colors):
        """Update progress bar styling"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid {colors['progress_border']};
                    border-radius: 6px;
                    background-color: {colors['progress_background']};
                    text-align: center;
                    font-weight: bold;
                    font-size: 11px;
                }}
                QProgressBar::chunk {{
                    background: {colors['progress_chunk']};
                    border-radius: 4px;
                    margin: 1px;
                }}
            """)

        if hasattr(self, 'progress_percentage'):
            self.progress_percentage.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text_color']};
                    background: {colors['container_background']};
                    padding: 6px 12px;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                }}
            """)

    def _update_container_styling(self, colors):
        """Update container styling"""
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: {colors['container_background']};
                    width: 12px;
                    border-radius: 6px;
                }}
                QScrollBar::handle:vertical {{
                    background: {colors['progress_border']};
                    border-radius: 6px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {colors['text_color']};
                }}
            """)

        # Update steps container if it exists
        for child in self.findChildren(QFrame):
            if child.objectName() == 'stepsContainer':
                child.setStyleSheet(f"""
                    QFrame {{
                        background: {colors['container_background']};
                        border-radius: 8px;
                        border: 1px solid {colors['container_border']};
                        margin: 4px 0;
                    }}
                """)

        # Update steps title if it exists
        for child in self.findChildren(QLabel):
            if child.objectName() == 'stepsTitle':
                child.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_color']};
                        background: transparent;
                        padding: 2px 0;
                        border: none;
                    }}
                """)

        # Update dots
        if hasattr(self, 'dots'):
            for dot in self.dots:
                dot.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_color']};
                        background: transparent;
                        padding: 0 2px;
                        border: none;
                    }}
                """)


class LoadingManager(QThread):
    """
    Thread-safe loading manager that coordinates initialization steps
    """

    # Signals
    step_completed = Signal(str, str)  # step_id, message
    progress_updated = Signal(int, str, str)  # progress, message, detail
    loading_finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Loading steps
        self.steps = []
        self.current_step = 0
        self.total_weight = 0
        self.completed_weight = 0

        # Initialization functions
        self.init_functions = []

    def add_step(self, step_id: str, description: str, init_function=None, weight: int = 1):
        """Add an initialization step"""
        step = {
            'id': step_id,
            'description': description,
            'function': init_function,
            'weight': weight,
            'completed': False
        }
        self.steps.append(step)
        self.total_weight += weight

    def run(self):
        """Execute all initialization steps"""
        try:
            self.logger.info(f"Starting initialization with {len(self.steps)} steps")

            for i, step in enumerate(self.steps):
                self.current_step = i
                step_id = step['id']
                description = step['description']
                function = step['function']

                # Update progress
                progress = int((self.completed_weight / self.total_weight) * 100) if self.total_weight > 0 else 0
                self.progress_updated.emit(progress, f"Loading {description}...", f"Step {i+1} of {len(self.steps)}")

                try:
                    # Execute initialization function if provided
                    if function and callable(function):
                        self.logger.debug(f"Executing step: {step_id}")
                        function()

                    # Mark step as completed
                    step['completed'] = True
                    self.completed_weight += step['weight']

                    # Emit completion signal
                    self.step_completed.emit(step_id, description)

                    # Small delay for visual feedback
                    self.msleep(100)

                except Exception as e:
                    error_msg = f"Error in initialization step '{step_id}': {e}"
                    self.logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    # Continue with other steps

            # Final progress update
            self.progress_updated.emit(100, "Initialization complete!", "Ready to start")
            self.loading_finished.emit()

        except Exception as e:
            error_msg = f"Critical error during initialization: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
