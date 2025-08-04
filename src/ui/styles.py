"""
Style Manager Module
Handles application theming and styling
"""

from typing import Dict
from PySide6.QtGui import QPalette, QColor


class StyleManager:
    """Manages application styles and themes"""

    def __init__(self, app=None):
        self.app = app
        self.themes = {
            "dark": self._get_dark_theme(),
            "light": self._get_light_theme(),
            "colorwave": self._get_colorwave_theme()
        }

    def get_stylesheet(self, theme: str = "dark") -> str:
        """Get stylesheet for specified theme"""
        return self.themes.get(theme, self.themes["dark"])

    def apply_theme(self, theme: str = "dark"):
        """Apply theme to the application"""
        if self.app:
            # Apply stylesheet
            stylesheet = self.get_stylesheet(theme)
            self.app.setStyleSheet(stylesheet)

            # CRITICAL FIX: Also set the application palette
            # This ensures that widgets without setStyleSheet() also get themed
            palette = self._get_palette(theme)
            self.app.setPalette(palette)
    
    def _get_dark_theme(self) -> str:
        """Get dark theme stylesheet"""
        return """
        /* Global Default Widget Styles */
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }

        QFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            color: #ffffff;
        }

        QGroupBox {
            background-color: #252526;
            border: 2px solid #3e3e42;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
            color: #ffffff;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 5px 10px 5px 10px;
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            color: #ffffff;
        }

        QLabel {
            background-color: transparent;
            color: #ffffff;
        }

        QPushButton {
            background-color: #0e639c;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 11px;
        }

        QPushButton:hover {
            background-color: #1177bb;
        }

        QPushButton:disabled {
            background-color: #555555;
            color: #999999;
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #2d2d30;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #0e639c;
        }

        QSpinBox, QDoubleSpinBox {
            background-color: #2d2d30;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
        }

        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #0e639c;
        }

        QComboBox {
            background-color: #2d2d30;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
        }

        QComboBox:focus {
            border: 2px solid #0e639c;
        }

        QComboBox::drop-down {
            border: none;
            background-color: #3e3e42;
        }

        QComboBox::down-arrow {
            image: none;
            border: none;
        }

        QListWidget, QTableWidget {
            background-color: #1e1e1e;
            alternate-background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 4px;
        }

        QListWidget::item, QTableWidget::item {
            background-color: transparent;
            color: #ffffff;
            padding: 4px;
            border-bottom: 1px solid #3e3e42;
        }

        QListWidget::item:selected, QTableWidget::item:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        QListWidget::item:hover, QTableWidget::item:hover {
            background-color: #3e3e42;
        }

        QScrollArea {
            background-color: #1e1e1e;
            border: none;
            color: #ffffff;
        }

        QScrollArea > QWidget > QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }

        QScrollArea QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }

        QCalendarWidget {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 4px;
        }

        QCalendarWidget QWidget {
            background-color: #252526;
            color: #ffffff;
        }

        QCalendarWidget QAbstractItemView {
            background-color: #252526;
            color: #ffffff;
            selection-background-color: #0e639c;
            selection-color: #ffffff;
        }

        QCalendarWidget QAbstractItemView:enabled {
            background-color: #252526;
            color: #ffffff;
        }

        QCalendarWidget QMenu {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
        }

        QCalendarWidget QSpinBox {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
        }

        QCalendarWidget QToolButton {
            background-color: #3e3e42;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 4px;
        }

        QCalendarWidget QToolButton:hover {
            background-color: #0e639c;
        }

        QCalendarWidget QToolButton:pressed {
            background-color: #094771;
        }

        QCalendarWidget QAbstractItemView {
            background-color: #252526;
            color: #ffffff;
            selection-background-color: #0e639c;
            selection-color: #ffffff;
            outline: none;
        }

        QCalendarWidget QAbstractItemView::item {
            background-color: transparent;
            color: #ffffff;
        }

        QCalendarWidget QAbstractItemView::item:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        QCalendarWidget QAbstractItemView::item:hover {
            background-color: #3e3e42;
            color: #ffffff;
        }

        QDialog {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3e3e42;
        }

        QMessageBox {
            background-color: #1e1e1e;
            color: #ffffff;
        }

        QMessageBox QLabel {
            background-color: transparent;
            color: #ffffff;
        }

        QToolTip {
            background-color: #3e3e42;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
        }

        QMessageBox QPushButton {
            background-color: #3e3e42;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px 12px;
            min-width: 60px;
        }

        QMessageBox QPushButton:hover {
            background-color: #0e639c;
        }

        QMessageBox QPushButton:pressed {
            background-color: #094771;
        }

        QWebEngineView {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            border-radius: 4px;
        }

        /* Additional widget styling to prevent white backgrounds */
        QDateEdit, QTimeEdit, QDateTimeEdit {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
        }

        QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {
            border: 2px solid #0e639c;
        }

        QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {
            background-color: #3e3e42;
            border: none;
            width: 20px;
        }

        QDateEdit::down-arrow, QTimeEdit::down-arrow, QDateTimeEdit::down-arrow {
            image: none;
            border: none;
        }

        QDateEdit QAbstractItemView, QTimeEdit QAbstractItemView, QDateTimeEdit QAbstractItemView {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            selection-background-color: #0e639c;
            selection-color: #ffffff;
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
            selection-background-color: #0e639c;
            selection-color: #ffffff;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #0e639c;
        }

        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
            background-color: #1e1e1e;
            color: #666666;
            border: 1px solid #2d2d30;
        }

        QSpinBox, QDoubleSpinBox {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
            selection-background-color: #0e639c;
        }

        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #0e639c;
        }

        QSpinBox::up-button, QDoubleSpinBox::up-button {
            background-color: #3e3e42;
            border: none;
            border-radius: 2px;
        }

        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
            background-color: #555555;
        }

        QSpinBox::down-button, QDoubleSpinBox::down-button {
            background-color: #3e3e42;
            border: none;
            border-radius: 2px;
        }

        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
            background-color: #555555;
        }

        QComboBox {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
            min-width: 6em;
        }

        QComboBox:focus {
            border: 2px solid #0e639c;
        }

        QComboBox::drop-down {
            border: none;
            background-color: #3e3e42;
            width: 20px;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }

        QComboBox::drop-down:hover {
            background-color: #555555;
        }

        QComboBox::down-arrow {
            image: none;
            border: none;
            width: 12px;
            height: 12px;
        }

        QComboBox QAbstractItemView {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            selection-background-color: #0e639c;
            selection-color: #ffffff;
            outline: none;
        }

        QComboBox QAbstractItemView::item {
            background-color: #252526;
            color: #ffffff;
            padding: 5px;
            border: none;
        }

        QComboBox QAbstractItemView::item:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        QComboBox QAbstractItemView::item:hover {
            background-color: #3e3e42;
            color: #ffffff;
        }

        QComboBox QAbstractItemView {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            selection-background-color: #0e639c;
            selection-color: #ffffff;
        }

        QDateEdit, QTimeEdit, QDateTimeEdit {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            padding: 5px;
        }

        QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {
            border: 2px solid #0e639c;
        }

        QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {
            background-color: #3e3e42;
            border: none;
            width: 20px;
        }

        QDateEdit::drop-down:hover, QTimeEdit::drop-down:hover, QDateTimeEdit::drop-down:hover {
            background-color: #555555;
        }

        QListWidget, QTableWidget, QTreeWidget {
            background-color: #252526;
            alternate-background-color: #2d2d30;
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            gridline-color: #3e3e42;
            selection-background-color: #0e639c;
            selection-color: #ffffff;
        }

        QListWidget::item, QTableWidget::item, QTreeWidget::item {
            background-color: transparent;
            color: #ffffff;
            padding: 4px;
            border-bottom: 1px solid #3e3e42;
        }

        QListWidget::item:selected, QTableWidget::item:selected, QTreeWidget::item:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        QListWidget::item:hover, QTableWidget::item:hover, QTreeWidget::item:hover {
            background-color: #3e3e42;
        }

        QTableWidget::item:alternate {
            background-color: #2d2d30;
        }

        QHeaderView::section {
            background-color: #3e3e42;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
            font-weight: bold;
        }

        QHeaderView::section:hover {
            background-color: #555555;
        }

        QTableCornerButton::section {
            background-color: #3e3e42;
            border: 1px solid #555555;
        }

        QCheckBox {
            color: #ffffff;
            spacing: 5px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #3e3e42;
            border-radius: 3px;
            background-color: #252526;
        }

        QCheckBox::indicator:hover {
            border: 1px solid #0e639c;
        }

        QCheckBox::indicator:checked {
            background-color: #0e639c;
            border: 1px solid #0e639c;
        }

        QCheckBox::indicator:checked:hover {
            background-color: #1177bb;
        }

        QRadioButton {
            color: #ffffff;
            spacing: 5px;
        }

        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            background-color: #252526;
        }

        QRadioButton::indicator:hover {
            border: 1px solid #0e639c;
        }

        QRadioButton::indicator:checked {
            background-color: #0e639c;
            border: 1px solid #0e639c;
        }

        QTabWidget::tab-bar {
            alignment: left;
        }

        QTabBar::tab {
            background-color: #3e3e42;
            color: #ffffff;
            border: 1px solid #555555;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 8px 12px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #252526;
            border-bottom: 2px solid #0e639c;
        }

        QTabBar::tab:hover:!selected {
            background-color: #555555;
        }

        QScrollBar:vertical {
            background-color: #252526;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #3e3e42;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #555555;
        }

        QScrollBar:horizontal {
            background-color: #252526;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background-color: #3e3e42;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #555555;
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }

        QProgressBar {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            text-align: center;
            color: #ffffff;
        }

        QProgressBar::chunk {
            background-color: #0e639c;
            border-radius: 3px;
        }

        QGroupBox {
            color: #ffffff;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            margin-top: 10px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            color: #ffffff;
        }

        QTabWidget::pane {
            background-color: #252526;
            border: 1px solid #3e3e42;
        }

        QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            border: 1px solid #3e3e42;
            padding: 8px 16px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        QTabBar::tab:hover {
            background-color: #3e3e42;
            color: #ffffff;
        }

        /* Main Window */
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        /* Sidebar */
        #sidebar {
            background-color: #252526;
            border-right: 1px solid #3e3e42;
        }
        
        #sidebarHeader {
            background-color: #2d2d30;
            border-bottom: 1px solid #3e3e42;
        }
        
        #sidebarTitle {
            color: #ffffff;
            font-weight: bold;
        }
        
        #toggleButton {
            background-color: #3e3e42;
            border: none;
            border-radius: 4px;
            color: #ffffff;
            font-size: 14px;
        }
        
        #toggleButton:hover {
            background-color: #4e4e52;
        }
        
        #sidebarButton {
            background-color: transparent;
            border: none;
            color: #cccccc;
            text-align: left;
            padding: 10px 15px;
            border-radius: 4px;
            font-size: 11px;
        }
        
        #sidebarButton:hover {
            background-color: #3e3e42;
            color: #ffffff;
        }
        
        #sidebarButton:checked {
            background-color: #0e639c;
            color: #ffffff;
        }
        
        #sidebarFooter {
            border-top: 1px solid #3e3e42;
        }
        
        /* Dashboard */
        #dashboardScrollArea {
            background-color: #1e1e1e;
            border: none;
        }
        
        #dashboardHeader {
            background-color: transparent;
        }
        
        #dashboardWelcome {
            color: #ffffff;
        }
        
        #refreshButton {
            background-color: #0e639c;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
        }
        
        #refreshButton:hover {
            background-color: #1177bb;
        }
        
        #sectionTitle {
            color: #ffffff;
            margin-bottom: 10px;
        }
        
        /* Stat Cards */
        #statCard {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
        }
        
        #statCard:hover {
            border-color: #0e639c;
        }
        
        #statCardTitle {
            color: #cccccc;
        }
        
        #statCardValue {
            color: #ffffff;
        }
        
        #statCardSubtitle {
            color: #999999;
        }
        
        /* Quick Action Cards */
        #quickActionCard {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
        }
        
        #quickActionCard:hover {
            border-color: #0e639c;
        }
        
        #quickActionTitle {
            color: #ffffff;
        }
        
        #quickActionDescription {
            color: #cccccc;
        }
        
        #quickActionButton {
            background-color: #0e639c;
            border: none;
            color: #ffffff;
            border-radius: 4px;
            font-size: 11px;
        }
        
        #quickActionButton:hover {
            background-color: #1177bb;
        }

        /* Enhanced Quick Action Buttons */
        #expenseQuickButton, #incomeQuickButton, #habitQuickButton {
            background-color: #0e639c;
            border: none;
            color: #ffffff;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: bold;
            min-height: 32px;
        }

        #expenseQuickButton:hover, #incomeQuickButton:hover, #habitQuickButton:hover {
            background-color: #1177bb;
            transform: translateY(-1px);
        }

        /* Compact layouts for better information density */
        QGroupBox {
            font-weight: bold;
            padding-top: 8px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
        }
        
        /* Activity Frame */
        #activityFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #2d2d30;
            border-top: 1px solid #3e3e42;
            color: #cccccc;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #2d2d30;
            color: #ffffff;
            border-bottom: 1px solid #3e3e42;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #3e3e42;
        }
        
        QMenu {
            background-color: #2d2d30;
            color: #ffffff;
            border: 1px solid #3e3e42;
        }
        
        QMenu::item {
            padding: 4px 20px;
        }
        
        QMenu::item:selected {
            background-color: #0e639c;
        }

        /* Context menus and popup styling */
        QMenu::separator {
            height: 1px;
            background-color: #3e3e42;
            margin: 2px 0px;
        }

        QMenu::indicator {
            width: 13px;
            height: 13px;
        }

        QMenu::indicator:checked {
            background-color: #0e639c;
            border: 1px solid #3e3e42;
        }

        QMenu::indicator:unchecked {
            background-color: #252526;
            border: 1px solid #3e3e42;
        }

        /* Ensure all popup widgets have dark backgrounds */
        QWidget[objectName*="popup"], QWidget[objectName*="Popup"] {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3e3e42;
        }

        /* Additional coverage for specific insight widgets only - REMOVED CARD SELECTORS */
        /* CRITICAL FIX: Removed summary selectors that were forcing dark backgrounds */
        QWidget[objectName*="insight"], QWidget[objectName*="Insight"] {
            background-color: #252526;
            color: #ffffff;
        }

        /* CRITICAL FIX: Removed frame selectors that were forcing dark backgrounds */
        /* These selectors were overriding global theme colors for frames */
        /* Now frames will inherit from global theme properly */

        /* Force dark theme for any remaining light elements */
        * {
            selection-background-color: #0e639c;
            selection-color: #ffffff;
        }
        
        /* Scroll Bars */
        QScrollBar:vertical {
            background-color: #2d2d30;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        
        /* Splitter */
        QSplitter::handle {
            background-color: #3e3e42;
        }
        
        QSplitter::handle:hover {
            background-color: #0e639c;
        }

        /* Module Header Styles - Standardized across all modules */
        #expenseHeader, #incomeHeader, #habitHeader, #attendanceHeader, #todoHeader, #investmentHeader, #budgetHeader, #tradingHeader {
            background-color: transparent;
            border-bottom: 1px solid #3e3e42;
            padding-bottom: 10px;
            max-height: 50px;
        }

        #expenseTitle, #incomeTitle, #habitTitle, #attendanceTitle, #todoTitle, #investmentTitle, #budgetTitle, #tradingTitle {
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        }

        /* Module Action Buttons - Standardized styling */
        #expenseAddButton, #expenseEditButton, #expenseDeleteButton, #expenseCategoriesButton, #expenseClearFiltersButton,
        #incomeAddGoalButton, #habitNavButton, #habitTodayButton, #habitManageButton, #habitAddButton,
        #attendanceTodayButton, #attendanceSemesterButton, #attendanceActionButton, #attendanceNavButton {
            background-color: #0e639c;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
            min-height: 32px;
            max-height: 32px;
        }

        #expenseAddButton:hover, #expenseEditButton:hover, #expenseDeleteButton:hover, #expenseCategoriesButton:hover, #expenseClearFiltersButton:hover,
        #incomeAddGoalButton:hover, #habitNavButton:hover, #habitTodayButton:hover, #habitManageButton:hover, #habitAddButton:hover,
        #attendanceTodayButton:hover, #attendanceSemesterButton:hover, #attendanceActionButton:hover, #attendanceNavButton:hover {
            background-color: #1177bb;
        }

        #expenseEditButton:disabled, #expenseDeleteButton:disabled, #habitNavButton:disabled, #attendanceNavButton:disabled {
            background-color: #555555;
            color: #999999;
        }

        #expenseSearchFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            padding: 10px;
        }

        #expenseSearchEdit, #expenseCategoryFilter {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            color: #ffffff;
            padding: 5px;
            border-radius: 3px;
        }

        #expenseTable {
            background-color: #1e1e1e;
            alternate-background-color: #252526;
            color: #ffffff;
            gridline-color: #3e3e42;
            selection-background-color: #0e639c;
        }

        #expenseTable::item {
            padding: 5px;
            border: none;
        }

        #expenseTable::item:selected {
            background-color: #0e639c;
        }

        #expenseStatsFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 15px;
        }

        #expenseStatsTitle {
            color: #ffffff;
        }

        #expenseStatValue {
            color: #0e639c;
        }

        #expenseQuickActions {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
        }

        #expenseQuickButton {
            background-color: #3e3e42;
            border: none;
            color: #ffffff;
            padding: 8px;
            border-radius: 4px;
            text-align: left;
        }

        #expenseQuickButton:hover {
            background-color: #4e4e52;
        }

        /* Expense Dialog Styles */
        #expenseFormFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 15px;
        }

        #expenseDateEdit, #expenseTypeCombo, #expenseCategoryCombo,
        #expenseSubcategoryCombo, #expenseTransactionModeCombo,
        #expenseAmountSpinbox, #expenseNotesEdit {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            color: #ffffff;
            padding: 5px;
            border-radius: 3px;
        }

        #expenseDialogButtonBox QPushButton {
            background-color: #0e639c;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 80px;
        }

        #expenseDialogButtonBox QPushButton:hover {
            background-color: #1177bb;
        }



        #incomeTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #252526;
        }

        #incomeTabWidget::tab-bar {
            alignment: left;
        }

        #incomeTabWidget QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 8px 16px;
            border: 1px solid #3e3e42;
            border-bottom: none;
        }

        #incomeTabWidget QTabBar::tab:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        #incomeTabWidget QTabBar::tab:hover {
            background-color: #3e3e42;
        }

        #incomeProgressFrame, #incomeStatsFrame, #incomeBreakdownFrame,
        #incomeNotesFrame, #incomeDailyFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 15px;
        }

        #incomeProgressTitle, #incomeStatsTitle {
            color: #ffffff;
        }

        #incomeGoalLabel, #incomeEarnedLabel, #incomeRemainingLabel {
            color: #cccccc;
        }

        #incomeMainProgressBar, #incomeWeeklyProgressBar, #incomeDayProgress {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            text-align: center;
        }

        #incomeMainProgressBar::chunk, #incomeWeeklyProgressBar::chunk,
        #incomeDayProgress::chunk {
            background-color: #0e639c;
            border-radius: 3px;
        }

        #incomeMainStatusLabel, #incomeDayStatus {
            font-weight: bold;
        }

        #incomeStatValue, #incomeSourceAmount, #incomeTotalAmount,
        #incomeExtraAmount, #incomeCurrentGoalLabel {
            color: #0e639c;
            font-weight: bold;
        }

        #incomeQuickActions {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
        }

        #todayOverviewFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 12px;
            padding: 15px;
            color: #ffffff;
        }

        QFrame[objectName^="metricCard_"] {
            background-color: #2d2d30;
            border: 2px solid #3e3e42;
            border-radius: 8px;
            padding: 15px;
            min-height: 80px;
        }

        QFrame[objectName^="metricCard_"]:hover {
            border-color: #0e639c;
            box-shadow: 0 2px 8px rgba(14, 99, 156, 0.3);
        }

        QLabel[objectName^="metricValue_"] {
            font-size: 24px;
            font-weight: bold;
            color: #0e639c;
        }

        QLabel[objectName^="metricTitle_"] {
            font-size: 12px;
            color: #cccccc;
            font-weight: 500;
        }

        #incomeQuickSourceButton {
            background-color: #3e3e42;
            border: none;
            color: #ffffff;
            padding: 2px 8px;
            border-radius: 4px;
            text-align: center;
            min-height: 22px;
            font-size: 11px;
        }

        #incomeQuickSourceButton:hover {
            background-color: #4e4e52;
        }

        #incomeWeekNavButton {
            background-color: #3e3e42;
            border: none;
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 4px;
        }

        #incomeWeekNavButton:hover {
            background-color: #4e4e52;
        }

        #incomeWeekLabel {
            color: #ffffff;
        }

        #incomeDayWidget {
            background-color: #2d2d30;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            padding: 8px;
            margin: 2px 0;
        }

        #incomeDayInfo {
            color: #cccccc;
            font-size: 10px;
        }

        /* Income Dialog Styles */
        #incomeFormFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 15px;
        }

        #incomeDateEdit, #incomeGoalSpinbox, #incomeZomatoSpinbox,
        #incomeSwiggySpinbox, #incomeShadowFaxSpinbox, #incomeOtherSpinbox,
        #incomeNotesEdit {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            color: #ffffff;
            padding: 5px;
            border-radius: 3px;
        }

        #incomeSectionLabel {
            color: #0e639c;
            font-weight: bold;
        }

        #incomeTotalLabel {
            color: #00aa00;
            font-weight: bold;
        }

        #incomeProgressBar {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            border-radius: 4px;
        }

        #incomeProgressBar::chunk {
            background-color: #0e639c;
            border-radius: 3px;
        }

        #incomeStatusLabel {
            font-weight: bold;
        }

        #incomeDialogButtonBox QPushButton {
            background-color: #0e639c;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 80px;
        }

        #incomeDialogButtonBox QPushButton:hover {
            background-color: #1177bb;
        }

        /* Income Analytics Dashboard Styles */
        #dashboardTitle {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
        }

        #analyticsTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #252526;
        }

        #analyticsTabWidget QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 8px 16px;
            border: 1px solid #3e3e42;
            border-bottom: none;
        }

        #analyticsTabWidget QTabBar::tab:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        #analyticsTabWidget QTabBar::tab:hover {
            background-color: #3e3e42;
        }

        /* Dashboard Main Tabs - Dark Theme */
        #dashboardMainTabs::pane {
            border: 1px solid #3e3e42;
            background-color: #252526;
        }

        #dashboardMainTabs QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 10px 20px;
            border: 1px solid #3e3e42;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }

        #dashboardMainTabs QTabBar::tab:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        #dashboardMainTabs QTabBar::tab:hover {
            background-color: #3e3e42;
            color: #ffffff;
        }

        /* Chart Title Styling */
        #chartTitle {
            color: #0e639c;
            background-color: transparent;
        }

        /* APPLIED TO DO ANALYTICS APPROACH: Natural expansion summary card styling - Dark Theme */
        #summaryCard {
            border: 1px solid #3e3e42;
            border-radius: 12px;  /* Larger border radius for modern look */
            padding: 25px;        /* Generous padding for spacious feel */
            margin: 10px;         /* Increased margins between cards for better separation */
            min-height: 180px;    /* Reasonable minimum height */
            min-width: 200px;     /* Reasonable minimum width */
            /* Remove max constraints to allow unlimited expansion for full data visibility like To Do Analytics */
        }

        #summaryCardTitle {
            color: #cccccc;
            font-size: 12px;      /* Increased font size for better readability */
            font-weight: bold;
            line-height: 1.3;     /* Better line height for readability */
        }

        #summaryCardValue {
            color: #0e639c;
            font-size: 32px;      /* APPLIED TO DO ANALYTICS APPROACH: Larger font size for maximum prominence */
            font-weight: bold;
            line-height: 1.1;
            margin: 10px 0px;     /* More generous margins for better spacing */
        }

        #summaryCardSubtitle {
            color: #888888;
            font-size: 11px;      /* Increased subtitle font for better readability */
            line-height: 1.3;     /* Better line height */
        }

        /* Overview Tab Widget Styles */
        #overviewTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #252526;
        }

        #overviewTabWidget QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 8px 16px;
            border: 1px solid #3e3e42;
            border-bottom: none;
        }

        #overviewTabWidget QTabBar::tab:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        #overviewTabWidget QTabBar::tab:hover {
            background-color: #3e3e42;
        }

        /* Habit Tracker Specific Styles */
        #habitDateLabel {
            color: #cccccc;
            font-size: 12px;
        }

        #habitScrollArea {
            background-color: transparent;
            border: none;
        }

        #habitGridWidget {
            background-color: transparent;
        }

        #habitCard {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 10px;
        }

        #habitCard:hover {
            border-color: #0e639c;
        }

        #habitCardCompleted {
            background-color: #252526;
            border-radius: 8px;
            padding: 10px;
        }

        #habitCardCompleted:hover {
            opacity: 0.9;
        }

        #habitIcon {
            color: #ffffff;
        }

        #habitName {
            color: #ffffff;
            font-weight: bold;
        }

        #habitProgress {
            color: #cccccc;
            font-size: 10px;
        }

        #habitCheckBox {
            spacing: 5px;
        }

        #habitCheckBox::indicator {
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 2px solid #3e3e42;
            background-color: #1e1e1e;
        }

        #habitCheckBox::indicator:checked {
            background-color: #0e639c;
            border-color: #0e639c;
        }

        #habitCheckBox::indicator:checked:hover {
            background-color: #1177bb;
        }

        #habitProgressFrame, #habitStatsFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 15px;
        }

        #habitProgressTitle, #habitStatsTitle {
            color: #ffffff;
        }

        #habitCompletionLabel, #habitMessageLabel {
            color: #cccccc;
        }

        #habitMainProgressBar {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            text-align: center;
        }

        #habitMainProgressBar::chunk {
            background-color: #0e639c;
            border-radius: 3px;
        }

        #habitStatValue {
            color: #0e639c;
            font-weight: bold;
        }

        #habitManagementItem {
            background-color: #2d2d30;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            padding: 10px;
            margin: 2px 0;
        }

        #habitManagementName {
            color: #ffffff;
            font-weight: bold;
        }

        #habitManagementDetails {
            color: #cccccc;
            font-size: 10px;
        }

        /* Attendance Tracker Specific Styles */

        #attendanceTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #252526;
        }

        #attendanceTabWidget QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            padding: 8px 16px;
            border: 1px solid #3e3e42;
            border-bottom: none;
        }

        #attendanceTabWidget QTabBar::tab:selected {
            background-color: #0e639c;
            color: #ffffff;
        }

        #attendanceDateLabel {
            color: #ffffff;
            font-weight: bold;
        }

        #attendanceDayLabel {
            color: #cccccc;
        }

        #attendancePeriodsFrame, #attendanceActionsFrame, #attendanceSummaryFrame,
        #attendanceNotesFrame, #attendanceStatsFrame, #attendanceSemesterFrame,
        #attendanceProgressFrame {
            background-color: #252526;
            border: 1px solid #3e3e42;
            border-radius: 8px;
            padding: 15px;
        }

        #periodButton {
            min-width: 60px;
            min-height: 40px;
            border-radius: 4px;
            font-weight: bold;
        }

        #attendanceSummaryValue, #attendanceStatValue, #attendanceSemesterValue {
            color: #0e639c;
            font-weight: bold;
        }

        #attendancePercentageValue {
            font-weight: bold;
            font-size: 12px;
        }

        #attendanceOverallPercentage {
            font-weight: bold;
            font-size: 16px;
        }

        #attendanceThresholdStatus {
            font-weight: bold;
        }

        #attendanceProgressBar {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            text-align: center;
        }

        #attendanceProgressBar::chunk {
            background-color: #0e639c;
            border-radius: 3px;
        }

        #attendanceStatsTitle {
            color: #ffffff;
        }

        #attendanceProgressLabel {
            color: #cccccc;
        }

        #attendanceNotesEdit {
            background-color: #1e1e1e;
            border: 1px solid #3e3e42;
            color: #ffffff;
            padding: 5px;
            border-radius: 3px;
        }
        """
    
    def _get_light_theme(self) -> str:
        """Get light theme stylesheet"""
        return """
        /* Global Default Widget Styles */
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }

        QFrame {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            color: #000000;
        }

        QLabel {
            background-color: transparent;
            color: #000000;
        }

        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 11px;
        }

        QPushButton:hover {
            background-color: #106ebe;
        }

        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 3px;
            padding: 5px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #0078d4;
        }

        QSpinBox, QDoubleSpinBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 3px;
            padding: 5px;
        }

        QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #0078d4;
        }

        QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
            border-radius: 3px;
            padding: 5px;
        }

        QComboBox:focus {
            border: 2px solid #0078d4;
        }

        QComboBox::drop-down {
            border: none;
            background-color: #e0e0e0;
        }

        QComboBox::down-arrow {
            image: none;
            border: none;
        }

        QListWidget, QTableWidget, QTreeWidget {
            background-color: #ffffff;
            alternate-background-color: #ffffff;
            color: #000000;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            gridline-color: #e0e0e0;
            selection-background-color: #0078d4;
            selection-color: #ffffff;
        }

        QListWidget::item, QTableWidget::item, QTreeWidget::item {
            background-color: transparent;
            color: #000000;
            padding: 4px;
            border-bottom: 1px solid #e0e0e0;
        }

        QListWidget::item:selected, QTableWidget::item:selected, QTreeWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        QListWidget::item:hover, QTableWidget::item:hover, QTreeWidget::item:hover {
            background-color: #f0f0f0;
        }

        QTableWidget::item:alternate {
            background-color: #ffffff;
        }

        QHeaderView::section {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #e0e0e0;
            padding: 4px;
        }

        QScrollArea {
            background-color: #ffffff;
            border: none;
        }

        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }

        QScrollBar:horizontal {
            background-color: #f0f0f0;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #a0a0a0;
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }

        QProgressBar {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            text-align: center;
            color: #000000;
        }

        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }

        QGroupBox {
            color: #000000;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            margin-top: 10px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            color: #000000;
        }

        QTabWidget::pane {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
        }

        QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            border: 1px solid #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        QTabBar::tab:hover {
            background-color: #e0e0e0;
            color: #000000;
        }

        /* Main Window */
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        
        /* Sidebar */
        #sidebar {
            background-color: #f3f3f3;
            border-right: 1px solid #d0d0d0;
        }
        
        #sidebarHeader {
            background-color: #e8e8e8;
            border-bottom: 1px solid #d0d0d0;
        }
        
        #sidebarTitle {
            color: #000000;
            font-weight: bold;
        }
        
        #toggleButton {
            background-color: #d0d0d0;
            border: none;
            border-radius: 4px;
            color: #000000;
            font-size: 14px;
        }
        
        #toggleButton:hover {
            background-color: #c0c0c0;
        }
        
        #sidebarButton {
            background-color: transparent;
            border: none;
            color: #333333;
            text-align: left;
            padding: 10px 15px;
            border-radius: 4px;
            font-size: 11px;
        }
        
        #sidebarButton:hover {
            background-color: #e0e0e0;
            color: #000000;
        }
        
        #sidebarButton:checked {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        #sidebarFooter {
            border-top: 1px solid #d0d0d0;
        }
        
        /* Dashboard */
        #dashboardScrollArea {
            background-color: #ffffff;
            border: none;
        }
        
        #dashboardHeader {
            background-color: transparent;
        }
        
        #dashboardWelcome {
            color: #000000;
        }
        
        #refreshButton {
            background-color: #0078d4;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
        }
        
        #refreshButton:hover {
            background-color: #106ebe;
        }
        
        #sectionTitle {
            color: #000000;
            margin-bottom: 10px;
        }
        
        /* Stat Cards */
        #statCard {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
        
        #statCard:hover {
            border-color: #0078d4;
        }
        
        #statCardTitle {
            color: #666666;
        }
        
        #statCardValue {
            color: #000000;
        }
        
        #statCardSubtitle {
            color: #888888;
        }
        
        /* Quick Action Cards */
        #quickActionCard {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
        
        #quickActionCard:hover {
            border-color: #0078d4;
        }
        
        #quickActionTitle {
            color: #000000;
        }
        
        #quickActionDescription {
            color: #666666;
        }
        
        #quickActionButton {
            background-color: #0078d4;
            border: none;
            color: #ffffff;
            border-radius: 4px;
            font-size: 11px;
        }
        
        #quickActionButton:hover {
            background-color: #106ebe;
        }

        /* Enhanced Quick Action Buttons */
        #expenseQuickButton, #incomeQuickButton, #habitQuickButton {
            background-color: #0078d4;
            border: none;
            color: #ffffff;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: bold;
            min-height: 32px;
        }

        #expenseQuickButton:hover, #incomeQuickButton:hover, #habitQuickButton:hover {
            background-color: #106ebe;
            transform: translateY(-1px);
        }

        /* Compact layouts for better information density */
        QGroupBox {
            font-weight: bold;
            padding-top: 8px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
        }
        
        /* Activity Frame */
        #activityFrame {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #ffffff;
            border-top: 1px solid #d0d0d0;
            color: #000000;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #ffffff;
            color: #000000;
            border-bottom: 1px solid #d0d0d0;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        
        QMenu {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #d0d0d0;
        }
        
        QMenu::item {
            padding: 4px 20px;
        }
        
        QMenu::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        /* Scroll Bars */
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        
        /* Splitter */
        QSplitter::handle {
            background-color: #e0e0e0;
        }

        QSplitter {
            background-color: #ffffff;
        }
        
        QSplitter::handle:hover {
            background-color: #0078d4;
        }

        /* Module Header Styles - Standardized across all modules */
        #expenseHeader, #incomeHeader, #habitHeader, #attendanceHeader, #todoHeader, #investmentHeader, #budgetHeader, #tradingHeader {
            background-color: transparent;
            border-bottom: 1px solid #d0d0d0;
            padding-bottom: 10px;
            max-height: 50px;
        }

        #expenseTitle, #incomeTitle, #habitTitle, #attendanceTitle, #todoTitle, #investmentTitle, #budgetTitle, #tradingTitle {
            color: #000000;
            font-size: 14px;
            font-weight: bold;
        }

        /* Module Action Buttons - Standardized styling */
        #expenseAddButton, #expenseEditButton, #expenseDeleteButton, #expenseCategoriesButton, #expenseClearFiltersButton,
        #incomeAddGoalButton, #habitNavButton, #habitTodayButton, #habitManageButton, #habitAddButton,
        #attendanceTodayButton, #attendanceSemesterButton, #attendanceActionButton, #attendanceNavButton {
            background-color: #0078d4;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
            min-height: 32px;
            max-height: 32px;
        }

        #expenseAddButton:hover, #expenseEditButton:hover, #expenseDeleteButton:hover, #expenseCategoriesButton:hover, #expenseClearFiltersButton:hover,
        #incomeAddGoalButton:hover, #habitNavButton:hover, #habitTodayButton:hover, #habitManageButton:hover, #habitAddButton:hover,
        #attendanceTodayButton:hover, #attendanceSemesterButton:hover, #attendanceActionButton:hover, #attendanceNavButton:hover {
            background-color: #106ebe;
        }

        #expenseEditButton:disabled, #expenseDeleteButton:disabled, #habitNavButton:disabled, #attendanceNavButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }

        #expenseSearchFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 10px;
        }

        #expenseSearchEdit, #expenseCategoryFilter {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            color: #000000;
            padding: 5px;
            border-radius: 3px;
        }

        #expenseTable {
            background-color: #ffffff;
            alternate-background-color: #f9f9f9;
            color: #000000;
            gridline-color: #e0e0e0;
            selection-background-color: #0078d4;
        }

        #expenseTable::item {
            padding: 5px;
            border: none;
        }

        #expenseTable::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        #expenseStatsFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }

        #expenseStatsTitle {
            color: #000000;
        }

        #expenseStatValue {
            color: #0078d4;
        }

        #expenseQuickActions {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }

        #expenseQuickButton {
            background-color: #e0e0e0;
            border: none;
            color: #000000;
            padding: 8px;
            border-radius: 4px;
            text-align: left;
        }

        #expenseQuickButton:hover {
            background-color: #d0d0d0;
        }

        /* Expense Dialog Styles */
        #expenseFormFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }

        #expenseDateEdit, #expenseTypeCombo, #expenseCategoryCombo,
        #expenseSubcategoryCombo, #expenseTransactionModeCombo,
        #expenseAmountSpinbox, #expenseNotesEdit {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            color: #000000;
            padding: 5px;
            border-radius: 3px;
        }

        #expenseDialogButtonBox QPushButton {
            background-color: #0078d4;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 80px;
        }

        #expenseDialogButtonBox QPushButton:hover {
            background-color: #106ebe;
        }



        #incomeTabWidget::pane {
            border: 1px solid #d0d0d0;
            background-color: #f9f9f9;
        }

        #incomeTabWidget::tab-bar {
            alignment: left;
        }

        #incomeTabWidget QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            padding: 8px 16px;
            border: 1px solid #d0d0d0;
            border-bottom: none;
        }

        #incomeTabWidget QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        #incomeTabWidget QTabBar::tab:hover {
            background-color: #e0e0e0;
        }

        #incomeProgressFrame, #incomeStatsFrame, #incomeBreakdownFrame,
        #incomeNotesFrame, #incomeDailyFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }

        #incomeProgressTitle, #incomeStatsTitle {
            color: #000000;
        }

        #incomeGoalLabel, #incomeEarnedLabel, #incomeRemainingLabel {
            color: #666666;
        }

        #incomeMainProgressBar, #incomeWeeklyProgressBar, #incomeDayProgress {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            text-align: center;
        }

        #incomeMainProgressBar::chunk, #incomeWeeklyProgressBar::chunk,
        #incomeDayProgress::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }

        #incomeMainStatusLabel, #incomeDayStatus {
            font-weight: bold;
        }

        #incomeStatValue, #incomeSourceAmount, #incomeTotalAmount,
        #incomeExtraAmount, #incomeCurrentGoalLabel {
            color: #0078d4;
            font-weight: bold;
        }

        #incomeQuickActions {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }

        #todayOverviewFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 15px;
            color: #000000;
        }

        QFrame[objectName^="metricCard_"] {
            background-color: #ffffff;
            border: 2px solid #e3f2fd;
            border-radius: 8px;
            padding: 15px;
            min-height: 80px;
        }

        QFrame[objectName^="metricCard_"]:hover {
            border-color: #2196f3;
            box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
        }

        QLabel[objectName^="metricValue_"] {
            font-size: 24px;
            font-weight: bold;
            color: #1976d2;
        }

        QLabel[objectName^="metricTitle_"] {
            font-size: 12px;
            color: #666666;
            font-weight: 500;
        }

        #incomeQuickSourceButton {
            background-color: #e0e0e0;
            border: none;
            color: #000000;
            padding: 12px 8px;
            border-radius: 4px;
            text-align: center;
            min-height: 32px;
            font-size: 11px;
        }

        #incomeQuickSourceButton:hover {
            background-color: #d0d0d0;
        }

        #incomeWeekNavButton {
            background-color: #e0e0e0;
            border: none;
            color: #000000;
            padding: 6px 12px;
            border-radius: 4px;
        }

        #incomeWeekNavButton:hover {
            background-color: #d0d0d0;
        }

        #incomeWeekLabel {
            color: #000000;
        }

        #incomeDayWidget {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 8px;
            margin: 2px 0;
        }

        #incomeDayInfo {
            color: #666666;
            font-size: 10px;
        }

        /* Income Dialog Styles */
        #incomeFormFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }

        #incomeDateEdit, #incomeGoalSpinbox, #incomeZomatoSpinbox,
        #incomeSwiggySpinbox, #incomeShadowFaxSpinbox, #incomeOtherSpinbox,
        #incomeNotesEdit {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            color: #000000;
            padding: 5px;
            border-radius: 3px;
        }

        #incomeSectionLabel {
            color: #0078d4;
            font-weight: bold;
        }

        #incomeTotalLabel {
            color: #00aa00;
            font-weight: bold;
        }

        #incomeProgressBar {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
        }

        #incomeProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }

        #incomeStatusLabel {
            font-weight: bold;
        }

        #incomeDialogButtonBox QPushButton {
            background-color: #0078d4;
            border: none;
            color: #ffffff;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 80px;
        }

        #incomeDialogButtonBox QPushButton:hover {
            background-color: #106ebe;
        }

        /* Income Analytics Dashboard Styles */
        #dashboardTitle {
            color: #000000;
            font-size: 16px;
            font-weight: bold;
        }

        #analyticsTabWidget::pane {
            border: 1px solid #d0d0d0;
            background-color: #f9f9f9;
        }

        #analyticsTabWidget QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            padding: 8px 16px;
            border: 1px solid #d0d0d0;
            border-bottom: none;
        }

        #analyticsTabWidget QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        #analyticsTabWidget QTabBar::tab:hover {
            background-color: #e0e0e0;
        }

        /* APPLIED TO DO ANALYTICS APPROACH: Natural expansion summary card styling - Light Theme */
        #summaryCard {
            border: 1px solid #e0e0e0;
            border-radius: 12px;  /* Larger border radius for modern look */
            padding: 25px;        /* Generous padding for spacious feel */
            margin: 10px;         /* Increased margins between cards for better separation */
            min-height: 180px;    /* Reasonable minimum height */
            min-width: 200px;     /* Reasonable minimum width */
            /* Remove max constraints to allow unlimited expansion for full data visibility like To Do Analytics */
        }

        #summaryCardTitle {
            color: #666666;
            font-size: 12px;      /* Increased font size for better readability */
            font-weight: bold;
            line-height: 1.3;     /* Better line height for readability */
        }

        #summaryCardValue {
            color: #0078d4;
            font-size: 32px;      /* APPLIED TO DO ANALYTICS APPROACH: Larger font size for maximum prominence */
            font-weight: bold;
            line-height: 1.1;
            margin: 10px 0px;     /* More generous margins for better spacing */
        }

        #summaryCardSubtitle {
            color: #888888;
            font-size: 11px;      /* Increased subtitle font for better readability */
            line-height: 1.3;     /* Better line height */
        }

        /* Overview Tab Widget Styles */
        #overviewTabWidget::pane {
            border: 1px solid #d0d0d0;
            background-color: #f9f9f9;
        }

        #overviewTabWidget QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            padding: 8px 16px;
            border: 1px solid #d0d0d0;
            border-bottom: none;
        }

        #overviewTabWidget QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        #overviewTabWidget QTabBar::tab:hover {
            background-color: #e0e0e0;
        }

        /* Dashboard Main Tabs - Light Theme */
        #dashboardMainTabs::pane {
            border: 1px solid #d0d0d0;
            background-color: #ffffff;
        }

        #dashboardMainTabs QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            padding: 10px 20px;
            border: 1px solid #d0d0d0;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }

        #dashboardMainTabs QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        #dashboardMainTabs QTabBar::tab:hover {
            background-color: #e0e0e0;
            color: #333333;
        }

        /* Habit Tracker Specific Styles */
        #habitDateLabel {
            color: #666666;
            font-size: 12px;
        }

        #habitScrollArea {
            background-color: transparent;
            border: none;
        }

        #habitGridWidget {
            background-color: transparent;
        }

        #habitCard {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 10px;
        }

        #habitCard:hover {
            border-color: #0078d4;
        }

        #habitCardCompleted {
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 10px;
        }

        #habitCardCompleted:hover {
            opacity: 0.9;
        }

        #habitIcon {
            color: #000000;
        }

        #habitName {
            color: #000000;
            font-weight: bold;
        }

        #habitProgress {
            color: #666666;
            font-size: 10px;
        }

        #habitCheckBox {
            spacing: 5px;
        }

        #habitCheckBox::indicator {
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 2px solid #d0d0d0;
            background-color: #ffffff;
        }

        #habitCheckBox::indicator:checked {
            background-color: #0078d4;
            border-color: #0078d4;
        }

        #habitCheckBox::indicator:checked:hover {
            background-color: #106ebe;
        }

        #habitProgressFrame, #habitStatsFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }

        #habitProgressTitle, #habitStatsTitle {
            color: #000000;
        }

        #habitCompletionLabel, #habitMessageLabel {
            color: #666666;
        }

        #habitMainProgressBar {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            text-align: center;
        }

        #habitMainProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }

        #habitStatValue {
            color: #0078d4;
            font-weight: bold;
        }

        #habitManagementItem {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 10px;
            margin: 2px 0;
        }

        #habitManagementName {
            color: #000000;
            font-weight: bold;
        }

        #habitManagementDetails {
            color: #666666;
            font-size: 10px;
        }

        /* Attendance Tracker Specific Styles */

        #attendanceTabWidget::pane {
            border: 1px solid #d0d0d0;
            background-color: #f9f9f9;
        }

        #attendanceTabWidget QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            padding: 8px 16px;
            border: 1px solid #d0d0d0;
            border-bottom: none;
        }

        #attendanceTabWidget QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }

        #attendanceDateLabel {
            color: #000000;
            font-weight: bold;
        }

        #attendanceDayLabel {
            color: #666666;
        }

        #attendancePeriodsFrame, #attendanceActionsFrame, #attendanceSummaryFrame,
        #attendanceNotesFrame, #attendanceStatsFrame, #attendanceSemesterFrame,
        #attendanceProgressFrame {
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }

        #periodButton {
            min-width: 60px;
            min-height: 40px;
            border-radius: 4px;
            font-weight: bold;
        }

        #attendanceSummaryValue, #attendanceStatValue, #attendanceSemesterValue {
            color: #0078d4;
            font-weight: bold;
        }

        #attendancePercentageValue {
            font-weight: bold;
            font-size: 12px;
        }

        #attendanceOverallPercentage {
            font-weight: bold;
            font-size: 16px;
        }

        #attendanceThresholdStatus {
            font-weight: bold;
        }

        #attendanceProgressBar {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            text-align: center;
        }

        #attendanceProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }

        #attendanceStatsTitle {
            color: #000000;
        }

        #attendanceProgressLabel {
            color: #666666;
        }

        #attendanceNotesEdit {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            color: #000000;
            padding: 5px;
            border-radius: 3px;
        }
        """

    def _get_colorwave_theme(self) -> str:
        """Get colorwave theme stylesheet"""
        return """
        /* Global Default Widget Styles */
        QWidget {
            background-color: #0a0a1a;
            color: #ffffff;
        }

        QFrame {
            background-color: #1a1a2e;
            border: 1px solid #4a3c5a;
            border-radius: 4px;
            color: #ffffff;
        }

        /* Main Window */
        QMainWindow {
            background-color: #0a0a1a;
            color: #ffffff;
        }

        /* Menu Bar */
        QMenuBar {
            background-color: #1a1a2e;
            color: #ffffff;
            border-bottom: 1px solid #4a3c5a;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }

        QMenuBar::item:selected {
            background-color: #e91e63;
            color: #ffffff;
        }

        QMenuBar::item:pressed {
            background-color: #c2185b;
        }

        /* Menu */
        QMenu {
            background-color: #1a1a2e;
            color: #ffffff;
            border: 1px solid #4a3c5a;
        }

        QMenu::item {
            padding: 4px 20px;
        }

        QMenu::item:selected {
            background-color: #e91e63;
        }

        /* Buttons */
        QPushButton {
            background-color: #c2185b;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 11px;
            min-height: 32px;
        }

        QPushButton:hover {
            background-color: #e91e63;
        }

        QPushButton:pressed {
            background-color: #ad1457;
        }

        QPushButton:disabled {
            background-color: #888888;
            color: #cccccc;
        }

        /* Secondary buttons */
        QPushButton[type="secondary"] {
            background-color: #7b1fa2;
            color: #ffffff;
        }

        QPushButton[type="secondary"]:hover {
            background-color: #9c27b0;
        }

        QPushButton[type="secondary"]:pressed {
            background-color: #6a1b9a;
        }

        /* Text inputs */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #2d1b3d;
            color: #ffffff;
            border: 1px solid #4a3c5a;
            border-radius: 4px;
            padding: 4px 8px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #00bcd4;
        }

        /* Combo boxes */
        QComboBox {
            background-color: #2d1b3d;
            color: #ffffff;
            border: 1px solid #4a3c5a;
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 20px;
        }

        QComboBox:hover {
            border-color: #c2185b;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #ffffff;
            margin-right: 5px;
        }

        QComboBox QAbstractItemView {
            background-color: #1a1a2e;
            color: #ffffff;
            border: 1px solid #4a3c5a;
            selection-background-color: #c2185b;
        }

        /* Tables */
        QTableWidget, QTableView {
            background-color: #1a1a2e;
            color: #ffffff;
            gridline-color: #4a3c5a;
            border: 1px solid #4a3c5a;
        }

        QTableWidget::item, QTableView::item {
            background-color: #1a1a2e;
            color: #ffffff;
            border-bottom: 1px solid #4a3c5a;
        }

        QTableWidget::item:selected, QTableView::item:selected {
            background-color: #c2185b;
            color: #ffffff;
        }

        QTableWidget::item:hover, QTableView::item:hover {
            background-color: rgba(194, 24, 91, 0.1);
        }

        QHeaderView::section {
            background-color: #2d1b3d;
            color: #ffffff;
            border: 1px solid #4a3c5a;
            padding: 4px;
        }

        /* Progress bars */
        QProgressBar {
            background-color: #2d1b3d;
            border: 1px solid #4a3c5a;
            border-radius: 4px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #00bcd4;
            border-radius: 3px;
        }

        /* Scroll bars */
        QScrollBar:vertical {
            background-color: #1a1a2e;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #c2185b;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #e91e63;
        }

        QScrollBar:horizontal {
            background-color: #1a1a2e;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background-color: #c2185b;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #e91e63;
        }

        /* Status bar */
        QStatusBar {
            background-color: #1a1a2e;
            color: #ffffff;
            border-top: 1px solid #4a3c5a;
        }

        /* Tool tips */
        QToolTip {
            background-color: #2d1b3d;
            color: #ffffff;
            border: 1px solid #4a3c5a;
            padding: 5px;
            border-radius: 3px;
        }

        /* Dashboard Main Tabs - Colorwave Theme */
        #dashboardMainTabs::pane {
            border: 1px solid #4a3c5a;
            background-color: #0a0a1a;
        }

        #dashboardMainTabs QTabBar::tab {
            background-color: #1a1a2e;
            color: #ffffff;
            padding: 10px 20px;
            border: 1px solid #4a3c5a;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }

        #dashboardMainTabs QTabBar::tab:selected {
            background-color: #c2185b;
            color: #ffffff;
        }

        #dashboardMainTabs QTabBar::tab:hover {
            background-color: #2d1b3d;
            color: #ffffff;
        }
        """

    def _get_palette(self, theme: str = "dark") -> QPalette:
        """Get palette for specified theme"""
        palette = QPalette()

        if theme == "dark":
            # Dark theme palette
            palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#252526"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2d2d30"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#3e3e42"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#3e3e42"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#0e639c"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#0e639c"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

            # Disabled colors
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#999999"))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#999999"))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#999999"))

        elif theme == "light":
            # Light theme palette
            palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f9f9f9"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffcc"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#f0f0f0"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#0078d4"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078d4"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

            # Disabled colors
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#666666"))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#666666"))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#666666"))

        elif theme == "colorwave":
            # Colorwave theme palette
            palette.setColor(QPalette.ColorRole.Window, QColor("#0a0a1a"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#1a1a2e"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2d1b3d"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2d1b3d"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#2d1b3d"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#f44336"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#c2185b"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#c2185b"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

            # Disabled colors
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#888888"))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#888888"))
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#888888"))

        return palette
