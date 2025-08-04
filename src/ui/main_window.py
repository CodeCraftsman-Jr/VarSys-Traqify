"""
Main Window Module
The primary application window with collapsible sidebar navigation
"""

import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QSplitter, QFrame, QLabel, QPushButton, QToolButton, QStatusBar,
    QMenuBar, QMenu, QMessageBox, QApplication, QDialog
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QAction, QIcon, QFont, QPixmap

from ..core.config import AppConfig, SettingsManager
from ..core.data_manager import DataManager
from ..core.update_system import UpdateManager
from .sidebar import Sidebar
from .dashboard import DashboardWidget
from .global_search import GlobalSearchDialog
from .styles import StyleManager
from .simple_optimized_styles import OptimizedStyleManager
from .simple_theme_overlay import SimpleThemeSwitchManager
from .plotly_theme import configure_plotly_theme
from .update_dialog import UpdateNotificationDialog, UpdateProgressDialog, UpdateSettingsDialog, UpdateHistoryDialog
from ..modules.expenses.widgets import ExpenseTrackerWidget
from ..modules.income.widgets import IncomeTrackerWidget
from ..modules.habits.widgets import HabitTrackerWidget
from ..modules.attendance.widgets import AttendanceTrackerWidget
from ..modules.todos.widgets import TodoTrackerWidget
from ..modules.investments.widgets import InvestmentTrackerWidget
from ..modules.budget.widgets import BudgetPlannerWidget
from ..modules.trading.widgets import TradingWidget


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation"""

    # Signals
    module_changed = Signal(str)
    initialization_complete = Signal()
    initialization_progress = Signal(str)  # For detailed progress updates
    
    def __init__(self, data_manager: DataManager, config: AppConfig, progress_callback=None):
        super().__init__()

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*60)
        self.logger.info("INITIALIZING MAIN WINDOW")
        self.logger.info("="*60)

        self.data_manager = data_manager
        self.config = config
        self.settings_manager = SettingsManager()
        self.progress_callback = progress_callback

        # Helper function to update progress
        def update_progress(progress, message, detail=""):
            if self.progress_callback:
                # Pass detail as both detail and step_detail for loading steps display
                self.progress_callback(progress, message, detail, detail)
            self.initialization_progress.emit(message)

        # Initialize optimized style manager
        update_progress(47, "Initializing style manager", "Setting up application styling and visual themes")
        self.style_manager = OptimizedStyleManager(QApplication.instance())

        # Initialize theme switch manager for visual feedback
        update_progress(49, "Setting up theme manager", "Configuring theme system and visual preferences")
        self.theme_switch_manager = SimpleThemeSwitchManager(self)

        # Initialize Firebase sync engine
        update_progress(51, "Connecting to Firebase", "Establishing cloud synchronization and data sync")
        self.sync_engine = None
        self.initialize_firebase_sync()

        self.logger.debug("Core components initialized")
        update_progress(53, "Core components ready", "Basic window systems and services initialized")

        # Allow UI updates
        QApplication.processEvents()

        # Initialize UI (this is the heavy operation with module widgets)
        self.logger.info("Setting up UI components...")
        update_progress(55, "Building user interface", "Creating application modules and widgets")
        self.setup_ui()

        # Allow UI updates after heavy UI setup
        QApplication.processEvents()

        update_progress(80, "Creating menu system", "Setting up application menus and navigation")
        self.setup_menu_bar()

        update_progress(82, "Setting up status bar", "Configuring status indicators and information display")
        self.setup_status_bar()

        update_progress(84, "Connecting UI signals", "Linking interface components and event handlers")
        self.setup_connections()

        # Allow UI updates after connections
        QApplication.processEvents()

        update_progress(86, "Applying theme and styles", "Finalizing visual appearance and styling")
        self.apply_theme(force_refresh=True)  # Force refresh to clear any cached stylesheets
        self.logger.info("UI setup complete")

        # Restore window state
        self.logger.debug("Restoring window state...")
        update_progress(87, "Restoring window state", "Loading saved window preferences and layout")
        self.restore_window_state()

        # Setup auto-save timer
        self.logger.debug("Setting up auto-save...")
        update_progress(88, "Configuring auto-save", "Setting up automatic data persistence")
        self.setup_auto_save()

        # Allow UI updates
        QApplication.processEvents()

        # Initialize update system
        self.logger.debug("Initializing update system...")
        update_progress(89, "Initializing update system", "Preparing application update mechanisms")
        self.setup_update_system()

        self.logger.info("MainWindow initialization complete")
        update_progress(89, "Main window ready", "Application interface and systems complete")

        # Emit signal that initialization is complete
        self.initialization_complete.emit()

    def trigger_post_loading_dialogs(self):
        """Trigger any dialogs that should appear after loading screen completes"""
        # Trigger trading startup dialog if it's pending
        if hasattr(self, 'trading_widget') and self.trading_widget:
            if hasattr(self.trading_widget, 'trigger_startup_dialog_if_pending'):
                self.trading_widget.trigger_startup_dialog_if_pending()
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Set window properties
        self.setWindowTitle(f"{self.config.app_name} v{self.config.app_version}")
        self.setMinimumSize(800, 600)
        self.resize(self.config.window_width, self.config.window_height)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable sidebar
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Create sidebar
        self.sidebar = Sidebar(self.config)
        self.splitter.addWidget(self.sidebar)
        
        # Create content area
        self.content_widget = QStackedWidget()
        self.splitter.addWidget(self.content_widget)
        
        # Set splitter proportions
        self.splitter.setSizes([self.config.sidebar_width, 
                               self.config.window_width - self.config.sidebar_width])
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        
        # Create content pages with progress updates
        QApplication.processEvents()  # Allow UI updates before heavy content creation
        self.setup_content_pages()
    
    def setup_content_pages(self):
        """Setup all content pages"""
        self.logger.info("Setting up content pages...")

        # Helper function to update progress during module creation
        def update_module_progress(progress, message, detail=""):
            if hasattr(self, 'progress_callback') and self.progress_callback:
                # Pass detail as both detail and step_detail for loading steps display
                self.progress_callback(progress, message, detail, detail)

        try:
            # Dashboard (default page)
            self.logger.debug("Creating Dashboard widget...")
            update_module_progress(57, "Creating dashboard", "Setting up main overview and summary widgets")
            QApplication.processEvents()  # Allow UI updates
            self.dashboard = DashboardWidget(self.data_manager, self.config)
            self.content_widget.addWidget(self.dashboard)
            self.logger.debug("Dashboard widget created successfully")
            QApplication.processEvents()  # Allow UI updates after heavy widget creation

            # Expense Tracker
            self.logger.debug("Creating Expense Tracker widget...")
            update_module_progress(60, "Creating expense tracker", "Setting up expense management and tracking")
            QApplication.processEvents()  # Allow UI updates
            self.expense_tracker = ExpenseTrackerWidget(self.data_manager, self.config)
            self.content_widget.addWidget(self.expense_tracker)
            self.logger.debug("Expense Tracker widget created successfully")
            QApplication.processEvents()  # Allow UI updates after heavy widget creation

            # Income Tracker
            self.logger.debug("Creating Income Tracker widget...")
            update_module_progress(63, "Creating income tracker", "Setting up income management and tracking")
            self.income_tracker = IncomeTrackerWidget(self.data_manager, self.config)
            self.content_widget.addWidget(self.income_tracker)
            self.logger.debug("Income Tracker widget created successfully")

            # Habit Tracker
            self.logger.debug("Creating Habit Tracker widget...")
            update_module_progress(66, "Creating habit tracker", "Setting up habit tracking and management")
            self.habit_tracker = HabitTrackerWidget(self.data_manager, self.config)
            self.content_widget.addWidget(self.habit_tracker)
            self.logger.debug("Habit Tracker widget created successfully")

            # Attendance Tracker - RE-ENABLED WITH SIMPLIFIED IMPLEMENTATION
            self.logger.debug("Creating Simplified Attendance Tracker widget...")
            update_module_progress(68, "Creating attendance tracker", "Setting up attendance tracking and management")
            try:
                from ..modules.attendance.simple_widgets import SimpleAttendanceTrackerWidget
                self.attendance_tracker = SimpleAttendanceTrackerWidget(self.data_manager, self.config)
                self.content_widget.addWidget(self.attendance_tracker)
                self.logger.debug("Simplified Attendance Tracker widget created successfully")
            except Exception as e:
                self.logger.error(f"Failed to create Simplified Attendance Tracker: {e}")
                self.attendance_tracker = None

            # To-Do List Module
            self.logger.debug("Creating To-Do List widget...")
            update_module_progress(70, "Creating todo tracker", "Setting up task management and organization")
            try:
                from ..modules.todos.widgets import TodoTrackerWidget
                self.todo_tracker = TodoTrackerWidget(self.data_manager, self.config)
                self.content_widget.addWidget(self.todo_tracker)
                self.logger.debug("To-Do List widget created successfully")
            except Exception as e:
                self.logger.error(f"Failed to create To-Do List widget: {e}")
                self.todo_tracker = None

            # Investment Tracker Module
            self.logger.debug("Creating Investment Tracker widget...")
            update_module_progress(72, "Creating investment tracker", "Setting up investment portfolio management")
            try:
                self.investment_tracker = InvestmentTrackerWidget(self.data_manager, self.config)
                self.content_widget.addWidget(self.investment_tracker)
                self.logger.debug("Investment Tracker widget created successfully")
            except Exception as e:
                self.logger.error(f"Failed to create Investment Tracker widget: {e}")
                import traceback
                self.logger.error(f"Investment Tracker error traceback: {traceback.format_exc()}")
                self.investment_tracker = None

            # Budget Planner Module
            self.logger.debug("Creating Budget Planner widget...")
            update_module_progress(74, "Creating budget planner", "Setting up budget planning and analysis")
            try:
                self.budget_planner = BudgetPlannerWidget(self.data_manager, self.config)
                self.content_widget.addWidget(self.budget_planner)
                self.logger.debug("Budget Planner widget created successfully")
            except Exception as e:
                self.logger.error(f"Failed to create Budget Planner widget: {e}")
                self.budget_planner = None

            # Trading Module
            self.logger.debug("Creating Trading widget...")
            update_module_progress(76, "Creating trading module", "Setting up trading interface and tools")
            try:
                self.trading_widget = TradingWidget(self.data_manager, self.config)
                self.content_widget.addWidget(self.trading_widget)
                self.logger.debug("Trading widget created successfully")

                # Note: Trading widget will handle its own authentication flow
                # including optional authentication and user education

            except Exception as e:
                self.logger.error(f"Failed to create Trading widget: {e}")
                self.trading_widget = None

            # All modules created
            update_module_progress(78, "Modules created", "All application modules and widgets loaded successfully")

        except Exception as e:
            self.logger.error(f"Critical error in setup_content_pages: {e}")
            raise

        # Module widgets mapping
        self.module_widgets = {
            'dashboard': self.dashboard,
            'expenses': self.expense_tracker,
            'income': self.income_tracker,
            'habits': self.habit_tracker,
            'attendance': self.attendance_tracker,  # Will be None if failed to load
            'todos': self.todo_tracker,  # Will be None if failed to load
            'investments': self.investment_tracker,  # Will be None if failed to load
            'budget': self.budget_planner,  # Will be None if failed to load
            'trading': self.trading_widget  # Will be None if failed to load
        }

        # Log module status
        for module_name, widget in self.module_widgets.items():
            status = "✅ LOADED" if widget is not None else "❌ NOT LOADED"
            self.logger.info(f"Module '{module_name}': {status}")

        # Set dashboard as default
        print(f"DEBUG: Setting dashboard as current widget. Dashboard widget: {self.dashboard}")
        print(f"DEBUG: Content widget has {self.content_widget.count()} widgets")
        print(f"DEBUG: Dashboard widget size: {self.dashboard.size()}")
        self.content_widget.setCurrentWidget(self.dashboard)
        print(f"DEBUG: Current widget after setting: {self.content_widget.currentWidget()}")
        print(f"DEBUG: Current widget index: {self.content_widget.currentIndex()}")
        self.logger.info("Content pages setup complete")

    def initialize_firebase_sync(self):
        """Initialize Firebase sync engine using secure backend system"""
        try:
            from ..core.firebase_sync import FirebaseSyncEngine

            # Create sync engine with secure backend system
            self.sync_engine = FirebaseSyncEngine(self.data_manager)

            # Connect sync engine to data manager
            self.data_manager.set_sync_engine(self.sync_engine)

            self.logger.info("Firebase sync engine initialized with secure backend system")

        except ImportError:
            self.logger.info("Firebase sync dependencies not available, sync disabled")
        except Exception as e:
            self.logger.error(f"Error initializing Firebase sync: {e}")

    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")

        # New action
        new_action = QAction("&New Entry", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_entry)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        # Import/Export actions
        import_action = QAction("&Import Data", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)

        export_action = QAction("&Export Data", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Backup actions
        backup_action = QAction("Create &Backup", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Theme actions
        theme_menu = view_menu.addMenu("&Theme")

        light_theme_action = QAction("&Light", self)
        light_theme_action.triggered.connect(lambda: self.change_theme("light"))
        theme_menu.addAction(light_theme_action)

        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.triggered.connect(lambda: self.change_theme("dark"))
        theme_menu.addAction(dark_theme_action)

        colorwave_theme_action = QAction("&Colorwave", self)
        colorwave_theme_action.triggered.connect(lambda: self.change_theme("colorwave"))
        theme_menu.addAction(colorwave_theme_action)
        
        view_menu.addSeparator()
        
        # Sidebar toggle
        toggle_sidebar_action = QAction("Toggle &Sidebar", self)
        toggle_sidebar_action.setShortcut("Ctrl+B")
        toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Global Search action
        search_action = QAction("&Global Search", self)
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.show_global_search)
        tools_menu.addAction(search_action)

        tools_menu.addSeparator()

        # Settings action
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Check for updates action
        check_updates_action = QAction("Check for &Updates", self)
        check_updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_updates_action)

        # Update settings action
        update_settings_action = QAction("Update &Settings", self)
        update_settings_action.triggered.connect(self.show_update_settings)
        help_menu.addAction(update_settings_action)

        # Update history action
        update_history_action = QAction("Update &History", self)
        update_history_action.triggered.connect(self.show_update_history)
        help_menu.addAction(update_history_action)

        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status labels
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Add permanent widgets
        self.records_label = QLabel("Records: 0")
        self.status_bar.addPermanentWidget(self.records_label)

        # Trading connection status
        self.trading_status_label = QLabel("🔴 Trading: Not Connected")
        self.trading_status_label.setStyleSheet("color: #DC3545; font-size: 10px;")
        self.trading_status_label.setToolTip("Trading connection status - click Trading tab to connect")
        self.status_bar.addPermanentWidget(self.trading_status_label)

        self.auto_save_label = QLabel("Auto-save: ON")
        self.status_bar.addPermanentWidget(self.auto_save_label)
    
    def setup_connections(self):
        """Setup signal connections with enhanced error handling"""
        try:
            # Sidebar connections
            if hasattr(self.sidebar, 'module_selected'):
                self.sidebar.module_selected.connect(self.switch_module)
                self.logger.debug("Sidebar module_selected signal connected")

            if hasattr(self.sidebar, 'sidebar_toggled'):
                self.sidebar.sidebar_toggled.connect(self.on_sidebar_toggled)
                self.logger.debug("Sidebar toggle signal connected")

            # Data manager connections
            if hasattr(self.data_manager, 'data_changed'):
                self.data_manager.data_changed.connect(self.on_data_changed)
                self.logger.debug("Data manager data_changed signal connected")

            # Trading widget connections
            if self.trading_widget and hasattr(self.trading_widget, 'token_manager'):
                # Connect to token manager signals if available
                QTimer.singleShot(2000, self.setup_trading_connections)  # Delay to ensure token manager is initialized

            if hasattr(self.data_manager, 'error_occurred'):
                self.data_manager.error_occurred.connect(self.show_error)
                self.logger.debug("Data manager error_occurred signal connected")

            self.logger.info("✅ All signal connections established successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to setup signal connections: {e}")
            self.show_error(f"Failed to setup application connections: {str(e)}")

    def setup_trading_connections(self):
        """Setup connections to trading widget signals"""
        try:
            if self.trading_widget:
                # Connect to connection status changes
                if hasattr(self.trading_widget, 'on_connection_status_changed'):
                    # We'll monitor the trading widget's connection status
                    pass

                # Update initial status
                self.update_trading_status(False)  # Start with disconnected status

                self.logger.debug("Trading connections setup completed")

        except Exception as e:
            self.logger.error(f"Error setting up trading connections: {e}")

    def update_trading_status(self, connected: bool, user_info: dict = None):
        """Update trading connection status in status bar"""
        try:
            if connected:
                if user_info and user_info.get('user_name'):
                    status_text = f"🟢 Trading: {user_info['user_name']}"
                else:
                    status_text = "🟢 Trading: Connected"
                self.trading_status_label.setText(status_text)
                self.trading_status_label.setStyleSheet("color: #28A745; font-size: 10px;")
                self.trading_status_label.setToolTip("Trading connection active")
            else:
                self.trading_status_label.setText("🔴 Trading: Not Connected")
                self.trading_status_label.setStyleSheet("color: #DC3545; font-size: 10px;")
                self.trading_status_label.setToolTip("Trading connection inactive - click Trading tab to connect")

        except Exception as e:
            self.logger.error(f"Error updating trading status: {e}")

    def setup_auto_save(self):
        """Setup auto-save timer"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(self.config.auto_save_interval * 1000)  # Convert to milliseconds
    
    def apply_theme(self, force_refresh=False):
        """Apply the current theme"""
        self.style_manager.apply_theme(self.config.theme, force_refresh=force_refresh)

        # CRITICAL FIX: Set theme on QApplication instance for chart widgets to access
        app = QApplication.instance()
        if app:
            app.current_theme = self.config.theme

        # Configure Plotly theme based on current theme
        self.configure_plotly_theme(self.config.theme)

        # Propagate theme changes to dashboard components
        self.propagate_theme_changes(self.config.theme)

    def configure_plotly_theme(self, theme):
        """Configure Plotly theme based on current application theme"""
        try:
            configure_plotly_theme(theme)
        except Exception as e:
            self.logger.warning(f"Failed to configure Plotly theme: {e}")
            # Fallback to light theme if configuration fails
            try:
                from .plotly_theme import configure_plotly_light_theme
                configure_plotly_light_theme()
            except:
                pass
    
    def switch_module(self, module_name: str):
        """Switch to a different module"""
        self.logger.debug(f"switch_module called with: {module_name}")

        # Remove the forced disable - we're going to fix the module
        # if module_name == "attendance":
        #     self.logger.info(f"🚨 ATTENDANCE MODULE CLICKED - Showing disabled dialog")
        #     self.show_attendance_disabled_dialog()
        #     return

        if module_name in self.module_widgets:
            widget = self.module_widgets[module_name]
            self.logger.debug(f"Widget for {module_name}: {widget}")

            if widget is not None:
                self.content_widget.setCurrentWidget(widget)
                self.module_changed.emit(module_name)
                self.status_label.setText(f"Switched to {module_name.title()}")
                self.logger.debug(f"Successfully switched to {module_name}")
            else:
                # Handle specific disabled modules with detailed feedback
                self.logger.debug(f"Module {module_name} is disabled (widget is None)")
                if module_name == "attendance":
                    self.show_attendance_disabled_dialog()
                elif module_name == "investments":
                    self.show_investment_error_dialog()
                else:
                    # Generic message for other modules
                    self.status_label.setText(f"{module_name.title()} module coming soon...")
        else:
            self.logger.warning(f"Module {module_name} not found in module_widgets")
            self.status_label.setText(f"Module {module_name} not found")
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        self.sidebar.toggle_sidebar()
    
    def on_sidebar_toggled(self, collapsed: bool):
        """Handle sidebar toggle"""
        if collapsed:
            self.splitter.setSizes([self.config.sidebar_collapsed_width, 
                                   self.width() - self.config.sidebar_collapsed_width])
        else:
            self.splitter.setSizes([self.config.sidebar_width, 
                                   self.width() - self.config.sidebar_width])
    
    def on_data_changed(self, module: str, operation: str):
        """Handle data changes"""
        self.status_label.setText(f"Data {operation} in {module}")
        # Update record count if needed
        self.update_record_count()
    
    def update_record_count(self):
        """Update the record count in status bar"""
        # This will be implemented when modules are added
        pass
    
    def show_error(self, error_message: str, title: str = "Error", details: str = None):
        """Show enhanced error message to user with logging and crash protection"""
        try:
            self.logger.error(f"User error displayed: {error_message}")

            # Create enhanced error dialog with error handling
            try:
                from PySide6.QtWidgets import QMessageBox  # Ensure import is available
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle(title)
                msg_box.setText(error_message)

                # Add details if provided
                if details:
                    msg_box.setDetailedText(details)

                # Add helpful buttons
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Help)
                msg_box.setDefaultButton(QMessageBox.Ok)

                # Show status bar message safely
                try:
                    if hasattr(self, 'status_label') and self.status_label:
                        self.status_label.setText(f"❌ Error: {error_message}")
                except Exception as status_error:
                    self.logger.error(f"Error updating status bar: {status_error}")

                # Handle help button
                result = msg_box.exec()
                if result == QMessageBox.Help:
                    try:
                        self.show_help_dialog()
                    except Exception as help_error:
                        self.logger.error(f"Error showing help dialog: {help_error}")

            except Exception as dialog_error:
                self.logger.error(f"Error creating error dialog: {dialog_error}")
                # Fallback to simple message box
                try:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(None, title, error_message)
                except Exception as fallback_error:
                    self.logger.error(f"Error showing fallback error dialog: {fallback_error}")

        except Exception as e:
            # Last resort - log the error and don't crash
            try:
                self.logger.error(f"Critical error in show_error method: {e}")
                print(f"CRITICAL ERROR in show_error: {e}")
                print(f"Original error message: {error_message}")
            except:
                # Even logging failed, just print to console
                print(f"CRITICAL ERROR: show_error method failed completely")
                print(f"Original error: {error_message}")
                print(f"Show error failure: {e}")

    def show_warning(self, message: str, title: str = "Warning"):
        """Show warning message to user"""
        self.logger.warning(f"User warning displayed: {message}")
        QMessageBox.warning(self, title, message)
        self.status_label.setText(f"⚠️ Warning: {message}")

    def show_info(self, message: str, title: str = "Information"):
        """Show information message to user"""
        self.logger.info(f"User info displayed: {message}")
        QMessageBox.information(self, title, message)
        self.status_label.setText(f"ℹ️ {message}")

    def show_success(self, message: str):
        """Show success message in status bar"""
        self.logger.info(f"Success: {message}")
        self.status_label.setText(f"✅ {message}")

    def show_attendance_disabled_dialog(self):
        """Show dialog explaining why attendance module is disabled"""
        dialog_text = """
        <h3>⚠️ Attendance Module Temporarily Disabled</h3>

        <p><b>The Attendance Tracker module is currently disabled due to technical issues.</b></p>

        <p><b>Issue Details:</b></p>
        <ul>
        <li>Pandas DataFrame operations are causing infinite recursion</li>
        <li>This prevents the module from loading properly</li>
        <li>The issue affects data reading and writing operations</li>
        </ul>

        <p><b>Current Status:</b></p>
        <ul>
        <li>🔧 The development team is working on a fix</li>
        <li>📊 Your existing attendance data is safe and preserved</li>
        <li>🚀 The module will be restored in the next update</li>
        </ul>

        <p><b>Alternative Solutions:</b></p>
        <ul>
        <li>Use the other modules (Expenses, Income, Habits, etc.) which are fully functional</li>
        <li>Check back after the next application update</li>
        <li>Contact support if you need urgent access to attendance data</li>
        </ul>

        <p><i>We apologize for the inconvenience and appreciate your patience.</i></p>
        """

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Attendance Module - Temporarily Disabled")
        msg_box.setText(dialog_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def show_investment_error_dialog(self):
        """Show dialog explaining why investment module failed to load"""
        dialog_text = """
        <h3>⚠️ Investment Module Loading Error</h3>

        <p><b>The Investment Tracker module failed to load properly.</b></p>

        <p><b>Possible Causes:</b></p>
        <ul>
        <li>Matplotlib library compatibility issues with Qt6</li>
        <li>Missing dependencies for chart rendering</li>
        <li>Data model initialization problems</li>
        <li>UI component creation failures</li>
        </ul>

        <p><b>Troubleshooting Steps:</b></p>
        <ul>
        <li>🔄 Restart the application to retry loading</li>
        <li>📊 Check the application logs (app_debug.log) for detailed error information</li>
        <li>🔧 Ensure all required Python packages are installed</li>
        <li>💻 Try updating matplotlib and other chart libraries</li>
        </ul>

        <p><b>Current Status:</b></p>
        <ul>
        <li>📈 Other modules (Expenses, Income, Habits, etc.) are fully functional</li>
        <li>💾 Your investment data is safe and preserved</li>
        <li>🚀 The module will be restored once the issue is resolved</li>
        </ul>

        <p><i>Please check the logs for more detailed error information.</i></p>
        """

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Investment Module - Loading Error")
        msg_box.setText(dialog_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

        # Update status bar
        self.status_label.setText("⚠️ Attendance module is temporarily disabled due to technical issues")

    def show_help_dialog(self):
        """Show help dialog with troubleshooting information"""
        help_text = """
        <h3>Troubleshooting Guide</h3>
        <p><b>Common Issues:</b></p>
        <ul>
        <li><b>Data not saving:</b> Check file permissions in the data directory</li>
        <li><b>Module not loading:</b> Check the logs for detailed error information</li>
        <li><b>Performance issues:</b> Try restarting the application</li>
        <li><b>Display problems:</b> Check your screen resolution and scaling</li>
        </ul>

        <p><b>Log Files:</b></p>
        <p>Detailed logs are saved to: <code>logs/app_debug.log</code></p>

        <p><b>Data Location:</b></p>
        <p>Your data is stored in: <code>data/</code> directory</p>

        <p><b>Backup:</b></p>
        <p>Automatic backups are created in: <code>data/.backups/</code></p>
        """

        help_dialog = QMessageBox(self)
        help_dialog.setIcon(QMessageBox.Information)
        help_dialog.setWindowTitle("Help & Troubleshooting")
        help_dialog.setText(help_text)
        help_dialog.setStandardButtons(QMessageBox.Ok)
        help_dialog.exec()
    
    def change_theme(self, theme: str):
        """Change application theme with optimized performance and visual feedback"""
        if self.style_manager.is_applying:
            self.logger.warning("Theme switch already in progress")
            return

        # Immediate feedback
        self.status_label.setText(f"Switching to {theme} theme...")

        # Update config
        self.config.theme = theme

        # CRITICAL FIX: Set theme on QApplication instance for chart widgets to access
        app = QApplication.instance()
        if app:
            app.current_theme = theme

        # CRITICAL FIX: Force refresh to clear cached stylesheets with old hardcoded colors
        self.logger.info(f"Forcing theme refresh to clear cache for {theme}")
        self.style_manager.apply_theme(theme, force_refresh=True)

        # Use optimized theme switching with visual feedback
        def on_theme_complete():
            self.status_label.setText(f"Theme changed to {theme}")
            self.logger.info(f"Theme successfully changed to {theme}")

        # Configure Plotly theme
        self.configure_plotly_theme(theme)

        # Propagate theme changes to dashboard components
        QTimer.singleShot(200, lambda: self.propagate_theme_changes(theme))

        # Update config after successful switch
        QTimer.singleShot(100, on_theme_complete)

    def propagate_theme_changes(self, theme: str):
        """Propagate theme changes to dashboard components"""
        try:
            # Update dashboard components that have theme support
            if hasattr(self, 'dashboard_widget') and self.dashboard_widget:
                # Update the main dashboard widget itself
                if hasattr(self.dashboard_widget, 'update_theme'):
                    self.dashboard_widget.update_theme(theme)
                    self.logger.debug(f"Applied theme {theme} to main dashboard widget")

                # CRITICAL FIX: Update expense analytics dashboard
                if hasattr(self.dashboard_widget, 'expense_analytics_dashboard'):
                    if hasattr(self.dashboard_widget.expense_analytics_dashboard, 'update_theme'):
                        self.dashboard_widget.expense_analytics_dashboard.update_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to expense analytics dashboard")
                    elif hasattr(self.dashboard_widget.expense_analytics_dashboard, 'set_theme'):
                        self.dashboard_widget.expense_analytics_dashboard.set_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to expense analytics dashboard (legacy)")
                # Check if dashboard has income analytics (original)
                if hasattr(self.dashboard_widget, 'income_analytics_dashboard'):
                    if hasattr(self.dashboard_widget.income_analytics_dashboard, 'update_theme'):
                        self.dashboard_widget.income_analytics_dashboard.update_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to income analytics dashboard")
                    elif hasattr(self.dashboard_widget.income_analytics_dashboard, 'set_theme'):
                        self.dashboard_widget.income_analytics_dashboard.set_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to income analytics dashboard (legacy)")

                # Check if dashboard has income analytics duplicate
                if hasattr(self.dashboard_widget, 'income_analytics_dashboard_duplicate'):
                    if hasattr(self.dashboard_widget.income_analytics_dashboard_duplicate, 'update_theme'):
                        self.dashboard_widget.income_analytics_dashboard_duplicate.update_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to income analytics dashboard duplicate")
                    elif hasattr(self.dashboard_widget.income_analytics_dashboard_duplicate, 'set_theme'):
                        self.dashboard_widget.income_analytics_dashboard_duplicate.set_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to income analytics dashboard duplicate (legacy)")

                # Check if dashboard has advanced analytics
                if hasattr(self.dashboard_widget, 'income_analytics_dashboard') and \
                   hasattr(self.dashboard_widget.income_analytics_dashboard, 'advanced_analytics'):
                    self.dashboard_widget.income_analytics_dashboard.advanced_analytics.set_theme(theme)
                    self.logger.debug(f"Applied theme {theme} to advanced analytics")

                # Check if duplicate dashboard has advanced analytics
                if hasattr(self.dashboard_widget, 'income_analytics_dashboard_duplicate') and \
                   hasattr(self.dashboard_widget.income_analytics_dashboard_duplicate, 'advanced_analytics'):
                    self.dashboard_widget.income_analytics_dashboard_duplicate.advanced_analytics.set_theme(theme)
                    self.logger.debug(f"Applied theme {theme} to duplicate advanced analytics")

                # CRITICAL FIX: Update expense advanced analytics
                if hasattr(self.dashboard_widget, 'advanced_analytics'):
                    if hasattr(self.dashboard_widget.advanced_analytics, 'set_theme'):
                        self.dashboard_widget.advanced_analytics.set_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to expense advanced analytics")
                    elif hasattr(self.dashboard_widget.advanced_analytics, 'update_theme'):
                        self.dashboard_widget.advanced_analytics.update_theme(theme)
                        self.logger.debug(f"Applied theme {theme} to expense advanced analytics (update_theme)")

            # Update individual module widgets
            if hasattr(self, 'module_widgets'):
                for module_name, widget in self.module_widgets.items():
                    if widget is not None and hasattr(widget, 'update_theme'):
                        try:
                            widget.update_theme(theme)
                            self.logger.debug(f"Applied theme {theme} to {module_name} module")
                        except Exception as e:
                            self.logger.warning(f"Failed to apply theme to {module_name} module: {e}")

            self.logger.info(f"Theme propagation completed for {theme}")

        except Exception as e:
            self.logger.error(f"Error propagating theme changes: {e}")
            import traceback
            self.logger.error(f"Theme propagation error traceback: {traceback.format_exc()}")
    
    def new_entry(self):
        """Create new entry in current module"""
        # This will be implemented when modules are added
        self.status_label.setText("New entry functionality coming soon...")
    
    def import_data(self):
        """Import data from file"""
        # This will be implemented later
        self.status_label.setText("Import functionality coming soon...")
    
    def export_data(self):
        """Export data to file"""
        # This will be implemented later
        self.status_label.setText("Export functionality coming soon...")
    
    def create_backup(self):
        """Create data backup"""
        if self.data_manager.backup_data():
            QMessageBox.information(self, "Backup", "Backup created successfully!")
            self.status_label.setText("Backup created successfully")
        else:
            QMessageBox.warning(self, "Backup", "Failed to create backup!")
    
    def show_global_search(self):
        """Show global search dialog"""
        try:
            search_dialog = GlobalSearchDialog(self.data_manager, self)
            search_dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening global search: {e}")
            self.show_error("Failed to open global search dialog")

    def show_settings(self):
        """Show settings dialog"""
        try:
            from .settings_dialog import SettingsDialog

            settings_dialog = SettingsDialog(self.config, self.data_manager, self)

            # Pass sync engine to settings dialog if available
            if hasattr(self, 'sync_engine') and self.sync_engine:
                settings_dialog.sync_engine = self.sync_engine

            settings_dialog.settings_changed.connect(self.on_settings_changed)

            if settings_dialog.exec() == QDialog.Accepted:
                self.status_label.setText("Settings saved successfully")

        except Exception as e:
            self.logger.error(f"Error opening settings dialog: {e}")
            self.show_error("Failed to open settings dialog")

    def on_settings_changed(self):
        """Handle settings changes"""
        try:
            # Reload config
            self.config = AppConfig.load_from_file()

            # Apply theme changes if needed (force refresh to clear cache)
            self.style_manager.apply_theme(self.config.theme, force_refresh=True)

            # Propagate theme changes to dashboard components
            self.propagate_theme_changes(self.config.theme)

            # Update other components as needed
            self.status_label.setText("Settings applied successfully")

        except Exception as e:
            self.logger.error(f"Error applying settings: {e}")
            self.show_error("Failed to apply settings changes")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         f"{self.config.app_name} v{self.config.app_version}\n\n"
                         "A comprehensive personal finance management application\n"
                         "built with PySide6.")
    
    def auto_save(self):
        """Perform auto-save"""
        # Auto-save is handled by the data manager
        self.status_label.setText("Auto-saved")
    
    def save_window_state(self):
        """Save window state"""
        if self.config.remember_window_state:
            self.settings_manager.save_window_geometry(self.saveGeometry())
            self.settings_manager.save_window_state(self.saveState())
    
    def restore_window_state(self):
        """Restore window state"""
        if self.config.remember_window_state:
            geometry = self.settings_manager.load_window_geometry()
            if geometry:
                self.restoreGeometry(geometry)
            
            state = self.settings_manager.load_window_state()
            if state:
                self.restoreState(state)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window state
        self.save_window_state()

        # Save configuration
        self.config.save_to_file()

        # Cleanup theme resources
        if hasattr(self, 'style_manager'):
            self.style_manager.cleanup()
        if hasattr(self, 'theme_switch_manager'):
            self.theme_switch_manager.cleanup()

        # Accept the close event
        event.accept()

    def setup_update_system(self):
        """Initialize the update system"""
        try:
            from ..core.update_manager import update_manager

            self.update_manager = update_manager

            # Set current version
            self.update_manager.set_current_version(getattr(self.config, 'app_version', '1.0.0'))

            # Connect update signals
            self.update_manager.update_available.connect(self.on_update_available)
            self.update_manager.update_check_completed.connect(self.on_update_check_completed)
            self.update_manager.update_failed.connect(self.on_update_failed)

            self.logger.info("Update system initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize update system: {e}")
            self.update_manager = None

    def check_for_updates(self, silent: bool = False):
        """Check for updates manually"""
        if not self.update_manager:
            if not silent:
                QMessageBox.warning(self, "Update System", "Update system is not available.")
            return

        self.logger.info("Manual update check requested")
        self.status_label.setText("Checking for updates...")

        # Use the new update manager
        self.update_manager.check_for_updates(show_no_updates=not silent)

    def on_update_available(self, version_info):
        """Handle update available notification"""
        self.logger.info(f"Update available: {version_info.version}")
        self.status_label.setText(f"Update available: v{version_info.version}")

    def on_update_check_completed(self, success: bool, message: str):
        """Handle update check completion"""
        if success:
            self.logger.info(f"Update check completed: {message}")
        else:
            self.logger.error(f"Update check failed: {message}")

        # Update status
        self.status_label.setText(message)

    def on_update_failed(self, stage: str, error_message: str):
        """Handle update failure"""
        self.logger.error(f"Update failed at {stage}: {error_message}")
        self.status_label.setText(f"Update failed: {error_message}")

        QMessageBox.warning(
            self, "Update Failed",
            f"Update failed during {stage}:\n\n{error_message}"
        )

    def start_update_download(self, version_info: dict):
        """Start downloading an update"""
        if not self.update_manager:
            return

        self.logger.info(f"Starting download for version {version_info.get('version', 'Unknown')}")

        # Show progress dialog
        self.update_progress_dialog = UpdateProgressDialog(self)
        self.update_progress_dialog.cancel_requested.connect(self.cancel_update_download)
        self.update_progress_dialog.show()

        # Start download
        self.update_manager.download_update(version_info)

    def on_download_progress(self, bytes_downloaded: int, total_bytes: int, percentage: int):
        """Handle download progress updates"""
        if self.update_progress_dialog:
            size_mb = bytes_downloaded / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)

            status = f"Downloading update... ({size_mb:.1f} / {total_mb:.1f} MB)"
            detail = f"{percentage}% complete"

            self.update_progress_dialog.update_progress(percentage, status, detail)

    def on_download_completed(self, file_path: str):
        """Handle download completion"""
        self.logger.info(f"Download completed: {file_path}")

        if self.update_progress_dialog:
            self.update_progress_dialog.update_progress(100, "Download complete", "Preparing installation...")

        # Ask user if they want to install now
        reply = QMessageBox.question(
            self, "Install Update",
            "Update downloaded successfully!\n\nWould you like to install it now?\n\n"
            "Note: The application will close during installation.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.install_update(file_path)
        else:
            if self.update_progress_dialog:
                self.update_progress_dialog.accept()
            self.status_label.setText("Update ready to install")

    def on_download_failed(self, error_msg: str):
        """Handle download failure"""
        self.logger.error(f"Download failed: {error_msg}")

        if self.update_progress_dialog:
            self.update_progress_dialog.reject()

        QMessageBox.critical(self, "Download Failed",
                           f"Failed to download update:\n\n{error_msg}")
        self.status_label.setText("Update download failed")

    def install_update(self, installer_path: str):
        """Install an update"""
        if not self.update_manager:
            return

        self.logger.info(f"Installing update from {installer_path}")

        if self.update_progress_dialog:
            self.update_progress_dialog.update_progress(0, "Installing update...",
                                                      "Please wait while the update is installed")

        # Start installation
        self.update_manager.install_update(installer_path)

    def on_installation_completed(self):
        """Handle installation completion"""
        self.logger.info("Update installation completed")

        if self.update_progress_dialog:
            self.update_progress_dialog.accept()

        # Show completion message and offer to restart
        reply = QMessageBox.information(
            self, "Update Complete",
            "Update installed successfully!\n\n"
            "The application needs to be restarted to use the new version.\n\n"
            "Would you like to restart now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.restart_application()
        else:
            self.status_label.setText("Update installed - restart required")

    def on_installation_failed(self, error_msg: str):
        """Handle installation failure"""
        self.logger.error(f"Installation failed: {error_msg}")

        if self.update_progress_dialog:
            self.update_progress_dialog.reject()

        QMessageBox.critical(self, "Installation Failed",
                           f"Failed to install update:\n\n{error_msg}")
        self.status_label.setText("Update installation failed")

    def cancel_update_download(self):
        """Cancel update download"""
        if self.update_manager and hasattr(self.update_manager, 'downloader'):
            if self.update_manager.downloader:
                self.update_manager.downloader.stop()
        self.status_label.setText("Update download cancelled")

    def skip_update_version(self, version: str):
        """Skip a specific update version"""
        if self.update_manager:
            self.update_manager.skip_version(version)
        self.status_label.setText(f"Version {version} will be skipped")

    def remind_update_later(self):
        """Handle remind later for updates"""
        self.status_label.setText("Update reminder postponed")

    def show_update_settings(self):
        """Show update settings dialog"""
        if not self.update_manager:
            QMessageBox.warning(self, "Update System", "Update system is not available.")
            return

        # Show the main settings dialog with the updates tab
        self.show_settings()

    def on_update_settings_changed(self, new_settings: dict):
        """Handle update settings changes"""
        if self.update_manager:
            self.status_label.setText("Update settings saved")

    def show_update_history(self):
        """Show update history and backup management"""
        if not self.update_manager:
            QMessageBox.warning(self, "Update System", "Update system is not available.")
            return

        # Show information about available backups
        backups = self.update_manager.installer.get_available_backups()
        if not backups:
            QMessageBox.information(
                self, "Update History",
                "No backup history available."
            )
            return

        # Create a simple dialog showing backup information
        backup_info = "Available Backups:\n\n"
        for backup in backups:
            backup_info += f"• Version {backup.version} - {backup.created_at}\n"
            backup_info += f"  Size: {backup.backup_size / (1024*1024):.1f} MB\n\n"

        QMessageBox.information(self, "Update History", backup_info)

    def restore_from_backup(self, backup_path: str):
        """Restore application from backup"""
        if not self.update_manager:
            return

        reply = QMessageBox.question(
            self, "Restore from Backup",
            f"Are you sure you want to restore from this backup?\n\n"
            f"This will replace the current application with the backup version.\n\n"
            f"Backup: {backup_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.update_manager.restore_from_backup(backup_path):
                QMessageBox.information(self, "Restore Complete",
                                      "Application restored from backup successfully!\n\n"
                                      "Please restart the application.")
                self.status_label.setText("Restored from backup - restart required")
            else:
                QMessageBox.critical(self, "Restore Failed",
                                   "Failed to restore from backup.")
                self.status_label.setText("Backup restore failed")

    def restart_application(self):
        """Restart the application"""
        import sys
        import subprocess

        try:
            # Close the current application
            self.close()

            # Start a new instance
            subprocess.Popen([sys.executable] + sys.argv)

            # Exit the current process
            sys.exit(0)

        except Exception as e:
            self.logger.error(f"Failed to restart application: {e}")
            QMessageBox.critical(self, "Restart Failed",
                               f"Failed to restart application:\n\n{e}\n\n"
                               "Please restart manually.")
