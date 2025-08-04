"""
Income Goal Tracker UI Widgets
Contains all UI components for the income goal tracking module
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QGroupBox, QSplitter, QTabWidget, QSpinBox, QDoubleSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QCheckBox, QProgressBar,
    QCalendarWidget, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette, QPainter, QBrush, QColor

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import calendar
import pandas as pd

from .models import IncomeRecord, GoalSetting, IncomeDataModel, WeeklyGoalTarget, MonthlyGoalSummary


class IncomeEntryDialog(QDialog):
    """Dialog for adding/editing daily income entries"""
    
    income_saved = Signal(dict)
    
    def __init__(self, data_model: IncomeDataModel, income: IncomeRecord = None, parent=None):
        super().__init__(parent)
        
        self.data_model = data_model
        self.income = income
        self.is_edit_mode = income is not None
        
        self.setup_ui()
        self.setup_connections()
        
        if self.is_edit_mode:
            self.populate_fields()
        else:
            # Set current goal for new entries
            current_goal = self.data_model.get_current_daily_goal()
            self.goal_spinbox.setValue(current_goal)
        
        self.setModal(True)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Income Entry" if self.is_edit_mode else "Add Income Entry")
        self.setMinimumSize(450, 600)
        self.resize(500, 650)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form layout
        form_frame = QFrame()
        form_frame.setObjectName("incomeFormFrame")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        
        # Date field
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setObjectName("incomeDateEdit")
        form_layout.addRow("Date:", self.date_edit)
        
        # Goal amount
        self.goal_spinbox = QDoubleSpinBox()
        self.goal_spinbox.setRange(0.0, 999999.99)
        self.goal_spinbox.setDecimals(2)
        self.goal_spinbox.setPrefix("₹ ")
        self.goal_spinbox.setObjectName("incomeGoalSpinbox")
        form_layout.addRow("Daily Goal:", self.goal_spinbox)
        
        # Income sources section
        sources_label = QLabel("Income Sources")
        sources_label.setObjectName("incomeSectionLabel")
        font = QFont()
        font.setBold(True)
        sources_label.setFont(font)
        form_layout.addRow("", sources_label)
        
        # Zomato
        self.zomato_spinbox = QDoubleSpinBox()
        self.zomato_spinbox.setRange(0.0, 999999.99)
        self.zomato_spinbox.setDecimals(2)
        self.zomato_spinbox.setPrefix("₹ ")
        self.zomato_spinbox.setObjectName("incomeZomatoSpinbox")
        form_layout.addRow("Zomato:", self.zomato_spinbox)
        
        # Swiggy
        self.swiggy_spinbox = QDoubleSpinBox()
        self.swiggy_spinbox.setRange(0.0, 999999.99)
        self.swiggy_spinbox.setDecimals(2)
        self.swiggy_spinbox.setPrefix("₹ ")
        self.swiggy_spinbox.setObjectName("incomeSwiggySpinbox")
        form_layout.addRow("Swiggy:", self.swiggy_spinbox)
        
        # Shadow Fax
        self.shadow_fax_spinbox = QDoubleSpinBox()
        self.shadow_fax_spinbox.setRange(0.0, 999999.99)
        self.shadow_fax_spinbox.setDecimals(2)
        self.shadow_fax_spinbox.setPrefix("₹ ")
        self.shadow_fax_spinbox.setObjectName("incomeShadowFaxSpinbox")
        form_layout.addRow("Shadow Fax:", self.shadow_fax_spinbox)

        # PC Repair
        self.pc_repair_spinbox = QDoubleSpinBox()
        self.pc_repair_spinbox.setRange(0.0, 999999.99)
        self.pc_repair_spinbox.setDecimals(2)
        self.pc_repair_spinbox.setPrefix("₹ ")
        self.pc_repair_spinbox.setObjectName("incomePCRepairSpinbox")
        form_layout.addRow("PC Repair:", self.pc_repair_spinbox)

        # Settings
        self.settings_spinbox = QDoubleSpinBox()
        self.settings_spinbox.setRange(0.0, 999999.99)
        self.settings_spinbox.setDecimals(2)
        self.settings_spinbox.setPrefix("₹ ")
        self.settings_spinbox.setObjectName("incomeSettingsSpinbox")
        form_layout.addRow("Settings:", self.settings_spinbox)

        # YouTube
        self.youtube_spinbox = QDoubleSpinBox()
        self.youtube_spinbox.setRange(0.0, 999999.99)
        self.youtube_spinbox.setDecimals(2)
        self.youtube_spinbox.setPrefix("₹ ")
        self.youtube_spinbox.setObjectName("incomeYouTubeSpinbox")
        form_layout.addRow("YouTube:", self.youtube_spinbox)

        # GP Links
        self.gp_links_spinbox = QDoubleSpinBox()
        self.gp_links_spinbox.setRange(0.0, 999999.99)
        self.gp_links_spinbox.setDecimals(2)
        self.gp_links_spinbox.setPrefix("₹ ")
        self.gp_links_spinbox.setObjectName("incomeGPLinksSpinbox")
        form_layout.addRow("GP Links:", self.gp_links_spinbox)

        # ID Sales
        self.id_sales_spinbox = QDoubleSpinBox()
        self.id_sales_spinbox.setRange(0.0, 999999.99)
        self.id_sales_spinbox.setDecimals(2)
        self.id_sales_spinbox.setPrefix("₹ ")
        self.id_sales_spinbox.setObjectName("incomeIDSalesSpinbox")
        form_layout.addRow("ID Sales:", self.id_sales_spinbox)

        # Other sources
        self.other_spinbox = QDoubleSpinBox()
        self.other_spinbox.setRange(0.0, 999999.99)
        self.other_spinbox.setDecimals(2)
        self.other_spinbox.setPrefix("₹ ")
        self.other_spinbox.setObjectName("incomeOtherSpinbox")
        form_layout.addRow("Other Sources:", self.other_spinbox)

        # Extra Work
        self.extra_work_spinbox = QDoubleSpinBox()
        self.extra_work_spinbox.setRange(0.0, 999999.99)
        self.extra_work_spinbox.setDecimals(2)
        self.extra_work_spinbox.setPrefix("₹ ")
        self.extra_work_spinbox.setObjectName("incomeExtraWorkSpinbox")
        form_layout.addRow("Extra Work:", self.extra_work_spinbox)
        
        # Total earned (calculated, read-only)
        self.total_label = QLabel("₹ 0.00")
        self.total_label.setObjectName("incomeTotalLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.total_label.setFont(font)
        form_layout.addRow("Total Earned:", self.total_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("incomeProgressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        form_layout.addRow("Progress:", self.progress_bar)
        
        # Status
        self.status_label = QLabel("Pending")
        self.status_label.setObjectName("incomeStatusLabel")
        form_layout.addRow("Status:", self.status_label)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes about today's income...")
        self.notes_edit.setObjectName("incomeNotesEdit")
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addWidget(form_frame)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.setObjectName("incomeDialogButtonBox")
        layout.addWidget(button_box)
        
        # Store references
        self.button_box = button_box
    
    def setup_connections(self):
        """Setup signal connections"""
        self.button_box.accepted.connect(self.save_income)
        self.button_box.rejected.connect(self.reject)
        
        # Connect spinboxes to update totals
        for spinbox in [self.zomato_spinbox, self.swiggy_spinbox,
                       self.shadow_fax_spinbox, self.pc_repair_spinbox,
                       self.settings_spinbox, self.youtube_spinbox,
                       self.gp_links_spinbox, self.id_sales_spinbox,
                       self.other_spinbox, self.extra_work_spinbox, self.goal_spinbox]:
            spinbox.valueChanged.connect(self.update_totals)
    
    def populate_fields(self):
        """Populate fields with existing income data"""
        if not self.income:
            return
        
        # Set date
        if isinstance(self.income.date, date):
            self.date_edit.setDate(QDate(self.income.date))
        
        # Set amounts
        self.goal_spinbox.setValue(self.income.goal_inc)
        self.zomato_spinbox.setValue(self.income.zomato)
        self.swiggy_spinbox.setValue(self.income.swiggy)
        self.shadow_fax_spinbox.setValue(self.income.shadow_fax)
        self.pc_repair_spinbox.setValue(getattr(self.income, 'pc_repair', 0.0))
        self.settings_spinbox.setValue(getattr(self.income, 'settings', 0.0))
        self.youtube_spinbox.setValue(getattr(self.income, 'youtube', 0.0))
        self.gp_links_spinbox.setValue(getattr(self.income, 'gp_links', 0.0))
        self.id_sales_spinbox.setValue(getattr(self.income, 'id_sales', 0.0))
        self.other_spinbox.setValue(self.income.other_sources)
        self.extra_work_spinbox.setValue(getattr(self.income, 'extra_work', 0.0))
        self.notes_edit.setPlainText(str(self.income.notes) if self.income.notes else "")
        
        # Update calculated fields
        self.update_totals()
    
    def update_totals(self):
        """Update calculated totals and progress"""
        # Calculate total from all sources
        total = (self.zomato_spinbox.value() + self.swiggy_spinbox.value() +
                self.shadow_fax_spinbox.value() + self.pc_repair_spinbox.value() +
                self.settings_spinbox.value() + self.youtube_spinbox.value() +
                self.gp_links_spinbox.value() + self.id_sales_spinbox.value() +
                self.other_spinbox.value() + self.extra_work_spinbox.value())

        self.total_label.setText(f"₹ {total:.2f}")
        
        # Calculate progress
        goal = self.goal_spinbox.value()
        if goal > 0:
            progress = min(100, (total / goal) * 100)
            self.progress_bar.setValue(int(progress))
        else:
            self.progress_bar.setValue(0)
        
        # Update status
        if total == 0:
            status = "Pending"
            color = "#999999"
        elif total >= goal:
            if total > goal:
                status = "Exceeded"
                color = "#00aa00"
            else:
                status = "Completed"
                color = "#0e639c"
        else:
            status = "In Progress"
            color = "#ff8800"
        
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def save_income(self):
        """Save the income record"""
        try:
            # Create income record
            income_data = IncomeRecord(
                id=self.income.id if self.is_edit_mode else None,
                date=self.date_edit.date().toPython(),
                zomato=self.zomato_spinbox.value(),
                swiggy=self.swiggy_spinbox.value(),
                shadow_fax=self.shadow_fax_spinbox.value(),
                pc_repair=self.pc_repair_spinbox.value(),
                settings=self.settings_spinbox.value(),
                youtube=self.youtube_spinbox.value(),
                gp_links=self.gp_links_spinbox.value(),
                id_sales=self.id_sales_spinbox.value(),
                other_sources=self.other_spinbox.value(),
                extra_work=self.extra_work_spinbox.value(),
                goal_inc=self.goal_spinbox.value(),
                notes=self.notes_edit.toPlainText()
            )
            
            # Validate
            errors = income_data.validate()
            if errors:
                QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                return
            
            # Save to data model
            if self.is_edit_mode:
                success = self.data_model.update_income_record(self.income.id, income_data)
            else:
                success = self.data_model.add_income_record(income_data)
            
            if success:
                self.income_saved.emit(income_data.to_dict())
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save income record")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")


class QuickIncomeEntryDialog(QDialog):
    """Streamlined quick entry dialog for fast income logging"""

    income_saved = Signal(dict)

    def __init__(self, data_model: IncomeDataModel, parent=None):
        super().__init__(parent)

        self.data_model = data_model
        self.income_model = data_model  # Alias for compatibility
        self.setup_ui()
        self.setup_connections()

        # Load today's existing data if available
        self.load_existing_data()

        self.setModal(True)

    def setup_ui(self):
        """Setup streamlined UI for quick entry"""
        self.setWindowTitle("Quick Income Entry - Today")
        self.setMinimumSize(400, 500)
        self.resize(450, 550)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header with today's date
        header_frame = QFrame()
        header_frame.setObjectName("quickEntryHeader")
        header_layout = QVBoxLayout(header_frame)

        date_label = QLabel(f"Quick Entry for {date.today().strftime('%A, %B %d, %Y')}")
        date_label.setObjectName("quickEntryDateLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        date_label.setFont(font)
        date_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(date_label)

        layout.addWidget(header_frame)

        # Quick source buttons in a grid
        sources_frame = QGroupBox("Select Income Source")
        sources_frame.setObjectName("quickEntrySourcesFrame")
        sources_layout = QGridLayout(sources_frame)

        # Create quick source buttons
        self.source_buttons = {}
        sources = [
            ("zomato", "Zomato", 0, 0),
            ("swiggy", "Swiggy", 0, 1),
            ("shadow_fax", "Shadow Fax", 1, 0),
            ("pc_repair", "PC Repair", 1, 1),
            ("settings", "Settings", 2, 0),
            ("youtube", "YouTube", 2, 1),
            ("gp_links", "GP Links", 3, 0),
            ("id_sales", "ID Sales", 3, 1),
            ("extra_work", "Extra Work", 4, 0),
            ("other", "Other", 4, 1)
        ]

        for source_key, source_name, row, col in sources:
            btn = QPushButton(source_name)
            btn.setObjectName("quickEntrySourceButton")
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, s=source_key: self.select_source(s))
            self.source_buttons[source_key] = btn
            sources_layout.addWidget(btn, row, col)

        layout.addWidget(sources_frame)

        # Amount entry section (initially hidden)
        self.amount_frame = QGroupBox("Enter Amount")
        self.amount_frame.setObjectName("quickEntryAmountFrame")
        self.amount_frame.setVisible(False)
        amount_layout = QVBoxLayout(self.amount_frame)

        self.selected_source_label = QLabel("")
        self.selected_source_label.setObjectName("quickEntrySelectedSource")
        font = QFont()
        font.setBold(True)
        self.selected_source_label.setFont(font)
        self.selected_source_label.setAlignment(Qt.AlignCenter)
        amount_layout.addWidget(self.selected_source_label)

        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.0, 99999.99)
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setPrefix("₹ ")
        self.amount_spinbox.setObjectName("quickEntryAmountSpinbox")
        self.amount_spinbox.setMinimumHeight(40)
        font = QFont()
        font.setPointSize(14)
        self.amount_spinbox.setFont(font)
        amount_layout.addWidget(self.amount_spinbox)

        # Quick amount buttons
        quick_amounts_layout = QHBoxLayout()
        quick_amounts = [50, 100, 200, 500, 1000]
        for amount in quick_amounts:
            btn = QPushButton(f"₹{amount}")
            btn.setObjectName("quickAmountButton")
            btn.clicked.connect(lambda checked, a=amount: self.set_quick_amount(a))
            quick_amounts_layout.addWidget(btn)

        amount_layout.addLayout(quick_amounts_layout)

        layout.addWidget(self.amount_frame)

        # Current total display
        self.total_frame = QGroupBox("Today's Total")
        self.total_frame.setObjectName("quickEntryTotalFrame")
        total_layout = QVBoxLayout(self.total_frame)

        self.total_label = QLabel("₹0.00")
        self.total_label.setObjectName("quickEntryTotalLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        self.total_label.setFont(font)
        self.total_label.setAlignment(Qt.AlignCenter)
        total_layout.addWidget(self.total_label)

        layout.addWidget(self.total_frame)

        # Button box
        button_layout = QHBoxLayout()

        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("quickEntryBackButton")
        self.back_button.setVisible(False)
        self.back_button.clicked.connect(self.go_back)
        button_layout.addWidget(self.back_button)

        button_layout.addStretch()

        self.save_button = QPushButton("Save & Add More")
        self.save_button.setObjectName("quickEntrySaveButton")
        self.save_button.setVisible(False)
        self.save_button.clicked.connect(self.save_and_continue)
        button_layout.addWidget(self.save_button)

        self.done_button = QPushButton("Done")
        self.done_button.setObjectName("quickEntryDoneButton")
        self.done_button.clicked.connect(self.finish_entry)
        button_layout.addWidget(self.done_button)

        layout.addLayout(button_layout)

        self.selected_source = None

    def setup_connections(self):
        """Setup signal connections"""
        self.amount_spinbox.valueChanged.connect(self.update_preview)

    def load_existing_data(self):
        """Load existing data for today"""
        try:
            today_record = self.income_model.get_income_record_by_date(date.today())
            if today_record:
                total = today_record.earned
                self.total_label.setText(f"₹{total:.2f}")
        except Exception as e:
            print(f"Error loading existing data: {e}")

    def select_source(self, source_key: str):
        """Select an income source"""
        self.selected_source = source_key

        source_names = {
            "zomato": "Zomato",
            "swiggy": "Swiggy",
            "shadow_fax": "Shadow Fax",
            "pc_repair": "PC Repair",
            "settings": "Settings",
            "youtube": "YouTube",
            "gp_links": "GP Links",
            "id_sales": "ID Sales",
            "extra_work": "Extra Work",
            "other": "Other Sources"
        }

        self.selected_source_label.setText(f"Adding earnings from {source_names[source_key]}")
        self.amount_frame.setVisible(True)
        self.back_button.setVisible(True)
        self.save_button.setVisible(True)

        # Focus on amount input
        self.amount_spinbox.setFocus()
        self.amount_spinbox.selectAll()

    def set_quick_amount(self, amount: float):
        """Set a quick amount"""
        self.amount_spinbox.setValue(amount)

    def update_preview(self):
        """Update the preview of total"""
        # This could show a preview of what the new total would be
        pass

    def go_back(self):
        """Go back to source selection"""
        self.selected_source = None
        self.amount_frame.setVisible(False)
        self.back_button.setVisible(False)
        self.save_button.setVisible(False)
        self.amount_spinbox.setValue(0.0)

    def save_and_continue(self):
        """Save current entry and continue adding more"""
        if self.save_current_entry():
            self.go_back()

    def finish_entry(self):
        """Finish the quick entry process"""
        if self.selected_source and self.amount_spinbox.value() > 0:
            if self.save_current_entry():
                self.accept()
        else:
            self.accept()

    def save_current_entry(self) -> bool:
        """Save the current entry"""
        if not self.selected_source or self.amount_spinbox.value() <= 0:
            return False

        try:
            amount = self.amount_spinbox.value()

            # Get or create today's record
            today_record = self.income_model.get_or_create_today_record()

            # Add to the specific source
            if self.selected_source == "zomato":
                today_record.zomato += amount
            elif self.selected_source == "swiggy":
                today_record.swiggy += amount
            elif self.selected_source == "shadow_fax":
                today_record.shadow_fax += amount
            elif self.selected_source == "pc_repair":
                today_record.pc_repair += amount
            elif self.selected_source == "settings":
                today_record.settings += amount
            elif self.selected_source == "youtube":
                today_record.youtube += amount
            elif self.selected_source == "gp_links":
                today_record.gp_links += amount
            elif self.selected_source == "id_sales":
                today_record.id_sales += amount
            elif self.selected_source == "extra_work":
                today_record.extra_work += amount
            elif self.selected_source == "other":
                today_record.other_sources += amount

            # Recalculate totals
            today_record.calculate_totals()

            # Save the record
            existing_record = self.income_model.get_income_record_by_date(date.today())
            if existing_record:
                success = self.income_model.update_income_record(existing_record.id, today_record)
            else:
                success = self.income_model.add_income_record(today_record)

            if success:
                self.income_saved.emit(today_record.to_dict())
                # Update total display
                self.total_label.setText(f"₹{today_record.earned:.2f}")
                return True
            else:
                QMessageBox.critical(self, "Error", "Failed to save income record")
                return False

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return False


class StylishIncomeVisualizationWidget(QWidget):
    """Stylish widget for income visualization with circular progress and charts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_amount = 0.0
        self.target_amount = 1000.0
        self.setup_ui()

    def setup_ui(self):
        """Setup the visualization UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Main visualization frame - EXPANDED: Better sizing for chart visibility
        viz_frame = QFrame()
        viz_frame.setObjectName("incomeVizFrame")
        viz_frame.setMinimumHeight(400)  # Increased from 200px to 400px for better chart visibility
        # Remove maximum height constraint to allow natural expansion
        viz_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        viz_layout = QHBoxLayout(viz_frame)
        viz_layout.setSpacing(20)  # Add spacing for better layout
        viz_layout.setContentsMargins(15, 15, 15, 15)  # Add margins for better appearance

        # Circular progress section
        progress_section = self.create_circular_progress()
        viz_layout.addWidget(progress_section, 1)

        # Stats section
        stats_section = self.create_stats_section()
        viz_layout.addWidget(stats_section, 1)

        layout.addWidget(viz_frame)

        # Source breakdown
        breakdown_frame = self.create_source_breakdown()
        layout.addWidget(breakdown_frame)

    def create_circular_progress(self):
        """Create circular progress indicator"""
        frame = QFrame()
        frame.setObjectName("circularProgressFrame")
        layout = QVBoxLayout(frame)

        # Progress circle (using a custom painted widget would be better, but using labels for now)
        progress_container = QFrame()
        progress_container.setMinimumSize(150, 150)
        progress_container.setMaximumSize(150, 150)
        progress_container.setObjectName("progressCircle")

        # Progress text overlay
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setAlignment(Qt.AlignCenter)

        self.progress_percentage_label = QLabel("0%")
        self.progress_percentage_label.setObjectName("progressPercentage")
        self.progress_percentage_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.progress_percentage_label.setFont(font)

        self.progress_status_label = QLabel("Pending")
        self.progress_status_label.setObjectName("progressStatus")
        self.progress_status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.progress_status_label.setFont(font)

        progress_layout.addWidget(self.progress_percentage_label)
        progress_layout.addWidget(self.progress_status_label)

        layout.addWidget(progress_container, 0, Qt.AlignCenter)

        # Amount labels
        self.current_amount_label = QLabel("₹0.00")
        self.current_amount_label.setObjectName("currentAmountLabel")
        self.current_amount_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.current_amount_label.setFont(font)

        self.target_amount_label = QLabel("of ₹1000.00")
        self.target_amount_label.setObjectName("targetAmountLabel")
        self.target_amount_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.current_amount_label)
        layout.addWidget(self.target_amount_label)

        return frame

    def create_stats_section(self):
        """Create statistics section"""
        frame = QFrame()
        frame.setObjectName("statsFrame")
        layout = QVBoxLayout(frame)

        # Title
        title = QLabel("Today's Progress")
        title.setObjectName("statsTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title.setFont(font)
        layout.addWidget(title)

        # Stats grid
        stats_grid = QGridLayout()

        # Remaining amount
        self.remaining_label = QLabel("₹1000.00")
        self.remaining_label.setObjectName("remainingLabel")
        stats_grid.addWidget(QLabel("Remaining:"), 0, 0)
        stats_grid.addWidget(self.remaining_label, 0, 1)

        # Extra amount
        self.extra_label = QLabel("₹0.00")
        self.extra_label.setObjectName("extraLabel")
        stats_grid.addWidget(QLabel("Extra:"), 1, 0)
        stats_grid.addWidget(self.extra_label, 1, 1)

        # Time remaining
        self.time_remaining_label = QLabel("Full day")
        self.time_remaining_label.setObjectName("timeRemainingLabel")
        stats_grid.addWidget(QLabel("Time left:"), 2, 0)
        stats_grid.addWidget(self.time_remaining_label, 2, 1)

        layout.addLayout(stats_grid)
        layout.addStretch()

        return frame

    def create_source_breakdown(self):
        """Create income source breakdown"""
        frame = QFrame()
        frame.setObjectName("sourceBreakdownFrame")
        layout = QVBoxLayout(frame)

        # Title
        title = QLabel("Income Sources")
        title.setObjectName("sourceTitle")
        font = QFont()
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Sources grid
        self.sources_layout = QGridLayout()
        layout.addLayout(self.sources_layout)

        return frame

    def update_visualization(self, current: float, target: float, sources: dict = None):
        """Update the visualization with new data"""
        self.current_amount = current
        self.target_amount = target

        # Calculate progress
        progress = (current / target * 100) if target > 0 else 0
        progress = min(100, progress)

        # Update progress circle
        self.progress_percentage_label.setText(f"{progress:.0f}%")
        self.current_amount_label.setText(f"₹{current:.2f}")
        self.target_amount_label.setText(f"of ₹{target:.2f}")

        # Update status
        if current == 0:
            status = "Pending"
            color = "#999999"
        elif current >= target:
            status = "Completed" if current == target else "Exceeded"
            color = "#00aa00"
        else:
            status = "In Progress"
            color = "#ff8800"

        self.progress_status_label.setText(status)
        self.progress_status_label.setStyleSheet(f"color: {color};")

        # Update stats
        remaining = max(0, target - current)
        extra = max(0, current - target)

        self.remaining_label.setText(f"₹{remaining:.2f}")
        self.extra_label.setText(f"₹{extra:.2f}")

        # Update time remaining (simplified)
        now = datetime.now()
        end_of_day = now.replace(hour=23, minute=59, second=59)
        time_left = end_of_day - now
        hours_left = time_left.seconds // 3600
        self.time_remaining_label.setText(f"{hours_left}h left")

        # Update sources breakdown
        if sources:
            self.update_sources_breakdown(sources)

    def update_sources_breakdown(self, sources: dict):
        """Update the sources breakdown display"""
        # Clear existing items
        for i in reversed(range(self.sources_layout.count())):
            self.sources_layout.itemAt(i).widget().setParent(None)

        # Add source items
        row = 0
        for source, amount in sources.items():
            if amount > 0:
                source_label = QLabel(f"{source}:")
                amount_label = QLabel(f"₹{amount:.2f}")
                amount_label.setAlignment(Qt.AlignRight)

                self.sources_layout.addWidget(source_label, row, 0)
                self.sources_layout.addWidget(amount_label, row, 1)
                row += 1


class IncomeProgressWidget(QWidget):
    """Widget showing income progress visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the progress widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Today's Progress")
        title_label.setObjectName("incomeProgressTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Progress frame
        progress_frame = QFrame()
        progress_frame.setObjectName("incomeProgressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        
        # Goal vs Earned
        self.goal_label = QLabel("Goal: ₹0.00")
        self.goal_label.setObjectName("incomeGoalLabel")
        progress_layout.addWidget(self.goal_label)
        
        self.earned_label = QLabel("Earned: ₹0.00")
        self.earned_label.setObjectName("incomeEarnedLabel")
        progress_layout.addWidget(self.earned_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("incomeMainProgressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Pending")
        self.status_label.setObjectName("incomeMainStatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.status_label.setFont(font)
        progress_layout.addWidget(self.status_label)
        
        # Remaining amount
        self.remaining_label = QLabel("Remaining: ₹0.00")
        self.remaining_label.setObjectName("incomeRemainingLabel")
        self.remaining_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.remaining_label)
        
        layout.addWidget(progress_frame)
        layout.addStretch()
    
    def update_progress(self, income_data: Dict[str, Any]):
        """Update progress display with income data"""
        goal = income_data.get('goal_inc', 0)
        earned = income_data.get('earned', 0)
        status = income_data.get('status', 'Pending')
        
        self.goal_label.setText(f"Goal: ₹{goal:.2f}")
        self.earned_label.setText(f"Earned: ₹{earned:.2f}")
        
        # Calculate progress
        if goal > 0:
            progress = min(100, (earned / goal) * 100)
            self.progress_bar.setValue(int(progress))
            self.progress_bar.setFormat(f"{progress:.1f}%")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0%")
        
        # Update status with color
        self.status_label.setText(status)
        if status == "Exceeded":
            color = "#00aa00"
        elif status == "Completed":
            color = "#0e639c"
        elif status == "In Progress":
            color = "#ff8800"
        else:
            color = "#999999"
        
        self.status_label.setStyleSheet(f"color: {color};")
        
        # Update remaining
        remaining = max(0, goal - earned)
        if remaining > 0:
            self.remaining_label.setText(f"Remaining: ₹{remaining:.2f}")
            self.remaining_label.setStyleSheet("color: #ff8800;")
        else:
            extra = earned - goal
            if extra > 0:
                self.remaining_label.setText(f"Extra: ₹{extra:.2f}")
                self.remaining_label.setStyleSheet("color: #00aa00;")
            else:
                self.remaining_label.setText("Goal Achieved!")
                self.remaining_label.setStyleSheet("color: #0e639c;")


class IncomeStatsWidget(QWidget):
    """Widget displaying income statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the statistics UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Income Statistics")
        title_label.setObjectName("incomeStatsTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Stats grid
        stats_frame = QFrame()
        stats_frame.setObjectName("incomeStatsFrame")
        stats_layout = QGridLayout(stats_frame)
        
        # Create stat labels
        self.total_earned_label = QLabel("₹0.00")
        self.average_daily_label = QLabel("₹0.00")
        self.this_month_label = QLabel("₹0.00")
        self.achievement_rate_label = QLabel("0%")
        self.streak_label = QLabel("0 days")
        self.best_day_label = QLabel("₹0.00")
        
        # Style stat labels
        for label in [self.total_earned_label, self.average_daily_label, 
                     self.this_month_label, self.achievement_rate_label,
                     self.streak_label, self.best_day_label]:
            label.setObjectName("incomeStatValue")
            font = QFont()
            font.setBold(True)
            font.setPointSize(11)
            label.setFont(font)
            label.setAlignment(Qt.AlignCenter)
        
        # Add to layout
        stats_layout.addWidget(QLabel("Total Earned:"), 0, 0)
        stats_layout.addWidget(self.total_earned_label, 0, 1)
        
        stats_layout.addWidget(QLabel("Average Daily:"), 1, 0)
        stats_layout.addWidget(self.average_daily_label, 1, 1)
        
        stats_layout.addWidget(QLabel("This Month:"), 2, 0)
        stats_layout.addWidget(self.this_month_label, 2, 1)
        
        stats_layout.addWidget(QLabel("Achievement Rate:"), 3, 0)
        stats_layout.addWidget(self.achievement_rate_label, 3, 1)
        
        stats_layout.addWidget(QLabel("Current Streak:"), 4, 0)
        stats_layout.addWidget(self.streak_label, 4, 1)
        
        stats_layout.addWidget(QLabel("Best Day:"), 5, 0)
        stats_layout.addWidget(self.best_day_label, 5, 1)
        
        layout.addWidget(stats_frame)
        layout.addStretch()
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update the statistics display"""
        self.total_earned_label.setText(f"₹{stats.get('total_earned', 0):.2f}")
        self.average_daily_label.setText(f"₹{stats.get('average_daily', 0):.2f}")
        self.this_month_label.setText(f"₹{stats.get('this_month_earned', 0):.2f}")
        self.achievement_rate_label.setText(f"{stats.get('goal_achievement_rate', 0):.1f}%")
        self.streak_label.setText(f"{stats.get('streak_days', 0)} days")
        self.best_day_label.setText(f"₹{stats.get('best_day_amount', 0):.2f}")


class MonthlyViewWidget(QWidget):
    """Widget showing monthly income overview with base income structure"""

    def __init__(self, income_model: IncomeDataModel, parent=None):
        super().__init__(parent)
        self.income_model = income_model
        self.current_month = date.today().replace(day=1)
        self.setup_ui()
        self.setup_connections()
        self.refresh_data()

    def setup_ui(self):
        """Setup the monthly view UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header with navigation
        header_layout = QHBoxLayout()

        self.prev_month_btn = QPushButton("◀ Previous")
        self.prev_month_btn.setObjectName("incomeMonthNavButton")
        header_layout.addWidget(self.prev_month_btn)

        self.month_label = QLabel("Current Month")
        self.month_label.setObjectName("incomeMonthLabel")
        self.month_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.month_label.setFont(font)
        header_layout.addWidget(self.month_label)

        self.next_month_btn = QPushButton("Next ▶")
        self.next_month_btn.setObjectName("incomeMonthNavButton")
        header_layout.addWidget(self.next_month_btn)

        layout.addLayout(header_layout)

        # Monthly summary cards with base vs bonus structure
        summary_layout = QHBoxLayout()

        # Total earned card
        total_card = QFrame()
        total_card.setObjectName("incomeMonthlyCard")
        total_layout = QVBoxLayout(total_card)
        self.total_earned_label = QLabel("₹0")
        self.total_earned_label.setObjectName("incomeMonthlyTotal")
        total_layout.addWidget(self.total_earned_label)
        total_layout.addWidget(QLabel("Total Earned"))
        summary_layout.addWidget(total_card)

        # Base income achieved card
        base_card = QFrame()
        base_card.setObjectName("incomeMonthlyCard")
        base_layout = QVBoxLayout(base_card)
        self.base_achieved_label = QLabel("₹0")
        self.base_achieved_label.setObjectName("incomeMonthlyBase")
        base_layout.addWidget(self.base_achieved_label)
        base_layout.addWidget(QLabel("Base Achieved"))
        summary_layout.addWidget(base_card)

        # Bonus earned card
        bonus_card = QFrame()
        bonus_card.setObjectName("incomeMonthlyCard")
        bonus_layout = QVBoxLayout(bonus_card)
        self.bonus_earned_label = QLabel("₹0")
        self.bonus_earned_label.setObjectName("incomeMonthlyBonus")
        self.bonus_earned_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        bonus_layout.addWidget(self.bonus_earned_label)
        bonus_layout.addWidget(QLabel("Bonus Earned"))
        summary_layout.addWidget(bonus_card)

        # Base progress card
        progress_card = QFrame()
        progress_card.setObjectName("incomeMonthlyCard")
        progress_layout = QVBoxLayout(progress_card)
        self.base_progress_label = QLabel("0%")
        self.base_progress_label.setObjectName("incomeMonthlyProgress")
        progress_layout.addWidget(self.base_progress_label)
        progress_layout.addWidget(QLabel("Base Progress"))
        summary_layout.addWidget(progress_card)

        layout.addLayout(summary_layout)

        # Monthly base progress bar
        progress_frame = QGroupBox("Monthly Base Income Progress")
        progress_layout = QVBoxLayout(progress_frame)

        self.monthly_progress = QProgressBar()
        self.monthly_progress.setObjectName("incomeMonthlyProgressBar")
        self.monthly_progress.setTextVisible(True)
        self.monthly_progress.setMinimumHeight(30)
        # Theme-aware styling will be applied later
        self.monthly_progress.setObjectName("monthlyProgressBar")
        progress_layout.addWidget(self.monthly_progress)

        # Base target info
        self.base_target_info_label = QLabel("Monthly Base Target: ₹0 | Days Remaining: 0")
        self.base_target_info_label.setAlignment(Qt.AlignCenter)
        self.base_target_info_label.setStyleSheet("color: #666; font-size: 10px;")
        progress_layout.addWidget(self.base_target_info_label)

        layout.addWidget(progress_frame)

        # Weekly breakdown
        self.weekly_frame = QFrame()
        self.weekly_frame.setObjectName("incomeWeeklyFrame")
        self.weekly_layout = QVBoxLayout(self.weekly_frame)
        layout.addWidget(self.weekly_frame)

        layout.addStretch()

    def setup_connections(self):
        """Setup signal connections"""
        self.prev_month_btn.clicked.connect(self.previous_month)
        self.next_month_btn.clicked.connect(self.next_month)

    def previous_month(self):
        """Navigate to previous month"""
        if self.current_month.month == 1:
            self.current_month = self.current_month.replace(year=self.current_month.year - 1, month=12)
        else:
            self.current_month = self.current_month.replace(month=self.current_month.month - 1)
        self.refresh_data()

    def next_month(self):
        """Navigate to next month"""
        if self.current_month.month == 12:
            self.current_month = self.current_month.replace(year=self.current_month.year + 1, month=1)
        else:
            self.current_month = self.current_month.replace(month=self.current_month.month + 1)
        self.refresh_data()

    def refresh_data(self):
        """Refresh monthly data with base income structure"""
        try:
            # Update header
            self.month_label.setText(self.current_month.strftime('%B %Y'))

            # Get monthly base vs bonus summary
            monthly_summary = self.get_monthly_base_vs_bonus_summary()

            # Update summary cards
            total_earned = monthly_summary['total_earned']
            total_base_target = monthly_summary['total_base_target']
            total_base_achieved = monthly_summary['total_base_achieved']
            total_bonus = monthly_summary['total_bonus']

            # Calculate base progress
            base_progress = (total_base_achieved / total_base_target * 100) if total_base_target > 0 else 0

            # Update labels
            self.total_earned_label.setText(f"₹{total_earned:,.0f}")
            self.base_achieved_label.setText(f"₹{total_base_achieved:,.0f}")
            self.bonus_earned_label.setText(f"₹{total_bonus:,.0f}")
            self.base_progress_label.setText(f"{base_progress:.1f}%")

            # Update progress bar
            self.monthly_progress.setValue(int(base_progress))
            self.monthly_progress.setFormat(f"{base_progress:.1f}% Base (₹{total_base_achieved:,.0f}/₹{total_base_target:,.0f}) + ₹{total_bonus:,.0f} Bonus")

            # Update base target info
            days_in_month = calendar.monthrange(self.current_month.year, self.current_month.month)[1]
            today = date.today()
            if self.current_month.year == today.year and self.current_month.month == today.month:
                days_remaining = days_in_month - today.day + 1
            else:
                days_remaining = days_in_month

            self.base_target_info_label.setText(f"Monthly Base Target: ₹{total_base_target:,.0f} | Days in Month: {days_in_month}")

            # Update weekly breakdown
            self.update_weekly_breakdown(monthly_summary['weekly_breakdown'])

        except Exception as e:
            print(f"Error refreshing monthly data: {e}")

    def get_monthly_base_vs_bonus_summary(self) -> Dict[str, Any]:
        """Get monthly summary with base vs bonus breakdown - OPTIMIZED VERSION"""
        try:
            # Calculate start and end dates for the month
            start_date = self.current_month
            if self.current_month.month == 12:
                end_date = self.current_month.replace(year=self.current_month.year + 1, month=1) - timedelta(days=1)
            else:
                end_date = self.current_month.replace(month=self.current_month.month + 1) - timedelta(days=1)

            # Get income records for the month
            df = self.income_model.get_income_records_by_date_range(start_date, end_date)

            monthly_summary = {
                'month_date': self.current_month,
                'total_earned': 0.0,
                'total_base_target': 0.0,
                'total_base_achieved': 0.0,
                'total_bonus': 0.0,
                'weekly_breakdown': []
            }

            if not df.empty:
                # Use vectorized calculation for better performance
                df_with_bonus = self.income_model.calculate_bulk_bonus_income(df)

                # Check if bonus calculation was successful
                if 'base_target' in df_with_bonus.columns:
                    # Calculate totals using pandas aggregation (much faster than loops)
                    monthly_summary['total_earned'] = float(df_with_bonus['earned'].sum())
                    monthly_summary['total_base_target'] = float(df_with_bonus['base_target'].sum())
                    monthly_summary['total_base_achieved'] = float(df_with_bonus['base_achieved'].sum())
                    monthly_summary['total_bonus'] = float(df_with_bonus['bonus_amount'].sum())
                else:
                    # Fallback calculation if bulk bonus calculation failed
                    monthly_summary['total_earned'] = float(df_with_bonus['earned'].sum())
                    # Calculate base targets manually
                    settings = self.income_model.get_current_base_income_settings()
                    for _, row in df_with_bonus.iterrows():
                        date_obj = pd.to_datetime(row['date']).date()
                        day_of_week = date_obj.weekday()
                        if day_of_week == 5:  # Saturday
                            base_target = settings.saturday_base
                        elif day_of_week == 6:  # Sunday
                            base_target = settings.sunday_base
                        else:  # Weekday
                            base_target = settings.weekday_base

                        earned = float(row['earned'])
                        monthly_summary['total_base_target'] += base_target
                        monthly_summary['total_base_achieved'] += min(earned, base_target)
                        monthly_summary['total_bonus'] += max(0.0, earned - base_target)
            else:
                # No data for this month - calculate theoretical base targets
                settings = self.income_model.get_current_base_income_settings()
                current_date = start_date
                while current_date <= end_date:
                    day_of_week = current_date.weekday()
                    if day_of_week == 5:  # Saturday
                        monthly_summary['total_base_target'] += settings.saturday_base
                    elif day_of_week == 6:  # Sunday
                        monthly_summary['total_base_target'] += settings.sunday_base
                    else:  # Weekday
                        monthly_summary['total_base_target'] += settings.weekday_base
                    current_date += timedelta(days=1)

            # Generate weekly breakdown (optimized to avoid redundant calculations)
            week_start = start_date
            while week_start <= end_date:
                week_end = min(week_start + timedelta(days=6), end_date)
                week_summary = self.income_model.get_weekly_base_vs_bonus_summary(week_start)
                monthly_summary['weekly_breakdown'].append(week_summary)
                week_start += timedelta(days=7)

            return monthly_summary

        except Exception as e:
            print(f"Error getting monthly base vs bonus summary: {e}")
            return {
                'month_date': self.current_month,
                'total_earned': 0.0,
                'total_base_target': 0.0,
                'total_base_achieved': 0.0,
                'total_bonus': 0.0,
                'weekly_breakdown': []
            }

    def update_weekly_breakdown(self, weekly_data: list):
        """Update weekly breakdown display"""
        # Clear existing weekly widgets
        for i in reversed(range(self.weekly_layout.count())):
            self.weekly_layout.itemAt(i).widget().setParent(None)

        # Add weekly breakdown
        for week_data in weekly_data:
            week_widget = self.create_week_widget(week_data)
            self.weekly_layout.addWidget(week_widget)

    def create_week_widget(self, week_data: Dict[str, Any]) -> QWidget:
        """Create widget for a single week with base vs bonus data"""
        week_widget = QFrame()
        week_widget.setObjectName("incomeWeekWidget")
        # Theme-aware styling will be applied later
        week_widget.setObjectName("incomeWeekWidget")
        week_layout = QHBoxLayout(week_widget)

        # Week info
        start_date = week_data.get('start_date', date.today())
        end_date = week_data.get('end_date', date.today())
        week_info = QLabel(f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}")
        week_info.setObjectName("incomeWeekInfo")
        week_info.setMinimumWidth(100)
        font = QFont()
        font.setBold(True)
        week_info.setFont(font)
        week_layout.addWidget(week_info)

        # Base vs bonus breakdown
        total_earned = week_data.get('total_earned', 0)
        total_base_target = week_data.get('total_base_target', 0)
        total_base_achieved = week_data.get('total_base_achieved', 0)
        total_bonus = week_data.get('total_bonus', 0)

        # Base progress
        base_progress = (total_base_achieved / total_base_target * 100) if total_base_target > 0 else 0

        # Progress bar for base achievement
        progress_bar = QProgressBar()
        progress_bar.setObjectName("incomeWeekProgress")
        progress_bar.setValue(int(base_progress))
        progress_bar.setFormat(f"Base: ₹{total_base_achieved:.0f}/₹{total_base_target:.0f}")
        progress_bar.setMinimumHeight(25)  # Ensure visible height
        progress_bar.setMaximumHeight(35)
        # Theme-aware styling will be applied later
        progress_bar.setObjectName("incomeWeekProgress")
        week_layout.addWidget(progress_bar)

        # Bonus display
        bonus_label = QLabel(f"Bonus: ₹{total_bonus:.0f}")
        bonus_label.setObjectName("incomeWeekBonus")
        bonus_label.setMinimumWidth(80)
        bonus_label.setAlignment(Qt.AlignCenter)
        bonus_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px;")
        week_layout.addWidget(bonus_label)

        # Total earned with target comparison
        if total_base_target > 0:
            total_label = QLabel(f"Total: ₹{total_earned:.0f}/₹{total_base_target:.0f}")
        else:
            total_label = QLabel(f"Total: ₹{total_earned:.0f}")
        total_label.setObjectName("incomeWeekTotal")
        total_label.setMinimumWidth(120)  # Increased width to accommodate target
        total_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        total_label.setFont(font)
        week_layout.addWidget(total_label)

        return week_widget

    def apply_theme(self, theme_name: str = 'dark'):
        """Apply theme to monthly view widget"""
        try:
            print(f"🎨 DEBUG: MonthlyViewWidget.apply_theme called with theme: {theme_name}")

            # Get theme colors from parent if available
            if hasattr(self.parent(), 'get_theme_colors'):
                colors = self.parent().get_theme_colors(theme_name)
            else:
                # Fallback colors
                if theme_name == 'dark':
                    colors = {
                        'background': '#1e1e1e',
                        'surface': '#252526',
                        'border': '#3e3e42',
                        'text': '#ffffff',
                        'progress_bg': '#2d2d30',
                        'progress_chunk': '#0e639c'
                    }
                else:
                    colors = {
                        'background': '#ffffff',
                        'surface': '#f8f9fa',
                        'border': '#d0d0d0',
                        'text': '#000000',
                        'progress_bg': '#f8f9fa',
                        'progress_chunk': '#0078d4'
                    }

            # Apply theme to main progress bar
            if hasattr(self, 'monthly_progress'):
                self.monthly_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {colors['border']};
                        border-radius: 8px;
                        text-align: center;
                        font-weight: bold;
                        font-size: 11px;
                        background-color: {colors['progress_bg']};
                        color: {colors['text']};
                        min-height: 30px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {colors['progress_chunk']};
                        border-radius: 6px;
                        margin: 1px;
                    }}
                """)

            # Apply theme to week widgets
            for i in range(self.weekly_layout.count()):
                widget = self.weekly_layout.itemAt(i).widget()
                if widget and widget.objectName() == "incomeWeekWidget":
                    widget.setStyleSheet(f"""
                        QFrame#incomeWeekWidget {{
                            border: 1px solid {colors['border']};
                            border-radius: 5px;
                            margin: 2px;
                            padding: 5px;
                            background-color: {colors['surface']};
                            color: {colors['text']};
                        }}
                        QFrame#incomeWeekWidget:hover {{
                            border-color: {colors['progress_chunk']};
                        }}
                    """)

                    # Apply theme to progress bars within week widgets
                    for progress_bar in widget.findChildren(QProgressBar):
                        progress_bar.setStyleSheet(f"""
                            QProgressBar {{
                                border: 2px solid {colors['border']};
                                border-radius: 5px;
                                text-align: center;
                                font-size: 11px;
                                font-weight: bold;
                                background-color: {colors['progress_bg']};
                                color: {colors['text']};
                                min-height: 25px;
                                max-height: 35px;
                            }}
                            QProgressBar::chunk {{
                                background-color: {colors['progress_chunk']};
                                border-radius: 3px;
                                margin: 1px;
                            }}
                        """)

            print(f"✅ SUCCESS: Applied theme '{theme_name}' to MonthlyViewWidget")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to MonthlyViewWidget: {e}")


class YearlyViewWidget(QWidget):
    """Widget showing yearly income overview with base income structure"""

    def __init__(self, income_model: IncomeDataModel, parent=None):
        super().__init__(parent)
        self.income_model = income_model
        self.current_year = date.today().year

        self.setup_ui()
        self.setup_connections()
        self.refresh_data()

    def setup_ui(self):
        """Setup the yearly view UI with scrollable content"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header with navigation (fixed at top)
        header_layout = QHBoxLayout()

        self.prev_year_btn = QPushButton("◀ Previous")
        self.prev_year_btn.setObjectName("incomeYearNavButton")
        header_layout.addWidget(self.prev_year_btn)

        self.year_label = QLabel("Current Year")
        self.year_label.setObjectName("incomeYearLabel")
        self.year_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.year_label.setFont(font)
        header_layout.addWidget(self.year_label)

        self.next_year_btn = QPushButton("Next ▶")
        self.next_year_btn.setObjectName("incomeYearNavButton")
        header_layout.addWidget(self.next_year_btn)

        layout.addLayout(header_layout)

        # Create scroll area for the main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2d2d30;
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
        """)

        # Create content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Yearly summary cards with base vs bonus structure
        summary_layout = QHBoxLayout()

        # Total earned card
        total_card = QFrame()
        total_card.setObjectName("incomeYearlyCard")
        total_layout = QVBoxLayout(total_card)
        self.total_earned_label = QLabel("₹0")
        self.total_earned_label.setObjectName("incomeYearlyTotal")
        total_layout.addWidget(self.total_earned_label)
        total_layout.addWidget(QLabel("Total Earned"))
        summary_layout.addWidget(total_card)

        # Base achieved card
        base_card = QFrame()
        base_card.setObjectName("incomeYearlyCard")
        base_layout = QVBoxLayout(base_card)
        self.base_achieved_label = QLabel("₹0")
        self.base_achieved_label.setObjectName("incomeYearlyBase")
        base_layout.addWidget(self.base_achieved_label)
        base_layout.addWidget(QLabel("Base Achieved"))
        summary_layout.addWidget(base_card)

        # Bonus earned card
        bonus_card = QFrame()
        bonus_card.setObjectName("incomeYearlyCard")
        bonus_layout = QVBoxLayout(bonus_card)
        self.bonus_earned_label = QLabel("₹0")
        self.bonus_earned_label.setObjectName("incomeYearlyBonus")
        self.bonus_earned_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        bonus_layout.addWidget(self.bonus_earned_label)
        bonus_layout.addWidget(QLabel("Bonus Earned"))
        summary_layout.addWidget(bonus_card)

        # Base progress card
        progress_card = QFrame()
        progress_card.setObjectName("incomeYearlyCard")
        progress_layout = QVBoxLayout(progress_card)
        self.base_progress_label = QLabel("0%")
        self.base_progress_label.setObjectName("incomeYearlyProgress")
        progress_layout.addWidget(self.base_progress_label)
        progress_layout.addWidget(QLabel("Base Progress"))
        summary_layout.addWidget(progress_card)

        content_layout.addLayout(summary_layout)

        # Yearly base progress bar
        progress_frame = QGroupBox("Yearly Base Income Progress")
        progress_layout = QVBoxLayout(progress_frame)

        self.yearly_progress = QProgressBar()
        self.yearly_progress.setObjectName("incomeYearlyProgressBar")
        self.yearly_progress.setTextVisible(True)
        self.yearly_progress.setMinimumHeight(30)
        # Theme-aware styling will be applied later
        self.yearly_progress.setObjectName("yearlyProgressBar")
        progress_layout.addWidget(self.yearly_progress)

        # Base target info
        self.base_target_info_label = QLabel("Yearly Base Target: ₹0")
        self.base_target_info_label.setAlignment(Qt.AlignCenter)
        self.base_target_info_label.setStyleSheet("color: #666; font-size: 10px;")
        progress_layout.addWidget(self.base_target_info_label)

        content_layout.addWidget(progress_frame)

        # Monthly breakdown
        self.monthly_frame = QFrame()
        self.monthly_frame.setObjectName("incomeMonthlyFrame")
        # Theme-aware styling will be applied later
        self.monthly_frame.setObjectName("incomeMonthlyFrame")
        self.monthly_layout = QVBoxLayout(self.monthly_frame)
        self.monthly_layout.setSpacing(8)
        self.monthly_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.addWidget(self.monthly_frame)

        # Add stretch to push content to top
        content_layout.addStretch()

        # Set the content widget to the scroll area and add scroll area to main layout
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

    def setup_connections(self):
        """Setup signal connections"""
        self.prev_year_btn.clicked.connect(self.previous_year)
        self.next_year_btn.clicked.connect(self.next_year)

    def previous_year(self):
        """Navigate to previous year"""
        self.current_year -= 1
        self.refresh_data()

    def next_year(self):
        """Navigate to next year"""
        self.current_year += 1
        self.refresh_data()

    def refresh_data(self):
        """Refresh yearly data with base income structure"""
        try:
            # Update header
            self.year_label.setText(str(self.current_year))

            # Get yearly base vs bonus summary
            yearly_summary = self.get_yearly_base_vs_bonus_summary()

            # Update summary cards
            total_earned = yearly_summary['total_earned']
            total_base_target = yearly_summary['total_base_target']
            total_base_achieved = yearly_summary['total_base_achieved']
            total_bonus = yearly_summary['total_bonus']

            # Calculate base progress
            base_progress = (total_base_achieved / total_base_target * 100) if total_base_target > 0 else 0

            # Update labels with proper formatting
            self.total_earned_label.setText(f"₹{total_earned:,.0f}")
            self.base_achieved_label.setText(f"₹{total_base_achieved:,.0f}")
            self.bonus_earned_label.setText(f"₹{total_bonus:,.0f}")
            self.base_progress_label.setText(f"{base_progress:.1f}%")

            # Update base target info
            self.base_target_info_label.setText(f"Yearly Base Target: ₹{total_base_target:,.0f}")

            # Update progress bar
            self.yearly_progress.setValue(int(base_progress))
            self.yearly_progress.setFormat(f"{base_progress:.1f}% Base (₹{total_base_achieved:,.0f}/₹{total_base_target:,.0f}) + ₹{total_bonus:,.0f} Bonus")

            # Update monthly breakdown
            self.update_monthly_breakdown(yearly_summary['monthly_breakdown'])

        except Exception as e:
            print(f"Error refreshing yearly data: {e}")

    def get_yearly_base_vs_bonus_summary(self) -> Dict[str, Any]:
        """Get yearly summary with base vs bonus breakdown - OPTIMIZED VERSION"""
        try:
            # Calculate start and end dates for the year
            start_date = date(self.current_year, 1, 1)
            end_date = date(self.current_year, 12, 31)

            # Get income records for the year
            df = self.income_model.get_income_records_by_date_range(start_date, end_date)



            yearly_summary = {
                'year': self.current_year,
                'total_earned': 0.0,
                'total_base_target': 0.0,
                'total_base_achieved': 0.0,
                'total_bonus': 0.0,
                'monthly_breakdown': []
            }

            # Flag to track if monthly breakdown has been created
            monthly_breakdown_created = False

            if not df.empty:
                # Force refresh of base income settings cache before calculation
                if hasattr(self.income_model, '_base_income_settings_cache'):
                    self.income_model._base_income_settings_cache = None
                    self.income_model._base_settings_cache_timestamp = None

                current_settings = self.income_model.get_current_base_income_settings()

                # Use vectorized calculation for all years, but force cache refresh for current year
                df_with_bonus = self.income_model.calculate_bulk_bonus_income(df)

                # Check if bonus calculation was successful
                if 'base_target' in df_with_bonus.columns:
                    print(f"Bulk bonus calculation successful for {self.current_year}")
                    # Calculate yearly totals using pandas aggregation
                    yearly_summary['total_earned'] = float(df_with_bonus['earned'].sum())
                    # Don't use sum of actual data base targets - calculate theoretical full year target
                    yearly_summary['total_base_achieved'] = float(df_with_bonus['base_achieved'].sum())
                    yearly_summary['total_bonus'] = float(df_with_bonus['bonus_amount'].sum())



                    # Group by month for monthly breakdown (vectorized)
                    df_with_bonus['month'] = pd.to_datetime(df_with_bonus['date']).dt.month
                    monthly_groups = df_with_bonus.groupby('month').agg({
                        'earned': 'sum',
                        'base_target': 'sum',
                        'base_achieved': 'sum',
                        'bonus_amount': 'sum'
                    }).reset_index()

                    # Create a lookup dictionary for months with data
                    monthly_data_lookup = {}
                    for _, month_data in monthly_groups.iterrows():
                        month_num = int(month_data['month'])
                        monthly_data_lookup[month_num] = {
                            'total_earned': float(month_data['earned']),
                            'total_base_target': float(month_data['base_target']),
                            'total_base_achieved': float(month_data['base_achieved']),
                            'total_bonus': float(month_data['bonus_amount'])
                        }

                    # Create complete monthly breakdown for all 12 months (only if not already created)
                    if not monthly_breakdown_created:
                        settings = self.income_model.get_current_base_income_settings()
                        for month in range(1, 13):
                            month_start = date(self.current_year, month, 1)

                            # Calculate theoretical target for the full month regardless of data
                            if month == 12:
                                month_end = date(self.current_year + 1, 1, 1) - timedelta(days=1)
                            else:
                                month_end = date(self.current_year, month + 1, 1) - timedelta(days=1)

                            month_base_target = 0.0
                            current_date = month_start
                            while current_date <= month_end:
                                day_of_week = current_date.weekday()
                                if day_of_week == 5:  # Saturday
                                    month_base_target += settings.saturday_base
                                elif day_of_week == 6:  # Sunday
                                    month_base_target += settings.sunday_base
                                else:  # Weekday
                                    month_base_target += settings.weekday_base
                                current_date += timedelta(days=1)

                            if month in monthly_data_lookup:
                                # Month has data - use actual earned/achieved but theoretical target
                                month_summary = {
                                    'month': month,
                                    'month_name': month_start.strftime('%B'),
                                    'total_earned': monthly_data_lookup[month]['total_earned'],
                                    'total_base_target': month_base_target,  # Use full month theoretical target
                                    'total_base_achieved': monthly_data_lookup[month]['total_base_achieved'],
                                    'total_bonus': monthly_data_lookup[month]['total_bonus']
                                }
                            else:
                                # Month has no data - use theoretical targets (already calculated above)
                                month_summary = {
                                    'month': month,
                                    'month_name': month_start.strftime('%B'),
                                    'total_earned': 0.0,
                                    'total_base_target': month_base_target,
                                    'total_base_achieved': 0.0,
                                    'total_bonus': 0.0
                                }

                            yearly_summary['monthly_breakdown'].append(month_summary)

                        # Calculate total yearly base target from monthly breakdown
                        yearly_summary['total_base_target'] = sum(
                            month['total_base_target'] for month in yearly_summary['monthly_breakdown']
                        )

                        monthly_breakdown_created = True
                else:
                    # Fallback calculation if bulk bonus calculation failed
                    print(f"Bulk bonus calculation failed for {self.current_year}, using fallback")
                    yearly_summary['total_earned'] = float(df_with_bonus['earned'].sum())
                    # Calculate base targets manually
                    settings = self.income_model.get_current_base_income_settings()
                    df_with_bonus['month'] = pd.to_datetime(df_with_bonus['date']).dt.month

                    # Manual calculation for each record (don't accumulate yearly totals here)
                    for _, row in df_with_bonus.iterrows():
                        date_obj = pd.to_datetime(row['date']).date()
                        day_of_week = date_obj.weekday()
                        if day_of_week == 5:  # Saturday
                            base_target = settings.saturday_base
                        elif day_of_week == 6:  # Sunday
                            base_target = settings.sunday_base
                        else:  # Weekday
                            base_target = settings.weekday_base

                        earned = float(row['earned'])
                        # Don't accumulate yearly totals here - will be calculated from monthly breakdown
                        yearly_summary['total_base_achieved'] += min(earned, base_target)
                        yearly_summary['total_bonus'] += max(0.0, earned - base_target)

                    # Create monthly groups manually
                    monthly_groups = df_with_bonus.groupby('month').agg({
                        'earned': 'sum'
                    }).reset_index()

                    # Create a lookup dictionary for months with data
                    monthly_data_lookup = {}
                    for idx, month_data in monthly_groups.iterrows():
                        month = int(month_data['month'])
                        month_df = df_with_bonus[df_with_bonus['month'] == month]

                        month_base_target = 0.0
                        month_base_achieved = 0.0
                        month_bonus = 0.0

                        for _, row in month_df.iterrows():
                            date_obj = pd.to_datetime(row['date']).date()
                            day_of_week = date_obj.weekday()
                            if day_of_week == 5:  # Saturday
                                base_target = settings.saturday_base
                            elif day_of_week == 6:  # Sunday
                                base_target = settings.sunday_base
                            else:  # Weekday
                                base_target = settings.weekday_base

                            earned = float(row['earned'])
                            month_base_target += base_target
                            month_base_achieved += min(earned, base_target)
                            month_bonus += max(0.0, earned - base_target)

                        monthly_data_lookup[month] = {
                            'total_earned': float(month_data['earned']),
                            'total_base_target': month_base_target,
                            'total_base_achieved': month_base_achieved,
                            'total_bonus': month_bonus
                        }

                    # Create complete monthly breakdown for all 12 months (fallback path)
                    settings = self.income_model.get_current_base_income_settings()
                    for month in range(1, 13):
                        month_start = date(self.current_year, month, 1)

                        # Calculate theoretical target for the full month regardless of data
                        if month == 12:
                            month_end = date(self.current_year + 1, 1, 1) - timedelta(days=1)
                        else:
                            month_end = date(self.current_year, month + 1, 1) - timedelta(days=1)

                        month_base_target = 0.0
                        current_date = month_start
                        while current_date <= month_end:
                            day_of_week = current_date.weekday()
                            if day_of_week == 5:  # Saturday
                                month_base_target += settings.saturday_base
                            elif day_of_week == 6:  # Sunday
                                month_base_target += settings.sunday_base
                            else:  # Weekday
                                month_base_target += settings.weekday_base
                            current_date += timedelta(days=1)

                        if month in monthly_data_lookup:
                            # Month has data - use actual earned/achieved but theoretical target
                            month_summary = {
                                'month': month,
                                'month_name': month_start.strftime('%B'),
                                'total_earned': monthly_data_lookup[month]['total_earned'],
                                'total_base_target': month_base_target,  # Use full month theoretical target
                                'total_base_achieved': monthly_data_lookup[month]['total_base_achieved'],
                                'total_bonus': monthly_data_lookup[month]['total_bonus']
                            }
                        else:
                            # Month has no data - use theoretical targets (already calculated above)
                            month_summary = {
                                'month': month,
                                'month_name': month_start.strftime('%B'),
                                'total_earned': 0.0,
                                'total_base_target': month_base_target,
                                'total_base_achieved': 0.0,
                                'total_bonus': 0.0
                            }

                        yearly_summary['monthly_breakdown'].append(month_summary)

                    # Calculate total yearly base target from monthly breakdown
                    yearly_summary['total_base_target'] = sum(
                        month['total_base_target'] for month in yearly_summary['monthly_breakdown']
                    )


            else:
                # No data for this year - calculate theoretical base targets
                settings = self.income_model.get_current_base_income_settings()
                for month in range(1, 13):
                    month_start = date(self.current_year, month, 1)
                    if month == 12:
                        month_end = date(self.current_year + 1, 1, 1) - timedelta(days=1)
                    else:
                        month_end = date(self.current_year, month + 1, 1) - timedelta(days=1)

                    month_base_target = 0.0
                    current_date = month_start
                    while current_date <= month_end:
                        day_of_week = current_date.weekday()
                        if day_of_week == 5:  # Saturday
                            month_base_target += settings.saturday_base
                        elif day_of_week == 6:  # Sunday
                            month_base_target += settings.sunday_base
                        else:  # Weekday
                            month_base_target += settings.weekday_base
                        current_date += timedelta(days=1)

                    month_summary = {
                        'month': month,
                        'month_name': month_start.strftime('%B'),
                        'total_earned': 0.0,
                        'total_base_target': month_base_target,
                        'total_base_achieved': 0.0,
                        'total_bonus': 0.0
                    }
                    yearly_summary['monthly_breakdown'].append(month_summary)
                    yearly_summary['total_base_target'] += month_base_target

            return yearly_summary

        except Exception as e:
            print(f"Error getting yearly base vs bonus summary: {e}")
            return {
                'year': self.current_year,
                'total_earned': 0.0,
                'total_base_target': 0.0,
                'total_base_achieved': 0.0,
                'total_bonus': 0.0,
                'monthly_breakdown': []
            }

    def update_monthly_breakdown(self, monthly_data: list):
        """Update monthly breakdown display"""
        # Clear existing monthly widgets
        for i in reversed(range(self.monthly_layout.count())):
            widget = self.monthly_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Add monthly breakdown
        if not monthly_data:
            no_data_label = QLabel("No monthly data available for this year")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            self.monthly_layout.addWidget(no_data_label)
        else:
            # Add a header for the monthly breakdown
            header_label = QLabel(f"Monthly Breakdown ({len(monthly_data)} months)")
            header_label.setAlignment(Qt.AlignCenter)
            # Theme-aware styling will be applied later
            header_label.setObjectName("monthlyBreakdownHeader")
            self.monthly_layout.addWidget(header_label)

            for month_data in monthly_data:
                try:
                    month_widget = self.create_month_widget(month_data)
                    self.monthly_layout.addWidget(month_widget)
                except Exception as e:
                    # Create a simple error widget
                    error_widget = QLabel(f"Error loading {month_data.get('month_name', 'Unknown')}: {str(e)}")
                    error_widget.setStyleSheet("color: red; padding: 10px; border: 1px solid red; margin: 2px;")
                    self.monthly_layout.addWidget(error_widget)

            # CRITICAL FIX: Apply theme styling to month widgets after creation
            # This ensures the month widgets have proper background colors for the current theme
            self.apply_theme_to_month_widgets('dark')  # Default to dark theme for now
            print(f"🎨 DEBUG: Applied theme styling to month widgets after creation")

    def create_month_widget(self, month_data: Dict[str, Any]) -> QWidget:
        """Create widget for a single month with base vs bonus data"""
        month_widget = QFrame()
        month_widget.setObjectName("incomeMonthWidget")
        # CRITICAL FIX: Remove hardcoded colors - theme styling will be applied by apply_theme method
        month_widget.setStyleSheet("""
            QFrame#incomeMonthWidget {
                border-radius: 10px;
                margin: 5px 0px;
                padding: 15px;
                min-height: 60px;
                max-height: 80px;
            }
        """)
        month_layout = QHBoxLayout(month_widget)

        # Month info
        month_info = QLabel(month_data['month_name'])
        month_info.setObjectName("incomeMonthInfo")
        month_info.setMinimumWidth(80)
        font = QFont()
        font.setBold(True)
        month_info.setFont(font)
        month_layout.addWidget(month_info)

        # Base vs bonus breakdown
        total_earned = month_data.get('total_earned', 0)
        total_base_target = month_data.get('total_base_target', 0)
        total_base_achieved = month_data.get('total_base_achieved', 0)
        total_bonus = month_data.get('total_bonus', 0)

        # Base progress
        base_progress = (total_base_achieved / total_base_target * 100) if total_base_target > 0 else 0

        # Progress bar for base achievement
        progress_bar = QProgressBar()
        progress_bar.setObjectName("incomeMonthProgress")
        progress_bar.setValue(int(base_progress))
        progress_bar.setFormat(f"Base: ₹{total_base_achieved:,.0f}/₹{total_base_target:,.0f}")
        progress_bar.setMinimumHeight(30)  # Increased height for better visibility
        progress_bar.setMaximumHeight(40)
        # Theme-aware styling will be applied later
        progress_bar.setObjectName("incomeMonthProgress")
        month_layout.addWidget(progress_bar)

        # Bonus display
        bonus_label = QLabel(f"Bonus: ₹{total_bonus:,.0f}")
        bonus_label.setObjectName("incomeMonthBonus")
        bonus_label.setMinimumWidth(100)
        bonus_label.setAlignment(Qt.AlignCenter)
        bonus_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px;")
        month_layout.addWidget(bonus_label)

        # Total earned with target comparison
        if total_base_target > 0:
            total_label = QLabel(f"Total: ₹{total_earned:,.0f}/₹{total_base_target:,.0f}")
        else:
            total_label = QLabel(f"Total: ₹{total_earned:,.0f}")
        total_label.setObjectName("incomeMonthTotal")
        total_label.setMinimumWidth(140)  # Increased width to accommodate target
        total_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        total_label.setFont(font)
        month_layout.addWidget(total_label)

        return month_widget

    def apply_theme_to_month_widgets(self, theme_name: str = 'dark'):
        """Apply theme-aware styling to all month widgets and their children"""
        try:
            # Get theme colors using the parent's theme system
            if hasattr(self.parent(), 'get_theme_colors'):
                colors = self.parent().get_theme_colors(theme_name)
            else:
                # Fallback color scheme
                if theme_name == 'dark':
                    colors = {
                        'background': '#1e1e1e',
                        'surface': '#252526',
                        'border': '#3e3e42',
                        'text': '#ffffff',
                        'accent': '#0e639c',
                        'progress_bg': '#2d2d30',
                        'progress_chunk': '#0e639c'
                    }
                else:
                    colors = {
                        'background': '#ffffff',
                        'surface': '#f8f9fa',
                        'border': '#d0d0d0',
                        'text': '#000000',
                        'accent': '#0078d4',
                        'progress_bg': '#f8f9fa',
                        'progress_chunk': '#0078d4'
                    }

            # Apply theme to all month widgets
            month_widgets_styled = 0
            progress_bars_styled = 0

            for i in range(self.monthly_layout.count()):
                widget = self.monthly_layout.itemAt(i).widget()
                if widget:
                    # Style month widgets
                    if widget.objectName() == "incomeMonthWidget":
                        widget.setStyleSheet(f"""
                            QFrame#incomeMonthWidget {{
                                background-color: {colors['surface']};
                                border: 2px solid {colors['border']};
                                border-radius: 10px;
                                margin: 5px 0px;
                                padding: 15px;
                                min-height: 60px;
                                max-height: 80px;
                                color: {colors['text']};
                            }}
                            QFrame#incomeMonthWidget:hover {{
                                border-color: {colors['accent']};
                            }}
                        """)
                        month_widgets_styled += 1

                        # Style progress bars within month widgets
                        for progress_bar in widget.findChildren(QProgressBar):
                            progress_bar.setStyleSheet(f"""
                                QProgressBar {{
                                    border: 2px solid {colors['border']};
                                    border-radius: 6px;
                                    text-align: center;
                                    font-size: 10px;
                                    font-weight: bold;
                                    background-color: {colors['progress_bg']};
                                    color: {colors['text']};
                                    min-height: 30px;
                                    max-height: 40px;
                                }}
                                QProgressBar::chunk {{
                                    background-color: {colors['progress_chunk']};
                                    border-radius: 4px;
                                    margin: 1px;
                                }}
                            """)
                            progress_bars_styled += 1

                    # Style header labels
                    elif widget.objectName() == "monthlyBreakdownHeader":
                        widget.setStyleSheet(f"""
                            QLabel#monthlyBreakdownHeader {{
                                font-weight: bold;
                                font-size: 16px;
                                padding: 10px;
                                background-color: {colors['surface']};
                                border: 1px solid {colors['border']};
                                border-radius: 5px;
                                margin-bottom: 10px;
                                color: {colors['text']};
                            }}
                        """)

            print(f"🎨 DEBUG: Applied theme to {month_widgets_styled} month widgets and {progress_bars_styled} progress bars in YearlyViewWidget")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to month widgets: {e}")

    def apply_theme(self, theme_name: str = 'dark'):
        """Apply theme to yearly view widget"""
        try:
            print(f"🎨 DEBUG: YearlyViewWidget.apply_theme called with theme: {theme_name}")

            # Get theme colors from parent if available
            if hasattr(self.parent(), 'get_theme_colors'):
                colors = self.parent().get_theme_colors(theme_name)
            else:
                # Fallback colors
                if theme_name == 'dark':
                    colors = {
                        'background': '#1e1e1e',
                        'surface': '#252526',
                        'border': '#3e3e42',
                        'text': '#ffffff',
                        'progress_bg': '#2d2d30',
                        'progress_chunk': '#0e639c'
                    }
                else:
                    colors = {
                        'background': '#ffffff',
                        'surface': '#f8f9fa',
                        'border': '#d0d0d0',
                        'text': '#000000',
                        'progress_bg': '#f8f9fa',
                        'progress_chunk': '#0078d4'
                    }

            # Apply theme to main progress bar
            if hasattr(self, 'yearly_progress'):
                self.yearly_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {colors['border']};
                        border-radius: 8px;
                        text-align: center;
                        font-weight: bold;
                        font-size: 11px;
                        background-color: {colors['progress_bg']};
                        color: {colors['text']};
                        min-height: 30px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {colors['progress_chunk']};
                        border-radius: 6px;
                        margin: 1px;
                    }}
                """)

            # Apply theme to monthly frame
            if hasattr(self, 'monthly_frame'):
                self.monthly_frame.setStyleSheet(f"""
                    QFrame#incomeMonthlyFrame {{
                        border: 1px solid {colors['border']};
                        border-radius: 8px;
                        background-color: {colors['surface']};
                        padding: 10px;
                        margin: 5px;
                        color: {colors['text']};
                    }}
                """)

            # Apply theme to month widgets
            self.apply_theme_to_month_widgets(theme_name)

            print(f"✅ SUCCESS: Applied theme '{theme_name}' to YearlyViewWidget")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to YearlyViewWidget: {e}")


class WeeklyViewWidget(QWidget):
    """Widget showing weekly income overview"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the weekly view UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header with navigation
        header_layout = QHBoxLayout()

        self.prev_week_btn = QPushButton("◀ Previous")
        self.prev_week_btn.setObjectName("incomeWeekNavButton")
        header_layout.addWidget(self.prev_week_btn)

        self.week_label = QLabel("Current Week")
        self.week_label.setObjectName("incomeWeekLabel")
        self.week_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        self.week_label.setFont(font)
        header_layout.addWidget(self.week_label)

        self.next_week_btn = QPushButton("Next ▶")
        self.next_week_btn.setObjectName("incomeWeekNavButton")
        header_layout.addWidget(self.next_week_btn)

        layout.addLayout(header_layout)

        # Weekly progress
        self.weekly_progress = QProgressBar()
        self.weekly_progress.setObjectName("incomeWeeklyProgressBar")
        self.weekly_progress.setTextVisible(True)
        layout.addWidget(self.weekly_progress)

        # Daily breakdown
        self.daily_frame = QFrame()
        self.daily_frame.setObjectName("incomeDailyFrame")
        self.daily_layout = QVBoxLayout(self.daily_frame)
        layout.addWidget(self.daily_frame)

        layout.addStretch()

    def update_weekly_data(self, weekly_data: Dict[str, Any]):
        """Update weekly view with data"""
        start_date = weekly_data['start_date']
        end_date = weekly_data['end_date']

        # Update header
        self.week_label.setText(f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}")

        # Update weekly progress
        week_progress = weekly_data.get('week_progress', 0)
        self.weekly_progress.setValue(int(week_progress))
        self.weekly_progress.setFormat(f"{week_progress:.1f}% (₹{weekly_data['total_earned']:.0f}/₹{weekly_data['total_goal']:.0f})")

        # Clear existing daily widgets
        for i in reversed(range(self.daily_layout.count())):
            self.daily_layout.itemAt(i).widget().setParent(None)

        # Add daily breakdown
        for day_data in weekly_data['daily_breakdown']:
            day_widget = self.create_day_widget(day_data)
            self.daily_layout.addWidget(day_widget)

    def create_day_widget(self, day_data: Dict[str, Any]) -> QWidget:
        """Create widget for a single day"""
        day_widget = QFrame()
        day_widget.setObjectName("incomeDayWidget")
        day_layout = QHBoxLayout(day_widget)

        # Day name and date
        day_info = QLabel(f"{day_data['day_name']}\n{day_data['date'].strftime('%m/%d')}")
        day_info.setObjectName("incomeDayInfo")
        day_info.setMinimumWidth(80)
        day_layout.addWidget(day_info)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setObjectName("incomeDayProgress")
        progress_bar.setValue(int(day_data['progress']))
        progress_bar.setFormat(f"₹{day_data['earned']:.0f}")
        day_layout.addWidget(progress_bar)

        # Status
        status_label = QLabel(day_data['status'])
        status_label.setObjectName("incomeDayStatus")
        status_label.setMinimumWidth(80)
        status_label.setAlignment(Qt.AlignCenter)

        # Color code status
        if day_data['status'] == "Exceeded":
            status_label.setStyleSheet("color: #00aa00; font-weight: bold;")
        elif day_data['status'] == "Completed":
            status_label.setStyleSheet("color: #0e639c; font-weight: bold;")
        elif day_data['status'] == "In Progress":
            status_label.setStyleSheet("color: #ff8800; font-weight: bold;")
        else:
            status_label.setStyleSheet("color: #999999;")

        day_layout.addWidget(status_label)

        # Edit button for this day
        edit_button = QPushButton("Edit")
        edit_button.setObjectName("incomeEditDayButton")
        edit_button.setMaximumWidth(60)
        edit_button.clicked.connect(lambda: self.edit_day_income(day_data['date']))
        day_layout.addWidget(edit_button)

        return day_widget

    def edit_day_income(self, date):
        """Signal to edit income for a specific date"""
        # This will be connected to the parent widget
        if hasattr(self.parent(), 'edit_income_for_date'):
            self.parent().edit_income_for_date(date)


