"""
Habit Analytics Utilities
Provides data processing functions for habit analytics calculations and statistics
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class HabitAnalytics:
    """Data class for habit analytics results"""
    total_habits: int = 0
    total_records: int = 0
    overall_completion_rate: float = 0.0
    best_streak: int = 0
    current_streak: int = 0
    habits_completed_today: int = 0
    habits_total_today: int = 0
    today_completion_rate: float = 0.0
    weekly_completion_rate: float = 0.0
    monthly_completion_rate: float = 0.0
    category_breakdown: Dict[str, Any] = None
    habit_performance: List[Dict[str, Any]] = None
    streak_analysis: Dict[str, Any] = None
    time_patterns: Dict[str, Any] = None


def calculate_habit_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive habit statistics"""
    if data.empty:
        return _get_empty_stats()
    
    # Ensure date column is datetime
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    
    stats = {}
    
    # Basic statistics
    stats['total_records'] = len(data)
    stats['total_habits'] = data['habit_name'].nunique()
    stats['total_completions'] = len(data[data['is_completed'] == True])
    stats['overall_completion_rate'] = float((stats['total_completions'] / stats['total_records']) * 100) if stats['total_records'] > 0 else 0.0
    
    # Date range statistics
    stats['date_range'] = {
        'start_date': data['date'].min().strftime('%Y-%m-%d'),
        'end_date': data['date'].max().strftime('%Y-%m-%d'),
        'total_days': (data['date'].max() - data['date'].min()).days + 1
    }
    
    # Today's statistics
    today = pd.Timestamp.now().date()
    today_data = data[data['date'].dt.date == today]
    stats['today'] = {
        'total_habits': len(today_data),
        'completed_habits': len(today_data[today_data['is_completed'] == True]),
        'completion_rate': float((len(today_data[today_data['is_completed'] == True]) / len(today_data)) * 100) if len(today_data) > 0 else 0.0
    }
    
    # Weekly statistics
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_data = data[(data['date'].dt.date >= week_start) & (data['date'].dt.date <= week_end)]
    stats['this_week'] = {
        'total_records': len(week_data),
        'completed_records': len(week_data[week_data['is_completed'] == True]),
        'completion_rate': float((len(week_data[week_data['is_completed'] == True]) / len(week_data)) * 100) if len(week_data) > 0 else 0.0
    }
    
    # Monthly statistics
    month_start = today.replace(day=1)
    month_data = data[data['date'].dt.date >= month_start]
    stats['this_month'] = {
        'total_records': len(month_data),
        'completed_records': len(month_data[month_data['is_completed'] == True]),
        'completion_rate': float((len(month_data[month_data['is_completed'] == True]) / len(month_data)) * 100) if len(month_data) > 0 else 0.0
    }
    
    # Streak analysis
    stats['streaks'] = calculate_streak_statistics(data)
    
    # Category analysis
    if 'category' in data.columns:
        stats['categories'] = calculate_category_statistics(data)
    
    # Time pattern analysis
    stats['time_patterns'] = calculate_time_patterns(data)
    
    # Habit performance ranking
    stats['habit_performance'] = calculate_habit_performance(data)
    
    return stats


