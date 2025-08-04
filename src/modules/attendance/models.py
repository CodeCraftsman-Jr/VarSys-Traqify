"""
Attendance Tracker Data Models
Handles attendance tracking data structure and validation
"""

import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class AttendanceStatus(Enum):
    """Attendance status enumeration"""
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    EXCUSED = "Excused"
    HOLIDAY = "Holiday"
    UNOFFICIAL_LEAVE = "Unofficial Leave"


class SemesterType(Enum):
    """Semester type enumeration"""
    ODD = "Odd"
    EVEN = "Even"


@dataclass
class AttendanceRecord:
    """Data class for daily attendance records"""
    id: Optional[int] = None
    date: Union[str, datetime, date] = None
    day: str = ""  # Monday, Tuesday, etc.
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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.date is None:
            self.date = date.today()
        elif isinstance(self.date, str):
            try:
                self.date = datetime.strptime(self.date, '%Y-%m-%d').date()
            except ValueError:
                self.date = date.today()
        elif isinstance(self.date, datetime):
            self.date = self.date.date()
        
        # Set day name
        if isinstance(self.date, date):
            self.day = self.date.strftime('%A')
        
        if self.created_at is None:
            self.created_at = datetime.now()
        
        self.updated_at = datetime.now()
        
        # Calculate attendance
        self.calculate_attendance()
    
    def calculate_attendance(self):
        """Calculate present periods and percentage"""
        periods = [
            self.period_1, self.period_2, self.period_3, self.period_4,
            self.period_5, self.period_6, self.period_7, self.period_8
        ]
        
        # Count present periods
        self.present_periods = sum(1 for period in periods if period == "Present")
        
        # Calculate percentage
        if self.is_holiday or self.is_unofficial_leave:
            self.percentage = 0.0  # Holidays/leaves don't count towards percentage
        else:
            self.percentage = (self.present_periods / self.total_periods) * 100
    
    def set_period_status(self, period_num: int, status: str):
        """Set status for a specific period"""
        if 1 <= period_num <= 8:
            setattr(self, f"period_{period_num}", status)
            self.calculate_attendance()
    
    def get_period_status(self, period_num: int) -> str:
        """Get status for a specific period"""
        if 1 <= period_num <= 8:
            return getattr(self, f"period_{period_num}")
        return "Absent"
    
    def mark_all_present(self):
        """Mark all periods as present"""
        for i in range(1, 9):
            setattr(self, f"period_{i}", "Present")
        self.calculate_attendance()
    
    def mark_all_absent(self):
        """Mark all periods as absent"""
        for i in range(1, 9):
            setattr(self, f"period_{i}", "Absent")
        self.calculate_attendance()
    
    def mark_holiday(self, is_holiday: bool = True):
        """Mark day as holiday"""
        self.is_holiday = is_holiday
        if is_holiday:
            self.is_unofficial_leave = False
            # Mark all periods as holiday
            for i in range(1, 9):
                setattr(self, f"period_{i}", "Holiday")
        self.calculate_attendance()
    
    def mark_unofficial_leave(self, is_leave: bool = True):
        """Mark day as unofficial leave"""
        self.is_unofficial_leave = is_leave
        if is_leave:
            self.is_holiday = False
            # Mark all periods as unofficial leave
            for i in range(1, 9):
                setattr(self, f"period_{i}", "Unofficial Leave")
        self.calculate_attendance()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        if isinstance(data['date'], date):
            data['date'] = data['date'].strftime('%Y-%m-%d')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(data['updated_at'], datetime):
            data['updated_at'] = data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttendanceRecord':
        """Create from dictionary"""
        # Handle datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()
        
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            try:
                data['updated_at'] = datetime.strptime(data['updated_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['updated_at'] = datetime.now()
        
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate the attendance record"""
        errors = []
        
        if self.semester < 1 or self.semester > 8:
            errors.append("Semester must be between 1 and 8")
        
        if not self.academic_year:
            errors.append("Academic year is required")
        
        valid_statuses = ["Present", "Absent", "Late", "Excused", "Holiday", "Unofficial Leave"]
        for i in range(1, 9):
            period_status = getattr(self, f"period_{i}")
            if period_status not in valid_statuses:
                errors.append(f"Invalid status for period {i}: {period_status}")
        
        return errors


@dataclass
class SemesterConfig:
    """Data class for semester configuration"""
    id: Optional[int] = None
    semester: int = 1
    academic_year: str = ""
    start_date: Union[str, datetime, date] = None
    end_date: Union[str, datetime, date] = None
    total_working_days: int = 0
    holidays: List[str] = None  # List of holiday dates
    is_current: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.start_date and isinstance(self.start_date, str):
            try:
                self.start_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
            except ValueError:
                self.start_date = date.today()
        elif isinstance(self.start_date, datetime):
            self.start_date = self.start_date.date()
        
        if self.end_date and isinstance(self.end_date, str):
            try:
                self.end_date = datetime.strptime(self.end_date, '%Y-%m-%d').date()
            except ValueError:
                self.end_date = None
        elif isinstance(self.end_date, datetime):
            self.end_date = self.end_date.date()
        
        if self.holidays is None:
            self.holidays = []
        
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV storage"""
        data = asdict(self)
        
        # Convert date objects to strings
        if isinstance(data['start_date'], date):
            data['start_date'] = data['start_date'].strftime('%Y-%m-%d')
        if data['end_date'] and isinstance(data['end_date'], date):
            data['end_date'] = data['end_date'].strftime('%Y-%m-%d')
        if isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert holidays list to comma-separated string
        if isinstance(data['holidays'], list):
            data['holidays'] = ','.join(data['holidays'])
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemesterConfig':
        """Create from dictionary"""
        # Handle datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['created_at'] = datetime.now()
        
        # Convert holidays string to list
        if 'holidays' in data and isinstance(data['holidays'], str):
            data['holidays'] = data['holidays'].split(',') if data['holidays'] else []
        
        return cls(**data)


class AttendanceDataModel:
    """Data model for attendance tracking management"""

    def __init__(self, data_manager):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("="*40)
        self.logger.info("INITIALIZING ATTENDANCE DATA MODEL")
        self.logger.info("="*40)

        try:
            self.logger.debug("Setting up data manager...")
            self.data_manager = data_manager
            self.module_name = "attendance"
            self.records_filename = "attendance_records.csv"
            self.semesters_filename = "semester_config.csv"
            self.logger.debug(f"Module: {self.module_name}, Records: {self.records_filename}, Semesters: {self.semesters_filename}")

            # Default columns for attendance records CSV
            self.records_columns = [
                'id', 'date', 'day', 'semester', 'academic_year',
                'period_1', 'period_2', 'period_3', 'period_4',
                'period_5', 'period_6', 'period_7', 'period_8',
                'total_periods', 'present_periods', 'percentage',
                'is_holiday', 'is_unofficial_leave', 'notes',
                'created_at', 'updated_at'
            ]
            self.logger.debug(f"Records columns defined: {len(self.records_columns)} columns")

            # Default columns for semester config CSV
            self.semesters_columns = [
                'id', 'semester', 'academic_year', 'start_date', 'end_date',
                'total_working_days', 'holidays', 'is_current', 'created_at'
            ]
            self.logger.debug(f"Semester columns defined: {len(self.semesters_columns)} columns")

            # Initialize default semester if not exists
            self.logger.debug("Initializing default semester...")
            self._initialize_default_semester()
            self.logger.debug("Default semester initialization complete")

            self.logger.info("✅ AttendanceDataModel initialization SUCCESSFUL")

        except Exception as e:
            self.logger.error(f"❌ CRITICAL ERROR in AttendanceDataModel.__init__: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _initialize_default_semester(self):
        """Initialize default semester if it doesn't exist"""
        try:
            if not self.data_manager.file_exists(self.module_name, self.semesters_filename):
                current_year = datetime.now().year
                academic_year = f"{current_year}-{current_year + 1}"

                default_semester = SemesterConfig(
                    semester=1,
                    academic_year=academic_year,
                    start_date=date(current_year, 7, 1),  # July 1st
                    end_date=date(current_year, 12, 31),  # December 31st
                    is_current=True
                )

                # Create DataFrame directly without using data manager to avoid recursion
                df = pd.DataFrame([default_semester.to_dict()])
                file_path = self.data_manager.get_file_path(self.module_name, self.semesters_filename)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(file_path, index=False, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Error initializing default semester: {e}")
            # Don't raise the error to prevent initialization failure

    def get_all_records(self) -> pd.DataFrame:
        """Get all attendance records"""
        try:
            df = self.data_manager.read_csv(
                self.module_name,
                self.records_filename,
                self.records_columns
            )
            return df
        except Exception as e:
            print(f"Error getting attendance records: {e}")
            # Return empty DataFrame with proper columns
            return pd.DataFrame(columns=self.records_columns)

    def get_current_semester_config(self) -> Optional[SemesterConfig]:
        """Get the current active semester configuration"""
        try:
            df = self.data_manager.read_csv(
                self.module_name,
                self.semesters_filename,
                self.semesters_columns
            )

            if df.empty:
                return None

            # Find current semester
            current_semesters = df[df['is_current'] == True]
            if not current_semesters.empty:
                return SemesterConfig.from_dict(current_semesters.iloc[0].to_dict())

            # If no current semester, return the most recent one
            return SemesterConfig.from_dict(df.iloc[-1].to_dict())
        except Exception as e:
            print(f"Error getting current semester config: {e}")
            return None

    def add_attendance_record(self, record: AttendanceRecord) -> bool:
        """Add a new attendance record"""
        errors = record.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        return self.data_manager.append_row(
            self.module_name,
            self.records_filename,
            record.to_dict(),
            self.records_columns
        )

    def update_attendance_record(self, record_id: int, record: AttendanceRecord) -> bool:
        """Update an existing attendance record"""
        errors = record.validate()
        if errors:
            self.data_manager.error_occurred.emit(f"Validation errors: {', '.join(errors)}")
            return False

        return self.data_manager.update_row(
            self.module_name,
            self.records_filename,
            record_id,
            record.to_dict()
        )

    def get_record_by_date(self, target_date: date) -> Optional[AttendanceRecord]:
        """Get attendance record for a specific date"""
        try:
            df = self.get_all_records()
            if df.empty:
                return None

            # Convert date column to datetime for comparison
            df['date'] = pd.to_datetime(df['date'])
            target_timestamp = pd.Timestamp(target_date)

            record_data = df[df['date'] == target_timestamp]
            if record_data.empty:
                return None

            return AttendanceRecord.from_dict(record_data.iloc[0].to_dict())
        except Exception as e:
            print(f"Error getting record by date: {e}")
            return None

    def get_or_create_record_for_date(self, target_date: date) -> AttendanceRecord:
        """Get or create attendance record for a specific date"""
        existing_record = self.get_record_by_date(target_date)

        if existing_record:
            return existing_record

        # Create new record
        current_semester = self.get_current_semester_config()

        # Validate semester - don't allow semester 8 unless it's active
        semester_number = current_semester.semester if current_semester else 1
        academic_year = current_semester.academic_year if current_semester else f"{target_date.year}-{target_date.year + 1}"

        # Additional check: if semester is 8 and not active, use semester 7 instead
        if semester_number == 8:
            try:
                # Check if semester 8 is actually active
                df = self.data_manager.read_csv(
                    self.module_name,
                    self.semesters_filename,
                    self.semesters_columns
                )
                if not df.empty:
                    semester_8_records = df[df['semester'] == 8]
                    if not semester_8_records.empty and not semester_8_records.iloc[0]['is_current']:
                        # Semester 8 exists but is not active, use semester 7
                        semester_number = 7
                        # Find semester 7 academic year
                        semester_7_records = df[df['semester'] == 7]
                        if not semester_7_records.empty:
                            academic_year = semester_7_records.iloc[0]['academic_year']
            except Exception as e:
                print(f"Warning: Error validating semester 8 status: {e}")

        new_record = AttendanceRecord(
            date=target_date,
            semester=semester_number,
            academic_year=academic_year
        )

        return new_record

    def save_attendance_record(self, record: AttendanceRecord) -> bool:
        """Save or update an attendance record"""
        try:
            existing_record = self.get_record_by_date(record.date)

            if existing_record:
                # Update existing record
                return self.update_attendance_record(existing_record.id, record)
            else:
                # Add new record
                return self.add_attendance_record(record)
        except Exception as e:
            print(f"Error saving attendance record: {e}")
            return False

    def get_semester_records(self, semester: int, academic_year: str) -> pd.DataFrame:
        """Get all records for a specific semester"""
        df = self.get_all_records()
        if df.empty:
            return df

        return df[(df['semester'] == semester) & (df['academic_year'] == academic_year)]

    def calculate_semester_attendance(self, semester: int, academic_year: str) -> Dict[str, Any]:
        """Calculate attendance statistics for a semester"""
        df = self.get_semester_records(semester, academic_year)

        if df.empty:
            return {
                'semester': semester,
                'academic_year': academic_year,
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'holiday_days': 0,
                'unofficial_leave_days': 0,
                'total_periods': 0,
                'present_periods': 0,
                'attendance_percentage': 0.0,
                'threshold_met': False,
                'threshold': 75.0
            }

        # Calculate statistics
        total_days = len(df)
        holiday_days = len(df[df['is_holiday'] == True])
        unofficial_leave_days = len(df[df['is_unofficial_leave'] == True])
        working_days = total_days - holiday_days - unofficial_leave_days

        # Calculate period-wise attendance
        working_df = df[(df['is_holiday'] == False) & (df['is_unofficial_leave'] == False)]

        if not working_df.empty:
            total_periods = working_df['total_periods'].sum()
            present_periods = working_df['present_periods'].sum()
            attendance_percentage = (present_periods / total_periods * 100) if total_periods > 0 else 0.0
        else:
            total_periods = 0
            present_periods = 0
            attendance_percentage = 0.0

        # Count present/absent days
        present_days = len(working_df[working_df['percentage'] > 0])
        absent_days = working_days - present_days

        return {
            'semester': semester,
            'academic_year': academic_year,
            'total_days': total_days,
            'working_days': working_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'holiday_days': holiday_days,
            'unofficial_leave_days': unofficial_leave_days,
            'total_periods': total_periods,
            'present_periods': present_periods,
            'attendance_percentage': attendance_percentage,
            'threshold_met': attendance_percentage >= 75.0,
            'threshold': 75.0
        }

    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """Get monthly attendance summary"""
        df = self.get_all_records()

        if df.empty:
            return {
                'year': year,
                'month': month,
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'attendance_percentage': 0.0
            }

        # Filter by month
        df['date'] = pd.to_datetime(df['date'])
        monthly_df = df[
            (df['date'].dt.year == year) &
            (df['date'].dt.month == month) &
            (df['is_holiday'] == False) &
            (df['is_unofficial_leave'] == False)
        ]

        if monthly_df.empty:
            return {
                'year': year,
                'month': month,
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'attendance_percentage': 0.0
            }

        total_periods = monthly_df['total_periods'].sum()
        present_periods = monthly_df['present_periods'].sum()
        attendance_percentage = (present_periods / total_periods * 100) if total_periods > 0 else 0.0

        present_days = len(monthly_df[monthly_df['percentage'] > 0])
        total_days = len(monthly_df)
        absent_days = total_days - present_days

        return {
            'year': year,
            'month': month,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'attendance_percentage': attendance_percentage
        }

    def get_attendance_summary(self) -> Dict[str, Any]:
        """Get overall attendance summary"""
        try:
            current_semester = self.get_current_semester_config()

            if not current_semester:
                return {
                    'current_semester': 0,
                    'current_academic_year': '',
                    'overall_percentage': 0.0,
                    'threshold_met': False,
                    'days_to_threshold': 0,
                    'total_records': 0,
                    'working_days': 0,
                    'present_periods': 0,
                    'total_periods': 0
                }

            # Get current semester statistics
            semester_stats = self.calculate_semester_attendance(
                current_semester.semester,
                current_semester.academic_year
            )

            # Calculate days needed to reach threshold
            current_percentage = semester_stats.get('attendance_percentage', 0.0)
            days_to_threshold = 0

            if current_percentage < 75.0:
                # Simple calculation - this could be more sophisticated
                total_periods = semester_stats.get('total_periods', 0)
                present_periods = semester_stats.get('present_periods', 0)

                # Calculate periods needed for 75%
                if total_periods > 0:
                    periods_needed = (total_periods * 0.75) - present_periods
                    days_to_threshold = max(0, int(periods_needed / 8))  # Assuming 8 periods per day

            return {
                'current_semester': current_semester.semester,
                'current_academic_year': current_semester.academic_year,
                'overall_percentage': current_percentage,
                'threshold_met': current_percentage >= 75.0,
                'days_to_threshold': days_to_threshold,
                'total_records': semester_stats.get('total_days', 0),
                'working_days': semester_stats.get('working_days', 0),
                'present_periods': semester_stats.get('present_periods', 0),
                'total_periods': semester_stats.get('total_periods', 0)
            }
        except Exception as e:
            print(f"Error in get_attendance_summary: {e}")
            return {
                'current_semester': 0,
                'current_academic_year': '',
                'overall_percentage': 0.0,
                'threshold_met': False,
                'days_to_threshold': 0,
                'total_records': 0,
                'working_days': 0,
                'present_periods': 0,
                'total_periods': 0
            }