class EnhancedDailyGoalWidget(QWidget):
    """Enhanced daily goal tracking widget with detailed progress"""

    def __init__(self, income_model: IncomeDataModel, parent=None):
        super().__init__(parent)
        self.income_model = income_model
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        """Setup the enhanced daily goal widget UI"""
        # Set size policy to allow expansion
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Main frame with enhanced styling - EXPANDED: Remove size restrictions
        main_frame = QGroupBox("Today's Goal Progress")
        main_frame.setObjectName("enhancedDailyGoalFrame")
        main_frame.setMinimumHeight(500)  # Reduced minimum height for better space utilization
        # Remove maximum height constraint to allow natural expansion
        main_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_frame.setStyleSheet("""
            QGroupBox#enhancedDailyGoalFrame {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: rgba(52, 152, 219, 0.05);
            }
            QGroupBox#enhancedDailyGoalFrame::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 10px 5px 10px;
                border-radius: 5px;
            }
        """)
        # Create scroll area for the main content
        scroll_area = QScrollArea(main_frame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrolling
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)     # Always show scroll bar to indicate more content
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove frame for seamless integration
        scroll_area.setMinimumHeight(450)  # Reduced minimum height for better space utilization
        # Remove maximum height constraint to allow natural expansion
        # Set size policy for proper expansion
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Set scroll step size for smoother scrolling
        scroll_area.verticalScrollBar().setSingleStep(25)  # Increased for better navigation
        scroll_area.verticalScrollBar().setPageStep(150)   # Larger page steps for quick navigation
        # Enable focus for keyboard navigation
        scroll_area.setFocusPolicy(Qt.WheelFocus)

        # Create content widget to hold all the content - EXPANDED: Remove fixed height
        content_widget = QWidget()
        # Remove fixed minimum height to allow natural content sizing
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins for more space
        content_layout.setSpacing(10)  # Reduced spacing for better fit

        # Set up the scroll area
        scroll_area.setWidget(content_widget)

        # Add scroll area to main frame
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)  # No margins for frame layout
        main_frame_layout.addWidget(scroll_area)

        # Goal overview section
        overview_layout = QGridLayout()
        overview_layout.setHorizontalSpacing(15)  # Reduced horizontal spacing
        overview_layout.setVerticalSpacing(10)    # Reduced vertical spacing

        # Create labels with better formatting
        goal_title_label = QLabel("Daily Goal:")
        goal_title_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setPointSize(11)
        goal_title_label.setFont(font)

        self.goal_amount_label = QLabel("₹2000.00")
        self.goal_amount_label.setObjectName("goalAmountLabel")
        self.goal_amount_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.goal_amount_label.setFont(font)
        overview_layout.addWidget(goal_title_label, 0, 0)
        overview_layout.addWidget(self.goal_amount_label, 0, 1)

        # Current earnings
        earnings_title_label = QLabel("Current Earnings:")
        earnings_title_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setPointSize(11)
        earnings_title_label.setFont(font)

        self.current_earnings_label = QLabel("₹0.00")
        self.current_earnings_label.setObjectName("currentEarningsLabel")
        self.current_earnings_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.current_earnings_label.setFont(font)
        overview_layout.addWidget(earnings_title_label, 1, 0)
        overview_layout.addWidget(self.current_earnings_label, 1, 1)

        # Remaining amount
        remaining_title_label = QLabel("Remaining:")
        remaining_title_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setPointSize(11)
        remaining_title_label.setFont(font)

        self.remaining_label = QLabel("₹2000.00")
        self.remaining_label.setObjectName("remainingLabel")
        self.remaining_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.remaining_label.setFont(font)
        overview_layout.addWidget(remaining_title_label, 2, 0)
        overview_layout.addWidget(self.remaining_label, 2, 1)

        # Progress percentage
        progress_title_label = QLabel("Progress:")
        progress_title_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setPointSize(11)
        progress_title_label.setFont(font)

        self.progress_percentage_label = QLabel("0%")
        self.progress_percentage_label.setObjectName("progressPercentageLabel")
        self.progress_percentage_label.setMinimumHeight(25)  # Reduced height
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.progress_percentage_label.setFont(font)
        overview_layout.addWidget(progress_title_label, 3, 0)
        overview_layout.addWidget(self.progress_percentage_label, 3, 1)

        content_layout.addLayout(overview_layout)

        # Progress bar with better spacing
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 8, 0, 8)  # Reduced margins

        progress_label = QLabel("Daily Progress:")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        progress_label.setFont(font)
        progress_layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("dailyGoalProgressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(35)  # Reduced height for better space utilization
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3e3e42;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 11px;
                background-color: #252526;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
                border-radius: 6px;
                margin: 1px;
            }
        """)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.progress_bar.setFont(font)
        progress_layout.addWidget(self.progress_bar)

        content_layout.addWidget(progress_container)

        # Time-based projections with improved spacing and styling - EXPANDED: Remove size restrictions
        projections_frame = QGroupBox("Projections")
        projections_frame.setMinimumHeight(180)  # Reduced minimum height for better space utilization
        # Remove maximum height constraint to allow natural expansion
        projections_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: rgba(231, 76, 60, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 3px 8px 3px 8px;
                border-radius: 4px;
            }
        """)
        projections_layout = QFormLayout(projections_frame)
        projections_layout.setVerticalSpacing(18)  # Optimized vertical spacing for better readability
        projections_layout.setHorizontalSpacing(15)  # Balanced horizontal spacing
        projections_layout.setContentsMargins(15, 20, 15, 15)  # Optimized margins for better content fit

        # Hours remaining in day
        current_time = datetime.now()
        hours_remaining = 24 - current_time.hour

        hours_title_label = QLabel("Hours Remaining:")
        font = QFont()
        font.setPointSize(10)
        hours_title_label.setFont(font)

        self.hours_remaining_label = QLabel(f"{hours_remaining} hours")
        self.hours_remaining_label.setMinimumHeight(25)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.hours_remaining_label.setFont(font)
        projections_layout.addRow(hours_title_label, self.hours_remaining_label)

        # Required hourly rate
        rate_title_label = QLabel("Required Rate:")
        font = QFont()
        font.setPointSize(10)
        rate_title_label.setFont(font)

        self.hourly_rate_label = QLabel("₹0.00/hour")
        self.hourly_rate_label.setMinimumHeight(25)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.hourly_rate_label.setFont(font)
        projections_layout.addRow(rate_title_label, self.hourly_rate_label)

        # Estimated completion time
        completion_title_label = QLabel("Est. Completion:")
        font = QFont()
        font.setPointSize(10)
        completion_title_label.setFont(font)

        self.completion_time_label = QLabel("--:--")
        self.completion_time_label.setMinimumHeight(25)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.completion_time_label.setFont(font)
        projections_layout.addRow(completion_title_label, self.completion_time_label)

        # Goal status
        status_title_label = QLabel("Status:")
        font = QFont()
        font.setPointSize(10)
        status_title_label.setFont(font)

        self.goal_status_label = QLabel("In Progress")
        self.goal_status_label.setObjectName("goalStatusLabel")
        self.goal_status_label.setMinimumHeight(25)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.goal_status_label.setFont(font)
        projections_layout.addRow(status_title_label, self.goal_status_label)

        content_layout.addWidget(projections_frame)

        # Base vs Bonus Income section - EXPANDED: Remove size restrictions
        base_bonus_frame = QGroupBox("💰 Today's Base vs Bonus")
        base_bonus_frame.setMinimumHeight(150)  # Reduced minimum height for better space utilization
        # Remove maximum height constraint to allow natural expansion
        base_bonus_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: rgba(155, 89, 182, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 3px 8px 3px 8px;
                border-radius: 4px;
            }
        """)
        base_bonus_layout = QFormLayout(base_bonus_frame)
        base_bonus_layout.setVerticalSpacing(15)  # Increased spacing for better visibility
        base_bonus_layout.setHorizontalSpacing(15)
        base_bonus_layout.setContentsMargins(15, 20, 15, 15)  # Increased top margin for title space

        # Base target
        base_target_title_label = QLabel("Base Target:")
        font = QFont()
        font.setPointSize(10)
        base_target_title_label.setFont(font)

        self.base_target_label = QLabel("₹500.00")
        self.base_target_label.setMinimumHeight(30)  # Increased for better visibility
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.base_target_label.setFont(font)
        base_bonus_layout.addRow(base_target_title_label, self.base_target_label)

        # Base achieved
        base_achieved_title_label = QLabel("Base Achieved:")
        font = QFont()
        font.setPointSize(10)
        base_achieved_title_label.setFont(font)

        self.base_achieved_label = QLabel("₹0.00")
        self.base_achieved_label.setMinimumHeight(30)  # Increased for better visibility
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.base_achieved_label.setFont(font)
        base_bonus_layout.addRow(base_achieved_title_label, self.base_achieved_label)

        # Bonus earned
        bonus_title_label = QLabel("Bonus Earned:")
        font = QFont()
        font.setPointSize(10)
        bonus_title_label.setFont(font)

        self.bonus_earned_label = QLabel("₹0.00")
        self.bonus_earned_label.setMinimumHeight(30)  # Increased for better visibility
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.bonus_earned_label.setFont(font)
        self.bonus_earned_label.setStyleSheet("color: #27ae60;")  # Green for bonus
        base_bonus_layout.addRow(bonus_title_label, self.bonus_earned_label)

        # Ensure the base vs bonus frame is visible and properly sized
        base_bonus_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        base_bonus_frame.setVisible(True)
        base_bonus_frame.show()
        content_layout.addWidget(base_bonus_frame)

        # Quick stats with improved spacing and styling - EXPANDED: Remove size restrictions
        stats_frame = QGroupBox("📊 Quick Stats")
        stats_frame.setMinimumHeight(120)  # Reduced minimum height for better space utilization
        # Remove maximum height constraint to allow natural expansion
        stats_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #27ae60;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: rgba(39, 174, 96, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 3px 8px 3px 8px;
                border-radius: 4px;
            }
        """)
        stats_layout = QFormLayout(stats_frame)
        stats_layout.setVerticalSpacing(12)  # Reduced spacing
        stats_layout.setHorizontalSpacing(15)  # Reduced spacing
        stats_layout.setContentsMargins(15, 15, 15, 15)  # Reduced margins

        # 7-Day Average
        avg_title_label = QLabel("7-Day Average:")
        font = QFont()
        font.setPointSize(10)
        avg_title_label.setFont(font)

        self.avg_daily_label = QLabel("₹0.00")
        self.avg_daily_label.setMinimumHeight(25)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.avg_daily_label.setFont(font)
        stats_layout.addRow(avg_title_label, self.avg_daily_label)

        # Best Day
        best_title_label = QLabel("Best Day:")
        font = QFont()
        font.setPointSize(10)
        best_title_label.setFont(font)

        self.best_day_label = QLabel("₹0.00")
        self.best_day_label.setMinimumHeight(25)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.best_day_label.setFont(font)
        stats_layout.addRow(best_title_label, self.best_day_label)

        # Goal Streak
        streak_title_label = QLabel("Goal Streak:")
        font = QFont()
        font.setPointSize(10)
        streak_title_label.setFont(font)

        self.streak_label = QLabel("0 days")
        self.streak_label.setMinimumHeight(25)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.streak_label.setFont(font)
        stats_layout.addRow(streak_title_label, self.streak_label)

        content_layout.addWidget(stats_frame)

        layout.addWidget(main_frame)

    def refresh_data(self):
        """Refresh the goal progress data"""
        try:
            # Get today's base income target instead of unified daily goal
            today = date.today()
            current_goal = self.income_model.get_base_income_for_date(today)
            self.goal_amount_label.setText(f"₹{current_goal:.2f}")

            # Get today's earnings
            today_record = self.income_model.get_income_record_by_date(date.today())
            current_earnings = today_record.earned if today_record else 0.0
            self.current_earnings_label.setText(f"₹{current_earnings:.2f}")

            # Calculate remaining and progress
            remaining = max(0, current_goal - current_earnings)
            self.remaining_label.setText(f"₹{remaining:.2f}")

            progress_percentage = min(100, (current_earnings / current_goal) * 100) if current_goal > 0 else 0
            self.progress_percentage_label.setText(f"{progress_percentage:.1f}%")
            self.progress_bar.setValue(int(progress_percentage))

            # Update progress bar format to show base target tracking
            self.progress_bar.setFormat(f"{progress_percentage:.1f}% Base Target (₹{current_earnings:.2f}/₹{current_goal:.2f})")

            # Update progress bar color based on progress
            if progress_percentage >= 100:
                self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
                self.goal_status_label.setText("✅ Base Goal Achieved!")
                self.goal_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            elif progress_percentage >= 80:
                self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #8BC34A; }")
                self.goal_status_label.setText("🎯 Almost There!")
                self.goal_status_label.setStyleSheet("color: #8BC34A; font-weight: bold;")
            elif progress_percentage >= 50:
                self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
                self.goal_status_label.setText("📈 On Track")
                self.goal_status_label.setStyleSheet("color: #FFC107; font-weight: bold;")
            else:
                self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FF5722; }")
                self.goal_status_label.setText("⚡ Need to Push!")
                self.goal_status_label.setStyleSheet("color: #FF5722; font-weight: bold;")

            # Update time-based projections
            current_time = datetime.now()
            hours_remaining = max(0, 24 - current_time.hour)
            self.hours_remaining_label.setText(f"{hours_remaining} hours")

            if hours_remaining > 0 and remaining > 0:
                required_hourly = remaining / hours_remaining
                self.hourly_rate_label.setText(f"₹{required_hourly:.2f}/hour")

                # Estimate completion time based on current rate
                if current_earnings > 0:
                    hours_elapsed = current_time.hour
                    if hours_elapsed > 0:
                        current_rate = current_earnings / hours_elapsed
                        if current_rate > 0:
                            hours_to_complete = remaining / current_rate
                            completion_time = current_time + timedelta(hours=hours_to_complete)
                            if completion_time.date() == date.today():
                                self.completion_time_label.setText(completion_time.strftime("%H:%M"))
                            else:
                                self.completion_time_label.setText("Tomorrow+")
                        else:
                            self.completion_time_label.setText("--:--")
                    else:
                        self.completion_time_label.setText("--:--")
                else:
                    self.completion_time_label.setText("--:--")
            else:
                self.hourly_rate_label.setText("₹0.00/hour")
                self.completion_time_label.setText("Goal Met!" if remaining == 0 else "--:--")

            # Update base vs bonus breakdown
            today = date.today()
            bonus_data = self.income_model.calculate_bonus_income(today, current_earnings)

            self.base_target_label.setText(f"₹{bonus_data['base_target']:.2f}")
            self.base_achieved_label.setText(f"₹{bonus_data['base_achieved']:.2f}")
            self.bonus_earned_label.setText(f"₹{bonus_data['bonus_amount']:.2f}")

            # Color code base achieved based on percentage
            base_percentage = bonus_data['base_percentage']
            if base_percentage >= 100:
                self.base_achieved_label.setStyleSheet("color: #27ae60; font-weight: bold;")  # Green
            elif base_percentage >= 80:
                self.base_achieved_label.setStyleSheet("color: #f39c12; font-weight: bold;")  # Orange
            else:
                self.base_achieved_label.setStyleSheet("color: #e74c3c; font-weight: bold;")  # Red

            # Update quick stats
            stats = self.income_model.get_income_summary()
            self.avg_daily_label.setText(f"₹{stats.get('average_daily', 0):.2f}")
            self.best_day_label.setText(f"₹{stats.get('best_day_amount', 0):.2f}")
            self.streak_label.setText(f"{stats.get('streak_days', 0)} days")

        except Exception as e:
            print(f"Error refreshing daily goal data: {e}")