def calculate_streak_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate streak statistics for all habits"""
    if data.empty:
        return {}
    
    streak_stats = {
        'overall_best_streak': 0,
        'overall_current_streak': 0,
        'habit_streaks': {},
        'streak_distribution': {}
    }
    
    # Calculate streaks for each habit
    for habit_name in data['habit_name'].unique():
        habit_data = data[data['habit_name'] == habit_name].sort_values('date')
        
        current_streak = 0
        best_streak = 0
        temp_streak = 0
        
        # Calculate best streak
        for _, record in habit_data.iterrows():
            if record['is_completed']:
                temp_streak += 1
                best_streak = max(best_streak, temp_streak)
            else:
                temp_streak = 0
        
        # Calculate current streak (from most recent data)
        recent_data = habit_data.tail(30).sort_values('date', ascending=False)
        for _, record in recent_data.iterrows():
            if record['is_completed']:
                current_streak += 1
            else:
                break
        
        streak_stats['habit_streaks'][habit_name] = {
            'current_streak': current_streak,
            'best_streak': best_streak
        }
        
        # Update overall stats
        streak_stats['overall_best_streak'] = max(streak_stats['overall_best_streak'], best_streak)
        streak_stats['overall_current_streak'] = max(streak_stats['overall_current_streak'], current_streak)
    
    # Streak distribution
    all_streaks = [info['best_streak'] for info in streak_stats['habit_streaks'].values()]
    if all_streaks:
        streak_stats['streak_distribution'] = {
            'mean': float(np.mean(all_streaks)),
            'median': float(np.median(all_streaks)),
            'std': float(np.std(all_streaks)),
            'min': int(np.min(all_streaks)),
            'max': int(np.max(all_streaks))
        }
    
    return streak_stats


def calculate_category_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate statistics by habit category"""
    if data.empty or 'category' not in data.columns:
        return {}
    
    category_stats = {}
    
    for category in data['category'].unique():
        category_data = data[data['category'] == category]
        
        total_records = len(category_data)
        completed_records = len(category_data[category_data['is_completed'] == True])
        completion_rate = (completed_records / total_records * 100) if total_records > 0 else 0
        
        category_stats[category] = {
            'total_records': total_records,
            'completed_records': completed_records,
            'completion_rate': float(completion_rate),
            'unique_habits': category_data['habit_name'].nunique(),
            'habit_list': list(category_data['habit_name'].unique())
        }
    
    return category_stats


