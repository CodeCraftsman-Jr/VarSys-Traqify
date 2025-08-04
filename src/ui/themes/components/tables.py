"""
Table component styles using design tokens
"""

def get_table_styles(tokens: dict) -> str:
    """Generate table styles from design tokens"""
    
    colors = tokens['colors']
    typography = tokens['typography']
    spacing = tokens['spacing']
    borders = tokens['borders']
    
    return f"""
/* TABLE STYLES */

/* Base table styling */
QTableWidget, QTableView {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    selection-background-color: {colors['selection_background']};
    selection-color: {colors['selection_text']};
}}

QTableWidget::item, QTableView::item {{
    color: {colors['text_primary']};
    background-color: transparent;
    padding: {spacing['sm']};
    border: none;
}}

QTableWidget::item:selected, QTableView::item:selected {{
    color: {colors['selection_text']};
    background-color: {colors['selection_background']};
}}

QTableWidget::item:hover, QTableView::item:hover {{
    background-color: {colors['hover_overlay']};
}}

QTableWidget::item:alternate, QTableView::item:alternate {{
    background-color: {colors['primary_surface_variant']};
}}

/* Header styling */
QHeaderView {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: none;
    font-weight: {typography['weight_bold']};
}}

QHeaderView::section {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: none;
    border-right: {borders['width_thin']} solid {colors['primary_border']};
    border-bottom: {borders['width_thin']} solid {colors['primary_border']};
    padding: {spacing['sm']} {spacing['base']};
    font-weight: {typography['weight_bold']};
}}

QHeaderView::section:hover {{
    background-color: {colors['accent_primary_hover']};
}}

QHeaderView::section:pressed {{
    background-color: {colors['accent_primary']};
}}

/* Horizontal header */
QHeaderView::section:horizontal {{
    border-top: none;
}}

/* Vertical header */
QHeaderView::section:vertical {{
    border-left: none;
}}

/* Corner button */
QTableCornerButton::section {{
    background-color: {colors['primary_surface_variant']};
    border: {borders['width_thin']} solid {colors['primary_border']};
}}

/* Tree widget styling */
QTreeWidget, QTreeView {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    selection-background-color: {colors['selection_background']};
    selection-color: {colors['selection_text']};
}}

QTreeWidget::item, QTreeView::item {{
    color: {colors['text_primary']};
    background-color: transparent;
    padding: {spacing['xs']} {spacing['sm']};
    border: none;
}}

QTreeWidget::item:selected, QTreeView::item:selected {{
    color: {colors['selection_text']};
    background-color: {colors['selection_background']};
}}

QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: {colors['hover_overlay']};
}}

QTreeWidget::branch, QTreeView::branch {{
    background-color: transparent;
}}

QTreeWidget::branch:has-siblings:!adjoins-item, QTreeView::branch:has-siblings:!adjoins-item {{
    border-image: none;
    border-left: {borders['width_thin']} solid {colors['primary_border']};
}}

QTreeWidget::branch:has-siblings:adjoins-item, QTreeView::branch:has-siblings:adjoins-item {{
    border-image: none;
    border-left: {borders['width_thin']} solid {colors['primary_border']};
    border-top: {borders['width_thin']} solid {colors['primary_border']};
}}

QTreeWidget::branch:!has-children:!has-siblings:adjoins-item, QTreeView::branch:!has-children:!has-siblings:adjoins-item {{
    border-image: none;
    border-left: {borders['width_thin']} solid {colors['primary_border']};
    border-top: {borders['width_thin']} solid {colors['primary_border']};
}}

/* List widget styling */
QListWidget, QListView {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    selection-background-color: {colors['selection_background']};
    selection-color: {colors['selection_text']};
}}

QListWidget::item, QListView::item {{
    color: {colors['text_primary']};
    background-color: transparent;
    padding: {spacing['sm']};
    border: none;
    border-bottom: {borders['width_thin']} solid {colors['primary_border']};
}}

QListWidget::item:selected, QListView::item:selected {{
    color: {colors['selection_text']};
    background-color: {colors['selection_background']};
}}

QListWidget::item:hover, QListView::item:hover {{
    background-color: {colors['hover_overlay']};
}}

QListWidget::item:alternate, QListView::item:alternate {{
    background-color: {colors['primary_surface_variant']};
}}

/* Expense table specific styling */
QTableWidget[objectName*="expense"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}

QTableWidget[objectName*="expense"]::item {{
    color: {colors['text_primary']};
    background-color: transparent;
    padding: {spacing['sm']};
}}

QTableWidget[objectName*="expense"]::item:selected {{
    color: {colors['selection_text']};
    background-color: {colors['selection_background']};
}}

QTableWidget[objectName*="expense"]::item:alternate {{
    background-color: {colors['primary_surface_variant']};
}}

/* Income table specific styling */
QTableWidget[objectName*="income"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}

/* Habit table specific styling */
QTableWidget[objectName*="habit"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}

/* Attendance table specific styling */
QTableWidget[objectName*="attendance"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}

/* Todo table specific styling */
QTableWidget[objectName*="todo"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}

/* Investment table specific styling */
QTableWidget[objectName*="investment"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}

/* Budget table specific styling */
QTableWidget[objectName*="budget"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}

/* Trading table specific styling */
QTableWidget[objectName*="trading"] {{
    background-color: {colors['primary_surface']};
    alternate-background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    gridline-color: {colors['primary_border']};
}}
"""