class EnhancedWeeklyViewWidget(QWidget):
    """Enhanced weekly view with goal tracking and income source analysis"""

    def __init__(self, income_model: IncomeDataModel, parent=None):
        super().__init__(parent)
        self.income_model = income_model
        self.current_week_start = None
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        """Setup the enhanced weekly view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header with navigation
        header_layout = QHBoxLayout()

        self.prev_week_btn = QPushButton("◀ Previous Week")
        self.prev_week_btn.clicked.connect(self.prev_week)
        header_layout.addWidget(self.prev_week_btn)

        self.week_label = QLabel("Week of [Date Range]")
        self.week_label.setObjectName("weekHeaderLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.week_label.setFont(font)
        self.week_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.week_label)

        self.next_week_btn = QPushButton("Next Week ▶")
        self.next_week_btn.clicked.connect(self.next_week)
        header_layout.addWidget(self.next_week_btn)

        layout.addLayout(header_layout)

        # Weekly summary cards
        summary_layout = QHBoxLayout()

        # Total earned card
        total_card = self.create_summary_card("Total Earned", "₹0.00", "#4CAF50")
        summary_layout.addWidget(total_card)

        # Weekly goal card
        goal_card = self.create_summary_card("Weekly Goal", "₹0.00", "#2196F3")
        summary_layout.addWidget(goal_card)

        # Progress card
        progress_card = self.create_summary_card("Progress", "0%", "#FF9800")
        summary_layout.addWidget(progress_card)

        # Average daily card
        avg_card = self.create_summary_card("Daily Average", "₹0.00", "#9C27B0")
        summary_layout.addWidget(avg_card)

        layout.addLayout(summary_layout)

        # Weekly progress bar
        progress_frame = QGroupBox("Weekly Progress")
        progress_layout = QVBoxLayout(progress_frame)

        self.weekly_progress_bar = QProgressBar()
        self.weekly_progress_bar.setObjectName("weeklyProgressBar")
        self.weekly_progress_bar.setMinimum(0)
        self.weekly_progress_bar.setMaximum(100)
        self.weekly_progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.weekly_progress_bar)

        layout.addWidget(progress_frame)

        # Main content area with tabs
        content_tabs = QTabWidget()

        # Daily breakdown tab
        daily_tab = self.create_daily_breakdown_tab()
        content_tabs.addTab(daily_tab, "Daily Breakdown")

        # Income sources tab
        sources_tab = self.create_income_sources_tab()
        content_tabs.addTab(sources_tab, "Income Sources")

        # Goal analysis tab
        analysis_tab = self.create_goal_analysis_tab()
        content_tabs.addTab(analysis_tab, "Goal Analysis")

        layout.addWidget(content_tabs)

    def create_summary_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a summary card widget - FIXED: No hardcoded background"""
        card = QFrame()
        card.setObjectName("summaryCard")
        # CRITICAL FIX: Remove hardcoded background-color to let global theme handle it
        card.setStyleSheet(f"""
            QFrame#summaryCard {{
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName(f"card{title.replace(' ', '')}Value")
        value_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        value_label.setFont(font)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        return card

    def hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB string"""
        hex_color = hex_color.lstrip('#')
        return ','.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

    def create_daily_breakdown_tab(self) -> QWidget:
        """Create daily breakdown tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Daily progress grid
        self.daily_grid_layout = QGridLayout()
        layout.addLayout(self.daily_grid_layout)

        layout.addStretch()
        return tab

    def create_income_sources_tab(self) -> QWidget:
        """Create income sources analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Source contribution chart placeholder
        sources_frame = QGroupBox("Income Source Contributions")
        sources_layout = QVBoxLayout(sources_frame)

        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(4)
        self.sources_table.setHorizontalHeaderLabels(["Source", "Amount", "Percentage", "Daily Avg"])
        sources_layout.addWidget(self.sources_table)

        layout.addWidget(sources_frame)

        # Source performance trends
        trends_frame = QGroupBox("Performance Trends")
        trends_layout = QVBoxLayout(trends_frame)

        self.trends_label = QLabel("Trend analysis will be displayed here")
        trends_layout.addWidget(self.trends_label)

        layout.addWidget(trends_frame)

        return tab

    def create_goal_analysis_tab(self) -> QWidget:
        """Create goal analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Goal achievement analysis
        analysis_frame = QGroupBox("Goal Achievement Analysis")
        analysis_layout = QFormLayout(analysis_frame)

        self.days_on_track_label = QLabel("0/7")
        analysis_layout.addRow("Days on Track:", self.days_on_track_label)

        self.projected_total_label = QLabel("₹0.00")
        analysis_layout.addRow("Projected Weekly Total:", self.projected_total_label)

        self.required_daily_label = QLabel("₹0.00")
        analysis_layout.addRow("Required Daily (Remaining):", self.required_daily_label)

        self.best_performing_day_label = QLabel("Monday")
        analysis_layout.addRow("Best Performing Day:", self.best_performing_day_label)

        self.worst_performing_day_label = QLabel("Sunday")
        analysis_layout.addRow("Needs Improvement:", self.worst_performing_day_label)

        layout.addWidget(analysis_frame)

        # Recommendations
        recommendations_frame = QGroupBox("Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_frame)

        self.recommendations_label = QLabel("Recommendations will be displayed here")
        self.recommendations_label.setWordWrap(True)
        recommendations_layout.addWidget(self.recommendations_label)

        layout.addWidget(recommendations_frame)

        layout.addStretch()
        return tab

    def prev_week(self):
        """Navigate to previous week"""
        if self.current_week_start:
            self.current_week_start -= timedelta(days=7)
            self.refresh_data()

    def next_week(self):
        """Navigate to next week"""
        if self.current_week_start:
            self.current_week_start += timedelta(days=7)
            self.refresh_data()

    def refresh_data(self):
        """Refresh weekly data"""
        try:
            # Set current week if not set
            if self.current_week_start is None:
                today = date.today()
                self.current_week_start = today - timedelta(days=today.weekday())

            # Get weekly data with base vs bonus breakdown
            weekly_data = self.income_model.get_weekly_base_vs_bonus_summary(self.current_week_start)

            # Update header
            end_date = self.current_week_start + timedelta(days=6)
            self.week_label.setText(f"Week of {self.current_week_start.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}")

            # Update summary cards with base vs bonus data
            total_earned = weekly_data.get('total_earned', 0)
            total_base_target = weekly_data.get('total_base_target', 0)
            total_base_achieved = weekly_data.get('total_base_achieved', 0)
            total_bonus = weekly_data.get('total_bonus', 0)

            # Calculate progress against base targets (prevent division by zero)
            if total_base_target > 0:
                base_progress = (total_base_achieved / total_base_target) * 100
            else:
                base_progress = 0

            # Calculate average daily (prevent division by zero)
            avg_daily = total_earned / 7 if total_earned >= 0 else 0

            # Find and update summary card values
            self.findChild(QLabel, "cardTotalEarnedValue").setText(f"₹{total_earned:.2f}")
            self.findChild(QLabel, "cardWeeklyGoalValue").setText(f"₹{total_base_target:.2f} (Base)")
            self.findChild(QLabel, "cardProgressValue").setText(f"{base_progress:.1f}% (Base)")
            self.findChild(QLabel, "cardDailyAverageValue").setText(f"₹{avg_daily:.2f}")

            # Update progress bar
            self.weekly_progress_bar.setValue(int(base_progress))
            self.weekly_progress_bar.setFormat(f"{base_progress:.1f}% Base (₹{total_base_achieved:.2f}/₹{total_base_target:.2f}) + ₹{total_bonus:.2f} Bonus")

            # Update daily breakdown
            self.update_daily_breakdown(weekly_data.get('daily_breakdown', []))

            # Update income sources
            self.update_income_sources(weekly_data)

            # Update goal analysis
            self.update_goal_analysis(weekly_data)

        except Exception as e:
            print(f"Error refreshing weekly data: {e}")

    def update_daily_breakdown(self, daily_data: list):
        """Update daily breakdown grid"""
        # Clear existing widgets
        for i in reversed(range(self.daily_grid_layout.count())):
            self.daily_grid_layout.itemAt(i).widget().setParent(None)

        # Add day widgets
        for i, day_data in enumerate(daily_data):
            day_widget = self.create_day_widget(day_data)
            self.daily_grid_layout.addWidget(day_widget, 0, i)

    def create_day_widget(self, day_data: dict) -> QWidget:
        """Create widget for a single day"""
        day_widget = QFrame()
        day_widget.setObjectName("dayWidget")
        layout = QVBoxLayout(day_widget)

        # Day name
        day_label = QLabel(day_data['day_name'][:3])  # Mon, Tue, etc.
        day_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        day_label.setFont(font)
        layout.addWidget(day_label)

        # Date
        date_label = QLabel(day_data['date'].strftime('%d'))
        date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(date_label)

        # Base vs Bonus breakdown
        base_target = day_data.get('base_target', 0)
        base_achieved = day_data.get('base_achieved', 0)
        bonus_amount = day_data.get('bonus_amount', 0)

        # Base achieved
        base_label = QLabel(f"₹{base_achieved:.0f}")
        base_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        base_label.setFont(font)

        # Color code based on base achievement
        base_percentage = day_data.get('base_percentage', 0)
        if base_percentage >= 100:
            base_label.setStyleSheet("color: #27ae60;")  # Green
        elif base_percentage >= 80:
            base_label.setStyleSheet("color: #f39c12;")  # Orange
        else:
            base_label.setStyleSheet("color: #e74c3c;")  # Red

        layout.addWidget(base_label)

        # Bonus amount (if any)
        if bonus_amount > 0:
            bonus_label = QLabel(f"+₹{bonus_amount:.0f}")
            bonus_label.setAlignment(Qt.AlignCenter)
            bonus_label.setStyleSheet("color: #27ae60; font-size: 10px; font-weight: bold;")
            layout.addWidget(bonus_label)
        else:
            # Add spacer to maintain consistent height
            spacer_label = QLabel("")
            spacer_label.setMinimumHeight(15)
            layout.addWidget(spacer_label)

        # Progress indicator (base achievement) - dark theme compatible
        progress = base_percentage
        if progress >= 100:
            day_widget.setStyleSheet("QFrame#dayWidget { border: 2px solid #4CAF50; border-radius: 8px; background-color: rgba(45, 90, 45, 0.3); }")
        elif progress >= 80:
            day_widget.setStyleSheet("QFrame#dayWidget { border: 2px solid #8BC34A; border-radius: 8px; background-color: rgba(60, 90, 45, 0.3); }")
        elif progress >= 50:
            day_widget.setStyleSheet("QFrame#dayWidget { border: 2px solid #FFC107; border-radius: 8px; background-color: rgba(90, 90, 45, 0.3); }")
        else:
            day_widget.setStyleSheet("QFrame#dayWidget { border: 2px solid #FF5722; border-radius: 8px; background-color: rgba(90, 45, 45, 0.3); }")

        return day_widget

    def update_income_sources(self, weekly_data: dict):
        """Update income sources analysis with real data"""
        self.sources_table.setRowCount(0)

        # Get real income source analysis for the week
        week_start = self.current_week_start
        week_end = week_start + timedelta(days=6)

        try:
            source_analysis = self.income_model.get_income_source_analysis(week_start, week_end)
            sources_data = source_analysis.get('sources', {})
            total_earned = source_analysis.get('total_earned', 0)

            if not sources_data:
                # Show message when no data is available
                self.sources_table.insertRow(0)
                self.sources_table.setItem(0, 0, QTableWidgetItem("No income data available for this week"))
                self.sources_table.setItem(0, 1, QTableWidgetItem("₹0.00"))
                self.sources_table.setItem(0, 2, QTableWidgetItem("0%"))
                self.sources_table.setItem(0, 3, QTableWidgetItem("₹0.00"))
                return

            # Display real source data
            for i, (source_name, source_data) in enumerate(sources_data.items()):
                self.sources_table.insertRow(i)

                # Format source name
                display_name = source_name.replace('_', ' ').title()
                self.sources_table.setItem(i, 0, QTableWidgetItem(display_name))

                # Real amounts and percentages
                self.sources_table.setItem(i, 1, QTableWidgetItem(f"₹{source_data['total']:.2f}"))
                self.sources_table.setItem(i, 2, QTableWidgetItem(f"{source_data['percentage']:.1f}%"))
                self.sources_table.setItem(i, 3, QTableWidgetItem(f"₹{source_data['average_daily']:.2f}"))

        except Exception as e:
            print(f"Error updating income sources: {e}")
            # Fallback to show no data message
            self.sources_table.insertRow(0)
            self.sources_table.setItem(0, 0, QTableWidgetItem("Error loading income source data"))
            self.sources_table.setItem(0, 1, QTableWidgetItem("₹0.00"))
            self.sources_table.setItem(0, 2, QTableWidgetItem("0%"))
            self.sources_table.setItem(0, 3, QTableWidgetItem("₹0.00"))

    def update_goal_analysis(self, weekly_data: dict):
        """Update goal analysis"""
        daily_breakdown = weekly_data.get('daily_breakdown', [])

        # Count days on track
        days_on_track = sum(1 for day in daily_breakdown if day.get('progress', 0) >= 100)
        self.days_on_track_label.setText(f"{days_on_track}/7")

        # Calculate projections
        total_earned = weekly_data.get('total_earned', 0)
        total_goal = weekly_data.get('total_goal', 0)

        # Simple projection based on current average
        if len(daily_breakdown) > 0:
            days_with_earnings = [d for d in daily_breakdown if d.get('earned', 0) > 0]
            if len(days_with_earnings) > 0:
                avg_daily = total_earned / len(days_with_earnings)
                projected_total = avg_daily * 7
            else:
                projected_total = 0
        else:
            projected_total = 0

        self.projected_total_label.setText(f"₹{projected_total:.2f}")

        # Required daily for remaining days
        remaining_days = 7 - len([d for d in daily_breakdown if d.get('date') <= date.today()])
        if remaining_days > 0:
            remaining_goal = max(0, total_goal - total_earned)
            required_daily = remaining_goal / remaining_days
            self.required_daily_label.setText(f"₹{required_daily:.2f}")
        else:
            self.required_daily_label.setText("Week Complete")

        # Find best and worst performing days
        if daily_breakdown:
            best_day = max(daily_breakdown, key=lambda x: x.get('earned', 0))
            worst_day = min(daily_breakdown, key=lambda x: x.get('earned', 0))

            self.best_performing_day_label.setText(best_day['day_name'])
            self.worst_performing_day_label.setText(worst_day['day_name'])

        # Generate recommendations
        recommendations = []
        if days_on_track < 5:
            recommendations.append("• Focus on consistency - try to meet daily goals more regularly")
        if projected_total < total_goal:
            recommendations.append("• Current pace is below weekly goal - consider increasing daily targets")
        if len(recommendations) == 0:
            recommendations.append("• Great job! You're on track to meet your weekly goal")

        self.recommendations_label.setText("\n".join(recommendations))


# IncomeSourceAnalysisWidget removed - not needed with manual base income settings




# SmartGoalAdjustmentWidget removed - not needed with manual base income settings



class BaseIncomeSettingsWidget(QWidget):
    """Widget for managing base daily income targets"""

    # Signal emitted when base income settings are updated
    base_income_updated = Signal()

    def __init__(self, income_model: IncomeDataModel, parent=None):
        super().__init__(parent)
        self.income_model = income_model
        self.setup_ui()
        self.load_current_settings()






class BaseIncomeSettingsWidget(QWidget):
    """Widget for managing base daily income targets"""

    # Signal emitted when base income settings are updated
    base_income_updated = Signal()

    def __init__(self, income_model: IncomeDataModel, parent=None):
        super().__init__(parent)
        self.income_model = income_model
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        """Setup the base income settings UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Base Daily Income Targets")
        title_label.setObjectName("baseIncomeTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        title_label.setFont(font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Save button
        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.setObjectName("saveBaseIncomeButton")
        self.save_btn.clicked.connect(self.save_settings)
        header_layout.addWidget(self.save_btn)

        layout.addLayout(header_layout)

        # Current settings display
        current_frame = QGroupBox("Current Base Income Structure")
        current_layout = QFormLayout(current_frame)

        self.current_weekday_label = QLabel("₹500.00")
        self.current_weekday_label.setObjectName("currentWeekdayBase")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.current_weekday_label.setFont(font)
        current_layout.addRow("Monday - Friday:", self.current_weekday_label)

        self.current_saturday_label = QLabel("₹700.00")
        self.current_saturday_label.setObjectName("currentSaturdayBase")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.current_saturday_label.setFont(font)
        current_layout.addRow("Saturday:", self.current_saturday_label)

        self.current_sunday_label = QLabel("₹1000.00")
        self.current_sunday_label.setObjectName("currentSundayBase")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.current_sunday_label.setFont(font)
        current_layout.addRow("Sunday:", self.current_sunday_label)

        # Weekly total
        self.weekly_total_label = QLabel("₹4200.00")
        self.weekly_total_label.setObjectName("weeklyTotalBase")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.weekly_total_label.setFont(font)
        self.weekly_total_label.setStyleSheet("color: #2196F3;")
        current_layout.addRow("Weekly Total:", self.weekly_total_label)

        layout.addWidget(current_frame)

        # Edit settings
        edit_frame = QGroupBox("Modify Base Income Targets")
        edit_layout = QFormLayout(edit_frame)

        # Weekday base
        self.weekday_spinbox = QDoubleSpinBox()
        self.weekday_spinbox.setRange(0.0, 9999.99)
        self.weekday_spinbox.setDecimals(2)
        self.weekday_spinbox.setPrefix("₹ ")
        self.weekday_spinbox.setValue(500.0)
        self.weekday_spinbox.valueChanged.connect(self.update_preview)
        edit_layout.addRow("Monday - Friday Base:", self.weekday_spinbox)

        # Saturday base
        self.saturday_spinbox = QDoubleSpinBox()
        self.saturday_spinbox.setRange(0.0, 9999.99)
        self.saturday_spinbox.setDecimals(2)
        self.saturday_spinbox.setPrefix("₹ ")
        self.saturday_spinbox.setValue(700.0)
        self.saturday_spinbox.valueChanged.connect(self.update_preview)
        edit_layout.addRow("Saturday Base:", self.saturday_spinbox)

        # Sunday base
        self.sunday_spinbox = QDoubleSpinBox()
        self.sunday_spinbox.setRange(0.0, 9999.99)
        self.sunday_spinbox.setDecimals(2)
        self.sunday_spinbox.setPrefix("₹ ")
        self.sunday_spinbox.setValue(1000.0)
        self.sunday_spinbox.valueChanged.connect(self.update_preview)
        edit_layout.addRow("Sunday Base:", self.sunday_spinbox)

        # Preview
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        # Theme-aware styling will be applied later
        preview_layout = QFormLayout(preview_frame)

        self.preview_weekly_label = QLabel("₹4200.00")
        self.preview_weekly_label.setStyleSheet("color: #666; font-style: italic; font-weight: bold;")
        preview_layout.addRow("→ New Weekly Total:", self.preview_weekly_label)

        self.preview_monthly_label = QLabel("₹18,000.00")
        self.preview_monthly_label.setStyleSheet("color: #666; font-style: italic; font-weight: bold;")
        preview_layout.addRow("→ Monthly Base Target:", self.preview_monthly_label)

        edit_layout.addRow("Preview:", preview_frame)

        layout.addWidget(edit_frame)

        # Information section
        info_frame = QGroupBox("How Base Income Works")
        info_layout = QVBoxLayout(info_frame)

        info_text = QLabel(
            "• Base income targets represent your minimum daily earning goals\n"
            "• Any earnings above the base amount are tracked as 'bonus' income\n"
            "• This helps you maintain consistent income while tracking extra achievements\n"
            "• All views will show base vs bonus breakdown for better insights"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666; padding: 10px;")
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)

        layout.addStretch()

    def load_current_settings(self):
        """Load current base income settings"""
        try:
            settings = self.income_model.get_current_base_income_settings()

            # Ensure values are floats before using them
            weekday_base = float(settings.weekday_base)
            saturday_base = float(settings.saturday_base)
            sunday_base = float(settings.sunday_base)

            # Update current display
            self.current_weekday_label.setText(f"₹{weekday_base:.2f}")
            self.current_saturday_label.setText(f"₹{saturday_base:.2f}")
            self.current_sunday_label.setText(f"₹{sunday_base:.2f}")

            # Update spinboxes
            self.weekday_spinbox.setValue(weekday_base)
            self.saturday_spinbox.setValue(saturday_base)
            self.sunday_spinbox.setValue(sunday_base)

            # Update current weekly total display
            self.update_current_weekly_total()

            # Update preview calculations
            self.update_preview()

        except Exception as e:
            print(f"Error loading base income settings: {e}")
            # Set default values if loading fails
            self.current_weekday_label.setText("₹500.00")
            self.current_saturday_label.setText("₹700.00")
            self.current_sunday_label.setText("₹1000.00")
            self.weekday_spinbox.setValue(500.0)
            self.saturday_spinbox.setValue(700.0)
            self.sunday_spinbox.setValue(1000.0)

            # Update current weekly total display
            self.update_current_weekly_total()

            # Update preview calculations
            self.update_preview()

    def update_preview(self):
        """Update preview calculations"""
        try:
            # Get values from spinboxes for preview calculations
            weekday_base = self.weekday_spinbox.value()
            saturday_base = self.saturday_spinbox.value()
            sunday_base = self.sunday_spinbox.value()

            # Calculate weekly total for preview (5 weekdays + 1 Saturday + 1 Sunday)
            weekly_total = (weekday_base * 5) + saturday_base + sunday_base

            # Calculate monthly estimate (4.33 weeks average)
            monthly_estimate = weekly_total * 4.33

            # Update preview labels (these show what the new values would be)
            self.preview_weekly_label.setText(f"₹{weekly_total:,.2f}")
            self.preview_monthly_label.setText(f"₹{monthly_estimate:,.2f}")

        except Exception as e:
            print(f"Error updating preview: {e}")
            # Set default values if calculation fails
            self.preview_weekly_label.setText("₹0.00")
            self.preview_monthly_label.setText("₹0.00")

    def update_current_weekly_total(self):
        """Update the current weekly total display based on current settings"""
        try:
            # Parse current values from the display labels
            current_weekday = float(self.current_weekday_label.text().replace('₹', '').replace(',', ''))
            current_saturday = float(self.current_saturday_label.text().replace('₹', '').replace(',', ''))
            current_sunday = float(self.current_sunday_label.text().replace('₹', '').replace(',', ''))

            # Calculate current weekly total
            current_weekly = (current_weekday * 5) + current_saturday + current_sunday
            self.weekly_total_label.setText(f"₹{current_weekly:,.2f}")

        except (ValueError, AttributeError) as e:
            print(f"Error updating current weekly total: {e}")
            # Fallback to loading from settings
            try:
                settings = self.income_model.get_current_base_income_settings()
                weekly_total = (settings.weekday_base * 5) + settings.saturday_base + settings.sunday_base
                self.weekly_total_label.setText(f"₹{weekly_total:,.2f}")
            except Exception as fallback_error:
                print(f"Error in fallback weekly total calculation: {fallback_error}")
                self.weekly_total_label.setText("₹0.00")

    def save_settings(self):
        """Save the new base income settings"""
        try:
            from .models import BaseIncomeSettings

            new_settings = BaseIncomeSettings(
                weekday_base=self.weekday_spinbox.value(),
                saturday_base=self.saturday_spinbox.value(),
                sunday_base=self.sunday_spinbox.value()
            )

            if self.income_model.update_base_income_settings(new_settings):
                # Calculate weekly total for success message
                weekly_total = new_settings.weekday_base * 5 + new_settings.saturday_base + new_settings.sunday_base

                # Show success message
                QMessageBox.information(
                    self, "Success",
                    "Base income settings updated successfully!\n\n"
                    f"New weekly base target: ₹{weekly_total:,.2f}"
                )

                # Reload current settings to reflect changes in UI
                self.load_current_settings()

                # Emit signal for optimized refresh of dependent widgets
                print("Base income settings saved - emitting update signal")
                self.base_income_updated.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to save base income settings")

        except Exception as e:
            print(f"Error saving base income settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save settings: {str(e)}")


class GoalSettingsDialog(QDialog):
    """Dialog for managing goal settings"""

    goals_updated = Signal()

    def __init__(self, data_model: IncomeDataModel, parent=None):
        super().__init__(parent)

        self.data_model = data_model
        self.setup_ui()
        self.setup_connections()
        self.load_goals()

        self.setModal(True)

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Goal Settings")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        # Current goal section - Unified Goal Display
        current_frame = QGroupBox("Current Goal Settings")
        current_layout = QFormLayout(current_frame)

        # Monthly goal (primary)
        self.current_monthly_goal_label = QLabel("₹0.00")
        self.current_monthly_goal_label.setObjectName("incomeCurrentMonthlyGoalLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.current_monthly_goal_label.setFont(font)
        current_layout.addRow("Monthly Goal:", self.current_monthly_goal_label)

        # Auto-calculated daily goal
        self.current_daily_goal_label = QLabel("₹0.00")
        self.current_daily_goal_label.setObjectName("incomeCurrentDailyGoalLabel")
        font = QFont()
        font.setPointSize(12)
        self.current_daily_goal_label.setFont(font)
        current_layout.addRow("Daily Goal (Auto):", self.current_daily_goal_label)

        # Auto-calculated yearly goal
        self.current_yearly_goal_label = QLabel("₹0.00")
        self.current_yearly_goal_label.setObjectName("incomeCurrentYearlyGoalLabel")
        font = QFont()
        font.setPointSize(12)
        self.current_yearly_goal_label.setFont(font)
        current_layout.addRow("Yearly Goal (Auto):", self.current_yearly_goal_label)

        layout.addWidget(current_frame)

        # Set new monthly goal section
        add_frame = QGroupBox("Set New Monthly Goal")
        add_layout = QFormLayout(add_frame)

        self.new_goal_name = QLineEdit()
        self.new_goal_name.setPlaceholderText("e.g., 'Updated Monthly Target'")
        add_layout.addRow("Goal Name:", self.new_goal_name)

        # Monthly amount input
        self.new_goal_amount = QDoubleSpinBox()
        self.new_goal_amount.setRange(1000.0, 999999.99)
        self.new_goal_amount.setDecimals(2)
        self.new_goal_amount.setPrefix("₹ ")
        self.new_goal_amount.setValue(30000.0)  # Default monthly goal
        self.new_goal_amount.valueChanged.connect(self.update_preview_calculations)
        add_layout.addRow("Monthly Amount:", self.new_goal_amount)

        # Preview calculations
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        # Theme-aware styling will be applied later
        preview_layout = QFormLayout(preview_frame)

        self.preview_daily_label = QLabel("₹0.00")
        self.preview_daily_label.setStyleSheet("color: #666; font-style: italic;")
        preview_layout.addRow("→ Daily Goal:", self.preview_daily_label)

        self.preview_yearly_label = QLabel("₹0.00")
        self.preview_yearly_label.setStyleSheet("color: #666; font-style: italic;")
        preview_layout.addRow("→ Yearly Goal:", self.preview_yearly_label)

        add_layout.addRow("Auto-calculated:", preview_frame)

        self.new_goal_description = QTextEdit()
        self.new_goal_description.setMaximumHeight(60)
        self.new_goal_description.setPlaceholderText("Optional description...")
        add_layout.addRow("Description:", self.new_goal_description)

        add_button = QPushButton("Set Monthly Goal")
        add_button.setObjectName("incomeAddGoalButton")
        add_button.clicked.connect(self.add_goal)
        add_layout.addRow("", add_button)

        layout.addWidget(add_frame)

        # Initialize preview
        self.update_preview_calculations()

        # Monthly goals history table
        history_frame = QGroupBox("Monthly Goal History")
        history_layout = QVBoxLayout(history_frame)

        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(6)
        self.goals_table.setHorizontalHeaderLabels(["Name", "Monthly Amount", "Daily (Auto)", "Active", "Created", "Actions"])
        self.goals_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        history_layout.addWidget(self.goals_table)

        layout.addWidget(history_frame)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def setup_connections(self):
        """Setup signal connections"""
        pass

    def update_preview_calculations(self):
        """Update the preview calculations for daily and yearly goals"""
        monthly_amount = self.new_goal_amount.value()

        # Calculate daily goal (using current month)
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        daily_amount = monthly_amount / days_in_month

        # Calculate yearly goal
        yearly_amount = monthly_amount * 12

        # Update preview labels
        self.preview_daily_label.setText(f"₹{daily_amount:.2f}")
        self.preview_yearly_label.setText(f"₹{yearly_amount:,.2f}")

    def load_goals(self):
        """Load goals into the interface"""
        # Update current goals display
        monthly_goal = self.data_model.get_current_monthly_goal()
        daily_goal = self.data_model.get_current_daily_goal()
        yearly_goal = self.data_model.get_current_yearly_goal()

        self.current_monthly_goal_label.setText(f"₹{monthly_goal:,.2f}")
        self.current_daily_goal_label.setText(f"₹{daily_goal:.2f}")
        self.current_yearly_goal_label.setText(f"₹{yearly_goal:,.2f}")

        # Load monthly goals table
        df = self.data_model.get_all_goals()

        # Filter for monthly goals only
        if not df.empty:
            monthly_goals = df[df['period'] == 'Monthly']
        else:
            monthly_goals = df

        if monthly_goals.empty:
            self.goals_table.setRowCount(0)
            return

        self.goals_table.setRowCount(len(monthly_goals))

        for row, (_, goal) in enumerate(monthly_goals.iterrows()):
            goal_id = goal['id']
            monthly_amount = float(goal['amount'])

            # Calculate daily amount for display
            today = date.today()
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            daily_amount = monthly_amount / days_in_month

            # Goal details
            self.goals_table.setItem(row, 0, QTableWidgetItem(str(goal['name'])))
            self.goals_table.setItem(row, 1, QTableWidgetItem(f"₹{monthly_amount:,.2f}"))
            self.goals_table.setItem(row, 2, QTableWidgetItem(f"₹{daily_amount:.2f}"))

            # Active checkbox with functionality
            checkbox = QCheckBox()
            checkbox.setChecked(bool(goal['is_active']))
            checkbox.stateChanged.connect(lambda state, gid=goal_id: self.toggle_goal_status(gid, state))
            self.goals_table.setCellWidget(row, 3, checkbox)

            # Created date
            created_date = goal['created_at']
            if isinstance(created_date, str):
                try:
                    created_date = datetime.strptime(created_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                except ValueError:
                    pass
            self.goals_table.setItem(row, 4, QTableWidgetItem(str(created_date)))

            # Actions container
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            # Edit button
            edit_btn = QPushButton("✏️")
            edit_btn.setObjectName("incomeEditGoalButton")
            edit_btn.setToolTip("Edit Goal")
            edit_btn.setMaximumWidth(30)
            edit_btn.clicked.connect(lambda checked, gid=goal_id: self.edit_goal(gid))
            actions_layout.addWidget(edit_btn)

            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setObjectName("incomeDeleteGoalButton")
            delete_btn.setToolTip("Delete Goal")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda checked, gid=goal_id: self.delete_goal(gid))
            actions_layout.addWidget(delete_btn)

            self.goals_table.setCellWidget(row, 5, actions_widget)

        # Resize columns to content
        self.goals_table.resizeColumnsToContents()

    def add_goal(self):
        """Add a new monthly goal"""
        name = self.new_goal_name.text().strip()
        amount = self.new_goal_amount.value()
        description = self.new_goal_description.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Goal name is required")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Error", "Monthly goal amount must be greater than 0")
            return

        # Deactivate existing monthly goals first
        existing_goals = self.data_model.get_all_goals()
        if not existing_goals.empty:
            monthly_goals = existing_goals[existing_goals['period'] == 'Monthly']
            for _, goal_row in monthly_goals.iterrows():
                if goal_row['is_active']:
                    goal = GoalSetting.from_dict(goal_row.to_dict())
                    goal.is_active = False
                    self.data_model.update_goal(goal_row['id'], goal)

        # Create new monthly goal
        goal = GoalSetting(
            name=name,
            period="Monthly",  # Always monthly
            amount=amount,
            description=description,
            is_active=True
        )

        if self.data_model.add_goal(goal):
            self.new_goal_name.clear()
            self.new_goal_amount.setValue(30000.0)  # Reset to default monthly amount
            self.new_goal_description.clear()
            self.load_goals()
            self.goals_updated.emit()

            # Calculate and show the derived goals
            daily_goal = self.data_model.get_current_daily_goal()
            yearly_goal = self.data_model.get_current_yearly_goal()

            QMessageBox.information(
                self, "Success",
                f"Monthly goal set successfully!\n\n"
                f"Monthly Goal: ₹{amount:,.2f}\n"
                f"Daily Goal: ₹{daily_goal:.2f}\n"
                f"Yearly Goal: ₹{yearly_goal:,.2f}"
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to set monthly goal")

    def toggle_goal_status(self, goal_id: int, state: int):
        """Toggle goal active status"""
        try:
            # Get the goal
            df = self.data_model.get_all_goals()
            goal_row = df[df['id'] == goal_id]

            if goal_row.empty:
                QMessageBox.warning(self, "Error", "Goal not found")
                return

            # Create updated goal
            goal_data = goal_row.iloc[0].to_dict()
            goal_data['is_active'] = state == 2  # Qt.Checked = 2
            goal = GoalSetting.from_dict(goal_data)

            # Update in database
            if self.data_model.update_goal(goal_id, goal):
                self.goals_updated.emit()
                QMessageBox.information(self, "Success", f"Goal {'activated' if goal.is_active else 'deactivated'} successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to update goal status")
                self.load_goals()  # Reload to reset checkbox

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating goal status: {str(e)}")
            self.load_goals()  # Reload to reset checkbox

    def edit_goal(self, goal_id: int):
        """Edit an existing goal"""
        try:
            # Get the goal
            df = self.data_model.get_all_goals()
            goal_row = df[df['id'] == goal_id]

            if goal_row.empty:
                QMessageBox.warning(self, "Error", "Goal not found")
                return

            # Create edit dialog
            goal_data = goal_row.iloc[0].to_dict()
            goal = GoalSetting.from_dict(goal_data)

            dialog = EditGoalDialog(goal, self.data_model, self)
            if dialog.exec() == QDialog.Accepted:
                self.load_goals()
                self.goals_updated.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editing goal: {str(e)}")

    def delete_goal(self, goal_id: int):
        """Delete a goal"""
        try:
            # Get the goal
            df = self.data_model.get_all_goals()
            goal_row = df[df['id'] == goal_id]

            if goal_row.empty:
                QMessageBox.warning(self, "Error", "Goal not found")
                return

            goal_name = goal_row.iloc[0]['name']

            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                f"Are you sure you want to delete the goal '{goal_name}'?\n\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if self.data_model.delete_goal(goal_id):
                    self.load_goals()
                    self.goals_updated.emit()
                    QMessageBox.information(self, "Success", "Goal deleted successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete goal")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error deleting goal: {str(e)}")


class EditGoalDialog(QDialog):
    """Dialog for editing an existing goal"""

    def __init__(self, goal: GoalSetting, data_model: IncomeDataModel, parent=None):
        super().__init__(parent)

        self.goal = goal
        self.data_model = data_model
        self.setup_ui()
        self.load_goal_data()

        self.setModal(True)
        self.setWindowTitle("Edit Goal")
        self.resize(400, 300)

    def setup_ui(self):
        """Setup the edit goal dialog UI"""
        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Goal name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter goal name...")
        form_layout.addRow("Name:", self.name_edit)

        # Goal period
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Daily", "Weekly", "Monthly", "Yearly"])
        form_layout.addRow("Period:", self.period_combo)

        # Goal amount
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.0, 999999.99)
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setPrefix("₹ ")
        form_layout.addRow("Amount:", self.amount_spinbox)

        # Start date
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date_edit)

        # End date
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addDays(30))
        self.end_date_edit.setCalendarPopup(True)
        form_layout.addRow("End Date:", self.end_date_edit)

        # Active status
        self.active_checkbox = QCheckBox("Goal is active")
        form_layout.addRow("", self.active_checkbox)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.setPlaceholderText("Optional description...")
        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        save_button = QPushButton("Save Changes")
        save_button.setObjectName("incomeSaveGoalButton")
        save_button.clicked.connect(self.save_goal)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def load_goal_data(self):
        """Load existing goal data into the form"""
        self.name_edit.setText(self.goal.name)
        self.period_combo.setCurrentText(self.goal.period)
        self.amount_spinbox.setValue(self.goal.amount)
        self.active_checkbox.setChecked(self.goal.is_active)

        if self.goal.description:
            # Ensure description is a string
            description_text = str(self.goal.description) if self.goal.description is not None else ""
            self.description_edit.setPlainText(description_text)

        # Set dates if available
        if self.goal.start_date:
            if isinstance(self.goal.start_date, str):
                try:
                    start_date = datetime.strptime(self.goal.start_date, '%Y-%m-%d').date()
                    self.start_date_edit.setDate(QDate(start_date))
                except ValueError:
                    pass
            elif isinstance(self.goal.start_date, (date, datetime)):
                if isinstance(self.goal.start_date, datetime):
                    start_date = self.goal.start_date.date()
                else:
                    start_date = self.goal.start_date
                self.start_date_edit.setDate(QDate(start_date))

        if self.goal.end_date:
            if isinstance(self.goal.end_date, str):
                try:
                    end_date = datetime.strptime(self.goal.end_date, '%Y-%m-%d').date()
                    self.end_date_edit.setDate(QDate(end_date))
                except ValueError:
                    pass
            elif isinstance(self.goal.end_date, (date, datetime)):
                if isinstance(self.goal.end_date, datetime):
                    end_date = self.goal.end_date.date()
                else:
                    end_date = self.goal.end_date
                self.end_date_edit.setDate(QDate(end_date))

    def save_goal(self):
        """Save the edited goal"""
        name = self.name_edit.text().strip()
        period = self.period_combo.currentText()
        amount = self.amount_spinbox.value()
        description = self.description_edit.toPlainText().strip()
        is_active = self.active_checkbox.isChecked()

        if not name:
            QMessageBox.warning(self, "Error", "Goal name is required")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Error", "Goal amount must be greater than 0")
            return

        # Update goal object
        self.goal.name = name
        self.goal.period = period
        self.goal.amount = amount
        self.goal.description = description
        self.goal.is_active = is_active
        self.goal.start_date = self.start_date_edit.date().toPython()
        self.goal.end_date = self.end_date_edit.date().toPython()

        # Save to database
        if self.data_model.update_goal(self.goal.id, self.goal):
            QMessageBox.information(self, "Success", "Goal updated successfully")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to update goal")


