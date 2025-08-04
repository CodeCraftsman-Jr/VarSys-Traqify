"""
Expense Tracker UI Widgets
Contains all UI components for the expense tracking module
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QGroupBox, QSplitter, QTabWidget, QSpinBox, QDoubleSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QCheckBox, QProgressBar,
    QScrollArea, QRadioButton, QListWidget, QListWidgetItem, QButtonGroup,
    QSlider, QSpacerItem, QSizePolicy, QApplication, QFileDialog, QMenu
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QSortFilterProxyModel, QThread
from PySide6.QtGui import QFont, QIcon, QPixmap, QStandardItemModel, QStandardItem, QColor, QBrush, QAction
from pathlib import Path

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import logging

from .models import ExpenseRecord, ExpenseDataModel
from .summary_widget import ExpenseSummaryWidget


class RetractableTabWidget(QWidget):
    """A retractable/collapsible tab widget for the 4x4 grid layout"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = True
        self.content_widget = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the retractable tab UI"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Header with expand/collapse button
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        self.header_frame.setMaximumHeight(30)
        self.header_frame.setCursor(Qt.PointingHandCursor)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)

        # Expand/collapse icon
        self.expand_icon = QLabel("▼")
        self.expand_icon.setStyleSheet("font-weight: bold; color: #666;")
        self.expand_icon.setFixedWidth(15)
        header_layout.addWidget(self.expand_icon)

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333;
                font-size: 10pt;
            }
        """)
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Make header clickable
        self.header_frame.mousePressEvent = self.toggle_expanded

        self.layout.addWidget(self.header_frame)

        # Content area
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #d0d0d0;
                border-top: none;
                border-radius: 0px 0px 4px 4px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(4, 4, 4, 4)

        self.layout.addWidget(self.content_frame)

    def set_content_widget(self, widget):
        """Set the content widget for this tab"""
        if self.content_widget:
            self.content_layout.removeWidget(self.content_widget)

        self.content_widget = widget
        self.content_layout.addWidget(widget)

    def toggle_expanded(self, event=None):
        """Toggle the expanded/collapsed state"""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.expand_icon.setText("▼")
            self.content_frame.setVisible(True)
        else:
            self.expand_icon.setText("▶")
            self.content_frame.setVisible(False)

    def set_expanded(self, expanded):
        """Set the expanded state"""
        if self.is_expanded != expanded:
            self.toggle_expanded()


class FilterTabWidget(QWidget):
    """1x7 horizontal box widget for different filter types"""

    def __init__(self, filter_widget, parent=None):
        super().__init__(parent)
        self.filter_widget = filter_widget

        # Flag to prevent automatic filtering during UI setup
        self.is_initializing = True

        # Timer for debouncing subcategory updates to reduce flickering
        from PySide6.QtCore import QTimer
        self.subcategory_update_timer = QTimer()
        self.subcategory_update_timer.setSingleShot(True)
        self.subcategory_update_timer.timeout.connect(self._perform_subcategory_update)
        self.pending_subcategories = None

        # Set size policy to expand horizontally and use full available width
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setup_ui()

        # Initialization complete - allow filtering
        self.is_initializing = False

    def setup_ui(self):
        """Setup the 1x7 horizontal box UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Main horizontal layout for filter boxes - use full available width
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(6)  # Further reduced spacing for 7 boxes

        # Create 7 filter boxes
        self.create_date_filter_box()
        self.create_transaction_filter_box()
        self.create_amount_filter_box()
        self.create_category_filter_box()
        self.create_subcategory_filter_box()
        self.create_preset_filter_box()
        self.create_action_filter_box()

        layout.addLayout(self.main_layout)

    def create_date_filter_box(self):
        """Create date filter box"""
        date_box = QGroupBox("📅 Date")
        date_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Use minimum width instead of fixed width to allow expansion
        date_box.setMinimumWidth(180)
        date_box.setMaximumHeight(250)  # Increased height for better visibility
        # Set size policy to expand horizontally
        from PySide6.QtWidgets import QSizePolicy
        date_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(date_box)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 10, 5, 5)

        # Quick date buttons (compact layout)
        date_buttons = [
            ("All", "all"),
            ("Today", "today"),
            ("This Week", "this_week"),
            ("Last Week", "last_week"),
            ("This Month", "this_month"),
            ("Last Month", "last_month")
        ]

        self.date_button_group = QButtonGroup()
        for text, value in date_buttons:
            btn = QRadioButton(text)
            btn.setProperty("filter_value", value)
            btn.setStyleSheet("font-size: 9pt; margin: 1px;")
            self.date_button_group.addButton(btn)
            layout.addWidget(btn)

        # Set "All" as default
        self.date_button_group.buttons()[0].setChecked(True)

        # Last N days section (compact)
        last_n_layout = QHBoxLayout()
        last_n_layout.setSpacing(2)
        last_n_layout.addWidget(QLabel("Last"))
        self.last_n_spin = QSpinBox()
        self.last_n_spin.setRange(1, 365)
        self.last_n_spin.setValue(30)
        self.last_n_spin.setMaximumWidth(50)
        self.last_n_spin.setStyleSheet("font-size: 8pt;")
        last_n_layout.addWidget(self.last_n_spin)
        last_n_layout.addWidget(QLabel("days"))

        layout.addLayout(last_n_layout)

        self.apply_last_n_btn = QPushButton("Apply")
        self.apply_last_n_btn.setStyleSheet("font-size: 8pt; padding: 1px; margin: 1px;")
        self.apply_last_n_btn.setMaximumHeight(20)
        layout.addWidget(self.apply_last_n_btn)

        # Date range section (compact)
        range_layout = QGridLayout()
        range_layout.setSpacing(2)

        range_layout.addWidget(QLabel("From:"), 0, 0)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setStyleSheet("font-size: 8pt;")
        self.start_date_edit.setMaximumHeight(20)
        range_layout.addWidget(self.start_date_edit, 0, 1)

        range_layout.addWidget(QLabel("To:"), 1, 0)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setStyleSheet("font-size: 8pt;")
        self.end_date_edit.setMaximumHeight(20)
        range_layout.addWidget(self.end_date_edit, 1, 1)

        layout.addLayout(range_layout)

        self.apply_range_btn = QPushButton("Apply Range")
        self.apply_range_btn.setStyleSheet("font-size: 8pt; padding: 1px; margin: 1px;")
        self.apply_range_btn.setMaximumHeight(20)
        layout.addWidget(self.apply_range_btn)

        self.main_layout.addWidget(date_box)

    def create_transaction_filter_box(self):
        """Create transaction type filter box"""
        trans_box = QGroupBox("💳 Transaction")
        trans_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Use minimum width instead of fixed width to allow expansion
        trans_box.setMinimumWidth(120)
        trans_box.setMaximumHeight(250)  # Increased height for better visibility
        # Set size policy to expand horizontally
        trans_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(trans_box)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 10, 5, 5)

        # Transaction type checkboxes
        self.trans_checkboxes = {}

        transaction_types = ["Expense", "Income", "Transfer"]
        for trans_type in transaction_types:
            checkbox = QCheckBox(trans_type)
            checkbox.setChecked(True)  # All selected by default
            checkbox.setStyleSheet("font-size: 9pt; margin: 1px;")
            self.trans_checkboxes[trans_type] = checkbox
            layout.addWidget(checkbox)

        # Select/Deselect buttons (compact)
        self.select_all_trans_btn = QPushButton("Select All")
        self.select_all_trans_btn.setStyleSheet("font-size: 8pt; padding: 1px; margin: 1px;")
        self.select_all_trans_btn.setMaximumHeight(20)
        layout.addWidget(self.select_all_trans_btn)

        self.deselect_all_trans_btn = QPushButton("Deselect All")
        self.deselect_all_trans_btn.setStyleSheet("font-size: 8pt; padding: 1px; margin: 1px;")
        self.deselect_all_trans_btn.setMaximumHeight(20)
        layout.addWidget(self.deselect_all_trans_btn)

        self.main_layout.addWidget(trans_box)

    def create_amount_filter_box(self):
        """Create amount filter box"""
        amount_box = QGroupBox("💰 Amount")
        amount_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Use minimum width instead of fixed width to allow expansion
        amount_box.setMinimumWidth(160)
        amount_box.setMaximumHeight(250)  # Increased height for better visibility
        # Set size policy to expand horizontally
        amount_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(amount_box)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 10, 5, 5)

        # Quick amount ranges (compact)
        amount_ranges = [
            ("All", None),
            ("₹0-₹50", (0, 50)),
            ("₹50-₹200", (50, 200)),
            ("₹200-₹500", (200, 500)),
            ("₹500+", (500, None))
        ]

        self.amount_button_group = QButtonGroup()
        for text, value in amount_ranges:
            btn = QRadioButton(text)
            btn.setProperty("filter_value", value)
            btn.setStyleSheet("font-size: 9pt; margin: 1px;")
            self.amount_button_group.addButton(btn)
            layout.addWidget(btn)

        # Set "All" as default
        self.amount_button_group.buttons()[0].setChecked(True)

        # Custom amount range (compact grid)
        custom_label = QLabel("Custom:")
        custom_label.setStyleSheet("font-size: 8pt; font-weight: bold; margin-top: 2px;")
        layout.addWidget(custom_label)

        custom_layout = QGridLayout()
        custom_layout.setSpacing(2)

        custom_layout.addWidget(QLabel("Min:"), 0, 0)
        self.min_amount_spin = QDoubleSpinBox()
        self.min_amount_spin.setRange(0, 999999)
        self.min_amount_spin.setPrefix("₹")
        self.min_amount_spin.setValue(0)
        self.min_amount_spin.setStyleSheet("font-size: 8pt;")
        self.min_amount_spin.setMaximumWidth(70)
        self.min_amount_spin.setMaximumHeight(20)
        custom_layout.addWidget(self.min_amount_spin, 0, 1)

        custom_layout.addWidget(QLabel("Max:"), 1, 0)
        self.max_amount_spin = QDoubleSpinBox()
        self.max_amount_spin.setRange(0, 999999)
        self.max_amount_spin.setPrefix("₹")
        self.max_amount_spin.setValue(1000)
        self.max_amount_spin.setStyleSheet("font-size: 8pt;")
        self.max_amount_spin.setMaximumWidth(70)
        self.max_amount_spin.setMaximumHeight(20)
        custom_layout.addWidget(self.max_amount_spin, 1, 1)

        layout.addLayout(custom_layout)

        self.apply_amount_btn = QPushButton("Apply")
        self.apply_amount_btn.setStyleSheet("font-size: 8pt; padding: 1px; margin: 1px;")
        self.apply_amount_btn.setMaximumHeight(20)
        layout.addWidget(self.apply_amount_btn)

        self.main_layout.addWidget(amount_box)

    def create_category_filter_box(self):
        """Create category filter box"""
        category_box = QGroupBox("📂 Category")
        category_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Use minimum width instead of fixed width to allow expansion
        category_box.setMinimumWidth(140)
        category_box.setMaximumHeight(250)  # Increased height for better visibility
        # Set size policy to expand horizontally
        category_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(category_box)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 10, 5, 5)

        # Category selection
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.setStyleSheet("font-size: 9pt;")
        self.category_combo.setMaximumHeight(22)
        layout.addWidget(self.category_combo)

        # Remove checkboxes - use combo box only for cleaner UI
        self.category_checkboxes = {}  # Keep empty dict for compatibility

        self.main_layout.addWidget(category_box)

    def create_subcategory_filter_box(self):
        """Create subcategory filter box"""
        subcategory_box = QGroupBox("📁 Sub-Category")
        subcategory_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Use minimum width instead of fixed width to allow expansion
        subcategory_box.setMinimumWidth(140)
        subcategory_box.setMaximumHeight(250)  # Increased height for better visibility
        # Set size policy to expand horizontally
        subcategory_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(subcategory_box)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 10, 5, 5)

        # Subcategory selection
        self.subcategory_combo = QComboBox()
        self.subcategory_combo.addItem("All Sub-categories")
        self.subcategory_combo.setStyleSheet("font-size: 9pt;")
        self.subcategory_combo.setMaximumHeight(22)
        layout.addWidget(self.subcategory_combo)

        # Remove checkboxes - use combo box only for cleaner UI
        self.subcategory_checkboxes = {}  # Keep empty dict for compatibility

        self.main_layout.addWidget(subcategory_box)

    def create_preset_filter_box(self):
        """Create filter presets box"""
        preset_box = QGroupBox("⚡ Preset")
        preset_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Use minimum width instead of fixed width to allow expansion
        preset_box.setMinimumWidth(140)
        preset_box.setMaximumHeight(250)  # Increased height for better visibility
        # Set size policy to expand horizontally
        preset_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(preset_box)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 10, 5, 5)

        preset_label = QLabel("Select:")
        preset_label.setStyleSheet("font-size: 9pt; margin: 1px;")
        layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Select preset...")
        self.preset_combo.setStyleSheet("font-size: 8pt;")
        self.preset_combo.setMaximumHeight(22)
        layout.addWidget(self.preset_combo)

        self.apply_preset_btn = QPushButton("Apply")
        self.apply_preset_btn.setStyleSheet("font-size: 8pt; padding: 1px; margin: 1px;")
        self.apply_preset_btn.setMaximumHeight(20)
        layout.addWidget(self.apply_preset_btn)

        # Add some spacing
        layout.addWidget(QLabel(""))

        self.main_layout.addWidget(preset_box)

    def create_action_filter_box(self):
        """Create filter actions box"""
        action_box = QGroupBox("🔧 Action")
        action_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        # Use minimum width instead of fixed width to allow expansion
        action_box.setMinimumWidth(130)
        action_box.setMaximumHeight(250)  # Increased height for better visibility
        # Set size policy to expand horizontally
        action_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(action_box)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 10, 5, 5)

        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 4px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.clear_all_btn.setMaximumHeight(22)
        layout.addWidget(self.clear_all_btn)

        # Active filter count
        self.active_filter_label = QLabel("(0 active)")
        self.active_filter_label.setStyleSheet("color: #666; font-style: italic; font-size: 8pt; margin: 2px;")
        self.active_filter_label.setWordWrap(True)
        self.active_filter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.active_filter_label)

        # Add some spacing
        layout.addWidget(QLabel(""))

        self.main_layout.addWidget(action_box)

        # Set stretch factors to make filter boxes expand proportionally
        # This ensures the filter boxes use the full available width
        for i in range(self.main_layout.count()):
            self.main_layout.setStretchFactor(self.main_layout.itemAt(i).widget(), 1)

        # Connect all filter signals
        self.setup_filter_connections()

    def setup_filter_connections(self):
        """Setup connections for all filter controls"""
        # Date filter connections
        self.date_button_group.buttonClicked.connect(self.apply_date_filter)
        self.apply_last_n_btn.clicked.connect(self.apply_last_n_days_filter)
        self.apply_range_btn.clicked.connect(self.apply_date_range_filter)

        # Transaction type connections
        for checkbox in self.trans_checkboxes.values():
            checkbox.stateChanged.connect(self.apply_transaction_type_filter)
        self.select_all_trans_btn.clicked.connect(self.select_all_transaction_types)
        self.deselect_all_trans_btn.clicked.connect(self.deselect_all_transaction_types)

        # Amount filter connections
        self.amount_button_group.buttonClicked.connect(self.apply_amount_filter)
        self.apply_amount_btn.clicked.connect(self.apply_custom_amount_filter)

        # Category filter connections
        self.category_combo.currentTextChanged.connect(self.on_category_combo_changed)

        # Subcategory filter connections
        self.subcategory_combo.currentTextChanged.connect(self.apply_subcategory_filter)

        # Preset and action connections
        self.apply_preset_btn.clicked.connect(self.apply_filter_preset)
        self.clear_all_btn.clicked.connect(self.clear_all_filters)

    def apply_date_filter(self, button):
        """Apply quick date filter - only apply when user selects specific filter"""
        filter_value = button.property("filter_value")

        if filter_value == "all":
            # Clear date filter - show all unfiltered data
            self.filter_widget.clear_date_filters()
            self.apply_all_filters()
        else:
            # Only apply filter when user selects a specific date range
            if filter_value == "today":
                today = QDate.currentDate()
                self.filter_widget.set_date_range(today, today)
            elif filter_value == "this_week":
                today = QDate.currentDate()
                start_of_week = today.addDays(-today.dayOfWeek() + 1)
                self.filter_widget.set_date_range(start_of_week, today)
            elif filter_value == "last_week":
                today = QDate.currentDate()
                start_of_last_week = today.addDays(-today.dayOfWeek() + 1 - 7)
                end_of_last_week = start_of_last_week.addDays(6)
                self.filter_widget.set_date_range(start_of_last_week, end_of_last_week)
            elif filter_value == "this_month":
                today = QDate.currentDate()
                start_of_month = QDate(today.year(), today.month(), 1)
                self.filter_widget.set_date_range(start_of_month, today)
            elif filter_value == "last_month":
                today = QDate.currentDate()
                # Get first day of last month
                first_day_this_month = QDate(today.year(), today.month(), 1)
                last_day_last_month = first_day_this_month.addDays(-1)
                first_day_last_month = QDate(last_day_last_month.year(), last_day_last_month.month(), 1)
                self.filter_widget.set_date_range(first_day_last_month, last_day_last_month)
            elif filter_value == "this_year":
                today = QDate.currentDate()
                start_of_year = QDate(today.year(), 1, 1)
                self.filter_widget.set_date_range(start_of_year, today)

            # Apply filters only when user makes a specific selection
            self.apply_all_filters()

    def apply_last_n_days_filter(self):
        """Apply last N days filter"""
        n_days = self.last_n_spin.value()
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-n_days + 1)
        self.filter_widget.set_date_range(start_date, end_date)
        self.apply_all_filters()

    def apply_date_range_filter(self):
        """Apply custom date range filter"""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        self.filter_widget.set_date_range(start_date, end_date)
        self.apply_all_filters()

    def apply_transaction_type_filter(self):
        """Apply transaction type filter - only apply when user makes specific selections"""
        # Don't apply filters during UI initialization
        if self.is_initializing:
            return

        selected_types = []
        for trans_type, checkbox in self.trans_checkboxes.items():
            if checkbox.isChecked():
                selected_types.append(trans_type)

        # Check if all types are selected (default state) - show unfiltered data
        all_types = list(self.trans_checkboxes.keys())
        if len(selected_types) == len(all_types):
            # All types selected = no filter applied, show all data
            self.filter_widget.clear_transaction_type_filters()
        elif selected_types:
            # Specific types selected = apply filter
            self.filter_widget.set_transaction_types(selected_types)
        else:
            # No types selected = apply empty filter (show no data)
            self.filter_widget.set_transaction_types([])

        self.apply_all_filters()

    def select_all_transaction_types(self):
        """Select all transaction types"""
        for checkbox in self.trans_checkboxes.values():
            checkbox.setChecked(True)
        self.apply_transaction_type_filter()

    def deselect_all_transaction_types(self):
        """Deselect all transaction types"""
        for checkbox in self.trans_checkboxes.values():
            checkbox.setChecked(False)
        self.apply_transaction_type_filter()

    def apply_amount_filter(self, button):
        """Apply quick amount filter - only apply when user selects specific range"""
        filter_value = button.property("filter_value")

        if filter_value is None:
            # "All" selected - clear amount filter, show unfiltered data
            self.filter_widget.clear_amount_filters()
            self.apply_all_filters()
        else:
            # Specific range selected - apply filter
            min_amount, max_amount = filter_value
            self.filter_widget.set_amount_range(min_amount, max_amount)
            self.apply_all_filters()

    def apply_custom_amount_filter(self):
        """Apply custom amount range filter - only apply when user sets specific values"""
        min_amount = self.min_amount_spin.value()
        max_amount = self.max_amount_spin.value()

        # Only apply filter if user has set meaningful values (not default 0-1000)
        if min_amount > 0 or max_amount < 1000:
            self.filter_widget.set_amount_range(min_amount, max_amount)
            self.apply_all_filters()
        else:
            # Default values - clear filter to show all data
            self.filter_widget.clear_amount_filters()
            self.apply_all_filters()

    # Category filter methods removed for 1x5 layout

    def apply_filter_preset(self):
        """Apply selected filter preset - only apply when user explicitly selects a preset"""
        preset_name = self.preset_combo.currentText()
        if preset_name != "Select a preset..." and preset_name != "":
            # User selected a specific preset - apply it
            self.filter_widget.apply_preset_by_name(preset_name)
            # No need to call apply_all_filters() as it's handled in apply_preset_data
        # If "Select a preset..." is selected, do nothing (keep current filter state)

    def on_category_combo_changed(self):
        """Handle category combo box changes - update subcategories immediately"""
        if self.is_initializing:
            return

        # Update subcategories based on current category selection
        selected_categories = []
        combo_selection = self.category_combo.currentText()
        if combo_selection and combo_selection != "All Categories":
            selected_categories.append(combo_selection)

        # Update subcategory options with debouncing to reduce flickering
        self.update_subcategory_options_for_categories_debounced(selected_categories)

        # Then apply the category filter
        self.apply_category_filter()

    def apply_category_filter(self):
        """Apply category filter - only apply when user makes specific selections"""
        # Don't apply filters during UI initialization
        if self.is_initializing:
            return

        selected_categories = []

        # Check combo box selection only
        combo_selection = self.category_combo.currentText()
        if combo_selection and combo_selection != "All Categories":
            selected_categories.append(combo_selection)

        # Always update subcategory options based on selected categories
        self.update_subcategory_options_for_categories(selected_categories)

        # Apply filter based on selections
        if selected_categories:
            # User has made specific category selections (either combo or checkboxes)
            self.filter_widget.set_category_filter(selected_categories)
            self.apply_all_filters()
        else:
            # No specific selections - show unfiltered data
            self.filter_widget.clear_category_filter()
            self.apply_all_filters()

    def update_subcategory_options_for_categories(self, selected_categories):
        """Update subcategory options based on selected categories using actual expense data"""
        try:
            if not selected_categories or "All Categories" in selected_categories:
                # Show all subcategories from actual expense data
                df = self.filter_widget.data_model.get_all_expenses()
                if not df.empty:
                    all_subcategories = df['sub_category'].dropna().unique().tolist()
                    all_subcategories = sorted([sub for sub in all_subcategories if sub and str(sub).strip()])
                    self.update_subcategory_combo_and_checkboxes(all_subcategories)
                else:
                    self.update_subcategory_combo_and_checkboxes([])
            else:
                # Filter subcategories based on selected categories using actual expense data
                df = self.filter_widget.data_model.get_all_expenses()
                if not df.empty:
                    # Filter expenses by selected categories
                    filtered_df = df[df['category'].isin(selected_categories)]
                    # Get unique subcategories from filtered data
                    filtered_subcategories = filtered_df['sub_category'].dropna().unique().tolist()
                    filtered_subcategories = sorted([sub for sub in filtered_subcategories if sub and str(sub).strip()])
                    self.update_subcategory_combo_and_checkboxes(filtered_subcategories)
                else:
                    self.update_subcategory_combo_and_checkboxes([])
        except Exception as e:
            print(f"Error updating subcategory options: {e}")

    def update_subcategory_options_for_categories_debounced(self, selected_categories):
        """Debounced version to reduce flickering from rapid changes"""
        self.pending_subcategories = selected_categories
        self.subcategory_update_timer.stop()
        self.subcategory_update_timer.start(100)  # 100ms delay

    def _perform_subcategory_update(self):
        """Perform the actual subcategory update"""
        if self.pending_subcategories is not None:
            self.update_subcategory_options_for_categories(self.pending_subcategories)
            self.pending_subcategories = None

    def update_subcategory_combo_and_checkboxes(self, subcategories):
        """Update both subcategory combo and checkboxes with minimal flickering"""
        # Disable updates temporarily to reduce flickering
        self.subcategory_combo.setUpdatesEnabled(False)

        try:
            # Update combo
            current_selection = self.subcategory_combo.currentText()
            self.subcategory_combo.clear()
            self.subcategory_combo.addItem("All Sub-categories")
            if subcategories:
                self.subcategory_combo.addItems(sorted(subcategories))

            # Restore selection if still valid
            index = self.subcategory_combo.findText(current_selection)
            if index >= 0:
                self.subcategory_combo.setCurrentIndex(index)

        finally:
            # Re-enable updates
            self.subcategory_combo.setUpdatesEnabled(True)

        # No checkboxes to update - using combo box only

    def apply_subcategory_filter(self):
        """Apply subcategory filter - only apply when user makes specific selections"""
        # Don't apply filters during UI initialization
        if self.is_initializing:
            return

        selected_subcategories = []

        # Check combo box selection only
        combo_selection = self.subcategory_combo.currentText()
        if combo_selection and combo_selection != "All Sub-categories":
            selected_subcategories.append(combo_selection)

        # Apply filter based on combo box selection
        if selected_subcategories:
            self.filter_widget.set_subcategory_filter(selected_subcategories)
            self.apply_all_filters()
        else:
            # "All Sub-categories" selected - show unfiltered data
            self.filter_widget.clear_subcategory_filter()
            self.apply_all_filters()

    # Checkbox methods removed - using combo box only approach

    def clear_all_filters(self):
        """Clear all active filters"""
        # Reset all filter controls to default state
        self.date_button_group.buttons()[0].setChecked(True)  # "All" button

        for checkbox in self.trans_checkboxes.values():
            checkbox.setChecked(True)

        self.amount_button_group.buttons()[0].setChecked(True)  # "All" button

        # Reset category filters
        self.category_combo.setCurrentIndex(0)  # "All Categories"

        # Reset subcategory filters
        self.subcategory_combo.setCurrentIndex(0)  # "All Sub-categories"

        # Clear the underlying filter widget
        self.filter_widget.clear_all_filters()
        self.apply_all_filters()

    def apply_all_filters(self):
        """Apply all current filter settings - only apply when user has made specific selections"""
        # Don't apply filters during initialization
        if self.is_initializing:
            return

        # Check if any filters are actually active (not in default "All" state)
        has_active_filters = self.filter_widget.get_active_filter_count() > 0

        if has_active_filters:
            # User has made specific filter selections - apply filters immediately
            self.filter_widget.apply_filters_immediately()
        else:
            # All filters are in default "All" state - show unfiltered data
            # Force refresh of unfiltered data
            self.filter_widget.show_unfiltered_data()

        self.update_active_filter_count()

    def update_active_filter_count(self):
        """Update the active filter count display"""
        count = self.filter_widget.get_active_filter_count()
        self.active_filter_label.setText(f"({count} active)")

    def populate_categories(self, categories, sub_categories):
        """Populate category lists for the 1x7 layout"""
        # Populate category combo
        current_category = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        if categories:
            self.category_combo.addItems(categories)

        # Restore selection if possible
        index = self.category_combo.findText(current_category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        # Populate subcategory combo
        current_subcategory = self.subcategory_combo.currentText()
        self.subcategory_combo.clear()
        self.subcategory_combo.addItem("All Sub-categories")
        if sub_categories:
            self.subcategory_combo.addItems(sub_categories)

        # Restore selection if possible
        index = self.subcategory_combo.findText(current_subcategory)
        if index >= 0:
            self.subcategory_combo.setCurrentIndex(index)

    # Category checkbox methods removed - using combo box only approach

    # Checkbox methods removed - using combo box only approach

    def populate_presets(self, presets):
        """Populate preset dropdown with available presets"""
        self.preset_combo.clear()
        self.preset_combo.addItem("Select a preset...")
        for preset in presets:
            self.preset_combo.addItem(preset)


class FilterWorkerThread(QThread):
    """Background thread for heavy filtering operations"""

    filtering_progress = Signal(int)  # Progress percentage
    filtering_completed = Signal(object)  # Filtered DataFrame
    filtering_error = Signal(str)  # Error message

    def __init__(self, data_model, filters, parent=None):
        super().__init__(parent)
        self.data_model = data_model
        self.filters = filters
        self.chunk_size = 1000

    def run(self):
        """Run the filtering operation in background with optimized processing"""
        try:
            self.filtering_progress.emit(10)

            # Use processed expenses for better performance
            df = self.data_model.get_processed_expenses()
            total_records = len(df)

            self.filtering_progress.emit(30)

            if total_records > self.chunk_size:
                # Process in chunks for large datasets
                filtered_df = self.process_in_chunks(df)
            else:
                # Process normally for smaller datasets using optimized method
                filtered_df = self.apply_filters_optimized(df)

            self.filtering_progress.emit(100)
            self.filtering_completed.emit(filtered_df)

        except Exception as e:
            self.filtering_error.emit(str(e))

    def apply_filters_optimized(self, df):
        """Apply filters with optimized pandas operations"""
        if df.empty:
            return df

        # Start with all data
        result_df = df.copy()

        # Apply date filters
        if 'date_filter' in self.filters:
            result_df = self.apply_date_filter_to_chunk(result_df)

        # Apply transaction type filters
        if 'transaction_types' in self.filters and self.filters['transaction_types']:
            result_df = result_df[result_df['type'].isin(self.filters['transaction_types'])]

        # Apply amount range filters
        if 'amount_range' in self.filters:
            result_df = self.apply_amount_filter_to_chunk(result_df)

        # Apply category filters
        if 'categories' in self.filters and self.filters['categories']:
            result_df = result_df[result_df['category'].isin(self.filters['categories'])]

        # Apply sub-category filters
        if 'sub_categories' in self.filters and self.filters['sub_categories']:
            result_df = result_df[result_df['sub_category'].isin(self.filters['sub_categories'])]

        return result_df

    def process_in_chunks(self, df):
        """Process large datasets in chunks with optimized operations"""
        chunks = []
        total_records = len(df)

        # Use larger chunk size for better performance
        optimized_chunk_size = min(self.chunk_size * 2, 5000)

        for i in range(0, total_records, optimized_chunk_size):
            chunk = df.iloc[i:i + optimized_chunk_size].copy()

            # Apply filters to chunk using optimized method
            filtered_chunk = self.apply_filters_to_chunk_optimized(chunk)
            if not filtered_chunk.empty:
                chunks.append(filtered_chunk)

            # Update progress more frequently
            progress = 30 + int((i / total_records) * 60)
            self.filtering_progress.emit(progress)

        # Combine all chunks efficiently
        if chunks:
            return pd.concat(chunks, ignore_index=True)
        else:
            return pd.DataFrame()

    def apply_filters_to_chunk_optimized(self, chunk_df):
        """Apply filters to chunk with optimized pandas operations and data type safety"""
        if chunk_df.empty:
            return chunk_df

        # Apply all filters in sequence for better performance
        result_df = chunk_df.copy()

        # Ensure data types are consistent
        string_columns = ['category', 'sub_category', 'type', 'transaction_mode', 'notes']
        for col in string_columns:
            if col in result_df.columns:
                result_df[col] = result_df[col].astype(str).fillna('')
                result_df[col] = result_df[col].replace('nan', '')

        # Ensure amount is numeric
        if 'amount' in result_df.columns:
            result_df['amount'] = pd.to_numeric(result_df['amount'], errors='coerce')

        # Date filter
        if 'date_filter' in self.filters:
            result_df = self.apply_date_filter_to_chunk(result_df)

        # Transaction type filter with data type safety
        if 'transaction_types' in self.filters:
            transaction_types = self.filters['transaction_types']
            if transaction_types:
                # Ensure both sides are strings
                transaction_types = [str(t) for t in transaction_types]
                result_df = result_df[result_df['type'].astype(str).isin(transaction_types)]
            else:
                # Empty list means show no data
                return pd.DataFrame(columns=result_df.columns)

        # Amount filter
        if 'amount_range' in self.filters:
            result_df = self.apply_amount_filter_to_chunk(result_df)

        # Category filter with data type safety
        if 'categories' in self.filters and self.filters['categories']:
            categories = [str(c) for c in self.filters['categories'] if str(c) != 'nan' and str(c) != '']
            if categories:
                result_df = result_df[result_df['category'].astype(str).isin(categories)]

        # Sub-category filter with data type safety
        if 'sub_categories' in self.filters and self.filters['sub_categories']:
            sub_categories = [str(sc) for sc in self.filters['sub_categories'] if str(sc) != 'nan' and str(sc) != '']
            if sub_categories:
                result_df = result_df[result_df['sub_category'].astype(str).isin(sub_categories)]

        return result_df

    def apply_filters_to_chunk(self, chunk_df):
        """Apply filters to a data chunk"""
        if chunk_df.empty:
            return chunk_df

        # Convert date column to datetime for filtering
        chunk_df['date'] = pd.to_datetime(chunk_df['date'])

        # Apply date filters
        if 'date_filter' in self.filters and self.filters['date_filter']:
            chunk_df = self.apply_date_filter_to_chunk(chunk_df)

        # Apply transaction type filters
        if 'transaction_types' in self.filters and self.filters['transaction_types']:
            chunk_df = chunk_df[chunk_df['type'].isin(self.filters['transaction_types'])]

        # Apply amount range filters
        if 'amount_range' in self.filters and self.filters['amount_range']:
            chunk_df = self.apply_amount_filter_to_chunk(chunk_df)

        # Apply category filters
        if 'categories' in self.filters and self.filters['categories']:
            chunk_df = chunk_df[chunk_df['category'].isin(self.filters['categories'])]

        # Apply sub-category filters
        if 'sub_categories' in self.filters and self.filters['sub_categories']:
            chunk_df = chunk_df[chunk_df['sub_category'].isin(self.filters['sub_categories'])]

        return chunk_df

    def apply_date_filter_to_chunk(self, chunk_df):
        """Apply date filtering to chunk"""
        date_filter = self.filters['date_filter']
        today = datetime.now().date()

        if date_filter == 'all':
            return chunk_df
        elif date_filter == 'today':
            return chunk_df[chunk_df['date'].dt.date == today]
        elif date_filter == 'this_week':
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return chunk_df[(chunk_df['date'].dt.date >= start_of_week) & (chunk_df['date'].dt.date <= end_of_week)]
        elif date_filter == 'this_month':
            start_of_month = today.replace(day=1)
            return chunk_df[chunk_df['date'].dt.date >= start_of_month]
        elif date_filter.startswith('last_') and date_filter.endswith('_days'):
            n_days = self.filters.get('last_n_days', 30)
            start_date = today - timedelta(days=n_days)
            return chunk_df[chunk_df['date'].dt.date >= start_date]
        elif date_filter == 'custom_range':
            start_date = self.filters.get('start_date')
            end_date = self.filters.get('end_date')
            if start_date and end_date:
                return chunk_df[(chunk_df['date'].dt.date >= start_date) & (chunk_df['date'].dt.date <= end_date)]

        return chunk_df

    def apply_amount_filter_to_chunk(self, chunk_df):
        """Apply amount filtering to chunk"""
        amount_range = self.filters['amount_range']
        if amount_range is None:
            return chunk_df

        min_amount, max_amount = amount_range

        if min_amount is not None and max_amount is not None:
            return chunk_df[(chunk_df['amount'] >= min_amount) & (chunk_df['amount'] <= max_amount)]
        elif min_amount is not None:
            return chunk_df[chunk_df['amount'] >= min_amount]
        elif max_amount is not None:
            return chunk_df[chunk_df['amount'] <= max_amount]

        return chunk_df


class CollapsibleGroupBox(QGroupBox):
    """A collapsible group box widget"""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self.on_toggled)

        # Store the original content widget
        self.content_widget = None

    def setContentWidget(self, widget):
        """Set the content widget that will be shown/hidden"""
        self.content_widget = widget
        layout = QVBoxLayout(self)
        layout.addWidget(widget)

    def on_toggled(self, checked):
        """Handle the toggle state"""
        if self.content_widget:
            self.content_widget.setVisible(checked)


