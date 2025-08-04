"""
Attendance Analytics Utilities
Provides data processing functions for attendance analytics calculations and statistics
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AttendanceAnalytics:
    """Data class for attendance analytics results"""
    total_days: int = 0
    working_days: int = 0
    present_days: int = 0
    absent_days: int = 0
    overall_attendance_rate: float = 0.0
    current_month_rate: float = 0.0
    current_week_rate: float = 0.0
    total_periods: int = 0
    present_periods: int = 0
    period_wise_stats: Dict[str, Any] = None
    monthly_breakdown: Dict[str, Any] = None
    semester_performance: List[Dict[str, Any]] = None
    time_patterns: Dict[str, Any] = None
    attendance_trends: Dict[str, Any] = None


def calculate_attendance_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive attendance statistics"""
    if data.empty:
        return _get_empty_stats()
    
    # Ensure date column is datetime
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    
    stats = {}
    
    # Basic statistics
    stats['total_records'] = len(data)
    stats['total_days'] = data['date'].nunique()
    
    # Filter working days (exclude holidays and unofficial leaves)
    working_data = data[(data['is_holiday'] == False) & (data['is_unofficial_leave'] == False)]
    stats['working_days'] = len(working_data)
    
    if working_data.empty:
        return _get_empty_stats()
    
    # Attendance calculations
    stats['present_days'] = len(working_data[working_data['percentage'] > 0])
    stats['absent_days'] = len(working_data[working_data['percentage'] == 0])
    stats['full_attendance_days'] = len(working_data[working_data['percentage'] == 100.0])
    stats['partial_attendance_days'] = len(working_data[(working_data['percentage'] > 0) & (working_data['percentage'] < 100.0)])
    
    # Overall attendance rate
    stats['overall_attendance_rate'] = float(working_data['percentage'].mean()) if len(working_data) > 0 else 0.0
    
    # Period-wise statistics
    stats['total_periods'] = int(working_data['total_periods'].sum())
    stats['present_periods'] = int(working_data['present_periods'].sum())
    stats['period_attendance_rate'] = float((stats['present_periods'] / stats['total_periods']) * 100) if stats['total_periods'] > 0 else 0.0
    
    # Date range statistics
    stats['date_range'] = {
        'start_date': data['date'].min().strftime('%Y-%m-%d'),
        'end_date': data['date'].max().strftime('%Y-%m-%d'),
        'total_span_days': (data['date'].max() - data['date'].min()).days + 1
    }
    
    # Current month statistics
    current_month = pd.Timestamp.now().to_period('M')
    current_month_data = working_data[working_data['date'].dt.to_period('M') == current_month]
    stats['current_month'] = {
        'total_days': len(current_month_data),
        'present_days': len(current_month_data[current_month_data['percentage'] > 0]),
        'attendance_rate': float(current_month_data['percentage'].mean()) if len(current_month_data) > 0 else 0.0,
        'total_periods': int(current_month_data['total_periods'].sum()) if len(current_month_data) > 0 else 0,
        'present_periods': int(current_month_data['present_periods'].sum()) if len(current_month_data) > 0 else 0
    }
    
    # Current week statistics
    today = pd.Timestamp.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    current_week_data = working_data[
        (working_data['date'].dt.date >= week_start) & 
        (working_data['date'].dt.date <= week_end)
    ]
    stats['current_week'] = {
        'total_days': len(current_week_data),
        'present_days': len(current_week_data[current_week_data['percentage'] > 0]),
        'attendance_rate': float(current_week_data['percentage'].mean()) if len(current_week_data) > 0 else 0.0,
        'total_periods': int(current_week_data['total_periods'].sum()) if len(current_week_data) > 0 else 0,
        'present_periods': int(current_week_data['present_periods'].sum()) if len(current_week_data) > 0 else 0
    }
    
    # Period-wise analysis
    stats['period_wise'] = calculate_period_wise_statistics(working_data)
    
    # Monthly breakdown
    stats['monthly_breakdown'] = calculate_monthly_breakdown(working_data)
    
    # Semester analysis
    if 'semester' in data.columns and 'academic_year' in data.columns:
        stats['semester_analysis'] = calculate_semester_statistics(working_data)
    
    # Time pattern analysis
    stats['time_patterns'] = calculate_time_patterns(working_data)
    
    # Attendance trends
    stats['attendance_trends'] = calculate_attendance_trends(working_data)
    
    # Performance indicators
    stats['performance_indicators'] = calculate_performance_indicators(working_data)
    
    return stats


