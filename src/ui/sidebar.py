"""
Sidebar Navigation Module
Collapsible sidebar with navigation buttons for all modules
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QScrollArea, QButtonGroup, QToolButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter



class SidebarButton(QPushButton):
    """Custom button for sidebar navigation"""
    
    def __init__(self, text: str, icon_name: str = None, parent=None):
        super().__init__(text, parent)
        
        self.setCheckable(True)
        self.setMinimumHeight(45)
        self.setMaximumHeight(45)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set button properties
        self.setText(text)
        self.setToolTip(text)
        
        # Set icon if provided
        if icon_name:
            self.set_icon(icon_name)
        
        # Apply styling
        self.setObjectName("sidebarButton")
    
    def set_icon(self, icon_name: str):
        """Set button icon"""
        # For now, we'll use text-based icons
        # In a real application, you'd load actual icon files
        icon_map = {
            "dashboard": "📊",
            "expenses": "💰",
            "income": "💵",
            "habits": "✅",
            "attendance": "📅",
            "todos": "📝",
            "investments": "📈",
            "budget": "💳",
            "trading": "💹",
            "settings": "⚙️"
        }
        
        if icon_name in icon_map:
            self.setText(f"{icon_map[icon_name]} {self.text()}")


class Sidebar(QWidget):
    """Collapsible sidebar navigation widget"""
    
    # Signals
    module_selected = Signal(str)
    sidebar_toggled = Signal(bool)  # True if collapsed
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.is_collapsed = False
        self.expanded_width = config.sidebar_width
        self.collapsed_width = config.sidebar_collapsed_width
        
        self.setup_ui()
        self.setup_navigation()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the sidebar UI"""
        # Set widget properties
        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.expanded_width)
        self.setObjectName("sidebar")
        
        # Create main layout - more compact
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(3, 3, 3, 3)  # Reduced from 5px to 3px
        self.main_layout.setSpacing(3)  # Reduced from 5px to 3px
        
        # Create header
        self.create_header()
        
        # Create navigation area
        self.create_navigation()
        
        # Create footer
        self.create_footer()
    
    def create_header(self):
        """Create sidebar header with toggle button"""
        header_frame = QFrame()
        header_frame.setObjectName("sidebarHeader")
        header_frame.setMinimumHeight(50)  # Reduced from 60px to 50px
        header_frame.setMaximumHeight(50)  # Reduced from 60px to 50px
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 8, 8, 8)  # Reduced from 10px to 8px
        
        # App title
        self.title_label = QLabel("Finance Dashboard")
        self.title_label.setObjectName("sidebarTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.title_label.setFont(font)
        header_layout.addWidget(self.title_label)
        
        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setText("☰")
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setMinimumSize(30, 30)
        self.toggle_button.setMaximumSize(30, 30)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.toggle_button)
        
        self.main_layout.addWidget(header_frame)
    
    def create_navigation(self):
        """Create navigation buttons"""
        # Create scroll area for navigation
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setObjectName("sidebarScrollArea")
        
        # Create navigation widget
        nav_widget = QWidget()
        nav_widget.setObjectName("navigationWidget")
        self.nav_layout = QVBoxLayout(nav_widget)
        self.nav_layout.setContentsMargins(3, 3, 3, 3)  # Reduced from 5px to 3px
        self.nav_layout.setSpacing(2)  # Reduced from 3px to 2px
        
        scroll_area.setWidget(nav_widget)
        self.main_layout.addWidget(scroll_area)
        
        # Store navigation widget for later use
        self.nav_widget = nav_widget
    
    def setup_navigation(self):
        """Setup navigation buttons"""
        # Create button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Define navigation items
        nav_items = [
            ("dashboard", "Dashboard", "dashboard"),
            ("expenses", "Expense Tracker", "expenses"),
            ("income", "Goal Income", "income"),
            ("habits", "Habit Tracker", "habits"),
            ("attendance", "Attendance", "attendance"),
            ("todos", "To-Do List", "todos"),
            ("investments", "Investments", "investments"),
            ("budget", "Budget Planning", "budget"),
            ("trading", "Trading", "trading"),
        ]
        
        self.nav_buttons = {}
        
        for module_id, display_name, icon_name in nav_items:
            button = SidebarButton(display_name, icon_name)
            button.clicked.connect(lambda checked, mid=module_id: self.on_button_clicked(mid))
            self.button_group.addButton(button)
            self.nav_layout.addWidget(button)
            self.nav_buttons[module_id] = button
            
        # Add stretch to push buttons to top
        self.nav_layout.addStretch()
        
        # Set dashboard as default selected
        self.nav_buttons["dashboard"].setChecked(True)
    
    def create_footer(self):
        """Create sidebar footer"""
        footer_frame = QFrame()
        footer_frame.setObjectName("sidebarFooter")
        footer_frame.setMinimumHeight(50)
        footer_frame.setMaximumHeight(50)
        
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        # Settings button
        self.settings_button = SidebarButton("Settings", "settings")
        self.settings_button.setCheckable(False)
        self.settings_button.clicked.connect(self.show_settings)
        footer_layout.addWidget(self.settings_button)
        
        self.main_layout.addWidget(footer_frame)
    
    def setup_connections(self):
        """Setup signal connections"""
        pass
    
    def toggle_sidebar(self):
        """Toggle sidebar between expanded and collapsed states"""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.collapse_sidebar()
        else:
            self.expand_sidebar()
        
        self.sidebar_toggled.emit(self.is_collapsed)
    
    def collapse_sidebar(self):
        """Collapse the sidebar"""
        # Hide text labels
        self.title_label.hide()
        
        # Update button text to show only icons
        for module_id, button in self.nav_buttons.items():
            text = button.text()
            if " " in text:
                icon = text.split(" ")[0]
                button.setText(icon)
                button.setToolTip(text.split(" ", 1)[1])
        
        # Update settings button
        settings_text = self.settings_button.text()
        if " " in settings_text:
            icon = settings_text.split(" ")[0]
            self.settings_button.setText(icon)
            self.settings_button.setToolTip("Settings")
        
        # Set collapsed width
        self.setMaximumWidth(self.collapsed_width)
        self.setMinimumWidth(self.collapsed_width)
    
    def expand_sidebar(self):
        """Expand the sidebar"""
        # Show text labels
        self.title_label.show()
        
        # Restore button text
        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("expenses", "💰 Expense Tracker"),
            ("income", "💵 Goal Income"),
            ("habits", "✅ Habit Tracker"),
            ("attendance", "📅 Attendance"),
            ("todos", "📝 To-Do List"),
            ("investments", "📈 Investments"),
            ("budget", "💳 Budget Planning"),
            ("trading", "💹 Trading"),
        ]
        
        for module_id, display_text in nav_items:
            if module_id in self.nav_buttons:
                self.nav_buttons[module_id].setText(display_text)
                self.nav_buttons[module_id].setToolTip(display_text.split(" ", 1)[1])
        
        # Restore settings button
        self.settings_button.setText("⚙️ Settings")
        self.settings_button.setToolTip("Settings")
        
        # Set expanded width
        self.setMaximumWidth(self.expanded_width)
        self.setMinimumWidth(self.expanded_width)
    
    def on_button_clicked(self, module_id: str):
        """Handle navigation button click"""
        self.module_selected.emit(module_id)
    
    def show_settings(self):
        """Show settings dialog"""
        try:
            from .settings_dialog import SettingsDialog

            # Get the main window to pass data_manager and config
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'data_manager'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'data_manager'):
                dialog = SettingsDialog(main_window.config, main_window.data_manager, self)
                dialog.exec()
            else:
                # Fallback - create a simple settings dialog
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Settings", "Settings functionality is available!\n\nFeatures:\n• Holiday Management\n• Theme Settings\n• Application Preferences")

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to open settings: {str(e)}")
    
    def set_active_module(self, module_id: str):
        """Set the active module programmatically"""
        if module_id in self.nav_buttons:
            self.nav_buttons[module_id].setChecked(True)