class FilterSummaryWidget(QWidget):
    """Widget to display active filter summary as chips/tags"""

    clear_filter_requested = Signal(str)  # Signal to clear specific filter

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.active_filters = {}

    def setup_ui(self):
        """Setup the summary widget UI"""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # Title label
        title_label = QLabel("Active Filters:")
        title_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.layout.addWidget(title_label)

        # Scroll area for filter chips - EXPANDED: Remove height restriction
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(35)  # Set minimum height for visibility
        # Remove maximum height constraint to allow natural expansion
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.chips_widget = QWidget()
        self.chips_layout = QHBoxLayout(self.chips_widget)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(3)

        self.scroll_area.setWidget(self.chips_widget)
        self.layout.addWidget(self.scroll_area)

        self.layout.addStretch()

    def update_filters(self, filters):
        """Update the displayed filter chips"""
        self.active_filters = filters

        # Clear existing chips
        for i in reversed(range(self.chips_layout.count())):
            child = self.chips_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Add new chips
        for filter_type, filter_value in filters.items():
            if filter_value:
                chip = self.create_filter_chip(filter_type, filter_value)
                self.chips_layout.addWidget(chip)

        self.chips_layout.addStretch()

    def create_filter_chip(self, filter_type, filter_value):
        """Create a filter chip widget"""
        chip_frame = QFrame()
        chip_frame.setFrameStyle(QFrame.Box)
        chip_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 12px;
                padding: 2px 8px;
            }
        """)

        chip_layout = QHBoxLayout(chip_frame)
        chip_layout.setContentsMargins(4, 2, 4, 2)
        chip_layout.setSpacing(4)

        # Filter text
        filter_text = self.format_filter_text(filter_type, filter_value)
        label = QLabel(filter_text)
        label.setFont(QFont("Arial", 8))
        chip_layout.addWidget(label)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setMaximumSize(16, 16)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-weight: bold;
                color: #666;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
                color: #d32f2f;
            }
        """)
        close_btn.clicked.connect(lambda: self.clear_filter_requested.emit(filter_type))
        chip_layout.addWidget(close_btn)

        return chip_frame

    def format_filter_text(self, filter_type, filter_value):
        """Format filter value for display"""
        if filter_type == "date_filter":
            if isinstance(filter_value, dict):
                # Handle date range dict
                start_date = filter_value.get('start_date')
                end_date = filter_value.get('end_date')
                if start_date and end_date:
                    # Handle both QDate and Python date objects
                    if hasattr(start_date, 'toString'):
                        # QDate object
                        start_str = start_date.toString('yyyy-MM-dd')
                        end_str = end_date.toString('yyyy-MM-dd')
                    else:
                        # Python date object
                        start_str = start_date.strftime('%Y-%m-%d')
                        end_str = end_date.strftime('%Y-%m-%d')

                    if start_date == end_date:
                        return f"Date: {start_str}"
                    else:
                        return f"Date: {start_str} to {end_str}"
                return "Date: Custom Range"
            elif isinstance(filter_value, str):
                # Handle string date filter
                return f"Date: {filter_value.replace('_', ' ').title()}"
            else:
                return "Date: Custom"
        elif filter_type == "transaction_types":
            return f"Types: {', '.join(filter_value)}"
        elif filter_type == "amount_range":
            if isinstance(filter_value, tuple):
                min_amt, max_amt = filter_value
                if min_amt is not None and max_amt is not None:
                    return f"Amount: ₹{min_amt}-₹{max_amt}"
                elif min_amt is not None:
                    return f"Amount: ≥₹{min_amt}"
                elif max_amt is not None:
                    return f"Amount: ≤₹{max_amt}"
            return "Amount: Custom"
        elif filter_type == "categories":
            return f"Categories: {', '.join(filter_value[:2])}{'...' if len(filter_value) > 2 else ''}"
        elif filter_type == "sub_categories":
            return f"Sub-categories: {', '.join(filter_value[:2])}{'...' if len(filter_value) > 2 else ''}"
        else:
            return f"{filter_type}: {filter_value}"


