#!/usr/bin/env python3
"""
Simplified Attendance Widget - No Pandas Dependencies
"""

import logging
from datetime import datetime, date
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCalendarWidget, QGroupBox,
    QCheckBox, QTextEdit, QMessageBox, QFrame,
    QScrollArea, QButtonGroup, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QComboBox, QDateEdit, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QPainter, QBrush

from .simple_models import SimpleAttendanceDataManager, SimpleAttendanceRecord
from src.ui.themes.utils import create_calendar_text_format, get_calendar_color_for_state, get_current_theme, get_calendar_color_with_alpha


class CustomAttendanceCalendar(QCalendarWidget):
    """Custom calendar widget with attendance highlighting using paintCell"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.attendance_data = {}  # date_string -> record
        self.current_theme = 'dark'

    def set_attendance_data(self, records, theme='dark'):
        """Set attendance data for calendar highlighting"""
        self.attendance_data = {}
        self.current_theme = theme

        # Convert records to a dictionary for quick lookup
        for record in records:
            self.attendance_data[record.date] = record

        # Force repaint
        self.updateCells()

    def paintCell(self, painter, rect, date):
        """Custom paint method to highlight cells based on attendance"""
        # Call parent paint first
        super().paintCell(painter, rect, date)

        # Get date string in YYYY-MM-DD format
        date_str = date.toString('yyyy-MM-dd')
        record = self.attendance_data.get(date_str)

        if record:
            # Determine color based on attendance status
            color = None

            # First check if it's a holiday (highest priority)
            if record.is_holiday or (record.notes and "holiday" in record.notes.lower()):
                color = get_calendar_color_with_alpha('warning', 180, self.current_theme)

            # Check for full attendance (all periods present)
            elif record.present_periods >= record.total_periods and record.total_periods > 0:
                color = get_calendar_color_with_alpha('success', 180, self.current_theme)

            # Check for complete absence (0 periods present) - but only if it's not a holiday
            elif record.present_periods == 0 and not record.is_holiday:
                color = get_calendar_color_with_alpha('error', 180, self.current_theme)

            # Partial attendance (some periods present, some absent)
            elif 0 < record.present_periods < record.total_periods:
                color = get_calendar_color_with_alpha('warning', 180, self.current_theme)

            if color:
                # Draw colored overlay with proper margins to avoid overlap
                margin = 2
                adjusted_rect = rect.adjusted(margin, margin, -margin, -margin)
                painter.fillRect(adjusted_rect, color)

                # Only show percentage for partial attendance (not 0% or 100%)
                if record.total_periods > 0:
                    percentage = (record.present_periods / record.total_periods) * 100
                    # Only show percentage text for partial attendance (between 1% and 99%)
                    if 0 < percentage < 100:
                        painter.setPen(QColor(255, 255, 255))  # White text for better visibility on colored backgrounds
                        # Set smaller font for the percentage
                        font = painter.font()
                        font.setPointSize(8)
                        painter.setFont(font)
                        # Position text in bottom part of cell to avoid overlapping with date number
                        text_rect = adjusted_rect.adjusted(0, adjusted_rect.height() // 2, 0, 0)
                        painter.drawText(text_rect, Qt.AlignCenter, f"{percentage:.0f}%")


class SimpleAttendanceTrackerWidget(QWidget):
    """Simplified attendance tracker widget"""
    
    # Signals
    data_changed = Signal()
    
    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        self.data_manager = data_manager  # Store the data_manager reference
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize simple data manager
        self.attendance_manager = SimpleAttendanceDataManager(str(data_manager.data_dir))

        # Current state
        self.current_date = date.today()
        self.current_record = None

        # Theme management
        self.current_theme = get_current_theme()

        # Timer for delayed auto-save to avoid conflicts with UI updates
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.auto_save_attendance)

        # Flag to prevent auto-save during UI initialization/clearing
        self.ui_updating = False

        self.setup_ui()
        self.load_current_date()
        self.highlight_calendar_dates()

        self.logger.info("✅ SimpleAttendanceTrackerWidget initialized successfully")

    def get_theme_colors(self, theme_name: str = None) -> dict:
        """Get theme-specific colors for attendance status"""
        if theme_name is None:
            theme_name = self.current_theme

        if theme_name == 'dark':
            return {
                'present_bg': '#2d5a2d',      # Dark green for present
                'present_text': '#90ee90',    # Light green text
                'holiday_bg': '#5a5a2d',      # Dark yellow for holiday
                'holiday_text': '#ffff90',    # Light yellow text
                'absent_bg': '#5a2d2d',       # Dark red for absent
                'absent_text': '#ffb3b3',     # Light red text
                'partial_bg': '#5a4a2d',      # Dark orange for partial
                'partial_text': '#ffcc90',    # Light orange text
                'neutral_bg': '#404040',      # Dark gray for neutral
                'neutral_text': '#cccccc'     # Light gray text
            }
        else:  # light theme
            return {
                'present_bg': '#e8f5e8',      # Light green for present
                'present_text': '#0d5a0d',    # Dark green text
                'holiday_bg': '#fff3e0',      # Light orange for holiday
                'holiday_text': '#cc7a00',    # Dark orange text
                'absent_bg': '#ffebee',       # Light red for absent
                'absent_text': '#c62d31',     # Dark red text
                'partial_bg': '#fff8e1',      # Light yellow for partial
                'partial_text': '#f57c00',    # Dark orange text
                'neutral_bg': '#f5f5f5',      # Light gray for neutral
                'neutral_text': '#666666'     # Dark gray text
            }

    def apply_theme(self, theme_name: str = 'dark'):
        """Apply theme to attendance widgets"""
        try:
            print(f"🎨 DEBUG: SimpleAttendanceTrackerWidget.apply_theme called with theme: {theme_name}")
            self.current_theme = theme_name

            # Refresh the records table with new theme colors
            if hasattr(self, 'records_table'):
                self.refresh_records_table()

            # Refresh calendar highlighting
            self.highlight_calendar_dates()

            print(f"✅ SUCCESS: Applied theme '{theme_name}' to Attendance Tracker widgets")

        except Exception as e:
            print(f"❌ ERROR: Failed to apply theme to Attendance Tracker: {e}")

    def update_theme(self, theme_name: str = 'dark'):
        """Update theme - compatibility method for main window theme propagation"""
        self.apply_theme(theme_name)

    def refresh_records_table(self):
        """Refresh the records table with current theme colors"""
        try:
            # Get all records and apply current filters
            all_records = self.attendance_manager.get_all_records()
            if not all_records:
                return

            # Apply current filters
            filtered_records = self.filter_records(all_records)

            # Repopulate table with theme-aware colors
            self.populate_records_table(filtered_records)

        except Exception as e:
            self.logger.error(f"Error refreshing records table: {e}")

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 20px to 10px
        layout.setSpacing(10)  # Reduced from 20px to 10px
        
        # Title
        title = QLabel("Attendance Tracker")
        title.setObjectName("pageTitle")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()

        # Today's attendance tab
        today_tab = QWidget()
        today_layout = QVBoxLayout(today_tab)

        # Main content in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Date selection section
        self.setup_date_section(content_layout)

        # Attendance marking section
        self.setup_attendance_section(content_layout)

        # Summary section
        self.setup_summary_section(content_layout)

        # Action buttons
        self.setup_action_buttons(content_layout)

        scroll_area.setWidget(content_widget)
        today_layout.addWidget(scroll_area)

        # All records tab
        records_tab = QWidget()
        self.setup_records_tab(records_tab)

        # Semester management tab
        semester_tab = QWidget()
        self.setup_semester_tab(semester_tab)

        # Add tabs
        self.tab_widget.addTab(today_tab, "Mark Attendance")
        self.tab_widget.addTab(records_tab, "All Records")
        self.tab_widget.addTab(semester_tab, "Semester Management")

        # Connect tab change event to refresh data when switching to All Records tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)
    
    def setup_date_section(self, layout):
        """Setup date selection section"""
        date_group = QGroupBox("Select Date")
        date_layout = QHBoxLayout(date_group)
        
        # Calendar widget - use custom calendar for better highlighting
        self.calendar = CustomAttendanceCalendar()
        self.calendar.setSelectedDate(QDate(self.current_date))
        self.calendar.clicked.connect(self.on_date_selected)
        # Set calendar to show current month and limit to reasonable date range
        self.calendar.setMinimumDate(QDate(2020, 1, 1))
        self.calendar.setMaximumDate(QDate(2030, 12, 31))
        date_layout.addWidget(self.calendar)
        
        # Current date info
        info_layout = QVBoxLayout()
        
        self.date_label = QLabel(f"Selected: {self.current_date.strftime('%A, %B %d, %Y')}")
        self.date_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_layout.addWidget(self.date_label)
        
        self.status_label = QLabel("Status: Not marked")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        date_layout.addLayout(info_layout)
        
        layout.addWidget(date_group)
    
    def setup_attendance_section(self, layout):
        """Setup attendance marking section"""
        attendance_group = QGroupBox("Mark Attendance")
        attendance_layout = QVBoxLayout(attendance_group)
        
        # Quick actions
        quick_layout = QHBoxLayout()
        
        self.present_all_btn = QPushButton("Mark All Present")
        self.present_all_btn.clicked.connect(self.mark_all_present)
        self.present_all_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        quick_layout.addWidget(self.present_all_btn)
        
        self.absent_all_btn = QPushButton("Mark All Absent")
        self.absent_all_btn.clicked.connect(self.mark_all_absent)
        self.absent_all_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        quick_layout.addWidget(self.absent_all_btn)
        
        self.holiday_btn = QPushButton("Mark as Holiday")
        self.holiday_btn.clicked.connect(self.mark_as_holiday)
        self.holiday_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        quick_layout.addWidget(self.holiday_btn)
        
        attendance_layout.addLayout(quick_layout)
        
        # Period-wise attendance
        periods_layout = QGridLayout()
        self.period_checkboxes = {}
        
        for i in range(1, 9):
            checkbox = QCheckBox(f"Period {i}")
            checkbox.stateChanged.connect(self.on_period_changed)
            periods_layout.addWidget(checkbox, (i-1) // 4, (i-1) % 4)
            self.period_checkboxes[i] = checkbox
        
        attendance_layout.addLayout(periods_layout)
        
        # Notes
        notes_label = QLabel("Notes:")
        attendance_layout.addWidget(notes_label)
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        self.notes_text.setPlaceholderText("Add any notes about today's attendance...")
        self.notes_text.textChanged.connect(self.on_period_changed)  # Auto-update when notes change
        attendance_layout.addWidget(self.notes_text)
        
        layout.addWidget(attendance_group)
    
    def setup_summary_section(self, layout):
        """Setup summary section"""
        summary_group = QGroupBox("Attendance Summary")
        summary_layout = QGridLayout(summary_group)
        
        # Summary labels
        self.total_days_label = QLabel("Total Days: 0")
        self.present_days_label = QLabel("Present Days: 0")
        self.absent_days_label = QLabel("Absent Days: 0")
        self.percentage_label = QLabel("Percentage: 0%")
        
        summary_layout.addWidget(self.total_days_label, 0, 0)
        summary_layout.addWidget(self.present_days_label, 0, 1)
        summary_layout.addWidget(self.absent_days_label, 1, 0)
        summary_layout.addWidget(self.percentage_label, 1, 1)
        
        layout.addWidget(summary_group)
    
    def setup_action_buttons(self, layout):
        """Setup action buttons"""
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Attendance")
        self.save_btn.clicked.connect(self.save_attendance)
        self.save_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        button_layout.addWidget(self.save_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("background-color: #607D8B; color: white; padding: 10px;")
        button_layout.addWidget(self.refresh_btn)

        self.refresh_calendar_btn = QPushButton("Refresh Calendar")
        self.refresh_calendar_btn.clicked.connect(self.force_refresh_calendar)
        self.refresh_calendar_btn.setStyleSheet("background-color: #795548; color: white; padding: 10px;")
        button_layout.addWidget(self.refresh_calendar_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def on_date_selected(self, selected_date):
        """Handle date selection"""
        self.current_date = selected_date.toPython()
        self.load_current_date()
    
    def load_current_date(self):
        """Load attendance for current date"""
        try:
            # Update date label
            self.date_label.setText(f"Selected: {self.current_date.strftime('%A, %B %d, %Y')}")
            
            # Load existing record
            date_str = self.current_date.strftime('%Y-%m-%d')
            self.logger.debug(f"Looking for record with date: '{date_str}'")
            self.current_record = self.attendance_manager.get_record_by_date(date_str)

            if self.current_record:
                self.logger.debug(f"Found record for {date_str}: present_periods={self.current_record.present_periods}, is_holiday={self.current_record.is_holiday}")
                self.load_record_to_ui(self.current_record)
                # Status will be updated by load_record_to_ui -> update_status_display
            else:
                self.logger.debug(f"No record found for {date_str}")
                # Let's check what dates are actually available
                all_records = self.attendance_manager.get_all_records()
                july_2025_records = [r for r in all_records if r.date.startswith('2025-07')]
                self.logger.debug(f"Available July 2025 records: {[r.date for r in july_2025_records[:5]]}")
                self.clear_ui()
                # Update status to indicate no data exists for this date
                self.status_label.setText("Status: No attendance data for this date")
            
            self.refresh_summary()
            
        except Exception as e:
            self.logger.error(f"Error loading date: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load attendance data: {str(e)}")
    
    def load_record_to_ui(self, record: SimpleAttendanceRecord):
        """Load record data to UI"""
        try:
            if not record:
                self.logger.warning("Attempted to load None record to UI")
                return

            # Set flag to prevent auto-save during UI loading
            self.ui_updating = True

            # Load period checkboxes with validation
            for i in range(1, 9):
                try:
                    period_status = getattr(record, f'period_{i}', "Absent")
                    if i in self.period_checkboxes:
                        self.period_checkboxes[i].setChecked(period_status == "Present")
                except Exception as e:
                    self.logger.warning(f"Error loading period {i}: {e}")
                    # Set to default state if error
                    if i in self.period_checkboxes:
                        self.period_checkboxes[i].setChecked(False)

            # Load notes with validation
            try:
                notes = getattr(record, 'notes', '')
                self.notes_text.setPlainText(str(notes) if notes else '')
            except Exception as e:
                self.logger.warning(f"Error loading notes: {e}")
                self.notes_text.clear()

            # Update status display after loading
            self.update_status_display()

            # Reset flag after UI loading is complete
            self.ui_updating = False

        except Exception as e:
            self.logger.error(f"Error loading record to UI: {e}")
            # Clear UI on error
            self.clear_ui()

    def update_status_display(self):
        """Update the status display based on current checkbox states"""
        present_count = sum(1 for cb in self.period_checkboxes.values() if cb.isChecked())
        percentage = (present_count / 8) * 100
        self.status_label.setText(f"Status: {present_count}/8 periods present ({percentage:.1f}%)")
    
    def clear_ui(self):
        """Clear UI for new record"""
        # Set flag to prevent auto-save during UI clearing
        self.ui_updating = True

        for checkbox in self.period_checkboxes.values():
            checkbox.setChecked(False)
        self.notes_text.clear()
        # Don't set status here - let the caller set appropriate message

        # Reset flag after UI clearing is complete
        self.ui_updating = False
    
    def on_period_changed(self):
        """Handle period checkbox changes"""
        # Update UI immediately
        self.update_status_display()

        # Only trigger auto-save if not updating UI programmatically
        if not self.ui_updating:
            self.logger.debug("Period changed by user - triggering auto-save")
            # Delay auto-save to avoid conflicts with UI updates
            self.auto_save_timer.stop()  # Stop any existing timer
            self.auto_save_timer.start(500)  # Start timer with 500ms delay
        else:
            self.logger.debug("Period changed during UI update - skipping auto-save")
    
    def mark_all_present(self):
        """Mark all periods as present"""
        for checkbox in self.period_checkboxes.values():
            checkbox.setChecked(True)
        # Update UI immediately
        self.update_status_display()
        # Delay auto-save
        self.auto_save_timer.stop()
        self.auto_save_timer.start(500)

    def mark_all_absent(self):
        """Mark all periods as absent"""
        for checkbox in self.period_checkboxes.values():
            checkbox.setChecked(False)
        # Update UI immediately
        self.update_status_display()
        # Delay auto-save
        self.auto_save_timer.stop()
        self.auto_save_timer.start(500)
    
    def mark_as_holiday(self):
        """Mark day as holiday"""
        for checkbox in self.period_checkboxes.values():
            checkbox.setChecked(False)
        self.notes_text.setPlainText("Holiday")
        # Update UI immediately
        self.status_label.setText("Status: Holiday (0/8 periods)")
        # Delay auto-save
        self.auto_save_timer.stop()
        self.auto_save_timer.start(500)

    def auto_save_attendance(self):
        """Automatically save attendance when changes are made"""
        try:
            self.logger.debug(f"🔄 Auto-save triggered for date: {self.current_date.strftime('%Y-%m-%d')}")
            # Create record
            date_str = self.current_date.strftime('%Y-%m-%d')
            day_name = self.current_date.strftime('%A')
            notes = self.notes_text.toPlainText().strip()
            is_holiday = "holiday" in notes.lower()

            # Debug: Check checkbox states
            present_count = sum(1 for cb in self.period_checkboxes.values() if cb.isChecked())
            self.logger.debug(f"Auto-saving: {present_count} periods checked")

            # Determine semester and academic year based on date
            semester_number = 1
            academic_year = f"{self.current_date.year}-{self.current_date.year + 1}"

            try:
                from .semester_models import SemesterManager
                semester_manager = SemesterManager(str(self.data_manager.data_dir), self.config)

                # Find semester for this date
                semester_info = semester_manager.get_semester_for_date(self.current_date)
                if semester_info:
                    # Only allow semester 8 if it's active
                    if semester_info.semester_number == 8 and not semester_info.is_active:
                        # Semester 8 is not active yet, use active semester instead
                        active_semester = semester_manager.get_active_semester()
                        if active_semester:
                            semester_number = active_semester.semester_number
                            academic_year = active_semester.academic_year
                    else:
                        semester_number = semester_info.semester_number
                        academic_year = semester_info.academic_year
                else:
                    # Use active semester if no specific semester found
                    active_semester = semester_manager.get_active_semester()
                    if active_semester:
                        semester_number = active_semester.semester_number
                        academic_year = active_semester.academic_year

            except Exception as e:
                self.logger.warning(f"Error determining semester: {e}")

            record = SimpleAttendanceRecord(
                date=date_str,
                day=day_name,
                semester=semester_number,
                academic_year=academic_year,
                notes=notes
            )

            # Set period statuses and debug
            for i in range(1, 9):
                status = "Present" if self.period_checkboxes[i].isChecked() else "Absent"
                setattr(record, f'period_{i}', status)
                self.logger.debug(f"Period {i}: {status}")

            # Check if it's a holiday
            if is_holiday:
                record.is_holiday = True
                for i in range(1, 9):
                    setattr(record, f'period_{i}', "Holiday")

            # Force recalculation of attendance
            record.calculate_attendance()

            # Debug: Check calculated values
            self.logger.debug(f"Record after calculation: present_periods={record.present_periods}, percentage={record.percentage}")

            # Save record silently (no popup messages for auto-save)
            if self.attendance_manager.save_record(record):
                self.current_record = record
                self.refresh_summary()  # This will also update calendar highlighting
                self.force_refresh_calendar()  # Ensure calendar is updated immediately
                self.data_changed.emit()
                self.logger.debug("Auto-save successful")
            else:
                self.logger.warning("Auto-save failed")

        except Exception as e:
            self.logger.error(f"Error auto-saving attendance: {e}")
            # Don't show error messages for auto-save to avoid annoying the user
    
    def save_attendance(self):
        """Save current attendance"""
        try:
            # Validate that at least something is marked or it's a holiday
            has_attendance = any(cb.isChecked() for cb in self.period_checkboxes.values())
            notes = self.notes_text.toPlainText().strip()
            is_holiday = "holiday" in notes.lower()

            if not has_attendance and not is_holiday and not notes:
                reply = QMessageBox.question(
                    self, "Confirm Save",
                    "No attendance marked and no notes added. Save as all absent?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # Create record
            date_str = self.current_date.strftime('%Y-%m-%d')
            day_name = self.current_date.strftime('%A')

            # Determine semester and academic year based on date
            semester_number = 1
            academic_year = f"{self.current_date.year}-{self.current_date.year + 1}"

            try:
                from .semester_models import SemesterManager
                semester_manager = SemesterManager(str(self.data_manager.data_dir), self.config)

                # Find semester for this date
                semester_info = semester_manager.get_semester_for_date(self.current_date)
                if semester_info:
                    # Only allow semester 8 if it's active
                    if semester_info.semester_number == 8 and not semester_info.is_active:
                        # Semester 8 is not active yet, use active semester instead
                        active_semester = semester_manager.get_active_semester()
                        if active_semester:
                            semester_number = active_semester.semester_number
                            academic_year = active_semester.academic_year
                    else:
                        semester_number = semester_info.semester_number
                        academic_year = semester_info.academic_year
                else:
                    # Use active semester if no specific semester found
                    active_semester = semester_manager.get_active_semester()
                    if active_semester:
                        semester_number = active_semester.semester_number
                        academic_year = active_semester.academic_year

            except Exception as e:
                self.logger.warning(f"Error determining semester: {e}")

            record = SimpleAttendanceRecord(
                date=date_str,
                day=day_name,
                semester=semester_number,
                academic_year=academic_year,
                notes=notes
            )

            # Set period statuses
            for i in range(1, 9):
                status = "Present" if self.period_checkboxes[i].isChecked() else "Absent"
                setattr(record, f'period_{i}', status)

            # Check if it's a holiday
            if is_holiday:
                record.is_holiday = True
                for i in range(1, 9):
                    setattr(record, f'period_{i}', "Holiday")

            # Force recalculation of attendance before saving
            record.calculate_attendance()

            # Save record
            if self.attendance_manager.save_record(record):
                QMessageBox.information(self, "Success",
                    f"Attendance saved successfully!\n"
                    f"Date: {self.current_date.strftime('%A, %B %d, %Y')}\n"
                    f"Periods Present: {record.present_periods}/{record.total_periods}\n"
                    f"Percentage: {record.percentage:.1f}%")
                self.current_record = record
                self.refresh_summary()  # This will also update calendar highlighting
                self.force_refresh_calendar()  # Ensure calendar is updated immediately
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to save attendance!")

        except Exception as e:
            self.logger.error(f"Error saving attendance: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save attendance: {str(e)}")
    
    def highlight_calendar_dates(self):
        """Highlight calendar dates based on attendance status using custom calendar widget"""
        try:
            # Get all attendance records
            records = self.attendance_manager.get_all_records()

            print(f"🎨 DEBUG: Calendar highlighting with theme '{self.current_theme}'")
            print(f"🎨 DEBUG: Setting attendance data for {len(records)} records")

            # Set attendance data on the custom calendar widget
            self.calendar.set_attendance_data(records, self.current_theme)

            # Debug counters
            present_count = 0
            absent_count = 0
            holiday_count = 0
            partial_count = 0

            for record in records:
                # Count different types for debugging
                if record.is_holiday or (record.notes and "holiday" in record.notes.lower()):
                    holiday_count += 1
                elif record.present_periods >= record.total_periods and record.total_periods > 0:
                    present_count += 1
                elif record.present_periods == 0 and not record.is_holiday:
                    absent_count += 1
                elif 0 < record.present_periods < record.total_periods:
                    partial_count += 1

            print(f"🎨 DEBUG: Calendar highlighting summary:")
            print(f"🎨 DEBUG: - Present days: {present_count}")
            print(f"🎨 DEBUG: - Absent days: {absent_count}")
            print(f"🎨 DEBUG: - Holiday days: {holiday_count}")
            print(f"🎨 DEBUG: - Partial days: {partial_count}")
            print(f"🎨 DEBUG: - Total highlighted: {present_count + absent_count + holiday_count + partial_count}")

        except Exception as e:
            self.logger.error(f"Error highlighting calendar dates: {e}")
            print(f"❌ ERROR: Calendar highlighting failed: {e}")

    def _is_valid_date(self, date_str):
        """Check if a date string is valid"""
        try:
            date_parts = date_str.split('-')
            if len(date_parts) == 3:
                year, month, day = map(int, date_parts)
                q_date = QDate(year, month, day)
                return q_date.isValid()
        except:
            pass
        return False

    def clear_calendar_formatting(self):
        """Clear all calendar date formatting properly"""
        try:
            # Create a default/empty format
            default_format = QTextCharFormat()

            # Get the current date range visible in the calendar
            current_date = self.calendar.selectedDate()
            current_year = current_date.year()
            current_month = current_date.month()

            # Clear formatting for a reasonable range around the current view
            # This covers the current year and adjacent years
            for year in range(current_year - 2, current_year + 3):
                for month in range(1, 13):
                    # Get the number of days in this month
                    days_in_month = QDate(year, month, 1).daysInMonth()
                    for day in range(1, days_in_month + 1):
                        date = QDate(year, month, day)
                        if date.isValid():
                            self.calendar.setDateTextFormat(date, default_format)

            self.logger.debug("Calendar formatting cleared successfully")

        except Exception as e:
            self.logger.warning(f"Error clearing calendar formatting: {e}")
            # Fallback to the original method
            self.calendar.setDateTextFormat(QDate(), QTextCharFormat())

    def refresh_data(self):
        """Refresh all data"""
        self.load_current_date()
        self.highlight_calendar_dates()  # Update calendar highlighting

    def force_refresh_calendar(self):
        """Force refresh calendar highlighting with debug logging"""
        self.logger.debug("Force refreshing calendar highlighting...")

        # Debug: Check current calendar view
        current_date = self.calendar.selectedDate()
        self.logger.debug(f"Current calendar view: {current_date.toString('yyyy-MM-dd')}")

        # Debug: Check if we have records for the current month
        records = self.attendance_manager.get_all_records()
        current_month_records = [r for r in records if r.date.startswith(f"{current_date.year()}-{current_date.month():02d}")]
        self.logger.debug(f"Records for current month ({current_date.year()}-{current_date.month():02d}): {len(current_month_records)}")

        self.highlight_calendar_dates()
    
    def refresh_summary(self):
        """Refresh summary statistics (semester-aware)"""
        try:
            # Get overall summary
            summary = self.attendance_manager.get_summary()

            # Validate summary data before displaying
            if not isinstance(summary, dict):
                raise ValueError("Summary is not a dictionary")

            required_fields = ['total_days', 'working_days', 'present_days', 'absent_days', 'overall_percentage']
            for field in required_fields:
                if field not in summary:
                    raise KeyError(f"Missing required field: {field}")

            # Try to get semester-specific summary
            try:
                from .semester_models import SemesterManager
                semester_manager = SemesterManager(str(self.data_manager.data_dir), self.config)
                active_semester = semester_manager.get_active_semester()

                if active_semester:
                    semester_summary = semester_manager.get_semester_summary(active_semester.semester_number)
                    if semester_summary:
                        # Use semester-specific data with improved working days display
                        working_days = semester_summary.get('total_working_days', 0)
                        attendance_days = semester_summary['total_days']

                        self.total_days_label.setText(f"Working Days (Sem {active_semester.semester_number}): {working_days} | Recorded: {attendance_days}")
                        self.present_days_label.setText(f"Present Days: {semester_summary['present_days']}")
                        self.absent_days_label.setText(f"Absent Days: {semester_summary['absent_days']}")

                        # Format percentage safely with period information
                        try:
                            percentage = float(semester_summary['attendance_percentage'])
                            total_periods = semester_summary.get('total_periods', 0)
                            present_periods = semester_summary.get('present_periods', 0)
                            self.percentage_label.setText(f"Attendance: {percentage:.1f}% ({present_periods}/{total_periods} periods)")
                        except (ValueError, TypeError):
                            self.percentage_label.setText("Attendance: 0.0%")

                        return  # Exit early if semester summary worked

            except Exception as e:
                self.logger.warning(f"Error getting semester summary: {e}")

            # Fallback to overall summary with improved working days display
            working_days = summary.get('working_days', summary['total_days'])
            self.total_days_label.setText(f"Working Days: {working_days} | Recorded: {summary['total_days']}")
            self.present_days_label.setText(f"Present Days: {summary['present_days']}")
            self.absent_days_label.setText(f"Absent Days: {summary['absent_days']}")

            # Format percentage safely with period information
            try:
                percentage = float(summary['overall_percentage'])
                total_periods = summary.get('total_periods', 0)
                present_periods = summary.get('present_periods', 0)
                self.percentage_label.setText(f"Attendance: {percentage:.1f}% ({present_periods}/{total_periods} periods)")
            except (ValueError, TypeError):
                self.percentage_label.setText("Attendance: 0.0%")
                self.logger.warning("Invalid percentage value in summary")

        except Exception as e:
            self.logger.error(f"Error refreshing summary: {e}")
            # Set default values on error
            self.total_days_label.setText("Total Days: 0")
            self.present_days_label.setText("Present Days: 0")
            self.absent_days_label.setText("Absent Days: 0")
            self.percentage_label.setText("Percentage: 0.0%")

        # Update calendar highlighting after summary refresh
        self.highlight_calendar_dates()

    def setup_records_tab(self, tab_widget):
        """Setup the records viewing and editing tab"""
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 20px to 10px
        layout.setSpacing(8)  # Reduced from 15px to 8px

        # Header with action buttons
        header_layout = QHBoxLayout()

        # Title
        records_title = QLabel("Attendance Records")
        records_title.setObjectName("pageTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        records_title.setFont(font)
        header_layout.addWidget(records_title)

        header_layout.addStretch()

        # Selection controls
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.setObjectName("attendanceSelectAllButton")
        self.select_all_button.setMinimumHeight(35)
        self.select_all_button.clicked.connect(self.select_all_records)
        header_layout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.setObjectName("attendanceDeselectAllButton")
        self.deselect_all_button.setMinimumHeight(35)
        self.deselect_all_button.clicked.connect(self.deselect_all_records)
        header_layout.addWidget(self.deselect_all_button)

        # Action buttons
        self.edit_record_button = QPushButton("Edit Selected")
        self.edit_record_button.setObjectName("attendanceEditRecordButton")
        self.edit_record_button.setMinimumHeight(35)
        self.edit_record_button.setEnabled(False)
        self.edit_record_button.clicked.connect(self.edit_selected_record)
        header_layout.addWidget(self.edit_record_button)

        self.delete_record_button = QPushButton("Delete Selected")
        self.delete_record_button.setObjectName("attendanceDeleteRecordButton")
        self.delete_record_button.setMinimumHeight(35)
        self.delete_record_button.setEnabled(False)
        self.delete_record_button.clicked.connect(self.delete_selected_record)
        header_layout.addWidget(self.delete_record_button)

        self.delete_multiple_button = QPushButton("Delete Multiple")
        self.delete_multiple_button.setObjectName("attendanceDeleteMultipleButton")
        self.delete_multiple_button.setMinimumHeight(35)
        self.delete_multiple_button.setEnabled(False)
        self.delete_multiple_button.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")
        self.delete_multiple_button.clicked.connect(self.delete_multiple_records)
        header_layout.addWidget(self.delete_multiple_button)

        self.refresh_records_button = QPushButton("Refresh")
        self.refresh_records_button.setObjectName("attendanceRefreshRecordsButton")
        self.refresh_records_button.setMinimumHeight(35)
        self.refresh_records_button.clicked.connect(self.load_all_records)
        header_layout.addWidget(self.refresh_records_button)

        layout.addLayout(header_layout)

        # Filter section
        self.setup_filters_section(layout)

        # Records table
        self.records_table = QTableWidget()
        self.records_table.setObjectName("attendanceRecordsTable")
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.records_table.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Allow multiple selection
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setSortingEnabled(True)

        # Set up table columns - added Select column at the beginning
        columns = ["Select", "Date", "Day", "Semester", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "Present", "Total", "Percentage", "Holiday", "Notes"]
        self.records_table.setColumnCount(len(columns))
        self.records_table.setHorizontalHeaderLabels(columns)

        # Set column widths
        header = self.records_table.horizontalHeader()
        header.setStretchLastSection(True)  # Notes column stretches
        header.resizeSection(0, 60)   # Select checkbox
        header.resizeSection(1, 100)  # Date
        header.resizeSection(2, 80)   # Day
        header.resizeSection(3, 80)   # Semester
        # Period columns (P1-P8)
        for i in range(4, 12):
            header.resizeSection(i, 40)
        header.resizeSection(12, 60)  # Present
        header.resizeSection(13, 50)  # Total
        header.resizeSection(14, 80)  # Percentage
        header.resizeSection(15, 60)  # Holiday

        # Connect selection change
        self.records_table.selectionModel().selectionChanged.connect(self.on_record_selection_changed)
        self.records_table.doubleClicked.connect(self.edit_selected_record)

        # Track checkboxes for multiple selection
        self.record_checkboxes = {}

        layout.addWidget(self.records_table)

        # Load records initially
        self.load_all_records()

    def setup_filters_section(self, layout):
        """Setup comprehensive filters section for records"""
        # Filter group box
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout(filter_group)

        # Row 1: Date filters
        date_row = QHBoxLayout()

        # Date range filter
        date_row.addWidget(QLabel("Date Range:"))
        self.start_date_filter = QDateEdit()
        self.start_date_filter.setDate(QDate(2020, 1, 1))  # Default to wide range to show all records
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.dateChanged.connect(self.apply_filters)
        date_row.addWidget(self.start_date_filter)

        date_row.addWidget(QLabel("to"))
        self.end_date_filter = QDateEdit()
        self.end_date_filter.setDate(QDate(2030, 12, 31))  # Default to wide range to show all records
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.dateChanged.connect(self.apply_filters)
        date_row.addWidget(self.end_date_filter)

        # Month filter
        date_row.addWidget(QLabel("Month:"))
        self.month_filter = QComboBox()
        months = ["All Months", "January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        self.month_filter.addItems(months)
        self.month_filter.currentTextChanged.connect(self.apply_filters)
        date_row.addWidget(self.month_filter)

        # Year filter
        date_row.addWidget(QLabel("Year:"))
        self.year_filter = QComboBox()
        current_year = datetime.now().year
        years = ["All Years"] + [str(year) for year in range(current_year - 5, current_year + 2)]
        self.year_filter.addItems(years)
        self.year_filter.currentTextChanged.connect(self.apply_filters)
        date_row.addWidget(self.year_filter)

        date_row.addStretch()
        filter_layout.addLayout(date_row)

        # Row 2: Type and semester filters
        type_row = QHBoxLayout()

        # Attendance type filter
        type_row.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Present", "Absent", "Holiday", "Partial"])
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        type_row.addWidget(self.type_filter)

        # Semester filter - only show completed semesters and current active semester
        type_row.addWidget(QLabel("Semester:"))
        self.semester_filter = QComboBox()

        # Get available semesters (completed + active)
        available_semesters = ["All Semesters"]
        try:
            from .semester_models import SemesterManager
            semester_manager = SemesterManager(str(self.data_manager.data_dir), self.config)
            active_semester = semester_manager.get_active_semester()

            # Add completed semesters (1-6) and current active semester (7)
            if active_semester and active_semester.semester_number == 7:
                # Currently in semester 7, show semesters 1-7
                available_semesters.extend([f"Semester {i}" for i in range(1, 8)])
            else:
                # Default to showing semesters 1-6 if no active semester or different active semester
                available_semesters.extend([f"Semester {i}" for i in range(1, 7)])
        except Exception as e:
            # Fallback: show semesters 1-7 (excluding 8)
            available_semesters.extend([f"Semester {i}" for i in range(1, 8)])

        self.semester_filter.addItems(available_semesters)
        self.semester_filter.currentTextChanged.connect(self.apply_filters)
        type_row.addWidget(self.semester_filter)

        # Percentage range filter
        type_row.addWidget(QLabel("Attendance %:"))
        self.min_percentage_filter = QSpinBox()
        self.min_percentage_filter.setRange(0, 100)
        self.min_percentage_filter.setValue(0)
        self.min_percentage_filter.setSuffix("%")
        self.min_percentage_filter.valueChanged.connect(self.apply_filters)
        type_row.addWidget(self.min_percentage_filter)

        type_row.addWidget(QLabel("to"))
        self.max_percentage_filter = QSpinBox()
        self.max_percentage_filter.setRange(0, 100)
        self.max_percentage_filter.setValue(100)
        self.max_percentage_filter.setSuffix("%")
        self.max_percentage_filter.valueChanged.connect(self.apply_filters)
        type_row.addWidget(self.max_percentage_filter)

        type_row.addStretch()
        filter_layout.addLayout(type_row)

        # Row 3: Search and actions
        search_row = QHBoxLayout()

        # Search filter
        search_row.addWidget(QLabel("Search:"))
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("Search in notes, dates...")
        self.search_filter.textChanged.connect(self.apply_filters)
        search_row.addWidget(self.search_filter)

        # Clear filters button
        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.clicked.connect(self.clear_filters)
        search_row.addWidget(self.clear_filters_button)

        # Apply filters button
        self.apply_filters_button = QPushButton("Apply Filters")
        self.apply_filters_button.clicked.connect(self.apply_filters)
        search_row.addWidget(self.apply_filters_button)

        filter_layout.addLayout(search_row)
        layout.addWidget(filter_group)

    def load_all_records(self):
        """Load all attendance records into the table"""
        try:
            self.logger.debug("Loading all attendance records...")

            # Get all records from the data manager
            records = self.attendance_manager.get_all_records()

            self.logger.debug(f"Found {len(records) if records else 0} attendance records")

            if not records:
                self.logger.debug("No records found, clearing table")
                self.records_table.setRowCount(0)
                return

            # Use the new populate method
            self.populate_records_table(records)
            self.logger.debug("Successfully populated records table")

        except Exception as e:
            self.logger.error(f"Error loading records: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load records: {str(e)}")

    def apply_filters(self):
        """Apply all active filters to the records table"""
        try:
            # Get all records
            all_records = self.attendance_manager.get_all_records()

            if not all_records:
                self.records_table.setRowCount(0)
                return

            # Apply filters
            filtered_records = self.filter_records(all_records)

            # Update table with filtered records
            self.populate_records_table(filtered_records)

        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            QMessageBox.warning(self, "Error", f"Failed to apply filters: {str(e)}")

    def filter_records(self, records):
        """Filter records based on current filter settings"""
        filtered = []

        # Get filter values
        start_date = self.start_date_filter.date().toPython()
        end_date = self.end_date_filter.date().toPython()
        month_filter = self.month_filter.currentText()
        year_filter = self.year_filter.currentText()
        type_filter = self.type_filter.currentText()
        semester_filter = self.semester_filter.currentText()
        min_percentage = self.min_percentage_filter.value()
        max_percentage = self.max_percentage_filter.value()
        search_text = self.search_filter.text().strip().lower()

        # Debug logging
        self.logger.debug(f"Filtering {len(records)} records with:")
        self.logger.debug(f"  Date range: {start_date} to {end_date}")
        self.logger.debug(f"  Month: {month_filter}, Year: {year_filter}")
        self.logger.debug(f"  Type: {type_filter}, Semester: {semester_filter}")
        self.logger.debug(f"  Percentage: {min_percentage}% to {max_percentage}%")
        self.logger.debug(f"  Search: '{search_text}'")

        for record in records:
            try:
                # Parse record date
                record_date = datetime.strptime(record.date, '%Y-%m-%d').date()

                # Date range filter
                if not (start_date <= record_date <= end_date):
                    continue

                # Month filter
                if month_filter != "All Months":
                    month_names = ["", "January", "February", "March", "April", "May", "June",
                                 "July", "August", "September", "October", "November", "December"]
                    if record_date.month != month_names.index(month_filter):
                        continue

                # Year filter
                if year_filter != "All Years":
                    if record_date.year != int(year_filter):
                        continue

                # Type filter
                if type_filter != "All Types":
                    if type_filter == "Present" and record.present_periods == 0:
                        continue
                    elif type_filter == "Absent" and (record.present_periods > 0 or record.is_holiday):
                        continue
                    elif type_filter == "Holiday" and not record.is_holiday:
                        continue
                    elif type_filter == "Partial" and not (0 < record.present_periods < record.total_periods):
                        continue

                # Semester filter
                if semester_filter != "All Semesters":
                    semester_num = int(semester_filter.split()[-1])
                    if record.semester != semester_num:
                        continue

                # Percentage filter
                if not (min_percentage <= record.percentage <= max_percentage):
                    continue

                # Search filter
                if search_text:
                    searchable_text = f"{record.date} {record.day} {record.notes or ''}".lower()
                    if search_text not in searchable_text:
                        continue

                # If we get here, record passes all filters
                filtered.append(record)

            except (ValueError, AttributeError) as e:
                self.logger.warning(f"Error filtering record {record.date}: {e}")
                continue

        self.logger.debug(f"Filtering complete: {len(filtered)} records match filters")
        if len(filtered) > 0:
            self.logger.debug(f"First 5 filtered dates: {[r.date for r in filtered[:5]]}")
        return filtered

    def populate_records_table(self, records):
        """Populate the records table with given records"""
        try:
            # Sort records by date (most recent first) - convert to datetime for proper sorting
            def date_sort_key(record):
                try:
                    # Convert date string (YYYY-MM-DD) to datetime for proper sorting
                    from datetime import datetime
                    return datetime.strptime(record.date, '%Y-%m-%d')
                except (ValueError, AttributeError):
                    # Fallback to string sorting if date parsing fails
                    return record.date

            records.sort(key=date_sort_key, reverse=True)
            self.logger.debug(f"Sorted {len(records)} records by date. First 5 dates: {[r.date for r in records[:5]]}")

            self.records_table.setRowCount(len(records))
            self.record_checkboxes.clear()  # Clear previous checkboxes

            for row, record in enumerate(records):
                # Select checkbox
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(self.on_checkbox_changed)
                self.records_table.setCellWidget(row, 0, checkbox)
                self.record_checkboxes[row] = checkbox

                # Date
                self.records_table.setItem(row, 1, QTableWidgetItem(record.date))

                # Day
                self.records_table.setItem(row, 2, QTableWidgetItem(record.day))

                # Semester
                self.records_table.setItem(row, 3, QTableWidgetItem(str(record.semester)))

                # Period columns (P1-P8)
                colors = self.get_theme_colors(self.current_theme)
                for i in range(1, 9):
                    period_status = getattr(record, f'period_{i}', 'Absent')
                    item = QTableWidgetItem(period_status)

                    # Color code the periods with theme-aware colors
                    if period_status == "Present":
                        item.setBackground(QColor(colors['present_bg']))
                        item.setForeground(QColor(colors['present_text']))
                    elif period_status == "Holiday":
                        item.setBackground(QColor(colors['holiday_bg']))
                        item.setForeground(QColor(colors['holiday_text']))
                    else:  # Absent
                        item.setBackground(QColor(colors['absent_bg']))
                        item.setForeground(QColor(colors['absent_text']))

                    self.records_table.setItem(row, 3 + i, item)

                # Present periods
                present_item = QTableWidgetItem(str(record.present_periods))
                if record.present_periods == record.total_periods:
                    present_item.setBackground(QColor(colors['present_bg']))
                    present_item.setForeground(QColor(colors['present_text']))
                elif record.present_periods > 0:
                    present_item.setBackground(QColor(colors['partial_bg']))
                    present_item.setForeground(QColor(colors['partial_text']))
                else:
                    present_item.setBackground(QColor(colors['absent_bg']))
                    present_item.setForeground(QColor(colors['absent_text']))
                self.records_table.setItem(row, 12, present_item)

                # Total periods
                self.records_table.setItem(row, 13, QTableWidgetItem(str(record.total_periods)))

                # Percentage
                percentage_item = QTableWidgetItem(f"{record.percentage:.1f}%")
                if record.percentage >= 75:
                    percentage_item.setBackground(QColor(colors['present_bg']))
                    percentage_item.setForeground(QColor(colors['present_text']))
                elif record.percentage >= 50:
                    percentage_item.setBackground(QColor(colors['partial_bg']))
                    percentage_item.setForeground(QColor(colors['partial_text']))
                else:
                    percentage_item.setBackground(QColor(colors['absent_bg']))
                    percentage_item.setForeground(QColor(colors['absent_text']))
                self.records_table.setItem(row, 14, percentage_item)

                # Holiday
                holiday_item = QTableWidgetItem("Yes" if record.is_holiday else "No")
                if record.is_holiday:
                    holiday_item.setBackground(QColor(colors['holiday_bg']))
                    holiday_item.setForeground(QColor(colors['holiday_text']))
                self.records_table.setItem(row, 15, holiday_item)

                # Notes
                notes = record.notes if record.notes else ""
                self.records_table.setItem(row, 16, QTableWidgetItem(notes))

        except Exception as e:
            self.logger.error(f"Error populating records table: {e}")

    def clear_filters(self):
        """Clear all filters and show all records"""
        try:
            # Reset all filter controls to be maximally inclusive
            # Set date range to cover a very wide range to include all possible records
            self.start_date_filter.setDate(QDate(2020, 1, 1))  # Start from 2020
            self.end_date_filter.setDate(QDate(2030, 12, 31))  # End at 2030
            self.month_filter.setCurrentIndex(0)  # "All Months"
            self.year_filter.setCurrentIndex(0)   # "All Years"
            self.type_filter.setCurrentIndex(0)   # "All Types"
            self.semester_filter.setCurrentIndex(0)  # "All Semesters"
            self.min_percentage_filter.setValue(0)
            self.max_percentage_filter.setValue(100)
            self.search_filter.clear()

            self.logger.debug("Filters cleared - set to maximally inclusive values")

            # Reload all records
            self.load_all_records()

        except Exception as e:
            self.logger.error(f"Error clearing filters: {e}")

    def on_record_selection_changed(self):
        """Handle record selection change"""
        has_selection = self.records_table.currentRow() >= 0
        self.edit_record_button.setEnabled(has_selection)
        self.delete_record_button.setEnabled(has_selection)

        # Update multiple delete button based on checkbox selections
        self.update_multiple_delete_button()

    def on_checkbox_changed(self):
        """Handle checkbox state change"""
        self.update_multiple_delete_button()

    def update_multiple_delete_button(self):
        """Update the state of the multiple delete button"""
        selected_count = self.get_selected_records_count()
        self.delete_multiple_button.setEnabled(selected_count > 0)

        if selected_count > 0:
            self.delete_multiple_button.setText(f"Delete Multiple ({selected_count})")
        else:
            self.delete_multiple_button.setText("Delete Multiple")

    def get_selected_records_count(self):
        """Get the number of selected records"""
        count = 0
        for checkbox in self.record_checkboxes.values():
            if checkbox.isChecked():
                count += 1
        return count

    def get_selected_record_dates(self):
        """Get the dates of selected records"""
        selected_dates = []
        for row, checkbox in self.record_checkboxes.items():
            if checkbox.isChecked():
                date_item = self.records_table.item(row, 1)  # Date is in column 1 now
                if date_item:
                    selected_dates.append(date_item.text())
        return selected_dates

    def select_all_records(self):
        """Select all records"""
        for checkbox in self.record_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all_records(self):
        """Deselect all records"""
        for checkbox in self.record_checkboxes.values():
            checkbox.setChecked(False)

    def edit_selected_record(self):
        """Edit the selected attendance record"""
        current_row = self.records_table.currentRow()
        if current_row >= 0:
            # Get the date from the selected row (Date is now in column 1)
            date_item = self.records_table.item(current_row, 1)
            if date_item:
                selected_date = date_item.text()
                # Switch to the first tab and load the selected date
                self.tab_widget.setCurrentIndex(0)
                # Parse the date and set it in the calendar
                try:
                    date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
                    self.current_date = date_obj
                    self.calendar.setSelectedDate(QDate(date_obj))
                    self.load_current_date()
                    QMessageBox.information(self, "Edit Mode",
                        f"Switched to edit mode for {date_obj.strftime('%A, %B %d, %Y')}.\n"
                        f"Make your changes and click 'Save Attendance'.")
                except ValueError as e:
                    QMessageBox.warning(self, "Error", f"Invalid date format: {e}")

    def delete_selected_record(self):
        """Delete the selected attendance record"""
        current_row = self.records_table.currentRow()
        if current_row >= 0:
            date_item = self.records_table.item(current_row, 1)  # Date is now in column 1
            if date_item:
                selected_date = date_item.text()

                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    f"Are you sure you want to delete the attendance record for {selected_date}?\n\n"
                    f"This action cannot be undone.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    if self.attendance_manager.delete_record(selected_date):
                        QMessageBox.information(self, "Success", "Record deleted successfully!")
                        self.load_all_records()
                        self.refresh_summary()
                        self.force_refresh_calendar()
                        self.data_changed.emit()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to delete record!")

    def delete_multiple_records(self):
        """Delete multiple selected attendance records"""
        selected_dates = self.get_selected_record_dates()

        if not selected_dates:
            QMessageBox.warning(self, "No Selection", "Please select one or more records to delete.")
            return

        # Show confirmation dialog with details
        selected_count = len(selected_dates)
        date_list = "\n".join(f"• {date}" for date in selected_dates[:10])  # Show first 10 dates
        if selected_count > 10:
            date_list += f"\n... and {selected_count - 10} more records"

        reply = QMessageBox.question(
            self, "Confirm Multiple Delete",
            f"Are you sure you want to delete {selected_count} attendance record(s)?\n\n"
            f"Records to be deleted:\n{date_list}\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Delete records one by one
            deleted_count = 0
            failed_dates = []

            for date in selected_dates:
                if self.attendance_manager.delete_record(date):
                    deleted_count += 1
                else:
                    failed_dates.append(date)

            # Show results
            if deleted_count > 0:
                success_msg = f"Successfully deleted {deleted_count} record(s)!"
                if failed_dates:
                    failed_list = ", ".join(failed_dates)
                    success_msg += f"\n\nFailed to delete {len(failed_dates)} record(s): {failed_list}"
                    QMessageBox.warning(self, "Partial Success", success_msg)
                else:
                    QMessageBox.information(self, "Success", success_msg)

                # Refresh the interface
                self.load_all_records()
                self.refresh_summary()
                self.force_refresh_calendar()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete any records!")

    def setup_semester_tab(self, tab_widget):
        """Setup the semester management tab"""
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 20px to 10px

        try:
            from .semester_widgets import SemesterManagementWidget

            # Create semester management widget
            self.semester_widget = SemesterManagementWidget(self.data_manager, self.config)
            self.semester_widget.semester_changed.connect(self.on_semester_changed)

            layout.addWidget(self.semester_widget)

        except Exception as e:
            self.logger.error(f"Error setting up semester tab: {e}")

            # Fallback UI
            error_label = QLabel(f"Error loading semester management: {str(e)}")
            error_label.setStyleSheet("color: red; font-style: italic;")
            layout.addWidget(error_label)

    def on_semester_changed(self):
        """Handle semester change"""
        try:
            # Refresh current date display to show correct semester
            self.load_current_date()
            self.refresh_summary()
            self.data_changed.emit()
        except Exception as e:
            self.logger.error(f"Error handling semester change: {e}")

    def on_tab_changed(self, index):
        """Handle tab change event"""
        try:
            # Tab indices: 0 = Mark Attendance, 1 = All Records, 2 = Semester Management
            if index == 1:  # All Records tab
                self.logger.debug("Switched to All Records tab - refreshing data")
                self.load_all_records()
            elif index == 0:  # Mark Attendance tab
                self.logger.debug("Switched to Mark Attendance tab - refreshing current date")
                self.load_current_date()
                self.force_refresh_calendar()
            elif index == 2:  # Semester Management tab
                self.logger.debug("Switched to Semester Management tab")
                # Refresh semester widget if it exists
                if hasattr(self, 'semester_widget') and self.semester_widget:
                    try:
                        self.semester_widget.load_semesters()
                    except Exception as e:
                        self.logger.warning(f"Error refreshing semester widget: {e}")
        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")

    def showEvent(self, event):
        """Handle widget show event"""
        super().showEvent(event)
        # Force refresh calendar highlighting when widget becomes visible
        QTimer.singleShot(100, self.force_refresh_calendar)


# Alias for compatibility
AttendanceTrackerWidget = SimpleAttendanceTrackerWidget
