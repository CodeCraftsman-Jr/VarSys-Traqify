"""
Global widget styles using design tokens
"""

def get_global_styles(tokens: dict) -> str:
    """Generate global widget styles from design tokens"""
    
    colors = tokens['colors']
    typography = tokens['typography']
    spacing = tokens['spacing']
    borders = tokens['borders']
    
    return f"""
/* GLOBAL WIDGET STYLES */

/* Base widget styling */
QWidget {{
    background-color: {colors['primary_background']};
    color: {colors['text_primary']};
    font-family: {typography['font_family']};
    font-size: {typography['size_base']};
}}

/* Frame styling */
QFrame {{
    background-color: {colors['primary_surface']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    color: {colors['text_primary']};
}}

/* Group box styling */
QGroupBox {{
    background-color: {colors['primary_surface']};
    border: {borders['width_base']} solid {colors['primary_border']};
    border-radius: {borders['radius_lg']};
    margin-top: {spacing['base']};
    padding-top: {spacing['lg']};
    color: {colors['text_primary']};
    font-weight: {typography['weight_bold']};
    font-size: {typography['size_lg']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: {spacing['base']};
    padding: {spacing['sm']} {spacing['base']};
    background-color: {colors['primary_background']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    color: {colors['text_primary']};
}}

/* Label styling */
QLabel {{
    background-color: transparent;
    color: {colors['text_primary']};
}}

/* Dialog styling */
QDialog {{
    background-color: {colors['primary_background']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
}}

/* Message box styling */
QMessageBox {{
    background-color: {colors['primary_background']};
    color: {colors['text_primary']};
}}

QMessageBox QLabel {{
    background-color: transparent;
    color: {colors['text_primary']};
}}

QMessageBox QPushButton {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    padding: {spacing['sm']} {spacing['base']};
    min-width: 60px;
    font-size: {typography['size_sm']};
}}

QMessageBox QPushButton:hover {{
    background-color: {colors['accent_primary']};
}}

QMessageBox QPushButton:pressed {{
    background-color: {colors['accent_primary_pressed']};
}}

/* Tooltip styling */
QToolTip {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    padding: {spacing['sm']};
    font-size: {typography['size_sm']};
}}

/* Main window styling */
QMainWindow {{
    background-color: {colors['primary_background']};
    color: {colors['text_primary']};
}}

/* Status bar styling */
QStatusBar {{
    background-color: {colors['primary_surface_variant']};
    border-top: {borders['width_thin']} solid {colors['primary_border']};
    color: {colors['text_secondary']};
}}

/* Menu bar styling */
QMenuBar {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border-bottom: {borders['width_thin']} solid {colors['primary_border']};
}}

QMenuBar::item {{
    background-color: transparent;
    padding: {spacing['sm']};
}}

QMenuBar::item:selected {{
    background-color: {colors['accent_primary']};
}}

QMenuBar::item:pressed {{
    background-color: {colors['accent_primary_pressed']};
}}

/* Menu styling */
QMenu {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
}}

QMenu::item {{
    padding: {spacing['sm']} {spacing['base']};
}}

QMenu::item:selected {{
    background-color: {colors['accent_primary']};
}}

QMenu::separator {{
    height: {borders['width_thin']};
    background-color: {colors['primary_border']};
    margin: {spacing['sm']} 0;
}}

/* Scroll bar styling */
QScrollBar:vertical {{
    background-color: {colors['primary_surface_variant']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {colors['primary_border']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['accent_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {colors['primary_surface_variant']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors['primary_border']};
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors['accent_secondary']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
}}

/* Progress bar styling */
QProgressBar {{
    background-color: {colors['primary_surface']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    text-align: center;
    color: {colors['text_primary']};
}}

QProgressBar::chunk {{
    background-color: {colors['accent_primary']};
    border-radius: {borders['radius_base']};
}}

/* Splitter styling */
QSplitter::handle {{
    background-color: {colors['primary_border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* Global selection styling */
* {{
    selection-background-color: {colors['selection_background']};
    selection-color: {colors['selection_text']};
}}

/* Web engine view styling */
QWebEngineView {{
    background-color: {colors['primary_background']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
}}

/* Date/time edit styling */
QDateEdit, QTimeEdit, QDateTimeEdit {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_sm']};
    padding: {spacing['sm']};
}}

QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
    border: {borders['width_base']} solid {colors['focus_ring']};
}}

QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {{
    background-color: {colors['primary_surface_variant']};
    border: none;
    width: 20px;
}}

/* Calendar widget styling */
QCalendarWidget {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    selection-background-color: {colors['accent_primary']};
}}

QCalendarWidget QAbstractItemView::item:selected {{
    background-color: {colors['accent_primary']};
    color: {colors['text_primary']};
}}

QCalendarWidget QAbstractItemView::item:hover {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
}}
"""