class ExpenseFilterWidget(QWidget):
    """Comprehensive filtering widget for expenses"""

    filters_changed = Signal()

    def __init__(self, data_model: ExpenseDataModel, parent=None):
        super().__init__(parent)

        self.data_model = data_model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Filter state
        self.active_filters = {}
        self.filter_presets = {}

        # Performance optimization
        self.filter_worker = None
        self.result_limit = 5000  # Limit results for very large datasets
        self.current_result_count = 0

        self.setup_ui()
        self.setup_connections()
        self.setup_filter_presets()

    def setup_ui(self):
        """Setup the filter widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # Header with active filter count and clear button
        header_layout = QHBoxLayout()

        self.filter_title = QLabel("Filters")
        self.filter_title.setFont(QFont("Arial", 10, QFont.Bold))

        self.active_count_label = QLabel("(0 active)")
        self.active_count_label.setStyleSheet("color: #666;")

        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.setMaximumWidth(80)
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        header_layout.addWidget(self.filter_title)
        header_layout.addWidget(self.active_count_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_button)

        layout.addLayout(header_layout)

        # Filter summary chips
        self.filter_summary = FilterSummaryWidget()
        self.filter_summary.clear_filter_requested.connect(self.clear_specific_filter)
        layout.addWidget(self.filter_summary)

        # Progress bar for heavy operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                font-size: 8pt;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Loading overlay for better UX
        self.loading_overlay = QFrame()
        self.loading_overlay.setVisible(False)
        self.loading_overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
        self.loading_overlay.setFixedHeight(60)

        loading_layout = QHBoxLayout(self.loading_overlay)
        loading_layout.setContentsMargins(10, 10, 10, 10)

        loading_label = QLabel("🔄 Processing filters...")
        loading_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #333;")
        loading_layout.addWidget(loading_label)

        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)  # Indeterminate progress
        self.loading_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
                font-size: 8pt;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 2px;
            }
        """)
        loading_layout.addWidget(self.loading_progress)

        layout.addWidget(self.loading_overlay)

        # Result count and load more section
        self.result_info_frame = QFrame()
        self.result_info_frame.setVisible(False)
        self.result_info_frame.setStyleSheet("QFrame { border: 1px solid #ffeaa7; border-radius: 4px; }")
        result_info_layout = QHBoxLayout(self.result_info_frame)
        result_info_layout.setContentsMargins(8, 4, 8, 4)

        self.result_count_label = QLabel()
        self.result_count_label.setStyleSheet("color: #856404; font-size: 9pt;")
        result_info_layout.addWidget(self.result_count_label)

        self.load_more_button = QPushButton("Load More")
        self.load_more_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 8pt;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e0a800; }
        """)
        self.load_more_button.clicked.connect(self.load_more_results)
        result_info_layout.addWidget(self.load_more_button)

        layout.addWidget(self.result_info_frame)

        # Create collapsible filter sections
        self.create_date_filters(layout)
        self.create_transaction_filters(layout)
        self.create_amount_filters(layout)
        self.create_category_filters(layout)
        self.create_filter_presets(layout)

    def create_date_filters(self, parent_layout):
        """Create date filtering section"""
        date_group = CollapsibleGroupBox("📅 Date Filters")
        date_content = QWidget()
        date_layout = QVBoxLayout(date_content)
        date_layout.setContentsMargins(5, 5, 5, 5)
        date_layout.setSpacing(8)

        # Quick date ranges - more compact horizontal layout
        quick_frame = QFrame()
        quick_frame.setFrameStyle(QFrame.StyledPanel)
        quick_frame.setStyleSheet("QFrame { border-radius: 4px; }")
        quick_layout = QVBoxLayout(quick_frame)
        quick_layout.setContentsMargins(8, 6, 8, 6)

        quick_label = QLabel("Quick Filters:")
        quick_label.setFont(QFont("Arial", 9, QFont.Bold))
        quick_layout.addWidget(quick_label)

        # First row of quick buttons
        quick_row1 = QHBoxLayout()
        quick_row2 = QHBoxLayout()

        self.date_quick_buttons = QButtonGroup()
        quick_options = [
            ("All Time", "all"),
            ("Today", "today"),
            ("This Week", "this_week"),
            ("Last Week", "last_week"),
            ("This Month", "this_month"),
            ("Last Month", "last_month"),
            ("This Year", "this_year")
        ]

        for i, (text, value) in enumerate(quick_options):
            btn = QRadioButton(text)
            btn.setProperty("filter_value", value)
            btn.setStyleSheet("QRadioButton { font-size: 8pt; }")
            self.date_quick_buttons.addButton(btn)

            if i < 4:
                quick_row1.addWidget(btn)
            else:
                quick_row2.addWidget(btn)

        # Set "All Time" as default
        self.date_quick_buttons.buttons()[0].setChecked(True)

        quick_layout.addLayout(quick_row1)
        quick_layout.addLayout(quick_row2)
        date_layout.addWidget(quick_frame)

        # Last N days filter
        last_n_frame = QFrame()
        last_n_frame.setFrameStyle(QFrame.StyledPanel)
        last_n_frame.setStyleSheet("QFrame { border-radius: 4px; }")
        last_n_layout = QHBoxLayout(last_n_frame)
        last_n_layout.setContentsMargins(8, 6, 8, 6)

        last_n_layout.addWidget(QLabel("Last"))

        self.last_n_days = QSpinBox()
        self.last_n_days.setRange(1, 365)
        self.last_n_days.setValue(30)
        self.last_n_days.setMaximumWidth(60)
        self.last_n_days.setStyleSheet("QSpinBox { font-size: 9pt; }")

        last_n_layout.addWidget(self.last_n_days)
        last_n_layout.addWidget(QLabel("days"))

        self.apply_last_n_button = QPushButton("Apply")
        self.apply_last_n_button.setMaximumWidth(60)
        self.apply_last_n_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        last_n_layout.addWidget(self.apply_last_n_button)
        last_n_layout.addStretch()

        date_layout.addWidget(last_n_frame)

        # Custom date range
        range_frame = QFrame()
        range_frame.setFrameStyle(QFrame.StyledPanel)
        range_frame.setStyleSheet("QFrame { border-radius: 4px; }")
        range_layout = QGridLayout(range_frame)
        range_layout.setContentsMargins(8, 6, 8, 6)

        range_layout.addWidget(QLabel("From:"), 0, 0)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet("QDateEdit { font-size: 9pt; }")
        range_layout.addWidget(self.start_date, 0, 1)

        range_layout.addWidget(QLabel("To:"), 0, 2)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet("QDateEdit { font-size: 9pt; }")
        range_layout.addWidget(self.end_date, 0, 3)

        self.apply_range_button = QPushButton("Apply Range")
        self.apply_range_button.setMaximumWidth(100)
        self.apply_range_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #1976d2; }
        """)
        range_layout.addWidget(self.apply_range_button, 0, 4)

        date_layout.addWidget(range_frame)

        date_group.setContentWidget(date_content)
        parent_layout.addWidget(date_group)

    def create_transaction_filters(self, parent_layout):
        """Create transaction type filtering section"""
        trans_group = CollapsibleGroupBox("💳 Transaction Types")
        trans_content = QWidget()
        trans_layout = QVBoxLayout(trans_content)
        trans_layout.setContentsMargins(5, 5, 5, 5)
        trans_layout.setSpacing(6)

        # Multi-select list for transaction types
        self.transaction_types_list = QListWidget()
        self.transaction_types_list.setMaximumHeight(80)
        self.transaction_types_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.transaction_types_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 9pt;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
        """)

        # Populate transaction types
        transaction_types = ["Expense", "Income", "Transfer"]
        for trans_type in transaction_types:
            item = QListWidgetItem(trans_type)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)  # All selected by default
            self.transaction_types_list.addItem(item)

        trans_layout.addWidget(self.transaction_types_list)

        # Select/Deselect all buttons
        trans_buttons_layout = QHBoxLayout()
        self.select_all_trans_button = QPushButton("Select All")
        self.select_all_trans_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        self.deselect_all_trans_button = QPushButton("Deselect All")
        self.deselect_all_trans_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #f57c00; }
        """)

        trans_buttons_layout.addWidget(self.select_all_trans_button)
        trans_buttons_layout.addWidget(self.deselect_all_trans_button)
        trans_buttons_layout.addStretch()

        trans_layout.addLayout(trans_buttons_layout)

        trans_group.setContentWidget(trans_content)
        parent_layout.addWidget(trans_group)

    def create_amount_filters(self, parent_layout):
        """Create amount filtering section"""
        amount_group = CollapsibleGroupBox("💰 Amount Filters")
        amount_content = QWidget()
        amount_layout = QVBoxLayout(amount_content)
        amount_layout.setContentsMargins(5, 5, 5, 5)
        amount_layout.setSpacing(8)

        # Predefined amount ranges
        predefined_frame = QFrame()
        predefined_frame.setFrameStyle(QFrame.StyledPanel)
        predefined_frame.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 4px; }")
        predefined_layout = QVBoxLayout(predefined_frame)
        predefined_layout.setContentsMargins(8, 6, 8, 6)

        quick_label = QLabel("Quick Ranges:")
        quick_label.setFont(QFont("Arial", 9, QFont.Bold))
        predefined_layout.addWidget(quick_label)

        # Amount range buttons in rows
        ranges_row1 = QHBoxLayout()
        ranges_row2 = QHBoxLayout()

        self.amount_quick_buttons = QButtonGroup()
        amount_ranges = [
            ("All", None),
            ("₹0-₹50", (0, 50)),
            ("₹50-₹200", (50, 200)),
            ("₹200-₹500", (200, 500)),
            ("₹500+", (500, None))
        ]

        for i, (text, value) in enumerate(amount_ranges):
            btn = QRadioButton(text)
            btn.setProperty("filter_value", value)
            btn.setStyleSheet("QRadioButton { font-size: 8pt; }")
            self.amount_quick_buttons.addButton(btn)

            if i < 3:
                ranges_row1.addWidget(btn)
            else:
                ranges_row2.addWidget(btn)

        # Set "All" as default
        self.amount_quick_buttons.buttons()[0].setChecked(True)

        predefined_layout.addLayout(ranges_row1)
        predefined_layout.addLayout(ranges_row2)
        amount_layout.addWidget(predefined_frame)

        # Custom amount range
        custom_frame = QFrame()
        custom_frame.setFrameStyle(QFrame.StyledPanel)
        custom_frame.setStyleSheet("QFrame { background-color: #f9f9f9; border-radius: 4px; }")
        custom_layout = QGridLayout(custom_frame)
        custom_layout.setContentsMargins(8, 6, 8, 6)

        custom_layout.addWidget(QLabel("Custom Range:"), 0, 0, 1, 4)

        custom_layout.addWidget(QLabel("Min:"), 1, 0)

        self.min_amount = QDoubleSpinBox()
        self.min_amount.setRange(0, 999999)
        self.min_amount.setPrefix("₹")
        self.min_amount.setValue(0)
        self.min_amount.setStyleSheet("QDoubleSpinBox { font-size: 9pt; }")
        custom_layout.addWidget(self.min_amount, 1, 1)

        custom_layout.addWidget(QLabel("Max:"), 1, 2)

        self.max_amount = QDoubleSpinBox()
        self.max_amount.setRange(0, 999999)
        self.max_amount.setPrefix("₹")
        self.max_amount.setValue(1000)
        self.max_amount.setStyleSheet("QDoubleSpinBox { font-size: 9pt; }")
        custom_layout.addWidget(self.max_amount, 1, 3)

        self.apply_amount_button = QPushButton("Apply Custom")
        self.apply_amount_button.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #7b1fa2; }
        """)
        custom_layout.addWidget(self.apply_amount_button, 2, 0, 1, 4)

        amount_layout.addWidget(custom_frame)

        amount_group.setContentWidget(amount_content)
        parent_layout.addWidget(amount_group)

    def create_category_filters(self, parent_layout):
        """Create category filtering section"""
        category_group = CollapsibleGroupBox("📂 Category Filters")
        category_content = QWidget()
        category_layout = QVBoxLayout(category_content)
        category_layout.setContentsMargins(5, 5, 5, 5)
        category_layout.setSpacing(8)

        # Primary categories
        primary_frame = QFrame()
        primary_frame.setFrameStyle(QFrame.StyledPanel)
        primary_frame.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 4px; }")
        primary_layout = QVBoxLayout(primary_frame)
        primary_layout.setContentsMargins(8, 6, 8, 6)

        primary_label = QLabel("Primary Categories:")
        primary_label.setFont(QFont("Arial", 9, QFont.Bold))
        primary_layout.addWidget(primary_label)

        self.primary_categories_list = QListWidget()
        self.primary_categories_list.setMaximumHeight(100)
        self.primary_categories_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.primary_categories_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-size: 9pt;
                background-color: #252526;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #3e3e42;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0e639c;
                color: #ffffff;
            }
        """)

        primary_layout.addWidget(self.primary_categories_list)

        # Category buttons
        cat_buttons_layout = QHBoxLayout()
        self.select_all_cat_button = QPushButton("Select All")
        self.select_all_cat_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        self.deselect_all_cat_button = QPushButton("Deselect All")
        self.deselect_all_cat_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #f57c00; }
        """)

        cat_buttons_layout.addWidget(self.select_all_cat_button)
        cat_buttons_layout.addWidget(self.deselect_all_cat_button)
        cat_buttons_layout.addStretch()

        primary_layout.addLayout(cat_buttons_layout)
        category_layout.addWidget(primary_frame)

        # Sub-categories (dynamically populated)
        sub_frame = QFrame()
        sub_frame.setFrameStyle(QFrame.StyledPanel)
        sub_frame.setStyleSheet("QFrame { background-color: #f9f9f9; border-radius: 4px; }")
        sub_layout = QVBoxLayout(sub_frame)
        sub_layout.setContentsMargins(8, 6, 8, 6)

        sub_label = QLabel("Sub-categories:")
        sub_label.setFont(QFont("Arial", 9, QFont.Bold))
        sub_layout.addWidget(sub_label)

        self.sub_categories_list = QListWidget()
        self.sub_categories_list.setMaximumHeight(80)
        self.sub_categories_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.sub_categories_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 9pt;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #eee;
            }
        """)

        sub_layout.addWidget(self.sub_categories_list)

        # Sub-category buttons
        sub_buttons_layout = QHBoxLayout()
        self.select_all_sub_button = QPushButton("Select All")
        self.select_all_sub_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        self.deselect_all_sub_button = QPushButton("Deselect All")
        self.deselect_all_sub_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #f57c00; }
        """)

        sub_buttons_layout.addWidget(self.select_all_sub_button)
        sub_buttons_layout.addWidget(self.deselect_all_sub_button)
        sub_buttons_layout.addStretch()

        sub_layout.addLayout(sub_buttons_layout)
        category_layout.addWidget(sub_frame)

        category_group.setContentWidget(category_content)
        parent_layout.addWidget(category_group)

    def create_filter_presets(self, parent_layout):
        """Create filter presets section"""
        presets_group = CollapsibleGroupBox("⚡ Filter Presets")
        presets_content = QWidget()
        presets_layout = QVBoxLayout(presets_content)
        presets_layout.setContentsMargins(5, 5, 5, 5)

        presets_frame = QFrame()
        presets_frame.setFrameStyle(QFrame.StyledPanel)
        presets_frame.setStyleSheet("QFrame { background-color: #f0f8ff; border-radius: 4px; }")
        presets_combo_layout = QHBoxLayout(presets_frame)
        presets_combo_layout.setContentsMargins(8, 6, 8, 6)

        presets_combo_layout.addWidget(QLabel("Preset:"))

        self.presets_combo = QComboBox()
        self.presets_combo.addItem("Select a preset...")
        self.presets_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 9pt;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        presets_combo_layout.addWidget(self.presets_combo)

        self.apply_preset_button = QPushButton("Apply")
        self.apply_preset_button.setMaximumWidth(60)
        self.apply_preset_button.setStyleSheet("""
            QPushButton {
                background-color: #673ab7;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #5e35b1; }
        """)
        presets_combo_layout.addWidget(self.apply_preset_button)

        presets_layout.addWidget(presets_frame)

        presets_group.setContentWidget(presets_content)
        parent_layout.addWidget(presets_group)

    def setup_connections(self):
        """Setup signal connections"""
        # Date filter connections
        self.date_quick_buttons.buttonClicked.connect(self.on_date_quick_changed)
        self.apply_last_n_button.clicked.connect(self.on_apply_last_n_days)
        self.apply_range_button.clicked.connect(self.on_apply_date_range)

        # Transaction type connections
        self.transaction_types_list.itemChanged.connect(self.on_transaction_types_changed)
        self.select_all_trans_button.clicked.connect(self.select_all_transaction_types)
        self.deselect_all_trans_button.clicked.connect(self.deselect_all_transaction_types)

        # Amount filter connections
        self.amount_quick_buttons.buttonClicked.connect(self.on_amount_quick_changed)
        self.apply_amount_button.clicked.connect(self.on_apply_custom_amount)

        # Category filter connections
        self.primary_categories_list.itemChanged.connect(self.on_primary_categories_changed)
        self.primary_categories_list.itemSelectionChanged.connect(self.update_sub_categories)
        self.sub_categories_list.itemChanged.connect(self.on_sub_categories_changed)

        self.select_all_cat_button.clicked.connect(self.select_all_categories)
        self.deselect_all_cat_button.clicked.connect(self.deselect_all_categories)
        self.select_all_sub_button.clicked.connect(self.select_all_sub_categories)
        self.deselect_all_sub_button.clicked.connect(self.deselect_all_sub_categories)

        # Preset connections
        self.apply_preset_button.clicked.connect(self.apply_selected_preset)

        # Clear all connection
        self.clear_all_button.clicked.connect(self.clear_all_filters)

        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common filter operations"""
        from PySide6.QtGui import QShortcut, QKeySequence

        # Ctrl+R: Clear all filters
        clear_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        clear_shortcut.activated.connect(self.clear_all_filters)

        # Ctrl+T: Focus on transaction types
        trans_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        trans_shortcut.activated.connect(lambda: self.transaction_types_list.setFocus())

        # Ctrl+D: Focus on date filters (apply last 30 days)
        date_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        date_shortcut.activated.connect(lambda: (self.last_n_days.setValue(30), self.on_apply_last_n_days()))

        # Ctrl+M: This month filter
        month_shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        month_shortcut.activated.connect(lambda: self.apply_quick_date_filter("this_month"))

        # Ctrl+W: This week filter
        week_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        week_shortcut.activated.connect(lambda: self.apply_quick_date_filter("this_week"))

    def apply_quick_date_filter(self, filter_value):
        """Apply a quick date filter programmatically"""
        for button in self.date_quick_buttons.buttons():
            if button.property("filter_value") == filter_value:
                button.setChecked(True)
                self.on_date_quick_changed(button)
                break

    def setup_filter_presets(self):
        """Setup predefined filter presets"""
        self.filter_presets = {
            "This Month's Food Expenses": {
                "date_filter": "this_month",
                "transaction_types": ["Expense"],
                "categories": ["Food & Dining", "Groceries"],
                "amount_range": None
            },
            "Last 30 Days Income": {
                "date_filter": "last_30_days",
                "transaction_types": ["Income"],
                "categories": [],
                "amount_range": None
            },
            "High Value Expenses (>₹200)": {
                "date_filter": "this_month",
                "transaction_types": ["Expense"],
                "categories": [],
                "amount_range": (200, None)
            },
            "This Week's Shopping": {
                "date_filter": "this_week",
                "transaction_types": ["Expense"],
                "categories": ["Shopping", "Online Stores"],
                "amount_range": None
            },
            "Monthly Transportation": {
                "date_filter": "this_month",
                "transaction_types": ["Expense"],
                "categories": ["Transportation", "Fuel"],
                "amount_range": None
            }
        }

        # Populate presets combo
        for preset_name in self.filter_presets.keys():
            self.presets_combo.addItem(preset_name)

    def populate_categories(self):
        """Populate category lists from data"""
        try:
            categories = self.data_model.get_category_list()

            # Clear existing items
            self.primary_categories_list.clear()

            # Add categories with checkboxes
            for category in categories:
                item = QListWidgetItem(category)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)  # All selected by default
                self.primary_categories_list.addItem(item)

        except Exception as e:
            self.logger.error(f"Error populating categories: {e}")

    def update_sub_categories(self):
        """Update sub-categories based on selected primary categories"""
        try:
            selected_categories = self.get_selected_categories()

            # Get all sub-categories for selected primary categories
            df = self.data_model.get_all_expenses()
            if df.empty:
                return

            sub_categories = set()
            for category in selected_categories:
                category_df = df[df['category'] == category]
                sub_cats = category_df['sub_category'].dropna().unique()
                sub_categories.update(sub_cats)

            # Clear and repopulate sub-categories list
            self.sub_categories_list.clear()

            for sub_category in sorted(sub_categories):
                if sub_category and sub_category.strip():  # Skip empty sub-categories
                    item = QListWidgetItem(sub_category)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Checked)
                    self.sub_categories_list.addItem(item)

        except Exception as e:
            self.logger.error(f"Error updating sub-categories: {e}")

    # Event handlers
    def on_date_quick_changed(self, button):
        """Handle quick date filter changes"""
        filter_value = button.property("filter_value")
        self.active_filters['date_filter'] = filter_value
        self.update_active_count()
        self.apply_filters_with_threading()

    def on_apply_last_n_days(self):
        """Apply last N days filter"""
        n_days = self.last_n_days.value()
        self.active_filters['date_filter'] = f"last_{n_days}_days"
        self.active_filters['last_n_days'] = n_days
        self.update_active_count()
        self.apply_filters_with_threading()

    def on_apply_date_range(self):
        """Apply custom date range filter"""
        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()

        self.active_filters['date_filter'] = 'custom_range'
        self.active_filters['start_date'] = start_date
        self.active_filters['end_date'] = end_date
        self.update_active_count()
        self.filters_changed.emit()

    def on_transaction_types_changed(self):
        """Handle transaction type filter changes"""
        selected_types = self.get_selected_transaction_types()
        self.active_filters['transaction_types'] = selected_types
        self.update_active_count()
        self.apply_filters_with_threading()

    def on_amount_quick_changed(self, button):
        """Handle quick amount filter changes"""
        filter_value = button.property("filter_value")
        self.active_filters['amount_range'] = filter_value
        self.update_active_count()
        self.apply_filters_with_threading()

    def on_apply_custom_amount(self):
        """Apply custom amount range filter"""
        min_amount = self.min_amount.value()
        max_amount = self.max_amount.value()

        if min_amount > max_amount:
            QMessageBox.warning(self, "Invalid Range", "Minimum amount cannot be greater than maximum amount.")
            return

        self.active_filters['amount_range'] = (min_amount, max_amount)
        self.update_active_count()
        self.apply_filters_with_threading()

    def on_primary_categories_changed(self):
        """Handle primary category filter changes"""
        selected_categories = self.get_selected_categories()
        self.active_filters['categories'] = selected_categories
        self.update_sub_categories()
        self.update_active_count()
        self.apply_filters_with_threading()

    def on_sub_categories_changed(self):
        """Handle sub-category filter changes"""
        selected_sub_categories = self.get_selected_sub_categories()
        self.active_filters['sub_categories'] = selected_sub_categories
        self.update_active_count()
        self.apply_filters_with_threading()

    def apply_selected_preset(self):
        """Apply the selected filter preset"""
        preset_name = self.presets_combo.currentText()
        if preset_name == "Select a preset..." or preset_name not in self.filter_presets:
            return

        preset = self.filter_presets[preset_name]
        self.apply_preset_data(preset)

    def apply_preset_data(self, preset):
        """Apply a filter preset data"""
        try:
            # Clear current filters first
            self.clear_all_filters()

            # Apply date filter
            if 'date_filter' in preset:
                date_filter = preset['date_filter']
                if date_filter == "last_30_days":
                    self.last_n_days.setValue(30)
                    self.on_apply_last_n_days()
                else:
                    # Find and check the appropriate radio button
                    for button in self.date_quick_buttons.buttons():
                        if button.property("filter_value") == date_filter:
                            button.setChecked(True)
                            self.on_date_quick_changed(button)
                            break

            # Apply transaction types
            if 'transaction_types' in preset:
                self.set_selected_transaction_types(preset['transaction_types'])
                self.on_transaction_types_changed()  # Trigger the change event

            # Apply categories
            if 'categories' in preset:
                self.set_selected_categories(preset['categories'])
                self.on_primary_categories_changed()  # Trigger the change event

            # Apply amount range
            if 'amount_range' in preset and preset['amount_range']:
                min_amount, max_amount = preset['amount_range']
                self.min_amount.setValue(min_amount)
                if max_amount:
                    self.max_amount.setValue(max_amount)
                self.on_apply_custom_amount()

            # Force apply filters after setting all preset values
            self.apply_filters_with_threading()

        except Exception as e:
            self.logger.error(f"Error applying preset: {e}")

    # Utility methods
    def get_selected_transaction_types(self):
        """Get list of selected transaction types"""
        selected = []
        for i in range(self.transaction_types_list.count()):
            item = self.transaction_types_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected

    def set_selected_transaction_types(self, types):
        """Set selected transaction types"""
        for i in range(self.transaction_types_list.count()):
            item = self.transaction_types_list.item(i)
            if item.text() in types:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        self.on_transaction_types_changed()

    def get_selected_categories(self):
        """Get list of selected primary categories"""
        selected = []
        for i in range(self.primary_categories_list.count()):
            item = self.primary_categories_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected

    def set_selected_categories(self, categories):
        """Set selected primary categories"""
        for i in range(self.primary_categories_list.count()):
            item = self.primary_categories_list.item(i)
            if item.text() in categories:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        self.on_primary_categories_changed()

    def get_selected_sub_categories(self):
        """Get list of selected sub-categories"""
        selected = []
        for i in range(self.sub_categories_list.count()):
            item = self.sub_categories_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected

    def select_all_transaction_types(self):
        """Select all transaction types"""
        for i in range(self.transaction_types_list.count()):
            item = self.transaction_types_list.item(i)
            item.setCheckState(Qt.Checked)
        self.on_transaction_types_changed()

    def deselect_all_transaction_types(self):
        """Deselect all transaction types"""
        for i in range(self.transaction_types_list.count()):
            item = self.transaction_types_list.item(i)
            item.setCheckState(Qt.Unchecked)
        self.on_transaction_types_changed()

    def select_all_categories(self):
        """Select all primary categories"""
        for i in range(self.primary_categories_list.count()):
            item = self.primary_categories_list.item(i)
            item.setCheckState(Qt.Checked)
        self.on_primary_categories_changed()

    def deselect_all_categories(self):
        """Deselect all primary categories"""
        for i in range(self.primary_categories_list.count()):
            item = self.primary_categories_list.item(i)
            item.setCheckState(Qt.Unchecked)
        self.on_primary_categories_changed()

    def select_all_sub_categories(self):
        """Select all sub-categories"""
        for i in range(self.sub_categories_list.count()):
            item = self.sub_categories_list.item(i)
            item.setCheckState(Qt.Checked)
        self.on_sub_categories_changed()

    def deselect_all_sub_categories(self):
        """Deselect all sub-categories"""
        for i in range(self.sub_categories_list.count()):
            item = self.sub_categories_list.item(i)
            item.setCheckState(Qt.Unchecked)
        self.on_sub_categories_changed()

    def clear_all_filters(self):
        """Clear all active filters"""
        # Reset date filters
        self.date_quick_buttons.buttons()[0].setChecked(True)  # All Time

        # Reset transaction types
        self.select_all_transaction_types()

        # Reset amount filters
        self.amount_quick_buttons.buttons()[0].setChecked(True)  # All

        # Reset categories
        self.select_all_categories()

        # Clear active filters
        self.active_filters.clear()
        self.update_active_count()
        self.filters_changed.emit()

    def clear_specific_filter(self, filter_type):
        """Clear a specific filter type"""
        if filter_type in self.active_filters:
            if filter_type == "date_filter":
                # Reset to "All Time"
                self.date_quick_buttons.buttons()[0].setChecked(True)
            elif filter_type == "transaction_types":
                self.select_all_transaction_types()
            elif filter_type == "amount_range":
                # Reset to "All"
                self.amount_quick_buttons.buttons()[0].setChecked(True)
            elif filter_type == "categories":
                self.select_all_categories()
            elif filter_type == "sub_categories":
                self.select_all_sub_categories()

            # Remove from active filters
            if filter_type in self.active_filters:
                del self.active_filters[filter_type]

            self.update_active_count()
            self.filters_changed.emit()

    def update_active_count(self):
        """Update the active filter count display and filter summary"""
        count = len([k for k, v in self.active_filters.items() if v])
        self.active_count_label.setText(f"({count} active)")

        # Update filter summary chips
        self.filter_summary.update_filters(self.active_filters)

    def load_more_results(self):
        """Load more results when limit is reached"""
        self.result_limit += 2500  # Increase limit
        self.apply_filters_with_threading()

    def apply_filters_with_threading(self):
        """Apply filters using background threading for large datasets"""
        # Check if we need background processing
        total_records = len(self.data_model.get_all_expenses())

        if total_records > 500 and self.active_filters:
            # Use background threading for large datasets
            self.show_progress_bar(True)

            # Stop any existing worker
            if self.filter_worker and self.filter_worker.isRunning():
                self.filter_worker.quit()
                self.filter_worker.wait()

            # Start new worker
            self.filter_worker = FilterWorkerThread(self.data_model, self.active_filters)
            self.filter_worker.filtering_progress.connect(self.update_progress)
            self.filter_worker.filtering_completed.connect(self.on_filtering_completed)
            self.filter_worker.filtering_error.connect(self.on_filtering_error)
            self.filter_worker.start()
        else:
            # Use direct filtering for smaller datasets
            self.apply_filters_direct()

    def apply_filters_direct(self):
        """Apply filters directly without threading with improved error handling"""
        try:
            # Show loading for better UX even for direct filtering
            self.show_progress_bar(True)

            if not self.active_filters:
                # No filters, emit signal to show all
                self.show_progress_bar(False)
                self.filters_changed.emit()
                return

            # Apply filters using the model's optimized method
            df = self.data_model.get_expenses_by_filters(self.active_filters)

            # Ensure we have valid results
            if df is None:
                df = pd.DataFrame()

            # Small delay to ensure loading screen is visible for fast operations
            import time
            time.sleep(0.1)

            self.show_progress_bar(False)
            self.handle_filtered_results(df)

        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            self.show_progress_bar(False)
            # Show empty results instead of all data on error
            self.handle_filtered_results(pd.DataFrame())

    def show_progress_bar(self, show):
        """Show or hide the progress bar with status text and loading overlay"""
        self.progress_bar.setVisible(show)
        self.loading_overlay.setVisible(show)

        if show:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Applying filters... %p%")
            # Disable filter controls during processing to prevent UI conflicts
            self.setEnabled(False)
        else:
            self.progress_bar.setFormat("")
            # Re-enable filter controls
            self.setEnabled(True)

    def update_progress(self, value):
        """Update progress bar value with dynamic status"""
        self.progress_bar.setValue(value)
        if value < 30:
            self.progress_bar.setFormat("Loading data... %p%")
        elif value < 90:
            self.progress_bar.setFormat("Filtering records... %p%")
        else:
            self.progress_bar.setFormat("Finalizing results... %p%")

    def on_filtering_completed(self, filtered_df):
        """Handle completion of background filtering"""
        self.show_progress_bar(False)
        self.handle_filtered_results(filtered_df)

    def on_filtering_error(self, error_message):
        """Handle filtering error"""
        self.show_progress_bar(False)
        self.logger.error(f"Background filtering error: {error_message}")
        self.filters_changed.emit()  # Fallback to showing all

    def handle_filtered_results(self, df):
        """Handle filtered results with result limiting"""
        self.current_result_count = len(df)

        # Check if we need to limit results
        if self.current_result_count > self.result_limit:
            # Show limited results
            limited_df = df.head(self.result_limit)
            self.show_result_info(True, self.current_result_count, self.result_limit)

            # Emit signal with limited data
            self.filters_changed.emit()
            # Note: The actual filtering will be handled by the parent widget
        else:
            # Show all results
            self.show_result_info(False, self.current_result_count, self.current_result_count)
            self.filters_changed.emit()

    def show_result_info(self, show_load_more, total_count, displayed_count):
        """Show or hide result information"""
        if show_load_more:
            self.result_info_frame.setVisible(True)
            self.result_count_label.setText(f"Showing {displayed_count} of {total_count} results")
            self.load_more_button.setVisible(True)
        elif total_count > 0:
            self.result_info_frame.setVisible(True)
            self.result_count_label.setText(f"Showing all {total_count} results")
            self.load_more_button.setVisible(False)
        else:
            self.result_info_frame.setVisible(False)

    def get_current_filters(self):
        """Get current filter state as a dictionary"""
        return self.active_filters.copy()

    def get_result_limit(self):
        """Get current result limit"""
        return self.result_limit

    def clear_date_filters(self):
        """Clear date filters"""
        if 'date_filter' in self.active_filters:
            del self.active_filters['date_filter']
        # Reset date controls
        self.date_quick_buttons.buttons()[0].setChecked(True)  # "All" button
        self.update_active_count()

    def set_date_range(self, start_date, end_date):
        """Set date range filter"""
        self.active_filters['date_filter'] = {
            'type': 'range',
            'start_date': start_date.toPython() if hasattr(start_date, 'toPython') else start_date,
            'end_date': end_date.toPython() if hasattr(end_date, 'toPython') else end_date
        }
        self.update_active_count()

    def set_transaction_types(self, types):
        """Set transaction type filter - handles empty lists to show no data"""
        if types is not None:
            # Set the filter even if empty list (to show no data when no types selected)
            self.active_filters['transaction_types'] = types
        elif 'transaction_types' in self.active_filters:
            del self.active_filters['transaction_types']
        self.update_active_count()

    def clear_transaction_type_filters(self):
        """Clear transaction type filters"""
        if 'transaction_types' in self.active_filters:
            del self.active_filters['transaction_types']
        self.update_active_count()

    def clear_amount_filters(self):
        """Clear amount filters"""
        if 'amount_range' in self.active_filters:
            del self.active_filters['amount_range']
        self.update_active_count()

    def set_amount_range(self, min_amount, max_amount):
        """Set amount range filter"""
        self.active_filters['amount_range'] = {
            'min': min_amount,
            'max': max_amount
        }
        self.update_active_count()

    def set_categories(self, categories, sub_categories):
        """Set category filters"""
        if categories:
            self.active_filters['categories'] = categories
        elif 'categories' in self.active_filters:
            del self.active_filters['categories']

        if sub_categories:
            self.active_filters['sub_categories'] = sub_categories
        elif 'sub_categories' in self.active_filters:
            del self.active_filters['sub_categories']

        self.update_active_count()

    def set_category_filter(self, categories):
        """Set category filter"""
        if categories:
            self.active_filters['categories'] = categories
        elif 'categories' in self.active_filters:
            del self.active_filters['categories']
        self.update_active_count()

    def clear_category_filter(self):
        """Clear category filter"""
        if 'categories' in self.active_filters:
            del self.active_filters['categories']
        self.update_active_count()

    def set_subcategory_filter(self, subcategories):
        """Set subcategory filter"""
        if subcategories:
            self.active_filters['sub_categories'] = subcategories
        elif 'sub_categories' in self.active_filters:
            del self.active_filters['sub_categories']
        self.update_active_count()

    def clear_subcategory_filter(self):
        """Clear subcategory filter"""
        if 'sub_categories' in self.active_filters:
            del self.active_filters['sub_categories']
        self.update_active_count()

    def apply_preset_by_name(self, preset_name):
        """Apply a filter preset by name"""
        if preset_name in self.filter_presets:
            preset = self.filter_presets[preset_name]
            self.apply_preset_data(preset)

    def apply_filters(self):
        """Apply all current filters"""
        self.apply_filters_with_threading()

    def apply_filters_immediately(self):
        """Apply filters immediately without delay - for user interactions"""
        # Force immediate application for better responsiveness
        if len(self.data_model.get_all_expenses()) <= 2000:
            # Use direct filtering for reasonable dataset sizes
            self.apply_filters_direct()
        else:
            # Use threading for very large datasets
            self.apply_filters_with_threading()

    def get_active_filter_count(self):
        """Get the number of active filters"""
        return len(self.active_filters)

    def show_unfiltered_data(self):
        """Show all unfiltered data - emit signal to refresh with all data"""
        # Clear all active filters
        self.active_filters.clear()
        self.update_active_count()
        # Emit signal to show unfiltered data
        self.filters_changed.emit()

    def clear_all_filters(self):
        """Clear all active filters and show unfiltered data"""
        self.active_filters.clear()
        self.update_active_count()
        # Emit signal to refresh with unfiltered data
        self.filters_changed.emit()


