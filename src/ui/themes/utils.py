"""
Theme utility functions for calendar and other UI components
"""

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QColor, QTextCharFormat, QBrush
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QColor, QTextCharFormat, QBrush
    except ImportError:
        from PyQt5.QtCore import QApplication
        from PyQt5.QtGui import QColor, QTextCharFormat, QBrush
from .base.tokens import get_calendar_colors


def get_current_theme() -> str:
    """
    Get the current application theme
    
    Returns:
        str: Current theme name ('light', 'dark', 'colorwave')
    """
    app = QApplication.instance()
    if hasattr(app, 'current_theme'):
        return app.current_theme
    else:
        # Fallback: detect theme from palette
        if app:
            palette = app.palette()
            bg_color = palette.color(palette.Window)
            # Simple heuristic: if background is dark, assume dark theme
            return 'dark' if bg_color.lightness() < 128 else 'light'
        return 'dark'  # Default fallback


def get_calendar_color_for_state(state: str, theme: str = None) -> QColor:
    """
    Get QColor for a specific calendar state based on current theme
    
    Args:
        state: One of 'success', 'warning', 'error', 'neutral'
        theme: Theme name (if None, uses current theme)
    
    Returns:
        QColor: Appropriate color for the state and theme
    """
    if theme is None:
        theme = get_current_theme()
    
    colors = get_calendar_colors(theme)
    color_hex = colors.get(state, colors['neutral'])
    return QColor(color_hex)


def get_calendar_text_color_for_state(state: str, theme: str = None) -> QColor:
    """
    Get text QColor for a specific calendar state based on current theme
    
    Args:
        state: One of 'success', 'warning', 'error', 'neutral'
        theme: Theme name (if None, uses current theme)
    
    Returns:
        QColor: Appropriate text color for the state and theme
    """
    if theme is None:
        theme = get_current_theme()
    
    colors = get_calendar_colors(theme)
    text_key = f"{state}_text"
    color_hex = colors.get(text_key, colors['neutral_text'])
    return QColor(color_hex)


def create_calendar_text_format(state: str, theme: str = None) -> QTextCharFormat:
    """
    Create a QTextCharFormat for calendar dates with appropriate colors
    
    Args:
        state: One of 'success', 'warning', 'error', 'neutral'
        theme: Theme name (if None, uses current theme)
    
    Returns:
        QTextCharFormat: Formatted text format with background and foreground colors
    """
    if theme is None:
        theme = get_current_theme()
    
    format = QTextCharFormat()
    
    # Set background color
    bg_color = get_calendar_color_for_state(state, theme)
    format.setBackground(QBrush(bg_color))
    
    # Set text color
    text_color = get_calendar_text_color_for_state(state, theme)
    format.setForeground(QBrush(text_color))
    
    return format


def get_calendar_color_with_alpha(state: str, alpha: int = 255, theme: str = None) -> QColor:
    """
    Get QColor for a specific calendar state with custom alpha transparency
    
    Args:
        state: One of 'success', 'warning', 'error', 'neutral'
        alpha: Alpha value (0-255, where 255 is fully opaque)
        theme: Theme name (if None, uses current theme)
    
    Returns:
        QColor: Color with specified alpha transparency
    """
    color = get_calendar_color_for_state(state, theme)
    color.setAlpha(alpha)
    return color