def calculate_time_patterns(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate time-based completion patterns"""
    if data.empty:
        return {}
    
    data = data.copy()
    data['date'] = pd.to_datetime(data['date'])
    data['weekday'] = data['date'].dt.day_name()
    data['hour'] = data['date'].dt.hour
    data['month'] = data['date'].dt.month_name()
    
    patterns = {}
    
    # Weekday patterns
    weekday_stats = data.groupby('weekday')['is_completed'].agg(['count', 'sum', 'mean']).round(3)
    weekday_stats.columns = ['total', 'completed', 'completion_rate']
    weekday_stats['completion_rate'] *= 100
    
    # Reorder weekdays
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_stats = weekday_stats.reindex(weekday_order, fill_value=0)
    
    patterns['weekday'] = weekday_stats.to_dict('index')
    
    # Monthly patterns
    if len(data['month'].unique()) > 1:
        monthly_stats = data.groupby('month')['is_completed'].agg(['count', 'sum', 'mean']).round(3)
        monthly_stats.columns = ['total', 'completed', 'completion_rate']
        monthly_stats['completion_rate'] *= 100
        patterns['monthly'] = monthly_stats.to_dict('index')
    
    # Time of day patterns (if completion_time is available)
    if 'completion_time' in data.columns:
        data['completion_time'] = pd.to_datetime(data['completion_time'], errors='coerce')
        completed_data = data[data['is_completed'] == True].dropna(subset=['completion_time'])
        
        if not completed_data.empty:
            completed_data['completion_hour'] = completed_data['completion_time'].dt.hour
            hourly_stats = completed_data.groupby('completion_hour').size().to_dict()
            patterns['hourly'] = hourly_stats
    
    return patterns


def calculate_habit_performance(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Calculate performance metrics for each habit"""
    if data.empty:
        return []
    
    performance_list = []
    
    for habit_name in data['habit_name'].unique():
        habit_data = data[data['habit_name'] == habit_name]
        
        total_records = len(habit_data)
        completed_records = len(habit_data[habit_data['is_completed'] == True])
        completion_rate = (completed_records / total_records * 100) if total_records > 0 else 0
        
        # Calculate streaks
        streaks = calculate_streak_statistics(habit_data)
        habit_streak_info = streaks.get('habit_streaks', {}).get(habit_name, {'current_streak': 0, 'best_streak': 0})
        
        # Calculate consistency (days with records vs total possible days)
        if not habit_data.empty:
            habit_data_copy = habit_data.copy()
            habit_data_copy['date'] = pd.to_datetime(habit_data_copy['date'])
            date_range = (habit_data_copy['date'].max() - habit_data_copy['date'].min()).days + 1
            unique_days = habit_data_copy['date'].dt.date.nunique()
            consistency = (unique_days / date_range * 100) if date_range > 0 else 0
        else:
            consistency = 0
        
        # Get category if available
        category = habit_data.iloc[0].get('category', 'Unknown') if not habit_data.empty else 'Unknown'
        
        performance_list.append({
            'habit_name': habit_name,
            'category': category,
            'total_records': total_records,
            'completed_records': completed_records,
            'completion_rate': float(completion_rate),
            'current_streak': habit_streak_info['current_streak'],
            'best_streak': habit_streak_info['best_streak'],
            'consistency': float(consistency),
            'performance_score': float((completion_rate * 0.6) + (consistency * 0.4))  # Weighted score
        })
    
    # Sort by performance score
    performance_list.sort(key=lambda x: x['performance_score'], reverse=True)
    
    return performance_list


def get_habit_insights(data: pd.DataFrame) -> List[str]:
    """Generate insights and recommendations based on habit data"""
    if data.empty:
        return ["No habit data available for analysis."]
    
    insights = []
    stats = calculate_habit_statistics(data)
    
    # Overall performance insights
    overall_rate = stats.get('overall_completion_rate', 0)
    if overall_rate >= 80:
        insights.append(f"🎉 Excellent habit consistency! You're maintaining a {overall_rate:.1f}% completion rate.")
    elif overall_rate >= 60:
        insights.append(f"👍 Good habit performance with {overall_rate:.1f}% completion rate. Room for improvement!")
    else:
        insights.append(f"📈 Your habit completion rate is {overall_rate:.1f}%. Focus on building consistency.")
    
    # Streak insights
    best_streak = stats.get('streaks', {}).get('overall_best_streak', 0)
    if best_streak >= 30:
        insights.append(f"🔥 Impressive! Your best streak is {best_streak} days. Keep the momentum going!")
    elif best_streak >= 7:
        insights.append(f"💪 You've achieved a {best_streak}-day streak. Aim for even longer streaks!")
    
    # Time pattern insights
    time_patterns = stats.get('time_patterns', {})
    weekday_patterns = time_patterns.get('weekday', {})
    
    if weekday_patterns:
        best_day = max(weekday_patterns.keys(), key=lambda k: weekday_patterns[k].get('completion_rate', 0))
        worst_day = min(weekday_patterns.keys(), key=lambda k: weekday_patterns[k].get('completion_rate', 0))
        
        best_rate = weekday_patterns[best_day].get('completion_rate', 0)
        worst_rate = weekday_patterns[worst_day].get('completion_rate', 0)
        
        if best_rate - worst_rate > 20:
            insights.append(f"📅 {best_day} is your strongest day ({best_rate:.1f}% completion), while {worst_day} needs attention ({worst_rate:.1f}%).")
    
    # Category insights
    categories = stats.get('categories', {})
    if categories:
        best_category = max(categories.keys(), key=lambda k: categories[k].get('completion_rate', 0))
        best_cat_rate = categories[best_category].get('completion_rate', 0)
        
        if best_cat_rate > overall_rate + 10:
            insights.append(f"🏆 Your '{best_category}' habits are performing exceptionally well ({best_cat_rate:.1f}% completion).")
    
    # Performance insights
    habit_performance = stats.get('habit_performance', [])
    if habit_performance:
        top_habit = habit_performance[0]
        if top_habit['completion_rate'] >= 90:
            insights.append(f"⭐ '{top_habit['habit_name']}' is your star habit with {top_habit['completion_rate']:.1f}% completion!")
        
        # Find habits that need attention
        struggling_habits = [h for h in habit_performance if h['completion_rate'] < 50]
        if struggling_habits:
            habit_names = [h['habit_name'] for h in struggling_habits[:2]]
            insights.append(f"🎯 Focus on improving: {', '.join(habit_names)}. Consider adjusting your approach.")
    
    return insights


def _get_empty_stats() -> Dict[str, Any]:
    """Return empty statistics structure"""
    return {
        'total_records': 0,
        'total_habits': 0,
        'total_completions': 0,
        'overall_completion_rate': 0.0,
        'date_range': {'start_date': '', 'end_date': '', 'total_days': 0},
        'today': {'total_habits': 0, 'completed_habits': 0, 'completion_rate': 0.0},
        'this_week': {'total_records': 0, 'completed_records': 0, 'completion_rate': 0.0},
        'this_month': {'total_records': 0, 'completed_records': 0, 'completion_rate': 0.0},
        'streaks': {},
        'categories': {},
        'time_patterns': {},
        'habit_performance': []
    }