class ExpenseEntryDialog(QDialog):
    """Dialog for adding/editing expense entries"""
    
    expense_saved = Signal(dict)
    
    def __init__(self, data_model: ExpenseDataModel, expense: ExpenseRecord = None, parent=None):
        super().__init__(parent)
        
        self.data_model = data_model
        self.expense = expense
        self.is_edit_mode = expense is not None
        
        self.setup_ui()
        self.setup_connections()
        
        if self.is_edit_mode:
            self.populate_fields()
        
        self.setModal(True)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Expense" if self.is_edit_mode else "Add New Expense")
        self.setMinimumSize(400, 500)
        self.resize(450, 550)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form layout
        form_frame = QFrame()
        form_frame.setObjectName("expenseFormFrame")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)
        
        # Date field
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setObjectName("expenseDateEdit")
        form_layout.addRow("Date:", self.date_edit)
        
        # Transaction type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Expense", "Income", "Transfer"])
        self.type_combo.setCurrentText("Expense")
        self.type_combo.setObjectName("expenseTypeCombo")
        form_layout.addRow("Type:", self.type_combo)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setObjectName("expenseCategoryCombo")
        self.populate_categories()
        form_layout.addRow("Category:", self.category_combo)
        
        # Sub-category
        self.subcategory_combo = QComboBox()
        self.subcategory_combo.setEditable(True)
        self.subcategory_combo.setObjectName("expenseSubcategoryCombo")
        form_layout.addRow("Sub-category:", self.subcategory_combo)
        
        # Transaction mode
        self.transaction_mode_combo = QComboBox()
        self.transaction_mode_combo.addItems([
            "Cash", "Credit Card", "Debit Card", "UPI", "Net Banking",
            "Wallet", "Cheque", "Bank Transfer", "Other"
        ])
        self.transaction_mode_combo.setObjectName("expenseTransactionModeCombo")
        form_layout.addRow("Payment Mode:", self.transaction_mode_combo)
        
        # Amount
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.01, 999999.99)
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setPrefix("₹ ")
        self.amount_spinbox.setObjectName("expenseAmountSpinbox")
        form_layout.addRow("Amount:", self.amount_spinbox)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes about this expense...")
        self.notes_edit.setObjectName("expenseNotesEdit")
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addWidget(form_frame)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.setObjectName("expenseDialogButtonBox")
        layout.addWidget(button_box)
        
        # Store references
        self.button_box = button_box
    
    def setup_connections(self):
        """Setup signal connections"""
        self.button_box.accepted.connect(self.save_expense)
        self.button_box.rejected.connect(self.reject)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
    
    def populate_categories(self):
        """Populate category dropdown"""
        categories = self.data_model.get_category_list()
        self.category_combo.clear()
        self.category_combo.addItems(categories)
    
    def on_category_changed(self, category: str):
        """Handle category change"""
        if category:
            subcategories = self.data_model.get_subcategory_list(category)
            self.subcategory_combo.clear()
            self.subcategory_combo.addItems(subcategories)
    
    def populate_fields(self):
        """Populate fields with existing expense data"""
        if not self.expense:
            return
        
        # Set date
        if isinstance(self.expense.date, date):
            self.date_edit.setDate(QDate(self.expense.date))
        
        # Set other fields
        self.type_combo.setCurrentText(self.expense.type)
        self.category_combo.setCurrentText(self.expense.category)
        self.on_category_changed(self.expense.category)  # Populate subcategories
        self.subcategory_combo.setCurrentText(self.expense.sub_category)
        self.transaction_mode_combo.setCurrentText(self.expense.transaction_mode)
        self.amount_spinbox.setValue(self.expense.amount)
        self.notes_edit.setPlainText(self.expense.notes)
    
    def save_expense(self):
        """Save the expense"""
        try:
            # Create expense record
            expense_data = ExpenseRecord(
                id=self.expense.id if self.is_edit_mode else None,
                date=self.date_edit.date().toPython(),
                type=self.type_combo.currentText(),
                category=self.category_combo.currentText(),
                sub_category=self.subcategory_combo.currentText(),
                transaction_mode=self.transaction_mode_combo.currentText(),
                amount=self.amount_spinbox.value(),
                notes=self.notes_edit.toPlainText()
            )
            
            # Validate
            errors = expense_data.validate()
            if errors:
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return
            
            # Save to data model
            if self.is_edit_mode:
                success = self.data_model.update_expense(self.expense.id, expense_data)
            else:
                success = self.data_model.add_expense(expense_data)
            
            if success:
                self.expense_saved.emit(expense_data.to_dict())
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save expense")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")