def calculate_period_wise_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics for each period"""
    if data.empty:
        return {}
    
    period_stats = {}
    
    for period in range(1, 9):
        period_col = f'period_{period}'
        if period_col in data.columns:
            period_data = data[data[period_col].notna()]
            
            if not period_data.empty:
                present_count = len(period_data[period_data[period_col] == 'Present'])
                total_count = len(period_data)
                attendance_rate = (present_count / total_count * 100) if total_count > 0 else 0
                
                period_stats[f'period_{period}'] = {
                    'present_days': present_count,
                    'total_days': total_count,
                    'attendance_rate': float(attendance_rate),
                    'absent_days': total_count - present_count
                }
    
    return period_stats


def calculate_monthly_breakdown(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate monthly attendance breakdown"""
    if data.empty:
        return {}
    
    data_copy = data.copy()
    data_copy['month_year'] = data_copy['date'].dt.strftime('%Y-%m')
    
    monthly_stats = {}
    
    for month_year in data_copy['month_year'].unique():
        month_data = data_copy[data_copy['month_year'] == month_year]
        
        monthly_stats[month_year] = {
            'total_days': len(month_data),
            'present_days': len(month_data[month_data['percentage'] > 0]),
            'absent_days': len(month_data[month_data['percentage'] == 0]),
            'full_attendance_days': len(month_data[month_data['percentage'] == 100.0]),
            'partial_attendance_days': len(month_data[(month_data['percentage'] > 0) & (month_data['percentage'] < 100.0)]),
            'average_attendance': float(month_data['percentage'].mean()),
            'total_periods': int(month_data['total_periods'].sum()),
            'present_periods': int(month_data['present_periods'].sum())
        }
    
    return monthly_stats


def calculate_semester_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate semester-wise attendance statistics"""
    if data.empty or 'semester' not in data.columns or 'academic_year' not in data.columns:
        return {}
    
    semester_stats = {}
    
    # Group by semester and academic year
    grouped = data.groupby(['semester', 'academic_year'])
    
    for (semester, year), semester_data in grouped:
        semester_key = f"Semester_{semester}_{year}"
        
        semester_stats[semester_key] = {
            'semester': semester,
            'academic_year': year,
            'total_days': len(semester_data),
            'present_days': len(semester_data[semester_data['percentage'] > 0]),
            'absent_days': len(semester_data[semester_data['percentage'] == 0]),
            'average_attendance': float(semester_data['percentage'].mean()),
            'total_periods': int(semester_data['total_periods'].sum()),
            'present_periods': int(semester_data['present_periods'].sum()),
            'period_attendance_rate': float((semester_data['present_periods'].sum() / semester_data['total_periods'].sum()) * 100) if semester_data['total_periods'].sum() > 0 else 0.0
        }
    
    return semester_stats


def calculate_time_patterns(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate time-based attendance patterns"""
    if data.empty:
        return {}
    
    data_copy = data.copy()
    data_copy['weekday'] = data_copy['date'].dt.day_name()
    data_copy['month'] = data_copy['date'].dt.month_name()
    data_copy['day_of_month'] = data_copy['date'].dt.day
    
    patterns = {}
    
    # Weekday patterns
    weekday_stats = data_copy.groupby('weekday').agg({
        'percentage': ['count', 'mean', 'sum'],
        'present_periods': 'sum',
        'total_periods': 'sum'
    }).round(2)
    
    weekday_stats.columns = ['total_days', 'avg_attendance', 'total_attendance', 'present_periods', 'total_periods']
    
    # Reorder weekdays
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_stats = weekday_stats.reindex(weekday_order, fill_value=0)
    
    patterns['weekday'] = weekday_stats.to_dict('index')
    
    # Monthly patterns
    if len(data_copy['month'].unique()) > 1:
        monthly_stats = data_copy.groupby('month').agg({
            'percentage': ['count', 'mean'],
            'present_periods': 'sum',
            'total_periods': 'sum'
        }).round(2)
        
        monthly_stats.columns = ['total_days', 'avg_attendance', 'present_periods', 'total_periods']
        patterns['monthly'] = monthly_stats.to_dict('index')
    
    # Day of month patterns
    day_stats = data_copy.groupby('day_of_month')['percentage'].mean().round(2)
    patterns['day_of_month'] = day_stats.to_dict()
    
    return patterns


