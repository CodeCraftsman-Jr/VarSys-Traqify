#!/usr/bin/env python3
"""
Simplified Attendance Models - No Pandas Dependencies
Uses basic CSV operations to avoid recursion issues
"""

import csv
import os
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging


@dataclass
class SimpleAttendanceRecord:
    """Simplified attendance record without pandas dependencies"""
    id: int = 0
    date: str = ""
    day: str = ""
    semester: int = 1
    academic_year: str = ""
    period_1: str = "Absent"
    period_2: str = "Absent"
    period_3: str = "Absent"
    period_4: str = "Absent"
    period_5: str = "Absent"
    period_6: str = "Absent"
    period_7: str = "Absent"
    period_8: str = "Absent"
    total_periods: int = 8
    present_periods: int = 0
    percentage: float = 0.0
    is_holiday: bool = False
    is_unofficial_leave: bool = False
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """Calculate attendance after initialization"""
        self.calculate_attendance()
    
    def calculate_attendance(self):
        """Calculate present periods and percentage with error handling"""
        try:
            periods = [
                self.period_1, self.period_2, self.period_3, self.period_4,
                self.period_5, self.period_6, self.period_7, self.period_8
            ]

            # Count present periods safely
            self.present_periods = sum(1 for period in periods if str(period).strip() == "Present")

            # Ensure present_periods is not negative
            if self.present_periods < 0:
                self.present_periods = 0

            # Ensure total_periods is valid
            if self.total_periods <= 0:
                self.total_periods = 8  # Default to 8 periods

            # Calculate percentage safely
            if self.is_holiday or self.is_unofficial_leave:
                self.percentage = 0.0
            else:
                try:
                    self.percentage = (self.present_periods / self.total_periods) * 100
                    # Ensure percentage is within valid range
                    if self.percentage < 0:
                        self.percentage = 0.0
                    elif self.percentage > 100:
                        self.percentage = 100.0
                except ZeroDivisionError:
                    self.percentage = 0.0
                except (TypeError, ValueError):
                    self.percentage = 0.0

        except Exception as e:
            # If anything goes wrong, set safe defaults
            print(f"Warning: Error in calculate_attendance: {e}")
            self.present_periods = 0
            self.percentage = 0.0
            if self.total_periods <= 0:
                self.total_periods = 8
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV writing"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimpleAttendanceRecord':
        """Create from dictionary (CSV row) with enhanced error handling"""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        # Convert string values to appropriate types with error handling
        record = cls()

        for key, value in data.items():
            if hasattr(record, key):
                try:
                    if key == 'id':
                        setattr(record, key, int(value) if value and str(value).strip() else 0)
                    elif key in ['semester', 'total_periods', 'present_periods']:
                        setattr(record, key, int(value) if value and str(value).strip() else 0)
                    elif key == 'percentage':
                        setattr(record, key, float(value) if value and str(value).strip() else 0.0)
                    elif key in ['is_holiday', 'is_unofficial_leave']:
                        setattr(record, key, str(value).lower().strip() in ['true', '1', 'yes'])
                    else:
                        # Handle string fields safely
                        str_value = str(value) if value is not None else ""
                        # Clean up common CSV artifacts
                        if str_value.lower() in ['nan', 'none', 'null']:
                            str_value = ""
                        setattr(record, key, str_value)
                except (ValueError, TypeError) as e:
                    # Log the error but continue with default value
                    print(f"Warning: Error converting field {key}={value}: {e}")
                    if key == 'id':
                        setattr(record, key, 0)
                    elif key in ['semester', 'total_periods', 'present_periods']:
                        setattr(record, key, 0)
                    elif key == 'percentage':
                        setattr(record, key, 0.0)
                    elif key in ['is_holiday', 'is_unofficial_leave']:
                        setattr(record, key, False)
                    else:
                        setattr(record, key, "")

        # Validate and calculate attendance
        try:
            record.calculate_attendance()
        except Exception as e:
            print(f"Warning: Error calculating attendance: {e}")
            # Set safe defaults
            record.present_periods = 0
            record.percentage = 0.0

        return record