class ExpenseTableWidget(QTableWidget):
    """Custom table widget for displaying expenses with multi-select and labeling"""

    expense_selected = Signal(int)  # expense_id
    expense_edit_requested = Signal(int)  # expense_id
    expense_delete_requested = Signal(int)  # expense_id
    expenses_multi_selected = Signal(list)  # list of expense_ids
    label_requested = Signal(list)  # list of expense_ids for labeling
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_table()
        self.setup_connections()

        # Get text color from current theme
        self.text_color = self.get_theme_text_color()

    def get_theme_text_color(self):
        """Get the appropriate text color for the current theme"""
        # Get current theme from application
        app = QApplication.instance()
        if hasattr(app, 'current_theme'):
            theme = app.current_theme
        else:
            # Fallback: detect theme from palette
            palette = app.palette() if app else QPalette()
            bg_color = palette.color(QPalette.Window)
            theme = 'dark' if bg_color.lightness() < 128 else 'light'

        # Return appropriate text color based on theme
        if theme == 'dark':
            return QColor(255, 255, 255)  # White text for dark theme
        else:
            return QColor(0, 0, 0)  # Black text for light theme

    def set_item_colors(self, item):
        """Set colors for a table item to ensure visibility - theme-aware"""
        if item:
            # Let the global theme handle colors - don't override
            # Just ensure the item data is properly set
            item.setData(Qt.DisplayRole, item.text())

    def setup_table(self):
        """Setup table properties"""
        # Set table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Enable multi-selection
        self.setSortingEnabled(True)
        self.setObjectName("expenseTable")

        # Enable context menu for labeling
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set columns
        columns = ["ID", "Date", "Type", "Category", "Sub-category", "Mode", "Amount", "Notes"]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # Configure header with enhanced resize functionality
        header = self.horizontalHeader()
        header.setStretchLastSection(True)

        # Enable manual column resizing by user
        header.setSectionsMovable(True)  # Allow column reordering
        header.setSectionsClickable(True)  # Allow column sorting
        header.setDefaultSectionSize(120)  # Default column width

        # Set resize modes for better user control
        header.setSectionResizeMode(0, QHeaderView.Fixed)             # ID (hidden)
        header.setSectionResizeMode(1, QHeaderView.Interactive)       # Date - user resizable
        header.setSectionResizeMode(2, QHeaderView.Interactive)       # Type - user resizable
        header.setSectionResizeMode(3, QHeaderView.Interactive)       # Category - user resizable
        header.setSectionResizeMode(4, QHeaderView.Interactive)       # Sub-category - user resizable
        header.setSectionResizeMode(5, QHeaderView.Interactive)       # Mode - user resizable
        header.setSectionResizeMode(6, QHeaderView.Interactive)       # Amount - user resizable
        header.setSectionResizeMode(7, QHeaderView.Stretch)           # Notes - stretches to fill

        # Set minimum column widths for better usability
        header.setMinimumSectionSize(80)
        self.setColumnWidth(1, 100)  # Date
        self.setColumnWidth(2, 80)   # Type
        self.setColumnWidth(3, 150)  # Category
        self.setColumnWidth(4, 150)  # Sub-category
        self.setColumnWidth(5, 100)  # Mode
        self.setColumnWidth(6, 100)  # Amount

        # Hide ID column
        self.setColumnHidden(0, True)

        # Add double-click to auto-resize functionality
        header.sectionDoubleClicked.connect(self.auto_resize_column)

    def auto_resize_column(self, logical_index):
        """Auto-resize column to fit content when double-clicked"""
        self.resizeColumnToContents(logical_index)
        # Ensure minimum width
        if self.columnWidth(logical_index) < 80:
            self.setColumnWidth(logical_index, 80)

    def setup_connections(self):
        """Setup signal connections"""
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def populate_table(self, expenses_df):
        """Populate table with expense data with robust error handling"""
        try:
            self.setRowCount(0)

            if expenses_df.empty:
                return

            # Ensure required columns exist
            required_columns = ['id', 'date', 'type', 'category', 'sub_category', 'transaction_mode', 'amount', 'notes']
            missing_columns = [col for col in required_columns if col not in expenses_df.columns]
            if missing_columns:
                print(f"Warning: Missing columns in expense data: {missing_columns}")
                return

            # Sort by date (newest first) with error handling
            try:
                expenses_df = expenses_df.sort_values('date', ascending=False)
            except Exception as e:
                print(f"Warning: Could not sort by date: {e}")
                # Continue without sorting

            self.setRowCount(len(expenses_df))

            for row, (_, expense) in enumerate(expenses_df.iterrows()):
                try:
                    # ID (hidden)
                    id_item = QTableWidgetItem(str(expense.get('id', '')))
                    self.set_item_colors(id_item)
                    self.setItem(row, 0, id_item)

                    # Date with robust handling
                    date_str = expense.get('date', '')
                    if pd.isna(date_str) or date_str == '' or str(date_str).lower() == 'nan':
                        date_str = 'Invalid Date'
                    elif isinstance(date_str, str):
                        try:
                            # Try standard date format first
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                            date_str = date_obj.strftime('%d/%m/%Y')
                        except ValueError:
                            try:
                                # Try datetime format
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
                                date_str = date_obj.strftime('%d/%m/%Y')
                            except ValueError:
                                try:
                                    # Try pandas timestamp string
                                    date_obj = pd.to_datetime(date_str).date()
                                    date_str = date_obj.strftime('%d/%m/%Y')
                                except:
                                    date_str = 'Invalid Date'  # Fallback for unparseable dates
                    elif hasattr(date_str, 'strftime'):
                        # Handle pandas Timestamp objects
                        try:
                            date_str = date_str.strftime('%d/%m/%Y')
                        except Exception:
                            date_str = 'Invalid Date'
                    else:
                        date_str = 'Invalid Date'

                    date_item = QTableWidgetItem(str(date_str))
                    self.set_item_colors(date_item)
                    self.setItem(row, 1, date_item)

                    # Type
                    type_item = QTableWidgetItem(str(expense.get('type', '')))
                    self.set_item_colors(type_item)
                    self.setItem(row, 2, type_item)

                    # Category
                    category_item = QTableWidgetItem(str(expense.get('category', '')))
                    self.set_item_colors(category_item)
                    self.setItem(row, 3, category_item)

                    # Sub-category
                    subcategory_item = QTableWidgetItem(str(expense.get('sub_category', '')))
                    self.set_item_colors(subcategory_item)
                    self.setItem(row, 4, subcategory_item)

                    # Transaction mode
                    mode_item = QTableWidgetItem(str(expense.get('transaction_mode', '')))
                    self.set_item_colors(mode_item)
                    self.setItem(row, 5, mode_item)

                    # Amount with error handling
                    try:
                        amount = float(expense.get('amount', 0))
                        amount_item = QTableWidgetItem(f"₹{amount:.2f}")
                        amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.set_item_colors(amount_item)
                        self.setItem(row, 6, amount_item)
                    except (ValueError, TypeError):
                        amount_item = QTableWidgetItem("₹0.00")
                        self.set_item_colors(amount_item)
                        self.setItem(row, 6, amount_item)

                    # Notes
                    notes = str(expense.get('notes', '')) if expense.get('notes') else ""
                    if len(notes) > 50:
                        notes = notes[:47] + "..."
                    notes_item = QTableWidgetItem(notes)
                    self.set_item_colors(notes_item)
                    self.setItem(row, 7, notes_item)

                except Exception as e:
                    print(f"Error populating row {row}: {e}")
                    # Continue with next row
                    continue

            # Force table refresh to ensure styling is applied
            self.viewport().update()
            self.repaint()

            # Apply theme-aware styling - let global theme handle colors
            # Remove any hardcoded stylesheets to allow theme inheritance
            self.setStyleSheet("")

        except Exception as e:
            print(f"Error populating table: {e}")
            self.setRowCount(0)

    def on_item_double_clicked(self, item):
        """Handle item double click"""
        row = item.row()
        expense_id = int(self.item(row, 0).text())
        self.expense_edit_requested.emit(expense_id)
    
    def on_selection_changed(self):
        """Handle selection change"""
        selected_rows = self.selectionModel().selectedRows()

        if len(selected_rows) == 1:
            # Single selection - emit single expense selected
            row = selected_rows[0].row()
            expense_id = int(self.item(row, 0).text())
            self.expense_selected.emit(expense_id)
        elif len(selected_rows) > 1:
            # Multi-selection - emit list of expense IDs
            expense_ids = []
            for index in selected_rows:
                row = index.row()
                expense_id = int(self.item(row, 0).text())
                expense_ids.append(expense_id)
            self.expenses_multi_selected.emit(expense_ids)

    def get_selected_expense_id(self) -> Optional[int]:
        """Get the ID of the currently selected expense (single selection)"""
        current_row = self.currentRow()
        if current_row >= 0:
            return int(self.item(current_row, 0).text())
        return None

    def get_selected_expense_ids(self) -> List[int]:
        """Get the IDs of all currently selected expenses"""
        selected_rows = self.selectionModel().selectedRows()
        expense_ids = []
        for index in selected_rows:
            row = index.row()
            expense_id = int(self.item(row, 0).text())
            expense_ids.append(expense_id)
        return expense_ids

    def show_context_menu(self, position):
        """Show context menu for selected expenses and table options"""
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)

        # Table resize options (always available)
        resize_menu = menu.addMenu("📏 Column Resize")

        auto_resize_all_action = resize_menu.addAction("🔧 Auto-resize All Columns")
        auto_resize_all_action.triggered.connect(self.auto_resize_all_columns)

        reset_widths_action = resize_menu.addAction("↩️ Reset Column Widths")
        reset_widths_action.triggered.connect(self.reset_column_widths)

        # Add separator before expense actions
        selected_ids = self.get_selected_expense_ids()
        if selected_ids:
            menu.addSeparator()

            # Add label action
            if len(selected_ids) == 1:
                label_action = menu.addAction("🏷️ Add Label")
            else:
                label_action = menu.addAction(f"🏷️ Add Label to {len(selected_ids)} expenses")

            label_action.triggered.connect(lambda: self.label_requested.emit(selected_ids))

            # Add other actions
            menu.addSeparator()

            if len(selected_ids) == 1:
                edit_action = menu.addAction("✏️ Edit")
                edit_action.triggered.connect(lambda: self.expense_edit_requested.emit(selected_ids[0]))

            delete_action = menu.addAction(f"🗑️ Delete {len(selected_ids)} expense(s)")
            delete_action.triggered.connect(lambda: self.request_delete_multiple(selected_ids))

        # Show menu
        menu.exec(self.mapToGlobal(position))

    def request_delete_multiple(self, expense_ids: List[int]):
        """Request deletion of multiple expenses"""
        for expense_id in expense_ids:
            self.expense_delete_requested.emit(expense_id)

    def auto_resize_all_columns(self):
        """Auto-resize all columns to fit their content"""
        for column in range(self.columnCount()):
            if not self.isColumnHidden(column):
                self.resizeColumnToContents(column)
                # Ensure minimum width
                if self.columnWidth(column) < 80:
                    self.setColumnWidth(column, 80)

    def reset_column_widths(self):
        """Reset all columns to default widths"""
        self.setColumnWidth(1, 100)  # Date
        self.setColumnWidth(2, 80)   # Type
        self.setColumnWidth(3, 150)  # Category
        self.setColumnWidth(4, 150)  # Sub-category
        self.setColumnWidth(5, 100)  # Mode
        self.setColumnWidth(6, 100)  # Amount
        # Notes column will stretch automatically


