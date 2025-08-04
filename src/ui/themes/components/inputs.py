"""
Input component styles using design tokens
"""

def get_input_styles(tokens: dict) -> str:
    """Generate input field styles from design tokens"""
    
    colors = tokens['colors']
    typography = tokens['typography']
    spacing = tokens['spacing']
    borders = tokens['borders']
    
    return f"""
/* INPUT FIELD STYLES */

/* Base input styling */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_sm']};
    padding: {spacing['sm']};
    font-size: {typography['size_base']};
    selection-background-color: {colors['selection_background']};
    selection-color: {colors['selection_text']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: {borders['width_base']} solid {colors['focus_ring']};
    outline: none;
}}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_disabled']};
    border-color: {colors['primary_border']};
}}

/* Spin box styling */
QSpinBox, QDoubleSpinBox {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_sm']};
    padding: {spacing['sm']};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: {borders['width_base']} solid {colors['focus_ring']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    background-color: {colors['primary_surface_variant']};
    border: none;
    border-radius: {borders['radius_sm']};
    width: 16px;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
    background-color: {colors['accent_primary']};
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {colors['primary_surface_variant']};
    border: none;
    border-radius: {borders['radius_sm']};
    width: 16px;
}}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {colors['accent_primary']};
}}

/* Combo box styling */
QComboBox {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_sm']};
    padding: {spacing['sm']};
    min-width: 100px;
}}

QComboBox:focus {{
    border: {borders['width_base']} solid {colors['focus_ring']};
}}

QComboBox::drop-down {{
    background-color: {colors['primary_surface_variant']};
    border: none;
    width: 20px;
    border-radius: {borders['radius_sm']};
}}

QComboBox::drop-down:hover {{
    background-color: {colors['accent_primary']};
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_sm']};
    selection-background-color: {colors['accent_primary']};
    selection-color: {colors['text_inverse']};
}}

QComboBox QAbstractItemView::item {{
    padding: {spacing['sm']};
    border: none;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {colors['accent_primary_hover']};
}}

/* Slider styling */
QSlider::groove:horizontal {{
    background-color: {colors['primary_surface_variant']};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {colors['accent_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -6px 0;
}}

QSlider::handle:horizontal:hover {{
    background-color: {colors['accent_primary_hover']};
}}

QSlider::groove:vertical {{
    background-color: {colors['primary_surface_variant']};
    width: 6px;
    border-radius: 3px;
}}

QSlider::handle:vertical {{
    background-color: {colors['accent_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: 0 -6px;
}}

QSlider::handle:vertical:hover {{
    background-color: {colors['accent_primary_hover']};
}}

/* Search input styling */
#expenseSearchFrame {{
    background-color: {colors['primary_surface']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    padding: {spacing['base']};
}}

/* Filter input styling */
QLineEdit[role="filter"] {{
    background-color: {colors['primary_surface']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    padding: {spacing['sm']} {spacing['base']};
    font-size: {typography['size_sm']};
}}

QLineEdit[role="filter"]:focus {{
    border-color: {colors['accent_primary']};
}}

/* Date/time input styling */
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
    border-radius: {borders['radius_sm']};
}}

QDateEdit::drop-down:hover, QTimeEdit::drop-down:hover, QDateTimeEdit::drop-down:hover {{
    background-color: {colors['accent_primary']};
}}

/* Calendar popup styling */
QCalendarWidget {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
}}

QCalendarWidget QWidget {{
    alternate-background-color: {colors['primary_surface_variant']};
}}

QCalendarWidget QAbstractItemView:enabled {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    selection-background-color: {colors['accent_primary']};
    selection-color: {colors['text_inverse']};
}}

QCalendarWidget QAbstractItemView::item:hover {{
    background-color: {colors['accent_primary_hover']};
}}

/* Text area styling */
QTextEdit {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    padding: {spacing['sm']};
    font-family: {typography['font_family']};
    font-size: {typography['size_base']};
}}

QPlainTextEdit {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    padding: {spacing['sm']};
    font-family: {typography['font_family_mono']};
    font-size: {typography['size_base']};
}}

/* Input validation states */
QLineEdit[state="error"], QTextEdit[state="error"], QComboBox[state="error"] {{
    border-color: {colors['error']};
}}

QLineEdit[state="warning"], QTextEdit[state="warning"], QComboBox[state="warning"] {{
    border-color: {colors['warning']};
}}

QLineEdit[state="success"], QTextEdit[state="success"], QComboBox[state="success"] {{
    border-color: {colors['success']};
}}
"""
