"""
Attendance tracking module for the Personal Finance Dashboard.

This module provides simplified functionality to track daily attendance
without pandas dependencies to avoid recursion issues.
"""

# Import simplified versions to avoid pandas recursion issues
from .simple_models import SimpleAttendanceDataManager, SimpleAttendanceRecord
from .simple_widgets import SimpleAttendanceTrackerWidget

# Aliases for compatibility
AttendanceDataModel = SimpleAttendanceDataManager
AttendanceRecord = SimpleAttendanceRecord
AttendanceTrackerWidget = SimpleAttendanceTrackerWidget

__all__ = [
    'AttendanceDataModel',
    'AttendanceRecord',
    'AttendanceTrackerWidget',
    'SimpleAttendanceDataManager',
    'SimpleAttendanceRecord',
    'SimpleAttendanceTrackerWidget'
]