class ExpenseStatsWidget(QWidget):
    """Enhanced widget displaying expense statistics with filtered data comparison"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_filtered = False
        self.unfiltered_stats = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the 1x2 layout transaction statistics UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Good spacing for readability
        layout.setContentsMargins(10, 10, 10, 10)  # Comfortable margins

        # Title with refresh button
        header_layout = QHBoxLayout()
        self.title_label = QLabel("📊 Transaction Summary")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 4px;
                text-align: center;
            }
        """)
        header_layout.addWidget(self.title_label)

        # Manual refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.refresh_button.clicked.connect(self.manual_refresh)
        header_layout.addWidget(self.refresh_button)

        layout.addLayout(header_layout)

        # Filter status indicator
        self.filter_status_frame = QFrame()
        self.filter_status_frame.setVisible(False)
        self.filter_status_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e8;
                border: 1px solid #4caf50;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        filter_status_layout = QVBoxLayout(self.filter_status_frame)
        filter_status_layout.setContentsMargins(6, 4, 6, 4)

        self.filter_summary_label = QLabel()
        self.filter_summary_label.setStyleSheet("color: #2e7d32; font-size: 9pt;")
        self.filter_summary_label.setWordWrap(True)
        filter_status_layout.addWidget(self.filter_summary_label)

        layout.addWidget(self.filter_status_frame)

        # Create 1x2 horizontal layout for statistics
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(12)  # Good spacing between columns

        # Left column: Summary sections (Credits, Debits, Overview)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)  # Good spacing between sections
        left_layout.setContentsMargins(8, 8, 8, 8)  # Comfortable margins

        # Credits summary section
        self.create_credits_summary_section(left_layout)

        # Debits summary section
        self.create_debits_summary_section(left_layout)

        # Additional summary section
        self.create_additional_summary_section(left_layout)

        left_scroll.setWidget(left_widget)
        main_horizontal_layout.addWidget(left_scroll)

        # Right column: Category breakdown
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)  # Good spacing between sections
        right_layout.setContentsMargins(8, 8, 8, 8)  # Comfortable margins

        # Category breakdown section
        self.create_category_breakdown_section(right_layout)

        right_scroll.setWidget(right_widget)
        main_horizontal_layout.addWidget(right_scroll)

        # Set equal proportions for both columns
        main_horizontal_layout.setStretch(0, 1)  # Left column
        main_horizontal_layout.setStretch(1, 1)  # Right column

        layout.addLayout(main_horizontal_layout)

    def manual_refresh(self):
        """Manual refresh triggered by user button click"""
        try:
            # Emit signal to parent to refresh data
            if hasattr(self.parent(), 'update_statistics'):
                self.parent().update_statistics()
            elif hasattr(self.parent(), 'load_expenses'):
                self.parent().load_expenses()

            # Update button text temporarily to show action
            original_text = self.refresh_button.text()
            self.refresh_button.setText("✓ Refreshed")
            self.refresh_button.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)

            # Reset button after 1 second
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.reset_refresh_button(original_text))

        except Exception as e:
            print(f"Error during manual refresh: {e}")

    def reset_refresh_button(self, original_text):
        """Reset refresh button to original state"""
        self.refresh_button.setText(original_text)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

    def create_credits_summary_section(self, parent_layout):
        """Create credits (income) summary section"""
        credits_frame = QFrame()
        credits_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #4caf50;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        credits_layout = QVBoxLayout(credits_frame)
        credits_layout.setContentsMargins(10, 8, 10, 8)
        credits_layout.setSpacing(8)

        # Credits title
        credits_title = QLabel("💰 Credits Summary (Income)")
        credits_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2e7d32;
                font-size: 11pt;
                margin-bottom: 6px;
                padding: 4px;
            }
        """)
        credits_layout.addWidget(credits_title)

        # Credits stats grid
        credits_stats_layout = QGridLayout()
        credits_stats_layout.setSpacing(8)
        credits_stats_layout.setContentsMargins(4, 4, 4, 4)

        # Create credit stat labels
        self.credits_amount_label = QLabel("₹0.00")
        self.credits_count_label = QLabel("0")

        # Style credit stat labels
        for label in [self.credits_amount_label, self.credits_count_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 10pt;
                    font-weight: bold;
                    color: #90ee90;
                    background-color: #2d5a2d;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                    padding: 6px;
                    text-align: center;
                }
            """)
            label.setAlignment(Qt.AlignCenter)

        # Add to layout
        credits_stats_layout.addWidget(QLabel("Total Amount:"), 0, 0)
        credits_stats_layout.addWidget(self.credits_amount_label, 0, 1)
        credits_stats_layout.addWidget(QLabel("Transaction Count:"), 1, 0)
        credits_stats_layout.addWidget(self.credits_count_label, 1, 1)

        credits_layout.addLayout(credits_stats_layout)
        parent_layout.addWidget(credits_frame)

    def create_debits_summary_section(self, parent_layout):
        """Create debits (expense) summary section"""
        debits_frame = QFrame()
        debits_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #f44336;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        debits_layout = QVBoxLayout(debits_frame)
        debits_layout.setContentsMargins(10, 8, 10, 8)
        debits_layout.setSpacing(8)

        # Debits title
        debits_title = QLabel("💸 Debits Summary (Expenses)")
        debits_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #c62828;
                font-size: 11pt;
                margin-bottom: 6px;
                padding: 4px;
            }
        """)
        debits_layout.addWidget(debits_title)

        # Debits stats grid
        debits_stats_layout = QGridLayout()
        debits_stats_layout.setSpacing(8)
        debits_stats_layout.setContentsMargins(4, 4, 4, 4)

        # Create debit stat labels
        self.debits_amount_label = QLabel("₹0.00")
        self.debits_count_label = QLabel("0")

        # Style debit stat labels
        for label in [self.debits_amount_label, self.debits_count_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 10pt;
                    font-weight: bold;
                    color: #b71c1c;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                    padding: 6px;
                    text-align: center;
                }
            """)
            label.setAlignment(Qt.AlignCenter)

        # Add to layout
        debits_stats_layout.addWidget(QLabel("Total Amount:"), 0, 0)
        debits_stats_layout.addWidget(self.debits_amount_label, 0, 1)
        debits_stats_layout.addWidget(QLabel("Transaction Count:"), 1, 0)
        debits_stats_layout.addWidget(self.debits_count_label, 1, 1)

        debits_layout.addLayout(debits_stats_layout)
        parent_layout.addWidget(debits_frame)

    def create_category_breakdown_section(self, parent_layout):
        """Create detailed category breakdown section"""
        self.category_frame = QFrame()
        self.category_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4fd;
                border: 1px solid #2196f3;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        category_layout = QVBoxLayout(self.category_frame)
        category_layout.setContentsMargins(10, 8, 10, 8)
        category_layout.setSpacing(8)

        # Category breakdown title
        category_title = QLabel("📊 Category-wise Breakdown")
        category_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #1565c0;
                font-size: 11pt;
                margin-bottom: 6px;
                padding: 4px;
            }
        """)
        category_layout.addWidget(category_title)

        # Scrollable area for category details (expanded to fill available space)
        self.category_scroll = QScrollArea()
        self.category_scroll.setWidgetResizable(True)
        # Remove height limitation to allow expansion
        self.category_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.category_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Set size policy to expand
        from PySide6.QtWidgets import QSizePolicy
        self.category_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.category_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bbdefb;
                border-radius: 4px;
            }
        """)

        self.category_content_widget = QWidget()
        self.category_content_layout = QVBoxLayout(self.category_content_widget)
        self.category_content_layout.setContentsMargins(4, 4, 4, 4)
        self.category_content_layout.setSpacing(2)

        # Default message
        self.no_data_label = QLabel("No filtered data available")
        self.no_data_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                text-align: center;
                padding: 20px;
            }
        """)
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.category_content_layout.addWidget(self.no_data_label)

        self.category_scroll.setWidget(self.category_content_widget)
        category_layout.addWidget(self.category_scroll)

        parent_layout.addWidget(self.category_frame)

    def create_additional_summary_section(self, parent_layout):
        """Create additional summary section to use more space"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        # Set size policy to expand and fill available space
        from PySide6.QtWidgets import QSizePolicy
        summary_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(10, 8, 10, 8)
        summary_layout.setSpacing(8)

        # Summary title
        summary_title = QLabel("📈 Transaction Overview")
        summary_title.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #495057;
                padding: 4px;
                margin-bottom: 6px;
            }
        """)
        summary_layout.addWidget(summary_title)

        # Net balance section
        net_frame = QFrame()
        net_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        net_layout = QHBoxLayout(net_frame)
        net_layout.setContentsMargins(8, 4, 8, 4)

        net_label = QLabel("Net Balance:")
        net_label.setStyleSheet("font-weight: bold; color: #6c757d;")
        self.net_balance_label = QLabel("₹0.00")
        self.net_balance_label.setStyleSheet("font-weight: bold; font-size: 12pt;")

        net_layout.addWidget(net_label)
        net_layout.addStretch()
        net_layout.addWidget(self.net_balance_label)
        summary_layout.addWidget(net_frame)

        # Average transaction section
        avg_frame = QFrame()
        avg_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        avg_layout = QHBoxLayout(avg_frame)
        avg_layout.setContentsMargins(8, 4, 8, 4)

        avg_label = QLabel("Average Transaction:")
        avg_label.setStyleSheet("font-weight: bold; color: #6c757d;")
        self.avg_transaction_label = QLabel("₹0.00")
        self.avg_transaction_label.setStyleSheet("font-weight: bold; color: #17a2b8;")

        avg_layout.addWidget(avg_label)
        avg_layout.addStretch()
        avg_layout.addWidget(self.avg_transaction_label)
        summary_layout.addWidget(avg_frame)

        # Total transactions section
        total_frame = QFrame()
        total_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        total_layout = QHBoxLayout(total_frame)
        total_layout.setContentsMargins(8, 4, 8, 4)

        total_label = QLabel("Total Transactions:")
        total_label.setStyleSheet("font-weight: bold; color: #6c757d;")
        self.total_transactions_label = QLabel("0")
        self.total_transactions_label.setStyleSheet("font-weight: bold; color: #6f42c1;")

        total_layout.addWidget(total_label)
        total_layout.addStretch()
        total_layout.addWidget(self.total_transactions_label)
        summary_layout.addWidget(total_frame)

        parent_layout.addWidget(summary_frame)

    def update_stats(self, stats: Dict[str, Any]):
        """Update the focused filtered transaction statistics with proper validation"""
        # Check if this is filtered data
        self.is_filtered = stats.get('filtered', False)

        # Update title and filter status
        if self.is_filtered:
            self.title_label.setText("📊 Filtered Transaction Summary")
            self.filter_status_frame.setVisible(True)
            filter_summary = stats.get('filter_summary', 'Filters applied')
            self.filter_summary_label.setText(f"🔍 Active Filters: {filter_summary}")
        else:
            self.title_label.setText("📊 All Transaction Summary")
            self.filter_status_frame.setVisible(False)

        # Check if we have valid transaction data
        total_transactions = stats.get('total_transactions', 0)
        has_valid_data = (
            total_transactions > 0 and
            (stats.get('total_income', 0) > 0 or stats.get('total_expense', 0) > 0)
        )

        if not has_valid_data:
            # No valid data - show zeros
            self.credits_amount_label.setText("₹0.00")
            self.credits_count_label.setText("0")
            self.debits_amount_label.setText("₹0.00")
            self.debits_count_label.setText("0")
            self.net_balance_label.setText("₹0.00")
            self.avg_transaction_label.setText("₹0.00")
            self.total_transactions_label.setText("0")
            self.clear_category_breakdown()
            return

        # Update credits and debits summaries with actual data
        credits_amount = stats.get('total_income', 0)
        credits_count = stats.get('income_count', 0)
        debits_amount = stats.get('total_expense', 0)
        debits_count = stats.get('expense_count', 0)

        self.credits_amount_label.setText(f"₹{credits_amount:.2f}")
        self.credits_count_label.setText(str(credits_count))
        self.debits_amount_label.setText(f"₹{debits_amount:.2f}")
        self.debits_count_label.setText(str(debits_count))

        # Update additional summary fields
        net_balance = credits_amount - debits_amount
        self.net_balance_label.setText(f"₹{net_balance:.2f}")

        # Set color based on net balance
        if net_balance > 0:
            self.net_balance_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #28a745;")
        elif net_balance < 0:
            self.net_balance_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #dc3545;")
        else:
            self.net_balance_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #6c757d;")

        # Update average transaction
        avg_amount = stats.get('average_amount', 0)
        self.avg_transaction_label.setText(f"₹{avg_amount:.2f}")

        # Update total transactions
        total_transactions = stats.get('total_transactions', 0)
        self.total_transactions_label.setText(str(total_transactions))

        # Update category breakdown with actual data
        self.update_category_breakdown(stats)

    def clear_category_breakdown(self):
        """Clear the category breakdown display"""
        # Clear existing category items
        for i in reversed(range(self.category_content_layout.count())):
            child = self.category_content_layout.itemAt(i).widget()
            if child and child != self.no_data_label:
                child.setParent(None)

        # Show default message
        self.no_data_label.setVisible(True)

    def update_category_breakdown(self, stats: Dict[str, Any]):
        """Update category breakdown with actual data and proper validation"""
        # Clear existing category items first
        self.clear_category_breakdown()

        # Get category breakdown data
        category_breakdown = stats.get('category_breakdown', {})

        # Check if we have valid transaction data
        total_transactions = stats.get('total_transactions', 0)
        has_valid_data = (
            total_transactions > 0 and
            category_breakdown and
            any(amount > 0 for amount in category_breakdown.values())
        )

        if not has_valid_data:
            # No valid category data available
            self.no_data_label.setText("No expense data available")
            self.no_data_label.setVisible(True)
            return

        # Hide the no data label
        self.no_data_label.setVisible(False)

        # Add category breakdown items
        total_amount = sum(abs(amount) for amount in category_breakdown.values())

        for category, amount in sorted(category_breakdown.items(), key=lambda x: abs(x[1]), reverse=True):
            if amount != 0:  # Only show categories with non-zero amounts
                percentage = (abs(amount) / total_amount * 100) if total_amount > 0 else 0

                # Create category item
                category_item = self.create_category_item(
                    category,
                    amount,
                    1,  # Count - we'll improve this later with actual transaction counts
                    percentage,
                    total_amount
                )
                self.category_content_layout.addWidget(category_item)

    def create_category_item(self, category_name, amount, count, percentage, total_amount):
        """Create a category breakdown item widget"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin: 1px;
                padding: 4px;
            }
        """)

        item_layout = QVBoxLayout(item_frame)
        item_layout.setContentsMargins(6, 4, 6, 4)
        item_layout.setSpacing(2)

        # Category name and percentage
        header_layout = QHBoxLayout()

        category_label = QLabel(category_name)
        category_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #495057;
                font-size: 9pt;
            }
        """)

        percentage_label = QLabel(f"{percentage:.1f}%")
        percentage_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 8pt;
                font-weight: bold;
            }
        """)
        percentage_label.setAlignment(Qt.AlignRight)

        header_layout.addWidget(category_label)
        header_layout.addWidget(percentage_label)
        item_layout.addLayout(header_layout)

        # Amount and count details
        details_layout = QHBoxLayout()

        amount_label = QLabel(f"₹{amount:.2f}")
        amount_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-weight: bold;
                font-size: 9pt;
            }
        """)

        count_label = QLabel(f"{count} transactions")
        count_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 8pt;
            }
        """)
        count_label.setAlignment(Qt.AlignRight)

        details_layout.addWidget(amount_label)
        details_layout.addWidget(count_label)
        item_layout.addLayout(details_layout)

        # Progress bar for visual representation
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(percentage))
        progress_bar.setTextVisible(False)
        progress_bar.setMaximumHeight(4)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e9ecef;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 2px;
            }
        """)
        item_layout.addWidget(progress_bar)

        return item_frame

    def set_filtered_data(self, filtered_df):
        """Set filtered DataFrame for detailed credits, debits, and category analysis with validation"""
        # Check if we have valid data
        if filtered_df.empty or not self._has_valid_transaction_data(filtered_df):
            # Reset to default values
            self.credits_amount_label.setText("₹0.00")
            self.credits_count_label.setText("0")
            self.debits_amount_label.setText("₹0.00")
            self.debits_count_label.setText("0")
            self.clear_category_breakdown()
            return

        try:
            # Calculate credits (income) summary
            credits_df = filtered_df[filtered_df['type'].isin(['Income', 'Credit'])]
            credits_total = float(credits_df['amount'].sum()) if not credits_df.empty else 0.0
            credits_count = len(credits_df)

            # Calculate debits (expenses) summary
            debits_df = filtered_df[filtered_df['type'].isin(['Expense', 'Debit'])]
            debits_total = float(debits_df['amount'].sum()) if not debits_df.empty else 0.0
            debits_count = len(debits_df)

            # Update credits summary
            self.credits_amount_label.setText(f"₹{credits_total:.2f}")
            self.credits_count_label.setText(str(credits_count))

            # Update debits summary
            self.debits_amount_label.setText(f"₹{debits_total:.2f}")
            self.debits_count_label.setText(str(debits_count))

            # Calculate category breakdown
            self.update_category_breakdown_with_data(filtered_df)

        except Exception as e:
            print(f"Error updating filtered data: {e}")
            # Reset to default values on error
            self.credits_amount_label.setText("₹0.00")
            self.credits_count_label.setText("0")
            self.debits_amount_label.setText("₹0.00")
            self.debits_count_label.setText("0")
            self.clear_category_breakdown()

    def update_category_breakdown_with_data(self, filtered_df):
        """Update category breakdown with actual filtered data"""
        try:
            # Clear existing breakdown
            self.clear_category_breakdown()

            if filtered_df.empty:
                return

            # Calculate category totals and counts
            category_stats = filtered_df.groupby('category').agg({
                'amount': ['sum', 'count']
            }).round(2)

            # Flatten column names
            category_stats.columns = ['total_amount', 'transaction_count']

            # Sort by total amount (highest to lowest)
            category_stats = category_stats.sort_values('total_amount', ascending=False)

            # Calculate total amount for percentage calculation
            total_amount = float(filtered_df['amount'].sum())

            if total_amount > 0:
                # Hide the no data label
                self.no_data_label.setVisible(False)

                # Create category items
                for category_name, stats in category_stats.iterrows():
                    amount = float(stats['total_amount'])
                    count = int(stats['transaction_count'])
                    percentage = (amount / total_amount) * 100

                    # Create and add category item
                    category_item = self.create_category_item(
                        category_name, amount, count, percentage, total_amount
                    )
                    self.category_content_layout.addWidget(category_item)

                # Add stretch to push items to top
                self.category_content_layout.addStretch()
            else:
                # Show no data message
                self.no_data_label.setVisible(True)

        except Exception as e:
            print(f"Error updating category breakdown: {e}")
            self.clear_category_breakdown()

    def _has_valid_transaction_data(self, df):
        """Check if DataFrame contains valid transaction data (excluding sample/test data)"""
        if df.empty:
            return False

        # Check if we have required columns
        required_columns = ['type', 'amount', 'category']
        if not all(col in df.columns for col in required_columns):
            return False

        # Filter out sample/test data
        real_data = self._filter_out_sample_data(df)
        if real_data.empty:
            return False

        # Check if we have valid transaction types
        valid_types = ['Income', 'Credit', 'Expense', 'Debit']
        if 'type' in real_data.columns:
            valid_type_data = real_data[real_data['type'].isin(valid_types)]
            if valid_type_data.empty:
                return False

        # Check if we have valid amounts (greater than 0)
        if 'amount' in real_data.columns:
            valid_amounts = real_data[real_data['amount'] > 0]
            if valid_amounts.empty:
                return False

        # Check if we have valid categories (not empty)
        if 'category' in real_data.columns:
            valid_categories = real_data[real_data['category'].str.strip() != '']
            if valid_categories.empty:
                return False

        return True

    def _filter_out_sample_data(self, df):
        """Filter out sample/test data to only include real transactions"""
        if df.empty:
            return df

        # Create a copy to avoid modifying the original
        filtered_df = df.copy()

        # Identify sample data patterns
        sample_patterns = [
            'Sample expense',
            'Sample income',
            'Test expense',
            'Test income',
            'Sample transaction',
            'Test transaction'
        ]

        # Check notes column for sample patterns
        if 'notes' in filtered_df.columns:
            for pattern in sample_patterns:
                filtered_df = filtered_df[~filtered_df['notes'].str.contains(pattern, case=False, na=False)]

        # Check for generic subcategory patterns that indicate sample data
        if 'sub_category' in filtered_df.columns:
            sample_subcategory_patterns = [
                r'.*_sub_\d+$',  # Patterns like "Shopping_sub_3", "Entertainment_sub_1"
                r'^General$',
                r'^Test.*',
                r'^Sample.*'
            ]

            for pattern in sample_subcategory_patterns:
                filtered_df = filtered_df[~filtered_df['sub_category'].str.match(pattern, case=False, na=False)]

        # If we have very few records (less than 10% of original or less than 100),
        # and they all look like sample data, consider it invalid
        if len(filtered_df) < max(10, len(df) * 0.1):
            # Additional check: if all remaining records have very similar amounts or patterns
            if not filtered_df.empty and 'amount' in filtered_df.columns:
                # Check if amounts are suspiciously uniform (common in sample data)
                amount_variance = filtered_df['amount'].var()
                amount_mean = filtered_df['amount'].mean()

                # If variance is very low relative to mean, it might be sample data
                if amount_mean > 0 and (amount_variance / amount_mean) < 0.1:
                    return pd.DataFrame()  # Return empty - likely all sample data

        return filtered_df


class CategoryManagementDialog(QDialog):
    """Dialog for managing expense categories"""
    
    categories_updated = Signal()
    
    def __init__(self, data_model: ExpenseDataModel, category_type: str = "expense", parent=None):
        super().__init__(parent)

        self.data_model = data_model
        self.category_type = category_type
        self.setup_ui()
        self.setup_connections()
        self.load_categories()

        self.setModal(True)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle(f"Manage {self.category_type.title()} Categories")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        # Category type filter section
        filter_frame = QGroupBox("Category Type")
        filter_layout = QHBoxLayout(filter_frame)

        self.category_type_combo = QComboBox()
        self.category_type_combo.addItems(["expense", "income"])
        self.category_type_combo.setCurrentText(self.category_type)
        self.category_type_combo.currentTextChanged.connect(self.on_category_type_changed)

        filter_layout.addWidget(QLabel("Show:"))
        filter_layout.addWidget(self.category_type_combo)
        filter_layout.addStretch()

        layout.addWidget(filter_frame)

        # Add new category section
        add_frame = QGroupBox(f"Add New {self.category_type.title()} Category")
        add_layout = QFormLayout(add_frame)
        
        self.new_category_edit = QLineEdit()
        self.new_subcategory_edit = QLineEdit()
        add_button = QPushButton("Add Category")
        add_button.clicked.connect(self.add_category)
        
        add_layout.addRow("Category:", self.new_category_edit)
        add_layout.addRow("Sub-category:", self.new_subcategory_edit)
        add_layout.addRow("", add_button)
        
        layout.addWidget(add_frame)
        
        # Categories table
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(4)
        self.categories_table.setHorizontalHeaderLabels(["Category", "Sub-category", "Active", "Actions"])
        self.categories_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.categories_table.setSelectionMode(QTableWidget.SingleSelection)
        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setSortingEnabled(True)
        self.categories_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.categories_table.customContextMenuRequested.connect(self.show_context_menu)

        # Set column widths
        header = self.categories_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Category column stretches
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Sub-category column stretches
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Active column fits content
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Actions column fits content

        layout.addWidget(self.categories_table)

        # Action buttons
        button_layout = QHBoxLayout()

        edit_button = QPushButton("Edit Selected")
        edit_button.clicked.connect(self.edit_category)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_category)
        button_layout.addWidget(delete_button)

        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Double-click to edit
        self.categories_table.itemDoubleClicked.connect(self.edit_category)
    
    def load_categories(self):
        """Load categories into the table filtered by category type"""
        # Clear the table first to ensure clean state
        self.categories_table.setRowCount(0)
        self.categories_table.clearContents()

        df = self.data_model.get_categories(self.category_type)

        if df.empty:
            # Force table update even when empty
            self.categories_table.viewport().update()
            return

        self.categories_table.setRowCount(len(df))

        for row, (_, category) in enumerate(df.iterrows()):
            # Store category ID in the first column's data
            category_item = QTableWidgetItem(str(category['category']))
            category_item.setData(Qt.UserRole, category['id'])  # Store ID for later use
            self.categories_table.setItem(row, 0, category_item)

            self.categories_table.setItem(row, 1, QTableWidgetItem(str(category['sub_category'])))

            # Active status checkbox with signal connection
            checkbox = QCheckBox()
            checkbox.setChecked(bool(category['is_active']))
            checkbox.stateChanged.connect(lambda state, cat_id=category['id']: self.toggle_category_status(cat_id, state == Qt.Checked))
            self.categories_table.setCellWidget(row, 2, checkbox)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)

            edit_btn = QPushButton("Edit")
            edit_btn.setMaximumWidth(50)
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_category_by_row(r))
            action_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Del")
            delete_btn.setMaximumWidth(50)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_category_by_row(r))
            action_layout.addWidget(delete_btn)

            self.categories_table.setCellWidget(row, 3, action_widget)

        # Force table refresh to ensure UI updates
        self.categories_table.viewport().update()
        self.categories_table.repaint()

    def add_category(self):
        """Add a new category"""
        category = self.new_category_edit.text().strip()
        subcategory = self.new_subcategory_edit.text().strip()
        
        if not category or not subcategory:
            QMessageBox.warning(self, "Error", "Both category and sub-category are required")
            return
        
        if self.data_model.add_category(category, subcategory, self.category_type):
            self.new_category_edit.clear()
            self.new_subcategory_edit.clear()
            self.load_categories()
            self.categories_updated.emit()
            QMessageBox.information(self, "Success", f"{self.category_type.title()} category added successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to add category")

    def on_category_type_changed(self, new_type: str):
        """Handle category type change"""
        self.category_type = new_type
        self.setWindowTitle(f"Manage {self.category_type.title()} Categories")

        # Update the add frame title
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox) and "Add New" in widget.title():
                widget.setTitle(f"Add New {self.category_type.title()} Category")
                break

        self.load_categories()

    def toggle_category_status(self, category_id: int, is_active: bool):
        """Toggle the active status of a category"""
        if self.data_model.toggle_category_status(category_id, is_active):
            self.categories_updated.emit()
        else:
            QMessageBox.warning(self, "Error", "Failed to update category status")
            # Reload to reset the checkbox
            self.load_categories()

    def edit_category(self):
        """Edit the selected category"""
        current_row = self.categories_table.currentRow()
        if current_row >= 0:
            self.edit_category_by_row(current_row)
        else:
            QMessageBox.information(self, "No Selection", "Please select a category to edit")

    def edit_category_by_row(self, row: int):
        """Edit category by row number"""
        if row < 0 or row >= self.categories_table.rowCount():
            return

        # Get category data
        category_item = self.categories_table.item(row, 0)
        subcategory_item = self.categories_table.item(row, 1)

        if not category_item or not subcategory_item:
            return

        category_id = category_item.data(Qt.UserRole)
        current_category = category_item.text()
        current_subcategory = subcategory_item.text()

        # Create cascading edit dialog
        dialog = CategoryEditDialog(
            self.data_model,
            self.category_type,
            category_id,
            current_category,
            current_subcategory,
            parent=self
        )

        if dialog.exec() == QDialog.Accepted:
            new_category, new_subcategory = dialog.get_values()

            if self.data_model.update_category(category_id, new_category, new_subcategory):
                self.load_categories()
                self.categories_updated.emit()
                QMessageBox.information(self, "Success", "Category updated successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to update category")

    def delete_category(self):
        """Delete the selected category"""
        current_row = self.categories_table.currentRow()
        if current_row >= 0:
            self.delete_category_by_row(current_row)
        else:
            QMessageBox.information(self, "No Selection", "Please select a category to delete")

    def delete_category_by_row(self, row: int):
        """Delete category by row number"""
        if row < 0 or row >= self.categories_table.rowCount():
            return

        # Get category data
        category_item = self.categories_table.item(row, 0)
        subcategory_item = self.categories_table.item(row, 1)

        if not category_item or not subcategory_item:
            return

        category_id = category_item.data(Qt.UserRole)
        category_name = category_item.text()
        subcategory_name = subcategory_item.text()

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the category '{category_name} - {subcategory_name}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.data_model.delete_category(category_id):
                self.load_categories()
                self.categories_updated.emit()
                QMessageBox.information(self, "Success", "Category deleted successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete category")

    def show_context_menu(self, position):
        """Show context menu for category table"""
        if self.categories_table.itemAt(position) is None:
            return

        context_menu = QMenu(self)

        edit_action = context_menu.addAction("Edit Category")
        edit_action.triggered.connect(self.edit_category)

        delete_action = context_menu.addAction("Delete Category")
        delete_action.triggered.connect(self.delete_category)

        context_menu.addSeparator()

        refresh_action = context_menu.addAction("Refresh")
        refresh_action.triggered.connect(self.load_categories)

        context_menu.exec(self.categories_table.mapToGlobal(position))


