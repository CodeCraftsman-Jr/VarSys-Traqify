"""
Navigation component styles using design tokens
"""

def get_navigation_styles(tokens: dict) -> str:
    """Generate navigation styles from design tokens"""
    
    colors = tokens['colors']
    typography = tokens['typography']
    spacing = tokens['spacing']
    borders = tokens['borders']
    
    return f"""
/* NAVIGATION STYLES */

/* Tab widget styling */
QTabWidget::pane {{
    border: {borders['width_thin']} solid {colors['primary_border']};
    background-color: {colors['primary_surface']};
    border-radius: {borders['radius_base']};
}}

QTabWidget::tab-bar {{
    alignment: left;
}}

QTabBar::tab {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_secondary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    padding: {spacing['sm']} {spacing['base']};
    margin-right: 2px;
    border-top-left-radius: {borders['radius_base']};
    border-top-right-radius: {borders['radius_base']};
    border-bottom: none;
}}

QTabBar::tab:selected {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
    border-color: {colors['accent_primary']};
}}

QTabBar::tab:hover {{
    background-color: {colors['accent_primary_hover']};
    color: {colors['text_primary']};
}}

QTabBar::tab:!selected {{
    margin-top: 2px;
}}

/* Sidebar styling */
#sidebar {{
    background-color: {colors['primary_surface']};
    border-right: {borders['width_thin']} solid {colors['primary_border']};
}}

#sidebarHeader {{
    background-color: {colors['primary_surface_variant']};
    border-bottom: {borders['width_thin']} solid {colors['primary_border']};
}}

#sidebarTitle {{
    color: {colors['text_primary']};
    font-weight: {typography['weight_bold']};
    font-size: {typography['size_lg']};
}}

#sidebarButton {{
    background-color: transparent;
    border: none;
    color: {colors['text_secondary']};
    text-align: left;
    padding: {spacing['base']} {spacing['lg']};
    border-radius: {borders['radius_base']};
    font-size: {typography['size_sm']};
    margin: {spacing['xs']} {spacing['sm']};
}}

#sidebarButton:hover {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
}}

#sidebarButton:checked {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
}}

#sidebarButton:pressed {{
    background-color: {colors['accent_primary_pressed']};
}}

#sidebarFooter {{
    border-top: {borders['width_thin']} solid {colors['primary_border']};
    background-color: {colors['primary_surface_variant']};
}}

/* Dashboard main tabs */
#dashboardMainTabs::pane {{
    border: {borders['width_thin']} solid {colors['primary_border']};
    background-color: {colors['primary_surface']};
}}

#dashboardMainTabs QTabBar::tab {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_secondary']};
    padding: {spacing['base']} {spacing['xl']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-bottom: none;
    border-top-left-radius: {borders['radius_base']};
    border-top-right-radius: {borders['radius_base']};
    margin-right: 2px;
}}

#dashboardMainTabs QTabBar::tab:selected {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
}}

#dashboardMainTabs QTabBar::tab:hover {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
}}

/* Module-specific tab widgets */
#expenseTabWidget::pane, #incomeTabWidget::pane, #habitTabWidget::pane,
#attendanceTabWidget::pane, #todoTabWidget::pane, #investmentTabWidget::pane,
#budgetTabWidget::pane, #tradingTabWidget::pane {{
    border: {borders['width_thin']} solid {colors['primary_border']};
    background-color: {colors['primary_surface']};
}}

#expenseTabWidget QTabBar::tab, #incomeTabWidget QTabBar::tab, #habitTabWidget QTabBar::tab,
#attendanceTabWidget QTabBar::tab, #todoTabWidget QTabBar::tab, #investmentTabWidget QTabBar::tab,
#budgetTabWidget QTabBar::tab, #tradingTabWidget QTabBar::tab {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_secondary']};
    padding: {spacing['sm']} {spacing['base']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-bottom: none;
    border-top-left-radius: {borders['radius_base']};
    border-top-right-radius: {borders['radius_base']};
}}

#expenseTabWidget QTabBar::tab:selected, #incomeTabWidget QTabBar::tab:selected, #habitTabWidget QTabBar::tab:selected,
#attendanceTabWidget QTabBar::tab:selected, #todoTabWidget QTabBar::tab:selected, #investmentTabWidget QTabBar::tab:selected,
#budgetTabWidget QTabBar::tab:selected, #tradingTabWidget QTabBar::tab:selected {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
}}

#expenseTabWidget QTabBar::tab:hover, #incomeTabWidget QTabBar::tab:hover, #habitTabWidget QTabBar::tab:hover,
#attendanceTabWidget QTabBar::tab:hover, #todoTabWidget QTabBar::tab:hover, #investmentTabWidget QTabBar::tab:hover,
#budgetTabWidget QTabBar::tab:hover, #tradingTabWidget QTabBar::tab:hover {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
}}

/* Breadcrumb navigation */
QLabel[role="breadcrumb"] {{
    color: {colors['text_secondary']};
    font-size: {typography['size_sm']};
}}

QLabel[role="breadcrumb"]:hover {{
    color: {colors['accent_primary']};
}}

/* Pagination controls */
QPushButton[role="pagination"] {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    border-radius: {borders['radius_base']};
    padding: {spacing['sm']};
    min-width: 32px;
    min-height: 32px;
}}

QPushButton[role="pagination"]:hover {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
}}

QPushButton[role="pagination"]:disabled {{
    background-color: {colors['primary_surface']};
    color: {colors['text_disabled']};
    border-color: {colors['primary_border']};
}}

QPushButton[role="pagination"][current="true"] {{
    background-color: {colors['accent_primary']};
    color: {colors['text_inverse']};
    border-color: {colors['accent_primary']};
}}

/* Dock widget styling */
QDockWidget {{
    background-color: {colors['primary_surface']};
    color: {colors['text_primary']};
    border: {borders['width_thin']} solid {colors['primary_border']};
}}

QDockWidget::title {{
    background-color: {colors['primary_surface_variant']};
    color: {colors['text_primary']};
    padding: {spacing['sm']};
    border-bottom: {borders['width_thin']} solid {colors['primary_border']};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background-color: {colors['primary_surface_variant']};
    border: none;
    border-radius: {borders['radius_sm']};
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background-color: {colors['accent_primary']};
}}

/* Toolbar styling */
QToolBar {{
    background-color: {colors['primary_surface_variant']};
    border: {borders['width_thin']} solid {colors['primary_border']};
    spacing: {spacing['sm']};
}}

QToolBar::handle {{
    background-color: {colors['primary_border']};
    width: 2px;
    margin: {spacing['sm']};
}}

QToolBar::separator {{
    background-color: {colors['primary_border']};
    width: 1px;
    margin: {spacing['sm']};
}}

/* Splitter styling */
QSplitter {{
    background-color: {colors['primary_background']};
}}

QSplitter::handle {{
    background-color: {colors['primary_border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QSplitter::handle:pressed {{
    background-color: {colors['accent_primary']};
}}
"""