def calculate_attendance_trends(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate attendance trends over time"""
    if data.empty:
        return {}
    
    data_copy = data.copy()
    data_copy = data_copy.sort_values('date')
    
    trends = {}
    
    # Weekly trends
    data_copy['week'] = data_copy['date'].dt.to_period('W')
    weekly_trends = data_copy.groupby('week')['percentage'].mean().round(2)
    trends['weekly'] = {
        'dates': [str(week) for week in weekly_trends.index],
        'attendance_rates': weekly_trends.values.tolist()
    }
    
    # Monthly trends
    data_copy['month'] = data_copy['date'].dt.to_period('M')
    monthly_trends = data_copy.groupby('month')['percentage'].mean().round(2)
    trends['monthly'] = {
        'dates': [str(month) for month in monthly_trends.index],
        'attendance_rates': monthly_trends.values.tolist()
    }
    
    # Calculate trend direction
    if len(monthly_trends) >= 2:
        recent_avg = monthly_trends.tail(3).mean()
        earlier_avg = monthly_trends.head(3).mean()
        trend_direction = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
        trends['trend_direction'] = trend_direction
        trends['trend_change'] = float(recent_avg - earlier_avg)
    
    return trends


def calculate_performance_indicators(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate key performance indicators"""
    if data.empty:
        return {}
    
    indicators = {}
    
    # Attendance consistency (standard deviation)
    indicators['consistency'] = {
        'std_deviation': float(data['percentage'].std()),
        'coefficient_of_variation': float(data['percentage'].std() / data['percentage'].mean() * 100) if data['percentage'].mean() > 0 else 0
    }
    
    # Attendance categories
    total_days = len(data)
    indicators['categories'] = {
        'excellent_days': len(data[data['percentage'] >= 90]),  # 90%+ attendance
        'good_days': len(data[(data['percentage'] >= 75) & (data['percentage'] < 90)]),  # 75-89%
        'poor_days': len(data[(data['percentage'] > 0) & (data['percentage'] < 75)]),  # 1-74%
        'absent_days': len(data[data['percentage'] == 0])  # 0%
    }
    
    # Calculate percentages
    categories_copy = dict(indicators['categories'])
    for category in categories_copy:
        indicators['categories'][f'{category}_percentage'] = float((indicators['categories'][category] / total_days) * 100)
    
    # Minimum attendance requirement check (75%)
    indicators['meets_minimum'] = {
        'overall_rate': float(data['percentage'].mean()),
        'meets_75_percent': data['percentage'].mean() >= 75.0,
        'days_below_75': len(data[data['percentage'] < 75.0]),
        'consecutive_absences': _calculate_max_consecutive_absences(data)
    }
    
    return indicators


def _calculate_max_consecutive_absences(data: pd.DataFrame) -> int:
    """Calculate maximum consecutive absences"""
    if data.empty:
        return 0
    
    data_sorted = data.sort_values('date')
    max_consecutive = 0
    current_consecutive = 0
    
    for _, row in data_sorted.iterrows():
        if row['percentage'] == 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive


def get_attendance_insights(data: pd.DataFrame) -> List[str]:
    """Generate insights and recommendations based on attendance data"""
    if data.empty:
        return ["No attendance data available for analysis."]
    
    insights = []
    stats = calculate_attendance_statistics(data)
    
    # Overall performance insights
    overall_rate = stats.get('overall_attendance_rate', 0)
    if overall_rate >= 90:
        insights.append(f"🎉 Excellent attendance! You're maintaining a {overall_rate:.1f}% attendance rate.")
    elif overall_rate >= 75:
        insights.append(f"👍 Good attendance with {overall_rate:.1f}% rate. You meet the minimum requirement!")
    else:
        insights.append(f"⚠️ Your attendance rate is {overall_rate:.1f}%. You need to improve to meet the 75% requirement.")
    
    # Period-wise insights
    period_stats = stats.get('period_wise', {})
    if period_stats:
        best_period = max(period_stats.keys(), key=lambda k: period_stats[k].get('attendance_rate', 0))
        worst_period = min(period_stats.keys(), key=lambda k: period_stats[k].get('attendance_rate', 0))
        
        best_rate = period_stats[best_period].get('attendance_rate', 0)
        worst_rate = period_stats[worst_period].get('attendance_rate', 0)
        
        if best_rate - worst_rate > 20:
            insights.append(f"📊 {best_period.replace('_', ' ').title()} is your strongest period ({best_rate:.1f}%), while {worst_period.replace('_', ' ').title()} needs attention ({worst_rate:.1f}%).")
    
    # Time pattern insights
    time_patterns = stats.get('time_patterns', {})
    weekday_patterns = time_patterns.get('weekday', {})
    
    if weekday_patterns:
        best_day = max(weekday_patterns.keys(), key=lambda k: weekday_patterns[k].get('avg_attendance', 0))
        worst_day = min(weekday_patterns.keys(), key=lambda k: weekday_patterns[k].get('avg_attendance', 0))
        
        best_day_rate = weekday_patterns[best_day].get('avg_attendance', 0)
        worst_day_rate = weekday_patterns[worst_day].get('avg_attendance', 0)
        
        if best_day_rate - worst_day_rate > 15:
            insights.append(f"📅 {best_day} is your best attendance day ({best_day_rate:.1f}%), while {worst_day} shows lower attendance ({worst_day_rate:.1f}%).")
    
    # Trend insights
    trends = stats.get('attendance_trends', {})
    trend_direction = trends.get('trend_direction', 'stable')
    
    if trend_direction == 'improving':
        insights.append("📈 Great news! Your attendance trend is improving over time.")
    elif trend_direction == 'declining':
        insights.append("📉 Your attendance trend is declining. Consider strategies to improve consistency.")
    
    # Performance indicators
    performance = stats.get('performance_indicators', {})
    meets_minimum = performance.get('meets_minimum', {})
    
    if not meets_minimum.get('meets_75_percent', False):
        days_below = meets_minimum.get('days_below_75', 0)
        insights.append(f"🎯 Focus on improvement: You have {days_below} days below 75% attendance. Consistency is key!")
    
    consecutive_absences = meets_minimum.get('consecutive_absences', 0)
    if consecutive_absences >= 3:
        insights.append(f"⚠️ You had {consecutive_absences} consecutive absences. Try to maintain regular attendance.")
    
    return insights


def _get_empty_stats() -> Dict[str, Any]:
    """Return empty statistics structure"""
    return {
        'total_records': 0,
        'total_days': 0,
        'working_days': 0,
        'present_days': 0,
        'absent_days': 0,
        'overall_attendance_rate': 0.0,
        'total_periods': 0,
        'present_periods': 0,
        'period_attendance_rate': 0.0,
        'date_range': {'start_date': '', 'end_date': '', 'total_span_days': 0},
        'current_month': {'total_days': 0, 'present_days': 0, 'attendance_rate': 0.0},
        'current_week': {'total_days': 0, 'present_days': 0, 'attendance_rate': 0.0},
        'period_wise': {},
        'monthly_breakdown': {},
        'semester_analysis': {},
        'time_patterns': {},
        'attendance_trends': {},
        'performance_indicators': {}
    }
