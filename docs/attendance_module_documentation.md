# Attendance Module Documentation

## Overview

The Attendance Module is a comprehensive attendance tracking system for the Personal Finance Dashboard application. It provides period-wise attendance marking, statistical analysis, and data persistence using CSV files.

## Features

### Core Functionality
- **Period-wise Attendance Tracking**: Track attendance for up to 8 periods per day
- **Calendar-based Date Selection**: Easy date navigation with visual calendar
- **Holiday Management**: Mark days as holidays with automatic handling
- **Statistical Analysis**: Real-time attendance percentage calculations
- **Data Persistence**: CSV-based storage with automatic backup
- **Error Handling**: Comprehensive error handling and data validation

### User Interface
- **Modern Qt-based UI**: Clean, intuitive interface using PySide6
- **Quick Actions**: One-click buttons for common operations
- **Real-time Updates**: Immediate feedback and statistics updates
- **Responsive Design**: Scrollable interface that adapts to content

## Architecture

### Module Structure
```
src/modules/attendance/
├── __init__.py                 # Module initialization and exports
├── simple_models.py           # Data models and CSV operations
├── simple_widgets.py          # UI components and widgets
├── models.py                  # Legacy models (deprecated)
└── widgets.py                 # Legacy widgets (deprecated)
```

### Key Components

#### 1. SimpleAttendanceRecord
**File**: `simple_models.py`

A dataclass representing a single day's attendance record.

**Attributes**:
- `id`: Unique record identifier
- `date`: Date in YYYY-MM-DD format
- `day`: Day of the week
- `semester`: Academic semester (1 or 2)
- `academic_year`: Academic year (e.g., "2025-2026")
- `period_1` to `period_8`: Individual period attendance ("Present", "Absent", "Holiday")
- `total_periods`: Total number of periods (default: 8)
- `present_periods`: Number of periods marked as present
- `percentage`: Attendance percentage for the day
- `is_holiday`: Boolean flag for holiday
- `is_unofficial_leave`: Boolean flag for unofficial leave
- `notes`: Additional notes for the day
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

**Methods**:
- `calculate_attendance()`: Calculates present periods and percentage
- `to_dict()`: Converts record to dictionary for CSV storage
- `from_dict(data)`: Creates record from dictionary (CSV row)

#### 2. SimpleAttendanceDataManager
**File**: `simple_models.py`

Manages CSV-based data operations for attendance records.

**Key Methods**:
- `get_all_records()`: Retrieves all attendance records
- `get_record_by_date(date)`: Gets record for specific date
- `save_record(record)`: Saves or updates a record
- `get_summary()`: Generates attendance statistics

**Features**:
- Automatic CSV file initialization
- Data validation and error handling
- Backup functionality
- Summary statistics generation

#### 3. SimpleAttendanceTrackerWidget
**File**: `simple_widgets.py`

Main UI component for attendance tracking.

**UI Sections**:
- **Date Selection**: Calendar widget with date information
- **Attendance Marking**: Period checkboxes and quick action buttons
- **Summary Display**: Real-time attendance statistics
- **Action Buttons**: Save, refresh, and other operations

## Data Storage

### CSV File Format
**Location**: `data/attendance/attendance_records.csv`

**Headers**:
```csv
id,date,day,semester,academic_year,period_1,period_2,period_3,period_4,period_5,period_6,period_7,period_8,total_periods,present_periods,percentage,is_holiday,is_unofficial_leave,notes,created_at,updated_at
```

**Example Record**:
```csv
1,2025-06-23,Monday,1,2025-2026,Present,Present,Absent,Present,Present,Present,Present,Present,8,7,87.5,false,false,Regular day,2025-06-23 10:30:00,2025-06-23 10:30:00
```

### Backup System
- Automatic backups created before major operations
- Backup files stored in `data/attendance/.backups/`
- Naming convention: `attendance_records_YYYYMMDD_HHMMSS.csv`

## Usage Guide

### Basic Operations

#### 1. Marking Attendance
1. Select date using the calendar widget
2. Check/uncheck period boxes for attendance
3. Add notes if needed
4. Click "Save Attendance"

