"""
To-Do Analytics Utilities
Provides data processing functions for to-do analytics calculations and statistics
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TodoAnalytics:
    """Data class for to-do analytics results"""
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    cancelled_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0
    average_completion_time: float = 0.0
    total_estimated_hours: float = 0.0
    total_actual_hours: float = 0.0
    priority_breakdown: Dict[str, Any] = None
    category_breakdown: Dict[str, Any] = None
    time_patterns: Dict[str, Any] = None
    productivity_metrics: Dict[str, Any] = None


def calculate_todo_statistics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive to-do statistics"""
    if data.empty:
        return _get_empty_stats()
    
    # Ensure date columns are datetime
    data = data.copy()
    for date_col in ['created_at', 'completed_at', 'due_date']:
        if date_col in data.columns:
            data[date_col] = pd.to_datetime(data[date_col], errors='coerce')
    
    stats = {}
    
    # Basic statistics
    stats['total_tasks'] = len(data)
    stats['completed_tasks'] = len(data[data['status'] == 'Completed'])
    stats['pending_tasks'] = len(data[data['status'] == 'Pending'])
    stats['in_progress_tasks'] = len(data[data['status'] == 'In Progress'])
    stats['cancelled_tasks'] = len(data[data['status'] == 'Cancelled'])
    
    # Completion rate
    stats['completion_rate'] = float((stats['completed_tasks'] / stats['total_tasks']) * 100) if stats['total_tasks'] > 0 else 0.0
    
    # Overdue tasks calculation
    today = pd.Timestamp.now().date()
    overdue_mask = (data['due_date'].notna()) & (data['due_date'].dt.date < today) & (data['status'] != 'Completed')
    stats['overdue_tasks'] = len(data[overdue_mask])
    stats['overdue_rate'] = float((stats['overdue_tasks'] / stats['total_tasks']) * 100) if stats['total_tasks'] > 0 else 0.0
    
    # Time-based statistics
    stats['time_analysis'] = calculate_time_analysis(data)
    
    # Priority breakdown
    stats['priority_breakdown'] = calculate_priority_breakdown(data)
    
    # Category breakdown
    stats['category_breakdown'] = calculate_category_breakdown(data)
    
    # Hours analysis
    stats['hours_analysis'] = calculate_hours_analysis(data)
    
    # Productivity metrics
    stats['productivity_metrics'] = calculate_productivity_metrics(data)
    
    # Time patterns
    stats['time_patterns'] = calculate_time_patterns(data)
    
    # Task trends
    stats['task_trends'] = calculate_task_trends(data)
    
    # Performance indicators
    stats['performance_indicators'] = calculate_performance_indicators(data)
    
    return stats


