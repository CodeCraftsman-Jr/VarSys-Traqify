"""
Semester Management UI Widgets
Provides UI for managing B.Tech semester system
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QDateEdit, QSpinBox, QCheckBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox,
    QTextEdit, QTabWidget, QProgressBar, QFrame, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from .semester_models import SemesterManager, SemesterInfo


class SemesterEditDialog(QDialog):
    """Dialog for editing semester information"""
    
    semester_updated = Signal()
    
    def __init__(self, semester_manager: SemesterManager, semester: SemesterInfo = None, parent=None):
        super().__init__(parent)
        
        self.semester_manager = semester_manager
        self.semester = semester
        self.is_edit_mode = semester is not None
        
        self.setup_ui()
        self.setup_connections()
        
        if self.is_edit_mode:
            self.load_semester_data()
        
        self.setModal(True)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Semester" if self.is_edit_mode else "Add Semester")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Semester number
        self.semester_spinbox = QSpinBox()
        self.semester_spinbox.setRange(1, 8)
        self.semester_spinbox.setValue(1)
        form_layout.addRow("Semester Number:", self.semester_spinbox)
        
        # Academic year
        self.academic_year_edit = QLineEdit()
        self.academic_year_edit.setPlaceholderText("e.g., 2024-2025")
        current_year = datetime.now().year
        self.academic_year_edit.setText(f"{current_year}-{current_year + 1}")
        form_layout.addRow("Academic Year:", self.academic_year_edit)
        
        # Start date
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date_edit)
        
        # End date
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addMonths(6))
        self.end_date_edit.setCalendarPopup(True)
        form_layout.addRow("End Date:", self.end_date_edit)
        
        # Active checkbox
        self.active_checkbox = QCheckBox("Set as Active Semester")
        form_layout.addRow("Status:", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Info section
        info_group = QGroupBox("Semester Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        layout.addWidget(button_box)
        
        # Store references
        self.button_box = button_box
        
        # Update info when values change
        self.semester_spinbox.valueChanged.connect(self.update_info)
        self.start_date_edit.dateChanged.connect(self.update_info)
        self.end_date_edit.dateChanged.connect(self.update_info)
        
        self.update_info()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.button_box.accepted.connect(self.save_semester)
        self.button_box.rejected.connect(self.reject)
    
    def update_info(self):
        """Update semester information display"""
        semester_num = self.semester_spinbox.value()
        year = ((semester_num - 1) // 2) + 1
        semester_type = "Odd" if semester_num % 2 == 1 else "Even"
        
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        # Calculate duration
        duration = (end_date - start_date).days
        
        year_names = {1: "First", 2: "Second", 3: "Third", 4: "Fourth"}
        year_name = year_names.get(year, f"Year {year}")
        
        info_text = f"""
        <b>Semester Details:</b><br>
        • <b>Name:</b> {year_name} Year - {semester_type} Semester<br>
        • <b>Duration:</b> {duration} days<br>
        • <b>Year:</b> {year}/4<br>
        • <b>Type:</b> {semester_type} Semester
        """
        
        self.info_label.setText(info_text)
    
    def load_semester_data(self):
        """Load semester data into the form"""
        if not self.semester:
            return
        
        self.semester_spinbox.setValue(self.semester.semester_number)
        self.academic_year_edit.setText(self.semester.academic_year)
        
        # Set dates
        try:
            start_date = datetime.strptime(self.semester.start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(self.semester.end_date, '%Y-%m-%d').date()
            
            self.start_date_edit.setDate(QDate(start_date))
            self.end_date_edit.setDate(QDate(end_date))
        except ValueError:
            pass
        
        self.active_checkbox.setChecked(self.semester.is_active)
    
    def save_semester(self):
        """Save the semester"""
        semester_num = self.semester_spinbox.value()
        academic_year = self.academic_year_edit.text().strip()
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        is_active = self.active_checkbox.isChecked()
        
        # Validation
        if not academic_year:
            QMessageBox.warning(self, "Error", "Academic year is required")
            return
        
        if start_date >= end_date:
            QMessageBox.warning(self, "Error", "End date must be after start date")
            return
        
        # Create or update semester
        if self.is_edit_mode:
            semester_info = self.semester
            semester_info.academic_year = academic_year
            semester_info.start_date = start_date.strftime('%Y-%m-%d')
            semester_info.end_date = end_date.strftime('%Y-%m-%d')
            semester_info.is_active = is_active
        else:
            semester_info = SemesterInfo(
                semester_number=semester_num,
                academic_year=academic_year,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                is_active=is_active
            )
        
        # Save to manager
        if self.semester_manager.update_semester(semester_info):
            # If this semester is set as active, deactivate others
            if is_active:
                self.semester_manager.set_active_semester(semester_num)
            
            QMessageBox.information(self, "Success", "Semester saved successfully!")
            self.semester_updated.emit()
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save semester!")


class SemesterManagementWidget(QWidget):
    """Widget for managing B.Tech semesters"""
    
    semester_changed = Signal()
    
    def __init__(self, data_manager, config=None, parent=None):
        super().__init__(parent)

        self.data_manager = data_manager
        self.config = config
        self.semester_manager = SemesterManager(str(data_manager.data_dir), config)
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.load_semesters()
    
    def setup_ui(self):
        """Setup the semester management UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("B.Tech Semester Management")
        title.setObjectName("pageTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        title.setFont(font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action buttons
        self.add_semester_button = QPushButton("Add Semester")
        self.add_semester_button.clicked.connect(self.add_semester)
        header_layout.addWidget(self.add_semester_button)
        
        self.edit_semester_button = QPushButton("Edit")
        self.edit_semester_button.setEnabled(False)
        self.edit_semester_button.clicked.connect(self.edit_semester)
        header_layout.addWidget(self.edit_semester_button)
        
        self.set_active_button = QPushButton("Set Active")
        self.set_active_button.setEnabled(False)
        self.set_active_button.clicked.connect(self.set_active_semester)
        header_layout.addWidget(self.set_active_button)
        
        layout.addLayout(header_layout)
        
        # Semesters table
        self.semesters_table = QTableWidget()
        self.semesters_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.semesters_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.semesters_table.setAlternatingRowColors(True)
        
        # Set up columns
        columns = ["Semester", "Name", "Academic Year", "Start Date", "End Date", "Working Days", "Status", "Attendance %"]
        self.semesters_table.setColumnCount(len(columns))
        self.semesters_table.setHorizontalHeaderLabels(columns)
        
        # Set column widths
        header = self.semesters_table.horizontalHeader()
        header.resizeSection(0, 80)   # Semester
        header.resizeSection(1, 200)  # Name
        header.resizeSection(2, 120)  # Academic Year
        header.resizeSection(3, 100)  # Start Date
        header.resizeSection(4, 100)  # End Date
        header.resizeSection(5, 100)  # Working Days
        header.resizeSection(6, 80)   # Status
        header.setStretchLastSection(True)  # Attendance %
        
        # Connect selection change
        self.semesters_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.semesters_table.doubleClicked.connect(self.edit_semester)
        
        layout.addWidget(self.semesters_table)
        
        # Current semester info
        current_group = QGroupBox("Current Active Semester")
        current_layout = QVBoxLayout(current_group)
        
        self.current_semester_label = QLabel("No active semester")
        self.current_semester_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        current_layout.addWidget(self.current_semester_label)
        
        layout.addWidget(current_group)
    
    def load_semesters(self):
        """Load semesters into the table"""
        try:
            semesters = self.semester_manager.get_all_semesters()
            
            self.semesters_table.setRowCount(len(semesters))
            
            active_semester = None
            
            for row, semester in enumerate(semesters):
                # Semester number
                self.semesters_table.setItem(row, 0, QTableWidgetItem(str(semester.semester_number)))
                
                # Name
                self.semesters_table.setItem(row, 1, QTableWidgetItem(semester.get_semester_name()))
                
                # Academic year
                self.semesters_table.setItem(row, 2, QTableWidgetItem(semester.academic_year))
                
                # Start date
                self.semesters_table.setItem(row, 3, QTableWidgetItem(semester.start_date))
                
                # End date
                self.semesters_table.setItem(row, 4, QTableWidgetItem(semester.end_date))
                
                # Working days
                working_days = semester.get_working_days()
                self.semesters_table.setItem(row, 5, QTableWidgetItem(str(working_days)))
                
                # Status
                status_item = QTableWidgetItem("Active" if semester.is_active else "Inactive")
                if semester.is_active:
                    status_item.setBackground(QColor("#2d5a2d"))  # Dark green for dark theme
                    status_item.setForeground(QColor("#ffffff"))
                    active_semester = semester
                self.semesters_table.setItem(row, 6, status_item)
                
                # Attendance percentage - only show for completed semesters and active semester
                if semester.semester_number <= 7 or semester.is_active:
                    summary = self.semester_manager.get_semester_summary(semester.semester_number)
                    attendance_pct = summary.get('attendance_percentage', 0.0)
                    pct_item = QTableWidgetItem(f"{attendance_pct:.1f}%")

                    # Color code attendance with dark theme colors
                    if attendance_pct >= 75:
                        pct_item.setBackground(QColor("#2d5a2d"))  # Dark green
                        pct_item.setForeground(QColor("#ffffff"))
                    elif attendance_pct >= 50:
                        pct_item.setBackground(QColor("#5a4a2d"))  # Dark orange
                        pct_item.setForeground(QColor("#ffffff"))
                    else:
                        pct_item.setBackground(QColor("#5a2d2d"))  # Dark red
                        pct_item.setForeground(QColor("#ffffff"))
                else:
                    # For semester 8 when not active, show "Not Started"
                    pct_item = QTableWidgetItem("Not Started")
                    pct_item.setBackground(QColor("#404040"))  # Gray
                    pct_item.setForeground(QColor("#cccccc"))

                self.semesters_table.setItem(row, 7, pct_item)
            
            # Update current semester display
            if active_semester:
                self.current_semester_label.setText(
                    f"{active_semester.get_semester_name()} ({active_semester.academic_year})"
                )
            else:
                self.current_semester_label.setText("No active semester")
                
        except Exception as e:
            self.logger.error(f"Error loading semesters: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load semesters: {str(e)}")
    
    def on_selection_changed(self):
        """Handle selection change"""
        has_selection = self.semesters_table.currentRow() >= 0
        self.edit_semester_button.setEnabled(has_selection)
        self.set_active_button.setEnabled(has_selection)
    
    def add_semester(self):
        """Add new semester"""
        dialog = SemesterEditDialog(self.semester_manager, parent=self)
        dialog.semester_updated.connect(self.on_semester_updated)
        dialog.exec()
    
    def edit_semester(self):
        """Edit selected semester"""
        current_row = self.semesters_table.currentRow()
        if current_row >= 0:
            semester_num_item = self.semesters_table.item(current_row, 0)
            if semester_num_item:
                semester_num = int(semester_num_item.text())
                semester = self.semester_manager.get_semester_by_number(semester_num)
                
                if semester:
                    dialog = SemesterEditDialog(self.semester_manager, semester, parent=self)
                    dialog.semester_updated.connect(self.on_semester_updated)
                    dialog.exec()
    
    def set_active_semester(self):
        """Set selected semester as active"""
        current_row = self.semesters_table.currentRow()
        if current_row >= 0:
            semester_num_item = self.semesters_table.item(current_row, 0)
            if semester_num_item:
                semester_num = int(semester_num_item.text())
                
                if self.semester_manager.set_active_semester(semester_num):
                    QMessageBox.information(self, "Success", f"Semester {semester_num} is now active!")
                    self.load_semesters()
                    self.semester_changed.emit()
                else:
                    QMessageBox.warning(self, "Error", "Failed to set active semester!")
    
    def on_semester_updated(self):
        """Handle semester update"""
        self.load_semesters()
        self.semester_changed.emit()