#### 2. Quick Actions
- **Mark All Present**: Sets all periods to present
- **Mark All Absent**: Sets all periods to absent
- **Mark as Holiday**: Marks day as holiday and clears periods

#### 3. Viewing Statistics
- Summary panel shows real-time statistics
- Overall percentage calculated automatically
- Total days, present days, and absent days displayed

### Advanced Features

#### Holiday Management
- Mark days as holidays using "Mark as Holiday" button
- Holiday days don't count toward attendance percentage
- Holiday periods are automatically set to "Holiday" status

#### Data Validation
- Automatic validation of all input data
- Error handling for corrupted or invalid data
- Safe defaults applied when data is missing or invalid

## Error Handling

### Data Validation
- **Type Conversion**: Safe conversion of string data to appropriate types
- **Range Validation**: Ensures percentages are 0-100%, periods are non-negative
- **Missing Data**: Provides safe defaults for missing fields
- **Corrupted Files**: Graceful handling of corrupted CSV files

### UI Error Handling
- **Invalid Records**: Safe loading of invalid or None records
- **File Operations**: Graceful handling of file permission errors
- **User Input**: Validation of user input before saving

### Recovery Mechanisms
- **Backup Restoration**: Automatic backup creation before risky operations
- **Data Repair**: Automatic repair of minor data inconsistencies
- **Graceful Degradation**: Application continues to function even with data errors

## Integration

### Dashboard Integration
The attendance module integrates with the main dashboard through:
- **Summary Statistics**: Provides attendance percentage for dashboard display
- **Data Manager**: Uses the application's central data management system
- **Navigation**: Accessible through the main application sidebar

### Configuration
- Uses application-wide configuration system
- Respects user preferences and settings
- Integrates with logging system for debugging

## Testing

### Test Coverage
The module includes comprehensive tests for:
- **Data Operations**: CSV read/write, record management
- **Error Handling**: Invalid data, file errors, edge cases
- **UI Components**: Widget creation, user interactions
- **Integration**: Dashboard integration, data manager compatibility

### Test Files
- `test_attendance_functionality.py`: Core functionality tests
- `test_csv_operations.py`: CSV operations and data storage tests
- `test_error_handling.py`: Comprehensive error handling tests

## Migration from Legacy

### Pandas Dependency Removal
The module was rewritten to remove pandas dependencies that caused recursion issues:
- **Before**: Used pandas DataFrames for data management
- **After**: Uses native Python data structures and CSV operations
- **Benefits**: Eliminated recursion errors, improved performance, reduced dependencies

### Compatibility
- Maintains API compatibility with existing code
- Provides aliases for legacy class names
- Seamless migration path from old implementation

## Performance Considerations

### Optimization Features
- **Lazy Loading**: Records loaded only when needed
- **Efficient CSV Operations**: Minimal file I/O operations
- **Memory Management**: Efficient data structures for large datasets
- **Caching**: Summary statistics cached for performance

### Scalability
- Handles thousands of attendance records efficiently
- CSV format allows easy data export and analysis
- Minimal memory footprint for large datasets

## Troubleshooting

### Common Issues

#### 1. CSV File Corruption
**Symptoms**: Error loading attendance data
**Solution**: Check backup files in `.backups/` directory

#### 2. Permission Errors
**Symptoms**: Cannot save attendance records
**Solution**: Ensure write permissions for `data/attendance/` directory

#### 3. Invalid Data
**Symptoms**: Incorrect attendance calculations
**Solution**: Module automatically repairs invalid data with safe defaults

### Debugging
- Enable debug logging for detailed operation logs
- Check console output for warning messages
- Use test scripts to verify functionality

## Future Enhancements

### Planned Features
- **Export Functionality**: Export data to Excel, PDF formats
- **Advanced Analytics**: Trend analysis, pattern recognition
- **Semester Management**: Better semester and academic year handling
- **Bulk Operations**: Import/export of multiple records

### API Extensions
- REST API for external integrations
- Plugin system for custom attendance rules
- Advanced reporting capabilities

## Support

For issues or questions regarding the attendance module:
1. Check the troubleshooting section above
2. Run the test scripts to verify functionality
3. Check application logs for error details
4. Review the source code documentation
