"""
Theme Switch Loading Overlay
Provides visual feedback during theme transitions
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QGraphicsOpacityEffect, QApplication
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    Signal, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtGui import QFont, QPainter, QColor, QBrush


class ThemeSwitchOverlay(QWidget):
    """
    Overlay widget that displays during theme switching with smooth animations
    """
    
    # Signals
    animation_finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # State tracking
        self.is_visible = False
        self.current_step = 0
        self.total_steps = 4
        
        # Animation properties
        self.opacity_effect = None
        self.fade_in_animation = None
        self.fade_out_animation = None
        self.progress_animation = None
        self.animation_group = None
        
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """Setup the overlay UI"""
        # Make widget frameless and stay on top
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create semi-transparent background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 8px;
            }
        """)
        
        # Content container
        content_widget = QWidget()
        content_widget.setFixedSize(300, 120)
        content_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 0.95);
                border: 2px solid rgba(14, 99, 156, 0.8);
                border-radius: 12px;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Title label
        self.title_label = QLabel("Switching Theme")
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: transparent;
                border: none;
            }
        """)
        content_layout.addWidget(self.title_label)
        
        # Status label
        self.status_label = QLabel("Preparing theme switch...")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                background-color: transparent;
                border: none;
            }
        """)
        content_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(62, 62, 66, 0.8);
                border: 1px solid rgba(62, 62, 66, 0.5);
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0e639c, stop:0.5 #1177bb, stop:1 #0e639c);
                border-radius: 3px;
            }
        """)
        content_layout.addWidget(self.progress_bar)
        
        # Center the content widget
        layout.addWidget(content_widget, 0, Qt.AlignCenter)
        
    def setup_animations(self):
        """Setup fade animations"""
        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(200)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out_animation.finished.connect(self.hide)
        self.fade_out_animation.finished.connect(self.animation_finished.emit)
        
        # Progress animation
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(300)
        self.progress_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def show_overlay(self, parent_widget=None):
        """Show the overlay with fade-in animation"""
        if self.is_visible:
            return
            
        self.is_visible = True
        self.current_step = 0
        
        # Position overlay over parent widget
        if parent_widget:
            parent_rect = parent_widget.geometry()
            self.setGeometry(parent_rect)
            
        # Reset progress
        self.progress_bar.setValue(0)
        self.status_label.setText("Preparing theme switch...")
        
        # Show and animate
        self.show()
        self.raise_()
        self.fade_in_animation.start()
        
        self.logger.debug("Theme switch overlay shown")
        
    def hide_overlay(self):
        """Hide the overlay with fade-out animation"""
        if not self.is_visible:
            return
            
        self.is_visible = False
        self.fade_out_animation.start()
        
        self.logger.debug("Theme switch overlay hiding")
        
    def update_progress(self, step: int, message: str = None):
        """Update progress and status message"""
        self.current_step = step
        progress_value = int((step / self.total_steps) * 100)
        
        # Animate progress bar
        self.progress_animation.setStartValue(self.progress_bar.value())
        self.progress_animation.setEndValue(progress_value)
        self.progress_animation.start()
        
        # Update status message
        if message:
            self.status_label.setText(message)
            
        # Process events to ensure smooth animation
        QApplication.processEvents()
        
        self.logger.debug(f"Progress updated: {progress_value}% - {message}")
        
    def set_total_steps(self, total: int):
        """Set total number of steps for progress calculation"""
        self.total_steps = max(1, total)
        
    def complete_progress(self):
        """Complete the progress and hide overlay"""
        self.update_progress(self.total_steps, "Theme switch complete!")
        
        # Brief delay to show completion
        QTimer.singleShot(300, self.hide_overlay)


class ThemeSwitchManager:
    """
    Manager class for coordinating theme switches with visual feedback
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.overlay = None
        self.is_switching = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def switch_theme_with_feedback(self, theme: str, style_manager):
        """
        Switch theme with visual feedback and progress indication
        """
        if self.is_switching:
            self.logger.warning("Theme switch already in progress, ignoring request")
            return
            
        self.is_switching = True
        
        try:
            # Create overlay if needed
            if not self.overlay:
                self.overlay = ThemeSwitchOverlay(self.main_window)
                
            # Show overlay
            self.overlay.show_overlay(self.main_window)
            
            # Step 1: Prepare theme switch
            self.overlay.update_progress(1, "Preparing theme switch...")
            QApplication.processEvents()
            
            # Step 2: Generate stylesheet
            self.overlay.update_progress(2, "Generating stylesheet...")
            QApplication.processEvents()
            
            # Get stylesheet (this is the heavy operation)
            stylesheet = style_manager.get_stylesheet(theme)
            
            # Step 3: Apply theme
            self.overlay.update_progress(3, "Applying theme...")
            QApplication.processEvents()
            
            # Apply stylesheet and palette
            if style_manager.app:
                style_manager.app.setStyleSheet(stylesheet)
                palette = style_manager._get_palette(theme)
                style_manager.app.setPalette(palette)
                
            # Step 4: Finalize
            self.overlay.update_progress(4, "Finalizing...")
            QApplication.processEvents()
            
            # Configure Plotly theme
            from .plotly_theme import configure_plotly_dark_theme
            configure_plotly_dark_theme()
            
            # Complete and hide overlay
            self.overlay.complete_progress()
            
            self.logger.info(f"Theme switched to {theme} with visual feedback")
            
        except Exception as e:
            self.logger.error(f"Error during theme switch: {e}")
            if self.overlay:
                self.overlay.hide_overlay()
        finally:
            self.is_switching = False
            
    def cleanup(self):
        """Cleanup resources"""
        if self.overlay:
            self.overlay.hide()
            self.overlay.deleteLater()
            self.overlay = None
