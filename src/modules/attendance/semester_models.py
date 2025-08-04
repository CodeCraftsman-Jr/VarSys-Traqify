"""
Semester Management Models for B.Tech Attendance System
Handles 8-semester system with proper date management
"""

import os
import csv
import json
import logging
from datetime import datetime, date, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class SemesterInfo:
    """Information about a B.Tech semester"""
    semester_number: int = 1  # 1-8
    academic_year: str = ""  # e.g., "2024-2025"
    start_date: str = ""  # ISO format date
    end_date: str = ""  # ISO format date
    year: int = 1  # 1-4 (which year of B.Tech)
    semester_type: str = "Odd"  # "Odd" or "Even"
    total_working_days: int = 0
    holidays: List[str] = None  # List of holiday dates
    is_active: bool = False
    created_at: str = ""
    
    def __post_init__(self):
        """Post-initialization processing"""
        if self.holidays is None:
            self.holidays = []
        
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        
        # Auto-calculate semester type and year
        if self.semester_number:
            self.year = ((self.semester_number - 1) // 2) + 1
            self.semester_type = "Odd" if self.semester_number % 2 == 1 else "Even"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemesterInfo':
        """Create from dictionary"""
        return cls(**data)
    
    def is_date_in_semester(self, check_date: date) -> bool:
        """Check if a date falls within this semester"""
        try:
            start = datetime.strptime(self.start_date, '%Y-%m-%d').date()
            end = datetime.strptime(self.end_date, '%Y-%m-%d').date()
            return start <= check_date <= end
        except ValueError:
            return False
    
    def get_working_days(self) -> int:
        """Calculate total working days (excluding weekends and holidays)"""
        try:
            start = datetime.strptime(self.start_date, '%Y-%m-%d').date()
            end = datetime.strptime(self.end_date, '%Y-%m-%d').date()
            
            working_days = 0
            current_date = start
            
            holiday_dates = set()
            for holiday_str in self.holidays:
                try:
                    holiday_date = datetime.strptime(holiday_str, '%Y-%m-%d').date()
                    holiday_dates.add(holiday_date)
                except ValueError:
                    continue
            
            while current_date <= end:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:  # Monday=0 to Friday=4
                    # Skip holidays
                    if current_date not in holiday_dates:
                        working_days += 1
                current_date += timedelta(days=1)
            
            return working_days
            
        except ValueError:
            return 0
    
    def get_semester_name(self) -> str:
        """Get human-readable semester name"""
        year_names = {1: "First", 2: "Second", 3: "Third", 4: "Fourth"}
        year_name = year_names.get(self.year, f"Year {self.year}")
        return f"{year_name} Year - {self.semester_type} Semester"


class SemesterManager:
    """Manages B.Tech semester information"""
    
    def __init__(self, data_dir: str, config=None):
        self.data_dir = Path(data_dir)
        self.attendance_dir = self.data_dir / "attendance"
        self.semesters_file = self.attendance_dir / "semesters.json"
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Ensure directory exists
        os.makedirs(self.attendance_dir, exist_ok=True)

        # Initialize with default semesters if file doesn't exist
        if not self.semesters_file.exists():
            self._create_default_semesters()
    
    def _create_default_semesters(self):
        """Create default B.Tech semester structure"""
        # Use college joining year from config, fallback to current year
        if self.config and hasattr(self.config, 'college_joining_year'):
            college_start_year = self.config.college_joining_year
        else:
            college_start_year = datetime.now().year
        
        # Create 8 semesters for a typical B.Tech program
        default_semesters = []
        
        for sem_num in range(1, 9):
            year = ((sem_num - 1) // 2) + 1  # 1-4
            is_odd = sem_num % 2 == 1
            
            # Calculate academic year based on college joining year
            if year == 1:
                academic_year = f"{college_start_year}-{college_start_year + 1}"
                if is_odd:
                    start_month, end_month = 7, 12  # July to December
                    start_year, end_year = college_start_year, college_start_year
                else:
                    start_month, end_month = 1, 6   # January to June
                    start_year, end_year = college_start_year + 1, college_start_year + 1
            else:
                base_year = college_start_year + year - 1
                academic_year = f"{base_year}-{base_year + 1}"
                if is_odd:
                    start_month, end_month = 7, 12
                    start_year, end_year = base_year, base_year
                else:
                    start_month, end_month = 1, 6
                    start_year, end_year = base_year + 1, base_year + 1
            
            # Create semester dates
            start_date = date(start_year, start_month, 1)
            if end_month == 12:
                end_date = date(end_year, 12, 31)
            else:
                end_date = date(end_year, 6, 30)
            
            semester = SemesterInfo(
                semester_number=sem_num,
                academic_year=academic_year,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                is_active=(sem_num == 1)  # First semester active by default
            )
            
            default_semesters.append(semester.to_dict())
        
        # Save to file
        try:
            with open(self.semesters_file, 'w', encoding='utf-8') as f:
                json.dump(default_semesters, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Created default semesters: {self.semesters_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating default semesters: {e}")
    
    def get_all_semesters(self) -> List[SemesterInfo]:
        """Get all semester information"""
        try:
            if not self.semesters_file.exists():
                return []
            
            with open(self.semesters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return [SemesterInfo.from_dict(sem_data) for sem_data in data]
            
        except Exception as e:
            self.logger.error(f"Error loading semesters: {e}")
            return []
    
    def get_semester_by_number(self, semester_number: int) -> Optional[SemesterInfo]:
        """Get semester by number (1-8)"""
        semesters = self.get_all_semesters()
        for semester in semesters:
            if semester.semester_number == semester_number:
                return semester
        return None
    
    def get_active_semester(self) -> Optional[SemesterInfo]:
        """Get the currently active semester"""
        semesters = self.get_all_semesters()
        for semester in semesters:
            if semester.is_active:
                return semester
        return None
    
    def get_semester_for_date(self, check_date: date) -> Optional[SemesterInfo]:
        """Get the semester that contains the given date"""
        semesters = self.get_all_semesters()
        for semester in semesters:
            if semester.is_date_in_semester(check_date):
                return semester
        return None
    
    def set_active_semester(self, semester_number: int) -> bool:
        """Set a semester as active (deactivates others)"""
        try:
            semesters = self.get_all_semesters()
            
            # Deactivate all semesters
            for semester in semesters:
                semester.is_active = False
            
            # Activate the specified semester
            for semester in semesters:
                if semester.semester_number == semester_number:
                    semester.is_active = True
                    break
            
            # Save changes
            return self.save_semesters(semesters)
            
        except Exception as e:
            self.logger.error(f"Error setting active semester: {e}")
            return False
    
    def update_semester(self, semester_info: SemesterInfo) -> bool:
        """Update semester information"""
        try:
            semesters = self.get_all_semesters()
            
            # Find and update the semester
            for i, semester in enumerate(semesters):
                if semester.semester_number == semester_info.semester_number:
                    semesters[i] = semester_info
                    break
            else:
                # Add new semester if not found
                semesters.append(semester_info)
            
            return self.save_semesters(semesters)
            
        except Exception as e:
            self.logger.error(f"Error updating semester: {e}")
            return False
    
    def save_semesters(self, semesters: List[SemesterInfo]) -> bool:
        """Save semester information to file"""
        try:
            semester_data = [sem.to_dict() for sem in semesters]
            
            with open(self.semesters_file, 'w', encoding='utf-8') as f:
                json.dump(semester_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(semesters)} semesters")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving semesters: {e}")
            return False
    
    def get_semester_summary(self, semester_number: int) -> Dict[str, Any]:
        """Get attendance summary for a specific semester"""
        try:
            from .simple_models import SimpleAttendanceDataManager

            semester = self.get_semester_by_number(semester_number)
            if not semester:
                return {}

            # Get attendance records for this semester
            attendance_manager = SimpleAttendanceDataManager(str(self.data_dir))
            all_records = attendance_manager.get_all_records()

            # Filter records for this semester - USE SEMESTER FIELD, NOT DATE RANGE
            semester_records = []
            for record in all_records:
                # Filter by actual semester field in the record, not by date range
                if record.semester == semester_number:
                    semester_records.append(record)
            
            # Calculate statistics properly
            # Get theoretical working days from semester dates (excluding weekends and holidays)
            total_working_days = semester.get_working_days()

            # Get actual attendance data
            holiday_records = [r for r in semester_records if r.is_holiday]
            non_holiday_records = [r for r in semester_records if not r.is_holiday]

            # Calculate attendance statistics
            total_attendance_days = len(non_holiday_records)  # Days with attendance records
            present_days = len([r for r in non_holiday_records if r.present_periods > 0])
            absent_days = len([r for r in non_holiday_records if r.present_periods == 0])
            holiday_days = len(holiday_records)

            # Calculate percentage based on period attendance (more accurate)
            total_periods = sum(r.total_periods for r in non_holiday_records)
            present_periods = sum(r.present_periods for r in non_holiday_records)

            # Use period-based percentage for more accuracy
            if total_periods > 0:
                percentage = (present_periods / total_periods) * 100
            else:
                percentage = 0.0
            
            return {
                'semester_number': semester_number,
                'semester_name': semester.get_semester_name(),
                'academic_year': semester.academic_year,
                'start_date': semester.start_date,
                'end_date': semester.end_date,
                'total_working_days': total_working_days,  # Theoretical working days
                'total_days': total_attendance_days,       # Days with attendance records
                'present_days': present_days,
                'absent_days': absent_days,
                'holiday_days': holiday_days,
                'attendance_percentage': round(percentage, 2),
                'total_periods': total_periods,            # Total periods in recorded days
                'present_periods': present_periods,        # Present periods
                'is_active': semester.is_active
            }
            
        except Exception as e:
            self.logger.error(f"Error getting semester summary: {e}")
            return {}