class SimpleAttendanceDataManager:
    """Simplified data manager using basic CSV operations"""
    
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
        self.attendance_dir = os.path.join(data_directory, "attendance")
        self.records_file = os.path.join(self.attendance_dir, "attendance_records.csv")
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        os.makedirs(self.attendance_dir, exist_ok=True)
        
        # CSV headers
        self.headers = [
            'id', 'date', 'day', 'semester', 'academic_year',
            'period_1', 'period_2', 'period_3', 'period_4',
            'period_5', 'period_6', 'period_7', 'period_8',
            'total_periods', 'present_periods', 'percentage',
            'is_holiday', 'is_unofficial_leave', 'notes',
            'created_at', 'updated_at'
        ]
        
        # Initialize CSV file if it doesn't exist
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(self.headers)
                self.logger.info(f"Initialized attendance CSV: {self.records_file}")
            except Exception as e:
                self.logger.error(f"Failed to initialize CSV: {e}")
    
    def get_all_records(self) -> List[SimpleAttendanceRecord]:
        """Get all attendance records"""
        records = []
        try:
            if not os.path.exists(self.records_file):
                return records
            
            with open(self.records_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        record = SimpleAttendanceRecord.from_dict(row)
                        records.append(record)
                    except Exception as e:
                        self.logger.warning(f"Skipping invalid record: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error reading records: {e}")
        
        return records
    
    def get_record_by_date(self, target_date: str) -> Optional[SimpleAttendanceRecord]:
        """Get record for specific date"""
        records = self.get_all_records()
        for record in records:
            if record.date == target_date:
                return record
        return None
    
    def save_record(self, record: SimpleAttendanceRecord) -> bool:
        """Save or update a record"""
        try:
            records = self.get_all_records()
            
            # Check if record exists
            existing_index = None
            for i, existing_record in enumerate(records):
                if existing_record.date == record.date:
                    existing_index = i
                    break
            
            # Set timestamps
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if existing_index is not None:
                # Update existing
                record.id = records[existing_index].id
                record.updated_at = now
                records[existing_index] = record
            else:
                # Add new
                record.id = max([r.id for r in records], default=0) + 1
                record.created_at = now
                record.updated_at = now
                records.append(record)
            
            # Write all records back to CSV
            return self._write_all_records(records)
        
        except Exception as e:
            self.logger.error(f"Error saving record: {e}")
            return False
    
    def _write_all_records(self, records: List[SimpleAttendanceRecord]) -> bool:
        """Write all records to CSV"""
        try:
            with open(self.records_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()
                for record in records:
                    writer.writerow(record.to_dict())
            return True
        except Exception as e:
            self.logger.error(f"Error writing records: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get attendance summary with proper working days and period-based calculation"""
        records = self.get_all_records()

        if not records:
            return {
                'total_days': 0,
                'working_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'holiday_days': 0,
                'total_periods': 0,
                'present_periods': 0,
                'overall_percentage': 0.0,
                'current_semester': 1,
                'academic_year': f"{datetime.now().year}-{datetime.now().year + 1}"
            }

        # Calculate day-based statistics
        total_days = len(records)
        holiday_days = len([r for r in records if r.is_holiday])
        working_days = total_days - holiday_days  # Working days = total days - holidays

        # Calculate period-based statistics (more accurate for attendance)
        working_records = [r for r in records if not r.is_holiday and not r.is_unofficial_leave]

        total_periods = sum(r.total_periods for r in working_records)
        present_periods = sum(r.present_periods for r in working_records)

        # Calculate attendance percentage based on periods, not days
        overall_percentage = (present_periods / total_periods * 100) if total_periods > 0 else 0.0

        # Calculate present/absent days for display
        present_days = len([r for r in working_records if r.present_periods > 0])
        absent_days = len([r for r in working_records if r.present_periods == 0])

        # Get current semester info
        current_record = records[-1] if records else None
        current_semester = current_record.semester if current_record else 1
        academic_year = current_record.academic_year if current_record else f"{datetime.now().year}-{datetime.now().year + 1}"

        return {
            'total_days': total_days,
            'working_days': working_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'holiday_days': holiday_days,
            'total_periods': total_periods,
            'present_periods': present_periods,
            'overall_percentage': round(overall_percentage, 2),
            'current_semester': current_semester,
            'academic_year': academic_year
        }

    def delete_record(self, date_str: str) -> bool:
        """Delete an attendance record by date"""
        try:
            if not os.path.exists(self.records_file):
                return False

            # Read all records
            records = []
            with open(self.records_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['date'] != date_str:  # Keep all records except the one to delete
                        records.append(row)

            # Write back the filtered records
            with open(self.records_file, 'w', newline='', encoding='utf-8') as file:
                if records:
                    writer = csv.DictWriter(file, fieldnames=self.headers)
                    writer.writeheader()
                    writer.writerows(records)
                else:
                    # If no records left, just write headers
                    writer = csv.writer(file)
                    writer.writerow(self.headers)

            self.logger.info(f"Deleted attendance record for date: {date_str}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting record for {date_str}: {e}")
            return False