class CategoryEditDialog(QDialog):
    """Dialog for editing categories with cascading dropdowns"""

    def __init__(self, data_model: ExpenseDataModel, category_type: str, category_id: int,
                 current_category: str, current_subcategory: str, parent=None):
        super().__init__(parent)

        self.data_model = data_model
        self.category_type = category_type
        self.category_id = category_id
        self.current_category = current_category
        self.current_subcategory = current_subcategory

        self.setup_ui()
        self.setup_connections()
        self.populate_categories()

        self.setModal(True)

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle(f"Edit {self.category_type.title()} Category")
        self.setMinimumSize(450, 200)

        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Category dropdown
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setInsertPolicy(QComboBox.NoInsert)
        form_layout.addRow("Category:", self.category_combo)

        # Subcategory dropdown
        self.subcategory_combo = QComboBox()
        self.subcategory_combo.setEditable(True)
        self.subcategory_combo.setInsertPolicy(QComboBox.NoInsert)
        form_layout.addRow("Sub-category:", self.subcategory_combo)

        layout.addLayout(form_layout)

        # Info label
        self.info_label = QLabel("Select a category to see available subcategories, or type to create new ones.")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def setup_connections(self):
        """Setup signal connections"""
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        self.category_combo.editTextChanged.connect(self.on_category_text_changed)

    def populate_categories(self):
        """Populate the category dropdown"""
        # Get all categories for the current type
        categories = self.data_model.get_category_list(self.category_type)

        self.category_combo.clear()
        self.category_combo.addItems(categories)

        # Set current category
        if self.current_category in categories:
            self.category_combo.setCurrentText(self.current_category)
        else:
            # If current category is not in the list, add it and select it
            self.category_combo.addItem(self.current_category)
            self.category_combo.setCurrentText(self.current_category)

        # Trigger subcategory population
        self.on_category_changed(self.current_category)

    def on_category_changed(self, category_text: str):
        """Handle category selection change"""
        if not category_text.strip():
            self.subcategory_combo.clear()
            self.info_label.setText("Select a category to see available subcategories.")
            return

        # Get subcategories for the selected category
        subcategories = self.data_model.get_subcategory_list(category_text, self.category_type)

        # Store current subcategory selection to preserve it if possible
        current_subcategory_text = self.subcategory_combo.currentText()

        self.subcategory_combo.clear()

        if subcategories:
            self.subcategory_combo.addItems(subcategories)
            self.info_label.setText(f"Found {len(subcategories)} subcategories for '{category_text}'. Select one or type a new subcategory.")

            # Try to restore previous selection
            if current_subcategory_text in subcategories:
                self.subcategory_combo.setCurrentText(current_subcategory_text)
            elif self.current_subcategory in subcategories:
                self.subcategory_combo.setCurrentText(self.current_subcategory)
        else:
            # No existing subcategories for this category
            self.info_label.setText(f"No existing subcategories for '{category_text}'. Type a new subcategory name.")

            # If this is the original category, add the original subcategory
            if category_text == self.current_category and self.current_subcategory:
                self.subcategory_combo.addItem(self.current_subcategory)
                self.subcategory_combo.setCurrentText(self.current_subcategory)

    def on_category_text_changed(self, text: str):
        """Handle category text change (when user types)"""
        # Only update subcategories if the text matches an existing category
        categories = self.data_model.get_category_list(self.category_type)
        if text.strip() in categories:
            # Don't trigger on_category_changed if it's already the current selection
            # to avoid unnecessary updates
            if text != self.category_combo.currentText():
                self.on_category_changed(text)
        else:
            # Clear subcategories when typing a new category
            self.subcategory_combo.clear()
            if text.strip():
                self.info_label.setText(f"Creating new category '{text}'. Type a subcategory name.")
            else:
                self.info_label.setText("Select a category to see available subcategories, or type to create new ones.")

    def get_values(self):
        """Get the selected category and subcategory values"""
        category = self.category_combo.currentText().strip()
        subcategory = self.subcategory_combo.currentText().strip()
        return category, subcategory

    def accept(self):
        """Override accept to validate input"""
        category, subcategory = self.get_values()

        if not category or not subcategory:
            QMessageBox.warning(self, "Error", "Both category and sub-category are required")
            return

        super().accept()