class IncomeTrackerWidget(QWidget):
    """Main income goal tracker widget"""

    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        self.data_manager = data_manager
        self.config = config
        self.income_model = IncomeDataModel(data_manager)
        self.current_week_start = None
        self.current_theme = 'dark'  # Default theme

        self.setup_ui()
        self.setup_connections()
        self.setup_base_income_connections()  # Set up base income signal connections after tabs are created
        self.refresh_data()

        # Setup auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(60000)  # Refresh every minute

    def get_theme_colors(self, theme_name: str = 'dark') -> dict:
        """Get theme-specific color palette"""
        if theme_name == 'dark':
            return {
                'background': '#1e1e1e',
                'surface': '#252526',
                'surface_light': '#2d2d30',
                'border': '#3e3e42',
                'border_light': '#464647',
                'text': '#ffffff',
                'text_secondary': '#cccccc',
                'accent': '#0e639c',
                'accent_hover': '#1177bb',
                'success': '#4caf50',
                'warning': '#ff9800',
                'error': '#f44336',
                'progress_bg': '#2d2d30',
                'progress_chunk': '#0e639c',
                'input_bg': '#252526',
                'input_border': '#3e3e42'
            }
        else:  # light theme
            return {
                'background': '#ffffff',
                'surface': '#f8f9fa',
                'surface_light': '#e9ecef',
                'border': '#d0d0d0',
                'border_light': '#e0e0e0',
                'text': '#000000',
                'text_secondary': '#666666',
                'accent': '#0078d4',
                'accent_hover': '#106ebe',
                'success': '#28a745',
                'warning': '#ffc107',
                'error': '#dc3545',
                'progress_bg': '#f8f9fa',
                'progress_chunk': '#0078d4',
                'input_bg': '#ffffff',
                'input_border': '#d0d0d0'
            }

    def apply_theme(self, theme_name: str = 'dark'):
        """Apply theme to all income tracker widgets"""
        try:
            print(f"🎨 DEBUG: IncomeTrackerWidget.apply_theme called with theme: {theme_name}")
            self.current_theme = theme_name
            colors = self.get_theme_colors(theme_name)

            # Apply theme to all tabs
            widgets_styled = 0

            # Apply to main tab widget
            if hasattr(self, 'tab_widget'):
                self.tab_widget.setStyleSheet(f"""
                    QTabWidget::pane {{
                        border: 1px solid {colors['border']};
                        background-color: {colors['background']};
                    }}
                    QTabBar::tab {{
                        background-color: {colors['surface']};
                        color: {colors['text']};
                        border: 1px solid {colors['border']};
                        padding: 8px 16px;
                        margin-right: 2px;
                    }}
                    QTabBar::tab:selected {{
                        background-color: {colors['accent']};
                        color: white;
                    }}
                    QTabBar::tab:hover {{
                        background-color: {colors['accent_hover']};
                        color: white;
                    }}
                """)
                widgets_styled += 1

            # Apply theme to all child widgets
            self.apply_theme_to_children(colors)

            print(f"✅ SUCCESS: Applied theme '{theme_name}' to Income Tracker widgets")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to Income Tracker: {e}")

    def apply_theme_to_children(self, colors: dict):
        """Apply theme to all child widgets recursively"""
        try:
            widgets_styled = 0

            # Apply to all input widgets (need to search for each type separately)
            input_widgets = []
            input_widgets.extend(self.findChildren(QLineEdit))
            input_widgets.extend(self.findChildren(QTextEdit))
            input_widgets.extend(self.findChildren(QSpinBox))
            input_widgets.extend(self.findChildren(QDoubleSpinBox))

            for widget in input_widgets:
                widget.setStyleSheet(f"""
                    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
                        background-color: {colors['input_bg']};
                        border: 2px solid {colors['input_border']};
                        border-radius: 4px;
                        padding: 6px;
                        color: {colors['text']};
                        selection-background-color: {colors['accent']};
                    }}
                    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                        border-color: {colors['accent']};
                    }}
                """)
                widgets_styled += 1

            # Apply to all progress bars
            for progress_bar in self.findChildren(QProgressBar):
                progress_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: 2px solid {colors['border']};
                        border-radius: 8px;
                        text-align: center;
                        font-weight: bold;
                        font-size: 11px;
                        background-color: {colors['progress_bg']};
                        color: {colors['text']};
                        min-height: 25px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {colors['progress_chunk']};
                        border-radius: 6px;
                        margin: 1px;
                    }}
                """)
                widgets_styled += 1

            # Apply to preview frames
            for frame in self.findChildren(QFrame):
                if frame.objectName() == "previewFrame":
                    frame.setStyleSheet(f"""
                        QFrame#previewFrame {{
                            background-color: {colors['surface']};
                            border: 1px solid {colors['border']};
                            border-radius: 5px;
                            padding: 10px;
                            color: {colors['text']};
                        }}
                    """)
                    widgets_styled += 1
                elif frame.objectName() == "primaryActionsFrame":
                    frame.setStyleSheet(f"""
                        QFrame#primaryActionsFrame {{
                            background-color: {colors['surface']};
                            border: 1px solid {colors['border']};
                            border-radius: 8px;
                            padding: 10px;
                            color: {colors['text']};
                        }}
                    """)
                    widgets_styled += 1
                elif frame.objectName() == "secondaryActionsFrame":
                    frame.setStyleSheet(f"""
                        QFrame#secondaryActionsFrame {{
                            background-color: {colors['surface']};
                            border: 1px solid {colors['border']};
                            border-radius: 8px;
                            padding: 10px;
                            color: {colors['text']};
                        }}
                    """)
                    widgets_styled += 1
                elif frame.objectName() == "sourceItemFrame":
                    accent_color = frame.property("accent_color") or colors['accent']
                    frame.setStyleSheet(f"""
                        QFrame#sourceItemFrame {{
                            background-color: {colors['surface']};
                            border-left: 4px solid {accent_color};
                            border-radius: 6px;
                            padding: 8px 12px;
                            margin: 2px 0;
                            color: {colors['text']};
                        }}
                        QFrame#sourceItemFrame:hover {{
                            background-color: {colors['surface_light']};
                        }}
                    """)
                    widgets_styled += 1

            # Apply theme to child view widgets (need to search for each type separately)
            child_widgets = []
            child_widgets.extend(self.findChildren(MonthlyViewWidget))
            child_widgets.extend(self.findChildren(YearlyViewWidget))

            for child_widget in child_widgets:
                if hasattr(child_widget, 'apply_theme'):
                    child_widget.apply_theme(self.current_theme)
                    widgets_styled += 1

            print(f"🎨 DEBUG: Applied theme to {widgets_styled} widgets in main IncomeTrackerWidget")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to child widgets: {e}")

    def update_theme(self, theme_name: str = 'dark'):
        """Update theme - compatibility method for main window theme propagation"""
        self.apply_theme(theme_name)

    def setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 20px to 10px
        layout.setSpacing(8)  # Reduced from 15px to 8px

        # Header
        self.create_header(layout)

        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("incomeTabWidget")

        # Today tab
        self.today_tab = self.create_today_tab()
        self.tab_widget.addTab(self.today_tab, "Today")

        # Weekly tab
        self.weekly_tab = self.create_weekly_tab()
        self.tab_widget.addTab(self.weekly_tab, "Weekly View")

        # Monthly tab
        self.monthly_tab = self.create_monthly_tab()
        self.tab_widget.addTab(self.monthly_tab, "Monthly View")

        # Yearly tab
        self.yearly_tab = self.create_yearly_tab()
        self.tab_widget.addTab(self.yearly_tab, "Yearly View")

        # Records tab for editing historical data
        self.records_tab = self.create_records_tab()
        self.tab_widget.addTab(self.records_tab, "All Records")

        # Statistics tab
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")

        # Analytics Dashboard moved to main Dashboard tab - no longer needed here

        # Source Analysis and Smart Goals tabs removed - not needed with manual base income settings

        # Base Income Settings tab
        self.base_income_tab = BaseIncomeSettingsWidget(self.income_model)
        self.tab_widget.addTab(self.base_income_tab, "Base Income")

        # Connect tab change to refresh data
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)

    def create_header(self, layout):
        """Create header with title only"""
        header_frame = QFrame()
        header_frame.setObjectName("incomeHeader")
        header_frame.setMaximumHeight(50)  # Standardized header height
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)  # Standardized margins
        header_layout.setSpacing(8)  # Standardized spacing

        # Title
        title_label = QLabel("Goal Income Tracker")
        title_label.setObjectName("incomeTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)  # Standardized font size
        title_label.setFont(font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        layout.addWidget(header_frame)

    def create_today_tab(self):
        """Create today's income tracking tab with redesigned layout"""
        tab = QWidget()

        # Create main scroll area for the entire tab
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setFrameShape(QFrame.NoFrame)

        # Main content widget
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        # === TOP SECTION: Overview Cards ===
        self.create_overview_section(main_layout)

        # === MIDDLE SECTION: Progress and Actions ===
        self.create_progress_and_actions_section(main_layout)

        # === BOTTOM SECTION: Detailed Breakdown ===
        self.create_detailed_breakdown_section(main_layout)

        # Set up scroll area
        main_scroll.setWidget(content_widget)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(main_scroll)

        return tab

    def create_overview_section(self, layout):
        """Create the top overview section with key metrics"""
        overview_frame = QFrame()
        overview_frame.setObjectName("todayOverviewFrame")
        # CRITICAL FIX: Remove all hardcoded styling to let global theme handle it completely

        overview_layout = QVBoxLayout(overview_frame)
        overview_layout.setSpacing(15)

        # Section title
        title_label = QLabel("📊 Today's Overview")
        title_label.setObjectName("sectionTitle")
        title_label.setStyleSheet("""
            QLabel#sectionTitle {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        overview_layout.addWidget(title_label)

        # Metrics cards in a horizontal layout
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(15)

        # Create metric cards
        self.create_metric_card(metrics_layout, "💰 Total Earned", "₹0.00", "totalEarned")
        self.create_metric_card(metrics_layout, "🎯 Goal Progress", "0%", "goalProgress")
        self.create_metric_card(metrics_layout, "⏰ Remaining", "₹0.00", "remaining")
        self.create_metric_card(metrics_layout, "🔥 Streak", "0 days", "streak")

        overview_layout.addLayout(metrics_layout)
        layout.addWidget(overview_frame)

    def create_metric_card(self, layout, title, value, object_name):
        """Create a metric card widget - FIXED: Remove hardcoded styling, use global theme"""
        card = QFrame()
        card.setObjectName(f"metricCard_{object_name}")
        # CRITICAL FIX: Remove all hardcoded styling to let global theme handle it

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(5)

        # Value label (main metric)
        value_label = QLabel(value)
        value_label.setObjectName(f"metricValue_{object_name}")
        value_label.setAlignment(Qt.AlignCenter)
        # CRITICAL FIX: Remove hardcoded styling to let global theme handle it

        # Title label
        title_label = QLabel(title)
        title_label.setObjectName(f"metricTitle_{object_name}")
        title_label.setAlignment(Qt.AlignCenter)
        # CRITICAL FIX: Remove hardcoded styling to let global theme handle it

        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)

        # Store references for updates
        setattr(self, f"metric_{object_name}_value", value_label)

        layout.addWidget(card)

    def create_progress_and_actions_section(self, layout):
        """Create the middle section with progress tracking and quick actions"""
        # Horizontal layout for progress and actions
        progress_actions_layout = QHBoxLayout()
        progress_actions_layout.setSpacing(20)

        # === LEFT: Enhanced Progress Tracking ===
        progress_container = QFrame()
        progress_container.setObjectName("progressContainer")
        progress_container.setStyleSheet("""
            QFrame#progressContainer {
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
            }
        """)

        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setSpacing(15)

        # Progress section title
        progress_title = QLabel("📈 Goal Progress & Insights")
        progress_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        progress_layout.addWidget(progress_title)

        # Add the enhanced daily goal widget (existing)
        self.daily_goal_widget = EnhancedDailyGoalWidget(self.income_model)
        progress_layout.addWidget(self.daily_goal_widget)

        progress_actions_layout.addWidget(progress_container, 2)  # 2/3 width

        # === RIGHT: Quick Actions Panel ===
        actions_container = QFrame()
        actions_container.setObjectName("actionsContainer")
        actions_container.setStyleSheet("""
            QFrame#actionsContainer {
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
            }
        """)

        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setSpacing(15)

        # Actions section title
        actions_title = QLabel("⚡ Quick Actions")
        actions_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        actions_layout.addWidget(actions_title)

        # Create modern quick action buttons
        self.create_quick_actions_grid(actions_layout)

        progress_actions_layout.addWidget(actions_container, 1)  # 1/3 width

        layout.addLayout(progress_actions_layout)

    def create_quick_actions_grid(self, layout):
        """Create modern quick action buttons grid"""
        # Primary actions (most used)
        primary_frame = QFrame()
        primary_frame.setObjectName("primaryActionsFrame")
        # Theme-aware styling will be applied later
        primary_layout = QVBoxLayout(primary_frame)
        primary_layout.setSpacing(8)

        primary_label = QLabel("🎯 Primary Sources")
        primary_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 12px;")
        primary_layout.addWidget(primary_label)

        primary_grid = QGridLayout()
        primary_grid.setSpacing(8)

        # Create primary action buttons
        primary_sources = [
            ("Zomato", "zomato", "#ff6b6b"),
            ("Swiggy", "swiggy", "#4ecdc4"),
            ("Shadow Fax", "shadow_fax", "#45b7d1"),
            ("PC Repair", "pc_repair", "#96ceb4")
        ]

        for i, (name, source, color) in enumerate(primary_sources):
            btn = self.create_action_button(name, source, color)
            primary_grid.addWidget(btn, i // 2, i % 2)

        primary_layout.addLayout(primary_grid)
        layout.addWidget(primary_frame)

        # Secondary actions
        secondary_frame = QFrame()
        secondary_frame.setObjectName("secondaryActionsFrame")
        # Theme-aware styling will be applied later
        secondary_layout = QVBoxLayout(secondary_frame)
        secondary_layout.setSpacing(8)

        secondary_label = QLabel("💼 Other Sources")
        secondary_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 12px;")
        secondary_layout.addWidget(secondary_label)

        secondary_grid = QGridLayout()
        secondary_grid.setSpacing(8)

        # Create secondary action buttons
        secondary_sources = [
            ("YouTube", "youtube", "#ff7675"),
            ("GP Links", "gp_links", "#a29bfe"),
            ("ID Sales", "id_sales", "#fd79a8"),
            ("Settings", "settings", "#fdcb6e"),
            ("Extra Work", "extra_work", "#6c5ce7"),
            ("Other", "other", "#74b9ff")
        ]

        for i, (name, source, color) in enumerate(secondary_sources):
            btn = self.create_action_button(name, source, color)
            secondary_grid.addWidget(btn, i // 2, i % 2)

        secondary_layout.addLayout(secondary_grid)
        layout.addWidget(secondary_frame)

        layout.addStretch()

    def create_action_button(self, name, source, color):
        """Create a modern action button"""
        btn = QPushButton(name)
        btn.setObjectName(f"modernActionButton_{source}")
        btn.setMinimumHeight(40)
        btn.setStyleSheet(f"""
            QPushButton#modernActionButton_{source} {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 8px;
            }}
            QPushButton#modernActionButton_{source}:hover {{
                background-color: {self.darken_color(color)};
                transform: translateY(-1px);
            }}
            QPushButton#modernActionButton_{source}:pressed {{
                background-color: {self.darken_color(color, 0.3)};
            }}
        """)
        btn.clicked.connect(lambda: self.quick_add_source(source))

        # Store reference for later use
        setattr(self, f"quick_{source}_button", btn)

        return btn

    def darken_color(self, hex_color, factor=0.2):
        """Darken a hex color by a factor"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        # Convert to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Darken
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        # Convert back to hex
        return f"#{''.join(f'{c:02x}' for c in darkened)}"

    def create_detailed_breakdown_section(self, layout):
        """Create the bottom section with detailed breakdown and insights"""
        breakdown_layout = QHBoxLayout()
        breakdown_layout.setSpacing(20)

        # === LEFT: Source Breakdown ===
        breakdown_container = QFrame()
        breakdown_container.setObjectName("breakdownContainer")
        breakdown_container.setStyleSheet("""
            QFrame#breakdownContainer {
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
            }
        """)

        breakdown_frame_layout = QVBoxLayout(breakdown_container)
        breakdown_frame_layout.setSpacing(15)

        # Breakdown title
        breakdown_title = QLabel("📋 Today's Breakdown")
        breakdown_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        breakdown_frame_layout.addWidget(breakdown_title)

        # Create source breakdown with modern styling
        self.create_source_breakdown_list(breakdown_frame_layout)

        breakdown_layout.addWidget(breakdown_container, 2)  # 2/3 width

        # === RIGHT: Insights and Notes ===
        insights_container = QFrame()
        insights_container.setObjectName("insightsContainer")
        insights_container.setStyleSheet("""
            QFrame#insightsContainer {
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
            }
        """)

        insights_layout = QVBoxLayout(insights_container)
        insights_layout.setSpacing(15)

        # Insights title
        insights_title = QLabel("💡 Insights & Notes")
        insights_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 10px;
        """)
        insights_layout.addWidget(insights_title)

        # Add stylish visualization widget
        self.stylish_viz_widget = StylishIncomeVisualizationWidget()
        insights_layout.addWidget(self.stylish_viz_widget)

        # Notes section with modern styling
        notes_frame = QFrame()
        notes_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        notes_layout = QVBoxLayout(notes_frame)

        notes_label = QLabel("📝 Today's Notes")
        notes_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 14px; margin-bottom: 8px;")
        notes_layout.addWidget(notes_label)

        self.today_notes_label = QLabel("No notes for today")
        self.today_notes_label.setObjectName("incomeTodayNotes")
        self.today_notes_label.setWordWrap(True)
        self.today_notes_label.setStyleSheet("""
            color: #6c757d;
            font-size: 12px;
            line-height: 1.4;
            padding: 5px;
        """)
        notes_layout.addWidget(self.today_notes_label)

        insights_layout.addWidget(notes_frame)
        insights_layout.addStretch()

        breakdown_layout.addWidget(insights_container, 1)  # 1/3 width

        layout.addLayout(breakdown_layout)

    def create_source_breakdown_list(self, layout):
        """Create modern source breakdown list"""
        # Create scroll area for breakdown
        breakdown_scroll = QScrollArea()
        breakdown_scroll.setWidgetResizable(True)
        breakdown_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        breakdown_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        breakdown_scroll.setFrameShape(QFrame.NoFrame)
        # Remove maximum height constraint to allow natural expansion
        breakdown_scroll.setMinimumHeight(250)  # Set minimum height for better visibility

        breakdown_widget = QWidget()
        breakdown_list_layout = QVBoxLayout(breakdown_widget)
        breakdown_list_layout.setSpacing(8)
        breakdown_list_layout.setContentsMargins(5, 5, 5, 5)

        # Define all income sources with icons and colors
        sources = [
            ("Zomato", "zomato_amount_label", "🍕", "#ff6b6b"),
            ("Swiggy", "swiggy_amount_label", "🛵", "#4ecdc4"),
            ("Shadow Fax", "shadow_fax_amount_label", "📦", "#45b7d1"),
            ("PC Repair", "pc_repair_amount_label", "💻", "#96ceb4"),
            ("YouTube", "youtube_amount_label", "📺", "#ff7675"),
            ("GP Links", "gp_links_amount_label", "🔗", "#a29bfe"),
            ("ID Sales", "id_sales_amount_label", "💳", "#fd79a8"),
            ("Settings", "settings_amount_label", "⚙️", "#fdcb6e"),
            ("Extra Work", "extra_work_amount_label", "💼", "#6c5ce7"),
            ("Other Sources", "other_amount_label", "📊", "#74b9ff")
        ]

        # Create source items
        for source_name, label_attr, icon, color in sources:
            source_item = self.create_source_item(source_name, label_attr, icon, color)
            breakdown_list_layout.addWidget(source_item)

        # Add separator and totals
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #dee2e6; margin: 10px 0;")
        breakdown_list_layout.addWidget(separator)

        # Total earned
        total_item = self.create_total_item("Total Earned", "total_amount_label", "💰", "#28a745", True)
        breakdown_list_layout.addWidget(total_item)

        # Extra amount
        extra_item = self.create_total_item("Extra Amount", "extra_amount_label", "🎉", "#17a2b8", False)
        breakdown_list_layout.addWidget(extra_item)

        breakdown_scroll.setWidget(breakdown_widget)
        layout.addWidget(breakdown_scroll)

    def create_source_item(self, name, label_attr, icon, color):
        """Create a modern source breakdown item"""
        item_frame = QFrame()
        # Store color for theme application
        item_frame.setProperty("accent_color", color)
        item_frame.setObjectName("sourceItemFrame")
        # Theme-aware styling will be applied later

        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(5, 5, 5, 5)

        # Icon and name
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        name_layout.addWidget(icon_label)

        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-weight: 500;
            color: #495057;
            font-size: 13px;
        """)
        name_layout.addWidget(name_label)
        name_layout.addStretch()

        item_layout.addLayout(name_layout)

        # Amount
        amount_label = QLabel("₹0.00")
        amount_label.setObjectName("incomeSourceAmount")
        amount_label.setAlignment(Qt.AlignRight)
        amount_label.setStyleSheet(f"""
            font-weight: bold;
            color: {color};
            font-size: 14px;
            min-width: 80px;
        """)

        # Store reference
        setattr(self, label_attr, amount_label)

        item_layout.addWidget(amount_label)

        return item_frame

    def create_total_item(self, name, label_attr, icon, color, is_bold=False):
        """Create a total/summary item"""
        item_frame = QFrame()
        item_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px 12px;
                margin: 4px 0;
            }}
        """)

        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(5, 5, 5, 5)

        # Icon and name
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        name_layout.addWidget(icon_label)

        name_label = QLabel(name)
        weight = "bold" if is_bold else "600"
        size = "15px" if is_bold else "14px"
        name_label.setStyleSheet(f"""
            font-weight: {weight};
            color: {color};
            font-size: {size};
        """)
        name_layout.addWidget(name_label)
        name_layout.addStretch()

        item_layout.addLayout(name_layout)

        # Amount
        amount_label = QLabel("₹0.00")
        amount_label.setAlignment(Qt.AlignRight)
        weight = "bold" if is_bold else "600"
        size = "16px" if is_bold else "15px"
        amount_label.setStyleSheet(f"""
            font-weight: {weight};
            color: {color};
            font-size: {size};
            min-width: 90px;
        """)

        # Store reference
        setattr(self, label_attr, amount_label)

        item_layout.addWidget(amount_label)

        return item_frame

    def update_overview_metrics(self, total_earned, goal_amount, remaining, streak_days):
        """Update the overview metric cards"""
        try:
            # Update total earned
            if hasattr(self, 'metric_totalEarned_value'):
                self.metric_totalEarned_value.setText(f"₹{total_earned:.2f}")

            # Update goal progress
            if hasattr(self, 'metric_goalProgress_value') and goal_amount > 0:
                progress = min(100, (total_earned / goal_amount) * 100)
                self.metric_goalProgress_value.setText(f"{progress:.1f}%")

            # Update remaining
            if hasattr(self, 'metric_remaining_value'):
                self.metric_remaining_value.setText(f"₹{remaining:.2f}")

            # Update streak
            if hasattr(self, 'metric_streak_value'):
                self.metric_streak_value.setText(f"{streak_days} days")

        except Exception as e:
            print(f"Error updating overview metrics: {e}")

    def calculate_goal_streak(self):
        """Calculate consecutive days of meeting daily goals"""
        try:
            # Simple implementation - you can enhance this based on your data model
            # For now, return a placeholder value
            return 0  # TODO: Implement actual streak calculation
        except Exception as e:
            print(f"Error calculating goal streak: {e}")
            return 0

    def create_weekly_tab(self):
        """Create enhanced weekly view tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Enhanced weekly widget with goal tracking
        self.enhanced_weekly_widget = EnhancedWeeklyViewWidget(self.income_model)
        layout.addWidget(self.enhanced_weekly_widget)

        return tab

    def create_monthly_tab(self):
        """Create monthly view tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.monthly_widget = MonthlyViewWidget(self.income_model)
        layout.addWidget(self.monthly_widget)

        return tab

    def create_yearly_tab(self):
        """Create yearly view tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.yearly_widget = YearlyViewWidget(self.income_model)
        layout.addWidget(self.yearly_widget)

        return tab

    def create_records_tab(self):
        """Create records tab for viewing and editing historical data"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Header with action buttons
        header_layout = QHBoxLayout()

        # Title
        records_title = QLabel("Income Records")
        records_title.setObjectName("incomeRecordsTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        records_title.setFont(font)
        header_layout.addWidget(records_title)

        header_layout.addStretch()

        # Action buttons
        self.add_record_button = QPushButton("Add Record")
        self.add_record_button.setObjectName("incomeAddRecordButton")
        self.add_record_button.setMinimumHeight(35)
        self.add_record_button.clicked.connect(self.add_income_record)
        header_layout.addWidget(self.add_record_button)

        self.edit_record_button = QPushButton("Edit")
        self.edit_record_button.setObjectName("incomeEditRecordButton")
        self.edit_record_button.setMinimumHeight(35)
        self.edit_record_button.setEnabled(False)
        self.edit_record_button.clicked.connect(self.edit_selected_record)
        header_layout.addWidget(self.edit_record_button)

        self.delete_record_button = QPushButton("Delete")
        self.delete_record_button.setObjectName("incomeDeleteRecordButton")
        self.delete_record_button.setMinimumHeight(35)
        self.delete_record_button.setEnabled(False)
        self.delete_record_button.clicked.connect(self.delete_selected_record)
        header_layout.addWidget(self.delete_record_button)

        layout.addLayout(header_layout)

        # Records table
        self.records_table = QTableWidget()
        self.records_table.setObjectName("incomeRecordsTable")
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.records_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setSortingEnabled(True)

        # Set up table columns
        columns = ["ID", "Date", "Zomato", "Swiggy", "Shadow Fax", "Other", "Total", "Goal", "Progress", "Status", "Notes"]
        self.records_table.setColumnCount(len(columns))
        self.records_table.setHorizontalHeaderLabels(columns)

        # Hide ID column
        self.records_table.setColumnHidden(0, True)

        # Set column widths
        header = self.records_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(1, 100)  # Date
        header.resizeSection(2, 80)   # Zomato
        header.resizeSection(3, 80)   # Swiggy
        header.resizeSection(4, 80)   # Shadow Fax
        header.resizeSection(5, 80)   # Other
        header.resizeSection(6, 100)  # Total
        header.resizeSection(7, 80)   # Goal
        header.resizeSection(8, 80)   # Progress
        header.resizeSection(9, 100)  # Status

        # Connect selection change
        self.records_table.selectionModel().selectionChanged.connect(self.on_record_selection_changed)
        self.records_table.doubleClicked.connect(self.edit_selected_record)

        layout.addWidget(self.records_table)

        return tab

    def create_stats_tab(self):
        """Create statistics tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Statistics widget
        self.stats_widget = IncomeStatsWidget()
        layout.addWidget(self.stats_widget)

        # Additional charts/graphs could go here
        layout.addStretch()

        return tab

    def setup_connections(self):
        """Setup signal connections"""
        # No button connections needed since quick action buttons were removed
        pass

        # Weekly navigation - use enhanced weekly widget if available
        if hasattr(self, 'enhanced_weekly_widget'):
            self.enhanced_weekly_widget.prev_week_btn.clicked.connect(self.prev_week)
            self.enhanced_weekly_widget.next_week_btn.clicked.connect(self.next_week)
        elif hasattr(self, 'weekly_widget'):
            self.weekly_widget.prev_week_btn.clicked.connect(self.prev_week)
            self.weekly_widget.next_week_btn.clicked.connect(self.next_week)

        # Data model connections
        self.data_manager.data_changed.connect(self.on_data_changed)

        # Base income settings connections - will be set up after tabs are created
        # This is handled in setup_base_income_connections method

    def setup_base_income_connections(self):
        """Setup base income signal connections after all tabs are created"""
        try:
            if hasattr(self, 'base_income_tab') and self.base_income_tab:
                print("Setting up base income signal connection")
                self.base_income_tab.base_income_updated.connect(self.on_base_income_updated)
                print("Base income signal connection established successfully")
            else:
                print("Warning: base_income_tab not found or not created yet")
        except Exception as e:
            print(f"Error setting up base income connections: {e}")

    def refresh_data(self):
        """Refresh all data with error handling and performance optimization"""
        try:
            print("Starting optimized income data refresh...")

            # Load critical data first (today's data for immediate UI feedback)
            print("Loading today data...")
            self.load_today_data()

            # Refresh enhanced daily goal widget early
            if hasattr(self, 'daily_goal_widget'):
                print("Refreshing daily goal widget...")
                self.daily_goal_widget.refresh_data()

            # Load other data in order of user importance
            print("Loading weekly data...")
            self.load_weekly_data()

            print("Loading monthly data...")
            self.load_monthly_data()

            print("Loading yearly data...")
            self.load_yearly_data()

            print("Loading records data...")
            self.load_records_data()

            print("Updating statistics...")
            self.update_statistics()

            # Analytics dashboard moved to main Dashboard tab - no longer refreshed here

            # Source analysis and smart goal widgets removed - not needed with manual base income settings
            print("Optimized income data refresh completed successfully")

        except Exception as e:
            import traceback
            print(f"Error refreshing income data: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            # Show user-friendly message
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Data Refresh Error",
                              "There was an issue refreshing the income data. Please try again.")
            # Set safe default values
            if hasattr(self, 'stylish_viz_widget'):
                self.stylish_viz_widget.update_visualization(0.0, 1000.0, {})
            if hasattr(self, 'daily_goal_widget'):
                try:
                    self.daily_goal_widget.refresh_data()
                except Exception as widget_error:
                    print(f"Error refreshing daily goal widget: {widget_error}")

    def refresh_data_async(self):
        """Asynchronous data refresh to prevent UI blocking"""
        from PySide6.QtCore import QTimer

        # Use QTimer to break up the refresh into smaller chunks
        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_steps = [
            self.load_today_data,
            lambda: self.daily_goal_widget.refresh_data() if hasattr(self, 'daily_goal_widget') else None,
            self.load_weekly_data,
            self.load_monthly_data,
            self.load_yearly_data,
            self.load_records_data,
            self.update_statistics
        ]
        self.current_refresh_step = 0

        def execute_next_step():
            if self.current_refresh_step < len(self.refresh_steps):
                try:
                    step = self.refresh_steps[self.current_refresh_step]
                    if step:
                        step()
                    self.current_refresh_step += 1
                    # Schedule next step with small delay to keep UI responsive
                    self.refresh_timer.timeout.connect(execute_next_step)
                    self.refresh_timer.start(10)  # 10ms delay between steps
                except Exception as e:
                    print(f"Error in refresh step {self.current_refresh_step}: {e}")
                    self.current_refresh_step += 1
                    if self.current_refresh_step < len(self.refresh_steps):
                        self.refresh_timer.start(10)
            else:
                print("Asynchronous income data refresh completed")

        execute_next_step()

    def load_today_data(self):
        """Load today's income data"""
        today_record = self.income_model.get_or_create_today_record()

        # Get daily target based on day of week
        daily_target = self.income_model.get_daily_target_for_date(date.today())

        # Update stylish visualization widget
        sources_dict = {
            'Zomato': getattr(today_record, 'zomato', 0.0),
            'Swiggy': getattr(today_record, 'swiggy', 0.0),
            'Shadow Fax': getattr(today_record, 'shadow_fax', 0.0),
            'PC Repair': getattr(today_record, 'pc_repair', 0.0),
            'Settings': getattr(today_record, 'settings', 0.0),
            'YouTube': getattr(today_record, 'youtube', 0.0),
            'GP Links': getattr(today_record, 'gp_links', 0.0),
            'ID Sales': getattr(today_record, 'id_sales', 0.0),
            'Other': getattr(today_record, 'other_sources', 0.0),
            'Extra Work': getattr(today_record, 'extra_work', 0.0)
        }

        self.stylish_viz_widget.update_visualization(
            current=today_record.earned,
            target=daily_target,
            sources=sources_dict
        )

        # Update breakdown
        self.zomato_amount_label.setText(f"₹{today_record.zomato:.2f}")
        self.swiggy_amount_label.setText(f"₹{today_record.swiggy:.2f}")
        self.shadow_fax_amount_label.setText(f"₹{today_record.shadow_fax:.2f}")
        self.pc_repair_amount_label.setText(f"₹{getattr(today_record, 'pc_repair', 0.0):.2f}")
        self.settings_amount_label.setText(f"₹{getattr(today_record, 'settings', 0.0):.2f}")
        self.youtube_amount_label.setText(f"₹{getattr(today_record, 'youtube', 0.0):.2f}")
        self.gp_links_amount_label.setText(f"₹{getattr(today_record, 'gp_links', 0.0):.2f}")
        self.id_sales_amount_label.setText(f"₹{getattr(today_record, 'id_sales', 0.0):.2f}")
        self.other_amount_label.setText(f"₹{today_record.other_sources:.2f}")
        self.extra_work_amount_label.setText(f"₹{getattr(today_record, 'extra_work', 0.0):.2f}")
        self.total_amount_label.setText(f"₹{today_record.earned:.2f}")
        self.extra_amount_label.setText(f"₹{today_record.extra:.2f}")

        # Update notes - ensure notes is always a string
        if today_record.notes and str(today_record.notes).strip():
            self.today_notes_label.setText(str(today_record.notes))
        else:
            self.today_notes_label.setText("No notes for today")

        # Update overview metrics
        remaining = max(0, daily_target - today_record.earned)
        streak_days = self.calculate_goal_streak()  # You may need to implement this method
        self.update_overview_metrics(
            total_earned=today_record.earned,
            goal_amount=daily_target,
            remaining=remaining,
            streak_days=streak_days
        )

    def load_weekly_data(self):
        """Load weekly data"""
        if self.current_week_start is None:
            # Start from Monday of current week
            today = date.today()
            self.current_week_start = today - timedelta(days=today.weekday())

        # Update enhanced weekly widget
        if hasattr(self, 'enhanced_weekly_widget'):
            self.enhanced_weekly_widget.current_week_start = self.current_week_start
            self.enhanced_weekly_widget.refresh_data()

        # Keep old weekly widget for compatibility
        if hasattr(self, 'weekly_widget'):
            weekly_data = self.income_model.get_weekly_summary(self.current_week_start)
            self.weekly_widget.update_weekly_data(weekly_data)

    def load_monthly_data(self):
        """Load monthly data"""
        try:
            if hasattr(self, 'monthly_widget'):
                self.monthly_widget.refresh_data()
        except Exception as e:
            print(f"Error loading monthly data: {e}")

    def load_yearly_data(self):
        """Load yearly data"""
        try:
            if hasattr(self, 'yearly_widget'):
                self.yearly_widget.refresh_data()
        except Exception as e:
            print(f"Error loading yearly data: {e}")

    def on_tab_changed(self, index):
        """Handle tab change to refresh data when needed"""
        try:
            tab_text = self.tab_widget.tabText(index)

            if tab_text == "Yearly View" and hasattr(self, 'yearly_widget'):
                # Refresh yearly view when it's activated
                self.yearly_widget.refresh_data()
            elif tab_text == "Monthly View" and hasattr(self, 'monthly_widget'):
                # Refresh monthly view when it's activated
                self.monthly_widget.refresh_data()
            elif tab_text == "Weekly View" and hasattr(self, 'enhanced_weekly_widget'):
                # Refresh weekly view when it's activated
                self.enhanced_weekly_widget.refresh_data()
            elif tab_text == "All Records" and hasattr(self, 'records_table'):
                # Refresh records table when it's activated
                self.load_records_data()

        except Exception as e:
            print(f"Error handling tab change: {e}")

    def update_statistics(self):
        """Update statistics display"""
        stats = self.income_model.get_income_summary()
        self.stats_widget.update_stats(stats)



    def quick_add_source(self, source: str):
        """Quick add amount to specific source"""
        from PySide6.QtWidgets import QInputDialog

        source_names = {
            "zomato": "Zomato",
            "swiggy": "Swiggy",
            "shadow_fax": "Shadow Fax",
            "pc_repair": "PC Repair",
            "settings": "Settings",
            "youtube": "YouTube",
            "gp_links": "GP Links",
            "id_sales": "ID Sales",
            "other": "Other Sources",
            "extra_work": "Extra Work"
        }

        amount, ok = QInputDialog.getDouble(
            self, f"Add {source_names[source]} Earnings",
            f"Enter amount earned from {source_names[source]}:",
            0.0, 0.0, 99999.99, 2
        )

        if ok and amount > 0:
            # Get or create today's record
            today_record = self.income_model.get_or_create_today_record()

            # Add to the specific source
            if source == "zomato":
                today_record.zomato += amount
            elif source == "swiggy":
                today_record.swiggy += amount
            elif source == "shadow_fax":
                today_record.shadow_fax += amount
            elif source == "pc_repair":
                today_record.pc_repair += amount
            elif source == "settings":
                today_record.settings += amount
            elif source == "youtube":
                today_record.youtube += amount
            elif source == "gp_links":
                today_record.gp_links += amount
            elif source == "id_sales":
                today_record.id_sales += amount
            elif source == "other":
                today_record.other_sources += amount
            elif source == "extra_work":
                today_record.extra_work += amount

            # Recalculate totals
            today_record.calculate_totals()

            # Save the record
            existing_record = self.income_model.get_income_record_by_date(date.today())
            if existing_record:
                self.income_model.update_income_record(existing_record.id, today_record)
            else:
                self.income_model.add_income_record(today_record)

            self.refresh_data()



    def prev_week(self):
        """Navigate to previous week"""
        if self.current_week_start:
            self.current_week_start -= timedelta(days=7)
            self.load_weekly_data()

        # Also update enhanced weekly widget
        if hasattr(self, 'enhanced_weekly_widget'):
            self.enhanced_weekly_widget.prev_week()

    def next_week(self):
        """Navigate to next week"""
        if self.current_week_start:
            self.current_week_start += timedelta(days=7)
            self.load_weekly_data()

        # Also update enhanced weekly widget
        if hasattr(self, 'enhanced_weekly_widget'):
            self.enhanced_weekly_widget.next_week()

    def on_income_saved(self, income_data: dict):
        """Handle income saved"""
        self.refresh_data()

    def on_data_changed(self, module: str, operation: str):
        """Handle data changes"""
        if module == "income":
            self.refresh_data()

    def on_base_income_updated(self):
        """Handle base income settings updates - optimized to avoid redundant refreshes"""
        print("Base income settings updated - performing optimized refresh")

        # Perform a single, comprehensive refresh instead of multiple individual refreshes
        # This avoids the cascade of redundant refresh calls
        self.refresh_base_income_dependent_widgets()

    def refresh_base_income_dependent_widgets(self):
        """Optimized refresh for base income dependent widgets only"""
        try:
            print("Performing optimized base income refresh...")

            # Only refresh widgets that directly depend on base income settings
            # Source analysis and smart goals are NOT dependent on base income structure

            # 1. Refresh Enhanced Daily Goal Widget (Today tab) - DEPENDS on base income
            if hasattr(self, 'daily_goal_widget'):
                print("Refreshing Daily Goal Widget (base income dependent)")
                self.daily_goal_widget.refresh_data()

            # 2. Refresh Enhanced Weekly View Widget - DEPENDS on base income
            if hasattr(self, 'enhanced_weekly_widget'):
                print("Refreshing Weekly View Widget (base income dependent)")
                self.enhanced_weekly_widget.refresh_data()

            # 3. Refresh Monthly and Yearly widgets - DEPEND on base income calculations
            if hasattr(self, 'monthly_widget'):
                print("Refreshing Monthly Widget (base income dependent)")
                self.monthly_widget.refresh_data()

            if hasattr(self, 'yearly_widget'):
                print("Refreshing Yearly Widget (base income dependent)")
                self.yearly_widget.refresh_data()

            # 4. Update statistics display (lightweight operation)
            self.update_statistics()

            # NOTE: Source Analysis and Smart Goals are NOT refreshed here because:
            # - Source Analysis: Analyzes income sources, not base targets
            # - Smart Goals: Provides recommendations based on historical data, not base structure

            print("Optimized base income refresh completed")

        except Exception as e:
            print(f"Error in optimized base income refresh: {e}")

    def add_income_record(self):
        """Add new income record"""
        dialog = IncomeEntryDialog(self.income_model, parent=self)
        dialog.income_saved.connect(self.on_income_saved)
        dialog.exec()

    def edit_selected_record(self):
        """Edit the selected income record"""
        current_row = self.records_table.currentRow()
        if current_row >= 0:
            # Get the record ID from the hidden column
            record_id = int(self.records_table.item(current_row, 0).text())
            self.edit_income_record_by_id(record_id)

    def edit_income_record_by_id(self, record_id: int):
        """Edit income record by ID"""
        record = self.income_model.get_income_record_by_id(record_id)
        if record:
            dialog = IncomeEntryDialog(self.income_model, record, parent=self)
            dialog.income_saved.connect(self.on_income_saved)
            dialog.exec()

    def edit_income_for_date(self, date):
        """Edit income for a specific date (called from weekly view)"""
        record = self.income_model.get_income_record_by_date(date)
        if record:
            dialog = IncomeEntryDialog(self.income_model, record, parent=self)
            dialog.income_saved.connect(self.on_income_saved)
            dialog.exec()
        else:
            # Create new record for this date
            new_record = IncomeRecord(date=date)
            dialog = IncomeEntryDialog(self.income_model, new_record, parent=self)
            dialog.income_saved.connect(self.on_income_saved)
            dialog.exec()

    def delete_selected_record(self):
        """Delete the selected income record"""
        current_row = self.records_table.currentRow()
        if current_row >= 0:
            record_id = int(self.records_table.item(current_row, 0).text())
            date_item = self.records_table.item(current_row, 1)
            date_text = date_item.text() if date_item else "Unknown"

            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete the income record for {date_text}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if self.income_model.delete_income_record(record_id):
                    QMessageBox.information(self, "Success", "Record deleted successfully!")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete record!")

    def on_record_selection_changed(self):
        """Handle record selection change"""
        has_selection = self.records_table.currentRow() >= 0
        self.edit_record_button.setEnabled(has_selection)
        self.delete_record_button.setEnabled(has_selection)

    def load_records_data(self):
        """Load all income records into the table"""
        try:
            df = self.income_model.get_all_income_records()

            if df.empty:
                self.records_table.setRowCount(0)
                return

            # Sort by date descending (most recent first)
            df = df.sort_values('date', ascending=False)

            self.records_table.setRowCount(len(df))

            for row, (_, record) in enumerate(df.iterrows()):
                # ID (hidden)
                self.records_table.setItem(row, 0, QTableWidgetItem(str(record['id'])))

                # Date
                date_str = str(record['date'])
                if isinstance(record['date'], str):
                    try:
                        date_obj = datetime.strptime(record['date'], '%Y-%m-%d').date()
                        date_str = date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                self.records_table.setItem(row, 1, QTableWidgetItem(date_str))

                # Income sources
                self.records_table.setItem(row, 2, QTableWidgetItem(f"₹{record['zomato']:.2f}"))
                self.records_table.setItem(row, 3, QTableWidgetItem(f"₹{record['swiggy']:.2f}"))
                self.records_table.setItem(row, 4, QTableWidgetItem(f"₹{record['shadow_fax']:.2f}"))
                self.records_table.setItem(row, 5, QTableWidgetItem(f"₹{record['other_sources']:.2f}"))

                # Total earned
                self.records_table.setItem(row, 6, QTableWidgetItem(f"₹{record['earned']:.2f}"))

                # Goal
                self.records_table.setItem(row, 7, QTableWidgetItem(f"₹{record['goal_inc']:.2f}"))

                # Progress
                self.records_table.setItem(row, 8, QTableWidgetItem(f"{record['progress']:.1f}%"))

                # Status
                status_item = QTableWidgetItem(str(record['status']))
                # Color code status
                if record['status'] == "Exceeded":
                    status_item.setBackground(QColor("#e8f5e8"))
                elif record['status'] == "Completed":
                    status_item.setBackground(QColor("#e3f2fd"))
                elif record['status'] == "In Progress":
                    status_item.setBackground(QColor("#fff3e0"))
                self.records_table.setItem(row, 9, status_item)

                # Notes
                notes = str(record['notes']) if record['notes'] else ""
                self.records_table.setItem(row, 10, QTableWidgetItem(notes))

        except Exception as e:
            print(f"Error loading records data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load records: {str(e)}")
