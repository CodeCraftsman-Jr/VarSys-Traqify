"""
Button component styles using design tokens
"""

def get_button_styles(tokens: dict) -> str:
    """Generate button styles from design tokens"""
    
    colors = tokens['colors']
    typography = tokens['typography']
    spacing = tokens['spacing']
    borders = tokens['borders']
    
    return f"""
/* BUTTON STYLES */

/* Base button styling */
QPushButton {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
    border: none;
    border-radius: {borders['radius_base']};
    padding: {spacing['sm']} {spacing['base']};
    font-size: {typography['size_sm']};
    font-weight: {typography['weight_normal']};
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {colors['accent_primary_hover']};
}}

QPushButton:pressed {{
    background-color: {colors['accent_primary_pressed']};
}}

QPushButton:disabled {{
    background-color: {colors['text_disabled']};
    color: {colors['text_secondary']};
}}

QPushButton:focus {{
    outline: {borders['width_base']} solid {colors['focus_ring']};
    outline-offset: 2px;
}}

/* Secondary button variant */
QPushButton[variant="secondary"] {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
}}

QPushButton[variant="secondary"]:hover {{
    background-color: {colors['accent_secondary']};
    border-color: {colors['accent_primary']};
}}

QPushButton[variant="secondary"]:pressed {{
    background-color: {colors['primary_border']};
}}

/* Danger button variant */
QPushButton[variant="danger"] {{
    background-color: {colors['error']};
    color: {colors['text_inverse']};
}}

QPushButton[variant="danger"]:hover {{
    background-color: {colors['error_hover']};
}}

/* Success button variant */
QPushButton[variant="success"] {{
    background-color: {colors['success']};
    color: {colors['text_inverse']};
}}

QPushButton[variant="success"]:hover {{
    background-color: {colors['success_hover']};
}}

/* Warning button variant */
QPushButton[variant="warning"] {{
    background-color: {colors['warning']};
    color: {colors['text_inverse']};
}}

QPushButton[variant="warning"]:hover {{
    background-color: {colors['warning_hover']};
}}

/* Small button size */
QPushButton[size="small"] {{
    padding: {spacing['xs']} {spacing['sm']};
    font-size: {typography['size_xs']};
    min-height: 24px;
}}

/* Large button size */
QPushButton[size="large"] {{
    padding: {spacing['base']} {spacing['lg']};
    font-size: {typography['size_lg']};
    min-height: 40px;
}}

/* Icon button styling */
QPushButton[type="icon"] {{
    padding: {spacing['sm']};
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    border-radius: {borders['radius_base']};
}}

/* Flat button styling */
QPushButton[type="flat"] {{
    background-color: transparent;
    color: {colors['text_primary']};
    border: none;
}}

QPushButton[type="flat"]:hover {{
    background-color: {colors['hover_overlay']};
}}

/* Toggle button styling */
QPushButton:checkable {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
}}

QPushButton:checked {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
    border-color: {colors['accent_primary']};
}}

QPushButton:checked:hover {{
    background-color: {colors['accent_primary_hover']};
}}

/* Module-specific button styling */
#expenseAddButton, #expenseEditButton, #expenseDeleteButton, 
#expenseCategoriesButton, #expenseClearFiltersButton,
#incomeAddGoalButton, #habitNavButton, #habitTodayButton, 
#habitManageButton, #habitAddButton,
#attendanceTodayButton, #attendanceSemesterButton, 
#attendanceActionButton, #attendanceNavButton,
#todoAddButton, #todoEditButton, #todoDeleteButton,
#investmentAddButton, #budgetAddButton, #tradingActionButton {{
    background-color: {colors['accent_primary']};
    border: none;
    color: {colors['text_inverse']};
    padding: {spacing['sm']} {spacing['base']};
    border-radius: {borders['radius_base']};
    font-size: {typography['size_sm']};
    min-height: 32px;
    max-height: 32px;
}}

#expenseAddButton:hover, #expenseEditButton:hover, #expenseDeleteButton:hover,
#expenseCategoriesButton:hover, #expenseClearFiltersButton:hover,
#incomeAddGoalButton:hover, #habitNavButton:hover, #habitTodayButton:hover,
#habitManageButton:hover, #habitAddButton:hover,
#attendanceTodayButton:hover, #attendanceSemesterButton:hover,
#attendanceActionButton:hover, #attendanceNavButton:hover,
#todoAddButton:hover, #todoEditButton:hover, #todoDeleteButton:hover,
#investmentAddButton:hover, #budgetAddButton:hover, #tradingActionButton:hover {{
    background-color: {colors['accent_primary_hover']};
}}

#expenseEditButton:disabled, #expenseDeleteButton:disabled,
#habitNavButton:disabled, #attendanceNavButton:disabled,
#todoEditButton:disabled, #todoDeleteButton:disabled {{
    background-color: {colors['text_disabled']};
    color: {colors['text_secondary']};
}}

/* Quick action buttons */
#expenseQuickButton, #incomeQuickButton, #habitQuickButton {{
    background-color: {colors['accent_primary']};
    border: none;
    color: {colors['text_inverse']};
    padding: {spacing['base']};
    border-radius: {borders['radius_lg']};
    font-size: {typography['size_base']};
    font-weight: {typography['weight_bold']};
    min-height: 48px;
}}

#expenseQuickButton:hover, #incomeQuickButton:hover, #habitQuickButton:hover {{
    background-color: {colors['accent_primary_hover']};
    transform: translateY(-1px);
}}

/* Refresh button */
#refreshButton {{
    background-color: {colors['accent_primary']};
    border: none;
    color: {colors['text_inverse']};
    padding: {spacing['sm']} {spacing['base']};
    border-radius: {borders['radius_base']};
    font-size: {typography['size_sm']};
}}

#refreshButton:hover {{
    background-color: {colors['accent_primary_hover']};
}}

/* Toggle button for sidebar */
#toggleButton {{
    background-color: {colors['primary_surface_variant']};
    border: none;
    border-radius: {borders['radius_base']};
    color: {colors['text_primary']};
    font-size: {typography['size_lg']};
    padding: {spacing['sm']};
}}

#toggleButton:hover {{
    background-color: {colors['accent_secondary']};
}}

/* Tool button styling */
QToolButton {{
    background-color: transparent;
    border: none;
    color: {colors['text_primary']};
    padding: {spacing['sm']};
    border-radius: {borders['radius_base']};
}}

QToolButton:hover {{
    background-color: {colors['hover_overlay']};
}}

QToolButton:pressed {{
    background-color: {colors['primary_surface_variant']};
}}

QToolButton:checked {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
}}

/* Radio button styling */
QRadioButton {{
    color: {colors['text_primary']};
    spacing: {spacing['sm']};
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: {borders['width_base']} solid {colors['primary_border']};
    background-color: {colors['primary_surface']};
}}

QRadioButton::indicator:checked {{
    background-color: {colors['accent_primary']};
    border-color: {colors['accent_primary']};
}}

QRadioButton::indicator:hover {{
    border-color: {colors['accent_primary_hover']};
}}

/* Checkbox styling */
QCheckBox {{
    color: {colors['text_primary']};
    spacing: {spacing['sm']};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: {borders['width_base']} solid {colors['primary_border']};
    border-radius: {borders['radius_sm']};
    background-color: {colors['primary_surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['accent_primary']};
    border-color: {colors['accent_primary']};
}}

QCheckBox::indicator:hover {{
    border-color: {colors['accent_primary_hover']};
}}

QCheckBox::indicator:checked:hover {{
    background-color: {colors['accent_primary_hover']};
}}
"""