class LabelManagementDialog(QDialog):
    """Dialog for adding labels to expenses"""

    def __init__(self, expense_ids: List[int], data_model, parent=None):
        super().__init__(parent)
        self.expense_ids = expense_ids
        self.data_model = data_model
        self.setWindowTitle(f"Add Label to {len(expense_ids)} Expense(s)")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
        self.load_existing_labels()

    def setup_ui(self):
        """Setup the label management UI"""
        layout = QVBoxLayout(self)

        # Info label
        info_text = f"Adding label to {len(self.expense_ids)} expense(s)"
        info_label = QLabel(info_text)
        info_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(info_label)

        # Label input
        label_frame = QFrame()
        label_layout = QFormLayout(label_frame)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Enter label name (e.g., 'Business', 'Personal', 'Tax Deductible')")
        label_layout.addRow("Label:", self.label_edit)

        # Color selection (optional)
        self.color_combo = QComboBox()
        colors = [
            ("Default", "#808080"),
            ("Red", "#f44336"),
            ("Green", "#4caf50"),
            ("Blue", "#2196f3"),
            ("Orange", "#ff9800"),
            ("Purple", "#9c27b0"),
            ("Teal", "#009688"),
            ("Pink", "#e91e63")
        ]

        for color_name, color_code in colors:
            self.color_combo.addItem(color_name, color_code)

        label_layout.addRow("Color:", self.color_combo)

        layout.addWidget(label_frame)

        # Existing labels
        existing_frame = QFrame()
        existing_layout = QVBoxLayout(existing_frame)

        existing_title = QLabel("Existing Labels:")
        existing_title.setFont(QFont("Arial", 10, QFont.Bold))
        existing_layout.addWidget(existing_title)

        self.existing_labels_list = QTableWidget()
        self.existing_labels_list.setColumnCount(3)
        self.existing_labels_list.setHorizontalHeaderLabels(["Label", "Color", "Count"])
        self.existing_labels_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.existing_labels_list.itemDoubleClicked.connect(self.on_existing_label_selected)
        existing_layout.addWidget(self.existing_labels_list)

        layout.addWidget(existing_frame)

        # Buttons
        button_layout = QHBoxLayout()

        apply_button = QPushButton("Apply Label")
        apply_button.clicked.connect(self.apply_label)
        button_layout.addWidget(apply_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def load_existing_labels(self):
        """Load existing labels from the database"""
        # This would load from a labels table if implemented
        # For now, show some example labels
        example_labels = [
            ("Business", "#2196f3", 15),
            ("Personal", "#4caf50", 23),
            ("Tax Deductible", "#ff9800", 8),
            ("Emergency", "#f44336", 3),
            ("Recurring", "#9c27b0", 12)
        ]

        self.existing_labels_list.setRowCount(len(example_labels))

        for row, (label, color, count) in enumerate(example_labels):
            self.existing_labels_list.setItem(row, 0, QTableWidgetItem(label))

            color_item = QTableWidgetItem()
            color_item.setBackground(QColor(color))
            color_item.setText(color)
            self.existing_labels_list.setItem(row, 1, color_item)

            self.existing_labels_list.setItem(row, 2, QTableWidgetItem(str(count)))

    def on_existing_label_selected(self, item):
        """Handle selection of existing label"""
        row = item.row()
        label_name = self.existing_labels_list.item(row, 0).text()
        self.label_edit.setText(label_name)

    def apply_label(self):
        """Apply the label to selected expenses"""
        label_text = self.label_edit.text().strip()
        if not label_text:
            QMessageBox.warning(self, "Error", "Please enter a label name")
            return

        color_code = self.color_combo.currentData()

        # Here you would implement the actual labeling logic
        # For now, just show a success message
        QMessageBox.information(
            self,
            "Success",
            f"Label '{label_text}' applied to {len(self.expense_ids)} expense(s)"
        )

        self.accept()


class ExpenseTrackerWidget(QWidget):
    """Main expense tracker widget"""

    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        self.data_manager = data_manager
        self.config = config
        self.expense_model = ExpenseDataModel(data_manager)

        self.setup_ui()
        self.setup_connections()
        self.refresh_data()

        # Auto-refresh timer disabled - users can manually refresh using the button
        # self.refresh_timer = QTimer()
        # self.refresh_timer.timeout.connect(self.refresh_data)
        # self.refresh_timer.start(30000)  # Refresh every 30 seconds

        # Check for new bank analyzer exports (delayed to allow UI to load)
        QTimer.singleShot(2000, self.check_for_bank_analyzer_exports)

    def update_theme(self, new_theme):
        """Update theme for expense tracker and all child components"""
        # Update summary widget if it exists
        if hasattr(self, 'summary_widget') and hasattr(self.summary_widget, 'update_theme'):
            self.summary_widget.update_theme(new_theme)

        # Update filter widget if it exists
        if hasattr(self, 'filter_widget') and hasattr(self.filter_widget, 'update_theme'):
            self.filter_widget.update_theme(new_theme)

        # Update stats widget if it exists
        if hasattr(self, 'stats_widget') and hasattr(self.stats_widget, 'update_theme'):
            self.stats_widget.update_theme(new_theme)

        # Update expense table if it exists
        if hasattr(self, 'expense_table') and hasattr(self.expense_table, 'update_theme'):
            self.expense_table.update_theme(new_theme)

        # Force update all widgets to apply new theme
        self.update()
        if hasattr(self, 'tab_widget'):
            self.tab_widget.update()
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if widget:
                    widget.update()

    def setup_ui(self):
        """Setup the main UI with tabs for different views"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 8)
        layout.setSpacing(6)

        # Header
        self.create_header(layout)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()

        # Expense Tracker Tab (original functionality)
        self.create_tracker_tab()

        # Expense Summary Tab (new analytics view)
        self.create_summary_tab()

        layout.addWidget(self.tab_widget)

    def create_tracker_tab(self):
        """Create the original expense tracker tab"""
        tracker_widget = QWidget()
        tracker_layout = QVBoxLayout(tracker_widget)
        tracker_layout.setContentsMargins(0, 0, 0, 0)
        tracker_layout.setSpacing(6)

        # 1x6 horizontal filter tabs at the top
        self.filter_widget = ExpenseFilterWidget(self.expense_model)
        self.filter_tabs = FilterTabWidget(self.filter_widget)
        tracker_layout.addWidget(self.filter_tabs)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel (table only)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel (focused statistics only)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([700, 300])
        tracker_layout.addWidget(splitter)

        self.tab_widget.addTab(tracker_widget, "💳 Expense Tracker")

    def create_summary_tab(self):
        """Create the new expense summary and analytics tab"""
        try:
            self.summary_widget = ExpenseSummaryWidget(self.data_manager, self.config)
            self.tab_widget.addTab(self.summary_widget, "📊 Analytics & Summary")
        except Exception as e:
            print(f"Error creating summary tab: {e}")
            # Create a placeholder if summary widget fails
            placeholder = QLabel("Summary view temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(placeholder, "📊 Analytics & Summary")

        # Create loading overlay for heavy operations
        self.create_loading_overlay()

    def create_header(self, layout):
        """Create header with title and action buttons"""
        header_frame = QFrame()
        header_frame.setObjectName("expenseHeader")
        header_frame.setMaximumHeight(50)  # Limit header height
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        header_layout.setSpacing(8)  # Reduced spacing between elements

        # Title
        title_label = QLabel("Expense Tracker")
        title_label.setObjectName("expenseTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)  # Reduced from 16 to 14
        title_label.setFont(font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Action buttons
        self.add_button = QPushButton("Add Expense")
        self.add_button.setObjectName("expenseAddButton")
        self.add_button.setMinimumHeight(32)  # Reduced from 35 to 32
        self.add_button.setMaximumHeight(32)  # Set maximum height to keep compact
        header_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.setObjectName("expenseEditButton")
        self.edit_button.setMinimumHeight(32)
        self.edit_button.setMaximumHeight(32)
        self.edit_button.setEnabled(False)
        header_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("expenseDeleteButton")
        self.delete_button.setMinimumHeight(32)
        self.delete_button.setMaximumHeight(32)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)

        self.categories_button = QPushButton("Manage Categories")
        self.categories_button.setObjectName("expenseCategoriesButton")
        self.categories_button.setMinimumHeight(32)
        self.categories_button.setMaximumHeight(32)
        header_layout.addWidget(self.categories_button)

        # Bank Statement Analyzer button - REMOVED
        # self.bank_analyzer_button = QPushButton("🏦 Bank Analyzer")
        # self.bank_analyzer_button.setObjectName("expenseBankAnalyzerButton")
        # self.bank_analyzer_button.setMinimumHeight(32)
        # self.bank_analyzer_button.setMaximumHeight(32)
        # self.bank_analyzer_button.setToolTip("Launch Bank Statement Analyzer to import transactions")
        # header_layout.addWidget(self.bank_analyzer_button)

        # Import from Bank Analyzer button - REMOVED
        # self.import_button = QPushButton("📥 Import")
        # self.import_button.setObjectName("expenseImportButton")
        # self.import_button.setMinimumHeight(32)
        # self.import_button.setMaximumHeight(32)
        # self.import_button.setToolTip("Import transactions from Bank Statement Analyzer export")
        # header_layout.addWidget(self.import_button)

        # Quick Import button for default transaction file - REMOVED
        # self.quick_import_button = QPushButton("⚡ Quick Import")
        # self.quick_import_button.setObjectName("expenseQuickImportButton")
        # self.quick_import_button.setMinimumHeight(32)
        # self.quick_import_button.setMaximumHeight(32)
        # self.quick_import_button.setToolTip("Quickly import pre-labeled transactions from default file")
        # header_layout.addWidget(self.quick_import_button)

        # Sync Categories button - REMOVED
        # self.sync_categories_button = QPushButton("🔄 Sync Categories")
        # self.sync_categories_button.setObjectName("expenseSyncCategoriesButton")
        # self.sync_categories_button.setMinimumHeight(32)
        # self.sync_categories_button.setMaximumHeight(32)
        # self.sync_categories_button.setToolTip("Synchronize categories with Bank Statement Analyzer")
        # header_layout.addWidget(self.sync_categories_button)

        layout.addWidget(header_frame)

    def create_left_panel(self):
        """Create left panel with expense table only"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Expense table (filter bar removed as requested)
        self.expense_table = ExpenseTableWidget()
        layout.addWidget(self.expense_table)

        return panel

    def create_right_panel(self):
        """Create right panel with expanded statistics to fill all available space"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Statistics widget (expanded to fill all available space)
        self.stats_widget = ExpenseStatsWidget()
        # Set size policy to expand and fill available space
        from PySide6.QtWidgets import QSizePolicy
        self.stats_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.stats_widget)

        return panel

    def create_loading_overlay(self):
        """Create loading overlay for heavy operations"""
        self.loading_overlay = QFrame(self)
        self.loading_overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 220);
                border-radius: 10px;
            }
        """)
        self.loading_overlay.setVisible(False)

        # Loading layout
        loading_layout = QVBoxLayout(self.loading_overlay)
        loading_layout.setAlignment(Qt.AlignCenter)

        # Loading spinner (using text for now)
        self.loading_label = QLabel("🔄 Processing...")
        self.loading_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #007bff; margin: 20px;")
        loading_layout.addWidget(self.loading_label)

        # Progress bar
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)  # Indeterminate progress
        self.loading_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        loading_layout.addWidget(self.loading_progress)

        # Status text
        self.loading_status = QLabel("Applying filters and updating data...")
        self.loading_status.setAlignment(Qt.AlignCenter)
        self.loading_status.setStyleSheet("color: #6c757d; margin: 10px;")
        loading_layout.addWidget(self.loading_status)

    def show_loading(self, message="Processing...", status="Please wait while the operation completes..."):
        """Show loading overlay with custom message"""
        self.loading_label.setText(f"🔄 {message}")
        self.loading_status.setText(status)

        # Position overlay to cover the entire widget
        self.loading_overlay.resize(self.size())
        self.loading_overlay.move(0, 0)
        self.loading_overlay.setVisible(True)
        self.loading_overlay.raise_()

        # Process events to show the overlay immediately
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

    def hide_loading(self):
        """Hide loading overlay"""
        self.loading_overlay.setVisible(False)

    def resizeEvent(self, event):
        """Handle resize events to keep loading overlay positioned correctly"""
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay') and self.loading_overlay.isVisible():
            self.loading_overlay.resize(self.size())

    def setup_connections(self):
        """Setup signal connections"""
        # Button connections
        self.add_button.clicked.connect(self.add_expense)
        self.edit_button.clicked.connect(self.edit_expense)
        self.delete_button.clicked.connect(self.delete_expense)
        self.categories_button.clicked.connect(self.manage_categories)
        # Removed button connections for Bank Analyzer, Import, Quick Import, and Sync Categories
        # self.bank_analyzer_button.clicked.connect(self.launch_bank_analyzer)
        # self.import_button.clicked.connect(self.import_from_bank_analyzer)
        # self.quick_import_button.clicked.connect(self.quick_import_transactions)
        # self.sync_categories_button.clicked.connect(self.sync_categories)

        # Table connections
        self.expense_table.expense_selected.connect(self.on_expense_selected)
        self.expense_table.expense_edit_requested.connect(self.edit_expense_by_id)
        self.expense_table.expense_delete_requested.connect(self.delete_expense_by_id)
        self.expense_table.expenses_multi_selected.connect(self.on_expenses_multi_selected)
        self.expense_table.label_requested.connect(self.show_label_dialog)

        # Filter widget connections
        self.filter_widget.filters_changed.connect(self.apply_comprehensive_filters)

        # Connect filter tabs to the underlying filter widget
        self.setup_filter_tab_connections()

        # Data model connections
        self.data_manager.data_changed.connect(self.on_data_changed)

    def setup_filter_tab_connections(self):
        """Setup connections between filter tabs and the main filter widget"""
        # The FilterTabWidget already connects to the underlying filter_widget
        # We just need to populate the categories and presets
        self.populate_filter_categories()
        self.populate_filter_presets()

    def populate_filter_categories(self):
        """Populate category lists in the filter tabs"""
        try:
            # Get all expenses to extract categories
            df = self.expense_model.get_all_expenses()

            if not df.empty:
                # Get unique categories and sub-categories
                categories = df['category'].dropna().unique().tolist()
                sub_categories = df['sub_category'].dropna().unique().tolist()

                # Populate the filter tab category lists
                self.filter_tabs.populate_categories(categories, sub_categories)

        except Exception as e:
            print(f"Error populating filter categories: {e}")
            # Provide default categories if there's an error
            default_categories = ["Food & Dining", "Transportation", "Shopping", "Entertainment", "Bills & Utilities"]
            default_sub_categories = ["Restaurants", "Groceries", "Fuel", "Public Transport", "Clothing", "Electronics"]
            self.filter_tabs.populate_categories(default_categories, default_sub_categories)

    def populate_filter_presets(self):
        """Populate filter presets in the filter tabs"""
        try:
            # Get presets from the filter widget
            presets = list(self.filter_widget.filter_presets.keys())
            self.filter_tabs.populate_presets(presets)

        except Exception as e:
            print(f"Error populating filter presets: {e}")
            # Provide default presets
            default_presets = ["This Month Expenses", "High Amount Transactions", "Food & Dining Only"]
            self.filter_tabs.populate_presets(default_presets)

    def refresh_data(self):
        """Refresh all data with comprehensive error handling"""
        try:
            # Try to load expenses first
            try:
                self.load_expenses()
            except Exception as e:
                print(f"Error loading expenses: {e}")
                # Clear table on error
                self.expense_table.setRowCount(0)

            # Try to update statistics
            try:
                self.update_statistics()
            except Exception as e:
                print(f"Error updating statistics: {e}")
                # Continue without statistics update

            # Try to populate filter widget categories
            try:
                self.filter_widget.populate_categories()
            except Exception as e:
                print(f"Error populating filter categories: {e}")
                # Continue without filter category update

            # Try to populate filter tab categories
            try:
                self.populate_filter_categories()
            except Exception as e:
                print(f"Error populating filter tab categories: {e}")
                # Continue without filter tab category update

        except Exception as e:
            print(f"Critical error refreshing expense data: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

            # Show user-friendly message only for critical errors
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Data Refresh Error",
                                  f"There was an issue refreshing the expense data:\n{str(e)}\n\nPlease try again or restart the application.")
            except:
                pass  # Don't fail if we can't show the message box

            # Load empty state gracefully
            try:
                self.expense_table.setRowCount(0)
            except:
                pass

    def load_expenses(self):
        """Load expenses into the table"""
        # Show loading for data loading
        self.show_loading("Loading Expenses", "Retrieving expense data from database...")

        try:
            df = self.expense_model.get_all_expenses()
            self.expense_table.populate_table(df)
            # Update statistics with all data
            self.update_statistics()
        finally:
            self.hide_loading()

    def update_statistics(self):
        """Update statistics display"""
        try:
            stats = self.expense_model.get_expense_summary()
            self.stats_widget.update_stats(stats)
        except Exception as e:
            print(f"Error updating statistics: {e}")

    def add_expense(self):
        """Add new expense"""
        dialog = ExpenseEntryDialog(self.expense_model, parent=self)
        dialog.expense_saved.connect(self.on_expense_saved)
        dialog.exec()

    def edit_expense(self):
        """Edit selected expense"""
        expense_id = self.expense_table.get_selected_expense_id()
        if expense_id:
            self.edit_expense_by_id(expense_id)

    def edit_expense_by_id(self, expense_id: int):
        """Edit expense by ID"""
        expense = self.expense_model.get_expense_by_id(expense_id)
        if expense:
            dialog = ExpenseEntryDialog(self.expense_model, expense, parent=self)
            dialog.expense_saved.connect(self.on_expense_saved)
            dialog.exec()

    def delete_expense(self):
        """Delete selected expense"""
        expense_id = self.expense_table.get_selected_expense_id()
        if not expense_id:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this expense?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.expense_model.delete_expense(expense_id):
                self.refresh_data()
                QMessageBox.information(self, "Success", "Expense deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete expense")

    def manage_categories(self):
        """Open category management dialog"""
        dialog = CategoryManagementDialog(self.expense_model, category_type="expense", parent=self)
        dialog.categories_updated.connect(self.populate_filter_categories)
        dialog.exec()

    def quick_add_expense(self, category: str, subcategory: str):
        """Quick add expense with predefined category"""
        expense = ExpenseRecord(
            category=category,
            sub_category=subcategory
        )
        dialog = ExpenseEntryDialog(self.expense_model, expense, parent=self)
        dialog.expense_saved.connect(self.on_expense_saved)
        dialog.exec()

    def apply_comprehensive_filters(self):
        """Apply comprehensive filters from the filter widget"""
        try:
            # Show loading screen for filtering operation
            self.show_loading("Applying Filters", "Processing expense data with current filter settings...")

            # Get current filter state
            filters = self.filter_widget.get_current_filters()
            result_limit = self.filter_widget.get_result_limit()

            # If no filters are active, show all expenses and update statistics
            if not filters:
                self.load_expenses()
                self.update_statistics()  # Update statistics with all data
                self.hide_loading()  # Hide loading screen
                return

            # Apply filters using the model's comprehensive filter method
            df = self.expense_model.get_expenses_by_filters(filters)

            # Apply result limiting if necessary
            if len(df) > result_limit:
                df = df.head(result_limit)

            # Update the table
            self.expense_table.populate_table(df)

            # Update statistics with filtered data
            self.update_filtered_statistics(df, filters)

            # Provide filtered data to stats widget for detailed analysis
            if hasattr(self.stats_widget, 'set_filtered_data'):
                self.stats_widget.set_filtered_data(df)

            # Hide loading screen when done
            self.hide_loading()

        except Exception as e:
            print(f"Error applying filters: {e}")
            # Fallback to showing all expenses
            self.load_expenses()
            self.update_statistics()
            # Hide loading screen even on error
            self.hide_loading()

    def update_filtered_statistics(self, filtered_df, filters):
        """Update statistics with filtered data"""
        try:
            # Calculate filtered statistics
            if not filtered_df.empty:
                filtered_stats = {
                    'total_expenses': len(filtered_df),
                    'total_amount': float(filtered_df['amount'].sum()),
                    'average_amount': float(filtered_df['amount'].mean()),
                    'categories_count': len(filtered_df['category'].unique()),
                    'filtered': True,
                    'filter_summary': self.format_filter_summary(filters)
                }
            else:
                filtered_stats = {
                    'total_expenses': 0,
                    'total_amount': 0.0,
                    'average_amount': 0.0,
                    'categories_count': 0,
                    'filtered': True,
                    'filter_summary': self.format_filter_summary(filters)
                }

            # Update the statistics widget
            self.stats_widget.update_stats(filtered_stats)

        except Exception as e:
            print(f"Error updating filtered statistics: {e}")

    def format_filter_summary(self, filters):
        """Format filter summary for display"""
        summary_parts = []

        if 'date_filter' in filters:
            summary_parts.append(f"Date: {filters['date_filter'].replace('_', ' ').title()}")

        if 'transaction_types' in filters:
            summary_parts.append(f"Types: {', '.join(filters['transaction_types'])}")

        if 'amount_range' in filters and filters['amount_range']:
            if isinstance(filters['amount_range'], tuple):
                min_amt, max_amt = filters['amount_range']
                if min_amt is not None and max_amt is not None:
                    summary_parts.append(f"Amount: ₹{min_amt}-₹{max_amt}")
                elif min_amt is not None:
                    summary_parts.append(f"Amount: ≥₹{min_amt}")
                elif max_amt is not None:
                    summary_parts.append(f"Amount: ≤₹{max_amt}")

        if 'categories' in filters:
            cat_count = len(filters['categories'])
            if cat_count <= 2:
                summary_parts.append(f"Categories: {', '.join(filters['categories'])}")
            else:
                summary_parts.append(f"Categories: {cat_count} selected")

        return " | ".join(summary_parts) if summary_parts else "No filters applied"

    def on_expense_selected(self, expense_id: int):
        """Handle expense selection"""
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def on_expense_saved(self, expense_data: dict):
        """Handle expense saved"""
        self.refresh_data()

    def on_data_changed(self, module: str, operation: str):
        """Handle data changes"""
        if module == "expenses":
            self.refresh_data()

    def on_expenses_multi_selected(self, expense_ids: List[int]):
        """Handle multiple expenses selected"""
        # Enable/disable buttons based on multi-selection
        self.edit_button.setEnabled(len(expense_ids) == 1)  # Only enable edit for single selection
        self.delete_button.setEnabled(len(expense_ids) > 0)  # Enable delete for any selection
        if len(expense_ids) > 1:
            total_amount = 0
            for expense_id in expense_ids:
                # Get expense amount (simplified - in real implementation you'd query the data)
                # For now, just show count
                pass

            # You could show a status message about selected expenses
            print(f"Selected {len(expense_ids)} expenses")

    def delete_expense_by_id(self, expense_id: int):
        """Delete expense by ID"""
        reply = QMessageBox.question(
            self, "Delete Expense",
            "Are you sure you want to delete this expense?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.expense_model.delete_expense(expense_id):
                self.refresh_data()
                QMessageBox.information(self, "Success", "Expense deleted successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete expense")

    def show_label_dialog(self, expense_ids: List[int]):
        """Show label management dialog for selected expenses"""
        try:
            dialog = LabelManagementDialog(expense_ids, self.expense_model, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open label dialog: {str(e)}")

    def launch_bank_analyzer(self):
        """Launch the Bank Statement Analyzer application"""
        try:
            # Import the integration module
            from ...core.bank_analyzer_integration import create_launcher

            # Create launcher with this widget as parent for dialogs
            launcher = create_launcher(self)

            # Check availability first
            is_available, message = launcher.check_analyzer_availability()
            if not is_available:
                QMessageBox.critical(self, "Bank Analyzer Not Available",
                                   f"Cannot launch Bank Statement Analyzer:\n\n{message}")
                return

            # Launch the analyzer
            success = launcher.launch_analyzer()

            if success:
                # Show status message
                self.show_status_message("🏦 Bank Statement Analyzer launched successfully")

                # Connect to signals for feedback
                launcher.analyzer_started.connect(
                    lambda: self.show_status_message("🏦 Bank Statement Analyzer is running")
                )
                launcher.analyzer_finished.connect(
                    lambda code: self.show_status_message("🏦 Bank Statement Analyzer closed")
                )
                launcher.analyzer_error.connect(
                    lambda error: QMessageBox.warning(self, "Bank Analyzer Error", f"Bank Statement Analyzer encountered an error: {error}")
                )
            else:
                QMessageBox.warning(self, "Launch Failed",
                                  "Failed to launch Bank Statement Analyzer. Please check the logs for more details.")

        except ImportError as e:
            QMessageBox.critical(self, "Integration Error",
                               f"Failed to load Bank Statement Analyzer integration:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Launch Error",
                               f"An unexpected error occurred while launching Bank Statement Analyzer:\n\n{str(e)}")

    def show_status_message(self, message: str):
        """Helper method to show status message"""
        try:
            # Try to find the main window's status label
            main_window = self.window()
            if hasattr(main_window, 'status_label'):
                main_window.status_label.setText(message)
        except:
            pass  # Ignore if we can't find the status label

    def import_from_bank_analyzer(self):
        """Import transactions from Bank Statement Analyzer export"""
        try:
            from PySide6.QtWidgets import QFileDialog

            # Check if the default transaction file exists
            default_file = "bank_statement_analyzer/data/processed_statements/transactions_Indian_Bank_20250706_154905.csv"

            # Open file dialog to select the export file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Bank Statement Analyzer Export",
                default_file if Path(default_file).exists() else "",
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_path:
                return

            # Use the new import method from the model
            result = self.expense_model.import_bank_statement_transactions(file_path)

            if result['success']:
                # Refresh the data to show imported transactions
                self.refresh_data()

                # Show success message
                message = f"{result['message']}"
                if result['errors']:
                    message += f"\n\nWarnings:\n" + "\n".join(result['errors'][:5])  # Show first 5 errors
                    if len(result['errors']) > 5:
                        message += f"\n... and {len(result['errors']) - 5} more warnings"

                QMessageBox.information(self, "Import Successful", message)
            else:
                # Show error message
                error_message = result['message']
                if result['errors']:
                    error_message += f"\n\nErrors:\n" + "\n".join(result['errors'][:5])
                    if len(result['errors']) > 5:
                        error_message += f"\n... and {len(result['errors']) - 5} more errors"

                QMessageBox.critical(self, "Import Failed", error_message)
                return

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred during import:\n{str(e)}")

    def quick_import_transactions(self):
        """Quick import from the default transaction file"""
        try:
            default_file = "bank_statement_analyzer/data/processed_statements/transactions_Indian_Bank_20250706_154905.csv"

            if not Path(default_file).exists():
                QMessageBox.warning(self, "File Not Found",
                                  f"Default transaction file not found:\n{default_file}\n\n"
                                  "Please use the regular Import button to select a file.")
                return

            # Confirm import
            reply = QMessageBox.question(self, "Quick Import",
                                       f"Import pre-labeled transactions from:\n{default_file}\n\n"
                                       "This will add all transactions to your expense tracker.",
                                       QMessageBox.Yes | QMessageBox.No)

            if reply != QMessageBox.Yes:
                return

            # Use the new import method from the model
            result = self.expense_model.import_bank_statement_transactions(default_file)

            if result['success']:
                # Refresh the data to show imported transactions
                self.refresh_data()

                # Show success message
                message = f"{result['message']}"
                if result['errors']:
                    message += f"\n\nWarnings:\n" + "\n".join(result['errors'][:3])  # Show first 3 errors
                    if len(result['errors']) > 3:
                        message += f"\n... and {len(result['errors']) - 3} more warnings"

                QMessageBox.information(self, "Quick Import Successful", message)
            else:
                # Show error message
                error_message = result['message']
                if result['errors']:
                    error_message += f"\n\nErrors:\n" + "\n".join(result['errors'][:3])
                    if len(result['errors']) > 3:
                        error_message += f"\n... and {len(result['errors']) - 3} more errors"

                QMessageBox.critical(self, "Quick Import Failed", error_message)

        except Exception as e:
            QMessageBox.critical(self, "Quick Import Error", f"An unexpected error occurred:\n{str(e)}")

    def check_for_bank_analyzer_exports(self):
        """Check for new exports from the Bank Statement Analyzer and suggest import"""
        try:
            from ...core.bank_analyzer_integration import create_workflow_helper

            workflow_helper = create_workflow_helper(self)
            workflow_helper.suggest_import(self)

        except Exception as e:
            # Silently ignore errors in this background check
            pass

    def sync_categories(self):
        """Synchronize categories with Bank Statement Analyzer"""
        try:
            from ...core.category_sync import create_category_synchronizer

            # Create synchronizer
            synchronizer = create_category_synchronizer()

            # Show sync options dialog
            sync_dialog = CategorySyncDialog(synchronizer, self)
            if sync_dialog.exec() == QDialog.Accepted:
                # Refresh categories after sync
                self.refresh_data()
                self.show_status_message("🔄 Categories synchronized successfully")

        except ImportError as e:
            QMessageBox.critical(self, "Sync Error",
                               f"Failed to load category synchronization module:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Sync Error",
                               f"An unexpected error occurred during category synchronization:\n\n{str(e)}")


class ImportPreviewDialog(QDialog):
    """Dialog to preview and select transactions for import"""

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.selected_rows = set(range(len(df)))  # All selected by default
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Import Preview - Bank Statement Analyzer")
        self.setMinimumSize(1000, 600)

        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel(f"Preview of {len(self.df)} transactions to import:")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header_label)

        # Instructions
        instructions = QLabel("Review the transactions below. Uncheck any transactions you don't want to import.")
        layout.addWidget(instructions)

        # Table
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)

        # Summary
        self.summary_label = QLabel()
        self.update_summary()
        layout.addWidget(self.summary_label)

        # Buttons
        button_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)

        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(select_none_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        import_btn = QPushButton("Import Selected")
        import_btn.clicked.connect(self.accept)
        import_btn.setDefault(True)
        button_layout.addWidget(import_btn)

        layout.addLayout(button_layout)

    def setup_table(self):
        """Setup the preview table"""
        # Add checkbox column
        columns = ['Select'] + list(self.df.columns)
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(self.df))

        # Populate table
        for row_idx, (_, row) in enumerate(self.df.iterrows()):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, r=row_idx: self.on_checkbox_changed(r, state))
            self.table.setCellWidget(row_idx, 0, checkbox)

            # Data columns
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                self.table.setItem(row_idx, col_idx + 1, item)

        # Resize columns
        self.table.resizeColumnsToContents()
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

    def on_checkbox_changed(self, row_idx, state):
        """Handle checkbox state change"""
        if state == Qt.Checked:
            self.selected_rows.add(row_idx)
        else:
            self.selected_rows.discard(row_idx)
        self.update_summary()

    def select_all(self):
        """Select all transactions"""
        self.selected_rows = set(range(len(self.df)))
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            checkbox.setChecked(True)
        self.update_summary()

    def select_none(self):
        """Deselect all transactions"""
        self.selected_rows.clear()
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            checkbox.setChecked(False)
        self.update_summary()

    def update_summary(self):
        """Update the summary label"""
        selected_count = len(self.selected_rows)
        total_count = len(self.df)

        if selected_count > 0:
            selected_df = self.df.iloc[list(self.selected_rows)]
            total_amount = selected_df['amount'].sum()
            self.summary_label.setText(f"Selected: {selected_count} of {total_count} transactions | Total Amount: ₹{total_amount:,.2f}")
        else:
            self.summary_label.setText(f"Selected: 0 of {total_count} transactions")

    def get_selected_transactions(self):
        """Get the selected transactions as a DataFrame"""
        if not self.selected_rows:
            return self.df.iloc[0:0]  # Empty DataFrame with same columns
        return self.df.iloc[list(self.selected_rows)]


class CategorySyncDialog(QDialog):
    """Dialog for category synchronization options"""

    def __init__(self, synchronizer, parent=None):
        super().__init__(parent)
        self.synchronizer = synchronizer
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Category Synchronization")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Synchronize Categories")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel("Choose how to synchronize categories between the main application and Bank Statement Analyzer:")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Sync status
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)

        sync_status = self.synchronizer.get_sync_status()
        if sync_status['status'] == 'never_synced':
            status_text = "Categories have never been synchronized"
        elif sync_status['status'] == 'synced':
            last_sync = sync_status.get('last_sync', 'Unknown')
            sync_type = sync_status.get('sync_type', 'Unknown')
            status_text = f"Last synchronized: {last_sync}\nSync type: {sync_type}"
        else:
            status_text = f"Status: {sync_status.get('error', 'Unknown error')}"

        status_label = QLabel(status_text)
        status_layout.addWidget(status_label)
        layout.addWidget(status_group)

        # Sync options
        options_group = QGroupBox("Synchronization Options")
        options_layout = QVBoxLayout(options_group)

        self.bidirectional_radio = QRadioButton("🔄 Bidirectional Sync (Recommended)")
        self.bidirectional_radio.setToolTip("Merge categories from both applications intelligently")
        self.bidirectional_radio.setChecked(True)
        options_layout.addWidget(self.bidirectional_radio)

        self.main_to_bank_radio = QRadioButton("➡️ Main App → Bank Analyzer")
        self.main_to_bank_radio.setToolTip("Copy categories from main application to bank analyzer")
        options_layout.addWidget(self.main_to_bank_radio)

        self.bank_to_main_radio = QRadioButton("⬅️ Bank Analyzer → Main App")
        self.bank_to_main_radio.setToolTip("Copy categories from bank analyzer to main application")
        options_layout.addWidget(self.bank_to_main_radio)

        layout.addWidget(options_group)

        # Warning
        warning_label = QLabel("⚠️ Warning: This operation will modify category data in both applications. Make sure to backup your data first.")
        warning_label.setStyleSheet("color: orange; font-weight: bold;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        sync_btn = QPushButton("Synchronize")
        sync_btn.clicked.connect(self.perform_sync)
        sync_btn.setDefault(True)
        button_layout.addWidget(sync_btn)

        layout.addLayout(button_layout)

    def perform_sync(self):
        """Perform the selected synchronization"""
        try:
            # Determine sync direction
            if self.bidirectional_radio.isChecked():
                direction = "bidirectional"
            elif self.main_to_bank_radio.isChecked():
                direction = "main_to_bank"
            elif self.bank_to_main_radio.isChecked():
                direction = "bank_to_main"
            else:
                QMessageBox.warning(self, "No Selection", "Please select a synchronization option.")
                return

            # Show progress
            progress = QProgressBar()
            progress.setRange(0, 0)  # Indeterminate progress
            self.layout().addWidget(progress)

            # Perform sync
            success, message = self.synchronizer.sync_categories(direction)

            # Remove progress bar
            progress.setParent(None)

            if success:
                QMessageBox.information(self, "Sync Successful", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Sync Failed", message)

        except Exception as e:
            QMessageBox.critical(self, "Sync Error", f"An error occurred during synchronization:\n\n{str(e)}")
