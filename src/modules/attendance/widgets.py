"""
Attendance Tracker UI Widgets
Contains all UI components for the attendance tracking module
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QCheckBox, QFrame, QGroupBox, QScrollArea, QTabWidget,
    QProgressBar, QSpinBox, QCalendarWidget, QMessageBox, QDialog,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QPainter, QBrush

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

from .models import AttendanceRecord, SemesterConfig, AttendanceDataModel
from src.ui.themes.utils import get_calendar_color_with_alpha


class PeriodButton(QPushButton):
    """Custom button for period attendance marking"""
    
    period_clicked = Signal(int, str)  # period_number, status
    
    def __init__(self, period_number: int, status: str = "Absent", parent=None):
        super().__init__(parent)
        
        self.period_number = period_number
        self.current_status = status
        
        self.setObjectName("periodButton")
        self.setMinimumSize(60, 40)
        self.setMaximumSize(60, 40)
        self.setCheckable(True)
        
        self.update_appearance()
        self.clicked.connect(self.on_clicked)
    
    def update_appearance(self):
        """Update button appearance based on status"""
        self.setText(f"P{self.period_number}")
        
        # Set tooltip
        self.setToolTip(f"Period {self.period_number}: {self.current_status}")
        
        # Set style based on status
        if self.current_status == "Present":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 2px solid #45a049;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.setChecked(True)
        elif self.current_status == "Late":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: 2px solid #f57c00;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
            self.setChecked(True)
        elif self.current_status == "Excused":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: 2px solid #1976D2;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            self.setChecked(True)
        elif self.current_status == "Holiday":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #9C27B0;
                    color: white;
                    border: 2px solid #7B1FA2;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7B1FA2;
                }
            """)
            self.setChecked(True)
        elif self.current_status == "Unofficial Leave":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #795548;
                    color: white;
                    border: 2px solid #5D4037;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5D4037;
                }
            """)
            self.setChecked(True)
        else:  # Absent
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: 2px solid #d32f2f;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            self.setChecked(False)
    
    def set_status(self, status: str):
        """Set the period status"""
        self.current_status = status
        self.update_appearance()
    
    def on_clicked(self):
        """Handle button click to cycle through statuses"""
        # Cycle through statuses: Absent -> Present -> Late -> Excused -> Absent
        status_cycle = ["Absent", "Present", "Late", "Excused"]
        
        try:
            current_index = status_cycle.index(self.current_status)
            next_index = (current_index + 1) % len(status_cycle)
            new_status = status_cycle[next_index]
        except ValueError:
            new_status = "Present"  # Default if current status is not in cycle
        
        self.set_status(new_status)
        self.period_clicked.emit(self.period_number, new_status)


class AttendanceCalendarWidget(QCalendarWidget):
    """Custom calendar widget for attendance tracking"""
    
    date_selected = Signal(QDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.attendance_data = {}  # date -> attendance_percentage
        self.setObjectName("attendanceCalendar")
        
        # Connect signals
        self.clicked.connect(self.date_selected.emit)
    
    def set_attendance_data(self, data: Dict[date, float]):
        """Set attendance data for calendar coloring"""
        self.attendance_data = data
        self.updateCells()
    
    def paintCell(self, painter, rect, date):
        """Custom paint method to color cells based on attendance"""
        # Call parent paint first
        super().paintCell(painter, rect, date)
        
        # Get attendance percentage for this date
        date_obj = date.toPython()
        attendance_percentage = self.attendance_data.get(date_obj, None)
        
        if attendance_percentage is not None:
            # Choose color based on attendance percentage using theme-aware colors
            if attendance_percentage >= 75:
                color = get_calendar_color_with_alpha('success', 150)
            elif attendance_percentage >= 50:
                color = get_calendar_color_with_alpha('warning', 150)
            elif attendance_percentage > 0:
                color = get_calendar_color_with_alpha('error', 150)
            else:
                color = get_calendar_color_with_alpha('neutral', 150)
            
            # Draw colored overlay
            painter.fillRect(rect, color)
            
            # Draw percentage text
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect, Qt.AlignCenter, f"{attendance_percentage:.0f}%")


class DailyAttendanceWidget(QWidget):
    """Widget for marking daily attendance"""
    
    attendance_changed = Signal(AttendanceRecord)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_record = None
        self.period_buttons = {}
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the daily attendance UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_frame = QFrame()
        header_frame.setObjectName("attendanceHeader")
        header_layout = QVBoxLayout(header_frame)
        
        self.date_label = QLabel("Select a date")
        self.date_label.setObjectName("attendanceDateLabel")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.date_label.setFont(font)
        self.date_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.date_label)
        
        self.day_label = QLabel("")
        self.day_label.setObjectName("attendanceDayLabel")
        self.day_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.day_label)
        
        layout.addWidget(header_frame)
        
        # Period grid
        periods_frame = QGroupBox("Periods")
        periods_frame.setObjectName("attendancePeriodsFrame")
        periods_layout = QGridLayout(periods_frame)
        periods_layout.setSpacing(10)
        
        # Create period buttons
        for i in range(1, 9):
            button = PeriodButton(i)
            button.period_clicked.connect(self.on_period_changed)
            self.period_buttons[i] = button
            
            row = (i - 1) // 4
            col = (i - 1) % 4
            periods_layout.addWidget(button, row, col)
        
        layout.addWidget(periods_frame)
        
        # Quick actions
        actions_frame = QGroupBox("Quick Actions")
        actions_frame.setObjectName("attendanceActionsFrame")
        actions_layout = QHBoxLayout(actions_frame)
        
        self.mark_all_present_btn = QPushButton("Mark All Present")
        self.mark_all_present_btn.setObjectName("attendanceActionButton")
        self.mark_all_present_btn.clicked.connect(self.mark_all_present)
        actions_layout.addWidget(self.mark_all_present_btn)
        
        self.mark_all_absent_btn = QPushButton("Mark All Absent")
        self.mark_all_absent_btn.setObjectName("attendanceActionButton")
        self.mark_all_absent_btn.clicked.connect(self.mark_all_absent)
        actions_layout.addWidget(self.mark_all_absent_btn)
        
        self.mark_holiday_btn = QPushButton("Mark Holiday")
        self.mark_holiday_btn.setObjectName("attendanceActionButton")
        self.mark_holiday_btn.clicked.connect(self.mark_holiday)
        actions_layout.addWidget(self.mark_holiday_btn)
        
        self.mark_leave_btn = QPushButton("Unofficial Leave")
        self.mark_leave_btn.setObjectName("attendanceActionButton")
        self.mark_leave_btn.clicked.connect(self.mark_unofficial_leave)
        actions_layout.addWidget(self.mark_leave_btn)
        
        layout.addWidget(actions_frame)
        
        # Summary
        summary_frame = QFrame()
        summary_frame.setObjectName("attendanceSummaryFrame")
        summary_layout = QFormLayout(summary_frame)
        
        self.present_periods_label = QLabel("0")
        self.present_periods_label.setObjectName("attendanceSummaryValue")
        summary_layout.addRow("Present Periods:", self.present_periods_label)
        
        self.total_periods_label = QLabel("8")
        self.total_periods_label.setObjectName("attendanceSummaryValue")
        summary_layout.addRow("Total Periods:", self.total_periods_label)
        
        self.percentage_label = QLabel("0%")
        self.percentage_label.setObjectName("attendancePercentageValue")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.percentage_label.setFont(font)
        summary_layout.addRow("Percentage:", self.percentage_label)
        
        layout.addWidget(summary_frame)
        
        # Notes
        notes_frame = QGroupBox("Notes")
        notes_frame.setObjectName("attendanceNotesFrame")
        notes_layout = QVBoxLayout(notes_frame)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes for this day...")
        self.notes_edit.setObjectName("attendanceNotesEdit")
        self.notes_edit.textChanged.connect(self.on_notes_changed)
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_frame)
        
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        pass
    
    def set_attendance_record(self, record: AttendanceRecord):
        """Set the attendance record to display"""
        self.current_record = record
        
        # Update date display
        if isinstance(record.date, date):
            self.date_label.setText(record.date.strftime("%B %d, %Y"))
            self.day_label.setText(record.date.strftime("%A"))
        
        # Update period buttons
        for i in range(1, 9):
            status = record.get_period_status(i)
            self.period_buttons[i].set_status(status)
        
        # Update summary
        self.update_summary()
        
        # Update notes
        notes_text = str(record.notes) if record.notes is not None else ""
        self.notes_edit.setPlainText(notes_text)
    
    def update_summary(self):
        """Update the summary display"""
        if not self.current_record:
            return
        
        self.present_periods_label.setText(str(self.current_record.present_periods))
        self.total_periods_label.setText(str(self.current_record.total_periods))
        self.percentage_label.setText(f"{self.current_record.percentage:.1f}%")
        
        # Color code percentage
        if self.current_record.percentage >= 75:
            color = "#4CAF50"  # Green
        elif self.current_record.percentage >= 50:
            color = "#FF9800"  # Orange
        else:
            color = "#f44336"  # Red
        
        self.percentage_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def on_period_changed(self, period_number: int, status: str):
        """Handle period status change"""
        if self.current_record:
            self.current_record.set_period_status(period_number, status)
            self.update_summary()
            self.attendance_changed.emit(self.current_record)
    
    def on_notes_changed(self):
        """Handle notes change"""
        if self.current_record:
            self.current_record.notes = self.notes_edit.toPlainText()
            self.attendance_changed.emit(self.current_record)
    
    def mark_all_present(self):
        """Mark all periods as present"""
        if self.current_record:
            self.current_record.mark_all_present()
            self.set_attendance_record(self.current_record)
            self.attendance_changed.emit(self.current_record)
    
    def mark_all_absent(self):
        """Mark all periods as absent"""
        if self.current_record:
            self.current_record.mark_all_absent()
            self.set_attendance_record(self.current_record)
            self.attendance_changed.emit(self.current_record)
    
    def mark_holiday(self):
        """Mark day as holiday"""
        if self.current_record:
            self.current_record.mark_holiday(True)
            self.set_attendance_record(self.current_record)
            self.attendance_changed.emit(self.current_record)
    
    def mark_unofficial_leave(self):
        """Mark day as unofficial leave"""
        if self.current_record:
            self.current_record.mark_unofficial_leave(True)
            self.set_attendance_record(self.current_record)
            self.attendance_changed.emit(self.current_record)


class AttendanceStatsWidget(QWidget):
    """Widget displaying attendance statistics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the statistics UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("Attendance Statistics")
        title_label.setObjectName("attendanceStatsTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Current semester info
        semester_frame = QFrame()
        semester_frame.setObjectName("attendanceSemesterFrame")
        semester_layout = QFormLayout(semester_frame)

        self.semester_label = QLabel("Semester 1")
        self.semester_label.setObjectName("attendanceSemesterValue")
        semester_layout.addRow("Current Semester:", self.semester_label)

        self.academic_year_label = QLabel("2023-2024")
        self.academic_year_label.setObjectName("attendanceSemesterValue")
        semester_layout.addRow("Academic Year:", self.academic_year_label)

        layout.addWidget(semester_frame)

        # Statistics
        stats_frame = QFrame()
        stats_frame.setObjectName("attendanceStatsFrame")
        stats_layout = QFormLayout(stats_frame)

        # Overall percentage
        self.overall_percentage_label = QLabel("0%")
        self.overall_percentage_label.setObjectName("attendanceOverallPercentage")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        self.overall_percentage_label.setFont(font)
        stats_layout.addRow("Overall Percentage:", self.overall_percentage_label)

        # Threshold status
        self.threshold_status_label = QLabel("Below Threshold")
        self.threshold_status_label.setObjectName("attendanceThresholdStatus")
        stats_layout.addRow("Threshold Status:", self.threshold_status_label)

        # Working days
        self.working_days_label = QLabel("0")
        self.working_days_label.setObjectName("attendanceStatValue")
        stats_layout.addRow("Working Days:", self.working_days_label)

        # Present periods
        self.present_periods_label = QLabel("0")
        self.present_periods_label.setObjectName("attendanceStatValue")
        stats_layout.addRow("Present Periods:", self.present_periods_label)

        # Total periods
        self.total_periods_label = QLabel("0")
        self.total_periods_label.setObjectName("attendanceStatValue")
        stats_layout.addRow("Total Periods:", self.total_periods_label)

        layout.addWidget(stats_frame)

        # Progress bar
        progress_frame = QFrame()
        progress_frame.setObjectName("attendanceProgressFrame")
        progress_layout = QVBoxLayout(progress_frame)

        progress_label = QLabel("Progress to 75% Threshold")
        progress_label.setObjectName("attendanceProgressLabel")
        progress_layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("attendanceProgressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(progress_frame)

        layout.addStretch()

    def update_stats(self, stats: Dict[str, Any]):
        """Update the statistics display"""
        # Semester info
        self.semester_label.setText(f"Semester {stats.get('current_semester', 0)}")
        self.academic_year_label.setText(stats.get('current_academic_year', ''))

        # Overall percentage
        percentage = stats.get('overall_percentage', 0)
        self.overall_percentage_label.setText(f"{percentage:.1f}%")

        # Color code percentage
        if percentage >= 75:
            color = "#4CAF50"  # Green
            status = "Above Threshold ✓"
        elif percentage >= 65:
            color = "#FF9800"  # Orange
            status = "Near Threshold ⚠"
        else:
            color = "#f44336"  # Red
            status = "Below Threshold ✗"

        self.overall_percentage_label.setStyleSheet(f"color: {color};")
        self.threshold_status_label.setText(status)
        self.threshold_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Other stats
        self.working_days_label.setText(str(stats.get('working_days', 0)))
        self.present_periods_label.setText(str(stats.get('present_periods', 0)))
        self.total_periods_label.setText(str(stats.get('total_periods', 0)))

        # Progress bar
        self.progress_bar.setValue(int(min(100, percentage)))
        self.progress_bar.setFormat(f"{percentage:.1f}%")


class AttendanceTrackerWidget(QWidget):
    """Main attendance tracker widget"""

    def __init__(self, data_manager, config, parent=None):
        super().__init__(parent)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*50)
        self.logger.info("INITIALIZING ATTENDANCE TRACKER WIDGET")
        self.logger.info("="*50)

        try:
            self.logger.debug("Setting up core components...")
            self.data_manager = data_manager
            self.config = config
            self.logger.debug("Data manager and config assigned")

            self.logger.debug("Creating AttendanceDataModel...")
            self.attendance_model = AttendanceDataModel(data_manager)
            self.logger.debug("AttendanceDataModel created successfully")

            self.current_date = date.today()
            self.logger.debug(f"Current date set to: {self.current_date}")

            self.logger.debug("Setting up UI...")
            self.setup_ui()
            self.logger.debug("UI setup complete")

            self.logger.debug("Setting up connections...")
            self.setup_connections()
            self.logger.debug("Connections setup complete")

            self.logger.debug("Refreshing data...")
            self.refresh_data()
            self.logger.debug("Data refresh complete")

            # Setup auto-refresh timer (disabled for now to prevent recursion issues)
            # self.refresh_timer = QTimer()
            # self.refresh_timer.timeout.connect(self.refresh_data)
            # self.refresh_timer.start(60000)  # Refresh every minute

            self.logger.info("✅ AttendanceTrackerWidget initialization SUCCESSFUL")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in AttendanceTrackerWidget.__init__: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error details: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        self.create_header(layout)

        # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("attendanceTabWidget")

        # Daily tab
        self.daily_tab = self.create_daily_tab()
        self.tab_widget.addTab(self.daily_tab, "Daily Attendance")

        # Calendar tab
        self.calendar_tab = self.create_calendar_tab()
        self.tab_widget.addTab(self.calendar_tab, "Calendar View")

        # Statistics tab
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")

        layout.addWidget(self.tab_widget)

    def create_header(self, layout):
        """Create header with title and action buttons"""
        header_frame = QFrame()
        header_frame.setObjectName("attendanceHeader")
        header_frame.setMaximumHeight(50)  # Standardized header height
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)  # Standardized margins
        header_layout.setSpacing(8)  # Standardized spacing

        # Title
        title_label = QLabel("Attendance Tracker")
        title_label.setObjectName("attendanceTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)  # Standardized font size
        title_label.setFont(font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Quick actions
        self.today_button = QPushButton("Go to Today")
        self.today_button.setObjectName("attendanceTodayButton")
        self.today_button.setMinimumHeight(32)  # Standardized button height
        self.today_button.setMaximumHeight(32)
        header_layout.addWidget(self.today_button)

        self.semester_settings_button = QPushButton("Semester Settings")
        self.semester_settings_button.setObjectName("attendanceSemesterButton")
        self.semester_settings_button.setMinimumHeight(35)
        header_layout.addWidget(self.semester_settings_button)

        layout.addWidget(header_frame)

    def create_daily_tab(self):
        """Create daily attendance tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(20)

        # Left panel - Daily attendance widget
        self.daily_attendance = DailyAttendanceWidget()
        layout.addWidget(self.daily_attendance)

        # Right panel - Statistics
        self.stats_widget = AttendanceStatsWidget()
        layout.addWidget(self.stats_widget)

        return tab

    def create_calendar_tab(self):
        """Create calendar view tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Simple calendar placeholder
        calendar_label = QLabel("Calendar view with attendance visualization coming soon...")
        calendar_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(calendar_label)

        return tab

    def create_stats_tab(self):
        """Create statistics tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Additional detailed statistics could go here
        detailed_stats_label = QLabel("Detailed statistics and reports coming soon...")
        detailed_stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(detailed_stats_label)

        return tab

    def setup_connections(self):
        """Setup signal connections"""
        # Header buttons
        self.today_button.clicked.connect(self.go_to_today)
        self.semester_settings_button.clicked.connect(self.show_semester_settings)

        # Daily attendance
        self.daily_attendance.attendance_changed.connect(self.on_attendance_changed)

        # Data model connections
        self.data_manager.data_changed.connect(self.on_data_changed)

    def refresh_data(self):
        """Refresh all data"""
        try:
            self.load_daily_attendance()
            self.update_statistics()
        except Exception as e:
            print(f"Error refreshing attendance data: {e}")
            # Set default values to prevent crashes
            pass

    def load_daily_attendance(self):
        """Load attendance for current date"""
        try:
            record = self.attendance_model.get_or_create_record_for_date(self.current_date)
            self.daily_attendance.set_attendance_record(record)
        except Exception as e:
            print(f"Error loading daily attendance: {e}")
            # Create a default record to prevent crashes
            from .models import AttendanceRecord
            default_record = AttendanceRecord(date=self.current_date)
            self.daily_attendance.set_attendance_record(default_record)

    def update_statistics(self):
        """Update statistics display"""
        stats = self.attendance_model.get_attendance_summary()
        self.stats_widget.update_stats(stats)

    def go_to_today(self):
        """Navigate to today's date"""
        self.current_date = date.today()
        self.refresh_data()

    def on_attendance_changed(self, record: AttendanceRecord):
        """Handle attendance record changes"""
        # Save the record
        self.attendance_model.save_attendance_record(record)

        # Refresh statistics
        self.update_statistics()

    def show_semester_settings(self):
        """Show semester settings dialog"""
        QMessageBox.information(self, "Semester Settings", "Semester settings dialog coming soon...")

    def on_data_changed(self, module: str, operation: str):
        """Handle data changes"""
        if module == "attendance":
            self.refresh_data()