def calculate_time_analysis(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate time-based analysis"""
    time_stats = {}
    
    # Average completion time for completed tasks
    completed_tasks = data[data['status'] == 'Completed'].copy()
    if not completed_tasks.empty and 'created_at' in completed_tasks.columns and 'completed_at' in completed_tasks.columns:
        completed_tasks['completion_time'] = (completed_tasks['completed_at'] - completed_tasks['created_at']).dt.total_seconds() / 3600  # hours
        time_stats['average_completion_time_hours'] = float(completed_tasks['completion_time'].mean())
        time_stats['median_completion_time_hours'] = float(completed_tasks['completion_time'].median())
        time_stats['fastest_completion_hours'] = float(completed_tasks['completion_time'].min())
        time_stats['slowest_completion_hours'] = float(completed_tasks['completion_time'].max())
    else:
        time_stats['average_completion_time_hours'] = 0.0
        time_stats['median_completion_time_hours'] = 0.0
        time_stats['fastest_completion_hours'] = 0.0
        time_stats['slowest_completion_hours'] = 0.0
    
    # Tasks created this week/month
    today = pd.Timestamp.now()
    week_start = today - pd.Timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    if 'created_at' in data.columns:
        time_stats['tasks_created_this_week'] = len(data[data['created_at'] >= week_start])
        time_stats['tasks_created_this_month'] = len(data[data['created_at'] >= month_start])
        time_stats['tasks_completed_this_week'] = len(data[(data['status'] == 'Completed') & (data['completed_at'] >= week_start)])
        time_stats['tasks_completed_this_month'] = len(data[(data['status'] == 'Completed') & (data['completed_at'] >= month_start)])
    else:
        time_stats['tasks_created_this_week'] = 0
        time_stats['tasks_created_this_month'] = 0
        time_stats['tasks_completed_this_week'] = 0
        time_stats['tasks_completed_this_month'] = 0
    
    return time_stats


def calculate_priority_breakdown(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate priority-based breakdown"""
    priority_stats = {}
    
    # Count by priority
    priority_counts = data['priority'].value_counts().to_dict()
    priority_stats['counts'] = priority_counts
    
    # Completion rate by priority
    priority_completion = {}
    for priority in data['priority'].unique():
        priority_data = data[data['priority'] == priority]
        completed = len(priority_data[priority_data['status'] == 'Completed'])
        total = len(priority_data)
        priority_completion[priority] = {
            'total': total,
            'completed': completed,
            'completion_rate': float((completed / total) * 100) if total > 0 else 0.0
        }
    
    priority_stats['completion_rates'] = priority_completion
    
    # Overdue by priority
    today = pd.Timestamp.now().date()
    overdue_mask = (data['due_date'].notna()) & (data['due_date'].dt.date < today) & (data['status'] != 'Completed')
    overdue_by_priority = data[overdue_mask]['priority'].value_counts().to_dict()
    priority_stats['overdue_counts'] = overdue_by_priority
    
    return priority_stats


def calculate_category_breakdown(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate category-based breakdown"""
    category_stats = {}
    
    # Count by category
    category_counts = data['category'].value_counts().to_dict()
    category_stats['counts'] = category_counts
    
    # Completion rate by category
    category_completion = {}
    for category in data['category'].unique():
        category_data = data[data['category'] == category]
        completed = len(category_data[category_data['status'] == 'Completed'])
        total = len(category_data)
        category_completion[category] = {
            'total': total,
            'completed': completed,
            'completion_rate': float((completed / total) * 100) if total > 0 else 0.0
        }
    
    category_stats['completion_rates'] = category_completion
    
    # Average hours by category
    category_hours = {}
    for category in data['category'].unique():
        category_data = data[data['category'] == category]
        category_hours[category] = {
            'avg_estimated_hours': float(category_data['estimated_hours'].mean()) if len(category_data) > 0 else 0.0,
            'avg_actual_hours': float(category_data['actual_hours'].mean()) if len(category_data) > 0 else 0.0,
            'total_estimated_hours': float(category_data['estimated_hours'].sum()),
            'total_actual_hours': float(category_data['actual_hours'].sum())
        }
    
    category_stats['hours_analysis'] = category_hours
    
    return category_stats


def calculate_hours_analysis(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate hours-based analysis"""
    hours_stats = {}
    
    # Total hours
    hours_stats['total_estimated_hours'] = float(data['estimated_hours'].sum())
    hours_stats['total_actual_hours'] = float(data['actual_hours'].sum())
    hours_stats['average_estimated_hours'] = float(data['estimated_hours'].mean()) if len(data) > 0 else 0.0
    hours_stats['average_actual_hours'] = float(data['actual_hours'].mean()) if len(data) > 0 else 0.0
    
    # Estimation accuracy
    tasks_with_both_hours = data[(data['estimated_hours'] > 0) & (data['actual_hours'] > 0)]
    if not tasks_with_both_hours.empty:
        estimation_accuracy = tasks_with_both_hours['actual_hours'] / tasks_with_both_hours['estimated_hours']
        hours_stats['estimation_accuracy_ratio'] = float(estimation_accuracy.mean())
        hours_stats['overestimated_tasks'] = len(tasks_with_both_hours[tasks_with_both_hours['actual_hours'] < tasks_with_both_hours['estimated_hours']])
        hours_stats['underestimated_tasks'] = len(tasks_with_both_hours[tasks_with_both_hours['actual_hours'] > tasks_with_both_hours['estimated_hours']])
        hours_stats['accurate_estimates'] = len(tasks_with_both_hours[tasks_with_both_hours['actual_hours'] == tasks_with_both_hours['estimated_hours']])
    else:
        hours_stats['estimation_accuracy_ratio'] = 1.0
        hours_stats['overestimated_tasks'] = 0
        hours_stats['underestimated_tasks'] = 0
        hours_stats['accurate_estimates'] = 0
    
    return hours_stats


def calculate_productivity_metrics(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate productivity metrics"""
    productivity = {}
    
    # Task velocity (tasks completed per day)
    completed_tasks = data[data['status'] == 'Completed'].copy()
    if not completed_tasks.empty and 'completed_at' in completed_tasks.columns:
        date_range = (completed_tasks['completed_at'].max() - completed_tasks['completed_at'].min()).days
        if date_range > 0:
            productivity['tasks_per_day'] = float(len(completed_tasks) / date_range)
        else:
            productivity['tasks_per_day'] = float(len(completed_tasks))
    else:
        productivity['tasks_per_day'] = 0.0
    
    # Completion consistency (standard deviation of daily completions)
    if not completed_tasks.empty and 'completed_at' in completed_tasks.columns:
        daily_completions = completed_tasks.groupby(completed_tasks['completed_at'].dt.date).size()
        productivity['completion_consistency'] = float(daily_completions.std()) if len(daily_completions) > 1 else 0.0
    else:
        productivity['completion_consistency'] = 0.0
    
    # Priority focus (percentage of high/urgent priority tasks completed)
    high_priority_tasks = data[data['priority'].isin(['High', 'Urgent'])]
    high_priority_completed = high_priority_tasks[high_priority_tasks['status'] == 'Completed']
    productivity['high_priority_completion_rate'] = float((len(high_priority_completed) / len(high_priority_tasks)) * 100) if len(high_priority_tasks) > 0 else 0.0
    
    # Task backlog (pending + in progress tasks)
    productivity['current_backlog'] = len(data[data['status'].isin(['Pending', 'In Progress'])])
    
    return productivity


def calculate_time_patterns(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate time-based patterns"""
    if data.empty or 'created_at' not in data.columns:
        return {}
    
    data_copy = data.copy()
    data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')
    
    patterns = {}
    
    # Day of week patterns
    data_copy['weekday'] = data_copy['created_at'].dt.day_name()
    weekday_stats = data_copy.groupby('weekday').agg({
        'status': ['count', lambda x: (x == 'Completed').sum()]
    })
    weekday_stats.columns = ['total_tasks', 'completed_tasks']
    weekday_stats['completion_rate'] = (weekday_stats['completed_tasks'] / weekday_stats['total_tasks'] * 100).round(1)
    
    # Reorder weekdays
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_stats = weekday_stats.reindex(weekday_order, fill_value=0)
    patterns['weekday'] = weekday_stats.to_dict('index')
    
    # Hour of day patterns
    data_copy['hour'] = data_copy['created_at'].dt.hour
    hourly_stats = data_copy.groupby('hour').size()
    patterns['hourly'] = hourly_stats.to_dict()
    
    # Monthly patterns
    data_copy['month'] = data_copy['created_at'].dt.month_name()
    monthly_stats = data_copy.groupby('month').agg({
        'status': ['count', lambda x: (x == 'Completed').sum()]
    })
    monthly_stats.columns = ['total_tasks', 'completed_tasks']
    monthly_stats['completion_rate'] = (monthly_stats['completed_tasks'] / monthly_stats['total_tasks'] * 100).round(1)
    patterns['monthly'] = monthly_stats.to_dict('index')
    
    return patterns


def calculate_task_trends(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate task trends over time"""
    if data.empty or 'created_at' not in data.columns:
        return {}
    
    data_copy = data.copy()
    data_copy['created_at'] = pd.to_datetime(data_copy['created_at'], errors='coerce')
    data_copy = data_copy.sort_values('created_at')
    
    trends = {}
    
    # Weekly trends
    data_copy['week'] = data_copy['created_at'].dt.to_period('W')
    weekly_creation = data_copy.groupby('week').size()
    
    # Weekly completion trends
    completed_data = data_copy[data_copy['status'] == 'Completed'].copy()
    if not completed_data.empty and 'completed_at' in completed_data.columns:
        completed_data['completed_at'] = pd.to_datetime(completed_data['completed_at'], errors='coerce')
        completed_data['completion_week'] = completed_data['completed_at'].dt.to_period('W')
        weekly_completion = completed_data.groupby('completion_week').size()
    else:
        weekly_completion = pd.Series(dtype=int)
    
    trends['weekly'] = {
        'creation_dates': [str(week) for week in weekly_creation.index],
        'creation_counts': weekly_creation.values.tolist(),
        'completion_dates': [str(week) for week in weekly_completion.index],
        'completion_counts': weekly_completion.values.tolist()
    }
    
    # Calculate trend direction
    if len(weekly_creation) >= 4:
        recent_avg = weekly_creation.tail(2).mean()
        earlier_avg = weekly_creation.head(2).mean()
        if recent_avg > earlier_avg * 1.1:
            trends['creation_trend'] = 'increasing'
        elif recent_avg < earlier_avg * 0.9:
            trends['creation_trend'] = 'decreasing'
        else:
            trends['creation_trend'] = 'stable'
    else:
        trends['creation_trend'] = 'insufficient_data'
    
    return trends


def calculate_performance_indicators(data: pd.DataFrame) -> Dict[str, Any]:
    """Calculate key performance indicators"""
    if data.empty:
        return {}
    
    indicators = {}
    
    # Task distribution health
    status_counts = data['status'].value_counts()
    total_tasks = len(data)
    
    indicators['task_health'] = {
        'completion_percentage': float((status_counts.get('Completed', 0) / total_tasks) * 100),
        'in_progress_percentage': float((status_counts.get('In Progress', 0) / total_tasks) * 100),
        'pending_percentage': float((status_counts.get('Pending', 0) / total_tasks) * 100),
        'cancelled_percentage': float((status_counts.get('Cancelled', 0) / total_tasks) * 100)
    }
    
    # Priority distribution
    priority_counts = data['priority'].value_counts()
    indicators['priority_distribution'] = {
        'urgent_percentage': float((priority_counts.get('Urgent', 0) / total_tasks) * 100),
        'high_percentage': float((priority_counts.get('High', 0) / total_tasks) * 100),
        'medium_percentage': float((priority_counts.get('Medium', 0) / total_tasks) * 100),
        'low_percentage': float((priority_counts.get('Low', 0) / total_tasks) * 100)
    }
    
    # Overdue analysis
    today = pd.Timestamp.now().date()
    if 'due_date' in data.columns:
        overdue_mask = (data['due_date'].notna()) & (data['due_date'].dt.date < today) & (data['status'] != 'Completed')
        overdue_tasks = data[overdue_mask]
        
        indicators['overdue_analysis'] = {
            'total_overdue': len(overdue_tasks),
            'overdue_percentage': float((len(overdue_tasks) / total_tasks) * 100),
            'overdue_by_priority': overdue_tasks['priority'].value_counts().to_dict(),
            'overdue_by_category': overdue_tasks['category'].value_counts().to_dict()
        }
    else:
        indicators['overdue_analysis'] = {
            'total_overdue': 0,
            'overdue_percentage': 0.0,
            'overdue_by_priority': {},
            'overdue_by_category': {}
        }
    
    return indicators


def get_todo_insights(data: pd.DataFrame) -> List[str]:
    """Generate insights and recommendations based on to-do data"""
    if data.empty:
        return ["No to-do data available for analysis."]
    
    insights = []
    stats = calculate_todo_statistics(data)
    
    # Overall performance insights
    completion_rate = stats.get('completion_rate', 0)
    if completion_rate >= 80:
        insights.append(f"🎉 Excellent productivity! You have a {completion_rate:.1f}% task completion rate.")
    elif completion_rate >= 60:
        insights.append(f"👍 Good progress with {completion_rate:.1f}% completion rate. Keep it up!")
    else:
        insights.append(f"📈 Your completion rate is {completion_rate:.1f}%. Focus on completing more tasks to improve productivity.")
    
    # Overdue tasks insights
    overdue_rate = stats.get('overdue_rate', 0)
    if overdue_rate > 20:
        insights.append(f"⚠️ You have {stats.get('overdue_tasks', 0)} overdue tasks ({overdue_rate:.1f}%). Consider reviewing your deadlines and priorities.")
    elif overdue_rate > 0:
        insights.append(f"📅 You have {stats.get('overdue_tasks', 0)} overdue tasks. Try to complete them soon!")
    
    # Priority insights
    priority_breakdown = stats.get('priority_breakdown', {})
    completion_rates = priority_breakdown.get('completion_rates', {})
    
    if completion_rates:
        high_priority_rate = completion_rates.get('High', {}).get('completion_rate', 0)
        urgent_priority_rate = completion_rates.get('Urgent', {}).get('completion_rate', 0)
        
        if high_priority_rate < 70 or urgent_priority_rate < 70:
            insights.append("🎯 Focus on completing high-priority and urgent tasks first to improve effectiveness.")
    
    # Time pattern insights
    time_patterns = stats.get('time_patterns', {})
    weekday_patterns = time_patterns.get('weekday', {})
    
    if weekday_patterns:
        best_day = max(weekday_patterns.keys(), key=lambda k: weekday_patterns[k].get('completion_rate', 0))
        best_rate = weekday_patterns[best_day].get('completion_rate', 0)
        
        if best_rate > 0:
            insights.append(f"📊 {best_day} is your most productive day with {best_rate:.1f}% completion rate.")
    
    # Hours estimation insights
    hours_analysis = stats.get('hours_analysis', {})
    estimation_ratio = hours_analysis.get('estimation_accuracy_ratio', 1.0)
    
    if estimation_ratio > 1.2:
        insights.append("⏱️ You tend to underestimate task duration. Consider adding buffer time to your estimates.")
    elif estimation_ratio < 0.8:
        insights.append("⏱️ You tend to overestimate task duration. You might be more efficient than you think!")
    
    # Productivity insights
    productivity = stats.get('productivity_metrics', {})
    backlog = productivity.get('current_backlog', 0)
    
    if backlog > 20:
        insights.append(f"📋 You have {backlog} tasks in your backlog. Consider breaking down large tasks or delegating some work.")
    
    return insights


def _get_empty_stats() -> Dict[str, Any]:
    """Return empty statistics structure"""
    return {
        'total_tasks': 0,
        'completed_tasks': 0,
        'pending_tasks': 0,
        'in_progress_tasks': 0,
        'cancelled_tasks': 0,
        'overdue_tasks': 0,
        'completion_rate': 0.0,
        'overdue_rate': 0.0,
        'time_analysis': {},
        'priority_breakdown': {},
        'category_breakdown': {},
        'hours_analysis': {},
        'productivity_metrics': {},
        'time_patterns': {},
        'task_trends': {},
        'performance_indicators': {}
    }
