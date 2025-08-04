"""
Settings Dialog Module
Comprehensive settings dialog with Holiday Management
"""

import logging
import requests
from datetime import datetime, date
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox,
    QProgressBar, QDateEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal, QDate, QThread
from PySide6.QtGui import QFont


class HolidayFetcher(QThread):
    """Thread for fetching holidays from API"""
    
    holidays_fetched = Signal(list)
    error_occurred = Signal(str)
    progress_updated = Signal(int)
    
    def __init__(self, api_key: str, country: str, year: int):
        super().__init__()
        self.api_key = api_key
        self.country = country
        self.year = year
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Fetch holidays from Calendarific API"""
        try:
            self.progress_updated.emit(10)
            
            # Calendarific API endpoint
            url = "https://calendarific.com/api/v2/holidays"
            params = {
                'api_key': self.api_key,
                'country': self.country,
                'year': self.year,
                'type': 'national,local,religious,observance'
            }
            
            self.progress_updated.emit(30)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            self.progress_updated.emit(70)
            
            data = response.json()
            
            if data.get('meta', {}).get('code') == 200:
                holidays = data.get('response', {}).get('holidays', [])
                self.progress_updated.emit(100)
                self.holidays_fetched.emit(holidays)
            else:
                error_msg = data.get('meta', {}).get('error_detail', 'Unknown API error')
                self.error_occurred.emit(f"API Error: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Network Error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Error fetching holidays: {str(e)}")


class HolidayManagementWidget(QWidget):
    """Widget for managing holidays"""
    
    holidays_updated = Signal()
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.holidays_data = []
        
        self.setup_ui()
        self.load_saved_holidays()
    
    def setup_ui(self):
        """Setup the holiday management UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # API Configuration Section
        api_group = QGroupBox("Holiday API Configuration")
        api_layout = QFormLayout(api_group)
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter your Calendarific API key")
        # Load API key from environment or settings
        import os
        api_key = os.getenv('CALENDARIFIC_API_KEY', '')
        self.api_key_edit.setText(api_key)
        api_layout.addRow("API Key:", self.api_key_edit)
        
        # Country selection
        self.country_combo = QComboBox()
        self.country_combo.addItems([
            "IN", "US", "GB", "CA", "AU", "DE", "FR", "JP", "CN", "BR"
        ])
        self.country_combo.setCurrentText("IN")  # Default to India
        api_layout.addRow("Country:", self.country_combo)
        
        # Year selection
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setRange(2020, 2030)
        self.year_spinbox.setValue(datetime.now().year)
        api_layout.addRow("Year:", self.year_spinbox)
        
        # Fetch button
        self.fetch_button = QPushButton("Fetch Holidays")
        self.fetch_button.clicked.connect(self.fetch_holidays)
        api_layout.addRow("", self.fetch_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        api_layout.addRow("Progress:", self.progress_bar)
        
        layout.addWidget(api_group)
        
        # Holidays Table Section
        table_group = QGroupBox("Holidays")
        table_layout = QVBoxLayout(table_group)
        
        # Table controls
        controls_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_holidays)
        controls_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all_holidays)
        controls_layout.addWidget(self.deselect_all_button)
        
        controls_layout.addStretch()

        # Show existing holidays button
        self.show_existing_button = QPushButton("Show Existing Holidays")
        self.show_existing_button.clicked.connect(self.show_existing_holidays)
        self.show_existing_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px; font-weight: bold;")
        controls_layout.addWidget(self.show_existing_button)

        self.apply_button = QPushButton("Apply Selected Holidays")
        self.apply_button.clicked.connect(self.apply_selected_holidays)
        self.apply_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        controls_layout.addWidget(self.apply_button)
        
        table_layout.addLayout(controls_layout)
        
        # Holidays table
        self.holidays_table = QTableWidget()
        self.holidays_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.holidays_table.setAlternatingRowColors(True)
        
        # Set up columns
        columns = ["Select", "Date", "Name", "Type", "Description"]
        self.holidays_table.setColumnCount(len(columns))
        self.holidays_table.setHorizontalHeaderLabels(columns)
        
        # Set column widths
        header = self.holidays_table.horizontalHeader()
        header.resizeSection(0, 60)   # Select
        header.resizeSection(1, 100)  # Date
        header.resizeSection(2, 200)  # Name
        header.resizeSection(3, 100)  # Type
        header.setStretchLastSection(True)  # Description
        
        table_layout.addWidget(self.holidays_table)
        
        layout.addWidget(table_group)
        
        # Status section
        self.status_label = QLabel("Ready to fetch holidays")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def fetch_holidays(self):
        """Fetch holidays from API"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter an API key")
            return
        
        country = self.country_combo.currentText()
        year = self.year_spinbox.value()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.fetch_button.setEnabled(False)
        self.status_label.setText("Fetching holidays...")
        
        # Start fetching in background thread
        self.holiday_fetcher = HolidayFetcher(api_key, country, year)
        self.holiday_fetcher.holidays_fetched.connect(self.on_holidays_fetched)
        self.holiday_fetcher.error_occurred.connect(self.on_fetch_error)
        self.holiday_fetcher.progress_updated.connect(self.progress_bar.setValue)
        self.holiday_fetcher.start()
    
    def on_holidays_fetched(self, holidays):
        """Handle successfully fetched holidays"""
        self.holidays_data = holidays
        self.populate_holidays_table()
        
        self.progress_bar.setVisible(False)
        self.fetch_button.setEnabled(True)
        self.status_label.setText(f"Fetched {len(holidays)} holidays successfully")
        
        QMessageBox.information(self, "Success", 
            f"Successfully fetched {len(holidays)} holidays for {self.year_spinbox.value()}")
    
    def on_fetch_error(self, error_message):
        """Handle fetch error"""
        self.progress_bar.setVisible(False)
        self.fetch_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_message}")
        
        QMessageBox.warning(self, "Error", f"Failed to fetch holidays:\n{error_message}")
    
    def populate_holidays_table(self):
        """Populate the holidays table with fetched data"""
        if not self.holidays_data:
            self.holidays_table.setRowCount(0)
            return
        
        self.holidays_table.setRowCount(len(self.holidays_data))
        
        for row, holiday in enumerate(self.holidays_data):
            # Select checkbox
            checkbox = QCheckBox()
            self.holidays_table.setCellWidget(row, 0, checkbox)
            
            # Date
            date_str = holiday.get('date', {}).get('iso', '')
            self.holidays_table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Name
            name = holiday.get('name', '')
            self.holidays_table.setItem(row, 2, QTableWidgetItem(name))
            
            # Type
            holiday_type = ', '.join(holiday.get('type', []))
            self.holidays_table.setItem(row, 3, QTableWidgetItem(holiday_type))
            
            # Description
            description = holiday.get('description', '')
            self.holidays_table.setItem(row, 4, QTableWidgetItem(description))
    
    def select_all_holidays(self):
        """Select all holidays"""
        for row in range(self.holidays_table.rowCount()):
            checkbox = self.holidays_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all_holidays(self):
        """Deselect all holidays"""
        for row in range(self.holidays_table.rowCount()):
            checkbox = self.holidays_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def show_existing_holidays(self):
        """Show existing holidays from all years"""
        existing_holidays = self.load_saved_holidays()

        if not existing_holidays:
            QMessageBox.information(self, "No Holidays", "No holidays found in storage.")
            return

        # Group holidays by year
        holidays_by_year = {}
        for holiday in existing_holidays:
            date_str = holiday.get('date', '')
            try:
                year = date_str[:4]  # Extract year from YYYY-MM-DD format
                if year not in holidays_by_year:
                    holidays_by_year[year] = []
                holidays_by_year[year].append(holiday)
            except:
                continue

        # Create summary message
        summary_lines = [f"📅 **Existing Holidays Summary**\n"]
        total_holidays = 0

        for year in sorted(holidays_by_year.keys()):
            count = len(holidays_by_year[year])
            total_holidays += count
            summary_lines.append(f"**{year}**: {count} holidays")

        summary_lines.append(f"\n**Total**: {total_holidays} holidays across {len(holidays_by_year)} years")
        summary_lines.append(f"\n💡 **Tip**: You can add holidays for any year without losing existing ones!")

        QMessageBox.information(self, "Existing Holidays", "\n".join(summary_lines))
    
    def apply_selected_holidays(self):
        """Apply selected holidays to the attendance system"""
        selected_holidays = []
        
        for row in range(self.holidays_table.rowCount()):
            checkbox = self.holidays_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                date_item = self.holidays_table.item(row, 1)
                name_item = self.holidays_table.item(row, 2)
                
                if date_item and name_item:
                    selected_holidays.append({
                        'date': date_item.text(),
                        'name': name_item.text()
                    })
        
        if not selected_holidays:
            QMessageBox.warning(self, "Warning", "No holidays selected")
            return
        
        # Save holidays and apply to attendance
        self.save_holidays(selected_holidays)
        applied_count = self.apply_holidays_to_attendance(selected_holidays)

        # Show detailed success message
        year = self.year_spinbox.value()
        QMessageBox.information(self, "Success",
            f"Successfully processed {len(selected_holidays)} holidays for {year}:\n"
            f"• Applied {applied_count} new holidays to attendance\n"
            f"• Holidays saved and merged with existing data\n"
            f"• You can now add holidays for other years")

        self.holidays_updated.emit()
    
    def save_holidays(self, holidays):
        """Save holidays to data storage, merging with existing holidays"""
        try:
            holidays_file = self.data_manager.data_dir / "holidays.json"
            import json

            # Load existing holidays
            existing_holidays = []
            if holidays_file.exists():
                try:
                    with open(holidays_file, 'r', encoding='utf-8') as f:
                        existing_holidays = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load existing holidays: {e}")
                    existing_holidays = []

            # Create a set of existing holiday dates for quick lookup
            existing_dates = {holiday.get('date', '') for holiday in existing_holidays}

            # Add new holidays that don't already exist
            new_holidays_added = 0
            for holiday in holidays:
                holiday_date = holiday.get('date', '')
                if holiday_date not in existing_dates:
                    existing_holidays.append(holiday)
                    existing_dates.add(holiday_date)
                    new_holidays_added += 1

            # Sort holidays by date for better organization
            existing_holidays.sort(key=lambda x: x.get('date', ''))

            # Save merged holidays
            with open(holidays_file, 'w', encoding='utf-8') as f:
                json.dump(existing_holidays, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Added {new_holidays_added} new holidays. Total holidays: {len(existing_holidays)}")

        except Exception as e:
            self.logger.error(f"Error saving holidays: {e}")
    
    def load_saved_holidays(self):
        """Load previously saved holidays"""
        try:
            holidays_file = self.data_manager.data_dir / "holidays.json"
            if holidays_file.exists():
                import json
                with open(holidays_file, 'r', encoding='utf-8') as f:
                    saved_holidays = json.load(f)
                self.logger.info(f"Loaded {len(saved_holidays)} saved holidays")
                return saved_holidays
        except Exception as e:
            self.logger.error(f"Error loading saved holidays: {e}")
        return []
    
    def apply_holidays_to_attendance(self, holidays):
        """Apply holidays to the attendance system"""
        try:
            # Import attendance manager
            from ..modules.attendance.simple_models import SimpleAttendanceDataManager, SimpleAttendanceRecord

            attendance_manager = SimpleAttendanceDataManager(str(self.data_manager.data_dir))

            applied_count = 0
            for holiday in holidays:
                try:
                    # Parse date - handle both simple date format and ISO format with timezone
                    date_str = holiday['date']

                    # Try different date formats
                    holiday_date = None
                    for date_format in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            if 'T' in date_str:
                                # Extract just the date part if it's an ISO datetime
                                date_part = date_str.split('T')[0]
                                holiday_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                            else:
                                holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            break
                        except ValueError:
                            continue

                    if holiday_date is None:
                        self.logger.warning(f"Could not parse date for holiday {holiday['name']}: {date_str}")
                        continue

                    # Create holiday record with clean date format
                    clean_date_str = holiday_date.strftime('%Y-%m-%d')
                    record = SimpleAttendanceRecord(
                        date=clean_date_str,
                        day=holiday_date.strftime('%A'),
                        semester=1,  # Default semester
                        academic_year=f"{holiday_date.year}-{holiday_date.year + 1}",
                        notes=f"Holiday: {holiday['name']}",
                        is_holiday=True
                    )

                    # Set all periods as holiday
                    for i in range(1, 9):
                        setattr(record, f'period_{i}', "Holiday")

                    # Save the record
                    if attendance_manager.save_record(record):
                        applied_count += 1

                except Exception as e:
                    self.logger.warning(f"Error applying holiday {holiday['name']}: {e}")

            self.logger.info(f"Applied {applied_count} holidays to attendance system")
            return applied_count

        except Exception as e:
            self.logger.error(f"Error applying holidays to attendance: {e}")
            QMessageBox.warning(self, "Error", f"Error applying holidays: {str(e)}")
            return 0


class SettingsDialog(QDialog):
    """Main settings dialog"""
    
    settings_changed = Signal()
    
    def __init__(self, config, data_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.load_settings()
        
        self.setModal(True)
    
    def setup_ui(self):
        """Setup the settings dialog UI"""
        self.setWindowTitle("Settings")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # General settings tab
        self.general_tab = self.create_general_tab()
        self.tab_widget.addTab(self.general_tab, "General")
        
        # Holiday management tab
        self.holiday_tab = HolidayManagementWidget(self.data_manager)
        self.holiday_tab.holidays_updated.connect(self.settings_changed.emit)
        self.tab_widget.addTab(self.holiday_tab, "Holiday Management")

        # Firebase Account tab
        try:
            from .firebase_settings import FirebaseAccountWidget
            self.firebase_tab = FirebaseAccountWidget()
            self.firebase_tab.settings_changed.connect(self.settings_changed.emit)
            self.tab_widget.addTab(self.firebase_tab, "Firebase Account")
        except ImportError as e:
            # Firebase dependencies not available
            pass

        # Sync tab
        try:
            from .sync_widgets import SyncControlWidget
            from ..core.firebase_sync import FirebaseSyncEngine

            # Create sync engine if not already created
            if not hasattr(self, 'sync_engine'):
                self.sync_engine = FirebaseSyncEngine(self.data_manager)

            self.sync_tab = SyncControlWidget(self.sync_engine)
            self.sync_tab.settings_changed.connect(self.settings_changed.emit)
            self.tab_widget.addTab(self.sync_tab, "Sync")
        except ImportError as e:
            # Firebase dependencies not available
            pass

        # Update settings tab
        try:
            from ..core.update_manager import update_manager
            self.update_tab = update_manager.get_update_settings_widget()
            self.update_tab.settings_changed.connect(self.settings_changed.emit)
            self.tab_widget.addTab(self.update_tab, "Updates")
        except ImportError as e:
            # Update system not available
            pass
        
        layout.addWidget(self.tab_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Application settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "colorwave"])
        app_layout.addRow("Theme:", self.theme_combo)
        
        self.auto_save_spinbox = QSpinBox()
        self.auto_save_spinbox.setRange(30, 3600)
        self.auto_save_spinbox.setSuffix(" seconds")
        app_layout.addRow("Auto-save interval:", self.auto_save_spinbox)
        
        layout.addWidget(app_group)
        
        # Data settings
        data_group = QGroupBox("Data Settings")
        data_layout = QFormLayout(data_group)
        
        self.backup_spinbox = QSpinBox()
        self.backup_spinbox.setRange(1, 100)
        data_layout.addRow("Max backup files:", self.backup_spinbox)
        
        layout.addWidget(data_group)

        # Attendance settings
        attendance_group = QGroupBox("Attendance Settings")
        attendance_layout = QFormLayout(attendance_group)

        self.college_year_spinbox = QSpinBox()
        self.college_year_spinbox.setRange(2020, 2030)
        self.college_year_spinbox.setValue(2024)  # Default to 2024
        attendance_layout.addRow("College Joining Year:", self.college_year_spinbox)

        layout.addWidget(attendance_group)

        layout.addStretch()
        return tab
    
    def load_settings(self):
        """Load current settings into the UI"""
        # General settings
        theme_index = self.theme_combo.findText(self.config.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        self.auto_save_spinbox.setValue(self.config.auto_save_interval)
        self.backup_spinbox.setValue(self.config.max_backup_files)
        self.college_year_spinbox.setValue(getattr(self.config, 'college_joining_year', 2024))
    
    def save_settings(self):
        """Save settings and close dialog"""
        # Update config
        self.config.theme = self.theme_combo.currentText()
        self.config.auto_save_interval = self.auto_save_spinbox.value()
        self.config.max_backup_files = self.backup_spinbox.value()
        self.config.college_joining_year = self.college_year_spinbox.value()
        
        # Save config to file
        self.config.save_to_file()
        
        self.settings_changed.emit()
        self.accept()
