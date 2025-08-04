# Holiday Management System

## Overview

The Holiday Management System is a comprehensive solution for automatically managing holidays in the Personal Finance Dashboard. It integrates with the Calendarific API to fetch official holidays and automatically applies them to the attendance tracking system.

## Features

### 🌟 **Core Features**
- **Calendarific API Integration**: Fetch official holidays from 200+ countries
- **Automatic Attendance Integration**: Holidays are automatically marked in the attendance system
- **Country Selection**: Support for multiple countries (IN, US, GB, CA, AU, DE, FR, JP, CN, BR)
- **Year Selection**: Fetch holidays for any year from 2020-2030
- **Holiday Types**: National, local, religious, and observance holidays
- **Selective Application**: Choose which holidays to apply to your attendance

### 🔧 **Technical Features**
- **Background Processing**: API calls run in separate threads to prevent UI freezing
- **Error Handling**: Comprehensive error handling for network issues and API errors
- **Data Persistence**: Holidays are saved locally for future reference
- **Progress Tracking**: Real-time progress indicators during API calls
- **Fallback Support**: Graceful handling of API failures

## Usage Guide

### Accessing Holiday Management

1. **Open Settings**: Go to `Tools` → `Settings` in the main menu
2. **Holiday Management Tab**: Click on the "Holiday Management" tab
3. **Configure API**: Enter your Calendarific API key (pre-configured: `2tMHledxFxWgwyLdX1t5qxnp4uHDZOQL`)

### Fetching Holidays

1. **Select Country**: Choose your country from the dropdown (default: India)
2. **Select Year**: Choose the year for which you want holidays (default: current year)
3. **Fetch Holidays**: Click "Fetch Holidays" to retrieve data from the API
4. **Wait for Results**: Monitor the progress bar during the fetch process

### Applying Holidays

1. **Review Holidays**: Browse the fetched holidays in the table
2. **Select Holidays**: Use checkboxes to select which holidays to apply
   - **Select All**: Click "Select All" to choose all holidays
   - **Deselect All**: Click "Deselect All" to clear all selections
3. **Apply to Attendance**: Click "Apply Selected Holidays" to integrate with attendance system

### Holiday Data

Each holiday entry contains:
- **Date**: ISO format date (YYYY-MM-DD)
- **Name**: Official holiday name
- **Type**: Holiday category (national, local, religious, observance)
- **Description**: Additional details about the holiday

## API Integration

### Calendarific API

The system uses the Calendarific API (https://calendarific.com/) which provides:
- **200+ Countries**: Comprehensive global holiday coverage
- **Multiple Types**: National, local, religious, and observance holidays
- **Reliable Data**: Official government sources
- **JSON Format**: Easy to parse and integrate

### API Configuration

```python
# API Endpoint
url = "https://calendarific.com/api/v2/holidays"

# Parameters
params = {
    'api_key': 'your_api_key_here',
    'country': 'IN',  # Country code
    'year': 2024,     # Year
    'type': 'national,local,religious,observance'
}
```

### Free Tier Limitations

- **1000 requests/month**: Sufficient for typical usage
- **Rate Limiting**: Automatic handling of rate limits
- **Caching**: Local storage reduces API calls

## Attendance Integration

### Automatic Application

When holidays are applied:
1. **Record Creation**: Creates attendance records for each holiday date
2. **Period Marking**: All 8 periods marked as "Holiday"
3. **Holiday Flag**: Sets `is_holiday = True` for the record
4. **Notes Addition**: Adds holiday name to the notes field
5. **Semester Assignment**: Uses default semester (configurable)

### Record Structure

```python
holiday_record = SimpleAttendanceRecord(
    date="2024-01-26",
    day="Friday",
    semester=1,
    academic_year="2024-2025",
    notes="Holiday: Republic Day",
    is_holiday=True,
    period_1="Holiday",
    period_2="Holiday",
    # ... all periods marked as Holiday
)
```

## Data Storage

### Local Storage

- **Location**: `data/holidays.json`
- **Format**: JSON array of holiday objects
- **Backup**: Automatic backup with attendance data
- **Persistence**: Holidays saved for future reference

### Data Structure

```json
[
  {
    "date": "2024-01-26",
    "name": "Republic Day"
  },
  {
    "date": "2024-08-15",
    "name": "Independence Day"
  }
]
```

## Error Handling

### Network Errors
- **Timeout Handling**: 10-second timeout for API calls
- **Connection Issues**: Graceful handling of network failures
- **Retry Logic**: User can manually retry failed requests

### API Errors
- **Invalid API Key**: Clear error message for authentication issues
- **Rate Limiting**: Automatic detection and user notification
- **Invalid Parameters**: Validation before API calls

### Data Errors
- **Malformed Responses**: Safe parsing with fallbacks
- **Missing Fields**: Default values for incomplete data
- **Date Parsing**: Robust date handling with validation

## Troubleshooting

### Common Issues

1. **API Key Invalid**
   - **Solution**: Verify API key in settings
   - **Check**: Visit Calendarific.com to validate key

2. **No Holidays Fetched**
   - **Solution**: Check internet connection
   - **Verify**: Country code and year selection

3. **Holidays Not Applied**
   - **Solution**: Ensure holidays are selected before applying
   - **Check**: Attendance module is functioning

4. **Network Timeout**
   - **Solution**: Check internet connection
   - **Retry**: Use the fetch button again

### Debug Information

Enable debug logging to see detailed information:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Google Calendar Integration**: Alternative API source
- **Custom Holiday Addition**: Manual holiday entry
- **Holiday Categories**: Filter by holiday types
- **Multi-Year Fetch**: Bulk holiday retrieval
- **Holiday Notifications**: Upcoming holiday alerts

### API Alternatives
- **Google Calendar API**: Backup holiday source
- **TimeAndDate.com API**: Additional holiday provider
- **Local Holiday Files**: Offline holiday data

## Security Considerations

### API Key Management
- **Environment Variables**: Store API keys securely
- **Key Rotation**: Regular API key updates
- **Access Control**: Limit API key permissions

### Data Privacy
- **Local Storage**: Holiday data stored locally
- **No Personal Data**: Only public holiday information
- **Secure Transmission**: HTTPS for all API calls

## Support

### Getting Help
- **Documentation**: Refer to this guide
- **Logs**: Check application logs for errors
- **API Documentation**: Visit Calendarific.com for API details

### Reporting Issues
- **Error Messages**: Include full error messages
- **Steps to Reproduce**: Detailed reproduction steps
- **System Information**: OS, Python version, etc.

---

**Note**: The Holiday Management System is designed to work seamlessly with the existing attendance tracking system. All holidays are automatically integrated and can be viewed in the attendance records tab.
